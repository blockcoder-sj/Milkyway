"""Dated, source-backed business notes; dynamic providers cover the wider directory."""
from copy import deepcopy


def src(label, url, as_of=None):
    return {"label": label, "url": url, "as_of": as_of, "level": "primary"}


def notes(
    description, products, segments, drivers, source, relations=(), **identifiers
):
    fact = lambda title, detail="": dict(title=title, detail=detail, source=source)
    return dict(
        description=description,
        description_source=source,
        products=[
            fact(*item) if isinstance(item, tuple) else fact(item) for item in products
        ],
        segments=[
            fact(*item) if isinstance(item, tuple) else fact(item) for item in segments
        ],
        drivers=[
            fact(*item) if isinstance(item, tuple) else fact(item) for item in drivers
        ],
        relations=[
            dict(
                name=name,
                kind=kind,
                symbol=symbol,
                detail=detail,
                source=origin or source,
            )
            for name, kind, symbol, detail, origin in relations
        ],
        sources=[source],
        **identifiers
    )


APPLE_REPORT = src(
    "Apple · 2025 Form 10-K",
    "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm",
    "2025-09-27",
)
APPLE_SUPPLY = src(
    "Apple · 미국 공급망 발표",
    "https://www.apple.com/newsroom/2025/08/apple-increases-us-commitment-to-600-billion-usd-announces-ambitious-program/",
    "2025-08-06",
)
APPLE_BROADCOM = src(
    "Apple · Broadcom 공급 확대",
    "https://www.apple.com/newsroom/2026/07/apple-to-increase-spend-with-broadcom-to-produce-billions-more-us-chips/",
    "2026-07-08",
)
MS_REPORT = src(
    "Microsoft · 2025 연차보고서",
    "https://www.microsoft.com/investor/reports/ar25/index.html",
    "2025-06-30",
)
NV_REPORT = src(
    "NVIDIA · FY2025 연차보고서",
    "https://www.sec.gov/Archives/edgar/data/1045810/000104581025000098/finalforfiling-2025xannual.pdf",
    "2025-01-26",
)
HYNIX_PARTNER = src(
    "SK hynix · NVIDIA 기술 파트너십",
    "https://news.skhynix.com/en/multi-year-tech-partnership-with-nvidia/",
    "2026-06-08",
)
AMZN_REPORT = src(
    "Amazon · 2025 Form 10-K",
    "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm",
    "2025-12-31",
)
SAMSUNG_REPORT = src(
    "삼성전자 · 2025 사업보고서",
    "https://images.samsung.com/is/content/samsung/assets/global/ir/docs/2025_4Q_Interim_Report.pdf",
    "2025-12-31",
)
TSMC_REPORT = src(
    "TSMC · 2025 Form 20-F",
    "https://www.sec.gov/Archives/edgar/data/1046179/000162828026025362/tsm-20251231.htm",
    "2025-12-31",
)

