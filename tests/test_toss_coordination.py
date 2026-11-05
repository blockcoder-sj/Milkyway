"""Real loopback HTTP + spawned clients enforcing Toss's one-valid-token rule."""
import datetime as dt
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from cloud_app import market_data_credentials
from cloud_app.toss_quotes import (
    TossQuoteClient, TossCredentials, TossAuthenticationError, TossIpNotAllowedError,
    TossEdgeBlockedError, TossPermissionError,
)
from cloud_app.toss_token_cache import SharedTossToken

UTC = dt.timezone.utc
CLIENT = 'Offline-Client-ID-0000000000001'
SECRET = 'Offline-Client-Secret-000000001'


def collect_in_process(payload):
    endpoint, root, shared, role = payload
    TossQuoteClient.base_url = endpoint
    client = TossQuoteClient(TossCredentials(CLIENT, SECRET))
    client.shared_token = SharedTossToken(Path(root), CLIENT, SECRET, endpoint) if shared else None
    errors = 0
    try:
        # Three separate adapters: paper quotes, history candles, and display.
        client.authenticate()
        for _ in range(10):
            try:
                if role == 'quotes': client.get_prices(['AAA'])
                elif role == 'history': client.daily_candles('AAA', count=1)
                else: client.get_json('/api/v1/market-indicators/prices', {'symbols':'KOSPI'})
            except TossAuthenticationError: errors += 1
        return {'role':role,'errors':errors}
    finally:
        client.session.close()


