"""Edited tubular-steel and synthetic-fuel value chains from original reports."""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

ANNUAL = {s: report(s) for s in ('TS', 'SSL')}
FIN = {'TS': ANNUAL['TS'], 'SSL': report('SSL', 'financials')}
TS_Q2 = source('Tenaris · 2026 Q2 영업·지역·물류 상태',
    'https://ir.tenaris.com/news-releases/news-release-details/tenaris-announces-2026-second-quarter-results', '2026-08-05')
SSL_NITRATES = source('Sasol · Enaex 질산염 사업 매각 계약·승인 조건',
    'https://sasol.com/media-centre/media-releases/sasol-and-enaex-africa-sign-agreement-sale-sasols-nitrates-business', '2026-09-09')
SSL_NATREF = source('Sasol · Natref 정지·연료 공급의 실제 후속 상태',
    'https://sasol.com/media-centre/media-releases/natref-operational-update', '2026-09-01')
SSL_SAF = source('Sasol · White Desert 상업 SAF 공급 약정',
    'https://sasol.com/media-centre/media-releases/sasol-and-white-desert-launch-landmark-commercial-sustainable-aviation-fuel-partnership-from-cape-town-to-antarctica', '2026-09-15')
AIR_LIQUIDE = source('Air Liquide · Secunda 장기 산소 공급·전력 조달',
    'https://www.airliquide.com/group/press-releases-news/2024-02-26/air-liquide-and-sasol-sign-long-term-contracts-supply-additional-110-mw-renewable-energy-secunda', '2024-02-26')

