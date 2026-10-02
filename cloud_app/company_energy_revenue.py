"""Exact, issuer-bound coordinates checked in FY2025 energy segment tables.

Chevron reports external sales by both segment and geography. Retain both actual
XBRL member names in a composite key; never silently drop a geographic dimension.
Valero's product facts are qualified by the associated reported segment.
"""
from . import company_energy_provider_revenue as providers
from . import company_energy_equipment_revenue as equipment
from . import company_energy_major_revenue as majors

COORDINATES = {**providers.COORDINATES, **equipment.COORDINATES, **majors.COORDINATES}
LABELS = {**providers.LABELS, **equipment.LABELS, **majors.LABELS}

for _segment, _label in [('Upstream', '상류 · 탐사·생산'), ('Downstream', '하류 · 정제·판매')]:
    for _region, _region_label in [('country:US', '미국'), ('us-gaap:NonUsMember', '미국 외')]:
        _member = f'cvx:{_segment}SegmentMember'
        _combined = _member + '/' + _region
        COORDINATES[('CVX', 93410, frozenset([
            ('us-gaap:StatementBusinessSegmentsAxis', _member),
            ('srt:StatementGeographicalAxis', _region),
        ]))] = ('segment', _combined)
        LABELS[('CVX', 93410, _combined)] = _label + ' · ' + _region_label

for _segment, _members in {
    'Refining': ['vlo:GasolineAndBlendstocksMember', 'vlo:DistillatesMember', 'us-gaap:ManufacturedProductOtherMember'],
    'RenewableDiesel': ['vlo:RenewableDieselProductMember', 'vlo:RenewableNaphthaProductMember', 'vlo:NeatSAFMember'],
    'Ethanol': ['vlo:EthanolProductMember', 'vlo:DistillersGrainsMember'],
}.items():
    for _member in _members:
        COORDINATES[('VLO', 1035002, frozenset([
            ('srt:ProductOrServiceAxis', _member),
            ('us-gaap:StatementBusinessSegmentsAxis', f'vlo:{_segment}Member'),
        ]))] = ('product', _member)

