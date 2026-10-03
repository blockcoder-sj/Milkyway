"""Reviewed downstream revenue coordinates with actual fiscal-year boundaries.

The original tags, issuer, full coordinate and document remain attached. Lease,
derivative, intercompany and unconsolidated investment scopes are not combined.
"""
DOCUMENTS = {
    ('DK',1694426):'https://www.sec.gov/Archives/edgar/data/1694426/000162828026012664/dk-20251231.htm',
    ('DKL',1552797):'https://www.sec.gov/Archives/edgar/data/1552797/000162828026012666/dkl-20251231.htm',
    ('PBF',1534504):'https://www.sec.gov/Archives/edgar/data/1534504/000153450426000010/pbf-20251231.htm',
    ('PARR',821483):'https://www.sec.gov/Archives/edgar/data/821483/000082148326000005/parr-20251231.htm',
    ('CVI',1376139):'https://www.sec.gov/Archives/edgar/data/1376139/000137613926000014/cvi-20251231.htm',
    ('CLMT',2013745):'https://www.sec.gov/Archives/edgar/data/2013745/000201374526000007/clmt-20251231x10k.htm',
    ('GLP',1323468):'https://www.sec.gov/Archives/edgar/data/1323468/000110465926021381/glp-20251231x10k.htm',
    ('CAPL',1538849):'https://www.sec.gov/Archives/edgar/data/1538849/000119312526071870/capl-20251231.htm',
    ('SGU',1002590):'https://www.sec.gov/Archives/edgar/data/1002590/000119312525311490/sgu-20250930.htm',
    ('SPH',1005210):'https://www.sec.gov/Archives/edgar/data/1005210/000119312525298630/sph-20250927.htm',
    ('MMLP',1176334):'https://www.sec.gov/Archives/edgar/data/1176334/000117633426000012/mmlp-20251231.htm',
    ('NGL',1504461):'https://www.sec.gov/Archives/edgar/data/1504461/000150446126000012/ngl-20260331.htm',
    ('GEL',1022321):'https://www.sec.gov/Archives/edgar/data/1022321/000102232126000008/gel-20251231.htm',
    ('WKC',789460):'https://www.sec.gov/Archives/edgar/data/789460/000078946026000015/wkc-20251231.htm',
    ('GPRE',1309402):'https://www.sec.gov/Archives/edgar/data/1309402/000130940226000019/gpre-20251231.htm',
    ('REX',744187):'https://www.sec.gov/Archives/edgar/data/744187/000093041326000937/c115944_10k-ixbrl.htm',
    ('GEVO',1392380):'https://www.sec.gov/Archives/edgar/data/1392380/000139238026000006/gevo-20251231x10k.htm',
}
PERIODS = {key:('2025-01-01','2025-12-31') for key in DOCUMENTS}
PERIODS.update({('SGU',1002590):('2024-10-01','2025-09-30'),
    ('SPH',1005210):('2024-09-29','2025-09-27'),
    ('NGL',1504461):('2025-04-01','2026-03-31'),
    ('REX',744187):('2025-02-01','2026-01-31')})
COORDINATES, LABELS = {}, {}
SEGMENT = 'us-gaap:StatementBusinessSegmentsAxis'
PRODUCT = 'srt:ProductOrServiceAxis'
OPERATING = ('srt:ConsolidationItemsAxis','us-gaap:OperatingSegmentsMember')


def _add(symbol,cik,pairs,group,member,label):
    COORDINATES[symbol,cik,frozenset(pairs)] = group,member
    LABELS[symbol,cik,member] = label


def _members(symbol,cik,axis,group,values,qualifiers=()):
    for member,label in values.items():
        _add(symbol,cik,[(axis,member),*qualifiers],group,member,label)


