"""Market feed/cache checks use only synthetic responses and temporary files."""

import datetime as dt
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

from cloud_app import market_feed, market_service
from cloud_app.market_catalog import CATALOG, FX, INDICES, US_SECTORS, KR_SECTORS

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 9, 30, 14, 0, tzinfo=UTC)


def payload(instrument=INDICES[0]):
    return {"chart": {"error": None, "result": [{
        "meta": {"symbol": instrument.symbol,
                 "instrumentType": "CURRENCY" if instrument.group == "fx" else "INDEX",
                 "regularMarketPrice": 110, "previousClose": 100,
                 "chartPreviousClose": 90, "regularMarketTime": NOW.timestamp(),
                 "currentTradingPeriod": {"regular": {
                     "start": (NOW - dt.timedelta(hours=1)).timestamp(),
                     "end": (NOW + dt.timedelta(hours=5)).timestamp()}}},
        "timestamp": [(NOW - dt.timedelta(minutes=5)).timestamp(), NOW.timestamp()],
        "indicators": {"quote": [{"close": [100, 110]}]},
    }]}}


class MarketDisplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SimpleNamespace(personal_local_mode=True, production=False,
                                        dataset_dir=Path(self.temp.name) / "personal-data")

    def tearDown(self):
        self.temp.cleanup()

    def seed(self):
        observation = market_feed.parse_chart(payload(), INDICES[0], NOW).model_dump(mode="json")
        with patch.object(market_service._provider, "run", return_value=[{"id":"sp500", "observation":observation}]):
            market_service.refresh_market(self.settings)
        return observation

    def test_catalog_is_unique_and_covers_actual_index_and_fx_categories(self):
        self.assertEqual(len(CATALOG), 37)
        self.assertEqual(len({item.id for item in CATALOG}), 37)
        self.assertEqual(len(US_SECTORS), 11)
        self.assertEqual(len(KR_SECTORS), 8)
        self.assertEqual(len(FX), 5)
        self.assertTrue(all(item.group == "sectors" for item in US_SECTORS + KR_SECTORS))

    def test_prior_close_is_not_replaced_by_multiday_baseline(self):
        result = market_feed.parse_chart(payload(), INDICES[0], NOW)
        self.assertEqual(result.previous_close, 100)
        self.seed()
        row = market_service.market_overview(self.settings, now=NOW)["items"][0]
        self.assertEqual(row["change_pct"], 10)
        self.assertFalse(row["is_realtime"])
        self.assertEqual(row["status"], "delayed")

    def test_invalid_symbol_type_price_and_future_timestamp_are_rejected(self):
        for changes in ({"symbol":"OTHER"}, {"instrumentType":"ETF"},
                        {"regularMarketPrice":float("nan")}, {"regularMarketPrice":-1},
                        {"regularMarketPrice":True}, {"regularMarketTime":NOW.timestamp()+3600}):
            with self.subTest(changes=changes):
                data = payload()
                data["chart"]["result"][0]["meta"].update(changes)
                with self.assertRaises(ValueError):
                    market_feed.parse_chart(data, INDICES[0], NOW)

    def test_hundred_yen_units_apply_to_price_prior_close_and_chart(self):
        item = next(item for item in FX if item.id == "jpykrw")
        result = market_feed.parse_chart(payload(item), item, NOW)
        self.assertEqual(result.value, 11000)
        self.assertEqual(result.previous_close, 10000)
        self.assertEqual(result.sparkline, [10000, 11000])

    def test_missing_prior_close_is_unknown_not_zero_percent(self):
        data = payload()
        del data["chart"]["result"][0]["meta"]["previousClose"]
        result = market_feed.parse_chart(data, INDICES[0], NOW)
        self.assertIsNone(result.previous_close)

    def test_empty_cache_is_bounded_catalog_and_never_fetches_on_read(self):
        with patch.object(market_service._provider, "run") as provider:
            result = market_service.market_overview(self.settings, now=NOW)
        provider.assert_not_called()
        self.assertEqual(result["available_count"], 0)
        self.assertEqual(len(result["items"]), 37)
        self.assertTrue(all(row["value"] is None for row in result["items"]))

    def test_partial_failure_and_timeout_preserve_prior_value_and_timestamp(self):
        old = self.seed()
        for result in ([{"id":"sp500", "error":"synthetic unavailable"}], TimeoutError()):
            kwargs = {"side_effect":result} if isinstance(result, Exception) else {"return_value":result}
            with patch.object(market_service._provider, "run", **kwargs):
                market_service.refresh_market(self.settings)
            row = market_service.market_overview(self.settings, now=NOW)["items"][0]
            self.assertEqual(row["value"], old["value"])
            self.assertEqual(row["fetched_at"], old["fetched_at"])
            self.assertEqual(row["status"], "stale")

    def test_old_cache_and_old_observation_are_marked_stale(self):
        self.seed()
        row = market_service.market_overview(self.settings, now=NOW+dt.timedelta(minutes=12))["items"][0]
        self.assertEqual(row["status"], "stale")
        self.assertIsNotNone(row["value"])

    def test_corrupt_oversized_and_symlink_cache_fail_closed(self):
        cache = market_service.cache_path(self.settings)
        for data in ("not-json", "[]", "x" * (market_service.MAX_CACHE_BYTES+1)):
            cache.write_text(data)
            self.assertEqual(market_service.market_overview(self.settings, now=NOW)["available_count"],0)
        cache.unlink()
        target = cache.parent / "target"
        target.write_text('{"version":1,"items":{}}')
        cache.symlink_to(target)
        self.assertEqual(market_service.read_cache(self.settings), {})

    def test_provider_uses_fixed_origin_bounded_body_and_no_redirects(self):
        response = Mock(status_code=200)
        session = Mock()
        session.get.return_value = response
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=False)
        data = payload()
        data["chart"]["result"][0]["meta"]["regularMarketTime"] = dt.datetime.now(UTC).timestamp()
        with patch.object(market_feed.requests, "Session", return_value=session), \
             patch.object(market_feed, "read_requests_json", return_value=data) as read:
            result = market_feed.fetch_one(INDICES[0])
        self.assertIn("observation", result)
        self.assertFalse(session.trust_env)
        args, kwargs = session.get.call_args
        self.assertEqual(args[0], "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC")
        self.assertFalse(kwargs["allow_redirects"])
        self.assertTrue(kwargs["stream"])
        read.assert_called_once_with(response, maximum_bytes=256*1024)

    def test_feed_is_unavailable_outside_personal_mode(self):
        self.settings.personal_local_mode = False
        with self.assertRaises(ValueError):
            market_service.refresh_market(self.settings)


if __name__ == "__main__":
    unittest.main()
