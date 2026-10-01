"""Bounded public research. SEC contact headers only; no AI or trading calls."""
import datetime as dt
import math
import os
import re
import time
from urllib.parse import quote, urlsplit
from bs4 import BeautifulSoup
from .bounded_io import read_requests_json, read_requests_bytes
from .market_broker_feed import FixedSession
from .company_schemas import CompanyKnowledge
from .company_revenue import parse_revenue
from .company_catalog import editorial_for
from .company_filings import document, parse_report, parse_subsidiaries, subsidiary_document

UTC = dt.timezone.utc
AGENT = "MilkywayPersonal/1.0"
_sec_last_request = 0.0
_sec_index = None
_sec_index_at = 0.0
_sec_names = None
_cooldowns = {}


class SourceCoolingDown(RuntimeError):
    """A source asked this collector to pause. No request or retry is made."""


def respect_source_limit(host):
    global _sec_last_request
    now = time.monotonic()
    if now < _cooldowns.get(host, 0):
        raise SourceCoolingDown("Source request limit")
    if host in {"data.sec.gov", "www.sec.gov"}:
        time.sleep(max(0, 0.35 - (now - _sec_last_request)))
        _sec_last_request = time.monotonic()


def remember_source_limit(host, response):
    if response.status_code != 429:
        return
    # No automatic retry. Bound an untrusted Retry-After header and pause this host.
    raw = str(response.headers.get("Retry-After", ""))[:100]
    try:
        seconds = int(raw)
    except ValueError:
        from email.utils import parsedate_to_datetime
        try:
            seconds = (parsedate_to_datetime(raw) - dt.datetime.now(UTC)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            seconds = 60
    _cooldowns[host] = time.monotonic() + max(60, min(seconds, 86400))


def get(url, params=None, maximum=4 * 1024 * 1024, html=False):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname
        not in {
            "data.sec.gov",
            "www.sec.gov",
            "comp.wisereport.co.kr",
        }
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("Unapproved company data host")
    headers = {"User-Agent": AGENT, "Accept": "text/html" if html else "application/json"}
    if parsed.hostname in {"data.sec.gov", "www.sec.gov"}:
        contact = os.getenv("SEC_CONTACT_EMAIL", "").strip()
        if contact and not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9.-]{1,180}\.[A-Za-z]{2,24}", contact):
            raise ValueError("SEC contact configuration invalid")
        if parsed.hostname == "www.sec.gov":
            if not contact:
                raise ValueError("SEC contact configuration required")
            if not (parsed.path == "/files/company_tickers.json" or re.fullmatch(
                r"/Archives/edgar/data/\d{1,10}/\d{18}/[A-Za-z0-9_.-]{1,160}", parsed.path
            ) and parsed.path.rsplit("/", 1)[-1] not in {".", ".."}):
                raise ValueError("Unapproved SEC document path")
        if contact:
            headers["User-Agent"] = AGENT + " " + contact
    respect_source_limit(parsed.hostname)
    with FixedSession() as session:
        response = session.get(
            url,
            params=params,
            headers=headers,
            timeout=(3, 15),
            stream=True,
        )
        try:
            remember_source_limit(parsed.hostname, response)
            response.raise_for_status()
            return (
                read_requests_bytes(response, maximum_bytes=maximum)
                if html
                else read_requests_json(response, maximum_bytes=maximum)
            )
        finally:
            response.close()


def source(label, url, as_of=None, level="primary"):
    return dict(label=label, url=url, as_of=as_of, level=level)


