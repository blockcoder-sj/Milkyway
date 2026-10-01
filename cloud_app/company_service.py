"""Local cached research and a bounded on-demand queue. HTTP never calls providers."""
import datetime as dt
import re
from fastapi import HTTPException
from .bounded_io import read_bounded_json
from .company_schemas import CompanyKnowledge
from .company_catalog import EDITORIAL_DIRECTORY, editorial_for
from .market_catalog import BY_ID
from .market_detail_catalog import KR_COMPANIES
from .market_details import read_cache
from .market_service import _write_cache

UTC = dt.timezone.utc
REFRESH_SECONDS = 86400
QUEUE_LIMIT = 200
SYMBOL = re.compile(r"[A-Z0-9][A-Z0-9.-]{0,19}")


def root(settings):
    if not settings.personal_local_mode or settings.production:
        raise HTTPException(404, "기업 정보를 찾을 수 없습니다")
    return settings.dataset_dir.parent / "company-details"


def company_row(settings, sector, symbol):
    root(settings)
    if (
        sector not in BY_ID
        or BY_ID[sector].group != "sectors"
        or not SYMBOL.fullmatch(symbol)
    ):
        raise HTTPException(404, "기업 정보를 찾을 수 없습니다")
    rows = read_cache(settings, sector).companies.rows
    row = next(
        (row.model_dump(mode="json") for row in rows if row.symbol == symbol), None
    )
    if row:
        return row
    # Korean editorial examples remain navigable while their quote snapshot refreshes.
    pair = next(
        (
            (code, name)
            for code, name in KR_COMPANIES.get(sector, [])
            if code + ".KS" == symbol
        ),
        None,
    )
    if pair:
        return dict(
            symbol=symbol,
            name=pair[1],
            market_cap=None,
            currency="KRW",
            displayed_share_pct=None,
            source="Npay 증권",
            url="https://m.stock.naver.com/domestic/stock/" + pair[0] + "/total",
        )
    if EDITORIAL_DIRECTORY.get(symbol, (None,))[0] == sector:
        notes = editorial_for(symbol)
        return dict(
            symbol=symbol,
            name=EDITORIAL_DIRECTORY[symbol][1],
            market_cap=None,
            currency="USD",
            displayed_share_pct=None,
            source=notes["description_source"]["label"],
            url=notes["description_source"]["url"],
        )
    raise HTTPException(404, "현재 섹터 기업 목록에 없는 종목입니다")


def read_company(settings, symbol):
    if not SYMBOL.fullmatch(symbol):
        raise ValueError("Invalid company symbol")
    from .company_graph import CompanyGraph

    stored = CompanyGraph(settings).by_symbol(symbol)
    if stored and stored["profile"]:
        value = CompanyKnowledge.model_validate(stored["profile"])
        # Different stock classes may identify the same issuer.
        value.symbol = symbol
        return value
    try:
        value = CompanyKnowledge.model_validate(
            read_bounded_json(
                root(settings) / (symbol + ".json"), maximum_bytes=2 * 1024 * 1024
            )
        )
        return value if value.symbol == symbol else None
    except (OSError, ValueError, TypeError):
        return None


def enqueue_company(settings, sector, symbol):
    row = company_row(settings, sector, symbol)
    now = dt.datetime.now(UTC)
    path = root(settings) / "requests" / (symbol + ".json")
    cached = read_company(settings, symbol)
    # Opening a page repeatedly cannot create unlimited provider calls.
    if (
        cached
        and cached.attempted_at
        and (now - cached.attempted_at).total_seconds() < 300
    ):
        return {"status": "recent", "symbol": symbol}
    if path.exists():
        return {"status": "queued", "symbol": symbol}
    from .company_graph import CompanyGraph

    entity = CompanyGraph(settings).by_symbol(symbol)
    if entity and path.with_name(entity["id"] + ".json").exists():
        return {"status": "queued", "symbol": symbol}
    requests = path.parent
    requests.mkdir(parents=True, exist_ok=True)
    if sum(1 for _ in requests.glob("*.json")) >= QUEUE_LIMIT:
        raise HTTPException(429, "기업 자료 수집 대기가 많습니다. 잠시 후 다시 요청해 주세요")
    _write_cache(
        path,
        {
            "sector": sector,
            "symbol": symbol,
            "name": row["name"],
            "requested_at": now.isoformat(),
        },
    )
    return {"status": "queued", "symbol": symbol}


def related_directory(settings, symbols, preferred_sector=None):
    wanted = set(symbols)
    found = {}
    if not wanted:
        return found
    for sector, rows in KR_COMPANIES.items():
        for code, name in rows:
            symbol = code + ".KS"
            if symbol in wanted and symbol not in found:
                found[symbol] = {"sector": sector, "name": name}
    for symbol, (sector, name) in EDITORIAL_DIRECTORY.items():
        if symbol in wanted and symbol not in found:
            found[symbol] = {"sector": sector, "name": name}
    sectors = sorted(
        (key for key, value in BY_ID.items() if value.group == "sectors"),
        key=lambda key: key != preferred_sector,
    )
    for sector in sectors:
        if wanted.issubset(found):
            break
        for row in read_cache(settings, sector).companies.rows:
            if row.symbol in wanted and row.symbol not in found:
                found[row.symbol] = {"sector": sector, "name": row.name}
    return found


def company_snapshot(settings, sector, symbol, now=None):
    row = company_row(settings, sector, symbol)
    now = now or dt.datetime.now(UTC)
    cached = read_company(settings, symbol)
    result = (
        cached.model_dump(mode="json")
        if cached
        else CompanyKnowledge(symbol=symbol, name=row["name"]).model_dump(mode="json")
    )
    # Source-backed notes are available immediately, even before an external fetch.
    notes = editorial_for(symbol)
    for key, value in notes.items():
        if key not in {"cik", "entity_id"} and not result.get(key):
            result[key] = value
    from .company_entities import identified
    from .company_graph import CompanyGraph

    graph = CompanyGraph(settings)
    profile = identified(result)
    existing = graph.by_symbol(symbol)
    if existing and not profile.entity_id:
        profile.entity_id = existing["entity_id"]
    result = profile.model_dump(mode="json")
    entity_key = graph.ingest(profile, sector)
    relations = graph.relations(entity_key)
    related = related_directory(
        settings,
        [edge["symbol"] for edge in result["relations"] if edge.get("symbol")],
        sector,
    )
    part = read_cache(settings, sector).companies
    peers = [
        item.model_dump(mode="json") for item in part.rows if item.symbol != symbol
    ][:80]
    comparable = bool(part.rows) and all(
        item.currency == row["currency"] and item.market_cap is not None
        for item in part.rows
    )
    return {
        **result,
        "entity_key": entity_key,
        "relations": relations,
        "collectable": True,
        "sector": sector,
        "sector_label": BY_ID[sector].label,
        "quote": row,
        "related_directory": related,
        "peers": peers,
        "quote_basis": {
            "count": len(part.rows),
            "market_cap_sum": sum(item.market_cap for item in part.rows)
            if comparable
            else None,
            "fetched_at": part.fetched_at.isoformat() if part.fetched_at else None,
        },
        "pending": any(
            (root(settings) / "requests" / (key + ".json")).exists()
            for key in (symbol, entity_key)
        ),
        "stale": not cached
        or bool(cached.errors)
        or not cached.fetched_at
        or (now - cached.fetched_at).total_seconds() > REFRESH_SECONDS,
        "refresh_seconds": REFRESH_SECONDS,
    }
