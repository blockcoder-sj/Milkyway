"""Select finite work from database state and the certified dataset on the broker."""

import datetime as dt
import json
import secrets

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, func, select, update
from terminal_events import effective_verified_events, load_events

from .authority import _aware, consume_budget, token_hash
from .database import (
    AdmittedTicker, BacktestJob, MarketDataConnection, PaperAccount, PaperPosition,
    User, WorkClaim, WorkCursor, WorkResource, quota_allocation, utcnow,
)
from .paper import regular_market_open
from .strategies import StrategySpec, get_dataset_bundle, latest_candidates


def credential_version(row):
    return "" if row is None else ":".join((row.provider, row.environment, _aware(row.updated_at).isoformat()))


def _next_resource(session, service, candidates):
    name = "authority-" + service
    cursor = session.get(WorkCursor, name)
    after = cursor.cursor_key if cursor else ""
    candidate = next((item for item in candidates if item.user_id + item.id > after), candidates[0])
    if cursor is None:
        cursor = WorkCursor(name=name, position=0)
        session.add(cursor)
    cursor.cursor_key = candidate.user_id + candidate.id
    return candidate


def issue_work(session, settings, service: str):
    if service not in {"paper", "backtest"}:
        raise HTTPException(403, "허용되지 않은 작업입니다")
    now = utcnow()
    with quota_allocation(session, "authority-work", service):
        # Completed/expired claims cannot be revived; retain the current slot.
        session.execute(delete(WorkClaim).where(WorkClaim.expires_at < now - dt.timedelta(hours=1)))
        active = int(session.scalar(select(func.count()).select_from(WorkClaim).where(
            WorkClaim.service == service, WorkClaim.expires_at > now, WorkClaim.completed_at.is_(None),
        )) or 0)
        if active >= (settings.quote_max_concurrent_requests if service == "paper" else 1):
            session.commit()
            return None
        if service == "paper":
            market_open = regular_market_open(now)
            slot = int(now.timestamp()) // max(20, settings.quote_interval_seconds)
            recent = select(WorkClaim.user_id).where(WorkClaim.service == service, WorkClaim.slot == slot)
            running = select(WorkClaim.user_id).where(WorkClaim.service == service, WorkClaim.expires_at > now, WorkClaim.completed_at.is_(None))
            rows = session.scalars(select(PaperAccount).join(User, User.id == PaperAccount.user_id)
                .where(User.active, PaperAccount.status.in_(("active", "review_required")), PaperAccount.user_id.not_in(recent), PaperAccount.user_id.not_in(running))
                .order_by(PaperAccount.user_id, PaperAccount.id).limit(settings.max_users * settings.max_accounts_per_user)).all()
        else:
            from .worker import _prune_backtest_results
            for owner_id in session.scalars(select(BacktestJob.user_id).distinct().limit(settings.max_users)).all():
                _prune_backtest_results(session, owner_id, settings)
            session.execute(update(BacktestJob).where(BacktestJob.status == "running", BacktestJob.started_at < now - dt.timedelta(seconds=settings.backtest_timeout_seconds + 30))
                .values(status="failed", error="Backtest exceeded its execution deadline", finished_at=now))
            rows = session.scalars(select(BacktestJob).join(User, User.id == BacktestJob.user_id)
                .where(User.active, BacktestJob.status == "queued").order_by(BacktestJob.user_id, BacktestJob.created_at, BacktestJob.id)
                .limit(settings.max_outstanding_backtests_total)).all()
            slot = 0  # Jobs are issued exactly once; failed jobs require a new job.
        if not rows:
            session.commit()
            return None
        row = _next_resource(session, service, rows)
        tickers, version = [], ""
        resources = []
        if service == "paper":
            connection = session.get(MarketDataConnection, row.user_id)
            version = credential_version(connection)
            quote_required = False
            verified_events = effective_verified_events(load_events(settings.terminal_events_path), through=now.date().isoformat())
            for account in (item for item in rows if item.user_id == row.user_id):
                approved = set(session.scalars(select(AdmittedTicker.ticker).where(AdmittedTicker.account_id == account.id)).all())
                holdings = set(session.scalars(select(PaperPosition.ticker).where(PaperPosition.account_id == account.id)).all())
                if holdings - approved:
                    # Legacy holdings need an operator's validated migration evidence.
                    account.status = "configuration_required"
                    continue
                # Only verified, promoted corporate actions may extend a
                # holding's symbol grant, including successor chains.
                settlement_symbols = set(holdings)
                for event in verified_events:
                    if event["ticker"] in settlement_symbols and event.get("successor_symbol"):
                        settlement_symbols.add(event["successor_symbol"])
                try:
                    spec = StrategySpec.model_validate_json(account.strategy.spec_json)
                except ValidationError:
                    # A runtime writer can insert malformed own strategy JSON.
                    # Quarantine that account and commit the fairness cursor.
                    account.status = "configuration_required"
                    continue
                needs_quotes = bool(market_open and connection and account.status == "active")
                candidates = latest_candidates(spec, get_dataset_bundle(settings)) if needs_quotes else []
                admitted = sorted(settlement_symbols | set(candidates))
                if len(set(tickers) | set(admitted)) > settings.shared_quote_batch_size:
                    account.status = "configuration_required"
                    continue
                quote_required = quote_required or needs_quotes
                resources.append((account, admitted))
                tickers.extend(admitted)
                for ticker in admitted:
                    if ticker not in approved:
                        session.add(AdmittedTicker(account_id=account.id, ticker=ticker))
                session.execute(delete(AdmittedTicker).where(AdmittedTicker.account_id == account.id, AdmittedTicker.ticker.not_in(admitted)))
            if not resources:
                session.commit()
                return None
            row = resources[0][0]
            tickers = sorted(set(tickers))
            lifetime = settings.quote_deadline_seconds + settings.shared_quote_tick_deadline_seconds + 10
        else:
            lifetime = settings.backtest_timeout_seconds + 30
            row.status, row.progress, row.worker_id, row.started_at = "running", 5, "authority", now
        raw = secrets.token_urlsafe(32)
        session.add(WorkClaim(token_hash=token_hash(raw), service=service, user_id=row.user_id,
            resource_id=row.id, strategy_id=row.strategy_id, tickers_json=json.dumps(tickers),
            quotes_consumed_at=now if service == "paper" and not quote_required else None,
            credential_version=version, slot=slot, expires_at=now + dt.timedelta(seconds=lifetime)))
        session.flush()
        for account, admitted in resources:
            session.add(WorkResource(claim_hash=token_hash(raw), resource_id=account.id,
                                    strategy_id=account.strategy_id, tickers_json=json.dumps(admitted)))
        session.commit()
        return {"claim": raw, "resource_id": row.id, "expires_at": (now + dt.timedelta(seconds=lifetime)).isoformat(),
                **({"quotes_required": quote_required} if service == "paper" else {})}


