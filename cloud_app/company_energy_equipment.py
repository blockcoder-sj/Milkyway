"""Edited equipment/drilling notes, with dated contracts and actual counterparties.

Operating assets, agreed orders, planned delivery and historical cooperation are
separate claims. No anonymous client is assigned a guessed public-company ticker.
"""
from .company_energy_sources import REPORTS, report, fact
from .company_research_notes import profile, relation, source

SYMBOLS = ('FTI', 'NOV', 'WHD', 'WTTR', 'FTK', 'NINE', 'TTI', 'NBR', 'HP', 'WFRD', 'RES', 'RNGR')
ANNUAL = {symbol: report(symbol) for symbol in SYMBOLS}
QUARTER = {symbol: report(symbol, 'quarter') for symbol in SYMBOLS}

FTI_PETRONAS = source('TechnipFMC · PETRONAS Limbayong 계약',
    'https://www.technipfmc.com/en/investors/financial-news-releases/press-release/technipfmc-awarded-iepci-contract-for-petronas-limbayong-project-offshore-malaysia/', '2026-09-15')
FTI_EQUINOR = source('TechnipFMC · Equinor 해저 개발 계약',
    'https://www.technipfmc.com/en/investors/financial-news-releases/press-release/technipfmc-awarded-subsea-contracts-by-equinor-for-multiple-projects-in-norway/', '2026-07-07')
FTI_PRYSMIAN = source('TechnipFMC · Prysmian 해상 풍력 협력',
    'https://www.technipfmc.com/en/investors/financial-news-releases/press-release/technipfmc-and-prysmian-announce-floating-offshore-wind-collaboration-agreement/', '2024-11-04')
NOV_EQUINOR = source('NOV · Equinor 3개 프로젝트 유연관 계약',
    'https://www.nov.com/news/nov-selected-to-provide-flexible-pipe-for-three-equinor-subsea-projects', '2026-07-20')
NOV_PETROBRAS = source('NOV · Petrobras CO₂ 내성 유연관 개발',
    'https://www.nov.com/news/nov-collaborates-with-petrobras-to-develop-co2-resistant-flexible-pipes-for-deepwater-applications', '2025-03-25')
NOV_ODFJELL = source('NOV · Odfjell 긴급 분리 시스템 현장 배치',
    'https://www.nov.com/news/nov-and-odfjell-successfully-deploy-rapid-emergency-disconnect-system-advancing-offshore-drilling-safety', '2026-07-22')
WTTR_PILOT = source('Select · Pilot Water 인수 계약',
    'https://investors.selectwater.com/news-events/press-releases/detail/152/select-water-solutions-announces-agreement-to-acquire-pilot-water-solutions', '2026-09-24')
WTTR_MEOR = source('Select · 미생물 회수 연구 협력',
    'https://www.selectwater.com/chemistry/completions/enhanced-oil-recovery/', '열람 2026-10-03')
FTK_PREPA = source('SEC · Flotek Puerto Rico 계약 해지 후속 공시',
    'https://www.sec.gov/Archives/edgar/data/928054/000092805426000084/ftk-20260818.htm', '2026-08-19')
FTK_PREPA_PARTY = source('SEC · Flotek Puerto Rico 과거 계약 상대·중지',
    'https://www.sec.gov/Archives/edgar/data/928054/000092805426000082/ftk-20260817.htm', '2026-08-18')
FTK_LOAN = source('Flotek · Elda River 자금 조달 계약',
    'https://ir.flotekind.com/2026-09-23-Flotek-Secures-120-Million-Senior-Secured-Term-Loan-to-Support-Continued-Strategic-Growth', '2026-09-23')
FTK_SUBS = source('SEC · Exhibit 21.1 · Flotek 자회사 명세',
    'https://www.sec.gov/Archives/edgar/data/928054/000092805426000020/ex211subsdiaries-q42025.htm', '2026-03-16')
NINE_NEWGEN = source('Nine · NewGen REGEN 재파쇄 시스템',
    'https://www.nineenergyservice.com/nine-rethink-refrac', '열람 2026-10-03')
NINE_MORPH = source('Nine · MorphPackers 북미 판매 계약',
    'https://www.nineenergyservice.com/news/nine-and-morphpackers-announce-agreement', '2017-06-19')
NINE_GEO = source('Nine · GEODynamics FracDock 계약',
    'https://www.nineenergyservice.com/news/introducing-the-fracdock', '2015-08-17')
TTI_LATEST = source('SEC · TETRA 2026 Q2 사업 진행 보고',
    'https://www.sec.gov/Archives/edgar/data/844965/000084496526000056/a20260630ttipressrelease.htm', '2026-08-03')
WFRD_NCS = source('Weatherford · NCS Multistage 인수 완료',
    'https://www.weatherford.com/investor-relations/investor-news-and-events/news/news-article/?ItemID=18786', '2026-09-01')
WFRD_DOMICILE = source('Weatherford · 법인 이전 승인·잔여 조건',
    'https://www.weatherford.com/investor-relations/investor-news-and-events/news/news-article/?ItemID=18811', '2026-09-03')
WFRD_VENTURA = source('Weatherford · Ventura Offshore MPD 계약',
    'https://www.weatherford.com/investor-relations/investor-news-and-events/news/news-article/?ItemID=18556', '2026-05-07')
WFRD_CONSTELLATION = source('Weatherford · Constellation 2개 계약',
    'https://www.weatherford.com/investor-relations/investor-news-and-events/news/news-article/?ItemID=18546', '2026-05-06')
WFRD_NOBLE = source('Weatherford · Noble 장비·유지 서비스 계약',
    'https://www.weatherford.com/investor-relations/investor-news-and-events/news/news-article/?ItemID=18536', '2026-05-05')
WFRD_ADNOC = source('Weatherford · ADNOC 3년 유정 개입 계약',
    'https://weatherford.gcs-web.com/node/17461/pdf', '2024-11-07')
RNGR_CVX = source('Ranger · Hess·Chevron ECHO 3기 계약',
    'https://investors.rangerenergy.com/news-and-events/press-releases/2026/07-14-2026-123118658', '2026-07-14')

