"""Primary-source energy reading notes; this catalog is not sector completion.

Report evidence/figures are separate from Korean narrative. Exact relationships
retain project and historical scope; no inferred issuer-to-issuer trade edges.
"""
from .company_energy_sources import REPORTS, report, fact
from .company_research_notes import profile, relation, source


CVX, COP, VLO = (report(symbol) for symbol in ('CVX','COP','VLO'))
CVX_Q, COP_Q, VLO_Q = (report(symbol,'quarter') for symbol in ('CVX','COP','VLO'))
CVX_BKR = source('Baker Hughes · Jansz-Io 공급 계약 발표',
    'https://www.bakerhughes.com/company/news/baker-hughes-deliver-subsea-compression-manifold-chevron-subsea-compression-project','2021-08-10')
VLO_PROCESS = source('Valero · 재생 디젤 제조 공정',
    'https://www.valero.com/renewables/renewable-diesel/renewable-diesel-science-process','열람 2026-10-02')

PUBLIC = {
    'CVX': profile('Chevron', CVX,
        '원유·천연가스 탐사·생산과 정유·연료·윤활유 판매를 함께 하는 통합 에너지 기업입니다. 상류 부문에는 미국 셰일·해상 유전, 카자흐스탄, 호주 LNG와 Guyana 등이 있고, 하류 부문에는 정유·판매 및 화학 합작사업이 있습니다.',
        '상류는 생산한 원유·가스, 하류는 정제·구매한 석유제품의 판매로 매출을 만듭니다. 2025년 고객 계약 매출은 1,844억3,200만 달러입니다. 지역·부문 간 내부거래를 제거한 매출이며, 지분법 이익 등을 포함한 전체 수익과 구분합니다.',
        [('원유·가스·NGL','생산 자산에서 원유·천연가스·천연가스액을 생산·판매합니다.'),
         ('LNG','호주 Gorgon·Wheatstone 등에서 가스를 액화해 공급합니다. 프로젝트 전체 설비능력과 Chevron 귀속 지분은 구별합니다.'),
         ('수송용 연료·윤활유','Chevron·Texaco·Caltex 등의 판매망을 통해 연료·기유·윤활유를 공급합니다.'),
         ('화학·첨가제','CPChem 합작사업은 올레핀·폴리올레핀 등을, Chevron Oronite는 연료·윤활유 첨가제를 취급합니다.')],
        customers='주유소 공급망, 산업·항공 연료 고객과 LNG 구매자가 주요 판매 경로입니다. 2025년 말 미국 내 Chevron·Texaco 브랜드 주유소 약 8,600곳에 직접 또는 판매업자를 통해 공급했습니다. 브랜드 점포 수 전체가 직영점 수는 아닙니다.',
        inputs='상류는 유전 개발·시추·해상 설비와 운송을, 하류는 원유 조달·정제설비·에너지·정비와 제품 물류를 사용합니다. 동일 회사 안에서도 원유 생산 판매와 원유 구매·정제의 경제 구조가 다릅니다.'),
    'COP': profile('ConocoPhillips', COP,
        '원유·천연가스의 탐사·개발·생산·판매를 중심으로 하는 독립 E&P 기업입니다. 미국 비전통 자원, 알래스카, 캐나다 오일샌드, 해외 생산 자산과 LNG 지분·판매 사업을 운영합니다. 2012년 분리한 Phillips 66의 정유 실적은 포함하지 않습니다.',
        '생산한 원유·역청·가스·NGL의 판매 및 에너지 마케팅 사업에서 매출이 발생합니다. 2025년 매출은 589억4,400만 달러이며, 영업 부문 합계 589억1,200만 달러와 본사·기타 3,200만 달러로 구분됩니다. 소계와 그 하위 부문을 중복 합산하지 않습니다.',
        [('원유·역청','미국·캐나다 및 해외 생산 자산의 액체 탄화수소 판매입니다.'),
         ('천연가스·NGL','가스와 분리한 액체 탄화수소를 각 지역 시장에 판매합니다.'),
         ('LNG 생산·판매','Australia Pacific LNG, QatarEnergy LNG 공동사업과 LNG 구매·판매 계약, 유럽 재기화 능력 등을 연결합니다.')],
        customers='생산물 판매와 LNG 장기계약·마케팅 사업을 운영합니다. APLNG의 LNG는 Sinopec과 Kansai Electric Power에 장기계약으로 판매하며, 이 계약은 합작사업의 판매입니다. ConocoPhillips 전체 매출의 고객별 비중으로 환산하지 않습니다.',
        inputs='유정 개발·시추·완결, 생산설비·운송과 LNG 사업 투자가 필요합니다. 지역별 자산·매장량·개발비와 판매 물량을 함께 구별해야 합니다. 자산 매입 금액과 당기 생산에 들어간 운영비는 서로 다른 항목입니다.'),
    'VLO': profile('Valero Energy', VLO,
        '원유를 휘발유·경유·항공유 등으로 가공해 판매하는 정유사입니다. 정유, 재생 디젤, 에탄올의 세 보고 부문을 운영하며 Diamond Green Diesel 합작사업을 연결합니다. 주요 시장은 미국·캐나다·영국·아일랜드·중남미입니다.',
        '2025년 외부 고객 매출은 1,226억8,700만 달러입니다. 정유 1,161억5,800만, 재생 디젤 25억800만, 에탄올 40억2,100만 달러입니다. 공시의 세금 포함 매출 기준이며 부문 내부거래는 제거했습니다. 부문별 이익률이나 생산능력 비중과는 다릅니다.',
        [('석유계 연료','휘발유·혼합 기재, 경유·항공유 등 중간유분, 기타 정유 제품을 생산·판매합니다.'),
         ('재생 디젤·나프타·SAF','DGD가 폐식용유·동물성 지방·비식용 옥수수유 등을 가공합니다. Port Arthur의 SAF 전환 능력은 해당 재생 디젤 설비능력의 일부입니다.'),
         ('에탄올·부산물','곡물 기반 에탄올과 증류곡물 등의 부산물을 판매합니다.')],
        customers='탱크터미널 도매 출하와 대량 판매·수출을 통해 연료를 공급합니다. DGD의 제품은 혼합업체와 최종 사용 고객에 판매합니다. 철도·선박·바지선 등 유통 경로와 정유소 인근 물류자산이 연결됩니다.',
        inputs='정유는 원유·에너지·수소·정비, 재생연료는 폐유지·동물성 지방·식물성 기름과 수소, 에탄올은 곡물 원료가 필요합니다. DGD는 Darling과 원료 공급 약정을 맺었으나 Darling에서 모든 원료를 의무적으로 사야 하는 계약은 아닙니다.'),
}

