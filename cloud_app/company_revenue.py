"""Bounded annual revenue slices from the issuer's inline XBRL, without AI.

Only standard revenue metrics and one-dimensional contexts are supported. A
denominator must be the same document/metric/currency/period, with no dimensions.
Displayed slices are not summed: products, segments and regions can overlap.
"""
import datetime as dt
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlsplit

from .company_filings import document

METRICS = (
    'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
    'us-gaap:Revenues', 'us-gaap:SalesRevenueNet', 'ifrs-full:Revenue',
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
}


def label(member):
    local = member.split(':')[-1]
    local = re.sub(r'Member$', '', local)
    return LABELS.get(local, re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', local))[:160]


def number(fact):
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
        if not value.is_finite() or not 0 <= value <= Decimal('1e16'):
            return None
        return value
    except (InvalidOperation, ValueError, OverflowError):
        return None


def parse_revenue(raw, origin, symbol, today=None):
    soup = document(raw)
    today = today or dt.datetime.now(dt.timezone.utc).date()
    match = re.fullmatch(r'/Archives/edgar/data/(\d{1,10})/\d{18}/[A-Za-z0-9_.-]+', urlsplit(origin['url']).path)
    if not match:
        return []
    expected_cik = int(match[1])
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
        if len(members) > 1 or (members and members[0].get('dimension') not in AXES):
            continue
        group = AXES[members[0]['dimension']] if members else None
        member = members[0].get_text(strip=True) if members else ''
        if group == 'product' and member in {'us-gaap:ProductMember', 'us-gaap:ServiceMember', 'us-gaap:ServiceOtherMember'}:
            # An alternate product/service split is not a child of every named
            # product family. Keep it in its own view instead of double counting.
            group = 'revenue_type'
        if member and not re.fullmatch(r'[A-Za-z0-9_.-]{1,30}:[A-Za-z0-9_.-]{1,150}', member):
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
        candidates = [key for key in clean if key[4] == group]
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
            denominator = total if total and value <= total else None
            result.append(dict(group=group, member=key[5], label=label(key[5]),
                value=float(value), unit=key[1], start=key[2], end=key[3],
                total=float(denominator) if denominator else None, metric=key[0], parent=None,
                source={**origin, 'url': origin['url'] + ('#' + anchors[key] if key in anchors else '')}))
    # Verified hierarchy of NVIDIA's disclosed product table, only if the reported
    # annual values themselves reconcile. Other overlapping slices stay ungrouped.
    if symbol == 'NVDA':
        product = {row['member']: row for row in result if row['group'] == 'product'}
        parent = product.get('nvda:DataCenterMember')
        children = [product.get('nvda:ComputeMember'), product.get('nvda:NetworkingMember')]
        if parent and all(children) and abs(sum(row['value'] for row in children) - parent['value']) <= 1:
            for row in children:
                row['parent'] = parent['member']
    return result[:80]
