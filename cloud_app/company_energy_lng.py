"""LNG import, liquefaction and export: dated construction and issuer scopes."""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('EE', 'NEXT', 'NFE', 'VG')
ANNUAL = {s: report(s) for s in SYMBOLS}
QUARTER = {s: report(s, 'quarter') for s in SYMBOLS}
EE_UPDATE = source('Excelerate · Q2 사업·일정 갱신',
    'https://excelerateenergy.com/news/excelerate-energy-reports-strong-second-quarter-2026-results/', '2026-08-05')
NEXT_UPDATE = source('NextDecade · Q2 건설·개발 보고',
    'https://nextdecade.gcs-web.com/news-releases/news-release-details/nextdecade-provides-second-quarter-2026-business-update', '2026-07-30')
NFE_CLOSE = source('SEC · New Fortress 구조조정·Brazil 분리 완료',
    'https://www.sec.gov/Archives/edgar/data/1749723/000174972326000118/nfe-20260911.htm', '2026-09-11')
VG_UPDATE = source('Venture Global · Q2 가동·시운전·개발',
    'https://ventureglobal.com/2026/08/11/venture-global-reports-second-quarter-2026-results/', '2026-08-11')
VG_CHINA = source('Venture Global · China Gas 신규 장기 계약',
    'https://ventureglobal.com/2026/09/14/venture-global-and-china-gas-announce-new-long-term-lng-agreement/', '2026-09-14')