PUBLIC = {
    'TS': profile('Tenaris', ANNUAL['TS'],
        '유정의 케이싱·튜빙(OCTG), 원유·가스 운송관과 산업용 무계목·용접 강관을 생산합니다. 강관 자체와 고압·부식 환경용 연결부, 현장 재고·적기 납품·기술 서비스를 묶어 에너지 생산자의 시추·생산 작업에 공급합니다.',
        '2025 연결 매출은 11,981,157,000 USD입니다. 강관 부문은 11,400,000,000, 기타는 581,000,000 USD로 백만 단위 반올림 표입니다. 강관 판매와 Rig Direct 서비스를 연결하며 관계사 Ternium·Usiminas 매출을 Tenaris 매출에 더하지 않습니다.',
        [('OCTG · 케이싱·튜빙', '케이싱은 유정 벽을 지지하고 튜빙은 생산 유체를 지상으로 보냅니다. 강도·부식·온도·압력 조건과 연결부 성능에 따라 제품 규격·제조 공정이 달라집니다.'),
         ('프리미엄 연결부 · Hydril/Wedge', '나사 연결의 밀봉·하중 성능을 제공하며 고압·심해·수평 유정 조건에 대응합니다. 관의 톤수와 고부가 연결 제품의 판매 구성을 구분합니다.'),
         ('Rig Direct · 공장–리그', '고객 시추 일정과 공장 생산·재고·물류를 연결해 현장에 적기 납품합니다. 고객의 전체 강관 구매량이나 독점 공급을 추정하지 않습니다.'),
         ('Line pipe · 가스·원유 인프라', '무계목 및 용접 운송관과 대구경 LSAW/ERW를 공급합니다. Saudi Steel Pipe·Global Pipe의 지역 생산과 유정용 OCTG 시장을 구분합니다.'),
         ('지역 생산 · Siderca·Tamsa·Dalmine', '아르헨티나·멕시코·이탈리아 및 Bay City·IPSCO 등 북미 생산을 통합합니다. 원료·전력·무역 규정과 공장 간 제품 이동이 납기·원가에 연결됩니다.'),
         ('조달 · Exiros와 제강 원료', 'Exiros의 공급사 선정·구매·재고 관리와 Gerdau·ArcelorMittal Tubarão·Usiminas·Ternium Argentina의 코일·후판 공급을 연결합니다.'),
         ('전력·가스 · Techgen·Tecpetrol', '멕시코 Techgen의 전력, 아르헨티나 Tecpetrol의 가스, 이탈리아 Edison Energia·Eni의 가스가 각 현장의 제조·발전 공정에 투입됩니다.')],
        customers='Pemex·Saudi Aramco·ADNOC 및 원유·가스 생산사·인프라·산업 고객입니다. Pemex 계약 갱신 협상과 고객의 투자·재고 조정은 판매·수금 경로에 각각 영향을 줍니다.',
        inputs='철스크랩·환원철·철강 원료·코일·후판·합금과 천연가스·전력·운송이 주요 투입입니다. Exiros 조달 공동사업, 외부 강재 공급, Techgen 전력과 자체 생산 설비를 구분합니다.',
        competition='공시는 Vallourec·Nippon Steel·JFE와 Saudi 지역 강관 기업을 경쟁 범위로 명시합니다. 고부가 OCTG·라인관·산업관별로 제품 강종·연결부·지역 고객에 따라 비교합니다.'),
    'SSL': profile('Sasol', ANNUAL['SSL'],
        '남아공 석탄·가스에서 합성 연료·기초 화학을 만들고 모잠비크 가스, 남아공 Natref 정유, 미국·유럽 특수 화학과 Qatar ORYX GTL을 연결합니다. 광산→가스화→합성가스→연료·화학, 가스 수송·정유·판매 경로를 함께 봐야 하는 통합 기업입니다.',
        'FY2026(2025년 7월~2026년 6월) 연결 매출은 272,118,000,000 ZAR입니다. 외부 매출은 채굴 4,000,000·가스 7,998,000,000·연료 122,075,000,000·아프리카 화학 59,862,000,000·미주 40,290,000,000·유라시아 41,889,000,000입니다. 내부 거래와 지분법 사업을 더하지 않습니다.',
        [('Secunda · 석탄–합성 연료', '채굴·매입 석탄과 가스를 가스화·합성 공정으로 액체 연료·화학 원료로 전환합니다. 석탄 품질·회수율·산소·증기·전력과 정비가 원료 투입·생산량에 연결됩니다.'),
         ('모잠비크·남아공 가스', '가스 생산·매입·수송과 도매·최종 산업 고객 판매입니다. Rompco의 배관 사업과 Sasol 고객 판매 매출을 구분합니다.'),
         ('Natref · 원유 정유', '외부 원유를 수입·정제해 연료를 공급합니다. 공동사업 파트너 Prax SA의 구조조정과 이용 가능 용량, 후속 정지·복구 공지가 실제 판매 경로에 연결됩니다.'),
         ('기초 화학 · 연료와 다른 시장', '에틸렌·에틸렌옥사이드·글리콜·폴리에틸렌, 메탄올·암모니아·비료·폭약 중간체·용제를 공급합니다. Enaex의 중간체 구매와 LyondellBasell 계열의 폴리에틸렌 판매 역할을 구분합니다.'),
         ('특수 화학 · 용도별 제품', '고순도 알루미나·촉매 담체·계면활성제·알코올·선형 알킬벤젠·왁스·페놀 등입니다. 세정·개인용품·윤활·금속가공·농업·건설 수요와 각 원료의 가격 경로가 다릅니다.'),
         ('ORYX GTL · Qatar 공동사업', '49% 지분 사업으로 Al Khaleej Gas의 가스를 합성 액체 연료로 전환합니다. JV 자체 매출·생산능력을 Sasol 연결 매출이나 단독 생산량으로 합산하지 않습니다.'),
         ('산소·재생 전력 · 조달·실제 가동', 'Air Liquide의 산소 설비와 공동 재생 전력 조달을 연결합니다. 연차 기준 약508 MW가 실제 운영 중이며 1.3 GW 초과 포트폴리오·660 MWh 저장은 계획·계약을 포함합니다.')],
        customers='연료의 도매·산업·주유소·항공 고객과 세계 화학 고객입니다. Enaex 폭약 중간체, Equistar 폴리에틸렌 판매, White Desert SAF 약정은 공개 이름·역할이 확인된 연결입니다.',
        inputs='자체·외부 석탄, 모잠비크·외부 가스와 원유, 에탄·에틸렌·벤젠·등유·유지계 원료·알루미늄, 산소·전력·수송이 투입됩니다. Eskom 전력, Transnet 철도·항만과 Air Liquide 산소 공급을 연결합니다.',
        competition='연료는 지역 공급·수입 정유제품·판매망, 화학은 동일 규격의 기초·특수 제품 공급과 경쟁합니다. LyondellBasell은 일부 화학 시장 사업자이면서 특정 JV·판매 계약의 파트너이기도 하므로 모든 거래를 경쟁 관계로 바꾸지 않습니다.'),
}
PUBLIC['TS']['brief'].append(fact('2026 Q2 · 수요·물류 상태',
    '중동 출하 지연·단위 물류비·원료비와 북미 가격, 공장 고정비 흡수의 영향을 구분합니다. 발표의 분기 매출 2,967,000,000 USD와 연간 표 11,981,157,000 USD는 기간이 다릅니다.', TS_Q2))
