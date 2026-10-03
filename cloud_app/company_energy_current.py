"""Dated current-business additions from individually read public originals.

Annual financial archives keep their own periods. Transaction targets and sellers
retain distinct identities; a completed acquisition is not an ongoing partnership.
"""
from copy import deepcopy
from .company_energy_sources import fact, report
from .company_research_notes import profile, relation, source

MGY_CLOSE = source('Magnolia · WildFire 인수 완료·합병 8-K',
    'https://www.sec.gov/Archives/edgar/data/1698990/000110465926107498/tm2625234d1_8k.htm', '2026-09-14')
MGY_UPDATE = source('Magnolia · 인수 후 사업·자산 매각 현황',
    'https://www.magnoliaoilgas.com/investors/press-releases/year/2026/10012026', '2026-10-01')
DTM_UPDATE = source('DT Midstream · 2026 Q2 장기 계약·확장 단계',
    'https://www.sec.gov/Archives/edgar/data/1842022/000114036126030142/ef20078985_ex99-1.htm', '2026-07-30')
CNQ_UPDATE = source('Canadian Natural · 2026 Q2 중간 보고서 p.7',
    'https://www.cnrl.com/wp-content/uploads/2026/08/26-Q2-Interim-Report.pdf#page=7', '2026-08-06')
PBR_UPDATE = source('Petrobras · 2026 Q2 생산·P-79 가동',
    'https://agencia.petrobras.com.br/en/w/negocio/petrobras-lucra-r-52-4-bilh%C3%B5es-no-segundo-trimestre-de-2026', '2026-08-06')
TTE_UPDATE = source('TotalEnergies · 2026 Q2 주요 사업 변화',
    'https://www.sec.gov/Archives/edgar/data/879764/000110465926086078/tot-20260630xex99d2.htm', '2026-07-23')
YPF_UPDATE = source('YPF · 2026 상반기 중간 재무·거래 주석',
    'https://www.sec.gov/Archives/edgar/data/904851/000119312526354159/d173514d6k.htm', '2026-08-10')