PUBLIC = {
    'EE': profile('Excelerate Energy', ANNUAL['EE'],
        'LNG를 수입해 다시 가스로 바꾸는 부유식 재기화 터미널과 가스·전력 인프라를 운영합니다. 생산지에서 액화·수출하는 사업과 수요국의 재기화·공급 역할이 다릅니다.',
        '2025 매출 1,228,263,000 USD는 FSRU·터미널 596,628,000과 LNG·가스·전력 판매 631,635,000입니다. 지역 표와 별도 수익 유형 교차표를 추가 합산하지 않습니다.',
        [('FSRU·재기화', 'LNG의 저장·열교환·가스 송출을 선박형 터미널에서 제공합니다. 선박 소유·리스와 터미널 운영 범위를 구별합니다.'),
         ('LNG·가스 판매', '구매 LNG를 재기화하거나 직접 공급하며 가격 지표·운송·take-or-pay 조건에 따라 매출과 원료 비용이 함께 달라집니다.'),
         ('전력·열', 'Jamaica의 Clarendon 열병합과 가스 터미널을 통해 가스·전력·증기를 계약 고객에게 공급합니다.'),
         ('Jamaica 실제 취득', '2025년 5월 NFE의 Montego Bay·Old Harbour·Clarendon 사업을 취득했습니다. 연초부터 보유했다고 가정한 pro forma와 실제 연결 매출은 다릅니다.'),
         ('계약 수익 종류', '리스 수익 541,013,000·재기화/기타 55,615,000·LNG/가스/전력 631,635,000 USD 구분은 같은 2025 매출의 다른 보기입니다.'),
         ('자산 기준일', '연말 11개 부유식 터미널과 2026 Q2의 신규 선박 인도 후 12개를 구별합니다. 조선소 인도와 수요국 터미널 가동은 별도 사건입니다.'),
         ('국가별 인프라', '항만·계류·파이프라인·가스 이용 발전소가 연결되며 선박만 도착했다고 전체 공급망이 준공된 것은 아닙니다.')],
        customers='정부·국영 에너지사·발전/산업 고객입니다. Petrobangla 장기 LNG 공급과 지역별 재기화 계약을 구별하며 익명 매출 집중도에 실명을 추정하지 않습니다.',
        inputs='QatarEnergy 등 LNG 조달, FSRU 건조·정비·crew, 항만·파이프라인과 수요국 허가가 필요합니다. HD Hyundai Heavy는 건조 공급사입니다.',
        competition='재기화 능력·계약 가동·터미널 위치·LNG 조달·통합 가스/전력 수행을 비교합니다. LNG 수출사의 생산량을 수입 터미널 시장점유율로 쓰지 않습니다.'),
    'NEXT': profile('NextDecade', ANNUAL['NEXT'],
        'Texas Brownsville의 Rio Grande LNG 액화·수출 설비를 건설·개발합니다. 현재 건설 중인 트레인과 향후 허가·투자 결정을 추진하는 추가 트레인을 구별합니다.',
        '향후 LNG 판매 가격은 고정 액화료와 원료·연료 비용에 연결된 변동료로 구성됩니다. 유효한 장기 계약·기대 연간 수수료·프로젝트 자금 조달은 당기 LNG 매출이 아닙니다.',
        [('Trains 1–3 · Phase 1', '2023년 7월 FID·금융 종결 후 착공한 단계입니다. 최종 준공·첫 LNG·상업 인도는 각 계약의 별도 기준입니다.'),
         ('Train 4', '2025년 9월 FID·금융 종결 후 착공했습니다. Phase 1과 공동 인프라를 사용하지만 별도 계약·법인·배분 조건이 있습니다.'),
         ('Train 5', '2025년 10월 착공 단계입니다. 5개 트레인 약 30 MTPA는 완공 후 예상 생산능력이며 현재 판매량이 아닙니다.'),
         ('Trains 6–8', '추가 약 18 MTPA의 개발·허가 단계입니다. 건설 중 5개와 합친 잠재 48 MTPA를 현재 가동 48 MTPA로 표시하지 않습니다.'),
         ('장기 SPA', '2025년말 14개 상대·약25.3 MTPA·평균19.5년 계약입니다. 취소/중단 때 고정료 조건과 첫 상업 인도 개시 조건을 구별합니다.'),
         ('EPC·액화 기술', 'Bechtel Energy의 turnkey EPC와 Honeywell AP-C3MR 기술입니다. 시공자·기술 제공자·원료 가스 판매자는 역할이 다릅니다.'),
         ('분배·CCS', 'JV의 가용 현금 배분율과 회계상 연결/지분율은 다른 개념입니다. 검토 중 CCS를 운영 중인 탄소 포집 매출로 만들지 않습니다.')],
        customers='장기 LNG 구매 상대와 향후 spot·단기/중기 고객입니다. TotalEnergies는 LNG 계약·프로젝트 투자·상장사 지분이 겹치는 실명 상대입니다.',
        inputs='천연가스·배관·액화 압축/열교환·전력·저장탱크·부두와 Bechtel EPC 수행이 필요합니다. 건설 자금과 작업 진척을 매출로 바꾸지 않습니다.',
        competition='완공 후 세계 LNG 액화·수출 공급과 가격·원료 접근·인도 신뢰성을 비교합니다. 개발 계획은 가동 생산능력과 구별합니다.'),
    'NFE': profile('New Fortress Energy', NFE_CLOSE,
        'LNG·천연가스의 공급·운송·재기화와 발전/운영 서비스를 연결합니다. 2026년 9월 구조조정 완료로 Brazil 사업이 별도 기업으로 분리돼 과거 연차의 그룹 범위가 현재 New NFE와 다릅니다.',
        '2025 매출 1,504,037,000 USD는 구조조정 전 연차 범위입니다. 터미널/인프라 1,384,693,000·선박 119,344,000이며 Cargo 276,404,000은 고객 계약 매출 중 일부입니다.',
        [('LNG 조달·FLNG', '자체 부유식 액화와 외부 LNG 조달을 결합합니다. 연차의 FLNG 1·FLNG 2 계획과 9월 구조조정 후 소유/금융 범위를 분리합니다.'),
         ('Puerto Rico 공급', 'San Juan 터미널에서 발전·산업 고객에게 가스를 공급합니다. PREPA 공급 계약과 과거 비상 발전 장비 매각은 다른 거래입니다.'),
         ('Mexico 공급', 'La Paz 터미널·가스 공급·발전과 CFEnergia 고객 계약을 연결합니다. 전력 회사와 직접 가스 계약 법인을 구별합니다.'),
         ('Genera PR', 'PREPA 화력 자산 운영·정비 계약의 서비스 회사입니다. 관리료·비용 환급 매출과 연료 공급 매출을 구별합니다.'),
         ('선박·리스', '소유·용선·운영하는 FSRU/LNG선과 Energos 소유 선박을 구별합니다. 타사 선박을 전부 NFE 소유 fleet로 만들지 않습니다.'),
         ('Jamaica 처분', '2025년 5월 Excelerate에 사업 처분을 완료했습니다. 해당 과거 자산을 현재 NFE 소유 터미널로 설명하지 않습니다.'),
         ('Brazil 분리', '9월 11일 완료된 구조조정으로 BrazilCo와 New NFE가 별도 기업이 됐습니다. 과거 Brazil 발전·터미널을 현재 New NFE 전체에 포함하지 않습니다.')],
        customers='PREPA·CFEnergia 등 가스/전력 계약 상대가 있습니다. 2025 익명 고객 30%를 PREPA·CFE로 추정하지 않으며 그 집중도를 분리 후 그룹에 그대로 적용하지 않습니다.',
        inputs='LNG·가스 원료, 액화·재기화 설비·용선·항만·발전 터빈·정비·자금이 필요합니다. 구조조정 후 자산별 채무와 전체 연결 부채는 다른 분모입니다.',
        competition='통합 LNG 공급·터미널·발전/정비 수행을 비교합니다. 구조조정 완료가 미래 이익·자금 조달·프로젝트 완공을 보장하지는 않습니다.'),
    'VG': profile('Venture Global', ANNUAL['VG'],
        'Louisiana의 LNG 액화·수출과 원료 가스 수송·해운·판매를 운영·개발합니다. 시운전 중 실제 LNG 판매가 가능하며 상업 가동일(COD)과 생산 시작은 같은 사건이 아닙니다.',
        '2025 매출 13,769,000,000 USD는 LNG 13,687,000,000·기타 82,000,000입니다. 부문 표의 내부거래 제거 -2,050,000,000을 보존하며 제품·지역과 더하지 않습니다.',
        [('Calcasieu Pass', '2022년 시운전 판매를 시작했고 2025년 4월 COD를 선언했습니다. 시운전 판매와 post-COD SPA 이행의 기간·가격 조건이 다릅니다.'),
         ('Plaquemines', '2025년 LNG 시운전 판매를 시작했습니다. 모듈 가동·통합 성능 검증·Phase 1/2 COD를 각각 구별합니다.'),
         ('CP2', '액화·배관과 이후 확장을 건설·개발합니다. 2025 부문 매출 1,000,000 USD를 완공 후 LNG 판매나 전체 가동 증거로 쓰지 않습니다.'),
         ('VG Commodities', '시운전·초과 용량 LNG와 선박/판매 활동을 연결합니다. 그룹 내 구매·판매 매출은 연결 단계에서 제거됩니다.'),
         ('가격·장기 계약', 'post-COD 고정 액화료+Henry Hub 연결 원료료와 spot/단기 시운전 판매를 구별합니다. 미래 MTPA 계약을 당기 매출로 환산하지 않습니다.'),
         ('모듈·시공', 'Baker Hughes 장비, UOP 전처리, CB&I 탱크와 KZJV EPC 등 공급 역할이 나뉩니다. 계약형식·부품 성능·전력 설비가 준공에 영향을 줍니다.'),
         ('고객·분쟁', 'LNG 장기 계약 상대가 경쟁사이기도 합니다. BP 중재의 책임 판단·향후 손해 심리·당사자 청구 금액과 확정 지급액을 구별합니다.')],
        customers='LNG 구매자·포트폴리오 사업자·전력/가스 유틸리티입니다. 2025 상위 3개 약 50%·최대 1개 약 23% 익명 매출 집중도에 실명을 붙이지 않습니다.',
        inputs='천연가스·배관 용량·액화 모듈·압축/발전 장비·전처리·탱크·선박·숙련 인력과 허가가 필요합니다. 총 개발 용량은 실제 생산량과 다릅니다.',
        competition='Cheniere·Freeport·Sempra 및 국영/대형 에너지사·상품 트레이더와 LNG 공급을 비교합니다. 고객과 경쟁 역할은 함께 존재할 수 있습니다.'),
}

