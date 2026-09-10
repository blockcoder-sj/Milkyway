"""Durable backtest queue plus the single-leader quote/paper loop."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import signal
import socket
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import delete, select, update

from .config import get_settings
from .credential_broker_client import (
    CredentialBrokerError,
    broker_member_quotes,
    broker_preflight,
    broker_shared_quotes,
    broker_next_work,
    broker_complete_work,
    broker_work_quotes,
)
from .database import (
    BacktestJob,
    bind_runtime_context,
    Lease,
    MarketDataConnection,
    RuntimeHeartbeat,
    SessionLocal,
    WorkCursor,
    acquire_transaction_lock,
    prepare_runtime_database,
    quota_allocation,
    utcnow,
)
from .kis_quotes import KisCredentials
from .market_data_credentials import decrypt_market_credential
from .paper import (
    apply_terminal_events,
    collect_holding_watchlist_ordered,
    collect_watchlist,
    collect_watchlist_ordered,
    KisQuoteProvider,
    make_quote_provider,
    mark_and_stop_accounts,
    QuoteProvider,
    rebalance_due_accounts,
    regular_market_open,
    store_member_quotes,
    store_quotes,
    TossQuoteProvider,
)
from .strategies import StrategySpec, run_strategy_backtest
from .toss_quotes import TossCredentials


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cloud_app.worker")
INSTANCE_ID = os.getenv("INSTANCE_ID", "{}:{}".format(socket.gethostname(), os.getpid()))
_member_provider_cache: dict[str, tuple[str, QuoteProvider]] = {}
_member_provider_lock = threading.Lock()
_member_retry_after: dict[str, float] = {}
_MEMBER_QUOTE_WORKERS = 8
_MEMBER_RETRY_SECONDS = 60.0


class PaperTickDeadlineExceeded(RuntimeError):
    """The complete quote and ledger tick exceeded its liveness budget."""


@contextmanager
def _paper_tick_deadline(seconds: float):
    """Hard-bound the whole production paper tick on the Unix worker."""

    if not hasattr(signal, "setitimer") or threading.current_thread() is not threading.main_thread():
        raise RuntimeError("paper tick deadlines require the main Unix worker thread")
    previous_handler = signal.getsignal(signal.SIGALRM)

    def expired(_signum, _frame):
        raise PaperTickDeadlineExceeded("paper tick deadline was exceeded")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, float(seconds)))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


@dataclass(frozen=True)
class MemberFeedConfig:
    user_id: str
    provider: str
    environment: str
    encrypted_api_key: str
    encrypted_api_secret: str
    updated_at: dt.datetime


class CredentialBrokerSharedQuoteProvider(QuoteProvider):
    """Shared quote adapter that keeps deployment broker credentials off the worker."""

    def __init__(self, settings):
        self.settings = settings

    def fetch(self, tickers):
        ordered = tuple(dict.fromkeys(str(value).strip().upper() for value in tickers))
        maximum = int(
            getattr(self.settings, "shared_quote_max_symbols_per_tick", len(ordered))
        )
        if len(ordered) > maximum:
            raise RuntimeError(
                "shared quote worklist exceeded the admitted per-tick limit"
            )
        batch_size = min(200, max(1, int(self.settings.shared_quote_batch_size)))
        deadline = time.monotonic() + float(
            getattr(self.settings, "shared_quote_tick_deadline_seconds", 30.0)
        )
        values = []
        for offset in range(0, len(ordered), batch_size):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning("shared quote tick deadline exhausted offset=%s", offset)
                break
            batch = ordered[offset : offset + batch_size]
            try:
                values.extend(
                    broker_shared_quotes(
                        self.settings,
                        tickers=batch,
                        timeout_seconds=remaining,
                    )
                )
            except CredentialBrokerError as exc:
                logger.warning(
                    "shared quote batch failed offset=%s size=%s error=%s",
                    offset,
                    len(batch),
                    type(exc).__name__,
                )
        return values


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


def _rotating_work_slice(
    session,
    name: str,
    values,
    maximum: int,
) -> tuple[str, ...]:
    """Select a durable wrapping slice so stable suffixes get eventual service."""

    ordered = tuple(dict.fromkeys(str(value) for value in values))
    maximum = max(0, int(maximum))
    if not ordered or maximum == 0:
        return ()
    with quota_allocation(session, "work-cursor", name):
        statement = select(WorkCursor).where(WorkCursor.name == name)
        if session.bind.dialect.name == "postgresql":
            statement = statement.with_for_update()
        cursor = session.scalar(statement)
        if cursor is None:
            cursor = WorkCursor(name=name, position=0)
            session.add(cursor)
        if cursor.cursor_key and cursor.cursor_key in ordered:
            start = (ordered.index(cursor.cursor_key) + 1) % len(ordered)
        else:
            start = int(cursor.position or 0) % len(ordered)
        count = min(maximum, len(ordered))
        selected = tuple(ordered[(start + offset) % len(ordered)] for offset in range(count))
        cursor.position = (start + count) % len(ordered)
        cursor.cursor_key = selected[-1]
        cursor.updated_at = utcnow()
        session.flush()
        return selected


def _fair_quote_work_slice(
    session,
    holdings,
    candidates,
    maximum: int,
) -> tuple[str, ...]:
    """Rotate one held-first worklist so every admitted symbol is serviced."""

    holding_values = tuple(dict.fromkeys(str(value) for value in holdings))
    holding_set = set(holding_values)
    candidate_values = tuple(
        value
        for value in dict.fromkeys(str(value) for value in candidates)
        if value not in holding_set
    )
    return _rotating_work_slice(
        session,
        "shared-quote-worklist",
        holding_values + candidate_values,
        maximum,
    )


def claim_backtest(session) -> BacktestJob | None:
    settings = get_settings()
    stale_before = utcnow() - dt.timedelta(seconds=settings.backtest_timeout_seconds)
    session.execute(
        update(BacktestJob)
        .where(
            BacktestJob.status == "running",
            BacktestJob.started_at.is_not(None),
            BacktestJob.started_at < stale_before,
        )
        .values(
            status="failed",
            error="Backtest exceeded its execution deadline",
            finished_at=utcnow(),
        )
    )
    with quota_allocation(session, "backtest-claim", "global"):
        owners = tuple(
            session.scalars(
                select(BacktestJob.user_id)
                .where(BacktestJob.status == "queued")
                .distinct()
                .order_by(BacktestJob.user_id)
            ).all()
        )
        if not owners:
            session.commit()
            return None
        cursor = session.get(WorkCursor, "backtest-owner")
        last_owner = cursor.cursor_key if cursor is not None else ""
        owner = next((candidate for candidate in owners if candidate > last_owner), owners[0])
        statement = (
            select(BacktestJob)
            .where(BacktestJob.status == "queued", BacktestJob.user_id == owner)
            .order_by(BacktestJob.created_at, BacktestJob.id)
            .limit(1)
        )
        if session.bind.dialect.name == "postgresql":
            statement = statement.with_for_update(skip_locked=True)
        job = session.scalar(statement)
        if job is None:
            session.rollback()
            return None
        if cursor is None:
            cursor = WorkCursor(name="backtest-owner", position=0)
            session.add(cursor)
        cursor.cursor_key = owner
        cursor.updated_at = utcnow()
        job.status = "running"
        job.progress = 5
        job.worker_id = INSTANCE_ID
        job.started_at = utcnow()
        session.commit()
        return job


def _prune_backtest_results(session, user_id: str, settings) -> None:
    cutoff = utcnow() - dt.timedelta(days=settings.backtest_retention_days)
    session.execute(
        delete(BacktestJob).where(
            BacktestJob.user_id == user_id,
            BacktestJob.status.in_(("completed", "failed")),
            BacktestJob.finished_at.is_not(None),
            BacktestJob.finished_at < cutoff,
        )
    )
    excess = session.scalars(
        select(BacktestJob.id)
        .where(
            BacktestJob.user_id == user_id,
            BacktestJob.status.in_(("completed", "failed")),
        )
        .order_by(BacktestJob.finished_at.desc(), BacktestJob.id.desc())
        .offset(settings.max_completed_backtests_per_user)
    ).all()
    if excess:
        session.execute(delete(BacktestJob).where(BacktestJob.id.in_(excess)))


@contextmanager
def _backtest_deadline(seconds: int):
    """Interrupt CPU-bound work in the worker main thread on POSIX."""

    if threading.current_thread() is not threading.main_thread() or not hasattr(
        signal, "setitimer"
    ):
        started = time.monotonic()
        yield
        if time.monotonic() - started > seconds:
            raise TimeoutError("Backtest exceeded its execution deadline")
        return

    def expired(_signum, _frame):
        raise TimeoutError("Backtest exceeded its execution deadline")

    previous = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous)


def process_one_backtest() -> bool:
    session = SessionLocal()
    work = None
    try:
        runtime_settings = get_settings()
        if runtime_settings.authority_enabled:
            work = broker_next_work(runtime_settings, "backtest")
            if work is None:
                return False
            bind_runtime_context(session, claim_token=work["claim"])
            job = session.get(BacktestJob, work["resource_id"])
        else:
            job = claim_backtest(session)
        if job is None:
            return False
        job_id = job.id
        logger.info("backtest started job=%s", job_id)
        spec = StrategySpec.model_validate_json(job.strategy.spec_json)
        arguments = {"start": job.start_date.isoformat(), "end": job.end_date.isoformat(), "bias_mode": job.bias_mode}
        # Computation can last minutes. Release the DB transaction and later
        # re-enter through the same live claim before persisting the result.
        session.rollback()
        with _backtest_deadline(runtime_settings.backtest_timeout_seconds):
            result = run_strategy_backtest(spec, **arguments)
        encoded_result = json.dumps(
            result, ensure_ascii=False, default=str, separators=(",", ":")
        )
        if len(encoded_result.encode("utf-8")) > runtime_settings.max_backtest_result_bytes:
            raise ValueError("Backtest result exceeded the retained byte limit")
        job = session.get(BacktestJob, job_id)
        if job is None or job.status != "running":
            return True
        job.result_json = encoded_result
        job.status = "completed"
        job.progress = 100
        job.finished_at = utcnow()
        if not runtime_settings.authority_enabled:
            _prune_backtest_results(session, job.user_id, runtime_settings)
        session.commit()
        logger.info("backtest completed job=%s", job.id)
        return True
    except Exception as exc:
        session.rollback()
        if "job_id" in locals():
            job = session.get(BacktestJob, job_id)
            if job is not None:
                job.status = "failed"
                job.error = "{}: {}".format(type(exc).__name__, str(exc))[:4000]
                job.finished_at = utcnow()
                if not get_settings().authority_enabled:
                    _prune_backtest_results(session, job.user_id, get_settings())
                session.commit()
        logger.error("backtest failed: %s\n%s", exc, traceback.format_exc())
        return True
    finally:
        session.close()
        if work is not None:
            try:
                broker_complete_work(get_settings(), "backtest", work["claim"])
            except CredentialBrokerError:
                logger.warning("backtest claim completion unavailable; expiry remains enforced")


def _member_feed_config(connection: MarketDataConnection) -> MemberFeedConfig:
    return MemberFeedConfig(
        user_id=connection.user_id,
        provider=connection.provider,
        environment=connection.environment,
        encrypted_api_key=connection.encrypted_api_key,
        encrypted_api_secret=connection.encrypted_api_secret,
        updated_at=connection.updated_at,
    )


def _member_feed_version(connection: MemberFeedConfig | MarketDataConnection) -> str:
    return "{}:{}:{}".format(
        connection.provider,
        connection.environment,
        connection.updated_at.isoformat(),
    )


def _member_provider(connection: MemberFeedConfig, settings) -> QuoteProvider:
    version = _member_feed_version(connection)
    with _member_provider_lock:
        cached = _member_provider_cache.get(connection.user_id)
    if cached is not None and cached[0] == version:
        return cached[1]
    api_key = decrypt_market_credential(
        connection.encrypted_api_key,
        settings,
        owner_id=connection.user_id,
        provider=connection.provider,
        environment=connection.environment,
        label="App Key",
    )
    api_secret = decrypt_market_credential(
        connection.encrypted_api_secret,
        settings,
        owner_id=connection.user_id,
        provider=connection.provider,
        environment=connection.environment,
        label="App Secret",
    )
    if connection.provider == "kis":
        provider = KisQuoteProvider(
            KisCredentials(
                api_key=api_key,
                api_secret=api_secret,
                paper=connection.environment == "paper",
            ),
            source="kis_member",
        )
    elif connection.provider == "toss" and connection.environment == "live":
        provider = TossQuoteProvider(
            TossCredentials(client_id=api_key, client_secret=api_secret),
            source="toss_member",
        )
    else:
        raise RuntimeError("unsupported member quote provider")
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
    if getattr(settings, "credential_backend", "local") == "broker":
        values = broker_member_quotes(
            settings,
            owner_id=connection.user_id,
            provider=connection.provider,
            environment=connection.environment,
            encrypted_api_key=connection.encrypted_api_key,
            encrypted_api_secret=connection.encrypted_api_secret,
            tickers=watchlist,
        )
        return connection.user_id, values
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
    if not getattr(settings, "member_credentials_enabled", True):
        return 0, 0
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
    fetched_quotes: list[tuple[MemberFeedConfig, str, list]] = []
    last_progress = time.monotonic()
    with ThreadPoolExecutor(max_workers=min(_MEMBER_QUOTE_WORKERS, len(tasks))) as executor:
        futures = {
            executor.submit(_fetch_member_quotes, connection, settings, watchlist): connection
            for connection, watchlist in tasks
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            connection = futures[future]
            user_id = connection.user_id
            try:
                returned_user_id, values = future.result()
                if returned_user_id != user_id:
                    raise RuntimeError("member quote provider returned a mismatched user")
                fetched_quotes.append((connection, returned_user_id, values))
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

    # Network I/O is complete before row locks are taken, keeping settings
    # updates responsive while still ordering replace/delete against quote writes.
    for connection, user_id, values in fetched_quotes:
        acquire_transaction_lock(session, "market-connection", user_id)
        current = session.scalar(
            select(MarketDataConnection)
            .where(MarketDataConnection.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        if current is None or _member_feed_version(current) != _member_feed_version(connection):
            with _member_provider_lock:
                _member_provider_cache.pop(user_id, None)
            _member_retry_after.pop(user_id, None)
            logger.info("member quotes discarded after connection change user=%s", user_id)
            continue
        quote_count += store_member_quotes(session, user_id, values)
        # Hold the connection-row lock through this write/transaction so a
        # concurrent replace/delete purges these rows after we commit.
        session.flush()
        _member_retry_after.pop(user_id, None)
    return quote_count, error_count


def run_paper_tick(provider, settings=None) -> None:
    settings = settings or get_settings()
    if getattr(settings, "authority_enabled", False):
        run_authorized_paper_tick(settings)
        return
    session = SessionLocal()
    try:
        with _paper_tick_deadline(
            float(getattr(settings, "shared_quote_tick_deadline_seconds", 30.0))
        ):
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
                watchlist = collect_watchlist_ordered(session)
                maximum = int(
                    getattr(settings, "shared_quote_max_symbols_per_tick", len(watchlist))
                )
                holdings = collect_holding_watchlist_ordered(session)
                holding_set = set(holdings)
                candidates = tuple(value for value in watchlist if value not in holding_set)
                admitted = _fair_quote_work_slice(
                    session, holdings, candidates, maximum
                )
                # Advance the fairness cursor even when the provider fails. Otherwise
                # a persistently failing prefix rolls the cursor back and can starve
                # every valid symbol behind it forever. Terminal-event application is
                # idempotent and is safe to commit at this boundary as well.
                session.commit()
                quotes = provider.fetch(admitted)
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
    except PaperTickDeadlineExceeded:
        session.invalidate()
        logger.critical("paper tick hard deadline exceeded; terminating worker")
        raise
    except Exception:
        session.rollback()
        logger.exception("paper tick failed")
    finally:
        session.close()


def run_authorized_paper_tick(settings):
    with _paper_tick_deadline(settings.shared_quote_tick_deadline_seconds):
        with ThreadPoolExecutor(max_workers=min(8, settings.quote_max_concurrent_requests)) as executor:
            futures = [executor.submit(_fetch_authorized_paper_work, settings)
                       for _ in range(min(8, settings.quote_max_concurrent_requests))]
            for future in as_completed(futures):
                work = future.result()
                if work is not None:
                    _apply_authorized_paper_work(settings, work)
    with SessionLocal() as session:
        heartbeat(session, "paper-worker", "authorized member batches")
        session.commit()


def _finish_authorized_paper_work(settings, work):
    try:
        broker_complete_work(settings, "paper", work["claim"])
    except CredentialBrokerError:
        logger.warning("paper claim completion unavailable; expiry remains enforced")


def _fetch_authorized_paper_work(settings):
    work = None
    try:
        # The broker chooses the account and exact symbols using trusted data.
        # Service credentials alone cannot request arbitrary owners or symbols.
        work = broker_next_work(settings, "paper")
        if work is None:
            return None
        if work.get("quotes_required", True):
            broker_work_quotes(settings, work["claim"])
        return work
    except Exception:
        logger.exception("authorized paper quote fetch failed")
        if work is not None:
            _finish_authorized_paper_work(settings, work)
        return None


def _apply_authorized_paper_work(settings, work):
    # Ledger work remains on the main Unix thread under the one whole-tick
    # signal deadline. Only independent network fetches use the thread pool.
    try:
        with SessionLocal() as session:
            bind_runtime_context(session, claim_token=work["claim"])
            apply_terminal_events(session, settings)
            if regular_market_open() and work.get("quotes_required", True):
                rebalance_due_accounts(session)
                mark_and_stop_accounts(session)
            heartbeat(session, "paper-worker", "authorized account tick")
            session.commit()
    except PaperTickDeadlineExceeded:
        raise
    except Exception:
        logger.exception("authorized paper tick failed")
    finally:
        _finish_authorized_paper_work(settings, work)


def main() -> int:
    settings = get_settings()
    role = os.getenv("WORKER_ROLE", "all").strip().lower()
    if role not in {"all", "backtest", "paper"}:
        raise SystemExit("WORKER_ROLE must be all, backtest or paper")
    if settings.production and role == "all":
        raise SystemExit(
            "production requires separate paper and backtest workers for quote liveness"
        )
    errors = settings.startup_errors(role if role != "all" else "deployment")
    if errors:
        raise SystemExit("Startup configuration failed:\n- " + "\n- ".join(errors))
    prepare_runtime_database()
    if settings.credential_backend == "broker":
        broker_preflight(settings, "paper" if role == "all" else role)
    provider = None
    if role in {"all", "paper"}:
        provider = (
            CredentialBrokerSharedQuoteProvider(settings)
            if settings.credential_backend == "broker" and settings.quote_provider == "kis"
            else make_quote_provider(settings)
        )
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
