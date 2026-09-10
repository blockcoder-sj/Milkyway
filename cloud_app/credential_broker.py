"""Narrow credential and provider-operation service.

Production must deploy this service under a different OCI workload identity
from the public app and paper worker. It deliberately has no raw decrypt,
arbitrary URL, or generic proxy operation.
"""

from __future__ import annotations

import hmac
import datetime as dt
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from .ai import AiProviderError, generate_strategy, local_ai_ready
from .ai_credentials import (
    decrypt_api_key,
    encrypt_api_key,
    key_hint,
    provider_catalog,
    validate_api_key,
    validate_provider_model,
)
from .config import get_settings, member_ai_credentials_enabled
from .credential_store import KmsCapacityError, validate_credential_backend
from .http_security import RequestBodyLimitMiddleware
from .kis_quotes import KisCredentials, KisQuoteClient, KisWorkBudgetExceeded
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
from .provider_secrets import provider_secret, verify_provider_secret_delivery
from .provider_process import ProviderProcess, ProviderOperationError


settings = get_settings()
app = FastAPI(
    title="Milkyway credential operation broker",
    docs_url=None if settings.production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.production else "/openapi.json",
)
app.add_middleware(
    RequestBodyLimitMiddleware,
    max_bytes=settings.max_request_body_bytes,
    read_timeout_seconds=settings.request_body_read_timeout_seconds,
    max_messages=settings.max_request_body_messages,
)
_verification_slots = threading.BoundedSemaphore(2)
_preflight_slots = threading.BoundedSemaphore(1)
_ai_slots = threading.BoundedSemaphore(settings.local_ai_max_concurrent_requests)
_quote_slots = threading.BoundedSemaphore(settings.quote_max_concurrent_requests)
_shared_kis_lock = threading.Lock()
_shared_kis_client: KisQuoteClient | None = None
_shared_kis_identity: tuple[str, str, bool] | None = None
_shared_ai_verified_until = 0.0
_TICKER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.^_-]{0,19}$")
_rate_lock = threading.Lock()
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_rate_windows: dict[str, int] = {}
_MAX_RATE_KEYS = max(512, settings.max_users * 20)


def _tenant_limit(multiplier: int) -> int:
    return max(1, int(getattr(settings, "max_users", 40))) * multiplier


def _shared_quote_rate_budget() -> int:
    """Admit every configured worker batch in any rolling minute."""

    batches_per_tick = (
        settings.shared_quote_max_symbols_per_tick
        + settings.shared_quote_batch_size
        - 1
    ) // settings.shared_quote_batch_size
    # Include both ends of a rolling window; the limiter expires entries only
    # once they are older than sixty seconds.
    ticks_per_minute = (60 + settings.quote_interval_seconds - 1) // (
        settings.quote_interval_seconds
    ) + 1
    return max(1, batches_per_tick * ticks_per_minute)


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
            for stale_key, values in list(_rate_buckets.items()):
                window = _rate_windows.get(stale_key, 3600)
                while values and values[0] < now - window:
                    values.popleft()
                if not values:
                    _rate_buckets.pop(stale_key, None)
                    _rate_windows.pop(stale_key, None)
            if len(_rate_buckets) >= _MAX_RATE_KEYS:
                oldest = min(
                    _rate_buckets,
                    key=lambda candidate: (
                        _rate_buckets[candidate][-1]
                        if _rate_buckets[candidate]
                        else float("-inf")
                    ),
                )
                _rate_buckets.pop(oldest, None)
                _rate_windows.pop(oldest, None)
        bucket = _rate_buckets[key]
        _rate_windows[key] = int(window_seconds)
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
    model_config = ConfigDict(extra="forbid")

    tickers: list[str] = Field(min_length=1, max_length=200)


class SharedAiGenerateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=5, max_length=3000)
    permit: SecretStr | None = Field(default=None, min_length=43, max_length=43)


def _member_post(path: str, *, market: bool = False, **kwargs):
    """Keep shared AI independent from member market credentials."""

    enabled = settings.member_credentials_enabled if market else member_ai_credentials_enabled(settings)
    if enabled and not settings.authority_enabled:
        return app.post(path, **kwargs)

    def disabled_route(function):
        return function

    return disabled_route


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