for _symbol, _cik, _mapping in [
    ('CVX', 93410, {'us-gaap:ReportableSegmentAggregationBeforeOtherOperatingSegmentMember':'상·하류 사업 합계'}),
    ('COP', 1163165, {
        'cop:AlaskaSegmentMember':'알래스카', 'cop:LowerFortyEightSegmentMember':'미국 본토 48개 주',
        'cop:CanadaOperatingSegmentMember':'캐나다', 'cop:EuropeMiddleEastAndNorthAfricaSegmentMember':'유럽·중동·북아프리카',
        'cop:AsiaPacificOperatingSegmentMember':'아시아·태평양', 'cop:CorporateSegmentMember':'본사·기타',
        'cop:TotalSegmentsMember':'영업 부문 합계',
    }),
    ('VLO', 1035002, {
        'vlo:RefiningMember':'정유', 'vlo:RenewableDieselMember':'재생 디젤', 'vlo:EthanolMember':'에탄올',
        'vlo:GasolineAndBlendstocksMember':'휘발유·혼합 기재', 'vlo:DistillatesMember':'경유·항공유 등 중간유분',
        'us-gaap:ManufacturedProductOtherMember':'기타 정유 제품', 'vlo:RenewableDieselProductMember':'재생 디젤 제품',
        'vlo:RenewableNaphthaProductMember':'재생 나프타', 'vlo:NeatSAFMember':'미혼합 지속가능항공유',
        'vlo:EthanolProductMember':'에탄올 제품', 'vlo:DistillersGrainsMember':'증류곡물 부산물',
        'country:CA':'캐나다', 'vlo:UnitedKingdomAndIrelandMember':'영국·아일랜드',
        'vlo:MexicoAndPeruMember':'멕시코·페루', 'vlo:OtherCountriesMember':'기타 국가',
    }),
    ('MPC', 1510295, {
        'mpc:RefiningAndMarketingMember':'정유·판매', 'mpc:MidstreamMember':'물류·가스처리',
        'mpc:RenewableDieselMember':'재생 디젤', 'us-gaap:CorporateNonSegmentMember':'본사·기타',
    }),
    ('PSX', 1534701, {
        'psx:MarketingSpecialitySegmentMember':'판매·특수제품', 'psx:MidstreamSegmentMember':'물류·가스처리',
        'psx:RefiningSegmentMember':'정유', 'psx:RenewableFuelsMember':'재생연료',
        'us-gaap:CorporateNonSegmentMember':'본사·기타',
        'psx:OtherProductLineMember':'서비스·기타',
        'psx:RefinedPetroleumProductsAndRenewableFuelsMember':'정유제품·재생연료',
        'srt:CrudeOilMember':'매입 원유 재판매', 'srt:NaturalGasLiquidsReservesMember':'NGL·천연가스',
        'country:DE':'독일', 'country:GB':'영국', 'psx:OtherGeographicalAreasMember':'기타 국가',
    }),
    ('DINO', 1915657, {
        'dino:AsphaltFuelOilAndOtherProductsMember':'아스팔트·연료유·기타 제품',
        'dino:LubricantsAndSpecialtyProductsMember':'윤활유·특수제품',
        'dino:RefinedProductMember':'정유제품 매출 소계',
        'dino:RenewableIdentificationNumbersRINsMember':'RIN 매각 · 기타 매출의 일부',
        'dino:TransportationAndLogisticServicesMember':'운송·물류 서비스',
        'dino:TransportationFuelsMember':'수송용 연료', 'srt:CrudeOilMember':'잉여 매입 원유 재판매',
        'us-gaap:ProductAndServiceOtherMember':'기타 매출',
        'dino:LubricantsAndSpecialtiesSegmentMember':'윤활유·특수제품',
        'dino:MarketingSegmentMember':'브랜드 연료 판매', 'dino:MidstreamSegmentMember':'물류',
        'dino:RefiningSegmentMember':'정유', 'dino:RenewablesSegmentMember':'재생연료',
    }),
    ('WMB', 107263, {
        'wmb:NonRegulatedServiceCommodityConsiderationMember':'집하·처리 등 · 현물 상품 대가',
        'wmb:NonRegulatedServiceMonetaryConsiderationMember':'집하·처리 등 · 현금 대가',
        'wmb:OtherServiceMember':'기타 서비스', 'wmb:RegulatedServiceMember':'규제 가스 운송·저장',
    }),
    ('KMI', 1506307, {
        'kmi:FeebasedservicesMember':'사용량 등 기반 서비스', 'kmi:FirmServicesMember':'확정 용량 서비스',
        'kmi:NaturalGasSalesMember':'천연가스 판매', 'kmi:OtherCommodityMember':'기타 상품 판매',
        'kmi:ProductOtherThanNaturalGasMember':'천연가스 외 제품 판매',
        'kmi:Co2Member':'CO₂·유전·재생가스', 'kmi:NaturalGasPipelinesMember':'천연가스 파이프라인',
        'kmi:ProductsPipelinesMember':'제품 파이프라인', 'kmi:TerminalsMember':'터미널', 'country:MX':'멕시코',
    }),
    ('TRGP', 1389170, {
        'srt:NaturalGasLiquidsReservesMember':'NGL 판매', 'srt:NaturalGasReservesMember':'천연가스 판매',
        'trgp:GatheringAndProcessingFeesMember':'집하·처리 수수료',
        'trgp:MidstreamServicesOtherMember':'기타 중류 서비스',
        'trgp:NGLTransportationFractionationAndServicesMember':'NGL 운송·분별·서비스',
        'trgp:StorageTerminalingAndExportMember':'저장·터미널·수출',
        'us-gaap:OilAndCondensateMember':'원유·콘덴세이트 판매',
        'trgp:GatheringAndProcessingMember':'집하·처리 · 외부 매출',
        'trgp:LogisticsAndTransportationMember':'물류·운송 · 외부 매출',
    }),
    ('OKE', 1039684, {
        'oke:CommoditySalesMember':'상품 판매 소계',
        'oke:ExchangeServicesAndNaturalGasGatheringAndProcessingRevenueMember':'교환·집하·처리',
        'oke:LiquidsCommodityMember':'액체 상품 판매', 'oke:OtherMember':'기타',
        'oke:ResidueNaturalGasSalesMember':'잔여 천연가스 판매',
        'oke:ServicesMember':'서비스·기타 소계',
        'oke:TransportationandStorageRevenueMember':'운송·저장',
    }),
    ('LNG', 3570, {
        'lng:LiquefiedNaturalGasMember':'LNG 판매 · 고객 계약',
        'lng:LiquefiedNaturalGasProcuredFromThirdPartiesMember':'외부 조달 LNG 재판매 · LNG 판매에 포함',
        'lng:RegasificationServiceMember':'재기화 서비스',
        'us-gaap:ProductAndServiceOtherMember':'기타 고객 계약 매출',
    }),
]:
    for _member, _label in _mapping.items():
        LABELS[(_symbol, _cik, _member)] = _label

