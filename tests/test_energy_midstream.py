"""Offline checks for reviewed operating links and midstream revenue scope."""
from copy import deepcopy
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_midstream import PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class MidstreamResearchTests(unittest.TestCase):
    def test_profiles_are_bounded_sourced_and_idempotent(self):
        for symbol, profile in PUBLIC.items():
            value = CompanyKnowledge(symbol=symbol, **profile)
            self.assertTrue(value.description_source)
            self.assertTrue(value.segments)
            self.assertTrue(value.drivers)
            self.assertTrue(value.revenue_mix)
            self.assertEqual(enrich(value).model_dump(), enrich(enrich(value)).model_dump())
            for item in value.brief + value.segments + value.products + value.drivers:
                self.assertEqual(item.source.level, 'primary')
        for key in PRIVATE:
            value = CompanyKnowledge(**private_profile(key))
            self.assertTrue(value.relations, key)
        for symbol, edges in EDGES.items():
            value = CompanyKnowledge(symbol=symbol, name=symbol, **enrichment(symbol))
            self.assertGreaterEqual(len(value.relations), len(edges))
            for edge in edges:
                self.assertEqual(edge['source']['level'], 'primary')
                if edge['registry_id']:
                    self.assertTrue(private_profile(edge['registry_id'])['brief'])

    def test_external_revenue_and_subtotals_reconcile(self):
        kmi = [r for r in REPORTS['KMI']['revenue_mix'] if r['group'] == 'segment']
        self.assertEqual(sum(r['value'] for r in kmi), 16937000000)
        self.assertEqual({r['total'] for r in kmi}, {16937000000})
        for symbol, total in [('OKE', 33629000000), ('LNG', 19464000000)]:
            rows = [r for r in REPORTS[symbol]['revenue_mix'] if r['group'] == 'product']
            self.assertEqual(sum(r['value'] for r in rows if not r['parent']), total)
        wmb = [r for r in REPORTS['WMB']['revenue_mix'] if r['group'] == 'revenue_type']
        self.assertEqual(sum(r['value'] for r in wmb), 14899000000)
        self.assertNotEqual(sum(r['value'] for r in wmb), 11950000000)

    def test_targa_coordinate_excludes_internal_totals_and_eliminations(self):
        cik = '1389170'
        origin = {k: REPORTS['TRGP']['annual'][k] for k in ('label', 'url', 'as_of', 'level')}
        segment = 'trgp:GatheringAndProcessingMember'
        qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        dates = dict(start='2025-01-01', end='2025-12-31', cik=cik)
        contexts = context('total', **dates) + context('gather', segment,
            axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier, **dates)
        raw = doc(contexts, fact('total', '17028.3') + fact('gather', '2692.6'))
        row, = parse_revenue(raw, origin, 'TRGP')
        self.assertEqual(row['value'], 2692600000)
        self.assertIn('530만', row['share_exclusion'])
        for wrong in ('us-gaap:IntersegmentEliminationMember', 'us-gaap:MaterialReconcilingItemsMember'):
            self.assertEqual(parse_revenue(raw.replace('us-gaap:OperatingSegmentsMember', wrong), origin, 'TRGP'), [])
        self.assertEqual(parse_revenue(raw, origin, 'OTHER'), [])

    def test_lng_subset_and_signed_adjustment_are_document_bound(self):
        rows = deepcopy(REPORTS['LNG']['revenue_mix'])
        child = next(r for r in rows if 'ProcuredFromThirdParties' in r['member'])
        self.assertEqual(child['parent'], 'lng:LiquefiedNaturalGasMember')
        child['parent'] = None
        before = deepcopy(rows)
        updated = present_revenue(rows, 'LNG')
        self.assertEqual(rows, before)
        self.assertEqual(next(r for r in updated if 'ProcuredFromThirdParties' in r['member'])['parent'], 'lng:LiquefiedNaturalGasMember')
        targa = [r for r in REPORTS['TRGP']['revenue_mix'] if r['group'] == 'segment']
        self.assertEqual(sum(r['value'] for r in targa) - 5300000, 17028300000)
        self.assertTrue(all(r['share_exclusion'] for r in targa))
        legacy = deepcopy(targa[0]); legacy.pop('share_exclusion')
        changed = {**legacy, 'source': {**legacy['source'], 'url': legacy['source']['url'].replace('000119312526059296', '000119312527059296')}}
        self.assertNotIn('share_exclusion', present_revenue([changed], 'TRGP')[0])

    def test_current_operating_links_and_plans_are_distinct(self):
        self.assertTrue(any(r['kind'] == 'customer' and r['symbol'] == 'DUK' for r in EDGES['WMB']))
        self.assertTrue(any(r['kind'] == 'supplier' and r['symbol'] == 'EOG' for r in EDGES['LNG']))
        self.assertTrue(any(r['kind'] == 'customer' and r['symbol'] == 'PBR' for r in EDGES['LNG']))
        self.assertFalse(any(r.get('symbol') == 'BX' for r in EDGES['TRGP']))
        wmb = ' '.join(r['detail'] for r in PUBLIC['WMB']['segments'])
        lng = ' '.join(r['detail'] for r in PUBLIC['LNG']['segments'])
        self.assertIn('9월 3일', wmb)
        self.assertIn('마지막', lng)
        self.assertIn('개시 연도', lng)


if __name__ == '__main__':
    unittest.main()
