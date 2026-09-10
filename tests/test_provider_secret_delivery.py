"""Local contract tests; none constitute deployed OCI IAM/Vault evidence."""

import base64
from dataclasses import replace
import os
import multiprocessing
import time
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("APP_ENV", "development")

from cloud_app import config, credential_broker, provider_secrets
from fastapi import HTTPException


_real_run_retrieval = provider_secrets._run_retrieval


def stalled_identity_or_refresh(sender, settings, purpose):
    time.sleep(30)


def bounded_test_release(sender, settings, purpose):
    sender.send_bytes(b"sk-test-release-abcdefghijklmnopqrstuvwxyz0123456789")
    sender.close()


def oversized_test_release(sender, settings, purpose):
    sender.send_bytes(b"x" * 5000)
    sender.close()


class ProviderSecretDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.settings = replace(
            config.get_settings(), app_env="production", service_role="broker",
            shared_ai_api_key="",
            oci_shared_ai_secret_id="ocid1.vaultsecret.oc1.ap-seoul-1.aaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        self.key = "sk-provider-only-abcdefghijklmnopqrstuvwxyz0123456789"
        runner = patch.object(provider_secrets, "_run_retrieval", side_effect=lambda settings, purpose, timeout: provider_secrets._fetch_oci_secret(settings, purpose))
        runner.start()
        self.addCleanup(runner.stop)

    def test_stalled_identity_process_is_killed_and_capacity_can_be_reused(self):
        before = {child.pid for child in multiprocessing.active_children()}
        started = time.monotonic()
        with patch.object(provider_secrets, "_release_worker", stalled_identity_or_refresh):
            with self.assertRaisesRegex(provider_secrets.ProviderSecretUnavailable, "deadline"):
                _real_run_retrieval(self.settings, "shared_ai", 0.4)
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertEqual({child.pid for child in multiprocessing.active_children()}, before)
        with patch.object(provider_secrets, "_release_worker", bounded_test_release):
            result = _real_run_retrieval(self.settings, "shared_ai", 3)
        self.assertTrue(result.startswith("sk-test-release-"))
        self.assertEqual({child.pid for child in multiprocessing.active_children()}, before)

    def test_release_pipe_rejects_an_oversized_message_and_reaps_the_child(self):
        before = {child.pid for child in multiprocessing.active_children()}
        with patch.object(provider_secrets, "_release_worker", oversized_test_release):
            with self.assertRaises(provider_secrets.ProviderSecretUnavailable):
                _real_run_retrieval(self.settings, "shared_ai", 3)
        self.assertEqual({child.pid for child in multiprocessing.active_children()}, before)

    @staticmethod
    def response(encoded, content_type="BASE64"):
        return SimpleNamespace(data=SimpleNamespace(secret_bundle_content=SimpleNamespace(
            content=encoded, content_type=content_type,
        )))

    def test_current_secret_is_resolved_only_in_the_broker(self):
        client = Mock()
        client.get_secret_bundle.return_value = self.response(base64.b64encode(self.key.encode()).decode())
        with patch.object(provider_secrets, "_client", return_value=client):
            self.assertEqual(provider_secrets.provider_secret(self.settings, "shared_ai"), self.key)
        self.assertEqual(client.get_secret_bundle.call_args.args, (self.settings.oci_shared_ai_secret_id,))
        self.assertEqual(client.get_secret_bundle.call_args.kwargs["stage"], "CURRENT")
        for role in ("app", "paper", "backtest", "scheduler", ""):
            with self.subTest(role=role), patch.object(provider_secrets, "_client") as factory:
                with self.assertRaises(provider_secrets.ProviderSecretUnavailable):
                    provider_secrets.provider_secret(replace(self.settings, service_role=role), "shared_ai")
                factory.assert_not_called()

    def test_secret_rotation_and_denial_never_reuse_a_previous_plaintext_key(self):
        client = Mock()
        rotated = self.key + "rotated"
        client.get_secret_bundle.side_effect = [
            self.response(base64.b64encode(self.key.encode()).decode()),
            self.response(base64.b64encode(rotated.encode()).decode()),
            RuntimeError("SDK body containing " + self.key),
        ]
        with patch.object(provider_secrets, "_client", return_value=client):
            self.assertEqual(provider_secrets.provider_secret(self.settings, "shared_ai"), self.key)
            self.assertEqual(provider_secrets.provider_secret(self.settings, "shared_ai"), rotated)
            with self.assertRaises(provider_secrets.ProviderSecretUnavailable) as raised:
                provider_secrets.provider_secret(self.settings, "shared_ai")
        self.assertNotIn(self.key, str(raised.exception))
        self.assertNotIn(self.settings.oci_shared_ai_secret_id, str(raised.exception))

    def test_invalid_bundle_encodings_and_keys_are_rejected(self):
        bad_values = [b"\xff" * 40, b"key\n" * 10, b"a" * 40, b"x" * 4097, b"replace-with-secret-value-here"]
        contents = [self.response("!invalid-base64!"), self.response("x" * 5500), self.response("AA==", "UNKNOWN_ENUM_VALUE")]
        contents += [self.response(base64.b64encode(value).decode()) for value in bad_values]
        for response in contents:
            with self.subTest(response=response), patch.object(provider_secrets, "_client") as factory:
                factory.return_value.get_secret_bundle.return_value = response
                with self.assertRaises(provider_secrets.ProviderSecretUnavailable):
                    provider_secrets.provider_secret(self.settings, "shared_ai")

    def test_production_rejects_plaintext_sources_before_opening_files(self):
        for suffix in ("", "_FILE"):
            with patch.dict(os.environ, {"APP_ENV": "production", "SHARED_AI_API_KEY" + suffix: "must-not-be-read"}, clear=True), patch.object(config, "_secret") as read:
                with self.assertRaises(RuntimeError):
                    config._configured_provider_secret("SHARED_AI_API_KEY")
                read.assert_not_called()

    def test_config_loading_does_not_contact_vault(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "OCI_SHARED_AI_SECRET_ID": self.settings.oci_shared_ai_secret_id}, clear=True), patch.object(provider_secrets, "_client") as client:
            config.get_settings.cache_clear()
            try:
                loaded = config.get_settings()
                self.assertEqual(loaded.shared_ai_api_key, "")
            finally:
                config.get_settings.cache_clear()
            client.assert_not_called()

    def test_paper_preflight_cannot_bypass_exhausted_quote_capacity(self):
        slots = threading.BoundedSemaphore(1)
        slots.acquire()
        with patch.object(credential_broker, "_quote_slots", slots), patch.object(credential_broker, "provider_secret") as release, patch.object(credential_broker, "_shared_kis_quotes") as quotes:
            with self.assertRaises(HTTPException) as raised:
                credential_broker.paper_preflight("paper")
        self.assertEqual(raised.exception.status_code, 429)
        release.assert_not_called()
        quotes.assert_not_called()
        self.assertFalse(slots.acquire(blocking=False))
        slots.release()

    def test_paper_preflight_uses_one_deadline_and_releases_capacity_on_denial(self):
        settings = replace(self.settings, credential_backend="shared", quote_provider="kis", quote_deadline_seconds=20)
        slots = threading.BoundedSemaphore(1)
        with patch.object(credential_broker, "settings", settings), patch.object(credential_broker, "_quote_slots", slots), patch.object(credential_broker, "_rate_limit"), patch.object(credential_broker, "validate_credential_backend"), patch.object(credential_broker.time, "monotonic", side_effect=[100, 101, 109]), patch.object(credential_broker, "provider_secret", return_value=self.key) as release, patch.object(credential_broker, "_shared_kis_quotes", return_value=[]) as quotes:
            credential_broker.paper_preflight("paper")
        self.assertEqual([call.kwargs["timeout_seconds"] for call in release.call_args_list], [19, 11])
        self.assertEqual(quotes.call_args.kwargs["deadline"], 120)
        self.assertTrue(slots.acquire(blocking=False))
        slots.release()
        with patch.object(credential_broker, "settings", settings), patch.object(credential_broker, "_quote_slots", slots), patch.object(credential_broker, "_rate_limit"), patch.object(credential_broker, "validate_credential_backend"), patch.object(credential_broker, "provider_secret", side_effect=provider_secrets.ProviderSecretUnavailable("denied")), patch.object(credential_broker, "_shared_kis_quotes") as quotes:
            with self.assertRaises(HTTPException) as raised:
                credential_broker.paper_preflight("paper")
        self.assertEqual(raised.exception.status_code, 503)
        quotes.assert_not_called()
        self.assertTrue(slots.acquire(blocking=False))
        slots.release()
