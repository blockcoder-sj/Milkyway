"""Fuel, regulated gas, compression, power and gathering reading notes."""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('CLNE','FGPR','NFG','NGS','SEI','SMC')
ANNUAL = {s:report(s) for s in SYMBOLS}
QUARTER = {s:report(s,'quarter') for s in SYMBOLS}
UPDATES = {
 'CLNE':source('Clean Energy · Q2 실제 연료 판매·매출','https://investors.cleanenergyfuels.com/news-events/press-releases/detail/472/clean-energy-reports-revenue-of-106-4-million-and-63-2-million-rng-gallons-sold-for-the-second-quarter-of-2026','2026-08-06'),
 'FGPR':source('Ferrellgas · FY2026 실제 결과','https://ferrellgas.gcs-web.com/news-releases/news-release-details/ferrellgas-partners-lp-reports-fourth-quarter-and-full-fiscal','2026-09-25'),
 'NFG':source('National Fuel · FY2026 Q3 생산·전망','https://investor.nationalfuelgas.com/news-and-events/press-releases/press-releases-details/2026/National-Fuel-Reports-Third-Quarter-Fiscal-2026-Earnings/default.aspx','2026-07-29'),
 'NGS':source('NGS · Flatrock 취득·Q2 임대 fleet','https://ir.ngsgi.com/node/15436','2026-08-10'),
 'SEI':source('Solaris · Omega 실제 취득 계약','https://www.sec.gov/Archives/edgar/data/1697500/000119312526385257/d441137d8k.htm','2026-09-08'),
 'SMC':source('Summit · Q2 집하·Double E 확장 상태','https://summitmidstreamcorporation.gcs-web.com/news-releases/news-release-details/summit-midstream-corporation-reports-second-quarter-2026','2026-08-10'),
}
GESA=source('Solaris · GESA 발전 서비스 취득','https://ir.solaris-energy.com/news/2026/07-06-2026-120016135','2026-07-06')
SEI_GUIDANCE=source('Solaris · 최신 전망과 비GAAP 구분','https://ir.solaris-energy.com/news/2026/09-08-2026-114509510','2026-09-08')