PUBLIC['CVX']['brief'] += [
    fact('핵심 자산·지역', '2025년 말 확인 매장량은 약 106억 BOE이며 미국 43%, 호주 15%, 카자흐스탄 11%였습니다. 이는 생산 설비능력이나 시장점유율이 아니라 회사 귀속 확인 매장량의 지역 구성입니다.', CVX),
    fact('합작사업과 연결 범위', 'Hess 인수로 Guyana Stabroek의 비운영 지분 30%와 Bakken 자산 등이 더해졌습니다. Hess Midstream의 집하·가스처리·물 처리 사업, CPChem·GS Caltex의 화학·정유 사업은 지분과 사업 역할을 각각 구분해 봅니다.', CVX),
    fact('최신 공시 변화', '2026년 2분기에 홍콩 연료·윤활유 사업 매각을 완료했습니다. 싱가포르 정유사 지분과 여러 아시아·호주 하류 자산의 매각 계약은 당시 2027년 종결 예정이었습니다. 체결한 매각 계약을 매각 완료로 표시하지 않습니다.', CVX_Q),
]
PUBLIC['COP']['brief'] += [
    fact('사업을 나누는 기준', '보고 부문은 알래스카, 미국 본토 48개 주, 캐나다, 유럽·중동·북아프리카, 아시아·태평양의 5개 지역입니다. 2025년 총 생산량은 하루 평균 237만5,000 BOE로 공시했습니다. 지역별 매출은 생산량 비중과 일치하지 않을 수 있습니다.', COP),
    fact('LNG에서 맡는 역할', 'APLNG에서는 Origin이 상류 생산·파이프라인, ConocoPhillips가 액화·수출 판매를 운영합니다. 2026년 6월 말 ConocoPhillips의 APLNG 지분은 47.5%, Port Arthur LNG 1단계 직접 지분은 30%였습니다.', COP_Q),
    fact('개발 단계와 현재 생산의 구별', '2025년 연차 공시에서 Willow는 건설 중이며 첫 생산은 2029년 초 계획으로 제시했습니다. Port Arthur LNG 1단계는 2027년 가동 계획이었습니다. 계획 생산능력을 현재 판매 매출로 계산하지 않습니다.', COP),
]
PUBLIC['VLO']['brief'] += [
    fact('설비의 기준일', '2025년 말 기준 정유소 15곳, 원유 등 총 처리능력 약 하루 320만 배럴, 에탄올 공장 12곳과 연간 약 17억 갤런 능력을 공시했습니다. 이후 Benicia 가동 중단이 있어 이 수치를 현재 가동 설비 수로 읽지 않습니다.', VLO),
    fact('2026년 Benicia 가동 중단', '분기 공시에 따르면 연료 생산을 단계적으로 중단하고 2026년 4월 모든 처리설비의 유휴화를 마쳤습니다. 북부 캘리포니아 고객에 대한 계약 의무는 수입 등 대체 공급으로 이행할 계획입니다.', VLO_Q),
    fact('2026년 Port Arthur 화재', '2026년 3월 23일 수첨처리설비 화재로 정유소가 전면 중단됐습니다. 4월 제한된 처리량으로 재가동한 뒤 2분기 중 정상 처리량으로 복귀했다고 공시했습니다. 복구비·보험금의 인식 시점은 다를 수 있습니다.', VLO_Q),
]

