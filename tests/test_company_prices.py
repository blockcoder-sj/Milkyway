"""Company display quotes: synthetic prices, no provider credentials or calls."""
import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from cloud_app import company_prices as prices, company_price_feed as public
from cloud_app import company_price_stream as stream, market_broker as broker
from cloud_app.company_graph import CompanyGraph
from cloud_app.company_schemas import CompanyKnowledge
from cloud_app.market_broker_feed import TossDisplay
from cloud_app.market_service import _write_cache

NOW = dt.datetime(2026, 10, 2, 14, 0, tzinfo=dt.timezone.utc)


def price(symbol='AAPL', **extra):
    return prices.Price(symbol=symbol, currency=prices.currency_for(symbol), value=1234.5,
        fetched_at=NOW, observed_at=NOW, method='reference', **extra).model_dump(mode='json')


class CompanyPriceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SimpleNamespace(personal_local_mode=True, production=False,
            credential_backend='local', dataset_dir=Path(self.temp.name)/'runtime/data')
        self.graph = CompanyGraph(self.settings)
        self.key = self.graph.ingest(CompanyKnowledge(symbol='AAPL', name='Apple'))

    def tearDown(self):
        self.temp.cleanup()

    def cache(self, row, error=None):
        _write_cache(prices.cache_path(self.settings), {'version':1,
            'items':{'AAPL':{'price':row,'error':error}}})

    def test_only_registered_stock_aliases_can_be_watched(self):
        self.assertEqual(prices.resolve_symbol(self.settings,self.key),'AAPL')
        for bad in ('MSFT','../secret','https://evil.test','005930.KS'):
            with self.subTest(symbol=bad), self.assertRaises(HTTPException):
                prices.watch(self.settings,self.key,'owner',bad,NOW)
        with self.assertRaises(HTTPException):
            prices.resolve_symbol(self.settings,'../secret')
        self.assertEqual(prices.active(self.settings,now=NOW),[])

    def test_unlisted_company_has_no_fabricated_stock_price(self):
        key=self.graph.ingest(CompanyKnowledge(name='Carl Zeiss SMT',registry_id='carl-zeiss-smt'))
        self.assertEqual(prices.snapshot(self.settings,key,now=NOW)['status'],'unlisted')
        self.assertEqual(prices.watch(self.settings,key,'owner',now=NOW)['status'],'unlisted')
        self.assertEqual(prices.active(self.settings,now=NOW),[])

    def test_watches_expire_and_are_owner_scoped(self):
        prices.watch(self.settings,self.key,'first',now=NOW)
        self.assertEqual(prices.active(self.settings,'first',NOW),['AAPL'])
        self.assertEqual(prices.active(self.settings,'second',NOW),[])
        self.assertEqual(prices.active(self.settings,now=NOW+dt.timedelta(seconds=91)),[])

    def test_concurrent_admission_cannot_exceed_global_limit(self):
        keys=[self.graph.ingest(CompanyKnowledge(symbol='T'+str(i),name='Synthetic '+str(i))) for i in range(18)]
        def add(key):
            try:
                prices.watch(self.settings,key,'owner',now=NOW)
                return True
            except HTTPException as exc:
                self.assertEqual(exc.status_code,429)
                return False
        with ThreadPoolExecutor(max_workers=6) as pool:
            self.assertEqual(sum(pool.map(add,keys)),prices.WATCH_LIMIT)
        self.assertEqual(len(prices.active(self.settings,now=NOW)),prices.WATCH_LIMIT)
        prices.watch(self.settings,keys[0],'owner',now=NOW+dt.timedelta(seconds=91))
        self.assertEqual(prices.active(self.settings,now=NOW+dt.timedelta(seconds=91)),['T0'])

    def test_prices_reject_booleans_nonfinite_wrong_identity_and_time(self):
        for field,value in [('value',True),('value',float('nan')),('value',0),('value',1e13),
                            ('previous_close',True),('fetched_at',NOW.replace(tzinfo=None)),
                            ('observed_at',NOW+dt.timedelta(minutes=1)),('currency','KRW'),('symbol','MSFT')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                prices.valid_price({**price(),field:value},'AAPL',NOW)

    def test_cached_broker_price_requires_current_connection_identity(self):
        self.cache(price(previous_close=1200))
        row={**price(),'value':1250,'method':'websocket'}
        _write_cache(broker.cache_path(self.settings),{'identity':'current','provider':'toss','items':{},'companies':{'AAPL':row}})
        for identity in (None,'another-owner','old-credential-revision'):
            self.assertEqual(prices.snapshot(self.settings,self.key,connection_identity=identity,now=NOW)['source'],'Yahoo Finance')
        result=prices.snapshot(self.settings,self.key,connection_identity='current',now=NOW)
        self.assertTrue(result['is_realtime'])
        self.assertEqual(result['source'],'토스증권')
        self.assertEqual(result['change'],50)
        self.assertEqual(result['comparison_source'],'Yahoo Finance · 전일 종가')

    def test_previous_day_reference_cannot_supply_premarket_baseline(self):
        self.cache({**price(previous_close=1200),'observed_at':(NOW-dt.timedelta(days=1)).isoformat()})
        _write_cache(broker.cache_path(self.settings),{'identity':'current','provider':'toss','items':{},
            'companies':{'AAPL':{**price(),'method':'poll'}}})
        result=prices.snapshot(self.settings,self.key,connection_identity='current',now=NOW)
        self.assertIsNone(result['change'])
        self.assertEqual(result['status'],'polled')

    def test_aged_trade_is_not_reported_as_realtime_and_aged_cache_falls_back(self):
        self.cache(price())
        _write_cache(broker.cache_path(self.settings),{'identity':'current','provider':'toss','items':{},
            'companies':{'AAPL':{**price(),'observed_at':(NOW-dt.timedelta(hours=2)).isoformat(),'method':'websocket'}}})
        self.assertEqual(prices.snapshot(self.settings,self.key,connection_identity='current',now=NOW)['status'],'last_trade')
        self.assertEqual(prices.snapshot(self.settings,self.key,connection_identity='current',now=NOW+dt.timedelta(seconds=46))['source'],'Yahoo Finance')

    def test_last_public_price_remains_visible_with_failure_and_age_label(self):
        self.cache(price(),error='참고 시세 수신 실패')
        result=prices.snapshot(self.settings,self.key,now=NOW+dt.timedelta(hours=1))
        self.assertEqual(result['value'],1234.5)
        self.assertEqual(result['status'],'stale')
        self.assertFalse(result['is_realtime'])
        self.assertIsNone(prices.snapshot(self.settings,self.key,now=NOW+dt.timedelta(days=8))['value'])

    def test_bad_cache_shapes_are_ignored(self):
        for items in ({'AAPL':None},{'AAPL':{'error':{}}}, {'AAPL':{'price':price(),'error':None}}|{str(i):{} for i in range(13)}):
            _write_cache(prices.cache_path(self.settings),{'version':1,'items':items})
            self.assertEqual(prices.read_public(self.settings),{})
        self.cache({**price(),'symbol':'MSFT'})
        self.assertIsNone(prices.snapshot(self.settings,self.key,now=NOW)['value'])

    def test_failed_refresh_preserves_only_registered_last_price(self):
        prices.watch(self.settings,self.key,'owner')
        self.cache(price())
        provider=Mock();provider.run.side_effect=TimeoutError()
        prices.refresh_public(self.settings,provider)
        row=prices.read_public(self.settings)['items']['AAPL']
        self.assertEqual(row['price']['value'],1234.5)
        self.assertTrue(row['error'])

    def test_display_routes_require_authentication_and_csrf(self):
        from cloud_app import main
        routes={route.path:route for route in main.app.routes if getattr(route,'path','').startswith('/api/company-entities/')}
        self.assertIn(main.current_user,[dep.call for dep in routes['/api/company-entities/{entity_key}/price'].dependant.dependencies])
        self.assertIn(main.csrf_guard,[dep.call for dep in routes['/api/company-entities/{entity_key}/price-watch'].dependant.dependencies])


class TradeProtocolTests(unittest.TestCase):
    def test_only_trade_topics_are_declared_and_batch_is_bounded(self):
        wanted=stream.topics(['AAPL','005930.KS'])
        self.assertEqual(stream.declaration(wanted),[{'type':'trade:us','codes':['AAPL']},{'type':'trade:kr','codes':['005930']}])
        self.assertEqual(stream.declaration({}),[])
        for symbols in (['AAPL']*13,['../../secret'],['order:us:AAPL']):
            with self.assertRaises(ValueError):stream.topics(symbols)

    def test_trade_requires_ack_exact_topic_currency_and_time(self):
        wanted=stream.topics(['AAPL']);subscribed=set(wanted)
        row={'type':'message','topic':'trade:us:AAPL','data':{'price':'1234.50','currency':'USD','timestamp':NOW.isoformat()}}
        self.assertIsNone(stream.parse_trade(json.dumps(row),wanted,set(),NOW))
        self.assertEqual(stream.parse_trade(json.dumps(row),wanted,subscribed,NOW)[1]['value'],1234.5)
        self.assertIsNone(stream.parse_trade(json.dumps({**row,'topic':'order:us:AAPL'}),wanted,subscribed,NOW))
        for data in ({**row['data'],'currency':'KRW'},{**row['data'],'price':True},
                     {**row['data'],'timestamp':NOW.replace(tzinfo=None).isoformat()},
                     {**row['data'],'timestamp':(NOW+dt.timedelta(minutes=1)).isoformat()},
                     {**row['data'],'timestamp':True}):
            with self.assertRaises(ValueError):stream.parse_trade(json.dumps({**row,'data':data}),wanted,subscribed,NOW)
        for bad in ('[]','x'*65537):
            with self.assertRaises(ValueError):stream.parse_trade(bad,wanted,subscribed,NOW)

    def display(self):
        result=TossDisplay({'key':'synthetic','secret':'synthetic'})
        result.company_stream=Mock();result.company_stream.snapshot.return_value={}
        result.next_indices=result.next_fx=float('inf')
        return result

    def test_stock_rest_has_cooldown_and_new_watches_get_initial_snapshot(self):
        display=self.display();display.request=Mock(side_effect=RuntimeError('synthetic failure'))
        with patch('cloud_app.market_broker_feed.time.monotonic',return_value=100):
            display.snapshot(['AAPL']);display.snapshot(['AAPL']);display.snapshot(['AAPL'])
            self.assertEqual(display.request.call_count,1)
            display.snapshot(['AAPL','MSFT'])
            self.assertEqual(display.request.call_count,2)
        display.client.session.close()

    def test_index_failure_does_not_block_stock_quotes_or_unsubscription(self):
        display=self.display();display.next_indices=0
        def request(path,params):
            if 'market-indicators' in path:raise RuntimeError('synthetic failure')
            return {'result':[{'symbol':'AAPL','lastPrice':'1250','timestamp':NOW.isoformat(),'currency':'USD'}]}
        display.request=Mock(side_effect=request)
        with patch('cloud_app.market_broker_feed.time.monotonic',return_value=100):
            result=display.snapshot(['AAPL'])
            self.assertEqual(result['company_prices']['AAPL']['value'],1250)
            display.snapshot([])
        display.company_stream.snapshot.assert_called_with([])
        display.client.session.close()

    def test_late_websocket_frame_cannot_replace_newer_rest_trade(self):
        display=self.display();display.request=Mock(return_value={'result':[{'symbol':'AAPL','lastPrice':'1250','timestamp':NOW.isoformat(),'currency':'USD'}]})
        display.company_stream.snapshot.return_value={'AAPL':{**price(),'method':'websocket','observed_at':(NOW-dt.timedelta(seconds=1)).isoformat()}}
        with patch('cloud_app.market_broker_feed.time.monotonic',return_value=100):
            self.assertEqual(display.snapshot(['AAPL'])['company_prices']['AAPL']['value'],1250)
        display.client.session.close()

    def test_public_fetch_never_accepts_unbounded_user_url_or_batch(self):
        with patch.object(public,'fetch') as fetch:
            for symbols in (['https://evil.test'],['AAPL']*13,[],None):
                with self.assertRaises(ValueError):public.collect({'symbols':symbols},{})
            fetch.assert_not_called()


if __name__=='__main__':
    unittest.main()
