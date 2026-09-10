import os
import time
import unittest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch

from cloud_app.provider_process import ProviderProcess, ProviderOperationError, MAX_RESPONSE_BYTES


def synthetic_provider(payload, configuration):
    if payload.get("reject"):
        from fastapi import HTTPException
        raise HTTPException(422, "API key format is invalid")
    if payload.get("stall"):
        time.sleep(60)
    if payload.get("large"):
        return "x" * (MAX_RESPONSE_BYTES + 1)
    return {"pid": os.getpid(), "value": payload["value"], "configuration": configuration}


def kis_slow_body(payload, _configuration):
    if payload.get("warmup"):
        return True
    from cloud_app.kis_quotes import KisCredentials, KisQuoteClient
    client = KisQuoteClient(KisCredentials(api_key="synthetic", api_secret="synthetic", paper=True), deadline_monotonic=time.monotonic() + 1)
    client.base_url = payload["url"]
    return client.connect()


class SyntheticKisClient:
    connects = 0

    def __init__(self, _credentials):
        self.token = ""

    def connect(self):
        type(self).connects += 1
        self.token = "synthetic-token"
        return True

    def get_quote(self, _ticker):
        from cloud_app.kis_quotes import KisWorkBudgetExceeded
        if time.monotonic() >= self.deadline_monotonic:
            raise KisWorkBudgetExceeded("deadline")
        time.sleep(.06)
        return {"price": 100}


def partial_kis_quotes(payload, configuration):
    from cloud_app import credential_broker as broker
    broker.settings = configuration
    broker.KisQuoteClient = SyntheticKisClient
    if payload.get("warmup"):
        return True
    values = broker._shared_kis_quotes_inline(
        broker.KisCredentials("synthetic-key", "synthetic-secret"),
        tuple(payload["body"]["tickers"]), deadline=payload["deadline"],
    )
    return {"count": len(values), "connects": SyntheticKisClient.connects, "pid": os.getpid()}


class ProviderProcessTests(unittest.TestCase):
    def test_normal_partial_quote_progress_arrives_without_losing_oauth_state(self):
        from cloud_app import credential_broker as broker
        configuration = SimpleNamespace(quote_deadline_seconds=1, quote_max_provider_calls=125)
        runner = ProviderProcess(partial_kis_quotes)
        try:
            runner.run({"warmup": True}, configuration, deadline=time.monotonic() + 10)
            with patch.object(broker, "settings", configuration), patch.dict(broker._network_pools, {"shared": [runner]}):
                partial = broker._network_call("shared", {"tickers": ["AAPL"] * 10}, time.monotonic() + .5)
                self.assertGreater(partial["count"], 0)
                self.assertLess(partial["count"], 10)
                following = broker._network_call("shared", {"tickers": ["AAPL"]}, time.monotonic() + 1)
                self.assertEqual(following["count"], 1)
                self.assertEqual(following["connects"], 1)
                self.assertEqual(partial["pid"], following["pid"])
        finally:
            runner.close()

    def test_trickling_kis_token_body_cannot_keep_preflight_capacity(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                body = b'{"access_token":"synthetic-token"}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                try:
                    for byte in body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(.05)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        runner = ProviderProcess(kis_slow_body)
        try:
            runner.run({"warmup": True}, None, deadline=time.monotonic() + 5)
            started = time.monotonic()
            with self.assertRaises(TimeoutError):
                runner.run({"url": "http://127.0.0.1:" + str(server.server_port)}, None, deadline=started + 1)
            self.assertLess(time.monotonic() - started, 1.5)
            self.assertIsNone(runner._process)
            self.assertTrue(runner.run({"warmup": True}, None, deadline=time.monotonic() + 5))
        finally:
            runner.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_deadline_kills_worker_and_clean_replacement_preserves_normal_reuse(self):
        runner = ProviderProcess(synthetic_provider)
        try:
            first = runner.run({"value": 1}, "synthetic", deadline=time.monotonic() + 5)
            second = runner.run({"value": 2}, "synthetic", deadline=time.monotonic() + 5)
            self.assertEqual(first["pid"], second["pid"])
            started = time.monotonic()
            with self.assertRaises(TimeoutError):
                runner.run({"stall": True}, "synthetic", deadline=started + .2)
            self.assertLess(time.monotonic() - started, 1.5)
            with self.assertRaises(ProcessLookupError):
                os.kill(first["pid"], 0)
            replacement = runner.run({"value": 3}, "synthetic", deadline=time.monotonic() + 5)
            self.assertNotEqual(first["pid"], replacement["pid"])
            self.assertEqual(replacement["value"], 3)
        finally:
            runner.close()

    def test_oversized_response_never_reaches_caller_and_worker_is_reaped(self):
        runner = ProviderProcess(synthetic_provider)
        try:
            with self.assertRaises(RuntimeError):
                runner.run({"large": True}, "synthetic", deadline=time.monotonic() + 5)
            self.assertIsNone(runner._process)
        finally:
            runner.close()

    def test_validation_error_preserves_status_and_existing_provider_state(self):
        runner = ProviderProcess(synthetic_provider)
        try:
            before = runner.run({"value": 1}, None, deadline=time.monotonic() + 5)
            with self.assertRaises(ProviderOperationError) as error:
                runner.run({"reject": True}, None, deadline=time.monotonic() + 5)
            self.assertEqual(error.exception.status_code, 422)
            after = runner.run({"value": 2}, None, deadline=time.monotonic() + 5)
            self.assertEqual(before["pid"], after["pid"])
        finally:
            runner.close()
