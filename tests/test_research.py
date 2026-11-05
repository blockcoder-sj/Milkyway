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

    def test_approved_research_saves_full_market_strategy_without_fixed_tickers(self):
        self.key()
        def automatic(request, key):
            response = self.provider_reply(request, key)
            response["reply"]["strategy"].update(universe="us_all", symbols=[])
            response["reply"]["strategy"]["portfolio"]["max_positions"] = 10
            return response
        self.provider.side_effect = automatic
        turn = self.prepare("미국 상장주식 전체에서 상승 추세 종목을 자동 선정해")
        self.provider.assert_not_called()
        approved = self.approve(turn)
        self.assertEqual(approved.status_code, 200, approved.text)
        strategy = self.db.scalar(select(Strategy).where(Strategy.user_id == self.user.id))
        spec = json.loads(strategy.spec_json)
        self.assertEqual(spec["universe"], "us_all")
        self.assertEqual(spec["symbols"], [])
        self.assertEqual(spec["portfolio"]["max_positions"], 10)
        self.assertEqual(self.provider.call_count, 1)

    def test_existing_fixed_strategy_can_convert_to_automatic_without_an_ai_call(self):
        self.key()
        turn = self.prepare()
        self.assertEqual(self.approve(turn).status_code, 200)
        original = self.db.scalar(select(Strategy).where(Strategy.user_id == self.user.id))
        saved = json.loads(original.spec_json)
        body = {"request_id":"convert-us-market-0001", "universe":"us_all", "symbols":[],
                **{key:saved[key] for key in ("portfolio","filters","factors")}}
        response = self.client.post(f'/api/research/sessions/{self.room["id"]}/versions/{original.id}/adjust',json=body)
        self.assertEqual(response.status_code,201,response.text)
        self.assertEqual(self.provider.call_count,1)
        self.db.expire_all()
        versions = self.db.scalars(select(Strategy).where(Strategy.user_id == self.user.id)).all()
        self.assertEqual(len(versions),2)
        original = self.db.get(Strategy,original.id)
        self.assertEqual(json.loads(original.spec_json)["symbols"],["AAPL","MSFT"])
        revised = next(row for row in versions if row.id != original.id)
        self.assertEqual(json.loads(revised.spec_json)["universe"],"us_all")
        self.assertEqual(json.loads(revised.spec_json)["symbols"],[])

    def test_structured_output_schema_requires_all_fields_and_forbids_extras(self):
        request = research_ai.make_request("gpt-5.4-mini", {"hypothesis":"simple"})
        format = request["text"]["format"]
        self.assertEqual(format["type"], "json_schema")
        self.assertTrue(format["strict"])
        def check(node):
            if isinstance(node, dict):
                self.assertNotIn("default", node)
                if node.get("type") == "object":
                    self.assertFalse(node["additionalProperties"])
                    self.assertEqual(set(node["required"]),set(node["properties"]))
                for value in node.values(): check(value)
            elif isinstance(node, list):
                for value in node: check(value)
        check(format["schema"])

    def test_json_mode_marker_is_in_input_not_only_instructions(self):
        request = research_ai.make_request("gpt-5.4-mini", {"hypothesis":"simple"})
        self.assertIn("JSON", json.loads(request["input"])["output_format"])

    def test_provider_diagnostics_never_expose_raw_error_or_secrets(self):
        error = research_ai.provider_rejection(400, {"error":{"code":"unsupported_value", "param":"text.format.type", "message":"synthetic-private-key"}})
        self.assertIn("HTTP 400", error.detail)
        self.assertIn("text.format.type", error.detail)
        self.assertNotIn("synthetic-private-key", error.detail)
        quota = research_ai.provider_rejection(429, {"error":{"code":"insufficient_quota"}})
        self.assertIn("잔액", quota.detail)
        bad = research_ai.provider_rejection(500, {"error":{"code":["secret"], "param":{"secret":True}}})
        self.assertNotIn("secret", bad.detail)

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
        self.assertIn("총 투자 60%", new["spec"]["description"])
        self.assertIn("평균 매입단가", new["spec"]["description"])
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

    def test_rename_preserves_history_and_approval_and_is_owner_scoped(self):
        turn=self.prepare()
        path=f'/api/research/sessions/{self.room["id"]}'
        before=self.client.get(path).json()
        renamed=self.client.patch(path,json={"title":"  추세 가설 연구  "})
        self.assertEqual(renamed.status_code,200)
        after=self.client.get(path).json()
        self.assertEqual(after['title'],'추세 가설 연구')
        self.assertEqual(before['turns'],after['turns'])
        self.assertEqual(before['versions'],after['versions'])
        self.provider.assert_not_called()
        for title in ['   ','x'*101]:
            self.assertEqual(self.client.patch(path,json={'title':title}).status_code,422)
        self.actor=self.other
        self.assertEqual(self.client.patch(path,json={'title':'외부'}).status_code,404)
        self.actor=self.user
        self.key()
        self.assertEqual(self.approve(turn).json()['status'],'completed')

    def test_failed_response_keeps_safe_diagnostic_usage_and_cannot_replay(self):
        self.key();turn=self.prepare()
        self.provider.side_effect=None
        self.provider.return_value={'error':{'code':'output_limit','detail':'출력 한도 초과','request_id':'req_123','http_status':200,'elapsed_ms':1234},'usage':{'input_tokens':100,'output_tokens':4000}}
        failed=self.approve(turn).json()
        self.assertEqual(failed['status'],'failed')
        self.assertEqual(failed['diagnostic']['code'],'output_limit')
        self.assertEqual(failed['usage']['output_tokens'],4000)
        self.assertEqual(failed['error'],'출력 한도 초과')
        self.assertEqual(self.approve(turn).json()['status'],'failed')
        self.assertEqual(self.provider.call_count,1)

    def test_lowest_reasoning_is_previewed_and_approved_exactly(self):
        self.key(); turn = self.prepare()
        self.assertEqual(turn["approval"]["model"], "gpt-5.4-mini")
        self.assertEqual(turn["approval"]["reasoning"], "none")
        self.assertEqual(turn["approval"]["request"]["reasoning"], {"effort": "none"})
        with patch.dict(os.environ, {"OPENAI_REASONING_EFFORT": "low"}):
            self.assertEqual(self.approve(turn).status_code, 409)
        self.provider.assert_not_called()

    def test_failed_draft_preserves_narrative_and_context_without_a_version(self):
        self.key(); turn = self.prepare()
        self.provider.side_effect = None
        self.provider.return_value = {'reply':{'reply':'대상을 먼저 확인하겠습니다',
            'strategy':{'invalid':'discarded'}, 'limitations':[], 'next_steps':[]},
            'error':{'code':'schema','detail':'전략 형식을 검증하지 못했습니다'},
            'usage':{'input_tokens':100,'output_tokens':200}}
        failed = self.approve(turn).json()
        self.assertEqual(failed['status'], 'failed')
        self.assertEqual(failed['response']['reply'], '대상을 먼저 확인하겠습니다')
        self.assertIsNone(failed['response']['strategy'])
        self.assertIsNone(failed['strategy_id'])
        self.assertEqual(self.client.get(f'/api/research/sessions/{self.room["id"]}').json()['versions'], [])
        self.assertEqual(self.approve(turn).json()['status'], 'failed')
        self.assertEqual(self.provider.call_count, 1)
        next_turn = self.prepare('그 가설을 다시 구체화해 주세요')
        history = json.loads(next_turn['approval']['request']['input'])['recent_history']
        self.assertEqual(history[0]['turn_status'], 'failed')
        self.assertFalse(history[0]['strategy_saved'])
        self.assertEqual(history[0]['assistant'], failed['response']['reply'])

    def test_strategy_save_denial_preserves_reply_and_usage_without_mutation(self):
        self.key(); turn = self.prepare()
        with patch.object(main, 'settings', replace(self.settings, max_strategies_per_user=0)):
            failed = self.approve(turn).json()
        self.assertEqual(failed['status'], 'failed')
        self.assertEqual(failed['diagnostic']['code'], 'save')
        self.assertEqual(failed['response']['reply'], '가설을 전략으로 만들었습니다')
        self.assertIsNone(failed['response']['strategy'])
        self.assertEqual(failed['usage']['output_tokens'], 100)
        room = self.client.get(f'/api/research/sessions/{self.room["id"]}').json()
        self.assertEqual(room['versions'], [])
        self.assertIsNone(room['selected_strategy_id'])


