"""
market_calendar.py — NYSE 시장 상태 감지 모듈 (3단계 fallback)

1차: exchange_calendars 패키지 (정확, 조기폐장 포함, 범위 제한 있음)
2차: Finnhub API (실시간 장 상태, 임시 휴장 감지, 네트워크 필요)
3차: 하드코딩 fallback (항상 동작, 조기폐장/임시 휴장 미지원)

사용법:
    from market_calendar import (
        is_trading_day, is_market_open_now, get_market_close_time,
        is_early_close, count_trading_days_between, next_trading_day,
        get_market_status,
    )

환경변수:
    FINNHUB_API_KEY — Finnhub 무료 API 키 (없으면 2차 레이어 비활성)
"""

import datetime
import logging
import os
import json
import time

from cloud_app.bounded_io import read_requests_json

logger = logging.getLogger("market_calendar")

# ============================================================
# Layer 1: exchange_calendars (오프라인, 정확, 범위 제한)
# ============================================================
_nyse_cal = None  # lazy singleton
_USE_EXCHANGE_CALENDARS = None  # None = 아직 시도 안 함
_XCAL_LAST_SESSION = None  # 캘린더 마지막 세션 날짜


def _get_nyse():
    """NYSE 캘린더 싱글턴 (lazy init, ~8MB)."""
    global _nyse_cal, _USE_EXCHANGE_CALENDARS, _XCAL_LAST_SESSION
    if _USE_EXCHANGE_CALENDARS is False:
        return None
    if _nyse_cal is not None:
        return _nyse_cal
    try:
        import exchange_calendars as xcals
        _nyse_cal = xcals.get_calendar("XNYS")
        _XCAL_LAST_SESSION = _nyse_cal.last_session.date()
        _USE_EXCHANGE_CALENDARS = True
        logger.info("exchange_calendars loaded (NYSE, ~%s). "
                     "Early-close & holiday detection enabled.", _XCAL_LAST_SESSION)
        return _nyse_cal
    except ImportError:
        _USE_EXCHANGE_CALENDARS = False
        logger.warning("exchange_calendars not installed. "
                        "pip install exchange_calendars for accurate detection.")
        return None
    except Exception as e:
        _USE_EXCHANGE_CALENDARS = False
        logger.warning("exchange_calendars init failed: %s. Using fallback.", e)
        return None


def _xcal_in_range(date_obj):
    """exchange_calendars 범위 안에 있는지 확인."""
    cal = _get_nyse()
    if cal is None:
        return False
    return cal.first_session.date() <= date_obj <= _XCAL_LAST_SESSION


# ============================================================
# Layer 2: Finnhub API (실시간, 임시 휴장 감지)
# ============================================================
_FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
_finnhub_cache = {}  # {date_str: {"is_open": bool, "holiday": str, "ts": float}}
_FINNHUB_CACHE_TTL = 3600  # 1시간 캐시
_MAX_FINNHUB_RESPONSE_BYTES = 64 * 1024


def _query_finnhub_market_status():
    # type: () -> dict | None
    """Finnhub /stock/market-status 호출. 실패 시 None."""
    if not _FINNHUB_API_KEY:
        return None
    try:
        import requests
        url = "https://finnhub.io/api/v1/stock/market-status"
        resp = requests.get(
            url,
            params={"exchange": "US"},
            headers={"X-Finnhub-Token": _FINNHUB_API_KEY},
            timeout=5,
            stream=True,
        )
        if resp.status_code == 200:
            data = read_requests_json(
                resp, maximum_bytes=_MAX_FINNHUB_RESPONSE_BYTES
            )
            # {"exchange":"US","holiday":"","isOpen":true,"session":"regular","t":1711...,"timezone":"America/New_York"}
            return data
        else:
            resp.close()
            logger.warning("Finnhub API returned %d", resp.status_code)
    except Exception as exc:
        logger.warning("Finnhub API failed: %s", type(exc).__name__)
    return None