PUBLIC = {
    'FTI': profile('TechnipFMC', ANNUAL['FTI'],
        '해저 유전·가스전의 생산 장비와 배관·제어·설치를 통합 공급하고, 지상 유정의 압력·유량 제어 장비를 제조합니다. 해저 사업(Subsea)과 Surface Technologies의 두 부문을 운영합니다. 석유·가스 생산자가 아니라 생산 설비 공급·설치 기업입니다.',
        '2025년 연결 매출은 9,932,600,000달러입니다. 해저 사업 8,665,900,000달러와 지상 장비 1,266,700,000달러로 구성됩니다. 제품·서비스별 고객 계약 매출 9,640,500,000달러는 연결 매출 전체와 다른 회계 범위입니다.',
        [('해저 생산·제어', '해저 tree·manifold·제어·연결 장치로 유정에서 나온 유체를 모으고 제어합니다. Subsea 2.0은 구성 가능한 표준 설계로 장비 제작·설치를 연결합니다.'),
         ('배관·해상 설치', '해저 생산 설비와 육상·해상 처리시설 사이의 유연관·강관 등을 설치합니다. iEPCI는 설계·조달·시공·설치를 한 계약 범위에 통합합니다.'),
         ('지상 압력·유량 제어', 'wellhead·tree, Chiksan·Weco 고압 유량 장비와 유지·검사 서비스를 제공합니다.')],
        customers='국제 에너지 기업·국영 생산자·독립 생산자가 개발 프로젝트를 발주합니다. 2025년 말 수주잔고에는 TotalEnergies·BP·Shell·Equinor·Petrobras·ExxonMobil 등의 프로젝트가 포함됩니다. 수주잔고를 당기 매출로 표시하지 않습니다.',
        inputs='금속·전용 부품·유연관과 강관, 생산·시험 설비, 해상 설치 선박·인력·물류가 필요합니다. 고객 승인, 설계·제작 진척과 해상 설치 일정이 장기 프로젝트의 납품·매출 인식에 연결됩니다.',
        competition='해저 설비·설치는 Baker Hughes·SLB OneSubsea·Saipem·Subsea7, 지상 장비는 SLB·Halliburton·Cactus·SPM 등과 경쟁합니다. 서로 다른 제품 시장의 경쟁사를 한 시장점유율 분모로 합치지 않습니다.'),
    'NOV': profile('NOV', ANNUAL['NOV'],
        '육상·해상 리그와 유전 서비스에 들어가는 장비·부품·소모품·수리·임대를 공급합니다. 해저 유연관, FPSO 처리설비, 산업용 펌프와 해상 풍력 설치선 장비도 취급합니다. 자체 원유 판매보다 고객의 설비 구매·유지 활동에 연결된 제조·서비스 기업입니다.',
        '2025년 연결 고객 계약 매출은 8,744,000,000달러입니다. 두 보고 부문은 8,911,000,000달러의 내부거래 포함 매출을 보고하고 167,000,000달러를 제거합니다. 제품 5,827,000,000달러, 서비스 1,954,000,000달러, 임대 963,000,000달러의 구성이 연결 매출과 일치합니다.',
        [('리그·유전 장비', 'top drive·관 취급·권양·시추 자동화·압력 제어와 파쇄·코일드 튜빙·와이어라인 장비를 제공합니다.'),
         ('설치 장비의 수명주기', '부품·정비·수리·검사·원격 감시·업그레이드와 장비 임대를 통해 설치된 장비를 계속 지원합니다.'),
         ('해저·해양·산업 설비', '유연관·해저 연결, FPSO 분리·처리, 물·MEG·CO₂ 설비, GustoMSC 해양·풍력 설치 장비와 산업 펌프를 공급합니다.')],
        customers='유전 서비스사·시추 계약사·원유·가스 생산자·조선소 등이 직접 영업·판매 대리망을 통해 구매합니다. 장비 수주잔고는 2025년 말 약 4,300,000,000달러였지만 취소·변경 조건이 있어 확정 당기 매출은 아닙니다.',
        inputs='강재·합금·외부 부품, 에너지, 제조 인력·시험·물류와 장기 장비의 조달이 필요합니다. 원료 가격·관세·환율과 조달 기간, 고객의 신규 장비 투자·기존 장비 정비 주기가 연결됩니다.'),
    'WHD': profile('Cactus', ANNUAL['WHD'],
        'wellhead·생산 tree·파쇄 압력 제어와 강재 보강 spoolable 관을 제조·판매·임대합니다. 압력 제어와 FlexSteel 관은 유정에서 맡는 역할이 다릅니다. 2026년에는 Baker Hughes의 Surface Pressure Control 사업을 인수한 Cactus International이 추가됐습니다.',
        '2025년 외부 고객 매출은 1,079,051,000달러이며 압력 제어 710,806,000달러와 spoolable 관 368,245,000달러입니다. 압력 제어의 내부거래 포함 매출 717,191,000달러를 외부 매출과 혼합하지 않습니다. 2026년 신규 인수 사업의 매출은 이 2025년 표에 포함하지 않습니다.',
        [('유정 압력 제어', 'wellhead·tree·frac stack·유량 제어 장비를 제조·판매하고 임대 및 현장 설치·지원 서비스를 제공합니다.'),
         ('FlexSteel 관', '강재로 보강한 spoolable 관과 연결구로 원유·가스·물의 생산·집하·반출 배관을 공급합니다. 일반 강관과 시공·운송 방식이 다릅니다.'),
         ('해외 압력 제어', '2026년 인수한 Surface Pressure Control 사업은 해외 유정 압력 제어·서비스 범위를 넓힙니다. Cactus International과 기존 FlexSteel은 별도 사업입니다.')],
        customers='유정 운영자가 필요할 때 납품 지시를 하는 call-out 주문과 합의 가격표를 사용합니다. 판매·임대·현장 서비스의 수익 인식과 고객 활동량을 구별합니다.',
        inputs='단조·기계 가공·강재와 관 보강 재료, 연결구 제조·시험, 현장 설치·운송과 서비스 거점이 필요합니다. FlexSteel은 Texas Baytown에서 관·연결구를 제조합니다.',
        competition='압력 제어는 Vault·SLB·TechnipFMC, spoolable 관은 Baker Hughes·Mattr·NOV 등과 경쟁합니다. 기존 강관은 Tenaris·Vallourec 등도 대체 공급자입니다.'),
    'WTTR': profile('Select Water Solutions', ANNUAL['WTTR'],
        '유전의 원수 확보·이송, 생산수 집하·재활용·처분과 완결용 약품을 제공하는 물 인프라·현장 서비스 기업입니다. 고정 인프라의 장기 물 처리와 이동식 현장 물류·서비스를 함께 운영합니다.',
        '2025년 외부 매출 1,407,344,000달러는 물 인프라 313,239,000달러, 물 서비스 786,525,000달러, 약품 307,580,000달러입니다. 세부 서비스 표의 내부거래·기타 조정액은 보고 부문 표의 내부거래 제거액과 다르므로 두 표를 합산하지 않습니다.',
        [('고정 물 인프라', '생산수 집하·처분정, 재활용 설비·파이프라인·저장시설을 연결합니다. 처리·허가 용량과 실제 일일 처리 물량을 구별합니다.'),
         ('현장 물·유체 서비스', '물 확보·이송·감시, 차량 운송, flowback·유정 시험, 임시 저장·고형물 처리와 숙박·임대를 제공합니다.'),
         ('약품·수질 맞춤', '마찰 저감·완결·수처리 약품을 개발·제조·공급합니다. FluidMatch는 현장 수질·완결 조건에 맞게 물과 약품을 조합하는 서비스입니다.')],
        customers='독립 E&P와 국제 에너지 기업을 서비스합니다. 고정 인프라는 acreage·wellbore dedication, 최소 물량, 우선 협의·거절권 등의 장기 약정과 유휴 능력의 추가 판매를 사용합니다. 허가능력만으로 계약 처리량이나 매출을 계산하지 않습니다.',
        inputs='물·처분 허가·부지·관로·펌프·전력·차량·인력과 약품 원료가 필요합니다. 일부 원료·장비는 한정 공급처에 의존해 대체 공급·기술을 검토합니다. 자체 약품이 물 재활용에도 쓰이는 내부 연결을 외부 기업 거래로 만들지 않습니다.'),
    'FTK': profile('Flotek Industries', ANNUAL['FTK'],
        '유정 완결·생산용 약품과 가스 품질 측정·분석, 가스 조절·발전 장비 임대를 제공합니다. Chemistry Technologies와 Data Analytics의 두 보고 부문이며 JP3 계측과 PWRtek 장비를 함께 사용합니다.',
        '2025년 매출 237,262,000달러 중 약품 209,786,000달러, 데이터·발전 27,476,000달러입니다. 공시가 부문과 특수관계자·제삼자 판매를 함께 구분하므로 4개 원문 항목으로 표시합니다. ProFrac의 Flotek 연결 부문 매출과 Flotek 단독 공시 매출은 기준이 다릅니다.',
        [('완결·생산 약품', '마찰 저감·계면활성·완결 유체 등 현장 조건에 맞춘 약품과 관련 지원을 제공합니다.'),
         ('가스 품질 측정·분석', 'JP3의 근적외선 계측으로 탄화수소 조성을 현장에서 반복 측정하고 가스 품질·운영 데이터를 제공합니다.'),
         ('가스 조절·발전 장비', '가스 품질 감지·조절과 분배 장치, 이동식 발전 자산 임대를 통해 현장·인프라 전력 공급을 지원합니다.')],
        customers='ProFrac은 장기 약품 공급과 발전 자산 임대의 핵심 거래 상대이며 동시에 지배·특수관계자 관계입니다. 외부 고객 판매를 별도로 공시합니다. 단기 매출, 최소 구매 부족분의 정산, 장비 임대의 기간을 구별합니다.',
        inputs='약품 원료·제조·실험실, 센서·계측·가스 조절 장치, 발전 설비와 현장 설치가 필요합니다. 관련 기업과의 계약·현금·장비 크레딧 정산을 일반 현금 매출로 혼합하지 않습니다.'),
    'NINE': profile('Nine Energy Service', ANNUAL['NINE'],
        '북미 육상 유정의 시멘팅·와이어라인·코일드 튜빙과 완결 도구를 공급합니다. 새 유정의 구간 분리·완결뿐 아니라 기존 유정 개입·재파쇄를 지원합니다. 2026년 구조조정을 거쳤으며 사업 서비스와 회계 기준 변화를 구분합니다.',
        '구조조정 전 기준 2025년 매출은 561,911,000달러로 서비스 431,211,000달러, 도구 판매 130,700,000달러입니다. 서비스 소계의 시멘팅·코일드 튜빙·와이어라인을 소계와 중복 합산하지 않습니다.',
        [('시멘팅', '케이싱 주변을 시멘트로 밀봉·지지하며 지층·가스·물 침입 조건에 맞는 slurry·첨가제를 설계합니다.'),
         ('와이어라인·코일드 튜빙', '유정 내 천공·계측·도구 전달과 plug 회수·분쇄·개입을 수행합니다. 와이어 케이블과 연속 강관은 서로 다른 전달 방식입니다.'),
         ('완결·재파쇄 도구', 'Stinger 용해성 plug, Scorpion 복합재 plug, Pincer 혼합형 plug와 liner·packer 등으로 구간을 분리합니다. 제품마다 후속 분쇄·회수 요구가 다릅니다.')],
        customers='육상 E&P가 완결·유정 개입 서비스를 구매합니다. 도구는 직접 판매와 독점 기술 판매 협력을 함께 사용합니다. 공시의 익명 고객을 이름이 알려진 대형 E&P로 추정해 연결하지 않습니다.',
        inputs='시멘트·첨가제·강관·원료·부품·차량·펌프와 전문 인력이 필요합니다. 전체 비용에서 단일 공급사가 10% 이상이 아니었다는 2025년 공시는 모든 제품의 공급망이 분산됐다는 뜻은 아닙니다.',
        competition='Halliburton·SLB·Patterson-UTI·KLX·Innovex와 완결 기술 업체 등이 제품·현장 서비스에서 경쟁합니다. 2025년 경쟁사로 기재된 NCS Multistage는 이후 Weatherford에 인수됐습니다.'),
    'TTI': profile('TETRA Technologies', ANNUAL['TTI'],
        '완결용 염수·약품·칼슘 클로라이드와 물·flowback 서비스를 제공합니다. 브롬 기반 유체·전해액과 Arkansas 염수 자원 개발도 추진합니다. Tetra Tech(TTEK)와 다른 기업입니다.',
        '2025년 고객 계약 매출은 630,932,000달러입니다. 완결 유체·제품 376,453,000달러와 물·flowback 서비스 254,479,000달러로 구성됩니다. 개발 중 광물 자원·생산 계획을 이미 판매한 매출로 넣지 않습니다.',
        [('완결 유체·특수 약품', 'Neptune 계열 고밀도 완결 유체, 브롬·칼슘계 제품과 산업용 약품을 공급합니다.'),
         ('물·flowback·모래 분리', '완결 후 나온 유체를 처리·시험하고 모래를 분리하며 물 관리 장비·서비스를 제공합니다.'),
         ('브롬·전해액·광물 개발', 'Arkansas 염수의 브롬 공급을 개발하고 배터리 전해액을 공급합니다. 리튬·마그네슘의 자원·계약 단계는 현재 상업 생산과 구별합니다.')],
        customers='원유·가스 생산자와 유전 서비스 업체, 칼슘 클로라이드 산업 고객·전력 저장 기업에 공급합니다. 유체 제품 판매와 임대·현장 서비스는 가격·원가 구조가 다릅니다.',
        inputs='브롬·hydrobromic acid 등과 제조·조달·물류가 필요합니다. LANXESS의 Arkansas 생산시설과 장기 브롬 공급·연장 약정을 사용하며 자체 브롬 프로젝트의 개발과 기존 조달을 병행합니다.'),
    'NBR': profile('Nabors Industries', ANNUAL['NBR'],
        '육상·해상 플랫폼 시추 리그를 운영하고, 시추 자동화·관 취급·소프트웨어·장비를 외부 고객과 자사 리그에 제공합니다. 미국·해외 시추, Drilling Solutions, Rig Technologies의 4개 부문입니다.',
        '2025년 4개 부문 매출 3,241,728,000달러에서 내부거래 57,035,000달러를 제거한 연결 영업매출은 3,184,693,000달러입니다. 자체 리그가 기술 부문 장비·서비스를 사용하는 내부 매출은 외부 고객 판매와 구분합니다.',
        [('계약 시추', '리그·인력·운영을 제공하고 작업 기간·계약 조건에 따라 매출을 인식합니다. 시장에 내놓은 리그 수와 실제 작업 중인 평균 리그 수는 다릅니다.'),
         ('시추 기술·디지털', 'RigCLOUD·자동화·managed pressure drilling·관 연결·시추 최적화 기술을 자사·타사 리그에 제공합니다.'),
         ('장비 제조·지원', 'Canrig의 top drive·catwalk·권양·관 취급·로봇 장비와 설치·지원 서비스를 제공합니다.')],
        customers='미국·해외 E&P와 시추·서비스 고객이 사용합니다. Saudi Aramco는 2025년 매출 약 30%의 고객으로 공시했지만 사우디 지역 매출을 Aramco 매출과 동일하게 표시하지 않습니다.',
        inputs='리그·강재·관·장비·부품·전력·연료·현장 인력·정비가 필요합니다. 가동률·계약 단가·이동·대기·정비와 지역별 고객의 시추 예산이 사업 조건입니다.'),
    'HP': profile('Helmerich & Payne', ANNUAL['HP'],
        '북미·해외 육상 계약 시추와 해상 플랫폼의 시추 운영 관리를 제공합니다. 2025년 KCA Deutag 인수로 해외 육상·해상 관리와 BENTEC 장비 제조가 추가됐습니다. 컴퓨터 업체 HP Inc.(HPQ)와 다른 기업입니다.',
        '회계연도 2025는 2024년 10월 1일부터 2025년 9월 30일까지이며 연결 매출은 3,746,013,000달러입니다. 북미·해외·해상 3개 보고 부문 외에 BENTEC 등 기타 사업이 있어 세 부문을 전체 100% 구성으로 계산하지 않습니다.',
        [('북미 육상 시추', 'FlexRig과 시추 기술·운영을 제공합니다. 기간 계약과 well-to-well 계약, FlexPool의 여러 리그·최소 시추일 약정 등을 구별합니다.'),
         ('해외 육상·해상 운영', '해외 육상 리그 운영과 고객이 소유한 해상 플랫폼 리그의 운영 관리를 수행합니다. 관리 계약을 자사 리그 소유 능력으로 합산하지 않습니다.'),
         ('BENTEC 제조·엔지니어링', 'KCA Deutag의 Kenera 사업을 BENTEC으로 통합한 장비·엔지니어링 사업입니다. 보고 부문상 기타 사업에 포함됩니다.')],
        customers='E&P·플랫폼 운영자가 시추·관리 서비스를 구매합니다. 2025년 말 북미 marketed·계약·활성 리그 수는 기준이 다르고 해외 KCA 사업의 계약 범위도 별도로 봅니다.',
        inputs='리그·드라이브·관 취급·제어·엔진·전력·부품과 현장 인력·정비가 필요합니다. 공시는 Desert 리그에 Caterpillar 엔진 사용을 명시합니다. 제조와 고객 소유 리그 관리의 자본 부담은 서로 다릅니다.',
        competition='미국 육상은 Nabors·Patterson-UTI·Precision Drilling, 해상 플랫폼 운영은 Nabors·Blake 등과 경쟁합니다.'),
    'WFRD': profile('Weatherford International', ANNUAL['WFRD'],
        '시추·평가, 유정 건설·완결, 생산·유정 개입 장비와 기술 서비스를 제공합니다. 압력 제어·관 연결·인공 채유·완결·디지털 기술로 유정의 건설부터 생산·폐쇄까지 지원합니다.',
        '2025년 매출은 4,918,000,000달러입니다. 3개 보고 부문 1,371,000,000달러·1,875,000,000달러·1,340,000,000달러와 기타 사업 332,000,000달러로 구성됩니다. 제품 1,938,000,000달러와 서비스 2,980,000,000달러는 같은 매출의 다른 분류입니다.',
        [('시추·평가', 'managed pressure drilling과 시추·평가 기술로 유정의 압력·지층 조건을 다룹니다.'),
         ('유정 건설·완결', '관 연결·케이싱·시멘팅 관련 기술, 완결 도구·구간 분리 등을 제공합니다.'),
         ('생산·개입', '인공 채유·유정 정비·개입·폐쇄와 생산 최적화·디지털 서비스를 제공합니다.')],
        customers='원유·가스 생산자와 해상 시추 계약사에 장비·현장 서비스·장기 유지 지원을 제공합니다. Noble·Ventura·Constellation의 계약은 장비 납품과 유지 기간, 현재 작업·미래 작업을 각각 구분합니다.',
        inputs='금속·장비·센서·제어·외부 부품과 제조·시험·물류·숙련 인력이 필요합니다. 설치 장비의 유지·부품과 현장 작업의 가동·계약 범위가 수익에 연결됩니다.',
        competition='SLB·Halliburton·Baker Hughes·Expro 등이 서비스·제품별로 경쟁합니다. NCS Multistage는 2026년 인수 완료 후 연결 사업으로 바뀌었습니다.'),
    'RES': profile('RPC', ANNUAL['RES'],
        'Cudd Energy Services·Cudd Pressure Control·Thru Tubing Solutions·Pintail Completions·Patterson Services를 통해 완결·유정 정비 기술과 장비 임대를 제공합니다. RPC(RES)와 Patterson-UTI(PTEN)는 다른 기업입니다.',
        '2025년 매출 1,626,566,000달러는 현장 기술 1,536,048,000달러와 장비 임대·지원 90,518,000달러입니다. 압력 펌핑·유정 내 도구·와이어라인 등 10개 세부 서비스는 원문의 실제 보고값으로 표시합니다.',
        [('압력 펌핑·완결', '수압파쇄·산 처리 등 압력 펌핑과 시멘팅·질소 서비스를 제공합니다.'),
         ('유정 내 도구·개입', 'Thru Tubing의 모터·fishing·plug 작업 도구와 코일드 튜빙·snubbing·와이어라인으로 완결·정비·폐쇄를 수행합니다.'),
         ('임대·지원', 'Patterson Services의 유전 도구·장비 임대 등으로 작업을 지원합니다. 2025년 4월 인수한 Pintail은 Permian 와이어라인 사업입니다.')],
        customers='미국 독립·대형 E&P와 일부 해외 고객을 대상으로 spot 작업과 전담 장비 서비스를 제공합니다. 2025년 미국 매출 1,594,244,000달러는 지리별 매출이며 미국 유전 서비스 시장점유율은 아닙니다.',
        inputs='고출력 펌프·엔진·변속기·차량·코일드 강관·소모품·시멘트·모래·약품과 숙련 인력·정비가 필요합니다. 고객의 완결 활동, 장비 가동·작업 효율과 유지·인력 비용이 연결됩니다.',
        competition='글로벌 서비스는 Halliburton·Baker Hughes·SLB, 미국 유사 서비스는 Liberty·Nine·Patterson-UTI·ProFrac·ProPetro 등과 경쟁합니다. 제품 시장마다 실제 경쟁 범위를 구별합니다.'),
    'RNGR': profile('Ranger Energy Services', ANNUAL['RNGR'],
        '미국 육상 고사양 유정 정비 리그·와이어라인과 처리·부대 서비스를 제공합니다. 생산 중인 유정의 workover·개입과 완결·폐쇄를 지원하며, 석유를 직접 생산·판매하는 E&P는 아닙니다.',
        '2025년 매출 546,900,000달러는 고사양 리그 347,000,000달러, 와이어라인 68,900,000달러, 처리·부대 서비스 131,000,000달러로 구성됩니다. 대다수 작업은 실제 제공 시간·서비스에 따른 매출이며 리그 보유 수만으로 매출을 계산하지 않습니다.',
        [('고사양 workover 리그', '완결·생산 유정의 관·장비 교체·정비·폐쇄 작업을 수행합니다. ECHO는 기존 리그의 하이브리드 전동화 사업입니다.'),
         ('와이어라인', '천공·계측·유정 개입·관 회수와 pump-down을 제공합니다.'),
         ('처리·부대 작업', '코일드 튜빙·유체 처리와 관련 임대·장비·현장 지원을 제공합니다. 부문 간 서비스 결합과 별도 작업을 구별합니다.')],
        customers='미국 E&P가 작업·시간 단위 서비스를 구매합니다. Hess·Chevron이 ECHO 3기 추가 계약 상대지만 2027년 예정 납품을 2026년 현재 가동 리그로 표시하지 않습니다.',
        inputs='리그·와이어라인 트럭·모터·유압·전동·관 취급·펌프·강관과 정비·현장 인력이 필요합니다. ECHO는 리그 임대와 비임대 서비스 요소·시간별 추가 요금이 결합된 계약입니다.'),
}

