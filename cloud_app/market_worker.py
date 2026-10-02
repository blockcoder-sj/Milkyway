"""Personal market display worker, scheduled independently from paper trading."""

import time
from concurrent.futures import ThreadPoolExecutor

from .config import get_settings
from .market_broker import refresh_broker, _provider as broker_provider
from .database import RuntimeHeartbeat, SessionLocal, prepare_runtime_database, utcnow
from .market_service import REFRESH_SECONDS, close_market_provider, refresh_market
from .company_price_feed import collect as collect_company_prices
from .company_prices import active as company_watches, refresh_public as refresh_company_prices
from .provider_process import ProviderProcess

company_provider = ProviderProcess(collect_company_prices)


def main():
    settings = get_settings()
    if not settings.personal_local_mode or settings.production:
        raise SystemExit("Market display worker requires personal local mode")
    errors = settings.startup_errors("deployment")
    if errors:
        raise SystemExit("Invalid personal configuration: " + "; ".join(errors))
    prepare_runtime_database()
    next_refresh = next_broker = 0.0
    detail = "waiting for first collection"
    pool = ThreadPoolExecutor(max_workers=2)
    pending = None
    price_pending = None
    next_price = 0.0
    watched = []
    try:
        while True:
            now = time.monotonic()
            current_watches = company_watches(settings)
            if price_pending is not None and price_pending.done():
                try:
                    price_pending.result()
                except (ValueError, OSError, RuntimeError):
                    pass
                price_pending = None
            if current_watches and price_pending is None and (now >= next_price or current_watches != watched):
                next_price, watched = now + 60, current_watches
                price_pending = pool.submit(refresh_company_prices, settings, company_provider)
            if pending is not None and pending.done():
                try:
                    cache = pending.result()
                    available = sum(bool(item.get("observation")) for item in cache["items"].values())
                    detail = f"Yahoo display quotes={available}"
                except (ValueError, OSError, RuntimeError):
                    detail = "display cache write failed; previous data preserved"
                pending = None
            if now >= next_refresh and pending is None:
                next_refresh = now + REFRESH_SECONDS
                pending = pool.submit(refresh_market, settings)
            if now >= next_broker:
                next_broker = now + 15
                try:
                    with SessionLocal() as session:
                        provider = refresh_broker(settings, session)
                    next_broker = now + (2 if provider == "kis" or current_watches else 15)
                except (ValueError, OSError, RuntimeError):
                    detail = "broker display unavailable; Yahoo fallback"
            with SessionLocal() as session:
                row = session.get(RuntimeHeartbeat, "market-data")
                if row is None:
                    row = RuntimeHeartbeat(component="market-data", instance_id="personal-market")
                row.observed_at, row.detail = utcnow(), detail
                session.add(row)
                session.commit()
            time.sleep(max(0.1, min(2, next_broker - time.monotonic())))
    finally:
        # Kill any in-flight provider before waiting on its executor thread.
        close_market_provider()
        broker_provider.close()
        company_provider.close()
        pool.shutdown(wait=True)


if __name__ == "__main__":
    main()
