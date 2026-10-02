"""Exact equipment, drilling and water-service filing coordinates.

External segment sales, gross segment sales and party-qualified sales have
different bases. Only the explicitly reviewed issuer/axis pairs are supported.
"""

COORDINATES, LABELS = {}, {}
SEGMENTS = {
    ('FTI', 1681459): {'fti:SubseaMember': '해저 개발 · Subsea',
                     'fti:SurfaceTechnologiesMember': '지상 생산·압력 제어'},
    ('NOV', 1021860): {'nov:EnergyProductsAndServicesMember': '에너지 제품·서비스',
                     'nov:EnergyEquipmentsMember': '에너지 장비'},
    ('TTI', 844965): {'tti:CompletionFluidsProductsDivisionMember': '완결 유체·화학 제품',
                    'tti:WaterFlowbackServicesMember': '물·flowback 서비스'},
    ('NBR', 1163739): {'nbr:USSegmentMember': '미국 시추',
        'nbr:InternationalExcludingCanadaMember': '해외 시추 · 캐나다 포함',
        'nbr:DrillingSolutionsMember': '시추 기술·서비스',
        'nbr:RigTechnologiesMember': '리그 기술·장비'},
    ('HP', 46765): {'hp:NorthAmericaSolutionsMember': '북미 시추',
        'hp:InternationalSolutionsSegmentMember': '해외 육상 시추',
        'hp:OffshoreGulfofMexicoMember': '해상 시추·운영 관리'},
    ('WFRD', 1603923): {'wfrd:DrillingandEvaluationMember': '시추·평가',
        'wfrd:WellConstructionAndCompletionMember': '유정 건설·완결',
        'wfrd:ProductionAndInterventionMember': '생산·유정 개입'},
    ('RES', 742278): {'res:TechnicalServiceMember': '현장 기술 서비스',
                    'res:SupportServicesMember': '장비 임대·지원 서비스'},
    ('RNGR', 1699039): {'rngr:HighSpecificationRigsMember': '고사양 유정 정비 리그',
        'rngr:WirelineServiceMember': '와이어라인',
        'rngr:ProcessingSolutionsAndAncillaryServicesMember': '처리·부대 서비스'},
}
for (_symbol, _cik), _mapping in SEGMENTS.items():
    for _member, _label in _mapping.items():
        COORDINATES[(_symbol, _cik, frozenset([
            ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
            ('us-gaap:StatementBusinessSegmentsAxis', _member),
        ]))] = ('segment', _member)
        LABELS[(_symbol, _cik, _member)] = _label

# Select's product axis contains actual external sales of its three divisions.
# The similarly named operating-segment axis includes internal sales instead.
WATER = {'wttr:WaterInfrastructureMember': '물 인프라 · 외부 매출',
         'wttr:WaterServicesMember': '현장 물 서비스 · 외부 매출',
         'wttr:ChemicaltechnologiesMember': '약품 · 외부 매출'}
for _member, _label in WATER.items():
    COORDINATES[('WTTR', 1693256, frozenset([
        ('srt:ProductOrServiceAxis', _member),
    ]))] = ('segment', _member)
    LABELS[('WTTR', 1693256, _member)] = _label

# Flotek directly reports sales for each segment and related/nonrelated party.
# Retain all three axes in four distinct leaves; do not invent a segment total.
for _segment, _label in [('ftk:ChemistryTechnologiesSegmentMember', '약품'),
                          ('ftk:DataAnalyticsSegmentMember', '데이터·발전')]:
    for _party, _party_label in [('us-gaap:RelatedPartyMember', '특수관계자 판매'),
                                 ('us-gaap:NonrelatedPartyMember', '제삼자 판매')]:
        _member = _segment + '/' + _party
        COORDINATES[('FTK', 928054, frozenset([
            ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
            ('us-gaap:StatementBusinessSegmentsAxis', _segment),
            ('us-gaap:RelatedPartyTransactionsByRelatedPartyAxis', _party),
        ]))] = ('segment', _member)
        LABELS[('FTK', 928054, _member)] = _label + ' · ' + _party_label

