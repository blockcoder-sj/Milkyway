"""Source-backed local semantic retrieval and graph association analysis.

Embeddings suggest similar evidence; only existing cited edges constitute
relationships. A bounded graph walk is an exploration path, never a causal model.
"""
from collections import deque
from copy import deepcopy
import json
import math
import re
import subprocess
import threading
from fastapi import HTTPException
from .company_graph import CompanyGraph
from .constellation_retrieval import corpus, company_scope
from .constellation_embeddings import DIMENSIONS, MODEL_REVISION, query_vector

SCHEMA = '''
CREATE TABLE IF NOT EXISTS cosmos_semantic_meta (id INTEGER PRIMARY KEY CHECK(id=1), generation TEXT NOT NULL, corpus_hash TEXT NOT NULL, revision TEXT NOT NULL, completed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cosmos_semantic_vectors (hash TEXT PRIMARY KEY, vector BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS cosmos_semantic_chunks (generation TEXT NOT NULL, doc_id TEXT NOT NULL, part INTEGER NOT NULL, node_id TEXT NOT NULL, edge_id TEXT NOT NULL, title TEXT NOT NULL, excerpt TEXT NOT NULL, citation TEXT NOT NULL, vector_hash TEXT NOT NULL, PRIMARY KEY(generation,doc_id,part));
CREATE TABLE IF NOT EXISTS cosmos_semantic_nodes (generation TEXT NOT NULL, id TEXT NOT NULL, node_id TEXT NOT NULL, vector BLOB NOT NULL, layout TEXT NOT NULL, PRIMARY KEY(generation,id));
'''
_lock = threading.Lock()
_cache = None
# Cross-language topic hints rerank semantic evidence; they never create facts.
# Leave unfamiliar queries to the encoder rather than guessing an industry.
_topics=tuple(re.compile(p,re.I) for p in (
    r'우라늄|원자력|uranium|nuclear',
    r'탄소.{0,12}포집|탄소.{0,12}저장|carbon.{0,12}captur|carbon.{0,12}stor|\bccs\b|\bccus\b',
    r'정유|휘발유|경유|refin|gasoline|diesel',
    r'\blng\b|액화|가스.{0,12}냉각|가스.{0,12}액체|liquef',
    r'석탄|\bcoal\b',
    r'파이프라인|pipeline',
    r'시추|drilling|oilfield',
    r'재생|바이오|renewable|biofuel',
))


def identity(node):
    return node.get('semantic_id') or node['id']


def _state(settings, graph, fingerprint, *, vectors=False):
    global _cache
    with CompanyGraph(settings).connection() as db:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE name='cosmos_semantic_meta'").fetchone()
        meta = db.execute('SELECT * FROM cosmos_semantic_meta WHERE id=1').fetchone() if exists else None
        if not meta or meta['corpus_hash'] != fingerprint or meta['revision'] != MODEL_REVISION:
            return None
        key = (str(CompanyGraph(settings).path), meta['generation'], vectors)
        with _lock:
            if _cache and _cache[0][:2] == key[:2] and (not vectors or _cache[0][2]):
                return _cache[1]
            records = [dict(r) for r in db.execute('SELECT * FROM cosmos_semantic_nodes WHERE generation=? ORDER BY id', (meta['generation'],))]
            try:
                out = dict(meta=dict(meta), nodes={r['id']: {'node_id': r['node_id'], 'layout': json.loads(r['layout'])} for r in records})
                for row in out['nodes'].values():
                    point=row['layout']['position']
                    if len(point)!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in point):raise ValueError('Invalid layout')
            except (ValueError,TypeError,KeyError):
                raise HTTPException(503, '의미 검색 배치 검증이 필요합니다.')
            if vectors:
                import numpy as np
                out['keys'] = [r['id'] for r in records]
                chunks = [dict(r) for r in db.execute('SELECT c.*,v.vector FROM cosmos_semantic_chunks c JOIN cosmos_semantic_vectors v ON v.hash=c.vector_hash WHERE c.generation=? ORDER BY c.doc_id,c.part', (meta['generation'],))]
                out['chunks'] = [{k:v for k,v in r.items() if k!='vector'} for r in chunks]
                try:
                    out['matrix'] = np.asarray([np.frombuffer(r['vector'], dtype='<f4') for r in records])
                    out['chunk_matrix'] = np.asarray([np.frombuffer(r['vector'], dtype='<f4') for r in chunks])
                except ValueError:
                    raise HTTPException(503, '의미 검색 인덱스 검증이 필요합니다.')
                for matrix in (out['matrix'], out['chunk_matrix']):
                    if matrix.ndim != 2 or matrix.shape[1] != DIMENSIONS or not np.isfinite(matrix).all() or not np.allclose(np.linalg.norm(matrix,axis=1),1,atol=.002):
                        raise HTTPException(503, '의미 검색 인덱스 검증이 필요합니다.')
            _cache = (key, out)
            return out