PUBLIC = {
 'CLNE':profile('Clean Energy Fuels',ANNUAL['CLNE'],
  '폐기물 메탄을 정제한 재생 천연가스(RNG)와 일반 천연가스를 조달하고 CNG·LNG 형태로 상용 운송 고객에게 공급합니다. RNG는 원료·생산 경로이고 CNG·LNG는 압축·액화 상태입니다.',
  '2025 매출 424,833,000 USD는 연료·크레딧·평가 조정 후 순매출 331,483,000·충전소 건설 33,984,000·운영/정비 56,732,000·기타 서비스 2,634,000입니다. 고객 연료 인센티브인 Amazon warrant 차감은 현금 연료 매출과 다릅니다.',
  [('RNG 조달·생산','낙농·가축 분뇨·매립지 등의 biogas를 정제해 가스망에 주입합니다. 자체·JV 생산과 제3자 구매를 구별합니다.'),
   ('CNG 충전','가스를 고압으로 압축해 대형 트럭·버스·폐기물 수거차에 충전합니다. 차량과 충전소의 장비·압력·저장 조건이 다릅니다.'),
   ('LNG 운송 연료','가스를 극저온 액화해 저장·수송·충전합니다. 선박·산업 대량 공급도 있으며 LNG 수출 프로젝트와 사업 범위가 다릅니다.'),
   ('RIN·LCFS','연방 재생 연료·주별 저탄소 연료 제도의 환경 크레딧입니다. RNG의 탄소강도·발생·거래 가격·자격을 구별하며 연료 톤수와 크레딧 매출을 더하지 않습니다.'),
   ('충전소 건설','고객 또는 자체 연료망의 설계·건설·장비 공급입니다. 건설 매출과 이후 연료 판매·O&M 수익은 다릅니다.'),
   ('운영·정비','타사 소유 충전소의 운영·정비와 연료 공급을 구별합니다. 서비스 처리 GGE를 회사가 직접 판매한 연료 GGE로 표시하지 않습니다.'),
   ('수량·JV','2025 RNG 차량용 판매 237.4백만 GGE와 판매·서비스 전체 468백만 GGE의 분모가 다릅니다. BP·TotalEnergies JV의 전체 매출을 연결 매출에 더하지 않습니다.')],
  customers='트럭·버스·수거차 및 물류·산업 고객입니다. Amazon·UPS·FedEx·Pepsi Frito-Lay 등 원문 실명 운송 이용자를 연결하며 계열 법인·직접 계약과 전체 그룹을 구별합니다.',
  inputs='biogas·일반 가스, 정제·압축·액화·저장 장비, 가스망·충전소·운송과 규제 인증이 필요합니다. 크레딧·파생상품·warrant 회계를 물리적 연료 공급과 구별합니다.',
  competition='디젤·배터리 전기·수소 등 운송 연료와 RNG/CNG/LNG 공급망을 가격·총 운행 비용·배출·충전 접근성으로 비교합니다. 자가 충전과 외부 충전 서비스를 구별합니다.'),
 'FGPR':profile('Ferrellgas Partners',ANNUAL['FGPR'],
  '미국 전역의 주거·농업·상업·산업 고객에 프로판을 유통하고 Blue Rhino 교환용 휴대 탱크를 제공합니다. 상장 partnership과 실제 운영 partnership·경영 general partner는 다른 법인입니다.',
  '2026년 7월 31일 종료 회계연도 매출 1,864,014,000 USD입니다. 소매 1,204,880,000·재판매상 도매 536,395,000·기타 가스 15,327,000·기타 제품/서비스 107,412,000을 합산하며 프로판 소계를 다시 더하지 않습니다.',
  [('주거 공급','고객 부지 탱크에 bulk delivery truck으로 배송합니다. 난방·온수·조리 수요와 겨울 기온·배송 밀도가 수익에 영향을 줍니다.'),
   ('상업·산업','지게차·제조·건조·사업장 난방용 프로판입니다. 고객 저장 장비와 공급·안전·기술 서비스를 연결합니다.'),
   ('농업','곡물 건조·난방·관개·잡초 관리 등에 사용합니다. 계절·강우·작물 수확과 연료 수요가 연결됩니다.'),
   ('Blue Rhino 교환 탱크','소매점에서 그릴용 휴대 탱크를 교환합니다. 브랜드·탱크·충전·배송 경로이며 소매점 전체 매출이 회사 매출은 아닙니다.'),
   ('재판매상 도매','독립 유통업체·소매상에 프로판을 판매합니다. 최종 소비자 소매 매출과 도매 출하를 중복 합산하지 않습니다.'),
   ('마진·저장','가스 구매와 배송 원가 대비 cents-per-gallon 마진을 봅니다. wholesale 상품 가격 상승이 이익 상승과 같지는 않습니다.'),
   ('holding·소유 구조','Ferrellgas LP·Finance Corp 두 직접 자회사와 Ferrellgas Inc 경영 역할을 구별합니다. 직원 ESOP의 GP 모회사 소유를 상장 partnership 100% 소유라고 설명하지 않습니다.')],
  customers='주거·상업·농업·도매·휴대 탱크 소매 경로입니다. 이름이 없는 공급·소매 계약에 특정 대형 유통사 이름이나 독점 점유율을 추정하지 않습니다.',
  inputs='정유·가스 처리에서 공급되는 프로판, 저장·탱크·delivery fleet·소매망·안전·인력이 필요합니다. 겨울 재고와 운전자본, 금융비용을 구별합니다.',
  competition='전국·지역 프로판 유통사·협동조합 및 전기·천연가스 등 대체 에너지가 경쟁합니다. 회사의 소매 판매량 기준 순위 주장을 전체 연료시장 점유율로 바꾸지 않습니다.'),
 'NFG':profile('National Fuel Gas',ANNUAL['NFG'],
  'Appalachia 천연가스의 생산·집하와 파이프라인·저장·규제 유틸리티를 연결하는 통합 가스 기업입니다. 탐색 사업 그룹과 공식 섹터 분류는 별개이며 가스 배급 유틸리티가 포함됩니다.',
  '2025년 9월 30일 종료 회계연도 연결 매출 2,277,541,000 USD는 생산/집하/기타 1,184,136,000·파이프라인/저장 276,131,000·유틸리티 817,274,000의 외부 매출입니다. 고객 계약 매출 2,219,117,000 구분과 전체 GAAP 매출은 범위가 다릅니다.',
  [('생산·집하','Seneca의 Pennsylvania Marcellus·Utica 가스 생산과 National Fuel Gas Midstream의 집하입니다. 동일 그룹 내 수송·집하를 외부 매출에 다시 더하지 않습니다.'),
   ('파이프라인·저장','Supply Corporation·Empire의 interstate 운송·저장입니다. 예약 용량의 월 고정료와 실제 수송량 기반 변동료를 구별합니다.'),
   ('가스 유틸리티','Distribution Corporation이 서부 New York·북서 Pennsylvania 약756,000고객에 가스를 공급합니다. 연료 비용 회수·규제 요금·고객 수·판매량은 다른 지표입니다.'),
   ('가격·헤지','생산 가스의 NYMEX·지역 basis·파생상품·수송 비용을 구별합니다. 생산 매출과 규제 배급의 구매 가스 pass-through를 같은 마진으로 비교하지 않습니다.'),
   ('용량·가스망','Appalachia 집하와 미국 북동부·Canada 연결망입니다. 파이프라인 접속 사업자와 물리적 가스 매도인·고객을 구별합니다.'),
   ('설비·안전','압축·배관·지하 저장·유틸리티 배급과 유정 개발에 설비투자가 필요합니다. 허가·수요·복구·시공과 실제 in-service 시점이 다릅니다.'),
   ('과거 사업·비교','California E&P는 2022년 처분한 과거 범위입니다. 결산연도·최근 분기·파생상품·규제 자산과 현재 운영 자산을 구별합니다.')],
  customers='가스 소비자·발전/산업 고객·shipper와 계열 생산사입니다. 계열사 물량과 제3자 외부 운송·판매를 구별합니다.',
  inputs='광물권·시추/완결·배관·압축기·저장층·노동·허가가 필요합니다. 유틸리티 구매 가스와 생산 자산의 채굴·감모·자본 원가는 다른 투입입니다.',
  competition='생산은 가스 원가·basis·광구 개발, 운송은 노선·용량·신뢰성, 배급은 규제·지역·대체 연료로 비교합니다. 유틸리티를 전부 spot 상품 판매로 설명하지 않습니다.'),
 'NGS':profile('Natural Gas Services Group',ANNUAL['NGS'],
  '천연가스·원유 생산과 처리에 필요한 압축기를 설계·조립·임대·유지보수합니다. 전기 모터·가스 엔진의 구동과 압축기 프레임·제어 OEM은 서로 다른 구성 요소입니다.',
  '2025 매출 172,315,000 USD는 압축기 임대 164,326,000·판매 3,992,000·사후 서비스 3,997,000입니다. 판매를 부품 2,120,000·압축기/재제작 1,872,000으로 나눈 표에서 판매 소계를 다시 더하지 않습니다.',
  [('계약 임대','중·대마력 압축기를 생산사 현장에 배치합니다. 가동·임대 마력·요금·계약 기간·정비 비용이 수익을 결정합니다.'),
   ('gas lift','고압 가스로 원유 유정의 인공 채유를 돕습니다. 압축 서비스 제공과 생산사가 소유한 원유 판매는 다른 사업입니다.'),
   ('가스 생산·처리','유정·집하·처리 설비의 압력을 맞춥니다. small/medium/large horsepower 용도와 장비별 압축단·성능을 구별합니다.'),
   ('전기 모터 구동','electric motor drive fleet를 확대합니다. 전기 장비의 설치·수전·가동과 가스 엔진 fleet의 마력을 구별합니다.'),
   ('설계·조립·판매','OEM 엔진·압축기·제어를 통합합니다. Caterpillar·Cummins·Waukesha·Ariel·FW Murphy는 원문 실명 부품 공급 역할입니다.'),
   ('사후 서비스','고객 소유 장비 call-out 서비스·신규 장비 시운전·부품·rebuild입니다. 임대한 자체 장비의 운영 정비와 구별합니다.'),
   ('fleet·지역 기준','2025년말 사용 마력562,676·보유/가용 마력662,542·마력 가동률84.9%입니다. Permian 78%는 임대 매출 기준이고 업계 시장점유율이 아닙니다.')],
  customers='OXY의 Occidental Permian LTD와 Devon이 2025 매출 합산59%의 실명 고객입니다. 회사별 비중을 임의로 나누거나 매출 집중도와 수취채권 비중을 섞지 않습니다.',
  inputs='OEM 엔진·전기 모터·압축기 프레임·제어·부품·steel·기술 인력·정비가 필요합니다. 대마력 장비 조달·설치 지연과 고객 현장 준비를 구별합니다.',
  competition='계약 압축 공급사와 고객 자체 fleet를 장비 성능·신뢰성·지역·요금·정비로 비교합니다. 보유 마력과 임대 중 마력·연료 종류를 같은 분모로 비교하지 않습니다.'),
 'SEI':profile('Solaris Energy Infrastructure',ANNUAL['SEI'],
  '발전·배전·제어·설치·시운전·운영/정비를 제공하며 유전 완결 원료 물류도 운영합니다. 과거 Solaris Oilfield Infrastructure 이름의 물류 중심 회사에서 현재 데이터센터·산업 전력 인프라로 사업 범위가 확대됐습니다.',
  '2025 손익계산서 매출 622,205,000 USD는 서비스 349,848,000·임대 272,357,000입니다. 부문 주석의 발전333.5백만·물류288.7백만은 반올림·분류가 다른 표이며 정확한 전체 구성비로 만들지 않습니다.',
  [('Power Solutions','발전 장비 임대·제어·배전·서비스를 제공합니다. 고객에게 공급할 계약 MW와 설치·시운전·실제 매출을 버는 MW를 구별합니다.'),
   ('Logistics Solutions','파쇄 원료 저장·이송 장비·현장 기술·software·last-mile 물류입니다. 원료 관리 서비스가 직접 원유 생산이나 모래 광산 판매는 아닙니다.'),
   ('장기 데이터센터 전력','장기 고객 계약은 설비 인도·시운전·고객 수락에 따라 시작됩니다. 미래 계약량·예상 run-rate EBITDA와 현재 GAAP 매출은 다릅니다.'),
   ('Stateline JV','Solaris50.1%·고객 측49.9% 공동사업입니다. 약900MW 계획과 과거 2025 매출, JV 지분·전체 fleet 능력의 분모를 구별합니다.'),
   ('배전·시운전','HVMVLV 취득 사업과 전력 배전·제어·현장 설치 역량입니다. 발전 turbine OEM·배전 장비·EPC·운영 서비스는 다른 역할입니다.'),
   ('공급·고객 실명 경계','2025 Power 매출의88%인 단일 고객과 주요 발전 장비 공급사는 원문에서 익명입니다. 알려진 업계 브랜드·AI 회사를 추정해 고객·공급사로 등록하지 않습니다.'),
   ('원료 물류·발전 비교','장비 lease와 service 회계·감가·가동·last-mile 비용을 구별합니다. 부문 주석과 손익계산서 분류 차이를 임의 조정 행으로 채우지 않습니다.')],
  customers='데이터센터·에너지·산업·상업 고객입니다. Stateline의 CTC 지분이 MZX Tech로 이전된 법인 기록과 익명 AI 고객의 그룹명을 구별합니다.',
  inputs='분산 발전기·turbine·엔진·배전·제어·연료·공사·인력·정비·자금이 필요합니다. 익명 OEM의 실명·직접 계약·납품 완료를 추정하지 않습니다.',
  competition='전력 인프라의 납기·가동·신뢰성·turnkey 설치·정비와 유전 물류의 효율·안전을 비교합니다. 발전 용량·계약 용량·발전량·물류 장비 수는 다른 지표입니다.'),
 'SMC':profile('Summit Midstream',ANNUAL['SMC'],
  '생산지의 천연가스·원유·생산수를 집하·압축·처리·수송하고 일부 가스·NGL·콘덴세이트를 판매합니다. 2024년 MLP에서 corporation으로 전환한 현재 SMC와 과거 SMLP 공시 범위를 구별합니다.',
  '2025 연결 매출 562,091,000 USD는 집하/처리255,677,000·가스/NGL/콘덴세이트265,059,000·기타41,355,000입니다. Double E 70% 지분의 JV 전체 매출은 연결 매출에 합산하지 않습니다.',
  [('Rockies','DJ·Williston의 가스·원유·생산수 집하입니다. 생산자의 원유 가격·시추 활동과 회사의 수수료 매출이 연결되지만 동일한 매출은 아닙니다.'),
   ('Mid-Con·Barnett','Arkoma·Barnett 등의 가스 집하·처리입니다. Tall Oak 취득 시스템의 통합·압축·고객 계약을 원래 사업과 구별합니다.'),
   ('Piceance','Colorado의 가스 집하·처리와 판매입니다. 처리 중 취득하는 상품 가격 노출과 고정 수수료를 구별합니다.'),
   ('Double E · Permian','70% 지분·운영의 가스 수송 JV이며 ExxonMobil 계열이30%입니다. 1.6Bcf/d 설계 능력·100% 처리량·회사 지분 EBITDA·연결 매출의 분모가 다릅니다.'),
   ('장기 집하 계약','지역 AMI·minimum volume commitments·수수료와 계약기간입니다. 미달 수수료·최소 약정량·실제 처리 물량을 구별합니다.'),
   ('상품·용수','일부 percentage-of-proceeds 계약에서 가스/NGL을 취득해 판매합니다. 원유·생산수 집하 수수료와 직접 상품 판매 마진을 구별합니다.'),
   ('처분·현재 망','2024년 Summit Utica·Ohio Gathering을 MPLX 측에 처분했습니다. 과거 Northeast 사업을 현재 보유 망으로 표시하지 않습니다.')],
  customers='광구·유정의 원유/가스 생산사와 가스 처리·수송 고객입니다. Double E 접속 처리시설과 firm capacity 계약 상대, 공개되지 않은 생산자 이름을 구별합니다.',
  inputs='집하 배관·압축·탈수·처리·수송·정비·생산수 처리 경로와 허가가 필요합니다. JV 처리량·자본과 연결 자산의 비용을 구별합니다.',
  competition='생산지 접속·고객 전용 지역·수수료·신뢰성·처리/출구 용량으로 비교합니다. 상품 트레이더·상류 생산자·집하 서비스를 같은 사업으로 표시하지 않습니다.'),
}
LATEST={
 'CLNE':'8월 6일 Q2 발표의 RNG 판매63.2백만 GGE·매출106.4백만 USD는 해당 분기입니다. 연간 판매·O&M 처리·warrant 차감/비GAAP 조정과 구별합니다.',
 'FGPR':'9월 25일 FY2026 실제 결과와 Class B→Class A 전환 완료를 발표했습니다. 연간 조정EBITDA·전체순이익·Class A 단위당 손익은 다른 지표입니다.',
 'NFG':'7월 29일 FY2026 Q3 발표의 Seneca 가스 생산104.3Bcf는 실제 분기이고 연간420–430Bcf는 전망입니다. appraisal·유정 간 상호작용과 장기 생산 목표를 구별합니다.',
 'NGS':'6월 12일 Flatrock Compression Holdings 취득을 완료했습니다. Q2 말 보유758,526HP·임대669,919HP이며 인수 전2025 fleet와 비교 범위가 다릅니다. Q2 취득 사업의 부분 월 실적을 완전한 분기 실적으로 표시하지 않습니다.',
 'SEI':'9월 1일 Omega Foundation Services 사업을 취득했습니다. 7월 GESA 인수와 함께 EPC·설치·정비 역량이 확대됐으며 2025 연차에는 소급 포함되지 않습니다. 9월 8일 EBITDA 전망은 비GAAP 미래 추정입니다.',
 'SMC':'8월 10일 발표의 Double E 평균859MMcf/d는100% JV 처리량이며 SMC 지분 처리량이 아닙니다. 확장 open season·향후 FID 전망과 기존 가동을 구별하며 예정일만으로 확장 완료를 표시하지 않습니다.',
}
for _symbol,_value in PUBLIC.items():
 _value['brief'].append(fact('최근 가동·연결 범위',LATEST[_symbol],UPDATES[_symbol]))
 _value['sources'].extend([QUARTER[_symbol],UPDATES[_symbol]])
 _value['filings']=[ANNUAL[_symbol],QUARTER[_symbol]]
 _value['revenue_mix']=REPORTS[_symbol]['revenue_mix']
 _value['segments']=_value['products'][:3]
 _value['drivers']=[fact('계약·가동·가격',LATEST[_symbol],UPDATES[_symbol]),fact('투입·수행',_value['brief'][3]['detail'],ANNUAL[_symbol])]
 _value['financial_context']=[fact('기간·계량·회계 범위','표에 표시한 원문 회계기간·USD입니다. GGE·HP·MW·Bcf/d·판매량·service 처리량·미래 약정량은 서로 다른 계량입니다. 상품·lease·service·크레딧·JV 매출을 중복 합산하지 않습니다.',ANNUAL[_symbol])]