for _symbol, _items in {
    'CVX': [('생산·판매와 정제 마진','생산물 가격·물량과 정제제품 판매가격·원유 구입비는 사업별로 구분합니다. 제품가격 하나로 상류·하류 이익을 동일하게 설명할 수 없습니다.'),
            ('신규 개발·정비·공동사업','프로젝트 가동 시점, 설비 정비, 공동사업의 비용·자금 부담과 생산 귀속이 운영 결과에 연결됩니다.')],
    'COP': [('생산량·실현가격','원유·역청·가스·NGL별 생산량, 판매가격과 지역 차이를 구분합니다. 자산 매각·인수가 생산 범위를 바꿀 수 있습니다.'),
            ('개발 투자와 자산 수명','유정·LNG·알래스카 개발 투자, 설비 가동 시점, 매장량 추정과 자산폐기 의무를 함께 확인합니다.')],
    'VLO': [('정제제품 가격과 원료 비용','휘발유·중간유분 판매가격, 원유 품질·가격 차이, 실제 수율·가동률과 에너지·정비 비용이 정유 사업에 연결됩니다.'),
            ('재생연료 원료·규제','폐유지·곡물·수소 원가와 제품 가격, RIN·저탄소연료 제도의 적격성·비용을 구분합니다. 지원액과 규정은 적용 연도별로 확인합니다.'),
            ('계획·비계획 가동 중단','정기 보수와 사고에 따른 처리량 변화, 재고 회계·복구비·보험금이 서로 다른 기간에 반영될 수 있습니다.')],
}.items():
    PUBLIC[_symbol]['drivers'] = [fact(title,detail,report(_symbol)) for title,detail in _items]
    PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    PUBLIC[_symbol]['sources'] += [report(_symbol,'quarter')]

PRIVATE = {
    'diamond-green-diesel': profile('Diamond Green Diesel', VLO,
        'Valero와 Darling Ingredients의 재생연료 공동사업입니다. St. Charles와 Port Arthur 인근 두 공장에서 폐유지 등을 재생 디젤·나프타·미혼합 지속가능항공유로 가공합니다.',
        '제품을 혼합업체·최종 사용 고객 등에 판매합니다. Valero 연결 부문의 외부 매출과 DGD 자체 매출·생산능력은 구별해야 합니다.',
        [('폐유지 전처리·연료 전환','원료 전처리 후 수소를 사용하는 가공과 이성화·분별 과정을 거칩니다.')],
        inputs='동물성 지방·폐식용유·비식용 옥수수유 등과 수소를 사용합니다. Darling의 공급 제안 의무가 Valero 측의 전량 구매 의무를 뜻하지 않습니다.'),
    'australia-pacific-lng': profile('Australia Pacific LNG', COP,
        '호주 Queensland의 석탄층 가스 생산과 Curtis Island 액화·수출을 연결하는 LNG 공동사업입니다. Origin이 상류·파이프라인을, ConocoPhillips가 액화·수출 판매를 운영합니다.',
        '호주 국내 가스 공급 및 Sinopec·Kansai Electric Power 등에 대한 장기 LNG 판매가 공시돼 있습니다. 두 액화 트레인의 능력은 각각 연간 450만 톤이며 실제 연간 판매량과는 다릅니다.'),
    'qatarenergy': profile('QatarEnergy', COP,
        '카타르 North Field 자원과 LNG 사업의 공동사업 파트너입니다. ConocoPhillips의 N3·North Field 확장 사업 공시에서 역할이 확인됩니다.',
        '여기서는 ConocoPhillips 공시로 확인된 공동 생산·액화 및 판매 구조를 정리합니다. QatarEnergy 그룹 전체 매출을 나타내지는 않습니다.'),
    'sinopec-group': profile('China Petrochemical Corporation · Sinopec Group', COP,
        'Australia Pacific LNG의 공동사업자이자 해당 LNG의 장기 구매자로 공시된 중국 에너지·화학 그룹입니다.',
        'APLNG 공시에 기재된 계약은 연간 760만 톤, 20년 LNG 판매입니다. 그룹 전체 구매량이나 상장 자회사 매출과 같은 수치는 아닙니다.'),
    'origin-energy': profile('Origin Energy', COP,
        'Australia Pacific LNG의 상류 가스 생산과 파이프라인 시스템 운영을 담당하는 공동사업자입니다.',
        'APLNG의 가스 생산·운송을 액화·수출 설비와 연결합니다. 이 기록은 확인된 공동사업 역할을 설명하며 Origin 그룹 전체 사업 분석은 포함하지 않습니다.'),
    'kansai-electric-power': profile('Kansai Electric Power', COP,
        'Australia Pacific LNG와 장기 LNG 구매계약을 맺은 일본 전력 기업입니다.',
        'ConocoPhillips의 2025년 공시에 APLNG와 연간 약 100만 톤, 20년 판매계약이 명시돼 있습니다. 전체 연료 조달이나 거래 상대 전부를 나타내는 수치는 아닙니다.'),
}

