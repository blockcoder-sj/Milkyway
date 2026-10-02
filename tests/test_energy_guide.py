"""Offline energy guide contract, source bindings, escaping and navigation."""
import datetime as dt
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from cloud_app import energy_guide
from cloud_app.market_details import detail_snapshot


class EnergyGuideTests(unittest.TestCase):
    def test_all_reading_notes_bind_to_primary_sources(self):
        guide = energy_guide.snapshot()
        self.assertEqual(len(guide['industries']), 7)
        self.assertEqual(len({x['code'] for x in guide['industries']}), 7)
        self.assertLess(len(json.dumps(guide, ensure_ascii=False).encode()), 100_000)
        self.assertIn('진행 중', guide['scope'])
        for source in guide['sources'].values():
            url = urlsplit(source['url'])
            self.assertEqual(url.scheme, 'https')
            self.assertIsNone(url.username)
            self.assertNotIn('wikipedia', url.hostname)
            self.assertNotIn('wikidata', url.hostname)
        for item in [*guide['industries'], *[i for section in guide['sections'] for i in section['entries']]]:
            self.assertTrue(item['body'])
            for source in item['source_ids']:
                self.assertIn(source, guide['sources'])
        # Callers can never corrupt a later cached HTTP snapshot.
        guide['sources'].clear()
        guide['sections'][0]['entries'][0]['steps'].clear()
        fresh = energy_guide.snapshot()
        self.assertTrue(fresh['sources'])
        self.assertTrue(fresh['sections'][0]['entries'][0]['steps'])

    def test_only_energy_receives_offline_industry_guide(self):
        now = dt.datetime(2026, 10, 2, tzinfo=dt.timezone.utc)
        with tempfile.TemporaryDirectory() as temp:
            settings = SimpleNamespace(personal_local_mode=True, production=False, dataset_dir=Path(temp)/'data')
            with patch('cloud_app.sector_classifications.fetch', side_effect=AssertionError('No request-time source fetching')):
                self.assertIn('industry_guide', detail_snapshot(settings, 'us_10', now))
                self.assertNotIn('industry_guide', detail_snapshot(settings, 'us_45', now))



if __name__ == '__main__':
    unittest.main()
