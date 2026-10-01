"""Reviewed industry reading and explicit partner lists from free issuer documents.

Separate company business descriptions from relationship announcements. Dates,
regions and plans are retained; list membership does not identify a product order.
"""
import json
from pathlib import Path
from .company_research_notes import source, profile, relation

REPORTS = json.loads(Path(__file__).with_name('company_industry_reports.json').read_text())

def annual(symbol):
    return {**REPORTS[symbol], 'label':symbol + ' · SEC 연차 공시'}

# Business, revenue, sales channel, inputs. No investment ratings or forecasts.
READING = {
    'ADI':('Analog Devices','아날로그·혼합 신호·전력·디지털 신호처리 반도체를 설계·제조합니다. 물리 신호를 측정하고 전자 시스템이 처리할 수 있도록 변환하는 부품 기업입니다.','데이터 변환기·증폭기·전력관리·RF 반도체와 관련 솔루션을 판매합니다.','산업·자동차·통신·소비자 전자기기 제조사를 대상으로 공급합니다.','반도체 공정·패키징·검사와 제품 설계 채택, 산업·자동차 생산 수요가 연결됩니다.'),
    'TXN':('Texas Instruments','전력과 실제 환경의 신호를 다루는 아날로그 반도체, 기기에 내장되는 프로세서를 설계·제조합니다.','아날로그·임베디드 처리 제품의 판매가 매출 원천입니다.','산업·자동차·데이터센터·개인 전자기기·통신 장비가 최종 사용 시장입니다.','자체 생산 시설과 웨이퍼 공정·조립·검사, 고객의 부품 재고와 설계 채택을 확인합니다.'),
    'GLW':('Corning','특수 유리·세라믹·광섬유 기술로 통신망·디스플레이·기기·자동차·생명과학용 재료와 부품을 공급합니다.','광통신, 디스플레이, 특수 소재, 자동차, 생명과학 제품 판매로 매출이 발생합니다.','통신망·데이터센터 운영사와 기기·자동차·실험실 관련 기업이 사용합니다.','광섬유·유리 제조 역량, 고객 설비 투자와 생산량, 에너지·환율을 확인합니다.'),
    'AMKR':('Amkor Technology','칩 제조 뒤의 패키징·검사를 위탁 수행하는 반도체 후공정 기업입니다.','첨단·일반 패키징과 관련 검사 서비스에서 매출이 발생합니다.','반도체 설계·제조사와 기기 제조사가 후공정을 위탁합니다.','고객이 맡긴 웨이퍼를 가공하며 패키지 소재·장비·수율·생산능력이 필요합니다. 웨이퍼 위탁과 원료 구매를 구분합니다.'),
    'LITE':('Lumentum','데이터센터와 통신망의 광신호 전송용 부품·모듈 및 레이저 기술을 공급합니다.','광통신 부품·모듈과 관련 광학·레이저 제품 판매가 사업의 기반입니다.','광통신·네트워크 장비와 데이터센터 관련 시장을 대상으로 합니다.','광학·반도체 생산과 고객의 데이터센터·통신망 투자, 제품 전환을 확인합니다.'),
    'COHR':('Coherent','레이저·광학 소재·광통신 부품을 제공하는 광전자 기술 기업입니다.','데이터센터·통신용 광부품과 산업용 레이저·소재 제품을 판매합니다.','데이터센터·통신망·산업용 장비와 관련 기기 제조사가 사용합니다.','광학 소재·정밀 가공·반도체 공정과 고객 설비 투자·제품 채택이 연결됩니다.'),
    'QRVO':('Qorvo','모바일 등 기기의 무선 신호를 송수신하는 RF 솔루션과 연결 기술을 공급합니다.','RF 반도체·모듈 등 제품 판매가 사업의 기반입니다.','모바일·통신·산업·방위 관련 고객의 기기에 제품이 채택됩니다.','고객 제품의 설계 채택과 생산량, RF 공정·패키징·외주 생산을 확인합니다. 공시의 매각 사업은 현 사업과 구분합니다.'),
    'NXPI':('NXP Semiconductors','자동차·산업·사물인터넷·모바일·통신 인프라용 반도체를 설계·공급합니다.','프로세서·마이크로컨트롤러·연결·보안·아날로그 반도체 제품 판매가 매출 원천입니다.','자동차와 전자 시스템 제조사·유통망을 통해 판매합니다.','자체·외주 반도체 생산, 패키징·검사와 자동차·산업 고객의 생산·재고가 연결됩니다.'),
    'JBL':('Jabil','고객 제품의 전자·기구 설계부터 조달·제조·조립·공급망 운영을 수행하는 제조 서비스 기업입니다.','고객별 제조 프로그램과 설계·관련 서비스에서 매출이 발생합니다.','클라우드·네트워크·의료·자동차·에너지·소비자 제품 기업 등이 제조를 위탁합니다.','전자 부품·기계 부품 조달, 생산라인 가동률·물류와 고객 프로그램의 시작·종료를 확인합니다.'),
    'FLEX':('Flex','제품 설계·공급망·전자 제조와 데이터센터용 전력·냉각·인프라 솔루션을 제공합니다.','제조·시스템 조립 서비스가 주된 매출 원천이며 전력·냉각·인프라 제품도 제공합니다.','기술·자동차·의료·산업·데이터센터 관련 고객의 제품과 시스템을 생산합니다.','부품·원재료 조달, 글로벌 제조·물류, 전력·열 관리와 고객 주문 변화가 연결됩니다.'),
    'DELL':('Dell Technologies','기업용 서버·스토리지·네트워크 인프라와 PC·주변기기를 공급합니다.','Infrastructure Solutions Group과 Client Solutions Group의 제품·서비스 판매로 매출이 발생합니다.','기업·공공기관·개인 고객에게 직접 또는 판매 파트너를 통해 제공합니다.','반도체·메모리·저장장치와 시스템 조립 공급망, 고객 IT 투자와 제품 수요를 확인합니다.'),
    'CSCO':('Cisco Systems','스위치·라우터·무선·서버 등 네트워크 하드웨어·소프트웨어와 보안·협업 솔루션을 제공합니다.','장비 판매와 소프트웨어·지원 서비스 매출을 구분합니다.','기업·공공기관·통신 사업자의 네트워크와 데이터센터에 사용됩니다.','반도체·광부품·외주 생산과 고객 네트워크 투자·소프트웨어 계약을 확인합니다.'),
    'META':('Meta Platforms','Facebook·Instagram·WhatsApp·Messenger 등 앱과 AR·VR 관련 Reality Labs 사업을 운영합니다.','주된 매출 원천은 앱에서 표시되는 광고입니다. 소비자 이용과 광고주의 광고비 지출을 구분합니다.','앱 이용자는 일반 소비자이며 광고 매출을 지급하는 고객은 광고주입니다.','데이터센터·AI 컴퓨팅 투자, 콘텐츠 관리와 모바일 플랫폼의 광고 측정·개인정보 정책이 연결됩니다.'),
    'NFLX':('Netflix','시리즈·영화·게임·라이브 프로그램을 제공하는 구독형 엔터테인먼트 서비스입니다.','주된 매출 원천은 회원의 월 구독료이며 광고 포함 요금제도 제공합니다.','일반 소비자가 서비스 요금제를 구독하고 콘텐츠를 이용합니다.','콘텐츠 제작·라이선스 비용, 콘텐츠 권리·상각, 스트리밍 전달망과 회원 유지가 연결됩니다.'),
    'WMT':('Walmart','매장·전자상거래·회원제 Sam’s Club을 연결하는 유통 기업입니다.','상품 판매, 회원제·관련 서비스에서 매출이 발생하며 미국·해외·Sam’s Club을 구분합니다.','소비자가 매장·온라인·픽업·배달을 통해 상품을 구매합니다.','상품 조달, 재고·유통센터·배송망, 인건비와 매장·디지털 운영이 연결됩니다.'),
    'PG':('Procter & Gamble','일상 생활에 사용하는 브랜드 소비재를 생산·판매합니다.','미용·건강·세탁·가정용품·아기·여성·가족 케어 제품 판매가 사업의 기반입니다.','유통사·소매점을 통해 소비자에게 판매합니다.','외부 원재료·포장재, 일부 자체 화학 원료, 연료·운송 비용과 가격 전가 여부를 확인합니다.'),
    'COST':('Costco','회원제 창고형 매장과 온라인 유통을 운영합니다.','상품 판매와 연간 회원비가 주요 수익 원천입니다. 회원비는 회원 기간에 걸쳐 인식합니다.','회원이 식품·생활용품 등 상품과 부가 서비스를 구매합니다.','상품 조달·재고 회전·물류와 회원 갱신·매장 운영 비용을 확인합니다.'),
    'V':('Visa','발급사·매입사·가맹점 사이의 전자 결제를 연결하는 네트워크입니다. 직접 카드 발급이나 소비자 대출을 하는 은행은 아닙니다.','결제 서비스·데이터 처리·국제 거래·관련 부가 서비스 수수료에서 매출이 발생합니다. 은행 간 정산 수수료와 Visa의 매출을 구분합니다.','금융기관·결제 사업자와의 네트워크 관계를 통해 소비자·가맹점 결제를 지원합니다.','거래 처리 시스템, 보안·부정 거래 방지와 네트워크 참여·규제 조건을 확인합니다.'),
    'MA':('Mastercard','금융기관·가맹점·소비자를 연결하는 결제 네트워크와 부가 서비스를 제공합니다.','결제 네트워크 수수료와 보안·데이터·분석 등 부가 서비스에서 매출이 발생합니다.','금융기관·결제 사업자 등이 네트워크와 서비스를 사용합니다.','거래 처리·보안 기술, 참여 금융기관과 결제·개인정보 규제를 확인합니다.'),
    'LLY':('Eli Lilly','인체 의약품을 발견·개발·제조·판매하는 제약 기업입니다.','당뇨·비만 등 치료제 판매로 매출이 발생하며 공시는 단일 인체 의약품 사업 부문으로 보고합니다.','의약품 유통망과 의료기관을 통해 환자가 치료제를 사용합니다.','임상·허가·특허·보험 급여와 생산시설·품질·원료 공급을 확인합니다.'),
    'PFE':('Pfizer','혁신 의약품의 연구·개발·제조·판매와 위탁 개발·제조 사업을 운영합니다.','의약품·관련 계약 매출이 사업의 기반입니다. Biopharma는 보고 사업 부문이며 PC1 위탁 제조와 구분합니다.','의약품 유통·의료 체계를 통해 환자에게 공급합니다.','허가·특허·약가·원료·생산 역량과 제품별 독점권 만료를 확인합니다. Pfizer Ignite는 2025년 중단 결정에 따른 축소 사업입니다.'),
    'ABT':('Abbott Laboratories','의료기기·진단·영양·기존 의약품 사업을 운영하는 의료 기업입니다.','네 보고 사업 부문의 제품 판매로 매출이 발생합니다.','의료기관·진단기관·유통망과 소비자 시장을 대상으로 합니다.','원재료·부품·소모품을 외부에서 구매하며 품질·허가·생산·유통을 확인합니다.'),
    'CVX':('Chevron','원유·천연가스 생산과 정제·제품 판매 등의 상류·하류 에너지 사업을 운영합니다.','자원 생산 판매와 정제·에너지 제품 판매로 매출이 발생합니다.','에너지·산업 고객과 제품 유통망에 공급합니다.','유가·가스 가격, 생산량·정제 여건과 설비·원료·공급망·통상 조건을 확인합니다.'),
    'COP':('ConocoPhillips','원유·천연가스의 탐사·개발·생산을 수행하는 에너지 기업입니다.','생산 자원의 판매가 사업의 기반이며 공시는 지역별 운영 부문으로 나눕니다.','에너지 시장의 거래·판매망을 통해 생산 자원을 공급합니다.','자원 가격·생산량, 개발 설비·운영 비용과 지역별 허가·통상 조건을 확인합니다.'),
    'SLB':('SLB','에너지 생산 현장의 기술·장비·서비스와 디지털 솔루션을 제공합니다.','유전·가스전 관련 기술·장비·서비스 제공이 사업의 기반입니다.','자원 개발·생산 기업이 현장 운영과 데이터 관리에 사용합니다.','고객 개발 투자와 현장 운영, 장비·인력·소프트웨어 및 지역별 제재·통상 조건을 확인합니다.'),
    'BA':('Boeing','민항기, 방위·우주 시스템과 관련 정비·지원 서비스를 제공합니다.','민항기 인도, 방위·우주 계약과 Global Services에서 매출이 발생합니다.','항공사·리스사·정부·방위 고객을 대상으로 합니다.','엔진·항공 부품 공급망, 생산·품질·인증·인도 일정과 계약 조건을 확인합니다.'),
    'GE':('GE Aerospace','민항·방위 항공 엔진과 관련 서비스·시스템을 제공합니다. 과거 GE의 전력·의료 사업과 구분합니다.','항공 엔진·부품 판매와 설치 엔진의 정비·수리·서비스에서 매출이 발생합니다.','항공기 제작사·항공사·정부와 군이 사용합니다.','특수 소재·항공 부품, 엔진 생산·정비 역량과 항공기 가동·인도량을 확인합니다.'),
    'UPS':('United Parcel Service','소화물 배송과 국제 운송·공급망 서비스를 제공합니다.','미국·국제 소화물 배송과 공급망 서비스 요금에서 매출이 발생합니다.','기업·전자상거래 판매자와 개인이 운송 서비스를 이용합니다.','연료·항공기·차량·인력·허브와 배송량·운송 품목·서비스 가격을 확인합니다.'),
    'FDX':('FedEx','항공·지상 운송망을 연결해 소화물 배송과 국제 물류 서비스를 제공합니다.','운송 서비스가 이행되는 기간에 매출을 인식합니다. 2026년 6월 1일 분사된 FedEx Freight는 이후 연결 사업과 구분합니다.','기업·전자상거래와 일반 발송자가 배송·국제 물류 서비스를 이용합니다.','연료·항공기·차량·인력·외부 운송사와 물동량·서비스 구성·요금을 확인합니다.'),
    'DOW':('Dow','포장·특수 플라스틱, 산업용 중간재·인프라 소재와 기능성 소재·코팅을 제공합니다.','화학·소재 제품 판매로 매출이 발생하며 세 보고 부문을 구분합니다.','포장·건설·산업·소비자 제품 등 소재 사용 기업에 공급합니다.','화학 원료·에너지와 생산시설·수요·공급망·지역별 운영 조건을 확인합니다.'),
    'APD':('Air Products','산업용 가스와 가스 생산·분리·정제 관련 설비를 공급합니다.','가스 판매와 관련 장비·설비 사업에서 매출이 발생합니다.','화학·정유·금속·제조·의료 등 산업 고객이 가스를 사용합니다.','전력·연료·운송·저장 설비와 고객 현장 가동·장기 계약 조건을 확인합니다.'),
    'ECL':('Ecolab','물 관리·위생·기관용 세정·해충 방제·생명과학 관련 솔루션을 제공합니다.','제품·프로그램·현장 서비스 제공으로 매출이 발생합니다. 한 고객이 여러 사업 부문의 서비스를 이용할 수 있습니다.','산업·기관·식품·생명과학 등 사업장 운영 고객이 사용합니다.','원재료·기술 지원·유통과 고객의 물·에너지 관리·위생 기준을 확인합니다.'),
    'FCX':('Freeport-McMoRan','구리 중심의 자원 채굴·처리와 관련 금속 사업을 운영합니다.','금속 생산·판매가 사업의 기반입니다. 광산의 매출과 제품 시장점유율은 다릅니다.','금속 가공·산업 관련 시장으로 판매하며 구리 선재 제품도 제조합니다.','광산 품위·회수율·생산량, 금속 가격·에너지·용수·자재와 운영 허가를 확인합니다.'),
    'SO':('Southern Company','전력 판매와 천연가스 유통을 수행하는 유틸리티 그룹입니다.','전통 전력 회사의 전력 판매, Southern Power의 도매 전력과 Southern Company Gas의 가스 유통을 구분합니다.','서비스 지역 고객과 도매 전력 시장에 공급합니다.','발전·송배전·가스 설비, 연료·신뢰성·수요와 규제 비용 회수 조건을 확인합니다.'),
    'AEP':('American Electric Power','발전·송전·배전 중심의 전력 사업을 운영합니다.','전력 공급과 규제·송전 사업에서 매출이 발생합니다.','서비스 지역의 전력 수요와 유틸리티 고객을 대상으로 합니다.','발전·전력망 투자, 연료·전력 수요·금리와 규제 요금·투자 비용 회수를 확인합니다.'),
    'EQIX':('Equinix','기업 장비가 설치되는 데이터센터 공간과 기업·네트워크 사이의 상호 연결 서비스를 제공합니다.','코로케이션과 인터커넥션 등의 반복 계약 매출이 주된 기반이며 보통 월별 청구·계약 기간에 걸쳐 인식합니다.','기업·클라우드·통신망 고객이 데이터센터와 연결 서비스를 사용합니다.','전력·냉각·건물·통신 연결과 설비 용량·가동률·임대 계약을 확인합니다.'),
}
PUBLIC={symbol:profile(name,annual(symbol),business,revenue,customers=customers,inputs=inputs,
                      products=[('핵심 제공 제품·서비스',business)])
        for symbol,(name,business,revenue,customers,inputs) in READING.items()}
