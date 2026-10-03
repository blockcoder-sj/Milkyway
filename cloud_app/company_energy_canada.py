"""Edited Canadian energy business maps from free audited/project originals.

The annual accounting scope, current asset scope and development stage are
separate. Counterparty names require actual evidence; anonymous buyers are not
identified by inference. No network requests or model calls happen here.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('SU', 'CNQ', 'IMO', 'CVE', 'OBE', 'BTE', 'VET', 'PDS')
AIF = {s: report(s, 'aif' if 'aif' in REPORTS[s] else 'annual') for s in SYMBOLS}
FIN = {s: report(s, 'financials' if 'financials' in REPORTS[s] else 'annual') for s in SYMBOLS}

SU_EQUIPMENT = source('Suncor · 2025 Q1 실적 설명 · 광산 장비 공급·공동 개발',
    'https://www.suncor.com/-/media/project/suncor/files/investor-centre/transcripts/2025-q1-suncor-energy-financial-results-call-transcript-en.pdf?created=20250508213000&modified=20250508213006', '2025-05-07')
SU_SECOND_SHOVEL = source('SMS Equipment·Komatsu · Fort Hills 두 번째 PC9000 실제 인도',
    'https://www.pc9000.com/en/news/news/expanding-the-fleet-second-komatsu-pc9000-excavator-arrives-at-suncor-s-fort-hills-mine/', '2025-11-12')
SU_Q2 = source('Suncor · 2026 Q2 결과 · 정유 능력 산정 변경',
    'https://www.suncor.com/-/media/project/suncor/files/news-releases/2026/2026-08-04-news-release-earnings-q2-2026-en.pdf', '2026-08-04')
CNQ_SWAP = source('Canadian Natural · AOSP 교환 거래 완료',
    'https://www.sec.gov/Archives/edgar/data/1017413/000101741325000053/a11032025closingofaospswap.htm', '2025-11-03')
IMO_Q2 = source('Imperial Oil · 2026 Q2 결과·운영 범위',
    'https://news.imperialoil.ca/news-releases/news-releases/2026/Imperial-announces-second-quarter-2026-financial-and-operating-results/default.aspx', '2026-07-31')
CVE_MEG = source('Cenovus · MEG 인수 완료',
    'https://www.cenovus.com/News-and-Stories/News-releases/2025/3187577', '2025-11-13')
CVE_Q2 = source('Cenovus · 2026 Q2 사업·개발 상태',
    'https://cenovus.com/News-and-Stories/News-releases/2026/3335023', '2026-07-29')
OBE_BELLY = source('Obsidian · Belly River 자산 인수 완료',
    'https://obsidianenergy.com/press-releases/obsidian-energy-closes-belly-river-acquisition-and-increases-2026-production-guidance/', '2026-07-02')
OBE_SEPTEMBER = source('Obsidian · 2026년 9월 실제 운영·생산 지침 변경',
    'https://www.sec.gov/Archives/edgar/data/1334388/000119312526390284/obe-ex99_1.htm', '2026-09-14')
ALBERTA_UNITS = source('Alberta 정부 · 유전 공동사업 운영사 목록 · 65643 PCU #11',
    'https://www.alberta.ca/system/files/custom_downloaded_images/energy-unit-listing.pdf#page=33', '2026-09-17')
OBE_ISN = source('ISN · Obsidian의 ISNetworld 실제 사용·확대 발표',
    'https://www.globenewswire.com/news-release/2026/04/14/3273598/0/en/Obsidian-Energy-Continues-to-Mitigate-Operational-Risk-with-ISN.html', '2026-04-14')
BTE_SALE = source('Baytex · 미국 Eagle Ford 매각 완료',
    'https://www.sec.gov/Archives/edgar/data/1279495/000106299325017428/exhibit99-1.htm', '2025-12-19')
BTE_BUYER = source('Baytex · Eagle Ford 매각 계약·법적 매수인',
    'https://www.sec.gov/Archives/edgar/data/1279495/000127949525000045/baytex-securitiespurchasea.htm', '2025-11-12')
BTE_Q2 = source('Baytex · 2026 Q2 생산·계속사업 원문',
    'https://www.baytexenergy.com/wp-content/uploads/news/1785445440-307301.pdf', '2026-07-30')
VET_Q2 = source('Vermilion · 2026 Q2 보고·7월 Wisselshorst 생산 개시',
    'https://www.vermilionenergy.com/wp-content/uploads/2026/07/VEI-Q2-2026-Report.pdf', '2026-07-29')
CORRIB_PARTNERS = source('Nephin · Corrib 공동사업 지분·자산 범위',
    'https://www.nephinenergy.com/projects-1', '열람 2026-10-03')
CORRIB_HYDROGEN = source('Nephin·Corrib JV·Gas Networks Ireland · 수소 시험사업 협약',
    'https://www.nephinenergy.com/news/2026/2/26/gni-and-corrib-jv-sign-strategic-collaboration-agreement-to-progress-green-hydrogen-pilot-project-at-bellanaboy', '2026-02-25')
PDS_Q2 = source('Precision Drilling · 2026 Q2 장비 운영·계약 현황',
    'https://www.precisiondrilling.com/press-release/precision-drilling-announces-2026-second-quarter-unaudited-financial-statements/', '2026-07-28')
PDS_PASON = source('Precision Drilling · AlphaApps Pason DAS 제품 사례',
    'https://www.precisiondrilling.com/resources/video/alphaapps-pason-das/', '2022-07-21')
KEYSTONE = source('South Bow · Keystone 원유 운송망·운영사',
    'https://www.southbow.com/keystone-pipeline-system/', '열람 2026-10-03')

PUBLIC = {
    'SU': profile('Suncor Energy', AIF['SU'],
        '오일샌드 채굴·증기 주입 생산과 개질, 해상 원유 생산, 정유·Petro-Canada 연료 판매를 연결하는 통합 에너지 기업입니다. 비투멘을 희석해 판매하거나 합성원유로 개질하고 정유 공장에 투입합니다.',
        '2025년 로열티 차감 전 고객 계약 매출은 52,377,000,000 CAD입니다. 오일샌드·탐사생산·정유판매 부문과 제품 표에는 내부 거래가 포함됩니다. 공장으로 이전한 원유와 외부 연료 판매를 같은 외부 매출처럼 합산하지 않습니다.',
        [('오일샌드 · 채굴과 개질', 'Base Plant·Fort Hills 광산과 Syncrude를 운영합니다. Base Plant와 Fort Hills는 100% 보유이며 Syncrude는 58.74% 지분·Suncor 운영입니다.'),
         ('Firebag·MacKay River · 열회수', '지하 비투멘을 증기 주입으로 회수합니다. 천연가스·물·증기 설비, 희석제와 수송 용량이 생산·출하를 연결합니다.'),
         ('합성원유·비투멘·원유·NGL', '광산·개질 사업의 합성원유·디젤과 희석 비투멘, 탐사·생산 사업의 원유·NGL을 판매합니다. 실제 표 제목으로 제품을 구분합니다.'),
         ('정유·Petro-Canada', '캐나다 Montréal·Sarnia·Edmonton 및 미국 정유와 연료 판매망입니다. 휘발유·경유·항공유 등 중간유분과 기타 제품을 판매합니다.'),
         ('자가 발전·전력 판매', '광산·열회수 시설의 열병합 발전 총 능력은 약 2,228 MW입니다. 공정용 증기·전력을 공급하고 남는 전력을 Alberta 전력망에 판매합니다.')],
        customers='정유·도매·산업 연료 고객과 Petro-Canada 소매망에 판매합니다. Canadian Tire의 주유소 재브랜딩·연료 유통 협력도 있습니다. Syncrude 각 지분 보유자는 자기 몫의 생산물을 직접 판매합니다.',
        inputs='광산 굴착기·운반 트럭·자율운반 소프트웨어, 증기용 천연가스·물, 희석제·수소·촉매, 정유 원료와 운송·터미널·정비를 사용합니다.',
        competition='오일샌드 생산·개질은 Canadian Natural·Imperial·Cenovus, 정유·연료 판매는 캐나다와 미국의 지역 정유·유통 사업과 경쟁 범위가 겹칩니다.'),
    'CNQ': profile('Canadian Natural Resources', AIF['CNQ'],
        '캐나다 원유·가스·오일샌드, 북해 및 아프리카 해상 생산과 중류·정유를 운영합니다. 광산 합성원유, 열회수 비투멘, 일반 중질유·경질유·NGL·천연가스의 자산·공정이 서로 다릅니다.',
        '2025년 로열티 차감 후 연결 매출은 38,762,000,000 CAD입니다. 북미 탐사생산 18,952,000,000 CAD와 오일샌드 채굴·개질 17,449,000,000 CAD가 큰 보고 부문이며 기타 세 부문·연결 조정도 포함됩니다.',
        [('Horizon·Albian · 광산·개질', 'Horizon은 100% 보유입니다. 2025년 11월 교환 후 Albian 광산 100%와 Scotford Upgrader·Quest 80%를 구분합니다. Scotford·Quest 운영자는 Shell입니다.'),
         ('열회수·중질유', 'SAGD 증기 회수, 일차 중질유 생산과 Pelican Lake의 폴리머 주입을 운영합니다. 회수 방식에 따라 가스·증기·희석제·설비 투입이 다릅니다.'),
         ('캐나다 원유·가스', 'Montney·Duvernay·Spirit River 등 북미 자산에서 경질유·NGL·가스를 생산합니다. 원유와 가스의 판매 가격·운송 경로가 다릅니다.'),
         ('국제 해상 생산', '영국 북해와 Côte d’Ivoire 등 해상 자산입니다. 캐나다 자산의 물량·회수 공법을 국제 해상 사업에 적용하지 않습니다.'),
         ('North West Redwater · 정유', 'NWRP의 50% 지분을 보유하며 자기 비투멘은 처리 계약의 25%에 해당합니다. 50% 소유 지분과 25% 가공 대가 부담·제품 물량을 구분합니다.')],
        customers='원유·가스·정유제품 구매자에게 판매하며 파이프라인·저장·시장 접근 계약을 확보합니다. NWRP는 비투멘을 경유 등으로 전환하는 별도 처리·판매 구조입니다.',
        inputs='광산 장비·개질·증기·폴리머·희석제와 시추·가스처리, 전력·물·정비를 사용합니다. 천연가스는 판매 제품인 동시에 일부 오일샌드 공정의 연료입니다.',
        competition='캐나다 오일샌드·원유·가스 자산과 개발 서비스·운송 용량을 놓고 다른 생산사들과 경쟁합니다. 자산별 지분 생산량과 프로젝트 전체 생산능력을 구분합니다.'),
    'IMO': profile('Imperial Oil', AIF['IMO'],
        '캐나다 Kearl·Cold Lake·Syncrude의 원유 생산, 정유·Esso·Mobil 연료 판매와 화학 제품을 운영합니다. ExxonMobil 그룹과 원료·제품 거래 및 기술·업무 지원이 연결됩니다.',
        '2025년 매출·기타소득 합계 47,078,000,000 CAD는 매출 46,918,000,000 CAD와 기타소득 160,000,000 CAD의 합계입니다. 부문 표는 내부 거래 제거 전이며 ExxonMobil 관련 매출도 공시에서 별도로 확인합니다.',
        [('Kearl · 오일샌드 광산', 'Imperial 70.96%·ExxonMobil Canada Properties 29.04%의 공동사업입니다. 비투멘을 희석해 자체·ExxonMobil 정유 공장과 외부 고객으로 출하합니다.'),
         ('Cold Lake · 열회수 생산', '증기 기반 공법으로 비투멘을 회수합니다. 천연가스·증기·희석제와 용매 적용·유정·처리 설비의 운영 상태가 연결됩니다.'),
         ('Syncrude · 합성원유', 'Imperial의 참여 지분은 25%이고 Suncor가 운영합니다. 합성원유를 자체·ExxonMobil 정유 공장 및 외부 고객으로 출하합니다.'),
         ('정유·Esso·Mobil', '원유를 연료로 가공하고 캐나다 도매·유통·브랜드 판매망에 공급합니다. 브랜드 주유소 전부를 Imperial 직영 점포로 보지 않습니다.'),
         ('화학·기술 지원', '석유화학 제품을 생산·판매하며 ExxonMobil 계열의 기술·엔지니어링·연구개발·IT·고객 지원 서비스를 사용합니다.')],
        customers='자체 및 ExxonMobil 정유 사업, 원유·제품의 외부 구매자와 Esso·Mobil 유통 고객이 연결됩니다. 2025년 ExxonMobil·계열 관련 매출 13,534,000,000 CAD는 여러 제품·거래를 합친 공시 범위입니다.',
        inputs='원유·가스·희석제, 광산·열회수·정유 장비·촉매·수소·전력과 정비를 사용합니다. ExxonMobil 관련 구매 5,227,000,000 CAD에는 상품과 기술·지원 거래 등이 섞여 있습니다.',
        competition='캐나다 오일샌드 생산·개질과 연료·화학 제품 판매의 지역·제품 시장에서 경쟁합니다. ExxonMobil은 소유 관계와 실제 공급·판매 역할을 함께 가진 상대입니다.'),
    'CVE': profile('Cenovus Energy', AIF['CVE'],
        '캐나다 오일샌드·일반 원유가스와 Canada·중국·Indonesia 해상 생산, 캐나다 및 미국 정유를 연결합니다. 2025년 MEG 인수와 일부 미국 정유 지분 매각으로 현재 자산과 연간 실적 범위가 달라졌습니다.',
        '2025년 연결 매출은 49,696,000,000 CAD입니다. 오일샌드·일반 생산·해상·캐나다 정유·미국 정유의 합계에서 본사·내부 거래 제거를 반영합니다. HCML 지분법 공동사업의 자체 매출은 연결 매출에 합산하지 않습니다.',
        [('오일샌드 · SAGD·열회수', 'Foster Creek·Sunrise·Christina Lake·Lloydminster 등의 비투멘·중질유 생산입니다. 인수한 MEG 자산은 Christina Lake North로 이어집니다.'),
         ('일반 원유·가스', 'Edson·Clearwater·Rainbow Lake·Northern Corridor 등에서 가스를 생산하고 가스처리·수송 자산을 연결합니다.'),
         ('중국 Liwan · CNOOC 협업', 'Liwan 3-1·Liuhua 34-2 지분은 각 49%, Liuhua 29-1은 75%입니다. Cenovus는 심해 설비, CNOOC는 얕은 바다·육상 가스처리 시설을 운영합니다.'),
         ('캐나다·미국 정유', 'Lloydminster 개질·정유와 Lima·Superior·Toledo 등을 운영합니다. Wood River·Borger 지분은 2025년 9월 30일 Phillips 66에 매각했습니다.'),
         ('Husky Midstream · 집하·저장', 'HMLP 35% 지분·운영을 통해 Lloydminster·Hardisty 등의 집하·파이프라인·저장과 가스처리를 연결합니다. Power Assets·CK Infrastructure는 공동사업 파트너입니다.')],
        customers='원유·가스·정유제품의 도매·산업 고객에게 판매합니다. 생산물을 자체 정유 공장으로 보내는 내부 거래와 외부 판매, 지분법 공동사업의 판매를 구분합니다.',
        inputs='증기·천연가스·희석제·물, 해저 설비·가스처리, 정유 원유·수소·촉매·전력, 운송·저장·정비와 유정 개발 서비스를 사용합니다.',
        competition='캐나다 비투멘·가스 생산 및 북미 정유제품 판매에서 다른 생산·정유 사업과 경쟁합니다. 사업 매각 상대와 현재 공동 운영자를 구분합니다.'),
    'OBE': profile('Obsidian Energy', AIF['OBE'],
        'Alberta의 Peace River 중질유와 Willesden Green의 Cardium·Belly River 경질유, Viking 등을 개발·생산합니다. 2025년 Pembina 자산 매각 뒤 2026년 Belly River 자산을 추가했습니다.',
        '2025년 로열티 차감 전 원유·NGL·가스 계약 매출은 599,800,000 CAD이며 연결 매출은 571,300,000 CAD입니다. 판매 가격·물량과 로열티·처리 비용이 회계상 집계 범위를 결정합니다.',
        [('Peace River · Clearwater·Bluesky', '중질유를 다중 분지 수평 유정 등으로 생산합니다. 시추·펌프·집하·처리·희석 및 원유 출하가 연결됩니다.'),
         ('Willesden Green · Cardium', '경질유·NGL·가스 개발 자산입니다. 유정 시추·완결, 유체 처리와 생산 설비를 운영합니다.'),
         ('Belly River · Wilson Creek', 'Willesden Green 경질유 플랫폼과 연결되는 자산입니다. 2026년 추가 인수 상태는 아래 최신 사업 변경에 표시합니다.'),
         ('Viking·잔여 공동 자산', 'Alberta의 Viking 사업과 잔여 비운영 자산이 있습니다. Pembina 처분 후에도 PCU #11 비운영 지분은 남아 있습니다.')],
        customers='원유·NGL·천연가스 구매자에게 판매합니다. 공시에 이름이 공개되지 않은 구매자를 특정 정유사·거래사로 추정하지 않습니다. 자산 매수인은 생산물 구매 고객과 다른 역할입니다.',
        inputs='시추·완결·펌프·유정 정비, 전력·가스·집하·처리·운송 서비스와 토지·수자원 접근이 필요합니다. 봄철 해빙·강우가 현장 접근과 작업 시기에 연결됩니다.',
        competition='Alberta 중질유·Cardium·Belly River 자산의 생산·개발 범위가 다른 지역 생산사와 겹칩니다. 대형 통합 정유사와 같은 사업 구조는 아닙니다.'),
    'BTE': profile('Baytex Energy', AIF['BTE'],
        '캐나다 Peace River·Peavine·Lloydminster 중질유와 Pembina Duvernay·Viking 경질유·가스 자산을 운영합니다. 미국 Eagle Ford는 2025년 12월 매각됐으며 NYSE 상장이 현재 미국 유전 보유를 뜻하지 않습니다.',
        '2025년 계속사업 캐나다 계약 매출 1,684,648,000 CAD는 중질유·경질유 및 콘덴세이트·NGL·가스로 구성됩니다. 로열티 차감 후 매출 1,480,815,000 CAD와 미국 중단사업 판매를 분리합니다.',
        [('Peace River·Peavine · 중질유', 'Clearwater 등 지층에서 중질유를 개발합니다. 다중 분지 유정, 유체 처리·운송과 중질유 판매 가격 차이가 연결됩니다.'),
         ('Lloydminster · 중질유', 'Alberta·Saskatchewan의 중질유 자산입니다. 현장 생산·정비와 처리·출하 인프라를 연결합니다.'),
         ('Pembina Duvernay · 경질유', '수평 시추·완결과 원유·가스 인프라를 운영합니다. Gibson이 투자한 인프라를 Baytex가 건설·운영하는 계약이 있습니다.'),
         ('Viking · 경질유·부산물', '경질유·가스·NGL을 생산하는 캐나다 자산입니다. NGL과 가스는 원유 물량과 같은 가격·단위로 취급하지 않습니다.')],
        customers='생산 원유·NGL·가스의 구매자와 판매·수송 경로를 연결합니다. 익명 고객 집중도 표에서 실제 기업명을 추정하지 않습니다. Gibson 기반시설 협력은 모든 생산물의 매입 계약을 뜻하지 않습니다.',
        inputs='시추·파쇄·모래·물·현장 서비스, 펌프·전력·희석·처리·운송 인프라가 필요합니다. 중질유 할인폭, CAD/USD와 로열티·헤지·운송·개발 비용이 공시 수치에 연결됩니다.',
        competition='캐나다 중질유와 Duvernay·Viking 개발 범위가 다른 지역 생산사와 겹칩니다. 매각한 미국 자산의 과거 생산량을 현재 경쟁 규모에 더하지 않습니다.'),
    'VET': profile('Vermilion Energy', AIF['VET'],
        '캐나다의 액체 탄화수소가 풍부한 가스와 유럽 천연가스, 프랑스 및 호주 원유 등을 생산합니다. 국가별 가격 기준·허가·세금·운송망과 해상·육상 개발 조건이 다릅니다.',
        '2025년 계속사업 매출은 1,765,141,000 CAD입니다. 캐나다·유럽·호주 지역과 지역 미배분 항목을 함께 표시합니다. 처분한 Saskatchewan·Manitoba 및 미국 사업은 중단사업으로 구분합니다.',
        [('캐나다 · Deep Basin·Montney', 'Westbrick 인수 자산과 기존 Deep Basin·West Pembina·Mica Montney의 가스·액체 생산입니다. AECO와 다른 판매 시장으로 가는 수송 경로를 연결합니다.'),
         ('Corrib · 아일랜드 해상 가스', 'Vermilion은 56.5% 지분·운영자이며 Nephin은 43.5% 비운영 지분입니다. 해저 유정·배관·Bellanaboy 처리시설·가스망으로 연결됩니다.'),
         ('독일·네덜란드·중동부 유럽', '육상 가스·관련 유전의 개발·유정 정비·집하·처리·판매 사업입니다. 국가별 가스 가격·허가·세금 적용 범위를 구분합니다.'),
         ('프랑스 원유·호주 Wandoo', '프랑스 Aquitaine·Paris Basin 원유와 호주 해상 Wandoo 생산입니다. 호주 생산 재개와 선적·판매 시점은 서로 다를 수 있습니다.')],
        customers='캐나다 및 유럽 가스 구매자와 원유 구매자에게 판매합니다. 국가·상품·통화별 계약과 헤지 범위가 다릅니다. Corrib의 국가 내 생산 비중을 아일랜드 총 가스 수요 점유율로 표시하지 않습니다.',
        inputs='시추·완결·유정 정비와 육상·해상 설비·가스처리·파이프라인·전력, 선적·저장과 국가별 허가가 필요합니다. 태풍·정기 보수·출하 주기가 생산과 매출에 서로 다른 시점으로 반영됩니다.',
        competition='캐나다 액체 풍부 가스와 유럽 가스·원유의 자원 개발·판매 범위에서 경쟁합니다. 가스 생산량·석유환산량과 매출 비중은 서로 다른 지표입니다.'),
    'PDS': profile('Precision Drilling', AIF['PDS'],
        '원유·가스·지열 생산사를 위해 육상 시추 장비·인력·디지털 기술을 제공하고 캐나다에서 유정 완결·보수·캠프·장비 임대를 운영합니다. 자원 생산사와 달리 계약 작업·장비 사용으로 수익이 생깁니다.',
        '2025년 연결 매출은 1,843,704,000 CAD입니다. 계약 시추와 유정 완결·생산 서비스 부문 사이의 내부 거래를 제거합니다. 서비스·지역 표는 같은 제거 후 연결 범위이며 일당·시간당 서비스가 주된 매출입니다.',
        [('Super Series · 육상 시추', '2025년 말 등록 육상 시추 장비는 184대: 캐나다 95·미국 80·Kuwait 6·Saudi Arabia 3대입니다. 보유 장비 수는 실제 가동 장비 수와 다릅니다.'),
         ('Alpha · 자동화·분석', 'AlphaAutomation·AlphaApps·AlphaAnalytics가 장비 제어·시추 과정·분석을 연결합니다. 외부 앱과 자체 기술을 사용하며 특정 앱 사례를 전체 공급 계약으로 확대하지 않습니다.'),
         ('EverGreen · 에너지·계측', '배터리 저장·이중 연료·가스 엔진·전력망 연결과 연료·배출량 모니터링 제품입니다. 장비 적용 비율은 전체 시추 시장 점유율이 아닙니다.'),
         ('유정 완결·보수·현장 지원', '캐나다의 등록 보수 장비 145대, 임대 장비 2,100개 이상, 숙소·시추 캠프 등을 포함합니다. 미국 유정 보수 사업은 2025년 2분기에 종료했습니다.'),
         ('Rostel·내부 조달·정비', 'Rostel이 장비·부품 제조·정비를, Columbia Oilfield Supply와 미국 조달 조직이 소모품·현장 공급을 담당합니다. 내부 제조와 외부 구매를 구분합니다.')],
        customers='원유·가스·지열 탐사·생산사의 유정 프로그램에 장비·인력을 제공합니다. 계약은 유정별 또는 기간 계약이며 작업 일수·단가·대기·중도 종료·기술료 조건이 다릅니다.',
        inputs='시추 장비·관·탑드라이브·펌프·엔진·디지털 제어, 소모품·연료·숙련 인력·정비가 필요합니다. 장비 재가동·이동·인증·고객 전용 개조에는 별도 비용·자본 투입이 생깁니다.',
        competition='Nabors·Helmerich & Payne 등과 육상 고사양 시추 장비·인력·기술 제공 범위가 겹칩니다. 직원 보수 비교 기업 목록을 실제 경쟁사·공급사 목록으로 사용하지 않습니다.'),
}

LATEST = {
    'SU': [('정유 능력 · 2026 산정 기준', '2026년 1월 정유 명목 능력을 일일 466,000배럴에서 511,000배럴로 변경했습니다. 2분기 원유 처리량 470,600배럴과 가동률 92%는 새 분모 기준이며 이전 분기 가동률도 재작성됐습니다.', SU_Q2)],
    'CNQ': [('AOSP · 현재 사업 경계', '교환 거래는 2025년 11월 1일 완료됐습니다. Albian 광산은 100%, Scotford Upgrader·Quest는 CNQ 80%·Shell 20%이며 두 시설은 Shell 운영입니다. 공시 발표일 11월 3일과 완료일을 구분합니다.', CNQ_SWAP)],
    'IMO': [('Kearl · 총량과 지분 물량', '2026년 2분기 Kearl 총 생산은 일일 257,000배럴, Imperial 지분 몫은 182,000배럴입니다. 전체 상류 생산 414,000 석유환산배럴은 별도 그룹 범위이며 정유 보수도 있었습니다.', IMO_Q2)],
    'CVE': [('MEG · 인수와 연결 기간', 'MEG 인수는 2025년 11월 13일 완료됐습니다. Christina Lake North 사업과 2025년 인수 이후 연결 실적을 구분하며 과거 1년 전부를 Cenovus 실적으로 더하지 않습니다.', CVE_MEG),
            ('West White Rose · 개발 상태', '2026년 2분기 발표는 첫 유정 시추 진행·3분기 말 첫 원유 생산 목표를 제시합니다. 이 자료만으로 생산 개시가 완료됐다고 표시하지 않습니다. DSAP 사업의 2028년 추가 생산도 계획입니다.', CVE_Q2)],
    'OBE': [('Belly River · 실제 인수 완료', 'Wilson Creek 인수는 2026년 6월 30일 완료됐고 7월 2일 발표됐습니다. 인수 자산의 5월 기준 약 2,500 석유환산배럴/일은 회사 전체 현재 생산량이 아닙니다.', OBE_BELLY),
            ('9월 운영 · 제3자 설비와 날씨', '9월 14일 발표에서 Belly River는 제3자 압축기 문제로 7~8월 가동 중단을 겪은 뒤 약 2,400 석유환산배럴/일로 복구됐습니다. 강우에 따른 개발 지연도 반영해 연간 생산 지침을 28,500~29,500 석유환산배럴/일로 변경했습니다. 이는 실제 연간 확정 생산량이 아닙니다.', OBE_SEPTEMBER)],
    'BTE': [('Eagle Ford · 미국 사업 매각', '미국 Eagle Ford 운영·비운영 자산 매각은 2025년 12월 19일 완료됐습니다. 캐나다 현재 사업과 중단사업 연간 실적을 구분합니다. 매수 계약의 법인명은 Eagle Ford Buyer Co., LLC입니다.', BTE_SALE),
            ('2026 Q2 · 현재 캐나다 생산', '2분기 생산은 일일 71,243 석유환산배럴이며 원유·NGL 88%입니다. 실제 분기 생산과 연간 생산 지침을 구분하고 매각한 미국 생산을 현재 물량에 더하지 않습니다.', BTE_Q2)],
    'VET': [('자산 재편 · 인수·매각 완료', 'Westbrick 인수는 2025년 2월 26일, Saskatchewan·Manitoba 매각은 7월 10일, 미국 매각은 7월 31일 완료됐습니다. 캐나다 전체 사업을 철수한 것은 아닙니다.', FIN['VET']),
            ('Wisselshorst · 생산 개시', '2026년 7월 독일 Wisselshorst 첫 유정 생산을 시작했습니다. 이후 설비 확대·추가 시추는 계획입니다. 호주 Wandoo는 2분기 생산을 재개했지만 그 분기 원유 선적은 없었습니다.', VET_Q2)],
    'PDS': [('국제 장비 · 가동·향후 계약', '2026년 2분기 실제 가동 장비는 국제 7대: Saudi Arabia 3·Kuwait 4대입니다. 추가 Kuwait 5년 계약은 기존 장비 재인증·개조 뒤 2027년 중반 가동 계획으로 현재 8대 가동을 뜻하지 않습니다.', PDS_Q2)],
}

DRIVERS = {
    'SU': [('판매·정제의 가격 기준', '생산 원유 가격, 비투멘·합성원유 가격 차이와 정유제품·원유 가격 차이가 서로 다른 사업의 수익에 연결됩니다.'), ('증기·희석·정비', '천연가스·희석제·전력·물 투입, 광산·개질·정유의 정기 보수·가동 중단 및 로열티가 생산·현금흐름에 반영됩니다.')],
    'CNQ': [('상품·공법별 비용', '가스·원유·비투멘·합성원유별 가격과 천연가스·희석제·증기·전력·유정·광산 비용을 구분합니다.'), ('운송·가공 약정', '운송 용량 약정과 NWRP의 장기 가공 대가·부채 부담은 실제 수송량·제품 매출과 별도로 지속될 수 있습니다.')],
    'IMO': [('원유·정유제품과 보수', '원유 판매 가격과 정유 마진, 광산·열회수·정유 설비의 보수·가동률, 재고·운송·제품 배합이 연결됩니다.'), ('그룹 내 서비스와 거래', 'ExxonMobil 계열 상품·기술·지원 거래의 범위와 비계열 외부 거래를 구분합니다. 계열 거래 총액은 단일 제품 공급액이 아닙니다.')],
    'CVE': [('증기·희석제·정유 원료', '오일샌드의 가스·증기·희석제 비용과 정유의 원유·제품 가격 차이, 보수·가동·운송·저장이 서로 다른 수치에 반영됩니다.'), ('사업 변화와 회계 범위', 'MEG 편입 시점, 미국 정유 지분 매각 전후와 지분법 공동사업 실적·배당을 연결·생산 물량과 구분합니다.')],
    'OBE': [('중질유와 경질유', '원유 상품 가격·중질유 할인폭, AECO 가스 가격, CAD/USD와 로열티·처리·운송 비용이 제품별 판매·현금흐름에 연결됩니다.'), ('개발·현장 접근', '시추·완결·유정 생산 감소·장비·인력과 봄 해빙·강우, 토지·지역사회 접근 조건이 작업·출하 일정에 연결됩니다.')],
    'BTE': [('중질유 가격·비용', 'WCS·WTI 가격 차이와 CAD/USD, 로열티·희석·처리·운송·시추·완결 비용이 공시 수치에 반영됩니다.'), ('헤지·개발·집계 기간', '헤지의 실현 결제와 미실현 평가, 실제 유정 생산과 개발 전망, 캐나다 계속사업과 매각 자산의 기간을 분리합니다.')],
    'VET': [('국가별 가스·원유', 'AECO·유럽 가스·원유 기준, 수송 시장·국가별 세금·환율·허가가 다릅니다. 가스 석유환산 비율을 판매액 비율로 사용하지 않습니다.'), ('가동·선적·헤지', '태풍·공장 보수·유정 정비·선적 주기와 실현·미실현 헤지 결과가 생산·판매·손익에 각각 반영됩니다.')],
    'PDS': [('계약 단가와 작업량', '작업 일수·시간, 계약 단가, 대기·부족분 보상·중도 종료·기술료와 국가별 장비 배치가 매출을 구성합니다.'), ('재가동·관·인력', '장비 재가동·이동·인증·개조 비용, 시추관 수명·정비·인력·연료와 환율이 비용·현금·감가상각에 연결됩니다.')],
}
for symbol, notes in PUBLIC.items():
    notes['brief'][1]['source'] = FIN[symbol]
    notes['brief'].extend(fact(title,text,origin) for title,text,origin in LATEST[symbol])
    notes['drivers'] = [fact(title,text,AIF[symbol]) for title,text in DRIVERS[symbol]]
    notes['revenue_mix'] = REPORTS[symbol]['revenue_mix']
    notes['sources'] += [FIN[symbol], *[origin for _,_,origin in LATEST[symbol]]]

PUBLIC['VET']['market_shares'] = [fact('Corrib · 아일랜드 국내 가스 생산 범위',
    '2025년 AIF는 Corrib가 아일랜드 국내 천연가스 생산의 100%라고 명시합니다. 수입 가스를 포함한 총 수요 점유율이나 Vermilion 단독 귀속 생산량의 점유율은 아닙니다.', AIF['VET'])]

PRIVATE = {}
CONTEXT = [
    ('syncrude','Syncrude',AIF['SU'],'오일샌드 노천 채굴·추출·개질로 합성원유를 생산하는 공동 운영 사업입니다. Suncor가 운영하고 Suncor 58.74%·Imperial 25% 등의 지분 소유자가 자기 몫을 판매합니다.','Mildred Lake·Aurora 광산에서 비투멘을 회수해 개질하고 운송망으로 출하합니다.'),
    ('komatsu','Komatsu',SU_EQUIPMENT,'Suncor 광산의 대형 굴착기와 자율운반 장비·소프트웨어에 연결된 장비 업체입니다. 이 페이지는 확인한 Suncor 공급·개발 역할을 정리합니다.','2025년 5월 설명에서 Fort Hills PC9000 첫 장비 투입 및 SMS와 운반 시스템 공동 개발을 확인합니다.'),
    ('sms-equipment','SMS Equipment',SU_EQUIPMENT,'Suncor 광산에서 Komatsu 장비·자율운반 기술과 현장 적용·지원에 연결되는 공급 업체입니다.','PC9000 공급·적용과 광산 자율운반 소프트웨어 개발의 확인된 역할이며 그룹 전체 매출·독점 공급을 뜻하지 않습니다.'),
    ('canadian-tire','Canadian Tire Corporation',AIF['SU'],'캐나다의 소매·주유소 사업자이며 Suncor의 Petro-Canada 주유소 재브랜딩·연료 유통 협력 상대입니다.','Suncor 2025 AIF가 해당 주유소 제휴·브랜드 전환을 명시합니다. 모든 점포를 Suncor 직영으로 보지 않습니다.'),
    ('north-west-redwater','North West Redwater Partnership',AIF['CNQ'],'Alberta에서 비투멘을 경유 등으로 가공하는 NWRP 공동사업입니다. CNQ 50% 지분과 비투멘 처리 계약 25%를 구분합니다.','명목 제품 출력 약 80,000배럴/일, 비투멘 투입 약 50,000배럴/일입니다. 처리 계약에서 CNQ 12,500·APMC 37,500배럴/일이며 실제 생산량은 별도입니다.'),
    ('alberta-petroleum-marketing','Alberta Petroleum Marketing Commission',AIF['CNQ'],'Alberta 정부의 에너지 판매 기관으로 NWRP 비투멘 가공 계약에서 75%의 가공 대가 부담 주체입니다.','NWRP에서 APMC의 비투멘 투입 범위는 약 37,500배럴/일입니다. 처리 계약 비중을 NWRP 소유 지분으로 해석하지 않습니다.'),
    ('cnooc-group','China National Offshore Oil Corporation · CNOOC',AIF['CVE'],'Cenovus의 Liwan·Liuhua 중국 해상 가스 공동사업에서 얕은 바다 설비·중앙 플랫폼·육상 가스처리를 운영하는 파트너입니다.','Cenovus 심해 생산과 CNOOC의 가스처리·운송 설비가 중국 상업 가스 시장으로 연결됩니다. 여기서는 확인한 프로젝트 역할을 정리합니다.'),
    ('husky-midstream','Husky Midstream Limited Partnership',AIF['CVE'],'Cenovus가 운영하는 집하·파이프라인·저장·가스처리 공동사업입니다. 지분은 Cenovus 35%·Power Assets 49%·CK Infrastructure 16%입니다.','Lloydminster·Hardisty 등의 파이프라인 약 2,300km, 저장 약 5,900,000배럴과 Ansell·Corser 가스처리를 통해 생산·판매 경로를 연결합니다.'),
    ('power-assets','Power Assets Holdings',AIF['CVE'],'Husky Midstream에서 49% 지분을 가진 인프라 투자 파트너입니다.','이 기록은 Cenovus의 집하·운송·저장 공동사업 역할이며 회사 전체 발전·전력 사업 분석은 아닙니다.'),
    ('ck-infrastructure','CK Infrastructure Holdings',AIF['CVE'],'Husky Midstream에서 16% 지분을 가진 인프라 투자 파트너입니다.','Cenovus가 운영하는 공동사업의 인프라·지분 역할을 설명하며 원유 구매 고객이나 직접 설비 공급 계약을 뜻하지 않습니다.'),
    ('husky-cnooc-madura','Husky-CNOOC Madura Limited',AIF['CVE'],'Indonesia Madura 해상 NGL·천연가스 탐사·생산 공동사업입니다. Cenovus는 40% 지분의 지분법 투자자입니다.','공동사업의 자체 매출과 Cenovus 연결 매출을 구분합니다. 중국 Liwan 심해 운영 사업과 다른 법인·자산입니다.'),
    ('inplay-oil','InPlay Oil',AIF['OBE'],'Obsidian의 Pembina 자산을 2025년 4월 인수한 캐나다 원유·가스 생산사입니다.','Obsidian은 일부 PCU #11 지분을 남겼고 거래 대가에 Willesden Green Cardium Unit #2 지분을 받았습니다. Obsidian의 InPlay 주식은 8월 Delek에 매각됐습니다.'),
    ('delek-group','Delek Group',AIF['OBE'],'Obsidian이 보유하던 InPlay 주식을 2025년 8월 인수한 거래 상대입니다.','거래는 2025년 8월 7일 완료됐습니다. Delek US Holdings(DK)와 다른 기업이며 원유 공급·구매 관계로 분류하지 않습니다.'),
    ('gibson-energy','Gibson Energy',AIF['BTE'],'Baytex의 Pembina Duvernay 원유·가스 인프라에 자금을 투입하고 Edmonton 터미널 접근을 연결하는 캐나다 인프라 사업자입니다.','2025 AIF의 15년 계약에서 약 50,000,000 CAD 투자와 Baytex 건설·운영을 확인합니다. 해당 인프라는 2025년 4분기 완공됐습니다.'),
    ('eagle-ford-buyer','Eagle Ford Buyer Co., LLC',BTE_BUYER,'Baytex 미국 Eagle Ford 사업 매각 계약의 법적 매수인입니다.','2025년 11월 계약 당사자이며 매각은 12월 19일 완료됐습니다. 공개 근거 없이 최종 소유자·운영 공급사·계약 조건을 추정하지 않습니다.'),
    ('nephin-energy','Nephin Energy',CORRIB_PARTNERS,'Corrib 해상 가스 사업의 43.5% 비운영 지분 파트너입니다. Vermilion의 56.5% 운영 지분과 연결됩니다.','Bellanaboy 가스처리시설·가스망과 관련한 Corrib 공동사업 역할이며 다른 Nephin 재생가스 사업의 매출과 같지 않습니다.'),
    ('gas-networks-ireland','Gas Networks Ireland',CORRIB_HYDROGEN,'Corrib·Bellanaboy 시설의 수소 시험사업 가능성 검토에 참여하는 아일랜드 가스망 사업자입니다.','2026년 협약은 타당성 조사·기술 평가 단계입니다. 상업 수소 대량 생산·Vermilion 장기 수소 구매 계약의 완료를 뜻하지 않습니다.'),
    ('san-antonio-internacional','San Antonio Internacional',AIF['PDS'],'Argentina 현장 운영 역량을 Precision 장비·Alpha 기술과 연결하는 육상 시추 협력 상대입니다.','2025년 12월 전략 협약은 Argentina 비전통 유전 시추 기회 개발이며 이 공시만으로 새 장비 납품·상업 작업 완료를 확정하지 않습니다.'),
    ('rostel-industries','Rostel Industries',AIF['PDS'],'Precision 시추·보수 장비와 부품을 제조·개조·수리하는 Calgary 기반 내부 제조·정비 조직입니다.','2025년 Rostel 매출 약 82%가 Precision 업무와 관련됩니다. Precision 전체 매출의 82%라는 뜻은 아닙니다.'),
    ('columbia-oilfield-supply','Columbia Oilfield Supply',AIF['PDS'],'캐나다 Precision 장비 현장의 소모품을 조달·포장·배포하는 내부 공급 조직입니다.','공통 구매·재고·현장 공급 업무를 수행합니다. 외부 원자재 판매 고객이나 그룹 전체 독점 공급 계약으로 표시하지 않습니다.'),
    ('pason-systems','Pason Systems',PDS_PASON,'Precision AlphaApps의 Pason DAS 시추 기술 제품 사례에 연결되는 업체입니다.','2022년 공식 제품 사례로 확인한 기술 통합 범위입니다. 현재 전체 장비의 설치율·구매액·독점 계약을 뜻하지 않습니다.'),
    ('whitecap-resources','Whitecap Resources',ALBERTA_UNITS,'Alberta 정부의 2026년 9월 17일 사업 단위 목록에서 Pembina Cardium Unit #11(65643)의 운영사로 확인되는 원유·가스 기업입니다.','Obsidian의 같은 자산 45% 비운영 참여 공시와 대조한 공동사업 연결입니다. 정부 목록에는 Whitecap 소유 지분·다른 참여자 전원의 지분이 나오지 않으므로 이를 추정하지 않습니다.'),
    ('pembina-cardium-unit-11','Pembina Cardium Unit #11',AIF['OBE'],'Alberta Pembina 지역의 Cardium 경질유 공동사업이며 Obsidian이 45% 비운영 지분으로 참여합니다.','Alberta 정부가 사업 단위 65643의 운영사를 Whitecap Resources로 기재합니다. 매각한 Obsidian 직영 Pembina 자산과 구분되는 잔여 공동사업입니다.'),
    ('glj-reserves','GLJ Ltd.',AIF['OBE'],'Obsidian의 2025년 말 원유·가스·NGL 매장량 및 미래 순수익을 독립 평가한 에너지 평가 기관입니다.','2026년 1월 23일 보고서는 2025년 12월 31일 기준 매장량을 평가했습니다. 평가 기관을 유전 운영사·원유 구매자나 시추 장비 업체로 표시하지 않습니다.'),
    ('isn-contractor-management','ISN',OBE_ISN,'Obsidian이 사용하는 ISNetworld 협력사·공급사 정보 및 안전·보험·운송사업자 검증 플랫폼의 제공사입니다.','2026년 4월 발표로 안전 프로그램 평가·운송사업자 추적·내부 조달/ERP 연계의 실제 사용을 확인했습니다. 검토 중인 하도급·사이버·재무 기능을 이미 사용 중이라고 표시하지 않습니다.'),
]
for key,name,origin,business,structure in CONTEXT:
    PRIVATE[key] = profile(name,origin,business,structure)

EDGES = {
    'SU': [relation('Syncrude',None,'partner','채굴·개질 공동 운영 사업 · Suncor 운영·58.74%; 각 소유자가 자기 지분 물량을 판매.',AIF['SU'],'syncrude'),
           relation('Imperial Oil','IMO','partner','Syncrude의 25% 지분 파트너 · Suncor는 58.74%·운영자로 광산·개질 자산을 함께 연결.',AIF['IMO']),
           relation('Enbridge','ENB','supplier','오일샌드 출하의 Athabasca Terminal 및 정유소의 Line 9·Mainline/Lakehead 운송 경로.',AIF['SU']),
           relation('Pembina Pipeline','PBA','supplier','Syncrude 합성원유를 Alberta Oil Sands Pipeline으로 시장에 운송.',AIF['SU']),
           relation('Komatsu',None,'supplier','Base Plant 자율운반 기술 공동 개발·Fort Hills PC9000 첫 장비 2025-05-01 투입 · 후속 장비는 당시 계획과 구분.',SU_EQUIPMENT,'komatsu'),
           relation('SMS Equipment',None,'supplier','Komatsu 장비·자율운반의 현장 적용·공동 개발·지원 · 2025년 실적 설명 확인 범위.',SU_EQUIPMENT,'sms-equipment'),
           relation('Caterpillar','CAT','supplier','Syncrude Aurora에서 797 운반 트럭 사용을 2025-05 설명에서 확인 · 신규 발주·현재 전체 장비 수를 뜻하지 않음.',SU_EQUIPMENT),
           relation('Canadian Tire Corporation',None,'partner','Petro-Canada 주유소 재브랜딩·연료 유통 협력 · 2025 AIF의 실제 사업 역할.',AIF['SU'],'canadian-tire'),
           relation('Trans Mountain',None,'supplier','정유·생산 사업의 원유·제품 출하 운송 경로 · 제품 매수인으로 추정하지 않음.',AIF['SU'],'trans-mountain')],
    'CNQ': [relation('Shell','SHEL','partner','Albian 광산 분리 후 Scotford Upgrader·Quest 공동사업 · CNQ 80%·Shell 20%, Shell 운영.',CNQ_SWAP),
            relation('Shell','SHEL','supplier','Scotford Upgrader·Quest의 개질·CO₂ 포집 운영을 담당 · 단순 지분 소유와 다른 운영 역할.',CNQ_SWAP),
            relation('Enbridge','ENB','supplier','Flanagan South 원유 운송 약정과 Westcoast 가스 운송 경로 · 약정 용량은 실제 물량이 아님.',AIF['CNQ']),
            relation('TC Energy','TRP','supplier','Canadian Mainline 천연가스 운송 경로 · Keystone 원유망 운영사와 구분.',AIF['CNQ']),
            relation('South Bow','SOBO','supplier','Keystone Base 원유 운송 약정 10,000배럴/일 · 실제 사용량·매출은 별도이며 South Bow 운영망.',AIF['CNQ']),
            relation('Trans Mountain',None,'supplier','확장 원유 운송 약정 169,000배럴/일 · 실제 수송량이 아닌 확보 용량.',AIF['CNQ'],'trans-mountain'),
            relation('North West Redwater Partnership',None,'partner','비투멘 가공·정유 JV · CNQ 지분50%·가공 계약25%, 40년 약정은 2058년까지.',AIF['CNQ'],'north-west-redwater')],
    'IMO': [relation('ExxonMobil','XOM','supplier','2025년 계열 관련 구매 5,227,000,000 CAD · 원유·제품·기술·엔지니어링·지원 등의 묶음이며 단일 원료 구매가 아님.',AIF['IMO']),
            relation('ExxonMobil','XOM','customer','2025년 ExxonMobil·계열 관련 매출 13,534,000,000 CAD · 상품·여러 거래의 공시 합계.',AIF['IMO']),
            relation('ExxonMobil','XOM','partner','Kearl 공동사업 · Imperial70.96%·ExxonMobil Canada Properties29.04%와 그룹 기술·업무 협력.',AIF['IMO']),
            relation('Suncor Energy','SU','partner','Syncrude 공동 생산·개질 · Imperial25%, Suncor58.74%·운영.',AIF['IMO']),
            relation('Syncrude',None,'partner','25% 참여 · 합성원유를 Imperial·ExxonMobil 정유 공장 및 외부 구매자에게 출하.',AIF['IMO'],'syncrude')],
    'CVE': [relation('China National Offshore Oil Corporation · CNOOC',None,'partner','Liwan·Liuhua 가스의 얕은 바다·중앙 플랫폼·Gaolan 가스처리 운영, Cenovus는 심해 설비 운영.',AIF['CVE'],'cnooc-group'),
            relation('Husky Midstream Limited Partnership',None,'supplier','집하·파이프라인·저장·가스처리로 Cenovus 생산·판매 경로를 연결 · 그룹 외부·자체 물량 범위 구분.',AIF['CVE'],'husky-midstream'),
            relation('Husky Midstream Limited Partnership',None,'partner','Cenovus35%·운영, Power Assets49%·CK Infrastructure16%의 인프라 JV.',AIF['CVE'],'husky-midstream'),
            relation('Power Assets Holdings',None,'partner','Husky Midstream 공동사업의 49% 지분 파트너 · 가스·원유 구매 고객으로 추정하지 않음.',AIF['CVE'],'power-assets'),
            relation('CK Infrastructure Holdings',None,'partner','Husky Midstream 공동사업의 16% 지분 파트너.',AIF['CVE'],'ck-infrastructure'),
            relation('Husky-CNOOC Madura Limited',None,'partner','Indonesia Madura 해상 가스·NGL 지분법 공동사업 · Cenovus40%, 자체 매출은 연결 매출에 더하지 않음.',AIF['CVE'],'husky-cnooc-madura'),
            relation('Enbridge','ENB','supplier','Flanagan South 등 장기 파이프라인 경로로 자체 정유소·미국 걸프·외부 고객에 원유 운송.',AIF['CVE']),
            relation('South Bow','SOBO','supplier','Keystone 원유 운송 경로 · 현재 운송망 운영사 근거는 South Bow 원문에 함께 제공.',AIF['CVE']),
            relation('Trans Mountain',None,'supplier','확장 원유망을 통한 캐나다 서안·판매 시장 접근 경로.',AIF['CVE'],'trans-mountain'),
            relation('Phillips 66','PSX','transaction','WRB Wood River·Borger 지분 50%를 2025-09-30 매각 · 현재 Cenovus JV로 표시하지 않음.',AIF['CVE'])],
    'OBE': [relation('Whitecap Resources',None,'partner','정부 목록의 PCU #11(65643) 운영사 · Obsidian45% 비운영 참여 공시와 동일 자산 대조; Whitecap 지분은 추정하지 않음.',ALBERTA_UNITS,'whitecap-resources'),
            relation('Pembina Cardium Unit #11',None,'partner','45% 비운영 참여 · 매각한 직영 Pembina 자산과 구분되는 공동 유전.',AIF['OBE'],'pembina-cardium-unit-11'),
            relation('GLJ Ltd.',None,'supplier','2025-12-31 기준 원유·가스·NGL 독립 매장량 평가 서비스 · 시추 장비나 원유 공급 역할이 아님.',AIF['OBE'],'glj-reserves'),
            relation('ISN',None,'supplier','ISNetworld 협력사 안전·보험·운송사업자 검증·조달/ERP 연계 · 실제 사용 확대를2026-04-14 공식 발표.',OBE_ISN,'isn-contractor-management'),
            relation('InPlay Oil',None,'transaction','Pembina 자산 매각 2025-04-07 완료, WG Cardium Unit #2 지분을 대가로 수취 · 지속적 공급·고객 관계가 아님.',AIF['OBE'],'inplay-oil'),
            relation('Delek Group',None,'transaction','InPlay 주식 9,139,784주 매각 2025-08-07 완료 · Delek US(DK)와 다른 법인.',AIF['OBE'],'delek-group')],
    'BTE': [relation('Gibson Energy',None,'partner','2025 AIF의 15년 Duvernay 인프라 약정 · Gibson 약50,000,000 CAD 투자, Baytex 건설·운영, Q4완공.',AIF['BTE'],'gibson-energy'),
            relation('Gibson Energy',None,'supplier','Duvernay 기반시설·Edmonton 터미널 시장 접근을 연결 · 모든 생산물을 구매하는 고객 계약으로 추정하지 않음.',AIF['BTE'],'gibson-energy'),
            relation('Eagle Ford Buyer Co., LLC',None,'transaction','미국 사업 매각 계약의 법적 매수인 · 2025-12-19 완료, 최종 소유자·현재 협력 관계를 추정하지 않음.',BTE_BUYER,'eagle-ford-buyer')],
    'VET': [relation('Nephin Energy',None,'partner','Corrib 가스 공동사업 · Nephin43.5% 비운영, Vermilion56.5%·운영.',CORRIB_PARTNERS,'nephin-energy'),
            relation('Gas Networks Ireland',None,'partner','Corrib·Bellanaboy의 수소 시험사업 타당성·기술 검토 협약 · 상업 대량 생산·구매 계약 아님.',CORRIB_HYDROGEN,'gas-networks-ireland')],
    'PDS': [relation('San Antonio Internacional',None,'partner','2025-12 Argentina 비전통 유전 시추 시장 협약 · 현지 운영+Precision 장비·Alpha 기술, 실제 신규 작업 완료와 구분.',AIF['PDS'],'san-antonio-internacional'),
            relation('Rostel Industries',None,'supplier','내부 장비·부품 제조·개조·정비 · Rostel2025매출82%가 Precision업무; 그룹 매출 비중 아님.',AIF['PDS'],'rostel-industries'),
            relation('Columbia Oilfield Supply',None,'supplier','캐나다 내부 소모품 조달·현장 배포 조직 · 외부 독점 공급 계약 아님.',AIF['PDS'],'columbia-oilfield-supply'),
            relation('Pason Systems',None,'partner','AlphaApps Pason DAS 제품 통합 사례 · 2022년 공식 제품 자료 확인, 현재 전 장비 설치·독점 계약을 뜻하지 않음.',PDS_PASON,'pason-systems')],
}

# Competitors are explicitly a comparison of disclosed business footprints,
# supported by both companies' originals, not a fabricated issuer peer list.
for symbol, peers, scope in [
    ('SU',['CNQ','CVE'],'캐나다 오일샌드 생산·개질'),
    ('CNQ',['SU','IMO'],'캐나다 오일샌드 생산·개질'),
    ('IMO',['SU','CVE'],'캐나다 원유 생산·정유·연료'),
    ('CVE',['SU','IMO'],'캐나다 오일샌드·정유'),
    ('OBE',['BTE','CNQ'],'Alberta 중질유·경질유 개발'),
    ('BTE',['OBE','CNQ'],'Alberta 중질유·Duvernay 개발'),
    ('VET',['EQNR','BP'],'유럽 천연가스 생산·판매'),
    ('PDS',['NBR','HP'],'북미 육상 고사양 시추 서비스'),
]:
    for peer in peers:
        origin = AIF.get(peer) or report(peer)
        name = PUBLIC.get(peer, {}).get('name') or {'EQNR':'Equinor','BP':'BP','NBR':'Nabors Industries','HP':'Helmerich & Payne'}[peer]
        EDGES[symbol].append(relation(name,peer,'competitor',scope+' · 양사 원문 사업 범위를 비교한 경쟁 후보; 실제 거래·공시 지정 경쟁사 목록은 아님.',origin))
        PUBLIC[symbol]['sources'].append(origin)

for symbol in ['CNQ','CVE']:
    PUBLIC[symbol]['sources'].append(KEYSTONE)
PUBLIC['SU']['brief'].append(fact('광산 장비 · 실제 후속 인도',
    'Komatsu·SMS는 두 번째 Fort Hills PC9000을 2025년 8월 실제 인도했고 11월 12일 이를 발표했습니다. 5월 설명의 7월 인도 계획과 실제 완료 시점을 구분하며 이후 추가 장비의 완료를 추정하지 않습니다.',SU_SECOND_SHOVEL))
PUBLIC['SU']['sources'].extend([SU_EQUIPMENT,SU_SECOND_SHOVEL])
PUBLIC['OBE']['sources'].extend([ALBERTA_UNITS,OBE_ISN])
PUBLIC['OBE']['products'][3]['detail'] += ' PCU #11에는 45% 비운영 지분으로 참여합니다.'
PUBLIC['OBE']['brief'].append(fact('PCU #11 · 정부 기록의 운영사',
    '2026년 9월 17일 Alberta 정부 목록에서 Pembina Cardium Unit #11(65643)의 운영사는 Whitecap Resources입니다. Obsidian의 동일 이름 비운영 자산 공시와 대조했습니다. 정부 목록에 없는 Whitecap 소유 지분은 추정하지 않습니다.',ALBERTA_UNITS))
PRIVATE['whitecap-resources']['sources'].append(AIF['OBE'])
PRIVATE['pembina-cardium-unit-11']['sources'].append(ALBERTA_UNITS)
for key,edges in {
    'syncrude':[relation('Suncor Energy','SU','partner','광산·개질 운영·58.74% 지분, 각 지분 보유자가 자기 물량을 판매.',AIF['SU']),relation('Imperial Oil','IMO','partner','25% 참여·귀속 합성원유 출하.',AIF['IMO']),relation('Pembina Pipeline','PBA','supplier','Alberta Oil Sands Pipeline으로 시장 출하.',AIF['SU'])],
    'north-west-redwater':[relation('Canadian Natural Resources','CNQ','customer','비투멘 가공 계약 25%·지분50% · 처리 몫과 소유 지분은 다른 범위.',AIF['CNQ']),relation('Alberta Petroleum Marketing Commission',None,'customer','비투멘 투입·가공 대가의75% · 소유 지분을 뜻하지 않음.',AIF['CNQ'],'alberta-petroleum-marketing')],
    'husky-midstream':[relation('Cenovus Energy','CVE','customer','집하·원유 운송·저장·가스처리 서비스의 생산·판매 연결.',AIF['CVE']),relation('Power Assets Holdings',None,'partner','49% 지분 공동사업 파트너.',AIF['CVE'],'power-assets'),relation('CK Infrastructure Holdings',None,'partner','16% 지분 공동사업 파트너.',AIF['CVE'],'ck-infrastructure')],
    'nephin-energy':[relation('Vermilion Energy','VET','partner','Corrib43.5%비운영·56.5%운영 공동사업.',CORRIB_PARTNERS),relation('Gas Networks Ireland',None,'partner','Corrib 수소 시험사업 검토 단계 협약.',CORRIB_HYDROGEN,'gas-networks-ireland')],
    'pembina-cardium-unit-11':[relation('Whitecap Resources',None,'partner','Alberta 정부 단위65643의 PCU #11 운영사 · 지분 추정 없음.',ALBERTA_UNITS,'whitecap-resources'),relation('Obsidian Energy','OBE','partner','45% 비운영 지분·시추·생산 공동사업 참여.',AIF['OBE'])],
}.items():
    PRIVATE[key]['relations'] = edges
