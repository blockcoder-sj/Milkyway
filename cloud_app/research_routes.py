"""Owner-scoped personal research API. Only /approve can invoke OpenAI."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Literal

from fastapi import Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update

from . import research_ai
from .database import BacktestJob, PaperAccount, Strategy, quota_allocation, utcnow
from .research_models import ResearchDeployment, ResearchExperiment, ResearchSession, ResearchTurn, ResearchVersion
from .strategies import StrategySpec
from .research_experiments import DeployBody, ExperimentBody, enqueue_experiment, experiment_evidence, experiment_payload


class SessionBody(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    objective: str = Field(default="", max_length=2000)


class MessageBody(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    request_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,64}$")


class ApprovalBody(BaseModel):
    request_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    approved: Literal[True]


def aware(value):
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def owned_session(db, user, session_id):
    row = db.scalar(select(ResearchSession).where(ResearchSession.id == session_id, ResearchSession.user_id == user.id))
    if row is None:
        raise HTTPException(404, "연구를 찾을 수 없습니다")
    return row


def versions(db, room):
    return db.scalars(select(ResearchVersion).where(ResearchVersion.session_id == room.id).order_by(ResearchVersion.number)).all()


def expire_interrupted(db, room):
    # Never retry a request whose remote completion is unknown after a restart.
    db.execute(update(ResearchTurn).where(ResearchTurn.session_id == room.id, ResearchTurn.status == "running",
        ResearchTurn.approved_at < utcnow() - dt.timedelta(seconds=research_ai.CALL_TIMEOUT + 60)).values(
            status="failed", error="연결이 중단되어 완료 여부를 확인하지 못했습니다. 자동 재시도하지 않습니다", finished_at=utcnow()))
    db.execute(update(ResearchTurn).where(ResearchTurn.session_id == room.id, ResearchTurn.status == "awaiting_approval",
        ResearchTurn.created_at < utcnow() - dt.timedelta(minutes=15)).values(status="expired", finished_at=utcnow()))
    db.commit()


def require_idle(db, room):
    busy = db.scalar(select(ResearchTurn.id).where(ResearchTurn.session_id == room.id,
                                                 ResearchTurn.status.in_(["awaiting_approval", "running"])))
    if busy:
        raise HTTPException(409, "기존 요청을 승인·취소하거나 실행 완료를 기다려 주세요")


def turn_payload(row):
    request = json.loads(row.request_json)
    return {"id": row.id, "status": row.status, "prompt": row.prompt, "created_at": row.created_at,
            "response": json.loads(row.response_json) if row.response_json else None,
            "usage": json.loads(row.usage_json) if row.usage_json else None,
            "strategy_id": row.strategy_id, "error": row.error,
            "approval": {"request_digest": row.request_digest, "model": request["model"],
                         "reasoning": request.get("reasoning", {}).get("effort", "none"), "max_calls": 1, "max_output_tokens": request["max_output_tokens"],
                         "input_characters": len(request["instructions"]) + len(request["input"]),
                         "expires_at": aware(row.created_at) + dt.timedelta(minutes=15),
                         "request": request if row.status == "awaiting_approval" else None}}


def evidence_context(db, room):
    ids = [row.strategy_id for row in versions(db, room)]
    jobs = db.scalars(select(BacktestJob).where(BacktestJob.user_id == room.user_id,
        BacktestJob.strategy_id.in_(ids), BacktestJob.status == "completed")
        .order_by(BacktestJob.created_at.desc()).limit(6)).all()
    return [{"job_id": row.id, "strategy_id": row.strategy_id, "start": str(row.start_date), "end": str(row.end_date),
             "metrics": json.loads(row.result_json).get("metrics"),
             "dataset_fingerprint": json.loads(row.result_json).get("dataset_fingerprint"),
             "caveat": json.loads(row.result_json).get("caveat")} for row in jobs if row.result_json]


def session_payload(db, room, main):
    rows = db.scalars(select(ResearchTurn).where(ResearchTurn.session_id == room.id)
                      .order_by(ResearchTurn.created_at, ResearchTurn.id)).all()
    version_rows = []
    for version in versions(db, room):
        strategy = db.scalar(select(Strategy).where(Strategy.id == version.strategy_id, Strategy.user_id == room.user_id))
        if strategy:
            version_rows.append({"number": version.number, "parent_strategy_id": version.parent_strategy_id,
                                 **main._strategy_payload(strategy)})
    return {"id": room.id, "title": room.title, "objective": room.objective,
            "selected_strategy_id": room.selected_strategy_id, "created_at": room.created_at,
            "turns": [turn_payload(row) for row in rows], "versions": version_rows,
            **experiment_evidence(db, room)}


def install(app):
    from . import main

    def personal():
        if not main.settings.personal_local_mode or main.settings.production:
            raise HTTPException(404, "개인 연구 기능을 사용할 수 없습니다")

    options = {"dependencies": [Depends(personal)]}

    @app.get("/api/research/config", **options)
    def config(user=Depends(main.current_user)):
        return research_ai.configuration_status(main.settings)

    @app.get("/api/research/sessions", **options)
    def list_sessions(user=Depends(main.current_user), db=Depends(main.get_db)):
        return [{"id": row.id, "title": row.title, "created_at": row.created_at} for row in db.scalars(
            select(ResearchSession).where(ResearchSession.user_id == user.id).order_by(ResearchSession.created_at.desc()))]

    @app.post("/api/research/sessions", status_code=201, **options)
    def create_session(body: SessionBody, user=Depends(main.csrf_guard), db=Depends(main.get_db)):
        with quota_allocation(db, "research", user.id):
            if db.scalar(select(func.count()).select_from(ResearchSession).where(ResearchSession.user_id == user.id)) >= 50:
                raise HTTPException(409, "연구는 최대 50개까지 저장할 수 있습니다")
            row = ResearchSession(user_id=user.id, title=body.title.strip() or "새 연구", objective=body.objective.strip())
            db.add(row)
            db.commit()
            return session_payload(db, row, main)

    @app.get("/api/research/sessions/{session_id}", **options)
    def get_session(session_id: str, user=Depends(main.current_user), db=Depends(main.get_db)):
        room = owned_session(db, user, session_id)
        expire_interrupted(db, room)
        return session_payload(db, room, main)

    @app.post("/api/research/sessions/{session_id}/messages", status_code=201, **options)
    def prepare(session_id: str, body: MessageBody, user=Depends(main.csrf_guard), db=Depends(main.get_db)):
        room = owned_session(db, user, session_id)
        expire_interrupted(db, room)
        with quota_allocation(db, "research", user.id):
            db.refresh(room)
            existing = db.scalar(select(ResearchTurn).where(ResearchTurn.session_id == room.id, ResearchTurn.request_id == body.request_id))
            if existing:
                if existing.prompt != body.prompt.strip():
                    raise HTTPException(409, "같은 요청 ID에 다른 내용을 사용할 수 없습니다")
                return turn_payload(existing)
            require_idle(db, room)
            if not body.prompt.strip():
                raise HTTPException(422, "대화 내용을 입력해 주세요")
            if db.scalar(select(func.count()).select_from(ResearchTurn).where(ResearchTurn.session_id == room.id)) >= 100:
                raise HTTPException(409, "이 연구의 대화 한도에 도달했습니다. 새 연구를 시작하세요")
            history = db.scalars(select(ResearchTurn).where(ResearchTurn.session_id == room.id, ResearchTurn.status == "completed")
                                 .order_by(ResearchTurn.created_at.desc(), ResearchTurn.id.desc()).limit(12)).all()
            selected = db.scalar(select(Strategy).where(Strategy.id == room.selected_strategy_id, Strategy.user_id == user.id))
            context = {"objective": room.objective, "user_message": body.prompt.strip(),
                       "selected_strategy": json.loads(selected.spec_json) if selected else None,
                       "recent_history": [{"user": row.prompt, "assistant": json.loads(row.response_json)["reply"]} for row in reversed(history)],
                       "evidence": {"backtests": evidence_context(db, room), **experiment_evidence(db, room)}}
            try:
                config = research_ai.local_configuration(main.settings)
                while True:
                    try:
                        request = research_ai.make_request(config.model, context, config.reasoning)
                        break
                    except ValueError:
                        if not context["recent_history"]:
                            raise
                        context["recent_history"].pop(0)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from None
            encoded = json.dumps(request, ensure_ascii=False, sort_keys=True)
            row = ResearchTurn(session_id=room.id, request_id=body.request_id, prompt=body.prompt.strip(),
                request_json=encoded, request_digest=hashlib.sha256(encoded.encode()).hexdigest(), base_strategy_id=room.selected_strategy_id)
            db.add(row)
            db.commit()
            return turn_payload(row)

    def owned_turn(db, user, turn_id):
        row = db.get(ResearchTurn, turn_id)
        if row is None:
            raise HTTPException(404, "요청을 찾을 수 없습니다")
        return row, owned_session(db, user, row.session_id)

    @app.post("/api/research/turns/{turn_id}/cancel", **options)
    def cancel(turn_id: str, user=Depends(main.csrf_guard), db=Depends(main.get_db)):
        row, room = owned_turn(db, user, turn_id)
        changed = db.execute(update(ResearchTurn).where(ResearchTurn.id == row.id, ResearchTurn.status == "awaiting_approval")
                             .values(status="cancelled", finished_at=utcnow())).rowcount
        db.commit()
        if not changed:
            raise HTTPException(409, "이미 실행되거나 종료된 요청입니다")
        db.refresh(row)
        return turn_payload(row)

    @app.post("/api/research/turns/{turn_id}/approve", **options)
    def approve(turn_id: str, body: ApprovalBody, user=Depends(main.csrf_guard), db=Depends(main.get_db)):
        row, room = owned_turn(db, user, turn_id)
        if row.request_digest != body.request_digest:
            raise HTTPException(409, "승인할 요청 내용이 다릅니다. 다시 확인해 주세요")
        if row.status != "awaiting_approval":
            return turn_payload(row)  # Repeated clicks and reconnects never make another call.
        if utcnow() - aware(row.created_at) > dt.timedelta(minutes=15):
            row.status = "expired"
            db.commit()
            raise HTTPException(409, "승인 시간이 만료되었습니다. 요청을 다시 작성해 주세요")
        try:
            config = research_ai.local_configuration(main.settings)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        if not config.key:
            raise HTTPException(409, ".env의 OPENAI_API_KEY를 설정하고 앱을 다시 실행해 주세요")
        request = json.loads(row.request_json)
        if config.model != request["model"] or config.reasoning != request.get("reasoning", {}).get("effort", "none"):
            raise HTTPException(409, "모델 설정이 변경됐습니다. 기존 요청을 취소하고 다시 작성해 주세요")
        main._rate_limit("research-ai:" + user.id, 20, 3600)
        claimed = db.execute(update(ResearchTurn).where(ResearchTurn.id == row.id, ResearchTurn.status == "awaiting_approval")
                             .values(status="running", approved_at=utcnow())).rowcount
        db.commit()
        if not claimed:
            db.refresh(row)
            return turn_payload(row)
        try:
            result = research_ai.invoke_approved(request, config.key)
            reply = research_ai.ResearchReply.model_validate(result["reply"])
            with quota_allocation(db, "research", user.id):
                db.refresh(row)
                if row.status != "running":
                    return turn_payload(row)
                row.response_json = reply.model_dump_json()
                row.usage_json = json.dumps(result.get("usage", {}))
                row.status, row.finished_at = "completed", utcnow()
                if reply.strategy:
                    with main._strategy_creation(db, user, reply.strategy, row.prompt[:3000]) as strategy:
                        number = len(versions(db, room)) + 1
                        db.add(ResearchVersion(session_id=room.id, strategy_id=strategy.id, number=number,
                                               parent_strategy_id=row.base_strategy_id))
                        row.strategy_id = strategy.id
                        room.selected_strategy_id = strategy.id
                else:
                    db.commit()
        except Exception as exc:
            db.rollback()
            db.refresh(row)
            row.status, row.finished_at = "failed", utcnow()
            row.error = exc.detail if isinstance(exc, HTTPException) and isinstance(exc.detail, str) else "응답 저장 또는 검증에 실패했습니다. 자동 재시도하지 않습니다"
            db.commit()
        return turn_payload(row)

    @app.post("/api/research/sessions/{session_id}/select/{strategy_id}", **options)
    def select_version(session_id: str, strategy_id: str, user=Depends(main.csrf_guard), db=Depends(main.get_db)):
        room = owned_session(db, user, session_id)
        with quota_allocation(db, "research", user.id):
            require_idle(db, room)
            if strategy_id not in {row.strategy_id for row in versions(db, room)}:
                raise HTTPException(404, "이 연구의 전략 버전이 아닙니다")
            room.selected_strategy_id = strategy_id
            db.commit()
        return session_payload(db, room, main)

    @app.post("/api/research/sessions/{session_id}/experiments", status_code=201, **options)
    def experiment(session_id: str, body: ExperimentBody, user=Depends(main.csrf_guard), db=Depends(main.get_db)):
        room = owned_session(db, user, session_id)
        return enqueue_experiment(db, user, room, body, main.settings, {v.strategy_id for v in versions(db, room)})

    @app.post("/api/research/sessions/{session_id}/deploy", status_code=201, **options)
    def deploy(session_id: str, body: DeployBody, user=Depends(main.csrf_guard), db=Depends(main.get_db)):
        room = owned_session(db, user, session_id)
        with quota_allocation(db, "research", user.id):
            existing = db.scalar(select(ResearchDeployment).where(ResearchDeployment.session_id == room.id,
                ResearchDeployment.request_id == body.request_id))
            if existing:
                account = db.get(PaperAccount, existing.account_id)
                if existing.strategy_id != body.strategy_id or account.name != body.name.strip():
                    raise HTTPException(409, "같은 요청 ID의 계좌 설정이 다릅니다")
                return main.account_snapshot(db, account)
            if body.strategy_id not in {v.strategy_id for v in versions(db, room)}:
                raise HTTPException(404, "이 연구의 전략 버전이 아닙니다")
            experiments = db.scalars(select(ResearchExperiment).where(ResearchExperiment.session_id == room.id)).all()
            verified = any(p["status"] == "completed" and any(c["strategy_id"] == body.strategy_id and
                (c.get("validation", {}).get("metrics") or {}).get("trade_count", 0) > 0 for c in p["candidates"])
                for p in (experiment_payload(db, e) for e in experiments))
            if not verified:
                raise HTTPException(409, "이 버전의 개발·검증 비교를 완료하고 검증 구간 거래 결과를 확인하세요")
            with main._account_creation(main.AccountBody(strategy_id=body.strategy_id, name=body.name), user, db) as account:
                db.add(ResearchDeployment(session_id=room.id, strategy_id=body.strategy_id,
                    account_id=account.id, request_id=body.request_id))
            return main.account_snapshot(db, account)

    @app.get("/api/research/sessions/{session_id}/export/{strategy_id}", **options)
    def export(session_id: str, strategy_id: str, user=Depends(main.current_user), db=Depends(main.get_db)):
        room = owned_session(db, user, session_id)
        if strategy_id not in {v.strategy_id for v in versions(db, room)}:
            raise HTTPException(404, "이 연구의 전략 버전이 아닙니다")
        strategy = main._owned_strategy(db, user, strategy_id)
        spec = StrategySpec.model_validate_json(strategy.spec_json)
        code = """# Run from the Milkyway repository: python strategy.py YYYY-MM-DD YYYY-MM-DD
# This file uses the same validated strategy engine as the application.
import json
import sys
from cloud_app.strategies import StrategySpec, run_strategy_backtest
SPEC = StrategySpec.model_validate_json(%r)
if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python strategy.py START END")
    print(json.dumps(run_strategy_backtest(SPEC, start=sys.argv[1], end=sys.argv[2], bias_mode="exploratory"), default=str, ensure_ascii=False))
""" % spec.model_dump_json()
        return Response(code, media_type="text/x-python", headers={"Content-Disposition": 'attachment; filename="milkyway-strategy.py"'})