HIERARCHIES = {
    ('CVX', 93410, 'segment'): {
        'us-gaap:ReportableSegmentAggregationBeforeOtherOperatingSegmentMember': [
            segment+'/'+region for segment in ['cvx:UpstreamSegmentMember','cvx:DownstreamSegmentMember']
            for region in ['country:US','us-gaap:NonUsMember']]},
    ('COP', 1163165, 'segment'): {
        'cop:TotalSegmentsMember': ['cop:AlaskaSegmentMember','cop:LowerFortyEightSegmentMember',
            'cop:CanadaOperatingSegmentMember','cop:EuropeMiddleEastAndNorthAfricaSegmentMember',
            'cop:AsiaPacificOperatingSegmentMember']},
    ('DINO', 1915657, 'product'): {
        'dino:RefinedProductMember': ['dino:TransportationFuelsMember',
            'dino:LubricantsAndSpecialtyProductsMember', 'dino:AsphaltFuelOilAndOtherProductsMember']},
    ('OKE', 1039684, 'product'): {
        'oke:CommoditySalesMember': ['oke:LiquidsCommodityMember', 'oke:ResidueNaturalGasSalesMember'],
        'oke:ServicesMember': ['oke:ExchangeServicesAndNaturalGasGatheringAndProcessingRevenueMember',
                             'oke:TransportationandStorageRevenueMember', 'oke:OtherMember']},
}
HIERARCHIES.update(equipment.HIERARCHIES)

# Targa's external segment rows use this exact two-axis coordinate. Its nearby
# MaterialReconcilingItems and IntersegmentElimination rows must not be admitted.
for _member in ('trgp:GatheringAndProcessingMember', 'trgp:LogisticsAndTransportationMember'):
    COORDINATES[('TRGP', 1389170, frozenset([
        ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', _member),
    ]))] = ('segment', _member)

# Energy Transfer's segment table explicitly distinguishes external customers
# from intersegment transactions on a third axis. Admit only external rows.
for _member, _label in {
    'et:IntrastateTransportationAndStorageMember':'주내 가스 운송·저장 · 외부 매출',
    'et:InterstateTransportationAndStorageMember':'주간 가스 운송·저장 · 외부 매출',
    'et:MidstreamMember':'생산지 집하·처리 · 외부 매출',
    'et:NGLandrefinedproductstransportationandservicesMember':'NGL·정유제품 물류 · 외부 매출',
    'et:CrudeoiltransportationandservicesMember':'원유 물류 · 외부 매출',
    'et:InvestmentInSunocoLPMember':'Sunoco 연결 사업 · 외부 매출',
    'et:InvestmentInUSACMember':'압축 서비스 · 외부 매출',
    'us-gaap:AllOtherSegmentsMember':'기타 연결 사업 · 외부 매출',
}.items():
    COORDINATES[('ET', 1276187, frozenset([
        ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:RelatedPartyTransactionsByRelatedPartyAxis', 'et:ExternalCustomersMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', _member),
    ]))] = ('segment', _member)
    LABELS[('ET', 1276187, _member)] = _label

for _member, _label in {
    'hesm:GatheringMember':'가스·원유·생산수 집하',
    'hesm:ProcessingAndStorageMember':'가스 처리·NGL 분별·저장',
    'hesm:TerminalingAndExportMember':'원유 터미널·출하',
}.items():
    COORDINATES[('HESM', 1789832, frozenset([
        ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', _member),
    ]))] = ('segment', _member)
    LABELS[('HESM', 1789832, _member)] = _label

