"""Primary research cleanup, migration and navigation without network access."""
import json
import datetime as dt
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cloud_app.company_catalog import enrich
from cloud_app.company_entities import seed_research, entity_snapshot
from cloud_app.company_graph import CompanyGraph, SCHEMA
from cloud_app.company_provenance import forbidden
from cloud_app.company_research_catalog import PRIVATE_COMPANIES, PUBLIC_COMPANIES
from cloud_app.company_schemas import CompanyKnowledge, Source, Relation

SEC = dict(label='SEC', url='https://www.sec.gov/Archives/edgar/data/1/000000000126000001/a.htm', level='primary')
WIKI = dict(label='Wikipedia', url='https://en.wikipedia.org/wiki/Test', level='primary')


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SimpleNamespace(personal_local_mode=True, production=False,
            dataset_dir=Path(self.temp.name) / 'runtime/personal-data')
        self.graph = CompanyGraph(self.settings)

    def tearDown(self):
        self.temp.cleanup()

    def test_host_and_grade_filters_cannot_be_relabelled_as_primary(self):
        for host in ['en.wikipedia.org', 'ko.wikipedia.org', 'www.wikidata.org', 'commons.wikimedia.org', 'en.wikipedia.org.']:
            self.assertTrue(forbidden(dict(label='Official', url='https://' + host, level='primary')))
        self.assertTrue(forbidden(dict(label='Not wiki', url='https://example.test', level='encyclopedia')))
        self.assertFalse(forbidden(SEC))

    def test_reading_seed_preserves_newer_database_evidence_than_json(self):
        now = dt.datetime.now(dt.timezone.utc)
        fresh = CompanyKnowledge(symbol='NVDA', name='NVIDIA', attempted_at=now,
            products=[dict(title='New verified record', detail='New detail', source=SEC)])
        key = self.graph.ingest(fresh)
        older = CompanyKnowledge(symbol='NVDA', name='NVIDIA', attempted_at=now-dt.timedelta(days=1))
        from cloud_app.company_service import root, read_company
        (root(self.settings) / 'NVDA.json').write_text(older.model_dump_json())
        self.assertEqual(read_company(self.settings, 'NVDA').attempted_at, now)
        with patch('cloud_app.company_service.related_directory', return_value={}):
            seed_research(self.settings)
        stored = self.graph.entity(key)['profile']
        self.assertEqual(stored['attempted_at'], fresh.model_dump(mode='json')['attempted_at'])
        self.assertTrue(any(row['title'] == 'New verified record' for row in stored['products']))

    def test_model_instance_revalidation_blocks_injected_encyclopedia_edges(self):
        value = CompanyKnowledge(symbol='TEST', name='Test')
        value.relations.append(Relation(name='Untrusted', kind='supplier', source=Source(**WIKI)))
        key = self.graph.ingest(value)
        self.assertEqual(self.graph.relations(key), [])
        self.assertEqual(self.graph.entity(key)['sources'], [])

    def test_v1_transaction_removes_all_wiki_knowledge_preserves_ids_and_originals(self):
        key, target = 'c_' + '1' * 32, 'c_' + '2' * 32
        old_schema = SCHEMA.replace(",\n original TEXT NOT NULL DEFAULT ''", '').replace('user_version=2', 'user_version=1')
        raw = dict(name='Test', symbol='TEST', entity_id='Q123', description='Old wiki summary',
            description_source=WIKI, sources=[WIKI, SEC],
            products=[dict(title='Wiki product', detail='Old', source=WIKI)],
            relations=[dict(name='Verified', symbol='OTHER', kind='supplier',
                detail='공시 공급 · 규칙으로 추출한 원문: We purchase from Other Corporation.', source=SEC)])
        with sqlite3.connect(self.graph.path) as db:
            db.executescript(old_schema)
            db.executemany('INSERT INTO company_entities VALUES(?,?,?,?)', [(key,'Test',None,None),(target,'Verified',None,None)])
            db.executemany('INSERT INTO company_aliases VALUES(?,?,?)', [('ticker','TEST',key),('wikidata','Q123',key),('ticker','OTHER',target)])
            db.executemany('INSERT INTO company_sources VALUES(?,?,?,?,?)', [('wiki','Wikipedia',WIKI['url'],None,'primary'), ('sec','SEC',SEC['url'],None,'primary')])
            db.executemany('INSERT INTO company_entity_sources VALUES(?,?)', [(key,'wiki'),(key,'sec'),(target,'sec')])
            db.execute('INSERT INTO company_profiles VALUES(?,?,?)', (key,json.dumps(raw),'old'))
            db.executemany('INSERT INTO company_relations VALUES(?,?,?,?,?,?,?,?)', [
                ('wiki-edge',key,key,target,'supplier','Untrusted','wiki',None),
                ('sec-edge',key,key,target,'supplier',raw['relations'][0]['detail'],'sec',None)])
        page = self.graph.entity(key)
        self.assertEqual(page['entity_id'], 'Q123')
        self.assertEqual(page['profile']['description'], '')
        self.assertEqual(page['profile']['products'], [])
        edges = self.graph.relations(key)
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]['target_id'], target)
        self.assertEqual(edges[0]['original'], 'We purchase from Other Corporation.')
        self.graph.remove_encyclopedia()
        with self.graph.connection() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM company_sources').fetchone()[0], 1)
            self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())

    def test_all_curated_profiles_and_relations_validate_without_wiki(self):
        for symbol in PUBLIC_COMPANIES:
            value = enrich(CompanyKnowledge(symbol=symbol, name=symbol))
            self.assertTrue(value.brief)
            self.assertTrue(value.description_source)
            self.assertFalse(any(forbidden(row) for row in value.sources))
            for edge in value.relations:
                self.assertFalse(forbidden(edge.source))
        self.assertGreaterEqual(len(PUBLIC_COMPANIES), 13)
        self.assertGreaterEqual(len(PRIVATE_COMPANIES), 18)

    def test_enrichment_is_idempotent_and_keeps_independent_evidence(self):
        old = CompanyKnowledge(symbol='MCD', name='McDonald’s', relations=[
            dict(name='Another supplier', kind='supplier', detail='Official evidence', source=SEC)])
        first = enrich(old)
        self.assertEqual(first.model_dump(), enrich(first).model_dump())
        self.assertTrue(any(row.name == 'Another supplier' for row in first.relations))
        self.assertTrue(any(row.registry_id == 'lopez-foods' for row in first.relations))
        for symbol in ['MSFT', 'NVDA', 'AAPL', 'TSM']:
            value = enrich(CompanyKnowledge(symbol=symbol, name=symbol))
            self.assertEqual(value.model_dump(), enrich(value).model_dump())

    def test_registry_pages_are_source_backed_clickable_and_business_edges_reverse(self):
        with patch('socket.create_connection', side_effect=AssertionError('Network forbidden')):
            seed_research(self.settings)
            owner = self.graph.by_symbol('MCD')
            target = next(row for row in self.graph.relations(owner['id']) if row['name'] == 'Lopez Foods')
            page = entity_snapshot(self.settings, target['target_id'])
        self.assertEqual(page['registry_id'], 'lopez-foods')
        self.assertTrue(page['brief'])
        self.assertFalse(page['collectable'])
        self.assertTrue(any(row['target_id'] == owner['id'] and row['kind'] == 'customer' for row in page['relations']))

    def test_ambiguous_parent_names_do_not_acquire_guessed_tickers(self):
        from cloud_app.company_filings import named
        self.assertEqual(named('Samsung and Merck are mentioned.', 'TEST'), [])
        self.assertIn(('Samsung Electronics','005930.KS'), named('Samsung Electronics supplies products.', 'TEST'))

    def test_semiconductor_suppliers_have_exact_identities_and_separate_business_evidence(self):
        from cloud_app.company_context import business_context
        from cloud_app.company_semiconductor_catalog import SAMSUNG_LIST, SAMSUNG_SUPPLIERS
        with patch('socket.create_connection', side_effect=AssertionError('Network forbidden')):
            seed_research(self.settings)
            samsung = self.graph.by_symbol('005930.KS')
            rows = self.graph.relations(samsung['id'])
        listed = [row for row in rows if row['kind'] == 'supplier' and any(
            item['source']['url'] == SAMSUNG_LIST['url'] for item in row['evidence'])]
        self.assertEqual(len(listed), len(SAMSUNG_SUPPLIERS))
        self.assertEqual(len(listed), 37)
        self.assertTrue(all(row['business'] for row in listed))
        self.assertTrue(all(row['business']['source']['url'] != SAMSUNG_LIST['url'] for row in listed))
        self.assertIn('232140.KQ', {row['symbol'] for row in listed})
        self.assertNotIn('112290.KQ', {row['symbol'] for row in listed})
        operating = next(row for row in listed if row['name'] == 'ASML Netherlands B.V.')
        self.assertIsNone(operating['symbol'])
        self.assertNotEqual(operating['target_id'], self.graph.by_symbol('ASML')['id'])
        wonik = next(row for row in listed if row['symbol'] == '240810.KQ')
        self.assertIn('증착', wonik['business']['detail'])
        self.assertTrue(any(row['kind'] == 'customer' and row['target_id'] == samsung['id']
                            for row in self.graph.relations(wonik['target_id'])))
        context = business_context(registry='kyec')
        context['source']['url'] = 'https://example.test/modified'
        self.assertNotEqual(context, business_context(registry='kyec'))
        self.assertIsNone(business_context(registry='not-a-reviewed-identity'))


if __name__ == '__main__':
    unittest.main()
