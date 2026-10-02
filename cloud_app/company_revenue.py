"""Bounded annual revenue slices from the issuer's inline XBRL, without AI.

Only standard revenue metrics and checked dimension combinations are supported. A
denominator must be the same document/metric/currency/period, with no dimensions.
Displayed slices are not summed: products, segments and regions can overlap.
"""
import datetime as dt
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlsplit

from .company_filings import document
from . import company_energy_revenue as energy

METRICS = (
    'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
    'us-gaap:Revenues', 'us-gaap:SalesRevenueNet', 'ifrs-full:Revenue',
    'ifrs-full:RevenueFromContractsWithCustomers',
    'ifrs-full:RevenueAndOperatingIncome',
    'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax',
)
AXES = {
    'srt:ProductOrServiceAxis': 'product',
    'us-gaap:StatementBusinessSegmentsAxis': 'segment',
    'srt:StatementGeographicalAxis': 'geography',
}
LABELS = {
    'DataCenter': '데이터센터', 'Compute': '컴퓨팅', 'Networking': '네트워킹',
    'Gaming': '게이밍', 'ProfessionalVisualization': '전문 시각화',
    'Automotive': '자동차', 'OEMAndOther': 'OEM·기타',
    'ComputeAndNetworkingSegment': '컴퓨팅·네트워킹', 'GraphicsSegment': '그래픽',
    'IPhone': '아이폰', 'iPhone': '아이폰', 'Mac': '맥', 'IPad': '아이패드',
    'iPad': '아이패드', 'Services': '서비스',
    'WearablesHomeandAccessories': '웨어러블·홈·액세서리',
    'WearablesHomeAndAccessories': '웨어러블·홈·액세서리',
    'ProductivityAndBusinessProcesses': '생산성·비즈니스 프로세스',
    'IntelligentCloud': '인텔리전트 클라우드',
    'MorePersonalComputing': '퍼스널 컴퓨팅',
    'DynamicsProductsAndCloudServices': 'Dynamics 제품·클라우드',
    'EnterpriseAndPartnerServices': '기업·파트너 서비스', 'LinkedInCorporation': 'LinkedIn',
    'MicrosoftThreeSixFiveCommercialProductsAndCloudServices': '기업용 Microsoft 365 제품·클라우드',
    'MicrosoftThreeSixFiveConsumerProductsAndCloudServices': '개인용 Microsoft 365 제품·클라우드',
    'OtherProductsAndServices': '기타 제품·서비스', 'SearchAdvertising': '검색 광고',
    'ServerProductsAndCloudServices': '서버 제품·클라우드', 'WindowsAndDevices': 'Windows·기기',
    'XBOX': 'Xbox', 'Product': '제품', 'ServiceOther': '서비스·기타', 'Service': '서비스',
    'NorthAmerica': '북미', 'International': '해외',
    'USMarket': '미국', 'InternationalOperatedMarkets': '해외 직접 운영 시장',
    'InternationalDevelopmentalLicensedMarketsandCorporate': '해외 개발·라이선스 시장 및 본사',
    'AmazonWebServices': 'AWS 클라우드', 'OnlineStores': '온라인 스토어',
    'PhysicalStores': '오프라인 스토어', 'ThirdPartySellerServices': '외부 판매자 서비스',
    'SubscriptionServices': '구독 서비스', 'AdvertisingServices': '광고 서비스',
    'CompanyOperatedRestaurants': '직영 레스토랑', 'FranchisedRestaurants': '가맹 레스토랑',
    'UnitedStates': '미국', 'UnitedStatesOfAmerica': '미국', 'US': '미국',
    'Taiwan': '대만', 'TW': '대만', 'China': '중국', 'CN': '중국',
    'ChinaIncludingHongKong': '중국·홍콩', 'Europe': '유럽', 'Japan': '일본',
    'JP': '일본', 'GreaterChina': '중화권', 'RestOfAsiaPacific': '기타 아시아태평양',
    'OtherCountries': '기타 국가', 'Other': '기타',
    'NonUs': '미국 외 지역',
    'SG': '싱가포르', 'KR': '한국', 'DE': '독일', 'GB': '영국',
    'Datacenter': '데이터센터', 'ClientAndGaming': '클라이언트·게이밍',
    'Client': '클라이언트', 'Embedded': '임베디드',
    'SemiconductorSolutions': '반도체 솔루션', 'InfrastructureSoftware': '인프라 소프트웨어',
    'Qct': 'QCT · 반도체 제품', 'QCT': 'QCT · 반도체 제품',
    'Qtl': 'QTL · 기술 라이선스', 'QTL': 'QTL · 기술 라이선스',
    'Qsi': 'QSI · 전략 투자', 'QSI': 'QSI · 전략 투자',
    'Handsets': '스마트폰', 'IoT': '사물인터넷', 'Iot': '사물인터넷',
    'ClientComputingGroupDatacenterAndAIAndNetworkAndEdge': 'Intel Products · 제품 사업 합계',
    'ClientComputingGroup': '클라이언트 컴퓨팅', 'DatacenterAndAI': '데이터센터·AI',
    'IntelFoundry': 'Intel Foundry · 제조', 'AllOtherSegments': '기타 사업',
    'ClientSolutions': '클라이언트 솔루션', 'InfrastructureSolutionsGroup': '인프라 솔루션',
    'AppliedGlobalServicesSegment': '설치 장비 서비스',
    'SemiconductorSystemsSegment': '반도체 제조 시스템',
    'CloudApplications': '클라우드 애플리케이션', 'CloudInfrastructure': '클라우드 인프라',
    'CloudRevenues': '클라우드 매출 합계', 'SoftwareRevenues': '소프트웨어 매출 합계',
    'SoftwareLicense': '소프트웨어 라이선스', 'SoftwareSupport': '소프트웨어 지원',
    'Hardware': '하드웨어', 'SubscriptionAndSupport': '구독·지원 합계',
    'Agentforce360PlatformSlackAndOther': 'Agentforce 360 플랫폼·Slack·기타',
    'IntegrationAndAnalytics': '시스템 연동·분석', 'MarketingAndCommerce': '마케팅·커머스',
    'Sales': '영업', 'ProfessionalServicesAndOther': '전문 서비스·기타',
    'ProfessionalServices': '전문 서비스', 'SubscriptionAndCirculation': '구독',
    'Subscription': '구독', 'Support': '지원', 'SubscriptionsAndServices': '구독·서비스',
    'DigitalMedia': '디지털 미디어', 'DigitalExperience': '디지털 경험',
    'PublishingAndAdvertising': '출판·광고', 'LicenseAndService': '라이선스·서비스',
    'TechnologyService': '기술 서비스',
    'FinancialServices': '금융 서비스', 'HybridCloud': '하이브리드 클라우드',
    'Server': '서버', 'CorporateInvestmentsAndOther': '본사 투자·기타',
    'CustomerSupportAndOther': '고객 지원·기타', 'System': '장비 시스템',
    'WaferInspection': '웨이퍼 검사', 'Patterning': '패턴 공정 관리',
    'SpecialtySemiconductorProcess': '특수 반도체 공정',
    'PCBAndComponentInspection': 'PCB·부품 검사',
    'Industrial': '산업용', 'Consumer': '소비자용', 'Communications': '통신',
    'ReportedSegment': '단일 보고 부문 합계', 'Analog': '아날로그',
    'EmbeddedProcessing': '임베디드 처리',
    'SubscriptionsandServices': '구독·서비스',
    'SubscriptionandSupport': '구독·지원 합계',
    'AgentforceIntegrationAndAgentforceAnalytics': 'Agentforce 연동·분석',
    'AgentforceMarketingAndAgentforceCommerce': 'Agentforce 마케팅·커머스',
    'AgentforceSales': 'Agentforce 영업', 'AgentforceService': 'Agentforce 고객 서비스',
    'ProfessionalServicesandOther': '전문 서비스·기타',
    'SubscriptionRevenue': '구독', 'HybridCloudSegment': '하이브리드 클라우드',
    'ServerSegment': '서버', 'CorporateAndOther': '본사·기타',
    'CustomerSupportandOther': '고객 지원·기타', 'OtherRevenue': '기타 매출',
    'ReportableSegment': '단일 보고 부문 합계',
}

