"""Reviewed semiconductor equipment/materials businesses and explicit trade links.

Product descriptions have their own issuer source. A supplier-list entry proves
inclusion at publication, never the exact product purchased or current contract.
Foreign/unlisted entities use registry IDs; Korean tickers were checked against
the official KIS KOSPI/KOSDAQ masters on 2026-10-02.
"""
from .company_research_notes import profile, relation, source

READ_DATE = '열람 2026-10-02'
SAMSUNG_LIST = source('Samsung Electronics · 공식 공급사 명단 · 발행일 미표기',
    'https://www.samsung.com/global/sustainability/policy-file/AYVhOfYaBGoAIx95/Supplier_List.pdf', READ_DATE)
WONIK_IPS = source('원익IPS · SEMICON Europa 2025 기업 제출 소개',
    'https://expo.semi.org/europa2025/public/eBooth.aspx?BoothID=656491&FromPage=Exhibitors.aspx&IndexInList=76&ListByBooth=true&ParentBoothID=', '2025')
DONGJIN_SITES = source('동진쎄미켐 · 해외 사업장·고객 공급 설명',
    'https://www.dongjin.com/en/company/be_overseas.php', READ_DATE)
ASML_ENTITIES = source('ASML · 2025 국가별 법인·활동 보고',
    'https://ourbrand.asml.com/m/44bf04d7ecacdbb6/original/asml-2025-public-country-by-country-report.pdf', '2025')
TOKAM = source('TOK · 한국 평택 공장 준공 발표',
    'https://www.tok.co.jp/eng/news/2026/260915', '2026-09-15')


def business(name, url, description, revenue, products, customers='', inputs=''):
    return profile(name, source(name+' · 공식 제품·사업 소개', url, READ_DATE),
                   description, revenue, products, customers, inputs)


