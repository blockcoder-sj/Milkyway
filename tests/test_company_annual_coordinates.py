"""Reviewed totals cannot authorize another issuer, year, metric or dimension."""
import datetime as dt
from decimal import Decimal
import unittest

from cloud_app.company_annual_coordinates import SU, VET, IMO, VET_AGGREGATE
from cloud_app.company_annual_financials import parse_annual_financials
from cloud_app.company_financial_labels import presented
from cloud_app.company_xbrl_precision import reported_value
from tests.test_company_annual_financials import annual
from tests.test_company_revenue import context, fact


class AnnualCoordinateTests(unittest.TestCase):
    def origin(self, url):
        return dict(label='SEC 원문',url=url,as_of='2026-03-04',level='primary')

    def parse(self, raw, url=VET, cik=1293135):
        return parse_annual_financials(raw,self.origin(url),cik,dt.date(2026,10,3))

    def test_vermillion_exact_aggregate_context_is_limited_to_balance_and_cash_flow(self):
        axis,member=VET_AGGREGATE
        dates=dict(start='2025-01-01',end='2025-12-31',cik='1293135')
        total=context('total',**dates)
        both=context('both',member,axis=axis,**dates)
        balance=both.replace('id="both"','id="balance"').replace(
            '<xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate>',
            '<xbrli:instant>2025-12-31</xbrli:instant>')
        raw=annual(total+both+balance,fact('total','100',metric='ifrs-full:Revenue')+
                   fact('both','120',metric='ifrs-full:Revenue')+
                   fact('both','80',metric='ifrs-full:CashFlowsFromUsedInOperatingActivities')+
                   fact('balance','200',metric='ifrs-full:Assets'),period='2025-12-31',form='40-F')
        self.assertEqual([r['value'] for r in self.parse(raw)],[100000000,200000000,80000000])
        # Unreviewed document/year only retains the actual undimensioned revenue.
        self.assertEqual(len(self.parse(raw,url=VET.replace('ex99d3','ex99d2'))),1)
        self.assertEqual(len(self.parse(raw.replace('2025','2024'))),1)
        self.assertEqual(len(self.parse(raw.replace(member,'ifrs-full:DiscontinuedOperationsMember'))),1)
        extra='<xbrldi:explicitMember dimension="ifrs-full:GeographicalAreasAxis">country:CA</xbrldi:explicitMember>'
        self.assertEqual(len(self.parse(raw.replace('</xbrldi:explicitMember>',
            '</xbrldi:explicitMember>'+extra))),1)
        self.assertEqual(len(self.parse(raw.replace('1293135','1293136'),url=VET.replace('1293135','1293136'),cik=1293136)),1)

    def test_suncor_visible_cash_flow_tags_are_document_and_year_bound(self):
        dates=dict(start='2025-01-01',end='2025-12-31',cik='311337')
        raw=annual(context('year',**dates),
            fact('year','12781',metric='ifrs-full:CashFlowsFromUsedInOperations')+
            fact('year','5856',metric='su:CashFlowsUsedForCapitalExpenditures'),period='2025-12-31',form='40-F')
        self.assertEqual([r['value'] for r in self.parse(raw,SU,311337)],[12781000000,5856000000])
        self.assertEqual(self.parse(raw,SU.replace('ex99d2','ex99d3'),311337),[])
        self.assertEqual(self.parse(raw.replace('2025','2024'),SU,311337),[])
        self.assertEqual(self.parse(raw.replace('311337','311338'),SU.replace('311337','311338'),311338),[])

    def test_imperial_revenue_and_other_income_label_only_applies_to_reviewed_table(self):
        dates=dict(start='2025-01-01',end='2025-12-31',cik='49938')
        raw=annual(context('year',**dates),fact('year','47078'),period='2025-12-31')
        row,=self.parse(raw,IMO,49938)
        self.assertEqual(row['label'],'매출·기타소득 합계')
        self.assertEqual(self.parse(raw.replace('2025','2024'),IMO,49938)[0]['label'],'매출')
        legacy={**row,'label':'매출'}
        self.assertEqual(presented([legacy])[0]['label'],row['label'])
        self.assertEqual(legacy['label'],'매출')

    def test_coarse_repeat_selects_the_actual_more_precise_fact_and_anchor(self):
        dates=dict(start='2025-01-01',end='2025-12-31',cik='1293135')
        balance=context('cash',**dates).replace(
            '<xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate>',
            '<xbrli:instant>2025-12-31</xbrli:instant>')
        exact=fact('cash','2,740',metric='ifrs-full:CashAndCashEquivalents',attrs='decimals="-6"',anchor='balance')
        coarse=fact('cash','2.7',scale='9',metric='ifrs-full:CashAndCashEquivalents',attrs='decimals="-8"',anchor='note')
        row,=self.parse(annual(balance,coarse+exact,period='2025-12-31',form='40-F'))
        self.assertEqual(row['value'],2740000000)
        self.assertTrue(row['source']['url'].endswith('#balance'))
        for conflict in [exact.replace('2,740','2,741'),coarse.replace('2.7','2.6'),coarse.replace('decimals="-8"','')]:
            self.assertEqual(self.parse(annual(balance,exact+conflict,period='2025-12-31',form='40-F')),[])

    def test_rounding_never_averages_missing_precision_or_conflicting_exact_values(self):
        d=Decimal
        self.assertIsNone(reported_value({(d('10'),0),(d('11'),0)}))
        self.assertIsNone(reported_value({(d('10'),None),(d('10.1'),1)}))
        self.assertIsNone(reported_value({(d('10'),0),(d('10.49'),1)}))
        self.assertEqual(reported_value({(d('10'),0),(d('10.4'),1)}),d('10.4'))
        self.assertEqual(reported_value({(d('10'),0),(d('10.5'),17)}),d('10.5'))


if __name__ == '__main__':
    unittest.main()