def _finnhub_is_open_today():
    # type: () -> bool | None
    """Finnhub으로 오늘 장이 열렸는지/열려있는지 확인. 모르면 None."""
    today_str = _now_et().date().strftime("%Y-%m-%d")
    # 캐시 확인
    cached = _finnhub_cache.get(today_str)
    if cached and (time.time() - cached["ts"]) < _FINNHUB_CACHE_TTL:
        return cached["is_open"]
    data = _query_finnhub_market_status()
    if data is None:
        return None
    is_open = data.get("isOpen", None)
    holiday_name = data.get("holiday", "")
    session = data.get("session", "")
    # 캐시 저장
    _finnhub_cache[today_str] = {
        "is_open": is_open,
        "holiday": holiday_name,
        "session": session,
        "ts": time.time(),
    }
    if holiday_name:
        logger.info("Finnhub: today is holiday (%s)", holiday_name)
    return is_open


def _finnhub_is_trading_day_today():
    # type: () -> bool | None
    """오늘이 거래일인지 Finnhub으로 확인. 모르면 None.
    isOpen=False + holiday 이름 있으면 → 휴장일.
    isOpen=False + 장 마감 후이면 → 거래일이었음.
    """
    today_str = _now_et().date().strftime("%Y-%m-%d")
    cached = _finnhub_cache.get(today_str)
    if cached and (time.time() - cached["ts"]) < _FINNHUB_CACHE_TTL:
        if cached.get("holiday"):
            return False  # 명시적 휴장
        # isOpen=False이지만 holiday 아니면 장 마감 후 → 거래일
        return True
    data = _query_finnhub_market_status()
    if data is None:
        return None
    holiday_name = data.get("holiday", "")
    _finnhub_cache[today_str] = {
        "is_open": data.get("isOpen"),
        "holiday": holiday_name,
        "session": data.get("session", ""),
        "ts": time.time(),
    }
    if holiday_name:
        return False
    return True


# ============================================================
# Layer 3: 하드코딩 fallback (항상 동작)
# ============================================================
def _kst_to_et(kst_dt):
    # type: (datetime.datetime) -> datetime.datetime
    """한국시간 → 미국 동부시간 변환 (DST 자동 처리)."""
    try:
        from zoneinfo import ZoneInfo
        kst = ZoneInfo("Asia/Seoul")
        et = ZoneInfo("US/Eastern")
        kst_aware = kst_dt.replace(tzinfo=kst)
        et_aware = kst_aware.astimezone(et)
        return et_aware.replace(tzinfo=None)
    except ImportError:
        et_approx = kst_dt - datetime.timedelta(hours=14)
        offset = _get_et_offset_fallback(et_approx.date())
        return kst_dt - datetime.timedelta(hours=offset)


def _get_et_offset_fallback(date_obj):
    # type: (datetime.date) -> int
    """KST-ET 오프셋 (DST 수동 계산). EDT=13h, EST=14h."""
    y = date_obj.year
    mar1 = datetime.date(y, 3, 1)
    dst_start = mar1 + datetime.timedelta(days=(6 - mar1.weekday()) % 7 + 7)
    nov1 = datetime.date(y, 11, 1)
    dst_end = nov1 + datetime.timedelta(days=(6 - nov1.weekday()) % 7)
    if dst_start <= date_obj < dst_end:
        return 13  # EDT
    return 14  # EST


def _now_et():
    # type: () -> datetime.datetime
    """현재 미국 동부시간."""
    return _kst_to_et(datetime.datetime.now())