ISSUER_LABELS = {
    ('NOW', 1373715): {'us-gaap:LicenseAndServiceMember': '구독 서비스',
                     'us-gaap:TechnologyServiceMember': '전문 서비스·기타'},
}
ADI_END_MARKETS = {'adi:' + member + 'Member' for member in
                   ('Industrial', 'Automotive', 'Communications', 'Consumer')}

# Checked against these issuers' filed annual segment tables on 2026-10-02.
# OperatingSegmentsMember is an explicit presentation qualifier, not permission
# to collapse arbitrary customer, region, elimination or product dimensions.
OPERATING_SEGMENTS = {'AMD': 2488, 'INTC': 50863, 'DELL': 1571996, 'AMAT': 6951, 'QCOM': 804328}
HIERARCHIES = {
    ('NVDA', 1045810, 'product'): {'nvda:DataCenterMember': ['nvda:ComputeMember', 'nvda:NetworkingMember']},
    ('AMD', 2488, 'segment'): {'amd:ClientAndGamingMember': ['amd:ClientMember', 'amd:GamingMember']},
    ('INTC', 50863, 'segment'): {'intc:ClientComputingGroupDatacenterAndAIAndNetworkAndEdgeMember':
                              ['intc:ClientComputingGroupMember', 'intc:DatacenterAndAIMember']},
    ('ORCL', 1341439, 'product'): {
        'orcl:CloudRevenuesMember': ['orcl:CloudApplicationsMember', 'orcl:CloudInfrastructureMember'],
        'orcl:SoftwareRevenuesMember': ['orcl:SoftwareLicenseMember', 'orcl:SoftwareSupportMember']},
    ('CRM', 1108524, 'product'): {'crm:SubscriptionandSupportMember': [
        'crm:Agentforce360PlatformSlackAndOtherMember',
        'crm:AgentforceIntegrationAndAgentforceAnalyticsMember',
        'crm:AgentforceMarketingAndAgentforceCommerceMember',
        'crm:AgentforceSalesMember', 'crm:AgentforceServiceMember']},
}
HIERARCHIES.update(energy.HIERARCHIES)


