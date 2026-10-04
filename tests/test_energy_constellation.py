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
                         1+sum(n.get('symbol')=='XOM' and n['kind'] in ('factor','product','segment','revenue') for n in nodes.values()))

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

    def test_stored_business_elements_revenue_scope_and_literal_evidence_retrieval(self):
        from cloud_app.constellation_retrieval import search
        root = self.graph.ingest(CompanyKnowledge(symbol='XOM', name='Exxon',
            products=[dict(title='독립 검수 제품', detail='Evidence probe', original='UniqueEvidenceNeedle production', source=SOURCE)],
            revenue_mix=[dict(group='product', member='probe:External', label='외부 공시 항목', value=80,
                total=100, unit='USD', start='2025-01-01', end='2025-12-31', metric='probe:Revenue', source=SOURCE),
                dict(group='segment', member='probe:Internal', label='내부 거래 포함 항목', value=95,
                total=100, includes_intersegment=True, unit='USD', start='2025-01-01', end='2025-12-31', metric='probe:Revenue', source=SOURCE)]), 'us_10')
        result = scene.snapshot(self.settings)
        product = next(n for n in result['nodes'] if n['name']=='독립 검수 제품')
        self.assertEqual(product['original'], 'UniqueEvidenceNeedle production')
        external = next(n for n in result['nodes'] if n['name']=='외부 공시 항목')
        internal = next(n for n in result['nodes'] if n['name']=='내부 거래 포함 항목')
        self.assertEqual(external['measure']['share_pct'],80)
        self.assertIsNone(internal['measure']['share_pct'])
        hits = search(self.settings,'UniqueEvidenceNeedle')
        self.assertEqual(hits['rows'][0]['node_id'],product['id'])
        self.assertEqual(hits['rows'][0]['citation']['url'],SOURCE['url'])
        self.assertTrue(hits['indexed_documents'] > 1000)
        self.assertEqual(search(self.settings,'"UniqueEvidenceNeedle" OR NonexistentTestNeedle --')['rows'],[])
        with self.graph.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM company_profiles WHERE entity_id=?',(root,)).fetchone()[0],1)
            self.assertEqual(db.execute('PRAGMA quick_check').fetchone()[0],'ok')
        self.settings.production=True
        with self.assertRaises(HTTPException) as caught: search(self.settings,'UniqueEvidenceNeedle')
        self.assertEqual(caught.exception.status_code,404)
        from fastapi.testclient import TestClient
        from cloud_app import main
        route = next(r for r in main.app.routes if r.path=='/api/energy-constellation/search')
        self.assertIn(main.current_user, [dep.call for dep in route.dependant.dependencies])
        self.settings.production=False
        overrides=dict(main.app.dependency_overrides)
        def denied():
            raise HTTPException(401, 'Not authenticated')
        try:
            with patch.object(main, 'settings', self.settings):
                client=TestClient(main.app)
                main.app.dependency_overrides[main.current_user]=denied
                self.assertEqual(client.get('/api/energy-constellation/search',params={'q':'UniqueEvidenceNeedle'}).status_code,401)
                main.app.dependency_overrides[main.current_user]=lambda:SimpleNamespace(id='constellation-http-test')
                response=client.get('/api/energy-constellation/search',params={'q':'UniqueEvidenceNeedle'})
                self.assertEqual(response.status_code,200)
                self.assertTrue(response.json()['rows'])
                self.assertEqual(client.get('/api/energy-constellation/search',params={'q':'x'*241}).status_code,422)
        finally:
            main.app.dependency_overrides.clear();main.app.dependency_overrides.update(overrides)


if __name__ == '__main__':
    unittest.main()
