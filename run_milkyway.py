"""Q-LAB personal paper trading: setup once, start every day with one file."""
from __future__ import annotations
import argparse
from collections import deque
import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from cloud_app.native_platform import flock, LOCK_EX, LOCK_NB, protect_directory


def prepare():
    if not (3, 12) <= sys.version_info[:2] <= (3, 14):
        raise RuntimeError("Python 3.14를 설치해 주세요. 기존 3.12·3.13도 사용할 수 있습니다")
    executable = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if (ROOT / '.venv').exists() and os.path.samefile(sys.prefix, ROOT / '.venv'):
        return
    # Serialize installation as well as application starts.
    with (ROOT / ".setup.lock").open("a+") as lock:
        try:
            flock(lock, LOCK_EX | LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("다른 설치 창이 실행 중입니다. 그 창이 끝날 때까지 기다려 주세요") from None
        if not executable.exists():
            print("[1/2] 밀키웨이 전용 Python 환경을 준비합니다", flush=True)
            subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
        requirements = ROOT / "requirements-native.txt"
        fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
        marker = ROOT / ".venv/.qlab-requirements"
        if not marker.exists() or marker.read_text() != fingerprint:
            print("[2/2] 필요한 구성요소를 설치합니다. 처음 한 번은 몇 분 기다려 주세요", flush=True)
            subprocess.run([str(executable), "-m", "pip", "install", "--disable-pip-version-check",
                            "--no-input", "-r", str(requirements)], check=True)
            marker.write_text(fingerprint)
    arguments = [str(executable), str(Path(__file__).resolve()), *sys.argv[1:]]
    if os.name != 'nt':
        os.execv(str(executable), arguments)
    bootstrap_job = WindowsJob()
    child = subprocess.Popen(arguments, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    bootstrap_job.assign(child)
    try:
        try:
            result = child.wait()
        except KeyboardInterrupt:
            child.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                result = child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                result = 1
    finally:
        bootstrap_job.close()
    raise SystemExit(result)


def environment(port):
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR",
               "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "LANG", "LC_ALL"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    runtime = ROOT / "runtime"
    env.update(APP_ENV="development", APP_NAME="Milkyway Q-LAB", PERSONAL_LOCAL_MODE="true",
        PUBLIC_BASE_URL=f"http://localhost:{port}", ALLOWED_HOSTS="localhost,127.0.0.1",
        DATABASE_URL="sqlite:///" + (runtime / "club.sqlite3").as_posix(),
        DATASET_DIR=str(runtime / "personal-data"), SNAPSHOTS_GLOB=str(runtime / "personal-snapshots/*.json"),
        TERMINAL_EVENTS_PATH=str(runtime / "personal-events/events.jsonl"), LOCAL_DEMO_DATA="false",
        CREDENTIAL_BACKEND="local", MEMBER_CREDENTIALS_ENABLED="true", SHARED_AI_ENABLED="false",
        AUTHORITY_ENABLED="false", QUOTE_PROVIDER="member", QUOTE_INTERVAL_SECONDS="15",
        QUOTE_MAX_AGE_SECONDS="180", SHARED_QUOTE_TICK_DEADLINE_SECONDS="45", WORKER_STALE_SECONDS="150",
        MAX_USERS="1", MAX_ACCOUNTS_PER_USER="5", MAX_STRATEGIES_PER_USER="30",
        MAX_BACKTESTS_PER_USER_DAY="100", MAX_OUTSTANDING_BACKTESTS_PER_USER="8",
        MAX_BACKTEST_RESULT_BYTES="8388608", KIS_ENVIRONMENT="paper", PYTHONUTF8="1",
        PYTHONUNBUFFERED="1", PYTHONPATH=str(ROOT), XDG_CACHE_HOME=str(runtime / "cache"))
    return env


class WindowsJob:
    """Close the job on launcher exit to stop workers and their provider children."""
    def __init__(self):
        self.handle = None
        if os.name != "nt":
            return
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [("ProcessTime", ctypes.c_longlong), ("JobTime", ctypes.c_longlong),
                ("Flags", w.DWORD), ("MinWorkingSet", ctypes.c_size_t), ("MaxWorkingSet", ctypes.c_size_t),
                ("ActiveProcessLimit", w.DWORD), ("Affinity", ctypes.c_size_t),
                ("PriorityClass", w.DWORD), ("SchedulingClass", w.DWORD)]
        class Extended(ctypes.Structure):
            _fields_ = [("Basic", Basic), ("Io", ctypes.c_ulonglong * 6),
                ("ProcessMemory", ctypes.c_size_t), ("JobMemory", ctypes.c_size_t),
                ("PeakProcessMemory", ctypes.c_size_t), ("PeakJobMemory", ctypes.c_size_t)]
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.api.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        limits = Extended()
        limits.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.handle or not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, process):
        if self.handle and not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            process.kill()
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def free_port(requested):
    for candidate in (requested, 18080, 0):
        try:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", candidate))
                return listener.getsockname()[1]
        except OSError:
            pass
    raise RuntimeError("사용 가능한 로컬 주소가 없습니다")


def start(args):
    protect_directory(ROOT / "runtime")
    protect_directory(ROOT / "backups")
    protect_directory(ROOT / "logs")
    with (ROOT / "runtime/launcher.lock").open("a+") as lock:
        try:
            flock(lock, LOCK_EX | LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("밀키웨이가 이미 실행 중입니다. 먼저 열린 실행 창을 사용해 주세요") from None
        port = free_port(args.port)
        url = f"http://localhost:{port}"
        env = environment(port)
        workers = {
            "app": ["-m", "uvicorn", "cloud_app.main:app", "--host", "127.0.0.1", "--port", str(port), "--workers", "1"],
            "paper": ["-m", "cloud_app.worker"],
            "backtest": ["-m", "cloud_app.worker"],
            "personal-data": ["-m", "cloud_app.worker"],
            "backup": ["-m", "cloud_app.local_ops", "backup-loop", "--runtime", str(ROOT / "runtime"), "--destination", str(ROOT / "backups")],
        }
        processes, handles, retries = {}, [], {role: deque() for role in workers}
        job = WindowsJob()
        def spawn(role):
            output = (ROOT / "logs" / (role + ".log")).open("a", encoding="utf-8")
            handles.append(output)
            child_env = dict(env)
            if role in {"paper", "backtest", "personal-data"}:
                child_env["WORKER_ROLE"] = role
            process = subprocess.Popen([sys.executable, *workers[role]], cwd=ROOT,
                env=child_env, stdout=output, stderr=subprocess.STDOUT,
                start_new_session=os.name != "nt",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0)
            processes[role] = process
            job.assign(process)

        def wait_for(path, seconds=600):
            deadline = time.monotonic() + seconds
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while time.monotonic() < deadline:
                for role, process in processes.items():
                    if process.poll() is not None:
                        raise RuntimeError(role + " 실행에 실패했습니다. logs 폴더의 오류를 확인해 주세요")
                try:
                    with opener.open(f"http://127.0.0.1:{port}" + path, timeout=2) as response:
                        if response.status == 200:
                            return
                except (OSError, urllib.error.URLError):
                    time.sleep(0.5)
            raise RuntimeError("시작 대기 시간이 지났습니다. logs 폴더를 확인해 주세요")

        def interrupted(_signum, _frame):
            raise KeyboardInterrupt
        signal.signal(signal.SIGINT, interrupted)
        signal.signal(signal.SIGTERM, interrupted)
        if os.name == 'nt':
            signal.signal(signal.SIGBREAK, interrupted)
        try:
            print("밀키웨이를 시작합니다. 잠시 기다려 주세요", flush=True)
            spawn("app")
            wait_for("/health/startup")
            for role in workers:
                if role != "app":
                    spawn(role)
            wait_for("/health/ready")
            (ROOT / "runtime/url.txt").write_text(url, encoding="utf-8")
            print(f"\n실행 중: {url}\n이 창을 켜 두세요. 브라우저 창은 닫아도 됩니다.\n종료: 이 창에서 Ctrl+C\n", flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            while True:
                time.sleep(1)
                for role, process in list(processes.items()):
                    if process.poll() is None:
                        continue
                    now = time.monotonic()
                    queue = retries[role]
                    while queue and now - queue[0] > 300:
                        queue.popleft()
                    if len(queue) >= 3:
                        raise RuntimeError(role + " 오류가 반복돼 종료합니다. logs 폴더를 확인해 주세요")
                    queue.append(now)
                    print(f"{role} 프로세스를 다시 실행합니다. 기록은 유지합니다", flush=True)
                    if os.name != "nt":
                        try:
                            os.killpg(process.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                    spawn(role)
        except KeyboardInterrupt:
            print("\n종료 중입니다. 이 창이 끝날 때까지 기다려 주세요", flush=True)
        finally:
            for process in reversed(list(processes.values())):
                if os.name != "nt":
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                elif process.poll() is None:
                    process.terminate()
            for process in processes.values():
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            job.close()
            for handle in handles:
                handle.close()
            print("종료 완료. 다음에도 같은 폴더에서 같은 명령을 실행하세요", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "doctor", "backup"), nargs="?", default="start")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    prepare()
    if args.action == "start":
        start(args)
    else:
        result = subprocess.call([sys.executable, "-m", "cloud_app.local_ops", args.action,
            "--runtime", str(ROOT / "runtime"), "--destination", str(ROOT / "backups")],
            cwd=ROOT, env=environment(args.port))
        raise SystemExit(result)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print("\n실행을 완료하지 못했습니다:", error, file=sys.stderr)
        raise SystemExit(1)
