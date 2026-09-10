"""Execute cloud-init failure paths using harmless temporary command stubs."""

from pathlib import Path
import os
import shlex
import subprocess
import tempfile
import unittest


CLOUD_INIT = Path(__file__).resolve().parents[1] / "deploy/oci/cloud-init.yaml"


class HostBootstrapTests(unittest.TestCase):
    def test_unsupported_os_stops_before_any_package_or_filesystem_mutation(self):
        source = CLOUD_INIT.read_text()
        # write_files executes before runcmd; it must not bypass the OS guard.
        self.assertNotIn("  - path: /etc/apt/", source)
        block = source.split("  - path: /usr/local/sbin/milkyway-bootstrap-host\n", 1)[1].split("    content: |\n", 1)[1]
        lines = []
        for line in block.splitlines():
            if not line.startswith("      "):
                break
            lines.append(line[6:])
        script = "\n".join(lines) + "\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release, keyring, marker = root / "os-release", root / "keyring", root / "mutation"
            keyring.touch()
            for command, body in {"dpkg": "printf 'arm64\\n'", "install": "touch " + shlex.quote(str(marker)) + "; exit 77"}.items():
                path = root / command
                path.write_text("#!/bin/sh\n" + body + "\n")
                path.chmod(0o700)
            script = script.replace(". /etc/os-release", ". " + shlex.quote(str(release))).replace("/usr/share/keyrings/ubuntu-archive-keyring.gpg", shlex.quote(str(keyring)))
            env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
            for identifier, version in (("debian", "12"), ("ubuntu", "22.04")):
                release.write_text(f"ID={identifier}\nVERSION_ID={version}\n")
                result = subprocess.run(["sh", "-c", script], env=env, capture_output=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertFalse(marker.exists())
            release.write_text("ID=ubuntu\nVERSION_ID=24.04\n")
            result = subprocess.run(["sh", "-c", script], env=env, capture_output=True)
            self.assertEqual(result.returncode, 77, result.stderr)
            self.assertTrue(marker.exists())

    def test_cloud_init_propagates_bootstrap_failure_before_service_start(self):
        commands = [line[4:] for line in CLOUD_INIT.read_text().split("runcmd:\n", 1)[1].splitlines() if line.startswith("  - ")]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker, bootstrap = root / "later-command", root / "bootstrap"
            for command in ("usermod", "install", "systemctl", "sysctl"):
                path = root / command
                path.write_text("#!/bin/sh\ntouch " + shlex.quote(str(marker)) + "\n")
                path.chmod(0o700)
            bootstrap.write_text("#!/bin/sh\nexit 73\n")
            bootstrap.chmod(0o700)
            script = "\n".join(commands).replace("/usr/local/sbin/milkyway-bootstrap-host", shlex.quote(str(bootstrap)))
            env = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
            result = subprocess.run(["sh", "-c", script], env=env, capture_output=True)
            self.assertEqual(result.returncode, 73, result.stderr)
            self.assertFalse(marker.exists())
            bootstrap.write_text("#!/bin/sh\nexit 0\n")
            result = subprocess.run(["sh", "-c", script], env=env, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(marker.exists())