def claim_record(session, raw: str, service: str):
    claim = session.scalar(select(WorkClaim).where(WorkClaim.token_hash == token_hash(raw)).with_for_update())
    user = session.get(User, claim.user_id) if claim else None
    if (claim is None or claim.service != service or claim.completed_at is not None
            or _aware(claim.expires_at) <= utcnow() or user is None or not user.active):
        raise HTTPException(403, "작업 권한이 없거나 만료되었습니다")
    return claim


def complete_work(session, raw: str, service: str):
    with quota_allocation(session, "claim", token_hash(raw)):
        claim = claim_record(session, raw, service)
        claim.completed_at = utcnow()
        session.commit()


def consume_quote_work(session, settings, raw: str):
    with quota_allocation(session, "claim", token_hash(raw)):
        claim = claim_record(session, raw, "paper")
        connection = session.get(MarketDataConnection, claim.user_id)
        if (claim.quotes_consumed_at is not None or connection is None
                or credential_version(connection) != claim.credential_version):
            raise HTTPException(403, "시세 요청 권한이 없거나 연결이 변경되었습니다")
        consume_budget(session, settings, "quotes-member", claim.user_id, 4, 60, commit=False)
        consume_budget(session, settings, "quotes-global", "all", settings.max_users * 4, 60, commit=False)
        claim.quotes_consumed_at = utcnow()
        session.commit()
        return claim