# NOV's subsegment breakouts include the separately tagged internal revenue.
NOV_CHILDREN = {
    'nov:EnergyProductsAndServicesMember': {
        'nov:CapitalEquipmentMember': '자본 장비',
        'nov:ServicesAndRentalMember': '서비스·임대',
        'nov:ProductSalesMember': '제품 판매',
        'nov:IntersegmentRevenueMember': '부문 간 내부 매출',
    },
    'nov:EnergyEquipmentsMember': {
        'nov:CapitalEquipmentMember': '자본 장비',
        'nov:AftermarketMember': '부품·수리·유지 서비스',
        'nov:IntersegmentRevenueMember': '부문 간 내부 매출',
    },
}
for _segment, _mapping in NOV_CHILDREN.items():
    for _child, _label in _mapping.items():
        _member = _child + '/' + _segment
        COORDINATES[('NOV', 1021860, frozenset([
            ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
            ('us-gaap:StatementBusinessSegmentsAxis', _segment),
            ('us-gaap:SubsegmentsAxis', _child),
        ]))] = ('segment', _member)
        LABELS[('NOV', 1021860, _member)] = _label

RES_PRODUCTS = {
    'res:TechnicalServiceMember': {
        'res:PressurePumpingMember': '수압파쇄·압력 펌핑',
        'res:DownholeToolsMember': '유정 내 도구', 'res:WirelineMember': '와이어라인',
        'res:CoiledTubingMember': '코일드 튜빙', 'res:CementingMember': '시멘팅',
        'res:NitrogenMember': '질소 서비스', 'res:SnubbingMember': 'snubbing · 압력하 관 삽입',
        'us-gaap:ProductAndServiceOtherMember': '기타 현장 기술 서비스',
    },
    'res:SupportServicesMember': {'res:RentalToolsMember': '도구 임대',
        'us-gaap:ProductAndServiceOtherMember': '기타 장비·지원 서비스'},
}
for _segment, _mapping in RES_PRODUCTS.items():
    for _product, _label in _mapping.items():
        _member = _product + '/' + _segment
        COORDINATES[('RES', 742278, frozenset([
            ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
            ('us-gaap:StatementBusinessSegmentsAxis', _segment),
            ('srt:ProductOrServiceAxis', _product),
        ]))] = ('product', _member)
        LABELS[('RES', 742278, _member)] = _label

for _symbol, _cik, _mapping in [
    ('FTI', 1681459, {'country:AE': '아랍에미리트', 'country:AO': '앙골라',
        'country:AU': '호주', 'country:BR': '브라질', 'country:GY': '가이아나',
        'country:ID': '인도네시아', 'country:IL': '이스라엘', 'country:MZ': '모잠비크',
        'country:NG': '나이지리아', 'country:NO': '노르웨이', 'country:SA': '사우디아라비아',
        'country:SR': '수리남', 'fti:AllOtherCountriesmemberMember': '기타 국가'}),
    ('NOV', 1021860, {'country:BR': '브라질', 'country:NO': '노르웨이',
        'nov:RentalMember': '임대', 'us-gaap:RoyaltyMember': '로열티 · 부분 자료'}),
    ('WHD', 1699136, {'whd:PressureControlSegmentMember': '압력 제어 · 외부 매출',
        'whd:SpoolableTechnologiesMember': 'spoolable 관 · FlexSteel',
        'whd:RentalRevenueMember': '임대', 'us-gaap:ProductAndServiceOtherMember': '현장·기타 서비스'}),
    ('WTTR', 1693256, {'wttr:ChemicalProductSalesRevenueMember': '약품 판매 · 내부거래 포함',
        'wttr:FluidHaulingMember': '물·유체 차량 운송', 'wttr:FluidsDisposalMember': '유체 처분',
        'wttr:WaterTransferAndMonitoringMember': '물 이송·감시',
        'wttr:AccommodationsAndRentalsRevenueMember': '숙박·임대',
        'wttr:WellTestingAndFlowbackMember': '유정 시험·flowback',
        'wttr:WaterContainmentMember': '물 임시 저장', 'wttr:SolidsManagementMember': '고형물 처리',
        'wttr:WaterRecyclingAndReuseMember': '물 재활용·재사용',
        'wttr:PipelinesAndLogisticsMember': '파이프라인·물류',
        'wttr:BakkenMember': 'Bakken', 'wttr:EagleFordMember': 'Eagle Ford',
        'wttr:HaynesvilleE.TexasMember': 'Haynesville·동부 Texas',
        'wttr:MarcellusUticaMember': 'Marcellus·Utica', 'wttr:MidconMember': 'MidContinent',
        'wttr:PermianBasinMember': 'Permian', 'wttr:RockiesMember': 'Rockies'}),
    ('FTK', 928054, {'ftk:RentalMember': '장비 임대', 'country:AE': '아랍에미리트'}),
    ('NINE', 1532286, {'nine:CementMember': '시멘팅', 'nine:CoiledTubingMember': '코일드 튜빙',
        'nine:WirelineMember': '와이어라인', 'nine:ToolsMember': '도구 판매',
        'nine:ToolRevenueMember': '도구 판매 소계', 'nine:ServiceRevenueMember': '서비스 소계'}),
    ('NBR', 1163739, {'country:SA': '사우디아라비아 · 부분 지역 자료'}),
    ('HP', 46765, {'hp:ReimbursementsOfOutOfPocketExpensesMember': '고객 비용 상환 · 부분 매출',
        'country:AR': '아르헨티나', 'country:AZ': '아제르바이잔', 'country:BH': '바레인',
        'country:CO': '콜롬비아', 'country:KW': '쿠웨이트', 'country:NO': '노르웨이',
        'country:OM': '오만', 'country:SA': '사우디아라비아', 'hp:OtherForeignMember': '기타 해외'}),
    ('WFRD', 1603923, {'srt:LatinAmericaMember': '중남미',
        'wfrd:EuropeSubSaharaAfricaRussiaMember': '유럽·사하라 이남·러시아',
        'wfrd:MiddleEastNorthAfricaAsiaMember': '중동·북아프리카·아시아',
        'wfrd:InternationalExcludingNorthAmericaCountriesMember': '북미 외 소계',
        'us-gaap:MaterialReconcilingItemsMember': '기타 사업 · 보고 부문 외'}),
    ('RNGR', 1699039, {'rngr:WirelineServicesMember': '와이어라인'}),
]:
    for _member, _label in _mapping.items():
        LABELS[(_symbol, _cik, _member)] = _label


