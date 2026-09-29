import asyncio
import datetime as dt
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pandas as pd
import yaml
from pydantic import ValidationError
from fastapi import HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("APP_ENV", "development")

from cloud_app.ai import (
    _anthropic_text,
    _chat_completion_text,
    _extract_object,
    local_ai_ready,
    _openai_text,
    _provider_request,
)
from cloud_app.ai_credentials import (
    decrypt_api_key,
    encrypt_api_key,
    key_hint,
    provider_catalog,
    validate_provider_model,
)
from cloud_app.dashboard_views import (
    SECTOR_LABELS,
    completed_session_freshness,
    market_overview,
    news_feed,
    sector_heatmap,
)
from cloud_app.database import (
    AiConnection,
    Base,
    BrowserSession,
    MarketDataConnection,
    MemberQuote,
    PaperAccount,
    PaperFill,
    PaperPosition,
    Quote,
    Strategy,
    User,
)
from cloud_app.main import (
    AiConnectionBody,
    LoginBody,
    MarketDataConnectionBody,
    PromptBody,
    _acquire_stream,
    _migrate_legacy_credentials,
    _release_stream,
    ai_strategy,
    current_user,
    delete_ai_connection,
    delete_market_data_connection,
    login,
    logout,
    put_ai_connection,
    put_market_data_connection,
)
from cloud_app.config import get_settings
from cloud_app.credential_store import (
    OCI_KMS_PREFIX,
    _legacy_fernet,
    validate_credential_backend,
)
from cloud_app.credential_broker import (
    AiEncryptBody as BrokerAiEncryptBody,
    SharedAiGenerateBody,
    _app_identity as broker_app_identity,
    _paper_identity as broker_paper_identity,
    ai_encrypt as broker_ai_encrypt,
    app as credential_broker_app,
    shared_ai_generate,
)
from cloud_app.credential_broker_client import (
    CredentialBrokerError,
    broker_generate_shared_strategy,
    _validated_quotes as validate_broker_quotes,
)
from cloud_app.http_security import RequestBodyLimitMiddleware
from cloud_app.kis_quotes import (
    KisAuthenticationError,
    KisCredentials,
    KisQuoteClient,
    KisRateLimitError,
)
from cloud_app.manage import migrate_credentials_to_oci
from cloud_app.market_data_credentials import (
    MarketDataProviderError,
    decrypt_market_credential,
    encrypt_market_credential,
    provider_catalog as market_data_provider_catalog,
    verify_connection as verify_market_data_connection,
)
from cloud_app.paper import (
    QuoteValue,
    TossQuoteProvider,
    _fill,
    apply_terminal_events,
    collect_watchlist,
    quote_map,
    rebalance_due_accounts,
    store_member_quotes,
)
from cloud_app.security import create_session, hash_password, parse_session, verify_password
from cloud_app.strategies import (
    DatasetSummary,
    StrategySpec,
    compile_raw_scores,
    eligibility_mask,
    strategy_code_preview,
)
from cloud_app.toss_quotes import (
    TossAuthenticationError,
    TossCredentials,
    TossIpNotAllowedError,
    TossQuoteClient,
    TossRateLimitError,
)
from terminal_events import append_event
import cloud_app.database as database_module
import market_calendar as market_calendar_module
from cloud_app.worker import (
    MemberFeedConfig,
    _fetch_member_quotes,
    _member_provider,
    collect_member_quotes as collect_worker_member_quotes,
    run_paper_tick,
)
from price_data_pipeline import PRICE_FORMAT, PRICE_SCHEMA_VERSION, price_file_path


def sample_spec(**portfolio_overrides):
    portfolio = {
        "initial_cash": 100_000,
        "max_positions": 10,
        "rebalance_days": 10,
        "cost_per_side": 0.003,
        "stop_loss_pct": -0.05,
    }
    portfolio.update(portfolio_overrides)
    return StrategySpec.model_validate(
        {
            "schema_version": 1,
            "name": "20 day momentum",
            "description": "safe test strategy",
            "factors": [{"kind": "momentum", "lookback": 20, "weight": 1}],
            "filters": {"min_price": 5, "min_average_volume": 200_000, "history_days": 60},
            "portfolio": portfolio,
        }
    )


