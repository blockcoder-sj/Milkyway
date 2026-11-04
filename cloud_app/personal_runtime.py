"""Local paper operation diagnostics and idempotent account resumption.

This module never starts containers, sends orders, resets balances or bypasses
the price/data gates. The separate owner-run launcher manages local processes.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import stat
import threading

from fastapi import HTTPException
from sqlalchemy import select

from . import config
from .database import MarketDataConnection, MemberQuote, PaperAccount, PaperPosition, RuntimeHeartbeat, quota_allocation, utcnow
from .paper import account_snapshot, regular_market_open
from .paper_sessions import as_utc, session_payload
from .personal_auth import local_login_enabled
from .personal_data import personal_data_status
from .strategies import StrategySpec


CONTROL_URL = "http://127.0.0.1:19480"
TOKEN_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_probe_slot = threading.BoundedSemaphore(1)


def quote_budget(session, specifications):
    """Reserve next targets plus holdings without limiting the analysis universe."""
    selected, reserved = set(), 0
    for spec, account_id in specifications:
        held = set(session.scalars(select(PaperPosition.ticker).where(PaperPosition.account_id == account_id)).all()) if account_id else set()
        if spec.universe == "us_market":
            reserved += max(2*spec.portfolio.max_positions, len(held)+spec.portfolio.max_positions)
        else:
            selected.update(spec.symbols); selected.update(held)
    return len(selected)+reserved


def quote_limit(session, user_id):
    connection = session.get(MarketDataConnection, user_id)
    return 200 if connection and connection.provider == "toss" else 20


def require_personal(settings):
    if not local_login_enabled(settings):
        raise HTTPException(404, "Not found")


def control_connection(settings):
    """Only authenticated local-owner routes may return this launch capability."""
    require_personal(settings)
    path = config.ROOT / "runtime/.local-control.json"
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size > 1024 or info.st_uid != os.getuid():
                raise ValueError("invalid local control file")
            payload = json.loads(stream.read(1025))
        token = payload.get("token", "")
        if not isinstance(token, str) or not TOKEN_PATTERN.fullmatch(token):
            raise ValueError("invalid control capability")
        return {"available": True, "url": CONTROL_URL, "token": token}
    except (OSError, ValueError, TypeError):
        return {"available": False, "url": CONTROL_URL}


def _worker(session, name, settings, now):
    row = session.get(RuntimeHeartbeat, name)
    age = (now - as_utc(row.observed_at)).total_seconds() if row else None
    return {"alive": bool(age is not None and 0 <= age <= settings.worker_stale_seconds),
            "observed_at": as_utc(row.observed_at).isoformat() if row else None,
            "error": bool(row and row.detail.startswith("error="))}


def _accounts(session, user_id, now):
    rows = session.scalars(select(PaperAccount).where(PaperAccount.user_id == user_id)
                           .order_by(PaperAccount.created_at.desc(), PaperAccount.id)).all()
    choices = []
    for row in rows:
        run = session_payload(session, row, now)
        expired = bool(run and (run["expired"] or run["completed_at"]))
        choices.append({"id": row.id, "name": row.name, "status": row.status,
                        "expired": expired, "session": run,
                        "resumable": row.status in {"active", "paused"} and not expired})
    return rows, choices


def _choose(rows, choices, account_id):
    if account_id:
        selected = next((r for r in rows if r.id == account_id), None)
        if selected is None:
            raise HTTPException(404, "계좌를 찾을 수 없습니다")
        return selected
    for status in ("active", "paused"):
        choice = next((c for c in choices if c["status"] == status and c["resumable"]), None)
        if choice:
            return next(r for r in rows if r.id == choice["id"])
    return rows[0] if rows else None


def probe_connection(session, settings, user_id, account_id):
    require_personal(settings)
    if not _probe_slot.acquire(blocking=False):
        return {"state": "probe_busy", "checked_at": utcnow().isoformat()}
    try:
        return _probe_connection(session, settings, user_id, account_id)
    finally:
        _probe_slot.release()


def _probe_connection(session, settings, user_id, account_id):
    """Bounded read-only provider check, including before the regular session.

    Probe prices never enter the execution quote table or create ledger rows.
    Only a sanitized health observation is saved, against the same key version.
    """
    require_personal(settings)
    from .worker import _member_feed_config, _member_feed_version, _fetch_member_quotes, _discard_member_provider
    connection = session.get(MarketDataConnection, user_id)
    row = session.scalar(select(PaperAccount).where(PaperAccount.id == account_id, PaperAccount.user_id == user_id))
    if connection is None or row is None:
        return {"state": "credentials_required", "checked_at": utcnow().isoformat()}
    config_value = _member_feed_config(connection)
    version = _member_feed_version(config_value)
    spec = StrategySpec.model_validate_json(row.strategy.spec_json)
    symbols = set(spec.symbols)
    if spec.universe == "us_market":
        from .us_universe import status
        symbols.update(status(settings, user_id, spec).get("candidates", []))
    symbols.update(session.scalars(select(PaperPosition.ticker).where(PaperPosition.account_id == row.id)).all())
    symbols = sorted(symbols)
    session.commit()  # No database transaction is held during provider networking.
    known = {"quote_ip_not_allowed", "quote_authentication_failed", "quote_rate_limited", "quote_network_unavailable"}
    received = 0
    try:
        owner, values = _fetch_member_quotes(config_value, settings, tuple(symbols))
        if owner != user_id:
            raise RuntimeError("invalid provider owner")
        received = len({q.ticker for q in values if q.ticker in symbols})
        state = "connected" if received == len(symbols) and received else "no_quotes"
    except Exception as exc:
        detail = getattr(exc, "detail", "")
        state = detail if isinstance(detail, str) and detail in known else "quote_timeout" if isinstance(exc, TimeoutError) else "quote_provider_unavailable"
    finally:
        _discard_member_provider(user_id)
    current = session.scalar(select(MarketDataConnection).where(MarketDataConnection.user_id == user_id).execution_options(populate_existing=True))
    now = utcnow()
    if current is None or _member_feed_version(current) != version:
        return {"state": "connection_changed", "checked_at": now.isoformat()}
    component = "personal-probe:" + user_id
    heartbeat = session.get(RuntimeHeartbeat, component)
    if heartbeat is None:
        heartbeat = RuntimeHeartbeat(component=component, instance_id="personal-recovery")
        session.add(heartbeat)
    heartbeat.observed_at = now
    heartbeat.detail = json.dumps({"state": state, "received": received, "requested": len(symbols)})
    session.commit()
    return {"state": state, "received": received, "requested": len(symbols), "checked_at": now.isoformat()}


def operation_status(session, settings, user_id, account_id=None, *, now=None):
    require_personal(settings)
    now = now or utcnow()
    rows, choices = _accounts(session, user_id, now)
    selected = _choose(rows, choices, account_id)
    workers = {key: _worker(session, name, settings, now) for key, name in
               (("paper", "paper-worker"), ("data", "personal-data"), ("backtest", "backtest-worker"))}
    connection = session.get(MarketDataConnection, user_id)
    connected = connection is not None
    market_open = regular_market_open()
    result = {"checked_at": now.isoformat(), "program_running": True, "market_open": market_open,
              "workers": workers, "credential_saved": connected, "accounts": choices,
              "account_id": selected.id if selected else None,
              "ready_to_trade": False, "ready_to_wait": False,
              "quotes": {"fresh": 0, "required": 0, "last_received_at": None},
              "last_execution_at": None, "last_fill_at": None}

    def state(code, title, message, tone="warn"):
        return {**result, "state": code, "title": title, "message": message, "tone": tone}

    if selected is None:
        return state("account_required", "운용할 계좌가 없습니다", "전략을 저장하고 페이퍼 계좌를 먼저 만들어 주세요.")
    choice = next(c for c in choices if c["id"] == selected.id)
    result["account_name"] = selected.name
    if choice["expired"]:
        return state("session_finished", "운용 기간 종료", "설정한 운용 기간이 끝났습니다. 기록은 보존하며, 새 기간을 시험하려면 새 페이퍼 계좌를 만들어 주세요.")
    if selected.status in {"review_required", "configuration_required"}:
        return state("review_required", "계좌 검토가 필요합니다", account_snapshot(session, selected)["execution_detail"], "error")
    if selected.status != "active":
        return state("paused", "계좌가 일시정지돼 있습니다", "복구·재개를 누르면 이 계좌의 잔고와 기록을 이어서 운용합니다.")
    if not workers["paper"]["alive"] or not workers["data"]["alive"]:
        return state("worker_offline", "자동매매 프로세스가 멈췄습니다", "복구·재개를 눌러 실행 프로세스를 다시 시작해 주세요.", "error")
    if workers["paper"]["error"] or workers["data"]["error"]:
        return state("worker_error", "운용 오류 · 자동 재시도 중", "기록을 보존하며 다시 시도합니다. 복구·재개로 프로세스와 계좌 상태를 함께 점검할 수 있습니다.", "error")
    if not connected:
        return state("credentials_required", "증권사 키 연결이 필요합니다", "증권사 연결 설정에서 본인의 시세 API를 연결해 주세요.")
    try:
        spec = StrategySpec.model_validate_json(selected.strategy.spec_json)
        symbols = set(spec.symbols)
        if spec.universe == "us_market":
            from .us_universe import status as universe_status
            result["universe"] = universe_status(settings, user_id, spec)
            if not result["universe"].get("ready"):
                return state("waiting_universe", "미국 전체 종목 분석 중", "전체 거래 가능 종목의 일봉과 전략 점수를 준비하고 있습니다. 진행률을 확인해 주세요.")
            symbols.update(result["universe"].get("candidates", []))
        symbols.update(session.scalars(select(PaperPosition.ticker).where(PaperPosition.account_id == selected.id)).all())
    except ValueError:
        return state("configuration_required", "전략 설정을 확인해 주세요", "저장한 실행 규칙을 읽을 수 없어 체결을 대기합니다.", "error")
    quotes = session.scalars(select(MemberQuote).where(MemberQuote.user_id == user_id, MemberQuote.ticker.in_(symbols))).all()
    recent = [q for q in quotes if 0 <= (now-as_utc(q.observed_at)).total_seconds() <= settings.quote_max_age_seconds]
    result["quotes"] = {"fresh": len(recent), "required": len(symbols),
                        "last_received_at": max((as_utc(q.observed_at) for q in quotes), default=None)}
    if result["quotes"]["last_received_at"]:
        result["quotes"]["last_received_at"] = result["quotes"]["last_received_at"].isoformat()
    execution = session.get(RuntimeHeartbeat, "paper-account:" + selected.id)
    result["last_execution_at"] = as_utc(execution.observed_at).isoformat() if execution else None
    from .database import PaperFill
    last_fill = session.scalar(select(PaperFill.executed_at).where(PaperFill.account_id == selected.id)
                               .order_by(PaperFill.executed_at.desc()).limit(1))
    result["last_fill_at"] = as_utc(last_fill).isoformat() if last_fill else None
    observations = [session.get(RuntimeHeartbeat, prefix + user_id) for prefix in ("personal-feed:", "personal-probe:")]
    observations = [r for r in observations if r and connection and as_utc(r.observed_at) >= as_utc(connection.updated_at)]
    probe = session.get(RuntimeHeartbeat, "personal-probe:" + user_id)
    if probe and connection and as_utc(probe.observed_at) >= as_utc(connection.updated_at):
        try:
            result["connection_probe"] = {"state": json.loads(probe.detail).get("state"), "checked_at": as_utc(probe.observed_at).isoformat()}
        except (TypeError, ValueError, AttributeError):
            pass
    feed = max(observations, key=lambda r: as_utc(r.observed_at), default=None)
    if feed and connection and as_utc(feed.observed_at) >= as_utc(connection.updated_at) and now >= as_utc(feed.observed_at):
        try:
            feed_state = json.loads(feed.detail).get("state")
        except (TypeError, ValueError, AttributeError):
            feed_state = None
        messages = {
            "quote_ip_not_allowed": ("허용 IP 확인 필요", "운용 장소나 VPN을 바꿨다면 토스 WTS의 허용 IP에 집의 현재 공인 IP를 등록해 주세요. 복구·재개를 누르면 바로 다시 확인합니다. 활성 계좌는 장중에도 자동 재시도합니다."),
            "quote_authentication_failed": ("증권사 인증 실패", "저장된 키가 거절됐습니다. 증권사 연결 설정에서 본인 키를 다시 확인해 주세요."),
            "quote_rate_limited": ("증권사 요청 한도 · 재시도 대기", "요청 한도에 도달했습니다. 계좌 기록을 보존하고 자동으로 다시 시도합니다."),
            "quote_network_unavailable": ("인터넷·증권사 연결 끊김", "새 시세가 없어 매매를 대기합니다. 연결이 돌아오면 활성 계좌는 자동으로 다시 시도합니다."),
            "quote_timeout": ("증권사 응답 지연", "응답 시간이 길어 시세 조회를 중단했습니다. 계좌 기록을 보존하며 자동으로 다시 시도합니다."),
            "quote_provider_unavailable": ("증권사 연결 확인 필요", "시세 API 연결에 실패했습니다. 인터넷과 키·시세 권한을 확인해 주세요. 자동 재시도는 계속합니다."),
            "no_quotes": ("선택 종목 시세 확인 필요", "계좌에 필요한 시세를 모두 받지 못했습니다. 종목 코드와 미국 주식 시세 이용 권한을 확인해 주세요."),
        }
        if feed_state in messages:
            title, message = messages[feed_state]
            return state(feed_state, title, message, "error" if feed_state != "quote_rate_limited" else "warn")
    if choice["session"] and now < dt.datetime.fromisoformat(choice["session"]["opens_at"]):
        result["ready_to_wait"] = True
        return state("scheduled", "지정 거래일 개장 대기", "프로세스와 계좌가 켜져 있습니다. 지정한 미국 거래일에 자료를 확인하고 자동으로 운용합니다.", "idle")
    if not market_open:
        result["ready_to_wait"] = True
        return state("market_closed", "미국 정규장 대기 중", "프로세스와 계좌가 켜져 있습니다. 개장 후 당일 자료와 최신 시세가 준비되면 자동매매를 재개합니다.", "idle")
    data = personal_data_status(settings, symbols=sorted(symbols), now=now)
    result["data_ready"] = bool(data.get("ready") and not data.get("stale") and data.get("action_ready"))
    if not result["data_ready"]:
        return state("waiting_data", "일봉·분할·배당 확인 대기", data.get("error") or "필요한 자료를 자동으로 확인 중입니다. 준비 전에는 체결하지 않습니다.")
    if len(recent) != len(symbols) or not symbols:
        if recent:
            return state("waiting_quotes", "일부 종목 시세 갱신 대기", f"최신 시세 {len(recent)}/{len(symbols)}종목. 시세가 오래된 종목의 체결을 보류하고 계속 조회합니다. 갱신되면 자동으로 재개합니다.")
        return state("waiting_quotes", "인터넷·증권사 시세 확인 중", "최신 시세가 부족해 매매를 대기합니다. 연결이 돌아오면 자동으로 다시 시도합니다. 계속 실패하면 허용 IP와 시세 권한을 확인해 주세요.")
    snapshot = account_snapshot(session, selected)
    if snapshot["execution_status"] in {"review_required", "configuration_required", "waiting_data", "price_discontinuity"}:
        return state("account_waiting", "계좌 실행 조건 확인 중", snapshot["execution_detail"])
    result["ready_to_trade"] = True
    return state("running", "자동매매 정상", "최신 시세를 받으며 전략 조건에 따라 매매하거나 보유합니다. 새 체결이 없어도 조건에 따른 대기일 수 있습니다.", "ok")


def resume_account(session, settings, user_id, account_id=None):
    require_personal(settings)
    with quota_allocation(session, "accounts", "global"):
        with quota_allocation(session, "accounts", user_id):
            rows, choices = _accounts(session, user_id, utcnow())
            row = _choose(rows, choices, account_id)
            if row is None:
                raise HTTPException(409, "재개할 페이퍼 계좌가 없습니다. 전략에서 계좌를 먼저 만들어 주세요.")
            choice = next(c for c in choices if c["id"] == row.id)
            if not choice["resumable"]:
                reason = "운용 기간이 종료된 계좌는 재개할 수 없습니다." if choice["expired"] else "전략·보유 종목 검토가 필요해 자동으로 재개하지 않습니다."
                raise HTTPException(409, reason)
            try:
                specifications = [(StrategySpec.model_validate_json(account.strategy.spec_json), account.id) for account in rows if account.status == "active" or account.id == row.id]
            except ValueError as exc:
                raise HTTPException(409, "저장한 전략 규칙을 확인해 주세요.") from exc
            limit = quote_limit(session, user_id)
            if quote_budget(session, specifications) > limit:
                raise HTTPException(409, f"동시 시세 감시는 {limit}종목까지입니다. 다른 계좌를 정지한 뒤 재개해 주세요.")
            changed = row.status != "active"
            row.status = "active"
            session.commit()
    return {"resumed": changed, "account_id": row.id,
            "operation": operation_status(session, settings, user_id, row.id)}


def resume_and_check(session, settings, user_id, account_id=None):
    result = resume_account(session, settings, user_id, account_id)
    result["probe"] = probe_connection(session, settings, user_id, result["account_id"])
    result["operation"] = operation_status(session, settings, user_id, result["account_id"])
    return result
