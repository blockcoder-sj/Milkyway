"""Reviewed industry reading guide. No network, database scan or model calls.

Industry process diagrams describe physical roles, never inferred company trades.
Individual issuer/contract coverage is audited separately from this guide.
"""
from copy import deepcopy

CHECKED = "2026-10-02"


def citation(label, url):
    return dict(label=label, url=url, kind="산업 구조 · 확인 " + CHECKED)


SOURCES = {
    "gics": citation("MSCI · GICS 방법론, 2026년 4월", "https://www.msci.com/indexes/documents/methodology/1_MSCI_Global_Industry_Classification_Standard_GICS_Methodology_20250220.pdf"),
    "refining": citation("EIA · 원유의 성질과 정제 투입·산출", "https://www.eia.gov/energyexplained/oil-and-petroleum-products/refining-crude-oil-inputs-and-outputs.php"),
    "gas": citation("EIA · 천연가스 처리·운송·저장", "https://www.eia.gov/energyexplained/natural-gas/delivery-and-storage.php"),
    "lng": citation("EIA · LNG 생산·운송·재기화", "https://www.eia.gov/energyexplained/natural-gas/liquefied-natural-gas.php"),
    "nuclear": citation("NRC · 원자력 연료주기", "https://www.nrc.gov/facilities-safety/fuel-cycle-facilities/stages-of-the-nuclear-fuel-cycle"),
    "coal": citation("EIA · 석탄의 종류와 용도", "https://www.eia.gov/energyexplained/coal/"),
    "coking": citation("EIA · 석탄 가격과 제철용 코크스", "https://www.eia.gov/energyexplained/coal/prices-and-outlook.php"),
    "ethanol": citation("EIA · 에탄올 원료와 제조", "https://www.eia.gov/energyexplained/biofuels/ethanol.php"),
    "biofuels": citation("EIA · 바이오디젤·재생 디젤·항공유", "https://www.eia.gov/energyexplained/biofuels/biodiesel-rd-other-basics.php"),
    "rin": citation("EPA · RIN 제도", "https://www.epa.gov/renewable-fuel-standard/renewable-identification-numbers-rins-under-renewable-fuel-standard-program"),
    "rfs": citation("EPA · Renewable Fuel Standard 개요", "https://www.epa.gov/renewable-fuel-standard/overview-renewable-fuel-standard-program"),
    "pipeline": citation("FERC · 주간 천연가스 파이프라인", "https://ferc.gov/natural-gas/natural-gas-pipelines"),
    "rates": citation("FERC · 운송 요율과 허가", "https://ferc.gov/natural-gas/general-information/cost-service-rate-filings"),
    "crack": citation("CME · 정제 스프레드의 계산", "https://www.cmegroup.com/articles/2024/trading-crack-spreads.html"),
    "weekly": citation("EIA · 주간 석유 통계 정의", "https://www.eia.gov/dnav/pet/TblDefs/pet_sum_sndw_tbldef.asp"),
    "consumption": citation("EIA · 제품 공급량의 계산과 의미", "https://www.eia.gov/tools/FAQs/faq.php?id=1394&t=10"),
    "reserves": citation("EIA · 확인 매장량의 정의", "https://www.eia.gov/dnav/pet/TblDefs/pet_crd_npres_tbldef2.asp"),
    "basis": citation("EIA · 지역 가스 가격과 Henry Hub 차이", "https://www.eia.gov/tODAyinenergy/detail.php?id=45037"),
}


def topic(title, body, sources, *, steps=(), formula=None, caveat=None):
    return dict(title=title, body=body, source_ids=sources.split(), steps=list(steps), formula=formula, caveat=caveat)


INDUSTRIES = [
    ("10101010", "Oil & Gas Drilling", "시추", "시추 장비·선박과 인력을 운용해 유정을 뚫는 계약 사업."),
    ("10101020", "Oil & Gas Equipment & Services", "장비·서비스", "탐사·시추·생산을 위한 장비, 기술, 현장 서비스를 제공."),
    ("10102010", "Integrated Oil & Gas", "통합 석유·가스", "자원 탐사·생산과 정제·판매를 함께 운영."),
    ("10102020", "Oil & Gas Exploration & Production", "탐사·생산", "원유·천연가스를 탐사하고 개발해 생산·판매."),
    ("10102030", "Oil & Gas Refining & Marketing", "정제·판매", "정유와 석유제품 판매를 주력으로 운영."),
    ("10102040", "Oil & Gas Storage & Transportation", "저장·운송", "석유·가스·정제제품의 파이프라인, 탱커, 저장 시설 운영."),
    ("10102050", "Coal & Consumable Fuels", "석탄·소모성 연료", "석탄과 에너지용 소모성 연료를 생산·채굴."),
]

