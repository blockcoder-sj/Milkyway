"""Personal market display worker, scheduled independently from paper trading."""

import time

from .config import get_settings
from .database import RuntimeHeartbeat, SessionLocal, prepare_runtime_database, utcnow
from .market_service import REFRESH_SECONDS, close_market_provider, refresh_market


def main():
    settings = get_settings()
    if not settings.personal_local_mode or settings.production:
        raise SystemExit("Market display worker requires personal local mode")
    errors = settings.startup_errors("deployment")
    if errors:
        raise SystemExit("Invalid personal configuration: " + "; ".join(errors))
    prepare_runtime_database()
    next_refresh = 0.0
    detail = "waiting for first collection"
    try:
        while True:
            if time.monotonic() >= next_refresh:
                try:
                    cache = refresh_market(settings)
                    available = sum(bool(item.get("observation")) for item in cache["items"].values())
                    failed = sum(bool(item.get("error")) for item in cache["items"].values())
                    detail = f"display quotes={available} unavailable_or_cached={failed}"
                except (ValueError, OSError, RuntimeError):
                    detail = "display cache write failed; previous data preserved"
                next_refresh = time.monotonic() + REFRESH_SECONDS
            with SessionLocal() as session:
                row = session.get(RuntimeHeartbeat, "market-data")
                if row is None:
                    row = RuntimeHeartbeat(component="market-data", instance_id="personal-market")
                row.observed_at, row.detail = utcnow(), detail
                session.add(row)
                session.commit()
            time.sleep(15)
    finally:
        close_market_provider()


if __name__ == "__main__":
    main()