EXTRA = {
    'FTI': [('해저 계약의 확인 범위', '2026년 9월 PETRONAS Carigali의 Limbayong에 Subsea 2.0 iEPCI 계약을 수주했습니다. 공식 금액 범위는 75,000,000~250,000,000달러이며 3분기 수주 인식입니다. 프로젝트 전체 개발비나 당기 매출은 아닙니다.', FTI_PETRONAS),
            ('회사·프로젝트 구분', 'Technip Energies는 분리한 별도 기업입니다. Subsea와 Surface의 제품 역할, 프로젝트 운영자의 개발과 장비 공급자의 수주를 구분합니다.', ANNUAL['FTI'])],
    'NOV': [('유연관의 공급 역할', 'Equinor Omega Sør·Brime·Tyrihans Nord 3개 해저 프로젝트에 유연관을 공급하는 계약을 2026년 7월 발표했습니다. 생산 운영자가 아니라 해저 관 공급 역할입니다.', NOV_EQUINOR),
            ('개발·검증 단계', 'Petrobras CO₂ 내성 유연관의 사전 상업 개발·검증 계약을 대규모 상업 납품 완료로 표시하지 않습니다.', NOV_PETROBRAS),
            ('긴급 분리 기술의 현장 확인', '2026년 7월 NOV·Odfjell의 Rapid EDS 현장 배치를 발표했습니다. 해상 리그와 riser의 긴급 분리 기능이며 Odfjell 계열의 사업 역할을 유조선 운영사와 혼합하지 않습니다.', NOV_ODFJELL)],
    'WHD': [('인수의 종결·지분 범위', 'Baker Hughes Surface Pressure Control 인수는 2026년 1월 1일 종결됐습니다. Cactus International은 Cactus 65%·Baker Hughes 35%이며 단독 100% 사업이 아닙니다. 기존 FlexSteel 인수와 Saudi 합작사업은 별개입니다.', QUARTER['WHD']),
            ('생산 거점의 기준', '2026년 6월 공시는 Louisiana·Suzhou·Saudi Arabia·Abu Dhabi·Vietnam의 제조 활동을 설명합니다. 연차 공시에서 계획이던 거점을 계속 계획 상태로 남기지 않습니다.', QUARTER['WHD'])],
    'WTTR': [('Pilot Water 인수 상태', '2026년 9월 24일 현금 600,000,000달러·주식 100,000,000달러와 조건부 추가 대가의 인수 계약을 발표했습니다. 규제 승인 등 조건을 거쳐 4분기 종결 예정이므로 Pilot을 현재 자회사로 표시하지 않습니다.', WTTR_PILOT),
             ('용량·실제 물량 구분', 'Pilot의 활성 처분 허가 2,700,000배럴/일과 미개발 허가 900,000배럴/일은 실제 물 처리와 다릅니다. 2026년 상반기 처리 약 850,000배럴/일·미래 계획과 구별합니다. 합병 후 목표도 현재 Select 단독 실적은 아닙니다.', WTTR_PILOT)],
    'FTK': [('발전 자산 거래의 방향', '2025년 4월 Flotek이 ProFrac에서 운영 중 22기·건설 중 8기의 이동식 발전 자산을 매입한 뒤 ProFrac에 6년 임대했습니다. Flotek이 자산을 판 거래가 아니며 2025년 말에는 8기 건설을 마쳤습니다.', ANNUAL['FTK']),
            ('Puerto Rico 계약 해지 완료', '8월 19일 후속 8-K는 PREPA가 8월 18일 즉시 효력의 공식 계약 해지를 통지했다고 확인합니다. 이 계약의 매출·대금 수령은 없었고 장비 배치도 시작하지 않았습니다. 이전 수주 발표의 약 400,000,000달러 예상 잔고를 현재 계약·매출에 포함하지 않습니다.', FTK_PREPA),
            ('현금과 장비 크레딧', '2026년 3월 ProFrac 최소 구매 부족분 정산 19,700,000달러는 현금 7,200,000달러와 장비 건설·임대 크레딧 12,500,000달러로 구성됩니다. 정산 전체를 현금 수령으로 표시하지 않습니다.', QUARTER['FTK'])],
    'NINE': [('현재 회계·주식의 기준', '2026년 3월 5일 구조조정을 마쳤으며 3월 6일부터 후속 기업 회계를 표시합니다. 이전 주식과 후속 주식·재무제표의 단순 연결은 피하고 재무 표의 적용 범위를 확인합니다.', QUARTER['NINE']),
             ('재파쇄 기술 연결', '현재 공식 제품 페이지는 NewGen Systems와 REGEN liner·packer 시스템 협력을 명시합니다. 이전 천공 구간을 격리해 기존 유정을 다시 파쇄하는 제품 역할을 보여줍니다.', NINE_NEWGEN)],
    'TTI': [('브롬 개발의 최신 단계', '2026년 5월 28일 브롬 프로젝트 최종 투자 결정을 승인했습니다. 2026년 8월 발표의 설비 완공 계획은 2027년 말·첫 생산 2028년 초로 현재 상업 생산이 아닙니다.', TTI_LATEST),
            ('광물·합작 약정의 범위', 'ExxonMobil 계열 Saltwerx와 Evergreen 염수의 비용 분담·운영 약정이 있습니다. 리튬·마그네슘 개발 및 Magrathea의 잠재 합작 조건서를 이미 확정한 상업 JV·생산으로 표시하지 않습니다.', QUARTER['TTI'])],
    'NBR': [('Aramco 합작 운영', 'SANAD는 Saudi Aramco와 50:50 공동사업이지만 Nabors가 주요 운영 활동을 지배하는 VIE로 연결합니다. 지분율만 보고 지분법 사업으로 표시하지 않습니다.', QUARTER['NBR']),
            ('Parker·Quail의 현재 범위', 'Parker 인수는 2025년 3월 11일 종결됐고 3월 12일부터 연결했습니다. Quail Tools는 2025년 8월 Superior Energy에 매각했으므로 현재 Nabors 자회사로 표시하지 않습니다.', ANNUAL['NBR'])],
    'HP': [('KCA 인수·기타 사업', 'KCA Deutag 인수는 2025년 1월 16일 종결됐습니다. 육상은 International Solutions, 해상 관리 계약은 Offshore Solutions, BENTEC은 기타 사업에 포함합니다. 당해 전체 기간을 처음부터 소유한 실적으로 표시하지 않습니다.', ANNUAL['HP']),
           ('이전 투자와 현재 소유', 'ADNOC Drilling 주식은 회계연도 2025에 매각했습니다. 과거 1% 투자 기록을 현재 지분이나 신규 고객 계약으로 사용하지 않습니다.', ANNUAL['HP'])],
    'WFRD': [('NCS 인수 완료', 'NCS Multistage 인수는 2026년 9월 1일 완료됐고 NCS 주식은 거래를 중단했습니다. 완결·저류층 진단 기술이 추가됐지만 Weatherford의 2025년 단독 부문 매출에 NCS를 소급 합산하지 않습니다.', WFRD_NCS),
             ('법인 이전은 잔여 조건 있음', '2026년 9월 3일 주주가 Ireland에서 Delaware로의 이전을 승인했습니다. 당시 Irish High Court 승인 등 조건이 남아 4분기 효력 발생을 예상했습니다. 주주 승인을 이전 완료로 표시하지 않습니다.', WFRD_DOMICILE)],
    'RES': [('Pintail 인수·기간', 'Pintail은 Thru Tubing을 통해 2025년 4월 1일 인수했습니다. 2025년 공시 매출에는 인수 후 기간이 포함돼 전년 자체 와이어라인 성장과 분리해야 합니다. 직원 재직 조건의 지급액은 매입대가와 구분합니다.', ANNUAL['RES']),
            ('사업 자회사 구분', 'Cudd Energy는 압력 펌핑, Cudd Pressure Control은 압력하 유정 개입, Thru Tubing은 유정 내 도구, Pintail은 와이어라인, Patterson Services는 임대·지원 역할을 맡습니다.', ANNUAL['RES'])],
    'RNGR': [('American Well Services 인수', 'American Well Services 인수는 2025년 11월 7일 완료됐습니다. 2026년 상반기에는 관련 일부 활동을 고사양 리그 부문으로 재분류했습니다. 취득일과 재분류 시점을 새로운 2026년 인수로 혼합하지 않습니다.', QUARTER['RNGR']),
             ('ECHO 계약의 납품 계획', 'Hess·Chevron의 추가 ECHO 3기는 Bakken용 방한 패키지를 갖춰 2027년 납품 예정입니다. 2027년 말 전체 ECHO 20기 목표는 현재 가동 대수가 아닙니다.', RNGR_CVX)],
}

