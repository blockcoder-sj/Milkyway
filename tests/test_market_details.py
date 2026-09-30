"""Market detail contracts, using synthetic public responses only."""
import datetime as dt
import email.utils
import tempfile
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cloud_app import market_detail_feed as feed,market_details as service
from cloud_app.market_catalog import CATALOG,BY_ID
from cloud_app.market_detail_catalog import context_for, RELATED_ETFS
from cloud_app.market_service import _write_cache

NOW=dt.datetime(2026,9,30,6,tzinfo=dt.timezone.utc)


def history_payload(identity='sp500'):
    instrument=BY_ID[identity]
    return {'chart':{'result':[{'meta':{'symbol':instrument.symbol,'instrumentType':'CURRENCY' if instrument.group=='fx' else 'INDEX','exchangeTimezoneName':'UTC'},
      'timestamp':[(NOW-dt.timedelta(days=1200)).timestamp(),(NOW-dt.timedelta(days=1)).timestamp(),NOW.timestamp(),(NOW+dt.timedelta(days=1)).timestamp()],
      'indicators':{'quote':[{'open':[10]*4,'high':[12]*4,'low':[9]*4,'close':[11]*4,'volume':[100]*4}]}}]}}


class MarketDetailTests(unittest.TestCase):
    def test_all_37_items_have_editorial_context_and_sources(self):
        for item in CATALOG:
            context=context_for(item.id)
            self.assertTrue(context['intro']);self.assertTrue(context['sources']);self.assertTrue(context['watchpoints'])
            self.assertTrue(all(source['url'].startswith('https://') for source in context['sources']))

    def test_history_restricts_three_years_and_future_bars(self):
        result=feed.parse_history(history_payload(),BY_ID['sp500'],NOW)
        self.assertEqual(len(result['rows']),2)
        self.assertEqual(result['rows'][0]['date'],'2026-09-29')
        value=history_payload();value['chart']['result'][0]['meta']['symbol']='OTHER'
        with self.assertRaises(ValueError): feed.parse_history(value,BY_ID['sp500'],NOW)

    def test_history_multiplier_applies_to_all_ohlc(self):
        result=feed.parse_history(history_payload('jpykrw'),BY_ID['jpykrw'],NOW)
        self.assertEqual(result['rows'][0]['open'],1000)
        self.assertEqual(result['rows'][0]['high'],1200)
        self.assertEqual(result['rows'][0]['close'],1100)

    def test_history_rejects_invalid_prices_and_oversized_arrays(self):
        value=history_payload();value['chart']['result'][0]['indicators']['quote'][0]['close']=[float('nan')]*4
        with self.assertRaises(ValueError):feed.parse_history(value,BY_ID['sp500'],NOW)
        value=history_payload();value['chart']['result'][0]['timestamp']=[NOW.timestamp()]*1201
        with self.assertRaises(ValueError):feed.parse_history(value,BY_ID['sp500'],NOW)

    def test_history_keeps_valid_close_when_ohlc_or_volume_is_invalid(self):
        payload=history_payload();columns=payload['chart']['result'][0]['indicators']['quote'][0]
        columns['high'][1]=5;columns['volume'][1]='bad';columns['close'][2]=None
        result=feed.parse_history(payload,BY_ID['sp500'],NOW)
        self.assertEqual(result['rows'][0]['close'],11)
        self.assertIsNone(result['rows'][0]['high']);self.assertIsNone(result['rows'][0]['open'])
        self.assertIsNone(result['rows'][0]['volume'])
        self.assertEqual(result['quality'],dict(received=4,outside_range=2,invalid_close=1,close_only=1,duplicates=0,accepted=1))
        typed=service.DetailCache.model_validate({'history':result})
        self.assertEqual(typed.history.quality.close_only,1)
        self.assertIsNone(typed.history.rows[0].high)

    def test_history_reports_duplicate_dates(self):
        payload=history_payload();row=payload['chart']['result'][0]
        row['timestamp'][2]=row['timestamp'][1]
        result=feed.parse_history(payload,BY_ID['sp500'],NOW)
        self.assertEqual(len(result['rows']),1);self.assertEqual(result['quality']['duplicates'],1)

    def test_companies_share_is_limited_to_same_currency_and_sample(self):
        payload={'finance':{'result':[{'quotes':[{'symbol':'AAA','shortName':'Alpha','marketCap':100,'currency':'USD'},
            {'symbol':'BBB','shortName':'Beta','marketCap':300,'currency':'USD'},
            {'symbol':'CCC','marketCap':9000,'currency':'KRW'}]}]}}
        result=feed.parse_us_companies(payload,NOW)
        self.assertEqual([row['displayed_share_pct'] for row in result['rows']],[25,75])

    def test_company_screen_keeps_more_than_eight_and_bounds_input(self):
        quotes=[{'symbol':f'C{i}','shortName':f'Company {i}','marketCap':100,'currency':'USD'} for i in range(100)]
        result=feed.parse_us_companies({'finance':{'result':[{'quotes':quotes}]}},NOW)
        self.assertEqual(len(result['rows']),100)
        self.assertAlmostEqual(sum(row['displayed_share_pct'] for row in result['rows']),100)
        with self.assertRaises(ValueError):feed.parse_us_companies({'finance':{'result':[{'quotes':quotes*11}]}},NOW)

    def test_monthly_news_retains_older_articles_sorts_and_deduplicates(self):
        rows=[{'url':f'https://news.google.com/rss/articles/{day}','title':'Headline','publisher':'BBC','published_at':(NOW-dt.timedelta(days=day)).isoformat()} for day in [20,1,31,8,29]]
        result=feed.merge_news(rows+[rows[0]],NOW)
        self.assertEqual([row['url'].rsplit('/',1)[1] for row in result],['1','8','20','29'])
        self.assertTrue({'nytimes.com','bbc.com','cnn.com','aljazeera.com'}.issubset(feed.ENGLISH_NEWS_HOSTS))
        xml=b'<rss><channel><item><title>BBC report</title><source url="https://www.bbc.com">BBC</source><link>https://news.google.com/rss/articles/month</link><pubDate>'+email.utils.format_datetime(NOW-dt.timedelta(days=25)).encode()+b'</pubDate></item></channel></rss>'
        self.assertEqual(len(feed.parse_news_rss(xml,NOW,feed.ENGLISH_NEWS_HOSTS)),1)

    def test_news_query_bounds_publisher_groups_in_each_time_window(self):
        from unittest.mock import MagicMock
        calls=[]
        response=MagicMock()
        session=MagicMock();session.__enter__.return_value=session
        def capture(url,**kwargs):
            calls.append(kwargs['params']['q']);return response
        session.get.side_effect=capture
        with patch.object(feed,'FixedSession',return_value=session),patch.object(feed,'read_requests_bytes',return_value=b'<rss><channel/></rss>'):
            result=feed.news(BY_ID['us_45'])
        self.assertEqual(len(calls),4*((len(feed.ENGLISH_NEWS_HOSTS)+5)//6))
        self.assertTrue(all(q.count('site:')<=6 and 'after:' in q and 'before:' in q and 'Nvidia' in q for q in calls))
        self.assertEqual(result['selection_version'],3)

    def test_title_scope_rejects_unrelated_indexed_body_matches(self):
        query=context_for('us_45')['news_query']
        self.assertTrue(feed.news_title_matches('Nvidia and Micron chip production',query,'us_45'))
        self.assertTrue(feed.news_title_matches('HPE raises AI guidance',query,'us_45'))
        self.assertFalse(feed.news_title_matches('Pilot stabs pilot on flight',query,'us_45'))
        self.assertFalse(feed.news_title_matches('Moderna downgraded by Citi',query,'us_45'))
        self.assertFalse(feed.news_title_matches('Mexico peso carry traders flee',query,'us_45'))
        self.assertTrue(feed.news_title_matches('원/달러 환율 변화',context_for('usdkrw')['news_query'],'usdkrw'))

    def test_changed_news_selection_does_not_retain_obsolete_query_results(self):
        with tempfile.TemporaryDirectory() as temp:
            settings=SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(temp)/'data')
            old=dict(title='Old selection',publisher='BBC',url='https://news.google.com/rss/articles/old',published_at=dt.datetime.now(dt.timezone.utc).isoformat())
            _write_cache(service.cache_path(settings,'us_45'),{'news':{'rows':[old],'selection_version':1}})
            with patch.object(service._provider,'run',return_value={'news':{'rows':[],'selection_version':2,'fetched_at':NOW.isoformat()}}):service.refresh_detail(settings,'us_45')
            result=service.read_cache(settings,'us_45')
            self.assertEqual(result.news.rows,[]);self.assertEqual(result.news.selection_version,2)

    def test_korean_market_cap_units_and_partial_snapshot(self):
        self.assertEqual(feed.parse_kr_cap('1,572조 6,489억'),1572648900000000)
        self.assertEqual(feed.parse_kr_cap('983억'),98300000000)
        with self.assertRaises(ValueError):feed.parse_kr_cap('983')
        result=feed.company_snapshot([{'symbol':'AAA','market_cap':100},{'symbol':'BBB','market_cap':None}],NOW)
        self.assertTrue(result['error']);self.assertTrue(all(row['displayed_share_pct'] is None for row in result['rows']))

    def test_news_urls_reject_credentials_scripts_and_bad_ports(self):
        self.assertFalse(feed.safe_news_url('https://finance.yahoo.com:bad/path'))
        self.assertFalse(feed.safe_news_url('javascript:alert(1)'))
        self.assertFalse(feed.safe_news_url('https://key@finance.yahoo.com/path'))

    def test_rss_rejects_entities_and_only_accepts_listed_publishers(self):
        with self.assertRaises(ValueError):feed.parse_news_rss(b'<!DOCTYPE x [<!ENTITY x "secret">]><rss/>',NOW)
        xml=b'<rss><channel><item><title>Headline</title><source url="https://www.yna.co.kr">Yonhap</source><link>https://news.google.com/rss/articles/test</link><pubDate>Wed, 30 Sep 2026 05:00:00 GMT</pubDate></item></channel></rss>'
        self.assertEqual(len(feed.parse_news_rss(xml,NOW)),1)
        self.assertEqual(feed.parse_news_rss(xml.replace(b'www.yna.co.kr',b'evil.test'),NOW),[])

    def test_cache_read_never_fetches_and_timeout_retains_original_timestamp(self):
        with tempfile.TemporaryDirectory() as temp:
            settings=SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(temp)/'data')
            original=feed.parse_history(history_payload(),BY_ID['sp500'],NOW)
            _write_cache(service.cache_path(settings,'sp500'),{'history':original})
            with patch.object(service._provider,'run',side_effect=TimeoutError):service.refresh_detail(settings,'sp500')
            with patch.object(service._provider,'run') as fetch:
                result=service.detail_snapshot(settings,'sp500',NOW)
                fetch.assert_not_called()
            self.assertEqual(result['history']['fetched_at'],original['fetched_at'].replace('+00:00','Z'))
            self.assertEqual(len(result['history']['rows']),2)
            self.assertTrue(result['history']['stale'])

    def test_path_traversal_and_cloud_mode_are_rejected(self):
        settings=SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path('/unused'))
        with self.assertRaises(ValueError):service.cache_path(settings,'../../.env')
        settings.production=True
        with self.assertRaises(ValueError):service.cache_path(settings,'sp500')

    def test_corrupt_typed_cache_and_oversized_files_are_unavailable(self):
        with tempfile.TemporaryDirectory() as temp:
            settings=SimpleNamespace(personal_local_mode=True,production=False,dataset_dir=Path(temp)/'data')
            path=service.cache_path(settings,'sp500');path.parent.mkdir()
            for content in ('[]','x'*524289,json.dumps({'history':{'rows':[{'date':'not-date','close':True}]}})):
                path.write_text(content)
                self.assertEqual(service.detail_snapshot(settings,'sp500',NOW)['history']['rows'],[])

    def test_related_etf_history_stays_a_separate_typed_series(self):
        self.assertEqual(len(RELATED_ETFS),20)
        value=history_payload();row=value['chart']['result'][0]
        row['meta'].update(symbol='XLK',instrumentType='ETF')
        with patch.object(feed,'history',side_effect=lambda instrument:feed.parse_history(value,instrument,NOW)):
            result=feed.related_history(BY_ID['us_45'])
        self.assertEqual(len(result['rows']),2)
        self.assertEqual(context_for('us_45')['related_chart']['symbol'],'XLK')
        self.assertIn('다르',context_for('us_45')['related_chart']['note'])
        with self.assertRaises(ValueError):feed.parse_history(value,BY_ID['us_45'],NOW)

    def test_english_rss_publisher_filter_and_localized_fx_query(self):
        xml=b'<rss><channel><item><title>Headline</title><source url="https://www.reuters.com">Reuters</source><link>https://news.google.com/rss/articles/test</link><pubDate>Wed, 30 Sep 2026 05:00:00 GMT</pubDate></item></channel></rss>'
        self.assertEqual(len(feed.parse_news_rss(xml,NOW,feed.ENGLISH_NEWS_HOSTS)),1)
        self.assertEqual(context_for('usdkrw')['news_locale'],'ko')

    def test_share_fact_is_dated_and_narrowly_scoped(self):
        fact=context_for('us_45')['market_share'][0]
        self.assertEqual(fact['period'],'2026년 2분기')
        self.assertIn('전체',fact['scope']);self.assertEqual(fact['values'][0]['value'],72.5)
        self.assertEqual(context_for('us_10')['market_share'],[])
