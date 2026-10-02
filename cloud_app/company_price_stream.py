"""Toss trade-only WebSocket for at most twelve registered company watches.

Protocol: the provider's canonical AsyncAPI (2026-10-02). Full-replace trade
declarations, acknowledged topics, bounded frames, PING and capped reconnects.
No account, order or order-event topic can be declared by this module.
"""
import datetime as dt
import json
import random
import threading
import time

from websockets.sync.client import connect

from .company_prices import Price, WATCH_LIMIT, broker_symbol, currency_for

UTC = dt.timezone.utc


def topics(symbols):
    if not isinstance(symbols, (list, tuple)) or len(symbols) > WATCH_LIMIT:
        raise ValueError('Invalid company watch batch')
    result = {}
    for symbol in symbols:
        result['trade:' + ('kr:' if currency_for(symbol) == 'KRW' else 'us:') + broker_symbol(symbol)] = symbol
    return result


def declaration(wanted):
    result = []
    for market in ('us', 'kr'):
        codes = sorted(key.split(':', 2)[2] for key in wanted if key.startswith('trade:' + market + ':'))
        if codes:
            result.append({'type': 'trade:' + market, 'codes': codes})
    return result


def parse_trade(frame, wanted, subscribed, now):
    if not isinstance(frame, str) or len(frame) > 65536:
        raise ValueError('Invalid trade frame')
    row = json.loads(frame)
    if not isinstance(row, dict):
        raise ValueError('Invalid trade message')
    topic = row.get('topic')
    if row.get('type') != 'message' or topic not in wanted or topic not in subscribed:
        return None
    data, symbol = row['data'], wanted[topic]
    if not isinstance(data, dict) or data.get('currency') != currency_for(symbol) or not isinstance(data.get('timestamp'), str):
        raise ValueError('Trade currency mismatch')
    value = Price(symbol=symbol, currency=data['currency'], value=data['price'],
                  observed_at=data['timestamp'], fetched_at=now, method='websocket')
    if not -30 <= (now - value.observed_at).total_seconds() <= 7*86400:
        raise ValueError('Trade timestamp invalid')
    return symbol, value.model_dump(mode='json')


class TossCompanyStream:
    def __init__(self, token):
        self.token = token
        self.lock = threading.Lock()
        self.changed = threading.Event()
        self.wanted, self.rows = {}, {}
        self.thread = None

    def snapshot(self, symbols):
        wanted = topics(symbols)
        with self.lock:
            if self.wanted != wanted:
                self.wanted = wanted
                self.rows = {symbol: row for symbol, row in self.rows.items() if symbol in wanted.values()}
                self.changed.set()
            if wanted and self.thread is None:
                self.thread = threading.Thread(target=self.receive, daemon=True)
                self.thread.start()
            return dict(self.rows)

    def receive(self):
        backoff = 1
        while True:
            with self.lock:
                wanted = dict(self.wanted)
            if not wanted:
                self.changed.wait(2)
                self.changed.clear()
                continue
            try:
                with connect('wss://openapi-ws.tossinvest.com/ws/v1', proxy=None,
                    additional_headers={'Authorization': 'Bearer ' + self.token()},
                    max_size=65536, max_queue=4, open_timeout=5, close_timeout=2,
                    compression=None, ping_interval=None) as socket:
                    declared, subscribed, rejected, sent_at = None, set(), set(), 0.0
                    acknowledged, declared_at, received_at = False, 0.0, time.monotonic()
                    while True:
                        with self.lock:
                            wanted = dict(self.wanted)
                        if not wanted:
                            break
                        if declared != wanted:
                            socket.send(json.dumps(declaration(wanted)))
                            declared, subscribed, rejected, sent_at = wanted, set(), set(), time.monotonic()
                            acknowledged, declared_at = False, sent_at
                        if (not acknowledged and time.monotonic()-declared_at>15) or time.monotonic()-received_at>120:
                            raise TimeoutError('Trade stream acknowledgment stalled')
                        if time.monotonic() - sent_at >= 60:
                            socket.send('PING')
                            sent_at = time.monotonic()
                        try:
                            frame = socket.recv(timeout=1)
                        except TimeoutError:
                            continue
                        if not isinstance(frame, str) or len(frame) > 65536:
                            raise ValueError('Invalid trade frame')
                        row = json.loads(frame)
                        if not isinstance(row, dict):
                            raise ValueError('Invalid trade message')
                        received_at = time.monotonic()
                        if row.get('type') == 'subscriptions':
                            accepted, refused = row.get('subscribed'), row.get('rejected')
                            if not isinstance(accepted, list) or not isinstance(refused, list) or len(accepted)+len(refused)>WATCH_LIMIT:
                                raise ValueError('Invalid subscription acknowledgment')
                            subscribed = {key for key in accepted if isinstance(key, str) and key in wanted}
                            rejected = {item['target'] for item in refused if isinstance(item, dict) and isinstance(item.get('target'), str) and item['target'] in wanted}
                            acknowledged = True
                            backoff = 1
                        elif row.get('type') == 'error':
                            # Do not repeat rejected declarations or leak messages.
                            raise ValueError('Trade stream rejected')
                        elif row.get('type') == 'message':
                            result = parse_trade(frame, wanted, subscribed-rejected, dt.datetime.now(UTC))
                            if result:
                                symbol, value = result
                                with self.lock:
                                    if symbol in self.wanted.values():
                                        previous = self.rows.get(symbol)
                                        if not previous or dt.datetime.fromisoformat(value['observed_at']) >= dt.datetime.fromisoformat(previous['observed_at']):
                                            self.rows[symbol] = value
            except Exception:
                with self.lock:
                    self.rows.clear()
                # No credential/error body enters cache. Backoff prevents loops.
                self.changed.wait(min(60, backoff) + random.random())
                self.changed.clear()
                backoff = min(60, backoff * 2)
