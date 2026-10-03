"""Annual financial exhibits require the original cover and its observed link.

The exhibit keeps its own citation and XBRL issuer/period/currency. A missing DEI
header is never synthesized, and a same-issuer URL alone is not annual evidence.
"""
import datetime as dt
import re
from urllib.parse import urljoin, urlsplit

from .company_annual_financials import (
    ANNUAL_FORMS, _annual_period, _consolidated_facts, _period_date,
)
from .company_filings import document
from .company_revenue import parse_revenue, source_cik


def same_annual_accession(exhibit, parent, expected_cik):
    """Require two distinct canonical SEC documents in one exact accession."""
    try:
        if (isinstance(expected_cik, bool)
                or not re.fullmatch(r'\d{1,10}', str(expected_cik))
                or source_cik(exhibit) != int(expected_cik)
                or source_cik(parent) != int(expected_cik)
                or exhibit.get('level') != 'primary' or parent.get('level') != 'primary'
                or exhibit.get('as_of') != parent.get('as_of')):
            return False
        dt.date.fromisoformat(parent['as_of'])
        child_url, parent_url = urlsplit(exhibit['url']), urlsplit(parent['url'])
        return (not child_url.query and not child_url.fragment
                and not parent_url.query and not parent_url.fragment
                and child_url.netloc == parent_url.netloc
                and child_url.path != parent_url.path
                and child_url.path.rsplit('/', 1)[0] == parent_url.path.rsplit('/', 1)[0])
    except (KeyError, TypeError, ValueError):
        return False


def _document_set(raw, origin, expected_cik, parent_raw, parent_origin, today):
    """Resolve the actual link and parent period before sharing any resources."""
    if not same_annual_accession(origin, parent_origin, expected_cik):
        return None
    parent = document(parent_raw)
    period_end = _annual_period(parent, parent_origin, today)
    if period_end is None:
        return None
    links = {urljoin(parent_origin['url'], node.get('href', '')).split('#')[0]
             for node in parent.find_all('a', href=True, limit=10000)}
    if origin['url'] not in links:
        return None
    soup = document(raw)
    try:
        headers = soup.find_all('ix:nonnumeric', limit=10000)
        forms = {f.get_text(strip=True) for f in headers if f.get('name') == 'dei:DocumentType'}
        ends = {_period_date(f) for f in headers if f.get('name') == 'dei:DocumentPeriodEndDate'}
        # A quarterly header or conflicting exhibit date cannot borrow an annual
        # cover. Most 40-F financial exhibits legitimately have no DEI header.
        if (len(forms) > 1 or (forms and not forms <= ANNUAL_FORMS)
                or (ends and ends != {period_end})):
            return None
    except (TypeError, ValueError):
        return None
    return soup, parent, period_end


def parse_attached_financials(raw, origin, expected_cik, parent_raw, parent_origin, today=None):
    """Facts cite the exhibit; identity/period/unit can live in its actual cover."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    resolved = _document_set(raw, origin, expected_cik, parent_raw, parent_origin, today)
    if resolved is None:
        return []
    soup, parent, period_end = resolved
    return _consolidated_facts(soup, origin, expected_cik, period_end, shared=parent)


def parse_attached_revenue(raw, origin, symbol, expected_cik, parent_raw, parent_origin, today=None):
    """Use the same verified document set and declared annual year for revenue."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    resolved = _document_set(raw, origin, expected_cik, parent_raw, parent_origin, today)
    if resolved is None:
        return []
    soup, parent, period_end = resolved
    return parse_revenue(raw, origin, symbol, today, shared=parent,
                         period_end=period_end, parsed=soup)
