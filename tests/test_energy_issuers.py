"""Issuer identity is exact; a research roster never certifies a GICS code."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from cloud_app.energy_issuers import issuer, registry, augment, summary
from cloud_app.company_directory import lookup
from cloud_app.company_service import company_row
from cloud_app.company_catalog import editorial_for
from cloud_app.sector_classifications import ClassificationView, ReadOnlyClassification


class EnergyIssuerTests(unittest.TestCase):
    def test_exact_current_identities_and_off_index_otc_are_preserved(self):
        self.assertEqual(len(registry().rows), 187)
        self.assertEqual(len({row.symbol for row in registry().rows}), 187)
        self.assertEqual(issuer('XOM').cik, '2115436')
        self.assertIn('ARKO', issuer('APC').name)
        self.assertIn('Summit', issuer('SMC').name)
        self.assertIn('Sunoco', issuer('SUNC').name)
        for symbol in ('AMEN', 'UNTC'):
            self.assertIsNone(issuer(symbol).cik)
            self.assertEqual(issuer(symbol).identity_source.level, 'primary')
        for symbol in ('HNR', 'IXPZ6', 'NRGU', 'RISE', 'USDP', 'UNKNOWN'):
            self.assertIsNone(issuer(symbol))
        self.assertEqual(editorial_for('KGS')['cik'], '1767042')

    def test_roster_and_nested_evidence_are_immutable(self):
        row = issuer('CQP')
        with self.assertRaises(ValidationError):
            row.name = 'Changed'
        with self.assertRaises(ValidationError):
            row.report_source.url = 'https://evil.example'
        info = summary()
        info['identity_source']['label'] = 'Changed'
        self.assertNotEqual(summary()['identity_source']['label'], 'Changed')

    def test_official_sector_wins_and_unknown_market_caps_cannot_make_weights(self):
        row = ReadOnlyClassification(symbol='KGS', name='Kodiak', sector='us_20', basis='Disclosed',
            source=dict(label='Official holding', url='https://example.test/holding'))
        initial = [dict(symbol='XOM', name='Exxon', market_cap=100, currency='USD',
                       source='Quote', url='https://finance.yahoo.com/quote/XOM', displayed_share_pct=100)]
        rows, added, omitted = augment(initial, 'us_10', ClassificationView(rows=(row,)))
        self.assertGreater(added, 150)
        self.assertEqual(omitted, 0)
        self.assertEqual(len({r['symbol'] for r in rows}), len(rows))
        self.assertNotIn('KGS', {r['symbol'] for r in rows})
        self.assertNotIn('NFG', {r['symbol'] for r in rows})
        self.assertTrue(all(r['displayed_share_pct'] is None for r in rows))
        self.assertTrue(all(r.get('classification') is None for r in rows))
        self.assertEqual(initial[0]['displayed_share_pct'], 100)
        self.assertEqual(augment(initial, 'us_45', ClassificationView())[0], initial)
        limited, added, omitted = augment(initial, 'us_10', ClassificationView(), maximum=2)
        self.assertEqual(len(limited), 2)
        self.assertEqual(added, 1)
        self.assertGreater(omitted, 150)

    def test_directory_and_page_do_not_require_provider_or_fund_membership(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = SimpleNamespace(personal_local_mode=True, production=False,
                                       dataset_dir=Path(temp)/'runtime/data')
            with patch('cloud_app.company_feed.get', side_effect=AssertionError('Provider I/O')):
                rows = lookup(settings, ['CQP', 'UNTC', 'UNKNOWN'])
                self.assertEqual(set(rows), {'CQP', 'UNTC'})
                self.assertEqual(company_row(settings, 'us_10', 'CQP')['symbol'], 'CQP')
                self.assertEqual(company_row(settings, 'us_10', 'UNTC')['name'], 'Unit Corporation')
                self.assertEqual(company_row(settings, 'us_55', 'NFG')['symbol'], 'NFG')


if __name__ == '__main__':
    unittest.main()
