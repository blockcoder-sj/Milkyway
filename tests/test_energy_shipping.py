"""Reviewed maritime business scopes, actual counterpart roles and navigation."""
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_shipping import PUBLIC, PRIVATE, EDGES, SYMBOLS
from cloud_app.company_energy_shipping_revenue import DOCUMENTS, PERIODS
from cloud_app.company_energy_financial_archive import archive
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import present_revenue
from cloud_app.company_schemas import CompanyKnowledge, RevenueLine
from cloud_app.energy_issuers import issuer, registry


class ShippingResearchTests(unittest.TestCase):
    def test_all_sixteen_have_edited_business_products_drivers_and_actual_financials(self):
        self.assertEqual(set(PUBLIC),set(SYMBOLS))
        self.assertEqual(len(PUBLIC),16)
        self.assertEqual(len(registry().rows),213)
        for symbol,profile in PUBLIC.items():
            with self.subTest(symbol=symbol):
                value=enrich(CompanyKnowledge(symbol=symbol,**profile))
                self.assertGreaterEqual(len(value.brief),6)
                self.assertGreaterEqual(len(value.products),6)
                self.assertTrue(value.segments and value.drivers and value.relations)
                self.assertTrue(value.financials and value.financial_context)
                self.assertEqual(value.model_dump(),enrich(value).model_dump())
                self.assertTrue(all(r.detail and r.source.level=='primary' and not r.original
                    for r in value.brief+value.products+value.segments+value.drivers))
                self.assertNotIn('wikipedia',str(value.model_dump()).lower())
                self.assertEqual(issuer(symbol).group,'shipping')
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)
        for symbol in ('MPC','PSX','DINO','WKC','GPRE','GEVO'):
            self.assertTrue(enrichment(symbol)['brief'])

    def test_fiscal_identity_receipts_and_added_statement_values(self):
        for symbol in SYMBOLS:
            record=archive()[symbol]; cik=int(record['cik'])
            self.assertEqual(record['annual']['url'],DOCUMENTS[symbol,cik])
            self.assertEqual(record['annual']['sha256'],REPORTS[symbol]['annual']['sha256'])
            for row in record['financials']:
                self.assertEqual(row['period'].split(' ~ ')[-1],PERIODS[symbol,cik][1])
        for symbol,label,value in [
                ('FRO','현금·현금성 자산',251347000),
                ('GLNG','현금·현금성 자산',1151221000),
                ('STNG','현금·현금성 자산',751955000),
                ('TORO','계속사업 영업활동 현금흐름',-6342733)]:
            actual,=[r for r in archive()[symbol]['financials'] if r['label']==label]
            self.assertEqual(actual['value'],value)
        self.assertEqual(PERIODS['LPG',1596993],('2025-04-01','2026-03-31'))

    def test_revenue_views_do_not_mix_subtotals_or_partial_amounts(self):
        expected={'DHT':('product',497197000),'FRO':('product',1965104000),
            'GLNG':('product',393522000),'FLNG':('segment',347637000),
            'LPG':('product',481511242),'INSW':('segment',843302000),
            'NAT':('product',291690000),'NVGS':('product',586961000),
            'STNG':('segment',938222000),'TEN':('product',798689000),
            'TK':('segment',949520000),'TNK':('segment',951797000),
            'TORO':('segment',21081840),'IMPP':('product',154775747),
            'PXS':('segment',38994000),'KNOP':('product',364443000)}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS),69)
        for symbol,(group,total) in expected.items():
            rows=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
            with self.subTest(symbol=symbol):
                self.assertEqual(sum(r['value'] for r in rows if r['group']==group),total)
                self.assertEqual(rows,present_revenue(rows,symbol))
                self.assertTrue(all(r['parent'] is None for r in rows))
        self.assertEqual(sum(r['value'] for r in REPORTS['GLNG']['revenue_mix'] if r['group']=='geography'),366724000)
        for symbol in ('LPG','NVGS','TEN','KNOP','IMPP'):
            self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in REPORTS[symbol]['revenue_mix']))
        for symbol in ('TK','TNK'):
            self.assertEqual(len([r for r in REPORTS[symbol]['revenue_mix'] if r['group']=='product']),9)
        self.assertIn('6,228,559',str(PUBLIC['IMPP']['brief']))

    def test_empty_cache_response_always_receives_reviewed_revenue(self):
        for symbol in SYMBOLS:
            with self.subTest(symbol=symbol):
                value=enrich(CompanyKnowledge(symbol=symbol,name=symbol))
                expected=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
                self.assertEqual([r.model_dump() for r in value.revenue_mix],
                    [RevenueLine.model_validate(r).model_dump() for r in expected])
                self.assertEqual(value.model_dump(),enrich(value).model_dump())

    def test_actual_roles_and_dates_are_not_changed_to_current_guesses(self):
        self.assertTrue(any(r['registry_id']=='goodwood-dht' and r['kind']=='subsidiary' for r in EDGES['DHT']))
        self.assertTrue(any(r['registry_id']=='tfg-marine' and r['kind']=='supplier' for r in EDGES['FRO']))
        self.assertTrue(any(r['registry_id']=='flex-fleet-management' and r['kind']=='supplier' for r in EDGES['FLNG']))
        self.assertTrue(any(r['registry_id']=='flex-fleet-management' and r['kind']=='subsidiary' for r in EDGES['FRO']))
        self.assertFalse(any(r['kind']=='customer' and r['registry_id'] in {'snh-cameroon','perenco-cameroon'} for r in EDGES['GLNG']))
        self.assertNotIn('GLNG',{r['symbol'] for r in EDGES['FLNG'] if r['kind']=='competitor'})
        for symbol in ('STNG','TEN','TORO','IMPP','PXS'):
            self.assertFalse(any(r['kind']=='subsidiary' for r in EDGES[symbol]))
        self.assertIn('4척·LPG 2척',str(PUBLIC['TORO']['brief']))
        self.assertIn('10월8일',str(PUBLIC['TORO']['brief']))
        self.assertIn('25척',str(PUBLIC['LPG']['brief']))
        self.assertIn('미완료',str(EDGES['TORO']))
        self.assertTrue(all('대조한' in r['detail'] for r in EDGES['DHT'] if r['kind']=='competitor'))
        self.assertGreaterEqual(len([r for r in EDGES['NVGS'] if r['kind']=='customer']),18)
        self.assertGreaterEqual(len([r for r in EDGES['LPG'] if r['kind']=='customer']),16)
        self.assertEqual(len([r for r in EDGES['TEN'] if r['kind']=='supplier']),8)

    def test_private_roles_and_verified_public_symbols_have_one_navigable_entity(self):
        with tempfile.TemporaryDirectory() as temp:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(temp)/'data'))
            for symbol in SYMBOLS:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in PRIVATE:
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol,key,kind,reverse in [
                ('DHT','goodwood-dht','subsidiary','parent'),
                ('FRO','tfg-marine','supplier','customer'),
                ('GLNG','sesa-flng','customer','supplier'),
                ('FLNG','flex-fleet-management','supplier','customer'),
                ('LPG','helios-lpg-pool','partner','partner'),
                ('LPG','bw-lpg-shipping','competitor','competitor'),
                ('INSW','tuka-insw','subsidiary','parent'),
                ('NVGS','cimc-sinopacific-navigator','supplier','customer'),
                ('STNG','scorpio-ship-management','supplier','customer'),
                ('TEN','hyundai-ocean-services-ten','supplier','customer'),
                ('TORO','robin-energy-toro','transaction','transaction'),
                ('PXS','itm-pyxis','supplier','customer'),
                ('KNOP','brazil-shipping-one-knot','customer','supplier')]:
                root=graph.by_symbol(symbol)
                edge=next(r for r in graph.relations(root['id']) if r['kind']==kind and graph.entity(r['target_id'])['registry_id']==key)
                target=graph.entity(edge['target_id'])
                self.assertTrue(target['profile']['brief'])
                back=next(r for r in graph.relations(target['id']) if r['target_id']==root['id'] and r['kind']==reverse)
                self.assertEqual(back['source'],edge['source'])
                if key in {'bw-lpg-shipping','robin-energy-toro'}:
                    ticker='BWLP' if key=='bw-lpg-shipping' else 'RBNE'
                    self.assertEqual(target['symbols'],[ticker])
                    self.assertEqual(graph.by_symbol(ticker)['id'],target['id'])

    def test_legacy_subtotals_and_wrong_metrics_cannot_reenter_current_filing(self):
        for symbol,member in [('TK','tk:VoyageChartersMember'),('TNK','tnk:OtherRevenuesMember'),
                ('GLNG','glng:BaseTollingRevenueMember'),('KNOP','knop:TimeAndBareboatCharterRevenuesMember')]:
            rows=deepcopy(REPORTS[symbol]['revenue_mix']);subtotal={**deepcopy(rows[0]),'member':member}
            self.assertEqual(present_revenue(rows+[subtotal],symbol),rows)
        ten=REPORTS['TEN']['revenue_mix']
        self.assertEqual(present_revenue(ten[:1],'TEN'),[])
        bad={**deepcopy(ten[1]),'metric':ten[0]['metric']}
        self.assertEqual(present_revenue([ten[0],bad],'TEN'),[])
        for symbol in SYMBOLS:
            rows=deepcopy(REPORTS[symbol]['revenue_mix'])
            eur=[{**r,'unit':'EUR'} for r in rows]
            self.assertEqual(present_revenue(eur,symbol),[])
            other=[{**r,'source':{**r['source'],'url':'https://www.sec.gov/Archives/edgar/data/1/other.htm'}} for r in eur]
            self.assertEqual(len(present_revenue(other,symbol)),len(other))
