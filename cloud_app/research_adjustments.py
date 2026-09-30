"""Local edits produce immutable research versions without invoking AI."""

import json
from fastapi import HTTPException
from sqlalchemy import select

from .database import Strategy, quota_allocation
from .research_models import ResearchAdjustment, ResearchVersion
from .research_store import owned_session, expire_interrupted, require_idle, versions, session_payload
from .strategies import StrategySpec


def adjust_version(services, db, user, session_id, strategy_id, body):
    room = owned_session(db, user, session_id)
    expire_interrupted(db, room)
    encoded = json.dumps(body.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    with quota_allocation(db, "research", user.id):
        existing = db.scalar(select(ResearchAdjustment).where(
            ResearchAdjustment.session_id == room.id, ResearchAdjustment.request_id == body.request_id))
        if existing:
            if existing.base_strategy_id != strategy_id or existing.request_json != encoded:
                raise HTTPException(409, "같은 조정 요청 ID에 다른 설정을 사용할 수 없습니다")
            return session_payload(db, room, services.strategy_payload)
        require_idle(db, room)
        db.refresh(room)
        version_rows = versions(db, room)
        if strategy_id not in {row.strategy_id for row in version_rows}:
            raise HTTPException(404, "이 대화의 전략 버전이 아닙니다")
        if room.selected_strategy_id != strategy_id:
            raise HTTPException(409, "대화의 기준 전략이 변경됐습니다. 최신 버전을 확인하세요")
        base = db.scalar(select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user.id))
        if base is None:
            raise HTTPException(404, "전략 버전을 찾을 수 없습니다")
        original = StrategySpec.model_validate_json(base.spec_json)
        values = original.model_dump(mode="json")
        values.update(portfolio=body.portfolio.model_dump(mode="json"),
                      filters=body.filters.model_dump(mode="json"),
                      factors=[factor.model_dump(mode="json") for factor in body.factors])
        try:
            spec = StrategySpec.model_validate(values)
        except ValueError:
            raise HTTPException(422, "조정한 전략 설정을 확인하세요") from None
        if spec == original:
            raise HTTPException(422, "설정을 변경한 뒤 새 버전으로 저장하세요")
        with services.strategy_creation(db, user, spec, "대화 전략의 운용 설정 직접 조정") as strategy:
            db.add(ResearchVersion(session_id=room.id, strategy_id=strategy.id,
                                   parent_strategy_id=strategy_id, number=len(version_rows) + 1))
            db.add(ResearchAdjustment(session_id=room.id, request_id=body.request_id,
                                     request_json=encoded, base_strategy_id=strategy_id, strategy_id=strategy.id))
            room.selected_strategy_id = strategy.id
    return session_payload(db, room, services.strategy_payload)
