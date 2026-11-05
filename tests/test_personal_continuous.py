"""Accelerated sessions with real HTTP, spawned Toss adapter and durable SQLite.

Only the external market-data server and historical dataset are synthetic. No
real credentials, brokerage orders, or external AI/provider calls are used.
"""
import datetime as dt
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from contextlib import closing
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cloud_app import paper, personal_data, worker
from cloud_app.config import get_settings
from cloud_app.database import (
    Base, EquityPoint, MarketDataConnection, MemberQuote, PaperAccount, PaperFill,
    PaperPosition, RuntimeHeartbeat, Strategy, User,
)
from cloud_app.local_ops import create_backup, restore_backup
from cloud_app.market_data_credentials import encrypt_market_credential
from cloud_app.paper_sessions import session_bounds
from cloud_app.research_models import PersonalPaperSession, ResearchBase
from cloud_app.strategies import StrategySpec, get_dataset_bundle
from tests.test_personal_data import write_outcome

UTC = dt.timezone.utc


def toss_http_execute(payload, configuration):
    """Executed in the actual provider child; replace only its HTTP destination."""
    from cloud_app import worker as child_worker
    from cloud_app.toss_quotes import TossQuoteClient
    endpoint = os.environ["MILKYWAY_OFFLINE_TOSS_ENDPOINT"]
    if not endpoint.startswith("http://127.0.0.1:"):
        raise RuntimeError("Offline fixture requires a loopback endpoint")
    TossQuoteClient.base_url = endpoint
    return child_worker._personal_quote_execute(payload, configuration)


