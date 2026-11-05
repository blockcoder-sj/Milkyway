"""Personal US-wide screening, isolated from the execution/stop worker.

Daily history is cached per security. A complete directory pass precedes every
published decision; there is no fixed ticker shortlist. Live Toss prices affect
price factors and the price filter. Volume factors use completed-session volume.
All provider work runs in a killable child and never holds a ledger transaction.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from price_data_pipeline import _atomic_price_frame, price_file_path, sha256_file, validate_price_frame
from universe_snapshot import NASDAQ_LISTED_URL, OTHER_LISTED_URL, parse_symbol_directory, build_legacy_snapshot, save_snapshot
from .bounded_io import read_bounded_json, read_requests_bytes
from .local_demo import _atomic_json
from .personal_data import EASTERN, SYMBOL_PATTERN, DATASET_KIND, last_completed_session
from .provider_process import ProviderProcess
from .toss_quotes import TossQuoteClient, TossCredentials, TossRateLimitError, TossAuthenticationError, TossIpNotAllowedError

CATALOG_LIMIT = 30_000  # Admission bound, never a top-N stock selection.
HISTORY_ROWS = 320
HISTORY_BATCH = 20
DECISION_MAX_AGE = 180
MAX_HISTORY_BYTES = 256 * 1024
_client = None


def root_for(settings):
    return settings.dataset_dir.parent / "auto-market"


def _read(path, limit, default=None):
    try:
        return read_bounded_json(path, maximum_bytes=limit)
    except FileNotFoundError:
        return default


def spec_digest(spec):
    return hashlib.sha256(spec.model_dump_json().encode()).hexdigest()


def parse_catalog(nasdaq, other):
    # Reuse directory security-type filtering, but remove the historical CSV
    # cache's A-Z-only restriction (BRK.B and other class shares are supported).
    rows = parse_symbol_directory(nasdaq, other)
    symbols = sorted({r["symbol"] for r in rows if r["exchange"] != "UNKNOWN_BLANK"
                      and not any(x != "symbol_not_cache_compatible" for x in r["exclusion_reasons"])
                      and SYMBOL_PATTERN.fullmatch(r["symbol"])})
    if not symbols or len(symbols) > CATALOG_LIMIT:
        raise ValueError("US directory is empty or exceeds its admission bound")
    return symbols


def _catalog(now):
    import requests
    texts = []
    for url, header in ((NASDAQ_LISTED_URL, "Symbol|"), (OTHER_LISTED_URL, "ACT Symbol|")):
        response = requests.get(url, timeout=15, stream=True)
        try:
            response.raise_for_status()
            raw = read_requests_bytes(response, maximum_bytes=8 * 1024 * 1024).decode("utf-8-sig")
        finally:
            response.close()
        if not raw.startswith(header) or "File Creation Time:" not in raw:
            raise ValueError("Incomplete official symbol directory")
        texts.append(raw)
    symbols = parse_catalog(*texts)
    # An HTML error or truncated directory must never silently narrow the market.
    if len(symbols) < 1000:
        raise ValueError("Official directory coverage is unexpectedly small")
    return {"date": now.astimezone(EASTERN).date().isoformat(), "symbols": symbols,
            "sha256": hashlib.sha256("\n".join(symbols).encode()).hexdigest(),
            "sources": [NASDAQ_LISTED_URL, OTHER_LISTED_URL]}


def _frame(rows):
    frame = pd.DataFrame(rows, columns=["date", "Open", "High", "Low", "Close", "Volume"])
    frame.index = pd.to_datetime(frame.pop("date"))
    frame = frame.astype(float).sort_index()
    if not validate_price_frame(frame)["valid"]:
        raise ValueError("Invalid screening history")
    return frame


def _history_path(root, symbol):
    if not SYMBOL_PATTERN.fullmatch(symbol):
        raise ValueError("Invalid history symbol")
    return root / "history" / (symbol + ".json")


def _save_history(root, symbol, frame, source, required):
    frame = frame.loc[frame.index <= pd.Timestamp(required)].tail(HISTORY_ROWS)
    if frame.empty or frame.index.max().date().isoformat() != required or not validate_price_frame(frame)["valid"]:
        return False
    rows = [[date.date().isoformat(), *map(float, row)] for date, row in frame[["Open", "High", "Low", "Close", "Volume"]].iterrows()]
    _atomic_json(_history_path(root, symbol), {"source": source, "session": required, "rows": rows})
    return True


def _history(client, root, symbols, required, now):
    outcomes, fallback = {}, []
    for symbol in symbols:
        try:
            rows = client.daily_candles(symbol, count=HISTORY_ROWS)
            frame = _frame(rows)
            if not _save_history(root, symbol, frame, "toss", required):
                fallback.append(symbol)
            else:
                outcomes[symbol] = "ready"
        except (TossRateLimitError, TossAuthenticationError, TossIpNotAllowedError):
            raise  # Do not fan out a provider-wide denial into thousands of calls.
        except Exception:
            fallback.append(symbol)
        time.sleep(0.12)
    if fallback:
        import yfinance as yf
        from price_data_pipeline import _extract_download
        aliases = {s: s.replace(".", "-") for s in fallback}
        raw = yf.download(list(aliases.values()), start=(dt.date.fromisoformat(required)-dt.timedelta(days=550)).isoformat(),
                          end=(dt.date.fromisoformat(required)+dt.timedelta(days=1)).isoformat(), interval="1d",
                          auto_adjust=True, progress=False, threads=4, group_by="ticker", timeout=10)
        for symbol in fallback:
            frame = _extract_download(raw, aliases[symbol], len(fallback)) if raw is not None else None
            ready = frame is not None and _save_history(root, symbol, frame, "yahoo_fallback", required)
            outcomes[symbol] = "ready" if ready else "unavailable"
    return outcomes


def factor_values(spec, frame, price):
    """Completed volume + current price, without inventing today's OHLC/volume."""
    close = frame["Close"].to_numpy(dtype=float)
    live = np.append(close, price)
    volume = frame["Volume"].to_numpy(dtype=float)
    values = []
    for f in spec.factors:
        n = f.lookback
        if f.weight == 0:
            values.append(0.)
            continue
        if len(close) < n + 1:
            return None
        if f.kind == "momentum": value = live[-1] / live[-1-n] - 1
        elif f.kind == "mean_reversion": value = -(live[-1] / live[-1-n] - 1)
        elif f.kind == "moving_average": value = live[-1] / live[-n:].mean() - 1
        elif f.kind == "low_volatility": value = -np.std(np.diff(live[-n-1:]) / live[-n-1:-1], ddof=1)
        elif f.kind == "volume_momentum": value = volume[-1] / volume[-n:].mean() - 1 if volume[-n:].mean() > 0 else float("nan")
        elif f.kind == "rsi":
            change = np.diff(live[-n-1:]); gain = np.maximum(change, 0).mean(); loss = -np.minimum(change, 0).mean()
            value = (100 - 100 / (1 + gain/loss) - 50) / 50 if loss else (1 if gain else 0)
        else: raise ValueError("Unsupported factor")
        if not math.isfinite(value): return None
        values.append(float(value))
    return values


