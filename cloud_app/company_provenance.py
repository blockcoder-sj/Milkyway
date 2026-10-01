"""Remove rejected encyclopedia knowledge while preserving navigation identities."""
from urllib.parse import urlsplit
import re


def forbidden(origin):
    if origin is None:
        return False
    value = origin if isinstance(origin, dict) else origin.model_dump()
    host = (urlsplit(value.get('url', '')).hostname or '').lower().rstrip('.')
    return value.get('level') == 'encyclopedia' or any(
        host == domain or host.endswith('.' + domain)
        for domain in ('wikipedia.org', 'wikidata.org', 'wikimedia.org')
    )


def clean(value):
    """Pure cleanup used for old JSON, DB profiles and new provider results."""
    if not isinstance(value, dict):
        value = value.model_dump()
    result = dict(value)
    rejected_source = any(forbidden(row) for row in result.get('sources', []))
    if not result.get('entity_id'):
        for item in result.get('sources', []):
            source = item if isinstance(item, dict) else item.model_dump()
            match = re.fullmatch(r'https://www\.wikidata\.org/wiki/(Q\d{1,12})', source.get('url', ''))
            if match and source.get('label') == 'Wikidata · 공개 기업 정보':
                # An old opaque alias keeps existing links stable; no wiki facts retained.
                result['entity_id'] = match[1]
                break
    for field in ('facts', 'products', 'segments', 'market_shares', 'drivers',
                  'relations', 'financials', 'brief', 'revenue_mix'):
        if field in result:
            rows = result[field]
            result[field] = [row for row in rows if not forbidden(
                row.get('source') if isinstance(row, dict) else row.source)]
    for field in ('sources', 'filings'):
        if field in result:
            result[field] = [row for row in result[field] if not forbidden(row)]
    if forbidden(result.get('description_source')) or (rejected_source and not result.get('description_source')):
        result['description'], result['description_source'] = '', None
    marker = ' · 규칙으로 추출한 원문: '
    for field in ('facts', 'products', 'segments', 'drivers', 'relations'):
        rows = []
        for item in result.get(field, []):
            row = dict(item) if isinstance(item, dict) else item.model_dump()
            if field == 'relations' and marker in row.get('detail', ''):
                row['detail'], original = row['detail'].split(marker, 1)
                row['original'] = row.get('original') or original[:1500]
            elif '원문' in row.get('title', '') and row.get('detail'):
                row['original'] = row.get('original') or row['detail'][:1500]
                row['detail'] = ''
            rows.append(row)
        if field in result:
            result[field] = rows
    if result.get('report_analysis'):
        item = result['report_analysis']
        if forbidden(item.get('source') if isinstance(item, dict) else item.source):
            result['report_analysis'] = None
    if 'errors' in result:
        legacy_wiki_failure = 'wikidata' in result.get('unavailable_sources', [])
        result['errors'] = [message for message in result['errors']
            if not any(word in message.lower() for word in ('wikidata', 'wikipedia', '공개 백과'))
            and not (legacy_wiki_failure and re.search(r'\bwiki\b', message, re.I))]
    if 'unavailable_sources' in result:
        result['unavailable_sources'] = [item for item in result['unavailable_sources'] if item != 'wikidata']
    return result
