"""Coal and mineral operations with dated ownership and accounting boundaries."""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('ARLP', 'BTU', 'CNR', 'NC')
ANNUAL = {s: report(s) for s in SYMBOLS}
QUARTER = {s: report(s, 'quarter') for s in SYMBOLS}
UPDATES = {
    'ARLP': source('Alliance · Q2 및 광물권 취득 완료', 'https://www.sec.gov/Archives/edgar/data/1086600/000110465926086855/arlp-20260727xex99d1.htm', '2026-07-27'),
    'BTU': source('Peabody · Q2 Centurion 가동·목표 갱신', 'https://www.peabodyenergy.com/Home/Company-News-1200', '2026-07-29'),
    'CNR': source('Core · Q2 보험 회수·사업 결과', 'https://investors.corenaturalresources.com/2026-08-06-Core-Natural-Resources-Reports-Second-Quarter-2026-Results', '2026-08-06'),
    'NC': source('NACCO · Q2 계약·개발 일정', 'https://ir.nacco.com/2026-08-05-NACCO-INDUSTRIES-ANNOUNCES-SECOND-QUARTER-2026-RESULTS', '2026-08-05'),
}
PUBLIC = {
    'ARLP': profile('Alliance Resource Partners', ANNUAL['ARLP'],
        '미국 지하 탄광에서 발전·산업용 석탄을 생산하고, 별도 원유·가스 및 석탄 광물권에서 로열티를 받는 partnership입니다. 광물권 소유와 직접 유정·광산 운영은 다른 역할입니다.',
        '2025 매출 2,194,811,000 USD는 석탄 1,932,515,000·원유/가스 로열티 137,849,000·운송 36,612,000·기타 87,835,000입니다. 부문 표에는 본사 조정 -6,081,000을 보존합니다.',
        [('Illinois Basin', 'Illinois·Indiana·Kentucky의 광산과 Ohio River 운송 경로입니다. 장기 계약 가격·판매량·열량·수송비가 수익을 결정합니다.'),
         ('Appalachia', 'Maryland·Pennsylvania·West Virginia와 Kentucky의 지하 광산입니다. 지역별 석탄 품질·광구·지질·채굴 비용을 구별합니다.'),
         ('석탄 운영', '2025년말 7개 지하 채굴 단지와 Indiana 석탄 적재 터미널입니다. 장기 약정량과 실제 생산·판매 톤수는 다릅니다.'),
         ('원유·가스 광물권', '생산사가 시추·운영하는 광물권에서 로열티를 받습니다. royalty acres와 leasehold 작업 지분, 채굴 회사의 전체 매출을 구별합니다.'),
         ('석탄 로열티', '계열 탄광이 내는 부문 매출은 연결에서 제거됩니다. 80,471,000 USD 석탄 로열티 부문을 연결 외부 매출에 다시 더하지 않습니다.'),
         ('Matrix 기술', '채굴 안전·추적·통신·제어 기술을 제공하는 Matrix Design Group 사업입니다. 석탄 상품 판매와 기술·기타 매출은 다릅니다.'),
         ('에너지 투자', '채굴·로열티 외 에너지 인프라·기술 투자입니다. 투자 평가손익·배당·손상차손을 석탄 매출로 표시하지 않습니다.')],
        customers='Louisville Gas and Electric와 American Electric Power가 각각 2025 연결 매출의 10%를 넘는 실명 고객입니다. 운송 조건·연료 품질·납기·신용을 계약별로 확인합니다.',
        inputs='광물권·장벽식 채굴 장비·노동·전력·환기·안전 기술·철도·바지선·터미널이 필요합니다. 광산 복구 의무와 담보 자금은 당기 원료 구매와 다릅니다.',
        competition='미국 발전·산업용 석탄의 가격·열량·황 함량·물류·신뢰성으로 비교합니다. 천연가스·재생 전원 대체와 석탄 공급사 간 경쟁을 구별합니다.'),
    'BTU': profile('Peabody Energy', ANNUAL['BTU'],
        '미국·호주의 발전용 및 제철용 석탄을 채굴·판매합니다. 발전 연료인 thermal coal과 코크스·철강 원료인 metallurgical coal은 수요·품질·가격 지표가 다릅니다.',
        '2025 연결 매출 3,861,500,000 USD는 발전용 2,768,300,000·제철용 1,034,800,000·기타 58,400,000입니다. 사업 부문 표는 같은 연결 매출의 별도 보기입니다.',
        [('Powder River Basin', '미국 Wyoming의 대규모 노천 광산에서 발전용 석탄을 공급합니다. 상대적으로 낮은 열량·황 함량과 철도 운송을 함께 고려합니다.'),
         ('기타 미국 발전용', 'Illinois Basin·서부 미국의 발전용 석탄입니다. 지역별 생산 원가·매장량·발전소 수요·계약 단가가 다릅니다.'),
         ('해상 발전용', '호주 발전용 석탄의 국내·수출 판매입니다. Newcastle 가격·품질·환율·항만 선적 조건이 수익에 영향을 줍니다.'),
         ('해상 제철용', '호주와 미국의 제철용 석탄입니다. premium hard coking coal 지표·강종 적합성·장벽식 채굴 이동·수출 운송을 구별합니다.'),
         ('Centurion', '기존 North Goonyella를 재개발했고 2026년 2월 장벽식 채굴을 시작했습니다. 채굴 시작이 설계 생산량·원가 목표 달성을 뜻하지 않습니다.'),
         ('Middlemount JV', '50% 지분의 비연결 공동사업입니다. 2025년 1.4백만 톤은 50% 지분 기준이며 JV 전체 판매량·매출을 연결 수치에 더하지 않습니다.'),
         ('운영 광산 범위', '2025년말 16개 가동 광산 이해관계에는 JV가 포함됩니다. 16개를 전부 완전 소유 광산으로 표시하지 않습니다.')],
        customers='발전소·철강사·산업 고객과 상품 거래 상대입니다. 최대 고객 약 8%·상위 5개 약 25%의 분모는 석탄 공급 계약 매출이며 익명 고객의 실명을 추정하지 않습니다.',
        inputs='광물권·채굴 장비·노동·전력·철도·항만과 복구 보증이 필요합니다. Dalrymple Bay 및 Middlemount의 Abbot Point 수출 경로를 고객 기업과 구별합니다.',
        competition='미국 ARLP·Core·Hallador와 호주·국제 석탄 공급사를 제품·품질·물류로 비교합니다. 동일 업종이라는 이유만으로 공급·고객 계약을 만들지 않습니다.'),
    'CNR': profile('Core Natural Resources', ANNUAL['CNR'],
        'CONSOL Energy와 Arch Resources가 2025년 1월 14일 결합한 미국 석탄 기업입니다. 고열량 발전용·산업용·제철용·Powder River Basin 석탄과 수출 터미널을 운영합니다.',
        '2025 연결 매출 4,164,775,000 USD는 석탄 4,129,481,000·제3자 터미널 21,477,000·기타 13,817,000입니다. 인수 전 1월 1–13일 Arch 실적이 연결되지 않은 실제 기간입니다.',
        [('고열량 발전용', 'Pennsylvania Mining Complex·West Elk 등의 석탄으로 발전·산업·수출 수요를 충족합니다. 제품별 최종 용도와 보고 부문은 다릅니다.'),
         ('제철용', 'Leer·Leer South 등의 탄광입니다. 광산별 조업·보험·재개·채굴 조건과 제철용 석탄 가격을 구별합니다.'),
         ('Powder River Basin', '저황 발전용 석탄을 공급합니다. 매출·판매 톤수·톤당 가격과 고열량 석탄 부문의 분모를 섞지 않습니다.'),
         ('Core Marine Terminal', 'Baltimore 수출 터미널입니다. 부문 총매출 87,680,000에서 내부 매출 66,203,000을 제거한 제3자 매출 21,477,000을 사용합니다.'),
         ('Dominion Terminal', 'Dominion Terminal Associates의 35% 지분입니다. 항만 전체 처리 능력과 CNR 지분·실제 선적량은 다릅니다.'),
         ('CONSOL Innovations', '석탄 기반 탄소 재료·복합재 기술 사업입니다. 자회사 CFOAM과 Touchstone 자산 취득을 석탄 광산 생산으로 합산하지 않습니다.'),
         ('결합·비교 기준', '현재 Core와 과거 Arch·CONSOL 이름을 구별합니다. 2024 수치는 현재 그룹의 완전한 12개월 결합 실적과 같지 않습니다.')],
        customers='미국 발전·산업·제철 고객과 해외 최종 이용자·트레이더입니다. 발전/산업/제철 최종 용도 표와 국내/수출 교차표는 같은 석탄 매출입니다.',
        inputs='장벽식·노천 장비·광물권·인력·안전·철도·항만이 필요합니다. Core Marine은 CSX·Norfolk Southern 철도 경로를 사용합니다.',
        competition='Peabody·Alliance 및 미국·국제 석탄 공급사와 품질·원가·선적·납기를 비교합니다. 터미널 처리 능력은 석탄 시장점유율과 다릅니다.'),
    'NC': profile('NACCO Industries', ANNUAL['NC'],
        '고객 발전소에 연결된 석탄 광산 운영, 골재·광물 계약 채굴, 원유·가스 광물권 및 작업 지분을 운영합니다. 고객이 자금을 대는 비연결 광산과 자본·원가를 직접 부담하는 연결 광산이 다릅니다.',
        '2025 연결 매출 277,198,000 USD는 Utility Coal 88,188,000·Contract Mining 140,013,000·Minerals/Royalties 37,630,000·본사 15,080,000에서 내부거래 3,713,000을 차감합니다.',
        [('Utility Coal Mining', '발전소 연료 공급·광산 복구를 제공합니다. 고객 부담 원가와 톤/열량당 관리 수수료, 연결 MLMC의 상품·운영 위험을 구별합니다.'),
         ('Contract Mining', '고객 소유 골재·광물 광산의 채굴·운반·dragline 서비스를 수행합니다. 수수료가 서비스 매출이며 고객 광물의 총 판매액이 아닙니다.'),
         ('Minerals and Royalties', 'Catapult의 원유·가스 광물권 로열티와 Eiger의 작업 지분입니다. 작업 지분에는 생산 원가·자본 부담이 있으며 단순 로열티와 다릅니다.'),
         ('비연결 광산', 'Coteau·Coyote Creek·Falkirk·Sabine은 VIE에서 NACCO가 주된 수익자가 아니므로 연결하지 않습니다. 광산 총매출을 그룹 매출에 더하지 않습니다.'),
         ('MLMC', 'Mississippi Lignite Mining Company는 연결 광산입니다. Red Hills 고객 발전소의 가동·보일러 문제와 채굴·복구 비용이 수익에 영향을 줍니다.'),
         ('Sawtooth · Thacker Pass', 'Lithium Americas·GM 공동사업 광산의 계약 채굴 서비스입니다. 현장 건설 수익은 이미 발생하지만 미래 리튬 상업 생산과 다릅니다.'),
         ('Sabine 복구·예정 이전', 'Pirkey 발전소 조기 폐쇄 후 2023년 4월 석탄 인도를 중단하고 복구 서비스를 제공합니다. 공시는 SWEPCO의 2026년 10월 1일 주식 취득 의무를 명시하나 실제 종결 증거는 미확보입니다.')],
        customers='2025 연결 매출 31%·25%·10%의 세 고객은 표에서 익명입니다. SWEPCO는 Sabine의 실명 복구 계약 상대지만 익명 집중도 고객으로 추정하지 않습니다.',
        inputs='대형 dragline·굴착기·정비·숙련 인력·안전·광산 허가·고객 자금이 필요합니다. 복구 비용 부담은 광산별 계약과 연결 여부에 따라 다릅니다.',
        competition='계약 채굴 서비스는 장비·안전·단가·현장 수행을, 광물권은 생산사 활동·상품 가격을 비교합니다. 자체 석탄 판매사 전체와 동일한 원가·매출 모델이 아닙니다.'),
}
LATEST = {
    'ARLP': '7월 1일 206.2백만 USD의 원유·가스 광물권 취득을 실제 완료해 순 로열티 면적 약48,500 acres를 추가했습니다. 2025 연차·6월말 잔액에는 이 취득 후 범위를 소급 적용하지 않습니다.',
    'BTU': '7월 29일 기준 Centurion 시운전·지붕 제어 제약을 관리하며 2026 판매 2.0–2.5백만 톤을 목표로 합니다. 과거 3.5백만 톤 전망과 최신 목표를 구별하며 목표를 실제 판매로 표시하지 않습니다.',
    'CNR': '8월 6일 보고는 Leer South 보험 합의 회수와 조업 결과입니다. Q2 인식한 보험 회수 수익 125.4백만 USD는 석탄 판매 매출이 아니며 실제 현금 회수 시점도 다릅니다.',
    'NC': '8월 5일 보고는 Sawtooth 건설 수익과 Thacker Pass 완전 생산 2028 목표를 구별합니다. Sabine 복구의 9월말 종료 전망은 주식 이전의 실제 종결 확인이 아닙니다.',
}
for _symbol, _value in PUBLIC.items():
    _value['brief'].append(fact('최근 사업·범위', LATEST[_symbol], UPDATES[_symbol]))
    _value['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    _value['sources'].extend([QUARTER[_symbol], UPDATES[_symbol]])
    _value['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    _value['segments'] = _value['products'][:3]
    _value['drivers'] = [fact('조업·계약 변화', LATEST[_symbol], UPDATES[_symbol]),
        fact('원료·서비스 투입', _value['brief'][3]['detail'], ANNUAL[_symbol])]
    _value['financial_context'] = [fact('연결·단위·기간', '2025 연차 USD입니다. 광물 자원·매장량·항만 능력·미래 계약량과 실제 당기 매출을 구별하며 제품·부문 표를 더하지 않습니다. 비연결 JV·VIE 총매출을 합산하지 않습니다.', ANNUAL[_symbol])]

_PARTIES = [
    ('alliance-coal','Alliance Coal LLC','ARLP','subsidiary','간접 완전소유 석탄 사업 holding 회사입니다. 상장 partnership의 광물권·기술 투자 전체와 사업 범위를 구별합니다.'),
    ('matrix-design','Matrix Design Group LLC','ARLP','subsidiary','간접 완전소유 채굴 안전·통신·제어 기술 기업입니다. 제품 서비스와 석탄 상품을 구별합니다.'),
    ('lge-coal','Louisville Gas and Electric Company','ARLP','customer','2025 연결 매출의 10%를 넘는 실명 석탄 고객입니다. 집중도를 시장점유율이나 전체 계약의 독점으로 해석하지 않습니다.'),
    ('middlemount-coal','Middlemount Coal Pty Ltd','BTU','partner','Peabody 50% 비연결 광산 JV입니다. 지분 기준 톤수와 JV 전체 매출을 연결 실적에 더하지 않습니다.'),
    ('core-arch','Arch Resources Inc.','CNR','subsidiary','2025년 1월 14일 결합 후 Core의 완전소유 자회사입니다. 인수 전 Arch 기간과 현재 Core 연결 실적을 구별합니다.'),
    ('dominion-terminal','Dominion Terminal Associates','CNR','partner','Core의 지분 35% 항만 공동사업입니다. 항만 처리 능력과 회사의 실제 선적량·매출은 다릅니다.'),
    ('consol-innovations','CONSOL Innovations LLC','CNR','subsidiary','Core의 탄소 재료·복합재 기술 자회사입니다. CFOAM 사업과 광산 석탄 판매를 구별합니다.'),
    ('nacco-natural','NACCO Natural Resources Corporation','NC','subsidiary','NACCO의 완전소유 자원 사업 holding 회사입니다. 연결 광산·비연결 VIE·계약 채굴을 구별합니다.'),
    ('sawtooth-mining','Sawtooth Mining LLC','NC','subsidiary','North American Mining 계열의 Thacker Pass 계약 채굴 회사입니다. 고객 JV의 리튬 생산 자산 전체를 소유한 회사가 아닙니다.'),
    ('swepco-sabine','Southwestern Electric Power Company','NC','customer','AEP 계열로 Sabine 복구 자금·보상을 부담하며 2026년 10월 1일 주식 취득 의무가 있습니다. 예정 계약 의무와 실제 종결 확인을 구별합니다.'),
]
PRIVATE, EDGES = {}, {s: [] for s in SYMBOLS}
for _key, _name, _symbol, _kind, _role in _PARTIES:
    _origin = ANNUAL[_symbol]
    PRIVATE[_key] = profile(_name, _origin, _role, '여기서는 원문으로 확인한 해당 사업 역할을 설명합니다. 독립 기업 전체 매출·지분을 추정하지 않습니다.',
        [('확인한 계약·사업', _role)], customers='확인한 석탄·광물 가치사슬의 상대와 연결합니다.')
    EDGES[_symbol].append(relation(_name, None, _kind, _role, _origin, _key))
EDGES['ARLP'].append(relation('American Electric Power', 'AEP', 'customer', '2025 연결 매출의 10%를 넘는 실명 석탄 고객입니다.', ANNUAL['ARLP']))
for _symbol, _peers in {'BTU': [('Alliance Resource Partners','ARLP'),('Core Natural Resources','CNR'),('Hallador Energy','HNRG')],}.items():
    for _name, _ticker in _peers:
        EDGES[_symbol].append(relation(_name, _ticker, 'competitor', '연차가 명시한 석탄 공급 경쟁 범위입니다. 고객·공급 계약이 아닙니다.', ANNUAL[_symbol]))
EDGES['NC'].append(relation('Lithium Americas', 'LAC', 'customer', 'Sawtooth의 Thacker Pass 고객 프로젝트입니다. 공동사업 지분과 채굴 서비스 역할을 구별합니다.', ANNUAL['NC']))
COMMON_CONTEXT = {}


def replaced_generated_relation(row, symbol):
    """The exact reviewed JV supersedes this generated Exhibit 21 claim."""
    origin = row.get('source', {})
    return (symbol == 'BTU' and row.get('kind') == 'subsidiary'
        and row.get('name') == 'Middlemount Coal Pty Ltd'
        and origin.get('url', '').split('#')[0] ==
            'https://www.sec.gov/Archives/edgar/data/1064728/000106472826000006/btu_20251231xex21.htm'
        and origin.get('as_of') == '2026-02-19'
        and origin.get('label', '').startswith('SEC · Exhibit 21')
        and row.get('detail', '').startswith('공시 자회사 명세서'))

PUBLIC['BTU']['products'].append(fact('Anglo 인수 계약 종료', '호주 제철용 석탄 자산 인수 계약은 2025년 8월 19일 종료됐습니다. 제안된 광산 인수와 예정 Dawson 재매각을 완료된 현재 자산으로 표시하지 않습니다.', ANNUAL['BTU']))
