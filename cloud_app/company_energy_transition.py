"""Reviewed legal identities, business lines and current changes for eight issuers."""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS=('APC','BDCO','IEP','INVX','NUAI','RSRV','SUNC','TBN')
ANNUAL={s:report(s) for s in SYMBOLS}
QUARTER={s:report(s,'quarter') for s in SYMBOLS}
UPDATES={
 'APC':source('APC · Q2 실제 결과·USPP 인수 계약','https://www.sec.gov/Archives/edgar/data/2080921/000119312526337979/apc-ex99_1.htm','2026-08-06'),
 'BDCO':source('Blue Dolphin · Q2 정유 실제 결과','https://www.sec.gov/Archives/edgar/data/793306/000143774926028116/ex_967513.htm','2026-08-14'),
 'IEP':source('IEP · Q2 연결·귀속·투자 범위','https://www.ielp.com/news-releases/news-release-details/icahn-enterprises-lp-nasdaq-iep-today-announced-its-second-2','2026-08-05'),
 'INVX':source('Innovex · Q2·TCO 취득 완료','https://www.sec.gov/Archives/edgar/data/1042893/000119312526330695/invx-ex99_1.htm','2026-08-03'),
 'NUAI':source('New Era · 전력 PPA·공급 예정','https://investors.newerainfra.ai/news/news-details/2026/New-Era-Energy--Digital-Secures-20-Year-207-MW-PPA-with-Vistra/default.aspx','2026-09-21'),
 'RSRV':QUARTER['RSRV'],
 'SUNC':source('SunocoCorp · Q2·연결/NCI 범위','https://www.sec.gov/Archives/edgar/data/2089661/000208966126000043/ex991sunerq22026.htm','2026-08-04'),
 'TBN':source('Tamboran · 첫 가스 판매 실제 개시','https://ir.tamboran.com/news-events/press-releases/detail/49/tamboran-delivers-first-gas-sales-from-the-beetaloo-basin','2026-09-08'),
}
PEP_SALE=source('IEP · Mavis 의 Pep Boys 취득 완료','https://www.ielp.com/news-releases/news-release-details/mavis-completes-acquisition-pep-boys-icahn-enterprises','2026-08-20')
NUAI_TENANTS=source('New Era · 임차인 협상 단계 공시','https://www.sec.gov/Archives/edgar/data/2028336/000121390026102859/ea0306502-8k_newera.htm','2026-09-24')