CATALOG = {
    "AAPL": notes(
        "스마트폰·개인용 컴퓨터·태블릿과 관련 기기, 소프트웨어 및 서비스를 제공하는 기업입니다.",
        [
            ("iPhone", "스마트폰"),
            ("Mac", "개인용 컴퓨터"),
            ("iPad", "태블릿"),
            ("Wearables, Home and Accessories", "Apple Watch·AirPods 등"),
            ("Services", "App Store·광고·클라우드·AppleCare 등"),
        ],
        ["Americas", "Europe", "Greater China", "Japan", "Rest of Asia Pacific"],
        [
            ("부품·제조 공급망", "부품 가용성과 외부 제조 역량"),
            ("환율", "해외 매출과 비용의 통화 환산"),
            ("제품 출시와 수요", "신제품 출시 일정과 수요"),
            ("규제·소송", "앱 유통·결제 등 사업 규칙"),
        ],
        APPLE_REPORT,
        [
            ("TSMC", "supplier", "TSM", "미국 생산 칩 공급", APPLE_SUPPLY),
            ("Broadcom", "supplier", "AVGO", "셀룰러·연결 반도체 공급 협력", APPLE_BROADCOM),
            ("GlobalFoundries", "supplier", "GFS", "미국 반도체 부품 생산 협력", APPLE_SUPPLY),
        ],
        cik="320193",
        entity_id="Q312",
    ),
    "MSFT": notes(
        "기업용 소프트웨어·생산성 서비스, 클라우드와 개인용 컴퓨팅을 제공하는 기업입니다.",
        ["Microsoft 365", "Azure", "Windows", "Dynamics", "Xbox", "LinkedIn"],
        [
            "Productivity and Business Processes",
            "Intelligent Cloud",
            "More Personal Computing",
        ],
        [
            ("데이터센터 투자·운영", "클라우드 인프라와 설비 비용"),
            ("구독·클라우드 수요", "상업용 소프트웨어와 서버 서비스 수요"),
            ("PC 시장", "Windows OEM과 기기 매출"),
            ("환율", "해외 매출·비용의 환산"),
        ],
        MS_REPORT,
        [
            (
                "OpenAI",
                "partner",
                None,
                "주요 투자 관계 및 상호 매출 배분 약정 · FY2025 공시 기준",
                MS_REPORT,
            ),
            ("LinkedIn", "subsidiary", None, "전문가 네트워크 사업", MS_REPORT),
        ],
        cik="789019",
        entity_id="Q2283",
    ),
    "NVDA": notes(
        "GPU와 데이터센터 컴퓨팅·네트워킹 플랫폼, 관련 소프트웨어를 제공하는 기업입니다.",
        ["GPU", "CUDA", "GeForce", "데이터센터 가속 컴퓨팅", "네트워킹·AI 시스템"],
        ["Compute & Networking", "Graphics"],
        [
            ("파운드리 생산 능력", "외부 웨이퍼 제조와 조립·검사 역량"),
            ("부품 공급·재고", "장기 발주와 공급 확약"),
            ("AI·데이터센터 투자", "서버·가속 컴퓨팅 수요"),
            ("수출 통제", "판매 가능 국가·제품 범위"),
        ],
        NV_REPORT,
        [
            ("TSMC", "supplier", "TSM", "반도체 웨이퍼 제조", NV_REPORT),
            (
                "Samsung Electronics",
                "supplier",
                "005930.KS",
                "반도체 웨이퍼 제조 · FY2025 공시 기준",
                NV_REPORT,
            ),
            ("SK hynix", "partner", "000660.KS", "AI 메모리 다년 기술 파트너십", HYNIX_PARTNER),
            ("AMD", "competitor", "AMD", "가속 컴퓨팅·그래픽 시장", NV_REPORT),
            ("Intel", "competitor", "INTC", "컴퓨팅 시장", NV_REPORT),
        ],
        cik="1045810",
        entity_id="Q182477",
    ),
    "AMZN": notes(
        "온라인·오프라인 유통, 판매자 서비스와 클라우드 서비스를 제공하는 기업입니다.",
        ["온라인 판매", "판매자 서비스", "AWS", "광고", "구독 서비스"],
        ["North America", "International", "Amazon Web Services"],
        [
            ("소비·판매량", "상품 판매와 판매자 서비스 규모"),
            ("배송·물류", "배송망과 주문 처리 비용"),
            ("클라우드 투자", "컴퓨팅 인프라 수요와 설비"),
            ("환율", "해외 사업 매출·비용 환산"),
        ],
        AMZN_REPORT,
        cik="1018724",
        entity_id="Q3884",
    ),
    "TSM": notes(
        "고객이 설계한 반도체를 제조하는 파운드리 기업입니다.",
        ["반도체 웨이퍼 제조", "첨단 공정", "첨단 패키징"],
        ["반도체 파운드리"],
        [
            ("공정·수율", "공정 개발과 제조 수율"),
            ("설비·생산능력", "팹 건설과 장비 투자"),
            ("전력·물", "제조에 필요한 인프라"),
            ("고객 설계와 수요", "고객의 반도체 발주"),
        ],
        TSMC_REPORT,
        [
            ("Apple", "customer", "AAPL", "미국 생산 칩 공급", APPLE_SUPPLY),
            ("NVIDIA", "customer", "NVDA", "웨이퍼 제조", NV_REPORT),
        ],
        cik="1046179",
    ),
    "005930.KS": notes(
        "반도체, 스마트폰·가전, 디스플레이와 자동차 전장·오디오 사업을 운영하는 기업입니다.",
        ["DRAM·NAND·시스템 반도체", "스마트폰·가전", "OLED 디스플레이", "자동차 전장·오디오"],
        ["DX", "DS", "Samsung Display", "Harman"],
        [
            ("반도체 수급", "메모리·시스템 반도체 수요와 공급"),
            ("제품 판매", "모바일·가전 판매"),
            ("생산 설비", "공정·설비 투자"),
            ("환율·통상", "수출 사업과 무역 정책"),
        ],
        SAMSUNG_REPORT,
        [
            ("Samsung Display", "subsidiary", None, "디스플레이 사업", SAMSUNG_REPORT),
            ("Harman", "subsidiary", None, "자동차 전장·오디오 사업", SAMSUNG_REPORT),
            ("NVIDIA", "customer", "NVDA", "웨이퍼 제조 · FY2025 NVIDIA 공시 기준", NV_REPORT),
        ],
    ),
    "000660.KS": notes(
        "DRAM·NAND 플래시와 AI 시스템용 메모리·저장 장치를 제공하는 기업입니다.",
        ["DRAM", "NAND Flash", "HBM", "기업용 SSD"],
        ["메모리 반도체"],
        [("메모리 제품과 공정", "AI 메모리 제품·제조·패키징 개발"), ("고객 설계 협력", "고객 시스템 요구와 맞춤형 메모리")],
        src(
            "SK hynix · 메모리 사업 소개",
            "https://news.skhynix.com/en/hbm-to-essd/",
            "2026-07",
        ),
        [("NVIDIA", "partner", "NVDA", "AI 메모리 다년 기술 파트너십", HYNIX_PARTNER)],
    ),
}

