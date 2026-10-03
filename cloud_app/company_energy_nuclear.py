"""Korean, source-backed nuclear fuel chain notes, including related industries.

Mining, conversion, enrichment, fuel research and rare earths are distinct roles.
This module does not assign GICS, infer unnamed buyers or make model calls.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('CCJ', 'DNN', 'NXE', 'UEC', 'EU', 'URG', 'LEU', 'LTBR', 'UUUU')
AIF = {s: report(s, 'aif' if 'aif' in REPORTS[s] else 'annual') for s in SYMBOLS}
FIN = {s: report(s, 'financials' if 'financials' in REPORTS[s] else 'annual') for s in SYMBOLS}
CCJ_CIGAR = source('Cameco · Cigar Lake 지분 거래 실제 완료',
    'https://www.cameco.com/media/news/cameco-closes-deal-to-increase-ownership-in-cigar-lake-mine-0', '2026-07-02')
CCJ_Q2 = source('Cameco · 2026 Q2 생산·정련·전환·계약',
    'https://www.cameco.com/media/news/cameco-reports-2026-second-quarter-results', '2026-07-31')
CCJ_WESTINGHOUSE = source('Cameco · 2026 Q2 재무 주석 19 · Westinghouse 실제 연료 거래',
    'https://www.sec.gov/Archives/edgar/data/1009001/000119312526326768/d125942dex993.htm', '2026-07-31')
ENERGOATOM = source('Energoatom · 2023년 Cameco 연료 공급 계약 체결',
    'https://energoatom.com.ua/en/news/petro-kotin-specialno-dlya-expro-consulting-pidbiv-pidsumki-roboti-energoatoma-za-2023-rik', '2023년 실적 · 열람 2026-10-03')
DNN_CONSTRUCTION = source('Denison · Phoenix 부지 준비 완료·본공사 진행',
    'https://denisonmines.com/news/denison-announces-completion-of-site-preparation-a-122849/', '2026-07-28')
DNN_POWER = source('Denison · SaskPower 138 kV 전력망 연결',
    'https://denisonmines.com/site/assets/files/7279/denison_mines_corp__denison_announces_grid_power_available_at_fu.pdf', '2026-01-08')
CNSC_ROOK = source('CNSC · Rook I 부지 준비·건설 허가',
    'https://www.canada.ca/en/nuclear-safety-commission/news/2026/03/commission-issues-a-licence-to-nexgen-energy-ltd-authorizing-site-preparation-and-construction-of-its-rook-i-project.html', '2026-03-05')
NXE_START = source('NexGen · 2026-08-13 Rook I 착공 행사·이미 진행 중인 공사',
    'https://www.nexgenenergy.ca/events-webcasts/nexgen-groundbreaking-ceremony---august-13-2026', '2026-08-25')
NXE_SRC = source('NexGen · Patterson Corridor East 시료와 SRC 분석',
    'https://www.nexgenenergy.ca/news-releases/nexgen-expands-high-grade-subdomain-vertical-extent-by-17-to-644-m-and-intersects-continuo', '2026-08-25')
NXE_SITE = source('NexGen · Rook I 현재 건설 범위·설계',
    'https://www.nexgenenergy.ca/rook-1-project', '열람 2026-10-03')
EU_Q2 = report('EU', 'quarter')
URG_START = source('Ur-Energy · Shirley Basin 첫 우라늄 원료 운송',
    'https://www.ur-energy.com/news-media/press-releases/detail/410/ur-energy-announces-first-shipment-of-uranium-from-shirley', '2026-08-20')
LEU_DOE = source('Centrus · DOE 900,000,000 USD 최종 계약·실증 완료와 미래 증설',
    'https://www.centrusenergy.com/news/centrus-signs-contract-with-department-of-energy-for-900-million-award-intends-to-transition-haleu-production-cascade-to-commercial-operation/', '2026-07-01')
LEU_XENERGY = source('Centrus · X-energy LEU·HALEU 공급 계약',
    'https://www.centrusenergy.com/news/centrus-energy-signs-leu-and-haleu-supply-agreement-with-x-energy/', '2026-08-06 발표 · 2026-08-10 게시')
LEU_RADIANT = source('Centrus · Radiant Kaleidos HALEU 공급 계약',
    'https://www.centrusenergy.com/news/centrus-and-radiant-announce-long-term-partnership-for-domestic-haleu-to-supply-kaleidos-microreactors/', '2026-09-09')
LEU_ANTARES = source('Centrus · Antares HALEU 공급 계약',
    'https://www.centrusenergy.com/news/centrus-and-antares-sign-multi-year-haleu-supply-contract/', '2026-09-17')
UUUU_ASM = source('Energy Fuels · Australian Strategic Materials 인수 실제 완료',
    'https://investors.energyfuels.com/2026-08-28-Energy-Fuels-Completes-Acquisition-of-Australian-Strategic-Materials', '2026-08-28')
UUUU_VAC = source('Energy Fuels · VAC 인수 계약·별도 완료 조건',
    'https://investors.energyfuels.com/2026-06-23-Energy-Fuels-Announces-Definitive-Agreement-to-Acquire-VAC-for-1-9-Billion-Equity-Value', '2026-06-23')

PUBLIC = {
    'CCJ': profile('Cameco', AIF['CCJ'],
        '캐나다·카자흐스탄 우라늄 생산과 매입·판매, 정련·전환·연료 가공을 운영합니다. 광산에서 나온 우라늄 정광과 원전용 UF₆·UO₂, 농축·원자로 서비스는 서로 다른 단계입니다. Westinghouse와 Inkai는 지분법 사업입니다.',
        '2025년 연결 매출 3,481,933,000 CAD는 우라늄 2,873,950,000·연료 서비스 562,421,000·기타 45,562,000입니다. Westinghouse 전체 매출이나 지분 비율을 적용한 내부 관리 매출을 연결 총매출에 다시 더하지 않습니다.',
        [('McArthur River → Key Lake', 'Saskatchewan 지하 광산의 고품위 광석을 Key Lake에서 처리합니다. 광산의 채굴량과 제련소 처리량은 같은 물량의 다른 단계이므로 합산하지 않습니다.'),
         ('Cigar Lake → Orano McClean Lake', 'Cigar Lake 광석을 Orano 운영 McClean Lake 제련소에서 처리합니다. 광산의 Cameco 지분은 2026년 7월 2일 거래 완료 후 57.418%입니다.'),
         ('Inkai · 카자흐스탄 ISR', 'Kazatomprom이 운영하는 공동사업입니다. Cameco 40%·Kazatomprom 60% 소유이며 우라늄 구매·판매와 지분법 이익을 구분합니다.'),
         ('Blind River·Port Hope', 'Blind River에서 우라늄 정광을 정련하고 Port Hope에서 UF₆·UO₂로 전환합니다. UF₆는 농축 단계, UO₂는 CANDU 등의 연료 제작으로 연결됩니다.'),
         ('Cameco Fuel Manufacturing', '원전 연료 다발과 부품 제조를 연결합니다. 정광 가격, 전환 가격, 연료 가공 서비스 대가는 서로 다른 거래 조건입니다.'),
         ('Westinghouse·GLE', 'Westinghouse 원전 연료·정비·설계 지분법 사업과 SILEX 기술을 이용하는 Global Laser Enrichment 개발 사업입니다. GLE는 상업 농축 공장의 실제 생산 매출로 표시하지 않습니다.')],
        customers='원전 운영사·전력 유틸리티·연료 제조사와 장기 계약으로 거래합니다. Energoatom의 우크라이나 연료 공급 계약과 Westinghouse의 연료 거래가 실명으로 확인됩니다. 연말 계약 잔량은 그해 인도 매출이 아닙니다.',
        inputs='광석·매입 우라늄·황산 등 시약·전력·수처리·운송·전환 공정과 숙련 인력이 필요합니다. Orano 처리 시설, Inkai 구매 우라늄과 SILEX 기술 사용은 각각 다른 공급 관계입니다.',
        competition='정광 공급은 광산 생산자·재고 판매자, 전환은 별도 전환 설비와 가격·기간·산지 조건에서 경쟁합니다. Cameco의 연결 매출 비율이나 생산능력을 제품 시장점유율로 대체하지 않습니다.'),
    'DNN': profile('Denison Mines', AIF['DNN'],
        'Saskatchewan 우라늄 광산·ISR 개발 기업입니다. Phoenix 개발이 핵심이며 Orano 운영 McClean Lake에서는 타사 광석 처리 수입이 발생합니다. 개발 광산의 미래 생산과 기존 제련소 수입을 구분합니다.',
        '2025년 매출 4,918,000 CAD는 광업 부문에 기록된 기존 처리 사업 중심의 수입입니다. Phoenix는 이 기간 상업 생산 매출이 없습니다. 우라늄 재고 평가·매각 손익과 운영 매출도 구분합니다.',
        [('Wheeler River · Phoenix', '직접 지분 90%와 JCU 보유 10%를 구분합니다. JCU의 50%를 보유하므로 간접분까지 포함한 유효 지분은 95%입니다. 이를 직접 소유 95% 또는 100%로 표시하지 않습니다.'),
         ('Phoenix · ISR·동결벽', '주입·회수정과 지하수 제어·동결벽·처리 설비를 구축합니다. 건설 허가와 가동 허가는 다르며 첫 생산 목표는 2028년 중반으로, 현재 생산 실적이 아닙니다.'),
         ('McClean Lake · 처리', 'Denison 22.5% 참여, Orano 운영의 공동사업입니다. Cigar Lake 광석의 유료 처리 계약과 그 대가의 일부를 Ecora에 이전한 기존 구조를 구분합니다.'),
         ('McClean North · SABRE', '2025년 재가동된 광체 채굴입니다. 공동사업 전체 생산량과 Denison 귀속 22.5% 물량을 별도로 읽어야 합니다.'),
         ('Midwest·Waterbury Lake', '각각 25.17%·70.55%의 개발·탐사 참여입니다. 아직 개발 중인 자원을 판매 가능한 생산량으로 합산하지 않습니다.'),
         ('JCU · 공동 탐사 포트폴리오', 'Denison과 UEC 계열 UEX가 각각 50%를 보유하며 UEX가 관리합니다. Phoenix 개발비 참여 여부에 관한 구조·분쟁은 광산 소유 지분과 별도입니다.')],
        customers='기존 처리 사업은 McClean Lake의 Cigar Lake 광석 처리로 연결됩니다. 미래 Phoenix 판매, 보유 정광 재고 거래, 현재 타사 광석 처리 계약은 서로 다른 수입 경로입니다.',
        inputs='SaskPower의 계통 전력, Wood Canada의 설계·조달·건설 관리, 시추·펌프·수처리·시약과 환경 복구가 필요합니다. Wood의 건설 관리 계약을 모든 장비의 일괄 공급 계약으로 확대하지 않습니다.',
        competition='우라늄 정광 공급과 장기 유틸리티 계약 시장을 대상으로 합니다. 고품위 자원 보유량은 현재 생산·현금 수입과 다르며 ISR 공정의 수질·회수율·허가 조건을 함께 확인해야 합니다.'),
    'NXE': profile('NexGen Energy', AIF['NXE'],
        'Saskatchewan 남서부 Athabasca의 Rook I·Arrow 우라늄 광산과 제련소를 개발하고 Patterson Corridor East를 탐사합니다. 현재는 건설 기업이며 상업 우라늄 생산 기업으로 표시하지 않습니다.',
        '2025년 감사 재무제표 주석 2는 탐사·개발 단계로 매출이 없다고 설명합니다. 손익계산서에는 매출 행이 없으며 금융수입 17,818,000 CAD는 우라늄 판매액이 아닙니다. 미인도 장기 판매 약정·자원량·설계 용량으로 제품별 매출이나 구성비를 만들지 않습니다.',
        [('Rook I·Arrow', '100% 보유 개발 프로젝트로 지하 채굴·제련·지하 광미 관리 시설을 함께 설계합니다. 2026년 3월 허가는 부지 준비·건설용이며 원전 운영·광산 상업 가동 허가가 아닙니다.'),
         ('지하 채굴·권양', '장공 채굴, 원격·자동화 장비, 광석 권양·저장·혼합이 계획돼 있습니다. 실제 채굴량·판매량과 설계 처리능력은 구분합니다.'),
         ('제련·U₃O₈ 정광', '광석을 제련해 우라늄 정광으로 만드는 공정입니다. 장기 발주·공사·시험 가동·고객 인도는 서로 다른 진행 단계입니다.'),
         ('지하 광미·수처리', '채굴 후 공간에 페이스트 광미를 되메우는 UGTMF와 물 처리를 설계합니다. 현장 공사 범위와 상업 운전 성능을 구분합니다.'),
         ('Patterson Corridor East', '탐사 시료를 Saskatchewan Research Council에서 분석합니다. 시추 방사선 계수와 시험실 우라늄 품위·광물 자원·매장량은 각각 다른 지표입니다.'),
         ('판매 약정·2021 타당성 조사', '이름이 공개되지 않은 미국 유틸리티 2곳과 장기 판매 약정이 공시돼 있습니다. Stantec·Wood·RPA의 2021년 기술 조사 참여는 현재 건설 EPC 수주로 바꾸지 않습니다.')],
        customers='미래 우라늄 정광 구매 약정 고객은 일부 익명 유틸리티로 공시됩니다. 이름을 추정하지 않습니다. 아직 상업 인도가 없는 건설 단계와 계약의 물량·가격 조항을 함께 표시합니다.',
        inputs='시추·시험실 분석·광산 및 제련 설계·토목·갱도·권양·전력·수처리 설비가 필요합니다. SRC의 현재 분석 서비스와 2021년 타당성 조사 작성사 역할은 근거 시점이 다릅니다.',
        competition='장기 우라늄 정광 공급 시장의 개발·생산 프로젝트와 경쟁합니다. 회사가 제시한 미래 세계 공급 비중은 가동 후 가정이며 현재 시장점유율이 아닙니다.'),
    'UEC': profile('Uranium Energy', AIF['UEC'],
        '미국 ISR 우라늄 생산과 캐나다 우라늄 프로젝트·매입 정광 재고를 운영합니다. Wyoming·Texas의 실제 생산, Saskatchewan 개발, 새 정련·전환 사업은 단계가 다릅니다.',
        '2026 회계연도는 2025-08-01~2026-07-31이며 매출은 37,250,000 USD입니다. 본문에서 이 수입은 재고 우라늄 판매로 분류됩니다. 채굴·처리된 물량을 모두 그해 판매 매출로 바꾸지 않습니다.',
        [('Christensen Ranch → Irigaray', 'Wyoming ISR에서 회수한 수지를 Irigaray 중앙 처리 설비로 연결합니다. FY2026 처리 생산량 211,942 lb와 이전 연도 포함 누적 341,908 lb는 기간이 다릅니다.'),
         ('Burke Hollow → Hobson', 'Texas의 Burke Hollow는 2026년 4월 생산을 시작했습니다. Hobson의 물리적 처리능력 2,000,000 lb와 허가 한도 4,000,000 lb는 실제 판매·현재 생산량이 아닙니다.'),
         ('세 중앙 처리 허브', '지역 위성 광구와 중앙 설비를 연결하는 구조입니다. 허브의 허가 용량 합계 12,100,000 lb를 올해 생산·판매량으로 제시하지 않습니다.'),
         ('Uranium Refining & Conversion', '정련·UF₆ 전환 설비 개발입니다. 초기 설계와 NRC 신청·심사 단계이며 Fluor의 엔지니어링 지원을 상업 전환 가동 실적으로 바꾸지 않습니다.'),
         ('UEX·JCU · 캐나다', 'UEX가 JCU의 50%를 보유하고 Denison이 나머지 50%를 보유합니다. 공동 프로젝트 권리·평가 손익·연결 매출은 서로 다릅니다.'),
         ('매입 정광·보관', '매입 우라늄을 Cameco의 캐나다 시설 및 ConverDyn의 미국 Metropolis 시설에서 보관합니다. 보관 서비스와 자체 채굴 생산은 별도입니다.')],
        customers='전력 유틸리티·정광 구매자에게 인도하며 매입 재고 판매도 포함합니다. 원문에 이름이 없는 구매자를 다른 원전 기업 이름으로 채우지 않습니다.',
        inputs='ISR 주입·회수정·수지·시약·전력·수처리, 중앙 처리·드럼·운송·보관과 Fluor 설계 서비스가 필요합니다. ConverDyn의 현재 참여사는 Solstice Advanced Materials와 General Atomics로 공시됩니다.',
        competition='미국 정광 생산·판매와 글로벌 우라늄 재고 공급 시장입니다. 생산 원가, 재고 매입 원가, 현물·장기 계약 가격과 미래 전환 설비 개발비를 구분합니다.'),
    'EU': profile('enCore Energy', AIF['EU'],
        '미국 ISR 우라늄 생산 기업으로 Texas의 Rosita·Alta Mesa 중앙 처리 설비와 위성 광구를 연결합니다. Kingsville Dome 및 Dewey Burdock·Gas Hills는 가동 상태·허가가 서로 다릅니다.',
        '2025년 연결 매출 43,155,000 USD는 우라늄 판매입니다. 익명 고객 3곳의 매출 27,231,000·10,980,000·4,944,000 USD는 판매 집중도이며 고객사를 식별하는 자료가 아닙니다. Alta Mesa는 70% 지분으로 지배·연결하고 30% 비지배지분을 구분합니다.',
        [('Rosita CPP', '2023년 11월부터 가동한 Texas 중앙 처리 시설입니다. 용존 우라늄을 회수한 수지를 처리·건조해 U₃O₈를 인도하며 허가 용량과 실제 생산은 다릅니다.'),
         ('Alta Mesa CPP·정군', 'enCore 70%·Boss Energy 30% 구조이며 enCore가 관리·지배합니다. 현장 주입·회수정 증설과 처리 설비의 이온 교환 회로 가동 단계가 별도입니다.'),
         ('Kingsville Dome', '허가·설비를 보유한 세 번째 중앙 처리 후보입니다. 기존 허가·장비 보유만으로 현재 상업 생산 중이라고 표시하지 않습니다.'),
         ('Upper Spring Creek–Brown', '2026년 6월 말 기준 위성 설비 1단계 건설 완료 후 최종 추출 허가가 필요한 단계입니다. 1,600 gpm 현장 유량 설계와 3,200 gpm 증설 목표는 판매 물량이 아닙니다.'),
         ('Dewey Burdock·Gas Hills', 'South Dakota·Wyoming 개발 자산입니다. WWC Engineering의 기술 보고서·허가·후속 건설을 원료 생산 실적으로 합산하지 않습니다.'),
         ('Verdera · 자산 매각', 'New Mexico의 Crownpoint·Hosta Butte 권리 매각 조건이 2026년 2월 충족되어 자산 제거·주식 대가가 인식됐습니다. 현재 enCore 직접 생산 자산으로 남겨 두지 않습니다.')],
        customers='공시 매출은 익명 유틸리티 판매 계약에 집중됩니다. 자체 생산과 외부 매입 정광을 함께 인도할 수 있으므로 인도량이 자체 추출량과 같다고 가정하지 않습니다.',
        inputs='시추·펌프·회수 수지·시약·전력·수질 제어·중앙 처리·운송·전환 시설 보관이 필요합니다. WWC Engineering은 기술 평가 서비스, Boss는 Alta Mesa 공동사업 및 별도의 과거 우라늄 대여 상대입니다.',
        competition='미국 ISR·기타 정광 공급과 유틸리티 장기 계약 시장입니다. 자체 추출 속도, 매입 인도 원가, 단계별 허가와 정군 개발 상태가 수입·투입 비용에 연결됩니다.'),
    'URG': profile('Ur-Energy', AIF['URG'],
        'Wyoming의 Lost Creek과 Shirley Basin에서 ISR 우라늄을 생산합니다. Shirley Basin 위성 광구의 수지를 Lost Creek 허브로 운송해 처리하는 구조입니다.',
        '2025년 매출은 27,207,000 USD로 우라늄 정광 27,179,000·처리 수수료 28,000입니다. 원문 고객 A/B의 수입은 고객 집중도이며 별도 제품 매출에 더하지 않습니다.',
        [('Lost Creek · ISR 허브', '주입·회수정에서 우라늄을 용액으로 회수하고 수지·처리·건조 설비를 이용합니다. 광구와 중앙 처리 공장의 생산 단계를 중복 계산하지 않습니다.'),
         ('Shirley Basin · 실제 생산', '2026년 4월 추출 시작, 6월 최종 운송·운영 허가를 거쳐 8월 19일 첫 우라늄 원료를 Lost Creek으로 운송했습니다. 첫 운송을 정상 최대 가동량으로 확대하지 않습니다.'),
         ('허브·위성 처리', 'Shirley Basin의 우라늄 적재 수지를 Lost Creek에서 최종 처리합니다. 같은 회사의 내부 원료 운송은 외부 고객의 정광 인도와 다릅니다.'),
         ('유틸리티 정광 인도', '생산·외부 매입·재고 및 계약 인도의 시점이 다릅니다. 전환 시설로 인도된 정광과 광산에서 회수된 정광을 기간·소유권 기준으로 구분합니다.'),
         ('허가 생산·타사 처리 용량', '두 시설의 연간 허가 생산·처리 용량 4,200,000 lb와 Shirley Basin 2,000,000 lb는 실제 연간 생산량이 아닙니다.'),
         ('기술 평가·복구', 'WWC Engineering의 Lost Creek·Shirley Basin 기술 보고서와 수질 복구·보증·광구 개발 비용이 원문에 제시됩니다. 미개발 자원을 판매 재고에 합산하지 않습니다.')],
        customers='원전 유틸리티와 장기·개별 인도 계약으로 거래합니다. 고객 실명이 공개되지 않은 A/B를 임의로 이름 붙이지 않습니다. 원료 운송 단계의 수지와 최종 판매 정광도 구분합니다.',
        inputs='시추·주입/회수정·전력·수지·시약·펌프·수질 복구·운송과 WWC Engineering 기술 평가가 필요합니다. 공시에 이름이 없는 설비 공급자를 계약 상대처럼 표시하지 않습니다.',
        competition='미국 ISR 및 다른 정광 생산·판매 기업의 유틸리티 공급 범위와 겹칩니다. 자원 평가·허가 용량·처리 생산·고객 인도량은 각기 다른 지표입니다.'),
    'LEU': profile('Centrus Energy', AIF['LEU'],
        '원전용 저농축 우라늄·농축 서비스의 공급·판매와 미국 원심분리 농축 기술·HALEU 개발을 운영합니다. 외부 SWU 조달, 자체 실증 생산, 증설·미래 고객 계약을 구분합니다.',
        '2025년 외부 매출 448,700,000 USD는 SWU 298,700,000·우라늄 47,500,000·기술 솔루션 102,500,000입니다. 본문 제거 전 합계 461,100,000의 잘못된 사업부 태그를 기술 솔루션 매출로 표시하지 않습니다.',
        [('SWU · 농축 서비스', '우라늄 동위원소 농축 작업의 단위와 대가입니다. TENEX·Orano 공급을 이용한 고객 판매이며 SWU 수량·우라늄 원료 중량·UF₆ 인도량은 단위가 다릅니다.'),
         ('우라늄·LEU 인도', '유틸리티의 농축 연료 구매와 원료 우라늄 인도·재고 거래를 연결합니다. 매출 인식·고객 선수금·미래 수주 잔고를 같은 금액으로 보지 않습니다.'),
         ('Piketon · HALEU 실증', 'DOE 실증 계약으로 생산한 누적 1,900 kg과 실증 완료를 구분합니다. 2026년 7월 계약 발표의 새 상업 용량 목표 2029년은 현재 생산능력이 아닙니다.'),
         ('American Centrifuge Operating', '자회사 ACO가 설비 개발·DOE 계약과 Fluor Federal Services의 EPC 계약을 수행합니다. 계약은 승인된 단계별 자금 범위에서 진행됩니다.'),
         ('X-energy·Radiant·Antares', '2026년 실제 체결된 LEU·HALEU 장기 공급 계약입니다. 고객 선납·미래 상업 인도 조항이 포함되며 현재 모두 인도 매출이 발생했다는 뜻은 아닙니다.'),
         ('기술 솔루션·설비 서비스', '농축 기술·엔지니어링·계약 서비스 부문입니다. 내부 매출 12,400,000 USD를 제거한 외부 수입과 회사 전체 제거 전 합계를 구분합니다.')],
        customers='기존 원전 유틸리티의 농축 연료 구매와 DOE 실증·개발 계약이 다른 수입 경로입니다. 후속 신규 고객 계약은 각 제품·관계 카드에 계약 시점과 함께 표시하며 고객사의 고객을 직접 구매자로 확대하지 않습니다.',
        inputs='TENEX와 Orano의 SWU, 우라늄 원료·UF₆ 운송·보관, 원심분리 장비·전력·기술 인력과 Fluor EPC가 필요합니다. 러시아산 공급에는 수입 제한·DOE 면제·기간 조건이 공시돼 있습니다.',
        competition='저농축 우라늄·HALEU 공급과 농축 기술·용량 개발 시장입니다. 조달 가능한 SWU, 허가·통상 조건, 고객 인도 시점과 증설 단계가 경쟁 범위를 결정합니다.'),
    'LTBR': profile('Lightbridge', AIF['LTBR'],
        '경수로 등에서 사용할 우라늄·지르코늄 기반 금속 핵연료를 연구하는 기업입니다. 연료 소재·형상·제조·조사 시험을 개발하며 상업 원전 연료 판매 단계와 구분합니다.',
        '2025년 원문 손익계산서의 매출은 0 USD입니다. 시험·개발 계약, 보유 현금·주식 발행, 미래 연료 판매 기대를 영업 매출로 표시하지 않습니다.',
        [('금속 우라늄·지르코늄 연료', '기존 산화물 연료와 다른 합금·형상·열 전달 특성을 연구합니다. 실증 전 제품 설계의 목표 성능을 상업 운전 검증 결과로 제시하지 않습니다.'),
         ('소재·시험 시편 제작', '합금·시편 제작 및 품질 확인을 진행합니다. 연구용 쿠폰·봉 시편은 전력회사에 인도하는 완성 연료 다발이 아닙니다.'),
         ('INL · ATR 조사 시험', 'Battelle Energy Alliance와의 CRADA를 통해 Idaho National Laboratory에서 조사 시험을 수행합니다. 2025년 11월 시작한 시편 조사와 조사 후 검사는 별도 단계입니다.'),
         ('조사 후 검사·인허가', '조사 후 물성·안전성 평가와 상용 인허가에 필요한 자료를 축적합니다. 예상 검사 일정·상업 허가·원전 장전은 각각 구분합니다.'),
         ('RATEN ICN · CANDU 검토', '루마니아 연구기관과 CANDU 적용 가능성을 검토했습니다. 완료된 1단계 연구와 추가 시험·후속 연구 계획을 연료 공급 계약으로 바꾸지 않습니다.'),
         ('Centrus · 완료된 FEED', '2024년에 수행·완료된 연료 제조 관련 개념·공정 설계 연구입니다. 과거 엔지니어링 용역을 현재 장기 우라늄 구매 계약으로 표시하지 않습니다.')],
        customers='상업 연료 판매 고객 매출은 발생하지 않았습니다. 연구기관·개발 파트너와의 시험·설계 협력이 확인되며 구매자가 확정되지 않은 원전 시장을 실명 고객 목록으로 만들지 않습니다.',
        inputs='우라늄·지르코늄 소재, 연료 제조 공정·시험 장비·조사 시설·분석·안전성 자료와 연구 인력이 필요합니다. INL·RATEN·Centrus의 역할은 상업 연료 납품과 다릅니다.',
        competition='기존 원전용 연료와 새로운 연료 기술의 개발·검증 범위입니다. 시험 성숙도·인허가·연료 제조 및 원전 적용 과정이 사업 단계에 연결됩니다.'),
    'UUUU': profile('Energy Fuels', AIF['UUUU'],
        '미국 우라늄 채굴·White Mesa 처리와 희토류 분리·광물사를 운영합니다. 2026년 ASM 인수로 한국 희토류 금속·합금 설비가 추가됐습니다. 정광·산화물·합금·영구자석은 다른 가치사슬 단계입니다.',
        '2025년 매출 65,922,000 USD는 우라늄 정광 48,234,000·광물사 15,821,000·대체 원료 처리/기타 1,867,000입니다. POSCO 검증용 NdPr 샘플 1.7 t의 대가 80,000 USD는 시운전 자산 원가 차감으로 처리돼 이 매출 표에 추가하지 않습니다.',
        [('White Mesa · 우라늄·바나듐', '미국의 일반 우라늄 제련소로 자체·타사 광석과 대체 원료를 처리합니다. 바나듐은 원료·가격·가동 조건에 따라 회수하며 모든 기간 제품 매출이 발생하는 것은 아닙니다.'),
         ('희토류 분리 · NdPr·Dy·Tb', 'Chemours 등의 모나자이트 원료를 사용합니다. NdPr 분리·검증용 샘플, 중희토류 시험·증설과 상업 대량 판매는 단계가 다릅니다.'),
         ('Base Resources·광물사', '2024년 인수한 자회사입니다. Kenya Kwale은 2024년 말 채굴 종료 후 복구 단계이며 Madagascar Vara Mada는 개발 자산입니다. 과거 광물사 재고 판매와 신규 광산 가동은 다릅니다.'),
         ('Bahia·Donald', 'Brazil Bahia와 Australia Donald는 모나자이트·광물사 공급을 위한 개발 자산입니다. Donald의 2025년 말 실제 지분 9.48%와 투자 이행 시 최대 49% 권리를 구분합니다.'),
         ('ASM · 한국 금속·합금', '2026년 8월 28일 인수 완료로 한국 Ochang 금속 설비와 Australia Dubbo 개발 자산이 추가됐습니다. 기존 NdFeB 합금 용량 1,300 t/년과 연말 목표 3,600 t/년 증설은 다릅니다.'),
         ('VAC · 미래 자석 제조 연결', '2026년 6월 체결한 영구자석 기업 인수 계약입니다. ASM과 별도 승인·완료 조건이며 현재 이미 연결 자회사로 표시하지 않습니다.')],
        customers='유틸리티의 우라늄 구매, 광물사 구매자와 NdPr 검증 샘플 고객의 역할을 구분합니다. POSCO International은 실제 샘플 고객, Vulcan Elements는 샘플 검증·장기 계약 협상 의향 파트너입니다.',
        inputs='우라늄 광석·대체 원료·Chemours 모나자이트, 화학 시약·전력·수처리·분리 설비와 가공·복구가 필요합니다. 자체 개발 광산의 미래 원료 공급을 현재 생산 조달량으로 계산하지 않습니다.',
        competition='우라늄 정광, 티타늄·지르콘 광물사, 희토류 산화물·금속·자석은 서로 다른 시장입니다. 제품별 범위·기간·분모가 확인되지 않은 매출 비율을 전체 희토류 시장점유율로 표시하지 않습니다.'),
}

CURRENT = {
    'CCJ': [('Cigar Lake · 현재 소유·처리 상대', '2026-07-02 거래 완료 후 Cameco 57.418%·Orano 42.582%입니다. 광석 처리는 별도의 Orano McClean Lake 계약으로 연결됩니다.', CCJ_CIGAR),
        ('2026 Q2 · 실제 거래·운영 범위', '분기 생산·운송 차질과 회복, 전환 사업 및 Westinghouse 계약을 연간 매출 표와 구분합니다. 7월의 Cigar Lake 일시 중단을 계속 영구 중단된 자산으로 표시하지 않습니다.', CCJ_Q2)],
    'DNN': [('Phoenix · 현재 건설 단계', '2026-07-28 부지 준비 완료와 본공사 진행이 발표됐습니다. 첫 생산 2028년 중반은 목표 일정입니다.', DNN_CONSTRUCTION),
        ('계통 전력 · 실제 연결', '2026-01-08 SaskPower 138 kV 선로가 Phoenix에 연결되어 건설·동결벽 작업용 계통 전력을 사용할 수 있게 됐습니다.', DNN_POWER)],
    'NXE': [('Rook I · 건설 허가 범위', '2026-03-05 CNSC가 2036년까지의 부지 준비·건설 허가를 발급했습니다. 상업 가동 허가와 현재 생산 매출이 아닙니다.', CNSC_ROOK),
        ('현재 현장 · 착공 이후', '2026-08-13 착공 행사가 열렸고 토목·갱도 준비·제련 부지·도로·임시 수처리 공사가 진행 중입니다. 회사의 4년 공사 계획은 완료된 생산시설이 아닙니다.', NXE_SITE)],
    'UEC': [('최신 연차 · 실제 생산·수입', '2026-07-31 종료 연차는 Christensen Ranch·Burke Hollow의 생산과 37,250,000 USD 재고 판매를 구분합니다. 모든 보유 광산이 생산 중인 것은 아닙니다.', AIF['UEC']),
        ('정련·전환 · 개발 단계', 'Uranium Refining & Conversion의 NRC 신청·Fluor 엔지니어링과 신규 상업 시설 개발은 현재 정련·전환 매출이 아닙니다.', AIF['UEC'])],
    'EU': [('2026 Q2 · 실제 인도·개발', '상반기 계약 인도 485,000 lb에는 외부 매입 360,000 lb가 포함돼 자체 추출량과 다릅니다. Upper Spring Creek 위성은 최종 추출 허가 후 가동할 단계입니다.', EU_Q2),
        ('Verdera·Boss · 현재 범위', 'Verdera 자산 매각은 2026년 조건 충족 후 반영됐습니다. Alta Mesa 70/30 구조는 유지되며 Boss의 별도 우라늄 대여는 2025년 8월 상환·종료됐습니다.', EU_Q2)],
    'URG': [('Shirley Basin · 첫 실제 운송', '2026-08-19 Shirley Basin 원료가 Lost Creek 처리 공장으로 처음 운송됐습니다. 생산 확대 진행과 최대 허가 용량은 구분합니다.', URG_START)],
    'LEU': [('DOE · 실증과 새 계약', '2026-07-01 900,000,000 USD 개발 계약 체결이 발표됐습니다. 누적 1,900 kg 실증 생산과 2029년 목표 새 용량·상업 전환을 구분합니다.', LEU_DOE),
        ('Antares · 체결·미래 인도', '2026-09-17 소형 원자로용 HALEU 공급 계약입니다. 선수금·장기 약정이 현재 인도 완료 매출을 뜻하지 않습니다.', LEU_ANTARES)],
    'LTBR': [('실제 연구 단계·매출', '2025년 매출 0 USD와 INL 조사 시험·RATEN 연구·완료된 Centrus 설계를 구분합니다. 미래 상업 계약·허가·장전은 확정된 현재 매출이 아닙니다.', AIF['LTBR'])],
    'UUUU': [('ASM · 인수 완료·실제 설비', '2026-08-28 ASM 인수 완료로 한국 금속·합금 설비가 추가됐습니다. 미국 금속 설비 계획·한국 증설·Dubbo 개발과 현재 운전 설비는 구분합니다.', UUUU_ASM),
        ('VAC · 인수 계약 단계', 'VAC는 2026-06-23 계약이며 ASM 인수 완료와 별도입니다. 승인·자금·완료 조건이 남은 거래를 현재 자회사로 분류하지 않습니다.', UUUU_VAC)],
}
DRIVERS = {
    'CCJ': [('생산·구매·인도 시점', '자체 생산과 Inkai·외부 구매, 운송·재고, 유틸리티 인도 시점과 계약 가격이 매출·원가에 각각 반영됩니다.'),
        ('전환·광석 처리·공동사업', '정련·전환 요금과 Orano 처리 비용, Westinghouse·Inkai 지분법 손익은 정광 판매 매출과 범위가 다릅니다.')],
    'DNN': [('Phoenix · 회수·허가·개발비', 'ISR 회수율·지하수 제어·동결벽·건설 일정과 Wood·전력 비용을 현재 기존 처리 수입과 구분합니다.'),
        ('McClean · 처리·스트림', 'Cigar Lake 처리 물량·계약과 Ecora 수입 이전 구조가 해당 처리 수입에 연결됩니다. 광산 지분은 총물량과 귀속분의 분모를 바꿉니다.')],
    'NXE': [('공사·허가·자금', '갱도·제련·광미·수처리 공사의 일정·비용과 건설 후 추가 운전 절차가 상업 인도 개시에 연결됩니다.'),
        ('탐사·판매 약정', '시추·분석 결과, 자원·매장량 및 미래 고객 계약은 각각 기술·판매 범위입니다. 시추 계수를 제품 판매량으로 환산하지 않습니다.')],
    'UEC': [('ISR · 자체 생산과 재고', '정군 회수·수지 처리·물량 확대와 외부 재고 원가·인도 가격을 구분합니다. 생산량·재고·인도량은 같은 숫자가 아닙니다.'),
        ('새 전환 설비', 'NRC 심사·엔지니어링·건설·공급망과 자본 지출이 개발 단계에 연결됩니다. 인허가 신청은 상업 운전 개시가 아닙니다.')],
    'EU': [('자체 추출·매입 인도', '정군 회수율·매입 정광 비중·약정 가격·인도 시점이 각각 원가와 매출에 반영됩니다.'),
        ('연결·자산 매각·공정 상태', 'Alta Mesa 지배·비지배지분과 Verdera 매각 손익·주식 평가, 신규 위성 허가·유량 설계를 구분합니다.')],
    'URG': [('정군·수질·처리', '주입·회수정 개발과 수질·시약·수지·전력, Lost Creek으로의 원료 운송·처리가 생산량·투입 비용에 연결됩니다.'),
        ('계약 인도·복구', '정광 생산과 고객 인도·매입 재고, 장기 가격·복구 의무를 같은 시점의 물량·매출로 보지 않습니다.')],
    'LEU': [('농축·통상·조달', 'SWU 조달 계약·러시아산 수입 제한·면제, 원료 인도와 고객 판매 시점이 공급·원가에 연결됩니다.'),
        ('미래 증설·선수금', 'DOE 개발 단계·Fluor 승인 자금·고객 선수금·미래 인도·상업 운전은 다른 상태입니다. 수주 잔고를 현재 영업 수입에 더하지 않습니다.')],
    'LTBR': [('연구·시험·인허가', '소재 제조·조사 시험·조사 후 검사·안전성 자료·인허가와 연구비·자금 조달이 사업 진행에 연결됩니다.'),
        ('상업 적용 범위', '연구 결과와 원전 사업자의 실제 구매·장전 결정은 별개입니다. 미래 성능 목표를 검증 완료한 판매 제품으로 표시하지 않습니다.')],
    'UUUU': [('원료·분리·제품 단계', '우라늄 광석·대체 원료·모나자이트 투입과 산화물·금속·합금·자석의 검증·생산·판매 상태를 구분합니다.'),
        ('개발·복구·인수 범위', 'Kwale 복구·신규 광물사 프로젝트 개발, ASM 실제 연결과 VAC 조건부 거래는 시점과 회계 범위가 다릅니다.')],
}
for _symbol, _notes in PUBLIC.items():
    _notes['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    _notes['brief'].extend(fact(title, detail, origin) for title, detail, origin in CURRENT[_symbol])
    _notes['drivers'] = [fact(title, detail, AIF[_symbol]) for title, detail in DRIVERS[_symbol]]
    _notes['sources'].extend(origin for _, _, origin in CURRENT[_symbol])
# Product descriptions containing newer facts carry their own actual source.
PUBLIC['CCJ']['products'][1]['source'] = CCJ_CIGAR
PUBLIC['NXE']['products'][0]['source'] = CNSC_ROOK
PUBLIC['NXE']['products'][4]['source'] = NXE_SRC
PUBLIC['EU']['products'][3]['source'] = EU_Q2
PUBLIC['EU']['products'][5]['source'] = EU_Q2
PUBLIC['URG']['products'][1]['source'] = URG_START
PUBLIC['URG']['products'][4]['source'] = URG_START
PUBLIC['LEU']['products'][2]['source'] = LEU_DOE
PUBLIC['LEU']['products'][4]['source'] = LEU_ANTARES
PUBLIC['LEU']['products'][4].update(title='Antares · HALEU',
    detail='2026-09-17 체결된 소형 원자로용 장기 HALEU 공급 계약입니다. 미래 연료 인도·선수금과 현재 인도 완료 매출을 구분합니다.')
PUBLIC['LEU']['products'].extend([
    fact('X-energy · LEU·HALEU', '2026년 8월 Xe-100·TRISO-X 사업의 LEU·HALEU 공급 계약을 체결했습니다. 미래 인도와 선납 조건이며 고객사의 발전소 고객을 Centrus 직접 고객으로 확대하지 않습니다.', LEU_XENERGY),
    fact('Radiant · Kaleidos', '2026-09-09 Kaleidos 이동형 소형 원자로용 장기 HALEU 공급 계약입니다. 미래 인도·선납과 현재 연료 공급 완료를 구분합니다.', LEU_RADIANT),
])
PUBLIC['UUUU']['products'][4]['source'] = UUUU_ASM
PUBLIC['UUUU']['products'][5]['source'] = UUUU_VAC
for _symbol, _origin in [('NXE', NXE_SITE), ('URG', URG_START), ('UUUU', UUUU_ASM)]:
    PUBLIC[_symbol]['description_source'] = _origin
    PUBLIC[_symbol]['brief'][0]['source'] = _origin
PUBLIC['NXE']['sources'].extend([NXE_START, NXE_SRC])
PUBLIC['LEU']['sources'].extend([LEU_XENERGY, LEU_RADIANT])
PUBLIC['UUUU']['drivers'][1]['source'] = UUUU_ASM

PRIVATE = {
    'orano-canada': profile('Orano Canada', AIF['DNN'],
        '캐나다 우라늄 광산·제련 운영 상대입니다. McClean Lake에서 Cigar Lake 광석을 처리하고 Denison과 공동 광산·처리 사업을 운영합니다.',
        '이 페이지는 확인된 우라늄 처리·공동사업 역할을 정리합니다. Orano 그룹 전체 매출이나 광산 귀속량을 뜻하지 않습니다.'),
    'kazatomprom-inkai': profile('Kazatomprom · Inkai', AIF['CCJ'],
        '카자흐스탄 ISR 우라늄 생산 및 Cameco의 Inkai 구매·공동사업 상대입니다. Inkai는 Kazatomprom이 운영합니다.',
        'Inkai 우라늄 구매와 지분법 손익은 Cameco 연결 매출과 다릅니다. Inkai 전체 실적에 Cameco 40%를 적용해 연결 매출에 더하지 않습니다.'),
    'westinghouse-electric': profile('Westinghouse Electric Company', CCJ_WESTINGHOUSE,
        '원전 연료·설계·서비스 기업이며 Cameco의 실제 연료 거래 상대이자 지분법 투자 사업입니다.',
        'Cameco 2026 Q2 주석은 연료 판매와 보관·취급 거래를 구분합니다. 이 페이지의 Cameco 연결 거래를 Westinghouse 전체 실적으로 확대하지 않습니다.'),
    'energoatom-ukraine': profile('Energoatom', ENERGOATOM,
        '우크라이나 원전 운영사로 2023년에 Cameco와 장기 연료 공급 계약을 체결했습니다.',
        '원전 연료 구매자 역할입니다. 계약 약정과 기간별 실제 인도·판매 인식은 다릅니다.'),
    'silex-gle': profile('SILEX Systems · GLE 기술', AIF['CCJ'],
        'Global Laser Enrichment 개발 사업의 레이저 농축 기술·공동사업 상대입니다.',
        '기술 라이선스·개발 참여와 상업 농축 생산 매출을 구분합니다. Cameco의 개발 지분은 실제 농축 서비스 생산량이 아닙니다.'),
    'wood-canada': profile('Wood Canada', AIF['DNN'],
        'Denison Phoenix의 설계·조달·건설 관리와 NexGen의 과거 타당성 조사에 참여한 엔지니어링 기업입니다.',
        'Phoenix의 2026 건설 관리와 Rook I의 2021 기술 조사 역할은 시점·사업 범위가 다릅니다. 모든 장비의 단독 EPC 공급으로 확대하지 않습니다.'),
    'saskpower-phoenix': profile('SaskPower', DNN_POWER,
        'Saskatchewan 전력 공급자로 Phoenix 광산 부지에 138 kV 계통 전력을 연결했습니다.',
        '전력 공급·현장 연결 역할입니다. 광산의 미래 정광 매출이나 실제 최대 가동 전력 소비를 나타내지 않습니다.'),
    'ecora-mcclean': profile('Ecora Resources · McClean 처리 수입', AIF['DNN'],
        'McClean Lake의 Cigar Lake 처리 수입 일부를 이전받는 계약 상대입니다.',
        'Denison의 2017년 계약 구조는 광석 처리 수입의 분배이며 Ecora를 원전용 우라늄 구매자로 표시하지 않습니다.'),
    'stantec-rook': profile('Stantec · Rook I 기술 조사', AIF['NXE'],
        'Rook I의 2021년 기술·타당성 조사 작성에 참여한 엔지니어링 기업입니다.',
        '원문에 확인되는 과거 기술 평가 역할입니다. 2026년 건설 EPC 수주가 확인된 것처럼 표시하지 않습니다.'),
    'rpa-rook': profile('Roscoe Postle Associates · Rook I 기술 조사', AIF['NXE'],
        'Rook I의 2021년 자원·광산 기술 조사에 참여한 전문 평가 기업입니다.',
        '당시 보고서의 참여 회사명을 보존합니다. 과거 기술 조사 참여와 현재 건설 계약은 다릅니다.'),
    'src-geoanalytical': profile('Saskatchewan Research Council · Geoanalytical Laboratory', NXE_SRC,
        'NexGen Patterson Corridor East의 2026년 탐사 시료를 분석하는 독립 시험실입니다.',
        '시험·분석 서비스 관계이며 광석 구매·광산 공동 소유·우라늄 인도 고객이 아닙니다.'),
    'converdyn-metropolis': profile('ConverDyn · Metropolis Works', AIF['UEC'],
        '미국 우라늄 전환·보관 시설로 UEC의 매입 정광 보관 경로에 포함됩니다.',
        'UEC 연차가 명시한 참여사는 Solstice Advanced Materials와 General Atomics입니다. 확인된 보관 역할을 UEC 개발 전환 시설의 EPC 수주로 확대하지 않습니다.'),
    'uex-jcu': profile('UEX · JCU', AIF['UEC'],
        'UEC 계열 UEX가 JCU 지분 50%를 보유하고 Denison과 캐나다 우라늄 프로젝트를 연결합니다.',
        'JCU 공동사업과 UEX의 관리 역할을 구분합니다. 간접 광산 권리와 직접 소유 지분은 분모가 다릅니다.'),
    'boss-alta-mesa': profile('Boss Energy · Alta Mesa', EU_Q2,
        'Alta Mesa의 30% 참여사이며 enCore가 70%를 보유·지배·관리합니다.',
        '미국 공동사업 생산·분배와 Boss의 다른 사업은 별개입니다. enCore 우라늄 대여 계약은 2025년 8월 상환·종료됐습니다.'),
    'wwc-uranium': profile('WWC Engineering', AIF['URG'],
        'Ur-Energy와 enCore 우라늄 프로젝트의 기술·자원 평가 보고서를 작성한 엔지니어링 기업입니다.',
        'Lost Creek·Shirley Basin·Texas·Gas Hills의 확인된 기술 평가 역할을 표시합니다. 공장 EPC·장비 공급·정광 구매를 추정하지 않습니다.'),
    'verdera-encore': profile('Verdera Energy', EU_Q2,
        'enCore의 Crownpoint·Hosta Butte 권리 매각 상대입니다. 거래 조건 충족 후 해당 자산과 주식 대가가 반영됐습니다.',
        '광산 자산 매각·주식 투자 관계입니다. enCore의 정광 판매 고객이나 현재 연결 자회사로 표시하지 않습니다.'),
    'tenex-centrus': profile('TENEX', AIF['LEU'],
        'Centrus가 저농축 우라늄 판매에 이용하는 러시아산 SWU 공급 계약 상대입니다.',
        '계약은 2028년까지의 기간과 수입 제한·DOE 면제 등 조건을 갖습니다. 계약 잔량을 무조건 인도 가능한 현재 공급으로 표시하지 않습니다.'),
    'orano-centrus': profile('Orano · 농축 공급', AIF['LEU'],
        'Centrus에 농축 서비스 SWU를 공급하는 계약 상대입니다.',
        '2023~2030 계약의 농축 공급 역할입니다. 원료 우라늄·SWU·UF₆ 제품의 물량 단위와 가격 조건을 구분합니다.'),
    'aco-centrus': profile('American Centrifuge Operating', AIF['LEU'],
        'Centrus의 농축 기술·Piketon 설비·DOE 계약을 수행하는 자회사입니다.',
        'Fluor Federal Services EPC와 DOE 실증·증설 계약은 단계별 승인·자금·가동 조건에 따라 진행됩니다.'),
    'doe-nuclear-fuel': profile('U.S. Department of Energy · 핵연료 계약', LEU_DOE,
        'Centrus의 HALEU 실증 및 2026년 상업 농축 능력 개발 계약을 체결한 미국 정부 부처입니다.',
        '기업이 아닌 계약 기관입니다. 개발 자금·실증 인도·미래 설비 목표를 같은 항목으로 합산하지 않습니다.'),
    'x-energy-haleu': profile('X-energy', LEU_XENERGY,
        'Xe-100 원자로·TRISO-X 연료 사업에 필요한 LEU·HALEU를 Centrus와 장기 공급 계약으로 연결합니다.',
        '2026년 8월 실제 체결 계약이며 미래 공급·선수금이 포함됩니다. X-energy의 발전소 도입 고객을 Centrus 직접 고객으로 확대하지 않습니다.'),
    'radiant-kaleidos': profile('Radiant · Kaleidos', LEU_RADIANT,
        'Kaleidos 이동형 소형 원자로에 필요한 미국산 HALEU 공급을 Centrus와 계약했습니다.',
        '2026-09-09 장기 공급 계약입니다. 미래 공급·선납 조건이 현재 모든 연료 인도 완료를 뜻하지 않습니다.'),
    'antares-haleu': profile('Antares · 소형 원자로', LEU_ANTARES,
        '소형 원자로용 HALEU를 Centrus에서 공급받는 장기 계약을 체결했습니다.',
        '2026-09-17 계약이며 미래 연료 공급·선수금 조항이 포함됩니다. 아직 발생하지 않은 상업 인도 매출을 생성하지 않습니다.'),
    'inl-lightbridge': profile('Idaho National Laboratory · Lightbridge 시험', AIF['LTBR'],
        'Lightbridge의 핵연료 시편을 Advanced Test Reactor에서 조사·분석하는 연구시설입니다.',
        'Battelle Energy Alliance와의 CRADA 연구 협력 범위입니다. 원전 상업 연료 구매자로 표시하지 않습니다.'),
    'raten-icn': profile('RATEN ICN', AIF['LTBR'],
        'Lightbridge와 CANDU 연료 적용 가능성을 연구한 루마니아 원자력 연구기관입니다.',
        '완료된 1단계 연구와 추가 시험 계획은 상업 원전 연료 인도·매출과 다릅니다.'),
    'vulcan-elements': profile('Vulcan Elements', AIF['UUUU'],
        'Energy Fuels 희토류 산화물을 영구자석 제조에 검증하는 협력 상대입니다.',
        '2025-08-26 MOU는 샘플 검증과 향후 장기 공급 협상 의향입니다. 이미 체결한 대량 공급 계약으로 표시하지 않습니다.'),
    'base-resources': profile('Base Resources', AIF['UUUU'],
        'Energy Fuels가 2024년 인수한 광물사·Madagascar 개발 자산 회사입니다.',
        'Kwale 채굴은 2024년 말 종료 후 복구 단계이며 Vara Mada는 개발 프로젝트입니다. 잔여 재고 판매와 새 광산 가동을 구분합니다.'),
    'astron-donald': profile('Astron · Donald', AIF['UUUU'],
        'Australia Donald의 희토류·광물사 개발 공동사업 상대입니다.',
        '2025년 말 Energy Fuels 9.48%·Astron 90.52%이며 후속 투자 시 최대 49% 참여권은 현재 지분이 아닙니다.'),
    'asm-energy-fuels': profile('Australian Strategic Materials', UUUU_ASM,
        '2026-08-28 Energy Fuels 인수가 완료된 희토류 금속·합금 기업입니다. 한국 Ochang 가동 설비와 Australia Dubbo 개발 자산을 연결합니다.',
        '기존 NdFeB 합금 능력 1,300 t/년, 확대 목표 3,600 t/년은 시점이 다릅니다. 미국 신규 금속 공장 계획은 현재 가동 설비가 아닙니다.'),
    'vac-energy-fuels': profile('Vacuumschmelze · VAC', UUUU_VAC,
        'Energy Fuels가 인수 계약을 체결한 희토류 영구자석·자성 소재 기업입니다.',
        '2026-06-23 계약은 규제·자금 등 완료 조건을 갖습니다. 현재 Energy Fuels 연결 자회사나 즉시 발생한 인수 후 매출로 표시하지 않습니다.'),
}

EDGES = {
    'CCJ': [relation('Orano Canada', None, 'supplier', 'Cigar Lake 광석을 McClean Lake에서 처리하는 실제 처리 서비스 · 현재 광산 공동 소유와 별도', AIF['CCJ'], 'orano-canada'),
        relation('Kazatomprom · Inkai', None, 'supplier', 'Inkai 운영·우라늄 구매 · 60/40 공동사업 전체 실적을 Cameco 연결 매출에 합산하지 않음', AIF['CCJ'], 'kazatomprom-inkai'),
        relation('Westinghouse Electric Company', None, 'customer', '2026 Q2 주석 19의 실제 연료 판매·보관·취급 거래 · 투자 지분과 별도', CCJ_WESTINGHOUSE, 'westinghouse-electric'),
        relation('Energoatom', None, 'customer', '2023년 실제 체결된 우크라이나 원전 연료 공급 계약 · 2035년까지의 약정과 실제 인도 구분', ENERGOATOM, 'energoatom-ukraine'),
        relation('SILEX Systems · GLE', None, 'partner', 'GLE 레이저 농축 기술 라이선스·개발 공동사업 · 현재 상업 농축 판매가 아님', AIF['CCJ'], 'silex-gle')],
    'DNN': [relation('Orano Canada', None, 'partner', 'McClean Lake 운영·처리 공동사업 · Denison 지분 22.5%와 전체 물량을 구분', AIF['DNN'], 'orano-canada'),
        relation('Cameco', 'CCJ', 'customer', 'Cigar Lake 광석의 McClean Lake 처리 경로 · 직접 Denison 정광 구매 계약과 구분', AIF['DNN']),
        relation('Uranium Energy', 'UEC', 'partner', 'UEC 계열 UEX와 JCU 각각 50% · Wheeler 직접 지분과 간접 권리 구분', AIF['DNN']),
        relation('Wood Canada', None, 'supplier', 'Phoenix 설계·조달·건설 관리 · 2026 실제 CM 계약, 모든 장비 단독 EPC 공급을 뜻하지 않음', AIF['DNN'], 'wood-canada'),
        relation('SaskPower', None, 'supplier', 'Phoenix 138 kV 계통 전력 연결 완료 · 2026-01-08', DNN_POWER, 'saskpower-phoenix'),
        relation('Ecora Resources', None, 'partner', '2017년 McClean 처리 수입 일부 이전 계약 · 정광 구매자가 아닌 금융·스트림 상대', AIF['DNN'], 'ecora-mcclean')],
    'NXE': [relation('Stantec', None, 'supplier', '2021 Rook I 타당성 조사 참여 · 과거 기술 평가, 2026 EPC 수주로 확대하지 않음', AIF['NXE'], 'stantec-rook'),
        relation('Wood Canada', None, 'supplier', '2021 Rook I 타당성 조사 참여 · 현재 공사 계약으로 확대하지 않음', AIF['NXE'], 'wood-canada'),
        relation('Roscoe Postle Associates', None, 'supplier', '2021 Rook I 기술·자원 평가 보고서 참여 · 당시 기업 이름 보존', AIF['NXE'], 'rpa-rook'),
        relation('Saskatchewan Research Council', None, 'supplier', '2026 PCE 탐사 시료 Geoanalytical Laboratory 시험·분석 · 광석 구매자가 아님', NXE_SRC, 'src-geoanalytical')],
    'UEC': [relation('Cameco', 'CCJ', 'supplier', '캐나다 시설의 매입 우라늄 보관 서비스 · 자체 채굴·정광 구매자와 구분', AIF['UEC']),
        relation('ConverDyn · Metropolis Works', None, 'supplier', '미국 시설의 매입 우라늄 보관 · 현재 Solstice·General Atomics 참여', AIF['UEC'], 'converdyn-metropolis'),
        relation('Fluor', None, 'supplier', 'UR&C 정련·전환 개발 엔지니어링 · 아직 상업 전환 가동을 뜻하지 않음', AIF['UEC'], 'fluor-lngcanada'),
        relation('UEX · JCU', None, 'subsidiary', 'UEX 계열·JCU 50% · UEX 관리와 공동 프로젝트 권리를 구분', AIF['UEC'], 'uex-jcu'),
        relation('Denison Mines', 'DNN', 'partner', 'JCU 50/50 공동사업 상대 · 광산 직접 지분과 간접 권리 구분', AIF['UEC'])],
    'EU': [relation('Boss Energy', None, 'partner', 'Alta Mesa 30% 참여 · enCore 70% 지배·관리, 별도 우라늄 대여는 2025년 종료', EU_Q2, 'boss-alta-mesa'),
        relation('WWC Engineering', None, 'supplier', 'Texas·Gas Hills S-K1300 기술 평가 보고서 · 장비·EPC 공급과 구분', AIF['EU'], 'wwc-uranium'),
        relation('Verdera Energy', None, 'transaction', 'Crownpoint·Hosta Butte 권리 매각 · 2026년 2월 조건 충족 후 자산 제거·주식 대가 반영', EU_Q2, 'verdera-encore')],
    'URG': [relation('WWC Engineering', None, 'supplier', 'Lost Creek·Shirley Basin 기술·자원 평가 · 정광 구매자·공장 EPC가 아님', AIF['URG'], 'wwc-uranium')],
    'LEU': [relation('TENEX', None, 'supplier', '2028년까지 SWU 계약 · 러시아산 수입 제한·DOE 면제·인도 조건', AIF['LEU'], 'tenex-centrus'),
        relation('Orano · 농축 공급', None, 'supplier', '2023~2030 SWU 공급 계약 · 우라늄 원료·농축 작업 단위 구분', AIF['LEU'], 'orano-centrus'),
        relation('Fluor', None, 'supplier', '2026-02-09 ACO의 Fluor Federal Services EPC · 승인 자금·단계별 범위, 공장 완료를 뜻하지 않음', AIF['LEU'], 'fluor-lngcanada'),
        relation('American Centrifuge Operating', None, 'subsidiary', 'Piketon 농축·DOE·EPC 계약 수행 · Centrus 연결 자회사', AIF['LEU'], 'aco-centrus'),
        relation('U.S. Department of Energy', None, 'customer', 'HALEU 실증·2026 개발 계약 · 기관 계약과 미래 상업 능력 구분', LEU_DOE, 'doe-nuclear-fuel'),
        relation('X-energy', None, 'customer', '2026년 8월 실제 LEU·HALEU 공급 계약 · 미래 인도·선납, 직접 고객 범위', LEU_XENERGY, 'x-energy-haleu'),
        relation('Radiant', None, 'customer', '2026-09-09 Kaleidos HALEU 장기 공급 계약 · 미래 인도·선납', LEU_RADIANT, 'radiant-kaleidos'),
        relation('Antares', None, 'customer', '2026-09-17 HALEU 장기 공급 계약 · 미래 인도·선납', LEU_ANTARES, 'antares-haleu')],
    'LTBR': [relation('Idaho National Laboratory', None, 'partner', 'Battelle Energy Alliance CRADA · ATR 시편 조사·후속 검사, 상업 연료 구매가 아님', AIF['LTBR'], 'inl-lightbridge'),
        relation('RATEN ICN', None, 'partner', 'CANDU 적용 1단계 연구 완료·후속 연구 검토 · 상업 연료 인도 계약이 아님', AIF['LTBR'], 'raten-icn'),
        relation('Centrus Energy', 'LEU', 'supplier', '2024년 완료된 FEED 엔지니어링 연구 · 현재 장기 연료 구매 계약이 아님', AIF['LTBR'])],
    'UUUU': [relation('Chemours', 'CC', 'supplier', 'Florida·Georgia 모나자이트 원료 공급 · 희토류 분리 투입 원료', AIF['UUUU']),
        relation('POSCO International', '047050.KS', 'customer', '2025 NdPr 1.7 t 검증용 샘플 · 80,000 USD 시운전 자산 원가 차감, 연결 매출 추가 금지', AIF['UUUU']),
        relation('Vulcan Elements', None, 'partner', '2025-08-26 MOU · 샘플 검증·미래 장기 계약 협상 의향, 대량 공급 계약 체결과 구분', AIF['UUUU'], 'vulcan-elements'),
        relation('Base Resources', None, 'subsidiary', '2024-10-02 인수 완료 · Kwale 복구·Vara Mada 개발·광물사 재고 범위', AIF['UUUU'], 'base-resources'),
        relation('Astron · Donald', None, 'partner', '2025년 말 실제 9.48% 참여 · 미래 투자로 최대 49% 권리, 상업 광산 가동이 아님', AIF['UUUU'], 'astron-donald'),
        relation('Australian Strategic Materials', None, 'subsidiary', '2026-08-28 실제 인수 완료 · 한국 가동 금속·합금·Dubbo 개발, 증설 목표 구분', UUUU_ASM, 'asm-energy-fuels'),
        relation('Vacuumschmelze · VAC', None, 'transaction', '2026-06-23 인수 계약 · 별도 승인·완료 조건, 현재 연결 자회사로 표시하지 않음', UUUU_VAC, 'vac-energy-fuels')],
}

# Fluor has an existing canonical counterpart shared with LNG Canada. Add the
# two reviewed nuclear roles without deleting that source or creating an alias.
COMMON_CONTEXT = {
    'fluor-lngcanada': {
        'brief': [fact('UEC · 정련·전환 엔지니어링',
            'UEC UR&C는 개발 엔지니어링 역할입니다. 인허가·개발 단계를 이미 완성된 상업 전환 공장으로 표시하지 않습니다.', AIF['UEC']),
            fact('Centrus · ACO EPC',
            '2026-02-09 Fluor Federal Services의 농축 설비 EPC 계약입니다. 승인된 자금·단계별 설계·조달·건설 범위이며 상업 공장 완료를 뜻하지 않습니다.', AIF['LEU'])],
        'sources': [AIF['UEC'], AIF['LEU']],
    },
}

# Revenue-stage evidence is the audited statement, rather than the business AIF.
PUBLIC['NXE']['brief'][1]['source'] = source('NexGen · 2025 감사 재무제표 · 주석 2', 'https://www.sec.gov/Archives/edgar/data/1698535/000119312526089376/d84755dex993.htm', '2026-03-04')
