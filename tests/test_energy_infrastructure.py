"""Original scopes, actual named counterpart roles and navigation; no providers."""
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_infrastructure import PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_materials import PUBLIC as MATERIALS, PRIVATE as MATERIAL_CONTEXT, EDGES as MATERIAL_EDGES
from cloud_app.company_energy_infrastructure_revenue import COORDINATES, DOCUMENTS, dimensions
from cloud_app.company_energy_financial_archive import archive, validate_archive
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from tests.test_company_revenue import context, doc, fact


class EnergyInfrastructureTests(unittest.TestCase):
    def test_edited_profiles_have_sources_values_inputs_and_idempotent_merge(self):
        self.assertEqual(set(PUBLIC) | set(MATERIALS), {'ENB', 'PBA', 'TRP', 'SOBO', 'TS', 'SSL'})
        for symbol, notes in {**PUBLIC, **MATERIALS}.items():
            with self.subTest(symbol=symbol):
                current = enrich(CompanyKnowledge(symbol=symbol, **notes))
                self.assertGreaterEqual(len(current.brief), 6)
                self.assertGreaterEqual(len(current.products), 6)
                self.assertTrue(current.financials and current.financial_context and current.revenue_mix)
                self.assertTrue(current.drivers and current.relations)
                self.assertEqual(enrich(current).model_dump(), current.model_dump())
                self.assertTrue(all(row.source.level == 'primary' and not row.original
                                    for row in current.brief + current.products + current.drivers))
        for key in {**PRIVATE, **MATERIAL_CONTEXT}:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)
        for edges in [*EDGES.values(), *MATERIAL_EDGES.values()]:
            for edge in edges:
                if edge['registry_id']:
                    self.assertTrue(private_profile(edge['registry_id']))

    def test_receipts_keep_actual_exhibits_periods_currencies_and_cover(self):
        records = archive()
        for symbol, total, unit in [('ENB', 65194000000, 'CAD'), ('PBA', 7778000000, 'CAD'),
            ('TRP', 15239000000, 'CAD'), ('SOBO', 1986000000, 'USD'),
            ('TS', 11981157000, 'USD'), ('SSL', 272118000000, 'ZAR')]:
            record = records[symbol]
            self.assertEqual(record['financials'][0]['value'], total)
            self.assertTrue(all(row['unit'] == unit for row in record['financials']))
            self.assertEqual(record['annual']['url'], DOCUMENTS[symbol, int(record['cik'])])
            if symbol in {'PBA', 'TRP', 'SOBO', 'SSL'}:
                self.assertEqual(record['parent_annual']['url'], REPORTS[symbol]['annual']['url'])
                self.assertEqual(record['annual_period_end'], '2026-06-30' if symbol == 'SSL' else '2025-12-31')
        self.assertEqual(records['SSL']['financials'][0]['period'], '2025-07-01 ~ 2026-06-30')
        bad = {'SSL': deepcopy(records['SSL'])}
        bad['SSL']['parent_annual'] = records['PBA']['parent_annual']
        with self.assertRaises(ValueError):
            validate_archive(bad)

    def test_external_sales_and_contract_only_tables_keep_distinct_denominators(self):
        for symbol, group, total in [('ENB', 'product', 65194000000), ('ENB', 'segment', 29329000000),
            ('ENB', 'geography', 65194000000), ('PBA', 'segment', 7778000000),
            ('PBA', 'product', 7335000000), ('TRP', 'segment', 15239000000),
            ('TRP', 'geography', 15239000000), ('SOBO', 'segment', 1986000000),
            ('SOBO', 'geography', 1986000000), ('TS', 'geography', 11981157000),
            ('SSL', 'segment', 272118000000), ('SSL', 'product', 266855000000),
            ('SSL', 'geography', 272118000000)]:
            with self.subTest(symbol=symbol, group=group):
                rows = [r for r in present_revenue(REPORTS[symbol]['revenue_mix'], symbol) if r['group'] == group]
                self.assertEqual(sum(r['value'] for r in rows), total)
                self.assertTrue(all(r['total'] == total for r in rows))
        trp = [r for r in present_revenue(REPORTS['TRP']['revenue_mix'], 'TRP') if r['group'] == 'product']
        self.assertEqual(sum(r['value'] for r in trp), 13963000000)
        self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in trp))
        self.assertFalse(any(any(word in r['member'] for word in ['PGIMember', 'TerniumSAMember', 'OryxGtlMember'])
                             for s in ['PBA', 'TS', 'SSL'] for r in REPORTS[s]['revenue_mix']))

    def test_rounding_and_toll_adjustment_are_not_fabricated_or_double_counted(self):
        ts = [r for r in present_revenue(REPORTS['TS']['revenue_mix'], 'TS') if r['group'] == 'segment']
        self.assertEqual(sum(r['value'] for r in ts), 11981000000)
        self.assertTrue(all(r['total'] is None and '157,000' in r['share_exclusion'] for r in ts))
        sobo = present_revenue(REPORTS['SOBO']['revenue_mix'], 'SOBO')
        self.assertEqual(sum(r['value'] for r in sobo if r['group'] == 'product'), 1986000000)
        gross, = [r for r in sobo if r['group'] == 'revenue_type']
        self.assertEqual(gross['value'], 1634000000)
        self.assertIn('변동 요금 분쟁', gross['share_exclusion'])
        self.assertNotIn('리스', gross['share_exclusion'])
        old = deepcopy(gross)
        old.update(group='product', label='Capacity Arrangements And Transportation', total=1986000000)
        corrected, = present_revenue([old], 'SOBO')
        self.assertEqual(corrected['group'], 'revenue_type')
        self.assertIsNone(corrected['total'])

    def test_coordinates_require_actual_issuer_and_preserve_all_axes(self):
        for (symbol, cik, pairs), (group, member) in COORDINATES.items():
            with self.subTest(symbol=symbol, member=member):
                pairs = sorted(pairs)
                self.assertEqual(dimensions(pairs, symbol, cik), (group, member))
                self.assertIsNone(dimensions(pairs, symbol, cik + 1))
                self.assertIsNone(dimensions(pairs + [('x:ExtraAxis', 'x:UnknownMember')], symbol, cik))
                axis, first = pairs[0]
                extra = ''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a, m in pairs[1:])
                dates = dict(cik=str(cik), start='2025-07-01' if symbol == 'SSL' else '2025-01-01',
                             end='2026-06-30' if symbol == 'SSL' else '2025-12-31')
                metric = ('ifrs-full:RevenueFromContractsWithCustomers' if symbol in {'PBA', 'SSL'} and group == 'product'
                          else 'ifrs-full:Revenue' if symbol in {'PBA', 'TS', 'SSL'}
                          else 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax' if
                          (symbol, group) in {('ENB', 'segment'), ('TRP', 'product')} else 'us-gaap:Revenues')
                raw = doc(context('total', **dates) + context('part', first, axis=axis, extra=extra, **dates),
                          fact('total', '100', metric=metric) + fact('part', '70', metric=metric))
                origin = dict(label='검토된 연차 원문', level='primary', as_of='2026-09-01', url=DOCUMENTS[symbol, cik])
                row, = parse_revenue(raw, origin, symbol)
                self.assertEqual((row['group'], row['member']), (group, member))
                self.assertEqual(parse_revenue(raw.replace(str(cik), str(cik + 1)), origin, symbol), [])

    def test_actual_named_inputs_and_pending_deals_keep_roles_and_stages(self):
        self.assertTrue(any(e['registry_id'] == 'pacific-canbriam' and e['kind'] == 'supplier' for e in EDGES['ENB']))
        self.assertTrue(any(e['symbol'] == 'BWXT' and e['kind'] == 'supplier' for e in EDGES['TRP']))
        for key in ('exiros', 'gerdau-tenaris', 'techgen', 'tecpetrol', 'edison-energia'):
            self.assertTrue(any(e['registry_id'] == key and e['kind'] == 'supplier' for e in MATERIAL_EDGES['TS']))
        for key in ('eskom-sasol', 'transnet-sasol', 'al-khaleej-gas'):
            self.assertTrue(any(e['registry_id'] == key and e['kind'] == 'supplier' for e in MATERIAL_EDGES['SSL']))
        for symbol, registry in [('ENB', 'tallgrass-crude'), ('TRP', 'esentia-energy')]:
            edges = [e for e in EDGES[symbol] if e['registry_id'] == registry]
            self.assertEqual({e['kind'] for e in edges}, {'transaction'})
        self.assertTrue(any(e['registry_id'] == 'enaex-africa' and e['kind'] == 'transaction' for e in MATERIAL_EDGES['SSL']))
        self.assertEqual({e['kind'] for e in MATERIAL_EDGES['SSL'] if e['registry_id'] == 'zaffra-sasol'}, {'transaction'})
        self.assertIn('허가', str(EDGES['SOBO']))
        self.assertIn('요금', str(archive()['SOBO']['financial_context']))

    def test_clickable_supplier_project_and_reverse_relations_keep_primary_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = CompanyGraph(SimpleNamespace(personal_local_mode=True, production=False,
                dataset_dir=Path(directory) / 'data'))
            for symbol in ('ENB', 'PBA', 'TRP', 'TS', 'SSL'):
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol, name=symbol)), 'us_10')
            identifiers = {}
            for key in ('woodfibre-lng', 'pacific-canbriam', 'cedar-lng', 'greenlight-electricity',
                        'techgen', 'oryx-gtl', 'al-khaleej-gas', 'trans-mountain'):
                identifiers[key] = graph.ingest(CompanyKnowledge(**private_profile(key)))
            root = graph.by_symbol('ENB')
            edge = next(e for e in graph.relations(root['id']) if e['name'] == 'Pacific Canbriam Energy')
            self.assertTrue(graph.entity(edge['target_id'])['profile']['brief'])
            reverse = next(e for e in graph.relations(edge['target_id']) if e['target_id'] == root['id'])
            self.assertEqual(reverse['kind'], 'customer')
            self.assertEqual(reverse['source'], edge['source'])
            woodfibre = graph.entity(identifiers['woodfibre-lng'])
            self.assertTrue(any(e['name'] == 'Pacific Canbriam Energy' for e in graph.relations(woodfibre['id'])))
            trans_mountain = private_profile('trans-mountain')
            self.assertGreaterEqual(len(trans_mountain['brief']), 5)
            self.assertTrue(any(e['symbol'] == 'DINO' for e in trans_mountain['relations']))


if __name__ == '__main__':
    unittest.main()
