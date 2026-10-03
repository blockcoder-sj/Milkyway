"""Original annual scopes, current transactions and issuer-bound revenue facts."""
import datetime as dt
import unittest
from cloud_app.company_catalog import enrich
from cloud_app.company_energy_transition import PUBLIC, PRIVATE, EDGES, SYMBOLS
from cloud_app.company_energy_transition_revenue import COORDINATES, DOCUMENTS, PERIODS, CONTRACT, INCLUDING, REVENUES, dimensions
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer
from tests.test_company_revenue import context, doc, fact

class TransitionResearchTests(unittest.TestCase):
    def test_original_totals_and_scope(self):
        totals={'APC':5581264000,'BDCO':279385000,'IEP':9658000000,'INVX':978251000,
                'NUAI':885400,'RSRV':17441161,'SUNC':25201000000}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS),56)
        for s,total in totals.items():
            rows=present_revenue(REPORTS[s]['revenue_mix'],s)
            for group in {r['group'] for r in rows}:
                self.assertEqual(sum(r['value'] for r in rows if r['group']==group),total)
        self.assertEqual(REPORTS['TBN']['revenue_mix'],[])
        self.assertEqual({r['member'] for r in REPORTS['NUAI']['revenue_mix']},
                         {'nehc:NaturalGasNetMember','srt:NaturalGasLiquidsReservesMember'})
        self.assertFalse(any(r['member']=='bdco:ConsolidatedValueMember' for r in REPORTS['BDCO']['revenue_mix']))
        for s in ('RSRV','IEP'):
            self.assertTrue(all(r['share_exclusion'] and r['total'] is None for r in REPORTS[s]['revenue_mix']))

    def test_exact_dimensions_reject_qualifiers_identity_currency_and_metric(self):
        for (s,c,pairs),expected in COORDINATES.items():
            pairs=sorted(pairs)
            with self.subTest(symbol=s,member=expected[1]):
                self.assertEqual(dimensions(pairs,s,c),expected)
                self.assertIsNone(dimensions(pairs+[pairs[0]],s,c))
                self.assertIsNone(dimensions(pairs+[('x:UnknownAxis','x:UnknownMember')],s,c))
                tag=REVENUES if s in ('IEP','SUNC') else INCLUDING if s in ('NUAI','RSRV') else CONTRACT
                if s=='RSRV' and expected[1]=='rsrv:LeaseBonusesAndOtherMember':tag='us-gaap:RegulatedOperatingRevenueGas'
                start,end=PERIODS[s,c]
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                dates=dict(cik=str(c),start=start,end=end)
                raw=doc(context('t',**dates)+context('p',pairs[0][1],axis=pairs[0][0],extra=extra,**dates),
                    f'<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric><ix:nonNumeric name="dei:DocumentPeriodEndDate">{end}</ix:nonNumeric>'+fact('t','100',metric=tag,scale=0)+fact('p','70',metric=tag,scale=0))
                origin=dict(label='원문',url=DOCUMENTS[s,c],as_of='2026-09-25',level='primary')
                row,=parse_revenue(raw,origin,s,dt.date(2026,10,4))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                self.assertEqual(parse_revenue(raw.replace(str(c),str(c+1)),origin,s),[])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin,s),[])
                self.assertEqual(parse_revenue(raw.replace(tag,'us-gaap:SalesRevenueNet'),origin,s),[])

    def test_legal_identity_and_current_status_survive_repeated_enrichment(self):
        for s in SYMBOLS:
            value=enrich(CompanyKnowledge(symbol=s,name=s))
            self.assertEqual(value.name,PUBLIC[s]['name'])
            self.assertTrue(value.financials and value.products and value.financial_context and value.relations)
            self.assertGreaterEqual(len(value.brief),6)
            self.assertEqual(enrich(value).model_dump(),value.model_dump())
            self.assertNotEqual(issuer(s).group,'pending')
        self.assertIn('Anadarko',PUBLIC['APC']['description'])
        self.assertIn('2027',PUBLIC['NUAI']['products'][4]['detail'])
        self.assertIn('판매',PUBLIC['TBN']['description'])
        self.assertIn('완료',PUBLIC['IEP']['products'][3]['detail'])
        self.assertIn('허가',PUBLIC['NUAI']['brief'][-1]['title'])

    def test_actual_roles_and_plan_are_separate(self):
        self.assertTrue(all(key in PRIVATE for rows in EDGES.values() for e in rows
                            if (key:=e.get('registry_id'))))
        self.assertEqual(next(e['kind'] for e in EDGES['APC'] if e.get('registry_id')=='us-petroleum-partners'),'transaction')
        self.assertEqual(next(e['kind'] for e in EDGES['BDCO'] if e.get('registry_id')=='lazarus-energy-holdings'),'customer')
        self.assertFalse(any(e.get('symbol')=='APA' for e in EDGES['TBN']))
        self.assertFalse(any(e['kind']=='customer' and e.get('symbol') in {'NVDA','MSFT','AMZN'} for e in EDGES['NUAI']))

    def test_apc_shell_and_combined_figures_are_not_mixed(self):
        rows=PUBLIC['APC']['financials']
        self.assertTrue(all('combined' in r['period'] for r in rows))
        self.assertEqual(next(r['value'] for r in rows if r['label'].startswith('총자산')),1273474000)
        self.assertFalse(any(r['value']==2112000 for r in rows))
