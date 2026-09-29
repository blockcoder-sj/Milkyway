"""Personal research tables, deliberately outside the cloud schema metadata."""
from __future__ import annotations

import datetime as dt
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from .database import new_id, utcnow


class ResearchBase(DeclarativeBase):
    pass


class ResearchSession(ResearchBase):
    __tablename__ = "research_sessions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(100))
    objective: Mapped[str] = mapped_column(Text, default="")
    selected_strategy_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ResearchTurn(ResearchBase):
    __tablename__ = "research_turns"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    request_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="awaiting_approval")
    prompt: Mapped[str] = mapped_column(Text)
    request_json: Mapped[str] = mapped_column(Text)
    request_digest: Mapped[str] = mapped_column(String(64))
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    strategy_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    base_strategy_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("session_id", "request_id"),)


class ResearchVersion(ResearchBase):
    __tablename__ = "research_versions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    strategy_id: Mapped[str] = mapped_column(String(32), unique=True)
    parent_strategy_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("session_id", "number"),)


class ResearchExperiment(ResearchBase):
    __tablename__ = "research_experiments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    request_id: Mapped[str] = mapped_column(String(64))
    request_json: Mapped[str] = mapped_column(Text)
    objective: Mapped[str] = mapped_column(String(30))
    start_date: Mapped[dt.date] = mapped_column(Date)
    split_date: Mapped[dt.date] = mapped_column(Date)
    end_date: Mapped[dt.date] = mapped_column(Date)
    generation: Mapped[str] = mapped_column(String(32))
    fingerprint: Mapped[str] = mapped_column(String(64))
    terminal_events: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("session_id", "request_id"),)


class ResearchRun(ResearchBase):
    __tablename__ = "research_runs"
    job_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("research_experiments.id"), index=True)
    strategy_id: Mapped[str] = mapped_column(String(32))
    segment: Mapped[str] = mapped_column(String(20))
    __table_args__ = (UniqueConstraint("experiment_id", "strategy_id", "segment"),)


class ResearchDeployment(ResearchBase):
    __tablename__ = "research_deployments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    strategy_id: Mapped[str] = mapped_column(String(32))
    account_id: Mapped[str] = mapped_column(String(32), unique=True)
    request_id: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("session_id", "request_id"),)
