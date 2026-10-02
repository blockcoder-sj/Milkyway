"""Edited integrated-energy dossiers and named commercial/project relationships.

Annual figures retain their actual accounting scope. Completed transactions,
conditional agreements and future capacity are dated separately. This module
contains reading notes from free issuer/project originals, not model output.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source
from .company_energy_equipment import FTI_EQUINOR, NOV_EQUINOR, NOV_PETROBRAS

SYMBOLS = ('XOM', 'SHEL', 'BP', 'TTE', 'E', 'EQNR', 'PBR', 'EC', 'YPF')
ANNUAL = {symbol: report(symbol) for symbol in SYMBOLS}

SHELL_ARC = source('Shell · ARC Resources 인수 완료',
    'https://www.shell.com/news-and-insights/newsroom/news-and-media-releases/2026/shell-completes-acquisition-of-arc-resources.html', '2026-09-02')
LNG_CANADA = source('Shell · LNG Canada 2단계 투자 결정·공동사업 구조',
    'https://www.shell.com/news-and-insights/newsroom/news-and-media-releases/2026/shell-takes-final-investment-decision-to-double-lng-canada-capacity.html', '2026-09-29')
LNG_CANADA_EPC = source('LNG Canada · JGC·Fluor 설계·조달·시공',
    'https://www.lngcanada.ca/what-we-do/jgc-fluor-joint-venture-jfjv/', '열람 2026-10-03')
ADURA = source('Shell · Equinor와 Adura 설립 완료',
    'https://www.shell.com/news-and-insights/newsroom/news-and-media-releases/2025/shell-and-equinor-complete-formation-of-adura.html', '2025-12-01')
SHELL_FTI = source('TechnipFMC · Shell Gato do Mato 해저 설비 계약',
    'https://www.technipfmc.com/en/investors/financial-news-releases/press-release/technipfmc-awarded-major-iepci-contract-for-shell-s-gato-do-mato-development-offshore-brazil/', '2025-03-25')
SHELL_MODEC = source('MODEC · Shell 브라질 FPSO 공급·운영 계약',
    'https://www.modec.com/news/2025/20250325_pr_gdm_psa.html', '2025-03-25')
BP_TIBER = source('TechnipFMC · BP Tiber 20K 해저 설비 계약',
    'https://www.technipfmc.com/media/tmwfxtdo/tfmc-tiber-award-press-release.pdf', '2026-01-05')
BP_CASTROL = source('Stonepeak · Castrol 지배 지분 인수 계약',
    'https://stonepeak.com/news/stonepeak-to-acquire-majority-controlling-interest-in-castrol-from-bp', '2025-12-24')
TTE_FTI = source('TechnipFMC · GranMorgu 해저 설비 계약',
    'https://www.technipfmc.com/en/investors/financial-news-releases/press-release/technipfmc-awarded-major-iepci-contract-for-totalenergies-granmorgu-development-offshore-suriname/', '2024-11-14')
TTE_GRANMORGU = source('TotalEnergies · GranMorgu 사업·공동사업자',
    'https://totalenergies.com/company/projects/oil/granmorgu-suriname-oil-project-line-totalenergies-transition-strategy', '열람 2026-10-03')
TTE_EDF = source('TotalEnergies·EDF · 프랑스 공장 장기 전력 공급 계약',
    'https://totalenergies.com/newsroom/totalenergies-and-edf-sign-a-longterm-partnership-to-secure-lowcarbon-electricity-supply-for-totalenergies-refining-chemicals-sites-in-france/?lang=eng', '2026-03-27')
ENI_PLENITUDE = source('Eni · Plenitude 자본·공동 지배 구조 변경 완료',
    'https://www.eni.com/it-IT/media/comunicati-stampa/2026/10/eni-completato-il-riassetto-azionario-e-di-governance-di-plenitude.html', '2026-10-01')
ENI_SEARAH = source('Eni · PETRONAS와 Searah 설립',
    'https://www.eni.com/en-IT/media/press-release/2026/06/pr-eni-petronas-establish-searah.html', '2026-06-08')
ARGENTINA_LNG = source('Eni · YPF·XRG Argentina LNG 공동 개발 계약',
    'https://www.eni.com/it-IT/media/comunicati-stampa/2026/02/cs-eni-ypf-xrg-firmano-agreement-avanzamento-progetto-argentina-lng.html', '2026-02-12')
EQNR_Q2 = source('Equinor · 2026년 2분기 사업 실적',
    'https://www.equinor.com/news/equinor-second-quarter-2026-results', '2026-07-22')
XOM_MODEC = source('MODEC · ExxonMobil Hammerhead FPSO 계약',
    'https://www.modec.com/news/2025/20250930_pr_Hammerhead-FID.html', '2025-09-30')
XOM_CCS_NUCOR = source('ExxonMobil · Nucor CCS 상업 운영 개시',
    'https://corporate.exxonmobil.com/what-we-do/delivering-industrial-solutions/carbon-capture-and-storage/lower-carbon-steel-and-permanent-storage-ccs-expands-across-the-gulf-coast', '2026-09-16')
XOM_CCS_NG3 = source('ExxonMobil · NG3 CCS 상업 운영 개시',
    'https://corporate.exxonmobil.com/what-we-do/delivering-industrial-solutions/carbon-capture-and-storage/expanding-our-ccs-operations-in-louisiana-with-another-project-startup', '2026-02-18')
XOM_CLIMATE = source('ExxonMobil · 2026 기후 보고·Baytown 중지 상태',
    'https://corporate.exxonmobil.com/publications/sustainability/executive-summary', '열람 2026-10-03')
GOLDEN_PASS = source('Golden Pass · 첫 LNG 생산',
    'https://www.goldenpasslng.com/newsroom/golden-pass-lng-marks-historic-milestone-with-first-lng-production', '2026-03-30')
PBR_FTI = source('TechnipFMC · Petrobras 해저 생산 설비 계약',
    'https://www.technipfmc.com/en/investors/financial-news-releases/press-release/technipfmc-awarded-significant-subsea-production-systems-contract-by-petrobras/', '2025-09-23')
EC_Q2 = source('Ecopetrol · 2026 Q2 사업·재무 원문',
    'https://files.ecopetrol.com.co/web/esp/inversionista/reporte-2q-2026.pdf', '2026-06-30')
YPF_STOCK = source('YPF · 보통주 분할·ADR 비율 안내',
    'https://inversores.ypf.com/', '열람 2026-10-03')

PUBLIC = {
    'XOM': profile('ExxonMobil', ANNUAL['XOM'],
        '원유·천연가스를 개발·생산하고 정유·화학·특수제품을 제조·판매하는 통합 에너지 기업입니다. Permian 셰일, Guyana 해상 생산, LNG와 글로벌 정유·화학 설비를 연결합니다. 탄소 포집·운송·저장 사업은 산업 고객의 별도 서비스입니다.',
        '2025년 총수익 332,238,000,000달러는 판매·기타 영업수익 323,905,000,000달러, 지분법 관계기업 이익 5,064,000,000달러, 기타 수익 3,269,000,000달러로 구성됩니다. 사업별 판매액과 총수익을 구분하고 본사 판매 85,000,000달러도 남겨둡니다.',
        [('상류 · 생산 자산', '미국 Permian·Pioneer 자산, Guyana, 캐나다 오일샌드 등에서 원유·천연가스·NGL을 생산합니다. 프로젝트 전체 생산량과 ExxonMobil 귀속 생산량은 다릅니다.'),
         ('Energy Products · 연료', '휘발유·경유·항공유 등 연료의 정제·구매·물류·판매를 연결합니다. 원유 생산 사업과 달리 원유가 정제 공장의 투입 원료이기도 합니다.'),
         ('Chemical Products · 석유화학', '올레핀·폴리올레핀·방향족 등 화학 원료와 제품을 제조합니다. 정유·화학 통합 공장, 에탄·나프타 등 원료와 전력·열을 사용합니다.'),
         ('Specialty Products · 특수제품', '윤활유·기유·첨가용 제품과 특수 수지 등을 공급합니다. 연료 판매와 구분되는 제품·고객·규격 사업입니다.'),
         ('산업 CO₂ 처리', '산업 시설에서 포집한 CO₂를 운송·저장합니다. 저장 계약의 연간 상한 물량은 실제 처리량이나 당기 매출이 아닙니다.')],
        customers='원유·가스·LNG 구매자, 브랜드 연료 유통망, 항공·산업 연료 고객, 화학·윤활유 고객에게 판매합니다. CCS 고객은 비료·철강·가스 처리 등 산업 시설로, 석유제품 고객과 구분합니다.',
        inputs='시추·완결·해상 생산 설비와 현장 서비스, 원유·가스·NGL, 정유·화학 촉매·전력·정비·물류를 사용합니다. 자체 생산 원료와 외부 매입·재판매 원료가 함께 있어 판매액을 자체 생산량과 바로 대응시키면 안 됩니다.'),
    'SHEL': profile('Shell', ANNUAL['SHEL'],
        '원유·가스 생산, LNG·가스 거래, 정유·화학, 연료·윤활유 판매, 전력·가스 공급을 운영합니다. 생산한 가스를 액화·운송·판매하고 외부 물량도 조달하는 통합 LNG 사업이 사업 구조의 핵심입니다.',
        '2025년 외부 고객 매출은 266,886,000,000달러입니다. Integrated Gas 38,457,000,000달러, Upstream 5,105,000,000달러, Marketing 111,855,000,000달러, Chemicals and Products 77,071,000,000달러, Renewables and Energy Solutions 34,359,000,000달러, 본사 39,000,000달러입니다. 부문 간 원료·제품 거래는 이 외부 매출에 더하지 않습니다.',
        [('통합 가스 · LNG·GTL', '가스전·액화 공장·LNG선·트레이딩·고객 판매를 연결합니다. GTL은 천연가스를 액체 연료·기유로 전환하는 사업입니다.'),
         ('상류 · 탐사·생산', '해상·육상 유전과 가스전을 개발·운영합니다. LNG 사업용 생산·거래는 Integrated Gas에 포함되는 부분이 있어 부문 매출을 총 생산량으로 해석하지 않습니다.'),
         ('연료·윤활유 판매', 'Shell 브랜드 주유·편의 서비스, 산업·항공·해운 연료와 윤활유를 공급합니다. 브랜드 점포·유통망과 직접 소유 점포는 다릅니다.'),
         ('정유·화학·거래', '원유를 연료로 정제하고 화학 원료·제품을 제조·판매합니다. 제품 거래 물량과 자사 공장 생산 물량을 구분합니다.'),
         ('전력·에너지 솔루션', '전력 발전·공급·거래, 파이프라인 가스, 재생에너지와 관련 에너지 서비스를 운영합니다.')],
        customers='LNG 수입자·발전·도시가스 고객, 연료 도매·소매 유통망, 산업·운송 고객이 주요 판매 경로입니다. LNG Canada의 공동사업자는 각자 가스를 제공하고 지분에 해당하는 LNG를 인수하는 구조이며 모두 Shell의 고객사는 아닙니다.',
        inputs='상류의 시추·해저 설비, 액화·압축 설비, 가스 파이프라인과 LNG선, 정유·화학 원료·촉매·전력 및 공장 유지보수가 연결됩니다. LNG는 공급 가스·액화·출하·판매 계약의 각 단계를 구별해야 합니다.'),
    'BP': profile('BP', ANNUAL['BP'],
        '원유·가스 생산과 LNG·가스·전력, 정유·연료·윤활유 판매를 운영하는 통합 에너지 기업입니다. Gas & Low Carbon Energy, Oil Production & Operations, Customers & Products의 세 사업과 본사·기타를 보고합니다.',
        '2025년 총수익·기타소득은 192,549,000,000달러입니다. 판매·기타 영업수익은 189,335,000,000달러이며, 고객 계약 매출 158,879,000,000달러는 별도 범위입니다. 부문·지역 표는 영업수익, 제품 표는 고객 계약 매출 기준으로 각각 표시합니다.',
        [('가스·저탄소 에너지', '가스 생산·LNG·가스와 전력 거래, 저탄소 에너지 관련 사업을 운영합니다. 외부 조달·재판매도 포함됩니다.'),
         ('원유 생산·운영', '유전 개발·생산 및 관련 운영 사업입니다. 정유 공장에 넘기는 내부 원유 거래와 외부 판매를 구분합니다.'),
         ('고객·제품', '정유·연료 유통·편의 서비스·Castrol 윤활유 등입니다. 소비자가 브랜드 주유소를 이용하는 관계와 기업 간 도매·장기 계약은 별개입니다.'),
         ('거래·판매 계약', '물량·지역·기간·가격 약정과 파생상품이 연결되는 에너지 거래 사업입니다. 매출 기준과 계약상 위험의 범위를 함께 봅니다.')],
        customers='주유·편의 유통망, 산업·항공·해운 연료 고객, 윤활유 고객과 LNG·가스·전력 구매자가 주요 경로입니다. 조달한 제품·가스의 재판매가 포함되어 제품 매출을 자체 생산량과 동일시하지 않습니다.',
        inputs='원유·가스·정유 원료, 시추·해상 설비·현장 서비스, LNG 운송·재기화 용량과 정유·윤활유 공장·첨가제·전력·정비를 사용합니다.'),
    'TTE': profile('TotalEnergies', ANNUAL['TTE'],
        '원유·가스 생산, LNG, 발전·전력 공급, 정유·화학, 연료 판매를 함께 운영합니다. Integrated LNG와 Integrated Power를 별도 보고해 가스 액화·판매와 발전·전력 사업을 구분할 수 있습니다.',
        '2025년 고객 계약 매출은 201,196,000,000달러입니다. 탐사·생산 5,590,000,000달러, 통합 LNG 10,096,000,000달러, 통합 전력 19,587,000,000달러, 정유·화학 87,207,000,000달러, 판매·서비스 78,708,000,000달러, 본사 8,000,000달러입니다. 내부거래 제거 전 부문 판매액은 구성비에 사용하지 않습니다.',
        [('탐사·생산', '원유·가스전 개발·생산과 지분 생산물을 판매합니다. 외부 매출만으로 전체 생산 규모를 설명할 수 없으며 내부 가스 공급도 있습니다.'),
         ('통합 LNG', '가스 생산·액화 지분·장기 조달·운송·재기화·판매·거래를 연결합니다.'),
         ('통합 전력', '가스·재생에너지 발전, 전력·가스 판매·거래와 관련 유연성 자산을 운영합니다.'),
         ('정유·화학', '원유를 정제하고 석유화학 원료·폴리머 등을 제조합니다. 프랑스 공장의 장기 전력 조달은 별도 공급 계약입니다.'),
         ('판매·서비스', '주유소·유통망, 항공·해운·산업 연료, 윤활유·특수 유체 등을 공급합니다.')],
        customers='원유·LNG 수요자, 전력·가스 고객, 연료 유통·산업·운송 고객에게 판매합니다. 주요 공동사업자는 자원·설비의 공동 개발 역할이며 고객 분류와 구분합니다.',
        inputs='시추·해저 생산 장비·FPSO·건설, 원유·가스·LNG·화학 원료, 발전 설비·전력과 물류·정비가 필요합니다. 개발 사업은 투자 결정·공사·가동·판매 단계마다 투입 업체가 달라집니다.'),
    'E': profile('Eni', ANNUAL['E'],
        '원유·가스 탐사·생산, 도매 가스·LNG·전력, 정유·화학, Enilive의 재생연료·연료 판매와 Plenitude의 전력·가스·충전을 운영합니다. 위성 사업에 외부 투자자를 받아 각 사업의 지배·연결 범위가 변할 수 있습니다.',
        '2025년 고객 계약 매출은 82,151,000,000유로입니다. 탐사·생산 37,109,000,000유로, 가스·LNG·전력 13,102,000,000유로, 정유·화학 5,223,000,000유로, Enilive 16,337,000,000유로, Plenitude 10,118,000,000유로, 본사 262,000,000유로입니다. 2025년 연결 범위이며 2026년 10월 Plenitude 구조 변경 전 수치입니다.',
        [('탐사·생산', '아프리카·유럽·중동·아시아 등의 유전·가스전을 개발하고 원유·가스를 생산합니다. Azule 등 공동사업은 연결 자회사와 회계 범위가 다릅니다.'),
         ('도매 가스·LNG·전력', '여러 생산국의 가스 조달·파이프라인·LNG·도매 판매·거래와 발전을 운영합니다.'),
         ('정유·화학', '정유 공장과 Versalis의 화학·폴리머 사업입니다. 원유·가스·나프타·전력·증기가 주요 원료·투입입니다.'),
         ('Enilive · 재생연료', '바이오정유·지속가능항공유·연료 유통과 모빌리티 서비스를 제공합니다. 재생연료는 원료 조달·전처리·공정·제품 인증을 연결합니다.'),
         ('Plenitude · 발전·소매·충전', '재생에너지 발전, 전력·가스 소매와 전기차 충전을 운영합니다. 최신 지배 구조와 과거 연결 매출을 분리해 표시합니다.')],
        customers='원유·가스·LNG 도매 구매자, 발전·에너지 소매 고객, 연료·윤활유 유통·산업 고객이 주요 경로입니다. 장기 가스 계약이 남아 있어도 해당 연도에 실제 공급이 있었는지 따로 확인합니다.',
        inputs='유전 개발·FPSO·시추·건설, 파이프라인·LNG 조달, 정유·바이오정유 원료·촉매·수소·전력, 화학 원료와 공장 정비가 필요합니다.'),
    'EQNR': profile('Equinor', ANNUAL['EQNR'],
        '노르웨이 대륙붕과 해외의 원유·가스 생산, 에너지 판매·중류 처리, 발전·재생에너지를 운영합니다. 노르웨이 국가 지분 자원과 자체 자원을 함께 판매하는 역할도 있어 판매량과 지분 생산량은 다릅니다.',
        '2025년 연결 매출은 106,462,000,000달러입니다. 여섯 부문 매출 합계 148,883,000,000달러에서 내부 거래 42,421,000,000달러를 제거합니다. 생산 부문과 MMP의 판매가 겹치는 제거 전 매출에 연결 구성비를 붙이지 않습니다. 제품별 고객 계약 매출은 105,242,000,000달러의 별도 범위입니다.',
        [('노르웨이 생산', '노르웨이 해상 유전·가스전과 관련 설비를 운영합니다. 파트너 지분·국가 지분과 Equinor 귀속 지분을 구분합니다.'),
         ('해외·미국 생산', '해외 해상·육상 및 미국 사업을 별도 보고합니다. UK Adura는 Shell과 설립한 공동사업입니다.'),
         ('MMP · 판매·물류·처리', '원유·가스·NGL·정유제품의 판매·운송·저장·처리와 거래를 운영합니다. 생산 사업에서 이전받은 내부 물량이 포함됩니다.'),
         ('발전·재생에너지', '해상 풍력·육상 재생에너지와 발전·유연성·전력 거래가 연결됩니다. 2026년부터 Power(PWR)로 재편한 보고 범위는 2025년 REN과 다릅니다.')],
        customers='정유사·가스 도매·발전·에너지 구매자에게 원유·가스·제품·전력을 판매합니다. 노르웨이 국가 자원 판매 계약과 일반 외부 고객 판매를 구분합니다.',
        inputs='해상 시추·해저 장비·유연관·플랫폼 정비, 가스 처리·운송·저장, 발전·풍력 설비와 전력 거래가 연결됩니다. 해상 장비 발주에서 계약·납품·가동은 서로 다른 시점입니다.'),
    'PBR': profile('Petrobras', ANNUAL['PBR'],
        '브라질 해상 원유·가스 생산과 정유·운송·판매, 가스·저탄소 에너지를 운영합니다. 심해 pre-salt 생산을 FPSO·해저 설비·가스 수송·육상 처리·정유·유통으로 연결하는 구조입니다.',
        '2025년 매출은 미국 달러 표시 공시 기준 89,195,000,000달러입니다. 탐사·생산·정유·가스·본사의 제거 전 합계 152,735,000,000달러에서 내부 거래 63,540,000,000달러를 제거합니다. 브라질 판매 62,938,000,000달러와 해외 판매 26,257,000,000달러는 중복 없는 지역 구분입니다.',
        [('해상 생산·FPSO', '해저 유정에서 나온 원유·가스를 부유식 생산·저장·하역 설비에서 처리하고 원유를 출하합니다. 설비 이름·처리 능력·지분 생산량은 각각 다른 정보입니다.'),
         ('정유·운송·판매', '원유를 경유·휘발유·항공유·LPG 등으로 정제하고 국내 유통·수출을 운영합니다. 브라질 석유제품 매출 소계 52,813,000,000달러의 하위 제품을 다시 합계에 더하지 않습니다.'),
         ('가스·저탄소 에너지', '자체 가스·볼리비아 조달·LNG 등 공급, 가스 처리·운송·판매와 발전·관련 에너지 사업입니다.'),
         ('Santos 가스 수송', 'Route 1·2·3가 해상 가스를 육상 처리시설로 운송합니다. Route 3는 Petrobras 소유이며 처리시설의 두 모듈은 2024년 11월·2025년 5월 상업 가동했습니다.')],
        customers='국내 연료 유통사·산업·항공·가스 고객과 해외 원유·제품 구매자에게 판매합니다. 공시에 나온 고객 수를 임의의 기업 명단으로 바꾸지 않습니다.',
        inputs='해저 장비·FPSO·시추·해상 서비스, 원유·가스·수소·촉매·전력, 가스 파이프라인 용량과 정유·물류 설비를 사용합니다. 국영 가스 공급자와 운송 계약사는 각각 실제 공급·운송 역할입니다.'),
    'EC': profile('Ecopetrol', ANNUAL['EC'],
        '콜롬비아를 중심으로 원유·가스 생산, 정유·석유화학, 수송·물류를 운영하며 ISA를 통해 송전·유료 도로 사업도 보유합니다. 석유·가스 생산에만 한정되지 않는 그룹입니다.',
        '2025년 매출은 119,694,000,000,000콜롬비아 페소입니다. 외부 매출 기준 생산 44,828,000,000,000페소, 정유·석유화학 56,195,000,000,000페소, 운송·물류 2,642,000,000,000페소, 송전·도로 16,029,000,000,000페소입니다. 공시의 billion COP를 실제 페소 단위로 환산하며 USD 수치와 섞지 않습니다.',
        [('탐사·생산', '콜롬비아 원유·가스와 미국 Permian 등 해외 생산 사업입니다. 공동 개발의 운영자·지분·연결 범위를 구분합니다.'),
         ('정유·석유화학', 'Barrancabermeja와 Cartagena의 정유·관련 제품 사업입니다. 정유 처리량은 생산 부문의 원유 생산량과 다른 지표입니다.'),
         ('수송·물류', 'Cenit·관련 파이프라인과 터미널을 통한 원유·제품 수송입니다. 그룹 내부 수송과 외부 수수료 매출을 구분합니다.'),
         ('ISA · 송전·도로', '전력 송전 자산과 유료 도로 운영·투자가 포함됩니다. 송전 수익을 발전 전력 판매 매출로 해석하지 않습니다.')],
        customers='국내 연료·가스 유통·산업 고객과 해외 원유·제품 구매자에게 판매합니다. 콜롬비아 연료 가격안정기금(FEPC) 채권은 지급·수금 구조에 연결되는 항목입니다.',
        inputs='생산·시추·해상 개발 장비, 정유 원료·촉매·수소·전력, 파이프라인·물류·공장 정비와 송전·도로 건설·유지보수가 필요합니다.'),
    'YPF': profile('YPF', ANNUAL['YPF'],
        '아르헨티나 Vaca Muerta 등에서 원유·가스를 생산하고 파이프라인·정유·연료 유통·윤활유와 LNG·신에너지 사업을 운영합니다. 생산 증설과 내륙 물류·수출 경로를 함께 연결하는 기업입니다.',
        '2025년 USD 표시 매출은 18,448,000,000달러입니다. 다섯 부문의 제거 전 매출 27,567,000,000달러에서 내부 거래 9,119,000,000달러를 제거합니다. 국가별 매출 15,662,000,000달러·1,628,000,000달러·307,000,000달러·851,000,000달러는 공시의 고객 소재지별 구분입니다.',
        [('상류 · 셰일·기존 유전', 'Vaca Muerta의 수평 시추·파쇄와 기존 원유·가스 자산을 운영합니다. 공동사업의 블록·운영자·지분이 각각 다릅니다.'),
         ('물류·정유·판매', '원유·제품 수송과 La Plata·Luján de Cuyo·Plaza Huincul 정유, 주유·산업·항공·해운 연료 판매를 연결합니다.'),
         ('LNG·통합 가스', '가스 공급·운송·LNG 개발 사업입니다. 공동 개발 계약·설계·최종 투자 결정·실제 액화 가동을 구분합니다.'),
         ('신에너지·윤활유', '전력·관련 신에너지와 제품 서비스를 운영하고 YPF·ELAION 등 윤활유 제품 및 기유 판매를 취급합니다.'),
         ('Vaca Muerta 수송', 'VMOC 파이프라인은 2025년 2분기 가동했고 설계 용량은 일일 377,000배럴입니다. Oldelval 경로와 VMOS 수출 경로 연결을 구분하며 실제 수송량으로 표시하지 않습니다.')],
        customers='주유소·유통망, 산업·항공·해운 고객과 원유·가스·제품 수출 구매자에게 판매합니다. Chevron 기유의 아르헨티나 독점 유통은 상류 공동 개발과 다른 거래 역할입니다.',
        inputs='셰일 시추·파쇄·모래·물·현장 서비스, 원유·가스·정유 촉매·수소·전력, 파이프라인·저장·출하·정비가 연결됩니다.'),
}

LATEST = {
    'XOM': [('상업 CCS · 실제 고객', '2026년 2월 NG3 가스 처리시설의 CO₂ 운송·저장이 시작됐고 9월 Nucor 제철 원료 시설 CCS가 시작됐습니다. 이 계약의 한도 능력과 실제 연간 처리량은 구분합니다.', XOM_CCS_NUCOR),
            ('Baytown · 투자 진행 상태', '2026년 기후 보고는 저탄소 수소 사업 중지를 명시합니다. 과거 발표한 산소·질소·수소 운송 협력을 현재 가동 중인 공급 관계로 표시하지 않습니다.', XOM_CLIMATE)],
    'SHEL': [('ARC · 인수 완료', '2026년 9월 2일 ARC Resources 인수가 완료됐습니다. 캐나다 Montney 원유·가스 생산 자산이 추가됐으며 Antero Resources(AR)와 다른 법인입니다.', SHELL_ARC),
             ('LNG Canada · 현재와 확장', '가동 중인 1단계 용량은 연간 14,000,000톤입니다. 9월 29일 2단계 투자를 결정했고 향후 총 28,000,000톤·2030년대 초 상업 운전을 계획합니다. 확장 능력은 현재 생산량이 아닙니다.', LNG_CANADA)],
    'BP': [('Castrol · 계약·잔여 조건', 'Castrol 지분 65%를 Stonepeak에 매각하고 BP가 35%를 남기는 계약이 2025년 12월 발표됐습니다. 2026년 6월 말 보고에서도 연말 완료 목표·잔여 조건이 있는 거래로 다룹니다.', report('BP','interim')),
           ('Azule · Angola 공동사업', 'BP·Eni 각 50%의 Azule은 Angola 생산·개발 공동사업입니다. 2026년 6월 Greater PAJ 투자를 결정했으며 미래 프로젝트 생산능력은 현재 생산량과 분리합니다.', report('BP','interim'))],
    'TTE': [('GranMorgu · 개발 단계', 'Suriname 해상 Block 58 개발은 TotalEnergies 운영·40%, APA 40%, Staatsolie 20%입니다. 2028년 첫 원유 생산 목표와 설계 능력은 계획이며 현재 가동 실적으로 표시하지 않습니다.', TTE_GRANMORGU),
            ('프랑스 공장 · 전력 조달', 'EDF와 12년 공급 계약을 체결했습니다. 2028년 1월 1일부터 프랑스 정유·화학 공장 전력 수요 약 60%에 해당하는 평균 약 400MW를 공급하는 범위이며 글로벌 그룹 전체 전력은 아닙니다.', TTE_EDF)],
    'E': [('Plenitude · 2026년 10월 구조 변경', '10월 1일 자본·지배 구조 변경을 완료했습니다. 지분은 Eni 65.03%, Ares 26.24%, EIP 8.73%이며 Eni·Ares 공동 지배로 연결 대상에서 제외됩니다. 지분 50% 초과를 단독 연결 지배로 해석하지 않습니다.', ENI_PLENITUDE),
          ('Searah · 아시아 가스 공동사업', '2026년 6월 Eni와 PETRONAS가 각 50%의 Searah를 설립했습니다. 인도네시아·말레이시아 가스 사업을 통합한 공동사업으로 그룹 전체 합병은 아닙니다.', ENI_SEARAH)],
    'EQNR': [('2026년 보고 부문 변경', '2026년 1월 1일부터 Power(PWR)는 이전 Renewables, MMP의 유연성 발전 자산과 Danske Commodities의 전력 거래를 묶습니다. 2025년 매출 표는 변경 전 부문 그대로 유지합니다.', ANNUAL['EQNR']),
             ('2026년 2분기 · 가동 자산', '2분기 지분 생산은 일일 2,165,000boe이며 Eirin·Symra의 새 생산과 Bacalhau·Adura가 포함됩니다. 분기 발전량은 1.19TWh입니다. 유전 프로젝트의 총 생산능력과 지분 생산을 구분합니다.', EQNR_Q2)],
    'PBR': [('가스 조달·운송 계약', '볼리비아 YPFB에서 가스를 조달하며 GTB·TBG·TAG·NTS와 수송 계약을 맺습니다. 과거 운송사 지분 소유 여부와 현재 유료 운송 서비스 관계는 다른 항목입니다.', ANNUAL['PBR']),
            ('Sirius · 조건부 가스 판매', 'Ecopetrol과 개발하는 Colombia Sirius의 판매 계약은 향후 개발·가동 조건이 있습니다. 2025년 공시에 나온 계약을 현재 가스 생산·매출로 표시하지 않습니다.', ANNUAL['EC'])],
    'EC': [('Sirius · 계약 단계', '2025년 12월 Petrobras와 가스 판매 절차를 완료했습니다. 17개 상대방·66개 조건부 계약, 일일 최대 249,000,000입방피트의 계약 범위이며 가동 목표는 2030년입니다. 이름이 공개되지 않은 구매자를 추정해 채우지 않습니다.', ANNUAL['EC']),
           ('2026년 2분기 · 사업 규모', '분기 지분 생산은 일일 705,800boe, 정유 처리량은 일일 438,500배럴, 수송량은 일일 1,125,000배럴입니다. 각기 다른 사업의 운영량이며 더해서 그룹 생산량으로 계산하지 않습니다.', EC_Q2)],
    'YPF': [('Argentina LNG · 개발 계약', '2026년 2월 YPF·Eni·XRG가 구속력 있는 공동 개발 계약을 맺었습니다. 설계와 최종 투자 결정 준비 단계이며 계획 LNG 능력을 현재 생산·매출로 표시하지 않습니다.', ARGENTINA_LNG),
            ('보통주·ADR · 종목 구분', '2026년 8월 4일 현지 보통주를 1주당 10주로 분할하고 ADR당 보통주 비율을 1:10으로 변경했습니다. NYSE ADR 자체를 1:10 분할한 것으로 처리하지 않습니다.', YPF_STOCK)],
}
for _symbol, _items in LATEST.items():
    PUBLIC[_symbol]['brief'].extend(fact(*item) for item in _items)

DRIVERS = {
    'XOM': [('생산·정제·화학의 연결', '원유·가스 판매가격·물량, 원유와 정유제품 가격차, 화학 원료·제품 가격차와 설비 가동·정비가 서로 다른 부문에 반영됩니다.'),
            ('개발·운영 비용', '시추·해상 생산·물류·현장 서비스·인력·정비·해체 비용과 프로젝트 가동 일정이 공시 사업 조건입니다.')],
    'SHEL': [('LNG·거래·물류', '가스 공급·액화 가동, LNG 계약의 가격 기준·납기, 운송·재기화·트레이딩의 물량과 약정이 연결됩니다.'),
             ('정유·화학·판매', '원료·제품 가격차, 공장 가동·정비, 연료·윤활유 판매 경로·물량과 운영 비용을 구분합니다.')],
    'BP': [('가격·설비·판매 경로', '원유·가스 생산가격·물량, 정유 공장의 원료·제품 가격차·가동률, 연료·편의·윤활유 물량과 비용이 사업별로 다르게 연결됩니다.'),
           ('계약·조달·회계 범위', '에너지 조달·트레이딩 계약, 내부 거래 제거, 고객 계약 매출과 기타 소득의 분류를 구분해야 사업 구성 표를 읽을 수 있습니다.')],
    'TTE': [('생산·LNG·전력', '자원 생산량·가격, 액화·운송·판매 약정, 발전 가동·전력 조달·판매 계약과 전력 거래가 각각의 사업에 연결됩니다.'),
            ('공장·개발', '정유·화학 원료와 제품 가격차·정비, 해상 개발·건설·납품·첫 생산 일정과 자본 투입이 공시 조건입니다.')],
    'E': [('가스 공급·원료', '가스 공급국·수송 경로·장기 조달·가격 약정, 정유·화학 원료·에너지와 재생연료 원료·전처리·제품 인증이 연결됩니다.'),
          ('공동사업·연결 범위', 'Azule 등 지분법 사업과 연결 사업을 구분합니다. 외부 투자 이후 지배·연결 방식이 바뀌면 과거·현재 부문 수치를 그대로 비교할 수 없습니다.')],
    'EQNR': [('국가 지분·생산·판매', '노르웨이 국가 자원 판매와 Equinor 지분 생산, 내부 물량 이전과 외부 매출을 구분합니다. 가스 시장·운송·처리·저장·판매 약정이 연결됩니다.'),
             ('해상 운영·전력', '해상 설비 가동·정비·시추·해저 장비·운송과 풍력·발전 가동·전력 거래의 조건은 서로 다릅니다.')],
    'PBR': [('원유·정유·국내 유통', '해상 생산·FPSO 가동, 원유·제품 가격·국내 판매 정책·물량, 정유 원료·제품 가격차와 공장 정비가 연결됩니다.'),
            ('가스·환율·계약', '국내 가스·볼리비아 가스·LNG의 조달·운송·판매 약정과 BRL·USD 표시 기준을 구분합니다.')],
    'EC': [('국내 가격·수금 구조', '원유·연료 가격과 판매 물량, FEPC 채권의 발생·수금, COP 환율·재무 표시 단위가 공시 사업·현금흐름에 연결됩니다.'),
           ('사업별 운영', '생산·정유·수송의 가동·정비와 송전·도로의 투자·운영·규제 계약은 각각 다른 사업 조건입니다.')],
    'YPF': [('셰일 개발·출하 경로', '시추·완결·물·모래·현장 서비스, 유정 생산과 파이프라인·저장·수출 능력·가동 시점이 연결됩니다.'),
            ('국내 판매·환율', '아르헨티나 국내 연료 판매·규제·가격·환율과 공시 USD 표시 기준, 원유·가스 수출·LNG 개발 계약을 구분합니다.')],
}
for _symbol, _items in DRIVERS.items():
    PUBLIC[_symbol]['drivers'] = [fact(title, detail, ANNUAL[_symbol]) for title, detail in _items]

EDGES = {
    'XOM': [
        relation('MODEC', None, 'supplier', 'Hammerhead FPSO의 설계·조달·건설·설치 계약과 첫 원유 생산부터 10년 운영·유지 서비스. 최초 생산은 승인 조건에 따라 빠르면 2029년 계획.', XOM_MODEC, 'modec'),
        relation('Nucor', 'NUE', 'customer', 'Louisiana Convent의 직접환원철 시설에서 포집한 CO₂ 운송·저장. 2026-09 상업 운영 개시, 연간 최대 800,000톤은 계약 능력.', XOM_CCS_NUCOR),
        relation('CF Industries', 'CF', 'customer', 'Donaldsonville 비료 시설의 포집 CO₂ 운송·저장. 2025-07 상업 운영 개시를 2026 원문에서 확인.', XOM_CCS_NG3),
        relation('New Generation Gas Gathering · NG3', None, 'customer', 'Gillis 가스 처리시설에서 포집한 CO₂ 운송·저장. 2026-02 상업 운영, CO₂ 제거 능력과 실제 처리량 구분.', XOM_CCS_NG3, 'ng3'),
        relation('Golden Pass LNG', None, 'partner', 'QatarEnergy 70%·ExxonMobil 30%의 LNG 사업. 2026-03-30 첫 LNG 생산은 1호 train이며 3개 train 전체 완료로 표시하지 않음.', GOLDEN_PASS, 'golden-pass-lng'),
        relation('QatarEnergy', None, 'partner', 'Golden Pass 공동사업 70%·ExxonMobil 30%. 자본·공동사업 관계이며 LNG 구매자 관계로 바꾸지 않음.', ANNUAL['XOM'], 'qatarenergy'),
        relation('Imperial Oil', 'IMO', 'subsidiary', '캐나다 생산·정유·판매 사업. 2025년 말 ExxonMobil 지분 69.6%; Kearl의 프로젝트 지분과 모회사 소유 비율은 다름.', ANNUAL['XOM']),
    ],
    'SHEL': [
        relation('TechnipFMC', 'FTI', 'supplier', '2025-03 발표 Gato do Mato 해저 생산·배관·설치 iEPCI 계약. 계약 체결을 납품 완료·생산 개시로 해석하지 않음.', SHELL_FTI),
        relation('MODEC', None, 'supplier', 'Gato do Mato FPSO 공급과 20년 운영·유지 서비스 계약. 계약·예정 운전과 현재 생산을 구분.', SHELL_MODEC, 'modec'),
        relation('ARC Resources', None, 'subsidiary', '캐나다 Montney 생산 자산. 2026-09-02 인수 완료. Antero Resources(AR)와 다른 법인.', SHELL_ARC, 'arc-resources'),
        relation('LNG Canada', None, 'partner', 'Shell 40%의 Kitimat LNG 공동사업. 각 참여사가 자기 가스를 공급하고 자기 몫 LNG를 인수. 2단계 2026-09 FID.', LNG_CANADA, 'lng-canada'),
        relation('Equinor', 'EQNR', 'partner', 'Adura를 각 50% 소유해 UK 해상 생산 자산을 통합. 2025-12 설립 완료, 해상 풍력 등 제외 자산은 별도.', ADURA),
        relation('Adura', None, 'partner', 'UK North Sea 독립 생산 공동사업. Shell·Equinor 각 50%; 각사 UK 자산 전체가 이전된 것은 아님.', ADURA, 'adura'),
        relation('Petrobras', 'PBR', 'partner', 'Santos Route 1 가스 파이프라인 Petrobras 65%·Shell 25%·Petrogal 10%. 실제 수송 공동사업.', ANNUAL['PBR']),
    ],
    'BP': [
        relation('TechnipFMC', 'FTI', 'supplier', 'Tiber 20K의 해저 tree·manifold·연결·제어와 배관·설치 iEPCI. 2026-01 계약 발표이며 실제 납품·첫 생산과 분리.', BP_TIBER),
        relation('Eni', 'E', 'partner', 'Angola Azule Energy 공동사업 각 50%. 연결 그룹 전체의 지분이 아니라 해당 JV의 지분.', report('BP','interim')),
        relation('Azule Energy', None, 'partner', 'Angola 생산·개발 JV. Greater PAJ의 2026-06 FID와 기존 가동 자산을 구분.', report('BP','interim'), 'azule-energy'),
        relation('Castrol', None, 'subsidiary', '윤활유 사업. 65% Stonepeak 매각 계약·BP 35% 잔여 계획은 2026-06말 보고 기준 잔여 조건이 있는 거래.', report('BP','interim'), 'castrol'),
        relation('Stonepeak', None, 'partner', 'Castrol 지분 65% 인수 계약 상대. 계약·승인·종결을 구분하며 현재 공급사·고객사로 분류하지 않음.', BP_CASTROL, 'stonepeak'),
    ],
    'TTE': [
        relation('TechnipFMC', 'FTI', 'supplier', 'GranMorgu 해저 tree·manifold·연결·제어·umbilical·유연관 등을 통합 공급·설치하는 계약.', TTE_FTI),
        relation('EDF', None, 'supplier', '2028-01부터 12년간 프랑스 정유·화학 공장 전력 수요 약 60%·평균 약 400MW 장기 공급 계약. 현재 글로벌 전력 공급 비율이 아님.', TTE_EDF, 'edf'),
        relation('APA', 'APA', 'partner', 'Suriname GranMorgu 공동개발 지분40%; TotalEnergies 운영·40%, Staatsolie20%. 첫 생산 목표는 2028년.', TTE_GRANMORGU),
        relation('Staatsolie', None, 'partner', 'GranMorgu 공동개발 지분20%. Suriname 국영 자원 기업의 참여이며 외부 고객 거래가 아님.', TTE_GRANMORGU, 'staatsolie'),
    ],
    'E': [
        relation('BP', 'BP', 'partner', 'Azule Energy의 Angola 생산·개발 공동사업 각50%. BP·Eni 그룹 전체가 합병한 구조가 아님.', report('BP','interim')),
        relation('Azule Energy', None, 'partner', 'BP와 각50% 보유한 Angola 생산·개발 JV. 지분법 사업과 Eni 연결 자회사 구분.', ANNUAL['E'], 'azule-energy'),
        relation('PETRONAS', None, 'partner', 'Searah 각50% 공동사업: 인도네시아·말레이시아 가스 사업 통합. 2026-06 설립.', ENI_SEARAH, 'petronas'),
        relation('Searah', None, 'partner', '아시아 가스 생산·개발 JV. Eni·PETRONAS 각50%.', ENI_SEARAH, 'searah'),
        relation('YPF', 'YPF', 'partner', 'XRG와 함께 Argentina LNG 공동개발 계약. 2026-02 구속력 있는 계약·설계·FID 준비 단계.', ARGENTINA_LNG),
        relation('XRG', None, 'partner', 'YPF·Eni와 Argentina LNG 공동개발 계약. ADNOC 그룹의 투자 기업이며 임의로 ADNOC Gas 종목과 동일시하지 않음.', ARGENTINA_LNG, 'xrg'),
        relation('Plenitude', None, 'partner', '2026-10-01부터 Eni·Ares 공동 지배·연결 제외. Eni65.03%·Ares26.24%·EIP8.73%. 과거 연결 자회사와 최신 구조 구분.', ENI_PLENITUDE, 'plenitude'),
        relation('Enilive', None, 'subsidiary', '재생연료·연료 판매 사업. 2025년 공시 기준 Eni70%·KKR30% 지분 구조.', ANNUAL['E'], 'enilive'),
        relation('Saipem', None, 'supplier', '공시의 바이오정유·프로젝트 엔지니어링 협력. 지분법 투자·공급 서비스·풍력 협력은 각각 다른 역할.', ANNUAL['E'], 'saipem'),
    ],
    'EQNR': [
        relation('TechnipFMC', 'FTI', 'supplier', '2026-07 Omega Sør·Brime·Tyrihans Nord 해저 설비 프로젝트 계약. 프로젝트별 범위·계약·납품 구분.', FTI_EQUINOR),
        relation('NOV', 'NOV', 'supplier', '같은 세 노르웨이 개발 프로젝트에 유연관 공급. TechnipFMC와 다른 공급 품목·계약.', NOV_EQUINOR),
        relation('Shell', 'SHEL', 'partner', 'UK 해상 생산 Adura 각50%. 2025-12 설립 완료, 양사의 잔여 UK 자산은 별도.', ADURA),
        relation('Adura', None, 'partner', 'Shell과 각50%로 설립한 UK 생산 사업. 일부 생산·개발 자산을 통합.', ADURA, 'adura'),
        relation('Petoro', None, 'partner', '노르웨이 국가 SDFI 지분을 관리하는 참여자. Equinor도 참여하는 생산 허가·석유 시설의 국가 지분과 역할을 구분.', ANNUAL['EQNR'], 'petoro'),
    ],
    'PBR': [
        relation('TechnipFMC', 'FTI', 'supplier', '2025-09 해저 생산 시스템 계약: 생산 장비·서비스 공급. 발표된 계약을 현재 가동 장비 전부로 확대하지 않음.', PBR_FTI),
        relation('NOV', 'NOV', 'supplier', 'CO₂ 내성을 갖춘 심해 유연관 공동 개발·공급 기술. Petrobras 해상 가스의 부식·재료 조건과 연결.', NOV_PETROBRAS),
        relation('YPFB', None, 'supplier', '볼리비아 국영 기업의 장기 천연가스 공급 계약. 최소 물량·연료유 가격 연동·계약 기간 조건이 있음.', ANNUAL['PBR'], 'ypfb'),
        relation('Gas TransBoliviano · GTB', None, 'supplier', '볼리비아 생산지에서 브라질 국경까지 가스 수송 계약.', ANNUAL['PBR'], 'gtb'),
        relation('Transportadora Brasileira Gasoduto Bolívia-Brasil · TBG', None, 'supplier', '브라질 가스 수송망의 용량·운송 계약. 소유 비율과 현재 유료 서비스 관계 구분.', ANNUAL['PBR'], 'tbg'),
        relation('Transportadora Associada de Gás · TAG', None, 'supplier', '브라질 가스 수송망 이용 계약. 과거 지분 매각과 운송 서비스는 별도.', ANNUAL['PBR'], 'tag-brazil'),
        relation('Nova Transportadora do Sudeste · NTS', None, 'supplier', '브라질 가스 수송망 이용 계약.', ANNUAL['PBR'], 'nts-brazil'),
        relation('Shell', 'SHEL', 'partner', 'Route 1 가스 수송 공동사업 Petrobras65%·Shell25%·Petrogal10%.', ANNUAL['PBR']),
        relation('Petrogal Brasil', None, 'partner', 'Route 1 가스 파이프라인 지분10%. Galp 그룹과 개별 사업 법인을 구분.', ANNUAL['PBR'], 'petrogal-brasil'),
        relation('Ecopetrol', 'EC', 'partner', 'Colombia Sirius 해상 가스 개발·조건부 판매 공동사업. 현재 생산·매출이 아님.', ANNUAL['EC']),
    ],
    'EC': [
        relation('Occidental Petroleum', 'OXY', 'partner', '2019년부터 미국 Permian 개발 제휴. 공시 순면적은 Occidental 직접 운영 자산 범위.', ANNUAL['EC']),
        relation('Petrobras', 'PBR', 'partner', 'Sirius 개발·조건부 가스 판매 공동사업. 17개 구매자는 명단이 확인된 기업으로만 표시할 수 있음.', ANNUAL['EC']),
        relation('Cenit Transporte y Logística de Hidrocarburos', None, 'subsidiary', '원유·제품 수송·물류 사업. 내부 수송과 외부 고객 수수료 매출 구분.', ANNUAL['EC'], 'cenit'),
        relation('Interconexión Eléctrica · ISA', None, 'subsidiary', 'Ecopetrol이 2021년 지분51.4% 취득한 송전·도로 사업. 발전 판매와 송전 수익 구분.', ANNUAL['EC'], 'isa'),
        relation('Refinería de Cartagena · Reficar', None, 'subsidiary', 'Cartagena 정유·제품 사업. 공시 연결 정유·석유화학 부문에 포함.', ANNUAL['EC'], 'reficar'),
    ],
    'YPF': [
        relation('Chevron', 'CVX', 'partner', 'CDNC를 통한 Narambuena 공동 개발 각50%. 블록·허가·시추·생산 개시 단계 구분.', ANNUAL['YPF']),
        relation('Chevron', 'CVX', 'supplier', '아르헨티나에서 Chevron Group I·II·III 기유의 독점 유통사인 YPF에 기유 공급. 상류 JV와 별도 제품 거래.', ANNUAL['YPF']),
        relation('Vista Energy', 'VIST', 'partner', 'Petronas 매각 이후 La Amarga Chica를 YPF와 공동 운영. 과거 Petronas 참여를 현재 관계로 유지하지 않음.', ANNUAL['YPF']),
        relation('Eni', 'E', 'partner', 'Argentina LNG의 공동 개발·설계·FID 준비 계약. 현재 가동 LNG 사업이 아님.', ARGENTINA_LNG),
        relation('XRG', None, 'partner', 'Argentina LNG의 구속력 있는 공동 개발 계약 상대.', ARGENTINA_LNG, 'xrg'),
        relation('Oldelval', None, 'supplier', 'VMOC에서 연결되는 원유 수송망. 정유 공급·수출 경로이며 장래 VMOS 수출 전용 경로와 구분.', ANNUAL['YPF'], 'oldelval'),
    ],
}

# Context pages intentionally describe only the verified business/project role.
# A foreign listing or private-company name never becomes a guessed US ticker.
PRIVATE = {
    'modec': profile('MODEC', XOM_MODEC, '해상 원유 생산용 FPSO·부유식 설비를 설계·조달·건설·설치하고 운영·유지보수하는 일본 기업입니다.', 'ExxonMobil Hammerhead와 Shell 브라질 프로젝트의 공개 계약에서 설비 공급과 장기 운영 역할이 확인됩니다.'),
    'ng3': profile('New Generation Gas Gathering · NG3', XOM_CCS_NG3, 'East Texas·Louisiana의 가스를 집하해 Gillis 처리시설에서 처리하는 프로젝트입니다.', '처리 중 제거한 CO₂는 ExxonMobil이 운송·저장합니다. 원문은 연간 최대 1,200,000톤의 제거 능력을 제시하며 실제 처리량과 구분합니다.'),
    'golden-pass-lng': profile('Golden Pass LNG', GOLDEN_PASS, '미국 Sabine Pass에서 가스를 액화·수출하는 QatarEnergy·ExxonMobil 공동사업입니다.', '2026년 3월 30일 첫 LNG 생산을 발표했습니다. 단계별 생산·출하·추가 train 건설을 구분합니다.'),
    'arc-resources': profile('ARC Resources', SHELL_ARC, '캐나다 British Columbia·Alberta의 Montney 원유·가스 생산 사업입니다. Shell이 2026년 9월 2일 인수를 완료했습니다.', '가스 생산·개발 자산을 Shell의 캐나다 통합 가스·LNG 사업과 연결합니다. 미국 Antero Resources 종목 AR과 다른 법인입니다.'),
    'lng-canada': profile('LNG Canada', LNG_CANADA, 'British Columbia Kitimat의 가스 액화·LNG 수출 공동사업입니다. 각 참여자가 자기 가스를 공급하고 자기 몫 LNG를 인수합니다.', '현재 1단계 연간 14,000,000톤, 투자 결정한 2단계 포함 향후 28,000,000톤 계획입니다. Shell40%·PETRONAS25%·PetroChina15%·Mitsubishi15%·Korea Gas5%.', [('가스·액화·출하','Coastal GasLink 파이프라인과 액화·저장·선박 출하가 연결됩니다. 2단계는 추가 train·저장·출하와 5개 압축소를 계획합니다.')]),
    'petronas': profile('PETRONAS', LNG_CANADA, '말레이시아 에너지 그룹으로 LNG Canada와 Eni의 Searah 공동사업에 참여합니다.', 'LNG Canada 지분25%의 가스 공급·LNG 인수 역할과 Searah 지분50%의 아시아 가스 사업은 서로 다른 프로젝트입니다.'),
    'petrochina-lngcanada': profile('PetroChina Company Limited', LNG_CANADA, 'LNG Canada 지분15%의 공동사업자입니다.', '자기 몫 가스를 공급하고 생산된 LNG의 지분 물량을 인수합니다. 이 페이지는 해당 사업 역할만 정리합니다.'),
    'mitsubishi-lngcanada': profile('Mitsubishi Corporation', LNG_CANADA, 'LNG Canada 지분15%의 공동사업자입니다.', '가스 조달과 지분 LNG 인수 역할이며 Shell의 일괄 고객사로 분류하지 않습니다.'),
    'korea-gas': profile('Korea Gas Corporation', LNG_CANADA, 'LNG Canada 지분5%에 참여하는 한국가스공사입니다.', '참여 지분의 가스 공급·LNG 인수 구조입니다. 해당 JV의 물량을 한국가스공사 전체 조달로 확대하지 않습니다.'),
    'jgc-lngcanada': profile('JGC Corporation', LNG_CANADA_EPC, 'Fluor와 구성한 공동사업을 통해 LNG Canada 액화시설의 설계·조달·시공을 수행합니다.', 'EPC 공급자의 역할이며 LNG 구매자·가스 공급자·생산 JV 지분 참여와 다릅니다.'),
    'fluor-lngcanada': profile('Fluor', LNG_CANADA_EPC, 'JGC와 구성한 공동사업을 통해 LNG Canada 설계·조달·시공을 수행하는 엔지니어링 기업입니다.', '이 페이지는 확인한 프로젝트 공급 역할을 정리하며 산업 전체·모든 고객 계약을 뜻하지 않습니다.'),
    'adura': profile('Adura', ADURA, 'Shell·Equinor가 각50% 소유하는 UK North Sea 생산 공동사업입니다. 2025년 12월 설립을 완료했습니다.', 'Mariner·Rosebank·Buzzard·Shearwater 등 생산·개발 자산을 묶었습니다. 각사의 일부 잔여 UK 자산·풍력 사업은 이전 범위에서 제외됩니다.'),
    'azule-energy': profile('Azule Energy', report('BP','interim'), 'BP·Eni가 각50% 보유한 Angola 원유·가스 생산·개발 공동사업입니다.', '기존 생산과 Greater PAJ의 신규 투자 결정·향후 생산을 구분합니다. 개별 블록의 Azule 지분과 모회사 각50% 지분은 다릅니다.'),
    'castrol': profile('Castrol', report('BP','interim'), '차량·산업용 윤활유·유체 사업입니다.', '2025년 12월 Stonepeak가65%를 인수하고 BP35%를 남기는 계약을 발표했습니다. 2026년 6월 말 보고에서는 잔여 조건·연말 완료 목표가 있는 거래입니다.'),
    'stonepeak': profile('Stonepeak', BP_CASTROL, '인프라 투자 기업으로 Castrol 지배 지분65% 인수 계약 상대입니다.', '투자·거래 종결 조건과 윤활유 사업의 실제 공급·고객 관계는 구분합니다.'),
    'staatsolie': profile('Staatsolie', TTE_GRANMORGU, 'Suriname의 국영 자원 기업으로 GranMorgu 지분20%를 보유합니다.', 'TotalEnergies 운영·40%, APA40%와 함께 개발하는 공동사업이며 첫 원유 생산 목표는2028년입니다.'),
    'edf': profile('EDF', TTE_EDF, '프랑스 전력 기업으로 TotalEnergies 프랑스 정유·화학 공장에 장기 전력을 공급하는 계약을 맺었습니다.', '2028년부터12년·평균약400MW·해당 공장 전력 수요 약60%의 계약 범위입니다. 현재 공급 실적·글로벌 그룹 전체 비율과 구분합니다.'),
    'searah': profile('Searah', ENI_SEARAH, 'Eni·PETRONAS 각50%의 인도네시아·말레이시아 가스 공동사업입니다.', '2026년6월 설립을 발표했습니다. 생산·개발·탐사를 통합하는 해당 JV와 두 모기업 전체를 구분합니다.'),
    'xrg': profile('XRG', ARGENTINA_LNG, 'ADNOC 그룹의 투자 기업으로 YPF·Eni와 Argentina LNG 공동 개발에 참여합니다.', '2026년2월 공동 개발 계약은 설계·투자 결정 준비 단계이며 계획 액화 능력은 현재 생산이 아닙니다.'),
    'plenitude': profile('Plenitude', ENI_PLENITUDE, '재생에너지 발전·전력과 가스 소매·전기차 충전 사업입니다.', '2026년10월1일 Eni65.03%·Ares26.24%·EIP8.73%로 변경됐고 Eni·Ares 공동 지배로 연결 제외됩니다. 소유 지분과 단독 연결 지배를 구분합니다.'),
    'enilive': profile('Enilive', ANNUAL['E'], 'Eni의 바이오정유·재생연료·연료 유통·모빌리티 사업입니다.', '2025년 공시의 지분은 Eni70%·KKR30%입니다. 재생연료 원료·전처리·제조·인증과 판매망을 연결합니다.'),
    'saipem': profile('Saipem', ANNUAL['E'], '해상·육상 에너지 프로젝트의 엔지니어링·건설·시공·관련 장비와 서비스를 제공합니다.', 'Eni 공시에서 바이오정유·프로젝트 협력과 지분법 투자 관계를 확인했습니다. 소유 관계와 실제 공급 프로젝트는 별도입니다.'),
    'petoro': profile('Petoro', ANNUAL['EQNR'], '노르웨이 국가의 직접 재정 지분 SDFI를 관리하는 국영 기업입니다.', 'Equinor도 참여하는 허가·석유 시설에 국가 지분을 관리합니다. 관리·공동사업 권리와 일반 가스 구매 고객 역할은 다릅니다.'),
    'ypfb': profile('YPFB', ANNUAL['PBR'], '볼리비아 국영 석유·가스 기업으로 Petrobras의 장기 가스 조달 상대입니다.', '공시는 최소 공급·구매 물량과 연료유 가격 연동 등 계약 조건을 설명합니다. 수송은 별도 운송사 계약으로 연결됩니다.'),
    'gtb': profile('Gas TransBoliviano · GTB', ANNUAL['PBR'], '볼리비아 생산지에서 브라질 국경으로 연결되는 가스 수송망 운영사입니다.', 'Petrobras와 수송 계약이 확인됩니다. 가스 생산·판매자 YPFB와 다른 운송 역할입니다.'),
    'tbg': profile('Transportadora Brasileira Gasoduto Bolívia-Brasil · TBG', ANNUAL['PBR'], '브라질 가스 수송망·용량을 제공하는 운송사입니다.', 'Petrobras가 수송 계약을 공시합니다. 용량 경매·계약 기간과 지분 매각 이력은 구분합니다.'),
    'tag-brazil': profile('Transportadora Associada de Gás · TAG', ANNUAL['PBR'], '브라질 가스 파이프라인 수송 사업자입니다.', 'Petrobras 공시의 수송 계약 상대입니다. 과거 지분 소유 이력이 현재 공급·수송 역할을 대체하지 않습니다.'),
    'nts-brazil': profile('Nova Transportadora do Sudeste · NTS', ANNUAL['PBR'], '브라질 가스 파이프라인 수송 사업자입니다.', 'Petrobras와 맺은 수송 계약이 확인됩니다. 원유·가스 생산·판매 사업과 다른 수수료·용량 서비스입니다.'),
    'petrogal-brasil': profile('Petrogal Brasil', ANNUAL['PBR'], '브라질 자원 사업 법인으로 Petrobras·Shell과 Route1 가스 수송에 참여합니다.', 'Route1 지분10%이며 Petrobras65%·Shell25%와 구분합니다. 이 비율은 Galp 그룹 전체의 소유 비율이 아닙니다.'),
    'cenit': profile('Cenit Transporte y Logística de Hidrocarburos', ANNUAL['EC'], 'Ecopetrol의 원유·석유제품 수송·물류 사업입니다.', '파이프라인·터미널과 관련 물류의 내부·외부 서비스를 연결합니다. 총 수송량을 외부 고객 매출로 그대로 환산하지 않습니다.'),
    'isa': profile('Interconexión Eléctrica · ISA', ANNUAL['EC'], '전력 송전·유료 도로 등 인프라를 운영하는 Ecopetrol 연결 사업입니다.', 'Ecopetrol은2021년51.4%를 취득했습니다. 송전 매출·자산은 발전 전력 판매와 다릅니다.'),
    'reficar': profile('Refinería de Cartagena · Reficar', ANNUAL['EC'], 'Cartagena의 정유·석유제품 사업으로 Ecopetrol 정유·석유화학 부문에 포함됩니다.', '원유 처리·정유제품 판매와 그룹 생산·물류를 연결합니다. 정유 처리량과 지분 원유 생산량을 구분합니다.'),
    'oldelval': profile('Oldelval', ANNUAL['YPF'], '아르헨티나 원유 수송망으로 Vaca Muerta VMOC 파이프라인에서 이어지는 경로입니다.', 'La Plata 정유 공급·수출 경로를 연결합니다. VMOS 수출 전용 경로와 구분합니다.'),
}

PRIVATE['lng-canada']['relations'] = [
    relation('Shell', 'SHEL', 'partner', '지분40%의 가스 공급·LNG 인수 역할.', LNG_CANADA),
    relation('PETRONAS', None, 'partner', '지분25%의 가스 공급·LNG 인수 역할.', LNG_CANADA, 'petronas'),
    relation('PetroChina Company Limited', None, 'partner', '지분15%의 가스 공급·LNG 인수 역할.', LNG_CANADA, 'petrochina-lngcanada'),
    relation('Mitsubishi Corporation', None, 'partner', '지분15%의 가스 공급·LNG 인수 역할.', LNG_CANADA, 'mitsubishi-lngcanada'),
    relation('Korea Gas Corporation', None, 'partner', '지분5%의 가스 공급·LNG 인수 역할.', LNG_CANADA, 'korea-gas'),
    relation('JGC Corporation', None, 'supplier', 'JGC·Fluor 공동사업의 설계·조달·시공 역할.', LNG_CANADA_EPC, 'jgc-lngcanada'),
    relation('Fluor', None, 'supplier', 'JGC·Fluor 공동사업의 설계·조달·시공 역할.', LNG_CANADA_EPC, 'fluor-lngcanada'),
]
PRIVATE['modec']['relations'] = [
    relation('ExxonMobil', 'XOM', 'customer', 'Hammerhead FPSO 설비 공급·향후 운영·유지 계약.', XOM_MODEC),
    relation('Shell', 'SHEL', 'customer', '브라질 FPSO 설비·20년 운영·유지 계약.', SHELL_MODEC),
]
PRIVATE['golden-pass-lng']['relations'] = [
    relation('ExxonMobil', 'XOM', 'partner', '지분30%의 공동사업자.', ANNUAL['XOM']),
    relation('QatarEnergy', None, 'partner', '지분70%의 공동사업자.', ANNUAL['XOM'], 'qatarenergy'),
]
PRIVATE['azule-energy']['relations'] = [
    relation('BP', 'BP', 'partner', 'Azule 지분50%.', report('BP','interim')),
    relation('Eni', 'E', 'partner', 'Azule 지분50%.', report('BP','interim')),
]
PRIVATE['adura']['relations'] = [
    relation('Shell', 'SHEL', 'partner', 'Adura 지분50%.', ADURA),
    relation('Equinor', 'EQNR', 'partner', 'Adura 지분50%.', ADURA),
]

for _symbol in SYMBOLS:
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol].get('revenue_mix', [])
    PUBLIC[_symbol]['filings'] = [ANNUAL[_symbol]]
    PUBLIC[_symbol]['sources'].extend(item['source'] for item in PUBLIC[_symbol]['brief'])
    PUBLIC[_symbol]['sources'].extend(edge['source'] for edge in EDGES[_symbol])
