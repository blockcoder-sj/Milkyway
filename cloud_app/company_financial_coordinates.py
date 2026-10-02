"""Exact filing coordinates and independent companyfacts corroboration."""
import re

from .company_revenue import source_cik


def metric(row):
    label = row['source']['label']
    for prefix in ('SEC 연차 원문 XBRL · ', 'SEC XBRL · '):
        if label.startswith(prefix):
            return label.removeprefix(prefix).removeprefix('us-gaap:')
    return None


def coordinate(row):
    tag = metric(row)
    if tag is None:
        return None
    return tag, row['unit'], row['period'], row['source']['url'].split('#')[0]


def corroborates(original, candidate):
    """Omit a repeated API value only when its issuer, tag, date and value agree.

    A different figure, filing date, period, currency or actual filing remains a
    separate report. This is not a name-based or approximate-value merge.
    """
    match = re.fullmatch(r'https://data\.sec\.gov/api/xbrl/companyfacts/CIK(\d{10})\.json',
                         candidate['source']['url'])
    return bool(match and original['source'].get('level') == 'primary'
        and candidate['source'].get('level') == 'primary'
        and source_cik(original['source']) == int(match[1])
        and metric(original) is not None and metric(original) == metric(candidate)
        and all(original[key] == candidate[key] for key in ('value', 'unit', 'period'))
        and original['source'].get('as_of') == candidate['source'].get('as_of')
        and original['source'].get('as_of'))
