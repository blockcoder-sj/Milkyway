"""Focused regressions for the sealed scan's grouped Medium findings.

The suite exercises local enforcement boundaries.  It deliberately does not
claim real provider, PostgreSQL, encrypted-restore, OCI IAM/KMS, or Audit
evidence.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import signal
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("APP_ENV", "development")

from cloud_app import config as config_module
from cloud_app import data_refresh as refresh_module
from cloud_app import credential_broker as broker_module
from cloud_app import credential_store as credential_store_module
from cloud_app import main as main_module
from cloud_app import strategies as strategies_module
from cloud_app import worker as worker_module
from cloud_app.bounded_io import (
    FileReadBudget, ResponseTooLarge, read_bounded_file, read_httpx_json,
)
from cloud_app.database import (
    Base,
    BacktestJob,
    Invitation,
    PaperAccount,
    Strategy,
    User,
    WorkCursor,
)
from cloud_app.security import hash_password, password_needs_rehash
from deploy.encrypted_backup import decrypt as decrypt_backup
from deploy.encrypted_backup import encrypt as encrypt_backup
from terminal_events import validate_event
from universe_snapshot import SnapshotAggregateBudgetExceeded

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SharedModeStartupTests(unittest.TestCase):
    def test_shared_backend_is_a_valid_non_encryption_mode(self):
        settings = SimpleNamespace(production=True, credential_backend="shared")
        credential_store_module.validate_credential_backend(settings)
        with self.assertRaises(RuntimeError):
            credential_store_module.encrypt_credential("secret", settings)

    def test_shared_mode_skips_legacy_tables_before_opening_a_session(self):
        with patch.object(
            main_module, "settings", replace(main_module.settings, member_credentials_enabled=False)
        ), patch.object(main_module, "SessionLocal") as session_factory:
            main_module._migrate_legacy_credentials()
        session_factory.assert_not_called()

    def test_kis_quote_freshness_configuration_rejects_multi_batch_ticks(self):
        base = config_module.get_settings()
        settings = replace(
            base,
            app_env="production",
            quote_provider="kis",
            market_data_sharing_allowed=True,
            shared_quote_batch_size=200,
            shared_quote_max_symbols_per_tick=400,
            shared_quote_tick_deadline_seconds=30,
            quote_interval_seconds=10,
            quote_max_age_seconds=180,
        )
        self.assertTrue(
            any(
                "exactly one broker batch" in error
                for error in settings.startup_errors("paper")
            )
        )

    def test_kis_quote_age_must_exceed_the_complete_tick_bound(self):
        base = config_module.get_settings()
        settings = replace(
            base,
            app_env="production",
            quote_provider="kis",
            market_data_sharing_allowed=True,
            shared_quote_batch_size=40,
            shared_quote_max_symbols_per_tick=40,
            shared_quote_tick_deadline_seconds=30,
            quote_interval_seconds=10,
            quote_max_age_seconds=31,
        )
        self.assertTrue(
            any(
                "must exceed the complete paper tick" in error
                for error in settings.startup_errors("paper")
            )
        )


class SecretValidationTests(unittest.TestCase):
    def test_reserved_placeholder_namespace_is_always_weak(self):
        for value in (
            "replace-with-a-real-server-side-provider-key",
            " REPLACE-WITH-32-PLUS-RANDOM-CHARACTERS ",
            "local-ai-not-configured",
        ):
            with self.subTest(value=value):
                self.assertTrue(config_module._weak_secret(value, 20))

    def test_broker_tokens_cannot_equal_provider_secrets(self):
        base = config_module.get_settings()
        shared = "zK4r9-pS2vX7mQ8dL1hN6cT3yW5uA0bE"
        settings = replace(
            base,
            app_env="production",
            credential_backend="shared",
            member_credentials_enabled=False,
            credential_broker_app_token=shared,
            credential_broker_paper_token="Q8pV4nL7sR2xM9cD5tY1kH6wB3jF0aUe",
            shared_ai_enabled=True,
            shared_ai_provider="openai",
            shared_ai_model="gpt-5",
            shared_ai_api_key=shared,
            quote_provider="mock",
            local_ai_enabled=False,
        )
        errors = settings.startup_errors("broker")
        self.assertTrue(any("independent" in item for item in errors), errors)

    def test_provider_secret_file_rejects_ambiguity_symlinks_and_open_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = root / "provider-key"
            secret.write_text("server-owned-provider-key-0123456789\n", encoding="utf-8")
            secret.chmod(0o600)
            environment = {"TEST_PROVIDER_SECRET_FILE": str(secret)}
            with patch.dict(os.environ, environment, clear=True):
                self.assertEqual(
                    config_module._secret("TEST_PROVIDER_SECRET"),
                    "server-owned-provider-key-0123456789",
                )
            with patch.dict(
                os.environ,
                {
                    "TEST_PROVIDER_SECRET": "raw-secret",
                    "TEST_PROVIDER_SECRET_FILE": str(secret),
                },
                clear=True,
            ):
                with self.assertRaises(RuntimeError):
                    config_module._secret("TEST_PROVIDER_SECRET")
            link = root / "provider-link"
            link.symlink_to(secret)
            with patch.dict(
                os.environ,
                {"TEST_PROVIDER_SECRET_FILE": str(link)},
                clear=True,
            ):
                with self.assertRaises(OSError):
                    config_module._secret("TEST_PROVIDER_SECRET")
            secret.chmod(0o644)
            with patch.dict(os.environ, environment, clear=True):
                with self.assertRaises(RuntimeError):
                    config_module._secret("TEST_PROVIDER_SECRET")


class AuthenticationAndEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()
        with main_module._attempt_lock:
            main_module._attempts.clear()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_hostile_account_pressure_does_not_block_correct_password(self):
        user = User(
            id="a" * 32,
            email="member@example.com",
            display_name="Member",
            password_hash=hash_password("correct horse battery staple"),
        )
        self.session.add(user)
        self.session.commit()
        for index in range(main_module.settings.login_account_attempts):
            with self.assertRaises(HTTPException):
                main_module.login(
                    main_module.LoginBody(email=user.email, password="wrong password"),
                    SimpleNamespace(
                        client=SimpleNamespace(host="198.51.100.{}".format(index + 1))
                    ),
                    Response(),
                    self.session,
                )
        result = main_module.login(
            main_module.LoginBody(
                email=user.email, password="correct horse battery staple"
            ),
            SimpleNamespace(client=SimpleNamespace(host="203.0.113.9")),
            Response(),
            self.session,
        )
        self.assertEqual(result["user"]["id"], user.id)

    def test_one_time_email_bound_invitation_is_consumed_once(self):
        token = "single-use-invitation-token-0001"
        invitation = Invitation.create(
            token=token,
            email="invitee@example.com",
            expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
            secret=main_module.settings.session_secret,
        )
        self.session.add(invitation)
        self.session.commit()
        request = SimpleNamespace(client=SimpleNamespace(host="198.51.100.44"))
        result = main_module.register(
            main_module.RegisterBody(
                email="invitee@example.com",
                display_name="Invitee",
                password="a sufficiently long password",
                invite_code=token,
            ),
            request,
            Response(),
            self.session,
        )
        self.assertEqual(result["user"]["email"], "invitee@example.com")
        with self.assertRaises(HTTPException) as raised:
            main_module.register(
                main_module.RegisterBody(
                    email="other@example.com",
                    display_name="Other",
                    password="another sufficiently long password",
                    invite_code=token,
                ),
                request,
                Response(),
                self.session,
            )
        self.assertEqual(raised.exception.status_code, 403)

    def test_legacy_password_hash_is_upgraded_after_success(self):
        legacy = hash_password(
            "correct horse battery staple", n=2**14, r=8, p=1
        )
        self.assertTrue(password_needs_rehash(legacy))


class BrokerAdmissionTests(unittest.TestCase):
    def test_shared_ai_capacity_is_admitted_before_budget_is_charged(self):
        slots = MagicMock()
        slots.acquire.return_value = False
        with patch.object(broker_module, "_ai_slots", slots), patch.object(
            broker_module, "_rate_limit"
        ) as rate_limit:
            with self.assertRaises(HTTPException) as raised:
                broker_module.shared_ai_generate(
                    broker_module.SharedAiGenerateBody(prompt="build a safe strategy"),
                    "app",
                )
        self.assertEqual(raised.exception.status_code, 429)
        rate_limit.assert_not_called()

    def test_shared_quote_batch_is_bounded_by_authoritative_broker_limit(self):
        values = ["T{:03d}".format(index) for index in range(41)]
        with self.assertRaises(ValueError):
            broker_module._normalized_tickers(values, maximum=40)

    def test_shared_quote_rate_budget_covers_the_configured_worker_cadence(self):
        with patch.object(
            broker_module,
            "settings",
            SimpleNamespace(
                shared_quote_max_symbols_per_tick=40,
                shared_quote_batch_size=40,
                quote_interval_seconds=10,
            ),
        ):
            self.assertEqual(broker_module._shared_quote_rate_budget(), 7)


class QueueAndQuoteFairnessTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_quote_cursor_eventually_serves_suffix_symbols(self):
        tickers = tuple("T{:03d}".format(index) for index in range(100))
        batches = [
            worker_module._rotating_work_slice(
                self.session, "quotes", tickers, 40
            )
            for _ in range(3)
        ]
        self.assertEqual(set().union(*map(set, batches)), set(tickers))
        cursor = self.session.get(WorkCursor, "quotes")
        self.assertIsNotNone(cursor)

    def test_complete_paper_tick_has_a_hard_deadline(self):
        with self.assertRaises(worker_module.PaperTickDeadlineExceeded):
            with worker_module._paper_tick_deadline(30):
                signal.raise_signal(signal.SIGALRM)

    def test_quote_cursor_advance_survives_provider_failure(self):
        factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        runtime_session = factory()
        provider = MagicMock()
        provider.fetch.side_effect = RuntimeError("provider unavailable")
        settings = SimpleNamespace(shared_quote_max_symbols_per_tick=1)
        with patch.object(worker_module, "SessionLocal", return_value=runtime_session), patch.object(
            worker_module, "acquire_lease", return_value=True
        ), patch.object(
            worker_module, "apply_terminal_events", return_value={"settled": 0, "review_accounts": 0}
        ), patch.object(
            worker_module, "regular_market_open", return_value=True
        ), patch.object(
            worker_module, "collect_watchlist_ordered", return_value=("AAA", "BBB")
        ), patch.object(
            worker_module, "collect_holding_watchlist_ordered", return_value=()
        ):
            worker_module.run_paper_tick(provider, settings)
        verification = factory()
        try:
            cursor = verification.get(WorkCursor, "shared-quote-worklist")
            self.assertEqual(cursor.position, 1)
        finally:
            verification.close()

    def test_saturated_holdings_do_not_permanently_exclude_candidates(self):
        batches = [
            worker_module._fair_quote_work_slice(
                self.session,
                ("H1", "H2"),
                ("C1", "C2"),
                2,
            )
            for _ in range(2)
        ]
        self.assertEqual(set().union(*map(set, batches)), {"H1", "H2", "C1", "C2"})

    def test_single_quote_slot_alternates_holdings_and_candidates(self):
        batches = [
            worker_module._fair_quote_work_slice(
                self.session,
                ("H1", "H2"),
                ("C1", "C2"),
                1,
            )
            for _ in range(4)
        ]
        self.assertEqual(set().union(*map(set, batches)), {"H1", "H2", "C1", "C2"})

    def test_capacity_edge_is_fully_served_inside_the_freshness_window(self):
        # Defaults use a 30-second worst-case tick plus the loop's one-second
        # sleep. Five complete 40-symbol batches fit inside the 180-second age.
        holdings = tuple("H{:03d}".format(index) for index in range(98))
        candidates = tuple("C{:03d}".format(index) for index in range(102))
        batches = [
            worker_module._fair_quote_work_slice(
                self.session,
                holdings,
                candidates,
                40,
            )
            for _ in range(5)
        ]
        self.assertEqual(
            set().union(*map(set, batches)),
            set(holdings) | set(candidates),
        )

    def test_backtest_claim_rotates_between_owners(self):
        now = dt.datetime.now(dt.timezone.utc)
        for index, owner in enumerate(("a", "a", "b", "b")):
            self.session.add(
                BacktestJob(
                    id=(str(index) * 32),
                    user_id=(owner * 32),
                    strategy_id=(("c" if owner == "a" else "d") * 32),
                    start_date=dt.date(2026, 1, 1),
                    end_date=dt.date(2026, 1, 2),
                    created_at=now + dt.timedelta(seconds=index),
                )
            )
        self.session.commit()
        first = worker_module.claim_backtest(self.session)
        second = worker_module.claim_backtest(self.session)
        self.assertNotEqual(first.user_id, second.user_id)

    def test_worker_prunes_completed_results_without_a_new_submission(self):
        now = dt.datetime.now(dt.timezone.utc)
        for index in range(3):
            self.session.add(
                BacktestJob(
                    id=(str(index + 1) * 32),
                    user_id=("p" * 32),
                    strategy_id=("s" * 32),
                    status="completed",
                    start_date=dt.date(2026, 1, 1),
                    end_date=dt.date(2026, 1, 2),
                    result_json="{}",
                    created_at=now - dt.timedelta(days=index),
                    finished_at=now - dt.timedelta(days=index),
                )
            )
        self.session.commit()
        worker_module._prune_backtest_results(
            self.session,
            "p" * 32,
            SimpleNamespace(
                backtest_retention_days=30,
                max_completed_backtests_per_user=2,
            ),
        )
        self.session.commit()
        remaining = self.session.query(BacktestJob).count()
        self.assertEqual(remaining, 2)


class AuxiliaryFileBudgetTests(unittest.TestCase):
    def test_invalid_snapshots_consume_the_budget_in_both_collection_callers(self):
        for invalid in (b"not-json", b"\xff" * 8, b'{"records": [], "membership_sha256": "bad"}'):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "a.json").write_bytes(invalid)
                (root / "b.json").write_bytes(invalid)
                with patch.object(strategies_module, "MAX_CERTIFIED_SNAPSHOT_BYTES", len(invalid)):
                    with self.assertRaises(SnapshotAggregateBudgetExceeded):
                        strategies_module._load_certified_snapshots(str(root / "*.json"))
                settings = SimpleNamespace(snapshots_glob=str(root / "*.json"))
                with patch.object(refresh_module, "MAX_PRIOR_SNAPSHOT_BYTES", len(invalid)), patch.object(
                    refresh_module, "get_settings", return_value=settings
                ), patch.object(
                    refresh_module, "fetch_official_sources",
                    return_value={"nasdaqlisted.txt": "", "otherlisted.txt": ""},
                ), patch.object(refresh_module, "build_snapshot", return_value={}), patch.object(
                    refresh_module, "save_snapshot"
                ) as save:
                    with self.assertRaises(SnapshotAggregateBudgetExceeded):
                        refresh_module.run_daily_refresh()
                    save.assert_not_called()

    def test_failed_generation_check_does_not_refund_captured_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "snapshot")
            path.write_bytes(b"12345678")
            before = path.stat()
            after = SimpleNamespace(
                st_dev=before.st_dev, st_ino=before.st_ino,
                st_size=before.st_size, st_mtime_ns=before.st_mtime_ns + 1,
            )
            budget = FileReadBudget(8)
            with patch("cloud_app.bounded_io.os.fstat", side_effect=[before, after]):
                with self.assertRaisesRegex(ValueError, "changed"):
                    read_bounded_file(path, maximum_bytes=100, budget=budget)
            self.assertEqual(budget.remaining, 0)

    def test_concurrent_growth_cannot_read_ahead_of_the_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "snapshot")
            path.write_bytes(b"x")
            real_fstat = os.fstat
            positions = []

            def changing_fstat(descriptor):
                metadata = real_fstat(descriptor)
                positions.append(os.lseek(descriptor, 0, os.SEEK_CUR))
                if len(positions) == 1:
                    with path.open("ab") as writer:
                        writer.write(b"x" * 65535)
                return metadata

            budget = FileReadBudget(1)
            with patch("cloud_app.bounded_io.os.fstat", side_effect=changing_fstat):
                with self.assertRaisesRegex(ValueError, "changed"):
                    read_bounded_file(path, maximum_bytes=100000, budget=budget)
            self.assertEqual(positions, [0, 1])
            self.assertEqual(budget.remaining, 0)

    def test_valid_snapshots_at_exact_budget_and_invalid_skip_within_budget(self):
        import hashlib

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.json").write_bytes(b"invalid")
            payload = {
                "records": [], "membership_sha256": hashlib.sha256(b"[]").hexdigest(),
                "certification_eligible": True, "effective_date": "2026-01-01",
                "captured_at_utc": "2026-01-01T00:00:00Z",
            }
            (root / "b.json").write_text(json.dumps(payload))
            payload["captured_at_utc"] = "2026-01-01T01:00:00Z"
            (root / "c.json").write_text(json.dumps(payload))
            size = sum(path.stat().st_size for path in root.iterdir())
            with patch.object(strategies_module, "MAX_CERTIFIED_SNAPSHOT_BYTES", size):
                self.assertEqual(strategies_module._load_certified_snapshots(str(root / "*.json")), [payload])

    def test_certified_snapshots_have_an_exact_aggregate_byte_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "a.json"
            second = root / "b.json"
            payload = json.dumps(
                {
                    "records": [],
                    "membership_sha256": (
                        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
                    ),
                    "certification_eligible": True,
                    "effective_date": "2026-01-01",
                }
            )
            first.write_text(payload)
            second.write_text(payload)
            with patch.object(
                strategies_module,
                "MAX_CERTIFIED_SNAPSHOT_BYTES",
                len(payload.encode("utf-8")),
            ):
                with self.assertRaises(SnapshotAggregateBudgetExceeded):
                    strategies_module._load_certified_snapshots(str(root / "*.json"))


class QuoteReactivationCapacityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()
        self.user = User(
            id="9" * 32,
            email="reactivate@example.com",
            display_name="Reactivate",
            password_hash="x",
        )
        self.session.add(self.user)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    @staticmethod
    def _spec(max_positions: int) -> str:
        return json.dumps(
            {
                "schema_version": 1,
                "name": "Capacity strategy",
                "description": "",
                "factors": [
                    {"kind": "momentum", "lookback": 20, "weight": 1.0}
                ],
                "portfolio": {"max_positions": max_positions},
            }
        )

    def _account(self, suffix: str, max_positions: int, status: str) -> PaperAccount:
        strategy = Strategy(
            id=(suffix * 32),
            user_id=self.user.id,
            name="Strategy " + suffix,
            spec_json=self._spec(max_positions),
        )
        account = PaperAccount(
            id=((suffix.lower()) * 32),
            user_id=self.user.id,
            strategy_id=strategy.id,
            name="Account " + suffix,
            status=status,
            initial_cash=1000,
            cash=1000,
        )
        self.session.add_all((strategy, account))
        return account

    def _kis_settings(self):
        return replace(
            main_module.settings,
            quote_provider="kis",
            quote_interval_seconds=10,
            shared_quote_batch_size=40,
            shared_quote_max_symbols_per_tick=40,
            shared_quote_tick_deadline_seconds=30,
            quote_max_age_seconds=180,
        )

    def test_reactivation_is_denied_when_freshness_capacity_is_full(self):
        self._account("A", 50, "active")
        self._account("B", 48, "active")
        paused = self._account("C", 1, "paused")
        self.session.commit()
        with patch.object(main_module, "settings", self._kis_settings()):
            with self.assertRaises(HTTPException) as raised:
                main_module.update_account(
                    paused.id,
                    main_module.StatusBody(status="active"),
                    self.user,
                    self.session,
                )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(paused.status, "paused")

    def test_reactivation_succeeds_at_the_exact_freshness_capacity(self):
        self._account("D", 50, "active")
        self._account("E", 47, "active")
        paused = self._account("F", 1, "paused")
        self.session.commit()
        with patch.object(
            main_module, "settings", self._kis_settings()
        ), patch.object(
            main_module,
            "account_snapshot",
            return_value={"status": "active"},
        ):
            result = main_module.update_account(
                paused.id,
                main_module.StatusBody(status="active"),
                self.user,
                self.session,
            )
        self.assertEqual(result["status"], "active")
        self.assertEqual(paused.status, "active")


class DatabaseOwnershipConstraintTests(unittest.TestCase):
    def test_job_and_account_cannot_reference_another_users_strategy(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            Base.metadata.create_all(connection)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        try:
            first = User(
                id="1" * 32,
                email="first@example.com",
                display_name="First",
                password_hash="x",
            )
            second = User(
                id="2" * 32,
                email="second@example.com",
                display_name="Second",
                password_hash="x",
            )
            strategy = Strategy(
                id="3" * 32,
                user_id=first.id,
                name="First strategy",
                spec_json="{}",
            )
            session.add_all((first, second, strategy))
            session.commit()
            for row in (
                BacktestJob(
                    user_id=second.id,
                    strategy_id=strategy.id,
                    start_date=dt.date(2026, 1, 1),
                    end_date=dt.date(2026, 1, 2),
                ),
                PaperAccount(
                    user_id=second.id,
                    strategy_id=strategy.id,
                    name="Mismatched",
                    initial_cash=1000,
                    cash=1000,
                ),
            ):
                session.add(row)
                with self.assertRaises(IntegrityError):
                    session.commit()
                session.rollback()
        finally:
            session.close()
            engine.dispose()


class BoundedIoTests(unittest.TestCase):
    def test_httpx_response_is_rejected_while_streaming(self):
        response = MagicMock()
        response.headers = {}
        response.iter_bytes.return_value = iter((b"{" + b"x" * 8, b"y" * 8 + b"}"))
        with self.assertRaises(ResponseTooLarge):
            read_httpx_json(response, maximum_bytes=12)
        response.close.assert_called_once()

    def test_auxiliary_reader_rejects_symlink_and_oversize(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text(json.dumps({"items": []}), encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaises(OSError):
                read_bounded_file(link, maximum_bytes=1024)
            with self.assertRaises(ValueError):
                read_bounded_file(target, maximum_bytes=2)


class DeploymentContractTests(unittest.TestCase):
    def test_ci_actions_are_immutable_and_permissions_are_read_only(self):
        workflow = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        for line in workflow.splitlines():
            if "uses:" not in line:
                continue
            reference = line.split("uses:", 1)[1].strip().split(" #", 1)[0]
            self.assertRegex(reference, r"^[^@]+@[0-9a-f]{40}$")

    def test_deployment_docs_never_render_real_secret_files(self):
        guide = (PROJECT_ROOT / "CLOUD_DEPLOYMENT.md").read_text(encoding="utf-8")
        for line in guide.splitlines():
            if "docker compose" in line and " config" in line:
                self.assertIn("--quiet", line)

    def test_runtime_grants_are_explicit_and_have_no_future_table_dml(self):
        grants = (PROJECT_ROOT / "deploy/postgres/runtime-roles.sql").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES", grants)
        # Historical broad defaults must be revoked during an upgrade.
        self.assertNotRegex(grants, r"ALTER DEFAULT PRIVILEGES[^;]*\bGRANT\b")
        self.assertNotIn("GRANT SELECT, INSERT, UPDATE ON users", grants)
        self.assertNotIn("GRANT SELECT, INSERT, DELETE ON backtest_jobs TO milkyway_app", grants)
        self.assertIn("GRANT UPDATE (status) ON paper_accounts TO milkyway_app", grants)
        self.assertIn("GRANT UPDATE (password_hash) ON users TO milkyway_app", grants)

    def test_backup_publishes_ciphertext_only_and_restore_is_separate(self):
        backup = (PROJECT_ROOT / "deploy/backup.sh").read_text(encoding="utf-8")
        compose = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")
        restore = (PROJECT_ROOT / "compose.restore.yaml").read_text(encoding="utf-8")
        self.assertIn("encrypted_backup.py encrypt", backup)
        self.assertNotIn("./deploy/restore.sh:/restore.sh", compose)
        self.assertIn("BACKUP_PRIVATE_KEY_PATH", restore)

    def test_scheduler_can_write_only_staging_and_not_published_data(self):
        compose = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("${PROMOTED_DATA_PATH:?set PROMOTED_DATA_PATH", compose)
        self.assertIn("${STAGING_DATA_PATH:?set STAGING_DATA_PATH}:/app/data_cache", compose)
        promoter = (PROJECT_ROOT / "cloud_app/promote_data.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("REVIEWED_SOURCE_PROVENANCE", promoter)
        self.assertIn("approved_manifest_sha256", promoter)

    def test_verified_terminal_events_reject_nonfinite_values(self):
        base = {
            "ticker": "AAPL",
            "effective_date": "2026-01-02",
            "event_type": "liquidation",
            "status": "verified",
            "source": "operator evidence",
        }
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_event({**base, "cash_per_share": value})

    def test_external_provider_secrets_use_vault_identifiers_without_file_mounts(self):
        compose = (PROJECT_ROOT / "compose.credential-broker.yaml").read_text(
            encoding="utf-8"
        )
        for name in ("SHARED_AI_API_KEY", "BROKER_API_KEY", "BROKER_API_SECRET"):
            self.assertNotIn("{}: ${{{}".format(name, name), compose)
            self.assertNotIn(name + "_FILE", compose)
        for identifier in ("OCI_SHARED_AI_SECRET_ID", "OCI_BROKER_API_KEY_SECRET_ID", "OCI_BROKER_API_SECRET_SECRET_ID"):
            self.assertIn(identifier, compose)


class EncryptedBackupTests(unittest.TestCase):
    def test_round_trip_tamper_rejection_and_existing_output_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=3072
            )
            private_path = root / "private.pem"
            public_path = root / "public.pem"
            private_path.write_bytes(
                private_key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            public_path.write_bytes(
                private_key.public_key().public_bytes(
                    serialization.Encoding.PEM,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )
            private_path.chmod(0o600)
            public_path.chmod(0o600)
            plaintext = root / "database.dump"
            encrypted = root / "database.mwbak"
            restored = root / "restored.dump"
            plaintext.write_bytes(b"postgres-custom-format-test" * 100)
            encrypt_backup(plaintext, encrypted, public_path)
            self.assertNotIn(plaintext.read_bytes(), encrypted.read_bytes())
            decrypt_backup(encrypted, restored, private_path)
            self.assertEqual(restored.read_bytes(), plaintext.read_bytes())

            tampered = root / "tampered.mwbak"
            damaged = bytearray(encrypted.read_bytes())
            damaged[-1] ^= 1
            tampered.write_bytes(damaged)
            rejected_output = root / "rejected.dump"
            with self.assertRaises(Exception):
                decrypt_backup(tampered, rejected_output, private_path)
            self.assertFalse(rejected_output.exists())

            sentinel = root / "sentinel.mwbak"
            sentinel.write_bytes(b"must-not-be-removed")
            with self.assertRaises(FileExistsError):
                encrypt_backup(plaintext, sentinel, public_path)
            self.assertEqual(sentinel.read_bytes(), b"must-not-be-removed")


if __name__ == "__main__":
    unittest.main()
