"""Reviewed FY2025 service-provider revenue coordinates and presentation bases.

Gross operating segments are not external revenue weights. These exceptions
belong to exact issuers and documents; elimination rows are never admitted as
positive revenue slices. Original XBRL numbers are preserved, including rounding.
"""

COORDINATES = {}
LABELS = {}

SEGMENTS = {
    ('SLB', 87347): {
        'slb:DigitalIntegrationMember': 'Digital · 디지털',
        'slb:ReservoirPerformanceMember': '저류층 평가·생산 최적화',
        'slb:WellConstructionMember': '시추·유정 건설',
        'slb:ProductionSystemsMember': '생산 시스템·장비',
        'us-gaap:AllOtherSegmentsMember': '기타 · APS·데이터센터·탄소포집',
    },
    ('PUMP', 1680247): {
        'pump:HydraulicFracturingSegmentMember': '수압파쇄',
        'pump:WirelineOperatingSegmentMember': '와이어라인',
        'pump:CementingOperatingSegmentMember': '시멘팅',
        'pump:PowerGenerationMember': '분산 발전 · PROPWR',
    },
    ('FLOC', 2035149): {
        'floc:ProductionSolutionsMember': '인공 채유 · Production Solutions',
        'floc:NaturalGasTechnologiesMember': '가스 기술 · Natural Gas Technologies',
    },
    ('ACDC', 1881487): {
        'acdc:StimulationServicesSegmentMember': '완결·수압파쇄 서비스',
        'acdc:ProppantProductionSegmentMember': '프로판트 생산',
        'acdc:ManufacturingSegmentMember': '장비 제조',
        'acdc:FlotekSegmentMember': 'Flotek · 약품·측정',
        'us-gaap:AllOtherSegmentsMember': '기타 사업',
    },
    ('DTI', 1884516): {
        'dti:WesternHemisphereMember': '서반구 · 내부거래 포함',
        'dti:EasternHemisphereMember': '동반구 · 내부거래 포함',
    },
}

for (_symbol, _cik), _members in SEGMENTS.items():
    for _member, _label in _members.items():
        COORDINATES[(_symbol, _cik, frozenset([
            ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
            ('us-gaap:StatementBusinessSegmentsAxis', _member),
        ]))] = ('segment', _member)
        LABELS[(_symbol, _cik, _member)] = _label

for _symbol, _cik, _mapping in [
    ('BKR', 1701605, {
        'bkr:IndustrialAndEnergyTechnologyMember': '산업·에너지 기술 · IET',
        'bkr:OilfieldServicesAndEquipmentMember': '유전 서비스·장비 · OFSE',
    }),
    ('HAL', 45012, {
        'hal:CompletionAndProductionMember': '완결·생산',
        'hal:DrillingAndEvaluationMember': '시추·평가',
        'hal:EuropeAfricaCISMember': '유럽·아프리카·CIS',
        'hal:MiddleEastAsiaMember': '중동·아시아',
        'srt:LatinAmericaMember': '중남미',
    }),
    ('PTEN', 889900, {
        'pten:CompletionServicesMember': '완결 서비스 · NexTier',
        'pten:DrillingProductsMember': '시추 제품 · Ulterra',
        'pten:DrillingServicesMember': '시추 서비스',
        'pten:OtherNonUSCountriesMember': '캐나다·콜롬비아 외 해외',
        'country:CA': '캐나다', 'country:CO': '콜롬비아',
    }),
    ('SND', 1529628, {
        'snd:SandMember': '규사·프로판트',
        'snd:SmartSystemsMember': 'SmartSystems · 현장 모래 관리',
        'snd:SandSegmentMember': '규사·프로판트',
        'snd:SmartSystemsSegmentMember': 'SmartSystems · 현장 모래 관리',
        'country:CA': '캐나다',
    }),
    ('AESI', 1984060, {
        'aesi:SandLogisticsMember': '모래·물류',
        'aesi:PowerMember': '분산 발전',
        'aesi:RentalRevenueMember': '발전 장비 임대',
    }),
    ('FLOC', 2035149, {
        'floc:SurfaceEquipmentMember': '지상 인공 채유 장비',
        'floc:DownholeComponentsMember': '유정 내 인공 채유 부품',
        'floc:VaporRecoveryMember': '증기·가스 회수',
        'us-gaap:NaturalGasProductionMember': '가스 압축·패키지 장비',
    }),
    ('DTI', 1884516, {
        'dti:ToolRentalMember': '시추·완결 도구 임대',
        'us-gaap:ProductMember': '도구·부품 판매',
    }),
    ('KLXE', 1738827, {
        'klxe:CompletionRevenuesMember': '완결 서비스',
        'klxe:DrillingRevenuesMember': '시추 서비스',
        'klxe:InterventionRevenuesMember': '유정 개입·정비',
        'klxe:ProductionRevenuesMember': '생산 지원',
    }),
]:
    for _member, _label in _mapping.items():
        LABELS[(_symbol, _cik, _member)] = _label

