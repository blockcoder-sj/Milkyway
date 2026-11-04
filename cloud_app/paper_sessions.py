"""Durable date limits for personal paper accounts, without provider calls."""
from __future__ import annotations

import datetime as dt
import json
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from market_calendar import get_market_hours, is_trading_day
from .database import EquityPoint, PaperAccount, PaperFill, PaperPosition
from .research_models import PersonalPaperSession


def as_utc(value):
    return value.replace(tzinfo=dt.timezone.utc) if value.tzinfo is None else value.astimezone(dt.timezone.utc)


def period_bounds(days: int, now: dt.datetime):
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 30:
        raise ValueError("운용 기간은 1~30일입니다")
    opens = as_utc(now)
    return opens.astimezone(ZoneInfo("America/New_York")).date(), (opens, opens + dt.timedelta(days=days))


def session_bounds(day: dt.date, now: dt.datetime):
    """Reject expired/non-trading dates; calendar includes DST and early closes."""
    eastern = ZoneInfo("America/New_York")
    today = as_utc(now).astimezone(eastern).date()
    if day < today or day > today + dt.timedelta(days=7) or not is_trading_day(day):
        raise ValueError("오늘부터 7일 이내의 미국 거래일을 선택하세요")
    hours = get_market_hours(day)
    if not hours:
        raise ValueError("해당 날짜의 미국 거래시간을 확인할 수 없습니다")
    opens = dt.datetime.combine(day, dt.time(hours[0], hours[1]), eastern).astimezone(dt.timezone.utc)
    closes = dt.datetime.combine(day, dt.time(hours[2], hours[3]), eastern).astimezone(dt.timezone.utc)
    if as_utc(now) >= closes:
        raise ValueError("이미 마감된 거래일에는 페이퍼 운용을 시작할 수 없습니다")
    return opens, closes


def finish_session(session, account, run, now):
    if run.completed_at is not None:
        return
    # No synthetic closing fill or closing-price observation. A restart after a
    # missed session records zero fills, and never resumes on the following day.
    positions = session.scalars(select(PaperPosition).where(PaperPosition.account_id == account.id)).all()
    point = session.scalar(select(EquityPoint).where(EquityPoint.account_id == account.id)
                           .order_by(EquityPoint.observed_at.desc()).limit(1))
    fills = session.scalar(select(func.count()).select_from(PaperFill).where(PaperFill.account_id == account.id))
    equity = account.cash + sum(p.shares * p.last_price for p in positions)
    run.summary_json = json.dumps({"cash": account.cash, "last_known_equity": equity,
        "return_pct": (equity / account.initial_cash - 1) * 100,
        "last_complete_valuation_at": as_utc(point.observed_at).isoformat() if point else None,
        "last_complete_valuation": point.equity if point else None,
        "fill_count": fills, "closing_price_verified": False,
        "positions": [{"ticker": p.ticker, "shares": p.shares, "last_price": p.last_price} for p in positions]})
    run.completed_at = as_utc(now)
    if account.status == "active":
        account.status = "paused"
    session.flush()


def expire_sessions(session, now):
    rows = session.execute(select(PersonalPaperSession, PaperAccount)
        .join(PaperAccount, PersonalPaperSession.account_id == PaperAccount.id)
        .where(PersonalPaperSession.completed_at.is_(None), PersonalPaperSession.closes_at <= as_utc(now))).all()
    for run, account in rows:
        finish_session(session, account, run, now)
    return len(rows)


def session_allows_execution(session, account, now):
    run = session.get(PersonalPaperSession, account.id)
    if run is None:
        return True
    if as_utc(now) >= as_utc(run.closes_at):
        finish_session(session, account, run, now)
        return False
    return run.completed_at is None and as_utc(run.opens_at) <= as_utc(now) < as_utc(run.closes_at)


def session_payload(session, account, now):
    run = session.get(PersonalPaperSession, account.id)
    if run is None:
        return None
    period = as_utc(run.closes_at) - as_utc(run.opens_at) >= dt.timedelta(days=1)
    return {"mode": "period" if period else "day", "duration_days": int((as_utc(run.closes_at)-as_utc(run.opens_at)).total_seconds()/86400) if period else None,
        "session_date": run.session_date.isoformat(), "opens_at": as_utc(run.opens_at).isoformat(),
        "closes_at": as_utc(run.closes_at).isoformat(), "expired": as_utc(now) >= as_utc(run.closes_at),
        "completed_at": as_utc(run.completed_at).isoformat() if run.completed_at else None,
        "summary": json.loads(run.summary_json) if run.summary_json else None}
