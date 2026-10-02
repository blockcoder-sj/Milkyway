"""Reviewed refining business notes and actual operating relationships.

Annual/quarterly figures stay in the evidence catalog. Counterparty pages cover
the documented role, not an unresearched claim of complete company coverage.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

MPC, PSX, DINO = (report(symbol) for symbol in ('MPC', 'PSX', 'DINO'))
MPC_Q, PSX_Q, DINO_Q = (report(symbol, 'quarter') for symbol in ('MPC', 'PSX', 'DINO'))
DINO_BASE = source('HF Sinclair · Chevron·SK Enmove 기유 공급 계약',
    'https://www.hfsinclair.com/investor-relations/press-releases/Press-Release-Details/2026/HF-Sinclairs-Lubricants--Specialties-Segment-Establishes-Strategic-Base-Oil-Supply-Network-Through-Agreements-with-SK-Enmove-and-Chevron/default.aspx', '2026-08-03')
PSX_SAF = source('Phillips 66 · 항공연료 공급 구조',
    'https://www.phillips66.com/newsroom/delivering-the-molecule-and-the-math/', '2026-04-15')
PSX_CORRIDOR = source('Phillips 66 · 미국 중부 생산·판매 연결망',
    'https://www.phillips66.com/newsroom/today-tomorrow-central-corridor/', '2026-10-01')
DHL_SAF = source('DHL · Phillips 66 SAF 구매 계약',
    'https://group.dhl.com/en/media-relations/press-releases/2025/dhl-express-and-phillips-66-advance-sustainable-aviation-fuel-usage.html', '2025-11-18')
LIN_H2 = source('Linde · Sweeny 수소 공급 개시',
    'https://www.linde.com/news-and-media/2021/linde-starts-up-major-new-hydrogen-facility-in-the-u-s-gulf-coast', '2021-10-21')
SPEEDWAY = source('미국 FTC · Speedway 인수·연료 공급 계약',
    'https://public-inspection.federalregister.gov/2021-15350.pdf', '2021-07-20')

PUBLIC = {
    'MPC': profile('Marathon Petroleum', MPC,
        '원유를 정제하고 연료를 유통하는 미국 하류·물류 기업입니다. 정유·판매, MPLX 중심의 물류·가스처리, 재생 디젤의 세 보고 부문으로 구성됩니다. 원유를 생산하는 Marathon Oil과 별개 회사입니다.',
        '2025년 연결 매출은 1,326억9,900만 달러입니다. 외부 고객 기준 정유·판매 1,242억5,200만, 물류·가스처리 56억2,800만, 재생 디젤 28억1,400만, 기타 500만 달러입니다. 물류 부문의 내부거래를 더하면 연결 매출과 중복됩니다.',
        [('휘발유·경유·항공유', '정유소에서 생산하거나 구매한 제품을 도매·현물·수출 및 브랜드 판매망에 공급합니다.'),
         ('물류·가스처리·NGL', 'MPLX의 집하·가스처리·분별과 원유·제품 파이프라인, 터미널·저장·선박 서비스가 포함됩니다.'),
         ('재생 디젤', 'Dickinson 자체 공장과 Neste와의 Martinez 공동사업, 농산물 원료의 집하·전처리를 연결합니다.'),
         ('아스팔트·석유화학 원료', '도로·지붕용 아스팔트, 프로필렌·방향족, 프로판과 코크스 등을 산업 고객에 판매합니다.')],
        customers='도매업자, 독립 Marathon 주유소 운영자, ARCO 직접 계약 판매점, 산업·수출 고객이 판매 경로입니다. 주유소의 브랜드와 소유주는 다를 수 있습니다.',
        inputs='정유용 원유는 국내외에서 구매합니다. 원유 품질·운임, 수소·에너지, 계획 정비와 물류 가용성이 공장 운영에 연결됩니다. 재생 디젤에는 옥수수유·대두유·지방·폐유지와 전처리 설비가 필요합니다.',
        competition='공시의 경쟁 범위는 원유·재생원료 조달, 도매·현물·브랜드 연료 공급, 물류·가스처리입니다. 물류는 연결 지역·수수료·신뢰성, 연료는 도달 시장·유통비·제품 구성에 따라 경쟁 상대가 달라집니다.'),
    'PSX': profile('Phillips 66', PSX,
        '정유소·가스처리·물류망·연료 판매망을 연결하는 에너지 기업입니다. 물류, 화학, 정유, 판매·특수제품, 재생연료의 다섯 보고 부문을 운영합니다. 화학 사업은 Chevron과 공동 보유한 CPChem에 대한 지분법 투자입니다.',
        '2025년 연결 매출은 1,323억7,600만 달러입니다. 제품별로 정유제품·재생연료 973억5,900만, 매입 원유 재판매 151억8,300만, NGL·천연가스 170억6,600만, 서비스·기타 27억6,800만 달러입니다. CPChem 전체 매출을 이 연결 매출에 더하지 않습니다.',
        [('정유·연료 판매', '휘발유·경유·항공유를 생산·구매해 판매합니다. 자체 정유소에서 판매 부문으로 넘기는 물량은 내부거래입니다.'),
         ('천연가스·NGL·LPG 물류', '집하·가스처리·분별·저장·파이프라인과 LPG 수출을 연결합니다.'),
         ('석유화학·플라스틱', 'CPChem이 에틸렌·폴리에틸렌·알파올레핀·방향족·특수화학 제품 등을 제조합니다.'),
         ('재생 디젤·SAF', 'Rodeo와 Humber의 생산·원료 조달·판매 사업입니다. 미혼합 SAF와 기존 항공유를 혼합해 사용하는 항공연료를 구별합니다.'),
         ('기유·윤활유', '판매·특수제품 부문에서 기유와 윤활유를 제조·유통합니다.')],
        customers='미국·유럽의 연료 도매·브랜드 판매망, 항공·산업 고객과 LPG 수출 시장을 대상으로 합니다. 정유와 판매 부문 사이의 거래가 커서 두 부문 총매출의 단순 합계는 회사 외부 매출을 나타내지 않습니다.',
        inputs='정유 원유·기타 원료를 외부에서 구매하며, 물류 사업에는 공급 지역의 가스 생산량과 가스·NGL 운송·처리 연결망이 필요합니다. 재생연료는 폐식용유·식물성 기름·동물성 지방 등을 사용합니다.',
        competition='정유·화학·재생연료는 원료 확보, 제품·비용·설비 효율로 경쟁합니다. 판매는 가격·공급 신뢰성·서비스·브랜드, 물류는 수수료·고객과 거점까지의 연결이 공시된 경쟁 요소입니다.'),
    'DINO': profile('HF Sinclair', DINO,
        '미국 중부·서부 정유소와 Sinclair 브랜드 연료 판매망, 윤활유·특수제품, 재생 디젤 및 물류 사업을 운영합니다. 원유를 직접 생산하는 회사가 아니라 구매한 원료를 가공·유통하는 회사입니다.',
        '2025년 연결 매출은 268억6,900만 달러입니다. 외부 고객 기준 정유 205억3,600만, 재생연료 5억5,100만, 브랜드 판매 31억4,200만, 윤활유·특수제품 25억1,900만, 물류 1억2,100만 달러입니다. 제품 소계와 하위 제품 매출은 중복 합산하지 않습니다.',
        [('수송용 연료·아스팔트', '휘발유·경유·항공유와 도로·건설용 아스팔트를 제조·판매합니다.'),
         ('재생 디젤', 'Cheyenne·Artesia·Sinclair 공장에서 대두유 등 재생원료를 가공합니다. Artesia 전처리 설비와 인접 정유소 수소 설비를 활용합니다.'),
         ('윤활유·특수제품', 'Petro-Canada Lubricants, Red Giant Oil, Sonneborn과 Tulsa 사업이 기유·윤활유·백유·왁스 등을 제공합니다.'),
         ('Sinclair 브랜드·물류', '독립 판매점에 연료·브랜드를 제공하고, 원유·제품 파이프라인·탱크·터미널을 운영합니다.')],
        customers='다른 정유사, 독립 판매점·편의점·트럭 정차장, 도매상·철도·항공 고객 등이 구매합니다. 2025년 어느 고객도 연결 매출의 10% 이상이 아니었습니다. 과거 Shell 관련 매출 비중을 2025년 비중으로 표시하지 않습니다.',
        inputs='대부분의 원유·재생원료를 구매합니다. 캐나다·미국 내륙·Alaska 원유를 파이프라인·선박·트럭으로 받으며, 윤활유에는 기유와 가공·배합·포장 공정이 필요합니다. 원료 공급사와 운송 서비스를 제공하는 회사를 구별합니다.',
        competition='El Dorado는 미국 Plains·Rocky Mountains 수요처에 공급하는 Gulf Coast 정유사와도 경쟁합니다. 생산원가뿐 아니라 해당 시장까지의 제품 운임이 경쟁 조건입니다. 공시에 이름이 없는 업체를 확정 경쟁사로 만들지 않습니다.'),
    'MPLX': profile('MPLX', MPC_Q,
        'Marathon Petroleum이 연결하는 상장 물류 MLP입니다. 정유소 물류와 원유·연료 운송·저장, 천연가스 집하·처리·NGL 분별 사업을 운영합니다. 이 페이지의 추가 설명은 모회사 공시에서 확인한 역할 범위입니다.',
        'MPC와 외부 고객에게 물류·처리 서비스를 제공합니다. MPC 연결 물류 부문 매출은 MPLX 자체 공시 매출과 범위가 같다고 가정할 수 없습니다.',
        [('정유소·제품 물류', '파이프라인·터미널·저장·예인선·바지선 등을 통해 MPC의 연료 공급망을 지원합니다.'),
         ('가스·NGL 처리', '가스 집하·처리와 NGL 분별·운송을 연결합니다.')]),
}

PUBLIC['MPC']['brief'] += [
    fact('정유 설비와 실제 처리량', '2025년 공시의 원유 정제능력은 하루 298만6,000배럴입니다. 같은 해 평균 원유 투입은 하루 278만7,000배럴, 기타 투입·혼합 원료는 20만2,000배럴입니다. 원유 능력·총 투입량·제품 판매량은 서로 다른 수치입니다.', MPC),
    fact('재생원료부터 연료까지', 'Green Bison은 ADM 75%·MPC 25% 공동사업으로 대두유를 MPC에 독점 공급합니다. 정제 대두유 능력은 연간 약 6억 파운드입니다. Dickinson의 재생 디젤 능력은 연간 1억8,400만 갤런, Martinez 공동사업 전체 능력은 7억3,000만 갤런입니다.', MPC),
    fact('MPLX의 연결 범위', '2026년 6월 말 MPC는 MPLX 일반 파트너를 소유하고 보통 지분 약 64%를 보유했습니다. MPLX는 2025년 7월 BANGL 잔여 지분 55%를 인수해 100% 소유하게 됐습니다. 자회사 지분과 고객 거래 관계를 함께 구별합니다.', MPC_Q),
    fact('2026년 정비 영향', 'Martinez 공동사업은 2026년 1분기 계획 정비를 진행했습니다. 상반기 재생 디젤 판매량·가동률 변화를 설명할 때 이 정비 기간을 반영하며, 설비능력을 실제 생산량으로 표시하지 않습니다.', MPC_Q),
    fact('Speedway와 연료 판매', '2021년 Speedway 점포 매각과 함께 7-Eleven과 15년 연료 공급 계약을 체결했습니다. 발표된 연간 기준 물량은 약 77억 갤런으로, 당해 실제 인도량이나 현재 회사 소유 점포 수를 뜻하지 않습니다.', SPEEDWAY),
]
PUBLIC['PSX']['brief'] += [
    fact('정유소·물류·판매의 연결', '2025년 말 공시 대상 정유소는 미국·유럽 10곳이며 회사 지분 귀속 원유 처리능력은 하루 194만8,000배럴입니다. 2026년 1월 1일 기준은 199만3,000배럴로 제시했습니다. 공동사업 공장 전체 능력과 회사 귀속 능력을 구분합니다.', PSX),
    fact('WRB 소유 변경', '2025년 10월 1일 Cenovus로부터 WRB 나머지 지분 50%를 인수했습니다. Wood River·Borger는 이후 전액 연결되며, Cenovus를 현재 WRB 공동 소유자로 표시하지 않습니다.', PSX),
    fact('Los Angeles 생산 중단', '2025년 4분기에 연료 생산을 중단했습니다. 2026년 2분기 공시 시점에는 시설 유휴화와 재개발 인허가 검토가 진행 중이었습니다. 이 시설을 정상 가동 정유소에 다시 더하지 않습니다.', PSX_Q),
    fact('CPChem의 매출이 표에 없는 이유', '화학 부문은 CPChem의 50% 지분법 투자입니다. 2025년 지분법 이익 2억9,700만 달러는 Phillips 66의 고객 매출과 다른 손익 항목입니다. 지분 비율을 제품 시장점유율로 사용할 수 없습니다.', PSX),
    fact('재생연료 공정 규모', 'Rodeo는 연간 약 8억 갤런의 재생원료 처리능력과 약 1억5,000만 갤런의 미혼합 SAF 생산능력을 설명합니다. 원료 처리능력에 SAF 능력을 더해 총제품 생산능력으로 표시하지 않습니다.', PSX_SAF),
    fact('항공연료 판매 연결', 'Rodeo의 SAF를 중부로 운송하고 Wood River의 기존 항공유와 혼합해 Chicago O’Hare로 공급하는 United Airlines 계약을 2026년 10월 공식 자료에서 확인했습니다. 공항 전체 연료의 독점 공급을 의미하지 않습니다.', PSX_CORRIDOR),
]
PUBLIC['DINO']['brief'] += [
    fact('공장·판매망을 읽는 기준', '2025년 말 정유 사업은 El Dorado·Tulsa·Navajo·Woods Cross·Puget Sound·Parco·Casper입니다. Sinclair 브랜드 연료 판매점 1,700곳 이상과 추가 브랜드 라이선스 350곳 이상은 공시 당시 직영 소매점 수가 아닙니다.', DINO),
    fact('재생 디젤의 원료·설비', 'Cheyenne·Artesia·Sinclair의 연간 재생 디젤 능력은 각각 약 9,000만·1억3,500만·1억5,300만 갤런입니다. 인접 정유소와 수소 등 일부 기반시설을 공유합니다. 합산 능력과 실제 연간 판매량은 구분합니다.', DINO),
    fact('윤활유 사업의 전환 계획', '2026년 7월 윤활유·특수제품 분리를 추진하고 Mississauga 기유 정제 자산을 2027년에 걸쳐 폐쇄할 계획을 발표했습니다. Ontario의 연구·배합·포장·물류는 유지할 계획입니다. 분리·폐쇄가 완료된 상태로 표시하지 않습니다.', DINO_Q),
    fact('새 기유 조달·유통 계약', '2026년 8월 SK Enmove의 Group III 기유와 Chevron의 Group II 기유 장기 공급 계약을 발표했습니다. HF Sinclair가 북미의 지정 시장에서 해당 제품을 유통하며, 새 공급 구조 전환은 2027년 하반기 완료 목표였습니다.', DINO_BASE),
    fact('2025년 기타 매출의 구성', '기타 매출 7억4,600만 달러에는 RIN 매각 4억3,000만 달러가 포함됩니다. RIN은 제품별 매출 합계에 다시 더하지 않고 별도 매출 유형으로 표시합니다.', DINO),
]

_DETAIL_SECTIONS = {
    'MPC': {'경쟁의 범위': 'drivers', 'MPLX의 연결 범위': 'segments'},
    'PSX': {'경쟁의 범위': 'drivers', '재생연료 공정 규모': 'products', '항공연료 판매 연결': 'products'},
    'DINO': {'경쟁의 범위': 'drivers', '2025년 기타 매출의 구성': 'segments'},
}

for _symbol, _drivers in {
    'MPC': [('정유 원가·가동', '원유 종류별 가격 차이, 제품 수율, 정비·에너지·물류비와 가동량을 확인합니다.'),
            ('물류의 외부·내부 수요', 'MPC 정유소 물류와 외부 가스 생산자의 처리 수요를 구분합니다. 내부 서비스 매출은 연결 과정에서 제거됩니다.'),
            ('재생연료 원가·크레딧', '유지류 원료비, 전처리·수소·정비와 규제 크레딧의 적용 범위가 사업 결과에 연결됩니다.')],
    'PSX': [('제품 가격과 원료 조달', '정유·화학·재생연료의 원료와 제품 가격 관계가 서로 다릅니다. 화학 지분법 이익과 연결 연료 매출을 구분합니다.'),
            ('가스·LPG 연결망', '가스 공급 물량, 처리·분별·수출 설비의 가용 능력과 비용을 확인합니다.'),
            ('설비·소유 범위 변경', '정유소 유휴화, WRB 연결 시점과 신규 설비 가동이 비교 기간의 사업 범위를 바꿉니다.')],
    'DINO': [('원유 품질·운송 경로', '정유소별 원유 조달과 제품 판매 지역이 다릅니다. 파이프라인·선박 중단은 원료와 출하 양쪽에 영향을 줍니다.'),
             ('재생연료·RIN', '원료·수소 비용과 제품 판매, 의무 이행용 RIN 비용·면제 및 RIN 매각을 각각 구분합니다.'),
             ('윤활유 조달 구조 전환', '자체 기유 생산 축소 계획, 장기 외부 공급·유통 계약과 배합·특수제품 사업의 유지 범위를 확인합니다.')],
}.items():
    # Keep eight essentials. Detailed notes stay in visible business/product/risk
    # sections, rather than the collapsed appendix for raw registration facts.
    _brief = []
    for _item in PUBLIC[_symbol]['brief']:
        _section = _DETAIL_SECTIONS[_symbol].get(_item['title'])
        if _section:
            PUBLIC[_symbol].setdefault(_section, []).append(_item)
        else:
            _brief.append(_item)
    PUBLIC[_symbol]['brief'] = _brief
    PUBLIC[_symbol].setdefault('drivers', []).extend(
        fact(title, detail, report(_symbol)) for title, detail in _drivers)
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    PUBLIC[_symbol]['sources'].append(report(_symbol, 'quarter'))
# The transition was announced after the annual report.
PUBLIC['DINO']['drivers'][-1]['source'] = DINO_BASE

PRIVATE = {
    'green-bison-soy-processing': profile('Green Bison Soy Processing', MPC,
        'North Dakota Spiritwood의 대두 가공 공동사업입니다. ADM 75%, Marathon Petroleum 25% 구조로 지역 대두를 가공합니다.',
        '정제 대두유를 MPC에 독점 공급해 재생 디젤 원료로 연결합니다. 연간 약 6억 파운드의 대두유 능력은 실제 매출이나 연료 생산량이 아닙니다.'),
    'martinez-renewables': profile('Martinez Renewables', MPC,
        'Marathon Petroleum과 Neste가 각각 50% 보유하는 California 재생 디젤 공동사업입니다. 재생원료 전처리와 연료 생산을 연결합니다.',
        '공동사업 전체 재생 디젤 능력은 연간 약 7억3,000만 갤런입니다. MPC 지분 귀속량이나 두 모회사의 실제 판매량으로 그대로 사용할 수 없습니다.'),
    'neste': profile('Neste', MPC,
        'Marathon Petroleum과 Martinez 재생 디젤 공동사업을 운영하는 핀란드 기업입니다. 이 기록은 해당 공동사업 관계를 설명합니다.',
        'Martinez 공동사업 지분은 50%로 공시돼 있습니다. Neste 전체 사업·매출이나 세계 시장점유율을 나타내는 자료가 아닙니다.'),
    'chevron-phillips-chemical': profile('Chevron Phillips Chemical', PSX,
        'Chevron과 Phillips 66이 각각 50% 보유하는 석유화학 공동사업입니다. 에틸렌·폴리에틸렌·알파올레핀, 방향족·특수화학 제품을 제조·판매합니다.',
        '2025년 말 29개 제조 시설을 소유하거나 공동사업 지분을 보유했습니다. Phillips 66은 지분법으로 회계처리하므로 CPChem의 제품 매출을 모회사 연결 매출에 합산하지 않습니다.',
        [('올레핀·폴리올레핀', '에틸렌을 폴리에틸렌·알파올레핀·폴리에틸렌 파이프 등으로 연결합니다.'),
         ('방향족·특수화학', '벤젠·시클로헥산·스티렌과 유기황·용제·촉매·시추·광업용 화학제품 등을 취급합니다.')]),
    'seven-eleven-us': profile('7-Eleven, Inc.', SPEEDWAY,
        '미국 Speedway 점포 인수와 함께 Marathon Petroleum의 연료 구매 계약을 체결한 소매 기업입니다.',
        '2021년 체결된 15년 계약의 연간 기준 연료 물량은 약 77억 갤런입니다. 이는 미국 Speedway 관련 계약 범위이며 전 세계 7-Eleven의 구매량이 아닙니다.'),
    'dhl-express': profile('DHL Express', DHL_SAF,
        '항공 네트워크를 사용하는 국제 특송 사업자입니다. Phillips 66과 SAF 장기 구매 계약을 발표했습니다.',
        '2025년 발표된 계약은 3년간 24만 톤을 넘는 SAF 공급입니다. 계약 총량과 매년 실제 인도량은 다르며 DHL 그룹 전체 연료 구매를 의미하지 않습니다.'),
    'sk-enmove': profile('SK Enmove · SK On 내 사업 조직', DINO_BASE,
        'HF Sinclair에 Group III 기유를 공급하고 YUBASE 브랜드의 북미 유통을 연결하는 계약 상대입니다. 2026년 발표는 SK On 내 CIC 조직으로 표기합니다.',
        'HF Sinclair 윤활유·특수제품 사업에 대한 장기 기유 공급과 북미 주요 지역 유통 계약이 확인됩니다. 이 관계를 SK On 전체 제품의 공급으로 확대하지 않습니다.'),
    'trans-mountain': profile('Trans Mountain', DINO,
        '캐나다 Edmonton에서 HF Sinclair Puget Sound 정유소까지 원유 공급을 연결하는 파이프라인 시스템의 운영 관계를 설명하는 기록입니다.',
        '공시는 이 경로를 캐나다 원유의 운송망으로 제시합니다. 운송사를 원유 자체의 매도인으로 해석하거나 원유 대금을 운송사 매출로 계산하지 않습니다.'),
    'red-giant-oil': profile('Red Giant Oil', DINO,
        'HF Sinclair의 철도 산업용 윤활유 사업입니다. Iowa Council Bluffs와 Texas Joshua에 배합·유통 시설을 운영합니다.',
        '철도 고객용 윤활유를 공급합니다. 별도 회사 매출을 HF Sinclair 윤활유·특수제품 부문 전체 매출과 동일하게 표시하지 않습니다.'),
    'sonneborn': profile('Sonneborn', DINO,
        'HF Sinclair의 백유·페트롤라툼·왁스 등 특수제품 사업입니다. 개인관리·화장품·의약품·식품가공 산업을 대상으로 합니다.',
        '미국 Pennsylvania Petrolia와 네덜란드 Amsterdam 제조 시설을 운영합니다. 공시의 시설 능력은 판매량·제품 시장점유율과 구분합니다.'),
    'industrial-oils-unlimited': profile('Industrial Oils Unlimited', DINO,
        '윤활유·특수 유체의 배합·유통 사업으로 HF Sinclair가 2026년 1월 인수했습니다. Oklahoma·Louisiana·Arkansas의 배합 시설과 Texas 물류 시설을 갖습니다.',
        '기존 HF Sinclair 윤활유 사업에 배합·유통 범위를 추가한 사업입니다. 인수 전 2025년 모회사 연결 매출에 포함됐다고 해석하지 않습니다.'),
}

EDGES = {
    'MPC': [
        relation('MPLX', 'MPLX', 'supplier', '정유소 원유·제품 운송·저장·터미널·수상 물류 제공. 자회사이면서 서비스 공급 역할.', MPC),
        relation('MPLX', 'MPLX', 'subsidiary', 'MPC가 일반 파트너 및 2026-06말 보통 지분 약64% 보유. 물류·가스처리 부문 연결.', MPC_Q),
        relation('Green Bison Soy Processing', None, 'supplier', '재생 디젤용 정제 대두유 독점 공급. 연간 약6억 파운드는 설비능력.', MPC, 'green-bison-soy-processing'),
        relation('Archer-Daniels-Midland', 'ADM', 'partner', 'Green Bison 대두 가공 공동사업: ADM75%·MPC25%. JV의 대두유 공급과 ADM 그룹의 직접 매출은 구별.', MPC),
        relation('Neste', None, 'partner', 'Martinez 재생 디젤 50:50 공동사업. 전처리·생산능력 공유.', MPC, 'neste'),
        relation('Martinez Renewables', None, 'supplier', '공동사업에서 생산한 재생 디젤 구매·판매. 2026년1분기 계획 정비.', MPC_Q, 'martinez-renewables'),
        relation('7-Eleven, Inc.', None, 'customer', '2021년 Speedway 거래 시 체결한15년 연료 공급 계약. 연간 기준77억 갤런은 현재 실제 인도량 아님.', SPEEDWAY, 'seven-eleven-us'),
    ],
    'PSX': [
        relation('Chevron', 'CVX', 'partner', 'CPChem의 50:50 석유화학 공동사업. 화학제품 제조·판매와 신규 설비 개발.', PSX),
        relation('Chevron Phillips Chemical', None, 'partner', '에틸렌·폴리에틸렌·특수화학 공동사업. Phillips66 지분50%, 지분법 회계.', PSX, 'chevron-phillips-chemical'),
        relation('Linde', 'LIN', 'supplier', 'Sweeny 정유소 고순도 수소 장기 공급·설비 가동을2021-10 발표. 당시 공급 개시 근거이며2026년 계약금액·공급량은 이 자료에 없음.', LIN_H2),
        relation('United Airlines', 'UAL', 'customer', 'SAF 공급 계약. Rodeo 생산→Wood River 항공유와 혼합→O’Hare 공급 경로를2026-10 자료에서 확인.', PSX_CORRIDOR),
        relation('DHL Express', None, 'customer', '2025-11 발표:3년간24만톤 초과 SAF 공급 계약. 전량 인도 완료나 독점 공급으로 표시하지 않음.', DHL_SAF, 'dhl-express'),
    ],
    'DINO': [
        relation('Chevron', 'CVX', 'supplier', 'Chevron Products Company의 GroupII 기유 장기 공급. HF Sinclair가 Canada·미국 지정 지역에서 유통,2026-08계약 발표.', DINO_BASE),
        relation('SK Enmove · SK On 내 사업 조직', None, 'supplier', 'GroupIII 기유 공급·YUBASE 북미 주요 시장 유통.2026-08발표; 새 조달 구조 전환은2027년 하반기 목표.', DINO_BASE, 'sk-enmove'),
        relation('ONEOK', 'OKE', 'supplier', 'El Dorado·Tulsa 등에서 원료 NGL 및 정유제품 운송 경로 제공. 원료 자체의 판매 계약으로 단정하지 않음.', DINO),
        relation('Enterprise Products Partners', 'EPD', 'supplier', 'Texas·Mid-Continent의 이소부탄·천연가솔린 등을 Navajo로 운송하는 공동이용 파이프라인. 원료 판매사와 운송사 구별.', DINO),
        relation('MPLX', 'MPLX', 'supplier', 'Woods Cross 정유소의 외부 제품 출하 파이프라인. 공시의 주요 제3자 물류 경로.', DINO),
        relation('Trans Mountain', None, 'supplier', 'Edmonton의 캐나다 원유를 Puget Sound 정유소로 운송하는 경로. 원유의 매도인으로 추정하지 않음.', DINO, 'trans-mountain'),
        relation('Shell', 'SHEL', 'customer', '역사적 고객:2024년 계열사 합산 매출11%,2023년12%.2025년에는 매출10% 이상 고객 없음; 현재 비중은 추정하지 않음.', DINO),
        relation('Red Giant Oil', None, 'subsidiary', '철도 산업용 윤활유 배합·유통.', DINO, 'red-giant-oil'),
        relation('Sonneborn', None, 'subsidiary', '개인관리·의약품·식품가공용 백유·왁스 등 제조.', DINO, 'sonneborn'),
        relation('Industrial Oils Unlimited', None, 'subsidiary', '2026-01인수 완료한 윤활유·특수 유체 배합·유통 사업.', DINO, 'industrial-oils-unlimited'),
    ],
    'CVX': [
        relation('Phillips 66', 'PSX', 'partner', '각50%의 CPChem 공동사업으로 석유화학 제품 제조·판매.', PSX),
        relation('Chevron Phillips Chemical', None, 'partner', 'Chevron·Phillips66의 석유화학 공동사업.', PSX, 'chevron-phillips-chemical'),
        relation('HF Sinclair', 'DINO', 'customer', 'Chevron Products Company의 GroupII 기유 장기 공급 계약·북미 지정 지역 유통.2026-08발표.', DINO_BASE),
    ],
    'MPLX': [
        relation('Marathon Petroleum', 'MPC', 'customer', '정유소와 연료 공급망에 운송·저장·터미널·수상 물류 제공.', MPC),
        relation('Marathon Petroleum', 'MPC', 'parent', '일반 파트너 및2026-06말 보통 지분 약64% 보유.', MPC_Q),
        relation('HF Sinclair', 'DINO', 'customer', 'Woods Cross 정유소의 제3자 제품 출하 경로 제공.', DINO),
    ],
}

# Explicit reciprocal roles support navigation without guessing group tickers.
PRIVATE['green-bison-soy-processing']['relations'] = [
    relation('Marathon Petroleum', 'MPC', 'customer', '정제 대두유 독점 공급 대상·공동사업자25%.', MPC),
    relation('Archer-Daniels-Midland', 'ADM', 'partner', '대두 가공 공동사업 지분75%.', MPC),
]
PRIVATE['martinez-renewables']['relations'] = [
    relation('Marathon Petroleum', 'MPC', 'customer', '공동사업 생산 재생 디젤을 구매해 판매.', MPC_Q),
    relation('Marathon Petroleum', 'MPC', 'partner', '재생 디젤 공동사업50%.', MPC),
    relation('Neste', None, 'partner', '재생 디젤 공동사업50%.', MPC, 'neste'),
]
PRIVATE['chevron-phillips-chemical']['relations'] = [
    relation('Chevron', 'CVX', 'partner', '석유화학 공동사업50%.', PSX),
    relation('Phillips 66', 'PSX', 'partner', '석유화학 공동사업50%·지분법 회계.', PSX),
]
for _key, _symbol, _name, _kind, _detail, _origin in [
    ('neste', 'MPC', 'Marathon Petroleum', 'partner', 'Martinez 재생 디젤50:50 공동사업.', MPC),
    ('seven-eleven-us', 'MPC', 'Marathon Petroleum', 'supplier', '2021년 체결15년 연료 공급 계약·Speedway 관련 범위.', SPEEDWAY),
    ('dhl-express', 'PSX', 'Phillips 66', 'supplier', '3년간24만톤 초과 SAF 계약·2025년 발표.', DHL_SAF),
    ('sk-enmove', 'DINO', 'HF Sinclair', 'customer', 'GroupIII 기유 공급·YUBASE 북미 주요 시장 유통 계약.', DINO_BASE),
    ('trans-mountain', 'DINO', 'HF Sinclair', 'customer', 'Puget Sound 정유소의 캐나다 원유 운송 경로.', DINO),
    ('red-giant-oil', 'DINO', 'HF Sinclair', 'parent', '윤활유·특수제품 부문에 포함.', DINO),
    ('sonneborn', 'DINO', 'HF Sinclair', 'parent', '윤활유·특수제품 부문에 포함.', DINO),
    ('industrial-oils-unlimited', 'DINO', 'HF Sinclair', 'parent', '2026년1월 인수 완료.', DINO),
]:
    PRIVATE[_key]['relations'] = [relation(_name, _symbol, _kind, _detail, _origin)]
