"""Atomic display cache and source-aware projections, independent of the ledger."""

import datetime as dt
import json
import os
import tempfile
import time

from .bounded_io import read_bounded_json
from .market_catalog import CATALOG
from .market_feed import Observation, collect_market
from .provider_process import ProviderProcess

REFRESH_SECONDS = 300
DEADLINE_SECONDS = 75
MAX_CACHE_BYTES = 2 * 1024 * 1024
_provider = ProviderProcess(collect_market)
UTC = dt.timezone.utc


def close_market_provider():
    _provider.close()


def _write_cache(path, cache):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".market-", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(cache, handle, ensure_ascii=False, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def cache_path(settings):
    if not settings.personal_local_mode or settings.production:
        raise ValueError("Market display feed requires personal local mode")
    return settings.dataset_dir.parent / "market-overview.json"


def read_cache(settings) -> dict:
    try:
        cache = read_bounded_json(cache_path(settings), maximum_bytes=MAX_CACHE_BYTES)
        if cache.get("version") != 1 or not isinstance(cache.get("items"), dict):
            return {}
        return cache
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def refresh_market(settings) -> dict:
    path = cache_path(settings)
    previous = read_cache(settings).get("items", {})
    try:
        collected = _provider.run({}, {}, deadline=time.monotonic() + DEADLINE_SECONDS)
        results = {row["id"]: row for row in collected}
    except (ValueError, RuntimeError, TimeoutError, OSError, TypeError, KeyError):
        results = {}
    items = {}
    for instrument in CATALOG:
        result = results.get(instrument.id, {})
        observation = result.get("observation")
        error = result.get("error", "시장 데이터 수집이 지연되고 있습니다")
        if observation is not None:
            try:
                observation = Observation.model_validate(observation).model_dump(mode="json")
                error = None
            except (ValueError, TypeError):
                observation = None
        if observation is None:
            old = previous.get(instrument.id, {})
            observation = old.get("observation") if isinstance(old, dict) else None
        items[instrument.id] = {"observation": observation, "error": error}
    cache = {"version": 1, "attempted_at": dt.datetime.now(UTC).isoformat(), "items": items}
    _write_cache(path, cache)
    return cache


def market_overview(settings, *, now=None) -> dict:
    now = now or dt.datetime.now(UTC)
    cache = read_cache(settings)
    stored = cache.get("items", {})
    rows = []
    for instrument in CATALOG:
        item = stored.get(instrument.id, {})
        row = {"id": instrument.id, "label": instrument.label, "symbol": instrument.symbol,
               "market": instrument.market, "group": instrument.group, "unit": instrument.unit,
               "description": instrument.description, "source": "Yahoo Finance",
               "source_url": instrument.source_url, "is_realtime": False,
               "status": "awaiting_source", "value": None, "change": None, "change_pct": None,
               "error": item.get("error") if isinstance(item, dict) else None}
        try:
            observation = Observation.model_validate(item.get("observation"))
            if observation.observed_at > now + dt.timedelta(minutes=2) or observation.fetched_at > now + dt.timedelta(minutes=2):
                raise ValueError("future observation")
            row.update(observation.model_dump(mode="json"))
            if observation.previous_close is not None:
                row["change"] = observation.value - observation.previous_close
                row["change_pct"] = row["change"] / observation.previous_close * 100
            stale = (bool(row["error"]) or now - observation.fetched_at > dt.timedelta(seconds=REFRESH_SECONDS * 2 + 60)
                     or now - observation.observed_at > dt.timedelta(days=4))
            trading = (observation.regular_start is not None and observation.regular_end is not None
                       and observation.regular_start <= now <= observation.regular_end)
            if trading and now - observation.observed_at > dt.timedelta(minutes=30):
                stale = True
            closed = observation.regular_start is not None and observation.regular_end is not None and not trading
            row["status"] = "stale" if stale else "completed_close" if closed else "delayed"
        except (ValueError, TypeError, AttributeError):
            row["status"] = "unavailable" if row["error"] else "awaiting_source"
        rows.append(row)
    return {"source": "Yahoo Finance", "refresh_seconds": REFRESH_SECONDS,
            "attempted_at": cache.get("attempted_at"), "items": rows,
            "available_count": sum(row["value"] is not None for row in rows),
            "total_count": len(rows),
            "note": "개인용 참고 시세 · 5분마다 수집 · 공급자 지연 가능 · 페이퍼 체결에 사용하지 않음"}
