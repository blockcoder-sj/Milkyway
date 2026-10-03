"""Reviewed producer revenue tables; preserve products, resales and other income.

Coordinates belong to one issuer and the complete original axis combination.
Presentation exceptions require the exact reviewed annual document and period.
"""
DOCUMENTS = {
    ('APA', 1841666): 'https://www.sec.gov/Archives/edgar/data/1841666/000184166626000015/apa-20251231.htm',
    ('CHRD', 1486159): 'https://www.sec.gov/Archives/edgar/data/1486159/000148615926000005/chrd-20251231.htm',
    ('OVV', 1792580): 'https://www.sec.gov/Archives/edgar/data/1792580/000119312526064309/ovv-20251231.htm',
    ('MGY', 1698990): 'https://www.sec.gov/Archives/edgar/data/1698990/000169899026000005/mgy-20251231.htm',
    ('MTDR', 1520006): 'https://www.sec.gov/Archives/edgar/data/1520006/000152000626000002/mtdr-20251231.htm',
    ('PR', 1658566): 'https://www.sec.gov/Archives/edgar/data/1658566/000165856626000035/pr-20251231.htm',
    ('SM', 893538): 'https://www.sec.gov/Archives/edgar/data/893538/000089353826000032/sm-20251231.htm',
    ('CRC', 1609253): 'https://www.sec.gov/Archives/edgar/data/1609253/000160925326000051/crc-20251231.htm',
    ('CRGY', 1866175): 'https://www.sec.gov/Archives/edgar/data/1866175/000186617526000026/crgy-20251231.htm',
    ('GPOR', 874499): 'https://www.sec.gov/Archives/edgar/data/874499/000162828026011487/gpor-20251231.htm',
    ('CRK', 23194): 'https://www.sec.gov/Archives/edgar/data/23194/000119312526059001/crk-20251231.htm',
    ('CNX', 1070412): 'https://www.sec.gov/Archives/edgar/data/1070412/000107041226000038/cnx-20251231.htm',
    ('BKV', 1838406): 'https://www.sec.gov/Archives/edgar/data/1838406/000162828026015661/bkv-20251231.htm',
    ('MUR', 717423): 'https://www.sec.gov/Archives/edgar/data/717423/000162828026011709/mur-20251231.htm',
    ('NOG', 1104485): 'https://www.sec.gov/Archives/edgar/data/1104485/000110448526000008/nog-20251231.htm',
    ('VTS', 1944558): 'https://www.sec.gov/Archives/edgar/data/1944558/000194455826000009/vitesse-20251231.htm',
}
COORDINATES = {}
LABELS = {}


def _add(symbol, cik, pairs, group, member, label):
    COORDINATES[symbol, cik, frozenset(pairs)] = group, member
    LABELS[symbol, cik, member] = label


def _members(symbol, cik, axis, group, values):
    for member, label in values.items():
        _add(symbol, cik, [(axis, member)], group, member, label)


PRODUCTS = {
    ('CHRD', 1486159): {
        'chrd:OilProductionMember': '자체 원유 생산·판매',
        'chrd:PurchasedOilSalesMember': '매입 원유 재판매',
        'chrd:NaturalGasAndNaturalGasLiquidServicesMember': '자체 천연가스·NGL',
        'chrd:PurchasedGasSalesMember': '매입 천연가스 재판매',
    },
    ('MGY', 1698990): {
        'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'srt:NaturalGasReservesMember': '천연가스',
        'srt:NaturalGasLiquidsReservesMember': 'NGL',
    },
    ('MTDR', 1520006): {
        'srt:OilReservesMember': '자체 원유',
        'srt:NaturalGasReservesMember': '자체 천연가스',
        'us-gaap:NaturalGasMidstreamMember': '집하·처리·물 서비스 · 외부',
        'mtdr:NaturalGasSalesMember': '매입 천연가스 재판매',
    },
    ('PR', 1658566): {
        'srt:CrudeOilMember': '원유',
        'srt:NaturalGasLiquidsReservesMember': 'NGL',
        'srt:NaturalGasReservesMember': '천연가스',
        'us-gaap:OilAndGasPurchasedMember': '매입 원유·가스 재판매',
    },
    ('SM', 893538): {
        'srt:CrudeOilMember': '원유', 'srt:NaturalGasReservesMember': '천연가스',
        'srt:NaturalGasLiquidsReservesMember': 'NGL',
    },
    ('CRGY', 1866175): {
        'srt:OilReservesMember': '원유', 'us-gaap:NaturalGasProductionMember': '천연가스',
        'srt:NaturalGasLiquidsReservesMember': 'NGL', 'crgy:MidstreamAndOtherMember': '집하·기타',
    },
    ('GPOR', 874499): {
        'us-gaap:NaturalGasProductionMember': '천연가스',
        'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'gpor:NaturalgasliquidsalesMember': 'NGL',
    },
    ('CRK', 23194): {
        'us-gaap:NaturalGasProductionMember': '자체 천연가스',
        'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'crk:GasServicesMember': '매입 가스 재판매·타사 집하·처리',
    },
    ('CNX', 1070412): {
        'srt:NaturalGasReservesMember': '천연가스',
        'cnx:NGLsMember': 'NGL', 'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'us-gaap:OilAndGasPurchasedMember': '매입 가스 재판매',
    },
    ('BKV', 1838406): {
        'srt:NaturalGasReservesMember': '천연가스',
        'srt:NaturalGasLiquidsReservesMember': 'NGL', 'srt:OilReservesMember': '원유',
        'us-gaap:NaturalGasMidstreamMember': '집하·처리 서비스',
        'bkv:MarketingMember': '판매 대행',
        'bkv:RelatedPartyAndOtherMember': '특수관계자 서비스·기타 계약 수입',
    },
    ('MUR', 717423): {
        'srt:OilReservesMember': '원유', 'srt:NaturalGasReservesMember': '천연가스',
        'srt:NaturalGasLiquidsReservesMember': 'NGL',
    },
    ('NOG', 1104485): {
        'srt:OilReservesMember': '원유', 'nog:NaturalGasandNGLMember': '천연가스·NGL',
        'us-gaap:ProductAndServiceOtherMember': '기타 고객 계약 수입',
    },
    ('VTS', 1944558): {
        'srt:OilReservesMember': '원유', 'srt:NaturalGasReservesMember': '천연가스',
    },
}
for (symbol, cik), values in PRODUCTS.items():
    _members(symbol, cik, 'srt:ProductOrServiceAxis', 'product', values)