SECTIONS = [
    dict(id="chains", title="원료에서 고객까지", intro="화살표는 산업의 물질 이동 과정입니다. 특정 기업 사이의 납품 계약을 뜻하지 않습니다.", entries=[
        topic("원유 → 정유 → 연료·화학 원료", "원유는 성질에 따라 가공 방법과 제품 수율이 달라집니다. 정유사는 증류와 추가 가공·혼합을 거쳐 휘발유·경유·항공유·아스팔트·윤활유 원료 등을 판매합니다. 같은 원유 투입량이라도 정유소의 설비와 원료 조합에 따라 산출물이 달라집니다.", "refining", steps=["자원 탐사·유정 개발", "원유 생산·집유", "파이프라인·탱커·저장", "정제·혼합", "도매·수출·소매", "운송·산업·화학 고객"]),
        topic("천연가스 → 처리 → 파이프라인·소비", "유정에서 나온 가스에는 물·불순물과 액체 탄화수소가 섞여 있습니다. 처리 시설에서 이를 분리한 뒤 규격에 맞는 건성 가스를 운송합니다. 생산, 집하, 처리, 장거리 수송, 저장, 최종 공급은 서로 다른 설비와 계약을 사용합니다.", "gas", steps=["가스 생산", "집하·압축", "탈수·불순물 제거", "건성 가스 분리", "장거리 운송·저장", "발전·산업·도시가스"]),
        topic("NGL → 분별 → 제품별 시장", "NGL은 가스 처리에서 분리되는 에탄·프로판·부탄 등의 액체 탄화수소입니다. 혼합 NGL을 분별 시설에서 제품별로 나눠 석유화학 원료·연료·정유 혼합 원료 등으로 판매합니다. LNG는 주로 메탄을 냉각한 것으로 NGL과 공정·용도가 다릅니다.", "gas lng", steps=["가스 처리의 혼합 NGL", "전용 운송", "분별", "에탄·프로판·부탄 등", "화학 공장·연료 시장·수출"]),
        topic("LNG → 액화 → 해상 수출 → 재기화", "파이프라인으로 받은 천연가스를 약 −162°C로 냉각해 부피를 줄이고 전용 선박으로 보냅니다. 수입 터미널에서는 저장 후 기체로 바꿔 공급합니다. 원료 가스 판매자, 액화 사업자, 화물 구매자, 선주와 수입 터미널은 각각 다른 역할입니다.", "lng", steps=["원료 가스 조달", "전처리·액화", "저장·선적", "LNG 운반선", "수입 터미널·재기화", "파이프라인 고객"]),
        topic("석탄 → 발전용·제철용", "석탄은 탄소 함량·열량 등에 따라 분류하며 사용처도 다릅니다. 발전용 연료와 제철용 코크스의 원료인 점결탄은 같은 상품으로 비교하지 않습니다. 광산 출하량, 판매 규격, 운송 방식과 납품 시장을 함께 봐야 합니다.", "coal coking", steps=["채굴", "선별·처리", "철도·바지선·수출항", "발전용 연료 또는 코크스 제조", "발전·제철·산업"]),
        topic("우라늄 → 전환·농축 → 원자로 연료", "광산에서 얻는 우라늄 정광과 농축 서비스는 다른 제품입니다. 정광을 전환·농축한 뒤 연료로 제작해 원자로에 공급합니다. 채굴량만으로 농축 설비의 능력을 나타낼 수 없으며, 발전소 운영도 별도 산업 활동입니다.", "nuclear", steps=["채굴·정광 U₃O₈", "UF₆로 전환", "우라늄 농축", "연료 제작", "원자로 사용", "사용후핵연료 저장·관리"]),
        topic("농산물·폐유지 → 바이오연료", "미국 연료용 에탄올은 주로 옥수수 전분에서 생산돼 휘발유에 혼합됩니다. 재생 디젤·바이오디젤·지속가능항공유는 원료·공정·제품 규격이 서로 다릅니다. 기업을 비교할 때 식물성 기름·동물성 지방·폐식용유 등 투입 원료와 실제 제품을 구분합니다.", "ethanol biofuels", steps=["곡물·유지·폐기물 원료", "전처리", "발효·정제 또는 연료 전환", "혼합·판매", "도로 운송·항공 고객"]),
    ]),
    dict(id="products", title="서로 구별해야 할 제품·단위", intro="이름이 비슷해도 가격 기준, 거래 단위와 고객이 다를 수 있습니다.", entries=[
        topic("원유의 경질·중질, 저유황·고유황", "API 비중은 원유의 밀도를 나타내는 척도이며, 황 함량도 정제 공정에 영향을 줍니다. 더 무거운 원유는 가벼운 고부가 제품을 얻기 위해 추가 가공이 필요할 수 있습니다. 원유를 모두 동일한 투입 원료로 취급하면 회사별 조달 구조를 놓칩니다.", "refining"),
        topic("가스의 부피와 열량", "천연가스의 거래·운영 자료에는 부피와 열량 단위가 함께 쓰입니다. Bcf는 10억 입방피트, MMBtu는 100만 British thermal units입니다. 가스 조성에 따라 단위 부피의 열량이 달라 고정 환산계수로 모든 제품을 비교할 수 없습니다.", "gas basis", caveat="회사별 단위·환산 가정과 원문 정의를 먼저 확인합니다."),
        topic("액화 용량과 실제 판매량", "LNG 설비의 명목 연간 생산능력과 특정 기간에 실제로 생산·판매한 물량은 다릅니다. 연료 사용, 정비와 운전 조건도 영향을 줍니다. mtpa는 연간 백만 미터톤의 능력 표시이며, 한 분기의 판매량과 직접 더하지 않습니다.", "lng"),
        topic("발전용 석탄과 점결탄", "같은 중량의 석탄이어도 열량과 품질이 다릅니다. 제철용 코크스를 만드는 점결탄은 원료 용도와 가격 조건을 따로 확인합니다. 기업의 발전용·제철용 판매 구성을 제품별로 나눠 읽습니다.", "coal coking"),
        topic("바이오디젤과 재생 디젤", "두 연료는 비슷한 원료를 사용할 수 있지만 제조 공정과 화학적 성질, 혼합·사용 규격이 다릅니다. 재생 디젤의 설비능력 전체를 지속가능항공유 생산능력으로 바꾸어 적지 않습니다. 실제 전환 설비와 제품 승인 범위를 확인합니다.", "biofuels"),
    ]),
    dict(id="calculations", title="수치의 정의·계산법", intro="계산 구조를 설명합니다. 아래 식으로 현재 시세를 계산하거나 투자 판단을 제시하지 않습니다.", entries=[
        topic("3:2:1 정제 스프레드", "원유 3배럴을 휘발유 2배럴과 초저유황 경유 1배럴로 가공한다고 가정한 가격 차이입니다. 제품 선물의 달러/갤런을 달러/배럴로 바꾸기 위해 42를 곱합니다.", "crack", formula="(2 × 휘발유 가격 × 42 + 경유 가격 × 42 − 3 × 원유 가격) ÷ 3", caveat="같은 만기·기준 시장의 가격을 사용합니다. 실제 수율, 에너지·운송·인건비·정비·규제 비용을 차감한 정유사 이익은 아닙니다."),
        topic("가스 지역 베이시스", "지역 거래 허브와 기준 허브 사이의 가격 차이입니다. 생산지와 판매지의 수급·운송 여건을 구분해 보기 위한 값입니다.", "basis", formula="동일 기간 지역 가스 가격 − 동일 기간 Henry Hub 가격", caveat="둘 다 같은 열량 단위와 가격 유형을 사용해야 합니다. 회사의 실제 판매가격에는 계약·품질·운송·헤지 조건이 별도로 반영될 수 있습니다."),
        topic("정유 가동률", "EIA 통계에서는 원유 증류설비의 투입량을 가동 가능한 설비능력과 비교합니다. 설비별 운전 여건과 기간 평균 방식이 있으므로 분모의 정의를 확인합니다.", "weekly", formula="원유 증류설비의 총 투입량 ÷ 가동 가능한 증류설비능력 × 100", caveat="정제제품 판매량을 분자로 쓰거나, 원유 처리능력과 전체 공정 처리능력을 섞지 않습니다."),
        topic("제품 공급량(Product supplied)", "EIA는 1차 공급망에서 빠져나간 제품을 국내 소비의 대용치로 사용합니다. 공급·재고·정제 투입·수출 등을 조정한 수급 집계이며 소비자의 카드 결제나 주유소 판매 전수 집계가 아닙니다.", "consumption", caveat="품목별 공급·처분 항목과 통계 조정을 원자료에서 확인합니다. 주간 잠정치와 월간 확정치의 범위를 구별합니다."),
        topic("정제 수율과 부피 증가", "가공 후 제품의 밀도가 투입 원유보다 낮으면 산출물의 총 부피가 더 커질 수 있습니다. 배럴 합계가 늘었다고 물질의 질량이 새로 생긴다는 뜻은 아닙니다.", "refining", caveat="정유소의 처리량·제품 수율과 회사의 총 판매량(외부 구매 재판매 포함)을 구별합니다."),
        topic("확인 매장량(Proved reserves)", "알려진 저류층에서 기존 경제·운영 조건하에 합리적으로 확실하게 회수할 수 있다고 추정하는 양입니다. 탐사 대상 전체 자원량이나 미래 생산의 확정 보장이 아닙니다.", "reserves", caveat="기준일·가격·기술·운영 조건에 따라 추정이 바뀝니다. 기업 간 비교에는 귀속 지분과 제품별 단위를 맞춥니다."),
    ]),
    dict(id="contracts", title="규제·계약을 읽는 순서", intro="가격 외에 실제 사업 범위와 계약 조건을 확인해야 하는 항목입니다.", entries=[
        topic("파이프라인 허가와 요율", "미국 주간 천연가스 파이프라인의 건설·운영 허가는 FERC 관할이며 운송 요율도 관련 제도의 적용을 받습니다. 주내 운송과 주간 운송은 적용 범위가 다를 수 있습니다. FERC는 파이프라인 안전 자체의 담당 기관은 아닙니다.", "pipeline rates", caveat="특정 프로젝트는 허가 신청·승인·착공·가동 중 어느 단계인지 구분합니다. 허가만으로 실제 운송량이나 매출을 계산하지 않습니다."),
        topic("재생연료 의무와 RIN", "RFS의 의무 이행에는 적격 재생연료를 나타내는 RIN의 확보·사용이 연결됩니다. 생산자, 수입자, 정유사와 혼합·판매 사업자의 역할이 다르므로 같은 제도가 모든 기업에 같은 매출 항목을 만들지는 않습니다.", "rin rfs", caveat="연료 적격성·연도별 의무·인센티브는 서로 구별합니다. 오래된 자료의 세율이나 지원액을 현재 조건으로 옮기지 않습니다."),
        topic("사업 관계의 확인 · 백과 편집 기준", "기업 관계도에서는 실제 발표나 공시에 이름이 나오는 거래 상대를 연결합니다. 공동사업 지분, 원료 공급, 제품 구매, 설비 시공, 기술협력은 역할을 각각 표시하고, 계약 체결·건설·가동 시점을 구분합니다.", "", caveat="이 항목은 밀키웨이의 편집 기준입니다. 같은 지역에서 영업하거나 같은 ETF에 포함됐다는 이유로 공급·고객 관계를 만들지 않습니다."),
    ]),
]


def snapshot():
    """Caller-owned plain data: renderers cannot mutate the shared reading notes."""
    return deepcopy(dict(
        title="Energy 산업 구조", checked_at=CHECKED,
        scope="GICS Energy의 7개 세부 업종과 원유·가스·LNG·석탄·원자력 연료·바이오연료의 흐름을 정리합니다. 기업별 조사·관계 검증은 별도로 진행 중입니다.",
        classification_note="산업 구조는 GICS 기준입니다. 개별 기업의 공식 코드 확인과는 별개이며, 무료 운용사 구성 자료가 미국 전체 기업 원장을 뜻하지는 않습니다.",
        industries=[dict(code=code,name=name,label=label,body=body,source_ids=['gics']) for code,name,label,body in INDUSTRIES],
        sections=SECTIONS, sources=SOURCES,
    ))