PUBLIC['SEI']['sources'].extend([GESA,SEI_GUIDANCE])
PUBLIC['SEI']['products'].extend([fact('GESA · 현재 발전 서비스','7월 취득한 Global Energy Services Alliance는 Baseload Power·Pro-Per의 발전 설치·시운전·수명 전반 O&M 역량을 결합합니다.',GESA),fact('Omega · 현재 EPC','9월 1일 취득한 Omega 사업은 데이터센터·LNG·산업 현장의 heavy civil EPC입니다. 현재 취득과 미래 시너지·이익 전망을 구별합니다.',UPDATES['SEI'])])
PUBLIC['CLNE']['market_shares']=[fact('회사 추정 · 차량용 RNG 판매','회사 연차는2025 California50%·미국32%라고 추정합니다. 차량용 RNG 시장의 회사 주장이고 일반 천연가스·전체 운송연료 점유율이나 독립 조사 확인 값이 아닙니다.',ANNUAL['CLNE'])]

_PARTIES=[
 ('maas-energy','Maas Energy Works LLC','CLNE','partner',ANNUAL['CLNE'],'낙농 RNG 공동 개발의 실명 상대입니다. 투자·건설·운영을 맡으며 특정 수익률 후 CLNE49%·Maas51% 이익 배분을 단순 회사 지분율로 바꾸지 않습니다.'),
 ('ferrellgas-operating','Ferrellgas LP','FGPR','subsidiary',ANNUAL['FGPR'],'프로판 유통을 수행하는 운영 partnership입니다. 선순위 Preferred 단위와 상장 holding·GP의 경제/경영 역할을 구별합니다.'),
 ('ferrellgas-finance','Ferrellgas Partners Finance Corp','FGPR','subsidiary',ANNUAL['FGPR'],'상장 partnership의 금융 자회사입니다. 직접 프로판 배송·소매 매출 회사로 표시하지 않습니다.'),
 ('ferrellgas-gp','Ferrellgas Inc.','FGPR','partner',ANNUAL['FGPR'],'상장·운영 partnership의 sole general partner로 경영을 수행합니다. ESOP 모회사 소유와 상장사100% 경제 지분은 다릅니다.'),
 ('seneca-resources','Seneca Resources Company LLC','NFG','subsidiary',ANNUAL['NFG'],'Pennsylvania Appalachian 천연가스 생산 계열사입니다. 가스 생산·시추·광물권과 그룹 내 집하/규제 배급 역할을 구별합니다.'),
 ('nfg-midstream','National Fuel Gas Midstream Company LLC','NFG','subsidiary',ANNUAL['NFG'],'Appalachia 가스 집하·압축·처리 계열사입니다. 주로 Seneca 생산을 수송하며 그룹 내 수수료와 외부 연결 매출을 구별합니다.'),
 ('nfg-supply','National Fuel Gas Supply Corporation','NFG','subsidiary',ANNUAL['NFG'],'interstate 가스 파이프라인·지하 저장 계열사입니다. 규제 용량 예약료와 실제 가스 상품 판매를 구별합니다.'),
 ('empire-pipeline','Empire Pipeline Inc.','NFG','subsidiary',ANNUAL['NFG'],'New York·Pennsylvania 가스 수송·저장 계열사입니다. 접속망·용량 고객과 원료 가스 매도인을 구별합니다.'),
 ('nfg-distribution','National Fuel Gas Distribution Corporation','NFG','subsidiary',ANNUAL['NFG'],'서부 New York·북서 Pennsylvania의 규제 가스 배급 계열사입니다. 생산·도매 수송과 최종 소비자 요금 사업은 다릅니다.'),
 ('ngs-waukesha','Waukesha · 가스 엔진','NGS','supplier',ANNUAL['NGS'],'압축 패키지의 가스 엔진 OEM 브랜드입니다. NGS 원문이 이름을 명시하며 전체 엔진 시장·직접 구매 계약액·독점 관계를 추정하지 않습니다.'),
 ('ngs-fw-murphy','FW Murphy · 제어','NGS','supplier',ANNUAL['NGS'],'압축기 패키지의 제어 OEM 역할입니다. 엔진·압축기 프레임 공급과 구별하며 확인되지 않은 법인 지분을 추정하지 않습니다.'),
 ('flatrock-compression','Flatrock Compression Holdings LLC','NGS','subsidiary',UPDATES['NGS'],'2026년 6월 12일 취득한 계약 압축 사업입니다. 취득 전 fleet·취득 후 임대 마력·부분 월 실적과 완전한 연간 실적을 구별합니다.'),
 ('stateline-power','Stateline Power LLC','SEI','partner',ANNUAL['SEI'],'Solaris50.1%·고객측49.9% 데이터센터 전력 JV입니다. 예정900MW와 실제 당기 매출·전체 fleet를 구별합니다.'),
 ('mzx-tech','MZX Tech LLC','SEI','partner',ANNUAL['SEI'],'CTC Property로부터 Stateline 지분을 넘겨받은 고객 측 계열 LLC입니다. 원문 미공개 AI 그룹의 이름을 추정하지 않습니다.'),
 ('gesa-power','Global Energy Services Alliance Inc.','SEI','subsidiary',GESA,'2026년 7월 취득한 발전 서비스 사업입니다. Baseload·Pro-Per의 설치·시운전·운영·수명 전반 정비 역량을 결합합니다.'),
 ('omega-foundation','Omega Foundation Services LLC','SEI','subsidiary',UPDATES['SEI'],'2026년 9월 1일 취득한 사업의 heavy civil EPC 운영 회사입니다. 공사·데이터센터/LNG 현장 지원과 발전 장비 OEM 역할은 다릅니다.'),
 ('double-e-pipeline','Double E Pipeline LLC','SMC','partner',ANNUAL['SMC'],'Summit70%·ExxonMobil 계열30%의 비연결 가스 수송 JV입니다. Summit가 운영하며 전체 매출·100% 처리량을 연결 매출에 더하지 않습니다.'),
 ('tall-oak-parent','Tall Oak Midstream Holdings LLC','SMC','transaction',ANNUAL['SMC'],'2024년 Tall Oak 지분 출자·인수 계약의 실명 상대입니다. 취득 운영 자산과 상장사의 주식·Class B/partnership unit 경제 권리를 구별합니다.'),
]
PRIVATE,EDGES={}, {s:[] for s in SYMBOLS}
for _key,_name,_symbol,_kind,_origin,_detail in _PARTIES:
 PRIVATE[_key]=profile(_name,_origin,_detail,'여기서는 확인한 특정 사업 역할을 설명하며 상대 전체 매출·비중·지분을 추정하지 않습니다.',[('확인한 역할',_detail)],customers='근거가 공개된 해당 연료·가스·서비스·전력 가치사슬에 연결합니다.')
 EDGES[_symbol].append(relation(_name,None,_kind,_detail,_origin,_key))
