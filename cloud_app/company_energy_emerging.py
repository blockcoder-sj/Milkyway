"""Primary-source notes for recent issuers and OTC operating businesses."""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('AMEN', 'EROK', 'FTW', 'HMH', 'NUCL', 'UNTC', 'WHK')
ANNUAL = {s: report(s) for s in SYMBOLS}
QUARTER = {s: report(s, 'quarter') for s in SYMBOLS}
FTW_CANYON = source('Presidio · Canyon Creek 인수 완료',
    'https://ir.bypresidio.com/news-events/press-releases/detail/129/presidio-closes-canyon-creek-acquisition', '2026-07-02')
FTW_RESULTS = source('Presidio · Q2 실제 결과·인수 후 범위',
    'https://ir.bypresidio.com/news-events/press-releases/detail/131/presidio-production-company-announces-second-quarter-2026-results', '2026-08-11')
HMH_DWR = source('HMH · Deepwater Riser Services 인수 완료',
    'https://investor.hmhw.com/news-releases/news-release-details/hmh-completes-acquisition-deepwater-riser-services-deepening-its', '2026-09-21')
UNTC_PRESENTATION = source('Unit · 2025 생산·처분·개발 보충',
    'https://unitcorp.com/wp-content/uploads/2026/03/2026-UNTC-Investor-Presentation.pdf', '2026-03-12')