def _backtest_identity(authorization: str | None = Header(default=None)) -> str:
    expected = settings.credential_broker_backtest_token
    if not expected or not hmac.compare_digest(_bearer(authorization), expected):
        raise HTTPException(401, "credential broker authentication failed")
    return "backtest"


def _safe_failure(exc: Exception) -> HTTPException:
    if isinstance(exc, ProviderOperationError):
        return HTTPException(exc.status_code, exc.detail)
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, KmsCapacityError):
        return HTTPException(status_code=429, detail="KMS 요청이 많습니다. 잠시 후 다시 시도하세요")
    if isinstance(exc, (AiProviderError, MarketDataProviderError)):
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=503, detail="자격증명 처리 서비스를 사용할 수 없습니다")


def _normalized_tickers(values: list[str], *, maximum: int = 200) -> tuple[str, ...]:
    tickers = tuple(sorted({value.strip().upper() for value in values}))
    if not tickers or len(tickers) > maximum or any(
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
    if settings.production:
        _network_call("kms-preflight", {}, time.monotonic() + settings.quote_deadline_seconds)
    else:
        validate_credential_backend(settings)
    if settings.authority_enabled:
        from .database import prepare_runtime_database
        prepare_runtime_database()
    if settings.production:
        verify_provider_secret_delivery(settings)


@app.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@app.post("/v1/preflight")
def preflight(_identity: str = Depends(_app_identity)) -> dict:
    _rate_limit("preflight:app", 10, 60)
    if not settings.authority_enabled:
        validate_credential_backend(settings)
    return {"status": "ok", "authority_enabled": settings.authority_enabled}


@app.post("/v1/backtest-preflight")
def backtest_preflight(_identity: str = Depends(_backtest_identity)) -> dict:
    _rate_limit("preflight:backtest", 10, 60)
    return {"status": "ok", "authority_enabled": settings.authority_enabled}


@app.post("/v1/paper-preflight")
def paper_preflight(_identity: str = Depends(_paper_identity)) -> dict:
    slots = _preflight_slots if getattr(settings, "authority_enabled", False) else _quote_slots
    if not slots.acquire(blocking=False):
        raise HTTPException(429, "시세 요청이 많습니다. 잠시 후 다시 시도하세요")
    deadline = time.monotonic() + settings.quote_deadline_seconds
    try:
        _rate_limit("preflight:paper", 10, 60)
        if not settings.authority_enabled:
            validate_credential_backend(settings, purposes=("market",))
        if settings.quote_provider == "kis" and not settings.authority_enabled:
            _shared_kis_quotes(
                KisCredentials(
                    api_key=provider_secret(settings, "broker_key", timeout_seconds=deadline - time.monotonic()),
                    api_secret=provider_secret(settings, "broker_secret", timeout_seconds=deadline - time.monotonic()),
                    account_id=settings.broker_account_id,
                    paper=settings.kis_environment == "paper",
                ),
                (),
                deadline=deadline,
            )
        return {
            "status": "ok",
            "authority_enabled": settings.authority_enabled,
            "quote_provider": settings.quote_provider,
            "sharing_allowed": settings.market_data_sharing_allowed,
            "environment": settings.kis_environment,
            "transport": settings.kis_quote_transport,
            "max_batch_size": settings.shared_quote_batch_size,
            "max_symbols_per_tick": settings.shared_quote_max_symbols_per_tick,
            "quote_interval_seconds": settings.quote_interval_seconds,
            "tick_deadline_seconds": settings.shared_quote_tick_deadline_seconds,
            "max_age_seconds": settings.quote_max_age_seconds,
        }
    except Exception as exc:
        raise _safe_failure(exc) from None
    finally:
        slots.release()


@app.post("/v1/ai/catalog")
def ai_catalog(_identity: str = Depends(_app_identity)) -> dict:
    if not member_ai_credentials_enabled(settings):
        provider, model = validate_provider_model(
            settings.shared_ai_provider, settings.shared_ai_model
        )
        ready = True
        if provider == "local":
            ready = settings.local_ai_enabled and local_ai_ready(
                base_url=settings.local_ai_base_url,
                model=settings.local_ai_model,
                api_key=settings.local_ai_api_key,
            )
        entry = next(
            item
            for item in provider_catalog(settings, local_ready=ready)
            if item["id"] == provider
        )
        entry.update(
            default_model=model,
            model_examples=[model],
            requires_api_key=False,
            available=settings.shared_ai_enabled,
            ready=(
                settings.shared_ai_enabled
                and ready
                and (
                    provider == "local"
                    or time.monotonic() < _shared_ai_verified_until
                )
            ),
            provider_verified=(provider == "local" and ready)
            or time.monotonic() < _shared_ai_verified_until,
            managed_by="club_server",
        )
        return {"providers": [entry]}
    ready = settings.local_ai_enabled and local_ai_ready(
        base_url=settings.local_ai_base_url,
        model=settings.local_ai_model,
        api_key=settings.local_ai_api_key,
    )
    return {"providers": provider_catalog(settings, local_ready=ready)}


@_member_post("/v1/ai/encrypt")
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


@_member_post("/v1/ai/validate")
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


@_member_post("/v1/ai/generate")
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


@app.post("/v1/ai/shared-generate")
def shared_ai_generate(
    body: SharedAiGenerateBody, _identity: str = Depends(_app_identity)
) -> dict:
    global _shared_ai_verified_until
    acquired = False
    deadline = time.monotonic() + settings.ai_timeout_seconds
    try:
        if getattr(settings, "authority_enabled", False):
            from .authority import consume_ai_permit
            from .database import SessionLocal
            if body.permit is None:
                raise HTTPException(403, "회원 요청 권한이 필요합니다")
            with SessionLocal() as session:
                consume_ai_permit(session, raw_permit=body.permit.get_secret_value(), prompt=body.prompt)
        acquired = _ai_slots.acquire(blocking=False)
        if not acquired:
            raise HTTPException(
                status_code=429,
                detail="AI 요청이 많습니다. 잠시 후 다시 시도해 주세요",
            )
        _rate_limit("shared-ai-generate", _tenant_limit(10), 3600)
        if not settings.shared_ai_enabled:
            raise RuntimeError("동아리 공용 AI가 비활성화되어 있습니다")
        provider, model = validate_provider_model(
            settings.shared_ai_provider, settings.shared_ai_model
        )
        if provider == "local":
            if not settings.local_ai_enabled:
                raise RuntimeError("로컬 AI 서버가 비활성화되어 있습니다")
            api_key = settings.local_ai_api_key
            local_base_url = settings.local_ai_base_url
        else:
            api_key = validate_api_key(provider_secret(
                settings, "shared_ai", timeout_seconds=deadline - time.monotonic()
            ))
            local_base_url = None
        spec, preview = generate_strategy(
            body.prompt,
            provider=provider,
            model=model,
            api_key=api_key,
            timeout_seconds=max(0.001, deadline - time.monotonic()),
            local_base_url=local_base_url,
        )
        _shared_ai_verified_until = time.monotonic() + 300.0
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


@_member_post("/v1/market/validate", market=True)
def market_validate(body: MarketCipherBody, _identity: str = Depends(_app_identity)) -> dict:
    try:
        _rate_limit("validate:global", _tenant_limit(20), 3600)
        _market_plaintext(body)
        return {"status": "ok"}
    except Exception as exc:
        raise _safe_failure(exc) from None


@_member_post("/v1/market/prepare", market=True)
def market_prepare(body: MarketPrepareBody, _identity: str = Depends(_app_identity)) -> dict:
    _rate_limit("market-prepare:global", _tenant_limit(10), 3600)
    _rate_limit("market-prepare:" + body.owner_id, 10, 3600)
    if settings.production:
        if not _verification_slots.acquire(blocking=False):
            raise HTTPException(429, "시세 API 인증 요청이 많습니다")
        try:
            payload = body.model_dump(mode="json")
            for field in ("api_key", "api_secret"):
                value = getattr(body, field)
                payload[field] = value.get_secret_value() if value else None
            return _network_call("prepare", payload, time.monotonic() + settings.quote_deadline_seconds)
        except Exception as exc:
            raise _safe_failure(exc) from None
        finally:
            _verification_slots.release()
    return _market_prepare_inline(body)


def _market_prepare_inline(body: MarketPrepareBody) -> dict:
    try:
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
    credentials: KisCredentials,
    tickers: tuple[str, ...],
    *,
    source: str,
    client: KisQuoteClient | None = None,
    deadline: float | None = None,
) -> list[BrokerQuote]:
    deadline = deadline if deadline is not None else time.monotonic() + settings.quote_deadline_seconds
    if client is None:
        client = KisQuoteClient(
            credentials,
            deadline_monotonic=deadline,
            max_provider_calls=settings.quote_max_provider_calls,
        )
    else:
        client.deadline_monotonic = deadline
        client.max_provider_calls = settings.quote_max_provider_calls
        client.provider_calls = 0
    if not client.token and not client.connect():
        raise RuntimeError("KIS quote provider connection failed")
    values = []
    for ticker in tickers:
        try:
            raw = client.get_quote(ticker)
        except KisWorkBudgetExceeded:
            break
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
        if time.monotonic() >= deadline:
            break
        time.sleep(min(0.08, max(0.0, deadline - time.monotonic())))
    return values


