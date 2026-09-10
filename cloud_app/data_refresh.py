"""One decision-grade daily refresh: snapshot, diff, prices, validation."""

from __future__ import annotations

import datetime as dt
import glob
import json
import logging
from pathlib import Path

from price_data_pipeline import update_completed_sessions, validate_dataset
from terminal_events import append_snapshot_diff
from universe_snapshot import (
    DEFAULT_EXCHANGES,
    SnapshotAggregateBudgetExceeded,
    build_snapshot,
    fetch_official_sources,
    load_snapshot_with_size,
    save_snapshot,
)

from .config import get_settings
from .bounded_io import FileReadBudget, bounded_paths


logger = logging.getLogger("cloud_app.data_refresh")
MAX_PRIOR_SNAPSHOT_BYTES = 64 * 1024 * 1024


def _new_york_today() -> dt.date:
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from pytz import timezone as ZoneInfo
    return dt.datetime.now(ZoneInfo("America/New_York")).date()


def run_daily_refresh() -> dict:
    settings = get_settings()
    sources = fetch_official_sources()
    snapshot = build_snapshot(
        sources["nasdaqlisted.txt"],
        sources["otherlisted.txt"],
        allowed_exchanges=DEFAULT_EXCHANGES,
    )
    snapshot_dir = Path(settings.snapshots_glob).parent
    before_paths = sorted(
        bounded_paths(
            (Path(item) for item in glob.iglob(settings.snapshots_glob)),
            maximum_count=1000,
        )
    )
    prior_snapshots = []
    byte_budget = FileReadBudget(MAX_PRIOR_SNAPSHOT_BYTES)
    for path in before_paths:
        try:
            prior_snapshot, _file_size = load_snapshot_with_size(
                path, byte_budget=byte_budget,
            )
            prior_snapshots.append(prior_snapshot)
        except SnapshotAggregateBudgetExceeded:
            raise
        except (OSError, ValueError, json.JSONDecodeError):
            logger.warning("ignoring invalid prior snapshot: %s", path)
    previous = (
        max(prior_snapshots, key=lambda item: str(item.get("captured_at_utc", "")))
        if prior_snapshots
        else None
    )
    snapshot_path = save_snapshot(snapshot, snapshot_dir, raw_sources=sources)
    diff_count = 0
    if previous and previous["membership_sha256"] != snapshot["membership_sha256"]:
        events = append_snapshot_diff(previous, snapshot, settings.terminal_events_path)
        diff_count = len(events)

    end_exclusive = (_new_york_today() + dt.timedelta(days=1)).isoformat()
    update = update_completed_sessions(
        settings.dataset_dir,
        [snapshot_path],
        end_exclusive=end_exclusive,
    )
    validation = validate_dataset(
        settings.dataset_dir,
        start=max("2026-01-01", snapshot["effective_date"]),
        end=_new_york_today().isoformat(),
        current_snapshot_path=snapshot_path,
        events_path=settings.terminal_events_path,
    )
    result = {
        "snapshot": str(snapshot_path),
        "membership_sha256": snapshot["membership_sha256"],
        "exchange_exit_alerts": diff_count,
        "price_update": update,
        "validation": {
            "forward_strategy_data_gate_ready": validation["forward_strategy_data_gate_ready"],
            "strategy_candidate_data_blockers": validation["strategy_candidate_data_blockers"],
            "unresolved_terminal_event_count": validation["unresolved_terminal_event_count"],
        },
    }
    logger.info("daily refresh validation: %s", json.dumps(result, ensure_ascii=False, default=str))
    if not validation["forward_strategy_data_gate_ready"]:
        blockers = validation["strategy_candidate_data_blockers"]
        raise RuntimeError(
            "daily data gate failed for {} strategy candidates: {}".format(
                len(blockers), ",".join(blockers[:20])
            )
        )
    logger.info("daily refresh quality gate passed")
    return result


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    result = run_daily_refresh()
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
