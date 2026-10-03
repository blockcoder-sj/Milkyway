"""Edited oil/gas transport maps with actual contracts and project stages.

Annual consolidation, project interests and current execution are different
scopes. No network/model calls, inferred anonymous customers or return forecasts.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source
from copy import deepcopy
from .company_energy_refining import PRIVATE as REFINING_CONTEXT

SYMBOLS = ('ENB', 'PBA', 'TRP', 'SOBO')
AIF = {s: report(s, 'aif' if 'aif' in REPORTS[s] else 'annual') for s in SYMBOLS}
FIN = {s: report(s, 'financials' if 'financials' in REPORTS[s] else 'annual') for s in SYMBOLS}

ENB_Q2 = source('Enbridge · 2026 Q2 운송·전력 사업과 실행 상태',
    'https://www.enbridge.com/media-center/news/details?id=123885&lang=en', '2026-07-31')
ENB_TALLGRASS = source('Enbridge · Tallgrass 원유 사업 인수 계약 · 8-K와 발표 원문',
    'https://www.enbridge.com/investment-center/reports-and-sec-filings/sec-filings/sec-filing-details?docId=265320', '2026-09-09')
PBA_Q2 = source('Pembina · 2026 Q2 보고·공동사업·건설과 실제 가동',
    'https://www.sec.gov/Archives/edgar/data/1546066/000154606626000064/q22026interimreport.htm', '2026-07-31')
GREENLIGHT = source('Pembina · Greenlight 투자 결정·EPC·장비·현재 파트너',
    'https://www.pembina.com/media-centre/news/details/3403fb77-2257-466b-a8e2-f043f4cd4650', '2026-07-02')
GREENLIGHT_META = source('Pembina · Greenlight 전력의 Meta 데이터센터 연결',
    'https://www.pembina.com/media-centre/news/details/b911e6dd-3f8b-4da6-b97c-7271354e9d32', '2026-07-08')
TRP_Q2 = source('TC Energy · 2026 Q2 실제 가동·요금·원전 보수',
    'https://www.tcenergy.com/announcements/2026/2026-07-30-tc-energy-reports-strong-second-quarter-2026-operating-and-financial-results/', '2026-07-30')
CGL_PHASE2 = source('TC Energy · Coastal GasLink 2단계 투자 결정·실행 역할',
    'https://www.tcenergy.com/announcements/2026/2026-09-29-coastal-gaslink-phase-2-to-proceed-following-lng-canada-final-investment-decision/', '2026-09-29')
TRP_SALE = source('TC Energy · Guadalajara–Manzanillo 매각 계약·완료 조건',
    'https://www.tcenergy.com/announcements/2026/2026-09-21-tc-energy-announces-sale-of-guadalajara-manzanillo-pipeline/', '2026-09-21')
SOBO_Q2 = source('South Bow · 2026 Q2 원유망 물량·장기 계약·개발 상태',
    'https://www.southbow.com/wp-content/uploads/2026/08/South-Bow-Corporation-Q2-2026-News-Release.pdf', '2026-08-05')

WOODFIBRE = source('Enbridge · Woodfibre LNG 지분·고객·가스 운송 경로',
    'https://www.enbridge.com/projects-and-infrastructure/projects/woodfibre-lng', '열람 2026-10-03')
WOODFIBRE_CONSTRUCTION = source('Woodfibre LNG · 현재 EPFC·건설 계약 상대',
    'https://woodfibrelng.ca/construction/', '열람 2026-10-03')
WESTCOAST = source('Enbridge · KKR/Apollo Westcoast 확장 투자 계약·완료 조건',
    'https://www.enbridge.com/media-center/news/details?id=123887&lang=en', '2026-08-27')
SEAWAY = source('Seaway 운영사 · 공동사업자·수송 시장·상품',
    'https://seawaypipeline.com/faqs/', '열람 2026-10-03')
TRANS_MOUNTAIN = source('Canada Energy Regulator · Trans Mountain 현재 망·용량·요금·경로',
    'https://apps.cer-rec.gc.ca/PPS/en/pipeline-profiles/trans-mountain-expanded-system', '열람 2026-10-03')
WOODFIBRE_BACKGROUND = source('Woodfibre LNG · 원료 가스 공급사·착공·예정 완료',
    'https://woodfibrelng.ca/media-centre/', '열람 2026-10-03')
BRUCE_COMPONENTS = source('Bruce Power · Unit3 실제 증기발생기·공급·교체 컨소시엄',
    'https://www.brucepower.com/2025/02/20/final-lift-sees-all-eight-massive-steam-generators-now-placed-into-unit-3-marking-a-major-milestone-in-bruce-powers-mcr-project/', '2025-02-20')

PUBLIC = {
    'ENB': profile('Enbridge', AIF['ENB'],
        '캐나다·미국의 원유 운송·저장·수출, 천연가스 운송·저장, 가스 유틸리티와 풍력·태양광 등을 운영합니다. 생산자가 원유·가스를 시장으로 보내는 경로와 가정·산업·발전 고객의 에너지 공급 경로를 연결합니다.',
        '2025년 연결 매출은 65,194,000,000 CAD입니다. 운송·저장·배급·전력 수입뿐 아니라 가스 상품 판매가 포함됩니다. 고객 계약 매출 표의 합계와 연결 총매출은 범위가 달라 상품 재판매를 운송 수수료와 같은 수익성으로 보지 않습니다.',
        [('Mainline·Lakehead · 원유 간선', '서부 캐나다 원유를 미국 중서부와 동부 캐나다 정유 시장으로 운송합니다. Mainline은 월별 물량 신청이 가능한 공용 운송망이며 일부 구간은 별도 요금입니다.'),
         ('Flanagan South·Seaway·Gray Oak', 'Cushing과 미국 걸프 정유·수출 시장을 연결합니다. Seaway의 Enbridge 지분 50%, Gray Oak의 유효 경제 지분 68.5%와 프로젝트 전체 용량을 구분합니다.'),
         ('천연가스 간선·저장', 'Texas Eastern·Algonquin·East Tennessee·BC Pipeline 및 Permian 공동사업입니다. 예약 용량 요금·사용량 요금·규제 요금과 실제 수송량은 서로 다른 항목입니다.'),
         ('가스 배급 · Ontario·미국', 'Ontario와 Ohio·North Carolina·Utah 등 가정·상업·산업 고객에게 가스를 공급합니다. 겨울 난방 수요와 각 지역의 요금·물량 분리 제도가 다릅니다.'),
         ('Matterhorn·Eiger · Permian 가스', 'WhiteWater·ONEOK·MPLX와 MXP 공동사업으로 연결됩니다. Enbridge의 10% 참여와 해당 공동사업의 Eiger 70% 보유는 분모가 다릅니다.'),
         ('재생 전력·전력 구매 계약', '풍력·태양광·저장 및 전력 구매 계약을 연결합니다. Meta에 연결된 장기 전력 계약과 건설 중 설비의 실제 발전 매출은 구분합니다.')],
        customers='생산사·정유사·원유 판매자·LNG 수출 설비·발전소와 가스 유틸리티 고객입니다. Suncor·Canadian Natural·Cenovus의 원문에서 실제 운송 경로를 별도로 확인할 수 있습니다.',
        inputs='강관·펌프·압축기·계측·전력·연료와 검사·정비·건설 서비스를 사용합니다. 상품 매매용 가스의 원가와 파이프라인 운영비를 구분합니다.',
        competition='캐나다 원유 시장 접근은 South Bow·Trans Mountain 등 운송 경로, 가스 수송은 TC Energy·미국 가스망과 공급지·목적지·요금·예약 용량에서 사업 범위가 겹칩니다.'),
    'PBA': profile('Pembina Pipeline', AIF['PBA'],
        '생산지 원유·콘덴세이트·가스·NGL을 집하·처리하고 파이프라인·분별·저장·수출·상품 판매로 연결합니다. 가스 처리 공동사업 PGI, Cedar LNG와 데이터센터 전력사업 Greenlight는 회계·진행 상태가 다른 자산입니다.',
        '2025년 연결 매출은 7,778,000,000 CAD입니다. 외부 매출 기준 파이프라인 3,316,000,000·설비 357,000,000·상품판매/신사업 4,059,000,000·미배분 46,000,000입니다. PGI 자체 매출은 지분법 공동사업이므로 연결 매출에 합산하지 않습니다.',
        [('원유·NGL·희석제 운송', 'Peace·Alberta Oil Sands·Cochin 등의 망으로 원유·합성원유·콘덴세이트·NGL과 역방향 희석제 수요를 연결합니다.'),
         ('Alliance·Aux Sable', '서부 캐나다 가스의 장거리 운송과 미국 NGL 회수·분별을 연결합니다. 통합 후 현재 자산과 과거 공동 소유 상태를 구분합니다.'),
         ('PGI · 가스 처리', 'Pembina의 60% 운영 참여 공동사업입니다. Whitecap의 Kaybob·Lator·Gold Creek/Karr와 Ovintiv·Cutbank Ridge의 Dawson 가스가 시설 이용·장기 계약으로 연결됩니다.'),
         ('Redwater · NGL 분별·저장', '혼합 NGL을 에탄·프로판·부탄 등으로 분리합니다. 공정 용량·가동량·판매 물량과 각 제품의 연결 수입을 구분합니다.'),
         ('Cedar LNG · 건설·액화 서비스', 'Haisla Nation과 Kitimat의 부유식 LNG를 건설합니다. ARC·PETRONAS·Ovintiv의 장기 액화 용량 계약, TC Energy 가스 공급 경로와 Samsung Heavy Industries·Black & Veatch 제작을 연결합니다.'),
         ('Greenlight · 전력 인프라', 'Meta 데이터센터를 위한 932 MW 가스 복합발전의 투자 결정이 2026년 7월 이뤄졌습니다. 가스 운송·EPC·터빈·전력 계약은 확인됐지만 현재 발전·매출로 표시하지 않습니다.')],
        customers='원유·가스 생산사와 정유·석유화학·LNG·상품 판매 고객입니다. Dow 에탄 공급과 Cedar 액화 계약, Whitecap·Cutbank Ridge의 시설 이용을 별도로 구분합니다.',
        inputs='가스·NGL·원유 상품 매입, 전력·펌프·압축기·분별·저장 설비와 건설·운송·정비를 사용합니다. 장비·EPC 계약 상대와 장기 시설 이용 고객을 같은 관계로 묶지 않습니다.',
        competition='Enbridge·TC Energy·Keyera·AltaGas 등의 운송·처리·저장·수출 범위와 일부 겹칩니다. 같은 기업이 특정 자산에서는 협력사 또는 용량 공급사일 수 있습니다.'),
    'TRP': profile('TC Energy', AIF['TRP'],
        '캐나다·미국·멕시코의 천연가스 운송·저장과 발전 사업을 운영합니다. NGTL·Canadian Mainline·Columbia·ANR 등의 가스망과 Bruce Power의 전력 생산을 연결하며 Keystone 원유망은 South Bow로 분리됐습니다.',
        '2025년 연결 매출은 15,239,000,000 CAD입니다. 캐나다·미국·멕시코 가스망과 전력·본사 부문에는 고객 계약 매출 외의 리스 등 수입도 포함됩니다. 가스 운송 계약의 용량 리스와 운영·정비 서비스 대가를 구분합니다.',
        [('NGTL·Canadian Mainline', '서부 캐나다 생산 가스를 Alberta 수요·대륙 운송망으로 연결합니다. 규제 요금·감가상각·간선 정산과 예약/실제 사용량이 매출에 다르게 반영됩니다.'),
         ('Columbia·ANR·미국 가스망', '생산지·가스 저장·발전 수요·LNG 수출을 연결합니다. 각 파이프라인의 요금 소송·정산·단계 인상은 해당 망의 범위입니다.'),
         ('Coastal GasLink·Cedar Link', 'LNG Canada에 가스를 운송하는 CGL 지분은 35%이고 TC Energy가 운영합니다. Cedar LNG에 연결할 확장 설비와 현재 CGL 수송을 구분합니다.'),
         ('TGNH·CFE · 멕시코', 'CFE와 2055년까지의 용량 계약이 Tamazunchale·Villa de Reyes·Tula·Southeast Gateway를 연결합니다. CFE의 지분 참여와 운송 서비스 계약은 다른 관계입니다.'),
         ('Bruce Power · 원전', 'Ontario의 원전 발전·장기 전력 계약과 호기별 대형 기기 교체를 연결합니다. 공동사업 발전량·시설 능력과 TC Energy의 지분 귀속·연결 매출은 다릅니다.'),
         ('가스·태양광·풍력 전력', '열병합 발전과 Saddlebrook 태양광, Sharp Hills 장기 전력 구매 등을 연결합니다. 소유 발전 능력과 제3자 전력 구매 계약을 구분합니다.')],
        customers='가스 생산·판매 회사, 가스 유틸리티·발전·산업·LNG 수출 고객입니다. LNG Canada 참여자별 25년 수송 계약과 멕시코 CFE의 용량 계약이 실제 공개된 연결입니다.',
        inputs='강관·압축기·전력·연료·계측과 건설·검사·정비, 발전 설비·원전 보수·연료를 사용합니다. 가스 매매 대금과 시설 예약·수송 서비스 수입은 다릅니다.',
        competition='Enbridge와 미국·캐나다 가스망은 같은 생산지·수요지 수송 기회에서 사업 범위가 겹칩니다. 2024년 10월 분리된 South Bow를 현재 TC Energy 원유 운송 자회사로 표시하지 않습니다.'),
    'SOBO': profile('South Bow', AIF['SOBO'],
        '서부 캐나다 원유를 미국 중서부·Cushing·걸프 정유 시장으로 보내는 Keystone·Marketlink 및 Alberta 원유망·저장·상품 판매를 운영합니다. 2024년 TC Energy에서 분리된 독립 기업입니다.',
        '2025년 연결 매출은 1,986,000,000 USD입니다. 사업 부문은 Keystone 1,447,000,000의 운송·용량 수입과 118,000,000의 기타 수입, 상품 판매 403,000,000, Alberta 등 운송 18,000,000을 포함합니다. 동일 망에서 겹치는 물량·매출 소계를 이중 합산하지 않습니다.',
        [('Keystone · 캐나다·미국 원유망', 'Hardisty에서 미국 Midwest와 Gulf Coast로 원유를 운송합니다. 장기 약정의 고정 요금과 운영비·정비를 반영하는 변동 요금, 비약정 물량을 구분합니다.'),
         ('Marketlink · Cushing–걸프', 'Keystone 걸프 구간 용량을 임차해 Cushing 출발 물량에 서비스를 제공합니다. Keystone 자체 물량에 Marketlink를 더하면 일부 구간의 같은 수송이 겹칩니다.'),
         ('Port Neches Link · Motiva', 'Motiva Port Arthur 정유소의 마지막 연결 구간입니다. South Bow 지분 74.9% 공동사업과 고객 정유소의 원유 수요를 연결합니다.'),
         ('Grand Rapids·White Spruce', 'PetroChina Canada와 50:50인 Grand Rapids, Canadian Natural Horizon의 White Spruce를 통해 오일샌드 원유를 Edmonton·Heartland 시장에 연결합니다.'),
         ('Blackrod · 원유·가스 두 경로', 'International Petroleum Blackrod SAGD 시설의 연료 가스 반입과 원유 반출을 연결합니다. 가스 lateral은 2025년 9월, 원유 lateral은 2026년 3월 가동했습니다.'),
         ('저장·상품 판매', 'Alberta·Oklahoma·Texas의 저장 탱크와 원유 매입·판매·운송·물류 서비스입니다. 물리 원유 매출과 보유 용량 수수료는 범위가 다릅니다.')],
        customers='생산·정유·원유 판매 고객과 Motiva·Canadian Natural·International Petroleum의 확인된 개별 자산 연결입니다. 세 대형 고객 매출 집중 수치는 공개됐지만 그 익명 고객을 추정해 이름 붙이지 않습니다.',
        inputs='운송용 펌프·전력·검사·보수·탱크·강관과 원유 상품 매입을 사용합니다. 압력 제한·정비·계약 요금 조정·환율과 수송 물량이 각각 수입·비용에 연결됩니다.',
        competition='Enbridge·Trans Mountain 등은 서부 캐나다 원유 출하 경로·시장 접근·요금에서 사업 범위가 겹칩니다. Keystone XL 과거 개발 사업과 현재 운송망을 구분합니다.'),
}

LATEST = {
    'ENB': [('Westcoast · 투자 계약과 향후 지분', '2026년8월 KKR·Apollo의2,700,000,000 CAD 확장 투자 계약을 발표했습니다. 완료 조건과 단계별가동 후29% 간접지분을 구분하며 현재29%보유로 표시하지 않습니다.', WESTCOAST),
            ('운송·전력 · 계획과 실제 가동', '2026 Q2 발표는 Houston Oil Terminal 가동과 Blackcomb 시운전, Bay Runner Twin 투자 결정을 구분합니다. Twin 추가 2.6 Bcf/d는 2030년 목표이며 기존 운송량이 아닙니다.', ENB_Q2),
            ('Tallgrass · 인수 계약 단계', '2026년 9월 9일 Tallgrass 원유 사업의 2,550,000,000 USD 인수 계약을 발표했습니다. Pony Express 75% 등의 거래는 규제 승인·완료 조건이 남아 있어 현재 소유 자산으로 합산하지 않습니다.', ENB_TALLGRASS)],
    'PBA': [('Greenlight · 현재 파트너·고객·장비', '2026년 7월 투자 결정 후 Pembina47.5%·MSIP47.5%·Kineticor5%입니다. Meta 전력 수요, Siemens Energy 장비, Aecon·Técnicas Reunidas EPC가 연결됩니다. 목표 가동은 2030년 하반기입니다.', GREENLIGHT),
            ('2026 Q2 · 실제 가동과 건설 중', 'Redwater RFS IV는 5월 실제 가동해 분별 능력이 256,000배럴/일입니다. Cedar 배관 기계적 완공은 LNG 공장 전체 가동과 다르며 Cedar의 목표는 2028년 말입니다.', PBA_Q2)],
    'TRP': [('Coastal GasLink 2단계 · 실행 역할', '2026년 9월 투자 결정 후 LNG Canada가 건설 실행을 맡고 CGL은 소유·운영·허가를 유지합니다. 기존 약2.1 Bcf/d에 대한 확장은 2027년 착공·2030년대 초 가동 목표입니다.', CGL_PHASE2),
            ('Guadalajara–Manzanillo · 미완료 매각', '2026년 9월 ESENTIA 계열에 EOM 매각 계약을 발표했습니다. 400,000,000 USD 거래는 2027년 상반기 완료 목표·승인 조건이며 이미 매각됐다고 표시하지 않습니다.', TRP_SALE),
            ('원전·가스망 · 최신 실제 상태', 'Bruce Unit3는 2026년 6월12일 상업운전에 복귀했습니다. Bison XPress 가동과 7월14일 Berland River 압축기 운영도 실제 상태이며 향후 확장 계획과 분리합니다.', TRP_Q2)],
    'SOBO': [('2026 Q2 · 수송량 범위', 'Keystone 평균596,000배럴/일과 걸프 구간800,000배럴/일은 구간·출발 물량이 달라 더하지 않습니다. 후자는 Hardisty 출발과 Marketlink의 Cushing 출발 물량을 포함합니다.', SOBO_Q2),
             ('Bridger · 개발·약정 단계', '9개 익명 고객의 20년 약정465,000배럴/일과 Bridger의 Liberty Bridge 공동 개발을 발표했습니다. Prairie Connector·Liberty Bridge는 허가·투자 결정이 남아 있어 현재 가동망으로 표시하지 않습니다.', SOBO_Q2)],
}
DRIVERS = {
    'ENB': [('요금·물량·상품 원가', '운송 요금·예약 용량·실제 수송·정산·상품 가스 가격과 배급 규제 구조가 다릅니다. 총매출 중 상품 재판매와 서비스 수입을 구분합니다.'), ('현장 운영·회계', '펌프·압축기 전력, 검사·보수·누출·허가·가동 제한 및 USD/CAD 환율이 비용·수입·번역 손익에 다르게 반영됩니다.')],
    'PBA': [('시설 이용·상품 판매', '처리·운송·분별·저장 요금, 최소 용량 약정과 물리 상품 매입·매각 차이, NGL 배합·수출 가격이 각 부문에 연결됩니다.'), ('공동사업·개발', 'PGI 등의 지분법 이익·배당과 연결 매출, 건설 중 자본·차입·확정 장비 계약과 실제 운영 현금을 구분합니다.')],
    'TRP': [('요금·예약·리스', '규제 원가·요금 정산, 확정 용량 약정과 서비스 사용량, CFE 계약의 리스/정비 요소 및 USD/CAD가 보고 수치에 연결됩니다.'), ('원전·개발 상태', '호기 정비·복귀·전력 계약 가격, 가스망 건설·허가·압축기·교체 비용 및 지분법 공동사업의 집계 범위가 다릅니다.')],
    'SOBO': [('고정·변동 요금', '약정 용량 고정 요금, 운영·무결성 비용의 변동 요금 반영과 비약정 물량, Cushing–걸프 가격차가 계약·물류 수입을 연결합니다.'), ('수송·안전·회계', '압력 제한·검사·정비·저장·출하량, 원유 상품 매입 원가·헤지와 CAD/USD가 보고값에 반영됩니다. 정상화 EBITDA는 매출·GAAP 이익과 다릅니다.')],
}
for symbol, notes in PUBLIC.items():
    notes['brief'][1]['source'] = FIN[symbol]
    notes['brief'].extend(fact(title,text,origin) for title,text,origin in LATEST[symbol])
    notes['drivers'] = [fact(title,text,AIF[symbol]) for title,text in DRIVERS[symbol]]
    notes['revenue_mix'] = REPORTS[symbol]['revenue_mix']
    notes['sources'] += [FIN[symbol], *[o for _,_,o in LATEST[symbol]]]

CONTEXT = [
    ('woodfibre-lng','Woodfibre LNG',WOODFIBRE,'Enbridge30%·Pacific Energy70%의 Squamish LNG 건설 공동사업입니다.','2.1Mtpa 설계 능력과 BP Gas Marketing15년 전량 인수약정, McDermott EPFC·Ledcor Bird 건설·FortisBC 가스 경로를 연결합니다.2027년 가동 목표입니다.'),
    ('pacific-energy-woodfibre','Pacific Energy Corporation',WOODFIBRE,'Woodfibre LNG70% 파트너이며 캐나다 가스·LNG 가치사슬에 참여하는 그룹입니다.','Enbridge30%와 프로젝트 건설·운영을 연결합니다. 프로젝트 전량 인수 고객인 BP와 지분 파트너를 구분합니다.'),
    ('mcdermott-woodfibre','McDermott International',WOODFIBRE_CONSTRUCTION,'Woodfibre LNG의 설계·조달·제작·건설(EPFC) 계약 상대입니다.','프로젝트 공식 건설 페이지가 현재 역할을 명시합니다. Enbridge 그룹 전체의 독점 공급 계약이나 완공을 뜻하지 않습니다.'),
    ('ledcor-bird','Ledcor Bird',WOODFIBRE_CONSTRUCTION,'Woodfibre LNG 현장 건설의 하도급 참여사입니다.','EPFC 주계약 McDermott와 구분되는 현장 역할이며 향후 가동·인도를 확정하는 기록이 아닙니다.'),
    ('fortisbc-woodfibre','FortisBC',WOODFIBRE,'Woodfibre LNG에 연결되는 Eagle Mountain 가스 운송망의 사업자입니다.','Enbridge T-South와 LNG 현장 사이의 가스 반입 경로를 연결합니다. 천연가스 상품 매도인으로 추정하지 않습니다.'),
    ('cedar-lng','Cedar LNG',AIF['PBA'],'Haisla Nation과 Pembina가 Kitimat에 건설하는 3.3 Mtpa 부유식 LNG 액화 공동사업입니다.','ARC1.5·PETRONAS1.0·Ovintiv0.5 Mtpa 장기 용량 계약과 CGL의 가스 운송, BC Hydro 전력·선박 제작을 연결합니다. 2028년 말 가동 목표입니다.'),
    ('haisla-nation','Haisla Nation',AIF['PBA'],'Cedar LNG의 다수 지분 Indigenous 공동사업 파트너입니다.','Kitimat 전통 영토에서 프로젝트 참여·공동 개발을 연결합니다. 가스 매수인·장비 공급 업체로 추정하지 않습니다.'),
    ('samsung-heavy-industries','Samsung Heavy Industries',AIF['PBA'],'Cedar LNG의 부유식 LNG 생산 장치 제작 계약 상대입니다.','Black & Veatch와 고정 총액 계약으로 장치를 제작합니다. Samsung Electronics와 다른 기업이며 예정 선박의 완성·인도를 뜻하지 않습니다.'),
    ('black-veatch','Black & Veatch',AIF['PBA'],'Cedar LNG 부유식 생산 장치의 설계·제작 계약 파트너입니다.','Samsung Heavy Industries와 고정 총액 계약에 참여합니다. 그룹 전체 매출이나 독점 관계로 표시하지 않습니다.'),
    ('bc-hydro','BC Hydro',AIF['PBA'],'Cedar LNG의 액화 설비를 전기로 구동하는 전력 공급 경로의 사업자입니다.','건설 중 공장의 예정 전력 공급과 현재 액화 생산량을 구분합니다.'),
    ('pembina-gas-infrastructure','Pembina Gas Infrastructure · PGI',AIF['PBA'],'Pembina60% 운영 참여의 서부 캐나다 가스 처리 공동사업입니다.','Kaybob·Dawson·Musreau 및 Whitecap·CRC/Ovintiv의 시설 이용과 계약을 연결합니다. 자체 수입은 Pembina 연결 매출에 합산하지 않습니다.'),
    ('cutbank-ridge-corporation','Cutbank Ridge Corporation',AIF['PBA'],'Ovintiv Canada와 Mitsubishi 계열 Cutbank Dawson이 참여하는 가스 생산 공동사업입니다.','Dawson 처리 시설을 30년의 해당 지역 독점 서비스 약정으로 연결합니다. 고객사의 전체 사업 독점을 뜻하지 않습니다.'),
    ('greenlight-electricity','Greenlight Electricity Centre',GREENLIGHT,'Meta 데이터센터용932 MW 가스 복합발전 개발 공동사업입니다.','Pembina47.5%·MSIP47.5%·Kineticor5%입니다. Siemens 장비·Aecon/Técnicas EPC·가스망 예약·장기 전력 계약을 연결하며2030년 하반기 가동 목표입니다.'),
    ('msip-greenlight','Morgan Stanley Infrastructure Partners',GREENLIGHT,'Greenlight의47.5% 인프라 투자 공동사업 파트너입니다.','프로젝트 자본·개발을 Pembina와 연결합니다. 지분 투자를 발전 장비 공급이나 가스 구매로 분류하지 않습니다.'),
    ('kineticor','Kineticor Asset Management',GREENLIGHT,'Greenlight의 개발·상업 계약 연결과 향후 확장을 맡는5% 파트너입니다.','2026년7월 투자 결정 후 파트너 구성으로 갱신합니다. 과거50:50 구성과 다릅니다.'),
    ('siemens-energy','Siemens Energy',GREENLIGHT,'Greenlight 가스·증기 터빈과 발전기 및 장기 장비 서비스 계약 공급사입니다.','가스 터빈2기와 증기 터빈·발전기 공급 고정가격 계약, 장기 서비스 약정을 구분합니다. Siemens AG의 다른 제품 공급으로 일반화하지 않습니다.'),
    ('aecon-group','Aecon Group',GREENLIGHT,'Greenlight의 설계·조달·건설 고정가격 계약 컨소시엄 참여사입니다.','Técnicas Reunidas와 EPC를 맡습니다. 발전 공장 운영자는 별도 제3자 계약이며 공개 이름을 추정하지 않습니다.'),
    ('tecnicas-reunidas','Técnicas Reunidas',GREENLIGHT,'Greenlight EPC 컨소시엄의 설계·조달·건설 계약 상대입니다.','Aecon과 고정가격 계약에 참여하며 예정 공장의 완공·가동과 계약 발표는 다릅니다.'),
    ('coastal-gaslink','Coastal GasLink',AIF['TRP'],'Dawson Creek에서 Kitimat의 LNG Canada로 가스를 운송하는 공동사업입니다. TC Energy35%·운영입니다.','LNG Canada5개 참여자25년 수송 계약, Cedar Link 확장과2026년9월2단계 투자 결정을 연결합니다. 기존망 가동과 확장 목표를 분리합니다.'),
    ('cfe-mexico','Comisión Federal de Electricidad · CFE',AIF['TRP'],'TC Energy의 TGNH 가스망을 이용하는 멕시코 전력 공기업이자 공동사업 파트너입니다.','2055년까지 용량 계약과2025년말13.01% 지분을 구분합니다. 향후15%·35%는 조건·계약 만료에 따른 예정 수치입니다.'),
    ('bruce-power','Bruce Power',AIF['TRP'],'Ontario 원전 발전과 호기별 대형 기기 교체를 수행하는 공동사업입니다.','IESO 장기 전력 계약과2026년6월 Unit3 복귀, 나머지 호기 보수 계획을 연결합니다. 사이트 전출력은 TC Energy 단독 귀속 수치가 아닙니다.'),
    ('ieso-ontario','Ontario Independent Electricity System Operator · IESO',AIF['TRP'],'Bruce Power 전력·보수 비용·계약 승인과 연결되는 Ontario 전력계통 기관입니다.','전력 계약·호기별 비용 검증과 요금 고객 환급을 연결하며 원전 장비 공급 업체가 아닙니다.'),
    ('esentia-energy','ESENTIA Energy Development',TRP_SALE,'TC Energy Guadalajara–Manzanillo 소유 법인 EOM의 매각 계약 상대입니다.','2026년9월계약·2027년상반기 완료 목표이며 승인이 남았습니다. 현재 TC Energy 자회사나 가스 공급계약 고객으로 표시하지 않습니다.'),
    ('international-petroleum','International Petroleum Corporation',AIF['SOBO'],'South Bow Blackrod 연결망을 이용하는 SAGD 원유 생산 회사입니다.','천연가스 반입 McMillan North와 원유 반출 Blackrod lateral을 장기 계약으로 연결합니다.'),
    ('petrochina-canada','PetroChina Canada',AIF['SOBO'],'South Bow와 Grand Rapids 원유망을50:50으로 보유하는 공동사업 파트너입니다.','Alberta 오일샌드 원유를 Edmonton·Heartland 터미널로 연결합니다. LNG Canada 지분 참여와 다른 법인·자산입니다.'),
    ('motiva-port-arthur','Motiva Enterprises',AIF['SOBO'],'Port Arthur 정유소의 원유 공급 경로와 Port Neches Link 공동사업을 연결하는 회사입니다.','South Bow의74.9% 공동사업 지분과 정유소 연결 역할을 구분합니다. 공개되지 않은 원유 구매량·구매 계약을 추정하지 않습니다.'),
    ('bridger-pipeline','Bridger Pipeline',SOBO_Q2,'South Bow와 Liberty Bridge 원유망 개발을 진행하는 계약 상대입니다.','Prairie Connector 연결·Guernsey–Cushing 예정망을 연결합니다. 허가·투자 결정이 남아 있으며 현재 가동 수송량으로 표시하지 않습니다.'),
    ('tallgrass-crude','Tallgrass Energy · 원유 사업',ENB_TALLGRASS,'Pony Express·Powder River Gateway·저장·판매 사업을 Enbridge에 매각하기로 계약한 상대입니다.','2026년9월 계약과 규제 승인·완료 조건을 구분합니다. 현재 Enbridge 소유로 합산하지 않습니다.'),
]
PRIVATE = {key:profile(name,origin,business,structure) for key,name,origin,business,structure in CONTEXT}

EDGES = {
    'ENB': [relation('Woodfibre LNG',None,'partner','30% 참여 건설JV · BP 장기 인수·EPFC·가스 경로 연결,현재액화생산아님.',WOODFIBRE,'woodfibre-lng'),
            relation('McDermott International',None,'supplier','30%JV Woodfibre LNG의 EPFC 계약 상대 · 프로젝트 공식자료의 역할,ENB 직접전체발주로 일반화하지 않음.',WOODFIBRE_CONSTRUCTION,'mcdermott-woodfibre'),
            relation('FortisBC',None,'supplier','Woodfibre LNG 가스반입 Eagle Mountain–T-South 연결망 · 상품 가스 판매자가 아님.',WOODFIBRE,'fortisbc-woodfibre'),
            relation('Enterprise Products Partners','EPD','partner','Seaway 원유 운송·저장 공동사업 · 각 회사50%, Cushing–걸프 정유·수출 경로.',SEAWAY),
            relation('ONEOK','OKE','partner','WhiteWater·MPLX·Enbridge와 MXP(Matterhorn·Eiger) 공동사업 · 자산별 지분·현재/예정 용량 구분.',AIF['ENB']),
            relation('MPLX','MPLX','partner','Matterhorn·Eiger 및 Permian 가스 운송 공동사업 연결.',AIF['ENB']),
            relation('WhiteWater',None,'partner','MXP 가스망의 공동 개발·운영 연결 · Enbridge10% MXP 참여 범위.',AIF['ENB'],'whitewater'),
            relation('Cheniere Energy','LNG','customer','ADCC가 Corpus Christi LNG 수출 시설로 가스를 전달하는 실제 운송 경로 · LNG 전체 매입 고객으로 일반화하지 않음.',AIF['ENB']),
            relation('NextDecade','NEXT','customer','Rio Grande LNG로 가스를 운송하는 Bay Runner·Twin 장기약정 · 확장2.6 Bcf/d는2030년 목표.',ENB_Q2),
            relation('Meta Platforms','META','customer','장기 전력 구매 계약으로 태양광·풍력·저장 개발 연결 · 2026 Q2 발표의 계약 범위.',ENB_Q2),
            relation('Occidental Petroleum','OXY','partner','Pelican CO₂ Hub 공동 개발 · 2025 연차에 승인된 프로젝트, 원유 구매 관계가 아님.',AIF['ENB']),
            relation('Tallgrass Energy',None,'transaction','원유 운송·저장·판매 사업 인수 계약 ·2026-09-09 발표, 완료 승인 조건 남음.',ENB_TALLGRASS,'tallgrass-crude')],
    'PBA': [relation('ARC Resources',None,'customer','Cedar LNG1.5 Mtpa/20년 액화 용량 약정 · 현재가동량아님, 미국Antero AR과다름.',AIF['PBA'],'arc-resources'),
            relation('PETRONAS',None,'customer','Cedar LNG1.0 Mtpa/20년 액화 서비스 약정 · 현재가동량아님.',AIF['PBA'],'petronas'),
            relation('Cedar LNG',None,'partner','Kitimat 부유식 액화 JV · 건설·계약과 현재가동 구분.',AIF['PBA'],'cedar-lng'),
            relation('Haisla Nation',None,'partner','Cedar LNG의 다수 지분 공동 개발·사업 참여.',AIF['PBA'],'haisla-nation'),
            relation('Pembina Gas Infrastructure',None,'partner','60% 운영 참여 PGI · 처리 서비스·지분법 회계 범위.',AIF['PBA'],'pembina-gas-infrastructure'),
            relation('Ovintiv','OVV','customer','Dawson 처리 시설 이용 및 Cedar LNG0.5 Mtpa/12년 액화 계약 · 서로 다른 자산·범위.',AIF['PBA']),
            relation('Cutbank Ridge Corporation',None,'customer','Dawson 처리 시설의30년 해당 지역 독점 서비스 약정.',AIF['PBA'],'cutbank-ridge-corporation'),
            relation('Whitecap Resources',None,'customer','PGI Kaybob·Lator·Gold Creek/Karr 처리·배관 약정과 설비 이용 · 해당 자산별 상태 구분.',PBA_Q2,'whitecap-resources'),
            relation('Dow','DOW','customer','Heartland 에탄 공급 장기계약 ·2029년말 개시,2030년말22,500배럴/일 목표 · 현재납품수치아님.',PBA_Q2),
            relation('Keyera',None,'partner','Base Line Terminal50:50 공동사업 · Pembina운영·원유저장.',AIF['PBA'],'keyera'),
            relation('Samsung Heavy Industries',None,'supplier','Cedar LNG 부유식 장치 고정총액 제작·조달 계약 · Black&Veatch 공동참여.',AIF['PBA'],'samsung-heavy-industries'),
            relation('Black & Veatch',None,'supplier','Cedar LNG 부유식 생산 장치 설계·제작 계약 역할.',AIF['PBA'],'black-veatch'),
            relation('BC Hydro',None,'supplier','Cedar LNG 전력구동 액화의 전력 공급 경로 · 현재가동량아님.',AIF['PBA'],'bc-hydro'),
            relation('TC Energy','TRP','supplier','Cedar LNG의 CGL/Cedar Link 가스 경로 및 Greenlight의 NGTL 예약 용량 · 실제현재물량과 구분.',GREENLIGHT),
            relation('Greenlight Electricity Centre',None,'partner','47.5% 참여 · Meta전력계약·EPC·터빈·가스예약 연결.',GREENLIGHT,'greenlight-electricity'),
            relation('Morgan Stanley Infrastructure Partners',None,'partner','Greenlight47.5% 현재 파트너 · 2026년7월 구성 변경.',GREENLIGHT,'msip-greenlight'),
            relation('Kineticor Asset Management',None,'partner','Greenlight개발·향후확장·5% 현재 참여.',GREENLIGHT,'kineticor'),
            relation('Siemens Energy',None,'supplier','Greenlight터빈·발전기 고정가격 공급 및 장기 장비서비스 계약.',GREENLIGHT,'siemens-energy'),
            relation('Aecon Group',None,'supplier','Greenlight고정가격EPC 컨소시엄 · 건설계약은 현재발전과 다름.',GREENLIGHT,'aecon-group'),
            relation('Técnicas Reunidas',None,'supplier','Greenlight고정가격EPC · Aecon과 설계·조달·건설.',GREENLIGHT,'tecnicas-reunidas'),
            relation('Meta Platforms','META','customer','Greenlight장기전력계약 고객 ·932MW·2030년하반기 가동목표,현재전력판매아님.',GREENLIGHT_META)],
    'TRP': [relation('Coastal GasLink',None,'partner','35%보유·운영 · LNG Canada 및 Cedar LNG 가스 운송 경로.',AIF['TRP'],'coastal-gaslink'),
            relation('LNG Canada',None,'customer','5개JV참여자25년수송계약·2026년9월2단계 건설실행책임 연결.',CGL_PHASE2,'lng-canada'),
            relation('Cedar LNG',None,'customer','Cedar Link를 통한 예정0.4 Bcf/d 운송 확장 · 현재가동/판매량아님.',AIF['TRP'],'cedar-lng'),
            relation('Pembina Pipeline','PBA','customer','Greenlight 발전사업의 NGTL 장기예약 용량 · 예정932MW발전용.',GREENLIGHT),
            relation('Comisión Federal de Electricidad',None,'customer','TGNH가스망2055년까지 take-or-pay TSA · 용량리스·운영정비 분리.',AIF['TRP'],'cfe-mexico'),
            relation('Comisión Federal de Electricidad',None,'partner','TGNH의2025년말13.01%참여 · 향후조건부15%/35%와 구분.',AIF['TRP'],'cfe-mexico'),
            relation('Bruce Power',None,'partner','원전발전·호기별보수·장기전력계약 공동사업.',AIF['TRP'],'bruce-power'),
            relation('Ontario IESO',None,'customer','Bruce Power 전력·장기계약 가격·보수검증 · TC Energy 직접가스고객과 구분.',AIF['TRP'],'ieso-ontario'),
            relation('ESENTIA Energy Development',None,'transaction','EOM Guadalajara–Manzanillo 매각계약 ·2027년상반기 목표,승인조건 남음.',TRP_SALE,'esentia-energy'),
            relation('South Bow','SOBO','transaction','원유망2024-10-01분리 완료 · 현재독립기업,Keystone는TC Energy자회사자산아님.',AIF['TRP'])],
    'SOBO': [relation('Motiva Enterprises',None,'customer','Port Neches Link에서 Port Arthur정유소에 원유운송 연결.',AIF['SOBO'],'motiva-port-arthur'),
             relation('Motiva Enterprises',None,'partner','Port Neches Link공동사업 · South Bow74.9%,고객정유소 연결과 구분.',AIF['SOBO'],'motiva-port-arthur'),
             relation('PetroChina Canada',None,'partner','Grand Rapids원유망50:50 · 장기약정과Alberta시장 연결.',AIF['SOBO'],'petrochina-canada'),
             relation('Canadian Natural Resources','CNQ','customer','White Spruce가Horizon원유를Grand Rapids망으로 운송 ·25년약정.',AIF['SOBO']),
             relation('International Petroleum Corporation',None,'customer','BlackrodSAGD 가스반입·원유반출 장기약정 ·각lateral실제가동날짜 구분.',AIF['SOBO'],'international-petroleum'),
             relation('Bridger Pipeline',None,'partner','Liberty Bridge예정원유망 공동개발 ·허가·투자결정·현재물량분리.',SOBO_Q2,'bridger-pipeline'),
             relation('TC Energy','TRP','transaction','2024-10-01원유사업 분리·독립기업 ·현재소유관계아님.',AIF['SOBO'])],
}
for symbol, peers in {'ENB':['TRP','SOBO'], 'PBA':['ENB','TRP'],
                      'TRP':['ENB','PBA'], 'SOBO':['ENB']}.items():
    EDGES[symbol] += [relation(PUBLIC[p]['name'],p,'competitor',
        '두 회사 원문의 가스·원유 운송·시장 접근 사업 범위 비교 · 모든 자산에서 직접 경쟁한다는 뜻이 아닙니다.', AIF[p]) for p in peers]

PRIVATE['cedar-lng']['relations'] = [
    relation('ARC Resources',None,'customer','1.5Mtpa/20년고정액화용량약정 ·현재가동량아님.',AIF['PBA'],'arc-resources'),
    relation('PETRONAS',None,'customer','1.0Mtpa/20년액화서비스약정.',AIF['PBA'],'petronas'),
    relation('Pembina Pipeline','PBA','partner','액화JV개발·운영·용량서비스 연결.',AIF['PBA']),
    relation('Haisla Nation',None,'partner','다수지분공동사업자·프로젝트지역 참여.',AIF['PBA'],'haisla-nation'),
    relation('Samsung Heavy Industries',None,'supplier','부유식장치고정총액제작계약.',AIF['PBA'],'samsung-heavy-industries'),
    relation('Black & Veatch',None,'supplier','부유식장치설계·제작계약.',AIF['PBA'],'black-veatch'),
    relation('BC Hydro',None,'supplier','전력구동액화의전력공급경로.',AIF['PBA'],'bc-hydro'),
    relation('Coastal GasLink',None,'supplier','Cedar Link확장으로가스반입연결.',AIF['TRP'],'coastal-gaslink'),
    relation('Ovintiv','OVV','customer','0.5Mtpa/12년액화용량약정 ·현재가동량아님.',AIF['PBA']),
]
PRIVATE['greenlight-electricity']['relations'] = [
    relation('Meta Platforms','META','customer','932MW장기전력수요 ·2030년하반기가동목표.',GREENLIGHT_META),
    relation('Siemens Energy',None,'supplier','터빈·발전기및장기장비서비스.',GREENLIGHT,'siemens-energy'),
    relation('Aecon Group',None,'supplier','고정가격EPC참여.',GREENLIGHT,'aecon-group'),
    relation('Técnicas Reunidas',None,'supplier','고정가격EPC컨소시엄참여.',GREENLIGHT,'tecnicas-reunidas'),
    relation('TC Energy','TRP','supplier','NGTL장기가스운송용량예약.',GREENLIGHT),
    relation('Pembina Pipeline','PBA','partner','47.5%참여·건설관리.',GREENLIGHT),
    relation('Kineticor Asset Management',None,'partner','5%참여·개발·향후확장.',GREENLIGHT,'kineticor'),
    relation('Morgan Stanley Infrastructure Partners',None,'partner','47.5%참여·프로젝트자본.',GREENLIGHT,'msip-greenlight'),
]
PRIVATE['coastal-gaslink']['sources'].append(CGL_PHASE2)
PRIVATE['coastal-gaslink']['brief'].append(fact('2단계 실행·일정',
    'LNG Canada건설실행·CGL소유/운영/허가 ·2027년착공·2030년대초가동목표이며현재용량아닙니다.',CGL_PHASE2))

PRIVATE['woodfibre-lng']['relations'] = [
    relation('Enbridge','ENB','partner','30% 공동사업 참여.',WOODFIBRE),
    relation('Pacific Energy Corporation',None,'partner','70% 프로젝트 참여.',WOODFIBRE,'pacific-energy-woodfibre'),
    relation('BP','BP','customer','BP Gas Marketing15년 전량 LNG 인수 약정 ·현재가동량아님.',WOODFIBRE),
    relation('McDermott International',None,'supplier','EPFC설계·조달·제작·건설.',WOODFIBRE_CONSTRUCTION,'mcdermott-woodfibre'),
    relation('Ledcor Bird',None,'supplier','현장건설하도급 역할.',WOODFIBRE_CONSTRUCTION,'ledcor-bird'),
    relation('FortisBC',None,'supplier','Eagle Mountain–T-South 가스반입 연결망.',WOODFIBRE,'fortisbc-woodfibre'),
]
PUBLIC['ENB']['products'].append(fact('Woodfibre LNG · 지분·공급망',
    'Enbridge30%·Pacific Energy70%이며 McDermottEPFC·Ledcor Bird현장건설·FortisBC가스망과 BP15년 LNG인수 약정을 연결합니다.2.1Mtpa는설계능력·2027년가동목표입니다.',WOODFIBRE))
PRIVATE['pacific-canbriam'] = profile('Pacific Canbriam Energy', WOODFIBRE_BACKGROUND,
    '북동부 British Columbia의 가스 사업자로 Woodfibre LNG의 예정 원료 가스 공급사입니다.',
    'Pacific Energy 계열이며 LNG 원료 가스 공급과 FortisBC의 운송, BP의 LNG 인수는 서로 다른 계약·역할입니다.',
    [('원료 가스 공급', 'Woodfibre 공식 자료가 공급사 이름을 명시합니다. 예정 LNG 공장의 현재 생산량·매출·독점 비중을 추정하지 않습니다.')])
PRIVATE['woodfibre-lng']['relations'].append(relation('Pacific Canbriam Energy', None, 'supplier',
    '북동부 BC의 예정 원료 가스 공급 · FortisBC 운송망과 다른 역할.', WOODFIBRE_BACKGROUND, 'pacific-canbriam'))
PRIVATE['woodfibre-lng']['sources'].append(WOODFIBRE_BACKGROUND)
EDGES['ENB'].append(relation('Pacific Canbriam Energy', None, 'supplier',
    '30% 공동사업 Woodfibre의 예정 원료 가스 공급 · Enbridge 전체 가스 매입과 구분.', WOODFIBRE_BACKGROUND, 'pacific-canbriam'))
PUBLIC['ENB']['sources'] += [SEAWAY, WOODFIBRE_BACKGROUND]

# Preserve the older refinery-specific evidence and reverse link while adding
# the regulator's wider company map. No live traffic is invented from capacity.
PRIVATE['trans-mountain'] = deepcopy(REFINING_CONTEXT['trans-mountain'])
PRIVATE['trans-mountain'].update(description=
    '캐나다 Edmonton 원유를 British Columbia·미국 Washington 정유 시장과 Westridge 수출 터미널로 운송하는 연방 Crown 소유 파이프라인 사업입니다.',
    description_source=TRANS_MOUNTAIN)
PRIVATE['trans-mountain']['brief'] += [
    fact('현재 망·명목 능력', '확장망은 2024년5월 상업 가동했고 현재 명목 능력은890,000배럴/일입니다. Edmonton–Burnaby 본선·Kamloops·Sumas·Puget Sound 분기와 해상 수출을 연결합니다. 명목 능력은 실제 물량이 아닙니다.', TRANS_MOUNTAIN),
    fact('시장·운송 요금', '서부 캐나다 생산자는 BC·Washington 정유소와 Westridge의 아시아·미국 서해안 출하 경로를 이용합니다. 약정은15/20년·물량·제품·구간별이며 비약정은 별도 프리미엄이 있습니다.', TRANS_MOUNTAIN),
    fact('소유·기준일', '현재 연방 Crown 소유 사업이며 Kinder Morgan의 현재 자회사로 표시하지 않습니다. 규제기관 페이지의 사업 설명·물량·요금 갱신일은 각각 달라 열람일을 모든 수치의 측정일로 쓰지 않습니다.', TRANS_MOUNTAIN),
]
PRIVATE['trans-mountain']['products'] = [fact(t, d, TRANS_MOUNTAIN) for t, d in [
    ('원유·정유제품 운송', '서부 캐나다 원유·합성원유·경질/중질 및 일부 제품을 경로·배치별로 수송합니다.'),
    ('BC·Washington 정유 경로', 'Burnaby와 Sumas/Puget Sound 분기를 통해 육상 정유 수요에 연결합니다.'),
    ('Westridge · 수출', '해상 선적과 아시아·미국 서해안 시장 접근을 연결합니다. 파이프 능력·선박 선적·판매 시장점유율은 서로 다릅니다.'),
    ('약정·비약정 요금', '15/20년 약정의 기간·물량·제품·구간과 비약정 요금 구조를 구분합니다.'),
]]
PRIVATE['trans-mountain']['drivers'] = [fact(t, d, TRANS_MOUNTAIN) for t, d in [
    ('경로·약정·이용', '서부 캐나다 출하 물량·약정 용량·신청·배분 및 BC/미국/해상 목적지에 따라 운송 이용과 요금이 달라집니다.'),
    ('규제·운송 비용', '허가·무결성 검사·보수·운송 요금 규제와 터미널·선박 연결을 봅니다. 장래 최적화 계획은 현재 능력에 합산하지 않습니다.'),
]]
PRIVATE['trans-mountain']['sources'].append(TRANS_MOUNTAIN)
for symbol in ('ENB', 'SOBO'):
    EDGES[symbol].append(relation('Trans Mountain', None, 'competitor',
        '서부 캐나다 원유의 시장 접근·목적지·요금에서 겹치는 운송 경로 · 규제기관 원문 비교.', TRANS_MOUNTAIN, 'trans-mountain'))

PRIVATE['bruce-power']['relations'] = [
    relation('TC Energy', 'TRP', 'partner', '원전 발전 공동사업 참여.', AIF['TRP']),
    relation('Ontario IESO', None, 'customer', '장기 전력 계약·보수 비용 검증.', AIF['TRP'], 'ieso-ontario'),
    relation('BWX Technologies', 'BWXT', 'supplier', 'Unit3 증기발생기의 BWXT Canada 제조 · 실제8기 설치·과거 제조 시점과 현재 교체를 구분.', BRUCE_COMPONENTS),
]
PRIVATE['bruce-power']['sources'].append(BRUCE_COMPONENTS)
EDGES['TRP'].append(relation('BWX Technologies', 'BWXT', 'supplier',
    'Bruce Power 공동사업 Unit3 증기발생기의 BWXT Canada 제조 · TC Energy 직접 전체 발주와 구분.', BRUCE_COMPONENTS))
PUBLIC['TRP']['sources'].append(BRUCE_COMPONENTS)
