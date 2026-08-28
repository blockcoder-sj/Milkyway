"""Immutable exchange-listed universe snapshots for forward backtests.

The project previously called a union of the current SEC ticker file, a
current Nasdaq screener response, and whatever happened to exist in
``data_cache`` a "bias-free" universe.  That union is useful for discovery,
but it is not point-in-time membership data.  This module instead captures
the official Nasdaq Trader symbol directory and writes a content-addressed,
append-only snapshot.

By default all national exchanges present in the Nasdaq Trader directory are
allowed: Nasdaq, NYSE, NYSE American, NYSE Arca, Cboe BZX, and IEX.  OTC
securities, ETFs, test issues, preferreds, warrants, rights, units, notes, and
funds remain in the raw source files but are excluded from the strategy
membership list.  Financial-status flags are deliberately *not* exclusions:
dropping a deficient or bankrupt issuer would reintroduce survivorship bias.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable, Mapping, Optional


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

DEFAULT_EXCHANGES = frozenset(
    {"NASDAQ", "NYSE", "NYSE_AMERICAN", "NYSE_ARCA", "CBOE_BZX", "IEX"}
)
OTHER_EXCHANGE_NAMES = {
    "A": "NYSE_AMERICAN",
    "N": "NYSE",
    "P": "NYSE_ARCA",
    "Z": "CBOE_BZX",
    "V": "IEX",
}
LEGACY_EXCHANGE_NAMES = {
    "NASD": "NASDAQ",
    "NASDAQ": "NASDAQ",
    "NYSE": "NYSE",
    "AMEX": "NYSE_AMERICAN",
    "NYSE_AMERICAN": "NYSE_AMERICAN",
}

_CACHE_SYMBOL = re.compile(r"^[A-Z]{1,5}$")
_EXCLUDED_SECURITY_TERMS = (
    " warrant",
    " warrants",
    " right",
    " rights",
    " unit",
    " units",
    " preferred",
    " preference",
    " depositary shares",
    " debt securities",
    " debenture",
    " bond",
    " notes due",
    " note due",
    " exchange traded fund",
    " exchange traded note",
    " exchange-traded note",
    " etn ",
    " etns ",
    " fund ",
    " fund,",
    " note ",
    " notes ",
    " gold trust",
    " silver trust",
    " bitcoin trust",
    " ethereum trust",
    " closed end fund",
    " closed-end fund",
    " income fund",
    " municipal fund",
    " index fund",
)


def _canonical_json(value) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_creation_time(text: str) -> Optional[str]:
    for line in reversed(text.splitlines()):
        if not line.startswith("File Creation Time:"):
            continue
        raw = line.split("|", 1)[0].replace("File Creation Time:", "").strip()
        try:
            parsed = dt.datetime.strptime(raw, "%m%d%Y%H:%M")
            return parsed.isoformat(timespec="minutes")
        except ValueError:
            return raw or None
    return None


def _normalized_name(name: str) -> str:
    return " " + re.sub(r"\s+", " ", str(name).strip().lower()) + " "


def _equity_like(name: str, *, etf: str, test_issue: str, next_shares: str = "N") -> bool:
    if str(etf).upper() == "Y" or str(test_issue).upper() == "Y":
        return False
    if str(next_shares).upper() == "Y":
        return False
    normalized = _normalized_name(name)
    return not any(term in normalized for term in _EXCLUDED_SECURITY_TERMS)


def _record(
    *,
    symbol: str,
    name: str,
    exchange: str,
    source_file: str,
    etf: str = "N",
    test_issue: str = "N",
    financial_status: Optional[str] = None,
    market_category: Optional[str] = None,
    next_shares: str = "N",
    allowed_exchanges: Iterable[str] = DEFAULT_EXCHANGES,
) -> dict:
    symbol = str(symbol).upper().strip()
    allowed = set(allowed_exchanges)
    equity_like = _equity_like(
        name, etf=etf, test_issue=test_issue, next_shares=next_shares
    )
    cache_compatible = bool(_CACHE_SYMBOL.fullmatch(symbol))
    eligible = exchange in allowed and equity_like and cache_compatible
    reasons = []
    if exchange not in allowed:
        reasons.append("exchange_not_allowed")
    if not equity_like:
        reasons.append("non_common_equity_or_test_issue")
    if not cache_compatible:
        reasons.append("symbol_not_cache_compatible")
    return {
        "symbol": symbol,
        "name": str(name).strip(),
        "exchange": exchange,
        "source_file": source_file,
        "etf": str(etf).upper() == "Y",
        "test_issue": str(test_issue).upper() == "Y",
        "financial_status": financial_status or None,
        "market_category": market_category or None,
        "eligible": eligible,
        "exclusion_reasons": reasons,
    }


def parse_symbol_directory(
    nasdaq_text: str,
    other_text: str,
    *,
    allowed_exchanges: Iterable[str] = DEFAULT_EXCHANGES,
) -> list[dict]:
    """Parse Nasdaq Trader's two pipe-delimited symbol-directory files."""
    records = []
    reader = csv.DictReader(io.StringIO(nasdaq_text), delimiter="|")
    for row in reader:
        symbol = (row.get("Symbol") or "").strip()
        if not symbol or symbol.startswith("File Creation Time:"):
            continue
        records.append(
            _record(
                symbol=symbol,
                name=row.get("Security Name") or "",
                exchange="NASDAQ",
                source_file="nasdaqlisted.txt",
                etf=row.get("ETF") or "N",
                test_issue=row.get("Test Issue") or "N",
                financial_status=row.get("Financial Status") or None,
                market_category=row.get("Market Category") or None,
                next_shares=row.get("NextShares") or "N",
                allowed_exchanges=allowed_exchanges,
            )
        )

    reader = csv.DictReader(io.StringIO(other_text), delimiter="|")
    for row in reader:
        symbol = (row.get("ACT Symbol") or "").strip()
        if not symbol or symbol.startswith("File Creation Time:"):
            continue
        exchange_code = (row.get("Exchange") or "").strip().upper()
        records.append(
            _record(
                symbol=symbol,
                name=row.get("Security Name") or "",
                exchange=OTHER_EXCHANGE_NAMES.get(
                    exchange_code, "UNKNOWN_{}".format(exchange_code or "BLANK")
                ),
                source_file="otherlisted.txt",
                etf=row.get("ETF") or "N",
                test_issue=row.get("Test Issue") or "N",
                allowed_exchanges=allowed_exchanges,
            )
        )

    # A symbol should have one primary listing.  Fail instead of silently
    # choosing one if the upstream files ever violate that contract.
    records.sort(key=lambda item: (item["symbol"], item["exchange"]))
    duplicates = []
    for previous, current in zip(records, records[1:]):
        if previous["symbol"] == current["symbol"]:
            duplicates.append(current["symbol"])
    if duplicates:
        raise ValueError("Duplicate primary symbols in directory: {}".format(duplicates[:10]))
    return records


