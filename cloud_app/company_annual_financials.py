"""Reported annual figures from a checked issuer's existing inline filing.

Consolidated facts require undimensioned or exact reviewed total contexts. Signed income and cash-flow
values are preserved; an absent liability or cash-flow tag is never calculated.
This parser performs no network requests or model calls.
"""
import datetime as dt
import re

from .company_filings import document
from .company_revenue import number, source_cik
from .company_xbrl_resources import resource_nodes
from .company_xbrl_precision import decimals, reported_value
from .company_annual_coordinates import context_tags, metric_allowed, financial_label


# Tag order selects a reported metric, never a sum of different accounting bases.
METRICS = (
    ('매출', ('us-gaap:Revenues', 'us-gaap:SalesRevenueNet',
             'ifrs-full:Revenue',
             'ifrs-full:RevenueFromContractsWithCustomers',
             'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
             'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'), False),
    ('영업이익', ('us-gaap:OperatingIncomeLoss',
                 'ifrs-full:ProfitLossFromOperatingActivities'), False),
    ('순이익', ('us-gaap:NetIncomeLoss', 'ifrs-full:ProfitLossAttributableToOwnersOfParent',
               'us-gaap:ProfitLoss', 'ifrs-full:ProfitLoss'), False),
    ('총자산', ('us-gaap:Assets', 'ifrs-full:Assets'), True),
    ('총부채', ('us-gaap:Liabilities', 'ifrs-full:Liabilities'), True),
    ('자본', ('us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
             'ifrs-full:Equity', 'us-gaap:StockholdersEquity'), True),
    ('현금·현금성 자산', ('us-gaap:CashAndCashEquivalentsAtCarryingValue',
                         'ifrs-full:CashAndCashEquivalents'), True),
    ('영업활동 현금흐름', ('us-gaap:NetCashProvidedByUsedInOperatingActivities',
                          'ifrs-full:CashFlowsFromUsedInOperatingActivities',
                          'ifrs-full:CashFlowsFromUsedInOperations'), False),
    ('유형자산 취득 현금', ('us-gaap:PaymentsToAcquirePropertyPlantAndEquipment',
                           'ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities',
                           'su:CashFlowsUsedForCapitalExpenditures'), False),
)
LABELS = {
    'su:CashFlowsUsedForCapitalExpenditures': '자본지출 현금 · 공시 기준',
    'ifrs-full:RevenueFromContractsWithCustomers': '고객 계약 매출 · IFRS',
    'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax': '고객 계약 매출 · 부과세 제외',
    'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax': '고객 계약 매출 · 부과세 포함',
    'us-gaap:NetIncomeLoss': '지배기업 귀속 순이익',
    'ifrs-full:ProfitLossAttributableToOwnersOfParent': '지배기업 귀속 순이익',
    'us-gaap:ProfitLoss': '순이익 · 비지배지분 포함',
    'ifrs-full:ProfitLoss': '순이익 · 비지배지분 포함',
    'us-gaap:StockholdersEquity': '주주자본 · 비지배지분 제외',
    'us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest': '자본 합계 · 비지배지분 포함',
    'ifrs-full:Equity': '자본 합계 · 비지배지분 포함',
}


