"""Real route + PostgreSQL role controls, run only in the disposable PG runner.

Only provider I/O and the certified dataset are synthetic. Browser requests,
issuer authentication, DB grants/RLS, permits and work selection run real code.
"""

import datetime as dt
import importlib
import os
import secrets
import time
import unittest
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from cloud_app import config
from cloud_app.database import AuthoritySession, BacktestJob, Base, Invitation, MarketDataConnection, RuntimeSession, User, WorkClaim, bind_runtime_context, utcnow
from cloud_app.strategies import StrategySpec
from tests.postgres_checks import apply_security, role_password


class AuthorityHttpIntegrationTests(unittest.TestCase):
    def test_member_browser_ai_and_worker_flow_with_real_role_connections(self):
        database = "authority_http"
        with psycopg.connect(autocommit=True) as owner:
            owner.execute("CREATE DATABASE " + database)

        def engine_for(role):
            return create_engine(URL.create("postgresql+psycopg", username="postgres" if role == "owner" else "milkyway_" + role,
                password=os.environ["PGPASSWORD"] if role == "owner" else role_password(role),
                host=os.environ["PGHOST"], database=database), hide_parameters=True,
                connect_args={"options": "-c idle_in_transaction_session_timeout=1000"} if role == "backtest" else {})

        engines = {role: engine_for(role) for role in ("owner", "authority", "app", "paper", "backtest")}
        self.addCleanup(lambda: [engine.dispose() for engine in engines.values()])
        Base.metadata.create_all(engines["owner"])
        with psycopg.connect(dbname=database, autocommit=True) as owner:
            apply_security(owner)
        factories = {role: sessionmaker(bind=engine, class_=RuntimeSession, expire_on_commit=False, autoflush=False) for role, engine in engines.items()}
        shared = replace(config.get_settings(), authority_enabled=True, member_credentials_enabled=True,
            shared_ai_enabled=True, app_env="production", credential_backend="broker",
            allowed_hosts=("app.test",), public_base_url="https://app.test",
            credential_broker_url="https://broker.test", session_secret=secrets.token_urlsafe(32),
            credential_broker_app_token=secrets.token_urlsafe(32), credential_broker_paper_token=secrets.token_urlsafe(32),
            credential_broker_backtest_token=secrets.token_urlsafe(32), shared_ai_provider="openai",
            shared_ai_model="gpt-4.1-mini", quote_max_concurrent_requests=8, shared_quote_batch_size=200)
        broker_settings = replace(shared, public_base_url="https://broker.test", credential_backend="oci-kms", service_role="broker")
        with patch.object(config, "get_settings", return_value=shared):
            main = importlib.import_module("cloud_app.main")
        with patch.object(config, "get_settings", return_value=broker_settings):
            broker = importlib.import_module("cloud_app.credential_broker")
        from cloud_app import authority_routes, work_routes, work_authority, credential_broker_client, database as database_module
        BrokerQuote = broker.BrokerQuote

        spec = StrategySpec(name="Member strategy", factors=[{"kind": "momentum"}])
        expected_provider_owners = []

        def prepare(body, _identity):
            with psycopg.connect(dbname=database) as owner:
                self.assertEqual(owner.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=%s AND usename='milkyway_authority' AND state='idle in transaction'", (database,)).fetchone()[0], 0)
            expected_provider_owners.append(body.owner_id)
            return {"encrypted_api_key": "opaque-private-key", "encrypted_api_secret": "opaque-private-secret", "key_hint": "key", "secret_hint": "secret"}

        def quotes(body, tickers):
            expected_provider_owners.append(body.owner_id)
            self.assertEqual(tickers, ("AAPL",))
            return [BrokerQuote(ticker="AAPL", price=100, bid=99, ask=101, volume=1000, source="kis_member", observed_at=utcnow())]

        # Route factories captured these callables at import; replace their
        # delegated implementations, preserving actual request validation.
        def network(operation, body, deadline):
            self.assertEqual(operation, "prepare")
            return prepare(broker.MarketPrepareBody.model_validate(body), "trusted-browser")

        with ExitStack() as stack:
            for module, name, value in ((main, "settings", shared), (main, "SessionLocal", factories["app"]),
                    (database_module, "SessionLocal", factories["authority"]),
                    (authority_routes, "SessionLocal", factories["authority"]), (work_routes, "SessionLocal", factories["authority"]),
                    (broker, "settings", broker_settings), (broker, "_network_call", network),
                    (broker, "_member_quotes_inline", quotes), (work_authority, "regular_market_open", lambda *_: True),
                    (work_authority, "get_dataset_bundle", lambda *_: object()), (work_authority, "latest_candidates", lambda *_: ["AAPL"])):
                stack.enter_context(patch.object(module, name, value))
            # _member_quotes uses the same production process entry, returning
            # a bounded synthetic provider response after authoritative lookup.
            def network_operations(operation, body, deadline):
                if operation == "member":
                    return broker._quote_payload(quotes(broker.MarketCipherBody.model_validate(body["credential"]), tuple(body["tickers"])))
                return network(operation, body, deadline)
            stack.enter_context(patch.object(broker, "_network_call", network_operations))
            broker_http = TestClient(broker.app, base_url="https://broker.test")
            catalog = broker_http.get("/credentials/providers").json()["providers"]
            choices = {row["id"]: {item["id"] for item in row["environments"]} for row in catalog}
            self.assertEqual(choices, {"kis": {"paper", "real"}, "toss": {"live"}})
            clients = [TestClient(main.app, base_url="https://app.test") for _ in range(2)]
            stack.callback(broker_http.close)
            for client in clients:
                stack.callback(client.close)

            requests = []
            def transport(settings, role, path, payload, **_kwargs):
                requests.append((role, path))
                if path == "/v1/permits/shared-ai":
                    with psycopg.connect(dbname=database) as owner:
                        self.assertEqual(owner.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=%s AND usename='milkyway_app' AND state='idle in transaction'", (database,)).fetchone()[0], 0)
                result = broker_http.post(path, json=payload, headers={"Authorization": "Bearer " + credential_broker_client._token(settings, role)})
                if result.status_code >= 400:
                    raise credential_broker_client.CredentialBrokerError(result.json().get("detail", "Rejected"), result.status_code)
                return result.json()
            stack.enter_context(patch.object(credential_broker_client, "_request", transport))
            identities, strategies, accounts = [], [], []
            password = "Synthetic-Member-Password-0123456789"
            for index, client in enumerate(clients):
                email, invitation = f"http{index}@example.com", secrets.token_urlsafe(32)
                with factories["owner"]() as session:
                    session.add(Invitation.create(token=invitation, email=email, secret=broker_settings.session_secret, expires_at=utcnow() + dt.timedelta(hours=1)))
                    session.commit()
                result = client.post("/api/auth/register", json={"email": email, "display_name": "HTTP member", "password": password, "invite_code": invitation})
                self.assertEqual(result.status_code, 201, result.text)
                self.assertNotIn("session_token", result.json())
                self.assertIn("HttpOnly", result.headers["set-cookie"])
                self.assertIn("Secure", result.headers["set-cookie"])
                identity = client.get("/api/auth/me").json()
                identities.append(identity)
                headers = {"X-CSRF-Token": identity["csrf"]}
                self.assertEqual(client.post("/api/strategies", json={"spec": spec.model_dump(mode="json")}).status_code, 403)
                result = client.post("/api/strategies", json={"spec": spec.model_dump(mode="json")}, headers=headers)
                self.assertEqual(result.status_code, 201, result.text)
                strategies.append(result.json()["id"])
                member_accounts = []
                for account_index in range(2):
                    result = client.post("/api/accounts", json={"strategy_id": strategies[-1], "name": f"Account {account_index}"}, headers=headers)
                    self.assertEqual(result.status_code, 201, result.text)
                    member_accounts.append(result.json()["id"])
                accounts.append(member_accounts)
                self.assertEqual(client.put("/api/me/market-data-connection", json={}).status_code, 405)
                self.assertEqual(broker_http.post("/credentials/login", json={"email": email, "password": password}, headers={"Origin": "https://app.test"}).status_code, 403)
                result = broker_http.post("/credentials/login", json={"email": email, "password": password}, headers={"Origin": "https://broker.test"})
                self.assertEqual(result.status_code, 200, result.text)
                self.assertNotIn("session_token", result.json())
                browser_headers = {"Origin": "https://broker.test", "X-CSRF-Token": result.json()["csrf"]}
                payload = {"provider": "kis", "environment": "paper", "api_key": "synthetic-member-key", "api_secret": "synthetic-member-secret"}
                injected = broker_http.put("/credentials/market", json=payload | {"owner_id": "f" * 32}, headers=browser_headers)
                self.assertEqual(injected.status_code, 422)
                self.assertNotIn("synthetic-member", injected.text)
                result = broker_http.put("/credentials/market", json=payload, headers=browser_headers)
                self.assertEqual(result.status_code, 200, result.text)
                self.assertNotIn("opaque-private", result.text)
                self.assertEqual(expected_provider_owners[-1], identity["id"])
                metadata = client.get("/api/me/market-data-connection")
                self.assertEqual(metadata.status_code, 200, metadata.text)
                self.assertNotIn("opaque-private", metadata.text)

            self.assertEqual([row["id"] for row in clients[0].get("/api/strategies").json()], [strategies[0]])
            self.assertEqual(clients[0].patch("/api/accounts/" + accounts[1][0], json={"status": "paused"}, headers={"X-CSRF-Token": identities[0]["csrf"]}).status_code, 404)
            for role in ("app", "paper", "backtest"):
                credential_broker_client.broker_preflight(shared, role)
            self.assertIn(("backtest", "/v1/backtest-preflight"), requests)
            from cloud_app import worker
            job_id = secrets.token_hex(16)
            with factories["authority"]() as session:
                session.add(BacktestJob(id=job_id, user_id=identities[0]["id"], strategy_id=strategies[0],
                    start_date=dt.date(2026, 1, 1), end_date=dt.date(2026, 2, 1), bias_mode="strict"))
                session.commit()
            def slow_backtest(*_args, **_kwargs):
                # Exceeds the real PG role connection's test idle timeout.
                time.sleep(1.2)
                return {"final_equity": 100001}
            with patch.object(worker, "SessionLocal", factories["backtest"]), patch.object(worker, "get_settings", return_value=shared), patch.object(worker, "run_strategy_backtest", side_effect=slow_backtest):
                self.assertTrue(worker.process_one_backtest())
            with factories["authority"]() as session:
                completed = session.get(BacktestJob, job_id)
                self.assertEqual(completed.status, "completed")
                self.assertIn("100001", completed.result_json)
            app_headers = {"Authorization": "Bearer " + shared.credential_broker_app_token}
            paper_headers = {"Authorization": "Bearer " + shared.credential_broker_paper_token}
            self.assertEqual(broker_http.post("/v1/work/paper/next", json={}, headers=app_headers).status_code, 401)
            self.assertEqual(broker_http.post("/v1/work/paper/next", json={"owner_id": identities[1]["id"]}, headers=paper_headers).status_code, 422)
            work = broker_http.post("/v1/work/paper/next", json={}, headers=paper_headers)
            self.assertEqual(work.status_code, 200, work.text)
            raw_claim = work.json()["work"]["claim"]
            result = broker_http.post("/v1/work/paper/quotes", json={"claim": raw_claim}, headers=paper_headers)
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()["count"], 1)
            owner_id = expected_provider_owners[-1]
            selected = next(index for index, identity in enumerate(identities) if identity["id"] == owner_id)
            with factories["paper"]() as session:
                from cloud_app.database import PaperAccount, PaperPosition
                bind_runtime_context(session, claim_token=raw_claim)
                self.assertEqual(set(session.scalars(select(PaperAccount.id)).all()), set(accounts[selected]))
                for account_id in accounts[selected]:
                    session.add(PaperPosition(account_id=account_id, ticker="AAPL", shares=1, avg_price=100, last_price=100))
                session.commit()
                self.assertEqual(len(session.scalars(select(PaperPosition)).all()), 2)
            self.assertEqual(broker_http.post("/v1/work/paper/quotes", json={"claim": raw_claim}, headers=paper_headers).status_code, 403)
            self.assertEqual(broker_http.post("/v1/work/paper/complete", json={"claim": raw_claim}, headers=paper_headers).status_code, 200)
            with factories["paper"]() as session:
                bind_runtime_context(session, claim_token=raw_claim)
                self.assertEqual(session.scalars(select(PaperAccount.id)).all(), [])
            # App bearer alone cannot start provider work; a real browser
            # session and CSRF mint a payload-bound one-use permit.
            prompt = "Build a cautious strategy"
            self.assertEqual(broker_http.post("/v1/ai/shared-generate", json={"prompt": prompt}, headers=app_headers).status_code, 403)
            with patch.object(broker, "provider_secret", return_value="synthetic-shared-ai-0123456789"), patch.object(broker, "generate_strategy", return_value=(spec, "preview")) as provider:
                result = clients[0].post("/api/strategies/generate", json={"prompt": prompt}, headers={"X-CSRF-Token": identities[0]["csrf"]})
                self.assertEqual(result.status_code, 201, result.text)
                provider.assert_called_once()
            old_cookie = clients[0].cookies.get("session")
            self.assertEqual(clients[0].post("/api/auth/logout", headers={"X-CSRF-Token": identities[0]["csrf"]}).status_code, 204)
            clients[0].cookies.set("session", old_cookie)
            self.assertEqual(clients[0].get("/api/auth/me").status_code, 401)
            # Multiple successful logins must share the same ten-session cap.
            from cloud_app.authority import issue_session
            def concurrent_login(_index):
                with factories["authority"]() as session:
                    return issue_session(session, broker_settings, session.get(User, identities[0]["id"]))
            with ThreadPoolExecutor(max_workers=8) as pool:
                issued = list(pool.map(concurrent_login, range(24)))
            self.assertEqual(len({value["session_token"] for value in issued}), 24)
            with factories["authority"]() as session:
                self.assertEqual(len(session.scalars(select(AuthoritySession).where(AuthoritySession.user_id == identities[0]["id"])).all()), 10)
