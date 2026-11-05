"""Local selected-symbol history with killable downloads and atomic generations.

Yahoo daily history is an independent, best-effort signal/backtest source. It is
never used as a brokerage quote or represented as certified historical membership.
The current generation is immutable so a refresh cannot corrupt an active reader.
"""

from __future__ import annotations

import datetime as dt
from . import native_platform as fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from dataclasses import replace
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from market_calendar import get_market_close_time, get_market_hours, is_trading_day
from price_data_pipeline import (
    _atomic_price_frame, _extract_download, load_manifest_snapshot,
    price_file_path, read_price_frame, sha256_file, validate_price_frame,
)
from universe_snapshot import build_legacy_snapshot, save_snapshot

from .bounded_io import read_bounded_file, read_bounded_json
from .local_demo import _atomic_json
from .provider_process import ProviderProcess

SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{0,5}(?:[.-][A-Z])?$")
MAX_PERSONAL_SYMBOLS = 100
MAX_HISTORY_ROWS = 850
MAX_PERSONAL_PRICE_BYTES = 512 * 1024
HISTORY_DEADLINE_SECONDS = 75
DATASET_KIND = "personal_selected_universe"
EASTERN = ZoneInfo("America/New_York")


def normalize_symbols(symbols, *, maximum=MAX_PERSONAL_SYMBOLS) -> list[str]:
    if not isinstance(symbols, (list, tuple, set)):
        raise ValueError("symbols must be a list of US stock tickers")
    normalized = []
    for item in symbols:
        if not isinstance(item, str):
            raise ValueError("ticker must be a string")
        symbol = item.strip().upper()
        if not SYMBOL_PATTERN.fullmatch(symbol):
            raise ValueError("invalid US stock ticker: {}".format(symbol[:20]))
        if symbol not in normalized:
            normalized.append(symbol)
    if len(normalized) > maximum:
        raise ValueError("at most {} distinct tickers are supported".format(maximum))
    return normalized


def last_completed_session(now=None) -> dt.date:
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    eastern = now.astimezone(EASTERN)
    day = eastern.date()
    closing = get_market_close_time(day)
    # Give the daily provider fifteen minutes after the actual close to settle.
    if closing:
        completed_at = eastern.replace(hour=closing[0], minute=closing[1], second=0, microsecond=0)
        if eastern >= completed_at + dt.timedelta(minutes=15):
            return day
    day -= dt.timedelta(days=1)
    for _ in range(14):
        if is_trading_day(day):
            return day
        day -= dt.timedelta(days=1)
    raise ValueError("no completed NYSE session in the previous fourteen days")


def _require_mode(settings):
    if not getattr(settings, "personal_local_mode", False) or settings.production:
        raise ValueError("personal history is available only in personal local mode")


def resolve_personal_settings(settings):
    """Capture a generation exactly once; never follow a mutable price directory."""
    _require_mode(settings)
    # Already captured by get_dataset_*.
    if (settings.dataset_dir / "manifest.json").is_file():
        manifest, _, _ = load_manifest_snapshot(settings.dataset_dir / "manifest.json")
        if manifest.get("dataset_kind") == DATASET_KIND:
            return settings
    pointer = read_bounded_json(settings.dataset_dir / "current.json", maximum_bytes=4096)
    name = pointer.get("generation") if isinstance(pointer, dict) else None
    if not isinstance(name, str) or not re.fullmatch(r"[0-9a-f]{32}", name):
        raise ValueError("personal history generation pointer is invalid")
    generation = settings.dataset_dir / "generations" / name
    if generation.is_symlink() or not generation.is_dir():
        raise ValueError("personal history generation is missing or unsafe")
    return replace(settings, dataset_dir=generation, snapshots_glob=str(generation / "snapshots" / "*.json"))


def _invalid_price_symbols(settings, metadata, symbols):
    """Cheap bounded integrity admission before trusting cached freshness."""
    invalid = []
    for symbol in symbols:
        if symbol not in metadata:
            continue
        try:
            item = metadata[symbol]
            if item["rows"] > MAX_HISTORY_ROWS:
                raise ValueError("personal price row limit exceeded")
            payload = read_bounded_file(
                price_file_path(settings.dataset_dir / "prices", symbol),
                maximum_bytes=MAX_PERSONAL_PRICE_BYTES,
            )
            if hashlib.sha256(payload).hexdigest() != item["sha256"]:
                raise ValueError("personal price integrity check failed")
        except (OSError, ValueError, TypeError, KeyError):
            invalid.append(symbol)
    return invalid


