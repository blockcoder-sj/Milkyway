"""Personal research HTTP and provider contract tests; no real API calls."""
import datetime as dt
import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cloud_app import main, research_ai
from cloud_app.database import Base, Strategy, User, utcnow
from cloud_app.research_models import ResearchBase, ResearchTurn, ResearchVersion


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.engine = create_engine("sqlite:///" + str(self.root / "db"), connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        ResearchBase.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, expire_on_commit=False, autoflush=False)
        self.db = self.factory()
        self.user = User(email="research@example.test", display_name="Research", password_hash="unused")
        self.other = User(email="other@example.test", display_name="Other", password_hash="unused")
        self.db.add_all([self.user, self.other]); self.db.commit()
        self.settings = replace(main.settings, personal_local_mode=True, app_env="development", authority_enabled=False,
            shared_ai_enabled=False, credential_backend="local", quote_provider="member", dataset_dir=self.root / "data", terminal_events_path=self.root / "events.jsonl",
            max_outstanding_backtests_per_user=8)
        self.patches = [patch.object(main, "settings", self.settings), patch.object(research_ai, "ROOT", self.root),
                        patch.dict(os.environ, {"OPENAI_API_KEY": "", "OPENAI_MODEL": "", "OPENAI_REASONING_EFFORT": ""})]
        for item in self.patches: item.start()
        self.actor = self.user
        def database():
            with self.factory() as db: yield db
        self.old_overrides = main.app.dependency_overrides.copy()
        main.app.dependency_overrides.update({main.get_db: database, main.current_user: lambda: self.actor,
                                              main.csrf_guard: lambda: self.actor})
        self.client = TestClient(main.app)  # No lifespan: never touches the configured runtime.
        main._attempts.clear()
        self.provider = patch.object(research_ai, "invoke_approved", side_effect=self.provider_reply).start()
        self.addCleanup(patch.stopall)
        self.room = self.client.post("/api/research/sessions", json={"title": "Test", "objective": "낙폭을 줄이는 가설"}).json()
        self.count = 0

    def tearDown(self):
        self.client.close()
        main.app.dependency_overrides.clear(); main.app.dependency_overrides.update(self.old_overrides)
        self.db.close(); self.engine.dispose()
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()

    def provider_reply(self, request, key):
        return {"reply": {"reply": "가설을 전략으로 만들었습니다", "strategy": {
            "name": "Research momentum", "symbols": ["AAPL", "MSFT"], "factors": [{"kind": "momentum"}],
            "portfolio": {"max_positions": 2}}, "limitations": [], "next_steps": ["기간을 나눠 검증하세요"]},
            "usage": {"input_tokens": 100, "output_tokens": 100, "total_tokens": 200}}

    def prepare(self, prompt="AAPL MSFT 모멘텀 전략", request_id=None):
        self.count += 1
        response = self.client.post(f'/api/research/sessions/{self.room["id"]}/messages',
            json={"prompt": prompt, "request_id": request_id or f"request-{self.count:05d}"})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def approve(self, turn):
        return self.client.post(f'/api/research/turns/{turn["id"]}/approve',
            json={"approved": True, "request_digest": turn["approval"]["request_digest"]})

    def key(self):
        (self.root / ".env").write_text("OPENAI_API_KEY=synthetic-test-key-never-valid\nOPENAI_MODEL=gpt-5.4-mini\n")

    def adjustment_fixture(self):
        self.key()
        self.assertEqual(self.approve(self.prepare()).json()["status"], "completed")
        room = self.client.get(f'/api/research/sessions/{self.room["id"]}').json()
        version = room["versions"][0]
        body = {key: version["spec"][key] for key in ("portfolio", "filters", "factors")}
        body["request_id"] = "adjustment-001"
        body["portfolio"] = {**body["portfolio"], "investment_fraction": 0.6, "max_position_fraction": 0.3, "rebalance_weights": True}
        url = f'/api/research/sessions/{room["id"]}/versions/{version["id"]}/adjust'
        self.provider.reset_mock()
        return version, body, url

    def test_adjustment_is_immutable_idempotent_and_never_calls_ai(self):
        version, body, url = self.adjustment_fixture()
        result = self.client.post(url, json=body)
        self.assertEqual(result.status_code, 201, result.text)
        room = result.json()
        self.assertEqual(len(room["versions"]), 2)
        old = next(item for item in room["versions"] if item["id"] == version["id"])
        new = next(item for item in room["versions"] if item["id"] == room["selected_strategy_id"])
        self.assertEqual(old["spec"], version["spec"])
        self.assertEqual(new["spec"]["portfolio"]["investment_fraction"], 0.6)
        self.assertEqual(new["spec"]["symbols"], old["spec"]["symbols"])
        again = self.client.post(url, json=body)
        self.assertEqual(len(again.json()["versions"]), 2)
        body["portfolio"]["rebalance_days"] = 3
        self.assertEqual(self.client.post(url, json=body).status_code, 409)
        self.provider.assert_not_called()

    def test_adjustment_rejects_pending_call_and_other_owner(self):
        _, body, url = self.adjustment_fixture()
        turn = self.prepare("비중 조정 논의")
        self.assertEqual(self.client.post(url, json=body).status_code, 409)
        self.client.post(f'/api/research/turns/{turn["id"]}/cancel')
        self.actor = self.other
        self.assertEqual(self.client.post(url, json=body).status_code, 404)
        self.provider.assert_not_called()

    def test_adjustment_rejects_stale_base_and_invalid_numbers(self):
        _, body, url = self.adjustment_fixture()
        self.assertEqual(self.client.post(url, json=body).status_code, 201)
        body["request_id"] = "adjustment-002"
        self.assertEqual(self.client.post(url, json=body).status_code, 409)
        body["portfolio"]["investment_fraction"] = 1.1
        self.assertEqual(self.client.post(url, json=body).status_code, 422)
        self.provider.assert_not_called()

    def test_adjustment_validates_symbol_count_and_nonzero_factors(self):
        _, body, url = self.adjustment_fixture()
        body["portfolio"]["max_positions"] = 3
        self.assertEqual(self.client.post(url, json=body).status_code, 422)
        body["portfolio"]["max_positions"] = 2
        body["factors"][0]["weight"] = 0
        self.assertEqual(self.client.post(url, json=body).status_code, 422)
        room = self.client.get(f'/api/research/sessions/{self.room["id"]}').json()
        self.assertEqual(len(room["versions"]), 1)
        self.provider.assert_not_called()

    def test_preview_status_and_cancel_never_call_provider(self):
        turn = self.prepare()
        config = self.client.get("/api/research/config").json()
        self.assertFalse(config["configured"])
        self.assertTrue(config["approval_required"])
        self.assertEqual(turn["approval"]["max_calls"], 1)
        self.assertFalse(turn["approval"]["request"]["store"])
        self.assertEqual(self.approve(turn).status_code, 409)
        self.assertEqual(self.client.post(f'/api/research/turns/{turn["id"]}/cancel').status_code, 200)
        self.key()
        self.approve(turn)
        self.provider.assert_not_called()

    def test_approval_persists_version_and_repeated_click_calls_once(self):
        self.key(); turn = self.prepare()
        self.assertEqual(self.approve(turn).json()["status"], "completed")
        self.approve(turn)
        self.assertEqual(self.provider.call_count, 1)
        room = self.client.get(f'/api/research/sessions/{self.room["id"]}').json()
        self.assertEqual(len(room["versions"]), 1)
        self.assertEqual(room["selected_strategy_id"], room["versions"][0]["id"])
        self.assertNotIn("synthetic-test-key", json.dumps(room))
        later = self.prepare("방금 전략의 손절만 3%로 바꿔줘")
        context = json.loads(later["approval"]["request"]["input"])
        self.assertEqual(context["selected_strategy"]["symbols"], ["AAPL", "MSFT"])
        self.assertEqual(len(context["recent_history"]), 1)
        self.approve(later)
        self.db.expire_all()
        rows = self.db.scalars(select(ResearchVersion).order_by(ResearchVersion.number)).all()
        self.assertEqual(rows[1].parent_strategy_id, rows[0].strategy_id)
        self.assertEqual(len(self.db.scalars(select(Strategy)).all()), 2)

    def test_request_id_is_idempotent_and_conflicting_body_rejected(self):
        first = self.prepare(request_id="same-request")
        again = self.prepare(request_id="same-request")
        self.assertEqual(first["id"], again["id"])
        response = self.client.post(f'/api/research/sessions/{self.room["id"]}/messages',
            json={"prompt": "different", "request_id": "same-request"})
        self.assertEqual(response.status_code, 409)

    def test_wrong_digest_false_approval_and_other_owner_cannot_call(self):
        self.key(); turn = self.prepare()
        for body in ({"approved": False, "request_digest": turn["approval"]["request_digest"]},
                     {"approved": True, "request_digest": "0" * 64}):
            self.assertIn(self.client.post(f'/api/research/turns/{turn["id"]}/approve', json=body).status_code, (409, 422))
        self.actor = self.other
        self.assertEqual(self.approve(turn).status_code, 404)
        self.assertEqual(self.client.get(f'/api/research/sessions/{self.room["id"]}').status_code, 404)
        self.provider.assert_not_called()

    def test_expired_approval_and_changed_model_require_new_request(self):
        self.key(); turn = self.prepare()
        row = self.db.get(ResearchTurn, turn["id"]); row.created_at = utcnow() - dt.timedelta(minutes=16); self.db.commit()
        self.assertEqual(self.approve(turn).status_code, 409)
        next_turn = self.prepare()
        with patch.dict(os.environ, {"OPENAI_MODEL": "another-model"}):
            self.assertEqual(self.approve(next_turn).status_code, 409)
        self.provider.assert_not_called()

    def test_failure_is_durable_and_never_retried_automatically(self):
        self.key(); turn = self.prepare()
        self.provider.side_effect = HTTPException(502, "synthetic failure")
        self.assertEqual(self.approve(turn).json()["status"], "failed")
        self.approve(turn)
        self.assertEqual(self.provider.call_count, 1)
        self.assertEqual(self.db.scalars(select(Strategy)).all(), [])

    def test_cloud_scope_and_legacy_generate_cannot_use_personal_key(self):
        self.key()
        self.assertEqual(self.client.post("/api/strategies/generate", json={"prompt": "AAPL 모멘텀"}).status_code, 409)
        with patch.object(main, "settings", replace(self.settings, personal_local_mode=False)):
            self.assertEqual(self.client.get("/api/research/config").status_code, 404)
        self.provider.assert_not_called()

    def test_strategy_save_failure_rolls_back_version_and_turn(self):
        self.key(); turn = self.prepare()
        with patch.object(main, "settings", replace(self.settings, max_strategies_per_user=0)):
            self.assertEqual(self.approve(turn).json()["status"], "failed")
        self.assertEqual(self.db.scalars(select(ResearchVersion)).all(), [])
        self.assertEqual(self.db.scalars(select(Strategy)).all(), [])

    def test_restart_marks_unknown_running_call_without_resending(self):
        self.key(); turn = self.prepare()
        row = self.db.get(ResearchTurn, turn["id"])
        row.status = "running"; row.approved_at = utcnow() - dt.timedelta(minutes=5); self.db.commit()
        result = self.client.get(f'/api/research/sessions/{self.room["id"]}').json()
        self.assertEqual(result["turns"][0]["status"], "failed")
        self.approve(turn); self.provider.assert_not_called()

    def build_experiment(self, candidates=1):
        from cloud_app import personal_data
        from tests.test_personal_data import NOW, write_outcome
        self.key()
        ids = [self.approve(self.prepare()).json()["strategy_id"] for _ in range(candidates)]
        with patch.object(personal_data._history_process, "run", side_effect=write_outcome):
            personal_data.refresh_personal_data(["AAPL", "MSFT"], self.settings, now=NOW)
        body = {"request_id": "experiment-001", "strategy_ids": ids, "start_date": "2026-03-02",
                "split_date": "2026-06-01", "end_date": "2026-09-24", "objective": "sharpe"}
        path = f'/api/research/sessions/{self.room["id"]}/experiments'
        response = self.client.post(path, json=body)
        self.assertEqual(response.status_code, 201, response.text)
        return body, path, response.json()

    def run_jobs(self, count):
        from contextlib import nullcontext
        from cloud_app import worker
        with patch.object(worker, "SessionLocal", self.factory), patch.object(worker, "get_settings", return_value=self.settings), \
             patch.object(worker, "_backtest_liveness", return_value=nullcontext()), \
             patch.object(worker, "_backtest_deadline", return_value=nullcontext()), \
             patch("cloud_app.personal_data.refresh_personal_data", side_effect=AssertionError("Must use captured data")):
            for _ in range(count): self.assertTrue(worker.process_one_backtest())

    def test_complete_experiment_export_deploy_and_followup(self):
        import ast
        from cloud_app.database import BacktestJob, PaperAccount, PaperFill
        body, path, experiment = self.build_experiment(2)
        self.assertEqual(self.client.post(path, json=body).json()["id"], experiment["id"])
        self.assertEqual(len(self.db.scalars(select(BacktestJob)).all()), 4)
        strategy_id = body["strategy_ids"][0]
        deploy_path = f'/api/research/sessions/{self.room["id"]}/deploy'
        deploy = {"strategy_id": strategy_id, "request_id": "deploy-0001", "name": "My paper"}
        self.assertEqual(self.client.post(deploy_path, json=deploy).status_code, 409)
        self.run_jobs(4)
        room = self.client.get(f'/api/research/sessions/{self.room["id"]}').json()
        comparison = room["experiments"][0]
        self.assertEqual(comparison["status"], "completed", comparison)
        self.assertIn(comparison["development_leader"], body["strategy_ids"])
        self.assertTrue(all(c["validation"]["metrics"]["trade_count"] > 0 for c in comparison["candidates"]))
        code = self.client.get(f'/api/research/sessions/{self.room["id"]}/export/{strategy_id}')
        self.assertEqual(code.status_code, 200)
        ast.parse(code.text)
        response = self.client.post(deploy_path, json=deploy)
        self.assertEqual(response.status_code, 201, response.text)
        account_id = response.json()["id"]
        self.assertEqual(self.client.post(deploy_path, json=deploy).json()["id"], account_id)
        self.assertEqual(len(self.db.scalars(select(PaperAccount)).all()), 1)
        self.db.add(PaperFill(account_id=account_id, ticker="AAPL", side="buy", shares=1, price=100,
                             fee=.3, reason="rebalance", dedupe_key="synthetic-research-fill")); self.db.commit()
        self.client.post(f'/api/research/sessions/{self.room["id"]}/select/{body["strategy_ids"][1]}')
        turn = self.prepare("검증 결과와 최근 체결을 설명해줘")
        evidence = json.loads(turn["approval"]["request"]["input"])["evidence"]
        self.assertEqual(evidence["paper"][0]["recent_fills"][0]["symbol"], "AAPL")
        self.assertEqual(evidence["paper"][0]["strategy_id"], strategy_id)
        self.assertEqual(self.db.get(PaperAccount, account_id).strategy_id, strategy_id)
        self.assertEqual(self.provider.call_count, 2)  # Evidence and paper execution make no AI call.
        self.actor = self.other
        self.assertEqual(self.client.post(path, json=body).status_code, 404)
        self.assertEqual(self.client.post(deploy_path, json=deploy).status_code, 404)
        self.assertEqual(self.client.get(f'/api/research/sessions/{self.room["id"]}/export/{strategy_id}').status_code, 404)

    def test_experiment_guards_and_data_tampering(self):
        body, path, experiment = self.build_experiment()
        self.assertEqual(self.client.post(path, json=dict(body, objective="return_pct")).status_code, 409)
        for changes in ({"strategy_ids": ["foreign"]}, {"split_date": "2026-03-01"},
                        {"strategy_ids": body["strategy_ids"] * 2}):
            self.assertEqual(self.client.post(path, json=dict(body, request_id="invalid-0001", **changes)).status_code, 422)
        with patch.object(main, "settings", replace(self.settings, max_outstanding_backtests_per_user=2)):
            self.assertEqual(self.client.post(path, json=dict(body, request_id="quota-000001")).status_code, 429)
        from cloud_app.research_models import ResearchExperiment
        row = self.db.get(ResearchExperiment, experiment["id"])
        row.fingerprint = "0" * 64; self.db.commit()
        self.run_jobs(2)
        room = self.client.get(f'/api/research/sessions/{self.room["id"]}').json()
        self.assertEqual(room["experiments"][0]["status"], "failed")
        self.assertIsNone(room["experiments"][0]["development_leader"])

    def test_lowest_reasoning_is_previewed_and_approved_exactly(self):
        self.key(); turn = self.prepare()
        self.assertEqual(turn["approval"]["model"], "gpt-5.4-mini")
        self.assertEqual(turn["approval"]["reasoning"], "none")
        self.assertEqual(turn["approval"]["request"]["reasoning"], {"effort": "none"})
        with patch.dict(os.environ, {"OPENAI_REASONING_EFFORT": "low"}):
            self.assertEqual(self.approve(turn).status_code, 409)
        self.provider.assert_not_called()


class ProviderContractTests(unittest.TestCase):
    def test_single_request_contract_and_rejection_do_not_retry(self):
        for status in (200, 429):
            calls = []
            def handle(request):
                calls.append(json.loads(request.content))
                return httpx.Response(status, json={"status": "completed", "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": '{"reply":"어떤 종목을 사용할까요?","strategy":null}'}]}], "usage": {}})
            client = httpx.Client(transport=httpx.MockTransport(handle))
            with patch.object(research_ai.httpx, "Client", return_value=client):
                request = research_ai.make_request("gpt-5.4-mini", {"user_message": "가설"})
                if status == 200:
                    self.assertIsNone(research_ai._execute(request, {"key": "synthetic"})["reply"]["strategy"])
                else:
                    with self.assertRaises(HTTPException): research_ai._execute(request, {"key": "synthetic"})
            self.assertEqual(len(calls), 1)
            self.assertFalse(calls[0]["store"])
            self.assertEqual(calls[0]["max_output_tokens"], 4000)


if __name__ == "__main__":
    unittest.main()