PUBLIC = {
 'AMEN': profile('Amen Properties', ANNUAL['AMEN'],
  'SFF Production의 원유·가스 생산 지분과 SFF Royalty의 로열티 투자, Midland의 잔여 부동산 지분을 보유하는 OTC 회사입니다. 과거 인터넷 포털·전력 소매·전력 관리 사업과 현재 자산을 구별합니다.',
  '2025년 미감사 연결 영업 매출은 2,348,341 USD입니다. SFF Royalty 지분법 이익 1,031,347 USD와 기타 이익은 영업 외 수익이므로 상품 매출에 더하지 않습니다. 원문은 원유·가스별 판매액을 나누지 않아 임의 구성비를 만들지 않습니다.',
  [('SFF Production', '2014년 잔여 지분 취득 이후 100% 연결 자회사입니다. 생산 비용을 부담하는 working interest와 순이익 권리를 통해 원유·가스 수입을 받습니다.'),
   ('SFF Royalty', '2007년 취득한 3분의 1 지분 투자입니다. 지분법 이익과 현금 분배를 구별하며 투자 대상 전체 매출을 연결 매출에 합산하지 않습니다.'),
   ('원유·가스 권리', 'Santa Fe Energy Trust와 Devon의 과거 자산 거래에서 취득한 여러 주의 권리입니다. 2007년 매도 상대를 현재 유일한 구매자·운영사로 추정하지 않습니다.'),
   ('잔여 부동산', 'Midland Superblock 주차용 부지의 18% 지분을 보유합니다. 2014년 매각한 사무실 건물 지분은 현재 보유 건물로 표시하지 않습니다.'),
   ('처분 수익', '2026년 Q2 leasehold 매각·양도 이익은 966,448 USD, 상반기는 3,286,658 USD입니다. 생산 상품 판매와 자산 처분 수익의 반복성을 구별합니다.'),
   ('현금·투자', '2025년말 현금 2,825,331 USD, SFF Royalty 장부가 86,955 USD입니다. 투자 장부가, 지분법 이익, 분배 현금은 같은 수치가 아닙니다.'),
   ('종료한 사업', 'W Power 전력 소매는 2008년 중단했고 Priority Power Management는 2010년 매각했습니다. NEMA 관련 법인도 2010년 해산되어 현재 자회사로 표시하지 않습니다.')],
  customers='생산 지분 수입은 유정 운영사와 구매자의 생산·정산에 의존합니다. 확인한 미감사 보고서는 현재 구매 상대를 실명으로 구분하지 않아 추정 고객을 연결하지 않습니다.',
  inputs='생산 지분의 유정 운영·정비·운송 비용과 권리 관리, 법인 비용이 필요합니다. 로열티 지분 투자와 비용을 부담하는 생산 지분의 현금 흐름은 다릅니다.',
  competition='광물권·생산 지분의 가격, 운영사 개발, 비용과 현금 분배를 비교합니다. 미감사 OTC 수치와 감사된 대형 생산사 수치를 같은 신뢰도로 표시하지 않습니다.'),
 'EROK': profile('EagleRock Land, LLC', ANNUAL['EROK'],
  'Permian의 Delaware·Midland 분지에서 토지 사용권, 용수·생산수 인프라와 관련 사용료·로열티를 관리합니다. 지표 토지를 통해 수입을 얻으며 지하 원유·가스 광물권을 직접 보유하는 생산 로열티 회사와는 사업 구조가 다릅니다.',
  '2025년 L&E 전신의 감사 매출 72,173,000 USD는 외부 용수 55,199,000·관계사 용수 509,000·토지 사용 및 기타 16,465,000 USD입니다. 상장 때 편입한 DE Flow·Shallow Valley의 과거 실적이나 예상 로열티를 이 전신 매출에 더하지 않습니다.',
  [('표면 사용 계약', '유정 부지·도로·파이프라인·전력선의 사용권과 통행권, 손상 보상·임대로 수입을 얻습니다. 토지 면적과 지하 생산 지분을 같은 소유 비율로 해석하지 않습니다.'),
   ('용수·caliche', '완결에 쓰는 용수와 도로·유정 부지용 caliche·표토를 공급합니다. 가스·원유 판매량이 아니라 물 수량·자원 판매·표면 이용 계약이 수익 기준입니다.'),
   ('Hydrosource 재활용', '5월 15일 실제 체결한 10년 계약입니다. 토지 내 재생수의 판매가 기준 로열티, 통과 수수료와 최초 5년 연 5백만 USD 최소 로열티를 구별합니다. 계약 최소액은 실제 당기 수입이 아닙니다.'),
   ('DE Flow 운영', 'DE IV Flow의 인프라는 편입하고 DEF Operating은 Double Eagle 측 운영 파트너로 남습니다. 운영계약 상대와 회사 소유 자산을 구별합니다.'),
   ('상장·법인 구조', '5월 15일 IPO 후 EagleRock Land Operating LLC가 운영 법인입니다. Class B는 의결권을 갖지만 상장 LLC의 경제 권리가 없으며 OpCo 보유 지분과 대응 관계를 따릅니다.'),
   ('Hydrosource 분리', 'IPO 직전 Hydrosource Logistics를 HL HoldCo에 분배했습니다. 2025년 전신 실적에는 포함되지만 현재 100% 자회사로 표시하지 않습니다.'),
   ('신규 토지 취득', '8월 10일 Hydrosource가 보유하던 Intrepid 관련 토지·물 권리·계약·허가를 약 78.2백만 USD에 취득했습니다. 약 22,000 fee acres와 28,000 연방 grazing acres는 서로 다른 권리입니다.')],
  customers='토지와 물을 쓰는 생산사·인프라 운영사입니다. Q2 상위 고객 A~D의 18·15·13·12% 집중도는 익명 공시이며 알려진 파트너 이름으로 대체하지 않습니다.',
  inputs='토지·용수 권리·생산수 처리·배관·파트너 운영·허가·자금이 필요합니다. 광물권 생산 투자와 토지·물 권리 취득, 재생수 운영 파트너의 비용을 구별합니다.',
  competition='Permian의 토지 접근성, 물 조달·처리·재활용, 장기 사용 계약과 대체 공급 경로를 비교합니다. 데이터센터·태양광·탄소 저장 등의 잠재 용도는 이미 발생한 매출로 표시하지 않습니다.'),
 'FTW': profile('Presidio Production Company', ANNUAL['FTW'],
  '기존의 성숙한 원유·가스 유정을 인수하고 운영·정비·데이터 분석으로 생산과 현금 흐름을 최적화하는 회사입니다. 2026년 3월 4일 EQV Ventures와 사업 결합을 마쳤으며 Western Anadarko에서 Arkoma로 확장했습니다.',
  '2025년 PIH 전신 매출 179,056,000 USD는 원유 81,640,000·가스 50,309,000·NGL 45,864,000·현장 서비스 1,243,000 USD입니다. EQV의 과거 SPAC 재무, 별도 EQVR 실적과 결합 pro forma를 합산하지 않습니다.',
  [('성숙 유정 운영', '신규 유정 시추보다 이미 생산하는 저감소율 자산의 인수·정비·최적화에 집중합니다. 2025년 전신의 약 21 MBoe/d와 Q2 2026의 22.8 MBoe/d는 범위·기간이 다릅니다.'),
   ('원유', '유정 인도 지점의 지수 가격 계약으로 판매합니다. 2025년 전신 판매 1,288천 barrel이며 판매액과 hedge를 포함한 실현 가격을 구별합니다.'),
   ('가스·NGL', '제3자 midstream이 집하·처리·판매하고 관련 비용을 차감한 수입을 정산합니다. 2025년 전신 가스 25,845 MMcf, NGL 2,098천 barrel이며 gross 처리량과 회사 판매량은 다릅니다.'),
   ('현장 서비스', '압축·공사·복구·배출 관련 서비스가 전신 매출에 포함됩니다. 운영 최적화 사업을 외부 AI 소프트웨어 매출로 추정하지 않습니다.'),
   ('Canyon Creek', '7월 인수를 완료해 Arkoma에 진입했습니다. 약 83백만 USD, Class A 1,962,240주 실제 발행과 서명 당시 금액을 구별합니다. Q2 실적에는 아직 편입되지 않았습니다.'),
   ('AI 적용 단계', 'Q2 회사 발표는 자체 자산에 AI를 우선 적용하고 생산 증대 약 1%를 달성했다고 설명합니다. 연 3~5% 목표는 미래 목표이며 외부 고객 계약이나 앱의 AI 호출 증거가 아닙니다.'),
   ('자금·hedge', '6월 9일 350백만 USD ABS 차환을 완료했습니다. 이자·원금, 유정 수입과 상품 파생상품 실현·미실현 손익은 서로 다른 현금 및 회계 흐름입니다.')],
  customers='원유 구매자와 가스 처리·판매 경로입니다. Q2 구매자 집중도 31·12·11%는 익명 공시이며 특정 정유사나 가스 업체를 추정해 연결하지 않습니다.',
  inputs='기존 유정·압축·workover·집하·처리·운송·현장 인력·자산 취득 자금이 필요합니다. 낮은 신규 시추 투자와 유지 비용이 없다는 주장은 다릅니다.',
  competition='Mid-Continent 생산 자산 인수 가격, 감소율, 정비·최적화, 운영 비용과 금융 조건을 비교합니다. 인수 후보 금액이나 목표 배당을 확정 거래·현금으로 표시하지 않습니다.'),
 'HMH': profile('HMH Holding Inc.', ANNUAL['HMH'],
  '육상·해양 시추용 장비와 압력 제어 시스템, 교체 부품·정비·디지털 서비스를 제공합니다. 2021년 Baker Hughes의 subsea drilling과 Akastor의 MHWirth 사업 결합에서 출발해 2026년 4월 2일 IPO를 완료했습니다.',
  '2025년 HMH B.V. 전신 연결 매출은 821,754,000 USD입니다. 서비스 383,385,000·외부 제품 213,544,000·부품 224,380,000·관계사 제품 445,000이며 ESS 438,553,000와 PCS 383,201,000은 같은 매출의 별도 부문 보기입니다.',
  [('ESS 시추 패키지', '리그의 상부 시추 장비·완전한 패키지와 유지 서비스를 공급합니다. 신규 리그·재가동 프로젝트와 개별 장비 판매를 구별합니다.'),
   ('PCS 압력 제어', 'BOP, 제어 시스템·시추 riser를 공급하고 정비합니다. 유정 제어 장비를 판매하는 OEM이며 리그 자체의 생산 계약을 모두 운영하는 회사는 아닙니다.'),
   ('정비·디지털', '설치 장비의 안전·수명·운영을 지원하는 recurring aftermarket와 디지털 솔루션입니다. 서비스 매출과 수주 잔고·book-to-bill의 기준은 다릅니다.'),
   ('교체 부품', '기존 시추·압력 제어 장비용 부품입니다. 2025년 서비스 46.7%와 부품 27.3%는 반올림된 전체 매출 비율이며 별도 서비스와 함께 더해 새 총계를 만들지 않습니다.'),
   ('브랜드·기술', 'Hydril Pressure Control·Wirth·Maritime Hydraulics·VetcoGray 등의 기존 제품 계보를 활용합니다. 브랜드 역사와 현재 상장 법인의 설립·소유 구조를 구별합니다.'),
   ('상장 후 지분', '상장·재편 후 Baker Hughes와 Akastor가 각각 Class B 15,945,826주를 보유해 합산 약 72% 의결권입니다. B.V. 경제 지분과 Inc. 의결권의 분모가 다르므로 과거 50:50 JV를 현재 전체 구조로 표시하지 않습니다.'),
   ('riser 서비스 확대', '9월 21일 Deepwater Riser Services 취득을 완료했습니다. Houma의 검사·재인증·보수·보관 사업을 확대하며 거래 가격은 발표에서 공개하지 않았습니다.')],
  customers='시추 계약사, 원유·가스 및 광업 운영사, 조선소·장비 제조사입니다. 공시가 특정 계약 상대를 밝히지 않은 설명에서 임의 고객 이름을 만들지 않습니다.',
  inputs='설계·특수 소재·가공·압력 제어 기술·정비 인력·부품 물류가 필요합니다. 프로젝트 진행률과 부품·정비의 설치 기반 수요, 납기·재고·보증 비용이 영향을 줍니다.',
  competition='시추 패키지·압력 제어·riser·정비별 입찰, 안전·인증, 설치 기반과 전체 수명 비용을 비교합니다. 광업 인접 사업을 석유 시추 시장 전체 점유율로 환산하지 않습니다.'),
 'NUCL': profile('Eagle Nuclear Energy Corp.', ANNUAL['NUCL'],
  'Aurora 우라늄 자원 개발과 대학 특허 기반 소형 원자로 기술 사업화를 추진하는 초기 개발 회사입니다. 2026년 2월 24일 SPAC 결합과 Oregon Energy 인수를 완료했으며 가동 중인 우라늄 광산·상용 발전소로 표시하지 않습니다.',
  '2025년 11월 30일 종료 재무는 Eagle Energy Metals 전신입니다. 영업 매출 항목이 없고 순손실 5,260,632 USD를 보고했습니다. 사업화 계획으로 제품별 매출 0이나 매출 구성비를 만들어 표시하지 않습니다.',
  [('Aurora 자원', 'Oregon의 Aurora는 Indicated 32.75백만 lb와 Inferred 4.98백만 lb의 우라늄 광물 자원입니다. 회수 가능한 proved reserve나 당기 생산·판매량을 뜻하지 않습니다.'),
   ('광구·탐사', 'May 31 공시는 Oregon·Nevada의 미특허 lode·placer claims를 명시합니다. 토지 관리청의 광구 권리와 생산·환경·광산 허가를 구별합니다.'),
   ('Oregon Energy', '2월 24일 membership interest 100% 취득으로 Aurora 권리를 편입했습니다. 취득 전 전신 장부가와 취득 후 2026년 연결 자산을 구별합니다.'),
   ('Aurora Energy 권리', '매도 상대는 광구에 1.0% net smelter return 로열티를 남겼습니다. 상장사 지분 1%가 아니며 자원·타당성 단계에 따른 추가 지급 의무도 남아 있습니다.'),
   ('독점 특허 license', '2025년 6월 20일 UNM Rainforest Innovations와 소형 원자로 특허의 사용·사업화·재허여 계약을 체결했습니다. 대학 기술 license가 원자력 규제기관의 운전 승인은 아닙니다.'),
   ('VSLLIM·SLIMM', '액체금속 냉각 설계의 서로 다른 열출력 범위입니다. 원문의 MWth를 전기 출력 MWe로 바꾸거나 이미 상용 납품한 원자로로 표시하지 않습니다.'),
   ('개발·자금', '탐사·연구·허가·사업화 자금이 필요하며 2025년 감사는 계속기업 불확실성을 명시합니다. Cordex의 확장 가능성과 우라늄·원자로 수입은 향후 개발 결과에 달려 있습니다.')],
  customers='우라늄 및 원자로 기술의 향후 수요를 목표로 합니다. 확인한 공시는 현재 상용 우라늄 판매나 발전 구매 고객을 입증하지 않아 확정 고객 목록을 만들지 않습니다.',
  inputs='광구·기술 license·지질 조사·타당성·환경 및 원자력 인허가·전문 인력·자금이 필요합니다. resource 추정치와 회수·가공·연료 사업 단계는 다릅니다.',
  competition='우라늄 개발과 초기 원자로 설계 사업을 따로 비교합니다. 회사의 Aurora 광구와 다른 기업의 Aurora 명칭 원자로를 같은 프로젝트로 연결하지 않습니다.'),
 'UNTC': profile('Unit Corporation', ANNUAL['UNTC'],
  'Unit Petroleum을 통해 원유·천연가스·NGL을 생산하는 OTC 회사입니다. 2025년 10월 1일 Unit Drilling을 Cactus Drilling에 매각해 현재 사업은 upstream 중심이며 과거 BOSS 리그 자회사 보유와 구별합니다.',
  '2025년 지속 사업 매출은 102,283,000 USD입니다. 지속 사업 순이익 41,554,000과 중단 사업 순이익 56,738,000의 합계가 전체 순이익 98,292,000 USD이며, 매각 이익을 제품 판매액에 더하지 않습니다.',
  [('Unit Petroleum', '100% 자회사로 원유·가스 생산을 운영합니다. Oklahoma의 Cherokee Shale·Red Fork·Woodford 등의 생산·개발 참여와 순지분 기준을 구별합니다.'),
   ('2025 생산', '원유 811천 barrel, NGL 1,033천 barrel, 가스 12,484 MMcf와 총 3,925 Mboe입니다. barrel과 Mcf를 직접 더하지 않고 가스 환산 기준을 따릅니다.'),
   ('Cherokee 개발', '2026년 3월 자료의 prospective 약 18,000 net acres와 누적 44 gross·2.1 net 유정 참여는 기준이 다릅니다. 개발 가능 면적을 전체 생산 지분으로 해석하지 않습니다.'),
   ('시추 사업 처분', '2025년 10월 매각에는 BOSS·SCR 리그, yard와 관련 장비가 포함됩니다. 약 119.7백만 USD 거래 대금과 처분 후 보유한 일부 운전자본을 구별합니다.'),
   ('leasehold 매각', '6월 24일 Caddo·Blaine County의 일부 leasehold 매각을 완료해 약 17.2백만 USD 현금을 받았습니다. 처분 토지의 미래 개발을 현재 보유 생산으로 표시하지 않습니다.'),
   ('현금·부채', '2025년말 현금 181,713,000 USD, 공시 장기 차입금은 dash입니다. Q2 현금과 자산 처분, 배당·주식 재매입의 흐름을 따로 확인합니다.'),
   ('가격·hedge', '생산량과 파생상품 제외 판매가, hedge 포함 실현 가격을 나누어 비교합니다. 파생상품 평가·결제 손익과 원유·가스 매출 구성비를 섞지 않습니다.')],
  customers='원유·가스·NGL 판매 경로입니다. 확인한 공식 연차·분기 실적 자료는 세부 상품 판매액과 현재 구매자 실명을 나누지 않아 물량×평균가로 세부 매출을 추정하지 않습니다.',
  inputs='유정·생산 설비·workover·처리·운송·개발 투자·인력이 필요합니다. 시추 자회사 매각 후에도 생산 유지와 참여 유정 비용이 남습니다.',
  competition='Mid-Continent 광구·개발 경제성·생산 유지비와 현금 배분을 비교합니다. 과거 contract drilling의 리그 경쟁·매출은 현재 지속 사업 비교에서 분리합니다.'),
 'WHK': profile('WhiteHawk Minerals Corp.', ANNUAL['WHK'],
  'Marcellus·Haynesville 등의 천연가스 중심 광물권·로열티를 보유합니다. 2026년 6월 상장과 함께 WhiteHawk Income Corporation에서 이름을 바꾸고 관리회사를 내부화했습니다. 유정 운영사는 별도이며 일반적인 생산 비용 부담 사업과 다릅니다.',
  '재작성된 2025년 전체 수입 67,595,000 USD는 로열티 50,075,000·파생상품 순이익 16,648,000·lease bonus 872,000 USD입니다. 상품 gross 판매 58,701,000에서 집하·수송 등 8,626,000을 차감한 로열티와 전체 수입을 구별합니다.',
  [('가스·원유·NGL', '2025년 gross 가스 48,720,000·원유 5,359,000·NGL 4,622,000 USD입니다. 차감 비용은 별도 음수 항목이며 비용 차감 전 상품 비율을 연결 수입의 점유율로 표시하지 않습니다.'),
   ('운영사·정산', '광구의 제3자 운영사가 생산하고 구매자에게 판매한 수입 중 회사 권리 몫을 정산합니다. 2025년 EQT 33%·Range 11%·CNX 10%는 운영사 집중도이며 최종 구매자나 지분 비율은 아닙니다.'),
   ('PHX 편입', '2025년 6월 23일 PHX 취득을 완료했습니다. 해당 연간 실적에는 취득 이후 부분 실적만 포함되며 과거 PHX 전체 연간 매출을 다시 더하지 않습니다.'),
   ('토지 권리 취득', '2025년 Three Rivers의 잔여 50% undivided 광물권 취득은 특정 자산 거래입니다. 2026년 4월 3일 Haynesville 추가 자산 취득도 매도 회사 전체 100% 인수와 구별합니다.'),
   ('내부 관리·OpCo', 'IPO 때 관리회사 지분을 운영 partnership에 편입하고 기존 Investment Management Agreement를 종료했습니다. Class B·OpCo interests, earnout과 현재 연결 범위는 다른 권리입니다.'),
   ('9월 SJM II 거래', '9월 25일 Three Rivers Royalty II·Cypress의 Marcellus·Haynesville 자산 취득을 완료했습니다. 조정 후 대금 약 96.8백만 USD와 계약상 105백만을 구별하며 과거 pro forma와 실제 편입 기간을 섞지 않습니다.'),
   ('재작성·우선주', '2025년 관계사 management fee와 취득 전 정산 수입의 오류를 수정했습니다. 2025년말 자산 507,138,000·부채 270,722,000·자본 208,754,000 USD 외에 mezzanine 우선주 27,662,000 USD가 있어 자산−부채가 자본과 같지 않습니다.')],
  customers='제3자 운영사·광물권 임차인의 생산·정산과 상품 구매자의 결제에 의존합니다. 운영사를 최종 천연가스 구매자로 바꾸지 않습니다.',
  inputs='광물권 취득 자금·권리 관리·운영사 개발·집하·처리·수송이 중요합니다. 로열티의 비용 차감과 운영사 시추비, 우선주 배당·관리 비용은 범위가 다릅니다.',
  competition='분지별 광물권 품질·운영사 개발 일정·취득 가격·금융 조건을 비교합니다. gross DSU acres·net royalty acres·순 생산·자원 매장량의 기준을 혼합하지 않습니다.'),
}

