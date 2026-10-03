"""Reviewed offshore tables: exact issuer, document, year and leaf coordinates.

Exclude nonconsolidated JV revenue, product/region subtotals and intersegment
columns. Hornbeck's annual table remains the historical Helix scope; Expro's
table is the specifically verified predecessor N.V. filing.
"""
from decimal import Decimal

IDENTITIES = {'NE': 1895262, 'RIG': 1451505, 'SDRL': 1737706, 'VAL': 314808,
              'TDW': 98222, 'SMHI': 1690334, 'VTOL': 1525221, 'HOS': 866829, 'XPRO': 1575828}
DOCUMENTS = {
    ('NE', 1895262): 'https://www.sec.gov/Archives/edgar/data/1895262/000189526226000076/ne-20251231.htm',
    ('RIG', 1451505): 'https://www.sec.gov/Archives/edgar/data/1451505/000145150526000018/rig-20251231x10k.htm',
    ('SDRL', 1737706): 'https://www.sec.gov/Archives/edgar/data/1737706/000173770626000010/sdrl-20251231.htm',
    ('VAL', 314808): 'https://www.sec.gov/Archives/edgar/data/314808/000031480826000029/val-20251231.htm',
    ('TDW', 98222): 'https://www.sec.gov/Archives/edgar/data/98222/000143774926006391/tdw20251231_10k.htm',
    ('SMHI', 1690334): 'https://www.sec.gov/Archives/edgar/data/1690334/000119312526072102/smhi-20251231.htm',
    ('VTOL', 1525221): 'https://www.sec.gov/Archives/edgar/data/1525221/000152522126000013/vtol-20251231.htm',
    ('HOS', 866829): 'https://www.sec.gov/Archives/edgar/data/866829/000086682926000008/hlx-20251231x10k.htm',
    ('XPRO', 1575828): 'https://www.sec.gov/Archives/edgar/data/1575828/000143774926004727/xpro20251231_10k.htm',
}
PERIOD = ('2025-01-01', '2025-12-31')
CONTRACT = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
METRICS = {s: 'us-gaap:Revenues' if s in {'SDRL', 'VAL', 'VTOL'} else
           'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax' if s == 'SMHI' else CONTRACT
           for s in IDENTITIES}
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


_members('NE', PRODUCT, 'product', {'ne:FloatersMember': '부유식 리그 시추',
    'ne:JackupsMember': 'Jackup 시추', 'us-gaap:ServiceOtherMember': '기타 서비스'})
_members('NE', SEGMENT, 'segment', {'ne:ReportableSegmentMember': '계약 시추 · 단일 보고 부문'})
_members('NE', GEO, 'geography', {'country:AU': '호주', 'country:BR': '브라질',
    'country:CO': '콜롬비아', 'country:DK': '덴마크', 'country:GH': '가나', 'country:GW': '기니비사우',
    'country:GY': '가이아나', 'country:MY': '말레이시아', 'country:NA': '나미비아',
    'country:NG': '나이지리아', 'country:NO': '노르웨이', 'country:SR': '수리남',
    'country:GB': '영국', 'country:US': '미국', 'ne:OtherCountriesMember': '기타 국가'},
    [(SEGMENT, 'ne:ReportableSegmentMember')])
_members('RIG', PRODUCT, 'product', {'rig:UltraDeepwaterFloatersMember': '초심해 부유식 리그',
    'rig:HarshEnvironmentFloatersMember': '가혹 환경 부유식 리그'})
_members('RIG', GEO, 'geography', {'country:US': '미국', 'country:BR': '브라질',
    'country:NO': '노르웨이', 'rig:OtherGeographicalMember': '기타 지역'})
_members('SDRL', GEO, 'geography', {'country:BR': '브라질', 'country:US': '미국',
    'country:AO': 'Angola', 'country:NO': '노르웨이', 'sdrl:OtherGeographicSegmentMember': '기타 지역'})
_members('VAL', SEGMENT, 'segment', {'val:FloatersMember': '부유식 리그 · 환급 포함',
    'val:JackupsMember': 'Jackups · 환급 포함', 'us-gaap:AllOtherSegmentsMember': '기타 · 비연결 ARO 제외'}, [OPERATING])
_members('VAL', GEO, 'geography', {'country:BR': '브라질', 'country:GB': '영국',
    'val:GulfOfAmericaMember': '미국 Gulf', 'country:AO': 'Angola', 'country:AU': '호주',
    'val:OtherGeographicAreasMember': '기타 지역'},
    [('us-gaap:ConcentrationRiskByTypeAxis', 'us-gaap:GeographicConcentrationRiskMember'),
     ('us-gaap:ConcentrationRiskByBenchmarkAxis', 'us-gaap:SalesRevenueNetMember')])