def parse_sec(submissions, facts, symbol, now):
    # Reject a mistaken CIK/entity match before using any financial figures.
    if symbol not in submissions.get("tickers", []):
        raise ValueError("SEC ticker mismatch")
    cik = int(submissions["cik"])
    recent = submissions.get("filings", {}).get("recent", {})
    if facts and int(facts.get("cik", -1)) != cik:
        raise ValueError("SEC companyfacts identity mismatch")
    filings = []
    forms = recent.get("form", [])
    for index, form in enumerate(forms[:50000]):
        if form not in {"10-K", "10-Q", "20-F", "40-F", "10-K/A"}:
            continue
        filing_date = recent["filingDate"][index]
        if filing_date > now.date().isoformat():
            continue
        accession = recent["accessionNumber"][index].replace("-", "")
        document = recent["primaryDocument"][index]
        if not re.fullmatch(r"\d{18}", accession) or not re.fullmatch(
            r"[A-Za-z0-9_.-]{1,160}", document
        ):
            continue
        filings.append(
            source(
                "SEC · " + form,
                f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{quote(document,safe="")}',
                filing_date,
            )
        )
        if len(filings) == 8:
            break
    source_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
    metric_tags = [
        (
            "매출",
            (
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
            ),
        ),
        ("영업이익", ("OperatingIncomeLoss",)),
        ("순이익", ("NetIncomeLoss", "ProfitLoss")),
        ("총자산", ("Assets",)),
        ("총부채", ("Liabilities",)),
        ("자기자본", ("StockholdersEquity",)),
    ]
    financials = []
    definitions = (facts or {}).get("facts", {}).get("us-gaap", {})
    for label, tags in metric_tags:
        candidates = []
        for tag in tags:
            for row in definitions.get(tag, {}).get("units", {}).get("USD", [])[:10000]:
                if (
                    row.get("form") not in {"10-K", "10-K/A", "20-F", "40-F"}
                    or row.get("fp") != "FY"
                ):
                    continue
                end = row.get("end", "")
                filed = row.get("filed", "")
                try:
                    if (
                        not end
                        or not filed
                        or end > now.date().isoformat()
                        or filed > now.date().isoformat()
                    ):
                        continue
                    dt.date.fromisoformat(end)
                    dt.date.fromisoformat(filed)
                    if label in {"매출", "영업이익", "순이익"}:
                        duration = (
                            dt.date.fromisoformat(end)
                            - dt.date.fromisoformat(row["start"])
                        ).days
                        if not 300 <= duration <= 400:
                            continue
                    value = row["val"]
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                        or abs(value) > 1e16
                    ):
                        continue
                    candidates.append((end, filed, tag, row))
                except (ValueError, TypeError, KeyError):
                    continue
        if candidates:
            end, filed, tag, row = max(
                candidates,
                key=lambda value: (value[0], value[1], -tags.index(value[2])),
            )
            financials.append(
                dict(
                    label=label,
                    value=row["val"],
                    unit="USD",
                    period=(row.get("start", "") + " ~ " if row.get("start") else "")
                    + end,
                    source=source("SEC XBRL · " + tag, source_url, filed),
                )
            )
    return dict(
        financials=financials,
        filings=filings,
        sources=filings
        + [
            source(
                "SEC · 기업 공시 정보", f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
            )
        ],
        facts=[
            dict(
                title="산업 분류",
                detail=("SEC의 SIC 산업 분류 코드 " + str(submissions.get('sic', '미제공'))
                    + "입니다. 시장 화면의 GICS 섹터와는 분류 체계가 다릅니다."),
                original=submissions.get("sicDescription", "")[:1500],
                source=source(
                    "SEC · SIC 산업 분류",
                    f"https://data.sec.gov/submissions/CIK{cik:010d}.json",
                ),
            )
        ],
    )