LATEST = {
 'AMEN': 'Q2 2026 영업 매출 724,210 USD와 leasehold 처분 이익 966,448 USD는 별도입니다. 상반기 처분 수입·지분법 이익이 순이익에 미치는 영향과 미감사 표시를 함께 읽습니다.',
 'EROK': 'Q2 2026 공시는 IPO 완료, Hydrosource 분리와 8월 10일 Intrepid 자산 취득 완료를 명시합니다. 전신·취득 후 실제 연결·회사 normalized 실적은 서로 다른 비교입니다.',
 'FTW': 'Q2의 2026년 3월 이후 successor와 연초 predecessor를 구별합니다. 7월 Canyon Creek 인수는 완료됐지만 Q2 실적에는 포함되지 않습니다.',
 'HMH': '상장 후 Inc.와 전신 B.V.의 이익 귀속을 구별합니다. 9월 21일 DWR 취득은 완료됐으며 가격은 해당 발표의 공개 범위 밖입니다.',
 'NUCL': 'May 31 분기는 2월 SPAC 결합·Oregon Energy 100% 취득과 license를 반영합니다. 2025년 11월말 전신 자산과 취득 후 광구 자산·mezzanine 권리를 혼합하지 않습니다.',
 'UNTC': '6월 24일 leasehold 매각 완료, Q2 생산 941 Mboe와 현금 189,595,000 USD를 보고했습니다. 시추 사업은 이미 처분했으며 과거 중단 사업과 비교합니다.',
 'WHK': '10월 1일 S-1의 FY2025 재작성 수치를 사용합니다. 9월 SJM II 취득·Series E 조달과 제안된 Series F offering을 현재 매출이나 완료된 공모로 혼합하지 않습니다.',
}
UPDATES = {**QUARTER, 'FTW': FTW_RESULTS, 'HMH': HMH_DWR, 'WHK': ANNUAL['WHK']}
for _s, _p in PUBLIC.items():
    _p['brief'].append(fact('최근 변화·자료 범위', LATEST[_s], UPDATES[_s]))
    _p['sources'].extend([QUARTER[_s], UPDATES[_s]])
    _p['filings'] = [ANNUAL[_s], QUARTER[_s]]
    _p['revenue_mix'] = REPORTS[_s]['revenue_mix']
    _p['segments'] = _p['products'][:3]
    _p['drivers'] = [fact('운영·거래·기간', LATEST[_s], UPDATES[_s]),
                     fact('주요 비용·투입', _p['brief'][3]['detail'], ANNUAL[_s])]
    _p['financial_context'] = [fact('재무를 읽는 기준', _p['brief'][1]['detail'], ANNUAL[_s])]

