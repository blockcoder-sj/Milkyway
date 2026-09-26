"""Recovery tests use real WAL databases and corrupt archives, never member data."""
import json
import concurrent.futures
from contextlib import closing
import fcntl
import threading
from unittest.mock import patch
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

from cloud_app.local_ops import create_backup, restore_backup


class LocalRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.backups = self.root / "backups"
        self.db = sqlite3.connect(str(self.runtime / "club.sqlite3"))
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE ledger(id INTEGER PRIMARY KEY, amount REAL)")
        self.db.execute("INSERT INTO ledger VALUES(1, 123.45)")
        self.db.commit()
        (self.runtime / ".market_credential_secret").write_text("synthetic-local-key" * 3)
        (self.runtime / "personal-data").mkdir()
        (self.runtime / "personal-data/current.json").write_text('{"generation":"synthetic"}')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_online_wal_backup_and_verified_restore_keep_committed_records(self):
        self.db.execute("INSERT INTO ledger VALUES(2, 678.90)")
        self.db.commit()
        self.db.execute("INSERT INTO ledger VALUES(3, 999)")
        archive = create_backup(self.runtime, self.backups)
        self.db.rollback()
        restored = self.root / "restored"
        report = restore_backup(archive, restored, self.backups)
        self.assertEqual(report["restored"], 3)
        with closing(sqlite3.connect(str(restored / "club.sqlite3"))) as connection:
            self.assertEqual(connection.execute("SELECT id,amount FROM ledger ORDER BY id").fetchall(), [(1,123.45),(2,678.9)])
        self.assertEqual((restored / ".market_credential_secret").read_text(), (self.runtime / ".market_credential_secret").read_text())
        self.assertFalse((restored / "RESTORE_IN_PROGRESS").exists())

    def test_replace_creates_safety_backup_and_restores_old_snapshot(self):
        archive = create_backup(self.runtime, self.backups)
        self.db.execute("INSERT INTO ledger VALUES(2,456)"); self.db.commit(); self.db.close()
        report = restore_backup(archive, self.runtime, self.backups, replace=True)
        self.assertTrue(Path(report["safety_backup"]).exists())
        with closing(sqlite3.connect(str(self.runtime / "club.sqlite3"))) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM ledger").fetchone()[0],1)
        safety = self.root / "safety"
        restore_backup(Path(report["safety_backup"]), safety, self.backups)
        with closing(sqlite3.connect(str(safety / "club.sqlite3"))) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM ledger").fetchone()[0],2)

    def test_tampered_archive_rejected_before_current_database_changes(self):
        archive = create_backup(self.runtime, self.backups)
        corrupt = self.backups / "corrupt.zip"
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(corrupt,"w") as target:
            for name in source.namelist():
                value = source.read(name)
                if name == ".market_credential_secret":
                    value = b"changed"
                target.writestr(name,value)
        with self.assertRaisesRegex(ValueError,"checksum"):
            restore_backup(corrupt,self.runtime,self.backups,replace=True)
        self.assertEqual(self.db.execute("SELECT amount FROM ledger").fetchone()[0],123.45)

    def test_path_traversal_rejected(self):
        archive = self.root / "traversal.zip"
        with zipfile.ZipFile(archive,"w") as target:
            target.writestr("../outside", "bad")
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            restore_backup(archive,self.root / "restore",self.backups)
        self.assertFalse((self.root / "outside").exists())

    def test_restore_keeps_account_review_reasons_and_resets_worker_liveness(self):
        self.db.execute("CREATE TABLE runtime_heartbeats(component TEXT PRIMARY KEY, detail TEXT)")
        self.db.executemany("INSERT INTO runtime_heartbeats VALUES(?,?)",[("paper-worker","running"),("paper-account:test","review_required split")])
        self.db.commit()
        archive=create_backup(self.runtime,self.backups)
        restored=self.root / "restored"
        restore_backup(archive,restored,self.backups)
        with sqlite3.connect(str(restored / "club.sqlite3")) as db:
            self.assertEqual(db.execute("SELECT component,detail FROM runtime_heartbeats").fetchall(),[("paper-account:test","review_required split")])

    def test_backup_waits_for_history_publication_and_captures_matching_pointer(self):
        history = self.runtime / "personal-data"
        blocked = threading.Event()
        original_flock = fcntl.flock

        def record_contention(descriptor, operation):
            try:
                return original_flock(descriptor, operation)
            except BlockingIOError:
                blocked.set()
                raise

        with (history / "refresh.lock").open("a+") as writer:
            original_flock(writer, fcntl.LOCK_EX)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                with patch("cloud_app.local_ops.fcntl.flock", side_effect=record_contention):
                    future = pool.submit(create_backup, self.runtime, self.backups)
                    try:
                        self.assertTrue(blocked.wait(5), "backup must contend for the writer publication lock")
                        generation = history / "generations" / "new-generation"
                        generation.mkdir(parents=True)
                        (generation / "prices.json").write_text('{"AAPL":100}')
                        (history / "current.json").write_text('{"generation":"new-generation"}')
                        self.assertFalse(future.done())
                    finally:
                        original_flock(writer, fcntl.LOCK_UN)
                    archive = future.result(timeout=10)
        with zipfile.ZipFile(archive) as backup:
            self.assertEqual(json.loads(backup.read("personal-data/current.json"))["generation"], "new-generation")
            self.assertIn("personal-data/generations/new-generation/prices.json", backup.namelist())

    def test_restoring_pre_data_backup_removes_newer_mutable_pointers(self):
        (self.runtime / "personal-data/current.json").unlink()
        (self.runtime / ".market_credential_secret").unlink()
        archive = create_backup(self.runtime, self.backups)
        (self.runtime / "personal-data/current.json").write_text('{"generation":"newer"}')
        (self.runtime / "personal-data/refresh-status.json").write_text('{"error":"newer error"}')
        (self.runtime / ".market_credential_secret").write_text("newer-secret")
        old_generation = self.runtime / "personal-data/generations/cache"
        old_generation.mkdir(parents=True)
        (old_generation / "data").write_text("immutable cache")
        self.db.close()
        report = restore_backup(archive, self.runtime, self.backups, replace=True)
        self.assertTrue(Path(report["safety_backup"]).exists())
        self.assertFalse((self.runtime / "personal-data/current.json").exists())
        self.assertFalse((self.runtime / "personal-data/refresh-status.json").exists())
        self.assertFalse((self.runtime / ".market_credential_secret").exists())
        self.assertTrue((old_generation / "data").exists())

    def test_backup_does_not_include_temporary_restore_files(self):
        staged = self.runtime / ".restore-failed"
        staged.mkdir(); (staged / "private").write_text("staged")
        archive = create_backup(self.runtime,self.backups)
        with zipfile.ZipFile(archive) as handle:
            self.assertNotIn(".restore-failed/private",handle.namelist())


if __name__ == "__main__":
    unittest.main()