def _is_us_market_holiday_hardcoded(date_obj):
    # type: (datetime.date) -> bool
    """미국 주요 공휴일 동적 계산 (fallback)."""
    y = date_obj.year
    holidays = set()
    # New Year's Day
    ny = datetime.date(y, 1, 1)
    if ny.weekday() == 6: ny = datetime.date(y, 1, 2)
    elif ny.weekday() == 5: ny = datetime.date(y - 1, 12, 31)
    holidays.add(ny)
    next_ny = datetime.date(y + 1, 1, 1)
    if next_ny.weekday() == 5:
        holidays.add(datetime.date(y, 12, 31))
    # MLK Day (1월 셋째 월요일)
    d = datetime.date(y, 1, 1)
    mondays = 0
    while mondays < 3:
        if d.weekday() == 0: mondays += 1
        if mondays < 3: d += datetime.timedelta(days=1)
    holidays.add(d)
    # Presidents Day (2월 셋째 월요일)
    d = datetime.date(y, 2, 1)
    mondays = 0
    while mondays < 3:
        if d.weekday() == 0: mondays += 1
        if mondays < 3: d += datetime.timedelta(days=1)
    holidays.add(d)
    # Memorial Day (5월 마지막 월요일)
    d = datetime.date(y, 5, 31)
    while d.weekday() != 0: d -= datetime.timedelta(days=1)
    holidays.add(d)
    # Good Friday (부활절 - 2일)
    a = y % 19
    b = y // 100
    c = y % 100
    d_val = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d_val - g + 15) % 30
    ii = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * ii - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = datetime.date(y, month, day)
    holidays.add(easter - datetime.timedelta(days=2))
    # Juneteenth
    jt = datetime.date(y, 6, 19)
    if jt.weekday() == 6: jt += datetime.timedelta(days=1)
    elif jt.weekday() == 5: jt -= datetime.timedelta(days=1)
    holidays.add(jt)
    # Independence Day
    id4 = datetime.date(y, 7, 4)
    if id4.weekday() == 6: id4 += datetime.timedelta(days=1)
    elif id4.weekday() == 5: id4 -= datetime.timedelta(days=1)
    holidays.add(id4)
    # Labor Day (9월 첫째 월요일)
    d = datetime.date(y, 9, 1)
    while d.weekday() != 0: d += datetime.timedelta(days=1)
    holidays.add(d)
    # Thanksgiving (11월 넷째 목요일)
    d = datetime.date(y, 11, 1)
    thursdays = 0
    while thursdays < 4:
        if d.weekday() == 3: thursdays += 1
        if thursdays < 4: d += datetime.timedelta(days=1)
    holidays.add(d)
    # Christmas
    xm = datetime.date(y, 12, 25)
    if xm.weekday() == 6: xm += datetime.timedelta(days=1)
    elif xm.weekday() == 5: xm -= datetime.timedelta(days=1)
    holidays.add(xm)
    return date_obj in holidays


def _is_early_close_hardcoded(date_obj):
    # type: (datetime.date) -> bool
    """NYSE 정기 조기폐장일 (13:00 마감)."""
    y = date_obj.year
    early_close_dates = set()
    # 추수감사절 다음날 (Black Friday)
    d = datetime.date(y, 11, 1)
    thursdays = 0
    while thursdays < 4:
        if d.weekday() == 3: thursdays += 1
        if thursdays < 4: d += datetime.timedelta(days=1)
    early_close_dates.add(d + datetime.timedelta(days=1))
    # 크리스마스 전날 (평일인 경우만)
    xm_eve = datetime.date(y, 12, 24)
    if xm_eve.weekday() < 5:
        early_close_dates.add(xm_eve)
    # 독립기념일 전날 (7/3, 평일인 경우만)
    jul3 = datetime.date(y, 7, 3)
    if jul3.weekday() < 5:
        early_close_dates.add(jul3)
    return date_obj in early_close_dates


# ============================================================
# Public API — 3단계 fallback 체인
# ============================================================
def is_trading_day(date_obj):
    # type: (datetime.date) -> bool
    """주어진 날짜가 NYSE 거래일인지 확인.
    1차: exchange_calendars (범위 내)
    2차: Finnhub API (오늘만, 임시 휴장 감지)
    3차: 하드코딩
    """
    # Layer 1: exchange_calendars
    if _xcal_in_range(date_obj):
        try:
            import pandas as pd
            return _get_nyse().is_session(pd.Timestamp(date_obj))
        except Exception:
            pass

    # Layer 2: Finnhub (오늘 날짜만 실시간 확인 가능)
    if date_obj == _now_et().date():
        result = _finnhub_is_trading_day_today()
        if result is not None:
            return result

    # Layer 3: 하드코딩
    return date_obj.weekday() < 5 and not _is_us_market_holiday_hardcoded(date_obj)


def is_early_close(date_obj):
    # type: (datetime.date) -> bool
    """주어진 날짜가 NYSE 조기폐장일인지 확인 (13:00 마감)."""
    # Layer 1: exchange_calendars
    if _xcal_in_range(date_obj):
        try:
            import pandas as pd
            cal = _get_nyse()
            ts = pd.Timestamp(date_obj)
            if not cal.is_session(ts):
                return False
            close_time = cal.session_close(ts)
            normal_close_hour = 20 if _get_et_offset_fallback(date_obj) == 14 else 19
            return close_time.hour < normal_close_hour
        except Exception:
            pass
    # Layer 3: 하드코딩 (Finnhub은 조기폐장 구분 어려움)
    return _is_early_close_hardcoded(date_obj)


