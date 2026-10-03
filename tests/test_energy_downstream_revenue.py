"""Complete issuer coordinates, actual fiscal calendars and narrow signed guards."""
from copy import deepcopy
import datetime as dt
import unittest

from cloud_app.company_energy_downstream_revenue import COORDINATES, DOCUMENTS, PERIODS, dimensions, canonical, metric_allowed
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import RevenueLine
from tests.test_company_revenue import context, doc, fact


def origin(symbol,cik):
    return dict(label='검토된 연차 원문',level='primary',as_of='2026-05-28',url=DOCUMENTS[symbol,cik])


def metric(symbol,group):
    if symbol in {'CVI','NGL','WKC','GPRE','REX'} or (symbol=='GLP' and group=='segment'):
        return 'us-gaap:Revenues'
    if symbol=='CAPL' or (symbol=='GEVO' and group=='product'):
        return 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
    return 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'


class DownstreamRevenueTests(unittest.TestCase):
    def test_every_approved_coordinate_is_complete_issuer_bound_and_parser_supported(self):
        self.assertEqual(len(DOCUMENTS),17)
        for (symbol,cik,pairs),expected in COORDINATES.items():
            with self.subTest(symbol=symbol,member=expected[1]):
                pairs=sorted(pairs)
                self.assertEqual(dimensions(pairs,symbol,cik),expected)
                self.assertIsNone(dimensions(pairs+[pairs[0]],symbol,cik))
                self.assertIsNone(dimensions(pairs+[('extra:Axis','extra:Member')],symbol,cik))
                self.assertIsNone(dimensions(pairs,symbol,cik+1))
                self.assertIsNone(dimensions(pairs,'OTHER',cik))
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                start,end=PERIODS[symbol,cik]
                dates=dict(cik=str(cik),start=start,end=end)
                tag=metric(symbol,expected[0])
                raw=doc(context('total',**dates)+context('part',pairs[0][1],axis=pairs[0][0],extra=extra,**dates),
                        fact('total','100',metric=tag,scale=0)+fact('part','70',metric=tag,scale=0))
                row,=parse_revenue(raw,origin(symbol,cik),symbol,dt.date(2026,10,3))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                self.assertEqual((row['start'],row['end']),(start,end))
                RevenueLine.model_validate(row)
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin(symbol,cik),symbol),[])

    def test_rex_derivative_sign_is_not_allowed_on_other_products_documents_or_periods(self):
        dates=dict(cik='744187',start='2025-02-01',end='2026-01-31')
        member='rex:DerivativeFinancialInstrumentGainsLossesMember'
        raw=doc(context('total',**dates)+context('part',member,**dates),
                fact('total','650,487',scale=3)+fact('part','254',scale=3,attrs='sign="-"'))
        source=origin('REX',744187)
        row,=parse_revenue(raw,source,'REX')
        self.assertEqual((row['group'],row['value']),('revenue_type',-254000))
        self.assertIsNone(row['total'])
        self.assertIn('650,741,000',row['share_exclusion'])
        RevenueLine.model_validate(row)
        for changed,other,symbol in [
            (raw.replace(member,'rex:EthanolMember'),source,'REX'),
            (raw.replace('2025-02-01','2024-02-01').replace('2026-01-31','2025-01-31'),source,'REX'),
            (raw,{**source,'url':source['url'].replace('c115944_10k','other')},'REX'),
            (raw,source,'OTHER')]:
            self.assertEqual(parse_revenue(changed,other,symbol),[])

    def test_duplicate_onshore_alias_is_one_row_and_conflict_requires_review(self):
        source=origin('GEL',1022321)
        dates=dict(cik='1022321',start='2025-01-01',end='2025-12-31')
        axis='us-gaap:StatementBusinessSegmentsAxis'
        raw=doc(context('total',**dates)+context('a','gel:OnshoreFacilitiesAndTransportationSegmentMember',axis=axis,**dates)
            +context('b','gel:OnshoreTransportationAndServicesSegmentMember',axis=axis,**dates),
            fact('total','1,630,415',scale=3,metric=metric('GEL','segment'))
            +fact('a','779,019',scale=3,metric=metric('GEL','segment'),anchor='a')
            +fact('b','779,019',scale=3,metric=metric('GEL','segment'),anchor='b'))
        row,=parse_revenue(raw,source,'GEL')
        self.assertEqual(row['value'],779019000)
        self.assertEqual(len(present_revenue([row,deepcopy(row)],'GEL')),1)
        self.assertEqual(parse_revenue(raw.replace('>779,019</ix:nonFraction>','>779,018</ix:nonFraction>',1),source,'GEL'),[])
        conflict={**deepcopy(row),'value':779018000}
        self.assertEqual(canonical([row,conflict],'GEL',1022321),[])

    def test_metric_filter_has_exact_document_year_issuer_scope(self):
        source=origin('GPRE',1309402)
        self.assertFalse(metric_allowed('us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
            'segment','2025-01-01','2025-12-31',source,'GPRE',1309402))
        for other,symbol,cik,start,end in [
            ({**source,'url':source['url'].replace('gpre-20251231','other')},'GPRE',1309402,'2025-01-01','2025-12-31'),
            (source,'OTHER',1309402,'2025-01-01','2025-12-31'),
            (source,'GPRE',1309403,'2025-01-01','2025-12-31'),
            (source,'GPRE',1309402,'2024-01-01','2024-12-31')]:
            self.assertTrue(metric_allowed('us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
                'segment',start,end,other,symbol,cik))

    def test_declared_annual_year_does_not_fall_back_to_a_prior_product_view(self):
        source=origin('GPRE',1309402)
        current=dict(cik='1309402',start='2025-01-01',end='2025-12-31')
        old=dict(cik='1309402',start='2024-01-01',end='2024-12-31')
        header=('<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric>'
                '<ix:nonNumeric name="dei:DocumentPeriodEndDate">2025-12-31</ix:nonNumeric>')
        raw=doc(context('total',**current)+context('current','gpre:EthanolProductionMember',
            axis='us-gaap:StatementBusinessSegmentsAxis',**current)
            +context('old','gpre:DistillerGrainsMember',**old),
            header+fact('total','100',scale=0)+fact('current','70',scale=0)
            +fact('old','50',scale=0,metric='us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'))
        row,=parse_revenue(raw,source,'GPRE')
        self.assertEqual((row['group'],row['start'],row['end']),('segment','2025-01-01','2025-12-31'))
        for end in ('not-a-date','2027-12-31'):
            self.assertEqual(parse_revenue(raw.replace('name="dei:DocumentPeriodEndDate">2025-12-31',
                'name="dei:DocumentPeriodEndDate">'+end),source,'GPRE'),[])

    def test_only_obsolete_gpre_current_annual_cache_is_removed(self):
        source=origin('GPRE',1309402)
        row=dict(group='product',member='gpre:DistillerGrainsMember',label='Distiller Grains',
            value=98675000,unit='USD',start='2024-01-01',end='2024-12-31',total=162973000,
            metric='us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',source=source)
        self.assertEqual(present_revenue([row],'GPRE'),[])
        other={**row,'source':{**source,'url':source['url'].replace('gpre-20251231','other')}}
        self.assertEqual(len(present_revenue([other],'GPRE')),1)
        self.assertEqual(len(present_revenue([row],'OTHER')),1)
        self.assertEqual(len(present_revenue([{**row,'start':'2023-01-01','end':'2023-12-31'}],'GPRE')),1)
