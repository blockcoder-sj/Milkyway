"""Reported annual slices; no live providers or AI calls."""
import datetime as dt
import unittest

from cloud_app.company_revenue import parse_revenue, present_revenue, source_cik
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.company_retention import preserve_previous

ORIGIN = dict(label='SEC · 10-K', level='primary', as_of='2026-02-25',
    url='https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm')


def context(key, member=None, axis='srt:ProductOrServiceAxis', start='2025-01-27', end='2026-01-25', extra='', cik='1045810'):
    member = f'<xbrldi:explicitMember dimension="{axis}">{member}</xbrldi:explicitMember>' if member else ''
    return f'<xbrli:context id="{key}"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{cik}</xbrli:identifier><xbrli:segment>{member}{extra}</xbrli:segment></xbrli:entity><xbrli:period><xbrli:startDate>{start}</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate></xbrli:period></xbrli:context>'


def fact(ctx, value, metric='us-gaap:Revenues', scale=6, unit='usd', attrs='', anchor='f-1'):
    return f'<ix:nonFraction name="{metric}" contextRef="{ctx}" unitRef="{unit}" format="ixt:num-dot-decimal" scale="{scale}" id="{anchor}" {attrs}>{value}</ix:nonFraction>'


def doc(contexts, facts):
    return '<html><xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit><xbrli:unit id="eur"><xbrli:measure>iso4217:EUR</xbrli:measure></xbrli:unit>' + contexts + facts + '</html>'


