"""Password hashing and short-lived signed browser sessions."""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import secrets


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise ValueError("올바른 이메일 주소가 아닙니다")
    return email


def validate_password(value: str) -> None:
    if len(value) < 10 or len(value) > 128:
        raise ValueError("비밀번호는 10~128자여야 합니다")


def hash_password(password: str) -> str:
    validate_password(password)
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1${}${}".format(salt.hex(), digest.hex())


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p), dklen=32
        )
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_session(user_id: str, role: str, secret: str, hours: int) -> tuple[str, str]:
    csrf = secrets.token_urlsafe(24)
    payload = {
        "sub": user_id,
        "role": role,
        "csrf": csrf,
        "jti": secrets.token_urlsafe(32),
        "exp": int((dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=hours)).timestamp()),
    }
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return body + "." + signature, csrf


def parse_session(token: str, secret: str) -> dict:
    try:
        body, signature = token.split(".", 1)
        expected = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("bad signature")
        payload = json.loads(_unb64(body))
        if not isinstance(payload, dict):
            raise ValueError("bad payload")
        if not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise ValueError("bad subject")
        if not isinstance(payload.get("csrf"), str) or len(payload["csrf"]) < 20:
            raise ValueError("bad csrf")
        if not isinstance(payload.get("jti"), str) or len(payload["jti"]) < 20:
            raise ValueError("bad session id")
        if int(payload["exp"]) < int(dt.datetime.now(dt.timezone.utc).timestamp()):
            raise ValueError("expired")
        return payload
    except Exception as exc:
        raise ValueError("invalid session") from exc
