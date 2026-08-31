"""Narrow credential and provider-operation service.

Production must deploy this service under a different OCI workload identity
from the public app and paper worker. It deliberately has no raw decrypt,
arbitrary URL, or generic proxy operation.
"""

from __future__ import annotations

import hmac
import datetime as dt
import os
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, SecretStr

from .ai import AiProviderError, generate_strategy, local_ai_ready
from .ai_credentials import (
    decrypt_api_key,
    encrypt_api_key,
    key_hint,
    provider_catalog,
    validate_api_key,
    validate_provider_model,
)
from .config import get_settings
from .credential_store import validate_credential_backend
from .http_security import RequestBodyLimitMiddleware
from .kis_quotes import KisCredentials, KisQuoteClient
from .market_data_credentials import (
    MarketDataProviderError,
    credential_hint,
    decrypt_market_credential,
    encrypt_market_credential,
    validate_market_credential,
    validate_provider_environment,
    verify_connection,
)
from .toss_quotes import TossCredentials, TossQuoteClient


settings = get_settings()
app = FastAPI(
    title="Milkyway credential operation broker",
    docs_url=None if settings.production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.production else "/openapi.json",
)
app.add_middleware(RequestBodyLimitMiddleware, max_bytes=settings.max_request_body_bytes)
_verification_slots = threading.BoundedSemaphore(2)
_ai_slots = threading.BoundedSemaphore(settings.local_ai_max_concurrent_requests)
_TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.^_-]{0,19}$")
_rate_lock = threading.Lock()
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_MAX_RATE_KEYS = max(512, settings.max_users * 20)


def _tenant_limit(multiplier: int) -> int:
    return max(1, int(getattr(settings, "max_users", 40))) * multiplier


@dataclass(frozen=True)
class BrokerQuote:
    ticker: str
    price: float
    bid: float
    ask: float
    volume: float
    source: str
    observed_at: dt.datetime


def _rate_limit(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    with _rate_lock:
        if key not in _rate_buckets and len(_rate_buckets) >= _MAX_RATE_KEYS:
            stale_before = now - 3600
            for stale_key in [
                candidate
                for candidate, values in _rate_buckets.items()
                if not values or values[-1] < stale_before
            ]:
                _rate_buckets.pop(stale_key, None)
            if len(_rate_buckets) >= _MAX_RATE_KEYS:
                raise HTTPException(
                    status_code=429,
                    detail="자격증명 서비스 요청이 많습니다. 잠시 후 다시 시도해 주세요",
                )
        bucket = _rate_buckets[key]
        while bucket and bucket[0] < now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail="자격증명 서비스 요청이 많습니다. 잠시 후 다시 시도해 주세요",
            )
        bucket.append(now)


class AiCipherBody(BaseModel):
    owner_id: str = Field(min_length=1, max_length=128)
    provider: str = Field(min_length=2, max_length=30)
    ciphertext: str = Field(max_length=20_000)


class AiEncryptBody(BaseModel):
    owner_id: str = Field(min_length=1, max_length=128)
    provider: str = Field(min_length=2, max_length=30)
    api_key: SecretStr


class AiGenerateBody(AiCipherBody):
    model: str = Field(min_length=2, max_length=100)
    prompt: str = Field(min_length=5, max_length=3000)


class MarketCipherBody(BaseModel):
    owner_id: str = Field(min_length=1, max_length=128)
    provider: str = Field(min_length=2, max_length=30)
    environment: str = Field(min_length=2, max_length=20)
    encrypted_api_key: str = Field(min_length=1, max_length=20_000)
    encrypted_api_secret: str = Field(min_length=1, max_length=20_000)


class MarketPrepareBody(BaseModel):
    owner_id: str = Field(min_length=1, max_length=128)
    provider: str = Field(min_length=2, max_length=30)
    environment: str = Field(min_length=2, max_length=20)
    api_key: SecretStr | None = None
    api_secret: SecretStr | None = None
    current_provider: str | None = Field(default=None, max_length=30)
    current_environment: str | None = Field(default=None, max_length=20)
    current_encrypted_api_key: str | None = Field(default=None, max_length=20_000)
    current_encrypted_api_secret: str | None = Field(default=None, max_length=20_000)


