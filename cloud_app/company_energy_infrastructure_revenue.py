"""Issuer-bound annual tables for transport, tubulars and integrated fuels.

External sales, contract-only sales and rounded segment tables have distinct
denominators. Associate/JV revenue and anonymous concentration rows are omitted.
"""

COORDINATES = {}
LABELS = {}
DOCUMENTS = {
    ('ENB', 895728): 'https://www.sec.gov/Archives/edgar/data/895728/000119312526049810/enb-20251231.htm',
    ('PBA', 1546066): 'https://www.sec.gov/Archives/edgar/data/1546066/000154606626000014/pba-20251231_d2.htm',
    ('TRP', 1232384): 'https://www.sec.gov/Archives/edgar/data/1232384/000123238426000015/trp-20251231_d2.htm',
    ('SOBO', 2019061): 'https://www.sec.gov/Archives/edgar/data/2019061/000201906126000006/sobo-20251231.htm',
    ('TS', 1190723): 'https://www.sec.gov/Archives/edgar/data/1190723/000155485526000490/ts-20251231.htm',
    ('SSL', 314590): 'https://www.sec.gov/Archives/edgar/data/314590/000110465926104048/ssl-20260630xex99d1.htm',
}


def _add(symbol, cik, pairs, group, member, label):
    COORDINATES[symbol, cik, frozenset(pairs)] = group, member
    LABELS[symbol, cik, member] = label


def _members(symbol, cik, axis, group, members):
    for member, label in members.items():
        _add(symbol, cik, [(axis, member)], group, member, label)


_members('ENB', 895728, 'srt:ProductOrServiceAxis', 'product', {
    'enb:CommoditySalesRevenueMember': '상품 판매 · 연결 총매출 기준',
    'enb:GasDistributionRevenueMember': '가스 배급 · 연결 총매출 기준',
    'enb:TransportationAndOtherServicesRevenuesMember': '운송·기타 서비스 · 연결 총매출 기준',
})
_members('ENB', 895728, 'us-gaap:StatementBusinessSegmentsAxis', 'segment', {
    'enb:LiquidsPipelinesSegmentMember': '원유·액체 운송 · 고객 계약만',
    'enb:GasTransmissionSegmentMember': '가스 운송 · 고객 계약만',
    'enb:GasDistributionandStorageSegmentMember': '가스 배급·저장 · 고객 계약만',
    'enb:RenewablePowerGenerationSegmentMember': '재생 전력 · 고객 계약만',
})
_members('ENB', 895728, 'srt:StatementGeographicalAxis', 'geography', {
    'country:CA': '캐나다', 'country:US': '미국',
})

_members('PBA', 1546066, 'ifrs-full:SegmentsAxis', 'segment', {
    'pba:PipelinesSegmentMember': '파이프라인 · 외부 매출',
    'pba:FacilitiesSegmentMember': '처리·분별·저장 설비 · 외부 매출',
    'pba:MarketingNewVenturesSegmentMember': '상품 판매·신사업 · 외부 매출',
})
_add('PBA', 1546066,
     [('ifrs-full:SegmentConsolidationItemsAxis', 'ifrs-full:UnallocatedAmountsMember')],
     'segment', 'ifrs-full:UnallocatedAmountsMember', '기업 공통·미배분 · 외부 매출')
_members('PBA', 1546066, 'ifrs-full:ProductsAndServicesAxis', 'product', {
    'pba:TakeOrPayContractMember': '최소 용량·물량 약정 · 고객 계약만',
    'pba:FeeForServiceMember': '이용량 기반 서비스 · 고객 계약만',
    'pba:ProductSalesMember': '상품 판매 · 고객 계약만',
})

