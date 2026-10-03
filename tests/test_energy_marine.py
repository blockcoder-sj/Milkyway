"""Historical issuer scope, JV assets and original leaf tables stay visible."""
import datetime as dt
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_financial_archive import archive, validate_archive
from cloud_app.company_energy_marine import EDGES, PRIVATE, PUBLIC, SYMBOLS
from cloud_app.company_energy_marine_revenue import COORDINATES, DOCUMENTS, METRICS, canonical, dimensions
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge, RevenueLine
from cloud_app.energy_issuers import issuer
from tests.test_company_revenue import context, doc, fact

HEADER = ('<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric>'
          '<ix:nonNumeric name="dei:DocumentPeriodEndDate">2025-12-31</ix:nonNumeric>')


class MarineResearchTests(unittest.TestCase):
    def test_nine_profiles_and_all_views_use_original_totals(self):
        totals = {'NE': 3285568000, 'RIG': 3965000000, 'SDRL': 1437000000,
            'VAL': 2369000000, 'TDW': 1352786000, 'SMHI': 227832000,
            'VTOL': 1490512000, 'HOS': 1291474000, 'XPRO': 1607095000}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS), 82)
        for symbol in SYMBOLS:
            value = enrich(CompanyKnowledge(symbol=symbol, name=symbol+' truncated'))
            self.assertEqual(value.name, PUBLIC[symbol]['name'])
            self.assertGreaterEqual(len(value.products), 7)
            self.assertGreaterEqual(len(value.brief), 6)
            self.assertTrue(value.financials and value.financial_context and value.relations)
            self.assertTrue(value.drivers and value.segments)
            self.assertEqual(value.model_dump(), enrich(value).model_dump())
            self.assertNotEqual(issuer(symbol).group, 'pending')
            rows = present_revenue(REPORTS[symbol]['revenue_mix'], symbol)
            self.assertEqual([r.model_dump() for r in value.revenue_mix],
                [RevenueLine.model_validate(r).model_dump() for r in rows])
            for group in {r['group'] for r in rows}:
                self.assertEqual(sum(r['value'] for r in rows if r['group'] == group), totals[symbol])
            self.assertEqual(rows, present_revenue(rows, symbol))
        for symbol in ('HOS', 'XPRO'):
            self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in REPORTS[symbol]['revenue_mix']))
        excluded = {'HOS': 'country:GB', 'VAL': 'val:AROMember', 'NE': 'us-gaap:OilAndGasServiceMember'}
        for symbol, member in excluded.items():
            self.assertFalse(any(r['member'] == member for r in REPORTS[symbol]['revenue_mix']))
        self.assertFalse(any('Sonadrill' in r['member'] for r in REPORTS['SDRL']['revenue_mix']))

    def test_conditional_deals_and_vessel_custody_are_not_completed_ownership(self):
        self.assertTrue(any(r['symbol'] == 'VAL' and r['kind'] == 'transaction' for r in EDGES['RIG']))
        self.assertFalse(any(r['symbol'] == 'VAL' and r['kind'] in {'subsidiary', 'owner'} for r in EDGES['RIG']))
        self.assertIn('proposed', PUBLIC['RIG']['brief'][-1]['detail'])
        self.assertIn('2027 Q2', PUBLIC['HOS']['brief'][-1]['detail'])
        self.assertIn('익명', PUBLIC['HOS']['brief'][-1]['detail'])
        self.assertIn('실제 취득', PUBLIC['XPRO']['brief'][-1]['title'])
        self.assertTrue(any(r['registry_id'] == 'sea1-helix' and r['kind'] == 'supplier' for r in EDGES['HOS']))
        self.assertFalse(any(r['registry_id'] == 'sea1-helix' and r['kind'] == 'subsidiary' for r in EDGES['HOS']))
        self.assertIn('50%', PRIVATE['aro-valaris']['description'])
        self.assertIn('45%', PRIVATE['seacor-marine-arabia']['description'])

    def test_corrected_card_source_preserves_cached_evidence_without_duplicate_text(self):
        card = deepcopy(PUBLIC['HOS']['segments'][0])
        old_source = deepcopy(PUBLIC['HOS']['description_source'])
        card['source'] = old_source
        other = {**card, 'detail': '다른 기간에 확인한 별도 설명'}
        value = enrich(CompanyKnowledge(symbol='HOS', name='HOS', segments=[card, other]))
        matching = [r for r in value.segments if r.title == card['title']
                    and r.detail == card['detail']]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].source.url, PUBLIC['HOS']['segments'][0]['source']['url'])
        self.assertTrue(any(r.detail == other['detail'] for r in value.segments))
        self.assertTrue(any(r.url == old_source['url'] for r in value.sources))
        self.assertEqual(value.model_dump(), enrich(value).model_dump())

    def test_exact_expro_predecessor_receipt_requires_scope_and_original_accession(self):
        raw = {'XPRO': deepcopy(archive()['XPRO'])}
        self.assertEqual(raw['XPRO']['cik'], '1575828')
        self.assertEqual(issuer('XPRO').cik, '2126198')
        self.assertEqual(raw['XPRO']['financials'][0]['value'], 1607095000)
        self.assertEqual(len(raw['XPRO']['financials']), 9)
        self.assertTrue(validate_archive(raw))
        for field in ('scope', 'document', 'issuer'):
            bad = deepcopy(raw)
            if field == 'scope': bad['XPRO']['financial_context'] = []
            if field == 'document':
                bad['XPRO']['annual']['url'] += 'other'
                for row in bad['XPRO']['financials']:
                    row['source']['url'] = bad['XPRO']['annual']['url']
            if field == 'issuer': bad['XPRO']['cik'] = issuer('XPRO').cik
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_archive(bad)

    def test_coordinates_reject_unknown_dimensions_currency_and_identity(self):
        for (symbol, cik, pairs), expected in COORDINATES.items():
            with self.subTest(symbol=symbol, member=expected[1]):
                pairs = sorted(pairs)
                self.assertEqual(dimensions(pairs, symbol, cik), expected)
                self.assertIsNone(dimensions(pairs+[pairs[0]], symbol, cik))
                self.assertIsNone(dimensions(pairs+[('x:Axis', 'x:Member')], symbol, cik))
                self.assertIsNone(dimensions(pairs, symbol, cik+1))
                self.assertIsNone(dimensions(pairs, 'OTHER', cik))
                extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                dates = dict(cik=str(cik), start='2025-01-01', end='2025-12-31')
                origin = dict(label='검토 원문', level='primary', as_of='2026-03-23', url=DOCUMENTS[symbol,cik])
                raw = doc(context('total', **dates)+context('part', pairs[0][1], axis=pairs[0][0], extra=extra, **dates),
                    HEADER+fact('total','100',metric=METRICS[symbol],scale=0)+fact('part','70',metric=METRICS[symbol],scale=0))
                row, = parse_revenue(raw, origin, symbol, dt.date(2026,10,4))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin,symbol),[])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin,symbol),[])

    def test_conflicts_are_removed_and_unrelated_documents_preserved(self):
        row = deepcopy(REPORTS['VAL']['revenue_mix'][0])
        self.assertEqual(canonical([row,{**row,'value':row['value']+1}],'VAL',314808),[])
        other = {**row,'source':{**row['source'],'url':row['source']['url']+'other'}}
        self.assertEqual(canonical([other],'VAL',314808),[other])

    def test_shared_entities_and_actual_reverse_navigation_remain_available(self):
        with tempfile.TemporaryDirectory() as temp:
            graph = CompanyGraph(SimpleNamespace(personal_local_mode=True, production=False, dataset_dir=Path(temp)/'data'))
            for symbol in SYMBOLS:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            for key in (*PRIVATE,'azule-energy','llog-exploration','saudi-aramco'):
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            for symbol,key,kind in [('VAL','azule-energy','customer'),('SDRL','llog-exploration','customer'),
                ('VTOL','sikorsky-bristow','supplier'),('HOS','helix-well-ops-uk','subsidiary'),
                ('XPRO','enhanced-drilling-expro','subsidiary'),('SMHI','seacor-marine-arabia','customer')]:
                root = graph.by_symbol(symbol)
                edge = next(r for r in graph.relations(root['id']) if r['kind'] == kind
                    and graph.entity(r['target_id'])['registry_id'] == key)
                target = graph.entity(edge['target_id'])
                self.assertTrue(target['profile']['brief'])
                self.assertTrue(any(r['target_id']==root['id'] for r in graph.relations(target['id'])))
