"""Bound human-read S-1 tables to the reviewed identity, period and values.

The filings contain predecessor and pro-forma financials alongside issuer data.
No document type is changed to make a prospectus appear to be an annual 10-K.
"""
from decimal import Decimal
from .company_energy_sources import REPORTS

IDENTITIES = {'EROK':2104882,'FTW':2083125,'HMH':2021880,'WHK':1921603}

def canonical(rows, symbol, cik):
    if IDENTITIES.get(symbol) != cik:
        return rows
    record = REPORTS[symbol]
    document = record['annual']['url']
    allowed = {(r['group'],r['member'],r['metric'],Decimal(str(r['value'])))
               for r in record['revenue_mix']}
    result, seen = [], set()
    for row in rows:
        if row['source']['url'].split('#')[0] != document:
            result.append(row)
            continue
        key = (row['group'],row['member'],row['metric'],Decimal(str(row['value'])))
        if (row['unit'] != 'USD' or (row['start'],row['end']) != ('2025-01-01','2025-12-31')
                or key not in allowed or key in seen):
            continue
        seen.add(key)
        result.append(row)
    return result
