"""Paper recovery preserves the ledger and reports each execution gate truthfully."""
import datetime as dt
import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from cloud_app import main, personal_runtime as runtime
from cloud_app.database import Base, MarketDataConnection, MemberQuote, PaperAccount, PaperFill, PaperPosition, RuntimeHeartbeat, Strategy, User, utcnow
from cloud_app.research_models import PersonalPaperSession, ResearchBase
from cloud_app.strategies import StrategySpec


class PersonalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.engine = create_engine("sqlite:///" + str(self.root / "db"))
        Base.metadata.create_all(self.engine); ResearchBase.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, expire_on_commit=False, autoflush=False)
        self.db = self.factory()
        self.settings = replace(main.settings, personal_local_mode=True, app_env="development", max_users=1,
                                authority_enabled=False, credential_backend="local", public_base_url="http://localhost:8080",
                                dataset_dir=self.root / "data", quote_provider="member")
        self.user = User(email="owner@test.invalid", display_name="Owner", password_hash="unused")
        self.db.add(self.user); self.db.flush()
        self.spec = StrategySpec(name="kept", symbols=["AAPL", "MSFT"], factors=[{"kind":"momentum"}], portfolio={"max_positions":2})
        self.strategy = Strategy(user_id=self.user.id, name="kept", spec_json=self.spec.model_dump_json())
        self.db.add(self.strategy); self.db.flush()
        self.account = PaperAccount(user_id=self.user.id, strategy_id=self.strategy.id, name="existing", status="active", initial_cash=100000, cash=98765)
        self.db.add(self.account); self.db.flush()
        self.db.add(MarketDataConnection(user_id=self.user.id,provider="toss",environment="live",encrypted_api_key="never-decrypt-in-diagnostics",encrypted_api_secret="never-decrypt",key_hint="none",secret_hint="none"))
        self.now = utcnow()
        for name in ("paper-worker", "personal-data", "backtest-worker"):
            self.db.add(RuntimeHeartbeat(component=name,instance_id="synthetic",observed_at=self.now,detail="running"))
        self.db.add_all([MemberQuote(user_id=self.user.id,ticker=s,price=100,source="synthetic-test",observed_at=self.now) for s in self.spec.symbols])
        self.db.commit()
        self.patches = [patch.object(main,"settings",self.settings),patch("cloud_app.paper.get_settings",return_value=self.settings),
                        patch.object(runtime,"regular_market_open",return_value=True),
                        patch.object(runtime,"personal_data_status",return_value={"ready":True,"stale":False,"action_ready":True})]
        for p in self.patches:p.start()

    def tearDown(self):
        self.db.close();self.engine.dispose()
        for p in reversed(self.patches):p.stop()
        self.directory.cleanup()

    def status(self):
        return runtime.operation_status(self.db,self.settings,self.user.id,self.account.id,now=self.now)

    def test_running_requires_fresh_worker_data_and_every_selected_quote(self):
        self.assertTrue(self.status()["ready_to_trade"])
        quote=self.db.get(MemberQuote,(self.user.id,"MSFT"));quote.observed_at=self.now-dt.timedelta(minutes=10);self.db.commit()
        self.assertEqual(self.status()["state"],"waiting_quotes")
        self.assertFalse(self.status()["ready_to_trade"])
        quote.observed_at=self.now+dt.timedelta(seconds=1);self.db.commit()
        self.assertFalse(self.status()["ready_to_trade"])
        quote.observed_at=self.now;self.db.commit()
        self.assertEqual(self.status()["state"],"running")
        with patch.object(runtime,"personal_data_status",return_value={"ready":False,"stale":True,"action_ready":False}):
            self.assertEqual(self.status()["state"],"waiting_data")
        row=self.db.get(RuntimeHeartbeat,"paper-worker");row.observed_at=self.now-dt.timedelta(minutes=10);self.db.commit()
        self.assertEqual(self.status()["state"],"worker_offline")

    def test_network_gap_and_reconnection_do_not_create_fills_or_reset_cash(self):
        quote=self.db.get(MemberQuote,(self.user.id,"AAPL"));self.db.delete(quote);self.db.commit()
        self.assertEqual(self.status()["state"],"waiting_quotes")
        self.db.add(MemberQuote(user_id=self.user.id,ticker="AAPL",price=105,source="synthetic-test",observed_at=self.now));self.db.commit()
        self.assertEqual(self.status()["state"],"running")
        self.assertEqual(self.account.cash,98765)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperFill)),0)

    def test_worker_provider_failure_is_specific_and_recovers_without_old_quotes(self):
        from cloud_app import worker
        from cloud_app.provider_process import ProviderOperationError
        from cloud_app.paper import QuoteValue
        with patch.object(worker,"regular_market_open",return_value=True),patch.dict(worker._member_retry_after,{},clear=True),patch.object(worker,"_discard_member_provider"),patch.object(worker,"_fetch_member_quotes",side_effect=ProviderOperationError(403,"quote_ip_not_allowed")):
            count,errors=worker.collect_member_quotes(self.db,self.settings);self.db.commit()
            self.assertEqual((count,errors),(0,1))
            self.assertEqual(self.db.scalar(select(func.count()).select_from(MemberQuote)),0)
        result=runtime.operation_status(self.db,self.settings,self.user.id,self.account.id)
        self.assertEqual(result["state"],"quote_ip_not_allowed")
        self.assertFalse(result["ready_to_trade"])
        values=[QuoteValue(s,100,0,0,0,"synthetic-test",utcnow()) for s in self.spec.symbols]
        with patch.object(worker,"regular_market_open",return_value=True),patch.dict(worker._member_retry_after,{},clear=True),patch.object(worker,"_fetch_member_quotes",return_value=(self.user.id,values)):
            count,errors=worker.collect_member_quotes(self.db,self.settings);self.db.commit()
            self.assertEqual((count,errors),(2,0))
        self.assertEqual(runtime.operation_status(self.db,self.settings,self.user.id,self.account.id)["state"],"running")
        self.assertEqual(self.account.cash,98765)

    def test_provider_errors_never_return_raw_secrets_or_urls_to_diagnostics(self):
        from cloud_app import worker
        from cloud_app.toss_quotes import TossIpNotAllowedError, TossAuthenticationError, TossRateLimitError
        import requests
        from unittest.mock import Mock
        cases=[(TossIpNotAllowedError("private response"),"quote_ip_not_allowed"),
               (TossAuthenticationError("private response"),"quote_authentication_failed"),
               (TossRateLimitError(1),"quote_rate_limited"),
               (requests.ConnectionError("https://private.invalid/secret"),"quote_network_unavailable")]
        for failure,expected in cases:
            with self.subTest(expected=expected),patch.object(worker,"_personal_quote_client",Mock(fetch=Mock(side_effect=failure))):
                with self.assertRaises(HTTPException) as exc:worker._personal_quote_execute({"tickers":["AAPL"]},{"provider":"toss"})
                self.assertEqual(exc.exception.detail,expected)

    def test_preopen_probe_detects_ip_rejection_and_success_without_using_probe_prices(self):
        from cloud_app import worker
        from cloud_app.provider_process import ProviderOperationError
        from cloud_app.paper import QuoteValue
        with patch.object(worker,"_fetch_member_quotes",side_effect=ProviderOperationError(403,"quote_ip_not_allowed")),patch.object(worker,"_discard_member_provider"):
            result=runtime.probe_connection(self.db,self.settings,self.user.id,self.account.id)
        self.assertEqual(result["state"],"quote_ip_not_allowed")
        with patch.object(runtime,"regular_market_open",return_value=False):
            self.assertEqual(runtime.operation_status(self.db,self.settings,self.user.id,self.account.id)["state"],"quote_ip_not_allowed")
        values=[QuoteValue(s,999,0,0,0,"synthetic-probe",utcnow()) for s in self.spec.symbols]
        with patch.object(worker,"_fetch_member_quotes",return_value=(self.user.id,values)),patch.object(worker,"_discard_member_provider"):
            result=runtime.probe_connection(self.db,self.settings,self.user.id,self.account.id)
        self.assertEqual(result["state"],"connected")
        self.assertEqual(self.db.get(MemberQuote,(self.user.id,"AAPL")).price,100)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperFill)),0)
        with patch.object(runtime,"regular_market_open",return_value=False):
            self.assertEqual(runtime.operation_status(self.db,self.settings,self.user.id,self.account.id)["state"],"market_closed")

    def test_parallel_probe_is_rejected_before_any_provider_or_key_access(self):
        runtime._probe_slot.acquire()
        try:
            with patch("cloud_app.worker._fetch_member_quotes") as external:
                result=runtime.probe_connection(self.db,self.settings,self.user.id,self.account.id)
                self.assertEqual(result["state"],"probe_busy");external.assert_not_called()
        finally:runtime._probe_slot.release()

    def test_market_closed_is_standby_instead_of_claiming_trading(self):
        with patch.object(runtime,"regular_market_open",return_value=False):
            result=self.status()
        self.assertEqual(result["state"],"market_closed")
        self.assertTrue(result["ready_to_wait"])
        self.assertFalse(result["ready_to_trade"])
        self.account.status="paused";self.db.commit()
        self.assertEqual(self.status()["state"],"paused")

    def test_resume_is_idempotent_and_preserves_existing_positions_and_fills(self):
        self.account.status="paused"
        position=PaperPosition(account_id=self.account.id,ticker="AAPL",shares=7,avg_price=100,last_price=105)
        fill=PaperFill(account_id=self.account.id,ticker="AAPL",side="BUY",shares=7,price=100,fee=1,reason="rebalance",dedupe_key="kept")
        self.db.add_all([position,fill]);self.db.commit()
        first=runtime.resume_account(self.db,self.settings,self.user.id,self.account.id)
        second=runtime.resume_account(self.db,self.settings,self.user.id,self.account.id)
        self.assertTrue(first["resumed"]);self.assertFalse(second["resumed"])
        self.assertEqual(self.account.cash,98765)
        self.assertEqual((position.shares,position.avg_price),(7,100))
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperAccount)),1)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperFill)),1)

    def test_expired_and_review_accounts_are_never_forced_to_resume(self):
        self.account.status="paused"
        self.db.add(PersonalPaperSession(account_id=self.account.id,session_date=(self.now-dt.timedelta(days=1)).date(),opens_at=self.now-dt.timedelta(days=1),closes_at=self.now-dt.timedelta(hours=1)))
        self.db.commit()
        self.assertEqual(self.status()["state"],"session_finished")
        with self.assertRaises(HTTPException) as exc:runtime.resume_account(self.db,self.settings,self.user.id,self.account.id)
        self.assertEqual(exc.exception.status_code,409)
        self.db.delete(self.db.get(PersonalPaperSession,self.account.id));self.account.status="review_required";self.db.commit()
        with self.assertRaises(HTTPException):runtime.resume_account(self.db,self.settings,self.user.id,self.account.id)
        self.assertEqual(self.account.status,"review_required")

    def test_account_ownership_and_active_symbol_capacity_remain_enforced(self):
        for fn in (runtime.resume_account,runtime.operation_status):
            with self.assertRaises(HTTPException) as exc:fn(self.db,self.settings,"another-owner",self.account.id)
            self.assertEqual(exc.exception.status_code,404)
        self.account.status="paused"
        spec=StrategySpec(name="20",symbols=["X"+chr(65+i) for i in range(20)],factors=[{"kind":"momentum"}])
        strategy=Strategy(user_id=self.user.id,name="20",spec_json=spec.model_dump_json());self.db.add(strategy);self.db.flush()
        self.db.add(PaperAccount(user_id=self.user.id,strategy_id=strategy.id,name="other",initial_cash=100000,cash=100000));self.db.commit()
        with self.assertRaises(HTTPException) as exc:runtime.resume_account(self.db,self.settings,self.user.id,self.account.id)
        self.assertEqual(exc.exception.status_code,409)
        self.assertEqual(self.account.status,"paused")

    def test_control_capability_requires_personal_mode_and_private_regular_file(self):
        root=self.root / "runtime";root.mkdir();path=root / ".local-control.json"
        with patch.object(runtime.config,"ROOT",self.root):
            self.assertFalse(runtime.control_connection(self.settings)["available"])
            path.write_text(json.dumps({"token":"a"*64}));path.chmod(0o600)
            self.assertEqual(runtime.control_connection(self.settings)["url"],"http://127.0.0.1:19480")
            path.chmod(0o644);self.assertFalse(runtime.control_connection(self.settings)["available"])
            path.unlink();path.symlink_to(self.root / "other")
            self.assertFalse(runtime.control_connection(self.settings)["available"])
        with self.assertRaises(HTTPException):runtime.control_connection(replace(self.settings,personal_local_mode=False))

    def test_http_resume_requires_session_csrf_and_personal_mode(self):
        overrides=main.app.dependency_overrides.copy()
        def db():
            with self.factory() as session:yield session
        main.app.dependency_overrides[main.get_db]=db
        # No lifespan: only the isolated database above is used.
        client=TestClient(main.app,base_url="http://localhost:8080")
        try:
            self.assertEqual(client.get("/api/personal/control").status_code,401)
            me=client.post("/api/auth/local",headers={"Origin":"http://localhost:8080","X-Milkyway-Local":"1"}).json()
            self.assertEqual(client.post("/api/personal/resume",json={"account_id":self.account.id}).status_code,403)
            with patch.object(runtime,"probe_connection",return_value={"state":"connected"}):
                response=client.post("/api/personal/resume",json={"account_id":self.account.id},headers={"X-CSRF-Token":me["csrf"]})
            self.assertEqual(response.status_code,200,response.text)
            self.assertNotIn("encrypted_api_key",response.text)
            with patch.object(main,"settings",replace(self.settings,personal_local_mode=False)):
                self.assertEqual(client.get("/api/personal/operation").status_code,404)
                self.assertNotIn("127.0.0.1:19480",client.get("/").headers["content-security-policy"])
        finally:
            client.close();main.app.dependency_overrides.clear();main.app.dependency_overrides.update(overrides)