def source_cik(origin):
    """An issuer's reviewed rules cannot be activated by a lookalike URL."""
    try:
        parsed = urlsplit(origin.get('url', ''))
        valid = (parsed.scheme == 'https' and parsed.hostname in {'www.sec.gov', 'sec.gov'}
                 and not parsed.username and not parsed.password and parsed.port in (None, 443))
    except ValueError:
        return None
    if not valid:
        return None
    match = re.fullmatch(r'/Archives/edgar/data/(\d{1,10})/\d{18}/[A-Za-z0-9_.-]+', parsed.path)
    return int(match[1]) if match else None


def basis(row):
    return (row['group'], row['start'], row['end'], row['unit'], row['metric'],
            row['source']['url'].split('#')[0])


def dimensions(members, symbol, cik):
    pairs = [(item.get('dimension'), item.get_text(strip=True)) for item in members]
    reviewed = energy.dimensions(pairs, symbol, cik)
    if reviewed:
        return reviewed
    if len(pairs) == 2 and OPERATING_SEGMENTS.get(symbol) == cik:
        qualifier = ('srt:ConsolidationItemsAxis', 'us-gaap:OperatingSegmentsMember')
        if qualifier in pairs:
            remainder = [item for item in pairs if item != qualifier]
            if len(remainder) == 1 and remainder[0][0] == 'us-gaap:StatementBusinessSegmentsAxis':
                return 'segment', remainder[0][1]
        if symbol == 'AMD':
            # Exact product/segment pairs from AMD's FY2025 table, not a generic
            # multi-axis rule. Its Client and Gaming rows reconcile below.
            for product, segment in [('amd:ClientMember', 'amd:ClientAndGamingMember'),
                                     ('amd:GamingMember', 'amd:GamingMember')]:
                if set(pairs) == {('srt:ProductOrServiceAxis', product),
                                  ('us-gaap:StatementBusinessSegmentsAxis', segment)}:
                    return 'segment', product
    if len(pairs) > 1 or (pairs and pairs[0][0] not in AXES):
        return None
    if not pairs:
        return None, ''
    axis, member = pairs[0]
    group = AXES[axis]
    if group == 'product' and member in {'us-gaap:ProductMember', 'us-gaap:ServiceMember', 'us-gaap:ServiceOtherMember'}:
        group = 'revenue_type'
    return group, member