DRIVERS = {
    'FTI': [('개발·설치 일정', '프로젝트 승인·제작·시험·선박·해상 설치와 고객 수령의 진척을 구별합니다.'), ('계약·원가 기준', '수주잔고, 변경 주문·프로젝트 원가와 매출 인식 시점은 서로 다른 지표입니다.')],
    'NOV': [('신규·기존 장비 수요', '고객의 리그·생산설비 신규 투자와 설치 장비의 부품·정비·임대 활동을 나눠 봅니다.'), ('조달·제조 원가', '강재·부품·에너지·관세·환율과 장기 장비 납기·취소 조건이 관련됩니다.')],
    'WHD': [('활동량·제품 믹스', '유정 개발·완결 작업량, 압력 장비 판매·임대·서비스와 관 판매의 구성이 다릅니다.'), ('거점·인수 범위', '제조·물류·현장 지원 원가와 SPC 연결·비지배지분을 구분합니다.')],
    'WTTR': [('물량·계약·용량', '실제 처리량, dedication·최소 물량 약정, 허가·설비능력과 유휴 능력 판매를 구별합니다.'), ('물·약품·규제', '전력·차량·인력·약품 원료, 수질·재사용 요구, 처분 허가·유발 지진 관련 제한이 연결됩니다.')],
    'FTK': [('고객·계약 정산', '특수관계자 판매·최소 구매 정산·크레딧·현금과 외부 약품 판매를 구별합니다.'), ('장비 가동·투자', '발전 장비의 실제 배치·임대 기간·정비·가스 품질과 건설·조달 자금이 관련됩니다.')],
    'NINE': [('완결 활동·도구 채택', '현장 작업량·단가·서비스 효율과 용해성·복합재 도구의 판매 믹스가 관련됩니다.'), ('원료·인력·정비', '시멘트·강관·부품·인력·정비 및 공급 제한, 구조조정 전·후 재무 기준을 구분합니다.')],
    'TTI': [('원료·제품 조건', '브롬·완결 유체의 조달·제품 믹스, offshore 고압·고온 조건과 산업용 약품 수요가 관련됩니다.'), ('건설·광물 개발', '브롬 시설의 실제 공정·자금·완공과 리튬·마그네슘 계약·개발 단계를 구별합니다.')],
    'NBR': [('리그·계약', '작업 중 평균 리그·일당·대기·이동·정비와 고객의 지역별 시추 예산을 확인합니다.'), ('기술·내부거래', '외부 기술·장비 판매와 자체 리그에 제공한 내부 서비스, SANAD 연결 범위를 구별합니다.')],
    'HP': [('계약·가동·비용', '기간·well-to-well 계약, 조기 종료·최소 작업 보장과 리그 가동·대기·인력·정비를 확인합니다.'), ('사업·기간 비교', '회계연도, KCA 인수 후 연결 기간, 고객 소유 플랫폼 관리와 BENTEC 제조를 구분합니다.')],
    'WFRD': [('유정 수명주기', '신규 시추·완결과 기존 유정 생산·정비·폐쇄 수요를 구별합니다.'), ('장비·서비스 계약', 'MPD 장비 납품과 이후 유지·부품, 현장 작업·미래 납품·인수 후 사업 범위가 관련됩니다.')],
    'RES': [('현장 수요·장비 효율', '완결 작업량·spot/전담 장비 조건·펌프 가동과 정비·인력 비용을 확인합니다.'), ('서비스·인수 기준', '압력 펌핑·도구·와이어라인·임대의 다른 원가 구조와 Pintail의 인수 후 매출을 구분합니다.')],
    'RNGR': [('작업·인력·유지', '실제 청구 시간·작업 종류·단가·장비 가동과 현장 인력·정비 비용이 연결됩니다.'), ('리그 전환·계약', 'ECHO 개조·제작 자본, 실제 납품과 미래 목표·임대 계약 요소를 구별합니다.')],
}

