"""Small original-document exceptions reviewed against visible annual tables.

No rule permits a country, product, subsidiary or discontinued-only value to
become a group total. These coordinates expire outside the exact issuer/document
and declared FY2025 period; unrelated issuers retain the strict default.
"""

SU = 'https://www.sec.gov/Archives/edgar/data/311337/000110465926020411/su-20251231xex99d2.htm'
VET = 'https://www.sec.gov/Archives/edgar/data/1293135/000110465926023553/vet-20251231xex99d3.htm'
IMO = 'https://www.sec.gov/Archives/edgar/data/49938/000004993826000009/imo-20251231.htm'
SU_TAGS = frozenset({'ifrs-full:CashFlowsFromUsedInOperations',
                     'su:CashFlowsUsedForCapitalExpenditures'})
VET_AGGREGATE = ('ifrs-full:ContinuingAndDiscontinuedOperationsAxis',
                 'ifrs-full:AggregateContinuingAndDiscontinuedOperationsMember')
VET_TAGS = frozenset({'ifrs-full:Assets', 'ifrs-full:Liabilities',
                      'ifrs-full:CashAndCashEquivalents', 'ifrs-full:Equity',
                      'ifrs-full:CashFlowsFromUsedInOperatingActivities'})


def _reviewed(origin, cik, end, document, identity):
    return (int(cik) == identity and end.isoformat() == '2025-12-31'
            and origin.get('url', '').split('#')[0] == document)


def metric_allowed(tag, origin, cik, end):
    return tag not in SU_TAGS or _reviewed(origin, cik, end, SU, 311337)


def context_tags(ctx, origin, cik, end, wanted):
    if ctx.find('xbrldi:typedmember'):
        return None
    pairs = [(m.get('dimension'), m.get_text(strip=True))
             for m in ctx.find_all('xbrldi:explicitmember')]
    if not pairs:
        return wanted
    if (pairs == [VET_AGGREGATE]
            and _reviewed(origin, cik, end, VET, 1293135)):
        return VET_TAGS
    return None


def financial_label(metric, fallback, origin, period):
    if (metric == 'us-gaap:Revenues' and origin
            and origin.get('url', '').split('#')[0] == IMO
            and period == '2025-01-01 ~ 2025-12-31'):
        return '매출·기타소득 합계'
    return fallback
