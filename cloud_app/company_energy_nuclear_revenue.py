"""Reviewed nuclear fuel revenue coordinates, with original table exceptions.

The two issuer tagging errors below are bound to an exact original, period,
member, currency and value. Original amounts and member IDs remain intact.
"""
DOCUMENTS = {
    ('CCJ', 1009001): 'https://www.sec.gov/Archives/edgar/data/1009001/000119312526116229/d34605dex992.htm',
    ('DNN', 1063259): 'https://www.sec.gov/Archives/edgar/data/1063259/000110465926036912/dnn-20251231xex99d3.htm',
    ('NXE', 1698535): 'https://www.sec.gov/Archives/edgar/data/1698535/000119312526089376/d84755dex993.htm',
    ('UEC', 1334933): 'https://www.sec.gov/Archives/edgar/data/1334933/000143774926031414/uec20260731_10k.htm',
    ('EU', 1500881): 'https://www.sec.gov/Archives/edgar/data/1500881/000162828026022507/encr-20251231.htm',
    ('URG', 1375205): 'https://www.sec.gov/Archives/edgar/data/1375205/000110465926025923/urg-20251231x10k.htm',
    ('LEU', 1065059): 'https://www.sec.gov/Archives/edgar/data/1065059/000162828026007117/leu-20251231.htm',
    ('LTBR', 1084554): 'https://www.sec.gov/Archives/edgar/data/1084554/000147793226001076/ltbr_10k.htm',
    ('UUUU', 1385849): 'https://www.sec.gov/Archives/edgar/data/1385849/000138584926000009/efr-20251231.htm',
}
COORDINATES = {}
LABELS = {}


def _add(symbol, cik, pairs, group, member, label=None):
    COORDINATES[symbol, cik, frozenset(pairs)] = group, member
    if label:
        LABELS[symbol, cik, member] = label


def _members(symbol, cik, axis, group, values):
    for member, label in values.items():
        _add(symbol, cik, [(axis, member)], group, member, label)


_members('CCJ', 1009001, 'ifrs-full:SegmentsAxis', 'segment', {
    'ccj:UraniumMember': '우라늄 생산·구매·판매',
    'ccj:FuelServicesMember': '우라늄 정련·전환·연료 서비스',
    'ccj:OtherSegmentMember': '기타 연결 사업',
})
for member, label in {'srt:NorthAmericaMember': '북미 고객',
    'srt:EuropeMember': '유럽 고객', 'srt:AsiaPacificMember': '아시아태평양 고객'}.items():
    _add('CCJ', 1009001, [('ifrs-full:SegmentsAxis', 'ifrs-full:ReportableSegmentsMember'),
        ('ifrs-full:GeographicalAreasAxis', member)], 'geography', member, label)
for member, label in {'ifrs-full:FixedpriceContractsMember': '고정 가격 계약',
    'ccj:MarketpricecontractsmemberMember': '시장 가격 연동 계약'}.items():
    _add('CCJ', 1009001, [('ifrs-full:SegmentsAxis', 'ifrs-full:ReportableSegmentsMember'),
        ('ifrs-full:TypesOfContractsAxis', member)], 'revenue_type', member, label)