def sec_company(symbol, cik):
    now = dt.datetime.now(UTC)
    submissions = get(
        f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
        maximum=8 * 1024 * 1024,
    )
    error = None
    try:
        facts = get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json",
            maximum=8 * 1024 * 1024,
        )
    except Exception as exc:
        facts = {}
        error = collection_error("SEC 재무 수치", exc)
    result = parse_sec(submissions, facts, symbol, now)
    if error:
        result["errors"] = [error]
        result["unavailable_sources"] = ["sec_financials"]
    # A recent amendment can contain only a cover/signature page. Prefer the
    # complete annual filing and retain amendments in the public filing list.
    annual = next((filing for filing in result["filings"] if filing["label"] in {
        "SEC · 10-K", "SEC · 20-F", "SEC · 40-F"
    }), None) or next((filing for filing in result["filings"] if filing["label"] == "SEC · 10-K/A"), None)
    if annual:
        try:
            if not re.search(r"\.html?$", annual["url"], re.I):
                raise ValueError("Unsupported filing document format")
            raw = get(annual["url"], maximum=24 * 1024 * 1024, html=True)
            parsed_document = document(raw)
            result['revenue_mix'] = parse_revenue(parsed_document, annual, symbol)
            try:
                sec_identity('__INDEX_ONLY__')
                names = _sec_names
            except Exception:
                # An unavailable identity index never replaces verified aliases
                # or invalidates the actual issuer filing we already received.
                names = None
            analysis = parse_report(parsed_document, symbol, annual, names)
            for key, value in analysis.items():
                result[key] = result.get(key, []) + value if isinstance(value, list) else value
            base = annual["url"].rsplit("/", 1)[0] + "/"
            try:
                exhibit_url = subsidiary_document(parsed_document, annual["url"])
                if not exhibit_url:
                    index = get(base + "index.json", maximum=1024 * 1024)
                    exhibit = next((item.get("name", "") for item in index.get("directory", {}).get("item", [])[:2000]
                        if re.fullmatch(r"[A-Za-z0-9_.-]{1,160}", item.get("name", ""))
                        and re.search(r"(?:ex(?:hibit)?[-_]?21(?:1|01)?)[_.-].*|(?:ex(?:hibit)?[-_]?21(?:1|01)?)\.html?$", item["name"], re.I)
                        and re.search(r"\.html?$", item["name"], re.I)), None)
                    exhibit_url = base + exhibit if exhibit else None
                if exhibit_url:
                    origin = source("SEC · Exhibit 21 자회사 명세서", exhibit_url, annual["as_of"] if exhibit_url.startswith(base) else None)
                    subsidiaries = parse_subsidiaries(get(origin["url"], maximum=4 * 1024 * 1024, html=True), origin)
                    result["relations"] += subsidiaries
                    result["sources"].append(origin)
                    result["report_analysis"]["detail"] += f" 자회사 명세서에서 {len(subsidiaries):,}건을 추가했습니다(최대 80건)."
                else:
                    result["report_analysis"]["detail"] += " 이번 공시에서 지원 형식의 자회사 명세서 링크를 찾지 못했습니다."
            except Exception as exc:
                result.setdefault("errors", []).append(collection_error("SEC 자회사 명세서", exc))
                result.setdefault("unavailable_sources", []).append("sec_subsidiaries")
        except Exception as exc:
            result.setdefault("errors", []).append(collection_error("SEC 공시 본문", exc))
            result.setdefault("unavailable_sources", []).extend(["sec_report", "sec_subsidiaries"])
    return result


def sec_identity(symbol):
    """Official exact ticker lookup; do not depend on an encyclopedia match."""
    global _sec_index, _sec_index_at, _sec_names
    if _sec_index is None or time.monotonic() - _sec_index_at > 86400:
        raw = get("https://www.sec.gov/files/company_tickers.json", maximum=4 * 1024 * 1024)
        rows = raw.values() if isinstance(raw, dict) else []
        _sec_index = {row["ticker"]: str(row["cik_str"]) for row in rows
            if isinstance(row, dict) and isinstance(row.get("ticker"), str)
            and re.fullmatch(r"\d{1,10}", str(row.get("cik_str", "")))}
        from .company_names import SecNameIndex
        _sec_names = SecNameIndex(raw.values() if isinstance(raw, dict) else [])
        _sec_index_at = time.monotonic()
    return _sec_index.get(symbol)


def collection_error(label, exc):
    """Known diagnostics only: no remote response text, credentials or headers."""
    from requests import HTTPError, Timeout, RequestException
    from .bounded_io import ResponseTooLarge
    if isinstance(exc, HTTPError):
        status = getattr(exc.response, "status_code", None)
        detail = f"HTTP {status}" if status in {400, 401, 403, 404, 429, 500, 502, 503, 504} else "공급자 HTTP 오류"
    elif isinstance(exc, SourceCoolingDown):
        detail = "공급자 요청 제한에 따른 대기 중 · 이번 출처는 재호출하지 않음"
    elif isinstance(exc, ResponseTooLarge):
        detail = "자료가 수신 크기 제한을 초과함"
    elif isinstance(exc, (Timeout, TimeoutError)):
        detail = "응답 시간 초과"
    elif isinstance(exc, RequestException):
        detail = "네트워크 연결 실패"
    elif isinstance(exc, ValueError) and str(exc).startswith("SEC contact configuration"):
        detail = ".env의 SEC_CONTACT_EMAIL 확인 후 기업 수집 프로세스 재시작 필요"
    else:
        detail = "식별자 또는 문서 형식을 확인할 수 없음"
    return f"{label} 수신·검증 실패 ({detail}). 확보한 다른 원자료는 유지합니다"


