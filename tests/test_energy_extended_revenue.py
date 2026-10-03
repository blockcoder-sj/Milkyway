"""Reviewed complete coordinates, duplicate tables and signed net receipts."""
from copy import deepcopy
import datetime as dt
import unittest

from pydantic import ValidationError

from cloud_app.company_energy_extended_revenue import COORDINATES, DOCUMENTS, dimensions
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import RevenueLine
from tests.test_company_revenue import context, doc, fact


def origin(symbol, cik):
    return dict(label='검토된 연차 원문', level='primary', as_of='2026-03-27',
                url=DOCUMENTS[symbol, cik])


def metric(symbol, group):
    if symbol in {'GFR', 'GPRK'}:
        return 'ifrs-full:Revenue'
    if symbol == 'EGY' or (symbol == 'INR' and group == 'revenue_type') or (symbol == 'KOS' and group == 'segment'):
        return 'us-gaap:Revenues'
    if symbol in {'TALO', 'PED', 'EPSN'}:
        return 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
    return 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'


class ExtendedRevenueTests(unittest.TestCase):
    def test_every_complete_coordinate_is_issuer_bound_and_parser_supported(self):
        self.assertEqual(len(DOCUMENTS), 16)
        for (symbol, cik, pairs), expected in COORDINATES.items():
            with self.subTest(symbol=symbol, member=expected[1]):
                pairs = sorted(pairs)
                self.assertEqual(dimensions(pairs, symbol, cik), expected)
                self.assertIsNone(dimensions(pairs + [pairs[0]], symbol, cik))
                self.assertIsNone(dimensions(pairs + [('extra:Axis', 'extra:Member')], symbol, cik))
                self.assertIsNone(dimensions(pairs, symbol, cik + 1))
                self.assertIsNone(dimensions(pairs, 'OTHER', cik))
                extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>'
                                for a, m in pairs[1:])
                dates = dict(cik=str(cik), start='2025-01-01', end='2025-12-31')
                raw = doc(context('total', **dates) + context('part', pairs[0][1],
                          axis=pairs[0][0], extra=extra, **dates),
                          fact('total', '100', metric=metric(symbol, expected[0]), scale=0)
                          + fact('part', '70', metric=metric(symbol, expected[0]), scale=0))
                row, = parse_revenue(raw, origin(symbol, cik), symbol, dt.date(2026, 10, 3))
                self.assertEqual((row['group'], row['member'], row['value']), (*expected, 70))
                RevenueLine.model_validate(row)
                self.assertEqual(parse_revenue(raw.replace(str(cik), str(cik + 1)), origin(symbol, cik), symbol), [])

    def negative_raw(self, member='srt:NaturalGasReservesMember', year='2025', cik='1001614'):
        dates = dict(cik=cik, start=year+'-01-01', end=year+'-12-31')
        tag = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
        return doc(context('total', **dates) + context('gas', member, **dates),
                   fact('total', '391,980', metric=tag, scale=3) + fact('gas', '3,322', metric=tag, scale=3, attrs='sign="-"'))

    def test_negative_net_gas_and_ngl_are_preserved_only_at_reviewed_annual_coordinates(self):
        source = origin('REPX', 1001614)
        for member in ('srt:NaturalGasReservesMember', 'srt:NaturalGasLiquidsReservesMember'):
            row, = parse_revenue(self.negative_raw(member), source, 'REPX')
            self.assertEqual(row['value'], -3322000)
            self.assertIsNone(row['total'])
            self.assertIn('운송비', row['share_exclusion'])
            RevenueLine.model_validate(row)
        for raw, other, symbol in [
            (self.negative_raw(year='2024'), source, 'REPX'),
            (self.negative_raw(member='srt:OilReservesMember'), source, 'REPX'),
            (self.negative_raw(), source, 'OTHER'),
            (self.negative_raw(), {**source, 'url':source['url'].replace('rep-20251231', 'other')}, 'REPX'),
            (self.negative_raw(cik='1001615'), source, 'REPX'),
        ]:
            with self.subTest(symbol=symbol, raw=raw[-120:]):
                self.assertEqual(parse_revenue(raw, other, symbol), [])

    def test_negative_schema_requires_explanation_and_no_percentage_denominator(self):
        row, = parse_revenue(self.negative_raw(), origin('REPX', 1001614), 'REPX')
        for change in ({'total':391980000}, {'share_exclusion':None}, {'share_exclusion':''}, {'value':float('nan')}):
            with self.assertRaises(ValidationError):
                RevenueLine.model_validate({**row, **change})

    def test_egy_repeated_geography_tables_do_not_double_count_or_choose_conflicts(self):
        source = origin('EGY', 894627)
        member = 'egy:GabonSegmentMember'
        dates = dict(cik='894627', start='2025-01-01', end='2025-12-31')
        qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        contexts = context('total', **dates) + context('one', member, axis='us-gaap:StatementBusinessSegmentsAxis', **dates)
        contexts += context('two', member, axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier, **dates)
        raw = doc(contexts, fact('total','359,272',scale=3) + fact('one','181,738',scale=3,anchor='a') + fact('two','181,738',scale=3,anchor='b'))
        row, = parse_revenue(raw, source, 'EGY')
        self.assertEqual((row['group'], row['value']), ('geography', 181738000))
        self.assertEqual(len(present_revenue([row, deepcopy(row)], 'EGY')), 1)
        # Older cache records may predate the metric filter in parse_revenue.
        # Contract-only income must not join EGY's derivative-inclusive view.
        contract = {**deepcopy(row), 'value':16528000,
                    'metric':'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'}
        self.assertEqual(present_revenue([row, contract], 'EGY'), [row])
        unrelated = {**contract, 'source':{**source, 'url':source['url'].replace('egy-20251231','other')}}
        self.assertEqual(len(present_revenue([row, unrelated], 'EGY')), 2)
        self.assertEqual(parse_revenue(raw.replace('>181,738</ix:nonFraction>', '>181,737</ix:nonFraction>', 1), source, 'EGY'), [])

    def test_txo_prior_single_segment_is_not_a_current_breakdown(self):
        source = origin('TXO', 1559432)
        row = dict(group='segment', member='txo:ReportableSegmentMember', label='단일 보고 부문 합계',
                   value=282810000, unit='USD', start='2024-01-01', end='2024-12-31',
                   total=282810000, metric='us-gaap:Revenues', source=source)
        self.assertEqual(present_revenue([row], 'TXO'), [])
        changed = {**row, 'source':{**source, 'url':source['url'].replace('txo-20251231','other')}}
        self.assertEqual(len(present_revenue([changed], 'TXO')), 1)
