"""Durable backtest queue plus the single-leader quote/paper loop."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import socket
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from sqlalchemy import select

from .config import get_settings
from .database import (
    BacktestJob,
    Lease,
    MarketDataConnection,
    RuntimeHeartbeat,
    SessionLocal,
    initialize_database,
    utcnow,
)
from .kis_quotes import KisCredentials
from .market_data_credentials import decrypt_market_credential
from .paper import (
    apply_terminal_events,
    collect_watchlist,
    KisQuoteProvider,
    make_quote_provider,
    mark_and_stop_accounts,
    rebalance_due_accounts,
    regular_market_open,
    store_member_quotes,
    store_quotes,
)
from .strategies import StrategySpec, run_strategy_backtest


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cloud_app.worker")
INSTANCE_ID = os.getenv("INSTANCE_ID", "{}:{}".format(socket.gethostname(), os.getpid()))
_member_provider_cache: dict[str, tuple[str, KisQuoteProvider]] = {}
_member_provider_lock = threading.Lock()
_member_retry_after: dict[str, float] = {}
_MEMBER_QUOTE_WORKERS = 8
_MEMBER_RETRY_SECONDS = 60.0


@dataclass(frozen=True)
class MemberFeedConfig:
    user_id: str
    provider: str
    environment: str
    encrypted_api_key: str
    encrypted_api_secret: str
    updated_at: dt.datetime


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


def _member_feed_config(connection: MarketDataConnection) -> MemberFeedConfig:
    return MemberFeedConfig(
        user_id=connection.user_id,
        provider=connection.provider,
        environment=connection.environment,
        encrypted_api_key=connection.encrypted_api_key,
        encrypted_api_secret=connection.encrypted_api_secret,
        updated_at=connection.updated_at,
    )


def _member_provider(connection: MemberFeedConfig, settings) -> KisQuoteProvider:
    version = "{}:{}:{}".format(
        connection.provider,
        connection.environment,
        connection.updated_at.isoformat(),
    )
    with _member_provider_lock:
        cached = _member_provider_cache.get(connection.user_id)
    if cached is not None and cached[0] == version:
        return cached[1]
    if connection.provider != "kis":
        raise RuntimeError("unsupported member quote provider")
    provider = KisQuoteProvider(
        KisCredentials(
            api_key=decrypt_market_credential(connection.encrypted_api_key, settings),
            api_secret=decrypt_market_credential(connection.encrypted_api_secret, settings),
            paper=connection.environment == "paper",
        ),
        source="kis_member",
    )
    with _member_provider_lock:
        existing = _member_provider_cache.get(connection.user_id)
        if existing is not None and existing[0] == version:
            return existing[1]
        _member_provider_cache[connection.user_id] = (version, provider)
    return provider


def _fetch_member_quotes(
    connection: MemberFeedConfig,
    settings,
    watchlist: tuple[str, ...],
):
    provider = _member_provider(connection, settings)
    return connection.user_id, provider.fetch(watchlist)


def _refresh_paper_progress(completed: int, total: int) -> None:
    progress_session = SessionLocal()
    try:
        if acquire_lease(progress_session, "paper-engine", 90):
            heartbeat(
                progress_session,
                "paper-worker",
                "member quote collection {}/{}".format(completed, total),
            )
            progress_session.commit()
        else:
            progress_session.rollback()
    except Exception:
        progress_session.rollback()
        logger.warning("paper worker progress heartbeat failed", exc_info=True)
    finally:
        progress_session.close()


def collect_member_quotes(session, settings) -> tuple[int, int]:
    if not regular_market_open():
        return 0, 0
    connections = session.scalars(select(MarketDataConnection)).all()
    active_users = {connection.user_id for connection in connections}
    with _member_provider_lock:
        for stale_user in set(_member_provider_cache) - active_users:
            _member_provider_cache.pop(stale_user, None)
            _member_retry_after.pop(stale_user, None)
    tasks: list[tuple[MemberFeedConfig, tuple[str, ...]]] = []
    now = time.monotonic()
    for connection in connections:
        if _member_retry_after.get(connection.user_id, 0.0) > now:
            continue
        watchlist = tuple(sorted(collect_watchlist(session, user_id=connection.user_id)))
        if watchlist:
            tasks.append((_member_feed_config(connection), watchlist))
    if not tasks:
        return 0, 0

    quote_count = 0
    error_count = 0
    last_progress = time.monotonic()
    with ThreadPoolExecutor(max_workers=min(_MEMBER_QUOTE_WORKERS, len(tasks))) as executor:
        futures = {
            executor.submit(_fetch_member_quotes, connection, settings, watchlist): connection.user_id
            for connection, watchlist in tasks
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            user_id = futures[future]
            try:
                returned_user_id, values = future.result()
                quote_count += store_member_quotes(session, returned_user_id, values)
                _member_retry_after.pop(user_id, None)
            except Exception as exc:
                error_count += 1
                with _member_provider_lock:
                    _member_provider_cache.pop(user_id, None)
                _member_retry_after[user_id] = time.monotonic() + _MEMBER_RETRY_SECONDS
                logger.error(
                    "member quote collection failed user=%s error=%s",
                    user_id,
                    type(exc).__name__,
                )
            if time.monotonic() - last_progress >= 15.0:
                _refresh_paper_progress(completed, len(tasks))
                last_progress = time.monotonic()
    return quote_count, error_count


def run_paper_tick(provider, settings=None) -> None:
    settings = settings or get_settings()
    session = SessionLocal()
    try:
        if not acquire_lease(session, "paper-engine", 90):
            session.rollback()
            return
        # Publish the lease before network I/O so another worker cannot start
        # the same paper tick while this one is collecting member quotes.
        session.commit()
        terminal = apply_terminal_events(session)
        quote_count = 0
        member_quote_count = 0
        member_quote_errors = 0
        rebalance_count = 0
        stop_count = 0
        if regular_market_open():
            watchlist = collect_watchlist(session)
            quotes = provider.fetch(watchlist)
            quote_count = store_quotes(session, quotes)
            member_quote_count, member_quote_errors = collect_member_quotes(session, settings)
            # SessionLocal disables autoflush. Make this tick's fresh shared and
            # member quotes visible to quote_map before any fills are evaluated.
            session.flush()
            # Keep the next-open contract aligned with backtest_core: rebalance
            # first, then apply the intraday stop to post-rebalance holdings.
            rebalance_count = rebalance_due_accounts(session)
            stop_count = mark_and_stop_accounts(session)
        heartbeat(
            session,
            "paper-worker",
            "quotes={} member_quotes={} member_errors={} stops={} rebalance_fills={} terminal={} review={}".format(
                quote_count,
                member_quote_count,
                member_quote_errors,
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
            run_paper_tick(provider, settings)
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
