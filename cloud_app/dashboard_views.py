"""Source-aware view models for the club dashboard.

The dashboard must never turn a missing feed into a convincing fake quote or
headline.  This module therefore carries source, observation time and status
alongside every value rendered by the browser.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import threading
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from market_calendar import count_trading_days_between, get_market_hours, is_trading_day, prev_trading_day

from .database import Quote, utcnow


MARKET_GROUPS = {
    "indices": (
        {"id": "kospi", "label": "코스피", "aliases": ("KOSPI", "^KS11")},
        {"id": "kosdaq", "label": "코스닥", "aliases": ("KOSDAQ", "^KQ11")},
        {"id": "sp500", "label": "S&P 500", "aliases": ("SPX", "^GSPC")},
        {"id": "dow", "label": "다우", "aliases": ("DJI", "^DJI")},
        {"id": "nasdaq", "label": "나스닥", "aliases": ("IXIC", "^IXIC")},
    ),
    "futures": (
        {
            "id": "kospi200_future",
            "label": "코스피 200 선물",
            "aliases": ("KOSPI200F", "101S9000"),
        },
        {"id": "nasdaq_future", "label": "나스닥 100 선물", "aliases": ("NQ", "NQ=F")},
    ),
}

SECTOR_LABELS = {
    "tech": "IT",
    "health": "Health",
    "finance": "Finance",
    "consumer": "Consumer",
    "industrial": "Industry",
    "reits": "REIT",
    "materials": "Material",
    "energy": "Energy",
    "communication": "Comm.",
    "utilities": "Utility",
}


def _aware(value: dt.datetime) -> dt.datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=dt.timezone.utc)


def market_overview(
    session: Session,
    *,
    quote_interval_seconds: int,
    now: dt.datetime | None = None,
) -> dict:
    """Build the requested index/futures rows without inventing missing data."""
    now = now or utcnow()
    aliases = {alias for rows in MARKET_GROUPS.values() for item in rows for alias in item["aliases"]}
    quotes = session.scalars(select(Quote).where(Quote.ticker.in_(aliases))).all()
    by_ticker = {row.ticker: row for row in quotes}
    live_window = dt.timedelta(seconds=max(120, quote_interval_seconds * 4))

    def render(item: dict) -> dict:
        candidates = [by_ticker[alias] for alias in item["aliases"] if alias in by_ticker]
        row = max(candidates, key=lambda value: _aware(value.observed_at)) if candidates else None
        if row is None:
            return {
                "id": item["id"],
                "label": item["label"],
                "symbol": item["aliases"][0],
                "value": None,
                "source": None,
                "observed_at": None,
                "status": "awaiting_source",
                "is_realtime": False,
            }
        observed_at = _aware(row.observed_at)
        if row.source == "dataset_close":
            status = "completed_close"
        elif now - observed_at <= live_window:
            status = "live"
        else:
            status = "stale"
        return {
            "id": item["id"],
            "label": item["label"],
            "symbol": row.ticker,
            "value": float(row.price),
            "source": row.source,
            "observed_at": observed_at,
            "status": status,
            "is_realtime": status == "live",
        }

    return {
        key: [render(item) for item in items]
        for key, items in MARKET_GROUPS.items()
    }


def completed_session_freshness(
    last_session: dt.date,
    *,
    now: dt.datetime | None = None,
) -> dict:
    """Compare the dataset with the latest fully completed NYSE session."""
    now = _aware(now or utcnow())
    eastern_now = now.astimezone(ZoneInfo("America/New_York"))
    local_date = eastern_now.date()
    hours = get_market_hours(local_date)
    if is_trading_day(local_date) and hours is not None:
        close_at = eastern_now.replace(
            hour=hours[2], minute=hours[3], second=0, microsecond=0
        )
        expected = local_date if eastern_now > close_at else prev_trading_day(local_date)
    else:
        expected = prev_trading_day(local_date)
    lag = 0
    if expected > last_session:
        lag = count_trading_days_between(last_session, expected) + 1
    return {
        "expected_latest_completed_session": expected,
        "trading_session_lag": lag,
        "fresh": lag == 0,
    }


_sector_cache_lock = threading.Lock()
_sector_cache: dict[tuple[str, str, int], dict] = {}


def sector_heatmap(bundle, sector_map_path: Path) -> dict:
    """Calculate latest one-session equal-weight sector returns.

    Market-cap history is not present in the current dataset, so an
    equal-weight mean is explicitly reported instead of implying an official
    sector-index return.
    """
    last_session = bundle.index.max().date().isoformat()
    map_mtime = sector_map_path.stat().st_mtime_ns if sector_map_path.exists() else 0
    cache_key = (bundle.fingerprint, last_session, map_mtime)
    with _sector_cache_lock:
        cached = _sector_cache.get(cache_key)
    if cached is not None:
        return cached

    if not sector_map_path.exists():
        return {
            "status": "awaiting_sector_map",
            "as_of": last_session,
            "method": "one_session_equal_weight_mean",
            "coverage_pct": 0.0,
            "cells": [],
        }
    try:
        raw_map = json.loads(sector_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "invalid_sector_map",
            "as_of": last_session,
            "method": "one_session_equal_weight_mean",
            "coverage_pct": 0.0,
            "cells": [],
        }

    close = bundle.panels["Close"]
    if len(close.index) < 2:
        return {
            "status": "insufficient_history",
            "as_of": last_session,
            "method": "one_session_equal_weight_mean",
            "coverage_pct": 0.0,
            "cells": [],
        }
    returns = (close.iloc[-1] / close.iloc[-2] - 1.0).replace([math.inf, -math.inf], float("nan")).dropna()
    sectors = pd.Series({ticker: raw_map.get(str(ticker).upper()) for ticker in returns.index})
    mapped = sectors.dropna()
    valid = returns.loc[returns.index.intersection(mapped.index)]
    frame = pd.DataFrame({"return": valid, "sector": mapped.loc[valid.index]}).dropna()
    cells = []
    for sector, rows in frame.groupby("sector"):
        values = rows["return"]
        cells.append(
            {
                "id": str(sector),
                "label": SECTOR_LABELS.get(str(sector), str(sector)),
                "return_pct": round(float(values.mean() * 100), 3),
                "advancers_pct": round(float((values > 0).mean() * 100), 1),
                "symbol_count": int(len(values)),
            }
        )
    cells.sort(key=lambda item: item["return_pct"], reverse=True)
    result = {
        "status": "ready" if cells else "insufficient_coverage",
        "market": "us",
        "taxonomy": "us_equity_simplified_10_sector",
        "as_of": last_session,
        "method": "one_session_equal_weight_mean",
        "coverage_pct": round(float(len(frame) / max(1, len(returns)) * 100), 1),
        "cells": cells,
    }
    with _sector_cache_lock:
        _sector_cache.clear()
        _sector_cache[cache_key] = result
    return result


def news_feed(path: Path) -> dict:
    """Read a provider-populated JSON cache; never fetch once per browser."""
    if not path.exists():
        return {"status": "awaiting_source", "provider": None, "observed_at": None, "items": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "invalid_feed", "provider": None, "observed_at": None, "items": []}
    container = raw if isinstance(raw, dict) else {"items": raw}
    items = []
    for item in container.get("items", [])[:20]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()[:300]
        url = str(item.get("url", "")).strip()
        parsed = urlparse(url)
        if not title or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        items.append(
            {
                "title": title,
                "url": url,
                "source": str(item.get("source", "")).strip()[:80] or "미지정",
                "published_at": item.get("published_at"),
                "category": str(item.get("category", "경제")).strip()[:40] or "경제",
            }
        )
    return {
        "status": "ready" if items else "empty",
        "provider": str(container.get("provider", "configured_feed"))[:80],
        "observed_at": container.get("observed_at"),
        "items": items,
    }
