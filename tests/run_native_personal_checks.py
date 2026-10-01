"""Real local HTTP/process/SQLite checks, no Docker or real API calls.

Uses an exclusive temporary directory, an allowlisted environment, loopback-only
sockets and synthetic providers. Existing runtime, .env and Docker volumes are
never read as configuration or changed. Temporary evidence is retained.
"""
from __future__ import annotations
import datetime as dt
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time

from tests.run_personal_checks import Client, EMAIL, PASSWORD, INVITE, free_loopback_port, wait_for

ROOT = Path(__file__).resolve().parents[1]


def run():
    output = Path(tempfile.mkdtemp(prefix="milkyway-native-check-"))
    root = output / "fixture"
    runtime = root / "runtime"
    runtime.mkdir(parents=True, mode=0o700)
    (root / "OFFLINE_TEST_ONLY").touch()
    key_file = root / ".env"
    key_file.write_text("OPENAI_API_KEY=synthetic-offline-key-never-valid\nOPENAI_MODEL=gpt-5.4-mini\nOPENAI_REASONING_EFFORT=none\n")
    key_file.chmod(0o600)
    port = free_loopback_port()
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "SYSTEMROOT", "WINDIR", "TMPDIR", "TEMP"}}
    env.update(APP_ENV="development", PERSONAL_LOCAL_MODE="true", LOCAL_DEMO_DATA="false",
        PUBLIC_BASE_URL=f"http://localhost:{port}", ALLOWED_HOSTS="localhost,127.0.0.1",
        DATABASE_URL="sqlite:///" + str(runtime / "club.sqlite3"), DATASET_DIR=str(runtime / "personal-data"),
        SNAPSHOTS_GLOB=str(runtime / "personal-snapshots/*.json"), TERMINAL_EVENTS_PATH=str(runtime / "events.jsonl"),
        CREDENTIAL_BACKEND="local", QUOTE_PROVIDER="member", SHARED_AI_ENABLED="false", AUTHORITY_ENABLED="false",
        CLUB_INVITE_CODE=INVITE, MAX_USERS="1", MAX_BACKTESTS_PER_USER_DAY="100",
        MAX_OUTSTANDING_BACKTESTS_PER_USER="8", PYTHONPATH=str(ROOT), PYTHONUNBUFFERED="1")
    processes, handles = {}, []
    report = {"status": "running", "external_api_calls": 0, "checks": [], "evidence": str(output)}

    def record(name):
        report["checks"].append(name)
        print("PASS:", name, flush=True)
        (output / "report.json").write_text(json.dumps(report, indent=2))

    def command(role):
        return [sys.executable, "-m", "tests.personal_process_fixture", role, str(root), "--port", str(port)]

    def start(role):
        handle = (output / (role + ".log")).open("a")
        handles.append(handle)
        processes[role] = subprocess.Popen(command(role), cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT)

    def stop(role, hard=False):
        process = processes.pop(role, None)
        if process and process.poll() is None:
            process.kill() if hard else process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)

    client = Client(f"http://127.0.0.1:{port}")
    try:
        start("app")
        wait_for("native app startup", lambda: client.request("/health/startup")[0] == 200, timeout=25)
        for role in ("paper", "backtest", "personal-data", "company-data"):
            start(role)
        wait_for("native workers", lambda: client.request("/health/ready")[0] == 200, timeout=25)
        assert client.request("/api/research/sessions")[0] == 401
        assert client.request("/api/company-details/kr_13/005930.KS")[0] == 401
        assert client.request('/api/company-entities/c_' + '0'*32)[0] == 401
        registration = client.expect(201, "/api/auth/register", "POST", {
            "email": EMAIL, "password": PASSWORD, "display_name": "Offline process check", "invite_code": INVITE})
        client.csrf = registration["csrf"]
        for asset in ("/", "/static/research.js", "/static/research/api.js", "/static/research/view.js", "/static/research/panel.js", "/static/company-relations.js", "/static/company-page.js", "/static/company.css"):
            client.expect(200, asset, raw=True)
        record("real_startup_workers_authentication_and_assets")
        client.csrf = "wrong"
        assert client.request("/api/research/sessions", "POST", {"title": "Denied"})[0] == 403
        assert client.request("/api/company-details/kr_13/005930.KS/refresh", "POST")[0] == 403
        client.csrf = registration["csrf"]
        client.expect(202, "/api/company-details/kr_13/005930.KS/refresh", "POST")
        wait_for("queued company worker", lambda: client.request("/api/company-details/kr_13/005930.KS")[1].get("description") == "Synthetic offline company collection", timeout=15)
        record("company_auth_csrf_queue_and_separate_worker")
        company = client.expect(200, "/api/company-details/kr_13/005930.KS")
        private = next(edge['target_id'] for edge in company['relations'] if edge['entity_id'] == 'Q123')
        private_path = '/api/company-entities/' + private
        page = client.expect(200, private_path)
        assert page['symbol'] is None and page['relations'][0]['target_id'] == company['entity_key']
        client.expect(202, private_path + '/refresh', 'POST')
        wait_for('private company worker', lambda: client.request(private_path)[1].get('description') == 'Synthetic offline company collection', timeout=15)
        record('canonical_private_company_navigation_and_reverse_evidence')
        room = client.expect(201, "/api/research/sessions", "POST", {"title": "Offline native check"})
        path = "/api/research/sessions/" + room["id"]
        turn = client.expect(201, path + "/messages", "POST", {"request_id": "native-request-1", "prompt": "AAPL MSFT momentum"})
        assert not (root / "synthetic-ai-calls.jsonl").exists()
        record("csrf_denied_and_preview_makes_no_provider_call")
        stop("app"); start("app")
        wait_for("restart", lambda: client.request("/health/startup")[0] == 200, timeout=25)
        assert client.expect(200, path)["turns"][0]["status"] == "awaiting_approval"
        approval = {"approved": True, "request_digest": turn["approval"]["request_digest"]}
        approved = client.expect(200, "/api/research/turns/" + turn["id"] + "/approve", "POST", approval)
        assert approved["status"] == "completed", approved
        client.expect(200, "/api/research/turns/" + turn["id"] + "/approve", "POST", approval)
        assert len((root / "synthetic-ai-calls.jsonl").read_text().splitlines()) == 1
        record("pending_approval_survives_restart_and_duplicate_calls_once_synthetic")
        subprocess.run(command("seed"), cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL, timeout=30)
        end = dt.date.today() - dt.timedelta(days=4)
        while end.weekday() >= 5:
            end -= dt.timedelta(days=1)
        body = {"request_id": "native-experiment-1", "strategy_ids": [approved["strategy_id"]],
            "start_date": str(end-dt.timedelta(days=180)), "split_date": str(end-dt.timedelta(days=90)),
            "end_date": str(end), "objective": "sharpe"}
        experiment = client.expect(201, path + "/experiments", "POST", body)
        def finished():
            experiment = client.expect(200, path)["experiments"][0]
            if experiment["status"] == "failed":
                raise AssertionError(experiment)
            return experiment["status"] == "completed"
        wait_for("real queued experiment workers", finished, timeout=30)
        account = client.expect(201, path + "/deploy", "POST", {"strategy_id": approved["strategy_id"],
            "name": "Offline paper", "request_id": "native-deploy-1"})
        client.expect(200, "/api/accounts/" + account["id"], "PATCH", {"status": "paused"})
        client.expect(200, "/api/accounts/" + account["id"] + "/history")
        before = client.expect(200, path)
        record("queued_backtests_pinned_version_paper_and_history")
        stop("app", hard=True); start("app")
        wait_for("crash recovery", lambda: client.request("/health/startup")[0] == 200, timeout=25)
        after = client.expect(200, path)
        assert before == after
        record("sigkill_recovery_preserves_research_and_paper")
        for role in list(processes):
            stop(role)
        from cloud_app.local_ops import create_backup, restore_backup
        archive = create_backup(runtime, output / "backups")
        restored = output / "restored"
        restore_backup(archive, restored, output / "restore-backups")
        with sqlite3.connect(runtime / "club.sqlite3") as original, sqlite3.connect(restored / "club.sqlite3") as restored_db:
            for table in ("research_sessions", "research_turns", "research_versions", "research_experiments", "paper_accounts", "backtest_jobs"):
                assert original.execute(f"SELECT * FROM {table}").fetchall() == restored_db.execute(f"SELECT * FROM {table}").fetchall()
        record("backup_restore_preserves_research_versions_and_ledger")
        report["status"] = "passed"
    except Exception:
        report["status"] = "failed"
        raise
    finally:
        for role in list(processes): stop(role)
        for handle in handles: handle.close()
        (output / "report.json").write_text(json.dumps(report, indent=2))
        print("Evidence:", output, flush=True)


if __name__ == "__main__":
    run()
