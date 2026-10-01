"""Company wiki pages and migration of pre-existing public research caches."""
import datetime as dt
import re
from fastapi import HTTPException

from .bounded_io import read_bounded_json
from .company_catalog import editorial_for, enrich, CATALOG
from .company_graph import CompanyGraph, ENTITY_KEY
from .company_schemas import CompanyKnowledge
from .market_catalog import BY_ID
from .market_service import _write_cache


def identified(value):
    """Recover a verified root ID from old cache attribution, never a name guess."""
    value = CompanyKnowledge.model_validate(value).model_dump(mode="json")
    if not value["entity_id"]:
        known = (
            editorial_for(value["symbol"]).get("entity_id") if value["symbol"] else None
        )
        for src in value["sources"]:
            match = re.fullmatch(
                r"https://www\.wikidata\.org/wiki/(Q\d{1,12})", src["url"]
            )
            if match and src["label"] == "Wikidata · 공개 기업 정보":
                known = match[1]
                break
        value["entity_id"] = known
    return CompanyKnowledge.model_validate(value)


def bootstrap(settings):
    from .company_service import root, related_directory, SYMBOL

    graph = CompanyGraph(settings)
    graph.remove_encyclopedia()
    imported = rejected = 0
    paths = [path for path in sorted(root(settings).glob('*.json')) if SYMBOL.fullmatch(path.stem)]
    directory = related_directory(settings, [path.stem for path in paths])
    # Read only the comparison timestamp; do not load each entity's 200 sources
    # or open thousands of SQLite connections during a repeated startup.
    with graph.connection() as db:
        for path in paths:
            try:
                raw = read_bounded_json(path, maximum_bytes=2 * 1024 * 1024)
                value = identified(enrich(raw))
                if value.symbol != path.stem:
                    raise ValueError('Wrong legacy company identity')
                clean = value.model_dump(mode='json')
                changed = raw != clean
                if changed:
                    _write_cache(path, clean)
                previous = db.execute(
                    "SELECT json_extract(p.payload,'$.attempted_at') AS attempted FROM company_profiles p "
                    "JOIN company_aliases a ON a.entity_id=p.entity_id WHERE a.namespace='ticker' AND a.value=?",
                    (value.symbol,),
                ).fetchone()
                if not changed and previous and (previous['attempted'] or '') >= (
                    value.attempted_at.isoformat() if value.attempted_at else ''):
                    continue
                graph.ingest(value, directory.get(value.symbol, {}).get('sector'))
                imported += 1
            except (OSError, ValueError, TypeError):
                rejected += 1
    return {"imported": imported, "rejected": rejected}


def seed_research(settings):
    """Publish vetted public research once at startup, with no provider calls."""
    from .company_research_catalog import PUBLIC_COMPANIES, RELATIONS, PRIVATE_COMPANIES, private_profile
    from .company_service import related_directory, read_company
    graph = CompanyGraph(settings)
    symbols = sorted(set(CATALOG) | set(PUBLIC_COMPANIES) | set(RELATIONS))
    directory = related_directory(settings, symbols)
    for symbol in symbols:
        old = read_company(settings, symbol)
        notes = PUBLIC_COMPANIES.get(symbol, {})
        name = directory.get(symbol, {}).get('name') or notes.get('name') or (old.name if old else symbol)
        profile = identified(enrich(old or CompanyKnowledge(symbol=symbol, name=name)))
        graph.ingest(profile, directory.get(symbol, {}).get('sector'))
    for key in PRIVATE_COMPANIES:
        graph.ingest(CompanyKnowledge.model_validate(private_profile(key)))


def get_entity(settings, key):
    from .company_service import root

    root(settings)
    if not ENTITY_KEY.fullmatch(key):
        raise HTTPException(404, "기업 정보를 찾을 수 없습니다")
    value = CompanyGraph(settings).entity(key)
    if value is None:
        raise HTTPException(404, "등록되지 않은 기업입니다")
    return value


def entity_snapshot(settings, key, now=None):
    from .company_service import (
        root,
        company_row,
        company_snapshot,
        related_directory,
        REFRESH_SECONDS,
    )

    entity = get_entity(settings, key)
    symbol = entity["symbols"][0] if entity["symbols"] else None
    # Keep prices/weights contextual to the actual classified directory.
    sector = entity["sector"]
    if symbol and sector is None:
        sector = related_directory(settings, [symbol]).get(symbol, {}).get("sector")
    if symbol and sector in BY_ID:
        try:
            company_row(settings, sector, symbol)
        except HTTPException:
            pass
        else:
            return company_snapshot(settings, sector, symbol, now)
    now = now or dt.datetime.now(dt.timezone.utc)
    value = entity["profile"] or CompanyKnowledge(
        symbol=symbol, entity_id=entity["entity_id"], registry_id=entity['registry_id'], name=entity["name"]
    ).model_dump(mode="json")
    value = enrich(value).model_dump(mode='json')
    relations = CompanyGraph(settings).relations(entity["id"])
    if not value["description"]:
        value["description"] = "출처가 있는 기업 관계 자료로 등록된 항목입니다. 제품·공시 등은 확보된 원자료만 표시합니다."
    if not value["sources"]:
        value["sources"] = entity["sources"]
    fetched = (
        dt.datetime.fromisoformat(value["fetched_at"]) if value["fetched_at"] else None
    )
    return {
        **value,
        "name": entity["name"],
        "entity_key": entity["id"],
        "entity_id": entity["entity_id"],
        "symbol": symbol,
        "sector": None,
        "sector_label": "기업 관계 자료",
        "relations": relations,
        "related_directory": {},
        "quote": {
            "market_cap": None,
            "currency": "",
            "displayed_share_pct": None,
            "source": "",
            "url": "",
        },
        "quote_basis": {},
        "peers": [],
        "pending": (root(settings) / "requests" / (entity["id"] + ".json")).exists(),
        "collectable": bool(symbol),
        "stale": not fetched
        or bool(value["errors"])
        or (now - fetched).total_seconds() > REFRESH_SECONDS,
        "refresh_seconds": REFRESH_SECONDS,
    }


def enqueue_entity(settings, key):
    from .company_service import root, QUEUE_LIMIT

    entity = get_entity(settings, key)
    symbol = entity["symbols"][0] if entity["symbols"] else None
    if not symbol:
        raise HTTPException(
            409, "이 기업은 검증된 공식 관계 자료로 제공합니다. 자동 공시 수집용 상장 종목은 등록되어 있지 않습니다"
        )
    profile = entity["profile"] or {}
    attempted = profile.get("attempted_at")
    now = dt.datetime.now(dt.timezone.utc)
    if attempted and (now - dt.datetime.fromisoformat(attempted)).total_seconds() < 300:
        return {"status": "recent", "entity_key": entity["id"]}
    path = root(settings) / "requests" / (entity["id"] + ".json")
    if path.exists() or (symbol and path.with_name(symbol + ".json").exists()):
        return {"status": "queued", "entity_key": entity["id"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    if sum(1 for _ in path.parent.glob("*.json")) >= QUEUE_LIMIT:
        raise HTTPException(429, "기업 자료 수집 대기가 많습니다. 잠시 후 다시 요청해 주세요")
    _write_cache(
        path,
        {
            "entity_key": entity["id"],
            "symbol": symbol,
            "entity_id": entity["entity_id"],
            "name": entity["name"],
            "sector": entity["sector"],
        },
    )
    return {"status": "queued", "entity_key": entity["id"]}
