"""Protect coal revenue, VIE scope and actual legal counterpart links."""
from copy import deepcopy
import datetime as dt
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_coal import EDGES, PRIVATE, PUBLIC, SYMBOLS
from cloud_app.company_energy_coal_revenue import COORDINATES, CONTRACT, DOCUMENTS, canonical, dimensions
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact

HEADER = ('<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric>'
          '<ix:nonNumeric name="dei:DocumentPeriodEndDate">2025-12-31</ix:nonNumeric>')


class CoalResearchTests(unittest.TestCase):
    def test_external_tables_balance_without_subtotal_or_vie_double_count(self):
        totals = {'ARLP':2194811000, 'BTU':3861500000, 'CNR':4164775000, 'NC':277198000}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS),32)
        for symbol in SYMBOLS:
            value=enrich(CompanyKnowledge(symbol=symbol,name=symbol))
            self.assertEqual(value.name,PUBLIC[symbol]['name'])
            self.assertTrue(value.financials and value.financial_context and value.relations)
            self.assertEqual(value.model_dump(),enrich(value).model_dump())
            rows=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
            for group in {r['group'] for r in rows}:
                self.assertEqual(sum(r['value'] for r in rows if r['group']==group),totals[symbol])
            if symbol in {'ARLP','NC'}:
                self.assertTrue(all(r['share_exclusion'] and r['total'] is None for r in rows if r['group']=='segment'))
        self.assertFalse(any(r['member']=='us-gaap:PublicUtilitiesInventoryCoalMember' for r in REPORTS['CNR']['revenue_mix']))
        cmt=next(r for r in REPORTS['CNR']['revenue_mix'] if r['member']=='cnr:CoreMarineTerminalMember')
        self.assertEqual(cmt['value'],21477000)
        self.assertFalse(any(r['value']==567841000 for r in REPORTS['NC']['revenue_mix']))

    def test_exact_coordinates_reject_currency_identity_and_unknown_qualifier(self):
        for (symbol,cik,pairs),expected in COORDINATES.items():
            pairs=sorted(pairs)
            with self.subTest(symbol=symbol,member=expected[1]):
                self.assertEqual(dimensions(pairs,symbol,cik),expected)
                self.assertIsNone(dimensions(pairs+[pairs[0]],symbol,cik))
                self.assertIsNone(dimensions(pairs+[('x:UnknownAxis','x:UnknownMember')],symbol,cik))
                metric='us-gaap:Revenues' if symbol=='BTU' else CONTRACT
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                dates=dict(cik=str(cik),start='2025-01-01',end='2025-12-31')
                origin=dict(label='검토 원문',level='primary',as_of='2026-03-04',url=DOCUMENTS[symbol,cik])
                raw=doc(context('total',**dates)+context('part',pairs[0][1],axis=pairs[0][0],extra=extra,**dates),
                    HEADER+fact('total','100',metric=metric,scale=0)+fact('part','70',metric=metric,scale=0))
                row,=parse_revenue(raw,origin,symbol,dt.date(2026,10,4))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin,symbol),[])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin,symbol),[])
                self.assertEqual(parse_revenue(raw.replace(metric,'us-gaap:SalesRevenueNet'),origin,symbol),[])

    def test_signed_adjustments_and_conflicting_cached_facts(self):
        for symbol,cik,member,value in [('ARLP',1086600,'us-gaap:CorporateNonSegmentMember',-6081000),
                                      ('NC',789933,'srt:ConsolidationEliminationsMember',-3713000)]:
            row=deepcopy(next(r for r in REPORTS[symbol]['revenue_mix'] if r['member']==member))
            self.assertEqual(row['value'],value)
            self.assertEqual(canonical([row,{**row,'value':value-1}],symbol,cik),[])
            dates=dict(cik=str(cik),start='2025-01-01',end='2025-12-31')
            raw=doc(context('total',**dates)+context('part',member,axis='srt:ConsolidationItemsAxis',**dates),
                HEADER+fact('total','10000000',metric=CONTRACT,scale=0)+fact('part',str(-value),metric=CONTRACT,scale=0,attrs='sign="-"'))
            actual,=parse_revenue(raw,row['source'],symbol,dt.date(2026,10,4))
            self.assertEqual(actual['value'],value)
            self.assertIsNone(actual['total'])

    def test_graph_keeps_jv_and_contract_roles_and_unconfirmed_closure(self):
        self.assertFalse(any(e['kind']=='subsidiary' and e['registry_id']=='middlemount-coal' for e in EDGES['BTU']))
        self.assertFalse(any('Sabine' in e['name'] and e['kind']=='subsidiary' for e in EDGES['NC']))
        self.assertIn('종결 증거는 미확보',PUBLIC['NC']['products'][-1]['detail'])
        with tempfile.TemporaryDirectory() as temp:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(temp)/'data'))
            for symbol in SYMBOLS: graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in PRIVATE: graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol,key,kind in [('ARLP','matrix-design','subsidiary'),('BTU','middlemount-coal','partner'),
                                   ('CNR','dominion-terminal','partner'),('NC','swepco-sabine','customer')]:
                root=graph.by_symbol(symbol)
                edge=next(e for e in graph.relations(root['id']) if e['kind']==kind and graph.entity(e['target_id'])['registry_id']==key)
                self.assertTrue(any(e['target_id']==root['id'] for e in graph.relations(edge['target_id'])))

    def test_generated_exhibit_claim_is_corrected_only_for_the_reviewed_jv(self):
        origin=dict(label='SEC · Exhibit 21 자회사 명세서',level='primary',as_of='2026-02-19',
            url='https://www.sec.gov/Archives/edgar/data/1064728/000106472826000006/btu_20251231xex21.htm')
        legacy=dict(name='Middlemount Coal Pty Ltd',kind='subsidiary',
            detail='공시 자회사 명세서 · 설립·등록 관할: Australia',source=origin)
        manager={**legacy,'name':'Middlemount Mine Management Pty Ltd'}
        value=enrich(CompanyKnowledge(symbol='BTU',name='Peabody',relations=[legacy,manager]))
        self.assertFalse(any(r.kind=='subsidiary' and r.name==legacy['name'] for r in value.relations))
        self.assertTrue(any(r.kind=='partner' and r.name==legacy['name'] for r in value.relations))
        self.assertTrue(any(r.kind=='subsidiary' and r.name==manager['name'] for r in value.relations))
        self.assertIn(origin,[s.model_dump() for s in value.sources])
        self.assertEqual(value.model_dump(),enrich(value).model_dump())
