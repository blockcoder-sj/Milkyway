"""Dated, source-backed business notes; dynamic providers cover the wider directory."""
from copy import deepcopy
import json


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
            (
                "Corning",
                "supplier",
                "GLW",
                "iPhone·Apple Watch 커버 유리 제조 확대 계획 · 2025-08 발표",
                APPLE_SUPPLY,
            ),
            (
                "Coherent",
                "supplier",
                "COHR",
                "Face ID 등에 사용하는 VCSEL 레이저 · 다년 계약",
                APPLE_SUPPLY,
            ),
            (
                "Texas Instruments",
                "supplier",
                "TXN",
                "Apple 제품용 기초 반도체 제조·생산능력 확대 계획 · 2025-08 발표",
                APPLE_SUPPLY,
            ),
            (
                "Samsung Electronics",
                "supplier",
                "005930.KS",
                "전력·성능 개선 칩 제조기술 개발·공급 계획 · 2025-08 발표",
                APPLE_SUPPLY,
            ),
            (
                "Amkor",
                "supplier",
                "AMKR",
                "Apple silicon 패키징·검사 시설 투자 계획 · 2025-08 발표",
                APPLE_SUPPLY,
            ),
            (
                "MP Materials",
                "supplier",
                "MP",
                "희토류 자석 구매 약정·재활용 라인 구축 계획 · 2025-08 발표",
                APPLE_SUPPLY,
            ),
            (
                "Applied Materials",
                "partner",
                "AMAT",
                "미국 반도체 제조장비 생산 확대 협력 · 2025-08 발표",
                APPLE_SUPPLY,
            ),
            (
                "GlobalWafers America",
                "partner",
                None,
                "미국 반도체 팹용 300mm 웨이퍼 생산 협력 · 2025-08 발표",
                APPLE_SUPPLY,
            ),
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

