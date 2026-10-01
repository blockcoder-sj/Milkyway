"""Keep prior evidence from a failed source, without resurrecting refreshed claims."""
from urllib.parse import urlsplit

LIST_LIMITS = {
    "facts": 30, "brief": 8, "products": 60, "segments": 30, "market_shares": 30,
    "drivers": 30, "relations": 100, "financials": 30, "filings": 12, "sources": 200,
}


def belongs_to_failed_source(item, field, failures):
    origin = item if field in {"filings", "sources"} else item.source
    host = urlsplit(origin.url).hostname
    if "wise" in failures and host == "comp.wisereport.co.kr":
        return True
    if host not in {"www.sec.gov", "data.sec.gov"}:
        return False
    if "sec" in failures:
        return True
    if "sec_financials" in failures and field == "financials":
        return True
    exhibit = origin.label.startswith("SEC · Exhibit 21")
    if "sec_subsidiaries" in failures and exhibit:
        return True
    return "sec_report" in failures and not exhibit and field in {
        "products", "segments", "drivers", "relations"
    }


def preserve_previous(parsed, old):
    """Prefer current rows, append only failed-source rows within existing limits."""
    if not old or not parsed.errors:
        return
    failures = set(parsed.unavailable_sources)
    retained = False
    for field, limit in LIST_LIMITS.items():
        current, previous = getattr(parsed, field), getattr(old, field)
        known = {row.model_dump_json() for row in current}
        legacy_missing = not failures and not current
        for row in previous:
            key = row.model_dump_json()
            if (len(current) < limit and key not in known
                    and (legacy_missing or belongs_to_failed_source(row, field, failures))):
                current.append(row)
                known.add(key)
                retained = True
    if (not parsed.report_analysis and old.report_analysis
            and (not failures or failures.intersection({"sec", "sec_report"}))):
        parsed.report_analysis = old.report_analysis
        retained = True
    if (not parsed.description and old.description and old.description_source
            and (not failures or belongs_to_failed_source(old.description_source, "sources", failures))):
        parsed.description, parsed.description_source = old.description, old.description_source
        retained = True
    if retained:
        date = old.fetched_at.isoformat() if old.fetched_at else "기준 시각 미제공"
        parsed.errors.append(
            f"미수신 항목은 이전 수집({date}) 자료를 유지합니다. 항목별 원자료 기준일을 확인하세요."
        )
