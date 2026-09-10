"""Shared quote collection and idempotent per-user paper ledgers."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from market_calendar import get_market_hours, is_trading_day, prev_trading_day
from terminal_events import effective_verified_events, load_events, unresolved_events

from .config import Settings, get_settings
from .database import (
    EquityPoint,
    MarketDataConnection,
    MemberQuote,
    PaperAccount,
    PaperFill,
    PaperPosition,
    Quote,
    utcnow,
)
from .strategies import StrategySpec, get_dataset_bundle, latest_candidates


logger = logging.getLogger("cloud_app.paper")


@dataclass(frozen=True)
class QuoteValue:
    ticker: str
    price: float
    bid: float
    ask: float
    volume: float
    source: str
    observed_at: dt.datetime


def _round_robin_unique(groups: dict[str, Iterable[str]]) -> tuple[str, ...]:
    queues = {
        owner: list(dict.fromkeys(str(value) for value in values))
        for owner, values in sorted(groups.items())
    }
    result: list[str] = []
    seen: set[str] = set()
    offset = 0
    while True:
        added = False
        for owner in sorted(queues):
            values = queues[owner]
            if offset >= len(values):
                continue
            value = values[offset]
            if value not in seen:
                seen.add(value)
                result.append(value)
            added = True
        if not added:
            return tuple(result)
        offset += 1


class QuoteProvider:
    def fetch(self, tickers: Iterable[str]) -> list[QuoteValue]:
        raise NotImplementedError


class DatasetQuoteProvider(QuoteProvider):
    """Development provider using the last completed daily close."""

    def fetch(self, tickers: Iterable[str]) -> list[QuoteValue]:
        bundle = get_dataset_bundle()
        now = utcnow()
        result = []
        for ticker in sorted(set(tickers)):
            if ticker not in bundle.panels["Close"]:
                continue
            series = bundle.panels["Close"][ticker].dropna()
            if series.empty:
                continue
            result.append(
                QuoteValue(ticker, float(series.iloc[-1]), 0.0, 0.0, 0.0, "dataset_close", now)
            )
        return result


class KisQuoteProvider(QuoteProvider):
    def __init__(self, credentials=None, *, source: str = "kis"):
        from .kis_quotes import KisCredentials, KisQuoteClient

        credentials = credentials or KisCredentials(
            api_key=os.getenv("BROKER_API_KEY", ""),
            api_secret=os.getenv("BROKER_API_SECRET", ""),
            account_id=os.getenv("BROKER_ACCOUNT_ID", ""),
            paper=True,
        )
        self.broker = KisQuoteClient(credentials)
        self.source = source
        if not self.broker.connect():
            raise RuntimeError("KIS quote provider connection failed")

    def fetch(self, tickers: Iterable[str]) -> list[QuoteValue]:
        result = []
        for ticker in sorted(set(tickers)):
            raw = self.broker.get_quote(ticker)
            now = utcnow()
            price = float(raw.get("price", 0) or 0)
            if price > 0:
                result.append(
                    QuoteValue(
                        ticker=ticker,
                        price=price,
                        bid=float(raw.get("bid", 0) or 0),
                        ask=float(raw.get("ask", 0) or 0),
                        volume=float(raw.get("volume", 0) or 0),
                        source=self.source,
                        observed_at=now,
                    )
                )
            # Stay comfortably below the documented per-second request cap.
            time.sleep(0.08)
        return result


class TossQuoteProvider(QuoteProvider):
    """Member-owned Toss feed using its 200-symbol batch current-price API."""

    def __init__(self, credentials, *, source: str = "toss_member"):
        from .toss_quotes import TossQuoteClient

        self.broker = TossQuoteClient(credentials)
        self.source = source
        self.broker.authenticate()

    def fetch(self, tickers: Iterable[str]) -> list[QuoteValue]:
        return [
            QuoteValue(
                ticker=raw["ticker"],
                price=float(raw["price"]),
                bid=float(raw.get("bid", 0) or 0),
                ask=float(raw.get("ask", 0) or 0),
                volume=float(raw.get("volume", 0) or 0),
                source=self.source,
                observed_at=raw["observed_at"],
            )
            for raw in self.broker.get_prices(tickers)
        ]


def make_quote_provider(settings: Settings | None = None) -> QuoteProvider:
    settings = settings or get_settings()
    if settings.quote_provider == "kis":
        if not settings.market_data_sharing_allowed:
            raise RuntimeError("market data sharing has not been explicitly enabled")
        return KisQuoteProvider()
    return DatasetQuoteProvider()


def _spec(account: PaperAccount) -> StrategySpec:
    return StrategySpec.model_validate_json(account.strategy.spec_json)


def collect_watchlist_ordered(session: Session, user_id: str | None = None) -> tuple[str, ...]:
    """Return held symbols first, then baselines and rebalance candidates."""

    account_statement = select(PaperAccount).where(PaperAccount.status == "active")
    if user_id is not None:
        account_statement = account_statement.where(PaperAccount.user_id == user_id)
    accounts = session.scalars(account_statement).all()
    tickers: list[str] = []
    seen: set[str] = set()

    def append(values) -> None:
        for value in values:
            ticker = str(value)
            if ticker not in seen:
                seen.add(ticker)
                tickers.append(ticker)

    append(collect_holding_watchlist_ordered(session, user_id=user_id))
    if user_id is None:
        append(("SPY", "QQQ", "IWM", "VIXY"))
    if not accounts:
        return tuple(tickers)
    et_now, _market_open, rebalance_window = _market_context()
    due_accounts = [
        account
        for account in accounts
        if rebalance_window
        and (
            account.last_rebalanced_on is None
            or (et_now.date() - account.last_rebalanced_on).days
            >= _spec(account).portfolio.rebalance_days
        )
    ]
    if not due_accounts:
        return tuple(tickers)
    bundle = get_dataset_bundle()
    strategy_candidates: dict[str, list[str]] = {}
    candidates_by_user: dict[str, list[str]] = {}
    for account in due_accounts:
        if account.strategy_id not in strategy_candidates:
            strategy_candidates[account.strategy_id] = latest_candidates(_spec(account), bundle)
        candidates_by_user.setdefault(account.user_id, []).extend(
            strategy_candidates[account.strategy_id]
        )
    append(_round_robin_unique(candidates_by_user))
    return tuple(tickers)


def collect_holding_watchlist_ordered(
    session: Session, user_id: str | None = None
) -> tuple[str, ...]:
    """Return a tenant-fair, de-duplicated list of active holdings."""

    position_statement = (
        select(PaperPosition.ticker, PaperAccount.user_id)
        .join(PaperAccount)
        .where(PaperAccount.status == "active")
    )
    if user_id is not None:
        position_statement = position_statement.where(PaperAccount.user_id == user_id)
    position_rows = session.execute(position_statement).all()
    holdings_by_user: dict[str, list[str]] = {}
    for ticker, owner_id in position_rows:
        holdings_by_user.setdefault(str(owner_id), []).append(str(ticker))
    return _round_robin_unique(
        {owner: sorted(values) for owner, values in holdings_by_user.items()}
    )


def collect_watchlist(session: Session, user_id: str | None = None) -> set[str]:
    return set(collect_watchlist_ordered(session, user_id=user_id))


def apply_terminal_events(session: Session, settings: Settings | None = None) -> dict:
    """Settle verified actions and freeze unresolved exchange exits."""
    settings = settings or get_settings()
    if not settings.terminal_events_path.exists():
        return {"settled": 0, "review_accounts": 0}
    events = load_events(settings.terminal_events_path)
    through = utcnow().date().isoformat()
    unresolved = {event["ticker"]: event for event in unresolved_events(events, through=through)}
    verified = effective_verified_events(events, through=through)
    accounts = session.scalars(
        select(PaperAccount).where(PaperAccount.status.in_(["active", "review_required"]))
    ).all()
    settled = 0
    review_accounts = 0
    for account in accounts:
        positions = _account_positions(session, account.id)
        blocked = set(positions) & set(unresolved)
        if blocked:
            account.status = "review_required"
            review_accounts += 1
            continue
        if account.status == "review_required":
            # Capacity may have changed while the account was frozen. Move it
            # to paused so the normal app activation path re-runs admission.
            account.status = "paused"
        for event in verified:
            ticker = event["ticker"]
            position = positions.get(ticker)
            if position is None:
                continue
            key = "{}:corporate-action:{}".format(account.id, event["event_id"])
            if session.scalar(select(PaperFill.id).where(PaperFill.dedupe_key == key)):
                continue
            old_shares = float(position.shares)
            cash_per_share = float(event.get("cash_per_share") or 0.0)
            account.cash += old_shares * cash_per_share
            successor = event.get("successor_symbol")
            ratio = float(event.get("share_ratio") or 0.0)
            if successor and ratio > 0:
                successor_position = positions.get(successor)
                successor_shares = old_shares * ratio
                adjusted_basis = max(0.0, position.avg_price - cash_per_share) / ratio
                if successor_position is None:
                    successor_position = PaperPosition(
                        account_id=account.id,
                        ticker=successor,
                        shares=successor_shares,
                        avg_price=adjusted_basis,
                        last_price=adjusted_basis,
                    )
                    session.add(successor_position)
                    positions[successor] = successor_position
                else:
                    total_basis = (
                        successor_position.avg_price * successor_position.shares
                        + adjusted_basis * successor_shares
                    )
                    successor_position.shares += successor_shares
                    successor_position.avg_price = total_basis / successor_position.shares
            session.delete(position)
            positions.pop(ticker, None)
            session.add(
                PaperFill(
                    account_id=account.id,
                    ticker=ticker,
                    side="ACTION",
                    shares=old_shares,
                    price=cash_per_share,
                    fee=0.0,
                    reason="corporate_action",
                    dedupe_key=key,
                )
            )
            # Production disables autoflush. Successor chains and the next
            # ledger phase must see these changes in this same transaction.
            session.flush()
            settled += 1
    # Status-only freezes/recoveries must affect the next phase's SQL filters.
    session.flush()
    return {"settled": settled, "review_accounts": review_accounts}


def store_quotes(session: Session, values: Iterable[QuoteValue]) -> int:
    count = 0
    for value in values:
        row = session.get(Quote, value.ticker)
        if row is None:
            row = Quote(ticker=value.ticker)
            session.add(row)
        row.price = value.price
        row.bid = value.bid
        row.ask = value.ask
        row.volume = value.volume
        row.source = value.source
        row.observed_at = value.observed_at
        count += 1
    return count


def store_member_quotes(session: Session, user_id: str, values: Iterable[QuoteValue]) -> int:
    count = 0
    for value in values:
        row = session.get(MemberQuote, (user_id, value.ticker))
        if row is None:
            row = MemberQuote(user_id=user_id, ticker=value.ticker)
            session.add(row)
        row.price = value.price
        row.bid = value.bid
        row.ask = value.ask
        row.volume = value.volume
        row.source = value.source
        row.observed_at = value.observed_at
        count += 1
    return count


def quote_map(
    session: Session,
    tickers: Iterable[str],
    max_age_seconds: int | None = None,
    *,
    user_id: str | None = None,
) -> dict[str, float]:
    wanted = sorted(set(tickers))
    if not wanted:
        return {}
    settings = get_settings()
    if max_age_seconds is None:
        max_age_seconds = int(getattr(settings, "quote_max_age_seconds", 180))
    cutoff = utcnow() - dt.timedelta(seconds=max_age_seconds)
    if (
        settings.member_credentials_enabled
        and user_id is not None
    ):
        if session.get(MarketDataConnection, user_id) is None:
            return {}
        rows = session.scalars(
            select(MemberQuote).where(
                MemberQuote.user_id == user_id,
                MemberQuote.ticker.in_(wanted),
                MemberQuote.observed_at >= cutoff,
            )
        ).all()
    else:
        rows = session.scalars(
            select(Quote).where(Quote.ticker.in_(wanted), Quote.observed_at >= cutoff)
        ).all()
    return {row.ticker: float(row.price) for row in rows if row.price > 0}


def _fill(
    session: Session,
    account: PaperAccount,
    ticker: str,
    side: str,
    shares: float,
    price: float,
    fee_rate: float,
    reason: str,
    dedupe_key: str,
) -> bool:
    if shares <= 1e-9 or price <= 0:
        return False
    if session.scalar(select(PaperFill.id).where(PaperFill.dedupe_key == dedupe_key)):
        return False
    position = session.scalar(
        select(PaperPosition).where(
            PaperPosition.account_id == account.id, PaperPosition.ticker == ticker
        )
    )
    value = shares * price
    fee = value * fee_rate
    if side == "SELL":
        if position is None:
            return False
        shares = min(shares, position.shares)
        value = shares * price
        fee = value * fee_rate
        account.cash += value - fee
        position.shares -= shares
        position.last_price = price
        if position.shares <= 1e-9:
            session.delete(position)
    elif side == "BUY":
        affordable = max(0.0, account.cash / (price * (1 + fee_rate)))
        shares = min(shares, affordable)
        if shares <= 1e-9:
            return False
        value = shares * price
        fee = value * fee_rate
        account.cash -= value + fee
        if position is None:
            position = PaperPosition(
                account_id=account.id,
                ticker=ticker,
                shares=0.0,
                avg_price=0.0,
                last_price=price,
            )
            session.add(position)
        total_cost = position.avg_price * position.shares + value
        position.shares += shares
        position.avg_price = total_cost / position.shares
        position.last_price = price
    else:
        raise ValueError("side must be BUY or SELL")
    session.add(
        PaperFill(
            account_id=account.id,
            ticker=ticker,
            side=side,
            shares=shares,
            price=price,
            fee=fee,
            reason=reason,
            dedupe_key=dedupe_key,
        )
    )
    # Subsequent fills, stops and equity queries share this transaction while
    # SessionLocal has autoflush=False. Publish inserts/deletes before them.
    session.flush()
    return True


def _account_positions(session: Session, account_id: str) -> dict[str, PaperPosition]:
    rows = session.scalars(
        select(PaperPosition).where(PaperPosition.account_id == account_id)
    ).all()
    return {row.ticker: row for row in rows}


def mark_and_stop_accounts(session: Session) -> int:
    accounts = session.scalars(select(PaperAccount).where(PaperAccount.status == "active")).all()
    fills = 0
    now = utcnow()
    for account in accounts:
        spec = _spec(account)
        positions = _account_positions(session, account.id)
        prices = quote_map(session, positions, user_id=account.user_id)
        for ticker, position in positions.items():
            price = prices.get(ticker)
            if price is None:
                continue
            position.last_price = price
            stop = spec.portfolio.stop_loss_pct
            if stop is not None and price <= position.avg_price * (1 + stop):
                key = "{}:{}:stop:{}".format(account.id, now.date().isoformat(), ticker)
                fills += int(
                    _fill(
                        session,
                        account,
                        ticker,
                        "SELL",
                        position.shares,
                        price,
                        spec.portfolio.cost_per_side,
                        "stop_loss",
                        key,
                    )
                )
        current_positions = _account_positions(session, account.id)
        equity = account.cash + sum(item.shares * item.last_price for item in current_positions.values())
        latest_point = session.scalar(
            select(EquityPoint)
            .where(EquityPoint.account_id == account.id)
            .order_by(EquityPoint.observed_at.desc())
            .limit(1)
        )
        latest_at = latest_point.observed_at if latest_point else None
        if latest_at is None or _as_utc(latest_at) <= now - dt.timedelta(minutes=5):
            session.add(EquityPoint(account_id=account.id, equity=equity, cash=account.cash, observed_at=now))
    return fills


def _as_utc(value: dt.datetime) -> dt.datetime:
    return value.replace(tzinfo=dt.timezone.utc) if value.tzinfo is None else value.astimezone(dt.timezone.utc)


def _market_context(now: dt.datetime | None = None) -> tuple[dt.datetime, bool, bool]:
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from pytz import timezone as ZoneInfo
    et_now = (now or utcnow()).astimezone(ZoneInfo("America/New_York"))
    if not is_trading_day(et_now.date()):
        return et_now, False, False
    hours = get_market_hours(et_now.date())
    if not hours:
        return et_now, False, False
    open_at = et_now.replace(hour=hours[0], minute=hours[1], second=0, microsecond=0)
    close_at = et_now.replace(hour=hours[2], minute=hours[3], second=0, microsecond=0)
    market_open = open_at <= et_now <= close_at
    rebalance_window = open_at + dt.timedelta(minutes=5) <= et_now <= close_at - dt.timedelta(minutes=15)
    return et_now, market_open, rebalance_window


def regular_market_open(now: dt.datetime | None = None) -> bool:
    """Return whether NYSE regular trading is open for quote collection."""
    return _market_context(now)[1]


def rebalance_due_accounts(session: Session, force: bool = False) -> int:
    et_now, _market_open, rebalance_window = _market_context()
    if not force and not rebalance_window:
        return 0
    bundle = get_dataset_bundle()
    if not bundle.forward_data_gate_ready:
        logger.error("paper rebalance blocked: latest forward data quality gate failed")
        return 0
    required_session = prev_trading_day(et_now.date())
    dataset_session = bundle.index.max().date()
    if dataset_session < required_session:
        logger.error(
            "paper rebalance blocked: dataset last session=%s required=%s",
            dataset_session,
            required_session,
        )
        return 0
    accounts = session.scalars(select(PaperAccount).where(PaperAccount.status == "active")).all()
    fill_count = 0
    for account in accounts:
        spec = _spec(account)
        if account.last_rebalanced_on is not None:
            age = (et_now.date() - account.last_rebalanced_on).days
            if age < spec.portfolio.rebalance_days:
                continue
        targets = latest_candidates(spec, bundle)
        if not targets:
            logger.warning("no strict-PIT candidates for account %s", account.id)
            continue
        positions = _account_positions(session, account.id)
        prices = quote_map(
            session, set(targets) | set(positions), user_id=account.user_id
        )
        required_quotes = set(targets) | set(positions)
        if any(ticker not in prices for ticker in required_quotes):
            logger.warning(
                "rebalance deferred for %s: one or more target/holding quotes are missing",
                account.id,
            )
            continue
        equity = account.cash + sum(
            position.shares * prices[ticker]
            for ticker, position in positions.items()
        )
        target_value = equity / len(targets)
        date_key = et_now.date().isoformat()
        old_symbols = set(positions)
        target_symbols = set(targets)

        # Canonical engine contract: retained holdings keep their quantities.
        # Only removals are sold and only newly selected symbols are bought.
        for ticker, position in list(positions.items()):
            if ticker not in target_symbols:
                key = "{}:{}:rebalance:{}:SELL".format(account.id, date_key, ticker)
                fill_count += int(
                    _fill(session, account, ticker, "SELL", position.shares, prices[ticker],
                          spec.portfolio.cost_per_side, "rebalance", key)
                )

        new_targets = [ticker for ticker in targets if ticker not in old_symbols]
        total_desired = target_value * len(new_targets)
        if total_desired > 0:
            affordable_gross = account.cash / (1 + spec.portfolio.cost_per_side)
            scale = min(1.0, affordable_gross / total_desired)
        else:
            scale = 0.0
        for ticker in new_targets:
            price = prices[ticker]
            desired = target_value * scale / price
            if desired > 1e-7:
                key = "{}:{}:rebalance:{}:BUY".format(account.id, date_key, ticker)
                fill_count += int(
                    _fill(session, account, ticker, "BUY", desired, price,
                          spec.portfolio.cost_per_side, "rebalance", key)
                )
        account.last_rebalanced_on = et_now.date()
    return fill_count


def account_snapshot(session: Session, account: PaperAccount) -> dict:
    positions = _account_positions(session, account.id)
    equity = account.cash + sum(row.shares * row.last_price for row in positions.values())
    return {
        "id": account.id,
        "name": account.name,
        "strategy_id": account.strategy_id,
        "status": account.status,
        "initial_cash": account.initial_cash,
        "cash": account.cash,
        "equity": equity,
        "return_pct": (equity / account.initial_cash - 1) * 100,
        "last_rebalanced_on": account.last_rebalanced_on,
        "positions": [
            {
                "ticker": row.ticker,
                "shares": row.shares,
                "avg_price": row.avg_price,
                "last_price": row.last_price,
                "market_value": row.shares * row.last_price,
                "pnl_pct": (row.last_price / row.avg_price - 1) * 100 if row.avg_price else 0.0,
            }
            for row in sorted(positions.values(), key=lambda item: item.ticker)
        ],
    }
