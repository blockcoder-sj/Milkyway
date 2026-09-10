"""Minimal Korea Investment Securities client for shared US equity quotes."""

from __future__ import annotations

import datetime as dt
import logging
import time
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter

from .bounded_io import read_requests_json


logger = logging.getLogger("cloud_app.kis_quotes")
_MAX_TOKEN_RESPONSE_BYTES = 64 * 1024
_MAX_QUOTE_RESPONSE_BYTES = 256 * 1024


class KisQuoteError(RuntimeError):
    """Base error for quote failures that must be visible to the worker."""


class KisAuthenticationError(KisQuoteError):
    """The access token or member-owned credentials were rejected."""


class KisRateLimitError(KisQuoteError):
    """KIS rejected the request because a request limit was reached."""


class KisWorkBudgetExceeded(KisQuoteError):
    """The bounded wall-clock or provider-call budget was consumed."""


@dataclass(frozen=True)
class KisCredentials:
    api_key: str
    api_secret: str
    account_id: str = ""
    paper: bool = True


class KisQuoteClient:
    """Quote-only KIS client; it cannot submit or manage brokerage orders."""

    _exchange_codes = ("NAS", "NYS", "AMS")

    def __init__(
        self,
        credentials: KisCredentials,
        *,
        deadline_monotonic: float | None = None,
        max_provider_calls: int | None = None,
    ):
        if not credentials.api_key or not credentials.api_secret:
            raise RuntimeError("KIS quote credentials are incomplete")
        self.credentials = credentials
        self.base_url = (
            "https://openapivts.koreainvestment.com:29443"
            if credentials.paper
            else "https://openapi.koreainvestment.com:9443"
        )
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=8)
        self.session.mount("https://", adapter)
        self.token = ""
        self.token_expires_at = dt.datetime.min
        self.exchange_cache: dict[str, str] = {}
        self.deadline_monotonic = deadline_monotonic
        self.max_provider_calls = max_provider_calls
        self.provider_calls = 0

    def _consume_provider_call(self) -> None:
        if (
            self.max_provider_calls is not None
            and self.provider_calls >= self.max_provider_calls
        ):
            raise KisWorkBudgetExceeded("KIS provider-call budget was exhausted")
        if self.deadline_monotonic is not None and time.monotonic() >= self.deadline_monotonic:
            raise KisWorkBudgetExceeded("KIS request deadline was exhausted")
        self.provider_calls += 1

    def _request_timeout(self) -> float:
        if self.deadline_monotonic is None:
            return 10.0
        remaining = self.deadline_monotonic - time.monotonic()
        if remaining <= 0:
            raise KisWorkBudgetExceeded("KIS request deadline was exhausted")
        return max(0.001, min(10.0, remaining))

    @staticmethod
    def _raise_for_rejection(response, payload: dict | None = None) -> None:
        if response.status_code in {401, 403}:
            raise KisAuthenticationError("KIS authentication was rejected")
        if response.status_code == 429:
            raise KisRateLimitError("KIS request limit was reached")
        response.raise_for_status()
        if payload is None or str(payload.get("rt_cd", "0")) == "0":
            return
        code = str(payload.get("msg_cd", ""))
        message = str(payload.get("msg1", ""))
        detail = "{} {}".format(code, message).upper()
        if any(
            marker in detail
            for marker in ("EGW00201", "RATE LIMIT", "TOO MANY", "초당", "호출 제한")
        ):
            raise KisRateLimitError("KIS request limit was reached")
        if any(
            marker in detail
            for marker in ("EGW00121", "EGW00123", "TOKEN", "AUTH", "인증")
        ):
            raise KisAuthenticationError("KIS authentication was rejected")
        raise KisQuoteError("KIS quote request was rejected ({})".format(code or "unknown"))

    def _refresh_token(self) -> None:
        self._consume_provider_call()
        response = self.session.post(
            self.base_url + "/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self.credentials.api_key,
                "appsecret": self.credentials.api_secret,
            },
            timeout=self._request_timeout(),
            stream=True,
        )
        try:
            self._raise_for_rejection(response)
            payload = read_requests_json(
                response, maximum_bytes=_MAX_TOKEN_RESPONSE_BYTES
            )
        except Exception:
            response.close()
            raise
        self._raise_for_rejection(response, payload)
        try:
            self.token = payload["access_token"]
        except (KeyError, TypeError) as exc:
            raise KisAuthenticationError("KIS access token was not returned") from exc
        self.token_expires_at = dt.datetime.now() + dt.timedelta(hours=23)

    def connect(self) -> bool:
        try:
            self._refresh_token()
            return True
        except KisWorkBudgetExceeded:
            raise
        except (KisQuoteError, requests.RequestException, TypeError, ValueError) as exc:
            logger.error("KIS token request failed: %s", type(exc).__name__)
            return False

    def _headers(self) -> dict[str, str]:
        if not self.token or dt.datetime.now() >= self.token_expires_at:
            self._refresh_token()
        return {
            "authorization": "Bearer " + self.token,
            "appkey": self.credentials.api_key,
            "appsecret": self.credentials.api_secret,
            "tr_id": "HHDFS00000300",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _request_quote(self, ticker: str, exchange_code: str) -> dict | None:
        headers = self._headers()
        self._consume_provider_call()
        response = self.session.get(
            self.base_url + "/uapi/overseas-price/v1/quotations/price",
            headers=headers,
            params={"AUTH": "", "EXCD": exchange_code, "SYMB": ticker},
            timeout=self._request_timeout(),
            stream=True,
        )
        try:
            self._raise_for_rejection(response)
            payload = read_requests_json(
                response, maximum_bytes=_MAX_QUOTE_RESPONSE_BYTES
            )
        except Exception:
            response.close()
            raise
        self._raise_for_rejection(response, payload)
        output = payload.get("output", {})
        price = float(output.get("last", 0) or 0)
        if price <= 0:
            return None
        return {
            "price": price,
            "bid": float(output.get("bidp", 0) or 0),
            "ask": float(output.get("askp", 0) or 0),
            "volume": int(float(output.get("tvol", 0) or 0)),
        }

    def get_quote(self, ticker: str) -> dict:
        ticker = ticker.strip().upper()
        candidates = []
        cached = self.exchange_cache.get(ticker)
        if cached:
            candidates.append(cached)
        candidates.extend(code for code in self._exchange_codes if code != cached)
        last_error: Exception | None = None
        authentication_retried = False
        for exchange_code in candidates:
            while True:
                try:
                    quote = self._request_quote(ticker, exchange_code)
                    break
                except KisAuthenticationError:
                    if authentication_retried:
                        raise
                    authentication_retried = True
                    self.token = ""
                    self.token_expires_at = dt.datetime.min
                    self._refresh_token()
                except KisRateLimitError:
                    raise
                except KisWorkBudgetExceeded:
                    raise
                except (KisQuoteError, requests.RequestException) as exc:
                    last_error = exc
                    logger.warning(
                        "KIS quote failed ticker=%s exchange=%s error=%s",
                        ticker,
                        exchange_code,
                        type(exc).__name__,
                    )
                    quote = None
                    break
            if quote:
                self.exchange_cache[ticker] = exchange_code
                return quote
        if last_error is not None:
            raise KisQuoteError("KIS quote lookup failed for {}".format(ticker)) from last_error
        return {"price": 0, "bid": 0, "ask": 0, "volume": 0}
