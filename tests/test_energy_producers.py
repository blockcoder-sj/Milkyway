"""Producer selling routes, accounting scopes and current contract stages."""
from copy import deepcopy
import datetime as dt
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_annual_coordinates import APA, CRK, financial_label
from cloud_app.company_annual_financials import parse_annual_financials
from cloud_app.company_catalog import enrich
from cloud_app.company_energy_financial_archive import archive
from cloud_app.company_energy_majors import PRIVATE as MAJOR_PRIVATE
from cloud_app.company_energy_producers import PUBLIC, PRIVATE, EDGES, SYMBOLS
from cloud_app.company_energy_producer_revenue import COORDINATES, DOCUMENTS, dimensions
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer
from tests.test_company_annual_financials import annual
from tests.test_company_revenue import context, doc, fact


class EnergyProducerTests(unittest.TestCase):
    def test_sixteen_profiles_are_primary_edited_idempotent_and_registered(self):
        self.assertEqual(set(PUBLIC), set(SYMBOLS))
        self.assertEqual(len(PUBLIC), 16)
        for symbol, notes in PUBLIC.items():
            with self.subTest(symbol=symbol):
                value = enrich(CompanyKnowledge(symbol=symbol, **notes))
                self.assertGreaterEqual(len(value.brief), 6)
                self.assertEqual(len(value.products), 6)
                self.assertTrue(value.drivers and value.relations and value.financials and value.financial_context)
                self.assertEqual(enrich(value).model_dump(), value.model_dump())
                self.assertTrue(all(row.source.level == 'primary' and not row.original
                    for row in value.brief + value.products + value.drivers))
                self.assertNotIn('wikipedia', str(value.model_dump()).lower())
                self.assertEqual(issuer(symbol).group, 'upstream')
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)

    def test_original_receipts_financial_tags_and_scopes_match_the_reviewed_table(self):
        for symbol in SYMBOLS:
            record = archive()[symbol]
            self.assertEqual(record['annual']['url'], DOCUMENTS[symbol, int(record['cik'])])
            self.assertTrue(record['financial_context'])
            self.assertTrue(all(row['unit'] == 'USD' for row in record['financials']))
        self.assertEqual(archive()['APA']['financials'][0]['label'], '원유·가스 생산·매입 판매 매출')
        self.assertEqual(archive()['APA']['financials'][0]['value'], 8920000000)
        self.assertEqual(archive()['CRK']['financials'][0]['label'], '영업수입 · 자산 처분이익 포함')
        self.assertEqual(archive()['CRK']['financials'][0]['value'], 2220289000)
        mur = next(r for r in archive()['MUR']['financials'] if r['label'] == '계속사업 영업활동 현금흐름')
        self.assertEqual(mur['value'], 1247808000)
        self.assertIn('ContinuingOperations', mur['source']['label'])

    def test_product_sums_exclude_subtotals_derivatives_associates_and_asset_gains(self):
        expected = {'APA': 8920000000, 'CHRD': 4877126000, 'OVV': 8663000000,
            'MGY': 1311845000, 'MTDR': 3656514000, 'PR': 5065211000, 'SM': 3138000000,
            'CRC': 2910000000, 'CRGY': 3579782000, 'GPOR': 1323527000, 'CRK': 1928351000,
            'CNX': 1959077000, 'BKV': 893781000, 'MUR': 2689845000, 'NOG': 2095059000,
            'VTS': 273989000}
        for symbol, total in expected.items():
            rows = present_revenue(REPORTS[symbol]['revenue_mix'], symbol)
            products = [r for r in rows if r['group'] == 'product']
            with self.subTest(symbol=symbol):
                self.assertEqual(sum(r['value'] for r in products), total)
                self.assertFalse(any('Customer' in r['member'] or 'ReportableSegment' in r['member']
                                     for r in rows))
        bkv = present_revenue(REPORTS['BKV']['revenue_mix'], 'BKV')
        self.assertEqual(sum(r['value'] for r in bkv if r['group'] == 'geography'), 893781000)
        self.assertFalse(any(r['value'] in {11752000, 523540000} for r in bkv))
        crk = present_revenue(REPORTS['CRK']['revenue_mix'], 'CRK')
        gain, = [r for r in crk if r['group'] == 'revenue_type']
        self.assertEqual(gain['value'], 291938000)
        self.assertIsNone(gain['total'])
        self.assertTrue(all('share_exclusion' in r for r in crk))
        mur = present_revenue(REPORTS['MUR']['revenue_mix'], 'MUR')
        segments = [r for r in mur if r['group'] == 'segment']
        self.assertEqual(sum(r['value'] for r in segments), 2689800000)
        self.assertTrue(all('45,000' in r['share_exclusion'] for r in segments))

    def test_complete_axes_and_exact_issuer_control_every_reviewed_coordinate(self):
        for (symbol, cik, pairs), expected in COORDINATES.items():
            pairs = sorted(pairs)
            with self.subTest(symbol=symbol, member=expected[1]):
                self.assertEqual(dimensions(pairs, symbol, cik), expected)
                self.assertIsNone(dimensions(pairs + [('test:ExtraAxis', 'test:Member')], symbol, cik))
                self.assertIsNone(dimensions(pairs + [pairs[0]], symbol, cik))
                self.assertIsNone(dimensions(pairs, symbol, cik + 1))
                self.assertIsNone(dimensions(pairs, 'OTHER', cik))
                axis, member = pairs[0]
                extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>'
                                for a, m in pairs[1:])
                dates = dict(cik=str(cik), start='2025-01-01', end='2025-12-31')
                metric = ('us-gaap:Revenues' if symbol in {'APA', 'MGY'} or (symbol == 'OVV' and expected[0] == 'segment')
                    else 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax' if symbol == 'SM'
                    else 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax')
                raw = doc(context('total', **dates) + context('part', member, axis=axis, extra=extra, **dates),
                          fact('total', '100', metric=metric, scale=0) + fact('part', '70', metric=metric, scale=0))
                origin = dict(label='검토된 원문', level='primary', as_of='2026-03-16', url=DOCUMENTS[symbol, cik])
                row, = parse_revenue(raw, origin, symbol, dt.date(2026, 10, 3))
                self.assertEqual((row['group'], row['member'], row['value']), (*expected, 70))
                self.assertEqual(parse_revenue(raw.replace(str(cik), str(cik + 1)), origin, symbol), [])

    def test_apa_visible_combined_revenue_does_not_authorize_country_or_extra_axis_totals(self):
        dates = dict(start='2025-01-01', end='2025-12-31', cik='1841666')
        ctx = context('product', 'us-gaap:OilAndGasMember', **dates)
        raw = annual(ctx, fact('product', '8920'), period='2025-12-31')
        origin = dict(label='SEC 원문', url=APA, as_of='2026-02-26', level='primary')
        rows = parse_annual_financials(raw, origin, 1841666, dt.date(2026, 10, 3))
        self.assertEqual([(r['label'], r['value']) for r in rows], [('원유·가스 생산·매입 판매 매출', 8920000000)])
        for other in [raw.replace('2025', '2024'), raw.replace('us-gaap:OilAndGasMember', 'apa:OilAndGasExcludingPurchasedMember'),
                      raw.replace('</xbrli:segment>', '<xbrldi:explicitMember dimension="srt:StatementGeographicalAxis">country:US</xbrldi:explicitMember></xbrli:segment>')]:
            self.assertEqual(parse_annual_financials(other, origin, 1841666, dt.date(2026, 10, 3)), [])
        self.assertEqual(parse_annual_financials(raw, dict(origin, url=APA.replace('apa-20251231', 'other')), 1841666), [])
        self.assertEqual(financial_label('us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax', '매출',
            dict(origin, url=CRK), '2024-01-01 ~ 2024-12-31'), '매출')

    def test_operating_contracts_and_transactions_have_distinct_current_roles(self):
        for symbol, target in [('CHRD', '047050.KS'), ('CRK', 'socar-comstock'), ('SM', 'caturus-sm-assets')]:
            edge, = [e for e in EDGES[symbol] if target in (e['symbol'], e['registry_id'])]
            self.assertEqual(edge['kind'], 'transaction')
        ctv, = [e for e in EDGES['CRC'] if e['registry_id'] == 'carbon-terra-vault']
        self.assertEqual(ctv['kind'], 'partner')
        self.assertIn('지분법', ctv['detail'])
        self.assertIn('75%', str(PUBLIC['BKV']['brief']))
        self.assertIn('Q4 완료', str(PUBLIC['CHRD']['brief']))
        self.assertTrue(any(e['symbol'] == 'WBI' and e['kind'] == 'supplier' for e in EDGES['PR']))
        self.assertTrue(all(e['kind'] == 'customer' for e in EDGES['CNX']))
        self.assertFalse(any('Quantum' in str(e) for e in EDGES['CRK']))
        self.assertFalse(any(e['symbol'] == 'ET' for e in EDGES['CHRD']))
        saipem = private_profile('saipem')
        self.assertTrue(all(s in saipem['sources'] for s in MAJOR_PRIVATE['saipem']['sources']))
        self.assertTrue(any('GranMorgu' in r['title'] for r in saipem['brief']))

    def test_source_and_period_changes_do_not_inherit_the_asset_gain_correction(self):
        gain = next(r for r in REPORTS['CRK']['revenue_mix'] if r['member'] == 'crk:GainOnSaleOfAssetsMember')
        legacy = deepcopy(gain)
        legacy.update(label='Gain On Sale Of Assets', group='product', total=2220289000)
        corrected, = present_revenue([legacy], 'CRK')
        self.assertEqual(corrected['group'], 'revenue_type')
        self.assertIsNone(corrected['total'])
        for field, value in [('start', '2024-01-01'), ('end', '2024-12-31'),
                             ('source', dict(legacy['source'], url=legacy['source']['url'].replace('crk-20251231', 'other')))]:
            changed = deepcopy(legacy)
            changed.pop('share_exclusion', None)
            changed[field] = value
            result, = present_revenue([changed], 'CRK')
            self.assertEqual(result['total'], 2220289000)
            self.assertNotIn('share_exclusion', result)

    def test_counterpart_navigation_preserves_reverse_kind_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = CompanyGraph(SimpleNamespace(personal_local_mode=True, production=False,
                dataset_dir=Path(directory) / 'data'))
            for symbol in SYMBOLS:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol, name=symbol)), 'us_10')
            for key in PRIVATE:
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol, registry, reverse_kind in [('CNX', 'dte-energy-trading', 'supplier'),
                ('MUR', 'bw-offshore-pioneer', 'customer'), ('CRK', 'socar-comstock', 'transaction'),
                ('MTDR', 'san-mateo-midstream', 'parent')]:
                root = graph.by_symbol(symbol)
                edge = next(e for e in graph.relations(root['id'])
                            if graph.entity(e['target_id'])['registry_id'] == registry)
                self.assertTrue(graph.entity(edge['target_id'])['profile']['brief'])
                reverse = next(e for e in graph.relations(edge['target_id']) if e['target_id'] == root['id'])
                self.assertEqual(reverse['kind'], reverse_kind)
                self.assertEqual(reverse['source'], edge['source'])

    def test_verified_pinnacle_aliases_upgrade_old_exhibit_bookmarks_without_fuzzy_merge(self):
        origin=dict(label='SEC · Exhibit 21 자회사 명세서',level='primary',as_of='2026-02-24',
                    url='https://www.sec.gov/Archives/edgar/data/23194/000119312526059001/ex21.htm')
        names=('Pinnacle Gas Services LLC','Pinnacle Gas Services LLC (1)','Unverified Pinnacle Services LLC')
        relations=[dict(name=n,kind='subsidiary',source=origin,detail='공시 자회사 명세서 · 원문에 기재된 기업명 · 관할 미확인') for n in names]
        with tempfile.TemporaryDirectory() as directory:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,
                dataset_dir=Path(directory)/'data'))
            old=CompanyKnowledge(symbol='CRK',name='Comstock',relations=relations)
            owner=graph.ingest(old,'us_10')
            previous={r['name']:r['target_id'] for r in graph.relations(owner)}
            graph.ingest(CompanyKnowledge(**private_profile('pinnacle-comstock')))
            graph.ingest(enrich(old),'us_10')
            canonical=graph.entity(previous[names[0]])['id']
            self.assertEqual(graph.entity(previous[names[1]])['id'],canonical)
            self.assertEqual(graph.entity(canonical)['registry_id'],'pinnacle-comstock')
            self.assertNotEqual(graph.entity(previous[names[2]])['id'],canonical)
            edges=[r for r in graph.relations(owner) if r['target_id']==canonical]
            self.assertEqual(len(edges),1)
            self.assertTrue(any(e['source']['url']==origin['url'] for e in edges[0]['evidence']))

    def test_murphy_actual_exhibit_replaces_cached_item_numbers_and_excludes_parent(self):
        receipt=REPORTS['MUR']['subsidiaries']
        names=[r['name'] for r in REPORTS['MUR']['subsidiary_relations']]
        self.assertEqual((len(names),len(set(names))),(51,51))
        self.assertIn('Murphy Australia Oil Pty. Ltd.',names)
        self.assertIn('Arkansas Oil Company',names)
        self.assertFalse(any('REGISTRANT' in name for name in names))
        self.assertEqual(receipt['bytes'],87992)
        self.assertEqual(len(receipt['sha256']),64)
        with tempfile.TemporaryDirectory() as directory:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,
                dataset_dir=Path(directory)/'data'))
            origin={k:receipt[k] for k in ('label','url','as_of','level')}
            raw={'symbol':'MUR','name':'Murphy','relations':[dict(name='viii.',kind='subsidiary',source=origin,
                detail='공시 자회사 명세서에 기재된 기업명 · 기존 수집에서 관할을 확인하지 못했습니다.')]}
            owner=graph.ingest(enrich(CompanyKnowledge.model_validate(raw)),'us_10')
            rows=graph.relations(owner)
            self.assertFalse(any(r['name']=='viii.' for r in rows))
            self.assertEqual(len([r for r in rows if r['kind']=='subsidiary']),51)
            self.assertTrue(any(r['kind']=='customer' and r['symbol']=='CVX' for r in rows))
            self.assertFalse(any('100.00' in r['detail'] for r in rows))


if __name__ == '__main__':
    unittest.main()