PUBLIC = {
    'CRUS': business('Cirrus Logic', 'https://investor.cirrus.com/company-overview/default.aspx',
        '기기의 오디오·진동·카메라·전력 기능을 처리하는 저전력 혼합 신호 반도체와 관련 소프트웨어를 제공합니다.',
        '맞춤·반맞춤·일반 판매용 IC와 관련 소프트웨어·알고리즘을 고객 기기에 통합합니다.',
        [('오디오', '코덱·스마트 코덱·증폭기·DSP와 음성·잡음 제거 알고리즘'),
         ('혼합 신호', '햅틱 드라이버·센싱, 카메라 제어, 배터리·전력 IC')],
        '스마트폰·태블릿·웨어러블·노트북·AR/VR 등의 기기 제조사가 제품을 사용합니다.'),
    'ENTG': business('Entegris', 'https://www.entegris.com/en/home/products.html',
        '반도체 공정 소재와 오염 제어·소재 취급 제품을 공급합니다. 미세 입자·불순물을 줄이고 화학물질·웨이퍼를 안전하게 다루는 공정에 참여합니다.',
        '소재·필터·정제·공급·운반 제품과 관련 지원 서비스가 제품 범위입니다.',
        [('공정 소재', '전구체·세정액·슬러리·특수가스'),
         ('오염·유체 제어', '가스·액체 필터와 정제기, 밸브·튜브·공급·계측 장치'),
         ('웨이퍼 취급', 'FOUP·웨이퍼 운반 용기·레티클 보관 용기')],
        '로직·메모리 제조사, 반도체 장비 업체와 화학 소재 공급사가 고객 분야입니다.'),
    'STM': business('STMicroelectronics', 'https://www.st.com/content/st_com/en/browse/product-portfolio.html',
        '전자기기의 연산·제어·감지·통신·전력 변환을 담당하는 반도체를 제공합니다.',
        '마이크로컨트롤러·전력·아날로그·센서·연결 반도체 등 제품별 공급을 구분합니다.',
        [('제어·연결', '마이크로컨트롤러·프로세서·RF·보안 반도체'),
         ('전력·아날로그', '전력 소자·모터 구동·전원 관리·아날로그 IC'),
         ('센서', 'MEMS·움직임·환경·거리 센서와 마이크로액추에이터')],
        '자동차·산업·개인 전자기기·통신·컴퓨팅 등의 시스템에 사용됩니다.'),
    '353200.KS': business('대덕전자', 'https://www.daeduck.com/ko/content/pkg.do',
        '반도체 칩을 기판·시스템에 연결하는 패키지 기판과 통신 장비용 다층 인쇄회로기판(MLB)을 제조합니다.',
        'CPU·ASIC·메모리·통신 제품에 쓰이는 패키지 기판을 판매합니다. 칩 자체를 설계·제조하는 회사와 구분합니다.',
        [('패키지 기판', 'FCBGA·FCCSP·CSP·SiP·AiP·FCBOC. 칩의 전기 연결·지지·보호 역할.'),
         ('적용 제품', '데이터센터 프로세서·자동차 MPU·통신 칩·모바일 AP·DRAM 등')],
        '반도체 패키징과 전자 시스템에서 기판을 사용하는 고객이 대상입니다.',
        '미세 회로·다층 적층·범프 연결·기판 휨 제어와 고객 제품에 맞는 신뢰성이 핵심 제조 조건입니다.'),
    '005290.KQ': business('동진쎄미켐', 'https://www.dongjin.com/business/semiconductor.php',
        '반도체 회로 형성·연마·증착 등에 사용하는 전자재료를 개발·제조합니다. 여기서는 반도체 소재 사업을 정리합니다.',
        '반도체 제조 공정에 사용하는 감광액·공정 보조 재료·습식 화학제품 등을 공급합니다.',
        [('노광 재료', '포토레지스트, 희석제·박리액, 반사 방지 하부막(BARC), 스핀 코팅 탄소막(SOC)'),
         ('공정 소재', 'CMP 슬러리·전구체 등')],
        '반도체 제조사가 웨이퍼에 회로를 형성하고 소재를 제거·가공할 때 사용합니다.',
        '공정별 감광·식각·연마 특성과 원료 정제·불순물 관리, 고객 공정과의 적합성이 연결됩니다.'),
    '240810.KQ': profile('원익IPS', WONIK_IPS,
        '반도체·디스플레이 제조 장비 업체입니다. 웨이퍼 위에 얇은 막을 쌓는 증착 장비와 확산·열처리 장비를 제공합니다.',
        'GEMINI·QUANTA·NOA·HyEta 증착 장비, 300series·LEVATA 열처리·확산 장비 등이 제품 기반입니다.',
        [('증착', 'PECVD·CVD·ALD. DRAM·NAND·로직의 절연막·금속막 형성'),
         ('확산·열처리', '산화·어닐·실리콘 성장 등 웨이퍼 공정')],
        '2025년 기업 제출 자료가 Samsung Electronics·SK hynix와의 양산 협력 및 GlobalFoundries·CXMT를 명시합니다.',
        '고객 공정에 맞는 막 두께·균일도·재료와 장비 설치·양산 지원이 연결됩니다.'),
    '104830.KQ': business('원익머트리얼즈', 'https://www.wimco.co.kr/kr/company/about',
        '반도체·디스플레이용 특수가스와 산업용 가스를 제조·정제·충전·판매합니다.',
        'NH₃·N₂O·C₃H₆·PH₃ 혼합가스 등을 공급합니다. 공정 가스 소모에 연결되는 소재 사업입니다.',
        [('특수가스', '반도체·디스플레이용 고순도 공정 가스'),
         ('제조·공급', '국내 생산 거점과 미국·중국 법인 운영')],
        '국내외 반도체·디스플레이 제조사가 고객입니다.',
        '가스 원료의 조달·정제·충전, 고순도 유지와 안전한 공급이 사업의 기반입니다.'),
    '030530.KQ': business('원익홀딩스', 'https://www.wonikholdings.kr/biz_02.do',
        '반도체·디스플레이 공정에 가스를 공급·정제·처리하는 장치를 제공합니다. 원익IPS·원익머트리얼즈와는 별도 법인입니다.',
        '가스 공급 시스템, 정제 장치와 배기가스 처리 솔루션을 제공합니다. 이 소개는 자체 장비 사업의 범위입니다.',
        [('공급 장치', '기체·액체·고체 전구체를 공정 조건에 맞게 공급'),
         ('정제·배기 처리', '불순물 제거용 정제 시스템과 열·플라즈마·촉매 방식 스크러버')],
        '반도체·디스플레이·태양전지 등의 공정 사업장이 사용합니다.',
        '가스별 온도·압력·순도, 밀폐·안전과 부산물 처리 조건에 맞춘 설계가 필요합니다.'),
    '319660.KQ': business('피에스케이', 'https://www.pskinc.com/index.php?lang=en',
        '웨이퍼 표면의 감광막·잔여물 등을 제거하는 반도체 전공정 장비를 제공합니다.',
        'Dry strip·dry cleaning·hard mask strip·wafer edge clean 장비가 제품군입니다. PSK Holdings와는 별도 회사입니다.',
        [('막 제거', 'SUPRA 감광막 제거, OMNIS 하드마스크 제거'),
         ('세정', 'INTEGER 건식 세정, PRECIA 웨이퍼 가장자리 세정')],
        '반도체 제조 공정의 표면 처리·세정 단계에서 장비를 사용합니다.',
        '제거할 막과 하부 재료의 선택비, 공정 온도·화학 조건과 장비 운용이 연결됩니다.'),
    '357780.KQ': business('솔브레인', 'https://www.soulbrain.co.kr/en/m21.php',
        '반도체 식각·세정·연마·증착용 화학 소재를 공급합니다. 디스플레이·이차전지 소재도 제품 범위에 포함됩니다.',
        '제조 공정에서 사용하는 화학 소재 판매가 기반입니다. 솔브레인홀딩스와 구분한 사업회사입니다.',
        [('식각·세정', '식각액·HF/BOE·세정액·박리액'),
         ('연마·증착', 'CMP 슬러리, CVD·ALD용 전구체')],
        '반도체·디스플레이 등 소재를 사용해 제품을 제조하는 고객이 대상입니다.',
        '소재 순도·선택비·미세 공정 적합성과 고객 생산 조건을 맞추는 것이 공급의 기반입니다.'),
    '232140.KQ': business('와이씨 · YC', 'https://yccorp.com/kr/company/summary.php',
        '반도체 메모리 검사장비를 개발·제작·판매합니다. 검사 대상 메모리를 만드는 제조사와 구분합니다.',
        '메모리 검사 시스템과 관련 기술을 제공합니다. 와이씨켐(112290)과는 다른 회사입니다.',
        [('메모리 검사장비', '양산용 반도체 테스트 장비 개발·제조')],
        '메모리의 전기적 특성·기능을 검사하는 반도체 생산 공정이 사용처입니다.'),
    '009150.KS': business('삼성전기', 'https://m.samsungsem.com/kr/index.do',
        '전자제품에 쓰이는 적층세라믹커패시터(MLCC), 카메라 모듈과 반도체 패키지 기판을 제공합니다.',
        '수동부품·광학 모듈·패키지 기판 판매가 사업 기반입니다. 삼성전자와 별도 상장회사입니다.',
        [('MLCC', '전원·신호 회로의 전기 저장·공급·잡음 제어 부품'),
         ('모듈·기판', '카메라 모듈과 칩 연결용 패키지 기판')]),
}

