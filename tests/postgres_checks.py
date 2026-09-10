"""Integration checks invoked only by run_postgres_checks.py."""

import hashlib
import os
import datetime as dt
import json
import secrets
import socket
from dataclasses import replace
from unittest.mock import patch
from pathlib import Path
import subprocess
import unittest
import tempfile

import psycopg
from psycopg import sql
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from cloud_app.authority import token_hash
from cloud_app import database as database_module
from cloud_app.config import get_settings
from cloud_app.database import (
    AdmittedTicker, AuthoritySession, BacktestJob, Base, MarketDataConnection, PaperAccount,
    PaperPosition, RuntimeSession, Strategy, User, WorkClaim, bind_runtime_context, utcnow,
)


ROLE_NAMES = ("app", "paper", "backtest", "scheduler", "backup", "authority")


def role_password(role):
    return "Synthetic-Role-Only-0123456789-" + role


def connect_role(role, database):
    return psycopg.connect(user="milkyway_" + role, password=role_password(role), dbname=database, autocommit=True)


def apply_security(connection):
    for name in ("runtime-roles.sql", "runtime-security.sql"):
        connection.execute(Path("/app/deploy/postgres", name).read_text())


class PostgreSQLIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {}
        with psycopg.connect(autocommit=True) as admin:
            # The real init-runtime-roles.sh ran in the temporary PG container.
            for role in ROLE_NAMES:
                row = admin.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolinherit,rolbypassrls FROM pg_roles WHERE rolname=%s", ("milkyway_" + role,)).fetchone()
                if row != (False, False, False, False, False):
                    raise AssertionError("Provisioned role lacks isolation: " + role)
            for mode in ("fresh", "upgrade"):
                database = "isolation_" + mode
                admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
                engine = create_engine(URL.create("postgresql+psycopg", username="postgres", password=os.environ["PGPASSWORD"], host=os.environ["PGHOST"], database=database), hide_parameters=True)
                if mode == "upgrade":
                    legacy = [table for name, table in Base.metadata.tables.items() if name not in {"authority_sessions", "operation_permits", "work_claims", "admitted_tickers", "work_resources"}]
                    Base.metadata.create_all(engine, tables=legacy)
                    with psycopg.connect(dbname=database, autocommit=True) as owner:
                        owner.execute(Path("/app/deploy/postgres/runtime-roles.sql").read_text())
                        owner.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO milkyway_app")
                Base.metadata.create_all(engine)
                auth = secrets.token_urlsafe(32)
                claim = secrets.token_urlsafe(32)
                backtest_claim = secrets.token_urlsafe(32)
                with sessionmaker(bind=engine)() as session:
                    for index, owner_id in enumerate(("a" * 32, "b" * 32)):
                        session.add(User(id=owner_id, email=f"{index}@example.com", display_name=f"Member {index}", password_hash="must-not-be-readable"))
                        session.flush()
                        strategy_id = str(index + 1) * 32
                        account_id = str(index + 3) * 32
                        session.add(Strategy(id=strategy_id, user_id=owner_id, name="Fixture", description="fixture", original_prompt="fixture", spec_json="{}", spec_version=1))
                        session.flush()
                        session.add(PaperAccount(id=account_id, user_id=owner_id, strategy_id=strategy_id, name="Fixture", initial_cash=1000, cash=1000, status="running"))
                        session.add(BacktestJob(id=str(index + 5) * 32, user_id=owner_id, strategy_id=strategy_id, status="running", bias_mode="strict", start_date=dt.date(2026, 1, 1), end_date=dt.date(2026, 2, 1)))
                        session.add(MarketDataConnection(user_id=owner_id, provider="kis", environment="paper", encrypted_api_key="opaque-private-key", encrypted_api_secret="opaque-private-secret", key_hint="key", secret_hint="secret"))
                        session.flush()
                        session.add(PaperPosition(account_id=account_id, ticker="AAPL", shares=1, avg_price=100, last_price=100))
                    session.add(AuthoritySession(token_hash=token_hash(auth), user_id="a" * 32, csrf="csrf-for-fixture", expires_at=utcnow() + dt.timedelta(minutes=10)))
                    session.add(WorkClaim(token_hash=token_hash(claim), service="paper", user_id="a" * 32, resource_id="3" * 32, strategy_id="1" * 32, tickers_json=json.dumps(["AAPL"]), credential_version="fixture", slot=1, expires_at=utcnow() + dt.timedelta(minutes=10)))
                    session.add(WorkClaim(token_hash=token_hash(backtest_claim), service="backtest", user_id="b" * 32, resource_id="6" * 32, strategy_id="2" * 32, tickers_json="[]", slot=1, expires_at=utcnow() + dt.timedelta(minutes=10)))
                    session.commit()
                with psycopg.connect(dbname=database, autocommit=True) as owner:
                    apply_security(owner)
                    apply_security(owner)
                    owner.execute("CREATE TABLE future_private_probe (value text)")
                cls.cases[database] = (auth, claim, backtest_claim)
                engine.dispose()

    def test_stolen_app_dsn_needs_independently_issued_raw_token(self):
        for database, (auth, _claim, _backtest) in self.cases.items():
            with self.subTest(database=database), connect_role("app", database) as app:
                self.assertEqual(app.execute("SELECT id FROM strategies").fetchall(), [])
                app.execute("SELECT set_config('milkyway.user_id', %s, false)", ("b" * 32,))
                self.assertEqual(app.execute("SELECT id FROM strategies").fetchall(), [])
                for value in (token_hash(auth), "X" * 43):
                    app.execute("SELECT set_config('milkyway.auth_token', %s, false)", (value,))
                    self.assertEqual(app.execute("SELECT id FROM strategies").fetchall(), [])
                app.execute("SELECT set_config('milkyway.auth_token', %s, false)", (auth,))
                self.assertEqual(app.execute("SELECT id FROM strategies").fetchall(), [("1" * 32,)])
                self.assertEqual(app.execute("SELECT account_id FROM paper_positions").fetchall(), [("3" * 32,)])
                self.assertEqual(app.execute("SELECT p.account_id FROM paper_positions p JOIN paper_accounts a ON a.id=p.account_id WHERE a.user_id=%s", ("b" * 32,)).fetchall(), [])
                for command in ("SELECT password_hash FROM users", "SELECT * FROM authority_sessions", "SELECT * FROM operation_permits", "SELECT * FROM work_claims", "SELECT * FROM work_resources", "SELECT * FROM admitted_tickers", "SELECT * FROM future_private_probe", "SELECT encrypted_api_key FROM market_data_connections", "SET ROLE milkyway_authority"):
                    with self.subTest(command=command), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        app.execute(command)
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    app.execute("INSERT INTO authority_sessions(token_hash,user_id,csrf,expires_at,created_at) VALUES (%s,%s,'forged',now()+interval '1 hour',now())", ("f" * 64, "b" * 32))
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    app.execute("INSERT INTO paper_accounts(id,user_id,strategy_id,name,initial_cash,cash,status,created_at) VALUES (%s,%s,%s,'Forged',1000,1000,'running',now())", ("9" * 32, "b" * 32, "2" * 32))
                self.assertEqual(app.execute("UPDATE paper_accounts SET status='paused' WHERE id=%s", ("4" * 32,)).rowcount, 0)

    def test_workers_are_bound_to_one_claim_and_tickers(self):
        for database, (_auth, claim, backtest) in self.cases.items():
            with self.subTest(database=database), connect_role("paper", database) as paper:
                self.assertEqual(paper.execute("SELECT id FROM paper_accounts").fetchall(), [])
                paper.execute("SELECT set_config('milkyway.claim_token', %s, false)", (claim,))
                self.assertEqual(paper.execute("SELECT id FROM paper_accounts").fetchall(), [("3" * 32,)])
                self.assertEqual(paper.execute("SELECT id FROM strategies").fetchall(), [("1" * 32,)])
                self.assertEqual(paper.execute("UPDATE paper_accounts SET cash=999 WHERE id=%s", ("4" * 32,)).rowcount, 0)
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    paper.execute("INSERT INTO paper_positions(account_id,ticker,shares,avg_price,last_price,updated_at) VALUES (%s,'MSFT',1,100,100,now())", ("3" * 32,))
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    paper.execute("SELECT encrypted_api_secret FROM market_data_connections")
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    paper.execute("INSERT INTO paper_fills(id,account_id,ticker,side,shares,price,fee,reason,dedupe_key,executed_at) VALUES (%s,%s,'AAPL','BUY',1,100,0,'rebalance',%s,now())",
                                  ("c" * 32, "3" * 32, "4" * 32 + ":2026-09-05:rebalance:AAPL:BUY"))
                paper.execute("INSERT INTO paper_fills(id,account_id,ticker,side,shares,price,fee,reason,dedupe_key,executed_at) VALUES (%s,%s,'AAPL','BUY',1,100,0,'rebalance',%s,now())",
                              ("d" * 32, "3" * 32, "3" * 32 + ":2026-09-05:rebalance:AAPL:BUY"))
                paper.execute("SELECT set_config('milkyway.claim_token', %s, false)", (backtest,))
                self.assertEqual(paper.execute("SELECT id FROM paper_accounts").fetchall(), [])
            with connect_role("backtest", database) as worker:
                worker.execute("SELECT set_config('milkyway.claim_token', %s, false)", (backtest,))
                self.assertEqual(worker.execute("SELECT id FROM backtest_jobs").fetchall(), [("6" * 32,)])
                self.assertEqual(worker.execute("SELECT id FROM strategies").fetchall(), [("2" * 32,)])
                self.assertEqual(worker.execute("UPDATE backtest_jobs SET progress=99 WHERE id=%s", ("5" * 32,)).rowcount, 0)

    def test_service_names_and_session_pool_context_are_isolated(self):
        for database, (auth, _claim, _backtest) in self.cases.items():
            with self.subTest(database=database), connect_role("scheduler", database) as scheduler:
                scheduler.execute("INSERT INTO leases(name,owner,expires_at) VALUES ('daily-data-refresh','fixture',now()+interval '1 minute')")
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    scheduler.execute("INSERT INTO leases(name,owner,expires_at) VALUES ('paper-engine','fixture',now()+interval '1 minute')")
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    scheduler.execute("INSERT INTO runtime_heartbeats(component,instance_id,observed_at,detail) VALUES ('paper-worker','fixture',now(),'forged')")
            engine = create_engine(URL.create("postgresql+psycopg", username="milkyway_app", password=role_password("app"), host=os.environ["PGHOST"], database=database), pool_size=1, max_overflow=0, hide_parameters=True)
            factory = sessionmaker(bind=engine, class_=RuntimeSession)
            try:
                with factory() as session:
                    bind_runtime_context(session, auth_token=auth)
                    self.assertEqual(session.scalars(select(Strategy.id)).all(), ["1" * 32])
                    session.rollback()
                    self.assertEqual(session.scalars(select(Strategy.id)).all(), ["1" * 32])
                    session.commit()
                    self.assertEqual(session.scalars(select(Strategy.id)).all(), ["1" * 32])
                    metadata = session.get(MarketDataConnection, "a" * 32)
                    self.assertEqual(metadata.key_hint, "key")
                with factory() as anonymous:
                    self.assertEqual(anonymous.scalars(select(Strategy.id)).all(), [])
            finally:
                engine.dispose()

    def test_trusted_corporate_action_recovers_a_frozen_account_without_credentials(self):
        from cloud_app.work_authority import issue_work, complete_work, consume_quote_work
        from cloud_app.paper import apply_terminal_events
        from cloud_app.strategies import StrategySpec
        from fastapi import HTTPException
        from terminal_events import append_event
        database = "isolation_fresh"
        engines = {role: create_engine(URL.create("postgresql+psycopg", username="milkyway_" + role,
            password=role_password(role), host=os.environ["PGHOST"], database=database), hide_parameters=True) for role in ("authority", "paper")}
        try:
            with psycopg.connect(dbname=database, autocommit=True) as owner:
                owner.execute("INSERT INTO users(id,email,display_name,password_hash,role,active,created_at) VALUES (%s,'action@example.com','Action','synthetic','member',true,now())", ("c" * 32,))
                spec = StrategySpec(name="Action fixture", factors=[{"kind": "momentum"}])
                owner.execute("INSERT INTO strategies(id,user_id,name,description,original_prompt,spec_json,spec_version,created_at) VALUES (%s,%s,'Action','','',%s,1,now())", ("7" * 32, "c" * 32, spec.model_dump_json()))
                owner.execute("INSERT INTO paper_accounts(id,user_id,strategy_id,name,initial_cash,cash,status,created_at) VALUES (%s,%s,%s,'Frozen',1000,1000,'review_required',now())", ("8" * 32, "c" * 32, "7" * 32))
                owner.execute("INSERT INTO paper_positions(id,account_id,ticker,shares,avg_price,last_price,updated_at) VALUES (%s,%s,'AAPL',1,100,100,now())", ("9" * 32, "8" * 32))
                owner.execute("INSERT INTO admitted_tickers(account_id,ticker,admitted_at) VALUES (%s,'AAPL',now())", ("8" * 32,))
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "events.jsonl"
                append_event(path, {"ticker": "AAPL", "effective_date": "2026-01-01", "event_type": "stock_merger", "status": "verified",
                                   "cash_per_share": 0, "successor_symbol": "MSFT", "share_ratio": 2, "source": "synthetic approved fixture"})
                append_event(path, {"ticker": "MSFT", "effective_date": "2026-02-01", "event_type": "stock_merger", "status": "verified",
                                   "cash_per_share": 0, "successor_symbol": "NVDA", "share_ratio": 2, "source": "synthetic approved successor fixture"})
                settings = replace(get_settings(), authority_enabled=True, terminal_events_path=path)
                authority_factory = sessionmaker(bind=engines["authority"], expire_on_commit=False, autoflush=False)
                with authority_factory() as session, patch("cloud_app.work_authority.regular_market_open", return_value=False):
                    work = issue_work(session, settings, "paper")
                    self.assertFalse(work["quotes_required"])
                    with self.assertRaises(HTTPException):
                        consume_quote_work(session, settings, work["claim"])
                from cloud_app import worker
                def finish(_settings, _role, claim):
                    with authority_factory() as session:
                        complete_work(session, claim, "paper")
                with patch.object(worker, "SessionLocal", sessionmaker(bind=engines["paper"], class_=RuntimeSession, autoflush=False)), \
                        patch.object(worker, "broker_next_work", side_effect=[work] + [None] * 7), \
                        patch.object(worker, "broker_work_quotes") as quote_request, \
                        patch.object(worker, "broker_complete_work", side_effect=finish):
                    worker.run_authorized_paper_tick(settings)
                    quote_request.assert_not_called()
                with authority_factory() as session:
                    self.assertEqual(session.get(PaperAccount, "8" * 32).status, "paused")
                    self.assertEqual([(row.ticker, row.shares) for row in session.scalars(select(PaperPosition).where(PaperPosition.account_id == "8" * 32)).all()], [("NVDA", 4)])
        finally:
            for engine in engines.values():
                engine.dispose()

    def test_startup_detects_missing_row_security_and_global_limit_is_not_hidden_by_rls(self):
        for database, (auth, _claim, _backtest) in self.cases.items():
            engine = create_engine(URL.create("postgresql+psycopg", username="milkyway_app", password=role_password("app"), host=os.environ["PGHOST"], database=database), hide_parameters=True)
            try:
                with patch.object(database_module, "engine", engine), patch.object(database_module, "settings", replace(get_settings(), authority_enabled=True)):
                    database_module.verify_database_schema()
                    with psycopg.connect(dbname=database, autocommit=True) as owner:
                        owner.execute("ALTER TABLE strategies DISABLE ROW LEVEL SECURITY")
                        try:
                            with self.assertRaises(RuntimeError):
                                database_module.verify_database_schema()
                        finally:
                            owner.execute("ALTER TABLE strategies ENABLE ROW LEVEL SECURITY")
                        owner.execute("UPDATE milkyway_private.limits SET value=2 WHERE name='max_outstanding_backtests_total'")
                        try:
                            with connect_role("app", database) as app:
                                app.execute("SELECT set_config('milkyway.auth_token', %s, false)", (auth,))
                                self.assertEqual(app.execute("SELECT count(*) FROM backtest_jobs").fetchone()[0], 1)
                                with self.assertRaises(psycopg.errors.CheckViolation):
                                    app.execute("INSERT INTO backtest_jobs(id,user_id,strategy_id,status,progress,bias_mode,start_date,end_date,created_at) VALUES (%s,%s,%s,'queued',0,'strict','2026-01-01','2026-02-01',now())", ("e"*32,"a"*32,"1"*32))
                        finally:
                            owner.execute("UPDATE milkyway_private.limits SET value=40 WHERE name='max_outstanding_backtests_total'")
            finally:
                engine.dispose()


