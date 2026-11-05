"""Quote-only client for the Toss Securities Open API."""

from __future__ import annotations

import datetime as dt
import logging
import math
import re
from dataclasses import dataclass
from typing import Iterable

import requests
from requests.adapters import HTTPAdapter

from .bounded_io import read_requests_json


logger = logging.getLogger("cloud_app.toss_quotes")
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]+$")
_MAX_TOKEN_RESPONSE_BYTES = 64 * 1024
_MAX_QUOTE_RESPONSE_BYTES = 512 * 1024


class TossOpenApiError(RuntimeError):
    """Base error for failures that must be visible to the paper worker."""


class TossAuthenticationError(TossOpenApiError):
    """The client credentials or access token were rejected."""


class TossIpNotAllowedError(TossOpenApiError):
    """The calling server IP is not registered in Toss Securities WTS."""


class TossPermissionError(TossOpenApiError):
    """The API denied access; this alone is not proof of an IP mismatch."""


class TossEdgeBlockedError(TossOpenApiError):
    """The provider's edge rejected the request format or delivery path."""


class TossRateLimitError(TossOpenApiError):
    """The client-specific Toss Open API rate limit was reached."""

    def __init__(self, retry_after: float = 1.0):
        super().__init__("Toss Open API request limit was reached")
        self.retry_after = max(1.0, retry_after)


def provider_error_text(error):
    if isinstance(error, TossIpNotAllowedError):
        return "토스 허용 IP 불일치입니다. 실제 API를 실행하는 PC의 공인 IP를 WTS에 등록하세요"
    if isinstance(error, TossEdgeBlockedError):
        return "토스가 요청 형식·접속 경로를 거부했습니다 (edge-blocked). IP 차단으로 확정할 수 없습니다"
    if isinstance(error, TossPermissionError):
        return "토스 API 접근 권한이 거부되었습니다 (403). 키 활성 상태와 이용 권한을 확인하세요"
    if isinstance(error, TossAuthenticationError):
        return "토스 인증이 거부되었습니다. 최신 Client ID·Secret을 저장하고 같은 키를 쓰는 다른 PC·프로그램의 중복 실행을 확인하세요"
    if isinstance(error, TossRateLimitError):
        return "토스 요청 한도 초과입니다. 자동 재시도 대기 중입니다"
    return "토스 API 수신에 실패했습니다. 연결 상태와 로컬 토큰 공유 파일의 접근 권한을 확인하세요"


@dataclass(frozen=True)
class TossCredentials:
    client_id: str
    client_secret: str