DOCUMENTS = {
    ('SLB', 87347): 'https://www.sec.gov/Archives/edgar/data/87347/000119312526021017/slb-20251231.htm',
    ('PUMP', 1680247): 'https://www.sec.gov/Archives/edgar/data/1680247/000168024726000028/pump-20251231.htm',
    ('FLOC', 2035149): 'https://www.sec.gov/Archives/edgar/data/2035149/000119312526077219/floc-20251231.htm',
    ('ACDC', 1881487): 'https://www.sec.gov/Archives/edgar/data/1881487/000119312526106120/acdc-20251231.htm',
    ('DTI', 1884516): 'https://www.sec.gov/Archives/edgar/data/1884516/000119312526095973/dti-20251231.htm',
    ('AESI', 1984060): 'https://www.sec.gov/Archives/edgar/data/1984060/000119312526067145/aesi-20251231.htm',
}

EXPLANATIONS = {
    ('SLB', 87347): '부문 합계 366억4,800만 달러에는 디지털 사업 등의 부문 간 중복 인식이 있습니다. '
        '9억4,000만 달러를 제거한 연결 매출 357억800만 달러와 분모가 달라 부문 구성비를 계산하지 않습니다.',
    ('PUMP', 1680247): '네 부문 합계 12억7,004만8,000 달러에서 내부거래 89만 달러를 제거한 '
        '연결 매출은 12억6,915만8,000 달러입니다. 제거 전 부문을 외부 매출 구성비로 표시하지 않습니다.',
    ('FLOC', 2035149): '두 부문 합계 8억1,850만5,000 달러에서 부문 간 매출 5,878만6,000 달러를 제거한 '
        '연결 매출은 7억5,971만9,000 달러입니다. 제품·장비 임대와 고객 계약 매출의 범위도 구분합니다.',
    ('ACDC', 1881487): '부문 합계 24억9,210만 달러에서 순연결조정 5억5,030만 달러를 차감하면 '
        '연결 매출 19억4,180만 달러입니다. 내부 매출 제거 5억6,110만 달러와 외부 서비스 조정 '
        '+1,080만 달러가 함께 있어 제거 전 부문 구성비를 계산하지 않습니다.',
    ('DTI', 1884516): '지역 부문 합계 1억7,204만5,000 달러에는 내부거래가 포함됩니다. 공시의 제거액 '
        '1,242만 달러와 연결 매출 1억5,962만6,000 달러 사이에는 천 달러 표시 단위의 반올림 차이 '
        '1,000달러가 있습니다. 원문 값을 바꾸거나 외부 매출 구성비로 계산하지 않습니다.',
}


def reviewed(row, symbol, cik):
    return (row['start'] == '2025-01-01' and row['end'] == '2025-12-31'
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def dimensions(pairs, symbol, cik):
    if (symbol, cik) == ('DTI', 1884516) and pairs == [
            ('srt:ProductOrServiceAxis', 'us-gaap:ProductMember')]:
        return 'product', 'us-gaap:ProductMember'
    if (symbol, cik) == ('AESI', 1984060) and pairs == [
            ('srt:ProductOrServiceAxis', 'aesi:RentalRevenueMember')]:
        return 'revenue_type', 'aesi:RentalRevenueMember'
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def presentation_group(row, symbol, cik):
    """Normalize the same reviewed facts in preexisting local caches."""
    if reviewed(row, symbol, cik):
        if (symbol, cik, row['member']) == ('DTI', 1884516, 'us-gaap:ProductMember'):
            return 'product'
        if (symbol, cik, row['member']) == ('AESI', 1984060, 'aesi:RentalRevenueMember'):
            return 'revenue_type'
    return row['group']


def canonical_revenue(rows, symbol):
    # Minimum-purchase shortfall is already in the revenue categories, not an
    # additional product. Keep the separately edited contract note instead.
    return [row for row in rows if not (
        (symbol, row['member']) == ('AESI', 'aesi:ShortfallRevenuesMember')
        and row['metric'] == 'us-gaap:Revenues' and reviewed(row, symbol, 1984060))]


def annotate(rows, symbol, cik):
    explanation = EXPLANATIONS.get((symbol, cik))
    if explanation:
        for row in rows:
            if row['group'] != 'segment' or row['member'] not in SEGMENTS[(symbol, cik)]:
                continue
            if reviewed(row, symbol, cik):
                row.update(share_exclusion=explanation, includes_intersegment=True, total=None)
            else:
                # Recognizing a label does not establish the accounting basis
                # in another report. Do not reuse the FY2025 elimination.
                row.update(share_exclusion='이 기간·공시의 영업 부문 매출과 연결 외부 매출의 포함 관계를 '
                    '별도로 확인해야 하므로 비중을 산출하지 않습니다.', total=None)
    return rows
