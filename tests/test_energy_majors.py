"""Major-issuer scope, exact IFRS coordinates and dated named roles, offline."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from cloud_app.company_catalog import enrich
from cloud_app.company_energy_majors import ANNUAL, PUBLIC, PRIVATE, EDGES
from cloud_app.company_energy_major_revenue import COORDINATES
from cloud_app.company_energy_sources import REPORTS
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_research_catalog import private_profile, enrichment
from cloud_app.company_revenue import parse_revenue, present_revenue
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.energy_issuers import issuer
from tests.test_company_revenue import context, doc, fact


class EnergyMajorTests(unittest.TestCase):
    def test_primary_edited_profiles_and_named_counterparts_validate_and_merge_idempotently(self):
        self.assertEqual(set(PUBLIC), {'XOM','SHEL','BP','TTE','E','EQNR','PBR','EC','YPF'})
        for symbol, notes in PUBLIC.items():
            with self.subTest(symbol=symbol):
                value = CompanyKnowledge(symbol=symbol, **notes)
                self.assertTrue(value.products and value.drivers and value.revenue_mix)
                self.assertEqual(len(value.brief), 6)
                current = enrich(value)
                self.assertTrue(current.financials)
                self.assertEqual(enrich(current).model_dump(), current.model_dump())
                self.assertNotEqual(issuer(symbol).group, 'pending')
                self.assertGreaterEqual(len(enrichment(symbol)['relations']), len(EDGES[symbol]))
                self.assertTrue(all(r.source.level == 'primary' and not r.original
                                    for r in value.brief + value.products + value.drivers))
        for key in PRIVATE:
            self.assertTrue(CompanyKnowledge(**private_profile(key)).brief)
        for edges in EDGES.values():
            for edge in edges:
                if edge['registry_id']:
                    self.assertTrue(private_profile(edge['registry_id'])['brief'])

    def test_external_segment_and_country_totals_reconcile_on_their_own_basis(self):
        for symbol, group, total in [
            ('SHEL','segment',266886000000),('SHEL','geography',266886000000),
            ('BP','segment',189335000000),('BP','geography',189335000000),
            ('BP','product',158879000000),('TTE','segment',201196000000),
            ('TTE','geography',201196000000),('E','segment',82151000000),
            ('E','geography',82151000000),('EQNR','product',105242000000),
            ('PBR','product',89195000000),('PBR','geography',89195000000),
            ('EC','segment',119694000000000),('EC','geography',119694000000000),
            ('YPF','geography',18448000000),('XOM','revenue_type',332238000000),
        ]:
            with self.subTest(symbol=symbol,group=group):
                rows = present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
                tops = [r for r in rows if r['group']==group and not r['parent']]
                self.assertEqual(sum(r['value'] for r in tops),total)
                self.assertTrue(all(r['total']==total for r in tops))

    def test_edited_brief_replaces_legacy_cards_before_validation_and_keeps_their_sources(self):
        old_source=dict(label='과거 공시',url='https://www.sec.gov/Archives/edgar/data/34088/000003408825000001/old.htm',
                        as_of='2025-02-01',level='primary')
        old=[dict(title=f'과거 요약 {index}',detail='이전 자료',source=old_source) for index in range(8)]
        result=enrich(CompanyKnowledge(symbol='XOM',name='ExxonMobil',brief=old))
        self.assertEqual(len(result.brief),6)
        self.assertFalse(any(r.title.startswith('과거 요약') for r in result.brief))
        self.assertTrue(any(s.url==old_source['url'] for s in result.sources))
        self.assertEqual(enrich(result).model_dump(),result.model_dump())

    def test_internal_sales_are_not_percentages_of_external_revenue(self):
        for symbol,gross,elimination,external in [
            ('EQNR',148883000000,42421000000,106462000000),
            ('PBR',152735000000,63540000000,89195000000),
            ('YPF',27567000000,9119000000,18448000000),
        ]:
            rows = [r for r in present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
                    if r['group']=='segment']
            self.assertEqual(sum(r['value'] for r in rows),gross)
            self.assertEqual(gross-elimination,external)
            self.assertTrue(all(r['total'] is None and r['includes_intersegment']
                                and r['share_exclusion'] for r in rows))

    def test_exxon_sales_and_equity_income_have_separate_scope(self):
        rows = present_revenue(REPORTS['XOM']['revenue_mix'],'XOM')
        segments = [r for r in rows if r['group']=='segment']
        self.assertEqual(len(segments),8)
        self.assertEqual(sum(r['value'] for r in segments),323820000000)
        self.assertEqual(323820000000+85000000,323905000000)
        self.assertEqual(323905000000+5064000000+3269000000,332238000000)
        self.assertTrue(all(r['total'] is None and '85,000,000' in r['share_exclusion'] for r in segments))

    def test_parent_regions_and_petroleum_subtotals_do_not_add_to_100_percent_twice(self):
        for symbol,child,parent in [('SHEL','country:GB','srt:EuropeMember'),
                                   ('BP','ifrs-full:CountryOfDomicileMember','bp:NonUSMember'),
                                   ('PBR','pbr:CountryUnitedStatesMember','pbr:ForeignMarketMember')]:
            rows = present_revenue(REPORTS[symbol]['revenue_mix'],symbol)
            self.assertEqual(next(r['parent'] for r in rows if r['member']==child),parent)
        rows = present_revenue(REPORTS['PBR']['revenue_mix'],'PBR')
        children = [r for r in rows if r['parent']=='pbr:SubtotalOilProductsMember']
        self.assertEqual(len(children),7)
        self.assertEqual(sum(r['value'] for r in children),52813000000)
        exports = [r for r in rows if r['parent']=='pbr:ExportsMember/pbr:ForeignMarketMember']
        self.assertEqual(sum(r['value'] for r in exports),25572000000)
        names = {r['member']:r['label'] for r in rows}
        self.assertIn('미국 외',names['pbr:CountryAmericasMember'])
        self.assertIn('중국·싱가포르 외',names['pbr:CountryAsiaMember'])

    def test_reviewed_dimensions_are_exact_issuer_bound_and_reject_extra_qualifiers(self):
        for (symbol,cik,pairs),(group,member) in COORDINATES.items():
            with self.subTest(symbol=symbol,member=member):
                pairs=sorted(pairs);axis,first=pairs[0]
                extra=''.join(f'<xbrldi:explicitMember dimension="{a}">{m}</xbrldi:explicitMember>'
                              for a,m in pairs[1:])
                dates=dict(cik=str(cik),start='2025-01-01',end='2025-12-31')
                metric=('us-gaap:Revenues' if symbol=='XOM' else
                        'ifrs-full:RevenueAndOperatingIncome' if symbol=='BP' and group!='product' else
                        'ifrs-full:RevenueFromContractsWithCustomers' if symbol in {'E','TTE'} or
                        (symbol in {'BP','EQNR'} and group=='product') else 'ifrs-full:Revenue')
                raw=doc(context('total',**dates)+context('part',first,axis=axis,extra=extra,**dates),
                        fact('total','100',metric=metric)+fact('part','70',metric=metric))
                result=parse_revenue(raw,ANNUAL[symbol],symbol)
                self.assertEqual(len(result),1)
                self.assertEqual((result[0]['group'],result[0]['member']),(group,member))
                self.assertEqual(parse_revenue(raw.replace(str(cik),str(cik+1)),ANNUAL[symbol],symbol),[])
                unreviewed='<xbrldi:explicitMember dimension="x:OtherAxis">x:OtherMember</xbrldi:explicitMember>'
                self.assertEqual(parse_revenue(raw.replace('</xbrli:segment>',unreviewed+'</xbrli:segment>'),
                                               ANNUAL[symbol],symbol),[])

    def test_bp_segment_basis_cannot_borrow_its_consolidated_total_income_denominator(self):
        member='bp:CustomersProductsMember'
        qualifier='<xbrldi:explicitMember dimension="ifrs-full:SegmentConsolidationItemsAxis">ifrs-full:OperatingSegmentsMember</xbrldi:explicitMember>'
        dates=dict(cik='313807',start='2025-01-01',end='2025-12-31')
        contexts=context('total',**dates)+context('part',member,axis='ifrs-full:SegmentsAxis',extra=qualifier,**dates)
        raw=doc(contexts,fact('total','192,549',metric='ifrs-full:Revenue')+
                fact('part','148,740',metric='ifrs-full:RevenueAndOperatingIncome'))
        row,=parse_revenue(raw,ANNUAL['BP'],'BP')
        self.assertIsNone(row['total'])
        full=raw.replace('</html>',fact('total','189,335',metric='ifrs-full:RevenueAndOperatingIncome')+'</html>')
        self.assertEqual(parse_revenue(full,ANNUAL['BP'],'BP')[0]['total'],189335000000)

    def test_different_documents_and_years_do_not_inherit_2025_eliminations(self):
        for symbol in ('EQNR','PBR','YPF','XOM'):
            for change in ('document','year'):
                rows=deepcopy(REPORTS[symbol]['revenue_mix'])
                for row in rows:
                    row['includes_intersegment']=False;row['share_exclusion']=None
                    if change=='document':row['source']['url']=row['source']['url'].replace('.htm','-other.htm')
                    else:row['start']='2024-01-01';row['end']='2024-12-31'
                result=present_revenue(rows,symbol)
                self.assertTrue(all(not r['includes_intersegment'] and not r['share_exclusion'] for r in result))

    def test_current_governance_and_future_capacity_keep_dates_and_conditions(self):
        plenitude=PRIVATE['plenitude']
        self.assertIn('65.03%',plenitude['brief'][1]['detail'])
        self.assertIn('공동 지배',plenitude['brief'][1]['detail'])
        self.assertIn('연결 제외',plenitude['brief'][1]['detail'])
        self.assertFalse(any(r['registry_id']=='plenitude' and r['kind']=='subsidiary' for r in EDGES['E']))
        self.assertIn('인수 완료',str(PUBLIC['SHEL']['brief']))
        self.assertFalse(any(r['symbol']=='AR' for r in EDGES['SHEL']))
        self.assertIn('현재 생산량이 아닙니다',str(PUBLIC['SHEL']['brief']))
        self.assertIn('현재 가동 LNG',str(EDGES['YPF']))
        self.assertIn('ADR 자체를',str(PUBLIC['YPF']['brief']))
        self.assertFalse(any(r['kind']=='customer' for r in PRIVATE['lng-canada']['relations']))

    def test_supplier_and_partner_links_have_clickable_counterparts_and_reverse_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph=CompanyGraph(SimpleNamespace(dataset_dir=Path(tmp)/'runtime/data',personal_local_mode=True,production=False))
            for symbol in ('SHEL','EQNR','XOM'):
                graph.ingest(enrich(CompanyKnowledge(symbol=symbol,name=symbol)),'us_10')
            targets={key:graph.ingest(CompanyKnowledge(**private_profile(key))) for key in
                     ('lng-canada','adura','modec','ng3','golden-pass-lng')}
            shell=graph.by_symbol('SHEL')['id']
            edges=graph.relations(shell)
            self.assertTrue(any(r['target_id']==targets['lng-canada'] for r in edges))
            self.assertTrue(any(r['target_id']==shell for r in graph.relations(targets['lng-canada'])))
            self.assertTrue(graph.entity(targets['lng-canada'])['profile']['brief'])