class SecurityTests(unittest.TestCase):
    def test_password_hash_and_signed_session(self):
        encoded = hash_password("correct horse battery staple")
        self.assertTrue(verify_password("correct horse battery staple", encoded))
        self.assertFalse(verify_password("wrong password", encoded))
        token, csrf = create_session("user-1", "member", "s" * 40, 1)
        payload = parse_session(token, "s" * 40)
        self.assertEqual(payload["sub"], "user-1")
        self.assertEqual(payload["csrf"], csrf)
        with self.assertRaises(ValueError):
            parse_session(token + "tampered", "s" * 40)

    def test_unknown_login_still_runs_password_verification(self):
        session = MagicMock()
        session.scalar.return_value = None
        request = SimpleNamespace(client=SimpleNamespace(host="198.51.100.77"))
        with patch("cloud_app.main._consume_login_budget"), patch(
            "cloud_app.main.verify_password", return_value=False
        ) as verify:
            with self.assertRaises(HTTPException) as raised:
                login(
                    LoginBody(email="missing@example.com", password="wrong-password"),
                    request,
                    Response(),
                    session,
                )
        self.assertEqual(raised.exception.status_code, 401)
        verify.assert_called_once()

    def test_user_ai_api_key_is_encrypted_and_not_returned_as_hint(self):
        settings = SimpleNamespace(ai_credential_secret="a" * 40, session_secret="s" * 40)
        api_key = "sk-test-this-is-a-long-private-key-1234"
        ciphertext = encrypt_api_key(api_key, settings)
        self.assertNotIn(api_key, ciphertext)
        self.assertEqual(decrypt_api_key(ciphertext, settings), api_key)
        self.assertEqual(key_hint(api_key), "••••1234")
        with self.assertRaises(RuntimeError):
            decrypt_api_key(
                ciphertext,
                SimpleNamespace(ai_credential_secret="b" * 40, session_secret="s" * 40),
            )

    def test_production_rejects_every_shipped_placeholder_and_accepts_strong_values(self):
        base = get_settings()
        example = replace(
            base,
            app_env="production",
            public_base_url="https://quant.example.com",
            allowed_hosts=("quant.example.com",),
            database_url=(
                "postgresql+psycopg://quantclub:"
                "replace-with-url-encoded-password@postgres:5432/quantclub"
            ),
            session_secret="replace-with-at-least-32-random-characters",
            invite_code="replace-with-private-club-invite",
            ai_credential_secret="replace-with-at-least-32-random-characters",
            market_credential_secret="replace-with-a-different-32-plus-random-value",
            local_ai_enabled=False,
        )
        errors = example.startup_errors("deployment")
        self.assertTrue(any("SESSION_SECRET" in item for item in errors))
        self.assertTrue(any("CLUB_INVITE_CODE" in item for item in errors))
        self.assertTrue(any("DATABASE_URL" in item for item in errors))
        self.assertTrue(any("AI_CREDENTIAL_SECRET" in item for item in errors))
        self.assertTrue(any("MARKET_CREDENTIAL_SECRET" in item for item in errors))
        self.assertTrue(any("example hostname" in item for item in errors))

        strong = replace(
            example,
            public_base_url="https://milkyway-quant.club",
            allowed_hosts=("milkyway-quant.club",),
            database_url=(
                "postgresql+psycopg://quantclub:"
                "Db-0123456789-Strong-Password@postgres:5432/quantclub?sslmode=verify-full&sslrootcert=/run/secrets/postgres_tls_ca"
            ),
            session_secret="Session-0123456789-abcdefghijklmnopqrstuvwxyz",
            invite_code="Invite-0123456789-Club-Members-Only",
            legacy_invite_enabled=False,
            credential_backend="broker",
            ai_credential_secret="",
            market_credential_secret="",
            oci_kms_crypto_endpoint="",
            oci_ai_credential_key_id="",
            oci_market_credential_key_id="",
            credential_broker_url="https://broker.milkyway-quant.club",
            credential_broker_app_token="App-0123456789-abcdefghijklmnopqrstuvwxyz",
            credential_broker_paper_token="Paper-9876543210-zyxwvutsrqponmlkjihg",
            credential_broker_backtest_token="Backtest-5432109876-abcdefghijklmnop",
            authority_enabled=True,
            member_credentials_enabled=True,
        )
        self.assertEqual(
            [
                error
                for error in strong.startup_errors("deployment")
                if error != "DATASET_DIR/manifest.json is missing"
            ],
            [],
        )
        broker = replace(
            strong,
            database_url="postgresql+psycopg://milkyway_authority:Authority-Db-0123456789-Strong@postgres:5432/quantclub?sslmode=verify-full&sslrootcert=/run/secrets/postgres_tls_ca",
            credential_backend="oci-kms",
            oci_kms_crypto_endpoint="https://fixture-crypto.kms.ap-seoul-1.oraclecloud.com",
            oci_ai_credential_key_id="ocid1.key.oc1.ap-seoul-1.ai-fixture",
            oci_market_credential_key_id="ocid1.key.oc1.ap-seoul-1.market-fixture",
            shared_ai_enabled=True,
            shared_ai_provider="openai",
            shared_ai_model="gpt-5.6-luna",
            service_role="broker",
            oci_shared_ai_secret_id="ocid1.vaultsecret.oc1.ap-seoul-1.aaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            credential_broker_url="",
        )
        self.assertEqual(broker.startup_errors("broker"), [])

    def test_v2_credentials_are_bound_to_owner_purpose_and_field_with_legacy_read(self):
        settings = SimpleNamespace(
            ai_credential_secret="AI-0123456789-abcdefghijklmnopqrstuvwxyz",
            market_credential_secret="Market-9876543210-zyxwvutsrqponmlkjihg",
            production=False,
        )
        api_key = "sk-test-this-is-a-long-private-key-1234"
        encrypted_ai = encrypt_api_key(
            api_key, settings, owner_id="user-one", provider="openai"
        )
        self.assertTrue(encrypted_ai.startswith("v2:"))
        self.assertEqual(
            decrypt_api_key(
                encrypted_ai, settings, owner_id="user-one", provider="openai"
            ),
            api_key,
        )
        with self.assertRaises(RuntimeError):
            decrypt_api_key(
                encrypted_ai, settings, owner_id="user-two", provider="openai"
            )
        with self.assertRaises(RuntimeError):
            decrypt_api_key(
                encrypted_ai, settings, owner_id="user-one", provider="anthropic"
            )

        market_key = "c_01HXYZABCDEFG123456789"
        encrypted_market = encrypt_market_credential(
            market_key,
            "App Key",
            settings,
            owner_id="user-one",
            provider="toss",
            environment="live",
        )
        self.assertEqual(
            decrypt_market_credential(
                encrypted_market,
                settings,
                owner_id="user-one",
                provider="toss",
                environment="live",
                label="App Key",
            ),
            market_key,
        )
        with self.assertRaises(RuntimeError):
            decrypt_market_credential(
                encrypted_market,
                settings,
                owner_id="user-two",
                provider="toss",
                environment="live",
                label="App Key",
            )

        legacy = _legacy_fernet(settings).encrypt(api_key.encode("utf-8")).decode("ascii")
        self.assertEqual(
            decrypt_api_key(legacy, settings, owner_id="user-one", provider="openai"),
            api_key,
        )

    def test_oci_kms_credentials_keep_roots_external_and_bind_associated_data(self):
        stored = {}
        encrypt_details = []

        class FakeKmsClient:
            fail_encrypt = False

            def encrypt(self, details):
                if self.fail_encrypt:
                    raise RuntimeError("simulated KMS outage")
                encrypt_details.append(details)
                token = "ciphertext-{}".format(len(stored) + 1)
                stored[token] = (
                    details.key_id,
                    details.associated_data,
                    details.plaintext,
                )
                return SimpleNamespace(data=SimpleNamespace(ciphertext=token))

            def decrypt(self, details):
                key_id, associated_data, plaintext = stored[details.ciphertext]
                if key_id != details.key_id or associated_data != details.associated_data:
                    raise ValueError("KMS associated data mismatch")
                return SimpleNamespace(data=SimpleNamespace(plaintext=plaintext))

        fake_client = FakeKmsClient()
        settings = SimpleNamespace(
            production=True,
            credential_backend="oci-kms",
            ai_credential_secret="",
            market_credential_secret="",
            oci_kms_crypto_endpoint=(
                "https://vault-name-crypto.kms.ap-seoul-1.oraclecloud.com"
            ),
            oci_ai_credential_key_id="ocid1.key.oc1.ap-seoul-1.ai-key",
            oci_market_credential_key_id="ocid1.key.oc1.ap-seoul-1.market-key",
        )
        api_key = "sk-test-this-is-a-long-private-key-1234"
        local_ciphertext = encrypt_api_key(
            api_key,
            SimpleNamespace(
                production=False,
                credential_backend="local",
                ai_credential_secret="a" * 40,
            ),
            owner_id="user-one",
            provider="openai",
        )
        with patch("cloud_app.credential_store._oci_kms_client", return_value=fake_client):
            ciphertext = encrypt_api_key(
                api_key, settings, owner_id="user-one", provider="openai"
            )
            self.assertTrue(ciphertext.startswith(OCI_KMS_PREFIX))
            self.assertNotIn(api_key, ciphertext)
            self.assertEqual(
                decrypt_api_key(
                    ciphertext,
                    settings,
                    owner_id="user-one",
                    provider="openai",
                ),
                api_key,
            )
            with self.assertRaises(RuntimeError):
                decrypt_api_key(
                    ciphertext,
                    settings,
                    owner_id="user-two",
                    provider="openai",
                )
            with self.assertRaises(RuntimeError):
                decrypt_api_key(
                    ciphertext,
                    settings,
                    owner_id="user-one",
                    provider="anthropic",
                )
            with self.assertRaises(RuntimeError):
                decrypt_api_key(
                    local_ciphertext,
                    settings,
                    owner_id="user-one",
                    provider="openai",
                )
            validate_credential_backend(settings)
            stored_count = len(stored)
            fake_client.fail_encrypt = True
            with self.assertRaisesRegex(RuntimeError, "encryption service is unavailable"):
                encrypt_api_key(
                    api_key,
                    settings,
                    owner_id="user-one",
                    provider="openai",
                )
            self.assertEqual(len(stored), stored_count)
        self.assertEqual(encrypt_details[0].encryption_algorithm, "AES_256_GCM")
        self.assertEqual(
            encrypt_details[0].associated_data,
            {
                "field": "openai:api-key",
                "owner": "user-one",
                "purpose": "ai",
                "version": "3",
            },
        )

    def test_offline_oci_migration_is_atomic_and_idempotent(self):
        legacy_ai_root = "AI-0123456789-abcdefghijklmnopqrstuvwxyz"
        legacy_market_root = "Market-9876543210-zyxwvutsrqponmlkjihg"
        base = get_settings()
        legacy_settings = replace(
            base,
            app_env="development",
            credential_backend="local",
            ai_credential_secret=legacy_ai_root,
            market_credential_secret=legacy_market_root,
        )
        target_settings = replace(
            base,
            app_env="production",
            credential_backend="oci-kms",
            ai_credential_secret="",
            market_credential_secret="",
            oci_kms_crypto_endpoint=(
                "https://vault-name-crypto.kms.ap-seoul-1.oraclecloud.com"
            ),
            oci_ai_credential_key_id="ocid1.key.oc1.ap-seoul-1.ai-key",
            oci_market_credential_key_id="ocid1.key.oc1.ap-seoul-1.market-key",
        )
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = session_factory()
        user = User(
            id="k" * 32,
            email="kms-migration@example.com",
            display_name="KMS migration",
            password_hash="unused",
        )
        ai_plaintext = "sk-test-this-is-a-long-private-key-1234"
        market_key = "c_01HXYZABCDEFG123456789"
        market_secret = "s_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        session.add_all(
            [
                user,
                AiConnection(
                    user_id=user.id,
                    provider="openai",
                    model="gpt-5.6-luna",
                    encrypted_api_key=encrypt_api_key(
                        ai_plaintext,
                        legacy_settings,
                        owner_id=user.id,
                        provider="openai",
                    ),
                    key_hint="••••1234",
                ),
                MarketDataConnection(
                    user_id=user.id,
                    provider="toss",
                    environment="live",
                    encrypted_api_key=encrypt_market_credential(
                        market_key,
                        "App Key",
                        legacy_settings,
                        owner_id=user.id,
                        provider="toss",
                        environment="live",
                    ),
                    encrypted_api_secret=encrypt_market_credential(
                        market_secret,
                        "App Secret",
                        legacy_settings,
                        owner_id=user.id,
                        provider="toss",
                        environment="live",
                    ),
                    key_hint="••••6789",
                    secret_hint="••••xxxx",
                ),
            ]
        )
        session.commit()
        session.close()

        with (
            patch("cloud_app.main.settings", target_settings),
            patch("cloud_app.main.SessionLocal", side_effect=session_factory),
        ):
            with self.assertRaisesRegex(RuntimeError, "offline OCI KMS migration"):
                _migrate_legacy_credentials()

        encrypted = {}

        class FakeKmsClient:
            fail_after = None

            def encrypt(self, details):
                if self.fail_after is not None and len(encrypted) >= self.fail_after:
                    raise RuntimeError("simulated KMS migration failure")
                token = "migration-ciphertext-{}".format(len(encrypted) + 1)
                encrypted[token] = (
                    details.key_id,
                    details.associated_data,
                    details.plaintext,
                )
                return SimpleNamespace(data=SimpleNamespace(ciphertext=token))

            def decrypt(self, details):
                key_id, associated_data, plaintext = encrypted[details.ciphertext]
                if key_id != details.key_id or associated_data != details.associated_data:
                    raise ValueError("KMS associated data mismatch")
                return SimpleNamespace(data=SimpleNamespace(plaintext=plaintext))

        fake_client = FakeKmsClient()
        with (
            patch("cloud_app.manage.get_settings", return_value=target_settings),
            patch("cloud_app.manage.initialize_database"),
            patch("cloud_app.manage.SessionLocal", side_effect=session_factory),
            patch(
                "cloud_app.manage._migration_secret",
                side_effect=[
                    legacy_ai_root,
                    legacy_market_root,
                    legacy_ai_root,
                    legacy_market_root,
                ],
            ) as prompt,
            patch("cloud_app.credential_store._oci_kms_client", return_value=fake_client),
        ):
            with self.assertRaisesRegex(SystemExit, "backup-confirmed"):
                migrate_credentials_to_oci("MIGRATE_TO_OCI_KMS")
            prompt.assert_not_called()
            fake_client.fail_after = 1
            with self.assertRaises(RuntimeError):
                migrate_credentials_to_oci(
                    "MIGRATE_TO_OCI_KMS", backup_confirmed=True
                )
            rolled_back = session_factory()
            self.assertFalse(
                rolled_back.get(AiConnection, user.id).encrypted_api_key.startswith(
                    OCI_KMS_PREFIX
                )
            )
            self.assertFalse(
                rolled_back.get(MarketDataConnection, user.id).encrypted_api_key.startswith(
                    OCI_KMS_PREFIX
                )
            )
            rolled_back.close()

            fake_client.fail_after = None
            self.assertEqual(
                migrate_credentials_to_oci(
                    "MIGRATE_TO_OCI_KMS", backup_confirmed=True
                ),
                0,
            )
            self.assertEqual(
                prompt.call_args_list,
                [
                    call("Legacy AI/shared credential root: "),
                    call("Legacy v2 market credential root: "),
                    call("Legacy AI/shared credential root: "),
                    call("Legacy v2 market credential root: "),
                ],
            )
            migrated = session_factory()
            ai_row = migrated.get(AiConnection, user.id)
            market_row = migrated.get(MarketDataConnection, user.id)
            self.assertTrue(ai_row.encrypted_api_key.startswith(OCI_KMS_PREFIX))
            self.assertTrue(market_row.encrypted_api_key.startswith(OCI_KMS_PREFIX))
            self.assertTrue(market_row.encrypted_api_secret.startswith(OCI_KMS_PREFIX))
            self.assertEqual(
                decrypt_api_key(
                    ai_row.encrypted_api_key,
                    target_settings,
                    owner_id=user.id,
                    provider="openai",
                ),
                ai_plaintext,
            )
            migrated.close()
            prompt.reset_mock()
            self.assertEqual(migrate_credentials_to_oci("MIGRATE_TO_OCI_KMS"), 0)
            prompt.assert_not_called()
            corrupted = session_factory()
            corrupted.get(AiConnection, user.id).encrypted_api_key = (
                OCI_KMS_PREFIX + "truncated"
            )
            corrupted.commit()
            corrupted.close()
            with self.assertRaises(RuntimeError):
                migrate_credentials_to_oci("MIGRATE_TO_OCI_KMS")
            prompt.assert_not_called()

    def test_broker_backend_has_no_local_crypto_or_raw_decrypt_route(self):
        broker_settings = SimpleNamespace(
            credential_backend="broker",
            production=True,
            ai_credential_secret="",
            market_credential_secret="",
        )
        with self.assertRaisesRegex(RuntimeError, "restricted to the credential broker"):
            encrypt_api_key(
                "sk-broker-boundary-private-value-1234",
                broker_settings,
                owner_id="owner-one",
                provider="openai",
            )
        with self.assertRaisesRegex(RuntimeError, "읽을 수 없습니다"):
            decrypt_api_key(
                OCI_KMS_PREFIX + "opaque-ciphertext",
                broker_settings,
                owner_id="owner-one",
                provider="openai",
            )
        route_paths = {route.path for route in credential_broker_app.routes}
        self.assertFalse(any("decrypt" in path or "proxy" in path for path in route_paths))
        self.assertNotIn("/v1/encrypt", route_paths)

    def test_broker_roles_are_distinct_and_ai_encrypt_never_returns_plaintext(self):
        scoped = SimpleNamespace(
            credential_broker_app_token="app-token-0123456789-abcdefghijklmnopqrstuvwxyz",
            credential_broker_paper_token="paper-token-9876543210-zyxwvutsrqponmlkjihg",
        )
        with patch("cloud_app.credential_broker.settings", scoped):
            self.assertEqual(
                broker_app_identity("Bearer " + scoped.credential_broker_app_token),
                "app",
            )
            self.assertEqual(
                broker_paper_identity("Bearer " + scoped.credential_broker_paper_token),
                "paper",
            )
            with self.assertRaises(HTTPException) as rejected:
                broker_app_identity("Bearer " + scoped.credential_broker_paper_token)
            self.assertEqual(rejected.exception.status_code, 401)

            plaintext = "sk-broker-boundary-private-value-5678"
            with patch(
                "cloud_app.credential_broker.encrypt_api_key",
                return_value=OCI_KMS_PREFIX + "opaque",
            ):
                response = broker_ai_encrypt(
                    BrokerAiEncryptBody(
                        owner_id="owner-one", provider="openai", api_key=plaintext
                    ),
                    "app",
                )
            self.assertEqual(response["ciphertext"], OCI_KMS_PREFIX + "opaque")
            self.assertEqual(response["key_hint"], "••••5678")
            self.assertNotIn(plaintext, json.dumps(response, ensure_ascii=False))

    def test_shared_ai_contract_accepts_only_prompt_and_uses_fixed_broker_settings(self):
        with self.assertRaises(ValidationError):
            SharedAiGenerateBody.model_validate(
                {
                    "prompt": "20일 모멘텀 전략을 만들어 주세요",
                    "provider": "attacker-selected",
                    "api_key": "attacker-supplied-secret",
                }
            )

        fixed = SimpleNamespace(
            max_users=40,
            shared_ai_enabled=True,
            shared_ai_provider="openai",
            shared_ai_model="gpt-5.6-luna",
            shared_ai_api_key="Shared-AI-0123456789-abcdefghijklmnopqrstuvwxyz",
            ai_timeout_seconds=120,
            local_ai_enabled=False,
            local_ai_api_key="",
            local_ai_base_url="http://ai.invalid/v1",
        )
        spec = sample_spec()
        with patch("cloud_app.credential_broker.settings", fixed), patch(
            "cloud_app.credential_broker._rate_limit"
        ), patch(
            "cloud_app.credential_broker.generate_strategy",
            return_value=(spec, "preview"),
        ) as generate:
            payload = shared_ai_generate(
                SharedAiGenerateBody(prompt="20일 모멘텀 전략을 만들어 주세요"),
                "app",
            )
        generate.assert_called_once()
        self.assertGreater(generate.call_args.kwargs["timeout_seconds"], 0)
        self.assertLessEqual(generate.call_args.kwargs["timeout_seconds"], 120)
        self.assertEqual(generate.call_args.args, (
            "20일 모멘텀 전략을 만들어 주세요",
        ))
        self.assertEqual(
            {key: value for key, value in generate.call_args.kwargs.items() if key != "timeout_seconds"},
            dict(provider="openai", model="gpt-5.6-luna", api_key=fixed.shared_ai_api_key, local_base_url=None),
        )
        self.assertEqual(payload["spec"]["name"], spec.name)
        self.assertNotIn(fixed.shared_ai_api_key, json.dumps(payload, ensure_ascii=False))

    def test_shared_ai_client_sends_prompt_only(self):
        settings = SimpleNamespace(ai_timeout_seconds=120)
        spec = sample_spec()
        with patch(
            "cloud_app.credential_broker_client._request",
            return_value={
                "spec": spec.model_dump(mode="json"),
                "preview": "preview",
            },
        ) as request:
            returned, preview = broker_generate_shared_strategy(
                settings,
                prompt="20일 모멘텀 전략을 만들어 주세요",
            )
        self.assertEqual(returned.name, spec.name)
        self.assertEqual(preview, "preview")
        self.assertEqual(
            request.call_args.args[3],
            {"prompt": "20일 모멘텀 전략을 만들어 주세요"},
        )

    def test_production_route_tables_exclude_member_credential_operations(self):
        environment = os.environ.copy()
        secret_directory = tempfile.TemporaryDirectory()
        self.addCleanup(secret_directory.cleanup)
        shared_ai_secret = Path(secret_directory.name, "shared-ai-api-key")
        shared_ai_secret.write_text(
            "Shared-AI-0123456789-abcdefghijklmnopqrstuvwxyz\n", encoding="utf-8"
        )
        shared_ai_secret.chmod(0o600)
        environment.update(
            APP_ENV="production",
            MEMBER_CREDENTIALS_ENABLED="false",
            PUBLIC_BASE_URL="https://milkyway.internal.club",
            ALLOWED_HOSTS="milkyway.internal.club",
            DATABASE_URL=(
                "postgresql+psycopg://milkyway_app:"
                "Db-0123456789-Strong-Password@postgres:5432/quantclub"
            ),
            SESSION_SECRET="Session-0123456789-abcdefghijklmnopqrstuvwxyz",
            LEGACY_CLUB_INVITE_ENABLED="false",
            CREDENTIAL_BACKEND="broker",
            CREDENTIAL_BROKER_URL="https://broker.internal.club",
            CREDENTIAL_BROKER_APP_TOKEN="App-0123456789-abcdefghijklmnopqrstuvwxyz",
            CREDENTIAL_BROKER_PAPER_TOKEN="Paper-9876543210-zyxwvutsrqponmlkjihg",
            SHARED_AI_ENABLED="true",
            SHARED_AI_PROVIDER="openai",
            SHARED_AI_MODEL="gpt-5.6-luna",
            QUOTE_PROVIDER="mock",
            MARKET_DATA_SHARING_ALLOWED="false",
            KIS_QUOTE_TRANSPORT="rest",
        )
        environment.pop("SHARED_AI_API_KEY", None)
        environment.pop("SHARED_AI_API_KEY_FILE", None)
        script = """
import json
from cloud_app.main import app as public_app
from cloud_app.credential_broker import app as broker_app
print(json.dumps({
    "public": [[route.path, sorted(getattr(route, "methods", []) or [])] for route in public_app.routes],
    "broker": [route.path for route in broker_app.routes],
}))
"""
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        routes = json.loads(completed.stdout.strip().splitlines()[-1])
        public_routes = {(path, tuple(methods)) for path, methods in routes["public"]}
        self.assertNotIn(("/api/me/ai-connection", ("PUT",)), public_routes)
        self.assertNotIn(("/api/me/market-data-connection", ("PUT",)), public_routes)
        self.assertNotIn(("/api/me/ai-connection", ("DELETE",)), public_routes)
        self.assertNotIn(("/api/me/market-data-connection", ("DELETE",)), public_routes)
        for path in (
            "/v1/ai/encrypt",
            "/v1/ai/validate",
            "/v1/ai/generate",
            "/v1/market/prepare",
            "/v1/market/validate",
            "/v1/market/quotes",
        ):
            self.assertNotIn(path, routes["broker"])
        self.assertIn("/v1/ai/shared-generate", routes["broker"])
        self.assertIn("/v1/market/shared-quotes", routes["broker"])

    def test_broker_quote_response_rejects_injected_or_nonfinite_values(self):
        observed = dt.datetime.now(dt.timezone.utc).isoformat()
        valid = {
            "quotes": [
                {
                    "ticker": "AAPL",
                    "price": 100.0,
                    "bid": 99.0,
                    "ask": 101.0,
                    "volume": 20.0,
                    "source": "kis_member",
                    "observed_at": observed,
                }
            ]
        }
        self.assertEqual(
            validate_broker_quotes(
                valid, requested=("AAPL",), allowed_sources={"kis_member"}
            )[0].ticker,
            "AAPL",
        )
        for field, value in (
            ("ticker", "MSFT"),
            ("source", "attacker"),
            ("price", float("nan")),
        ):
            corrupted = json.loads(json.dumps(valid))
            corrupted["quotes"][0][field] = value
            with self.assertRaises(CredentialBrokerError):
                validate_broker_quotes(
                    corrupted,
                    requested=("AAPL",),
                    allowed_sources={"kis_member"},
                )

    def test_app_and_worker_use_broker_operations_without_local_decrypt(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(
            id="b" * 32,
            email="broker-boundary@example.com",
            display_name="Broker boundary",
            password_hash="unused",
        )
        session.add(user)
        session.commit()
        base = get_settings()
        runtime_settings = replace(base, credential_backend="broker")
        catalog = [
            {
                "id": "openai",
                "available": True,
                "ready": True,
                "label": "OpenAI",
                "default_model": "gpt-5.6-luna",
                "model_examples": ["gpt-5.6-luna"],
                "requires_api_key": True,
                "disabled_reason": None,
            }
        ]
        with patch("cloud_app.main.settings", runtime_settings), patch(
            "cloud_app.main.broker_encrypt_ai",
            return_value=(OCI_KMS_PREFIX + "opaque-ai", "••••1234"),
        ) as broker_encrypt, patch(
            "cloud_app.main.broker_ai_catalog", return_value=catalog
        ), patch(
            "cloud_app.main.encrypt_api_key",
            side_effect=AssertionError("public app attempted local encryption"),
        ):
            result = put_ai_connection(
                AiConnectionBody(
                    provider="openai",
                    model="gpt-5.6-luna",
                    api_key="sk-app-never-decrypts-private-key-1234",
                ),
                user,
                session,
            )
        broker_encrypt.assert_called_once()
        self.assertEqual(result["key_hint"], "••••1234")

        now = dt.datetime.now(dt.timezone.utc)
        connection = MemberFeedConfig(
            user_id=user.id,
            provider="kis",
            environment="real",
            encrypted_api_key=OCI_KMS_PREFIX + "opaque-key",
            encrypted_api_secret=OCI_KMS_PREFIX + "opaque-secret",
            updated_at=now,
        )
        quote = QuoteValue("AAPL", 100.0, 99.0, 101.0, 10.0, "kis_member", now)
        with patch(
            "cloud_app.worker.broker_member_quotes", return_value=[quote]
        ) as broker_quotes, patch(
            "cloud_app.worker._member_provider",
            side_effect=AssertionError("paper worker attempted local decryption"),
        ):
            returned_user, values = _fetch_member_quotes(
                connection, SimpleNamespace(credential_backend="broker"), ("AAPL",)
            )
        broker_quotes.assert_called_once()
        self.assertEqual(returned_user, user.id)
        self.assertEqual(values, [quote])
        session.close()

    def test_market_save_uses_broker_for_verify_retain_and_rebind(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(
            id="m" * 32,
            email="broker-market@example.com",
            display_name="Broker market",
            password_hash="unused",
        )
        session.add(user)
        session.commit()
        runtime_settings = replace(get_settings(), credential_backend="broker")
        first = {
            "encrypted_api_key": OCI_KMS_PREFIX + "market-key-one",
            "encrypted_api_secret": OCI_KMS_PREFIX + "market-secret-one",
            "key_hint": "••••1234",
            "secret_hint": "••••5678",
        }
        rebound = {
            **first,
            "encrypted_api_key": OCI_KMS_PREFIX + "market-key-two",
            "encrypted_api_secret": OCI_KMS_PREFIX + "market-secret-two",
        }
        with patch("cloud_app.main.settings", runtime_settings), patch(
            "cloud_app.main.broker_prepare_market", side_effect=[first, rebound]
        ) as prepare, patch(
            "cloud_app.main.decrypt_market_credential",
            side_effect=AssertionError("public app attempted market decryption"),
        ), patch(
            "cloud_app.main.verify_market_data_connection",
            side_effect=AssertionError("public app attempted provider authentication"),
        ):
            put_market_data_connection(
                MarketDataConnectionBody(
                    provider="kis",
                    environment="real",
                    api_key="KIS-BROKER-KEY-1234567890",
                    api_secret="KIS-BROKER-SECRET-1234567890",
                    personal_use_only=True,
                ),
                user,
                session,
            )
            put_market_data_connection(
                MarketDataConnectionBody(
                    provider="kis",
                    environment="paper",
                    personal_use_only=True,
                ),
                user,
                session,
            )
        self.assertEqual(prepare.call_count, 2)
        retained = prepare.call_args_list[1].kwargs
        self.assertEqual(retained["current_provider"], "kis")
        self.assertEqual(retained["current_environment"], "real")
        self.assertEqual(
            retained["current_encrypted_api_key"], OCI_KMS_PREFIX + "market-key-one"
        )
        stored = session.get(MarketDataConnection, user.id)
        self.assertEqual(stored.environment, "paper")
        self.assertEqual(stored.encrypted_api_key, OCI_KMS_PREFIX + "market-key-two")
        session.close()

    def test_ai_generation_uses_broker_without_exposing_provider_key_to_app(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(
            id="g" * 32,
            email="broker-generate@example.com",
            display_name="Broker generate",
            password_hash="unused",
        )
        session.add(user)
        session.add(
            AiConnection(
                user_id=user.id,
                provider="openai",
                model="gpt-5.6-luna",
                encrypted_api_key=OCI_KMS_PREFIX + "opaque-ai",
                key_hint="••••1234",
            )
        )
        session.commit()
        runtime_settings = replace(get_settings(), credential_backend="broker")
        with patch("cloud_app.main.settings", runtime_settings), patch(
            "cloud_app.main.broker_generate_strategy",
            return_value=(sample_spec(), "validated preview"),
        ) as broker_generate, patch(
            "cloud_app.main.decrypt_api_key",
            side_effect=AssertionError("public app attempted AI decryption"),
        ), patch(
            "cloud_app.main.generate_strategy",
            side_effect=AssertionError("public app attempted provider request"),
        ):
            payload = ai_strategy(
                PromptBody(prompt="20일 모멘텀 전략을 만들어 주세요"), user, session
            )
        broker_generate.assert_called_once()
        self.assertEqual(payload["spec"]["name"], "20 day momentum")
        self.assertNotIn("api_key", str(payload))
        session.close()

    def test_compose_moves_kms_and_provider_secrets_to_separate_broker(self):
        compose = yaml.safe_load(
            Path(__file__).resolve().parents[1].joinpath("compose.yaml").read_text(
                encoding="utf-8"
            )
        )
        services = compose["services"]
        app_environment = services["app"]["environment"]
        paper_environment = services["paper-worker"]["environment"]
        forbidden_roots = {"AI_CREDENTIAL_SECRET", "MARKET_CREDENTIAL_SECRET"}
        for name in ("app", "paper-worker", "backtest-worker", "scheduler"):
            self.assertFalse(
                forbidden_roots & set(services[name].get("environment", {})), name
            )
        self.assertEqual(app_environment["CREDENTIAL_BACKEND"], "broker")
        self.assertIn("CREDENTIAL_BROKER_URL", app_environment)
        self.assertIn("CREDENTIAL_BROKER_APP_TOKEN", app_environment)
        self.assertNotIn("CREDENTIAL_BROKER_PAPER_TOKEN", app_environment)
        self.assertNotIn("OCI_AI_CREDENTIAL_KEY_ID", app_environment)
        self.assertNotIn("OCI_MARKET_CREDENTIAL_KEY_ID", app_environment)
        self.assertIn("MARKET_DATA_SHARING_ALLOWED", app_environment)
        self.assertEqual(paper_environment["CREDENTIAL_BACKEND"], "broker")
        self.assertNotIn("OCI_AI_CREDENTIAL_KEY_ID", paper_environment)
        self.assertNotIn("OCI_MARKET_CREDENTIAL_KEY_ID", paper_environment)
        self.assertIn("CREDENTIAL_BROKER_PAPER_TOKEN", paper_environment)
        self.assertNotIn("CREDENTIAL_BROKER_APP_TOKEN", paper_environment)
        self.assertNotIn("BROKER_API_KEY", paper_environment)
        self.assertIn("outbound", services["paper-worker"]["networks"])
        self.assertIn("outbound", services["backtest-worker"]["networks"])
        broker_compose = yaml.safe_load(
            Path(__file__).resolve().parents[1]
            .joinpath("compose.credential-broker.yaml")
            .read_text(encoding="utf-8")
        )
        broker_environment = broker_compose["services"]["credential-broker"]["environment"]
        self.assertEqual(broker_environment["CREDENTIAL_BACKEND"], "oci-kms")
        self.assertEqual(broker_environment["MEMBER_CREDENTIALS_ENABLED"], "true")
        self.assertEqual(broker_environment["AUTHORITY_ENABLED"], "true")
        self.assertNotIn("SHARED_AI_API_KEY", broker_environment)
        self.assertNotIn("SHARED_AI_API_KEY_FILE", broker_environment)
        self.assertIn("OCI_SHARED_AI_SECRET_ID", broker_environment)
        self.assertIn("OCI_AI_CREDENTIAL_KEY_ID", broker_environment)
        self.assertIn("OCI_MARKET_CREDENTIAL_KEY_ID", broker_environment)
        self.assertNotIn("BROKER_API_KEY", broker_environment)
        self.assertNotIn("BROKER_API_SECRET", broker_environment)
        self.assertNotIn("BROKER_API_KEY_FILE", broker_environment)
        self.assertNotIn("BROKER_API_SECRET_FILE", broker_environment)
        self.assertIn("OCI_BROKER_API_KEY_SECRET_ID", broker_environment)
        self.assertIn("OCI_BROKER_API_SECRET_SECRET_ID", broker_environment)
        broker_source = Path(__file__).resolve().parents[1].joinpath(
            "cloud_app/credential_broker.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("from .paper", broker_source)
        self.assertIn(
            "CREDENTIAL_BACKEND", services["backtest-worker"]["environment"]
        )
        self.assertIn("CREDENTIAL_BROKER_BACKTEST_TOKEN", services["backtest-worker"]["environment"])
        self.assertNotIn("CREDENTIAL_BROKER_APP_TOKEN", services["backtest-worker"]["environment"])
        self.assertNotIn("CREDENTIAL_BROKER_BACKTEST_TOKEN", app_environment)
        self.assertNotIn("CREDENTIAL_BACKEND", services["scheduler"]["environment"])
        self.assertIn(
            "./deploy/backup-once.sh:/backup/backup-once.sh:ro",
            services["backup"]["volumes"],
        )
        restore = Path(__file__).resolve().parents[1].joinpath(
            "deploy/restore.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('--dbname="$PGDATABASE"', restore)
        self.assertNotIn('--dbname="$POSTGRES_DB"', restore)

    def test_offline_migration_accepts_one_shared_prefixless_legacy_root(self):
        shared_root = "Shared-legacy-0123456789-abcdefghijklmnopqrstuvwxyz"
        base = get_settings()
        legacy_settings = replace(
            base,
            app_env="development",
            credential_backend="local",
            ai_credential_secret=shared_root,
            market_credential_secret="unused-market-root-012345678901234",
        )
        target_settings = replace(
            base,
            app_env="production",
            credential_backend="oci-kms",
            ai_credential_secret="",
            market_credential_secret="",
            oci_kms_crypto_endpoint="https://vault-crypto.example.invalid",
            oci_ai_credential_key_id="ocid1.key.oc1.ap-seoul-1.ai-key",
            oci_market_credential_key_id="ocid1.key.oc1.ap-seoul-1.market-key",
        )
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = session_factory()
        user = User(
            id="l" * 32,
            email="legacy-shared@example.com",
            display_name="Legacy shared",
            password_hash="unused",
        )
        ai_plaintext = "sk-shared-legacy-private-key-1234"
        market_key = "legacy-market-key-1234567890"
        market_secret = "legacy-market-secret-1234567890"
        legacy_fernet = _legacy_fernet(legacy_settings)
        session.add_all(
            [
                user,
                AiConnection(
                    user_id=user.id,
                    provider="openai",
                    model="gpt-5.6-luna",
                    encrypted_api_key=legacy_fernet.encrypt(
                        ai_plaintext.encode("utf-8")
                    ).decode("ascii"),
                    key_hint="••••1234",
                ),
                MarketDataConnection(
                    user_id=user.id,
                    provider="kis",
                    environment="paper",
                    encrypted_api_key=legacy_fernet.encrypt(
                        market_key.encode("utf-8")
                    ).decode("ascii"),
                    encrypted_api_secret=legacy_fernet.encrypt(
                        market_secret.encode("utf-8")
                    ).decode("ascii"),
                    key_hint="••••7890",
                    secret_hint="••••7890",
                ),
            ]
        )
        session.commit()
        session.close()

        kms_values = {}

        def fake_encrypt(value, _settings, purpose, owner_id, field):
            ciphertext = OCI_KMS_PREFIX + "legacy-migration-{}".format(
                len(kms_values) + 1
            )
            kms_values[ciphertext] = (value, purpose, owner_id, field)
            return ciphertext

        def fake_decrypt(ciphertext, _settings, purpose, owner_id, field):
            value, stored_purpose, stored_owner, stored_field = kms_values[ciphertext]
            if (purpose, owner_id, field) != (
                stored_purpose,
                stored_owner,
                stored_field,
            ):
                raise ValueError("KMS context mismatch")
            return value

        with (
            patch("cloud_app.manage.get_settings", return_value=target_settings),
            patch("cloud_app.manage.initialize_database"),
            patch("cloud_app.manage.SessionLocal", side_effect=session_factory),
            patch("cloud_app.manage._migration_secret", return_value=shared_root) as prompt,
            patch(
                "cloud_app.credential_store._encrypt_with_oci_kms",
                side_effect=fake_encrypt,
            ),
            patch(
                "cloud_app.credential_store._decrypt_with_oci_kms",
                side_effect=fake_decrypt,
            ),
        ):
            self.assertEqual(
                migrate_credentials_to_oci(
                    "MIGRATE_TO_OCI_KMS", backup_confirmed=True
                ),
                0,
            )
        prompt.assert_called_once_with("Legacy AI/shared credential root: ")
        migrated = session_factory()
        self.assertTrue(
            migrated.get(AiConnection, user.id).encrypted_api_key.startswith(
                OCI_KMS_PREFIX
            )
        )
        market = migrated.get(MarketDataConnection, user.id)
        self.assertTrue(market.encrypted_api_key.startswith(OCI_KMS_PREFIX))
        self.assertTrue(market.encrypted_api_secret.startswith(OCI_KMS_PREFIX))
        migrated.close()

    def test_strategy_dsl_rejects_unknown_fields(self):
        payload = sample_spec().model_dump()
        payload["runtime_code"] = "import os"
        with self.assertRaises(ValidationError):
            StrategySpec.model_validate(payload)

    def test_dataset_summary_rejects_price_hash_mismatch_before_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory)
            prices = dataset / "prices"
            prices.mkdir()
            price_file_path(prices, "AAPL").write_bytes(b"tampered")
            (dataset / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": PRICE_SCHEMA_VERSION,
                        "price_format": PRICE_FORMAT,
                        "prices": {
                            "AAPL": {
                                "first_date": "2026-01-02",
                                "last_date": "2026-01-02",
                                "rows": 1,
                                "sha256": "0" * 64,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "integrity"):
                DatasetSummary(
                    SimpleNamespace(
                        dataset_dir=dataset,
                        snapshots_glob=str(dataset / "snapshots/*.json"),
                    )
                )

    def test_database_backed_logout_revokes_a_copied_cookie(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(
            id="9" * 32,
            email="session@example.com",
            display_name="Session",
            password_hash="x",
        )
        session.add(user)
        token, _csrf = create_session(user.id, user.role, "s" * 40, 1)
        payload = parse_session(token, "s" * 40)
        session.add(
            BrowserSession(
                token_hash=hashlib.sha256(payload["jti"].encode()).hexdigest(),
                user_id=user.id,
                expires_at=dt.datetime.fromtimestamp(payload["exp"], tz=dt.timezone.utc),
            )
        )
        session.commit()
        request = SimpleNamespace(cookies={"session": token}, state=SimpleNamespace())
        with patch("cloud_app.main.settings", replace(get_settings(), session_secret="s" * 40)):
            authenticated = current_user(request, session)
            logout(request, Response(), authenticated, session)
            with self.assertRaises(HTTPException) as raised:
                current_user(
                    SimpleNamespace(cookies={"session": token}, state=SimpleNamespace()),
                    session,
                )
        self.assertEqual(raised.exception.status_code, 401)
        session.close()

    def test_request_body_limit_rejects_declared_and_chunked_oversize(self):
        async def invoke(headers, messages, limit=16):
            called = False
            sent = []

            async def endpoint(_scope, receive, send):
                nonlocal called
                called = True
                await receive()
                await send({"type": "http.response.start", "status": 204, "headers": []})
                await send({"type": "http.response.body", "body": b""})

            queue = list(messages)

            async def receive():
                return queue.pop(0)

            async def send(message):
                sent.append(message)

            middleware = RequestBodyLimitMiddleware(endpoint, limit)
            await middleware(
                {"type": "http", "method": "POST", "path": "/login", "headers": headers},
                receive,
                send,
            )
            return called, sent[0]["status"]

        declared = asyncio.run(
            invoke(
                [(b"content-length", b"17")],
                [{"type": "http.request", "body": b"", "more_body": False}],
            )
        )
        chunked = asyncio.run(
            invoke(
                [],
                [
                    {"type": "http.request", "body": b"123456789", "more_body": True},
                    {"type": "http.request", "body": b"123456789", "more_body": False},
                ],
            )
        )
        allowed = asyncio.run(
            invoke(
                [(b"content-length", b"4")],
                [{"type": "http.request", "body": b"test", "more_body": False}],
            )
        )
        self.assertEqual(declared, (False, 413))
        self.assertEqual(chunked, (False, 413))
        self.assertEqual(allowed, (True, 204))

    def test_request_body_replay_preserves_disconnect_signal(self):
        async def invoke():
            observed = []
            sent = []
            queue = [
                {"type": "http.request", "body": b"", "more_body": False},
                {"type": "http.disconnect"},
            ]

            async def endpoint(_scope, receive, send):
                observed.append(await receive())
                observed.append(await receive())
                await send({"type": "http.response.start", "status": 204, "headers": []})
                await send({"type": "http.response.body", "body": b""})

            async def receive():
                return queue.pop(0)

            async def send(message):
                sent.append(message)

            await RequestBodyLimitMiddleware(endpoint, 16)(
                {"type": "http", "method": "GET", "path": "/api/stream", "headers": []},
                receive,
                send,
            )
            return observed, sent

        observed, sent = asyncio.run(invoke())
        self.assertEqual(observed[0]["type"], "http.request")
        self.assertEqual(observed[1]["type"], "http.disconnect")
        self.assertEqual(sent[0]["status"], 204)

    def test_stream_limits_are_released(self):
        user_id = "stream-test-user"
        self.assertTrue(_acquire_stream(user_id))
        self.assertTrue(_acquire_stream(user_id))
        self.assertFalse(_acquire_stream(user_id))
        _release_stream(user_id)
        self.assertTrue(_acquire_stream(user_id))
        _release_stream(user_id)
        _release_stream(user_id)

    def test_sqlite_files_and_parent_are_owner_only(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            runtime.mkdir(mode=0o755)
            database = runtime / "club.sqlite3"
            wal = Path(str(database) + "-wal")
            database.write_bytes(b"db")
            wal.write_bytes(b"wal")
            os.chmod(database, 0o644)
            os.chmod(wal, 0o644)
            with patch.object(database_module, "_sqlite_path", database):
                database_module._secure_sqlite_files()
            self.assertEqual(runtime.stat().st_mode & 0o777, 0o700)
            self.assertEqual(database.stat().st_mode & 0o777, 0o600)
            self.assertEqual(wal.stat().st_mode & 0o777, 0o600)

    def test_finnhub_token_uses_header_and_is_not_logged_on_failure(self):
        secret = "finnhub-secret-token"
        response = MagicMock(status_code=200, headers={})
        response.iter_content.return_value = [b"{}"]
        with patch.object(market_calendar_module, "_FINNHUB_API_KEY", secret):
            with patch("requests.get", return_value=response) as get:
                market_calendar_module._query_finnhub_market_status()
            self.assertEqual(get.call_args.kwargs["params"], {"exchange": "US"})
            self.assertEqual(get.call_args.kwargs["headers"], {"X-Finnhub-Token": secret})
            with patch("requests.get", side_effect=RuntimeError("url?token=" + secret)):
                with self.assertLogs("market_calendar", level=logging.WARNING) as logs:
                    self.assertIsNone(market_calendar_module._query_finnhub_market_status())
            self.assertNotIn(secret, "\n".join(logs.output))

    def test_ai_connection_is_owned_by_one_user(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        first = User(id="1" * 32, email="one@example.com", display_name="One", password_hash="x")
        second = User(id="2" * 32, email="two@example.com", display_name="Two", password_hash="x")
        session.add_all([first, second])
        session.add(
            AiConnection(
                user_id=first.id,
                provider="openai",
                model="gpt-5.6-luna",
                encrypted_api_key="encrypted-only",
                key_hint="••••1234",
            )
        )
        session.commit()
        self.assertIsNotNone(session.get(AiConnection, first.id))
        self.assertIsNone(session.get(AiConnection, second.id))
        session.close()

    def test_ai_connection_endpoint_never_returns_plaintext_key(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="3" * 32, email="member@example.com", display_name="Member", password_hash="x")
        session.add(user)
        session.commit()
        api_key = "sk-test-user-owned-private-key-9876"
        payload = put_ai_connection(
            AiConnectionBody(provider="openai", model="gpt-5.6-luna", api_key=api_key),
            user,
            session,
        )
        self.assertTrue(payload["connected"])
        self.assertNotIn("api_key", payload)
        self.assertEqual(payload["key_hint"], "••••9876")
        stored = session.get(AiConnection, user.id)
        self.assertNotIn(api_key, stored.encrypted_api_key)
        kept = put_ai_connection(
            AiConnectionBody(provider="openai", model="gpt-5.6-terra"),
            user,
            session,
        )
        self.assertEqual(kept["model"], "gpt-5.6-terra")
        with self.assertRaises(HTTPException):
            put_ai_connection(
                AiConnectionBody(provider="anthropic", model="claude-sonnet-4-20250514"),
                user,
                session,
            )
        delete_ai_connection(user, session)
        self.assertIsNone(session.get(AiConnection, user.id))
        session.close()

    def test_local_ai_connection_needs_no_member_api_key(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="4" * 32, email="local@example.com", display_name="Local", password_hash="x")
        session.add(user)
        session.commit()
        local_settings = SimpleNamespace(
            member_credentials_enabled=True,
            local_ai_enabled=True,
            local_ai_base_url="http://ai:8080/v1",
            local_ai_model="Qwen2.5-Coder-7B-Instruct-GGUF",
            local_ai_api_key="server-owned-key",
        )
        with patch("cloud_app.main.settings", local_settings), patch(
            "cloud_app.main.local_ai_ready", return_value=True
        ):
            payload = put_ai_connection(
                AiConnectionBody(
                    provider="local",
                    model="user-overridden-model",
                ),
                user,
                session,
            )
        self.assertTrue(payload["connected"])
        self.assertEqual(payload["key_hint"], "서버 관리")
        stored = session.get(AiConnection, user.id)
        self.assertEqual(stored.encrypted_api_key, "")
        self.assertEqual(stored.model, "Qwen2.5-Coder-7B-Instruct-GGUF")
        session.close()

    def test_member_market_data_credentials_are_verified_encrypted_and_owned(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="6" * 32, email="quotes@example.com", display_name="Quotes", password_hash="x")
        session.add(user)
        session.commit()
        api_key = "KIS-APP-KEY-THIS-IS-PRIVATE-1234"
        api_secret = "KIS-APP-SECRET-THIS-IS-PRIVATE-5678"
        with patch("cloud_app.main.verify_market_data_connection") as verify:
            payload = put_market_data_connection(
                MarketDataConnectionBody(
                    provider="kis",
                    environment="real",
                    api_key=api_key,
                    api_secret=api_secret,
                    personal_use_only=True,
                ),
                user,
                session,
            )
        verify.assert_called_once_with("kis", "real", api_key, api_secret)
        self.assertTrue(payload["connected"])
        self.assertNotIn("api_key", payload)
        self.assertNotIn("api_secret", payload)
        stored = session.get(MarketDataConnection, user.id)
        self.assertNotIn(api_key, stored.encrypted_api_key)
        self.assertNotIn(api_secret, stored.encrypted_api_secret)
        self.assertEqual(
            decrypt_market_credential(
                stored.encrypted_api_key,
                owner_id=user.id,
                provider="kis",
                environment="real",
                label="App Key",
            ),
            api_key,
        )
        session.add(
            MemberQuote(
                user_id=user.id,
                ticker="AAPL",
                price=200,
                bid=0,
                ask=0,
                volume=0,
                source="old_connection",
                observed_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        session.commit()
        with patch("cloud_app.main.verify_market_data_connection") as verify_again:
            kept = put_market_data_connection(
                MarketDataConnectionBody(
                    provider="kis",
                    environment="paper",
                    personal_use_only=True,
                ),
                user,
                session,
            )
        verify_again.assert_called_once_with("kis", "paper", api_key, api_secret)
        self.assertEqual(kept["environment"], "paper")
        rebound = session.get(MarketDataConnection, user.id)
        self.assertEqual(
            decrypt_market_credential(
                rebound.encrypted_api_key,
                owner_id=user.id,
                provider="kis",
                environment="paper",
                label="App Key",
            ),
            api_key,
        )
        self.assertEqual(session.query(MemberQuote).filter_by(user_id=user.id).count(), 0)
        session.add(
            MemberQuote(
                user_id=user.id,
                ticker="MSFT",
                price=300,
                bid=0,
                ask=0,
                volume=0,
                source="current_connection",
                observed_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        session.commit()
        delete_market_data_connection(user, session)
        self.assertIsNone(session.get(MarketDataConnection, user.id))
        self.assertEqual(session.query(MemberQuote).filter_by(user_id=user.id).count(), 0)
        session.close()

    def test_member_can_store_a_verified_toss_market_data_connection(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="t" * 32, email="toss@example.com", display_name="Toss", password_hash="x")
        session.add(user)
        session.commit()
        client_id = "c_01HXYZABCDEFG123456789"
        client_secret = "s_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        with patch("cloud_app.main.verify_market_data_connection") as verify:
            payload = put_market_data_connection(
                MarketDataConnectionBody(
                    provider="toss",
                    environment="live",
                    api_key=client_id,
                    api_secret=client_secret,
                    personal_use_only=True,
                ),
                user,
                session,
            )
        verify.assert_called_once_with("toss", "live", client_id, client_secret)
        self.assertEqual(payload["provider"], "toss")
        self.assertEqual(payload["environment"], "live")
        self.assertNotIn("api_key", payload)
        stored = session.get(MarketDataConnection, user.id)
        self.assertNotIn(client_id, stored.encrypted_api_key)
        self.assertEqual(
            decrypt_market_credential(
                stored.encrypted_api_key,
                owner_id=user.id,
                provider="toss",
                environment="live",
                label="App Key",
            ),
            client_id,
        )
        session.close()

    def test_market_data_save_rejects_a_concurrent_connection_change(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="c" * 32, email="conflict@example.com", display_name="Conflict", password_hash="x")
        session.add(user)
        session.commit()
        client_id = "c_01HXYZABCDEFG123456789"
        client_secret = "s_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        with patch("cloud_app.main.verify_market_data_connection"):
            put_market_data_connection(
                MarketDataConnectionBody(
                    provider="toss",
                    environment="live",
                    api_key=client_id,
                    api_secret=client_secret,
                    personal_use_only=True,
                ),
                user,
                session,
            )
        stored = session.get(MarketDataConnection, user.id)
        changed = SimpleNamespace(
            provider="toss",
            environment="live",
            updated_at=stored.updated_at + dt.timedelta(seconds=1),
        )
        with patch("cloud_app.main.verify_market_data_connection"), patch.object(
            session, "scalar", return_value=changed
        ):
            with self.assertRaises(HTTPException) as raised:
                put_market_data_connection(
                    MarketDataConnectionBody(
                        provider="toss",
                        environment="live",
                        personal_use_only=True,
                    ),
                    user,
                    session,
                )
        self.assertEqual(raised.exception.status_code, 409)
        session.close()

    def test_market_data_connection_requires_personal_use_acknowledgement(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="7" * 32, email="license@example.com", display_name="License", password_hash="x")
        session.add(user)
        session.commit()
        with self.assertRaises(HTTPException) as raised:
            put_market_data_connection(
                MarketDataConnectionBody(
                    provider="kis",
                    environment="real",
                    api_key="KIS-APP-KEY-THIS-IS-PRIVATE-1234",
                    api_secret="KIS-APP-SECRET-THIS-IS-PRIVATE-5678",
                ),
                user,
                session,
            )
        self.assertEqual(raised.exception.status_code, 422)
        session.close()

    def test_market_data_verification_backpressure_returns_429(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="8" * 32, email="busy-quotes@example.com", display_name="Busy", password_hash="x")
        session.add(user)
        session.commit()
        slots = MagicMock()
        slots.acquire.return_value = False
        with patch("cloud_app.main._market_data_verification_slots", slots), patch(
            "cloud_app.main.verify_market_data_connection"
        ) as verify:
            with self.assertRaises(HTTPException) as raised:
                put_market_data_connection(
                    MarketDataConnectionBody(
                        provider="kis",
                        environment="real",
                        api_key="KIS-APP-KEY-THIS-IS-PRIVATE-1234",
                        api_secret="KIS-APP-SECRET-THIS-IS-PRIVATE-5678",
                        personal_use_only=True,
                    ),
                    user,
                    session,
                )
        self.assertEqual(raised.exception.status_code, 429)
        verify.assert_not_called()
        slots.release.assert_not_called()
        session.close()

    def test_member_quote_isolated_from_shared_quote_for_personal_paper_use(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        owner = User(id="9" * 32, email="owner@example.com", display_name="Owner", password_hash="x")
        other = User(id="a" * 32, email="other@example.com", display_name="Other", password_hash="x")
        now = dt.datetime.now(dt.timezone.utc)
        session.add_all([owner, other])
        session.add(
            MarketDataConnection(
                user_id=owner.id,
                provider="kis",
                environment="real",
                encrypted_api_key="encrypted-key",
                encrypted_api_secret="encrypted-secret",
                key_hint="•••1234",
                secret_hint="•••5678",
                verified_at=now,
            )
        )
        session.add(Quote(ticker="AAPL", price=100, bid=0, ask=0, volume=0, source="shared", observed_at=now))
        session.add(MemberQuote(user_id=owner.id, ticker="AAPL", price=200, bid=0, ask=0, volume=0, source="kis_member", observed_at=now))
        session.commit()
        self.assertEqual(quote_map(session, ["AAPL"], user_id=owner.id), {"AAPL": 200.0})
        self.assertEqual(quote_map(session, ["AAPL"], user_id=other.id), {})
        session.close()

    def test_local_ai_backpressure_returns_429_without_calling_model(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, expire_on_commit=False)()
        user = User(id="5" * 32, email="busy@example.com", display_name="Busy", password_hash="x")
        session.add(user)
        session.add(
            AiConnection(
                user_id=user.id,
                provider="local",
                model="Qwen2.5-Coder-7B-Instruct-GGUF",
                encrypted_api_key="",
                key_hint="서버 관리",
            )
        )
        session.commit()
        local_settings = SimpleNamespace(
            personal_local_mode=False,
            member_credentials_enabled=True,
            local_ai_enabled=True,
            local_ai_base_url="http://ai:8080/v1",
            local_ai_model="Qwen2.5-Coder-7B-Instruct-GGUF",
            local_ai_api_key="server-owned-key",
            ai_timeout_seconds=120,
        )
        slots = MagicMock()
        slots.acquire.return_value = False
        with patch("cloud_app.main.settings", local_settings), patch(
            "cloud_app.main._local_ai_slots", slots
        ), patch("cloud_app.main.generate_strategy") as generate:
            with self.assertRaises(HTTPException) as raised:
                ai_strategy(PromptBody(prompt="20일 모멘텀 전략"), user, session)
        self.assertEqual(raised.exception.status_code, 429)
        generate.assert_not_called()
        slots.release.assert_not_called()
        session.close()


class KisQuoteClientTests(unittest.TestCase):
    def setUp(self):
        self.client = KisQuoteClient(
            KisCredentials(api_key="k" * 24, api_secret="s" * 32, paper=True)
        )
        self.client.session = MagicMock()
        self.client.token = "current-token"
        self.client.token_expires_at = dt.datetime.now() + dt.timedelta(hours=1)

    @staticmethod
    def response(status_code: int, payload: dict):
        response = MagicMock()
        response.status_code = status_code
        encoded = json.dumps(payload).encode("utf-8")
        response.headers = {"Content-Length": str(len(encoded))}
        response.iter_content.return_value = [encoded]
        if status_code >= 400:
            response.raise_for_status.side_effect = RuntimeError("unexpected status handling")
        return response

    def test_rate_limit_http_status_is_not_silently_returned_as_zero(self):
        self.client.session.get.return_value = self.response(429, {})
        with self.assertRaises(KisRateLimitError):
            self.client.get_quote("AAPL")
        self.client.session.get.assert_called_once()

    def test_kis_success_status_with_rate_limit_code_is_an_error(self):
        self.client.session.get.return_value = self.response(
            200,
            {"rt_cd": "1", "msg_cd": "EGW00201", "msg1": "초당 거래건수 초과"},
        )
        with self.assertRaises(KisRateLimitError):
            self.client.get_quote("AAPL")
        self.client.session.get.assert_called_once()

    def test_authentication_failure_refreshes_once_then_retries_quote(self):
        unauthorized = self.response(401, {})
        success = self.response(
            200,
            {
                "rt_cd": "0",
                "output": {"last": "123.45", "bidp": "123", "askp": "124", "tvol": "9"},
            },
        )
        self.client.session.get.side_effect = [unauthorized, success]

        def refresh_token():
            self.client.token = "refreshed-token"
            self.client.token_expires_at = dt.datetime.now() + dt.timedelta(hours=1)

        with patch.object(self.client, "_refresh_token", side_effect=refresh_token) as refresh:
            quote = self.client.get_quote("AAPL")
        self.assertEqual(quote["price"], 123.45)
        self.assertEqual(self.client.session.get.call_count, 2)
        refresh.assert_called_once()

    def test_second_authentication_failure_is_raised(self):
        self.client.session.get.side_effect = [
            self.response(401, {}),
            self.response(403, {}),
        ]

        def refresh_token():
            self.client.token = "refreshed-token"
            self.client.token_expires_at = dt.datetime.now() + dt.timedelta(hours=1)

        with patch.object(self.client, "_refresh_token", side_effect=refresh_token):
            with self.assertRaises(KisAuthenticationError):
                self.client.get_quote("AAPL")
        self.assertEqual(self.client.session.get.call_count, 2)


class TossQuoteClientTests(unittest.TestCase):
    def setUp(self):
        self.client = TossQuoteClient(
            TossCredentials(
                client_id="c_01HXYZABCDEFG123456789",
                client_secret="s_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            )
        )
        self.client.session = MagicMock()
        self.client.token = "current-token"
        self.client.token_expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)

    @staticmethod
    def response(status_code: int, payload: dict, headers: dict | None = None):
        response = MagicMock()
        response.status_code = status_code
        encoded = json.dumps(payload).encode("utf-8")
        response.headers = {"Content-Length": str(len(encoded)), **(headers or {})}
        response.iter_content.return_value = [encoded]
        return response

    def test_authenticate_uses_form_encoded_client_credentials(self):
        self.client.token = ""
        self.client.session.post.return_value = self.response(
            200,
            {"access_token": "issued-token", "token_type": "Bearer", "expires_in": 86400},
        )
        self.client.authenticate()
        self.assertEqual(self.client.token, "issued-token")
        call = self.client.session.post.call_args
        self.assertEqual(call.args[0], "https://openapi.tossinvest.com/oauth2/token")
        self.assertEqual(call.kwargs["data"]["grant_type"], "client_credentials")
        self.assertNotIn("json", call.kwargs)

    def test_prices_batch_maps_kr_and_us_quotes_with_provider_timestamps(self):
        self.client.session.get.return_value = self.response(
            200,
            {
                "result": [
                    {
                        "symbol": "AAPL",
                        "timestamp": "2026-08-28T10:30:00-04:00",
                        "lastPrice": "185.70",
                        "currency": "USD",
                    },
                    {
                        "symbol": "005930",
                        "timestamp": "2026-08-28T23:30:00+09:00",
                        "lastPrice": "72000",
                        "currency": "KRW",
                    },
                ]
            },
        )
        quotes = self.client.get_prices(["AAPL", "005930", "AAPL"])
        self.assertEqual([quote["ticker"] for quote in quotes], ["AAPL", "005930"])
        self.assertEqual(quotes[0]["price"], 185.7)
        self.assertEqual(quotes[0]["observed_at"].tzinfo, dt.timezone.utc)
        self.assertEqual(
            self.client.session.get.call_args.kwargs["params"]["symbols"],
            "005930,AAPL",
        )

    def test_null_timestamp_skips_only_that_symbol_and_preserves_batch(self):
        self.client.session.get.return_value = self.response(
            200,
            {
                "result": [
                    {
                        "symbol": "AAPL",
                        "timestamp": "2026-08-28T10:30:00-04:00",
                        "lastPrice": "185.70",
                        "currency": "USD",
                    },
                    {
                        "symbol": "NEW",
                        "timestamp": None,
                        "lastPrice": "10.00",
                        "currency": "USD",
                    },
                ]
            },
        )
        quotes = self.client.get_prices(["AAPL", "NEW"])
        self.assertEqual([quote["ticker"] for quote in quotes], ["AAPL"])

    def test_prices_are_split_into_official_200_symbol_batches(self):
        self.client.session.get.side_effect = [
            self.response(200, {"result": []}),
            self.response(200, {"result": []}),
        ]
        symbols = ["T{:03d}".format(index) for index in range(201)]
        self.assertEqual(self.client.get_prices(symbols), [])
        self.assertEqual(self.client.session.get.call_count, 2)
        first_symbols = self.client.session.get.call_args_list[0].kwargs["params"]["symbols"]
        second_symbols = self.client.session.get.call_args_list[1].kwargs["params"]["symbols"]
        self.assertEqual(len(first_symbols.split(",")), 200)
        self.assertEqual(len(second_symbols.split(",")), 1)

    def test_invalid_symbol_is_skipped_without_blocking_valid_holdings(self):
        self.client.session.get.return_value = self.response(200, {"result": []})
        self.assertEqual(self.client.get_prices(["AAPL", "BAD/SYMBOL"]), [])
        requested = self.client.session.get.call_args.kwargs["params"]["symbols"]
        self.assertEqual(requested, "AAPL")

    def test_expired_token_is_refreshed_once_then_prices_are_retried(self):
        self.client.session.get.side_effect = [
            self.response(401, {"error": {"code": "expired-token"}}),
            self.response(200, {"result": []}),
        ]

        def authenticate():
            self.client.token = "refreshed-token"
            self.client.token_expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)

        with patch.object(self.client, "authenticate", side_effect=authenticate) as refresh:
            self.assertEqual(self.client.get_prices(["AAPL"]), [])
        refresh.assert_called_once()
        self.assertEqual(self.client.session.get.call_count, 2)

    def test_second_authentication_rejection_is_not_retried_forever(self):
        self.client.session.get.side_effect = [
            self.response(401, {"error": {"code": "expired-token"}}),
            self.response(401, {"error": {"code": "invalid-token"}}),
        ]

        def authenticate():
            self.client.token = "refreshed-token"
            self.client.token_expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)

        with patch.object(self.client, "authenticate", side_effect=authenticate) as refresh:
            with self.assertRaises(TossAuthenticationError):
                self.client.get_prices(["AAPL"])
        refresh.assert_called_once()
        self.assertEqual(self.client.session.get.call_count, 2)

    def test_unregistered_server_ip_is_a_distinct_error(self):
        self.client.session.get.return_value = self.response(
            403,
            {"error": {"code": "edge-blocked"}},
        )
        with self.assertRaises(TossIpNotAllowedError):
            self.client.get_prices(["AAPL"])

    def test_rate_limit_preserves_retry_after(self):
        self.client.session.get.return_value = self.response(
            429,
            {"error": {"code": "rate-limit-exceeded"}},
            {"Retry-After": "2.5"},
        )
        with self.assertRaises(TossRateLimitError) as raised:
            self.client.get_prices(["AAPL"])
        self.assertEqual(raised.exception.retry_after, 2.5)


class MarketDataProviderTests(unittest.TestCase):
    def test_catalog_exposes_toss_labels_environment_and_allowed_ip_requirement(self):
        providers = {provider["id"]: provider for provider in market_data_provider_catalog()}
        self.assertEqual(set(providers), {"kis", "toss"})
        toss = providers["toss"]
        self.assertEqual(toss["environments"], [
            {"id": "live", "label": "실시간 시세 · 내부 페이퍼 체결 전용"}
        ])
        self.assertEqual(toss["credential_labels"]["key"], "Client ID")
        self.assertTrue(toss["requires_allowed_ip"])
        self.assertTrue(toss["setup_url"].startswith("https://"))

    def test_toss_verification_explains_unregistered_server_ip(self):
        with patch(
            "cloud_app.market_data_credentials.TossQuoteClient.authenticate",
            side_effect=TossIpNotAllowedError("blocked"),
        ):
            with self.assertRaises(MarketDataProviderError) as raised:
                verify_market_data_connection(
                    "toss",
                    "live",
                    "c_01HXYZABCDEFG123456789",
                    "s_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                )
        self.assertIn("허용 IP", str(raised.exception))

    def test_worker_builds_toss_provider_from_decrypted_member_credentials(self):
        import cloud_app.worker as worker_module

        settings = SimpleNamespace(
            ai_credential_secret="a" * 40,
            market_credential_secret="m" * 40,
            session_secret="s" * 40,
        )
        client_id = "c_01HXYZABCDEFG123456789"
        client_secret = "s_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        config = MemberFeedConfig(
            user_id="w" * 32,
            provider="toss",
            environment="live",
            encrypted_api_key=encrypt_market_credential(
                client_id,
                "App Key",
                settings,
                owner_id="w" * 32,
                provider="toss",
                environment="live",
            ),
            encrypted_api_secret=encrypt_market_credential(
                client_secret,
                "App Secret",
                settings,
                owner_id="w" * 32,
                provider="toss",
                environment="live",
            ),
            updated_at=dt.datetime.now(dt.timezone.utc),
        )
        worker_module._member_provider_cache.clear()
        provider = MagicMock()
        with patch("cloud_app.worker.TossQuoteProvider", return_value=provider) as build:
            self.assertIs(_member_provider(config, settings), provider)
        credentials = build.call_args.args[0]
        self.assertEqual(credentials.client_id, client_id)
        self.assertEqual(credentials.client_secret, client_secret)
        self.assertEqual(build.call_args.kwargs["source"], "toss_member")
        worker_module._member_provider_cache.clear()

    def test_toss_provider_preserves_exchange_timestamp_for_freshness_gate(self):
        provider = object.__new__(TossQuoteProvider)
        provider.broker = MagicMock()
        provider.source = "toss_member"
        observed_at = dt.datetime(2026, 8, 28, 14, 30, tzinfo=dt.timezone.utc)
        provider.broker.get_prices.return_value = [
            {
                "ticker": "AAPL",
                "price": 185.7,
                "bid": 0,
                "ask": 0,
                "volume": 0,
                "observed_at": observed_at,
            }
        ]
        values = provider.fetch(["AAPL"])
        self.assertEqual(values[0].observed_at, observed_at)
        self.assertEqual(values[0].source, "toss_member")

    def test_worker_discards_quotes_if_connection_changes_during_network_fetch(self):
        import cloud_app.worker as worker_module

        observed_at = dt.datetime.now(dt.timezone.utc)
        original = SimpleNamespace(
            user_id="r" * 32,
            provider="toss",
            environment="live",
            encrypted_api_key="encrypted-id",
            encrypted_api_secret="encrypted-secret",
            updated_at=observed_at,
        )
        replaced = SimpleNamespace(
            **{
                **vars(original),
                "provider": "kis",
                "environment": "paper",
                "updated_at": observed_at + dt.timedelta(seconds=1),
            }
        )
        session = MagicMock()
        session.scalars.return_value.all.return_value = [original]
        session.scalar.return_value = replaced
        quote = QuoteValue(
            ticker="AAPL",
            price=185.7,
            bid=0,
            ask=0,
            volume=0,
            source="toss_member",
            observed_at=observed_at,
        )
        worker_module._member_provider_cache.clear()
        worker_module._member_retry_after.clear()
        with patch("cloud_app.worker.store_member_quotes") as store:
            with (
                patch("cloud_app.worker.regular_market_open", return_value=True),
                patch("cloud_app.worker.collect_watchlist", return_value={"AAPL"}),
                patch(
                    "cloud_app.worker._fetch_member_quotes",
                    return_value=(original.user_id, [quote]),
                ),
            ):
                result = collect_worker_member_quotes(session, SimpleNamespace())
        self.assertEqual(result, (0, 0))
        store.assert_not_called()
        session.flush.assert_not_called()


class StrategyDslTests(unittest.TestCase):
    def test_unsupported_ai_code_cannot_enter_strategy_spec(self):
        with self.assertRaises(ValidationError):
            StrategySpec.model_validate(
                {
                    "schema_version": 1,
                    "name": "unsafe",
                    "factors": [{"kind": "python_eval", "lookback": 20, "weight": 1}],
                }
            )

    def test_ai_json_extractor_ignores_surrounding_markdown_but_not_non_json(self):
        self.assertEqual(_extract_object("```json\n{\"name\": \"x\"}\n```"), {"name": "x"})
        with self.assertRaises(ValueError):
            _extract_object("import os; os.system('whoami')")

    def test_ai_provider_catalog_and_response_parsers(self):
        providers = {item["id"] for item in provider_catalog()}
        self.assertEqual(providers, {"openai", "anthropic", "local"})
        local = next(item for item in provider_catalog() if item["id"] == "local")
        self.assertFalse(local["requires_api_key"])
        self.assertEqual(validate_provider_model("OpenAI", "gpt-5.6-luna"), ("openai", "gpt-5.6-luna"))
        with self.assertRaises(ValueError):
            validate_provider_model("custom", "model")
        self.assertEqual(
            _openai_text({"output": [{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}]}),
            "{}",
        )
        self.assertEqual(_anthropic_text({"content": [{"type": "text", "text": "{}"}]}), "{}")
        self.assertEqual(
            _chat_completion_text({"choices": [{"message": {"content": "{}"}}]}),
            "{}",
        )

    def test_local_ai_request_uses_only_server_configured_endpoint_and_key(self):
        response = MagicMock()
        payload = json.dumps(
            {"choices": [{"message": {"content": "{}"}}]}
        ).encode("utf-8")
        response.headers = {"Content-Length": str(len(payload))}
        response.iter_bytes.return_value = [payload]
        client = MagicMock()
        client.stream.return_value.__enter__.return_value = response
        result = _provider_request(
            client,
            "local",
            "Qwen2.5-Coder-7B-Instruct-GGUF",
            "server-owned-key",
            "20일 모멘텀 전략",
            local_base_url="http://ai:8080/v1/",
        )
        self.assertEqual(result, "{}")
        method, url = client.stream.call_args.args
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://ai:8080/v1/chat/completions")
        self.assertEqual(
            client.stream.call_args.kwargs["headers"],
            {"Authorization": "Bearer server-owned-key"},
        )
        self.assertEqual(
            client.stream.call_args.kwargs["json"]["response_format"],
            {"type": "json_object"},
        )

    def test_local_ai_readiness_requires_the_configured_model(self):
        response = MagicMock()
        payload = json.dumps(
            {"data": [{"id": "Qwen2.5-Coder-7B-Instruct-GGUF"}]}
        ).encode("utf-8")
        response.headers = {"Content-Length": str(len(payload))}
        response.iter_bytes.return_value = [payload]
        stream = MagicMock()
        stream.return_value.__enter__.return_value = response
        with patch("cloud_app.ai.httpx.stream", stream) as request:
            self.assertTrue(
                local_ai_ready(
                    base_url="http://ready-ai-test:8080/v1",
                    model="Qwen2.5-Coder-7B-Instruct-GGUF",
                    api_key="server-owned-key",
                    cache_seconds=15,
                )
            )
            self.assertTrue(
                local_ai_ready(
                    base_url="http://ready-ai-test:8080/v1",
                    model="Qwen2.5-Coder-7B-Instruct-GGUF",
                    api_key="server-owned-key",
                    cache_seconds=15,
                )
            )
        request.assert_called_once()

    def test_factor_compiler_is_signal_only_and_preview_forces_delay(self):
        dates = pd.date_range("2026-01-01", periods=24, freq="D")
        close = pd.DataFrame(
            {
                "AAA": range(100, 124),
                "BBB": [100.0] * 24,
            },
            index=dates,
            dtype=float,
        )
        spec = sample_spec()
        bundle = SimpleNamespace(index=dates, panels={"Close": close, "Volume": close * 1000})
        raw = compile_raw_scores(spec, bundle)
        self.assertGreater(raw.loc[dates[-1], "AAA"], raw.loc[dates[-1], "BBB"])
        self.assertIn("score.shift(1)", strategy_code_preview(spec))
        self.assertIn("backtest_core.run_backtest", strategy_code_preview(spec))

    def test_next_open_eligibility_uses_previous_completed_row(self):
        index = pd.date_range("2026-01-01", periods=3, freq="D")
        observed = pd.DataFrame({"AAA": [False, True, False]}, index=index)
        bundle = SimpleNamespace(data={}, snapshots=[], index=index)
        with patch(
            "cloud_app.strategies.build_strategy_eligibility_mask", return_value=observed
        ):
            delayed = eligibility_mask(sample_spec(), bundle, "strict")
            live = eligibility_mask(
                sample_spec(), bundle, "strict", delay_for_next_open=False
            )
        self.assertEqual(delayed["AAA"].tolist(), [False, False, True])
        self.assertEqual(live["AAA"].tolist(), [False, True, False])


class DashboardViewTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine, expire_on_commit=False)()

    def tearDown(self):
        self.session.close()

    def test_market_contract_keeps_missing_feeds_explicit(self):
        now = dt.datetime(2026, 8, 28, 3, 0, tzinfo=dt.timezone.utc)
        self.session.add(
            Quote(
                ticker="^GSPC",
                price=6500.25,
                bid=0,
                ask=0,
                volume=0,
                source="licensed_test_feed",
                observed_at=now - dt.timedelta(seconds=10),
            )
        )
        self.session.commit()
        result = market_overview(self.session, quote_interval_seconds=30, now=now)
        self.assertEqual([item["label"] for item in result["indices"]], [
            "코스피", "코스닥", "S&P 500", "다우", "나스닥"
        ])
        sp500 = next(item for item in result["indices"] if item["id"] == "sp500")
        kospi = next(item for item in result["indices"] if item["id"] == "kospi")
        self.assertTrue(sp500["is_realtime"])
        self.assertEqual(sp500["value"], 6500.25)
        self.assertEqual(kospi["status"], "awaiting_source")
        self.assertIsNone(kospi["value"])

    def test_sector_heatmap_is_equal_weight_and_reports_coverage(self):
        index = pd.DatetimeIndex(["2026-08-27", "2026-08-28"])
        close = pd.DataFrame(
            {"AAA": [100.0, 110.0], "BBB": [100.0, 90.0], "CCC": [50.0, 55.0]},
            index=index,
        )
        bundle = SimpleNamespace(index=index, panels={"Close": close}, fingerprint="dashboard-test")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sectors.json"
            path.write_text(json.dumps({"AAA": "tech", "BBB": "tech", "CCC": "health"}))
            result = sector_heatmap(bundle, path)
        tech = next(item for item in result["cells"] if item["id"] == "tech")
        health = next(item for item in result["cells"] if item["id"] == "health")
        self.assertAlmostEqual(tech["return_pct"], 0.0)
        self.assertAlmostEqual(health["return_pct"], 10.0)
        self.assertEqual(tech["label"], "IT")
        self.assertEqual(health["label"], "Health")
        self.assertEqual(result["taxonomy"], "us_equity_simplified_10_sector")
        self.assertEqual(result["coverage_pct"], 100.0)

    def test_sector_labels_stay_compact_for_heatmap_cards(self):
        self.assertEqual(SECTOR_LABELS, {
            "tech": "IT",
            "health": "Health",
            "finance": "Finance",
            "consumer": "Consumer",
            "industrial": "Industry",
            "reits": "REIT",
            "materials": "Material",
            "energy": "Energy",
            "communication": "Comm.",
            "utilities": "Utility",
        })

    def test_news_feed_accepts_only_http_links(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "news.json"
            path.write_text(json.dumps({
                "provider": "club-feed",
                "items": [
                    {"title": "Valid", "url": "https://example.com/story", "source": "Example"},
                    {"title": "Unsafe", "url": "javascript:alert(1)", "source": "Bad"},
                ],
            }))
            result = news_feed(path)
        self.assertEqual(result["status"], "ready")
        self.assertEqual([item["title"] for item in result["items"]], ["Valid"])

    def test_data_freshness_uses_completed_nyse_sessions(self):
        result = completed_session_freshness(
            dt.date(2026, 8, 24),
            now=dt.datetime(2026, 8, 27, 17, 0, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(result["expected_latest_completed_session"], dt.date(2026, 8, 26))
        self.assertEqual(result["trading_session_lag"], 2)
        self.assertFalse(result["fresh"])


class PaperLedgerTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)()
        user = User(
            id="u" * 32,
            email="member@example.com",
            display_name="Member",
            password_hash="unused",
        )
        strategy = Strategy(
            id="s" * 32,
            user_id=user.id,
            name="Strategy",
            description="",
            spec_json=sample_spec().model_dump_json(),
        )
        self.account = PaperAccount(
            id="a" * 32,
            user_id=user.id,
            strategy_id=strategy.id,
            name="Paper",
            initial_cash=100_000,
            cash=100_000,
        )
        self.session.add_all([user, strategy, self.account])
        self.session.commit()

    def tearDown(self):
        self.session.close()

    def test_personal_watchlist_is_empty_without_an_active_account(self):
        user = User(
            id="v" * 32,
            email="no-account@example.com",
            display_name="No Account",
            password_hash="unused",
        )
        self.session.add(user)
        self.session.commit()
        with patch("cloud_app.paper.get_dataset_bundle") as dataset:
            self.assertEqual(collect_watchlist(self.session, user_id=user.id), set())
        dataset.assert_not_called()

    def test_same_tick_member_quote_is_visible_before_fill_evaluation(self):
        self.session.autoflush = False
        self.session.add(
            MarketDataConnection(
                user_id=self.account.user_id,
                provider="kis",
                environment="paper",
                encrypted_api_key="encrypted-key",
                encrypted_api_secret="encrypted-secret",
                key_hint="••••1234",
                secret_hint="••••5678",
                verified_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        self.session.commit()
        observed = {}

        def collect_personal_quotes(session, _settings):
            count = store_member_quotes(
                session,
                self.account.user_id,
                [
                    QuoteValue(
                        ticker="AAPL",
                        price=222.0,
                        bid=221.0,
                        ask=223.0,
                        volume=10.0,
                        source="kis_member",
                        observed_at=dt.datetime.now(dt.timezone.utc),
                    )
                ],
            )
            return count, 0

        def inspect_engine_quotes(session):
            observed.update(quote_map(session, ["AAPL"], user_id=self.account.user_id))
            return 0

        provider = MagicMock()
        provider.fetch.return_value = []
        with (
            patch("cloud_app.worker.SessionLocal", return_value=self.session),
            patch("cloud_app.worker.acquire_lease", return_value=True),
            patch("cloud_app.worker.regular_market_open", return_value=True),
            patch("cloud_app.worker.apply_terminal_events", return_value={"settled": 0, "review_accounts": 0}),
            patch("cloud_app.worker.collect_watchlist", return_value=set()),
            patch("cloud_app.worker.collect_watchlist_ordered", return_value=()),
            patch("cloud_app.worker.collect_member_quotes", side_effect=collect_personal_quotes),
            patch("cloud_app.worker.rebalance_due_accounts", side_effect=inspect_engine_quotes),
            patch("cloud_app.worker.mark_and_stop_accounts", return_value=0),
            patch("cloud_app.worker.heartbeat"),
        ):
            run_paper_tick(provider, SimpleNamespace())
        self.assertEqual(observed, {"AAPL": 222.0})

    def test_shared_mode_ignores_legacy_member_quotes_for_paper_fills(self):
        now = dt.datetime.now(dt.timezone.utc)
        self.session.add_all(
            [
                MarketDataConnection(
                    user_id=self.account.user_id,
                    provider="kis",
                    environment="paper",
                    encrypted_api_key="legacy-encrypted-key",
                    encrypted_api_secret="legacy-encrypted-secret",
                    key_hint="••••1234",
                    secret_hint="••••5678",
                    verified_at=now,
                ),
                Quote(
                    ticker="AAPL",
                    price=111.0,
                    bid=110.0,
                    ask=112.0,
                    volume=10.0,
                    source="kis",
                    observed_at=now,
                ),
                MemberQuote(
                    user_id=self.account.user_id,
                    ticker="AAPL",
                    price=999.0,
                    bid=998.0,
                    ask=1000.0,
                    volume=10.0,
                    source="kis_member",
                    observed_at=now,
                ),
            ]
        )
        self.session.commit()
        with patch(
            "cloud_app.paper.get_settings",
            return_value=SimpleNamespace(member_credentials_enabled=False),
        ):
            prices = quote_map(
                self.session,
                ["AAPL"],
                user_id=self.account.user_id,
            )
        self.assertEqual(prices, {"AAPL": 111.0})

    def test_fill_dedupe_prevents_duplicate_paper_execution(self):
        first = _fill(
            self.session, self.account, "AAA", "BUY", 100, 10, 0.003,
            "rebalance", "same-event",
        )
        second = _fill(
            self.session, self.account, "AAA", "BUY", 100, 10, 0.003,
            "rebalance", "same-event",
        )
        self.session.commit()
        self.assertTrue(first)
        self.assertFalse(second)
        position = self.session.query(PaperPosition).one()
        self.assertAlmostEqual(position.shares, 100)
        self.assertEqual(self.session.query(PaperFill).count(), 1)
        self.assertAlmostEqual(self.account.cash, 98_997)

    def test_rebalance_retains_existing_quantity_like_backtest_core(self):
        self.account.cash = 90_000
        self.session.add(
            PaperPosition(
                account_id=self.account.id,
                ticker="AAA",
                shares=100,
                avg_price=100,
                last_price=100,
            )
        )
        self.session.commit()
        et_now = dt.datetime(
            2026, 8, 25, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=-4))
        )
        bundle = SimpleNamespace(
            index=pd.DatetimeIndex(["2026-08-24"]), forward_data_gate_ready=True
        )
        with (
            patch("cloud_app.paper._market_context", return_value=(et_now, True, True)),
            patch("cloud_app.paper.get_dataset_bundle", return_value=bundle),
            patch("cloud_app.paper.prev_trading_day", return_value=dt.date(2026, 8, 24)),
            patch("cloud_app.paper.latest_candidates", return_value=["AAA", "BBB"]),
            patch("cloud_app.paper.quote_map", return_value={"AAA": 100.0, "BBB": 100.0}),
        ):
            fill_count = rebalance_due_accounts(self.session)
        self.session.commit()

        positions = {
            row.ticker: row
            for row in self.session.query(PaperPosition)
            .filter(PaperPosition.account_id == self.account.id)
            .all()
        }
        self.assertEqual(fill_count, 1)
        self.assertAlmostEqual(positions["AAA"].shares, 100.0)
        self.assertAlmostEqual(positions["BBB"].shares, 500.0)
        self.assertAlmostEqual(self.account.cash, 39_850.0)

    def test_new_buy_and_stop_sale_are_visible_to_same_tick_equity(self):
        from cloud_app.database import EquityPoint
        from cloud_app.paper import mark_and_stop_accounts
        et_now = dt.datetime(2026, 8, 25, 10, tzinfo=dt.timezone(dt.timedelta(hours=-4)))
        bundle = SimpleNamespace(index=pd.DatetimeIndex(["2026-08-24"]), forward_data_gate_ready=True)
        with (
            patch("cloud_app.paper._market_context", return_value=(et_now, True, True)),
            patch("cloud_app.paper.get_dataset_bundle", return_value=bundle),
            patch("cloud_app.paper.prev_trading_day", return_value=dt.date(2026, 8, 24)),
            patch("cloud_app.paper.latest_candidates", return_value=["AAA"]),
            patch("cloud_app.paper.quote_map", return_value={"AAA": 100.0}),
        ):
            self.assertEqual(rebalance_due_accounts(self.session), 1)
            mark_and_stop_accounts(self.session)
        self.session.commit()
        holdings = self.session.query(PaperPosition).all()
        expected = self.account.cash + sum(row.shares * row.last_price for row in holdings)
        self.assertGreater(expected, 99000)
        self.assertAlmostEqual(self.session.query(EquityPoint).one().equity, expected)
        later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=6)
        with patch("cloud_app.paper.quote_map", return_value={"AAA": 50.0}), patch("cloud_app.paper.utcnow", return_value=later):
            self.assertEqual(mark_and_stop_accounts(self.session), 1)
        self.session.commit()
        self.assertEqual(self.session.query(PaperPosition).count(), 0)
        latest = self.session.query(EquityPoint).order_by(EquityPoint.observed_at.desc()).first()
        self.assertAlmostEqual(latest.equity, self.account.cash)

    def test_unresolved_exit_freezes_then_verified_cash_settles(self):
        self.session.add(
            PaperPosition(
                account_id=self.account.id,
                ticker="EXIT",
                shares=10,
                avg_price=20,
                last_price=18,
            )
        )
        self.session.commit()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            append_event(
                path,
                {
                    "ticker": "EXIT",
                    "effective_date": dt.date.today().isoformat(),
                    "event_type": "exchange_exit",
                    "status": "unresolved",
                },
            )
            result = apply_terminal_events(
                self.session, SimpleNamespace(terminal_events_path=path)
            )
            self.assertEqual(result["review_accounts"], 1)
            self.assertEqual(self.account.status, "review_required")
            from cloud_app.paper import mark_and_stop_accounts
            with patch("cloud_app.paper.quote_map", return_value={"EXIT": 1.0}):
                self.assertEqual(mark_and_stop_accounts(self.session), 0)
            self.assertEqual(self.session.query(PaperPosition).count(), 1)
            append_event(
                path,
                {
                    "ticker": "EXIT",
                    "effective_date": dt.date.today().isoformat(),
                    "event_type": "liquidation",
                    "status": "verified",
                    "cash_per_share": 4.0,
                    "source": "court filing",
                },
            )
            result = apply_terminal_events(
                self.session, SimpleNamespace(terminal_events_path=path)
            )
            self.session.commit()
            self.assertEqual(result["settled"], 1)
            self.assertEqual(self.account.status, "paused")
            self.assertEqual(self.session.query(PaperPosition).count(), 0)
            self.assertAlmostEqual(self.account.cash, 100_040)


if __name__ == "__main__":
    unittest.main()
