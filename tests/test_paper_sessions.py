"""Offline checks for one-session operation; no broker/AI/network calls."""
import datetime as dt
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cloud_app import main, paper, worker
from cloud_app.database import Base, EquityPoint, PaperAccount, PaperFill, PaperPosition, Strategy, User
from cloud_app.paper_sessions import expire_sessions, session_allows_execution, session_bounds, session_payload
from cloud_app.research_models import PersonalPaperSession, ResearchBase
from cloud_app.strategies import StrategySpec

UTC = dt.timezone.utc


class PaperSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine("sqlite:///" + str(Path(self.temp.name) / "paper.db"))
        Base.metadata.create_all(self.engine)
        ResearchBase.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.db = self.factory()
        self.now = dt.datetime(2026, 10, 2, 12, tzinfo=UTC)
        self.settings = replace(main.settings, personal_local_mode=True, app_env="development",
                                authority_enabled=False, quote_provider="member")
        self.patches = [patch.object(main, "settings", self.settings),
                        patch.object(main, "utcnow", side_effect=lambda: self.now),
                        patch.object(paper, "get_settings", return_value=self.settings),
                        patch.object(paper, "utcnow", side_effect=lambda: self.now),
                        patch.object(worker, "utcnow", side_effect=lambda: self.now),
                        patch.object(worker, "SessionLocal", self.factory)]
        for item in self.patches:
            item.start()
        self.user = User(email="owner@example.test", display_name="owner", password_hash="unused")
        self.other = User(email="other@example.test", display_name="other", password_hash="unused")
        self.db.add_all([self.user, self.other]); self.db.flush()
        spec = StrategySpec(name="session test", symbols=["AAA"], factors=[{"kind": "momentum"}], portfolio={"max_positions": 1})
        self.strategy = Strategy(user_id=self.user.id, name=spec.name, spec_json=spec.model_dump_json())
        self.db.add(self.strategy); self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def create(self, day=dt.date(2026, 10, 2)):
        data = main.create_account(main.AccountBody(strategy_id=self.strategy.id, name="one day", session_date=day), self.user, self.db)
        return self.db.get(PaperAccount, data["id"])

    def test_bounds_respect_dst_and_early_closes(self):
        self.assertEqual(session_bounds(self.now.date(), self.now),
                         (dt.datetime(2026, 10, 2, 13, 30, tzinfo=UTC), dt.datetime(2026, 10, 2, 20, tzinfo=UTC)))
        winter = dt.datetime(2026, 11, 27, 12, tzinfo=UTC)
        self.assertEqual(session_bounds(winter.date(), winter),
                         (dt.datetime(2026, 11, 27, 14, 30, tzinfo=UTC), dt.datetime(2026, 11, 27, 18, tzinfo=UTC)))

    def test_invalid_or_expired_dates_rejected_without_account(self):
        for day in [dt.date(2026, 10, 1), dt.date(2026, 10, 3), dt.date(2026, 10, 12)]:
            with self.assertRaises(HTTPException) as error:
                self.create(day)
            self.assertEqual(error.exception.status_code, 422)
        self.now = self.now.replace(hour=20)
        with self.assertRaises(HTTPException):
            self.create()
        self.assertEqual(self.db.scalars(select(PaperAccount)).all(), [])

    def test_owner_and_personal_only_creation(self):
        body = main.AccountBody(strategy_id=self.strategy.id, name="test", session_date=self.now.date())
        with self.assertRaises(HTTPException) as error:
            main.create_account(body, self.other, self.db)
        self.assertEqual(error.exception.status_code, 404)
        with patch.object(main, "settings", replace(self.settings, personal_local_mode=False)):
            with self.assertRaises(HTTPException) as error:
                main.create_account(body, self.user, self.db)
            self.assertEqual(error.exception.status_code, 422)
        route = next(r for r in main.app.routes if r.path == "/api/accounts" and "POST" in r.methods)
        self.assertIn(main.csrf_guard, [d.call for d in route.dependant.dependencies])

    def test_fills_guard_open_close_and_preserve_position_without_fake_sale(self):
        account = self.create()
        self.assertFalse(paper._fill(self.db, account, "AAA", "BUY", 10, 100, .001, "rebalance", "early"))
        self.now = self.now.replace(hour=13, minute=30)
        self.assertTrue(paper._fill(self.db, account, "AAA", "BUY", 10, 100, .001, "rebalance", "open"))
        self.db.commit()
        self.now = self.now.replace(hour=20, minute=0)
        self.assertFalse(paper._fill(self.db, account, "AAA", "SELL", 10, 95, .001, "stop_loss", "late"))
        self.assertFalse(paper._fill(self.db, account, "AAA", "BUY", 10, 100, .001, "rebalance", "late-buy"))
        self.db.commit()
        self.assertEqual(account.status, "paused")
        self.assertEqual(len(self.db.scalars(select(PaperFill)).all()), 1)
        self.assertEqual(self.db.scalar(select(PaperPosition.shares)), 10)
        summary = session_payload(self.db, account, self.now)["summary"]
        self.assertEqual(summary["fill_count"], 1)
        self.assertFalse(summary["closing_price_verified"])
        self.assertIsNone(summary["last_complete_valuation_at"])

    def test_missed_day_after_restart_is_completed_with_zero_fills(self):
        account = self.create(); account_id = account.id
        self.db.close()
        self.now += dt.timedelta(days=3)
        with self.factory() as restarted:
            self.assertEqual(expire_sessions(restarted, self.now), 1)
            restarted.commit()
            row = restarted.get(PaperAccount, account_id)
            first = session_payload(restarted, row, self.now)
            self.assertEqual(first["summary"]["fill_count"], 0)
            self.assertEqual(row.status, "paused")
            self.assertFalse(session_allows_execution(restarted, row, self.now))
            self.assertEqual(expire_sessions(restarted, self.now + dt.timedelta(hours=1)), 0)
            self.assertEqual(first, session_payload(restarted, row, self.now))

    def test_expiry_commits_before_later_worker_failure_even_when_market_closed(self):
        account = self.create(); account_id = account.id
        self.db.close(); self.now = self.now.replace(hour=21)
        provider = Mock()
        with patch.object(worker, "apply_personal_corporate_actions", side_effect=RuntimeError("offline fixture")), self.assertLogs("cloud_app.worker", level="ERROR"):
            worker.run_paper_tick(provider, self.settings)
        provider.fetch.assert_not_called()
        with self.factory() as restarted:
            self.assertEqual(restarted.get(PaperAccount, account_id).status, "paused")
            self.assertIsNotNone(restarted.get(PersonalPaperSession, account_id).completed_at)

    def test_future_day_never_executes_early_and_unscheduled_accounts_unchanged(self):
        scheduled = self.create(dt.date(2026, 10, 5))
        ordinary = self.create(None)
        self.now = self.now.replace(hour=15)
        self.assertFalse(session_allows_execution(self.db, scheduled, self.now))
        self.assertTrue(session_allows_execution(self.db, ordinary, self.now))
        self.assertIsNone(session_payload(self.db, ordinary, self.now))
        self.now += dt.timedelta(days=3)
        self.assertTrue(session_allows_execution(self.db, scheduled, self.now))

    def test_resume_rejects_expired_session_and_other_owner(self):
        account = self.create(); self.now = self.now.replace(hour=21)
        for actor, status in [(self.other, 404), (self.user, 409)]:
            with self.assertRaises(HTTPException) as error:
                main.update_account(account.id, main.StatusBody(status="active"), actor, self.db)
            self.assertEqual(error.exception.status_code, status)
        snapshot = paper.account_snapshot(self.db, account)
        self.assertEqual(snapshot["execution_status"], "session_finished")
        self.assertTrue(snapshot["paper_session"]["expired"])

    def test_last_observation_keeps_its_real_time_and_summary_is_immutable(self):
        account = self.create()
        seen = self.now.replace(hour=19, minute=50)
        self.db.add(EquityPoint(account_id=account.id, equity=100000, cash=100000, observed_at=seen))
        self.db.commit(); self.now = self.now.replace(hour=21)
        expire_sessions(self.db, self.now); self.db.commit()
        summary = session_payload(self.db, account, self.now)["summary"]
        self.assertEqual(summary["last_complete_valuation_at"], seen.isoformat())
        account.cash = 90000; self.db.commit()
        expire_sessions(self.db, self.now + dt.timedelta(days=3))
        self.assertEqual(summary, session_payload(self.db, account, self.now)["summary"])

    def test_session_is_created_in_same_transaction_as_account(self):
        body = main.AccountBody(strategy_id=self.strategy.id, name="rollback", session_date=self.now.date())
        with self.assertRaises(RuntimeError):
            with main._account_creation(body, self.user, self.db):
                raise RuntimeError("rollback before commit")
        self.db.rollback()
        self.assertEqual(self.db.scalars(select(PaperAccount)).all(), [])
        self.assertEqual(self.db.scalars(select(PersonalPaperSession)).all(), [])
