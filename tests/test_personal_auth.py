"""Local auto-entry keeps ordinary session/CSRF and owner isolation intact."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from cloud_app import main
from cloud_app.database import Base, BrowserSession, Strategy, User
from cloud_app.security import verify_password


class PersonalAuthTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_engine("sqlite:///" + str(Path(self.directory.name) / "db"))
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine, expire_on_commit=False, autoflush=False)
        self.settings = replace(
            main.settings, personal_local_mode=True, app_env="development",
            max_users=1, authority_enabled=False, credential_backend="local",
            public_base_url="http://localhost:8080",
        )
        self.settings_patch = patch.object(main, "settings", self.settings)
        self.settings_patch.start()
        self.overrides = main.app.dependency_overrides.copy()

        def database():
            with self.factory() as session:
                yield session

        main.app.dependency_overrides[main.get_db] = database
        # No lifespan: only the isolated database above is used.
        self.client = TestClient(main.app, base_url="http://localhost:8080")
        self.headers = {"Origin": "http://localhost:8080", "X-Milkyway-Local": "1",
                        "Sec-Fetch-Site": "same-origin"}

    def tearDown(self):
        self.client.close()
        main.app.dependency_overrides.clear()
        main.app.dependency_overrides.update(self.overrides)
        self.settings_patch.stop()
        self.engine.dispose()
        self.directory.cleanup()

    def enter(self, client=None):
        return (client or self.client).post("/api/auth/local", headers=self.headers, json={})

    def test_fresh_install_creates_one_owner_and_reuses_session(self):
        self.assertTrue(self.client.get("/api/config").json()["local_auto_login"])
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        response = self.enter()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        self.assertIn("SameSite=strict", response.headers["set-cookie"])
        self.assertEqual(self.client.get("/api/auth/me").json(), response.json())
        self.assertEqual(self.enter().json(), response.json())
        with self.factory() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(User)), 1)
            self.assertEqual(session.scalar(select(func.count()).select_from(BrowserSession)), 1)
            self.assertFalse(verify_password("local-club", session.scalar(select(User)).password_hash))

    def test_existing_owner_password_and_strategy_are_preserved(self):
        with self.factory() as session:
            owner = User(email="existing@example.test", display_name="Existing", password_hash="existing-hash")
            session.add(owner)
            session.flush()
            session.add(Strategy(user_id=owner.id, name="Saved", spec_json="{}", original_prompt="saved"))
            session.commit()
            owner_id = owner.id
        self.assertEqual(self.enter().json()["id"], owner_id)
        with self.factory() as session:
            self.assertEqual(session.get(User, owner_id).password_hash, "existing-hash")
            self.assertEqual(session.scalar(select(Strategy)).user_id, owner_id)

    def test_cross_origin_missing_headers_and_non_loopback_are_denied(self):
        cases = [
            {}, {"Origin": "http://localhost:8080"},
            {**self.headers, "Origin": "https://attacker.example"},
            {**self.headers, "Origin": "null"},
            {**self.headers, "Origin": "http://localhost:9999"},
            {**self.headers, "Sec-Fetch-Site": "same-site"},
            {**self.headers, "Host": "testserver", "Origin": "http://testserver"},
        ]
        for headers in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.client.post("/api/auth/local", headers=headers).status_code, 403)
        preflight = self.client.options("/api/auth/local", headers={
            "Origin": "https://attacker.example", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-milkyway-local"})
        self.assertNotIn("access-control-allow-origin", preflight.headers)
        with self.factory() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(User)), 0)

    def test_cloud_production_and_ambiguous_config_cannot_auto_login(self):
        for changes in ({"personal_local_mode": False}, {"app_env": "production"},
                        {"max_users": 2}, {"authority_enabled": True},
                        {"credential_backend": "broker"}, {"public_base_url": "https://example.com"}):
            with self.subTest(changes=changes), patch.object(main, "settings", replace(self.settings, **changes)):
                self.assertFalse(self.client.get("/api/config").json()["local_auto_login"])
                self.assertEqual(self.enter().status_code, 404)

    def test_csrf_still_required_and_revoked_session_is_recreated(self):
        me = self.enter().json()
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 403)
        old_cookie = self.client.cookies.get("session")
        self.assertEqual(self.client.post("/api/auth/logout", headers={"X-CSRF-Token": me["csrf"]}).status_code, 204)
        self.client.cookies.set("session", old_cookie)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        renewed = self.enter().json()
        self.assertEqual(renewed["id"], me["id"])
        self.assertNotEqual(renewed["csrf"], me["csrf"])

    def test_multiple_or_inactive_users_are_never_silently_selected(self):
        with self.factory() as session:
            session.add(User(email="one@example.test", display_name="One", password_hash="unused", active=False))
            session.commit()
        self.assertEqual(self.enter().status_code, 403)
        with self.factory() as session:
            session.add(User(email="two@example.test", display_name="Two", password_hash="unused"))
            session.commit()
        self.assertEqual(self.enter().status_code, 409)

    def test_simultaneous_tabs_create_one_owner_and_bounded_sessions(self):
        # Do not run application lifespan in the disposable test clients.
        def enter_without_lifespan(_):
            client = TestClient(main.app, base_url="http://localhost:8080")
            try:
                return self.enter(client).json()["id"]
            finally:
                client.close()

        with ThreadPoolExecutor(max_workers=6) as pool:
            ids = list(pool.map(enter_without_lifespan, range(12)))
        self.assertEqual(len(set(ids)), 1)
        with self.factory() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(User)), 1)
            self.assertEqual(session.scalar(select(func.count()).select_from(BrowserSession)), 10)


if __name__ == "__main__":
    unittest.main()
