"""FastAPI surface for the temporary 30-member quant club."""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import hashlib
import hmac
import ipaddress
import json
import io
import logging
import re
import threading
import time
import tempfile
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, SecretStr, ValidationError
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.background import BackgroundTask
from fastapi.encoders import jsonable_encoder

from .ai import AiProviderError, generate_strategy, local_ai_ready
from .ai_credentials import (
    decrypt_api_key,
    encrypt_api_key,
    key_hint,
    provider_catalog,
    validate_api_key,
    validate_provider_model,
)
from .config import get_settings, member_ai_credentials_enabled
from .credential_store import credential_ciphertext_prefix
from .credential_broker_client import (
    CredentialBrokerError,
    broker_auth,
    broker_ai_catalog,
    broker_encrypt_ai,
    broker_generate_shared_strategy,
    broker_generate_strategy,
    broker_prepare_market,
    broker_preflight,
    broker_validate_ai,
    broker_validate_market,
)
from .database import (
    BacktestJob,
    AiConnection,
    EquityPoint,
    MarketDataConnection,
    MemberQuote,
    LoginThrottle,
    BrowserSession,
    Invitation,
    PaperAccount,
    PaperFill,
    PaperPosition,
    RuntimeHeartbeat,
    SessionLocal,
    Strategy,
    User,
    acquire_transaction_lock,
    bind_runtime_context,
    prepare_runtime_database,
    quota_allocation,
    invitation_token_hash,
    utcnow,
)
from .dashboard_views import completed_session_freshness, market_overview, news_feed, sector_heatmap
from .http_security import RequestBodyLimitMiddleware
from .paper import account_snapshot, regular_market_open
from .personal_auth import local_login_enabled, local_owner, require_local_request
from .market_data_credentials import (
    MarketDataProviderError,
    credential_hint as market_credential_hint,
    decrypt_market_credential,
    encrypt_market_credential,
    provider_catalog as market_data_provider_catalog,
    validate_market_credential,
    validate_provider_environment,
    verify_connection as verify_market_data_connection,
)
from .security import (
    create_session,
    hash_password,
    normalize_email,
    parse_session,
    password_needs_rehash,
    validate_password,
    verify_password,
)
from .strategies import (
    StrategySpec,
    get_dashboard_dataset,
    get_dataset_summary,
    strategy_code_preview,
)


settings = get_settings()
logger = logging.getLogger("cloud_app.main")
_DUMMY_PASSWORD_HASH = hash_password("milkyway-invalid-login-placeholder")
_local_ai_slots = threading.BoundedSemaphore(settings.local_ai_max_concurrent_requests)
_market_data_verification_slots = threading.BoundedSemaphore(2)
_password_slots = threading.BoundedSemaphore(settings.password_max_concurrent_requests)
STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title=settings.app_name, docs_url=None if settings.production else "/docs")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
app.add_middleware(
    RequestBodyLimitMiddleware,
    max_bytes=settings.max_request_body_bytes,
    read_timeout_seconds=settings.request_body_read_timeout_seconds,
    max_messages=settings.max_request_body_messages,
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _broker_enabled() -> bool:
    return getattr(settings, "credential_backend", "local") == "broker"


def _member_api(method: str, path: str, *, market: bool = False, **kwargs):
    """Register member AI and market operations according to their own modes."""

    enabled = settings.member_credentials_enabled if market else member_ai_credentials_enabled(settings)
    if enabled and not settings.authority_enabled:
        return getattr(app, method)(path, **kwargs)

    def disabled_route(function):
        return function

    return disabled_route


class RegisterBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=2, max_length=60)
    password: str = Field(min_length=10, max_length=128)
    invite_code: str = Field(min_length=8, max_length=256)


class LoginBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class PromptBody(BaseModel):
    prompt: str = Field(min_length=5, max_length=3000)


class AiConnectionBody(BaseModel):
    provider: str = Field(min_length=2, max_length=30)
    model: str = Field(min_length=2, max_length=100)
    api_key: SecretStr | None = None


class MarketDataConnectionBody(BaseModel):
    provider: str = Field(min_length=2, max_length=30)
    environment: str = Field(min_length=2, max_length=20)
    api_key: SecretStr | None = None
    api_secret: SecretStr | None = None
    personal_use_only: bool = False


class StrategyBody(BaseModel):
    spec: StrategySpec
    original_prompt: str = Field(default="", max_length=3000)


class BacktestBody(BaseModel):
    strategy_id: str
    start_date: dt.date
    end_date: dt.date
    bias_mode: str = "strict"


class AccountBody(BaseModel):
    strategy_id: str
    name: str = Field(min_length=2, max_length=100)
    session_date: dt.date | None = None


class StatusBody(BaseModel):
    status: str


_attempt_lock = threading.Lock()
_attempts: dict[str, deque[float]] = defaultdict(deque)
_attempt_windows: dict[str, int] = {}
_max_rate_limit_keys = max(1024, settings.max_users * 100)
_stream_lock = threading.Lock()
_stream_counts: dict[str, int] = defaultdict(int)
_stream_total = 0


def _rate_limit(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    with _attempt_lock:
        if key not in _attempts and len(_attempts) >= _max_rate_limit_keys:
            for stale_key, values in list(_attempts.items()):
                window = _attempt_windows.get(stale_key, 3600)
                while values and values[0] < now - window:
                    values.popleft()
                if not values:
                    _attempts.pop(stale_key, None)
                    _attempt_windows.pop(stale_key, None)
            if len(_attempts) >= _max_rate_limit_keys:
                oldest = min(
                    _attempts,
                    key=lambda candidate: (
                        _attempts[candidate][-1] if _attempts[candidate] else float("-inf")
                    ),
                )
                _attempts.pop(oldest, None)
                _attempt_windows.pop(oldest, None)
        bucket = _attempts[key]
        _attempt_windows[key] = int(window_seconds)
        while bucket and bucket[0] < now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
        bucket.append(now)


def _client_rate_identity(value: str) -> str:
    """Bound IPv6 privacy-address churn while retaining distinct IPv4 clients."""

    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return "unknown"
    if isinstance(address, ipaddress.IPv6Address):
        return str(ipaddress.ip_network("{}/64".format(address), strict=False))
    return address.compressed


def _login_budget_key(kind: str, value: str) -> str:
    return hmac.new(
        settings.session_secret.encode("utf-8"),
        ("login-budget\0" + kind + "\0" + value).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _consume_login_budget(
    session: Session,
    kind: str,
    value: str,
    limit: int,
    window_seconds: int,
    *,
    enforce: bool = True,
    commit: bool = True,
) -> bool:
    """Persist an admission decision before password verification runs."""

    key_hash = _login_budget_key(kind, value)
    now = utcnow()
    with quota_allocation(session, "login-throttle", key_hash):
        if kind == "global":
            session.execute(
                delete(LoginThrottle).where(
                    LoginThrottle.updated_at
                    < now
                    - dt.timedelta(
                        seconds=max(120, settings.login_account_window_seconds * 2)
                    )
                )
            )
        row = session.get(LoginThrottle, key_hash)
        if row is None:
            row = LoginThrottle(
                key_hash=key_hash,
                bucket_kind=kind,
                attempts=0,
                window_started_at=now,
                updated_at=now,
            )
        started = row.window_started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=dt.timezone.utc)
        if started <= now - dt.timedelta(seconds=window_seconds):
            row.attempts = 0
            row.window_started_at = now
        saturated = row.attempts >= limit
        if saturated and enforce:
            session.rollback()
            raise HTTPException(
                status_code=429,
                detail="로그인 요청이 많습니다. 잠시 후 다시 시도하세요.",
            )
        if not saturated:
            row.attempts += 1
        row.updated_at = now
        session.add(row)
        if commit:
            session.commit()
        else:
            session.flush()
        return saturated


def _acquire_stream(user_id: str) -> bool:
    global _stream_total
    with _stream_lock:
        if _stream_total >= settings.max_streams_total:
            return False
        if _stream_counts[user_id] >= settings.max_streams_per_user:
            return False
        _stream_counts[user_id] += 1
        _stream_total += 1
        return True


def _release_stream(user_id: str) -> None:
    global _stream_total
    with _stream_lock:
        if _stream_counts.get(user_id, 0) <= 0:
            return
        _stream_counts[user_id] -= 1
        if _stream_counts[user_id] == 0:
            _stream_counts.pop(user_id, None)
        _stream_total = max(0, _stream_total - 1)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _authenticate_request(request: Request, session: Session) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    if settings.authority_enabled:
        if not isinstance(token, str) or len(token) != 43:
            raise HTTPException(401, "세션이 만료되었습니다")
        bind_runtime_context(session, auth_token=token)
        row = session.execute(text("SELECT * FROM milkyway_private.principal()")).mappings().one_or_none()
        if row is None:
            raise HTTPException(401, "세션이 만료되었습니다")
        request.state.session_payload = {"sub": row["user_id"], "csrf": row["csrf"], "role": row["role"]}
        # Construct a detached public identity. The app has no users-table grant.
        return User(id=row["user_id"], email=row["email"], display_name=row["display_name"], role=row["role"], active=True)
    try:
        payload = parse_session(token, settings.session_secret)
    except ValueError:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")
    user = session.get(User, payload["sub"])
    if user is None or not user.active:
        raise HTTPException(status_code=401, detail="비활성 계정입니다")
    session_id = str(payload.get("jti", ""))
    if not session_id:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")
    token_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    browser_session = session.get(BrowserSession, token_hash)
    if browser_session is None or browser_session.user_id != user.id:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")
    expires_at = browser_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=dt.timezone.utc)
    if expires_at <= utcnow():
        session.delete(browser_session)
        session.commit()
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")
    request.state.session_payload = payload
    request.state.browser_session = browser_session
    return user


