"""Deterministic extraction of named business relationships from free filings.

No model, embeddings or inferred customer names. Only explicit issuer statements
or a competition section create an edge. Every edge retains its original excerpt.
"""
import re
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

# Vetted issuer/brand aliases. Unknown mentions never acquire a guessed ticker.
COMPANIES = (
    ("TSMC", "TSM", ("Taiwan Semiconductor Manufacturing", "TSMC")),
    ("Samsung Electronics", "005930.KS", ("Samsung Electronics",)),
    ("SK hynix", "000660.KS", ("SK Hynix", "SK hynix")),
    ("Micron Technology", "MU", ("Micron Technology", "Micron")),
    ("Intel", "INTC", ("Intel Corporation", "Intel")),
    ("Advanced Micro Devices", "AMD", ("Advanced Micro Devices",)),
    ("NVIDIA", "NVDA", ("NVIDIA",)),
    ("Broadcom", "AVGO", ("Broadcom",)),
    ("Qualcomm", "QCOM", ("Qualcomm", "QUALCOMM")),
    ("Texas Instruments", "TXN", ("Texas Instruments",)),
    ("GlobalFoundries", "GFS", ("GlobalFoundries",)),
    ("Ambarella", "AMBA", ("Ambarella",)),
    ("Renesas Electronics", None, ("Renesas Electronics",)),
    ("Tesla", "TSLA", ("Tesla Inc", "Tesla")),
    ("Arista Networks", "ANET", ("Arista Networks",)),
    ("Lumentum Holdings", "LITE", ("Lumentum Holdings",)),
    ("Marvell Technology", "MRVL", ("Marvell Technology",)),
    ("Apple", "AAPL", ("Apple Inc", "Apple")),
    ("Microsoft", "MSFT", ("Microsoft Corporation", "Microsoft")),
    ("Alphabet", "GOOGL", ("Alphabet Inc", "Alphabet", "Google")),
    ("Amazon", "AMZN", ("Amazon.com", "Amazon")),
    ("Meta Platforms", "META", ("Meta Platforms", "Facebook")),
    ("Alibaba Group", "BABA", ("Alibaba Group", "Alibaba")),
    ("Baidu", "BIDU", ("Baidu",)),
    ("Oracle", "ORCL", ("Oracle",)),
    ("Cisco Systems", "CSCO", ("Cisco Systems", "Cisco")),
    ("IBM", "IBM", ("International Business Machines", "IBM")),
    ("Dell Technologies", "DELL", ("Dell Technologies", "Dell")),
    ("Hewlett Packard Enterprise", "HPE", ("Hewlett Packard Enterprise",)),
    ("HP", "HPQ", ("HP Inc",)),
    ("Fabrinet", "FN", ("Fabrinet",)),
    ("Hon Hai Precision Industry", None, ("Hon Hai Precision Industry", "Foxconn")),
    ("Wistron Corporation", None, ("Wistron Corporation", "Wistron")),
    ("Huawei", None, ("Huawei",)),
    ("OpenAI", None, ("OpenAI",)),
    ("Anthropic", None, ("Anthropic",)),
    ("Arm", "ARM", ("Arm Holdings",)),
    ("Salesforce", "CRM", ("Salesforce",)),
    ("Adobe", "ADBE", ("Adobe",)),
    ("SAP", "SAP", ("SAP SE",)),
    ("Netflix", "NFLX", ("Netflix",)),
    ("Spotify", "SPOT", ("Spotify",)),
    ("Walmart", "WMT", ("Walmart",)),
    ("Target", "TGT", ("Target Corporation",)),
    ("Costco", "COST", ("Costco",)),
    ("Coca-Cola", "KO", ("Coca-Cola",)),
    ("PepsiCo", "PEP", ("PepsiCo",)),
    ("Procter & Gamble", "PG", ("Procter & Gamble",)),
    ("JPMorgan Chase", "JPM", ("JPMorgan Chase", "JPMorganChase")),
    ("Bank of America", "BAC", ("Bank of America",)),
    ("Citigroup", "C", ("Citigroup",)),
    ("Wells Fargo", "WFC", ("Wells Fargo",)),
    ("Goldman Sachs", "GS", ("Goldman Sachs",)),
    ("Morgan Stanley", "MS", ("Morgan Stanley",)),
    ("American Express", "AXP", ("American Express",)),
    ("Visa", "V", ("Visa Inc",)),
    ("Mastercard", "MA", ("Mastercard",)),
    ("PayPal", "PYPL", ("PayPal",)),
    ("UnitedHealth Group", "UNH", ("UnitedHealth Group",)),
    ("Eli Lilly", "LLY", ("Eli Lilly",)),
    ("Pfizer", "PFE", ("Pfizer",)),
    ("Merck", "MRK", ("Merck & Co",)),
    ("Johnson & Johnson", "JNJ", ("Johnson & Johnson",)),
    ("ExxonMobil", "XOM", ("Exxon Mobil", "ExxonMobil")),
    ("Chevron", "CVX", ("Chevron",)),
    ("Shell", "SHEL", ("Shell plc",)),
    ("Caterpillar", "CAT", ("Caterpillar",)),
    ("Deere", "DE", ("Deere & Company",)),
    ("Boeing", "BA", ("The Boeing Company", "Boeing")),
    ("Airbus", None, ("Airbus",)),
    ("Lockheed Martin", "LMT", ("Lockheed Martin",)),
    ("General Electric", "GE", ("General Electric", "GE Aerospace")),
    ("Linde", "LIN", ("Linde",)),
    ("Air Products", "APD", ("Air Products",)),
    ("UPS", "UPS", ("United Parcel Service",)),
    ("FedEx", "FDX", ("FedEx",)),
    ("ASML", "ASML", ("ASML",)),
    ("Applied Materials", "AMAT", ("Applied Materials",)),
    ("Lam Research", "LRCX", ("Lam Research",)),
    ("KLA", "KLAC", ("KLA Corporation", "KLA-Tencor")),
    ("Onto Innovation", "ONTO", ("Onto Innovation",)),
    ("Amkor", "AMKR", ("Amkor Technology",)),
    ("McDonald's", "MCD", ("McDonald's", "McDonald’s")),
    ("Accenture", "ACN", ("Accenture",)),
    ("Thermo Fisher Scientific", "TMO", ("Thermo Fisher Scientific",)),
    ("Novo Nordisk", "NVO", ("Novo Nordisk",)),
    ("Sanofi", "SNY", ("Sanofi",)),
    ("Prologis", "PLD", ("Prologis",)),
    ("NextEra Energy", "NEE", ("NextEra Energy",)),
    ("GE Vernova", "GEV", ("GE Vernova",)),
    ("Home Depot", "HD", ("The Home Depot", "Home Depot Inc")),
    ("BHP", "BHP", ("BHP Group",)),
    ("Rio Tinto", "RIO", ("Rio Tinto",)),
)
MATCHERS = tuple((name, symbol, re.compile(r"(?<![\w])(?:" + "|".join(
    re.escape(alias) for alias in sorted(set(aliases), key=len, reverse=True)
) + r")(?![\w])", re.I)) for name, symbol, aliases in COMPANIES)