PUBLIC['APH']=profile('Amphenol',source('Amphenol · 공식 사업 소개','https://www.amphenol.com/about','열람 2026-10-02'),
    '전자 시스템의 커넥터·케이블·안테나·센서 등 연결 부품을 설계·제조합니다.',
    '전자 연결·센서·안테나와 관련 부품·시스템 판매가 사업의 기반입니다.',
    [('전자 연결 부품','고속·전력·광통신 커넥터와 케이블·센서·안테나')],
    '자동차·산업·통신·데이터센터·항공·방위·모바일 시장에 공급합니다.')
PUBLIC['HPE']=profile('Hewlett Packard Enterprise',source('HPE · NVIDIA 기업 AI 협력','https://www.hpe.com/us/en/newsroom/blog-post/2025/06/hpe-and-nvidia-a-partnership-driving-the-next-generation-of-ai-innovation.html','2025-06-24'),
    '기업용 서버·하이브리드 클라우드·네트워크와 관련 솔루션을 제공합니다.',
    '기업용 인프라 제품·솔루션과 관련 서비스가 사업의 기반입니다.',
    [('기업 AI 인프라','서버·네트워크·Private Cloud AI와 구축 지원')],'기업의 IT·AI 인프라 수요에 대응합니다.')

APPLE_LIST=source('Apple · FY2023 공식 공급사 목록','https://www.supplychainreports.apple/Apple-Supplier-List','2023-09-30')
TSMC_SUPPLY=source('TSMC · 2025 공급망 포상 명단','https://pr.tsmc.com/english/news/3274','2025-11-28')
TSMC_ALLIANCE=source('TSMC · 3DFabric Alliance 분야별 구성','https://www.tsmc.com/english/dedicatedFoundry/oip/3dfabric_alliance','열람 2026-10-02')
NV_SYSTEM=source('NVIDIA · RTX PRO 서버·스토리지·도입 파트너 발표','https://nvidianews.nvidia.com/news/nvidia-rtx-pro-servers-speed-trillion-dollar-enterprise-it-industry-transition-to-ai-factories','2025-05-18')
FOX_REPORT=source('Foxconn · 2025 연차보고서','https://image.honhai.com/upload/202605/financy_by_year/2025_Annual_Report_20260523_7728.pdf#page=6','2025-12-31')
PRIVATE={
    'foxconn':profile('Hon Hai Precision Industry · Foxconn',FOX_REPORT,
        '전자 제품·컴퓨팅·네트워크 시스템과 부품을 위탁 제조하는 그룹입니다. AI 서버·모듈·냉각에서 서버 랙 통합까지 제공합니다.',
        '고객 제품의 제조·시스템 공급이 사업의 기반입니다. 2025년 매출 구성은 클라우드·네트워크 40%, 스마트 소비자 전자제품 38%, 컴퓨팅 15%, 부품·기타 7%입니다.',
        [('클라우드·네트워크','AI 서버·모듈·서버 랙 및 관련 시스템'),('전자 제조','소비자 전자기기·컴퓨터와 부품')],
        '전자기기·클라우드 시스템 기업이 제조·시스템 통합을 위탁합니다.',
        '반도체 칩·고속 커넥터·정밀 기계 부품과 글로벌 제조·조립·물류망이 연결됩니다.'),
    'wistron':profile('Wistron',source('Wistron · 공식 제품·서비스 분야','https://www.wistron.com/en','열람 2026-10-02'),
        '기업용·네트워크, 개인 컴퓨팅, 디스플레이·자동차 콕핏·산업 관련 전자 제품과 서비스를 제공합니다.',
        '전자 제품·관련 기술 서비스 사업을 운영합니다. 발표된 미국 AI 서버 공장 계획은 실제 매출과 구분합니다.',
        [('기업·네트워크','기업용·네트워크 시스템'),('컴퓨팅·서비스','개인 컴퓨팅·산업 제품과 유지보수·재활용')]),
    'cargill':profile('Cargill',source('Cargill · 공식 사업 구조','https://www.cargill.com/about/cargill-at-a-glance','열람 2026-10-02'),
        '농산물 조달·거래·가공·물류와 단백질·식품 원료·사료·바이오 기반 산업 제품을 제공합니다.',
        '식품·원료·농업·산업 제품 판매와 거래·물류·관련 서비스가 사업의 기반입니다.',
        [('식품·원료','육류·단백질·유지·전분·코코아·감미료'),('농업·거래','곡물·유지 종자 조달·가공·유통과 사료')],
        '식품 제조·외식·유통 고객과 농민·축산업·산업 고객에 제공합니다.',
        '농산물·축산물 조달, 저장·가공·운송과 원자재 가격·공급 조건이 연결됩니다.'),
    'mccain':profile('McCain',source('McCain · 공식 사업·브랜드','https://www.mccain.com/about-us/our-business-brands/','열람 2026-10-02'),
        '냉동 감자·감자 가공품과 애피타이저·편의 식품을 생산하는 식품 기업입니다.',
        '외식·급식용 제품과 소매 유통용 냉동·냉장 식품 판매가 사업의 기반입니다.',
        [('감자 가공 식품','감자튀김·감자 가공품·냉동 스낵')],'외식·식품 서비스와 슈퍼마켓 등 소매 채널에 판매합니다.'),
}