def current_user(request: Request, session: Session = Depends(get_db)) -> User:
    return _authenticate_request(request, session)


@dataclass(frozen=True)
class StreamPrincipal:
    user_id: str


def stream_principal(request: Request) -> StreamPrincipal:
    """Authenticate an SSE request without retaining a pooled DB connection."""

    session = SessionLocal()
    try:
        return StreamPrincipal(user_id=_authenticate_request(request, session).id)
    finally:
        session.close()


def csrf_guard(request: Request, user: User = Depends(current_user)) -> User:
    supplied = request.headers.get("X-CSRF-Token", "")
    expected = request.state.session_payload.get("csrf", "")
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="CSRF validation failed")
    return user


def _set_session(response: Response, user: User, session: Session) -> str:
    token, csrf = create_session(user.id, user.role, settings.session_secret, settings.session_hours)
    payload = parse_session(token, settings.session_secret)
    token_hash = hashlib.sha256(payload["jti"].encode("utf-8")).hexdigest()
    session.execute(delete(BrowserSession).where(BrowserSession.expires_at <= utcnow()))
    stale_user_sessions = session.scalars(
        select(BrowserSession)
        .where(BrowserSession.user_id == user.id)
        .order_by(BrowserSession.created_at.desc())
        .offset(9)
    ).all()
    for stale_session in stale_user_sessions:
        session.delete(stale_session)
    session.add(
        BrowserSession(
            token_hash=token_hash,
            user_id=user.id,
            expires_at=dt.datetime.fromtimestamp(payload["exp"], tz=dt.timezone.utc),
        )
    )
    session.commit()
    response.set_cookie(
        "session",
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.production,
        samesite="strict",
        path="/",
    )
    return csrf


def _owned_strategy(session: Session, user: User, strategy_id: str) -> Strategy:
    row = session.scalar(
        select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user.id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    return row


def _migrate_legacy_credentials() -> None:
    """Upgrade local ciphertext, or reject records needing offline KMS migration."""

    if settings.authority_enabled or not settings.member_credentials_enabled:
        return
    session = SessionLocal()
    changed = False
    try:
        target_prefix = credential_ciphertext_prefix(settings)
        ai_rows = session.scalars(select(AiConnection)).all() if member_ai_credentials_enabled(settings) else ()
        for row in ai_rows:
            if row.provider == "local" or not row.encrypted_api_key:
                continue
            if row.encrypted_api_key.startswith(target_prefix):
                if _broker_enabled():
                    broker_validate_ai(
                        settings,
                        owner_id=row.user_id,
                        provider=row.provider,
                        ciphertext=row.encrypted_api_key,
                    )
                elif target_prefix != "v2:":
                    validate_api_key(
                        decrypt_api_key(
                            row.encrypted_api_key,
                            settings,
                            owner_id=row.user_id,
                            provider=row.provider,
                        )
                    )
                continue
            if not row.encrypted_api_key.startswith(target_prefix):
                if target_prefix != "v2:":
                    raise RuntimeError(
                        "Stored AI credentials require the offline OCI KMS migration command"
                    )
                plaintext = decrypt_api_key(
                    row.encrypted_api_key,
                    settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                )
                row.encrypted_api_key = encrypt_api_key(
                    plaintext,
                    settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                )
                changed = True
        for row in session.scalars(select(MarketDataConnection)).all():
            if row.encrypted_api_key.startswith(target_prefix):
                if _broker_enabled():
                    pass
                elif target_prefix != "v2:":
                    validate_market_credential(
                        decrypt_market_credential(
                            row.encrypted_api_key,
                            settings,
                            owner_id=row.user_id,
                            provider=row.provider,
                            environment=row.environment,
                            label="App Key",
                        ),
                        "App Key",
                    )
            else:
                if target_prefix != "v2:":
                    raise RuntimeError(
                        "Stored market credentials require the offline OCI KMS migration command"
                    )
                plaintext_key = decrypt_market_credential(
                    row.encrypted_api_key,
                    settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                    environment=row.environment,
                    label="App Key",
                )
                row.encrypted_api_key = encrypt_market_credential(
                    plaintext_key,
                    "App Key",
                    settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                    environment=row.environment,
                )
                changed = True
            if row.encrypted_api_secret.startswith(target_prefix):
                if _broker_enabled():
                    broker_validate_market(
                        settings,
                        owner_id=row.user_id,
                        provider=row.provider,
                        environment=row.environment,
                        encrypted_api_key=row.encrypted_api_key,
                        encrypted_api_secret=row.encrypted_api_secret,
                    )
                elif target_prefix != "v2:":
                    validate_market_credential(
                        decrypt_market_credential(
                            row.encrypted_api_secret,
                            settings,
                            owner_id=row.user_id,
                            provider=row.provider,
                            environment=row.environment,
                            label="App Secret",
                        ),
                        "App Secret",
                    )
            else:
                if target_prefix != "v2:":
                    raise RuntimeError(
                        "Stored market credentials require the offline OCI KMS migration command"
                    )
                plaintext_secret = decrypt_market_credential(
                    row.encrypted_api_secret,
                    settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                    environment=row.environment,
                    label="App Secret",
                )
                row.encrypted_api_secret = encrypt_market_credential(
                    plaintext_secret,
                    "App Secret",
                    settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                    environment=row.environment,
                )
                changed = True
        if changed:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.on_event("startup")
def startup() -> None:
    errors = settings.startup_errors("app")
    if errors:
        raise RuntimeError("Startup configuration failed: " + "; ".join(errors))
    prepare_runtime_database()
    if settings.personal_local_mode and not settings.production:
        from .company_entities import bootstrap, seed_research
        bootstrap(settings)
        seed_research(settings)
    if _broker_enabled():
        broker_preflight(settings, "app")
    _migrate_legacy_credentials()
    if not settings.personal_local_mode:
        get_dataset_summary(settings)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if settings.production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/api/config")
def public_config():
    return {"personal_local_mode": settings.personal_local_mode,
            "local_auto_login": local_login_enabled(settings),
            "local_demo_data": settings.local_demo_data,
            "quote_interval_seconds": settings.quote_interval_seconds}


@app.get("/health/startup")
def startup_ready(session: Session = Depends(get_db)):
    session.execute(text("SELECT 1"))
    return {"status": "ready", "scope": "web_and_database"}


def _worker_payload(session: Session, component: str) -> dict:
    row = session.get(RuntimeHeartbeat, component)
    observed = row.observed_at if row else None
    if observed is not None and observed.tzinfo is None:
        observed = observed.replace(tzinfo=dt.timezone.utc)
    return {"instance_id": row.instance_id if row else None,
            "observed_at": observed, "detail": row.detail if row else "not started",
            "error": bool(row and row.detail.startswith("error=")),
            "alive": bool(observed and observed >= utcnow() - dt.timedelta(seconds=settings.worker_stale_seconds))}


@app.get("/health/ready")
def ready(session: Session = Depends(get_db)):
    details = {
        "database": False,
        "dataset": False,
        "data_gate": False,
        "demo_data": settings.local_demo_data,
        "worker": False,
    }
    try:
        session.execute(text("SELECT 1"))
        details["database"] = True
        if settings.personal_local_mode:
            from .personal_data import personal_data_status
            data = personal_data_status(settings)
            details["dataset"] = bool(data.get("ready"))
            details["data_gate"] = bool(data.get("ready") and not data.get("stale"))
        else:
            summary = get_dataset_summary(settings)
            details["dataset"] = summary.symbol_count > 0
            details["data_gate"] = summary.forward_data_gate_ready
        heartbeat = session.get(RuntimeHeartbeat, "paper-worker")
        if heartbeat:
            observed = heartbeat.observed_at
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=dt.timezone.utc)
            details["worker"] = observed >= utcnow() - dt.timedelta(seconds=settings.worker_stale_seconds)
    except Exception as exc:
        logger.warning("readiness component check failed error=%s", type(exc).__name__)
        details["error"] = "component check failed"
    # The deterministic local dataset intentionally has no point-in-time data
    # certification. It is nevertheless a ready development sandbox; strict
    # backtests remain unavailable because ``data_gate`` stays false.
    details["backtest_worker"] = _worker_payload(session, "backtest-worker")["alive"]
    details["personal_data_worker"] = (not settings.personal_local_mode or _worker_payload(session, "personal-data")["alive"])
    # Local Compose depends on /health/startup; it can therefore require its
    # independently running workers here without creating a dependency cycle.
    # Keep the separately governed cloud readiness contract unchanged.
    workers_ok = not (settings.personal_local_mode or settings.local_demo_data) or (
        details["worker"] and details["backtest_worker"] and details["personal_data_worker"]
    )
    ok = details["database"] and workers_ok and (
        settings.personal_local_mode or (details["dataset"] and (details["data_gate"] or settings.local_demo_data))
    )
    return JSONResponse({"status": "ready" if ok else "not_ready", "components": details}, status_code=200 if ok else 503)


