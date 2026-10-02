"""Annual source identity, signed figures and accounting scope, offline."""
import datetime as dt
import unittest

from cloud_app.company_annual_financials import parse_annual_financials
from cloud_app.company_revenue import number
from cloud_app.company_filings import document
from cloud_app.company_schemas import Financial
from tests.test_company_revenue import context, doc, fact, ORIGIN


def annual(contexts, facts, period='2026-01-25', form='10-K', attrs=''):
    header = (f'<ix:nonNumeric name="dei:DocumentType">{form}</ix:nonNumeric>'
              f'<ix:nonNumeric name="dei:DocumentPeriodEndDate" {attrs}>{period}</ix:nonNumeric>')
    return doc(contexts, header + facts)


class AnnualFinancialTests(unittest.TestCase):
    def parse(self, raw, origin=None, cik=1045810):
        return parse_annual_financials(raw, origin or ORIGIN, cik, dt.date(2026, 10, 3))

    def test_consolidated_signed_figures_keep_currency_period_and_original_anchor(self):
        instant = context('balance').replace('<xbrli:startDate>2025-01-27</xbrli:startDate>'
            '<xbrli:endDate>2026-01-25</xbrli:endDate>', '<xbrli:instant>2026-01-25</xbrli:instant>')
        raw = annual(context('year') + instant, fact('year', '100') +
            fact('year', '5', metric='us-gaap:NetIncomeLoss', attrs='sign="-"', anchor='loss') +
            fact('balance', '80', metric='us-gaap:Assets', anchor='assets'))
        rows = self.parse(raw)
        self.assertEqual([r['value'] for r in rows], [100000000, -5000000, 80000000])
        self.assertEqual(rows[1]['label'], '지배기업 귀속 순이익')
        self.assertEqual(rows[2]['period'], '2026-01-25')
        self.assertTrue(rows[1]['source']['url'].endswith('#loss'))
        for row in rows:
            Financial.model_validate(row)
        signed = document(fact('year', '5', attrs='sign="-"')).find('ix:nonfraction')
        self.assertIsNone(number(signed))
        self.assertEqual(number(signed, signed=True), -5000000)

    def test_contract_revenue_is_not_labeled_total_company_sales(self):
        raw = annual(context('year'), fact('year', '90',
            metric='us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'))
        row, = self.parse(raw)
        self.assertEqual(row['label'], '고객 계약 매출 · 부과세 제외')
        self.assertEqual(self.parse(raw.replace('ExcludingAssessedTax', 'IncludingAssessedTax'))[0]['label'],
                         '고객 계약 매출 · 부과세 포함')

    def test_reporting_period_supports_nested_english_month_date(self):
        raw = annual(context('year'), fact('year', '100'),
            period='<span>January 25</span>, <span>2026</span>',
            attrs='format="ixt:date-monthname-day-year-en"')
        self.assertEqual(len(self.parse(raw)), 1)
        self.assertEqual(len(self.parse(raw.replace('January', 'Jan'))), 1)
        self.assertEqual(self.parse(raw.replace('January', 'NotAMonth')), [])
        self.assertEqual(self.parse(raw.replace('date-monthname-day-year-en', 'unknown')), [])

    def test_source_and_context_identity_must_match_checked_issuer(self):
        raw = annual(context('year'), fact('year', '100'))
        self.assertEqual(self.parse(raw, cik=87347), [])
        self.assertEqual(self.parse(raw.replace('1045810', '87347')), [])
        self.assertEqual(self.parse(raw, cik=True), [])
        self.assertEqual(self.parse(raw, origin={**ORIGIN, 'url': ORIGIN['url'].replace('www.sec.gov', 'evil.test')}), [])

    def test_segments_subsidiaries_typed_axes_and_quarters_never_become_annual_total(self):
        for member, extra in [
            ('us-gaap:ProductMember', ''),
            (None, '<xbrldi:typedMember dimension="x:EntityAxis"><x:Entity>Child</x:Entity></xbrldi:typedMember>'),
        ]:
            raw = annual(context('year', member, extra=extra), fact('year', '100'))
            self.assertEqual(self.parse(raw), [])
        quarter = annual(context('year'), fact('year', '100'), form='10-Q')
        self.assertEqual(self.parse(quarter), [])
        short = annual(context('year', start='2025-10-26'), fact('year', '100'))
        self.assertEqual(self.parse(short), [])

    def test_ambiguous_values_or_currencies_need_review_instead_of_guessing(self):
        for extra in [fact('year', '90'), fact('year', '100', unit='eur')]:
            self.assertEqual(self.parse(annual(context('year'), fact('year', '100') + extra)), [])
        self.assertEqual(len(self.parse(annual(context('year'), fact('year', '100') * 2))), 1)

    def test_future_and_conflicting_report_periods_are_rejected(self):
        raw = annual(context('year'), fact('year', '100'))
        other = '<ix:nonNumeric name="dei:DocumentPeriodEndDate">2025-12-31</ix:nonNumeric>'
        self.assertEqual(self.parse(raw.replace('</html>', other + '</html>')), [])
        self.assertEqual(self.parse(raw, origin={**ORIGIN, 'as_of': '2027-02-25'}), [])
        self.assertEqual(self.parse(raw.replace('2026-01-25', '2027-01-25')), [])

    def test_parent_and_total_equity_bases_are_kept_separate(self):
        instant = context('balance').replace('<xbrli:startDate>2025-01-27</xbrli:startDate>'
            '<xbrli:endDate>2026-01-25</xbrli:endDate>', '<xbrli:instant>2026-01-25</xbrli:instant>')
        raw = annual(instant, fact('balance', '50', metric='us-gaap:StockholdersEquity'))
        self.assertIn('비지배지분 제외', self.parse(raw)[0]['label'])
        total = raw.replace('us-gaap:StockholdersEquity',
                            'us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest')
        self.assertIn('비지배지분 포함', self.parse(total)[0]['label'])
        self.assertFalse(any(r['label'] == '총부채' for r in self.parse(raw)))


if __name__ == '__main__':
    unittest.main()
