import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "cloud_app" / "static" / "index.html"
PROFILE = ROOT / "cloud_app" / "static" / "profile.js"


class _Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class DashboardFrontendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.document = _Document()
        cls.document.feed(cls.html)

    def _elements_with(self, attribute):
        return [(tag, attrs) for tag, attrs in self.document.elements if attribute in attrs]

    def test_landing_auth_and_dashboard_routes_have_single_owners(self):
        actions = self._elements_with("id")
        by_id = {attrs["id"]: (tag, attrs) for tag, attrs in actions}
        self.assertEqual(by_id["landingAction"][0], "button")
        self.assertIn("about", by_id)
        self.assertNotIn("data-show-auth", self.html)
        self.assertEqual(len(self._elements_with("data-open-dashboard")), 2)
        self.assertGreaterEqual(len(self._elements_with("data-show-landing")), 2)

    def test_authenticated_profile_contract_is_present(self):
        self.assertEqual(len(self._elements_with("data-authenticated-only")), 2)
        self.assertEqual(len(self._elements_with("data-open-profile")), 2)
        self.assertEqual(len(self._elements_with("data-profile-menu-action")), 3)
        ids = {attrs["id"] for _, attrs in self._elements_with("id")}
        self.assertIn("profileMenu", ids)
        self.assertIn("profileDialog", ids)
        self.assertIn("profileSettingsForm", ids)
        self.assertIn("aiConnectionSettings", ids)
        self.assertIn("aiConnectionForm", ids)
        self.assertIn("aiProvider", ids)
        self.assertIn("aiModel", ids)
        self.assertIn("aiApiKey", ids)
        self.assertIn("aiDisconnectBtn", ids)
        self.assertIn("aiConnectBtn", ids)
        self.assertNotIn("aiStatus", ids)

    def test_strategy_builder_uses_connection_action(self):
        self.assertIn("전략 코드 생성", self.html)
        self.assertNotIn("AI 연결 대기", self.html)
        self.assertNotIn("동아리 로컬 AI", self.html)
        self.assertNotIn("AI 웹 구독 계정", self.html)
        self.assertNotIn("대시보드 시작 화면", self.html)
        self.assertIn("requires_api_key", PROFILE.read_text(encoding="utf-8"))
        self.assertIn('data-profile-menu-action="settings"', self.html)
        self.assertIn('data-profile-menu-action="logout"', self.html)

    def test_profile_controller_loads_before_app_controller(self):
        scripts = [attrs.get("src") for tag, attrs in self.document.elements if tag == "script" and attrs.get("src")]
        self.assertEqual([source.split("?", 1)[0] for source in scripts[-2:]], ["/static/profile.js", "/static/app.js"])
        self.assertTrue(all("?v=" in source for source in scripts[-2:]))


if __name__ == "__main__":
    unittest.main()