# A profile constructor's annual citation must not leak onto a later event.
for _s, _indices, _origin in [('AMEN',[4],QUARTER['AMEN']),
        ('EROK',[2,3,4,5,6],QUARTER['EROK']),
        ('FTW',[4],FTW_CANYON),('FTW',[0,5,6],FTW_RESULTS),
        ('HMH',[6],HMH_DWR),('NUCL',[1,2,3,4],QUARTER['NUCL']),
        ('UNTC',[1,2,3],UNTC_PRESENTATION),('UNTC',[4],QUARTER['UNTC'])]:
    for _i in _indices:
        PUBLIC[_s]['products'][_i]['source'] = _origin
    PUBLIC[_s]['sources'].append(_origin)
for _s in ('EROK','FTW','NUCL'):
    PUBLIC[_s]['description_source'] = UPDATES[_s]
    PUBLIC[_s]['brief'][0]['source'] = UPDATES[_s]
for _s in ('EROK','FTW'):
    PUBLIC[_s]['brief'][2]['source'] = QUARTER[_s]

# Human-read reported tables. These are not synthetic XBRL facts or 10-Ks.
FINANCIALS = {
 'AMEN': ('FY2025 · 미감사 연결', [('매출',2348341),('순이익',1698375),('총자산',6176693),('유동부채',758073),('자본',5418620),('현금',2825331)]),
 'EROK': ('FY2025 · Lea & Eddy 전신', [('매출',72173000),('순손실',-73071000),('총자산',282010000),('members deficit',-41715000),('현금',9042000)]),
 'FTW': ('FY2025 · PIH 전신', [('매출',179056000),('순이익',55875000),('총자산',377917000),('members deficit',-31983000),('현금',4119000)]),
 'HMH': ('FY2025 · HMH B.V. 전신 연결', [('매출',821754000),('순이익 · 연결',46123000),('총자산',1357704000),('총부채',657252000),('자본',700452000),('현금',96585000)]),
 'NUCL': ('FY2025-11-30 · Eagle Energy 전신', [('순손실',-5260632),('총자산',2887962),('총부채',898605),('자본',1689357),('상환형 주식 · mezzanine',300000),('현금',1301928)]),
 'UNTC': ('FY2025 · 지속·중단 사업 구별', [('매출 · 지속 사업',102283000),('순이익 · 지속 사업',41554000),('순이익 · 중단 포함',98292000),('총자산',330742000),('자본',281074000),('현금',181713000)]),
 'WHK': ('FY2025 · 재작성 연결', [('전체 수입 · 파생상품 포함',67595000),('순손실 · 연결',-3585000),('총자산',507138000),('총부채',270722000),('자본',208754000),('우선주 · mezzanine',27662000),('현금',28989000)]),
}
for _s, (_period, _rows) in FINANCIALS.items():
    PUBLIC[_s]['financials'] = [dict(label=label,value=value,unit='USD',period=_period,source=ANNUAL[_s]) for label,value in _rows]

