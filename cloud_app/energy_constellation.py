"""Bounded, local Energy ecosystem snapshot. No collection or AI calls.

Company claims, editorial grouping and analytical exposure paths remain distinct.
Only exact stored aliases identify legal entities. The scope is the issuer roster
and its direct neighbours, including known links between those neighbours.
"""
from copy import deepcopy
from hashlib import sha256
import threading
import time

from fastapi import HTTPException
from .company_context import business_context
from .company_graph import CompanyGraph
from .company_provenance import forbidden
from .company_relation_presentation import evidence_order
from .company_schemas import Source
from .company_research_catalog import PUBLIC_COMPANIES, PRIVATE_COMPANIES, REGISTERED_TICKERS
from .company_catalog import editorial_for
from .energy_guide import SECTIONS, SOURCES
from .energy_issuers import GROUPS, registry

MAX_RECORDS = 40000
MAX_NODES = 8000
_lock = threading.Lock()
_cached = None


def _chunks(values):
    values = list(values)
    for start in range(0, len(values), 350):
        yield values[start:start + 350]


def _origin(value):
    if not value or forbidden(value):
        return None
    try:
        return Source.model_validate({key: value[key] for key in ('label', 'url', 'as_of', 'level') if key in value}).model_dump()
    except ValueError:
        return None


def _guide_source(key):
    item = SOURCES[key]
    return dict(label=item['label'], url=item['url'], level='primary', as_of='열람 2026-10-02')