# The alliance describes the exact role; this does not imply a purchase contract.
ALLIANCE_ROWS=[
    ('Cadence','CDNS',None,'EDA 도구·IP·검사'),('Keysight','KEYS',None,'EDA·검사'),
    ('Siemens EDA',None,'siemens-eda','EDA·검사'),('Synopsys','SNPS',None,'EDA·IP·검사'),
    ('Alphawave',None,'alphawave','반도체 IP'),('Arm','ARM',None,'반도체 IP'),
    ('proteanTecs',None,'proteantecs','반도체 IP'),('Silicon Creations',None,'silicon-creations','반도체 IP'),
    ('Alchip',None,'alchip','설계·가치사슬'),('Global Unichip',None,'global-unichip','설계·가치사슬'),
    ('IC-Link by imec',None,'imec-ic-link','설계·가치사슬'),
    ('Micron','MU',None,'메모리'),('Samsung Electronics','005930.KS',None,'메모리'),('SK hynix','000660.KS',None,'메모리'),
    ('ASE Group','ASX',None,'패키징·검사 OSAT'),('SPIL',None,'spil','패키징·검사 OSAT'),
    ('STATSChipPAC',None,'stats-chippac','패키징·검사 OSAT'),('Amkor','AMKR',None,'패키징·검사 OSAT'),
    ('IBIDEN',None,'ibiden','패키징 기판'),('Kinsus',None,'kinsus','패키징 기판'),
    ('Toppan',None,'toppan','패키징 기판'),('Unimicron',None,'unimicron','패키징 기판'),
    ('Advantest',None,'advantest','반도체 검사'),('Teradyne','TER',None,'반도체 검사')]
