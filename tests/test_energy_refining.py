"""Offline contracts for primary-source refining notes and accounting scope."""
from copy import deepcopy
import unittest
from urllib.parse import urlsplit

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_refining import PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class RefiningResearchTests(unittest.TestCase):
    def test_profiles_validate_sources_and_linked_context_pages(self):
        for symbol, profile in PUBLIC.items():
            value = CompanyKnowledge(symbol=symbol, **profile)
            self.assertEqual(enrich(value).model_dump(), enrich(enrich(value)).model_dump())
            self.assertLessEqual(len(value.brief), 8)
        for key in PRIVATE:
            value = CompanyKnowledge(**private_profile(key))
            self.assertTrue(value.relations)
            self.assertTrue(value.brief)
        for symbol, edges in EDGES.items():
            value = CompanyKnowledge(symbol=symbol, name=symbol, **enrichment(symbol))
            self.assertGreaterEqual(len(value.relations), len(edges))
            for row in edges:
                self.assertEqual(row['source']['level'], 'primary')
                host = urlsplit(row['source']['url']).hostname
                self.assertNotIn('wikipedia', host)
                self.assertNotIn('wikidata', host)
                if row['registry_id']:
                    self.assertIsNotNone(private_profile(row['registry_id']))
        # Additional refining edges must extend, not replace earlier Chevron work.
        names = {r['name'] for r in enrichment('CVX')['relations']}
        self.assertTrue({'Baker Hughes', 'HF Sinclair', 'Phillips 66'} <= names)

    def test_external_revenue_roots_reconcile_without_duplicate_subtotals(self):
        totals = {'MPC': 132699000000, 'PSX': 132376000000, 'DINO': 26869000000}
        for symbol, total in totals.items():
            rows = REPORTS[symbol]['revenue_mix']
            self.assertTrue(rows)
            for group in {r['group'] for r in rows} - {'revenue_type'}:
                values = [r for r in rows if r['group'] == group]
                self.assertEqual(sum(r['value'] for r in values if not r['parent']), total)
                self.assertEqual({r['total'] for r in values}, {total})
                self.assertTrue(all(not r['includes_intersegment'] for r in values))
        dino = REPORTS['DINO']['revenue_mix']
        self.assertEqual(len([r for r in dino if r['parent']]), 3)
        rin, = [r for r in dino if r['group'] == 'revenue_type']
        self.assertEqual(rin['value'], 430000000)
        self.assertIn('기타 매출의 일부', rin['label'])

    def test_reviewed_events_are_visible_without_duplicate_old_appendix_facts(self):
        for symbol in ('MPC', 'PSX', 'DINO'):
            profile = PUBLIC[symbol]
            self.assertEqual(len(profile['brief']), 8)
            event = deepcopy(profile['brief'][-1])
            other = {**event, 'detail': 'Earlier distinct evidence must remain.'}
            old = CompanyKnowledge(symbol=symbol, name=symbol, facts=[event, other])
            updated = enrich(old)
            self.assertEqual([r.detail for r in updated.facts], [other['detail']])
            self.assertEqual(len(old.facts), 2)

    def test_corporate_coordinate_is_exact_and_issuer_bound(self):
        for symbol, cik, value in [('MPC', 1510295, 5), ('PSX', 1534701, 37)]:
            origin = {k: REPORTS[symbol]['annual'][k] for k in ('label', 'url', 'as_of', 'level')}
            contexts = (context('total', cik=str(cik)) + context('corp',
                'us-gaap:CorporateNonSegmentMember', axis='srt:ConsolidationItemsAxis', cik=str(cik)))
            raw = doc(contexts, fact('total', '200') + fact('corp', str(value)))
            row, = parse_revenue(raw, origin, symbol)
            self.assertEqual((row['group'], row['label'], row['value']), ('segment', '본사·기타', value * 1e6))
            self.assertEqual(parse_revenue(raw, origin, 'OTHER'), [])
            self.assertEqual(parse_revenue(raw.replace('CorporateNonSegmentMember', 'EliminationsMember'), origin, symbol), [])

    def test_rin_subset_reclassifies_legacy_cache_once_with_exact_report_scope(self):
        rows = deepcopy(REPORTS['DINO']['revenue_mix'])
        rin = next(r for r in rows if r['group'] == 'revenue_type')
        rin['group'], rin['label'] = 'product', 'Legacy RIN label'
        before = deepcopy(rows)
        old = CompanyKnowledge(symbol='DINO', name='HF Sinclair', revenue_mix=rows)
        new = enrich(old)
        self.assertEqual(len(new.revenue_mix), len(rows))
        self.assertEqual(sum(r.group == 'revenue_type' for r in new.revenue_mix), 1)
        self.assertEqual(new.model_dump(), enrich(new).model_dump())
        self.assertEqual(rows, before)
        for changed in [dict(start='2024-01-01', end='2024-12-31'),
                        dict(source={**rin['source'], 'url':rin['source']['url'].replace('000191565726000016', '000191565727000016')})]:
            self.assertEqual(present_revenue([{**rin, **changed}], 'DINO')[0]['group'], 'product')
        self.assertEqual(present_revenue([rin], 'OTHER')[0]['group'], 'product')

    def test_contract_roles_and_past_changes_remain_explicit(self):
        dino = EDGES['DINO']
        self.assertTrue(any(r['symbol'] == 'CVX' and r['kind'] == 'supplier' for r in dino))
        self.assertTrue(any(r['symbol'] == 'EPD' and '운송사' in r['detail'] for r in dino))
        shell = next(r for r in dino if r['symbol'] == 'SHEL')
        self.assertIn('역사적', shell['detail'])
        self.assertIn('2025년', shell['detail'])
        self.assertFalse(any(r.get('symbol') == 'CVE' for r in EDGES['PSX']))
        text = ' '.join(r['detail'] for r in PUBLIC['DINO']['brief'])
        self.assertIn('완료된 상태로 표시하지 않습니다', text)
        self.assertIn('2027년 하반기', text)


if __name__ == '__main__':
    unittest.main()