@app.post("/api/auth/local")
def local_login(request: Request, response: Response, session: Session = Depends(get_db)):
    require_local_request(request, settings)
    # Serialize initial creation and session issuance across concurrent tabs.
    with quota_allocation(session, "local-session", "global"):
        user = local_owner(session)
        try:
            authenticated = _authenticate_request(request, session)
        except HTTPException as exc:
            if exc.status_code != 401:
                raise
            authenticated = None
        if authenticated is not None and authenticated.id == user.id:
            csrf = request.state.session_payload["csrf"]
        else:
            csrf = _set_session(response, user, session)
        return {"id": user.id, "email": user.email, "display_name": user.display_name,
                "role": user.role, "csrf": csrf}


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterBody, request: Request, response: Response, session: Session = Depends(get_db)):
    source = _client_rate_identity(request.client.host if request.client else "unknown")
    _rate_limit("register:" + source, 5, 3600)
    if settings.authority_enabled:
        return _authority_login_response(response, "register", body.model_dump())
    try:
        email = normalize_email(body.email)
        validate_password(body.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    try:
        with quota_allocation(session, "registration", "global"):
            user_count = int(session.scalar(select(func.count()).select_from(User)) or 0)
            if user_count >= settings.max_users:
                raise HTTPException(status_code=409, detail="동아리 계정 정원이 마감되었습니다")
            if session.scalar(select(User.id).where(User.email == email)) is not None:
                raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다")

            invitation = None
            legacy_allowed = settings.legacy_invite_enabled and hmac.compare_digest(
                body.invite_code, settings.invite_code
            )
            if not legacy_allowed:
                try:
                    token_hash = invitation_token_hash(
                        body.invite_code, settings.session_secret
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=403, detail="초대 코드가 올바르지 않습니다"
                    ) from None
                statement = select(Invitation).where(
                    Invitation.token_hash == token_hash
                )
                if session.bind.dialect.name == "postgresql":
                    statement = statement.with_for_update()
                invitation = session.scalar(statement)
                if invitation is None:
                    raise HTTPException(
                        status_code=403, detail="초대 코드가 올바르지 않습니다"
                    )
                expires_at = invitation.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=dt.timezone.utc)
                if (
                    invitation.redeemed_at is not None
                    or expires_at <= utcnow()
                    or not hmac.compare_digest(invitation.email, email)
                ):
                    raise HTTPException(
                        status_code=403, detail="초대 코드가 올바르지 않습니다"
                    )

            _consume_login_budget(
                session,
                "registration",
                "all-registration-attempts",
                settings.registration_global_attempts,
                3600,
                commit=False,
            )

            acquired = _password_slots.acquire(blocking=False)
            if not acquired:
                raise HTTPException(
                    status_code=429,
                    detail="가입 요청이 많습니다. 잠시 후 다시 시도하세요.",
                )
            try:
                encoded_password = hash_password(body.password)
            finally:
                _password_slots.release()
            user = User(
                email=email,
                display_name=body.display_name.strip(),
                password_hash=encoded_password,
                role="member",
            )
            session.add(user)
            session.flush()
            if invitation is not None:
                invitation.redeemed_at = utcnow()
                invitation.redeemed_by = user.id
            session.commit()
    except HTTPException:
        session.rollback()
        raise
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다")
    csrf = _set_session(response, user, session)
    return {"user": {"id": user.id, "email": user.email, "display_name": user.display_name}, "csrf": csrf}


@app.post("/api/auth/login")
def login(body: LoginBody, request: Request, response: Response, session: Session = Depends(get_db)):
    key = "login:" + _client_rate_identity(
        request.client.host if request.client else "unknown"
    )
    _rate_limit(key, 10, 600)
    if settings.authority_enabled:
        return _authority_login_response(response, "login", body.model_dump())
    try:
        email = normalize_email(body.email)
    except ValueError:
        email = "invalid"
    _consume_login_budget(
        session,
        "global",
        "all-login-attempts",
        settings.login_global_attempts,
        60,
    )
    account_saturated = _consume_login_budget(
        session,
        "account",
        email,
        settings.login_account_attempts,
        settings.login_account_window_seconds,
        enforce=False,
    )
    user = session.scalar(select(User).where(User.email == email))
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    acquired = _password_slots.acquire(blocking=False)
    if not acquired:
        raise HTTPException(status_code=429, detail="로그인 요청이 많습니다. 잠시 후 다시 시도하세요.")
    try:
        password_matches = verify_password(body.password, password_hash)
        replacement_hash = (
            hash_password(body.password)
            if password_matches and password_needs_rehash(password_hash)
            else None
        )
    finally:
        _password_slots.release()
    if user is None or not password_matches or not user.active:
        if account_saturated is True:
            raise HTTPException(
                status_code=429,
                detail="로그인 요청이 많습니다. 잠시 후 다시 시도하세요.",
            )
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
    if replacement_hash is not None:
        user.password_hash = replacement_hash
    session.execute(
        delete(LoginThrottle).where(
            LoginThrottle.key_hash == _login_budget_key("account", email)
        )
    )
    csrf = _set_session(response, user, session)
    return {"user": {"id": user.id, "email": user.email, "display_name": user.display_name}, "csrf": csrf}


@app.post("/api/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    _user: User = Depends(csrf_guard),
    session: Session = Depends(get_db),
):
    if settings.authority_enabled:
        try:
            broker_auth(settings, "logout", {"session_token": request.cookies.get("session", ""), "csrf": request.headers.get("X-CSRF-Token", "")})
        except CredentialBrokerError as exc:
            raise HTTPException(exc.status_code, exc.detail) from None
    browser_session = getattr(request.state, "browser_session", None)
    if browser_session is not None:
        session.delete(browser_session)
        session.commit()
    response.delete_cookie("session", path="/")


@app.get("/api/auth/me")
def me(request: Request, user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "csrf": request.state.session_payload["csrf"],
    }


def _authority_login_response(response: Response, operation: str, payload: dict) -> dict:
    try:
        result = broker_auth(settings, operation, payload)
    except CredentialBrokerError as exc:
        raise HTTPException(exc.status_code, exc.detail) from None
    token = result.pop("session_token", None)
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise HTTPException(503, "인증 서비스 응답이 올바르지 않습니다")
    response.set_cookie("session", token, max_age=settings.session_hours * 3600,
                        httponly=True, secure=settings.production, samesite="strict", path="/")
    return result


def _ai_connection_payload(row: AiConnection | None) -> dict:
    if _broker_enabled():
        try:
            catalog = broker_ai_catalog(settings)
        except CredentialBrokerError:
            logger.warning("shared AI status probe unavailable")
            catalog = []
    else:
        local_ready = settings.local_ai_enabled and local_ai_ready(
            base_url=settings.local_ai_base_url,
            model=settings.local_ai_model,
            api_key=settings.local_ai_api_key,
        )
        catalog = provider_catalog(settings, local_ready=local_ready)
    if not member_ai_credentials_enabled(settings):
        entry = catalog[0] if catalog else {}
        available = bool(entry.get("available") and entry.get("ready"))
        configured = bool(settings.shared_ai_enabled)
        return {
            "connected": configured,
            "configured": configured,
            "available": available,
            "provider": entry.get("id", settings.shared_ai_provider),
            "model": entry.get("default_model", settings.shared_ai_model),
            "provider_verified": bool(entry.get("provider_verified", False)),
            "key_hint": None,
            "updated_at": None,
            "providers": catalog,
            "management": "club_server",
        }
    availability = {item["id"]: item["available"] and item["ready"] for item in catalog}
    configured = row is not None
    available = configured and availability.get(row.provider, False)
    return {
        "connected": bool(available),
        "configured": configured,
        "available": bool(available),
        "provider": row.provider if row else None,
        "model": row.model if row else None,
        "key_hint": row.key_hint if row else None,
        "updated_at": row.updated_at if row else None,
        "providers": catalog,
    }


@app.get("/api/me/ai-connection")
def get_ai_connection(user: User = Depends(current_user), session: Session = Depends(get_db)):
    if settings.personal_local_mode:
        from .research_ai import configuration_status
        return configuration_status(settings)
    row = session.get(AiConnection, user.id) if member_ai_credentials_enabled(settings) else None
    return _ai_connection_payload(row)