for _symbol, _cik, _mapping in [
    ('EPD', 1061219, {
        'epd:NglPipelinesAndServicesMember':'NGL 파이프라인·서비스 · 내부거래 제거 후',
        'epd:OnshoreCrudeOilPipelinesAndServicesMember':'원유 파이프라인·서비스 · 내부거래 제거 후',
        'epd:OnshoreNaturalGasPipelinesAndServicesMember':'천연가스 파이프라인·서비스 · 내부거래 제거 후',
        'epd:PetrochemicalAndRefinedProductsServicesMember':'석유화학·정유제품 서비스 · 내부거래 제거 후',
    }),
    ('ET', 1276187, {
        'et:NGLsalesMember':'NGL 판매', 'et:NaturalgassalesMember':'천연가스 판매',
        'us-gaap:NaturalGasMidstreamMember':'운송·집하·처리 등 서비스',
        'us-gaap:OilAndGasMember':'원유 판매',
        'us-gaap:OilAndGasRefiningAndMarketingMember':'정유제품 판매',
        'us-gaap:ProductAndServiceOtherMember':'기타 상품·서비스',
    }),
    ('MPLX', 1552000, {
        'mplx:CrudeOilAndProductsLogisticsMember':'원유·정유제품 물류 · 고객 계약',
        'mplx:NaturalGasAndNGLServicesMember':'천연가스·NGL 서비스 · 고객 계약',
    }),
    ('WES', 1423902, {
        'wes:ServiceFeeBasedMember':'고정 수수료 기반 서비스',
        'wes:ServiceProductBasedMember':'상품 가격 기반 서비스',
    }),
    ('HESM', 1789832, {
        'hesm:AffiliateServicesMember':'관계사 서비스 · 고객 계약',
        'hesm:ThirdPartyServicesMember':'제3자 서비스 · 고객 계약',
    }),
]:
    for _member, _label in _mapping.items():
        LABELS[(_symbol, _cik, _member)] = _label


for _party, _label in [('us-gaap:NonrelatedPartyMember', 'LNG · 제3자 판매'),
                       ('us-gaap:SubsidiaryOfCommonParentMember', 'LNG · Cheniere 계열 판매')]:
    _member = 'cqp:LiquefiedNaturalGasMember/' + _party
    COORDINATES[('CQP', 1383650, frozenset([
        ('srt:ProductOrServiceAxis', 'cqp:LiquefiedNaturalGasMember'),
        ('us-gaap:RelatedPartyTransactionsByRelatedPartyAxis', _party),
    ]))] = ('product', _member)
    LABELS[('CQP', 1383650, _member)] = _label

for _symbol, _cik, _mapping in [
    ('DTM', 1842022, {'dtm:GatheringSegmentMember': '생산지 집하', 'dtm:PipelineSegmentMember': '배관·저장'}),
    ('AM', 1623925, {
        'am:NaturalGasGatheringTransportationMarketingAndProcessingAffiliateMember': 'Antero 집하·압축 · 고객 관계 상각 전',
        'am:NaturalGasWaterHandlingAndTreatmentAffiliateMember': 'Antero 물 서비스 · 고객 관계 상각 전',
        'am:NaturalGasWaterHandlingAndTreatmentMember': '제3자 물 서비스 · 고객 관계 상각 전',
    }),
    ('KNTK', 1692787, {
        'apa:GatheringAndProcessingServicesMember': '집하·처리 서비스',
        'apa:MinimumVolumeCommitmentsMember': '최소 물량 미달 대가 · 서비스 매출에 포함',
        'apa:NaturalGasNGLsAndCondensateSalesMember': '가스·NGL·콘덴세이트 판매',
        'apa:ProductAndServiceMember': '제품·서비스 매출 소계',
    }),
    ('CQP', 1383650, {'cqp:RegasificationServiceMember': '재기화 서비스',
                    'cqp:LiquefiedNaturalGasMember': 'LNG 매출 소계'}),
    ('SUN', 1552275, {'sun:LeaseRevenueMember': '임대', 'sun:SalesRevenueMember': '연료·상품 판매',
                     'sun:ServiceRevenueMember': '물류·기타 서비스', 'country:CA': '캐나다',
                     'country:US': '미국', 'sun:ForeignMember': '미국·캐나다 외'}),
    ('USAC', 1522727, {'usac:ContractOperationsRevenueMember': '계약 압축 서비스',
                      'usac:RetailPartsAndServicesMember': '부품·정비 서비스'}),
    ('KGS', 1767042, {'kgs:ContractServicesMember': '계약 압축 서비스 · 2025년 부문',
                     'kgs:OtherServicesMember': '기타 서비스 · 2025년 부문'}),
    ('AROC', 1389050, {'aroc:AftermarketServicesSegmentMember': '고객 소유 장비 · 정비·부품',
                      'aroc:ContractOperationsSegmentMember': '회사 소유 장비 · 계약 운영'}),
]:
    for _member, _label in _mapping.items():
        LABELS[(_symbol, _cik, _member)] = _label