PRIVATE = {
    'kyec': business('King Yuan Electronics · KYEC', 'https://www.kyec.com.tw/en/About/company-profile',
        '반도체 칩의 전기적 동작을 검사하는 테스트 전문 기업입니다.',
        '웨이퍼 프로빙, 패키징 후 최종 검사, 번인과 시스템 레벨 테스트 서비스를 제공합니다.',
        [('웨이퍼·최종 검사', '패키징 전·후 칩의 동작·성능 검사'), ('번인·SLT', '스트레스 조건과 실제 시스템 환경에서 검사')],
        '팹리스·종합 반도체 제조사·파운드리가 검사 서비스를 이용합니다.',
        '테스터·프로브카드·소켓, 테스트 프로그램과 냉각·전력·장비 가동 능력이 연결됩니다.'),
    'tongfu': business('Tongfu Microelectronics', 'https://expo.semi.org/china2025/public/eBooth.aspx?BoothID=601605&FromPage=Exhibitors.aspx&IndexInList=1216&ListByBooth=true&Nav=False&ParentBoothID=',
        '반도체 패키징과 테스트를 외부 고객에게 제공하는 OSAT 기업입니다.',
        '리드프레임·기판·플립칩·웨이퍼 레벨 패키징과 웨이퍼 프로빙·최종 테스트를 제공합니다.',
        [('패키징', '리드프레임·기판·플립칩·웨이퍼 레벨 기술'), ('검사', '엔지니어링 테스트·웨이퍼 프로빙·최종 테스트')]),
    'asm-international': business('ASM International', 'https://www.asm.com/our-technology-products/epitaxy',
        '반도체 웨이퍼 위에 원자 단위의 박막·결정층을 형성하는 증착 장비를 제공합니다.',
        'ALD·에피택시·PECVD·수직로와 관련 서비스가 제품·서비스 범위입니다.',
        [('증착', 'ALD·PECVD와 실리콘·SiGe·SiC 에피택시'), ('열 공정', '확산·산화·LPCVD용 수직로')],
        '로직·메모리·전력 반도체 제조 공정이 적용처입니다.'),
    'asml-netherlands': profile('ASML Netherlands B.V.', ASML_ENTITIES,
        'ASML 그룹의 네덜란드 운영 법인입니다. 공식 법인별 보고에 연구개발·제조·판매·서비스 활동이 기재되어 있습니다.',
        '운영 법인의 제조·판매·서비스 범위를 표시합니다. 상장 모회사 ASML Holding 전체 매출과 동일시하지 않습니다.',
        [('운영 범위', '연구개발·구매·제조·판매·서비스')]),
    'tokyo-electron': business('Tokyo Electron', 'https://www.tel.com/product/all/',
        '반도체 회로를 형성하는 도포·현상·식각·증착·세정·열처리 등의 공정 장비를 제공합니다.',
        '공정별 장비 플랫폼을 반도체 생산 현장에 공급합니다.',
        [('회로 형성', '도포·현상, 플라즈마 식각, 증착·열처리'), ('표면 처리·검사', '세정 시스템·웨이퍼 프로버 등')]),
    'globalwafers': business('GlobalWafers', 'https://www.sas-globalwafers.com/en/products/',
        '반도체 칩을 만드는 기초 소재인 웨이퍼를 공급합니다.',
        '실리콘 잉곳·연마 웨이퍼·에피택셜 웨이퍼·SOI 등 규격별 소재를 판매합니다.',
        [('웨이퍼', '연마·에피택셜·SOI 등 반도체용 기판'), ('원재료 가공', '실리콘 잉곳과 웨이퍼 가공')]),
    'edwards': business('Edwards', 'https://www.edwardsvacuum.com/en-us/semiconductor',
        '반도체 공정의 진공을 만들고 배기가스를 처리하는 장비·서비스를 제공합니다.',
        '진공 펌프·가스 저감 장치와 유지·지원 서비스가 사업 범위입니다.',
        [('진공', '공정 챔버의 진공 유지용 펌프'), ('배기가스', '공정 부산물·유해가스 처리와 관련 서비스')]),
    'ebara': business('Ebara', 'https://www.ebara.com/global-en/precision/',
        '펌프 등 산업 장비를 운영하며 반도체 분야에서는 표면 연마와 진공·배기가스 관련 설비를 제공합니다.',
        '반도체 사업 범위는 CMP·건식 진공펌프·가스 저감 장치·오존수 발생기와 지원 서비스입니다.',
        [('표면 연마', '웨이퍼 표면 평탄화를 위한 CMP'), ('공정 환경', '진공펌프·배기가스 처리·오존수 발생기')]),
    'advantest': business('Advantest', 'https://www.advantest.com/en/products/',
        'SoC·메모리 등의 반도체가 설계한 대로 동작하는지 확인하는 테스트 장비·소프트웨어를 제공합니다.',
        '자동 시험 장비, 핸들러·인터페이스 등 주변 장치와 소프트웨어·시스템 테스트가 제품 범위입니다.',
        [('테스터', 'SoC·메모리 성능·품질 시험'), ('주변 장치·소프트웨어', '핸들러·인터페이스·테스트 데이터·설계 검증')]),
    'air-liquide': business('Air Liquide', 'https://www.airliquide.com/group/activities/electronics',
        '산업용 가스 그룹이며 전자 사업에서 반도체용 고순도 가스와 첨단 소재를 제공합니다.',
        '가스·소재를 벌크·배관·고객 현장 생산 방식 등으로 공급합니다. 이 정리는 전자 사업에 초점을 맞춥니다.',
        [('가스·소재', '반도체 공정용 고순도 가스와 첨단 재료'), ('공급 방식', '벌크·배관·현장 전용 생산설비')]),
    'mediatek': business('MediaTek', 'https://www.mediatek.com/products/smartphones',
        '모바일 기기의 연산·통신 등을 통합하는 반도체를 제공합니다.',
        'Dimensity·Helio 등 스마트폰용 칩·플랫폼을 기기 제조사에 공급합니다.',
        [('모바일 SoC', '연산·그래픽·통신·카메라 등 기능을 통합한 스마트폰 칩')]),
    'murata': business('Murata Manufacturing', 'https://www.murata.com/products',
        '전자 회로에 들어가는 커패시터·인덕터·필터·센서와 무선 연결 모듈 등을 제공합니다.',
        '전자 부품·모듈·전원 관련 제품 공급이 사업 기반입니다.',
        [('수동·RF 부품', '커패시터·인덕터·필터·RF 스위치·프런트엔드 모듈'),
         ('센서·연결', '센서·타이밍 부품·무선 연결 모듈·전원 제품')]),
    'tdk': business('TDK', 'https://product.tdk.com/en/products/index.html',
        '전자·자성 재료 기술을 바탕으로 수동부품·센서·전원·배터리 관련 제품을 제공합니다.',
        '커패시터·코일·자성 부품·센서·전원 및 저장장치 관련 제품을 공급합니다.',
        [('회로 부품', '커패시터·인덕터·EMC·RF 부품·자석'), ('시스템 부품', '센서·전원·배터리·HDD 헤드 등')]),
    'tok-advanced-materials': profile('TOK Advanced Materials · 티오케이첨단재료', TOKAM,
        '한국에서 포토레지스트를 연구개발·제조·판매하는 TOK 계열 소재 기업입니다.',
        '포토레지스트 공급과 고순도 화학제품 생산 기반을 운영·확장합니다. 평택 신공장은 2026-09 준공, 가동은 2027년 상반기 계획입니다.',
        [('포토레지스트', '반도체 회로 패턴 형성용 감광 재료'), ('고순도 화학제품', '평택 생산동 준공 후 가동 예정')],
        '한국 반도체 고객 가까이에서 소재를 생산·공급하는 사업 모델입니다.'),
    'semes': business('세메스 · SEMES', 'https://www.semes.com/',
        '반도체 전공정·후공정 장비와 디스플레이·물류 자동화 설비를 개발·생산합니다.',
        '세정·포토트랙·식각·테스트·패키징 등 공정 장비 공급이 사업 범위입니다.',
        [('전공정', '웨이퍼 세정·포토트랙·식각'), ('후공정·자동화', '테스트·패키징과 제조 현장 물류 자동화')]),
    'samsung-display': business('삼성디스플레이', 'https://www.samsungdisplay.com/eng/tech/oled-display.jsp',
        '전자기기 화면에 사용하는 OLED 디스플레이를 제공합니다.',
        '완제품용 디스플레이 패널·기술을 공급합니다. TV·스마트폰 완제품 판매와는 범위가 다릅니다.',
        [('OLED', '스마트폰·노트북·태블릿 등의 화면용 디스플레이')]),
}