CATALOG.update(
    {
        "GOOGL": notes(
            "Google 서비스·클라우드와 기타 신사업을 운영하는 Alphabet의 상장 주식입니다.",
            [
                "Google Search",
                "YouTube",
                "Android·Chrome",
                "Google Workspace",
                "Google Cloud",
            ],
            ["Google Services", "Google Cloud", "Other Bets"],
            [
                ("광고 수요", "검색·영상 등 광고 사업"),
                ("데이터센터", "클라우드와 AI 인프라"),
                ("규제", "경쟁·개인정보 관련 사업 조건"),
            ],
            src(
                "Alphabet · 2025 Form 10-K",
                "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm",
                "2025-12-31",
            ),
        ),
        "WMT": notes(
            "매장과 전자상거래를 함께 운영하는 유통 기업입니다.",
            ["생활용품·식품 유통", "전자상거래", "Sam’s Club 회원제 유통"],
            ["미국 유통", "해외 유통", "Sam’s Club"],
            [("공급·배송", "상품 공급망과 주문 처리"), ("소비자·회원 수요", "상품과 회원 서비스 이용")],
            src(
                "Walmart · 회사·사업 소개",
                "https://corporate.walmart.com/about",
                "열람 2026-10-01",
            ),
        ),
        "JPM": notes(
            "개인·기업 금융과 투자은행·자산관리 서비스를 제공하는 금융 기업입니다.",
            ["예금·대출", "투자은행·결제", "자산·부 관리"],
            [
                "Consumer & Community Banking",
                "Commercial & Investment Banking",
                "Asset & Wealth Management",
            ],
            [],
            src(
                "JPMorganChase · 사업 영역",
                "https://www.jpmorganchase.com/about",
                "열람 2026-10-01",
            ),
        ),
        "DUK": notes(
            "전력과 천연가스 유틸리티 사업을 운영하는 기업입니다.",
            ["전력 공급", "천연가스 공급", "발전·전력망"],
            [],
            [("발전·전력망 설비", "발전원과 전력망 투자"), ("에너지 구성", "천연가스·원자력·재생에너지·저장 장치")],
            src(
                "Duke Energy · 회사 소개",
                "https://www.duke-energy.com/our-company/about-us",
                "열람 2026-10-01",
            ),
        ),
        "PLD": notes(
            "물류 부동산의 소유·관리·개발과 관련 서비스를 제공하는 기업입니다.",
            ["창고·물류 시설", "부동산 개발·운영", "물류 시설 서비스"],
            [],
            [("고객 산업·공급망", "유통·제조·운송망과 전자상거래"), ("개발 조건", "토지·인력·시설 개발 여건")],
            src(
                "Prologis · 물류 부동산 사업",
                "https://www.prologis.com/logistics-real-estate",
                "열람 2026-10-01",
            ),
        ),
        "XOM": notes(
            "에너지·화학·윤활유와 저탄소 기술 사업을 운영하는 기업입니다.",
            ["석유·가스", "연료", "윤활유", "화학 제품", "저탄소 기술"],
            ["Upstream", "Product Solutions", "Low Carbon Solutions"],
            [],
            src(
                "ExxonMobil · 사업 부문",
                "https://corporate.exxonmobil.com/who-we-are/our-global-organization/business-divisions",
                "2026-10-01",
            ),
        ),
        "LIN": notes(
            "산업용·의료용·특수가스와 엔지니어링 서비스를 제공하는 기업입니다.",
            ["산업용 가스", "의료용 산소", "반도체용 고순도 가스", "수소·탄소 포집 기술", "엔지니어링"],
            [],
            [("사업 노출 분야", "화학·에너지·식음료·전자·의료·제조·금속·광업 고객에게 가스와 기술을 제공합니다.")],
            src("Linde · 사업 소개", "https://www.linde.com/about-us", "2026-10-01"),
        ),
        "CAT": notes(
            "건설·광산 장비, 산업용 엔진과 관련 제품·기술·서비스를 제공하는 기업입니다.",
            ["건설 장비", "광산 장비", "산업용 디젤·가스 엔진", "장비 서비스"],
            [],
            [("고객 산업", "건설·광업과 산업용 엔진 고객의 사업 활동을 확인할 수 있습니다.")],
            src(
                "Caterpillar · 고객 산업",
                "https://www.caterpillar.com/en/company/about-caterpillar/industries.html",
                "2026-10-01",
            ),
        ),
        "JNJ": notes(
            "혁신 의약품과 의료 기술 사업을 운영하는 헬스케어 기업입니다.",
            ["의약품", "의료기기·의료 기술"],
            ["Innovative Medicine", "MedTech"],
            [],
            src(
                "Johnson & Johnson · 회사 소개",
                "https://www.jnj.com/our-company",
                "2026-10-01",
            ),
        ),
    }
)
CATALOG["GOOG"] = deepcopy(CATALOG["GOOGL"])

