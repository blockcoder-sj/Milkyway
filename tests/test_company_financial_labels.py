"""Accounting metric names survive parsing, legacy enrichment and repeat reads."""
from copy import deepcopy
import unittest

from cloud_app.company_catalog import enrich, editorial_for
from cloud_app.company_financial_labels import presented
from cloud_app.company_feed import parse_sec
from tests.test_company_research import submissions, NOW


class FinancialLabelTests(unittest.TestCase):
    def test_contract_revenue_is_not_labelled_total_company_sales(self):
        metric = 'RevenueFromContractWithCustomerExcludingAssessedTax'
        record = dict(form='10-K', fp='FY', start='2025-01-01', end='2025-12-31',
                      filed='2026-02-01', val=123)
        facts = dict(cik=320193, facts={'us-gaap': {metric: {'units': {'USD': [record]}}}})
        result = parse_sec(submissions(), facts, 'AAPL', NOW)['financials'][0]
        self.assertEqual(result['label'], '고객 계약 매출 · 부과세 제외')
        self.assertEqual(result['value'], 123)

    def test_legacy_labels_change_without_mutation_or_value_replacement(self):
        row = dict(label='매출', value=19464000000, unit='USD', period='2025',
                   source=dict(label='SEC XBRL · RevenueFromContractWithCustomerExcludingAssessedTax',
                               url='https://data.sec.gov/api/xbrl/companyfacts/CIK0000003570.json'))
        original = deepcopy(row)
        result = enrich(dict(symbol='LNG', name='Cheniere', financials=[row]))
        self.assertEqual(row, original)
        self.assertEqual(result.financials[0].value, 19464000000)
        self.assertIn('고객 계약', result.financials[0].label)
        self.assertEqual(enrich(result).model_dump(), result.model_dump())

    def test_unrelated_metrics_and_current_exxon_identity(self):
        rows = [dict(label='매출', source={'label': 'SEC XBRL · Revenues'}),
                dict(label='영업이익', source={'label': 'SEC XBRL · OperatingIncomeLoss'})]
        self.assertEqual(presented(rows), rows)
        self.assertEqual(editorial_for('XOM')['cik'], '2115436')


if __name__ == '__main__':
    unittest.main()
