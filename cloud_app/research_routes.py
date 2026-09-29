"""HTTP binding for personal research; business workflows live in ResearchService."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from . import research_ai
from .research_experiments import DeployBody, ExperimentBody
from .research_ports import ResearchServices
from .research_schemas import ApprovalBody, MessageBody, SessionBody
from .research_service import ResearchService


def install(app, *, services: ResearchServices, current_user, csrf_guard, get_db):
    def personal():
        settings = services.get_settings()
        if not settings.personal_local_mode or settings.production:
            raise HTTPException(404, "개인 연구 기능을 사용할 수 없습니다")

    router = APIRouter(prefix="/api/research", dependencies=[Depends(personal)])

    def reader(user=Depends(current_user), db=Depends(get_db)):
        return ResearchService(services, db, user)

    def writer(user=Depends(csrf_guard), db=Depends(get_db)):
        return ResearchService(services, db, user)

    @router.get("/config")
    def config(user=Depends(current_user)):
        return research_ai.configuration_status(services.get_settings())

    @router.get("/sessions")
    def list_sessions(service=Depends(reader)):
        return service.list_sessions()

    @router.post("/sessions", status_code=201)
    def create_session(body: SessionBody, service=Depends(writer)):
        return service.create_session(body)

    @router.get("/sessions/{session_id}")
    def get_session(session_id: str, service=Depends(reader)):
        return service.get_session(session_id)

    @router.post("/sessions/{session_id}/messages", status_code=201)
    def prepare(session_id: str, body: MessageBody, service=Depends(writer)):
        return service.prepare(session_id, body)

    @router.post("/turns/{turn_id}/cancel")
    def cancel(turn_id: str, service=Depends(writer)):
        return service.cancel(turn_id)

    @router.post("/turns/{turn_id}/approve")
    def approve(turn_id: str, body: ApprovalBody, service=Depends(writer)):
        return service.approve(turn_id, body)

    @router.post("/sessions/{session_id}/select/{strategy_id}")
    def select_version(session_id: str, strategy_id: str, service=Depends(writer)):
        return service.select_version(session_id, strategy_id)

    @router.post("/sessions/{session_id}/experiments", status_code=201)
    def experiment(session_id: str, body: ExperimentBody, service=Depends(writer)):
        return service.experiment(session_id, body)

    @router.post("/sessions/{session_id}/deploy", status_code=201)
    def deploy(session_id: str, body: DeployBody, service=Depends(writer)):
        return service.deploy(session_id, body)

    @router.get("/sessions/{session_id}/export/{strategy_id}")
    def export(session_id: str, strategy_id: str, service=Depends(reader)):
        return Response(
            service.export(session_id, strategy_id),
            media_type="text/x-python",
            headers={"Content-Disposition": 'attachment; filename="milkyway-strategy.py"'},
        )

    app.include_router(router)
