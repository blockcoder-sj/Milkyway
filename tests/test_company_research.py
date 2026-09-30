"""Company identity, provenance and local queue boundaries, without external calls."""
import datetime as dt
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from cloud_app import (
    company_feed as feed,
    company_service as service,
    company_worker as worker,
)
from cloud_app.company_catalog import CATALOG, editorial_for
from cloud_app.company_schemas import CompanyKnowledge, Source
from cloud_app.market_details import cache_path
from cloud_app.market_service import _write_cache

NOW = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)


def claim(value, **kwargs):
    return dict(mainsnak={"datavalue": {"value": value}}, **kwargs)


def submissions(symbol="AAPL"):
    return dict(
        cik=320193,
        tickers=[symbol],
        sicDescription="Electronic computers",
        filings={
            "recent": {
                "form": ["10-K"],
                "filingDate": ["2025-10-31"],
                "accessionNumber": ["0000320193-25-000079"],
                "primaryDocument": ["aapl-20250927.htm"],
            }
        },
    )


class CompanyFeedTests(unittest.TestCase):
    def test_ticker_can_be_an_exchange_qualifier(self):
        entity = {
            "claims": {
                "P414": [
                    claim(
                        {"id": "Q82059"},
                        qualifiers={"P249": [{"datavalue": {"value": "AAPL"}}]},
                    )
                ]
            }
        }
        self.assertTrue(feed.identity_matches(entity, "AAPL"))
        self.assertFalse(feed.identity_matches(entity, "MSFT"))
        self.assertTrue(
            feed.identity_matches({"claims": {"P249": [claim("005930")]}}, "005930.KS")
        )

    def test_ended_or_deprecated_relations_are_not_current(self):
        ended = {"P582": [{"datavalue": {"value": {"time": "+2025-01-01T00:00:00Z"}}}]}
        entity = {
            "claims": {
                "P355": [
                    claim({"id": "Q1"}, rank="deprecated"),
                    claim({"id": "Q2"}, qualifiers=ended),
                    claim({"id": "Q3"}),
                ]
            }
        }
        self.assertEqual(
            [feed.claim_value(c)["id"] for c in feed.claims(entity, "P355", NOW)],
            ["Q3"],
        )

    def test_fixed_network_hosts_reject_arbitrary_urls_before_io(self):
        with patch.object(feed, "FixedSession") as session:
            for url in (
                "http://data.sec.gov/test",
                "https://evil.test/",
                "https://key@data.sec.gov/",
                "https://data.sec.gov:444/",
            ):
                with self.assertRaises(ValueError):
                    feed.get(url)
            session.assert_not_called()

    def test_sec_requires_both_ticker_and_financial_identity(self):
        with self.assertRaises(ValueError):
            feed.parse_sec(submissions("MSFT"), {}, "AAPL", NOW)
        with self.assertRaises(ValueError):
            feed.parse_sec(submissions(), {"cik": 789019}, "AAPL", NOW)

    def test_annual_financials_exclude_quarters_future_and_invalid_values(self):
        annual = dict(
            form="10-K",
            fp="FY",
            start="2024-09-29",
            end="2025-09-27",
            filed="2025-10-31",
            val=400,
        )
        rows = [
            annual,
            {**annual, "val": True},
            {**annual, "val": float("nan")},
            {**annual, "start": "2025-07-01", "val": 50},
            {**annual, "end": "2027-01-01", "filed": "2027-02-01", "val": 900},
        ]
        facts = {
            "cik": 320193,
            "facts": {"us-gaap": {"Revenues": {"units": {"USD": rows}}}},
        }
        result = feed.parse_sec(submissions(), facts, "AAPL", NOW)
        self.assertEqual(result["financials"][0]["value"], 400)
        self.assertEqual(result["financials"][0]["period"], "2024-09-29 ~ 2025-09-27")
        self.assertIn("/320193/000032019325000079/", result["filings"][0]["url"])

    def test_sec_partial_failure_preserves_filings_with_a_notice(self):
        with patch.object(feed, "get", side_effect=[submissions(), TimeoutError()]):
            result = feed.sec_company("AAPL", "320193")
        self.assertTrue(result["filings"])
        self.assertEqual(result["financials"], [])
        self.assertTrue(result["errors"])

    def test_wise_identity_and_sales_mix_are_separate_from_market_share(self):
        html = b'<div id="comInfo">Samsung 005930</div><table id="cTB203"><tbody><tr><td>Memory</td><td>45.2</td></tr></tbody></table><table id="cTB204"><tr><td>99</td></tr></table>'
        result = feed.parse_wise(html, "005930.KS")
        self.assertIn("45.2%", result["segments"][0]["detail"])
        self.assertIn("시장점유율이 아닙니다", result["segments"][0]["detail"])
        self.assertNotIn("market_shares", result)
        with self.assertRaises(ValueError):
            feed.parse_wise(html, "000660.KS")

    def test_catalog_is_typed_source_backed_and_independent_on_each_read(self):
        for symbol in CATALOG:
            data = editorial_for(symbol)
            data.pop("cik", None)
            data.pop("entity_id", None)
            typed = CompanyKnowledge(symbol=symbol, name=symbol, **data)
            self.assertTrue(typed.products)
            self.assertTrue(typed.description_source)
        a = editorial_for("AAPL")
        a["products"].clear()
        self.assertTrue(editorial_for("AAPL")["products"])
        share = editorial_for("TSM")["market_shares"][0]
        self.assertIn("2026년 2분기", share["detail"])
        self.assertTrue(share["source"]["as_of"])

    def test_no_ai_and_partial_public_data_failure_retains_curated_notes(self):
        with patch.object(feed, "wikidata", side_effect=TimeoutError()), patch.object(
            feed, "sec_company", side_effect=TimeoutError()
        ):
            result = feed.collect_company({"symbol": "AAPL", "name": "Apple"}, {})
        self.assertTrue(result["products"])
        self.assertTrue(result["errors"])
        self.assertEqual(result["financials"], [])

    def test_source_and_model_bounds(self):
        for url in (
            "javascript:alert(1)",
            "https://user:secret@example.test/",
            "https://example.test:bad/",
        ):
            with self.assertRaises(ValueError):
                Source(label="bad", url=url)
        with self.assertRaises(ValidationError):
            CompanyKnowledge(symbol="../env", name="bad")
        with self.assertRaises(ValidationError):
            CompanyKnowledge(symbol="AAA", name="bad", products=[{}] * 61)


class CompanyQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SimpleNamespace(
            personal_local_mode=True,
            production=False,
            dataset_dir=Path(self.temp.name) / "data",
        )
        _write_cache(
            cache_path(self.settings, "us_45"),
            {
                "companies": {
                    "rows": [
                        dict(
                            symbol="AAPL",
                            name="Apple",
                            market_cap=100,
                            currency="USD",
                            source="Yahoo Finance",
                            url="https://finance.yahoo.com/quote/AAPL/",
                            displayed_share_pct=100,
                        )
                    ]
                }
            },
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_cache_only_read_and_missing_editorial_appear_immediately(self):
        with patch.object(worker._provider, "run") as provider:
            value = service.company_snapshot(self.settings, "us_45", "AAPL", NOW)
            provider.assert_not_called()
        self.assertTrue(value["products"])
        self.assertTrue(value["stale"])

    def test_queue_is_deduplicated_bounded_and_has_cooldown(self):
        first = service.enqueue_company(self.settings, "us_45", "AAPL")
        self.assertEqual(first["status"], "queued")
        self.assertEqual(
            service.enqueue_company(self.settings, "us_45", "AAPL")["status"], "queued"
        )
        path = service.root(self.settings) / "requests/AAPL.json"
        self.assertEqual(len(list(path.parent.glob("*.json"))), 1)
        path.unlink()
        value = CompanyKnowledge(
            symbol="AAPL", name="Apple", attempted_at=dt.datetime.now(dt.timezone.utc)
        )
        _write_cache(
            service.root(self.settings) / "AAPL.json", value.model_dump(mode="json")
        )
        self.assertEqual(
            service.enqueue_company(self.settings, "us_45", "AAPL")["status"], "recent"
        )
        (service.root(self.settings) / "AAPL.json").unlink()
        with patch.object(service, "QUEUE_LIMIT", 0):
            with self.assertRaises(HTTPException) as error:
                service.enqueue_company(self.settings, "us_45", "AAPL")
        self.assertEqual(error.exception.status_code, 429)

    def test_unknown_symbols_traversal_and_cloud_mode_are_rejected(self):
        for sector, symbol in [
            ("us_45", "../.env"),
            ("unknown", "AAPL"),
            ("sp500", "AAPL"),
            ("us_45", "NO_SUCH"),
        ]:
            with self.assertRaises(HTTPException):
                service.company_snapshot(self.settings, sector, symbol)
        self.settings.personal_local_mode = False
        with self.assertRaises(HTTPException):
            service.company_snapshot(self.settings, "us_45", "AAPL")

    def test_wrong_company_cache_is_discarded(self):
        _write_cache(
            service.root(self.settings) / "AAPL.json",
            CompanyKnowledge(symbol="MSFT", name="Microsoft").model_dump(mode="json"),
        )
        self.assertIsNone(service.read_company(self.settings, "AAPL"))

    def test_editorial_ads_relation_is_navigable_without_fabricating_a_quote(self):
        value = service.company_snapshot(self.settings, "us_45", "TSM", NOW)
        self.assertEqual(value["name"], "TSMC")
        self.assertIsNone(value["quote"]["market_cap"])
        self.assertIsNone(value["quote"]["displayed_share_pct"])
        self.assertEqual(
            service.related_directory(self.settings, ["TSM"])["TSM"]["sector"], "us_45"
        )

    def test_quote_basis_uses_the_full_received_universe(self):
        value = service.company_snapshot(self.settings, "us_45", "AAPL", NOW)
        self.assertEqual(value["quote_basis"]["count"], 1)
        self.assertEqual(value["quote_basis"]["market_cap_sum"], 100)

    def test_partial_collection_keeps_missing_old_financial_section(self):
        from cloud_app.company_schemas import Financial

        old = CompanyKnowledge(
            symbol="AAPL",
            name="Apple",
            fetched_at=NOW,
            financials=[
                Financial(
                    label="매출",
                    value=100,
                    unit="USD",
                    period="2025",
                    source=Source(label="SEC", url="https://data.sec.gov/"),
                )
            ],
        )
        _write_cache(
            service.root(self.settings) / "AAPL.json", old.model_dump(mode="json")
        )
        path = service.root(self.settings) / "requests/AAPL.json"
        _write_cache(path, {"sector": "us_45", "symbol": "AAPL"})
        partial = CompanyKnowledge(
            symbol="AAPL", name="Apple", errors=["SEC 수신 실패"], fetched_at=NOW
        ).model_dump(mode="json")
        with patch.object(worker._provider, "run", return_value=partial):
            worker.process_request(self.settings, path)
        result = service.read_company(self.settings, "AAPL")
        self.assertEqual(result.financials[0].value, 100)
        self.assertTrue(any("이전 수집" in error for error in result.errors))

    def test_worker_timeout_retains_original_data_and_timestamp(self):
        old = CompanyKnowledge(
            symbol="AAPL", name="Apple", fetched_at=NOW, description="original"
        )
        _write_cache(
            service.root(self.settings) / "AAPL.json", old.model_dump(mode="json")
        )
        path = service.root(self.settings) / "requests/AAPL.json"
        _write_cache(path, {"sector": "us_45", "symbol": "AAPL"})
        with patch.object(worker._provider, "run", side_effect=TimeoutError()):
            worker.process_request(self.settings, path)
        result = service.read_company(self.settings, "AAPL")
        self.assertEqual(result.description, "original")
        self.assertEqual(result.fetched_at, NOW)
        self.assertTrue(result.errors)
        self.assertFalse(path.exists())

    def test_timeout_on_first_fetch_still_shows_source_backed_notes(self):
        path = service.root(self.settings) / "requests/AAPL.json"
        _write_cache(path, {"sector": "us_45", "symbol": "AAPL"})
        with patch.object(worker._provider, "run", side_effect=TimeoutError()):
            worker.process_request(self.settings, path)
        self.assertTrue(
            service.company_snapshot(self.settings, "us_45", "AAPL")["products"]
        )

    def test_worker_revalidates_queue_filename_and_provider_identity(self):
        path = service.root(self.settings) / "requests/WRONG.json"
        _write_cache(path, {"sector": "us_45", "symbol": "AAPL"})
        with patch.object(worker._provider, "run") as provider:
            with self.assertRaises(ValueError):
                worker.process_request(self.settings, path)
            provider.assert_not_called()
        path.unlink()
        path = path.with_name("AAPL.json")
        _write_cache(path, {"sector": "us_45", "symbol": "AAPL"})
        with patch.object(
            worker._provider,
            "run",
            return_value={"symbol": "MSFT", "name": "Microsoft"},
        ):
            worker.process_request(self.settings, path)
        result = service.read_company(self.settings, "AAPL")
        self.assertEqual(result.symbol, "AAPL")
        self.assertTrue(result.errors)


if __name__ == "__main__":
    unittest.main()
