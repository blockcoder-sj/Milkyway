"""Two-hop business exploration from the local, source-backed company graph.

An edge is always a stored statement. A path never creates a direct trade claim.
Only one chosen neighbour is expanded, eight rows at a time; no provider or AI I/O.
"""
import math
import re

from fastapi import HTTPException
from .company_graph import CompanyGraph
from .company_provenance import forbidden

BUSINESS_KINDS = ('supplier', 'customer', 'partner', 'competitor')
PAGE_SIZE = 8
EVIDENCE_LIMIT = 10


def _business(graph, key):
    return [edge for edge in graph.relations(key) if edge['kind'] in BUSINESS_KINDS
            and not forbidden(edge['source'])]


def _node(entity):
    profile = entity.get('profile') or {}
    brief = []
    for fact in profile.get('brief', []):
        if fact.get('detail') and re.search('[가-힣]', fact['detail']) and not forbidden(fact['source']):
            brief.append({'title':fact['title'], 'detail':fact['detail'][:320], 'source':fact['source']})
        if len(brief) == 2:
            break
    return {'id':entity['id'], 'name':entity['name'],
            'symbol':next(iter(entity['symbols']), None), 'brief':brief}


def _statement(edge):
    value = {key:edge.get(key) for key in ('name', 'target_id', 'symbol', 'kind',
                                          'detail', 'reverse', 'reported_by', 'source')}
    evidence = [row for row in edge.get('evidence', [edge]) if not forbidden(row['source'])]
    value['evidence'] = evidence[:EVIDENCE_LIMIT]
    value['evidence_total'] = len(evidence)
    return value


def network_snapshot(settings, entity_key, via, page=1, kind='all'):
    """Current -> chosen company -> its recorded business relationships.

    A company merely sharing a sector, investor or supplier is never an edge.
    All limits also apply to direct Python callers, independently of HTTP parsing.
    """
    if kind not in ('all', *BUSINESS_KINDS) or type(page) is not int or not 1 <= page <= 50:
        raise ValueError('Invalid business network query')
    from .company_entities import get_entity
    root, middle = get_entity(settings, entity_key), get_entity(settings, via)
    graph = CompanyGraph(settings)
    direct = [edge for edge in _business(graph, root['id']) if edge['target_id'] == middle['id']]
    if not direct:
        raise HTTPException(404, '현재 기업과 확인된 사업 관계가 있는 기업을 선택하세요')
    related = [edge for edge in _business(graph, middle['id']) if edge['target_id'] != root['id']]
    counts = {key:sum(edge['kind'] == key for edge in related) for key in BUSINESS_KINDS}
    filtered = [edge for edge in related if kind == 'all' or edge['kind'] == kind]
    filtered.sort(key=lambda edge:(BUSINESS_KINDS.index(edge['kind']), edge['name'].casefold(), edge['target_id']))
    pages = max(1, math.ceil(len(filtered) / PAGE_SIZE))
    page = min(page, pages)
    rows = [_statement(edge) for edge in filtered[(page - 1)*PAGE_SIZE:page*PAGE_SIZE]]
    return {'root':_node(root), 'via':_node(middle), 'direct':list(map(_statement, direct)),
            'rows':rows, 'kind':kind, 'counts':counts, 'total':len(filtered),
            'page':page, 'pages':pages, 'page_size':PAGE_SIZE,
            'bounds':{'statement_rows_per_company':400, 'evidence_per_relation':EVIDENCE_LIMIT}}
