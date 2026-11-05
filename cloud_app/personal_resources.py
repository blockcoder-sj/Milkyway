"""Owner-scoped local resource deletion; no brokerage/network operations.

Research version/run/deployment IDs remain as tombstones for request replay and
monotonic version numbering. Executable strategies and account ledgers are
removed, and comparisons containing a deleted strategy become invalid.
"""
import json
from contextlib import contextmanager

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Literal
from sqlalchemy import delete, select, text, update

from .database import (
    AdmittedTicker, BacktestJob, EquityPoint, PaperAccount, PaperFill,
    PaperPosition, RuntimeHeartbeat, Strategy, quota_allocation,
)
from .research_models import PersonalPaperSession, ResearchSession, ResearchTurn


class DeleteBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: Literal[True]


def require_local(settings):
    if not settings.personal_local_mode or settings.production or settings.authority_enabled:
        raise HTTPException(404, "Not found")


@contextmanager
def _deletion_transaction(db, owner):
    # Use the same app locks as research/account/strategy/queue creation. SQLite
    # also needs a write reservation before reading: the paper worker is another
    # process, so a Python lock alone cannot serialize a live ledger deletion.
    with quota_allocation(db, "research", owner), quota_allocation(db, "accounts", "global"), quota_allocation(db, "strategies", owner), quota_allocation(db, "backtests", "global"):
        db.rollback()
        if db.bind.dialect.name == "sqlite":
            db.execute(text("BEGIN IMMEDIATE"))
        try:
            yield
            db.commit()
        except BaseException:
            db.rollback()
            raise


def delete_account(db, owner, account_id):
    with _deletion_transaction(db, owner):
        account = db.scalar(select(PaperAccount).where(PaperAccount.id == account_id, PaperAccount.user_id == owner))
        if account is None:
            raise HTTPException(404, "계좌를 찾을 수 없습니다")
        # Explicit children also support legacy SQLite installations whose FK
        # enforcement was disabled. The current runtime enforces CASCADE too.
        for model in (PersonalPaperSession, AdmittedTicker, PaperPosition, PaperFill, EquityPoint):
            db.execute(delete(model).where(model.account_id == account_id))
        db.execute(delete(RuntimeHeartbeat).where(RuntimeHeartbeat.component == "paper-account:" + account_id))
        db.execute(delete(PaperAccount).where(PaperAccount.id == account_id, PaperAccount.user_id == owner))
        # Keep ResearchDeployment's request ID: replay must not recreate a
        # deliberately deleted account. Research evidence joins live accounts.


def delete_strategy(db, owner, strategy_id):
    with _deletion_transaction(db, owner):
        strategy = db.scalar(select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == owner))
        if strategy is None:
            raise HTTPException(404, "전략을 찾을 수 없습니다")
        if db.scalar(select(PaperAccount.id).where(PaperAccount.strategy_id == strategy_id).limit(1)):
            raise HTTPException(409, "이 전략에 연결된 페이퍼 계좌를 먼저 삭제하세요")
        if db.scalar(select(BacktestJob.id).where(BacktestJob.strategy_id == strategy_id, BacktestJob.status == "running").limit(1)):
            raise HTTPException(409, "백테스트 실행이 끝난 뒤 전략을 삭제하세요")
        rooms = select(ResearchSession.id).where(ResearchSession.user_id == owner)
        # Pending/running approved payloads must not silently change underneath
        # the user or restore a strategy deleted while its provider was working.
        if db.scalar(select(ResearchTurn.id).where(
            ResearchTurn.session_id.in_(rooms), ResearchTurn.status.in_(["awaiting_approval", "running"]),
        ).limit(1)):
            raise HTTPException(409, "승인 대기 요청을 취소하거나 AI 응답이 끝난 뒤 전략을 삭제하세요")
        turns = db.scalars(select(ResearchTurn).where(ResearchTurn.session_id.in_(rooms), ResearchTurn.strategy_id == strategy_id)).all()
        for turn in turns:
            if turn.response_json:
                try:
                    response = json.loads(turn.response_json)
                except (TypeError, ValueError):
                    response = None
                    turn.response_json = None
                if isinstance(response, dict):
                    response["strategy"] = None
                    turn.response_json = json.dumps(response, ensure_ascii=False)
            turn.strategy_id = None
        db.flush()
        db.execute(update(ResearchTurn).where(ResearchTurn.session_id.in_(rooms), ResearchTurn.base_strategy_id == strategy_id).values(base_strategy_id=None))
        db.execute(update(ResearchSession).where(ResearchSession.user_id == owner, ResearchSession.selected_strategy_id == strategy_id).values(selected_strategy_id=None))
        db.execute(delete(BacktestJob).where(BacktestJob.strategy_id == strategy_id, BacktestJob.user_id == owner))
        db.execute(delete(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == owner))