_members('TRP', 1232384, 'us-gaap:StatementBusinessSegmentsAxis', 'segment', {
    'trp:CanadianNaturalGasPipelinesMember': '캐나다 천연가스망',
    'trp:U.S.NaturalGasPipelinesMember': '미국 천연가스망',
    'trp:MexicoNaturalGasPipelinesMember': '멕시코 천연가스망',
    'trp:PowerAndEnergySolutionsMember': '전력·에너지 솔루션',
    'us-gaap:CorporateMember': '본사·기타',
})
_members('TRP', 1232384, 'srt:StatementGeographicalAxis', 'geography', {
    'trp:CanadaDomesticMember': '캐나다 내수', 'trp:CanadaExportMember': '캐나다 수출',
    'country:US': '미국', 'trp:MexicoandInternationalMember': '멕시코·기타 해외',
})
for member, label in {
    'trp:CapacityArrangementsAndTransportationMember': '용량 예약·운송 · 고객 계약만',
    'trp:PowerGenerationMember': '발전 · 고객 계약만',
    'trp:NaturalGasStorageAndOtherMember': '가스 저장·기타 · 고객 계약만',
}.items():
    _add('TRP', 1232384, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
                         ('srt:ProductOrServiceAxis', member)], 'product', member, label)

for member, label in {
    'sobo:KeystonePipelineSystemSegmentMember': 'Keystone · 운송·기타',
    'sobo:MarketingSegmentMember': '상품 판매',
    'sobo:IntraAlbertaAndOtherSegmentMember': 'Alberta 운송망·기타',
}.items():
    _add('SOBO', 2019061, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
                          ('us-gaap:StatementBusinessSegmentsAxis', member)], 'segment', member, label)
_members('SOBO', 2019061, 'srt:ProductOrServiceAxis', 'product', {
    'sobo:CapacityArrangementsAndTransportationAndOtherMember': '용량·운송 · 요금 분쟁 조정 후',
    'sobo:MarketingActivitiesMember': '상품 판매',
    'us-gaap:ProductAndServiceOtherMember': '기타 수입',
})
_members('SOBO', 2019061, 'srt:ProductOrServiceAxis', 'revenue_type', {
    'sobo:CapacityArrangementsAndTransportationMember': '용량·운송 · 요금 조정 전 소계',
    'sobo:OtherThanCapacityArrangementsAndTransportationMember': '변동 요금 분쟁 · 매출 차감',
})
_members('SOBO', 2019061, 'srt:StatementGeographicalAxis', 'geography', {
    'country:US': '미국', 'sobo:CanadaDomesticMember': '캐나다 내수',
    'sobo:CanadaExportMember': '캐나다 수출',
})

_members('TS', 1190723, 'ifrs-full:SegmentsAxis', 'segment', {
    'ts:TubesMember': '강관 · 백만 USD 반올림 표',
    'ifrs-full:AllOtherSegmentsMember': '기타 사업 · 백만 USD 반올림 표',
})
_members('TS', 1190723, 'ifrs-full:GeographicalAreasAxis', 'geography', {
    'srt:NorthAmericaMember': '북미', 'srt:SouthAmericaMember': '남미',
    'srt:EuropeMember': '유럽', 'ts:AsiaPacificMiddleEastAndAfricaMember': '아시아태평양·중동·아프리카',
})
_members('SSL', 314590, 'ifrs-full:SegmentsAxis', 'segment', {
    'ssl:MiningSegmentMember': '석탄 채굴 · 외부 매출',
    'ssl:GasSegmentMember': '가스 · 외부 매출',
    'ssl:FuelsSegmentMember': '연료 · 외부 매출',
    'ssl:ChemicalsAfricaMember': '아프리카 화학 · 외부 매출',
    'ssl:ChemicalsAmericaMember': '미주 화학 · 외부 매출',
    'ssl:ChemicalsEurasiaMember': '유라시아 화학 · 외부 매출',
})
_members('SSL', 314590, 'ifrs-full:GeographicalAreasAxis', 'geography', {
    'ifrs-full:CountryOfDomicileMember': '남아프리카공화국', 'country:MZ': '모잠비크',
    'country:US': '미국', 'srt:EuropeMember': '유럽', 'ssl:OtherCountryMember': '기타 국가',
})
for segment, products in {
    'ssl:EnergyBusinessSegmentMember': {
        'ssl:CoalMember': '에너지 · 석탄', 'ssl:LiquidFuelsMember': '에너지 · 액체 연료',
        'ssl:GasAndCondensateMember': '에너지 · 가스·콘덴세이트',
    },
    'ssl:ChemicalsAfricaMember': {
        'ssl:BaseChemicalsMember': '아프리카 · 기초 화학',
        'ssl:DifferentiatedChemicalsMember': '아프리카 · 특수 화학',
    },
    'ssl:ChemicalsAmericaMember': {
        'ssl:BaseChemicalsMember': '미주 · 기초 화학',
        'ssl:DifferentiatedChemicalsMember': '미주 · 특수 화학',
    },
    'ssl:ChemicalsEurasiaMember': {'ssl:DifferentiatedChemicalsMember': '유라시아 · 특수 화학'},
}.items():
    for member, label in products.items():
        _add('SSL', 314590, [('ifrs-full:SegmentsAxis', segment),
                            ('ifrs-full:ProductsAndServicesAxis', member)],
             'product', segment + '/' + member, label + ' · 고객 계약만')
