"""ZIP update preservation, failure recovery, and native display supervision."""
import io
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import run_milkyway as launcher
import update_milkyway as updater
from cloud_app.native_platform import flock, LOCK_EX, LOCK_NB


REVISION = "a" * 40
BASE_FILES = {"run_milkyway.py": b"# updated launcher\n", "update_milkyway.py": b"# updater\n",
              "requirements-native.txt": b"-r requirements-native.lock\n",
              "requirements-native.lock": b"# lock\n", "cloud_app/native_platform.py": b"# platform\n"}


def archive(extra=None):
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as z:
        for name, data in {**BASE_FILES, **(extra or {})}.items():
            z.writestr("Milkyway-" + REVISION + "/" + name, data)
    return content.getvalue()


class NativeUpdateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "run_milkyway.py").write_bytes(b"# old launcher\n")

    def test_update_keeps_private_files_and_installs_new_code(self):
        private = {"runtime/club.sqlite3": b"synthetic ledger", "backups/previous.zip": b"backup",
                   ".env": b"synthetic private settings", ".env.example": b"synthetic personal example key",
                   ".venv/keep": b"environment", "logs/keep": b"log"}
        for name, data in private.items():
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        files = updater.archive_sources(archive({**{n: b"MUST NOT REPLACE" for n in private},
                                                 "cloud_app/.env": b"MUST NOT INSTALL"}))
        updater.apply_sources(self.root, files, REVISION)
        for name, data in private.items():
            self.assertEqual((self.root / name).read_bytes(), data)
        self.assertFalse((self.root / "cloud_app/.env").exists())
        self.assertEqual((self.root / "run_milkyway.py").read_bytes(), BASE_FILES["run_milkyway.py"])
        self.assertEqual(json.loads((self.root / ".milkyway-version.json").read_text())["commit"], REVISION)

    def test_failed_replace_restores_old_code_and_removes_new_files(self):
        original = (self.root / "run_milkyway.py").read_bytes()
        real_replace = os.replace
        failed = False
        def fail_once(source, target):
            nonlocal failed
            if Path(target).name == "requirements-native.txt" and not failed:
                failed = True
                raise OSError("synthetic write failure")
            return real_replace(source, target)
        with patch.object(updater.os, "replace", side_effect=fail_once):
            with self.assertRaises(OSError):
                updater.apply_sources(self.root, updater.archive_sources(archive()), REVISION)
        self.assertEqual((self.root / "run_milkyway.py").read_bytes(), original)
        self.assertFalse((self.root / "update_milkyway.py").exists())
        self.assertFalse((self.root / ".milkyway-version.json").exists())

    def test_archive_rejects_unsafe_paths_and_symlinks(self):
        for path in ("../outside.py", "/outside.py", "root/../../outside.py", "root\\outside.py", "C:/outside.py"):
            with self.subTest(path=path):
                data = io.BytesIO()
                with zipfile.ZipFile(data, "w") as z:
                    z.writestr(path, b"unsafe")
                with self.assertRaises(RuntimeError):
                    updater.archive_sources(data.getvalue())
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            link = zipfile.ZipInfo("root/cloud_app/link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(link, "outside")
        with self.assertRaises(RuntimeError):
            updater.archive_sources(data.getvalue())

    def test_incomplete_or_oversized_archives_are_rejected(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            z.writestr("root/README.md", "not the exercise")
        with self.assertRaises(RuntimeError):
            updater.archive_sources(data.getvalue())
        with patch.object(updater, "MAX_SOURCE_BYTES", 1):
            with self.assertRaises(RuntimeError):
                updater.archive_sources(archive())

    def test_symlink_destination_cannot_overwrite_outside_installation(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "cloud_app").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            updater.apply_sources(self.root, updater.archive_sources(archive()), REVISION)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual((self.root / "run_milkyway.py").read_bytes(), b"# old launcher\n")

    def test_running_launcher_blocks_update_before_download(self):
        runtime = self.root / "runtime"
        runtime.mkdir()
        with (runtime / "launcher.lock").open("a+") as held:
            flock(held, LOCK_EX | LOCK_NB)
            with patch.object(updater, "download") as fetch:
                with self.assertRaisesRegex(RuntimeError, "Ctrl.C"):
                    updater.main(self.root)
                fetch.assert_not_called()

    def test_update_pins_archive_to_verified_branch_revision(self):
        metadata = json.dumps({"object": {"sha": REVISION}}).encode()
        with patch.object(updater, "download", side_effect=[metadata, archive()]) as fetch:
            updater.main(self.root)
        self.assertIn("/git/ref/heads/codex/week10-python", fetch.call_args_list[0].args[0])
        self.assertTrue(fetch.call_args_list[1].args[0].endswith("/zip/" + REVISION))

    def test_download_failure_does_not_change_code(self):
        with patch.object(updater, "download", side_effect=OSError("synthetic network failure")):
            with self.assertRaises(OSError):
                updater.main(self.root)
        self.assertEqual((self.root / "run_milkyway.py").read_bytes(), b"# old launcher\n")

    def test_parent_extraction_folder_is_resolved_but_git_checkout_is_refused(self):
        nested = self.root / "Milkyway-codex-week10-python"
        nested.mkdir()
        (self.root / "run_milkyway.py").rename(nested / "run_milkyway.py")
        self.assertEqual(updater.installation_root(self.root), nested.resolve())
        (nested / ".git").mkdir()
        with self.assertRaises(RuntimeError):
            updater.installation_root(self.root)


class NativeDisplaySupervisionTests(unittest.TestCase):
    def test_launcher_starts_restarts_and_stops_market_display_workers(self):
        with tempfile.TemporaryDirectory() as directory:
            processes, modules, log_handles = [], [], []
            class Process:
                def __init__(self, module):
                    self.module, self.pid = module, 10000 + len(processes)
                    self.returncode = None
                    self.waited = False
                def poll(self): return self.returncode
                def wait(self, **kwargs): self.waited = True; return 0
                def terminate(self): self.returncode = 0
                def kill(self): self.returncode = 1
            def spawn(arguments, **kwargs):
                module = arguments[2]
                process = Process(module)
                processes.append(process); modules.append(module)
                log_handles.append(kwargs['stdout'])
                return process
            loops = 0
            def tick(seconds):
                nonlocal loops
                loops += 1
                self.assertTrue(all(handle.closed for handle in log_handles),
                                'Parent log descriptors must be released after each child starts')
                if loops == 1:
                    next(p for p in processes if p.module == "cloud_app.market_worker").returncode = 1
                else:
                    raise KeyboardInterrupt
            response = SimpleNamespace(status=200)
            class Context:
                def __enter__(self): return response
                def __exit__(self, *args): pass
            opener = SimpleNamespace(open=lambda *a, **k: Context())
            with patch.object(launcher, "ROOT", Path(directory)), patch.object(launcher, "protect_directory", side_effect=lambda p: p.mkdir(parents=True, exist_ok=True)), patch.object(launcher.subprocess, "Popen", side_effect=spawn), patch.object(launcher.urllib.request, "build_opener", return_value=opener), patch.object(launcher.time, "sleep", side_effect=tick), patch.object(launcher.signal, "signal"), patch.object(launcher.os, "killpg", create=True), patch.object(launcher, "WindowsJob"):
                launcher.start(SimpleNamespace(port=0, no_browser=True))
            self.assertEqual(modules.count("cloud_app.market_worker"), 2)
            self.assertEqual(modules.count("cloud_app.market_detail_worker"), 1)
            # Every current child is awaited on shutdown, including the restarted feed.
            self.assertTrue(all(p.waited for p in processes if p.returncode is None))


if __name__ == "__main__":
    unittest.main()