def personal_data_status(settings, *, symbols=None, now=None) -> dict:
    _require_mode(settings)
    required = last_completed_session(now).isoformat()
    action_day = (now or dt.datetime.now(dt.timezone.utc)).astimezone(EASTERN).date().isoformat()
    result = {
        "ready": False, "stale": True, "latest_session": None,
        "required_session": required, "symbols": [], "fresh_symbols": [],
        "stale_symbols": [], "missing_symbols": [], "error": None,
        "updated_at": None, "generation": None, "source": "Yahoo daily history",
        "certification_eligible": False,
        "action_ready": False, "missing_action_symbols": [], "invalid_symbols": [],
    }
    try:
        captured = resolve_personal_settings(settings)
        manifest, _, _ = load_manifest_snapshot(captured.dataset_dir / "manifest.json")
        requested = normalize_symbols(symbols if symbols is not None else list(manifest["prices"]))
        metadata = manifest["prices"]
        invalid = _invalid_price_symbols(captured, metadata, requested)
        result.update(
            symbols=list(metadata), updated_at=manifest.get("updated_at"),
            generation=captured.dataset_dir.name,
            latest_session=max(item["last_date"] for item in metadata.values()),
            fresh_symbols=[s for s in requested if s not in invalid and metadata.get(s, {}).get("last_date") == required],
            stale_symbols=[s for s in requested if s in metadata and (s in invalid or metadata[s]["last_date"] != required)],
            missing_symbols=[s for s in requested if s not in metadata],
            missing_action_symbols=[s for s in requested if s in invalid or metadata.get(s, {}).get("action_checked_on") != action_day],
            invalid_symbols=invalid,
        )
        if invalid:
            result["error"] = "일봉 파일 손상을 감지해 다시 받습니다: " + ", ".join(invalid)
        result["action_ready"] = bool(requested and not result["missing_action_symbols"])
        result["ready"] = bool(result["action_ready"] and len(result["fresh_symbols"]) == len(requested))
        result["stale"] = not result["ready"]
    except FileNotFoundError:
        result["error"] = "과거 일봉을 준비하고 있습니다. 전략 저장 후 잠시 기다려 주세요."
    except (ValueError, OSError, KeyError, TypeError):
        result["error"] = "과거 일봉 파일 검증에 실패했습니다. 자동 재시도를 기다려 주세요."
    try:
        attempt = read_bounded_json(settings.dataset_dir / "refresh-status.json", maximum_bytes=16384)
        result["last_attempt_at"] = attempt.get("attempted_at")
        if attempt.get("error"):
            result["error"] = attempt["error"]
    except (OSError, ValueError, TypeError):
        pass
    if result["fresh_symbols"] and not result["stale_symbols"] and not result["missing_symbols"] and result["missing_action_symbols"]:
        result["error"] = "완료된 일봉은 준비됐습니다. 오늘의 분할·배당 확인은 개장 후 재시도하며, 확인 전 신규 페이퍼 체결은 대기합니다."
    return result


def personal_corporate_actions(settings, now=None) -> list[dict]:
    """Known provider actions only; absence is not proof no action is scheduled."""
    _require_mode(settings)
    captured = resolve_personal_settings(settings)
    manifest, _, _ = load_manifest_snapshot(captured.dataset_dir / "manifest.json")
    today = (now or dt.datetime.now(dt.timezone.utc)).astimezone(EASTERN).date().isoformat()
    return [dict(event, ticker=ticker)
            for ticker, events in manifest.get("corporate_actions", {}).items()
            for event in events if event["date"] <= today]


def _raw_symbol_frame(raw, symbol, count):
    if isinstance(raw.columns, pd.MultiIndex):
        if symbol in raw.columns.get_level_values(0):
            return raw[symbol]
        if symbol in raw.columns.get_level_values(1):
            return raw.xs(symbol, level=1, axis=1)
        return None
    return raw if count == 1 else None


