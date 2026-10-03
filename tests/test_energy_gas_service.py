"""Fuel and service table boundaries, mixed lease metrics and actual graph roles."""
import datetime as dt
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_gas_service import EDGES, PRIVATE, PUBLIC, SYMBOLS
from cloud_app.company_energy_gas_service_revenue import COORDINATES, CONTRACT, DOCUMENTS, PERIODS, dimensions
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact
from cloud_app.energy_issuers import issuer


def header(end):
    return ('<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric>'
            f'<ix:nonNumeric name="dei:DocumentPeriodEndDate">{end}</ix:nonNumeric>')


class GasServiceResearchTests(unittest.TestCase):
    def test_actual_original_tables_and_dated_business_profiles(self):
        totals={'CLNE':424833000,'FGPR':1864014000,'NFG':2277541000,
                'NGS':172315000,'SEI':622205000,'SMC':562091000}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS),45)
        for symbol in SYMBOLS:
            value=enrich(CompanyKnowledge(symbol=symbol,name=symbol))
            self.assertEqual(value.name,PUBLIC[symbol]['name'])
            self.assertTrue(value.financials and value.relations and value.financial_context)
            self.assertEqual(value.model_dump(),enrich(value).model_dump())
            rows=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
            for group in {r['group'] for r in rows}:
                expected=2219117000 if symbol=='NFG' and group=='product' else (
                    622200000 if symbol=='SEI' and group!='revenue_type' else totals[symbol])
                self.assertEqual(sum(r['value'] for r in rows if r['group']==group),expected)
        self.assertEqual(issuer('NFG').sector_hint,'us_55')
        for symbol in SYMBOLS:
            self.assertNotEqual(issuer(symbol).group,'pending')
        self.assertEqual(len(REPORTS['FGPR']['revenue_mix']),5)
        self.assertTrue(all(r['end']=='2026-07-31' for r in REPORTS['FGPR']['revenue_mix']))
        self.assertFalse(any(r['member']=='ngs:ProductSalesMember' for r in REPORTS['NGS']['revenue_mix']))
        self.assertFalse(any(r['member'].startswith('smlp:') and r['group']=='product' for r in REPORTS['SMC']['revenue_mix']))

    def test_original_coordinates_and_compound_members(self):
        for (symbol,cik,pairs),expected in COORDINATES.items():
            pairs=sorted(pairs)
            with self.subTest(symbol=symbol,member=expected[1]):
                self.assertEqual(dimensions(pairs,symbol,cik),expected)
                self.assertIsNone(dimensions(pairs+[pairs[0]],symbol,cik))
                self.assertIsNone(dimensions(pairs+[('x:UnknownAxis','x:UnknownMember')],symbol,cik))
                metric='us-gaap:Revenues' if (symbol=='NFG' and expected[0]=='segment') or (symbol=='SEI' and expected[0]!='revenue_type') else CONTRACT
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                start,end=PERIODS[symbol,cik]
                dates=dict(cik=str(cik),start=start,end=end)
                origin=dict(label='검토 원문',level='primary',as_of='2026-09-25',url=DOCUMENTS[symbol,cik])
                raw=doc(context('total',**dates)+context('part',pairs[0][1],axis=pairs[0][0],extra=extra,**dates),
                    header(end)+fact('total','100',metric=metric,scale=0)+fact('part','70',metric=metric,scale=0))
                row,=parse_revenue(raw,origin,symbol,dt.date(2026,10,4))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin,symbol),[])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin,symbol),[])
                self.assertEqual(parse_revenue(raw.replace(metric,'us-gaap:SalesRevenueNet'),origin,symbol),[])

    def test_lease_statement_rows_are_not_inferred_from_a_missing_total(self):
        for symbol,cik,metric,value in [('NGS',1084991,'us-gaap:RentalIncomeNonoperating',164326000),
                                     ('SEI',1697500,'us-gaap:OperatingLeaseLeaseIncome',272357000)]:
            start,end=PERIODS[symbol,cik]
            dates=dict(cik=str(cik),start=start,end=end)
            origin=dict(label='검토 원문',level='primary',as_of='2026-03-16',url=DOCUMENTS[symbol,cik])
            raw=doc(context('total',**dates),header(end)+fact('total',str(value),metric=metric,scale=0))
            row,=parse_revenue(raw,origin,symbol,dt.date(2026,10,4))
            self.assertEqual(row['value'],value)
            self.assertTrue(row['share_exclusion'])
            self.assertIsNone(row['total'])
            self.assertEqual(parse_revenue(raw.replace(metric,'us-gaap:Revenues'),origin,symbol),[])
            self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin,symbol),[])

    def test_mixed_and_rounded_scopes_have_no_false_percentages(self):
        for symbol in ['SEI','NGS']:
            rows=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
            self.assertTrue(all(r['share_exclusion'] and r['total'] is None for r in rows))
        sei=REPORTS['SEI']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in sei if r['group']=='revenue_type'),622205000)
        self.assertEqual(sum(r['value'] for r in sei if r['group']=='segment'),622200000)
        self.assertFalse(any(r['value']==5000 for r in sei))

    def test_actual_graph_roles_and_no_guessed_ai_counterparty(self):
        self.assertFalse(any(e.get('symbol') in {'NVDA','CAT','BKR'} for e in EDGES['SEI']))
        self.assertEqual(sum(e['kind']=='customer' for e in EDGES['NGS']),2)
        self.assertTrue(any(e['kind']=='partner' and e['registry_id']=='double-e-pipeline' for e in EDGES['SMC']))
        with tempfile.TemporaryDirectory() as temp:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(temp)/'data'))
            for symbol in SYMBOLS:graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in (*PRIVATE,'ariel-compressors'):graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol,key,kind in [('CLNE','maas-energy','partner'),('FGPR','ferrellgas-gp','partner'),
                ('NFG','seneca-resources','subsidiary'),('NGS','ariel-compressors','supplier'),
                ('SEI','omega-foundation','subsidiary'),('SMC','double-e-pipeline','partner')]:
                root=graph.by_symbol(symbol)
                edge=next(e for e in graph.relations(root['id']) if e['kind']==kind and graph.entity(e['target_id'])['registry_id']==key)
                self.assertTrue(any(e['target_id']==root['id'] for e in graph.relations(edge['target_id'])))
