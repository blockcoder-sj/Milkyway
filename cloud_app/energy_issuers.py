"""Exact public issuer research roster; this is not a GICS security master.

The SEC exchange file establishes issuer/ticker identity, not business sector.
An original filing receipt establishes collection, not completed editorial work.
Official disclosed sector rows always take precedence over navigation hints.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .bounded_io import read_bounded_json
from .company_schemas import Source

GROUPS = {
    'pending': '사업 분류 조사 중', 'integrated': '통합 원유·가스',
    'upstream': '탐사·생산', 'refining': '정유·제품',
    'gas-infrastructure': '가스·NGL·원유 인프라', 'lng': 'LNG',
    'fuel-distribution': '연료 유통', 'compression': '압축·분산 발전',
    'nuclear-fuel': '원자력 연료 · 산업 연결', 'coal-minerals': '석탄·광물',
    'digital-power': '디지털 인프라·전력 · 산업 연결',
    'diversified': '복합 사업 · 산업 연결', 'utility': '가스 유틸리티 · 산업 연결',
    'oilfield-services': '시추·완결·유정 서비스',
    'equipment': '유전 장비·도구·인공 채유',
    'proppant-logistics': '파쇄 모래·현장 물류',
    'drilling': '계약 시추·리그',
    'shipping': '원유·제품·가스 해상 운송 · 산업 연결',
    'mineral-royalty': '광물권·로열티·순이익 권리',
    'surface-land': '토지·용수·생산수 사용권',
}


class ImmutableSource(Source):
    model_config = ConfigDict(extra='forbid', frozen=True)


class Issuer(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    symbol: str = Field(pattern=r'^[A-Z][A-Z0-9.-]{0,19}$')
    name: str = Field(min_length=1, max_length=120)
    cik: str | None = Field(default=None, pattern=r'^[1-9][0-9]{0,9}$')
    exchange: str = Field(min_length=1, max_length=40)
    group: Literal['pending', 'integrated', 'upstream', 'refining',
                   'gas-infrastructure', 'lng', 'fuel-distribution', 'compression',
                   'nuclear-fuel', 'coal-minerals', 'digital-power', 'diversified', 'utility',
                   'oilfield-services', 'equipment', 'proppant-logistics', 'drilling', 'shipping',
                   'mineral-royalty', 'surface-land']
    scope: Literal['research', 'context']
    sector_hint: Literal['us_10', 'us_55'] = 'us_10'
    report_source: ImmutableSource
    identity_source: ImmutableSource | None = None


class Registry(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    checked_at: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    identity_source: ImmutableSource
    rows: tuple[Issuer, ...] = Field(max_length=500)


@lru_cache(maxsize=1)
def registry():
    value = Registry.model_validate(read_bounded_json(
        Path(__file__).with_suffix('.json'), maximum_bytes=1024 * 1024))
    if len({row.symbol for row in value.rows}) != len(value.rows):
        raise ValueError('Duplicate issuer research symbol')
    return value


@lru_cache(maxsize=1)
def _by_symbol():
    return {row.symbol: row for row in registry().rows}


def issuer(symbol):
    return _by_symbol().get(symbol)


def navigation(symbol, disclosed_sector=None):
    row = issuer(symbol)
    if row is None:
        return None
    return {'sector': disclosed_sector or row.sector_hint, 'name': row.name}


def company_row(symbol, sector, disclosed_sector=None):
    row = issuer(symbol)
    if row is None or (disclosed_sector or row.sector_hint) != sector:
        return None
    return dict(symbol=row.symbol, name=row.name, market_cap=None, currency='USD',
        displayed_share_pct=None, source=row.report_source.label[:80], url=row.report_source.url,
        directory_basis=('산업 연결 기업 · 공식 GICS 분류와 별도' if row.scope == 'context'
                         else '발행기업 조사 목록 · 공식 GICS 분류와 별도'),
        directory_group=GROUPS[row.group])


def augment(rows, identity, view, *, maximum=1100):
    """Append exact research issuers, without turning their hints into classifications."""
    if identity != 'us_10':
        return rows, 0, 0
    if not 1 <= maximum <= 1100:
        raise ValueError('Invalid company directory bound')
    disclosed = {row.symbol: row.sector for row in view.rows}
    result = [dict(row) for row in rows]
    known = {row['symbol'] for row in result}
    for row in result:
        entry = issuer(row['symbol'])
        if entry:
            row['directory_group'] = GROUPS[entry.group]
            row['directory_basis'] = ('산업 연결 기업 · 공식 GICS 분류와 별도' if entry.scope == 'context'
                                      else '발행기업 조사 목록 · 공식 GICS 분류와 별도')
    added = omitted = 0
    for entry in registry().rows:
        if entry.symbol in known or (disclosed.get(entry.symbol) or entry.sector_hint) != identity:
            continue
        if len(result) >= maximum:
            omitted += 1
            continue
        result.append(company_row(entry.symbol, identity, disclosed.get(entry.symbol)))
        added += 1
    # Newly identified issuers have no synchronous quote call. A partial sum
    # cannot be the denominator of a complete research-directory weight.
    if any(row.get('market_cap') is None for row in result):
        result = [{**row, 'displayed_share_pct': None} for row in result]
    return result, added, omitted


def summary():
    value = registry()
    return dict(checked_at=value.checked_at, research_issuers=len(value.rows),
        method='SEC 현행 종목·거래소와 발행기업 공시를 연결한 조사 목록입니다. '
               'OTC 종목은 기업 공식 IR로 확인합니다. 사업별 탐색 그룹은 GICS 코드가 아니며 '
               '자료 수집·목록 등재를 조사 완료로 계산하지 않습니다.',
        identity_source=value.identity_source.model_dump(mode='json'))
