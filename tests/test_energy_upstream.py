"""Own production/resale, exact dimensions and sourced operating counterparties."""
from copy import deepcopy
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_upstream import PUBLIC, PRIVATE, EDGES, ANNUAL
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class EnergyUpstreamTests(unittest.TestCase):
    def test_profiles_private_navigation_and_sources(self):
        self.assertEqual(set(PUBLIC), {'EOG', 'FANG', 'OXY', 'DVN', 'EQT', 'EXE', 'AR', 'RRC'})
        for symbol, notes in PUBLIC.items():
            value = CompanyKnowledge(symbol=symbol, **notes)
            self.assertTrue(value.brief and value.products and value.segments and value.drivers and value.revenue_mix)
            self.assertEqual(enrich(value).model_dump(), enrich(enrich(value)).model_dump())
            self.assertGreaterEqual(len(enrichment(symbol)['relations']), len(EDGES[symbol]))
            for row in value.brief + value.products + value.segments + value.drivers:
                self.assertEqual(row.source.level, 'primary')
                self.assertNotIn('wikipedia', row.source.url)
            self.assertEqual(next(row.source.url for row in value.brief if row.title == '매출이 생기는 구조'),
                             ANNUAL[symbol]['url'])
        for key in PRIVATE:
            value = CompanyKnowledge(**private_profile(key))
            self.assertTrue(value.relations, key)
        for rows in EDGES.values():
            for row in rows:
                if row['registry_id']:
                    self.assertTrue(private_profile(row['registry_id'])['brief'])

    def test_revenue_roots_and_different_accounting_scopes(self):
        for symbol, group, amount in [('EOG', 'segment', 22632000000),
                ('EOG', 'product', 22582000000), ('FANG', 'product', 14929000000),
                ('DVN', 'product', 16786000000), ('EXE', 'product', 11639000000),
                ('AR', 'product', 5275823000), ('RRC', 'product', 2988164000)]:
            rows = REPORTS[symbol]['revenue_mix']
            self.assertEqual(sum(row['value'] for row in rows if row['group'] == group and not row['parent']), amount)
        fang = REPORTS['FANG']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in fang if r['parent'] == 'fang:OilNaturalGasAndNaturalGasLiquidMember'), 13453000000)
        oxy = REPORTS['OXY']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in oxy if r['group'] == 'product'), 20902000000)
        self.assertEqual(sum(r['value'] for r in oxy if r['group'] == 'segment') - 588000000, 21593000000)
        eqt = REPORTS['EQT']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in eqt if r['group'] == 'segment') - 1253532000, 8644211000)
        self.assertEqual(len([r for r in eqt if r['group'] == 'segment']), 3)
        self.assertFalse(any(r['member'] == 'us-gaap:OilAndGasMember' for r in eqt))
        for symbol in ('OXY', 'EQT'):
            for row in REPORTS[symbol]['revenue_mix']:
                if row['group'] == 'segment':
                    self.assertTrue(row['includes_intersegment'] and row['share_exclusion'])
                    self.assertIsNone(row['total'])

    def test_devon_exact_two_axes_and_parent_sums(self):
        origin = ANNUAL['DVN']
        dates = dict(cik='1090012', start='2025-01-01', end='2025-12-31')
        location = '<xbrldi:explicitMember dimension="us-gaap:IncomeStatementLocationAxis">dvn:OilGasAndNGLSalesMember</xbrldi:explicitMember>'
        raw = doc(context('total', **dates) + context('part', 'srt:OilReservesMember',
            axis='srt:ProductOrServiceAxis', extra=location, **dates), fact('total', '16786') + fact('part', '8906'))
        row, = parse_revenue(raw, origin, 'DVN')
        self.assertIn('/dvn:OilGasAndNGLSalesMember', row['member'])
        self.assertEqual(row['value'], 8906000000)
        self.assertEqual(parse_revenue(raw, origin, 'OTHER'), [])
        self.assertEqual(parse_revenue(raw.replace('1090012', '1090013'), origin, 'DVN'), [])
        self.assertEqual(parse_revenue(raw.replace('dvn:OilGasAndNGLSalesMember', 'dvn:UnknownMember'), origin, 'DVN'), [])
        for parent, total in [('dvn:OilGasAndNGLSalesMember', 11223000000),
                              ('dvn:MarketingAndMidstreamRevenuesMember', 5563000000)]:
            self.assertEqual(sum(row['value'] for row in REPORTS['DVN']['revenue_mix'] if row['parent'] == parent), total)

    def test_eqt_legacy_duplicate_only_removed_when_exactly_equivalent(self):
        production = deepcopy(next(row for row in REPORTS['EQT']['revenue_mix']
            if row['member'] == 'eqt:SalesOfNaturalGasNGLsAndOilAtProductionMember'))
        duplicate = {**production, 'member': 'us-gaap:OilAndGasMember'}
        self.assertEqual(len(present_revenue([production, duplicate], 'EQT')), 1)
        for changed in [{**duplicate, 'value': duplicate['value'] + 1},
                        {**duplicate, 'unit': 'EUR'},
                        {**duplicate, 'source': {**duplicate['source'], 'url': duplicate['source']['url'].replace('20251231', '20241231')}}]:
            self.assertEqual(len(present_revenue([production, changed], 'EQT')), 2)
        self.assertEqual(len(present_revenue([production, duplicate], 'OTHER')), 2)

    def test_eqt_segment_metric_keeps_upstream_with_gross_table(self):
        qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        dates = dict(cik='33213', start='2025-01-01', end='2025-12-31')
        contexts = context('total', **dates) + context('up', 'eqt:UpstreamSegmentMember',
            axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier, **dates)
        contexts += context('gather', 'eqt:GatheringSegmentMember',
            axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier, **dates)
        values = fact('total', '8644.211')
        values += fact('up', '8024.057') + fact('gather', '1301.434')
        values += fact('gather', '1301.434', metric='us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax')
        rows = parse_revenue(doc(contexts, values), ANNUAL['EQT'], 'EQT')
        self.assertEqual({row['member'] for row in rows}, {'eqt:UpstreamSegmentMember', 'eqt:GatheringSegmentMember'})
        self.assertTrue(all(row['metric'] == 'us-gaap:Revenues' and row['share_exclusion'] for row in rows))

    def test_current_and_historical_contracts_are_not_conflated(self):
        oxy = ' '.join(row['detail'] for row in PUBLIC['OXY']['segments'])
        self.assertIn('2026년 1월 2일', oxy)
        self.assertIn('계약 체결 물량', oxy)
        devon = ' '.join(row['detail'] for row in PUBLIC['DVN']['segments'])
        self.assertIn('2026년 5월 7일', devon)
        self.assertFalse(any(row.get('symbol') == 'CTRA' for row in EDGES['DVN']))
        exe = ' '.join(row['detail'] for row in PUBLIC['EXE']['segments'])
        self.assertIn('9월 16일', exe)
        self.assertIn('SPA는 종료', exe)
        self.assertFalse(any(row['name'] == 'Gunvor' for row in EDGES['EXE']))
        for symbol, supplier in [('EOG', 'PUMP'), ('OXY', 'LBRT'), ('EQT', 'SND'), ('EXE', 'PTEN')]:
            self.assertTrue(any(row['symbol'] == supplier and row['kind'] == 'supplier' for row in EDGES[symbol]))
        for symbol in PUBLIC:
            comparisons = [row for row in EDGES[symbol] if row['kind'] == 'competitor']
            self.assertTrue(comparisons)
            self.assertTrue(all('비교 대상' in row['detail'] for row in comparisons))

    def test_range_site_roles_keep_unknown_contract_date_and_identity(self):
        rows = [row for row in EDGES['RRC'] if '현장 안내' in row['detail']]
        self.assertEqual(len(rows), 8)
        self.assertFalse(any(row['symbol'] == 'FLOC' for row in rows))
        profrac = next(row for row in rows if row['name'] == 'ProFrac')
        self.assertEqual(profrac['registry_id'], 'range-profrac')
        for row in rows:
            self.assertIn('지속 여부 미확인', row['detail'])
            self.assertIn('발표일 미표기', row['source']['as_of'])
            if row['symbol']:
                self.assertTrue(any(edge['symbol'] == 'RRC' and edge['kind'] == 'customer'
                    for edge in EDGES[row['symbol']]))


if __name__ == '__main__':
    unittest.main()
