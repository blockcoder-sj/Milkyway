"""Reviewed gas infrastructure: physical service, OEM supply and contract stages.

Do not infer confidential customer names from concentration percentages. The
annual revenue table and later operating changes keep separate source dates.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

SYMBOLS = ('DTM', 'AM', 'KNTK', 'CQP', 'SUN', 'USAC', 'KGS', 'AROC')
ANNUAL = {symbol: report(symbol) for symbol in SYMBOLS}
QUARTER = {symbol: report(symbol, 'quarter') for symbol in SYMBOLS}
VECTOR = source('Enbridge · Vector 공동 수송 확장',
    'https://www.enbridge.com/stories/2026/may/vector-pipeline-versatility-westbound-expansion-growing-midwest-utility-demand', '2026-05-08')
AM_SALE = source('Antero Midstream · Ohio Utica 매각 완료 8-K',
    'https://www.anteromidstream.com/investors/sec-filings/all-sec-filings/content/0001104659-26-018616/tm267010d1_8k.htm', '2026-02-23')
KINETIK = source('Kinetik · 2026년 2분기 가동·개발 현황',
    'https://ir.kinetik.com/news/news-details/2026/Kinetik-Reports-Record-Second-Quarter-2026-Results-and-Raises-Full-Year-2026-Guidance/default.aspx', '2026-08-05')
ARIEL = source('Ariel · 공식 압축 패키지 공급·서비스 파트너',
    'https://www.arielcorp.com/contact/ariel-distributors/distributor-list.html', '열람 2026-10-03')
KGS_ENGINES = source('Kodiak · 압축·발전 장비 발표 자료',
    'https://ir.kodiakgas.com/sec-filings/all-sec-filings/content/0001193125-26-039600/0001193125-26-039600.pdf', '2026-02-05')
KGS_BKR = source('Kodiak·Baker Hughes · 발전 장비 공급 계약',
    'https://ir.kodiakgas.com/news-events/press-releases/detail/82/kodiak-gas-services-baker-hughes-announce-multi-year-gas', '2026-07-08')
KGS_POWER = source('Kodiak · West Texas 전력 공급 계약',
    'https://ir.kodiakgas.com/news-events/press-releases/detail/86/kodiak-gas-services-announces-power-supply-agreement-with', '2026-09-21')
AROC_RESULTS = source('Archrock · 2026년 2분기 계약·운영 현황',
    'https://www.sec.gov/Archives/edgar/data/1389050/000138905026000025/aroc-20260804xex99d1.htm', '2026-08-04')

PUBLIC = {
    'DTM': profile('DT Midstream', ANNUAL['DTM'],
        'Appalachia·Haynesville의 생산지 가스를 집하하고 Midwest·Eastern Canada·Gulf 발전·도시가스·LNG 수요로 연결합니다. 배관·저장과 생산지 집하 두 부문이며 일부 장거리 배관은 지분법 공동사업입니다.',
        '2025년 연결 매출 12억4,300만 달러는 배관·저장 6억8,700만과 집하 5억5,600만입니다. 지분법 공동사업의 전체 매출은 연결 매출에 포함하지 않습니다. 2025년 확정 계약 비율은 배관 매출 92%·비연결 공동사업 매출 99%로 분모가 다릅니다.',
        [('확정 가스 수송·저장', '용량 예약·최소 물량 약정에서 고정 수요 요금·미달 대가를 받고 비확정 수송은 실제 물량 기반으로 받습니다.'),
         ('유정 집하·처리', '집하·압축·탈수·간선 연결과 Haynesville의 일부 물·모래 서비스입니다.'),
         ('상호 연결망', 'Guardian·Midwestern·Viking과 LEAP, NEXUS·Vector·Millennium이 서로 다른 생산지·수요 시장을 연결합니다.')],
        customers='2025년 Expand Energy가 연결 영업 매출 약 45%입니다. 유틸리티·발전·산업·마케터 고객과 생산지 고객의 계약을 구분하고, 이름을 밝히지 않은 utility를 특정 기업으로 추정하지 않습니다.',
        inputs='압축·배관·저장 설비, 연료·전력, 통행권·시공·정비와 환경·FERC 허가가 필요합니다. 매입 가스 판매 사업의 가격 노출과 고정 용량 수송의 노출은 다릅니다.',
        competition='같은 공급지·수요지의 대체 수송·저장·집하 경로, 요금·신뢰성·연결성과 추가 용량이 경쟁 조건입니다.'),
    'AM': profile('Antero Midstream', ANNUAL['AM'],
        'Antero Resources의 Appalachian 생산·완결을 지원하는 가스 집하·압축·물 서비스 기업입니다. MarkWest와 가스 처리·NGL 분별 공동사업을 운영하고 2026년 West Virginia 자산을 추가했습니다.',
        '2025년 Antero 집하·압축 9억8,728만4,000, Antero 물 서비스 2억6,939만9,000, 제3자 물 241만5,000 달러입니다. 합계 12억5,909만8,000에서 고객 관계 상각 7,067만2,000을 차감한 연결 매출은 11억8,842만6,000입니다. 양수 항목만으로 100% 구성비를 만들지 않습니다.',
        [('집하·압축', '전용 생산 면적의 유정 가스를 모아 압축하고 처리 공장·장거리 배관에 전달합니다.'),
         ('완결·생산수', '강·저수지 등 물을 배관·저장·펌프·혼합 시설로 공급하고 일부 생산수·환류수를 운송합니다.'),
         ('MarkWest 처리·분별 JV', '각 50% 공동사업으로 West Virginia 처리 시설과 Ohio 분별기 두 곳의 3분의 1 지분을 갖습니다. MarkWest가 일상 운영합니다.')],
        customers='매출 대부분이 Antero Resources입니다. 가스 집하·압축 계약은 2038년, 물 서비스는 2035년까지이며 고정 요금·원가 기반·최소 물량 조건이 다릅니다.',
        inputs='배관·압축기·물 펌프·전력·물 가용성과 생산자 개발 일정이 핵심입니다. Antero가 운영 인력·행정 서비스를 파견하고 비용을 정산합니다.',
        competition='자체·외부 처리·수송망과 생산 면적 전용 계약이 범위입니다. 생산량과 신규 유정 완결의 물 수요는 같은 지표가 아닙니다.'),
    'KNTK': profile('Kinetik', ANNUAL['KNTK'],
        'Delaware Basin의 가스·NGL·원유·생산수를 집하·압축·처리·운송·폐기하고 Gulf 시장에 연결하는 기업입니다. Midstream Logistics와 Pipeline Transportation 두 부문입니다.',
        '2025년 연결 영업 매출 17억6,438만9,000 달러는 제품 판매 13억722만8,000, 서비스 4억4,549만6,000, 기타 1,166만5,000입니다. 최소 물량 미달 대가 200만은 서비스 매출에 포함됩니다. PHP·Shin Oak 지분법 이익이나 EPIC 매각 이익을 매출에 더하지 않습니다.',
        [('가스 집하·처리', '2025년 말 4,200마일 이상 집하 배관·825,000마력 이상 압축·8개 처리 complex·하루 2.4 Bcf 이상 cryogenic 용량입니다.'),
         ('생산수·원유', '원유 집하·안정화·저장과 생산수 집하·폐기를 제공합니다. 2025년 말 물 처분 허가 용량 하루 약 580,000배럴은 실제 물 처리량이 아닙니다.'),
         ('장거리 배관·시장 접근', 'PHP 가스 배관 55.5%, Shin Oak NGL 배관 33% 지분과 자체 Delaware Link·NGL 배관을 구별합니다.')],
        customers='Apache와 제품·서비스 계약을 유지하며 Permian Resources의 Barilla Draw 자산 편입으로 생산지 연결을 확장했습니다. 생산자 가스 공급과 처리 서비스 구매가 겹칠 수 있습니다.',
        inputs='압축·처리·산성 가스 주입·전력·연료·약품·물 처분 허가와 PHP demand fee·Shin Oak capacity fee가 비용입니다.',
        competition='같은 생산지 물량과 하류 반출 능력이 범위입니다. Waha 가격 때문에 생산자가 감산하면 처리·상품·운송의 물량이 함께 달라질 수 있습니다.'),
    'CQP': profile('Cheniere Energy Partners', ANNUAL['CQP'],
        'Sabine Pass LNG 터미널·액화 6개 train·Creole Trail 가스 배관을 보유한 MLP입니다. Cheniere Energy의 Corpus Christi까지 모두 CQP 자산으로 표시하지 않습니다.',
        '2025년 연결 매출 107억5,800만 달러는 제3자 LNG 82억, Cheniere 계열 LNG 23억5,800만, 재기화 1억3,600만, 기타 6,400만입니다. LNG 고정 액화료와 Henry Hub 연동 변동료·마케팅 거래를 구별합니다.',
        [('LNG 액화·출하', '2025년 말 명목 생산능력 연 3,000만 톤 이상, 저장 17 Bcfe·탱크 5개·선석 3개입니다. 설비능력과 실제 판매량은 다릅니다.'),
         ('원료 가스 조달·수송', '미국 가스 조달·IPM과 94마일 Creole Trail·외부 가스 배관·저장 계약으로 원료를 확보합니다.'),
         ('재기화', 'TotalEnergies가 하루 1 Bcf 예약 대가를 실제 사용과 관계없이 지급합니다. LNG 액화·수출 구매 계약과 별개의 역할입니다.'),
         ('Sabine Pass 확장', '추가 3개 train·최대 약 연 2,000만 톤은 개발 계획입니다. 규제·상업·자금 조건과 FID를 충족하기 전 현재 가동능력에 합산하지 않습니다.')],
        customers='2025년 외부 고객 계약 매출에서 BG Gulf Coast 계열 22%, 한국가스공사 15%, GAIL 15%, Naturgy 14%, TotalEnergies 10%입니다. 회사 전체 시총 비중이나 글로벌 LNG 시장점유율이 아닙니다.',
        inputs='천연가스·운송·저장·액화 연료, 압축기·열교환기·전력·정비·선적이 필요합니다. 고정 액화료는 취소·미인수 조건을, IPM은 글로벌 지수·액화·운송 차감을 확인합니다.',
        competition='다른 LNG 공급 프로젝트와 목적지·인도 방식·지수·정비·운송 조건으로 경쟁합니다. 계약 취소권과 터미널 가동 중단은 별도 조건입니다.'),
    'SUN': profile('Sunoco LP', ANNUAL['SUN'],
        '연료 도매·직영 편의점, 배관·저장·터미널과 Burnaby 정유소를 운영하는 MLP입니다. NuStar·Parkland 편입 후 북미·Caribbean·유럽의 물류·유통으로 확장됐습니다.',
        '2025년 연결 매출 252억100만 달러는 연료·상품 판매 237억200만, 서비스 13억6,900만, 임대 1억3,000만입니다. 판매액에는 매입 연료 재판매가 포함되므로 정유 이익이나 배관 수수료만을 뜻하지 않습니다. Parkland는 2025년 10월 말 편입돼 연간 매출에 2개월만 반영됐습니다.',
        [('브랜드·비브랜드 연료', '주유소·유통상·사업자·정부에 휘발유·경유·항공·선박 연료·프로판·윤활유를 공급합니다.'),
         ('직영·위탁 유통', '편의점·식품·자동차용품과 연료 소매·카드락을 운영하고 도매·위탁 수익을 구별합니다.'),
         ('배관·터미널', '원유·정유제품·암모니아의 배관·저장·터미널과 ET 공동사업이 있습니다. 암모니아는 원유 배럴 처리량에 더하지 않습니다.'),
         ('Burnaby 정유', '2025년 말 운영능력 하루 약 55,000배럴. 경질 저유황·합성 원유와 바이오 원료를 처리하고 BC 소매망·공항·상업 고객에 공급합니다.')],
        customers='제3자 dealer·distributor·commission agent와 상업·정부·직영 고객입니다. Vancouver International Airport는 Burnaby 제품의 실제 판매 경로입니다.',
        inputs='주요 브랜드 연료 공급사는 Chevron·Exxon·Phillips 66·Valero이며 보통 초기 3–5년 공급 계약입니다. 연료 매입·세금·재고·운송·정비·임차 비용이 관련됩니다.',
        competition='지역 연료 도매·소매·저장·물류와 브랜드·가격·신뢰성으로 경쟁합니다. 원유 가격 변화와 도매 마진·소비량은 다른 항목입니다.'),
    'USAC': profile('USA Compression Partners', ANNUAL['USAC'],
        '자사 천연가스 압축 장비를 설치·운영·정비해 생산·집하·처리·운송·gas lift를 지원하는 MLP입니다. 2026년 J-W Power를 편입해 압축기 제조·부품·서비스도 추가했습니다.',
        '2025년 매출 9억9,809만9,000 달러는 계약 압축 9억7,163만6,000과 부품·서비스 2,646만3,000입니다. 계약은 대체로 6개월–5년 고정 요금이며 가스 소유권을 갖거나 원료 가스를 판매하는 사업과 다릅니다.',
        [('큰 압축기', '생산지 가스를 처리·간선망으로 보내기 위한 압력을 제공합니다. 2025년 말 총 fleet 390만 마력과 실제 수익 발생·가동 마력을 구별합니다.'),
         ('작은 gas lift 장비', '가스를 유정에 주입해 액체 생산을 돕습니다. 가스 수송과 용도가 다르며 장비 크기별 수익·배치 조건도 다릅니다.'),
         ('OEM 부품·패키징', '엔진·압축기 프레임/실린더·냉각기·제어와 조립·정비가 별도 공급 역할입니다.')],
        customers='2025년 고객 약 260개·상위 10개가 매출 46%입니다. Energy Transfer 계열 압축 서비스 매출은 이름이 확인되는 관계사 거래입니다. 미공개 나머지 고객 이름은 추측하지 않습니다.',
        inputs='Caterpillar·Cummins·INNIO Waukesha·TECO-Westinghouse 엔진, Ariel·Cooper Gemini·Arrow 압축기, 여러 냉각기 제조사와 패키징 업체에 의존합니다. 운전 연료는 일반적으로 고객이 제공합니다.',
        competition='고객의 직접 장비 구매·운영, 다른 계약 압축·지역 업체가 범위입니다. 마력·가동률·요금·기계적 가용성·장비 이동·정비가 사업의 핵심 변수입니다.'),
    'KGS': profile('Kodiak Gas Services', ANNUAL['KGS'],
        '미국 생산자·midstream 고객에게 압축 장비를 제공·운영하고, 2026년부터 데이터센터·microgrid 등에 분산 발전·수용가 내부 전력을 공급합니다. 현재 압축 인프라·발전 인프라·기타 서비스 3개 보고 부문입니다.',
        '2025년 연결 매출 13억810만 달러는 당시 계약 압축 11억8,127만, 기타 서비스 1억2,683만입니다. 2026년 4월 DPS 인수 전 수치여서 새 발전 부문이 포함돼 있지 않습니다. 2025년 구성과 2026년 3개 부문을 같은 기간으로 합산하지 않습니다.',
        [('압축 인프라', '대형 장비 중심으로 gas lift·집하·처리·운송 압력을 제공합니다. Permian·Eagle Ford 비중과 장비 배치·신뢰성이 관련됩니다.'),
         ('발전 인프라', '고객 현장 발전기·balance of plant를 공급하고 설치·운전·정비합니다. 전력 MW와 압축기 마력은 별도 단위입니다.'),
         ('기타 서비스', '고객 소유 장비의 부품·정비·재구성·설치 등 압축·발전의 보조 서비스를 제공합니다.')],
        customers='2025년 상위 4개가 매출 32%, 한 고객이 10% 이상이나 실명을 공시하지 않았습니다. 미공개 고객명을 같은 지역 생산자로 추측하지 않습니다.',
        inputs='Caterpillar 엔진·Ariel 압축기, 조립·정비·전력 설비와 기술자가 필요합니다. 새 Baker Hughes 공급은 터빈·발전기·교육·부품을 연결합니다.',
        competition='계약 압축과 분산 발전은 고객·설비·단위·계약이 다른 사업입니다. 압축 수요는 생산·처리·운송 물량, 발전 수요는 전력 용량·연료·가동 조건을 확인합니다.'),
    'AROC': profile('Archrock', ANNUAL['AROC'],
        '미국 천연가스의 생산·처리·운송·저장에 필요한 압축 장비를 소유·운영하고, 고객 소유 장비 정비·재구성·부품 서비스를 제공합니다. contract operations와 aftermarket services 두 부문입니다.',
        '2025년 매출 14억8,981만8,000 달러는 회사 소유 계약 운영 12억7,208만1,000과 고객 소유 장비 정비·부품 2억1,773만7,000입니다. 계약 운영이 약 85%이며 장비 매각 대금·인수 대가를 서비스 매출로 표시하지 않습니다.',
        [('계약 압축', '설계·조달·소유·설치·운전·수리·정비를 제공합니다. 주로 1,000마력 초과 큰 장비에 초점을 둡니다.'),
         ('고객 소유 장비 지원', '정비·overhaul·재구성·부품·현장 운전 서비스를 제공하며 고객이 설비를 소유합니다.'),
         ('전기 구동·메탄·NGL', '전기 구동 압축과 메탄 회수·NGL 관련 솔루션은 가스 엔진의 연료·배출 조건과 구별합니다.')],
        customers='2025년 상위 5개가 두 부문 매출 35%이고 단일 고객은 연결 매출 10%를 넘지 않았습니다. 생산자·가스 처리·집하·운송 고객으로 실명 미공개 집중도를 특정 기업명에 연결하지 않습니다.',
        inputs='압축 패키지·엔진·부품·윤활유·기술자·정비소와 장비 이동이 필요합니다. Ariel 공식 목록에서 압축 패키지 파트너 관계를 확인했으며 이 목록만으로 구매액·독점 계약을 추정하지 않습니다.',
        competition='같은 현장의 압축 서비스를 제공하는 다른 업체 및 고객의 자체 운영이 범위입니다. 계약 요금·기계적 가용성·가동 마력과 고객 소유 정비 수요를 구별합니다.'),
}

for _symbol in ('AM', 'KGS'):
    PUBLIC[_symbol]['description_source'] = QUARTER[_symbol]
    PUBLIC[_symbol]['brief'][0]['source'] = QUARTER[_symbol]
PUBLIC['KGS']['products'] = [fact(row['title'], row['detail'], QUARTER['KGS']) for row in PUBLIC['KGS']['products']]

OPERATIONS = {
    'DTM': [('집하 계약 유형', '2025년 집하 매출에서 firm revenue 약 57%·flowing gas 약 36%입니다. 배관 부문의 92%와 다른 분모이며 모두 회사 전체 매출 비율이 아닙니다.', ANNUAL['DTM']),
            ('Vector 확장', 'Enbridge 60%·DTM 40% 공동 배관에서 서향 하루 400 MMcf 추가 용량을 승인했습니다. 20년 확정 계약으로 예약됐으며 2028년 가동 계획입니다. 별도 비구속적 수요 조사 300–500 MMcf는 승인 용량이 아닙니다.', VECTOR)],
    'AM': [('현재 보유망 변동', 'HG Midstream 인수는 2026년 2월 3일 완료, Ohio Utica 자산 매각은 2월 23일 완료됐습니다. 매각된 118마일 집하·0.7 Bcf/d 압축·85마일 물 배관을 현재 전체 보유망에 더하지 않습니다.', QUARTER['AM']),
           ('Utica 인수 상대', 'Infinity Natural Resources 계열과 Northern Oil and Gas가 매수했습니다. 과거 자산 거래이며 Antero Midstream의 현재 자회사·지속 공급 관계가 아닙니다.', AM_SALE),
           ('운영·행정 공급', 'Antero가 파견·운영·행정 서비스를 제공하고 직접 비용·배분 간접 비용을 정산합니다. 서비스 계약은 2039년까지이며 AR의 2025년 말 지분 29%와 다른 역할입니다.', ANNUAL['AM'])],
    'KNTK': [('판매한 배관', '2024년 GCX, 2025년 10월 31일 EPIC 지분을 매각했습니다. EPIC 매각 당시 Kinetik 지분 27.5%·선급 현금 5억420만 달러는 배관 운송 매출이 아닙니다.', ANNUAL['KNTK']),
             ('실제 운송 비용', 'PHP에 demand fee, Breviloba/Shin Oak에 capacity fee를 지급합니다. 2026년 상반기 두 계약 비용 합계 1,540만 달러로 지분 소유와 실제 물류 구매를 나눕니다.', QUARTER['KNTK']),
             ('가동과 건설', '2026년 8월 발표에서 ECCC 가동을 확인했습니다. KLII는 2028년 중반, Diamond Volt 40 MW는 2027년 2분기, 산성 가스 주입·sour conversion은 2026년 말 계획입니다.', KINETIK)],
    'CQP': [('취소·원료 가격 조건', '장기 SPA는 통상 인수 취소에도 고정료를 지급하며 변동료는 Henry Hub와 액화 연료·수송에 연결됩니다. IPM은 글로벌 LNG·가스 지수에서 액화료·운송비 등을 차감하는 구조입니다.', ANNUAL['CQP']),
            ('계약 기간·판매 범위', '2025년 말 기존 SPA/IPM의 가중 평균 잔여 기간은 약 13년·예상 생산의 약 85%를 제3자 계약에 연결했습니다. 예약·예상 물량을 현재 판매량으로 사용하지 않습니다.', ANNUAL['CQP']),
            ('확장 시공 계약의 현재 단계', '2026년 5월 Bechtel과 1단계 lump-sum turnkey EPC를 체결하고 초기 설계·조달의 제한적 착수 지시를 발행했습니다. 전체 프로젝트의 긍정적 FID·가동 완료와 다릅니다.', QUARTER['CQP']),
            ('그룹 내 중복', 'CQP의 Sabine Pass 사업은 LNG 그룹 연결에 포함됩니다. LNG와 CQP의 매출·생산능력을 업계 합계에 중복 더하지 않습니다.', ANNUAL['CQP'])],
    'SUN': [('최근 편입', 'Parkland 인수는 2025년 10월 31일 완료. TanQuid의 독일 15곳·폴란드 1곳 터미널은 2026년 1월 16일, Delta의 Caribbean 5개 시장 자산은 4월 1일 편입됐습니다.', QUARTER['SUN']),
            ('Energy Transfer 공동 물류', 'J.C. Nolan의 Midland 경유 저장·500마일 수송과 ET-S Permian의 원유·물 집하·저장이 연결됩니다. 공동사업 전체 능력과 귀속 능력은 다릅니다.', ANNUAL['SUN']),
            ('상장 증권 구분', 'SunocoCorp(SUNC)의 Class D 경제적 지분·일반 파트너 이사회 위임 구조는 Sunoco LP(SUN) 증권과 다릅니다. Summit Midstream(SMC)을 SunocoCorp로 연결하지 않습니다.', ANNUAL['SUN'])],
    'USAC': [('J-W 실제 편입', '2026년 1월 12일 인수 완료로 총 fleet 약 100만·active 약 80만 마력이 추가됐습니다. 초기 8억6,000만 달러 발표와 취득일 공정가치·조정 포함 9억1,160만 달러를 구별합니다.', QUARTER['USAC']),
             ('고객·모회사·공급 역할', 'Energy Transfer 계열은 압축 서비스 고객이며 IT·회계·HR 자원과 SEC Energy 패키징 공급도 연결합니다. 2026년 2월 ET의 LP 32%·GP 100%는 별도의 지배 관계입니다.', ANNUAL['USAC'])],
    'KGS': [('발전 인수와 부문 변경', 'DPS를 2026년 4월 1일 인수 완료해 Kodiak Power Solutions로 운영합니다. 취득 대가는 현금 5억8,730만·주식 공정가치 1억3,900만 달러이며 초기 발표 금액과 다릅니다.', QUARTER['KGS']),
            ('발전 장비 공급', 'Baker Hughes 초기 장비 주문은 약 1 GW를 2030년까지 공급하는 범위이고 전체 framework는 최대 1.8 GW입니다. NovaLT16·Frame 5 터빈·BRUSH 발전기 주문을 현재 설치 능력에 더하지 않습니다.', KGS_BKR),
            ('West Texas 고객 계약', '2026년 9월 계약은 76 MW·6년·약 40개 가스 왕복 발전기입니다. 설치는 2026년 4분기–2027년 1분기, 매출 개시는 2027년 1분기 예상입니다. 운영자·hyperscaler·GPU 보증사 실명은 미공개입니다.', KGS_POWER)],
    'AROC': [('통상 계약 기간', '현장별 초기 계약은 보통 12–36개월·최대 장비는 통상 60개월까지입니다. 이후 30일 사전 통지 해지의 월별 계약과 고정 장기 확약을 구별합니다.', ANNUAL['AROC']),
             ('최근 장기 계약', '2026년 8월 발표에서 기존 전략 고객 약 665,000마력·8년 기본·2년 연장 옵션 계약을 확인했습니다. 고객 실명을 밝히지 않아 특정 생산자 이름을 붙이지 않습니다.', AROC_RESULTS),
             ('NGCS 편입', '2025년 5월 1일 NGCS 편입으로 약 326,000 운영 마력·18,000 신규 계약 backlog가 추가됐습니다. backlog는 현재 가동 마력이 아닙니다.', QUARTER['AROC'])],
}

for _symbol, _rows in OPERATIONS.items():
    PUBLIC[_symbol]['segments'] = [fact(*row) for row in _rows]
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    PUBLIC[_symbol]['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    PUBLIC[_symbol]['sources'] += [QUARTER[_symbol], *(row[2] for row in _rows)]
    PUBLIC[_symbol]['drivers'] = [fact('물량·계약·가격의 구분',
        {'AM': '생산자 가스 물량·완결 횟수·전용 면적·상각과 처리 JV 이익을 구별합니다.',
         'KNTK': 'Waha 베이시스·감산·NGL 회수·sour gas 처리·반출 능력과 제품 매매 마진이 관련됩니다.',
         'CQP': 'Henry Hub·글로벌 지수·액화료·정비·날씨·선적 시점과 계약 취소 조건을 확인합니다.',
         'SUN': '연료 소비·도매/소매 마진·상품 매입·재고·세금·수송·규제 크레딧을 나눕니다.',
         'DTM': '용량 요금·예약 갱신·생산자 개발·계절 수요·허가와 FERC 요율 회수가 관련됩니다.',
         'USAC': '수익 발생 마력·가동률·월 요금·장비 이동·정비·부품 조달·고객 신용을 구별합니다.',
         'KGS': '압축 마력·발전 MW·각 가동률·설비 조달·연료·계약 개시가 다른 사업 변수입니다.',
         'AROC': '가동 마력·요금·기계적 가용성·정비 원가·부품 매출과 장비 매각을 나눕니다.'}[_symbol],
        QUARTER[_symbol] if _symbol == 'KGS' else ANNUAL[_symbol])]

EDGES = {
    'DTM': [relation('Expand Energy', 'EXE', 'customer', '2025년 연결 영업 매출 약 45% · 지분법 JV 전체 매출 제외', ANNUAL['DTM']),
            relation('Enbridge', 'ENB', 'partner', 'Vector 가스 배관 ENB 60%·DTM 40% · 실제 운영 JV와 승인된 2028년 확장', VECTOR)],
    'AM': [relation('Antero Resources', 'AR', 'customer', '가스 집하·압축·물 서비스의 핵심 고객 · 장기 계약·전용 면적·최소 물량', ANNUAL['AM']),
           relation('Antero Resources', 'AR', 'supplier', '운영 인력 파견·행정 서비스 · 직접·배분 간접 비용 정산', ANNUAL['AM']),
           relation('MPLX', 'MPLX', 'partner', 'MarkWest와 처리·분별 각 50% JV · MarkWest가 일상 운영', ANNUAL['AM']),
           relation('Infinity Natural Resources', 'INR', 'partner', '계열사가 2026년 2월 Ohio Utica 자산 매수 · 과거 거래, 현재 JV 아님', AM_SALE),
           relation('Northern Oil and Gas', 'NOG', 'partner', '2026년 2월 Ohio Utica 공동 매수 · 현재 AM 자회사·공급사 아님', AM_SALE)],
    'KNTK': [relation('APA / Apache', 'APA', 'customer', 'Apache와 제품·서비스 매출 계약 · Apache의 과거 주식 매각과 현재 거래는 다른 관계', ANNUAL['KNTK']),
             relation('Kinder Morgan', 'KMI', 'partner', 'PHP 가스 배관 공동 소유·Kinder Morgan 운영 · Kinetik 약 55.5%', ANNUAL['KNTK']),
             relation('Enterprise Products Partners', 'EPD', 'partner', 'Breviloba/Shin Oak NGL 공동사업 · Kinetik 33%·Enterprise 운영', ANNUAL['KNTK']),
             relation('Permian Highway Pipeline', None, 'supplier', '가스 운송 demand fee를 실제 지급 · 지분법 JV 보유와 물류 구매를 분리', QUARTER['KNTK'], 'permian-highway'),
             relation('Breviloba / Shin Oak', None, 'supplier', 'NGL 운송 capacity fee 지급 · PHP와 합산 2026년 상반기 비용 1,540만 달러', QUARTER['KNTK'], 'shin-oak')],
    'CQP': [relation('Cheniere Energy', 'LNG', 'parent', 'Sabine Pass를 그룹 연결 · Corpus Christi는 CQP 소유 자산이 아님', ANNUAL['CQP']),
            relation('Shell / BG Gulf Coast', 'SHEL', 'customer', 'BG Gulf Coast 계열 SPA · 2025년 외부 고객 계약 매출 22%', ANNUAL['CQP']),
            relation('한국가스공사', None, 'customer', 'Sabine Pass LNG SPA · 2025년 외부 고객 계약 매출 15%', ANNUAL['CQP'], 'kogas'),
            relation('GAIL (India)', None, 'customer', 'Sabine Pass LNG SPA · 2025년 외부 고객 계약 매출 15%', ANNUAL['CQP'], 'gail-india'),
            relation('Naturgy LNG GOM', None, 'customer', 'Sabine Pass LNG SPA · 2025년 외부 고객 계약 매출 14%', ANNUAL['CQP'], 'naturgy-lng'),
            relation('TotalEnergies', 'TTE', 'customer', 'LNG SPA 2025년 계약 매출 10% · 별도로 하루 1 Bcf 재기화 TUA 예약', ANNUAL['CQP']),
            relation('Bechtel', None, 'supplier', '2026년 5월 Sabine Pass 확장 1단계 EPC · 초기 설계·조달 제한 착수, FID·전체 가동 아님', QUARTER['CQP'], 'bechtel')],
    'SUN': [*[relation(name, symbol, 'supplier', '2025년 공시의 물량 기준 주요 브랜드 연료 공급사 · 공급 계약 통상 초기 3–5년', ANNUAL['SUN'])
              for name, symbol in [('Chevron', 'CVX'), ('ExxonMobil', 'XOM'), ('Phillips 66', 'PSX'), ('Valero', 'VLO')]],
            relation('Energy Transfer', 'ET', 'partner', 'J.C. Nolan 경유 수송·저장 및 ET-S Permian 원유·물 집하 공동사업', ANNUAL['SUN']),
            relation('SunocoCorp', 'SUNC', 'owner', 'Class D units와 GP 이사회 위임 구조 · Sunoco LP와 별도 상장 증권', ANNUAL['SUN'])],
    'USAC': [relation('Caterpillar', 'CAT', 'supplier', '천연가스 압축 장비 엔진 · 3300/3400/3500/3600 계열', ANNUAL['USAC']),
             relation('Cummins', 'CMI', 'supplier', '압축 장비 엔진 공급 · 공시의 실제 부품 제조사', ANNUAL['USAC']),
             relation('Energy Transfer', 'ET', 'customer', '계열사에 압축 서비스를 제공하고 관계사 매출을 공시', QUARTER['USAC']),
             relation('Energy Transfer', 'ET', 'supplier', 'IT·회계·HR 인력·자원 공동 서비스', ANNUAL['USAC']),
             relation('Energy Transfer', 'ET', 'parent', 'GP 100%·2026년 2월 LP 32% 소유 · 직접 거래와 다른 지배 역할', ANNUAL['USAC'])],
    'KGS': [relation('Caterpillar', 'CAT', 'supplier', '큰 왕복 가스 압축 엔진과 편입 발전기 fleet · 장비·인력 인증을 공식 발표', KGS_ENGINES),
            relation('Ariel', None, 'partner', '공식 Contract Compression 패키지 파트너 · 목록만으로 직접 구매액·독점 공급 계약은 확인하지 않음', ARIEL, 'ariel-compressors'),
            relation('Baker Hughes', 'BKR', 'supplier', '초기 약 1 GW 터빈·BRUSH 발전기 주문 · 2030년까지 공급, 현재 설치 완료 아님', KGS_BKR),
            relation('Kodiak Power Solutions / DPS', None, 'subsidiary', '2026년 4월 1일 DPS 인수 완료 후 발전 사업으로 편입·개칭', QUARTER['KGS'], 'kodiak-power')],
    'AROC': [relation('Ariel', None, 'partner', 'Ariel이 Archrock Services를 공식 Contract Compression 패키지 파트너로 등재 · 직접 구매액은 이 목록에 없음', ARIEL, 'ariel-compressors'),
             relation('National Gas Compression Systems', None, 'subsidiary', '2025년 5월 편입 · 큰 압축 장비·운영 고객 계약', QUARTER['AROC'], 'ngcs')],
}

PRIVATE = {}
for _key, _name, _business, _origin in [
    ('ariel-compressors', 'Ariel', '왕복 가스 압축기·프레임·실린더와 부품·서비스를 공급합니다. 압축 패키징·운영 업체를 공식 파트너 목록에 구분해 제공합니다.', ARIEL),
    ('permian-highway', 'Permian Highway Pipeline', 'Waha–Katy·Gulf/Mexico 시장을 연결하는 가스 배관입니다. Kinetik은 공동 지분을 보유하면서 demand fee를 지급하는 실제 수송 고객입니다.', ANNUAL['KNTK']),
    ('shin-oak', 'Breviloba / Shin Oak', 'Permian–Mont Belvieu NGL 배관입니다. Kinetik 33% 공동 지분과 capacity fee 지출, Enterprise 운영 역할이 구분됩니다.', ANNUAL['KNTK']),
    ('kogas', '한국가스공사', 'CQP Sabine Pass 장기 LNG 구매 고객입니다. 확인된 거래·비중은 CQP 고객 계약 매출 기준이며 한국 전체 가스 수요나 이 회사 전체 조달 비중이 아닙니다.', ANNUAL['CQP']),
    ('gail-india', 'GAIL (India)', 'CQP Sabine Pass 장기 LNG 구매 고객입니다. 공시에 실명과 2025년 고객 계약 매출 15%를 확인했습니다.', ANNUAL['CQP']),
    ('naturgy-lng', 'Naturgy LNG GOM', 'CQP Sabine Pass LNG 계약 법인입니다. 그룹 모회사와 계약 당사자를 구분하고 실명 법인 기준으로 연결합니다.', ANNUAL['CQP']),
    ('kodiak-power', 'Kodiak Power Solutions / DPS', '분산·수용가 내부 발전기를 공급·설치·운전·정비합니다. 2026년 4월 Kodiak이 DPS를 인수 완료한 뒤 편입 발전 사업으로 운영합니다.', QUARTER['KGS']),
    ('ngcs', 'National Gas Compression Systems', '천연가스 계약 압축 사업입니다. 2025년 5월 Archrock 편입으로 운영 fleet·고객 계약을 연결했습니다.', QUARTER['AROC']),
]:
    PRIVATE[_key] = profile(_name, _origin, _business, '', products=[('확인한 사업 역할', _business)])

# These are named components in the issuer's own supplier paragraph, not a
# generic list of brands that could theoretically be used in the industry.
for _key, _name, _part in [
    ('innio-waukesha', 'INNIO Waukesha', '가스 엔진'), ('teco-westinghouse', 'TECO-Westinghouse', '압축 장비 구동 장비'),
    ('air-x-changers', 'Air-X-Changers', '압축 패키지 냉각기'), ('alfa-laval-us', 'Alfa Laval (US)', '압축 패키지 냉각기'),
    ('axh-air-coolers', 'AXH air-coolers', '압축 패키지 냉각기'), ('eads-cooling', 'EADS Cooling Solutions', '압축 패키지 냉각기'),
    ('rr-engineering', 'R&R Engineering', '압축 패키지 냉각기'), ('cooper-gemini', 'Cooper Machinery Services / Gemini', '압축기 프레임·실린더'),
    ('arrow-engine', 'Arrow Engine Company', '압축기 프레임·실린더'), ('sec-energy', 'SEC Energy Products / Standard Equipment', '압축 패키지 조립'),
    ('jw-power', 'J-W Power', '압축기 제조·패키징·운영'),
]:
    _kind = 'subsidiary' if _key == 'jw-power' else 'supplier'
    _detail = ('2026년 1월 인수 완료 · 압축기 제조·운영 편입' if _key == 'jw-power'
               else 'USAC 연차보고서에 실명이 제시된 ' + _part + ' 공급')
    EDGES['USAC'].append(relation(_name, None, _kind, _detail, ANNUAL['USAC'], _key))
    PRIVATE[_key] = profile(_name, ANNUAL['USAC'], _detail, '', products=[(_part, '공급 금액·독점 여부·제품별 전체 고객 목록은 이 자료에서 제시하지 않습니다.')])
EDGES['USAC'].append(relation('Ariel', None, 'supplier', '표준 압축기 프레임·실린더의 주 공급사', ANNUAL['USAC'], 'ariel-compressors'))

for _symbol, _rows in EDGES.items():
    for _edge in _rows:
        if _edge['registry_id'] in PRIVATE:
            PRIVATE[_edge['registry_id']]['relations'].append(relation(PUBLIC[_symbol]['name'], _symbol,
                {'subsidiary': 'parent', 'supplier': 'customer', 'customer': 'supplier', 'partner': 'partner'}[_edge['kind']],
                _edge['detail'], _edge['source']))