LATEST = {
    'EE': ('일정·가동 갱신', '8월 5일 발표는 Acadia의 Jordan 7월 가동, Colombia Express 2027 Q1 예상, Iraq 터미널 2027 Q2 초 예상, 선박 전환 2028 초 예상입니다. 과거 연차의 Iraq 2026 Q3 예상은 최신 일정으로 대체합니다.', EE_UPDATE),
    'NEXT': ('현재 건설·미래 첫 LNG', '7월 30일 보고는 Train 1 첫 LNG 2027 H1 예상입니다. Train 6의 Baker Hughes 압축기 reservation과 허가 신청은 FID·납품·가동 완료가 아닙니다.', NEXT_UPDATE),
    'NFE': ('구조조정·자산 분리 완료', '9월 11일 UK 계획 이행과 미국 인정 후 구조조정을 실제 완료했습니다. Brazil 사업 분리·새 금융 조건은 과거 2025 연차와 별도 범위입니다.', NFE_CLOSE),
    'VG': ('신규 장기 계약·가동 구분', '9월 14일 China Gas 신규 0.5 MTPA·20년·2030 시작 SPA를 체결했습니다. 전체 2.5 MTPA 장기 계약과 신규 0.5를 더해 3.0으로 계산하지 않습니다. 계약량은 현재 매출·시장점유율이 아닙니다.', VG_CHINA),
}
for _symbol, _value in PUBLIC.items():
    _title, _detail, _origin = LATEST[_symbol]
    _value['brief'].append(fact(_title, _detail, _origin))
    _value['sources'].extend([ANNUAL[_symbol], QUARTER[_symbol], _origin])
    _value['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    _value['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    _value['segments'] = [fact(r['title'], r['detail'], r['source']) for r in _value['products'][:3]]
    _value['drivers'] = [fact('가동·인도·계약', _detail, _origin),
                         fact('투입·수행', _value['brief'][3]['detail'], ANNUAL[_symbol])]
    _value['financial_context'] = [fact('기간·연결 범위',
        '표에 표시한 2025 연차 USD 범위입니다. 계약량·개발 능력·backlog·JV 현금 배분과 당기 연결 매출·현금은 다릅니다. 제품·지역·부문 표를 서로 더하지 않습니다.', ANNUAL[_symbol])]

PUBLIC['EE']['products'][5]['source'] = QUARTER['EE']
for _index in (1, 2, 3, 4, 5):
    PUBLIC['NFE']['brief'][_index]['source'] = ANNUAL['NFE'] if _index < 5 else NFE_CLOSE
for _index in range(6):
    PUBLIC['NFE']['products'][_index]['source'] = ANNUAL['NFE']
PUBLIC['NFE']['products'][-1]['source'] = NFE_CLOSE
PUBLIC['NFE']['segments'] = [fact(r['title'], r['detail'], r['source']) for r in PUBLIC['NFE']['products'][:3]]
PUBLIC['NFE']['financial_context'].append(fact('구조조정 전 실적',
    '2025 연차는2026년 9월 11일 Brazil 분리 전 그룹입니다. 현재 New NFE 자체 연차 수치·구성비로 표시하지 않습니다.', NFE_CLOSE))
PUBLIC['NEXT']['financial_context'].append(fact('건설 단계·매출 표',
    '2025년 연결 손익계산서 41쪽은 매출을 대시로 표시합니다. 개발·건설 중에는 매출을 발생시키지 못한다는 위험 설명도 함께 확인했습니다. 판매 전 단계이므로 제품별 구성비를 만들지 않습니다. 전체 순손실 429,637,000 USD에는 비지배지분 손실 123,203,000 USD가 포함되며 보통주 귀속 손실은 306,434,000 USD입니다.', ANNUAL['NEXT']))
PUBLIC['VG']['brief'].append(fact('최근 프로젝트 단계',
    '8월 11일 기준 Plaquemines Phase 1 COD는 2026 Q4, Phase 2는 2027 중반 목표이며 CP2 첫 LNG는 2027 H2 목표입니다. 현재 시운전 LNG 판매와 최종 COD·예정 확장 FID를 구별합니다.', VG_UPDATE))
PUBLIC['VG']['products'][-1]['source'] = QUARTER['VG']
PUBLIC['VG']['sources'].append(VG_UPDATE)

_PARTIES = [
    ('petrobangla', 'Petrobangla', 'EE', 'customer', ANNUAL['EE'],
     'Bangladesh Oil, Gas & Mineral Corporation이며 Excelerate의 장기 LNG 구매 상대입니다.',
     '15년 SPA의2026/2027 0.85 MTPA와2028–2040 1.0 MTPA는 계약 기간별 수량입니다. 실제 출하·현금 수취와 구별합니다.'),
    ('nepco-jordan', 'National Electric Power Company · Jordan', 'EE', 'customer', EE_UPDATE,
     'Jordan Aqaba 재기화 터미널의 Acadia 9개월 용선 계약 상대입니다.',
     '2026년 5월 계약·7월 초 실제 가동을 발표했습니다. 임시 Jordan 배치와 Iraq 장기 터미널 가동은 다릅니다.'),
    ('puerto-bahia', 'Sociedad Portuaria Puerto Bahia', 'EE', 'customer', EE_UPDATE,
     'Frontera Energy 자회사이며 Colombia 신규 LNG 터미널의 재기화 선박 계약 상대입니다.',
     'Express 7년 용선·연장 옵션,2027 Q1 예상 시작입니다. 미래 Colombia 가동을 이미 완료된 것으로 표시하지 않습니다.'),
    ('prepa', 'Puerto Rico Electric Power Authority', 'NFE', 'customer', ANNUAL['NFE'],
     'Puerto Rico 전력 공공기관으로 NFE의 가스 공급과 Genera PR의 발전 운영·정비 계약 상대입니다.',
     '2025년 12월 7년 가스 공급 계약·연간 최대 75 TBtu와 관리 서비스 역할을 구별합니다. 최대 계약량은 실제 공급량이 아닙니다.'),
    ('cfenergia', 'CFEnergia', 'NFE', 'customer', ANNUAL['NFE'],
     'Mexico Comisión Federal de Electricidad의 자회사로 NFE La Paz 가스 판매 계약 상대입니다.',
     'Baja California Sur 발전소 대상 take-or-pay 공급입니다. 모회사 공공기관 전체와 직접 계약 법인을 구별합니다.'),
    ('genera-pr', 'Genera PR LLC', 'NFE', 'subsidiary', QUARTER['NFE'],
     'NFE의 Puerto Rico 발전 자산 운영·정비 서비스 자회사입니다.',
     'PREPA 계약에서 고정 연간 관리료와 pass-through 비용 환급을 받습니다. 연료 공급·관리 서비스·과거 장비 매각 매출은 별도입니다.'),
    ('energos-infrastructure', 'Energos Infrastructure', 'NFE', 'supplier', ANNUAL['NFE'],
     'NFE가 사용하는 일부 FSRU·LNG선·FSU의 선박 소유·용선 제공자입니다.',
     '연차 fleet 설명의6척은 Energos 소유입니다. 타사 소유 선박을 NFE 완전 소유 자산으로 만들지 않습니다.'),
    ('china-gas', 'China Gas Holdings Limited', 'VG', 'customer', VG_CHINA,
     '홍콩0384.HK 상장 가스·LPG 공급 그룹이며 Venture Global의 장기 LNG 구매 상대입니다.',
     '신규 0.5 MTPA·2030 시작20년 SPA와 전체 2.5 MTPA 계약을 구별합니다. 이 수량은 미래 계약량이며 현재 매출이 아닙니다.'),
    ('kzjv-lng', 'KZJV, LLC', 'VG', 'supplier', ANNUAL['VG'],
     'KBR EPC Member·Zachry Industrial이 소유한 Plaquemines 두 단계의 EPC 계약 LLC입니다. 시공 범위와 장비 OEM 공급을 구별합니다.',
     '실비 환급·목표 가격·일정 인센티브 계약입니다. 프로젝트 연결 매출이나 자체 LNG 판매 회사로 표시하지 않습니다.'),
    ('cbi-lng', 'CB&I · LNG 저장탱크', 'VG', 'supplier', ANNUAL['VG'],
     'Plaquemines 액화 프로젝트의 LNG 저장탱크 제공·시공 역할입니다.',
     '장비·시공 역할 설명이며 상장 LNG 발행기업의 자회사나 가스 고객으로 표시하지 않습니다.'),
    ('nfe-brazil-holdings', 'NFE Brazil Holdings Limited', 'NFE', 'transaction', NFE_CLOSE,
     'Bermuda 법인으로9월 11일 Brazil 사업 분리 계약과 전환 서비스 계약의 실명 상대입니다.',
     'Bradford County Holdings와 Brazil TopCo 범위를 구성하며 분리 후 독립 기업입니다. 현재 New NFE 완전소유 자회사로 표시하지 않습니다.'),
]
PRIVATE, EDGES = {}, {s: [] for s in SYMBOLS}
for _key, _name, _symbol, _kind, _origin, _business, _role in _PARTIES:
    PRIVATE[_key] = profile(_name, _origin, _business, _role,
        customers='여기서는 확인된 LNG 사업 관계를 설명합니다. 상대 회사 전체 매출·익명 고객을 추정하지 않습니다.')
    EDGES[_symbol].append(relation(_name, None, _kind, _role, _origin, _key))

EDGES['EE'] += [
    relation('QatarEnergy', None, 'supplier', '2026 시작 LNG 구매 SPA·Petrobangla 판매와 back-to-back 가격 조건. 계약량은 실제 도착 물량이 아님.', ANNUAL['EE'], 'qatarenergy'),
    relation('HD Hyundai Heavy Industries', None, 'supplier', '170,000m³ FSRU 건조·2026 Q2 인도 완료. Iraq 터미널의 실제 가동 완료와 별도.', QUARTER['EE'], 'hyundai-heavy-dorian'),
    relation('New Fortress Energy', 'NFE', 'transaction', 'Jamaica 사업 2025년 5월 실제 취득·처분 완료. 전체 NFE 인수나 현재 모회사 관계가 아님.', ANNUAL['EE']),
]
EDGES['NFE'].append(relation('Excelerate Energy', 'EE', 'transaction',
    '2025년 5월 Jamaica 사업 처분 완료. 사업 매각 상대와 현재 고객/모회사를 구별.', ANNUAL['NFE']))
EDGES['NEXT'] += [
    relation('Bechtel', None, 'supplier', 'Bechtel Energy Inc.의 Rio Grande Trains 1–5 EPC 설계·조달·시공. 첫 LNG2027 H1 예상.', NEXT_UPDATE, 'bechtel'),
    relation('Honeywell', 'HON', 'supplier', 'AP-C3MR 액화 기술. 브랜드·기술 제공과 전체 EPC/원료 공급 역할을 구별.', ANNUAL['NEXT']),
    relation('Baker Hughes', 'BKR', 'supplier', 'Train 6 주 냉매 압축기 reservation 계약. 발주 준비를 실제 납품·FID·가동 완료로 표시하지 않음.', NEXT_UPDATE),
    relation('TotalEnergies', 'TTE', 'customer', 'Phase 1·Train 4 장기 LNG 구매 계약. 분기 공시의 프로젝트 투자·상장사10%초과 지분과 판매 계약 역할을 구별.', QUARTER['NEXT']),
    relation('TotalEnergies', 'TTE', 'partner', 'Phase 1·Train 4 프로젝트 출자·신용 지원의 관련자 역할. 현금 분배율·상장사 지분율·매출을 구별.', QUARTER['NEXT']),
]
EDGES['VG'] += [
    relation('Baker Hughes', 'BKR', 'supplier', '장기 master agreement의 액화/전력 장비·생산능력 예약·개별 purchase order. 실제 장비 인도는 별도.', ANNUAL['VG']),
    relation('Honeywell', 'HON', 'supplier', 'UOP의 Plaquemines 가스 전처리 설비 공급 역할. 그룹 매출 전체가 이 계약 매출인 것은 아님.', ANNUAL['VG']),
    relation('WhiteWater', None, 'partner', 'Blackfin 가스 파이프라인 공동 개발. LNG 판매 고객·VG 완전소유 자회사와 다른 역할.', ANNUAL['VG'], 'whitewater'),
    relation('BP', 'BP', 'customer', 'BP Gas Marketing의 post-COD SPA·중재.2025 책임 판단과2027년 5월 손해 심리 예정은 확정 손해 지급과 다름.', QUARTER['VG']),
]
PRIVATE['genera-pr']['relations'].append(relation('Puerto Rico Electric Power Authority', None,
    'customer', '화력 자산 운영·정비의 고정 관리료·비용 환급 계약 상대.', QUARTER['NFE'], 'prepa'))

COMMON_CONTEXT = {
    'bechtel': [fact('Rio Grande LNG EPC', 'NextDecade Trains 1–5의 계약 시공자는 Bechtel Energy Inc.입니다. 기존 Cheniere 사업과 별도 프로젝트이며 첫 LNG2027 H1 예상입니다.', NEXT_UPDATE)],
    'qatarenergy': [fact('Excelerate LNG 공급', '2026부터 LNG 공급 SPA와 Petrobangla 판매 back-to-back 계약을 연결합니다. 다른 공동사업 지분·현재 인도·매출과 구별합니다.', ANNUAL['EE'])],
    'hyundai-heavy-dorian': [fact('Excelerate FSRU 실제 인도', '170,000m³ 재기화 터미널 선박을 2026 Q2 인도했습니다. 조선소 인도와 Iraq 2027 예상 가동은 다른 사건입니다.', QUARTER['EE'])],
    'whitewater': [fact('Blackfin LNG 원료 수송', 'Venture Global과 Blackfin 가스 파이프라인을 공동 개발합니다. 기존 Eiger·MXP 사업과 다른 프로젝트 범위입니다.', ANNUAL['VG'])],
}
COMMON_CONTEXT = {key: {'brief': notes} for key, notes in COMMON_CONTEXT.items()}