HIERARCHIES[('KNTK', 1692787, 'product')] = {
    'apa:ProductAndServiceMember': ['apa:GatheringAndProcessingServicesMember',
                                  'apa:NaturalGasNGLsAndCondensateSalesMember']}

# FY2025 E&P tables distinguish own production, resale and gross segment sales.
# Every multi-axis coordinate is an exact issuer/CIK pair, not a generic fallback.
for _product, _label in [('srt:OilReservesMember', '원유'), ('dvn:GasMember', '천연가스'),
                         ('dvn:NGLMember', 'NGL')]:
    for _location, _prefix in [('dvn:OilGasAndNGLSalesMember', '자체 생산'),
                               ('dvn:MarketingAndMidstreamRevenuesMember', '판매·중류')]:
        _member = _product + '/' + _location
        COORDINATES[('DVN', 1090012, frozenset([
            ('srt:ProductOrServiceAxis', _product),
            ('us-gaap:IncomeStatementLocationAxis', _location),
        ]))] = ('product', _member)
        LABELS[('DVN', 1090012, _member)] = _prefix + ' · ' + _label

for _product, _label in [('srt:OilReservesMember', '원유'),
                         ('srt:NaturalGasLiquidsReservesMember', 'NGL'),
                         ('srt:NaturalGasReservesMember', '천연가스'),
                         ('us-gaap:ProductAndServiceOtherMember', '기타')]:
    _member = _product + '/oxy:OilAndGasSegmentMember'
    COORDINATES[('OXY', 797468, frozenset([
        ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('srt:ProductOrServiceAxis', _product),
        ('us-gaap:StatementBusinessSegmentsAxis', 'oxy:OilAndGasSegmentMember'),
    ]))] = ('product', _member)
    LABELS[('OXY', 797468, _member)] = '탐사·생산 · ' + _label

for _segment in ('oxy:OilAndGasSegmentMember', 'oxy:MidstreamAndMarketingMember'):
    # These are gross net-sales rows; eliminations remain a separate adjustment.
    COORDINATES[('OXY', 797468, frozenset([
        ('srt:ConsolidationItemsAxis', 'oxy:OtherOperatingSegmentsAndIntersegmentEliminationsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', _segment),
    ]))] = ('segment', _segment)

for _segment in ('eqt:UpstreamSegmentMember', 'eqt:GatheringSegmentMember', 'eqt:TransmissionSegmentMember'):
    COORDINATES[('EQT', 33213, frozenset([
        ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', _segment),
    ]))] = ('segment', _segment)
for _product in ('eqt:NaturalGasSalesMember', 'eqt:NGLsSalesMember', 'eqt:OilSalesMember'):
    COORDINATES[('EQT', 33213, frozenset([
        ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('srt:ProductOrServiceAxis', _product),
        ('us-gaap:StatementBusinessSegmentsAxis', 'eqt:UpstreamSegmentMember'),
    ]))] = ('product', _product)

