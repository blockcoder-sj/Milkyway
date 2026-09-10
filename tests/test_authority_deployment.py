import secrets
import unittest
from dataclasses import replace
from urllib.parse import quote
from unittest.mock import patch

from cloud_app.config import get_settings, valid_database_tls_query
from cloud_app.deployment_secrets import DATABASE_PASSWORDS, DATABASE_URLS, OTHER_SECRET_NAMES, deployment_secret_errors
from cloud_app.credential_broker_client import CredentialBrokerError, broker_preflight


class AuthorityDeploymentTests(unittest.TestCase):
    def test_postgres_ca_and_hostname_verification_cannot_be_overridden_in_dsn(self):
        good = "sslmode=verify-full&sslrootcert=/run/secrets/postgres_tls_ca"
        self.assertTrue(valid_database_tls_query(good))
        for query in ("", good + "&sslmode=disable", good + "&options=-c%20row_security=off", good.replace("verify-full", "require"), good.replace("postgres_tls_ca", "untrusted_ca")):
            self.assertFalse(valid_database_tls_query(query))
        env = {name: secrets.token_urlsafe(32) for name in DATABASE_PASSWORDS + OTHER_SECRET_NAMES}
        env.update(APP_VM_PRIVATE_IP="10.2.0.5", POSTGRES_USER="migration")
        for name, (user_env, password_env) in DATABASE_URLS.items():
            user = env[user_env] if user_env else "milkyway_" + password_env.split("_", 1)[0].lower()
            env[name] = "postgresql+psycopg://" + user + ":" + quote(env[password_env], safe="") + "@postgres/quantclub?" + good
        self.assertEqual(deployment_secret_errors(env), [])
        for ip in ("0.0.0.0", "127.0.0.1", "8.8.8.8", "::", ""):
            self.assertTrue(deployment_secret_errors(env | {"APP_VM_PRIVATE_IP": ip}))
        self.assertTrue(deployment_secret_errors(env | {"AUTHORITY_DATABASE_URL": env["APP_DATABASE_URL"]}))
        self.assertTrue(deployment_secret_errors(env | {"CREDENTIAL_BROKER_BACKTEST_TOKEN": env["CREDENTIAL_BROKER_APP_TOKEN"]}))

    def test_broker_browser_origin_and_runtime_database_scheme_fail_closed(self):
        settings = replace(get_settings(), app_env="production", authority_enabled=True)
        for origin in ("http://broker.test", "https://broker.test/credentials", "https://user@broker.test", "https://broker.test?query=1"):
            self.assertTrue(any("PUBLIC_BASE_URL" in error for error in replace(settings, public_base_url=origin).startup_errors("broker")))
        for url in ("sqlite:///runtime/db", "mysql://user:password@db/name", "https://user:password@db/name"):
            self.assertTrue(any("PostgreSQL URL" in error for error in replace(settings, database_url=url).startup_errors("app")))

    def test_backtest_preflight_uses_its_own_role_and_requires_authority(self):
        settings = replace(get_settings(), authority_enabled=True)
        with patch("cloud_app.credential_broker_client._request", return_value={"status": "ok", "authority_enabled": True}) as request:
            broker_preflight(settings, "backtest")
            request.assert_called_once_with(settings, "backtest", "/v1/backtest-preflight", {})
        with patch("cloud_app.credential_broker_client._request", return_value={"status": "ok"}):
            with self.assertRaises(CredentialBrokerError):
                broker_preflight(settings, "backtest")