SEGMENTS = {
    ('DK',1694426):{'dk:RefiningMember':'정유 · 외부 수입','dk:LogisticsMember':'물류 · 외부 수입'},
    ('DKL',1552797):{'dkl:GatheringAndProcessingMember':'집하·처리 · 리스 포함',
        'dkl:WholesaleMarketingAndTerminallingMember':'도매 판매·터미널 · 리스 포함',
        'dkl:StorageAndTransportationMember':'저장·운송 · 리스 포함'},
    ('PBF',1534504):{'pbf:RefiningGroupMember':'정유 · 내부 거래 제거 전',
        'pbf:LogisticsGroupMember':'물류 · 내부 거래 제거 전'},
    ('CVI',1376139):{'cvi:PetroleumSegmentMember':'석유 · 외부 수입',
        'cvi:RenewablesSegmentMember':'재생연료 · 외부 수입',
        'cvi:NitrogenFertilizerSegmentMember':'질소 비료 · 외부 수입'},
    ('CLMT',2013745):{'clmt:SpecialtyProductsAndSolutionsMember':'특수제품',
        'clmt:PerformanceBrandsMember':'브랜드 제품','clmt:MontanaRenewablesMember':'Montana Renewables'},
    ('GLP',1323468):{'glp:WholesaleSegmentMember':'도매 · 상품 거래 포함',
        'glp:GasolineDistributionAndStationOperationsSegmentMember':'주유소·유통 · 리스 포함',
        'glp:CommercialSegmentMember':'상업 판매 · 상품 거래 포함'},
    ('CAPL',1538849):{'capl:WholesaleMember':'도매 · 리스 포함','capl:RetailSegmentMember':'소매 · 리스 포함'},
    ('MMLP',1176334):{'mmlp:TerminallingAndStorageSegmentMember':'터미널·저장',
        'mmlp:TransportationSegmentMember':'운송','mmlp:SulfurServicesSegmentMember':'황·황 서비스',
        'mmlp:SpecialtyProductsSegmentMember':'특수제품'},
    ('GEL',1022321):{'gel:OffshorePipelineTransportationSegmentMember':'해상 배관 · 외부 수입',
        'gel:MarineTransportationSegmentMember':'해상 운송 · 외부 수입',
        'gel:OnshoreTransportationAndServicesSegmentMember':'육상 물류·서비스 · 외부 수입'},
    ('GPRE',1309402):{'gpre:EthanolProductionMember':'에탄올 생산 · 상품 거래 포함',
        'gpre:AgribusinessAndEnergyServicesMember':'농산물·에너지 서비스 · 상품 거래 포함'},
    ('GEVO',1392380):{'gevo:GevoSegmentMember':'Gevo · 특수 연료·개발',
        'gevo:RenewableNaturalGasSegmentMember':'RNG','gevo:GevoNorthDakotaSegmentMember':'North Dakota'},
}
for (_symbol,_cik),_members_by_name in SEGMENTS.items():
    _qualifiers = [OPERATING] if _symbol in {'DK','PBF','CAPL'} else []
    if _symbol == 'CLMT':
        _qualifiers = [OPERATING,('us-gaap:SubsegmentsConsolidationItemsAxis','us-gaap:SalesRevenueSegmentMember')]
    _members(_symbol,_cik,SEGMENT,'segment',_members_by_name,_qualifiers)
    if _symbol == 'DKL':
        _members(_symbol,_cik,SEGMENT,'segment',_members_by_name,[OPERATING])

# Genesis repeats an external onshore amount with an alternate actual member.
_add('GEL',1022321,[(SEGMENT,'gel:OnshoreFacilitiesAndTransportationSegmentMember')],
     'segment','gel:OnshoreTransportationAndServicesSegmentMember','육상 물류·서비스 · 외부 수입')
ALIASES = {('GEL',1022321,'gel:OnshoreFacilitiesAndTransportationSegmentMember'):
           'gel:OnshoreTransportationAndServicesSegmentMember'}

