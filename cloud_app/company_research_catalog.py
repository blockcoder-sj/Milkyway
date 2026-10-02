"""Human-reviewed Korean reading notes from free, dated primary documents.

Keep each claim attached to its actual document. These are reading notes, not
live estimates or an automatic translation. Source documents remain independent
of ticker identity and sector classification.
"""
from copy import deepcopy
from .company_research_notes import source, profile, relation




TSMC_SUPPLY = source("TSMC · 2025 공급망 포상 명단", "https://pr.tsmc.com/english/news/3274", "2025-11-28")
ASML_REPORT = source("ASML · 2025 Form 20-F", "https://www.sec.gov/Archives/edgar/data/937966/000162828026011378/asml-20251231.htm", "2025-12-31")
TRUMPF_LASER = source("TRUMPF · ASML용 EUV 레이저 개발", "https://www.trumpf.com/en_US/newsroom/global-press-releases/press-release-detail-page/release/asml-honors-trumpf-for-new-euv-laser-9838/", "2025-10-24")
MCD_REPORT = source("McDonald’s · 2025 Form 10-K", "https://www.sec.gov/Archives/edgar/data/63908/000006390826000035/mcd-20251231.htm", "2025-12-31")
MCD_US = source("McDonald’s · 미국 식품 공급사", "https://www.mcdonalds.com/us/en-us/about-our-food/meet-our-suppliers.html")
MCD_CA = source("McDonald’s · 캐나다 식품 공급사", "https://www.mcdonalds.com/ca/en-ca/about-our-food/sourcing.html")
MCD_GOOGLE = source("McDonald’s · Google Cloud 협력", "https://corporate.mcdonalds.com/corpmcd/our-stories/article/mcd-google-cloud-announce-partnership.htm.html", "2023-12-06")
MCD_ACN = source("Accenture · McDonald’s 기술 협력", "https://newsroom.accenture.com/news/2023/mcdonald-s-corporation-and-accenture-expand-partnership-to-accelerate-technology-adoption-and-reinvent-customer-and-crew-experiences", "2023-12-19")
MU_REPORT = source("Micron · FY2026 Q3 Form 10-Q", "https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/mu-20260528.htm", "2026-05-28")
MU_HBM = source("Micron · HBM3E 제품·납품 안내", "https://www.micron.com/products/memory/hbm/hbm3e")
MEMORY_RESEARCH = source("DBS · 메모리 산업 자료", "https://www.dbs.com/content/article/pdf/CIO/2025/202505/CIOIndustryGuide_May2025.pdf", "2025-05", "provider")
NV_US = source("NVIDIA · 미국 AI 제조 공급망", "https://blogs.nvidia.com/blog/nvidia-manufacture-american-made-ai-supercomputers-us/", "2025-04-14")
NV_HYNIX = source("NVIDIA · SK hynix 메모리 공동개발", "https://nvidianews.nvidia.com/news/sk-hynix-ai-factory", "2026-06-08")
LIN_SAMSUNG = source("Linde · 삼성전자 평택 고순도 가스 공급", "https://www.linde.com/news-and-media/2025/linde-to-expand-supply-of-industrial-gases-to-samsung-in-south-korea", "2025-04-29")
XOM_AIR = source("ExxonMobil · Air Liquide Baytown 계약", "https://corporate.exxonmobil.com/news/news-releases/2024/0624_exxonmobil-adds-air-liquide-to-worlds-largest-low-carbon-hydrogen-project", "2024-06-24")
PEP_REPORT = source("PepsiCo · 2025 연차보고서", "https://www.pepsico.com/docs/pepsico-5v9wci20/media/Files/investors/pepsico-2025-annual-report.pdf", "2025-12-27")
PLD_CLIENTS = source("Prologis · 2025 Q3 고객·운영 보충 자료", "https://ir.prologis.com/financials/sec-filings/content/0001193125-25-239551/pld-ex99_1.htm", "2025-09-30")
CAT_MINING = source("Caterpillar · BHP·Rio Tinto 전기 트럭 시험", "https://www.cat.com/en_US/news/machine-press-releases/bhp-rio-tinto-caterpillar-launch-battery-electric-haul-truck.html", "2026-06-23")
NVO_REPORT = source("Novo Nordisk · 2025 Form 20-F", "https://annualreport.novonordisk.com/2025/_assets/downloads/novo-nordisk-form-20-f-2025.pdf", "2025-12-31")
TMO_SANOFI = source("Thermo Fisher · Sanofi 생산시설 인수·제조 계약", "https://ir.thermofisher.com/investors/news-events/news/news-details/2025/Thermo-Fisher-Scientific-Completes-Acquisition-of-Sanofis-Ridgefield-New-Jersey-Site/default.aspx", "2025-09-02")
IBM_SAP = source("IBM · SAP 클라우드 ERP 협력", "https://newsroom.ibm.com/2025-01-07-RISE-with-SAP-on-IBM-Power-Virtual-Server-to-Help-Accelerate-Transformation-with-SAP-S-4HANA", "2025-01-07")
IBM_CARLSBERG = source("IBM · Carlsberg ERP 전환 계약", "https://ncee.newsroom.ibm.com/Carlsberg-Partners-with-IBM", "2025-05-26")
NEE_GENERATION = source("NextEra Energy · 2024 Q4 실적 설명", "https://www.investor.nexteraenergy.com/~/media/Files/N/NEE-IR/news-and-events/events-and-presentations/2025/Final_Q4%202024%20Script.pdf", "2025-01-24")




