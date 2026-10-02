"""Exact, issuer-bound coordinates checked in FY2025 energy segment tables.

Chevron reports external sales by both segment and geography. Retain both actual
XBRL member names in a composite key; never silently drop a geographic dimension.
Valero's product facts are qualified by the associated reported segment.
"""
COORDINATES = {}
LABELS = {}

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
}


def dimensions(pairs, symbol, cik):
    # These issuers put external corporate revenue on a consolidation axis.
    # Never accept the operating-segment totals or elimination coordinates here.
    if ((symbol, cik) in {('MPC', 1510295), ('PSX', 1534701)}
            and pairs == [('srt:ConsolidationItemsAxis', 'us-gaap:CorporateNonSegmentMember')]):
        return 'segment', 'us-gaap:CorporateNonSegmentMember'
    if len(pairs) != 2 or len(set(pairs)) != 2:
        return None
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def compound_member(member, symbol, cik):
    return '/' in member and (symbol, cik, member) in LABELS


def separate_revenue_type(row, symbol, cik):
    # A narrative subset of Other revenues is not an additional product bucket.
    # Bound this reading to the reviewed filing/period, including old cached rows.
    return (symbol == 'DINO' and cik == 1915657 and row['group'] == 'product'
            and row['member'] == 'dino:RenewableIdentificationNumbersRINsMember'
            and row['start'] == '2025-01-01' and row['end'] == '2025-12-31'
            and row['source']['url'].split('#')[0] ==
            'https://www.sec.gov/Archives/edgar/data/1915657/000191565726000016/dino-20251231.htm')