# Supplier membership and the supplier's own product scope are separate facts.
SAMSUNG_SUPPLIERS = [
    ('Analog Devices', 'ADI', None), ('Advantest', None, 'advantest'),
    ('Air Liquide', None, 'air-liquide'), ('Air Products', 'APD', None),
    ('Applied Materials', 'AMAT', None), ('ASM International', None, 'asm-international'),
    ('ASML Netherlands B.V.', None, 'asml-netherlands'), ('Cirrus Logic', 'CRUS', None),
    ('대덕전자', '353200.KS', None), ('동진쎄미켐', '005290.KQ', None),
    ('Ebara', None, 'ebara'), ('Edwards', None, 'edwards'), ('Entegris', 'ENTG', None),
    ('GlobalWafers', None, 'globalwafers'), ('Intel', 'INTC', None), ('KLA', 'KLAC', None),
    ('Lam Research', 'LRCX', None), ('Linde', 'LIN', None), ('MediaTek', None, 'mediatek'),
    ('Micron', 'MU', None), ('Murata Manufacturing', None, 'murata'), ('NXP', 'NXPI', None),
    ('피에스케이', '319660.KQ', None), ('Qorvo', 'QRVO', None),
    ('삼성디스플레이', None, 'samsung-display'), ('삼성전기', '009150.KS', None),
    ('세메스', None, 'semes'), ('솔브레인', '357780.KQ', None), ('STMicroelectronics', 'STM', None),
    ('TDK', None, 'tdk'), ('Texas Instruments', 'TXN', None),
    ('TOK Advanced Materials', None, 'tok-advanced-materials'), ('Tokyo Electron', None, 'tokyo-electron'),
    ('원익홀딩스', '030530.KQ', None), ('원익IPS', '240810.KQ', None),
    ('원익머트리얼즈', '104830.KQ', None), ('와이씨', '232140.KQ', None),
]
EDGES = {'005930.KS': [relation(name, symbol, 'supplier',
    '공식 공급사 명단 등재 · 발행 시점 기준', SAMSUNG_LIST, key)
    for name, symbol, key in SAMSUNG_SUPPLIERS]}
