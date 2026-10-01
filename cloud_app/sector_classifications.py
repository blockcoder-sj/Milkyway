"""Public fund disclosures cross-check sectors; this is not a licensed GICS master.

Only exact US exchange tickers are joined. Cash, derivatives, other markets and
ambiguous symbols are excluded. The HTTP app reads a local cache only.
"""
import csv
import datetime as dt
import io
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from .bounded_io import read_bounded_json, read_requests_bytes
from .company_schemas import Source
from .market_broker_feed import FixedSession

UTC = dt.timezone.utc
REFRESH_SECONDS = 86400
SECTORS = {
    "Energy": "us_10", "Materials": "us_15", "Industrials": "us_20",
    "Consumer Discretionary": "us_25", "Consumer Staples": "us_30",
    "Health Care": "us_35", "Financials": "us_40", "Information Technology": "us_45",
    "Communication": "us_50", "Communication Services": "us_50",
    "Utilities": "us_55", "Real Estate": "us_60",
}
FUNDS = {"XLE": "us_10", "XLB": "us_15", "XLI": "us_20", "XLY": "us_25",
         "XLP": "us_30", "XLV": "us_35", "XLF": "us_40", "XLK": "us_45",
         "XLC": "us_50", "XLU": "us_55", "XLRE": "us_60"}
ITOT_URL = "https://www.ishares.com/us/products/239724/ishares-core-s-p-total-u-s-stock-market-etf/latest-holdings.csv"
SYMBOL = re.compile(r"[A-Z][A-Z0-9.-]{0,19}")


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,19}$")
    name: str = Field(min_length=1, max_length=120)
    sector: str = Field(pattern=r"^us_(10|15|20|25|30|35|40|45|50|55|60)$")
    basis: str = Field(max_length=80)
    source: Source


