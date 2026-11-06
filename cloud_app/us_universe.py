"""Daily scans of every Toss-tradable US common equity, separate from execution.

HTTP readers only read the local SQLite cache. The bounded provider child has
fixed quote/catalog/candle endpoints and no account or order methods.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import sqlite3
import threading
import time
import os
import uuid
from dataclasses import replace
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select

from .bounded_io import read_requests_json
from .database import MarketDataConnection, SessionLocal, Strategy, RuntimeHeartbeat, utcnow
from .market_data_credentials import decrypt_market_credential
from .personal_data import EASTERN, last_completed_session
from .provider_process import ProviderProcess, ProviderOperationError
from .strategies import StrategySpec, raw_factor
from .toss_quotes import TossQuoteClient, TossCredentials, TossAuthenticationError, TossIpNotAllowedError, TossRateLimitError

MARKETS = ("NYSE", "NASDAQ", "AMEX", "US_ETC")
EQUITIES = {"STOCK", "FOREIGN_STOCK", "DEPOSITARY_RECEIPT", "REIT", "INFRASTRUCTURE_FUND"}
SYMBOL = re.compile(r"^[A-Z][A-Z0-9.-]{0,19}$")
_client = None
_pace_lock = threading.Lock()
_next_request = 0.0


class HistoryUnavailable(ValueError):
    pass


def key(spec):
    value = spec.model_dump(mode="json")
    value.pop("name", None); value.pop("description", None)
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def database_path(settings, owner):
    if not settings.personal_local_mode or settings.production or not re.fullmatch(r"[a-f0-9]{32}",owner):
        raise ValueError("Personal universe requires a local owner")
    return settings.dataset_dir.parent/"us-universe"/owner/"scan.sqlite3"


@contextmanager
def _db(settings, owner, write=False):
    path = database_path(settings, owner)
    if write:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path) if write else "file:"+str(path)+"?mode=ro", uri=not write, timeout=3)
    connection.row_factory = sqlite3.Row
    if write:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS meta (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS instruments (symbol TEXT PRIMARY KEY, name TEXT, market TEXT, epoch TEXT);
        CREATE TABLE IF NOT EXISTS histories (symbol TEXT PRIMARY KEY, epoch TEXT, rows TEXT NOT NULL, error TEXT);
        CREATE TABLE IF NOT EXISTS selections (id TEXT PRIMARY KEY, epoch TEXT, value TEXT NOT NULL);
        """)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _version(connection):
    if connection is None or connection.provider != "toss":
        return None
    return hashlib.sha256((str(connection.updated_at)+connection.encrypted_api_key+connection.encrypted_api_secret).encode()).hexdigest()


def _current_version(owner):
    with SessionLocal() as session:
        return _version(session.get(MarketDataConnection, owner))


def _meta(db):
    row = db.execute("SELECT value FROM meta WHERE id=1").fetchone()
    return json.loads(row[0]) if row else {}


def _save(db, value):
    db.execute("INSERT OR REPLACE INTO meta VALUES(1,?)", (json.dumps(value),));db.commit()


def status(settings, owner, spec=None):
    try:
        with _db(settings, owner) as db:
            value = _meta(db)
            result = {k:value.get(k) for k in ("state","total","processed","eligible","excluded","unavailable_history","first_session","required_session","updated_at","error","retry_at","markets")}
            if spec is not None:
                row = db.execute("SELECT epoch,value FROM selections WHERE id=?",(key(spec),)).fetchone()
                expected = last_completed_session().isoformat()
                result["ready"] = bool(row and row[0] == value.get("epoch") and value.get("state")=="ready" and value.get("required_session")==expected and value.get("epoch", "").startswith(utcnow().astimezone(EASTERN).date().isoformat()+"|"))
                result["ready"] = result["ready"] and value.get("epoch", "").endswith("|"+str(_current_version(owner)))
                result["candidates"] = json.loads(row[1])["targets"] if result["ready"] else []
            return result
    except (OSError,sqlite3.Error,ValueError,TypeError,KeyError):
        return {"state":"waiting","ready":False,"total":0,"processed":0,"candidates":[]}


def candidates(settings, owner, spec):
    value = status(settings,owner,spec)
    if not value.get("ready"):
        raise ValueError("미국 전체 종목 분석이 아직 준비되지 않았습니다")
    return value["candidates"]