def hierarchy(rows, symbol, cik):
    """Set only reviewed parent links whose actual reported values reconcile."""
    for (issuer, identity, group), mapping in HIERARCHIES.items():
        if (issuer, identity) != (symbol, cik):
            continue
        by_basis = {}
        for row in rows:
            if row['group'] == group and source_cik(row['source']) == cik:
                by_basis.setdefault(basis(row), {}).setdefault(row['member'], []).append(row)
                if any(row['member'] in names for names in mapping.values()):
                    row['parent'] = None
        for candidates in by_basis.values():
            # Ambiguous cached duplicates are not a basis for a parent link.
            lookup = {name: values[0] for name, values in candidates.items() if len(values) == 1}
            for name, child_names in mapping.items():
                parent, children = lookup.get(name), [lookup.get(key) for key in child_names]
                if parent and all(children) and abs(sum(Decimal(str(row['value'])) for row in children)
                                                   - Decimal(str(parent['value']))) <= 1:
                    for row in children:
                        row['parent'] = name
    return rows


def present_revenue(rows, symbol):
    """Apply checked labels/bases to old caches too, without fetching or changing values."""
    result = []
    for value in rows:
        row = dict(value)
        cik = source_cik(row['source'])
        local = re.sub(r'Member$', '', row['member'].split(':')[-1])
        override = (energy.LABELS.get((symbol, cik, row['member']))
                    or ISSUER_LABELS.get((symbol, cik), {}).get(row['member']))
        if override or local in LABELS:
            row['label'] = override or LABELS[local]
        row['group'] = energy.presentation_group(row, symbol, cik)
        if energy.separate_revenue_type(row, symbol, cik):
            row['group'], row['parent'] = 'revenue_type', None
        if symbol == 'ADI' and cik == 6281 and row['group'] == 'segment' and row['member'] in ADI_END_MARKETS:
            row['group'] = 'end_market'
        if symbol == 'INTC' and cik == 50863 and row['group'] == 'segment':
            row['includes_intersegment'], row['total'] = True, None
        result.append(row)
    for cik in {source_cik(row['source']) for row in result} - {None}:
        hierarchy(result, symbol, cik)
        energy.annotate([row for row in result if source_cik(row['source']) == cik], symbol, cik)
    return energy.canonical_revenue(result, symbol)


