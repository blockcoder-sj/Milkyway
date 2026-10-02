"""Registered-company display prices. No provider I/O or trading writes in HTTP.

Short-lived watches use the public graph's SQLite transaction; quote snapshots
are bounded caches populated only by market-data. Broker snapshots are admitted
only for the owner's current connection identity.
"""
import datetime as dt
import re
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from .bounded_io import read_bounded_json
from .company_graph import CompanyGraph
from .market_service import _write_cache

UTC = dt.timezone.utc
WATCH_SECONDS = 90
WATCH_LIMIT = 12
PUBLIC_REFRESH_SECONDS = 60
PRICE_SYMBOL = re.compile(r'(?:[A-Z][A-Z0-9.-]{0,19}|\d{6}\.(?:KS|KQ))')
SOURCE_URLS = {'toss': 'https://openapi.tossinvest.com/openapi-docs/overview.md',
               'kis': 'https://apiportal.koreainvestment.com/'}


class Price(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    symbol: str = Field(pattern=r'^(?:[A-Z][A-Z0-9.-]{0,19}|\d{6}\.(?:KS|KQ))$')
    currency: str = Field(pattern=r'^(USD|KRW)$')
    value: float = Field(gt=0, le=1e12)
    previous_close: float | None = Field(default=None, gt=0, le=1e12)
    observed_at: AwareDatetime | None = None
    fetched_at: AwareDatetime
    regular_start: AwareDatetime | None = None
    regular_end: AwareDatetime | None = None
    method: str = Field(pattern=r'^(websocket|poll|reference)$')
    delay_minutes: int | None = Field(default=None, ge=0, le=1440)

    @field_validator('value', 'previous_close', 'delay_minutes', mode='before')
    @classmethod
    def reject_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError('Boolean is not a price')
        return value


def broker_symbol(symbol):
    if not isinstance(symbol, str) or not PRICE_SYMBOL.fullmatch(symbol):
        raise ValueError('Unsupported stock symbol')
    return symbol[:6] if re.fullmatch(r'\d{6}\.(KS|KQ)', symbol) else symbol


def currency_for(symbol):
    broker_symbol(symbol)
    return 'KRW' if symbol.endswith(('.KS', '.KQ')) else 'USD'


def resolve_symbol(settings, key, symbol=None):
    from .company_entities import get_entity
    entity = get_entity(settings, key)
    selected = symbol or next((value for value in entity['symbols'] if PRICE_SYMBOL.fullmatch(value)), None)
    if not selected:
        return None
    if selected not in entity['symbols'] or not PRICE_SYMBOL.fullmatch(selected):
        raise HTTPException(404, '이 기업에 등록된 상장 종목 시세만 조회할 수 있습니다')
    return selected


def _watches(db):
    db.execute('CREATE TABLE IF NOT EXISTS company_price_watches ('
               'owner_id TEXT NOT NULL, symbol TEXT NOT NULL, expires_at TEXT NOT NULL, '
               'PRIMARY KEY(owner_id,symbol))')


def watch(settings, key, owner_id, symbol=None, now=None):
    selected = resolve_symbol(settings, key, symbol)
    if selected is None:
        return {'status': 'unlisted', 'symbol': None}
    now = now or dt.datetime.now(UTC)
    with CompanyGraph(settings).connection() as db:
        _watches(db)
        # Serialize admission and upsert. Expired display watches are disposable.
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM company_price_watches WHERE expires_at<=?', (now.isoformat(),))
        exists = db.execute('SELECT 1 FROM company_price_watches WHERE owner_id=? AND symbol=?',
                            (owner_id, selected)).fetchone()
        if not exists and db.execute('SELECT COUNT(*) FROM company_price_watches').fetchone()[0] >= WATCH_LIMIT:
            raise HTTPException(429, '동시에 열어 둔 기업 시세가 많습니다. 잠시 후 다시 확인해 주세요')
        db.execute('INSERT INTO company_price_watches VALUES(?,?,?) ON CONFLICT(owner_id,symbol) '
                   'DO UPDATE SET expires_at=excluded.expires_at',
                   (owner_id, selected, (now + dt.timedelta(seconds=WATCH_SECONDS)).isoformat()))
    return {'status': 'watching', 'symbol': selected, 'expires_seconds': WATCH_SECONDS}


def active(settings, owner_id=None, now=None):
    now = now or dt.datetime.now(UTC)
    with CompanyGraph(settings).connection() as db:
        _watches(db)
        query = 'SELECT symbol FROM company_price_watches WHERE expires_at>?'
        args = [now.isoformat()]
        if owner_id is not None:
            query += ' AND owner_id=?'
            args.append(owner_id)
        rows = db.execute(query + ' ORDER BY symbol LIMIT ?', (*args, WATCH_LIMIT)).fetchall()
    return [row[0] for row in rows if PRICE_SYMBOL.fullmatch(row[0])]


def cache_path(settings):
    if not settings.personal_local_mode or settings.production:
        raise ValueError('Company display prices require personal local mode')
    return settings.dataset_dir.parent / 'company-prices.json'


def read_public(settings):
    try:
        value = read_bounded_json(cache_path(settings), maximum_bytes=128 * 1024)
        if (value.get('version') == 1 and isinstance(value.get('items'), dict) and len(value['items']) <= WATCH_LIMIT
            and all(isinstance(item, dict) and isinstance(item.get('error'), (str, type(None)))
                    for item in value['items'].values())):
            return value
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return {}


def refresh_public(settings, provider):
    import time
    symbols = active(settings)
    if not symbols:
        return None
    previous = read_public(settings).get('items', {})
    try:
        result = provider.run({'symbols': symbols}, {}, deadline=time.monotonic() + 35)
        if not isinstance(result, dict):
            raise ValueError('Invalid company price batch')
    except (OSError, ValueError, TypeError, RuntimeError, TimeoutError):
        result = {}
    items = {}
    for symbol in symbols:
        try:
            quote = Price.model_validate(result[symbol])
            if quote.symbol != symbol or quote.currency != currency_for(symbol) or quote.method != 'reference':
                raise ValueError('Wrong stock price identity')
            items[symbol] = {'price': quote.model_dump(mode='json'), 'error': None}
        except (ValueError, TypeError, KeyError):
            items[symbol] = {'price': previous.get(symbol, {}).get('price'), 'error': '참고 시세 수신·검증 실패'}
    _write_cache(cache_path(settings), {'version': 1, 'items': items,
                                     'attempted_at': dt.datetime.now(UTC).isoformat()})
    return len(items)


def valid_price(value, symbol, now, maximum_age=180):
    quote = Price.model_validate(value)
    if (quote.symbol != symbol or quote.currency != currency_for(symbol)
        or not -30 <= (now - quote.fetched_at).total_seconds() <= maximum_age
        or (quote.observed_at is not None and not -30 <= (now - quote.observed_at).total_seconds() <= 7*86400)):
        raise ValueError('Stock price expired or mismatched')
    return quote


def snapshot(settings, key, symbol=None, *, connection_identity=None, now=None):
    selected = resolve_symbol(settings, key, symbol)
    now = now or dt.datetime.now(UTC)
    if selected is None:
        return {'symbol': None, 'value': None, 'status': 'unlisted', 'note': '비상장·시세 종목 미등록 기업'}
    public_item = read_public(settings).get('items', {}).get(selected, {})
    reference = None
    try:
        reference = valid_price(public_item.get('price'), selected, now, maximum_age=7*86400)
        if reference.method != 'reference':
            reference = None
    except (ValueError, TypeError):
        pass
    from .market_broker import read_cache
    broker = read_cache(settings, connection_identity)
    quote, source, url, error = reference, 'Yahoo Finance', 'https://finance.yahoo.com/quote/' + selected + '/', public_item.get('error')
    if reference and (now - reference.fetched_at).total_seconds() > 180:
        error = '최근 참고 시세 수신이 지연되었습니다'
    provider = broker.get('provider')
    if provider in SOURCE_URLS:
        try:
            candidate = valid_price(broker.get('companies', {}).get(selected), selected, now)
            if (now - candidate.fetched_at).total_seconds() > 45:
                raise ValueError('Broker price expired')
            quote, source, url, error = candidate, '토스증권' if provider == 'toss' else '한국투자증권', SOURCE_URLS[provider], None
        except (ValueError, TypeError, AttributeError):
            pass
    if quote is None:
        return {'symbol': selected, 'currency': currency_for(selected), 'value': None,
                'status': 'awaiting', 'note': '시장 데이터 수집을 기다리고 있습니다'}
    value = quote.model_dump(mode='json')
    age = (now - quote.observed_at).total_seconds() if quote.observed_at else None
    status = 'realtime' if quote.method == 'websocket' and age is not None and age <= 60 else 'polled' if quote.method == 'poll' and age is not None and age <= 60 else 'reference'
    if age is not None and age > 60 and quote.method != 'reference':
        status = 'last_trade'
    if error:
        status = 'stale'
    elif quote.method == 'reference' and quote.regular_start and quote.regular_end:
        status = 'delayed' if quote.regular_start <= now <= quote.regular_end else 'closed'
    baseline_source = source if quote.previous_close else None
    baseline_url = url if quote.previous_close else None
    # Same local trading day only: a previous-day Yahoo session cannot supply
    # today's premarket baseline. The other provider's baseline is labelled.
    if (not quote.previous_close and reference and reference.previous_close and quote.observed_at and reference.observed_at
        and not public_item.get('error') and (now-reference.fetched_at).total_seconds()<=180):
        zone = ZoneInfo('Asia/Seoul' if quote.currency == 'KRW' else 'America/New_York')
        if quote.observed_at.astimezone(zone).date() == reference.observed_at.astimezone(zone).date():
            value['previous_close'] = reference.previous_close
            baseline_source, baseline_url = 'Yahoo Finance · 전일 종가', 'https://finance.yahoo.com/quote/' + selected + '/'
    previous = value['previous_close']
    return {**value, 'status': status, 'is_realtime': status == 'realtime', 'source': source,
            'source_url': url, 'comparison_source': baseline_source, 'comparison_source_url': baseline_url,
            'change': quote.value - previous if previous else None,
            'change_pct': (quote.value / previous - 1)*100 if previous else None,
            'error': error, 'refresh_seconds': 2}