def _merge_action_rows(existing, frame, action_day):
    """Merge corroborating event values; conflicting provider data stays blocked."""
    merged = {event["date"]: dict(event) for event in existing}
    for timestamp, row in frame.iterrows():
        stamp = pd.Timestamp(timestamp)
        day = stamp.tz_convert(EASTERN).date() if stamp.tzinfo else stamp.date()
        if day > action_day:
            continue
        try:
            values = {"split_ratio": float(row["Stock Splits"]), "dividend": float(row["Dividends"])}
        except (TypeError, ValueError, OverflowError):
            return None
        if any(not np.isfinite(value) or value < 0 for value in values.values()):
            return None
        if not any(values.values()):
            continue
        event = merged.setdefault(day.isoformat(), {"date": day.isoformat(), "split_ratio": 0., "dividend": 0.})
        for key, value in values.items():
            if value and event[key] and not np.isclose(value, event[key], rtol=1e-8, atol=1e-10):
                return None
            if value:
                event[key] = value
    return [merged[key] for key in sorted(merged)]


def _confirm_intraday_actions(yf, symbols, aliases, metadata, actions, action_day, as_of):
    """A missing daily Close must not hide available same-session action data.

    Intraday prices only attest to the session of the Yahoo action response.
    They never enter signal history, brokerage quotes, or the fill ledger.
    """
    if not symbols or not as_of:
        return
    try:
        observed = dt.datetime.fromisoformat(as_of)
    except (TypeError, ValueError):
        return
    if observed.tzinfo is None:
        return
    eastern = observed.astimezone(EASTERN)
    hours = get_market_hours(action_day)
    if not hours or eastern.date() != action_day or eastern.time() < dt.time(hours[0], hours[1]):
        return
    opens = pd.Timestamp(dt.datetime.combine(action_day, dt.time(hours[0], hours[1]), EASTERN))
    closes = pd.Timestamp(dt.datetime.combine(action_day, dt.time(hours[2], hours[3]), EASTERN))
    try:
        raw = yf.download(
            [aliases[symbol] for symbol in symbols], start=action_day.isoformat(),
            end=(action_day + dt.timedelta(days=1)).isoformat(), interval="5m",
            auto_adjust=False, actions=True, progress=False, threads=4,
            group_by="ticker", timeout=10, keepna=True, ignore_tz=False,
        )
    except Exception:
        return  # Keep the existing daily generation and retry on the next refresh.
    if raw is None or raw.empty:
        return
    for symbol in symbols:
        frame = _raw_symbol_frame(raw, aliases[symbol], len(symbols))
        if frame is None or not {"Close", "Dividends", "Stock Splits"}.issubset(frame.columns):
            continue
        try:
            index = pd.DatetimeIndex(frame.index)
        except (TypeError, ValueError):
            continue
        if index.tz is None:
            continue  # Do not guess the trading day of an ambiguous timestamp.
        eligible = (index >= opens) & (index < closes) & (index <= pd.Timestamp(observed))
        today = frame.loc[eligible]
        close = pd.to_numeric(today["Close"], errors="coerce")
        if not ((close > 0) & np.isfinite(close)).any():
            continue
        events = _merge_action_rows(actions[symbol], today, action_day)
        if events is None:
            continue
        actions[symbol] = events
        metadata[symbol]["action_checked_on"] = action_day.isoformat()
        metadata[symbol]["action_check_source"] = "yahoo_intraday_5m"


def _download_history(payload, configuration):
    """Run entirely in ProviderProcess, which kills hangs at the wall deadline."""
    import yfinance as yf

    symbols = normalize_symbols(payload["symbols"])
    target = Path(configuration["target"])
    required = dt.date.fromisoformat(payload["required_session"])
    action_day = dt.date.fromisoformat(payload["action_day"])
    start = required - dt.timedelta(days=1095)
    # Yahoo's class share separator differs from the brokerage convention.
    aliases = {symbol: symbol.replace(".", "-") for symbol in symbols}
    raw = yf.download(
        list(aliases.values()), start=start.isoformat(),
        end=(action_day + dt.timedelta(days=1)).isoformat(), interval="1d",
        auto_adjust=True, actions=True, progress=False, threads=4,
        group_by="ticker", timeout=10, keepna=True,
    )
    if raw is None or raw.empty:
        return {"prices": {}, "corporate_actions": {}}
    metadata, actions = {}, {}
    for symbol, alias in aliases.items():
        original = _raw_symbol_frame(raw, alias, len(symbols))
        if original is None:
            continue
        frame = _extract_download(raw, alias, len(symbols))
        if frame is None:
            continue
        frame = frame[frame.index <= pd.Timestamp(required)].tail(MAX_HISTORY_ROWS)
        if len(frame) < 20 or not validate_price_frame(frame)["valid"]:
            continue
        # A missing final day is retained as stale, never re-labelled as today.
        path = price_file_path(target / "prices", symbol)
        _atomic_price_frame(frame, path)
        metadata[symbol] = {
            "rows": len(frame), "first_date": frame.index.min().date().isoformat(),
            "last_date": frame.index.max().date().isoformat(), "sha256": sha256_file(path),
        }
        # Before the opening print, Yahoo may return only yesterday's rows and
        # omit today's split/dividend. Keep retrying rather than certifying that
        # empty action list for the rest of the trading day.
        today_rows = original.loc[[pd.Timestamp(index).date() == action_day for index in original.index]]
        has_today_bar = bool(not today_rows.empty and pd.to_numeric(today_rows["Close"], errors="coerce").notna().any())
        metadata[symbol]["action_checked_on"] = action_day.isoformat() if (has_today_bar or not is_trading_day(action_day)) else None
        events = []
        for date, row in original.iterrows():
            day = pd.Timestamp(date).date()
            if day > action_day:
                continue
            split, dividend = float(row.get("Stock Splits", 0) or 0), float(row.get("Dividends", 0) or 0)
            if not np.isfinite(split) or not np.isfinite(dividend):
                continue
            if split > 0 or dividend > 0:
                events.append({"date": day.isoformat(), "split_ratio": split, "dividend": dividend})
        actions[symbol] = events
    missing_actions = [symbol for symbol in metadata if metadata[symbol]["action_checked_on"] is None]
    _confirm_intraday_actions(yf, missing_actions, aliases, metadata, actions, action_day, payload.get("as_of"))
    return {"prices": metadata, "corporate_actions": actions}