def label(member):
    local = member.split(':')[-1]
    local = re.sub(r'Member$', '', local)
    return LABELS.get(local, re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', local))[:160]


def number(fact, *, signed=False):
    """Conservative support for numeric inline transformations, never eval."""
    raw = fact.get_text('', strip=True).replace('\u00a0', '').strip()
    transform = fact.get('format', '')
    if fact.get('xsi:nil', '').lower() in {'true', '1'} or len(raw) > 100:
        return None
    if transform in {'ixt:zerodash', 'ixt:zero-dash'} and raw in {'-', '—', '–'}:
        raw = '0'
    elif transform in {'ixt:num-dot-decimal', 'ixt:numdotdecimal'}:
        if not re.fullmatch(r'(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?', raw):
            return None
        raw = raw.replace(',', '')
    elif transform in {'ixt:num-comma-decimal', 'ixt:numcommadecimal'}:
        if not re.fullmatch(r'(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?', raw):
            return None
        raw = raw.replace('.', '').replace(',', '.')
    elif transform or not re.fullmatch(r'\d+(?:\.\d+)?', raw):
        return None
    try:
        scale = fact.get('scale', '0')
        if not re.fullmatch(r'-?\d{1,2}', scale) or not -12 <= int(scale) <= 12:
            return None
        if fact.get('sign', '') not in {'', '-'}:
            return None
        value = Decimal(raw) * (Decimal(10) ** int(scale))
        if fact.get('sign') == '-':
            value = -value
        lower = Decimal('-1e16') if signed else Decimal(0)
        if not value.is_finite() or not lower <= value <= Decimal('1e16'):
            return None
        return value
    except (InvalidOperation, ValueError, OverflowError):
        return None


def parse_revenue(raw, origin, symbol, today=None):
    soup = document(raw)
    today = today or dt.datetime.now(dt.timezone.utc).date()
    expected_cik = source_cik(origin)
    if expected_cik is None:
        return []
    contexts, units = {}, {}
    for unit in soup.find_all('xbrli:unit', limit=200):
        measures = unit.find_all('xbrli:measure')
        if len(measures) == 1 and not unit.find('xbrli:divide'):
            currency = measures[0].get_text(strip=True)
            if re.fullmatch(r'iso4217:[A-Z]{3}', currency):
                units[unit.get('id')] = currency.split(':')[1]
    for ctx in soup.find_all('xbrli:context', limit=10000):
        identifier = ctx.find('xbrli:identifier')
        if (not identifier or identifier.get('scheme') != 'http://www.sec.gov/CIK'
                or not re.fullmatch(r'\d{1,10}', identifier.get_text(strip=True))
                or int(identifier.get_text(strip=True)) != expected_cik
                or ctx.find('xbrldi:typedmember')):
            continue
        start, end = ctx.find('xbrli:startdate'), ctx.find('xbrli:enddate')
        if not start or not end or ctx.find('xbrli:instant'):
            continue
        try:
            first, last = dt.date.fromisoformat(start.text), dt.date.fromisoformat(end.text)
        except ValueError:
            continue
        if not 300 <= (last - first).days <= 400 or last > today:
            continue
        members = ctx.find_all('xbrldi:explicitmember')
        classified = dimensions(members, symbol, expected_cik)
        if classified is None:
            continue
        group, member = classified
        if member and not (re.fullmatch(r'[A-Za-z0-9_.-]{1,30}:[A-Za-z0-9_.-]{1,150}', member)
                           or energy.compound_member(member, symbol, expected_cik)):
            continue
        contexts[ctx.get('id')] = (start.text, end.text, group, member)
    # Duplicate reports of the same fact must agree; conflicting values are dropped.
    values, anchors = {}, {}
    for fact in soup.find_all('ix:nonfraction', limit=100000):
        tag, ctx, currency = fact.get('name'), contexts.get(fact.get('contextref')), units.get(fact.get('unitref'))
        if tag not in METRICS or not ctx or not currency:
            continue
        value = number(fact)
        if value is None:
            continue
        key = (tag, currency, *ctx)
        values.setdefault(key, set()).add(value)
        anchor = fact.get('id', '')
        if re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', anchor):
            anchors.setdefault(key, anchor)
    clean = {key: next(iter(rows)) for key, rows in values.items() if len(rows) == 1}
    result = []
    for group in ('product', 'segment', 'geography', 'revenue_type'):
        candidates = [key for key in clean if key[4] == group and
                      energy.metric_allowed(key[0], group, key[2], key[3], origin, symbol, expected_cik)]
        if not candidates:
            continue
        # One matching metric/currency/period per view. No mixing current and prior years.
        chosen = max(candidates, key=lambda key: (key[3], -METRICS.index(key[0]), key[2], key[1]))
        prefix = chosen[:4]
        total = clean.get((*prefix, None, ''))
        for key in sorted(candidates):
            if key[:4] != prefix:
                continue
            value = clean[key]
            internal = symbol == 'INTC' and expected_cik == 50863 and group == 'segment'
            denominator = total if total and value <= total and not internal else None
            result.append(dict(group=group, member=key[5], label=label(key[5]),
                value=float(value), unit=key[1], start=key[2], end=key[3],
                total=float(denominator) if denominator else None, metric=key[0], parent=None,
                includes_intersegment=internal,
                source={**origin, 'url': origin['url'] + ('#' + anchors[key] if key in anchors else '')}))
    return present_revenue(result, symbol)[:80]
