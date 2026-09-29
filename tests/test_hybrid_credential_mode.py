"""Shared AI and personal brokerage are independent local application modes."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from dataclasses import replace
from unittest.mock import patch

os.environ.setdefault("APP_ENV", "development")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud_app import credential_broker, main
from cloud_app.config import get_settings, member_ai_credentials_enabled
from cloud_app.database import AiConnection, Base, Strategy, User
from tests.test_cloud_platform import sample_spec


class HybridCredentialModeTests(unittest.TestCase):
    def test_shared_ai_disables_only_member_ai_routes(self):
        env = os.environ.copy()
        env.update(APP_ENV="development", MEMBER_CREDENTIALS_ENABLED="true", SHARED_AI_ENABLED="true")
        script = '''
import json
from cloud_app.main import app
from cloud_app.credential_broker import app as broker
print(json.dumps({
    "public": [[path, [method.upper()]] for path, methods in app.openapi()["paths"].items() for method in methods],
    "broker": [r.path for r in broker.routes],
}))
'''
        completed = subprocess.run(
            [sys.executable, "-c", script], env=env,
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        routes = json.loads(completed.stdout)
        mutations = {(path, method) for path, methods in routes["public"] for method in methods}
        for method in ("PUT", "DELETE"):
            self.assertNotIn(("/api/me/ai-connection", method), mutations)
            self.assertIn(("/api/me/market-data-connection", method), mutations)
        self.assertIn("/v1/ai/shared-generate", routes["broker"])
        self.assertIn("/v1/market/prepare", routes["broker"])
        self.assertIn("/v1/market/quotes", routes["broker"])
        for operation in ("encrypt", "validate", "generate"):
            self.assertNotIn("/v1/ai/" + operation, routes["broker"])

    def test_shared_ai_never_reads_or_decrypts_a_legacy_member_ai_key(self):
        settings = replace(get_settings(), member_credentials_enabled=True, shared_ai_enabled=True, credential_backend="broker")
        self.assertFalse(member_ai_credentials_enabled(settings))
        engine = create_engine("sqlite:///:memory:")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        with sessionmaker(bind=engine, expire_on_commit=False)() as session:
            user = User(email="hybrid@example.com", display_name="Hybrid", password_hash="unused")
            session.add(user)
            session.flush()
            session.add(AiConnection(user_id=user.id, provider="openai", model="legacy", encrypted_api_key="must-not-be-used", key_hint="old"))
            session.commit()
            original_get = session.get

            def get_without_ai(model, *args, **kwargs):
                self.assertIsNot(model, AiConnection)
                return original_get(model, *args, **kwargs)

            with patch.object(main, "settings", settings), patch.object(
                session, "get", side_effect=get_without_ai
            ), patch.object(main, "broker_generate_shared_strategy", return_value=(sample_spec(), "preview")) as shared, patch.object(
                main, "broker_generate_strategy"
            ) as personal, patch.object(main, "decrypt_api_key") as decrypt:
                result = main.ai_strategy(main.PromptBody(prompt="20일 모멘텀 전략을 만들어 주세요"), user, session)
            shared.assert_called_once()
            personal.assert_not_called()
            decrypt.assert_not_called()
            self.assertEqual(session.query(Strategy).filter_by(user_id=user.id).count(), 1)
            self.assertNotIn("must-not-be-used", str(result))

    def test_hybrid_catalog_has_one_server_managed_provider(self):
        settings = replace(get_settings(), member_credentials_enabled=True, shared_ai_enabled=True, shared_ai_provider="openai")
        with patch.object(credential_broker, "settings", settings):
            result = credential_broker.ai_catalog("app")
        self.assertEqual(len(result["providers"]), 1)
        provider = result["providers"][0]
        self.assertEqual(provider["id"], "openai")
        self.assertFalse(provider["requires_api_key"])
        self.assertEqual(provider["managed_by"], "club_server")
