"""Broker display contracts: synthetic frames, no credentials or network calls."""
import datetime as dt
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from cloud_app import market_broker as broker, market_broker_feed as feed, market_service
from cloud_app.market_catalog import BY_ID
from cloud_app.market_feed import Observation

NOW = dt.datetime(2026, 9, 30, 1, 20, 30, tzinfo=dt.timezone.utc)


def frame(code='0001', clock='102030', sign='2'):
    fields = [code, clock, '2700', sign, '10', '1', '1', '1', '1', '0.37', '2680', '2710', '2670'] + ['0'] * 17
    return '0|H0UPCNT0|001|' + '^'.join(fields)


class BrokerDisplayTests(unittest.TestCase):
    def test_catalog_mapping_is_fixed_and_valid(self):
        self.assertEqual(len(feed.KIS_CODES), 11)
        self.assertTrue(set(feed.KIS_CODES.values()).issubset(BY_ID))
        self.assertEqual(feed.CAPABILITIES['toss'], ('kospi', 'kosdaq', 'usdkrw'))

    def test_kis_signed_difference_and_timestamps(self):
        for sign, previous in [('2',2690), ('5',2710), ('3',2700)]:
            value = feed.parse_kis_frame(frame(sign=sign), NOW)['kospi']
            self.assertEqual(value['previous_close'], previous)
            self.assertEqual(Observation.model_validate(value).observed_at, NOW)
        self.assertEqual(feed.parse_kis_frame(frame(clock='092000'), NOW), {})
        self.assertEqual(feed.parse_kis_frame(frame(code='9999'), NOW), {})

    def test_kis_rejects_unexpected_oversized_and_nonfinite_frames(self):
        for bad in ('x' * 65537, frame().replace('H0UPCNT0','H0STCNT0'), frame().replace('0|','1|',1),
                    frame().replace('|001|','|021|'), frame().replace('2700','NaN'), frame()+'^0'):
            with self.subTest(bad=bad[:30]), self.assertRaises(ValueError):
                feed.parse_kis_frame(bad, NOW)

    def test_toss_missing_timestamp_is_not_fabricated(self):
        row = {'symbol':'KOSPI','lastPrice':'2700'}
        self.assertEqual(feed.parse_toss_indices({'result':[row]},NOW), {})
        row['timestamp'] = NOW.isoformat()
        value = feed.parse_toss_indices({'result':[row]},NOW)['kospi']
        self.assertIsNone(value['previous_close'])
        row['timestamp'] = NOW.replace(tzinfo=None).isoformat()
        self.assertEqual(feed.parse_toss_indices({'result':[row]},NOW), {})

    def test_fx_mid_rate_and_validity(self):
        payload = {'result': {'baseCurrency':'USD','quoteCurrency':'KRW','rate':'1410','midRate':'1400',
                   'validFrom':NOW.isoformat(),'validUntil':(NOW+dt.timedelta(seconds=60)).isoformat()}}
        self.assertEqual(feed.parse_toss_fx(payload,NOW)['value'],1400)
        with self.assertRaises(ValueError): feed.parse_toss_fx(payload,NOW+dt.timedelta(minutes=2))
        payload['result']['quoteCurrency'] = 'JPY'
        with self.assertRaises(ValueError): feed.parse_toss_fx(payload,NOW)

    def test_broker_priority_does_not_mix_yahoo_baseline(self):
        row = {'id':'kospi','value':2600,'previous_close':2500,'change':100,'change_pct':4,
               'source':'Yahoo Finance','error':'Yahoo failed','sparkline':[2500,2600]}
        obs = Observation(value=2700,observed_at=NOW,fetched_at=NOW).model_dump(mode='json')
        broker.project_broker(row, {'provider':'toss','items':{'kospi':obs}},NOW)
        self.assertEqual(row['value'],2700)
        self.assertEqual(row['source'],'토스증권')
        self.assertIsNone(row['change_pct'])
        self.assertIsNone(row['previous_close'])
        self.assertEqual(row['sparkline'],[])
        self.assertFalse(row['is_realtime'])

    def test_stale_broker_falls_back_to_unchanged_yahoo_value(self):
        row = {'id':'kospi','value':2600,'source':'Yahoo Finance'}
        obs = feed.parse_kis_frame(frame(),NOW)['kospi']
        broker.project_broker(row,{'provider':'kis','items':{'kospi':obs}},NOW+dt.timedelta(seconds=31))
        self.assertEqual(row['value'],2600)
        self.assertEqual(row['source'],'Yahoo Finance')
        self.assertIn('fallback_reason',row)

    def test_kis_current_frame_is_realtime(self):
        row={'id':'kospi'}
        broker.project_broker(row,{'provider':'kis','items':feed.parse_kis_frame(frame(),NOW)},NOW)
        self.assertTrue(row['is_realtime'])
        self.assertEqual(row['status'],'realtime')

    def test_expired_fx_falls_back(self):
        row={'id':'usdkrw','value':1350,'source':'Yahoo Finance'}
        obs=Observation(value=1400,observed_at=NOW,fetched_at=NOW,regular_end=NOW+dt.timedelta(seconds=5)).model_dump(mode='json')
        broker.project_broker(row,{'provider':'toss','items':{'usdkrw':obs}},NOW+dt.timedelta(seconds=6))
        self.assertEqual(row['value'],1350)

    def test_toss_fx_honors_its_validity_window_and_fresh_collection(self):
        row={'id':'usdkrw','value':1350,'source':'Yahoo Finance'}
        obs=Observation(value=1400,observed_at=NOW-dt.timedelta(seconds=159),fetched_at=NOW-dt.timedelta(seconds=40),regular_end=NOW+dt.timedelta(seconds=100)).model_dump(mode='json')
        broker.project_broker(row,{'provider':'toss','items':{'usdkrw':obs}},NOW)
        self.assertEqual(row['value'],1400)
        self.assertEqual(row['source'],'토스증권')
        self.assertEqual(row['status'],'reference')
        row={'id':'usdkrw','value':1350,'source':'Yahoo Finance'}
        broker.project_broker(row,{'provider':'toss','items':{'usdkrw':obs}},NOW+dt.timedelta(seconds=51))
        self.assertEqual(row['value'],1350)  # An old fetch cannot stay active just because validUntil is future.

    def test_cache_is_scoped_to_current_owner_and_credential_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            settings=SimpleNamespace(personal_local_mode=True,production=False,credential_backend='local',dataset_dir=Path(temp)/'data')
            market_service._write_cache(broker.cache_path(settings),{'identity':'current','provider':'kis','items':{}})
            self.assertEqual(broker.read_cache(settings,'other'),{})
            self.assertEqual(broker.read_cache(settings,None),{})
            self.assertEqual(broker.read_cache(settings,'current')['provider'],'kis')
            connection=SimpleNamespace(user_id='u',provider='kis',environment='real',updated_at=NOW)
            old=broker.identity(connection); connection.updated_at=NOW+dt.timedelta(seconds=1)
            self.assertNotEqual(old,broker.identity(connection))

    def test_ambiguous_owner_never_selects_a_connection(self):
        session=Mock(); session.scalars.return_value.all.return_value=[Mock(),Mock()]
        self.assertIsNone(broker.owner_connection(session))
        session.get.assert_not_called()

    def test_redirects_and_environment_proxies_disabled(self):
        session=feed.FixedSession(); self.assertFalse(session.trust_env)
        response=Mock(status_code=302)
        with patch('requests.Session.request',return_value=response) as request:
            with self.assertRaises(ValueError): session.get('https://openapi.tossinvest.com/test')
        self.assertFalse(request.call_args.kwargs['allow_redirects'])
        response.close.assert_called_once()
        session.close()

    def test_no_connection_closes_child_and_clears_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            settings=SimpleNamespace(personal_local_mode=True,production=False,credential_backend='local',dataset_dir=Path(temp)/'data')
            with patch.object(broker,'owner_connection',return_value=None), patch.object(broker._provider,'close') as close, patch.object(broker._provider,'run') as run:
                self.assertIsNone(broker.refresh_broker(settings,Mock()))
            close.assert_called_once(); run.assert_not_called()

    def test_kis_paper_credentials_are_never_used_on_real_endpoint(self):
        self.assertEqual(feed.collect_broker({}, {'provider':'kis','environment':'paper'}),{})

    def test_stalled_stream_is_reaped_by_coordinator(self):
        stream=object.__new__(feed.KisDisplay); stream.last_progress=0
        with patch.object(feed.time,'monotonic',return_value=100):
            with self.assertRaises(RuntimeError): stream.snapshot()