_PARTIES = [
 ('sff-production','SFF Production LLC','AMEN','subsidiary',ANNUAL['AMEN'],'2014년 이후 100% 연결 자회사입니다. 원유·가스 working interest와 순이익 권리를 관리합니다.'),
 ('sff-royalty','SFF Royalty LLC','AMEN','partner',ANNUAL['AMEN'],'3분의 1 지분법 투자입니다. 로열티 권리의 이익과 현금 분배를 받으며 전체 매출은 연결하지 않습니다.'),
 ('erok-opco','EagleRock Land Operating LLC','EROK','subsidiary',QUARTER['EROK'],'IPO 후 운영 법인입니다. 상장 LLC의 managing member 통제와 다른 OpCo 보유자의 경제 지분을 구별합니다.'),
 ('def-operating','DEF Operating LLC','EROK','partner',QUARTER['EROK'],'Double Eagle 측 물 인프라 운영 파트너입니다. 편입한 DE Flow 자산과 계약상 별도 운영 법인을 구별합니다.'),
 ('presidio-investment','Presidio Investment Holdings LLC','FTW','subsidiary',ANNUAL['FTW'],'PIH는 2025년 비교 전신 사업입니다. 2026년 사업 결합 후 구조와 전신의 별도 자산·매출 범위를 구별합니다.'),
 ('canyon-creek-assets','Canyon Creek · Presidio 취득 자산','FTW','transaction',FTW_CANYON,'7월 인수 완료한 Arkoma 자산입니다. Vortus 측 및 추가 매도자 자산 거래로, 이름만으로 특정 매도 법인 전체를 자회사로 표시하지 않습니다.'),
 ('hmh-bv','HMH Holding B.V.','HMH','subsidiary',ANNUAL['HMH'],'상장 Inc.가 관리하는 운영 법인입니다. B.V. 전신 연결 재무와 상장 후 비지배 경제 지분을 구별합니다.'),
 ('akastor','Akastor ASA','HMH','partner',ANNUAL['HMH'],'Norway 상장 투자 그룹이며 MHWirth 사업의 출자자입니다. IPO 후 Class B 의결권 및 B.V. 지분 관계와 과거 50:50를 구별합니다.'),
 ('deepwater-riser','Deepwater Riser Services LLC','HMH','subsidiary',HMH_DWR,'9월 21일 취득 완료한 Houma의 riser 검사·재인증·보수·보관 사업입니다. 가격은 해당 발표에서 공개하지 않았습니다.'),
 ('oregon-energy','Oregon Energy LLC','NUCL','subsidiary',QUARTER['NUCL'],'2월 24일 membership interest 100% 취득으로 Aurora 광구를 편입했습니다. 광구 권리는 가동·생산 허가와 다릅니다.'),
 ('aurora-energy-seller','Aurora Energy · Eagle 광구 매도자','NUCL','partner',QUARTER['NUCL'],'Oregon Energy 매도자이며 1.0% 광구 NSR 로열티를 보유합니다. 다른 Aurora 명칭 원자로 회사 또는 상장사 지분 1%와 구별합니다.'),
 ('unm-rainforest','UNM Rainforest Innovations','NUCL','partner',QUARTER['NUCL'],'University of New Mexico의 기술 이전 조직입니다. 2025년 독점 SMR 특허 license의 계약 상대이며 상용 원자로 운전 허가 기관은 아닙니다.'),
 ('unit-petroleum','Unit Petroleum Company','UNTC','subsidiary',QUARTER['UNTC'],'100% 자회사로 현재 원유·가스·NGL 생산을 담당합니다. 처분한 시추 법인과 구별합니다.'),
 ('cactus-drilling','Cactus Drilling Company LLC','UNTC','transaction',ANNUAL['UNTC'],'2025년 10월 1일 Unit Drilling 취득을 완료한 관계사 거래 상대입니다. Cactus Inc. ticker WHD와 동일 회사로 연결하지 않습니다.'),
 ('whk-opco','WhiteHawk Income Operating Partnership LP','WHK','subsidiary',QUARTER['WHK'],'상장 후 운영·관리회사 지분을 보유하는 OpCo입니다. 100% 법인 소유와 Class B에 대응하는 OpCo 경제 지분을 구별합니다.'),
 ('phx-minerals','PHX Minerals LLC','WHK','subsidiary',QUARTER['WHK'],'2025년 취득 이후 광물권 운영 자회사입니다. 과거 상장 PHX와 현 법인, 취득 전 매출 범위는 다릅니다.'),
 ('three-rivers-royalty-ii','Three Rivers Royalty II LLC','WHK','transaction',ANNUAL['WHK'],'SJM II의 2026년 9월 광물권 자산 매도자입니다. 2025년 Three Rivers Royalty의 잔여 50% 자산 거래와 다른 법인·기간입니다.'),
 ('cypress-minerals','Cypress Mineral Partners LLC','WHK','transaction',ANNUAL['WHK'],'SJM II의 Marcellus·Haynesville 자산 매도자입니다. 9월 25일 거래 완료는 회사 전체 지분 인수가 아닙니다.'),
]
PRIVATE, EDGES = {}, {s: [] for s in SYMBOLS}
for _key, _name, _s, _kind, _origin, _detail in _PARTIES:
    PRIVATE[_key] = profile(_name, _origin, _detail,
        '확인한 해당 사업 역할만 설명합니다. 상대 전체 매출·지분·시장 순위는 추정하지 않습니다.',
        [('확인한 사업 역할', _detail)], customers='원문에서 확인한 산업·운영·계약 관계입니다.')
    EDGES[_s].append(relation(_name, None, _kind, _detail, _origin, _key))