for _symbol in SYMBOLS:
    PUBLIC[_symbol]['brief'] += [fact(title, detail, origin) for title, detail, origin in EXTRA[_symbol]]
    PUBLIC[_symbol]['drivers'] = [fact(title, detail, ANNUAL[_symbol]) for title, detail in DRIVERS[_symbol]]
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    PUBLIC[_symbol]['sources'] += [QUARTER[_symbol]]

SEGMENT_TEXT = {
    'FTI': [('해저 개발 · Subsea', '해저 생산·배관·설치·제어 및 관련 서비스입니다.'), ('Surface Technologies', '지상 유정 압력·유량 제어 장비·서비스입니다.')],
    'NOV': [('Energy Products and Services', '현장 제품·서비스·임대와 자본 장비를 보고합니다. 해당 부문 총액에는 내부 매출이 포함됩니다.'), ('Energy Equipment', '대형 장비와 부품·유지 지원을 보고합니다. 두 부문의 총액에서 내부거래를 제거합니다.')],
    'WHD': [('Pressure Control', '압력 장비의 제품·임대·현장 서비스입니다.'), ('Spoolable Technologies', 'FlexSteel 관·연결구·현장 지원입니다. 2026년 인수한 SPC와 2025년 연결 범위는 구별합니다.')],
    'WTTR': [('Water Infrastructure', '고정 집하·관로·재활용·처분·저장 시설과 장기 약정입니다.'), ('Water Services', '이동식 현장 물·유체·flowback·임대 서비스입니다.'), ('Chemical Technologies', '완결·수처리 약품의 제조·판매·현장 적용입니다.')],
    'FTK': [('Chemistry Technologies', '특수관계자·제삼자 약품 판매를 구별합니다.'), ('Data Analytics', 'JP3 계측·분석과 발전 자산 임대입니다. 약품 부문과 고객·원가 구조가 다릅니다.')],
    'NINE': [('서비스와 도구의 매출 분류', '시멘팅·와이어라인·코일드 튜빙 서비스와 도구 판매의 공시 분류입니다. 세 서비스와 서비스 소계를 동시에 합산하지 않습니다.')],
    'TTI': [('Completion Fluids & Products', '완결 유체·칼슘계·브롬계 제품과 관련 산업·전해액 사업입니다.'), ('Water & Flowback Services', '물 관리·완결 후 flowback·모래 분리·장비 서비스입니다.')],
    'NBR': [('미국 시추', '미국 리그·계약 시추 사업입니다.'), ('해외 시추', '캐나다를 포함한 해외 시추·SANAD 등이며 XBRL의 오래된 member 이름과 현재 지역 범위를 혼합하지 않습니다.'), ('Drilling Solutions', '시추 자동화·최적화·관 연결·압력 관리 등입니다.'), ('Rig Technologies', 'Canrig 장비·제조·지원 등이며 자사 리그 판매 내부거래를 제거합니다.')],
    'HP': [('North America Solutions', '북미 육상 시추·기술 사업입니다.'), ('International Solutions', 'KCA 해외 육상 사업을 포함한 계약 시추입니다.'), ('Offshore Solutions', '고객 소유 플랫폼의 시추 운영 관리를 포함합니다.'), ('기타 사업', 'BENTEC 제조·엔지니어링, 부동산·자체 보험 사업 등으로 세 부문 합계 밖에 있습니다.')],
    'WFRD': [('Drilling and Evaluation', '시추·평가 기술·서비스입니다.'), ('Well Construction and Completion', '유정 건설·완결 제품·서비스입니다.'), ('Production and Intervention', '생산·유정 개입입니다.'), ('기타 사업', '3개 보고 부문 외 매출을 별도로 포함합니다. 동일 매출을 제품·서비스 표와 합산하지 않습니다.')],
    'RES': [('Technical Services', '압력 펌핑·유정 내 도구·와이어라인·코일드 튜빙·시멘팅·질소·snubbing 등입니다.'), ('Support Services', '도구 임대·기타 지원이며 세부 서비스의 기타 항목은 기술 부문 기타와 구분합니다.')],
    'RNGR': [('High Specification Rigs', '고사양 유정 정비 리그·작업입니다.'), ('Wireline Services', '천공·계측·개입·pump-down 등입니다.'), ('Processing Solutions and Ancillary Services', '처리·코일드 튜빙·부대 임대·작업 등입니다. AWS 관련 2026년 재분류 기준을 별도로 확인합니다.')],
}
for _symbol, _items in SEGMENT_TEXT.items():
    PUBLIC[_symbol]['segments'] = [fact(title, detail, ANNUAL[_symbol]) for title, detail in _items]

