"""Regression coverage for the GitHub-cloneable offline local sandbox."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cloud_app.config import get_settings
from cloud_app.local_demo import create_local_demo
from cloud_app.strategies import DatasetBundle, DatasetSummary


class LocalDemoTests(unittest.TestCase):
    def test_generated_demo_is_loadable_but_not_strict_backtest_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = create_local_demo(root)
            self.assertEqual(create_local_demo(root), dataset)
            settings = replace(
                get_settings(),
                dataset_dir=dataset,
                snapshots_glob=str(root / "universe_snapshots" / "*.json"),
                terminal_events_path=root / "universe_events" / "events.jsonl",
                local_demo_data=True,
            )
            summary = DatasetSummary(settings)
            bundle = DatasetBundle(settings)

            self.assertEqual(summary.symbol_count, 3)
            self.assertEqual(bundle.symbol_count, 3)
            self.assertFalse(summary.forward_data_gate_ready)
            self.assertFalse(bundle.forward_data_gate_ready)

    def test_production_rejects_the_local_demo_switch(self):
        settings = replace(get_settings(), app_env="production", local_demo_data=True)
        self.assertIn(
            "LOCAL_DEMO_DATA is allowed only in development",
            settings.startup_errors("app"),
        )
