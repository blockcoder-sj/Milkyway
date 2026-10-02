"""Edited oilfield-service and equipment research, with actual counterparties.

Equipment orders, field work and proposed power projects have different stages.
Customer concentrations are issuer revenue shares, never industry market shares.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source
from .company_energy_upstream import EXE_CREWS, RANGE_COMPLETE, RANGE_DRILL
from .company_energy_services import KGS_BKR

SYMBOLS = ('SLB', 'BKR', 'HAL', 'PTEN', 'PUMP', 'LBRT', 'SND', 'AESI',
           'FLOC', 'ACDC', 'DTI', 'KLXE')
ANNUAL = {symbol: report(symbol) for symbol in SYMBOLS}
QUARTER = {symbol: report(symbol, 'quarter') for symbol in SYMBOLS}

SLB_ARAMCO = source('SLB · Aramco 유정 건설 4건 수주',
    'https://www.slb.com/newsroom/press-release/2026/pr-2026-0924-slb-aramco', '2026-09-24')
SLB_ROVUMA = source('SLB OneSubsea · ExxonMobil Rovuma 해저 시스템 수주',
    'https://www.slb.com/newsroom/press-release/2026/pr-2026-0929-slb-oss-xom-rovuma', '2026-09-29')
ONESUBSEA = source('OneSubsea · 공동사업·제품 역할',
    'https://www.onesubsea.slb.com/about/investors', '열람 2026-10-03')
SLB_KELVION = source('SLB · Kelvion 인수 계약·완료 조건',
    'https://www.slb.com/newsroom/press-release/2026/pr-2026-0831', '2026-08-31')
BKR_CHART = source('Baker Hughes · Chart 인수 완료·새 부문',
    'https://investors.bakerhughes.com/news/press-releases/news-details/2026/Baker-Hughes-Completes-Acquisition-of-Chart-Industries/default.aspx', '2026-07-16')
BKR_NLNG = source('Baker Hughes · Nigeria LNG 터보기계 장기 정비 계약',
    'https://www.bakerhughes.com/company/news/baker-hughes-extends-longterm-service-agreement-nigeria-lng-support-critical-expansion', '2026-06-29')
HAL_YPF = source('Halliburton · YPF Vaca Muerta 완결 수주',
    'https://www.halliburton.com/en/about-us/press-release/ypf-awards-halliburton-multibillion-dollar-long-term-unconventional-completions-contract-argentina', '2026-04-13')
HAL_ENI = source('Halliburton · Eni Cronos 심해 유정 건설·완결 수주',
    'https://www.halliburton.com/en/about-us/press-release/halliburton-awarded-bundled-deepwater-well-construction-completions-contract', '2026-09-15')
HAL_BASRA = source('Halliburton · Basra Oil 유전 관리·EPCM 수주',
    'https://www.halliburton.com/en/about-us/press-release/basra-oil-company-awards-halliburton-contract-to-advance-oil-and-gas-development-in-southern-iraq', '2026-07-20')
HAL_VOLTA = source('Halliburton·VoltaGrid · 400 MW 장비 제조 예약',
    'https://ir.halliburton.com/news-releases/news-release-details/voltagrid-and-halliburton-make-400-mw-power-commitment', '2025-12-11')
PUMP_COTERRA = source('PROPWR · Coterra 계열 현장 microgrid 계약',
    'https://ir.propetroservices.com/news-events/press-releases/detail/138/propwr-secures-distributed-microgrid-contract-with-coterra-energy-and-adds-190-megawatts-in-new-orders', '2025-12-12')
LIBERTY_BERGEN = source('Liberty · Bergen 발전기·Piller 전력 안정화 장비 주문',
    'https://libertyenergy.com/bergen-engines-liberty-energy-to-advance-power-services-for-ai-data-centers/', '2026-05-08')
LIBERTY_POWERBRIDGE = source('Liberty·PowerBridge · Alpha 데이터센터 공동 개발',
    'https://libertyenergy.com/liberty-energy-and-powerbridge-form-strategic-joint-venture-to-support-powered-data-center-campus-development/', '2026-07-22')
LIBERTY_SLB = source('Liberty·SLB · 데이터센터·발전 협력 추진',
    'https://libertyenergy.com/slb-liberty-energy-to-form-strategic-alliance-for-data-center-infrastructure-and-power/', '2026-07-14')
ATLAS_CAT = source('Atlas · Caterpillar 발전 장비 공급 framework',
    'https://ir.atlas.energy/news-events/press-releases/detail/66/atlas-energy-solutions-enters-agreement-with-caterpillar', '2026-03-10')
ATLAS_KODIAK = source('Kodiak AI · Atlas 자율 모래 운송의 실제 운영·확장',
    'https://kodiak.ai/news/atlas-driverless-permian-expansion', '2026-07-31')
KODIAK_Q2 = source('Kodiak AI · 2026년 2분기 실제 운전 차량',
    'https://investors.kodiak.ai/news-releases/news-release-details/kodiak-ai-reports-second-quarter-2026-results-and-advances', '2026-08-06')
FLOWCO_PACKAGE = source('Flowco · Estis 가스 lift 패키지의 실제 OEM 부품',
    'https://www.flowco-inc.com/products-services/conventional-gas-lift/compressors/3306ta-jgq-2', '열람 2026-10-03')
FLOWCO_VALIANT = source('Flowco · Valiant 인수 완료·ESP 제품 범위',
    'https://ir.flowco-inc.com/news-events/news/news-details/2026/Flowco-Completes-Acquisition-of-Valiant-Artificial-Lift-Solutions/default.aspx', '2026-03-03')
FLOWCO_ESP = source('Flowco · Valiant의 인공 채유·유체 이동 제품',
    'https://www.flowco-inc.com/blog-articles/flowco-adds-esps-to-the-production-optimization-platform-introducing-valiant-by-flowco', '2026-03-30')
KLX_WOLF = source('KLX · Wolf Pack 일부 자산 인수 계약',
    'https://www.sec.gov/Archives/edgar/data/1738827/000173882726000023/klxe-20260602.htm', '2026-06-02')
PROFRAC_SEISMOS = source('ProFrac·Seismos · 현장 폐쇄루프 파쇄 수행',
    'https://ir.pfholdingscorp.com/news-events/press-releases/detail/66/profrac-and-seismos-deploy-closed-loop-fracturing-at', '2026-03-12')

PUBLIC = {
    'SLB': profile('SLB', ANNUAL['SLB'],
        '유전의 평가·시추·완결·생산 장비와 디지털 기술을 공급합니다. OneSubsea의 해저 생산 시스템, ChampionX의 생산 약품·인공 채유와 데이터센터·탄소포집 사업도 연결합니다.',
        '2025년 연결 매출은 35,708,000,000달러로 제품 14,508,000,000·서비스 21,200,000,000입니다. 5개 부문 합계 36,648,000,000에는 중복 인식이 있어 940,000,000을 제거해야 합니다. 부문 합계로 전체 구성비를 만들지 않습니다.',
        [('저류층·유정 평가', '암석·유체 측정, 검층·시험·탄성파 및 유정 자극으로 개발·생산 계획에 필요한 데이터를 제공합니다.'),
         ('시추·유정 건설', '방향성 시추·비트·시추 유체·시멘팅·완결과 통합 유정 건설을 제공합니다.'),
         ('생산 시스템', '해저·지상 생산 장비, 밸브·wellhead·인공 채유와 생산 약품을 공급·정비합니다.'),
         ('Digital·신규 인프라', '데이터·소프트웨어·원격 운영, 데이터센터 모듈 및 탄소포집 장비·운영입니다.')],
        customers='국영·국제·독립 생산자가 구매자입니다. 통합 유정 건설과 해저 시스템의 수주, 장비 납품·전체 프로젝트 가동 단계를 구분합니다.',
        inputs='임대·제조·현장 운영에 금속·전자부품·약품·압력 장비·전력·정비·숙련 인력이 필요합니다. 장비 직접 제조와 외부 도구·부품·현장 서비스 구매가 함께 존재합니다.',
        competition='평가·시추·완결·생산·해저 시스템별로 경쟁 상대가 다릅니다. 통합 서비스 회사의 전체 매출을 미국 수압파쇄 시장 점유율로 표시하지 않습니다.'),
    'BKR': profile('Baker Hughes', BKR_CHART,
        '유전 서비스·장비와 가스·LNG·발전·산업용 터보기계 및 정비를 공급합니다. 2026년 7월 Chart 인수 완료 후 열관리·공기/가스 장비와 생애주기 서비스를 세 번째 부문으로 편입했습니다.',
        '2025년 매출 27,733,000,000달러는 OFSE 14,324,000,000·IET 13,409,000,000입니다. 제품 18,216,000,000·서비스 9,517,000,000은 같은 매출의 다른 구분이며 Chart 2026년 편입은 포함하지 않습니다.',
        [('OFSE · 유전 서비스·장비', '저류층 평가·시추·완결·생산 최적화와 지상·해저 시스템을 공급합니다.'),
         ('IET · 산업·에너지 기술', '가스 압축·터빈·LNG 설비·발전과 산업용 계측·제어·정비를 제공합니다.'),
         ('Chart · 2026년 편입', '공기·가스 처리, 열교환·열관리와 관련 정비입니다. 2025년 Baker Hughes 부문 표와 기간이 다릅니다.')],
        customers='생산자·LNG 액화사·발전·산업 고객입니다. 유전 서비스, 산업 설비 공급과 장기 정비 고객은 서로 다른 용도로 제품·서비스를 구매합니다.',
        inputs='터빈·압축기·열교환기용 금속·정밀 가공·전자 제어·공급망과 제조·현장 정비 인력이 필요합니다. 제조 장비·재고와 장기 현장 정비의 비용·인력 구조를 구분합니다.',
        competition='유전 서비스는 서비스 종류·지역, 산업 장비는 효율·납기·설치기반·정비 계약으로 경쟁합니다. 공급 장비의 MW와 발전 사업자의 실제 운영 MW를 구별합니다.'),
    'HAL': profile('Halliburton', ANNUAL['HAL'],
        '원유·가스 유정의 시추·평가부터 완결·생산 지원까지 장비·약품·현장 서비스를 공급합니다. Landmark 소프트웨어와 ZEUS 전기식 파쇄·OCTIV 자동화도 제공합니다.',
        '2025년 연결 매출 22,184,000,000달러는 완결·생산 12,782,000,000·시추·평가 9,402,000,000입니다. 제품 6,455,000,000·서비스 15,729,000,000과 지역별 표는 같은 매출을 다른 기준으로 나눈 것입니다.',
        [('완결·생산', '수압파쇄·시멘팅·와이어라인·완결 도구·인공 채유·생산 약품과 유정 개입 서비스를 제공합니다.'),
         ('시추·평가', '방향성 시추·유체·검층·시험·비트·유정 건설과 지하 데이터·소프트웨어를 제공합니다.'),
         ('통합 프로젝트', '개별 현장 서비스 외에 개발 계획·실행·EPCM을 묶은 계약을 수행합니다.')],
        customers='국영·국제·독립 생산자가 고객이며 개발 계획·신규 유정 건설·완결과 가동 중 생산 지원이 별도 수요입니다. 수주한 프로젝트의 전체 유전 매출을 Halliburton 매출로 표시하지 않습니다.',
        inputs='파쇄 모래·약품·물·연료·장비·도구·금속·운송·인력이 필요합니다. 외부 도구·소모재 구매와 장비 자체 제조·정비가 서로 다른 공급 역할입니다.',
        competition='완결·평가·시추·디지털·통합 프로젝트별로 SLB·Baker Hughes 및 전문 업체와 경쟁합니다. 미국 파쇄의 경쟁 범위와 해외 해저 유정 건설을 같은 시장으로 합산하지 않습니다.'),
    'PTEN': profile('Patterson-UTI Energy', ANNUAL['PTEN'],
        '미국 등의 육상 시추, NexTier 완결·파쇄 및 Ulterra 시추 비트 사업을 운영합니다. 장비·작업팀을 제공해 생산자의 유정 건설을 지원하며 생산자 자체의 원유·가스 판매업과 다릅니다.',
        '2025년 매출 4,826,624,000달러는 완결 2,892,247,000·시추 서비스 1,557,642,000·시추 제품 343,707,000·기타 33,028,000입니다. 시추 리그 계약과 비트 판매·파쇄 작업의 단가는 서로 다른 기준입니다.',
        [('계약 시추', '육상 리그·작업팀·자동화·방향성 시추로 유정을 건설합니다. 미국·Colombia·Ecuador에서 운영합니다.'),
         ('NexTier 완결', '파쇄·와이어라인·pumpdown·시멘팅, 현장 천연가스 연료·모래 배송을 연결합니다.'),
         ('Ulterra 시추 제품', 'PDC 비트와 기타 시추 제품을 제조·수리해 에너지·지열·광업 고객에 공급합니다.')],
        customers='주요·독립 생산자가 구매자입니다. 2025년 최대 고객은 597,000,000달러·약 12%, 상위 5개는 약 39%로 이름은 해당 집중도 표에 없습니다. 집중도 수치를 실명 수주 자료와 임의로 연결하지 않습니다.',
        inputs='금속·비트 원재료·리그/펌프 부품·모래·약품·가스·인력·현장 하도급이 필요합니다. Ulterra 관련 NOV 특허 분쟁을 장비 공급 계약으로 전환하지 않습니다.',
        competition='계약 시추·완결 서비스·비트 제품별 시장이 다릅니다. ProFrac과 KLX의 공시가 완결·현장 서비스 경쟁 업체로 명시합니다.'),
    'PUMP': profile('ProPetro Holding', ANNUAL['PUMP'],
        'Permian 중심의 파쇄·와이어라인·시멘팅과 PROPWR 분산 발전을 공급합니다. FORCE 전기식 파쇄 fleet와 Silvertip·AquaProp의 현장 지원을 결합합니다.',
        '2025년 연결 매출 1,269,158,000달러입니다. 파쇄 929,210,000·와이어라인 209,034,000·시멘팅 130,266,000·발전 1,538,000의 합계에서 내부거래 890,000을 제거합니다. 새 발전 장비 주문을 연간 실현 매출에 더하지 않습니다.',
        [('파쇄·전기식 FORCE', '장비·전담 인력·모래/소모재 조달·작업 데이터와 분석을 묶어 완결 서비스를 제공합니다.'),
         ('와이어라인·시멘팅', '유정 내 도구 설치·천공과 케이싱 고정·격리 서비스를 제공합니다.'),
         ('PROPWR 발전', '유전 현장·데이터센터용 가스 발전기·microgrid를 설치·운영합니다.')],
        customers='2025년 ExxonMobil 24.9%·Occidental 13.7%·EOG 12.1%·Permian Resources 11.2%입니다. 회사 매출 집중도이며 고객의 파쇄 비용 비중이나 Permian 시장점유율이 아닙니다.',
        inputs='모래·약품·물·펌프/유체 부품·인력·전력과 발전 장비가 필요합니다. 발전 장비 구매·자금 조달, 파쇄의 현장 연료·정비·소모재 비용은 다른 역할입니다.',
        competition='미국 파쇄는 HAL·Liberty·ProFrac·Patterson 등과 작업 능력·신뢰성·비용·장비로 경쟁합니다. 발전 주문과 파쇄 가동 fleet를 같은 단위로 합산하지 않습니다.'),
    'LBRT': profile('Liberty Energy', ANNUAL['LBRT'],
        '북미 중심의 파쇄·와이어라인·모래 물류·현장 가스·CNG와 작업 데이터를 통합 제공합니다. Liberty Power Innovations는 별도로 현장·데이터센터 분산 발전과 제어를 개발합니다.',
        '2025년 연결 매출은 4,006,116,000달러입니다. 공시는 단일 사업 부문으로 보고해 파쇄·모래·발전을 나눈 연간 매출 금액을 제공하지 않습니다. 관련자/비관련자 매출 분리를 제품별 구성으로 바꾸지 않습니다.',
        [('완결·현장 통합', '파쇄·와이어라인, 모래 생산/배송과 현장 가스·CNG 공급을 묶습니다. 2025년 말 가동 파쇄 fleet는 약 40개입니다.'),
         ('PropX·모래 물류', '모래 운반·현장 저장·공급 기술로 완결 현장의 물류를 지원합니다.'),
         ('LPI · 발전·제어', 'IMG의 설계·운영·제어 역량을 편입하고 가스 발전·전력 안정화와 데이터센터 인프라를 개발합니다.')],
        customers='2025년 OXY·XTO Energy는 각각 매출 10% 초과이며 상위 5개 고객 합계는 39%입니다. 정확한 개별 비율이 없는 회사에 임의 비율을 붙이지 않습니다.',
        inputs='모래·약품·장비·정비 부품·가스·인력과 발전 엔진·전력 안정화가 필요합니다. SLB 계열의 약품·프로판트·장비·정비 부품 구매는 2025년 공시에서 지속 거래로 확인됩니다.',
        competition='ProFrac·HAL·ProPetro·Patterson 등과 미국 완결 작업을 경쟁합니다. 발전은 장비 공급·운영·전력 품질·현장 인허가와 계약 기간을 별도로 비교합니다.'),
    'SND': profile('Smart Sand', ANNUAL['SND'],
        'Northern White 규사를 생산해 파쇄용 프로판트로 판매하고 철도·환적·현장 SmartSystems로 배송합니다. 지역 내 모래와 다른 제품·수송 구조를 가진 업체입니다.',
        '2025년 매출 330,153,000달러는 모래 325,762,000·SmartSystems 4,391,000입니다. 제품 구분과 보고 부문에 같은 두 항목이 반복돼 합산하지 않습니다. 미국 298,252,000·Canada 31,901,000은 다른 지역 구분입니다.',
        [('Northern White 모래', '입도·강도 등 사양에 맞춘 규사를 선별·처리해 생산자·완결 서비스사에 판매합니다.'),
         ('철도·환적', 'Wisconsin·Illinois 광산과 환적 터미널을 여러 Class I 철도에 연결합니다.'),
         ('SmartSystems', '현장 모래 저장·공급 장비와 관련 서비스입니다. 전체 모래 판매량과 별개인 수익 항목입니다.')],
        customers='2025년 EQT 27.7%·EOG 10.9%, 그 외 99개 고객입니다. 2024년 EQT·Encino·Liberty 집중도는 다른 연도이며 각 연도의 실명·비율을 그대로 구분합니다.',
        inputs='모래 광물권·광산 설비·전기/가스·철도·환적·트럭·현장 장비가 필요합니다. Oakdale은 CPKC/Union Pacific, Ottawa/Peru는 BNSF, Blair는 Canadian National 운송 경로를 이용합니다.',
        competition='제품의 입도·강도·일관성, 광산 위치와 고객 현장까지의 배송 비용·신뢰성이 경쟁 요소입니다. 상장 규사 업체 시총 비중을 파쇄 모래 시장점유율로 표시하지 않습니다.'),
    'AESI': profile('Atlas Energy Solutions', ANNUAL['AESI'],
        'Permian의 파쇄 모래 생산·현장 배송과 Dune Express 컨베이어를 운영합니다. Moser 편입 후 가스 분산 발전·발전 장비 임대도 제공하며 Kodiak AI 기술로 일부 모래 배송을 무인 운영합니다.',
        '2025년 매출 1,095,310,000달러는 모래·물류 1,036,759,000·발전 58,551,000입니다. 제품 477,985,000·서비스 558,774,000·발전 장비 임대 58,551,000은 다른 구분으로 합계가 일치합니다.',
        [('지역 내 모래·물류', 'Permian의 여러 생산 시설에서 dry/damp sand를 공급하고 트럭·현장 설비로 배송합니다.'),
         ('Dune Express', '42마일 전기식 컨베이어가 모래를 유정 가까운 출하 지점으로 보냅니다. 후속 현장 배송은 별도입니다.'),
         ('Moser 분산 발전', '가스 발전 장비를 임대·설치·운영하고 운송·현장 지원을 제공합니다.'),
         ('자율 배송', 'Kodiak Driver를 탑재한 Atlas 소유 트럭이 임대 도로에서 모래를 운송합니다. Kodiak Gas Services(KGS)와 다른 기업입니다.')],
        customers='생산자·완결 서비스사와 전력이 필요한 현장·산업 고객입니다. 모래의 최소구매 미달 대가 23,900,000달러는 이미 매출에 포함된 계약 항목으로 추가 제품 매출처럼 더하지 않습니다.',
        inputs='모래 광물권·로열티·컨베이어 전력·가스·트럭·운전자/원격운영·설비 정비와 발전기 조달이 필요합니다. 장비 구매·기술 이용과 생산자에게 제공하는 현장 배송·발전 서비스를 구분합니다.',
        competition='지역 내 모래의 공급·운송·현장 가용성과 분산 발전을 별도 시장으로 비교합니다. 공칭 생산능력·운송 ton·발전 MW를 매출 구성비로 환산하지 않습니다.'),
    'FLOC': profile('Flowco Holdings', QUARTER['FLOC'],
        '인공 채유·가스 lift·plunger lift와 증기/메탄 회수 시스템을 제조·임대·판매·정비합니다. Estis·Flowco Production·Flogistix와 2026년 편입한 Valiant ESP를 연결합니다. 수압파쇄 업체 ProFrac(ACDC)와 다릅니다.',
        '2025년 매출 759,719,000달러는 지상 장비 239,409,000·유정 내 부품 257,866,000·증기 회수 228,841,000·가스 패키지 33,603,000입니다. 고객 계약 매출 341,761,000 외 장비 임대 매출을 포함하며 부문 간 매출은 제거합니다.',
        [('고압·일반 가스 lift', '가압 가스를 유정에 주입해 액체를 끌어올립니다. 유정 생산 단계에 따라 장비·압력·downhole valve를 조정합니다.'),
         ('Plunger lift', '유정의 압력을 반복적으로 이용해 액체를 지상으로 올리는 도구·자동화입니다.'),
         ('증기 회수·VRU', '메탄·탄화수소 증기를 압축·회수해 판매 배관 또는 인공 채유에 연결합니다.'),
         ('가스 패키지·디지털', '자체·타사 압축 운영용 패키지를 제조하고 계측·원격 감시·제어를 제공합니다.')],
        customers='유정 생산자와 계약 가스 시스템 운영자가 구매자입니다. 계약 임대·부품 판매·현장 정비의 고객과 수익 구조를 구분하며 이름이 없는 집중도 표에 생산자 이름을 추정해 붙이지 않습니다.',
        inputs='금속·압력 부품·가스 엔진·압축기·전자 제어와 조립·현장 정비가 필요합니다. 핵심 HPGL·VRU·valve·mandrel을 국내에서 자체 제조하지만 모든 부품을 자체 생산한다는 뜻은 아닙니다.',
        competition='인공 채유 방식·가스 lift·VRU·압축 패키지별 대안이 다릅니다. 부품 제조·장비 임대와 생산자 자체 가스 판매를 같은 시장으로 분류하지 않습니다.'),
    'ACDC': profile('ProFrac Holding', ANNUAL['ACDC'],
        '수압파쇄·완결, 현지 모래 생산, 펌프·밸브·유체 장비 제조와 Flotek 약품·측정을 연결하는 수직 통합 서비스 기업입니다. Livewire를 통한 현장 발전도 보고 부문 밖 기타 사업에 포함합니다.',
        '2025년 연결 매출 1,941,800,000달러는 외부 서비스 1,692,700,000·제품 249,100,000입니다. 부문 합계 2,492,100,000에는 내부거래가 있어 순연결조정 550,300,000을 차감합니다. 제거 전 매출을 100% 구성으로 표시하지 않습니다.',
        [('완결·파쇄', '이동식 파쇄 fleet·보조 장비·작업팀으로 shale 유정을 완결합니다.'),
         ('현지 프로판트', 'Haynesville·Permian·Eagle Ford의 모래 광산을 운영해 자체·외부 완결 현장에 공급합니다.'),
         ('장비 제조', '고마력 펌프·밸브·배관·swivel·manifold·fluid end를 제조·시험합니다.'),
         ('Flotek·Livewire', 'Flotek은 약품·데이터 측정, Livewire는 현장 전력으로 서로 다른 투입 요소를 지원합니다.')],
        customers='미국 shale 생산자·서비스사가 구매자입니다. 2025년 상위 10개 고객은 연결 매출 45%·단일 고객 10% 이상은 없었습니다. 고객 이름이 없는 집중도 표를 실명 현장 소개와 임의로 연결하지 않습니다.',
        inputs='자체 모래·장비·약품을 내부 공급하면서 연료·물·부품·인력·외부 소재도 조달합니다. 내부 공급 부문의 매출을 회사 외부 매출에 다시 더하지 않습니다.',
        competition='연차보고서가 미국 완결 경쟁 업체로 Halliburton·Liberty·ProPetro·Patterson-UTI를 명시합니다. Flotek 약품 사업과 모래 사업에는 별도 경쟁 범위가 있습니다.'),
    'DTI': profile('Drilling Tools International', ANNUAL['DTI'],
        '시추·완결 도구를 임대·판매·수리하는 업체입니다. stabilizer·drill collar·reamer·casing 도구 등을 공급하며 생산자, 큰 서비스 업체와 장비 OEM을 고객으로 연결합니다.',
        '2025년 연결 매출 159,626,000달러는 도구 임대 129,562,000·제품 판매 30,064,000입니다. 서반구·동반구 부문은 내부거래 포함으로 외부 구성비에 사용하지 않으며 공시 천 달러 단위의 반올림 차이를 유지합니다.',
        [('시추 도구 임대', '도구 fleet를 현장에 배치하고 검사·수리·교체·물류로 사용을 지원합니다.'),
         ('제품·부품', '시추·완결 도구·부품을 판매하고 OEM·서비스 고객에 공급합니다.'),
         ('COMPASS·운영망', '임대 주문·현장 정보·fleet 사용을 관리하고 지역 시설에서 수리·재배치를 지원합니다.')],
        customers='2025년 서비스사 48%·생산자 48%·장비 OEM 4%입니다. BKR·HAL·SLB, Chevron·BPX·EOG·OXY 및 NOV가 실명 고객입니다. 고객군 비중은 도구 임대 시장점유율이 아닙니다.',
        inputs='특수강·정밀 가공·마모 부품·검사/수리·숙련 인력·현장 물류가 필요합니다. 인수 업체 Deep Casing Tools·European Drilling Projects·Titan Tools의 전문 도구와 지역망을 연결합니다.',
        competition='고객의 직접 도구 소유·내부 정비 및 다른 임대·전문 도구 업체와 경쟁합니다. 서반구·동반구는 지리 기준 보고 부문이며 제품과 같은 구분이 아닙니다.'),
    'KLXE': profile('KLX Energy Services', ANNUAL['KLXE'],
        '북미 생산자의 시추·완결·유정 개입·생산을 지원하는 전문 서비스 기업입니다. 코일드 튜빙·와이어라인·압력 제어·방향성 시추·현장 도구와 인력을 공급합니다.',
        '2025년 매출 636,600,000달러는 완결 356,500,000·시추 110,900,000·유정 개입 61,900,000·생산 107,300,000입니다. 서비스 종류별 표와 운영 지역 보고 부문을 구별합니다.',
        [('시추', '방향성 시추·도구·압력 제어 등 유정 건설을 지원합니다.'),
         ('완결', '와이어라인·코일드 튜빙·현장 압력 제어와 완결 관련 전문 서비스를 제공합니다.'),
         ('개입·생산', '가동 유정의 정비·개입·시험과 생산 지원입니다. 신규 시추 작업과 다른 수요입니다.')],
        customers='북미의 major·독립·지역 생산자 550곳 이상입니다. 2025년 상위 5개 고객 합계 약 31%, 단일 10% 이상 고객은 없었으며 해당 문단에 없는 고객 실명은 추정하지 않습니다.',
        inputs='도구·파이프/튜빙·부품·화학/현장 소모재·연료·차량·인력과 정비가 필요합니다. 소수 공급사 의존 공시가 있다고 임의로 특정 OEM을 공급사로 지정하지 않습니다.',
        competition='공시가 SLB·HAL·BKR·Patterson·Liberty·RPC·ProPetro·Ranger·Nine 및 사설 전문 업체를 명시합니다. 실제 납품·협력 관계와 이 경쟁 업체 목록을 나눕니다.'),
}

OPERATIONS = {
    'SLB': [
        ('부문 중복·제품 기준', 'Digital Operations는 디지털과 핵심 부문에 함께 인식됩니다. 2025년 부문 합계의 제거 940,000,000달러를 유지하며 제품·서비스 표는 연결 매출 35,708,000,000 기준입니다.', ANNUAL['SLB']),
        ('ChampionX의 부분 기간', '2025년 7월 16일 인수 완료돼 약품·인공 채유·계측 사업이 편입됐습니다. 편입 전 ChampionX의 연간 매출을 SLB 2025년 연결 매출에 임의로 더하지 않습니다.', ANNUAL['SLB']),
        ('OneSubsea의 운영 공동사업', 'SLB 70%·Aker Solutions 20%·Subsea7 10% 공동사업이 해저 생산 시스템·디지털·서비스를 제공합니다. 실제 제품 역할과 지분 소유를 함께 확인하며 공동사업 전체 매출을 세 회사에 각각 합산하지 않습니다.', ONESUBSEA),
        ('Aramco 수주 단계', '2026년 9월 4개 계약을 수주했습니다. 3년 동안 450정 이상을 건설하는 범위·추가 최대 2년 옵션이며 미래 계획 유정 수를 현재 준공·생산 유정 수로 쓰지 않습니다.', SLB_ARAMCO),
        ('Rovuma 실제 제품', 'ExxonMobil Mozambique가 Area 4 파트너를 대표해 해저 tree·manifold·umbilical·제어와 설치 지원을 발주했습니다. LNG 액화플랜트 전체 건설비나 현행 LNG 생산량을 뜻하지 않습니다.', SLB_ROVUMA),
        ('Kelvion의 현재 단계', '2026년 8월 31일 열관리·열교환 업체 인수 계약을 발표했습니다. 현금 약 3,400,000,000달러·인수 부채 약 700,000,000, 2027년 상반기 완료 목표와 승인 조건이 있어 현재 완료 자회사로 표시하지 않습니다.', SLB_KELVION),
    ],
    'BKR': [
        ('2025년의 두 부문', 'OFSE·IET 합계 27,733,000,000달러와 제품·서비스·미국/해외 표는 동일 기간 연결 매출의 다른 구분입니다. 유전 서비스와 LNG 터빈·압축 정비는 고객의 투자·운영 수요가 다릅니다.', ANNUAL['BKR']),
        ('Chart의 완료·현재 부문', 'Chart 인수는 2026년 7월 16일 완료됐고 세 번째 보고 부문입니다. Chart 자체 2025년 매출 약 4,300,000,000달러를 Baker Hughes의 당시 연결 실적에 더하지 않습니다.', BKR_CHART),
        ('Nigeria LNG 정비 범위', 'Bonny Island 터보기계의 13년 lifecycle 서비스 계약입니다. Train 7 완료 후 설비 능력 30 Mtpa는 미래 전체 터미널 능력이며 이번 서비스 매출·현재 LNG 판매량과 다릅니다.', BKR_NLNG),
        ('Kodiak Gas 장비 주문', '2030년까지 초기 약 1 GW·전체 framework 최대 1.8 GW입니다. NovaLT16·Frame 5 터빈과 BRUSH 발전기 주문으로 현재 발전·전력 판매 실적에 합산하지 않습니다.', KGS_BKR),
        ('도구 조달의 실제 상대', 'DTI의 2025년 공시는 Baker Hughes를 임대 도구 고객으로 명시합니다. DTI의 전체 서비스사 매출 비율 48%를 Baker Hughes 한 고객의 구매 비중으로 쓰지 않습니다.', ANNUAL['DTI']),
    ],
    'HAL': [
        ('사업·지역 기준', '2025년 북미 매출 9,066,000,000달러와 중남미 3,935,000,000·유럽/아프리카/CIS 3,351,000,000·중동/아시아 5,832,000,000은 연결 매출을 지역으로 나눈 것입니다.', ANNUAL['HAL']),
        ('YPF · 전기식 파쇄', '2026년 4월 Vaca Muerta의 전담·다년 완결 계약을 수주했습니다. ZEUS 전기식 파쇄의 첫 해외 배치와 OCTIV 자동화가 범위이며 계약 총액의 기간별 인식·현재 가동 fleet는 별도로 확인합니다.', HAL_YPF),
        ('Eni · 심해 유정 건설', '2026년 9월 Cyprus Block 6 Cronos 개발의 통합 시추·완결 수주입니다. 유체·방향성 시추·LOGIX·시멘팅·시험·코일드 튜빙이 포함됩니다.', HAL_ENI),
        ('Basra · 자산 소유와 서비스', 'Bin Umar·Sindbad의 개발 계획·생산 최적화·Landmark·EPCM을 제공합니다. Basra Oil이 자산 소유·운영·의사결정 권한을 유지해 HAL을 유전 소유자로 표시하지 않습니다.', HAL_BASRA),
        ('VoltaGrid · 미래 전력 설비', '2025년 12월 400 MW 모듈형 가스 전력 시스템의 제조 용량을 확보했고 납품은 2028년입니다. 현재 400 MW 상업 가동·HAL 자체 발전 매출로 쓰지 않습니다.', HAL_VOLTA),
        ('실명 도구 공급', 'DTI 공시는 Halliburton을 시추 도구 고객으로 명시합니다. 전체 서비스사 고객군 매출 비중을 Halliburton 단일 고객의 구매 비중으로 쓰지 않습니다.', ANNUAL['DTI']),
    ],
    'PTEN': [
        ('보유·시장 제공·가동의 차이', '2025년 말 marketed 육상 리그 152개 중 Tier-1 super-spec 137개입니다. marketed는 고객에 제공 가능한 리그이며 모두 실제 작업 중이라는 뜻은 아닙니다.', ANNUAL['PTEN']),
        ('제품·완결의 편입', 'Ulterra는 2023년 8월 14일, NexTier는 9월 1일 인수·합병 완료됐습니다. 현재 각각 시추 제품과 완결 서비스를 담당하는 편입 사업입니다.', ANNUAL['PTEN']),
        ('실제 EXE 작업팀', 'EXE가 2026년 2분기 Pennsylvania의 Patterson 583 시추팀·NexTier 29 파쇄팀을 소개했습니다. 익명 최대 고객의 연간 매출을 EXE로 추정하는 근거는 아닙니다.', EXE_CREWS),
        ('지역·제품망', 'Ulterra는 북미·국제 제조·유통으로 30개국 이상 에너지·지열·광업에 제품을 공급합니다. 해외 제품 판매망과 미국·Colombia·Ecuador 시추 리그를 구분합니다.', ANNUAL['PTEN']),
    ],
    'PUMP': [
        ('매출·현장 비용', '2025년 서비스 원가의 현장 인건비 275,902,000달러·소모재 259,742,000·기타 직접 비용 432,531,000을 구별합니다. 원가와 감가·장비 투자·부문 EBITDA는 같은 수치가 아닙니다.', ANNUAL['PUMP']),
        ('XTO 전기식 계약', '2024년 4월 계약은 FORCE fleet 2개·세 번째 옵션과 wireline/pumpdown입니다. 2025년 공시의 종료 예상은 2026년 말이며 해지·release 권리와 주문·실제 가동을 구분합니다.', ANNUAL['PUMP']),
        ('Caterpillar 공급 약정', '2026년 4월 28일 PROPWR의 추가 1.5 GW 장비 framework를 체결했습니다. 종료 권리·납기 조건이 있고 기존 주문 포함 전체 portfolio 수치와 범위가 다릅니다.', QUARTER['PUMP']),
        ('Coterra 계열의 전력 고객', '2025년 12월 New Mexico Permian 현장 microgrid 계약을 체결했습니다. 당시 2026년 1분기 배치 목표였으며 현재 계약 법인의 실제 승계·가동량은 별도 확인 대상입니다. 당시 전체 portfolio 220 MW 초과 예약을 이 계약 단독 물량으로 쓰지 않습니다.', PUMP_COTERRA),
    ],
    'LBRT': [
        ('사업별 매출의 공개 범위', '2025년 공시는 단일 사업 부문으로 4,006,116,000달러를 보고합니다. 파쇄·모래·현장 가스·신규 발전의 개별 연간 금액은 공개된 부문 표가 없어 임의 구성비를 만들지 않습니다.', ANNUAL['LBRT']),
        ('현장 가동·사업 확장', '2025년 말 약 40개 active 파쇄 fleet와 2025년 3월 3일 IMG 인수 대가 약 19,600,000달러를 구별합니다. 발전 프로젝트 설계·제어·운영 역량을 취득한 것이며 모든 계획 MW가 가동한 것은 아닙니다.', ANNUAL['LBRT']),
        ('SLB의 공급·과거 지분', 'SLB 계열의 약품·프로판트·장비·부품 구매는 계속됩니다. SLB의 Liberty 주식 보유는 2023년 1월 31일 종료돼 현재 소유 관계로 표시하지 않습니다. 당시 한 달 구매 1,700,000달러를 2025년 구매액으로 쓰지 않습니다.', ANNUAL['LBRT']),
        ('Bergen·Piller 납품', 'Bergen 가스 발전기 45기·각 11.2 MWe와 Piller SHIELDX 전력 안정화 장비를 결합합니다. 총 500 MW 초과의 주문이며 납품 개시는 2027년 하반기입니다. 두 공급사는 Langley 계열로 현재 Rolls-Royce 계열이 아닙니다.', LIBERTY_BERGEN),
        ('Alpha 공동 개발 조건', 'PowerBridge와 West Texas의 계획 2 GW 데이터센터 campus를 개발합니다. 초기 300 MW 초과·첫 전력 목표 2027년 4분기이며 최종 상업 계약·승인 조건이 있어 현재 가동 규모로 쓰지 않습니다.', LIBERTY_POWERBRIDGE),
        ('SLB의 다른 협력 역할', 'SLB는 모듈형 데이터센터 인프라·프로젝트, Liberty는 발전·제어·운영을 맡는 협력을 추진합니다. SLB의 누적 모듈 인프라 공급 1.3 GW를 Liberty의 현재 발전량으로 바꾸지 않습니다.', LIBERTY_SLB),
    ],
    'SND': [
        ('광산·능력 기준', 'Oakdale의 처리능력 약 5,500,000톤/년은 공칭 능력입니다. 생산·판매량과 입도별 사양, 고객에게 도착한 물량을 별도로 확인합니다.', ANNUAL['SND']),
        ('철도별 실제 경로', 'Oakdale의 현장 CPKC·근처 Union Pacific, Ottawa/Peru의 BNSF, Blair의 Canadian National을 연결합니다. 노선 접근이 모든 운송의 독점 계약·가격·구매액을 공개한다는 뜻은 아닙니다.', ANNUAL['SND']),
        ('고객 기준 연도', '2025년 EQT 27.7%·EOG 10.9%와 2024년 EQT 31.9%·Encino 13.8%·Liberty 10.2%를 나눕니다. 고객 편입·제품 배송 경로 변화와 연도별 회사 매출 분모를 구분합니다.', ANNUAL['SND']),
    ],
    'AESI': [
        ('모래 시설·사양', '2025년 공시는 Permian의 proppant 시설 14곳과 100 mesh·40/70 mesh dry/damp sand를 설명합니다. 입도·시설 수·연간 공칭 생산능력은 서로 다른 지표입니다.', ANNUAL['AESI']),
        ('최소구매 미달 대가', '일부 계약은 기간별 최소 구매량을 충족하지 못하면 합의한 대가를 청구합니다. 2025년 23,900,000달러는 이미 매출에 포함돼 제품·서비스·발전 임대에 추가 합산하지 않습니다.', ANNUAL['AESI']),
        ('Caterpillar 장비·기간', '2026년 3월 4일 추가 1.4 GW 공급 framework를 체결했습니다. 2027–2029년 CG260-16·G3520 주문과 총 구매 약정 840,000,000달러이며 현재 운영 MW로 쓰지 않습니다.', ATLAS_CAT),
        ('장비 구매 상대·계약 만기', 'Caterpillar는 제조 용량을 확보하고 장비 구매는 승인된 판매점을 통합니다. Framework 기간은 2030년 12월 31일까지이며 예상 지출은 2029년까지·납품은 2030년까지입니다. 2026년 6월 말 약정 지출은 아직 없고 초기 약정액에는 조정 조건이 있습니다.', QUARTER['AESI']),
        ('실제 무인 운송', '2026년 6월 말 Atlas 소유 Kodiak 운전 트럭은 35대입니다. 분기 말 실제 운전 차량과 앞으로 도입할 차량·장거리 운행 목표를 구분합니다.', KODIAK_Q2),
        ('자율 운송 확장의 조건', '100대는 2027년 중반 목표입니다. Atlas fleet의 2027년 초 공도 운행은 승인·운영 조건이 있어 기존 임대 도로의 상업 운송과 구분합니다.', ATLAS_KODIAK),
        ('42마일 이후 배송', 'Dune Express의 두 출하 지점에서 자율 트럭이 고객 현장까지 배송합니다. 컨베이어 수송과 truck 운송을 같은 물량으로 중복 집계하지 않습니다.', ATLAS_KODIAK),
        ('직접 원가의 구성', '인건비·운송·전기/가스·연료·정비·광물권 로열티와 임차가 주요 항목입니다. 자율 트럭 도입이 모든 인력·원격 운영·정비 비용을 없앤다는 뜻은 아닙니다.', ANNUAL['AESI']),
    ],
    'FLOC': [
        ('유정의 생산 단계', '초기 HPGL·ESP 이후 일반 gas lift, 이후 plunger lift로 연결할 수 있습니다. 공시의 HPGL 통상 첫 1–2년은 적용 단계이며 모든 계약의 고정 기간을 뜻하지 않습니다.', ANNUAL['FLOC']),
        ('임대·판매의 연결', '2025년 연결 매출은 고객 계약 341,761,000달러와 임대 417,958,000을 포함합니다. 임대 장비의 유지·재배치·가동과 제품 판매량을 구분합니다.', ANNUAL['FLOC']),
        ('부문 간 패키지 공급', '자체 가스 시스템을 Production Solutions에 공급하고 외부 계약 시스템 업체에도 판매합니다. 부문 합계 818,505,000에서 58,786,000을 제거한 연결 매출 759,719,000을 유지합니다.', ANNUAL['FLOC']),
        ('현재 법인·비교 기간', 'Estis·Flowco Productions·Flogistix 결합은 2024년 6월 20일입니다. 그 이전 predecessor 결과는 Estis만 포함하므로 2024년 전체를 현재 결합 범위로 취급하지 않습니다.', ANNUAL['FLOC']),
        ('Valiant 현재 편입·제품', '취득일은 2026년 3월 2일이고 완료 발표는 3월 3일입니다. Valiant의 전기 수중펌프·linear ESP·유체 이동·유정 감시를 추가했습니다. 2025년 매출 표에는 편입되지 않았습니다.', QUARTER['FLOC']),
        ('Valiant 대가·공시 문단 차이', '2026년 2분기 총취득 대가는 약 316,000,000달러입니다. 취득 현금은 재무 주석·취득자산 표에서 121,300,000, 경영진 설명에서는 113,200,000으로 다르게 기재됩니다. 지급 현금도 283,100,000·283,200,000으로 달라 순인수 대가를 하나로 재계산하지 않습니다. 초기 약 200,000,000 순대가 발표와도 범위가 다릅니다.', QUARTER['FLOC']),
        ('실제 OEM·패키징', 'Estis 3306TA-JGQ/2의 공식 사양은 Caterpillar G3306TA 엔진·Ariel JGQ/2 압축기·Murphy/TECO 제어를 명시합니다. 패키지 구성은 확인되지만 이 페이지가 직접 구매 계약액·독점 공급을 공개하지는 않습니다.', FLOWCO_PACKAGE),
    ],
    'ACDC': [
        ('프로판트 능력·실제 가동', '8개 광산의 연간 공칭 능력 약 21,500,000톤에는 중단된 Merryville도 포함됩니다. 실제 생산·판매·자체 fleet 소비와 같은 수치가 아닙니다.', ANNUAL['ACDC']),
        ('연결 매출 조정', '2025년 부문 합계 2,492,100,000달러에서 내부매출 561,100,000 제거·외부 서비스 +10,800,000 조정으로 연결 1,941,800,000입니다. 순조정 550,300,000을 단순 외부 제품 항목으로 만들지 않습니다.', ANNUAL['ACDC']),
        ('Flotek 연결과 세무 범위', '2026년 2분기에도 Flotek은 보고 부문입니다. 연결 재무제표와 법인세 신고 그룹은 달라 공시의 세무 연결 제외를 재무 연결 제외로 읽지 않습니다.', QUARTER['ACDC']),
        ('Seismos 실제 공동 수행', '2026년 2월 13일–3월 4일 4개 유정·183 stages에 SAFA 유정 내 측정·제어와 ProPilot 표면 실행을 함께 적용했습니다. 회사의 효율 홍보 수치를 모든 유정에 보장된 생산 성능으로 쓰지 않습니다.', PROFRAC_SEISMOS),
        ('Range 공급 역할의 범위', 'Range가 ProFrac을 완결 업체로 명시합니다. 해당 안내에는 발표일·계약 만기가 없어 2026년 새 수주·현재 전체 계약액으로 표시하지 않습니다.', RANGE_COMPLETE),
        ('Livewire의 전력 역할', 'Livewire는 2024년 10월 운영을 시작한 자체·임대 가스 왕복 엔진/터빈 기반 현장 발전입니다. 2026년 보고의 기타 활동이며 압축·파쇄와 다른 서비스입니다.', QUARTER['ACDC']),
    ],
    'DTI': [
        ('고객군·실명 범위', '서비스 업체 48%·생산자 48%·OEM 4%는 2025년 DTI 매출 기준입니다. BKR·HAL·SLB와 Chevron·BPX·EOG·OXY·NOV의 실명이 확인되지만 개별 구매액·독점 계약은 제공하지 않습니다.', ANNUAL['DTI']),
        ('시설·서비스망', '북미 15개 지점과 유럽·중동·Asia Pacific 11개 지원 center를 운영합니다. 별도 부동산 표의 시설 수·소유/임차 기준과 운영 지점 수를 섞지 않습니다.', ANNUAL['DTI']),
        ('인수와 제품 역할', 'Deep Casing Tools·European Drilling Projects·Titan Tools는 casing·유정 폐쇄/slot recovery·시추 도구와 지역 공급망에 연결됩니다. Titan은 2025년 1월 편입돼 연간 비교 범위가 다릅니다.', ANNUAL['DTI']),
        ('우선 공급 계약의 익명', '2013년부터 한 큰 고객과 first-call 계약을 운영했고 최근 연장은 2026년까지입니다. 문단에 상대 실명이 없어 위의 특정 고객에게 계약을 귀속하지 않습니다.', ANNUAL['DTI']),
        ('원문 반올림 유지', '서반구 148,569,000·동반구 23,476,000달러와 내부거래 제거 12,420,000, 연결 159,626,000 사이의 1,000달러 반올림 차이를 숨기기 위해 숫자를 바꾸지 않습니다.', ANNUAL['DTI']),
    ],
    'KLXE': [
        ('고객 집중도·사업 분모', '2025년 고객 550곳 이상·상위 5개 매출 약 31%·개별 10% 이상 없음입니다. 전체 고객 수를 현재 수주 잔고나 고객별 제품 시장점유율로 바꾸지 않습니다.', ANNUAL['KLXE']),
        ('개별 제품과 계약 시추', '방향성·압력 제어·와이어라인·코일드 튜빙·개입 도구를 제공합니다. 생산자에게 직접 공급하는 전문 서비스와 큰 통합 서비스 업체의 패키지를 비교합니다.', ANNUAL['KLXE']),
        ('QES 편입 법인', 'Quintana Energy Services는 2020년 7월 28일 편입됐습니다. 과거 QES 상장 종목을 현재 독립 경쟁사·시세 종목으로 유지하지 않습니다.', ANNUAL['KLXE']),
        ('Wolf Pack의 인수 범위', '2026년 6월 2일 Wolf Pack Rentals의 일부 자산을 취득했습니다. 법인 전체를 자회사로 취득했다는 뜻이 아닙니다. 계약 당시 17,000,000달러와 후속 분기 취득 대가 16,900,000은 조정·지급 시점·현재가치 기준이 다릅니다.', KLX_WOLF),
        ('취득 대가·후불 지급', '2026년 2분기 공시의 당일 현금 14,100,000달러·두 차례 후불 각 1,500,000의 현재가치 2,700,000·예상 조정 100,000을 구분합니다. 후불은 종결 후 180·360일에 현금 또는 주식으로 지급할 수 있어 명목액을 취득 대가에 그대로 더하지 않습니다.', QUARTER['KLXE']),
        ('사업 조건과 비용', '현장 활동·서비스별 가동·단가, 인건비·장비 정비·운송·소모재와 고객의 예산이 연결됩니다. 원유 가격과 전문 서비스 업체의 매출은 직접 동일한 지표가 아닙니다.', ANNUAL['KLXE']),
    ],
}

for _symbol, _rows in OPERATIONS.items():
    PUBLIC[_symbol]['segments'] = [fact(*row) for row in _rows]
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    PUBLIC[_symbol]['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    PUBLIC[_symbol]['sources'] += [ANNUAL[_symbol], QUARTER[_symbol], *(row[2] for row in _rows)]
    PUBLIC[_symbol]['drivers'] = [fact('운영·판매·투자의 구분', {
        'SLB': '시추·완결·기존 유정 생산·해저 개발과 소프트웨어/장비·정비의 수요, 부문 간 중복 인식·원가·현장 실행을 나눕니다.',
        'BKR': '유전 서비스 수요·LNG/산업 장비 주문·납품과 설치기반 정비, 제조 원가·납기·장기 계약을 구분합니다.',
        'HAL': '지역·서비스별 현장 활동·가동·단가, 모래/약품/물·연료·장비 정비와 인건비를 확인합니다.',
        'PTEN': 'marketed와 active 리그, 작업일·단가·고객 예산, 파쇄 가동과 Ulterra 비트 제품 판매를 나눕니다.',
        'PUMP': '파쇄 fleet·펌핑 시간·단가·소모재와 PROPWR 주문·납품·운영 MW·장비 투자를 별도로 확인합니다.',
        'LBRT': '파쇄 fleet·완결 수요·연료/모래/약품·인력·정비와 LPI 발전의 계약·납품·가동 조건을 구분합니다.',
        'SND': '모래 입도·수요·판매량·단가, 광산 전력·가스·철도 요금·환적·운송 거리가 연결됩니다.',
        'AESI': '모래 생산·컨베이어/트럭 물류·현장 수요와 발전 장비 임대·주문·연료·정비를 다른 단위로 확인합니다.',
        'FLOC': '장비 임대 가동·요금·계약 갱신·재배치/정비와 부품 판매, 회수 가스·규제 조건을 구분합니다.',
        'ACDC': '외부 파쇄 수요·가동과 자체 모래/제조/약품의 내부거래·소모재·연료·현장 인력을 나눕니다.',
        'DTI': '도구 fleet 임대·재배치·손실/손상·수리, 신규 제품 판매·고객 활동·지역망을 확인합니다.',
        'KLXE': '시추·완결·개입·생산의 서로 다른 현장 수요·가동·단가·인건비·장비 정비·고객 신용을 확인합니다.',
    }[_symbol], ANNUAL[_symbol])]
    for _card in PUBLIC[_symbol]['brief']:
        if _symbol in {'BKR', 'FLOC'} and _card['title'] != '무엇을 하는 기업인가':
            _card['source'] = ANNUAL[_symbol]
    if _symbol == 'BKR':
        for _product in PUBLIC[_symbol]['products'][:2]:
            _product['source'] = ANNUAL[_symbol]
    if _symbol == 'FLOC':
        for _product in PUBLIC[_symbol]['products']:
            _product['source'] = ANNUAL[_symbol]

PUBLIC['AESI']['products'][-1]['source'] = ATLAS_KODIAK
PUBLIC['FLOC']['products'].append(fact('Valiant · ESP',
    '전기 수중펌프·linear ESP·지상 유체 이동과 유정 감시를 공급합니다. 2026년 편입 사업입니다.', FLOWCO_ESP))
PUBLIC['FLOC']['sources'].append(FLOWCO_ESP)

EDGES = {
    'SLB': [
        relation('Saudi Aramco', None, 'customer', '2026년 9월 통합 유정 건설 4건 · 3년·450정 이상 계획·최대 2년 연장 옵션', SLB_ARAMCO, 'saudi-aramco'),
        relation('ExxonMobil', 'XOM', 'customer', 'Mozambique 계열의 Rovuma 1단계 · tree·manifold·umbilical·제어와 설치 지원 수주', SLB_ROVUMA),
        relation('SLB OneSubsea', None, 'subsidiary', '해저 생산 시스템 운영 JV · SLB 70%·Aker 20%·Subsea7 10%, 전체 능력 중복 합산 금지', ONESUBSEA, 'slb-onesubsea'),
        relation('Aker Solutions', None, 'partner', 'OneSubsea의 해저 시스템 실제 공동사업 · 단순 금융 보유와 다른 제품·기술 역할', ONESUBSEA, 'aker-solutions'),
        relation('Subsea7', None, 'partner', 'OneSubsea의 해저 시스템·설치 분야 공동사업', ONESUBSEA, 'subsea7'),
        relation('ChampionX / SLB 편입 사업', None, 'subsidiary', '2025년 7월 16일 인수 완료 · 생산 약품·인공 채유·계측, 현재 CHX 독립 종목 아님', ANNUAL['SLB'], 'championx-slb'),
        relation('Liberty Energy', 'LBRT', 'partner', '모듈형 데이터센터 인프라·프로젝트와 Liberty 발전·제어·운영의 협력 추진 · 현재 발전량 아님', LIBERTY_SLB),
    ],
    'BKR': [
        relation('Chart Industries / Baker Hughes 편입', None, 'subsidiary', '2026년 7월 16일 완료 · 열관리·가스 처리·lifecycle의 세 번째 부문, 현재 GTLS 독립 종목 아님', BKR_CHART, 'chart-bkr'),
        relation('Nigeria LNG', None, 'customer', 'Bonny Island·Train 7 터보기계 lifecycle 서비스 · 13년, 프로젝트 전체 설비능력과 정비 매출 구분', BKR_NLNG, 'nigeria-lng'),
        relation('Kodiak Gas Services', 'KGS', 'customer', '초기 약 1 GW NovaLT16·Frame 5 터빈·BRUSH 발전기 주문 · 전체 framework 최대 1.8 GW·2030년까지', KGS_BKR),
        relation('Range Resources', 'RRC', 'customer', '방향성 시추 현장 역할 · 공식 안내 게시일·현재 계약 지속 여부 미확인', RANGE_DRILL),
    ],
    'HAL': [
        relation('YPF', 'YPF', 'customer', 'Vaca Muerta 전담 다년 완결 계약 · ZEUS 전기식 파쇄·OCTIV, 2026년 4월 수주', HAL_YPF),
        relation('Eni', 'E', 'customer', 'Cyprus Block 6 Cronos 심해 시추·유정 건설·완결 통합 수주 · 2026년 9월', HAL_ENI),
        relation('Basra Oil Company', None, 'customer', 'Bin Umar·Sindbad IFMS/EPCM · Basra가 자산 소유·운영 권한 유지, HAL은 기술·프로젝트 관리', HAL_BASRA, 'basra-oil'),
        relation('VoltaGrid', None, 'partner', '데이터센터 전력 협력 · 400 MW 제조 확보·납품 2028년, 현재 상업 가동 아님', HAL_VOLTA, 'voltagrid'),
        relation('Range Resources', 'RRC', 'customer', '시멘팅 현장 역할 · 공식 안내 게시일·현재 계약 지속 여부 미확인', RANGE_DRILL),
    ],
    'PTEN': [
        relation('Expand Energy', 'EXE', 'customer', '2026년 2분기 Patterson 583 시추·NexTier 29 frac 실제 작업팀 · 전체 계약액·독점 여부 미공개', EXE_CREWS),
        relation('NexTier / Patterson 완결 사업', None, 'subsidiary', '2023년 9월 1일 합병 완료 · 파쇄·wireline·pumpdown·현장 연료·모래 물류', ANNUAL['PTEN'], 'nextier-pten'),
        relation('Ulterra', None, 'subsidiary', '2023년 8월 14일 인수 완료 · PDC 비트 제조·수리·국제 제품망', ANNUAL['PTEN'], 'ulterra-pten'),
    ],
    'PUMP': [
        *[relation(name, symbol, 'customer', f'2025년 회사 매출 {share}% · 파쇄·완결 서비스 고객 집중도, 고객 지출·시장점유율 아님', ANNUAL['PUMP'])
          for name, symbol, share in [('ExxonMobil / XTO', 'XOM', 24.9), ('Occidental', 'OXY', 13.7),
                                     ('EOG Resources', 'EOG', 12.1), ('Permian Resources', 'PR', 11.2)]],
        relation('Caterpillar', 'CAT', 'supplier', 'PROPWR의 2026년 4월 추가 1.5 GW 발전 장비 framework · 종료·납기 조건, 현재 가동 아님', QUARTER['PUMP']),
        relation('Coterra / Devon 편입 법인', None, 'customer', '2025년 12월 New Mexico 현장 microgrid 계약 · 이후 Devon 편입, 현재 계약 승계·가동량 별도 확인', PUMP_COTERRA, 'coterra-devon'),
        relation('Silvertip / ProPetro', None, 'subsidiary', '와이어라인·pumpdown의 편입 현장 사업 · 파쇄와 다른 제품 역할', ANNUAL['PUMP'], 'silvertip-pump'),
        relation('AquaProp / ProPetro', None, 'subsidiary', '2024년 인수 · 현장 프로판트 물류·공급 지원', ANNUAL['PUMP'], 'aquaprop-pump'),
        relation('PROPWR', None, 'subsidiary', '분산 발전·microgrid 운영 사업 · 발전기 주문·계약 예약·현재 가동을 구분', QUARTER['PUMP'], 'propwr'),
    ],
    'LBRT': [
        relation('Occidental', 'OXY', 'customer', '2025년 Liberty 매출 10% 초과 · 정확한 개별 비율은 공시되지 않음', ANNUAL['LBRT']),
        relation('ExxonMobil / XTO', 'XOM', 'customer', '2025년 XTO Energy 매출 10% 초과 · Exxon 전체 구매 비중·시장점유율 아님', ANNUAL['LBRT']),
        relation('SLB', 'SLB', 'supplier', '약품·프로판트·장비·정비 부품의 지속 구매 · 2023년 1월 종료된 주식 보유와 구분', ANNUAL['LBRT']),
        relation('Bergen Engines', None, 'supplier', 'B36:45V20 AG1 가스 발전기 45기·각 11.2 MWe 주문 · 납품 2027년 하반기', LIBERTY_BERGEN, 'bergen-engines'),
        relation('Piller Power Systems', None, 'supplier', 'Bergen 발전기와 결합한 SHIELDX 전력 안정화 · Langley 계열, 2027년 납품 계획', LIBERTY_BERGEN, 'piller-power'),
        relation('PowerBridge', None, 'partner', 'Alpha West Texas 데이터센터 공동 개발 · 계획 2 GW·최초 전력 2027년 4분기 목표·최종 상업 계약/승인 조건', LIBERTY_POWERBRIDGE, 'powerbridge-infrastructure'),
        relation('Liberty Power Innovations', None, 'subsidiary', '발전·전력 제어·운영 플랫폼 · 파쇄 매출과 미래 발전 주문을 구분', ANNUAL['LBRT'], 'liberty-power-innovations'),
        relation('IMG Energy Solutions', None, 'subsidiary', '2025년 3월 3일 취득 · 발전 설계·제어·운영·전력 시장 역량', ANNUAL['LBRT'], 'img-liberty'),
        relation('PropX', None, 'subsidiary', '모래 물류·현장 공급 기술의 편입 사업', ANNUAL['LBRT'], 'propx-liberty'),
    ],
    'SND': [
        relation('EQT', 'EQT', 'customer', '2025년 Smart Sand 매출 27.7% · 파쇄용 모래 고객 집중도', ANNUAL['SND']),
        relation('EOG Resources', 'EOG', 'customer', '2025년 Smart Sand 매출 10.9% · 자체 회사 매출의 고객 비율', ANNUAL['SND']),
        relation('Liberty Energy', 'LBRT', 'customer', '2024년 매출 10.2% · 2025년 고객 비율로 표시하지 않는 과거 연도 근거', ANNUAL['SND']),
        relation('Canadian Pacific Kansas City', 'CP', 'supplier', 'Oakdale 현장 Class I 철도망으로 모래 수송 · 구매액·독점 계약은 이 공시에 없음', ANNUAL['SND']),
        relation('Union Pacific', 'UNP', 'supplier', 'Oakdale 인근 Byron 환적망의 모래 수송 경로', ANNUAL['SND']),
        relation('Canadian National', 'CNI', 'supplier', 'Blair 현장 Class I 철도망의 모래 수송 경로', ANNUAL['SND']),
        relation('BNSF Railway', None, 'supplier', 'Ottawa 광산·Peru 환적의 Class I 철도 접근 · 현재 운송 구매액은 별도', ANNUAL['SND'], 'bnsf-railway'),
    ],
    'AESI': [
        relation('Caterpillar', 'CAT', 'supplier', '추가 1.4 GW 제조 용량 framework · 실제 장비 구매는 승인 판매점, 계약 2030년 말까지·납품 예상 2030년까지', QUARTER['AESI']),
        relation('Kodiak AI', None, 'supplier', 'Atlas 소유 무인 배송 트럭의 Kodiak Driver 기술 · Nasdaq KDK, Kodiak Gas(KGS)와 다른 회사', ATLAS_KODIAK, 'kodiak-ai'),
        relation('Moser Energy Systems', None, 'subsidiary', '2025년 취득 · 가스 발전 장비 임대·현장 전력·운영/정비', ANNUAL['AESI'], 'moser-atlas'),
    ],
    'FLOC': [
        relation('Caterpillar', 'CAT', 'supplier', 'Estis 3306TA-JGQ/2 패키지의 G3306TA 엔진 제조사 · 실제 사양, 직접 구매액·독점 공급은 미확인', FLOWCO_PACKAGE),
        relation('Ariel', None, 'supplier', 'Estis 3306TA-JGQ/2 패키지의 JGQ/2 압축기 제조사 · 실제 사양, 직접 구매 계약액은 미확인', FLOWCO_PACKAGE, 'ariel-compressors'),
        relation('Estis Compression', None, 'subsidiary', 'HPGL·압축·gas lift의 실제 제조·임대·정비 사업', ANNUAL['FLOC'], 'estis-flowco'),
        relation('Flowco Production Solutions', None, 'subsidiary', 'gas lift valve·mandrel·plunger lift·계측·자동화 사업', ANNUAL['FLOC'], 'production-solutions-flowco'),
        relation('Flogistix', None, 'subsidiary', 'VRU·증기/가스 회수·압축 패키지·현장 정비 사업', ANNUAL['FLOC'], 'flogistix-flowco'),
        relation('Valiant Artificial Lift Solutions', None, 'subsidiary', '2026년 3월 2일 취득 완료·3월 3일 발표 · ESP·linear ESP·유체 이동·유정 감시', QUARTER['FLOC'], 'valiant-flowco'),
    ],
    'ACDC': [
        relation('Range Resources', 'RRC', 'customer', '공식 안내의 완결 서비스 공급 · 게시일·현재 계약 지속 여부 미확인', RANGE_COMPLETE),
        relation('Seismos', None, 'partner', 'SAFA 유정 내 측정·제어와 ProPilot 표면 실행 · 2026년 4개 유정·183 stages 실제 공동 수행', PROFRAC_SEISMOS, 'seismos'),
        relation('Flotek Industries', 'FTK', 'supplier', '파쇄 약품 공급 · 2025년 최소구매 미달 대가 27,400,000달러, 실제 약품 물량과 구분', ANNUAL['ACDC']),
        relation('Flotek Industries', 'FTK', 'subsidiary', '약품·측정의 연결 보고 부문 · 연결 재무와 법인세 신고 그룹이 다름', QUARTER['ACDC']),
        relation('Alpine Silica', None, 'subsidiary', '프로판트 광산 운영 · 8개 광산 공칭 능력에는 중단 광산 포함', ANNUAL['ACDC'], 'alpine-silica'),
        relation('Livewire Power', None, 'subsidiary', '자체·임대 가스 엔진/터빈으로 현장 전력 제공 · 기타 사업', QUARTER['ACDC'], 'livewire-profrac'),
        *[relation(name, symbol, 'competitor', '미국 stimulation/수압파쇄 · 2025년 연차보고서가 명시한 경쟁 업체, 납품·공동사업 아님', ANNUAL['ACDC'])
          for name, symbol in [('Halliburton', 'HAL'), ('Liberty Energy', 'LBRT'),
                               ('ProPetro', 'PUMP'), ('Patterson-UTI', 'PTEN')]],
    ],
    'DTI': [
        *[relation(name, symbol, 'customer', '2025년 DTI 공시의 실명 도구 고객 · 개별 구매액·독점 계약은 미공개', ANNUAL['DTI'])
          for name, symbol in [('Baker Hughes', 'BKR'), ('Halliburton', 'HAL'), ('SLB', 'SLB'),
                               ('Chevron', 'CVX'), ('EOG Resources', 'EOG'), ('Occidental', 'OXY'), ('NOV', 'NOV')]],
        relation('BPX Energy', None, 'customer', '2025년 DTI가 명시한 생산자 도구 고객 · BP 그룹 전체 구매액으로 확장하지 않음', ANNUAL['DTI'], 'bpx-energy'),
        relation('Liberty Lift Solutions', None, 'customer', '2025년 DTI가 명시한 장비 OEM 고객 · Liberty Energy(LBRT)와 다른 기업', ANNUAL['DTI'], 'liberty-lift-solutions'),
        relation('Deep Casing Tools', None, 'subsidiary', 'casing·유정 폐쇄/slot recovery의 도구·기술을 편입', ANNUAL['DTI'], 'deep-casing-dti'),
        relation('European Drilling Projects', None, 'subsidiary', '2024년 편입 · 동반구의 전문 도구·서비스망', ANNUAL['DTI'], 'edp-dti'),
        relation('Titan Tools', None, 'subsidiary', '2025년 1월 취득 · 시추 도구·임대와 지역망 편입', ANNUAL['DTI'], 'titan-dti'),
    ],
    'KLXE': [
        relation('Quintana Energy Services / KLX 편입', None, 'subsidiary', '2020년 7월 28일 합병 완료 · 현재 QES 독립 상장 종목 아님', ANNUAL['KLXE'], 'quintana-klx'),
        *[relation(name, symbol, 'competitor', '북미 시추·완결·현장 전문 서비스 · 2025년 KLX 공시가 명시한 경쟁 업체, 실제 납품·파트너 관계 아님', ANNUAL['KLXE'])
          for name, symbol in [('SLB', 'SLB'), ('Halliburton', 'HAL'), ('Baker Hughes', 'BKR'),
                               ('Patterson-UTI', 'PTEN'), ('Liberty Energy', 'LBRT'), ('RPC', 'RES'),
                               ('ProPetro', 'PUMP'), ('Ranger Energy Services', 'RNGR'), ('Nine Energy Services', 'NINE')]],
    ],
}

PRIVATE = {}
for _key, _name, _business, _origin in [
    ('saudi-aramco', 'Saudi Aramco', 'Saudi 원유·가스 생산자입니다. SLB에 2026년 9월 4개 통합 유정 건설 계약을 발주했으며 건설 계획·완료와 실제 생산을 구분합니다.', SLB_ARAMCO),
    ('slb-onesubsea', 'SLB OneSubsea', '해저 tree·manifold·umbilical·제어와 설치 지원을 제공합니다. SLB·Aker Solutions·Subsea7 공동사업이며 ExxonMobil Rovuma는 2026년 확인한 실제 수주입니다.', SLB_ROVUMA),
    ('aker-solutions', 'Aker Solutions', '해저 생산 기술·장비를 OneSubsea 공동사업에 연결합니다. OneSubsea 20% 지분은 다른 Aker 그룹 기업과 구분합니다.', ONESUBSEA),
    ('subsea7', 'Subsea7', '해저 시스템 설치·엔지니어링을 연결하는 OneSubsea 공동사업 파트너입니다. 지분 보유만이 아니라 해저 개발 공급망의 제품·설치 역할을 구분합니다.', ONESUBSEA),
    ('championx-slb', 'ChampionX / SLB 편입 사업', '생산 약품·인공 채유·고도화 장비와 측정 기술을 제공합니다. SLB가 2025년 7월 인수 완료했으며 과거 CHX를 현재 독립 상장사로 취급하지 않습니다.', ANNUAL['SLB']),
    ('chart-bkr', 'Chart Industries / Baker Hughes 편입', '공기·가스 처리·열관리·열교환과 관련 lifecycle 서비스를 제공합니다. Baker Hughes가 2026년 7월 인수 완료한 보고 부문입니다.', BKR_CHART),
    ('nigeria-lng', 'Nigeria LNG', 'Bonny Island에서 LNG를 생산하는 실제 터보기계 정비 고객입니다. Baker Hughes의 13년 서비스와 Train 7의 개발·확장 단계를 나눕니다.', BKR_NLNG),
    ('basra-oil', 'Basra Oil Company', 'Iraq Bin Umar·Sindbad 유전의 소유·운영·의사결정 권한을 유지하고 Halliburton에 개발 계획·디지털·EPCM을 발주했습니다.', HAL_BASRA),
    ('voltagrid', 'VoltaGrid', '모듈형 천연가스 전력 플랫폼을 공급하며 Halliburton의 국제 운영망과 데이터센터 전력 프로젝트를 추진합니다. 발표된 400 MW 제조 확보는 2028년 납품 범위입니다.', HAL_VOLTA),
    ('nextier-pten', 'NexTier / Patterson 완결 사업', '파쇄·wireline·pumpdown·시멘팅과 현장 가스·모래 배송을 제공합니다. Patterson에 편입된 완결 사업이며 EXE의 실제 작업팀이 확인됐습니다.', ANNUAL['PTEN']),
    ('ulterra-pten', 'Ulterra', 'PDC 시추 비트와 기타 시추 제품을 제조·수리·유통합니다. Patterson 편입 사업으로 에너지·지열·광업에 제품을 제공합니다.', ANNUAL['PTEN']),
    ('silvertip-pump', 'Silvertip / ProPetro', '유정의 wireline·pumpdown 등 완결 서비스를 제공합니다. ProPetro의 편입 사업으로 수압파쇄·시멘팅과 다른 작업 범위를 갖습니다.', ANNUAL['PUMP']),
    ('aquaprop-pump', 'AquaProp / ProPetro', '프로판트 현장 물류·공급을 지원합니다. ProPetro가 2024년 취득한 사업으로 직접 파쇄 작업과 제품 역할을 나눕니다.', ANNUAL['PUMP']),
    ('propwr', 'PROPWR', '유전·산업·데이터센터용 분산 가스 발전·microgrid의 장비·설치·운영 플랫폼입니다. Caterpillar framework·현재 예약·납품·가동을 구분합니다.', QUARTER['PUMP']),
    ('bergen-engines', 'Bergen Engines', '중속 가스 엔진·발전기를 제조합니다. Liberty의 45기 주문은 2027년 하반기부터 납품하며 2021년 말부터 Langley 계열로 과거 Rolls-Royce와 구분합니다.', LIBERTY_BERGEN),
    ('piller-power', 'Piller Power Systems', '민감한 전력 수요를 안정화하는 flywheel·SHIELDX 기술을 제공합니다. Bergen 엔진과 Liberty 전력 플랫폼에 결합되는 Langley 계열 업체입니다.', LIBERTY_BERGEN),
    ('powerbridge-infrastructure', 'PowerBridge / 데이터센터 인프라', 'West Texas 데이터센터 campus·전력 연계·fiber 등을 개발하고 Liberty와 Alpha 공동 개발을 추진합니다. Nasdaq의 유사 이름 Powerbridge Technologies와 다른 법인입니다.', LIBERTY_POWERBRIDGE),
    ('liberty-power-innovations', 'Liberty Power Innovations', '분산 발전·전력 품질·제어·운영 플랫폼입니다. LPI의 발전 사업과 Liberty 파쇄 fleet, 아직 납품 전인 Bergen 주문을 별도 범위로 구분합니다.', LIBERTY_BERGEN),
    ('img-liberty', 'IMG Energy Solutions', '분산 전력 시스템의 설계·건설 관리·소프트웨어/감시·운영·전력 시장 역량을 제공합니다. 2025년 3월 Liberty가 취득했습니다.', ANNUAL['LBRT']),
    ('propx-liberty', 'PropX', '모래의 운반·현장 저장·공급 기술을 제공합니다. Liberty 완결의 물류 사업과 별도 제품 역할을 갖는 편입 사업입니다.', ANNUAL['LBRT']),
    ('bnsf-railway', 'BNSF Railway', '북미 Class I 철도 운영사로 Smart Sand Ottawa 광산·Peru 환적의 모래 배송 경로에 연결됩니다. 노선 접근 근거에서 독점 계약·구매액을 추정하지 않습니다.', ANNUAL['SND']),
    ('kodiak-ai', 'Kodiak AI', 'Kodiak Driver 자율운행 기술을 공급하는 Nasdaq KDK 기업입니다. Atlas가 트럭을 소유·운영하고 Kodiak은 운행 기술을 제공합니다. 압축 업체 Kodiak Gas Services(KGS)와 다릅니다.', ATLAS_KODIAK),
    ('moser-atlas', 'Moser Energy Systems', '천연가스 분산 발전 장비·임대·현장 설치·정비를 제공합니다. Atlas가 2025년 취득해 발전 보고 부문으로 편입했습니다.', ANNUAL['AESI']),
    ('estis-flowco', 'Estis Compression', '고압·일반 gas lift와 압축 장비를 패키징·임대·판매·정비합니다. Flowco의 실제 운영 사업이며 공식 패키지에 Caterpillar·Ariel 부품을 명시합니다.', FLOWCO_PACKAGE),
    ('production-solutions-flowco', 'Flowco Production Solutions', 'gas lift valve·mandrel·plunger lift와 계측·원격 감시·자동화 제품을 제공합니다. 유정의 생산 단계에 따라 도구·제어를 조정합니다.', ANNUAL['FLOC']),
    ('flogistix-flowco', 'Flogistix', '메탄·탄화수소 증기를 회수·압축하는 VRU, 가스 시스템과 현장 정비를 제공합니다. Flowco의 Natural Gas Technologies 사업으로 편입돼 있습니다.', ANNUAL['FLOC']),
    ('valiant-flowco', 'Valiant Artificial Lift Solutions', '전기 수중펌프·linear ESP·지상 유체 이동과 유정 감시를 제공합니다. 취득일 2026년 3월 2일·완료 발표 3월 3일을 구분합니다.', QUARTER['FLOC']),
    ('seismos', 'Seismos', '유정 내 측정과 폐쇄루프 파쇄 의사결정·제어 기술 SAFA를 공급합니다. ProFrac ProPilot과 2026년 4개 유정·183 stages를 실제 공동 수행했습니다.', PROFRAC_SEISMOS),
    ('alpine-silica', 'Alpine Silica', 'ProFrac의 현지 프로판트 광산을 운영합니다. 8개 광산의 공칭 능력과 중단 광산·실제 생산·내부 공급·외부 판매를 구분합니다.', ANNUAL['ACDC']),
    ('livewire-profrac', 'Livewire Power', '가스 왕복 엔진·터빈의 자체/임대 자산으로 유전·비유전 현장에 전력을 제공합니다. ProFrac의 기타 사업이며 압축·파쇄 물량과 다른 기준입니다.', QUARTER['ACDC']),
    ('bpx-energy', 'BPX Energy', '원유·가스 탐사·생산 업체이며 DTI가 2025년 도구 고객으로 실명을 명시했습니다. 이 거래만으로 BP 그룹 전체 도구 구매 비중을 추정하지 않습니다.', ANNUAL['DTI']),
    ('liberty-lift-solutions', 'Liberty Lift Solutions', '인공 채유 장비 OEM으로 DTI가 도구 고객을 명시했습니다. 완결 서비스 업체 Liberty Energy(LBRT)와 다른 법인으로 분리합니다.', ANNUAL['DTI']),
    ('deep-casing-dti', 'Deep Casing Tools', 'casing·완결·유정 폐쇄와 slot recovery의 전문 도구·기술을 공급합니다. DTI가 편입해 동반구 제품·지원망을 확대했습니다.', ANNUAL['DTI']),
    ('edp-dti', 'European Drilling Projects', '시추·유정 최적화 도구와 유럽·동반구 서비스망을 제공합니다. DTI가 2024년 취득했습니다.', ANNUAL['DTI']),
    ('titan-dti', 'Titan Tools', '시추 도구·임대와 지역 지원을 제공합니다. DTI가 2025년 1월 취득해 당시 매출·감가 비교 범위가 달라졌습니다.', ANNUAL['DTI']),
    ('quintana-klx', 'Quintana Energy Services / KLX 편입', '북미 현장 서비스 사업으로 2020년 KLX에 합병 편입됐습니다. 과거 QES와 현재 KLXE의 법인·시세 범위를 구분합니다.', ANNUAL['KLXE']),
]:
    PRIVATE[_key] = profile(_name, _origin, _business,
        '확인한 제품·서비스·계약과 모회사 연결 범위를 정리합니다. 독립 회사 매출·제품별 비중을 공개된 거래 물량으로 임의 환산하지 않습니다.')

# Keep both directions navigable without treating share ownership as the only
# operational link. Graph ingestion also records source-side inverse evidence.
for _key, _value in PRIVATE.items():
    for _symbol, _rows in EDGES.items():
        for _edge in _rows:
            if _edge.get('registry_id') == _key:
                _inverse = {'supplier': 'customer', 'customer': 'supplier',
                            'subsidiary': 'parent', 'partner': 'partner'}[_edge['kind']]
                _value['relations'].append(relation(PUBLIC[_symbol]['name'], _symbol,
                    _inverse, _edge['detail'], _edge['source']))

# Manually confirmed identity bridge from the earlier Range source-local page.
PUBLIC['ACDC']['registry_id'] = 'range-profrac'
