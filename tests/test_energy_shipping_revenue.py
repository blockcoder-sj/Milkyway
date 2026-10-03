"""Exact maritime issuer/document/FY scope and mixed statement metrics."""
from copy import deepcopy
import datetime as dt
import unittest

from cloud_app.company_energy_shipping_revenue import (
    COORDINATES, DOCUMENTS, PERIODS, EXTRA_METRICS, STATEMENT_LINES,
    CONTRACT, CONTRACT_TAX, LEASE, dimensions, extra_metrics)
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import RevenueLine
from tests.test_company_revenue import context, doc, fact


def origin(symbol,cik):
    return dict(label='검토된 연차 원문',level='primary',as_of='2026-05-28',url=DOCUMENTS[symbol,cik])


def header(end):
    return ('<ix:nonNumeric name="dei:DocumentType">20-F</ix:nonNumeric>'
            '<ix:nonNumeric name="dei:DocumentPeriodEndDate">'+end+'</ix:nonNumeric>')


def metric(symbol,group):
    if symbol=='DHT': return 'dht:ShippingRevenue'
    if symbol=='FRO': return 'ifrs-full:RevenueFromRenderingOfServices'
    if symbol=='STNG': return 'ifrs-full:Revenue'
    if symbol=='TORO': return LEASE if group=='product' else 'us-gaap:Revenues'
    if symbol=='INSW' and group=='product': return 'us-gaap:Revenues'
    if symbol=='PXS': return CONTRACT_TAX if group=='product' else 'us-gaap:Revenues'
    if symbol in {'NVGS','IMPP'}: return CONTRACT_TAX
    return CONTRACT


