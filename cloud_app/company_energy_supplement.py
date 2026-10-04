"""Two concrete additions from a bounded follow-up of free primary filings."""
from .company_energy_sources import fact, report


def apply(public):
    origin = report('LBRT')
    public['LBRT']['revenue_mix'] = [dict(
        group='revenue_type', member=member, label=label, value=value, unit='USD',
        start='2025-01-01', end='2025-12-31', total=4006116000,
        metric=metric, source=origin,
        share_exclusion='관련자 여부에 따른 매출 구분입니다. 파쇄·모래·발전의 제품별 비중이 아닙니다.')
        for member, label, value, metric in (
            ('reported:NonrelatedRevenue', '비관련자 매출', 4000269000, 'reported:Revenue'),
            ('reported:RelatedRevenue', '관련자 매출', 5847000, 'reported:RevenueRelatedParties'))]
    public['LBRT'].setdefault('financial_context', []).append(fact(
        '추가 확인 · 관련자 매출 구분',
        'FY2025 손익계산서는 비관련자 매출 4,000,269,000 USD와 관련자 매출 5,847,000 USD를 '
        '구별하며 합계는 4,006,116,000 USD입니다. 단일 보고 부문이므로 이 구분을 '
        '파쇄·모래·발전 제품의 매출이나 연결 내부거래로 해석하지 않습니다.', origin))
    public['EU'].setdefault('financial_context', []).append(fact(
        '추가 확인 · 익명 고객 집중',
        'FY2025 주석 18은 외부 고객 세 곳의 매출을 각각 27,231,000·10,980,000·4,944,000 USD로 '
        '보고하며 합계가 전체 매출 43,155,000 USD와 일치합니다. 고객 이름과 광산별 판매액은 '
        '이 주석에서 밝히지 않습니다. 반올림한 63%·25%·11%의 합계가 99%라는 이유로 '
        '가상의 네 번째 고객을 추가하지 않습니다.', report('EU')))