def document(raw):
    return raw if isinstance(raw, BeautifulSoup) else BeautifulSoup(raw, "html.parser")


def blocks(raw):
    """Keep document order, headings and original anchors, without executing HTML."""
    soup = document(raw)
    result = []
    for node in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4"]):
        if node.find_parent(["script", "style", "ix:header", "ix:hidden", "noscript"]):
            continue
        if node.find(["p", "div", "li", "h1", "h2", "h3", "h4"]):
            continue
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
        if text:
            anchor = node.get("id", "")
            result.append((text[:10000], anchor if re.fullmatch(r"[\w.-]{1,120}", anchor) else ""))
        if len(result) >= 25000:
            break
    return result


def named(text, issuer_symbol, name_index=None):
    legal = name_index.mentions(text) if name_index else []
    result = []
    for name, symbol, matcher in MATCHERS:
        if symbol == issuer_symbol or {symbol, issuer_symbol} <= {'GOOG','GOOGL'}:
            continue
        if any(not any(start < mention.end() and mention.start() < end and exact_symbol != symbol
                       for start,end,_,exact_symbol in legal) for mention in matcher.finditer(text)):
            result.append((name,symbol))
    if name_index:
        existing = {symbol for _, symbol in result}
        result += [(name, symbol) for name, symbol in name_index.named(text, issuer_symbol) if symbol not in existing]
    return result


