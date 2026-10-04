"""Offline semantic index lifecycle, source grounding and API boundaries."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from fastapi import HTTPException
from cloud_app import constellation_semantics as semantic, constellation_index as index
from cloud_app import constellation_embeddings as embeddings
from cloud_app.company_graph import CompanyGraph

SOURCE=dict(label='Primary LNG report',url='https://www.sec.gov/test.htm',level='primary')
ROOT='c_'+'a'*32
OTHER='c_'+'b'*32


def vector(a,b=0):
    value=np.zeros(embeddings.DIMENSIONS,dtype='<f4');value[:2]=a,b
    return value/np.linalg.norm(value)


class FakeEncoder:
    calls=0
    def chunks(self,text):return [text]
    def encode(self,texts):
        self.calls+=1
        return np.asarray([vector(0,1) if 'coal' in t else vector(1,.05) if 'Similar' in t else vector(1) for t in texts])


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.settings=SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(self.temp.name)/'runtime/data')
        self.public=CompanyGraph(self.settings)
        self.graph=dict(focus_id=ROOT,nodes=[
            dict(id=ROOT,name='LNG issuer',kind='issuer',sources=[SOURCE]),
            dict(id='p',semantic_id=ROOT+':products:0',name='LNG carrier',kind='product',sources=[SOURCE]),
            dict(id='q',semantic_id=OTHER+':products:0',name='Similar gas ship',kind='product',sources=[SOURCE]),
            dict(id='coal',name='coal business',kind='product',sources=[SOURCE]),
            dict(id=OTHER,name='Supplier',kind='company',sources=[SOURCE]),
            dict(id='factor:oil',name='Oil price',kind='factor',sources=[SOURCE]),
            dict(id='r',name='Gas revenue',kind='revenue',latest=True,sources=[SOURCE],measure=dict(group='product',value=80,total=100,share_pct=80))],edges=[
            dict(id='supplier',source=OTHER,target=ROOT,kind='supplier',analytical=False,detail='Reported LNG supply',citation=SOURCE),
            dict(id='business',source=ROOT,target='p',kind='business_scope',analytical=True,detail='Reported business scope',citation=SOURCE),
            dict(id='factor',source='p',target='factor:oil',kind='classification',analytical=True,detail='Common oil exposure',citation=SOURCE),
            dict(id='revenue',source=ROOT,target='r',kind='revenue',analytical=False,detail='Reported sales',citation=SOURCE)])
        self.documents=[(n['id'],n['id'],'',n['name'],n['name']+' public description',json.dumps(SOURCE)) for n in self.graph['nodes']]
        self.fingerprint='first'
        self.fake=FakeEncoder()
        self.patches=[patch.object(index,'corpus',side_effect=self.corpus),patch.object(semantic,'corpus',side_effect=self.corpus),patch.object(index,'encoder',return_value=self.fake),patch.object(semantic,'query_vector',return_value=vector(1))]
        for p in self.patches:p.start()
        semantic._cache=None

    def corpus(self,settings):return deepcopy(self.graph),list(self.documents),self.fingerprint
    def prepare(self):return index.prepare(self.settings,batch_size=2,progress=lambda *a,**k:None)
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        semantic._cache=None;self.temp.cleanup()

    def test_semantic_ranking_canonical_company_scope_citations_and_no_new_claims(self):
        result=self.prepare();self.assertEqual(result['nodes'],7)
        hits=semantic.search(self.settings,'액화한 가스 운송')['rows']
        self.assertNotIn('coal',[h['node_id'] for h in hits]);self.assertTrue(hits)
        self.assertTrue(all(h['citation']==SOURCE for h in hits))
        scoped=semantic.search(self.settings,'운송',ROOT)['rows']
        self.assertIn(ROOT+':products:0',[h['node_id'] for h in scoped]);self.assertNotIn('q',[h['node_id'] for h in scoped])
        with self.assertRaises(HTTPException) as caught:semantic.search(self.settings,'gas','unknown')
        self.assertEqual(caught.exception.status_code,404)
        graph=semantic.decorate(self.settings,deepcopy(self.graph))
        self.assertEqual(graph['semantic_status'],'ready');self.assertEqual(len(graph['nodes']),7)
        self.assertTrue(all(len(n['semantic']['position'])==3 for n in graph['nodes']))
        original=deepcopy(self.graph)
        analysis=semantic.analysis(self.settings,ROOT,'product',True)
        self.assertEqual(analysis['confirmed'][0]['citation'],SOURCE)
        self.assertEqual(analysis['confirmed'][0]['node_id'],OTHER)
        self.assertEqual(analysis['revenue'][0]['measure']['share_pct'],80)
        self.assertTrue(analysis['paths'][0]['steps'][-1]['analytical'])
        similar=semantic.analysis(self.settings,ROOT+':products:0',company=True)['similar']
        self.assertEqual(similar[0]['node_id'],'q');self.assertEqual(similar[0]['company_id'],OTHER)
        self.assertEqual(self.graph,original)
        with self.public.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM company_relations').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM company_profiles').fetchone()[0],0)

    def test_resumable_vectors_atomic_activation_and_stale_corpus(self):
        first=self.prepare();calls=self.fake.calls
        second=self.prepare();self.assertEqual(second['new_vectors'],0);self.assertEqual(self.fake.calls,calls)
        self.assertEqual(first['generation'],second['generation'])
        self.fingerprint='new';self.documents.append(('new','p','','New LNG evidence','Changed source text',json.dumps(SOURCE)))
        with patch.object(self.fake,'encode',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError):self.prepare()
        with self.public.connection() as db:
            self.assertEqual(db.execute('SELECT generation FROM cosmos_semantic_meta').fetchone()[0],first['generation'])
        with self.assertRaises(HTTPException) as caught:semantic.analysis(self.settings,ROOT)
        self.assertEqual(caught.exception.status_code,503)
        self.prepare();self.assertTrue(semantic.search(self.settings,'gas')['rows'])

    def test_corrupted_vector_and_missing_model_fail_closed(self):
        self.prepare()
        with self.public.connection() as db:db.execute("UPDATE cosmos_semantic_vectors SET vector=?",(b'broken',))
        semantic._cache=None
        with self.assertRaises(HTTPException) as caught:semantic.search(self.settings,'gas')
        self.assertEqual(caught.exception.status_code,503)
        with self.assertRaises(ValueError):embeddings.verify(Path(self.temp.name)/'missing')
        for personal,production in [(False,False),(True,True)]:
            self.settings.personal_local_mode=personal;self.settings.production=production
            with self.assertRaises(ValueError):embeddings.model_directory(self.settings)
        self.settings.personal_local_mode=True;self.settings.production=False
        with patch.object(embeddings.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps([0]*384))):
            with self.assertRaises(ValueError):embeddings.query_vector(self.settings,'gas')

    def test_chunk_offsets_cover_full_source_and_restore_tokenizer_limits(self):
        from tokenizers import Tokenizer,models,pre_tokenizers
        import threading
        enc=embeddings.Encoder.__new__(embeddings.Encoder)
        enc.lock=threading.Lock();enc.tokenizer=Tokenizer(models.WordLevel({'[UNK]':0,'<pad>':1},unk_token='[UNK]'))
        enc.tokenizer.pre_tokenizer=pre_tokenizers.Whitespace()
        text=' '.join('word'+str(i) for i in range(800))
        pieces=enc.chunks(text)
        self.assertGreater(len(pieces),4);self.assertTrue(pieces[-1].endswith('word799'))
        self.assertTrue(all('word'+str(i) in ' '.join(pieces).split() for i in range(800)))
        self.assertTrue(all(piece in text for piece in pieces))
        self.assertEqual(enc.tokenizer.truncation['max_length'],256)
        self.assertEqual(len(enc.chunks(' '.join('word'+str(i) for i in range(337)))),2)

    def test_topic_reranking_and_company_search_exclude_neighbour_other_edges(self):
        from cloud_app import constellation_retrieval as lexical
        self.graph['nodes'].append(dict(id='uranium',name='Uranium fuel',kind='product',sources=[SOURCE]))
        self.documents.append(('uranium','uranium','','Uranium fuel','Nuclear production',json.dumps(SOURCE)))
        self.graph['edges'].append(dict(id='unrelated',source=OTHER,target='coal',kind='supplier',analytical=False,detail='Other coal contract',citation=SOURCE))
        self.documents.append(('edge:unrelated',OTHER,'unrelated','Unrelated coal contract','UniqueOutsideNeedle',json.dumps(SOURCE)))
        self.documents.append(('edge:supplier',OTHER,'supplier','LNG supply','UniqueInsideNeedle',json.dumps(SOURCE)))
        self.prepare()
        self.assertEqual(semantic.search(self.settings,'원자력 연료')['rows'][0]['node_id'],'uranium')
        self.assertNotIn('unrelated',[r['edge_id'] for r in semantic.search(self.settings,'gas',ROOT)['rows']])
        with patch.object(lexical,'corpus',side_effect=self.corpus):
            self.assertFalse(lexical.search(self.settings,'UniqueOutsideNeedle',ROOT)['rows'])
            self.assertTrue(lexical.search(self.settings,'UniqueInsideNeedle',ROOT)['rows'])

    def test_authenticated_routes_validate_scope_mode_and_offline_readiness(self):
        from fastapi.testclient import TestClient
        from cloud_app import main
        previous=dict(main.app.dependency_overrides)
        try:
            def denied():raise HTTPException(401,'Authentication required')
            with patch.object(main,'settings',self.settings):
                client=TestClient(main.app);main.app.dependency_overrides[main.current_user]=denied
                for endpoint in ('search?q=gas&mode=semantic','analysis?node_id='+ROOT):
                    self.assertEqual(client.get('/api/energy-constellation/'+endpoint).status_code,401)
                main.app.dependency_overrides[main.current_user]=lambda:SimpleNamespace(id='semantic-test-user')
                self.assertEqual(client.get('/api/energy-constellation/search?q=gas&mode=semantic').status_code,503)
                self.prepare()
                self.assertEqual(client.get('/api/energy-constellation/search?q=gas&mode=semantic').status_code,200)
                self.assertEqual(client.get('/api/energy-constellation/search?q=gas&mode=sql').status_code,422)
                self.assertEqual(client.get('/api/energy-constellation/analysis?node_id='+ROOT+'&basis=stock_price').status_code,422)
                self.assertEqual(client.get('/api/energy-constellation/analysis?node_id=missing').status_code,404)
        finally:
            main.app.dependency_overrides.clear();main.app.dependency_overrides.update(previous)
