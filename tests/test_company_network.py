"""Two-hop exploration stays bounded, authenticated and source-backed offline."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from fastapi import HTTPException
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.company_network import network_snapshot

SRC = dict(label='Synthetic issuer filing',url='https://www.sec.gov/report.htm',as_of='2025-12-31',level='primary')


class CompanyNetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.settings=SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(self.temp.name)/'runtime/data')
        self.graph=CompanyGraph(self.settings)
        self.graph.ingest(CompanyKnowledge(symbol='AAA',name='Root',relations=[dict(name='Middle',symbol='BBB',kind='supplier',detail='첫 단계 제조 공급',source=SRC)]))
        self.graph.ingest(CompanyKnowledge(symbol='BBB',name='Middle',brief=[dict(title='사업',detail='전자 부품 제조와 판매',source=SRC)],relations=[
            *[dict(name=f'Leaf {i:02}',symbol=f'L{i:02}',kind='partner' if i%2 else 'supplier',detail=f'명시된 사업 관계 {i}',source=SRC) for i in range(19)],
            dict(name='Owner',symbol='OWN',kind='owner',detail='소유 관계',source=SRC)]))
        self.root=self.graph.by_symbol('AAA')['id'];self.via=self.graph.by_symbol('BBB')['id']

    def tearDown(self):self.temp.cleanup()

    def test_pagination_filters_and_no_invented_direct_edge(self):
        first=network_snapshot(self.settings,self.root,self.via)
        self.assertEqual(first['total'],19);self.assertEqual(first['pages'],3);self.assertEqual(len(first['rows']),8)
        self.assertEqual(first['counts']['supplier'],10);self.assertEqual(first['counts']['partner'],9)
        self.assertEqual(first['via']['brief'][0]['detail'],'전자 부품 제조와 판매')
        last=network_snapshot(self.settings,self.root,self.via,50)
        self.assertEqual(last['page'],3);self.assertEqual(len(last['rows']),3)
        self.assertEqual(len({r['target_id'] for page in range(1,4) for r in network_snapshot(self.settings,self.root,self.via,page)['rows']}),19)
        only=network_snapshot(self.settings,self.root,self.via,kind='partner')
        self.assertEqual(only['total'],9);self.assertTrue(all(r['kind']=='partner' for r in only['rows']))
        self.assertTrue(all(r['target_id']!=self.root for r in first['rows']))
        self.assertEqual(len(self.graph.relations(self.root)),1)
        self.assertEqual(first['direct'][0]['detail'],'첫 단계 제조 공급')

    def test_reverse_claim_retains_issuer_and_empty_extra_network(self):
        result=network_snapshot(self.settings,self.via,self.root)
        self.assertEqual(result['direct'][0]['kind'],'customer')
        self.assertEqual(result['direct'][0]['reported_by'],'Root')
        self.assertTrue(result['direct'][0]['reverse']);self.assertEqual(result['total'],0)
        self.assertEqual(result['rows'],[]);self.assertEqual(result['pages'],1)

    def test_unknown_unrelated_and_nonpersonal_are_rejected(self):
        unrelated=self.graph.by_symbol('L01')['id']
        for key,via in [(self.root,unrelated),(self.root,'../env'),('c_'+'0'*32,self.via)]:
            with self.assertRaises(HTTPException):network_snapshot(self.settings,key,via)
        for page,kind in [(0,'all'),(51,'all'),(True,'all'),(1,'owner')]:
            with self.assertRaises(ValueError):network_snapshot(self.settings,self.root,self.via,page,kind)
        self.settings.personal_local_mode=False
        with self.assertRaises(HTTPException):network_snapshot(self.settings,self.root,self.via)

    def test_evidence_payload_is_bounded_but_count_preserved(self):
        self.graph.ingest(CompanyKnowledge(symbol='BBB',name='Middle',relations=[dict(name='Leaf',symbol='L00',kind='supplier',detail=f'관계 증거 {i}',source=SRC) for i in range(20)]))
        row=network_snapshot(self.settings,self.root,self.via)['rows'][0]
        self.assertEqual(row['evidence_total'],20);self.assertEqual(len(row['evidence']),10)

    def test_ownership_statements_cannot_crowd_out_business_before_limit(self):
        for index in range(5):
            self.graph.ingest(CompanyKnowledge(symbol=f'O{index}',name=f'Owner {index}',relations=[
                dict(name='Root',symbol='AAA',kind='subsidiary',detail=f'Subsidiary claim {item}',source=SRC) for item in range(100)]))
        with self.graph.connection() as db:
            db.execute("UPDATE company_relations SET observed_at=CASE WHEN kind='subsidiary' THEN '2026-10-01' ELSE '2020-01-01' END")
        rows=self.graph.relations(self.root)
        self.assertTrue(any(row['target_id']==self.via and row['kind']=='supplier' for row in rows))
        self.assertLessEqual(sum(len(row['evidence']) for row in rows),400)
