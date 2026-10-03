"""Exact annual LNG tables, including the signed VG reconciliation.

NFE's 2025 scope precedes the September 2026 Brazil separation. Commissioning
sales are actual revenue; contracted future LNG capacity is not revenue.
"""
from decimal import Decimal

IDENTITIES = {'EE': 1888447, 'NEXT': 1612720, 'NFE': 1749723, 'VG': 2007855}
DOCUMENTS = {
    ('EE', 1888447): 'https://www.sec.gov/Archives/edgar/data/1888447/000119312526078407/ee-20251231.htm',
    ('NEXT', 1612720): 'https://www.sec.gov/Archives/edgar/data/1612720/000161272026000009/next-20251231.htm',
    ('NFE', 1749723): 'https://www.sec.gov/Archives/edgar/data/1749723/000174972326000032/nfe-20251231.htm',
    ('VG', 2007855): 'https://www.sec.gov/Archives/edgar/data/2007855/000200785526000013/vg-20251231.htm',
}
PERIOD = ('2025-01-01', '2025-12-31')
CONTRACT = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
PRODUCT = 'srt:ProductOrServiceAxis'
SEGMENT = 'us-gaap:StatementBusinessSegmentsAxis'
GEO = 'srt:StatementGeographicalAxis'
OPERATING = ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember')
COORDINATES, LABELS = {}, {}


def _members(symbol, axis, group, values, qualifiers=()):
    cik = IDENTITIES[symbol]
    for member, label in values.items():
        COORDINATES[symbol, cik, frozenset([(axis, member), *qualifiers])] = group, member
        LABELS[symbol, cik, member] = label


_members('EE', PRODUCT, 'product', {'ee:FsruAndTerminalServicesMember': 'FSRU·터미널 서비스',
    'ee:GasSalesMember': 'LNG·가스·전력 판매'})
_members('EE', GEO, 'geography', {'srt:NorthAmericaMember': '북미', 'srt:AsiaPacificMember': '아시아·태평양',
    'srt:LatinAmericaMember': '중남미', 'srt:EuropeMember': '유럽',
    'us-gaap:MiddleEastMember': '중동', 'ee:OtherMember': '기타 지역'})
_members('NFE', PRODUCT, 'product', {'nfe:CargoSalesMember': 'Cargo 판매 · 고객 계약 매출의 일부'})
_members('NFE', SEGMENT, 'segment', {'nfe:TerminalsAndInfrastructureSegmentMember': '터미널·인프라 · 2025 범위',
    'nfe:ShipsSegmentMember': '선박 · 2025 범위'}, [OPERATING])
_members('NFE', GEO, 'geography', {'country:US': '미국', 'us-gaap:NonUsMember': '미국 외 · 2025 범위'})
_members('VG', PRODUCT, 'product', {'vg:LiquefiedNaturalGasMember': 'LNG 판매',
    'us-gaap:ProductAndServiceOtherMember': '기타 제품·서비스'})
_members('VG', SEGMENT, 'segment', {'vg:CalcasieuProjectSegmentMember': 'Calcasieu Pass',
    'vg:PlaqueminesProjectSegmentMember': 'Plaquemines', 'vg:CP2ProjectSegmentMember': 'CP2',
    'vg:SalesAndShippingSegmentMember': '판매·해운'}, [OPERATING])
_members('VG', 'srt:ConsolidationItemsAxis', 'segment',
    {'vg:CorporateReconcilingItemsAndEliminationsMember': '본사 조정·내부거래 제거'})
_members('VG', GEO, 'geography', {'country:US': '미국', 'country:DE': '독일', 'country:FR': '프랑스',
    'country:NL': '네덜란드', 'country:GB': '영국', 'vg:OtherGeographicalAreasMember': '기타 지역'})


def reviewed(row, symbol, cik):
    return ((row['start'], row['end']) == PERIOD
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def dimensions(pairs, symbol, cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol, cik, frozenset(pairs)))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    if not reviewed(dict(start=start, end=end, source=origin), symbol, cik):
        return True
    return tag == (CONTRACT if symbol == 'VG' or (symbol == 'NFE' and group == 'product') else 'us-gaap:Revenues')


def canonical(rows, symbol, cik):
    allowed = {(group, member) for (issuer, identity, _), (group, member) in COORDINATES.items()
               if (issuer, identity) == (symbol, cik)}
    selected = [row for row in rows if not reviewed(row, symbol, cik) or (
        row['unit'] == 'USD' and (row['group'], row['member']) in allowed
        and metric_allowed(row['metric'], row['group'], row['start'], row['end'], row['source'], symbol, cik))]
    values = {}
    for row in selected:
        if reviewed(row, symbol, cik):
            key = tuple(row[k] for k in ('group', 'member', 'start', 'end', 'unit', 'metric'))
            values.setdefault(key, set()).add(Decimal(str(row['value'])))
    kept, seen = [], set()
    for row in selected:
        if reviewed(row, symbol, cik):
            key = tuple(row[k] for k in ('group', 'member', 'start', 'end', 'unit', 'metric'))
            if key in seen or len(values[key]) != 1:
                continue
            seen.add(key)
        kept.append(row)
    return kept


def presentation_group(row, symbol, cik):
    if reviewed(row, symbol, cik):
        groups = {group for (issuer, identity, _), (group, member) in COORDINATES.items()
                  if (issuer, identity, member) == (symbol, cik, row['member'])}
        if len(groups) == 1:
            return groups.pop()
    return row['group']


def signed_value(tag, context, origin, symbol, cik):
    start, end, group, member = context
    return (symbol == 'VG' and cik == IDENTITIES['VG'] and tag == CONTRACT
            and (group, member) == ('segment', 'vg:CorporateReconcilingItemsAndEliminationsMember')
            and reviewed(dict(start=start, end=end, source=origin), symbol, cik))


def annotate(rows, symbol, cik):
    for row in rows:
        if reviewed(row, symbol, cik):
            row['label'] = LABELS.get((symbol, cik, row['member']), row['label'])
            row['parent'] = None
            if symbol == 'NFE':
                row['share_exclusion'] = '2025 연차 범위입니다. 2026년9월 Brazil 분리 후 New NFE 전체 구성비가 아닙니다. Cargo는 고객 계약 매출의 일부입니다.'
                row['total'] = None
            if symbol == 'VG' and row['group'] == 'segment':
                row['share_exclusion'] = '부문 매출에 -2,050,000,000 USD 본사 조정·내부거래 제거를 포함합니다. 부문 합계를 연결 구성비로 사용하지 않습니다.'
                row['includes_intersegment'], row['total'] = True, None
    return rows