@_member_api("put", "/api/me/ai-connection")
def put_ai_connection(
    body: AiConnectionBody,
    user: User = Depends(csrf_guard),
    session: Session = Depends(get_db),
):
    _rate_limit("ai-connection:" + user.id, 20, 3600)
    try:
        provider, model = validate_provider_model(body.provider, body.model)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    row = session.get(AiConnection, user.id)
    supplied_key = body.api_key.get_secret_value() if body.api_key else ""
    if provider == "local":
        if _broker_enabled():
            try:
                local_entry = next(
                    item for item in broker_ai_catalog(settings) if item.get("id") == "local"
                )
            except (CredentialBrokerError, StopIteration) as exc:
                detail = exc.detail if isinstance(exc, CredentialBrokerError) else "로컬 AI 공급자 정보가 없습니다"
                status_code = exc.status_code if isinstance(exc, CredentialBrokerError) else 503
                raise HTTPException(status_code=status_code, detail=detail)
            local_enabled = bool(local_entry.get("available"))
            model = str(local_entry.get("default_model") or model)
        else:
            local_enabled = settings.local_ai_enabled
            model = settings.local_ai_model
        if not local_enabled:
            raise HTTPException(status_code=503, detail="서버 관리자가 로컬 AI를 먼저 활성화해야 합니다")
        encrypted_key = ""
        hint = "서버 관리"
    elif not supplied_key and (row is None or row.provider != provider):
        raise HTTPException(status_code=422, detail="새 AI 공급자를 연결하려면 API 키를 입력해 주세요")
    elif supplied_key:
        try:
            if _broker_enabled():
                encrypted_key, hint = broker_encrypt_ai(
                    settings,
                    owner_id=user.id,
                    provider=provider,
                    api_key=supplied_key,
                )
            else:
                encrypted_key = encrypt_api_key(
                    supplied_key, settings, owner_id=user.id, provider=provider
                )
                hint = key_hint(supplied_key)
        except CredentialBrokerError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    else:
        encrypted_key = row.encrypted_api_key
        hint = row.key_hint
    if row is None:
        row = AiConnection(
            user_id=user.id,
            provider=provider,
            model=model,
            encrypted_api_key=encrypted_key,
            key_hint=hint,
        )
    else:
        row.provider = provider
        row.model = model
        row.encrypted_api_key = encrypted_key
        row.key_hint = hint
        row.updated_at = utcnow()
    session.add(row)
    session.commit()
    return _ai_connection_payload(row)


@_member_api("delete", "/api/me/ai-connection", status_code=204)
def delete_ai_connection(user: User = Depends(csrf_guard), session: Session = Depends(get_db)):
    row = session.get(AiConnection, user.id)
    if row is not None:
        session.delete(row)
        session.commit()


def _market_data_connection_payload(row: MarketDataConnection | None) -> dict:
    if not settings.member_credentials_enabled:
        shared = settings.quote_provider == "kis" and settings.market_data_sharing_allowed
        return {
            "connected": shared,
            "configured": settings.quote_provider == "kis",
            "provider": settings.quote_provider,
            "environment": settings.kis_environment if settings.quote_provider == "kis" else None,
            "key_hint": None,
            "secret_hint": None,
            "verified_at": None,
            "verification_status": "worker_managed" if shared else "not_configured",
            "updated_at": None,
            "providers": [],
            "usage_scope": "shared_club_feed",
            "management": "club_server",
            "transport": "rest_polling" if settings.quote_provider == "kis" else "dataset",
        }
    return {
        "connected": row is not None,
        "configured": row is not None,
        "provider": row.provider if row else None,
        "environment": row.environment if row else None,
        "key_hint": row.key_hint if row else None,
        "secret_hint": row.secret_hint if row else None,
        "verified_at": row.verified_at if row else None,
        "verification_status": "last_success" if row else "not_configured",
        "updated_at": row.updated_at if row else None,
        "providers": market_data_provider_catalog(),
        "usage_scope": "personal_paper_only",
        "management": "credential_broker" if settings.authority_enabled else "member",
        "management_url": settings.credential_broker_url + "/credentials" if settings.authority_enabled else None,
    }


def _market_data_connection_version(row: MarketDataConnection | None) -> str | None:
    if row is None:
        return None
    return "{}:{}:{}".format(row.provider, row.environment, row.updated_at.isoformat())


@app.get("/api/me/market-data-connection")
def get_market_data_connection(
    user: User = Depends(current_user), session: Session = Depends(get_db)
):
    row = (
        session.get(MarketDataConnection, user.id)
        if settings.member_credentials_enabled
        else None
    )
    return _market_data_connection_payload(row)


@_member_api("put", "/api/me/market-data-connection", market=True)
def put_market_data_connection(
    body: MarketDataConnectionBody,
    user: User = Depends(csrf_guard),
    session: Session = Depends(get_db),
):
    _rate_limit("market-data-connection:" + user.id, 10, 3600)
    if not body.personal_use_only:
        raise HTTPException(
            status_code=422,
            detail="개인 페이퍼 트레이딩 용도 확인이 필요합니다",
        )
    try:
        provider, environment = validate_provider_environment(body.provider, body.environment)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    row = session.get(MarketDataConnection, user.id)
    expected_version = _market_data_connection_version(row)
    supplied_key = body.api_key.get_secret_value() if body.api_key else ""
    supplied_secret = body.api_secret.get_secret_value() if body.api_secret else ""
    same_provider = row is not None and row.provider == provider
    prepared = None
    if _broker_enabled():
        try:
            prepared = broker_prepare_market(
                settings,
                owner_id=user.id,
                provider=provider,
                environment=environment,
                api_key=supplied_key,
                api_secret=supplied_secret,
                current_provider=row.provider if same_provider else None,
                current_environment=row.environment if same_provider else None,
                current_encrypted_api_key=row.encrypted_api_key if same_provider else None,
                current_encrypted_api_secret=row.encrypted_api_secret if same_provider else None,
            )
        except CredentialBrokerError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    else:
        try:
            if supplied_key:
                api_key = validate_market_credential(supplied_key, "App Key")
            elif same_provider:
                api_key = decrypt_market_credential(
                    row.encrypted_api_key,
                    settings,
                    owner_id=user.id,
                    provider=row.provider,
                    environment=row.environment,
                    label="App Key",
                )
            else:
                raise ValueError("새 시세 공급자를 연결하려면 App Key를 입력해 주세요")
            if supplied_secret:
                api_secret = validate_market_credential(supplied_secret, "App Secret")
            elif same_provider:
                api_secret = decrypt_market_credential(
                    row.encrypted_api_secret,
                    settings,
                    owner_id=user.id,
                    provider=row.provider,
                    environment=row.environment,
                    label="App Secret",
                )
            else:
                raise ValueError("새 시세 공급자를 연결하려면 App Secret을 입력해 주세요")
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        verification_slot = _market_data_verification_slots.acquire(blocking=False)
        if not verification_slot:
            raise HTTPException(
                status_code=429,
                detail="시세 API 인증 요청이 많습니다. 잠시 후 다시 시도해 주세요",
            )
        try:
            verify_market_data_connection(provider, environment, api_key, api_secret)
        except MarketDataProviderError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        finally:
            _market_data_verification_slots.release()

    # Authentication is network I/O and stays outside the transaction lock.
    # The advisory lock does not require paper-worker UPDATE rights on the
    # credential row and remains held until commit/rollback.
    acquire_transaction_lock(session, "market-connection", user.id)
    locked_row = session.scalar(
        select(MarketDataConnection)
        .where(MarketDataConnection.user_id == user.id)
        .execution_options(populate_existing=True)
    )
    if _market_data_connection_version(locked_row) != expected_version:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="시세 API 설정이 다른 요청에서 변경됐습니다. 다시 시도해 주세요",
        )
    row = locked_row

    # Always bind fresh ciphertext to the selected provider/environment. This
    # also safely rebinds retained credentials when only the environment changes.
    if prepared is not None:
        encrypted_key = prepared["encrypted_api_key"]
        encrypted_secret = prepared["encrypted_api_secret"]
        key_value_hint = prepared["key_hint"]
        secret_value_hint = prepared["secret_hint"]
    else:
        encrypted_key = encrypt_market_credential(
            api_key,
            "App Key",
            settings,
            owner_id=user.id,
            provider=provider,
            environment=environment,
        )
        encrypted_secret = encrypt_market_credential(
            api_secret,
            "App Secret",
            settings,
            owner_id=user.id,
            provider=provider,
            environment=environment,
        )
        key_value_hint = market_credential_hint(api_key)
        secret_value_hint = market_credential_hint(api_secret)
    verified_at = utcnow()
    if row is None:
        row = MarketDataConnection(
            user_id=user.id,
            provider=provider,
            environment=environment,
            encrypted_api_key=encrypted_key,
            encrypted_api_secret=encrypted_secret,
            key_hint=key_value_hint,
            secret_hint=secret_value_hint,
            verified_at=verified_at,
        )
    else:
        row.provider = provider
        row.environment = environment
        row.encrypted_api_key = encrypted_key
        row.encrypted_api_secret = encrypted_secret
        row.key_hint = key_value_hint
        row.secret_hint = secret_value_hint
        row.verified_at = verified_at
        row.updated_at = verified_at
    # A reverified or replaced connection must never inherit a quote collected
    # under the previous credential/environment.
    session.execute(delete(MemberQuote).where(MemberQuote.user_id == user.id))
    session.add(row)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="시세 API 설정이 동시에 생성됐습니다. 다시 시도해 주세요",
        ) from exc
    return _market_data_connection_payload(row)


@_member_api("delete", "/api/me/market-data-connection", market=True, status_code=204)
def delete_market_data_connection(
    user: User = Depends(csrf_guard), session: Session = Depends(get_db)
):
    acquire_transaction_lock(session, "market-connection", user.id)
    row = session.scalar(
        select(MarketDataConnection)
        .where(MarketDataConnection.user_id == user.id)
        .execution_options(populate_existing=True)
    )
    if row is not None:
        session.execute(delete(MemberQuote).where(MemberQuote.user_id == user.id))
        session.delete(row)
        session.commit()


