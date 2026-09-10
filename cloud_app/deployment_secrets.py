"""Fail-closed, non-logging validation for app-VM deployment secrets."""

from __future__ import annotations

import hmac
import ipaddress
import os
from urllib.parse import unquote, urlsplit

from .config import _weak_secret, valid_database_tls_query


DATABASE_PASSWORDS = (
    "POSTGRES_PASSWORD",
    "APP_DB_PASSWORD",
    "PAPER_DB_PASSWORD",
    "BACKTEST_DB_PASSWORD",
    "SCHEDULER_DB_PASSWORD",
    "BACKUP_DB_PASSWORD",
    "AUTHORITY_DB_PASSWORD",
)
DATABASE_URLS = {
    "MIGRATION_DATABASE_URL": ("POSTGRES_USER", "POSTGRES_PASSWORD"),
    "APP_DATABASE_URL": (None, "APP_DB_PASSWORD"),
    "PAPER_DATABASE_URL": (None, "PAPER_DB_PASSWORD"),
    "BACKTEST_DATABASE_URL": (None, "BACKTEST_DB_PASSWORD"),
    "SCHEDULER_DATABASE_URL": (None, "SCHEDULER_DB_PASSWORD"),
    "AUTHORITY_DATABASE_URL": (None, "AUTHORITY_DB_PASSWORD"),
}
OTHER_SECRET_NAMES = (
    "SESSION_SECRET",
    "CREDENTIAL_BROKER_APP_TOKEN",
    "CREDENTIAL_BROKER_PAPER_TOKEN",
    "CREDENTIAL_BROKER_BACKTEST_TOKEN",
)


def deployment_secret_errors(environment: dict[str, str] | None = None) -> list[str]:
    values = environment if environment is not None else dict(os.environ)
    errors: list[str] = []
    collected: list[tuple[str, str]] = []
    try:
        address = ipaddress.ip_address(values.get("APP_VM_PRIVATE_IP", ""))
        if not any(address in ipaddress.ip_network(network) for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
            raise ValueError
    except ValueError:
        errors.append("APP_VM_PRIVATE_IP must be an RFC1918 private interface address")

    for name in DATABASE_PASSWORDS + OTHER_SECRET_NAMES:
        value = values.get(name, "")
        if _weak_secret(value, 32):
            errors.append("{} must be a non-placeholder high-entropy secret".format(name))
        elif value:
            collected.append((name, value))

    for url_name, (user_name, password_name) in DATABASE_URLS.items():
        raw = values.get(url_name, "")
        try:
            parsed = urlsplit(raw)
        except ValueError:
            parsed = None
        if (
            parsed is None
            or parsed.scheme not in {"postgresql", "postgresql+psycopg"}
            or not parsed.hostname
            or not parsed.username
            or parsed.password is None
            or not valid_database_tls_query(parsed.query)
            or parsed.fragment
        ):
            errors.append("{} must be a credentialed PostgreSQL URL".format(url_name))
            continue
        expected_password = values.get(password_name, "")
        if not hmac.compare_digest(unquote(parsed.password), expected_password):
            errors.append("{} password does not match {}".format(url_name, password_name))
        if user_name and not hmac.compare_digest(
            unquote(parsed.username), values.get(user_name, "")
        ):
            errors.append("{} user does not match {}".format(url_name, user_name))

    seen: dict[str, str] = {}
    for name, value in collected:
        previous = seen.get(value)
        if previous is not None:
            errors.append("{} and {} must be independent".format(previous, name))
        else:
            seen[value] = name
    return errors


def main() -> int:
    errors = deployment_secret_errors()
    if errors:
        for error in errors:
            print("deployment secret validation failed: " + error)
        return 1
    print("deployment secret validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