def decorate(settings, graph):
    _, _, fingerprint = corpus(settings)
    state = _state(settings, graph, fingerprint)
    graph['semantic_status'] = 'ready' if state else 'not_prepared'
    if state:
        for node in graph['nodes']:
            row = state['nodes'].get(identity(node))
            if row: node['semantic'] = deepcopy(row['layout'])
    return graph


def decorate_company(settings, result):
    if not result.get('entity_key'): return result
    graph, _, fingerprint = corpus(settings)
    state = _state(settings, graph, fingerprint)
    result['semantic_status'] = 'ready' if state and result['entity_key'] in state['nodes'] else 'not_prepared'
    if state:
        wanted = {result['entity_key'], *(r['target_id'] for r in result['relations'])}
        root = result['entity_key']
        for field in ('products','segments','drivers','facts','revenue_mix'):
            wanted.update(root+':'+('revenue' if field=='revenue_mix' else field)+':'+str(i) for i,_ in enumerate(result.get(field, [])))
        result['constellation_semantics'] = {k:deepcopy(v['layout']) for k,v in state['nodes'].items() if k in wanted}
    return result


def _ready(settings):
    graph, _, fingerprint = corpus(settings)
    state = _state(settings, graph, fingerprint, vectors=True)
    if not state:
        raise HTTPException(503, '의미 검색 자료를 준비해야 합니다. 단어 검색은 계속 사용할 수 있습니다.')
    return graph, state


def search(settings, query, focus=None):
    import numpy as np
    graph, state = _ready(settings)
    by_id = {n['id']:n for n in graph['nodes']}
    allowed,allowed_edges=company_scope(graph,focus) if focus else (None,None)
    try: vector = query_vector(settings, query[:240])
    except (ValueError, OSError, subprocess.TimeoutExpired):
        raise HTTPException(503, '로컬 의미 검색 모델을 확인해야 합니다. 단어 검색은 사용할 수 있습니다.')
    scores = np.einsum('ij,j->i',state['chunk_matrix'],vector)
    topics=[t for t in _topics if t.search(query)]
    ranking=scores.copy()
    if topics:
        for i,hit in enumerate(state['chunks']):
            in_title=any(t.search(hit['title']) for t in topics)
            in_text=any(t.search(hit['excerpt']) for t in topics)
            ranking[i]+=.08 if in_title else .025 if in_text else -.08
    rows, seen = [], set()
    for i in np.argsort(-ranking, kind='stable'):
        hit = state['chunks'][int(i)]
        if hit['node_id'] not in by_id or allowed is not None and hit['node_id'] not in allowed: continue
        if allowed_edges is not None and hit['edge_id'] and hit['edge_id'] not in allowed_edges:continue
        if hit['doc_id'] in seen: continue
        # E5 cosine values are not probabilities or economic exposure weights.
        if float(scores[i]) < .70: continue
        seen.add(hit['doc_id'])
        node_id = identity(by_id[hit['node_id']]) if focus else hit['node_id']
        if focus and hit['edge_id']:
            edge = next(e for e in graph['edges'] if e['id']==hit['edge_id'])
            other = edge['target'] if edge['source']==focus else edge['source']
            if edge['source']==focus or edge['target']==focus: node_id=identity(by_id[other])
        rows.append(dict(node_id=node_id, edge_id=hit['edge_id'], title=hit['title'], excerpt=hit['excerpt'][:700],
                         citation=json.loads(hit['citation']), similarity=round(float(scores[i]),4)))
        if len(rows)==12: break
    return dict(rows=rows, indexed_documents=len({r['doc_id'] for r in state['chunks']}),
                indexed_chunks=len(state['chunks']), method='로컬 의미 검색 + 다국어 에너지 주제 재정렬 · 출처 자료 발췌 · 유사도는 거래 관계·경제적 영향도가 아닙니다.')