PUBLIC['TS']['sources'].append(TS_Q2)
PUBLIC['SSL']['brief'] += [
    fact('후속 계약 · Enaex 질산염', '2026년 9월 Enaex 질산염 매각은 승인 조건이 남아 있고 Sasol의23% 참여는 거래 후 예정입니다. 기존 중간체 공급·폭약 협력과 별도인 미완료 거래입니다.', SSL_NITRATES),
    fact('Natref · 연차 이후 운영', '9월1일 공지는 8월 설비 정지와 9월 말까지 공급 안정화 조치를 설명합니다. 6월 말 연차의 생산 개선을 현재 정상 가동으로 일반화하지 않습니다.', SSL_NATREF),
    fact('Zaffra · 종료 절차', 'Topsoe와50:50인 Zaffra는 2026년6월25일 질서 있는 사업 종료를 결의했습니다. 과거 개발 계획을 현재 신규 공장 건설·매출로 표시하지 않습니다.', ANNUAL['SSL']),
]
PUBLIC['SSL']['products'].append(fact('상업 SAF · White Desert',
    '2026년9월 상업 바이오 SAF 공급 약정으로 Cape Town–남극 항공 운항에 연결합니다. 발표만으로 납품 완료·계약 금액을 만들지 않으며 녹색 수소 e-fuel 개발과 구분합니다.', SSL_SAF))
PUBLIC['SSL']['sources'] += [SSL_NITRATES, SSL_NATREF, SSL_SAF]
for symbol, notes in PUBLIC.items():
    notes['brief'][1]['source'] = FIN[symbol]
    notes['revenue_mix'] = REPORTS[symbol]['revenue_mix']
    notes['sources'].append(FIN[symbol])
PUBLIC['TS']['drivers'] = [fact(t, d, ANNUAL['TS']) for t, d in [
    ('시추·재고·수금', '생산자 시추·완결 일정, 강관 재고와 고객 투자·지급 능력이 출하·가격·미수금에 연결됩니다. Pemex의 연말 수금 개선과 현재 계약 갱신 협상은 각각 별도 상태입니다.'),
    ('원료·에너지·공장', '스크랩·환원철·코일·합금·가스·전력과 공장 가동률·수송·관세가 원가에 반영됩니다. 계약 서비스·특수 연결부와 단순 톤수 가격을 같은 지표로 보지 않습니다.'),
    ('지역·제품 구성', '북미·남미·중동 고객 구성, 현지 조달 정책·무역 규제와 강종·무계목/용접·프리미엄 연결 제품이 제품별 매출·현장 경로를 바꿉니다.'),
]]
PUBLIC['SSL']['drivers'] = [fact(t, d, ANNUAL['SSL']) for t, d in [
    ('원료·전력·물류', '석탄 품질·가스 공급·원유·에탄 가격, Eskom 전력·산소·증기·Transnet 물류와 정비가 생산·재고·비용에 연결됩니다.'),
    ('제품 가격·환율·규제', '연료·화학 가격과 USD/ZAR, 가스 요금 규제·배출 허가·탄소 비용이 사업별 매출·비용·평가액에 다르게 반영됩니다.'),
    ('판매 경로·공동사업', '폴리에틸렌 위탁 판매와 글리콜 유통 계약, ORYX·LIP JV 가동, Natref 파트너 용량 및 계획 재생 전력의 실제 운영 전환을 구분합니다.'),
]]