PUBLIC={
 'APC':profile('ARKO Petroleum',ANNUAL['APC'],
  '2025년 설립하고 2026년 2월 상장한 ARKO 계열 연료 도매·fleet fueling 회사입니다. ticker APC 의 현재 법인은 ARKO Petroleum 이며 과거 Anadarko 생산사와 동일 기업이 아닙니다.',
  '2025 combined 매출 5,581,264,000 USD 는 제 3 자 연료 3,203,273,000·관계사 연료 2,302,547,000·기타 순매출 63,063,000·관계사 기타 12,381,000 입니다. 상장 전 이전 대상 사업의 결합 실적이며 ARKO 전체 소매 매출은 아닙니다.',
  [('도매 cost-plus','dealers·sub-wholesalers·bulk 구매자에게 연료 원가·수송·세금에 정액 마진을 붙여 판매합니다. 상품 가격과 gallon 당 이익이 같은 지표는 아닙니다.'),
   ('위탁 consignment','최종 고객 판매까지 연료 소유권과 가격 결정을 유지하며 dealer 와 gross profit 을 배분합니다. cost-plus 거래의 인도 시점·마진과 구별합니다.'),
   ('fleet cardlock','무인 상용차 주유 거점과 연료 카드·제 3 자 network 접근 서비스를 운영합니다. 회사 운영 거점과 제 3 자 카드 이용 거점을 구별합니다.'),
   ('GPMP','ARKO 소매점에 연료·공급 수수료를 제공합니다. 내부 wholesale 공급은 제거하며 2025 5cent/gallon 과 2026 6cent/gallon 계약 조건의 기간을 구별합니다.'),
   ('외부 부문 매출','2025 wholesale2,753,108,000·fleet483,779,000·GPMP2,306,808,000·All Other37,569,000 USD 합계입니다. GPMP 내부 거래를 다시 더하지 않습니다.'),
   ('상장·control','IPO2월 13일 완료·거래 2월 12일 개시,3월 추가발행 후 ARKO Parent 경제 지분 73.6%·의결권 93.3% 입니다. Class A/B 와 상장 전 100% 관계는 시점이 다릅니다.'),
   ('사업장 전환','2025 ARKO 소매점 256 곳의 dealer 전환은 공급 부문을 옮기는 변화입니다. 연료 판매 거점 2,099·ARKO 공급 1,095·cardlock295 의 역할·분모를 구별합니다.')],
  customers='독립 dealer·상용 fleet·bulk 구매자 및 ARKO 소매점입니다. ARKO 관계사 연료 매출과 외부 고객 집중도를 구별합니다.',
  inputs='정유·터미널 공급 연료, 수송·저장·dealer 부지·연료 카드·인력이 필요합니다. ARKO 의 소매 상품 조달과 APC 연료 도매 사업은 범위가 다릅니다.',
  competition='연료 도매·지역 dealer 공급·fleet fueling 을 gallon 당 마진·계약·네트워크·자금으로 비교합니다. 원유 생산량이나 광물권 매출과 비교하지 않습니다.'),
 'BDCO':profile('Blue Dolphin Energy',ANNUAL['BDCO'],
  'Texas Nixon 의 경질 저유황 원유 정제와 petroleum 저장·tolling 을 운영하는 OTC 정유 회사입니다. Nixon15,000bpd 증류 능력과 약 1.25 백만 barrel 저장 능력은 설계·저장 기준입니다.',
  '2025 연결 279,385,000 USD 는 정제 외부 276,243,000·tolling/terminal 외부 3,142,000 입니다. 부문 gross tolling5,957,000 에서 내부 2,815,000 이 제거되므로 연결 소계·gross 를 함께 더하지 않습니다.',
  [('항공유','Nixon 의 완제품 jet fuel 입니다. 대부분 LEH 에 판매하고 LEH 가 DLA 로 판매합니다. 직접 DLA 계약과 관계사 중간 판매를 구별합니다.'),
   ('나프타','경질 중간유분으로 다른 정유·혼합 원료에 판매합니다. 최종 자동차 휘발유 직접 판매와 구별합니다.'),
   ('HOBM·AGO','유전 mud 용 base 와 atmospheric gas oil 등 중간제품입니다. 제품 slate 는 수요·원료·정제 운전 조건에 따라 달라집니다.'),
   ('원유·수송','MV Purchasing 의 Eagle Ford 경질 원유 계약과 제 3 자 truck 인도입니다. 분기 자동 갱신 계약을 장기 고정 공급 보장으로 표시하지 않습니다.'),
   ('저장 terminaling','고객별 탱크 규모·기간 수수료입니다. 저장 가능 barrel 과 당기 throughput·제품 판매량은 다릅니다.'),
   ('tolling','naphtha stabilizer throughput gallon/barrel 료와 월 reservation 료입니다. 고객 상품을 처리하는 수수료와 자체 원유 정제 판매를 구별합니다.'),
   ('운영 법인·관계사','Lazarus Energy 와 Lazarus Refining & Marketing 은 회사 자회사, LEH 는 지배 주주 측 판매·운영 관계사입니다. 같은 Lazarus 이름만으로 100% 소유를 추정하지 않습니다.')],
  customers='PADD3 도매·정유 고객과 관계사 LEH, 저장/tolling 고객입니다. 제 3 자 수출 고객의 최종 목적지와 회사 직접 해외 소매사업은 다릅니다.',
  inputs='경질 원유·응축유, 증류·stabilizer·tank·truck·인력·정비·허가가 필요합니다. 원유 cost·crack spread·운전자본·관계사 계약이 영향을 줍니다.',
  competition='Gulf Coast 정유·항공유·중간제품 공급과 저장 서비스를 원료·yield·제품 가격·물류·가동률로 비교합니다. 설계 15,000bpd 를 실제 일일 처리량으로 표시하지 않습니다.'),
 'IEP':profile('Icahn Enterprises',ANNUAL['IEP'],
  '투자와 에너지·자동차·식품 포장·부동산·홈 패션·제약의 7 개 보고 부문을 가진 diversified partnership 입니다. CVR 에너지 연결 사업이 크지만 IEP 전체를 정유 단일 회사로 설명하지 않습니다.',
  '2025 전체 9,658 백만 USD 는 에너지 7,188·자동차 1,423·포장 362·부동산 336·홈패션 171·제약 105·투자 12·holding61 입니다. 투자 순손익·다른 영업 수익과 고객 계약 매출은 범위가 다릅니다.',
  [('CVR 정유','Coffeyville·Wynnewood 의 휘발유·경유·jet·pet coke 등을 생산합니다. 연결 CVR 전체 매출과 IEP 경제 지분 귀속을 구별합니다.'),
   ('질소 비료','CVR Partners 의 UAN·ammonia 입니다. Coffeyville pet coke 공정과 East Dubuque 천연가스 공정의 원료·cost 가 다릅니다.'),
   ('투자 펀드','자체 및 Icahn 가족·계열 자본을 운용합니다. 외부 고객에게 공개 판매하는 자산운용사 AUM·수수료와 다르며 매매·평가 손익이 포함됩니다.'),
   ('자동차 서비스','2025 Pep Boys 등이 포함된 과거 서비스 부문입니다. 2026년 8월 20일 Mavis 에 Pep Boys 매각 완료, AAMCO·Precision Tune 과 소유 부동산은 보유합니다.'),
   ('Viskase 포장','cellulosic·fibrous·plastic meat casing 입니다. 2025 말 93% 라는 과거 지분과 이후 Enzon 거래·현재 법인 범위를 구별합니다.'),
   ('부동산·home','임대·주택 개발·resort 와 WestPoint Home 소비자 섬유 제품입니다. 임대료·주택 매각·제조 판매는 다른 수익입니다.'),
   ('Vivus 제약','체중 관리·췌장 효소 결핍 승인 치료제와 개발 pipeline 입니다. 연결 holding 의 사업이며 에너지 매출에 합치지 않습니다.')],
  customers='부문별 fuel marketer·비료 retailer·자동차 서비스 소비자·식품 제조·임차인·의약 수요입니다. 자가 투자·제 3 자 고객·관계사 거래를 구별합니다.',
  inputs='정유 원료·비료 gas/pet coke·서비스 인력·포장 원료·섬유·연구/유통과 투자·부동산 자금입니다. 한 가지 원유 가격 노출로 전체사업을 설명하지 않습니다.',
  competition='각 영업회사의 산업 경쟁과 investment NAV·레버리지·펀드 손익을 구별합니다. indicative NAV 는 시장가격·GAAP equity·매출과 다릅니다.'),
 'INVX':profile('Innovex International',ANNUAL['INVX'],
  '유정 건설·완결·생산·intervention 의 육상·해양 장비와 서비스를 제공합니다. 2024년 9월 6일 Innovex Downhole 과 Dril-Quip 결합 후 현재 법인명이며 단순 Dril-Quip 과거 해양 장비 회사가 아닙니다.',
  '2025 연결 978,251,000 USD 는 제품 685,293,000·서비스 126,263,000·임대 166,695,000 입니다. NAM511,156,000·국제/해양 467,095,000 시장 구분과 10 개 지리 항목은 각각 독립 표입니다.',
  [('well construction','centralizer·float equipment·casing packer·stage cementing tools 로 casing 고정·cement 배치를 지원합니다.'),
   ('well completion','liner hanger·toe sleeve·frac plug·completion packer·casing flotation 으로 자극·생산 개시를 지원합니다.'),
   ('surface wellhead','시추·생산·thermal·artificial lift 용 지상 wellhead·frac system 입니다. 유정 자체 생산 판매와 구별합니다.'),
   ('subsea','해저 wellhead·connector·casing connector·centralization·diverter 입니다. 2025년 7월 subsea tree 제품군을 처분했으므로 현재 핵심 제품으로 표시하지 않습니다.'),
   ('artificial lift 지원','ESP penetrator·tubing hanger·adapter·cable management·spooling 입니다. pump 본체와 접근·설치 보조 제품은 다른 역할입니다.'),
   ('fishing·intervention','걸린 drill string·도구·잔해 회수와 well repair 입니다. 제품 판매·임대·현장 service/mileage 청구를 구별합니다.'),
   ('Citadel·TCO','2025년 5월 30일 Citadel Casing Solutions 취득과 2026년 7월 1일 TCO Group AS 취득은 완료 거래입니다. TCO 는 2025 연차에 소급 포함되지 않습니다.')],
  customers='E&P·국영/국제 생산사·oilfield service 고객입니다. 이름 없는 Malaysia tension package 고객이나 예상 wellhead award 를 특정 생산사·완료 수주로 추정하지 않습니다.',
  inputs='steel·machining·seal·기술/설계·manufacturing·rental fleet·현장 인력이 필요합니다. 지리 판매·상품 구성·시추 활동은 다른 매출 구분입니다.',
  competition='유정 도구·wellhead·subsea·lift support 를 성능·납기·시공·신뢰성으로 비교합니다. 회사 TAM 기반 시장점유율 추정은 독립적으로 확인한 시장 자료와 구별합니다.'),
 'NUAI':profile('New Era Energy & Digital',ANNUAL['NUAI'],
  'New Era Helium 에서 Texas 데이터센터·전력 인프라 개발로 전환한 회사입니다. 과거 gas 생산 매출과 현재 powered land/shell 개발, 미래 임차인·전력 공급을 구별합니다.',
  '2025 기존 사업 매출 885,400 USD 는 가스 순매출 645,478·NGL239,922 입니다. 가스 gross2,516,970 에서 집하·처리 1,871,492 를 차감한 순매출과 gross 를 함께 더하지 않습니다. 데이터센터 예상 용량을 현재 매출로 표시하지 않습니다.',
  [('legacy gas','기존 가스·NGL·helium 관련 광구의 과거 매출입니다. 회사명 변경과 원료 helium 생산/판매 완료는 같은 사건이 아닙니다.'),
   ('TCDC 개발','Ector County 캠퍼스의 토지·허가·전력·fiber 를 묶는 개발입니다. 2025 연차 438acre 와 9월 발표 493acre·장기 1.4GW 계획은 기준 시점이 다릅니다.'),
   ('powered land·shell','전력 확보 토지·건물 또는 build-to-suit 임대 개발입니다. grid/behind-the-meter 구성과 완공·임차인·매출 개시를 따로 봅니다.'),
   ('TCDC 지분','2026년 1월 16일 SharonAI 의 50% 를 취득했습니다. 과거 50:50 JV 를 현재 지분 구조로 표시하지 않으며 지급·전환사채 의무와 소유 지분을 구별합니다.'),
   ('Luminant PPA','9월 21일 TCDC PowerCo 의 20년 200–207MW 계약입니다. Vistra Odessa 시설 공급은 2027Q3 예정이며 현재 데이터센터가 가동 중이라는 증거가 아닙니다.'),
   ('조건부 발전 partner','전력 인도 시작 후 해당 powered project 부분 Vistra5% 비의결권을 예정한 framework 입니다. 현재 확정 지분이나 회사 전체 5% 로 표시하지 않습니다.'),
   ('임차인·자금','9월 24일 공시는 여러 잠재 anchor tenant 와 협상 중입니다. 익명 hyperscaler 의 이름·서명 임대·완공 여부를 추정하지 않습니다.')],
  customers='기존 gas 구매 경로와 미래 hyperscaler·enterprise·edge 임차인은 단계가 다릅니다. PPA 공급 상대와 데이터센터 임차 고객은 같은 역할이 아닙니다.',
  inputs='토지·허가·firm power·grid·gas·fiber·냉각·construction·자금·tenant credit 이 필요합니다. 전력 확보만으로 건설·상업 가동의 모든 조건이 충족되지는 않습니다.',
  competition='데이터센터의 납기·전력 접근·개발/임대·자금과 legacy gas 를 구별합니다. plannedGW·전력 PPA MW·가동 MW·compute 매출의 분모를 혼합하지 않습니다.'),
 'RSRV':profile('Reserve Petroleum',ANNUAL['RSRV'],
  '미국 mineral property 를 관리하고 비운영 working interest·royalty 로 원유·천연가스 탐사/개발에 참여합니다. 자체 시추를 모두 직접 운영하는 회사가 아니며 royalty 와 비용 부담 working interest 가 다릅니다.',
  '2025 연결 17,441,161 USD 는 원유/가스 16,699,954 와 lease bonus·기타 741,207 입니다. 상품은 원유 11,549,413·가스 4,802,719·기타 347,822 이며 oil/gas 소계를 다시 더하지 않습니다.',
  [('mineral management','12 개주 nonproducing net88,868acre, 주요 Arkansas·Kansas·Oklahoma·South Dakota·Texas 입니다. 순 acre·총 acre 와 현재 생산 유정 면적은 다릅니다.'),
   ('royalty','광물권 lease/farmout 대가와 생산 수익을 받습니다. 2025 royalty/기타 3,425,011 USD 는 oil/gas 판매의 부분집합이며 다시 더하지 않습니다.'),
   ('working interest','제 3 자 operator 의 탐사·개발 비용을 지분에 따라 부담합니다. net well·gross well·royalty percentage 는 같은 지분 기준이 아닙니다.'),
   ('원유 판매','생산 operator 가 고객·인도 지점·local index 계약을 관리하고 회사 몫을 정산합니다. 시장가격·유정 생산·현금 정산의 시차를 구별합니다.'),
   ('가스 판매','월별 인도·가격·volume 기준입니다. operator 의 gross gas 판매와 회사 지분 매출은 다릅니다.'),
   ('lease bonus','광물권 계약의 upfront bonus·기타 수익입니다. 원유/가스 단위 상품 매출 지표와 별도 원문 회계 범위입니다.'),
   ('Bailey Hilltop','Grady County gas gathering pipeline LLC 의 10% 투자입니다. 비연결 지분법 investee 이며 전체 pipeline 매출을 회사 매출에 더하지 않습니다.')],
  customers='2025 Crawley Petroleum33%·Mewbourne Oil19% 는 공시 oil/gas 판매 집중도입니다. 전체기업 시장점유율·두 회사 보유 지분과 구별합니다.',
  inputs='광물권·operator 의시추/완결·pipeline·운송·처리·lease operating cost·인허가입니다. mineral/royalty 와 working interest 의 투자·통제 책임이 다릅니다.',
  competition='광구·mineral lease·기술·비용·operator 개발 일정으로 비교합니다. commodity 구매 고객이 operator 이기도 한 역할을 근거 없이 다른 지분 관계로 바꾸지 않습니다.'),
 'SUNC':profile('SunocoCorp LLC',ANNUAL['SUNC'],
  'Sunoco LP Class D unit 을 보유하는 상장 LLC 입니다. 2025년 Parkland 거래와 함께 상장했고 unit 당 SUN 경제 권리에 대응하지만 법인·세금·비지배 지분 범위가 다릅니다.',
  '2025 재무는 SUN 을 모든 비교 기간 연결한 25,201 백만 USD 입니다. 연료/상품 23,702·서비스 1,369·임대 130 이며 이 전체 매출이 SUNC unitholder 에게 100% 귀속되는 현금은 아닙니다.',
  [('holding·경제 권리','SUNC 의 SUN Class D unit 과 별도 상장 common unit 은 일반적으로 1:1 경제 권리에 대응합니다. SUN 운영 자산을 SUNC 가 100% 직접 소유한다는 뜻은 아닙니다.'),
   ('연료 유통','dealer·distributor·commercial·retail fuel 공급입니다. 연료 가격·판매 gallon·마진과 관련 소매 매출을 구별합니다.'),
   ('파이프라인','원유·정유제품 수송 수수료와 예약 용량입니다. ET 계열 연결·JV 운영과 단순 100% 자회사 관계를 구별합니다.'),
   ('터미널','저장·throughput·독일/Poland TanQuid 사업입니다. 2026년 1월 16일 취득 완료와 2025 비교 범위를 구별합니다.'),
   ('Parkland 정유·유통','2025년 11월 Parkland 취득 후 Canada·국제 유통·Burnaby 정유 등이 편입됩니다. 2025 는 취득 이후 부분 실적이며 전체 2026 연간 실적을 소급 넣지 않습니다.'),
   ('지배·법인','Energy Transfer 가 SunocoCorp Manager·SUN GP 를 소유하는 관리/control 관계입니다. SUNC 상장 unit 의 100% 경제 소유와는 다릅니다.'),
   ('NCI·배당','SUN 전체의 연결 EBITDA/DCF 와 SUNC common unitholder 에게 전달되는 SUN 분배금을 구별합니다. 연결 현금을 모두 SUNC 배당 가능액으로 표시하지 않습니다.')],
  customers='SUN 의 연료 dealer·retailer·산업·pipeline/terminal shipper 입니다. SUNC 자체 보유 unit·투자자와 운영 고객은 다릅니다.',
  inputs='SUN 의 fuel 조달·pipeline·tank·refinery·운송·retail 인력·자금입니다. SUNC holding 의 unit·관리·세금 비용과 운영사업 원가를 구별합니다.',
  competition='SUN 운영 사업의 경쟁과 holding unit의 구조·세금·분배 권리는 다른 비교입니다. SUNC와 SUN을 함께 더해 산업 전체 매출로 계산하지 않습니다.'),
 'TBN':profile('Tamboran Resources',ANNUAL['TBN'],
  'Australia Northern Territory Beetaloo 의 shale gas 를 개발하고 2026년 9월 Shenandoah South 첫 가스 판매를 시작했습니다. US 상장 법인·Australia 운영/JV·광구 working interest·공급 계약은 각각 다른 범위입니다.',
  '2026년 6월 30일 종료 연차에는 가스 판매 매출이 없으며 이후 9월 첫 판매가 시작됐습니다. 원문의 dash 를 세부 제품별 매출 0 으로 발명하지 않고 과거 무매출과 현재 생산 전환을 함께 설명합니다.',
  [('Beetaloo shale','수평정과 파쇄로 분지의 shale gas를 개발합니다. 탐사 자원, 총면적, 배관 용량, 회수 가능 매장량과 실제 생산은 서로 다른 지표입니다.'),
   ('Shenandoah South','Pilot 가스의 NT 시장 인도는9월에 시작했습니다. gross 40TJ/d 목표 plateau는 NT정부 주문량·유정 성능·최종 시운전에 따라 늘어납니다. 이미40TJ/d를 지속 판매 중이라고 표시하지 않습니다.'),
   ('가스 처리·SPCF','Shenandoah South 처리시설의 건설·시운전·실제 판매 가스를 구별합니다. 전체 시설 용량과 회사 경제 지분 기준 생산은 다릅니다.'),
   ('APA transport','Sturt Plateau pipeline이 Amadeus 망에 연결합니다. 7월 practical completion과9월 판매 가스 수취·수송료 개시는 향후 East Coast 배관 계획과 다릅니다.'),
   ('Falcon 취득','2026년5월 28일 Falcon 거래를 완료해 FOGA 약98.1%와 관련 자산을 취득했습니다. 잔여 소수 지분 강제 취득, Daly Waters 면적 재배치 조건, 과거77.5/22.5 광구 JV의 분모를 구별합니다.'),
   ('service 투입','H&P FlexRig, Liberty의 파쇄 서비스, Baker Hughes 기술 관계입니다. 공급 서비스와 상장사 지분 투자자 역할, 발표 MOU의 확대 범위는 다릅니다.'),
   ('장기 판로','NT정부의 실제 pilot 구매 계약과 BP·Shell의 비구속 LNG MOU, 동부 retailer LOI를 구별합니다. NT LNG와 동부 배관은 향후 계획이며 현재 가동 수출 터미널로 표시하지 않습니다.')],
  customers='현재 NT정부 pilot 계약과 미래 Australia East Coast·국제 LNG 구매 기회입니다. 비구속 MOU/LOI, 계약 최대 수량과 실제 판매를 구별합니다.',
  inputs='광구·용수·proppant·rig·파쇄·처리·배관·자금·허가가 필요합니다. 회사 순지분, JV 전체 용량과 발전·수출 계획을 같은 현재 매출로 합산하지 않습니다.',
  competition='Australia 국내 가스·개발 원가·배관 출구·LNG 기회로 비교합니다. Henry Hub 가격 비교와 예상 시장 규모를 이미 획득한 점유율로 표시하지 않습니다.'),
}
LATEST={
 'APC':'8월 6일 US Petroleum Partners 사업 취득 계약 발표는 서명 단계입니다. 예상 연간 280백만 gallon과 조정 EBITDA 30백만 USD는 향후 편입 추정입니다. 취득 완료나 현재 매출로 표시하지 않습니다.',
 'BDCO':'8월 14일 Q2 매출·마진·운전 결과는 해당 분기의 증거입니다. 지배 주주 측 지분은 연차84.4%, Q2 Jonathan Carroll/LEH 합산85.1%로 각 공시 시점이 다릅니다. 회사의100% 소유를 뜻하지 않습니다.',
 'IEP':'Q2 발표의 CVI 보유 약71%와2025년말 약70%는 시점이 다릅니다. 8월 20일 Pep Boys 매각을 완료했고, 자동차 보유 부동산·AAMCO·Precision Tune은 남아 있습니다. 귀속 손실과 indicative NAV도 연결 매출과 구별합니다.',
 'INVX':'7월 1일 TCO Group AS 취득 완료를8월 3일 Q2에 공개했습니다. 수주·예상 계약과 당기 매출,2025년 Citadel 부분 편입과 pro forma 전년 매출의 범위를 구별합니다.',
 'NUAI':'9월 21일 PPA 서명은 확인됐지만 전력 공급은2027년3분기 예정입니다. 9월 24일 anchor 임차인 협상은 확정 고객 계약이 아닙니다. 원문이 공개하지 않은 AI 기업 이름을 추정하지 않습니다.',
 'RSRV':'2026년6월 30일 분기는 원유·가스·lease·지분 투자 비교 자료입니다. 분기와2025년 연간, operator가 수취한 gross 매출과 회사 몫을 구별합니다.',
 'SUNC':'8월 4일 Q2 발표의 SUN 전체 연결 매출14,259백만과 SUNC member 귀속 이익39백만 USD는 범위가 다릅니다. 전체 연결 DCF를 SUNC 배당 가능 현금으로 표시하지 않습니다.',
 'TBN':'9월 8일 첫 가스 판매 개시와 FY2026 연차의6월 30일 무매출 기간을 구별합니다. 처리시설 시운전은 추가 진행 중이며, plateau 도달·LNG 확장은 향후 계획입니다.',
}
for _s,_p in PUBLIC.items():
 _p['brief'].append(fact('최근 실제 상태·비교 범위',LATEST[_s],UPDATES[_s]))
 _p['sources'].extend([QUARTER[_s],UPDATES[_s]])
 _p['filings']=[ANNUAL[_s],QUARTER[_s]]
 _p['revenue_mix']=REPORTS[_s]['revenue_mix']
 _p['segments']=_p['products'][:3]
 _p['drivers']=[fact('가동·거래·기간',LATEST[_s],UPDATES[_s]),fact('투입·원가',_p['brief'][3]['detail'],ANNUAL[_s])]
 _p['financial_context']=[fact('연결·경제 지분·계량 범위','원문 연차 기간·통화·단위를 따릅니다. 상장 전 결합 사업, 취득 후 편입, 전체 연결, 비지배 지분, JV, gross/net, lease, 투자 순손익을 구별합니다. 발표 계획이나 미래 용량을 현재 매출로 표시하지 않습니다.',ANNUAL[_s])]
