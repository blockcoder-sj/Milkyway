"""Relational state for users, jobs and idempotent paper fills."""

from __future__ import annotations

import datetime as dt
import os
import uuid
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

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
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    encrypted_api_secret: Mapped[str] = mapped_column(Text)
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


class BacktestJob(Base):
    __tablename__ = "backtest_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"), index=True)
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


class PaperAccount(Base):
    __tablename__ = "paper_accounts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    initial_cash: Mapped[float] = mapped_column(Float)
    cash: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    last_rebalanced_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    strategy: Mapped[Strategy] = relationship()


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

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
        _secure_sqlite_files()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def initialize_database() -> None:
    Base.metadata.create_all(engine)
    _secure_sqlite_files()
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))


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