for _symbol, _cik, _mapping in [
    ('EOG', 821189, {'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'srt:NaturalGasLiquidsReservesMember': 'NGL', 'us-gaap:NaturalGasProductionMember': '천연가스',
        'us-gaap:NaturalGasGatheringTransportationMarketingAndProcessingMember': '집하·처리·재판매',
        'eog:UnitedStatesOfAmericaSegmentMember': '미국 · 영업매출·기타',
        'eog:TrinidadMember': '트리니다드 · 영업매출·기타', 'eog:OtherInternationalMember': '기타 해외 · 영업매출·기타'}),
    ('FANG', 1539838, {'fang:OilExplorationandProductionMember': '자체 생산 · 원유',
        'us-gaap:NaturalGasProductionMember': '자체 생산 · 천연가스',
        'fang:NaturalGasLiquidsProductionMember': '자체 생산 · NGL',
        'fang:OilNaturalGasAndNaturalGasLiquidMember': '자체 생산품 판매 소계',
        'fang:OilPurchasedMember': '매입 원유 재판매'}),
    ('OXY', 797468, {'oxy:OilAndGasSegmentMember': '탐사·생산 · 내부거래 제거 전',
        'oxy:MidstreamAndMarketingMember': '중류·판매 · 내부거래 제거 전',
        'oxy:OutsideOfNorthAmericaMember': '북미 외 · 고객 계약 매출'}),
    ('DVN', 1090012, {'dvn:OilGasAndNGLSalesMember': '자체 생산품 판매 소계',
        'dvn:MarketingAndMidstreamRevenuesMember': '매입 상품 판매·중류 소계'}),
    ('EQT', 33213, {'eqt:UpstreamSegmentMember': '탐사·생산 · 내부거래 제거 전',
        'eqt:GatheringSegmentMember': '집하 · 내부거래 제거 전',
        'eqt:TransmissionSegmentMember': '간선 수송 · 내부거래 제거 전',
        'eqt:NaturalGasSalesMember': '자체 생산 · 천연가스', 'eqt:NGLsSalesMember': '자체 생산 · NGL',
        'eqt:OilSalesMember': '자체 생산 · 원유',
        'eqt:SalesOfNaturalGasNGLsAndOilAtProductionMember': '자체 생산품 판매 소계',
        'eqt:RevenuesFromContractWithCustomersMember': '고객 계약 매출 소계'}),
    ('EXE', 895126, {'us-gaap:OilAndGasMember': '자체 생산품 판매 소계',
        'us-gaap:NaturalGasGatheringTransportationMarketingAndProcessingMember': '외부 상품 재판매 소계',
        'exe:NaturalGasSalesMember': '자체 생산 · 천연가스', 'exe:OilSalesMember': '자체 생산 · 원유',
        'exe:NaturalGasLiquidsSalesMember': '자체 생산 · NGL',
        'exe:NaturalGasMarketingSalesMember': '재판매 · 천연가스', 'exe:OilMarketingSalesMember': '재판매 · 원유',
        'exe:NaturalGasLiquidsMarketingSalesMember': '재판매 · NGL'}),
    ('AR', 1433270, {'us-gaap:NaturalGasProductionMember': '천연가스 판매',
        'ar:NaturalGasLiquidsSalesMember': 'NGL 판매', 'us-gaap:OilAndCondensateMember': '원유·콘덴세이트 판매',
        'ar:MarketingsMember': '판매·수송 용량 활용',
        'ar:CommodityDerivativeFairValueGainsLossesMember': '파생상품 공정가치 손익',
        'ar:AmortizationOfDeferredRevenueVppMember': '과거 생산 대가 이연매출 상각',
        'ar:OtherRevenueAndIncomeMember': '기타 매출·수익'}),
    ('RRC', 315852, {'rrc:NaturalGasNaturalGasLiquidsAndOilSalesMember': '자체 생산품 판매',
        'rrc:BrokeredNaturalGasAndMarketingMember': '매입 가스 재판매·마케팅'}),
]:
    for _member, _label in _mapping.items():
        LABELS[(_symbol, _cik, _member)] = _label

HIERARCHIES[('FANG', 1539838, 'product')] = {
    'fang:OilNaturalGasAndNaturalGasLiquidMember': ['fang:OilExplorationandProductionMember',
        'us-gaap:NaturalGasProductionMember', 'fang:NaturalGasLiquidsProductionMember']}
HIERARCHIES[('DVN', 1090012, 'product')] = {
    _parent: [_child + '/' + _parent for _child in ('srt:OilReservesMember', 'dvn:GasMember', 'dvn:NGLMember')]
    for _parent in ('dvn:OilGasAndNGLSalesMember', 'dvn:MarketingAndMidstreamRevenuesMember')}
HIERARCHIES[('EXE', 895126, 'product')] = {
    'us-gaap:OilAndGasMember': ['exe:NaturalGasSalesMember', 'exe:OilSalesMember', 'exe:NaturalGasLiquidsSalesMember'],
    'us-gaap:NaturalGasGatheringTransportationMarketingAndProcessingMember': [
        'exe:NaturalGasMarketingSalesMember', 'exe:OilMarketingSalesMember', 'exe:NaturalGasLiquidsMarketingSalesMember']}
