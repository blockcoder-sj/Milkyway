"""Bounded free stock price fallback; fixed host, no credentials or orders."""
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from .bounded_io import read_requests_json
from .company_prices import PRICE_SYMBOL, WATCH_LIMIT, Price, currency_for
from .market_broker_feed import FixedSession
from .market_catalog import Instrument
from .market_feed import parse_chart


def fetch(symbol):
    try:
        with FixedSession() as session:
            response = session.get('https://query1.finance.yahoo.com/v8/finance/chart/' + quote(symbol, safe=''),
                params={'range': '1d', 'interval': '5m'}, headers={'User-Agent': 'MilkywayPersonal/1.0'},
                timeout=(3, 8), stream=True)
            try:
                response.raise_for_status()
                payload = read_requests_json(response, maximum_bytes=256*1024)
            finally:
                response.close()
        instrument = Instrument(symbol, symbol, symbol, 'kr' if symbol.endswith(('.KS', '.KQ')) else 'us', 'stocks', '기업 시세')
        observation = parse_chart(payload, instrument, dt.datetime.now(dt.timezone.utc))
        meta = payload['chart']['result'][0]['meta']
        if meta.get('currency') != currency_for(symbol):
            raise ValueError('Stock currency mismatch')
        fields = observation.model_dump(mode='json')
        fields = {key: value for key, value in fields.items() if key in Price.model_fields}
        return symbol, Price(symbol=symbol, currency=meta['currency'], method='reference',
            delay_minutes=meta.get('exchangeDataDelayedBy'), **fields).model_dump(mode='json')
    except Exception:
        return symbol, None


def collect(payload, _configuration):
    symbols = payload.get('symbols')
    if (not isinstance(symbols, list) or not 1 <= len(symbols) <= WATCH_LIMIT
        or any(not isinstance(symbol, str) or not PRICE_SYMBOL.fullmatch(symbol) for symbol in symbols)):
        raise ValueError('Invalid registered stock batch')
    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(fetch, sorted(set(symbols))))