def _strategy_payload(row: Strategy) -> dict:
    spec = StrategySpec.model_validate_json(row.spec_json)
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "spec": spec.model_dump(mode="json"),
        "code_preview": strategy_code_preview(spec),
        "created_at": row.created_at,
    }


@app.get("/api/strategies")
def list_strategies(user: User = Depends(current_user), session: Session = Depends(get_db)):
    rows = session.scalars(
        select(Strategy).where(Strategy.user_id == user.id).order_by(Strategy.created_at.desc())
    ).all()
    return [_strategy_payload(row) for row in rows]


@contextmanager
def _strategy_creation(session: Session, user: User, spec: StrategySpec, prompt: str):
    if spec.universe == "us_all" and not settings.personal_local_mode:
        raise HTTPException(status_code=422, detail="전체 미국 종목 자동 선정은 개인 로컬 모드에서 지원합니다")
    if spec.symbols and not settings.personal_local_mode:
        raise HTTPException(status_code=422, detail="직접 종목 지정은 개인 로컬 모드에서만 지원합니다")
    if settings.personal_local_mode:
        if spec.universe == "selected" and not spec.symbols:
            raise HTTPException(status_code=422, detail="미국 전체 자동 선정을 선택하거나 직접 지정할 티커를 입력하세요")
        if spec.universe == "selected" and spec.portfolio.max_positions > len(spec.symbols):
            raise HTTPException(status_code=422, detail="최대 보유 종목 수는 선택한 티커 수 이하여야 합니다")
    with quota_allocation(session, "strategies", user.id):
        if settings.personal_local_mode:
            existing = session.scalars(select(Strategy).where(Strategy.user_id == user.id)).all()
            universe = set(spec.symbols)
            for saved in existing:
                universe.update(StrategySpec.model_validate_json(saved.spec_json).symbols)
            if len(universe) > 100:
                raise HTTPException(status_code=409, detail="이 PC의 전체 전략 티커는 최대 100개까지 저장할 수 있습니다")
        count = session.scalar(select(func.count()).select_from(Strategy).where(Strategy.user_id == user.id))
        if int(count or 0) >= settings.max_strategies_per_user:
            raise HTTPException(status_code=409, detail="사용자별 전략 수 한도를 초과했습니다")
        row = Strategy(
            user_id=user.id,
            name=spec.name,
            description=spec.description,
            original_prompt=prompt,
            spec_json=spec.model_dump_json(),
        )
        session.add(row)
        session.flush()
        yield row
        session.commit()


def _save_strategy(session: Session, user: User, spec: StrategySpec, prompt: str) -> Strategy:
    with _strategy_creation(session, user, spec, prompt) as row:
        return row


@app.post("/api/strategies/generate", status_code=201)
def ai_strategy(body: PromptBody, user: User = Depends(csrf_guard), session: Session = Depends(get_db), request: Request = None):
    if settings.personal_local_mode:
        raise HTTPException(409, "연구 채팅에서 요청 내용을 확인하고 AI 호출을 승인해 주세요")
    member_ai = member_ai_credentials_enabled(settings)
    connection = (
        session.get(AiConnection, user.id)
        if member_ai
        else None
    )
    if member_ai and connection is None:
        raise HTTPException(status_code=409, detail="설정에서 AI를 먼저 연결해 주세요")
    local_slot_acquired = False
    try:
        if not member_ai:
            if settings.authority_enabled:
                session.rollback()
            if not _broker_enabled():
                raise RuntimeError("동아리 공용 AI broker가 설정되지 않았습니다")
            _rate_limit("ai:" + user.id, 10, 3600)
            spec, _preview = broker_generate_shared_strategy(
                settings,
                prompt=body.prompt,
                **({"session_token": request.cookies.get("session", ""), "csrf": request.headers.get("X-CSRF-Token", "")} if settings.authority_enabled else {}),
            )
        elif _broker_enabled():
            _rate_limit("ai:" + user.id, 10, 3600)
            spec, _preview = broker_generate_strategy(
                settings,
                owner_id=user.id,
                provider=connection.provider,
                model=connection.model,
                ciphertext=connection.encrypted_api_key,
                prompt=body.prompt,
            )
        elif connection.provider == "local":
            if not settings.local_ai_enabled:
                raise RuntimeError("로컬 AI 서버가 비활성화되어 있습니다")
            local_slot_acquired = _local_ai_slots.acquire(blocking=False)
            if not local_slot_acquired:
                raise HTTPException(
                    status_code=429,
                    detail="로컬 AI 요청이 많습니다. 잠시 후 다시 시도해 주세요",
                )
            api_key = settings.local_ai_api_key
            model = settings.local_ai_model
            local_base_url = settings.local_ai_base_url
        else:
            api_key = decrypt_api_key(
                connection.encrypted_api_key,
                settings,
                owner_id=user.id,
                provider=connection.provider,
            )
            model = connection.model
            local_base_url = None
        if member_ai and not _broker_enabled():
            _rate_limit("ai:" + user.id, 10, 3600)
            spec, _preview = generate_strategy(
                body.prompt,
                provider=connection.provider,
                model=model,
                api_key=api_key,
                timeout_seconds=settings.ai_timeout_seconds,
                local_base_url=local_base_url,
            )
    except AiProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except CredentialBrokerError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        if local_slot_acquired:
            _local_ai_slots.release()
    return _strategy_payload(_save_strategy(session, user, spec, body.prompt))


@app.post("/api/strategies", status_code=201)
def create_strategy(body: StrategyBody, user: User = Depends(csrf_guard), session: Session = Depends(get_db)):
    return _strategy_payload(_save_strategy(session, user, body.spec, body.original_prompt))


@app.post("/api/backtests", status_code=202)
def create_backtest(body: BacktestBody, user: User = Depends(csrf_guard), session: Session = Depends(get_db)):
    strategy = _owned_strategy(session, user, body.strategy_id)
    if body.bias_mode not in {"strict", "exploratory"}:
        raise HTTPException(status_code=422, detail="bias_mode must be strict or exploratory")
    if body.start_date > body.end_date:
        raise HTTPException(status_code=422, detail="시작일은 종료일보다 늦을 수 없습니다")
    if (body.end_date - body.start_date).days > 370:
        raise HTTPException(status_code=422, detail="현재 클럽 데이터셋은 최대 1년 구간만 허용합니다")
    if settings.personal_local_mode and body.bias_mode != "exploratory":
        raise HTTPException(status_code=422, detail="개인 선택 종목 백테스트는 탐색용(exploratory)으로 실행해 주세요")
    try:
        dataset_settings = settings
        if settings.personal_local_mode and StrategySpec.model_validate_json(strategy.spec_json).universe == "us_all":
            from .auto_universe import backtest_settings, prepare_backtest_generation
            prepare_backtest_generation(settings)
            dataset_settings = backtest_settings(settings)
        summary = get_dataset_summary(dataset_settings)
    except (ValueError, FileNotFoundError, OSError):
        raise HTTPException(status_code=409, detail="전략 가격 이력을 준비 중입니다. 데이터 상태를 확인하고 잠시 후 다시 실행해 주세요")
    first_execution = dt.date.fromisoformat(summary.first_certified_execution_date)
    if body.bias_mode == "strict" and body.start_date < first_execution:
        raise HTTPException(
            status_code=422,
            detail="엄격 PIT 시작일은 첫 인증 스냅샷의 다음 거래일 {} 이후여야 합니다".format(
                summary.first_certified_execution_date
            ),
        )
    if body.end_date > summary.last_completed_session:
        raise HTTPException(
            status_code=422,
            detail="마지막 완료 세션 {}을 넘을 수 없습니다".format(
                summary.last_completed_session.isoformat()
            ),
        )
    if body.bias_mode == "strict" and not summary.forward_data_gate_ready:
        raise HTTPException(
            status_code=503,
            detail="최신 일일 데이터 품질 게이트가 통과될 때까지 엄격 PIT 백테스트를 중단합니다",
        )
    today = utcnow().date()
    with quota_allocation(session, "backtests", "global"):
        with quota_allocation(session, "backtests", user.id):
            daily_count = session.scalar(
                select(func.count()).select_from(BacktestJob).where(
                    BacktestJob.user_id == user.id,
                    BacktestJob.created_at
                    >= dt.datetime.combine(today, dt.time.min, tzinfo=dt.timezone.utc),
                )
            )
            if int(daily_count or 0) >= settings.max_backtests_per_user_day:
                raise HTTPException(status_code=429, detail="일일 백테스트 한도를 초과했습니다")
            user_outstanding = session.scalar(
                select(func.count()).select_from(BacktestJob).where(
                    BacktestJob.user_id == user.id,
                    BacktestJob.status.in_(("queued", "running")),
                )
            )
            if int(user_outstanding or 0) >= settings.max_outstanding_backtests_per_user:
                raise HTTPException(
                    status_code=429, detail="완료되지 않은 백테스트 한도를 초과했습니다"
                )
            global_outstanding = session.scalar(
                select(func.count()).select_from(BacktestJob).where(
                    BacktestJob.status.in_(("queued", "running"))
                )
            )
            if int(global_outstanding or 0) >= settings.max_outstanding_backtests_total:
                raise HTTPException(
                    status_code=429, detail="공용 백테스트 대기열이 가득 찼습니다"
                )
            job = BacktestJob(
                user_id=user.id,
                strategy_id=strategy.id,
                bias_mode=body.bias_mode,
                start_date=body.start_date,
                end_date=body.end_date,
            )
            session.add(job)
            session.commit()
    return {"id": job.id, "status": job.status}