def dimensions(pairs, symbol, cik):
    if (symbol, cik) == ('WFRD', 1603923) and pairs == [
            ('srt:ConsolidationItemsAxis', 'us-gaap:MaterialReconcilingItemsMember')]:
        return 'segment', 'us-gaap:MaterialReconcilingItemsMember'
    if (symbol, cik) == ('RNGR', 1699039) and len(pairs) == 1:
        axis, member = pairs[0]
        canonical = {'rngr:WirelineServicesMember': 'rngr:WirelineServiceMember'}.get(member, member)
        if axis == 'srt:ProductOrServiceAxis' and canonical in SEGMENTS[(symbol, cik)]:
            return 'segment', canonical
    types = {('NOV', 1021860): {'nov:RentalMember'},
             ('WHD', 1699136): {'whd:RentalRevenueMember', 'us-gaap:ProductAndServiceOtherMember'},
             ('FTK', 928054): {'ftk:RentalMember'}}
    if (len(pairs) == 1 and pairs[0][0] == 'srt:ProductOrServiceAxis'
            and pairs[0][1] in types.get((symbol, cik), set())):
        return 'revenue_type', pairs[0][1]
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def presentation_group(row, symbol, cik):
    member = row['member']
    if (symbol, cik) == ('WTTR', 1693256) and row['group'] == 'product' and member in WATER:
        return 'segment'
    types = {('NOV', 1021860): {'nov:RentalMember'},
             ('WHD', 1699136): {'whd:RentalRevenueMember', 'us-gaap:ProductAndServiceOtherMember'},
             ('FTK', 928054): {'ftk:RentalMember'}}
    if member in types.get((symbol, cik), set()):
        return 'revenue_type'
    if (symbol, cik) == ('RNGR', 1699039):
        canonical = {'rngr:WirelineServicesMember': 'rngr:WirelineServiceMember'}.get(member, member)
        if canonical in SEGMENTS[(symbol, cik)]:
            row['member'] = canonical
            return 'segment'
    return row['group']


HIERARCHIES = {
    ('NOV', 1021860, 'segment'): {
        parent: [child + '/' + parent for child in children]
        for parent, children in NOV_CHILDREN.items()
    },
    ('NINE', 1532286, 'product'): {'nine:ServiceRevenueMember': [
        'nine:CementMember', 'nine:CoiledTubingMember', 'nine:WirelineMember']},
    ('WFRD', 1603923, 'geography'): {'wfrd:InternationalExcludingNorthAmericaCountriesMember': [
        'srt:LatinAmericaMember', 'wfrd:EuropeSubSaharaAfricaRussiaMember',
        'wfrd:MiddleEastNorthAfricaAsiaMember']},
}