def get_market_hours(date_obj):
    # type: (datetime.date) -> tuple | None
    """(open_hour, open_min, close_hour, close_min) in ET. None if holiday."""
    if not is_trading_day(date_obj):
        return None
    if is_early_close(date_obj):
        return (9, 30, 13, 0)
    return (9, 30, 16, 0)


def get_market_close_time(date_obj):
    # type: (datetime.date) -> tuple | None
    """(close_hour, close_min) in ET. None if not a trading day."""
    hours = get_market_hours(date_obj)
    if hours is None:
        return None
    return (hours[2], hours[3])


def is_market_open_now():
    # type: () -> bool
    """현재 NYSE가 열려있는지 확인.
    시간 기반 체크를 먼저 수행하고, Finnhub은 장중 임시 휴장 감지에만 사용.
    (버그 수정: Finnhub 캐시가 프리마켓 isOpen=False를 장중에도 반환하는 문제 방지)
    """
    # Layer 1 + 3: 시간 기반 체크 (primary)
    now = _now_et()
    today = now.date()
    hours = get_market_hours(today)
    if hours is None:
        return False
    market_open = now.replace(hour=hours[0], minute=hours[1], second=0)
    market_close = now.replace(hour=hours[2], minute=hours[3], second=0)
    if not (market_open <= now <= market_close):
        return False  # 장 시간 밖 → Finnhub 불필요

    # Layer 2: Finnhub — 장 시간 내에서 임시 휴장 감지용
    if _FINNHUB_API_KEY:
        result = _finnhub_is_open_today()
        if result is False:
            return False  # 장 시간인데 Finnhub=False → 임시 휴장

    return True


def get_market_status():
    # type: () -> dict
    """현재 시장 상태 상세 정보."""
    now = _now_et()
    today = now.date()

    # 사용 중인 백엔드 표시
    backend = "hardcoded"
    if _xcal_in_range(today):
        backend = "exchange_calendars"
    elif _FINNHUB_API_KEY:
        backend = "finnhub_api"

    hours = get_market_hours(today)

    if hours is None:
        next_day = next_trading_day(today)
        # Finnhub 캐시에서 휴일 이름 확인
        today_str = today.strftime("%Y-%m-%d")
        holiday_name = ""
        cached = _finnhub_cache.get(today_str)
        if cached:
            holiday_name = cached.get("holiday", "")
        reason = "weekend" if today.weekday() >= 5 else ("holiday: " + holiday_name if holiday_name else "holiday")
        return {
            "status": "closed",
            "reason": reason,
            "next_open": next_day.strftime("%Y-%m-%d"),
            "now_et": now.strftime("%Y-%m-%d %H:%M ET"),
            "backend": backend,
        }

    market_open = now.replace(hour=hours[0], minute=hours[1], second=0)
    market_close = now.replace(hour=hours[2], minute=hours[3], second=0)

    if now < market_open:
        return {
            "status": "pre_market",
            "opens_at": "{:02d}:{:02d} ET".format(hours[0], hours[1]),
            "closes_at": "{:02d}:{:02d} ET".format(hours[2], hours[3]),
            "early_close": is_early_close(today),
            "now_et": now.strftime("%Y-%m-%d %H:%M ET"),
            "backend": backend,
        }
    elif now <= market_close:
        return {
            "status": "open",
            "closes_at": "{:02d}:{:02d} ET".format(hours[2], hours[3]),
            "early_close": is_early_close(today),
            "now_et": now.strftime("%Y-%m-%d %H:%M ET"),
            "backend": backend,
        }
    else:
        next_day = next_trading_day(today)
        return {
            "status": "after_hours",
            "closed_at": "{:02d}:{:02d} ET".format(hours[2], hours[3]),
            "next_open": next_day.strftime("%Y-%m-%d"),
            "now_et": now.strftime("%Y-%m-%d %H:%M ET"),
            "backend": backend,
        }