# SEC identifiers are fixed only for well-known, ticker-bound issuers. Wikidata
# supplies identifiers for the wider directory; SEC rechecks the ticker itself.
CIKS = {
    "GOOGL": "1652044",
    "GOOG": "1652044",
    "META": "1326801",
    "AVGO": "1730168",
    "AMD": "2488",
    "INTC": "50863",
    "XOM": "34088",
    "CVX": "93410",
    "LIN": "1707925",
    "CAT": "18230",
    "GE": "40545",
    "WMT": "104169",
    "COST": "909832",
    "PG": "80424",
    "KO": "21344",
    "PEP": "77476",
    "JNJ": "200406",
    "LLY": "59478",
    "UNH": "731766",
    "JPM": "19617",
    "BAC": "70858",
    "BRK-B": "1067983",
    "NEE": "753308",
    "DUK": "1326160",
    "PLD": "1045609",
    "AMT": "1053507",
}


# Curated business classification, separate from received Yahoo constituents.
EDITORIAL_DIRECTORY = {"TSM": ("us_45", "TSMC")}


def editorial_for(symbol):
    value = deepcopy(CATALOG.get(symbol, {}))
    if symbol in CIKS:
        value["cik"] = CIKS[symbol]
    if symbol in {"TSM", "005930.KS"}:
        share = "72.5%" if symbol == "TSM" else "5.9%"
        value["market_shares"] = [
            {
                "title": "글로벌 파운드리 매출 점유율 · " + share,
                "detail": "2026년 2분기 · 파운드리 사업 매출 기준입니다. 반도체 전체 또는 섹터 전체의 점유율이 아닙니다. 공급자 발표 비율을 표시하며 앱에서 재계산하지 않습니다.",
                "source": src(
                    "TrendForce · 2026 Q2 파운드리 조사",
                    "https://www.trendforce.com/presscenter/news/20260909-13225.html",
                    "2026-06-30",
                ),
            }
        ]
    return value