HIERARCHIES[('EQT', 33213, 'product')] = {
    'eqt:SalesOfNaturalGasNGLsAndOilAtProductionMember': [
        'eqt:NaturalGasSalesMember', 'eqt:NGLsSalesMember', 'eqt:OilSalesMember']}


def _documented_subset(rows, group, child_name, parent_name, document):
    for child in rows:
        if (child['group'] != group or child['member'] != child_name
                or child['source']['url'].split('#')[0] != document
                or child['end'] != '2025-12-31'):
            continue
        parents = [row for row in rows if row['group'] == group and row['member'] == parent_name
                   and all(row[key] == child[key] for key in ('start', 'end', 'unit', 'metric'))
                   and row['source']['url'].split('#')[0] == document and child['value'] <= row['value']]
        if len(parents) == 1:
            child['parent'] = parents[0]['member']


def annotate(rows, symbol, cik):
    """Period-bound presentation notes; preserve source values and metric scope."""
    equipment.annotate(rows, symbol, cik)
    if (symbol, cik) == ('NBR', 1163739):
        _documented_subset(rows, 'geography', 'country:SA', 'us-gaap:NonUsMember',
            equipment.DOCUMENTS[('NBR', 1163739)])
    if (symbol, cik) == ('TRGP', 1389170):
        for row in rows:
            if (row['group'] == 'segment' and row['end'] == '2025-12-31'
                    and row['source']['url'].split('#')[0] ==
                    'https://www.sec.gov/Archives/edgar/data/1389170/000119312526059296/trgp-20251231.htm'):
                row['share_exclusion'] = ('두 부문의 외부 매출 합계에는 기타 조정 −530만 달러가 필요합니다. '
                    '음수 조정과 양수 매출을 100% 구성비로 표시하지 않습니다.')
    if (symbol, cik) == ('LNG', 3570):
        _documented_subset(rows, 'product', 'lng:LiquefiedNaturalGasProcuredFromThirdPartiesMember',
            'lng:LiquefiedNaturalGasMember',
            'https://www.sec.gov/Archives/edgar/data/3570/000000357026000005/lng-20251231.htm')
    if (symbol, cik) == ('KNTK', 1692787):
        _documented_subset(rows, 'product', 'apa:MinimumVolumeCommitmentsMember',
            'apa:GatheringAndProcessingServicesMember',
            'https://www.sec.gov/Archives/edgar/data/1692787/000169278726000048/apa-20251231.htm')
    if (symbol, cik) == ('AM', 1623925):
        for row in rows:
            if (row['end'] == '2025-12-31' and row['source']['url'].split('#')[0] ==
                    'https://www.sec.gov/Archives/edgar/data/1623925/000110465926013380/am-20251231x10k.htm'):
                row['share_exclusion'] = ('이 항목은 고객 관계 상각 전 매출입니다. 합계 12억5,909만8,000 달러에서 '
                    '7,067만2,000 달러를 차감한 연결 매출 11억8,842만6,000 달러와 범위가 달라 구성비를 계산하지 않습니다.')
    for issuer, identity, document, explanation in [
        ('OXY', 797468, 'https://www.sec.gov/Archives/edgar/data/797468/000162828026009059/oxy-20251231.htm',
         '두 영업 부문은 내부거래 제거 전입니다. 연결 매출로 맞추려면 5억8,800만 달러의 내부거래 제거가 필요하며 제품 표는 탐사·생산 부문만 포함하므로 전체 연결 구성비를 계산하지 않습니다.'),
        ('EQT', 33213, 'https://www.sec.gov/Archives/edgar/data/33213/000003321326000018/eqt-20251231.htm',
         '집하·수송의 내부 매출을 포함하는 부문 표입니다. 12억5,353만2,000 달러의 내부거래·기타 제거가 필요하므로 전체 연결 구성비를 계산하지 않습니다.'),
    ]:
        if (symbol, cik) == (issuer, identity):
            for row in rows:
                if (_reviewed_year(row, document)
                        and (row['group'] == 'segment' or (symbol == 'OXY' and row['group'] == 'product'))):
                    row['share_exclusion'] = explanation
                    if row['group'] == 'segment':
                        row['includes_intersegment'], row['total'] = True, None
    return majors.annotate(providers.annotate(rows, symbol, cik), symbol, cik)


