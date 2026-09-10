"""Independent authentication and durable authorization on the broker VM.

Public app/worker database roles must have no write access to these sessions,
permits or claims. Runtime SQL policies independently resolve the presented raw
opaque token against authority-owned records; caller-selected user IDs are never
authorization evidence.
"""

import datetime as dt
import hashlib
import hmac
import json
import re
import secrets
import threading
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from .database import (
    AuthoritySession, Invitation, LoginThrottle, OperationPermit, User,
    invitation_token_hash, quota_allocation, utcnow,
)
from .security import hash_password, normalize_email, password_needs_rehash, validate_password, verify_password


_password_slots = threading.BoundedSemaphore(4)
_OPAQUE_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}")


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    return hash_password("milkyway-authority-invalid-login")


def token_hash(token: str) -> str:
    if not isinstance(token, str) or not _OPAQUE_TOKEN.fullmatch(token):
        raise HTTPException(401, "세션이 만료되었습니다")
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _aware(value):
    return value if value.tzinfo is not None else value.replace(tzinfo=dt.timezone.utc)


def _budget_key(settings, kind: str, value: str) -> str:
    return hmac.new(
        settings.session_secret.encode(), ("authority-budget\0" + kind + "\0" + value).encode(), hashlib.sha256,
    ).hexdigest()


def consume_budget(session, settings, kind: str, value: str, limit: int, seconds: int, *, enforce=True, commit=True) -> bool:
    key = _budget_key(settings, kind, value)
    now = utcnow()
    with quota_allocation(session, "authority-budget", key):
        if kind == "login-global":
            session.execute(delete(LoginThrottle).where(
                LoginThrottle.bucket_kind.in_(("login-global", "login-account")),
                LoginThrottle.updated_at < now - dt.timedelta(seconds=max(120, settings.login_account_window_seconds * 2)),
            ))
        row = session.get(LoginThrottle, key)
        if row is None:
            row = LoginThrottle(key_hash=key, bucket_kind=kind[:20], attempts=0, window_started_at=now, updated_at=now)
        if _aware(row.window_started_at) <= now - dt.timedelta(seconds=seconds):
            row.attempts = 0
            row.window_started_at = now
        saturated = row.attempts >= limit
        if saturated and enforce:
            raise HTTPException(429, "요청이 많습니다. 잠시 후 다시 시도하세요")
        if not saturated:
            row.attempts += 1
        row.updated_at = now
        session.add(row)
        if commit:
            session.commit()
        else:
            session.flush()
        return saturated


def principal(session, raw_token: str, csrf: str | None = None) -> tuple[User, AuthoritySession]:
    record = session.get(AuthoritySession, token_hash(raw_token))
    if record is None or _aware(record.expires_at) <= utcnow():
        raise HTTPException(401, "세션이 만료되었습니다")
    user = session.get(User, record.user_id)
    if user is None or not user.active:
        raise HTTPException(401, "비활성 계정입니다")
    if csrf is not None and (not csrf or not hmac.compare_digest(csrf, record.csrf)):
        raise HTTPException(403, "CSRF validation failed")
    return user, record


def issue_session(session, settings, user: User) -> dict:
    with quota_allocation(session, "authority-sessions", user.id):
        raw_token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        session.execute(delete(AuthoritySession).where(AuthoritySession.expires_at <= utcnow()))
        expired = session.scalars(
            select(AuthoritySession).where(AuthoritySession.user_id == user.id)
            .order_by(AuthoritySession.created_at.desc()).offset(9)
        ).all()
        for record in expired:
            session.delete(record)
        session.add(AuthoritySession(
            token_hash=token_hash(raw_token), user_id=user.id, csrf=csrf,
            expires_at=utcnow() + dt.timedelta(hours=settings.session_hours),
        ))
        session.commit()
        return {
            "session_token": raw_token, "csrf": csrf,
            "user": {"id": user.id, "email": user.email, "display_name": user.display_name, "role": user.role},
        }


def register_member(session, settings, *, email: str, display_name: str, password: str, invite_code: str) -> dict:
    try:
        email = normalize_email(email)
        validate_password(password)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    if not 2 <= len(display_name.strip()) <= 60:
        raise HTTPException(422, "이름은 2~60자여야 합니다")
    try:
        with quota_allocation(session, "registration", "global"):
            if int(session.scalar(select(func.count()).select_from(User)) or 0) >= settings.max_users:
                raise HTTPException(409, "동아리 계정 정원이 마감되었습니다")
            if session.scalar(select(User.id).where(User.email == email)) is not None:
                raise HTTPException(409, "이미 가입된 이메일입니다")
            try:
                invitation_hash = invitation_token_hash(invite_code, settings.session_secret)
            except ValueError:
                raise HTTPException(403, "초대 코드가 올바르지 않습니다") from None
            invitation = session.scalar(select(Invitation).where(Invitation.token_hash == invitation_hash).with_for_update())
            if (
                invitation is None or invitation.redeemed_at is not None
                or _aware(invitation.expires_at) <= utcnow()
                or not hmac.compare_digest(invitation.email, email)
            ):
                raise HTTPException(403, "초대 코드가 올바르지 않습니다")
            consume_budget(session, settings, "registration", "global", settings.registration_global_attempts, 3600, commit=False)
            if not _password_slots.acquire(blocking=False):
                raise HTTPException(429, "가입 요청이 많습니다. 잠시 후 다시 시도하세요")
            try:
                encoded = hash_password(password)
            finally:
                _password_slots.release()
            user = User(email=email, display_name=display_name.strip(), password_hash=encoded, role="member", active=True)
            session.add(user)
            session.flush()
            invitation.redeemed_at = utcnow()
            invitation.redeemed_by = user.id
            return issue_session(session, settings, user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "이미 가입된 이메일입니다") from None
    except Exception:
        session.rollback()
        raise