PUBLIC['IEP']['sources'].append(PEP_SALE)
PUBLIC['NUAI']['sources'].append(NUAI_TENANTS)
PUBLIC['NUAI']['brief'].append(fact('허가·일정 변경', '9월 24일 공시는 9월 21일 Texas 데이터센터 허가 중지와 ERCOT 감사에 따른 air permit 등 지연 가능성을 명시합니다. PPA 서명만으로 전체 허가가 완료됐다고 설명하지 않습니다.', NUAI_TENANTS))

_PARTIES=[
 ('gpm-petroleum','GPM Petroleum LP','APC','subsidiary',ANNUAL['APC'],'GPMP 연료 도매와 ARKO 소매 공급 운영 법인입니다. 계열 공급과 내부 거래 제거를 구별합니다.'),
 ('us-petroleum-partners','US Petroleum Partners LLC','APC','transaction',UPDATES['APC'],'8월 6일 사업 취득 계약의 서명 상대입니다. 취득 완료 공시는 확인하지 않았으며 현재100% 자회사로 표시하지 않습니다.'),
 ('lazarus-energy','Lazarus Energy LLC','BDCO','subsidiary',ANNUAL['BDCO'],'Nixon 정유 운영 자회사입니다. 지배 주주 측 LEH 관계사와 다른 법인입니다.'),
 ('lazarus-refining','Lazarus Refining & Marketing LLC','BDCO','subsidiary',ANNUAL['BDCO'],'Tolling·terminaling 관련 회사 자회사입니다. 지배 주주 측 LEH와 구별합니다.'),
 ('lazarus-energy-holdings','Lazarus Energy Holdings LLC','BDCO','customer',ANNUAL['BDCO'],'항공유의 주요 관계사 구매자이며 지배 주주 측 운영 역할도 있습니다. 최종 DLA 판매가 BDCO의 직접 DLA 계약은 아닙니다.'),
 ('mv-purchasing','MV Purchasing LLC','BDCO','supplier',ANNUAL['BDCO'],'Nixon의 경질 Eagle Ford 원유 공급과 terminal storage 계약 상대입니다. 분기 자동 갱신 계약과 장기 공급 확약을 구별합니다.'),
 ('icahn-automotive','Icahn Automotive Group LLC','IEP','subsidiary',UPDATES['IEP'],'자동차 서비스 holding입니다. Pep Boys 처분 후 보유 부동산·AAMCO·Precision Tune 잔여 사업과2025년 사업 범위를 구별합니다.'),
 ('westpoint-home','WestPoint Home LLC','IEP','subsidiary',ANNUAL['IEP'],'홈 섬유 제조·조달·유통 운영 자회사입니다. 에너지 매출과 다른 산업입니다.'),
 ('vivus-pharma','Vivus LLC','IEP','subsidiary',ANNUAL['IEP'],'승인 치료제·개발 의약품 자회사입니다. 연결 영업 사업과 holding의 투자 매매 역할을 구별합니다.'),
 ('citadel-casing','Citadel Casing Solutions LLC','INVX','subsidiary',ANNUAL['INVX'],'2025년5월 30일 취득한 downhole casing 기술 사업입니다. 취득 전 pro forma 매출과 실제 연차 편입은 다릅니다.'),
 ('tco-group','TCO Group AS','INVX','subsidiary',UPDATES['INVX'],'2026년7월 1일 취득을 완료한 국제 유정 기술 사업입니다. 2025년 연차에 소급 포함되지 않습니다.'),
 ('texas-critical-data','Texas Critical Data Centers LLC','NUAI','subsidiary',ANNUAL['NUAI'],'2026년1월 16일 SharonAI의50% 지분 취득 후 개발 자회사입니다. 과거50:50 JV, 현재 지분과 전환사채 지급 의무를 구별합니다.'),
 ('tcdc-powerco','TCDC PowerCo LLC','NUAI','subsidiary',UPDATES['NUAI'],'9월 21일 Luminant PPA를 체결한 전력 계약 자회사입니다. 전력 공급은2027년3분기 예정입니다.'),
 ('luminant-et','Luminant ET Services Company LLC','NUAI','supplier',UPDATES['NUAI'],'Vistra 계열 PPA 법인입니다. 최소200·최대207MW 확정 계약과2027년3분기 전력 가용 예정 시점을 구별합니다.'),
 ('crawley-petroleum','Crawley Petroleum Corporation','RSRV','customer',ANNUAL['RSRV'],'2025년 공시 원유·가스 매출33% 구매 상대입니다. 회사 전체 시장점유율이나 지분 소유로 해석하지 않습니다.'),
 ('mewbourne-oil','Mewbourne Oil Company','RSRV','customer',ANNUAL['RSRV'],'2025년 원유·가스 매출19% 구매 상대입니다. Working interest operator, 상품 구매와 회사 소유 관계는 근거 범위가 다릅니다.'),
 ('bailey-hilltop','Bailey Hilltop Pipeline LLC','RSRV','partner',ANNUAL['RSRV'],'Oklahoma Grady County 가스 집하 시스템의10% 비연결 투자입니다. 전체 pipeline 매출을 회사 매출에 합산하지 않습니다.'),
 ('sunococorp-manager','SunocoCorp Manager LLC','SUNC','partner',ANNUAL['SUNC'],'Energy Transfer가100% 소유한 SUNC 관리 법인입니다. SUNC unit의 경제100% 소유를 의미하지 않습니다.'),
 ('daly-waters-energy','Daly Waters Energy LP','TBN','partner',ANNUAL['TBN'],'Beetaloo 광구·면적 재배치·Shenandoah JV 파트너입니다. 전체 광구 working interest와 상장사 지분은 다릅니다.'),
 ('nt-government','Northern Territory Government','TBN','customer',ANNUAL['TBN'],'Pilot 가스 구매 계약 상대이자9월부터 실제 가스를 인도하는 시장입니다. Gross 40TJ/d 최대 plateau·주문량과 실제 판매를 구별합니다.'),
 ('apa-australia','APA Group · Australia','TBN','supplier',ANNUAL['TBN'],'Sturt Plateau·Amadeus 접속 가스 수송 상대입니다. Australia APA Group과 US상장 APA 생산사는 다른 기업입니다.'),
]
PRIVATE,EDGES={}, {s:[] for s in SYMBOLS}
for _key,_name,_s,_kind,_origin,_detail in _PARTIES:
 PRIVATE[_key]=profile(_name,_origin,_detail,'확인한 해당 사업 역할을 설명하며 상대 전체 매출·지분·순위는추정하지 않습니다.',[('확인한 역할',_detail)],customers='근거가 공개된연결 사업·거래·가치사슬역할입니다.')
 EDGES[_s].append(relation(_name,None,_kind,_detail,_origin,_key))