PUBLIC['005930.KS'] = {'name': '삼성전자', 'facts': [dict(
    title='공식 공급사 목록의 범위', source=SAMSUNG_LIST,
    detail='공개에 동의한 부품·제조 외주 업체 목록으로, 발행 당시 소재·제조 조달 지출의 80%를 포괄합니다. '
           '문서에 발행일은 없습니다. 개별 공급액·현재 계약·납품 제품은 이 명단으로 확정하지 않습니다. '
           '연결 기업의 제품 소개는 해당 업체의 별도 공식 자료입니다.')], 'relations': []}
EDGES['005290.KQ'] = [relation('Samsung Electronics', '005930.KS', 'customer',
    '시안 공장용 반도체 화학재료와 Texas 시설용 희석제 공급을 해외 사업장 소개에 명시.', DONGJIN_SITES)]
EDGES['240810.KQ'] = [relation(name, symbol, 'customer',
    '2025년 기업 제출 소개에 공정 장비의 양산 협력·공급 대상 기업으로 명시.', WONIK_IPS)
    for name, symbol in [('Samsung Electronics', '005930.KS'), ('SK hynix', '000660.KS'), ('GlobalFoundries', 'GFS')]]
PRIVATE['asml-netherlands']['relations'].append(relation('ASML Holding', 'ASML', 'parent',
    '2025년 그룹 법인별 활동 보고에 포함된 운영 법인.', ASML_ENTITIES))

