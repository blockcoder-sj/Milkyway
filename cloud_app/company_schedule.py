"""Round-robin free research refresh across received sector company directories."""
import datetime as dt
from fastapi import HTTPException
from .market_catalog import BY_ID
from .market_details import read_cache
from .company_service import root, read_company, enqueue_company, QUEUE_LIMIT, REFRESH_SECONDS
from .bounded_io import read_bounded_json
from .market_service import _write_cache

SCAN_LIMIT = 50


def cursors(path):
    try:
        value = read_bounded_json(path, maximum_bytes=8192)
        return {key: number for key, number in value.items()
                if key in BY_ID and type(number) is int and 0 <= number <= 1100}
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def automatic(path):
    try:
        return read_bounded_json(path, maximum_bytes=4096).get("automatic") is True
    except (OSError, ValueError, TypeError):
        return False


def schedule(settings, now=None):
    """One due issuer per sector per minute; keep twenty slots for explicit requests."""
    now = now or dt.datetime.now(dt.timezone.utc)
    requests = root(settings) / "requests"
    requests.mkdir(parents=True, exist_ok=True)
    available = max(0, QUEUE_LIMIT - 20 - sum(1 for _ in requests.glob("*.json")))
    cursor_path = root(settings) / "schedule" / "cursors.json"
    positions = cursors(cursor_path)
    queued = []
    for sector, definition in BY_ID.items():
        if not available:
            break
        if definition.group != "sectors":
            continue
        rows = read_cache(settings, sector).companies.rows
        if not rows:
            continue
        start = positions.get(sector, 0) % len(rows)
        # A fully populated large directory must not block worker heartbeats by
        # reopening thousands of profiles. Resume the bounded scan next minute.
        for offset in range(min(len(rows), SCAN_LIMIT)):
            index = (start + offset) % len(rows)
            row = rows[index]
            positions[sector] = (index + 1) % len(rows)
            cached = read_company(settings, row.symbol)
            if cached and cached.attempted_at:
                wait = 3600 if cached.errors else REFRESH_SECONDS
                # Old profiles are reprocessed once to add filing body evidence.
                if not cached.errors and not cached.report_analysis and not row.symbol.endswith(".KS"):
                    wait = 3600
                if (now - cached.attempted_at).total_seconds() < wait:
                    continue
            path = requests / (row.symbol + ".json")
            if path.exists():
                continue
            try:
                result = enqueue_company(settings, sector, row.symbol, automatic_request=True, now=now)
                if result["status"] != "queued" or not path.exists():
                    continue
                queued.append(row.symbol)
                available -= 1
                break
            except HTTPException:
                continue
    _write_cache(cursor_path, positions)
    return queued