PRODUCTS = {
    ('DKL',1552797):{'dkl:ServiceRevenueThirdPartyMember':'제삼자 서비스 · 리스 제외',
        'dkl:ServiceRevenueAffiliateMember':'계열 서비스 · 리스 제외',
        'dkl:ProductRevenueThirdPartyMember':'제삼자 상품 · 리스 제외',
        'dkl:ProductRevenueAffiliateMember':'계열 상품 · 리스 제외'},
    ('PARR',821483):{'parr:FuelRevenueMember':'연료','parr:OtherRevenueMember':'기타'},
    ('GLP',1323468):{'glp:RefinedPetroleumProductsRenewableFuelsCrudeOilAndPropaneMember':'연료 상품 · 고객 계약',
        'glp:StationOperationsMember':'점포 운영 · 고객 계약'},
    ('CAPL',1538849):{'capl:FuelSalesToExternalCustomersMember':'외부 연료 · 리스 제외',
        'capl:FoodAndMerchandiseSalesMember':'식품·상품 · 리스 제외',
        'us-gaap:ProductAndServiceOtherMember':'기타 · 리스 제외'},
    ('SGU',1002590):{'sgu:HomeHeatingOilAndPropaneMember':'난방유·프로판',
        'sgu:MotorFuelAndOtherPetroleumProductsMember':'차량·기타 연료',
        'sgu:EquipmentInstallationsMember':'설비 설치',
        'sgu:EquipmentMaintenanceServiceContractsMember':'정비 계약',
        'sgu:BillableCallServicesMember':'유상 방문'},
    ('SPH',1005210):{'sph:PropaneMember':'프로판','sph:FuelOilAndRefinedFuelsMember':'연료유·정유 제품',
        'sph:NaturalGasAndElectricityMember':'가스·전력','sph:OtherSalesRevenueNetMember':'기타'},
    ('MMLP',1176334):{'mmlp:TerminallingAndStorageMember':'터미널·저장',
        'mmlp:TransportationMember':'운송','mmlp:SulfurServiceProductsMember':'황 서비스',
        'mmlp:SulfurServiceProductSalesMember':'황 제품','mmlp:SpecialtyProductsMember':'특수제품'},
    ('GEL',1022321):{'gel:FeebasedRevenuesMember':'수수료 수입','gel:ProductSalesMember':'상품 판매',
        'gel:RefineryServicesMember':'정유 서비스'},
    ('REX',744187):{'rex:EthanolMember':'에탄올','rex:DriedDistillersGrainsMember':'건조 증류곡물',
        'rex:DistillersCornOilMember':'증류 옥수수유','rex:ModifiedDistillersGrainsMember':'변형 증류곡물',
        'rex:OtherMember':'기타'},
    ('GEVO',1392380):{'gevo:EthanolMember':'에탄올','gevo:EthanolRelatedProductsMember':'에탄올 부산물',
        'gevo:EnvironmentalAttributesMember':'환경 속성','gevo:RenewableNaturalGasCommodityMember':'RNG 상품',
        'gevo:HydrocarbonMember':'탄화수소 제품',
        'gevo:OtherRevenueSaleOfIsooctaneAndSoftwareServicesMember':'기타 · 상품·서비스'},
}
for (_symbol,_cik),_values in PRODUCTS.items():
    _members(_symbol,_cik,PRODUCT,'product',_values)
_members('PBF',1534504,PRODUCT,'product',{
    'pbf:GasolineAndDistillateMember':'휘발유·중간유분 · 정유 내',
    'pbf:FeedstocksAndOtherMember':'원료·기타 · 정유 내',
    'pbf:AsphaltandResidualOilMember':'아스팔트·잔사유 · 정유 내',
    'pbf:ChemicalsMember':'화학 원료 · 정유 내','pbf:LubricantsMember':'윤활유 · 정유 내'},
    [(SEGMENT,'pbf:RefiningGroupMember')])

for _segment,_values in {
    'clmt:SpecialtyProductsAndSolutionsMember':{'clmt:LubricatingOilsMember':'윤활유',
        'clmt:SolventsMember':'용제','clmt:WaxesMember':'왁스','clmt:OtherSpecialtyProductsMember':'기타 특수제품'},
    'clmt:MontanaRenewablesMember':{'clmt:GasolineMember':'휘발유 · Montana',
        'clmt:DieselMember':'경유 · Montana','clmt:JetFuelMember':'항공유 · Montana',
        'clmt:AsphaltHeavyFuelOilsAndOtherMember':'아스팔트·중유·기타 · Montana',
        'clmt:RenewableFuelsMember':'재생연료 · Montana'},
}.items():
    _members('CLMT',2013745,PRODUCT,'product',_values,[
        ('us-gaap:ConcentrationRiskByBenchmarkAxis','us-gaap:SalesMember'),
        ('us-gaap:ConcentrationRiskByTypeAxis','us-gaap:ProductConcentrationRiskMember'),(SEGMENT,_segment)])
