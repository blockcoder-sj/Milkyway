"""Exact observed exhibit/parent identity; no network or invented annual header."""
import datetime as dt
import unittest

from cloud_app.company_annual_attachments import (
    parse_attached_financials, parse_attached_revenue, same_annual_accession,
)
from cloud_app.company_annual_financials import parse_annual_financials
from tests.test_company_annual_financials import annual
from tests.test_company_revenue import context, doc, fact, ORIGIN

EXHIBIT = {**ORIGIN, 'url': ORIGIN['url'].rsplit('/', 1)[0] + '/financials.htm', 'level':'primary'}
PARENT = {**ORIGIN, 'level':'primary'}
TODAY = dt.date(2026, 10, 3)


def cover(link='financials.htm', form='40-F', period='2026-01-25'):
    return annual(context('year'), f'<a href="{link}">Audited financial statements</a>',
                  form=form, period=period)


class AnnualAttachmentTests(unittest.TestCase):
    def parse(self, raw=None, origin=None, parent_raw=None, parent_origin=None, cik=1045810):
        return parse_attached_financials(
            raw if raw is not None else doc(context('year'), fact('year','100')),
            origin or EXHIBIT, cik,
            parent_raw if parent_raw is not None else cover(), parent_origin or PARENT, TODAY)

    def test_observed_attachment_uses_parent_period_and_its_own_fact_citation(self):
        raw = doc(context('year'),fact('year','100',anchor='reported'))
        self.assertEqual(parse_annual_financials(raw,EXHIBIT,1045810,TODAY),[])
        row, = self.parse(raw)
        self.assertEqual(row['value'],100000000)
        self.assertEqual(row['period'],'2025-01-27 ~ 2026-01-25')
        self.assertEqual(row['source']['url'],EXHIBIT['url']+'#reported')
        self.assertIn('XBRL',row['source']['label'])
        self.assertEqual(len(self.parse(parent_raw=cover(EXHIBIT['url']))),1)

    def test_same_issuer_or_accession_without_actual_cover_link_is_rejected(self):
        self.assertEqual(self.parse(parent_raw=cover('different.htm')),[])
        self.assertEqual(self.parse(parent_raw=cover('financials.htm?version=2')),[])
        self.assertEqual(self.parse(parent_raw=cover('https://evil.test/financials.htm')),[])

    def test_url_date_authority_and_exact_accession_must_agree(self):
        for change in [
            {'url':EXHIBIT['url'].replace('/1045810/','/999/')},
            {'url':EXHIBIT['url'].replace('www.sec.gov','evil.test')},
            {'url':EXHIBIT['url']+'?x=1'},
            {'url':EXHIBIT['url']+'#anchor'},
            {'url':PARENT['url']},
            {'as_of':'2026-03-01'},
            {'level':'reference'},
        ]:
            with self.subTest(change=change):
                self.assertEqual(self.parse(origin={**EXHIBIT,**change}),[])
        directory=EXHIBIT['url'].rsplit('/',1)[0]
        different=directory.rsplit('/',1)[0]+'/000000000000000001/financials.htm'
        self.assertFalse(same_annual_accession({**EXHIBIT,'url':different},PARENT,1045810))
        self.assertFalse(same_annual_accession(EXHIBIT,PARENT,True))

    def test_quarterly_future_or_conflicting_headers_are_rejected(self):
        for parent in [cover(form='10-Q'),cover(period='2027-01-25')]:
            self.assertEqual(self.parse(parent_raw=parent),[])
        self.assertEqual(self.parse(raw=annual(context('year'),fact('year','100'),form='10-Q')),[])
        self.assertEqual(self.parse(raw=annual(context('year'),fact('year','100'),period='2025-12-31')),[])
        self.assertEqual(self.parse(origin={**EXHIBIT,'as_of':'2027-03-01'},
                                   parent_origin={**PARENT,'as_of':'2027-03-01'}),[])

    def test_facts_still_require_exact_consolidated_issuer_annual_period(self):
        for raw in [doc(context('year').replace('1045810','999'),fact('year','100')),
                    doc(context('year','us-gaap:ProductMember'),fact('year','100')),
                    doc(context('year',start='2025-10-26'),fact('year','100')),
                    doc(context('year'),fact('year','100')+fact('year','90'))]:
            self.assertEqual(self.parse(raw),[])

    def test_parent_shared_resources_and_conflicting_ids_are_handled_conservatively(self):
        raw = '<html>'+fact('year','100')+'</html>'
        row, = self.parse(raw)
        self.assertEqual(row['value'],100000000)
        # Neither an exhibit override nor the cover wins a conflicting ID.
        conflicting=doc(context('year').replace('1045810','999'),fact('year','100'))
        self.assertEqual(self.parse(conflicting),[])
        conflicting_unit=doc('',fact('year','100')).replace('iso4217:USD','iso4217:CAD')
        self.assertEqual(self.parse(conflicting_unit),[])
        self.assertEqual(self.parse(raw,parent_raw=cover('other.htm')),[])

    def test_space_grouped_original_numbers_preserve_scale_and_reject_bad_groups(self):
        row, = self.parse('<html>'+fact('year','52 377')+'</html>')
        self.assertEqual(row['value'],52377000000)
        for malformed in ('52 37','5 2377','52, 377','52 377 USD','52 377e3'):
            self.assertEqual(self.parse('<html>'+fact('year',malformed)+'</html>'),[])

    def test_revenue_uses_observed_parent_resources_and_declared_year_only(self):
        segments=context('seg','us-gaap:ProductMember')
        parent=annual(context('year')+segments,'<a href="financials.htm">Financials</a>',form='40-F')
        raw='<html>'+fact('year','100')+fact('seg','40')+'</html>'
        rows=parse_attached_revenue(raw,EXHIBIT,'NVDA',1045810,parent,PARENT,TODAY)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['value'],40000000)
        self.assertEqual(rows[0]['total'],100000000)
        self.assertTrue(rows[0]['source']['url'].startswith(EXHIBIT['url']))
        wrong=parent.replace('2025-01-27','2024-01-27').replace('2026-01-25','2025-01-25')
        # Matching resources are now last year's contexts, so the declared header
        # also changes with them; an exhibit's conflicting period is rejected.
        conflicting=annual('',fact('seg','40'),period='2026-01-25')
        self.assertEqual(parse_attached_revenue(conflicting,EXHIBIT,'NVDA',1045810,wrong,PARENT,TODAY),[])


if __name__ == '__main__':
    unittest.main()