CONTEXT = [
    ('exiros', 'Exiros', ANNUAL['TS'], 'Tenaris·Ternium50:50의 조달 공동사업입니다.', '공급사 발굴·구매·공급사 성과·재고를 관리합니다. Tenaris 공급 투입 경로와 자본 참여가 다른 관계이며 모든 강재를 자체 생산하지 않습니다.'),
    ('gerdau-tenaris', 'Gerdau', ANNUAL['TS'], 'Tenaris가 공개한 브라질 용접관용 코일·후판 공급사입니다.', '원문은 Gerdau·ArcelorMittal Tubarão·Usiminas에서 주로 구매한다고 명시합니다. 구매량·시장점유율·독점 공급은 공개되지 않았습니다.'),
    ('arcelormittal-tubarao', 'ArcelorMittal Tubarão', ANNUAL['TS'], 'Tenaris의 브라질 용접 강관 원료 공급 경로입니다.', '코일·후판 조달 관계를 표시하며 ArcelorMittal의 다른 강관 사업·Vallourec 투자와 공급 관계를 구분합니다.'),
    ('usiminas-tenaris', 'Usiminas', ANNUAL['TS'], 'Ternium 계열로 Tenaris 브라질 사업의 강재 공급사입니다.', '코일·후판 구매와 Tenaris의 투자·지분법 회계를 별도로 봅니다. Usiminas 자체 매출을 Tenaris 매출에 더하지 않습니다.'),
    ('ternium-argentina', 'Ternium Argentina', ANNUAL['TS'], 'Tenaris 아르헨티나 용접 강관 사업의 강재 공급사입니다.', 'Ternium의 현지 자회사이며 모회사 투자·Exiros 조달 공동사업과 실제 코일·후판 공급은 다른 연결입니다.'),
    ('techgen', 'Techgen', ANNUAL['TS'], '멕시코 Pesquería 가스 복합발전 공동사업입니다.', 'Tenaris22%·Ternium48%·Tecpetrol30%이며 Tenaris는 발전 용량22%를 계약합니다. 지분과 전력 구매·남는 전력의 제3자 판매를 구분합니다.'),
    ('tecpetrol', 'Tecpetrol', ANNUAL['TS'], 'Tenaris 아르헨티나 사업의 주요 천연가스 공급사입니다.', '가스 공급과 Techgen30% 공동사업 참여를 연결합니다. San Faustin 공통 지배 관계가 모든 구매 가격·거래를 동일하게 만들지는 않습니다.'),
    ('edison-energia', 'Edison Energia', ANNUAL['TS'], 'Tenaris 이탈리아 발전 시설의 천연가스 공급사입니다.', '발전소 공급은 Edison Energia, 이탈리아 제조 공장의 가스는 Eni로 원문이 구분합니다.'),
    ('saudi-steel-pipe', 'Saudi Steel Pipe', ANNUAL['TS'], 'Tenaris가 지배하는 Saudi ERW 강관 제조 기업입니다.', 'Tenaris47.8% 참여와 지배를 공시하며 Global Pipe Company57.3% 참여가 연결됩니다. Saudi Aramco의 장기·중기 관종별 구매 계약을 현지 생산에 연결합니다.'),
    ('global-pipe-company', 'Global Pipe Company', ANNUAL['TS'], 'Saudi Jubail의 대구경 LSAW 용접관 제조 기업입니다.', 'Saudi Steel Pipe의57.3% 참여로 Tenaris 연결 지배 사업입니다. 유정 OCTG와 장거리 라인관의 제품·납품 경로를 구분합니다.'),
    ('tenaris-siderca', 'Siderca', ANNUAL['TS'], 'Tenaris 아르헨티나의 무계목 강관 제조 사업입니다.', '철강·환원철·가스·전력에서 관 압연·열처리·연결부·납품으로 이어지는 현지 생산을 연결합니다.'),
    ('tenaris-tamsa', 'Tamsa', ANNUAL['TS'], 'Tenaris 멕시코의 무계목 강관 제조 사업입니다.', 'Techgen 전력과 Pemex Rig Direct 적기 공급을 연결하는 현지 제조 사업입니다.'),
    ('tenaris-dalmine', 'Dalmine', ANNUAL['TS'], 'Tenaris 이탈리아의 무계목 강관 제조 사업입니다.', 'Eni 제조용 가스와 Edison Energia 발전용 가스, 산업·에너지용 강관을 연결합니다.'),
    ('vallourec-tenaris', 'Vallourec', ANNUAL['TS'], 'Tenaris 공시가 명시한 고부가 OCTG·프리미엄 연결부 경쟁사입니다.', '지역 생산·제품 강종·고객 조건별 경쟁 범위를 보여 줍니다. 공시의 정성 시장 설명을 검증된 제품 점유율 숫자로 바꾸지 않습니다.'),
    ('nippon-steel-tenaris', 'Nippon Steel', ANNUAL['TS'], 'Tenaris가 국제 고합금 강관 시장의 경쟁사로 명시한 기업입니다.', '아시아·중동 제품 경쟁과 특정 관종을 구분합니다. 과거 Vallourec 브라질 공동 생산 관계를 현재 지분으로 표시하지 않습니다.'),
    ('jfe-tenaris', 'JFE', ANNUAL['TS'], 'Tenaris 공시가 국제 고합금 강관 경쟁 범위에 포함한 기업입니다.', '고급 강종·고객 시장의 경쟁이며 전 세계 모든 강관을 동일 시장으로 계산하지 않습니다.'),
    ('adnoc-tenaris', 'ADNOC', ANNUAL['TS'], 'Tenaris의 UAE OCTG와 Rig Direct 서비스 고객입니다.', '공시가 현장 강관 공급·서비스 확대를 명시하며 특정 고객별 매출액·독점 공급 비중을 추정하지 않습니다.'),
    ('eskom-sasol', 'Eskom', ANNUAL['SSL'], 'Sasol 남아공 공정의 전력 공급 공기업입니다.', '외부 전력 공급 안정성과 요금, 자체 발전·재생 전력을 구분합니다. 가스·LNG 공동 검토를 실제 LNG 공급으로 표시하지 않습니다.'),
    ('transnet-sasol', 'Transnet', ANNUAL['SSL'], 'Sasol의 남아공 철도·항만·수출 물류 경로 사업자입니다.', '운송·항만 정지·취소는 화학 출하·재고·육상 운송에 연결됩니다. Sasol 자회사가 아니라 외부 물류 경로입니다.'),
    ('natref-sasol', 'Natref', ANNUAL['SSL'], 'Sasol과 Prax SA가 참여하는 남아공 원유 정유 공동사업입니다.', 'Sasol의 합성 연료 시설과 다른 원유 정유 경로입니다. Prax 용량 이용과 파트너 구조조정, 8월 정지의 후속 공지를 연결합니다.'),
    ('prax-south-africa', 'Prax South Africa', ANNUAL['SSL'], 'Sasol Natref의 공동사업 파트너입니다.', '2025년10월 사업 구조조정에 들어갔고 지분 매각을 위한 절차·지원 조건이 남았습니다. 예전 TotalEnergies 지분 관계를 현재 파트너로 사용하지 않습니다.'),
    ('enaex-africa', 'Enaex Africa', ANNUAL['SSL'], 'Sasol의 폭약 중간체 구매·가공 파트너입니다.', '광산용 최종 폭약으로 전환합니다. 2026년9월 질산염 사업 매입은 규제 승인 조건이 남은 별도 거래이며 기존 공급·협력과 구분합니다.'),
    ('oryx-gtl', 'ORYX GTL', ANNUAL['SSL'], 'Sasol49%의 Qatar 가스–액체 연료 공동사업입니다.', 'Al Khaleej Gas 장기 가스 구매 계약과 합성 연료 생산을 연결합니다. 회사 전체 매출·연결 범위와 JV 자체 수치를 구분합니다.'),
    ('al-khaleej-gas', 'Al Khaleej Gas', ANNUAL['SSL'], 'ORYX GTL 원료 천연가스의 장기 공급 계약 상대입니다.', 'ExxonMobil Middle East Gas Marketing과 Qatar Petroleum 공동사업으로 원문에 명시됩니다. 2005년 개시25년 계약과 연장 협의를 구분합니다.'),
    ('rompco-sasol', 'Rompco', FIN['SSL'], '모잠비크–남아공 가스 수송 관계사입니다.', '공시의 자체 매출은 Sasol 연결 매출이 아닙니다. 가스 생산·판매와 배관 운송 경로를 구분합니다.'),
    ('lip-jv-sasol', 'Louisiana Integrated Polyethylene JV', ANNUAL['SSL'], 'Sasol과 LyondellBasell 계열의50:50 미국 화학 공동사업입니다.', '에틸렌·폴리에틸렌 생산과 Equistar의 위탁 판매를 연결합니다. 공동사업의 총 생산·매출을 Sasol 단독 귀속으로 합산하지 않습니다.'),
    ('equistar-sasol', 'Equistar Chemicals', ANNUAL['SSL'], 'LyondellBasell 계열로 Sasol의 LIP JV 폴리에틸렌을 판매하는 계약 상대입니다.', '위탁 판매 계약은 2030년11월30일 만료 예정입니다. 원료 공급·소유 지분과 판매 대행은 다른 역할입니다.'),
    ('zaffra-sasol', 'Zaffra', ANNUAL['SSL'], 'Sasol·Topsoe50:50의 과거 SAF 개발 공동사업입니다.', '2026년6월25일 질서 있는 사업 종료 결의가 공개됐습니다. 기존 개발 발표를 현재 가동 설비·상업 생산으로 표시하지 않습니다.'),
    ('topsoe-sasol', 'Topsoe', ANNUAL['SSL'], 'Sasol과 SAF 기술 공동사업 Zaffra를 만든 기술 파트너입니다.', '2026년6월 사업 종료 절차로 갱신합니다. 과거 신규 공장 계획을 현재 활동 중인 공동사업과 구분합니다.'),
    ('white-desert-sasol', 'White Desert', SSL_SAF, 'Cape Town–남극 항공 운항의 Sasol SAF 공급 약정 고객입니다.', '2026년9월 발표는 지속 가능한 바이오 원료 기반의 상업 SAF 약정입니다. 녹색 수소 e-fuel 계획이나 완료 납품 실적과 구분합니다.'),
]
PRIVATE = {key: profile(name, origin, business, structure)
           for key, name, origin, business, structure in CONTEXT}
