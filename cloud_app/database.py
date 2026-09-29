"""Relational state for users, jobs and idempotent paper fills."""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    inspect,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from .config import get_settings


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(60))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="member")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BrowserSession(Base):
    """Revocable browser session; only a SHA-256 token identifier is stored."""

    __tablename__ = "browser_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship()


class AuthoritySession(Base):
    """Opaque sessions minted only by the independent authentication authority."""

    __tablename__ = "authority_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OperationPermit(Base):
    """Short-lived, single-use broker authorization; no plaintext keys stored."""

    __tablename__ = "operation_permits"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_hash: Mapped[str] = mapped_column(ForeignKey("authority_sessions.token_hash", ondelete="CASCADE"))
    operation: Mapped[str] = mapped_column(String(40))
    audience: Mapped[str] = mapped_column(String(20))
    nonce: Mapped[str] = mapped_column(String(64))
    payload_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("session_hash", "operation", "nonce"),)


class WorkClaim(Base):
    """Authority-selected worker resource and exact permitted quote work."""

    __tablename__ = "work_claims"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    service: Mapped[str] = mapped_column(String(20), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[str] = mapped_column(String(32), index=True)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"))
    tickers_json: Mapped[str] = mapped_column(Text, default="[]")
    credential_version: Mapped[str] = mapped_column(String(128), default="")
    slot: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    quotes_consumed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("service", "resource_id", "slot"),)


class AdmittedTicker(Base):
    """Symbols selected by the authority, never by a worker's ledger writes."""

    __tablename__ = "admitted_tickers"
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id", ondelete="CASCADE"), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    admitted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkResource(Base):
    """Exact accounts/strategies in one authority-selected member quote batch."""

    __tablename__ = "work_resources"
    claim_hash: Mapped[str] = mapped_column(ForeignKey("work_claims.token_hash", ondelete="CASCADE"), primary_key=True)
    resource_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"))
    tickers_json: Mapped[str] = mapped_column(Text)


class LoginThrottle(Base):
    """Privacy-preserving durable authentication admission bucket."""

    __tablename__ = "login_throttles"
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    bucket_kind: Mapped[str] = mapped_column(String(20))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    window_started_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, index=True
    )


def invitation_token_hash(token: str, secret: str) -> str:
    if len(token) < 20 or len(token) > 256:
        raise ValueError("invitation token length is invalid")
    return hmac.new(
        secret.encode("utf-8"),
        ("milkyway-invitation\0" + token).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class Invitation(Base):
    """A recipient-bound, expiring, single-use club membership grant."""

    __tablename__ = "invitations"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    redeemed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    redeemed_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    @classmethod
    def create(
        cls,
        *,
        token: str,
        email: str,
        expires_at: dt.datetime,
        secret: str,
    ) -> "Invitation":
        return cls(
            token_hash=invitation_token_hash(token, secret),
            email=email,
            expires_at=expires_at,
        )


class AiConnection(Base):
    """One user-selected AI connection; cloud credentials stay encrypted."""

    __tablename__ = "ai_connections"
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    key_hint: Mapped[str] = mapped_column(String(12))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    user: Mapped[User] = relationship()


class MarketDataConnection(Base):
    """One verified, member-owned quote connection; secrets stay encrypted."""

    __tablename__ = "market_data_connections"
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    provider: Mapped[str] = mapped_column(String(30))
    environment: Mapped[str] = mapped_column(String(20))
    encrypted_api_key: Mapped[str] = mapped_column(Text, deferred=True)
    encrypted_api_secret: Mapped[str] = mapped_column(Text, deferred=True)
    key_hint: Mapped[str] = mapped_column(String(12))
    secret_hint: Mapped[str] = mapped_column(String(12))
    verified_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    user: Mapped[User] = relationship()


class Strategy(Base):
    __tablename__ = "strategies"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    original_prompt: Mapped[str] = mapped_column(Text, default="")
    spec_json: Mapped[str] = mapped_column(Text)
    spec_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship()
    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_strategy_id_user"),
    )


class BacktestJob(Base):
    __tablename__ = "backtest_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    bias_mode: Mapped[str] = mapped_column(String(20), default="strict")
    start_date: Mapped[dt.date] = mapped_column(Date)
    end_date: Mapped[dt.date] = mapped_column(Date)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    strategy: Mapped[Strategy] = relationship()
    __table_args__ = (
        ForeignKeyConstraint(
            ("strategy_id", "user_id"),
            ("strategies.id", "strategies.user_id"),
            ondelete="CASCADE",
            name="fk_backtest_strategy_owner",
        ),
    )


