"""Service tables do not combine incompatible subtotals or invent identities."""
import datetime as dt
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_energy_specialists import EDGES, PRIVATE, PUBLIC, SYMBOLS
from cloud_app.company_energy_specialist_revenue import (
    COORDINATES, DOCUMENTS, CONTRACT, dimensions, signed_value, canonical)
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge, RevenueLine
from cloud_app.energy_issuers import issuer
from tests.test_company_revenue import context, doc, fact


def original(symbol, cik):
    return dict(label='검토 원문', level='primary', as_of='2026-03-23', url=DOCUMENTS[symbol, cik])


HEADER = ('<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric>'
          '<ix:nonNumeric name="dei:DocumentPeriodEndDate">2025-12-31</ix:nonNumeric>')


class SpecialistResearchTests(unittest.TestCase):
    def test_five_profiles_enrich_and_preserve_separate_views(self):
        totals = {'CLB': 526520000, 'FET': 791474000, 'NESR': 1324047000,
                  'OII': 2784156000, 'OIS': 668988000}
        self.assertEqual(sum(len(REPORTS[s]['revenue_mix']) for s in SYMBOLS), 49)
        for symbol in SYMBOLS:
            value = enrich(CompanyKnowledge(symbol=symbol, name=symbol+' partial provider'))
            self.assertEqual(value.name, PUBLIC[symbol]['name'])
            self.assertTrue(value.financials and value.financial_context and value.relations)
            self.assertGreaterEqual(len(value.products), 7)
            self.assertGreaterEqual(len(value.brief), 6)
            self.assertTrue(value.drivers and value.segments)
            self.assertEqual(enrich(value).model_dump(), value.model_dump())
            self.assertNotEqual(issuer(symbol).group, 'pending')
            rows = present_revenue(REPORTS[symbol]['revenue_mix'], symbol)
            self.assertEqual([r.model_dump() for r in value.revenue_mix],
                [RevenueLine.model_validate(r).model_dump() for r in rows])
            self.assertEqual(rows, present_revenue(rows, symbol))
            for group in {r['group'] for r in rows}:
                self.assertEqual(sum(r['value'] for r in rows if r['group'] == group), totals[symbol])
            for row in rows:
                RevenueLine.model_validate(row)
                self.assertIsNone(row['parent'])
        fet = REPORTS['FET']['revenue_mix']
        self.assertEqual([r['value'] for r in fet if r['value'] < 0], [-502000])
        self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in fet if r['group'] == 'product'))
        self.assertFalse(any(r['member'] == 'us-gaap:NonUsMember' for r in REPORTS['OII']['revenue_mix']))
        self.assertFalse(any('WdVonGonten' in r['member'] for r in REPORTS['NESR']['revenue_mix']))

    def test_counterparts_are_real_roles_and_anonymous_customers_stay_anonymous(self):
        self.assertEqual(len(PRIVATE), 6)
        self.assertFalse(any(r['kind'] == 'customer' for r in EDGES['NESR']))
        self.assertFalse(any(r['kind'] == 'subsidiary' for r in EDGES['FET']))
        self.assertIn('49%', PUBLIC['NESR']['brief'][2]['detail'])
        self.assertIn('12%', PUBLIC['OII']['brief'][2]['detail'])
        self.assertIn('2026', PUBLIC['OIS']['brief'][-1]['detail'])
        with tempfile.TemporaryDirectory() as temp:
            graph = CompanyGraph(SimpleNamespace(personal_local_mode=True, production=False,
                                                 dataset_dir=Path(temp)/'data'))
            for symbol in SYMBOLS:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol, name=symbol)), 'us_10')
            for key in PRIVATE:
                item = CompanyKnowledge(**private_profile(key))
                graph.ingest(item, 'us_10')
            for symbol in SYMBOLS:
                root = graph.by_symbol(symbol)
                for edge in graph.relations(root['id']):
                    target = graph.entity(edge['target_id'])
                    if target['registry_id'] in PRIVATE:
                        self.assertTrue(target['profile']['brief'])
                        self.assertTrue(any(back['target_id'] == root['id']
                            for back in graph.relations(target['id'])))

    def test_original_coordinates_require_exact_dimensions_and_currency(self):
        for (symbol, cik, pairs), expected in COORDINATES.items():
            with self.subTest(symbol=symbol, member=expected[1]):
                pairs = sorted(pairs)
                self.assertEqual(dimensions(pairs, symbol, cik), expected)
                self.assertIsNone(dimensions(pairs+[pairs[0]], symbol, cik))
                self.assertIsNone(dimensions(pairs+[('x:Axis', 'x:Member')], symbol, cik))
                self.assertIsNone(dimensions(pairs, symbol, cik+1))
                self.assertIsNone(dimensions(pairs, 'OTHER', cik))
                extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a, m in pairs[1:])
                tag = 'us-gaap:Revenues' if symbol == 'OII' else CONTRACT
                dates = dict(cik=str(cik), start='2025-01-01', end='2025-12-31')
                raw = doc(context('total', **dates) + context('part', pairs[0][1],
                    axis=pairs[0][0], extra=extra, **dates),
                    HEADER+fact('total', '100', metric=tag, scale=0)+fact('part', '70', metric=tag, scale=0))
                row, = parse_revenue(raw, original(symbol, cik), symbol, dt.date(2026, 10, 4))
                self.assertEqual((row['group'], row['member'], row['value']), (*expected, 70))
                self.assertEqual(parse_revenue(raw.replace(str(cik), str(cik+1)), original(symbol, cik), symbol), [])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"', 'unitRef="eur"'), original(symbol, cik), symbol), [])

    def test_signed_elimination_is_not_allowed_in_other_documents_or_periods(self):
        source = original('FET', 1401257)
        coordinate = ('2025-01-01', '2025-12-31', 'product', 'us-gaap:IntersegmentEliminationMember')
        self.assertTrue(signed_value(CONTRACT, coordinate, source, 'FET', 1401257))
        for ticker, cik, context_row, origin in [
            ('OTHER', 1401257, coordinate, source), ('FET', 1401258, coordinate, source),
            ('FET', 1401257, ('2024-01-01', *coordinate[1:]), source),
            ('FET', 1401257, coordinate, {**source, 'url': source['url']+'other'})]:
            self.assertFalse(signed_value(CONTRACT, context_row, origin, ticker, cik))

    def test_conflicting_cached_values_are_removed_without_changing_other_documents(self):
        row = deepcopy(REPORTS['OII']['revenue_mix'][0])
        conflict = {**row, 'value': row['value']+1}
        self.assertEqual(canonical([row, conflict], 'OII', 73756), [])
        foreign = {**row, 'source': {**row['source'], 'url': row['source']['url']+'other'}}
        self.assertEqual(canonical([foreign], 'OII', 73756), [foreign])