def relationship_kind(text, competition=False):
    """High precision issuer statements; hypothetical and negated claims stay out."""
    if re.search(r"\b(?:could|might|may|would|potential|hypothetical|not|no longer|terminated|previously|formerly)\b", text, re.I):
        return None
    if re.search(r"(?:we|the company) (?:utilize|use|purchase|buy|source|engage with).{0,150}(?:foundries|manufacturers|subcontractors|from)", text, re.I):
        role = "메모리 공급" if re.search(r"\bmemory\b", text, re.I) else "제조·부품 공급"
        return "supplier", "공시 " + role
    if re.search(r"our (?:principal |major |key )?(?:suppliers|manufacturing partners) (?:include|are)", text, re.I):
        return "supplier", "공시 공급·제조 관계"
    if re.search(r"(?:our (?:largest |major |key )?customers (?:include|are)|we (?:sell|supply|provide).{0,100} to )", text, re.I):
        return "customer", "공시 판매·고객 관계"
    if re.search(r"(?:we (?:have )?(?:partner(?:ed)?|collaborat(?:e|ed)) with|our partnership with|our partners (?:include|are))", text, re.I):
        return "partner", "공시 협력 관계"
    if re.search(r"(?:our (?:wholly[- ]owned )?subsidiar(?:y|ies)|wholly[- ]owned subsidiar(?:y|ies) of (?:us|the company))", text, re.I):
        return "subsidiary", "공시에 명시된 자회사"
    if re.search(r"(?:our (?:principal |major )?competitors (?:include|are)|we compete (?:with|against))", text, re.I) or (
        competition and re.search(r"\b(?:competitors?|competition|compete|including|such as)\b", text, re.I)
    ):
        return "competitor", "공시 경쟁 항목에 명시된 기업"
    return None


CLAIM_PATTERNS = (
    ('supplier', re.compile(r'(?:our (?:principal |major |key )?(?:suppliers|manufacturing partners) (?:include|are)|(?:we|the company) (?:utilize|use|purchase|buy|source|engage with).{0,150}?(?:foundries|manufacturers|subcontractors|from))', re.I)),
    ('customer', re.compile(r'(?:our (?:largest |major |key )?customers (?:include|are)|we (?:sell|supply|provide).{0,100}? to )', re.I)),
    ('partner', re.compile(r'(?:we (?:have )?(?:partner(?:ed)?|collaborat(?:e|ed)) with|our partnership with|our partners (?:include|are))', re.I)),
    ('competitor', re.compile(r'(?:our (?:principal |major )?competitors (?:include|are)|we compete (?:with|against))', re.I)),
)


def statements(sentence, competition):
    if re.search(r'\b(?:could|might|may|would|potential|hypothetical|not|no longer|terminated|previously|formerly)\b', sentence, re.I):
        return []
    triggers = sorted((match.start(), match.end(), kind) for kind, pattern in CLAIM_PATTERNS for match in pattern.finditer(sentence))
    result = []
    for index, (start, end, kind) in enumerate(triggers):
        tail = sentence[end:triggers[index+1][0] if index+1 < len(triggers) else len(sentence)]
        tail = re.split(r'\b(?:using|through|because|whereas|with|which|that|to|for)\b', tail, maxsplit=1, flags=re.I)[0]
        relation = relationship_kind(sentence[start:end] + tail)
        if relation:
            result.append((kind, relation[1], tail))
    if not triggers:
        relation = relationship_kind(sentence, competition)
        if relation:
            result.append((*relation, sentence))
    return result


