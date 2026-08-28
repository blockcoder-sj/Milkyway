"""FastAPI surface for the temporary 30-member quant club."""

from __future__ import annotations

import datetime as dt
import hmac
import json
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, SecretStr, ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .ai import AiProviderError, generate_strategy
from .ai_credentials import (
    decrypt_api_key,
    encrypt_api_key,
    key_hint,
    provider_catalog,
    validate_provider_model,
)
from .config import get_settings
from .database import (
    BacktestJob,
    AiConnection,
    EquityPoint,
    PaperAccount,
    PaperFill,
    RuntimeHeartbeat,
    SessionLocal,
    Strategy,
    User,
    initialize_database,
    utcnow,
)
from .dashboard_views import completed_session_freshness, market_overview, news_feed, sector_heatmap
from .paper import account_snapshot
from .security import (
    create_session,
    hash_password,
    normalize_email,
    parse_session,
    validate_password,
    verify_password,
)
from .strategies import StrategySpec, get_dataset_bundle, strategy_code_preview


settings = get_settings()
STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title=settings.app_name, docs_url=None if settings.production else "/docs")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class RegisterBody(BaseModel):
    email: str
    display_name: str = Field(min_length=2, max_length=60)
    password: str
    invite_code: str


class LoginBody(BaseModel):
    email: str
    password: str


class PromptBody(BaseModel):
    prompt: str = Field(min_length=5, max_length=3000)


class AiConnectionBody(BaseModel):
    provider: str = Field(min_length=2, max_length=30)
    model: str = Field(min_length=2, max_length=100)
    api_key: SecretStr | None = None


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


class StatusBody(BaseModel):
    status: str


_attempt_lock = threading.Lock()
_attempts: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit(key: str, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    with _attempt_lock:
        bucket = _attempts[key]
        while bucket and bucket[0] < now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
        bucket.append(now)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def current_user(request: Request, session: Session = Depends(get_db)) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    try:
        payload = parse_session(token, settings.session_secret)
    except ValueError:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")
    user = session.get(User, payload["sub"])
    if user is None or not user.active:
        raise HTTPException(status_code=401, detail="비활성 계정입니다")
    request.state.session_payload = payload
    return user


def csrf_guard(request: Request, user: User = Depends(current_user)) -> User:
    supplied = request.headers.get("X-CSRF-Token", "")
    expected = request.state.session_payload.get("csrf", "")
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="CSRF validation failed")
    return user


def _set_session(response: Response, user: User) -> str:
    token, csrf = create_session(user.id, user.role, settings.session_secret, settings.session_hours)
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


@app.on_event("startup")
def startup() -> None:
    errors = settings.startup_errors()
    if errors:
        raise RuntimeError("Startup configuration failed: " + "; ".join(errors))
    initialize_database()
    get_dataset_bundle(settings)


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


@app.get("/health/ready")
def ready(session: Session = Depends(get_db)):
    details = {"database": False, "dataset": False, "data_gate": False, "worker": False}
    try:
        session.execute(text("SELECT 1"))
        details["database"] = True
        bundle = get_dataset_bundle(settings)
        details["dataset"] = bool(bundle.data)
        details["data_gate"] = bundle.forward_data_gate_ready
        heartbeat = session.get(RuntimeHeartbeat, "paper-worker")
        if heartbeat:
            observed = heartbeat.observed_at
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=dt.timezone.utc)
            details["worker"] = observed >= utcnow() - dt.timedelta(seconds=settings.worker_stale_seconds)
    except Exception as exc:
        details["error"] = str(exc)[:300]
    ok = details["database"] and details["dataset"] and details["data_gate"]
    return JSONResponse({"status": "ready" if ok else "not_ready", "components": details}, status_code=200 if ok else 503)


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterBody, request: Request, response: Response, session: Session = Depends(get_db)):
    _rate_limit("register:" + (request.client.host if request.client else "unknown"), 5, 3600)
    if not hmac.compare_digest(body.invite_code, settings.invite_code):
        raise HTTPException(status_code=403, detail="초대 코드가 올바르지 않습니다")
    user_count = int(session.scalar(select(func.count()).select_from(User)) or 0)
    if user_count >= settings.max_users:
        raise HTTPException(status_code=409, detail="동아리 계정 정원이 마감되었습니다")
    try:
        email = normalize_email(body.email)
        validate_password(body.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    user = User(
        email=email,
        display_name=body.display_name.strip(),
        password_hash=hash_password(body.password),
        role="member",
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다")
    csrf = _set_session(response, user)
    return {"user": {"id": user.id, "email": user.email, "display_name": user.display_name}, "csrf": csrf}


@app.post("/api/auth/login")
def login(body: LoginBody, request: Request, response: Response, session: Session = Depends(get_db)):
    key = "login:" + (request.client.host if request.client else "unknown")
    _rate_limit(key, 10, 600)
    try:
        email = normalize_email(body.email)
    except ValueError:
        email = "invalid"
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash) or not user.active:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
    csrf = _set_session(response, user)
    return {"user": {"id": user.id, "email": user.email, "display_name": user.display_name}, "csrf": csrf}


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response, _user: User = Depends(csrf_guard)):
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


