"""Cloud launch gate. Exits non-zero until every local prerequisite passes."""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
from pathlib import Path

from price_data_pipeline import sha256_file

from .config import get_settings
from .strategies import _load_certified_snapshots


def run(check_database: bool = False, check_docker: bool = True) -> dict:
    settings = get_settings()
    checks = {}
    errors = list(settings.startup_errors())
    checks["configuration"] = not errors
    if check_docker:
        checks["docker"] = shutil.which("docker") is not None
        if not checks["docker"]:
            errors.append("docker executable is missing")
        else:
            command = subprocess.run(
                ["docker", "compose", "version"], capture_output=True, text=True, timeout=15
            )
            checks["docker_compose"] = command.returncode == 0
            if not checks["docker_compose"]:
                errors.append("docker compose plugin is unavailable")
    manifest_path = settings.dataset_dir / "manifest.json"
    checks["dataset_manifest"] = manifest_path.exists()
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        missing = []
        corrupt = []
        for ticker, metadata in manifest.get("prices", {}).items():
            path = settings.dataset_dir / "prices" / "{}_data.pkl".format(ticker)
            if not path.exists():
                missing.append(ticker)
            elif sha256_file(path) != metadata["sha256"]:
                corrupt.append(ticker)
        checks["dataset_files"] = not missing and not corrupt
        if missing:
            errors.append("dataset has {} missing price files".format(len(missing)))
        if corrupt:
            errors.append("dataset has {} hash mismatches".format(len(corrupt)))
    validation = {}
    validation_path = settings.dataset_dir / "validation_report.json"
    checks["forward_data_gate"] = False
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        checks["forward_data_gate"] = bool(
            validation.get("forward_strategy_data_gate_ready", False)
        )
        if not checks["forward_data_gate"]:
            errors.append(
                "forward data gate has {} strategy candidate blockers".format(
                    len(validation.get("strategy_candidate_data_blockers", []))
                )
            )
    else:
        errors.append("dataset validation_report.json is missing")
    snapshots = _load_certified_snapshots(settings.snapshots_glob)
    checks["certified_snapshot"] = bool(snapshots)
    if not snapshots:
        errors.append("no certified universe snapshot found")
    elif checks["forward_data_gate"]:
        latest_snapshot_hash = snapshots[-1]["membership_sha256"]
        if validation.get("current_snapshot_membership_sha256") != latest_snapshot_hash:
            checks["forward_data_gate"] = False
            errors.append("validation report does not match the latest certified snapshot")
        manifest_last_date = max(
            (
                str(item.get("last_date", ""))
                for item in manifest.get("prices", {}).values()
            ),
            default="",
        )
        if str(validation.get("window", {}).get("end", "")) < manifest_last_date:
            checks["forward_data_gate"] = False
            errors.append("validation report predates the latest dataset session")
    if check_database:
        try:
            from .database import engine
            with engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
            checks["database_connection"] = True
        except Exception as exc:
            checks["database_connection"] = False
            errors.append("database connection failed: {}".format(exc))
    return {"ready": not errors, "checks": checks, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-database", action="store_true")
    parser.add_argument("--skip-docker", action="store_true")
    args = parser.parse_args()
    result = run(args.check_database, check_docker=not args.skip_docker)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
