"""Equipment issuer scope, independent revenue bases and current contract state."""
from copy import deepcopy
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_equipment import PUBLIC, PRIVATE, EDGES, ANNUAL, QUARTER
from cloud_app.company_energy_equipment_revenue import COORDINATES
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import enrichment, private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer
from tests.test_company_revenue import context, doc, fact


class EnergyEquipmentTests(unittest.TestCase):
    def test_edited_profiles_have_primary_briefs_products_segments_and_drivers(self):
        self.assertEqual(set(PUBLIC), {'FTI', 'NOV', 'WHD', 'WTTR', 'FTK', 'NINE',
                                     'TTI', 'NBR', 'HP', 'WFRD', 'RES', 'RNGR'})
        for symbol, notes in PUBLIC.items():
            with self.subTest(symbol=symbol):
                value = CompanyKnowledge(symbol=symbol, **notes)
                self.assertTrue(value.brief and value.products and value.segments and value.drivers)
                current = enrich(value)
                self.assertEqual(enrich(current).model_dump(), current.model_dump())
                self.assertGreaterEqual(len(enrichment(symbol)['relations']), len(EDGES[symbol]))
                for row in value.brief + value.products + value.segments + value.drivers:
                    self.assertEqual(row.source.level, 'primary')
                    self.assertFalse(row.original)
                self.assertTrue(current.financials)
                self.assertNotEqual(issuer(symbol).group, 'pending')
                self.assertEqual(issuer(symbol).report_source.level, 'primary')
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)
        for rows in EDGES.values():
            for row in rows:
                if row['registry_id']:
                    self.assertTrue(private_profile(row['registry_id'])['brief'])

    def test_reported_revenue_totals_do_not_double_count_subsets(self):
        cases = [('FTI', 'segment', 9932600000), ('WHD', 'segment', 1079051000),
                 ('WTTR', 'segment', 1407344000), ('FTK', 'segment', 237262000),
                 ('NINE', 'product', 561911000), ('TTI', 'segment', 630932000),
                 ('WFRD', 'segment', 4918000000), ('RES', 'product', 1626566000),
                 ('RNGR', 'segment', 546900000)]
        for symbol, group, total in cases:
            rows = present_revenue(REPORTS[symbol]['revenue_mix'], symbol)
            self.assertEqual(sum(r['value'] for r in rows if r['group'] == group and not r['parent']), total,
                             (symbol, group))
        for symbol, gross, elimination, external in [('NOV',8911000000,167000000,8744000000),
                                                    ('NBR',3241728000,57035000,3184693000)]:
            rows = [r for r in present_revenue(REPORTS[symbol]['revenue_mix'], symbol)
                    if r['group'] == 'segment' and not r['parent']]
            self.assertEqual(sum(r['value'] for r in rows), gross)
            self.assertEqual(gross-elimination, external)
            self.assertTrue(all(r['total'] is None and r['includes_intersegment'] for r in rows))

    def test_water_service_detail_has_its_own_adjustments_and_no_external_percentage(self):
        rows = [r for r in present_revenue(REPORTS['WTTR']['revenue_mix'], 'WTTR')
                if r['group'] == 'product']
        self.assertEqual(sum(r['value'] for r in rows), 1420376000)
        self.assertEqual(1420376000-13032000, 1407344000)
        self.assertTrue(all(r['total'] is None and '13,032,000' in r['share_exclusion'] for r in rows))
        self.assertTrue(all('13,703,000' not in r['share_exclusion'] for r in rows))

    def test_flotek_other_countries_excludes_separately_reported_uae(self):
        rows = [r for r in present_revenue(REPORTS['FTK']['revenue_mix'], 'FTK')
                if r['group'] == 'geography']
        self.assertEqual(sum(r['value'] for r in rows), 237262000)
        other = next(r for r in rows if r['member'] == 'us-gaap:NonUsMember')
        self.assertEqual(other['value'], 1359000)
        self.assertIn('UAE 제외', other['label'])

    def test_partial_saudi_geography_is_inside_non_us_not_additional_revenue(self):
        rows = [r for r in present_revenue(REPORTS['NBR']['revenue_mix'], 'NBR')
                if r['group'] == 'geography']
        saudi = next(r for r in rows if r['member'] == 'country:SA')
        self.assertEqual(saudi['parent'], 'us-gaap:NonUsMember')
        self.assertEqual(sum(r['value'] for r in rows if not r['parent']), 3184693000)

    def test_exact_multi_axis_coordinates_reject_wrong_issuer_and_extra_dimensions(self):
        for (symbol, cik, pairs), (group, member) in COORDINATES.items():
            if symbol == 'HP': dates = dict(cik=str(cik), start='2024-10-01', end='2025-09-30')
            else: dates = dict(cik=str(cik), start='2025-01-01', end='2025-12-31')
            pairs = sorted(pairs)
            axis, first = pairs[0]
            extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>'
                            for a,m in pairs[1:])
            raw = doc(context('total', **dates)+context('part', first, axis=axis, extra=extra, **dates),
                      fact('total','100')+fact('part','70'))
            result = parse_revenue(raw, ANNUAL[symbol], symbol)
            self.assertEqual(len(result), 1, (symbol, pairs))
            self.assertEqual((result[0]['group'], result[0]['member']), (group, member))
            if len(pairs) > 1:
                self.assertEqual(parse_revenue(raw, ANNUAL[symbol], 'UNKNOWN'), [])
            self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)), ANNUAL[symbol], symbol), [])
            more = '<xbrldi:explicitMember dimension="x:UnreviewedAxis">x:UnreviewedMember</xbrldi:explicitMember>'
            self.assertEqual(parse_revenue(raw.replace('</xbrli:segment>',more+'</xbrli:segment>'),
                                           ANNUAL[symbol],symbol), [])

    def test_other_years_never_reuse_reviewed_elimination_or_country_scope(self):
        for symbol in ('NOV','NBR','WTTR','FTK'):
            rows = deepcopy(REPORTS[symbol]['revenue_mix'])
            for row in rows:
                row['start']='2024-01-01'; row['end']='2024-12-31'
            result = present_revenue(rows,symbol)
            self.assertTrue(all('13,032,000' not in (r.get('share_exclusion') or '') for r in result))
            if symbol == 'FTK':
                self.assertTrue(all('UAE 제외' not in r['label'] for r in result))

    def test_completed_acquisitions_pending_deals_and_terminated_contracts_are_distinct(self):
        self.assertIn('1월 1일 종결', str(PUBLIC['WHD']['brief']))
        self.assertIn('현재 자회사로 표시하지', str(PUBLIC['WTTR']['brief']))
        self.assertIn('8월 18일 즉시 효력', str(PUBLIC['FTK']['brief']))
        self.assertIn('매출·대금 수령은 없었고', str(PUBLIC['FTK']['brief']))
        self.assertIn('9월 1일 완료', str(PUBLIC['WFRD']['brief']))
        self.assertIn('4분기 효력', str(PUBLIC['WFRD']['brief']))
        self.assertIn('2027년 납품 예정', str(PUBLIC['RNGR']['brief']))
        self.assertFalse(any(r['symbol']=='TTEK' for r in EDGES['TTI']))
        self.assertFalse(any(r['symbol']=='HPQ' for r in EDGES['HP']))
        self.assertFalse(any(r['symbol']=='PTEN' for r in EDGES['RES'] if r['kind']=='subsidiary'))
        # Contract-party identity and later termination each keep their own evidence.
        power = PRIVATE['power-expectations']
        self.assertIn('000092805426000082', power['description_source']['url'])
        self.assertTrue(any('000092805426000084' in r['source']['url'] for r in power['brief']))

    def test_named_supplier_customer_and_partner_links_survive_graph_navigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph=CompanyGraph(SimpleNamespace(dataset_dir=Path(tmp)/'runtime/data',
                                               personal_local_mode=True, production=False))
            for symbol in ('NINE','TTI','WFRD','RNGR'):
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)), 'us_10')
            targets = {key: graph.ingest(CompanyKnowledge(**private_profile(key)))
                       for key in ('newgen-systems','lanxess-bromine','saltwerx','ncs-multistage')}
            root=graph.by_symbol('NINE')['id']
            edges=graph.relations(root)
            newgen=next(row for row in edges if row['target_id']==targets['newgen-systems'] and row['kind']=='supplier')
            self.assertTrue(graph.entity(newgen['target_id'])['profile']['brief'])
            self.assertTrue(any(row['target_id']==root for row in graph.relations(newgen['target_id'])))