@app.get("/api/backtests")
def list_backtests(user: User = Depends(current_user), session: Session = Depends(get_db), limit: int = 50, offset: int = 0):
    if not 1 <= limit <= 100 or offset < 0:
        raise HTTPException(status_code=422, detail="limit은 1~100, offset은 0 이상이어야 합니다")
    rows = session.scalars(
        select(BacktestJob).where(BacktestJob.user_id == user.id)
        .order_by(BacktestJob.created_at.desc(), BacktestJob.id.desc()).offset(offset).limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "strategy_id": row.strategy_id,
            "strategy_name": row.strategy.name,
            "status": row.status,
            "progress": row.progress,
            "bias_mode": row.bias_mode,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "error": row.error,
            "result": json.loads(row.result_json) if row.result_json else None,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def _ensure_shared_quote_capacity(
    session: Session, *, additional_positions: int = 0
) -> None:
    """Bound held plus rebalance-candidate demand to the freshness window."""

    if settings.quote_provider != "kis":
        return
    # Include the worker loop's mandatory one-second sleep and leave the
    # boundary second unused. quote_map() consumes the same configured age.
    effective_tick_seconds = max(
        settings.quote_interval_seconds,
        int(settings.shared_quote_tick_deadline_seconds + 0.999999),
    ) + 1
    refreshes = max(
        1,
        (settings.quote_max_age_seconds - 1) // effective_tick_seconds,
    )
    capacity = settings.shared_quote_max_symbols_per_tick * refreshes
    # Four market baselines are refreshed alongside member holdings.
    position_capacity = max(0, capacity - 4)
    active_accounts = session.scalars(
        select(PaperAccount).where(PaperAccount.status == "active")
    ).all()
    # A due account can simultaneously need quotes for every current holding
    # and a disjoint target set of the same configured size.
    reserved = 2 * sum(
        StrategySpec.model_validate_json(account.strategy.spec_json).portfolio.max_positions
        for account in active_accounts
    )
    if reserved + (2 * int(additional_positions)) > position_capacity:
        raise HTTPException(
            status_code=409,
            detail="공용 시세 freshness 용량을 초과해 새 활성 계좌를 만들 수 없습니다",
        )


def _ensure_personal_quote_capacity(session: Session, user_id: str, spec: StrategySpec, *, account_id: str | None = None) -> None:
    if not settings.personal_local_mode:
        return
    connection = session.get(MarketDataConnection, user_id)
    automatic = spec.universe == "us_all"
    held = set(session.scalars(select(PaperPosition.ticker).where(PaperPosition.account_id == account_id)).all()) if account_id else set()
    symbols = set() if automatic else set(spec.symbols) | held
    reserve = spec.portfolio.max_positions + max(len(held), spec.portfolio.max_positions) if automatic else 0
    active = session.scalars(select(PaperAccount).where(
        PaperAccount.user_id == user_id, PaperAccount.status == "active")).all()
    for account in active:
        if account.id == account_id:
            continue
        active_spec = StrategySpec.model_validate_json(account.strategy.spec_json)
        held = set(session.scalars(select(PaperPosition.ticker).where(PaperPosition.account_id == account.id)).all())
        if active_spec.universe == "us_all":
            automatic = True
            reserve += active_spec.portfolio.max_positions + max(len(held), active_spec.portfolio.max_positions)
        else:
            symbols.update(active_spec.symbols)
            symbols.update(held)
    if automatic and (connection is None or connection.provider != "toss"):
        raise HTTPException(status_code=409, detail="전체 미국 종목 자동 운용에는 토스 시세 연결이 필요합니다")
    if len(symbols) + reserve > (200 if automatic else 20):
        raise HTTPException(status_code=409, detail="활성 계좌의 체결 시세 용량을 초과했습니다. 자동 선정은 목표·보유 종목 200개, 직접 지정은 20개까지입니다")


@contextmanager
def _account_creation(body, user, session):
    strategy = _owned_strategy(session, user, body.strategy_id)
    spec = StrategySpec.model_validate_json(strategy.spec_json)
    day = getattr(body, "session_date", None)
    bounds = None
    if day is not None:
        if not settings.personal_local_mode or settings.production:
            raise HTTPException(422, "거래일 지정은 개인 로컬 모드에서만 지원합니다")
        from .paper_sessions import session_bounds
        try:
            bounds = session_bounds(day, utcnow())
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    with quota_allocation(session, "accounts", "global"):
        with quota_allocation(session, "accounts", user.id):
            count = session.scalar(
                select(func.count()).select_from(PaperAccount).where(PaperAccount.user_id == user.id)
            )
            if int(count or 0) >= settings.max_accounts_per_user:
                raise HTTPException(status_code=409, detail="사용자별 페이퍼 계좌 한도를 초과했습니다")
            _ensure_shared_quote_capacity(
                session, additional_positions=spec.portfolio.max_positions
            )
            _ensure_personal_quote_capacity(session, user.id, spec)
            row = PaperAccount(
                user_id=user.id,
                strategy_id=strategy.id,
                name=body.name.strip(),
                initial_cash=spec.portfolio.initial_cash,
                cash=spec.portfolio.initial_cash,
            )
            session.add(row)
            session.flush()
            if bounds is not None:
                from .research_models import PersonalPaperSession
                session.add(PersonalPaperSession(account_id=row.id, session_date=day,
                    opens_at=bounds[0], closes_at=bounds[1]))
                session.flush()
            yield row
            session.commit()



@app.post("/api/accounts", status_code=201)
def create_account(body: AccountBody, user: User = Depends(csrf_guard), session: Session = Depends(get_db)):
    with _account_creation(body, user, session) as row:
        pass
    return account_snapshot(session, row)


@app.get("/api/accounts")
def list_accounts(user: User = Depends(current_user), session: Session = Depends(get_db)):
    rows = session.scalars(
        select(PaperAccount).where(PaperAccount.user_id == user.id).order_by(PaperAccount.created_at)
    ).all()
    return [account_snapshot(session, row) for row in rows]


@app.patch("/api/accounts/{account_id}")
def update_account(
    account_id: str,
    body: StatusBody,
    user: User = Depends(csrf_guard),
    session: Session = Depends(get_db),
):
    if body.status not in {"active", "paused"}:
        raise HTTPException(status_code=422, detail="status must be active or paused")
    row = session.scalar(
        select(PaperAccount).where(PaperAccount.id == account_id, PaperAccount.user_id == user.id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다")
    if row.status in {"review_required", "configuration_required"}:
        raise HTTPException(
            status_code=409,
            detail="상장 이탈/corporate action 검토가 필요해 사용자가 재개할 수 없습니다",
        )
    with quota_allocation(session, "accounts", "global"):
        if settings.personal_local_mode and body.status == "active":
            from .paper_sessions import session_payload
            run = session_payload(session, row, utcnow())
            if run and (run["expired"] or run["completed_at"]):
                raise HTTPException(409, "지정한 거래일이 종료되었습니다. 새 페이퍼 계좌를 만들어 주세요")
        if row.status != "active" and body.status == "active":
            spec = StrategySpec.model_validate_json(row.strategy.spec_json)
            _ensure_shared_quote_capacity(
                session, additional_positions=spec.portfolio.max_positions
            )
            _ensure_personal_quote_capacity(session, user.id, spec, account_id=row.id)
        row.status = body.status
        session.commit()
    return account_snapshot(session, row)


@app.get("/api/accounts/{account_id}/history")
def account_history(account_id: str, user: User = Depends(current_user), session: Session = Depends(get_db), point_offset: int = 0, fill_offset: int = 0, point_limit: int = 3000, fill_limit: int = 300):
    if min(point_offset, fill_offset) < 0 or not 1 <= point_limit <= 3000 or not 1 <= fill_limit <= 1000:
        raise HTTPException(status_code=422, detail="기록 페이지 범위가 올바르지 않습니다")
    account = session.scalar(
        select(PaperAccount).where(PaperAccount.id == account_id, PaperAccount.user_id == user.id)
    )
    if account is None:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다")
    points = session.scalars(
        select(EquityPoint).where(EquityPoint.account_id == account.id)
        .order_by(EquityPoint.observed_at.desc(), EquityPoint.id.desc()).offset(point_offset).limit(point_limit)
    ).all()
    fills = session.scalars(
        select(PaperFill).where(PaperFill.account_id == account.id)
        .order_by(PaperFill.executed_at.desc(), PaperFill.id.desc()).offset(fill_offset).limit(fill_limit)
    ).all()
    return {
        "equity": [{"at": row.observed_at, "value": row.equity} for row in reversed(points)],
        "pagination": {"point_offset": point_offset, "fill_offset": fill_offset,
                       "point_total": session.scalar(select(func.count()).select_from(EquityPoint).where(EquityPoint.account_id == account.id)),
                       "fill_total": session.scalar(select(func.count()).select_from(PaperFill).where(PaperFill.account_id == account.id))},
        "fills": [
            {
                "ticker": row.ticker, "side": row.side, "shares": row.shares,
                "price": row.price, "fee": row.fee, "reason": row.reason,
                "executed_at": row.executed_at,
            }
            for row in fills
        ],
    }


def _download_response(handle, filename: str, media_type: str):
    handle.seek(0)
    def chunks():
        while True:
            value = handle.read(64 * 1024)
            if not value:
                break
            yield value
    return StreamingResponse(chunks(), media_type=media_type,
        headers={"Content-Disposition": 'attachment; filename="{}"'.format(filename)},
        background=BackgroundTask(handle.close))


@app.get("/api/accounts/{account_id}/export")
def export_account(account_id: str, kind: str = "fills", user: User = Depends(current_user), session: Session = Depends(get_db)):
    account = session.scalar(select(PaperAccount).where(PaperAccount.id == account_id, PaperAccount.user_id == user.id))
    if account is None:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다")
    if kind not in {"fills", "equity"}:
        raise HTTPException(status_code=422, detail="kind는 fills 또는 equity입니다")
    _rate_limit("export:" + user.id, 10, 60)
    handle = tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b")
    try:
        handle.write(b"\xef\xbb\xbf")
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        columns = (["executed_at", "ticker", "side", "shares", "price", "fee", "reason", "id"] if kind == "fills"
                   else ["observed_at", "equity", "cash", "id"])
        model = PaperFill if kind == "fills" else EquityPoint
        when = model.executed_at if kind == "fills" else model.observed_at
        writer.writerow(columns)
        handle.write(buffer.getvalue().encode("utf-8"))
        for row in session.scalars(select(model).where(model.account_id == account.id).order_by(when, model.id).execution_options(yield_per=500)):
            buffer.seek(0); buffer.truncate(0)
            values = [getattr(row, column) for column in columns]
            writer.writerow([("'" + value if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"} else value) for value in values])
            handle.write(buffer.getvalue().encode("utf-8"))
        return _download_response(handle, "milkyway-{}-{}.csv".format(account.id, kind), "text/csv; charset=utf-8")
    except BaseException:
        handle.close()
        raise


@app.get("/api/backtests/export")
def export_backtests(user: User = Depends(current_user), session: Session = Depends(get_db)):
    _rate_limit("export:" + user.id, 10, 60)
    handle = tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b")
    try:
        handle.write(b"[")
        separator = b""
        for row in session.scalars(select(BacktestJob).where(BacktestJob.user_id == user.id).order_by(BacktestJob.created_at, BacktestJob.id).execution_options(yield_per=20)):
            payload = {column: getattr(row, column) for column in ("id", "strategy_id", "status", "bias_mode", "start_date", "end_date", "error", "created_at", "finished_at")}
            payload["result"] = json.loads(row.result_json) if row.result_json else None
            payload["strategy_spec"] = json.loads(row.strategy.spec_json)
            handle.write(separator + json.dumps(jsonable_encoder(payload), ensure_ascii=False, allow_nan=False).encode("utf-8"))
            separator = b",\n"
        handle.write(b"]")
        return _download_response(handle, "milkyway-backtests.json", "application/json")
    except BaseException:
        handle.close()
        raise


def _market_connection_identity(session, user):
    from .market_broker import identity
    return identity(session.get(MarketDataConnection, user.id))


@app.get("/api/market-details/{instrument_id}")
def personal_market_detail(instrument_id: str, user: User = Depends(current_user)):
    from .market_catalog import BY_ID
    from .market_details import detail_snapshot
    if not settings.personal_local_mode or settings.production or instrument_id not in BY_ID:
        raise HTTPException(404, "시장 항목을 찾을 수 없습니다")
    return detail_snapshot(settings, instrument_id)


@app.get("/api/company-details/{sector_id}/{symbol}")
def personal_company_detail(sector_id: str, symbol: str, user: User = Depends(current_user)):
    from .company_service import company_snapshot
    from .constellation_semantics import decorate_company
    return decorate_company(settings, company_snapshot(settings, sector_id, symbol))


@app.get("/api/energy-constellation")
def personal_energy_constellation(user: User = Depends(current_user)):
    from .energy_constellation import snapshot
    from .constellation_semantics import decorate
    return decorate(settings, snapshot(settings))


@app.get("/api/energy-constellation/search")
def personal_constellation_evidence(q: str = Query(min_length=1, max_length=240),
                                   mode: str = Query('keyword', pattern='^(keyword|semantic)$'),
                                   focus: str | None = Query(None, max_length=160),
                                   user: User = Depends(current_user)):
    _rate_limit("constellation-evidence:" + user.id, 60, 3600)
    if mode=='semantic':
        from .constellation_semantics import search
        return search(settings, q, focus)
    from .constellation_retrieval import search
    return search(settings, q, focus)


@app.get('/api/energy-constellation/analysis')
def personal_constellation_analysis(node_id: str = Query(min_length=1, max_length=160),
                                    basis: str = Query('relations', pattern='^(relations|product|segment|geography|revenue_type|end_market)$'),
                                    company: bool = False, user: User = Depends(current_user)):
    _rate_limit('constellation-analysis:'+user.id,120,3600)
    from .constellation_semantics import analysis
    return analysis(settings, node_id, basis, company)


@app.get("/api/company-entities/{entity_key}")
def personal_company_entity(entity_key: str, user: User = Depends(current_user)):
    from .company_entities import entity_snapshot
    from .constellation_semantics import decorate_company
    return decorate_company(settings, entity_snapshot(settings, entity_key))


@app.get("/api/company-entities/{entity_key}/network")
def personal_company_network(entity_key: str, via: str, page: int = Query(1, ge=1, le=50),
                             kind: str = Query("all", pattern="^(all|supplier|customer|partner|competitor)$"),
                             user: User = Depends(current_user)):
    from .company_network import network_snapshot
    return network_snapshot(settings, entity_key, via, page, kind)


@app.get("/api/company-entities/{entity_key}/price")
def personal_company_price(entity_key: str, symbol: str | None = Query(None, max_length=20),
                           user: User = Depends(current_user), session: Session = Depends(get_db)):
    from .company_prices import snapshot
    return snapshot(settings, entity_key, symbol,
                    connection_identity=_market_connection_identity(session, user))


@app.post("/api/company-entities/{entity_key}/price-watch", status_code=202)
def personal_company_price_watch(entity_key: str, symbol: str | None = Query(None, max_length=20),
                                 user: User = Depends(csrf_guard)):
    from .company_prices import watch
    _rate_limit('company-price-watch:' + user.id, 30, 60)
    return watch(settings, entity_key, user.id, symbol)


@app.post("/api/company-entities/{entity_key}/refresh", status_code=202)
def personal_company_entity_refresh(entity_key: str, user: User = Depends(csrf_guard)):
    from .company_entities import enqueue_entity
    _rate_limit("company-research:" + user.id, 60, 3600)
    return enqueue_entity(settings, entity_key)


@app.post("/api/company-details/{sector_id}/{symbol}/refresh", status_code=202)
def personal_company_refresh(sector_id: str, symbol: str, user: User = Depends(csrf_guard)):
    from .company_service import enqueue_company
    _rate_limit("company-research:" + user.id, 60, 3600)
    return enqueue_company(settings, sector_id, symbol)


@app.get("/api/market-overview")
def personal_market_snapshot(user: User = Depends(current_user), session: Session = Depends(get_db)):
    if not settings.personal_local_mode or settings.production:
        raise HTTPException(404, "Not found")
    from .market_service import market_overview as snapshot
    return snapshot(settings, connection_identity=_market_connection_identity(session, user))


def _personal_dashboard(user: User, session: Session) -> dict:
    from .personal_data import personal_data_status
    from .research_ai import configuration_status
    from .market_service import market_overview as personal_market_overview
    ai_status = configuration_status(settings)
    accounts = session.scalars(select(PaperAccount).where(PaperAccount.user_id == user.id).order_by(PaperAccount.created_at)).all()
    required_symbols = set()
    automatic_specs = []
    selection_current = True
    for account in accounts:
        if account.status == "active":
            spec = StrategySpec.model_validate_json(account.strategy.spec_json)
            required_symbols.update(spec.symbols)
            if spec.universe == "us_all":
                automatic_specs.append(spec)
                from .auto_universe import decision_for
                try:
                    required_symbols.update(decision_for(settings, spec, utcnow())["targets"])
                except (ValueError, OSError):
                    selection_current = False
            required_symbols.update(session.scalars(select(PaperPosition.ticker).where(PaperPosition.account_id == account.id)).all())
    data = personal_data_status(settings, symbols=sorted(required_symbols) if required_symbols else None)
    from .auto_universe import status as auto_status
    screening = auto_status(settings)
    if automatic_specs and not selection_current:
        data = {**data, "ready":False, "error":screening.get("message")}
    snapshots = [account_snapshot(session, row) for row in accounts]
    connection = session.get(MarketDataConnection, user.id)
    worker = _worker_payload(session, "paper-worker")
    data_worker = _worker_payload(session, "personal-data")
    backtest_worker = _worker_payload(session, "backtest-worker")
    quotes = session.scalars(select(MemberQuote).where(MemberQuote.user_id == user.id).order_by(MemberQuote.ticker)).all()
    now = utcnow()
    def aware(value):
        return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
    market = [{"id": row.ticker, "label": row.ticker, "symbol": row.ticker,
               "value": row.price, "source": row.source, "observed_at": aware(row.observed_at),
               "status": "live" if dt.timedelta(0) <= now - aware(row.observed_at) <= dt.timedelta(seconds=settings.quote_max_age_seconds) else "stale",
               "is_realtime": dt.timedelta(0) <= now - aware(row.observed_at) <= dt.timedelta(seconds=settings.quote_max_age_seconds)} for row in quotes]
    last_quote = max((row["observed_at"] for row in market), default=None)
    active = [row for row in accounts if row.status == "active"]
    open_now = regular_market_open()
    # Paper operation does not depend on the optional backtest queue worker.
    # Its actual heartbeat remains available separately in workers.backtest.
    if not worker["alive"] or not data_worker["alive"]:
        state, message = "worker_offline", "실행 프로세스를 시작하거나 재시작해 주세요. doctor 명령으로 상태를 확인할 수 있습니다."
    elif worker["error"]:
        state, message = "worker_error", "가상 체결 처리 중 오류가 발생했습니다. 원장은 보존되며 자동 재시도합니다. 반복되면 doctor와 로그를 확인하세요."
    elif connection is None:
        state, message = "credentials_required", "프로필에서 본인의 증권사 시세 API를 연결해 주세요."
    elif not active:
        state, message = "account_required", "전략을 저장하고 페이퍼 계좌를 만들어 활성화해 주세요."
    elif not data.get("ready") or data.get("stale") or not data.get("action_ready", True):
        state, message = "waiting_data", "일봉 데이터를 준비 중입니다. 이전 기록은 유지되며 데이터가 준비되면 자동으로 재개합니다."
    elif not open_now:
        state, message = "market_closed", "미국 정규장 대기 중입니다. 장이 열리면 시세 조회를 자동으로 재개합니다."
    elif not required_symbols.issubset({row["symbol"] for row in market if row["is_realtime"]}):
        state, message = "waiting_quotes", "새 증권사 시세를 기다리는 중입니다. 키·환경·네트워크·시세 이용 권한을 확인해 주세요."
    elif any(row.get("execution_status") not in {None, "active", "ready", "rebalanced", "market_closed"} for row in snapshots if row["status"] == "active"):
        state, message = "account_waiting", "시세 연결 중입니다. 계좌별 실행 상태에서 체결 대기 사유를 확인해 주세요."
    else:
        state, message = "running", "개인 시세를 수신 중입니다. 전략 일정에 따라 로컬 가상 원장에 체결합니다."
    first, last = None, data.get("latest_session")
    fingerprint = str(data.get("generation") or "")[:16]
    try:
        summary = get_dataset_summary(settings)
        first, last = summary.first_completed_session, summary.last_completed_session
    except (ValueError, OSError, FileNotFoundError):
        pass
    empty_heatmap = {"status": "selected_universe", "market": "us", "cells": [], "coverage_pct": 0, "as_of": last}
    return {
        "personal_local_mode": True, "local_demo_data": False,
        "operational": {"status": state, "message": message, "market_open": open_now, "last_quote_at": last_quote},
        "automatic_universe": screening,
        "personal_data": {**data, "status": "ready" if data.get("ready") and not data.get("stale") else "waiting_data",
                          "message": data.get("error") or "선택 종목 일봉 자동 갱신", "last_completed_session": last,
                          "symbol_count": len(data.get("symbols", []))},
        "market": market, "market_groups": {"us": market, "kr": []},
        "market_overview": personal_market_overview(settings, connection_identity=_market_connection_identity(session, user)),
        "sector_heatmap": empty_heatmap, "sector_heatmaps": {"us": empty_heatmap, "kr": empty_heatmap},
        "news": [], "accounts": snapshots,
        "data": {"first_completed_session": first, "last_completed_session": last,
                 "symbol_count": len(data.get("symbols", [])), "fresh": bool(data.get("ready") and not data.get("stale")),
                 "first_certified_snapshot": None, "first_certified_execution_date": None,
                 "forward_data_gate_ready": False, "strategy_candidate_data_blockers": 0,
                 "fingerprint": fingerprint, "trading_session_lag": 1 if data.get("stale") else 0,
                 "calendar_age_days": None},
        "worker": worker, "workers": {"paper": worker, "backtest": backtest_worker, "data": data_worker,
                                       "backup": _worker_payload(session, "local-backup")},
        "ai_enabled": ai_status["available"], "ai_connection": ai_status,
        "market_data_connection": _market_data_connection_payload(connection), "quote_provider": "member",
    }


@app.get("/health/trading")
def trading_ready(user: User = Depends(current_user), session: Session = Depends(get_db)):
    if not settings.personal_local_mode:
        return ready(session)
    payload = _personal_dashboard(user, session)["operational"]
    return JSONResponse(jsonable_encoder(payload), status_code=200 if payload["status"] in {"running", "market_closed"} else 503)


@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), session: Session = Depends(get_db)):
    if settings.personal_local_mode:
        return _personal_dashboard(user, session)
    if not member_ai_credentials_enabled(settings):
        # Authentication performed DB reads, but no writes are pending. Release
        # the checkout before a bounded broker status probe, then lazily acquire
        # a connection again for dashboard state.
        session.rollback()
        ai_connection_payload = _ai_connection_payload(None)
    else:
        ai_connection_payload = None
    bundle = get_dashboard_dataset(settings)
    market_groups = market_overview(
        session, quote_interval_seconds=settings.quote_interval_seconds
    )
    us_sector_heatmap = sector_heatmap(bundle, settings.sector_map_path)
    kr_sector_heatmap = {
        "status": "awaiting_korean_equity_data",
        "market": "kr",
        "taxonomy": "krx_provider_industry",
        "as_of": None,
        "method": "one_session_equal_weight_mean",
        "coverage_pct": 0.0,
        "cells": [],
    }
    accounts = session.scalars(select(PaperAccount).where(PaperAccount.user_id == user.id)).all()
    worker = session.get(RuntimeHeartbeat, "paper-worker")
    last_completed_session = bundle.last_completed_session
    freshness = completed_session_freshness(last_completed_session)
    ai_connection = (
        session.get(AiConnection, user.id)
        if member_ai_credentials_enabled(settings)
        else None
    )
    market_data_connection = (
        session.get(MarketDataConnection, user.id)
        if settings.member_credentials_enabled
        else None
    )
    if ai_connection_payload is None:
        ai_connection_payload = _ai_connection_payload(ai_connection)
    return {
        "personal_local_mode": False,
        "local_demo_data": settings.local_demo_data,
        "market": [row for rows in market_groups.values() for row in rows],
        "market_groups": market_groups,
        "sector_heatmap": us_sector_heatmap,
        "sector_heatmaps": {"us": us_sector_heatmap, "kr": kr_sector_heatmap},
        "news": news_feed(settings.news_feed_path),
        "accounts": [account_snapshot(session, row) for row in accounts],
        "data": {
            "first_completed_session": bundle.first_completed_session,
            "last_completed_session": last_completed_session,
            "calendar_age_days": max(0, (utcnow().date() - last_completed_session).days),
            **freshness,
            "symbol_count": bundle.symbol_count,
            "first_certified_snapshot": bundle.first_snapshot_date,
            "first_certified_execution_date": bundle.first_certified_execution_date,
            "forward_data_gate_ready": bundle.forward_data_gate_ready,
            "strategy_candidate_data_blockers": len(
                bundle.validation.get("strategy_candidate_data_blockers", [])
            ),
            "fingerprint": bundle.fingerprint[:16],
        },
        "worker": {
            "instance_id": worker.instance_id if worker else None,
            "observed_at": worker.observed_at if worker else None,
            "detail": worker.detail if worker else "not started",
        },
        "ai_enabled": ai_connection_payload["connected"],
        "ai_connection": ai_connection_payload,
        "market_data_connection": _market_data_connection_payload(market_data_connection),
        "quote_provider": settings.quote_provider,
    }


@app.get("/api/stream")
async def stream(request: Request, principal: StreamPrincipal = Depends(stream_principal)):
    if not _acquire_stream(principal.user_id):
        raise HTTPException(status_code=429, detail="실시간 연결 한도를 초과했습니다")

    async def events():
        try:
            for _ in range(120):
                if await request.is_disconnected():
                    break
                yield "event: heartbeat\ndata: {}\n\n".format(int(time.time()))
                await asyncio.sleep(15)
        finally:
            _release_stream(principal.user_id)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.exception_handler(ValidationError)
def validation_error(_request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors(include_url=False)})


from .research_routes import install as install_research_routes
from .research_ports import ResearchServices
install_research_routes(
    app,
    services=ResearchServices(
        get_settings=lambda: settings,
        rate_limit=_rate_limit,
        strategy_creation=_strategy_creation,
        account_creation=lambda strategy_id, name, user, session: _account_creation(
            AccountBody(strategy_id=strategy_id, name=name), user, session),
        strategy_payload=_strategy_payload,
        account_snapshot=account_snapshot,
        owned_strategy=_owned_strategy,
    ),
    current_user=current_user, csrf_guard=csrf_guard, get_db=get_db,
)
