"""Regenerate Linux/Python 3.11 wheel locks using the pinned lock tooling.

Run in an isolated Python 3.11 Linux environment after installing
requirements-lock.lock with --require-hashes --only-binary=:all:.
Then build the image, run tests, and audit before accepting the new locks.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request


def main() -> None:
    if sys.version_info[:2] != (3, 11) or sys.platform != "linux":
        raise SystemExit("Lock generation requires Python 3.11 on Linux")
    root = Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',choices=('requirements','requirements-audit','requirements-lock','requirements-semantic'))
    args=parser.parse_args()
    for name in ((args.only,) if args.only else ("requirements", "requirements-audit", "requirements-lock")):
        with tempfile.TemporaryDirectory(prefix="milkyway-lock-") as directory:
            resolved = Path(directory, "resolved.txt")
            subprocess.run([
                sys.executable, "-m", "piptools", "compile", "--allow-unsafe",
                "--strip-extras", "--resolver=backtracking", "--no-emit-index-url",
                "--no-emit-trusted-host", "--pip-args=--only-binary=:all:",
                "--output-file", str(resolved), str(root / (name + ".in")),
            ], check=True)
            pins = []
            for line in resolved.read_text().splitlines():
                if not line or line[0].isspace() or line.startswith("#") or line == "--only-binary :all:":
                    continue
                if "==" not in line or ";" in line:
                    raise RuntimeError("Unrecognized resolved requirement")
                package, version = line.split("==", 1)
                with urllib.request.urlopen(
                    "https://pypi.org/pypi/{}/{}/json".format(package, version), timeout=60
                ) as response:
                    release = json.load(response)
                hashes = sorted({
                    item["digests"]["sha256"] for item in release["urls"]
                    if item["packagetype"] == "bdist_wheel" and not item.get("yanked")
                })
                if not hashes or any(len(bytes.fromhex(value)) != hashlib.sha256().digest_size for value in hashes):
                    raise RuntimeError("Missing wheel SHA256 metadata")
                if name == "requirements" and package == "uvloop":
                    line += ' ; sys_platform != "win32"'
                pins.append(line + "".join(" \\\n    --hash=sha256:" + value for value in hashes))
            if name == "requirements":
                # Uvicorn's Windows-only console dependency is absent from the
                # Linux resolver; preserve its reviewed, wheel-only pin.
                pins.append('colorama==0.4.6 ; sys_platform == "win32" ' + chr(92)
                            + '\n    --hash=sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6')
            (root / (name + ".lock")).write_text(
                "# Python 3.11 / Linux. Transitive versions resolved with pip-tools 7.6.1.\n"
                "# Wheel SHA256 values verified against official PyPI release metadata.\n"
                + "\n".join(pins) + "\n"
            )


if __name__ == "__main__":
    main()