for name,symbol,key,role in ALLIANCE_ROWS:
    item=profile(name,TSMC_ALLIANCE,'TSMC 첨단 패키징·3D IC 설계 생태계에서 '+role+' 역할로 등록된 기업입니다.',
                 '이 자료는 '+role+' 분야의 협력 참여를 확인합니다. 기업 전체 매출·고객 거래액은 별도 공시 범위입니다.',
                 [(role,'3DFabric Alliance 공식 분야별 참여 목록')])
    if key and key not in PRIVATE:PRIVATE[key]=item
    elif symbol and symbol not in PUBLIC and symbol not in {'MU','005930.KS','000660.KS'}:PUBLIC[symbol]=item

# Supplier-list facts have historical scope and make no product-specific guess.
APPLE_ROWS=[('3M','MMM',None),('ASE Technology Holding','ASX',None),('Amkor','AMKR',None),
 ('Amphenol','APH',None),('Analog Devices','ADI',None),('Broadcom','AVGO',None),
 ('Cirrus Logic','CRUS',None),('Coherent','COHR',None),('Corning','GLW',None),('Diodes','DIOD',None),
 ('Flex','FLEX',None),('Foxconn',None,'foxconn'),('Intel','INTC',None),('Jabil','JBL',None),
 ('LG Display','LPL',None),('Lumentum','LITE',None),('Microchip Technology','MCHP',None),
 ('Micron','MU',None),('NXP','NXPI',None),('ON Semiconductor','ON',None),('Power Integrations','POWI',None),
 ('Qorvo','QRVO',None),('Qualcomm','QCOM',None),('Samsung Electronics','005930.KS',None),
 ('SK hynix','000660.KS',None),('Skyworks','SWKS',None),('Sony','SONY',None),
 ('STMicroelectronics','STM',None),('Synaptics','SYNA',None),('TSMC','TSM',None),
 ('Texas Instruments','TXN',None),('Trinseo','TSE',None),('Viavi','VIAV',None),('Western Digital','WDC',None),('Wistron',None,'wistron')]
