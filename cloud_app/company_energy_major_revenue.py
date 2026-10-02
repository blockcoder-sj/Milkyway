"""Exact external, internal and regional coordinates in checked major filings.

IFRS SegmentsAxis does not always mean an operating segment: Petrobras also uses
it for products and markets. Unknown members and extra dimensions stay excluded.
"""

COORDINATES = {}
LABELS = {}
SEGMENTS = {
    ('SHEL', 1306965): {
        'shel:IntegratedGasMember': '통합 가스·LNG·GTL',
        'shel:UpstreamMember': '상류 · 탐사·생산',
        'shel:MarketingSegmentMember': '판매 · 연료·윤활유',
        'shel:ChemicalsAndProductsSegmentMember': '화학·정유 제품',
        'shel:RenewablesAndEnergySolutionsSegmentMember': '재생에너지·전력·가스 거래',
        'shel:CorporateSegment1Member': '본사·기타'},
    ('TTE', 879764): {
        'tot:ExplorationAndProductionSegmentMember': '탐사·생산',
        'tot:IntegratedLngSegmentMember': '통합 LNG',
        'tot:IntegratedPowerSegmentMember': '통합 전력',
        'tot:RefiningAndChemicalsSegmentMember': '정유·화학',
        'tot:MarketingAndServicesSegmentMember': '판매·서비스',
        'tot:CorporateSegmentMember': '본사'},
    ('E', 1002242): {
        'e:ExplorationAndProductionSegmentMember': '탐사·생산',
        'e:GlobalGasAndLngPortfolioAndPowerSegmentMember': '도매 가스·LNG·전력',
        'e:RefiningAndChemicalsSegmentMember': '정유·화학',
        'e:EniliveSegmentMember': 'Enilive · 재생연료·연료 판매',
        'e:PlenitudeSegmentMember': 'Plenitude · 전력·가스·충전',
        'e:CorporateAndOtherActivitiesMember': '본사·기타'},
    ('EQNR', 1140625): {
        'eqnr:ExplorationAndProductionNorwayMember': '탐사·생산 · 노르웨이',
        'eqnr:ExplorationAndProductionInternationalMember': '탐사·생산 · 기타 해외',
        'eqnr:ExplorationAndProductionUsaMember': '탐사·생산 · 미국',
        'eqnr:MarketingMidstreamAndProcessingMember': '판매·물류·처리',
        'eqnr:RenewablesMember': '재생에너지 · 2025년 부문',
        'ifrs-full:AllOtherSegmentsMember': '기타'},
    ('BP', 313807): {
        'bp:GasLowCarbonEnergyMember': '가스·저탄소 에너지',
        'bp:OilProductionOperationsMember': '원유 생산·운영',
        'bp:CustomersProductsMember': '연료·윤활유·고객·제품'},
    ('PBR', 1119639): {
        'pbr:ExplorationAndProductionMember': '탐사·생산',
        'pbr:RefiningTransportationAndMarketingMember': '정유·운송·판매',
        'pbr:GasAndLowCarbonEnergiesMember': '가스·저탄소 에너지',
        'pbr:CorporateAndOtherBusinessMember': '본사·기타'},
    ('EC', 1444406): {
        'ec:ExplorationAndProductionMember': '탐사·생산',
        'ec:RefiningAndPetrochemicalsMember': '정유·석유화학',
        'ec:TransportationAndLogisticsMember': '운송·물류',
        'ec:ElectricPowerTransmissionAndTollRoadsConcessionsMember': '송전·유료 도로'},
    ('YPF', 904851): {
        'ypf:UpstreamMember': '상류 · 탐사·생산',
        'ypf:MidstreamAndDownstreamMember': '물류·정유·판매',
        'ypf:LNGandIntegratedGasMember': 'LNG·통합 가스',
        'ypf:NewEnergiesMember': '신에너지',
        'ypf:CentralAdministrationAndOthersMember': '본사·기타'},
}


def _add(symbol, cik, pairs, group, member, label):
    COORDINATES[symbol, cik, frozenset(pairs)] = (group, member)
    LABELS[symbol, cik, member] = label


