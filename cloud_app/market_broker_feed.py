"""Display-only broker adapters; fixed subscriptions and bounded provider I/O."""

import datetime as dt
import json
import threading
import time
from zoneinfo import ZoneInfo

import requests
from websockets.sync.client import connect

from .bounded_io import read_requests_json
from .market_feed import Observation
from .toss_quotes import TossCredentials, TossQuoteClient

UTC = dt.timezone.utc
SEOUL = ZoneInfo('Asia/Seoul')
# KIS idxcode.mst: verified against the provider's master on 2026-09-30.
KIS_CODES = {'0001': 'kospi', '1001': 'kosdaq', '2001': 'kospi200',
             **{f'{code:04d}': f'kr_{code}' for code in (13, 8, 15, 19, 18, 21, 24, 25)}}
TOSS_CODES = {'KOSPI': 'kospi', 'KOSDAQ': 'kosdaq'}
CAPABILITIES = {'kis': tuple(KIS_CODES.values()), 'toss': (*TOSS_CODES.values(), 'usdkrw')}


class FixedSession(requests.Session):
    """Never forward credentials via redirects or environment proxies."""
    def __init__(self):
        super().__init__()
        self.trust_env = False

    def request(self, method, url, **kwargs):
        kwargs['allow_redirects'] = False
        response = super().request(method, url, **kwargs)
        if 300 <= response.status_code < 400:
            response.close()
            raise ValueError('Broker redirect rejected')
        return response


def observed(value, now):
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result > now + dt.timedelta(seconds=30):
        raise ValueError('Invalid broker timestamp')
    return result


def parse_toss_indices(payload, now):
    rows = {}
    result = payload['result']
    if not isinstance(result, list) or len(result) > 8:
        raise ValueError('Invalid indicator batch')
    for row in result:
        identity = TOSS_CODES.get(row.get('symbol'))
        if identity:
            try:
                rows[identity] = Observation(value=row['lastPrice'], observed_at=observed(row['timestamp'], now),
                                             fetched_at=now).model_dump(mode='json')
            except (ValueError, TypeError, KeyError, AttributeError):
                continue
    return rows


def parse_toss_fx(payload, now):
    row = payload['result']
    if row['baseCurrency'] != 'USD' or row['quoteCurrency'] != 'KRW':
        raise ValueError('Currency mismatch')
    start, end = observed(row['validFrom'], now), observed(row['validUntil'], now + dt.timedelta(minutes=5))
    if not start <= now < end or end - start > dt.timedelta(minutes=5):
        raise ValueError('Reference rate expired')
    return Observation(value=row['midRate'], observed_at=start, fetched_at=now, regular_end=end).model_dump(mode='json')


def parse_kis_frame(frame, now):
    if not isinstance(frame, str) or len(frame) > 65536:
        raise ValueError('Invalid frame')
    encrypted, transaction, count, values = frame.split('|', 3)
    count = int(count)
    if encrypted != '0' or transaction != 'H0UPCNT0' or not 1 <= count <= 20:
        raise ValueError('Unexpected subscription')
    fields = values.split('^')
    if len(fields) != count * 30:
        raise ValueError('Invalid field count')
    rows = {}
    for offset in range(0, len(fields), 30):
        raw = fields[offset:offset + 30]
        identity = KIS_CODES.get(raw[0])
        if not identity:
            continue
        local = now.astimezone(SEOUL)
        clock = dt.datetime.strptime(raw[1], '%H%M%S').time()
        timestamp = dt.datetime.combine(local.date(), clock, SEOUL)
        # Frames have no date. Only accept a near-current clock during the same day.
        if abs((timestamp - now).total_seconds()) > 30:
            continue
        value, difference = float(raw[2]), abs(float(raw[4]))
        if raw[3] not in {'1', '2', '3', '4', '5'}:
            continue
        difference *= -1 if raw[3] in {'4', '5'} else 0 if raw[3] == '3' else 1
        rows[identity] = Observation(value=value, previous_close=value - difference,
            day_high=float(raw[11]) or None, day_low=float(raw[12]) or None,
            observed_at=timestamp, fetched_at=now).model_dump(mode='json')
    return rows