def reviewed(row, symbol, cik):
    start = '2024-10-01' if symbol == 'HP' else '2025-01-01'
    end = '2025-09-30' if symbol == 'HP' else '2025-12-31'
    return (row['start'] == start and row['end'] == end
            and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def annotate(rows, symbol, cik):
    for row in rows:
        gross = ((symbol, cik, row['group']) in {
            ('NOV', 1021860, 'segment'), ('NBR', 1163739, 'segment'),
            ('WTTR', 1693256, 'product')})
        if gross:
            row['total'] = None
            if reviewed(row, symbol, cik):
                row['includes_intersegment'] = True
                row['share_exclusion'] = {
                    'NOV': '두 부문 합계 8,911,000,000달러에서 내부거래 167,000,000달러를 제거한 '
                        '연결 매출은 8,744,000,000달러입니다. 제거 전 부문 비중은 계산하지 않습니다.',
                    'NBR': '네 부문 합계 3,241,728,000달러에서 내부거래 57,035,000달러를 제거한 '
                        '연결 영업매출은 3,184,693,000달러입니다. 제거 전 부문 비중은 계산하지 않습니다.',
                    'WTTR': '상세 서비스 10개 항목 합계는 1,420,376,000달러입니다. '
                        '공시의 내부거래 제거·기타 서비스 조정 −13,032,000달러를 반영하면 '
                        '1,407,344,000달러입니다. 총액 기준 부문 표와는 조정 범위가 달라 '
                        '서로 합산하거나 외부 매출 구성비로 표시하지 않습니다.',
                }[symbol]
            else:
                row['includes_intersegment'] = False
                row['share_exclusion'] = '이 표의 내부거래·연결조정 기준은 해당 문서에서 별도로 확인해야 하므로 비중을 계산하지 않습니다.'
        if (symbol, cik, row['group']) == ('HP', 46765, 'segment'):
            row['total'] = None
            row['share_exclusion'] = '세 보고 부문은 기타 사업을 포함한 연결 매출 전체가 아닙니다. 기타·연결조정 범위와 비교하기 전에는 전체 구성비를 계산하지 않습니다.'
        if (symbol, cik, row['group']) == ('FTI', 1681459, 'revenue_type') and reviewed(row, symbol, cik):
            row['share_exclusion'] = ('제품·서비스 합계는 고객 계약 매출 9,640,500,000달러이며 '
                '연결 매출 9,932,600,000달러 전체와 범위가 다릅니다. 전체 매출 구성비로 표시하지 않습니다.')
            row['total'] = None
        if ((symbol, cik, row['group'], row['member']) ==
                ('FTK', 928054, 'geography', 'us-gaap:NonUsMember') and reviewed(row, symbol, cik)):
            row['label'] = '기타 해외 · UAE 제외'


def canonical(rows, symbol, cik):
    result = []
    for row in rows:
        if reviewed(row, symbol, cik):
            if (symbol == 'NOV' and row['member'] == 'us-gaap:RoyaltyMember'
                    and row['metric'] == 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'):
                # Already included in the complete product/service/rental view.
                continue
            if (symbol == 'NINE' and row['member'] == 'nine:ToolRevenueMember'
                    and any(other['member'] == 'nine:ToolsMember'
                            and all(other[k] == row[k] for k in ('group', 'value', 'unit', 'start', 'end', 'metric'))
                            and other['source']['url'].split('#')[0] == row['source']['url'].split('#')[0]
                            for other in rows)):
                continue
        result.append(row)
    return result

DOCUMENTS = {
    ('NOV', 1021860): 'https://www.sec.gov/Archives/edgar/data/1021860/000119312526048350/nov-20251231.htm',
    ('NBR', 1163739): 'https://www.sec.gov/Archives/edgar/data/1163739/000110465926014997/nbr-20251231x10k.htm',
    ('WTTR', 1693256): 'https://www.sec.gov/Archives/edgar/data/1693256/000110465926017085/wttr-20251231x10k.htm',
    ('HP', 46765): 'https://www.sec.gov/Archives/edgar/data/46765/000004676525000071/hp-20250930.htm',
    ('NINE', 1532286): 'https://www.sec.gov/Archives/edgar/data/1532286/000153228626000005/nine-20251231.htm',
    ('FTI', 1681459): 'https://www.sec.gov/Archives/edgar/data/1681459/000168145926000010/fti-20251231.htm',
    ('WHD', 1699136): 'https://www.sec.gov/Archives/edgar/data/1699136/000162828026012377/whd-20251231.htm',
    ('FTK', 928054): 'https://www.sec.gov/Archives/edgar/data/928054/000092805426000020/ftk-20251231.htm',
}
