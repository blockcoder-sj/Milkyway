"""Issuer-specific MLP operating notes, not duplicated copies of a network.

All figures preserve their own legal entity, accounting scope and report date.
Project agreements do not prove a supplier's complete customer list.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

EPD, ET, MPLX, PAA, PAGP, WES, HESM = (
    report(s) for s in ('EPD', 'ET', 'MPLX', 'PAA', 'PAGP', 'WES', 'HESM'))
EPD_Q, ET_Q, MPLX_Q, PAA_Q, PAGP_Q, WES_Q, HESM_Q = (
    report(s, 'quarter') for s in ('EPD', 'ET', 'MPLX', 'PAA', 'PAGP', 'WES', 'HESM'))
EPD_RESULTS = source('Enterprise · 2026년 2분기 운영·개발 현황',
    'https://ir.enterpriseproducts.com/node/45311', '2026-07-30')
ENTERGY = source('Energy Transfer·Entergy Louisiana · 확정 가스 운송 계약',
    'https://ir.energytransfer.com/news-releases/news-release-details/entergy-louisiana-and-energy-transfer-sign-agreement-supports', '2025-11-04')
CLOUD = source('Energy Transfer·CloudBurst · 조건부 가스 공급 계약',
    'https://ir.energytransfer.com/news-releases/news-release-details/energy-transfer-and-cloudburst-sign-agreement-natural-gas-supply/', '2025-02-10')
ET_RESULTS = source('Energy Transfer · 2026년 2분기 연결·운영 현황',
    'https://ir.energytransfer.com/news-releases/news-release-details/energy-transfer-reports-second-quarter-2026-results-and-updates/', '2026-08-04')
MPLX_RESULTS = source('MPLX · 2026년 2분기 개발 현황',
    'https://ir.mplx.com/CorporateProfile/press-releases/news-release/2026/MPLX-LP-Reports-Second-Quarter-2026-Financial-Results/default.aspx', '2026-08-04')
WES_RESULTS = source('Western Midstream · 2026년 2분기 자산·생산수 처리',
    'https://www.westernmidstream.com/press-release-356/', '2026-08-05')
NAVIGATOR = source('Navigator Gas · Enterprise 에틸렌 수출 공동사업',
    'https://investors.navigatorgas.com/news/news-details/2026/Navigator-Gas-Announces-Preliminary-Second-Quarter-2026-Results-Unaudited/', '2026-08-04')

PUBLIC = {
    'EPD': profile('Enterprise Products Partners', EPD,
        '천연가스·NGL·원유·석유화학·정유제품을 집하·처리하고 운송·분별·저장·수출·판매로 연결하는 북미 물류 MLP입니다. 생산지 가스의 NGL 회수부터 Mont Belvieu 분별·Gulf 수출까지 네트워크로 이어집니다.',
        '2025년 내부거래 제거 후 매출 525억9,600만 달러는 NGL 173억1,600만, 원유 207억6,100만, 천연가스 41억6,700만, 석유화학·정유제품 103억5,200만 달러입니다. 내부 거래를 포함한 부문 매출 1,841억3,600만 달러를 외부 매출로 사용하지 않습니다.',
        [('NGL 가치사슬', '혼합 NGL을 배관으로 운송하고 에탄·프로판·부탄·천연가솔린으로 분리해 석유화학·연료·수출 고객에 연결합니다.'),
         ('원유 공급·수출', '생산지 원유를 모아 품질별로 관리하고 배관·저장·터미널로 정유소·해외 구매자에 연결합니다. 운송료와 원유 재판매를 구분합니다.'),
         ('천연가스 운송·처리', '집하·처리·간선·저장·판매를 제공합니다. 고정 수수료 외 keep-whole·제품 비율·판매대금 비율 계약도 있습니다.'),
         ('석유화학·정유제품', '프로필렌 생산, 부탄 이성화·옥탄 향상, 에틸렌 수출, 연료 배관·터미널·내륙 해상 운송을 운영합니다.')],
        customers='생산자는 집하·처리·운송 고객이며 정유·석유화학·LPG·수출 구매자는 제품·물류 고객입니다. Oxy의 Midland 가스 집하·처리는 전용 생산 면적에 연결되는 실제 장기 고객 관계입니다.',
        inputs='상품 매입, 가스 처리·분별의 연료·전력, 파이프·펌프·압축기·탱크·선적 설비·시공·정비가 필요합니다. 원료 매매와 수수료 사업의 비용 구조는 다릅니다.',
        competition='생산지 접근, 하류 연결·저장·수출 능력과 처리 조건이 경쟁 범위입니다. 원유·가스·NGL·석유화학의 시장과 대체 경로가 다릅니다.'),
    'ET': profile('Energy Transfer', ET,
        '가스 집하·처리·주내·주간 운송·저장, NGL·연료·원유 물류·판매를 연결하는 MLP입니다. Sunoco의 연료 유통·해외 사업과 USA Compression의 압축 서비스를 연결 재무에 포함합니다.',
        '2025년 연결 매출 855억3,600만 달러의 외부 부문은 가스 주내 수송 35억4,400만, 주간 수송 24억1,600만, 집하·처리 33억5,600만, NGL·연료 211억8,300만, 원유 264억7,900만, Sunoco 251억7,800만, 압축 9억3,300만, 기타 24억4,700만 달러입니다.',
        [('가스 생산지·간선망', '유정 집하·처리에서 파이프라인·저장으로 이어집니다. 확정 용량 요금·실제 수송료·가스 판매와 상품 노출을 구별합니다.'),
         ('NGL·정유제품', '분별·배관·저장·터미널·수출과 관련 제품 판매입니다. Nederland·Marcus Hook 등 수출 거점과 지역 연료 수요를 연결합니다.'),
         ('원유 집하·수송·판매', '생산지 원유를 간선·저장·Gulf 정유·수출 시장에 연결합니다. 원유 판매액을 운송료로 해석하지 않습니다.'),
         ('연결된 유통·압축', 'Sunoco와 USA Compression은 별도 상장 사업입니다. 두 회사 매출을 Energy Transfer 전체 매출에 다시 더하지 않습니다.')],
        customers='생산자·도시가스·발전·산업·정유·석유화학·수출 고객입니다. Entergy Louisiana는 장래 확정 운송 상대이며 Shell은 기존 Lake Charles 재기화 고객입니다.',
        inputs='상품 매입, 압축·펌프 전력·연료, 처리약품·설비·시공·정비·터미널 운영이 필요합니다. 처리·운송·저장·선적은 같은 가치사슬 안에 연결됩니다.',
        competition='같은 생산지·수요처를 연결하는 대체 집하·처리·수송·저장·수출 경로가 경쟁 범위입니다. 공동 배관 참여와 회사 전체의 공급 관계를 구별합니다.'),
    'MPLX': profile('MPLX', MPLX,
        'Marathon Petroleum이 후원하는 물류 MLP입니다. 원유·정유제품 물류와 천연가스·NGL 서비스 두 부문으로 정유소 탱크·배관·터미널·선박부터 생산지 가스 집하·처리·분별까지 다룹니다.',
        '2025년 고객 계약 매출 97억2,600만 달러는 원유·정유제품 물류 48억4,000만, 가스·NGL 48억8,600만 달러입니다. 임대·지분법 이익·투자 손익 등 비ASC 606 항목 32억7,200만을 포함한 매출·기타수익 129억9,800만 달러와 범위가 다릅니다.',
        [('정유 물류', 'Marathon 정유소의 원료·제품을 배관·탱크·터미널·선박으로 연결하고 운송·저장·운영·연료 유통 서비스를 제공합니다.'),
         ('가스·NGL 생산지', '가스를 집하·압축·처리하고 NGL을 분별·운송·저장·판매합니다. sour gas 처리·산성 가스 주입도 운영합니다.'),
         ('장거리 연결', 'Whistler·Matterhorn·Eiger 공동사업과 BANGL 등이 Permian을 Gulf 수요 거점에 연결합니다. 프로젝트별 지분·운영·건설 단계가 다릅니다.'),
         ('LPG 수출 개발', 'ONEOK와 Texas City 터미널·배관을 개발합니다. 예정 수출능력은 현재 판매량이 아닙니다.')],
        customers='2025년 Marathon은 주요 비현금 항목 제외 매출·기타수익 약 48%, 원유·정유제품 물류 부문 약 88%였습니다. 모회사 소유 지분이나 고객 계약 매출 비율과 같은 수치가 아닙니다.',
        inputs='생산·정유 물량, 압축·처리·분별의 연료·전력·배관·설비·정비·선박이 필요합니다. 제품 매매와 sour gas 처리·주입 비용은 수수료 물류와 다릅니다.',
        competition='동일 생산지·정유소·하류 시장의 집하·처리·분별·물류 서비스가 경쟁 범위입니다. 모회사 정유 물류와 외부 생산자 가스 사업을 구별합니다.'),
    'PAA': profile('Plains All American Pipeline', PAA,
        '북미 원유를 집하·구매하고 배관·터미널·저장·수출·판매로 연결하는 MLP입니다. Permian·Cushing·Gulf 정유·수출 거점이 핵심이며 Canadian NGL 사업은 2026년 매각됐습니다.',
        '2025년 계속사업 연결 매출 442억6,200만 달러는 제품 판매 425억100만과 서비스 17억6,100만 달러입니다. 원유 재판매액을 운송료나 시장점유율로 사용하지 않습니다. Canadian NGL은 중단사업으로 따로 보고했습니다.',
        [('원유 공급·판매', '생산자 물량·품질을 모아 정유·수출 구매자에 공급합니다. 원유 가격·품질·지역 차익과 운송·저장 비용을 구별합니다.'),
         ('장거리 배관·터미널', 'Permian에서 Corpus Christi·Houston·Cushing으로 연결하고 저장·환적·선적·품질 관리를 제공합니다.'),
         ('미국 잔존 NGL', '미국 남서부 저장·터미널·일부 상품 거래가 남습니다. 매각된 캐나다 분별·배관망을 현재 보유망으로 표시하지 않습니다.'),
         ('공동 배관', 'Cactus II·BridgeTex·Capline·Wink to Webster의 소유와 운영사가 다릅니다. 전체 능력과 지분 귀속 능력을 구분합니다.')],
        customers='2025년 ExxonMobil 계열이 매출 약 31%였으며 주로 여러 지역의 원유 재판매입니다. BP의 10%는 2023년 수치이며 현재 비중이 아닙니다. 장기 수송·전용 면적 약정도 있습니다.',
        inputs='원유·제품 매입, 품질 분리·혼합, 펌프 전력·연료, 배관·탱크·철도·트럭·선박·정비가 필요합니다. 상품·신용·헤지와 물리적 인도 능력을 구별합니다.',
        competition='생산지 공급 집하·고객 접근·수송 경로·저장·품질·요금이 경쟁 조건입니다. 지역·품질 가격 차이를 전체 원유 가격 방향과 동일하게 보지 않습니다.'),
    'PAGP': profile('Plains GP Holdings', PAGP,
        'Plains All American 운영망에 간접 경제적 지분과 지배 구조로 연결되는 별도 상장 지주회사입니다. PAA와 다른 원유 네트워크를 하나 더 운영하는 회사가 아닙니다.',
        '2025년 계속사업 연결 매출 442억6,200만 달러는 연결된 PAA 운영 사업의 상품 판매·서비스에서 발생합니다. PAGP와 PAA는 별도 증권이나 두 매출·배관 능력을 산업 합계에 중복 더하면 안 됩니다.',
        [('운영 사업 연결', 'PAA의 원유 집하·수송·저장·터미널·판매와 미국 잔존 NGL 사업을 연결합니다.'),
         ('Class A 경제적 대응', 'Class A 주식·AAP 지분·귀속 PAA units 사이 일대일 경제적 대응을 유지합니다.'),
         ('지배·귀속·과세', '연결 재무가 모든 이익의 100% 귀속을 뜻하지 않습니다. 비지배 지분·법인 과세와 상장 구조 차이를 구별합니다.')],
        customers='제품과 물류를 구매하는 운영 고객은 PAA의 고객입니다. PAGP 투자자는 원유 구매 고객과 다른 역할입니다.',
        inputs='물리적 상품·물류 비용은 연결 운영 사업에서 발생합니다. 지주 구조의 관리·자금·세금과 실제 배관 비용을 분리합니다.',
        competition='경쟁 범위는 연결 PAA의 원유 공급·물류와 같습니다. PAGP와 PAA를 서로의 원유 공급 경쟁사로 표시하지 않습니다.'),
    'WES': profile('Western Midstream Partners', WES,
        '생산지 천연가스·원유·NGL·생산수를 집하·처리·운송하는 MLP입니다. Delaware·DJ·Powder River 등에서 운영하며 2025년 Aris·2026년 Brazos Delaware를 편입했습니다.',
        '2025년 실제 고객 매출 38억4,159만9,000 달러는 수수료 서비스 34억5,305만2,000, 상품 기반 서비스 1억9,386만6,000, 제품 1억9,468만1,000입니다. 기타 180만4,000을 더한 매출·기타수익 38억4,340만3,000 달러는 Aris 연초 편입 가상 pro forma와 다릅니다.',
        [('가스 집하·처리', '유정 가스를 압축·탈수·처리해 NGL을 회수하고 판매·간선망에 연결합니다. 고정 수수료와 제품 비율·고정 회수 계약의 노출이 다릅니다.'),
         ('원유·콘덴세이트', '원유·콘덴세이트·NGL을 집하·안정화·수송해 터미널·간선·정유소에 연결합니다.'),
         ('생산수·재사용', '생산수를 집하·운송·처리·재활용·공급·폐기합니다. 주입 허가·지질·처리·고객 물 수요가 비용과 수익에 연결됩니다.'),
         ('새 처리수 용도', '산업 냉각·관개 등에 맞게 정제하는 실증은 유정 내 재활용과 다릅니다. 실증시설은 상업 규모 공장이 아닙니다.')],
        customers='Occidental과 외부 생산자에게 서비스를 제공합니다. West Texas의 2025년 Oxy 43%는 해당 complex 처리량 비중이지 회사 매출 비중이 아닙니다. ConocoPhillips의 가스 집하·처리 계약도 확인됩니다.',
        inputs='전력·연료·약품·압축·처리·펌프·배관·주입 설비·시공·정비가 필요합니다. 물 처분 용량·허가·재활용과 새 용도 개발 투자가 관련됩니다.',
        competition='동일 생산지의 대체 집하·처리·물 시설과 위치·용량·요금·허가·신뢰성으로 경쟁합니다. 가스·원유·생산수의 단위를 합산하지 않습니다.'),
    'HESM': profile('Hess Midstream', HESM,
        'Bakken·Three Forks의 가스·원유·생산수 집하, 가스 처리·NGL 분별·저장·원유 터미널·철도 출하를 제공하는 수수료 사업입니다. Hess 인수 후 Chevron이 현재 후원사·주요 거래 상대입니다.',
        '2025년 부문 매출은 집하 8억7,060만, 처리·저장 6억2,000만, 터미널·출하 1억3,070만 달러로 합계 16억2,130만입니다. 고객 계약 매출 16억1,720만은 관계사 15억7,360만과 제3자 4,360만 달러로 회계 범위가 다릅니다.',
        [('생산지 집하', '가스·원유·생산수를 집하·압축·처리·운송합니다. 가스 Mcf·원유와 물 배럴별 요금·최소 물량을 적용합니다.'),
         ('가스 처리·NGL', '가스를 정제하고 NGL을 회수·분별합니다. Little Missouri 4는 Targa 운영·각 50% 공동사업입니다.'),
         ('저장·터미널·철도', '원유·프로판 저장과 송유관·철도·트럭으로 출하합니다. 철도는 차량 수뿐 아니라 왕복 회전 일수도 제약입니다.'),
         ('최소 물량 계약', 'Chevron 지명량의 80%를 3년 rolling MVC로 설정하고 미달량×요금의 대가를 받습니다. 약정은 실제 처리량이 아닙니다.')],
        customers='2026년 2분기·상반기 Chevron 수수료 계약이 매출의 95%입니다. Chevron이 계약해 전달하는 제3자 물량도 포함하므로 직접 생산 물량 비중과 다릅니다.',
        inputs='압축·처리·분별·펌프 전력·연료·배관·설비·정비·확장 투자입니다. LM4에 처리료·비례 전력비를 지급하고 Chevron은 운영·행정·파견 서비스를 제공합니다.',
        competition='Bakken 내 물량 확보를 위한 집하·처리·저장·출하가 경쟁 범위입니다. 전용 면적·MVC가 있으므로 단기 원유 가격만으로 수수료를 설명하지 않습니다.'),
}

# A later quarter, not the annual report, supports these updated statements.
PUBLIC['WES']['description_source'] = WES_Q
for _symbol, _title, _origin in [('WES', '무엇을 하는 기업인가', WES_Q),
                               ('HESM', '고객·판매 경로', HESM_Q)]:
    for _item in PUBLIC[_symbol]['brief']:
        if _item['title'] == _title:
            _item['source'] = _origin

_OPERATIONS = {
    'EPD': [
        ('Bahia·Cowboy 연결', 'Bahia는 2025년 12월 가동·ExxonMobil 지분 40% 매각 완료. 하루 60만 배럴을 100만으로 확대하고 Cowboy에서 92마일 연장, 2027년 4분기 목표입니다. Enterprise는 기존 Bahia 60%·연장 30%·운영 역할을 갖습니다.', EPD),
        ('Oxy 실제 집하 고객', '2025년 8월 22일 Midland 집하 자산 약 200마일을 5억8,100만 달러에 인수하고 Oxy 약 73,000에이커·4개 county를 장기 집하·처리합니다. 매도자와 현재 서비스 고객이 겹칩니다.', EPD),
        ('수출 가동·개발 구분', 'Neches River 2단계는 2026년 5월 가동했습니다. 새 가스 공장 각 하루 300 MMcf 두 곳과 Frac 15 하루 15만 배럴은 2분기 승인한 계획이며 현재 처리량에 더하지 않습니다.', EPD_RESULTS),
        ('에틸렌 수출 공동사업', 'Morgan’s Point 터미널은 Navigator와 각 50% 공동사업입니다. 명목 선적능력과 실제 선적량, 저장 파운드와 선적 톤을 구별합니다.', EPD),
    ],
    'ET': [
        ('Lake Charles 현재 역할', '기존 LNG 수입·재기화는 저장 약 9 Bcf·송출 하루 1.8 Bcf이며 Shell 장기 계약에서 매출이 발생합니다. 별도 액화·수출 개발은 2025년 12월 중단돼 LNG 수출 생산설비로 표시하지 않습니다.', ET),
        ('Entergy 발전 연료 경로', '2025년 11월 계약은 2028-02–2048-01 초기 하루 250,000 MMBtu 확정 운송입니다. Tiger 약 12마일·최대 하루 1 Bcf 지선을 개발합니다. 직접 고객은 Entergy Louisiana이며 Meta는 하류 전력 수요처입니다.', ENTERGY),
        ('CloudBurst 조건부 약정', '최대 하루 450,000 MMBtu·최소 10년의 Oasis 공급은 고객 FID 조건부입니다. 2025년 발표의 예정일을 완료 증거 없이 현재 가동으로 표시하지 않습니다.', CLOUD),
        ('유통·압축 연결 범위', '2026년 2분기 발표는 Sunoco common/Class D 약 15%, USA Compression common 약 32%와 일반 파트너·관리 지배를 공시합니다. 과거 지분율과 현재 지배를 구별합니다.', ET_RESULTS),
        ('Bayou Bridge', 'Phillips 66 공동 원유 배관은 ET 60%·운영, Nederland–Lake Charles–St. James 명목 하루 약 48만 배럴입니다. 지분율과 실제 수송량은 다릅니다.', ET),
    ],
    'MPLX': [
        ('정유 물류 자산', '2025년 말 전체·공동 소유 배관 14,853마일, 정유소 물류 13곳, 터미널 88곳입니다. 공동 소유 길이를 전부 100% 소유로 읽지 않습니다.', MPLX),
        ('처리 단계와 단위', '2025년 말 가스 집하 하루 9.4 Bcf·처리 11.2 Bcf, 분별·탈에탄 하루 819,000배럴입니다. 같은 생산물이 여러 단계를 지나므로 합산하지 않습니다.', MPLX),
        ('신규 편입 사업', '2025년 Northwind·BANGL·Whiptail을 편입해 sour gas 처리·산성 가스 주입·NGL 운송망을 확장했습니다. 인수 대가는 매출이 아닙니다.', MPLX),
        ('최근 개발 현황', '2026년 8월 발표 당시 Harmon Creek III는 8월 개시 예정이며 sour gas·장거리 가스·LPG 수출 개발을 진행했습니다. 후속 준공 확인 없는 예정일을 실제 가동일로 바꾸지 않습니다.', MPLX_RESULTS),
    ],
    'PAA': [
        ('Canadian NGL 매각 완료', 'Keyera 매각은 2026년 5월 12일 완료됐습니다. 분기 공시 대가 CAD 53억2,800만은 약 USD 38억8,300만이며 현금·운전자본·후속 조정을 포함합니다. 현재 남은 NGL은 미국 사업입니다.', PAA_Q),
        ('부문·내부거래', '2025년 원유 441억3,100만·NGL 1억5,100만에서 내부거래 2,000만 달러를 제거하면 계속사업 연결 442억6,200만입니다. 고객 계약·전체 매출·중단사업을 구별합니다.', PAA),
        ('공동 수송 경로', 'Cactus II 명목 하루 67만 배럴은 PAA 70%·Enbridge JV, BridgeTex 하루 44만은 PAA 40%·ONEOK 계열 운영입니다. 전체 능력과 지분 귀속량은 다릅니다.', PAA),
        ('원유 품질·물류', '경질·중질·황 함량과 정유소 설비마다 원료 선호가 다릅니다. 집하·품질 분리·저장·수송으로 지역 공급·정유 수요 불균형을 연결합니다.', PAA),
    ],
    'PAGP': [
        ('PAA 자산의 중복 방지', 'Class A 주식은 AAP를 통해 귀속 PAA units에 일대일 대응합니다. 두 상장 증권을 탐색하되 원유·물류·매출을 중복 합산하지 않습니다.', PAGP),
        ('운영 범위 변화', 'PAA의 Canadian NGL 매각은 PAGP의 연결 범위에도 반영됩니다. 2026년 5월 완료 후 이를 현재 자회사 사업으로 남기지 않습니다.', PAGP_Q),
    ],
    'WES': [
        ('실적과 인수 가상치', 'Aris는 2025년 10월 15일부터 연결됩니다. 연초 편입 가정의 2025년 pro forma 매출·기타수익 42억8,174만4,000 달러는 실제 보고 실적이 아닙니다.', WES),
        ('Brazos 편입 완료', '2026년 6월 11일 Brazos Delaware 인수를 완료했습니다. 2분기 발표의 처리능력 추가는 하루 약 460 MMcf입니다. 인수 자산 전체와 분기 기여 기간을 구분합니다.', WES_RESULTS),
        ('실제 고객 계약 변경', '2026년 Oxy 가스 집하를 cost-of-service에서 고정 수수료로 전환하고 MVC를 2027년 말까지 추가했습니다. ConocoPhillips의 기존 시스템 가스도 처리하며 관련 Oxy units 상환은 2월 완료했습니다.', WES_Q),
        ('물 실증·건설', 'JIP 2는 2026년 2분기 가동·하루 약 1,000배럴 회수 담수입니다. Pathfinder는 2027년 1분기, North Loving II는 2분기 예정이며 실증·건설·상업 규모를 구별합니다.', WES_RESULTS),
    ],
    'HESM': [
        ('현재 후원사', 'GIP는 2025년 5월 30일 전부 매각, Chevron의 Hess 인수는 7월 18일 완료됐습니다. Hess 계약은 유지되며 현재 상대·후원사는 Chevron 계열입니다.', HESM),
        ('계약 기간·요금', '일부 주요 계약은 2024–2033년 추가 10년으로 연장됐습니다. 물·특정 집하 기간은 별도이며 연간 재산정·최대 3% 물가 조정 조건을 일괄 고정 요금으로 단순화하지 않습니다.', HESM_Q),
        ('LM4 실제 처리', 'Little Missouri 4는 명목 하루 200 MMcf·각 50%·Targa 운영입니다. HESM이 처리료·비례 전력비를 지급하며 공동 손익·배당도 받습니다.', HESM_Q),
        ('고객 집중 범위', '2026년 2분기·상반기 Chevron 수수료 계약 95%에는 Chevron 계약으로 전달된 제3자 물량도 포함합니다. 직접 생산량이나 소유 지분율과 다릅니다.', HESM_Q),
    ],
}
for _symbol, _rows in _OPERATIONS.items():
    PUBLIC[_symbol]['segments'] = [fact(*row) for row in _rows]
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']

_DRIVERS = {
    'EPD': [('처리·수출 연결', '생산지 물량과 처리·분별·운송·선적 능력이 맞아야 인도합니다. 수수료·상품 마진·파생상품 평가손익을 구별합니다.'), ('원가·확장 투자', '매입 상품·전력·연료·정비와 신규 처리·분별·수출·배관 건설을 나눕니다.')],
    'ET': [('가격과 확정 운송', '상품 매출·매입 원가는 가격·판매량, 확정 운송은 용량·요율·신용·가동과 관련됩니다.'), ('계획과 운영', '발전·데이터센터 계약의 조건·시공·허가·가동일을 확인합니다. 중단한 수출 개발의 과거 약정을 미래 생산으로 보지 않습니다.')],
    'MPLX': [('정유·생산지 활동', 'Marathon 가동·물류 약정과 생산자의 시추·가스 성분·집하·처리량은 서로 다른 수익 경로입니다.'), ('회계 범위', '수수료·제품 거래·임대·비연결 JV 손익이 다릅니다. 매출과 EBITDA를 합치지 않습니다.')],
    'PAA': [('품질·지역·운임', '공급·정유 수요·원유 품질·배관·저장 여유·운송비가 거래 마진과 물량에 연결됩니다.'), ('신용·헤지·인도', '대규모 재판매는 운전자본·신용·헤지·평가와 실제 인도 능력이 필요합니다.')],
    'PAGP': [('연결과 귀속', 'PAA 전체 매출과 PAGP 주주 귀속 이익이 다릅니다. 비지배·세금·지주 비용을 구별합니다.')],
    'WES': [('물 처분·재사용', '물량·주입 허가·압력·지진 관련 제한·처리·재활용과 새 용도 검증이 관련됩니다.'), ('계약별 노출', '고정 요금·MVC와 상품 기반·고정 회수 계약의 노출이 다릅니다. 인수 가상치를 실제 실적으로 사용하지 않습니다.')],
    'HESM': [('개발계획·MVC', '개발계획은 장래 최소 약정, 미달 대가·요금 재산정과 연결됩니다. 실제 처리를 구별합니다.'), ('설비·철도 회전', '가스 성분·압축·LM4 전력비와 배관·철도 회전 주기가 활용에 연결됩니다.')],
}
for _symbol, _rows in _DRIVERS.items():
    PUBLIC[_symbol]['drivers'] = [fact(title, detail, report(_symbol)) for title, detail in _rows]

EDGES = {
    'EPD': [
        relation('ExxonMobil', 'XOM', 'partner', 'Bahia NGL·Cowboy 처리공장 연결 JV · 2025-12 지분 거래 완료·확장과 연장은 2027년 4분기 목표', EPD),
        relation('Occidental Petroleum', 'OXY', 'customer', 'Midland 가스 집하·처리 장기 계약 · 약 73,000에이커 전용, 2025-08-22 자산 편입과 연계', EPD),
        relation('Navigator Holdings', 'NVGS', 'partner', 'Morgan’s Point 에틸렌 수출 터미널 각 50% · 선박 운송·육상 수출 연결', NAVIGATOR),
        relation('HF Sinclair', 'DINO', 'customer', 'Navajo로 NGL 등을 운송하는 공동이용 배관 · 원료 매도인으로 단정하지 않음', report('DINO')),
        relation('Seaway Crude Holdings', None, 'partner', 'Cushing–Gulf 원유 배관·저장·수출 · Enterprise 50% 지분법 사업', EPD, 'seaway'),
        relation('Seaway Crude Holdings', None, 'supplier', 'Enterprise 원유 판매 사업에 운송·저장 서비스 제공 · 2025년 지급액 2,600만 달러, 지분법 이익과 별도', EPD, 'seaway'),
    ],
    'ET': [
        relation('Phillips 66', 'PSX', 'partner', 'Bayou Bridge 원유 배관 · ET 60%·운영, Texas–Louisiana 정유·수출 연결', ET),
        relation('Entergy', 'ETR', 'customer', 'Entergy Louisiana 확정 가스 수송 · 초기 하루 250,000 MMBtu, 2028-02–2048-01 · 직접 계약 상대', ENTERGY),
        relation('CloudBurst Data Centers', None, 'customer', 'Oasis 최대 하루 450,000 MMBtu 약정 · 고객 FID 조건부·가동 완료 미확인', CLOUD, 'cloudburst'),
        relation('Shell', 'SHEL', 'customer', 'Lake Charles 기존 LNG 수입·재기화 장기 이용 · 중단한 액화·수출 개발과 별도', ET),
        relation('Sunoco', 'SUN', 'subsidiary', '연료 유통·배관·터미널 상장 연결 MLP · ET-S Permian·J.C. Nolan 공동 운영도 있음', ET),
        relation('USA Compression Partners', 'USAC', 'subsidiary', '가스 압축 상장 연결 MLP · 지배와 common 소유율은 별도', ET_RESULTS),
        relation('SunocoCorp', 'SUNC', 'subsidiary', 'Sunoco 경제적 지분에 연결된 상장 법인 · 별도의 두 번째 연료망으로 합산하지 않음', ET_RESULTS),
    ],
    'MPLX': [
        relation('Marathon Petroleum', 'MPC', 'customer', '정유 물류·저장·선박·유통·운영 수수료 · 2025년 주요 비현금 항목 제외 매출·기타수익 48%, 원유·제품 물류 88%', MPLX),
        relation('Marathon Petroleum', 'MPC', 'supplier', 'MPLX에 IT·엔지니어링·법무·회계·자금·인사·행정 서비스 제공 · 정유 물류 구매 역할과 별도', MPLX),
        relation('Marathon Petroleum', 'MPC', 'parent', '2025년 말 약 64% common units·GP 지배 · 주요 실제 고객 역할과 별도', MPLX),
        relation('Targa Resources', 'TRGP', 'partner', 'Centrahoma 처리 JV 비운영 40% · Blackcomb 참여는 별도 프로젝트', report('TRGP')),
        relation('ONEOK', 'OKE', 'partner', 'Texas City LPG 터미널·관련 배관 각 50% 공동 개발 · Eiger에도 별도로 참여', report('OKE')),
        relation('WhiteWater', None, 'partner', 'Eiger 가스 간선 개발·건설·운영 연결 · 프로젝트별 지분·참여사 구별', report('OKE'), 'whitewater'),
        relation('Enbridge', 'ENB', 'partner', 'Whistler·Rio Bravo를 연결하는 WPC 공동사업 · Eiger 참여는 별도', MPLX),
        relation('HF Sinclair', 'DINO', 'customer', 'Woods Cross 정유소 제품 출하 배관 서비스 · 하류 운송 경로', report('DINO')),
        relation('Northwind Midstream', None, 'subsidiary', '2025년 편입 · Permian sour gas 집하·처리·산성 가스 주입', MPLX, 'northwind-midstream'),
        relation('BANGL', None, 'subsidiary', '2025년 잔여 지분 취득 · Permian–Gulf NGL 운송', MPLX, 'bangl'),
    ],
    'PAA': [
        relation('ExxonMobil', 'XOM', 'customer', '2025년 계속사업 매출 약 31% · 여러 지역 원유 재판매, 운송료 비중 아님', PAA),
        relation('ONEOK', 'OKE', 'partner', 'BridgeTex · PAA 40%, ONEOK 계열 운영, 명목 하루 약 440,000배럴', PAA),
        relation('Enbridge', 'ENB', 'partner', 'Cactus II 공동 원유 배관 · PAA 70%·운영, 명목 하루 약 670,000배럴', PAA),
        relation('Marathon Petroleum', 'MPC', 'partner', 'Capline · PAA 약 54%·Marathon 계열 운영, Patoka–St. James', PAA),
        relation('Plains GP Holdings', 'PAGP', 'parent', '지배·간접 경제적 지분으로 연결 · 별도 상장 증권, 자산·매출 중복 금지', PAGP),
        relation('Keyera', None, 'partner', '자산 거래 상대: Canadian NGL 매각 2026-05-12 완료 · 현재 공급 계약·JV로 추정하지 않음', PAA_Q, 'keyera'),
    ],
    'PAGP': [relation('Plains All American Pipeline', 'PAA', 'subsidiary', 'AAP를 통한 경제적 지분·연결 사업 · 동일 물류망의 별도 증권', PAGP)],
    'WES': [
        relation('Occidental Petroleum', 'OXY', 'customer', '2026년 Delaware 가스 집하·처리 고정 요금 전환·MVC 추가 · 원유·물 서비스도 연결', WES_Q),
        relation('ConocoPhillips', 'COP', 'customer', 'DBM 기존 시스템 가스 집하·처리 · 2026년 계약 변경·Oxy units 상환과 연계', WES_Q),
        relation('Occidental Petroleum', 'OXY', 'parent', 'GP는 Oxy 완전 소유 · 운영 고객 역할과 별도, 과거 common 소유율을 현재로 단정하지 않음', WES_Q),
        relation('Aris Water Solutions', None, 'subsidiary', '2025-10-15 편입 · Delaware 생산수 집하·처리·재활용·공급', WES_Q, 'aris-water'),
        relation('Brazos Delaware', None, 'subsidiary', '2026-06-11 편입 · Delaware 가스 집하·처리, WES Operating 하위 사업', WES_Q, 'brazos-delaware'),
    ],
    'HESM': [
        relation('Chevron', 'CVX', 'customer', '2026년 상반기 계약 매출 95% · Chevron 계약을 거친 제3자 물량 포함, MVC·집하·처리·출하', HESM_Q),
        relation('Chevron', 'CVX', 'supplier', '운영·행정·직원 파견 서비스 · 원료 자체 매도인으로 표시하지 않음', HESM_Q),
        relation('Chevron', 'CVX', 'parent', 'Hess 인수 후 현재 후원사·GP 간접 지배 · GIP는 2025년 전부 매각', HESM),
        relation('Targa Resources', 'TRGP', 'supplier', 'LM4 가스 처리료·비례 전력비 지급 · Targa 공장 운영', HESM_Q),
        relation('Targa Resources', 'TRGP', 'partner', 'Little Missouri 4 각 50% · 2019년 가동·명목 하루 200 MMcf', HESM),
    ],
}

PRIVATE = {}
for _key, _name, _origin, _business, _role in [
    ('seaway', 'Seaway Crude Holdings', EPD, 'Cushing 원유를 Texas Gulf의 정유·수출 시장으로 연결하는 배관·터미널 공동사업입니다.', 'Enterprise 50% 지분법 사업의 소유와 실제 운송·저장 거래를 구별합니다.'),
    ('cloudburst', 'CloudBurst Data Centers', CLOUD, 'Texas 데이터센터 개발의 가스 공급 계약 상대입니다.', 'Energy Transfer Oasis 약정은 고객 FID 조건부입니다. 발전 연료와 IT 장비 공급을 구별합니다.'),
    ('northwind-midstream', 'Northwind Midstream', MPLX, 'Permian sour gas 집하·처리·산성 가스 주입 자산입니다.', '2025년 MPLX 편입 후 생산지 불순물 처리·집하 병목을 연결하는 운영 역할입니다.'),
    ('bangl', 'BANGL', MPLX, 'Permian NGL을 Gulf 분별·수출 가치사슬에 연결하는 배관입니다.', '2025년 MPLX 잔여 지분 취득을 반영해 과거 공동 소유자를 현재로 남기지 않습니다.'),
    ('aris-water', 'Aris Water Solutions', WES_Q, 'Delaware 생산수 집하·처리·재활용·공급 사업으로 2025년 WES에 편입됐습니다.', '과거 독립 ARIS와 현재 연결 사업의 기간·주체를 구별합니다.'),
    ('brazos-delaware', 'Brazos Delaware', WES_Q, 'Delaware 가스 집하·처리 자산으로 2026년 WES에 편입됐습니다.', 'WES Operating을 통해 생산지와 하류 가스·NGL 시장에 연결합니다.'),
    ('keyera', 'Keyera', PAA_Q, 'Canadian NGL 사업의 2026년 인수 상대인 캐나다 중류 사업자입니다.', '매각된 처리·분별·저장·수송의 현재 소유를 이해하는 기록입니다. 인수 한 건으로 회사 전체 사업을 추정하지 않습니다.'),
]:
    PRIVATE[_key] = profile(_name, _origin, _business,
        '확인한 운영·계약 역할의 연결 자료입니다. 해당 거래가 회사 전체 매출을 뜻하지 않습니다.',
        [('연결 사업 역할', _role)], customers=_role)
PRIVATE['seaway']['relations'] = [relation('Enterprise Products Partners', 'EPD', 'partner', 'Cushing–Gulf 배관·수출 공동사업 · Enterprise 50%', EPD)]
PRIVATE['cloudburst']['relations'] = [relation('Energy Transfer', 'ET', 'supplier', 'Oasis 가스 공급 · 고객 FID 조건부 약정', CLOUD)]
PRIVATE['keyera']['relations'] = [relation('Plains All American Pipeline', 'PAA', 'partner', 'Canadian NGL 자산 인수 · 2026-05-12 완료, 현재 공급·JV로 추정하지 않음', PAA_Q)]
for _key, _symbol, _origin in [('northwind-midstream', 'MPLX', MPLX), ('bangl', 'MPLX', MPLX),
        ('aris-water', 'WES', WES_Q), ('brazos-delaware', 'WES', WES_Q)]:
    PRIVATE[_key]['relations'] = [relation(PUBLIC[_symbol]['name'], _symbol, 'parent', '현재 편입·운영 기업 · 독립 회사의 과거 기간과 구별', _origin)]
