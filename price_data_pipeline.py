"""Reproducible 2026 OHLCV dataset builder and quality gate.

The builder keeps research datasets separate from the live ``data_cache`` so
refreshing adjusted prices cannot splice two incompatible adjustment bases.
Every run records the universe snapshot hashes, provider parameters, file
hashes, failures, and quality results in ``manifest.json``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Mapping, Optional

import numpy as np
import pandas as pd

from terminal_events import load_events, unresolved_events
from universe_snapshot import eligible_symbols, load_snapshot


REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
UF_DATALESS = 0x40000000


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_dataless(path: Path | str) -> bool:
    flags = getattr(os.stat(path), "st_flags", 0)
    return bool(flags & UF_DATALESS)


def hydration_status(data_dir: Path | str) -> dict:
    paths = list(Path(data_dir).glob("*_data.pkl"))
    dataless = sum(is_dataless(path) for path in paths)
    return {
        "files": len(paths),
        "dataless": dataless,
        "hydrated": len(paths) - dataless,
        "hydrated_rate": (len(paths) - dataless) / len(paths) if paths else 0.0,
    }


def request_hydration(data_dir: Path | str) -> dict:
    data_dir = Path(data_dir)
    before = hydration_status(data_dir)
    executable = "/usr/bin/brctl"
    if not Path(executable).exists():
        raise RuntimeError("brctl is only available for iCloud-backed data on macOS")
    subprocess.run([executable, "download", str(data_dir)], check=True)
    after = hydration_status(data_dir)
    return {"before": before, "after_request": after}


def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("price payload is not a DataFrame")
    frame = frame.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        raise ValueError("per-symbol price frame must not have MultiIndex columns")
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("missing columns: {}".format(missing))
    index = pd.to_datetime(frame.index, errors="coerce")
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert(None)
    frame.index = pd.DatetimeIndex(index).normalize()
    frame = frame[~frame.index.isna()]
    frame = frame.loc[:, list(REQUIRED_COLUMNS)]
    for column in REQUIRED_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.sort_index()
    return frame


def validate_price_frame(
    frame: pd.DataFrame,
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    ohlc_relative_tolerance: float = 1e-6,
) -> dict:
    try:
        normalized = _normalize_frame(frame)
    except Exception as exc:
        return {"valid": False, "error": str(exc)}
    duplicate_rows = int(normalized.index.duplicated(keep=False).sum())
    window = normalized
    if start is not None:
        window = window[window.index >= pd.Timestamp(start)]
    if end is not None:
        window = window[window.index <= pd.Timestamp(end)]

    prices = window[["Open", "High", "Low", "Close"]]
    invalid_numeric = int((~np.isfinite(prices.to_numpy(dtype=float))).any(axis=1).sum())
    nonpositive_prices = int((prices <= 0).any(axis=1).sum())
    row_scale = prices.abs().max(axis=1).clip(lower=1.0)
    ohlc_tolerance = row_scale * float(ohlc_relative_tolerance)
    bad_ohlc = int(
        (
            (
                window["High"] + ohlc_tolerance
                < window[["Open", "Close", "Low"]].max(axis=1)
            )
            | (
                window["Low"] - ohlc_tolerance
                > window[["Open", "Close", "High"]].min(axis=1)
            )
        ).sum()
    )
    bad_volume = int(((window["Volume"] < 0) | ~np.isfinite(window["Volume"])).sum())
    valid = bool(
        len(window) > 0
        and duplicate_rows == 0
        and invalid_numeric == 0
        and nonpositive_prices == 0
        and bad_ohlc == 0
        and bad_volume == 0
    )
    return {
        "valid": valid,
        "rows_total": int(len(normalized)),
        "rows_window": int(len(window)),
        "first_date": normalized.index.min().date().isoformat() if len(normalized) else None,
        "last_date": normalized.index.max().date().isoformat() if len(normalized) else None,
        "duplicate_rows": duplicate_rows,
        "invalid_numeric_rows": invalid_numeric,
        "nonpositive_price_rows": nonpositive_prices,
        "bad_ohlc_rows": bad_ohlc,
        "bad_volume_rows": bad_volume,
        "ohlc_relative_tolerance": float(ohlc_relative_tolerance),
    }


def repair_ohlc_bounds(
    frame: pd.DataFrame, *, max_relative_deviation: float = 0.10
) -> tuple[pd.DataFrame, list[dict]]:
    """Repair only self-contradictory High/Low bounds, preserving O/C/V.

    Some completed Yahoo daily bars temporarily report High below Open/Close or
    Low above Open/Close.  The values used by strategy signals (Close, Volume)
    and next-session execution are never changed.  Repairs above the explicit
    relative limit remain invalid and therefore keep the forward gate closed.
    """
    normalized = _normalize_frame(frame)
    repaired = normalized.copy()
    repairs = []
    limit = float(max_relative_deviation)
    if not 0 <= limit <= 1:
        raise ValueError("max_relative_deviation must be between 0 and 1")
    for date, row in normalized.iterrows():
        values = [float(row[column]) for column in ("Open", "High", "Low", "Close")]
        if not all(np.isfinite(value) and value > 0 for value in values):
            continue
        open_price, high, low, close = values
        repaired_high = max(open_price, high, low, close)
        repaired_low = min(open_price, high, low, close)
        if repaired_high == high and repaired_low == low:
            continue
        deviation = max(repaired_high - high, low - repaired_low, 0.0)
        scale = max(abs(value) for value in values)
        relative = deviation / max(scale, 1e-9)
        if relative > limit:
            continue
        repaired.at[date, "High"] = repaired_high
        repaired.at[date, "Low"] = repaired_low
        repairs.append(
            {
                "date": pd.Timestamp(date).date().isoformat(),
                "original_high": high,
                "original_low": low,
                "repaired_high": repaired_high,
                "repaired_low": repaired_low,
                "relative_deviation": relative,
            }
        )
    return repaired, repairs


def _extract_download(raw: pd.DataFrame, ticker: str, batch_size: int) -> Optional[pd.DataFrame]:
    if raw is None or raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = set(map(str, raw.columns.get_level_values(0)))
        level1 = set(map(str, raw.columns.get_level_values(1)))
        if ticker in level0:
            frame = raw[ticker]
        elif ticker in level1:
            frame = raw.xs(ticker, axis=1, level=1)
        else:
            return None
    elif batch_size == 1:
        frame = raw
    else:
        return None
    try:
        return _normalize_frame(frame).dropna(how="any")
    except Exception:
        return None


def _atomic_pickle(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    os.close(descriptor)
    try:
        frame.to_pickle(temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_json(value: Mapping, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_dataset(
    snapshot_paths: Iterable[Path | str],
    output_dir: Path | str,
    *,
    start: str = "2025-09-01",
    end: Optional[str] = None,
    batch_size: int = 50,
    retries: int = 2,
    limit: Optional[int] = None,
    allow_uncertified_snapshots: bool = False,
) -> dict:
    """Download full adjusted OHLCV windows for the union of given snapshots."""
    import yfinance as yf

    snapshots = [load_snapshot(path) for path in snapshot_paths]
    if not snapshots:
        raise ValueError("At least one universe snapshot is required")
    uncertified = [
        snapshot.get("snapshot_type")
        for snapshot in snapshots
        if not snapshot.get("certification_eligible", False)
    ]
    if uncertified and not allow_uncertified_snapshots:
        raise ValueError(
            "Uncertified snapshots cannot build a decision-grade dataset: {}".format(
                uncertified
            )
        )
    symbols = sorted(set().union(*(eligible_symbols(snapshot) for snapshot in snapshots)))
    if limit is not None:
        symbols = symbols[: max(0, int(limit))]
    output_dir = Path(output_dir)
    price_dir = output_dir / "prices"
    end = end or (dt.date.today() + dt.timedelta(days=1)).isoformat()

    succeeded = {}
    failed = {}
    started_at = dt.datetime.now(dt.timezone.utc)
    for offset in range(0, len(symbols), batch_size):
        batch = symbols[offset : offset + batch_size]
        raw = None
        last_error = None
        for attempt in range(retries + 1):
            try:
                raw = yf.download(
                    " ".join(batch),
                    start=start,
                    end=end,
                    auto_adjust=True,
                    actions=False,
                    progress=False,
                    group_by="ticker",
                    threads=True,
                    timeout=30,
                )
                if raw is not None and not raw.empty:
                    break
            except Exception as exc:
                last_error = str(exc)
            if attempt < retries:
                time.sleep(2 ** attempt)

        for ticker in batch:
            frame = _extract_download(raw, ticker, len(batch)) if raw is not None else None
            if frame is None or frame.empty:
                failed[ticker] = last_error or "empty_download"
                continue
            quality = validate_price_frame(frame, start=start, end=end)
            if not quality["valid"]:
                failed[ticker] = "quality:{}".format(quality)
                continue
            path = price_dir / "{}_data.pkl".format(ticker)
            _atomic_pickle(frame, path)
            succeeded[ticker] = {
                "rows": int(len(frame)),
                "first_date": frame.index.min().date().isoformat(),
                "last_date": frame.index.max().date().isoformat(),
                "sha256": sha256_file(path),
            }
        print(
            "downloaded {}/{} valid={} failed={}".format(
                min(offset + batch_size, len(symbols)),
                len(symbols),
                len(succeeded),
                len(failed),
            ),
            flush=True,
        )

    manifest = {
        "schema_version": 1,
        "dataset_type": "exchange_listed_2026_ohlcv",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "duration_seconds": (
            dt.datetime.now(dt.timezone.utc) - started_at
        ).total_seconds(),
        "provider": "yfinance",
        "provider_parameters": {
            "start": start,
            "end_exclusive": end,
            "auto_adjust": True,
            "actions": False,
            "interval": "1d",
        },
        "snapshot_paths": [str(Path(path)) for path in snapshot_paths],
        "snapshot_membership_sha256": [
            snapshot["membership_sha256"] for snapshot in snapshots
        ],
        "certification_eligible_snapshots": all(
            snapshot.get("certification_eligible", False) for snapshot in snapshots
        ),
        "requested_count": len(symbols),
        "valid_count": len(succeeded),
        "failed_count": len(failed),
        "prices": succeeded,
        "failures": failed,
    }
    _atomic_json(manifest, output_dir / "manifest.json")
    return manifest


def finalize_completed_sessions(
    dataset_dir: Path | str,
    *,
    end_exclusive: str,
    batch_size: int = 50,
    retries: int = 2,
) -> dict:
    """Drop an incomplete current session and retry only prior failures."""
    import yfinance as yf

    dataset_dir = Path(dataset_dir)
    manifest_path = dataset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cutoff = pd.Timestamp(end_exclusive)
    price_dir = dataset_dir / "prices"
    quarantine_dir = dataset_dir / "quarantine_prices"
    succeeded = {}
    failures = dict(manifest.get("failures", {}))

    # Existing files passed the earlier gate.  Remove the incomplete session,
    # validate again, and create hashes for the exact completed-session slice.
    for ticker in sorted(manifest.get("prices", {})):
        path = price_dir / "{}_data.pkl".format(ticker)
        try:
            frame = _normalize_frame(pd.read_pickle(path))
            frame = frame[frame.index < cutoff]
            quality = validate_price_frame(frame)
            if not quality["valid"]:
                failures[ticker] = "post_trim_quality:{}".format(quality)
                continue
            _atomic_pickle(frame, path)
            succeeded[ticker] = {
                "rows": int(len(frame)),
                "first_date": frame.index.min().date().isoformat(),
                "last_date": frame.index.max().date().isoformat(),
                "sha256": sha256_file(path),
            }
        except Exception as exc:
            failures[ticker] = "post_trim_error:{}".format(exc)

    retry_symbols = sorted(failures)
    remaining_failures = {}
    quarantine = {}
    start = manifest["provider_parameters"]["start"]
    for offset in range(0, len(retry_symbols), batch_size):
        batch = retry_symbols[offset : offset + batch_size]
        raw = None
        last_error = None
        for attempt in range(retries + 1):
            try:
                raw = yf.download(
                    " ".join(batch),
                    start=start,
                    end=end_exclusive,
                    auto_adjust=True,
                    actions=False,
                    progress=False,
                    group_by="ticker",
                    threads=True,
                    timeout=30,
                )
                if raw is not None and not raw.empty:
                    break
            except Exception as exc:
                last_error = str(exc)
            if attempt < retries:
                time.sleep(2 ** attempt)

        for ticker in batch:
            frame = _extract_download(raw, ticker, len(batch)) if raw is not None else None
            if frame is None or frame.empty:
                remaining_failures[ticker] = last_error or "empty_download"
                continue
            frame = frame[frame.index < cutoff]
            quality = validate_price_frame(frame)
            if quality["valid"]:
                path = price_dir / "{}_data.pkl".format(ticker)
                _atomic_pickle(frame, path)
                succeeded[ticker] = {
                    "rows": int(len(frame)),
                    "first_date": frame.index.min().date().isoformat(),
                    "last_date": frame.index.max().date().isoformat(),
                    "sha256": sha256_file(path),
                }
                continue
            quarantine_path = quarantine_dir / "{}_data.pkl".format(ticker)
            _atomic_pickle(frame, quarantine_path)
            quarantine[ticker] = {
                "quality": quality,
                "sha256": sha256_file(quarantine_path),
            }
            remaining_failures[ticker] = "quality:{}".format(quality)
        print(
            "retried {}/{} recovered={} remaining={}".format(
                min(offset + batch_size, len(retry_symbols)),
                len(retry_symbols),
                len(succeeded) - len(manifest.get("prices", {})),
                len(remaining_failures),
            ),
            flush=True,
        )

    manifest["finalized_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest["provider_parameters"]["end_exclusive"] = end_exclusive
    manifest["completed_sessions_only"] = True
    manifest["prices"] = succeeded
    manifest["failures"] = remaining_failures
    manifest["quarantine"] = quarantine
    manifest["valid_count"] = len(succeeded)
    manifest["failed_count"] = len(remaining_failures)
    # A ticker recovered in an earlier run can leave a stale file behind even
    # after the completed-session slice proves unusable.  Keep it for audit,
    # but move it outside ``prices`` so no ad-hoc glob loader can include it.
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    for ticker in remaining_failures:
        stale_path = price_dir / "{}_data.pkl".format(ticker)
        if not stale_path.exists():
            continue
        audit_path = quarantine_dir / "{}_stale_data.pkl".format(ticker)
        os.replace(stale_path, audit_path)
        quarantine.setdefault(ticker, {})["stale_file_sha256"] = sha256_file(audit_path)
    _atomic_json(manifest, manifest_path)
    return manifest


def update_completed_sessions(
    dataset_dir: Path | str,
    snapshot_paths: Iterable[Path | str],
    *,
    end_exclusive: str,
    batch_size: int = 50,
    retries: int = 2,
) -> dict:
    """Append completed sessions and add symbols from new PIT snapshots.

    Existing files are retained for securities that disappeared or were
    halted; a transient provider failure never deletes an already verified
    history. If adjusted overlap changes (usually a split), the complete
    series is fetched again and the manifest records the superseded hash.
    """
    import yfinance as yf

    dataset_dir = Path(dataset_dir)
    manifest_path = dataset_dir / "manifest.json"
    lock_path = dataset_dir / ".update.lock"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        snapshots = [load_snapshot(path) for path in snapshot_paths]
        if not snapshots:
            raise ValueError("At least one current snapshot is required")
        if any(not item.get("certification_eligible", False) for item in snapshots):
            raise ValueError("Daily updates require certified exchange-directory snapshots")

        cutoff = pd.Timestamp(end_exclusive)
        full_start = str(manifest["provider_parameters"]["start"])
        recent_start = (cutoff - pd.Timedelta(days=14)).date().isoformat()
        existing = set(manifest.get("prices", {}))
        current_members = set().union(*(eligible_symbols(item) for item in snapshots))
        requested = sorted(existing | current_members)
        price_dir = dataset_dir / "prices"
        previous_hashes = {}
        refresh_errors = {}
        ohlc_bound_repairs = {}
        added = []
        restated = []

        def download(batch, start):
            raw = None
            last_error = None
            for attempt in range(retries + 1):
                try:
                    raw = yf.download(
                        " ".join(batch),
                        start=start,
                        end=end_exclusive,
                        auto_adjust=True,
                        actions=False,
                        progress=False,
                        group_by="ticker",
                        threads=True,
                        timeout=30,
                    )
                    if raw is not None and not raw.empty:
                        return raw, None
                except Exception as exc:
                    last_error = str(exc)
                if attempt < retries:
                    time.sleep(2 ** attempt)
            return raw, last_error or "empty_download"

        for offset in range(0, len(requested), batch_size):
            batch = requested[offset : offset + batch_size]
            old_batch = [ticker for ticker in batch if ticker in existing]
            new_batch = [ticker for ticker in batch if ticker not in existing]
            payloads = []
            if old_batch:
                payloads.append((old_batch, recent_start, *download(old_batch, recent_start)))
            if new_batch:
                payloads.append((new_batch, full_start, *download(new_batch, full_start)))
            for symbols, start, raw, batch_error in payloads:
                for ticker in symbols:
                    fresh = _extract_download(raw, ticker, len(symbols)) if raw is not None else None
                    path = price_dir / "{}_data.pkl".format(ticker)
                    if fresh is None or fresh.empty:
                        refresh_errors[ticker] = batch_error or "empty_download"
                        continue
                    fresh = fresh[fresh.index < cutoff]
                    fresh, ticker_repairs = repair_ohlc_bounds(fresh)
                    if ticker in existing and path.exists():
                        old = _normalize_frame(pd.read_pickle(path))
                        overlap = old.index.intersection(fresh.index)
                        needs_restatement = False
                        if len(overlap):
                            old_close = old.loc[overlap, "Close"].astype(float)
                            new_close = fresh.loc[overlap, "Close"].astype(float)
                            relative = ((old_close - new_close).abs() / new_close.abs().clip(lower=1e-9))
                            needs_restatement = bool((relative > 1e-5).any())
                        if needs_restatement:
                            full_raw, full_error = download([ticker], full_start)
                            full = _extract_download(full_raw, ticker, 1) if full_raw is not None else None
                            if full is None or full.empty:
                                refresh_errors[ticker] = "restatement_failed:{}".format(full_error)
                                continue
                            combined = full[full.index < cutoff]
                            combined, ticker_repairs = repair_ohlc_bounds(combined)
                            restated.append(ticker)
                        else:
                            combined = pd.concat([old, fresh]).sort_index()
                            combined = combined[~combined.index.duplicated(keep="last")]
                    else:
                        combined = fresh
                        added.append(ticker)
                    quality = validate_price_frame(combined)
                    if not quality["valid"]:
                        refresh_errors[ticker] = "quality:{}".format(quality)
                        continue
                    if path.exists():
                        previous_hashes[ticker] = manifest["prices"][ticker]["sha256"]
                    _atomic_pickle(combined, path)
                    manifest.setdefault("prices", {})[ticker] = {
                        "rows": int(len(combined)),
                        "first_date": combined.index.min().date().isoformat(),
                        "last_date": combined.index.max().date().isoformat(),
                        "sha256": sha256_file(path),
                    }
                    if ticker_repairs:
                        ohlc_bound_repairs[ticker] = ticker_repairs
            print(
                "updated {}/{} added={} errors={}".format(
                    min(offset + batch_size, len(requested)), len(requested), len(added), len(refresh_errors)
                ),
                flush=True,
            )

        known_paths = list(manifest.get("snapshot_paths", []))
        known_hashes = list(manifest.get("snapshot_membership_sha256", []))
        for path, snapshot in zip(snapshot_paths, snapshots):
            if snapshot["membership_sha256"] not in known_hashes:
                known_paths.append(str(Path(path)))
                known_hashes.append(snapshot["membership_sha256"])
        manifest["snapshot_paths"] = known_paths
        manifest["snapshot_membership_sha256"] = known_hashes
        manifest["provider_parameters"]["end_exclusive"] = end_exclusive
        manifest["completed_sessions_only"] = True
        manifest["last_incremental_update_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        manifest["last_incremental_previous_hashes"] = previous_hashes
        manifest["last_incremental_restated_symbols"] = sorted(restated)
        manifest["last_incremental_ohlc_bound_repairs"] = ohlc_bound_repairs
        manifest["last_incremental_refresh_errors"] = refresh_errors
        manifest.setdefault("quality_rule", {})["incremental_ohlc_bound_repair"] = {
            "max_relative_deviation": 0.10,
            "preserved_columns": ["Open", "Close", "Volume"],
            "formula": "High=max(High,Open,Close,Low); Low=min(Low,Open,Close,High)",
        }
        manifest["valid_count"] = len(manifest.get("prices", {}))
        manifest["requested_count"] = len(requested)
        manifest["failed_count"] = len(manifest.get("failures", {}))
        _atomic_json(manifest, manifest_path)
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    return {
        "updated_count": len(requested) - len(refresh_errors),
        "added": sorted(added),
        "restated": sorted(restated),
        "ohlc_bound_repair_tickers": sorted(ohlc_bound_repairs),
        "ohlc_bound_repair_rows": sum(len(rows) for rows in ohlc_bound_repairs.values()),
        "refresh_errors": refresh_errors,
        "end_exclusive": end_exclusive,
    }


def validate_dataset(
    dataset_dir: Path | str,
    *,
    start: str,
    end: str,
    current_snapshot_path: Optional[Path | str] = None,
    events_path: Optional[Path | str] = None,
    workers: int = 8,
) -> dict:
    dataset_dir = Path(dataset_dir)
    manifest_path = dataset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = set(manifest.get("prices", {}))
    current_snapshot_membership_sha256 = None
    if current_snapshot_path is not None:
        current_snapshot = load_snapshot(current_snapshot_path)
        expected = eligible_symbols(current_snapshot)
        current_snapshot_membership_sha256 = current_snapshot["membership_sha256"]

    results = {}

    def inspect(ticker: str) -> tuple[str, dict]:
        if ticker not in manifest.get("prices", {}):
            return ticker, {
                "valid": False,
                "error": "manifest_failure:{}".format(
                    manifest.get("failures", {}).get(ticker, "not_in_manifest")
                ),
            }
        path = dataset_dir / "prices" / "{}_data.pkl".format(ticker)
        if not path.exists():
            return ticker, {"valid": False, "error": "missing_file"}
        try:
            frame = pd.read_pickle(path)
        except Exception as exc:
            return ticker, {"valid": False, "error": "read_error:{}".format(exc)}
        result = validate_price_frame(frame, start=start, end=end)
        if result.get("valid"):
            result["sha256"] = sha256_file(path)
        return ticker, result

    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as executor:
        futures = {executor.submit(inspect, ticker): ticker for ticker in sorted(expected)}
        for future in as_completed(futures):
            ticker, result = future.result()
            results[ticker] = result

    invalid = {ticker: result for ticker, result in results.items() if not result.get("valid")}
    unresolved = []
    if events_path is not None:
        unresolved = unresolved_events(load_events(events_path), through=end)
    strategy_blockers = []
    data_availability_exclusions = []
    for ticker in sorted(invalid):
        quarantine_path = dataset_dir / "quarantine_prices" / "{}_data.pkl".format(ticker)
        executable_path = dataset_dir / "prices" / "{}_data.pkl".format(ticker)
        # A failed incremental row is not placed in quarantine because the
        # previously verified history must remain executable. Use that prior
        # history to decide whether silently excluding the ticker today would
        # remove an otherwise eligible strategy candidate.
        candidate_evidence_path = (
            quarantine_path if quarantine_path.exists() else executable_path
        )
        if not candidate_evidence_path.exists():
            data_availability_exclusions.append(ticker)
            continue
        try:
            frame = _normalize_frame(pd.read_pickle(candidate_evidence_path))
            recent = frame[frame.index <= pd.Timestamp(end)].tail(60)
            would_pass_screen = bool(
                len(recent) >= 60
                and float(recent["Close"].iloc[-1]) >= 5.0
                and float(recent["Volume"].mean()) >= 200_000
            )
        except Exception:
            would_pass_screen = True
        if would_pass_screen:
            strategy_blockers.append(ticker)
        else:
            data_availability_exclusions.append(ticker)

    report = {
        "schema_version": 1,
        "validated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dataset_dir": str(dataset_dir),
        "window": {"start": start, "end": end},
        "current_snapshot_membership_sha256": current_snapshot_membership_sha256,
        "expected_count": len(expected),
        "valid_count": len(results) - len(invalid),
        "invalid_count": len(invalid),
        "unresolved_terminal_event_count": len(unresolved),
        "certification_ready": len(invalid) == 0 and len(unresolved) == 0,
        "forward_strategy_data_gate_ready": (
            len(strategy_blockers) == 0 and len(unresolved) == 0
        ),
        "strategy_candidate_data_blockers": strategy_blockers,
        "data_availability_exclusions": data_availability_exclusions,
        "invalid": invalid,
        "unresolved_terminal_events": unresolved,
    }
    _atomic_json(report, dataset_dir / "validation_report.json")
    return report


def reconcile_dataset_storage(dataset_dir: Path | str) -> dict:
    """Ensure only manifest-approved symbols remain in the executable price directory."""
    dataset_dir = Path(dataset_dir)
    manifest_path = dataset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    price_dir = dataset_dir / "prices"
    quarantine_dir = dataset_dir / "quarantine_prices"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    approved = set(manifest.get("prices", {}))
    moved = []
    for path in sorted(price_dir.glob("*_data.pkl")):
        ticker = path.name[: -len("_data.pkl")]
        if ticker in approved:
            continue
        destination = quarantine_dir / "{}_stale_data.pkl".format(ticker)
        os.replace(path, destination)
        manifest.setdefault("quarantine", {}).setdefault(ticker, {})[
            "stale_file_sha256"
        ] = sha256_file(destination)
        moved.append(ticker)
    missing_approved = sorted(
        ticker
        for ticker in approved
        if not (price_dir / "{}_data.pkl".format(ticker)).exists()
    )
    manifest["storage_reconciled_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest["storage_approved_file_count"] = len(approved) - len(missing_approved)
    manifest["storage_missing_approved"] = missing_approved
    _atomic_json(manifest, manifest_path)
    return {
        "approved_count": len(approved),
        "moved_to_quarantine": moved,
        "missing_approved": missing_approved,
    }


def recover_quarantine(dataset_dir: Path | str) -> dict:
    """Promote quarantined frames that pass the current, versioned quality rules."""
    dataset_dir = Path(dataset_dir)
    manifest_path = dataset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    price_dir = dataset_dir / "prices"
    quarantine_dir = dataset_dir / "quarantine_prices"
    recovered = []
    still_invalid = {}
    for ticker in sorted(manifest.get("failures", {})):
        path = quarantine_dir / "{}_data.pkl".format(ticker)
        if not path.exists():
            still_invalid[ticker] = manifest["failures"][ticker]
            continue
        try:
            frame = _normalize_frame(pd.read_pickle(path))
            quality = validate_price_frame(frame)
        except Exception as exc:
            still_invalid[ticker] = "quarantine_read_error:{}".format(exc)
            continue
        if not quality["valid"]:
            still_invalid[ticker] = "quality:{}".format(quality)
            continue
        destination = price_dir / "{}_data.pkl".format(ticker)
        _atomic_pickle(frame, destination)
        manifest.setdefault("prices", {})[ticker] = {
            "rows": int(len(frame)),
            "first_date": frame.index.min().date().isoformat(),
            "last_date": frame.index.max().date().isoformat(),
            "sha256": sha256_file(destination),
            "recovered_from_quarantine": True,
        }
        recovered.append(ticker)
    manifest["failures"] = still_invalid
    manifest["valid_count"] = len(manifest.get("prices", {}))
    manifest["failed_count"] = len(still_invalid)
    manifest["quality_rule"] = {"ohlc_relative_tolerance": 1e-6}
    manifest["quarantine_rechecked_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    _atomic_json(manifest, manifest_path)
    return {"recovered": recovered, "remaining_failures": still_invalid}


def derive_dataset_for_snapshot(
    parent_dataset_dir: Path | str,
    snapshot_path: Path | str,
    output_dir: Path | str,
) -> dict:
    """Create an exact snapshot subset using hard links to verified parent files."""
    parent_dataset_dir = Path(parent_dataset_dir)
    output_dir = Path(output_dir)
    snapshot_path = Path(snapshot_path)
    parent_manifest_path = parent_dataset_dir / "manifest.json"
    parent = json.loads(parent_manifest_path.read_text(encoding="utf-8"))
    snapshot = load_snapshot(snapshot_path)
    if not snapshot.get("certification_eligible", False):
        raise ValueError("Cannot derive from an uncertified universe snapshot")
    requested = sorted(eligible_symbols(snapshot))
    price_dir = output_dir / "prices"
    price_dir.mkdir(parents=True, exist_ok=True)
    prices = {}
    failures = {}
    for ticker in requested:
        metadata = parent.get("prices", {}).get(ticker)
        source = parent_dataset_dir / "prices" / "{}_data.pkl".format(ticker)
        destination = price_dir / "{}_data.pkl".format(ticker)
        if metadata is None or not source.exists():
            failures[ticker] = parent.get("failures", {}).get(
                ticker, "not_available_in_parent_dataset"
            )
            continue
        if not destination.exists():
            try:
                os.link(source, destination)
            except OSError:
                shutil.copy2(source, destination)
        actual_hash = sha256_file(destination)
        if actual_hash != metadata["sha256"]:
            raise ValueError("Derived price hash mismatch for {}".format(ticker))
        prices[ticker] = dict(metadata)

    manifest = {
        "schema_version": 1,
        "dataset_type": "derived_exchange_listed_equity_ohlcv",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "derived_from_dataset": str(parent_dataset_dir),
        "derived_from_manifest_sha256": sha256_file(parent_manifest_path),
        "provider": parent.get("provider"),
        "provider_parameters": parent.get("provider_parameters", {}),
        "completed_sessions_only": parent.get("completed_sessions_only", False),
        "snapshot_paths": [str(snapshot_path)],
        "snapshot_membership_sha256": [snapshot["membership_sha256"]],
        "certification_eligible_snapshots": True,
        "requested_count": len(requested),
        "valid_count": len(prices),
        "failed_count": len(failures),
        "prices": prices,
        "failures": failures,
        "quality_rule": parent.get("quality_rule", {}),
    }
    _atomic_json(manifest, output_dir / "manifest.json")
    return manifest


def load_price_dataset(dataset_dir: Path | str) -> dict[str, pd.DataFrame]:
    dataset_dir = Path(dataset_dir)
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    data = {}
    for ticker, metadata in manifest.get("prices", {}).items():
        path = dataset_dir / "prices" / "{}_data.pkl".format(ticker)
        if sha256_file(path) != metadata["sha256"]:
            raise ValueError("Price hash mismatch: {}".format(path))
        data[ticker] = _normalize_frame(pd.read_pickle(path))
    return data


def build_eligibility_mask(
    snapshots: Iterable[Mapping],
    index: pd.DatetimeIndex,
    columns: Iterable[str],
    *,
    pre_snapshot_policy: str = "none",
    allow_uncertified_snapshots: bool = False,
) -> pd.DataFrame:
    """Build a date-by-symbol membership mask from frozen snapshots.

    ``pre_snapshot_policy='none'`` is the strict default.  ``'first'`` applies
    the first later snapshot retrospectively and must only be used for the
    explicitly caveated current-universe 2026 exploratory run.
    """
    if pre_snapshot_policy not in {"none", "first"}:
        raise ValueError("pre_snapshot_policy must be none/first")
    ordered = sorted(snapshots, key=lambda item: str(item["effective_date"]))
    if not allow_uncertified_snapshots:
        invalid = [
            snapshot.get("snapshot_type")
            for snapshot in ordered
            if not snapshot.get("certification_eligible", False)
        ]
        if invalid:
            raise ValueError("Uncertified membership snapshots: {}".format(invalid))
    columns = list(columns)
    mask = pd.DataFrame(False, index=pd.DatetimeIndex(index), columns=columns)
    if not ordered:
        return mask
    if pre_snapshot_policy == "first":
        mask.loc[:, list(set(columns) & eligible_symbols(ordered[0]))] = True
    for position, snapshot in enumerate(ordered):
        start = pd.Timestamp(snapshot["effective_date"])
        end = (
            pd.Timestamp(ordered[position + 1]["effective_date"]) - pd.Timedelta(days=1)
            if position + 1 < len(ordered)
            else None
        )
        rows = mask.index >= start
        if end is not None:
            rows &= mask.index <= end
        mask.loc[rows, :] = False
        members = list(set(columns) & eligible_symbols(snapshot))
        mask.loc[rows, members] = True
    return mask


def build_strategy_eligibility_mask(
    data: Mapping[str, pd.DataFrame],
    snapshots: Iterable[Mapping],
    index: pd.DatetimeIndex,
    *,
    min_history: int = 60,
    min_average_volume: float = 200_000,
    min_price: float = 5.0,
    pre_snapshot_policy: str = "none",
) -> pd.DataFrame:
    """Combine PIT listing membership with date-local liquidity/price rules."""
    columns = sorted(data)
    membership = build_eligibility_mask(
        snapshots,
        index,
        columns,
        pre_snapshot_policy=pre_snapshot_policy,
    )
    close = pd.DataFrame(
        {ticker: frame["Close"] for ticker, frame in data.items()}, index=index
    )
    volume = pd.DataFrame(
        {ticker: frame["Volume"] for ticker, frame in data.items()}, index=index
    )
    history = close.notna().rolling(min_history, min_periods=min_history).sum()
    average_volume = volume.rolling(min_history, min_periods=min_history).mean()
    liquid = (
        (history >= min_history)
        & (average_volume >= float(min_average_volume))
        & (close >= float(min_price))
    )
    return membership & liquid.fillna(False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate a 2026 OHLCV dataset")
    subparsers = parser.add_subparsers(dest="command", required=True)

    hydrate_parser = subparsers.add_parser("hydrate")
    hydrate_parser.add_argument("--data-dir", type=Path, default=Path("data_cache"))

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("--snapshot", action="append", required=True, type=Path)
    download_parser.add_argument("--output-dir", required=True, type=Path)
    download_parser.add_argument("--start", default="2025-09-01")
    download_parser.add_argument("--end")
    download_parser.add_argument("--batch-size", type=int, default=50)
    download_parser.add_argument("--limit", type=int)
    download_parser.add_argument("--allow-uncertified-snapshots", action="store_true")

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--dataset-dir", required=True, type=Path)
    finalize_parser.add_argument("--end-exclusive", required=True)
    finalize_parser.add_argument("--batch-size", type=int, default=50)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--dataset-dir", required=True, type=Path)
    update_parser.add_argument("--snapshot", action="append", required=True, type=Path)
    update_parser.add_argument("--end-exclusive", required=True)
    update_parser.add_argument("--batch-size", type=int, default=50)

    reconcile_parser = subparsers.add_parser("reconcile")
    reconcile_parser.add_argument("--dataset-dir", required=True, type=Path)

    recover_parser = subparsers.add_parser("recover")
    recover_parser.add_argument("--dataset-dir", required=True, type=Path)

    derive_parser = subparsers.add_parser("derive")
    derive_parser.add_argument("--parent-dataset-dir", required=True, type=Path)
    derive_parser.add_argument("--snapshot", required=True, type=Path)
    derive_parser.add_argument("--output-dir", required=True, type=Path)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--dataset-dir", required=True, type=Path)
    validate_parser.add_argument("--start", default="2026-01-02")
    validate_parser.add_argument("--end", required=True)
    validate_parser.add_argument("--current-snapshot", type=Path)
    validate_parser.add_argument("--events", type=Path)
    args = parser.parse_args()

    if args.command == "hydrate":
        result = request_hydration(args.data_dir)
    elif args.command == "download":
        result = build_dataset(
            args.snapshot,
            args.output_dir,
            start=args.start,
            end=args.end,
            batch_size=args.batch_size,
            limit=args.limit,
            allow_uncertified_snapshots=args.allow_uncertified_snapshots,
        )
    elif args.command == "finalize":
        result = finalize_completed_sessions(
            args.dataset_dir,
            end_exclusive=args.end_exclusive,
            batch_size=args.batch_size,
        )
    elif args.command == "update":
        result = update_completed_sessions(
            args.dataset_dir,
            args.snapshot,
            end_exclusive=args.end_exclusive,
            batch_size=args.batch_size,
        )
    elif args.command == "reconcile":
        result = reconcile_dataset_storage(args.dataset_dir)
    elif args.command == "recover":
        result = recover_quarantine(args.dataset_dir)
    elif args.command == "derive":
        result = derive_dataset_for_snapshot(
            args.parent_dataset_dir, args.snapshot, args.output_dir
        )
    else:
        result = validate_dataset(
            args.dataset_dir,
            start=args.start,
            end=args.end,
            current_snapshot_path=args.current_snapshot,
            events_path=args.events,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
