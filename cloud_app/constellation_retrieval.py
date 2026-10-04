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


def search(settings, query):
    tokens = re.findall(r'\w+', query[:240], re.UNICODE)[:8]
    if not tokens:
        # Still enforce the local-only boundary for empty queries.
        if not settings.personal_local_mode or settings.production:
            snapshot(settings)
        return {'rows': [], 'method': '공시·공개 자료 DB 키워드 검색 · AI 생성 답변 아님'}
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
        for row in db.execute("SELECT node_id,edge_id,title,snippet(constellation_evidence,4,'','','…',32) AS excerpt,citation FROM constellation_evidence WHERE constellation_evidence MATCH ? ORDER BY bm25(constellation_evidence,0,0,0,6,1,0),doc_id LIMIT 12", (expression,)):
            source = _origin(json.loads(row['citation']))
            if row['node_id'] in nodes and source:
                rows.append(dict(node_id=row['node_id'], edge_id=row['edge_id'], title=row['title'],
                                 excerpt=row['excerpt'][:700], citation=source))
    return {'rows': rows, 'indexed_documents': len(documents),
            'method': '공시·공개 자료 DB 키워드 검색 · 검색 순위는 사업 비중·경제적 영향도와 다름 · AI 생성 답변 아님'}