EDGES = {
    'FTI': [
        relation('PETRONAS Carigali', None, 'customer', 'Limbayong iEPCI 해저 개발 계약 · 2026-09 수주, 75~250백만 달러의 공급자 발표 범위; 실제 납품·당기 매출과 구분', FTI_PETRONAS, 'petronas-carigali'),
        relation('Equinor', 'EQNR', 'customer', 'Omega Sør·Brime·Tyrihans Nord SPS·제어·강관 설치 계약 · 2026-07 수주', FTI_EQUINOR),
        relation('Prysmian', None, 'partner', '해상 풍력 계류·앵커와 해저 전력 케이블의 통합 설계·조달·설치 협력 · 2024-11 계약', FTI_PRYSMIAN, 'prysmian-energy-context'),
        relation('Saudi Aramco', None, 'customer', '2025년 말 Surface 수주잔고의 주요 발주자. 회사 전체 고객별 매출 비중은 아님.', ANNUAL['FTI'], 'saudi-aramco'),
        relation('ADNOC', None, 'customer', '2025년 말 Surface 수주잔고의 주요 발주자. 프로젝트 공급 수주를 당기 매출로 표시하지 않음.', ANNUAL['FTI'], 'adnoc-gas-context'),
        relation('Baker Hughes', 'BKR', 'competitor', '해저 생산·지상 압력 제어 제품 경쟁', ANNUAL['FTI']),
        relation('SLB OneSubsea', None, 'competitor', '해저 생산 시스템 경쟁', ANNUAL['FTI'], 'slb-onesubsea'),
        relation('Cactus', 'WHD', 'competitor', '지상 생산·압력 제어 경쟁', ANNUAL['FTI']),
    ],
    'NOV': [
        relation('Equinor', 'EQNR', 'customer', 'Omega Sør·Brime·Tyrihans Nord 프로젝트 유연관 공급 · 2026-07 발표', NOV_EQUINOR),
        relation('Petrobras', 'PBR', 'partner', 'CO₂ 내성 심해 유연관 사전 상업 개발·검증 ETEC 계약 · 2025-02 체결, 보상은 상업화 조건과 구분', NOV_PETROBRAS),
        relation('Odfjell', None, 'partner', 'Rapid EDS 긴급 분리 시스템 공동 현장 배치 · 2026-07, 해상 시추·기술 역할', NOV_ODFJELL, 'odfjell-drilling-context'),
        relation('GustoMSC', None, 'subsidiary', '해양 리그·선박·크레인·풍력 설치 장비 엔지니어링', ANNUAL['NOV'], 'gustomsc'),
    ],
    'WHD': [
        relation('Baker Hughes', 'BKR', 'partner', 'Cactus International 35% 공동사업자, SPC 인수 2026-01-01 종결. 소유 관계와 관 제품 경쟁은 별도.', QUARTER['WHD']),
        relation('FlexSteel', None, 'subsidiary', '강재 보강 spoolable 관·연결구·설치 사업 · 2023-02-28 인수 완료', ANNUAL['WHD'], 'flexsteel'),
        relation('Cactus International', None, 'subsidiary', 'Cactus 65% 지배 사업; BKR 전 Surface Pressure Control 해외 압력 제어', QUARTER['WHD'], 'cactus-international'),
        relation('SLB', 'SLB', 'competitor', '압력 제어 제품', ANNUAL['WHD']),
        relation('TechnipFMC', 'FTI', 'competitor', '압력 제어 제품', ANNUAL['WHD']),
        relation('NOV', 'NOV', 'competitor', 'spoolable 관 제품', ANNUAL['WHD']),
        relation('Tenaris', 'TS', 'competitor', '생산·집하 관의 전통 강관 대체 제품', ANNUAL['WHD']),
    ],
    'WTTR': [
        relation('Pilot Water Solutions', None, 'partner', '2026-09-24 인수 계약 상대 · 4분기 조건부 종결 예정. 현재 자회사로 표시하지 않음.', WTTR_PILOT, 'pilot-water-solutions'),
        relation('University of Texas at Austin', None, 'partner', 'MEOR 미생물 회수 기술 연구 협력 · 공식 기술 페이지의 명시 범위', WTTR_MEOR, 'ut-austin-meor'),
        relation('University of Houston', None, 'partner', 'MEOR 미생물 회수 기술 연구 협력', WTTR_MEOR, 'university-houston-meor'),
        relation('University of Calgary', None, 'partner', 'MEOR 미생물 회수 기술 연구 협력', WTTR_MEOR, 'university-calgary-meor'),
    ],
    'FTK': [
        relation('ProFrac Holding', 'ACDC', 'customer', '장기 약품 구매 및 2025년 매입 발전 자산의 6년 임차 · 특수관계자 판매', ANNUAL['FTK']),
        relation('ProFrac Holding', 'ACDC', 'supplier', 'Flotek이 2025-04 발전 자산 30기를 매입한 거래 상대. 지속적 일반 부품 공급 계약으로 확대하지 않음.', ANNUAL['FTK']),
        relation('JP3 Measurement', None, 'subsidiary', '가스·탄화수소 근적외선 계측과 현장 데이터 분석', ANNUAL['FTK'], 'jp3-measurement'),
        relation('Power Expectations', None, 'partner', '과거 Puerto Rico 전력 컨소시엄·계약 협력 상대. 이 근거는 작업 중지 시점 공시이며 이후 공식 해지 상태는 기업 기본 정리의 후속 8-K에서 확인.', FTK_PREPA_PARTY, 'power-expectations'),
        relation('Elda River Capital Management', None, 'partner', '2026-09 장비·운전자금·차환 금융 계약의 선도 대주. 원료 공급이나 운영 고객 관계가 아님.', FTK_LOAN, 'elda-river-capital'),
    ],
    'NINE': [
        relation('NewGen Systems', None, 'supplier', 'REGEN 재파쇄 liner·packer 기술·제품 협력 · 현재 공식 제품 페이지', NINE_NEWGEN, 'newgen-systems'),
        relation('NewGen Systems', None, 'partner', '재파쇄 시스템과 Nine 현장 서비스의 결합', NINE_NEWGEN, 'newgen-systems'),
        relation('MorphPackers', None, 'supplier', 'STORM·CENTURION 제품의 미국·캐나다 독점 판매 계약 · 2017-06. 당시 확인이며 현재 계약 갱신·수량은 미확인.', NINE_MORPH, 'morph-packers'),
        relation('GEODynamics', None, 'supplier', 'FracDock·GEOBall 북미 독점 공급 계약 · 2015-08. 역사적 계약으로 현재 전량 공급을 뜻하지 않음.', NINE_GEO, 'geodynamics'),
        relation('Halliburton', 'HAL', 'competitor', '완결·시멘팅·와이어라인·유정 도구', ANNUAL['NINE']),
        relation('SLB', 'SLB', 'competitor', '완결·유정 기술', ANNUAL['NINE']),
        relation('Patterson-UTI', 'PTEN', 'competitor', '미국 완결·현장 서비스', ANNUAL['NINE']),
        relation('KLX Energy Services', 'KLXE', 'competitor', '완결·유정 개입 서비스', ANNUAL['NINE']),
    ],
    'TTI': [
        relation('LANXESS', None, 'supplier', 'Arkansas bromine·hydrobromic acid 장기 공급·2027년까지 연결 약정. 제품별 조달 범위와 자체 개발을 구별.', ANNUAL['TTI'], 'lanxess-bromine'),
        relation('Saltwerx', None, 'partner', 'Evergreen 염수 test well·개발비 분담·운영 약정, ExxonMobil 간접 자회사. 확정 상업 lithium JV로 표시하지 않음.', QUARTER['TTI'], 'saltwerx'),
        relation('Magrathea', None, 'partner', '염수 magnesium 잠재 합작사업 조건서 · 최종 JV·상업 생산과 구분', ANNUAL['TTI'], 'magrathea-magnesium'),
        relation('Diversified Construction & Design', None, 'supplier', 'TETRA Bromine Project와 2026-06-12 Master Services Agreement. 브롬 설비 건설의 계약 상대이며 DEC 상장사와 다름.', QUARTER['TTI'], 'diversified-construction-design'),
        relation('Eos Energy Enterprises', 'EOSE', 'customer', '전력 저장 사업에 전해액·PureFlow 공급 관련 사업 보고. 미래 생산 확대 목표를 TETRA 현재 매출로 넣지 않음.', TTI_LATEST),
    ],
    'NBR': [
        relation('Saudi Aramco', None, 'customer', '2025년 회사 매출 약30% 고객 · 지역 Saudi 매출과 분모·범위가 다름', ANNUAL['NBR'], 'saudi-aramco'),
        relation('Saudi Aramco', None, 'partner', 'SANAD 50:50 공동사업, Nabors 지배 VIE 연결', QUARTER['NBR'], 'saudi-aramco'),
        relation('SANAD', None, 'subsidiary', 'Saudi Aramco·Nabors 공동 육상 시추 사업; 50%지만 Nabors 연결', QUARTER['NBR'], 'sanad'),
        relation('Canrig', None, 'subsidiary', 'top drive·관 취급·자동화·장비와 지원 서비스', ANNUAL['NBR'], 'canrig'),
        relation('Parker Drilling', None, 'subsidiary', '2025-03-11 인수 종결·03-12부터 연결; Quail Tools는 이후 매각', QUARTER['NBR'], 'parker-drilling'),
        relation('Helmerich & Payne', 'HP', 'competitor', '육상·플랫폼 시추 계약', ANNUAL['NBR']),
        relation('Patterson-UTI', 'PTEN', 'competitor', '미국 육상 시추 계약', ANNUAL['NBR']),
    ],
    'HP': [
        relation('Caterpillar', 'CAT', 'supplier', '공시의 Desert 리그 엔진 OEM · 모든 리그·부품의 유일 공급자를 뜻하지 않음', ANNUAL['HP']),
        relation('KCA Deutag', None, 'subsidiary', '2025-01-16 인수 종결; 해외 육상·해상 관리·제조 사업', ANNUAL['HP'], 'kca-deutag'),
        relation('BENTEC', None, 'subsidiary', 'KCA Kenera를 통합한 제조·엔지니어링 브랜드·사업, 보고상 기타', ANNUAL['HP'], 'bentec'),
        relation('Nabors Industries', 'NBR', 'competitor', '미국 육상·해상 플랫폼 시추', ANNUAL['HP']),
        relation('Patterson-UTI', 'PTEN', 'competitor', '미국 육상 시추', ANNUAL['HP']),
        relation('Precision Drilling', 'PDS', 'competitor', '미국 육상 시추', ANNUAL['HP']),
    ],
    'WFRD': [
        relation('NCS Multistage', None, 'subsidiary', '완결·저류층 진단 사업 · 2026-09-01 인수 완료, 이전 NCSM 주식 거래 종료', WFRD_NCS, 'ncs-multistage'),
        relation('Noble', 'NE', 'customer', 'Guyana MPD2기·Nigeria 기존 장비 업그레이드·전 선단 부품·서비스 약정. 발표의 미래 납품과 현재 실행을 구별.', WFRD_NOBLE),
        relation('Ventura Offshore', None, 'customer', 'SSV Victoria Brazil Búzios MPD·리그 통합·유지 계약 · 2026-05', WFRD_VENTURA, 'ventura-offshore'),
        relation('Constellation Oil Services', None, 'customer', 'Gold Star 개입: 2026-03~2028-12; Brava Star 시추·유지: 2027Q1~2030-12의 별도 미래 작업', WFRD_CONSTELLATION, 'constellation-oil-services'),
        relation('ADNOC', None, 'customer', '2024-11 발표한 3년 rigless 유정 재활성화 서비스, 당시2024Q4 시작 계획; 실제 전기간 매출·수량 미공시', WFRD_ADNOC, 'adnoc-gas-context'),
        relation('SLB', 'SLB', 'competitor', '시추·완결·생산·개입 제품·서비스', ANNUAL['WFRD']),
        relation('Halliburton', 'HAL', 'competitor', '시추·완결·생산 서비스', ANNUAL['WFRD']),
        relation('Baker Hughes', 'BKR', 'competitor', '유정 기술·서비스', ANNUAL['WFRD']),
    ],
    'RES': [
        relation('Cudd Energy Services', None, 'subsidiary', '압력 펌핑·완결 기술 서비스', ANNUAL['RES'], 'cudd-energy-services'),
        relation('Cudd Pressure Control', None, 'subsidiary', '압력하 snubbing·유정 개입 등', ANNUAL['RES'], 'cudd-pressure-control'),
        relation('Thru Tubing Solutions', None, 'subsidiary', '모터·fishing·plug 작업 등 유정 내 기술·도구', ANNUAL['RES'], 'thru-tubing-solutions'),
        relation('Pintail Completions', None, 'subsidiary', 'Permian 와이어라인 · 2025-04-01부터 연결', ANNUAL['RES'], 'pintail-completions'),
        relation('Patterson Services', None, 'subsidiary', '유전 도구·장비 임대. Patterson-UTI와 다른 기업.', ANNUAL['RES'], 'patterson-services'),
        relation('Liberty Energy', 'LBRT', 'competitor', '미국 pressure pumping·완결 서비스', ANNUAL['RES']),
        relation('ProPetro', 'PUMP', 'competitor', '미국 pressure pumping·완결 서비스', ANNUAL['RES']),
        relation('ProFrac Holding', 'ACDC', 'competitor', '미국 pressure pumping·완결 서비스', ANNUAL['RES']),
        relation('Nine Energy Service', 'NINE', 'competitor', '유정 내 도구·와이어라인·개입', ANNUAL['RES']),
    ],
    'RNGR': [
        relation('Chevron', 'CVX', 'customer', 'Hess Corporation과 ECHO3기 계약 · Bakken·2027납품예정, Hess는Chevron100%자회사', RNGR_CVX),
        relation('American Well Services', None, 'subsidiary', 'Permian 고사양 리그·지원 장비 사업 · 2025-11-07 인수', QUARTER['RNGR'], 'american-well-services'),
    ],
}

