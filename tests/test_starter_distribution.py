"""The beginner download cannot open or collect sector/company research."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud_app import main, market_details
from cloud_app.database import Base
from cloud_app.research_models import ResearchBase


class StarterDistributionTests(unittest.TestCase):
    def test_authenticated_summary_and_index_work_while_research_routes_are_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine("sqlite:///" + directory + "/db")
            Base.metadata.create_all(engine)
            ResearchBase.metadata.create_all(engine)
            factory = sessionmaker(bind=engine, expire_on_commit=False)
            settings = replace(main.settings, personal_local_mode=True, app_env="development",
                               authority_enabled=False, credential_backend="local", max_users=1,
                               public_base_url="http://localhost:8080", dataset_dir=Path(directory)/"data")
            def db():
                with factory() as session:
                    yield session
            prior = main.app.dependency_overrides.copy()
            main.app.dependency_overrides[main.get_db] = db
            try:
                with patch.object(main, "settings", settings), patch.object(market_details._provider, "run") as external:
                    client = TestClient(main.app, base_url="http://localhost:8080")
                    try:
                        login = client.post("/api/auth/local", headers={"X-Milkyway-Local":"1", "Origin":"http://localhost:8080"})
                        self.assertEqual(login.status_code, 200)
                        self.assertFalse(client.get("/api/config").json()["sector_details_enabled"])
                        overview = client.get("/api/market-overview")
                        self.assertEqual(overview.status_code, 200)
                        sectors = [row for row in overview.json()["items"] if row["group"] == "sectors"]
                        self.assertEqual(len(sectors), 19)
                        for identity in ("us_10", "us_45", "kr_13"):
                            self.assertEqual(client.get("/api/market-details/"+identity).status_code, 404)
                        for route in ("/api/company-details/us_10/XOM", "/api/energy-constellation",
                                      "/api/energy-constellation/search?q=oil", "/api/company-entities/c_"+"0"*32):
                            self.assertEqual(client.get(route).status_code, 404)
                        self.assertEqual(client.get("/api/market-details/sp500").status_code, 200)
                        self.assertEqual(client.get("/api/market-details/usdkrw").status_code, 200)
                        external.assert_not_called()
                    finally:
                        client.close()
            finally:
                main.app.dependency_overrides.clear()
                main.app.dependency_overrides.update(prior)
                engine.dispose()

    def test_sector_refresh_is_rejected_before_provider_or_cache_access(self):
        settings = replace(main.settings, personal_local_mode=True, app_env="development")
        with patch.object(market_details._provider, "run") as external:
            for identity in ("us_10", "kr_13"):
                with self.assertRaises(ValueError):
                    market_details.refresh_detail(settings, identity)
            external.assert_not_called()
