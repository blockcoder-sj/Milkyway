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
CURRENT_SCRYPT_N = 2**15
CURRENT_SCRYPT_R = 8
CURRENT_SCRYPT_P = 1
_MIN_ACCEPTED_SCRYPT_N = 2**14
_MAX_ACCEPTED_SCRYPT_N = 2**18


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise ValueError("올바른 이메일 주소가 아닙니다")
    return email


def validate_password(value: str) -> None:
    if len(value) < 10 or len(value) > 128:
        raise ValueError("비밀번호는 10~128자여야 합니다")


def hash_password(
    password: str,
    *,
    n: int = CURRENT_SCRYPT_N,
    r: int = CURRENT_SCRYPT_R,
    p: int = CURRENT_SCRYPT_P,
) -> str:
    validate_password(password)
    if (
        n < _MIN_ACCEPTED_SCRYPT_N
        or n > _MAX_ACCEPTED_SCRYPT_N
        or n & (n - 1)
        or not 1 <= r <= 16
        or not 1 <= p <= 4
    ):
        raise ValueError("scrypt password policy is invalid")
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=n, r=r, p=p, dklen=32, maxmem=64 * 1024 * 1024
    )
    return "scrypt${}${}${}${}${}".format(n, r, p, salt.hex(), digest.hex())


def _password_hash_parameters(encoded: str) -> tuple[int, int, int, bytes, bytes]:
    algorithm, n_raw, r_raw, p_raw, salt_hex, digest_hex = encoded.split("$")
    if algorithm != "scrypt":
        raise ValueError("unsupported password hash")
    n, r, p = int(n_raw), int(r_raw), int(p_raw)
    if (
        n < _MIN_ACCEPTED_SCRYPT_N
        or n > _MAX_ACCEPTED_SCRYPT_N
        or n & (n - 1)
        or not 1 <= r <= 16
        or not 1 <= p <= 4
    ):
        raise ValueError("invalid scrypt parameters")
    salt = bytes.fromhex(salt_hex)
    digest = bytes.fromhex(digest_hex)
    if len(salt) != 16 or len(digest) != 32:
        raise ValueError("invalid password hash size")
    return n, r, p, salt, digest


def password_needs_rehash(encoded: str) -> bool:
    try:
        n, r, p, _salt, _digest = _password_hash_parameters(encoded)
    except (ValueError, TypeError):
        return True
    return (n, r, p) != (CURRENT_SCRYPT_N, CURRENT_SCRYPT_R, CURRENT_SCRYPT_P)


def verify_password(password: str, encoded: str) -> bool:
    try:
        n, r, p, salt, expected = _password_hash_parameters(encoded)
        actual = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=32,
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(actual, expected)
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
