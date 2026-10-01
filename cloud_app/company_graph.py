"""Local company identity, directed relationships and their original evidence.

This database contains public research only. It never shares the trading ledger,
credentials, AI calls or production database. JSON profiles remain compatible.
"""
from contextlib import contextmanager
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid

from .company_schemas import CompanyKnowledge, Source
from .company_provenance import forbidden

ENTITY_KEY = re.compile(r"c_[a-f0-9]{32}")
QID = re.compile(r"Q\d{1,12}")
SYMBOL = re.compile(r"[A-Z0-9][A-Z0-9.-]{0,19}")
INVERSE = {
    "subsidiary": "parent",
    "parent": "subsidiary",
    "owner": "holding",
    "holding": "owner",
    "supplier": "customer",
    "customer": "supplier",
    "partner": "partner",
    "competitor": "competitor",
}
SCHEMA = """
CREATE TABLE company_entities (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT,
 redirect_to TEXT REFERENCES company_entities(id));
CREATE TABLE company_aliases (
 namespace TEXT NOT NULL, value TEXT NOT NULL,
 entity_id TEXT NOT NULL REFERENCES company_entities(id),
 PRIMARY KEY(namespace,value));
CREATE INDEX company_alias_entity ON company_aliases(entity_id);
CREATE TABLE company_sources (
 id TEXT PRIMARY KEY, label TEXT NOT NULL, url TEXT NOT NULL,
 as_of TEXT, level TEXT NOT NULL);
CREATE TABLE company_entity_sources (
 entity_id TEXT NOT NULL REFERENCES company_entities(id),
 source_id TEXT NOT NULL REFERENCES company_sources(id),
 PRIMARY KEY(entity_id,source_id));
CREATE INDEX company_entity_source_origin ON company_entity_sources(source_id);
CREATE TABLE company_profiles (
 entity_id TEXT PRIMARY KEY REFERENCES company_entities(id),
 payload TEXT NOT NULL, digest TEXT NOT NULL);
CREATE TABLE company_relations (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES company_entities(id),
 subject_id TEXT NOT NULL REFERENCES company_entities(id),
 object_id TEXT NOT NULL REFERENCES company_entities(id),
 kind TEXT NOT NULL, detail TEXT NOT NULL,
 source_id TEXT NOT NULL REFERENCES company_sources(id), observed_at TEXT,
 original TEXT NOT NULL DEFAULT '');
CREATE INDEX company_relation_subject ON company_relations(subject_id);
CREATE INDEX company_relation_object ON company_relations(object_id);
CREATE INDEX company_relation_owner ON company_relations(owner_id);
CREATE INDEX company_relation_source ON company_relations(source_id);
PRAGMA user_version=2;
"""


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _enable_wal(db):
    """Change journal mode once; SQLite's mode switch can return BUSY immediately.

    Concurrent first opens wait within the existing five second connection budget.
    Normal reads never request another journal-mode write. No claim is retried.
    """
    deadline = time.monotonic() + 5
    while True:
        try:
            mode = db.execute('PRAGMA journal_mode').fetchone()[0]
            if mode == 'wal':
                return
            if db.execute('PRAGMA journal_mode=WAL').fetchone()[0] != 'wal':
                raise ValueError('Company graph requires WAL mode')
            return
        except sqlite3.OperationalError as exc:
            if (getattr(exc, 'sqlite_errorcode', 0) & 0xff) not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(0.025, remaining))