def _shared_kis_quotes(
    credentials: KisCredentials, tickers: tuple[str, ...], *, deadline: float | None = None,
) -> list[BrokerQuote]:
    deadline = deadline if deadline is not None else time.monotonic() + settings.quote_deadline_seconds
    if settings.production:
        result = _network_call("shared", {"api_key": credentials.api_key, "api_secret": credentials.api_secret,
            "paper": credentials.paper, "account_id": credentials.account_id, "tickers": tickers}, deadline)
        return _network_quotes(result)
    return _shared_kis_quotes_inline(credentials, tickers, deadline=deadline)


def _shared_kis_quotes_inline(
    credentials: KisCredentials, tickers: tuple[str, ...], *, deadline: float | None = None,
) -> list[BrokerQuote]:
    """Reuse the one operator-owned OAuth session without concurrent mutation."""

    global _shared_kis_client, _shared_kis_identity
    identity = (credentials.api_key, credentials.api_secret, credentials.paper)
    deadline = deadline if deadline is not None else time.monotonic() + settings.quote_deadline_seconds
    if not _shared_kis_lock.acquire(timeout=max(0.0, deadline - time.monotonic())):
        raise KisWorkBudgetExceeded("KIS request deadline was exhausted")
    try:
        if _shared_kis_client is None or _shared_kis_identity != identity:
            _shared_kis_client = KisQuoteClient(credentials)
            _shared_kis_identity = identity
        return _kis_quotes(
            credentials,
            tickers,
            source="kis",
            client=_shared_kis_client,
            deadline=deadline,
        )
    finally:
        _shared_kis_lock.release()


