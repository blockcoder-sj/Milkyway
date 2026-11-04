"""Workers share one valid local token without racing grants or leaking files."""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from cloud_app import toss_token_cache as cache


class TokenCacheTests(unittest.TestCase):
    def client(self):
        return SimpleNamespace(credentials=SimpleNamespace(client_id="synthetic",client_secret="synthetic-secret"),token="",token_expires_at=dt.datetime.min.replace(tzinfo=dt.timezone.utc))

    def test_concurrent_clients_mint_once_and_reuse_private_token(self):
        with tempfile.TemporaryDirectory() as root,patch.object(cache,"ROOT",Path(root)):
            clients=[self.client() for _ in range(8)];calls=[]
            def run(client):
                def grant():
                    calls.append(1);time.sleep(.01)
                    client.token="synthetic-token";client.token_expires_at=dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)
                cache.authenticate(client,grant);return client.token
            with ThreadPoolExecutor(max_workers=8) as pool:tokens=list(pool.map(run,clients))
            self.assertEqual(tokens,["synthetic-token"]*8);self.assertEqual(len(calls),1)
            path,_=cache._paths(clients[0]);self.assertEqual(path.stat().st_mode&0o777,0o600)

    def test_rejected_old_token_does_not_invalidate_newer_shared_token(self):
        with tempfile.TemporaryDirectory() as root,patch.object(cache,"ROOT",Path(root)):
            client=self.client();path,_=cache._paths(client)
            cache._write(path,{"token":"new","expires":(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat()})
            client.token="old";cache.invalidate(client)
            self.assertEqual(cache._read(path)["token"],"new")
            client.token="new";cache.invalidate(client,"old")
            self.assertEqual(client.token,"new");self.assertEqual(cache._read(path)["token"],"new")
            client.token="new";cache.invalidate(client);self.assertEqual(cache._read(path),{})

    def test_symlink_and_publicly_readable_token_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as root,patch.object(cache,"ROOT",Path(root)):
            client=self.client();path,_=cache._paths(client)
            path.write_text('{}');path.chmod(0o644)
            with self.assertRaises(ValueError):cache.authenticate(client,lambda:None)
            path.unlink();path.symlink_to(Path(root)/"outside")
            with self.assertRaises(OSError):cache.authenticate(client,lambda:None)