def parse_catalog(payload, market):
    rows = payload.get("result")
    if not isinstance(rows,list) or len(rows)>30000:
        raise ValueError("Invalid universe catalog")
    selected = {}
    for item in rows:
        if not isinstance(item,dict):raise ValueError("Invalid universe item")
        if item.get("securityType") not in EQUITIES or item.get("isCommonShare") is not True:
            continue
        symbol, name = item.get("symbol"),item.get("name")
        if not isinstance(symbol,str) or not SYMBOL.fullmatch(symbol) or not isinstance(name,str) or len(name)>300:
            raise ValueError("Invalid equity identity")
        selected[symbol] = {"symbol":symbol,"name":name,"market":market}
    if market in {"NYSE","NASDAQ"} and not selected:
        raise ValueError("Empty primary US equity catalog")
    return list(selected.values())


def parse_candles(payload, required):
    result = payload.get("result")
    raw = result.get("candles") if isinstance(result,dict) else None
    if not isinstance(raw,list) or len(raw)>200:
        raise ValueError("Invalid daily candles")
    rows = {}
    for item in raw:
        if not isinstance(item,dict) or item.get("currency")!="USD":raise ValueError("Invalid candle currency")
        stamp = dt.datetime.fromisoformat(item["timestamp"].replace("Z","+00:00"))
        if stamp.tzinfo is None:raise ValueError("Candle timezone missing")
        day = stamp.astimezone(EASTERN).date()
        if day>required:continue  # Never rank today's incomplete daily candle.
        fields = [item[n] for n in ("openPrice","highPrice","lowPrice","closePrice","volume")]
        if any(isinstance(v,bool) for v in fields):raise ValueError("Invalid numeric candle")
        o,h,l,c,v = [float(v) for v in fields]
        if not all(math.isfinite(n) for n in (o,h,l,c,v)) or min(o,h,l,c)<=0 or max(o,h,l,c)>1e12 or not 0<=v<=1e16 or h<max(o,l,c) or l>min(o,h,c):
            raise ValueError("Invalid OHLCV")
        row = [day.isoformat(),o,h,l,c,v]
        if day in rows and rows[day]!=row:raise ValueError("Conflicting daily candle")
        rows[day]=row
    return [rows[d] for d in sorted(rows)],result.get("nextBefore")


def _request(client, path, params):
    global _next_request
    with _pace_lock:
        delay = _next_request-time.monotonic()
        if delay>0:time.sleep(delay)
        _next_request=time.monotonic()+.15
    response = client.session.get(client.base_url+path,params=params,headers=client._headers(),timeout=(3,10),stream=True)
    try:
        if response.status_code in {400,404}:
            raise HistoryUnavailable("History is not available for this instrument")
        client._raise_for_status(response)
        value=read_requests_json(response,maximum_bytes=8*1024*1024)
        client._raise_for_status(response,value)
        return value
    finally:response.close()


def _execute(payload, config):
    global _client
    if _client is None:_client=TossQuoteClient(TossCredentials(config["key"],config["secret"]))
    try:
        if payload["operation"]=="catalog":
            market=payload["market"]
            if market not in MARKETS:raise ValueError("Invalid exchange")
            return parse_catalog(_request(_client,"/api/v1/stocks/all",{"market":market,"status":"ACTIVE","commonShare":"true"}),market)
        required=dt.date.fromisoformat(payload["required"])
        def history(symbol):
            if not SYMBOL.fullmatch(symbol):raise ValueError("Invalid symbol")
            try:
                rows={};before=None
                for _ in range(2):
                    params={"symbol":symbol,"interval":"1d","count":200,"adjusted":"true"}
                    if before:params["before"]=before
                    values,before=parse_candles(_request(_client,"/api/v1/candles",params),required)
                    rows.update({r[0]:r for r in values})
                    if len(rows)>=max(payload.get("minimum",payload["needed"]),min(payload["needed"],199)) or not before:break
                return symbol,{"rows":[rows[d] for d in sorted(rows)],"error":None if rows else "unavailable"}
            except HistoryUnavailable:
                return symbol,{"rows":[],"error":"unavailable"}
            except (ValueError,KeyError,TypeError):
                return symbol,{"rows":[],"error":"invalid_history"}
        with ThreadPoolExecutor(max_workers=4) as pool:
            return dict(pool.map(history,payload["symbols"]))
    except TossRateLimitError as exc:
        raise HTTPException(429,"retry:"+str(min(3600,max(30,int(exc.retry_after))))) from None
    except TossIpNotAllowedError:
        raise HTTPException(403,"ip_not_allowed") from None
    except TossAuthenticationError:
        raise HTTPException(401,"authentication_failed") from None