class MarketQuotesBody(MarketCipherBody):
    tickers: list[str] = Field(min_length=1, max_length=200)


class SharedQuotesBody(BaseModel):
    tickers: list[str] = Field(min_length=1, max_length=200)


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="credential broker authentication failed")
    return authorization[7:]


def _app_identity(authorization: str | None = Header(default=None)) -> str:
    expected = settings.credential_broker_app_token
    if not expected or not hmac.compare_digest(_bearer(authorization), expected):
        raise HTTPException(status_code=401, detail="credential broker authentication failed")
    return "app"


def _paper_identity(authorization: str | None = Header(default=None)) -> str:
    expected = settings.credential_broker_paper_token
    if not expected or not hmac.compare_digest(_bearer(authorization), expected):
        raise HTTPException(status_code=401, detail="credential broker authentication failed")
    return "paper"


def _safe_failure(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, (AiProviderError, MarketDataProviderError)):
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=503, detail="자격증명 처리 서비스를 사용할 수 없습니다")


def _normalized_tickers(values: list[str]) -> tuple[str, ...]:
    tickers = tuple(sorted({value.strip().upper() for value in values}))
    if not tickers or len(tickers) > 200 or any(
        not _TICKER_PATTERN.fullmatch(value) for value in tickers
    ):
        raise ValueError("시세 종목 목록이 올바르지 않습니다")
    return tickers


def _quote_payload(values: list[BrokerQuote]) -> dict:
    return {
        "quotes": [
            {
                "ticker": value.ticker,
                "price": value.price,
                "bid": value.bid,
                "ask": value.ask,
                "volume": value.volume,
                "source": value.source,
                "observed_at": value.observed_at.isoformat(),
            }
            for value in values[:200]
        ]
    }


@app.on_event("startup")
def startup() -> None:
    errors = settings.startup_errors("broker")
    if errors:
        raise RuntimeError("Startup configuration failed: " + "; ".join(errors))
    validate_credential_backend(settings)


@app.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@app.post("/v1/preflight")
def preflight(_identity: str = Depends(_app_identity)) -> dict:
    _rate_limit("preflight:app", 10, 60)
    validate_credential_backend(settings)
    return {"status": "ok"}


@app.post("/v1/paper-preflight")
def paper_preflight(_identity: str = Depends(_paper_identity)) -> dict:
    _rate_limit("preflight:paper", 10, 60)
    validate_credential_backend(settings, purposes=("market",))
    return {"status": "ok"}


@app.post("/v1/ai/catalog")
def ai_catalog(_identity: str = Depends(_app_identity)) -> dict:
    ready = settings.local_ai_enabled and local_ai_ready(
        base_url=settings.local_ai_base_url,
        model=settings.local_ai_model,
        api_key=settings.local_ai_api_key,
    )
    return {"providers": provider_catalog(settings, local_ready=ready)}


@app.post("/v1/ai/encrypt")
def ai_encrypt(body: AiEncryptBody, _identity: str = Depends(_app_identity)) -> dict:
    try:
        _rate_limit("ai-encrypt:global", _tenant_limit(10), 3600)
        _rate_limit("ai-encrypt:" + body.owner_id, 10, 3600)
        provider, _model = validate_provider_model(body.provider, "broker-validation")
        if provider == "local":
            raise ValueError("로컬 AI에는 회원 API 키를 저장하지 않습니다")
        value = validate_api_key(body.api_key.get_secret_value())
        return {
            "ciphertext": encrypt_api_key(
                value, settings, owner_id=body.owner_id, provider=provider
            ),
            "key_hint": key_hint(value),
        }
    except Exception as exc:
        raise _safe_failure(exc) from None


@app.post("/v1/ai/validate")
def ai_validate(body: AiCipherBody, _identity: str = Depends(_app_identity)) -> dict:
    try:
        _rate_limit("validate:global", _tenant_limit(20), 3600)
        provider, _model = validate_provider_model(body.provider, "broker-validation")
        validate_api_key(
            decrypt_api_key(
                body.ciphertext,
                settings,
                owner_id=body.owner_id,
                provider=provider,
            )
        )
        return {"status": "ok"}
    except Exception as exc:
        raise _safe_failure(exc) from None


