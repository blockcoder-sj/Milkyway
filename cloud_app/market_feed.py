"""Bounded public market display feed. No credentials, orders, or trading writes."""

import datetime as dt
import math
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, field_validator
import requests

from .bounded_io import read_requests_json
from .market_catalog import CATALOG, Instrument

UTC = dt.timezone.utc


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    value: float = Field(gt=0, le=1e12)
    previous_close: float | None = Field(default=None, gt=0, le=1e12)
    day_high: float | None = Field(default=None, gt=0, le=1e12)
    day_low: float | None = Field(default=None, gt=0, le=1e12)
    year_high: float | None = Field(default=None, gt=0, le=1e12)
    year_low: float | None = Field(default=None, gt=0, le=1e12)
    observed_at: dt.datetime
    fetched_at: dt.datetime
    regular_start: dt.datetime | None = None
    regular_end: dt.datetime | None = None
    # Intraday values are decorative, never used to compute daily performance.
    sparkline: list[float] = Field(default_factory=list, max_length=400)

    @field_validator("observed_at", "fetched_at", "regular_start", "regular_end")
    @classmethod
    def aware_time(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("market time must include a timezone")
        return value

    @field_validator("sparkline")
    @classmethod
    def positive_points(cls, values):
        if any(not math.isfinite(v) or not 0 < v <= 1e12 for v in values):
            raise ValueError("invalid chart point")
        return values


def _price(value, multiplier=1.0):
    if isinstance(value, bool):
        return None
    try:
        number = float(value) * multiplier
    except (ValueError, TypeError, OverflowError):
        return None
    return number if math.isfinite(number) and 0 < number <= 1e12 else None


def _timestamp(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return dt.datetime.fromtimestamp(value, UTC)
    except (ValueError, OverflowError, OSError):
        return None


def parse_chart(payload: dict, instrument: Instrument, now: dt.datetime) -> Observation:
    chart = payload["chart"]
    if chart.get("error") or len(chart.get("result") or []) != 1:
        raise ValueError("source has no quote")
    row = chart["result"][0]
    meta = row["meta"]
    expected_type = {"indices": "INDEX", "sectors": "INDEX", "fx": "CURRENCY",
                     "futures": "FUTURE", "commodities": "FUTURE", "stocks": "EQUITY"}[instrument.group]
    if meta.get("symbol") != instrument.symbol or meta.get("instrumentType") != expected_type:
        raise ValueError("source instrument mismatch")
    observed = _timestamp(meta.get("regularMarketTime"))
    if observed is None or observed > now + dt.timedelta(minutes=2):
        raise ValueError("source quote timestamp is invalid")
    period = meta.get("currentTradingPeriod", {}).get("regular", {})
    timestamps = row.get("timestamp") or []
    prices = ((row.get("indicators", {}).get("quote") or [{}])[0].get("close") or [])
    if len(timestamps) > 2000 or len(prices) > 2000:
        raise ValueError("source chart exceeds point limit")
    points = []
    for raw_time, raw_price in zip(timestamps, prices):
        when, price = _timestamp(raw_time), _price(raw_price, instrument.multiplier)
        if when is not None and when <= min(now, observed) and price is not None:
            points.append(price)
    # The request is always range=1d. previousClose is the prior-session close;
    # never use an older multi-day range baseline as the daily comparison.
    return Observation(
        value=_price(meta.get("regularMarketPrice"), instrument.multiplier),
        previous_close=_price(meta.get("previousClose"), instrument.multiplier),
        day_high=_price(meta.get("regularMarketDayHigh"), instrument.multiplier),
        day_low=_price(meta.get("regularMarketDayLow"), instrument.multiplier),
        year_high=_price(meta.get("fiftyTwoWeekHigh"), instrument.multiplier),
        year_low=_price(meta.get("fiftyTwoWeekLow"), instrument.multiplier),
        observed_at=observed, fetched_at=now,
        regular_start=_timestamp(period.get("start")), regular_end=_timestamp(period.get("end")),
        sparkline=points[-400:],
    )


def fetch_one(instrument: Instrument) -> dict:
    try:
        with requests.Session() as session:
            session.trust_env = False
            response = session.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(instrument.symbol, safe=""),
                params={"range": "1d", "interval": "5m"},
                headers={"User-Agent": "MilkywayPersonal/1.0"},
                timeout=(3, 8), allow_redirects=False, stream=True,
            )
            if response.status_code != 200:
                response.close()
                return {"id": instrument.id, "error": "공급자 응답 오류 (HTTP {})".format(response.status_code)}
            payload = read_requests_json(response, maximum_bytes=256 * 1024)
        observation = parse_chart(payload, instrument, dt.datetime.now(UTC))
        return {"id": instrument.id, "observation": observation.model_dump(mode="json")}
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError, AttributeError):
        return {"id": instrument.id, "error": "공급자 데이터를 받거나 검증하지 못했습니다"}


def collect_market(_payload, _configuration) -> list[dict]:
    # Fixed catalog and concurrency; no user-selected URLs or symbols.
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(fetch_one, CATALOG))
