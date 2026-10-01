"""Product brands are not counterparties; old bad claims cannot remain in SQLite."""
import datetime as dt
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cloud_app.company_entities import bootstrap
from cloud_app.company_filings import parse_report, counterparties
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_names import SecNameIndex
from cloud_app.company_schemas import CompanyKnowledge

SRC = dict(label='Synthetic SEC filing', url='https://www.sec.gov/report.htm', level='primary')
BAD = ('We provide Together AI with access to dedicated NVIDIA H100 GPU infrastructure '
       'across multiple clusters for hosted services.')


class CompanyRelationValidationTests(unittest.TestCase):
    def relation(self):
        return dict(name='NVIDIA', symbol='NVDA', kind='customer',
                    detail='공시 판매·고객 관계', original=BAD, source=SRC)

    def test_providing_access_to_brand_products_is_not_a_customer_claim(self):
        self.assertEqual(parse_report(('<p>'+BAD+'</p>').encode(), 'CHRN', SRC)['relations'], [])
        for text in ["We provide hosted services to NVIDIA's customers.",
                     'Our customers include NVIDIA H100 GPU users and Apple Inc.',
                     'We collaborate with suppliers of NVIDIA for advanced infrastructure.']:
            rows = parse_report(('<p>'+text+' Additional business operations are described here.</p>').encode(), 'SELF', SRC)['relations']
            self.assertFalse(any(row['symbol']=='NVDA' for row in rows))
        real = parse_report(b'<p>We provide finished semiconductor services to NVIDIA Corporation for its data center systems.</p>', 'SELF', SRC)
        self.assertEqual([(row['symbol'],row['kind']) for row in real['relations']], [('NVDA','customer')])

    def test_resource_filter_keeps_exact_legal_names_and_separate_unknown_aliases(self):
        index = SecNameIndex([dict(title='Bank of America Corp',ticker='BAC',cik_str=1)])
        self.assertEqual(counterparties('Bank of America Corp and NVIDIA Corporation','SELF',index),
                         [('NVIDIA','NVDA'),('Bank of America','BAC')])
        self.assertEqual(counterparties('Renesas Electronics products and Hon Hai Precision Industry','SELF'),
                         [('Hon Hai Precision Industry',None)])

    def test_real_customer_and_competitor_lists_keep_roles_without_card_brand_confusion(self):
        raw=b'<h2>Competition</h2><p>Examples include American Express, Mastercard and other named payment networks in our industry.</p><p>Some of the largest retailers we sell to include Amazon, Costco and Walmart, through our channels.</p>'
        result=parse_report(raw,'SELF',SRC)
        self.assertTrue(any(row['symbol']=='MA' and row['kind']=='competitor' for row in result['relations']))
        self.assertTrue(any(row['symbol']=='AMZN' and row['kind']=='customer' for row in result['relations']))
        self.assertEqual(counterparties('Mastercard \u00ae credit cards and American Express','SELF'),[('American Express','AXP')])
        self.assertEqual(counterparties("Amazon.com's marketplace",'SELF',role='competitor'),[('Amazon','AMZN')])
        self.assertEqual(counterparties("NVIDIA's customers",'SELF',role='competitor'),[])

    def test_legacy_recheck_preserves_reviewed_valid_and_v3_full_legal_statements(self):
        good = dict(name='Beta Manufacturing Corp',symbol='BETA',kind='supplier',
                    detail='공시 제조·부품 공급',original='We purchase parts from Beta Manufacturing Corp for device systems.',source=SRC)
        reviewed = {**self.relation(), 'detail':'직접 검토한 별도의 관계 진술'}
        for version in [0,2,3]:
            value = CompanyKnowledge(symbol='CHRN', name='Issuer', collector_version=version,
                relations=[self.relation(),good,reviewed],report_analysis=dict(title='공시 확인',detail='기존 추출 수',source=SRC))
            self.assertEqual(len(value.relations),2)
            self.assertIn('1건',value.report_analysis.detail)
            self.assertEqual(value.model_dump(),CompanyKnowledge.model_validate(value).model_dump())

    def test_reviewed_cloud_value_chain_has_correct_customer_and_supplier(self):
        from cloud_app.company_catalog import enrich
        value=enrich(CompanyKnowledge(symbol='CHRN',name='ChronoScale'))
        self.assertEqual({(row.symbol,row.registry_id,row.kind) for row in value.relations},
                         {('NVDA',None,'supplier'),(None,'together-ai','customer'),
                          ('MSFT',None,'customer'),('NTNX',None,'partner'),
                          ('CRWV',None,'competitor'),('NBIS',None,'competitor'),
                          (None,'crusoe','competitor'),(None,'lambda-labs','competitor')})
        self.assertTrue(all(row.source.url.endswith('chrn-20260531.htm') for row in value.relations))
        self.assertTrue(any('99.5%' in row.detail for row in value.brief))

    def test_bootstrap_removes_only_unsupported_owner_claim_and_repairs_unchanged_cache(self):
        with TemporaryDirectory() as directory:
            settings=SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(directory)/'runtime/data')
            graph=CompanyGraph(settings)
            raw=CompanyKnowledge(symbol='ROOTX',name='Issuer',collector_version=4,
                attempted_at=dt.datetime(2026,10,1,tzinfo=dt.timezone.utc),relations=[self.relation(),
                    {**self.relation(),'detail':'별도로 검토된 고객 관계'}]).model_dump(mode='json')
            owner=graph.ingest(raw)
            graph.ingest(CompanyKnowledge(symbol='NVDA',name='NVIDIA',relations=[dict(
                name='Issuer',symbol='ROOTX',kind='supplier',detail='다른 발행사의 검토 진술',source=SRC)]))
            raw['collector_version']=2
            path=settings.dataset_dir.parent/'company-details'/'ROOTX.json'
            path.write_text(json.dumps(raw))
            with graph.connection() as db:
                db.execute('UPDATE company_profiles SET payload=?,digest=? WHERE entity_id=?',(json.dumps(raw),'legacy',owner))
            with patch('cloud_app.company_service.related_directory',return_value={}):
                self.assertEqual(bootstrap(settings)['rejected'],0)
                self.assertEqual(bootstrap(settings)['imported'],0)
            details={item['detail'] for row in graph.relations(owner) for item in row['evidence']}
            self.assertEqual(details,{'별도로 검토된 고객 관계','다른 발행사의 검토 진술'})
            cache=json.loads(path.read_text())
            self.assertEqual(len(cache['relations']),1)
            self.assertEqual(graph.entity(owner)['profile']['collector_version'],2)
            with graph.connection() as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())