EDGES={
    'AAPL':[relation(name,ticker,'supplier','FY2023 Apple 공식 공급사 목록 등재 · 당시 직접 소재·제조·조립 지출 범위의 목록이며 현재 계약·제품·공급액은 추정하지 않음',APPLE_LIST,key) for name,ticker,key in APPLE_ROWS],
    'TSM':[relation(name,ticker,'partner',role+' · 3DFabric Alliance 참여 · 협력 생태계 구성원이며 직접 발주·독점 공급 계약을 뜻하지 않음',TSMC_ALLIANCE,key) for name,ticker,key,role in ALLIANCE_ROWS],
    'NVDA':[relation(name,ticker,'partner',role+' · 2025 발표 당시 제공 계획·파트너 목록이며 납품 매출을 뜻하지 않음',NV_SYSTEM,key) for name,ticker,key,role in [
        ('Cisco','CSCO',None,'RTX PRO 서버·기업 AI 시스템'),('Dell','DELL',None,'RTX PRO 서버·스토리지'),
        ('Hewlett Packard Enterprise','HPE',None,'RTX PRO 서버·스토리지'),('IBM','IBM',None,'인증 스토리지'),
        ('NetApp','NTAP',None,'인증 스토리지'),('Nutanix','NTNX',None,'인증 스토리지'),('Pure Storage','PSTG',None,'인증 스토리지'),
        ('Accenture','ACN',None,'기업 AI 인프라 도입·컨설팅'),('Infosys','INFY',None,'기업 AI 인프라 도입·컨설팅'),
        ('Wipro','WIT',None,'기업 AI 인프라 도입·컨설팅'),('Supermicro','SMCI',None,'RTX PRO 서버'),
        ('Foxconn',None,'foxconn','RTX PRO 서버'),('Wistron',None,'wistron','RTX PRO 서버')]],
    'KO':[],
}
# Coca-Cola's official list distinguishes bottlers from the parent FEMSA issuer.
KO_REPORT=source('Coca-Cola · 2025 연차 공시','https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm','2026-02-20')
PUBLIC['KO']=profile('Coca-Cola',KO_REPORT,'음료 브랜드와 농축액·시럽, 완제품 음료 사업을 운영합니다.',
    '보틀러 등에 농축액·시럽을 판매하고 완제품도 판매합니다. 2025년 매출 기준 농축액 사업 59%, 완제품 41%이며 판매량 비중과 다릅니다.',
    [('농축액·시럽','허가된 보틀러가 물·감미료를 더해 음료를 제조·포장'),('완제품 음료','자체·유통망·리테일을 통한 완제품 판매')],
    '보틀러·유통사·소매 채널을 통해 소비자가 구매합니다. 보틀러의 전체 매출은 본사의 매출과 다릅니다.')
