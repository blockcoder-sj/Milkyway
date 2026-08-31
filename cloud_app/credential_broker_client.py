"""Narrow client for the credential/provider-operation trust boundary.

The public app and paper worker can request fixed provider operations, but this
module intentionally exposes no generic decrypt or proxy primitive.
"""

from __future__ import annotations

import datetime as dt
import math
from urllib.parse import urlsplit

import httpx

from .config import Settings
from .paper import QuoteValue
from .strategies import StrategySpec


_MAX_RESPONSE_BYTES = 2 * 1024 * 1024


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
        response = httpx.post(
            _broker_origin(settings) + path,
            headers={
                "Authorization": "Bearer " + _token(settings, role),
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout_seconds,
            trust_env=False,
        )
    except httpx.RequestError:
        raise CredentialBrokerError("자격증명 서비스에 연결할 수 없습니다") from None
    if len(response.content) > _MAX_RESPONSE_BYTES:
        raise CredentialBrokerError("자격증명 서비스 응답이 허용 크기를 초과했습니다")
    if response.status_code >= 400:
        safe_status = response.status_code if response.status_code in {409, 422, 429, 502, 503} else 503
        detail = "자격증명 서비스 요청에 실패했습니다"
        try:
            candidate = response.json().get("detail")
            if isinstance(candidate, str) and 0 < len(candidate) <= 300:
                detail = candidate
        except (TypeError, ValueError):
            pass
        raise CredentialBrokerError(detail, safe_status)
    try:
        result = response.json()
    except ValueError:
        raise CredentialBrokerError("자격증명 서비스 응답이 올바르지 않습니다") from None
    if not isinstance(result, dict):
        raise CredentialBrokerError("자격증명 서비스 응답이 올바르지 않습니다")
    return result


def broker_preflight(settings: Settings, role: str) -> None:
    path = "/v1/preflight" if role == "app" else "/v1/paper-preflight"
    result = _request(settings, role, path, {})
    if result.get("status") != "ok":
        raise CredentialBrokerError("자격증명 서비스 사전 점검에 실패했습니다")


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
    result = _request(settings, "app", "/v1/ai/catalog", {})
    catalog = result.get("providers")
    if not isinstance(catalog, list) or len(catalog) > 10:
        raise CredentialBrokerError("자격증명 서비스 공급자 목록이 올바르지 않습니다")
    return catalog


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
    settings: Settings, *, tickers: tuple[str, ...]
) -> list[QuoteValue]:
    result = _request(
        settings,
        "paper",
        "/v1/market/shared-quotes",
        {"tickers": list(tickers)},
        timeout_seconds=45.0,
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
