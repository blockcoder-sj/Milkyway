"""Owner-run loopback launcher for the personal paper workstation.

Only seven fixed Milkyway services can be started/restarted. There is no shell,
arbitrary command, Docker socket in the web app, volume deletion or restore API.
The browser uses an owner-only capability and an exact loopback Origin.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
PORT = 19480
SERVICE = "milkyway-local-control-v1"
SERVICES = ("app", "paper-worker", "personal-data", "backtest-worker", "market-data", "market-details", "backup")
STATE_DIR = ROOT / "runtime/local-control"
ACCOUNT = re.compile(r"^[a-f0-9]{32}$")
TOKEN = re.compile(r"^[a-f0-9]{64}$")


class ControlError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise ControlError("로컬 실행기의 리디렉션 응답은 허용하지 않습니다.")


def app_port(root=ROOT):
    value = os.environ.get("MILKYWAY_PORT")
    if value is None:
        try:
            with (root / ".env").open(encoding="utf-8") as stream:
                for line in stream:
                    match = re.fullmatch(r'\s*MILKYWAY_PORT\s*=\s*["\']?(\d+)["\']?\s*(?:#.*)?', line.rstrip())
                    if match:
                        value = match.group(1)
        except FileNotFoundError:
            pass
    value = value or "8080"
    if not re.fullmatch(r"\d{1,5}", value) or not 1024 <= int(value) <= 65535 or int(value) == PORT:
        raise ControlError("MILKYWAY_PORT 설정을 확인해 주세요.")
    return int(value)


def owner_token(directory=STATE_DIR):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if directory.is_symlink():
        raise ControlError("실행기 저장 폴더를 확인해 주세요.")
    if os.name != "nt":
        os.chmod(directory, 0o700)
    path = directory / "token"
    if path.is_symlink():
        raise ControlError("실행기 연결 파일은 바로가기를 사용할 수 없습니다.")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "r", encoding="ascii") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 65 or (os.name != "nt" and info.st_mode & 0o077):
                raise ControlError("실행기 연결 파일의 권한을 확인해 주세요.")
            value = stream.read(66).strip()
        if not TOKEN.fullmatch(value):
            raise ControlError("실행기 연결 파일을 확인해 주세요.")
        return value
    except FileNotFoundError:
        value = secrets.token_hex(32)
        descriptor, temporary = tempfile.mkstemp(prefix=".token-new-", dir=directory)
        try:
            with os.fdopen(descriptor, "w", encoding="ascii") as stream:
                stream.write(value)
                stream.flush(); os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                return owner_token(directory)
            return value
        finally:
            Path(temporary).unlink(missing_ok=True)


def loopback_json(url, *, token=None, origin=None, body=None, timeout=3):
    parts = urlsplit(url)
    if parts.scheme != "http" or parts.hostname not in {"localhost", "127.0.0.1"}:
        raise ControlError("로컬 주소만 사용할 수 있습니다.")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if origin:
        headers["Origin"] = origin
    payload = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode()
    request = Request(url, data=payload, headers=headers)
    # Never send a local capability through a configured corporate/VPN proxy.
    with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=timeout) as response:
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ControlError("실행기 응답이 너무 큽니다.")
        return json.loads(raw)


class Controller:
    def __init__(self, root=ROOT, token=None, port=None):
        self.root = root.resolve()
        self.token = token or owner_token()
        self.app_port = port or app_port(root)
        self.origins = {"http://localhost:{}".format(self.app_port), "http://127.0.0.1:{}".format(self.app_port)}
        self.app_url = "http://localhost:{}".format(self.app_port)
        self.docker = shutil.which("docker") or "/usr/local/bin/docker"
        self.lock = threading.Lock()
        self.deadline = None
        self.monitor_lock = threading.Lock()
        self.last_services = {"available": False, "services": {}, "checked_at": 0}
        self.job = {"state": "idle", "message": "시작·복구 실행기가 준비돼 있습니다.", "busy": False}

    def status(self):
        with self.lock:
            return dict(self.job)

    def progress(self, message):
        with self.lock:
            self.job["message"] = message
            self.job["updated_at"] = time.time()

    def command(self, args, *, timeout=30, input=None, check=True):
        if self.deadline is not None:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise ControlError("복구 점검 시간이 길어졌습니다. 저장된 기록은 보존돼 있으니 상태를 확인하고 다시 눌러 주세요.")
            timeout = min(timeout, remaining)
        try:
            result = subprocess.run([self.docker, *args], cwd=self.root, input=input,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ControlError("Docker 명령이 완료되지 않았습니다. Docker Desktop을 확인해 주세요.") from exc
        if check and result.returncode:
            # Docker output can include config details. Never relay it to browsers.
            raise ControlError("Docker 작업에 실패했습니다. 실행기 창에서 설치와 실행 상태를 확인해 주세요.")
        return result

    def compose(self, *args, **kwargs):
        return self.command(["compose", "-f", "compose.personal.yaml", *args], **kwargs)

    def _docker_ready(self):
        return self.command(["info", "--format", "{{.ServerVersion}}"], timeout=5, check=False).returncode == 0

    def _start_docker(self):
        if self._docker_ready():
            return
        self.progress("Docker Desktop을 시작하고 있습니다.")
        if sys.platform == "darwin":
            subprocess.Popen(["/usr/bin/open", "-a", "Docker"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os.name == "nt":
            desktop = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker/Docker/Docker Desktop.exe"
            if not desktop.is_file():
                raise ControlError("Docker Desktop을 먼저 설치해 주세요.")
            subprocess.Popen([str(desktop)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            self.command(["desktop", "start"], timeout=30, check=False)
        deadline = time.monotonic() + 150
        while time.monotonic() < deadline:
            if self._docker_ready():
                return
            time.sleep(2)
        raise ControlError("Docker 엔진이 아직 준비되지 않았습니다. 초기 안내를 확인한 뒤 다시 눌러 주세요.")

    def _inventory(self, timeout=30):
        text = self.compose("ps", "-a", "--format", "json", timeout=timeout).stdout.strip()
        if not text:
            return {}
        rows = json.loads(text) if text.startswith("[") else [json.loads(line) for line in text.splitlines()]
        return {row["Service"]: row for row in rows if row.get("Service") in SERVICES}

    def services(self):
        if not self.monitor_lock.acquire(blocking=False):
            return dict(self.last_services)
        try:
            if time.time()-self.last_services["checked_at"] < 3:
                return dict(self.last_services)
            try:
                inventory = self._inventory(timeout=4)
                self.last_services = {"available": True, "checked_at": time.time(),
                                      "services": {name: inventory.get(name, {}).get("State", "missing") for name in SERVICES}}
            except (ControlError, OSError, ValueError, TypeError, KeyError):
                self.last_services = {"available": False, "services": {}, "checked_at": time.time()}
            return dict(self.last_services)
        finally:
            self.monitor_lock.release()

    def _start_services(self, allow_build):
        inventory = self._inventory()
        missing = [name for name in SERVICES if name not in inventory]
        if missing and self.command(["image", "inspect", "milkyway-personal:local"], check=False).returncode:
            if not allow_build:
                raise ControlError("첫 설치가 필요합니다. Milkyway 시작·복구 파일을 실행해 주세요.")
            self.progress("처음 실행 환경을 설치합니다. 다운로드가 끝날 때까지 기다려 주세요.")
            self.compose("build", "app", timeout=900)
        # Starting existing containers preserves their image, configuration and volumes.
        # compose up for all services could otherwise recreate unrelated healthy workers.
        for name in SERVICES:
            row = inventory.get(name)
            if row is None:
                self.compose("up", "-d", "--no-deps", "--no-build", name, timeout=90)
            elif row.get("State") != "running":
                identifier = row.get("ID", "")
                if not re.fullmatch(r"[a-f0-9]{12,64}", identifier):
                    raise ControlError("실행 프로세스를 식별할 수 없습니다.")
                self.command(["start", identifier], timeout=45)

    def _web_ready(self):
        try:
            return loopback_json(self.app_url + "/health/startup", timeout=2).get("status") == "ready"
        except (OSError, URLError, ValueError, ControlError):
            return False

    def _wait_web(self):
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            if self._web_ready():
                return
            time.sleep(1)
        self.progress("웹 프로그램 응답이 없어 앱 프로세스를 다시 시작합니다.")
        self.compose("restart", "app", timeout=60)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if self._web_ready():
                return
            time.sleep(1)
        raise ControlError("웹 프로그램이 아직 응답하지 않습니다. 기존 기록은 보존돼 있습니다.")

    def _app_command(self, command, account_id=None, input=None):
        args = ["exec", "-T", "app", "python", "-m", "cloud_app.local_ops", command]
        if account_id:
            args.append(account_id)
        result = self.compose(*args, input=input, timeout=30)
        return json.loads(result.stdout)

    def _recover(self, account_id, allow_build):
        try:
            self.deadline = time.monotonic() + 300
            self.progress("실행 환경을 확인하고 있습니다.")
            self._start_docker()
            self.progress("밀키웨이와 자동매매 프로세스를 확인하고 있습니다.")
            self._start_services(allow_build)
            self._wait_web()
            self._app_command("pair-control", input=self.token)
            doctor = self._app_command("doctor")
            for service in ("paper-worker", "personal-data", "backtest-worker"):
                worker = doctor.get("workers", {}).get(service, {})
                if not worker.get("alive") or str(worker.get("detail", "")).startswith("error="):
                    self.progress("{} 프로세스를 다시 시작합니다.".format(service))
                    self.compose("restart", service, timeout=60)
            self.progress("기존 계좌의 잔고와 기록을 이어서 재개합니다.")
            result = self._app_command("resume", account_id)
            if not result.get("blocked"):
                deadline = time.monotonic() + 120
                alive = False
                while time.monotonic() < deadline:
                    doctor = self._app_command("doctor")
                    if all(doctor.get("workers", {}).get(name, {}).get("alive") for name in ("paper-worker", "personal-data")):
                        alive = True
                        break
                    self.progress("실행 프로세스의 첫 응답을 기다립니다. 기존 작업 잠금은 안전하게 유지합니다.")
                    time.sleep(2)
                if not alive:
                    raise ControlError("프로세스 응답을 확인하지 못했습니다. 자동매매가 정상이라고 표시하지 않습니다. 화면의 상태를 확인해 주세요.")
            with self.lock:
                self.job.update(state="blocked" if result.get("blocked") else "complete", busy=False,
                                message=result.get("message") or "복구 점검을 마쳤습니다. 화면에서 자동매매 상태를 확인해 주세요.",
                                result=result, finished_at=time.time())
        except Exception as exc:
            with self.lock:
                self.job.update(state="failed", busy=False, finished_at=time.time(),
                                message=str(exc) if isinstance(exc, ControlError) else "실행기 점검에 실패했습니다. 저장된 기록은 보존돼 있습니다.")
        finally:
            self.deadline = None

    def recover(self, account_id=None, *, allow_build=False):
        if account_id is not None and (not isinstance(account_id, str) or not ACCOUNT.fullmatch(account_id)):
            raise ValueError("Invalid account")
        with self.lock:
            if self.job.get("busy"):
                return dict(self.job)
            self.job = {"state": "running", "busy": True, "message": "복구를 시작합니다.", "started_at": time.time()}
            snapshot = dict(self.job)
        threading.Thread(target=self._recover, args=(account_id, allow_build), daemon=True).start()
        return snapshot


def handler_for(controller):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self):
            super().setup()
            self.connection.settimeout(3)

        def log_message(self, *_args):
            pass

        def _send(self, code, data, *, cors=False):
            encoded = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Connection", "close")
            if cors:
                self.send_header("Access-Control-Allow-Origin", self.headers["Origin"])
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
                self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()
            self.wfile.write(encoded)
            self.close_connection = True

        def _origin(self):
            return (self.headers.get("Host") in {"127.0.0.1:{}".format(PORT), "localhost:{}".format(PORT)}
                    and self.headers.get("Origin") in controller.origins)

        def _authorize(self):
            if not self._origin():
                self._send(403, {"error": "origin_denied"})
                return False
            if not hmac.compare_digest(self.headers.get("Authorization", "").encode("utf-8"), ("Bearer " + controller.token).encode("ascii")):
                self._send(403, {"error": "capability_required"}, cors=True)
                return False
            return True

        def do_OPTIONS(self):
            if self.path not in {"/v1/status", "/v1/services", "/v1/recover"} or not self._origin():
                self._send(403, {"error": "origin_denied"})
                return
            requested = {p.strip().lower() for p in self.headers.get("Access-Control-Request-Headers", "").split(",") if p.strip()}
            if self.headers.get("Access-Control-Request-Method") not in {"GET", "POST"} or not requested <= {"authorization", "content-type"}:
                self._send(403, {"error": "preflight_denied"})
                return
            self._send(200, {"ok": True}, cors=True)

        def do_GET(self):
            if self.path == "/health":
                if self.headers.get("Host") not in {"127.0.0.1:{}".format(PORT), "localhost:{}".format(PORT)}:
                    self._send(403, {"error": "host_denied"})
                else:
                    self._send(200, {"service": SERVICE})
                return
            if not self._authorize():
                return
            if self.path == "/v1/status":
                self._send(200, controller.status(), cors=True)
            elif self.path == "/v1/services":
                self._send(200, controller.services(), cors=True)
            else:
                self._send(404, {"error": "not_found"}, cors=True)

        def do_POST(self):
            if not self._authorize():
                return
            if self.path not in {"/v1/recover", "/v1/shutdown"}:
                self._send(404, {"error": "not_found"}, cors=True)
                return
            try:
                if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError("invalid body")
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 512:
                    raise ValueError("invalid body length")
                self.connection.settimeout(3)
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict) or set(body) - {"account_id"}:
                    raise ValueError("invalid fields")
                if self.path == "/v1/shutdown":
                    if controller.status().get("busy"):
                        self._send(409, {"error": "recovery_running"}, cors=True)
                    else:
                        self._send(200, {"stopping": True}, cors=True)
                        threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                self._send(202, controller.recover(body.get("account_id")), cors=True)
            except (ValueError, TypeError, OSError):
                self._send(422, {"error": "invalid_request"}, cors=True)

    return Handler


class LocalControlServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        # Disconnects/malformed local requests must not fill logs with request data.
        pass


def ensure_server(token, port):
    origin = "http://localhost:{}".format(port)
    try:
        loopback_json("http://127.0.0.1:{}/v1/status".format(PORT), token=token, origin=origin)
        return
    except HTTPError as exc:
        raise ControlError("실행기 포트를 다른 설치가 사용 중입니다. 다른 설치의 실행기를 먼저 종료해 주세요.") from exc
    except (URLError, OSError, ValueError):
        pass
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    log = STATE_DIR / "launcher.log"
    fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0), 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ControlError("실행기 로그 파일을 확인해 주세요.")
    with os.fdopen(fd, "a", encoding="utf-8") as output:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "serve"], cwd=ROOT,
                         stdout=output, stderr=output, start_new_session=os.name != "nt",
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        try:
            loopback_json("http://127.0.0.1:{}/v1/status".format(PORT), token=token, origin=origin)
            return
        except (URLError, OSError, ValueError):
            time.sleep(.2)
    raise ControlError("시작·복구 실행기를 열 수 없습니다. 포트와 Python 설치를 확인해 주세요.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "serve", "stop"), nargs="?", default="start")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    token = owner_token()
    port = app_port()
    if args.command == "serve":
        server = LocalControlServer(("127.0.0.1", PORT), handler_for(Controller(token=token, port=port)))
        server.serve_forever(poll_interval=.2)
        server.server_close()
        return
    origin = "http://localhost:{}".format(port)
    if args.command == "stop":
        loopback_json("http://127.0.0.1:{}/v1/shutdown".format(PORT), token=token, origin=origin, body={})
        print("시작·복구 실행기를 종료했습니다. 페이퍼 운용은 그대로 유지됩니다.")
        return
    bootstrap = Controller(token=token, port=port)
    print("Docker와 밀키웨이 설치를 확인합니다.", flush=True)
    bootstrap._start_docker()
    if bootstrap.command(["image", "inspect", "milkyway-personal:local"], check=False).returncode:
        print("첫 설치를 진행합니다. 다운로드가 끝날 때까지 기다려 주세요.", flush=True)
        bootstrap.compose("build", "app", timeout=900)
    ensure_server(token, port)
    loopback_json("http://127.0.0.1:{}/v1/recover".format(PORT), token=token, origin=origin, body={})
    deadline = time.monotonic() + 360
    previous = ""
    while True:
        result = loopback_json("http://127.0.0.1:{}/v1/status".format(PORT), token=token, origin=origin)
        if result["message"] != previous:
            print(result["message"], flush=True)
            previous = result["message"]
        if not result.get("busy"):
            break
        if time.monotonic() >= deadline:
            raise ControlError("복구가 계속 진행 중입니다. 잠시 뒤 실행기를 다시 열어 상태를 확인해 주세요.")
        time.sleep(1)
    if result["state"] == "failed":
        raise SystemExit(1)
    if not args.no_browser:
        import webbrowser
        webbrowser.open(origin + "/#strategy")


if __name__ == "__main__":
    try:
        main()
    except (ControlError, OSError, ValueError) as exc:
        print(str(exc) if isinstance(exc, ControlError) else "실행기를 시작할 수 없습니다. 설치와 포트를 확인해 주세요.", file=sys.stderr)
        raise SystemExit(1)