for (_symbol, _cik), _members in SEGMENTS.items():
    for _member, _label in _members.items():
        _pairs = [('ifrs-full:SegmentsAxis', _member)]
        if _symbol in {'BP', 'EQNR', 'YPF'}:
            _pairs.append(('ifrs-full:SegmentConsolidationItemsAxis', 'ifrs-full:OperatingSegmentsMember'))
        if _symbol == 'EC':
            _pairs += [('ifrs-full:SegmentConsolidationItemsAxis', 'ifrs-full:OperatingSegmentsMember'),
                       ('ec:SalesByTypeAxis', 'ec:ThirdPartySalesMember')]
        _add(_symbol, _cik, _pairs, 'segment', _member, _label)

_add('BP', 313807, [('ifrs-full:SegmentConsolidationItemsAxis', 'bp:OtherBusinessAndCorporateNonSegmentMember')],
     'segment', 'bp:OtherBusinessAndCorporateNonSegmentMember', '기타 사업·본사')

GEOGRAPHY = {
    ('SHEL', 1306965): {'srt:EuropeMember': '유럽', 'shel:AsiaOceaniaAndAfricaMember': '아시아·오세아니아·아프리카',
        'country:US': '미국', 'shel:OtherAmericasMember': '기타 미주', 'country:GB': '영국 · 유럽 안의 항목'},
    ('TTE', 879764): {'ifrs-full:CountryOfDomicileMember': '프랑스', 'tot:RestOfEuropeExcludingFranceMember': '프랑스 외 유럽',
        'srt:NorthAmericaMember': '북미', 'srt:AfricaMember': '아프리카',
        'tot:RestOfWorldExcludingEuropeNorthAmericaAndAfricaMember': '유럽·북미·아프리카 외'},
    ('E', 1002242): {'country:IT': '이탈리아', 'e:OtherEuropeanMember': '기타 EU',
    'e:RestOfEuropeMember': 'EU 외 유럽', 'srt:AmericasMember': '미주', 'srt:AsiaMember': '아시아',
        'srt:AfricaMember': '아프리카', 'e:OtherAreasMember': '기타 지역'},
    ('BP', 313807): {'country:US': '미국', 'bp:NonUSMember': '미국 외',
        'ifrs-full:CountryOfDomicileMember': '영국 · 미국 외 지역 안의 항목'},
    ('EC', 1444406): {'country:CO': '콜롬비아', 'country:US': '미국', 'country:CN': '중국',
        'country:BR': '브라질', 'country:IN': '인도', 'ec:SingaporeAndOtherAsianCountriesMember': '싱가포르·기타 아시아',
        'country:PE': '페루', 'country:CL': '칠레', 'ec:OtherSouthAmericaCountriesMember': '기타 남미',
        'ec:CentralAmericaAndCaribbeanMember': '중미·카리브', 'srt:EuropeMember': '유럽'},
    ('YPF', 904851): {'country:AR': '아르헨티나', 'ypf:MercosurAndAssociatesCountriesMember': 'Mercosur·연관국',
        'srt:EuropeMember': '유럽', 'ifrs-full:ForeignCountriesMember': '기타 해외'},
}
for (_symbol, _cik), _members in GEOGRAPHY.items():
    for _member, _label in _members.items():
        _add(_symbol, _cik, [('ifrs-full:GeographicalAreasAxis', _member)], 'geography', _member, _label)

for _member, _label in {
    'bp:OilAndGasCrudeOilMember': '원유', 'bp:OilandGasOilProductsMember': '석유제품',
    'bp:NaturalGasProductsMember': '천연가스', 'bp:ProductAndServiceOther1Member': '기타 제품·서비스',
}.items():
    _add('BP', 313807, [('ifrs-full:ProductsAndServicesAxis', _member)], 'product', _member, _label)

for _member, _label in {
    'srt:CrudeOilMember': '원유', 'eqnr:NaturalGasMember': '천연가스',
    'eqnr:RefinedProductsMember': '정유제품', 'eqnr:NaturalGasLiquidsMember': 'NGL',
    'eqnr:PowerMember': '전력', 'eqnr:TrasnsportationMember': '운송',
    'eqnr:OtherProductsMember': '기타 제품',
}.items():
    _add('EQNR', 1140625, [('ifrs-full:ProductsAndServicesAxis', _member)], 'product', _member, _label)