def _member_quotes(body: MarketCipherBody, tickers: tuple[str, ...]) -> list[BrokerQuote]:
    if settings.production:
        return _network_quotes(_network_call("member", {"credential": body.model_dump(mode="json"), "tickers": tickers},
                                            time.monotonic() + settings.quote_deadline_seconds))
    return _member_quotes_inline(body, tickers)


def _member_quotes_inline(body: MarketCipherBody, tickers: tuple[str, ...]) -> list[BrokerQuote]:
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


@_member_post("/v1/market/quotes", market=True)
def market_quotes(body: MarketQuotesBody, _identity: str = Depends(_paper_identity)) -> dict:
    acquired = False
    try:
        _rate_limit("market-quotes:global", _tenant_limit(4), 60)
        _rate_limit("market-quotes:" + body.owner_id, 4, 60)
        acquired = _quote_slots.acquire(blocking=False)
        if not acquired:
            raise HTTPException(
                status_code=429,
                detail="시세 요청이 많습니다. 잠시 후 다시 시도하세요",
            )
        values = _member_quotes(body, _normalized_tickers(body.tickers))
        return _quote_payload(values)
    except Exception as exc:
        raise _safe_failure(exc) from None
    finally:
        if acquired:
            _quote_slots.release()


@app.post("/v1/market/shared-quotes")
def shared_quotes(body: SharedQuotesBody, _identity: str = Depends(_paper_identity)) -> dict:
    acquired = False
    deadline = time.monotonic() + settings.quote_deadline_seconds
    try:
        if settings.authority_enabled:
            raise HTTPException(403, "발급된 작업을 통해 시세를 요청하세요")
        acquired = _quote_slots.acquire(blocking=False)
        if not acquired:
            raise HTTPException(
                status_code=429,
                detail="시세 요청이 많습니다. 잠시 후 다시 시도하세요",
            )
        _rate_limit("shared-quotes", _shared_quote_rate_budget(), 60)
        if settings.quote_provider != "kis" or not settings.market_data_sharing_allowed:
            raise ValueError("공용 KIS 시세가 활성화되지 않았습니다")
        credentials = KisCredentials(
            api_key=provider_secret(settings, "broker_key", timeout_seconds=deadline - time.monotonic()),
            api_secret=provider_secret(settings, "broker_secret", timeout_seconds=deadline - time.monotonic()),
            account_id=settings.broker_account_id,
            paper=settings.kis_environment == "paper",
        )
        tickers = _normalized_tickers(
            body.tickers, maximum=settings.shared_quote_batch_size
        )
        return _quote_payload(_shared_kis_quotes(credentials, tickers, deadline=deadline))
    except Exception as exc:
        raise _safe_failure(exc) from None
    finally:
        if acquired:
            _quote_slots.release()