class TossDisplay:
    def __init__(self, configuration):
        self.client = TossQuoteClient(TossCredentials(configuration['key'], configuration['secret']))
        self.client.session.close()
        self.client.session = FixedSession()
        self.fx = None
        self.next_fx = 0
        self.retry_at = 0
        self.auth_lock = threading.Lock()
        self.next_indices = self.next_stocks = 0
        self.indices = {}
        self.stock_rows = {}
        self.stock_symbols = ()
        from .company_price_stream import TossCompanyStream
        self.company_stream = TossCompanyStream(self.stock_token)

    def stock_token(self):
        with self.auth_lock:
            return self.client._headers()['Authorization'].removeprefix('Bearer ')

    def request(self, path, params):
        with self.auth_lock:
            headers = self.client._headers()
        response = self.client.session.get(self.client.base_url + path, params=params,
            headers=headers, stream=True, timeout=(3, 5))
        try:
            self.client._raise_for_status(response)
            result = read_requests_json(response, maximum_bytes=64 * 1024)
            self.client._raise_for_status(response, result)
            return result
        finally:
            response.close()

    def snapshot(self, symbols=()):
        rows = dict(self.indices)
        if time.monotonic() >= max(self.next_indices, self.retry_at):
            self.next_indices = time.monotonic() + 15
            try:
                self.indices = parse_toss_indices(self.request('/api/v1/market-indicators/prices',
                    {'symbols': 'KOSPI,KOSDAQ'}), dt.datetime.now(UTC))
                rows.update(self.indices)
            except (ValueError, TypeError, KeyError, AttributeError, RuntimeError, requests.RequestException):
                self.retry_at = time.monotonic() + 60
        if time.monotonic() >= self.next_fx:
            self.next_fx = time.monotonic() + 60
            self.fx = None
            try:
                self.fx = parse_toss_fx(self.request('/api/v1/exchange-rate',
                    {'baseCurrency': 'USD', 'quoteCurrency': 'KRW'}), dt.datetime.now(UTC))
            except (ValueError, TypeError, KeyError, AttributeError, RuntimeError, requests.RequestException):
                pass
        if self.fx:
            rows['usdkrw'] = self.fx
        from .company_prices import Price, broker_symbol, currency_for, WATCH_LIMIT
        if len(symbols) > WATCH_LIMIT:
            raise ValueError('Too many watched stocks')
        selected = {broker_symbol(symbol): symbol for symbol in symbols}
        # REST supplies the initial snapshot; the stream starts at the next trade.
        if selected and (time.monotonic() >= self.next_stocks or tuple(sorted(symbols)) != self.stock_symbols):
            self.next_stocks = time.monotonic() + 15
            self.stock_symbols = tuple(sorted(symbols))
            try:
                values = self.request('/api/v1/prices', {'symbols': ','.join(sorted(selected))})['result']
                if not isinstance(values, list) or len(values) > WATCH_LIMIT:
                    raise ValueError('Invalid company price batch')
                for value in values:
                    symbol = selected.get(value.get('symbol'))
                    if symbol and value.get('currency') == currency_for(symbol):
                        try:
                            self.stock_rows[symbol] = Price(symbol=symbol, currency=value['currency'],
                                value=value['lastPrice'], observed_at=value.get('timestamp'),
                                fetched_at=dt.datetime.now(UTC), method='poll').model_dump(mode='json')
                        except (ValueError, TypeError):
                            continue
            except (ValueError, TypeError, KeyError, AttributeError, RuntimeError, requests.RequestException):
                self.next_stocks = time.monotonic() + 60
        streamed = self.company_stream.snapshot(list(symbols))
        companies = {symbol: value for symbol, value in self.stock_rows.items() if symbol in symbols}
        for symbol, value in streamed.items():
            # A late old frame cannot replace a newer REST trade.
            previous = companies.get(symbol)
            if not previous or not previous.get('observed_at') or dt.datetime.fromisoformat(value['observed_at']) >= dt.datetime.fromisoformat(previous['observed_at']):
                companies[symbol] = value
        self.stock_rows = {symbol: value for symbol, value in self.stock_rows.items() if symbol in symbols}
        rows['company_prices'] = companies
        return rows