class ContinuousPaperTests(unittest.TestCase):
    last_report = {}

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="milkyway-continuous-")
        self.root = Path(self.directory.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.now = dt.datetime(2026, 11, 5, 14, 35, tzinfo=UTC)
        self.monotonic = 10_000.
        self.prices = {"AAA": 100., "BBB": 100.}
        self.omitted = set()
        self.quote_age = 0
        self.http_status = 200
        self.expire_once = False
        self.on_prices = None
        self.quote_calls = self.auth_calls = 0
        self.checks = []
        self.settings = replace(
            get_settings(), app_env="development", personal_local_mode=True,
            credential_backend="local", authority_enabled=False, shared_ai_enabled=False,
            member_credentials_enabled=True, quote_provider="member", quote_max_age_seconds=180,
            shared_quote_tick_deadline_seconds=30, local_demo_data=False,
            dataset_dir=self.runtime / "personal-data", snapshots_glob=str(self.runtime / "unused/*.json"),
            terminal_events_path=self.runtime / "events.jsonl",
            market_credential_secret="Offline-only-0123456789-abcdefghijklmnopqrstuvwxyz",
        )
        self.engine = create_engine("sqlite:///" + str(self.runtime / "club.sqlite3"))
        Base.metadata.create_all(self.engine)
        ResearchBase.metadata.create_all(self.engine)
        (self.runtime / "club.sqlite3").chmod(0o600)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            disable_nagle_algorithm = True

            def reply(self, status, payload):
                content = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(content)))
                if status == 429:
                    self.send_header("Retry-After", "1")
                self.end_headers()
                self.wfile.write(content)

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                if self.path != "/oauth2/token":
                    return self.reply(404, {})
                fixture.auth_calls += 1
                self.reply(200, {"access_token": "synthetic-token", "expires_in": 3600})

            def do_GET(self):
                parsed = urlsplit(self.path)
                if parsed.path != "/api/v1/prices":
                    return self.reply(404, {})
                fixture.quote_calls += 1
                if fixture.expire_once:
                    fixture.expire_once = False
                    return self.reply(401, {"error": {"code": "expired-token"}})
                if fixture.http_status != 200:
                    return self.reply(fixture.http_status, {"error": {"code": "rate-limit-exceeded"}})
                timestamp = (fixture.now - dt.timedelta(seconds=fixture.quote_age)).isoformat()
                symbols = parse_qs(parsed.query)["symbols"][0].split(",")
                result = [{"symbol": symbol, "lastPrice": str(fixture.prices[symbol]),
                           "currency": "USD", "timestamp": timestamp}
                          for symbol in symbols if symbol not in fixture.omitted]
                callback, fixture.on_prices = fixture.on_prices, None
                if callback:
                    callback()
                self.reply(200, {"result": result})

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.patches = [
            patch.dict(os.environ, {"MILKYWAY_OFFLINE_TOSS_ENDPOINT": f"http://127.0.0.1:{self.server.server_port}",
                                    "NO_PROXY": "127.0.0.1,localhost"}),
            patch.object(paper, "get_settings", return_value=self.settings),
            patch.object(worker, "get_settings", return_value=self.settings),
            patch.object(worker, "SessionLocal", self.sessions),
            patch.object(worker, "INSTANCE_ID", "continuous-fixture-first"),
            patch.object(worker, "_personal_quote_execute", toss_http_execute),
            patch.dict(worker._member_provider_cache, {}, clear=True),
            patch.dict(worker._member_retry_after, {}, clear=True),
            patch.object(paper, "utcnow", side_effect=lambda: self.now),
            patch.object(worker, "utcnow", side_effect=lambda: self.now),
            patch.object(worker.time, "monotonic", side_effect=lambda: self.monotonic),
            patch.object(paper, "get_dataset_bundle", side_effect=lambda: get_dataset_bundle(self.settings)),
            patch.object(personal_data._history_process, "run", side_effect=write_outcome),
        ]
        for item in self.patches:
            item.start()
        self.spec = StrategySpec.model_validate({
            "name": "Continuous fixture", "symbols": ["AAA", "BBB"],
            "factors": [{"kind": "momentum", "lookback": 2}],
            "filters": {"history_days": 20, "min_average_volume": 0},
            "portfolio": {"max_positions": 2, "rebalance_days": 3, "investment_fraction": .8,
                          "max_position_fraction": .5, "rebalance_weights": True, "stop_loss_pct": -.1},
        })
        with self.sessions() as session:
            user = User(email="continuous@example.test", display_name="Offline", password_hash="synthetic")
            session.add(user); session.flush()
            self.owner = user.id
            strategy = Strategy(user_id=user.id, name=self.spec.name, spec_json=self.spec.model_dump_json(), original_prompt="")
            session.add(strategy); session.flush()
            accounts = [PaperAccount(user_id=user.id, strategy_id=strategy.id, name=name,
                                     initial_cash=100000, cash=100000, created_at=self.now)
                        for name in ["Continuous", "One session"]]
            session.add_all(accounts); session.flush()
            self.account, self.daily_account = [account.id for account in accounts]
            opens, closes = session_bounds(self.now.date(), self.now)
            session.add(PersonalPaperSession(account_id=self.daily_account, session_date=self.now.date(),
                                             opens_at=opens, closes_at=closes))
            context = {"owner_id": user.id, "provider": "toss", "environment": "live"}
            session.add(MarketDataConnection(user_id=user.id, provider="toss", environment="live",
                encrypted_api_key=encrypt_market_credential("Synthetic-Client-ID-0123456789", "App Key", self.settings, **context),
                encrypted_api_secret=encrypt_market_credential("Synthetic-Client-Secret-0123456789", "App Secret", self.settings, **context),
                key_hint="test", secret_hint="test"))
            session.commit()
        for name in [".session_secret", ".market_credential_secret"]:
            path = self.runtime / name
            path.write_text(self.settings.market_credential_secret)
            path.chmod(0o600)
        self.refresh()

    def tearDown(self):
        worker._discard_member_provider(self.owner)
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()
        self.directory.cleanup()

    def refresh(self):
        status = personal_data.refresh_personal_data(self.spec.symbols, self.settings, now=self.now)
        self.assertTrue(status["ready"], status)

    def tick(self, seconds=15):
        self.monotonic += seconds
        worker.run_paper_tick(paper.MemberOnlyQuoteProvider(), self.settings)

    def snapshot(self):
        with self.sessions() as session:
            return {"fills": len(session.scalars(select(PaperFill)).all()),
                    "points": len(session.scalars(select(EquityPoint)).all()),
                    "cash": {row.id: row.cash for row in session.scalars(select(PaperAccount)).all()},
                    "positions": {row.account_id + ":" + row.ticker: row.shares
                                  for row in session.scalars(select(PaperPosition)).all()}}

    def pid(self):
        return worker._member_provider_cache[self.owner][1].runner._process.pid

    def test_sessions_outages_oauth_restart_rebalance_and_backup(self):
        started = time.perf_counter()
        self.tick()
        self.assertEqual(self.snapshot()["fills"], 4)
        first_pid = self.pid()
        first = self.snapshot()
        self.tick()
        self.assertEqual(self.snapshot(), first)
        self.assertEqual(self.pid(), first_pid)
        self.checks.append("first fills, repeated-tick idempotency and OAuth/process reuse")

        self.now += dt.timedelta(minutes=5)
        self.prices["AAA"] = 85.
        self.tick()
        self.assertEqual(self.snapshot()["fills"], 6)
        self.tick()
        self.assertEqual(self.snapshot()["fills"], 6)
        self.checks.append("one stop per holding despite repeated polls")

        self.http_status = 429
        before = self.snapshot()
        self.now += dt.timedelta(minutes=5)
        with self.assertLogs("cloud_app.worker", level="ERROR"):
            self.tick()
        self.assertEqual(self.snapshot(), before)
        with self.sessions() as session:
            self.assertEqual(session.scalars(select(MemberQuote)).all(), [])
        calls = self.quote_calls
        self.http_status = 200
        self.tick()
        self.assertEqual(self.quote_calls, calls)  # The retry backoff has not elapsed.
        self.monotonic += 60
        self.tick()
        recovered_pid = self.pid()
        self.assertNotEqual(recovered_pid, first_pid)
        self.checks.append("429 backoff, cached-quote invalidation, no fabricated fills/equity and recovery")

        self.expire_once = True
        auth = self.auth_calls
        self.tick()
        self.assertEqual(self.auth_calls, auth + 1)
        self.assertEqual(self.pid(), recovered_pid)
        self.checks.append("expired-token refresh without losing the provider process")

        before = self.snapshot()
        self.now += dt.timedelta(minutes=5)
        self.prices["BBB"] = 80.
        for age, omitted in [(600, set()), (-600, set()), (0, {"BBB"})]:
            self.quote_age, self.omitted = age, omitted
            self.tick()
            self.assertEqual(self.snapshot(), before)
        self.quote_age, self.omitted = 0, set()
        self.prices["BBB"] = 100.
        self.tick()
        self.checks.append("stale, future and partial quotes cannot trigger stops or complete equity marks")

        self.now = self.now.replace(hour=21, minute=0, second=0)
        before, calls = self.snapshot(), self.quote_calls
        self.tick()
        self.assertEqual(self.quote_calls, calls)
        self.assertEqual(self.snapshot()["fills"], before["fills"])
        with self.sessions() as session:
            self.assertEqual(session.get(PaperAccount, self.daily_account).status, "paused")
            run = session.get(PersonalPaperSession, self.daily_account)
            self.assertIsNotNone(run.completed_at)
            self.assertFalse(json.loads(run.summary_json)["closing_price_verified"])
        self.checks.append("date-limited session expiry retains balances without a fabricated closing sale")

        rebalance_dates = [dt.date(2026, 11, 5)]
        for day in [6, 7, 8, 9, 10, 11, 12, 13]:
            self.now = dt.datetime(2026, 11, day, 14, 35, tzinfo=UTC)
            self.monotonic += 3600
            if day in {7, 8}:
                before, calls = self.snapshot(), self.quote_calls
                self.tick()
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(self.quote_calls, calls)
                continue
            if day == 9:
                worker._discard_member_provider(self.owner)
                self.engine.dispose()
                worker.INSTANCE_ID = "continuous-fixture-restarted"
            if day == 13:
                self.prices["BBB"] = 120.
            self.refresh()
            self.tick()
            with self.sessions() as session:
                date = session.get(PaperAccount, self.account).last_rebalanced_on
                self.assertEqual(session.get(PaperAccount, self.daily_account).status, "paused")
            if date != rebalance_dates[-1]:
                rebalance_dates.append(date)
        self.assertEqual(rebalance_dates, [dt.date(2026, 11, 5), dt.date(2026, 11, 9), dt.date(2026, 11, 12)])
        self.checks.append("seven trading sessions, closed weekends, persistent restart and calendar-day rebalancing")

        polls = max(1, min(5000, int(os.getenv("MILKYWAY_TEST_SOAK_TICKS", "60"))))
        before, stable_pid = self.snapshot(), self.pid()
        threads_before = threading.active_count()
        fd_directory = next((path for path in [Path('/proc/self/fd'), Path('/dev/fd')] if path.is_dir()), None)
        fds_before = len(list(fd_directory.iterdir())) if fd_directory else None
        for _ in range(polls):
            self.now += dt.timedelta(seconds=15)
            self.tick()
        self.assertEqual(self.snapshot()["fills"], before["fills"])
        self.assertEqual(self.snapshot()["positions"], before["positions"])
        self.assertEqual(self.pid(), stable_pid)
        threads_after = threading.active_count()
        fds_after = len(list(fd_directory.iterdir())) if fd_directory else None
        self.assertLessEqual(threads_after, threads_before + 4)
        if fds_before is not None:
            self.assertLessEqual(fds_after, fds_before + 4)
        with self.sessions() as session:
            self.assertEqual(len(session.scalars(select(MemberQuote)).all()), 2)
            self.assertTrue(all(row.cash >= 0 for row in session.scalars(select(PaperAccount)).all()))
        self.checks.append(f"{polls} repeated HTTP/provider/SQLite ticks without duplicate fills or provider proliferation")

        self.now = self.now.replace(hour=20, minute=59, second=59)
        self.prices["BBB"] = 80.
        self.on_prices = lambda: setattr(self, "now", self.now + dt.timedelta(seconds=2))
        before = self.snapshot()
        self.tick()
        self.assertEqual(self.snapshot(), before)
        self.checks.append("quote I/O crossing the market close creates no late stop")

        self.engine.dispose()
        archive = create_backup(self.runtime, self.root / "backups")
        restored = self.root / "restored"
        restore_backup(archive, restored, self.root / "restore-backups")
        with closing(sqlite3.connect(self.runtime / "club.sqlite3")) as original, \
             closing(sqlite3.connect(restored / "club.sqlite3")) as recovered:
            for table in ["paper_accounts", "paper_positions", "paper_fills", "equity_points", "personal_paper_sessions", "market_data_connections"]:
                self.assertEqual(original.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall(),
                                 recovered.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall())
        self.checks.append("backup and restore retain accounts, positions, fills, valuations and encrypted synthetic credentials")
        type(self).last_report = {"checks": self.checks, "replayed_trading_sessions": 7,
            "repeated_ticks": polls, "quote_http_requests": self.quote_calls,
            "authentication_http_requests": self.auth_calls, "final_fills": self.snapshot()["fills"],
            "parent_threads_before": threads_before, "parent_threads_after": threads_after,
            "parent_fds_before": fds_before, "parent_fds_after": fds_after,
            "seconds": round(time.perf_counter() - started, 3), "real_broker_credentials_used": False,
            "real_external_provider_calls": 0, "accelerated_time": True}


if __name__ == "__main__":
    unittest.main()
