"""Independently validate and publish one immutable market-data generation.

The scheduled downloader can write only the staging tree. This command is run
manually by an operator identity that can read staging and write the separate
published root; the scheduler container never receives that write capability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from price_data_pipeline import (
    MAX_DATASET_COMPRESSED_BYTES,
    MAX_PRICE_FILE_BYTES,
    load_manifest_snapshot,
    price_file_path,
    read_price_frame,
)
from terminal_events import effective_verified_events, load_events
from universe_snapshot import load_snapshot

from .bounded_io import bounded_paths, read_bounded_file, read_bounded_json


MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024
MAX_SNAPSHOTS = 1000
MAX_SNAPSHOT_TOTAL_BYTES = 64 * 1024 * 1024
MAX_VALIDATION_BYTES = 4 * 1024 * 1024
MAX_AUXILIARY_BYTES = 8 * 1024 * 1024
DATASET_RELATIVE_PATH = Path(
    "backtest_datasets/2026_equities_pit_20260824"
)


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _copy_optional(source: Path, destination: Path, maximum_bytes: int) -> None:
    try:
        payload = read_bounded_file(source, maximum_bytes=maximum_bytes)
    except FileNotFoundError:
        return
    _write_new(destination, payload)


def _copy_and_validate_generation(
    staging_root: Path,
    temporary_root: Path,
    approved_event_ids: set[str],
) -> tuple[str, dict]:
    staged_dataset = staging_root / DATASET_RELATIVE_PATH
    manifest, manifest_bytes, manifest_sha256 = load_manifest_snapshot(
        staged_dataset / "manifest.json"
    )
    target_dataset = temporary_root / DATASET_RELATIVE_PATH
    _write_new(target_dataset / "manifest.json", manifest_bytes)

    compressed_bytes = 0
    for ticker, metadata in sorted(manifest["prices"].items()):
        source = price_file_path(staged_dataset / "prices", ticker)
        payload = read_bounded_file(source, maximum_bytes=MAX_PRICE_FILE_BYTES)
        compressed_bytes += len(payload)
        if compressed_bytes > MAX_DATASET_COMPRESSED_BYTES:
            raise ValueError("staged dataset exceeds the aggregate byte budget")
        expected = str(metadata.get("sha256", ""))
        if len(expected) != 64 or hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError("staged price hash does not match the manifest")
        destination = price_file_path(target_dataset / "prices", ticker)
        _write_new(destination, payload)
        frame = read_price_frame(
            destination, require_valid=True, expected_sha256=expected
        )
        if (
            len(frame) != int(metadata.get("rows", -1))
            or frame.index.min().date().isoformat() != str(metadata.get("first_date", ""))
            or frame.index.max().date().isoformat() != str(metadata.get("last_date", ""))
        ):
            raise ValueError("staged price metadata does not match the copied bytes")

    snapshot_sources = tuple(
        sorted(
            bounded_paths(
                (staging_root / "universe_snapshots").glob("*.json"),
                maximum_count=MAX_SNAPSHOTS,
            )
        )
    )
    if not snapshot_sources:
        raise ValueError("no staged universe snapshots were found")
    snapshots = []
    snapshot_bytes = 0
    for source in snapshot_sources:
        if source.name in {".", ".."} or source.name != Path(source.name).name:
            raise ValueError("staged snapshot name is invalid")
        destination = temporary_root / "universe_snapshots" / source.name
        payload = read_bounded_file(source, maximum_bytes=MAX_SNAPSHOT_BYTES)
        snapshot_bytes += len(payload)
        if snapshot_bytes > MAX_SNAPSHOT_TOTAL_BYTES:
            raise ValueError("staged snapshots exceed the aggregate byte budget")
        _write_new(destination, payload)
        snapshots.append(load_snapshot(destination))
    snapshots.sort(key=lambda item: str(item["effective_date"]))

    validation_source = staged_dataset / "validation_report.json"
    validation = read_bounded_json(
        validation_source, maximum_bytes=MAX_VALIDATION_BYTES
    )
    if not isinstance(validation, dict):
        raise ValueError("staged validation report must be an object")
    latest_snapshot_hash = snapshots[-1]["membership_sha256"]
    last_price_date = max(
        str(metadata["last_date"]) for metadata in manifest["prices"].values()
    )
    if (
        not validation.get("forward_strategy_data_gate_ready")
        or validation.get("current_snapshot_membership_sha256")
        != latest_snapshot_hash
        or str(validation.get("window", {}).get("end", "")) < last_price_date
    ):
        raise ValueError("staged validation report does not approve this generation")
    validation["approved_manifest_sha256"] = manifest_sha256
    validation_bytes = json.dumps(
        validation, ensure_ascii=False, sort_keys=True, indent=2
    ).encode("utf-8")
    if len(validation_bytes) > MAX_VALIDATION_BYTES:
        raise ValueError("approved validation report exceeds its byte budget")
    _write_new(target_dataset / "validation_report.json", validation_bytes)

    event_source = staging_root / "universe_events" / "events.jsonl"
    try:
        event_payload = read_bounded_file(
            event_source, maximum_bytes=4 * 1024 * 1024, allow_empty=True
        )
    except FileNotFoundError:
        event_payload = b""
    if event_payload:
        event_destination = temporary_root / "universe_events" / "events.jsonl"
        _write_new(event_destination, event_payload)
        verified = effective_verified_events(load_events(event_destination))
        semantic_keys: set[tuple[str, str, str]] = set()
        for event in verified:
            if event["event_id"] not in approved_event_ids:
                raise ValueError(
                    "verified terminal event requires explicit operator approval: "
                    + event["event_id"]
                )
            semantic_key = (
                event["ticker"],
                event["effective_date"],
                event["event_type"],
            )
            if semantic_key in semantic_keys:
                raise ValueError("duplicate verified terminal-event transition")
            semantic_keys.add(semantic_key)

    for relative in (Path("_sector_map.json"), Path("news/news_feed.json")):
        _copy_optional(
            staging_root / relative,
            temporary_root / relative,
            MAX_AUXILIARY_BYTES,
        )

    promotion = {
        "schema_version": 1,
        "manifest_sha256": manifest_sha256,
        "latest_snapshot_membership_sha256": latest_snapshot_hash,
        "approved_verified_event_ids": sorted(approved_event_ids),
    }
    _write_new(
        temporary_root / "promotion.json",
        json.dumps(promotion, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    )
    return manifest_sha256, promotion


def promote(
    staging_root: Path,
    published_root: Path,
    *,
    confirm: str,
    approved_event_ids: set[str],
) -> Path:
    if confirm != "REVIEWED_SOURCE_PROVENANCE":
        raise ValueError("independent source-provenance review was not confirmed")
    staging_root = staging_root.resolve(strict=True)
    published_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    published_root = published_root.resolve(strict=True)
    if (
        staging_root == published_root
        or staging_root in published_root.parents
        or published_root in staging_root.parents
    ):
        raise ValueError("staging and published roots must be separate")
    temporary = Path(tempfile.mkdtemp(prefix=".promotion-", dir=published_root))
    try:
        manifest_sha256, _promotion = _copy_and_validate_generation(
            staging_root, temporary, approved_event_ids
        )
        destination = published_root / ("generation-" + manifest_sha256)
        if destination.exists():
            raise FileExistsError("this immutable generation is already published")
        os.rename(temporary, destination)
        descriptor = os.open(published_root, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return destination
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging-root", type=Path, default=Path("/staging"))
    parser.add_argument("--published-root", type=Path, default=Path("/published"))
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--approve-event", action="append", default=[])
    args = parser.parse_args()
    destination = promote(
        args.staging_root,
        args.published_root,
        confirm=args.confirm,
        approved_event_ids=set(args.approve_event),
    )
    print("Published immutable data generation:", destination.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