class ProviderContractTests(unittest.TestCase):
    def test_recovery_keeps_prose_but_no_rejected_or_interrupted_strategy(self):
        cases = [
            ('completed', '{"reply":"가설을 먼저 확인합니다","strategy":{"name":"x"}}', 'schema'),
            ('completed', '{"reply":"확인된 내용만 보존","strategy":{"factors":[', 'json'),
            ('incomplete', '{"reply":"확인한 대화 내용","strategy":{"factors":[', 'output_limit'),
            ('completed', '{"reply":"   ","strategy":null}', 'schema'),
        ]
        for state, text, code in cases:
            with self.subTest(state=state, text=text):
                calls = []
                def handle(request):
                    calls.append(request)
                    return httpx.Response(200, json={'status':state,
                        'incomplete_details':{'reason':'max_output_tokens'},
                        'output':[{'type':'message','content':[{'type':'output_text','text':text}]}]})
                with patch.object(research_ai.httpx,'Client',return_value=httpx.Client(transport=httpx.MockTransport(handle))):
                    result = research_ai._execute({}, {'key':'synthetic'})
                self.assertEqual(result['error']['code'], code)
                if '   ' in text:
                    self.assertNotIn('reply', result)
                else:
                    self.assertIsNone(result['reply']['strategy'])
                    self.assertTrue(result['reply']['reply'])
                self.assertEqual(len(calls), 1)

    def test_a_refusal_never_recovers_a_partial_narrative(self):
        payload = {'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},
                   'output':[{'type':'message','content':[{'type':'refusal','refusal':'declined'},
                       {'type':'output_text','text':'{"reply":"discarded","strategy":'}]}]}
        client=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=payload)))
        with patch.object(research_ai.httpx,'Client',return_value=client):
            result = research_ai._execute({}, {'key':'synthetic'})
        self.assertEqual(result['error']['code'], 'refusal')
        self.assertNotIn('reply', result)

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
                    self.assertEqual(research_ai._execute(request, {"key": "synthetic"})["error"]["code"], "provider")
            self.assertEqual(len(calls), 1)
            self.assertFalse(calls[0]["store"])
            self.assertEqual(calls[0]["max_output_tokens"], 4000)

    def test_failures_are_specific_bounded_and_never_echo_provider_secrets(self):
        cases=[
            (200,{'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'},'usage':{'output_tokens':4000}},'output_limit'),
            (200,{'status':'completed','output':[{'content':[{'type':'refusal','refusal':'synthetic-secret'}]}]},'refusal'),
            (200,{'status':'completed','output':[]},'empty'),
            (200,{'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'bad synthetic-secret'}]}]},'json'),
            (200,{'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'{"reply":"ok","strategy":{"name":"x","portfolio":{"max_positions":100}}}'}]}]},'schema'),
            (401,{'error':{'message':'synthetic-secret','code':'invalid_api_key'}},'provider')]
        for status,payload,code in cases:
            with self.subTest(code=code):
                calls=[]
                def handle(request):
                    calls.append(request)
                    return httpx.Response(status,json=payload,headers={'x-request-id':'req_safe123'})
                with patch.object(research_ai.httpx,'Client',return_value=httpx.Client(transport=httpx.MockTransport(handle))):
                    result=research_ai._execute({}, {'key':'synthetic-key'})
                self.assertEqual(result['error']['code'],code)
                self.assertEqual(result['error']['request_id'],'req_safe123')
                self.assertNotIn('synthetic-secret',json.dumps(result))
                self.assertEqual(len(calls),1)
        for error,code in [(httpx.ReadTimeout('synthetic-secret'),'timeout'),(httpx.ConnectError('synthetic-secret'),'network')]:
            def handle(request):raise error
            with patch.object(research_ai.httpx,'Client',return_value=httpx.Client(transport=httpx.MockTransport(handle))):
                result=research_ai._execute({}, {'key':'synthetic-key'})
            self.assertEqual(result['error']['code'],code)
            self.assertNotIn('synthetic-secret',json.dumps(result))


if __name__ == "__main__":
    unittest.main()