def login_member(session, settings, *, email: str, password: str) -> dict:
    if not isinstance(password, str) or not 1 <= len(password) <= 128:
        raise HTTPException(422, "비밀번호 형식이 올바르지 않습니다")
    try:
        email = normalize_email(email)
    except ValueError:
        email = "invalid"
    consume_budget(session, settings, "login-global", "all", settings.login_global_attempts, 60)
    saturated = consume_budget(session, settings, "login-account", email, settings.login_account_attempts, settings.login_account_window_seconds, enforce=False)
    user = session.scalar(select(User).where(User.email == email))
    if not _password_slots.acquire(blocking=False):
        raise HTTPException(429, "로그인 요청이 많습니다. 잠시 후 다시 시도하세요")
    try:
        encoded = user.password_hash if user is not None else _dummy_password_hash()
        matches = verify_password(password, encoded)
        if matches and user is not None and password_needs_rehash(encoded):
            user.password_hash = hash_password(password)
    finally:
        _password_slots.release()
    if user is None or not user.active or not matches:
        raise HTTPException(429 if saturated else 401, "이메일 또는 비밀번호가 올바르지 않습니다")
    session.execute(delete(LoginThrottle).where(LoginThrottle.key_hash == _budget_key(settings, "login-account", email)))
    return issue_session(session, settings, user)


def revoke_session(session, raw_token: str, csrf: str) -> None:
    _user, record = principal(session, raw_token, csrf)
    session.delete(record)
    session.commit()


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def issue_ai_permit(session, settings, *, raw_token: str, csrf: str, prompt: str, nonce: str) -> str:
    """The service bearer alone cannot authorize a provider operation."""
    if not 5 <= len(prompt) <= 3000 or not re.fullmatch(r"[A-Za-z0-9_-]{32,64}", nonce):
        raise HTTPException(422, "요청 형식이 올바르지 않습니다")
    user, browser = principal(session, raw_token, csrf)
    with quota_allocation(session, "ai-permit", "global"):
        # Retain used nonces for the entire browser session, including expiry.
        if session.scalar(select(OperationPermit.token_hash).where(
            OperationPermit.session_hash == browser.token_hash,
            OperationPermit.operation == "shared-ai", OperationPermit.nonce == nonce,
        )):
            raise HTTPException(409, "이미 사용한 요청입니다")
        consume_budget(session, settings, "ai-member", user.id, 10, 3600, commit=False)
        consume_budget(session, settings, "ai-global", "all", settings.max_users * 10, 3600, commit=False)
        raw = secrets.token_urlsafe(32)
        session.add(OperationPermit(
            token_hash=token_hash(raw), user_id=user.id, session_hash=browser.token_hash,
            operation="shared-ai", audience="app", nonce=nonce,
            payload_hash=payload_hash({"prompt": prompt}),
            expires_at=min(_aware(browser.expires_at), utcnow() + dt.timedelta(seconds=30)),
        ))
        session.commit()
        return raw


def consume_ai_permit(session, *, raw_permit: str, prompt: str) -> str:
    with quota_allocation(session, "permit-consume", token_hash(raw_permit)):
        permit = session.scalar(select(OperationPermit).where(OperationPermit.token_hash == token_hash(raw_permit)).with_for_update())
        now = utcnow()
        browser = session.get(AuthoritySession, permit.session_hash) if permit else None
        user = session.get(User, permit.user_id) if permit else None
        if (
            permit is None or permit.consumed_at is not None or _aware(permit.expires_at) <= now
            or permit.operation != "shared-ai" or permit.audience != "app"
            or browser is None or _aware(browser.expires_at) <= now
            or user is None or not user.active or browser.user_id != user.id
            or not hmac.compare_digest(permit.payload_hash, payload_hash({"prompt": prompt}))
        ):
            raise HTTPException(403, "요청 권한이 없거나 만료되었습니다")
        permit.consumed_at = now
        session.commit()  # Never refund on provider failure or process restart.
        return user.id