PUBLIC_COMPANIES = {
    "AMAT": profile("Applied Materials", source("Applied Materials · 공식 사업 소개", "https://www.appliedmaterials.com/us/en/about.html"),
        "반도체·디스플레이를 제조하는 장비와 재료 공학 솔루션을 제공합니다.",
        "칩·디스플레이 제조 시스템과 관련 서비스 제공이 사업의 기반입니다.",
        [("반도체 제조 장비", "재료를 형성·가공하는 제조 공정 솔루션"), ("디스플레이·서비스", "디스플레이 제조 장비와 생산 지원")],
        "반도체·디스플레이 제조사가 사용합니다.", "전용 부품과 외부 상용 부품·모듈을 조립·통합·검사해 시스템을 제조합니다."),
    "LRCX": profile("Lam Research", source("Lam Research · 공식 제품·고객 지원", "https://www.lamresearch.com/company/company-overview/"),
        "반도체 제조 공정의 식각·증착·세정 장비와 관련 생산 지원을 제공합니다.",
        "반도체 공정 장비 판매와 설치 장비의 서비스·부품·업그레이드가 사업의 기반입니다.",
        [("식각·증착", "반도체의 물질층을 제거하거나 쌓는 공정 장비"), ("세정·고객 지원", "공정 세정과 장비 서비스·부품·업그레이드")]),
    "KLAC": profile("KLA", source("KLA · 2026 Form 10-K", "https://ir.kla.com/sec-filings/all-sec-filings/content/0000319201-26-000027/klac-20260630.htm", "2026-06-30"),
        "반도체와 전자 제조 과정의 결함 검사·계측·공정 제어 및 수율 관리 솔루션을 공급합니다.",
        "공정 제어·제조 장비와 데이터 분석 제품·서비스를 판매합니다.",
        [("검사·계측", "웨이퍼·마스크·칩의 결함과 공정 상태 확인"), ("제조·데이터 솔루션", "패키징·PCB 등의 공정 장비와 데이터 분석")]),
    "ONTO": profile("Onto Innovation", source("Onto Innovation · 공식 사업·제품 소개", "https://ontoinnovation.com/about-us/"),
        "웨이퍼에서 첨단 패키징까지 검사·3D 계측·공정 분석 솔루션을 제공합니다.",
        "공정 제어 장비·분석 솔루션과 판매·서비스 조직을 통해 고객을 지원합니다.",
        [("3D 계측·결함 검사", "트랜지스터·배선·웨이퍼·패키지의 구조와 결함 확인"), ("첨단 패키징·분석", "패키징 노광과 공장 분석 솔루션")]),
    "MCD": profile("McDonald’s", MCD_REPORT,
        "맥도날드는 직영점 운영과 가맹점 사업을 함께 하는 외식 기업입니다. 음식 판매 외에 가맹점의 브랜드·운영 체계와 점포 부동산을 관리합니다.",
        "직영점 음식 매출과 가맹점 임대료·로열티·초기 수수료가 매출 원천입니다. 가맹점이 손님에게 받은 전체 매출은 맥도날드 본사의 연결 매출과 다릅니다.",
        [("외식·매장", "버거·치킨·감자튀김·커피 등을 매장·드라이브스루·배달로 판매"),
         ("가맹·부동산", "브랜드와 운영 체계를 제공하고 점포 임대료·로열티 등을 수취")],
        "식사 구매자는 일반 소비자이고, 본사의 가맹 매출은 가맹 사업자에게서 발생합니다.",
        "쇠고기·닭고기·감자·커피·포장재 공급, 인건비·임대료·물류가 운영과 연결됩니다. 원재료 공급 계약의 범위는 국가마다 다릅니다.",
        "공시는 간편 외식 시장을 경쟁 범위로 정의합니다. 가격·편의성·서비스·메뉴·제품 품질로 경쟁하며, 식품 제조업과 구분되는 외식 사업입니다."),
    "ASML": profile("ASML", ASML_REPORT,
        "반도체 회로를 웨이퍼에 인쇄하는 EUV·DUV 노광 장비와 계측·검사 솔루션을 공급합니다.",
        "새 노광 시스템의 판매와 이미 설치된 장비의 유지보수·업그레이드가 매출 원천입니다. 제품별 납품·고객 인수 시점이 공시 매출 인식에 영향을 줍니다.",
        [("EUV·High NA EUV", "첨단 공정용 극자외선 노광 시스템"), ("DUV", "심자외선 노광 시스템"),
         ("설치 장비 서비스", "유지보수·부품·생산성 업그레이드")],
        "파운드리·메모리·종합 반도체 제조사가 장비를 구매합니다.",
        "광학계·레이저·정밀 모듈 등 외부 공급망과 고객 팹 설치·가동 환경이 중요합니다. Carl Zeiss SMT가 핵심 광학계를 공급합니다.",
        "공시에 명시된 DUV 경쟁사는 Canon과 Nikon입니다. DUV 경쟁 관계를 모든 EUV 제품의 동일한 경쟁 관계로 확대하지 않습니다."),
    "MU": profile("Micron Technology", MU_REPORT,
        "데이터센터·모바일·자동차 등에서 사용하는 DRAM·NAND·NOR 메모리와 저장장치를 설계·제조합니다.",
        "메모리 반도체와 SSD 등 제품 판매로 매출이 발생합니다. DRAM과 NAND의 제품 구성·판매 단가·출하량을 구분해서 확인해야 합니다.",
        [("DRAM·HBM", "작업용 메모리와 AI 가속기용 고대역폭 메모리"), ("NAND·SSD", "비휘발성 저장용 반도체와 저장장치")],
        "클라우드·반도체 시스템·기기 제조사 등이 고객입니다. 명시되지 않은 대형 고객 이름은 추정하지 않습니다.",
        "메모리 팹의 생산·첨단 공정 전환과 조립·검사 설비가 사업과 연결됩니다.",
        "DRAM·NAND 공급 증가와 경쟁사의 설비 투자, 중국 메모리 업체의 진입이 공시 위험 요인에 포함됩니다."),
    "IBM": profile("IBM", IBM_SAP,
        "기업의 하이브리드 클라우드·AI 도입과 업무 시스템 전환을 지원하는 소프트웨어·인프라·컨설팅 기업입니다.",
        "기업용 소프트웨어와 인프라 제공, 구축·전환·운영 컨설팅 서비스에서 매출이 발생합니다.",
        [("하이브리드 클라우드·AI", "Red Hat OpenShift·watsonx 등 기업 시스템"), ("컨설팅·IBM Power", "ERP 전환·운영 지원과 서버·클라우드 인프라")],
        "금융·통신·의료 등 기업과 공공기관이 주요 사용 집단입니다."),
    "SAP": profile("SAP", IBM_SAP,
        "재무·구매·인사·공급망·고객 관리 등 기업 핵심 업무를 연결하는 ERP·클라우드 애플리케이션을 제공합니다.",
        "기업용 소프트웨어와 클라우드 서비스 제공이 사업의 기반입니다. 클라우드 전환 프로젝트에는 구축·운영 파트너가 참여합니다.",
        [("SAP S/4HANA Cloud", "기업 자원관리 시스템"), ("RISE with SAP", "ERP 클라우드 전환 프로그램")], "기업의 업무 부서와 IT 조직이 고객입니다."),
    "PEP": profile("PepsiCo", PEP_REPORT,
        "스낵·간편 식품과 음료를 생산·판매하는 기업입니다. 소비자는 브랜드 제품을 구매하고 유통사·보틀러가 판매망에 참여합니다.",
        "완제품 판매와 일부 음료 농축액 판매에서 매출이 발생합니다. 독립 보틀러를 거치는 간접 매출과 직접 유통 매출을 구분합니다.",
        [("식품·스낵", "Frito-Lay·Quaker 등의 식품 브랜드"), ("음료", "Pepsi·Gatorade 등의 음료·농축액")],
        "대형 유통망·도매상·보틀러 등으로 판매합니다. 2025년 Walmart 및 계열사 관련 매출은 연결 매출의 14%이며 직·간접 매출을 포함합니다.",
        "농산물·식품 재료·포장재·에너지·운송과 물류망이 제조·유통과 연결됩니다."),
    "TMO": profile("Thermo Fisher Scientific", TMO_SANOFI,
        "연구·분석·진단에 필요한 장비·시약·소모품과 제약 개발·위탁 생산 서비스를 제공합니다.",
        "연구 제품 공급과 분석·제약 서비스 계약에서 매출이 발생합니다. 제품 판매와 의약품 개발·생산 서비스의 고객 수요가 다릅니다.",
        [("연구·실험실 제품", "Thermo Scientific·Applied Biosystems·Invitrogen·Fisher Scientific"),
         ("제약 개발·생산 서비스", "Patheon·PPD 등을 통한 개발 지원·위탁 제조")],
        "연구기관·실험실·제약·바이오 기업 등이 고객입니다. Sanofi 치료제의 충전·포장 제조 계약이 공개되어 있습니다."),
    "NVO": profile("Novo Nordisk", NVO_REPORT,
        "당뇨병·비만과 관련 만성 질환의 치료제를 연구·개발·생산하는 제약 기업입니다.",
        "의약품 판매가 매출 원천입니다. 지역별 판매와 치료 분야별 구성을 구분하며 유통·보험 급여 조건을 함께 확인해야 합니다.",
        [("당뇨병·비만 치료", "인슐린과 GLP-1 관련 치료제 등"), ("희귀 질환 치료", "관련 전문 의약품")],
        "의약품 유통망을 통해 의료기관·환자에게 공급합니다.",
        "연구개발·생산 역량·허가·특허·약가와 보험 급여 조건이 사업의 주요 확인 항목입니다.",
        "공시는 글로벌 당뇨병 시장에서 Eli Lilly를 주요 경쟁 기업으로 명시합니다."),
    "NEE": profile("NextEra Energy", NEE_GENERATION,
        "규제 전력 사업 FPL과 발전·재생에너지·저장장치 사업을 함께 운영하는 에너지 기업입니다.",
        "전력 공급과 발전·저장 프로젝트를 통해 매출이 발생합니다. 규제 전력 사업과 에너지 자원 사업의 비용·계약 구조를 구분합니다.",
        [("FPL", "플로리다 전력 사업"), ("NextEra Energy Resources", "발전·재생에너지·저장장치 프로젝트")]),
}