def select_many_from_market(specs, histories, quotes, now, *, max_age=180):
    """One streamed history pass for every saved strategy, with bounded memory."""
    states = [{"values":{}, "times":{}, "excluded":{"history":0,"quote":0,"filters":0}} for _ in specs]
    required = last_completed_session(now).isoformat()
    for symbol, history in histories.items():
        if not history or history.get("session") != required:
            for state in states: state["excluded"]["history"] += 1
            continue
        quote = quotes.get(symbol)
        try:
            stamp = dt.datetime.fromisoformat(quote["observed_at"])
            price = float(quote["price"])
            if stamp.tzinfo is None or not 0 <= (now-stamp).total_seconds() <= max_age or not math.isfinite(price) or price <= 0:
                raise ValueError()
        except (TypeError, ValueError, KeyError):
            for state in states: state["excluded"]["quote"] += 1
            continue
        frame = _frame(history["rows"])
        if frame.index.max().date().isoformat() != required:
            for state in states: state["excluded"]["history"] += 1
            continue
        for spec, state in zip(specs, states):
            factors = factor_values(spec, frame, price)
            days = spec.filters.history_days
            passed = (len(frame) >= days and price >= spec.filters.min_price and
                      frame["Volume"].tail(days).mean() >= spec.filters.min_average_volume)
            if factors is None or not passed:
                state["excluded"]["filters"] += 1
                continue
            state["values"][symbol] = factors
            state["times"][symbol] = stamp
    results = []
    for spec, state in zip(specs, states):
        values, exclusions = state["values"], state["excluded"]
        if not values:
            results.append(([], {}, exclusions, None))
            continue
        data = pd.DataFrame.from_dict(values, orient="index").sort_index()
        score = data.rank(pct=True).mul([f.weight for f in spec.factors]).sum(axis=1)
        targets = score.sort_values(ascending=False, kind="stable").head(spec.portfolio.max_positions).index.tolist()
        p = spec.portfolio
        weight = min(p.investment_fraction / len(targets), p.max_position_fraction)
        results.append((targets, {s:weight for s in targets}, exclusions, min(state["times"][symbol] for symbol in targets).isoformat()))
    return results