# Concise Korean reading notes for the existing core directory. These retain the
# date and origin of the business report, separately from newer relationship news.
CORE_READING = {
    'AAPL': (
        '아이폰·맥·아이패드·웨어러블 등 기기 판매와 디지털 콘텐츠·구독·광고·결제 등 서비스에서 매출이 발생합니다. 기기와 서비스는 서로 다른 매출 구분입니다.',
        '개인·기업·교육·정부 고객에게 직접 판매하거나 이동통신사·재판매 업체를 통해 판매합니다.',
        '핵심 부품과 완제품 조립을 외부 공급망에 의존합니다. 부품 공급·제조 차질, 제품 출시 시기와 유통 재고가 사업 조건입니다.'),
    'MSFT': (
        '클라우드 이용과 소프트웨어 구독·라이선스, 기기·게임·광고 등에서 매출이 발생합니다. Microsoft 365의 구독과 Azure의 사용량 기반 서비스는 구분해서 봅니다.',
        '기업·공공기관·개발자·개인이 사용하며 직접 계약, 판매 파트너와 PC 제조사 경로로 공급합니다.',
        '데이터센터·서버·전력과 네트워크, 소프트웨어 개발·보안 운영이 클라우드 제공의 기반입니다.'),
    'NVDA': (
        '가속 컴퓨팅·네트워크 제품과 시스템, 그래픽 제품 및 관련 소프트웨어·서비스 판매가 매출 원천입니다. GPU 출하와 시스템·플랫폼 매출의 범위를 구분합니다.',
        '클라우드·서버·기기 제조사와 유통 경로를 통해 판매합니다. 공개되지 않은 특정 고객의 구매액은 추정하지 않습니다.',
        '직접 웨이퍼 팹을 운영하지 않고 외부 파운드리·조립·검사·부품 공급망을 사용합니다. 첨단 생산 능력·메모리·패키징과 수출 통제가 사업 조건입니다.'),
    'AMZN': (
        '자체 상품 판매, 외부 판매자 수수료·물류 서비스, AWS 이용, 광고와 구독에서 매출이 발생합니다. 외부 판매자의 전체 거래액을 아마존 매출로 합치지 않습니다.',
        '상품 구매자·입점 판매자·개발자·기업·광고주·콘텐츠 제작자가 서로 다른 고객 집단입니다.',
        '주문 처리·배송망과 물류 인력, 상품 조달 및 AWS 데이터센터·전력·컴퓨팅 설비가 필요합니다.'),
    'TSM': (
        '고객의 반도체 설계를 위탁 제조하고 관련 패키징 서비스를 제공합니다. 공정과 제품별 제조 서비스가 매출의 기반입니다.',
        '팹리스 설계사와 자체 생산을 병행하는 반도체 기업 등이 고객입니다. 익명 대형 고객 이름은 추정하지 않습니다.',
        '노광·식각·증착·계측 장비와 웨이퍼·소재, 팹의 전력·물·첨단 패키징 생산 능력이 연결됩니다.'),
    '005930.KS': (
        '반도체·스마트폰·가전·디스플레이와 전장·오디오 제품을 판매합니다. 완제품과 부품 사업, 내부 거래를 구분해서 공시를 확인합니다.',
        '일반 소비자와 기기·시스템 제조사, 기업 고객에게 직접 또는 판매망을 통해 공급합니다.',
        '메모리·파운드리 공정과 제조 설비, 부품·소재 조달과 완제품 유통이 사업에 연결됩니다.'),
    '000660.KS': (
        'DRAM·NAND와 HBM·SSD 등 메모리·저장 제품을 제공합니다. 시스템에 맞춘 메모리 개발·제조·패키징을 함께 수행합니다.',
        'AI·데이터센터·기기·시스템의 메모리 수요가 제품 사용처입니다. NVIDIA와의 확인된 개발 관계는 아래 관계도에 따로 표시합니다.',
        '메모리 공정·패키징과 고객 시스템 설계의 적합성, 생산 설비와 소재가 제품 제공에 연결됩니다.'),
    'GOOGL': (
        '검색·영상 등 광고, 구독·플랫폼·기기 판매와 Google Cloud 서비스가 매출 원천입니다. 기타 신사업은 별도 보고합니다.',
        '광고주·개인 이용자와 클라우드·업무 소프트웨어를 쓰는 기업·개발자가 서로 다른 고객 집단입니다.',
        '데이터센터·네트워크·전력·콘텐츠와 서비스 개발·규제 대응이 사업 운영과 연결됩니다.'),
    'JPM': (
        '예금·대출 등에서 발생하는 순이자수익과 카드·결제·투자은행·자산 관리 등의 수수료가 수익 원천입니다. 일반 제조업의 제품 매출과 금융업의 수익 구분은 다릅니다.',
        '개인·소기업·기업·금융기관·정부와 자산 관리 고객에게 은행·투자·결제 서비스를 제공합니다.',
        '자금 조달과 예금 기반, 신용·시장 위험 관리, 결제·IT 운영과 규제 자본이 사업 조건입니다.'),
    'DUK': (
        '전력과 천연가스 공급을 중심으로 사업을 운영합니다. 고객에게 에너지 서비스를 제공하는 유틸리티입니다.',
        '서비스 지역의 주거·상업·산업 고객과 지역 사회에 전력·가스를 제공합니다.',
        '발전원·연료, 전력망·가스 공급 설비의 투자·운영이 에너지 공급과 연결됩니다.'),
    'PLD': (
        '물류 부동산을 소유·개발·운영하고 고객에게 시설과 관련 서비스를 제공합니다.',
        '유통·전자상거래·제조·운송 기업이 시설을 사용합니다. 공개 고객 목록의 기준일과 계약 범위는 아래 관계도에 표시합니다.',
        '물류 입지와 시설 개발·운영 여건, 고객의 공급망·물류 수요가 사업과 연결됩니다.'),
    'XOM': (
        '석유·가스 생산과 연료·윤활유·화학 제품, 저탄소 솔루션 사업을 운영합니다. 각 부문의 사업 단계와 제품을 구분합니다.',
        '에너지·산업용 제품의 판매망과 기업 고객에게 제품·솔루션을 공급합니다.',
        '자원 개발·생산, 정유·화학 설비와 투입 원료가 사업 기반입니다. 발표된 신규 프로젝트는 실제 가동과 구분합니다.'),
    'LIN': (
        '산업용·의료용·특수가스와 가스 관련 엔지니어링을 제공합니다.',
        '화학·에너지·식음료·전자·의료·제조·금속·광업 분야가 고객 산업입니다.',
        '고객의 가스 사용 공정과 고순도 공급 조건, 가스 생산·공급 설비가 연결됩니다.'),
    'CAT': (
        '건설·광산 장비와 산업용 엔진, 제품 사용에 필요한 기술·서비스를 제공합니다.',
        '건설·광업과 산업용 엔진을 사용하는 고객에게 제품·솔루션을 공급합니다.',
        '고객의 건설·광산 운영 및 장비 사용 환경이 제품 수요와 연결됩니다. 시험 중인 장비 도입과 실제 판매를 구분합니다.'),
    'JNJ': (
        '혁신 의약품과 의료기기·의료 기술 제품을 제공하는 두 사업 영역을 운영합니다.',
        '의료·환자 치료에 쓰이는 의약품과 의료 기술을 제공합니다.',
        '의약품 연구·개발과 의료기술 제품 개발, 생산·공급이 사업의 기반입니다.'),
}
CORE_READING['GOOG'] = CORE_READING['GOOGL']
for _symbol, (_revenue, _customers, _inputs) in CORE_READING.items():
    _notes = CATALOG[_symbol]
    _origin = _notes['description_source']
    if _symbol == 'NVDA':
        _origin = src('NVIDIA · FY2026 Form 10-K',
            'https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm', '2026-01-25')
    elif _symbol == 'JPM':
        _origin = src('JPMorganChase · 2025 Form 10-K',
            'https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm', '2025-12-31')
    _notes['brief'] = [dict(title=title, detail=detail, source=_origin) for title, detail in (
        ('무엇을 하는 기업인가', _notes['description']), ('매출이 생기는 구조', _revenue),
        ('고객·판매 경로', _customers), ('공급망·주요 투입 요소', _inputs))]

