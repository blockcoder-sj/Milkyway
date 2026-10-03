"""Replace this parser's excerpts only where reviewed Korean sections exist."""
from .company_revenue import source_cik


GENERATED_TITLES = {
    'products': '공시 제품·서비스 원문',
    'segments': '공시 사업 구성 원문',
    'drivers': '공시 사업 위험·투입 요소 원문',
}


def replace_excerpts(data, curated, normalized):
    """Preserve translated/manual facts, other issuers, and original citations."""
    if not curated.get('cik'):
        return
    own_ciks = {int(curated['cik'])}
    # A verified historical operating issuer can differ from its new holdco.
    # Use only curated original financial citations, never user cache sources.
    own_ciks.update(source_cik(row['source']) for row in normalized['financials'])
    own_ciks.discard(None)
    reviewed_revenue = any(row['title'] == '매출이 생기는 구조' and row['detail']
                           for row in normalized['brief'])
    for key, title in GENERATED_TITLES.items():
        if not normalized[key] and not (key == 'segments' and reviewed_revenue):
            continue
        retained = []
        for row in data[key]:
            if (row['title'] == title and row['original'] and not row['detail']
                    and row['source']['level'] == 'primary'
                    and source_cik(row['source']) in own_ciks):
                data['sources'].append(row['source'])
            else:
                retained.append(row)
        data[key] = retained
