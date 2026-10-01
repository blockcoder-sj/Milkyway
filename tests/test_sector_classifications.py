"""Synthetic disclosure parsing, exact sector joins and offline cache boundaries."""
import datetime as dt
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cloud_app import sector_classifications as sector
from cloud_app.market_service import _write_cache
from cloud_app.market_details import cache_path, detail_snapshot

NOW = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)


def classification(symbol="MCD", identity="us_25"):
    return sector.Classification(symbol=symbol, name="McDonalds", sector=identity,
        basis="Public disclosure", source=dict(label="State Street", url=sector.fund_url("XLY"), as_of="2026-09-30"))


def quote(symbol="MCD", cap=100):
    return dict(symbol=symbol, name=symbol, market_cap=cap, currency="USD",
                source="Yahoo", url="https://finance.yahoo.com/quote/" + symbol, displayed_share_pct=100)


class ClassificationTests(unittest.TestCase):
    def test_csv_identity_sector_and_exact_us_exchange_tickers(self):
        head = b'iShares Core S&P Total U.S. Stock Market ETF\nFund Holdings as of,"Sep 30, 2026"\n\nTicker,Name,Sector,Asset Class,Location,Exchange,Market Currency\n'
        raw = head + b'MCD,McDonalds,Consumer Discretionary,Equity,United States,NYSE,USD\n' * 500
        raw += b'BAD,Foreign,Consumer Staples,Equity,Japan,NYSE,USD\nCASH,Money,Consumer Staples,Cash,United States,NYSE,USD\n'
        rows = sector.parse_itot(raw, NOW)
        self.assertEqual(len(rows), 500)
        self.assertEqual(rows[0].sector, "us_25")
        self.assertEqual(rows[0].source.as_of, "2026-09-30")
        with self.assertRaises(ValueError):
            sector.parse_itot(raw.replace(b'Core S&P', b'Other S&P'), NOW)
        with self.assertRaises(ValueError):
            sector.parse_itot(raw, NOW - dt.timedelta(days=2))

    def test_spreadsheet_fund_identity_date_and_cash_exclusion(self):
        import xml.etree.ElementTree as ET
        ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        strings = ['Fund Name:', 'Technology Fund', 'XLK', 'As of 30-Sep-2026', 'Name', 'Ticker', 'NVIDIA', 'NVDA', '67066G104', 'USD', 'CASH']
        shared = ET.Element('sst', xmlns=ns)
        for string in strings:
            ET.SubElement(ET.SubElement(shared, 'si'), 't').text = string
        sheet = ET.Element('worksheet', xmlns=ns)
        body = ET.SubElement(sheet, 'sheetData')
        values = [{'A':0,'B':1},{'A':0,'B':2},{'A':0,'B':3},{'A':4,'B':5}, {'A':6,'B':7,'C':8,'H':9},{'A':10,'B':10,'H':9}]
        for index, value in enumerate(values, 1):
            row = ET.SubElement(body, 'row')
            for col, string in value.items():
                ET.SubElement(ET.SubElement(row, 'c', r=f'{col}{index}', t='s'), 'v').text = str(string)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('xl/sharedStrings.xml', ET.tostring(shared))
            archive.writestr('xl/worksheets/sheet1.xml', ET.tostring(sheet))
        rows = sector.parse_fund(buffer.getvalue(), 'XLK', NOW)
        self.assertEqual([r.symbol for r in rows], ['NVDA'])
        with self.assertRaises(ValueError):
            sector.parse_fund(buffer.getvalue(), 'XLY', NOW)
        with self.assertRaises(ValueError):
            sector.xlsx_rows(b'x' * (2 * 1024 * 1024 + 1))

    def test_misclassified_company_moves_and_missing_disclosure_members_are_added(self):
        cache = sector.ClassificationCache(rows=[classification()], fetched_at=NOW)
        rows, audit = sector.reconcile([quote()], 'us_30', cache, NOW)
        self.assertEqual(rows, [])
        self.assertEqual(audit['moved'], [{'symbol':'MCD','sector':'us_25'}])
        rows, audit = sector.reconcile([quote('OTHER')], 'us_25', cache, NOW)
        self.assertEqual({r['symbol'] for r in rows}, {'MCD','OTHER'})
        self.assertIsNone(next(r for r in rows if r['symbol']=='MCD')['market_cap'])
        self.assertTrue(all(r['displayed_share_pct'] is None for r in rows))
        self.assertEqual(audit['unverified'], 1)
        self.assertIsNone(next(r for r in rows if r['symbol']=='OTHER')['classification'])

    def test_network_is_fixed_no_environment_proxy_or_redirect(self):
        with patch.object(sector, 'FixedSession') as session:
            with self.assertRaises(ValueError):
                sector.fetch('https://localhost/secret')
            session.assert_not_called()
        from cloud_app.market_broker_feed import FixedSession
        session = FixedSession()
        self.assertFalse(session.trust_env)
        session.close()

    def test_cache_snapshot_has_classification_but_never_fetches(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = SimpleNamespace(personal_local_mode=True, production=False, dataset_dir=Path(temp)/'data')
            _write_cache(sector.path(settings), sector.ClassificationCache(rows=[classification()], fetched_at=NOW).model_dump(mode='json'))
            _write_cache(cache_path(settings,'us_25'), {'companies':{'rows':[quote()], 'fetched_at':NOW.isoformat()}})
            with patch.object(sector, 'fetch', side_effect=AssertionError('Unexpected network')):
                snapshot = detail_snapshot(settings, 'us_25', NOW)
                self.assertEqual(snapshot['companies']['rows'][0]['classification']['sector'], 'us_25')
                self.assertEqual(snapshot['companies']['classification_audit']['matched'],1)
            read = sector.read(settings)
            read.rows.clear()
            self.assertEqual(len(sector.read(settings).rows),1)

    def test_failed_source_retained_successful_disclosure_can_retract(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = SimpleNamespace(personal_local_mode=True, production=False, dataset_dir=Path(temp)/'data')
            old = sector.ClassificationCache(rows=[classification(), classification('OTHER')], fetched_at=NOW)
            _write_cache(sector.path(settings), old.model_dump(mode='json'))
            fresh = sector.ClassificationCache(rows=[classification()], fetched_at=NOW, attempted_at=NOW, errors=['ITOT failed'])
            provider = SimpleNamespace(run=lambda *a,**kw:fresh.model_dump(mode='json'))
            self.assertEqual([r.symbol for r in sector.refresh(settings,provider).rows], ['MCD'])


if __name__=='__main__':
    unittest.main()
