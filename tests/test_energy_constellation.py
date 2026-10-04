"""Offline ecosystem completeness, identity and source boundaries."""
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from cloud_app import energy_constellation as scene
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.company_catalog import enrich

SOURCE = dict(label='Public primary report', url='https://www.sec.gov/test.htm',
              level='primary', as_of='2026-10-01')


class EnergyConstellationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SimpleNamespace(personal_local_mode=True, production=False,
            dataset_dir=Path(self.temp.name)/'runtime/data')
        scene._cached = None
        self.graph = CompanyGraph(self.settings)

    def tearDown(self):
        self.temp.cleanup()
        scene._cached = None

    def test_fresh_pc_contains_roster_catalogue_and_business_elements_without_ingest(self):
        result = scene.snapshot(self.settings)
        self.assertEqual(result['issuer_count'], 213)
        nodes = {n['id']: n for n in result['nodes']}
        self.assertEqual(sum(n['kind']=='issuer' for n in nodes.values()), 213)
        self.assertTrue(any(n['kind']=='company' for n in nodes.values()))
        self.assertTrue(any(n['id'].startswith('drivers:') for n in nodes.values()))
        self.assertTrue(any(n['id'].startswith('segments:') for n in nodes.values()))
        self.assertEqual(sum(n['id'].startswith('factor:') for n in nodes.values()), 8)
        comparisons=[e for e in result['edges'] if '공시 사업 범위를 대조한 비교 대상' in e['detail']]
        self.assertTrue(comparisons)
        self.assertTrue(all(e['analytical'] for e in comparisons))
        for edge in result['edges']:
            self.assertIn(edge['source'], nodes)
            self.assertIn(edge['target'], nodes)
            self.assertTrue(edge['citation']['url'].startswith('https://'))
            self.assertNotIn('wikipedia', edge['citation']['url'])
        with self.graph.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM company_relations').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM company_profiles').fetchone()[0], 0)

    def test_more_than_company_page_cap_exact_identity_and_canonical_direction(self):
        root = self.graph.ingest(CompanyKnowledge(symbol='XOM', name='Exxon'), 'us_10')
        for i in range(501):
            self.graph.ingest(CompanyKnowledge(name=f'Target {i}', symbol=f'ZZ{i}', relations=[
                dict(name='Exxon', symbol='XOM', kind='customer', detail=f'Supply {i}', source=SOURCE)]), 'us_10')
        other = self.graph.ingest(CompanyKnowledge(symbol='OUTSIDE', name='Other sector',
            relations=[dict(name='Unrelated', symbol='UNRELATED', kind='customer', source=SOURCE)]), 'us_45')
        result = scene.snapshot(self.settings)
        nodes = {n['id']: n for n in result['nodes']}
        self.assertEqual(sum(n.get('symbol','').startswith('ZZ') for n in nodes.values() if n.get('symbol')), 501)
        self.assertNotIn(other, nodes)
        self.assertEqual(result['stored_claim_records'], 501)
        edges = [e for e in result['edges'] if e['detail'].startswith('Supply ')]
        self.assertEqual(len(edges), 501)
        self.assertTrue(all(e['target']==root and e['kind']=='customer' for e in edges))
        self.assertEqual(sum(n.get('symbol')=='XOM' for n in nodes.values()),
                         1+sum(n.get('symbol')=='XOM' and n['kind'] in ('factor','product') for n in nodes.values()))

    def test_cache_copies_and_invalidates_on_graph_change_and_fails_closed_at_limit(self):
        first = scene.snapshot(self.settings)
        first['nodes'].clear()
        self.assertTrue(scene.snapshot(self.settings)['nodes'])
        self.graph.ingest(CompanyKnowledge(symbol='XOM', name='Exxon', relations=[
            dict(name='New public neighbour', symbol='ZZNEW', kind='partner', source=SOURCE)]), 'us_10')
        self.assertTrue(any(n.get('symbol')=='ZZNEW' for n in scene.snapshot(self.settings)['nodes']))
        scene._cached = None
        with patch.object(scene, 'MAX_NODES', 2), self.assertRaises(HTTPException) as caught:
            scene.snapshot(self.settings)
        self.assertEqual(caught.exception.status_code, 413)
        for personal, production in [(False,False),(True,True)]:
            self.settings.personal_local_mode=personal; self.settings.production=production
            with self.assertRaises(HTTPException) as caught:
                scene.snapshot(self.settings)
            self.assertEqual(caught.exception.status_code, 404)

    def test_bounded_followup_preserves_reported_revenue_and_anonymous_customer_scope(self):
        liberty = enrich(CompanyKnowledge(symbol='LBRT', name='Liberty'))
        rows = [r for r in liberty.revenue_mix if r.member in ('reported:NonrelatedRevenue','reported:RelatedRevenue')]
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r.value for r in rows), 4006116000)
        self.assertTrue(all(r.share_exclusion and r.group=='revenue_type' for r in rows))
        eu = enrich(CompanyKnowledge(symbol='EU', name='enCore'))
        self.assertTrue(any('43,155,000' in f.detail and '네 번째 고객' in f.detail for f in eu.financial_context))


if __name__ == '__main__':
    unittest.main()
