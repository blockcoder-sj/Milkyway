#!/usr/bin/env python3
"""Docker-only runtime operations; host Python uses the standard library only.

Run from any directory: python deploy/local_tools.py doctor|backup|restore FILE.
Restore deliberately stops all writers and keeps them stopped on any failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", str(ROOT / "compose.personal.yaml")]


def run(arguments, *, capture=False):
    return subprocess.run(arguments, cwd=ROOT, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor", "backup", "restore"))
    parser.add_argument("archive", nargs="?")
    parser.add_argument("--output", type=Path, default=ROOT / "backups")
    args = parser.parse_args()
    if args.command == "doctor":
        run(COMPOSE + ["ps"])
        run(COMPOSE + ["exec", "-T", "app", "python", "-m", "cloud_app.local_ops", "doctor"])
        return
    archive = Path(args.archive).resolve() if args.archive else None
    if args.command == "restore":
        if archive is None or not archive.is_file():
            parser.error("restore requires an existing .zip backup file")
        print("Stopping local processes for a verified restore. A safety backup is created first.", flush=True)
        run(COMPOSE + ["stop", "app", "paper-worker", "backtest-worker", "personal-data", "backup"])
    helper = "milkyway-recovery-" + uuid.uuid4().hex[:12]
    run(COMPOSE + ["run", "--no-deps", "-d", "--name", helper, "backup", "sleep", "600"])
    successful = False
    try:
        if args.command == "backup":
            result = run(["docker", "exec", helper, "python", "-m", "cloud_app.local_ops", "backup"], capture=True)
            path = json.loads(result.stdout)["backup"]
            args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
            output = args.output / Path(path).name
            run(["docker", "cp", helper + ":" + path, str(output)])
            try:
                output.chmod(0o600)
            except OSError:
                pass
            print("Private backup saved: " + str(output))
        else:
            # docker cp would create root:root mode0600 in the helper, which
            # its unprivileged app user cannot read. Stream as that user so
            # ownership and secret-file permissions are correct on every OS.
            script = "import os,sys,shutil\nfd=os.open('/tmp/restore.zip',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\nwith os.fdopen(fd,'wb') as out: shutil.copyfileobj(sys.stdin.buffer,out)"
            with archive.open("rb") as source:
                subprocess.run(["docker", "exec", "-i", helper, "python", "-c", script],
                               cwd=ROOT, stdin=source, check=True)
            run(["docker", "exec", helper, "python", "-m", "cloud_app.local_ops", "restore", "/tmp/restore.zip", "--replace"])
        successful = True
    finally:
        subprocess.run(["docker", "rm", "-f", helper], cwd=ROOT, check=False, stdout=subprocess.DEVNULL)
    if successful and args.command == "restore":
        run(COMPOSE + ["up", "-d"])
        print("Restore complete. Sign in again; holdings and history were restored.")


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        raise SystemExit("Operation failed: {}. After a failed restore, services stay stopped; fix the cause and rerun restore.".format(exc))