for name,ticker,key in [('Coca-Cola FEMSA',None,'coca-cola-femsa'),('Coca-Cola Europacific Partners','CCEP',None),
                      ('Coca-Cola HBC',None,'coca-cola-hbc'),('Arca Continental',None,'arca-continental'),('Swire Coca-Cola',None,'swire-coca-cola')]:
    EDGES['KO'].append(relation(name,ticker,'customer','2025 공시의 주요 보틀러 · 허가 지역에서 음료 제조·포장·유통을 수행하며 전체 소비자 매출은 Coca-Cola 본사 매출과 구분',KO_REPORT,key))
    item=profile(name,KO_REPORT,'Coca-Cola 공시의 주요 보틀러로, 해당 허가 지역에서 음료 제조·포장·유통을 수행합니다.',
                 '음료 완제품의 지역 판매·유통 사업이며 Coca-Cola 본사의 농축액 사업과 구분합니다.',
                 [('음료 제조·유통','공시에서 확인된 보틀러 운영 역할')])
    if key:PRIVATE[key]=item
    else:PUBLIC[ticker]=item

SUPPLIER_READING=[
 ('disco','DISCO','https://www.disco.co.jp/eg/technology/index.html','웨이퍼 절단·박막화·연마 장비와 블레이드·휠 등 가공 소모품을 제공합니다.','정밀 가공 장비·도구·공정 응용 솔루션 판매가 사업의 기반입니다.'),
 ('ebara','EBARA','https://www.ebara.com/global-en/precision/','반도체용 CMP 평탄화 장비, 진공 펌프와 배기가스 처리 시스템 등을 제공합니다.','반도체 제조용 장비와 관련 지원·서비스 사업입니다. EBARA의 전체 펌프 사업과 구분한 정밀 기계 분야입니다.'),
 ('kokusai-electric','KOKUSAI ELECTRIC','https://www.kokusai-electric.com/en/','반도체 박막 증착과 막 특성을 개선하는 처리 공정 장비를 제공합니다.','증착·처리 장비 공급과 관련 서비스가 사업의 기반입니다.'),
 ('sumco','SUMCO','https://www.sumcosi.com/english/products/lineup.html','반도체 회로를 만드는 기반 재료인 실리콘 웨이퍼를 제조합니다.','연마·에피택셜 웨이퍼 등 반도체용 웨이퍼 제품을 공급합니다.'),
 ('jsr','JSR','https://jsr.co.jp/jsr_e/products/em/','반도체 노광용 포토레지스트·다층 소재와 공정·첨단 패키징 소재를 제공합니다.','이 페이지는 전자 소재 공급 분야를 정리하며 다른 사업과 기업 전체 매출은 구분합니다.'),
 ('advantest','Advantest','https://www.advantest.com/en/about/business/','웨이퍼 공정 말미와 패키징 이후 칩의 동작·전기 특성을 확인하는 반도체 검사 장비를 제공합니다.','반도체 자동 검사 장비·관련 솔루션을 공급합니다.'),
 ('screen','SCREEN Semiconductor Solutions','https://www.screen.co.jp/spe/en/products','웨이퍼 세정 등 반도체 제조 공정 장비를 제공합니다.','반도체 공정 장비 공급 사업을 정리하며 SCREEN 그룹의 다른 사업과 구분합니다.'),
]
for key,name,url,business,revenue in SUPPLIER_READING:
    origin=source(name+' · 공식 반도체 제품·사업 소개',url,'열람 2026-10-02')
    PRIVATE[key]=profile(name,origin,business,revenue,[("업계에서 제공하는 제품",business)],'반도체 제조·검사 관련 기업이 사용하는 장비·소재 분야입니다.')
    EDGES['TSM'].append(relation(name,None,'supplier','2025 TSMC 공식 공급망 포상 명단 등재 · 계약액·독점 여부·개별 공정 납품 범위는 명단만으로 추정하지 않음',TSMC_SUPPLY,key))
EDGES['TSM'].append(relation('Canon',None,'supplier','2025 TSMC 공식 공급망 포상 명단 등재 · 장비별 주문액과 제품별 납품 범위는 추정하지 않음',TSMC_SUPPLY,'canon'))
EDGES['GE']=[relation('Boeing','BA','customer','2025 GE Aerospace 공시의 일부 Boeing 기종에 공급되는 엔진 · 기종에 따른 선택·단독 공급 차이를 유지하며 Boeing 전체 엔진으로 확대하지 않음',annual('GE'))]