EDGES['CLNE'] += [relation('BP','BP','partner','BP Products North America와50:50 낙농 RNG JV.2025말5가동/1건설·예상수량과 실제 연결 매출을 구별.',ANNUAL['CLNE']),relation('TotalEnergies','TTE','partner','50:50 RNG 프로젝트 JV와 TMS의 상장사 지분 역할을 구별. 프로젝트 현금·전체매출을 합산하지 않음.',ANNUAL['CLNE']),relation('Amazon','AMZN','customer','실명 운송 연료 이용·구매와 Amazon.com NV Investment Holdings warrant 회계를 구별.',ANNUAL['CLNE'])]
EDGES['NGS'] += [relation('Caterpillar','CAT','supplier','압축기 패키지 엔진 OEM. 직접 계약금액·독점 관계를 추정하지 않음.',ANNUAL['NGS']),relation('Cummins','CMI','supplier','압축기 패키지 엔진 OEM. 패키징·프레임·제어 공급과 다른 역할.',ANNUAL['NGS']),relation('Ariel',None,'supplier','압축기 프레임 OEM. 기존 Estis 공급 역할과 별도 NGS 패키지 범위.',ANNUAL['NGS'],'ariel-compressors'),relation('Occidental Petroleum','OXY','customer','직접 계약 법인은 Occidental Permian LTD. Devon과2025 합산59% 매출 집중도이며 OXY 단독 비중을 추정하지 않음.',ANNUAL['NGS']),relation('Devon Energy','DVN','customer','OXY와2025 합산59%의 실명 고객. 회사별 비중·수취채권 비중을 추정하지 않음.',ANNUAL['NGS'])]
EDGES['SMC'] += [relation('ExxonMobil','XOM','partner','Double E30% 지분 계열 파트너. 회사 전체 그룹 지분·전체JV 매출과 구별.',ANNUAL['SMC']),relation('MPLX','MPLX','transaction','2024년 Summit Utica·Ohio Gathering 처분 완료의 상대 계열. 현재 Summit 보유 Northeast 자산으로 표시하지 않음.',ANNUAL['SMC'])]
COMMON_CONTEXT={'ariel-compressors':{'brief':[fact('NGS 압축기 프레임 OEM','NGS 연차가 Ariel을 압축 패키지 프레임 OEM으로 명시합니다. 기존 Estis 장비 사양과 별도 공급 역할이며 직접 구매금액·시장점유율은 미확인입니다.',ANNUAL['NGS'])]}}