class KisDisplay:
    """A bounded fixed stream inside the killable provider child process."""
    def __init__(self, configuration):
        self.configuration = configuration
        self.lock = threading.Lock()
        self.rows = {}
        self.last_progress = time.monotonic()
        self.approval = None
        self.approval_until = 0
        threading.Thread(target=self.receive, daemon=True).start()

    def snapshot(self):
        if time.monotonic() - self.last_progress > 90:
            raise RuntimeError("Broker stream stalled")
        with self.lock:
            return dict(self.rows)

    def receive(self):
        # Official KIS stream uses ws, not TLS. Only a quote-subscription approval
        # key is sent there; app credentials travel solely over verified HTTPS.
        # This untrusted display feed is never admitted to the paper ledger.
        while True:
            try:
                if time.monotonic() >= self.approval_until:
                    with FixedSession() as session:
                        response = session.post('https://openapi.koreainvestment.com:9443/oauth2/Approval',
                            json={'grant_type': 'client_credentials', 'appkey': self.configuration['key'],
                                  'secretkey': self.configuration['secret']}, stream=True, timeout=(3, 5))
                        try:
                            response.raise_for_status()
                            payload = read_requests_json(response, maximum_bytes=65536)
                        finally:
                            response.close()
                    key = payload.get('approval_key')
                    if not isinstance(key, str) or not 10 <= len(key) <= 512:
                        raise ValueError('Invalid approval')
                    self.approval, self.approval_until = key, time.monotonic() + 23 * 3600
                with connect('ws://ops.koreainvestment.com:21000/tryitout', proxy=None,
                             max_size=65536, max_queue=4, open_timeout=5, close_timeout=2,
                             compression=None, ping_interval=None) as socket:
                    for code in KIS_CODES:
                        socket.send(json.dumps({'header': {'approval_key': self.approval, 'custtype': 'P',
                            'tr_type': '1', 'content-type': 'utf-8'},
                            'body': {'input': {'tr_id': 'H0UPCNT0', 'tr_key': code}}}))
                        time.sleep(0.1)
                    while True:
                        frame = socket.recv(timeout=60)
                        self.last_progress = time.monotonic()
                        if isinstance(frame, str) and frame.startswith('{'):
                            message = json.loads(frame)
                            if message.get('header', {}).get('tr_id') == 'PINGPONG':
                                socket.pong(frame.encode())
                            elif message.get('body', {}).get('rt_cd') not in (None, '0'):
                                raise ValueError('Subscription rejected')
                        else:
                            rows = parse_kis_frame(frame, dt.datetime.now(UTC))
                            with self.lock:
                                self.rows.update(rows)
            except Exception:
                # No raw responses, credentials, or exception URLs enter logs/cache.
                with self.lock:
                    self.rows.clear()
                self.approval_until = 0
                self.last_progress = time.monotonic()
                time.sleep(60)


_adapter = None


def collect_broker(_payload, configuration):
    global _adapter
    if _adapter is None:
        if configuration['provider'] == 'toss' and configuration['environment'] == 'live':
            _adapter = TossDisplay(configuration)
        elif configuration['provider'] == 'kis' and configuration['environment'] == 'real':
            _adapter = KisDisplay(configuration)
        else:
            return {}
    if configuration['provider'] == 'toss':
        return _adapter.snapshot(_payload.get('company_symbols', []))
    return _adapter.snapshot()