def count_trading_days_between(start_date, end_date):
    # type: (datetime.date, datetime.date) -> int
    """start_date ~ end_date 사이의 영업일 수 (양 끝 제외)."""
    if end_date <= start_date:
        return 0
    # Layer 1: exchange_calendars (범위 내)
    if _xcal_in_range(start_date) and _xcal_in_range(end_date):
        try:
            import pandas as pd
            range_start = start_date + datetime.timedelta(days=1)
            range_end = end_date - datetime.timedelta(days=1)
            if range_start > range_end:
                return 0
            sessions = _get_nyse().sessions_in_range(
                pd.Timestamp(range_start), pd.Timestamp(range_end))
            return len(sessions)
        except Exception:
            pass
    # Layer 3: 하드코딩
    count = 0
    d = start_date + datetime.timedelta(days=1)
    while d < end_date:
        if d.weekday() < 5 and not _is_us_market_holiday_hardcoded(d):
            count += 1
        d += datetime.timedelta(days=1)
    return count


def next_trading_day(from_date):
    # type: (datetime.date) -> datetime.date
    """from_date 다음 거래일."""
    # Layer 1
    cal = _get_nyse()
    if cal is not None:
        try:
            import pandas as pd
            ts = pd.Timestamp(from_date) + pd.Timedelta(days=1)
            for _ in range(10):
                if ts.date() > _XCAL_LAST_SESSION:
                    break  # 범위 초과 → fallback
                if cal.is_session(ts):
                    return ts.date()
                ts += pd.Timedelta(days=1)
        except Exception:
            pass
    # Layer 3
    d = from_date + datetime.timedelta(days=1)
    while d.weekday() >= 5 or _is_us_market_holiday_hardcoded(d):
        d += datetime.timedelta(days=1)
    return d


def prev_trading_day(from_date):
    # type: (datetime.date) -> datetime.date
    """from_date 이전 거래일."""
    cal = _get_nyse()
    if cal is not None:
        try:
            import pandas as pd
            ts = pd.Timestamp(from_date) - pd.Timedelta(days=1)
            for _ in range(10):
                if ts.date() < cal.first_session.date():
                    break
                if cal.is_session(ts):
                    return ts.date()
                ts -= pd.Timedelta(days=1)
        except Exception:
            pass
    d = from_date - datetime.timedelta(days=1)
    while d.weekday() >= 5 or _is_us_market_holiday_hardcoded(d):
        d -= datetime.timedelta(days=1)
    return d


# ============================================================
# CLI 테스트
# ============================================================
if __name__ == "__main__":
    print("=== Market Calendar Status ===")
    status = get_market_status()
    for k, v in status.items():
        print("  {}: {}".format(k, v))

    today = datetime.date.today()
    print("\nToday ({})".format(today))
    print("  Trading day: {}".format(is_trading_day(today)))
    print("  Early close: {}".format(is_early_close(today)))
    print("  Market open now: {}".format(is_market_open_now()))
    print("  Market hours: {}".format(get_market_hours(today)))
    print("  Next trading day: {}".format(next_trading_day(today)))
    print("  Prev trading day: {}".format(prev_trading_day(today)))

    # 향후 7일 스케줄
    print("\n=== Next 7 days ===")
    d = today
    for _ in range(7):
        hours = get_market_hours(d)
        tag = ""
        if hours is None:
            tag = "CLOSED"
        elif is_early_close(d):
            tag = "EARLY CLOSE (13:00)"
        else:
            tag = "NORMAL (16:00)"
        print("  {} ({}) — {}".format(d, d.strftime("%a"), tag))
        d += datetime.timedelta(days=1)

    # 백엔드 정보
    print("\n=== Backend Info ===")
    print("  exchange_calendars: {}".format(
        "active (~{})".format(_XCAL_LAST_SESSION) if _USE_EXCHANGE_CALENDARS else "inactive"))
    print("  Finnhub API: {}".format("configured" if _FINNHUB_API_KEY else "not configured"))
    print("  Hardcoded fallback: always available")

    # 범위 초과 테스트
    print("\n=== Range boundary test ===")
    if _XCAL_LAST_SESSION:
        beyond = _XCAL_LAST_SESSION + datetime.timedelta(days=30)
        print("  {} (beyond xcal range): trading={}".format(
            beyond, is_trading_day(beyond)))