def select_from_market(spec, histories, quotes, now, *, max_age=180):
    return select_many_from_market([spec], histories, quotes, now, max_age=max_age)[0]


def _screen(client, root, payload, now):
    from .strategies import StrategySpec
    catalog = _read(root / "catalog.json", 8*1024*1024)
    symbols = catalog["symbols"]
    quotes = {}
    # All listings are attempted. A failed batch aborts publication rather than
    # presenting a partial network sweep as a complete market decision.
    for offset in range(0, len(symbols), 200):
        batch = symbols[offset:offset+200]
        for value in client.get_prices(batch):
            quotes[value["ticker"]] = {"price": value["price"], "observed_at": value["observed_at"].isoformat()}
        time.sleep(0.12)
    finished = dt.datetime.now(dt.timezone.utc)
    # Tests may replay time; production passes a real timestamp and uses the
    # completion clock so a slow sweep cannot certify old quotes as fresh.
    required = last_completed_session(now).isoformat()
    if last_completed_session(finished).isoformat() != required:
        raise ValueError("History session changed during screening")
    class HistoryFiles:
        def items(self):
            for symbol in symbols:
                yield symbol, _read(_history_path(root, symbol), MAX_HISTORY_BYTES)
    histories = HistoryFiles()
    decisions = {}
    specs = [StrategySpec.model_validate_json(value) for value in payload["specs"]]
    results = select_many_from_market(specs, histories, quotes, finished)
    for spec, (targets, weights, excluded, oldest) in zip(specs, results):
        decisions[spec_digest(spec)] = {"targets": targets, "weights": weights, "excluded": excluded,
            "quote_as_of": oldest, "created_at": finished.isoformat(), "history_session": required,
            "catalog_sha256": catalog["sha256"], "universe_count": len(symbols),
            "quoted_count": len(quotes), "evaluated_count": len(symbols)-sum(excluded.values())}
    _atomic_json(root / "decisions.json", decisions)
    return {"screened": len(symbols), "selected": sorted({s for d in decisions.values() for s in d["targets"]})}


def _execute(payload, configuration):
    global _client
    root = Path(configuration["root"])
    now = dt.datetime.fromisoformat(payload["now"])
    if payload["action"] == "catalog":
        catalog = _catalog(now)
        _atomic_json(root / "catalog.json", catalog)
        return {"count": len(catalog["symbols"])}
    if _client is None:
        _client = TossQuoteClient(TossCredentials(configuration["key"], configuration["secret"]))
    if payload["action"] == "history":
        try:
            return _history(_client, root, payload["symbols"], payload["required"], now)
        except TossRateLimitError as exc:
            from fastapi import HTTPException
            raise HTTPException(429, "retry_after="+str(min(3600, max(1, exc.retry_after)))) from None
    if payload["action"] == "screen":
        try:
            return _screen(_client, root, payload, now)
        except TossRateLimitError as exc:
            from fastapi import HTTPException
            raise HTTPException(429, "retry_after="+str(min(3600, max(1, exc.retry_after)))) from None
    raise ValueError("Unknown automatic screening action")


_process = ProviderProcess(_execute)