# Nonlisted or foreign entities use vetted local registry keys, never guessed US
# tickers. The linked company can have its own page without an encyclopedia ID.
PRIVATE_COMPANIES = {
    "openai": profile("OpenAI", source("Microsoft · OpenAI 계약 개정", "https://blogs.microsoft.com/blog/2026/04/27/the-next-phase-of-the-microsoft-openai-partnership/", "2026-04-27"),
        "AI 모델과 관련 제품을 개발·제공하는 기업입니다. Microsoft와 모델·제품 IP 라이선스와 클라우드 협력 관계를 유지합니다.",
        "모델·제품 제공 사업을 운영하며 Microsoft에 대한 매출 배분 조건이 공개되어 있습니다. 이 자료는 전체 매출·이익 수치를 공개하지 않습니다.",
        [("AI 모델·제품", "모델·제품 IP 라이선스와 클라우드 제공 협력")]),
    "anthropic": profile("Anthropic", source("Microsoft · NVIDIA·Anthropic 협력", "https://blogs.microsoft.com/blog/2025/11/18/microsoft-nvidia-and-anthropic-announce-strategic-partnerships/", "2025-11-18"),
        "Claude AI 모델을 개발하는 기업입니다. 클라우드 플랫폼을 통해 기업이 Claude를 이용할 수 있도록 협력합니다.",
        "Claude 모델 제공과 컴퓨팅 용량 계약이 공개되어 있습니다. 발표된 투자·구매 약정은 실제 완료된 매출이나 지출과 구분합니다.",
        [("Claude", "기업용 AI 모델과 클라우드 모델 접근")]),
    "carl-zeiss-smt": profile("Carl Zeiss SMT", ASML_REPORT, "ASML 노광 장비에 사용되는 핵심 광학계를 공급하는 기업입니다.", "반도체 제조용 광학계 공급 사업이 공식 보고서에 명시되어 있습니다.", [("노광 광학계", "EUV·DUV 장비의 정밀 광학 부품")]),
    "trumpf": profile("TRUMPF", TRUMPF_LASER, "ASML의 EUV 노광 시스템에 사용되는 고출력 레이저를 개발·공급합니다.", "EUV 레이저 개발·공급 관계가 공식 발표되어 있습니다. 2025년 발표 당시 새 레이저의 2026년 공급은 계획이었습니다.", [("EUV 레이저", "노광용 극자외선 광원에 사용하는 고에너지 레이저")]),
    "canon": profile("Canon", ASML_REPORT, "ASML의 공시에 DUV 노광 장비 시장의 경쟁 기업으로 명시된 기업입니다.", "이 페이지는 확인된 반도체 장비 사업 관계를 정리합니다. Canon 전체 사업 매출과 동일하지 않습니다.", [("DUV 노광 장비", "공시에 확인된 경쟁 제품 범위")]),
    "nikon": profile("Nikon", ASML_REPORT, "ASML의 공시에 DUV 노광 장비 시장의 경쟁 기업으로 명시된 기업입니다.", "이 페이지는 확인된 반도체 장비 사업 관계를 정리합니다. Nikon 전체 사업 매출과 동일하지 않습니다.", [("DUV 노광 장비", "공시에 확인된 경쟁 제품 범위")]),
    "lopez-foods": profile("Lopez Foods", MCD_US, "맥도날드 미국 매장에 패티용 쇠고기를 공급하는 식품 기업입니다.", "미국 공급망의 쇠고기 공급 관계가 확인됩니다. 계약 금액과 맥도날드 의존 비중은 이 자료에서 공개되지 않습니다.", [("쇠고기", "미국 맥도날드 패티용 원료")]),
    "keystone-foods": profile("Keystone Foods", MCD_US, "맥도날드에 치킨 맥너겟용 닭고기 등 식재료를 공급합니다.", "공식 공급사 소개에서 확인된 식재료 공급 사업입니다. 공급사 소유 관계와 다른 거래는 별도 검증 항목입니다.", [("닭고기 등", "맥너겟 등 메뉴에 사용하는 식재료")]),
    "gavina": profile("Gaviña Gourmet Coffee", MCD_US, "맥카페 음료에 사용되는 커피를 공급하는 기업입니다.", "커피 공급 관계가 확인됩니다. 전체 매출과 공급 비중은 이 페이지에서 추정하지 않습니다.", [("커피", "맥카페 음료용 커피")]),
    "cargill": profile("Cargill", MCD_CA, "맥도날드 캐나다가 공개한 식품 공급 기업 중 하나입니다.", "자료는 캐나다 공급 관계를 확인하며 특정 식재료·거래액까지 명시하지는 않습니다."),
    "mccain": profile("McCain", MCD_CA, "맥도날드 캐나다의 공개 식품 공급사입니다.", "캐나다 식품 공급 관계가 확인됩니다. 자료에 없는 제품별 공급 비중은 표시하지 않습니다."),
    "mother-parkers": profile("Mother Parkers", MCD_CA, "맥도날드 캐나다의 공개 식품·음료 공급사입니다.", "캐나다 공급 관계가 확인됩니다. 자료에 없는 계약 조건은 표시하지 않습니다."),
    "saputo": profile("Saputo", MCD_CA, "맥도날드 캐나다의 공개 식품 공급사입니다.", "캐나다 공급 관계가 확인됩니다. 다른 국가의 공급 관계로 확대하지 않습니다."),
    "nestle": profile("Nestlé", MCD_CA, "맥도날드 캐나다의 공개 식품 공급사입니다.", "캐나다 식품 공급 관계가 확인됩니다. Nestlé 전체 사업 분석은 별도 공식 공시 자료가 필요합니다."),
    "danone": profile("Danone", MCD_CA, "맥도날드 캐나다의 공개 식품 공급사입니다.", "캐나다 식품 공급 관계가 확인됩니다. 전 세계 맥도날드 공급을 뜻하지 않습니다."),
    "foxconn": profile("Hon Hai Precision Industry · Foxconn", NV_US, "NVIDIA가 미국 AI 슈퍼컴퓨터 제조 협력사로 발표한 기업입니다.", "2025년 발표에 Houston 시스템 제조 시설 계획이 포함되어 있습니다. 계획을 실제 납품 매출로 계산하지 않습니다."),
    "wistron": profile("Wistron", NV_US, "NVIDIA가 미국 AI 슈퍼컴퓨터 제조 협력사로 발표한 기업입니다.", "2025년 발표에 Dallas 시스템 제조 시설 계획이 포함되어 있습니다. 완료 여부는 후속 자료에서 확인해야 합니다."),
    "spil": profile("Siliconware Precision Industries · SPIL", NV_US, "NVIDIA의 미국 AI 반도체 공급망 발표에 포함된 패키징·검사 협력사입니다.", "발표에서 확인한 조립·검사 역할을 표시합니다. 직접 납품 계약 규모는 공개되지 않습니다."),
    "air-liquide": profile("Air Liquide", XOM_AIR, "Baytown 저탄소 수소 사업의 산소·질소 공급과 수소 운송망 협력 기업입니다.", "가스 공급 설비와 파이프라인 운송 계약이 발표되었습니다. 투자 결정·허가 조건이 포함된 계획입니다."),
    "carlsberg": profile("Carlsberg", IBM_CARLSBERG, "IBM과 ERP 업무 시스템 전환 계약을 발표한 기업입니다.", "이 페이지는 IBM의 고객·시스템 전환 관계를 정리합니다. Carlsberg의 전체 사업 매출 분석을 뜻하지 않습니다."),
}




