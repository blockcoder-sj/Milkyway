"""Resumable, offline-only construction of derived public semantic data."""
import datetime as dt
import hashlib
import json
import math
from .company_graph import CompanyGraph
from .constellation_retrieval import corpus
from .constellation_embeddings import DIMENSIONS, MODEL_REVISION, encoder
from .constellation_semantics import SCHEMA, identity

MAX_CHUNKS = 80000


def prepare(settings, batch_size=8, progress=print):
    import numpy as np
    graph, documents, fingerprint = corpus(settings)
    model = encoder(settings)
    generation = hashlib.sha256((fingerprint+MODEL_REVISION+'chunks-200-overlap-32-layout-v2').encode()).hexdigest()
    public = CompanyGraph(settings)
    with public.connection() as db:
        db.executescript(SCHEMA)
    chunks=[]
    for doc_id,node_id,edge_id,title,body,citation in documents:
        for part,excerpt in enumerate(model.chunks(title+'\n'+body)):
            vector_hash=hashlib.sha256((MODEL_REVISION+'\0'+excerpt).encode()).hexdigest()
            chunks.append((generation,doc_id,part,node_id,edge_id,title,excerpt,citation,vector_hash))
            if len(chunks)>MAX_CHUNKS:raise ValueError('Semantic corpus exceeds the bounded chunk limit')
    wanted=sorted({row[-1] for row in chunks})
    cached=set()
    with public.connection() as db:
        for start in range(0,len(wanted),512):
            keys=wanted[start:start+512]
            cached.update(r['hash'] for r in db.execute('SELECT hash FROM cosmos_semantic_vectors WHERE hash IN ('+','.join('?' for _ in keys)+')',keys))
    pending={r[-1]:r[6] for r in chunks if r[-1] not in cached}
    todo=list(pending.items())
    progress(f'근거 문서 {len(documents)} / 청크 {len(chunks)} / 새 벡터 {len(todo)}',flush=True)
    for start in range(0,len(todo),batch_size):
        batch=todo[start:start+batch_size]
        vectors=model.encode([text for _,text in batch])
        with public.connection() as db:
            db.executemany('INSERT OR IGNORE INTO cosmos_semantic_vectors VALUES(?,?)',
                           [(key,vector.tobytes()) for (key,_),vector in zip(batch,vectors)])
        if start%(batch_size*100)==0:progress(f'벡터 {min(start+batch_size,len(todo))}/{len(todo)}',flush=True)
    with public.connection() as db:
        vector_cache={}
        # Old generations and interrupted caches stay on disk; only the bounded
        # current corpus is read into memory, even after many future refreshes.
        for start in range(0,len(wanted),512):
            keys=wanted[start:start+512]
            vector_cache.update((r['hash'],np.frombuffer(r['vector'],dtype='<f4')) for r in db.execute('SELECT * FROM cosmos_semantic_vectors WHERE hash IN ('+','.join('?' for _ in keys)+')',keys))
    for key in wanted:
        vector=vector_cache[key]
        if vector.shape!=(DIMENSIONS,) or not np.isfinite(vector).all() or abs(float(np.linalg.norm(vector))-1)>.002:
            raise ValueError('Invalid cached source embedding')
    by_doc={}
    for row in chunks:by_doc.setdefault(row[1],[]).append(vector_cache[row[-1]])
    means={k:np.mean(v,axis=0) for k,v in by_doc.items()}
    incident={n['id']:[] for n in graph['nodes']}
    for e in graph['edges']:
        value=means.get('edge:'+e['id'])
        if value is not None:
            for key in (e['source'],e['target']):
                if len(incident[key])<4:incident[key].append(value)
    nodes=[];vectors=[]
    for n in sorted(graph['nodes'],key=identity):
        value=means.get(n['id'])
        if value is None and incident[n['id']]:value=np.mean(incident[n['id']],axis=0)
        if value is None:continue
        value=value/max(float(np.linalg.norm(value)),1e-12)
        nodes.append(n);vectors.append(value)
    matrix=np.asarray(vectors,dtype='<f4')
    if not len(nodes):raise ValueError('No source-backed semantic nodes')
    # Deterministic spherical k-means: clusters derive from real embeddings,
    # with 3D anchors and a small PCA offset within each cluster.
    count=min(24,len(nodes));centers=[matrix[0]];best=matrix@centers[0]
    for _ in range(1,count):
        next_center=matrix[int(np.argmin(best))];centers.append(next_center);best=np.maximum(best,matrix@next_center)
    centers=np.asarray(centers)
    for _ in range(16):
        groups=(matrix@centers.T).argmax(axis=1)
        updated=np.asarray([matrix[groups==i].mean(axis=0) if np.any(groups==i) else centers[i] for i in range(count)])
        updated/=np.maximum(np.linalg.norm(updated,axis=1,keepdims=True),1e-12)
        if np.allclose(updated,centers,atol=1e-5):break
        centers=updated
    groups=(matrix@centers.T).argmax(axis=1)
    centered=matrix-matrix.mean(axis=0)
    _,basis=np.linalg.eigh(centered.T@centered)
    basis=basis[:,-3:]
    for i in range(3):
        if basis[np.abs(basis[:,i]).argmax(),i]<0:basis[:,i]*=-1
    offsets=centered@basis
    offsets/=np.maximum(np.max(np.abs(offsets),axis=0),1e-12)
    labels=[]
    for center in centers:
        choices=np.argsort(-(matrix@center),kind='stable')
        representative=next((nodes[int(i)] for i in choices if nodes[int(i)]['kind'] in ('issuer','product','segment','factor') and nodes[int(i)].get('sources')),nodes[int(choices[0])])
        labels.append(representative['name'][:80])
    rows=[]
    for i,node in enumerate(nodes):
        cluster=int(groups[i]);vertical=1-2*(cluster+.5)/count;radius=math.sqrt(1-vertical*vertical);angle=cluster*math.pi*(3-math.sqrt(5))
        point=np.array([math.cos(angle)*radius,math.sin(angle)*radius,vertical])+offsets[i]*.18
        point/=np.linalg.norm(point)
        layout=dict(cluster=cluster,position=[round(float(v),6) for v in point],label=labels[cluster])
        rows.append((generation,identity(node),node['id'],matrix[i].tobytes(),json.dumps(layout,ensure_ascii=False)))
    with public.connection() as db:
        # Completed generations remain intact until the new one is atomically activated.
        db.executemany('INSERT OR REPLACE INTO cosmos_semantic_chunks VALUES(?,?,?,?,?,?,?,?,?)',chunks)
        db.executemany('INSERT OR REPLACE INTO cosmos_semantic_nodes VALUES(?,?,?,?,?)',rows)
        db.execute('INSERT OR REPLACE INTO cosmos_semantic_meta VALUES(1,?,?,?,?)',
                   (generation,fingerprint,MODEL_REVISION,dt.datetime.now(dt.timezone.utc).isoformat()))
    progress(f'완료: 의미 요소 {len(nodes)} / 근거 청크 {len(chunks)}',flush=True)
    return dict(documents=len(documents),chunks=len(chunks),nodes=len(nodes),new_vectors=len(todo),generation=generation)
