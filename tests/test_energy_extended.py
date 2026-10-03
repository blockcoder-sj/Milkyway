"""Edited business facts, actual contract stages and counterpart navigation."""
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_extended import PUBLIC, PRIVATE, EDGES, SYMBOLS
from cloud_app.company_energy_extended_revenue import DOCUMENTS
from cloud_app.company_energy_financial_archive import archive
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer


class ExtendedEnergyTests(unittest.TestCase):
    def test_sixteen_edited_primary_profiles_and_all_counterparts_validate(self):
        self.assertEqual(set(PUBLIC), set(SYMBOLS))
        self.assertEqual(len(PUBLIC), 16)
        for symbol, notes in PUBLIC.items():
            with self.subTest(symbol=symbol):
                value = enrich(CompanyKnowledge(symbol=symbol, **notes))
                self.assertGreaterEqual(len(value.brief), 6)
                self.assertGreaterEqual(len(value.products), 6)
                self.assertTrue(value.drivers and value.relations and value.financials and value.financial_context)
                self.assertEqual(enrich(value).model_dump(), value.model_dump())
                self.assertTrue(all(r.source.level == 'primary' and r.detail and not r.original
                                    for r in value.brief + value.products + value.drivers))
                self.assertNotIn('wikipedia', str(value.model_dump()).lower())
                self.assertEqual(issuer(symbol).group, 'gas-infrastructure' if symbol == 'WBI' else 'upstream')
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)

    def test_exact_original_receipts_currency_units_and_entity_scope(self):
        for symbol in SYMBOLS:
            record = archive()[symbol]
            self.assertEqual(record['annual']['url'], DOCUMENTS[symbol, int(record['cik'])])
            self.assertTrue(record['financial_context'])
            self.assertTrue(all(r['unit'] == ('CAD' if symbol == 'GFR' else 'USD') for r in record['financials']))
        self.assertEqual(archive()['GFR']['financials'][0]['value'], 584395000)
        self.assertEqual(archive()['GFR']['annual_period_end'], '2025-12-31')
        self.assertEqual(archive()['GFR']['parent_annual']['url'], REPORTS['GFR']['parent_annual']['url'])
        self.assertEqual(archive()['EPSN']['financials'][0]['value'], 51587556)

    def test_reported_product_and_geography_sums_preserve_signed_values_without_subtotals(self):
        expected = {'INR': ('product',350375000), 'GFR':('product',603303000),
            'EGY':('geography',359272000), 'GPRK':('geography',492518000),
            'GTE':('product',596713000), 'KOS':('geography',1297846000),
            'TALO':('product',1780070000), 'WTI':('product',501462000),
            'DEC':('product',1611455000), 'REPX':('product',391980000),
            'HPK':('product',863359000), 'SD':('product',156357000),
            'PED':('product',45751000), 'EPSN':('product',51587556),
            'TXO':('product',363147000), 'WBI':('product',525553000)}
        for symbol, (group, total) in expected.items():
            rows = present_revenue(REPORTS[symbol]['revenue_mix'], symbol)
            with self.subTest(symbol=symbol):
                self.assertEqual(sum(r['value'] for r in rows if r['group'] == group), total)
                self.assertFalse(any('ReportableSegment' in r['member'] for r in rows))
        repx = REPORTS['REPX']['revenue_mix']
        self.assertEqual(sorted(r['value'] for r in repx if r['value'] < 0), [-3322000,-3039000])
        self.assertTrue(all(r['total'] is None and r.get('share_exclusion') for r in repx))
        epsn = REPORTS['EPSN']['revenue_mix']
        self.assertTrue(all(r['includes_intersegment'] and r['total'] is None for r in epsn if r['group'] == 'segment'))
        self.assertEqual(len([r for r in REPORTS['EGY']['revenue_mix'] if r['group'] == 'geography']),4)

    def test_closed_and_pending_transactions_and_contract_roles_stay_distinct(self):
        pending, = [e for e in EDGES['GTE'] if e['kind'] == 'transaction']
        self.assertIn('미완료',pending['detail'])
        self.assertIn('10월9일',str(PUBLIC['GTE']['brief']))
        talos, = [e for e in EDGES['TALO'] if e['kind'] == 'transaction']
        self.assertIn('2026-09-22 실제 취득 완료',talos['detail'])
        self.assertTrue(any(e['symbol']=='SDRL' and e['kind']=='supplier' for e in EDGES['TALO']))
        self.assertTrue(any(e['symbol']=='LB' and e['kind']=='supplier' for e in EDGES['WBI']))
        self.assertTrue(any(e['registry_id']=='ctoc-txo' and '완료' in e['detail'] for e in EDGES['TXO']))
        self.assertFalse(any(e['kind']=='customer' for e in EDGES['PED']))
        self.assertFalse(any(e['kind']=='subsidiary' and e['registry_id'] in {'rpc-power-riley','monza-energy-wt'}
                             for rows in EDGES.values() for e in rows))

    def test_counterparts_have_pages_reverse_roles_and_source_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = CompanyGraph(SimpleNamespace(personal_local_mode=True, production=False,
                dataset_dir=Path(directory)/'data'))
            for symbol in SYMBOLS:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in PRIVATE:
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol, registry, reverse in [('GFR','trafigura-canada-greenfire','supplier'),
                ('GTE','maurel-prom-grantierra','transaction'), ('TXO','ctoc-txo','transaction'),
                ('EPSN','arm-epsilon','customer'), ('WBI','ranger-waterbridge','parent')]:
                root = graph.by_symbol(symbol)
                edge = next(e for e in graph.relations(root['id'])
                            if graph.entity(e['target_id'])['registry_id']==registry and
                               (symbol!='GFR' or e['kind']=='customer'))
                target = graph.entity(edge['target_id'])
                self.assertTrue(target['profile']['brief'])
                back = next(e for e in graph.relations(target['id'])
                            if e['target_id']==root['id'] and e['kind']==reverse)
                self.assertEqual(back['source'],edge['source'])

    def test_edited_sections_remove_only_own_parser_excerpts_and_keep_the_citations(self):
        source = {**PUBLIC['INR']['description_source'], 'url':PUBLIC['INR']['description_source']['url']+'#old-product'}
        old = dict(title='공시 제품·서비스 원문', detail='', original='We offer gathered and processed gas services.', source=source)
        manual = {**old, 'detail':'수동 검토한 별도 보충 정보입니다.'}
        other = deepcopy(old)
        other['source']['url'] = other['source']['url'].replace('/2029118/', '/99999/')
        segment = {**old, 'title':'공시 사업 구성 원문'}
        result = enrich(CompanyKnowledge(symbol='INR',name='Infinity',products=[old,manual,other],segments=[segment]))
        self.assertNotIn(old,[r.model_dump(mode='json') for r in result.products])
        self.assertFalse(result.segments)
        self.assertIn(source,[r.model_dump(mode='json') for r in result.sources])
        self.assertTrue(any(r.detail==manual['detail'] for r in result.products))
        self.assertTrue(any('/99999/' in r.source.url for r in result.products))
        self.assertEqual(enrich(result).model_dump(),result.model_dump())
        unreviewed = enrich(CompanyKnowledge(symbol='UNKNOWN',name='Unknown',products=[old],segments=[segment]))
        self.assertTrue(unreviewed.products and unreviewed.segments)