class CompanyGraph:
    def __init__(self, settings):
        if not settings.personal_local_mode or settings.production:
            raise ValueError("Company graph requires personal local mode")
        directory = settings.dataset_dir.parent / "company-details"
        if directory.is_symlink():
            raise ValueError("Unsafe company graph directory")
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = directory / "graph.sqlite3"

    @contextmanager
    def connection(self):
        if self.path.is_symlink():
            raise ValueError("Unsafe company graph file")
        # Establish private permissions before SQLite opens a new file.
        descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.close(descriptor)
        os.chmod(self.path, 0o600)
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            _enable_wal(db)
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                # Serialize first creation across app and worker startup.
                db.execute("BEGIN IMMEDIATE")
                if db.execute("PRAGMA user_version").fetchone()[0] == 0:
                    for statement in SCHEMA.split(";"):
                        if statement.strip():
                            db.execute(statement)
                db.commit()
            elif version == 1:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('PRAGMA user_version').fetchone()[0] == 1:
                    db.execute("ALTER TABLE company_relations ADD COLUMN original TEXT NOT NULL DEFAULT ''")
                    db.execute('CREATE INDEX IF NOT EXISTS company_entity_source_origin ON company_entity_sources(source_id)')
                    db.execute('CREATE INDEX IF NOT EXISTS company_relation_source ON company_relations(source_id)')
                    self._remove_encyclopedia(db)
                    db.execute('PRAGMA user_version=2')
                db.commit()
            elif version != 2:
                raise ValueError("Unsupported company graph schema")
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _remove_encyclopedia(db):
        rejected = [row['id'] for row in db.execute('SELECT * FROM company_sources') if forbidden(dict(row))]
        affected = set()
        for key in rejected:
            affected.update(row[0] for row in db.execute('SELECT entity_id FROM company_entity_sources WHERE source_id=?', (key,)))
            db.execute('DELETE FROM company_relations WHERE source_id=?', (key,))
            db.execute('DELETE FROM company_entity_sources WHERE source_id=?', (key,))
            db.execute('DELETE FROM company_sources WHERE id=?', (key,))
        for key in affected:
            if not db.execute('SELECT 1 FROM company_entity_sources WHERE entity_id=? LIMIT 1', (key,)).fetchone():
                ticker = db.execute("SELECT value FROM company_aliases WHERE entity_id=? AND namespace='ticker' LIMIT 1", (key,)).fetchone()
                db.execute('UPDATE company_entities SET name=? WHERE id=?', (ticker[0] if ticker else '공식 자료 확인 대기', key))
        marker = ' · 규칙으로 추출한 원문: '
        for row in db.execute('SELECT id,detail,original FROM company_relations').fetchall():
            if marker in row['detail']:
                detail, original = row['detail'].split(marker, 1)
                db.execute('UPDATE company_relations SET detail=?,original=? WHERE id=?',
                           (detail, row['original'] or original, row['id']))
        # Exact ticker / old opaque identity aliases are preserved; no new wiki I/O.
        for row in db.execute('SELECT p.entity_id,p.payload,p.digest,e.sector,e.name FROM company_profiles p JOIN company_entities e ON e.id=p.entity_id').fetchall():
            profile = CompanyKnowledge.model_validate_json(row['payload'])
            if row['entity_id'] in affected and not profile.description_source:
                profile.name = row['name']
            for edge in profile.relations:
                if marker in edge.detail:
                    edge.detail, edge.original = edge.detail.split(marker, 1)
            payload = encoded(profile.model_dump(mode='json'))
            fingerprint = digest(payload + '|' + (row['sector'] or ''))
            if payload != row['payload'] or fingerprint != row['digest']:
                db.execute('UPDATE company_profiles SET payload=?,digest=? WHERE entity_id=?',
                           (payload, fingerprint, row['entity_id']))

    def remove_encyclopedia(self):
        """Idempotent public-knowledge cleanup, independent from the trading DB."""
        with self.connection() as db:
            self._remove_encyclopedia(db)

    @staticmethod
    def _resolve(db, key):
        if not isinstance(key, str) or not ENTITY_KEY.fullmatch(key):
            raise ValueError("Invalid company entity")
        for _ in range(16):
            row = db.execute(
                "SELECT * FROM company_entities WHERE id=?", (key,)
            ).fetchone()
            if row is None:
                return None
            if not row["redirect_to"]:
                return dict(row)
            key = row["redirect_to"]
        raise ValueError("Company identity redirect cycle")

    def _merge(self, db, target, old):
        if target == old:
            return
        # Only exact authoritative alias matches can reach this operation.
        left = db.execute(
            "SELECT value FROM company_aliases WHERE namespace='wikidata' AND entity_id=?",
            (target,),
        ).fetchone()
        right = db.execute(
            "SELECT value FROM company_aliases WHERE namespace='wikidata' AND entity_id=?",
            (old,),
        ).fetchone()
        if left and right and left[0] != right[0]:
            raise ValueError("Conflicting company identities")
        db.execute(
            "UPDATE company_aliases SET entity_id=? WHERE entity_id=?", (target, old)
        )
        db.execute(
            "INSERT OR IGNORE INTO company_entity_sources SELECT ?,source_id FROM company_entity_sources WHERE entity_id=?",
            (target, old),
        )
        db.execute("DELETE FROM company_entity_sources WHERE entity_id=?", (old,))
        for column in ("subject_id", "object_id", "owner_id"):
            db.execute(
                f"UPDATE company_relations SET {column}=? WHERE {column}=?",
                (target, old),
            )
        db.execute(
            "INSERT OR IGNORE INTO company_profiles SELECT ?,payload,digest FROM company_profiles WHERE entity_id=?",
            (target, old),
        )
        db.execute("DELETE FROM company_profiles WHERE entity_id=?", (old,))
        db.execute(
            "UPDATE company_entities SET redirect_to=? WHERE id=?", (target, old)
        )
        db.execute(
            "UPDATE company_entities SET redirect_to=? WHERE redirect_to=?",
            (target, old),
        )

    def _entity(self, db, name, symbol=None, qid=None, reference=None, sector=None, registry=None):
        aliases = []
        if symbol:
            if not SYMBOL.fullmatch(symbol):
                raise ValueError("Invalid company symbol")
            aliases.append(("ticker", symbol))
        if qid:
            if not QID.fullmatch(qid):
                raise ValueError("Invalid Wikidata identity")
            aliases.append(("wikidata", qid))
        if registry:
            from .company_research_catalog import PRIVATE_COMPANIES
            if registry not in PRIVATE_COMPANIES or symbol:
                raise ValueError("Unknown primary-source company registry")
            aliases.append(("registry", registry))
            if reference:
                # Upgrade an earlier source-local alias only after manual registry
                # verification; this keeps existing links to that evidence alive.
                aliases.append(("reference", digest(reference + "|" + name.casefold().strip())))
        if not aliases:
            if not reference:
                raise ValueError("Company identity requires evidence")
            # Equal names alone do not establish an equal legal entity.
            aliases.append(
                ("reference", digest(reference + "|" + name.casefold().strip()))
            )
        existing = []
        for namespace, value in aliases:
            row = db.execute(
                "SELECT entity_id FROM company_aliases WHERE namespace=? AND value=?",
                (namespace, value),
            ).fetchone()
            if row:
                resolved = self._resolve(db, row[0])["id"]
                if resolved not in existing:
                    existing.append(resolved)
        key = existing[0] if existing else "c_" + uuid.uuid4().hex
        if not existing:
            db.execute(
                "INSERT INTO company_entities(id,name,sector) VALUES(?,?,?)",
                (key, name[:120], sector),
            )
        else:
            for other in existing[1:]:
                self._merge(db, key, other)
            prior_q = db.execute(
                "SELECT value FROM company_aliases WHERE namespace='wikidata' AND entity_id=?",
                (key,),
            ).fetchone()
            if qid and prior_q and prior_q[0] != qid:
                raise ValueError("Conflicting company Wikidata identity")
            if sector:
                db.execute(
                    "UPDATE company_entities SET sector=?,name=? WHERE id=?",
                    (sector, name[:120], key),
                )
        for namespace, value in aliases:
            db.execute(
                "INSERT OR IGNORE INTO company_aliases VALUES(?,?,?)",
                (namespace, value, key),
            )
        return key

    def ingest(self, knowledge, sector=None):
        profile = CompanyKnowledge.model_validate(knowledge)
        payload = encoded(profile.model_dump(mode="json"))
        fingerprint = digest(payload + "|" + (sector or ""))
        with self.connection() as db:
            alias = (
                ("ticker", profile.symbol)
                if profile.symbol
                else ("registry", profile.registry_id) if profile.registry_id
                else ("wikidata", profile.entity_id)
            )
            row = db.execute(
                "SELECT p.entity_id,p.digest FROM company_profiles p JOIN company_aliases a ON a.entity_id=p.entity_id WHERE a.namespace=? AND a.value=?",
                alias,
            ).fetchone()
            if row and row["digest"] == fingerprint:
                return row["entity_id"]
            db.execute("BEGIN IMMEDIATE")
            key = self._entity(
                db, profile.name, profile.symbol, profile.entity_id, sector=sector,
                registry=profile.registry_id
            )
            db.execute(
                "INSERT OR REPLACE INTO company_profiles VALUES(?,?,?)",
                (key, payload, fingerprint),
            )
            sources = list(profile.sources) + list(profile.filings)
            if profile.description_source:
                sources.append(profile.description_source)
            for field in (
                "facts",
                "brief",
                "revenue_mix",
                "products",
                "segments",
                "market_shares",
                "drivers",
                "financials",
            ):
                sources.extend(item.source for item in getattr(profile, field))
            for origin in sources:
                self._source(db, key, origin)
            # A successful replacement retracts only this profile's old claims.
            db.execute("DELETE FROM company_relations WHERE owner_id=?", (key,))
            for edge in profile.relations:
                target = self._entity(
                    db, edge.name, edge.symbol, edge.entity_id, edge.source.url,
                    registry=edge.registry_id
                )
                if target == key:
                    continue
                source_id = self._source(db, key, edge.source)
                db.execute(
                    "INSERT OR IGNORE INTO company_entity_sources VALUES(?,?)",
                    (target, source_id),
                )
                relation_id = digest(
                    encoded([key, target, edge.kind, edge.detail, source_id])
                )
                db.execute(
                    "INSERT OR REPLACE INTO company_relations VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        relation_id,
                        key,
                        key,
                        target,
                        edge.kind,
                        edge.detail,
                        source_id,
                        profile.fetched_at.isoformat() if profile.fetched_at else None,
                        edge.original,
                    ),
                )
            return key

    @staticmethod
    def _source(db, key, origin):
        src = origin.model_dump()
        source_id = digest(encoded(src))
        db.execute(
            "INSERT OR IGNORE INTO company_sources VALUES(?,?,?,?,?)",
            (source_id, src["label"], src["url"], src["as_of"], src["level"]),
        )
        db.execute(
            "INSERT OR IGNORE INTO company_entity_sources VALUES(?,?)", (key, source_id)
        )
        return source_id

    def entity(self, key):
        with self.connection() as db:
            row = self._resolve(db, key)
            if row is None:
                return None
            aliases = db.execute(
                "SELECT namespace,value FROM company_aliases WHERE entity_id=? ORDER BY namespace,value",
                (row["id"],),
            ).fetchall()
            row["symbols"] = [a["value"] for a in aliases if a["namespace"] == "ticker"]
            row["entity_id"] = next(
                (a["value"] for a in aliases if a["namespace"] == "wikidata"), None
            )
            row["registry_id"] = next(
                (a["value"] for a in aliases if a["namespace"] == "registry"), None
            )
            profile = db.execute(
                "SELECT payload FROM company_profiles WHERE entity_id=?", (row["id"],)
            ).fetchone()
            row["profile"] = (
                CompanyKnowledge.model_validate_json(profile[0]).model_dump(mode="json")
                if profile
                else None
            )
            row["sources"] = [
                dict(item)
                for item in db.execute(
                    "SELECT s.label,s.url,s.as_of,s.level FROM company_sources s JOIN company_entity_sources es ON s.id=es.source_id WHERE es.entity_id=? ORDER BY s.as_of DESC,s.id LIMIT 200",
                    (row["id"],),
                ).fetchall()
            ]
            return row

    def by_symbol(self, symbol):
        if not SYMBOL.fullmatch(symbol):
            raise ValueError("Invalid company symbol")
        if not self.path.exists():
            return None
        with self.connection() as db:
            row = db.execute(
                "SELECT entity_id FROM company_aliases WHERE namespace='ticker' AND value=?",
                (symbol,),
            ).fetchone()
        return self.entity(row[0]) if row else None

    def relations(self, key):
        with self.connection() as db:
            entity = self._resolve(db, key)
            if not entity:
                return []
            key = entity["id"]
            rows = db.execute(
                """SELECT r.*,s.label,s.url,s.as_of,s.level,
                       origin.name AS reported_by, other.id AS target_id,other.name
                 FROM company_relations r JOIN company_sources s ON s.id=r.source_id
                 JOIN company_entities origin ON origin.id=r.owner_id
                 JOIN company_entities other ON other.id=CASE WHEN r.subject_id=? THEN r.object_id ELSE r.subject_id END
                 WHERE (r.subject_id=? OR r.object_id=?) AND r.subject_id!=r.object_id
                 ORDER BY CASE WHEN r.kind IN ('supplier','customer','partner','competitor') THEN 0 ELSE 1 END,
                          r.observed_at DESC,r.id LIMIT 400""",
                (key, key, key),
            ).fetchall()
            ids = list({row['target_id'] for row in rows})
            aliases_by_id = {target:[] for target in ids}
            if ids:
                for alias in db.execute('SELECT entity_id,namespace,value FROM company_aliases WHERE entity_id IN (' + ','.join('?' for _ in ids) + ') ORDER BY namespace,value', ids):
                    aliases_by_id[alias['entity_id']].append(alias)
            result = []
            groups = {}
            seen = set()
            for row in rows:
                reverse = row["object_id"] == key
                kind = INVERSE[row["kind"]] if reverse else row["kind"]
                identity = (
                    row["target_id"],
                    kind,
                    row["source_id"],
                    row["detail"],
                    reverse,
                    row["reported_by"],
                )
                if identity in seen:
                    continue
                seen.add(identity)
                evidence = dict(
                    detail=row["detail"],
                    original=row['original'],
                    reverse=reverse,
                    reported_by=row["reported_by"],
                    observed_at=row["observed_at"],
                    source=Source(
                        label=row["label"],
                        url=row["url"],
                        as_of=row["as_of"],
                        level=row["level"],
                    ).model_dump(),
                )
                group_key = (row["target_id"], kind)
                if group_key in groups:
                    groups[group_key]["evidence"].append(evidence)
                    continue
                aliases = aliases_by_id[row['target_id']]
                relation = dict(
                    name=row["name"],
                    kind=kind,
                    detail=row["detail"],
                    original=row['original'],
                    target_id=row["target_id"],
                    reverse=reverse,
                    reported_by=row["reported_by"],
                    symbol=next(
                        (a["value"] for a in aliases if a["namespace"] == "ticker"),
                        None,
                    ),
                    entity_id=next(
                        (a["value"] for a in aliases if a["namespace"] == "wikidata"),
                        None,
                    ),
                    source=evidence["source"],
                    evidence=[evidence],
                )
                groups[group_key] = relation
                result.append(relation)
            return result