_history_process = ProviderProcess(_download_history)


def _sync_directory(path):
    fcntl.sync_directory(path)


def _csv_content_digest(path):
    # gzip FNAME can include the writer's random temporary filename. Compare
    # verified CSV content, while retaining compressed hashes for tamper checks.
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _content_inventory(metadata):
    return {symbol: {key: value for key, value in item.items() if key != "sha256"}
            for symbol, item in metadata.items()}


def refresh_personal_data(symbols, settings, now=None) -> dict:
    """Refresh selected history once per completed session and retain good data.

    Validation/provider failures are visible status, not deletion. A lock spans
    preparation/promotion so independent workers cannot lose another generation.
    """
    _require_mode(settings)
    requested = normalize_symbols(symbols)
    root = settings.dataset_dir
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / "refresh.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return personal_data_status(settings, symbols=requested, now=now)
        if not requested:
            return personal_data_status(settings, now=now)
        old_settings, old_manifest = None, {}
        try:
            old_settings = resolve_personal_settings(settings)
            old_manifest, _, _ = load_manifest_snapshot(old_settings.dataset_dir / "manifest.json")
        except (OSError, ValueError):
            pass
        # Keep cached symbols for backtests and paused strategies when an active
        # account worker asks for a subset. The global admission cap remains 100.
        requested = normalize_symbols(sorted(set(requested) | set(old_manifest.get("prices", {}))))
        status = personal_data_status(settings, symbols=requested, now=now)
        eastern_now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(EASTERN)
        action_day = eastern_now.date().isoformat()
        if status["ready"]:
            return status
        if (len(status["fresh_symbols"]) == len(requested)
                and is_trading_day(eastern_now.date()) and eastern_now.time() < dt.time(9, 30)):
            # Today's daily bar cannot yet establish the action check. Do not
            # repeatedly download the same large history overnight.
            return status
        attempted = (now or dt.datetime.now(dt.timezone.utc)).isoformat()
        generations = root / "generations"
        generations.mkdir(exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".pending-", dir=generations))
        try:
            needed = [symbol for symbol in requested
                      if symbol not in status["fresh_symbols"] or symbol in status["missing_action_symbols"]]
            try:
                outcome = _history_process.run(
                    {"symbols": needed, "required_session": status["required_session"], "action_day": action_day,
                     "as_of": eastern_now.isoformat()},
                    {"target": str(staging)}, deadline=time.monotonic() + HISTORY_DEADLINE_SECONDS,
                )
            except (OSError, ValueError, TypeError, RuntimeError, TimeoutError):
                # Even an outage may leave healthy old symbols alongside a
                # corrupted one. Build a clean partial generation from those
                # verified files, never copying the corrupt fallback forward.
                outcome = {"prices": {}, "corporate_actions": {}}
            metadata = outcome["prices"]
            actions = outcome.get("corporate_actions", {})
            for symbol, previous in old_manifest.get("prices", {}).items():
                if symbol in metadata and metadata[symbol]["last_date"] >= previous["last_date"]:
                    continue
                if symbol in status["invalid_symbols"]:
                    continue
                source = price_file_path(old_settings.dataset_dir / "prices", symbol)
                try:
                    read_price_frame(source, require_valid=True, expected_sha256=previous["sha256"])
                except (OSError, ValueError):
                    continue
                destination = price_file_path(staging / "prices", symbol)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                os.chmod(destination, 0o600)
                with destination.open("rb") as handle:
                    os.fsync(handle.fileno())
                metadata[symbol] = dict(previous)
                actions[symbol] = old_manifest.get("corporate_actions", {}).get(symbol, [])
            if not metadata:
                raise ValueError("no valid daily prices returned")
            for symbol, item in metadata.items():
                if symbol not in requested:
                    raise ValueError("history provider returned an unexpected symbol")
                frame = read_price_frame(price_file_path(staging / "prices", symbol), require_valid=True, expected_sha256=item["sha256"])
                if len(frame) > MAX_HISTORY_ROWS or frame.index.max().date().isoformat() > status["required_session"]:
                    raise ValueError("history exceeds its permitted window")
                if item["rows"] != len(frame) or item["last_date"] != frame.index.max().date().isoformat():
                    raise ValueError("history metadata mismatch")
                item["content_sha256"] = _csv_content_digest(price_file_path(staging / "prices", symbol))
            failed = [s for s in requested if metadata.get(s, {}).get("last_date") != status["required_session"] or metadata.get(s, {}).get("action_checked_on") != action_day]
            attempt_status = {
                "attempted_at": attempted,
                "error": "일부 종목의 최신 일봉을 받지 못했습니다: " + ", ".join(failed) if failed else None,
            }
            unchanged = (_content_inventory(metadata) == _content_inventory(old_manifest.get("prices", {}))
                    and actions == old_manifest.get("corporate_actions", {}))
            if unchanged:
                try:
                    for symbol, item in old_manifest["prices"].items():
                        read_price_frame(price_file_path(old_settings.dataset_dir / "prices", symbol), require_valid=True, expected_sha256=item["sha256"])
                except (OSError, ValueError):
                    unchanged = False  # A verified new generation repairs corruption.
            if unchanged:
                # One bad symbol may cause retries all day. Identical validated
                # data must not produce thousands of retained copies/backups.
                _atomic_json(root / "refresh-status.json", attempt_status)
                return personal_data_status(settings, symbols=requested, now=now)
            snapshot = build_legacy_snapshot(
                {symbol: "NASDAQ" for symbol in metadata},
                effective_date=min(item["first_date"] for item in metadata.values()),
            )
            for record in snapshot["records"]:
                record["exchange"] = "USER_SELECTED"
            snapshot["allowed_exchanges"] = []
            snapshot["membership_sha256"] = hashlib.sha256(json.dumps(snapshot["records"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            snapshot.update(snapshot_type=DATASET_KIND, provenance="user-selected current universe, not historical listing evidence", notes="Exploratory backtests only; actual listing exchanges are not asserted.")
            save_snapshot(snapshot, staging / "snapshots")
            manifest = {
                "schema_version": 2, "price_format": "csv-gzip-v1",
                "dataset_kind": DATASET_KIND, "source": "yfinance",
                "auto_adjust": True, "updated_at": attempted,
                "action_checked_on": action_day,
                "prices": metadata, "corporate_actions": actions,
            }
            _atomic_json(staging / "manifest.json", manifest)
            _atomic_json(staging / "validation_report.json", {
                "dataset_kind": DATASET_KIND, "forward_strategy_data_gate_ready": False,
                "window": {"end": status["required_session"]},
                "strategy_candidate_data_blockers": [],
            })
            _sync_directory(staging / "prices")
            _sync_directory(staging / "snapshots")
            _sync_directory(staging)
            name = uuid.uuid4().hex
            os.replace(staging, generations / name)
            _sync_directory(generations)
            _atomic_json(root / "current.json", {"generation": name})
            _sync_directory(root)
            _atomic_json(root / "refresh-status.json", attempt_status)
        except (OSError, ValueError, TypeError, KeyError, RuntimeError, TimeoutError):
            _atomic_json(root / "refresh-status.json", {
                "attempted_at": attempted,
                "error": "과거 일봉 다운로드/검증에 실패했습니다. 기존 기록은 보존되며 자동 재시도합니다.",
            })
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return personal_data_status(settings, symbols=requested, now=now)
