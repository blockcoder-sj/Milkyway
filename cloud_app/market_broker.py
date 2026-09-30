"""Single-owner broker display cache. Never writes execution quotes or orders."""

import datetime as dt
import hashlib
import json
import time

from sqlalchemy import select

from .bounded_io import read_bounded_json
from .database import MarketDataConnection, User
from .market_broker_feed import CAPABILITIES, collect_broker
from .market_data_credentials import decrypt_market_credential
from .market_feed import Observation
from .provider_process import ProviderProcess

_provider = ProviderProcess(collect_broker)
UTC = dt.timezone.utc


def identity(connection):
    if connection is None:
        return None
    return hashlib.sha256(json.dumps([connection.user_id, connection.provider, connection.environment,
        str(connection.updated_at)]).encode()).hexdigest()


def owner_connection(session):
    users = session.scalars(select(User).limit(2)).all()
    return session.get(MarketDataConnection, users[0].id) if len(users) == 1 and users[0].active else None


def cache_path(settings):
    if not settings.personal_local_mode or settings.production or settings.credential_backend != 'local':
        raise ValueError('Broker display requires personal credential custody')
    return settings.dataset_dir.parent / 'market-broker.json'


def read_cache(settings, connection_identity):
    if not connection_identity:
        return {}
    try:
        cache = read_bounded_json(cache_path(settings), maximum_bytes=256 * 1024)
        if (not isinstance(cache, dict) or cache.get('identity') != connection_identity
                or cache.get('provider') not in {'kis', 'toss', None} or not isinstance(cache.get('items'), dict)):
            return {}
        return cache
    except (ValueError, OSError, TypeError, AttributeError):
        return {}


def refresh_broker(settings, session):
    from .market_service import _write_cache
    path = cache_path(settings)
    connection = owner_connection(session)
    provider = connection.provider if connection else None
    cache = {'identity': identity(connection), 'provider': provider, 'items': {},
             'attempted_at': dt.datetime.now(UTC).isoformat()}
    if connection is None or provider not in CAPABILITIES or (provider == 'kis' and connection.environment != 'real'):
        _provider.close()
    else:
        try:
            configuration = {'provider': provider, 'environment': connection.environment,
                             'identity': cache['identity']}
            for field, encrypted, label in (('key', connection.encrypted_api_key, 'App Key'),
                                             ('secret', connection.encrypted_api_secret, 'App Secret')):
                configuration[field] = decrypt_market_credential(encrypted, settings,
                    owner_id=connection.user_id, provider=provider, environment=connection.environment, label=label)
            collected = _provider.run({}, configuration, deadline=time.monotonic() + (20 if provider == 'toss' else 5))
            for key, value in collected.items():
                if key in CAPABILITIES[provider]:
                    try:
                        cache['items'][key] = Observation.model_validate(value).model_dump(mode='json')
                    except (ValueError, TypeError):
                        continue
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError, OSError, TimeoutError):
            _provider.close()
            cache['items'] = {}
    _write_cache(path, cache)
    return provider


def project_broker(row, broker, now):
    provider = broker.get('provider')
    if row['id'] not in CAPABILITIES.get(provider, ()):
        return
    try:
        observation = Observation.model_validate(broker.get('items', {}).get(row['id']))
        age = (now - observation.observed_at).total_seconds()
        fetched_age = (now - observation.fetched_at).total_seconds()
        limit = 30 if provider == 'kis' else 90 if row['id'] == 'usdkrw' else 60
        observation_limit = 300 if provider == 'toss' and row['id'] == 'usdkrw' else limit
        expired_fx = row['id'] == 'usdkrw' and (observation.regular_end is None or now >= observation.regular_end)
        if expired_fx or not -30 <= age <= observation_limit or not -30 <= fetched_age <= limit:
            raise ValueError('Broker quote stale')
        row.update(observation.model_dump(mode='json'))
        row.update(change=None, change_pct=None, error=None, source='한국투자증권' if provider == 'kis' else '토스증권',
                   source_url='https://apiportal.koreainvestment.com/' if provider == 'kis' else 'https://developers.tossinvest.com/docs/market-data',
                   status='realtime' if provider == 'kis' else 'reference' if row['id'] == 'usdkrw' else 'polled',
                   is_realtime=provider == 'kis')
        if observation.previous_close is not None:
            row['change'] = observation.value - observation.previous_close
            row['change_pct'] = row['change'] / observation.previous_close * 100
    except (ValueError, TypeError, AttributeError):
        row['fallback_reason'] = '증권사 시세 미수신 또는 유효 시간 초과 · Yahoo Finance로 보완'
