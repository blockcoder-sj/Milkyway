"""Reported annual figures from a checked issuer's existing inline filing.

Only undimensioned consolidated facts are admitted. Signed income and cash-flow
values are preserved; an absent liability or cash-flow tag is never calculated.
This parser performs no network requests or model calls.
"""
import datetime as dt
import re

from .company_filings import document
from .company_revenue import number, source_cik


# Tag order selects a reported metric, never a sum of different accounting bases.
METRICS = (
    ('매출', ('us-gaap:Revenues', 'us-gaap:SalesRevenueNet',
             'ifrs-full:Revenue',
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
                          'ifrs-full:CashFlowsFromUsedInOperatingActivities'), False),
    ('유형자산 취득 현금', ('us-gaap:PaymentsToAcquirePropertyPlantAndEquipment',
                           'ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities'), False),
)
LABELS = {
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
    if transform in {'ixt:date-monthname-day-year-en', 'ixt:datemonthdayyearen'}:
        match = re.fullmatch(r'([A-Za-z]+)\s+(\d{1,2})\s*,?\s+(\d{4})', text)
        months = ('january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december')
        names = {name: index + 1 for index, name in enumerate(months)}
        names.update({name[:3]: index + 1 for index, name in enumerate(months)})
        if match and match[1].lower() in names:
            return dt.date(int(match[3]), names[match[1].lower()], int(match[2]))
    raise ValueError('Unsupported annual period date')


def parse_annual_financials(raw, origin, expected_cik, today=None):
    """Require the source, XBRL context and caller's verified issuer to agree."""
    if isinstance(expected_cik, bool) or not re.fullmatch(r'\d{1,10}', str(expected_cik)):
        return []
    if source_cik(origin) != int(expected_cik):
        return []
    today = today or dt.datetime.now(dt.timezone.utc).date()
    soup = document(raw)
    try:
        nonnumeric = soup.find_all('ix:nonnumeric', limit=10000)
        forms = {f.get_text(strip=True) for f in nonnumeric if f.get('name') == 'dei:DocumentType'}
        if len(forms) != 1 or not forms <= {'10-K', '10-K/A', '20-F', '20-F/A', '40-F', '40-F/A'}:
            return []
        ends = {_period_date(f) for f in nonnumeric if f.get('name') == 'dei:DocumentPeriodEndDate'}
        if len(ends) != 1:
            return []
        period_end = next(iter(ends))
        if period_end > today or (origin.get('as_of') and
                                 dt.date.fromisoformat(origin['as_of']) > today):
            return []
    except (TypeError, ValueError):
        return []
    contexts, currencies = {}, {}
    for unit in soup.find_all('xbrli:unit', limit=200):
        measures = unit.find_all('xbrli:measure')
        if len(measures) == 1 and not unit.find('xbrli:divide'):
            measure = measures[0].get_text(strip=True)
            if re.fullmatch(r'iso4217:[A-Z]{3}', measure):
                currencies[unit.get('id')] = measure.split(':')[1]
    for ctx in soup.find_all('xbrli:context', limit=10000):
        identifier = ctx.find('xbrli:identifier')
        if (not identifier or identifier.get('scheme') != 'http://www.sec.gov/CIK'
                or not re.fullmatch(r'\d{1,10}', identifier.get_text(strip=True))
                or int(identifier.get_text(strip=True)) != int(expected_cik)
                or ctx.find('xbrldi:explicitmember') or ctx.find('xbrldi:typedmember')):
            continue
        instant = ctx.find('xbrli:instant')
        start, end = ctx.find('xbrli:startdate'), ctx.find('xbrli:enddate')
        try:
            if instant and not start and not end and dt.date.fromisoformat(instant.text) == period_end:
                contexts[ctx.get('id')] = (None, period_end.isoformat())
            elif start and end and not instant:
                first, last = dt.date.fromisoformat(start.text), dt.date.fromisoformat(end.text)
                if last == period_end and 300 <= (last - first).days <= 400:
                    contexts[ctx.get('id')] = (first.isoformat(), last.isoformat())
        except ValueError:
            continue
    wanted = {tag for _, tags, _ in METRICS for tag in tags}
    values, anchors = {}, {}
    for f in soup.find_all('ix:nonfraction', limit=100000):
        tag = f.get('name')
        ctx, currency = contexts.get(f.get('contextref')), currencies.get(f.get('unitref'))
        if tag not in wanted or not ctx or not currency:
            continue
        value = number(f, signed=True)
        if value is None:
            continue
        key = (tag, currency, *ctx)
        values.setdefault(key, set()).add(value)
        anchor = f.get('id', '')
        if re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', anchor):
            anchors.setdefault(key, anchor)
    result = []
    for label, tags, is_instant in METRICS:
        for tag in tags:
            candidates = [key for key in values
                          if key[0] == tag and (key[2] is None) == is_instant]
            # An ambiguous period, currency or repeated value needs review.
            if not candidates:
                continue
            if len(candidates) != 1 or len(values[candidates[0]]) != 1:
                break
            key = candidates[0]
            period = (key[2] + ' ~ ' if key[2] else '') + key[3]
            result.append(dict(label=LABELS.get(tag, label), value=float(next(iter(values[key]))),
                unit=key[1], period=period,
                source={**origin, 'label': 'SEC 연차 원문 XBRL · ' + tag,
                        'url': origin['url'] + ('#' + anchors[key] if key in anchors else '')}))
            break
    return result
