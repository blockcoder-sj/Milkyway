"""Reviewed royalties retain accounting basis, legal identity and navigation."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_land import PUBLIC, PRIVATE, EDGES, SYMBOLS
from cloud_app.company_energy_land_tables import FINANCIALS, REVENUE, PERIODS
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import present_revenue
from cloud_app.company_schemas import CompanyKnowledge, Financial, RevenueLine
from cloud_app.energy_issuers import issuer, registry


class LandResearchTests(unittest.TestCase):
    def test_all_fifteen_are_available_without_cached_provider_details(self):
        self.assertEqual(set(PUBLIC),set(SYMBOLS))
        self.assertEqual(len(SYMBOLS),15)
        self.assertEqual(len(registry().rows),213)
        for symbol in SYMBOLS:
            with self.subTest(symbol=symbol):
                value=enrich(CompanyKnowledge(symbol=symbol,name=symbol+' provider truncated'))
                self.assertEqual(value.name,PUBLIC[symbol]['name'])
                self.assertGreaterEqual(len(value.brief),6)
                self.assertGreaterEqual(len(value.products),7)
                self.assertTrue(value.financials and value.financial_context)
                self.assertTrue(value.segments and value.drivers and value.relations)
                self.assertTrue(all(r.detail and r.source.level=='primary' and not r.original
                    for r in value.brief+value.products+value.segments+value.drivers))
                expected=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
                self.assertEqual([r.model_dump() for r in value.revenue_mix],
                    [RevenueLine.model_validate(r).model_dump() for r in expected])
                self.assertEqual(enrich(value).model_dump(),value.model_dump())
                self.assertNotIn('wikipedia',str(value.model_dump()).lower())
                self.assertNotEqual(issuer(symbol).group,'pending')
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)
        for symbol in ('WBI','GPOR','DHT','XOM'):
            self.assertTrue(enrichment(symbol)['brief'])

    def test_report_totals_keep_different_bases_and_partial_breakdowns(self):
        expected={'BSM':422328000,'DMLP':152832000,'KRP':321739000,
            'NRP':202340000,'TPL':798190000,'VNOM':1346000000,'CKX':838543,
            'MNR':1175390000,'MXC':6561324,'LB':199093000,'PNRG':185909000}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS),69)
        for symbol,total in expected.items():
            with self.subTest(symbol=symbol):
                rows=present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
                self.assertEqual(sum(r['value'] for r in rows if r['group']=='product'),total)
                self.assertEqual(rows,present_revenue(rows,symbol))
                self.assertTrue(all(r['parent'] is None for r in rows))
        bsm=REPORTS['BSM']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in bsm),469919000)
        pnrg=REPORTS['PNRG']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in pnrg),189052000)
        self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in pnrg))
        self.assertEqual(len(REPORTS['LB']['revenue_mix']),10)
        self.assertEqual(issuer('MNR').group,'upstream')
        self.assertEqual(issuer('NRP').group,'coal-minerals')
        self.assertEqual(issuer('TPL').group,'surface-land')
        self.assertEqual(issuer('BSM').group,'mineral-royalty')

    def test_noninline_trusts_use_manual_tables_and_fiscal_dates(self):
        self.assertEqual(PERIODS['NRT'],('2024-11-01','2025-10-31'))
        for symbol,rows in REVENUE.items():
            for row in rows:
                RevenueLine.model_validate(row)
                self.assertEqual((row['start'],row['end']),PERIODS[symbol])
                self.assertTrue(row['member'].startswith('table:'))
                self.assertTrue(row['metric'].startswith('table:'))
                self.assertTrue(row['total'] is None and row['share_exclusion'])
                self.assertIn('#',row['source']['url'])
            for row in FINANCIALS[symbol]:
                Financial.model_validate(row)
                self.assertNotIn('XBRL',row['source']['label'])
                self.assertEqual(row['period'].split(' ~ ')[-1],PERIODS[symbol][1])
        nrt=REVENUE['NRT']
        for group in ('product','geography','revenue_type'):
            self.assertEqual(sum(r['value'] for r in nrt if r['group']==group),8649904)
        self.assertEqual(FINANCIALS['NRT'][0]['value']-8649904,190)
        self.assertIn('1 USD',REVENUE['PBT'][0]['share_exclusion'])

    def test_actual_roles_do_not_turn_into_guessed_ownership_or_completed_deals(self):
        self.assertFalse(any(r['symbol']=='WBI' and r['kind']=='subsidiary' for r in EDGES['LB']))
        self.assertFalse(any(r['symbol']=='EOG' and r['kind']=='customer' for r in EDGES['LB']))
        self.assertTrue(any(r['symbol']=='WBI' and r['kind']=='customer' for r in EDGES['LB']))
        self.assertTrue(any(r['kind']=='partner' and r['registry_id']=='sisecam-wyoming-nrp' for r in EDGES['NRP']))
        self.assertFalse(any(r['kind']=='subsidiary' and r['registry_id']=='dmlp-operating' for r in EDGES['DMLP']))
        self.assertFalse(any(r['kind']=='parent' for r in EDGES['PBT']))
        self.assertIn('2026-09-18',{r['source']['as_of'] for r in PUBLIC['PBT']['brief']})
        self.assertIn('10월13일',str(PUBLIC['LB']['brief']))
        self.assertIn('예정 상태',str(PUBLIC['LB']['brief']))
        self.assertIn('14%',PUBLIC['BSM']['brief'][2]['detail'])
        self.assertIn('2024',PUBLIC['BSM']['brief'][2]['detail'])
        self.assertNotIn('netherland-sewell-land',PRIVATE)

    def test_shared_legal_entities_have_direct_and_reverse_navigation(self):
        with tempfile.TemporaryDirectory() as temp:
            graph=CompanyGraph(SimpleNamespace(personal_local_mode=True,production=False,
                                               dataset_dir=Path(temp)/'data'))
            for symbol in (*SYMBOLS,'WBI','GPOR'):
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in (*PRIVATE,'nsai-reserve-engineering','cawley-gillespie'):
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol,key,kind,reverse in [
                ('CRT','simcoe-mach','partner','partner'),
                ('MNR','simcoe-mach','subsidiary','parent'),
                ('MNR','simlog-mach','subsidiary','parent'),
                ('MNR','nsai-reserve-engineering','supplier','customer'),
                ('KRP','rivercrest-ii-land','transaction','transaction'),
                ('PBT','argent-trust','supplier','customer'),
                ('PBT','new-pbt-land','transaction','transaction'),
                ('NRP','sisecam-wyoming-nrp','partner','partner')]:
                root=graph.by_symbol(symbol)
                edge=next(r for r in graph.relations(root['id']) if r['kind']==kind
                    and graph.entity(r['target_id'])['registry_id']==key)
                target=graph.entity(edge['target_id'])
                self.assertTrue(target['profile']['brief'])
                back=next(r for r in graph.relations(target['id'])
                    if r['target_id']==root['id'] and r['kind']==reverse)
                self.assertEqual(back['source'],edge['source'])
            lb=graph.by_symbol('LB');wbi=graph.by_symbol('WBI')
            self.assertEqual(len([r for r in graph.relations(lb['id'])
                if r['target_id']==wbi['id'] and r['kind']=='customer']),1)
