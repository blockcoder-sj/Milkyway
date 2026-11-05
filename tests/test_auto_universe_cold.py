"""Empty-cache first-buy path with real HTTP/child process and replayed time.

Only the provider's directory, candles/prices and corporate-action dataset are
synthetic. The data-worker orchestration, Toss adapter and paper ledger are real.
"""
import datetime as dt
import json
import os
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.parse import urlsplit
from unittest.mock import patch

from sqlalchemy import select,func
from cloud_app import auto_universe as auto,personal_data,worker
from cloud_app.database import PaperAccount,PaperFill,RuntimeHeartbeat
from cloud_app.local_demo import _atomic_json
from cloud_app.provider_process import ProviderProcess
from tests import test_personal_continuous as continuous
from tests.test_auto_universe import automatic_spec,history,auto_http_execute


def cold_http_execute(payload,configuration):
    if payload['action']=='catalog':
        now=dt.datetime.fromisoformat(payload['now'])
        catalog={'date':now.astimezone(auto.EASTERN).date().isoformat(),
                 'symbols':['AAA','BBB'],'sha256':'cold-fixture-directory'}
        _atomic_json(Path(configuration['root'])/'catalog.json',catalog)
        return {'count':2}
    return auto_http_execute(payload,configuration)


class ColdAutomaticPaperTests(unittest.TestCase):
    def setUp(self):
        f=self.fixture=continuous.ContinuousPaperTests()
        # The normal continuous fixture warms selected-symbol history. This
        # regression must begin with neither selected nor market-wide history.
        with patch.object(continuous.ContinuousPaperTests,'refresh',lambda self:None):f.setUp()
        self.addCleanup(f.tearDown)
        self.assertFalse((f.settings.dataset_dir/'current.json').exists())
        self.assertFalse(auto.root_for(f.settings).exists())
        spec=self.spec=automatic_spec()
        with f.sessions() as db:
            db.get(PaperAccount,f.account).strategy.spec_json=spec.model_dump_json();db.commit()
        f.candle_requests=[]
        class Handler(f.server.RequestHandlerClass):
            def do_GET(self):
                if urlsplit(self.path).path!='/api/v1/candles':return super().do_GET()
                f.candle_requests.append(self.path)
                if f.http_status!=200:
                    return self.reply(f.http_status,{'error':{'code':'rate-limit-exceeded'}})
                candles=[{'timestamp':r[0]+'T00:00:00-05:00','currency':'USD',
                    **{key:str(value) for key,value in zip(('openPrice','highPrice','lowPrice','closePrice','volume'),r[1:])}}
                    for r in history(f.now)['rows']]
                self.reply(200,{'result':{'candles':candles,'nextBefore':None}})
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def close():server.shutdown();server.server_close();thread.join(timeout=2)
        self.addCleanup(close)
        endpoint=patch.dict(os.environ,{'MILKYWAY_OFFLINE_TOSS_ENDPOINT':f'http://127.0.0.1:{server.server_port}'})
        endpoint.start();self.addCleanup(endpoint.stop)
        self.runner=ProviderProcess(cold_http_execute);self.addCleanup(self.runner.close)
        process=patch.object(auto,'_process',self.runner);process.start();self.addCleanup(process.stop)
        f.prices.update(AAA=110.,BBB=100.)

    def data_step(self):
        f=self.fixture;real_refresh=auto.refresh;real_history=personal_data.refresh_personal_data
        with patch.object(auto,'refresh',side_effect=lambda settings,specs,config:real_refresh(settings,specs,config,f.now)),patch.object(personal_data,'refresh_personal_data',side_effect=lambda symbols,settings,**kwargs:real_history(symbols,settings,now=f.now,**kwargs)):
            return worker.refresh_personal_history(f.settings)

    def fills(self):
        with self.fixture.sessions() as db:return db.scalar(select(func.count()).select_from(PaperFill))

    def test_empty_tickers_and_empty_cache_collect_before_first_purchase(self):
        f=self.fixture
        f.tick();self.assertEqual(self.fills(),0)
        self.assertTrue(self.data_step())  # Catalog + first actual candle batch.
        self.assertEqual(len(f.candle_requests),2)
        f.tick();self.assertEqual(self.fills(),0)  # A partial preparation is never a decision.
        self.assertFalse(self.data_step())
        self.assertEqual(auto.decision_for(f.settings,self.spec,f.now)['targets'],['AAA'])
        f.tick();self.assertEqual(self.fills(),2)
        f.tick();self.assertEqual(self.fills(),2)

    def test_interrupted_first_preparation_recovers_without_manual_tickers(self):
        f=self.fixture;f.http_status=429
        self.assertFalse(self.data_step())
        self.assertEqual(auto.status(f.settings)['status'],'retry_wait')
        f.tick();self.assertEqual(self.fills(),0)
        f.http_status=200;f.now+=dt.timedelta(seconds=61);f.monotonic+=61
        self.assertTrue(self.data_step())
        self.assertFalse(self.data_step())
        f.tick();self.assertEqual(self.fills(),2)

        f.http_status=503;f.monotonic+=61;f.now+=dt.timedelta(seconds=61)
        f.tick();self.assertEqual(self.fills(),2)
        f.http_status=200;f.monotonic+=61;f.now+=dt.timedelta(seconds=61)
        f.tick();self.assertEqual(self.fills(),2)

    def test_selection_status_recovers_only_after_fresh_screen_without_new_buys(self):
        f=self.fixture
        self.data_step();self.data_step();f.tick()
        self.assertEqual(self.fills(),2)
        def status():
            with f.sessions() as db:
                return json.loads(db.get(RuntimeHeartbeat,'paper-account:'+f.account).detail)['status']
        self.assertEqual(status(),'active')
        # Held quotes recover before the complete-market scan. That alone must
        # not clear the selection warning or cause another initial purchase.
        f.now+=dt.timedelta(seconds=auto.DECISION_MAX_AGE+1)
        f.tick();self.assertEqual(status(),'waiting_selection')
        f.tick();self.assertEqual(status(),'waiting_selection')
        self.assertEqual(self.fills(),2)
        self.data_step()
        f.tick();self.assertEqual(status(),'active')
        self.assertEqual(self.fills(),2)
