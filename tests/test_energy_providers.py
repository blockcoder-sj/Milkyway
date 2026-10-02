"""Operating counterparties, gross/external bases and exact issuer aliases."""
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_providers import PUBLIC, PRIVATE, EDGES, ANNUAL
from cloud_app.company_energy_provider_revenue import SEGMENTS
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class EnergyProviderTests(unittest.TestCase):
    def test_profiles_and_operating_links_are_sourced_and_navigable(self):
        self.assertEqual(set(PUBLIC), {'SLB', 'BKR', 'HAL', 'PTEN', 'PUMP', 'LBRT',
                                     'SND', 'AESI', 'FLOC', 'ACDC', 'DTI', 'KLXE'})
        for symbol, notes in PUBLIC.items():
            value = CompanyKnowledge(symbol=symbol, **notes)
            self.assertTrue(value.brief and value.products and value.segments and value.drivers)
            self.assertEqual(enrich(value).model_dump(), enrich(enrich(value)).model_dump())
            self.assertGreaterEqual(len(enrichment(symbol)['relations']), len(EDGES[symbol]))
            for row in value.brief + value.products + value.segments + value.drivers:
                self.assertEqual(row.source.level, 'primary')
                self.assertNotIn('wikipedia', row.source.url)
        for key in PRIVATE:
            value = CompanyKnowledge(**private_profile(key))
            self.assertTrue(value.brief and value.relations, key)
        for rows in EDGES.values():
            for row in rows:
                if row['registry_id']:
                    self.assertTrue(private_profile(row['registry_id'])['brief'])

    def test_annual_sums_keep_independent_revenue_bases(self):
        checks = [('SLB', 'revenue_type', 35708000000),
                  ('BKR', 'segment', 27733000000), ('HAL', 'segment', 22184000000),
                  ('PTEN', 'segment', 4826624000), ('SND', 'product', 330153000),
                  ('AESI', 'segment', 1095310000), ('AESI', 'revenue_type', 1095310000),
                  ('FLOC', 'product', 759719000), ('ACDC', 'revenue_type', 1941800000),
                  ('DTI', 'product', 159626000), ('KLXE', 'product', 636600000)]
        for symbol, group, total in checks:
            rows = REPORTS[symbol]['revenue_mix']
            self.assertEqual(sum(row['value'] for row in rows
                                 if row['group'] == group and not row['parent']), total)
        gross = [('SLB', 36648000000, 940000000, 35708000000),
                 ('PUMP', 1270048000, 890000, 1269158000),
                 ('FLOC', 818505000, 58786000, 759719000),
                 ('ACDC', 2492100000, 550300000, 1941800000)]
        for symbol, total, adjustment, external in gross:
            rows = [row for row in REPORTS[symbol]['revenue_mix'] if row['group'] == 'segment']
            self.assertEqual(sum(row['value'] for row in rows), total)
            self.assertEqual(total - adjustment, external)
            self.assertTrue(all(row['includes_intersegment'] and row['share_exclusion']
                                and row['total'] is None for row in rows))
        dti = [row for row in REPORTS['DTI']['revenue_mix'] if row['group'] == 'segment']
        self.assertEqual(sum(row['value'] for row in dti) - 12420000, 159625000)
        self.assertTrue(all('1,000' in row['share_exclusion'] for row in dti))

    def test_checked_segment_coordinates_reject_other_entities_and_extra_axes(self):
        for (symbol, cik), mapping in SEGMENTS.items():
            member = next(iter(mapping))
            qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
            dates = dict(cik=str(cik), start='2025-01-01', end='2025-12-31')
            raw = doc(context('total', **dates) + context('part', member,
                axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier, **dates),
                fact('total', '100') + fact('part', '70'))
            row, = parse_revenue(raw, ANNUAL[symbol], symbol)
            self.assertTrue(row['includes_intersegment'])
            self.assertIsNone(row['total'])
            self.assertEqual(parse_revenue(raw, ANNUAL[symbol], 'UNKNOWN'), [])
            self.assertEqual(parse_revenue(raw.replace(str(cik), str(cik + 1)), ANNUAL[symbol], symbol), [])
            self.assertEqual(parse_revenue(raw.replace(qualifier, qualifier * 2), ANNUAL[symbol], symbol), [])
            extra = '<xbrldi:explicitMember dimension="srt:StatementGeographicalAxis">country:US</xbrldi:explicitMember>'
            self.assertEqual(parse_revenue(raw.replace(qualifier, qualifier + extra), ANNUAL[symbol], symbol), [])

    def test_legacy_atlas_shortfall_is_not_an_additional_product(self):
        base = deepcopy(REPORTS['AESI']['revenue_mix'][0])
        shortfall = {**base, 'group': 'product', 'member': 'aesi:ShortfallRevenuesMember',
                     'metric': 'us-gaap:Revenues', 'value': 23900000}
        self.assertEqual(present_revenue([shortfall], 'AESI'), [])
        for changed in [{**shortfall, 'start': '2024-01-01', 'end': '2024-12-31'},
                        {**shortfall, 'metric': 'us-gaap:SalesRevenueNet'},
                        {**shortfall, 'source': {**shortfall['source'], 'url':
                                                shortfall['source']['url'].replace('20251231', '20241231')}}]:
            self.assertEqual(len(present_revenue([changed], 'AESI')), 1)
        self.assertEqual(len(present_revenue([shortfall], 'UNKNOWN')), 1)
        self.assertFalse(any(row['member'] == shortfall['member'] for row in REPORTS['AESI']['revenue_mix']))

    def test_other_report_segment_basis_cannot_reuse_annual_elimination(self):
        row = deepcopy(next(row for row in REPORTS['SLB']['revenue_mix'] if row['group'] == 'segment'))
        row.update(start='2024-01-01', end='2024-12-31', total=100000000000,
                   includes_intersegment=False, share_exclusion=None)
        result, = present_revenue([row], 'SLB')
        self.assertIsNone(result['total'])
        self.assertIn('별도로 확인', result['share_exclusion'])
        self.assertNotIn('9억4,000만', result['share_exclusion'])
        self.assertFalse(result['includes_intersegment'])
        unknown, = present_revenue([row], 'UNKNOWN')
        self.assertEqual(unknown['total'], row['total'])

    def test_legacy_single_axis_facts_are_regrouped_without_changing_values(self):
        dti = deepcopy(next(row for row in REPORTS['DTI']['revenue_mix']
                            if row['member'] == 'us-gaap:ProductMember'))
        dti['group'] = 'revenue_type'
        atlas = deepcopy(next(row for row in REPORTS['AESI']['revenue_mix']
                              if row['member'] == 'aesi:RentalRevenueMember'))
        atlas['group'] = 'product'
        for symbol, row, group in [('DTI', dti, 'product'), ('AESI', atlas, 'revenue_type')]:
            result, = present_revenue([row], symbol)
            self.assertEqual(result['group'], group)
            self.assertEqual(result['value'], row['value'])
            self.assertEqual(result['source'], row['source'])
            self.assertEqual(present_revenue([row], 'UNKNOWN')[0]['group'], row['group'])
        self.assertEqual(REPORTS['LBRT']['revenue_mix'], [])
        self.assertIn('단일 사업 부문', PUBLIC['LBRT']['segments'][0]['detail'])

    def test_transactions_actual_activity_and_similar_names_keep_their_scope(self):
        slb = ' '.join(row['detail'] for row in PUBLIC['SLB']['segments'])
        self.assertIn('2027년 상반기 완료 목표', slb)
        self.assertFalse(any('Kelvion' in row['name'] and row['kind'] == 'subsidiary' for row in EDGES['SLB']))
        self.assertFalse(any(row['symbol'] in {'GTLS', 'CHX'} for rows in EDGES.values() for row in rows))
        atlas = ' '.join(row['detail'] for row in PUBLIC['AESI']['segments'])
        self.assertIn('35대', atlas)
        self.assertIn('100대는 2027년', atlas)
        self.assertIn('승인된 판매점', atlas)
        self.assertIn('2030년 12월 31일', atlas)
        self.assertTrue(any(row['registry_id'] == 'kodiak-ai' for row in EDGES['AESI']))
        self.assertFalse(any(row['symbol'] == 'KGS' for row in EDGES['AESI']))
        self.assertTrue(any(row['registry_id'] == 'liberty-lift-solutions' for row in EDGES['DTI']))
        self.assertFalse(any(row['symbol'] == 'LBRT' for row in EDGES['DTI']))
        flowco = ' '.join(row['detail'] for row in PUBLIC['FLOC']['segments'])
        self.assertIn('2026년 3월 2일', flowco)
        self.assertIn('G3306TA', flowco)
        self.assertIn('JGQ/2', flowco)
        self.assertIn('121,300,000', flowco)
        self.assertIn('113,200,000', flowco)
        self.assertIn('다르게 기재', flowco)
        klx = ' '.join(row['detail'] for row in PUBLIC['KLXE']['segments'])
        self.assertIn('일부 자산', klx)
        self.assertFalse(any('Wolf Pack' in row['name'] and row['kind'] == 'subsidiary' for row in EDGES['KLXE']))
        self.assertFalse(any(row['symbol'] in {'PBTS', 'RR.L'} for row in EDGES['LBRT']))

    def test_verified_public_alias_preserves_old_bookmarks_and_rejects_wrong_ticker(self):
        legacy = enrich(CompanyKnowledge(registry_id='range-profrac', name='ProFrac / Range 현장'))
        self.assertEqual((legacy.symbol, legacy.name), ('ACDC', 'ProFrac Holding'))
        current = enrich(CompanyKnowledge(symbol='ACDC', name='Old stub name'))
        self.assertEqual((current.registry_id, current.name), ('range-profrac', 'ProFrac Holding'))
        private = enrich(CompanyKnowledge(registry_id='liberty-lift-solutions', name='Liberty Lift Solutions'))
        self.assertIsNone(private.symbol)
        self.assertEqual(private.name, 'Liberty Lift Solutions')
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            enrich(CompanyKnowledge(symbol='FLOC', registry_id='range-profrac', name='Wrong issuer'))
        with tempfile.TemporaryDirectory() as temp:
            settings = SimpleNamespace(personal_local_mode=True, production=False,
                                       dataset_dir=Path(temp)/'runtime/data')
            graph = CompanyGraph(settings)
            # Reproduce an earlier registry-only bookmark without the new bridge.
            old_edge = dict(name='ProFrac', registry_id='range-profrac', kind='supplier',
                            source=ANNUAL['ACDC'])
            with patch('cloud_app.company_research_catalog.REGISTERED_TICKERS', {}):
                range_id = graph.ingest(CompanyKnowledge(symbol='RRC', name='Range', relations=[old_edge]))
                old_id = graph.relations(range_id)[0]['target_id']
            public_id = graph.ingest(CompanyKnowledge(symbol='ACDC', name='ProFrac'))
            self.assertNotEqual(public_id, old_id)
            self.assertEqual(graph.ingest(CompanyKnowledge(symbol='ACDC', **PUBLIC['ACDC'])), public_id)
            self.assertEqual(graph.entity(old_id)['id'], public_id)
            self.assertEqual(graph.relations(range_id)[0]['target_id'], public_id)
            self.assertTrue(graph.relations(public_id))
            with graph.connection() as db:
                self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
            with self.assertRaisesRegex(ValueError, 'registry'):
                graph.ingest(CompanyKnowledge(symbol='FLOC', registry_id='range-profrac', name='Wrong issuer'))
            self.assertEqual(graph.entity(old_id)['symbols'], ['ACDC'])


if __name__ == '__main__':
    unittest.main()