def decision_for(settings, spec, now=None, *, require_fresh=True):
    now = now or dt.datetime.now(dt.timezone.utc)
    data = _read(root_for(settings) / "decisions.json", 1024*1024, {})
    decision = data.get(spec_digest(spec))
    if not isinstance(decision, dict):
        raise ValueError("미국 전체 종목 탐색·시세 수신 준비 중입니다")
    if require_fresh:
        stamp = dt.datetime.fromisoformat(decision["created_at"])
        catalog = _read(root_for(settings) / "catalog.json", 8*1024*1024, {})
        if (not 0 <= (now-stamp).total_seconds() <= DECISION_MAX_AGE
                or (decision.get("quote_as_of") is not None and not 0 <= (now-dt.datetime.fromisoformat(decision["quote_as_of"])).total_seconds() <= DECISION_MAX_AGE)
                or decision.get("history_session") != last_completed_session(now).isoformat()
                or catalog.get("date") != now.astimezone(EASTERN).date().isoformat()
                or decision.get("catalog_sha256") != catalog.get("sha256")):
            raise ValueError("전체 종목의 최신 탐색 결과를 기다립니다")
    return decision


def status(settings):
    return _read(root_for(settings) / "status.json", 16384, {"status": "waiting", "message": "미국 전체 종목 자동 탐색 준비 중"})


def _refresh(settings, specs, configuration, now=None):
    """One bounded work unit; the data worker loops quickly while preparing."""
    now = now or dt.datetime.now(dt.timezone.utc)
    root = root_for(settings)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = {**configuration, "root": str(root)}
    catalog = _read(root / "catalog.json", 8*1024*1024, {})
    stamp = now.astimezone(EASTERN).date().isoformat()
    def call(action, **extra):
        return _process.run({"action": action, "now": now.isoformat(), **extra}, config, deadline=time.monotonic()+75)
    if catalog.get("date") != stamp:
        call("catalog")
        catalog = _read(root / "catalog.json", 8*1024*1024)
    required = last_completed_session(now).isoformat()
    progress = _read(root / "progress.json", 4*1024*1024, {})
    if progress.get("session") != required or progress.get("catalog") != catalog["sha256"]:
        progress = {"session": required, "catalog": catalog["sha256"], "outcomes": {}}
    missing = [s for s in catalog["symbols"] if s not in progress["outcomes"]]
    if missing:
        _atomic_json(root / "status.json", {"status":"preparing", "universe_count":len(catalog["symbols"]),
            "prepared_count":len(progress["outcomes"]), "message":"미국 전체 {}종목 이력 준비 중: {}/{}".format(len(catalog["symbols"]),len(progress["outcomes"]),len(catalog["symbols"]))})
        outcomes = call("history", symbols=missing[:HISTORY_BATCH], required=required)
        progress["outcomes"].update(outcomes)
        _atomic_json(root / "progress.json", progress)
    remaining = len(catalog["symbols"])-len(progress["outcomes"])
    state = {"status": "preparing" if remaining else "ready", "universe_count": len(catalog["symbols"]),
             "prepared_count": len(progress["outcomes"]), "history_count": sum(v == "ready" for v in progress["outcomes"].values()),
             "unavailable_count": sum(v != "ready" for v in progress["outcomes"].values()), "history_session": required,
             "updated_at": now.isoformat(), "message": "미국 전체 {}종목: 이력 확인 {}/{} · 데이터 미제공 {}".format(
                 len(catalog["symbols"]), len(progress["outcomes"]), len(catalog["symbols"]), sum(v != "ready" for v in progress["outcomes"].values()))}
    _atomic_json(root / "status.json", state)
    if missing:
        # At most one provider work unit per heartbeat/lease interval.
        return True, []
    from .paper import regular_market_open
    selected = []
    retry = sorted(s for s, v in progress["outcomes"].items() if v != "ready")
    if retry and (progress.get("retry_pending") or not regular_market_open(now)):
        offset = progress.get("retry_offset", 0) % len(retry)
        batch = (retry + retry)[offset:offset+min(HISTORY_BATCH, len(retry))]
        progress["outcomes"].update(call("history", symbols=batch, required=required))
        progress["retry_offset"] = offset + len(batch)
        progress["retry_pending"] = False
        _atomic_json(root / "progress.json", progress)
        return regular_market_open(now), []
    if regular_market_open(now):
        screened = call("screen", specs=[spec.model_dump_json() for spec in specs])
        selected = screened["selected"]
        state.update(status="screened", message=state["message"]+" · 최신 토스 시세로 선정 완료")
        _atomic_json(root / "status.json", state)
    # Revisit unavailable securities between complete sweeps, preserving a
    # completed coverage record and bounded progress across restarts.
    progress["retry_pending"] = bool(retry)
    _atomic_json(root / "progress.json", progress)
    return False, selected