# Petrobras's petroleum-products subtotal and the seven children are Brazilian
# domestic sales, not the group's worldwide production or product-market share.
_oil_total = 'pbr:SubtotalOilProductsMember'
_add('PBR', 1119639, [('ifrs-full:SegmentsAxis', _oil_total)], 'product', _oil_total, '브라질 석유제품 판매 합계')
for _member, _label in {'pbr:DieselMember': '경유', 'pbr:GasolineMember': '휘발유',
    'pbr:LiquefiedPetroleumGasMember': 'LPG', 'pbr:JetFuelMember': '항공유',
    'pbr:NaphthaMember': '나프타', 'pbr:FuelOiIincludingBunkerFuelMember': '연료유·벙커유',
    'pbr:OtherOilProductsMember': '기타 석유제품'}.items():
    _add('PBR', 1119639, [('ifrs-full:ServiceConcessionArrangementsAxis', _member),
        ('ifrs-full:SegmentsAxis', _oil_total)], 'product', _member, '브라질 · ' + _label)
for _market, _items in {
    'pbr:DomesticMarketMember': {
        'pbr:NaturalGasMember': '천연가스', 'pbr:CrudeOilsMember': '원유',
        'pbr:RenewablesAndNitrogenProductsMember': '재생에너지·질소 제품',
        'pbr:BreakageMember': '미사용 고객 권리 대가',
        'pbr:ElectricitiesMember': '전력', 'pbr:ServicesAgencyAndOthersMember': '서비스·대행·기타'},
    'pbr:ForeignMarketMember': {
        'pbr:ExportsMember': '수출 합계', 'pbr:CrudeOilsMember': '원유 수출',
        'pbr:FuelOiIincludingBunkerFuelMember': '연료유·벙커유 수출',
        'pbr:OtherOilProductsMember': '기타 석유제품 수출', 'pbr:SalesAbroadMember': '해외 현지 판매'},
}.items():
    for _member, _label in _items.items():
        _key = _member + '/' + _market
        _add('PBR', 1119639, [('ifrs-full:ServiceConcessionArrangementsAxis', _member),
             ('ifrs-full:SegmentsAxis', _market)], 'product', _key,
             ('브라질 · ' if _market == 'pbr:DomesticMarketMember' else '해외 · ') + _label)
for _member, _label in {'pbr:DomesticMarketMember': '브라질', 'pbr:ForeignMarketMember': '해외'}.items():
    _add('PBR', 1119639, [('ifrs-full:SegmentsAxis', _member)], 'geography', _member, _label)
for _member, _label in {'pbr:CountryChinaMember': '중국', 'pbr:CountryAmericasMember': '미국 외 미주',
    'pbr:CountryEuropeMember': '유럽', 'pbr:CountryAsiaMember': '중국·싱가포르 외 아시아',
    'pbr:CountryUnitedStatesMember': '미국', 'pbr:CountrySingaporeMember': '싱가포르',
    'pbr:OthersCountriesMember': '기타 해외 국가'}.items():
    _add('PBR', 1119639, [('ifrs-full:SegmentsAxis', _member)], 'geography', _member, _label)

# ExxonMobil's original 2025 operating issuer (34088) is not the new 2026 holdco.
# Each external-sales fact keeps its sales qualifier, segment AND geography.
for _segment, _label in {'xom:UpstreamMember':'상류', 'xom:EnergyProductsMember':'연료·에너지 제품',
    'xom:ChemicalProductsMember':'화학 제품', 'xom:SpecialtyProductsMember':'특수 제품'}.items():
    for _region, _area in [('country:US','미국'),('us-gaap:NonUsMember','미국 외')]:
        _member = _segment + '/' + _region
        _add('XOM',34088,[('srt:ProductOrServiceAxis','xom:SalesAndOtherOperatingRevenueMember'),
            ('srt:StatementGeographicalAxis',_region),('us-gaap:StatementBusinessSegmentsAxis',_segment)],
            'segment',_member,_label+' · '+_area+' 외부 판매')
for _member, _label in {'xom:SalesAndOtherOperatingRevenueMember':'판매·기타 영업 수익',
    'xom:IncomeFromEquityAffiliatesMember':'지분법 관계기업 이익', 'xom:OtherRevenueMember':'기타 수익'}.items():
    _add('XOM',34088,[('srt:ProductOrServiceAxis',_member)],'revenue_type',_member,_label)