class RevenueTests(unittest.TestCase):
    def parse(self, raw, symbol='NVDA'):
        return parse_revenue(raw, ORIGIN, symbol, dt.date(2026, 10, 1))

    def test_chevron_keeps_both_segment_and_geography_with_external_only_coordinates(self):
        origin = {**ORIGIN, 'url':'https://www.sec.gov/Archives/edgar/data/93410/000009341026000078/cvx-20251231.htm'}
        contexts = context('total', cik='93410') + context('parent', 'us-gaap:ReportableSegmentAggregationBeforeOtherOperatingSegmentMember',
            axis='us-gaap:StatementBusinessSegmentsAxis', cik='93410')
        facts = fact('total','184,432') + fact('parent','184,328')
        for index,(segment,region,value) in enumerate([
            ('Upstream','country:US','19,608'),('Upstream','us-gaap:NonUsMember','33,844'),
            ('Downstream','country:US','65,331'),('Downstream','us-gaap:NonUsMember','65,545'),
        ]):
            geography=f'<xbrldi:explicitMember dimension="srt:StatementGeographicalAxis">{region}</xbrldi:explicitMember>'
            contexts += context(str(index),'cvx:'+segment+'SegmentMember',axis='us-gaap:StatementBusinessSegmentsAxis',extra=geography,cik='93410')
            facts += fact(str(index),value)
        raw = doc(contexts,facts)
        rows = parse_revenue(raw,origin,'CVX')
        self.assertEqual(len(rows),5)
        self.assertEqual(len([r for r in rows if r['parent']]),4)
        self.assertTrue(all('/' in r['member'] for r in rows if r['parent']))
        self.assertEqual(len({r['label'] for r in rows}),5)
        CompanyKnowledge(symbol='CVX', name='Chevron',revenue_mix=rows)
        # No geography silently dropped; qualifier/internal-sales and extra axes fail closed.
        extra='<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        internal=raw.replace('</xbrli:segment>',extra+'</xbrli:segment>')
        self.assertEqual(parse_revenue(internal,origin,'CVX'),[])
        self.assertEqual(len(parse_revenue(raw,origin,'OTHER')),1)
        self.assertEqual(parse_revenue(raw,{**origin,'url':origin['url'].replace('www.sec.gov','evil.test')},'CVX'),[])

    def test_valero_only_accepts_reviewed_product_segment_pair(self):
        origin={**ORIGIN,'url':'https://www.sec.gov/Archives/edgar/data/1035002/000162828026011499/vlo-20251231.htm'}
        metric='us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
        extra='<xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">vlo:RefiningMember</xbrldi:explicitMember>'
        raw=doc(context('total',cik='1035002')+context('p','vlo:GasolineAndBlendstocksMember',extra=extra,cik='1035002'),
                fact('total','122,687',metric=metric)+fact('p','50,917',metric=metric))
        row,=parse_revenue(raw,origin,'VLO')
        self.assertEqual(row['label'],'휘발유·혼합 기재')
        self.assertEqual(row['total'],122687000000)
        self.assertEqual(parse_revenue(raw.replace('vlo:RefiningMember','vlo:EthanolMember'),origin,'VLO'),[])
        self.assertEqual(parse_revenue(raw,origin,'OTHER'),[])

    def test_conocophillips_subtotal_not_added_again_and_old_cache_labels_updated(self):
        origin={**ORIGIN,'url':'https://www.sec.gov/Archives/edgar/data/1163165/000116316526000009/cop-20251231.htm'}
        members=[('AlaskaSegment',5638),('LowerFortyEightSegment',41395),('CanadaOperatingSegment',3625),
                 ('EuropeMiddleEastAndNorthAfricaSegment',6484),('AsiaPacificOperatingSegment',1770),('TotalSegments',58912),('CorporateSegment',32)]
        contexts=context('total',cik='1163165');facts=fact('total','58,944')
        for member,value in members:
            contexts+=context(member,'cop:'+member+'Member',axis='us-gaap:StatementBusinessSegmentsAxis',cik='1163165')
            facts+=fact(member,str(value))
        rows=parse_revenue(doc(contexts,facts),origin,'COP')
        self.assertEqual(sum(r['value'] for r in rows if not r['parent']),58944000000)
        self.assertEqual(len([r for r in rows if r['parent']]),5)
        cached=[dict(r,parent=None,label='English') for r in rows]
        revised=present_revenue(cached,'COP')
        self.assertTrue(all(r['label']!='English' for r in revised))
        self.assertEqual(sum(r['value'] for r in revised if not r['parent']),58944000000)

    def test_curated_revenue_replaces_same_filing_coordinates_without_cache_duplicates(self):
        from cloud_app.company_catalog import enrich
        from cloud_app.company_energy_research import REPORTS
        original=REPORTS['COP']['revenue_mix']
        legacy=[dict(r,label='Old English label',parent=None) for r in original]
        # An independent, later source must remain intact.
        newer={**legacy[0], 'source':{**legacy[0]['source'],'url':'https://www.sec.gov/Archives/edgar/data/1163165/000116316526000099/cop-another.htm'}}
        value=enrich(CompanyKnowledge(symbol='COP',name='ConocoPhillips',revenue_mix=legacy+[newer]))
        self.assertEqual(len(value.revenue_mix),len(original)+1)
        self.assertTrue(any(r.source.url.endswith('cop-another.htm') for r in value.revenue_mix))
        self.assertEqual(value.model_dump(),enrich(value).model_dump())

    def test_reported_units_denominator_hierarchy_and_latest_period(self):
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember')
            + context('c', 'nvda:ComputeMember') + context('n', 'nvda:NetworkingMember')
            + context('old', 'nvda:DataCenterMember', start='2024-01-27', end='2025-01-25'),
            fact('total', '200') + fact('p', '150') + fact('c', '100') + fact('n', '50') + fact('old', '90'))
        rows = self.parse(raw)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row['total'] == 200000000 for row in rows))
        self.assertTrue(all(row['end'] == '2026-01-25' for row in rows))
        child = next(row for row in rows if row['label'] == '컴퓨팅')
        self.assertEqual(child['parent'], 'nvda:DataCenterMember')
        self.assertEqual(child['value'], 100000000)
        self.assertTrue(child['source']['url'].endswith('#f-1'))
        self.assertEqual(len(CompanyKnowledge(symbol='NVDA', name='NVIDIA', revenue_mix=rows).revenue_mix), 3)

    def test_unknown_overlap_not_guessed_and_other_issuer_no_hierarchy(self):
        raw = doc(context('p', 'nvda:DataCenterMember') + context('c', 'nvda:ComputeMember')
            + context('n', 'nvda:NetworkingMember'), fact('p', '150') + fact('c', '100') + fact('n', '49'))
        self.assertTrue(all(row['parent'] is None for row in self.parse(raw)))
        raw = raw.replace('49<', '50<')
        self.assertTrue(all(row['parent'] is None for row in self.parse(raw, 'OTHER')))

    def test_alternate_product_service_split_is_a_separate_view(self):
        raw = doc(context('total') + context('p', 'msft:ServerProductsAndCloudServicesMember')
            + context('goods', 'us-gaap:ProductMember') + context('services', 'us-gaap:ServiceOtherMember'),
            fact('total', '200') + fact('p', '150') + fact('goods', '40') + fact('services', '160'))
        rows = self.parse(raw, 'MSFT')
        self.assertEqual(len([row for row in rows if row['group'] == 'product']), 1)
        self.assertEqual(len([row for row in rows if row['group'] == 'revenue_type']), 2)

    def test_no_wrong_currency_metric_period_or_dimensional_denominator(self):
        for denominator in [
            fact('total', '200', unit='eur'),
            fact('total', '200', metric='us-gaap:SalesRevenueNet'),
            fact('prior', '200'), fact('slice', '200'),
        ]:
            with self.subTest(denominator=denominator):
                raw = doc(context('total') + context('prior', start='2024-01-27', end='2025-01-25')
                    + context('slice', 'nvda:OtherMember') + context('p', 'nvda:DataCenterMember'),
                    fact('p', '150') + denominator)
                target = next(row for row in self.parse(raw) if row['member'] == 'nvda:DataCenterMember')
                self.assertIsNone(target['total'])

    def test_reject_multiple_typed_future_short_and_other_issuer_contexts(self):
        cases = [
            dict(extra='<xbrldi:explicitMember dimension="srt:MajorCustomersAxis">x:OtherMember</xbrldi:explicitMember>'),
            dict(extra='<xbrldi:typedMember dimension="x:Axis">value</xbrldi:typedMember>'),
            dict(end='2026-12-31'), dict(start='2025-12-01'), dict(cik='9999'),
            dict(axis='srt:MajorCustomersAxis'), dict(start='not-a-date'),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.parse(doc(context('p', 'nvda:DataCenterMember', **args), fact('p', '150'))), [])

    def test_numeric_and_conflicting_fact_guards(self):
        for value, attrs, scale in [('NaN', '', 6), ('1e9', '', 6), ('1,50', '', 6),
            ('150', 'xsi:nil="true"', 6), ('150', 'sign="-"', 6), ('150', '', 20),
            ('99999999999999999', '', 6)]:
            with self.subTest(value=value, attrs=attrs, scale=scale):
                self.assertEqual(self.parse(doc(context('p', 'nvda:DataCenterMember'), fact('p', value, attrs=attrs, scale=scale))), [])
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember'),
            fact('total', '200') + fact('total', '201') + fact('p', '150'))
        self.assertIsNone(self.parse(raw)[0]['total'])
        raw += fact('p', '151')
        self.assertEqual(self.parse(raw), [])

    def test_slice_larger_than_consolidated_total_has_no_percentage(self):
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember'), fact('total', '100') + fact('p', '150'))
        self.assertIsNone(self.parse(raw)[0]['total'])

    def test_amd_reported_operating_qualifier_and_product_children(self):
        origin = {**ORIGIN, 'url': 'https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm'}
        qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        contexts = context('total', cik='2488')
        facts = fact('total', '34,639')
        for key, member, value in [('dc', 'Datacenter', '16,635'), ('cg', 'ClientAndGaming', '14,550'), ('e', 'Embedded', '3,454')]:
            contexts += context(key, 'amd:' + member + 'Member', axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier, cik='2488')
            facts += fact(key, value)
        for key, member, segment, value in [('c', 'Client', 'ClientAndGaming', '10,640'), ('g', 'Gaming', 'Gaming', '3,910')]:
            extra = '<xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">amd:' + segment + 'Member</xbrldi:explicitMember>'
            contexts += context(key, 'amd:' + member + 'Member', extra=extra, cik='2488')
            facts += fact(key, value)
        raw = doc(contexts, facts)
        rows = parse_revenue(raw, origin, 'AMD')
        self.assertEqual(len(rows), 5)
        self.assertEqual({row['group'] for row in rows}, {'segment'})
        roots = [row for row in rows if not row['parent']]
        self.assertEqual(sum(row['value'] for row in roots), 34639000000)
        self.assertEqual(len(roots), 3)
        self.assertEqual({row['parent'] for row in rows if row['label'] in {'클라이언트', '게이밍'}}, {'amd:ClientAndGamingMember'})
        self.assertEqual(parse_revenue(raw, origin, 'OTHER'), [])
        self.assertEqual(parse_revenue(raw.replace('OperatingSegmentsMember', 'EliminationsMember'), origin, 'AMD')[0]['parent'], None)
        self.assertEqual(parse_revenue(raw, {**origin, 'url': origin['url'].replace('www.sec.gov', 'example.com')}, 'AMD'), [])

    def test_intel_internal_segment_revenue_has_no_consolidated_percentage(self):
        origin = {**ORIGIN, 'url': 'https://www.sec.gov/Archives/edgar/data/50863/000005086326000011/intc-20251227.htm'}
        qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        raw = doc(context('total', cik='50863') + context('foundry', 'intc:IntelFoundryMember',
            axis='us-gaap:StatementBusinessSegmentsAxis', extra=qualifier, cik='50863'),
            fact('total', '52,853') + fact('foundry', '17,826'))
        row, = parse_revenue(raw, origin, 'INTC')
        self.assertTrue(row['includes_intersegment'])
        self.assertIsNone(row['total'])
        # Old caches receive the same presentation correction without a refresh.
        cached = {**row, 'includes_intersegment': False, 'total': 52853000000}
        self.assertIsNone(present_revenue([cached], 'INTC')[0]['total'])
        self.assertIsNotNone(cached['total'])

    def test_reviewed_qcom_qualifier_preserves_missing_matching_denominator(self):
        origin = {**ORIGIN, 'url': 'https://www.sec.gov/Archives/edgar/data/804328/000080432825000085/qcom-20250928.htm'}
        qualifier = '<xbrldi:explicitMember dimension="srt:ConsolidationItemsAxis">us-gaap:OperatingSegmentsMember</xbrldi:explicitMember>'
        contexts = context('total', cik='804328', start='2024-09-29', end='2025-09-28')
        for key in ['Qct', 'Qtl']:
            contexts += context(key, 'qcom:' + key + 'Member', axis='us-gaap:StatementBusinessSegmentsAxis',
                start='2024-09-30', end='2025-09-28', extra=qualifier, cik='804328')
        raw = doc(contexts, fact('total', '44,284') + fact('Qct', '38,367') + fact('Qtl', '5,582'))
        rows = parse_revenue(raw, origin, 'QCOM')
        self.assertEqual({row['label'] for row in rows}, {'QCT · 반도체 제품', 'QTL · 기술 라이선스'})
        self.assertTrue(all(row['total'] is None for row in rows))
        self.assertEqual(parse_revenue(raw, origin, 'OTHER'), [])
        for url in ['https://www.sec.gov:bad/report', 'https://[bad', 'https://www.sec.gov.evil.test/Archives/edgar/data/804328/000080432825000085/qcom.htm']:
            self.assertIsNone(source_cik({'url': url}))

    def test_including_tax_metric_and_adi_end_markets_are_not_operating_segments(self):
        origin = {**ORIGIN, 'url': 'https://www.sec.gov/Archives/edgar/data/1535527/000153552726000010/crwd-20260131.htm'}
        metric = 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
        raw = doc(context('total', cik='1535527') + context('sub', 'us-gaap:SubscriptionAndCirculationMember', cik='1535527'),
                  fact('total', '4,812,005', metric=metric, scale=3) + fact('sub', '4,564,683', metric=metric, scale=3))
        row, = parse_revenue(raw, origin, 'CRWD')
        self.assertEqual(row['value'], 4564683000)
        self.assertEqual(row['total'], 4812005000)
        adi = {**row, 'group': 'segment', 'member': 'adi:IndustrialMember', 'source': {**origin,
            'url': 'https://www.sec.gov/Archives/edgar/data/6281/000000628125000153/adi-20251101.htm'}}
        aggregate = {**adi, 'member': 'adi:ReportableSegmentMember'}
        rows = present_revenue([adi, aggregate], 'ADI')
        self.assertEqual([row['group'] for row in rows], ['end_market', 'segment'])
        self.assertEqual(rows[1]['label'], '단일 보고 부문 합계')
        self.assertEqual(CompanyKnowledge(symbol='ADI', name='Analog Devices', revenue_mix=rows).revenue_mix[0].group, 'end_market')

    def test_cached_hierarchies_require_same_report_period_currency_metric_and_unique_rows(self):
        raw = doc(context('p', 'nvda:DataCenterMember') + context('c', 'nvda:ComputeMember')
            + context('n', 'nvda:NetworkingMember'), fact('p', '150') + fact('c', '100') + fact('n', '50'))
        baseline = self.parse(raw)
        for change in [dict(unit='EUR'), dict(end='2025-01-25'), dict(metric='us-gaap:SalesRevenueNet'),
                       dict(source={**ORIGIN, 'url': ORIGIN['url'].replace('nvda-20260125', 'other-document')})]:
            with self.subTest(change=change):
                rows = [dict(row) for row in baseline]
                rows[0].update(change)
                self.assertFalse(any(row['parent'] for row in present_revenue(rows, 'NVDA')))
        self.assertFalse(any(row['parent'] for row in present_revenue(baseline + [baseline[0]], 'NVDA')))

    def test_oracle_product_subtotals_are_not_double_counted(self):
        origin = {**ORIGIN, 'url': 'https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm'}
        contexts, facts = '', ''
        for key, value in [('CloudRevenues', '33,989'), ('CloudApplications', '15,888'), ('CloudInfrastructure', '18,101'),
                           ('SoftwareRevenues', '24,541'), ('SoftwareLicense', '4,737'), ('SoftwareSupport', '19,804')]:
            contexts += context(key, 'orcl:' + key + 'Member', cik='1341439')
            facts += fact(key, value)
        rows = parse_revenue(doc(contexts, facts), origin, 'ORCL')
        self.assertEqual(len([row for row in rows if row['parent']]), 4)
        self.assertEqual(len([row for row in rows if not row['parent']]), 2)

    def test_failed_annual_report_preserves_old_revenue_only(self):
        raw = doc(context('total') + context('p', 'nvda:DataCenterMember'), fact('total', '200') + fact('p', '150'))
        old = CompanyKnowledge(symbol='NVDA', name='NVIDIA', revenue_mix=self.parse(raw))
        new = CompanyKnowledge(symbol='NVDA', name='NVIDIA', errors=['failed'], unavailable_sources=['sec_report'])
        preserve_previous(new, old)
        self.assertEqual(new.revenue_mix, old.revenue_mix)
        fresh = CompanyKnowledge(symbol='NVDA', name='NVIDIA')
        preserve_previous(fresh, old)
        self.assertFalse(fresh.revenue_mix)


if __name__ == '__main__':
    unittest.main()