# Counterpart pages describe the evidenced role, not an unreviewed entire group.
PRIVATE = {}
for _key, _name, _business, _origin in [
    ('petronas-carigali', 'PETRONAS Carigali', '말레이시아 Limbayong 해저 개발을 발주한 PETRONAS 탐사·생산 계열입니다. TechnipFMC의 계약은 FMC Wellhead Equipment Sdn Bhd를 통한 해저 설비·설치이며 그룹 전체 발주액과 다릅니다.', FTI_PETRONAS),
    ('prysmian-energy-context', 'Prysmian', '해저 전력 케이블 제조·설치 기술을 TechnipFMC의 해상 풍력 계류·통합 설계와 연결하는 협력 상대입니다. 이 페이지는 해당 계약 역할을 다룹니다.', FTI_PRYSMIAN),
    ('odfjell-drilling-context', 'Odfjell', 'NOV Rapid EDS의 해상 시추·기술 현장 협력 상대입니다. 탱커·화학 운송 계열의 사업·매출과 섞지 않습니다.', NOV_ODFJELL),
    ('gustomsc', 'GustoMSC', 'NOV의 해양 시추·풍력 설치선 설계·jacking·크레인 장비 사업입니다.', ANNUAL['NOV']),
    ('flexsteel', 'FlexSteel', 'Cactus의 강재 보강 spoolable 관·연결구·현장 설치 사업입니다. 생산·집하·반출 배관에 사용하며 2023년 인수 완료했습니다.', ANNUAL['WHD']),
    ('cactus-international', 'Cactus International', 'Baker Hughes SPC 사업을 인수한 해외 압력 제어 사업으로 Cactus65%·Baker Hughes35% 공동 소유입니다. 2026년 1월 1일 종결한 사업이며 FlexSteel과 다릅니다.', QUARTER['WHD']),
    ('pilot-water-solutions', 'Pilot Water Solutions', '유전 생산수 처분·집하·물 인프라 기업입니다. Select가 2026년 9월 인수 계약을 맺었지만 당시 종결 조건이 남아 현재 자회사로 표시하지 않습니다.', WTTR_PILOT),
    ('ut-austin-meor', 'University of Texas at Austin', 'Select가 공식 기술 페이지에서 명시한 MEOR 미생물 회수 연구 협력 기관입니다. 기업 소유·유전 운영 관계가 아닙니다.', WTTR_MEOR),
    ('university-houston-meor', 'University of Houston', 'Select의 미생물 회수 기술 연구 협력 기관입니다.', WTTR_MEOR),
    ('university-calgary-meor', 'University of Calgary', 'Select의 미생물 회수 기술 연구 협력 기관입니다.', WTTR_MEOR),
    ('jp3-measurement', 'JP3 Measurement', 'Flotek의 현장 근적외선 탄화수소 계측·데이터 분석 사업입니다. 측정·가스 조절·발전 임대의 역할을 구분합니다.', ANNUAL['FTK']),
    ('power-expectations', 'Power Expectations', 'Puerto Rico 발전 프로젝트에서 Flotek과 협력했던 컨소시엄 상대입니다. 이 계약은 후속 8-K에서 2026년 8월 18일 공식 해지가 확인돼 현재 가동·수주로 표시하지 않습니다.', FTK_PREPA_PARTY),
    ('elda-river-capital', 'Elda River Capital Management', 'Flotek의 2026년 9월 담보 대출 선도 대주입니다. 75,000,000달러 초기 조달과 이후 조건부 인출을 구별하며 장비 제조 공급사·매출 고객은 아닙니다.', FTK_LOAN),
    ('newgen-systems', 'NewGen Systems', 'Nine의 REGEN 재파쇄 liner·packer 기술·제품 협력 상대입니다. 기존 천공 구간 격리와 재완결 역할이 공식 제품 페이지에 명시돼 있습니다.', NINE_NEWGEN),
    ('morph-packers', 'MorphPackers', 'STORM·CENTURION 확장형 steel packer의 2017년 Nine 북미 판매 계약 상대입니다. 역사적 계약의 근거이며 2026년 갱신·출하량은 미확인입니다.', NINE_MORPH),
    ('geodynamics', 'GEODynamics', '2015년 Nine에 FracDock·GEOBall 북미 독점 공급권을 부여한 완결 기술 상대입니다. 당시 계약을 현재 공급량·전량 독점으로 확대하지 않습니다.', NINE_GEO),
    ('lanxess-bromine', 'LANXESS', 'TETRA의 bromine·hydrobromic acid 조달 상대입니다. Arkansas 생산 기반의 장기 공급·연장 약정과 TETRA 자체 개발을 구별합니다.', ANNUAL['TTI']),
    ('saltwerx', 'Saltwerx', 'ExxonMobil 간접 자회사로 TETRA의 Evergreen 염수 test well·비용 분담·운영 약정 상대입니다. 리튬 생산의 최종 JV와 상업 생산 완료를 뜻하지 않습니다.', QUARTER['TTI']),
    ('magrathea-magnesium', 'Magrathea', 'TETRA 염수 magnesium 개발의 잠재 합작사업 조건서 상대입니다. 최종 계약·상업 생산과 구분합니다.', ANNUAL['TTI']),
    ('diversified-construction-design', 'Diversified Construction & Design', 'TETRA Bromine Project LLC와 2026년 6월 Master Services Agreement를 맺은 설비 건설 상대입니다. 상장 E&P Diversified Energy(DEC)와 다른 이름·법인입니다.', QUARTER['TTI']),
    ('sanad', 'SANAD', 'Saudi Aramco와 Nabors의 50:50 Saudi 육상 시추 공동사업입니다. Nabors의 운영 지배에 따라 VIE로 연결합니다.', QUARTER['NBR']),
    ('canrig', 'Canrig', 'Nabors의 top drive·관 취급·권양·자동화·로봇 장비와 지원 사업입니다.', ANNUAL['NBR']),
    ('parker-drilling', 'Parker Drilling', '2025년 3월 Nabors가 인수한 계약 시추 사업입니다. 이후 매각한 Quail Tools를 현재 Parker·Nabors 자산으로 표시하지 않습니다.', QUARTER['NBR']),
    ('kca-deutag', 'KCA Deutag', 'H&P가 2025년 1월 인수한 해외 육상 시추·고객 소유 해상 플랫폼 운영·BENTEC 제조 사업입니다.', ANNUAL['HP']),
    ('bentec', 'BENTEC', 'H&P·KCA Deutag의 장비 제조·엔지니어링 사업입니다. Kenera 및 하위 브랜드를 통합한 현재 명칭이며 보고상 기타 사업입니다.', ANNUAL['HP']),
    ('ncs-multistage', 'NCS Multistage', '완결·저류층 진단·유정 성능 제품·서비스 기업입니다. 2026년 9월 Weatherford 인수가 완료돼 이전 NCSM 주식은 거래를 중단했습니다.', WFRD_NCS),
    ('ventura-offshore', 'Ventura Offshore', 'Brazil 등에서 심해 drillship·semisubmersible 리그를 운영하는 시추 계약사입니다. SSV Victoria에 Weatherford MPD·유지 서비스를 발주했습니다.', WFRD_VENTURA),
    ('constellation-oil-services', 'Constellation Oil Services', 'Brazil 심해 시추·유정 개입 리그 운영사입니다. Gold Star 현재 개입과 Brava Star 미래 MPD 계약의 기간이 다릅니다.', WFRD_CONSTELLATION),
    ('cudd-energy-services', 'Cudd Energy Services', 'RPC의 압력 펌핑·완결 현장 기술 서비스 사업입니다.', ANNUAL['RES']),
    ('cudd-pressure-control', 'Cudd Pressure Control', 'RPC의 압력하 유정 개입·snubbing 서비스 사업입니다.', ANNUAL['RES']),
    ('thru-tubing-solutions', 'Thru Tubing Solutions', 'RPC의 유정 내 모터·fishing·plug 작업 기술·도구 사업입니다.', ANNUAL['RES']),
    ('pintail-completions', 'Pintail Completions', 'RPC가 Thru Tubing을 통해 2025년 4월 인수한 Permian 와이어라인·천공 사업입니다.', ANNUAL['RES']),
    ('patterson-services', 'Patterson Services', 'RPC의 유전 도구·장비 임대 사업입니다. 독립 상장사 Patterson-UTI와 혼합하지 않습니다.', ANNUAL['RES']),
    ('american-well-services', 'American Well Services', 'Ranger가 2025년 11월 인수한 Permian 고사양 유정 정비 리그·지원 장비 사업입니다. 인수일과 2026년 부문 재분류를 구별합니다.', QUARTER['RNGR']),
]:
    PRIVATE[_key] = profile(_name, _origin, _business,
        '상대 기업의 공식 공시·계약에서 확인한 사업 역할을 정리합니다. 그룹 전체 재무·시장점유율로 확대하지 않습니다.')

