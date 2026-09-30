"""Bounded public company research. No credentials, AI, orders or dynamic hosts."""
import datetime as dt
import math
import re
from urllib.parse import quote, urlsplit
from bs4 import BeautifulSoup
from .bounded_io import read_requests_json, read_requests_bytes
from .market_broker_feed import FixedSession
from .company_schemas import CompanyKnowledge
from .company_catalog import editorial_for

UTC = dt.timezone.utc
AGENT = "MilkywayPersonal/1.0"
WIKI = "https://www.wikidata.org/w/api.php"


def get(url, params=None, maximum=4 * 1024 * 1024, html=False):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname
        not in {
            "www.wikidata.org",
            "en.wikipedia.org",
            "ko.wikipedia.org",
            "data.sec.gov",
            "comp.wisereport.co.kr",
        }
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("Unapproved company data host")
    with FixedSession() as session:
        response = session.get(
            url,
            params=params,
            headers={
                "User-Agent": AGENT,
                "Accept": "text/html" if html else "application/json",
            },
            timeout=(3, 10),
            stream=True,
        )
        try:
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


def claim_value(claim):
    return claim.get("mainsnak", {}).get("datavalue", {}).get("value")


def claims(entity, prop, now):
    result = []
    for claim in entity.get("claims", {}).get(prop, [])[:200]:
        if claim.get("rank") == "deprecated":
            continue
        ends = claim.get("qualifiers", {}).get("P582", [])
        if any(
            str(e.get("datavalue", {}).get("value", {}).get("time", ""))[1:11]
            <= now.date().isoformat()
            for e in ends
        ):
            continue
        result.append(claim)
    return result


def identity_matches(entity, symbol):
    now = dt.datetime.now(UTC)
    tickers = [claim_value(row) for row in claims(entity, "P249", now)]
    tickers += [
        snak.get("datavalue", {}).get("value")
        for row in claims(entity, "P414", now)
        for snak in row.get("qualifiers", {}).get("P249", [])
    ]
    return symbol.removesuffix(".KS") in tickers


def find_entity(name, symbol, known_id=None):
    if known_id:
        candidates = [known_id]
    else:
        search_name = re.sub(
            r"\s+(?:Inc(?:orporated)?|Corporation|Corp|Company|Ltd|Limited|plc)[.,]?$",
            "",
            name,
            flags=re.IGNORECASE,
        ).strip()
        found = get(
            WIKI,
            {
                "action": "wbsearchentities",
                "search": search_name,
                "language": "en" if not symbol.endswith(".KS") else "ko",
                "limit": 3,
                "format": "json",
            },
            maximum=64 * 1024,
        )
        candidates = [
            row["id"]
            for row in found.get("search", [])
            if re.fullmatch(r"Q\d{1,12}", row.get("id", ""))
        ]
    if not candidates:
        return None
    response = get(
        WIKI,
        {
            "action": "wbgetentities",
            "ids": "|".join(candidates),
            "props": "claims|labels|descriptions|sitelinks",
            "sitefilter": "enwiki|kowiki",
            "languages": "ko|en",
            "format": "json",
        },
    )
    for identifier in candidates:
        entity = response.get("entities", {}).get(identifier, {})
        if identity_matches(entity, symbol):
            return identifier, entity
    return None


def reference(claim, identifier, now):
    # Keep the Wikidata statement as the attribution; references are linked separately.
    dates = claim.get("qualifiers", {}).get("P585", [])
    as_of = next(
        (
            str(row.get("datavalue", {}).get("value", {}).get("time", ""))[1:11]
            for row in dates
        ),
        None,
    )
    return source(
        "Wikidata · 관계 진술",
        f"https://www.wikidata.org/wiki/{identifier}",
        as_of,
        level="encyclopedia",
    )