PRIVATE['natref-sasol']['sources'].append(SSL_NATREF)
PRIVATE['enaex-africa']['sources'].append(SSL_NITRATES)

EDGES = {
    'TS': [
        relation('Exiros', None, 'supplier', '공급사 선정·구매·재고 관리의 조달 경로.', ANNUAL['TS'], 'exiros'),
        relation('Exiros', None, 'partner', 'Ternium과50:50 조달 공동사업.', ANNUAL['TS'], 'exiros'),
        relation('Ternium', 'TX', 'partner', 'Exiros50:50 및 Techgen48% 파트너 · 지분법 자체 매출과 공급 거래 구분.', ANNUAL['TS']),
        relation('Ternium Argentina', None, 'supplier', '아르헨티나 용접관용 코일·후판.', ANNUAL['TS'], 'ternium-argentina'),
        relation('Gerdau', None, 'supplier', '브라질 용접관용 코일·후판.', ANNUAL['TS'], 'gerdau-tenaris'),
        relation('ArcelorMittal Tubarão', None, 'supplier', '브라질 용접관용 코일·후판.', ANNUAL['TS'], 'arcelormittal-tubarao'),
        relation('Usiminas', None, 'supplier', '브라질 용접관용 강재 · Ternium 계열.', ANNUAL['TS'], 'usiminas-tenaris'),
        relation('Techgen', None, 'supplier', '멕시코 제조용 전력 · Tenaris 용량22% 계약.', ANNUAL['TS'], 'techgen'),
        relation('Techgen', None, 'partner', 'Tenaris22%·Ternium48%·Tecpetrol30% 발전 공동사업.', ANNUAL['TS'], 'techgen'),
        relation('Tecpetrol', None, 'supplier', '아르헨티나 주요 제조·환원철용 천연가스.', ANNUAL['TS'], 'tecpetrol'),
        relation('Edison Energia', None, 'supplier', '이탈리아 발전 시설용 천연가스.', ANNUAL['TS'], 'edison-energia'),
        relation('Eni', 'E', 'supplier', '이탈리아 제조 공장용 천연가스 · 발전소 계약과 구분.', ANNUAL['TS']),
        relation('Comisión Federal de Electricidad', None, 'supplier', '멕시코 전력의 일부 공급 · 주력 Techgen과 구분.', ANNUAL['TS'], 'cfe-mexico'),
        relation('PEMEX', None, 'customer', '1994년부터 Rig Direct·적기 강관 공급 · 현재 장기 계약 갱신 협상.', ANNUAL['TS'], 'pemex'),
        relation('Saudi Aramco', None, 'customer', '무계목·LSAW OCTG 장기 및 ERW·라인관 중기 공급 계약.', ANNUAL['TS'], 'saudi-aramco'),
        relation('ADNOC', None, 'customer', 'UAE OCTG·Rig Direct 현장 서비스.', ANNUAL['TS'], 'adnoc-tenaris'),
        *[relation(name, None, 'subsidiary', detail, ANNUAL['TS'], key) for key, name, detail in [
            ('tenaris-siderca', 'Siderca', '아르헨티나 무계목관 제조'), ('tenaris-tamsa', 'Tamsa', '멕시코 무계목관 제조'),
            ('tenaris-dalmine', 'Dalmine', '이탈리아 무계목관 제조'), ('saudi-steel-pipe', 'Saudi Steel Pipe', '47.8% 참여·지배 ERW관 제조'),
            ('global-pipe-company', 'Global Pipe Company', 'Saudi Steel Pipe57.3% 참여로 지배·LSAW관 제조'),
        ]],
        *[relation(name, None, 'competitor', '공시에 명시된 국제 OCTG·고합금 강관 경쟁 범위.', ANNUAL['TS'], key)
          for name, key in [('Vallourec', 'vallourec-tenaris'), ('Nippon Steel', 'nippon-steel-tenaris'), ('JFE', 'jfe-tenaris')]],
    ],
    'SSL': [
        relation('Eskom', None, 'supplier', '남아공 공정의 외부 전력.', ANNUAL['SSL'], 'eskom-sasol'),
        relation('Transnet', None, 'supplier', '철도·항만·수출 물류 경로.', ANNUAL['SSL'], 'transnet-sasol'),
        relation('Air Liquide', None, 'supplier', 'Secunda 산소 설비의 장기 공급 계약 · 전력 공동 조달과 구분.', AIR_LIQUIDE, 'air-liquide'),
        relation('Air Liquide', None, 'partner', '공동 전력 조달 · 현재 운영 MW와 계약 포트폴리오 구분.', ANNUAL['SSL'], 'air-liquide'),
        relation('Prax South Africa', None, 'partner', 'Natref 파트너 · 2025년10월 구조조정·지분 매각 절차.', ANNUAL['SSL'], 'prax-south-africa'),
        relation('Natref', None, 'partner', '원유 정유 공동사업 · 후속 설비 정지·공급 조치 확인.', SSL_NATREF, 'natref-sasol'),
        relation('Enaex Africa', None, 'customer', '폭약 중간체 구매·최종 폭약 전환.', ANNUAL['SSL'], 'enaex-africa'),
        relation('Enaex Africa', None, 'partner', '2020년부터의 광산 폭약 사업 협력.', SSL_NITRATES, 'enaex-africa'),
        relation('Enaex Africa', None, 'transaction', '질산염 사업 매각 계약 · 2026년9월·승인 조건·거래 후23% 참여 예정.', SSL_NITRATES, 'enaex-africa'),
        relation('ORYX GTL', None, 'partner', 'Qatar 가스–액체 연료49% 공동사업.', ANNUAL['SSL'], 'oryx-gtl'),
        relation('Al Khaleej Gas', None, 'supplier', 'ORYX GTL 원료 가스 장기 계약 · Sasol 본사 직접 발주와 구분.', ANNUAL['SSL'], 'al-khaleej-gas'),
        relation('Rompco', None, 'partner', '모잠비크–남아공 가스 수송 관계사 · 자체 매출은 연결 밖.', FIN['SSL'], 'rompco-sasol'),
        relation('LyondellBasell', 'LYB', 'partner', 'LIP JV50:50 · Equistar 폴리에틸렌 판매 계약.', ANNUAL['SSL']),
        relation('Louisiana Integrated Polyethylene JV', None, 'partner', 'Lake Charles 에틸렌·폴리에틸렌 생산 공동사업.', ANNUAL['SSL'], 'lip-jv-sasol'),
        relation('Equistar Chemicals', None, 'customer', 'Sasol 폴리에틸렌 위탁 판매 경로 · 직접 최종 소비자와 구분.', ANNUAL['SSL'], 'equistar-sasol'),
        relation('White Desert', None, 'customer', '상업 바이오 SAF 공급 약정 · 납품 완료·금액을 추정하지 않음.', SSL_SAF, 'white-desert-sasol'),
        relation('Zaffra', None, 'transaction', 'Topsoe와50:50 과거 JV · 2026년6월25일 사업 종료 절차 결의.', ANNUAL['SSL'], 'zaffra-sasol'),
        relation('Topsoe', None, 'transaction', 'Zaffra 과거 기술 공동사업자 · 사업 종료 상태.', ANNUAL['SSL'], 'topsoe-sasol'),
    ],
}
PRIVATE['techgen']['relations'] = [
    relation('Tenaris', 'TS', 'customer', '발전 용량22%의 계약 구매.', ANNUAL['TS']),
    relation('Tenaris', 'TS', 'partner', '22% 공동사업 참여.', ANNUAL['TS']),
    relation('Ternium', 'TX', 'partner', '48% 공동사업 참여.', ANNUAL['TS']),
    relation('Tecpetrol', None, 'partner', '30% 공동사업 참여.', ANNUAL['TS'], 'tecpetrol'),
]
PRIVATE['oryx-gtl']['relations'] = [
    relation('Sasol', 'SSL', 'partner', '49% 공동사업 참여.', ANNUAL['SSL']),
    relation('Al Khaleej Gas', None, 'supplier', '원료 가스 최소 구매량·25년 계약.', ANNUAL['SSL'], 'al-khaleej-gas'),
]
PRIVATE['al-khaleej-gas']['relations'] = [
    relation('ORYX GTL', None, 'customer', '장기 가스 구매 계약.', ANNUAL['SSL'], 'oryx-gtl'),
    relation('ExxonMobil', 'XOM', 'partner', 'Middle East Gas Marketing의 공동사업 역할.', ANNUAL['SSL']),
    relation('QatarEnergy', None, 'partner', '원문의 Qatar Petroleum 공동사업자 역할.', ANNUAL['SSL'], 'qatarenergy'),
]
PRIVATE['lip-jv-sasol']['relations'] = [
    relation('Sasol', 'SSL', 'partner', '50% 공동사업 참여.', ANNUAL['SSL']),
    relation('LyondellBasell', 'LYB', 'partner', '계열 LC Offtake50% 참여.', ANNUAL['SSL']),
    relation('Equistar Chemicals', None, 'customer', '2030년11월까지 위탁 판매 계약.', ANNUAL['SSL'], 'equistar-sasol'),
]