_members('SSL', 314590, 'ifrs-full:ProductsAndServicesAxis', 'product', {
    'ssl:OtherIpRefineryServicesMember': '지식재산·정유 서비스 · 고객 계약만',
})


def dimensions(pairs, symbol, cik):
    if len(set(pairs)) != len(pairs):
        return None
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def reviewed(row, symbol, cik):
    start, end = ('2025-07-01', '2026-06-30') if symbol == 'SSL' else ('2025-01-01', '2025-12-31')
    return (row['start'] == start and row['end'] == end
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    row = {'start': start, 'end': end, 'source': origin}
    if not reviewed(row, symbol, cik):
        return True
    if symbol == 'ENB' and group == 'segment':
        return tag == 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
    if symbol in {'ENB', 'TRP'} and group in {'product', 'segment', 'geography'}:
        return tag == ('us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
                       if symbol == 'TRP' and group == 'product' else 'us-gaap:Revenues')
    if symbol == 'PBA':
        return tag == ('ifrs-full:RevenueFromContractsWithCustomers' if group == 'product' else 'ifrs-full:Revenue')
    if symbol in {'TS', 'SSL'}:
        return tag == ('ifrs-full:RevenueFromContractsWithCustomers'
                       if symbol == 'SSL' and group == 'product' else 'ifrs-full:Revenue')
    if symbol == 'SOBO' and group in {'segment', 'geography'}:
        return tag == 'us-gaap:Revenues'
    return True


def presentation_group(row, symbol, cik):
    if reviewed(row, symbol, cik):
        for (issuer, identity, _), (group, member) in COORDINATES.items():
            if (issuer, identity, member) == (symbol, cik, row['member']):
                return group
    return row['group']


def annotate(rows, symbol, cik):
    for row in rows:
        if not reviewed(row, symbol, cik):
            continue
        if symbol == 'TS' and row['group'] == 'segment':
            row['total'] = None
            row['share_exclusion'] = ('사업 부문은 백만 USD 반올림 표로 11,400,000,000 + 581,000,000입니다. '
                '정밀 연결 매출 11,981,157,000 USD와 차이 157,000 USD를 임의로 부문에 배분하지 않습니다.')
        if symbol == 'SOBO' and row['group'] == 'revenue_type':
            row['total'] = None
            row['share_exclusion'] = ('용량·운송 1,634,000,000 USD에서 Keystone 변동 요금 분쟁 관련 169,000,000 USD를 차감한 '
                '1,465,000,000 USD가 제품 구성 표에 포함됩니다. 소계·차감 항목을 제품 매출에 다시 더하지 않습니다.')
        if symbol == 'TRP' and row['group'] == 'product':
            row['total'] = None
            row['share_exclusion'] = ('영업 부문 고객 계약 매출 13,963,000,000 CAD만 포함합니다. '
                '리스 등 1,262,000,000 CAD 및 본사 14,000,000 CAD를 포함한 연결 매출 15,239,000,000 CAD와 범위가 다릅니다.')
    return rows