_members('DNN', 1063259, 'ifrs-full:SegmentsAxis', 'segment', {
    'dnn:MiningMember': '광업 · 주로 타사 광석 처리',
    'dnn:CorporateAndOtherSegmentMember': '본사·기타',
})
_members('UEC', 1334933, 'srt:ProductOrServiceAxis', 'product', {
    'uec:SaleOfInventoryMember': '재고 우라늄 판매',
    'uec:TollProcessingServicesMember': '타사 원료 처리',
})
# The annual table puts product rows on a MajorCustomersAxis. Select only the
# one-axis copy; customer A/B and the duplicate segment-qualified copy differ.
_members('URG', 1375205, 'srt:MajorCustomersAxis', 'product', {
    'urg:UThreeOEightSalesMember': '우라늄 정광 판매',
    'urg:DisposalFeesMember': '처리·폐기 수수료',
})
_members('LEU', 1065059, 'srt:ProductOrServiceAxis', 'product', {
    'leu:SeparativeWorkUnitsMember': '농축 서비스 · SWU',
    'leu:UraniumMember': '우라늄 판매',
})
_add('LEU', 1065059, [('srt:ProductOrServiceAxis', 'us-gaap:ServiceMember'),
    ('us-gaap:StatementBusinessSegmentsAxis', 'leu:ContractServicesSegmentMember')],
    'product', 'us-gaap:ServiceMember/leu:ContractServicesSegmentMember', '기술 솔루션 · 외부 서비스')
_members('LEU', 1065059, 'srt:StatementGeographicalAxis', 'geography', {
    'country:US': '미국', 'country:JP': '일본', 'country:NL': '네덜란드',
    'leu:OtherForeignMember': '기타 해외',
})
# Preserve the reported member. Its human-readable TOTAL label is applied only
# to the reviewed 461.1m USD fact, rather than globally relabeling this member.
_add('LEU', 1065059,
    [('us-gaap:StatementBusinessSegmentsAxis', 'leu:ContractServicesSegmentMember')],
    'segment', 'leu:ContractServicesSegmentMember')
for segment, member, label in [
    ('efr:UraniumSegmentMember', 'efr:RevenuesUraniumConcentratesMember', '우라늄 정광'),
    ('efr:UraniumSegmentMember', 'efr:RevenuesVanadiumConcentratesMember', '바나듐 정광'),
    ('efr:HeavyMineralSandsSegmentMember', 'efr:RevenuesHeavyMineralSandsMember', '광물사 · 티타늄·지르콘 제품'),
    ('efr:RareEarthElementsSegmentMember', 'efr:RevenuesRECarbonateMember', '희토류 탄산염'),
    ('efr:UraniumSegmentMember', 'efr:RevenuesAlternateFeedMaterialsProcessingAndOtherMember', '대체 원료 처리·기타'),
]:
    _add('UUUU', 1385849, [('efr:RevenueTypeAxis', member),
        ('us-gaap:StatementBusinessSegmentsAxis', segment)], 'product', member, label)
