"""Create a deterministic, synthetic dataset for the offline local sandbox.

The generated files are deliberately written under a Docker volume or ignored
``runtime/`` directory. They contain no provider data, credentials, or claim of
point-in-time certification, so strict backtests remain disabled.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import tempfile
from pathlib import Path

import pandas as pd

from price_data_pipeline import _atomic_price_frame, price_file_path, sha256_file
from universe_snapshot import build_legacy_snapshot, save_snapshot


DEMO_TICKERS = ("ALPHA", "BETA", "GAMMA")
DATASET_NAME = "local-demo"


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _price_frame(ticker_index: int) -> pd.DataFrame:
    dates = pd.bdate_range("2026-01-02", periods=260)
    values = []
    base = 55.0 + ticker_index * 35.0
    for offset, _date in enumerate(dates):
        trend = offset * (0.05 + ticker_index * 0.01)
        wave = math.sin(offset / (9.0 + ticker_index)) * (1.8 + ticker_index * 0.3)
        close = base + trend + wave
        opening = close - math.sin(offset / 5.0) * 0.45
        values.append(
            {
                "Open": opening,
                "High": max(opening, close) + 0.8,
                "Low": min(opening, close) - 0.8,
                "Close": close,
                "Volume": 1_000_000 + ticker_index * 150_000 + (offset % 17) * 10_000,
            }
        )
    return pd.DataFrame(values, index=dates)


def create_local_demo(output_root: Path) -> Path:
    """Create the demo once and return its dataset directory without overwriting it."""

    root = output_root.expanduser().resolve()
    dataset = root / "backtest_datasets" / DATASET_NAME
    manifest_path = dataset / "manifest.json"
    if manifest_path.exists():
        return dataset

    prices = dataset / "prices"
    price_metadata = {}
    for ticker_index, ticker in enumerate(DEMO_TICKERS):
        path = price_file_path(prices, ticker)
        frame = _price_frame(ticker_index)
        _atomic_price_frame(frame, path)
        price_metadata[ticker] = {
            "rows": len(frame),
            "first_date": frame.index.min().date().isoformat(),
            "last_date": frame.index.max().date().isoformat(),
            "sha256": sha256_file(path),
        }

    snapshot = build_legacy_snapshot(
        {ticker: "NASDAQ" for ticker in DEMO_TICKERS},
        effective_date="2026-01-02",
        captured_at=dt.datetime(2026, 1, 2, tzinfo=dt.timezone.utc),
    )
    snapshot["snapshot_type"] = "local_demo_synthetic"
    snapshot["provenance"] = "deterministic synthetic data for the offline local sandbox"
    snapshot["notes"] = "Not market data. Never use for investment decisions or performance claims."
    save_snapshot(snapshot, root / "universe_snapshots")

    _atomic_json(
        dataset / "validation_report.json",
        {
            "dataset_kind": "local_demo_synthetic",
            "forward_strategy_data_gate_ready": False,
            "current_snapshot_membership_sha256": snapshot["membership_sha256"],
            "window": {"start": "2026-01-02", "end": "2026-12-31"},
            "strategy_candidate_data_blockers": [
                "Synthetic local demo data is not eligible for strict PIT backtests."
            ],
        },
    )
    _atomic_json(
        manifest_path,
        {
            "schema_version": 2,
            "price_format": "csv-gzip-v1",
            "dataset_kind": "local_demo_synthetic",
            "prices": price_metadata,
        },
    )
    return dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Milkyway's offline synthetic local demo data")
    parser.add_argument("--output-root", type=Path, default=Path("runtime/local-demo"))
    args = parser.parse_args()
    dataset = create_local_demo(args.output_root)
    print("Local synthetic demo dataset ready: {}".format(dataset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