# APA's oil/gas/NGL production has a qualifying production-vs-purchase axis.
for member, label in {
    'srt:OilReservesMember': '자체 원유', 'srt:NaturalGasReservesMember': '자체 천연가스',
    'srt:NaturalGasLiquidsReservesMember': '자체 NGL',
}.items():
    _add('APA', 1841666, [('srt:ProductOrServiceAxis', 'apa:OilAndGasExcludingPurchasedMember'),
        ('srt:ReserveQuantitiesByTypeOfReserveAxis', member)], 'product', member, label)
_members('APA', 1841666, 'srt:ProductOrServiceAxis', 'product', {
    'us-gaap:OilAndGasPurchasedMember': '매입 원유·가스 재판매',
})
for member, label in {
    'apa:SegmentUnitedStatesMember': '미국 · 자체 생산',
    'apa:SegmentEgyptMember': '이집트 · 자체 생산 · 비지배지분 포함',
    'apa:SegmentNorthSeaMember': '북해 · 자체 생산',
}.items():
    _add('APA', 1841666, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('srt:ProductOrServiceAxis', 'apa:OilAndGasExcludingPurchasedMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', member)], 'geography', member, label)

# Ovintiv uses MajorCustomersAxis for product rows; anonymous purchaser members
# and the purchased-goods subtotal are not additional production products.
for member, label in {
    'ovv:OilOneMember': '자체 원유', 'srt:NaturalGasReservesMember': '자체 천연가스',
    'srt:NaturalGasLiquidsReservesMember': '자체 NGL',
}.items():
    _add('OVV', 1792580, [('srt:ProductOrServiceAxis', member),
        ('srt:MajorCustomersAxis', 'ovv:ProductRevenueMember')], 'product', member, label)