# Every entry records a company-specific fact and its actual reporting scope.
CURRENT = {
    'CAPL': [fact('2026 Q2 · 판매액과 실제 물량',
        '분기 연료 판매 매출은 전년보다 26% 늘었지만 평균 판매가격이 43% 오른 반면 판매량은 11% 줄었습니다. 회사는 기존 사업 물량 감소와 딜러 계약의 순감소를 설명합니다. 매출 증가를 연료 수요·판매량 증가로 해석하지 않습니다.', report('CAPL', 'quarter'))],
    'CNQ': [fact('2026 Q2 · Baobab 생산 재개',
        'FPSO 보수 완료 후 Baobab 생산이 2026년 6월 재개됐습니다. 해외 탐사·생산의 분기 원유 평균은 하루 10,390배럴이며, Baobab 재개 후 순귀속량 약 10,000 BOE/일은 별도 자산·기간·단위입니다. 북해의 계획 폐쇄·철거 영향도 구분합니다.', CNQ_UPDATE)],
    'CNX': [fact('2026 Q2 · 가스 물량과 헤지 범위',
        '분기 판매량은 151.5 Bcfe로 전년 167.6 Bcfe보다 줄었습니다. 원유·가스·NGL 매출 3억9,000만 달러와 파생상품 현금 정산 4,500만 달러를 더한 비GAAP 4억3,500만 달러는 다른 지표입니다. 헤지 정산을 제품 판매 매출로 합치지 않습니다.', report('CNX', 'quarter'))],
    'CRGY': [fact('2026 상반기 · Vital 인수 회계 범위',
        'Vital 결합은 2025년 12월 완료된 거래입니다. 2026년 상반기 주석은 취득가격 배분이 잠정치이며 측정기간 조정이 진행 중임을 설명합니다. 회계 조정을 새로운 인수·생산 개시로 표시하거나 결합 전 연간 실적을 현재 포트폴리오와 그대로 비교하지 않습니다.', report('CRGY', 'quarter'))],
    'CVI': [fact('2026 Q2 · 재생연료 사업 재분류',
        'Wynnewood 재생 디젤 설비는 2025년 12월 탄화수소 처리로 전환됐고, 분기 공시 시점에는 재생원료 처리·재생 디젤 판매를 하지 않습니다. 2026년 1분기부터 Renewables가 독립 보고 부문에서 빠져 비교 기간도 Other로 재분류됐습니다. 2025년 매출표와 현재 보고 부문을 구분합니다.', report('CVI', 'quarter'))],
    'DTI': [fact('2026 Q2 · 지역 부문과 내부거래',
        'Titan 인수 이후 Western Hemisphere와 Eastern Hemisphere의 두 보고 부문으로 시추 공구 임대·제품 판매를 관리합니다. 부문 간 거래를 제거한 외부 고객 연결 매출과 각 지역 총매출은 다르며, 지역 비중을 개별 공구 제품 비중으로 바꾸지 않습니다.', report('DTI', 'quarter'))],
    'DTM': [fact('2026 Q2 · 계약 체결과 확장 단계',
        '7월 발표는 Haynesville 확장 장기 계약을 체결했으며 LEAP Phase 5가 하루 200 MMcf의 수송능력을 추가할 계획이라고 설명합니다. Guardian G3는 6월 말 FERC 7(c) 신청 단계이고 Viking 현대화 1단계는 투자 결정 단계입니다. 계약·신청을 완공·실제 수송량으로 표시하지 않습니다.', DTM_UPDATE)],
    'GEL': [fact('2026 Q2 · 해상 자산 매각 후 운영 역할',
        '6월 3일 비핵심 해상 가스 파이프라인·플랫폼을 9,500만 달러에 실제 매각했습니다. 이후에도 장기 운영·정비 서비스를 제공하며 선지급 대금은 서비스 기간에 걸쳐 수익으로 인식합니다. 매각한 자산 소유와 계속 제공하는 서비스를 분리하고 공개되지 않은 매수자 이름은 추정하지 않습니다.', report('GEL', 'quarter'))],
    'HP': [fact('FY2026 Q3 · 해외 시추와 중단 리그',
        '6월 30일 종료 3개월은 이 회사의 FY2026 3분기입니다. 해외 매출은 해당 분기 42.7%이며 9개월 누적 41.7%와 구분합니다. 공시는 사우디의 익명 단일 고객과 일부 중단 리그를 설명합니다. 국가만으로 고객사를 특정하거나 중단 리그를 현재 가동 리그로 세지 않습니다.', report('HP', 'quarter'))],
    'LTBR': [fact('2026 Q2 · 연료 시험과 연구비',
        'INL 관련 연구개발비는 분기 총 연구개발비의 25%, 상반기의 24%입니다. 이 비율은 매출·시장점유율이 아닙니다. BEA 연구 약정의 선급금 190만 달러도 제품 매출이 아닙니다. 2025년 11월 연료 시편의 ATR 삽입 달성과 향후 조사·시험·상용 승인 단계를 구분합니다.', report('LTBR', 'quarter'))],
    'MGY': [fact('2026년 9월 · WildFire 인수 완료',
        '9월 10일 WildFire Intermediate Holdings 지분 100% 인수를 완료했습니다. 매도자는 WildFire Energy I LLC이며 대상 법인은 완료 직후 Magnolia Oil & Gas Operating LLC로 합병됐습니다. 실제 현금 대가는 25억7,000만 달러로 최종 조정 대상이며 Class A 주식 32,203,000주와 6억 달러 채권 의무 승계가 별도입니다.', MGY_CLOSE),
        fact('2026년 10월 · 인수 후 포트폴리오',
        '10월 1일 발표는 3분기 비핵심 자산 매각 완료와 Gonzales County 면적 취득을 확인합니다. 매각 대가 4,750만 달러와 616 순에이커 수취를 구분합니다. 4분기 첫 전체 분기 생산 159~161 Mboe/일은 예상치이며 2025년 연간 재무표나 이미 확정된 실제 생산으로 바꾸지 않습니다.', MGY_UPDATE)],
    'MTDR': [fact('2026 Q2 · 외부 물류 수익과 원료 재판매',
        '분기 외부 물류 매출은 가스 집하·처리 증가와 물 처분 감소를 함께 반영합니다. 매입 천연가스의 재판매·San Mateo 처리 후 잔류가스·NGL 판매는 매입 비용과 매출을 총액으로 표시합니다. 자사 생산 매출·외부 서비스 수수료·매입 가스 판매를 같은 물량·마진 기준으로 비교하지 않습니다.', report('MTDR', 'quarter'))],
    'PR': [fact('2026 Q2 · 유종별 생산과 가스 감산',
        '전년 대비 분기 원유 판매량은 12% 늘었지만 NGL은 12%, 가스는 17% 줄었습니다. 회사는 음의 가스 가격으로 가스 비중이 높은 유정의 생산을 제한했다고 설명합니다. 원유 증가를 전체 석유환산 생산 증가로 바꾸거나 음의 가격을 데이터 오류로 지우지 않습니다.', report('PR', 'quarter'))],
    'RES': [fact('2026 상반기 · 서비스 수요와 인수 비교',
        '상반기 매출 증가에는 Pintail의 6개월 전체 연결과 압력 펌핑·다운홀 공구·코일드튜빙 활동 증가가 포함됩니다. 2025년 비교 기간에는 4월 1일 취득 후 실적만 연결됩니다. 회사는 완결 서비스의 공급 과잉과 효율 개선이 가동률·가격에 부담을 준다고 설명합니다. 인수 효과와 기존 사업 성장을 구분합니다.', report('RES', 'quarter'))],
    'SGU': [fact('FY2026 Q3 · 계절 사업과 인수 범위',
        '6월 30일 종료 보고서는 FY2026 3분기·9개월 누적입니다. 연료·서비스 고객 유형을 구분하고 여름 분기를 겨울 난방 성수기와 그대로 비교하지 않습니다. 9개월 동안 난방유 사업 한 곳을 현금 100만 달러에 취득했지만 이름은 공시하지 않았습니다. 전기 인수 규모·기업 이름을 현재 거래로 옮기지 않습니다.', report('SGU', 'quarter'))],
    'SND': [fact('2026 Q2 · 모래와 현장 저장 시스템',
        'Sand와 SmartSystems 두 보고 부문을 유지합니다. Sand에는 프랙사와 산업용 모래가, SmartSystems에는 현장 저장·하역·공급 시스템 임대가 포함됩니다. 분기 매출 약 1억1,510만 달러와 판매량 약 186만4,000톤의 전년 대비 증가는 물량과 소폭 가격 상승을 반영합니다. 총매출을 모래 제품 매출로만 표시하지 않습니다.', report('SND', 'quarter'))],
    'TTE': [fact('2026 Q2 · ECA 시운전과 태양광 매각',
        '7월 9일 ECA LNG의 첫 화물 출하를 발표했습니다. TotalEnergies 지분 16.6%와 상업운전 이후 20년간 연 170만 톤 구매 계약은 별도 범위이며 시운전 화물이 상업운전 완료를 뜻하지 않습니다. 같은 날 유럽 7개국 170 MW 분산 태양광 포트폴리오를 Amarenco·AMPYR에 실제 매각했다고 발표했습니다.', TTE_UPDATE)],
    'VTS': [fact('2026 Q2 · 생산과 익명 구매자 집중',
        '분기 생산은 하루 17,354 BOE이며 원유 비중은 60%입니다. 직접 운영 자산 매출의 82%는 두 구매자에 집중됐지만 공시는 이름을 밝히지 않습니다. 전체 회사 매출의 고객 점유율이나 비운영 자산 구매자 집중으로 확대하지 않습니다. Lucero 실적은 2025년 3월 7일 이후 연결된 비교 범위입니다.', report('VTS', 'quarter'))],
    'WKC': [fact('2026 Q2 · 항공 서비스 인수 후 조정',
        'Universal Trip Support는 2025년 11월 5일 취득 완료됐고 2026년 1분기에는 운전자본 조정 대금 830만 달러를 추가 지급했습니다. 항공·육상·해상의 세 보고 부문과 항공 여행 지원 서비스를 구분합니다. 2025년 연간 매출에는 취득 후 일부 기간만 연결되므로 전체 연간 서비스 매출로 해석하지 않습니다.', report('WKC', 'quarter'))],
    'PBR': [fact('2026 Q2 · P-79 실제 생산 개시',
        'P-79는 5월 첫 원유 생산, 6월 가스 주입을 시작했습니다. 회사 귀속 원유·가스 생산 334만 BOE/일과 회사가 운영하는 자산 전체 487만 BOE/일은 다른 범위입니다. P-80·P-82·P-83은 발표 시점에 2027년 예정이므로 현재 가동 생산으로 포함하지 않습니다.', PBR_UPDATE)],
    'YPF': [fact('2026 상반기 · 취득 완료와 LNG 조건',
        'Vista와의 Bandurria Sur·Bajo del Toro 거래는 5월 7일 완료됐습니다. Bandurria Sur 직접·간접 지분 44.9%와 Bajo del Toro 관련 직접 지분 65%를 구분합니다. 6월 Eni·XRG의 UPCO ARLNG 참여 계약은 승인 등 완료 조건이 남아 있으며 각 32%·YPF 36%는 완료 후 예정 지분입니다. LNG 개발 지분을 현재 생산·매출로 바꾸지 않습니다.', YPF_UPDATE)],
    'NC': [fact('2026 Q2 · Sabine 인계 의무와 완료 확인',
        '공시는 SWEPCO가 2026년 10월 Sabine 통제권을 인수할 계약상 의무를 설명합니다. 10월 4일 검토에서는 실제 인계 완료를 확인할 후속 원문을 확보하지 못했습니다. 예정일이 지났다는 이유로 인계 완료·계약 종료를 확정하지 않습니다.', report('NC', 'quarter'))],
}

