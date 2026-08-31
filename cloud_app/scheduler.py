"""Runs data maintenance after the US close with a database lease."""

from __future__ import annotations

import datetime as dt
import logging
import os
import socket
import time

from market_calendar import is_trading_day

from .config import get_settings
from .data_refresh import run_daily_refresh
from .database import SessionLocal, initialize_database
from .worker import acquire_lease, heartbeat


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cloud_app.scheduler")


def _now_et() -> dt.datetime:
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from pytz import timezone as ZoneInfo
    return dt.datetime.now(ZoneInfo("America/New_York"))


def main() -> int:
    errors = get_settings().startup_errors("scheduler")
    if errors:
        raise SystemExit("Startup configuration failed:\n- " + "\n- ".join(errors))
    initialize_database()
    last_run: dt.date | None = None
    logger.info("data scheduler started host=%s", socket.gethostname())
    while True:
        now = _now_et()
        session = SessionLocal()
        try:
            heartbeat(session, "data-scheduler", "last_run={}".format(last_run))
            should_run = (
                is_trading_day(now.date())
                and (now.hour, now.minute) >= (18, 30)
                and last_run != now.date()
                and acquire_lease(session, "daily-data-refresh", 7200)
            )
            session.commit()
        finally:
            session.close()
        if should_run:
            try:
                run_daily_refresh()
                last_run = now.date()
            except Exception:
                logger.exception("daily data refresh failed; will retry in 15 minutes")
                time.sleep(900)
                continue
        time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())