class PaperAccount(Base):
    __tablename__ = "paper_accounts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(100))
    initial_cash: Mapped[float] = mapped_column(Float)
    cash: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    last_rebalanced_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    strategy: Mapped[Strategy] = relationship()
    __table_args__ = (
        ForeignKeyConstraint(
            ("strategy_id", "user_id"),
            ("strategies.id", "strategies.user_id"),
            ondelete="RESTRICT",
            name="fk_paper_account_strategy_owner",
        ),
    )


class PaperPosition(Base):
    __tablename__ = "paper_positions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    shares: Mapped[float] = mapped_column(Float)
    avg_price: Mapped[float] = mapped_column(Float)
    last_price: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("account_id", "ticker", name="uq_position_account_ticker"),)


class PaperFill(Base):
    __tablename__ = "paper_fills"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True)
    ticker: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(String(8))
    shares: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(40))
    dedupe_key: Mapped[str] = mapped_column(String(180), unique=True)
    executed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class EquityPoint(Base):
    __tablename__ = "equity_points"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    account_id: Mapped[str] = mapped_column(ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True)
    equity: Mapped[float] = mapped_column(Float)
    cash: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (Index("ix_equity_account_observed", "account_id", "observed_at"),)


class Quote(Base):
    __tablename__ = "quotes"
    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    price: Mapped[float] = mapped_column(Float)
    bid: Mapped[float] = mapped_column(Float, default=0.0)
    ask: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(40))
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)


class MemberQuote(Base):
    """A quote visible only to one member and that member's paper accounts."""

    __tablename__ = "member_quotes"
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    price: Mapped[float] = mapped_column(Float)
    bid: Mapped[float] = mapped_column(Float, default=0.0)
    ask: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(40))
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    user: Mapped[User] = relationship()


class RuntimeHeartbeat(Base):
    __tablename__ = "runtime_heartbeats"
    component: Mapped[str] = mapped_column(String(50), primary_key=True)
    instance_id: Mapped[str] = mapped_column(String(100))
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    detail: Mapped[str] = mapped_column(Text, default="")


class Lease(Base):
    __tablename__ = "leases"
    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    owner: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)


class WorkCursor(Base):
    """Durable fair-scheduling position shared across worker restarts."""

    __tablename__ = "work_cursors"
    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    cursor_key: Mapped[str] = mapped_column(String(128), default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


settings = get_settings()
_sqlite_path: Path | None = None
if settings.database_url.startswith("sqlite"):
    raw_path = settings.database_url.split("///", 1)[-1]
    if raw_path != ":memory:":
        _sqlite_path = Path(raw_path)
        parent = _sqlite_path.parent
        if parent != Path("."):
            parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(parent, 0o700)


def _secure_sqlite_files() -> None:
    if _sqlite_path is None:
        return
    parent = _sqlite_path.parent
    if parent != Path(".") and parent.exists():
        os.chmod(parent, 0o700)
    for path in (
        _sqlite_path,
        Path(str(_sqlite_path) + "-wal"),
        Path(str(_sqlite_path) + "-shm"),
    ):
        if path.exists():
            os.chmod(path, 0o600)

_engine_options: dict = {"pool_pre_ping": True, "hide_parameters": True}
if settings.database_url.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}
else:
    _engine_options["connect_args"] = {"connect_timeout": 5, "options": "-c statement_timeout=10000 -c idle_in_transaction_session_timeout=15000"}
    _engine_options.update(
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
    )
engine = create_engine(settings.database_url, **_engine_options)


if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
        _secure_sqlite_files()


class RuntimeSession(Session):
    """Reapply verified-token context for every transaction, including pool reuse."""


@event.listens_for(RuntimeSession, "after_begin")
def _runtime_context(session, _transaction, connection):
    if connection.dialect.name == "postgresql":
        connection.execute(text(
            "SELECT set_config('milkyway.auth_token', :auth, true), "
            "set_config('milkyway.claim_token', :claim, true)"
        ), {"auth": session.info.get("auth_token", ""), "claim": session.info.get("claim_token", "")})


def bind_runtime_context(session, *, auth_token: str = "", claim_token: str = "") -> None:
    if session.in_transaction():
        raise RuntimeError("Cannot change a principal inside an active transaction")
    if auth_token and claim_token:
        raise RuntimeError("A transaction must have exactly one authorization audience")
    session.info["auth_token"] = auth_token
    session.info["claim_token"] = claim_token


SessionLocal = sessionmaker(bind=engine, class_=RuntimeSession, expire_on_commit=False, autoflush=False)

_local_quota_locks_guard = threading.Lock()
_local_quota_locks: dict[int, threading.Lock] = {}