# Business segment names remain exact official labels, with Korean reading aids.
SEGMENT_KO = {
    'Productivity and Business Processes': '생산성·비즈니스 프로세스',
    'Intelligent Cloud': '클라우드', 'More Personal Computing': '퍼스널 컴퓨팅',
    'Compute & Networking': '컴퓨팅·네트워킹', 'Graphics': '그래픽',
    'North America': '북미', 'International': '해외', 'Amazon Web Services': 'AWS 클라우드',
    'Google Services': 'Google 서비스', 'Google Cloud': 'Google 클라우드', 'Other Bets': '기타 신사업',
    'Consumer & Community Banking': '개인·지역 은행',
    'Commercial & Investment Banking': '상업·투자은행', 'Asset & Wealth Management': '자산·부 관리',
    'Upstream': '자원 개발·생산', 'Product Solutions': '연료·화학 등 제품',
    'Low Carbon Solutions': '저탄소 솔루션', 'Innovative Medicine': '혁신 의약품', 'MedTech': '의료 기술',
    'DX': '완제품(DX)', 'DS': '반도체(DS)', 'Samsung Display': '삼성디스플레이', 'Harman': '하만 전장·오디오',
}
for _notes in CATALOG.values():
    for _row in _notes['segments']:
        _row['title'] = SEGMENT_KO.get(_row['title'], _row['title'])

# Free official product/partnership statements complement annual reports that do
# not name commercial counterparties. Announced transitions remain labelled plans.
APPLE_CARD = src("Apple · Apple Card 발급사 전환 발표",
    "https://www.apple.com/newsroom/2026/01/chase-to-become-new-issuer-of-apple-card/", "2026-01-07")
CATALOG["JPM"]["relations"] += [
    dict(name="Amazon", kind="partner", symbol="AMZN",
        detail="Amazon 결제 화면의 Chase Pay Over Time 분할 결제 서비스 · 일부 Chase 카드 고객에 순차 제공", source=src("Chase · Amazon 결제 서비스 안내", "https://www.chase.com/personal/credit-cards/education/basics/a-guide-chase-pay-over-time-on-amazon", "열람 2026-10-01")),
    dict(name="United Airlines", kind="partner", symbol="UAL",
        detail="United 개인·사업자 공동 브랜드 신용카드와 MileagePlus 고객 혜택", source=src("Chase · United 공동 브랜드 카드", "https://www.chase.com/personal/credit-cards/united", "열람 2026-10-01")),
    dict(name="Apple", kind="partner", symbol="AAPL",
        detail="Apple Card 신규 발급사 전환 합의 · 2026-01 발표 당시 약 24개월 전환 예상. 전환 완료를 뜻하지 않습니다.", source=APPLE_CARD),
]
CATALOG["AAPL"]["relations"] += [
    dict(name="JPMorgan Chase", kind="partner", symbol="JPM",
        detail="Apple Card 발급사 전환 합의 · 2026-01 발표 당시 약 24개월 전환 예상. 전환 완료를 뜻하지 않습니다.", source=APPLE_CARD),
    dict(name="Mastercard", kind="partner", symbol="MA",
        detail="Apple Card 결제 네트워크 · 발급사 전환 후에도 네트워크 유지 예정", source=APPLE_CARD),
]
CATALOG["MSFT"]["relations"].append(dict(name="OpenAI", kind="partner", symbol=None,
    detail="클라우드·AI 협력 계약 개정 발표 · 계약 조건은 원문 기준으로 확인", source=src("Microsoft · OpenAI 협력 계약 개정", "https://blogs.microsoft.com/blog/2026/04/27/the-next-phase-of-the-microsoft-openai-partnership/", "2026-04-27")))