@app.post("/v1/ai/generate")
def ai_generate(body: AiGenerateBody, _identity: str = Depends(_app_identity)) -> dict:
    acquired = False
    try:
        _rate_limit("ai-generate:global", _tenant_limit(10), 3600)
        _rate_limit("ai-generate:" + body.owner_id, 10, 3600)
        acquired = _ai_slots.acquire(blocking=False)
        if not acquired:
            raise HTTPException(
                status_code=429,
                detail="AI 요청이 많습니다. 잠시 후 다시 시도해 주세요",
            )
        provider, model = validate_provider_model(body.provider, body.model)
        if provider == "local":
            if body.ciphertext:
                raise ValueError("로컬 AI 자격증명 형식이 올바르지 않습니다")
            if not settings.local_ai_enabled:
                raise RuntimeError("로컬 AI 서버가 비활성화되어 있습니다")
            api_key = settings.local_ai_api_key
            model = settings.local_ai_model
            local_base_url = settings.local_ai_base_url
        else:
            api_key = decrypt_api_key(
                body.ciphertext,
                settings,
                owner_id=body.owner_id,
                provider=provider,
            )
            local_base_url = None
        spec, preview = generate_strategy(
            body.prompt,
            provider=provider,
            model=model,
            api_key=api_key,
            timeout_seconds=settings.ai_timeout_seconds,
            local_base_url=local_base_url,
        )
        return {"spec": spec.model_dump(mode="json"), "preview": preview}
    except HTTPException:
        raise
    except Exception as exc:
        raise _safe_failure(exc) from None
    finally:
        if acquired:
            _ai_slots.release()


def _market_plaintext(body: MarketCipherBody) -> tuple[str, str, str, str]:
    provider, environment = validate_provider_environment(body.provider, body.environment)
    api_key = validate_market_credential(
        decrypt_market_credential(
            body.encrypted_api_key,
            settings,
            owner_id=body.owner_id,
            provider=provider,
            environment=environment,
            label="App Key",
        ),
        "App Key",
    )
    api_secret = validate_market_credential(
        decrypt_market_credential(
            body.encrypted_api_secret,
            settings,
            owner_id=body.owner_id,
            provider=provider,
            environment=environment,
            label="App Secret",
        ),
        "App Secret",
    )
    return provider, environment, api_key, api_secret


@app.post("/v1/market/validate")
def market_validate(body: MarketCipherBody, _identity: str = Depends(_app_identity)) -> dict:
    try:
        _rate_limit("validate:global", _tenant_limit(20), 3600)
        _market_plaintext(body)
        return {"status": "ok"}
    except Exception as exc:
        raise _safe_failure(exc) from None


