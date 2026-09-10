"""Narrow client for the credential/provider-operation trust boundary.

The public app and paper worker can request fixed provider operations, but this
module intentionally exposes no generic decrypt or proxy primitive.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import math
import secrets
import threading
import time
from urllib.parse import urlsplit

import httpx

from .config import Settings
from .bounded_io import ResponseTooLarge, read_httpx_json
from .paper import QuoteValue
from .strategies import StrategySpec


_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_catalog_condition = threading.Condition()
_catalog_cache: dict[str, object] = {
    "key": None,
    "expires_at": 0.0,
    "providers": (),
    "probing": False,
}


class CredentialBrokerError(RuntimeError):
    def __init__(self, detail: str, status_code: int = 503):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _broker_origin(settings: Settings) -> str:
    origin = getattr(settings, "credential_broker_url", "").rstrip("/")
    parsed = urlsplit(origin)
    allowed_schemes = {"https"} if bool(getattr(settings, "production", False)) else {"http", "https"}
    if (
        parsed.scheme not in allowed_schemes
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise CredentialBrokerError("자격증명 서비스 주소가 올바르지 않습니다")
    return origin


def _token(settings: Settings, role: str) -> str:
    if role == "app":
        value = getattr(settings, "credential_broker_app_token", "")
    elif role == "paper":
        value = getattr(settings, "credential_broker_paper_token", "")
    elif role == "backtest":
        value = getattr(settings, "credential_broker_backtest_token", "")
    else:  # pragma: no cover - internal programming guard
        raise ValueError("unsupported credential broker role")
    if not value:
        raise CredentialBrokerError("자격증명 서비스 인증이 설정되지 않았습니다")
    return value


def _request(
    settings: Settings,
    role: str,
    path: str,
    payload: dict,
    *,
    timeout_seconds: float = 30.0,
) -> dict:
    try:
        with httpx.stream(
            "POST",
            _broker_origin(settings) + path,
            headers={
                "Authorization": "Bearer " + _token(settings, role),
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout_seconds,
            trust_env=False,
        ) as response:
            status_code = response.status_code
            result = read_httpx_json(
                response, maximum_bytes=_MAX_RESPONSE_BYTES
            )
    except (httpx.RequestError, ResponseTooLarge, ValueError):
        raise CredentialBrokerError("자격증명 서비스에 연결할 수 없습니다") from None
    if status_code >= 400:
        safe_status = status_code if status_code in {401, 403, 409, 422, 429, 502, 503} else 503
        detail = "자격증명 서비스 요청에 실패했습니다"
        try:
            candidate = result.get("detail")
            if isinstance(candidate, str) and 0 < len(candidate) <= 300:
                detail = candidate
        except (AttributeError, TypeError, ValueError):
            pass
        raise CredentialBrokerError(detail, safe_status)
    if not isinstance(result, dict):
        raise CredentialBrokerError("자격증명 서비스 응답이 올바르지 않습니다")
    return result


def broker_preflight(settings: Settings, role: str) -> None:
    path = {"app": "/v1/preflight", "paper": "/v1/paper-preflight", "backtest": "/v1/backtest-preflight"}[role]
    result = _request(settings, role, path, {})
    if result.get("status") != "ok":
        raise CredentialBrokerError("자격증명 서비스 사전 점검에 실패했습니다")
    if getattr(settings, "authority_enabled", False) and not result.get("authority_enabled"):
        raise CredentialBrokerError("독립 인증 서비스 설정이 일치하지 않습니다")
    if role == "paper":
        expected = {
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
        if any(result.get(key) != value for key, value in expected.items()):
            raise CredentialBrokerError(
                "paper worker와 broker의 공용 시세 설정이 일치하지 않습니다"
            )


def broker_auth(settings: Settings, operation: str, payload: dict) -> dict:
    if operation not in {"register", "login", "logout"}:
        raise ValueError("unsupported authentication operation")
    return _request(settings, "app", "/v1/auth/" + operation, payload, timeout_seconds=15)


def broker_validate_ai(
    settings: Settings, *, owner_id: str, provider: str, ciphertext: str
) -> None:
    _request(
        settings,
        "app",
        "/v1/ai/validate",
        {"owner_id": owner_id, "provider": provider, "ciphertext": ciphertext},
    )


def broker_encrypt_ai(
    settings: Settings, *, owner_id: str, provider: str, api_key: str
) -> tuple[str, str]:
    result = _request(
        settings,
        "app",
        "/v1/ai/encrypt",
        {"owner_id": owner_id, "provider": provider, "api_key": api_key},
    )
    ciphertext = result.get("ciphertext")
    hint = result.get("key_hint")
    if not isinstance(ciphertext, str) or not ciphertext.startswith("v3:oci-kms:"):
        raise CredentialBrokerError("자격증명 서비스가 잘못된 암호문을 반환했습니다")
    if not isinstance(hint, str) or len(hint) > 12:
        raise CredentialBrokerError("자격증명 서비스가 잘못된 힌트를 반환했습니다")
    return ciphertext, hint


def broker_ai_catalog(settings: Settings) -> list[dict]:
    key = (
        _broker_origin(settings),
        hashlib.sha256(_token(settings, "app").encode("utf-8")).digest(),
    )
    now = time.monotonic()
    with _catalog_condition:
        if _catalog_cache["key"] == key and now < float(
            _catalog_cache["expires_at"]
        ):
            return [dict(item) for item in _catalog_cache["providers"]]
        if _catalog_cache["key"] == key and _catalog_cache["probing"]:
            _catalog_condition.wait(timeout=2.5)
            cached = _catalog_cache["providers"]
            if cached:
                return [dict(item) for item in cached]
            raise CredentialBrokerError("자격증명 서비스 상태 확인이 진행 중입니다")
        stale = (
            tuple(_catalog_cache["providers"])
            if _catalog_cache["key"] == key
            else ()
        )
        _catalog_cache.update(key=key, probing=True)
    try:
        result = _request(
            settings, "app", "/v1/ai/catalog", {}, timeout_seconds=2.0
        )
        catalog = result.get("providers")
        if not isinstance(catalog, list) or len(catalog) > 10 or any(
            not isinstance(item, dict) for item in catalog
        ):
            raise CredentialBrokerError("자격증명 서비스 공급자 목록이 올바르지 않습니다")
    except CredentialBrokerError:
        with _catalog_condition:
            _catalog_cache.update(probing=False, expires_at=time.monotonic() + 2.0)
            _catalog_condition.notify_all()
        if stale:
            return [dict(item) for item in stale]
        raise
    with _catalog_condition:
        _catalog_cache.update(
            key=key,
            providers=tuple(dict(item) for item in catalog),
            expires_at=time.monotonic() + 15.0,
            probing=False,
        )
        _catalog_condition.notify_all()
    return [dict(item) for item in catalog]


def broker_generate_strategy(
    settings: Settings,
    *,
    owner_id: str,
    provider: str,
    model: str,
    ciphertext: str,
    prompt: str,
) -> tuple[StrategySpec, str]:
    result = _request(
        settings,
        "app",
        "/v1/ai/generate",
        {
            "owner_id": owner_id,
            "provider": provider,
            "model": model,
            "ciphertext": ciphertext,
            "prompt": prompt,
        },
        timeout_seconds=float(settings.ai_timeout_seconds) + 10.0,
    )
    try:
        spec = StrategySpec.model_validate(result.get("spec"))
    except Exception:
        raise CredentialBrokerError("자격증명 서비스가 잘못된 전략을 반환했습니다", 502) from None
    preview = result.get("preview")
    if not isinstance(preview, str) or len(preview) > 20_000:
        raise CredentialBrokerError("자격증명 서비스가 잘못된 전략을 반환했습니다", 502)
    return spec, preview


def broker_generate_shared_strategy(
    settings: Settings, *, prompt: str, session_token: str = "", csrf: str = ""
) -> tuple[StrategySpec, str]:
    """Generate through the broker without exposing provider choice or credentials."""

    payload = {"prompt": prompt}
    if getattr(settings, "authority_enabled", False):
        permitted = _request(settings, "app", "/v1/permits/shared-ai", {
            "session_token": session_token, "csrf": csrf, "prompt": prompt,
            "nonce": secrets.token_urlsafe(24),
        })
        payload["permit"] = permitted.get("permit", "")
    result = _request(
        settings,
        "app",
        "/v1/ai/shared-generate",
        payload,
        timeout_seconds=float(settings.ai_timeout_seconds) + 10.0,
    )
    try:
        spec = StrategySpec.model_validate(result.get("spec"))
    except Exception:
        raise CredentialBrokerError(
            "자격증명 서비스가 잘못된 전략을 반환했습니다", 502
        ) from None
    preview = result.get("preview")
    if not isinstance(preview, str) or len(preview) > 20_000:
        raise CredentialBrokerError(
            "자격증명 서비스가 잘못된 전략을 반환했습니다", 502
        )
    return spec, preview


def broker_next_work(settings: Settings, role: str) -> dict | None:
    result = _request(settings, role, "/v1/work/" + role + "/next", {})
    work = result.get("work")
    if work is None:
        return None
    import re
    if (not isinstance(work, dict) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", str(work.get("claim", "")))
            or not re.fullmatch(r"[a-f0-9]{32}", str(work.get("resource_id", "")))):
        raise CredentialBrokerError("작업 권한 응답이 올바르지 않습니다")
    return work


def broker_complete_work(settings: Settings, role: str, claim: str) -> None:
    _request(settings, role, "/v1/work/" + role + "/complete", {"claim": claim})


def broker_work_quotes(settings: Settings, claim: str) -> None:
    _request(settings, "paper", "/v1/work/paper/quotes", {"claim": claim}, timeout_seconds=settings.quote_deadline_seconds + 5)


def broker_validate_market(
    settings: Settings,
    *,
    owner_id: str,
    provider: str,
    environment: str,
    encrypted_api_key: str,
    encrypted_api_secret: str,
) -> None:
    _request(
        settings,
        "app",
        "/v1/market/validate",
        {
            "owner_id": owner_id,
            "provider": provider,
            "environment": environment,
            "encrypted_api_key": encrypted_api_key,
            "encrypted_api_secret": encrypted_api_secret,
        },
    )


def broker_prepare_market(
    settings: Settings,
    *,
    owner_id: str,
    provider: str,
    environment: str,
    api_key: str,
    api_secret: str,
    current_provider: str | None,
    current_environment: str | None,
    current_encrypted_api_key: str | None,
    current_encrypted_api_secret: str | None,
) -> dict:
    result = _request(
        settings,
        "app",
        "/v1/market/prepare",
        {
            "owner_id": owner_id,
            "provider": provider,
            "environment": environment,
            "api_key": api_key or None,
            "api_secret": api_secret or None,
            "current_provider": current_provider,
            "current_environment": current_environment,
            "current_encrypted_api_key": current_encrypted_api_key,
            "current_encrypted_api_secret": current_encrypted_api_secret,
        },
        timeout_seconds=35.0,
    )
    for field in ("encrypted_api_key", "encrypted_api_secret"):
        if not isinstance(result.get(field), str) or not result[field].startswith("v3:oci-kms:"):
            raise CredentialBrokerError("자격증명 서비스가 잘못된 암호문을 반환했습니다")
    for field in ("key_hint", "secret_hint"):
        if not isinstance(result.get(field), str) or len(result[field]) > 12:
            raise CredentialBrokerError("자격증명 서비스가 잘못된 힌트를 반환했습니다")
    return result


def broker_member_quotes(
    settings: Settings,
    *,
    owner_id: str,
    provider: str,
    environment: str,
    encrypted_api_key: str,
    encrypted_api_secret: str,
    tickers: tuple[str, ...],
) -> list[QuoteValue]:
    result = _request(
        settings,
        "paper",
        "/v1/market/quotes",
        {
            "owner_id": owner_id,
            "provider": provider,
            "environment": environment,
            "encrypted_api_key": encrypted_api_key,
            "encrypted_api_secret": encrypted_api_secret,
            "tickers": list(tickers),
        },
        timeout_seconds=45.0,
    )
    return _validated_quotes(
        result,
        requested=tickers,
        allowed_sources={"kis_member", "toss_member"},
    )


def broker_shared_quotes(
    settings: Settings,
    *,
    tickers: tuple[str, ...],
    timeout_seconds: float = 45.0,
) -> list[QuoteValue]:
    result = _request(
        settings,
        "paper",
        "/v1/market/shared-quotes",
        {"tickers": list(tickers)},
        timeout_seconds=max(0.1, min(45.0, float(timeout_seconds))),
    )
    return _validated_quotes(result, requested=tickers, allowed_sources={"kis"})


def _validated_quotes(
    result: dict,
    *,
    requested: tuple[str, ...],
    allowed_sources: set[str],
) -> list[QuoteValue]:
    rows = result.get("quotes")
    if not isinstance(rows, list) or len(rows) > min(200, len(set(requested))):
        raise CredentialBrokerError("자격증명 서비스 시세 응답이 올바르지 않습니다")
    requested_set = set(requested)
    seen: set[str] = set()
    values = []
    try:
        for row in rows:
            ticker = str(row["ticker"])
            source = str(row["source"])
            price = float(row["price"])
            bid = float(row.get("bid", 0.0))
            ask = float(row.get("ask", 0.0))
            volume = float(row.get("volume", 0.0))
            observed_at = dt.datetime.fromisoformat(str(row["observed_at"]))
            if (
                ticker not in requested_set
                or ticker in seen
                or source not in allowed_sources
                or not math.isfinite(price)
                or price <= 0
                or any(not math.isfinite(value) or value < 0 for value in (bid, ask, volume))
                or observed_at.tzinfo is None
            ):
                raise ValueError("invalid normalized quote")
            seen.add(ticker)
            values.append(
                QuoteValue(
                    ticker=ticker,
                    price=price,
                    bid=bid,
                    ask=ask,
                    volume=volume,
                    source=source,
                    observed_at=observed_at.astimezone(dt.timezone.utc),
                )
            )
    except (KeyError, TypeError, ValueError):
        raise CredentialBrokerError("자격증명 서비스 시세 응답이 올바르지 않습니다", 502) from None
    return values
