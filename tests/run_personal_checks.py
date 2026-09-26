"""Opt-in HTTP/install/restart checks using only new, uniquely named Docker volumes.

Build the image separately, then run:
    python tests/run_personal_checks.py --image milkyway-personal:local

Default: internal Docker network, HTTP from inside the app container, and explicitly synthetic daily history. Host-port reachability is checked only with --online-history. No broker
keys, provider authentication, actual market quote or real orders are involved.
--online-history allows public Yahoo history requests only; broker keys are still
never accepted. Existing Docker projects/volumes and the user's runtime are untouched.
Containers/networks are removed at exit; named synthetic volumes are preserved and
listed in report.json so failure evidence is not destroyed.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import http.cookiejar
from http.cookies import SimpleCookie
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
EMAIL = "synthetic-personal-check@example.test"
PASSWORD = "Synthetic-Only-Personal-Checks-20260926!"
INVITE = "synthetic-personal-invite"
RUN_DEADLINE = None

HTTP_TRANSPORT = r'''
import base64,json,sys,urllib.error,urllib.request
payload=json.load(sys.stdin)
request=urllib.request.Request("http://localhost:8000"+payload["path"],method=payload["method"],headers=payload["headers"],data=payload["body"].encode() if payload["body"] is not None else None)
try:
 response=urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=15)
except urllib.error.HTTPError as error:
 response=error
with response:
 print(json.dumps({"status":response.status,"body":base64.b64encode(response.read()).decode(),"cookies":response.headers.get_all("Set-Cookie",[])}))
'''


# This fixture only changes the provider boundary inside one disposable exec.
# The actual validation, immutable publication and strategy engine still execute.
SEED_HISTORY = r'''
import datetime as dt, json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from cloud_app.config import get_settings
from cloud_app import personal_data as history
from price_data_pipeline import _atomic_price_frame, price_file_path, sha256_file

def synthetic(payload, configuration, **kwargs):
    result = {"prices": {}, "corporate_actions": {}}
    for offset, symbol in enumerate(payload["symbols"]):
        days = pd.bdate_range(end=payload["required_session"], periods=400)
        steps = np.arange(len(days), dtype=float)
        close = 90 + steps * (.04 + .01 * offset) + np.sin(steps / 7)
        frame = pd.DataFrame({"Open":close-.1,"High":close+1,"Low":close-1,"Close":close,"Volume":np.full(len(days),1_000_000)},index=days)
        path = price_file_path(Path(configuration["target"]) / "prices", symbol)
        _atomic_price_frame(frame,path)
        result["prices"][symbol] = {"rows":len(frame),"first_date":days.min().date().isoformat(),"last_date":days.max().date().isoformat(),"sha256":sha256_file(path),"action_checked_on":payload["action_day"]}
        result["corporate_actions"][symbol] = []
    return result

with patch.object(history._history_process,"run",side_effect=synthetic):
    status = history.refresh_personal_data(["AAPL","MSFT"],get_settings())
assert status["ready"],status
print(json.dumps({"fixture":"synthetic_daily_history","last_session":status["latest_session"]}))
'''


class Client:
    def __init__(self, base, transport=None):
        self.base = base
        self.transport = transport
        self.cookies = {}
        self.csrf = ""
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(self, path, method="GET", body=None, *, raw=False):
        headers = {"Content-Type": "application/json"}
        if self.csrf:
            headers["X-CSRF-Token"] = self.csrf
        if self.transport is not None:
            if self.cookies:
                headers["Cookie"] = "; ".join(key + "=" + value for key, value in self.cookies.items())
            result = json.loads(self.transport(json.dumps({"path": path, "method": method, "headers": headers,
                "body": json.dumps(body) if body is not None else None})))
            for encoded in result["cookies"]:
                parsed = SimpleCookie(); parsed.load(encoded)
                for key, value in parsed.items():
                    if value["max-age"] == "0":
                        self.cookies.pop(key, None)
                    else:
                        self.cookies[key] = value.value
            content = base64.b64decode(result["body"])
            return result["status"], content if raw else json.loads(content) if content else None
        request = urllib.request.Request(self.base + path, headers=headers, method=method,
                                         data=json.dumps(body).encode() if body is not None else None)
        try:
            response = self.opener.open(request, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            content = response.read()
            result = content if raw else json.loads(content) if content else None
            return response.status, result

    def expect(self, status, path, method="GET", body=None, *, raw=False):
        actual, result = self.request(path, method, body, raw=raw)
        if actual != status:
            # Responses contain no secret test credentials. Do not print cookies/CSRF.
            raise AssertionError(f"{method} {path}: HTTP {actual}, expected {status}; {str(result)[:500]}")
        return result

    def login(self):
        result = self.expect(200, "/api/auth/login", "POST", {"email": EMAIL, "password": PASSWORD})
        self.csrf = result["csrf"]


def wait_for(label, function, *, timeout=120, interval=1):
    deadline = min(time.monotonic() + timeout, RUN_DEADLINE or float("inf"))
    while time.monotonic() < deadline:
        try:
            result = function()
            if result:
                return result
        except (OSError, urllib.error.URLError, json.JSONDecodeError, RuntimeError):
            pass
        time.sleep(interval)
    raise TimeoutError(label + " did not become ready")


def free_loopback_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def snapshot(client):
    # Execution heartbeat details intentionally change across process restarts.
    accounts = client.expect(200, "/api/accounts")
    return {
        "strategies": client.expect(200, "/api/strategies"),
        "accounts": [{key: value for key, value in row.items() if key not in {"execution_status", "execution_detail"}}
                     for row in accounts],
        "backtests": client.expect(200, "/api/backtests"),
        "history": {row["id"]: client.expect(200, "/api/accounts/" + row["id"] + "/history") for row in accounts},
    }


def run_checks(args):
    global RUN_DEADLINE
    RUN_DEADLINE = time.monotonic() + 300
    output = (args.output or Path(tempfile.mkdtemp(prefix="milkyway-personal-evidence-"))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    project = "milkyway-personal-check-" + uuid.uuid4().hex[:12]
    port = free_loopback_port()
    config_path = output / "compose.check.json"
    report = {"project": project, "port": port, "image": args.image,
              "history_source": "Yahoo online" if args.online_history else "synthetic offline",
              "http_transport": "host localhost" if args.online_history else "HTTP inside app container (internal network)",
              "checks": [], "status": "running", "volumes_preserved": []}
    report_path = output / "report.json"
    compose = ["docker", "compose", "-f", str(config_path), "-p", project]
    started = False

    def record(name, **details):
        report["checks"].append({"name": name, "passed": True, **details})
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"check": name, "passed": True, **details}), flush=True)

    def command(*parts, input=None, log_output=True):
        completed = subprocess.run([*compose, *parts], cwd=ROOT, text=True, input=input,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45 if parts[0] in {"logs", "down"} else max(1, min(180, RUN_DEADLINE - time.monotonic())))
        with (output / "compose.log").open("a", encoding="utf-8") as log:
            log.write("COMMAND " + " ".join(parts[:5]) + "\n" + (completed.stdout + completed.stderr if log_output else "HTTP response omitted (test session privacy)") + "\n")
        if completed.returncode:
            raise RuntimeError("Compose command failed: " + " ".join(parts[:5]) + "; see compose.log")
        return completed.stdout

    try:
        # Refuse implicit pulls or a mutable build; caller chooses a built image.
        subprocess.run(["docker", "image", "inspect", args.image], check=True, capture_output=True)
        with tempfile.NamedTemporaryFile(prefix="milkyway-empty-env-", mode="w") as empty_environment:
            rendered = subprocess.run(
                ["docker", "compose", "--env-file", empty_environment.name, "-f", str(ROOT / "compose.personal.yaml"),
                 "config", "--format", "json"], cwd=ROOT, check=True, capture_output=True, text=True)
        config = json.loads(rendered.stdout)
        config["name"] = project
        for name, volume in config.get("volumes", {}).items():
            volume["name"] = project + "-" + name
            volume.pop("external", None)
            report["volumes_preserved"].append(volume["name"])
        for name, network in config.get("networks", {}).items():
            network["name"] = project + "-" + name
            network["internal"] = not args.online_history
            network.pop("external", None)
        for name, service in config["services"].items():
            service.pop("build", None)
            service["image"] = args.image
            service["pull_policy"] = "never"
            service.pop("container_name", None)
            service["environment"].update({"CLUB_INVITE_CODE": INVITE, "PUBLIC_BASE_URL": f"http://localhost:{port}"})
            # Reject accidental host binds or unknown shared runtime sources.
            for mount in service.get("volumes", []):
                if mount.get("type") != "volume" or mount.get("source") not in config["volumes"]:
                    raise RuntimeError("Check harness refuses non-isolated mounts")
            if name == "app":
                service["ports"] = [{"host_ip": "127.0.0.1", "published": str(port), "target": 8000, "protocol": "tcp"}]
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        command("config", "--quiet")
        started = True
        command("up", "-d", "--wait", "--wait-timeout", "120")
        # Docker Desktop may not publish internal-network ports to the host.
        # Keep offline services hermetic and run real HTTP against app loopback.
        transport = None if args.online_history else lambda payload: command(
            "exec", "-T", "app", "python", "-c", HTTP_TRANSPORT, input=payload, log_output=False)
        client = Client(f"http://localhost:{port}", transport=transport)
        wait_for("web startup", lambda: client.request("/health/startup")[0] == 200)
        public = client.expect(200, "/api/config")
        assert public["personal_local_mode"] is True and public["local_demo_data"] is False
        for asset in ("/", "/static/personal.js", "/static/app.js", "/static/profile.js"):
            assert client.expect(200, asset, raw=True)
        record("clean_startup_and_packaged_assets")
        registration = client.expect(201, "/api/auth/register", "POST", {
            "email": EMAIL, "password": PASSWORD, "display_name": "합성 HTTP 검증", "invite_code": INVITE})
        client.csrf = registration["csrf"]
        # Credentialless readiness is intentional: process liveness != trading readiness.
        wait_for("all worker heartbeats", lambda: client.request("/health/ready")[0] == 200)
        dashboard = client.expect(200, "/api/dashboard")
        assert dashboard["operational"]["status"] == "credentials_required", dashboard["operational"]
        assert client.request("/health/trading")[0] == 503
        record("registration_and_honest_credentialless_readiness")
        if not args.online_history:
            command("exec", "-T", "app", "python", "-", input=SEED_HISTORY)
        spec = {"name": "합성 검증 모멘텀", "symbols": ["AAPL", "MSFT"],
                "factors": [{"kind": "momentum", "lookback": 20, "weight": 1}],
                "filters": {"history_days": 60, "min_price": 5, "min_average_volume": 200000},
                "portfolio": {"max_positions": 2, "rebalance_days": 1, "cost_per_side": .003,
                              "stop_loss_pct": -.05, "initial_cash": 100000}}
        strategy = client.expect(201, "/api/strategies", "POST", {"spec": spec})
        account = client.expect(201, "/api/accounts", "POST", {"strategy_id": strategy["id"], "name": "합성 계좌"})
        # A historical backtest does not need today's corporate-action check.
        # Before the open, Yahoo may have no current-day row yet.
        wait_for("selected daily history", lambda: {"AAPL", "MSFT"}.issubset(
            set(client.expect(200, "/api/dashboard")["personal_data"].get("fresh_symbols", []))), timeout=240)
        dashboard = client.expect(200, "/api/dashboard")
        end = dt.date.fromisoformat(dashboard["data"]["last_completed_session"])
        start = end - dt.timedelta(days=180)
        job = client.expect(202, "/api/backtests", "POST", {"strategy_id": strategy["id"],
            "start_date": start.isoformat(), "end_date": end.isoformat(), "bias_mode": "exploratory"})

        def completed_backtest():
            row = next(row for row in client.expect(200, "/api/backtests") if row["id"] == job["id"])
            if row["status"] == "failed":
                raise AssertionError("Backtest failed: " + str(row.get("error")))
            return row if row["status"] == "completed" else None

        result = wait_for("backtest", completed_backtest, timeout=180)
        assert not result["result"]["certification_eligible"]
        assert result["result"]["metrics"]["trade_count"] > 0
        record("manual_strategy_history_and_exploratory_backtest")
        for status in ("paused", "active"):
            assert client.expect(200, "/api/accounts/" + account["id"], "PATCH", {"status": status})["status"] == status
        for kind in ("fills", "equity"):
            content = client.expect(200, f'/api/accounts/{account["id"]}/export?kind={kind}', raw=True)
            assert len(content.decode("utf-8-sig").splitlines()) >= 1
        exported = client.expect(200, "/api/backtests/export")
        assert job["id"] in {row["id"] for row in exported}
        # Freeze the ledger before comparing restarts. An active cash-only
        # account may legitimately gain an equity observation during market hours.
        client.expect(200, "/api/accounts/" + account["id"], "PATCH", {"status": "paused"})
        baseline = snapshot(client)
        (output / "snapshot.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
        record("pause_resume_full_exports_and_durable_snapshot")
        for name, action in (("normal_restart", ("restart",)),
                             ("sigkill_recovery", ("kill", "-s", "SIGKILL"))):
            command(*action)
            if name == "sigkill_recovery":
                command("up", "-d", "--wait", "--wait-timeout", "120")
            wait_for("web after " + name, lambda: client.request("/health/startup")[0] == 200)
            client.login()
            assert snapshot(client) == baseline, name + " changed durable state"
            record(name + "_preserves_strategy_account_backtest_history")
        command("stop", "paper-worker", "backtest-worker")
        # Accelerate only this isolated database's heartbeat clock; do not wait150s.
        command("exec", "-T", "app", "python", "-c", "import sqlite3; db=sqlite3.connect('/app/runtime/club.sqlite3'); db.execute(\"UPDATE runtime_heartbeats SET observed_at='2000-01-01 00:00:00' WHERE component IN ('paper-worker','backtest-worker')\"); db.commit(); db.close()")
        assert client.request("/health/startup")[0] == 200
        assert client.request("/health/ready")[0] == 503
        assert client.expect(200, "/api/dashboard")["operational"]["status"] == "worker_offline"
        record("stopped_workers_fail_readiness_while_web_stays_available", heartbeat_clock="accelerated")
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        if started:
            try:
                (output / "containers.log").write_text(command("logs", "--no-color", "--tail", "150"), encoding="utf-8")
            except Exception:
                pass
            try:
                command("down", "--timeout", "20")  # Deliberately never --volumes.
            except Exception as error:
                report["cleanup_error"] = str(error)
                report["status"] = "failed"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Evidence: " + str(report_path), flush=True)
        if report.get("cleanup_error"):
            raise RuntimeError("Disposable container cleanup failed; see report.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="existing packaged image to verify; no image build or pull")
    parser.add_argument("--online-history", action="store_true", help="opt into public Yahoo history instead of the offline fixture")
    parser.add_argument("--output", type=Path, help="directory for config, logs and JSON evidence")
    run_checks(parser.parse_args())


if __name__ == "__main__":
    main()