class SingleTokenServerTests(unittest.TestCase):
    last_report = {}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='toss-shared-token-')
        self.root = Path(self.temp.name)
        self.issued = self.denied = self.gets = 0
        self.current = ''
        self.mode = None
        self.secret = SECRET
        self.lock = threading.Lock()
        fixture = self
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            disable_nagle_algorithm = True
            def reply(self, status, payload):
                raw = json.dumps(payload).encode()
                self.send_response(status); self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
            def do_POST(self):
                data=parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode())
                if fixture.mode:
                    if fixture.mode == 'access_denied':
                        return self.reply(403,{'error':'access_denied','error_description':'IP address not allowed'})
                    return self.reply(403,{'error':{'code':fixture.mode,'message':'untrusted '+SECRET}})
                if data.get('client_id') != [CLIENT] or data.get('client_secret') != [fixture.secret]:
                    return self.reply(401,{'error':'invalid_client','error_description':'Client authentication failed'})
                with fixture.lock:
                    fixture.issued += 1
                    fixture.current = 'synthetic-bearer-' + str(fixture.issued)
                    token=fixture.current
                self.reply(200,{'access_token':token,'expires_in':86400})
            def do_GET(self):
                with fixture.lock:
                    fixture.gets += 1
                    allowed=self.headers.get('Authorization') == 'Bearer '+fixture.current
                    if not allowed:fixture.denied += 1
                if not allowed:
                    return self.reply(401,{'error':{'code':'token-revoked'}})
                if urlsplit(self.path).path == '/api/v1/candles':
                    result={'candles':[{'timestamp':'2026-11-04T00:00:00+09:00','currency':'USD','openPrice':'100','highPrice':'101','lowPrice':'99','closePrice':'100','volume':'1000000'}],'nextBefore':None}
                else:
                    result=[{'symbol':'AAA','lastPrice':'100','currency':'USD','timestamp':dt.datetime.now(UTC).isoformat()}]
                self.reply(200,{'result':result})
            def log_message(self,*args):pass
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.endpoint=f'http://127.0.0.1:{self.server.server_port}'
        self.patch=patch.object(TossQuoteClient,'base_url',self.endpoint);self.patch.start()

    def tearDown(self):
        self.patch.stop();self.server.shutdown();self.server.server_close();self.thread.join(timeout=2);self.temp.cleanup()

    def client(self, secret=SECRET, shared=True):
        client=TossQuoteClient(TossCredentials(CLIENT,secret))
        client.shared_token=SharedTossToken(self.root/'tokens',CLIENT,secret,self.endpoint) if shared else None
        self.addCleanup(client.session.close)
        return client

    def test_unshared_clients_reproduce_revocation_and_shared_clients_reuse_one_token(self):
        a,b=self.client(shared=False),self.client(shared=False)
        a.authenticate();b.authenticate()
        a.get_prices(['AAA']);b.get_prices(['AAA'])
        self.assertGreaterEqual(self.issued,4)
        self.assertGreaterEqual(self.denied,2)
        baseline={'issued':self.issued,'revoked_responses':self.denied}
        self.issued=self.denied=self.gets=0;self.current=''
        a,b=self.client(),self.client()
        for _ in range(10):
            a.get_prices(['AAA']);b.get_prices(['AAA'])
        self.assertEqual(self.issued,1);self.assertEqual(self.denied,0)
        raw=next((self.root/'tokens').glob('*.token')).read_bytes()
        for value in [SECRET,CLIENT,self.current]:self.assertNotIn(value.encode(),raw)
        type(self).last_report={'before':baseline,'after':{'issued':self.issued,'revoked_responses':self.denied,'successful_queries':self.gets}}

    def test_three_spawned_roles_share_one_token(self):
        with multiprocessing.get_context('spawn').Pool(3) as pool:
            result=pool.map(collect_in_process,[(self.endpoint,str(self.root/'process-cache'),True,role) for role in ['quotes','history','display']])
        self.assertEqual(sum(r['errors'] for r in result),0,result)
        self.assertEqual(self.issued,1)
        self.assertEqual(self.denied,0)
        self.assertEqual(self.gets,30)

    def test_newly_published_token_is_adopted_after_inflight_rejection(self):
        a,b=self.client(),self.client()
        a.authenticate();old=a.token
        b.authenticate(force=True)
        a._refresh_rejected_token(old)
        self.assertEqual(a.token,b.token)
        self.assertEqual(self.issued,2)
        a.get_prices(['AAA']);self.assertEqual(self.denied,0)

    def test_rotated_secret_cannot_reuse_old_cache_or_overwrite_new_token(self):
        old=self.client();old.authenticate()
        self.secret='Rotated-Offline-Secret-00000000002'
        new=self.client(self.secret);new.authenticate()
        self.assertEqual(self.issued,2)
        with self.assertRaises(TossAuthenticationError):old.get_prices(['AAA'])
        new.get_prices(['AAA']);self.assertEqual(self.issued,2)

    def test_ip_waf_and_permission_denials_are_distinct_and_do_not_leak_input(self):
        cases=[('access_denied',TossIpNotAllowedError,'허용 IP'),('edge-blocked',TossEdgeBlockedError,'edge-blocked'),('forbidden',TossPermissionError,'접근 권한')]
        for mode,error,word in cases:
            with self.subTest(mode=mode):
                self.mode=mode;client=self.client(shared=False)
                with self.assertRaises(error) as raised:client.authenticate()
                self.assertNotIn(SECRET,str(raised.exception))
                with patch.object(market_data_credentials,'TossQuoteClient',return_value=client):
                    with self.assertRaises(market_data_credentials.MarketDataProviderError) as displayed:
                        market_data_credentials.verify_connection('toss','live',CLIENT,SECRET)
                self.assertIn(word,str(displayed.exception))
                if mode != 'access_denied':self.assertIn('확정할 수 없습니다',str(displayed.exception))

    def test_history_worker_keeps_the_provider_reason_visible(self):
        from fastapi import HTTPException
        from cloud_app import auto_universe as auto
        for mode,word in [('access_denied','허용 IP 불일치'),('edge-blocked','edge-blocked'),('forbidden','접근 권한')]:
            with self.subTest(mode=mode):
                self.mode=mode
                with patch.object(auto,'_client',self.client(shared=False)), patch('yfinance.download') as yahoo:
                    with self.assertRaises(HTTPException) as raised:
                        auto._execute({'action':'history','symbols':['AAA'],'required':'2026-11-04','now':dt.datetime.now(UTC).isoformat()}, {'root':str(self.root)})
                    yahoo.assert_not_called()
                self.assertTrue(raised.exception.detail.startswith('TOSS: '))
                self.assertIn(word,raised.exception.detail)
                self.assertNotIn(SECRET,raised.exception.detail)

    def test_paper_worker_keeps_the_provider_reason_visible(self):
        from fastapi import HTTPException
        from cloud_app import worker
        self.mode='edge-blocked'
        with patch.object(worker,'_personal_quote_client',None):
            with self.assertRaises(HTTPException) as raised:
                worker._personal_quote_execute({'tickers':['AAA']},{'provider':'toss','environment':'live','key':CLIENT,'secret':SECRET})
        self.assertTrue(raised.exception.detail.startswith('TOSS: '))
        self.assertIn('edge-blocked',raised.exception.detail)
        self.assertIn('확정할 수 없습니다',raised.exception.detail)

    def test_personal_clients_automatically_choose_the_same_cache(self):
        from cloud_app.config import get_settings
        from dataclasses import replace
        settings=replace(get_settings(),personal_local_mode=True,credential_backend='local',app_env='development',dataset_dir=self.root/'runtime/personal-data')
        with patch('cloud_app.config.get_settings',return_value=settings):
            a=TossQuoteClient(TossCredentials(CLIENT,SECRET));b=TossQuoteClient(TossCredentials(CLIENT,SECRET))
            try:
                a.get_prices(['AAA']);b.get_prices(['AAA'])
                self.assertEqual(self.issued,1)
                self.assertEqual(a.shared_token.path,b.shared_token.path)
            finally:a.session.close();b.session.close()
