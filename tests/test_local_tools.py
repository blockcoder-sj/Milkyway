"""Host recovery orchestration: stop writers and preserve selected worker state."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deploy import local_tools


class LocalToolsTests(unittest.TestCase):
    def restore(self, archive, services=(), failure=False):
        arguments = ["local_tools.py", "restore", str(archive), *services]

        def run(command, **kwargs):
            if failure and "restore" in command:
                raise subprocess.CalledProcessError(1, command)

        with patch("sys.argv", arguments), patch.object(local_tools, "run", side_effect=run) as commands, \
                patch.object(local_tools.subprocess, "run"):
            if failure:
                with self.assertRaises(subprocess.CalledProcessError):
                    local_tools.main()
            else:
                local_tools.main()
        return [call.args[0] for call in commands.call_args_list]

    def test_selected_services_keep_paper_and_backtest_stopped(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "backup.zip"
            archive.touch()
            selected = ["app", "personal-data", "market-data", "backup"]
            commands = self.restore(archive, ["--start-services", *selected])
        self.assertEqual(commands[0], local_tools.COMPOSE + ["stop", *local_tools.SERVICES])
        self.assertEqual(commands[-1], local_tools.COMPOSE + ["up", "-d", *selected])

    def test_default_restore_still_starts_all_services(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "backup.zip"
            archive.touch()
            commands = self.restore(archive)
        self.assertEqual(commands[-1], local_tools.COMPOSE + ["up", "-d"])

    def test_failed_restore_does_not_restart_writers(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "backup.zip"
            archive.touch()
            commands = self.restore(archive, ["--start-services", "app"], failure=True)
        self.assertEqual(commands[0], local_tools.COMPOSE + ["stop", *local_tools.SERVICES])
        self.assertFalse(any(command[len(local_tools.COMPOSE):len(local_tools.COMPOSE) + 1] == ["up"]
                             for command in commands))

    def test_invalid_service_fails_before_docker_operations(self):
        with patch("sys.argv", ["local_tools.py", "restore", "backup.zip", "--start-services", "other"]), \
                patch.object(local_tools, "run") as commands, patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                local_tools.main()
        self.assertEqual(error.exception.code, 2)
        commands.assert_not_called()

    def test_service_option_is_rejected_for_backup(self):
        with patch("sys.argv", ["local_tools.py", "backup", "--start-services", "app"]), \
                patch.object(local_tools, "run") as commands, patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                local_tools.main()
        self.assertEqual(error.exception.code, 2)
        commands.assert_not_called()


if __name__ == "__main__":
    unittest.main()
