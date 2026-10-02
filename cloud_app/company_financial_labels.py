"""Display the reported metric, without changing a value or its accounting scope."""

CONTRACT_REVENUE = 'RevenueFromContractWithCustomerExcludingAssessedTax'


def label(metric, fallback):
    if metric.removeprefix('us-gaap:') == CONTRACT_REVENUE:
        return '고객 계약 매출 · 부과세 제외'
    return fallback


def presented(rows):
    """Also correct legacy caches whose SEC contract revenue was called total sales."""
    result = []
    for row in rows:
        metric = row.get('source', {}).get('label', '').removeprefix('SEC XBRL · ')
        result.append({**row, 'label': label(metric, row['label'])}
                      if row['label'] == '매출' else dict(row))
    return result
