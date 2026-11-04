"""Owner-only token coordination for local workers; one token per Toss client."""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from contextlib import contextmanager

from .config import ROOT


def enabled():
    return os.environ.get("PERSONAL_LOCAL_MODE", "").lower() in {"1", "true", "yes"}


def _paths(client):
    root = Path(ROOT)/"runtime/.toss-tokens"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Invalid local token directory")
    identity = hashlib.sha256((client.credentials.client_id+"\0"+client.credentials.client_secret).encode()).hexdigest()
    return root/(identity+".json"), root/(identity+".lock")


@contextmanager
def _locked(path):
    fd = os.open(path, os.O_RDWR|os.O_CREAT|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_NONBLOCK",0), 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("Invalid local token lock")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _read(path):
    try:
        fd = os.open(path, os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_NONBLOCK",0))
        with os.fdopen(fd, encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 32768:
                raise ValueError("Invalid local token file")
            return json.loads(stream.read(32769))
    except FileNotFoundError:
        return {}


def _write(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix=".new-",dir=path.parent)
    try:
        with os.fdopen(descriptor,"w",encoding="utf-8") as stream:
            json.dump(value,stream);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def authenticate(client, grant):
    path, lock = _paths(client)
    with _locked(lock):
        cached = _read(path)
        try:
            token = cached["token"]
            expires = dt.datetime.fromisoformat(cached["expires"])
            valid = isinstance(token,str) and 0 < len(token) <= 16384 and expires.tzinfo is not None and expires > dt.datetime.now(dt.timezone.utc)
        except (KeyError,TypeError,ValueError):
            valid = False
        if valid:
            client.token, client.token_expires_at = token, expires
        else:
            client.token = ""  # A rejected grant must not reenter invalidation's lock.
            grant()
            _write(path,{"token":client.token,"expires":client.token_expires_at.isoformat()})


def invalidate(client, rejected_token=None):
    token = rejected_token or client.token
    if not token:
        return
    path, lock = _paths(client)
    with _locked(lock):
        if _read(path).get("token") == token:
            _write(path,{})
    if client.token == token:
        client.token = ""