from .company_industry_catalog import PUBLIC as INDUSTRY_PUBLIC, PRIVATE as INDUSTRY_PRIVATE, EDGES as INDUSTRY_EDGES
PUBLIC_COMPANIES.update(INDUSTRY_PUBLIC)
PRIVATE_COMPANIES.update(INDUSTRY_PRIVATE)
from .company_it_research import PUBLIC as IT_PUBLIC, PRIVATE as IT_PRIVATE, EDGES as IT_EDGES
PUBLIC_COMPANIES.update(IT_PUBLIC)
PRIVATE_COMPANIES.update(IT_PRIVATE)
from .company_semiconductor_catalog import PUBLIC as SEMI_PUBLIC, PRIVATE as SEMI_PRIVATE, EDGES as SEMI_EDGES
PUBLIC_COMPANIES.update(SEMI_PUBLIC)
PRIVATE_COMPANIES.update(SEMI_PRIVATE)
from .company_energy_research import PUBLIC as ENERGY_PUBLIC, PRIVATE as ENERGY_PRIVATE, EDGES as ENERGY_EDGES
PUBLIC_COMPANIES.update(ENERGY_PUBLIC)
PRIVATE_COMPANIES.update(ENERGY_PRIVATE)
from .company_energy_refining import PUBLIC as REFINING_PUBLIC, PRIVATE as REFINING_PRIVATE, EDGES as REFINING_EDGES
PUBLIC_COMPANIES.update(REFINING_PUBLIC)
PRIVATE_COMPANIES.update(REFINING_PRIVATE)
from .company_energy_midstream import PUBLIC as MIDSTREAM_PUBLIC, PRIVATE as MIDSTREAM_PRIVATE, EDGES as MIDSTREAM_EDGES
PUBLIC_COMPANIES.update(MIDSTREAM_PUBLIC)
PRIVATE_COMPANIES.update(MIDSTREAM_PRIVATE)