def backtest_settings(settings):
    # Already pinned by the research workflow.
    manifest = _read(settings.dataset_dir / "manifest.json", 8*1024*1024, {})
    if manifest.get("universe_mode") == "us_all":
        return settings
    return replace(settings, dataset_dir=root_for(settings) / "backtests")


def _prepare_backtest_generation(settings):
    """Publish immutable, complete current-listing history for reproducible tests."""
    root = root_for(settings)
    catalog = _read(root / "catalog.json", 8*1024*1024, {})
    progress = _read(root / "progress.json", 4*1024*1024, {})
    if not catalog or len(progress.get("outcomes", {})) < len(catalog["symbols"]):
        raise ValueError("전체 종목의 이력 준비가 끝난 뒤 다시 시도해 주세요")
    destination = root / "backtests"
    destination.mkdir(exist_ok=True)
    current = _read(destination / "current.json", 4096, {})
    if current.get("session") == progress["session"] and current.get("catalog") == catalog["sha256"]:
        return
    generations = destination / "generations"; generations.mkdir(exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".pending-", dir=generations))
    try:
        metadata = {}
        for symbol in catalog["symbols"]:
            item = _read(_history_path(root, symbol), MAX_HISTORY_BYTES)
            if not item or item.get("session") != progress["session"]: continue
            frame = _frame(item["rows"])
            if frame.index.max().date().isoformat() != progress["session"]:
                raise ValueError("History cache contains an unexpected session")
            path = price_file_path(staging / "prices", symbol)
            _atomic_price_frame(frame, path)
            metadata[symbol] = {"rows":len(frame), "first_date":frame.index.min().date().isoformat(),
                                "last_date":frame.index.max().date().isoformat(), "sha256":sha256_file(path)}
        if not metadata: raise ValueError("No current history is available")
        snapshot = build_legacy_snapshot({s:"NASDAQ" for s in metadata}, effective_date=progress["session"])
        snapshot.update(snapshot_type=DATASET_KIND, certification_eligible=False, provenance="Current US listings; exploratory history with survivorship bias")
        save_snapshot(snapshot, staging / "snapshots")
        _atomic_json(staging / "manifest.json", {"schema_version":2,"price_format":"csv-gzip-v1","dataset_kind":DATASET_KIND,
                     "universe_mode":"us_all", "prices":metadata,"corporate_actions":{}, "source":"toss_with_yahoo_fallback", "auto_adjust":True})
        _atomic_json(staging / "validation_report.json", {"forward_strategy_data_gate_ready":False,"strategy_candidate_data_blockers":[]})
        name = uuid.uuid4().hex; os.replace(staging, generations / name)
        _atomic_json(destination / "current.json", {"generation":name,"session":progress["session"],"catalog":catalog["sha256"]})
    finally:
        if staging.exists(): shutil.rmtree(staging)


def prepare_backtest_generation(settings):
    from . import native_platform as locks
    settings.dataset_dir.mkdir(parents=True, exist_ok=True)
    with (settings.dataset_dir / "refresh.lock").open("a+") as lock:
        locks.flock(lock, locks.LOCK_EX)
        return _prepare_backtest_generation(settings)


def refresh(settings, specs, configuration, now=None):
    """Publish an actionable failure and enforce cooldown across restarts."""
    from .provider_process import ProviderOperationError
    now = now or dt.datetime.now(dt.timezone.utc)
    previous = status(settings)
    retry = previous.get("retry_at")
    if retry and now < dt.datetime.fromisoformat(retry):
        return False, []
    try:
        return _refresh(settings, specs, configuration, now)
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        code = exc.status_code if isinstance(exc, ProviderOperationError) else 503
        message = ("토스 요청 한도에 도달했습니다. 자동 재시도 대기" if code == 429 else
                   "전체 종목 데이터 수신·검증을 완료하지 못했습니다. 토스 인증·IP·네트워크 상태를 확인하세요. 기존 원장은 보존하며 자동 재시도합니다")
        delay = 60
        if code == 429 and str(exc.detail).startswith("retry_after="):
            try:
                delay = max(60, min(3600, float(exc.detail.split("=",1)[1])))
            except ValueError:
                pass
        _atomic_json(root_for(settings) / "status.json", {**previous, "status":"retry_wait", "message":message,
            "updated_at":now.isoformat(), "retry_at":(now+dt.timedelta(seconds=delay)).isoformat(), "error_code":code})
        return False, []