_members('TDW', PRODUCT, 'product', {'tdw:VesselMember': '선박 서비스',
    'us-gaap:ProductAndServiceOtherMember': '기타'})
_members('TDW', GEO, 'geography', {'country:AO': 'Angola', 'country:GB': '영국',
    'country:SA': 'Saudi Arabia', 'country:NO': '노르웨이', 'country:AU': '호주',
    'country:US': '미국', 'tdw:OtherCountriesMember': '기타 국가'})
_members('SMHI', PRODUCT, 'product', {'smhi:TimeCharterMember': 'Time charter · 운영 포함',
    'smhi:BareboatCharterMember': 'Bareboat charter · 고객 운영',
    'smhi:OtherMarineServicesMember': '기타 해양 서비스'})
_members('SMHI', GEO, 'geography', {'country:US': '미국', 'smhi:AfricaAndEuropeMember': '아프리카·유럽',
    'smhi:MiddleEastAndAsiaMember': '중동·아시아', 'srt:LatinAmericaMember': '중남미'})
_members('VTOL', SEGMENT, 'segment', {'vtol:OffshoreEnergyServicesMember': '해양 에너지 항공 수송',
    'vtol:GovernmentServicesMember': '정부 SAR·항공 서비스', 'us-gaap:AllOtherSegmentsMember': '기타 항공 서비스'})
_members('VTOL', GEO, 'geography', {'country:GB': '영국', 'country:NO': '노르웨이',
    'country:US': '미국', 'country:NG': '나이지리아', 'vtol:OtherCountriesMember': '기타 국가'})
_members('HOS', PRODUCT, 'product', {'hlx:ProductionMaximizationMember': '생산 개선 · 결합 전 Helix',
    'hlx:DecommissioningMember': '폐쇄·철거 · 결합 전 Helix', 'hlx:RenewablesMember': '재생에너지 · 결합 전 Helix',
    'us-gaap:ServiceOtherMember': '기타 · 결합 전 Helix'})
_members('HOS', SEGMENT, 'segment', {'hlx:WellInterventionMember': '유정 개입 · 결합 전 Helix',
    'hlx:RoboticsMember': '로봇 · 내부거래 제거 후', 'hlx:ShallowWaterAbandonmentMember': '천해 폐쇄 · 제거 후',
    'hlx:ProductionFacilitiesMember': '생산시설 · 결합 전 Helix'})
_members('HOS', GEO, 'geography', {'country:US': '미국', 'hlx:NorthSeaMember': 'North Sea · 영국 포함',
    'country:BR': '브라질', 'srt:AsiaPacificMember': '아시아·태평양', 'srt:AfricaMember': '아프리카',
    'hlx:OtherGeographicLocationMember': '기타 지역'})
_members('XPRO', PRODUCT, 'product', {'xpro:WellConstructionMember': '유정 건설 · 이전 NV',
    'xpro:WellManagementMember': '유정 관리 · 이전 NV'})
_members('XPRO', SEGMENT, 'segment', {'xpro:NLAMember': 'NLA · 북미·중남미',
    'xpro:ESSAMember': 'ESSA · 유럽·사하라 이남 아프리카', 'xpro:MENAMember': 'MENA · 중동·북아프리카',
    'xpro:APACMember': 'APAC · 아시아·태평양'})


def reviewed(row, symbol, cik):
    return ((row['start'], row['end']) == PERIOD
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def dimensions(pairs, symbol, cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol, cik, frozenset(pairs)))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    return (not reviewed(dict(start=start, end=end, source=origin), symbol, cik)
            or tag == METRICS[symbol])


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


def annotate(rows, symbol, cik):
    for row in rows:
        if reviewed(row, symbol, cik):
            row['label'] = LABELS.get((symbol, cik, row['member']), row['label'])
            row['parent'] = None
            if symbol in {'HOS', 'XPRO'}:
                row['share_exclusion'] = ('결합 전 Helix의 2025 매출입니다. 현재 Hornbeck 전체 구성비와 다릅니다.' if symbol == 'HOS' else
                    '이전 Expro Group Holdings N.V.의 2025 매출입니다. 2026년7월 취득과 현재 Ltd 자체 연차 구성비가 아닙니다.')
                row['total'] = None
    return rows
