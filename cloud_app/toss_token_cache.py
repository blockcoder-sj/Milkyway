"""One encrypted, cross-process OAuth token per Toss client in personal mode.

Toss revokes the preceding token on every issuance. The file lock spans issuance
and atomic publication, so quote, display and history workers share one token.
No client secret or plaintext bearer token is written to disk.
"""
from contextlib import contextmanager
import datetime as dt
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import tempfile
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from . import native_platform as locks
from .bounded_io import read_bounded_file

UTC = dt.timezone.utc
MAX_CACHE_BYTES = 96 * 1024


class SharedTossToken:
    def __init__(self, root, client_id, client_secret, origin):
        self.root = Path(root)
        if self.root.is_symlink():
            raise ValueError("Unsafe token cache directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt": self.root.chmod(0o700)
        identity = (origin + "\0" + client_id).encode()
        name = hashlib.sha256(identity).hexdigest()
        self.path, self.lock_path = self.root / (name + ".token"), self.root / (name + ".lock")
        self.aad = b"milkyway-toss-shared-token-v1\0" + identity
        self.key = hmac.new(client_secret.encode(), self.aad, hashlib.sha256).digest()

    @contextmanager
    def _locked(self):
        descriptor = os.open(self.lock_path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "a+b") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError("Unsafe token lock")
            deadline = time.monotonic() + 15
            while True:
                try:
                    locks.flock(handle, locks.LOCK_EX | locks.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Shared token issuance is busy")
                    time.sleep(.03)
            try: yield
            finally: locks.flock(handle, locks.LOCK_UN)

    def _read(self):
        try:
            info = self.path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise OSError("Unsafe token cache file")
            if os.name != "nt" and (info.st_uid != os.getuid() or info.st_mode & 0o077):
                raise PermissionError("Token cache must be private to its owner")
            blob = read_bounded_file(self.path, maximum_bytes=MAX_CACHE_BYTES)
            raw = AESGCM(self.key).decrypt(blob[:12], blob[12:], self.aad)
            data = json.loads(raw)
            token = data["token"]
            expires = dt.datetime.fromisoformat(data["expires_at"])
            now = dt.datetime.now(UTC)
            if (not isinstance(token, str) or not 1 <= len(token) <= 32768 or expires.tzinfo is None
                    or not dt.timedelta(0) < expires-now <= dt.timedelta(days=2)):
                return None
            return token, expires
        except FileNotFoundError:
            return None
        except (ValueError, KeyError, TypeError, UnicodeError):
            return None
        except Exception as exc:
            from cryptography.exceptions import InvalidTag
            if isinstance(exc, InvalidTag): return None
            raise

    def _write(self, token, expires):
        raw = json.dumps({"token":token,"expires_at":expires.isoformat()}, separators=(",", ":")).encode()
        nonce = os.urandom(12)
        blob = nonce + AESGCM(self.key).encrypt(nonce, raw, self.aad)
        descriptor, temporary = tempfile.mkstemp(prefix=".token-", dir=self.root)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(blob); handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)

    def obtain(self, issue, *, rejected=None, force=False):
        with self._locked():
            cached = self._read()
            if cached and not force and (rejected is None or cached[0] != rejected):
                return cached
            token, expires = issue()
            self._write(token, expires)
            return token, expires


def personal_token_cache(credentials, origin):
    from .config import get_settings
    settings = get_settings()
    if not settings.personal_local_mode or settings.production or settings.credential_backend != "local":
        return None
    return SharedTossToken(settings.dataset_dir.parent / "toss-auth", credentials.client_id, credentials.client_secret, origin)