for segment, label in {'efr:UraniumSegmentMember': '우라늄·바나듐·대체 원료 처리',
    'efr:HeavyMineralSandsSegmentMember': '광물사',
    'efr:RareEarthElementsSegmentMember': '희토류'}.items():
    _add('UUUU', 1385849, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', segment)], 'segment', segment, label)
for country, segments in {
    'US': ('Uranium', 'HeavyMineralSands'), 'CA': ('Uranium',),
    'SA': ('HeavyMineralSands',), 'CN': ('HeavyMineralSands',),
    'JP': ('Uranium', 'HeavyMineralSands'), 'NL': ('Uranium', 'HeavyMineralSands'),
    'EE': ('Uranium', 'RareEarthElements'), 'DE': ('Uranium',),
    'ES': ('HeavyMineralSands',), 'KR': ('HeavyMineralSands',),
    'MX': ('Uranium',), 'KE': ('HeavyMineralSands',), 'AE': ('Uranium',),
}.items():
    names = {'US': '미국', 'CA': '캐나다', 'SA': '사우디아라비아', 'CN': '중국',
        'JP': '일본', 'NL': '네덜란드', 'EE': '에스토니아', 'DE': '독일',
        'ES': '스페인', 'KR': '한국', 'MX': '멕시코', 'KE': '케냐', 'AE': '아랍에미리트'}
    for segment in segments:
        member = 'country:' + country + '/efr:' + segment + 'SegmentMember'
        # The two erroneous tags receive no global display override.
        corrected_tag = (country, segment) in {('EE', 'RareEarthElements'), ('AE', 'Uranium')}
        label = None if corrected_tag else names[country] + ' · ' + {
            'Uranium': '우라늄', 'HeavyMineralSands': '광물사', 'RareEarthElements': '희토류'}[segment]
        _add('UUUU', 1385849, [('srt:StatementGeographicalAxis', 'country:' + country),
            ('us-gaap:StatementBusinessSegmentsAxis', 'efr:' + segment + 'SegmentMember')],
            'geography', member, label)


def dimensions(pairs, symbol, cik):
    if len(set(pairs)) != len(pairs):
        return None
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def compound_member(member, symbol, cik):
    return '/' in member and any((s, identity, candidate) == (symbol, cik, member)
        for (s, identity, _), (_, candidate) in COORDINATES.items())


def reviewed(row, symbol, cik):
    dates = ('2025-08-01', '2026-07-31') if symbol == 'UEC' else ('2025-01-01', '2025-12-31')
    return (row['start'], row['end']) == dates and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    if not reviewed(dict(start=start, end=end, source=origin), symbol, cik):
        return True
    expected = ('ifrs-full:RevenueFromContractsWithCustomers' if symbol == 'CCJ'
        else 'ifrs-full:Revenue' if symbol in {'DNN', 'NXE'} else 'us-gaap:Revenues'
        if symbol in {'URG', 'UEC', 'EU'} else 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax')
    return tag == expected


def _gross_total(row, symbol, cik):
    return ((symbol, cik) == ('LEU', 1065059) and reviewed(row, symbol, cik)
        and row['member'] == 'leu:ContractServicesSegmentMember'
        and row['unit'] == 'USD' and row['value'] == 461100000)


def presentation_group(row, symbol, cik):
    return 'revenue_type' if _gross_total(row, symbol, cik) else row['group']


def annotate(rows, symbol, cik):
    for row in rows:
        if not reviewed(row, symbol, cik):
            continue
        if symbol == 'CCJ' and row['unit'] == 'CAD':
            row['share_exclusion'] = ('고객 계약 매출의 합계는 3,481,933,000 CAD로 연결 매출과 일치하지만 '
                '원문의 해당 합계는 ReportableSegmentsMember 좌표입니다. 같은 지표의 무차원 총액이 없어 '
                '다른 매출 태그의 총액을 분모로 대체하지 않습니다. 세 보기의 금액은 서로 중복되는 별도 분류입니다.')
        if _gross_total(row, symbol, cik):
            row['group'], row['label'], row['total'], row['parent'] = 'revenue_type', '전체 사업 · 내부 제거 전', None, None
            row['share_exclusion'] = ('본문의 전체 사업 합계 461,100,000 USD에 기술 솔루션 사업부 태그가 잘못 연결돼 있습니다. '
                '내부 매출 12,400,000 USD 제거 후 연결 매출은 448,700,000 USD이며 실제 외부 기술 솔루션 매출은 102,500,000 USD입니다.')
        if symbol == 'UUUU' and row['unit'] == 'USD':
            correction = {
                ('country:EE/efr:RareEarthElementsSegmentMember', 348000): '오스트리아 · 광물사 · 본문 기준',
                ('country:AE/efr:UraniumSegmentMember', 195000): '아랍에미리트 · 광물사 · 본문 기준',
            }.get((row['member'], row['value']))
            if correction:
                row['label'] = correction
                row['share_exclusion'] = ('원문 매출 지역 표의 국가·제품 이름을 표시했습니다. XBRL의 국가 또는 사업부 태그는 본문과 '
                    '일치하지 않으며 원래 태그·금액·출처를 보존합니다. 이 표는 고객 소재지와 제품을 함께 나눈 표입니다.')
    return rows


def canonical(rows, symbol, cik):
    allowed = {member for (s, identity, _), (_, member) in COORDINATES.items() if (s, identity) == (symbol, cik)}
    return [row for row in rows if not reviewed(row, symbol, cik) or row['member'] in allowed]
