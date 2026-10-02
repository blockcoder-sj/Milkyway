"""Reviewed MLP figures, exact external coordinates and current project states."""
from copy import deepcopy
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_mlp import PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import parse_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class MlpResearchTests(unittest.TestCase):
    def test_profiles_and_contextual_links_are_typed_sourced_and_idempotent(self):
        for symbol, notes in PUBLIC.items():
            before = deepcopy(notes)
            value = CompanyKnowledge(symbol=symbol, **notes)
            self.assertEqual(enrich(value).model_dump(), enrich(enrich(value)).model_dump())
            self.assertEqual(notes, before)
            self.assertTrue(value.revenue_mix)
            self.assertTrue(value.products)
            self.assertTrue(value.drivers)
            for item in value.brief + value.products + value.segments + value.drivers:
                self.assertEqual(item.source.level, 'primary')
        for key in PRIVATE:
            value = CompanyKnowledge(**private_profile(key))
            self.assertTrue(value.relations, key)
        for symbol, rows in EDGES.items():
            value = CompanyKnowledge(symbol=symbol, name=symbol, **enrichment(symbol))
            self.assertGreaterEqual(len(value.relations), len(rows))

    def test_exact_external_segments_reconcile(self):
        for symbol, total, count in [('EPD', 52596000000, 4), ('ET', 85536000000, 8),
                                      ('MPLX', 9726000000, 2), ('HESM', 1621300000, 3)]:
            rows = [r for r in REPORTS[symbol]['revenue_mix'] if r['group'] == 'segment']
            self.assertEqual(len(rows), count, symbol)
            self.assertEqual(sum(r['value'] for r in rows), total, symbol)
        for symbol in ('PAA', 'PAGP'):
            rows = [r for r in REPORTS[symbol]['revenue_mix'] if r['group'] == 'revenue_type']
            self.assertEqual(sum(r['value'] for r in rows), 44262000000)
        wes = REPORTS['WES']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in wes), 3841599000)
        self.assertNotEqual(sum(r['value'] for r in wes), 4281744000)  # pro forma

    def test_et_three_axes_require_external_customers_and_exact_issuer(self):
        origin = {k: REPORTS['ET']['annual'][k] for k in ('label', 'url', 'as_of', 'level')}
        qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        external = '<xbrldi:explicitMember dimension="us-gaap:RelatedPartyTransactionsByRelatedPartyAxis">et:ExternalCustomersMember</xbrldi:explicitMember>'
        dates = dict(cik='1276187', start='2025-01-01', end='2025-12-31')
        contexts = context('total', **dates) + context('part', 'et:IntrastateTransportationAndStorageMember',
            axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier+external, **dates)
        raw = doc(contexts, fact('total', '85536', metric='us-gaap:Revenues') +
                  fact('part', '3544', metric='us-gaap:Revenues'))
        row, = parse_revenue(raw, origin, 'ET')
        self.assertEqual(row['value'], 3544000000)
        self.assertEqual(row['total'], 85536000000)
        self.assertEqual(parse_revenue(raw.replace('et:ExternalCustomersMember', 'et:IntersegmentMember'), origin, 'ET'), [])
        self.assertEqual(parse_revenue(raw.replace('et:ExternalCustomersMember', 'et:UnknownMember'), origin, 'ET'), [])
        self.assertEqual(parse_revenue(raw, origin, 'OTHER'), [])
        self.assertEqual(parse_revenue(raw.replace('1276187', '1276188'), origin, 'ET'), [])

    def test_current_contracts_and_holding_roles_are_not_guessed(self):
        notes = ' '.join(r['detail'] for r in PUBLIC['ET']['segments'])
        self.assertIn('중단', notes)
        self.assertIn('FID 조건부', notes)
        self.assertTrue(any(r['symbol'] == 'ETR' and r['kind'] == 'customer' for r in EDGES['ET']))
        self.assertFalse(any(r.get('symbol') == 'META' for r in EDGES['ET']))
        self.assertIn('5월 12일', ' '.join(r['detail'] for r in PUBLIC['PAA']['segments']))
        self.assertIn('중복', ' '.join(r['detail'] for r in PUBLIC['PAGP']['segments']))
        self.assertEqual({r['kind'] for r in EDGES['HESM'] if r['symbol'] == 'TRGP'}, {'supplier', 'partner'})


if __name__ == '__main__':
    unittest.main()