class PostgreSQLTransportTests(unittest.TestCase):
    def test_tls_verifies_server_identity_and_plaintext_is_rejected(self):
        with psycopg.connect() as database:
            self.assertEqual(database.execute("SELECT ssl,version FROM pg_stat_ssl WHERE pid=pg_backend_pid()").fetchone(), (True, "TLSv1.3"))
        with self.assertRaises(psycopg.OperationalError):
            psycopg.connect(sslmode="disable")
        with self.assertRaises(psycopg.OperationalError):
            psycopg.connect(host="incorrect-server.invalid", hostaddr=socket.gethostbyname(os.environ["PGHOST"]))
        with self.assertRaises(psycopg.OperationalError):
            psycopg.connect(sslrootcert="/etc/ssl/certs/ca-certificates.crt")


class EncryptedRestoreIntegrationTests(unittest.TestCase):
    def test_real_dump_encrypt_restore_and_tamper_rejection(self):
        with psycopg.connect(autocommit=True) as database:
            database.execute("CREATE TABLE restore_probe (id integer PRIMARY KEY, payload text NOT NULL)")
            database.execute("INSERT INTO restore_probe VALUES (1, %s), (2, %s)", ("member one", "한글 데이터"))
            expected = database.execute("SELECT * FROM restore_probe ORDER BY id").fetchall()
        for tool in ("pg_dump", "pg_restore"):
            version = subprocess.check_output([tool, "--version"], text=True)
            self.assertRegex(version, r"PostgreSQL\) 16\.")

        private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        private_path = Path("/run/secrets/backup-private.pem")
        public_path = Path("/run/secrets/backup-public.pem")
        private_path.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        private_path.chmod(0o600)
        public_path.write_bytes(private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        public_path.chmod(0o600)
        subprocess.run(["sh", "/app/deploy/backup-once.sh"], check=True, capture_output=True)
        backup, = Path("/backups").glob("*.mwbak")
        self.assertEqual(list(Path("/tmp").glob("*.dump")), [])

        with psycopg.connect(autocommit=True) as database:
            database.execute("DROP TABLE restore_probe")
        restore = subprocess.run(["sh", "/app/deploy/restore.sh", str(backup)], capture_output=True, text=True)
        self.assertEqual(restore.returncode, 0, restore.stderr)
        with psycopg.connect() as database:
            self.assertEqual(database.execute("SELECT * FROM restore_probe ORDER BY id").fetchall(), expected)
        self.assertEqual(list(Path("/tmp").glob("*.dump")), [])

        changed = bytearray(backup.read_bytes())
        changed[-1] ^= 1
        backup.write_bytes(changed)
        # A matching public checksum cannot bypass authenticated encryption.
        Path(str(backup) + ".sha256").write_text(hashlib.sha256(changed).hexdigest() + "  " + backup.name + "\n")
        rejected = subprocess.run(["sh", "/app/deploy/restore.sh", str(backup)], capture_output=True)
        self.assertNotEqual(rejected.returncode, 0)
        with psycopg.connect() as database:
            self.assertEqual(database.execute("SELECT * FROM restore_probe ORDER BY id").fetchall(), expected)
        self.assertEqual(list(Path("/tmp").glob("*.dump")), [])


if __name__ == "__main__":
    if os.getenv("MILKYWAY_DISPOSABLE_POSTGRES_TEST") != "1" or not os.getenv("PGHOST", "").startswith("milkyway-check-"):
        raise SystemExit("Use tests/run_postgres_checks.py with an isolated test database")
    from tests.authority_http_checks import AuthorityHttpIntegrationTests
    # The fixture class must create the isolated runtime roles first.
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in (
        PostgreSQLIsolationTests, PostgreSQLTransportTests, EncryptedRestoreIntegrationTests, AuthorityHttpIntegrationTests,
    ))
    raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
