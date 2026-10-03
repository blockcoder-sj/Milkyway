"""Reviewed small/offshore producer and water-service revenue coordinates.

Actual issuer, complete axes, document, metric and annual period stay attached.
Subtotals, royalties, intersegment and negative net receipts remain separate.
"""
DOCUMENTS = {
    ('INR', 2029118): 'https://www.sec.gov/Archives/edgar/data/2029118/000202911826000014/inr-20251231.htm',
    ('GFR', 1966287): 'https://www.sec.gov/Archives/edgar/data/1966287/000121390026027268/ea028059001ex99-2.htm',
    ('EGY', 894627): 'https://www.sec.gov/Archives/edgar/data/894627/000089462726000013/egy-20251231.htm',
    ('GPRK', 1464591): 'https://www.sec.gov/Archives/edgar/data/1464591/000110465926037819/gprk-20251231x20f.htm',
    ('GTE', 1273441): 'https://www.sec.gov/Archives/edgar/data/1273441/000127344126000010/gte-20251231.htm',
    ('KOS', 1509991): 'https://www.sec.gov/Archives/edgar/data/1509991/000150999126000017/kos-20251231.htm',
    ('TALO', 1724965): 'https://www.sec.gov/Archives/edgar/data/1724965/000119312526067807/talo-20251231.htm',
    ('WTI', 1288403): 'https://www.sec.gov/Archives/edgar/data/1288403/000110465926028315/wti-20251231x10k.htm',
    ('DEC', 1922446): 'https://www.sec.gov/Archives/edgar/data/1922446/000192244626000020/dec-20251231.htm',
    ('REPX', 1001614): 'https://www.sec.gov/Archives/edgar/data/1001614/000100161426000011/rep-20251231.htm',
    ('HPK', 1792849): 'https://www.sec.gov/Archives/edgar/data/1792849/000143774926007770/hpe20251231_10k.htm',
    ('SD', 1349436): 'https://www.sec.gov/Archives/edgar/data/1349436/000162828026015318/sd-20251231.htm',
    ('PED', 1141197): 'https://www.sec.gov/Archives/edgar/data/1141197/000165495426003098/ped_10k.htm',
    ('EPSN', 1726126): 'https://www.sec.gov/Archives/edgar/data/1726126/000110465926035794/epsn-20251231x10k.htm',
    ('TXO', 1559432): 'https://www.sec.gov/Archives/edgar/data/1559432/000119312526076813/txo-20251231.htm',
    ('WBI', 2064947): 'https://www.sec.gov/Archives/edgar/data/2064947/000119312526106541/wbi-20251231.htm',
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
    ('INR', 2029118): {'srt:OilReservesMember': '원유',
        'srt:NaturalGasReservesMember': '천연가스', 'srt:NaturalGasLiquidsReservesMember': 'NGL'},
    ('GFR', 1966287): {'gfr:DilutedBitumenSalesMember': '희석 역청 · 로열티 차감 전',
        'gfr:NonDilutedBitumenSalesMember': '비희석 역청 · 로열티 차감 전'},
    ('TALO', 1724965): {'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'us-gaap:NaturalGasProductionMember': '천연가스', 'srt:NaturalGasLiquidsReservesMember': 'NGL'},
    ('WTI', 1288403): {'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'us-gaap:NaturalGasProductionMember': '천연가스', 'srt:NaturalGasLiquidsReservesMember': 'NGL',
        'us-gaap:ProductAndServiceOtherMember': '기타 판매'},
    ('DEC', 1922446): {'srt:NaturalGasReservesMember': '천연가스',
        'srt:NaturalGasPerThousandCubicFeetMember': 'NGL · 원문 제품명',
        'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'us-gaap:NaturalGasMidstreamMember': '집하·운송', 'us-gaap:ProductAndServiceOtherMember': '기타 서비스'},
    ('REPX', 1001614): {'srt:OilReservesMember': '원유 · 순판매',
        'srt:NaturalGasReservesMember': '천연가스 · 집하·처리·운송비 차감 후',
        'srt:NaturalGasLiquidsReservesMember': 'NGL · 집하·처리·운송비 차감 후'},
    ('HPK', 1792849): {'hpk:CrudeOilSalesMember': '원유', 'hpk:NaturalGasAndNGLSalesMember': '천연가스·NGL'},
    ('EPSN', 1726126): {'srt:NaturalGasReservesMember': '천연가스',
        'srt:NaturalGasLiquidsReservesMember': 'NGL', 'us-gaap:OilAndCondensateMember': '원유·콘덴세이트',
        'epsn:GasGatheringAndCompressionMember': '외부 집하·압축'},
    ('TXO', 1559432): {'us-gaap:OilAndCondensateMember': '원유·콘덴세이트 · 고객 계약',
        'srt:NaturalGasLiquidsReservesMember': 'NGL · 고객 계약', 'srt:NaturalGasReservesMember': '천연가스 · 고객 계약'},
}
for (symbol, cik), values in PRODUCTS.items():
    _members(symbol, cik, 'ifrs-full:ProductsAndServicesAxis' if symbol == 'GFR' else 'srt:ProductOrServiceAxis', 'product', values)
_members('INR', 2029118, 'srt:ProductOrServiceAxis', 'revenue_type',
    {'inr:MidstreamActivitiesMember': '외부 중류 수입 · 상품 판매와 별도 지표'})
_members('GFR', 1966287, 'ifrs-full:ProductsAndServicesAxis', 'revenue_type',
    {'gfr:RoyaltiesMember': '로열티 차감액 · 양수 원문 금액'})
_members('SD', 1349436, 'srt:ReserveQuantitiesByTypeOfReserveAxis', 'product',
    {'srt:OilReservesMember': '원유', 'srt:NaturalGasReservesMember': '천연가스',
     'srt:NaturalGasLiquidsReservesMember': 'NGL'})
_members('PED', 1141197, 'us-gaap:StatementBusinessSegmentsAxis', 'product',
    {'ped:OilSalesMember': '원유', 'ped:NaturalGasSalesMember': '천연가스', 'ped:NaturalGasLiquidsSalesMember': 'NGL'})
for member, label in {'egy:GabonSegmentMember': 'Gabon', 'egy:EgyptMember': 'Egypt',
                     'egy:CanadaMember': 'Canada · 2025 매각 예정 자산', 'egy:CoteDIvoire1Member': "Côte d’Ivoire"}.items():
    _add('EGY', 894627, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', member)], 'geography', member, label)
for member, label in {'country:CO': 'Colombia', 'country:AR': 'Argentina',
                     'country:BR': 'Brazil · 2025 처분 사업', 'country:EC': 'Ecuador · 2025 처분 사업'}.items():
    _members('GPRK', 1464591, 'ifrs-full:GeographicalAreasAxis', 'geography', {member: label})
_add('GPRK', 1464591, [('ifrs-full:GeographicalAreasAxis', 'gprk:IfrsCorporateMember'),
    ('ifrs-full:SegmentsAxis', 'ifrs-full:AllOtherSegmentsMember')], 'geography', 'gprk:IfrsCorporateMember', '본사·기타')
for country, label in {'country:CO': 'Colombia', 'country:EC': 'Ecuador', 'country:CA': 'Canada'}.items():
    _members('GTE', 1273441, 'srt:StatementGeographicalAxis', 'geography', {country: label})
_members('GTE', 1273441, 'srt:ReserveQuantitiesByTypeOfReserveAxis', 'product',
    {'srt:CrudeOilMember': '원유', 'srt:NaturalGasReservesMember': '천연가스', 'srt:NaturalGasLiquidsReservesMember': 'NGL'})
for member, label in {'country:GH': 'Ghana · 계약 판매', 'country:GQ': 'Equatorial Guinea · 계약 판매',
                     'kos:MauritaniaSenegalMember': 'Mauritania·Senegal · 계약 판매',
                     'kos:GulfOfAmericaMember': 'Gulf of America · 계약 판매'}.items():
    _add('KOS', 1509991, [('srt:ProductOrServiceAxis', 'us-gaap:OilAndGasMember'),
        ('srt:StatementGeographicalAxis', member)], 'geography', 'us-gaap:OilAndGasMember/' + member, label)
for member, label in {'kos:GhanaSegmentMember': 'Ghana · 파생상품 포함',
                     'kos:EquatorialGuineaSegmentMember': 'Equatorial Guinea · 파생상품 포함',
                     'kos:MauritaniaAndSenegalMember': 'Mauritania·Senegal · 파생상품 포함',
                     'kos:GulfOfAmericaMember': 'Gulf of America · 파생상품 포함'}.items():
    _add('KOS', 1509991, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', member)], 'segment', member, label)
for member, label in {'epsn:UpstreamUsaSegmentMember': '상류 · 외부 판매',
                     'epsn:GasGatheringSegmentMember': '집하·압축 · 내부 거래 포함'}.items():
    _add('EPSN', 1726126, [('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember'),
        ('us-gaap:StatementBusinessSegmentsAxis', member)], 'segment', member, label)
for member, label in {'wbi:ProducedWaterHandlingMember': '생산수 처리',
                     'wbi:WaterSolutionsMember': '용수·재사용 서비스', 'wbi:OtherRevenuesMember': '기타 서비스'}.items():
    for related, role in {'us-gaap:NonrelatedPartyMember': '제삼자', 'us-gaap:RelatedPartyMember': '특수관계자'}.items():
        _add('WBI', 2064947, [('srt:ProductOrServiceAxis', member),
            ('us-gaap:RelatedPartyTransactionsByRelatedPartyAxis', related)],
            'product', member + '/' + related, label + ' · ' + role)
_members('WBI', 2064947, 'srt:ProductOrServiceAxis', 'revenue_type',
    {'wbi:ProducedWaterHandlingRevenuesExcludingSkimOilMember': '생산수 서비스 · 회수 원유 제외',
     'wbi:SkimOilMember': '생산수에서 회수한 원유 · 생산수 처리 내 포함'})


def dimensions(pairs, symbol, cik):
    return None if len(set(pairs)) != len(pairs) else COORDINATES.get((symbol, cik, frozenset(pairs)))


def reviewed(row, symbol, cik):
    return ((row['start'], row['end']) == ('2025-01-01', '2025-12-31')
        and row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik)))


def signed_value(tag, context, origin, symbol, cik):
    start, end, group, member = context
    return ((symbol, cik) == ('REPX', 1001614) and group == 'product'
        and member in {'srt:NaturalGasReservesMember', 'srt:NaturalGasLiquidsReservesMember'}
        and tag == 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
        and reviewed(dict(start=start, end=end, source=origin), symbol, cik))


def metric_allowed(tag, group, start, end, origin, symbol, cik):
    if not reviewed(dict(start=start, end=end, source=origin), symbol, cik):
        return True
    expected = ('ifrs-full:Revenue' if symbol in {'GFR', 'GPRK'}
        else 'us-gaap:Revenues' if symbol == 'EGY' or (symbol == 'INR' and group == 'revenue_type')
             or (symbol == 'KOS' and group == 'segment')
        else 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax' if symbol in {'TALO','PED','EPSN'}
        else 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax')
    return tag == expected


def canonical(rows, symbol, cik):
    allowed = {member for (s, identity, _), (_, member) in COORDINATES.items() if (s, identity) == (symbol, cik)}
    def legacy_total(row):
        exact = row['source']['url'].split('#')[0] == DOCUMENTS.get((symbol, cik))
        single = {('INR', 2029118): 'inr:ReportableSegmentMember',
                  ('TXO', 1559432): 'txo:ReportableSegmentMember'}
        prior_service = ((symbol, cik) == ('REPX', 1001614)
            and row['member'] == 'us-gaap:ServiceMember'
            and (row['start'], row['end']) == ('2024-01-01', '2024-12-31'))
        return exact and (row['member'] == single.get((symbol, cik)) or prior_service)
    selected = [r for r in rows if not legacy_total(r)
        and (not reviewed(r, symbol, cik) or (r['member'] in allowed
            and metric_allowed(r['metric'], r['group'], r['start'], r['end'],
                               r['source'], symbol, cik)))]
    # EGY repeats the same consolidated geographic amounts in its segment and
    # geographic tables. Normalize first, retain one agreeing coordinate, and
    # omit a conflicting coordinate rather than pick an arbitrary anchor.
    values = {}
    for row in selected:
        if reviewed(row, symbol, cik):
            key = tuple(row[k] for k in ('group', 'member', 'start', 'end', 'unit', 'metric'))
            values.setdefault(key, set()).add(row['value'])
    result, seen = [], set()
    for row in selected:
        if reviewed(row, symbol, cik):
            key = tuple(row[k] for k in ('group', 'member', 'start', 'end', 'unit', 'metric'))
            if key in seen or len(values[key]) != 1:
                continue
            seen.add(key)
        result.append(row)
    return result


def presentation_group(row, symbol, cik):
    if reviewed(row, symbol, cik):
        mapping = {m: g for (s, identity, _), (g, m) in COORDINATES.items() if (s, identity) == (symbol, cik)}
        return mapping.get(row['member'], row['group'])
    return row['group']


def annotate(rows, symbol, cik):
    explanations = {
        'INR': '제품 판매 350,375,000 USD와 외부 중류 6,056,000은 서로 다른 매출 지표이며 합계 356,431,000입니다. 제품 비중은 제품 계약 합계 기준입니다.',
        'GFR': '제품 합계 603,303,000 CAD는 로열티 차감 전 판매입니다. 로열티 18,908,000 차감 후 연결 매출 584,395,000과 같은 분모가 아니므로 비중을 생략합니다.',
        'REPX': '원유 398,341,000 USD, 가스 -3,322,000, NGL -3,039,000의 순판매 합계는 391,980,000입니다. 가스·NGL 집하·처리·운송비가 해당 판매액보다 커 음수이며 구성비를 생략합니다.',
        'DEC': '상품 판매 1,538,821,000 USD·외부 집하 40,492,000·기타 서비스 32,142,000과 파생상품 포함 연결 수입 1,829,142,000의 범위가 다릅니다. 상품 소계를 제품에 다시 더하지 않습니다.',
        'KOS': '지역 계약 판매 합계 1,297,846,000 USD와 파생상품 포함 지역 수입 합계 1,288,352,000은 다릅니다. 두 보기는 합산하지 않습니다.',
        'EPSN': '집하 부문 8,548,504 USD에 내부 거래가 포함됩니다. 내부 거래 1,864,769 제거 후 외부 집하 6,683,735이며 상품 44,903,821과 연결 매출 51,587,556을 이룹니다.',
        'TXO': '고객 계약 판매 363,147,000 USD와 파생상품 포함 매출 401,012,000은 다른 범위입니다. 공동사업 Cross Timbers는 지분비례 연결입니다.',
        'WBI': '제품 보기는 제삼자·특수관계자 매출을 분리한 합계 525,553,000 USD입니다. 매출 유형은 생산수 처리 내부 분해 471,626,000의 부분 정보이며 제품 보기에 다시 더하지 않습니다.',
    }
    for row in rows:
        if not reviewed(row, symbol, cik):
            continue
        explanation = explanations.get(symbol)
        explain = (symbol not in {'INR','EPSN','WBI','KOS'}
            or (symbol == 'INR' and row['group'] == 'revenue_type')
            or (symbol == 'EPSN' and row['group'] == 'segment')
            or (symbol == 'WBI' and row['group'] == 'revenue_type')
            or (symbol == 'KOS' and row['group'] == 'geography'))
        if explanation and explain:
            row['share_exclusion'] = explanation
        if symbol in {'GFR','REPX'} or (symbol == 'WBI' and row['group'] == 'revenue_type'):
            row['total'] = None
        if symbol == 'EPSN' and row['group'] == 'segment':
            row['includes_intersegment'], row['total'] = True, None
    return rows