_add('CLMT',2013745,[('us-gaap:ConcentrationRiskByBenchmarkAxis','us-gaap:SalesMember'),
    ('us-gaap:ConcentrationRiskByTypeAxis','us-gaap:ProductConcentrationRiskMember'),
    (SEGMENT,'clmt:PerformanceBrandsMember')],'product','clmt:PerformanceBrandsMember','브랜드 제품')

_members('SPH',1005210,'us-gaap:EquitySecuritiesByIndustryAxis','end_market',{
    'sph:ResidentialSectorMember':'주거 · 소매','sph:CommercialSectorMember':'상업 · 소매',
    'sph:IndustrialSectorMember':'산업 · 소매','us-gaap:GovernmentSectorMember':'정부 · 소매',
    'us-gaap:AgriculturalSectorMember':'농업 · 소매'},[(PRODUCT,'us-gaap:RetailMember')])
_members('SPH',1005210,PRODUCT,'end_market',{'sph:WholesaleMember':'도매 · 고객 범위'})
_members('NGL',1504461,PRODUCT,'revenue_type',{
    'us-gaap:ProductMember':'상품 수입','us-gaap:ServiceMember':'서비스 수입'})
_members('NGL',1504461,SEGMENT,'segment',{
    'ngl:WaterSolutionsSegmentMember':'물 서비스','ngl:CrudeOilLogisticsSegmentMember':'원유 물류',
    'ngl:LiquidsLogisticsSegmentMember':'액체 물류'},[OPERATING])
_add('NGL',1504461,[('srt:ConsolidationItemsAxis','us-gaap:CorporateNonSegmentMember')],
    'segment','us-gaap:CorporateNonSegmentMember','본사·기타')
_members('WKC',789460,SEGMENT,'segment',{'wkc:AviationSegmentMember':'항공',
    'wkc:LandSegmentMember':'육상','wkc:MarineSegmentMember':'해상'},[OPERATING])
_members('WKC',789460,'srt:StatementGeographicalAxis','geography',{
    'country:US':'미국','us-gaap:EMEAMember':'Europe·Middle East·Africa',
    'srt:AsiaPacificMember':'Asia·Pacific',
    'wkc:AmericasExcludingUnitedStatesMember':'미국 외 Americas'})
_members('REX',744187,PRODUCT,'revenue_type',{
    'rex:DerivativeFinancialInstrumentGainsLossesMember':'파생상품 수입 조정 · 제품 외'})


def dimensions(pairs,symbol,cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol,cik,frozenset(pairs)))


def reviewed(row,symbol,cik):
    return ((row['start'],row['end']) == PERIODS.get((symbol,cik))
        and row.get('unit','USD') == 'USD'
        and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol,cik)))


def metric_allowed(tag,group,start,end,origin,symbol,cik):
    if not reviewed(dict(start=start,end=end,source=origin),symbol,cik):
        return True
    if symbol in {'CVI','NGL','WKC','GPRE','REX'} or (symbol == 'GLP' and group == 'segment'):
        expected = 'us-gaap:Revenues'
    elif symbol == 'CAPL' or (symbol == 'GEVO' and group == 'product'):
        expected = 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax'
    else:
        expected = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
    return tag == expected


def signed_value(tag,context,origin,symbol,cik):
    start,end,group,member = context
    return ((symbol,cik) == ('REX',744187) and group == 'revenue_type'
        and member == 'rex:DerivativeFinancialInstrumentGainsLossesMember'
        and tag == 'us-gaap:Revenues'
        and reviewed(dict(start=start,end=end,source=origin),symbol,cik))


def presentation_group(row,symbol,cik):
    if reviewed(row,symbol,cik):
        member = ALIASES.get((symbol,cik,row['member']),row['member'])
        if member != row['member']:
            row['member'] = member
        groups = {(m,g) for (s,identity,_),(g,m) in COORDINATES.items() if (s,identity)==(symbol,cik)}
        possible = {g for m,g in groups if m==member}
        if len(possible)==1:
            return possible.pop()
    return row['group']


