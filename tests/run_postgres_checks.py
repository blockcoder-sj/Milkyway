"""Run real PostgreSQL checks on a private, disposable Docker network.

No published ports, host database credentials, persistent volumes or existing
containers are used. The image argument must be an already-built test image.
"""

import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import time
import uuid


POSTGRES_IMAGE = "postgres:16-alpine@sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685"
TEST_PASSWORD = "Synthetic-Postgres-Test-Only-0123456789"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    prefix = "milkyway-check-" + uuid.uuid4().hex[:12]
    network, database, runner = prefix, prefix + "-pg", prefix + "-runner"
    certificates = tempfile.TemporaryDirectory(prefix="milkyway-check-tls-")
    tls = Path(certificates.name)

    def docker(*command, **kwargs):
        return subprocess.run(["docker", *command], check=True, **kwargs)

    try:
        spec = importlib.util.spec_from_file_location("postgres_tls", root / "deploy/create-postgres-tls.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tls = tls / "generated"
        module.create(tls, database)
        try:
            module.create(tls, database)
        except FileExistsError:
            pass
        else:
            raise AssertionError("TLS generator must not overwrite existing identity files")
        docker("network", "create", "--internal", network, capture_output=True)
        docker(
            "run", "--detach", "--name", database, "--network", network,
            "--tmpfs", "/var/lib/postgresql/data:rw,nosuid,nodev,size=512m",
            "--tmpfs", "/run/secrets:rw,nosuid,nodev,size=1m",
            "--mount", f"type=bind,source={tls / 'server.key'},target=/tls/server.key,readonly",
            "--mount", f"type=bind,source={tls / 'server.crt'},target=/tls/server.crt,readonly",
            "--mount", f"type=bind,source={root / 'deploy/postgres/pg_hba.conf'},target=/etc/postgresql/test_hba.conf,readonly",
            "--mount", f"type=bind,source={root / 'deploy/postgres/init-runtime-roles.sh'},target=/init-source.sh,readonly",
            *[argument for role in ("app", "paper", "backtest", "scheduler", "backup", "authority")
              for argument in ("--env", role.upper() + "_DB_PASSWORD=Synthetic-Role-Only-0123456789-" + role)],
            "--env", "POSTGRES_USER=postgres", "--env", "POSTGRES_DB=postgres",
            "--env", "POSTGRES_PASSWORD=" + TEST_PASSWORD, "--entrypoint", "sh", POSTGRES_IMAGE,
            "-eu", "-c", "cp /init-source.sh /docker-entrypoint-initdb.d/10-runtime-roles.sh\nchmod 0644 /docker-entrypoint-initdb.d/10-runtime-roles.sh\ncp /tls/server.key /run/secrets/server.key\ncp /tls/server.crt /run/secrets/server.crt\nchown postgres:postgres /run/secrets/server.key\nchmod 600 /run/secrets/server.key\nexec /usr/local/bin/docker-entrypoint.sh postgres -c ssl=on -c ssl_min_protocol_version=TLSv1.3 -c ssl_cert_file=/run/secrets/server.crt -c ssl_key_file=/run/secrets/server.key -c hba_file=/etc/postgresql/test_hba.conf",
            capture_output=True,
        )
        deadline = time.monotonic() + 60
        while True:
            ready = subprocess.run(
                ["docker", "exec", database, "pg_isready", "-h", "127.0.0.1", "-U", "postgres"],
                capture_output=True,
            )
            if ready.returncode == 0:
                break
            running = docker("inspect", "--format", "{{.State.Running}}", database, capture_output=True, text=True)
            if running.stdout.strip() != "true":
                docker("logs", database)
                raise RuntimeError("Disposable PostgreSQL initialization failed")
            if time.monotonic() >= deadline:
                docker("logs", database)
                raise RuntimeError("Disposable PostgreSQL did not become ready")
            time.sleep(0.25)
        # Re-running role provisioning is required for existing-volume
        # upgrades. Exercise it without recreating the database or volume.
        docker("exec", database, "sh", "/docker-entrypoint-initdb.d/10-runtime-roles.sh", capture_output=True)
        docker(
            "run", "--rm", "--name", runner, "--network", network, "--read-only",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m",
            "--tmpfs", "/runtime:rw,nosuid,nodev,uid=10001,gid=10001,size=64m",
            "--tmpfs", "/backups:rw,nosuid,nodev,uid=10001,gid=10001,size=64m",
            "--tmpfs", "/run/secrets:rw,nosuid,nodev,uid=10001,gid=10001,size=1m",
            "--mount", f"type=bind,source={tls / 'ca.crt'},target=/run/secrets/postgres_tls_ca,readonly",
            "--mount", "type=bind,source={},target=/app,readonly".format(root),
            "--mount", "type=bind,source={},target=/backup,readonly".format(root / "deploy"),
            "--workdir", "/app", "--env", "APP_ENV=development",
            "--env", "DATABASE_URL=sqlite:////runtime/club.sqlite3",
            "--env", "MILKYWAY_DISPOSABLE_POSTGRES_TEST=1",
            "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PGHOST=" + database,
            "--env", "PGUSER=postgres", "--env", "PGPASSWORD=" + TEST_PASSWORD,
            "--env", "PGDATABASE=postgres", "--env", "RESTORE_CONFIRM=quantclub",
            "--env", "PGSSLMODE=verify-full", "--env", "PGSSLROOTCERT=/run/secrets/postgres_tls_ca",
            args.image, "python", "-m", "tests.postgres_checks", timeout=300,
        )
    finally:
        for name in (runner, database):
            subprocess.run(["docker", "rm", "--force", name], capture_output=True)
        subprocess.run(["docker", "network", "rm", network], capture_output=True)
        certificates.cleanup()


if __name__ == "__main__":
    main()
