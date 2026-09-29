"""Focused regressions for the sealed whole-repository Deep Security Scan.

These tests intentionally exercise the shared enforcement boundaries rather
than reproducing provider or OCI infrastructure.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import os
import pickle
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import yaml
from fastapi import HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud_app import config as config_module
from cloud_app import credential_broker as broker_module
from cloud_app import credential_store as credential_store_module
from cloud_app import main as main_module
from cloud_app.database import Base, User
from cloud_app.http_security import RequestBodyLimitMiddleware
from cloud_app.kis_quotes import KisCredentials, KisQuoteClient, KisWorkBudgetExceeded
from cloud_app.paper import _round_robin_unique
from cloud_app.security import hash_password
from cloud_app.strategies import DashboardDataset
from cloud_app.worker import (
    CredentialBrokerSharedQuoteProvider,
    collect_member_quotes as collect_worker_member_quotes,
)
from price_data_pipeline import (
    MAX_DATASET_SYMBOLS,
    PRICE_FORMAT,
    PRICE_SCHEMA_VERSION,
    read_price_frame,
    sha256_file,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("APP_ENV", "development")


def _materialize_pickle_marker(marker: str) -> pd.DataFrame:
    Path(marker).write_text("pickle executed", encoding="utf-8")
    return pd.DataFrame(
        {
            "Open": [10.0],
            "High": [11.0],
            "Low": [9.0],
            "Close": [10.5],
            "Volume": [100.0],
        },
        index=pd.to_datetime(["2026-01-02"]),
    )


class _MatchingHashPickle:
    def __init__(self, marker: Path):
        self.marker = str(marker)

    def __reduce__(self):
        return _materialize_pickle_marker, (self.marker,)


class DeploymentModeRegressionTests(unittest.TestCase):
    def tearDown(self):
        config_module.get_settings.cache_clear()

    def test_unknown_or_explicitly_empty_app_env_fails_during_settings_load(self):
        with patch.dict(os.environ, {}, clear=True):
            config_module.get_settings.cache_clear()
            with self.assertRaises((RuntimeError, ValueError)):
                config_module.get_settings()
        for value in ("prod", "prodution", "staging", "", "   "):
            with self.subTest(value=value), patch.dict(os.environ, {"APP_ENV": value}):
                config_module.get_settings.cache_clear()
                with self.assertRaises((RuntimeError, ValueError)):
                    config_module.get_settings()

    def test_production_compose_cannot_override_app_env(self):
        compose = yaml.safe_load((PROJECT_ROOT / "compose.yaml").read_text())
        self.assertEqual(compose["x-runtime-environment"]["APP_ENV"], "production")


class DatasetBoundaryRegressionTests(unittest.TestCase):
    def test_matching_hash_pickle_is_rejected_without_deserialization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prices = root / "prices"
            prices.mkdir()
            marker = root / "pickle-marker"
            price_path = prices / "EVIL_data.csv.gz"
            price_path.write_bytes(pickle.dumps(_MatchingHashPickle(marker)))
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": PRICE_SCHEMA_VERSION,
                        "price_format": PRICE_FORMAT,
                        "prices": {
                            "EVIL": {
                                "rows": 1,
                                "first_date": "2026-01-02",
                                "last_date": "2026-01-02",
                                "sha256": sha256_file(price_path),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            settings = SimpleNamespace(
                dataset_dir=root,
                snapshots_glob=str(root / "snapshots/*.json"),
            )
            snapshot = {
                "effective_date": "2026-01-02",
                "captured_at_utc": "2026-01-02T00:00:00+00:00",
                "membership_sha256": "a" * 64,
                "certification_eligible": True,
            }
            with patch("cloud_app.strategies._load_certified_snapshots", return_value=[snapshot]):
                with self.assertRaises(ValueError):
                    DashboardDataset(settings)
            self.assertFalse(marker.exists(), "a matching-hash pickle was executed")

    def test_runtime_dataset_boundary_contains_no_pickle_loader_or_writer(self):
        for relative in (
            "price_data_pipeline.py",
            "cloud_app/strategies.py",
            "cloud_app/preflight.py",
        ):
            source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("read_pickle", source, relative)
            self.assertNotIn("to_pickle", source, relative)

    def test_non_monotonic_price_dates_are_rejected_instead_of_sorted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AAPL_data.csv.gz"
            frame = pd.DataFrame(
                {
                    "Open": [10.0, 10.0],
                    "High": [11.0, 11.0],
                    "Low": [9.0, 9.0],
                    "Close": [10.0, 10.0],
                    "Volume": [100.0, 100.0],
                },
                index=pd.to_datetime(["2026-01-03", "2026-01-02"]),
            )
            frame.to_csv(
                path,
                index_label="Date",
                date_format="%Y-%m-%d",
                compression={"method": "gzip", "mtime": 0},
            )
            with self.assertRaisesRegex(ValueError, "strictly increasing"):
                read_price_frame(path, require_valid=True)

    def test_manifest_symbol_budget_fails_before_file_parsing(self):
        manifest = {
            "schema_version": PRICE_SCHEMA_VERSION,
            "price_format": PRICE_FORMAT,
            "prices": {
                "T{:04d}".format(index): {"rows": 1}
                for index in range(MAX_DATASET_SYMBOLS + 1)
            },
        }
        from price_data_pipeline import require_price_manifest

        with self.assertRaisesRegex(ValueError, "symbol limit"):
            require_price_manifest(manifest)


class RequestAdmissionRegressionTests(unittest.TestCase):
    def tearDown(self):
        with main_module._attempt_lock:
            main_module._attempts.clear()

    def test_rate_key_capacity_evicts_lru_instead_of_blocking_new_namespace(self):
        with patch.object(main_module, "_max_rate_limit_keys", 2):
            main_module._rate_limit("register:198.51.100.1", 5, 3600)
            main_module._rate_limit("register:198.51.100.2", 5, 3600)
            main_module._rate_limit("login:203.0.113.9", 10, 600)
        self.assertIn("login:203.0.113.9", main_module._attempts)

    def test_ipv6_privacy_addresses_share_a_documented_prefix_bucket(self):
        normalize = getattr(main_module, "_client_rate_identity", None)
        self.assertIsNotNone(normalize)
        self.assertEqual(normalize("2001:db8:abcd:1::1"), normalize("2001:db8:abcd:1::ffff"))
        self.assertNotEqual(normalize("2001:db8:abcd:1::1"), normalize("2001:db8:abcd:2::1"))

    def test_slow_body_times_out_before_endpoint_and_message_flood_is_bounded(self):
        async def slow_case():
            called = False
            sent = []
            first = True

            async def endpoint(_scope, _receive, _send):
                nonlocal called
                called = True

            async def receive():
                nonlocal first
                if first:
                    first = False
                    return {"type": "http.request", "body": b"{", "more_body": True}
                await asyncio.Event().wait()

            async def send(message):
                sent.append(message)

            middleware = RequestBodyLimitMiddleware(
                endpoint,
                1024,
                read_timeout_seconds=0.02,
                max_messages=4,
            )
            await middleware({"type": "http", "headers": []}, receive, send)
            return called, sent

        called, sent = asyncio.run(slow_case())
        self.assertFalse(called)
        self.assertEqual(sent[0]["status"], 408)

    def test_public_and_broker_servers_have_edge_and_uvicorn_admission_limits(self):
        for relative in ("deploy/Caddyfile", "deploy/credential-broker.Caddyfile"):
            source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("read_body", source)
            self.assertIn("read_header", source)
        for relative in ("compose.yaml", "compose.credential-broker.yaml"):
            source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("--limit-concurrency", source)
            self.assertIn("--backlog", source)


class DatabaseStateRegressionTests(unittest.TestCase):
    def test_all_quota_allocations_use_one_transaction_scoped_guard(self):
        for function in (
            main_module.register,
            main_module._strategy_creation,
            main_module.create_backtest,
            main_module._account_creation,
        ):
            self.assertIn("quota_allocation", inspect.getsource(function), function.__name__)

        self.assertIn("_strategy_creation", inspect.getsource(main_module._save_strategy))
        self.assertIn("_account_creation", inspect.getsource(main_module.create_account))
        quota_allocation = getattr(main_module, "quota_allocation", None)
        self.assertIsNotNone(quota_allocation)
        fake_session = MagicMock()
        fake_session.bind.dialect.name = "postgresql"
        with quota_allocation(fake_session, "test", "owner"):
            pass
        statement = str(fake_session.execute.call_args.args[0])
        self.assertIn("pg_advisory_xact_lock", statement)

    def test_distributed_guesses_share_a_durable_account_budget(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(
            id="d" * 32,
            email="victim@example.com",
            display_name="Victim",
            password_hash=hash_password("correct horse battery staple"),
        )
        session.add(user)
        session.commit()
        with main_module._attempt_lock:
            main_module._attempts.clear()
        for index in range(10):
            request = SimpleNamespace(client=SimpleNamespace(host="198.51.100.{}".format(index + 1)))
            with self.assertRaises(HTTPException) as raised:
                main_module.login(
                    main_module.LoginBody(email=user.email, password="wrong password"),
                    request,
                    Response(),
                    session,
                )
            self.assertEqual(raised.exception.status_code, 401)
        with self.assertRaises(HTTPException) as raised:
            main_module.login(
                main_module.LoginBody(email=user.email, password="wrong password"),
                SimpleNamespace(client=SimpleNamespace(host="203.0.113.99")),
                Response(),
                session,
            )
        self.assertEqual(raised.exception.status_code, 429)
        session.close()

    def test_stream_authentication_does_not_use_request_scoped_db_dependency(self):
        source = inspect.getsource(main_module.stream)
        self.assertNotIn("Depends(current_user)", source)
        self.assertIn("stream_principal", source)

    def test_compose_assigns_distinct_runtime_database_principals(self):
        compose = yaml.safe_load((PROJECT_ROOT / "compose.yaml").read_text())
        self.assertNotIn("DATABASE_URL", compose["x-runtime-environment"])
        urls = []
        for service in ("app", "paper-worker", "backtest-worker", "scheduler"):
            value = compose["services"][service]["environment"]["DATABASE_URL"]
            urls.append(value)
            self.assertNotEqual(value, "${DATABASE_URL:?set DATABASE_URL}")
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn("database-migrate", compose["services"])
        role_sql = PROJECT_ROOT / "deploy/postgres/runtime-roles.sql"
        self.assertTrue(role_sql.is_file())
        source = role_sql.read_text(encoding="utf-8")
        for role in ("milkyway_app", "milkyway_paper", "milkyway_backtest", "milkyway_scheduler"):
            self.assertIn(role, source)

    def test_production_runtime_verifies_schema_instead_of_creating_it(self):
        self.assertIn("prepare_runtime_database", inspect.getsource(main_module.startup))
        self.assertNotIn("initialize_database", inspect.getsource(main_module.startup))
        database_source = (PROJECT_ROOT / "cloud_app/database.py").read_text(encoding="utf-8")
        self.assertIn("if settings.production", database_source)
        self.assertIn("verify_database_schema()", database_source)


class BrokerResourceRegressionTests(unittest.TestCase):
    def test_shared_candidate_order_round_robins_tenants(self):
        ordered = _round_robin_unique(
            {
                "tenant-a": ["A{:03d}".format(index) for index in range(200)],
                "tenant-b": ["B000", "B001"],
            }
        )
        self.assertEqual(ordered[:4], ("A000", "B000", "A001", "B001"))

    def test_kis_provider_budget_rejects_before_network_call(self):
        client = KisQuoteClient(
            KisCredentials(api_key="key", api_secret="secret"),
            max_provider_calls=0,
        )
        with patch.object(client.session, "post") as request:
            with self.assertRaises(KisWorkBudgetExceeded):
                client.connect()
        request.assert_not_called()

    def test_quote_bulkhead_rejects_before_kms_or_provider_work(self):
        slots = MagicMock()
        slots.acquire.return_value = False
        body = broker_module.MarketQuotesBody(
            owner_id="owner",
            provider="kis",
            environment="paper",
            encrypted_api_key="cipher-key",
            encrypted_api_secret="cipher-secret",
            tickers=["AAPL"],
        )
        with patch.object(broker_module, "_quote_slots", slots, create=True), patch.object(
            broker_module, "_member_quotes"
        ) as member_quotes:
            with self.assertRaises(HTTPException) as raised:
                broker_module.market_quotes(body, "paper")
        self.assertEqual(raised.exception.status_code, 429)
        member_quotes.assert_not_called()

    def test_shared_watchlist_is_chunked_at_transport_boundary(self):
        settings = SimpleNamespace(shared_quote_batch_size=200)
        provider = CredentialBrokerSharedQuoteProvider(settings)
        tickers = ["T{:03d}".format(index) for index in range(401)]
        with patch("cloud_app.worker.broker_shared_quotes", return_value=[]) as request:
            provider.fetch(tickers)
        self.assertGreaterEqual(request.call_count, 3)
        for item in request.call_args_list:
            self.assertLessEqual(len(item.kwargs["tickers"]), 200)
            self.assertGreater(item.kwargs["timeout_seconds"], 0)
            self.assertLessEqual(item.kwargs["timeout_seconds"], 30)

    def test_shared_mode_skips_all_member_credential_and_quote_tables(self):
        session = MagicMock()
        self.assertEqual(
            collect_worker_member_quotes(
                session,
                SimpleNamespace(member_credentials_enabled=False),
            ),
            (0, 0),
        )
        session.scalars.assert_not_called()
        grants = Path(__file__).resolve().parents[1].joinpath(
            "deploy/postgres/runtime-roles.sql"
        ).read_text(encoding="utf-8")
        paper_lines = "\n".join(
            line for line in grants.splitlines() if "milkyway_paper" in line
        )
        self.assertNotIn("market_data_connections", paper_lines)
        self.assertNotIn("member_quotes", paper_lines)

    def test_kms_bulkhead_fails_fast_before_oci_call(self):
        capacity_error = getattr(credential_store_module, "KmsCapacityError", None)
        self.assertIsNotNone(capacity_error)
        slots = MagicMock()
        slots.acquire.return_value = False
        settings = SimpleNamespace(
            production=True,
            credential_backend="oci-kms",
            oci_kms_crypto_endpoint="https://example.invalid",
            oci_ai_credential_key_id="ocid1.key.test.ai",
            oci_market_credential_key_id="ocid1.key.test.market",
        )
        client = MagicMock()
        with patch.object(credential_store_module, "_kms_slots", slots), patch.object(
            credential_store_module, "_oci_kms_client", return_value=client
        ):
            with self.assertRaises(capacity_error):
                credential_store_module._encrypt_with_oci_kms(
                    "secret", settings, "ai", "owner", "openai:api-key"
                )
        client.encrypt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
