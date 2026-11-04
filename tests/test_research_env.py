"""Personal AI key files, with synthetic credentials and no provider requests."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cloud_app import research_ai


class ResearchEnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.settings = SimpleNamespace(personal_local_mode=True, production=False)
        for context in (patch.object(research_ai, "ROOT", self.root),
                        patch.dict(os.environ, {"OPENAI_API_KEY": "", "OPENAI_MODEL": "",
                                                "OPENAI_REASONING_EFFORT": ""})):
            context.start()
            self.addCleanup(context.stop)
        provider = patch.object(research_ai.httpx, "Client")
        self.provider = provider.start()
        self.addCleanup(provider.stop)

    def test_example_key_is_usable_without_env_and_never_rewrites_either_file(self):
        example = self.root / ".env.example"
        original = b"OPENAI_API_KEY=synthetic-example-key-never-valid\nOPENAI_MODEL=gpt-5.4-mini\n"
        example.write_bytes(original)
        config = research_ai.local_configuration(self.settings)
        self.assertEqual(config.key, "synthetic-example-key-never-valid")
        status = research_ai.configuration_status(self.settings)
        self.assertTrue(status["configured"])
        self.assertTrue(status["approval_required"])
        self.assertFalse(status["provider_verified"])
        self.assertNotIn(config.key, str(status))
        self.assertEqual(example.read_bytes(), original)
        self.assertFalse((self.root / ".env").exists())
        self.provider.assert_not_called()

    def test_env_always_wins_over_example_including_intentionally_empty_key(self):
        (self.root / ".env.example").write_text("OPENAI_API_KEY=synthetic-example-key-never-valid\n")
        for value in ("synthetic-env-key-never-valid", ""):
            with self.subTest(empty=not value):
                (self.root / ".env").write_text("OPENAI_API_KEY=" + value + "\n")
                self.assertEqual(research_ai.local_configuration(self.settings).key, value)

    def test_process_environment_still_has_priority(self):
        (self.root / ".env.example").write_text("OPENAI_API_KEY=synthetic-example-key-never-valid\n")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-process-key-never-valid"}):
            self.assertEqual(research_ai.local_configuration(self.settings).key,
                             "synthetic-process-key-never-valid")

    def test_windows_utf8_bom_crlf_and_quoted_keys_are_accepted(self):
        (self.root / ".env.example").write_bytes(
            b'\xef\xbb\xbfOPENAI_API_KEY="synthetic-windows-key-never-valid"\r\n')
        self.assertEqual(research_ai.local_configuration(self.settings).key,
                         "synthetic-windows-key-never-valid")

    def test_invalid_or_oversized_file_fails_without_exposing_contents(self):
        for filename, content in ((".env", b"\xffsynthetic-secret-do-not-show"),
                                  (".env.example", b"x" * 16385)):
            with self.subTest(filename=filename):
                path = self.root / filename
                path.write_bytes(content)
                status = research_ai.configuration_status(self.settings)
                self.assertFalse(status["configured"])
                self.assertIn(filename, status["error"])
                self.assertNotIn("synthetic-secret", str(status))
                path.unlink()

    def test_no_files_means_no_key_and_no_provider_call(self):
        self.assertFalse(research_ai.configuration_status(self.settings)["configured"])
        self.provider.assert_not_called()

    def test_example_fallback_is_never_available_outside_personal_local_mode(self):
        (self.root / ".env.example").write_text("OPENAI_API_KEY=synthetic-example-key-never-valid\n")
        for settings in (SimpleNamespace(personal_local_mode=False, production=False),
                         SimpleNamespace(personal_local_mode=True, production=True)):
            self.assertFalse(research_ai.configuration_status(settings)["configured"])


if __name__ == "__main__":
    unittest.main()