def _ai_connection_payload(row: AiConnection | None) -> dict:
    return {
        "connected": row is not None,
        "provider": row.provider if row else None,
        "model": row.model if row else None,
        "key_hint": row.key_hint if row else None,
        "updated_at": row.updated_at if row else None,
        "providers": provider_catalog(),
    }


@app.get("/api/me/ai-connection")
def get_ai_connection(user: User = Depends(current_user), session: Session = Depends(get_db)):
    return _ai_connection_payload(session.get(AiConnection, user.id))


@app.put("/api/me/ai-connection")
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
    if not supplied_key and (row is None or row.provider != provider):
        raise HTTPException(status_code=422, detail="새 AI 공급자를 연결하려면 API 키를 입력해 주세요")
    if supplied_key:
        try:
            encrypted_key = encrypt_api_key(supplied_key, settings)
            hint = key_hint(supplied_key)
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


@app.delete("/api/me/ai-connection", status_code=204)
def delete_ai_connection(user: User = Depends(csrf_guard), session: Session = Depends(get_db)):
    row = session.get(AiConnection, user.id)
    if row is not None:
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


def _save_strategy(session: Session, user: User, spec: StrategySpec, prompt: str) -> Strategy:
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
    session.commit()
    return row


@app.post("/api/strategies/generate", status_code=201)
def ai_strategy(body: PromptBody, user: User = Depends(csrf_guard), session: Session = Depends(get_db)):
    _rate_limit("ai:" + user.id, 10, 3600)
    connection = session.get(AiConnection, user.id)
    if connection is None:
        raise HTTPException(status_code=409, detail="설정에서 AI API를 먼저 연결해 주세요")
    try:
        api_key = decrypt_api_key(connection.encrypted_api_key, settings)
        spec, _preview = generate_strategy(
            body.prompt,
            provider=connection.provider,
            model=connection.model,
            api_key=api_key,
            timeout_seconds=settings.ai_timeout_seconds,
        )
    except AiProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
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
    bundle = get_dataset_bundle(settings)
    first_execution = dt.date.fromisoformat(bundle.first_certified_execution_date)
    if body.bias_mode == "strict" and body.start_date < first_execution:
        raise HTTPException(
            status_code=422,
            detail="엄격 PIT 시작일은 첫 인증 스냅샷의 다음 거래일 {} 이후여야 합니다".format(
                bundle.first_certified_execution_date
            ),
        )
    if body.end_date > bundle.index.max().date():
        raise HTTPException(
            status_code=422,
            detail="마지막 완료 세션 {}을 넘을 수 없습니다".format(
                bundle.index.max().date().isoformat()
            ),
        )
    if body.bias_mode == "strict" and not bundle.forward_data_gate_ready:
        raise HTTPException(
            status_code=503,
            detail="최신 일일 데이터 품질 게이트가 통과될 때까지 엄격 PIT 백테스트를 중단합니다",
        )
    today = utcnow().date()
    count = session.scalar(
        select(func.count()).select_from(BacktestJob).where(
            BacktestJob.user_id == user.id,
            BacktestJob.created_at >= dt.datetime.combine(today, dt.time.min, tzinfo=dt.timezone.utc),
        )
    )
    if int(count or 0) >= settings.max_backtests_per_user_day:
        raise HTTPException(status_code=429, detail="일일 백테스트 한도를 초과했습니다")
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
def list_backtests(user: User = Depends(current_user), session: Session = Depends(get_db)):
    rows = session.scalars(
        select(BacktestJob).where(BacktestJob.user_id == user.id)
        .order_by(BacktestJob.created_at.desc()).limit(50)
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


@app.post("/api/accounts", status_code=201)
def create_account(body: AccountBody, user: User = Depends(csrf_guard), session: Session = Depends(get_db)):
    strategy = _owned_strategy(session, user, body.strategy_id)
    count = session.scalar(
        select(func.count()).select_from(PaperAccount).where(PaperAccount.user_id == user.id)
    )
    if int(count or 0) >= settings.max_accounts_per_user:
        raise HTTPException(status_code=409, detail="사용자별 페이퍼 계좌 한도를 초과했습니다")
    spec = StrategySpec.model_validate_json(strategy.spec_json)
    row = PaperAccount(
        user_id=user.id,
        strategy_id=strategy.id,
        name=body.name.strip(),
        initial_cash=spec.portfolio.initial_cash,
        cash=spec.portfolio.initial_cash,
    )
    session.add(row)
    session.flush()
    session.add(EquityPoint(account_id=row.id, equity=row.cash, cash=row.cash))
    session.commit()
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
    if row.status == "review_required":
        raise HTTPException(
            status_code=409,
            detail="상장 이탈/corporate action 검토가 필요해 사용자가 재개할 수 없습니다",
        )
    row.status = body.status
    session.commit()
    return account_snapshot(session, row)


@app.get("/api/accounts/{account_id}/history")
def account_history(account_id: str, user: User = Depends(current_user), session: Session = Depends(get_db)):
    account = session.scalar(
        select(PaperAccount).where(PaperAccount.id == account_id, PaperAccount.user_id == user.id)
    )
    if account is None:
        raise HTTPException(status_code=404, detail="계좌를 찾을 수 없습니다")
    points = session.scalars(
        select(EquityPoint).where(EquityPoint.account_id == account.id)
        .order_by(EquityPoint.observed_at).limit(3000)
    ).all()
    fills = session.scalars(
        select(PaperFill).where(PaperFill.account_id == account.id)
        .order_by(PaperFill.executed_at.desc()).limit(300)
    ).all()
    return {
        "equity": [{"at": row.observed_at, "value": row.equity} for row in points],
        "fills": [
            {
                "ticker": row.ticker, "side": row.side, "shares": row.shares,
                "price": row.price, "fee": row.fee, "reason": row.reason,
                "executed_at": row.executed_at,
            }
            for row in fills
        ],
    }


@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), session: Session = Depends(get_db)):
    bundle = get_dataset_bundle(settings)
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
    last_completed_session = bundle.index.max().date()
    freshness = completed_session_freshness(last_completed_session)
    ai_connection = session.get(AiConnection, user.id)
    return {
        "market": [row for rows in market_groups.values() for row in rows],
        "market_groups": market_groups,
        "sector_heatmap": us_sector_heatmap,
        "sector_heatmaps": {"us": us_sector_heatmap, "kr": kr_sector_heatmap},
        "news": news_feed(settings.news_feed_path),
        "accounts": [account_snapshot(session, row) for row in accounts],
        "data": {
            "first_completed_session": bundle.index.min().date(),
            "last_completed_session": last_completed_session,
            "calendar_age_days": max(0, (utcnow().date() - last_completed_session).days),
            **freshness,
            "symbol_count": len(bundle.data),
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
        "ai_enabled": ai_connection is not None,
        "ai_connection": _ai_connection_payload(ai_connection),
        "quote_provider": settings.quote_provider,
    }


@app.get("/api/stream")
def stream(_user: User = Depends(current_user)):
    def events():
        for _ in range(120):
            yield "event: heartbeat\ndata: {}\n\n".format(int(time.time()))
            time.sleep(15)
    return StreamingResponse(events(), media_type="text/event-stream")


@app.exception_handler(ValidationError)
def validation_error(_request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors(include_url=False)})
