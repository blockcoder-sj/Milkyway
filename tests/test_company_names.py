import unittest
from cloud_app.company_names import SecNameIndex
from cloud_app.company_filings import parse_report, named


class SecNameTests(unittest.TestCase):
    def index(self):
        return SecNameIndex([
            dict(title='Alpha Devices, Inc.',ticker='ALP',cik_str=1),
            dict(title='Beta Manufacturing Corp',ticker='BETA',cik_str=2),
            dict(title='Manufacturing Corp',ticker='SHORT',cik_str=3),
            dict(title='Duplicate Group Inc',ticker='D1',cik_str=4),
            dict(title='Duplicate Group Inc',ticker='D2',cik_str=5),
            dict(title='Dual Class Holdings Inc',ticker='CL.A',cik_str=6),
            dict(title='Dual Class Holdings Inc',ticker='CL.B',cik_str=6),
            dict(title='Invalid',ticker='../env',cik_str=7)])

    def test_exact_full_names_ambiguity_self_and_overlap(self):
        index=self.index()
        self.assertEqual(index.named('We work with Alpha Devices, Inc. and Beta Manufacturing Corp','SELF'),[('Alpha Devices, Inc.','ALP'),('Beta Manufacturing Corp','BETA')])
        self.assertEqual(index.named('Alpha Devices manufactures devices; alphabet devices are unrelated','SELF'),[])
        self.assertEqual(index.named('Alpha Devices Inc','ALP'),[])
        self.assertEqual(index.named('Duplicate Group Inc and Dual Class Holdings Inc','SELF'),[])
        self.assertEqual(index.named('Beta Manufacturing Corp','SELF'),[('Beta Manufacturing Corp','BETA')])
        self.assertEqual(index.named('Alpha; Devices Inc','SELF'),[])

    def test_only_explicit_named_roles_with_actual_filing_provenance(self):
        src=dict(label='Issuer filing',url='https://www.sec.gov/report.htm',level='primary')
        raw=b'<p>We sell finished products to Alpha Devices Inc using memory from Beta Manufacturing Corp.</p><p>We purchase parts from Beta Manufacturing Corp and we collaborate with Alpha Devices Inc for device development.</p>'
        result=parse_report(raw,'SELF',src,self.index())
        self.assertEqual({(r['symbol'],r['kind']) for r in result['relations']},{('ALP','customer'),('BETA','supplier'),('ALP','partner')})
        self.assertTrue(all(r['source']==src for r in result['relations']))
        self.assertTrue(result['sources'][0]['url'].endswith('company_tickers.json'))

    def test_competition_context_does_not_override_supply_or_example_mentions(self):
        src=dict(label='Issuer filing',url='https://www.sec.gov/report.htm',level='primary')
        raw=b'<h2>Competition</h2><p>We purchase memory from Micron Technology for our products and our manufacturing operations.</p><p>Apple Inc uses our wider technology ecosystem as one general example of the market.</p><p>Our competitors include Intel Corporation in several markets for high performance processors.</p>'
        rows=parse_report(raw,'NVDA',src)['relations']
        self.assertEqual({(r['symbol'],r['kind']) for r in rows},{('MU','supplier'),('INTC','competitor')})

    def test_brand_substring_cannot_override_exact_other_issuer(self):
        index=SecNameIndex([dict(title='Apple Hospitality REIT Inc',ticker='APLE',cik_str=10)])
        self.assertEqual(named('Our partners include Apple Hospitality REIT Inc','SELF',index),[('Apple Hospitality REIT Inc','APLE')])
        self.assertEqual(named('Our partners include Apple Hospitality REIT Inc','APLE',index),[])
        self.assertIn(('Apple','AAPL'),named('Our partners include Apple Inc','SELF',index))

    def test_out_of_schema_legal_names_are_excluded_and_boilerplate_is_not_product(self):
        long_name='Long Legal Company '+('Holding '*20)+'Inc'
        index=SecNameIndex([dict(title=long_name,ticker='LONG',cik_str=22)])
        self.assertEqual(index.named(long_name,'SELF'),[])
        src=dict(label='Issuer',url='https://www.sec.gov/report.htm',level='primary')
        raw=b'<p>We offer competitive, performance-based compensation packages for our employees and management.</p><p>We offer semiconductor processors and software for our enterprise and industrial customer systems.</p>'
        rows=parse_report(raw,'SELF',src)['products']
        self.assertEqual(len(rows),1);self.assertNotIn('compensation',rows[0]['original'])