@app.exception_handler(RequestValidationError)
def invalid_request(_request: Request, _error: RequestValidationError):
    # Pydantic's default JSON contains the rejected input, including API keys.
    return JSONResponse(status_code=422, content={"detail": "요청 형식이 올바르지 않습니다"})


@app.middleware("http")
async def broker_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.update({
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'none'; script-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
    })
    return response


from .authority_routes import install_authority_routes


def _network_execute(payload, configuration):
    global settings
    settings = configuration
    operation, body, deadline = payload["operation"], payload["body"], payload["deadline"]
    if operation == "kms-preflight":
        validate_credential_backend(settings)
        return {"status": "ok"}
    if operation == "prepare":
        return _market_prepare_inline(MarketPrepareBody.model_validate(body))
    if operation == "shared":
        values = _shared_kis_quotes_inline(KisCredentials(api_key=body["api_key"], api_secret=body["api_secret"],
            paper=body["paper"], account_id=body["account_id"]), tuple(body["tickers"]), deadline=deadline)
    elif operation == "member":
        values = _member_quotes_inline(MarketCipherBody.model_validate(body["credential"]), tuple(body["tickers"]))
    else:
        raise ValueError("unsupported provider operation")
    return _quote_payload(values)


_network_pools = {
    "kms-preflight": [ProviderProcess(_network_execute)],
    "shared": [ProviderProcess(_network_execute)],
    "member": [ProviderProcess(_network_execute) for _ in range(settings.quote_max_concurrent_requests)],
    "prepare": [ProviderProcess(_network_execute) for _ in range(2)],
}
_network_next = defaultdict(int)
_network_pool_lock = threading.Lock()


def _network_call(operation, body, deadline):
    with _network_pool_lock:
        pool = _network_pools[operation]
        runner = pool[_network_next[operation] % len(pool)]
        _network_next[operation] += 1
    # Allow normal partial quote results to be encoded and delivered before the
    # hard parent deadline. A slow body still causes the child to be killed.
    margin = min(.5, max(0, deadline - time.monotonic()) * .25)
    return runner.run({"operation": operation, "body": body, "deadline": deadline - margin}, settings, deadline=deadline)


def _network_quotes(payload):
    return [BrokerQuote(**{**item, "observed_at": dt.datetime.fromisoformat(item["observed_at"])}) for item in payload["quotes"]]


@app.on_event("shutdown")
def close_provider_processes():
    for pool in _network_pools.values():
        for runner in pool:
            runner.close()

install_authority_routes(app, settings, _app_identity, market_prepare, MarketPrepareBody)

from .work_routes import install_work_routes

install_work_routes(app, settings, _paper_identity, _backtest_identity,
                    _member_quotes, MarketCipherBody, _quote_slots, _safe_failure)
