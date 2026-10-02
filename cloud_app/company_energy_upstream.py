"""Edited E&P operating notes with actual counterparties and dated scope.

Production-equivalent volumes are not revenue weights. Anonymous buyers stay
anonymous, and a terminated SPA or sold business is not a current relationship.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('EOG', 'FANG', 'OXY', 'DVN', 'EQT', 'EXE', 'AR', 'RRC')
ANNUAL = {symbol: report(symbol) for symbol in SYMBOLS}
QUARTER = {symbol: report(symbol, 'quarter') for symbol in SYMBOLS}
FANG_UPDATE = source('Diamondback · 2026년 2분기 생산·현장 운영',
    'https://www.diamondbackenergy.com/news-releases/news-release-details/letter-stockholders-issued-diamondback-energy-inc-12', '2026-08-03')
MENTO = source('Morrison·TOFCO · Mento 플랫폼 건조',
    'https://morrisonenergy.com/morrison-celebrates-tofco-role-in-the-successful-construction-of-the-mento-platform/', '2024년 · 열람 2026-10-03')
STRATOS = source('1PointFive · STRATOS 설비·투입 요소·시공사',
    'https://www.1pointfive.com/projects/stratos', '열람 2026-10-03')
BAIN = source('Occidental·1PointFive · Bain 탄소 제거 계약',
    'https://www.oxy.com/news/news-releases/1pointfive-and-bain--company-announce-agreement-for-direct-air-capture-carbon-removal-credits/', '2026-01-13')
MSFT_CDR = source('1PointFive · Microsoft 탄소 제거 계약',
    'https://www.1pointfive.com/news/1pointfive-and-microsoft-announce-agreement-for-direct-air-capture-cdr-credits', '2024-07-09')
TWIN_EAGLE = source('Expand Energy · Twin Eagle 인수 완료',
    'https://www.expandenergy.com/2026/09/16/expand-energy-and-twin-eagle-transaction-closes-combined-organization-creates-north-americas-leading-integrated-natural-gas-company/', '2026-09-16')
EXE_CREWS = source('Expand Energy · 실제 시추·완결 작업팀',
    'https://www.expandenergy.com/2026/08/26/rig-and-frac-crew-of-the-quarter-winners-2q-2026/', '2026-08-26')
EXE_LNG = source('Expand Energy · Delfin 신규 SPA·기존 계약 종료',
    'https://investors.expandenergy.com/news-releases/news-release-details/expand-energy-corporation-reports-first-quarter-2026-results', '2026-04-28')
RANGE_ETHANE = source('Range · 에탄 판매·Mariner East 원래 계약',
    'https://ir.rangeresources.com/news-releases/news-release-details/range-anchors-mariner-east-project-and-announces-new-ethane', '2012-09-26')
RANGE_UPDATE = source('Range · 2026년 7월 생산·물류 개발 자료',
    'https://ir.rangeresources.com/static-files/cd9b4c2c-f4fe-4118-9659-a4c3528b95b1', '2026-07-21')
RANGE_DRILL = source('Range · 시추 현장 공급사 안내',
    'https://www.rangeresources.com/drilling/', '발표일 미표기 · 열람 2026-10-03')
RANGE_COMPLETE = source('Range · 완결 현장 공급사 안내',
    'https://www.rangeresources.com/completions/', '발표일 미표기 · 열람 2026-10-03')
INEOS_FEED = source('INEOS Project ONE · 에탄 공급망 설명',
    'https://project-one.ineos.com/en/questions/raw-materials-production/', '열람 2026-10-03')
PUMP = source('ProPetro · 2025 고객·서비스 공시',
    'https://www.sec.gov/Archives/edgar/data/1680247/000168024726000028/pump-20251231.htm', '2026-02-19')
LBRT = source('Liberty Energy · 2025 고객 공시',
    'https://www.sec.gov/Archives/edgar/data/1694028/000169402826000006/lbrt-20251231.htm', '2026-02-02')
SAND = source('Smart Sand · 2025 실제 고객 공시',
    'https://www.sec.gov/Archives/edgar/data/1529628/000152962826000006/snd-20251231.htm', '2026-02-26')
MOMENTUM = source('Williams · Momentum 인수 완료',
    'https://www.williams.com/2026/09/03/williams-completes-acquisition-of-momentum-midstream/', '2026-09-03')

PUBLIC = {
    'EOG': profile('EOG Resources', ANNUAL['EOG'],
        '미국의 여러 shale basin과 Trinidad 등에서 원유·천연가스·NGL을 개발·생산합니다. 유정 생산품 판매뿐 아니라 집하·처리와 외부 상품을 포함한 마케팅도 합니다. 2025년 Encino 편입으로 Utica 가스·광물권 사업이 확대됐습니다.',
        '2025년 원유·콘덴세이트 125억100만, 가스 27억9,100만, NGL 23억7,600만, 집하·처리·마케팅 49억1,400만 달러입니다. 이 판매 항목 225억8,200만에 파생상품 1,300만·자산 매각 손실 3,500만·기타 7,200만을 조정한 영업매출·기타 합계는 226억3,200만입니다.',
        [('원유·콘덴세이트', 'Delaware·Eagle Ford·Bakken 등에서 생산하고 지역 배관·Gulf·Cushing·Corpus Christi 수출 시장으로 판매합니다.'),
         ('천연가스·LNG 연계', 'Utica·Dorado 등의 가스를 공급하며 일부 Corpus Christi 공급은 회사 선택에 따라 JKM 또는 Henry Hub 가격에 연결됩니다.'),
         ('NGL·집하·처리·마케팅', '가스에서 회수한 에탄·프로판 등의 판매와 물류·외부 상품 마케팅입니다. 판매액을 물류 수수료·순이익과 혼동하지 않습니다.')],
        customers='미국 정유사·마케터·가스 구매자가 판매 경로입니다. 2025년 판매 기준 10% 이상인 정유사 두 곳의 이름은 공개하지 않았습니다. Trinidad 가스는 National Gas Company 계열, 원유는 Heritage Petroleum·bpTT에 판매합니다.',
        inputs='광물권·시추·수압파쇄·모래·물·케이싱·연료·인력·집하·처리·배관 용량이 필요합니다. 생산지 가격과 수송 후 판매지 가격, 원유와 가스의 서로 다른 가격 노출을 구별합니다.',
        competition='생산 면적·현장 서비스·배관 반출·상품 판매 시장을 경쟁합니다. 생산량이나 6 Mcf=1 boe 환산은 제품 매출 비중·시장 점유율이 아닙니다.'),
    'FANG': profile('Diamondback Energy', ANNUAL['FANG'],
        'Permian Basin의 Midland·Delaware에서 원유·수반가스·NGL을 생산하는 기업입니다. 운영 유정의 개발 사업과 Viper의 광물권·로열티 사업을 연결하며, 매입 원유의 재판매도 합니다.',
        '2025년 자체 생산품 판매 134억5,300만 달러는 원유 116억2,100만·가스 4억·NGL 14억3,200만입니다. 매입 원유 재판매 14억7,600만과 기타 영업수익 9,700만을 포함한 매출은 150억2,600만입니다. 재판매 원유 원가 14억7,400만은 판매액과 별도이며 파생상품 손익은 매출 밖에 있습니다.',
        [('원유 개발·생산', '장거리 수평정 시추·완결·인공 채유·물 관리로 Midland·Delaware 자산을 개발합니다.'),
         ('수반가스·NGL', '원유와 함께 생산한 가스를 처리·수송합니다. Waha 반출 병목·가스 처분 조건이 원유 유정의 가동에도 연결됩니다.'),
         ('Viper 광물권·로열티', '유정을 직접 운영하는 생산자 사업과 개발 비용을 직접 부담하지 않는 광물권 수익을 구별합니다.')],
        customers='2025년 주요 구매자는 Medallion Midstream 16%, Shell Trading (USA) 13%, Enterprise Crude Oil 12%, Vitol 11%입니다. 이 회사별 매출 집중도를 Permian 시장 점유율로 사용하지 않습니다.',
        inputs='시추·완결 장비·모래·약품·물·케이싱·현장 연료와 가스 반출 용량이 필요합니다. 원유 시세·Midland/Houston 차이, 재판매 원가, 현장 운영비와 신규 유정 투자를 따로 확인합니다.',
        competition='Permian 생산 면적·인력·현장 서비스·반출 경로를 두고 경쟁합니다. 현재 생산자와 인수된 Endeavor·Double Eagle을 독립된 상장 경쟁사로 중복 세지 않습니다.'),
    'OXY': profile('Occidental Petroleum', QUARTER['OXY'],
        '미국·중동·북아프리카 등의 원유·가스 생산과 중류·마케팅, CO₂ 활용·저장을 수행합니다. OxyChem은 2026년 1월 Berkshire Hathaway에 매각됐으며 현재 사업 개요에서 자체 화학 부문으로 유지하지 않습니다.',
        '2025년 계속사업 매출은 215억9,300만 달러입니다. 탐사·생산 209억200만과 중류·판매 12억7,900만에서 내부거래 5억8,800만을 제거합니다. 고객 계약 매출 215억6,900만과 기타 매출 2,400만을 구별하고, 중단사업 OxyChem 매출 43억6,800만은 여기에 더하지 않습니다.',
        [('원유·가스 생산', 'Permian의 shale·CO₂ EOR, Rockies·Gulf와 Oman·UAE·Qatar·Algeria 등에서 생산합니다.'),
         ('중류·전력·마케팅', '원유·가스·NGL의 집하·수송·저장·판매와 CO₂ 및 전력 자산입니다.'),
         ('탄소 제거·저장', '1PointFive는 탄소 제거 크레딧·저장 사업을 개발합니다. Carbon Engineering 기술·Worley 시공과 실제 판매 계약을 구별합니다.')],
        customers='원유·가스·NGL 구매자와 탄소 제거 크레딧 구매자는 다른 고객입니다. Bain·Microsoft 계약은 1PointFive의 STRATOS 크레딧이며 OXY 전체 원유 판매량으로 표시하지 않습니다.',
        inputs='시추·완결·물·전력·배관, EOR용 CO₂ 조달·순환과 저장 허가가 필요합니다. DAC는 전력·고온 열용 가스·비음용 지하수·흡수제·지중 저장에 연결됩니다.',
        competition='생산지별 원유·가스 자산·서비스·물류와 탄소 제거 계약의 조건이 각각 경쟁 범위입니다. 보상 산정용 peer 명단을 실제 납품·경쟁 관계로 전환하지 않습니다.'),
    'DVN': profile('Devon Energy', QUARTER['DVN'],
        'Delaware·Eagle Ford·Anadarko·Rockies의 원유·가스·NGL을 개발·생산하며, 2026년 5월 Coterra 합병 완료로 Marcellus 등 자산을 편입했습니다. 생산지 물·집하·처리 공동사업과 상품 마케팅도 연결됩니다.',
        '2025년 합병 전 고객 계약 매출 167억8,600만 달러는 자체 생산품 112억2,300만과 판매·중류 55억6,300만입니다. 자체 원유 89억600만·가스 8억4,200만·NGL 14억7,500만을 소계 아래에 표시합니다. 파생상품 4억200만을 포함한 영업매출은 171억8,800만이며 Coterra 전체 2025년 실적은 포함하지 않습니다.',
        [('원유·가스 개발', '생산 면적의 수평정·완결·생산 설비를 개발하고 생산물을 판매합니다.'),
         ('외부 상품 판매·중류', '자체 판매망에 외부 상품을 모아 수송·재판매합니다. 2025년 판매·중류 매출 55억6,300만과 해당 원가 56억3,500만을 구별합니다.'),
         ('물·처리 공동사업', 'WaterBridge와 생산수 처분, Catalyst와 원유 집하·가스 처리 서비스를 연결합니다. JV 이익과 JV 전체 매출은 Devon 자체 연결 매출에 더하지 않습니다.')],
        customers='정유사·가스·NGL 마케터 등의 구매자에게 판매합니다. 구체적 거래 상대와 JV 서비스 공급자를 구별하고 계약상 익명 고객을 특정 회사로 추정하지 않습니다.',
        inputs='시추·완결·물 공급·생산수 처리·집하·배관·전력·현장 인력과 광물권 비용이 필요합니다. Dow 공동개발, Catalyst의 고정 수수료와 WaterBridge 전용 계약은 각각 역할이 다릅니다.',
        competition='같은 basin의 자산·개발 서비스·판로를 경쟁합니다. Coterra는 2026년 5월 이후 별도 현재 상장 경쟁사가 아니라 편입 법인입니다.'),
    'EQT': profile('EQT', ANNUAL['EQT'],
        'Appalachia 천연가스 생산과 자체 집하·간선 수송을 연결하는 기업입니다. Upstream·Gathering·Transmission 세 부문이며, 자체 처리 시설 외에도 MarkWest·Williams Ohio Valley·Blue Racer 서비스를 이용합니다.',
        '2025년 연결 영업매출 86억4,421만1,000 달러는 생산품 판매 77억2,671만2,000·파생상품 2억9,099만4,000·배관·기타 6억2,650만5,000입니다. 부문 합계 98억9,774만3,000에서 내부거래·기타 12억5,353만2,000을 제거하며 고객 계약 매출 83억4,686만6,000과 범위가 다릅니다.',
        [('Marcellus·Utica 가스', '천연가스와 액체 성분을 생산·판매합니다. 2025년 자체 생산 판매의 가스·NGL·원유를 소계 아래에서 나눕니다.'),
         ('생산지 집하·처리', '집하·압축·물과 일부 처리망을 운영하고 외부 처리사에서 에탄·프로판 등 액체 성분을 회수합니다.'),
         ('간선 수송·MVP', '규제 수송망과 Mountain Valley Pipeline 지분·용량 계약으로 동부·남부 수요에 연결합니다.')],
        customers='마케터·유틸리티·산업 고객에 판매합니다. 2025년 판매 물량 약 49%가 Appalachia 밖으로 가지만 회사 매출 비율은 아닙니다. 배관의 용량 예약 고객과 가스를 사는 고객을 구분합니다.',
        inputs='시추·완결·모래·물·인력·압축·처리·확정 배관 용량과 규제 허가가 필요합니다. 자체 연결망의 비용과 외부 계약 비용, 지분법 JV의 요금을 구별합니다.',
        competition='Appalachia 생산 면적·서비스·가스 반출 및 지역 가격을 경쟁합니다. 자체 수직 통합과 외부 운송 구매를 같은 관계로 표시하지 않습니다.'),
    'EXE': profile('Expand Energy', ANNUAL['EXE'],
        'Haynesville·북동부/남서부 Appalachia에서 가스 중심 생산을 하고 외부 가스·NGL도 마케팅합니다. 2026년 9월 Twin Eagle 인수 완료로 판매·최적화·저장·수송 플랫폼을 편입했습니다.',
        '2025년 자체 생산품 판매 84억7,600만과 외부 상품 재판매 31억6,300만 달러입니다. 파생상품 이익 5억5,000만과 자산 매각 손실 6,500만을 조정한 매출·기타 합계는 121억2,400만입니다. Twin Eagle의 2026년 편입과 2024년 Southwestern 부분 기간을 고려해 연도 간 범위를 비교합니다.',
        [('Haynesville 건성 가스', '2025년 가스 1,095 Bcf를 생산했습니다. Gulf 가스 수요·액화 시설과 NG3 집하·처리망에 연결됩니다.'),
         ('Appalachia 가스·NGL', '북동부 가스 958 Bcf와 남서부 가스 356 Bcf·원유 590만 배럴·NGL 2,960만 배럴입니다.'),
         ('마케팅·LNG 구매', '생산·외부 가스 판매와 LNG 구매·재판매 구조를 구분합니다. Delfin 2026년 SPA는 미래 액화 LNG를 구매하는 조건부 계약입니다.')],
        customers='2025년 헤지 전 매출 11%인 구매자 한 곳은 익명입니다. 생산품의 구매자와 집하·수송·처리 서비스를 제공하는 업체는 거래 방향이 다릅니다.',
        inputs='생산 설비·시추·완결·집하·처리·배관·저장 용량이 필요합니다. NG3는 실제 서비스 공급자이며 그 CO₂ 저장 서비스는 Exxon 계열이 담당합니다.',
        competition='Haynesville·Appalachia의 가스 개발 및 수송·판매 시장을 경쟁합니다. 취소된 Gunvor·Delfin 과거 SPA를 현재 고객·공급 계약으로 표시하지 않습니다.'),
    'AR': profile('Antero Resources', ANNUAL['AR'],
        'Appalachia의 가스·NGL·콘덴세이트를 생산하고 Antero Midstream·MarkWest의 집하·처리·물 서비스와 확정 장거리 수송망으로 판매합니다. 2026년 HG 생산 자산을 편입하고 Utica 일부 자산을 매각했습니다.',
        '2025년 매출 52억7,582만3,000 달러는 가스 28억7,324만1,000·NGL 19억8,684만·원유 1억5,015만8,000·마케팅 1억2,590만·VPP 이연매출 상각 2,526만4,000·파생상품 1억1,104만9,000·기타 337만1,000입니다. 이연매출 상각과 파생상품을 실제 생산품 판매 물량으로 바꾸지 않습니다.',
        [('습성 가스·NGL', '2025년 가스 808 Bcf·에탄 2,984만2,000배럴·C3+ NGL 4,201만 배럴·원유 289만9,000배럴을 생산했습니다.'),
         ('처리·분별·판매', 'Sherwood·Smithburg 처리 및 Hopedale 분별 인프라에 연결합니다. 직접 MarkWest 시설과 AM/MarkWest JV 시설을 구별합니다.'),
         ('수송 용량 활용', 'Chicago·Gulf·Atlantic 등 다양한 시장에 가스·NGL을 운송하고 초과 예약 용량의 활용을 마케팅합니다.')],
        customers='가스·NGL 마케터·산업 고객과 수출 경로에 판매합니다. MarkWest의 과거 구매 비중을 2025년 고객 비중으로 반복하지 않고 운송사의 이름을 원료 구매자라고 추정하지 않습니다.',
        inputs='시추·완결·물과 Antero Midstream 집하·압축·물 공급, MarkWest 처리·분별 및 확정 배관 요금이 필요합니다. 예약한 용량은 실제 유정 생산량과 다른 지표입니다.',
        competition='Appalachia 습성 가스·액체 성분 회수·장거리 판매 경로가 경쟁 범위입니다. 가스 가격과 NGL 가격·성분별 회수 조건을 구별합니다.'),
    'RRC': profile('Range Resources', ANNUAL['RRC'],
        'Pennsylvania Marcellus에서 천연가스·NGL·원유를 생산하고 처리·수송·수출 경로를 통해 판매합니다. NGL의 에탄·프로판·부탄 등 성분별 판매와 가스·원유를 나눠 이해해야 합니다.',
        '2025년 자체 생산 판매 28억1,559만1,000 달러와 매입 가스 재판매·마케팅 1억7,257만3,000의 합계인 고객 계약 매출은 29억8,816만4,000입니다. 파생상품 공정가치 수익 1억2,153만5,000·기타 581만6,000을 포함한 매출·기타 수익은 31억1,551만5,000입니다. 생산 판매의 가스 17억3,020만5,000·NGL 9억7,931만3,000·원유 1억607만3,000은 같은 소계입니다.',
        [('Marcellus 생산', '천연가스와 NGL을 생산합니다. 총 생산량을 6 Mcf=1 boe로 환산할 때 제품 가치·실제 판매 단위는 별도로 유지합니다.'),
         ('에탄·수출 판로', '미국·Canada·Europe 처리·수송·화학 원료 판매 경로가 있습니다. 2012년 원래 INEOS·NOVA·ATEX 발표와 현재 공시를 구분합니다.'),
         ('외부 가스 마케팅', '자체 생산품 판매와 외부 가스 구매·재판매·마케팅 수익을 분리합니다.')],
        customers='제품 가격·신용·신뢰성에 따라 구매자를 선택합니다. 2025년 10% 고객 A의 이름은 공시상 익명이므로 INEOS라고 단정하지 않습니다. INEOS 공식 공급망 자료의 실명 관계와 익명 집중도는 별도입니다.',
        inputs='시추·완결·물·모래·임차 설비, 가스 처리·장거리 수송·분별·수출 시설을 이용합니다. 공시 판매가격의 물류 차감 전후를 구별합니다.',
        competition='Marcellus의 면적·현장 서비스·물류 접근과 상품 판로를 경쟁합니다. 보상용 peer 또는 일반 산업 명단을 실제 공급·판매 계약으로 바꾸지 않습니다.'),
}

OPERATIONS = {
    'EOG': [
        ('보유 자산·생산량', '2025년 말 순확인 매장량 55억1,400만 boe, 미국 약 99%·Trinidad 약 1%입니다. 연 생산은 4억4,980만 boe이며 원유·콘덴세이트 1억9,050만 배럴·가스 924 Bcf·NGL 1억520만 배럴입니다. 6 Mcf=1 boe는 에너지 환산이며 가격 환산이 아닙니다.', ANNUAL['EOG']),
        ('개발 면적·지역', 'Delaware 약 395,000 net acres·Eagle Ford 약 565,000·Dorado 약 160,000입니다. Utica play 약 110만 net acres에는 net mineral 135,000이 포함됩니다. 공시의 전체 Appalachian 면적 173만6,000과 Utica play 면적은 범위가 다릅니다.', ANNUAL['EOG']),
        ('Encino 취득 범위', '2025년 8월 1일 Encino 취득을 완료했습니다. 순부채 등을 포함한 약 57억 달러와 취득 현금·인수 채무는 서로 다른 수치입니다. 취득 후 실제 실적과 1월 1일부터 합친 pro forma를 구분합니다.', QUARTER['EOG']),
        ('판매·가격·약정', '가스는 판매지 spot/index 가격을 사용하며 일부 LNG 연계 판매에서 JKM/Henry Hub를 선택합니다. 2026년 원유 고정 인도 약정 2,400만 배럴·가스 573 Bcf는 계약량이며 이미 생산·판매한 실적이 아닙니다.', ANNUAL['EOG']),
        ('유정 운영 비용', '2025년 boe당 lease operating 3.72달러·집하/처리/수송 4.74·G&A 1.82입니다. 감가·고갈 9.34 및 기타 감가 0.58, 순이자 0.52를 더한 선택 비용 20.72는 신규 개발 투자·모든 세금까지 포함한 손익분기 유가가 아닙니다.', ANNUAL['EOG']),
        ('Trinidad 현재 개발', '2025년 연차보고서는 Mento의 실제 개발 3개·탐사 1개 유정 완결과 별도 Coconut 설계·건설을 확인합니다. Mento 생산과 Coconut 개발 계획은 다른 프로젝트입니다.', ANNUAL['EOG']),
        ('Trinidad 플랫폼 공급', 'EOG/bpTT 공동 개발 Mento에서 TOFCO가 플랫폼을 건조했습니다. 건조 완료와 설치·시운전·첫 가스는 다른 단계입니다. 공급사 페이지의 2024년 게시일과 본문 행사 날짜가 불일치해 이를 첫 가스 날짜의 근거로 사용하지 않습니다.', MENTO),
    ],
    'FANG': [
        ('생산 규모·지분 기준', '2025년 순생산은 3억3,617만8,000 boe·일평균 921,036 boe이며 원유 1억8,146만2,000 배럴·가스 447.855 Bcf·NGL 8,007만3,000 배럴입니다. 운영하는 면적 약 97%와 평균 working interest 약 79%는 다른 분모입니다.', ANNUAL['FANG']),
        ('현장 비용·수익 범위', '2025년 boe당 LOE 5.55달러·집하/처리/수송 1.53·현금 G&A 0.62·생산/재산세 2.53의 합계 10.23은 현금 운영 비용입니다. DD&A 14.99와 신규 유정 투자·금융 비용을 별도로 확인하며 이 합계를 유가 손익분기점으로 쓰지 않습니다.', ANNUAL['FANG']),
        ('2026년 2분기 실제 운영', '원유 일평균 약 525,000배럴·전체 약 101만8,000 boe입니다. LOE 5.96달러/boe·현금 G&A 0.52·총 현금 운영 비용 10.96입니다. 분기 비용을 2025년 연간 비용과 같은 기준일로 표시하지 않습니다.', FANG_UPDATE),
        ('가스 반출·완결 효율', '2분기 헤지 전 가스 실현가격은 −2.15달러/Mcf였습니다. Waha 가격·배관 정비·반출 제한은 수반가스 처분과 원유 감산에도 연결됩니다. 연속 펌핑 평균 21.3시간/일·완결 길이 약 4,700 ft/일은 물량·유정 생산량과 다른 운영 지표입니다.', FANG_UPDATE),
        ('Viper·WTG 변경', 'Viper의 Sitio 취득과 지주 구조 변경 뒤 2026년 2월 9일 비Permian 광물권을 GRP/Warwick 계열에 매각했습니다. Remuda JV 25%는 WTG Midstream을 2024년 ET에 매각한 잔여 지분으로 현재 WTG 운영 자회사를 의미하지 않습니다.', QUARTER['FANG']),
    ],
    'OXY': [
        ('지속 사업·중단 사업', 'OxyChem은 2026년 1월 2일 매각 완료됐습니다. 조정된 매각대금 약 95억 달러와 당초 약 97억 발표를 구별합니다. 일부 과거 환경 부채·보상 책임이 남는다고 화학 생산 사업이 계속 OXY 소유인 것은 아닙니다.', QUARTER['OXY']),
        ('탐사·생산 판매 범위', '2025년 원유 171억7,400만·NGL 22억4,900만·가스 13억6,900만·기타 1억1,000만 달러의 합계는 탐사·생산 209억200만입니다. 중류와 내부거래 제거를 포함한 회사 전체 매출과 분모가 다릅니다.', ANNUAL['OXY']),
        ('중동 가스·NGL', 'Dolphin upstream 지분 24.5%의 권리는 2032년 중반까지이며 2025년 순생산 약 40,000 boe/d입니다. UAE Shah/Al Hosn 40% 권리는 2041년까지이고 순가스 약 283 MMcf/d·NGL/콘덴세이트 약 42,000배럴/일입니다.', ANNUAL['OXY']),
        ('Dolphin 수송', 'Qatar–UAE/Oman 230마일 가스망의 설계 용량 3.2 Bcf/d와 통상 약 2.0 Bcf/d·여름 약 2.2 Bcf/d 실수송을 구별합니다. upstream 지분·수송 지분·배관 전체 용량을 중복 합산하지 않습니다.', ANNUAL['OXY']),
        ('STRATOS 개발 단계', '2026년 제출 연차보고서의 첫 250,000톤/년과 추가 250,000톤/년 계획을 완전 상업 가동 실적으로 표시하지 않습니다. BlackRock 개발 JV는 연결 대상이며 2025년 말 투자액 5억 달러와 총 약정 5억5,000만 달러를 구별합니다.', ANNUAL['OXY']),
        ('Bain 크레딧 계약', '2026년 1월 발표의 Bain 구매는 STRATOS 크레딧 9,000톤·3년입니다. 발표 당시 start-up 진행 중이며 계약 체결 물량은 이미 검증·발행된 크레딧이나 현재 연간 설비 생산량이 아닙니다.', BAIN),
        ('DAC 투입 요소', '공기 중 CO₂를 액체 흡수제로 포집하고 calciner 열에 가스·설비에 전력을 씁니다. 비음용 염수는 처리·재사용하며 포집 CO₂를 Class VI 저장정에 주입합니다. 설계 500,000톤/년과 실제 제거량·발행 크레딧은 다릅니다.', STRATOS),
    ],
    'DVN': [
        ('합병 후 현재 범위', 'Coterra 합병은 2026년 5월 7일 완료됐고 각 Coterra 주식은 Devon 0.70주로 전환됐습니다. Devon이 회계상 취득자이며 이전 Coterra의 연간 생산·매출을 Devon 2025년 표에 더하지 않습니다.', QUARTER['DVN']),
        ('자체 생산·외부 판매', '자체 생산 판매는 원유 89억600만·가스 8억4,200만·NGL 14억7,500만입니다. 외부 판매·중류의 원유 35억8,000만·가스 10억1,000만·NGL 9억7,300만은 다른 판매 경로로 각 소계 아래에서 표시합니다.', ANNUAL['DVN']),
        ('WaterBridge 물 처분', 'Delaware/Eagle Ford의 생산수 집하·처분 전용 계약은 2038년까지입니다. 2023년 JV 30%와 2025년 기업 결합·IPO 후 WaterBridge 약 14%는 다른 법인·시점이며 현재 지분처럼 혼용하지 않습니다.', ANNUAL['DVN']),
        ('Catalyst 처리·집하', 'Howard Energy Partners 계열과 각 50%로 Stateline 인프라를 보유하고 HEP가 운영합니다. 50,000 net acres 생산에 2038년까지 고정 요금 원유 집하·가스 처리 계약을 적용하며 Devon의 실제 서비스 비용은 지분 소유와 별개입니다.', ANNUAL['DVN']),
        ('공동개발·지열', 'Dow와 Anadarko 면적 공동개발의 2025년 말 2-rig program이 있습니다. Fervo 투자 2024년 1억1,700만·2025년 4분기 5,000만 달러 및 지분 약 15%는 지열 상품 구매·발전 판매 매출이 아닙니다.', ANNUAL['DVN']),
        ('종료된 JV', 'BPX와 Blackhawk 공동사업은 2025년 4월 1일 해산해 면적을 나눴습니다. 이를 현재 진행 중인 공동 개발 관계로 반복하지 않습니다.', ANNUAL['DVN']),
    ],
    'EQT': [
        ('자산·용량', '2025년 말 확인 매장량 약 28 Tcfe·생산권 약 230만 gross acres·집하/수송 배관 약 2,945마일입니다. gross 면적과 net 생산 지분은 다르며 매장량은 앞으로 모두 같은 가격에 판매될 매출이 아닙니다.', ANNUAL['EQT']),
        ('외부 처리 계약', 'MarkWest·Williams Ohio Valley·Blue Racer에서 가스를 처리하고 NGL을 회수합니다. firm 처리 약 1.0 Bcf/d 중 자체 시설 약 0.2 Bcf/d이며 계약 용량과 실제 처리량을 구별합니다.', ANNUAL['EQT']),
        ('MVP 수송 예약', '전체 확정 반출 용량 약 4.3 Bcf/d 중 MVP Mainline 약 1.29 Bcf/d는 2044년 6월 30일까지 예약했습니다. Southgate 추가 0.55 Bcf/d는 가동 후 조건이며 현재 사용 가능한 용량에 더하지 않습니다.', ANNUAL['EQT']),
        ('현재 MVP 공동사업', '2026년 6월 Mainline Series A의 상대는 NextEra·AltaGas·RGC·Vega와 EQT/Blackstone 측입니다. ConEd의 A/C 지분은 3월 30일 취득했으므로 ConEd를 현재 동일 지분의 공동 소유자로 표시하지 않습니다.', QUARTER['EQT']),
        ('공동사업 역할·내부거래', 'MVP A는 Mainline·B는 Southgate·C는 Boost이며 EQT 계열이 운영합니다. Laurel Mountain은 Williams 등과 집하·처리 자산 JV입니다. 생산자가 자체 집하·수송망에 지불한 매출을 연결 회사 밖 매출처럼 더하지 않습니다.', QUARTER['EQT']),
    ],
    'EXE': [
        ('자체 생산·매장량', '2025년 가스 2,409 Bcf·원유 590만 배럴·NGL 2,960만 배럴, 합계 2,622 Bcfe·일평균 7,183 MMcfe입니다. 확인 매장량 25,880 Bcfe는 생산·판매 완료 물량이 아닙니다.', ANNUAL['EXE']),
        ('생산·물류 비용', '2025년 Mcfe당 생산 비용 0.24달러·집하/처리/수송 0.91입니다. 제3자 상품 마케팅 매출 31억6,300만·원가 31억6,000만은 순마진·자체 생산 매출과 다릅니다. 연간 자본지출 28억5,200만은 운영 비용과 별도입니다.', ANNUAL['EXE']),
        ('NG3 실제 서비스', '35% 지분 JV NG3는 2025년 10월 1일 집하를 시작했습니다. 평균 약 900 MMcf/d·12년 집하/처리 계약의 예약과 실제 인도량을 구별합니다. Exxon 계열로 CO₂ 전달·저장은 2026년 2월 시작됐습니다.', QUARTER['EXE']),
        ('Twin Eagle 편입 후 규모', '2026년 9월 16일 인수 완료 후 완전자회사로 운영합니다. 합산 마케팅 약 14 Bcf/d·확정 수송 약 9 Bcf/d·저장 약 49 Bcf·미국/Canada 고객 1,000곳 이상은 상업 플랫폼 수치이며 자체 가스 생산량과 다릅니다.', TWIN_EAGLE),
        ('LNG 계약 교체', '4월 22일 Delfin FLNG 1과 약 115만 톤/년·20년 LNG 구매 SPA를 체결했습니다. 2031년 개시 목표·FID 조건부이고 기존 Delfin/Gunvor SPA는 종료됐습니다. 생산자 가스 판매와 미래 액화 LNG 구매를 구분합니다.', EXE_LNG),
        ('실제 현장 서비스 공급', '2026년 2분기 Haynesville의 Key 6123 workover, Pennsylvania의 Patterson 583 시추 및 NexTier 29 frac 작업팀을 회사가 직접 소개했습니다. 특정 팀의 현장 수행은 확인되지만 전체 계약액·독점 공급은 이 자료에 없습니다.', EXE_CREWS),
    ],
    'AR': [
        ('생산·회수 기준', '2025년 일평균 약 3.442 Bcfe입니다. 에탄·C3+ 성분은 별도 단위·제품이며 6 Mcf=1 boe 환산으로 제품별 가치·매출 비중을 계산하지 않습니다.', ANNUAL['AR']),
        ('현재 생산 면적 변동', 'HG Production 취득은 2026년 2월 3일 완료됐고 West Virginia 약 385,000 net acres를 포함합니다. 취득 약 28억 달러와 새 생산 실적을 2025년 연간 결과에 합쳐 표시하지 않습니다.', QUARTER['AR']),
        ('Utica 생산 자산 매각', 'Ohio 약 80,000 gross·70,000 net acres와 확인 매장량 약 600 Bcfe의 매각은 2026년 2월 23일 완료됐습니다. 조정 전 8억 달러와 수령·판매 비용 차감 약 7억6,000만은 다른 범위이며 AM의 물류 자산 매각과 별도입니다.', QUARTER['AR']),
        ('가스 처리·분별 구조', 'Sherwood 1–6은 MarkWest, 7–13 및 Smithburg는 AM/MarkWest JV 시설입니다. Hopedale 분별기 JV 지분과 처리량·수수료를 구별하며 AM이 AR에 공급하는 집하·물 서비스와도 나눕니다.', ANNUAL['AR']),
        ('확정 수송 계약', 'Columbia/TCO·Columbia Gulf·ANR·MXP/GXP는 TC Energy의 가스망입니다. Tennessee는 Kinder Morgan, Rover·Mariner East 2는 Energy Transfer, ATEX는 Enterprise로 연결합니다. Sunoco Pipeline의 NGL 운송을 Sunoco LP의 연료 유통과 혼동하지 않습니다.', ANNUAL['AR']),
        ('인력·행정의 역방향 거래', 'AR은 AM에 인력·운영·행정 서비스를 제공하고 비용을 정산하는 공급자이면서 집하·물 서비스를 구매하는 고객입니다. 단순 보유 지분만으로 이 양방향 거래를 대체하지 않습니다.', report('AM')),
    ],
    'RRC': [
        ('자산·생산', '2025년 말 lease 약 879,000 gross·769,000 net acres, 생산 가스정 1,577 gross·1,499 net입니다. 연 생산 가스 560.891967 Bcf·NGL 4,055만1,764배럴·원유 197만5,937배럴, 합계 816.058173 Bcfe입니다.', ANNUAL['RRC']),
        ('판매가격·운영비 기준', '공시 실현가격은 일부 제3자 집하·수송·처리 비용 차감 전입니다. 2025년 LOE 0.13달러/Mcfe·생산/재산세 0.04는 물류·감가·개발 투자까지 모두 포함한 비용이 아닙니다.', ANNUAL['RRC']),
        ('수송·처리 계약', '확정 배관 용량·최소 지급·처리 계약으로 제품 반출을 확보합니다. 생산자 판매물의 가액과 처리사가 수취하는 수수료, percent-of-proceeds 계약의 액체 성분 분배는 다른 수치입니다.', ANNUAL['RRC']),
        ('연간 비용의 주요 축', '2025년 집하·수송·처리·압축 비용은 12억2,332만4,000 달러로 별도 표시합니다. 외부 가스 재판매·마케팅 원가 1억8,555만4,000과 해당 판매액 1억7,257만3,000, 직접 운영 1억217만1,000을 섞어 생산품 자체 원가율로 만들지 않습니다.', ANNUAL['RRC']),
        ('물류 개발·가동 단계', '2026년 7월 자료의 추가 처리 300 MMcf/d는 commissioning, 가스 반출 250 MMcf/d·NGL 반출/수출 20,000배럴/일은 성장 대응 계획입니다. 예정 용량을 현재 실제 제품 판매 물량에 더하지 않습니다.', RANGE_UPDATE),
        ('확인한 에탄 공급망', 'INEOS의 공식 원료 설명은 Range를 미국 에탄 공급사로 명시합니다. 2012년 원래 15년 판매 계약·Mariner East·NOVA·ATEX 발표와 최신 익명 고객 집중도를 연결해 2025년 점유율을 추정하지 않습니다.', INEOS_FEED),
        ('시추의 실제 공급 역할', '공식 현장 안내는 Baker·Schlumberger의 방향성 시추와 Halliburton의 시멘팅을 명시합니다. 발표일·계약 만기는 미표기이며 현재 계약 지속 여부는 재확인 대상입니다.', RANGE_DRILL),
        ('완결의 실제 공급 역할', '공식 현장 안내는 ProFrac·CalFrac의 완결, Sandbox의 모래 물류와 Tetra의 flowback을 명시합니다. 발표일·계약 만기는 미표기이며 현재 계약 지속 여부는 재확인 대상입니다.', RANGE_COMPLETE),
    ],
}

for _symbol, _rows in OPERATIONS.items():
    PUBLIC[_symbol]['segments'] = [fact(*row) for row in _rows]
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    PUBLIC[_symbol]['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    PUBLIC[_symbol]['sources'] += [ANNUAL[_symbol], QUARTER[_symbol], *(row[2] for row in _rows)]
    for _card in PUBLIC[_symbol]['brief']:
        if _card['title'] == '매출이 생기는 구조':
            _card['source'] = ANNUAL[_symbol]
    PUBLIC[_symbol]['drivers'] = [fact('회사별 운영 변수', {
        'EOG': '미국 원유·가스·NGL의 서로 다른 판매지 가격, Corpus Christi의 JKM/Henry Hub 선택, 신규 유정 생산·Encino 편입과 원유/가스 물류·개발 비용이 연결됩니다.',
        'FANG': '원유 가격과 Midland/Houston 베이시스, Waha 수반가스 가격·반출 제한·가스 감산에 따른 원유 가동, 시추·완결 길이·일정·물·현장 비용을 나눕니다.',
        'OXY': '원유·가스 생산가격과 CO₂ EOR의 조달·순환·생산 효율, 중동 공동사업 귀속량 및 DAC 전력·열·저장·검증 비용은 각각 다른 운영 변수입니다.',
        'DVN': '생산 basin별 원유·가스·NGL 가격, 생산수 처분·Catalyst 고정 요금·새 유정 투자를 나눕니다. Coterra 편입 전후의 면적·기간·제품 구성이 달라 과거 회사 전체와 단순 비교하지 않습니다.',
        'EQT': 'Appalachia 가스 가격·외부 판매 시장의 베이시스, 처리 시 NGL 회수, 확정 수송 예약·자체 집하/수송의 내부거래 제거와 외부 요금을 구별합니다.',
        'EXE': 'Haynesville와 Appalachia 가스의 서로 다른 생산·물류 비용, NG3 가동·CO₂ 처리, 마케팅 매입/판매 스프레드와 실제 생산·재판매 물량을 나눕니다.',
        'AR': '가스 가격과 에탄/C3+ 가격·처리 회수, 집하·압축·물 비용, 확정 장거리 수송 요금·초과 용량 활용, HG 편입과 Utica 매각의 생산 범위를 확인합니다.',
        'RRC': '에탄·프로판·부탄 등 제품 구성과 실현가격, 수출/국내 판로·처리·물류 요금, 유정 완결 시점과 DUC 전환·유지/성장 투자를 구별합니다.',
        }[_symbol], ANNUAL[_symbol])]
PUBLIC['EXE']['description_source'] = TWIN_EAGLE
PUBLIC['EXE']['brief'][0]['source'] = TWIN_EAGLE
PUBLIC['AR']['description_source'] = QUARTER['AR']
PUBLIC['AR']['brief'][0]['source'] = QUARTER['AR']

EDGES = {
    'EOG': [
        relation('National Gas Company of Trinidad and Tobago', None, 'customer', '2025년 Trinidad 가스 판매 계약 2개 · NGC 및 계열사 실명 확인', ANNUAL['EOG'], 'ngc-trinidad'),
        relation('Heritage Petroleum', None, 'customer', '2025년 Trinidad 원유·콘덴세이트 실제 판매', ANNUAL['EOG'], 'heritage-petroleum'),
        relation('bp / bpTT', 'BP', 'customer', '2025년 bp Trinidad and Tobago LLC에 원유·콘덴세이트 판매', ANNUAL['EOG']),
        relation('bp / bpTT', 'BP', 'partner', 'Mento 공동 개발·별도 Coconut farmout · bpTT와 프로젝트별 역할', ANNUAL['EOG']),
        relation('TOFCO', None, 'supplier', 'Mento 플랫폼을 실제 건조 · 2024년 건조·반출 단계, 이후 생산은 별도 자료', MENTO, 'tofco'),
        relation('Encino Acquisition Partners', None, 'subsidiary', '2025년 8월 1일 취득 완료 · Utica 생산 자산·광물권 편입', QUARTER['EOG'], 'encino-eog'),
        relation('ProPetro', 'PUMP', 'supplier', '압력 펌핑·wireline 등 현장 서비스 · 2025년 ProPetro 매출의 EOG 12.1%, EOG 원가 비중 아님', PUMP),
        relation('Smart Sand', 'SND', 'supplier', '수압파쇄용 모래·물류 · 2025년 Smart Sand 매출의 EOG 10.9%, EOG 전체 모래 구매 비중 아님', SAND),
    ],
    'FANG': [
        relation('Medallion Midstream', None, 'customer', '2025년 Diamondback 매출 16% 구매자 · 물류 역할과 상품 구매를 구별', ANNUAL['FANG'], 'medallion-midstream'),
        relation('Shell / Shell Trading (USA)', 'SHEL', 'customer', '2025년 Diamondback 매출 13% · 법인 Shell Trading (USA) Company', ANNUAL['FANG']),
        relation('Enterprise / Enterprise Crude Oil', 'EPD', 'customer', '2025년 Diamondback 매출 12% · 계약 구매 법인 Enterprise Crude Oil LLC', ANNUAL['FANG']),
        relation('Vitol', None, 'customer', '2025년 Diamondback 매출 11% · Vitol Inc. 상품 구매', ANNUAL['FANG'], 'vitol-us'),
        relation('Viper Energy', 'VNOM', 'subsidiary', '광물권·로열티 연결 사업 · Sitio 취득·지주 법인 변경 후 현재 범위', QUARTER['FANG']),
        relation('Remuda Midstream Holdings', None, 'partner', '25% 비운영 JV 지분 · WTG Midstream은 2024년 ET로 매각, 현재 운영 자회사 아님', ANNUAL['FANG'], 'remuda-midstream'),
    ],
    'OXY': [
        relation('ProPetro', 'PUMP', 'supplier', '2025년 압력 펌핑·wireline 등 · ProPetro 매출의 OXY 13.7%, OXY 전체 비용 비중 아님', PUMP),
        relation('Liberty Energy', 'LBRT', 'supplier', '2025년 완결 서비스 · Liberty가 OXY를 매출 10% 초과 고객으로 실명 공시', LBRT),
        relation('Worley', None, 'supplier', '1PointFive STRATOS 실제 EPC·현장 인력 교육 · 설비 개발 단계와 운영량 분리', STRATOS, 'worley-energy'),
        relation('ADNOC', None, 'partner', 'UAE Shah/Al Hosn gas 공동 생산·처리 · OXY 40% 권리 2041년까지', ANNUAL['OXY'], 'adnoc-gas-context'),
        relation('Dolphin Energy', None, 'partner', 'Qatar 가스 생산·UAE/Oman 수송의 서로 다른 경제 지분 각 24.5%', ANNUAL['OXY'], 'dolphin-energy'),
        relation('BlackRock', 'BLK', 'partner', 'STRATOS 개발·운영·offtake 계약의 실제 JV · 단순 OXY 상장 주식 보유 관계와 다름', ANNUAL['OXY']),
        relation('1PointFive', None, 'subsidiary', 'DAC 탄소 제거 크레딧·지중 저장 사업 개발·판매', BAIN, '1pointfive'),
        relation('Carbon Engineering', None, 'subsidiary', '2023년 취득한 DAC 기술 사업 · 1PointFive와 기술·개발 역할이 다름', ANNUAL['OXY'], 'carbon-engineering'),
        relation('Bain & Company', None, 'customer', '1PointFive가 STRATOS CDR 크레딧 9,000톤·3년 판매 계약 · 원유 고객 아님', BAIN, 'bain-company'),
        relation('Microsoft', 'MSFT', 'customer', '1PointFive STRATOS CDR 500,000톤·6년 판매 계약 · 계약과 실제 인도 분리', MSFT_CDR),
    ],
    'DVN': [
        relation('WaterBridge', 'WBI', 'supplier', '생산수 집하·처분 전용 계약 2038년까지 · 2025년 IPO 후 지분과 실제 서비스 구매 분리', ANNUAL['DVN']),
        relation('WaterBridge', 'WBI', 'partner', '물 인프라 공동 개발 · 2025년 결합·IPO 후 약 14%는 그 기준일의 경제 지분', ANNUAL['DVN']),
        relation('Catalyst Midstream', None, 'supplier', 'Stateline 50,000 net acres의 실제 고정 요금 원유 집하·가스 처리 · 2038년까지', ANNUAL['DVN'], 'catalyst-midstream'),
        relation('Howard Energy Partners', None, 'partner', 'Catalyst 각 50% 공동 개발·HEP 운영 · 실제 서비스와 지분법 이익 구별', ANNUAL['DVN'], 'howard-energy'),
        relation('Dow', 'DOW', 'partner', 'Anadarko Basin 생산 면적 공동 개발 · 2025년 말 2-rig program', ANNUAL['DVN']),
        relation('Fervo Energy', None, 'partner', '지열 개발 투자 · 2025년 말 지분 약 15%, Devon이 발전 고객이라는 뜻 아님', ANNUAL['DVN'], 'fervo-energy'),
        relation('Coterra / 편입 법인', None, 'subsidiary', '2026년 5월 7일 합병 완료 · 독립된 현재 CTRA 상장 종목으로 연결하지 않음', QUARTER['DVN'], 'coterra-devon'),
    ],
    'EQT': [
        relation('MPLX / MarkWest', 'MPLX', 'supplier', '2025년 실제 가스 처리·NGL 성분 회수 계약 · MarkWest Energy Partners', ANNUAL['EQT']),
        relation('Williams / Ohio Valley Midstream', 'WMB', 'supplier', '실제 가스 처리·NGL 회수 · 별도 Laurel Mountain 공동 소유와 구별', ANNUAL['EQT']),
        relation('Williams', 'WMB', 'partner', 'Laurel Mountain Midstream 집하·처리 JV · 실제 자산 운영 공동사업', QUARTER['EQT']),
        relation('Blue Racer Midstream', None, 'supplier', '실제 가스 처리·NGL 회수 계약 · Williams의 JV 지분과 EQT 서비스 구매는 다른 역할', ANNUAL['EQT'], 'blue-racer'),
        relation('Mountain Valley Pipeline', None, 'supplier', 'Mainline 1.29 Bcf/d 확정 수송 2044년 6월까지 · Southgate .55는 미래 가동 조건', ANNUAL['EQT'], 'mvp-operating'),
        relation('NextEra Energy', 'NEE', 'partner', '2026년 6월 MVP Mainline Series A의 공동사업 상대 · 전력 구매 계약 아님', QUARTER['EQT']),
        relation('Smart Sand', 'SND', 'supplier', '수압파쇄용 모래·물류 · 2025년 Smart Sand 매출의 EQT 27.7%, EQT 전체 비용 비중 아님', SAND),
    ],
    'EXE': [
        relation('NG3 / New Generation Gas Gathering', None, 'supplier', '실제 집하·처리·수송 공급 · 2025년 10월 가동, 평균 900 MMcf/d·12년 약정', ANNUAL['EXE'], 'ng3-gathering'),
        relation('Williams / Momentum', 'WMB', 'partner', 'NG3 실제 공동사업 · EXE 35%; Williams의 Momentum 인수는 2026년 9월 완료', MOMENTUM),
        relation('ExxonMobil', 'XOM', 'supplier', 'NG3 JV가 CO₂ 저장 서비스를 구매 · 2026년 2월 전달·저장 시작, EXE 가스 구매자라는 뜻 아님', QUARTER['EXE']),
        relation('DT Midstream', 'DTM', 'supplier', 'DTM의 실제 가스 집하·수송 서비스 고객 · 2025년 DTM 연결 영업매출의 EXE 약 45%', report('DTM')),
        relation('Patterson-UTI / NexTier', 'PTEN', 'supplier', '2026년 2분기 Patterson 583 시추·NexTier 29 frac 현장 수행을 EXE가 직접 확인', EXE_CREWS),
        relation('Key Energy Services', None, 'supplier', '2026년 2분기 Haynesville Key 6123 workover 팀의 실제 현장 수행', EXE_CREWS, 'key-energy-services'),
        relation('Twin Eagle', None, 'subsidiary', '2026년 9월 16일 인수 완료 · 미국/Canada 가스 마케팅·수송·저장 플랫폼', TWIN_EAGLE, 'twin-eagle'),
        relation('Delfin FLNG 1', None, 'supplier', '2026년 4월 신규 LNG 구매 SPA 약 115만 톤/년·20년 · FID 조건부·2031년 목표', EXE_LNG, 'delfin-flng1'),
    ],
    'AR': [
        relation('Antero Midstream', 'AM', 'supplier', '집하·압축·물 공급의 실제 구매 · 생산 가스·완결 물 수요 장기 계약', ANNUAL['AR']),
        relation('Antero Midstream', 'AM', 'customer', 'AR 인력·운영·행정 서비스를 AM에 제공하고 비용 정산', report('AM')),
        relation('MPLX / MarkWest', 'MPLX', 'supplier', '가스 처리·NGL 분별·성분 회수 · 직접 MarkWest 시설과 AM/MarkWest JV 구별', ANNUAL['AR']),
        relation('TC Energy', 'TRP', 'supplier', 'Columbia·Columbia Gulf·ANR·MXP/GXP 가스 수송 예약 · South Bow의 액체 배관과 구별', ANNUAL['AR']),
        relation('Kinder Morgan', 'KMI', 'supplier', 'Tennessee Gas Pipeline 확정 수송 · 가스 판매 고객 아님', ANNUAL['AR']),
        relation('Energy Transfer', 'ET', 'supplier', 'Rover 가스·Mariner East 2 NGL 수송 · Sunoco LP 연료 유통과 다른 운영 법인', ANNUAL['AR']),
        relation('Enterprise Products Partners', 'EPD', 'supplier', 'ATEX 에탄 장거리 수송 계약 · 생산 NGL 판매와 물류 구매 구별', ANNUAL['AR']),
        relation('HG Production', None, 'subsidiary', '2026년 2월 3일 생산 자산 취득 완료 · AM이 산 HG Midstream과 다른 법인', QUARTER['AR'], 'hg-production'),
        relation('INEOS', None, 'customer', '공식 Project ONE 공급망 설명에서 Antero 에탄 공급을 확인 · 계약 물량·매출 비중은 추정하지 않음', INEOS_FEED, 'ineos-ethane'),
    ],
    'RRC': [
        relation('INEOS', None, 'customer', '공식 공급망에 Range 에탄 공급사 실명 · 익명 2025년 Customer A 비중과 동일시하지 않음', INEOS_FEED, 'ineos-ethane'),
        relation('MPLX / MarkWest', 'MPLX', 'supplier', '2012년 원래 Mariner East 처리·분별 경로 · 역사적 계약 자료, 현재 변경된 용량·요금은 이 발표로 확정하지 않음', RANGE_ETHANE),
        relation('Enterprise Products Partners', 'EPD', 'supplier', '2012년 발표 ATEX 에탄 수송 계약 · 역사적 거래, 2026년 실제 인도량으로 표시하지 않음', RANGE_ETHANE),
        relation('Baker Hughes / Baker', 'BKR', 'supplier', '방향성 시추 · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_DRILL),
        relation('SLB / Schlumberger', 'SLB', 'supplier', '방향성 시추 · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_DRILL),
        relation('Halliburton', 'HAL', 'supplier', '시멘팅 · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_DRILL),
        relation('ProFrac', None, 'supplier', '완결 서비스 · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_COMPLETE, 'range-profrac'),
        relation('TETRA Technologies / Tetra', 'TTI', 'supplier', 'flowback · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_COMPLETE),
        relation('Nine Energy Service', 'NINE', 'supplier', 'wireline · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_COMPLETE),
        relation('CalFrac', None, 'supplier', '완결 서비스 · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_COMPLETE, 'range-calfrac'),
        relation('Sandbox Logistics', None, 'supplier', '모래 물류 · 공식 현장 안내, 발표일·현재 계약 지속 여부 미확인', RANGE_COMPLETE, 'range-sandbox'),
    ],
}

PRIVATE = {}
for _key, _name, _business, _origin in [
    ('ngc-trinidad', 'National Gas Company of Trinidad and Tobago', 'Trinidad에서 EOG 가스를 구매하는 국영 가스 사업자와 계열입니다. 확인한 2025년 거래를 미국 가스 구매나 NGC 전체 수요로 확대하지 않습니다.', ANNUAL['EOG']),
    ('heritage-petroleum', 'Heritage Petroleum', 'EOG의 Trinidad 원유·콘덴세이트 구매자입니다. 여기서는 공시로 확인한 생산품 구매 역할을 정리합니다.', ANNUAL['EOG']),
    ('tofco', 'TOFCO', 'Chet Morrison Contractors와 Trinidad Weldfab의 공동사업으로 offshore 플랫폼을 건조합니다. EOG/bpTT Mento의 실제 제작을 공식 공급사 자료에서 확인했습니다.', MENTO),
    ('encino-eog', 'Encino Acquisition Partners', 'Utica 가스 생산 자산·광물권의 사업입니다. 2025년 8월 EOG 취득 완료로 독립된 현재 상장 경쟁사와 구별합니다.', QUARTER['EOG']),
    ('medallion-midstream', 'Medallion Midstream', 'Permian 원유 집하·수송과 구매를 연결하는 기업입니다. Diamondback의 FY2025 구매자 공시에서 매출 16%를 확인했습니다.', ANNUAL['FANG']),
    ('vitol-us', 'Vitol Inc.', '원유·에너지 상품을 구매·유통하는 거래 법인입니다. 2025년 Diamondback 매출 11%의 구매자이며 전체 Vitol 시장 점유율이 아닙니다.', ANNUAL['FANG']),
    ('remuda-midstream', 'Remuda Midstream Holdings', 'Diamondback의 비운영 투자 JV입니다. WTG Midstream 운영 자회사는 2024년 ET에 매각됐으며 현재 지분과 과거 운영망을 구별합니다.', ANNUAL['FANG']),
    ('worley-energy', 'Worley', '산업 설비의 엔지니어링·조달·시공을 제공합니다. STRATOS의 실제 EPC 수행을 1PointFive가 확인했고 설비 운영·가스 생산자는 아닙니다.', STRATOS),
    ('adnoc-gas-context', 'ADNOC / Shah gas', 'UAE의 가스 생산·처리 공동사업 상대입니다. Shah/Al Hosn에서 OXY 40% 참여와 gas·NGL·condensate 생산을 연결합니다.', ANNUAL['OXY']),
    ('dolphin-energy', 'Dolphin Energy', 'Qatar 가스 생산을 UAE·Oman 배관 수요와 연결합니다. 생산·배관의 두 경제적 지분과 배관 전체 능력·실수송량을 구별합니다.', ANNUAL['OXY']),
    ('1pointfive', '1PointFive', 'OXY 계열의 탄소 제거·저장 개발·판매 기업입니다. STRATOS에서 포집·지중 저장한 탄소에 대한 크레딧을 고객에게 공급하는 계약을 체결합니다.', BAIN),
    ('carbon-engineering', 'Carbon Engineering', '액체 흡수제를 사용하는 DAC 기술과 설계 혁신을 개발합니다. OXY가 취득한 기술 계열이며 STRATOS 시공사 Worley와 다른 역할입니다.', STRATOS),
    ('bain-company', 'Bain & Company', '1PointFive의 STRATOS 탄소 제거 크레딧 구매 고객입니다. 확인한 계약은 9,000톤·3년이며 일반 컨설팅 서비스 매출과 다른 방향의 거래입니다.', BAIN),
    ('catalyst-midstream', 'Catalyst Midstream', 'Stateline의 원유 집하·가스 처리 JV로 Devon 생산에 실제 고정 요금 서비스를 제공합니다. Devon/HEP 각 50%와 HEP 운영 역할을 구별합니다.', ANNUAL['DVN']),
    ('howard-energy', 'Howard Energy Partners', '에너지 물류·처리 개발·운영 기업입니다. Devon과 Catalyst를 공동 개발하고 HEP 계열이 운영합니다.', ANNUAL['DVN']),
    ('fervo-energy', 'Fervo Energy', '지열 자원 개발 기업입니다. Devon의 투자와 기술·개발 연계를 확인했으며 지분 투자를 Devon의 발전 상품 구매 계약으로 표시하지 않습니다.', ANNUAL['DVN']),
    ('coterra-devon', 'Coterra / Devon 편입 법인', 'Marcellus·Permian·Anadarko 생산 자산을 갖던 Coterra는 2026년 5월 Devon과 합병 완료했습니다. 이전 CTRA 시세·전년 실적을 현재 독립 상장사처럼 취급하지 않습니다.', QUARTER['DVN']),
    ('mvp-operating', 'Mountain Valley Pipeline', 'Mainline 가스 수송과 Southgate·Boost 개발의 series JV입니다. EQT 계열이 운영하고 생산자는 확정 수송 용량을 구매합니다.', QUARTER['EQT']),
    ('ng3-gathering', 'NG3 / New Generation Gas Gathering', 'Haynesville 가스 집하·처리·수송 및 CO₂ 분리·저장을 연결하는 JV입니다. 가스 집하는 2025년 10월, Exxon으로 CO₂ 전달은 2026년 2월 시작됐습니다.', QUARTER['EXE']),
    ('key-energy-services', 'Key Energy Services', '유정 정비·workover 현장 서비스를 제공합니다. EXE가 Haynesville의 Key 6123 팀 수행을 2026년 2분기 자료에서 확인했습니다.', EXE_CREWS),
    ('twin-eagle', 'Twin Eagle', '미국·Canada 천연가스 마케팅·수송·저장·최적화 사업입니다. 2026년 9월 16일 EXE 인수 완료 후 이름을 유지한 완전자회사로 운영합니다.', TWIN_EAGLE),
    ('delfin-flng1', 'Delfin FLNG 1', '해상 LNG 액화 vessel 1의 프로젝트 법인입니다. EXE의 약 115만 톤/년 구매 SPA는 2031년 목표·FID 조건부이며 현재 액화 인도 완료가 아닙니다.', EXE_LNG),
    ('hg-production', 'HG Energy II Production Holdings', 'West Virginia Marcellus 생산 자산입니다. 2026년 2월 AR이 취득한 생산 법인으로 AM의 HG Midstream 인프라 취득과 나눕니다.', QUARTER['AR']),
    ('ineos-ethane', 'INEOS / 에탄 공급망', '에탄을 석유화학 기초 원료로 사용합니다. 공식 공급망에 Range·Antero를 명시하지만 익명 고객 집중도·전체 조달량·국가별 제품 점유율은 이 문서에서 추정하지 않습니다.', INEOS_FEED),
    ('range-calfrac', 'CalFrac / Range 현장', 'Range가 완결 서비스 업체로 명시했습니다. 안내에는 발표일과 계약 기간이 없습니다.', RANGE_COMPLETE),
    ('range-profrac', 'ProFrac / Range 현장', 'Range가 완결 서비스 업체로 명시했습니다. Flowco(FLOC)와 다른 기업입니다.', RANGE_COMPLETE),
    ('range-sandbox', 'Sandbox Logistics / Range 현장', 'Range가 모래 물류 업체로 명시했습니다. 안내에는 발표일과 계약 기간이 없습니다.', RANGE_COMPLETE),
]:
    PRIVATE[_key] = profile(_name, _origin, _business, '', products=[('확인한 산업 역할', _business)])

for _symbol, _rows in EDGES.items():
    for _edge in _rows:
        if _edge['registry_id'] in PRIVATE:
            PRIVATE[_edge['registry_id']]['relations'].append(relation(PUBLIC[_symbol]['name'], _symbol,
                {'subsidiary': 'parent', 'supplier': 'customer', 'customer': 'supplier', 'partner': 'partner'}[_edge['kind']],
                _edge['detail'], _edge['source']))

# Source-side disclosures establish actual supply, not just plausible services.
for _symbol, _name, _origin, _customers, _detail in [
    ('PUMP', 'ProPetro', PUMP, [('EOG', 'EOG Resources'), ('OXY', 'Occidental Petroleum'),
                              ('XOM', 'ExxonMobil'), ('PR', 'Permian Resources')],
     '2025년 압력 펌핑·wireline 등 실제 서비스 고객 · 공급사 매출 집중도는 고객 전체 구매 비중이 아님'),
    ('LBRT', 'Liberty Energy', LBRT, [('OXY', 'Occidental Petroleum')], '2025년 매출 10% 초과로 실명 공시한 완결 서비스 고객'),
    ('SND', 'Smart Sand', SAND, [('EQT', 'EQT'), ('EOG', 'EOG Resources')], '2025년 수압파쇄 모래·물류 실제 고객 · FY2024 Encino 비중과 현재 EOG 비중 구별'),
]:
    EDGES.setdefault(_symbol, []).extend(relation(_customer_name, _customer, 'customer', _detail, _origin)
        for _customer, _customer_name in _customers)

for _supplier in ('BKR', 'SLB', 'HAL', 'TTI', 'NINE'):
    _edge = next(row for row in EDGES['RRC'] if row['symbol'] == _supplier)
    EDGES.setdefault(_supplier, []).append(relation('Range Resources', 'RRC', 'customer',
        _edge['detail'], _edge['source']))

# Explicit business-scope comparisons; no invented transaction or claimed issuer
# statement naming a rival. Each target's own primary filing supports its scope.
for _symbol, _other, _scope in [('EOG', 'FANG', 'Delaware 원유·수반가스 개발'),
        ('FANG', 'EOG', 'Delaware 원유·수반가스 개발'), ('OXY', 'DVN', '미국 Permian 원유·가스 개발'),
        ('DVN', 'OXY', '미국 Permian 원유·가스 개발'), ('EQT', 'EXE', 'Appalachia 가스 생산·판로'),
        ('EXE', 'EQT', 'Appalachia 가스 생산·판로'), ('AR', 'RRC', 'Appalachia 습성 가스·NGL'),
        ('RRC', 'AR', 'Appalachia 습성 가스·NGL')]:
    EDGES[_symbol].append(relation(PUBLIC[_other]['name'], _other, 'competitor',
        '공시 사업 범위를 대조한 비교 대상 · ' + _scope + ' · 실제 거래나 회사가 직접 발표한 경쟁사 명단이 아님', ANNUAL[_other]))
    PUBLIC[_symbol]['sources'].append(ANNUAL[_other])
