"""Visible accounting scope and explicit analytical comparisons from reviewed notes."""
from copy import deepcopy
from .company_energy_sources import fact

FINANCIAL_SYMBOLS = ('AESI', 'AM', 'AR', 'AROC', 'BKR', 'COP', 'CQP', 'CVX', 'DINO', 'DTI', 'DTM', 'DVN', 'EOG', 'EPD', 'EQT', 'ET', 'EXE', 'FANG', 'FLOC', 'FTI', 'FTK', 'HAL', 'HESM', 'HP', 'KGS', 'KLXE', 'KMI', 'KNTK', 'LBRT', 'LNG', 'MPC', 'MPLX', 'NBR', 'NOV', 'OKE', 'OXY', 'PAA', 'PAGP', 'PSX', 'PTEN', 'PUMP', 'RES', 'RNGR', 'RRC', 'SLB', 'SND', 'SUN', 'TRGP', 'TTI', 'USAC', 'VLO', 'WES', 'WFRD', 'WHD', 'WMB', 'WTTR')

COMPARISONS = {
 'CVX': '상류 자원·개발·생산 원가와 하류 정제·제품 유통을 따로 비교합니다. LNG는 프로젝트 지분·계약·출구, 연료는 정유·운임·판매망이 비교 기준입니다.',
 'COP': '독립 탐사·생산사의 자원·생산 원가·개발 투자·판매 경로를 비교합니다. LNG 지분·계약 사업과 직접 정유 사업은 다른 범위이며 PSX를 COP 연결 사업으로 포함하지 않습니다.',
 'VLO': '정유는 원료·정제 수율·가동률·출하 시장, 재생 디젤은 유지류 원료·수소·규제 크레딧, 에탄올은 옥수수·에너지·부산물과 판로로 비교합니다.',
 'XOM': '상류·LNG와 정유·화학·특수제품을 각각 자원·개발 원가·가동률·판매 경로로 비교합니다. 포집·운송·저장 계약은 고객 개발 단계와 현재 영업 실적을 나누어 읽습니다.',
 'SHEL': 'LNG·상류·화학·제품 유통·전력의 사업별 비용·계약·판매망을 비교합니다. 액화 능력·생산 지분·마케팅 거래량은 서로 다른 분모입니다.',
 'BP': '상류·가스·LNG와 연료·윤활유 판매 사업을 따로 비교합니다. 자산 매각·계약·재편은 기준일에 따라 사업 범위를 바꾸며 단순 규모만으로 직접 경쟁을 확정하지 않습니다.',
 'TTE': '원유·가스·LNG·정유·화학과 통합 전력의 시장을 구별합니다. 생산·정제 원가, 장기 계약, 전력 가동·판매와 개발 투자 기준을 비교합니다.',
 'E': '원유·가스 생산, 글로벌 가스·LNG, 정유·바이오·화학과 전력 사업을 따로 비교합니다. 운영사 역할·프로젝트 지분·계약 판로와 전체 연결 매출은 다른 기준입니다.',
 'EQNR': '노르웨이·해외 생산, 판매·물류·처리와 전력의 자원·개발 원가·출구·가동을 비교합니다. 국가 자원 판매 역할과 회사 자체 생산, 2025 REN과 2026 Power 범위를 구별합니다.',
 'PBR': '브라질 심해 생산·FPSO·정유·연료·가스의 비용·가동·출하 경로를 비교합니다. 프로젝트 총능력과 회사 귀속량, 국내외 시장의 제품 기준을 구별합니다.',
 'EC': '콜롬비아 생산·정유·수송과 ISA 송전·도로의 경쟁·규제 범위를 나눕니다. 송전 수입을 발전 상품 판매로 바꾸거나 COP 표시 금액을 USD 규모로 비교하지 않습니다.',
 'YPF': 'Argentina 셰일 자원·개발·국내 정유·연료 유통을 비교합니다. LNG 개발과 장래 수출 계약·처리능력을 현재 판매 사업으로 간주하지 않습니다.',
 'FTK': '현장 약품·배합과 데이터·발전의 고객·기술·비용을 각각 비교합니다. ProFrac 관련 매출과 제3자 고객, 모회사 연결 매출과 자체 공시 범위는 다릅니다.',
 'NBR': '계약 시추는 리그 성능·인력·가동·지역 계약 조건, 기술·장비는 공급·자동화·서비스로 비교합니다. 자체 리그 내부 기술 거래는 외부 시장 매출이 아닙니다.',
 'NOV': '시추·완결·생산 장비와 에너지 설비·기술의 입찰·납기·설치 기반·정비를 비교합니다. 제조 판매·서비스·임대, 내부 부문 공급과 외부 고객 매출은 구별합니다.',
 'RNGR': '유정 서비스 리그, 와이어라인과 처리·부대 서비스를 지역 수요·가동 시간·인력·장비·가격으로 비교합니다. 고사양 리그 수가 제품 시장점유율을 뜻하지 않습니다.',
 'TTI': '완결 유체·화학 제품과 물·flowback의 기술·현장 서비스·조달·환경 조건을 따로 비교합니다. 개발 중 광물 자원과 실제 판매 제품은 같은 시장 규모가 아닙니다.',
 'WTTR': '물의 조달·집하·처리·재활용·현장 공급과 약품을 지역·인프라 연결·계약·물량·비용으로 비교합니다. 내부거래 제거와 서비스 처리량의 범위가 다릅니다.',
}

def apply(public):
    # Only the individually inspected, pre-existing missing scope cards above.
    # New profiles must not receive a generic card that masks missing research.
    for symbol in FINANCIAL_SYMBOLS:
        profile = public[symbol]
        revenue = next(row for row in profile['brief'] if row['title'] == '매출이 생기는 구조')
        profile.setdefault('financial_context', []).append(
            fact('연간 재무·매출 비교 범위', revenue['detail'], deepcopy(revenue['source'])))
    for symbol, detail in COMPARISONS.items():
        profile = public[symbol]
        origin = profile['brief'][0]['source']
        profile.setdefault('drivers', []).append(fact('경쟁을 비교하는 기준 · 사업 분석',
            '공시된 사업을 바탕으로 정리한 비교 기준입니다. ' + detail +
            ' 특정 경쟁사와의 실제 거래나 점유율을 입증하는 항목은 아닙니다.', deepcopy(origin)))
