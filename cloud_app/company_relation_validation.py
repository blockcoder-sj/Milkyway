"""Recheck old automatic SEC statements without fetching or inventing identities.

Human-reviewed notes and subsidiary exhibits are not inferred filing statements.
Existing ticker/name identity is retained only when the same role and counterparty
remain supported by the stored original under the current clause rules.
"""
import re
from functools import lru_cache
from urllib.parse import urlsplit

AUTOMATIC = frozenset({
    '공시 제조·부품 공급', '공시 메모리 공급', '공시 공급·제조 관계',
    '공시 판매·고객 관계', '공시 협력 관계', '공시 경쟁 항목에 명시된 기업',
    '공시에 명시된 자회사',
})


def supported(edge, issuer):
    return _supported(edge.get('name',''),edge.get('symbol'),edge['kind'],edge['original'],issuer)


@lru_cache(maxsize=2048)
def _supported(name, symbol, role, original, issuer):
    from .company_filings import statements, counterparties, is_counterparty
    tokens = re.findall(r'[A-Za-z0-9]+', name)
    exact = re.compile(r'\b' + r'[^\w;:<>\n]*'.join(map(re.escape,tokens)) + r'\b', re.I) if 2 <= len(tokens) <= 24 else None
    claims = statements(original, role == 'competitor')
    if not claims and role == 'competitor':
        # Older records retain the competition-section context even when a
        # bullet/list doesn't repeat the heading. Do not discard that context
        # solely because the sentence has no new extraction trigger.
        claims = [('competitor','',original)]
    for kind, _, candidates in claims:
        if kind != role:
            continue
        if any(target == symbol and (symbol is not None or candidate == name)
               for candidate,target in counterparties(candidates,issuer,role=role)):
            return True
        # A v3 full legal name may be outside the vetted brand list. This only
        # checks the already stored exact identity; it assigns no new ticker.
        if exact and any(is_counterparty(candidates, match.start(), match.end(),role)
                         for match in exact.finditer(candidates)):
            return True
    return False


def legacy_rejections(value):
    version = value.get('collector_version', 0)
    if type(version) is not int or version >= 4:
        return []
    result = []
    marker = ' · 규칙으로 추출한 원문: '
    for item in value.get('relations', []):
        edge = dict(item) if isinstance(item, dict) else item.model_dump()
        if marker in edge.get('detail', ''):
            edge['detail'], original = edge['detail'].split(marker,1)
            edge['original'] = edge.get('original') or original[:1500]
        origin = edge.get('source') or {}
        if not isinstance(origin, dict):
            origin = origin.model_dump()
        if (edge.get('detail') in AUTOMATIC and edge.get('original')
                and (urlsplit(origin.get('url','')).hostname or '').lower().rstrip('.') == 'www.sec.gov'
                and not supported(edge,value.get('symbol'))):
            result.append(edge)
    return result