PRIVATE_NAMES = {value['name']: key for key, value in PRIVATE_COMPANIES.items()}
PRIVATE_NAMES.update({'Foxconn':'foxconn', 'Hon Hai Precision Industry':'foxconn',
                      'Wistron Corporation':'wistron', 'SPIL':'spil'})


RELATIONS = {
    "TSM": [relation(name, ticker, "supplier", "2025년 공식 공급망 포상 명단에 등재 · 거래액·독점 공급 여부는 공개하지 않음", TSMC_SUPPLY)
             for name, ticker in [("ASML", "ASML"), ("Applied Materials", "AMAT"), ("Lam Research", "LRCX"),
                                  ("KLA", "KLAC"), ("Onto Innovation", "ONTO")]],
    "ASML": [relation("Carl Zeiss SMT", None, "supplier", "핵심 노광 광학계 공급 · 단일 공급 의존은 공시 위험 항목", ASML_REPORT, "carl-zeiss-smt"),
             relation("TRUMPF", None, "supplier", "EUV 고에너지 레이저 개발·공급 · 2025-10 발표 당시 새 제품의 2026년 공급은 계획", TRUMPF_LASER, "trumpf"),
             relation("Canon", None, "competitor", "DUV 노광 시스템 시장 · EUV까지 같은 경쟁 범위로 확대하지 않음", ASML_REPORT, "canon"),
             relation("Nikon", None, "competitor", "DUV 노광 시스템 시장", ASML_REPORT, "nikon")],
    "MCD": [relation("Lopez Foods", None, "supplier", "미국 패티용 쇠고기 공급", MCD_US, "lopez-foods"),
            relation("Keystone Foods", None, "supplier", "치킨 맥너겟용 닭고기 등 식재료", MCD_US, "keystone-foods"),
            relation("Gaviña Gourmet Coffee", None, "supplier", "맥카페 커피 공급", MCD_US, "gavina"),
            relation("Coca-Cola", "KO", "supplier", "캐나다 식품·음료 공급사 목록 · 다른 국가의 계약 범위를 추정하지 않음", MCD_CA),
            *[relation(name, None, "supplier", "맥도날드 캐나다 공식 식품 공급사 목록 · 제품별 계약 금액 미공개", MCD_CA, key)
              for name, key in [("Cargill", "cargill"), ("McCain", "mccain"), ("Mother Parkers", "mother-parkers"),
                                ("Saputo", "saputo"), ("Nestlé", "nestle"), ("Danone", "danone")]],
            relation("Alphabet", "GOOGL", "partner", "Google Cloud 매장 엣지·클라우드·AI 기술 협력 · 2023-12 발표 당시 확대는 계획", MCD_GOOGLE),
            relation("Accenture", "ACN", "partner", "매장·고객 경험 기술 도입과 디지털 역량 교육 협력", MCD_ACN)],
    "MU": [relation("NVIDIA", "NVDA", "customer", "24GB 8단 HBM3E를 H200 GPU에 공급 · 제품 페이지에 출하 명시", MU_HBM),
           relation("Samsung Electronics", "005930.KS", "competitor", "DRAM·NAND 메모리 시장 · DBS 2025-05 산업 자료 기준", MEMORY_RESEARCH),
           relation("SK hynix", "000660.KS", "competitor", "DRAM·NAND 메모리 시장 · DBS 2025-05 산업 자료 기준", MEMORY_RESEARCH)],
    "NVDA": [relation("Foxconn", None, "supplier", "Houston AI 슈퍼컴퓨터 시스템 제조 협력 · 2025-04 발표 계획", NV_US, "foxconn"),
             relation("Wistron", None, "supplier", "Dallas AI 슈퍼컴퓨터 시스템 제조 협력 · 2025-04 발표 계획", NV_US, "wistron"),
             relation("Amkor", "AMKR", "supplier", "미국 AI 반도체 패키징·검사 협력 · 발표 계획", NV_US),
             relation("SPIL", None, "supplier", "미국 AI 반도체 패키징·검사 협력 · 발표 계획", NV_US, "spil"),
             relation("SK hynix", "000660.KS", "supplier", "AI 플랫폼용 메모리 공동개발·공급 협력 · 2026-06 발표 계획 포함", NV_HYNIX)],
    "LIN": [relation("Samsung Electronics", "005930.KS", "customer", "평택 팹 고순도 질소·산소·아르곤·수소 공급 · 기존 공급과 신규 설비 확장 계획을 구분", LIN_SAMSUNG)],
    "XOM": [relation("Air Liquide", None, "supplier", "Baytown 저탄소 수소·암모니아용 산소·질소 공급 설비·운송 계약 · 투자·허가 조건부 계획", XOM_AIR, "air-liquide")],
    "PEP": [relation("Walmart", "WMT", "customer", "Walmart·Sam’s Club 등 계열사 관련 직·간접 판매 · 2025년 매출 14% 포함, 전부 직접 거래는 아님", PEP_REPORT)],
    "PLD": [relation(name, ticker, "customer", "물류 부동산 임차 고객 · 2025 Q3 고객 목록, 상품 구매 고객을 뜻하지 않음", PLD_CLIENTS)
            for name, ticker in [("Amazon", "AMZN"), ("Home Depot", "HD"), ("FedEx", "FDX"), ("UPS", "UPS"),
                                 ("GXO Logistics", "GXO"), ("Walmart", "WMT"), ("PepsiCo", "PEP"), ("MercadoLibre", "MELI"),
                                 ("Lululemon", "LULU"), ("Burlington Stores", "BURL"), ("Ryder", "R"), ("Wayfair", "W")]],
    "CAT": [relation("BHP", "BHP", "partner", "배터리 전기식 광산 운반 트럭의 시험 협력 · 시험을 상용 대량 판매로 표시하지 않음", CAT_MINING),
            relation("Rio Tinto", "RIO", "partner", "배터리 전기식 광산 운반 트럭의 시험 협력", CAT_MINING)],
    "NVO": [relation("Eli Lilly", "LLY", "competitor", "글로벌 당뇨병 치료제 시장 · Novo Nordisk 2025 공시 명시", NVO_REPORT)],
    "TMO": [relation("Sanofi", "SNY", "customer", "Ridgefield 시설 인수 완료 후 Sanofi 치료제 충전·포장 제조 지속 계약", TMO_SANOFI)],
    "IBM": [relation("SAP", "SAP", "partner", "IBM Power Virtual Server와 SAP S/4HANA Cloud ERP 전환·구축 협력", IBM_SAP),
            relation("Carlsberg", None, "customer", "ERP 전환·구축·운영 지원 계약", IBM_CARLSBERG, "carlsberg")],
    "NEE": [relation("GE Vernova", "GEV", "partner", "천연가스 발전 프로젝트 협력 · 2025-01 실적 발표 계획, GE Aerospace와 별도 기업", NEE_GENERATION)],
}


for _symbol, _edges in INDUSTRY_EDGES.items():
    RELATIONS.setdefault(_symbol, []).extend(_edges)
for _symbol, _edges in IT_EDGES.items():
    RELATIONS.setdefault(_symbol, []).extend(_edges)
for _symbol, _edges in SEMI_EDGES.items():
    RELATIONS.setdefault(_symbol, []).extend(_edges)
for _symbol, _edges in ENERGY_EDGES.items():
    RELATIONS.setdefault(_symbol, []).extend(_edges)
for _symbol, _edges in REFINING_EDGES.items():
    RELATIONS.setdefault(_symbol, []).extend(_edges)
for _symbol, _edges in MIDSTREAM_EDGES.items():
    RELATIONS.setdefault(_symbol, []).extend(_edges)


def enrichment(symbol):
    value = deepcopy(PUBLIC_COMPANIES.get(symbol, {}))
    value.pop("name", None)
    value.setdefault("relations", []).extend(deepcopy(RELATIONS.get(symbol, [])))
    return value if value.get("relations") or value.get("brief") else {}


def private_profile(key):
    value = deepcopy(PRIVATE_COMPANIES[key])
    return dict(**value, registry_id=key)
