"""Dated offshore drilling, vessel, aviation and well-service reading notes.

Current combinations are distinct from historical annual issuer scopes. Owned,
chartered, managed and JV assets are not an interchangeable fleet count.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('NE', 'RIG', 'SDRL', 'VAL', 'TDW', 'SMHI', 'VTOL', 'HOS', 'XPRO')
ANNUAL = {s: report(s) for s in SYMBOLS}
QUARTER = {s: report(s, 'quarter') for s in SYMBOLS}
RIG_VAL = source('Transocean · Valaris 조건부 인수 계약',
    'https://investor.deepwater.com/news-releases/news-release-details/transocean-acquire-valaris/', '2026-02-09')
RIG_SEPT = source('Transocean · 실제 수주·여전히 proposed 결합',
    'https://investor.deepwater.com/news-releases/news-release-details/transocean-ltd-announces-80-million-contract-ultra-deepwater', '2026-09-15')
HOS_CLOSE = source('Hornbeck · 실제 결합 완료·법인 승계',
    'https://www.sec.gov/Archives/edgar/data/866829/000119312526378529/d102206d8k.htm', '2026-09-01')
HOS_COMBINED = source('Hornbeck · 결합 후 pro forma 사업·자산',
    'https://www.sec.gov/Archives/edgar/data/866829/000119312526380897/d138666dex991.htm', '2026-09-03')
HOS_DECOM = source('Hornbeck · Helix Well Ops North Sea 수주',
    'https://hornbeckoffshore.gcs-web.com/news-releases/news-release-details/hornbeck-offshore-awarded-multi-year-decommissioning-contract', '2026-09-14')
XPRO_CLOSE = source('Expro · Enhanced Drilling 실제 취득 완료',
    'https://www.expro.com/media-hub/news/expro-announces-second-quarter-2026-results', '2026-07-28')

PUBLIC = {
    'NE': profile('Noble Corporation', ANNUAL['NE'],
        '생산자의 해양 유정을 drillship·semi-submersible·jackup과 작업팀으로 시추하는 계약 시추 회사입니다. 원유 생산 지분 매출과 리그 작업 dayrate는 다른 사업입니다.',
        '2025 계약 매출 3,285,568,000 USD입니다. floater 2,567,698,000·jackup 539,509,000·기타 178,361,000이며 시추 소계 3,107,207,000을 다시 더하지 않습니다.',
        [('Floaters', '심해 drillship·semi-submersible의 시추 장비·인력·위치 유지·유정 제어를 제공합니다.'),
         ('Jackups', '다리를 해저에 고정하는 천해·일부 가혹 환경 리그입니다. 수심·환경·유정 깊이에 따라 장비가 다릅니다.'),
         ('Dayrate', '정상 작업일의 일일 대가이며 수리·중단·기상 때 낮은 대가 또는 무대가 조건이 있을 수 있습니다.'),
         ('자산 기준일', '2025년말 36기(25 floaters·11 jackups)와 연차 작성일 31기(25·6)를 구분합니다. 과거 자산 수를 현재 fleet로 고정하지 않습니다.'),
         ('고객별 조건', 'Exxon·AkerBP·Petrobras 일부 계약의 단가 조정과 Shell·TotalEnergies 성과 조건은 계약별로 다릅니다.'),
         ('취소·backlog', '서명 계약의 미래 작업 대가이며 취소·가동·가격 조정 조건 때문에 실현 매출·현금과 다릅니다.'),
         ('장비·인력', '유정 제어·시추·해양 정비·숙련 crew와 지역별 작업 승인이 수행 기반입니다.')],
        customers='2025 ExxonMobil 19.7%·BP 13.2%·Petrobras 12.5%입니다. Shell 12.3%는 2024, TotalEnergies 10.5%는 2023이며 현재 비율로 표시하지 않습니다.',
        inputs='리그·BOP·시추/위치 유지·정비 부품·연료·물류·인력과 조선소 작업이 필요합니다. 공개하지 않은 OEM 이름은 추정하지 않습니다.',
        competition='심해·천해·가혹 환경 계약별 능력·가용 일정·안전·단가로 시추사와 경쟁합니다.'),
    'RIG': profile('Transocean', ANNUAL['RIG'],
        '심해·초심해와 가혹 환경의 부유식 해양 리그를 운영해 생산자에게 계약 시추를 제공합니다. 고객 유정의 원유를 자기 상품으로 판매하는 구조가 아닙니다.',
        '2025 매출 3,965,000,000 USD이며 초심해 2,777,000,000·가혹 환경 1,188,000,000입니다. 지역별 표와 제품×지역 교차표를 중복 합산하지 않습니다.',
        [('초심해', '심해 drillship·semi-submersible의 시추·위치 유지·대형 유정 건설 작업입니다.'),
         ('가혹 환경', '주로 거친 해상·기상 조건에 맞춘 floater 시추입니다. 천해 jackup과 같은 자산이 아닙니다.'),
         ('장비 능력', 'dual activity·고용량 hoisting 등 장비 사양과 계약 가동일·수익성을 구분합니다.'),
         ('계약·가동', 'dayrate·동원/철수·장비 정비·종료 조건을 확인하며 계약 전액을 이미 받은 현금으로 표시하지 않습니다.'),
         ('고객 집중', '2025 Petrobras 22%·Shell 22%·Equinor 12%입니다. 2026 backlog 고객 비율은 다른 분모입니다.'),
         ('부분 소유·리스', '소유·부분 소유·운영 자산을 구분하며 Petrobras 10000의 금융리스 구조를 단순 완전 소유로 바꾸지 않습니다.'),
         ('Valaris 계획', '2월9일 결합 계약과 9월15일 proposed 표현을 확인했습니다. 조건부 결합을 현재 모회사·완료 자산 합계로 표시하지 않습니다.')],
        customers='대형·국영·독립 생산자이며 원문 실명 매출 집중도를 사용합니다. 9월15일 신규 고객은 익명으로 유지합니다.',
        inputs='리그·BOP·해양 정비·연료·부품·crew·조선소·물류가 필요하며 기상·정비로 가동 대가가 달라집니다.',
        competition='초심해·가혹 환경 시추 계약과 가용 fleet를 비교합니다. 제안된 결합 fleet와 현재 회사 fleet는 다릅니다.'),
    'SDRL': profile('Seadrill', ANNUAL['SDRL'],
        '자체 해양 리그 시추와 Sonadrill 관련 리그 관리 서비스를 제공합니다. 합작 사업과 Sonangol 소유 리그를 자체 소유 자산으로 합산하지 않습니다.',
        '2025 연결 매출 1,437,000,000 USD입니다. Brazil 611,000,000·미국 368,000,000·Angola 331,000,000·Norway 97,000,000·기타 30,000,000입니다.',
        [('심해 시추', 'drillship·semi-submersible의 dayrate 작업이며 benign·harsh 환경과 계약 상태를 구분합니다.'),
         ('2025 소유 상태', '15기 소유 중 10기 가동·1기 upgrade·1기 수리·3기 cold stacked입니다. 전부 가동 fleet가 아닙니다.'),
         ('Sonangol 관리', '별도로 Sonangol 소유 2기를 관리합니다. 자체 소유 15기에 더해 소유 17기라고 표시하지 않습니다.'),
         ('Sonadrill', 'Seadrill·Sonangol 각 50% JV입니다. 2025 Libongos·Quenguela를 Sonangol에서, West Gemini를 Seadrill에서 용선하고 Seadrill이 3기를 관리합니다.'),
         ('관리·임대·추가 서비스', '관련자 관리료·리스·추가 작업·비용 환급은 시추 dayrate와 다른 계약 경로입니다.'),
         ('지분법 매출', 'Sonadrill 전체 매출 382,000,000 USD를 Seadrill 연결 매출에 추가하지 않습니다.'),
         ('고객·기간', '2025 Petrobras 36%·Sonadrill 22%·Talos 11%·LLOG 10%이며 현재 새 계약 단가·물량이 아닙니다.')],
        customers='국제·국영·독립 생산자와 관련 관리 JV가 고객입니다. Sonadrill은 단순 최종 원유 구매자와 다른 역할입니다.',
        inputs='crew·리그/BOP 정비·부품·연료·조선소 작업과 고객/지역 작업 허가가 필요합니다.',
        competition='심해 계약·리그 가용·작업 신뢰성을 비교하며 JV·관리 fleet와 소유 fleet의 회계 범위를 구분합니다.'),
    'VAL': profile('Valaris', ANNUAL['VAL'],
        'floaters·jackups로 국제 해양 계약 시추를 제공하며 Saudi Aramco와 ARO 지분법 공동사업을 보유합니다. Transocean과는 조건부 결합 계약 상태입니다.',
        '2025 연결 매출 2,369,000,000 USD입니다. floaters 1,260,600,000·jackups 912,800,000·기타 195,600,000이며 ARO 전체 571,000,000을 연결 총액에 더하지 않습니다.',
        [('Floaters', '심해 drillship·semi-submersible 계약과 고객 요구에 따른 장비·crew·동원을 제공합니다.'),
         ('Jackups', '천해 리그를 운영하며 지역·고객별 단가·작업 조건이 다릅니다.'),
         ('ARO JV', 'Saudi Aramco와 각 50%의 비연결 공동사업입니다. 전체 JV 매출과 Valaris의 지분법 손익을 구분합니다.'),
         ('자산 기준일', '2026-02-20 46기 소유(13 drillship·2 semi-submersible·31 jackup)와 ARO 추가 9기를 구분합니다. 현재 가동 수라는 뜻은 아닙니다.'),
         ('환급 대가', '사업부 매출은 비용 환급을 포함합니다. 환급 제외 subtotal을 다시 더하지 않습니다.'),
         ('고객 집중', '2025 상위 5개 49%·Petrobras/BP/Azule 합산 35%입니다. 합산 비율을 3사에 임의 배분하지 않습니다.'),
         ('조건부 결합', 'Valaris 주식당 RIG 15.235주 교환 계획과 주주/규제 승인·종결 조건입니다. 완료 전 지분·시너지·fleet를 현재 실적으로 표시하지 않습니다.')],
        customers='대형 국제·국영·독립 생산자입니다. 실명 상위 고객과 아직 실행되지 않은 미래 작업 backlog는 다릅니다.',
        inputs='해양 리그·crew·장비 정비·연료·조선소·물류·보험과 현장 요건이 필요합니다.',
        competition='심해·천해 리그 계약별로 비교합니다. 제안된 인수 관계와 현재 독립 계약 경쟁 범위를 구분합니다.'),
    'TDW': profile('Tidewater', ANNUAL['TDW'],
        '해양 생산·시추·개발·폐쇄와 일부 풍력 작업에 선박·물류 지원을 제공합니다. 원유 tanker 운송이나 유정 시추 리그 자체 운영과 다른 OSV 사업입니다.',
        '2025 선박 매출 1,338,931,000 USD·기타 13,855,000, 합계 1,352,786,000입니다. 지역별 표는 같은 연결 매출의 다른 보기입니다.',
        [('PSV', '유전 현장에 장비·화물·소모품을 공급합니다. 2025년말 PSV 139척 중 중형 69·대형 70척이며 deck 면적 사양을 사용합니다.'),
         ('AHTS', '리그 견인·anchor handling 등 해양 작업을 지원합니다. PSV와 역할·계약 단위가 다릅니다.'),
         ('현장 수송', '인력·장비·보급품·workover·생산 유지·폐쇄/복구 현장을 지원합니다.'),
         ('특수·풍력 지원', '해양 건설·seismic·subsea·pipe/cable laying·지반 survey 등 특수 작업 지원입니다.'),
         ('전체 선박 기준', '2025년말 30개국 이상·208척 serving fleet입니다. PSV 139척을 다시 더하지 않습니다.'),
         ('지역 운영', '5개 지역 보고 부문이며 선박은 프로젝트 종료·새 계약에 따라 이동합니다. 지역 매출과 회사 국적은 다릅니다.'),
         ('고객·계약', '2025 상위 5개 29.8%·10개 47.9%입니다. 해당 집중도 표만으로 익명 고객 이름을 추정하지 않습니다.')],
        customers='생산자·해양 시공/서비스·풍력 사업자가 사용하며 계약별 취소·가동·대가 조건을 확인합니다.',
        inputs='선박·승무원·정비·연료·부품·항만·지역 인허가와 일부 현지 공동사업이 필요합니다.',
        competition='OSV의 deck·동적 위치 유지·출력·안전·지역 가용·단가를 비교하며 tanker tonne-mile 시장과 같은 지표로 보지 않습니다.'),
    'SMHI': profile('SEACOR Marine Holdings', ANNUAL['SMHI'],
        'OSV·고속 지원선 등으로 해양 에너지·풍력 현장의 화물·인력·장비·건설·응급 대응을 지원합니다. 소유·용선·관리 선박이 포함됩니다.',
        '2025 time charter 215,381,000 USD·bareboat 3,235,000·기타 9,216,000, 합계 227,832,000입니다. JV의 전체 매출과 제품×지역 표를 추가 합산하지 않습니다.',
        [('Time charter', '선박과 운영을 제공하며 통상 연료 외 운영 비용을 부담합니다. 계약기간 동안 일별 매출을 인식합니다.'),
         ('Bareboat charter', '선박을 제공하고 고객이 운영 비용·운영 위험을 부담합니다. 승무원 포함 time charter와 다릅니다.'),
         ('PSV·고속 지원선', '화물·인력 수송과 해양 작업 지원이며 fast support의 높은 속도·승객/화물 사양은 별도입니다.'),
         ('관리 선박', '비계열 소유자의 선박을 대가를 받고 운용합니다. 관리 수를 소유 fleet라고 표시하지 않습니다.'),
         ('SEACOR Marine Arabia', '45% 참여 JV로 Saudi Aramco에 선박을 제공하는 실제 경로입니다. SMHI와 Aramco의 직접 계약 매출 전체로 바꾸지 않습니다.'),
         ('실명 고객', '2025 Azule 27%·ExxonMobil 17%·SEACOR Marine Arabia 14%, 상위 10개 84%입니다.'),
         ('건조 일정', '2025년말 Fujian Mawei DP-2 PSV 2척 건조 중·2026 Q4/2027 Q1 예정입니다. 연차의 예정 인도를 완료 선박으로 표시하지 않습니다.')],
        customers='생산자·해양 시공·풍력 사업자와 JV 용선 경로입니다. 계약은 취소·단기 갱신 조건 때문에 명시 기간 전체의 작업을 보장하지 않습니다.',
        inputs='선박·승무원·정비·연료·항만과 새 선박 조선소가 필요합니다. 소유·lease-in·managed를 원문 기준으로 구분합니다.',
        competition='선종·지역·속도/deck·작업 능력·가용·용선 조건이 비슷한 OSV 사업을 비교합니다.'),
    'VTOL': profile('Bristow Group', ANNUAL['VTOL'],
        '해양 유전 인력/물류 항공 수송과 정부 수색구조 SAR·응급 대응 및 기타 항공 서비스를 제공합니다. 정부 계약과 유전 현장 수송을 분리합니다.',
        '2025 매출 1,490,512,000 USD입니다. Offshore Energy 990,480,000·Government 379,437,000·기타 120,595,000이며 전부 원유 지원 매출로 표시하지 않습니다.',
        [('해양 수송', '헬리콥터로 해양 시설 인력·필요 물자를 수송하며 비행 안전·가용·현장 일정을 관리합니다.'),
         ('정부 SAR', 'UK·Ireland·미국·Netherlands/Dutch Caribbean 정부 항공 응급 대응·수색구조입니다.'),
         ('UKSAR2G', 'DfT/MCA의 10년 프로그램으로 2024 말 전환 시작·2026 말 완료 예상입니다. 헬리콥터·고정익·UAS가 포함됩니다.'),
         ('Ireland', 'Irish Department of Transport의 10년 Coast Guard SAR 계약입니다. 2024 말 시작·마지막 base는 2026 초 가동했습니다.'),
         ('BSEE', '미국 Gulf 해양 시설을 검사하는 정부 기관에 수송 서비스를 제공합니다.'),
         ('제조·정비 공급', '공시는 Sikorsky Commercial·Leonardo·Nova Systems·General Electric Aviation의 부품/overhaul 의존을 실명으로 명시합니다.'),
         ('부품·fleet 제약', '2025 S92 약 29% fleet이며 부품 지연으로 대체 조달·일부 기체 ground가 발생했습니다. 보유 기체 모두가 가동이라는 뜻은 아닙니다.')],
        customers='생산자와 정부 기관이며 2025 UK SAR 계약은 전사 매출 약 19%입니다. 정부 부문 전체 379,437,000과 같은 범위가 아닙니다.',
        inputs='항공기·승무원·정비·OEM 부품·연료·기지·훈련·항공 인허가가 필요합니다. 리스와 소유·부품 공급과 모회사 지분은 다릅니다.',
        competition='해양 비행·정부 SAR별 안전·가용·기종·기지·장기 계약 조건을 비교하며 OSV와 서비스 단위가 다릅니다.'),
    'HOS': profile('Hornbeck Offshore Services', HOS_CLOSE,
        '2026-09-01 Helix·옛 Hornbeck 결합을 완료한 해양 수송·해저 작업·유정 개입 회사입니다. 기존 Helix 발행 법인이 Delaware로 전환·Hornbeck 이름과 HOS 종목을 사용합니다.',
        '아래 2025 연차 매출 1,291,474,000 USD는 결합 전 Helix만 포함합니다. 결합 후 pro forma LTM·수주·선박 능력을 2025 연결 매출에 더하지 않습니다.',
        [('해양 수송·특수 지원', '옛 Hornbeck의 OSV·MPSV 현장 물류·해양 건설/방산 지원과 Helix 기술 서비스를 연결합니다.'),
         ('Well Intervention', 'riser 기반·riserless 장비와 선박으로 기존 유정 생산 개선·폐쇄를 수행합니다.'),
         ('Robotics·Subsea', 'ROV·trenching·survey·설치·IMR·풍력 케이블 매설과 해저 정비/폐쇄 지원입니다.'),
         ('2025 Shallow Water·Facilities', '결합 전 Helix의 천해 폐쇄·회수와 HP I 생산시설 업무입니다. 결합 후 새 부문과 같은 연간 범위로 표시하지 않습니다.'),
         ('소유·용선·예정 자산', '현재 pro forma 자료의 85척은 5척 용선과 2027/2028 예정 신조 MPSV 등 범위 설명을 포함합니다. 전부 현재 소유·가동 85척으로 바꾸지 않습니다.'),
         ('Sea1 Offshore 용선', '브라질 Sea Helix 1·Siem Helix 2는 Sea1의 장기 용선이며 Petrobras 계약·자체 소유 선박과 구분합니다.'),
         ('이전 실명 고객', '2025 Helix Shell 18%·Petrobras 10%입니다. 결합 후 Hornbeck 전체 고객 집중도라고 표시하지 않습니다.')],
        customers='생산자·해양 시공·풍력·방산 고객이며 결합 전 Helix와 결합 후 회사의 기간·범위를 구분합니다.',
        inputs='선박·용선·ROV·유정 접근/압력 장비·잠수·crew·프로젝트 설계·정비와 지역 작업 허가가 필요합니다.',
        competition='해양 수송·유정 개입·해저 작업별 비교이며 결합 전 단일 사업의 매출과 결합 후 pro forma를 같은 시계열로 놓지 않습니다.'),
    'XPRO': profile('Expro', ANNUAL['XPRO'],
        '유정 건설·유체 관리·해저 유정 접근·개입/건전성 기술을 제공하는 서비스 회사입니다. 2025 연차는 이전 Expro Group Holdings N.V.의 실제 사업·실적입니다.',
        '2025 매출 1,607,095,000 USD이며 Well Construction 548,642,000·Well Management 1,058,453,000입니다. 4개 지역 보고 부문은 같은 매출의 다른 보기입니다.',
        [('Well Construction', '관 취급·tubular·시멘팅·시추·wellbore cleanup과 circulation/pipe recovery 도구입니다.'),
         ('Well Flow Management', '유정 유체 시험·계측·관리와 생산 수행을 지원합니다.'),
         ('Subsea Well Access', '심해 유정 접근·제어 장비와 운영 서비스를 제공하며 직접 원유 판매와 다릅니다.'),
         ('Intervention·Integrity', '유정 개입·회수·정비·건전성 기술로 생산 수명과 폐쇄를 지원합니다.'),
         ('4개 보고 지역', 'NLA 558,033,000·ESSA 486,900,000·MENA 363,616,000·APAC 198,546,000 USD입니다. 제품 표와 더하지 않습니다.'),
         ('Coretrax', '2024 CTL UK Holdco 지분을 취득해 유정 성능·개입 기술을 편입했습니다. 과거 인수 대가와 당기 매출은 다릅니다.'),
         ('법인 이전', '2026-07-13 Luxembourg를 거쳐 Cayman Expro Ltd로 이전·주식 1:1 전환, 7월14일 XPRO 거래입니다. 이전 NV 연차를 현재 Ltd 자체 연차로 바꾸지 않습니다.')],
        customers='생산자·탐사개발 고객이며 2025 개별 고객 10% 초과는 없습니다. 과거 2024 10.5%·2023 12.5% 고객을 현재 실명 고객으로 추정하지 않습니다.',
        inputs='주조·단조·OEM/강관 제조사의 부품·장비·원재료·전문 현장 인력이 필요합니다. 일부 장비의 제한된 공급원 이름은 공개하지 않았습니다.',
        competition='유정 건설·관리·해저 접근·개입 기술·안전·현장 수행·가용·비용으로 비교합니다.'),
}

LATEST = {
    'NE': ('최근 분기', '2026 Q2 공시와 7월27일 fleet 보고 기간을 구분합니다. 과거 연차의 2025년말/작성일 자산 수는 실시간 가동 수가 아닙니다.', QUARTER['NE']),
    'RIG': ('9월 실제 수주·결합 상태', 'Deepwater Conqueror의 익명 Equatorial Guinea 운영사 2개 유정·약 170일·2027 시작 예상, 약 80,000,000 USD backlog입니다. 추가 서비스·동원/철수 대가는 제외. 27기(초심해20·가혹7)이며 Valaris 결합은 여전히 proposed입니다.', RIG_SEPT),
    'SDRL': ('최근 분기', '2026 Q2 원문의 소유·관리·관련자 거래·JV 범위를 확인합니다. 2025년말 cold-stacked·upgrade·가동 상태를 최신 fleet로 고정하지 않습니다.', QUARTER['SDRL']),
    'VAL': ('조건부 결합·현재 범위', '9월15일 Transocean 원문에서도 proposed 결합입니다. 주식 교환 비율·2026 H2 예상·주주/규제 조건을 이미 완료된 인수로 표시하지 않습니다.', RIG_SEPT),
    'TDW': ('최근 분기', '2026 Q2 보고 기간의 가동/지역 매출과 2025 연차 fleet·매출 표를 분리합니다. 지역 이동·선박 정비·고객 취소 조건이 실제 수행에 영향을 줍니다.', QUARTER['TDW']),
    'SMHI': ('최근 분기', '2026 Q2 범위와 연차의 신조 인도 예상 시점을 분리합니다. JV 현장 고객과 회사의 직접 매출 상대를 구분합니다.', QUARTER['SMHI']),
    'VTOL': ('최근 분기', '2026 Q2 보고 범위와 정부 SAR·해양 수송·기타 서비스를 구분합니다. OEM 부품 지연·기체 가동과 계약 전환 완료 여부는 별도 확인 지표입니다.', QUARTER['VTOL']),
    'HOS': ('9월 North Sea 실제 수주', 'Helix Well Ops (U.K.)가 익명 주요 운영사의 riserless plug & abandonment 계약을 수주했습니다. 2027 Q2 시작 예상·확정 2년+옵션이며 Well Enhancer 또는 Seawell·well access·ROV·잠수·설계를 묶습니다.', HOS_DECOM),
    'XPRO': ('Enhanced Drilling 실제 취득', '2026-07-23 Enhanced Drilling 취득을 완료했습니다. 7월28일 실적 발표로 완료를 확인하며 2025 연차·2026 Q2 말 실적에 7월 취득 후 매출을 추가하지 않습니다.', XPRO_CLOSE),
}
for _symbol, _value in PUBLIC.items():
    _title, _detail, _origin = LATEST[_symbol]
    _value['brief'].append(fact(_title, _detail, _origin))
    _value['sources'].extend([ANNUAL[_symbol], QUARTER[_symbol], _origin])
    _value['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    _value['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    _value['segments'] = [fact(r['title'], r['detail'], r['source']) for r in _value['products'][:3]]
    _value['drivers'] = [fact('가동·수요·계약', _value['brief'][0]['detail'], _value['description_source']),
                         fact('투입·정비·인력', _value['brief'][3]['detail'], ANNUAL[_symbol])]
    _value['financial_context'] = [fact('연간 실적·자산·현금',
        '표에 표시한 2025 USD 연차 범위입니다. 제품·지역·사업부를 서로 더하지 않습니다. backlog·고객 비중·자산 수·JV 전체 매출을 연결 당기 매출·현금으로 바꾸지 않습니다.', ANNUAL[_symbol])]

# Historical Helix claims use their own filing, not the later merger source.
for _index in (1, 3):
    PUBLIC['HOS']['brief'][_index]['source'] = ANNUAL['HOS']
for _index in (0, 1, 2):
    PUBLIC['HOS']['products'][_index]['source'] = HOS_COMBINED
for _index in (3, 5, 6):
    PUBLIC['HOS']['products'][_index]['source'] = ANNUAL['HOS']
PUBLIC['HOS']['products'][4]['source'] = HOS_COMBINED
PUBLIC['HOS']['segments'] = [fact(r['title'], r['detail'], r['source']) for r in PUBLIC['HOS']['products'][:3]]
PUBLIC['HOS']['sources'].extend([HOS_COMBINED, HOS_DECOM])
PUBLIC['HOS']['financial_context'].append(fact('결합 전 Helix 실적',
    '2025 연차·2026 Q2는 기존 Helix이며 9월1일 결합 후 Hornbeck 전체 실적이 아닙니다. pro forma LTM과 실제 연결 보고 기간을 분리합니다.', HOS_CLOSE))
PUBLIC['XPRO']['products'][-1]['source'] = QUARTER['XPRO']
PUBLIC['XPRO']['sources'].append(XPRO_CLOSE)
PUBLIC['RIG']['sources'].append(RIG_VAL)
PUBLIC['VAL']['sources'].append(RIG_VAL)

PRIVATE = {}
EDGES = {s: [] for s in SYMBOLS}
COMMON_CONTEXT = {}
for _key, _name, _symbol, _kind, _origin, _business, _role in [
    ('sonadrill-seadrill', 'Sonadrill', 'SDRL', 'partner', ANNUAL['SDRL'],
     'Seadrill·Sonangol 각 50%의 Angola 해양 시추 공동사업입니다.',
     '2025 3기 용선·Seadrill 관리이며 2기는 Sonangol 소유, West Gemini는 Seadrill 소유입니다. JV 전체 매출을 연결 매출에 더하지 않습니다.'),
    ('sonangol-seadrill', 'Sonangol EP', 'SDRL', 'partner', ANNUAL['SDRL'],
     'Sonadrill의 50% 공동사업 파트너이며 실제 리그 소유·용선 제공자입니다.',
     'Libongos·Quenguela를 Sonadrill에 용선하고 Seadrill이 관리합니다. 자산 소유자·용선 고객·관리업체의 역할이 다릅니다.'),
    ('aro-valaris', 'ARO Drilling', 'VAL', 'partner', ANNUAL['VAL'],
     'Valaris·Saudi Aramco 각 50%의 비연결 해양 시추 공동사업입니다.',
     '2026-02-20 별도 소유 9기는 Valaris 소유 46기와 구분합니다. 2025 전체 매출 571,000,000 USD는 Valaris 연결 당기 매출에 추가하지 않습니다.'),
    ('seacor-marine-arabia', 'SEACOR Marine Arabia LLC', 'SMHI', 'partner', ANNUAL['SMHI'],
     'SEACOR 계열이 45% 참여하는 실제 Saudi Arabia 선박 공동사업입니다.',
     'Saudi Aramco 현장에 선박을 용선하는 경로이며 SMHI의 2025 고객 매출 14%입니다. 45% 소유와 매출 14%는 다른 분모입니다.'),
    ('fujian-mawei-seacor', 'Fujian Mawei Shipbuilding Ltd.', 'SMHI', 'supplier', ANNUAL['SMHI'],
     'SEACOR Marine의 DP-2 PSV 2척 건조 계약 조선소입니다.',
     '2025년말 건조 중·2026 Q4와 2027 Q1 인도 예정입니다. 건조 예정 선박을 당시 가동 fleet로 표시하지 않습니다.'),
    ('uk-dft-bristow', 'UK Department for Transport', 'VTOL', 'customer', ANNUAL['VTOL'],
     'Bristow UK SAR 계약의 정부 고객이며 Maritime and Coastguard Agency 업무를 지원합니다.',
     '2025 UK SAR 전사 매출 약 19%이며 UKSAR2G 10년 프로그램 전환은 2026 말 완료 예상입니다. 기존 계약 취소/대가 조건도 존재합니다.'),
    ('irish-transport-bristow', 'Irish Department of Transport', 'VTOL', 'customer', ANNUAL['VTOL'],
     'Bristow의 Irish Coast Guard SAR 10년 계약 고객입니다.',
     '2024 말 시작·4개 base 중 마지막은 2026 초 가동했습니다. 국가 계약 대가를 원문에 없는 기관별 금액으로 나누지 않습니다.'),
    ('bsee-bristow', 'Bureau of Safety and Environmental Enforcement', 'VTOL', 'customer', ANNUAL['VTOL'],
     '미국 Gulf 해양 시설 검사 기관이며 Bristow의 실제 수송 서비스 고객입니다.',
     '미국 정부 전체·Oceaneering 방산 고객과 구체적 기관을 구분합니다. 기관별 항공 수송 대가는 해당 원문에 없습니다.'),
    ('sikorsky-bristow', 'Sikorsky Commercial Inc.', 'VTOL', 'supplier', ANNUAL['VTOL'],
     'Bristow가 공시한 항공기 부품·overhaul 공급 OEM입니다.',
     'S92 부품 지연으로 대체 부품 조달·일부 기체 ground가 발생했습니다. 공급 의존을 항공기 fleet 소유 지분으로 바꾸지 않습니다.'),
    ('leonardo-bristow', 'Leonardo S.p.A.', 'VTOL', 'supplier', ANNUAL['VTOL'],
     'Bristow가 실명 명시한 항공기 부품·overhaul 공급 OEM입니다.',
     'AW189 등 현장/SAR 기체와 부품·정비 가용이 연결됩니다. 공개하지 않은 구매량·독점·계약 대가는 추정하지 않습니다.'),
    ('nova-systems-bristow', 'Nova Systems International Ltd.', 'VTOL', 'supplier', ANNUAL['VTOL'],
     'Bristow 공시에 명시된 항공기 장착 구성품·정비 관련 공급자입니다.',
     '제한된 공급자 의존을 명시합니다. 모회사 지분·기체 대수·제품별 매출은 이 관계 문서에서 추정하지 않습니다.'),
    ('ge-aviation-bristow', 'General Electric Aviation Inc.', 'VTOL', 'supplier', ANNUAL['VTOL'],
     'Bristow가 공시한 항공기 장착 구성품·overhaul 공급자입니다.',
     '공시에 명시된 실제 법인명을 사용하며 다른 GE 계열과 이름만으로 자동 통합하지 않습니다.'),
    ('sea1-helix', 'Sea1 Offshore', 'HOS', 'supplier', ANNUAL['HOS'],
     '결합 전 Helix 브라질 유정 개입선 2척을 장기 용선하는 선박 제공자입니다.',
     'Sea Helix 1·Siem Helix 2의 용선과 Petrobras 작업 계약이 연결됩니다. 선박 제공자를 최종 시추 고객이나 HOS 소유 자회사로 표시하지 않습니다.'),
    ('helix-well-ops-uk', 'Helix Well Ops (U.K.) Limited', 'HOS', 'subsidiary', HOS_DECOM,
     'Hornbeck의 실제 영국 유정 개입·폐쇄 서비스 자회사입니다.',
     '2026-09 North Sea 익명 운영사의 확정 2년+옵션 계약 수주, 2027 Q2 시작 예상입니다. 고객 이름·미래 작업 완료·현금 수취를 추정하지 않습니다.'),
    ('hercules-hornbeck', 'Hercules Sub LLC · 9월 결합 승계', 'HOS', 'subsidiary', HOS_CLOSE,
     '2026-09-01 옛 Hornbeck 합병의 최종 생존 LLC이며 기존 Helix Delaware의 100% 자회사입니다.',
     'Odyssey Sub의 1차 합병 후 옛 Hornbeck이 이 LLC에 다시 합병했습니다. 상장 HOS 발행기업과 같은 법인 ID로 합치지 않습니다.'),
    ('coretrax-expro', 'CTL UK Holdco Limited · Coretrax', 'XPRO', 'subsidiary', ANNUAL['XPRO'],
     '2024-05-15 Expro Holdings UK 3가 취득한 유정 건설·개입 기술 사업입니다.',
     '효력 기준일 2024-05-01과 closing 5월15일을 구분합니다. 실제 법인명과 Coretrax 제품 브랜드는 이 원문에서 직접 연결됩니다.'),
    ('enhanced-drilling-expro', 'Enhanced Drilling', 'XPRO', 'subsidiary', XPRO_CLOSE,
     'Expro가 2026-07-23 실제 취득한 Enhanced Well Technologies Group AS의 시추 기술 사업이며 노르웨이 MPD 기술을 제공합니다.',
     '7월28일 완료 발표로 현재 사업 범위를 갱신합니다. 2025 이전 법인 연차·2026 Q2 말 재무에 취득 후 매출을 더하지 않습니다.'),
]:
    PRIVATE[_key] = profile(_name, _origin, _business, _role,
        [('확인된 제품·역할', _role)], customers='이 설명은 해당 실제 관계의 역할이며 상대 회사 전체 재무를 추정하지 않습니다.')
    EDGES[_symbol].append(relation(_name, None, _kind, _role, _origin, _key))
    PRIVATE[_key]['relations'].append(relation(PUBLIC[_symbol]['name'], _symbol,
        'parent' if _kind == 'subsidiary' else 'customer' if _kind == 'supplier' else
        'supplier' if _kind == 'customer' else 'partner', _role, _origin))

PRIVATE['sonadrill-seadrill']['relations'].append(relation('Sonangol EP', None, 'owner',
    '실제 50% JV 소유 · 리그 용선·관리 대가와 다른 관계', ANNUAL['SDRL'], 'sonangol-seadrill'))
PRIVATE['aro-valaris']['relations'].append(relation('Saudi Aramco', None, 'owner',
    '실제 50% JV 소유 · 이미 등록된 동일 법인 사용', ANNUAL['VAL'], 'saudi-aramco'))
PRIVATE['seacor-marine-arabia']['relations'].append(relation('Saudi Aramco', None, 'customer',
    '현장에 선박 용선 · SMHI의 직접 매출 상대와 구분', ANNUAL['SMHI'], 'saudi-aramco'))
EDGES['SDRL'].append(relation('Sonadrill', None, 'customer',
    '2025 연결 매출 22% · 관리·리스·추가 서비스·환급 경로이며 JV 소유 50%와 다른 분모',
    ANNUAL['SDRL'], 'sonadrill-seadrill'))
EDGES['SMHI'].append(relation('SEACOR Marine Arabia LLC', None, 'customer',
    '2025 연결 매출 14% · Saudi Aramco 현장으로 연결되는 JV 용선 경로',
    ANNUAL['SMHI'], 'seacor-marine-arabia'))
for _symbol, _customers in {
    'NE': [('XOM', 'ExxonMobil', '2025 매출 19.7%'), ('BP', 'BP', '2025 매출 13.2%'), ('PBR', 'Petrobras', '2025 매출 12.5%')],
    'RIG': [('PBR', 'Petrobras', '2025 매출 22%'), ('SHEL', 'Shell', '2025 매출 22%'), ('EQNR', 'Equinor', '2025 매출 12%')],
    'SDRL': [('PBR', 'Petrobras', '2025 매출 36%'), ('TALO', 'Talos Energy', '2025 매출 11%')],
    'VAL': [('PBR', 'Petrobras', '2025 상위 실명 고객 · BP/Azule와 합산 35%'), ('BP', 'BP', '2025 상위 실명 고객 · 개별 비율을 합산값에서 배분하지 않음')],
    'SMHI': [('XOM', 'ExxonMobil', '2025 매출 17%')],
    'HOS': [('SHEL', 'Shell', '결합 전 Helix 2025 매출 18%'), ('PBR', 'Petrobras', '결합 전 Helix 2025 매출 10%')],
}.items():
    for _ticker, _name, _role in _customers:
        EDGES[_symbol].append(relation(_name, _ticker, 'customer', _role+' · 회사 매출 비중이며 계약물량·시장점유율이 아님', ANNUAL[_symbol]))
EDGES['SDRL'].append(relation('LLOG Exploration Company', None, 'customer',
    '2025 시추 고객 매출 10% · 현재 Harbour 소유 맥락은 기존 동일 법인 설명에서 확인', ANNUAL['SDRL'], 'llog-exploration'))
for _symbol, _role in [('VAL', '2025 상위 고객 · Petrobras/BP와 합산 35%'), ('SMHI', '2025 고객 매출 27%')]:
    EDGES[_symbol].append(relation('Azule Energy', None, 'customer', _role,
        ANNUAL[_symbol], 'azule-energy'))
    COMMON_CONTEXT.setdefault('azule-energy', {'brief': [], 'sources': []})
    COMMON_CONTEXT['azule-energy']['brief'].append(fact(PUBLIC[_symbol]['name']+' 실제 고객', _role, ANNUAL[_symbol]))
    COMMON_CONTEXT['azule-energy']['sources'].append(ANNUAL[_symbol])
COMMON_CONTEXT['llog-exploration'] = {'brief': [fact('Seadrill 실제 시추 고객',
    '2025 Seadrill 매출 10%이며 현재 Harbour 인수 맥락과 해당 연간 계약 관계를 구분합니다.', ANNUAL['SDRL'])], 'sources': [ANNUAL['SDRL']]}
EDGES['RIG'].append(relation('Valaris', 'VAL', 'transaction',
    '조건부 인수 계약 · 9월15일에도 proposed · 완료 모회사/자회사 아님', RIG_SEPT))
EDGES['VAL'].append(relation('Transocean', 'RIG', 'transaction',
    '조건부 결합 · 1주당 RIG 15.235주 계획 · 종결/주주/규제 승인 조건', RIG_VAL))
for _symbol, _peers, _scope in [
    ('NE', ('RIG', 'SDRL', 'VAL'), '일부 해양 계약 시추'),
    ('RIG', ('NE', 'SDRL'), '일부 초심해·가혹 환경 시추'),
    ('SDRL', ('NE', 'RIG', 'VAL'), '일부 심해 리그'),
    ('VAL', ('NE', 'SDRL'), '일부 심해·천해 리그'),
    ('TDW', ('SMHI', 'HOS'), '일부 OSV·해양 지원'),
    ('SMHI', ('TDW', 'HOS'), '일부 OSV·해양 수송'),
    ('HOS', ('TDW', 'SMHI', 'OII'), '일부 OSV·해저 작업'),
    ('XPRO', ('SLB', 'HAL', 'BKR'), '일부 유정 건설·관리·개입'),
]:
    for _peer in _peers:
        EDGES[_symbol].append(relation(_peer, _peer, 'competitor',
            _scope+' 사업 범위의 편집 비교 · 원문 실명 경쟁사 주장과 구분', ANNUAL[_symbol]))