def _period_date(fact):
    text = re.sub(r'\s+', ' ', fact.get_text(' ', strip=True))
    transform = fact.get('format', '').lower()
    if not transform:
        return dt.date.fromisoformat(text)
    if transform in {'ixt:date-monthname-day-year-en', 'ixt:datemonthdayyearen',
                     'ixt:date-day-monthname-year-en', 'ixt:datedaymonthyearen'}:
        match = re.fullmatch(r'([A-Za-z]+)\s+(\d{1,2})\s*,?\s+(\d{4})', text)
        if transform in {'ixt:date-day-monthname-year-en', 'ixt:datedaymonthyearen'}:
            match = re.fullmatch(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', text)
        months = ('january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december')
        names = {name: index + 1 for index, name in enumerate(months)}
        names.update({name[:3]: index + 1 for index, name in enumerate(months)})
        if match:
            day_first = transform in {'ixt:date-day-monthname-year-en', 'ixt:datedaymonthyearen'}
            month, day = (match[2], match[1]) if day_first else (match[1], match[2])
            if month.lower() in names:
                return dt.date(int(match[3]), names[month.lower()], int(day))
    raise ValueError('Unsupported annual period date')


ANNUAL_FORMS = frozenset({'10-K', '10-K/A', '20-F', '20-F/A', '40-F', '40-F/A'})


def _annual_period(soup, origin, today):
    """Read the declared annual header, never infer a year from a URL."""
    try:
        nonnumeric = soup.find_all('ix:nonnumeric', limit=10000)
        forms = {f.get_text(strip=True) for f in nonnumeric if f.get('name') == 'dei:DocumentType'}
        if len(forms) != 1 or not forms <= ANNUAL_FORMS:
            return None
        ends = {_period_date(f) for f in nonnumeric if f.get('name') == 'dei:DocumentPeriodEndDate'}
        if len(ends) != 1:
            return None
        period_end = next(iter(ends))
        filed = dt.date.fromisoformat(origin['as_of']) if origin.get('as_of') else None
        if period_end > today or (filed and (filed > today or period_end > filed)):
            return None
        return period_end
    except (TypeError, ValueError):
        return None


def parse_annual_financials(raw, origin, expected_cik, today=None):
    """Require the source, XBRL context and caller's verified issuer to agree."""
    if isinstance(expected_cik, bool) or not re.fullmatch(r'\d{1,10}', str(expected_cik)):
        return []
    if source_cik(origin) != int(expected_cik):
        return []
    today = today or dt.datetime.now(dt.timezone.utc).date()
    soup = document(raw)
    period_end = _annual_period(soup, origin, today)
    if period_end is None:
        return []
    return _consolidated_facts(soup, origin, expected_cik, period_end)


def _consolidated_facts(soup, origin, expected_cik, period_end, shared=None):
    """Read signed, unambiguous facts in the exact consolidated annual contexts."""
    contexts, currencies = {}, {}
    wanted = {tag for _, tags, _ in METRICS for tag in tags}
    for unit in resource_nodes(soup, shared, 'xbrli:unit', 200):
        measures = unit.find_all('xbrli:measure')
        if len(measures) == 1 and not unit.find('xbrli:divide'):
            measure = measures[0].get_text(strip=True)
            if re.fullmatch(r'iso4217:[A-Z]{3}', measure):
                currencies[unit.get('id')] = measure.split(':')[1]
    for ctx in resource_nodes(soup, shared, 'xbrli:context', 10000):
        identifier = ctx.find('xbrli:identifier')
        if (not identifier or identifier.get('scheme') != 'http://www.sec.gov/CIK'
                or not re.fullmatch(r'\d{1,10}', identifier.get_text(strip=True))
                or int(identifier.get_text(strip=True)) != int(expected_cik)):
            continue
        accepted = context_tags(ctx, origin, expected_cik, period_end, wanted)
        if accepted is None:
            continue
        instant = ctx.find('xbrli:instant')
        start, end = ctx.find('xbrli:startdate'), ctx.find('xbrli:enddate')
        try:
            if instant and not start and not end and dt.date.fromisoformat(instant.text) == period_end:
                contexts[ctx.get('id')] = ((None, period_end.isoformat()), accepted)
            elif start and end and not instant:
                first, last = dt.date.fromisoformat(start.text), dt.date.fromisoformat(end.text)
                if last == period_end and 300 <= (last - first).days <= 400:
                    contexts[ctx.get('id')] = ((first.isoformat(), last.isoformat()), accepted)
        except ValueError:
            continue
    values, anchors = {}, {}
    for f in soup.find_all('ix:nonfraction', limit=100000):
        tag = f.get('name')
        ctx, currency = contexts.get(f.get('contextref')), currencies.get(f.get('unitref'))
        if (tag not in wanted or not ctx or not currency or tag not in ctx[1]
                or not metric_allowed(tag, origin, expected_cik, period_end)):
            continue
        value = number(f, signed=True)
        if value is None:
            continue
        key = (tag, currency, *ctx[0])
        precision = decimals(f)
        values.setdefault(key, set()).add((value, precision))
        anchor = f.get('id', '')
        if re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', anchor):
            anchors.setdefault((key, value, precision), anchor)
    result = []
    for label, tags, is_instant in METRICS:
        for tag in tags:
            candidates = [key for key in values
                          if key[0] == tag and (key[2] is None) == is_instant]
            # An ambiguous period, currency or repeated value needs review.
            if not candidates:
                continue
            if len(candidates) != 1:
                break
            key = candidates[0]
            value = reported_value(values[key])
            if value is None:
                break
            precision = max((p for v, p in values[key] if v == value and p is not None), default=None)
            anchor = anchors.get((key, value, precision))
            period = (key[2] + ' ~ ' if key[2] else '') + key[3]
            result.append(dict(label=financial_label(tag, LABELS.get(tag, label), origin, period), value=float(value),
                unit=key[1], period=period,
                source={**origin, 'label': 'SEC 연차 원문 XBRL · ' + tag,
                        'url': origin['url'] + ('#' + anchor if anchor else '')}))
            break
    return result
