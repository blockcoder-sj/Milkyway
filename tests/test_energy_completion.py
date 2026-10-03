"""Sector-wide public evidence coverage and accounting context boundaries."""
import unittest
from cloud_app.company_catalog import enrich
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.company_energy_review import FINANCIAL_SYMBOLS, COMPARISONS
from cloud_app.company_research_catalog import PUBLIC_COMPANIES, REGISTERED_TICKERS
from cloud_app.energy_issuers import registry


class EnergyCompletionTests(unittest.TestCase):
    def test_all_issuers_have_dated_reading_notes_and_accounting_scope(self):
        rows = registry().rows
        self.assertEqual(len(rows), 213)
        for entry in rows:
            with self.subTest(symbol=entry.symbol):
                value = enrich(CompanyKnowledge(symbol=entry.symbol, name=entry.name))
                self.assertNotEqual(entry.group, 'pending')
                for field in ('brief', 'products', 'drivers', 'financials', 'financial_context', 'relations'):
                    self.assertTrue(getattr(value, field), field)
                self.assertEqual(enrich(value).model_dump(), value.model_dump())
                for field in ('brief', 'products', 'drivers', 'financial_context'):
                    for note in PUBLIC_COMPANIES[entry.symbol].get(field, []):
                        self.assertEqual(note['source']['level'], 'primary')
                        self.assertTrue(note['source']['url'] and note['source']['as_of'])

    def test_initial_accounting_context_keeps_exact_document_scope_and_analysis_is_labelled(self):
        for symbol in FINANCIAL_SYMBOLS:
            profile = PUBLIC_COMPANIES[symbol]
            revenue = next(row for row in profile['brief'] if row['title'] == '매출이 생기는 구조')
            scope = next(row for row in profile['financial_context'] if row['title'] == '연간 재무·매출 비교 범위')
            self.assertEqual((scope['detail'], scope['source']), (revenue['detail'], revenue['source']))
        for symbol in COMPARISONS:
            card = next(row for row in PUBLIC_COMPANIES[symbol]['drivers'] if row['title'] == '경쟁을 비교하는 기준 · 사업 분석')
            self.assertIn('비교 기준', card['detail'])
            self.assertIn('사업 분석', card['title'])

    def test_parkland_acquisition_and_listing_are_separate_events(self):
        card = next(row for row in PUBLIC_COMPANIES['SUNC']['products'] if row['title'] == 'Parkland 정유·유통')
        self.assertIn('10월 31일', card['detail'])
        self.assertIn('11월 6일', card['detail'])

    def test_restored_registry_bookmark_gets_the_same_public_financial_archive(self):
        for key, symbol in REGISTERED_TICKERS.items():
            direct = enrich(CompanyKnowledge(symbol=symbol, name=symbol))
            if not direct.financials:
                continue
            with self.subTest(registry=key, symbol=symbol):
                restored = enrich(CompanyKnowledge(registry_id=key, name='Earlier private role'))
                self.assertEqual(restored.symbol, symbol)
                self.assertEqual(restored.financials, direct.financials)
                self.assertEqual(restored.financial_context, direct.financial_context)
                self.assertEqual(enrich(restored).model_dump(), restored.model_dump())

    def test_reviewed_accounting_scope_replaces_same_document_cache_but_preserves_history(self):
        from copy import deepcopy
        current = enrich(CompanyKnowledge(symbol='NXE', name='NXE'))
        obsolete = deepcopy(current.financial_context[0])
        obsolete.detail = 'Earlier missing-coordinate explanation'
        historic = deepcopy(obsolete)
        historic.source.as_of = '2025-03-04'
        renamed = deepcopy(current.financial_context[0])
        renamed.title = 'Earlier presentation title'
        restored = enrich(CompanyKnowledge(symbol='NXE', name='NXE', financial_context=[obsolete, historic, renamed]))
        self.assertFalse(any(r.detail == obsolete.detail and r.source.as_of == '2026-03-04'
                             for r in restored.financial_context))
        self.assertIn(historic, restored.financial_context)
        self.assertNotIn(renamed, restored.financial_context)

    def test_completed_purchase_does_not_create_a_surviving_target_subsidiary(self):
        from cloud_app.company_energy_current import EDGES, PRIVATE
        target = EDGES['MGY'][0]
        seller = EDGES['MGY'][1]
        self.assertEqual(target['kind'], 'transaction')
        self.assertNotEqual(target['registry_id'], seller['registry_id'])
        self.assertIn('합병', target['detail'])
        self.assertIn('현재 독립 법인', PRIVATE[target['registry_id']]['brief'][0]['detail'])
        current = enrich(CompanyKnowledge(symbol='MGY', name='MGY'))
        self.assertIn('2025', current.financials[0].period)
        self.assertTrue(any('예상치' in x.detail and '159~161' in x.detail for x in current.drivers))

    def test_fiscal_quarters_and_operational_quantities_keep_their_denominators(self):
        from cloud_app.company_energy_current import CURRENT
        self.assertIn('FY2026 Q3', CURRENT['HP'][0]['title'])
        self.assertIn('9개월', CURRENT['SGU'][0]['detail'])
        self.assertIn('비GAAP', CURRENT['CNX'][0]['detail'])
        self.assertIn('82%', CURRENT['VTS'][0]['detail'])
        self.assertIn('직접 운영 자산', CURRENT['VTS'][0]['detail'])
        self.assertIn('시운전', CURRENT['TTE'][0]['detail'])
        self.assertIn('완료 조건', CURRENT['YPF'][0]['detail'])
        self.assertIn('확정하지 않습니다', CURRENT['NC'][0]['detail'])
