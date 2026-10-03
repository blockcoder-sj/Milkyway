"""Revenue coordinates are bound to issuer, original report and fiscal period."""
import datetime as dt
import unittest

from cloud_app.company_energy_land_revenue import (
    COORDINATES,DOCUMENTS,PERIODS,STATEMENT_LINES,EXTRA_METRICS,
    CONTRACT,CONTRACT_TAX,LEASE,NRP_SEGMENT,dimensions,extra_metrics)
from cloud_app.company_revenue import parse_revenue
from cloud_app.company_schemas import RevenueLine
from tests.test_company_revenue import context,doc,fact


def origin(symbol,cik):
    return dict(label='검토된 연차 원문',level='primary',as_of='2026-06-30',url=DOCUMENTS[symbol,cik])


def header(end):
    return ('<ix:nonNumeric name="dei:DocumentType">10-K</ix:nonNumeric>'
            '<ix:nonNumeric name="dei:DocumentPeriodEndDate">'+end+'</ix:nonNumeric>')


def metric(symbol,group,member):
    if symbol in {'DMLP','PNRG'}:return CONTRACT_TAX
    if symbol=='MNR':return 'us-gaap:Revenues'
    if symbol=='NRP':return NRP_SEGMENT if group=='segment' else 'us-gaap:Revenues'
    if symbol=='CKX' and member=='ckx:SurfaceLeasesUnrelatedPartiesMember':return LEASE
    return CONTRACT


class LandRevenueTests(unittest.TestCase):
    def test_multiaxis_coordinates_and_wrong_issuer_currency_are_checked(self):
        self.assertEqual(len(DOCUMENTS),11)
        for (symbol,cik,pairs),expected in COORDINATES.items():
            with self.subTest(symbol=symbol,member=expected[1]):
                pairs=sorted(pairs)
                self.assertEqual(dimensions(pairs,symbol,cik),expected)
                for invalid in [pairs+[pairs[0]],pairs+[('x:Axis','x:Member')]]:
                    self.assertIsNone(dimensions(invalid,symbol,cik))
                self.assertIsNone(dimensions(pairs,symbol,cik+1))
                self.assertIsNone(dimensions(pairs,'OTHER',cik))
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                start,end=PERIODS[symbol,cik];dates=dict(cik=str(cik),start=start,end=end)
                tag=metric(symbol,*expected)
                raw=doc(context('total',**dates)+context('part',pairs[0][1],axis=pairs[0][0],extra=extra,**dates),
                        header(end)+fact('total','100',metric=tag,scale=0)+fact('part','70',metric=tag,scale=0))
                row,=parse_revenue(raw,origin(symbol,cik),symbol,dt.date(2026,10,4))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                RevenueLine.model_validate(row)
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin(symbol,cik),symbol),[])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin(symbol,cik),symbol),[])

    def test_statement_adjustments_keep_signed_values_without_fake_dimensions(self):
        for (symbol,cik),_ in DOCUMENTS.items():
            for tag,_ in STATEMENT_LINES.get(symbol,()):
                with self.subTest(symbol=symbol,metric=tag):
                    start,end=PERIODS[symbol,cik];dates=dict(cik=str(cik),start=start,end=end)
                    raw=doc(context('total',**dates),header(end)+fact('total','70',metric=tag,scale=0))
                    row,=parse_revenue(raw,origin(symbol,cik),symbol)
                    self.assertEqual((row['group'],row['member'],row['metric'],row['value']),('revenue_type',tag,tag,70))
                    negative=raw.replace('name="'+tag+'"','sign="-" name="'+tag+'"')
                    row,=parse_revenue(negative,origin(symbol,cik),symbol)
                    self.assertEqual(row['value'],-70)
                    self.assertTrue(row['total'] is None and row['share_exclusion'])
                    self.assertEqual(parse_revenue(raw.replace(header(end),''),origin(symbol,cik),symbol),[])
                    conflict=raw.replace('</html>',fact('total','71',metric=tag,scale=0,anchor='conflict')+'</html>')
                    self.assertEqual(parse_revenue(conflict,origin(symbol,cik),symbol),[])

    def test_added_metrics_do_not_leak_to_other_documents_years_or_issuers(self):
        for (symbol,cik),_ in DOCUMENTS.items():
            source=origin(symbol,cik);end=dt.date.fromisoformat(PERIODS[symbol,cik][1])
            self.assertEqual(extra_metrics(source,symbol,cik,end),EXTRA_METRICS.get(symbol,()))
            for other,ticker,identity,last in [
                ({**source,'url':source['url'].replace('.htm','-other.htm')},symbol,cik,end),
                (source,'OTHER',cik,end),(source,symbol,cik+1,end),
                (source,symbol,cik,None),(source,symbol,cik,end.replace(year=end.year-1))]:
                self.assertEqual(extra_metrics(other,ticker,identity,last),())