def canonical(rows,symbol,cik):
    allowed = {(group,member) for (s,identity,_),(group,member) in COORDINATES.items()
               if (s,identity)==(symbol,cik)}
    # The current GPRE annual can cache a partial 2024 contract-product table
    # from the earlier parser. Preserve independent reports and historical views.
    def obsolete_product(row):
        return ((symbol,cik)==('GPRE',1309402) and row['group']=='product'
            and (row['start'],row['end'])==('2024-01-01','2024-12-31')
            and row.get('unit','USD')=='USD'
            and row['metric']=='us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
            and row['member'] in {'gpre:DistillerGrainsMember','gpre:ProductsAndServicesOtherMember'}
            and row['source']['url'].split('#')[0]==DOCUMENTS.get((symbol,cik)))
    selected = [row for row in rows if not obsolete_product(row) and (not reviewed(row,symbol,cik)
        or ((row['group'],row['member']) in allowed
            and metric_allowed(row['metric'],row['group'],row['start'],row['end'],row['source'],symbol,cik)))]
    values = {}
    for row in selected:
        if reviewed(row,symbol,cik):
            key=tuple(row[k] for k in ('group','member','start','end','unit','metric'))
            values.setdefault(key,set()).add(row['value'])
    result,seen = [],set()
    for row in selected:
        if reviewed(row,symbol,cik):
            key=tuple(row[k] for k in ('group','member','start','end','unit','metric'))
            if key in seen or len(values[key]) != 1:
                continue
            seen.add(key)
        result.append(row)
    return result


def annotate(rows,symbol,cik):
    explanations = {
        'DKL':'부문 수입 1,013,323,000 USD에는 리스 215,888,000이 포함됩니다. 상품·서비스 797,435,000의 부분 구성에 리스를 더하거나 같은 비중 분모로 사용하지 않습니다.',
        'PBF':'정유 제품 29,297,700,000 USD는 정유 내부 구성입니다. 물류 383,500,000을 포함한 부문 합계 29,681,200,000에서 내부 거래 348,900,000을 제거해 연결 29,332,300,000이 됩니다.',
        'GLP':'상품 거래·리스 등을 포함한 연결 18,561,421,000 USD와 고객 계약 판매 8,713,114,000의 범위가 다릅니다. 계약 제품 부분에는 전체 연결 기준 비중을 표시하지 않습니다.',
        'CAPL':'전체 3,662,534,000 USD 중 상품·서비스 3,599,988,000과 리스 62,546,000을 구분합니다. 리스가 빠진 제품 부분을 전체 매출 구성비로 사용하지 않습니다.',
        'WKC':'원문 부문 수입은 0.1 million 단위로 반올림되어 합계 36,916,700,000 USD와 연결 36,916,600,000의 차이 100,000이 있습니다. 금액을 임의 조정하거나 이 표의 비중을 계산하지 않습니다.',
        'GPRE':'2025년 외부 수입 2,091,680,000 USD는 상품 거래 회계를 포함합니다. 계약 태그의 에탄올 0은 에탄올 전체 매출 0이 아니며 계약 수입 188,979,000과 같은 분모로 사용하지 않습니다.',
        'REX':'제품 650,741,000 USD에서 파생상품 조정 -254,000을 반영하면 연결 650,487,000입니다. 양수 제품 비율·음수 조정 비율을 계산하지 않으며 지분법 Big River 전체 수입은 제외합니다.',
    }
    for row in rows:
        if not reviewed(row,symbol,cik):
            continue
        group=row['group']
        omit = (symbol in {'PBF','REX'} or
            (symbol in {'DKL','GLP','CAPL'} and group=='product') or
            (symbol=='WKC' and group=='segment'))
        if symbol in explanations:
            row['share_exclusion'] = explanations[symbol]
        if omit:
            row['total'] = None
        if symbol=='PBF' and group=='segment':
            row['includes_intersegment'] = True
    return rows