def analysis(settings, node_id, basis='relations', company=False):
    import numpy as np
    graph, state = _ready(settings)
    nodes = {n['id']:n for n in graph['nodes']}
    semantic = {identity(n):n for n in graph['nodes']}
    node = semantic.get(node_id) or nodes.get(node_id)
    if not node: raise HTTPException(404, '현재 에너지 지도에 없는 요소입니다.')
    adjacency = {key:[] for key in nodes}
    for e in graph['edges']:
        adjacency[e['source']].append((e['target'],e));adjacency[e['target']].append((e['source'],e))
    direct = adjacency[node['id']]
    confirmed = [dict(node_id=identity(nodes[k]) if company else k, name=nodes[k]['name'], kind=e['kind'],
                      analytical=e['analytical'], detail=e['detail'], citation=e['citation']) for k,e in direct if e['kind'] in ('customer','supplier','parent','subsidiary','holding','owner','partner','transaction')][:8]
    visited={node['id']};queue=deque([(node['id'], [])]);paths=[]
    while queue and len(paths)<4:
        current, path = queue.popleft()
        if current!=node['id'] and current.startswith('factor:'):
            paths.append(dict(name=nodes[current]['name'],node_id=current,steps=path));continue
        if len(path)>=3: continue
        for other,e in adjacency[current]:
            if other in visited: continue
            visited.add(other)
            step=dict(from_name=nodes[e['source']]['name'],to_name=nodes[e['target']]['name'],kind=e['kind'],analytical=e['analytical'],detail=e['detail'],citation=e['citation'])
            queue.append((other,path+[step]))
    similar=[]
    key=identity(node)
    if key in state['nodes']:
        own=state['keys'].index(key);scores=np.einsum('ij,j->i',state['matrix'],state['matrix'][own])
        connected={k for k,_ in direct}|{node['id']}
        for i in np.argsort(-scores,kind='stable'):
            candidate=nodes[state['nodes'][state['keys'][int(i)]]['node_id']]
            if candidate['id'] in connected or candidate['kind']!=node['kind']:continue
            if candidate.get('scope')=='source_only':continue
            if float(scores[i])<.80:break
            # Recommendations never add, rename, merge or persist graph edges.
            owner=identity(candidate).split(':')[0]
            similar.append(dict(node_id=candidate['id'],name=candidate['name'],similarity=round(float(scores[i]),4),sources=candidate.get('sources',[])[:1],company_id=owner if owner.startswith('c_') else None))
            if len(similar)==6:break
    revenue=[]
    for other,_ in direct:
        n=nodes[other]
        if n['kind']=='revenue' and n.get('latest') and n['measure']['group']==basis:
            revenue.append(dict(name=n['name'],measure=n['measure'],citation=n['sources'][0]))
    revenue.sort(key=lambda r:-(r['measure']['share_pct'] if r['measure']['share_pct'] is not None else -1))
    return dict(name=node['name'],description=node.get('description',''),sources=node.get('sources',[])[:1],
                confirmed=confirmed,paths=paths,similar=similar,revenue=revenue[:8],
                method='확인된 연결과 출처를 따라 정리한 탐색 분석입니다. 경로는 인과·수익 영향 모델이 아니며 의미 유사 요소는 실제 관계가 확인된 기업과 구별합니다.')