DOCUMENTS = {
    'XOM':'https://www.sec.gov/Archives/edgar/data/34088/000003408826000045/xom-20251231.htm',
    'BP':'https://www.sec.gov/Archives/edgar/data/313807/000031380726000006/bp-20251231.htm',
    'EQNR':'https://www.sec.gov/Archives/edgar/data/1140625/000114062526000013/eqnr-20251231.htm',
    'PBR':'https://www.sec.gov/Archives/edgar/data/1119639/000129281426002168/pbrform20f_2025.htm',
    'YPF':'https://www.sec.gov/Archives/edgar/data/904851/000119312526126363/d95578d20f.htm',
    'SHEL':'https://www.sec.gov/Archives/edgar/data/1306965/000162828026017024/shel-20251231.htm',
}


def dimensions(pairs, symbol, cik):
    if len(pairs) != len(set(pairs)):
        return None
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def reviewed(row, symbol):
    return (row['start']=='2025-01-01' and row['end']=='2025-12-31'
            and row['source']['url'].split('#')[0]==DOCUMENTS.get(symbol))


def annotate(rows, symbol, cik):
    for row in rows:
        if not reviewed(row,symbol):
            continue
        if symbol=='EQNR' and cik==1140625 and row['group']=='segment':
            row['includes_intersegment'],row['total']=True,None
            row['share_exclusion']='2025년 부문 합계 148,883,000,000 USD는 내부 거래 포함입니다. 42,421,000,000 USD를 제거한 연결 매출 106,462,000,000 USD와 구분하며 비중을 계산하지 않습니다.'
        if symbol=='YPF' and cik==904851 and row['group']=='segment':
            row['includes_intersegment'],row['total']=True,None
            row['share_exclusion']='2025년 부문 매출 합계 27,567,000,000 USD에서 내부 거래 9,119,000,000 USD를 제거합니다. 연결 매출 18,448,000,000 USD로 구성비를 계산하지 않습니다.'
        if symbol=='PBR' and cik==1119639:
            if row['group']=='segment':
                row['includes_intersegment'],row['total']=True,None
                row['share_exclusion']='2025년 부문 매출은 내부 거래를 포함합니다. 63,540,000,000 USD의 제거 후 연결 매출은 89,195,000,000 USD입니다.'
            if row['group']=='product' and row['member'] in {
                    'pbr:DieselMember','pbr:GasolineMember','pbr:LiquefiedPetroleumGasMember',
                    'pbr:JetFuelMember','pbr:NaphthaMember','pbr:FuelOiIincludingBunkerFuelMember',
                    'pbr:OtherOilProductsMember'}:
                row['parent']=_oil_total
            if row['group']=='product' and row['member'] in {
                    name+'/pbr:ForeignMarketMember' for name in
                    ('pbr:CrudeOilsMember','pbr:FuelOiIincludingBunkerFuelMember','pbr:OtherOilProductsMember')}:
                row['parent']='pbr:ExportsMember/pbr:ForeignMarketMember'
            if row['group']=='geography' and row['member'] not in {'pbr:DomesticMarketMember','pbr:ForeignMarketMember'}:
                row['parent']='pbr:ForeignMarketMember'
        if symbol=='SHEL' and cik==1306965 and row['member']=='country:GB':
            row['parent']='srt:EuropeMember'
        if symbol=='BP' and cik==313807 and row['member']=='ifrs-full:CountryOfDomicileMember':
            row['parent']='bp:NonUSMember'
        if symbol=='XOM' and cik==34088 and row['group']=='segment':
            row['total']=None
            row['share_exclusion']='영업 부문별 외부 판매이며 총 수익과 범위가 다릅니다. 8개 행 합계 323,820,000,000 USD와 본사 판매 85,000,000 USD를 합친 판매 수익 323,905,000,000 USD는 지분법 이익·기타 수익을 포함한 332,238,000,000 USD와 구별합니다.'
    return rows


def presentation_group(row, symbol, cik):
    if ((symbol,cik)==('XOM',34088) and reviewed(row,symbol)
            and (symbol,cik,row['member']) in LABELS
            and '/' not in row['member']):
        return 'revenue_type'
    return row['group']


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    if (symbol,cik,group,start,end)==('XOM',34088,'revenue_type','2025-01-01','2025-12-31') and origin['url'].split('#')[0]==DOCUMENTS['XOM']:
        return tag=='us-gaap:Revenues'
    return True
