"""Quote-only client for the Toss Securities Open API."""

from __future__ import annotations

import datetime as dt
import logging
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


class TossRateLimitError(TossOpenApiError):
    """The client-specific Toss Open API rate limit was reached."""

    def __init__(self, retry_after: float = 1.0):
        super().__init__("Toss Open API request limit was reached")
        self.retry_after = max(1.0, retry_after)


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
        if response.status_code == 401 or code in {"invalid-token", "expired-token"}:
            raise TossAuthenticationError("Toss Open API authentication was rejected")
        if response.status_code == 403:
            raise TossIpNotAllowedError("Toss Open API server IP is not allowed")
        if response.status_code == 429 or code in {
            "edge-rate-limit-exceeded",
            "rate-limit-exceeded",
        }:
            raise TossRateLimitError(self._retry_after(response))
        response.raise_for_status()
        if code:
            raise TossOpenApiError("Toss Open API request was rejected ({})".format(code))

    def authenticate(self) -> None:
        response = self.session.post(
            self.base_url + "/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
            },
            timeout=10,
            stream=True,
        )
        try:
            self._raise_for_status(response)
            payload = read_requests_json(
                response, maximum_bytes=_MAX_TOKEN_RESPONSE_BYTES
            )
        except Exception:
            response.close()
            raise
        self._raise_for_status(response, payload)
        try:
            token = str(payload["access_token"])
            expires_in = max(60, int(payload.get("expires_in", 86400)))
        except (KeyError, TypeError, ValueError) as exc:
            raise TossAuthenticationError("Toss Open API access token was not returned") from exc
        if not token:
            raise TossAuthenticationError("Toss Open API access token was empty")
        self.token = token
        self.token_expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            seconds=max(30, expires_in - 60)
        )

    def connect(self) -> bool:
        try:
            self.authenticate()
            return True
        except (TossOpenApiError, requests.RequestException, TypeError, ValueError) as exc:
            logger.error("Toss Open API token request failed: %s", type(exc).__name__)
            return False

    def _headers(self) -> dict[str, str]:
        if not self.token or dt.datetime.now(dt.timezone.utc) >= self.token_expires_at:
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

    def _request_batch(self, symbols: list[str]) -> list[dict]:
        authentication_retried = False
        while True:
            response = self.session.get(
                self.base_url + "/api/v1/prices",
                headers=self._headers(),
                params={"symbols": ",".join(symbols)},
                timeout=10,
                stream=True,
            )
            try:
                self._raise_for_status(response)
                payload = read_requests_json(
                    response, maximum_bytes=_MAX_QUOTE_RESPONSE_BYTES
                )
                self._raise_for_status(response, payload)
                result = payload.get("result")
                if not isinstance(result, list):
                    raise TossOpenApiError("Toss quote response has no result list")
                return result
            except TossAuthenticationError:
                response.close()
                if authentication_retried:
                    raise
                authentication_retried = True
                self.token = ""
                self.token_expires_at = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
                self.authenticate()
            except Exception:
                response.close()
                raise

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
