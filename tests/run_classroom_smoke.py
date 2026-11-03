"""Native classroom startup and durable restart; no provider credentials or calls."""
from pathlib import Path
import http.cookiejar
import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]


def main():
    if (ROOT / 'runtime/club.sqlite3').exists():
        raise RuntimeError('Use a fresh checkout; existing personal records are never touched')
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    process = None
    output = (ROOT / 'native-smoke.log').open('w', encoding='utf-8')

    def request(path, payload=None):
        headers = {'Origin': base, 'X-Milkyway-Local': '1', 'Sec-Fetch-Site': 'same-origin'}
        if payload is not None:
            headers['Content-Type'] = 'application/json'
        message = urllib.request.Request(base + path, headers=headers,
            data=None if payload is None else json.dumps(payload).encode())
        with opener.open(message, timeout=5) as response:
            return json.loads(response.read())

    def start():
        env = dict(os.environ, PYTHONUTF8='1')
        return subprocess.Popen([sys.executable, str(ROOT / 'run_milkyway.py'),
            '--port', str(port), '--no-browser'], cwd=ROOT, env=env,
            stdout=output, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)

    def wait_ready():
        nonlocal base
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('Launcher exited before readiness')
            location = ROOT / 'runtime/url.txt'
            if location.exists():
                base = location.read_text(encoding='utf-8').strip().replace('localhost', '127.0.0.1')
            try:
                if request('/health/ready')['status'] == 'ready':
                    return
            except OSError:
                time.sleep(.5)
        raise RuntimeError('Readiness deadline exceeded')

    def stop():
        if process and process.poll() is None:
            if os.name == 'nt':
                # Closing the parent also tests the kill-on-close job boundary.
                process.terminate()
            else:
                process.send_signal(signal.SIGINT)
            process.wait(timeout=30)

    try:
        process = start()
        wait_ready()
        first = request('/api/auth/local', {})
        assert first['id'] and first['csrf']
        print('PASS startup, local account, all required worker heartbeats', flush=True)
        duplicate = subprocess.run([sys.executable, str(ROOT / 'run_milkyway.py'), '--no-browser'],
            cwd=ROOT, env=dict(os.environ, PYTHONUTF8='1'), capture_output=True, text=True, encoding='utf-8', timeout=15)
        assert duplicate.returncode == 1 and '이미 실행 중' in duplicate.stderr
        print('PASS duplicate launch blocked', flush=True)
        stop()
        with sqlite3.connect(ROOT / 'runtime/club.sqlite3') as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        process = start()
        wait_ready()
        assert request('/api/auth/local', {})['id'] == first['id']
        print('PASS shutdown and next-day restart preserve account', flush=True)
        stop()
        backup = subprocess.run([sys.executable, str(ROOT / 'run_milkyway.py'), 'backup'],
            cwd=ROOT, env=dict(os.environ, PYTHONUTF8='1'), capture_output=True, text=True, encoding='utf-8', check=True, timeout=30)
        assert Path(json.loads(backup.stdout)['backup']).is_file()
        print('PASS manual backup', flush=True)
    except Exception:
        output.flush()
        for path in [ROOT / 'native-smoke.log', *sorted((ROOT / 'logs').glob('*.log'))]:
            print('\nLOG:', path.name, '\n', path.read_text(encoding='utf-8', errors='replace')[-8000:], flush=True)
        raise
    finally:
        stop()
        output.close()


if __name__ == '__main__':
    main()