def build_snapshot(
    nasdaq_text: str,
    other_text: str,
    *,
    captured_at: Optional[dt.datetime] = None,
    allowed_exchanges: Iterable[str] = DEFAULT_EXCHANGES,
) -> dict:
    captured_at = captured_at or dt.datetime.now(dt.timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=dt.timezone.utc)
    allowed = sorted(set(allowed_exchanges))
    records = parse_symbol_directory(
        nasdaq_text, other_text, allowed_exchanges=allowed
    )
    membership_sha = sha256_bytes(_canonical_json(records))
    creation_values = [
        value
        for value in (
            _source_creation_time(nasdaq_text),
            _source_creation_time(other_text),
        )
        if value
    ]
    effective_date = (
        max(creation_values)[:10]
        if creation_values and re.match(r"^\d{4}-\d{2}-\d{2}", max(creation_values))
        else captured_at.date().isoformat()
    )
    eligible_count = sum(bool(row["eligible"]) for row in records)
    return {
        "schema_version": 2,
        "snapshot_type": "official_exchange_directory",
        "certification_eligible": True,
        "captured_at_utc": captured_at.astimezone(dt.timezone.utc).isoformat(),
        "effective_date": effective_date,
        "allowed_exchanges": allowed,
        "filters": {
            "otc_excluded": True,
            "etf_excluded": True,
            "test_issues_excluded": True,
            "non_common_security_name_filter": True,
            "cache_symbol_regex": _CACHE_SYMBOL.pattern,
            "financial_status_excluded": False,
        },
        "sources": [
            {
                "name": "nasdaqlisted.txt",
                "url": NASDAQ_LISTED_URL,
                "sha256": sha256_bytes(nasdaq_text.encode("utf-8")),
                "file_creation_time": _source_creation_time(nasdaq_text),
            },
            {
                "name": "otherlisted.txt",
                "url": OTHER_LISTED_URL,
                "sha256": sha256_bytes(other_text.encode("utf-8")),
                "file_creation_time": _source_creation_time(other_text),
            },
        ],
        "record_count": len(records),
        "eligible_count": eligible_count,
        "membership_sha256": membership_sha,
        "records": records,
    }


