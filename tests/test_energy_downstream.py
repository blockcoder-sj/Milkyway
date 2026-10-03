"""Edited downstream facts, fiscal scopes and named counterpart navigation."""
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_downstream import PUBLIC, PRIVATE, EDGES, SYMBOLS
from cloud_app.company_energy_downstream_revenue import DOCUMENTS, PERIODS
from cloud_app.company_energy_financial_archive import archive
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer


class DownstreamResearchTests(unittest.TestCase):
    def test_seventeen_primary_edited_profiles_do_not_replace_earlier_refiners(self):
        self.assertEqual(set(PUBLIC),set(SYMBOLS))
        self.assertEqual(len(PUBLIC),17)
        for symbol,profile in PUBLIC.items():
            with self.subTest(symbol=symbol):
                value=enrich(CompanyKnowledge(symbol=symbol,**profile))
                self.assertGreaterEqual(len(value.brief),6)
                self.assertGreaterEqual(len(value.products),6)
                self.assertTrue(value.drivers and value.financials and value.financial_context and value.relations)
                self.assertEqual(value.model_dump(),enrich(value).model_dump())
                self.assertTrue(all(r.source.level=='primary' and r.detail and not r.original
                                    for r in value.brief+value.products+value.drivers))
                self.assertNotIn('wikipedia',str(value.model_dump()).lower())
                self.assertNotEqual(issuer(symbol).group,'pending')
        for symbol in ('MPC','PSX','DINO'):
            self.assertEqual(len(enrichment(symbol)['brief']),8)
            self.assertTrue(enrichment(symbol)['relations'])
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)

    def test_annual_receipts_fiscal_dates_and_reported_cash_are_exact(self):
        for symbol in SYMBOLS:
            record=archive()[symbol]
            cik=int(record['cik'])
            self.assertEqual(record['annual']['url'],DOCUMENTS[symbol,cik])
            self.assertEqual(record['annual']['sha256'],REPORTS[symbol]['annual']['sha256'])
            for row in record['financials']:
                self.assertEqual(row['period'].split(' ~ ')[-1],PERIODS[symbol,cik][1])
                self.assertEqual(row['unit'],'USD')
            self.assertTrue(record['financial_context'])
        cash,=[r for r in archive()['SGU']['financials'] if r['label']=='현금·현금성 자산']
        self.assertEqual(cash['value'],24683000)
        self.assertIn('2024-09-29',str(PUBLIC['SPH']['brief']))
        self.assertEqual(PERIODS['REX',744187],('2025-02-01','2026-01-31'))

    def test_reported_external_and_partial_views_keep_their_own_basis(self):
        expected={
            'DK':('segment',10722900000),'DKL':('segment',1013323000),
            'PBF':('product',29297700000),'PARR':('product',7464650000),
            'CVI':('segment',7162000000),'CLMT':('segment',4137100000),
            'GLP':('segment',18561421000),'CAPL':('segment',3662534000),
            'SGU':('product',1784418000),'SPH':('product',1432518000),
            'MMLP':('segment',716113000),'NGL':('segment',3156159000),
            'GEL':('segment',1630415000),'WKC':('geography',36916600000),
            'GPRE':('segment',2091680000),'REX':('product',650741000),
            'GEVO':('product',160580000)}
        for symbol,(group,total) in expected.items():
            rows=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
            with self.subTest(symbol=symbol):
                self.assertEqual(sum(r['value'] for r in rows if r['group']==group),total)
                self.assertTrue(all(r['label'] and r['source']['level']=='primary' for r in rows))
        for symbol,total in [('DKL',797435000),('GLP',8713114000),('CAPL',3599988000)]:
            rows=[r for r in REPORTS[symbol]['revenue_mix'] if r['group']=='product']
            self.assertEqual(sum(r['value'] for r in rows),total)
            self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in rows))
        self.assertEqual(sum(r['value'] for r in REPORTS['SPH']['revenue_mix'] if r['group']=='end_market'),1432518000)
        self.assertEqual(sum(r['value'] for r in REPORTS['WKC']['revenue_mix'] if r['group']=='segment'),36916700000)
        self.assertTrue(all(r['total'] is None for r in REPORTS['WKC']['revenue_mix'] if r['group']=='segment'))
        rex=REPORTS['REX']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in rex),650487000)
        self.assertEqual([r['value'] for r in rex if r['value']<0],[-254000])
        self.assertFalse(any(r['group']=='product' for r in REPORTS['GPRE']['revenue_mix']))

    def test_named_roles_and_pending_projects_keep_their_actual_stage(self):
        self.assertTrue(any(r['symbol']=='HPK' and r['kind']=='supplier' for r in EDGES['DK']))
        self.assertTrue(any(r['registry_id']=='bp-oil-supply' and r['kind']=='supplier' for r in EDGES['CLMT']))
        self.assertTrue(any(r['symbol']=='SUN' and r['kind']=='customer' for r in EDGES['PBF']))
        self.assertTrue(any(r['registry_id']=='cargill' and r['kind']=='partner' for r in EDGES['SGU']))
        self.assertFalse(any(r['registry_id']=='cargill' and r['kind']=='supplier' for r in EDGES['SGU']))
        self.assertIn('만료',str(PUBLIC['DKL']['products']))
        self.assertIn('2027-10-01',str(PUBLIC['DKL']['brief']))
        self.assertIn('승인이 남은',str(PUBLIC['PARR']['brief']))
        self.assertIn('19%',str(PUBLIC['SPH']['brief']))
        self.assertIn('38%',str(PUBLIC['SPH']['brief']))
        self.assertIn('의견 수렴',str(PUBLIC['REX']['brief']))
        self.assertIn('현재 실적으로 표시하지',str(PUBLIC['GEVO']['brief']))
        self.assertFalse(any(r['kind']=='subsidiary' and r['name'] in {'Royal Purple','Bel-Ray','TruFuel'}
                             for r in EDGES['CLMT']))

    def test_reviewed_revenue_reaches_an_empty_cached_company_response(self):
        fields = ('group','member','value','metric','start','end')
        for symbol in SYMBOLS:
            with self.subTest(symbol=symbol):
                value = enrich(CompanyKnowledge(symbol=symbol,name=symbol))
                expected = present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
                self.assertTrue(value.revenue_mix)
                self.assertEqual([tuple(r.model_dump()[k] for k in fields) for r in value.revenue_mix],
                                 [tuple(r[k] for k in fields) for r in expected])
                self.assertEqual(value.model_dump(),enrich(value).model_dump())

    def test_counterparts_are_clickable_and_reverse_roles_preserve_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,
                dataset_dir=Path(temp)/'data'))
            for symbol in SYMBOLS:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in PRIVATE:
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol,registry,kind,reverse in [
                ('CLMT','bp-oil-supply','supplier','customer'),
                ('SPH','adirondack-farms-rng','supplier','customer'),
                ('MMLP','martin-resource-management','customer','supplier'),
                ('NGL','hydrosource-logistics','customer','supplier'),
                ('GEL','llog-exploration','customer','supplier'),
                ('GPRE','tallgrass-high-plains-carbon','supplier','customer'),
                ('WKC','jetblue-world-fuel','customer','supplier'),
                ('GEVO','quill-financial-gevo','customer','supplier')]:
                root=graph.by_symbol(symbol)
                edge=next(r for r in graph.relations(root['id']) if r['kind']==kind
                    and graph.entity(r['target_id'])['registry_id']==registry)
                target=graph.entity(edge['target_id'])
                self.assertTrue(target['profile']['brief'])
                back=next(r for r in graph.relations(target['id']) if r['target_id']==root['id'] and r['kind']==reverse)
                self.assertEqual(back['source'],edge['source'])
                if symbol=='WKC':
                    self.assertEqual(target['symbols'],['JBLU'])
                    self.assertEqual(graph.by_symbol('JBLU')['id'],target['id'])

    def test_legacy_metric_and_subtotal_cache_cannot_reenter_reviewed_views(self):
        rows=deepcopy(REPORTS['GLP']['revenue_mix'])
        contract=next(r for r in rows if r['group']=='product')
        wrong={**deepcopy(contract),'group':'segment','member':'glp:WholesaleSegmentMember',
               'value':3210899000,'metric':'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'}
        self.assertEqual(present_revenue(rows+[wrong],'GLP'),rows)
        newer={**wrong,'source':{**wrong['source'],'url':wrong['source']['url'].replace('glp-20251231','other')}}
        self.assertEqual(len(present_revenue(rows+[newer],'GLP')),len(rows)+1)
        subtotal={**deepcopy(REPORTS['REX']['revenue_mix'][0]),'group':'segment',
                  'member':'rex:EthanolAndByProductsMember','value':1658393000}
        self.assertEqual(present_revenue([subtotal],'REX'),[])
