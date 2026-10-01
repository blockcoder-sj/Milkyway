"""Reported annual slices; no live providers or AI calls."""
import datetime as dt
import unittest

from cloud_app.company_revenue import parse_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.company_retention import preserve_previous

ORIGIN = dict(label='SEC · 10-K', level='primary', as_of='2026-02-25',
    url='https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm')


def context(key, member=None, axis='srt:ProductOrServiceAxis', start='2025-01-27', end='2026-01-25', extra='', cik='1045810'):
    member = f'<xbrldi:explicitMember dimension="{axis}">{member}</xbrldi:explicitMember>' if member else ''
    return f'<xbrli:context id="{key}"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{cik}</xbrli:identifier><xbrli:segment>{member}{extra}</xbrli:segment></xbrli:entity><xbrli:period><xbrli:startDate>{start}</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate></xbrli:period></xbrli:context>'


def fact(ctx, value, metric='us-gaap:Revenues', scale=6, unit='usd', attrs='', anchor='f-1'):
    return f'<ix:nonFraction name="{metric}" contextRef="{ctx}" unitRef="{unit}" format="ixt:num-dot-decimal" scale="{scale}" id="{anchor}" {attrs}>{value}</ix:nonFraction>'


def doc(contexts, facts):
    return '<html><xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit><xbrli:unit id="eur"><xbrli:measure>iso4217:EUR</xbrli:measure></xbrli:unit>' + contexts + facts + '</html>'


class RevenueTests(unittest.TestCase):
    def parse(self, raw, symbol='NVDA'):
        return parse_revenue(raw, ORIGIN, symbol, dt.date(2026, 10, 1))

    def test_reported_units_denominator_hierarchy_and_latest_period(self):
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember')
            + context('c', 'nvda:ComputeMember') + context('n', 'nvda:NetworkingMember')
            + context('old', 'nvda:DataCenterMember', start='2024-01-27', end='2025-01-25'),
            fact('total', '200') + fact('p', '150') + fact('c', '100') + fact('n', '50') + fact('old', '90'))
        rows = self.parse(raw)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row['total'] == 200000000 for row in rows))
        self.assertTrue(all(row['end'] == '2026-01-25' for row in rows))
        child = next(row for row in rows if row['label'] == '컴퓨팅')
        self.assertEqual(child['parent'], 'nvda:DataCenterMember')
        self.assertEqual(child['value'], 100000000)
        self.assertTrue(child['source']['url'].endswith('#f-1'))
        self.assertEqual(len(CompanyKnowledge(symbol='NVDA', name='NVIDIA', revenue_mix=rows).revenue_mix), 3)

    def test_unknown_overlap_not_guessed_and_other_issuer_no_hierarchy(self):
        raw = doc(context('p', 'nvda:DataCenterMember') + context('c', 'nvda:ComputeMember')
            + context('n', 'nvda:NetworkingMember'), fact('p', '150') + fact('c', '100') + fact('n', '49'))
        self.assertTrue(all(row['parent'] is None for row in self.parse(raw)))
        raw = raw.replace('49<', '50<')
        self.assertTrue(all(row['parent'] is None for row in self.parse(raw, 'OTHER')))

    def test_alternate_product_service_split_is_a_separate_view(self):
        raw = doc(context('total') + context('p', 'msft:ServerProductsAndCloudServicesMember')
            + context('goods', 'us-gaap:ProductMember') + context('services', 'us-gaap:ServiceOtherMember'),
            fact('total', '200') + fact('p', '150') + fact('goods', '40') + fact('services', '160'))
        rows = self.parse(raw, 'MSFT')
        self.assertEqual(len([row for row in rows if row['group'] == 'product']), 1)
        self.assertEqual(len([row for row in rows if row['group'] == 'revenue_type']), 2)

    def test_no_wrong_currency_metric_period_or_dimensional_denominator(self):
        for denominator in [
            fact('total', '200', unit='eur'),
            fact('total', '200', metric='us-gaap:SalesRevenueNet'),
            fact('prior', '200'), fact('slice', '200'),
        ]:
            with self.subTest(denominator=denominator):
                raw = doc(context('total') + context('prior', start='2024-01-27', end='2025-01-25')
                    + context('slice', 'nvda:OtherMember') + context('p', 'nvda:DataCenterMember'),
                    fact('p', '150') + denominator)
                target = next(row for row in self.parse(raw) if row['member'] == 'nvda:DataCenterMember')
                self.assertIsNone(target['total'])

    def test_reject_multiple_typed_future_short_and_other_issuer_contexts(self):
        cases = [
            dict(extra='<xbrldi:explicitMember dimension="srt:MajorCustomersAxis">x:OtherMember</xbrldi:explicitMember>'),
            dict(extra='<xbrldi:typedMember dimension="x:Axis">value</xbrldi:typedMember>'),
            dict(end='2026-12-31'), dict(start='2025-12-01'), dict(cik='9999'),
            dict(axis='srt:MajorCustomersAxis'), dict(start='not-a-date'),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.parse(doc(context('p', 'nvda:DataCenterMember', **args), fact('p', '150'))), [])

    def test_numeric_and_conflicting_fact_guards(self):
        for value, attrs, scale in [('NaN', '', 6), ('1e9', '', 6), ('1,50', '', 6),
            ('150', 'xsi:nil="true"', 6), ('150', 'sign="-"', 6), ('150', '', 20),
            ('99999999999999999', '', 6)]:
            with self.subTest(value=value, attrs=attrs, scale=scale):
                self.assertEqual(self.parse(doc(context('p', 'nvda:DataCenterMember'), fact('p', value, attrs=attrs, scale=scale))), [])
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember'),
            fact('total', '200') + fact('total', '201') + fact('p', '150'))
        self.assertIsNone(self.parse(raw)[0]['total'])
        raw += fact('p', '151')
        self.assertEqual(self.parse(raw), [])

    def test_slice_larger_than_consolidated_total_has_no_percentage(self):
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember'), fact('total', '100') + fact('p', '150'))
        self.assertIsNone(self.parse(raw)[0]['total'])

    def test_failed_annual_report_preserves_old_revenue_only(self):
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember'), fact('total', '200') + fact('p', '150'))
        old = CompanyKnowledge(symbol='NVDA', name='NVIDIA', revenue_mix=self.parse(raw))
        new = CompanyKnowledge(symbol='NVDA', name='NVIDIA', errors=['failed'], unavailable_sources=['sec_report'])
        preserve_previous(new, old)
        self.assertEqual(new.revenue_mix, old.revenue_mix)
        fresh = CompanyKnowledge(symbol='NVDA', name='NVIDIA')
        preserve_previous(fresh, old)
        self.assertFalse(fresh.revenue_mix)


if __name__ == '__main__':
    unittest.main()
