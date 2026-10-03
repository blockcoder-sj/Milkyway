"""Edited laboratory, equipment and subsea-service notes from dated filings.

Brand names are product operations, never inferred legal subsidiaries. Unnamed
customers and vendors remain unnamed; concentrations have their own period.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation

SYMBOLS = ('CLB', 'FET', 'NESR', 'OII', 'OIS')
ANNUAL = {symbol: report(symbol) for symbol in SYMBOLS}
QUARTER = {symbol: report(symbol, 'quarter') for symbol in SYMBOLS}

PUBLIC = {
    'CLB': profile('Core Laboratories', ANNUAL['CLB'],
        '저류층의 암석·유체를 실험실에서 분석하고 유정 생산을 높이는 천공·진단·추적 기술을 제공합니다. 원유를 직접 생산하는 회사가 아니라 생산자의 개발·회수 의사결정을 지원합니다.',
        '2025 매출 526,520,000 USD입니다. Reservoir Description 347,683,000·Production Enhancement 178,837,000이며 서비스 399,422,000·제품 127,098,000은 같은 매출의 다른 분류입니다.',
        [('암석·코어 분석', '공극·투과도·유체 포화도·압력 조건을 측정해 개발·완결·회수 설계를 지원합니다.'),
         ('유체·PVT 분석', '고온·고압에서 원유·가스 특성을 분석하고 탄화수소·정제품·바이오연료의 품질·수량을 측정합니다.'),
         ('실험실 장비', '자체 실험실뿐 아니라 고객·대학·정부 실험실용 분석 장비도 제조합니다.'),
         ('RAPID·공동 연구', '저류층 데이터·공동 산업 연구를 제공하며 보유 지식재산의 재판매 권리와 법적 합작 지분은 다릅니다.'),
         ('Production Enhancement', '천공·완결 도구, 화학 추적자·진단과 물/CO₂ 주입의 이동 경로 분석을 제공합니다.'),
         ('시설·지역', '2025 연차 기준 50개국 이상·70개 이상 사무소이며 Aberdeen·Abu Dhabi·Houston·Kuala Lumpur·Rotterdam 기술센터가 연결됩니다.'),
         ('지역 매출 기준', '서비스는 수행·프로젝트 지역, 제품은 배송지 기준입니다. 배송지를 최종 사용 고객의 본사로 바꾸지 않습니다.')],
        customers='생산자·정유/유체 사업자·연구기관이 구매합니다. 2025 개별 고객 10% 이상은 없으며 원문에 없는 최대 고객·장비 공급사 이름은 만들지 않습니다.',
        inputs='실험·제조 시설, 전문 분석 인력, 측정 장비·화학 추적자·금속 부품과 고객 시료·데이터가 필요합니다.',
        competition='저류층 분석·완결 진단·천공 제품의 범위별로 비교합니다. 경쟁사의 종합 유전 서비스 매출 전체와 실험실 매출을 같은 시장으로 보지 않습니다.'),
    'FET': profile('Forum Energy Technologies', ANNUAL['FET'],
        '시추·완결·해저 작업·인공 채유·생산 처리용 장비와 소모품을 설계·제조합니다. 고객은 생산자뿐 아니라 리그·파쇄·와이어라인 서비스사와 산업·방산·재생에너지 사업자입니다.',
        '2025 연결 매출 791,474,000 USD입니다. 시추·완결 내부거래 포함 477,191,000과 인공 채유·다운홀 314,785,000에서 502,000을 제거합니다. 제거 후 부문 매출은 476,689,000·314,785,000입니다.',
        [('시추 장비·소모품', '관 취급·크레인·펌프/유체단·밸브·센서와 OEM/수리용 베어링을 제공합니다.'),
         ('Perry 해저 로봇', '심해 건설 work-class ROV와 해저 배관·전력/통신 케이블 매설용 trencher입니다. 최대 3m 초과 절삭 깊이는 장비 사양입니다.'),
         ('VisualSoft·ICE Unity', '해저 작업 영상·데이터 관리와 ROV 운영 지원 기술입니다.'),
         ('완결·개입·코일튜빙', '파쇄·와이어라인·유정 개입용 압력/유체 장비와 코일튜빙 제품을 제공합니다.'),
         ('Davis-Lynch', '석유·가스·지열 유정의 centralizer·float·시멘팅 도구·packer 등 케이싱 고정·격리 제품군입니다.'),
         ('Variperm·인공 채유 보호', '중질유 모래/유량 제어와 ESP 케이블·가스/모래 보호 제품입니다. 브랜드별 매출은 별도로 공개하지 않습니다.'),
         ('생산 처리·밸브', 'separator·압력용기·skid·desalter와 PBV/DSI/Accuseal 밸브를 직접 또는 유통사를 통해 판매합니다.'),
         ('매출 활동 기반', '2025 약 80%는 소모품·활동 기반 장비이며 나머지는 주로 자본 장비와 소량 임대·기타 서비스입니다.')],
        customers='육상/해상 리그사·현장 서비스사·생산자·처리/정유 사업자와 정부 연구·해군 조직입니다. 이름을 공개하지 않은 고객 집중도를 특정 생산자에 배정하지 않습니다.',
        inputs='금속·주조/가공 부품·전자 제어·유체 부품과 전문 제조 인력이 필요합니다. 제품 브랜드가 외부 원재료 공급사라는 뜻은 아닙니다.',
        competition='시추·ROV·완결 소모품·생산 처리·밸브별로 가격·성능·납기·정비를 비교합니다. 모든 제품을 한 파쇄 서비스 시장으로 묶지 않습니다.'),
    'NESR': profile('National Energy Services Reunited', ANNUAL['NESR'],
        '주로 중동·북아프리카 MENA의 생산자에게 생산·완결·시추·평가와 통합 현장 서비스를 제공합니다. 기술 파트너 제품과 자체 작업팀을 결합합니다.',
        '2025 생산 서비스 815,999,000 USD·시추/평가 508,048,000, 합계 1,324,047,000입니다. MENA 1,315,939,000·기타 지역 8,108,000은 별도 지역 보기입니다.',
        [('생산 서비스', '완결·자극·시멘팅·코일튜빙·압력/유체 관리 등 기존·신규 유정의 생산을 지원합니다.'),
         ('시추·평가·Roya', '방향성 시추·유정 평가·관리 압력 시추 MPD 기술을 제공하며 파트너 기술과 작업 수행을 연결합니다.'),
         ('PHX 기술 협력', '북미 방향성 시추 기술을 MENA로 도입하는 실제 기술 파트너입니다.'),
         ('Beyond·Kinetic', 'Beyond의 MPD와 Kinetic KBOS 분출 정지 기술 협력입니다. KBOS 상업 fleet는 2025 확대됐습니다.'),
         ('NEDA', '용수·광물 추출·배출 모니터링·flare gas 활용입니다. 2025 DLE pilot 완료와 상업 대규모 매출은 다른 단계입니다.'),
         ('NORI 연구', 'Dhahran Techno Valley 연구센터의 저류층 분석·기술 시험이 현장 서비스와 연결됩니다.'),
         ('IPM 지급 구조', '고객 유정 생산에서 발생한 현금에 연동해 보상받는 개발·관리 계약입니다. 일반 작업 직후 대금 수취와 다릅니다.'),
         ('WDVGE 투자', 'WD Von Gonten Engineering은 소수 투자·지분법 사업입니다. 피투자자의 매출 17,824,000 USD를 NESR 연결 매출에 더하지 않습니다.')],
        customers='2025 익명 고객 4곳의 비중은 49%·9%·8%·7%입니다. 이 집중도만으로 Aramco나 다른 국영 생산자의 이름을 붙이지 않습니다.',
        inputs='현장 인력·장비·약품·정비·기술 파트너와 프로젝트별 고객 자산·생산 데이터가 필요합니다. 2025 직원+독립 계약자 7,352명은 모두 정규직이라는 뜻이 아닙니다.',
        competition='MENA 현장 완결·시추·평가·통합 생산 서비스의 실제 범위로 비교하며 국별 현지화·기술·작업 안전·회수 조건이 중요합니다.'),
    'OII': profile('Oceaneering International', ANNUAL['OII'],
        '해저 로봇·umbilical 제조·해양 작업·설비 건전성/디지털 서비스와 항공우주·방산 기술을 제공합니다. 에너지 기업 분류지만 비에너지 매출도 포함합니다.',
        '2025 연결 매출 2,784,156,000 USD입니다. 에너지 4개 부문 2,324,252,000과 Aerospace & Defense 459,904,000이며 서비스 2,208,190,000·제품 575,966,000은 같은 총액의 다른 보기입니다.',
        [('Subsea Robotics', 'ROV·survey·positioning·tooling으로 시추 지원·설치·점검·수리를 수행합니다. 2025년말 work-class ROV 250대에 특수 시스템이 포함됩니다.'),
         ('Liberty·Freedom·Isurus', '원격 운용 E-ROV·hybrid AUV/ROV와 해저 로봇입니다. 전담 선박 대기·현장 인력 부담을 줄이는 기술이며 별도 공개 제품 매출은 없습니다.'),
         ('Manufactured Products', '미국·Scotland·Brazil에서 해저 전력·제어·약품 전달 umbilical을 만들며 육상 제조·물류용 이동 로봇도 포함합니다.'),
         ('Offshore Projects Group', 'IMR·riserless 경정비·잠수·유정 개입·해양 프로젝트를 수행합니다. 2025 심해 작업선 2척 소유·5척 용선을 구분합니다.'),
         ('IMDS', '육상/해상 에너지·발전·석유화학 자산의 부식·비파괴 검사·건전성 관리·소프트웨어입니다.'),
         ('GDi', '2024-10 약 33,000,000 USD에 취득한 영국 디지털/소프트웨어 기업이며 IMDS 역량과 연결됩니다.'),
         ('Aerospace & Defense', '미국 정부 등의 해양·우주·방산 설계/기술 업무이며 전부 석유 생산 지원 매출로 표시하지 않습니다.')],
        customers='2025 상위 5개 고객 31%, 미국 정부 12%이며 그 외 개별 고객 10% 초과는 없습니다. 정부 기관별 금액이나 익명 에너지 고객 이름을 추정하지 않습니다.',
        inputs='금속·주조·단조·가공·물류·전력/제어 부품·소프트웨어·숙련 작업자·선박이 필요합니다. 대다수 재료/서비스는 복수 공급원이며 미공개 공급사 이름은 만들지 않습니다.',
        competition='ROV·해저 작업·umbilical·검사·비에너지 로봇/방산별로 계약·기술·선박·인력 범위를 비교합니다.'),
    'OIS': profile('Oil States International', ANNUAL['OIS'],
        '해상 생산·시추용 고성능 부품과 육상/해상 완결·유정 개입 서비스, 천공·격리용 다운홀 소모품을 제공합니다. 방산·풍력·지열·해저 광물 관련 제품도 포함됩니다.',
        '2025 연결 매출 668,988,000 USD입니다. Offshore Manufactured Products 431,093,000·Completion and Production Services 114,548,000·Downhole Technologies 123,347,000이며 제품/서비스 436,397,000·232,591,000은 별도 보기입니다.',
        [('해상 제조', 'FlexJoint·connector·고압 riser·MPD·mooring·crane·해저 배관과 설치/검사/수리 제품·서비스입니다.'),
         ('비석유 제조', '해상 풍력·지열·해저 광물 수집과 해군 함정의 밸브·소음/진동 완화 제품입니다.'),
         ('Oil States Energy Services·Tempress', '완결·생산 단계의 압력 제어·다운홀·extended-reach 작업 브랜드입니다. 브랜드 이름만으로 별도 법인 소유를 추정하지 않습니다.'),
         ('천공·격리', '천공 구멍·관통 깊이/품질을 개선하는 도구와 toe valve·frac plug·setting tool·bridge plug를 제공합니다.'),
         ('미국 육상 조정', '2025 시설·서비스 축소·인력 감축과 비현금 손상을 반영합니다. 2024-08 남은 육상 리그 매각 전 시추 사업을 현재 보유 fleet로 표시하지 않습니다.'),
         ('수주 잔액', '2025년말 해상 제조 backlog 435,000,000 USD는 계약상 주문 잔액이며 연결 연간 실현 매출이나 현금 보유액이 아닙니다.'),
         ('고객·유통', '최종 사용자·설계사·prime contractor와 경쟁사의 outsourcing 주문이 포함됩니다. 경쟁 관계가 모든 제품 거래의 부재를 뜻하지 않습니다.')],
        customers='2025~2023 개별 고객이 연결 매출 10%를 초과하지 않았습니다. 공개하지 않은 주요 고객 이름과 계약량은 추정하지 않습니다.',
        inputs='금속·정밀 가공/주조·제어 부품·현장 인력·유정 접근과 생산자의 개발/완결 예산이 필요합니다. 긴 해상 개발과 단기 육상 활동의 수요 주기가 다릅니다.',
        competition='공시는 해상 제조의 Baker Hughes·Hutchinson·NOV·OneSubsea·TenarisHydril을 명시합니다. 각각 제품 범위가 다르며 전체 회사 매출로 시장점유율을 계산하지 않습니다.'),
}

LATEST = {
    'CLB': '2026 Q2 공시는 Reservoir Description·Production Enhancement와 연결 범위를 다시 확인합니다. 반기 실적을 단순 두 배 해 연간 전망으로 표시하지 않습니다.',
    'FET': '2026 Q2 공시는 2개 사업 부문을 유지합니다. 장비 주문·backlog·진행률 매출과 실제 현금 수취를 구분합니다.',
    'NESR': '2026 상반기 IPM 인식 매출과 관련 상각은 0입니다. 2025 익명 고객 비율·pilot를 현재 신규 상업 계약으로 바꾸지 않습니다.',
    'OII': '2026-06-30 건설 중 자산 52,000,000 USD는 주로 로봇·해양 프로젝트 부문입니다. 2025 ROV·선박 수를 실시간 fleet라고 표시하지 않습니다.',
    'OIS': '2026 Q1 추가 미국 육상 서비스 철수·장비 매각 대상으로 1,400,000 USD 손상을 인식했습니다. 2026 상반기 매출 302,022,000 USD이며 2025 연간 표와 기간이 다릅니다.',
}
for _symbol, _value in PUBLIC.items():
    _value['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    _value['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    _value['brief'].append(fact('최근 분기·진행 상태', LATEST[_symbol], QUARTER[_symbol]))
    _value['sources'].append(QUARTER[_symbol])
    _value['segments'] = [fact(item['title'], item['detail'], item['source'])
                          for item in _value['products'][:3]]
    _value['drivers'] = [fact('수요·실제 수행', _value['brief'][0]['detail'], ANNUAL[_symbol]),
                         fact('고객·계약 집중', _value['brief'][2]['detail'], ANNUAL[_symbol])]
    _value['financial_context'] = [fact('기간·연결·분모',
        '2025 연결 USD 기준입니다. 제품·사업부·지역은 같은 매출의 별도 관점이며 서로 합산하지 않습니다. 고객 집중도는 회사 매출 비율이며 업계 시장점유율이 아닙니다.', ANNUAL[_symbol])]

PRIVATE = {}
EDGES = {symbol: [] for symbol in SYMBOLS}
for _key, _name, _symbol, _kind, _business, _role in [
    ('phx-nesr', 'PHX Energy Services Corp.', 'NESR', 'partner', 'NESR가 공시한 방향성 시추 기술 파트너입니다.', '북미 기술을 MENA로 도입하는 기술 협력이며 NESR 연결 자회사 소유 관계를 뜻하지 않습니다.'),
    ('beyond-energy-nesr', 'Beyond Energy Services & Technology Corp.', 'NESR', 'partner', 'NESR 관리 압력 시추 MPD의 기술 파트너입니다.', '장비·기술과 현장 MPD 수행을 연결합니다. 공개하지 않은 지분·계약금액은 표시하지 않습니다.'),
    ('kinetic-pressure-nesr', 'Kinetic Pressure Control Limited', 'NESR', 'partner', 'Kinetic Blowout Stopper KBOS를 개발하는 NESR의 기술 파트너입니다.', 'MENA 도입과 2025 KBOS 상업 fleet 확대가 확인됩니다. 예정 시험을 이미 완료된 납품으로 표시하지 않습니다.'),
    ('wdvge-nesr', 'WD Von Gonten Engineering LLC', 'NESR', 'holding', 'NESR가 소수 지분을 투자한 석유공학·저류층 전문 사업입니다.', '2022-07 투자·지분법 대상이며 2025 피투자자 매출 17,824,000 USD를 NESR 매출에 더하지 않습니다.'),
    ('gdi-oceaneering', 'Global Design Innovation Ltd. · GDi', 'OII', 'subsidiary', 'Oceaneering가 2024-10 취득한 영국 디지털·소프트웨어 사업입니다.', '약 33,000,000 USD 취득 대가와 현재 연간 소프트웨어 매출은 다릅니다. 디지털/IMDS 역량 확장에 사용합니다.'),
    ('us-government-oceaneering', '미국 정부 · Oceaneering 고객', 'OII', 'customer', 'Oceaneering가 실명 공시한 비에너지 기술 고객 범위입니다.', '2025 연결 매출 12%이며 주로 항공우주·방산 부문입니다. 정부 부처별 대가와 예산을 만들지 않습니다.'),
]:
    _origin = ANNUAL[_symbol]
    PRIVATE[_key] = profile(_name, _origin, _business, _role,
        [('확인된 역할', _role)], customers='이 페이지는 해당 관계의 실제 역할을 설명하며 상대 회사 전체 매출을 추정하지 않습니다.')
    EDGES[_symbol].append(relation(_name, None, _kind, _role, _origin, _key))
    PRIVATE[_key]['relations'].append(relation(PUBLIC[_symbol]['name'], _symbol,
        'parent' if _kind == 'subsidiary' else 'partner' if _kind in {'partner', 'holding'} else 'supplier',
        _role, _origin))

# Brands remain product descriptions above; no guessed corporate graph nodes.
for _symbol, _peers, _scope in [
    ('CLB', ('SLB', 'HAL'), '일부 저류층 평가·완결 진단·천공 기술'),
    ('FET', ('NOV', 'OIS'), '일부 시추·유정 장비·소모품'),
    ('NESR', ('SLB', 'HAL', 'BKR'), '일부 MENA 현장 서비스'),
    ('OII', ('OIS', 'FTI'), '일부 해저 제조·서비스'),
]:
    for _peer in _peers:
        EDGES[_symbol].append(relation(_peer, _peer, 'competitor',
            _scope + ' 사업 범위 비교 · 공시를 대조한 편집 비교이며 원문 실명 경쟁사 주장과 구분', ANNUAL[_symbol]))
for _peer, _name in [('BKR', 'Baker Hughes'), ('NOV', 'NOV'), ('TS', 'Tenaris · TenarisHydril')]:
    EDGES['OIS'].append(relation(_name, _peer, 'competitor', '2025 원문 실명 · 해상 제조 제품 경쟁', ANNUAL['OIS']))
EDGES['OIS'].append(relation('SLB OneSubsea', None, 'competitor', '해상 제조 제품 경쟁 · 이미 등록된 실제 JV 사용', ANNUAL['OIS'], 'slb-onesubsea'))