@app.post("/v1/market/prepare")
def market_prepare(body: MarketPrepareBody, _identity: str = Depends(_app_identity)) -> dict:
    try:
        _rate_limit("market-prepare:global", _tenant_limit(10), 3600)
        _rate_limit("market-prepare:" + body.owner_id, 10, 3600)
        provider, environment = validate_provider_environment(body.provider, body.environment)
        supplied_key = body.api_key.get_secret_value() if body.api_key else ""
        supplied_secret = body.api_secret.get_secret_value() if body.api_secret else ""
        can_retain = (
            body.current_provider == provider
            and body.current_environment is not None
            and body.current_encrypted_api_key is not None
            and body.current_encrypted_api_secret is not None
        )
        if supplied_key:
            api_key = validate_market_credential(supplied_key, "App Key")
        elif can_retain:
            api_key = decrypt_market_credential(
                body.current_encrypted_api_key,
                settings,
                owner_id=body.owner_id,
                provider=provider,
                environment=body.current_environment,
                label="App Key",
            )
        else:
            raise ValueError("새 시세 공급자를 연결하려면 App Key를 입력해 주세요")
        if supplied_secret:
            api_secret = validate_market_credential(supplied_secret, "App Secret")
        elif can_retain:
            api_secret = decrypt_market_credential(
                body.current_encrypted_api_secret,
                settings,
                owner_id=body.owner_id,
                provider=provider,
                environment=body.current_environment,
                label="App Secret",
            )
        else:
            raise ValueError("새 시세 공급자를 연결하려면 App Secret을 입력해 주세요")
        if not _verification_slots.acquire(blocking=False):
            raise HTTPException(
                status_code=429,
                detail="시세 API 인증 요청이 많습니다. 잠시 후 다시 시도해 주세요",
            )
        try:
            verify_connection(provider, environment, api_key, api_secret)
        finally:
            _verification_slots.release()
        return {
            "encrypted_api_key": encrypt_market_credential(
                api_key,
                "App Key",
                settings,
                owner_id=body.owner_id,
                provider=provider,
                environment=environment,
            ),
            "encrypted_api_secret": encrypt_market_credential(
                api_secret,
                "App Secret",
                settings,
                owner_id=body.owner_id,
                provider=provider,
                environment=environment,
            ),
            "key_hint": credential_hint(api_key),
            "secret_hint": credential_hint(api_secret),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise _safe_failure(exc) from None


def _kis_quotes(
    credentials: KisCredentials, tickers: tuple[str, ...], *, source: str
) -> list[BrokerQuote]:
    client = KisQuoteClient(credentials)
    if not client.connect():
        raise RuntimeError("KIS quote provider connection failed")
    values = []
    for ticker in tickers:
        raw = client.get_quote(ticker)
        price = float(raw.get("price", 0) or 0)
        if price > 0:
            values.append(
                BrokerQuote(
                    ticker=ticker,
                    price=price,
                    bid=float(raw.get("bid", 0) or 0),
                    ask=float(raw.get("ask", 0) or 0),
                    volume=float(raw.get("volume", 0) or 0),
                    source=source,
                    observed_at=dt.datetime.now(dt.timezone.utc),
                )
            )
        time.sleep(0.08)
    return values


def _member_quotes(body: MarketCipherBody, tickers: tuple[str, ...]) -> list[BrokerQuote]:
    provider, environment, api_key, api_secret = _market_plaintext(body)
    if provider == "kis":
        return _kis_quotes(
            KisCredentials(
                api_key=api_key,
                api_secret=api_secret,
                paper=environment == "paper",
            ),
            tickers,
            source="kis_member",
        )
    if provider == "toss" and environment == "live":
        client = TossQuoteClient(
            TossCredentials(client_id=api_key, client_secret=api_secret)
        )
        client.authenticate()
        return [
            BrokerQuote(
                ticker=raw["ticker"],
                price=float(raw["price"]),
                bid=float(raw.get("bid", 0) or 0),
                ask=float(raw.get("ask", 0) or 0),
                volume=float(raw.get("volume", 0) or 0),
                source="toss_member",
                observed_at=raw["observed_at"],
            )
            for raw in client.get_prices(tickers)
        ]
    raise ValueError("지원하지 않는 회원 시세 공급자입니다")


@app.post("/v1/market/quotes")
def market_quotes(body: MarketQuotesBody, _identity: str = Depends(_paper_identity)) -> dict:
    try:
        _rate_limit("market-quotes:global", _tenant_limit(4), 60)
        _rate_limit("market-quotes:" + body.owner_id, 4, 60)
        values = _member_quotes(body, _normalized_tickers(body.tickers))
        return _quote_payload(values)
    except Exception as exc:
        raise _safe_failure(exc) from None


@app.post("/v1/market/shared-quotes")
def shared_quotes(body: SharedQuotesBody, _identity: str = Depends(_paper_identity)) -> dict:
    try:
        _rate_limit("shared-quotes", 4, 60)
        if settings.quote_provider != "kis" or not settings.market_data_sharing_allowed:
            raise ValueError("공용 KIS 시세가 활성화되지 않았습니다")
        credentials = KisCredentials(
            api_key=os.getenv("BROKER_API_KEY", ""),
            api_secret=os.getenv("BROKER_API_SECRET", ""),
            account_id=os.getenv("BROKER_ACCOUNT_ID", ""),
            paper=True,
        )
        return _quote_payload(
            _kis_quotes(credentials, _normalized_tickers(body.tickers), source="kis")
        )
    except Exception as exc:
        raise _safe_failure(exc) from None