class ClassificationCache(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: list[Classification] = Field(default_factory=list, max_length=6000)
    fetched_at: AwareDatetime | None = None
    attempted_at: AwareDatetime | None = None
    errors: list[str] = Field(default_factory=list, max_length=15)


class ReadOnlySource(Source):
    model_config = ConfigDict(extra='forbid', frozen=True)


class ReadOnlyClassification(Classification):
    model_config = ConfigDict(extra='forbid', frozen=True)
    source: ReadOnlySource


class ClassificationView(BaseModel):
    """Immutable shared snapshot; readers do not clone 6,000 nested models."""
    model_config = ConfigDict(extra='forbid', frozen=True)
    rows: tuple[ReadOnlyClassification, ...] = Field(default=(), max_length=6000)
    fetched_at: AwareDatetime | None = None
    attempted_at: AwareDatetime | None = None
    errors: tuple[str, ...] = Field(default=(), max_length=15)


def fund_url(ticker):
    if ticker not in FUNDS:
        raise ValueError("Unknown sector disclosure")
    return "https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-" + ticker.lower() + ".xlsx"


def fetch(url):
    if url not in {ITOT_URL, *(fund_url(t) for t in FUNDS)}:
        raise ValueError("Unapproved classification URL")
    with FixedSession() as session:
        response = session.get(url, headers={"User-Agent": "MilkywayPersonal/1.0"},
                               timeout=(3, 12), stream=True)
        try:
            response.raise_for_status()
            return read_requests_bytes(response, maximum_bytes=2 * 1024 * 1024)
        finally:
            response.close()


def date_value(value, pattern, now):
    when = dt.datetime.strptime(value, pattern).date()
    if not dt.date(2000, 1, 1) <= when <= now.date():
        raise ValueError("Invalid holdings date")
    return when.isoformat()


def parse_itot(raw, now):
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Oversized holdings")
    data = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(data) < 3 or len(data[1]) != 2 or data[1][0] != 'Fund Holdings as of' or data[0] != ["iShares Core S&P Total U.S. Stock Market ETF"] or len(data) > 6500:
        raise ValueError("Wrong holdings identity")
    when = date_value(data[1][1], "%b %d, %Y", now)
    index = next((i for i, row in enumerate(data[:30]) if row[:4] == ["Ticker", "Name", "Sector", "Asset Class"]), None)
    if index is None:
        raise ValueError("Missing holdings header")
    src = Source(label="iShares · ITOT 공식 보유종목 섹터", url=ITOT_URL, as_of=when)
    result = []
    for values in data[index + 1:]:
        row = dict(zip(data[index], values))
        if (row.get("Asset Class") != "Equity" or row.get("Location") != "United States"
            or row.get("Exchange") not in {"NASDAQ", "NYSE", "New York Stock Exchange Inc.", "NYSE Arca", "Nyse Mkt Llc", "Cboe BZX"}
            or row.get("Market Currency") != "USD" or row.get("Sector") not in SECTORS):
            continue
        symbol = row.get("Ticker", "").replace(".", "-")
        if not SYMBOL.fullmatch(symbol):
            continue
        result.append(Classification(symbol=symbol, name=row["Name"][:120],
            sector=SECTORS[row["Sector"]], basis="공식 운용사 섹터 공시 대조", source=src))
    if len(result) < 500:
        raise ValueError("Incomplete broad market disclosure")
    return result


def xlsx_rows(raw):
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Oversized spreadsheet")
    namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        files = archive.infolist()
        if len(files) > 100 or sum(f.file_size for f in files) > 8 * 1024 * 1024:
            raise ValueError("Oversized spreadsheet contents")
        def document(path):
            content = archive.read(path)
            checked = content.replace(b'\x00', b'').upper()
            if b"<!DOCTYPE" in checked or b"<!ENTITY" in checked:
                raise ValueError("Unsafe spreadsheet XML")
            return ET.fromstring(content)
        shared = ["".join(s.itertext()) for s in document("xl/sharedStrings.xml").findall("m:si", namespace)]
        sheet = document("xl/worksheets/sheet1.xml")
        rows = sheet.findall(".//m:row", namespace)
        if len(rows) > 1500 or len(shared) > 10000:
            raise ValueError("Too many spreadsheet rows")
        result = []
        for row in rows:
            cells = {}
            for cell in row:
                ref = re.fullmatch(r"([A-Z]{1,2})\d{1,5}", cell.get("r", ""))
                if not ref:
                    continue
                value = cell.find("m:v", namespace)
                text = value.text or "" if value is not None else ""
                if cell.get("t") == "s":
                    text = shared[int(text)]
                elif cell.get("t") == "inlineStr":
                    text = "".join(cell.itertext())
                cells[ref[1]] = text[:300]
            result.append(cells)
        return result


def parse_fund(raw, ticker, now):
    rows = xlsx_rows(raw)
    if len(rows) < 6 or rows[1].get("B") != ticker or rows[0].get("A") != "Fund Name:":
        raise ValueError("Wrong sector fund")
    when = date_value(rows[2].get("B", "").removeprefix("As of "), "%d-%b-%Y", now)
    header = next((i for i, row in enumerate(rows[:10]) if row.get("A") == "Name" and row.get("B") == "Ticker"), None)
    if header is None:
        raise ValueError("Missing sector holdings header")
    src = Source(label=f"State Street · {ticker} 공식 구성 공시", url=fund_url(ticker), as_of=when)
    result = []
    for row in rows[header + 1:]:
        symbol = row.get("B", "").replace(".", "-")
        # US common shares have a nine-character CUSIP. Exclude fund cash/futures.
        if (not SYMBOL.fullmatch(symbol) or row.get("H") != "USD"
            or not re.fullmatch(r"[A-Z0-9]{9}", row.get("C", ""))
            or "CASH" in row.get("A", "") or not row.get("A")):
            continue
        result.append(Classification(symbol=symbol, name=row["A"][:120], sector=FUNDS[ticker],
            basis="S&P Select Sector 연계 구성 공시 대조", source=src))
    if not result:
        raise ValueError("No sector constituents")
    return result


def collect(_payload, _configuration):
    now = dt.datetime.now(UTC)
    rows, errors = [], []
    try:
        rows.extend(parse_itot(fetch(ITOT_URL), now))
    except Exception:
        errors.append("iShares 전체 시장 섹터 공시 수신·검증 실패")
    def sector(ticker):
        return parse_fund(fetch(fund_url(ticker)), ticker, now)
    # At most three public requests concurrently; no retries or environment proxy.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [(ticker, pool.submit(sector, ticker)) for ticker in FUNDS]
        seen = {}
        for ticker, future in futures:
            try:
                for row in future.result():
                    if row.symbol in seen and seen[row.symbol].sector != row.sector:
                        raise ValueError("Conflicting sector memberships")
                    seen[row.symbol] = row
            except Exception:
                errors.append(ticker + " 구성 공시 수신·검증 실패")
    # Sector-specific disclosures have an explicit index sector link.
    by_symbol = {row.symbol: row for row in rows}
    by_symbol.update(seen)
    return ClassificationCache(rows=list(by_symbol.values()), fetched_at=now if by_symbol else None,
                               attempted_at=now, errors=errors).model_dump(mode="json")


def path(settings):
    if not settings.personal_local_mode or settings.production:
        raise ValueError("Classification requires personal mode")
    return settings.dataset_dir.parent / "market-classifications" / "sectors.json"


def read(settings):
    try:
        location = path(settings)
        stat = location.stat()
        return _read(str(location), stat.st_mtime_ns, stat.st_size).model_copy(deep=True)
    except (OSError, ValueError, TypeError):
        return ClassificationCache()


def read_view(settings):
    """Read-only cached view, invalidated by the atomic file's timestamp/size."""
    try:
        location = path(settings)
        stat = location.stat()
        return _read_view(str(location), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError, TypeError):
        return ClassificationView()


@lru_cache(maxsize=8)
def _read_view(location, mtime, size):
    return ClassificationView.model_validate(_read(location, mtime, size).model_dump(mode='json'))


@lru_cache(maxsize=8)
def _read(location, _mtime, _size):
    from pathlib import Path
    return ClassificationCache.model_validate(read_bounded_json(Path(location), maximum_bytes=4 * 1024 * 1024))


def refresh(settings, provider):
    from .market_service import _write_cache
    old = read(settings)
    value = ClassificationCache.model_validate(provider.run({}, {}, deadline=time.monotonic() + 55))
    # Preserve failed source disclosures; successful sources can remove membership.
    succeeded = {row.source.url for row in value.rows}
    retained = [row for row in old.rows if row.source.url not in succeeded] if value.errors else []
    value.rows = list({row.symbol: row for row in retained + value.rows}.values())[:6000]
    _write_cache(path(settings), value.model_dump(mode="json"))
    return value


def reconcile(rows, sector, cache, now=None):
    """Audit every received row and add disclosed members; never invent market caps."""
    now = now or dt.datetime.now(UTC)
    mapped = {row.symbol: row for row in cache.rows}
    result, removed = [], []
    for value in rows:
        row = dict(value)
        verified = mapped.get(row["symbol"])
        if verified and verified.sector != sector:
            removed.append({"symbol": row["symbol"], "sector": verified.sector})
            continue
        row["classification"] = verified.model_dump(mode="json") if verified else None
        result.append(row)
    present = {row["symbol"] for row in result}
    for row in cache.rows:
        if row.sector == sector and row.symbol not in present:
            result.append(dict(symbol=row.symbol, name=row.name, market_cap=None, currency="USD",
                displayed_share_pct=None, source="시가총액 수신 대기", url="https://finance.yahoo.com/quote/" + row.symbol + "/",
                classification=row.model_dump(mode="json")))
    result.sort(key=lambda row: (row.get("market_cap") is None, -(row.get("market_cap") or 0), row["name"]))
    if not all(row.get("market_cap") is not None for row in result):
        for row in result:
            row["displayed_share_pct"] = None
    else:
        total = sum(row["market_cap"] for row in result)
        for row in result:
            row["displayed_share_pct"] = row["market_cap"] / total * 100 if total else None
    stale = bool(cache.errors) or not cache.fetched_at or not -120 <= (now - cache.fetched_at).total_seconds() <= REFRESH_SECONDS * 3
    return result[:1100], dict(checked=len(rows), matched=sum(bool(r.get("classification")) for r in result[:1100]),
        unverified=sum(not r.get("classification") for r in result), moved=removed, stale=stale,
        omitted=max(0, len(result)-1100),
        fetched_at=cache.fetched_at.isoformat() if cache.fetched_at else None, errors=cache.errors,
        method="무료 공식 운용사 구성·섹터 공시 대조 · GICS 전체 원장 직접 검증과 구분")