def parse_wise(raw, symbol):
    soup = BeautifulSoup(raw, "html.parser")
    code = symbol[:6]
    header = soup.select_one("#comInfo")
    if header is None or code not in header.get_text(" ", strip=True):
        raise ValueError("Wrong company overview")
    url = "https://comp.wisereport.co.kr/company/c1020001.aspx?cmp_cd=" + code
    src = source("Npay 증권 · WiseReport 기업개요", url, level="provider")
    facts = []
    table = soup.select_one("#cTB201")
    if table:
        for tr in table.select("tr"):
            cells = tr.select("th,td")
            for index in range(0, len(cells) - 1, 2):
                title = cells[index].get_text(" ", strip=True)
                value = cells[index + 1].get_text(" ", strip=True)
                if title and value and title not in {"항목", "내용"}:
                    facts.append(
                        dict(title=title[:160], detail=value[:1500], source=src)
                    )
    segments = []
    table = soup.select_one("#cTB203")
    if table:
        for tr in table.select("tbody tr")[:30]:
            cells = tr.select("td")
            if len(cells) >= 2:
                name = cells[0].get_text(" ", strip=True)
                share = cells[1].get_text(" ", strip=True)
                if name:
                    segments.append(
                        dict(
                            title=name[:160],
                            detail="공급자 매출 구성비 "
                            + share
                            + "%. 기준 기간과 연결 조정은 원문을 확인하세요. 제품 시장점유율이 아닙니다.",
                            source=src,
                        )
                    )
    # Market shares with no verified scope/date are deliberately not promoted to comparable metrics.
    return dict(
        facts=facts[:25],
        segments=segments,
        sources=[src, source("DART · 기업 사업보고서", "https://dart.fss.or.kr/")],
    )


def wise_company(symbol):
    return parse_wise(
        get(
            "https://comp.wisereport.co.kr/company/c1020001.aspx",
            {"cmp_cd": symbol[:6]},
            maximum=2 * 1024 * 1024,
            html=True,
        ),
        symbol,
    )


def collect_company(payload, _configuration):
    symbol = payload.get("symbol")
    name = payload["name"]
    if symbol is not None and not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,19}", symbol):
        raise ValueError("Invalid symbol")
    requested_qid = payload.get("entity_id")
    if requested_qid is not None and not re.fullmatch(r"Q\d{1,12}", requested_qid):
        raise ValueError("Invalid company entity")
    if not symbol and not requested_qid:
        raise ValueError("Missing company identity")
    editorial = editorial_for(symbol) if symbol else {}
    result = {"symbol": symbol, "name": name[:120], "errors": [], "sources": [], "unavailable_sources": []}
    cik = editorial.pop("cik", None)
    qid = requested_qid or editorial.pop("entity_id", None)
    editorial.pop("entity_id", None)
    result["entity_id"] = qid
    if not cik and symbol and not symbol.endswith(".KS"):
        try:
            cik = sec_identity(symbol)
        except Exception as exc:
            result["errors"].append(collection_error("SEC 종목·CIK 목록", exc))
            result["unavailable_sources"].append("sec")
    try:
        extra = (
            wise_company(symbol)
            if symbol and symbol.endswith(".KS")
            else sec_company(symbol, cik)
            if cik and symbol
            else {}
        )
        for key, value in extra.items():
            result[key] = value + result.get(key, []) if isinstance(value, list) else value
        if symbol and not symbol.endswith(".KS") and not cik:
            result["errors"].append("SEC 기업 식별자가 확인되지 않아 공시 재무 수치를 표시하지 않습니다")
    except Exception as exc:
        result["errors"].append(collection_error("기업 공시·개요", exc))
        result["unavailable_sources"].append("wise" if symbol and symbol.endswith(".KS") else "sec")
    for key, value in editorial.items():
        if isinstance(value, list):
            result[key] = value + result.get(key, [])
        elif value:
            result[key] = value
    for key in [
        "facts",
        "products",
        "segments",
        "market_shares",
        "drivers",
        "relations",
        "financials",
        "revenue_mix",
        "filings",
        "sources",
    ]:
        result[key] = result.get(key, [])[
            : {
                "facts": 30,
                "products": 60,
                "segments": 30,
                "drivers": 30,
                "market_shares": 30,
                "relations": 100,
                "financials": 30,
                "revenue_mix": 80,
                "filings": 12,
                "sources": 200,
            }[key]
        ]
    result["fetched_at"] = dt.datetime.now(UTC).isoformat()
    result['collector_version'] = 3
    result["unavailable_sources"] = list(dict.fromkeys(result["unavailable_sources"]))
    return CompanyKnowledge.model_validate(result).model_dump(mode="json")