# Extra product fields keep their own evidence, not the supplier-list source.
PUBLIC['353200.KS']['products'].append(dict(title='MLB · 통신용 다층 기판',
    detail='유선 네트워크 스위치·라우터와 광통신 모듈에 쓰이는 다층 PCB.',
    source=source('대덕전자 · MLB 제품', 'https://www.daeduck.com/ko/content/mlb.do', READ_DATE)))
PUBLIC['104830.KQ']['products'].append(dict(title='공정별 가스',
    detail='증착·확산, 식각·세정, 이온 주입·도핑, 엑시머 레이저용 가스를 구분합니다.',
    source=source('원익머트리얼즈 · 반도체 가스', 'https://www.wimco.co.kr/kr/product/semiconductor', READ_DATE)))
PUBLIC['232140.KQ']['products'] = [dict(title='웨이퍼 메모리 검사',
    detail='NAND용 MT6122와 DRAM용 MT6133·MT6135S·MT8311.',
    source=source('와이씨 · 제품 소개', 'https://yccorp.com/kr/product/product_list.php', READ_DATE)),
    dict(title='설치·유지보수·개조', detail='장비 설치·이설, 부품 수리·교체·판매, 소프트웨어 갱신·개조와 고객 교육.',
    source=source('와이씨 · 고객 지원', 'https://yccorp.com/kr/product/customer.php', READ_DATE))]
PUBLIC['009150.KS']['products'][0]['source'] = source('삼성전기 · MLCC 제품·원리',
    'https://www.samsungsem.com/kr/product/passive-component/mlcc.do', READ_DATE)
PRIVATE['samsung-display']['products'].append(dict(title='QD-OLED',
    detail='TV·모니터용 퀀텀닷 기반 자발광 디스플레이.',
    source=source('삼성디스플레이 · QD-OLED', 'https://www.samsungdisplay.com/eng/tech/quantum-dot.jsp', READ_DATE)))
