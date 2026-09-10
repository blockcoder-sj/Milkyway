import datetime as dt
import unittest
from dataclasses import replace
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cloud_app import work_authority as authority
from cloud_app.config import get_settings
from cloud_app.database import (
    AdmittedTicker, BacktestJob, Base, MarketDataConnection, PaperAccount,
    PaperPosition, Strategy, User, WorkClaim, WorkResource, utcnow,
)
from cloud_app.strategies import StrategySpec


class TrustedWorkTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()
        self.settings = replace(get_settings(), authority_enabled=True, member_credentials_enabled=True,
                                quote_max_concurrent_requests=2, shared_quote_batch_size=200)
        self.spec = StrategySpec(name="Trusted fixture", factors=[{"kind": "momentum"}])
        for i in range(2):
            owner = str(i + 1) * 32
            self.session.add(User(id=owner, email=f"member{i}@example.com", display_name="Member", password_hash="synthetic"))
            self.session.flush()
            self.session.add(Strategy(id=str(i + 3) * 32, user_id=owner, name="Fixture", spec_json=self.spec.model_dump_json()))
            self.session.add(MarketDataConnection(user_id=owner, provider="kis", environment="paper", encrypted_api_key="opaque-key", encrypted_api_secret="opaque-secret", key_hint="key", secret_hint="secret"))
            self.session.flush()
            for j in range(2):
                self.session.add(PaperAccount(id=f"{i}{j}" * 16, user_id=owner, strategy_id=str(i + 3) * 32, name="Fixture", initial_cash=1000, cash=1000))
        self.session.commit()
        self.market = patch.object(authority, "regular_market_open", return_value=True)
        self.bundle = patch.object(authority, "get_dataset_bundle", return_value=object())
        self.candidates = patch.object(authority, "latest_candidates", return_value=["AAPL", "MSFT"])
        for context in (self.market, self.bundle, self.candidates):
            context.start()
            self.addCleanup(context.stop)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_one_member_batch_has_exact_resources_and_replay_safe_quote_plan(self):
        work = authority.issue_work(self.session, self.settings, "paper")
        self.assertEqual(set(work), {"claim", "resource_id", "expires_at", "quotes_required"})
        claim = authority.claim_record(self.session, work["claim"], "paper")
        self.assertEqual(claim.user_id, "1" * 32)
        resources = self.session.scalars(select(WorkResource).where(WorkResource.claim_hash == claim.token_hash)).all()
        self.assertEqual({r.resource_id for r in resources}, {"00" * 16, "01" * 16})
        self.assertEqual({r.strategy_id for r in resources}, {"3" * 32})
        with self.assertRaises(HTTPException):
            authority.claim_record(self.session, work["claim"], "backtest")
        self.session.rollback()
        admitted = authority.consume_quote_work(self.session, self.settings, work["claim"])
        self.assertEqual(admitted.tickers_json, '["AAPL", "MSFT"]')
        with self.assertRaises(HTTPException):
            authority.consume_quote_work(self.session, self.settings, work["claim"])
        self.session.rollback()
        authority.complete_work(self.session, work["claim"], "paper")
        with self.assertRaises(HTTPException):
            authority.claim_record(self.session, work["claim"], "paper")
        self.session.rollback()
        next_work = authority.issue_work(self.session, self.settings, "paper")
        self.assertEqual(authority.claim_record(self.session, next_work["claim"], "paper").user_id, "2" * 32)

    def test_worker_written_symbols_cannot_manufacture_a_provider_quote_plan(self):
        self.session.add(PaperPosition(account_id="00" * 16, ticker="UNAPPROVED", shares=1, avg_price=1, last_price=1))
        self.session.commit()
        work = authority.issue_work(self.session, self.settings, "paper")
        self.assertEqual(self.session.get(PaperAccount, "00" * 16).status, "configuration_required")
        claim = authority.claim_record(self.session, work["claim"], "paper")
        self.assertNotIn("UNAPPROVED", claim.tickers_json)
        self.assertEqual(self.session.scalars(select(WorkResource.resource_id).where(WorkResource.claim_hash == claim.token_hash)).all(), ["01" * 16])

    def test_changed_credentials_disabled_member_and_expiry_revoke_work(self):
        work = authority.issue_work(self.session, self.settings, "paper")
        row = self.session.get(MarketDataConnection, "1" * 32)
        row.updated_at = utcnow() + dt.timedelta(seconds=1)
        self.session.commit()
        with self.assertRaises(HTTPException):
            authority.consume_quote_work(self.session, self.settings, work["claim"])
        self.session.rollback()
        user = self.session.get(User, "1" * 32)
        user.active = False
        self.session.commit()
        with self.assertRaises(HTTPException):
            authority.claim_record(self.session, work["claim"], "paper")
        user.active = True
        claim = self.session.get(WorkClaim, authority.token_hash(work["claim"]))
        claim.expires_at = utcnow() - dt.timedelta(seconds=1)
        self.session.commit()
        with self.assertRaises(HTTPException):
            authority.claim_record(self.session, work["claim"], "paper")

    def test_backtest_authority_selects_a_queued_job_once(self):
        self.session.add(BacktestJob(id="b" * 32, user_id="1" * 32, strategy_id="3" * 32,
            start_date=dt.date(2026, 1, 1), end_date=dt.date(2026, 2, 1), bias_mode="strict"))
        self.session.commit()
        work = authority.issue_work(self.session, self.settings, "backtest")
        self.assertEqual(work["resource_id"], "b" * 32)
        self.assertEqual(self.session.get(BacktestJob, "b" * 32).status, "running")
        self.assertIsNone(authority.issue_work(self.session, self.settings, "backtest"))
        authority.complete_work(self.session, work["claim"], "backtest")
        self.assertIsNone(authority.issue_work(self.session, self.settings, "backtest"))

    def test_malformed_member_strategy_does_not_roll_back_rotation(self):
        self.session.get(Strategy, "3" * 32).spec_json = '{"invalid":'
        self.session.commit()
        self.assertIsNone(authority.issue_work(self.session, self.settings, "paper"))
        self.assertEqual(self.session.get(PaperAccount, "00" * 16).status, "configuration_required")
        self.assertEqual(self.session.get(PaperAccount, "01" * 16).status, "configuration_required")
        # Even an app writer repeatedly reactivating its invalid account does
        # not reset the durable cursor or deprive the next member of service.
        self.session.get(PaperAccount, "00" * 16).status = "active"
        self.session.commit()
        work = authority.issue_work(self.session, self.settings, "paper")
        self.assertEqual(authority.claim_record(self.session, work["claim"], "paper").user_id, "2" * 32)

    def test_member_quote_capacity_overflow_quarantines_only_affected_accounts(self):
        self.settings = replace(self.settings, shared_quote_batch_size=1)
        self.candidates.stop()
        with patch.object(authority, "latest_candidates", side_effect=[["AAPL", "MSFT"], ["AAPL"], ["AAPL"], ["AAPL"]]):
            work = authority.issue_work(self.session, self.settings, "paper")
            self.assertEqual(self.session.get(PaperAccount, "00" * 16).status, "configuration_required")
            self.assertEqual(work["resource_id"], "01" * 16)
            authority.complete_work(self.session, work["claim"], "paper")
            work = authority.issue_work(self.session, self.settings, "paper")
            self.assertEqual(authority.claim_record(self.session, work["claim"], "paper").user_id, "2" * 32)

    def test_trusted_dataset_failure_remains_a_fail_closed_error(self):
        with patch.object(authority, "get_dataset_bundle", side_effect=ValueError("Unapproved dataset")):
            with self.assertRaisesRegex(ValueError, "Unapproved dataset"):
                authority.issue_work(self.session, self.settings, "paper")
        self.session.rollback()
        self.assertEqual(self.session.get(PaperAccount, "00" * 16).status, "active")