EDGES = {
    'CVX': [
        relation('Baker Hughes','BKR','supplier','Jansz-Io 해저 압축 매니폴드 구조·연결장치·제어 공급 계약 · 2021-08 발표. 당시 계약의 확인이며 2026년 납품 완료·계약금액을 뜻하지 않음.',CVX_BKR),
        relation('Hess Midstream','HESM','supplier','Hess 인수로 연결된 Bakken 집하·압축·가스처리·원유·생산수 물류 사업. Chevron과 외부 고객에게 수수료 기반 서비스를 제공.',CVX),
        relation('ConocoPhillips','COP','partner','AMPCO 메탄올 공동사업: Chevron과 ConocoPhillips 각45%, SONAGAS10%. 2025년 공시 당시 공장은 비가동 상태.',COP),
    ],
    'COP': [
        relation('QatarEnergy',None,'partner','N3 가스 생산·액화 공동사업과 North Field East·South LNG 확장 공동사업의 파트너. 개별 JV 지분을 그룹 지분으로 해석하지 않음.',COP_Q,'qatarenergy'),
        relation('Australia Pacific LNG',None,'partner','호주 석탄층 가스 생산·액화·수출 공동사업. 2026-06말 지분47.5%; ConocoPhillips는 액화·수출 판매 운영.',COP_Q,'australia-pacific-lng'),
        relation('Origin Energy',None,'partner','APLNG 상류 생산·파이프라인 운영을 맡으며 ConocoPhillips의 액화·수출 운영과 연결.',COP,'origin-energy'),
        relation('China Petrochemical Corporation · Sinopec Group',None,'customer','APLNG를 통한 LNG 장기 판매: 20년·연간760만톤 계약. ConocoPhillips 단독 직접 매출이나 그룹 전체 판매로 확대하지 않음.',COP,'sinopec-group'),
        relation('Kansai Electric Power',None,'customer','APLNG를 통한 LNG 장기 판매: 20년·연간약100만톤 계약. 합작사업의 판매 관계.',COP,'kansai-electric-power'),
        relation('Chevron','CVX','partner','AMPCO 메탄올 공동사업 각45%. 2025년 공시 당시 공장은 비가동 상태.',COP),
    ],
    'VLO': [
        relation('Darling Ingredients','DAR','supplier','DGD 재생연료용 원료 공급 약정. Darling은 원료 일부를 시장가격으로 제안하며 DGD는 전부 또는 일부를 의무 구매할 필요가 없음.',VLO),
        relation('Darling Ingredients','DAR','partner','Diamond Green Diesel 공동사업 파트너. 원료 공급 역할과 합작사업 관계를 별도로 표시.',VLO),
        relation('Diamond Green Diesel',None,'subsidiary','Valero가 연결하는 재생 디젤·나프타·SAF 공동사업. Valero가 공장 운영과 일부 관리 기능을 제공.',VLO,'diamond-green-diesel'),
    ],
}
PRIVATE['diamond-green-diesel']['relations'] = [
    relation('Darling Ingredients','DAR','supplier','폐유지 등 원료 공급 약정. DGD에 전량 구매 의무는 없음.',VLO),
    relation('Valero Energy','VLO','partner','재생연료 공장의 운영과 일부 관리 기능 제공 및 공동사업자.',VLO),
]
PRIVATE['diamond-green-diesel']['products'][0]['source'] = VLO_PROCESS
PRIVATE['australia-pacific-lng']['relations'] = [
    relation('ConocoPhillips','COP','partner','액화·수출 판매 운영, 2026-06말 지분47.5%.',COP_Q),
    relation('Origin Energy',None,'partner','상류 생산·파이프라인 운영.',COP,'origin-energy'),
    relation('China Petrochemical Corporation · Sinopec Group',None,'customer','20년·연간760만톤 LNG 계약.',COP,'sinopec-group'),
    relation('Kansai Electric Power',None,'customer','20년·연간약100만톤 LNG 계약.',COP,'kansai-electric-power'),
]