_members('OVV', 1792580, 'srt:ProductOrServiceAxis', 'product', {
    'ovv:NaturalGasGatheringProcessingAndOtherServiceMember': '집하·처리·기타 서비스',
})
_members('OVV', 1792580, 'srt:MajorCustomersAxis', 'product', {
    'ovv:SalesOfPurchasedProductMember': '매입 제품 재판매',
})
for member, label in {
    'ovv:UsaOperationsExcludingIntercompanySegmentTransactionsMember': '미국 · 외부 고객 계약',
    'ovv:CanadianOperationsExcludingIntercompanySegmentTransactionsMember': '캐나다 · 외부 고객 계약',
}.items():
    _add('OVV', 1792580, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', member)], 'geography', member, label)
for member, label in {
    'ovv:UsaOperationsMember': '미국 · 파생상품 포함',
    'ovv:CanadianOperationsMember': '캐나다 · 파생상품 포함',
}.items():
    _add('OVV', 1792580, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', member)], 'segment', member, label)
_members('OVV', 1792580, 'srt:ConsolidationItemsAxis', 'segment', {
    'us-gaap:CorporateNonSegmentMember': '본사·기타 · 파생상품 포함',
})
_members('SM', 893538, 'srt:StatementGeographicalAxis', 'geography', {
    'sm:MidlandBasinMember': 'Midland Basin · 합병 전',
    'sm:SouthTexasMember': 'South Texas · 합병 전', 'sm:UintaBasinMember': 'Uinta Basin · 합병 전',
})
for member, label in {
    'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
    'us-gaap:NaturalGasProductionMember': '천연가스',
    'us-gaap:PublicUtilitiesInventoryPropaneMember': 'NGL · 본문 제품명',
}.items():
    _add('CRC', 1609253, [('srt:ProductOrServiceAxis', member),
        ('us-gaap:StatementBusinessSegmentsAxis', 'crc:OilAndNaturalGasSegmentMember')],
        'product', member, label)
_members('CRK', 23194, 'srt:ProductOrServiceAxis', 'revenue_type', {
    'crk:GainOnSaleOfAssetsMember': '자산 매각이익 · 고객 제품 판매 아님',
})
_members('BKV', 1838406, 'srt:StatementGeographicalAxis', 'geography', {
    'stpr:PA': 'Pennsylvania · 계약 수입', 'stpr:TX': 'Texas · 계약 수입',
})
for member, label in {
    'mur:UnitedStatesSegmentMember': '미국 · 반올림 부문 금액',
    'mur:CanadaSegmentMember': '캐나다 · 반올림 부문 금액',
    'mur:OtherCountriesSegmentMember': '기타 국가 · 반올림 부문 금액',
}.items():
    _add('MUR', 717423, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('srt:ProductOrServiceAxis', 'us-gaap:OilAndGasExplorationAndProductionMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', member)], 'segment', member, label)


def dimensions(pairs, symbol, cik):
    if len(set(pairs)) != len(pairs):
        return None
    return COORDINATES.get((symbol, cik, frozenset(pairs)))


def reviewed(row, symbol, cik):
    return ((row['start'], row['end']) == ('2025-01-01', '2025-12-31')
        and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    if not reviewed(dict(start=start, end=end, source=origin), symbol, cik):
        return True
    expected = ('us-gaap:Revenues' if symbol in {'APA', 'MGY'} or (symbol == 'OVV' and group == 'segment')
        else 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax' if symbol == 'SM'
        else 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax')
    return tag == expected


def canonical(rows, symbol, cik):
    allowed = {member for (s, identity, _), (_, member) in COORDINATES.items() if (s, identity) == (symbol, cik)}
    # The parser also found the FY2024 whole-business repeat under GPOR's
    # sole ReportableSegmentsMember. It is not a business composition bucket.
    def prior_total(row):
        return ((symbol, cik) == ('GPOR', 874499)
            and row['source']['url'].split('#')[0] == DOCUMENTS['GPOR', 874499]
            and (row['start'], row['end']) == ('2024-01-01', '2024-12-31')
            and row['member'] == 'gpor:ReportableSegmentsMember'
            and row['metric'] == 'us-gaap:Revenues' and row['unit'] == 'USD')
    return [r for r in rows if not prior_total(r)
            and (not reviewed(r, symbol, cik) or r['member'] in allowed)]


def presentation_group(row, symbol, cik):
    if ((symbol, cik) == ('CRK', 23194) and reviewed(row, symbol, cik)
            and row['member'] == 'crk:GainOnSaleOfAssetsMember'):
        return 'revenue_type'
    return row['group']


def annotate(rows, symbol, cik):
    for row in rows:
        if not reviewed(row, symbol, cik):
            continue
        if symbol == 'APA':
            row['share_exclusion'] = ('제품 보기의 생산 매출 7,229,000,000 USD와 매입 재판매 1,691,000,000을 구분합니다. '
                '지역 보기는 생산 매출만 포함하며 이집트 비지배지분도 연결됩니다. 수입·기타이익 합계 9,220,000,000과 같은 분모가 아닙니다.')
        if symbol == 'CRK':
            row['share_exclusion'] = ('원문 합계 2,220,289,000 USD의 매출 태그에는 자산 매각이익 291,938,000이 포함돼 있습니다. '
                '고객 제품·서비스 합계 1,928,351,000과 매각이익을 합친 제품 구성비를 표시하지 않습니다.')
            if row['member'] == 'crk:GainOnSaleOfAssetsMember':
                row['total'] = None
        if symbol == 'MUR' and row['group'] == 'segment':
            row['share_exclusion'] = ('부문 금액은 소수 첫째 자리 백만 USD로 반올림되어 합계 2,689,800,000과 '
                '정확한 계약 매출 2,689,845,000이 45,000 차이 납니다. 차이를 임의 배분하지 않습니다.')
        if symbol == 'NOG':
            row['share_exclusion'] = ('원유·가스·NGL 2,081,288,000 USD와 기타 고객 계약 수입 13,771,000을 구분합니다. '
                '파생상품 손익을 포함한 전체 수입 2,475,723,000과 같은 분모로 계산하지 않습니다.')
    return rows
