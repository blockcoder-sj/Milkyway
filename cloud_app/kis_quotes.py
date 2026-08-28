"""Minimal Korea Investment Securities client for shared US equity quotes."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter


logger = logging.getLogger("cloud_app.kis_quotes")


@dataclass(frozen=True)
class KisCredentials:
    api_key: str
    api_secret: str
    account_id: str
    paper: bool = True


class KisQuoteClient:
    """Quote-only KIS client; it cannot submit or manage brokerage orders."""

    _exchange_codes = ("NAS", "NYS", "AMS")

    def __init__(self, credentials: KisCredentials):
        if not credentials.api_key or not credentials.api_secret or not credentials.account_id:
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

    def connect(self) -> bool:
        try:
            response = self.session.post(
                self.base_url + "/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.credentials.api_key,
                    "appsecret": self.credentials.api_secret,
                },
                timeout=10,
            )
            response.raise_for_status()
            self.token = response.json()["access_token"]
            self.token_expires_at = dt.datetime.now() + dt.timedelta(hours=23)
            return True
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            logger.error("KIS token request failed: %s", type(exc).__name__)
            return False

    def _headers(self) -> dict[str, str]:
        if not self.token or dt.datetime.now() >= self.token_expires_at:
            if not self.connect():
                raise RuntimeError("KIS token refresh failed")
        return {
            "authorization": "Bearer " + self.token,
            "appkey": self.credentials.api_key,
            "appsecret": self.credentials.api_secret,
            "tr_id": "HHDFS00000300",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _request_quote(self, ticker: str, exchange_code: str) -> dict | None:
        response = self.session.get(
            self.base_url + "/uapi/overseas-price/v1/quotations/price",
            headers=self._headers(),
            params={"AUTH": "", "EXCD": exchange_code, "SYMB": ticker},
            timeout=10,
        )
        response.raise_for_status()
        output = response.json().get("output", {})
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
        for exchange_code in candidates:
            try:
                quote = self._request_quote(ticker, exchange_code)
            except requests.RequestException as exc:
                logger.warning("KIS quote failed ticker=%s error=%s", ticker, type(exc).__name__)
                continue
            if quote:
                self.exchange_cache[ticker] = exchange_code
                return quote
        return {"price": 0, "bid": 0, "ask": 0, "volume": 0}