ANTHROPIC_PARTNERSHIP = src(
    "Microsoft · NVIDIA·Anthropic 협력 발표",
    "https://blogs.microsoft.com/blog/2025/11/18/microsoft-nvidia-and-anthropic-announce-strategic-partnerships/",
    "2025-11-18",
)
CATALOG["NVDA"]["relations"] += [
    dict(name="Meta Platforms", kind="partner", symbol="META",
        detail="AI 데이터센터의 CPU·GPU·네트워크 및 모델 공동 설계 협력 · Blackwell·Rubin GPU 확장 계획 포함. 발표된 도입 규모를 매출이나 완료된 납품으로 계산하지 않습니다.",
        source=src("NVIDIA · Meta 인프라 협력 발표", "https://nvidianews.nvidia.com/news/meta-builds-ai-infrastructure-with-nvidia", "2026-02-17")),
    dict(name="Amazon", kind="partner", symbol="AMZN",
        detail="AWS의 NVLink Fusion·Trainium4·Graviton·Nitro 및 클라우드 인프라 통합 협력 · 신규 통합은 발표 당시 계획을 포함합니다.",
        source=src("NVIDIA · AWS 협력 확대", "https://blogs.nvidia.com/blog/aws-partnership-expansion-reinvent/", "2025-12-02")),
    dict(name="Anthropic", kind="partner", symbol=None,
        detail="AI 모델·GPU 아키텍처 설계와 엔지니어링 협력 발표 · 향후 컴퓨팅 용량·투자 약정은 실제 납품·투자 완료를 뜻하지 않습니다.",
        source=ANTHROPIC_PARTNERSHIP),
]
CATALOG["MSFT"]["relations"].append(dict(name="Anthropic", kind="partner", symbol=None,
    detail="Azure에서 Claude 제공과 Copilot·Foundry 모델 접근 확대 협력 · 컴퓨팅 구매 약정은 완료된 매출을 뜻하지 않습니다.",
    source=ANTHROPIC_PARTNERSHIP))