EDGES['APC'].append(relation('ARKO','ARKO','partner','ARKO Parent 경제 73.6%·의결권 93.3% 는 3월 IPO 추가 발행 후입니다. APC 도매와 ARKO 소매를구별합니다.',ANNUAL['APC']))
EDGES['IEP'] += [relation('CVR Energy','CVI','subsidiary','2025 말약 70%·Q2 약 71% 연결 지배 사업. 전체 연결 매출과경제 귀속을구별.',UPDATES['IEP']),relation('CVR Partners','UAN','partner','2025 말 IEP 직접 3% 외에 CVI 보유 37%·GP control 경로를구별. 100% 직접 소유가 아님.',ANNUAL['IEP'])]
EDGES['NUAI'].append(relation('Vistra','VST','partner','Luminant PPA·개발 framework. 전력 인도 후 특정 project 부분 5% 비의결권 예정과 현재 지분을 구별.',UPDATES['NUAI']))
EDGES['SUNC'] += [relation('Sunoco LP','SUN','partner','Class D unit·경제 권리·회계 연결과 SUN 전체 unit100% 직접 소유는다름.',ANNUAL['SUNC']),relation('Energy Transfer','ET','partner','Manager·SUN GP 관리/control 소유. 상장 SUNC 경제 지분 100% 가 아님.',ANNUAL['SUNC'])]
EDGES['TBN'] += [relation('Helmerich & Payne','HP','supplier','FlexRig 실명 시추 계약과추가 rig 옵션을구별.',ANNUAL['TBN']),relation('Liberty Energy','LBRT','supplier','frac fleet/service 실명 관계와 2026년 9월확대 MOU·실제 서비스를구별.',ANNUAL['TBN']),relation('BP','BP','partner','미래 NTLNG 비구속 20년 offtake MOU. 현재 가동구매계약이 아님.',ANNUAL['TBN']),relation('Shell','SHEL','partner','미래 LNG 비구속 MOU. 실제 NT pilot gas 판매와 다름.',ANNUAL['TBN'])]

# The non-inline APC annual distinguishes a 2,112 USD-thousand shell from the business.
PUBLIC["APC"]["financials"]=[dict(label=label,value=value,unit="USD",period="2025-01-01 – 2025-12-31 · combined",source=ANNUAL["APC"]) for label,value in [("매출 · 이전 대상 결합 사업",5581264000),("순이익 · 결합 사업",32727000),("총자산 · 결합 사업",1273474000),("총부채 · 결합 사업",1237359000),("순투자 · ARKO Parent",36115000),("현금 · 결합 사업",15556000)]]