PRIVATE = {
    'wildfire-intermediate-holdings': profile('WildFire Intermediate Holdings, LLC · 합병 전 거래 대상', MGY_CLOSE,
        'Magnolia가 2026년 9월 10일 지분 100%를 취득한 법인입니다. 완료 직후 Magnolia Oil & Gas Operating LLC로 합병돼 현재 독립 법인으로 표시하지 않습니다.',
        '이 기록은 인수 대상 법인과 거래 구조를 설명합니다. 합병 전 실적·비감사 결합 가정치를 현재 독립 기업의 매출로 만들지 않습니다.'),
    'wildfire-energy-i': profile('WildFire Energy I LLC · 거래 매도자', MGY_CLOSE,
        'Magnolia의 2026년 WildFire 인수 계약 매도자입니다. WildFire Intermediate Holdings 지분을 매도한 법인으로 대상 법인·Magnolia와 구분합니다.',
        '공시는 매매대금과 주식·채무 승계를 설명합니다. 거래 대가를 이 법인의 제품 판매 매출로 표시하거나 매매를 지속적 공급 계약으로 바꾸지 않습니다.'),
    'amarenco-tte-solar': profile('Amarenco · TotalEnergies 태양광 거래 역할', TTE_UPDATE,
        '2026년 7월 TotalEnergies의 유럽 분산 태양광 자산 매각 상대 중 하나입니다. 이 기록은 해당 거래에서의 역할을 설명합니다.',
        '170 MW는 매각 포트폴리오 전체의 설비능력입니다. Amarenco 단독 취득량·회사 매출·상장 종목을 추정하지 않습니다.'),
    'ampyr-tte-solar': profile('AMPYR · TotalEnergies 태양광 거래 역할', TTE_UPDATE,
        '2026년 7월 TotalEnergies의 유럽 분산 태양광 자산 매각 상대 중 하나입니다. 이 기록은 해당 거래에서의 역할을 설명합니다.',
        '170 MW는 두 매수자 거래 포트폴리오 전체이며 개별 법인별 배분·매출은 이 발표로 확정하지 않습니다. 비슷한 이름의 법인에 임의로 연결하지 않습니다.'),
}
EDGES = {
    'MGY': [relation('WildFire Intermediate Holdings, LLC · 합병 전 거래 대상', None, 'transaction',
        '2026-09-10 지분 100% 인수 완료 직후 Magnolia Operating으로 합병. 현재 독립 자회사 아님.', MGY_CLOSE, 'wildfire-intermediate-holdings'),
        relation('WildFire Energy I LLC', None, 'transaction',
        '2026-09-10 완료 WildFire 지분 인수의 매도자. 인수 대상 법인과 별개.', MGY_CLOSE, 'wildfire-energy-i')],
    'TTE': [relation('Amarenco', None, 'transaction', '2026-07-09 유럽 170 MW 분산 태양광 포트폴리오 매각 상대 중 하나. 개별 배분 미확정.', TTE_UPDATE, 'amarenco-tte-solar'),
        relation('AMPYR', None, 'transaction', '2026-07-09 유럽 분산 태양광 매각 상대 중 하나. 지속적 공급·협력 계약으로 해석하지 않음.', TTE_UPDATE, 'ampyr-tte-solar')],
    'YPF': [relation('Vista Energy', 'VIST', 'transaction', '2026-05-07 Bandurria Sur·Bajo del Toro 관련 거래 완료. 다른 광구의 공동 운영 관계와 구분.', YPF_UPDATE)],
}


def apply(public):
    for symbol, notes in CURRENT.items():
        public[symbol].setdefault('drivers', []).extend(deepcopy(notes))