class ShippingRevenueTests(unittest.TestCase):
    def test_all_coordinates_are_complete_unique_and_cik_bound(self):
        self.assertEqual(len(DOCUMENTS),16)
        for (symbol,cik,pairs),expected in COORDINATES.items():
            with self.subTest(symbol=symbol,member=expected[1]):
                pairs=sorted(pairs)
                self.assertEqual(dimensions(pairs,symbol,cik),expected)
                for changed in [pairs+[pairs[0]],pairs+[('extra:Axis','extra:Member')]]:
                    self.assertIsNone(dimensions(changed,symbol,cik))
                self.assertIsNone(dimensions(pairs,symbol,cik+1))
                self.assertIsNone(dimensions(pairs,'OTHER',cik))
                if symbol=='TEN': continue  # Both original metrics must reconcile together.
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>' for a,m in pairs[1:])
                start,end=PERIODS[symbol,cik]; dates=dict(cik=str(cik),start=start,end=end)
                tag=metric(symbol,expected[0])
                raw=doc(context('total',**dates)+context('part',pairs[0][1],axis=pairs[0][0],extra=extra,**dates),
                    header(end)+fact('total','100',metric=tag,scale=0)+fact('part','70',metric=tag,scale=0))
                row,=parse_revenue(raw,origin(symbol,cik),symbol,dt.date(2026,10,3))
                self.assertEqual((row['group'],row['member'],row['value']),(*expected,70))
                self.assertEqual((row['start'],row['end']),(start,end))
                RevenueLine.model_validate(row)
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),origin(symbol,cik),symbol),[])
                self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin(symbol,cik),symbol),[])

    def test_extra_metrics_require_exact_url_issuer_cik_and_declared_year(self):
        for (symbol,cik),_ in DOCUMENTS.items():
            source=origin(symbol,cik);end=dt.date.fromisoformat(PERIODS[symbol,cik][1])
            self.assertEqual(extra_metrics(source,symbol,cik,end),EXTRA_METRICS.get(symbol,()))
            for other,ticker,identity,last in [
                ({**source,'url':source['url'].replace('.htm','-other.htm')},symbol,cik,end),
                (source,'OTHER',cik,end),(source,symbol,cik+1,end),
                (source,symbol,cik,None),(source,symbol,cik,end.replace(year=end.year-1))]:
                self.assertEqual(extra_metrics(other,ticker,identity,last),())

    def test_original_statement_metrics_keep_keys_without_invented_dimensions(self):
        for (symbol,cik),_ in DOCUMENTS.items():
            for tag,group,_ in STATEMENT_LINES.get(symbol,()):
                with self.subTest(symbol=symbol,metric=tag):
                    start,end=PERIODS[symbol,cik];dates=dict(cik=str(cik),start=start,end=end)
                    raw=doc(context('total',**dates),header(end)+fact('total','70',metric=tag,scale=0))
                    row,=parse_revenue(raw,origin(symbol,cik),symbol)
                    self.assertEqual((row['group'],row['member'],row['metric'],row['value']),(group,tag,tag,70))
                    self.assertIsNone(row['total'])
                    self.assertIn('#f-1',row['source']['url'])
                    RevenueLine.model_validate(row)
                    self.assertEqual(parse_revenue(raw.replace(header(end),''),origin(symbol,cik),symbol),[])
                    self.assertEqual(parse_revenue(raw.replace('unitRef="usd"','unitRef="eur"'),origin(symbol,cik),symbol),[])
                    typed=raw.replace('<xbrli:segment>','<xbrli:segment><xbrldi:typedMember dimension="x:Axis"><x:Value>foreign</x:Value></xbrldi:typedMember>')
                    self.assertEqual(parse_revenue(typed,origin(symbol,cik),symbol),[])
                    conflicting=raw.replace('</html>',fact('total','71',metric=tag,scale=0,anchor='conflict')+'</html>')
                    self.assertEqual(parse_revenue(conflicting,origin(symbol,cik),symbol),[])

    def test_ten_mixed_metrics_need_both_components_and_actual_statement_total(self):
        symbol,cik='TEN',1166663;source=origin(symbol,cik)
        dates=dict(cik=str(cik),start='2025-01-01',end='2025-12-31')
        contexts=context('total',**dates)+context('voyage','tnp:VoyageChartersAndContractsMember',axis='us-gaap:IncomeStatementLocationAxis',**dates)
        contexts+=context('lease','tnp:TimeBareboatAndPoolingCharterArrangementsMember',axis='srt:StatementScenarioAxis',**dates)
        total=fact('total','100',scale=0)
        voyage=fact('voyage','30',metric='us-gaap:RevenueNotFromContractWithCustomer',scale=0)
        lease=fact('lease','70',metric='tnp:OperatingLeaseLeaseIncome1',scale=0)
        raw=doc(contexts,header('2025-12-31')+total+voyage+lease)
        rows=parse_revenue(raw,source,symbol)
        self.assertEqual(len(rows),2)
        self.assertEqual(sum(r['value'] for r in rows),100)
        self.assertTrue(all(r['total'] is None and r['share_exclusion'] for r in rows))
        self.assertEqual(len({r['metric'] for r in rows}),2)
        for altered in [raw.replace(voyage,''),raw.replace(lease,''),raw.replace(total,''),raw.replace('>70</ix:nonFraction>','>71</ix:nonFraction>'),raw.replace(header('2025-12-31'),'')]:
            self.assertEqual(parse_revenue(altered,source,symbol),[])
        conflict=raw.replace('</html>',fact('lease','71',metric='tnp:OperatingLeaseLeaseIncome1',scale=0)+'</html>')
        self.assertEqual(parse_revenue(conflict,source,symbol),[])

    def test_current_document_filters_are_not_applied_to_other_documents_or_years(self):
        source=origin('KNOP',1564180)
        row=dict(group='product',member='knop:TimeAndBareboatCharterRevenuesMember',label='old subtotal',
            value=100,unit='USD',start='2025-01-01',end='2025-12-31',total=None,metric=CONTRACT,source=source)
        self.assertEqual(present_revenue([row],'KNOP'),[])
        newer={**row,'source':{**source,'url':source['url'].replace('20f.htm','other.htm')}}
        self.assertEqual(len(present_revenue([newer],'KNOP')),1)
        older={**row,'start':'2024-01-01','end':'2024-12-31'}
        self.assertEqual(len(present_revenue([older],'KNOP')),1)
        self.assertEqual(len(present_revenue([row],'OTHER')),1)
