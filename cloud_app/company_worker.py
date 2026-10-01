"""Company collection runs separately from trading and market workers."""
import time
import sqlite3
from fastapi import HTTPException
from .config import get_settings
from .database import RuntimeHeartbeat, SessionLocal, prepare_runtime_database, utcnow
from .bounded_io import read_bounded_json
from .company_feed import collect_company
from .company_schemas import CompanyKnowledge
from .company_service import root, read_company, company_row, SYMBOL
from .market_service import _write_cache
from .provider_process import ProviderProcess
from .company_graph import CompanyGraph
from .company_entities import get_entity, identified, bootstrap, seed_research
from .company_schedule import schedule, automatic
from .company_retention import preserve_previous

_provider = ProviderProcess(collect_company)


def process_request(settings, path):
    # Queue content is revalidated against the fixed sector directory, not trusted as a URL.
    value = read_bounded_json(path, maximum_bytes=4096)
    key = value.get("entity_key")
    if key:
        entity = get_entity(settings, key)
        symbol = entity["symbols"][0] if entity["symbols"] else None
        qid, sector = entity["entity_id"], entity["sector"]
        if (
            path.name != key + ".json"
            or key != entity["id"]
            or value.get("symbol") != symbol
            or value.get("entity_id") != qid
            or not symbol
        ):
            raise ValueError("Invalid registered company request")
        row = {"name": entity["name"]}
        old = (
            CompanyKnowledge.model_validate(entity["profile"])
            if entity["profile"]
            else None
        )
    else:
        symbol, sector = value["symbol"], value["sector"]
        if (
            not isinstance(symbol, str)
            or not SYMBOL.fullmatch(symbol)
            or path.name != symbol + ".json"
        ):
            raise ValueError("Invalid company request")
        row = company_row(settings, sector, symbol)
        old = read_company(settings, symbol)
        qid = identified(old).entity_id if old else None
    now = utcnow()
    try:
        result = _provider.run(
            {"symbol": symbol, "entity_id": qid, "name": row["name"]},
            {},
            deadline=time.monotonic() + 75,
        )
        parsed = identified(result)
        if parsed.symbol != symbol or (qid and parsed.entity_id != qid):
            raise ValueError("Wrong company result")
        preserve_previous(parsed, old)
        parsed.attempted_at = now
    except (RuntimeError, TimeoutError, OSError, ValueError):
        parsed = old or CompanyKnowledge(symbol=symbol, entity_id=qid, name=row["name"])
        parsed.errors = ["기업 자료 수집이 중단되었습니다. 기존 자료가 있다면 유지합니다."]
        parsed.attempted_at = now
    CompanyGraph(settings).ingest(identified(parsed), sector)
    if symbol:
        _write_cache(
            root(settings) / (symbol + ".json"), parsed.model_dump(mode="json")
        )
    path.unlink(missing_ok=True)
    return symbol or key


def main():
    settings = get_settings()
    if not settings.personal_local_mode or settings.production:
        raise SystemExit("Company worker requires personal mode")
    if settings.startup_errors("deployment"):
        raise SystemExit("Invalid personal configuration")
    prepare_runtime_database()
    bootstrap(settings)
    seed_research(settings)
    requests = root(settings) / "requests"
    requests.mkdir(parents=True, exist_ok=True)
    last_schedule = 0.0
    try:
        while True:
            if time.monotonic() - last_schedule >= 60:
                try:
                    schedule(settings)
                except (OSError, ValueError, sqlite3.Error):
                    pass
                last_schedule = time.monotonic()
            # User refreshes precede automatic background work. Heartbeat each issuer.
            pending = sorted(requests.glob("*.json"), key=lambda p: (automatic(p), p.stat().st_mtime))[:1]
            for path in pending:
                try:
                    detail = "company " + process_request(settings, path)
                except (OSError, ValueError, KeyError, TypeError, HTTPException):
                    path.unlink(missing_ok=True)
                    detail = "invalid company request rejected"
                except sqlite3.Error:
                    # Preserve the queued request on a transient database write failure.
                    detail = "company graph write deferred"
                with SessionLocal() as db:
                    heartbeat = db.get(
                        RuntimeHeartbeat, "company-data"
                    ) or RuntimeHeartbeat(
                        component="company-data", instance_id="personal-company-data"
                    )
                    heartbeat.observed_at, heartbeat.detail = utcnow(), detail
                    db.add(heartbeat)
                    db.commit()
            with SessionLocal() as db:
                heartbeat = db.get(
                    RuntimeHeartbeat, "company-data"
                ) or RuntimeHeartbeat(
                    component="company-data", instance_id="personal-company-data"
                )
                heartbeat.observed_at, heartbeat.detail = (
                    utcnow(),
                    "company research ready",
                )
                db.add(heartbeat)
                db.commit()
            time.sleep(1 if pending else 3)
    finally:
        _provider.close()


if __name__ == "__main__":
    main()