def wikidata(name, symbol, known_id=None):
    found = find_entity(name, symbol, known_id)
    if not found:
        raise ValueError("No exact ticker-matched entity")
    identifier, entity = found
    now = dt.datetime.now(UTC)
    properties = {"P355": "subsidiary", "P749": "parent", "P127": "owner"}
    relation_claims = [
        (kind, row)
        for prop, kind in properties.items()
        for row in claims(entity, prop, now)
    ][:80]
    product_claims = claims(entity, "P1056", now)[:50]
    industry_claims = claims(entity, "P452", now)[:10]
    needed = {
        value["id"]
        for _, row in relation_claims
        for value in [claim_value(row)]
        if isinstance(value, dict) and re.fullmatch(r"Q\d{1,12}", value.get("id", ""))
    }
    needed |= {
        value["id"]
        for row in product_claims + industry_claims
        for value in [claim_value(row)]
        if isinstance(value, dict) and re.fullmatch(r"Q\d{1,12}", value.get("id", ""))
    }
    labels = {}
    ids = sorted(needed)
    for offset in range(0, len(ids), 50):
        response = get(
            WIKI,
            {
                "action": "wbgetentities",
                "ids": "|".join(ids[offset : offset + 50]),
                "props": "labels",
                "languages": "ko|en",
                "format": "json",
            },
            maximum=512 * 1024,
        )
        for key, item in response.get("entities", {}).items():
            label = item.get("labels", {})
            labels[key] = (label.get("ko") or label.get("en") or {}).get("value", key)
    info_source = source(
        "Wikidata · 공개 기업 정보",
        f"https://www.wikidata.org/wiki/{identifier}",
        level="encyclopedia",
    )

    def facts(rows):
        return [
            dict(
                title=labels[value["id"]][:160], source=reference(row, identifier, now)
            )
            for row in rows
            for value in [claim_value(row)]
            if isinstance(value, dict) and value.get("id") in labels
        ]

    relations = [
        dict(
            name=labels[value["id"]][:160],
            kind=kind,
            entity_id=value["id"],
            source=reference(row, identifier, now),
            detail="공개 백과에 등록된 관계입니다. 진술의 기준일과 원자료를 확인하세요.",
        )
        for kind, row in relation_claims
        for value in [claim_value(row)]
        if isinstance(value, dict) and value.get("id") in labels
    ]
    # Links to statement references are preserved without fetching arbitrary hosts.
    references = []
    for _, claim in relation_claims:
        for ref in claim.get("references", [])[:8]:
            for snak in ref.get("snaks", {}).get("P854", [])[:3]:
                value = snak.get("datavalue", {}).get("value")
                if (
                    isinstance(value, str)
                    and value.startswith("https://")
                    and len(value) <= 2000
                ):
                    try:
                        from .company_schemas import Source

                        references.append(
                            Source.model_validate(
                                source("관계 진술의 참고 원문", value, level="encyclopedia")
                            ).model_dump()
                        )
                    except ValueError:
                        pass
    description = (
        entity.get("descriptions", {}).get("ko")
        or entity.get("descriptions", {}).get("en")
        or {}
    ).get("value", "")
    cik = next(
        (
            str(claim_value(row))
            for row in entity.get("claims", {}).get("P5531", [])
            if re.fullmatch(r"\d{1,10}", str(claim_value(row)))
        ),
        None,
    )
    result = dict(
        description=description[:1500],
        description_source=info_source,
        products=facts(product_claims),
        facts=facts(industry_claims),
        relations=relations,
        sources=[info_source] + references[:100],
    )
    wiki_link = entity.get("sitelinks", {}).get("kowiki") or entity.get(
        "sitelinks", {}
    ).get("enwiki")
    if wiki_link:
        language = "ko" if "kowiki" in entity.get("sitelinks", {}) else "en"
        try:
            result["facts"] += wikipedia_business(language, wiki_link["title"])
        except Exception:
            pass
    return result, cik


def wikipedia_business(language, title):
    """Licensed encyclopedia context, attributed separately from official disclosures."""
    if language not in {"ko", "en"}:
        raise ValueError("Unsupported encyclopedia")
    url = f"https://{language}.wikipedia.org/w/api.php"
    payload = get(
        url,
        {
            "action": "query",
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
            "exchars": "1400",
            "titles": title,
            "redirects": "1",
            "format": "json",
        },
        maximum=256 * 1024,
    )
    pages = payload.get("query", {}).get("pages", {})
    if len(pages) != 1:
        return []
    page = next(iter(pages.values()))
    text = page.get("extract", "")
    if not isinstance(text, str) or not text.strip():
        return []
    origin = source(
        "Wikipedia · 기업 개요 (CC BY-SA)",
        f"https://{language}.wikipedia.org/wiki/"
        + quote(page.get("title", title).replace(" ", "_"), safe=""),
        level="encyclopedia",
    )
    return [dict(title="공개 백과 사업 개요", detail=text[:1400], source=origin)]


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
    for index, form in enumerate(forms[:2000]):
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
                detail=submissions.get("sicDescription", "")[:1500],
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
        maximum=2 * 1024 * 1024,
    )
    error = None
    try:
        facts = get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json",
            maximum=8 * 1024 * 1024,
        )
    except Exception:
        facts = {}
        error = "SEC 재무 수치를 수신하지 못했습니다. 수신한 공시 링크는 유지합니다"
    result = parse_sec(submissions, facts, symbol, now)
    if error:
        result["errors"] = [error]
    return result


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
    symbol = payload["symbol"]
    name = payload["name"]
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,19}", symbol):
        raise ValueError("Invalid symbol")
    editorial = editorial_for(symbol)
    result = {"symbol": symbol, "name": name[:120], "errors": [], "sources": []}
    cik = editorial.pop("cik", None)
    qid = editorial.pop("entity_id", None)
    try:
        wiki, wiki_cik = wikidata(name, symbol, qid)
        result.update(wiki)
        cik = cik or wiki_cik
    except Exception:
        result["errors"].append("공개 백과 정보를 수신하거나 종목과 일치시킬 수 없습니다")
    try:
        extra = (
            wise_company(symbol)
            if symbol.endswith(".KS")
            else sec_company(symbol, cik)
            if cik
            else {}
        )
        for key, value in extra.items():
            result[key] = result.get(key, []) + value
        if not symbol.endswith(".KS") and not cik:
            result["errors"].append("SEC 기업 식별자가 확인되지 않아 공시 재무 수치를 표시하지 않습니다")
    except Exception:
        result["errors"].append("기업 공시·개요 자료 수신에 실패했습니다")
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
                "filings": 12,
                "sources": 200,
            }[key]
        ]
    result["fetched_at"] = dt.datetime.now(UTC).isoformat()
    return CompanyKnowledge.model_validate(result).model_dump(mode="json")
