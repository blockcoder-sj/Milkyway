"""Loopback-only browser fixture: temporary DB/history and mocked AI, no real APIs.
Run: APP_ENV=development DATABASE_URL=sqlite:///:memory: python -m tests.serve_research_fixture
"""
from fastapi import Request
import uvicorn
from tests.test_research import ResearchTests
from cloud_app import main


def run():
    @main.app.middleware("http")
    async def identify_fixture(request, call_next):
        response = await call_next(request)
        response.headers["X-Milkyway-Offline-Fixture"] = "synthetic-no-external-ai"
        return response


    fixture = ResearchTests()
    fixture.setUp()
    try:
        fixture.build_experiment(2)
        fixture.run_jobs(4)

        def actor(request: Request):
            request.state.session_payload = {"csrf": "synthetic-csrf"}
            return fixture.user

        main.app.dependency_overrides[main.current_user] = actor

        uvicorn.run(main.app, host="127.0.0.1", port=8767, lifespan="off", log_level="warning")
    finally:
        fixture.tearDown()
        fixture.doCleanups()


if __name__ == "__main__":
    run()
