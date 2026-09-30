"""Fixed display instruments; never a paper execution universe or order list."""

from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class Instrument:
    id: str
    label: str
    symbol: str
    market: str
    group: str
    description: str
    unit: str = "pt"
    multiplier: float = 1.0

    @property
    def source_url(self) -> str:
        return "https://finance.yahoo.com/quote/" + quote(self.symbol, safe="") + "/"


INDICES = (
    Instrument("sp500", "S&P 500", "^GSPC", "us", "indices", "미국 대형주 시장을 대표하는 지수"),
    Instrument("dow", "다우 산업평균", "^DJI", "us", "indices", "미국 주요 30개 기업의 주가 가중 지수"),
    Instrument("nasdaq", "나스닥 종합", "^IXIC", "us", "indices", "나스닥 상장 종목을 포괄하는 지수"),
    Instrument("nasdaq100", "나스닥 100", "^NDX", "us", "indices", "나스닥의 주요 비금융 대형주 지수"),
    Instrument("russell2000", "러셀 2000", "^RUT", "us", "indices", "미국 소형주 시장 지수"),
    Instrument("vix", "VIX", "^VIX", "us", "indices", "S&P 500 옵션 가격에 반영된 기대 변동성", "%"),
    Instrument("kospi", "코스피", "^KS11", "kr", "indices", "한국 유가증권시장 종합주가지수"),
    Instrument("kosdaq", "코스닥", "^KQ11", "kr", "indices", "한국 코스닥시장 종합주가지수"),
    Instrument("kospi200", "코스피 200", "^KS200", "kr", "indices", "한국 유가증권시장 대표 200종목 지수"),
)
FX = (
    Instrument("usdkrw", "원 / 달러", "KRW=X", "global", "fx", "1 미국 달러당 원화", "KRW"),
    Instrument("jpykrw", "원 / 100엔", "JPYKRW=X", "global", "fx", "100 일본 엔당 원화", "KRW", 100),
    Instrument("eurkrw", "원 / 유로", "EURKRW=X", "global", "fx", "1 유로당 원화", "KRW"),
    Instrument("usdjpy", "엔 / 달러", "JPY=X", "global", "fx", "1 미국 달러당 일본 엔", "JPY"),
    Instrument("eurusd", "달러 / 유로", "EURUSD=X", "global", "fx", "1 유로당 미국 달러", "USD"),
)
FUTURES = (
    Instrument("sp500_future", "S&P 500 선물", "ES=F", "us", "futures", "E-mini S&P 500 최근월 선물 · 만기 교체에 유의"),
    Instrument("nasdaq_future", "나스닥 100 선물", "NQ=F", "us", "futures", "E-mini Nasdaq 100 최근월 선물 · 만기 교체에 유의"),
    Instrument("gold", "금 선물", "GC=F", "global", "commodities", "금 최근월 선물 · 트로이온스당 달러", "USD"),
    Instrument("oil", "WTI 원유 선물", "CL=F", "global", "commodities", "WTI 최근월 선물 · 배럴당 달러", "USD"),
)
US_SECTORS = tuple(
    # Yahoo lists the energy price index as ^GSPE; ^SP500-10 is unavailable.
    Instrument("us_" + code, label, "^GSPE" if code == "10" else "^SP500-" + code,
               "us", "sectors", description)
    for code, label, description in (
        ("10", "Energy", "S&P 500 에너지 · 석유·가스·에너지 장비 및 서비스"),
        ("15", "Materials", "S&P 500 소재 · 화학·금속·건축자재·포장재"),
        ("20", "Industrials", "S&P 500 산업재 · 자본재·운송·산업 서비스"),
        ("25", "Consumer Discretionary", "S&P 500 경기소비재 · 자동차·유통·여가"),
        ("30", "Consumer Staples", "S&P 500 필수소비재 · 식음료·생활용품"),
        ("35", "Health Care", "S&P 500 헬스케어 · 제약·의료기기·의료 서비스"),
        ("40", "Financials", "S&P 500 금융 · 은행·보험·자본시장"),
        ("45", "Information Technology", "S&P 500 정보기술 · 소프트웨어·하드웨어·반도체"),
        ("50", "Communication Services", "S&P 500 커뮤니케이션 서비스 · 통신·미디어·인터넷 플랫폼"),
        ("55", "Utilities", "S&P 500 유틸리티 · 전기·가스·수도"),
        ("60", "Real Estate", "S&P 500 부동산 · 리츠·부동산 관리 및 개발"),
    )
)
KR_SECTORS = tuple(
    Instrument("kr_" + code, label, "KOSPI-" + code + ".KS", "kr", "sectors", description)
    for code, label, description in (
        ("13", "전기·전자", "코스피 전기·전자 업종 지수"),
        ("8", "화학", "코스피 화학 업종 지수"),
        ("15", "운송장비", "코스피 운송장비 업종 지수"),
        ("19", "운수·창고", "코스피 운수·창고 업종 지수"),
        ("18", "건설", "코스피 건설 업종 지수"),
        ("21", "금융업", "코스피 금융업 지수 · 아래 증권·보험 업종과 범위가 겹칩니다"),
        ("24", "증권", "코스피 증권 업종 지수 · 금융업의 하위 업종"),
        ("25", "보험", "코스피 보험 업종 지수 · 금융업의 하위 업종"),
    )
)
CATALOG = INDICES + FX + FUTURES + US_SECTORS + KR_SECTORS
BY_ID = {item.id: item for item in CATALOG}
