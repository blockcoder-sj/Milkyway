"""Canadian source scopes, actual named roles and navigation, entirely offline."""
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_canada import AIF, FIN, PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_canada_revenue import COORDINATES, DOCUMENTS
from cloud_app.company_energy_financial_archive import archive, validate_archive
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class EnergyCanadaTests(unittest.TestCase):
    def test_profiles_have_edited_primary_notes_and_preserve_sources_on_repeat_merge(self):
        self.assertEqual(set(PUBLIC),{'SU','CNQ','IMO','CVE','OBE','BTE','VET','PDS'})
        for symbol,notes in PUBLIC.items():
            with self.subTest(symbol=symbol):
                current=enrich(CompanyKnowledge(symbol=symbol,**notes))
                self.assertGreaterEqual(len(current.brief),6)
                self.assertGreaterEqual(len(current.products),4)
                self.assertTrue(current.drivers and current.revenue_mix and current.financials)
                self.assertTrue(current.financial_context)
                self.assertEqual(enrich(current).model_dump(),current.model_dump())
                self.assertTrue(all(f.source.level=='primary' and not f.original
                                    for f in current.brief+current.products+current.drivers))
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)
        for rows in EDGES.values():
            for edge in rows:
                if edge['registry_id']:
                    self.assertTrue(private_profile(edge['registry_id']))

    def test_exhibit_figures_retain_cover_receipt_and_the_actual_financial_document(self):
        expected={'SU':52377000000,'CNQ':38762000000,'IMO':47078000000,'CVE':49696000000,
                  'OBE':571300000,'BTE':1480815000,'VET':1765141000,'PDS':1843704000}
        records=archive()
        for symbol,value in expected.items():
            with self.subTest(symbol=symbol):
                record=records[symbol]
                self.assertEqual(record['annual']['url'],FIN[symbol]['url'])
                self.assertEqual(record['financials'][0]['value'],value)
                self.assertTrue(all(r['unit']=='CAD' for r in record['financials']))
                if symbol not in {'CNQ','IMO'}:
                    self.assertEqual(record['parent_annual']['url'],REPORTS[symbol]['annual']['url'])
                    self.assertEqual(record['annual_period_end'],'2025-12-31')
        self.assertEqual(records['IMO']['financials'][0]['label'],'매출·기타소득 합계')
        self.assertEqual(next(r['value'] for r in records['CVE']['financials'] if r['label']=='현금·현금성 자산'),2740000000)
        self.assertEqual(next(r['value'] for r in records['SU']['financials'] if r['label']=='영업활동 현금흐름'),12781000000)
        self.assertEqual(next(r['value'] for r in records['VET']['financials'] if r['label']=='총자산'),5344220000)
        self.assertEqual(next(r['value'] for r in records['VET']['financials'] if r['label']=='총부채'),3122359000)
        self.assertIn('Saskatchewan',records['VET']['financial_context'][0]['detail'])
        self.assertIn('Manitoba',records['VET']['financial_context'][0]['detail'])
        self.assertLess(next(r['value'] for r in records['BTE']['financials'] if '순이익' in r['label']),0)
        bad={'SU':deepcopy(records['SU'])}
        bad['SU']['annual']['url']=bad['SU']['annual']['url'].replace('ex99d2','ex99d3')
        for row in bad['SU']['financials']:
            row['source']['url']=row['source']['url'].replace('ex99d2','ex99d3')
        with self.assertRaises(ValueError):validate_archive(bad)

    def test_same_basis_products_and_countries_reconcile_without_suppressing_valid_ratios(self):
        for symbol,group,total in [('SU','geography',52377000000),('CVE','geography',49696000000),
                                  ('OBE','product',599800000),('BTE','product',1684648000),
                                  ('VET','geography',1765141000),('PDS','product',1843704000),
                                  ('PDS','geography',1843704000)]:
            with self.subTest(symbol=symbol,group=group):
                rows=[r for r in present_revenue(REPORTS[symbol]['revenue_mix'],symbol) if r['group']==group]
                self.assertEqual(sum(r['value'] for r in rows),total)
                self.assertTrue(all(r['total']==total and not r.get('share_exclusion') for r in rows))
        su=next(r for r in REPORTS['SU']['revenue_mix'] if 'NaturalGasMember' in r['member'])
        self.assertEqual(su['label'],'탐사·생산 · 원유·NGL')
        self.assertEqual(su['value'],2509000000)

    def test_internal_sales_keep_exact_eliminations_and_positive_other_adjustment(self):
        for symbol,gross,adjustment,total in [('SU',60504000000,-8127000000,52377000000),
            ('CNQ',37686000000,1076000000,38762000000),('IMO',69482000000,-22404000000,47078000000),
            ('CVE',58637000000,-8941000000,49696000000),('PDS',1854854000,-11150000,1843704000)]:
            rows=[r for r in present_revenue(REPORTS[symbol]['revenue_mix'],symbol) if r['group']=='segment']
            expected=gross+adjustment if symbol=='CNQ' else gross
            self.assertEqual(sum(r['value'] for r in rows),expected)
            self.assertEqual(gross+adjustment,total)
            self.assertTrue(all(r['includes_intersegment'] and r['total'] is None and r['share_exclusion'] for r in rows))
        imo=present_revenue(REPORTS['IMO']['revenue_mix'],'IMO')[0]['share_exclusion']
        self.assertIn('기타소득',imo)
        self.assertIn('160,000,000',imo)

    def test_reviewed_coordinates_reject_wrong_issuer_or_extra_dimensions(self):
        for (symbol,cik,pairs),(group,member) in COORDINATES.items():
            with self.subTest(symbol=symbol,member=member):
                pairs=sorted(pairs);axis,first=pairs[0]
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                dates=dict(cik=str(cik),start='2025-01-01',end='2025-12-31')
                metric='us-gaap:Revenues' if symbol=='IMO' else 'ifrs-full:Revenue'
                raw=doc(context('total',**dates)+context('part',first,axis=axis,extra=extra,**dates),
                        fact('total','100',metric=metric)+fact('part','70',metric=metric))
                origin={**FIN[symbol],'url':DOCUMENTS[symbol,cik]}
                row,=parse_revenue(raw,origin,symbol)
                self.assertEqual((row['group'],row['member']),(group,member))
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin,symbol),[])
                unexpected='<xbrldi:explicitMember dimension="x:ExtraAxis">x:OtherMember</xbrldi:explicitMember>'
                self.assertEqual(parse_revenue(raw.replace('</xbrli:segment>',unexpected+'</xbrli:segment>'),origin,symbol),[])

    def test_actual_deals_do_not_become_current_supplier_or_joint_venture(self):
        for symbol,name in [('OBE','InPlay Oil'),('OBE','Delek Group'),('BTE','Eagle Ford Buyer Co., LLC'),('CVE','Phillips 66')]:
            matches=[e for e in EDGES[symbol] if e['name']==name]
            self.assertEqual(len(matches),1)
            self.assertEqual(matches[0]['kind'],'transaction')
        self.assertFalse(any(e['symbol']=='DK' for e in EDGES['OBE']))
        self.assertFalse(any(e['symbol']=='TRP' for e in EDGES['CVE']))
        self.assertTrue(any(e['symbol']=='SOBO' for e in EDGES['CVE']))
        self.assertIn('56.5%',PUBLIC['VET']['products'][1]['detail'])
        self.assertIn('총 수요',PUBLIC['VET']['market_shares'][0]['detail'])
        self.assertTrue(any(e['registry_id']=='whitecap-resources' and e['kind']=='partner'
                            for e in EDGES['OBE']))
        self.assertTrue(any(e['registry_id']=='isn-contractor-management' and e['kind']=='supplier'
                            for e in EDGES['OBE']))
        self.assertIn('65643',str(PUBLIC['OBE']['brief']))
        self.assertIn('연간 확정 생산량이 아닙니다',str(PUBLIC['OBE']['brief']))
        self.assertIn('실제 인도',str(PUBLIC['SU']['brief']))

    def test_context_navigation_and_reverse_role_keep_original_statement(self):
        with tempfile.TemporaryDirectory() as directory:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,
                dataset_dir=Path(directory)/'data'))
            for symbol in ('PDS','OBE'):
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in ('rostel-industries','delek-group'):
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            root=graph.by_symbol('PDS')
            edge=next(e for e in graph.relations(root['id']) if e['name']=='Rostel Industries' and e['kind']=='supplier')
            detail=graph.entity(edge['target_id'])
            self.assertTrue(detail and detail['profile']['brief'])
            reverse=next(e for e in graph.relations(edge['target_id']) if e['target_id']==root['id'])
            self.assertEqual(reverse['kind'],'customer')
            self.assertTrue(reverse['reverse'])
            self.assertEqual(reverse['source'],edge['source'])
            deal=next(e for e in graph.relations(graph.by_symbol('OBE')['id']) if e['name']=='Delek Group')
            backwards=next(e for e in graph.relations(deal['target_id']) if e['target_id']==graph.by_symbol('OBE')['id'])
            self.assertEqual(backwards['kind'],'transaction')


if __name__ == '__main__':
    unittest.main()
