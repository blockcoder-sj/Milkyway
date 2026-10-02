"""Specific operating links, accounting adjustments and supplier identity."""
from copy import deepcopy
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_services import PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class EnergyServicesTests(unittest.TestCase):
    def test_all_profiles_and_exact_private_links_are_valid(self):
        for symbol, notes in PUBLIC.items():
            value = CompanyKnowledge(symbol=symbol, **notes)
            self.assertTrue(value.brief)
            self.assertTrue(value.revenue_mix)
            self.assertTrue(value.drivers)
            self.assertEqual(enrich(value).model_dump(), enrich(enrich(value)).model_dump())
            for row in value.brief + value.products + value.segments + value.drivers:
                self.assertEqual(row.source.level, 'primary')
        for key in PRIVATE:
            value = CompanyKnowledge(**private_profile(key))
            self.assertTrue(value.relations, key)
        for symbol, rows in EDGES.items():
            value = CompanyKnowledge(symbol=symbol, name=symbol, **enrichment(symbol))
            self.assertGreaterEqual(len(value.relations), len(rows))
            for edge in rows:
                if edge['registry_id']:
                    self.assertTrue(private_profile(edge['registry_id'])['brief'])
        self.assertTrue(all(row['kind'] == 'supplier' for row in PRIVATE['kogas']['relations']))
        for symbol in ('KGS', 'AROC'):
            self.assertEqual(next(r['kind'] for r in EDGES[symbol]
                                 if r['registry_id'] == 'ariel-compressors'), 'partner')
            self.assertTrue(any(r['symbol'] == symbol and r['kind'] == 'partner'
                                for r in PRIVATE['ariel-compressors']['relations']))

    def test_revenue_scopes_reconcile_without_ignoring_negative_adjustments(self):
        for symbol, group, total in [('DTM', 'segment', 1243000000), ('CQP', 'product', 10758000000),
                ('SUN', 'product', 25201000000), ('USAC', 'product', 998099000),
                ('KGS', 'segment', 1308100000), ('AROC', 'segment', 1489818000),
                ('KNTK', 'product', 1764389000)]:
            rows = REPORTS[symbol]['revenue_mix']
            self.assertEqual(sum(r['value'] for r in rows if r['group'] == group and not r['parent']), total)
        am = REPORTS['AM']['revenue_mix']
        self.assertEqual(sum(r['value'] for r in am) - 70672000, 1188426000)
        self.assertTrue(all(r['share_exclusion'] for r in am))

    def test_cqp_two_axis_customer_roles_do_not_collapse(self):
        origin = {k: REPORTS['CQP']['annual'][k] for k in ('label', 'url', 'as_of', 'level')}
        dates = dict(cik='1383650', start='2025-01-01', end='2025-12-31')
        party = '<xbrldi:explicitMember dimension="us-gaap:RelatedPartyTransactionsByRelatedPartyAxis">us-gaap:NonrelatedPartyMember</xbrldi:explicitMember>'
        raw = doc(context('total', **dates) + context('part', 'cqp:LiquefiedNaturalGasMember',
            axis='srt:ProductOrServiceAxis', extra=party, **dates),
            fact('total', '10758') + fact('part', '8200'))
        row, = parse_revenue(raw, origin, 'CQP')
        self.assertIn('NonrelatedPartyMember', row['member'])
        self.assertEqual(row['value'], 8200000000)
        self.assertEqual(parse_revenue(raw.replace('us-gaap:NonrelatedPartyMember', 'cqp:UnknownMember'), origin, 'CQP'), [])
        self.assertEqual(parse_revenue(raw, origin, 'OTHER'), [])
        self.assertEqual(parse_revenue(raw.replace('1383650', '1383651'), origin, 'CQP'), [])

    def test_document_bound_subsets_and_current_states(self):
        rows = deepcopy(REPORTS['KNTK']['revenue_mix'])
        child = next(r for r in rows if r['member'] == 'apa:MinimumVolumeCommitmentsMember')
        self.assertEqual(child['parent'], 'apa:GatheringAndProcessingServicesMember')
        child['parent'] = None
        self.assertEqual(next(r for r in present_revenue(rows, 'KNTK') if r['member'] == child['member'])['parent'],
                         'apa:GatheringAndProcessingServicesMember')
        altered = {**child, 'source': {**child['source'], 'url': child['source']['url'].replace('20251231', '20261231')}}
        self.assertIsNone(present_revenue([altered], 'KNTK')[0]['parent'])
        notes = ' '.join(r['detail'] for r in PUBLIC['KGS']['segments'])
        self.assertIn('2030년까지', notes)
        self.assertIn('2027년 1분기', notes)
        self.assertFalse(any(r.get('symbol') in {'NVDA', 'MSFT', 'GOOGL'} for r in EDGES['KGS']))
        self.assertTrue(any(r['symbol'] == 'CMI' and r['kind'] == 'supplier' for r in EDGES['USAC']))
        self.assertTrue(any(r['registry_id'] == 'bechtel' for r in EDGES['CQP']))


if __name__ == '__main__':
    unittest.main()