def _build(graph):
    entries = registry().rows
    symbols = {item.symbol for item in entries}
    nodes, edges = {}, {}
    nodes['energy'] = dict(id='energy', name='에너지 생태계', kind='sector',
                          description='확정한 213개 기업·직접 연결 기업·사업 요소·공개 근거의 분석용 영향 경로.', sources=[])

    def edge(a, b, kind, detail, source, analytical=False, identity=None):
        source = _origin(source)
        if not source or a == b:
            return
        analytical = analytical or (kind == 'competitor' and '공시 사업 범위를 대조한 비교 대상' in detail)
        key = identity or sha256((a + '|' + b + '|' + kind + '|' + str(analytical)).encode()).hexdigest()[:24]
        if key not in edges:
            edges[key] = dict(id=key, source=a, target=b, kind=kind, detail=detail[:700],
                              citation=source, analytical=analytical, evidence_count=1)
        elif edges[key]['citation'] != source or edges[key]['detail'] != detail:
            edges[key]['evidence_count'] += 1

    raw = []
    aliases = {}
    entities = {}
    ticker_ids = {}
    catalog = {item.symbol: editorial_for(item.symbol) for item in entries}
    lookup = {}
    def identities(value):
        result = []
        symbol = value.get('symbol') or REGISTERED_TICKERS.get(value.get('registry_id'))
        for namespace, alias in (('ticker', symbol), ('wikidata', value.get('entity_id')), ('registry', value.get('registry_id'))):
            if alias:
                result.append((namespace, alias))
        source = _origin(value.get('source'))
        if source:
            result.append(('reference', sha256((source['url'] + '|' + value['name'].casefold().strip()).encode()).hexdigest()))
        return result
    wanted = set()
    for symbol, profile in catalog.items():
        wanted.add(('ticker', symbol))
        for relation in profile.get('relations', []):
            wanted.update(identities(relation))
    # Private profiles add only links whose endpoints are already in the direct
    # neighbourhood. They never expand this snapshot into an unlimited graph.
    for key, profile in PRIVATE_COMPANIES.items():
        wanted.update(identities(dict(profile, registry_id=key)))
        for relation in profile.get('relations', []):
            wanted.update(identities(relation))
    with graph.connection() as db:
        db.execute('BEGIN')
        for namespace in ('ticker', 'wikidata', 'registry', 'reference'):
            for chunk in _chunks(sorted(alias for ns, alias in wanted if ns == namespace)):
                marks = ','.join('?' for _ in chunk)
                for row in db.execute(f'SELECT value,entity_id FROM company_aliases WHERE namespace=? AND value IN ({marks})', [namespace, *chunk]):
                    lookup[(namespace, row['value'])] = row['entity_id']
        for chunk in _chunks(sorted(symbols)):
            marks = ','.join('?' for _ in chunk)
            for row in db.execute(f"SELECT value,entity_id FROM company_aliases WHERE namespace='ticker' AND value IN ({marks})", chunk):
                ticker_ids[row['value']] = row['entity_id']
        roots = set(ticker_ids.values())
        # First determine the complete direct neighbourhood; never silently
        # apply each company page's 400-record limit to the sector map.
        seen = set()
        for chunk in _chunks(sorted(roots)):
            marks = ','.join('?' for _ in chunk)
            query = f"""SELECT r.*,s.label,s.url,s.as_of,s.level FROM company_relations r
                        JOIN company_sources s ON s.id=r.source_id
                        WHERE r.subject_id IN ({marks}) OR r.object_id IN ({marks}) LIMIT ?"""
            for row in db.execute(query, [*chunk, *chunk, MAX_RECORDS + 1]):
                if row['id'] not in seen:
                    seen.add(row['id'])
                    if _origin(dict(row)):
                        raw.append(dict(row))
            if len(seen) > MAX_RECORDS:
                raise HTTPException(413, '관계 원문이 표시 범위를 초과했습니다. 자료를 나눠 검토해야 합니다.')
        ids = roots | {row[field] for row in raw for field in ('subject_id', 'object_id', 'owner_id')}
        if len(ids) > MAX_NODES:
            raise HTTPException(413, '연결 기업이 표시 범위를 초과했습니다. 자료를 나눠 검토해야 합니다.')
        # Include already recorded neighbour-to-neighbour connections, without
        # an unbounded recursive expansion into unrelated sectors.
        for chunk in _chunks(sorted(ids)):
            marks = ','.join('?' for _ in chunk)
            query = f"""SELECT r.*,s.label,s.url,s.as_of,s.level FROM company_relations r
                        JOIN company_sources s ON s.id=r.source_id
                        WHERE r.subject_id IN ({marks}) LIMIT ?"""
            scanned = list(db.execute(query, [*chunk, MAX_RECORDS + 1]))
            if len(scanned) > MAX_RECORDS:
                raise HTTPException(413, '연결 자료가 표시 범위를 초과했습니다.')
            for row in scanned:
                if row['object_id'] in ids and row['owner_id'] in ids and row['id'] not in seen:
                    seen.add(row['id'])
                    if _origin(dict(row)):
                        raw.append(dict(row))
            if len(seen) > MAX_RECORDS:
                raise HTTPException(413, '관계 원문이 표시 범위를 초과했습니다.')
        for chunk in _chunks(sorted(ids)):
            marks = ','.join('?' for _ in chunk)
            for row in db.execute(f'SELECT id,name,sector FROM company_entities WHERE id IN ({marks}) AND redirect_to IS NULL', chunk):
                entities[row['id']] = dict(row)
            for row in db.execute(f'SELECT entity_id,namespace,value FROM company_aliases WHERE entity_id IN ({marks}) ORDER BY namespace,value', chunk):
                aliases.setdefault(row['entity_id'], []).append(dict(row))
    for key, item in entities.items():
        values = aliases.get(key, [])
        symbol = next((a['value'] for a in values if a['namespace'] == 'ticker'), None)
        registered = next((a['value'] for a in values if a['namespace'] == 'registry'), None)
        context = business_context(symbol, registered)
        nodes[key] = dict(id=key, name=item['name'], symbol=symbol, kind='company', sector=item['sector'],
                          description=context['detail'] if context else '원문에 이름과 관계가 등록된 항목입니다. 별도 사업 분석은 확인하지 못했습니다.',
                          scope='role_context' if context else 'source_only',
                          sources=[context['source']] if context else [])
    for row in sorted(raw, key=lambda row: evidence_order(row, aliases)):
        a, b, kind = row['subject_id'], row['object_id'], row['kind']
        if a not in nodes or b not in nodes:
            continue
        # Canonical direction: supplier -> customer and parent -> subsidiary.
        if kind in ('supplier', 'parent', 'owner'):
            a, b = b, a
            kind = {'supplier': 'customer', 'parent': 'subsidiary', 'owner': 'holding'}[kind]
        elif kind in ('partner', 'competitor', 'transaction') and a > b:
            a, b = b, a
        edge(a, b, kind, row['detail'], {k: row[k] for k in ('label', 'url', 'as_of', 'level')})
    def resolve(value):
        candidates = identities(value)
        for identity in candidates:
            if identity in lookup:
                return lookup[identity]
        if not candidates:
            return None
        namespace, alias = candidates[0]
        return 'catalog:' + namespace + ':' + alias

    def catalog_relation(owner, relation, expand=False):
        origin = _origin(relation.get('source'))
        if not origin:
            return
        target = resolve(relation)
        if not target or not expand and target not in nodes:
            return
        if target not in nodes:
            symbol = relation.get('symbol') or REGISTERED_TICKERS.get(relation.get('registry_id'))
            context = business_context(symbol, relation.get('registry_id'))
            nodes[target] = dict(id=target, name=relation['name'], symbol=symbol, kind='company',
                description=context['detail'] if context else '원문에 등록된 관계입니다. 별도 사업 분석은 확보하지 못했습니다.',
                scope='role_context' if context else 'source_only', sources=[context['source']] if context else [origin])
        a, b, kind = owner, target, relation['kind']
        if kind in ('supplier', 'parent', 'owner'):
            a, b = b, a
            kind = {'supplier': 'customer', 'parent': 'subsidiary', 'owner': 'holding'}[kind]
        elif kind in ('partner', 'competitor', 'transaction') and a > b:
            a, b = b, a
        edge(a, b, kind, relation.get('detail', ''), origin)

    # Reviewed catalogue claims are visible even on a fresh PC before any
    # company page has been opened. This does not seed or alter the database.
    for item in entries:
        key = ticker_ids.get(item.symbol, 'catalog:ticker:' + item.symbol)
        nodes.setdefault(key, dict(id=key, name=PUBLIC_COMPANIES[item.symbol]['name'], kind='issuer'))
    for item in entries:
        key = ticker_ids.get(item.symbol, 'catalog:ticker:' + item.symbol)
        for relation in catalog[item.symbol].get('relations', []):
            catalog_relation(key, relation, True)
    for registry_id, profile in PRIVATE_COMPANIES.items():
        owner = resolve(dict(profile, registry_id=registry_id))
        if owner in nodes:
            for relation in profile.get('relations', []):
                catalog_relation(owner, relation)
    for item in entries:
        profile = PUBLIC_COMPANIES[item.symbol]
        key = ticker_ids.get(item.symbol, 'catalog:ticker:' + item.symbol)
        origin = profile['brief'][0]['source']
        nodes[key] = dict(id=key, name=profile['name'], symbol=item.symbol, kind='issuer', sector=item.sector_hint,
                          description=profile['brief'][0]['detail'], scope=item.scope, sources=[origin])
        group = 'group:' + item.group
        nodes.setdefault(group, dict(id=group, name=GROUPS[item.group], kind='group',
                                    description='사업 내용에 따른 탐색 분류입니다. 공식 GICS 편입이나 기업 간 거래를 뜻하지 않습니다.', sources=[origin]))
        edge('energy', group, 'classification', '에너지 연구의 사업 탐색 그룹', origin, True)
        edge(group, key, 'classification', '편집한 사업 분류 · 공식 지수 구성이나 거래 관계와 구별', origin, True)
        for index, (field, product) in enumerate((field, card) for field in ('products', 'segments', 'drivers') for card in profile.get(field, [])):
            topic = f'{field}:{item.symbol}:{index}'
            source = _origin(product.get('source'))
            if not source:
                continue
            nodes[topic] = dict(id=topic, name=product['title'], kind='factor' if field == 'drivers' else 'product', symbol=item.symbol,
                                description=product['detail'], sources=[source])
            edge(key, topic, 'exposure' if field == 'drivers' else 'business_scope',
                 '출처에 근거한 사업 영향·분석 기준. 영향의 크기·부호를 계산한 값은 아닙니다.' if field == 'drivers' else '공시에서 확인한 제품·설비·사업 범위. 별도 기업이나 외부 거래가 아닙니다.', source, field == 'drivers')
    # Physical processes are separate from company trades and company products.
    for index, chain in enumerate(SECTIONS[0]['entries']):
        key = 'chain:' + str(index)
        origins = [_guide_source(s) for s in chain['source_ids']]
        nodes[key] = dict(id=key, name=chain['title'], kind='product', description=chain['body'], sources=origins)
        edge('energy', key, 'industry_process', '산업의 물질·사업 과정 · 특정 기업의 납품 계약 아님', origins[0], True)
        previous = key
        for number, step in enumerate(chain['steps']):
            target = f'process:{index}:{number}'
            nodes[target] = dict(id=target, name=step, kind='product', description=chain['body'], sources=origins)
            edge(previous, target, 'industry_process', '산업 과정의 다음 단계 · 기업 간 거래 아님', origins[0], True)
            previous = target
    oil = dict(label='EIA · 원유 수급·가격 영향', url='https://www.eia.gov/energyexplained/oil-and-petroleum-products/prices-and-outlook.php', level='primary', as_of='2023-08-16')
    gas = dict(label='EIA · 천연가스 가격 요인', url='https://www.eia.gov/energyexplained/natural-gas/factors-affecting-natural-gas-prices.php', level='primary', as_of='열람 2026-10-04')
    factors = [
        ('oil-price', '원유 수급·가격', '세계 수급은 원유 판매 가격과 정유 투입비용에 연결됩니다. 기업별 이익 변화의 크기나 부호를 계산한 값은 아닙니다.', oil, ['integrated', 'upstream', 'refining', 'fuel-distribution', 'mineral-royalty']),
        ('gas-price', '가스 수급·가격', '가스 생산·저장·날씨·소비 수요는 가격에 연결됩니다. 생산자의 판매액과 LNG·유틸리티의 조달비용은 구별합니다.', gas, ['upstream', 'gas-infrastructure', 'lng', 'utility']),
        ('demand', '경기·에너지 수요', '경제 활동과 운송·산업의 소비는 석유 수요에 연결됩니다.', oil, []),
        ('opec', 'OPEC 공급 정책', '생산 목표와 실제 이행·여유 생산능력은 세계 석유 공급과 가격에 영향을 줄 수 있습니다.', oil, []),
        ('geopolitics', '지정학·공급 차질', '분쟁·정치 사건에 따른 공급 차질은 가격 불확실성과 변동성 경로입니다. 특정 사건의 현재 영향을 확정하지 않습니다.', oil, []),
        ('weather', '날씨·계절', '허리케인·한파·난방 수요는 공급·수요에 영향을 줄 수 있습니다. 현재 재난 발생이나 특정 기업 피해를 뜻하지 않습니다.', oil, []),
        ('inventory', '재고·여유 공급능력', '재고·여유 생산능력이 낮으면 공급 차질에 대한 가격 반응이 달라질 수 있습니다.', oil, []),
        ('regulation', '허가·연료 규정', '가스 수송의 허가·요율과 바이오연료 RIN 제도는 별도 사업 조건입니다. 규제기관과 기업의 거래 관계가 아닙니다.', _guide_source('pipeline'), ['gas-infrastructure'])]
    for key, name, description, origin, groups in factors:
        identity = 'factor:' + key
        nodes[identity] = dict(id=identity, name=name, kind='factor', description=description, sources=[origin])
        for group in groups:
            target = 'group:' + group
            if target in nodes:
                edge(identity, target, 'exposure', '산업 구조를 연결한 분석용 영향 경로 · 정량 영향·거래 계약 아님', origin, True)
        if key in ('demand', 'opec', 'geopolitics', 'weather', 'inventory'):
            edge(identity, 'factor:oil-price', 'exposure', '공개 산업 설명에 근거한 원유 수급·가격 영향 경로', origin, True)
        if key == 'regulation':
            nodes[identity]['sources'].append(_guide_source('rin'))
            edge(identity, 'chain:6', 'exposure', '바이오연료 제도와 산업 공정의 분석용 연결', _guide_source('rin'), True)
    if len(nodes) > MAX_NODES or len(edges) > MAX_RECORDS:
        raise HTTPException(413, '생태계 자료가 표시 범위를 초과했습니다.')
    return dict(focus_id='energy', nodes=list(nodes.values()), edges=list(edges.values()),
                checked_at='2026-10-04', issuer_count=len(entries), stored_claim_records=len(raw),
                scope='확정한 213개 기업과 공개 연구·저장 자료의 직접 연결 기업·그 사이의 확인된 관계·제품·부문·사업 요인·8개 공통 외부 요인. 전 세계 모든 기업·외부 변수의 완전한 목록은 아닙니다.',
                method='실제 관계, 사업 분류, 분석용 영향 경로를 구분합니다. 위치와 크기는 탐색을 위한 배치이며 실제 이익 영향도·투자 중요도·거래액의 추정값이 아닙니다.')


def snapshot(settings):
    if not settings.personal_local_mode or settings.production:
        raise HTTPException(404, '에너지 관계도를 찾을 수 없습니다')
    graph = CompanyGraph(settings)
    fingerprint = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in
                        (graph.path, graph.path.with_name(graph.path.name + '-wal')) if p.exists())
    key = (str(graph.path), fingerprint)
    global _cached
    with _lock:
        if _cached and _cached[0] == key and time.monotonic() - _cached[1] < 60:
            return deepcopy(_cached[2])
        result = _build(graph)
        _cached = (key, time.monotonic(), result)
        return deepcopy(result)
