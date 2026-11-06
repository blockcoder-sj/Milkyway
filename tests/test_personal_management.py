"""Deletion is owner/CSRF scoped, preserves dependencies and frees quota."""
import datetime as dt
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.orm import sessionmaker

from cloud_app import main
from cloud_app.database import Base, User, Strategy, PaperAccount, PaperPosition, PaperFill, EquityPoint, BacktestJob
from cloud_app.research_models import ResearchBase, ResearchSession, ResearchVersion, PersonalPaperSession
from cloud_app.paper_sessions import period_bounds, session_allows_execution
from cloud_app.strategies import StrategySpec


class PersonalManagementTests(unittest.TestCase):
    def remove(self, path, **kwargs):
        return self.client.request("DELETE", path, json={"confirm": True}, **kwargs)

    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.engine=create_engine("sqlite:///"+self.directory.name+"/db")
        @event.listens_for(self.engine,"connect")
        def foreign_keys(db, _):db.execute("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(self.engine);ResearchBase.metadata.create_all(self.engine)
        self.factory=sessionmaker(bind=self.engine,expire_on_commit=False)
        self.db=self.factory()
        self.settings=replace(main.settings,personal_local_mode=True,app_env="development",authority_enabled=False,
                              credential_backend="local",max_users=1,public_base_url="http://localhost:8080",dataset_dir=Path(self.directory.name)/"data")
        self.owner=User(email="owner@tests.invalid",display_name="Owner",password_hash="unused")
        self.db.add(self.owner);self.db.flush()
        self.spec=StrategySpec(name="Test strategy",symbols=["AAPL"],factors=[{"kind":"momentum"}],portfolio={"max_positions":1})
        self.strategy=Strategy(user_id=self.owner.id,name=self.spec.name,spec_json=self.spec.model_dump_json())
        self.db.add(self.strategy);self.db.commit()
        self.before=main.app.dependency_overrides.copy()
        def db():
            with self.factory() as s:yield s
        main.app.dependency_overrides[main.get_db]=db
        self.setting_patch=patch.object(main,"settings",self.settings);self.setting_patch.start()
        self.paper_patch=patch("cloud_app.paper.get_settings",return_value=self.settings);self.paper_patch.start()
        self.client=TestClient(main.app,base_url="http://localhost:8080")
        me=self.client.post("/api/auth/local",headers={"Origin":"http://localhost:8080","X-Milkyway-Local":"1"}).json()
        self.headers={"X-CSRF-Token":me["csrf"]}

    def tearDown(self):
        self.client.close();self.db.close();self.engine.dispose()
        self.paper_patch.stop();self.setting_patch.stop();main.app.dependency_overrides.clear();main.app.dependency_overrides.update(self.before)
        self.directory.cleanup()

    def account(self, owner=None):
        row=PaperAccount(user_id=owner or self.owner.id,strategy_id=self.strategy.id,name="Paper",initial_cash=100000,cash=100000)
        self.db.add(row);self.db.commit();return row

    def test_account_delete_requires_csrf_and_cascades_only_its_own_records(self):
        row=self.account();other=self.account();identity=row.id;other_id=other.id
        self.db.add_all([PaperPosition(account_id=row.id,ticker="AAPL",shares=1,avg_price=100,last_price=101),
            PaperFill(account_id=row.id,ticker="AAPL",side="BUY",shares=1,price=100,fee=0,reason="test",dedupe_key="kept"),
            EquityPoint(account_id=row.id,equity=100001,cash=99900)])
        self.db.commit()
        self.assertEqual(self.remove("/api/accounts/"+row.id).status_code,403)
        self.assertEqual(self.remove("/api/accounts/"+row.id,headers=self.headers).status_code,204)
        self.db.expire_all()
        self.assertIsNone(self.db.get(PaperAccount,identity))
        self.assertIsNotNone(self.db.get(PaperAccount,other_id))
        for model in (PaperPosition,PaperFill,EquityPoint):self.assertEqual(self.db.scalar(select(func.count()).select_from(model)),0)

    def test_another_owner_cannot_delete_or_disclose_account_or_strategy(self):
        other=User(email="other@tests.invalid",display_name="Other",password_hash="unused")
        self.db.add(other);self.db.flush()
        strategy=Strategy(user_id=other.id,name="Other",spec_json=self.spec.model_dump_json());self.db.add(strategy);self.db.flush()
        row=PaperAccount(user_id=other.id,strategy_id=strategy.id,name="Other paper",initial_cash=1,cash=1)
        self.db.add(row);self.db.commit()
        for kind,identity in (("accounts",row.id),("strategies",strategy.id)):
            self.assertEqual(self.remove("/api/"+kind+"/"+identity,headers=self.headers).status_code,404)

    def test_strategy_delete_is_blocked_until_dependent_accounts_are_removed(self):
        row=self.account()
        self.assertEqual(self.remove("/api/strategies/"+self.strategy.id,headers=self.headers).status_code,409)
        self.remove("/api/accounts/"+row.id,headers=self.headers)
        room=ResearchSession(user_id=self.owner.id,title="Research",selected_strategy_id=self.strategy.id)
        self.db.add(room);self.db.flush()
        self.db.add(ResearchVersion(session_id=room.id,strategy_id=self.strategy.id,number=1))
        self.db.commit()
        self.assertEqual(self.remove("/api/strategies/"+self.strategy.id).status_code,403)
        self.assertEqual(self.remove("/api/strategies/"+self.strategy.id,headers=self.headers).status_code,204)
        self.db.expire_all();self.assertIsNone(self.db.get(ResearchSession,room.id).selected_strategy_id)

    def test_running_backtest_prevents_strategy_delete(self):
        self.db.add(BacktestJob(user_id=self.owner.id,strategy_id=self.strategy.id,status="running",start_date=dt.date(2026,1,1),end_date=dt.date(2026,2,1)))
        self.db.commit()
        self.assertEqual(self.remove("/api/strategies/"+self.strategy.id,headers=self.headers).status_code,409)

    def test_one_week_run_survives_sessions_and_expires_without_liquidating(self):
        response=self.client.post("/api/accounts",json={"strategy_id":self.strategy.id,"name":"One week","run_days":7},headers=self.headers)
        self.assertEqual(response.status_code,201,response.text)
        run=response.json()["paper_session"]
        self.assertEqual(run["mode"],"period");self.assertEqual(run["duration_days"],7)
        opens=dt.datetime.fromisoformat(run["opens_at"]);closes=dt.datetime.fromisoformat(run["closes_at"])
        self.assertEqual(closes-opens,dt.timedelta(days=7))
        row=self.db.get(PaperAccount,response.json()["id"])
        self.assertTrue(session_allows_execution(self.db,row,opens+dt.timedelta(days=3)))
        self.assertFalse(session_allows_execution(self.db,row,closes))
        self.db.commit();self.assertEqual(row.status,"paused")
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperFill)),0)
        self.assertFalse(session_allows_execution(self.db,row,closes+dt.timedelta(days=1)))

    def test_duration_and_one_day_schedule_are_mutually_exclusive(self):
        response=self.client.post("/api/accounts",json={"strategy_id":self.strategy.id,"name":"Bad schedule","run_days":7,"session_date":"2026-11-05"},headers=self.headers)
        self.assertEqual(response.status_code,422)
        for days in (0,31):
            with self.assertRaises(ValueError):period_bounds(days,dt.datetime.now(dt.timezone.utc))
