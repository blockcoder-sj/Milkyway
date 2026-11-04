"""Offline history generation, failover and selected-universe regressions."""

import datetime as dt
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

from cloud_app.config import get_settings
from cloud_app.local_demo import create_local_demo
from cloud_app import personal_data as history
from cloud_app.strategies import (
    DatasetBundle, StrategySpec, compile_raw_scores, get_dataset_bundle,
    latest_candidates, raw_factor, run_strategy_backtest, strategy_code_preview,
)
from price_data_pipeline import _atomic_price_frame, price_file_path, sha256_file


NOW = dt.datetime(2026, 9, 25, 14, 0, tzinfo=dt.timezone.utc)


def frame_ending(day, rows=350, *, multiplier=1):
    dates = pd.bdate_range(end=day, periods=rows)
    values = np.arange(rows, dtype=float)
    close = 90 + values * .04 * multiplier + np.sin(values / 7)
    return pd.DataFrame({"Open": close - .1, "High": close + 1, "Low": close - 1,
                         "Close": close, "Volume": np.full(rows, 1_000_000)}, index=dates)


def write_outcome(payload, configuration, **kwargs):
    result = {"prices": {}, "corporate_actions": {}}
    for offset, ticker in enumerate(payload["symbols"]):
        frame = frame_ending(payload["required_session"], multiplier=offset+1)
        path = price_file_path(Path(configuration["target"]) / "prices", ticker)
        _atomic_price_frame(frame, path)
        result["prices"][ticker] = {"rows": len(frame), "first_date": frame.index.min().date().isoformat(),
            "last_date": frame.index.max().date().isoformat(), "sha256": sha256_file(path),
            "action_checked_on": payload["action_day"]}
        result["corporate_actions"][ticker] = []
    return result


class PersonalDataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.settings = replace(get_settings(), app_env="development", personal_local_mode=True,
            local_demo_data=False, dataset_dir=self.root / "history",
            snapshots_glob=str(self.root / "unused" / "*.json"),
            terminal_events_path=self.root / "events.jsonl")
        self.spec = StrategySpec(name="Selected strategy", symbols=["AAPL"],
            factors=[{"kind": "momentum", "lookback": 20}],
            filters={"history_days": 20, "min_average_volume": 0})

    def tearDown(self):
        self.temporary.cleanup()

    def refresh(self, symbols=("AAPL",), now=NOW):
        with patch.object(history._history_process, "run", side_effect=write_outcome):
            return history.refresh_personal_data(list(symbols), self.settings, now=now)

    def test_initial_status_and_generation_are_uncertified_but_usable(self):
        self.assertFalse(history.personal_data_status(self.settings, now=NOW)["ready"])
        status = self.refresh()
        self.assertTrue(status["ready"], status)
        bundle = get_dataset_bundle(self.settings)
        self.assertFalse(bundle.forward_data_gate_ready)
        self.assertFalse(bundle.snapshots[0]["certification_eligible"])
        self.assertEqual(bundle.snapshots[0]["records"][0]["exchange"], "USER_SELECTED")
        self.assertEqual(latest_candidates(self.spec, bundle, now=NOW), ["AAPL"])
        with self.assertRaisesRegex(ValueError, "strict PIT"):
            run_strategy_backtest(self.spec, start="2026-07-01", end="2026-09-24", settings=self.settings)
        result = run_strategy_backtest(self.spec, start="2026-07-01", end="2026-09-24",
            bias_mode="exploratory", settings=self.settings)
        self.assertGreater(result["metrics"]["trade_count"], 0)
        self.assertFalse(result["certification_eligible"])

    def test_provider_failure_and_atomic_publish_failure_keep_last_generation(self):
        first = self.refresh()
        pointer = (self.settings.dataset_dir / "current.json").read_bytes()
        later = NOW + dt.timedelta(days=3)
        with patch.object(history._history_process, "run", side_effect=TimeoutError("synthetic hang")):
            status = history.refresh_personal_data(["AAPL"], self.settings, now=later)
        self.assertEqual((self.settings.dataset_dir / "current.json").read_bytes(), pointer)
        self.assertEqual(status["generation"], first["generation"])
        self.assertTrue(status["stale"])
        self.assertIsNotNone(status["error"])
        original = history._atomic_json
        def fail_pointer(path, value):
            if path.name == "current.json":
                raise OSError("synthetic disk full at promotion")
            return original(path, value)
        with patch.object(history._history_process, "run", side_effect=write_outcome), patch.object(history, "_atomic_json", side_effect=fail_pointer):
            history.refresh_personal_data(["AAPL"], self.settings, now=later)
        self.assertEqual((self.settings.dataset_dir / "current.json").read_bytes(), pointer)
        self.assertEqual(latest_candidates(self.spec, get_dataset_bundle(self.settings), now=NOW), ["AAPL"])

    def test_per_symbol_freshness_does_not_hide_other_symbol_failure(self):
        self.refresh(["AAPL", "MSFT"])
        def partial(payload, configuration, **kwargs):
            return write_outcome(dict(payload, symbols=["AAPL"]), configuration)
        later = NOW + dt.timedelta(days=3)
        with patch.object(history._history_process, "run", side_effect=partial):
            status = history.refresh_personal_data(["AAPL", "MSFT"], self.settings, now=later)
        self.assertEqual(status["stale_symbols"], ["MSFT"])
        self.assertTrue(history.personal_data_status(self.settings, symbols=["AAPL"], now=later)["ready"])
        bundle = get_dataset_bundle(self.settings)
        self.assertEqual(latest_candidates(self.spec, bundle, now=later), ["AAPL"])
        with self.assertRaises(ValueError):
            latest_candidates(self.spec.model_copy(update={"symbols": ["MSFT"]}), bundle, now=later)

    def test_partial_refresh_cannot_certify_another_symbols_daily_action_check(self):
        friday_after_close = dt.datetime(2026, 9, 25, 21, tzinfo=dt.timezone.utc)
        self.refresh(["AAPL", "MSFT"], now=friday_after_close)
        monday_open = NOW + dt.timedelta(days=3)
        def partial(payload, configuration, **kwargs):
            return write_outcome(dict(payload, symbols=["AAPL"]), configuration)
        with patch.object(history._history_process, "run", side_effect=partial):
            status = history.refresh_personal_data(["AAPL", "MSFT"], self.settings, now=monday_open)
        self.assertFalse(status["ready"])
        self.assertEqual(status["stale_symbols"], [])  # Both still have Friday close.
        self.assertEqual(status["missing_action_symbols"], ["MSFT"])
        bundle = get_dataset_bundle(self.settings)
        self.assertEqual(latest_candidates(self.spec, bundle, now=monday_open), ["AAPL"])
        with self.assertRaisesRegex(ValueError, "기업행사"):
            latest_candidates(self.spec.model_copy(update={"symbols": ["MSFT"]}), bundle, now=monday_open)

    def test_identical_partial_retries_do_not_accumulate_generations(self):
        def partial(payload, configuration, **kwargs):
            return write_outcome(dict(payload, symbols=["AAPL"]), configuration)
        with patch.object(history._history_process, "run", side_effect=partial):
            first = history.refresh_personal_data(["AAPL", "BAD"], self.settings, now=NOW)
            for minute in range(1, 4):
                later = history.refresh_personal_data(["AAPL", "BAD"], self.settings, now=NOW + dt.timedelta(minutes=minute))
                self.assertEqual(later["generation"], first["generation"])
                self.assertEqual(later["missing_symbols"], ["BAD"])
        self.assertEqual(len(list((self.settings.dataset_dir / "generations").iterdir())), 1)

    def test_seven_calendar_days_and_restart_readers_keep_consistent_generations(self):
        prior_bundle = None
        for offset in range(7):
            now = NOW + dt.timedelta(days=offset)
            status = self.refresh(["AAPL", "MSFT"], now)
            self.assertTrue(status["ready"], (now, status))
            restarted_bundle = DatasetBundle(self.settings)
            self.assertEqual(latest_candidates(self.spec, restarted_bundle, now=now), ["AAPL"])
            if prior_bundle is not None:
                self.assertTrue(prior_bundle.manifest_path.exists())
            prior_bundle = restarted_bundle

    def test_selection_rank_is_not_contaminated_by_other_strategies(self):
        self.refresh(["AAPL", "MSFT"])
        bundle = get_dataset_bundle(self.settings)
        scores = compile_raw_scores(self.spec, bundle)
        self.assertEqual(list(scores.columns), ["AAPL"])
        self.assertEqual(scores.iloc[-1, 0], 1.0)

    def test_rsi_handles_uninterrupted_uptrend_and_flat_prices(self):
        close = pd.DataFrame({"UP": np.arange(1., 31.), "FLAT": np.full(30, 10.)})
        values = raw_factor("rsi", 20, {"Close": close})
        self.assertEqual(values.iloc[-1]["UP"], 1.)
        self.assertEqual(values.iloc[-1]["FLAT"], 0.)
        self.assertTrue(values.iloc[0].isna().all())

    def test_download_excludes_intraday_and_future_prices_but_preserves_today_actions(self):
        raw = frame_ending("2026-09-28", rows=50)
        raw["Stock Splits"] = 0.
        raw["Dividends"] = 0.
        raw.loc[pd.Timestamp("2026-09-25"), "Stock Splits"] = 2.
        target = self.root / "download"
        target.mkdir()
        with patch.dict("sys.modules", {"yfinance": SimpleNamespace(download=lambda *a, **k: raw)}):
            result = history._download_history({"symbols": ["AAPL"], "required_session": "2026-09-24", "action_day": "2026-09-25"}, {"target": str(target)})
        self.assertEqual(result["prices"]["AAPL"]["last_date"], "2026-09-24")
        self.assertEqual(result["corporate_actions"]["AAPL"], [{"date": "2026-09-25", "split_ratio": 2., "dividend": 0.}])
        self.assertEqual(result["prices"]["AAPL"]["action_checked_on"], "2026-09-25")

    def test_yesterday_only_premarket_response_does_not_claim_today_actions_checked(self):
        raw = frame_ending("2026-09-24", rows=50)
        with patch.dict("sys.modules", {"yfinance": SimpleNamespace(download=lambda *a, **k: raw)}):
            result = history._download_history({"symbols": ["AAPL"], "required_session": "2026-09-24", "action_day": "2026-09-25"}, {"target": str(self.root / "premarket")})
        self.assertIsNone(result["prices"]["AAPL"]["action_checked_on"])

    def test_premarket_wait_does_not_redownload_already_current_history(self):
        self.refresh(now=dt.datetime(2026, 9, 25, 21, tzinfo=dt.timezone.utc))
        with patch.object(history._history_process, "run") as download:
            status = history.refresh_personal_data(["AAPL"], self.settings, now=dt.datetime(2026, 9, 28, 11, tzinfo=dt.timezone.utc))
        download.assert_not_called()
        self.assertFalse(status["action_ready"])
        self.assertEqual(status["fresh_symbols"], ["AAPL"])
        self.assertIn("완료된 일봉은 준비", status["error"])

    def test_invalid_prices_never_replace_valid_dataset(self):
        first = self.refresh()
        def tampered(payload, configuration, **kwargs):
            value = write_outcome(payload, configuration)
            value["prices"]["AAPL"]["sha256"] = "0" * 64
            return value
        with patch.object(history._history_process, "run", side_effect=tampered):
            status = history.refresh_personal_data(["AAPL"], self.settings, now=NOW + dt.timedelta(days=3))
        self.assertEqual(status["generation"], first["generation"])
        self.assertIsNotNone(status["error"])

    def test_same_session_corruption_and_deletion_are_repaired_without_waiting_for_tomorrow(self):
        self.refresh(["AAPL", "MSFT"])
        for damage in ("corrupt", "delete"):
            with self.subTest(damage=damage):
                before = history.resolve_personal_settings(self.settings)
                healthy = price_file_path(before.dataset_dir / "prices", "MSFT").read_bytes()
                damaged = price_file_path(before.dataset_dir / "prices", "AAPL")
                if damage == "corrupt":
                    damaged.write_bytes(b"synthetic disk corruption")
                else:
                    damaged.unlink()
                status = history.personal_data_status(self.settings, now=NOW)
                self.assertFalse(status["ready"])
                self.assertEqual(status["invalid_symbols"], ["AAPL"])
                self.assertTrue(history.personal_data_status(self.settings, symbols=["MSFT"], now=NOW)["ready"])
                with patch.object(history._history_process, "run", side_effect=write_outcome) as download:
                    repaired = history.refresh_personal_data(["AAPL", "MSFT"], self.settings, now=NOW)
                self.assertEqual(download.call_args.args[0]["symbols"], ["AAPL"])
                self.assertTrue(repaired["ready"], repaired)
                self.assertNotEqual(repaired["generation"], before.dataset_dir.name)
                after = history.resolve_personal_settings(self.settings)
                self.assertEqual(price_file_path(after.dataset_dir / "prices", "MSFT").read_bytes(), healthy)
                self.assertEqual(set(DatasetBundle(self.settings).data), {"AAPL", "MSFT"})

    def test_failed_corruption_repair_excludes_bad_fallback_and_retains_healthy_symbols(self):
        self.refresh(["AAPL", "MSFT"])
        before = history.resolve_personal_settings(self.settings)
        healthy = price_file_path(before.dataset_dir / "prices", "MSFT").read_bytes()
        price_file_path(before.dataset_dir / "prices", "AAPL").write_bytes(b"broken")
        with patch.object(history._history_process, "run", side_effect=TimeoutError("repair unavailable")):
            status = history.refresh_personal_data(["AAPL", "MSFT"], self.settings, now=NOW)
        self.assertFalse(status["ready"])
        self.assertEqual(status["missing_symbols"], ["AAPL"])
        self.assertTrue(history.personal_data_status(self.settings, symbols=["MSFT"], now=NOW)["ready"])
        after = history.resolve_personal_settings(self.settings)
        self.assertFalse(price_file_path(after.dataset_dir / "prices", "AAPL").exists())
        self.assertEqual(price_file_path(after.dataset_dir / "prices", "MSFT").read_bytes(), healthy)
        bundle = DatasetBundle(self.settings)
        self.assertEqual(set(bundle.data), {"MSFT"})
        with self.assertRaises(ValueError):
            latest_candidates(self.spec, bundle, now=NOW)
        self.assertTrue(before.dataset_dir.exists())

    def test_personal_preview_names_selected_universe_without_changing_production(self):
        preview = strategy_code_preview(self.spec, self.settings)
        self.assertIn("selected_symbols = ['AAPL']", preview)
        self.assertNotIn("pit_membership", preview)
        production = strategy_code_preview(self.spec, replace(self.settings, app_env="production"))
        self.assertIn("pit_membership", production)
        self.assertNotIn("selected_symbols", production)

    def test_complete_session_clock_handles_holiday_weekend_and_early_close(self):
        self.assertEqual(history.last_completed_session(dt.datetime(2026, 9, 7, 20, tzinfo=dt.timezone.utc)), dt.date(2026, 9, 4))
        self.assertEqual(history.last_completed_session(dt.datetime(2026, 11, 27, 18, 14, tzinfo=dt.timezone.utc)), dt.date(2026, 11, 25))
        self.assertEqual(history.last_completed_session(dt.datetime(2026, 11, 27, 18, 16, tzinfo=dt.timezone.utc)), dt.date(2026, 11, 27))

    def test_symbol_validation_and_production_scope(self):
        self.assertEqual(self.spec.model_copy().symbols, ["AAPL"])
        for symbols in (["../../secret"], ["AAPL;exit"], ["한글"], ["A" + str(i) for i in range(101)]):
            with self.assertRaises(ValueError):
                StrategySpec(name="Bad symbols", symbols=symbols, factors=[{"kind": "momentum"}])
        with self.assertRaises(ValueError):
            history.refresh_personal_data(["AAPL"], replace(self.settings, app_env="production"), now=NOW)

    def test_demo_exploratory_works_without_enabling_strict(self):
        dataset = create_local_demo(self.root / "demo")
        settings = replace(self.settings, personal_local_mode=False, local_demo_data=True,
            dataset_dir=dataset, snapshots_glob=str(self.root / "demo" / "universe_snapshots" / "*.json"))
        spec = self.spec.model_copy(update={"symbols": []})
        result = run_strategy_backtest(spec, start="2026-04-01", end="2026-09-18", bias_mode="exploratory", settings=settings)
        self.assertGreater(result["metrics"]["trade_count"], 0)
        with self.assertRaises(ValueError):
            run_strategy_backtest(spec, start="2026-04-01", end="2026-09-18", settings=settings)

    def test_personal_backtest_retains_all_trades_beyond_five_hundred(self):
        def churning(payload, configuration, **kwargs):
            result = {"prices": {}, "corporate_actions": {}}
            for offset, symbol in enumerate(payload["symbols"]):
                frame = frame_ending(payload["required_session"])
                close = 100. + ((np.arange(len(frame)) + offset) % 2) * .01
                for column in ("Open", "Close"):
                    frame[column] = close
                frame["High"], frame["Low"] = close + 1, close - 1
                path = price_file_path(Path(configuration["target"]) / "prices", symbol)
                _atomic_price_frame(frame, path)
                result["prices"][symbol] = {"rows": len(frame), "first_date": str(frame.index.min().date()),
                    "last_date": str(frame.index.max().date()), "sha256": sha256_file(path), "action_checked_on": payload["action_day"]}
                result["corporate_actions"][symbol] = []
            return result
        with patch.object(history._history_process, "run", side_effect=churning):
            status = history.refresh_personal_data(["AAA", "BBB"], self.settings, now=NOW)
        self.assertTrue(status["ready"])
        spec = StrategySpec(name="High turnover export", symbols=["AAA", "BBB"],
            factors=[{"kind": "momentum", "lookback": 3}],
            filters={"history_days": 20, "min_average_volume": 0},
            portfolio={"max_positions": 1, "rebalance_days": 1, "stop_loss_pct": None})
        bundle = get_dataset_bundle(self.settings)
        result = run_strategy_backtest(spec, start=str(bundle.index[40].date()), end="2026-09-24", bias_mode="exploratory", settings=self.settings)
        self.assertGreater(result["metrics"]["trade_count"], 500)
        self.assertEqual(len(result["trades"]), result["metrics"]["trade_count"])


if __name__ == "__main__":
    unittest.main()