def rank(rows, spec, required):
    values={};allowed=[]
    from market_calendar import is_trading_day
    days=[];day=required
    while len(days)<400:
        if is_trading_day(day):days.append(day)
        day-=dt.timedelta(days=1)
    calendar=pd.DatetimeIndex(sorted(days))
    # One issuer at a time keeps a whole-market scan out of the execution RAM.
    for symbol,bars in rows:
        if not bars:continue
        frame=pd.DataFrame(bars,columns=["Date","Open","High","Low","Close","Volume"]).set_index("Date")
        frame.index=pd.DatetimeIndex(frame.index)
        if frame.index[-1].date()!=required:continue
        frame=frame.reindex(calendar)
        panels={name:frame[[name]].rename(columns={name:symbol}) for name in ("Open","High","Low","Close","Volume")}
        vector=[]
        for factor in spec.factors:
            value=raw_factor(factor.kind,factor.lookback,panels).iloc[-1,0]
            vector.append(float(value) if pd.notna(value) else float("nan"))
        values[symbol]=vector
        tail=frame.tail(spec.filters.history_days)
        if len(tail)>=spec.filters.history_days and tail["Close"].notna().all() and tail["Volume"].mean()>=spec.filters.min_average_volume and tail["Close"].iloc[-1]>=spec.filters.min_price:
            allowed.append(symbol)
    if not values:return [],0
    factors=pd.DataFrame.from_dict(values,orient="index")
    scored=factors.rank(pct=True,method="average").fillna(0).mul([f.weight for f in spec.factors]).sum(axis=1)
    weighted=factors.notna().mul([abs(f.weight) for f in spec.factors]).sum(axis=1)>0
    scored=scored.where(weighted).reindex(allowed).dropna()
    # Stable ticker order resolves score ties reproducibly across restarts.
    scored=scored.sort_index().sort_values(ascending=False,kind="stable")
    return list(scored.head(spec.portfolio.max_positions).index),len(scored)


def _configuration(row, settings):
    return {field:decrypt_market_credential(getattr(row,"encrypted_api_"+field),settings,owner_id=row.user_id,
        provider=row.provider,environment=row.environment,label=label) for field,label in (("key","App Key"),("secret","App Secret"))}


