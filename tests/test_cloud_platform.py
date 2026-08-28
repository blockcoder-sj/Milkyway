import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
from pydantic import ValidationError
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    MarketDataConnectionBody,
    PromptBody,
    ai_strategy,
    delete_ai_connection,
    delete_market_data_connection,
    put_ai_connection,
    put_market_data_connection,
)
from cloud_app.kis_quotes import (
    KisAuthenticationError,
    KisCredentials,
    KisQuoteClient,
    KisRateLimitError,
)
from cloud_app.market_data_credentials import decrypt_market_credential
from cloud_app.paper import (
    QuoteValue,
    _fill,
    apply_terminal_events,
    collect_watchlist,
    quote_map,
    rebalance_due_accounts,
    store_member_quotes,
)
from cloud_app.security import create_session, hash_password, parse_session, verify_password
from cloud_app.strategies import (
    StrategySpec,
    compile_raw_scores,
    eligibility_mask,
    strategy_code_preview,
)
from terminal_events import append_event
from cloud_app.worker import run_paper_tick


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
        self.assertEqual(decrypt_market_credential(stored.encrypted_api_key), api_key)
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
        self.assertEqual(quote_map(session, ["AAPL"], user_id=other.id), {"AAPL": 100.0})
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
        response.content = b"payload"
        response.json.return_value = payload
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
        response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
        client = MagicMock()
        client.post.return_value = response
        result = _provider_request(
            client,
            "local",
            "Qwen2.5-Coder-7B-Instruct-GGUF",
            "server-owned-key",
            "20일 모멘텀 전략",
            local_base_url="http://ai:8080/v1/",
        )
        self.assertEqual(result, "{}")
        url, = client.post.call_args.args
        self.assertEqual(url, "http://ai:8080/v1/chat/completions")
        self.assertEqual(
            client.post.call_args.kwargs["headers"],
            {"Authorization": "Bearer server-owned-key"},
        )
        self.assertEqual(
            client.post.call_args.kwargs["json"]["response_format"],
            {"type": "json_object"},
        )

    def test_local_ai_readiness_requires_the_configured_model(self):
        response = MagicMock()
        response.json.return_value = {
            "data": [{"id": "Qwen2.5-Coder-7B-Instruct-GGUF"}]
        }
        with patch("cloud_app.ai.httpx.get", return_value=response) as request:
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
        self.session = sessionmaker(bind=engine, expire_on_commit=False)()
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
            patch("cloud_app.worker.collect_member_quotes", side_effect=collect_personal_quotes),
            patch("cloud_app.worker.rebalance_due_accounts", side_effect=inspect_engine_quotes),
            patch("cloud_app.worker.mark_and_stop_accounts", return_value=0),
            patch("cloud_app.worker.heartbeat"),
        ):
            run_paper_tick(provider, SimpleNamespace())
        self.assertEqual(observed, {"AAPL": 222.0})

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
            self.assertEqual(self.account.status, "active")
            self.assertEqual(self.session.query(PaperPosition).count(), 0)
            self.assertAlmostEqual(self.account.cash, 100_040)


if __name__ == "__main__":
    unittest.main()
