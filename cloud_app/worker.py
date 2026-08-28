"""Durable backtest queue plus the single-leader quote/paper loop."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import socket
import time
import traceback

from sqlalchemy import select

from .config import get_settings
from .database import (
    BacktestJob,
    Lease,
    RuntimeHeartbeat,
    SessionLocal,
    initialize_database,
    utcnow,
)
from .paper import (
    apply_terminal_events,
    collect_watchlist,
    make_quote_provider,
    mark_and_stop_accounts,
    rebalance_due_accounts,
    store_quotes,
)
from .strategies import StrategySpec, run_strategy_backtest


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cloud_app.worker")
INSTANCE_ID = os.getenv("INSTANCE_ID", "{}:{}".format(socket.gethostname(), os.getpid()))


def heartbeat(session, component: str, detail: str = "") -> None:
    row = session.get(RuntimeHeartbeat, component)
    if row is None:
        row = RuntimeHeartbeat(component=component, instance_id=INSTANCE_ID, observed_at=utcnow())
        session.add(row)
    row.instance_id = INSTANCE_ID
    row.observed_at = utcnow()
    row.detail = detail[:1000]


def acquire_lease(session, name: str, ttl_seconds: int) -> bool:
    now = utcnow()
    row = session.get(Lease, name, with_for_update=True)
    if row is None:
        session.add(
            Lease(name=name, owner=INSTANCE_ID, expires_at=now + dt.timedelta(seconds=ttl_seconds))
        )
        return True
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=dt.timezone.utc)
    if row.owner == INSTANCE_ID or expires <= now:
        row.owner = INSTANCE_ID
        row.expires_at = now + dt.timedelta(seconds=ttl_seconds)
        return True
    return False


def claim_backtest(session) -> BacktestJob | None:
    statement = (
        select(BacktestJob)
        .where(BacktestJob.status == "queued")
        .order_by(BacktestJob.created_at)
        .limit(1)
    )
    if session.bind.dialect.name == "postgresql":
        statement = statement.with_for_update(skip_locked=True)
    job = session.scalar(statement)
    if job is None:
        return None
    job.status = "running"
    job.progress = 5
    job.worker_id = INSTANCE_ID
    job.started_at = utcnow()
    session.commit()
    return job


def process_one_backtest() -> bool:
    session = SessionLocal()
    try:
        job = claim_backtest(session)
        if job is None:
            return False
        logger.info("backtest started job=%s", job.id)
        spec = StrategySpec.model_validate_json(job.strategy.spec_json)
        result = run_strategy_backtest(
            spec,
            start=job.start_date.isoformat(),
            end=job.end_date.isoformat(),
            bias_mode=job.bias_mode,
        )
        job.result_json = json.dumps(result, ensure_ascii=False, default=str, separators=(",", ":"))
        job.status = "completed"
        job.progress = 100
        job.finished_at = utcnow()
        session.commit()
        logger.info("backtest completed job=%s", job.id)
        return True
    except Exception as exc:
        session.rollback()
        if "job" in locals() and job is not None:
            job = session.get(BacktestJob, job.id)
            job.status = "failed"
            job.error = "{}: {}".format(type(exc).__name__, str(exc))[:4000]
            job.finished_at = utcnow()
            session.commit()
        logger.error("backtest failed: %s\n%s", exc, traceback.format_exc())
        return True
    finally:
        session.close()


def run_paper_tick(provider) -> None:
    session = SessionLocal()
    try:
        if not acquire_lease(session, "paper-engine", 90):
            session.rollback()
            return
        terminal = apply_terminal_events(session)
        watchlist = collect_watchlist(session)
        quotes = provider.fetch(watchlist)
        quote_count = store_quotes(session, quotes)
        # Keep the next-open contract aligned with backtest_core: rebalance
        # first, then apply the intraday stop to the post-rebalance holdings.
        rebalance_count = rebalance_due_accounts(session)
        stop_count = mark_and_stop_accounts(session)
        heartbeat(
            session,
            "paper-worker",
            "quotes={} stops={} rebalance_fills={} terminal={} review={}".format(
                quote_count,
                stop_count,
                rebalance_count,
                terminal["settled"],
                terminal["review_accounts"],
            ),
        )
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("paper tick failed")
    finally:
        session.close()


def main() -> int:
    settings = get_settings()
    role = os.getenv("WORKER_ROLE", "all").strip().lower()
    if role not in {"all", "backtest", "paper"}:
        raise SystemExit("WORKER_ROLE must be all, backtest or paper")
    errors = settings.startup_errors()
    if errors:
        raise SystemExit("Startup configuration failed:\n- " + "\n- ".join(errors))
    initialize_database()
    provider = make_quote_provider(settings) if role in {"all", "paper"} else None
    logger.info(
        "worker started instance=%s role=%s quote_provider=%s",
        INSTANCE_ID,
        role,
        settings.quote_provider if provider else "disabled",
    )
    next_paper = 0.0
    next_heartbeat = 0.0
    while True:
        did_work = process_one_backtest() if role in {"all", "backtest"} else False
        now = time.monotonic()
        if provider is not None and now >= next_paper:
            run_paper_tick(provider)
            next_paper = now + settings.quote_interval_seconds
        if role == "backtest" and now >= next_heartbeat:
            session = SessionLocal()
            try:
                heartbeat(session, "backtest-worker", "queue polling")
                session.commit()
            finally:
                session.close()
            next_heartbeat = now + 15.0
        if not did_work:
            time.sleep(1.0)


if __name__ == "__main__":
    raise SystemExit(main())