def tick(settings, runner, requested_specs=None):
    with SessionLocal() as session:
        strategies=list(requested_specs or [])
        if requested_specs is None:
            for row in session.scalars(select(Strategy)).all():
                spec=StrategySpec.model_validate_json(row.spec_json)
                if spec.universe=="us_market":strategies.append((row.user_id,spec))
        if not strategies:return
        owner=strategies[0][0]
        connection=session.get(MarketDataConnection,owner)
        if connection is None or connection.provider!="toss":return
        configuration=_configuration(connection,settings)
        version=_version(connection)
    specs=[s for user,s in strategies if user==owner]
    now=utcnow();required=last_completed_session(now)
    needed=max([200,*[f.lookback+1 for s in specs for f in s.factors],*[s.filters.history_days for s in specs]])
    epoch="|".join([now.astimezone(EASTERN).date().isoformat(),required.isoformat(),str(needed),version])
    with _db(settings,owner,write=True) as db:
        meta=_meta(db)
        if meta.get("epoch")!=epoch:meta={"epoch":epoch,"state":"catalog","markets":[],"processed":0,"total":0,"required_session":required.isoformat()}
        if meta.get("retry_at",0)>time.time():return
        if meta.get("state")=="ready" and not meta.get("first_session"):
            meta["first_session"] = db.execute("SELECT min(json_extract(rows,'$[0][0]')) FROM histories WHERE epoch=? AND error IS NULL AND json_extract(rows,'$[#-1][0]')=?",(epoch,required.isoformat())).fetchone()[0]
            _save(db,meta)
        if meta.get("state")=="ready" and all(db.execute("SELECT 1 FROM selections WHERE id=? AND epoch=?",(key(s),epoch)).fetchone() for s in specs):return
        try:
            pending=[m for m in MARKETS if m not in meta["markets"]]
            if pending:
                market=pending[0]
                rows=runner.run({"operation":"catalog","market":market},configuration,deadline=time.monotonic()+35)
                if _current_version(owner) != version:return
                db.executemany("INSERT OR REPLACE INTO instruments VALUES(?,?,?,?)",[(r["symbol"],r["name"],market,epoch) for r in rows])
                meta["markets"].append(market);meta["state"]="catalog"
            else:
                symbols=[r[0] for r in db.execute("SELECT i.symbol FROM instruments i LEFT JOIN histories h ON h.symbol=i.symbol WHERE i.epoch=? AND (h.epoch IS NULL OR h.epoch!=?) ORDER BY i.symbol LIMIT 48",(epoch,epoch))]
                if symbols:
                    rows=runner.run({"operation":"history","symbols":symbols,"required":required.isoformat(),"needed":needed,"minimum":max([s.filters.history_days for s in specs]+[f.lookback+1 for s in specs for f in s.factors])},configuration,deadline=time.monotonic()+90)
                    if _current_version(owner) != version:return
                    if set(rows)!=set(symbols):raise ValueError("Incomplete scan batch")
                    stored=[]
                    for symbol in symbols:
                        value=rows[symbol]
                        if isinstance(value,list):value={"rows":value,"error":None}
                        if not isinstance(value,dict) or not isinstance(value.get("rows"),list) or value.get("error") not in {None,"unavailable","invalid_history"}:
                            raise ValueError("Invalid scan result")
                        stored.append((symbol,epoch,json.dumps(value["rows"]),value.get("error")))
                    db.executemany("INSERT OR REPLACE INTO histories VALUES(?,?,?,?)",stored)
                    meta["state"]="scanning"
                else:
                    for spec in specs:
                        iterator=((r[0],json.loads(r[1])) for r in db.execute("SELECT i.symbol,h.rows FROM instruments i JOIN histories h ON h.symbol=i.symbol WHERE i.epoch=? AND h.epoch=? AND h.error IS NULL ORDER BY i.symbol",(epoch,epoch)))
                        targets,eligible=rank(iterator,spec,required)
                        db.execute("INSERT OR REPLACE INTO selections VALUES(?,?,?)",(key(spec),epoch,json.dumps({"targets":targets,"eligible":eligible})))
                        meta["eligible"]=eligible
                    if not meta.get("dataset_generation"):
                        meta["dataset_generation"]=_export(db,settings,epoch,required)
                    meta["state"]="ready"
                    meta["first_session"] = db.execute("SELECT min(json_extract(rows,'$[0][0]')) FROM histories WHERE epoch=? AND error IS NULL AND json_extract(rows,'$[#-1][0]')=?",(epoch,required.isoformat())).fetchone()[0]
            if _current_version(owner) != version:
                db.rollback()
                return
            meta["total"]=db.execute("SELECT count(*) FROM instruments WHERE epoch=?",(epoch,)).fetchone()[0]
            meta["processed"]=db.execute("SELECT count(*) FROM histories WHERE epoch=?",(epoch,)).fetchone()[0]
            meta["unavailable_history"]=db.execute("SELECT count(*) FROM histories WHERE epoch=? AND error IS NOT NULL",(epoch,)).fetchone()[0]
            meta["excluded"]=max(0,meta.get("total",0)-meta.get("eligible",0)) if meta["state"]=="ready" else None
            meta["error"]=None;meta["retry_at"]=0
        except (ProviderOperationError,RuntimeError,TimeoutError,ValueError,OSError) as exc:
            db.rollback()
            detail=getattr(exc,"detail","")
            delay=int(detail.split(":")[1]) if isinstance(detail,str) and re.fullmatch(r"retry:\d{1,4}",detail) else 60
            meta["error"]="rate_limited" if getattr(exc,"status_code",0)==429 else detail if detail in {"ip_not_allowed","authentication_failed"} else "provider_unavailable"
            meta["retry_at"]=time.time()+delay
        meta["updated_at"]=utcnow().isoformat();_save(db,meta)


