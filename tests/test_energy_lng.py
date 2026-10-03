"""LNG construction, separated issuer scope and original signed tables."""
from copy import deepcopy
import datetime as dt
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_lng import EDGES, PRIVATE, PUBLIC, SYMBOLS
from cloud_app.company_energy_lng_revenue import COORDINATES, CONTRACT, DOCUMENTS, dimensions
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge, RevenueLine
from cloud_app.energy_issuers import issuer
from tests.test_company_revenue import context, doc, fact

HEADER = ('<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric>'
          '<ix:nonNumeric name="dei:DocumentPeriodEndDate">2025-12-31</ix:nonNumeric>')


class LngResearchTests(unittest.TestCase):
    def test_actual_enrichment_keeps_original_views_and_preseparation_scope(self):
        totals = {'EE': 1228263000, 'NFE': 1504037000, 'VG': 13769000000}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS), 26)
        for symbol in SYMBOLS:
            value = enrich(CompanyKnowledge(symbol=symbol,name=symbol+' truncated'))
            self.assertEqual(value.name, PUBLIC[symbol]['name'])
            self.assertGreaterEqual(len(value.products), 7)
            self.assertGreaterEqual(len(value.brief), 6)
            self.assertTrue(value.financials and value.financial_context and value.relations)
            self.assertTrue(value.segments and value.drivers)
            self.assertEqual(issuer(symbol).group, 'lng')
            self.assertEqual(value.model_dump(), enrich(value).model_dump())
            rows = present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
            self.assertEqual([r.model_dump() for r in value.revenue_mix],
                [RevenueLine.model_validate(r).model_dump() for r in rows])
            for group in {r['group'] for r in rows}:
                if symbol == 'NFE' and group == 'product':
                    self.assertEqual(sum(r['value'] for r in rows if r['group']==group),276404000)
                else:
                    self.assertEqual(sum(r['value'] for r in rows if r['group']==group), totals[symbol])
        self.assertFalse(REPORTS['NEXT']['revenue_mix'])
        self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in REPORTS['NFE']['revenue_mix']))
        vg = [r for r in REPORTS['VG']['revenue_mix'] if r['group']=='segment']
        self.assertEqual(next(r['value'] for r in vg if 'Eliminations' in r['member']),-2050000000)
        self.assertTrue(all(r['includes_intersegment'] and r['share_exclusion'] for r in vg))

    def test_original_coordinates_reject_identity_dimensions_and_wrong_metric(self):
        for (symbol,cik,pairs),expected in COORDINATES.items():
            pairs = sorted(pairs)
            with self.subTest(symbol=symbol,member=expected[1]):
                self.assertEqual(dimensions(pairs,symbol,cik),expected)
                self.assertIsNone(dimensions(pairs+[pairs[0]],symbol,cik))
                self.assertIsNone(dimensions(pairs+[('x:UnknownAxis','x:UnknownMember')],symbol,cik))
                self.assertIsNone(dimensions(pairs,symbol,cik+1))
                metric = CONTRACT if symbol=='VG' or (symbol=='NFE' and expected[0]=='product') else 'us-gaap:Revenues'
                extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                dates = dict(cik=str(cik),start='2025-01-01',end='2025-12-31')
                origin = dict(label='검토 원문',level='primary',as_of='2026-04-06',url=DOCUMENTS[symbol,cik])
                raw = doc(context('total',**dates)+context('part',pairs[0][1],axis=pairs[0][0],extra=extra,**dates),
                    HEADER+fact('total','100',metric=metric,scale=0)+fact('part','70',metric=metric,scale=0))
                row, = parse_revenue(raw,origin,symbol,dt.date(2026,10,4))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin,symbol),[])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin,symbol),[])
                wrong = 'us-gaap:SalesRevenueNet'
                self.assertEqual(parse_revenue(raw.replace(metric,wrong),origin,symbol),[])

    def test_signed_reconciliation_is_retained_and_conflicting_cache_is_removed(self):
        from cloud_app.company_energy_lng_revenue import canonical
        row = deepcopy(next(r for r in REPORTS['VG']['revenue_mix'] if r['value']<0))
        self.assertEqual(canonical([row,{**row,'value':row['value']-1}],'VG',2007855),[])
        other = {**row,'source':{**row['source'],'url':row['source']['url']+'other'}}
        self.assertEqual(canonical([other],'VG',2007855),[other])
        pairs=[('srt:ConsolidationItemsAxis','vg:CorporateReconcilingItemsAndEliminationsMember')]
        dates=dict(cik='2007855',start='2025-01-01',end='2025-12-31')
        raw=doc(context('total',**dates)+context('part',pairs[0][1],axis=pairs[0][0],**dates),
            HEADER+fact('total','13769',metric=CONTRACT,scale=6)+fact('part','2050',metric=CONTRACT,scale=6,attrs='sign="-"'))
        value,=parse_revenue(raw,row['source'],'VG',dt.date(2026,10,4))
        self.assertEqual(value['value'],-2050000000)
        self.assertIsNone(value['total'])

    def test_actual_business_graph_preserves_independent_brazil_and_shared_counterparts(self):
        with tempfile.TemporaryDirectory() as temp:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(temp)/'data'))
            for symbol in SYMBOLS:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in (*PRIVATE,'qatarenergy','bechtel','hyundai-heavy-dorian','whitewater'):
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol,key,kind in [('EE','nepco-jordan','customer'),('NEXT','bechtel','supplier'),
                ('NFE','nfe-brazil-holdings','transaction'),('VG','china-gas','customer')]:
                root=graph.by_symbol(symbol)
                edge=next(e for e in graph.relations(root['id']) if e['kind']==kind
                          and graph.entity(e['target_id'])['registry_id']==key)
                self.assertTrue(any(e['target_id']==root['id'] for e in graph.relations(edge['target_id'])))
            self.assertFalse(any(e['kind']=='subsidiary' and e['registry_id']=='nfe-brazil-holdings' for e in EDGES['NFE']))
            self.assertFalse(any('Iraq Ministry' in e['name'] for e in EDGES['EE']))
            self.assertTrue(any('Rio Grande' in r['title'] for r in private_profile('bechtel')['brief']))
            self.assertIn('Cheniere', private_profile('bechtel')['description'])