def _quota_lock_key(scope: str, owner: str) -> int:
    digest = hashlib.blake2b(
        ("milkyway-quota\0" + scope + "\0" + owner).encode("utf-8"),
        digest_size=8,
    ).digest()
    return int.from_bytes(digest, "big", signed=True)


@contextmanager
def quota_allocation(session, scope: str, owner: str):
    """Serialize one quota decision through commit/rollback.

    PostgreSQL's transaction advisory lock spans all app replicas. The keyed
    process lock exists only for the explicitly non-production SQLite mode.
    """

    key = _quota_lock_key(scope, owner)
    if session.bind.dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
        yield
        return
    with _local_quota_locks_guard:
        lock = _local_quota_locks.setdefault(key, threading.Lock())
    with lock:
        yield


def acquire_transaction_lock(session, scope: str, owner: str) -> None:
    """Acquire a PostgreSQL transaction lock without requiring row UPDATE rights."""

    if session.bind.dialect.name == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": _quota_lock_key(scope, owner)},
        )


def initialize_database() -> None:
    Base.metadata.create_all(engine)
    if settings.personal_local_mode and not settings.production:
        from .research_models import ResearchBase
        ResearchBase.metadata.create_all(engine)
    _secure_sqlite_files()
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))


def verify_database_schema() -> None:
    """Fail closed in production instead of granting runtime schema DDL."""

    inspector = inspect(engine)
    missing = sorted(set(Base.metadata.tables) - set(inspector.get_table_names()))
    if missing:
        raise RuntimeError(
            "database migration is incomplete; missing tables: {}".format(
                ", ".join(missing)
            )
        )
    if settings.authority_enabled:
        if engine.dialect.name != "postgresql":
            raise RuntimeError("Authority isolation requires PostgreSQL")
        protected = {"users", "strategies", "backtest_jobs", "paper_accounts", "paper_positions", "paper_fills",
                     "equity_points", "market_data_connections", "member_quotes", "runtime_heartbeats", "leases", "work_cursors"}
        with engine.connect() as connection:
            role = connection.execute(text("SELECT rolname,rolsuper,rolbypassrls,rolcreaterole FROM pg_roles WHERE rolname=current_user")).one()
            if role[0] not in {"milkyway_app", "milkyway_paper", "milkyway_backtest", "milkyway_scheduler", "milkyway_authority"} or any(role[1:]):
                raise RuntimeError("Runtime database identity has excessive privileges")
            if connection.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_auth_members WHERE member=current_user::regrole)")):
                raise RuntimeError("Runtime database identity must not assume another role")
            rows = connection.execute(text("SELECT c.relname,c.relrowsecurity,r.rolname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='public'"))
            observed = {name for name, enabled, owner in rows if enabled and owner not in {"milkyway_app", "milkyway_paper", "milkyway_backtest", "milkyway_scheduler", "milkyway_authority"}}
            if not protected <= observed:
                raise RuntimeError("Required row security migration is incomplete")
            functions = set(connection.scalars(text("SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='milkyway_private' AND p.prosecdef AND 'search_path=pg_catalog, public'=ANY(p.proconfig)")))
            if not {"member_id", "principal", "current_claim", "enforce_admission"} <= functions:
                raise RuntimeError("Required authority functions are missing or unsafe")
            if role[0] != "milkyway_authority" and connection.scalar(text("SELECT has_table_privilege(current_user,'public.authority_sessions','INSERT') OR has_table_privilege(current_user,'public.work_claims','INSERT') OR has_any_column_privilege(current_user,'public.invitations','UPDATE')")):
                raise RuntimeError("Runtime database identity can mint authority records")


def prepare_runtime_database() -> None:
    if settings.production:
        verify_database_schema()
    else:
        initialize_database()


def apply_runtime_grants() -> None:
    """Apply least-privilege grants after an offline schema migration."""

    if engine.dialect.name != "postgresql":
        return
    grant_path = Path(__file__).resolve().parents[1] / "deploy/postgres/runtime-roles.sql"
    source = grant_path.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.exec_driver_sql(source)
        if settings.authority_enabled:
            connection.exec_driver_sql(grant_path.with_name("runtime-security.sql").read_text(encoding="utf-8"))
            for name in ("max_strategies_per_user", "max_accounts_per_user", "max_backtests_per_user_day",
                         "max_outstanding_backtests_per_user", "max_outstanding_backtests_total", "max_backtest_result_bytes"):
                connection.execute(text("UPDATE milkyway_private.limits SET value=:value WHERE name=:name"),
                                   {"name": name, "value": getattr(settings, name)})


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