# Fixed ticker-bound issuers complement the exact official SEC index.
CIKS = {
    "GOOGL": "1652044",
    "GOOG": "1652044",
    "META": "1326801",
    "AVGO": "1730168",
    "AMD": "2488",
    "INTC": "50863",
    "XOM": "2115436",
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
    from .company_research_catalog import enrichment
    extra = enrichment(symbol)
    from .company_energy_financial_archive import editorial as financial_editorial
    for key, rows in financial_editorial(symbol).items():
        extra[key] = rows + extra.get(key, [])
    for key, rows in extra.items():
        if key == 'brief' and rows:
            # Edited summaries replace the old summary before schema validation.
            # Retain the old citations in the source appendix, not duplicate cards.
            value.setdefault('sources', []).extend(row['source'] for row in value.get(key, []))
            value[key] = rows
        else:
            value[key] = rows + value.get(key, []) if isinstance(rows, list) else rows
    if symbol in CIKS:
        value["cik"] = CIKS[symbol]
    else:
        from .energy_issuers import issuer
        entry = issuer(symbol)
        if entry and entry.cik:
            value['cik'] = entry.cik
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


def enrich(value):
    """Apply reviewed reading notes to cached profiles without losing raw evidence."""
    from .company_schemas import CompanyKnowledge
    from .company_subsidiaries import replaced_by_reviewed
    from .company_research_catalog import private_profile, PRIVATE_NAMES, PRIVATE_COMPANIES, REGISTERED_TICKERS, PUBLIC_COMPANIES
    data = CompanyKnowledge.model_validate(value).model_dump(mode="json")
    if data.get('registry_id') and data['registry_id'] not in PRIVATE_COMPANIES:
        raise ValueError('Unknown primary-source company registry')
    registered_symbol = REGISTERED_TICKERS.get(data.get('registry_id'))
    if registered_symbol:
        if data['symbol'] and data['symbol'] != registered_symbol:
            raise ValueError('Conflicting registered company symbol')
        data['symbol'] = registered_symbol
    curated = (private_profile(data['registry_id']) if data.get('registry_id')
               else editorial_for(data['symbol']))
    canonical_registry = curated.get('registry_id')
    if canonical_registry in REGISTERED_TICKERS and REGISTERED_TICKERS[canonical_registry] == data['symbol']:
        data['registry_id'] = canonical_registry
        data['name'] = PUBLIC_COMPANIES[data['symbol']]['name']
    normalized = CompanyKnowledge.model_validate({
        'name': data['name'], **{key: rows for key, rows in curated.items()
                               if key in CompanyKnowledge.model_fields and key not in {'name', 'entity_id'}}
    }).model_dump(mode='json')
    from .company_reviewed_excerpts import replace_excerpts
    replace_excerpts(data, curated, normalized)
    # A reviewed note moved into a visible section should not also remain in the
    # old raw-fact appendix. Match the entire validated fact, including evidence.
    promoted = {json.dumps(row, sort_keys=True, ensure_ascii=False)
                for key in ('brief', 'products', 'segments', 'drivers') for row in normalized[key]}
    data['facts'] = [row for row in data['facts']
                     if json.dumps(row, sort_keys=True, ensure_ascii=False) not in promoted]
    for key, rows in curated.items():
        if key in {'cik', 'name', 'entity_id', 'registry_id'}:
            continue
        if isinstance(rows, list):
            if key == 'brief' and normalized[key]:
                data['sources'].extend(row['source'] for row in data[key] + normalized[key])
                data[key] = normalized[key]
                continue
            seen, merged = set(), []
            preferred = {(row.get('title'), row.get('source', {}).get('url'), row.get('source', {}).get('as_of'))
                         for row in normalized[key]} if key in {'products', 'segments', 'drivers', 'market_shares'} else set()
            # A reviewed figure replaces the same filing coordinate, including
            # old English labels/anchors. Other periods and sources are retained.
            previous_rows = data.get(key, [])
            if key == 'revenue_mix':
                from .company_revenue import basis, present_revenue
                previous_rows = present_revenue(previous_rows, data['symbol'])
                reviewed_revenue = {(*basis(row), row['member']) for row in normalized[key]}
            if key == 'financials':
                from .company_financial_coordinates import coordinate, corroborates
                reviewed_financials = {coordinate(row) for row in normalized[key]} - {None}
            previous = []
            for row in previous_rows:
                if key == 'relations':
                    if not row.get('symbol') and not row.get('registry_id') and row['name'] in PRIVATE_NAMES:
                        row = {**row, 'registry_id': PRIVATE_NAMES[row['name']]}
                    if replaced_by_reviewed(row, normalized[key]):
                        continue
                if key == 'revenue_mix' and (*basis(row), row['member']) in reviewed_revenue:
                    continue
                if key == 'financials' and coordinate(row) in reviewed_financials:
                    continue
                if key == 'financials' and any(corroborates(item, row) for item in normalized[key]):
                    data['sources'].append(row['source'])
                    continue
                if key == 'segments':
                    row = {**row, 'title': SEGMENT_KO.get(row['title'], row['title'])}
                identity = (row.get('title'), row.get('source', {}).get('url'), row.get('source', {}).get('as_of')) if isinstance(row, dict) else None
                if identity not in preferred:
                    previous.append(row)
            for row in normalized[key] + previous:
                if key == 'relations' and not row.get('symbol') and not row.get('registry_id') and row['name'] in PRIVATE_NAMES:
                    row = {**row, 'registry_id': PRIVATE_NAMES[row['name']]}
                identity = json.dumps(row, sort_keys=True, ensure_ascii=False)
                if identity not in seen:
                    seen.add(identity)
                    merged.append(row)
            limit = CompanyKnowledge.model_fields[key].metadata
            bound = next((item.max_length for item in limit if hasattr(item, 'max_length')), 200)
            data[key] = merged[:bound]
        elif rows:
            data[key] = rows
    if not data['brief'] and curated.get('description_source'):
        origin = curated['description_source']
        cards = [('핵심 사업', curated.get('description', ''))]
        for key, label in [('products', '제품·서비스'), ('segments', '사업을 나누는 기준'), ('drivers', '확인할 사업 조건')]:
            detail = ' · '.join(row['title'] + (': ' + row['detail'] if row.get('detail') else '')
                                for row in curated.get(key, [])[:6])
            cards.append((label, detail[:600]))
        data['brief'] = [dict(title=title, detail=detail, source=origin) for title, detail in cards if detail]
    for edge in data['relations']:
        if not edge.get('symbol') and not edge.get('registry_id') and edge['name'] in PRIVATE_NAMES:
            edge['registry_id'] = PRIVATE_NAMES[edge['name']]
    from .company_revenue import present_revenue
    data['revenue_mix'] = present_revenue(data['revenue_mix'], data['symbol'])
    from .company_financial_labels import presented
    data['financials'] = presented(data['financials'])
    # Old summary and corroborating figure citations may be promoted after the
    # source-list merge. Deduplicate once at the end, preserving full provenance.
    data['sources'] = list({json.dumps(row, sort_keys=True, ensure_ascii=False): row
                            for row in data['sources']}.values())[:200]
    return CompanyKnowledge.model_validate(data)
