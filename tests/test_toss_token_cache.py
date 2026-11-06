"""Owner-only storage and simultaneous callers of the unified encrypted cache."""
import datetime as dt
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import time
import unittest
from cloud_app.toss_token_cache import SharedTossToken


class TossTokenCacheTests(unittest.TestCase):
    def cache(self, root):
        return SharedTossToken(Path(root)/'tokens', 'synthetic-client', 'synthetic-secret', 'https://example.test')

    def test_concurrent_clients_share_one_oauth_grant(self):
        with tempfile.TemporaryDirectory() as root:
            clients=[self.cache(root) for _ in range(8)];calls=[]
            def issue():
                calls.append(1);time.sleep(.01)
                return 'synthetic-token',dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)
            with ThreadPoolExecutor(max_workers=8) as pool:
                tokens=list(pool.map(lambda client:client.obtain(issue)[0],clients))
            self.assertEqual(tokens,['synthetic-token']*8)
            self.assertEqual(len(calls),1)
            if os.name!='nt':self.assertEqual(clients[0].path.stat().st_mode&0o777,0o600)
            self.assertNotIn(b'synthetic-token',clients[0].path.read_bytes())

    def test_rejected_old_token_does_not_invalidate_newer_shared_token(self):
        with tempfile.TemporaryDirectory() as root:
            cache=self.cache(root);expires=dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)
            cache.obtain(lambda:('new',expires))
            def forbidden():raise AssertionError('A newer valid token must be reused')
            self.assertEqual(cache.obtain(forbidden,rejected='old')[0],'new')
            self.assertEqual(cache.obtain(lambda:('renewed',expires),rejected='new')[0],'renewed')

    @unittest.skipIf(os.name=='nt','POSIX file modes and symlinks')
    def test_symlink_and_publicly_readable_token_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            cache=self.cache(root);expires=dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)
            cache.obtain(lambda:('token',expires));cache.path.chmod(0o644)
            with self.assertRaises(PermissionError):cache.obtain(lambda:('replacement',expires))
            cache.path.unlink();cache.path.symlink_to(Path(root)/'outside')
            with self.assertRaises(OSError):cache.obtain(lambda:('replacement',expires))
