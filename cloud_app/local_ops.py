"""Personal-install backups, recovery and diagnostics (no broker network calls)."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import getpass
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import tempfile
import time
import uuid
import zipfile

MAX_ARCHIVE_BYTES = 4 * 1024**3
MAX_ARCHIVE_FILES = 50_000


@contextmanager
def _database(path, *, timeout=10):
    connection = sqlite3.connect(str(path), timeout=timeout)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _integrity(path: Path) -> None:
    with _database(path) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLite integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise RuntimeError("SQLite foreign key check failed")


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def create_backup(runtime: Path, destination: Path) -> Path:
    # The immutable generations are safe only if their *mutable pointer* is
    # captured under the same publication lock used by the history worker.
    history = runtime / "personal-data"
    history.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (history / "refresh.lock").open("a+") as lock:
        deadline = time.monotonic() + 100
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("History publication is busy; backup will retry")
                time.sleep(0.1)
        return _create_backup_locked(runtime, destination)


def _create_backup_locked(runtime: Path, destination: Path) -> Path:
    """SQLite online backup includes committed WAL transactions, even while trading.

    Runtime files are immutable generations/keys. Files already in use are never
    replaced by a refresh, so copying them after the DB snapshot is consistent.
    The archive contains local encryption roots: treat it as private key material.
    """
    database = runtime / "club.sqlite3"
    if not database.is_file():
        raise RuntimeError("No local database exists yet")
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination, 0o700)
    name = "milkyway-{}-{}.zip".format(dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"), uuid.uuid4().hex[:8])
    target = destination / name
    temporary = destination / ("." + name + ".partial")
    with tempfile.TemporaryDirectory(prefix="milkyway-backup-") as directory:
        copy = Path(directory) / "club.sqlite3"
        deadline = time.monotonic() + 60
        def progress(_status, _remaining, _total):
            if time.monotonic() > deadline:
                raise TimeoutError("SQLite backup timed out; previous backups preserved")
        with _database(database) as source, _database(copy) as dest:
            source.backup(dest, pages=256, progress=progress, sleep=0.05)
        _integrity(copy)
        entries = {"club.sqlite3": copy}
        graph_name = "company-details/graph.sqlite3"
        graph = runtime / graph_name
        if graph.is_symlink():
            raise RuntimeError("Runtime backup refuses symbolic links")
        if graph.is_file():
            graph_copy = Path(directory) / "company-graph.sqlite3"
            with _database(graph) as source, _database(graph_copy) as dest:
                source.backup(dest, pages=256, progress=progress, sleep=0.05)
            _integrity(graph_copy)
            entries[graph_name] = graph_copy
        for path in sorted(runtime.rglob("*")):
            relative = path.relative_to(runtime)
            if any(part.startswith(".restore-") for part in relative.parts) or relative.name == "RESTORE_IN_PROGRESS":
                continue
            if path.is_symlink():
                raise RuntimeError("Runtime backup refuses symbolic links")
            if not path.is_file() or path.name.startswith((".session-new-", ".secret-new-")):
                continue
            if path.name in {"club.sqlite3", "club.sqlite3-wal", "club.sqlite3-shm"} or path.suffix in {".lock", ".partial"}:
                continue
            if relative.as_posix() in {graph_name, graph_name + "-wal", graph_name + "-shm"}:
                continue
            entries[relative.as_posix()] = path
        if len(entries) > MAX_ARCHIVE_FILES or sum(path.stat().st_size for path in entries.values()) > MAX_ARCHIVE_BYTES:
            raise RuntimeError("Runtime exceeds backup size budget; export/archive old data first")
        manifest = {"format": "milkyway-personal-backup-v1", "created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "files": {}}
        try:
            with temporary.open("xb") as raw:
                os.chmod(temporary, 0o600)
                with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    for relative, path in entries.items():
                        # Hash the bytes actually archived, not a separate read of
                        # a mutable status/pointer file.
                        digest = hashlib.sha256()
                        size = 0
                        with path.open("rb") as source, archive.open(relative, "w") as out:
                            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                                out.write(chunk); digest.update(chunk); size += len(chunk)
                        manifest["files"][relative] = {"sha256": digest.hexdigest(), "size": size}
                    archive.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, sort_keys=True))
                raw.flush(); os.fsync(raw.fileno())
            os.replace(temporary, target)
            _sync_directory(destination)
        finally:
            temporary.unlink(missing_ok=True)
    return target


def _validate_archive(archive_path: Path, staged: Path) -> dict:
    if archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Backup archive is too large")
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(entries) > MAX_ARCHIVE_FILES + 1 or len(set(names)) != len(names):
            raise ValueError("Backup contains duplicate or excessive entries")
        if sum(entry.file_size for entry in entries) > MAX_ARCHIVE_BYTES:
            raise ValueError("Uncompressed backup exceeds size limit")
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in entry.filename or ":" in entry.filename or not path.parts:
                raise ValueError("Unsafe backup member path")
            mode = entry.external_attr >> 16
            if stat.S_IFMT(mode) not in {0, stat.S_IFREG} or entry.is_dir():
                raise ValueError("Backup must contain only regular files")
        if "BACKUP_MANIFEST.json" not in names or archive.getinfo("BACKUP_MANIFEST.json").file_size > 16 * 1024**2:
            raise ValueError("Backup manifest missing or oversized")
        manifest = json.loads(archive.read("BACKUP_MANIFEST.json"))
        if manifest.get("format") != "milkyway-personal-backup-v1" or not isinstance(manifest.get("files"), dict):
            raise ValueError("Unsupported backup format")
        if set(manifest["files"]) != set(names) - {"BACKUP_MANIFEST.json"} or "club.sqlite3" not in manifest["files"]:
            raise ValueError("Backup manifest does not match its contents")
        for name, expected in manifest["files"].items():
            target = staged.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with archive.open(name) as source, target.open("xb") as dest:
                shutil.copyfileobj(source, dest, length=1024 * 1024)
            os.chmod(target, 0o600)
            if target.stat().st_size != expected["size"] or _digest(target) != expected["sha256"]:
                raise ValueError("Backup checksum mismatch")
    _integrity(staged / "club.sqlite3")
    if (staged / "company-details/graph.sqlite3").exists():
        _integrity(staged / "company-details/graph.sqlite3")
    return manifest


def restore_backup(archive: Path, runtime: Path, destination: Path, *, replace: bool = False) -> dict:
    """Caller MUST stop app, paper, data, backtest and automatic backup services."""
    if (runtime / "club.sqlite3").exists() and not replace:
        raise ValueError("Existing runtime: stop services and explicitly pass --replace")
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Stage on the same filesystem, fully verify before touching current files.
    with tempfile.TemporaryDirectory(prefix=".restore-", dir=runtime) as directory:
        staged = Path(directory)
        manifest = _validate_archive(archive, staged)
        safety = create_backup(runtime, destination) if (runtime / "club.sqlite3").exists() else None
        marker = runtime / "RESTORE_IN_PROGRESS"
        marker.write_text(json.dumps({"archive": str(archive), "safety_backup": str(safety)}), encoding="utf-8")
        os.chmod(marker, 0o600)
        _sync_directory(runtime)
        # Older backups may predate all history/keys. Do not keep a newer
        # install's mutable pointers or signing/encryption roots in that case.
        for name in ("personal-data/current.json", "personal-data/refresh-status.json", ".session_secret", ".market_credential_secret", ".ai_credential_secret"):
            if name not in manifest["files"]:
                (runtime / name).unlink(missing_ok=True)
        # The DB is replaced last. A failed restore is recoverable from `safety`.
        for name in manifest["files"]:
            if name == "club.sqlite3":
                continue
            target = runtime / name
            cursor = runtime
            for part in PurePosixPath(name).parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise ValueError("Restore target contains symbolic links")
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.replace(staged / name, target)
        for suffix in ("-wal", "-shm"):
            (runtime / ("club.sqlite3" + suffix)).unlink(missing_ok=True)
            (runtime / ("company-details/graph.sqlite3" + suffix)).unlink(missing_ok=True)
        if "company-details/graph.sqlite3" not in manifest["files"]:
            (runtime / "company-details/graph.sqlite3").unlink(missing_ok=True)
        os.replace(staged / "club.sqlite3", runtime / "club.sqlite3")
        _sync_directory(runtime)
        # Reset stale process leases/sessions after recovery; holdings/results
        # remain untouched. Browser session signatures may use a restored key.
        with _database(runtime / "club.sqlite3") as db:
            for table in ("leases", "browser_sessions"):
                if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                    db.execute("DELETE FROM " + table)
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='runtime_heartbeats'").fetchone():
                # Account review reasons are user records, not worker liveness.
                db.execute("DELETE FROM runtime_heartbeats WHERE component NOT LIKE 'paper-account:%'")
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='backtest_jobs'").fetchone():
                db.execute("UPDATE backtest_jobs SET status='failed', error='백업 복원으로 중단된 작업입니다. 다시 실행해 주세요' WHERE status='running'")
        marker.unlink()
        _sync_directory(runtime)
        return {"restored": len(manifest["files"]), "safety_backup": str(safety) if safety else None}


def _backup_heartbeat(runtime: Path, detail: str) -> None:
    with _database(runtime / "club.sqlite3") as db:
        db.execute("INSERT INTO runtime_heartbeats(component,instance_id,observed_at,detail) VALUES(?,?,?,?) ON CONFLICT(component) DO UPDATE SET observed_at=excluded.observed_at,detail=excluded.detail",
                   ("local-backup", "local-backup", dt.datetime.now(dt.timezone.utc).isoformat(" "), detail))


def doctor(runtime: Path) -> dict:
    result = {"database": "missing", "workers": {}, "disk_free_bytes": shutil.disk_usage(runtime).free}
    if (runtime / "club.sqlite3").exists():
        _integrity(runtime / "club.sqlite3")
        result["database"] = "ok"
        with _database(runtime / "club.sqlite3") as db:
            for component, observed, detail in db.execute("SELECT component,observed_at,detail FROM runtime_heartbeats WHERE component IN ('paper-worker','backtest-worker','personal-data','local-backup')"):
                stamp = dt.datetime.fromisoformat(observed)
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=dt.timezone.utc)
                age = max(0, (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds())
                result["workers"][component] = {"age_seconds": round(age), "alive": age < 150, "detail": detail}
    from .config import get_settings
    from .personal_data import personal_data_status
    result["data"] = personal_data_status(get_settings())
    result["credentials"] = "not printed; verify in the local profile screen"
    return result


def reset_password(runtime: Path, email: str, password: str) -> None:
    from .security import hash_password, normalize_email
    encoded = hash_password(password)
    with _database(runtime / "club.sqlite3") as db:
        row = db.execute("SELECT id FROM users WHERE email=?", (normalize_email(email),)).fetchone()
        if row is None:
            raise ValueError("No account with this email exists")
        db.execute("UPDATE users SET password_hash=? WHERE id=?", (encoded, row[0]))
        db.execute("DELETE FROM browser_sessions WHERE user_id=?", (row[0],))
        db.execute("DELETE FROM login_throttles")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("backup", "backup-loop", "restore", "doctor", "reset-password"))
    parser.add_argument("archive", nargs="?")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--runtime", type=Path, default=Path("/app/runtime"))
    parser.add_argument("--destination", type=Path, default=Path("/app/backups"))
    args = parser.parse_args()
    if args.command == "reset-password":
        if not args.archive:
            parser.error("reset-password requires your account email")
        password = getpass.getpass("New password (10–128 characters): ")
        if password != getpass.getpass("Confirm password: "):
            raise ValueError("Passwords do not match")
        reset_password(args.runtime, args.archive, password)
        print("Password changed. Sign in again; trading records are unchanged.")
    elif args.command == "backup":
        print(json.dumps({"backup": str(create_backup(args.runtime, args.destination))}))
    elif args.command == "restore":
        if not args.archive:
            parser.error("restore requires an archive path")
        print(json.dumps(restore_backup(Path(args.archive), args.runtime, args.destination, replace=args.replace)))
    elif args.command == "doctor":
        print(json.dumps(doctor(args.runtime), ensure_ascii=False, default=str, indent=2))
    else:
        next_backup = 0.0
        detail = "waiting for initial backup"
        while True:
            try:
                if time.monotonic() >= next_backup:
                    path = create_backup(args.runtime, args.destination)
                    detail = "backup ok " + path.name
                    next_backup = time.monotonic() + 6 * 3600
                    print(json.dumps({"backup": path.name}), flush=True)
                _backup_heartbeat(args.runtime, detail)
            except Exception as exc:
                detail = "backup failed: " + type(exc).__name__
                print(json.dumps({"error": detail}), flush=True)
                try:
                    _backup_heartbeat(args.runtime, detail)
                except Exception:
                    pass
                next_backup = time.monotonic() + 60
            time.sleep(30)


if __name__ == "__main__":
    main()
