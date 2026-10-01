"""Research workflows. No imports from the HTTP composition root or UI layer."""

from __future__ import annotations
import datetime as dt
import hashlib
import json
from fastapi import HTTPException
from sqlalchemy import func, select, update
from . import research_ai
from .database import PaperAccount, Strategy, quota_allocation, utcnow
from .research_models import (
    ResearchDeployment,
    ResearchExperiment,
    ResearchSession,
    ResearchTurn,
    ResearchVersion,
)
from .research_schemas import ApprovalBody, MessageBody, SessionBody
from .research_experiments import (
    DeployBody,
    ExperimentBody,
    enqueue_experiment,
    experiment_evidence,
    experiment_payload,
)
from .research_store import (
    aware,
    owned_session,
    owned_turn,
    versions,
    expire_interrupted,
    require_idle,
    turn_payload,
    evidence_context,
    session_payload,
)
from .research_ports import ResearchServices
from .research_validation import narrative_only
from .strategies import StrategySpec


class ResearchService:
    """One authenticated request's DB unit of work and explicit application ports."""

    def __init__(self, services: ResearchServices, db, user):
        self.services = services
        self.db = db
        self.user = user

    @property
    def settings(self):
        return self.services.get_settings()

    def list_sessions(self):
        return [
            {"id": row.id, "title": row.title, "created_at": row.created_at}
            for row in self.db.scalars(
                select(ResearchSession)
                .where(ResearchSession.user_id == self.user.id)
                .order_by(ResearchSession.created_at.desc())
            )
        ]

    def create_session(self, body: SessionBody):
        with quota_allocation(self.db, "research", self.user.id):
            if (
                self.db.scalar(
                    select(func.count())
                    .select_from(ResearchSession)
                    .where(ResearchSession.user_id == self.user.id)
                )
                >= 50
            ):
                raise HTTPException(409, "연구는 최대 50개까지 저장할 수 있습니다")
            row = ResearchSession(
                user_id=self.user.id, title=body.title.strip() or "새 연구", objective=body.objective.strip()
            )
            self.db.add(row)
            self.db.commit()
            return session_payload(self.db, row, self.services.strategy_payload)

    def get_session(self, session_id: str):
        room = owned_session(self.db, self.user, session_id)
        expire_interrupted(self.db, room)
        return session_payload(self.db, room, self.services.strategy_payload)

    def rename_session(self, session_id: str, body):
        room = owned_session(self.db, self.user, session_id)
        title = body.title.strip()
        if not title:
            raise HTTPException(422, "대화 이름을 입력해 주세요")
        room.title = title
        self.db.commit()
        return {"id": room.id, "title": room.title}

    def prepare(self, session_id: str, body: MessageBody):
        room = owned_session(self.db, self.user, session_id)
        expire_interrupted(self.db, room)
        with quota_allocation(self.db, "research", self.user.id):
            self.db.refresh(room)
            existing = self.db.scalar(
                select(ResearchTurn).where(
                    ResearchTurn.session_id == room.id, ResearchTurn.request_id == body.request_id
                )
            )
            if existing:
                if existing.prompt != body.prompt.strip():
                    raise HTTPException(409, "같은 요청 ID에 다른 내용을 사용할 수 없습니다")
                return turn_payload(existing)
            require_idle(self.db, room)
            if not body.prompt.strip():
                raise HTTPException(422, "대화 내용을 입력해 주세요")
            if (
                self.db.scalar(
                    select(func.count()).select_from(ResearchTurn).where(ResearchTurn.session_id == room.id)
                )
                >= 100
            ):
                raise HTTPException(409, "이 연구의 대화 한도에 도달했습니다. 새 연구를 시작하세요")
            history = self.db.scalars(
                select(ResearchTurn)
                .where(ResearchTurn.session_id == room.id,
                       ResearchTurn.status.in_(['completed', 'failed']),
                       ResearchTurn.response_json.is_not(None))
                .order_by(ResearchTurn.created_at.desc(), ResearchTurn.id.desc())
                .limit(12)
            ).all()
            selected = self.db.scalar(
                select(Strategy).where(
                    Strategy.id == room.selected_strategy_id, Strategy.user_id == self.user.id
                )
            )
            context = {
                "objective": room.objective,
                "user_message": body.prompt.strip(),
                "selected_strategy": json.loads(selected.spec_json) if selected else None,
                "recent_history": [
                    {"user": row.prompt, "assistant": json.loads(row.response_json)["reply"],
                     "turn_status": row.status, "strategy_saved": bool(row.strategy_id)}
                    for row in reversed(history)
                ],
                "evidence": {
                    "backtests": evidence_context(self.db, room),
                    **experiment_evidence(self.db, room),
                },
            }
            try:
                config = research_ai.local_configuration(self.settings)
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
            row = ResearchTurn(
                session_id=room.id,
                request_id=body.request_id,
                prompt=body.prompt.strip(),
                request_json=encoded,
                request_digest=hashlib.sha256(encoded.encode()).hexdigest(),
                base_strategy_id=room.selected_strategy_id,
            )
            self.db.add(row)
            self.db.commit()
            return turn_payload(row)

    def cancel(self, turn_id: str):
        row, room = owned_turn(self.db, self.user, turn_id)
        changed = self.db.execute(
            update(ResearchTurn)
            .where(ResearchTurn.id == row.id, ResearchTurn.status == "awaiting_approval")
            .values(status="cancelled", finished_at=utcnow())
        ).rowcount
        self.db.commit()
        if not changed:
            raise HTTPException(409, "이미 실행되거나 종료된 요청입니다")
        self.db.refresh(row)
        return turn_payload(row)

    def approve(self, turn_id: str, body: ApprovalBody):
        row, room = owned_turn(self.db, self.user, turn_id)
        if row.request_digest != body.request_digest:
            raise HTTPException(409, "승인할 요청 내용이 다릅니다. 다시 확인해 주세요")
        if row.status != "awaiting_approval":
            return turn_payload(row)
        if utcnow() - aware(row.created_at) > dt.timedelta(minutes=15):
            row.status = "expired"
            self.db.commit()
            raise HTTPException(409, "승인 시간이 만료되었습니다. 요청을 다시 작성해 주세요")
        try:
            config = research_ai.local_configuration(self.settings)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        if not config.key:
            raise HTTPException(409, ".env의 OPENAI_API_KEY를 설정하고 앱을 다시 실행해 주세요")
        request = json.loads(row.request_json)
        if config.model != request["model"] or config.reasoning != request.get("reasoning", {}).get(
            "effort", "none"
        ):
            raise HTTPException(409, "모델 설정이 변경됐습니다. 기존 요청을 취소하고 다시 작성해 주세요")
        self.services.rate_limit("research-ai:" + self.user.id, 20, 3600)
        claimed = self.db.execute(
            update(ResearchTurn)
            .where(ResearchTurn.id == row.id, ResearchTurn.status == "awaiting_approval")
            .values(status="running", approved_at=utcnow())
        ).rowcount
        self.db.commit()
        if not claimed:
            self.db.refresh(row)
            return turn_payload(row)
        reply, usage = None, {}
        try:
            result = research_ai.invoke_approved(request, config.key)
            usage = research_ai.safe_usage({'usage': result.get('usage', {})})
            if result.get("error"):
                self.db.refresh(row)
                if row.status == "running":
                    narrative = narrative_only(result.get('reply'))
                    row.response_json = json.dumps(narrative, ensure_ascii=False) if narrative else None
                    row.status, row.finished_at = "failed", utcnow()
                    row.error = json.dumps(result["error"], ensure_ascii=False)
                    row.usage_json = json.dumps(usage)
                    self.db.commit()
                return turn_payload(row)
            reply = research_ai.ResearchReply.model_validate(result["reply"])
            with quota_allocation(self.db, "research", self.user.id):
                self.db.refresh(row)
                if row.status != "running":
                    return turn_payload(row)
                row.response_json = reply.model_dump_json()
                row.usage_json = json.dumps(usage)
                row.status, row.finished_at = ("completed", utcnow())
                if reply.strategy:
                    with self.services.strategy_creation(
                        self.db, self.user, reply.strategy, row.prompt[:3000]
                    ) as strategy:
                        number = len(versions(self.db, room)) + 1
                        self.db.add(
                            ResearchVersion(
                                session_id=room.id,
                                strategy_id=strategy.id,
                                number=number,
                                parent_strategy_id=row.base_strategy_id,
                            )
                        )
                        row.strategy_id = strategy.id
                        room.selected_strategy_id = strategy.id
                else:
                    self.db.commit()
        except Exception as exc:
            self.db.rollback()
            self.db.refresh(row)
            if row.status != 'running':
                return turn_payload(row)
            row.status, row.finished_at = ("failed", utcnow())
            detail = (
                exc.detail
                if isinstance(exc, HTTPException) and isinstance(exc.detail, str)
                else "응답 저장 또는 검증에 실패했습니다. 자동 재시도하지 않습니다"
            )
            if reply:
                row.response_json = json.dumps(narrative_only(reply.model_dump(mode='json')), ensure_ascii=False)
                row.error = json.dumps({'code':'save', 'detail':research_ai.ERROR_MESSAGES['save']+' · '+detail,
                                       'request_id':None, 'http_status':None, 'elapsed_ms':None}, ensure_ascii=False)
            else:
                row.error = detail
            row.usage_json = json.dumps(usage)
            self.db.commit()
        return turn_payload(row)

    def select_version(self, session_id: str, strategy_id: str):
        room = owned_session(self.db, self.user, session_id)
        with quota_allocation(self.db, "research", self.user.id):
            require_idle(self.db, room)
            if strategy_id not in {row.strategy_id for row in versions(self.db, room)}:
                raise HTTPException(404, "이 연구의 전략 버전이 아닙니다")
            room.selected_strategy_id = strategy_id
            self.db.commit()
        return session_payload(self.db, room, self.services.strategy_payload)

    def experiment(self, session_id: str, body: ExperimentBody):
        room = owned_session(self.db, self.user, session_id)
        return enqueue_experiment(
            self.db, self.user, room, body, self.settings, {v.strategy_id for v in versions(self.db, room)}
        )

    def adjust(self, session_id: str, strategy_id: str, body):
        from .research_adjustments import adjust_version
        return adjust_version(self.services, self.db, self.user, session_id, strategy_id, body)

    def deploy(self, session_id: str, body: DeployBody):
        room = owned_session(self.db, self.user, session_id)
        with quota_allocation(self.db, "research", self.user.id):
            existing = self.db.scalar(
                select(ResearchDeployment).where(
                    ResearchDeployment.session_id == room.id, ResearchDeployment.request_id == body.request_id
                )
            )
            if existing:
                account = self.db.get(PaperAccount, existing.account_id)
                if existing.strategy_id != body.strategy_id or account.name != body.name.strip():
                    raise HTTPException(409, "같은 요청 ID의 계좌 설정이 다릅니다")
                return self.services.account_snapshot(self.db, account)
            if body.strategy_id not in {v.strategy_id for v in versions(self.db, room)}:
                raise HTTPException(404, "이 연구의 전략 버전이 아닙니다")
            experiments = self.db.scalars(
                select(ResearchExperiment).where(ResearchExperiment.session_id == room.id)
            ).all()
            verified = any(
                (
                    p["status"] == "completed"
                    and any(
                        (
                            c["strategy_id"] == body.strategy_id
                            and (c.get("validation", {}).get("metrics") or {}).get("trade_count", 0) > 0
                            for c in p["candidates"]
                        )
                    )
                    for p in (experiment_payload(self.db, e) for e in experiments)
                )
            )
            if not verified:
                raise HTTPException(
                    409, "이 버전의 개발·검증 비교를 완료하고 검증 구간 거래 결과를 확인하세요"
                )
            with self.services.account_creation(body.strategy_id, body.name, self.user, self.db) as account:
                self.db.add(
                    ResearchDeployment(
                        session_id=room.id,
                        strategy_id=body.strategy_id,
                        account_id=account.id,
                        request_id=body.request_id,
                    )
                )
            return self.services.account_snapshot(self.db, account)

    def export(self, session_id: str, strategy_id: str):
        room = owned_session(self.db, self.user, session_id)
        if strategy_id not in {v.strategy_id for v in versions(self.db, room)}:
            raise HTTPException(404, "이 연구의 전략 버전이 아닙니다")
        strategy = self.services.owned_strategy(self.db, self.user, strategy_id)
        spec = StrategySpec.model_validate_json(strategy.spec_json)
        code = (
            '# Run from the Milkyway repository: python strategy.py YYYY-MM-DD YYYY-MM-DD\n# This file uses the same validated strategy engine as the application.\nimport json\nimport sys\nfrom cloud_app.strategies import StrategySpec, run_strategy_backtest\nSPEC = StrategySpec.model_validate_json(%r)\nif __name__ == "__main__":\n    if len(sys.argv) != 3:\n        raise SystemExit("Usage: python strategy.py START END")\n    print(json.dumps(run_strategy_backtest(SPEC, start=sys.argv[1], end=sys.argv[2], bias_mode="exploratory"), default=str, ensure_ascii=False))\n'
            % spec.model_dump_json()
        )
        return code