def build_legacy_snapshot(
    exchange_map: Mapping[str, str],
    *,
    effective_date: str,
    captured_at: Optional[dt.datetime] = None,
) -> dict:
    """Freeze an existing KIS exchange cache without claiming official PIT proof."""
    captured_at = captured_at or dt.datetime.now(dt.timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=dt.timezone.utc)
    records = []
    for symbol, raw_exchange in sorted(exchange_map.items()):
        exchange = LEGACY_EXCHANGE_NAMES.get(str(raw_exchange).upper(), "UNKNOWN")
        records.append(
            _record(
                symbol=symbol,
                name="",
                exchange=exchange,
                source_file="exchange_cache.json",
                allowed_exchanges=DEFAULT_EXCHANGES,
            )
        )
    membership_sha = sha256_bytes(_canonical_json(records))
    raw_sha = sha256_bytes(_canonical_json(dict(sorted(exchange_map.items()))))
    return {
        "schema_version": 2,
        "snapshot_type": "legacy_exchange_lookup_cache",
        "certification_eligible": False,
        "provenance": "retroactively_frozen_partial_lookup_cache_not_a_universe",
        "notes": "This file accumulated broker exchange lookups and is not a complete historical listing snapshot.",
        "captured_at_utc": captured_at.astimezone(dt.timezone.utc).isoformat(),
        "effective_date": str(effective_date),
        "allowed_exchanges": sorted(DEFAULT_EXCHANGES),
        "filters": {
            "otc_excluded": True,
            "security_type_available": False,
            "cache_symbol_regex": _CACHE_SYMBOL.pattern,
        },
        "sources": [
            {
                "name": "exchange_cache.json",
                "url": None,
                "sha256": raw_sha,
                "file_creation_time": None,
            }
        ],
        "record_count": len(records),
        "eligible_count": sum(bool(row["eligible"]) for row in records),
        "membership_sha256": membership_sha,
        "records": records,
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_snapshot(
    snapshot: Mapping,
    output_dir: Path | str,
    *,
    raw_sources: Optional[Mapping[str, str]] = None,
) -> Path:
    """Save a content-addressed snapshot; existing content is never overwritten."""
    output_dir = Path(output_dir)
    membership_sha = str(snapshot["membership_sha256"])
    effective_date = str(snapshot["effective_date"])
    snapshot_type = str(snapshot.get("snapshot_type", "snapshot"))
    filename = "{}_v{}_{}_{}.json".format(
        effective_date, snapshot.get("schema_version", 1), snapshot_type, membership_sha[:16]
    )
    path = output_dir / filename
    payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("membership_sha256") != membership_sha:
            raise FileExistsError("Snapshot path collision: {}".format(path))
        return path
    _atomic_write(path, payload)

    if raw_sources:
        raw_dir = output_dir / "raw"
        for source_name, text in raw_sources.items():
            source_sha = sha256_bytes(text.encode("utf-8"))
            raw_path = raw_dir / "{}_{}_{}".format(
                effective_date, source_sha[:16], Path(source_name).name
            )
            if not raw_path.exists():
                _atomic_write(raw_path, text.encode("utf-8"))
    return path


def load_snapshot(path: Path | str, *, verify: bool = True) -> dict:
    snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
    if verify:
        actual = sha256_bytes(_canonical_json(snapshot.get("records", [])))
        expected = snapshot.get("membership_sha256")
        if actual != expected:
            raise ValueError(
                "Universe snapshot hash mismatch for {}: expected {}, got {}".format(
                    path, expected, actual
                )
            )
    return snapshot


def eligible_symbols(snapshot: Mapping) -> set[str]:
    return {
        str(row["symbol"])
        for row in snapshot.get("records", [])
        if bool(row.get("eligible"))
    }


def listed_symbols(snapshot: Mapping) -> set[str]:
    """Symbols present on an allowed exchange, independent of strategy filters."""
    allowed = set(snapshot.get("allowed_exchanges", DEFAULT_EXCHANGES))
    return {
        str(row["symbol"])
        for row in snapshot.get("records", [])
        if row.get("exchange") in allowed
        and bool(_CACHE_SYMBOL.fullmatch(str(row.get("symbol", ""))))
    }


def diff_snapshots(previous: Mapping, current: Mapping) -> dict:
    before = eligible_symbols(previous)
    after = eligible_symbols(current)
    return {
        "previous_effective_date": previous.get("effective_date"),
        "current_effective_date": current.get("effective_date"),
        "previous_membership_sha256": previous.get("membership_sha256"),
        "current_membership_sha256": current.get("membership_sha256"),
        "added": sorted(after - before),
        "removed": sorted(before - after),
        "unchanged_count": len(before & after),
    }


def fetch_official_sources(timeout: float = 30.0) -> dict[str, str]:
    import requests

    headers = {"User-Agent": "us-trading-bot-universe/1.0 research contact=local"}
    sources = {}
    for name, url in (
        ("nasdaqlisted.txt", NASDAQ_LISTED_URL),
        ("otherlisted.txt", OTHER_LISTED_URL),
    ):
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        text = response.content.decode("utf-8-sig")
        if "File Creation Time:" not in text:
            raise ValueError("Missing source timestamp in {}".format(url))
        sources[name] = text
    return sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture immutable listed-universe snapshots")
    parser.add_argument(
        "--output-dir", default="data_cache/universe_snapshots", type=Path
    )
    parser.add_argument("--from-exchange-cache", type=Path)
    parser.add_argument("--effective-date")
    parser.add_argument(
        "--include-exchanges",
        default=",".join(sorted(DEFAULT_EXCHANGES)),
        help="Comma-separated canonical exchange names",
    )
    args = parser.parse_args()

    if args.from_exchange_cache:
        if not args.effective_date:
            parser.error("--effective-date is required with --from-exchange-cache")
        exchange_map = json.loads(args.from_exchange_cache.read_text(encoding="utf-8"))
        snapshot = build_legacy_snapshot(
            exchange_map, effective_date=args.effective_date
        )
        path = save_snapshot(snapshot, args.output_dir)
    else:
        allowed = {
            value.strip().upper()
            for value in args.include_exchanges.split(",")
            if value.strip()
        }
        sources = fetch_official_sources()
        snapshot = build_snapshot(
            sources["nasdaqlisted.txt"],
            sources["otherlisted.txt"],
            allowed_exchanges=allowed,
        )
        path = save_snapshot(snapshot, args.output_dir, raw_sources=sources)

    print(path)
    print(
        "eligible={}/{} membership_sha256={}".format(
            snapshot["eligible_count"],
            snapshot["record_count"],
            snapshot["membership_sha256"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
