import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtest_core import run_backtest
from execution_price_store import build_0935_panel
from price_data_pipeline import (
    build_eligibility_mask,
    repair_ohlc_bounds,
    sha256_file,
    update_completed_sessions,
    validate_dataset,
    validate_price_frame,
)
from terminal_events import (
    append_event,
    append_snapshot_diff,
    load_events,
    unresolved_events,
)
from universe_snapshot import (
    build_snapshot,
    eligible_symbols,
    load_snapshot,
    save_snapshot,
)


NASDAQ_TEXT = """Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
GOOD|Good Corp. Common Stock|Q|N|N|100|N|N
FAIL|Failing Corp. Common Stock|S|N|Q|100|N|N
ETFQ|Example ETF|G|N|N|100|Y|N
TEST|Test Security|Q|Y|N|100|N|N
File Creation Time: 0824202611:01|||||||
"""

OTHER_TEXT = """ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
NYSE|NYSE Corp. Common Stock|N|NYSE|N|100|N|NYSE
AMEX|American Corp. Common Stock|A|AMEX|N|100|N|AMEX
ARCA|Arca Corp. Common Stock|P|ARCA|N|100|N|ARCA
WARR|Example Corp. Warrants|N|WARR|N|100|N|WARR
FUND|Example Income Fund Common Shares|N|FUND|N|100|N|FUND
NOTE|Example Corp. Subordinated Notes|N|NOTE|N|100|N|NOTE
File Creation Time: 0824202611:01||||||
"""


def config(**overrides):
    value = {
        "capital": 100_000,
        "max_positions": 1,
        "sector_cap_pct": 1.0,
        "cost_per_side": 0.0,
        "position_stop_pct": None,
        "buffer_mult": 1.0,
        "inertia_bonus": 0.0,
        "risk_free_rate": 0.0,
        "rebal_interval": 100,
        "max_replace_per_rebal": 1,
        "missing_price_policy": "raise",
        "fractional_shares": True,
        "dynamic_stop_enabled": False,
        "min_signal_count": 1,
    }
    value.update(overrides)
    return value


