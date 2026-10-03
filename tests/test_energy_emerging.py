"""Predecessor, restated, non-operating and post-close issuer boundaries."""
from copy import deepcopy
import unittest
from cloud_app.company_catalog import enrich
from cloud_app.company_energy_emerging import PUBLIC, PRIVATE, EDGES, SYMBOLS, QUARTER, FTW_CANYON
from cloud_app.company_energy_emerging_revenue import canonical
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_research_catalog import PRIVATE_COMPANIES
from cloud_app.company_revenue import present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer

class EmergingResearchTests(unittest.TestCase):
    def test_predecessor_and_restatement_bridges(self):
        totals = {'EROK':72173000,'FTW':179056000,'HMH':821754000}
        for s,total in totals.items():
            rows=present_revenue(REPORTS[s]['revenue_mix'],s)
            for group in {r['group'] for r in rows}:
                self.assertEqual(sum(r['value'] for r in rows if r['group']==group),total)
        rows=present_revenue(REPORTS['WHK']['revenue_mix'],'WHK')
        self.assertEqual(sum(r['value'] for r in rows if r['group']=='product'),50075000)
        self.assertEqual(sum(r['value'] for r in rows if r['group']=='revenue_type'),67595000)
        self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in rows))
        self.assertEqual([r['value'] for r in rows if r['value']<0],[-8626000])
        for s in ('AMEN','UNTC','NUCL'):
            self.assertEqual(REPORTS[s]['revenue_mix'],[])

    def test_mezzanine_and_discontinued_business_are_not_sales_or_equity(self):
        figures={s:{r['label']:r['value'] for r in PUBLIC[s]['financials']} for s in SYMBOLS}
        self.assertEqual(figures['NUCL']['총자산'],figures['NUCL']['총부채']+figures['NUCL']['자본']+300000)
        self.assertEqual(figures['WHK']['총자산'],figures['WHK']['총부채']+figures['WHK']['자본']+27662000)
        self.assertEqual(figures['UNTC']['순이익 · 중단 포함']-figures['UNTC']['순이익 · 지속 사업'],56738000)
        self.assertEqual(figures['AMEN']['매출'],2348341)
        self.assertNotIn('매출',figures['NUCL'])

    def test_cached_subtotals_projections_and_wrong_currency_do_not_replace_originals(self):
        for s,cik in [('EROK',2104882),('FTW',2083125),('HMH',2021880),('WHK',1921603)]:
            rows=deepcopy(REPORTS[s]['revenue_mix'])
            fake=deepcopy(rows[0]);fake['member']='reported:Total'
            foreign=deepcopy(rows[0]);foreign['unit']='EUR'
            changed=deepcopy(rows[0]);changed['value']+=1
            projection=deepcopy(rows[0]);projection['end']='2026-12-31'
            self.assertEqual(canonical(rows+[fake,foreign,changed,projection,rows[0]],s,cik),rows)

    def test_seven_issuers_enrich_idempotently_with_dated_primary_evidence(self):
        for s in SYMBOLS:
            value=enrich(CompanyKnowledge(symbol=s,name=s))
            self.assertEqual(value.name,PUBLIC[s]['name'])
            self.assertEqual(enrich(value).model_dump(),value.model_dump())
            self.assertGreaterEqual(len(value.brief),6)
            self.assertTrue(value.financials and value.products and value.financial_context and value.relations)
            self.assertNotEqual(issuer(s).group,'pending')
            self.assertEqual(issuer(s).report_source.as_of,REPORTS[s]['annual']['as_of'])
            self.assertTrue(all(r['source']['level']=='primary' for r in PUBLIC[s]['products']))
        self.assertEqual(PUBLIC['EROK']['products'][6]['source'],QUARTER['EROK'])
        self.assertEqual(PUBLIC['FTW']['products'][4]['source'],FTW_CANYON)

    def test_actual_operating_and_transaction_roles_link_exact_entities(self):
        for rows in EDGES.values():
            for edge in rows:
                if edge.get('registry_id'):
                    self.assertIn(edge['registry_id'],PRIVATE_COMPANIES)
        self.assertEqual(next(e['kind'] for e in EDGES['EROK'] if e.get('registry_id')=='hydrosource-logistics'),'partner')
        self.assertEqual(next(e['kind'] for e in EDGES['UNTC'] if e.get('registry_id')=='cactus-drilling'),'transaction')
        self.assertFalse(any(e.get('symbol')=='WHD' for e in EDGES['UNTC']))
        self.assertTrue(all(e['kind']=='partner' for e in EDGES['WHK'] if e.get('symbol')))
        self.assertFalse(any(e['kind']=='customer' for e in EDGES['NUCL']))
