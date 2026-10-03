"""Original nuclear fuel scopes, bounded tagging corrections and navigation."""
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_financial_archive import archive, validate_archive
from cloud_app.company_energy_majors import PRIVATE as MAJOR_CONTEXT
from cloud_app.company_energy_nuclear import PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_nuclear_revenue import COORDINATES, DOCUMENTS, dimensions
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer
from tests.test_company_revenue import context, doc, fact


class EnergyNuclearTests(unittest.TestCase):
    def test_nine_edited_profiles_validate_and_merge_without_duplication(self):
        self.assertEqual(set(PUBLIC), {'CCJ', 'DNN', 'NXE', 'UEC', 'EU', 'URG', 'LEU', 'LTBR', 'UUUU'})
        for symbol, notes in PUBLIC.items():
            with self.subTest(symbol=symbol):
                value = enrich(CompanyKnowledge(symbol=symbol, **notes))
                self.assertGreaterEqual(len(value.brief), 6)
                self.assertGreaterEqual(len(value.products), 6)
                self.assertTrue(value.drivers and value.relations and value.financials and value.financial_context)
                self.assertEqual(enrich(value).model_dump(), value.model_dump())
                self.assertTrue(all(row.source.level == 'primary' and not row.original
                    for row in value.brief + value.products + value.drivers))
                self.assertNotIn('wikipedia', str(value.model_dump()).lower())
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)

    def test_original_exhibit_parents_financial_periods_and_currencies_are_preserved(self):
        records = archive()
        for symbol, total, unit in [('CCJ', 3481933000, 'CAD'), ('DNN', 4918000, 'CAD'),
            ('UEC', 37250000, 'USD'), ('EU', 43155000, 'USD'), ('URG', 27207000, 'USD'),
            ('LEU', 448700000, 'USD'), ('LTBR', 0, 'USD'), ('UUUU', 65922000, 'USD')]:
            record = records[symbol]
            self.assertEqual(record['financials'][0]['value'], total)
            self.assertTrue(all(row['unit'] == unit for row in record['financials']))
            self.assertEqual(record['annual']['url'], DOCUMENTS[symbol, int(record['cik'])])
        for symbol in ('CCJ', 'DNN', 'NXE'):
            self.assertEqual(records[symbol]['parent_annual']['url'], REPORTS[symbol]['annual']['url'])
            self.assertEqual(records[symbol]['annual_period_end'], '2025-12-31')
        self.assertEqual(records['UEC']['financials'][0]['period'], '2025-08-01 ~ 2026-07-31')
        self.assertFalse(any(row['label'] == '매출' for row in records['NXE']['financials']))
        self.assertEqual(issuer('NXE').scope, 'context')
        bad = {'CCJ': deepcopy(records['CCJ'])}
        bad['CCJ']['parent_annual'] = records['DNN']['parent_annual']
        with self.assertRaises(ValueError):
            validate_archive(bad)

    def test_actual_compositions_reconcile_without_associate_or_customer_double_counting(self):
        for symbol, groups, total in [('CCJ', ('segment', 'geography', 'revenue_type'), 3481933000),
            ('DNN', ('segment',), 4918000), ('UEC', ('product',), 37250000),
            ('URG', ('product',), 27207000), ('LEU', ('product', 'geography'), 448700000),
            ('UUUU', ('product', 'segment', 'geography'), 65922000)]:
            for group in groups:
                with self.subTest(symbol=symbol, group=group):
                    rows = [r for r in present_revenue(REPORTS[symbol]['revenue_mix'], symbol) if r['group'] == group]
                    self.assertEqual(sum(r['value'] for r in rows), total)
                    if symbol == 'CCJ':
                        self.assertTrue(all(r['total'] is None and '무차원' in r['share_exclusion'] for r in rows))
                    else:
                        self.assertTrue(all(r['total'] == total for r in rows))
        self.assertFalse(REPORTS['EU']['revenue_mix'] or REPORTS['NXE']['revenue_mix'] or REPORTS['LTBR']['revenue_mix'])
        for symbol in PUBLIC:
            self.assertFalse(any(any(word in r['member'] for word in ('CustomerA', 'CustomerB', 'CustomerOne',
                'SignificantInvestments', 'WestinghouseElectric', 'ReportableSegmentsMember'))
                for r in REPORTS[symbol]['revenue_mix']))

    def test_centrus_total_mistag_is_corrected_only_at_the_reviewed_coordinate(self):
        rows = present_revenue(REPORTS['LEU']['revenue_mix'], 'LEU')
        gross, = [r for r in rows if r['member'] == 'leu:ContractServicesSegmentMember']
        self.assertEqual((gross['group'], gross['label'], gross['value']),
            ('revenue_type', '전체 사업 · 내부 제거 전', 461100000))
        self.assertIsNone(gross['total'])
        self.assertIn('102,500,000', gross['share_exclusion'])
        old = deepcopy(gross)
        old.update(group='segment', label='Contract Services Segment', total=448700000)
        corrected, = present_revenue([old], 'LEU')
        self.assertEqual(corrected, gross)
        for field, value in [('value', 461100001), ('unit', 'CAD'), ('start', '2024-01-01'),
            ('end', '2024-12-31'), ('source', dict(old['source'], url=old['source']['url'].replace('leu-20251231', 'copy')))]:
            changed = deepcopy(old)
            changed.pop('share_exclusion', None)
            changed[field] = value
            unaffected, = present_revenue([changed], 'LEU')
            self.assertEqual(unaffected['group'], 'segment')
            self.assertNotEqual(unaffected['label'], '전체 사업 · 내부 제거 전')

    def test_energy_fuels_table_reading_keeps_original_mistagged_members_and_amounts(self):
        rows = present_revenue(REPORTS['UUUU']['revenue_mix'], 'UUUU')
        for member, amount, label in [
            ('country:EE/efr:RareEarthElementsSegmentMember', 348000, '오스트리아 · 광물사 · 본문 기준'),
            ('country:AE/efr:UraniumSegmentMember', 195000, '아랍에미리트 · 광물사 · 본문 기준')]:
            row, = [r for r in rows if r['member'] == member]
            self.assertEqual((row['value'], row['label'], row['group']), (amount, label, 'geography'))
            self.assertIn('태그', row['share_exclusion'])
            old = dict(row, label='Original wrong tag label')
            corrected, = present_revenue([old], 'UUUU')
            self.assertEqual(corrected, row)
            for field, value in [('value', amount + 1), ('unit', 'CAD'), ('end', '2024-12-31'),
                ('source', dict(row['source'], url=row['source']['url'].replace('efr-20251231', 'copy')))]:
                changed = deepcopy(old)
                changed.pop('share_exclusion', None)
                changed[field] = value
                unaffected, = present_revenue([changed], 'UUUU')
                self.assertNotEqual(unaffected['label'], label)
                self.assertEqual(unaffected['member'], member)

    def test_coordinates_require_complete_axes_actual_issuer_and_matching_period(self):
        for (symbol, cik, pairs), (group, member) in COORDINATES.items():
            with self.subTest(symbol=symbol, member=member):
                pairs = sorted(pairs)
                self.assertEqual(dimensions(pairs, symbol, cik), (group, member))
                self.assertIsNone(dimensions(pairs, symbol, cik + 1))
                self.assertIsNone(dimensions(pairs + [('x:ExtraAxis', 'x:UnknownMember')], symbol, cik))
                self.assertIsNone(dimensions(pairs + [pairs[0]], symbol, cik))
                axis, first = pairs[0]
                extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a, m in pairs[1:])
                dates = dict(cik=str(cik), start='2025-08-01' if symbol == 'UEC' else '2025-01-01',
                    end='2026-07-31' if symbol == 'UEC' else '2025-12-31')
                metric = ('ifrs-full:RevenueFromContractsWithCustomers' if symbol == 'CCJ'
                    else 'ifrs-full:Revenue' if symbol == 'DNN' else 'us-gaap:Revenues'
                    if symbol in {'UEC', 'URG'} else 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax')
                raw = doc(context('total', **dates) + context('part', first, axis=axis, extra=extra, **dates),
                    fact('total', '100', metric=metric, scale=0) + fact('part', '70', metric=metric, scale=0))
                origin = dict(label='검토된 원문', level='primary', as_of='2026-09-29', url=DOCUMENTS[symbol, cik])
                row, = parse_revenue(raw, origin, symbol)
                self.assertEqual((row['group'], row['member'], row['value']), (group, member, 70))
                self.assertEqual(parse_revenue(raw.replace(str(cik), str(cik + 1)), origin, symbol), [])

    def test_named_roles_current_vs_historical_stages_and_shared_fluor(self):
        self.assertEqual({e['kind'] for e in EDGES['UUUU'] if e['registry_id'] == 'vac-energy-fuels'}, {'transaction'})
        self.assertEqual({e['kind'] for e in EDGES['UUUU'] if e['registry_id'] == 'asm-energy-fuels'}, {'subsidiary'})
        for key in ('x-energy-haleu', 'radiant-kaleidos', 'antares-haleu'):
            row, = [e for e in EDGES['LEU'] if e['registry_id'] == key]
            self.assertEqual(row['kind'], 'customer')
            self.assertIn('미래', row['detail'])
        self.assertTrue(any('2024년 완료' in e['detail'] and e['symbol'] == 'LEU' for e in EDGES['LTBR']))
        self.assertTrue(all('2021' in e['detail'] for e in EDGES['NXE'] if e['registry_id'] != 'src-geoanalytical'))
        self.assertIn('95%', str(PUBLIC['DNN']['products']))
        self.assertIn('57.418%', str(PUBLIC['CCJ']['brief']))
        fluor = private_profile('fluor-lngcanada')
        self.assertTrue(all(s in fluor['sources'] for s in MAJOR_CONTEXT['fluor-lngcanada']['sources']))
        self.assertTrue(any('UEC' in row['title'] for row in fluor['brief']))
        self.assertTrue(any('Centrus' in row['title'] for row in fluor['brief']))

    def test_clickable_counterpart_pages_reverse_trade_and_primary_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = CompanyGraph(SimpleNamespace(personal_local_mode=True, production=False,
                dataset_dir=Path(directory) / 'data'))
            for symbol in PUBLIC:
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol, name=symbol)), 'us_10')
            for key in PRIVATE:
                graph.ingest(CompanyKnowledge(**private_profile(key)))
            graph.ingest(CompanyKnowledge(**private_profile('fluor-lngcanada')))
            for symbol, target, kind in [('LEU', 'X-energy', 'supplier'), ('UUUU', 'Vulcan Elements', 'partner'),
                ('NXE', 'Saskatchewan Research Council', 'customer')]:
                root = graph.by_symbol(symbol)
                edge = next(e for e in graph.relations(root['id']) if e['name'] == target)
                self.assertTrue(graph.entity(edge['target_id'])['profile']['brief'])
                reverse = next(e for e in graph.relations(edge['target_id']) if e['target_id'] == root['id'])
                self.assertEqual(reverse['kind'], kind)
                self.assertEqual(reverse['source'], edge['source'])


if __name__ == '__main__':
    unittest.main()