# Supplemental roles for an already registered multi-industry counterpart.
# Merge these facts into the common page instead of replacing older evidence.
COMMON_CONTEXT = {
    'air-liquide': {
        'description': '산업용 가스·공급 설비와 장기 가스 계약을 제공하며 Sasol Secunda의 산소 생산·전력 조달 경로에 참여합니다.',
        'description_source': AIR_LIQUIDE,
        'brief': [fact('Sasol · 실제 산소 공급', 'Air Liquide는 2021년6월부터 Sasol에서 인수한16기와 기존1기 등 Secunda의17기 공기분리 설비를 운영한다고 확인합니다. 장기 산소 공급과 예정 전력 계약의 가동은 별도입니다.', AIR_LIQUIDE),
                  fact('현재 재생 전력 · 범위', 'Sasol FY2026 원문은 공동 조달 및 외부 고객 공급을 포함한 포트폴리오와 약508 MW의 실제 운영을 구분합니다. 2024 계약 발표의690 MW를 현재 발전량으로 표시하지 않습니다.', ANNUAL['SSL'])],
        'products': [fact('산소·공기분리 설비', '공기를 분리해 합성가스·연료·화학 공정용 산소를 공급합니다. 설계 능력·실제 생산·고객 구매는 서로 다른 수치입니다.', AIR_LIQUIDE)],
        'relations': [relation('Sasol', 'SSL', 'customer', 'Secunda 장기 산소 공급 고객.', AIR_LIQUIDE),
                      relation('Sasol', 'SSL', 'partner', '재생 전력 공동 조달 · 실제 운영 상태는2026 원문 기준.', ANNUAL['SSL'])],
        'sources': [AIR_LIQUIDE, ANNUAL['SSL']],
    },
}
PUBLIC['SSL']['sources'].append(AIR_LIQUIDE)
