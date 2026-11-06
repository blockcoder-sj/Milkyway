"""Deletion HTTP/ledger/research invariants with synthetic local data only."""
import datetime as dt
import json
import unittest
from dataclasses import replace
from unittest.mock import patch

from fastapi import Request
from sqlalchemy import select, func, text
from cloud_app import main, personal_resources as resources
from cloud_app.database import (
    AdmittedTicker, BacktestJob, EquityPoint, PaperAccount, PaperFill,
    PaperPosition, RuntimeHeartbeat, Strategy, utcnow,
)
from cloud_app.research_models import PersonalPaperSession, ResearchDeployment, ResearchSession, ResearchTurn, ResearchVersion
from cloud_app.strategies import StrategySpec
from tests import test_research as research, test_personal_continuous as continuous


class ResourceDeletionTests(unittest.TestCase):
    def setUp(self):
        self.f = research.ResearchTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.addCleanup(self.f.tearDown)
        self.db, self.client, self.owner = self.f.db, self.f.client, self.f.user.id
        self.db.execute(text("PRAGMA foreign_keys=ON")); self.db.commit()

    def strategy(self, owner=None):
        spec=StrategySpec(name="Deletable strategy",universe="us_all",factors=[{"kind":"momentum"}])
        row=Strategy(user_id=owner or self.owner,name=spec.name,spec_json=spec.model_dump_json())
        self.db.add(row);self.db.commit()
        return row.id

    def account(self, strategy=None, owner=None):
        strategy = strategy or self.strategy(owner)
        row=PaperAccount(user_id=owner or self.owner,strategy_id=strategy,name="Delete fixture",cash=90000,initial_cash=100000)
        self.db.add(row);self.db.commit()
        account_id=row.id
        self.db.add_all([
            PaperPosition(account_id=account_id,ticker="AAA",shares=100,avg_price=100,last_price=100),
            PaperFill(account_id=account_id,ticker="AAA",side="BUY",shares=100,price=100,fee=0,reason="rebalance",dedupe_key=account_id+":fixture"),
            EquityPoint(account_id=account_id,equity=100000,cash=90000),
            AdmittedTicker(account_id=account_id,ticker="AAA"),
            RuntimeHeartbeat(component="paper-account:"+account_id,instance_id="fixture",observed_at=utcnow(),detail="active"),
            PersonalPaperSession(account_id=account_id,session_date=dt.date(2026,11,5),opens_at=utcnow(),closes_at=utcnow()),
        ]);self.db.commit()
        return account_id

    def remove(self, kind, ident, **kw):
        return self.client.request("DELETE",f"/api/{kind}/{ident}",json=kw or {"confirm":True})

    def test_account_delete_removes_ledger_and_schedule_without_touching_other_account(self):
        strategy=self.strategy(); account=self.account(strategy); other=self.account(strategy)
        self.assertEqual(self.remove("accounts",account).status_code,204)
        self.db.expire_all()
        self.assertIsNone(self.db.get(PaperAccount,account))
        self.assertIsNotNone(self.db.get(PaperAccount,other))
        for model in (PersonalPaperSession,AdmittedTicker,PaperPosition,PaperFill,EquityPoint):
            self.assertEqual(self.db.scalar(select(func.count()).select_from(model).where(model.account_id==account)),0)
        self.assertIsNone(self.db.get(RuntimeHeartbeat,"paper-account:"+account))
        self.assertIsNotNone(self.db.get(Strategy,strategy))
        self.assertEqual(self.remove("accounts",account).status_code,404)
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperFill)),1)

    def test_owner_confirmation_csrf_and_local_mode_are_required(self):
        account=self.account();strategy=self.strategy()
        for kind,ident in [("accounts",account),("strategies",strategy)]:
            self.assertEqual(self.remove(kind,ident,confirm=False).status_code,422)
            self.assertEqual(self.client.request("DELETE",f"/api/{kind}/{ident}").status_code,422)
            self.f.actor=self.f.other
            self.assertEqual(self.remove(kind,ident).status_code,404)
            self.f.actor=self.f.user
            for config in (replace(self.f.settings,personal_local_mode=False),replace(self.f.settings,app_env="production")):
                with patch.object(main,"settings",config):
                    self.assertEqual(self.remove(kind,ident).status_code,404)
        override=main.app.dependency_overrides.pop(main.csrf_guard)
        current=main.app.dependency_overrides[main.current_user]
        def identified(request: Request):
            request.state.session_payload={"csrf":"synthetic-delete-token"}
            return self.f.user
        main.app.dependency_overrides[main.current_user]=identified
        try:
            self.assertEqual(self.remove("accounts",account).status_code,403)
        finally:
            main.app.dependency_overrides[main.csrf_guard]=override
            main.app.dependency_overrides[main.current_user]=current
        self.assertIsNotNone(self.db.get(PaperAccount,account))
        self.assertIsNotNone(self.db.get(Strategy,strategy))

    def test_strategy_requires_account_deletion_and_no_running_backtest(self):
        strategy=self.strategy();account=self.account(strategy)
        self.assertEqual(self.remove("strategies",strategy).status_code,409)
        self.assertEqual(self.remove("accounts",account).status_code,204)
        job=BacktestJob(user_id=self.owner,strategy_id=strategy,start_date=dt.date(2026,1,1),end_date=dt.date(2026,11,4),status="running")
        self.db.add(job);self.db.commit();job_id=job.id
        self.assertEqual(self.remove("strategies",strategy).status_code,409)
        job.status="queued";self.db.commit()
        self.assertEqual(self.remove("strategies",strategy).status_code,204)
        self.db.expire_all()
        self.assertIsNone(self.db.get(Strategy,strategy));self.assertIsNone(self.db.get(BacktestJob,job_id))

    def test_account_delete_failure_rolls_back_all_children(self):
        account=self.account();execute=self.db.execute
        def fail(statement,*args,**kw):
            if getattr(statement,"is_delete",False) and statement.table.name=="paper_accounts":
                raise RuntimeError("synthetic final-step failure")
            return execute(statement,*args,**kw)
        with patch.object(self.db,"execute",side_effect=fail):
            with self.assertRaises(RuntimeError):resources.delete_account(self.db,self.owner,account)
        self.assertIsNotNone(self.db.get(PaperAccount,account))
        for model in (PaperPosition,PaperFill,EquityPoint):
            self.assertEqual(self.db.scalar(select(func.count()).select_from(model).where(model.account_id==account)),1)

    def test_deleted_version_is_not_selected_recreated_or_renumbered(self):
        f=self.f;f.key()
        for _ in range(2):self.assertEqual(f.approve(f.prepare()).status_code,200)
        before=self.client.get(f'/api/research/sessions/{f.room["id"]}').json()
        first,second=[v["id"] for v in before["versions"]]
        self.assertEqual(self.remove("strategies",first).status_code,204)
        self.assertEqual(self.client.post(f'/api/research/sessions/{f.room["id"]}/select/{first}').status_code,404)
        self.assertEqual(f.approve(f.prepare()).status_code,200)
        room=self.client.get(f'/api/research/sessions/{f.room["id"]}').json()
        self.assertEqual([v["number"] for v in room["versions"]],[2,3])
        latest=room["selected_strategy_id"]
        self.assertEqual(self.remove("strategies",latest).status_code,204)
        room=self.client.get(f'/api/research/sessions/{f.room["id"]}').json()
        self.assertIsNone(room["selected_strategy_id"])
        self.assertEqual([v["id"] for v in room["versions"]],[second])
        self.assertIsNone(room["turns"][-1]["strategy_id"])
        self.assertIsNone(room["turns"][-1]["response"]["strategy"])
        self.assertTrue(room["turns"][-1]["response"]["reply"])

    def test_pending_ai_request_blocks_deletion_without_spending(self):
        f=self.f;f.key();self.assertEqual(f.approve(f.prepare()).status_code,200)
        strategy=self.db.scalar(select(Strategy.id).where(Strategy.user_id==self.owner))
        pending=f.prepare()
        self.assertEqual(self.remove("strategies",strategy).status_code,409)
        self.assertEqual(f.provider.call_count,1)
        self.client.post(f'/api/research/turns/{pending["id"]}/cancel')
        self.assertEqual(self.remove("strategies",strategy).status_code,204)
        self.assertEqual(f.provider.call_count,1)

    def test_deployment_replay_cannot_recreate_deleted_account(self):
        f=self.f;f.key();self.assertEqual(f.approve(f.prepare()).status_code,200)
        strategy=self.db.scalar(select(Strategy.id).where(Strategy.user_id==self.owner))
        account=self.account(strategy)
        body={"strategy_id":strategy,"name":"Delete fixture","request_id":"deployment-replay-0001"}
        self.db.add(ResearchDeployment(session_id=f.room["id"],strategy_id=strategy,account_id=account,request_id=body["request_id"]));self.db.commit()
        self.assertEqual(self.remove("accounts",account).status_code,204)
        result=self.client.post(f'/api/research/sessions/{f.room["id"]}/deploy',json=body)
        self.assertEqual(result.status_code,409,result.text)
        self.assertIn("삭제",result.json()["detail"])
        self.assertEqual(self.db.scalar(select(func.count()).select_from(PaperAccount)),0)

    def test_deleting_experiment_candidate_invalidates_comparison(self):
        f=self.f;f.key();body,_,_=f.build_experiment(2)
        target=body["strategy_ids"][0]
        self.assertEqual(self.remove("strategies",target).status_code,204)
        room=self.client.get(f'/api/research/sessions/{f.room["id"]}').json()
        experiment=room["experiments"][0]
        self.assertEqual(experiment["status"],"invalidated")
        self.assertIsNone(experiment["development_leader"])
        self.assertIn("삭제",experiment["caveat"])


class DeleteWhileQuotingTests(unittest.TestCase):
    def test_deleted_account_cannot_receive_a_late_fill(self):
        f=continuous.ContinuousPaperTests();f.setUp();self.addCleanup(f.tearDown)
        def remove_during_http():
            with f.sessions() as db: resources.delete_account(db,f.owner,f.account)
        f.on_prices=remove_during_http
        f.tick()
        with f.sessions() as db:
            self.assertIsNone(db.get(PaperAccount,f.account))
            for model in (PaperPosition,PaperFill,EquityPoint):
                self.assertEqual(db.scalar(select(func.count()).select_from(model).where(model.account_id==f.account)),0)
            self.assertEqual(db.scalar(select(func.count()).select_from(PaperFill).where(PaperFill.account_id==f.daily_account)),2)
        f.tick()
        with f.sessions() as db:self.assertIsNone(db.get(PaperAccount,f.account))
