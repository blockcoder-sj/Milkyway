"""Original annual receipts never imply business research completion."""
from copy import deepcopy
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_financial_archive import archive, editorial, validate_archive
from cloud_app.company_provenance import clean
from cloud_app.company_schemas import CompanyKnowledge


class EnergyFinancialArchiveTests(unittest.TestCase):
    def test_all_original_coordinates_and_issuer_identities_validate(self):
        records = archive()
        self.assertEqual(len(records), 205)
        self.assertEqual(sum(bool(r['financials']) for r in records.values()), 200)
        self.assertEqual(sum(len(r['financials']) for r in records.values()), 1567)
        self.assertEqual(records['STNG']['financials'][0]['value'], 938222000)
        self.assertEqual(records['PBA']['financials'][0]['value'], 7778000000)

    def test_large_bp_receipt_metadata_does_not_bypass_size_bound_or_original_identity(self):
        raw={'BP':deepcopy(archive()['BP'])}
        self.assertEqual(raw['BP']['annual']['bytes'],29303585)
        self.assertEqual(raw['BP']['financials'][0]['value'],192549000000)
        self.assertTrue(validate_archive(raw))
        raw['BP']['annual']['bytes']=48*1024*1024+1
        with self.assertRaises(ValueError):
            validate_archive(raw)

    def test_foreign_source_or_unverified_issuer_is_rejected(self):
        raw = {'ACDC': deepcopy(archive()['ACDC'])}
        for field, value in [('cik', '928054'), ('cik', '0')]:
            bad = deepcopy(raw); bad['ACDC'][field] = value
            with self.assertRaises(ValueError):
                validate_archive(bad)
        bad = deepcopy(raw)
        bad['ACDC']['financials'][0]['source']['url'] = archive()['FTK']['annual']['url']
        with self.assertRaises(ValueError):
            validate_archive(bad)
        with self.assertRaises(ValueError):
            validate_archive({'UNKNOWN': raw['ACDC']})

    def test_annual_exhibit_receipt_preserves_exact_parent_and_declared_period(self):
        raw={'ACDC':deepcopy(archive()['ACDC'])}
        record=raw['ACDC']
        record['parent_annual']=deepcopy(record['annual'])
        record['parent_annual']['url']=record['annual']['url'].rsplit('/',1)[0]+'/cover.htm'
        record['annual_period_end']='2025-12-31'
        result=validate_archive(raw)['ACDC']
        self.assertEqual(result['parent_annual']['sha256'],record['parent_annual']['sha256'])
        self.assertTrue(result['financials'][0]['source']['url'].startswith(record['annual']['url']))
        for change in ('period','date','issuer','accession','authority','level','missing_parent','missing_period'):
            bad=deepcopy(raw);entry=bad['ACDC'];parent=entry['parent_annual']
            if change=='period':entry['annual_period_end']='2024-12-31'
            if change=='date':parent['as_of']='2026-03-01'
            if change=='issuer':parent['url']=archive()['FTK']['annual']['url']
            if change=='accession':parent['url']=parent['url'].rsplit('/',2)[0]+'/000000000000000001/cover.htm'
            if change=='authority':parent['url']=parent['url'].replace('www.sec.gov','evil.test')
            if change=='level':parent['level']='provider'
            if change=='missing_parent':entry['parent_annual']=None
            if change=='missing_period':entry['annual_period_end']=None
            with self.subTest(change=change),self.assertRaises(ValueError):
                validate_archive(bad)

    def test_historical_scopes_stay_visible_and_cannot_be_silently_dropped(self):
        for symbol in ('XOM', 'HOS', 'NINE', 'ACDC'):
            result = enrich(CompanyKnowledge(symbol=symbol, name=symbol))
            self.assertTrue(result.financial_context)
            self.assertTrue(result.financials)
        raw = {'XOM': deepcopy(archive()['XOM'])}
        raw['XOM']['financial_context'] = []
        with self.assertRaises(ValueError):
            validate_archive(raw)

    def test_edited_filing_coordinate_replaces_old_label_but_preserves_other_periods(self):
        figure = deepcopy(archive()['ACDC']['financials'][0])
        old = deepcopy(figure)
        old['label'] = '매출'
        old['source']['label'] = 'SEC XBRL · RevenueFromContractWithCustomerExcludingAssessedTax'
        old['source']['url'] = old['source']['url'].split('#')[0] + '#old'
        prior = deepcopy(old); prior['period'] = '2024-01-01 ~ 2024-12-31'
        result = enrich(CompanyKnowledge(symbol='ACDC', name='ProFrac', financials=[old, prior]))
        current = [r for r in result.financials if r.period == figure['period'] and '매출' in r.label]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0].source.url, figure['source']['url'])
        self.assertTrue(any(r.period == prior['period'] for r in result.financials))

    def test_mutating_returned_editorial_does_not_change_shared_archive(self):
        result = editorial('ACDC')
        result['financials'].clear()
        result['financial_context'].clear()
        self.assertEqual(len(editorial('ACDC')['financials']), 9)
        self.assertEqual(len(editorial('ACDC')['financial_context']), 1)

    def test_matching_api_figure_is_corroboration_not_a_second_reported_value(self):
        original = deepcopy(archive()['FTK']['financials'][0])
        api = deepcopy(original)
        api['source']['label'] = 'SEC XBRL · RevenueFromContractWithCustomerExcludingAssessedTax'
        api['source']['url'] = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000928054.json'
        result = enrich(CompanyKnowledge(symbol='FTK',name='Flotek',financials=[api]))
        matches = [r for r in result.financials if r.period == original['period'] and r.value == original['value']]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].source.url, original['source']['url'])
        self.assertTrue(any(s.url == api['source']['url'] for s in result.sources))
        self.assertEqual(enrich(result).model_dump(), result.model_dump())

    def test_api_dedup_requires_exact_issuer_metric_currency_period_date_and_value(self):
        from cloud_app.company_financial_coordinates import corroborates
        original = deepcopy(archive()['FTK']['financials'][0])
        api = deepcopy(original)
        api['source']['label'] = 'SEC XBRL · RevenueFromContractWithCustomerExcludingAssessedTax'
        api['source']['url'] = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000928054.json'
        self.assertTrue(corroborates(original,api))
        for key,value in [('value',original['value']+1),('unit','EUR'),('period','2024-01-01 ~ 2024-12-31')]:
            with self.subTest(key=key):
                changed=deepcopy(api);changed[key]=value
                self.assertFalse(corroborates(original,changed))
        for key,value in [('url',api['source']['url'].replace('0000928054','0001881487')),
                          ('url',original['source']['url']),('as_of','2026-08-10'),
                          ('label','SEC XBRL · Revenues'),('level','provider')]:
            with self.subTest(key=key,value=value):
                changed=deepcopy(api);changed['source'][key]=value
                self.assertFalse(corroborates(original,changed))

    def test_financial_scope_uses_same_encyclopedia_rejection_policy(self):
        origin = dict(label='Wikipedia', url='https://en.wikipedia.org/wiki/Example')
        value = clean(dict(name='Example', financial_context=[dict(title='Scope', source=origin)]))
        self.assertEqual(value['financial_context'], [])

    def test_original_annual_requires_currency_period_and_unique_coordinate(self):
        raw = {'ACDC': deepcopy(archive()['ACDC'])}
        for change in ('currency', 'period', 'instant_revenue', 'duplicate', 'metric', 'naive_receipt'):
            bad = deepcopy(raw); figure = bad['ACDC']['financials'][0]
            if change == 'currency': figure['unit'] = 'usd'
            if change == 'period': figure['period'] = '2025-10-01 ~ 2025-12-31'
            if change == 'instant_revenue': figure['period'] = '2025-12-31'
            if change == 'duplicate': bad['ACDC']['financials'] = [figure, figure]
            if change == 'metric': figure['source']['label'] = 'SEC 연차 원문 XBRL · x:Guess'
            if change == 'naive_receipt': bad['ACDC']['annual']['collected_at'] = '2026-10-02T12:00:00'
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_archive(bad)