def _reviewed_year(row, document):
    return (row['start'] == '2025-01-01' and row['end'] == '2025-12-31'
            and row['source']['url'].split('#')[0] == document)


def canonical_revenue(rows, symbol):
    """EQT repeats one production subtotal under two tags; keep its specific row.

    Do not delete facts in another report, period, metric, currency or value.
    This also normalizes legacy caches without fetching or modifying numbers.
    """
    document = 'https://www.sec.gov/Archives/edgar/data/33213/000003321326000018/eqt-20251231.htm'
    rows = providers.canonical_revenue(rows, symbol)
    from .company_revenue import source_cik
    for cik in {source_cik(row['source']) for row in rows} - {None}:
        rows = equipment.canonical(rows, symbol, cik)
    if symbol != 'EQT':
        return rows
    kept = []
    for row in rows:
        duplicate = (row['group'] == 'product' and row['member'] == 'us-gaap:OilAndGasMember'
                     and _reviewed_year(row, document) and any(
                         candidate['member'] == 'eqt:SalesOfNaturalGasNGLsAndOilAtProductionMember'
                         and candidate['group'] == row['group'] and _reviewed_year(candidate, document)
                         and all(candidate[key] == row[key] for key in ('start', 'end', 'unit', 'metric', 'value'))
                         for candidate in rows))
        if not duplicate:
            kept.append(row)
    return kept


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    # EQT's segment view has a Revenues-tag Upstream row but contract-revenue
    # rows only for Gathering/Transmission. Selecting the latter drops Upstream.
    if ((symbol, cik, group, start, end) == ('EQT', 33213, 'segment', '2025-01-01', '2025-12-31')
            and origin['url'].split('#')[0] ==
            'https://www.sec.gov/Archives/edgar/data/33213/000003321326000018/eqt-20251231.htm'):
        return tag == 'us-gaap:Revenues'
    return majors.metric_allowed(tag, group, start, end, origin, symbol, cik)


def dimensions(pairs, symbol, cik):
    if len(set(pairs)) != len(pairs):
        return None
    reviewed = providers.dimensions(pairs, symbol, cik)
    if reviewed:
        return reviewed
    reviewed = equipment.dimensions(pairs, symbol, cik)
    if reviewed:
        return reviewed
    reviewed = majors.dimensions(pairs, symbol, cik)
    if reviewed:
        return reviewed
    # These issuers put external corporate revenue on a consolidation axis.
    # Never accept the operating-segment totals or elimination coordinates here.
    if ((symbol, cik) in {('MPC', 1510295), ('PSX', 1534701)}
            and pairs == [('srt:ConsolidationItemsAxis', 'us-gaap:CorporateNonSegmentMember')]):
        return 'segment', 'us-gaap:CorporateNonSegmentMember'
    if len(pairs) not in (2, 3) or len(set(pairs)) != len(pairs):
        return None
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def presentation_group(row, symbol, cik):
    group = providers.presentation_group(row, symbol, cik)
    row['group'] = group
    row['group'] = equipment.presentation_group(row, symbol, cik)
    return majors.presentation_group(row, symbol, cik)


def compound_member(member, symbol, cik):
    return '/' in member and (symbol, cik, member) in LABELS


def separate_revenue_type(row, symbol, cik):
    # A narrative subset of Other revenues is not an additional product bucket.
    # Bound this reading to the reviewed filing/period, including old cached rows.
    if (symbol, cik) == ('EQT', 33213):
        return (row['group'] == 'product' and row['member'] == 'eqt:RevenuesFromContractWithCustomersMember'
                and _reviewed_year(row, 'https://www.sec.gov/Archives/edgar/data/33213/000003321326000018/eqt-20251231.htm'))
    return (symbol == 'DINO' and cik == 1915657 and row['group'] == 'product'
            and row['member'] == 'dino:RenewableIdentificationNumbersRINsMember'
            and row['start'] == '2025-01-01' and row['end'] == '2025-12-31'
            and row['source']['url'].split('#')[0] ==
            'https://www.sec.gov/Archives/edgar/data/1915657/000191565726000016/dino-20251231.htm')