EDGES['EROK'].append(relation('Hydrosource Logistics', None, 'partner',
    'IPO 직전 분리된 별도 관계사이며 5월 15일 실제 재활용·로열티 계약 상대입니다. 현재 EROK 100% 자회사가 아닙니다.',QUARTER['EROK'],'hydrosource-logistics'))
EDGES['HMH'].append(relation('Baker Hughes','BKR','partner',
    '출자·주요 주주 관계입니다. IPO 후 Class B 의결권 및 B.V. 경제 지분과 제품 판매·공급 역할을 구별합니다.',ANNUAL['HMH']))
for _name, _ticker, _detail in [
 ('EQT','EQT','2025년 EQT Production 운영 자산의 수입 집중도 33%'),
 ('Range Resources','RRC','2025년 운영 자산의 수입 집중도 11%'),
 ('CNX Resources','CNX','2025년 CNX Gas 운영 자산의 수입 집중도 10%'),
 ('Expand Energy','EXE','PHX 취득으로 추가한 Haynesville 자산의 실명 운영사'),
 ('Comstock Resources','CRK','PHX 취득으로 추가한 Haynesville 자산의 실명 운영사'),
 ('Devon Energy','DVN','PHX 취득으로 추가한 SCOOP/STACK 자산의 실명 운영사')]:
    EDGES['WHK'].append(relation(_name,_ticker,'partner',_detail+'입니다. 광물권 운영·로열티 정산 관계이며 최종 상품 구매자나 회사 지분 비율이 아닙니다.',ANNUAL['WHK']))

COMMON_CONTEXT = {'hydrosource-logistics': {'sources':[QUARTER['EROK']],
    'products':[fact('EagleRock과 현재 역할','IPO 직전 분리 후 별도 관계사로 재생수 사업을 운영합니다. EagleRock의 물 관련 royalty 계약과 NGL 생산수 공급 경로는 서로 다른 역할입니다.',QUARTER['EROK'])]}}