class UniverseSnapshotTests(unittest.TestCase):
    def test_regular_exchange_filter_keeps_distressed_common_stock(self):
        snapshot = build_snapshot(
            NASDAQ_TEXT,
            OTHER_TEXT,
            captured_at=dt.datetime(2026, 8, 25, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(snapshot["effective_date"], "2026-08-24")
        self.assertEqual(
            eligible_symbols(snapshot), {"GOOD", "FAIL", "NYSE", "AMEX", "ARCA"}
        )
        self.assertTrue(next(row for row in snapshot["records"] if row["symbol"] == "FAIL")["eligible"])
        self.assertIn("ARCA", eligible_symbols(snapshot))
        self.assertNotIn("FUND", eligible_symbols(snapshot))
        self.assertNotIn("NOTE", eligible_symbols(snapshot))

    def test_snapshot_hash_detects_tampering(self):
        snapshot = build_snapshot(NASDAQ_TEXT, OTHER_TEXT)
        with tempfile.TemporaryDirectory() as directory:
            path = save_snapshot(snapshot, directory)
            self.assertEqual(load_snapshot(path)["membership_sha256"], snapshot["membership_sha256"])
            payload = json.loads(path.read_text())
            payload["records"][0]["eligible"] = not payload["records"][0]["eligible"]
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_snapshot(path)

    def test_snapshot_diff_is_unresolved_not_fake_terminal_loss(self):
        previous = build_snapshot(NASDAQ_TEXT, OTHER_TEXT)
        current = build_snapshot(
            NASDAQ_TEXT.replace("GOOD|Good Corp. Common Stock|Q|N|N|100|N|N\n", ""),
            OTHER_TEXT,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            added = append_snapshot_diff(previous, current, path)
            self.assertEqual([event["ticker"] for event in added], ["GOOD"])
            self.assertEqual(load_events(path)[0]["status"], "unresolved")
            self.assertIsNone(load_events(path)[0]["cash_per_share"])


class DataContractTests(unittest.TestCase):
    def test_price_quality_rejects_impossible_ohlc(self):
        frame = pd.DataFrame(
            {
                "Open": [10.0],
                "High": [9.0],
                "Low": [8.0],
                "Close": [10.0],
                "Volume": [100.0],
            },
            index=pd.to_datetime(["2026-01-02"]),
        )
        result = validate_price_frame(frame)
        self.assertFalse(result["valid"])
        self.assertEqual(result["bad_ohlc_rows"], 1)

    def test_price_quality_allows_float_roundoff_only(self):
        frame = pd.DataFrame(
            {
                "Open": [6.944611],
                "High": [6.944611],
                "Low": [6.777116 + 8.88e-16],
                "Close": [6.777116],
                "Volume": [1_000_000.0],
            },
            index=pd.to_datetime(["2026-06-29"]),
        )
        result = validate_price_frame(frame)
        self.assertTrue(result["valid"])
        self.assertEqual(result["bad_ohlc_rows"], 0)

    def test_bounded_ohlc_repair_preserves_signal_and_execution_columns(self):
        frame = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [99.0],
                "Low": [98.0],
                "Close": [99.5],
                "Volume": [500_000.0],
            },
            index=pd.to_datetime(["2026-08-24"]),
        )
        repaired, audit = repair_ohlc_bounds(frame)
        self.assertTrue(validate_price_frame(repaired)["valid"])
        self.assertEqual(float(repaired.iloc[0]["Open"]), 100.0)
        self.assertEqual(float(repaired.iloc[0]["Close"]), 99.5)
        self.assertEqual(float(repaired.iloc[0]["Volume"]), 500_000.0)
        self.assertEqual(float(repaired.iloc[0]["High"]), 100.0)
        self.assertEqual(len(audit), 1)

    def test_ohlc_repair_refuses_large_deviation(self):
        frame = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [50.0],
                "Low": [40.0],
                "Close": [90.0],
                "Volume": [500_000.0],
            },
            index=pd.to_datetime(["2026-08-24"]),
        )
        repaired, audit = repair_ohlc_bounds(frame)
        self.assertFalse(validate_price_frame(repaired)["valid"])
        self.assertEqual(audit, [])

    def test_strict_membership_mask_is_empty_before_first_snapshot(self):
        snapshot = build_snapshot(NASDAQ_TEXT, OTHER_TEXT)
        index = pd.to_datetime(["2026-08-21", "2026-08-24", "2026-08-25"])
        mask = build_eligibility_mask([snapshot], index, ["GOOD", "ETFQ"])
        self.assertFalse(bool(mask.loc["2026-08-21", "GOOD"]))
        self.assertTrue(bool(mask.loc["2026-08-24", "GOOD"]))
        self.assertFalse(bool(mask.loc["2026-08-24", "ETFQ"]))

    def test_0935_panel_selects_nearest_observation(self):
        observations = [
            {
                "ticker": "AAA",
                "price": 10,
                "observed_at_utc": "2026-01-02T14:34:00+00:00",
                "source": "broker",
            },
            {
                "ticker": "AAA",
                "price": 11,
                "observed_at_utc": "2026-01-02T14:35:05+00:00",
                "source": "broker",
            },
        ]
        panel = build_0935_panel(observations)
        self.assertEqual(float(panel.loc["2026-01-02", "AAA"]), 11.0)

    def test_incremental_update_appends_without_deleting_verified_history(self):
        nasdaq = """Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
AAA|AAA Corp. Common Stock|Q|N|N|100|N|N
File Creation Time: 0103202618:30|||||||
"""
        other = """ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
File Creation Time: 0103202618:30||||||
"""
        snapshot = build_snapshot(nasdaq, other)
        old = pd.DataFrame(
            {
                "Open": [10.0, 11.0], "High": [11.0, 12.0], "Low": [9.0, 10.0],
                "Close": [10.5, 11.5], "Volume": [300_000.0, 310_000.0],
            },
            index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
        )
        fresh = pd.DataFrame(
            {
                "Open": [11.0, 12.0], "High": [12.0, 13.0], "Low": [10.0, 11.0],
                "Close": [11.5, 12.5], "Volume": [310_000.0, 320_000.0],
            },
            index=pd.to_datetime(["2026-01-02", "2026-01-03"]),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "dataset"
            price_dir = dataset / "prices"
            price_dir.mkdir(parents=True)
            price_path = price_dir / "AAA_data.pkl"
            old.to_pickle(price_path)
            manifest = {
                "schema_version": 1,
                "provider_parameters": {"start": "2026-01-01", "end_exclusive": "2026-01-03"},
                "snapshot_paths": [], "snapshot_membership_sha256": [],
                "prices": {"AAA": {"rows": 2, "first_date": "2026-01-01", "last_date": "2026-01-02", "sha256": sha256_file(price_path)}},
                "failures": {},
            }
            (dataset / "manifest.json").write_text(json.dumps(manifest))
            snapshot_path = save_snapshot(snapshot, root / "snapshots")
            fake_yfinance = SimpleNamespace(download=lambda *args, **kwargs: fresh.copy())
            with patch.dict(sys.modules, {"yfinance": fake_yfinance}):
                result = update_completed_sessions(
                    dataset, [snapshot_path], end_exclusive="2026-01-04", batch_size=50
                )
            updated = pd.read_pickle(price_path)
            self.assertEqual(list(updated.index), list(pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])))
            self.assertEqual(result["refresh_errors"], {})
            self.assertEqual(json.loads((dataset / "manifest.json").read_text())["prices"]["AAA"]["rows"], 3)

    def test_missing_latest_row_blocks_an_otherwise_eligible_candidate(self):
        index = pd.bdate_range(end="2026-08-21", periods=60)
        frame = pd.DataFrame(
            {
                "Open": 10.0,
                "High": 11.0,
                "Low": 9.0,
                "Close": 10.0,
                "Volume": 300_000.0,
            },
            index=index,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "dataset"
            price_dir = dataset / "prices"
            price_dir.mkdir(parents=True)
            price_path = price_dir / "GOOD_data.pkl"
            frame.to_pickle(price_path)
            (dataset / "manifest.json").write_text(
                json.dumps(
                    {
                        "prices": {
                            "GOOD": {
                                "sha256": sha256_file(price_path),
                                "last_date": "2026-08-21",
                            }
                        }
                    }
                )
            )
            snapshot = build_snapshot(NASDAQ_TEXT, OTHER_TEXT)
            snapshot_path = save_snapshot(snapshot, root / "snapshots")
            report = validate_dataset(
                dataset,
                start="2026-08-24",
                end="2026-08-24",
                current_snapshot_path=snapshot_path,
            )
            self.assertFalse(report["forward_strategy_data_gate_ready"])
            self.assertIn("GOOD", report["strategy_candidate_data_blockers"])


class BacktestIntegrationTests(unittest.TestCase):
    def test_verified_terminal_cash_is_settled_when_close_disappears(self):
        index = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"])
        close = pd.DataFrame({"AAA": [10.0, 10.0, np.nan]}, index=index)
        scores = pd.DataFrame({"AAA": [1.0, 1.0, np.nan]}, index=index)
        event = {
            "ticker": "AAA",
            "effective_date": "2026-01-06",
            "event_type": "cash_merger",
            "status": "verified",
            "cash_per_share": 4.0,
            "source": "issuer filing",
        }
        result = run_backtest(
            scores,
            close,
            config=config(execution_timing="close"),
            get_sector=lambda _: "all",
            terminal_events=[event],
        )
        self.assertAlmostEqual(result["equity_curve"].iloc[-1], 40_000.0)
        self.assertEqual(result["trade_log"][-1]["side"], "CORPORATE_ACTION")
        self.assertEqual(result["trade_log"][-1]["fee"], 0.0)

    def test_next_0935_uses_explicit_execution_panel(self):
        index = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"])
        close = pd.DataFrame({"AAA": [10.0, 10.0, 10.0]}, index=index)
        scores = pd.DataFrame({"AAA": [1.0, 1.0, 1.0]}, index=index)
        execution = pd.DataFrame({"AAA": [10.0, 20.0, 10.0]}, index=index)
        result = run_backtest(
            scores,
            close,
            config=config(execution_timing="next_0935"),
            get_sector=lambda _: "all",
            execution_prices=execution,
        )
        self.assertEqual(result["trade_log"][0]["price"], 20.0)
        self.assertAlmostEqual(result["equity_curve"].iloc[1], 50_000.0)

    def test_eligibility_mask_blocks_higher_scoring_ineligible_symbol(self):
        index = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"])
        close = pd.DataFrame(
            {"AAA": [10.0, 10.0, 10.0], "BBB": [10.0, 10.0, 10.0]}, index=index
        )
        scores = pd.DataFrame(
            {"AAA": [2.0, 2.0, 2.0], "BBB": [1.0, 1.0, 1.0]}, index=index
        )
        eligible = pd.DataFrame(
            {"AAA": [False, False, False], "BBB": [True, True, True]}, index=index
        )
        result = run_backtest(
            scores,
            close,
            config=config(execution_timing="close"),
            get_sector=lambda _: "all",
            eligible_mask=eligible,
        )
        self.assertEqual(result["trade_log"][0]["ticker"], "BBB")

    def test_event_store_is_idempotent(self):
        event = {
            "ticker": "AAA",
            "effective_date": "2026-01-06",
            "event_type": "liquidation",
            "status": "verified",
            "cash_per_share": 1.5,
            "source": "court filing",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            self.assertTrue(append_event(path, event)[1])
            self.assertFalse(append_event(path, event)[1])
            self.assertEqual(len(load_events(path)), 1)

    def test_verified_event_resolves_prior_append_only_alert(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            append_event(
                path,
                {
                    "ticker": "AAA",
                    "effective_date": "2026-01-05",
                    "event_type": "exchange_exit",
                    "status": "unresolved",
                },
            )
            append_event(
                path,
                {
                    "ticker": "AAA",
                    "effective_date": "2026-01-06",
                    "event_type": "cash_merger",
                    "status": "verified",
                    "cash_per_share": 10.0,
                    "source": "issuer filing",
                },
            )
            self.assertEqual(unresolved_events(load_events(path)), [])


if __name__ == "__main__":
    unittest.main()