PRODUCTS={
 'ADI':[('신호 변환·전력·RF','데이터 변환기·증폭기·전력관리·RF IC와 신호처리 제품')],
 'TXN':[('아날로그','전력관리·신호 체인 반도체'),('임베디드 처리','기기의 제어·연산용 프로세서')],
 'GLW':[('광통신','광섬유·케이블·광 연결 제품'),('유리·소재','디스플레이·기기·자동차·생명과학용 소재')],
 'AMKR':[('첨단 패키징','플립칩·메모리·웨이퍼 수준 가공과 검사'),('일반 패키징','와이어본드·전력 소자 패키징과 검사')],
 'LITE':[('광통신','광신호 전송·증폭·경로 제어용 부품·모듈'),('레이저','관련 레이저·광학 제품')],
 'COHR':[('광통신','데이터센터·통신망용 광부품·트랜시버'),('산업 광전자','레이저·광학 소재와 관련 부품')],
 'QRVO':[('RF·연결','무선 송수신용 반도체·모듈')],
 'NXPI':[('처리·제어','프로세서·마이크로컨트롤러'),('연결·보안','전자 시스템의 연결·보안·아날로그 반도체')],
 'JBL':[('설계·제조','전자·기계 설계, 제조·조립·검사'),('공급망','고객별 조달·생산·물류 운영')],
 'FLEX':[('제조 서비스','전자 기판·시스템 조립과 설계·조달'),('중요 인프라','데이터센터 전력·냉각·랙 수준 시스템')],
 'DELL':[('기업 인프라','서버·스토리지·네트워크와 관련 지원'),('클라이언트','PC·주변기기와 관련 서비스')],
 'CSCO':[('네트워크','스위치·라우터·무선·서버·광 연결'),('소프트웨어·지원','보안·협업·관리와 관련 서비스')],
 'META':[('앱·광고','Facebook·Instagram 등 앱과 광고 상품'),('Reality Labs','AR·VR 관련 제품·기술')],
 'NFLX':[('엔터테인먼트','시리즈·영화·게임·라이브 프로그램'),('요금제','일반·광고 포함 구독 서비스')],
 'WMT':[('소매·전자상거래','매장·온라인·픽업·배달을 통한 상품 판매'),('회원제','Sam’s Club 운영')],
 'PG':[('일상 소비재','미용·건강·세탁·가정·아기·여성·가족 케어 브랜드 제품')],
 'COST':[('회원제 상품 판매','창고형 매장·온라인 상품과 관련 부가 서비스')],
 'V':[('결제 네트워크','거래 승인·청산·정산과 국제 결제'),('부가 서비스','보안·토큰·데이터와 관련 결제 솔루션')],
 'MA':[('결제 네트워크','전자 결제 연결·처리'),('부가 서비스','보안·데이터·분석 등 관련 솔루션')],
 'LLY':[('인체 의약품','당뇨병·비만 등 치료 분야의 의약품')],
 'PFE':[('Biopharma','혁신 의약품 연구·개발·판매'),('PC1','위탁 개발·제조와 전문 원료 의약품')],
 'ABT':[('기기·진단','의료기기·진단 제품'),('영양·의약품','영양 제품·기존 의약품')],
 'CVX':[('상류','원유·천연가스 탐사·생산'),('하류','정제·에너지 제품 판매 등')],
 'COP':[('자원 생산','원유·천연가스 탐사·개발·생산')],
 'SLB':[('현장 기술·서비스','자원 개발·생산용 기술·장비·서비스'),('디지털','현장 데이터와 운영용 솔루션')],
 'BA':[('항공·방위·우주','민항기와 방위·우주 시스템'),('서비스','정비·부품·운영 지원')],
 'GE':[('항공 엔진','민항·방위 항공 엔진·시스템'),('서비스','엔진 정비·수리·부품·관련 지원')],
 'UPS':[('소화물','미국·국제 배송'),('공급망','국제 운송·통관 등 관련 서비스')],
 'FDX':[('운송·물류','항공·지상 소화물 배송과 국제 물류')],
 'DOW':[('포장·특수 플라스틱','포장·소재 제품'),('산업·기능성 소재','산업용 중간재·인프라·기능성 소재·코팅')],
 'APD':[('산업 가스','산업용 가스와 관련 공급'),('장비','공기 분리·가스 정제·저온 저장·운송 설비')],
 'ECL':[('물·위생','물 관리·기관용 세정·위생 프로그램'),('전문 서비스','해충 방제·생명과학 관련 솔루션')],
 'FCX':[('금속','구리 중심 금속 생산·판매와 구리 선재')],
 'SO':[('전력','규제 전력·도매 전력'),('가스','천연가스 유통')],
 'AEP':[('전력망·공급','발전·송전·배전')],
 'EQIX':[('코로케이션','데이터센터 공간·전력 등 장비 설치 서비스'),('인터커넥션','기업·네트워크 간 연결 서비스')],
}
for symbol,rows in PRODUCTS.items():
    PUBLIC[symbol]['products']=[dict(title=title,detail=detail,source=annual(symbol)) for title,detail in rows]

CHRN_REPORT=source('ChronoScale · FY2026 연차 공시',
    'https://www.sec.gov/Archives/edgar/data/1549084/000162828026058018/chrn-20260531.htm','2026-08-19')
PUBLIC['CHRN']=profile('ChronoScale Holdings Corporation',CHRN_REPORT,
    'GPU 장비를 데이터센터에 배치해 AI·머신러닝 등의 연산 용량을 제공하는 클라우드 기업입니다. 과거 Ekso 외골격 사업은 매각 대상·중단 사업으로 구분합니다.',
    'GPU당 시간 기준의 고정 사용료를 월별 청구합니다. FY2026 공시에서 클라우드 사업은 전체 매출의 약 99.5%입니다. 기업 제품의 시장점유율은 아닙니다.',
    [('GPU 연산 용량','전용 GPU 인프라를 이용하는 클라우드 연산 서비스')],
    '2026년 5월 31일 기준 클라우드 고객은 Together AI 한 곳입니다. 같은 연차 공시는 이후 체결한 Microsoft의 2년 GPU 서비스 계약도 설명합니다. 계약 체결과 장비 인도·실제 매출은 구분합니다.',
    'NVIDIA GPU 공급과 제3자 데이터센터의 공간·전력 및 장비 금융이 필요합니다. 공시에 있는 AMD 활용 계획은 현재 공급 거래와 구분합니다.',
    '공시에서 CoreWeave·Crusoe·Lambda Labs·Nebius Group을 AI 클라우드 경쟁사로 명시합니다. Nutanix와의 2026년 8월 협력 발표는 최종 계약·구현이 예정된 체계로 설명합니다.')
