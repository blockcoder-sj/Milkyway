"""Owner-scoped queries and response projections for the research service."""

import datetime as dt
import json
from fastapi import HTTPException
from sqlalchemy import select, update
from . import research_ai
from .database import BacktestJob, Strategy, utcnow
from .research_models import ResearchRun, ResearchSession, ResearchTurn, ResearchVersion
from .research_experiments import experiment_evidence


def aware(value):
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def owned_session(db, user, session_id):
    row = db.scalar(
        select(ResearchSession).where(ResearchSession.id == session_id, ResearchSession.user_id == user.id)
    )
    if row is None:
        raise HTTPException(404, "연구를 찾을 수 없습니다")
    return row


def versions(db, room):
    return db.scalars(
        select(ResearchVersion).where(ResearchVersion.session_id == room.id).order_by(ResearchVersion.number)
    ).all()


def expire_interrupted(db, room):
    db.execute(
        update(ResearchTurn)
        .where(
            ResearchTurn.session_id == room.id,
            ResearchTurn.status == "running",
            ResearchTurn.approved_at < utcnow() - dt.timedelta(seconds=research_ai.CALL_TIMEOUT + 60),
        )
        .values(
            status="failed",
            error="연결이 중단되어 완료 여부를 확인하지 못했습니다. 자동 재시도하지 않습니다",
            finished_at=utcnow(),
        )
    )
    db.execute(
        update(ResearchTurn)
        .where(
            ResearchTurn.session_id == room.id,
            ResearchTurn.status == "awaiting_approval",
            ResearchTurn.created_at < utcnow() - dt.timedelta(minutes=15),
        )
        .values(status="expired", finished_at=utcnow())
    )
    db.commit()


def require_idle(db, room):
    busy = db.scalar(
        select(ResearchTurn.id).where(
            ResearchTurn.session_id == room.id, ResearchTurn.status.in_(["awaiting_approval", "running"])
        )
    )
    if busy:
        raise HTTPException(409, "기존 요청을 승인·취소하거나 실행 완료를 기다려 주세요")


def turn_payload(row):
    request = json.loads(row.request_json)
    return {
        "id": row.id,
        "status": row.status,
        "prompt": row.prompt,
        "created_at": row.created_at,
        "response": json.loads(row.response_json) if row.response_json else None,
        "usage": json.loads(row.usage_json) if row.usage_json else None,
        "strategy_id": row.strategy_id,
        "error": row.error,
        "approval": {
            "request_digest": row.request_digest,
            "model": request["model"],
            "reasoning": request.get("reasoning", {}).get("effort", "none"),
            "max_calls": 1,
            "max_output_tokens": request["max_output_tokens"],
            "input_characters": len(request["instructions"]) + len(request["input"]),
            "expires_at": aware(row.created_at) + dt.timedelta(minutes=15),
            "request": request if row.status == "awaiting_approval" else None,
        },
    }


def evidence_context(db, room):
    ids = [row.strategy_id for row in versions(db, room)]
    jobs = db.scalars(
        select(BacktestJob)
        .where(
            BacktestJob.user_id == room.user_id,
            BacktestJob.strategy_id.in_(ids),
            BacktestJob.status == "completed",
            ~BacktestJob.id.in_(select(ResearchRun.job_id)),
        )
        .order_by(BacktestJob.created_at.desc())
        .limit(6)
    ).all()
    return [
        {
            "job_id": row.id,
            "strategy_id": row.strategy_id,
            "start": str(row.start_date),
            "end": str(row.end_date),
            "metrics": json.loads(row.result_json).get("metrics"),
            "dataset_fingerprint": json.loads(row.result_json).get("dataset_fingerprint"),
            "caveat": json.loads(row.result_json).get("caveat"),
        }
        for row in jobs
        if row.result_json
    ]


def session_payload(db, room, strategy_payload):
    rows = db.scalars(
        select(ResearchTurn)
        .where(ResearchTurn.session_id == room.id)
        .order_by(ResearchTurn.created_at, ResearchTurn.id)
    ).all()
    version_rows = []
    for version in versions(db, room):
        strategy = db.scalar(
            select(Strategy).where(Strategy.id == version.strategy_id, Strategy.user_id == room.user_id)
        )
        if strategy:
            version_rows.append(
                {
                    "number": version.number,
                    "parent_strategy_id": version.parent_strategy_id,
                    **strategy_payload(strategy),
                }
            )
    return {
        "id": room.id,
        "title": room.title,
        "objective": room.objective,
        "selected_strategy_id": room.selected_strategy_id,
        "created_at": room.created_at,
        "turns": [turn_payload(row) for row in rows],
        "versions": version_rows,
        **experiment_evidence(db, room),
    }


def owned_turn(db, user, turn_id):
    row = db.get(ResearchTurn, turn_id)
    if row is None:
        raise HTTPException(404, "요청을 찾을 수 없습니다")
    return (row, owned_session(db, user, row.session_id))