class TossQuoteClient:
    """OAuth client for KR/US quotes; this class contains no order methods."""

    base_url = "https://openapi.tossinvest.com"
    max_symbols_per_request = 200

    def __init__(self, credentials: TossCredentials):
        if not credentials.client_id or not credentials.client_secret:
            raise TossAuthenticationError("Toss Open API credentials are incomplete")
        self.credentials = credentials
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=8)
        self.session.mount("https://", adapter)
        self.token = ""
        self.token_expires_at = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
        from .toss_token_cache import personal_token_cache
        self.shared_token = personal_token_cache(credentials, self.base_url)

    @staticmethod
    def _error_code(payload: dict | None) -> str:
        if not isinstance(payload, dict):
            return ""
        error = payload.get("error")
        if isinstance(error, dict):
            return str(error.get("code", ""))
        return str(error or "")

    @staticmethod
    def _retry_after(response) -> float:
        try:
            return float(response.headers.get("Retry-After", 1))
        except (TypeError, ValueError):
            return 1.0

    def _raise_for_status(self, response, payload: dict | None = None) -> None:
        code = self._error_code(payload)
        safe_code = code if re.fullmatch(r"[a-z0-9_-]{1,64}", code) else "HTTP " + str(response.status_code)
        if code in {"ip-not-allowed", "access_denied"}:
            raise TossIpNotAllowedError("Toss rejected the request IP (" + code + ")")
        if response.status_code == 401 or code in {"invalid-token", "expired-token", "token-revoked", "invalid_client"}:
            raise TossAuthenticationError("Toss authentication rejected (" + safe_code + ")")
        if code == "edge-blocked":
            raise TossEdgeBlockedError("Toss edge rejected the request (edge-blocked)")
        if response.status_code == 403:
            raise TossPermissionError("Toss access denied (" + safe_code + ")")
        if response.status_code == 429 or code in {"edge-rate-limit-exceeded", "rate-limit-exceeded"}:
            raise TossRateLimitError(self._retry_after(response))
        response.raise_for_status()
        if code:
            raise TossOpenApiError("Toss API request rejected")

    def _response_json(self, response, *, maximum_bytes):
        # Read the bounded error envelope before classifying it. 403 alone can
        # mean IP, WAF/edge, or permission; never label all of them IP blocking.
        try:
            payload = read_requests_json(response, maximum_bytes=maximum_bytes)
        except (ValueError, UnicodeError):
            self._raise_for_status(response)
            raise TossOpenApiError("Toss response is not valid JSON") from None
        self._raise_for_status(response, payload)
        if not isinstance(payload, dict):
            raise TossOpenApiError("Toss response must be an object")
        return payload

    def _issue_token(self):
        response = self.session.post(
            self.base_url + "/oauth2/token",
            data={"grant_type":"client_credentials", "client_id":self.credentials.client_id,
                  "client_secret":self.credentials.client_secret}, timeout=10, stream=True,
        )
        try:
            payload = self._response_json(response, maximum_bytes=_MAX_TOKEN_RESPONSE_BYTES)
        finally:
            response.close()
        try:
            token = payload["access_token"]
            lifetime = int(payload.get("expires_in", 86400))
            if not isinstance(token, str) or not 1 <= len(token) <= 32768 or not 1 <= lifetime <= 172800:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise TossAuthenticationError("Toss returned an invalid access token") from None
        margin = min(60, lifetime / 10)
        return token, dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=max(1, lifetime-margin))

    def authenticate(self, *, rejected_token=None, force=False) -> None:
        if self.shared_token is None:
            self.token, self.token_expires_at = self._issue_token()
        else:
            try:
                self.token, self.token_expires_at = self.shared_token.obtain(self._issue_token, rejected=rejected_token, force=force)
            except (OSError, ValueError, TimeoutError):
                raise TossOpenApiError("Local Toss token coordination is unavailable") from None

    def _refresh_rejected_token(self, rejected):
        if self.shared_token is not None:
            self.authenticate(rejected_token=rejected)
        else:
            self.token = ""
            self.token_expires_at = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
            self.authenticate()

    def connect(self) -> bool:
        try:
            self.authenticate()
            return True
        except (TossOpenApiError, requests.RequestException, TypeError, ValueError) as exc:
            logger.error("Toss Open API token request failed: %s", type(exc).__name__)
            return False

    def _headers(self) -> dict[str, str]:
        if self.shared_token is not None or not self.token or dt.datetime.now(dt.timezone.utc) >= self.token_expires_at:
            self.authenticate()
        return {"Authorization": "Bearer " + self.token, "Accept": "application/json"}

    @staticmethod
    def _observed_at(value: str) -> dt.datetime:
        try:
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError) as exc:
            raise TossOpenApiError("Toss quote timestamp is invalid") from exc
        if parsed.tzinfo is None:
            raise TossOpenApiError("Toss quote timestamp has no timezone")
        return parsed.astimezone(dt.timezone.utc)

    @staticmethod
    def _normalize_symbols(tickers: Iterable[str]) -> list[str]:
        symbols = sorted(
            {
                ticker.strip().upper()
                for ticker in tickers
                if isinstance(ticker, str) and ticker.strip()
            }
        )
        invalid = [symbol for symbol in symbols if not _SYMBOL_PATTERN.fullmatch(symbol)]
        for symbol in invalid:
            logger.warning("Toss quote skipped ticker=%s reason=invalid-symbol", symbol)
        return [symbol for symbol in symbols if symbol not in invalid]

    def get_json(self, path, params, *, maximum_bytes=64*1024):
        if path not in {"/api/v1/prices", "/api/v1/market-indicators/prices", "/api/v1/exchange-rate"}:
            raise ValueError("Unsupported quote-only endpoint")
        for attempt in range(2):
            headers = self._headers()
            response = self.session.get(self.base_url + path, params=params, headers=headers, stream=True, timeout=(3, 5))
            try:
                return self._response_json(response, maximum_bytes=maximum_bytes)
            except TossAuthenticationError:
                if attempt: raise
                self._refresh_rejected_token(headers["Authorization"].removeprefix("Bearer "))
            finally:
                response.close()

    def _request_batch(self, symbols: list[str]) -> list[dict]:
        authentication_retried = False
        while True:
            headers = self._headers()
            response = self.session.get(
                self.base_url + "/api/v1/prices",
                headers=headers,
                params={"symbols": ",".join(symbols)},
                timeout=10,
                stream=True,
            )
            try:
                payload = self._response_json(response, maximum_bytes=_MAX_QUOTE_RESPONSE_BYTES)
                result = payload.get("result")
                if not isinstance(result, list):
                    raise TossOpenApiError("Toss quote response has no result list")
                return result
            except TossAuthenticationError:
                response.close()
                if authentication_retried:
                    raise
                authentication_retried = True
                self._refresh_rejected_token(headers["Authorization"].removeprefix("Bearer "))
            except Exception:
                response.close()
                raise

    def daily_candles(self, symbol: str, *, count: int = 320) -> list[list]:
        """Bounded adjusted daily pages; inclusive cursors are de-duplicated."""
        if not _SYMBOL_PATTERN.fullmatch(symbol) or not 1 <= count <= 850:
            raise ValueError("Invalid daily candle request")
        rows, before, seen_cursors = {}, None, set()
        for _ in range(7):
            params = {"symbol": symbol, "interval": "1d", "count": min(200, count), "adjusted": "true"}
            if before: params["before"] = before
            for attempt in range(2):
                headers = self._headers()
                response = self.session.get(self.base_url + "/api/v1/candles", headers=headers,
                                            params=params, timeout=10, stream=True)
                try:
                    payload = self._response_json(response, maximum_bytes=_MAX_QUOTE_RESPONSE_BYTES)
                    result = payload.get("result")
                    if not isinstance(result, dict) or not isinstance(result.get("candles"), list) or len(result["candles"]) > 200:
                        raise TossOpenApiError("Invalid candle page")
                    break
                except TossAuthenticationError:
                    if attempt: raise
                    self._refresh_rejected_token(headers["Authorization"].removeprefix("Bearer "))
                finally:
                    response.close()
            for candle in result["candles"]:
                if candle.get("currency") != "USD":
                    raise TossOpenApiError("US history currency is not USD")
                self._observed_at(candle.get("timestamp"))
                # Daily API timestamps label sessions; preserve the source's
                # calendar-date label rather than shifting a midnight KST bar.
                day = dt.date.fromisoformat(candle["timestamp"][:10]).isoformat()
                row = [day, *[float(candle[key]) for key in ("openPrice", "highPrice", "lowPrice", "closePrice", "volume")]]
                if any(not math.isfinite(v) or v <= 0 for v in row[1:5]) or not math.isfinite(row[5]) or row[5] < 0:
                    raise TossOpenApiError("Invalid candle numeric value")
                if day in rows and rows[day] != row:
                    raise TossOpenApiError("Conflicting inclusive candle pages")
                rows[day] = row
            if len(rows) >= count or not result.get("nextBefore"):
                break
            cursor = result["nextBefore"]
            self._observed_at(cursor)
            if cursor in seen_cursors:
                raise TossOpenApiError("Candle pagination made no progress")
            seen_cursors.add(cursor); before = cursor
        return [rows[day] for day in sorted(rows)][-count:]

    def get_prices(self, tickers: Iterable[str]) -> list[dict]:
        symbols = self._normalize_symbols(tickers)
        quotes: list[dict] = []
        for offset in range(0, len(symbols), self.max_symbols_per_request):
            batch = symbols[offset : offset + self.max_symbols_per_request]
            for raw in self._request_batch(batch):
                symbol = str(raw.get("symbol", "")).strip().upper()
                if symbol not in batch:
                    continue
                try:
                    price = float(raw.get("lastPrice", 0) or 0)
                except (TypeError, ValueError):
                    logger.warning("Toss quote skipped ticker=%s reason=invalid-price", symbol)
                    continue
                if price <= 0:
                    continue
                timestamp = raw.get("timestamp")
                if timestamp is None:
                    logger.debug("Toss quote skipped ticker=%s reason=no-trade-timestamp", symbol)
                    continue
                try:
                    observed_at = self._observed_at(timestamp)
                except TossOpenApiError:
                    logger.warning("Toss quote skipped ticker=%s reason=invalid-timestamp", symbol)
                    continue
                quotes.append(
                    {
                        "ticker": symbol,
                        "price": price,
                        "bid": 0.0,
                        "ask": 0.0,
                        "volume": 0.0,
                        "observed_at": observed_at,
                    }
                )
        return quotes