PRIVATE['together-ai']=profile('Together AI',source('Together AI · 공식 플랫폼·서비스',
    'https://www.together.ai/','열람 2026-10-02'),
    'AI 모델 추론·GPU 컴퓨팅·모델 훈련을 위한 클라우드 플랫폼을 제공합니다.',
    '모델 추론·컴퓨팅·전용 인프라·훈련 서비스를 제공합니다. 공개된 제품·과금 방식의 범위이며 전체 기업 매출은 확인하지 않았습니다.',
    [('모델 추론','서버리스·배치·전용 모델 추론'),('컴퓨팅·훈련','GPU 클러스터와 모델 훈련·미세 조정')],
    'AI 애플리케이션을 개발·운영하는 개발자와 기업을 대상으로 합니다.')
EDGES['CHRN']=[
    relation('NVIDIA','NVDA','supplier','2026년 5월말 공시의 주요 GPU 공급사 · GPU 제품 사용을 NVIDIA에 판매한다는 주장으로 바꾸지 않음',CHRN_REPORT),
    relation('Together AI',None,'customer','2026년 5월말 클라우드 사업의 단일 고객 · GPU당 시간 요금의 연산 용량 계약',CHRN_REPORT,'together-ai'),
    relation('Microsoft','MSFT','customer','연차 공시에서 최근 체결한 2년 GPU 서비스 계약 · GB300 클러스터의 일정별 인도 의무이며 완료 매출을 뜻하지 않음',CHRN_REPORT),
    relation('Nutanix','NTNX','partner','2026년 8월 기업용 AI 인프라 공동 영업·개발·통합 체계 발표 · 최종 계약과 구현은 예정 사항',CHRN_REPORT),
    relation('CoreWeave','CRWV','competitor','공시에 명시된 AI 클라우드 서비스 경쟁사 · 상대 기업의 전체 사업을 동일하게 보지 않음',CHRN_REPORT),
    relation('Nebius Group','NBIS','competitor','공시에 명시된 AI 클라우드 서비스 경쟁사',CHRN_REPORT),
    relation('Crusoe',None,'competitor','공시에 Crusoe Energy로 명시된 AI 클라우드 서비스 경쟁사',CHRN_REPORT,'crusoe'),
    relation('Lambda Labs',None,'competitor','공시에 명시된 AI 클라우드 서비스 경쟁사 · 현재 Lambda 브랜드의 GPU 컴퓨팅 사업',CHRN_REPORT,'lambda-labs'),
]

# Product scopes come from each firm's free official site, not another issuer's
# competitor list. Published performance claims are not market-share evidence.
PUBLIC['CRWV']=profile('CoreWeave, Inc.',source('CoreWeave · 공식 플랫폼·제품',
    'https://www.coreweave.com/','열람 2026-10-02'),
    'AI 모델 훈련·추론을 위한 클라우드 연산과 스토리지·네트워크·운영 서비스를 제공합니다.',
    'GPU·CPU 연산, 스토리지, 네트워크와 관리형 인프라 서비스가 공개된 제공 범위입니다. 제품 소개만으로 전체 기업 매출 구성이나 시장점유율을 만들지 않습니다.',
    [('연산·인프라','GPU·CPU 컴퓨팅과 베어메탈 서버'),('데이터·운영','스토리지·네트워크·관리형 서비스와 AI 개발 플랫폼')],
    'AI 모델 훈련·추론을 운영하는 기업과 개발자가 대상입니다.')
PUBLIC['NBIS']=profile('Nebius Group N.V.',source('Nebius · 공식 AI 클라우드·제품',
    'https://nebius.com/','열람 2026-10-02'),
    'AI 개발자를 위한 GPU 클라우드와 훈련·추론·데이터·모델 운영 도구를 제공합니다.',
    '연산·네트워크·AI 스토리지·서버리스 및 관리형 추론 서비스를 제공합니다. 이 자료는 AI 클라우드 제품 범위이며 그룹의 전체 매출 구성을 뜻하지 않습니다.',
    [('AI 컴퓨팅','GPU 연산·네트워크·AI 스토리지'),('모델 운영','서버리스·관리형 추론·DataOps·ModelOps')],
    'AI 모델을 개발하고 서비스에 배포하는 개발자와 기업을 대상으로 합니다.')
PRIVATE['crusoe']=profile('Crusoe',source('Crusoe · 공식 사업·플랫폼',
    'https://www.crusoe.ai/','열람 2026-10-02'),
    'AI 데이터센터 인프라를 설계·구축·운영하고 AI 클라우드와 관리형 AI 서비스를 제공합니다.',
    '데이터센터 인프라, 클라우드 인프라·플랫폼 및 관리형 AI가 공개된 사업 범위입니다. 미공개 전체 매출이나 특정 고객의 구매 금액을 추정하지 않습니다.',
    [('AI 인프라','데이터센터와 에너지 연계 인프라'),('AI 클라우드','GPU 컴퓨팅·관리형 추론·서버리스 미세 조정')],
    'AI 모델 훈련·추론과 관련 데이터 작업을 운영하는 고객을 대상으로 합니다.')
PRIVATE['lambda-labs']=profile('Lambda Labs',source('Lambda · 공식 GPU 클라우드',
    'https://lambda.ai/','열람 2026-10-02'),
    'Lambda 브랜드로 AI 훈련·추론에 사용하는 GPU 인스턴스와 전용 클러스터를 제공합니다.',
    '클라우드 GPU 인스턴스·1-Click 클러스터·전용 Supercluster가 공개된 제품 범위입니다. 전체 매출·계약 금액·시장점유율은 확인하지 않았습니다.',
    [('GPU 인스턴스','실험·개발용 GPU 컴퓨팅'),('GPU 클러스터','분산 AI 작업용 클러스터와 전용 Supercluster')],
    'AI 모델을 개발·훈련하고 추론을 운영하는 고객을 대상으로 합니다.')
