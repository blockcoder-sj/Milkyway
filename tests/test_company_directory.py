"""Exact, cache-only company navigation without reparsing every chart."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cloud_app.company_directory import lookup
from cloud_app.market_details import cache_path
from cloud_app.market_service import _write_cache
from cloud_app import sector_classifications as sectors


def row(symbol, name):
    return dict(symbol=symbol, name=name, currency='USD', market_cap=None,
        source='Yahoo', url='https://finance.yahoo.com/quote/'+symbol)


class DirectoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SimpleNamespace(personal_local_mode=True, production=False,
            dataset_dir=Path(self.temp.name)/'runtime/data')

    def tearDown(self):
        self.temp.cleanup()

    def test_navigation_is_independent_of_charts_and_never_fetches(self):
        _write_cache(cache_path(self.settings,'us_45'),
            {'companies':{'rows':[row('EXAMPLE','Verified received name')]}, 'history':{'rows':['unsupported']}})
        with patch('cloud_app.sector_classifications.fetch', side_effect=AssertionError('Unexpected I/O')):
            self.assertEqual(lookup(self.settings,['EXAMPLE'])['EXAMPLE']['sector'],'us_45')
        result = lookup(self.settings,['EXAMPLE'])
        result['EXAMPLE']['name'] = 'Changed'
        self.assertEqual(lookup(self.settings,['EXAMPLE'])['EXAMPLE']['name'],'Verified received name')
        self.assertEqual(lookup(self.settings,[]),{})

    def test_atomic_directory_change_invalidates_and_unknown_is_not_guessed(self):
        path = cache_path(self.settings,'us_45')
        _write_cache(path, {'companies':{'rows':[row('OLD','Old')]}})
        self.assertIn('OLD',lookup(self.settings,['OLD']))
        _write_cache(path, {'companies':{'rows':[row('NEW','New')]}})
        result = lookup(self.settings,['OLD','NEW','UNKNOWN'])
        self.assertEqual(set(result),{'NEW'})

    def test_disclosed_classification_wins_and_fallback_honors_current_sector(self):
        for sector in ['us_45','us_30']:
            _write_cache(cache_path(self.settings,sector),{'companies':{'rows':[row('MCD','McDonalds'),row('EXAMPLE','Example')]}})
        disclosed=sectors.Classification(symbol='MCD',name='McDonalds',sector='us_25',basis='Disclosed',
            source=dict(label='State Street',url=sectors.fund_url('XLY')))
        _write_cache(sectors.path(self.settings),sectors.ClassificationCache(rows=[disclosed]).model_dump(mode='json'))
        result=lookup(self.settings,['MCD','EXAMPLE'],'us_45')
        self.assertEqual(result['MCD']['sector'],'us_25')
        self.assertEqual(result['EXAMPLE']['sector'],'us_45')


if __name__=='__main__':
    unittest.main()
