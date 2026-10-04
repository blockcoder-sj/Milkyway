"""Local, source-backed retrieval for the graph. No embeddings or model calls.

FTS is a derived index inside the public company DB; original profiles, claims
and citations are retained. This is the retrieval stage, not an LLM RAG answer.
"""
import hashlib
import json
import re
import threading

from .company_graph import CompanyGraph
from .energy_constellation import snapshot, _origin

_lock = threading.Lock()


def corpus(settings):
    """One source-checked corpus for lexical and semantic retrieval."""
    graph = snapshot(settings)
    nodes = {n['id']: n for n in graph['nodes']}
    documents = []
    for n in graph['nodes']:
        source = next((s for s in n.get('sources', []) if _origin(s)), None)
        if source:
            parts = [n.get('description', ''), n.get('original', '')]
            measure = n.get('measure')
            if measure:
                share = measure['share_pct']
                basis = ('비중 미산출: ' + measure['exclusion'] if share is None else f'같은 매출 지표 내 {share:.2f}%')
                parts.append(f"공시 기간 {measure['start']} ~ {measure['end']} · 금액 {measure['value']:,.0f} {measure['unit']} · 지표 {measure['metric']} · {basis}")
            body = '\n'.join(part for part in parts if part)
            documents.append((n['id'], n['id'], '', n['name'] + ' ' + (n.get('symbol') or ''), body,
                              json.dumps(source, ensure_ascii=False)))
    for e in graph['edges']:
        source = _origin(e['citation'])
        if source:
            a, b = nodes[e['source']], nodes[e['target']]
            documents.append(('edge:'+e['id'], e['source'], e['id'], a['name']+' → '+b['name'],
                              e['detail']+'\n'+e.get('original', ''), json.dumps(source, ensure_ascii=False)))
    fingerprint = hashlib.sha256(json.dumps(documents, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    return graph, documents, fingerprint


def company_scope(graph, focus):
    """Exactly the company's sourced elements and direct company relations."""
    from fastapi import HTTPException
    nodes={n['id']:n for n in graph['nodes']}
    if focus not in nodes or nodes[focus]['kind'] not in ('issuer','company'):
        raise HTTPException(404,'현재 에너지 지도에 없는 기업입니다.')
    allowed={focus};edges=set()
    for edge in graph['edges']:
        if focus not in (edge['source'],edge['target']):continue
        other=edge['target'] if edge['source']==focus else edge['source']
        n=nodes[other]
        if n['kind'] in ('issuer','company') or n.get('semantic_id','').startswith(focus+':'):
            allowed.add(other);edges.add(edge['id'])
    return allowed,edges


def search(settings, query, focus=None):
    tokens = re.findall(r'\w+', query[:240], re.UNICODE)[:8]
    if not tokens:
        # Still enforce the local-only boundary for empty queries.
        if not settings.personal_local_mode or settings.production:
            snapshot(settings)
        return {'rows': [], 'method': '공시·공개 자료 DB 키워드 검색 · AI 생성 답변 아님'}
    graph, documents, fingerprint = corpus(settings)
    nodes = {n['id']: n for n in graph['nodes']}
    allowed,allowed_edges=company_scope(graph,focus) if focus else (None,None)
    # Only word tokens reach MATCH. Quoted terms are literal and SQL values are
    # parameterized; user input cannot supply FTS operators or column selectors.
    expression = ' AND '.join('"'+t[:80]+'"*' for t in tokens)
    with _lock, CompanyGraph(settings).connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS constellation_index_meta (id INTEGER PRIMARY KEY CHECK(id=1), fingerprint TEXT NOT NULL)')
        db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS constellation_evidence USING fts5(doc_id UNINDEXED,node_id UNINDEXED,edge_id UNINDEXED,title,body,citation UNINDEXED)')
        previous = db.execute('SELECT fingerprint FROM constellation_index_meta WHERE id=1').fetchone()
        if not previous or previous[0] != fingerprint:
            db.execute('DELETE FROM constellation_evidence')
            db.executemany('INSERT INTO constellation_evidence VALUES(?,?,?,?,?,?)', documents)
            db.execute('INSERT OR REPLACE INTO constellation_index_meta VALUES(1,?)', (fingerprint,))
        rows = []
        scope=' AND node_id IN ('+','.join('?' for _ in allowed)+") AND (edge_id='' OR edge_id IN ("+','.join('?' for _ in allowed_edges)+'))' if allowed is not None else ''
        params=(expression,*sorted(allowed),*sorted(allowed_edges)) if allowed is not None else (expression,)
        for row in db.execute("SELECT node_id,edge_id,title,snippet(constellation_evidence,4,'','','…',32) AS excerpt,citation FROM constellation_evidence WHERE constellation_evidence MATCH ?"+scope+" ORDER BY bm25(constellation_evidence,0,0,0,6,1,0),doc_id LIMIT 12", params):
            source = _origin(json.loads(row['citation']))
            if row['node_id'] in nodes and source:
                node_id=row['node_id']
                if focus and row['edge_id']:
                    edge=next(e for e in graph['edges'] if e['id']==row['edge_id'])
                    if focus in (edge['source'],edge['target']):node_id=edge['target'] if edge['source']==focus else edge['source']
                if focus:node_id=nodes[node_id].get('semantic_id') or node_id
                rows.append(dict(node_id=node_id, edge_id=row['edge_id'], title=row['title'],
                                 excerpt=row['excerpt'][:700], citation=source))
    return {'rows': rows, 'indexed_documents': len(documents),
            'method': '공시·공개 자료 DB 키워드 검색 · 검색 순위는 사업 비중·경제적 영향도와 다름 · AI 생성 답변 아님'}