def _export(db, settings, epoch, required):
    """Freeze the same full scan for reproducible exploratory backtests."""
    from price_data_pipeline import _atomic_price_frame, price_file_path, sha256_file
    from universe_snapshot import build_legacy_snapshot, save_snapshot
    from .local_demo import _atomic_json
    root=settings.dataset_dir/"generations"
    root.mkdir(parents=True,exist_ok=True)
    name=uuid.uuid4().hex
    staging=root/(".universe-"+name);staging.mkdir(mode=0o700)
    metadata={};exchanges={}
    for row in db.execute("SELECT i.symbol,i.market,h.rows FROM instruments i JOIN histories h ON i.symbol=h.symbol WHERE i.epoch=? AND h.epoch=? AND h.error IS NULL ORDER BY i.symbol",(epoch,epoch)):
        bars=json.loads(row[2])[-max(200,int(epoch.split("|")[2])):]
        if not bars:continue
        frame=pd.DataFrame(bars,columns=["Date","Open","High","Low","Close","Volume"]).set_index("Date")
        frame.index=pd.DatetimeIndex(frame.index)
        if frame.index[-1].date()!=required:continue
        path=price_file_path(staging/"prices",row[0]);_atomic_price_frame(frame,path)
        metadata[row[0]]={"rows":len(frame),"first_date":frame.index[0].date().isoformat(),"last_date":required.isoformat(),"sha256":sha256_file(path)}
        exchanges[row[0]]=row[1]
    if not metadata:raise ValueError("No completed full-market history")
    snapshot=build_legacy_snapshot(exchanges,effective_date=min(r["first_date"] for r in metadata.values()))
    for record in snapshot["records"]:
        record["exchange"]=exchanges[record["symbol"]]
        record["eligible"]=True
    snapshot["membership_sha256"]=hashlib.sha256(json.dumps(snapshot["records"],ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    snapshot.update(snapshot_type="personal_selected_universe",allowed_exchanges=[],provenance="current Toss-tradable full US equity catalog; not historical listing evidence",notes="Current-membership exploratory tests only")
    save_snapshot(snapshot,staging/"snapshots")
    _atomic_json(staging/"manifest.json",{"schema_version":2,"price_format":"csv-gzip-v1","dataset_kind":"personal_selected_universe","universe_scope":"us_market","source":"toss","auto_adjust":True,"updated_at":utcnow().isoformat(),"prices":metadata,"corporate_actions":{}})
    _atomic_json(staging/"validation_report.json",{"forward_strategy_data_gate_ready":False,"window":{"end":required.isoformat()},"strategy_candidate_data_blockers":[]})
    os.replace(staging,root/name)
    return name


def dataset_settings(settings, owner=None):
    from .bounded_io import read_bounded_json
    path=settings.dataset_dir/"manifest.json"
    if path.is_file() and read_bounded_json(path,maximum_bytes=32*1024*1024).get("universe_scope")=="us_market":return settings
    if owner is None:
        from .personal_auth import local_owner
        with SessionLocal() as session:owner=local_owner(session).id
    with _db(settings,owner) as db:
        meta=_meta(db);name=meta.get("dataset_generation","")
        if meta.get("state")!="ready" or not re.fullmatch(r"[a-f0-9]{32}",name):raise ValueError("미국 전체 종목의 일봉 수집 완료를 기다려 주세요")
    generation=settings.dataset_dir/"generations"/name
    return replace(settings,dataset_dir=generation,snapshots_glob=str(generation/"snapshots/*.json"))


def main():
    from .config import get_settings
    from .database import prepare_runtime_database
    settings=get_settings()
    if not settings.personal_local_mode or settings.production:raise SystemExit("Universe worker requires personal mode")
    if settings.startup_errors("deployment"):raise SystemExit("Invalid personal universe configuration")
    prepare_runtime_database();runner=ProviderProcess(_execute)
    try:
        while True:
            try:tick(settings,runner);detail="running"
            except Exception as exc:detail="error="+type(exc).__name__
            with SessionLocal() as session:
                row=session.get(RuntimeHeartbeat,"universe-data")
                if row is None:row=RuntimeHeartbeat(component="universe-data",instance_id="us-market-scan");session.add(row)
                row.observed_at=utcnow();row.detail=detail;session.commit()
            time.sleep(2)
    finally:runner.close()


if __name__=="__main__":main()