def parse_report(raw, symbol, origin, name_index=None):
    rows = blocks(raw)
    if not rows:
        raise ValueError("Empty filing body")
    result = {key: [] for key in ("facts", "products", "segments", "drivers", "relations")}
    section = ""
    remaining = 0
    seen = set()
    for text, anchor in rows:
        if re.fullmatch(r"\d{1,4}|Table of Contents", text, re.I):
            continue
        short = len(text) < 100
        if short and re.fullmatch(r"(?:competition|competitors|competitive environment|our (?:current |principal |major )?competitors include)", text.strip(" .:"), re.I):
            section, remaining = "competition", 12
            continue
        if short and re.fullmatch(r"(?:manufacturing|supply chain|business|general|our business|overview|products(?: and services)?|risk factors|item\s+1a\.?.*)", text.strip(" .:"), re.I):
            section, remaining = "", 0
        if len(text) < 80:
            if short and not text.startswith(("•", "–", "-")):
                section, remaining = "", 0
            continue
        src = {**origin, "url": origin["url"] + ("#" + anchor if anchor else "")}
        # Sentence boundary preserves corporate abbreviations and names in lists.
        sentences = re.split(r"(?<!Inc)(?<!Ltd)(?<!Co)\.\s+(?=[A-Z•])", text)
        for sentence in sentences:
            for kind, role, candidates in statements(sentence, section == "competition" and remaining > 0):
                for name, target_symbol in named(candidates, symbol, name_index):
                    # Keep different business roles/statements for the same company.
                    # The UI groups their evidence into one node without discarding it.
                    key = (name, kind, sentence)
                    if key in seen or len(result["relations"]) >= 80:
                        continue
                    seen.add(key)
                    result["relations"].append(dict(name=name, symbol=target_symbol, kind=kind,
                        detail=role, original=sentence[:1500], source=src))
        remaining = max(0, remaining - 1)
        if remaining == 0:
            section = ""
        # Excerpts describe the issuer's business, not an inferred investment view.
        categories = (
            ("products", "공시 제품·서비스 원문", r"(?:we (?:offer|provide|design|develop|manufacture)|our (?:products|services) (?:include|are))"),
            ("segments", "공시 사업 구성 원문", r"(?:reportable segments|operating segments|organized.{0,50}segments|business segments)"),
            ("drivers", "공시 사업 위험·투입 요소 원문", r"(?:we depend|our (?:business|operations|results).{0,80}(?:depend|affected)|supply chain|raw materials|customer concentration)"),
        )
        for key, title, pattern in categories:
            boilerplate = re.search(r"(?:forward[- ]looking|you should carefully consider|compensation packages|employee benefits|we offer competitive.{0,60}compensation)", text, re.I)
            if not boilerplate and len(result[key]) < 4 and re.search(pattern, text, re.I) and text not in seen:
                result[key].append(dict(title=title, detail="", original=text[:1500], source=src))
                seen.add(text)
    count = len(result["relations"])
    if name_index:
        result['sources'] = [dict(label='SEC · 공식 기업명·종목·CIK 목록', url='https://www.sec.gov/files/company_tickers.json', level='primary')]
    result["report_analysis"] = dict(title="공시 본문 확인", detail=
        f"공시 문단 {len(rows):,}개를 규칙으로 확인해 기업 관계 {count:,}건을 추출했습니다(본문 최대 80건). "
        "영문 원문과 기준일을 보존합니다. 명시되지 않은 관계·익명 고객은 추정하지 않습니다. "
        "관계가 0건인 분류는 관계가 없다는 뜻이 아닙니다. 이 규칙이 찾지 못한 관계도 있을 수 있습니다.", source=origin)
    return result


def parse_subsidiaries(raw, origin):
    """Exhibit 21 table names remain source-local identities, never name-based merges."""
    soup = document(raw)
    if not re.search(r"subsidiar", soup.get_text(" ", strip=True)[:4000], re.I):
        raise ValueError("Not a subsidiary exhibit")
    result, seen = [], set()
    for tr in soup.find_all("tr")[:2000]:
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
        values = [re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip() for cell in cells]
        values = [value for value in values if value]
        if len(values) < 2:
            continue
        name = values[0]
        if not 3 <= len(name) <= 160 or re.search(r"(?:subsidiar|jurisdiction|\bname\b|exhibit|^state$|^December \d)", name, re.I):
            continue
        if name in seen or not re.search(r"[A-Za-z]", name):
            continue
        jurisdiction = " ".join(values[1:])
        if not jurisdiction or len(jurisdiction) > 200:
            continue
        seen.add(name)
        result.append(dict(name=name, kind="subsidiary", symbol=None,
            detail="공시 자회사 명세서 · 설립·등록 관할: " + jurisdiction + " · 표에 기재된 관계이며 지분율·현재 거래 규모는 추정하지 않습니다.", source=origin))
        if len(result) >= 80:
            break
    return result


def subsidiary_document(raw, annual_url):
    """Follow only the issuer's explicitly named SEC subsidiary exhibit."""
    issuer = urlsplit(annual_url).path.split("/")[4]
    soup = document(raw)
    for anchor in soup.find_all("a", href=True)[:10000]:
        if not re.fullmatch(r"(?:subsidiaries of (?:the )?(?:registrant|company)|list of subsidiaries)", anchor.get_text(" ", strip=True), re.I):
            continue
        url = urljoin(annual_url, anchor["href"])
        parsed = urlsplit(url)
        if (parsed.scheme == "https" and parsed.netloc == "www.sec.gov" and not parsed.query and not parsed.fragment
            and re.fullmatch(r"/Archives/edgar/data/" + re.escape(issuer) + r"/\d{18}/[A-Za-z0-9_.-]{1,160}\.html?", parsed.path)):
            return url
    return None
