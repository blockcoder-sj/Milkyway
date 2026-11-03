"""Append-only 09:35 ET execution-price observations.

Daily Open is a documented proxy.  Exact forward parity requires recording a
broker quote or licensed 5-minute bar at the strategy's execution timestamp.
This store turns those observations into the sparse date-by-symbol panel
accepted by ``backtest_core.run_backtest(execution_timing='next_0935')``.
"""

from __future__ import annotations

import argparse
import datetime as dt
from cloud_app import native_platform as fcntl
import hashlib
import json
import os
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.8 broker environments
    from pytz import timezone as ZoneInfo

import pandas as pd


NEW_YORK = ZoneInfo("America/New_York")


def validate_observation(value: dict) -> dict:
    ticker = str(value["ticker"]).upper().strip()
    price = float(value["price"])
    observed_at = dt.datetime.fromisoformat(str(value["observed_at_utc"]).replace("Z", "+00:00"))
    if observed_at.tzinfo is None:
        raise ValueError("observed_at_utc must be timezone-aware")
    observed_at = observed_at.astimezone(dt.timezone.utc)
    trading_date = str(value.get("trading_date") or observed_at.astimezone(NEW_YORK).date())
    dt.date.fromisoformat(trading_date)
    if not ticker or price <= 0:
        raise ValueError("ticker and a positive price are required")
    source = str(value.get("source") or "").strip()
    if not source:
        raise ValueError("source is required")
    result = {
        "schema_version": 1,
        "ticker": ticker,
        "trading_date": trading_date,
        "observed_at_utc": observed_at.isoformat(),
        "price": price,
        "source": source,
        "kind": str(value.get("kind", "quote")),
    }
    identity = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result["observation_id"] = hashlib.sha256(identity).hexdigest()
    return result


def append_observation(path: Path | str, value: dict) -> tuple[dict, bool]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    observation = validate_observation(value)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        ids = {
            validate_observation(json.loads(line))["observation_id"]
            for line in handle
            if line.strip()
        }
        if observation["observation_id"] in ids:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return observation, False
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(observation, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return observation, True


def load_observations(path: Path | str) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    observations = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                observations.append(validate_observation(json.loads(line)))
            except Exception as exc:
                raise ValueError("Invalid execution observation {}:{}".format(path, line_number)) from exc
    return observations


def build_0935_panel(
    observations: list[dict], *, tolerance_minutes: int = 3
) -> pd.DataFrame:
    """Choose the observation closest to 09:35 ET within the tolerance."""
    chosen = {}
    for raw in observations:
        observation = validate_observation(raw)
        observed = dt.datetime.fromisoformat(observation["observed_at_utc"]).astimezone(NEW_YORK)
        target = observed.replace(hour=9, minute=35, second=0, microsecond=0)
        distance = abs((observed - target).total_seconds())
        if observed.date().isoformat() != observation["trading_date"]:
            continue
        if distance > tolerance_minutes * 60:
            continue
        key = (observation["trading_date"], observation["ticker"])
        existing = chosen.get(key)
        if existing is None or distance < existing[0]:
            chosen[key] = (distance, observation)
    if not chosen:
        return pd.DataFrame(dtype=float)
    rows = [
        {
            "date": pd.Timestamp(date),
            "ticker": ticker,
            "price": observation["price"],
        }
        for (date, ticker), (_, observation) in chosen.items()
    ]
    frame = pd.DataFrame(rows)
    return frame.pivot(index="date", columns="ticker", values="price").sort_index()


def main() -> int:
    parser = argparse.ArgumentParser(description="Record or export 09:35 ET prices")
    parser.add_argument(
        "--store", type=Path, default=Path("data_cache/execution_prices/0935.jsonl")
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--ticker", required=True)
    add_parser.add_argument("--price", type=float, required=True)
    add_parser.add_argument("--observed-at-utc", required=True)
    add_parser.add_argument("--trading-date")
    add_parser.add_argument("--source", required=True)
    add_parser.add_argument("--kind", default="quote")
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--output", type=Path, required=True)
    export_parser.add_argument("--tolerance-minutes", type=int, default=3)
    args = parser.parse_args()

    if args.command == "add":
        observation, added = append_observation(
            args.store,
            {
                "ticker": args.ticker,
                "price": args.price,
                "observed_at_utc": args.observed_at_utc,
                "trading_date": args.trading_date,
                "source": args.source,
                "kind": args.kind,
            },
        )
        print(json.dumps({"added": added, **observation}, sort_keys=True))
    else:
        panel = build_0935_panel(
            load_observations(args.store), tolerance_minutes=args.tolerance_minutes
        )
        if not args.output.name.endswith(".csv.gz"):
            raise SystemExit("execution price exports must use a .csv.gz output path")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        panel.to_csv(args.output, compression={"method": "gzip", "mtime": 0})
        print("{} rows={} columns={}".format(args.output, *panel.shape))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