PRIVATE['saltwerx']['relations'] = [relation('ExxonMobil', 'XOM', 'parent',
    'TETRA 2026Q2 공시의 ExxonMobil 간접 전액 소유 자회사', QUARTER['TTI'])]
PRIVATE['cactus-international']['relations'] = [
    relation('Cactus', 'WHD', 'parent', '65% 지배 공동사업자', QUARTER['WHD']),
    relation('Baker Hughes', 'BKR', 'partner', '35% 공동사업자', QUARTER['WHD'])]
PRIVATE['sanad']['relations'] = [
    relation('Nabors Industries', 'NBR', 'parent', '50%·운영 지배 VIE 연결', QUARTER['NBR']),
    relation('Saudi Aramco', None, 'partner', '50% 공동사업자·시추 고객', QUARTER['NBR'], 'saudi-aramco')]
PRIVATE['power-expectations']['brief'].append(fact('관련 프로젝트의 후속 상태',
    'Flotek의 후속 8-K는 PREPA가 2026년 8월 18일 계약을 즉시 해지했고 매출·수령 대금·장비 배치가 없었다고 확인합니다.', FTK_PREPA))
# The counterpart identity belongs to the earlier contract; the termination is a
# separate, later source. Never let one receipt stand in for both claims.
PRIVATE['power-expectations']['description'] = 'Flotek 공시에서 확인한 과거 Puerto Rico 전력 컨소시엄 협력 상대입니다. 현재 상태는 아래 후속 공시에서 확인합니다.'
PRIVATE['power-expectations']['brief'][0]['detail'] = PRIVATE['power-expectations']['description']
PUBLIC['RNGR']['segments'][-1]['source'] = QUARTER['RNGR']

# Exhibit 21 has two parallel company columns and legal-form rows underneath.
# These names and jurisdictions are read from that exact table, never inferred
# from the parent address or confused with legal forms such as Texas Corporation.
for _key, _name, _place, _role in [
    ('flotek-chemistry', 'Flotek Chemistry, LLC', 'Oklahoma',
     'Flotek의 약품 사업 법인입니다. 그룹 사업 부문과 이 법인 단독 매출을 구분합니다.'),
    ('jp3-measurement', 'JP3 Measurement, LLC', 'Texas',
     'Flotek의 탄화수소 계측·데이터 분석 사업 법인입니다.'),
    ('flotek-paymaster', 'Flotek Paymaster, Inc.', 'Texas',
     'Flotek의 공시 자회사 명세에 기재된 법인입니다. 명칭만으로 외부 고객·급여 거래액을 추정하지 않습니다.'),
    ('pwrtek', 'PWRtek, LLC', 'Texas',
     'Flotek의 공시 자회사 명세에 기재된 법인입니다. 그룹 발전 사업 매출 전체를 이 법인 매출로 대입하지 않습니다.'),
]:
    if _key not in PRIVATE:
        PRIVATE[_key] = profile(_name, FTK_SUBS, _role,
            '2025년 말 자회사 명세의 법인 범위입니다. 법인별 매출·계약 금액은 이 명세에 공개되지 않습니다.')
    PRIVATE[_key]['brief'].append(fact('공시 법인명·설립 관할',
        _name + ' · 설립·등록 관할: ' + _place + ' · 2025년 말 Exhibit 21.1 기준입니다.', FTK_SUBS))
    EDGES['FTK'].append(relation(_name, None, 'subsidiary',
        '공시 자회사 명세서 · 설립·등록 관할: ' + _place + ' · 2025년 말 명세; 법인별 지분율·매출은 별도 확인.',
        FTK_SUBS, _key))

# Exhibit 21 proves the legal identity only. The annual contract index is the
# separate evidence for Chemistry's actual chemical-supply business role.
PRIVATE['flotek-chemistry']['description_source'] = ANNUAL['FTK']
PRIVATE['flotek-chemistry']['brief'][0]['source'] = ANNUAL['FTK']
PRIVATE['flotek-chemistry']['products'] = [fact('약품 공급 계약',
    '2025년 연차 공시 계약 목록은 ProFrac Services와 2022년 체결한 Chemical Products Supply Agreement 및 후속 변경 계약을 명시합니다. 법인별 전체 매출·현재 계약 금액과는 구분합니다.', ANNUAL['FTK'])]
