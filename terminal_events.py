"""Append-only corporate-action and exchange-exit event store.

An exchange-listing disappearance is an alert, not a terminal return.  A cash
merger, bankruptcy recovery, symbol change, or an actual liquidation price
must be resolved from evidence before the backtest can settle a held position.
Unresolved events are intentionally ignored by the accounting engine, which
will then fail closed if a held security has no price.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Mapping, Optional

from universe_snapshot import listed_symbols, load_snapshot


EVENT_TYPES = {
    "exchange_exit",
    "cash_merger",
    "stock_merger",
    "mixed_merger",
    "bankruptcy_recovery",
    "liquidation",
    "symbol_change",
}
EVENT_STATUSES = {"unresolved", "verified", "rejected"}


def _canonical_event(event: Mapping) -> dict:
    result = {
        "schema_version": int(event.get("schema_version", 1)),
        "ticker": str(event["ticker"]).upper().strip(),
        "effective_date": str(event["effective_date"]),
        "event_type": str(event["event_type"]),
        "status": str(event.get("status", "unresolved")),
        "cash_per_share": event.get("cash_per_share"),
        "successor_symbol": event.get("successor_symbol"),
        "share_ratio": event.get("share_ratio"),
        "source": event.get("source"),
        "notes": event.get("notes"),
        "observed_in_snapshot": event.get("observed_in_snapshot"),
        "previous_snapshot": event.get("previous_snapshot"),
    }
    if result["cash_per_share"] is not None:
        result["cash_per_share"] = float(result["cash_per_share"])
    if result["successor_symbol"] is not None:
        result["successor_symbol"] = str(result["successor_symbol"]).upper().strip()
    if result["share_ratio"] is not None:
        result["share_ratio"] = float(result["share_ratio"])
    return result


def validate_event(event: Mapping) -> dict:
    result = _canonical_event(event)
    if not result["ticker"]:
        raise ValueError("ticker is required")
    try:
        dt.date.fromisoformat(result["effective_date"])
    except ValueError as exc:
        raise ValueError("effective_date must be YYYY-MM-DD") from exc
    if result["event_type"] not in EVENT_TYPES:
        raise ValueError("Unsupported event_type: {}".format(result["event_type"]))
    if result["status"] not in EVENT_STATUSES:
        raise ValueError("Unsupported status: {}".format(result["status"]))
    cash = result["cash_per_share"]
    ratio = result["share_ratio"]
    successor = result["successor_symbol"]
    if cash is not None and cash < 0:
        raise ValueError("cash_per_share must be non-negative")
    if ratio is not None and ratio <= 0:
        raise ValueError("share_ratio must be positive")
    if bool(successor) != bool(ratio is not None):
        raise ValueError("successor_symbol and share_ratio must be supplied together")
    if result["status"] == "verified":
        if cash is None and successor is None:
            raise ValueError("A verified event needs cash_per_share and/or successor shares")
        if not result["source"]:
            raise ValueError("A verified event needs an evidence source")
    identity = dict(result)
    encoded = json.dumps(
        identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    result["event_id"] = hashlib.sha256(encoded).hexdigest()
    return result


def load_events(path: Path | str) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    events = []
    seen = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                event = validate_event(raw)
            except Exception as exc:
                raise ValueError("Invalid event at {}:{}: {}".format(path, line_number, exc)) from exc
            if event["event_id"] in seen:
                continue
            seen.add(event["event_id"])
            events.append(event)
    return events


def append_event(path: Path | str, event: Mapping) -> tuple[dict, bool]:
    """Append one validated event under an advisory lock; duplicates are idempotent."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    validated = validate_event(event)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        existing_ids = set()
        for line in handle:
            if line.strip():
                existing_ids.add(validate_event(json.loads(line))["event_id"])
        if validated["event_id"] in existing_ids:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return validated, False
        stored = dict(validated)
        stored["recorded_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(stored, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return validated, True


def append_snapshot_diff(
    previous_snapshot: Mapping,
    current_snapshot: Mapping,
    path: Path | str,
) -> list[dict]:
    """Record exchange departures as unresolved; never invent terminal proceeds."""
    # A security that remains listed but becomes ineligible (for example an
    # ETF or preferred that the legacy cache could not classify) is not a
    # terminal event.  Compare exchange presence, not strategy eligibility.
    before = listed_symbols(previous_snapshot)
    after = listed_symbols(current_snapshot)
    removed = sorted(before - after)
    added = []
    for ticker in removed:
        event, was_added = append_event(
            path,
            {
                "ticker": ticker,
                "effective_date": current_snapshot["effective_date"],
                "event_type": "exchange_exit",
                "status": "unresolved",
                "cash_per_share": None,
                "successor_symbol": None,
                "share_ratio": None,
                "source": None,
                "notes": "Absent from the later allowed-exchange snapshot; resolve merger, rename, OTC move, or liquidation before certification.",
                "observed_in_snapshot": current_snapshot["membership_sha256"],
                "previous_snapshot": previous_snapshot["membership_sha256"],
            },
        )
        if was_added:
            added.append(event)
    return added


def effective_verified_events(
    events: Iterable[Mapping], *, through: Optional[str] = None
) -> list[dict]:
    result = []
    for event in events:
        validated = validate_event(event)
        if validated["status"] != "verified":
            continue
        if through is not None and validated["effective_date"] > str(through):
            continue
        result.append(validated)
    return sorted(result, key=lambda item: (item["effective_date"], item["ticker"]))


def unresolved_events(events: Iterable[Mapping], *, through: Optional[str] = None) -> list[dict]:
    # The store is append-only.  A later verified/rejected record for the same
    # ticker resolves an earlier exchange-exit alert without deleting history.
    active = {}
    for event in events:
        validated = validate_event(event)
        if through is not None and validated["effective_date"] > str(through):
            continue
        ticker = validated["ticker"]
        if validated["status"] == "unresolved":
            active[ticker] = validated
        else:
            active.pop(ticker, None)
    return sorted(active.values(), key=lambda item: (item["effective_date"], item["ticker"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage terminal/corporate-action events")
    parser.add_argument(
        "--store", type=Path, default=Path("data_cache/universe_events/events.jsonl")
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser("diff", help="append unresolved snapshot exits")
    diff_parser.add_argument("previous", type=Path)
    diff_parser.add_argument("current", type=Path)

    add_parser = subparsers.add_parser("add", help="append a manually verified event")
    add_parser.add_argument("--ticker", required=True)
    add_parser.add_argument("--effective-date", required=True)
    add_parser.add_argument("--event-type", required=True, choices=sorted(EVENT_TYPES))
    add_parser.add_argument("--status", choices=sorted(EVENT_STATUSES), default="verified")
    add_parser.add_argument("--cash-per-share", type=float)
    add_parser.add_argument("--successor-symbol")
    add_parser.add_argument("--share-ratio", type=float)
    add_parser.add_argument("--source")
    add_parser.add_argument("--notes")

    subparsers.add_parser("list-unresolved")
    args = parser.parse_args()

    if args.command == "diff":
        previous = load_snapshot(args.previous)
        current = load_snapshot(args.current)
        added = append_snapshot_diff(previous, current, args.store)
        print("appended_unresolved={}".format(len(added)))
    elif args.command == "add":
        _, added = append_event(
            args.store,
            {
                "ticker": args.ticker,
                "effective_date": args.effective_date,
                "event_type": args.event_type,
                "status": args.status,
                "cash_per_share": args.cash_per_share,
                "successor_symbol": args.successor_symbol,
                "share_ratio": args.share_ratio,
                "source": args.source,
                "notes": args.notes,
            },
        )
        print("appended={}".format(added))
    else:
        events = unresolved_events(load_events(args.store))
        for event in events:
            print(
                "{effective_date} {ticker} {event_type} {notes}".format(**event)
            )
        print("unresolved={}".format(len(events)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
