"""Reviewed gas, NGL and LNG businesses and documented operating links.

Annual tables describe their own periods. Later project releases supersede the
construction status, never the historical revenue scope. No model calls occur.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_research_notes import profile, relation, source

WMB, KMI, TRGP, OKE, LNG = (report(s) for s in ('WMB', 'KMI', 'TRGP', 'OKE', 'LNG'))
WMB_Q, KMI_Q, TRGP_Q, OKE_Q, LNG_Q = (
    report(s, 'quarter') for s in ('WMB', 'KMI', 'TRGP', 'OKE', 'LNG'))

MOMENTUM = source('Williams · Momentum 인수 완료',
    'https://www.williams.com/2026/09/03/williams-completes-acquisition-of-momentum-midstream/', '2026-09-03')
WOODSIDE = source('Williams · Louisiana LNG·가스 공급망 계약',
    'https://investor.williams.com/news-releases/news-release-details/williams-accelerates-wellhead-water-strategy-upstream-asset', '2025-10-22')
POWER = source('Williams · 현장 전력 공동사업',
    'https://www.williams.com/2026/07/13/williams-announces-5-34-billion-investment-in-power-innovation-joint-venture-from-blackstone/', '2026-07-13')
WMB_RESULTS = source('Williams · 2026년 2분기·공동사업 후속 현황',
    'https://investor.williams.com/news-releases/news-release-details/williams-delivers-strong-second-quarter-2026-results-announces', '2026-08-03')
TRIDENT = source('Kinder Morgan · Trident 설계·단계별 일정',
    'https://www.kindermorgan.com/Operations/Projects/Trident-Intrastate-Project', '열람 2026-10-03')
WESTERN = source('Kinder Morgan·Phillips 66·HF Sinclair · Western Gateway 투자 결정',
    'https://ir.kindermorgan.com/news/news-details/2026/Phillips-66-Kinder-Morgan-and-HF-Sinclair-Announce-Final-Investment-Decision-for-Western-Gateway-Pipeline-2026-eaM3IVIktJ/default.aspx', '2026-08-11')
STX = source('Kinder Morgan · South Texas 자산 인수·공동 운영',
    'https://ir.kindermorgan.com/news/news-details/2023/Kinder-Morgan-Closes-on-the-1.815-Billion-Acquisition-of-NextEra-Energy-Partners-South-Texas-Assets/default.aspx', '2023-12-28')
CO2 = source('Kinder Morgan · CO₂ 공급·운송망',
    'https://www.kindermorgan.com/Operations/CO2/Index', '열람 2026-10-03')
EOG_IPM = source('Cheniere·EOG · 가스 공급 IPM 증액·연장 계약',
    'https://lngir.cheniere.com/news-events/press-releases/detail/240/cheniere-and-eog-increase-volume-and-extend-term-of', '2022-02-24')
CNQ_IPM = source('Cheniere·Canadian Natural · 2030년 개시 IPM 계약',
    'https://lngir.cheniere.com/news-events/press-releases/detail/319/cheniere-signs-long-term-integrated-production-marketing', '2025-05-28')
JERA_SPA = source('Cheniere·JERA · 2029–2050 LNG 구매 계약',
    'https://lngir.cheniere.com/news-events/press-releases/detail/323/cheniere-and-jera-sign-long-term-lng-sale-and-purchase', '2025-08-07')
CPC_SPA = source('Cheniere·CPC · LNG 인도 계약',
    'https://lngir.cheniere.com/news-events/press-releases/detail/332/cheniere-and-cpc-sign-long-term-lng-sale-and-purchase', '2026-02-26')
PETROBRAS_SPA = source('Cheniere·Petrobras · LNG 구매 계약',
    'https://lngir.cheniere.com/news-events/press-releases/detail/346/cheniere-and-petrobras-sign-long-term-lng-sale-and-purchase', '2026-09-29')
STAGE3 = source('Cheniere · Corpus Christi Stage 3 준공·설비 인계',
    'https://lngir.cheniere.com/news-events/press-releases/detail/345/cheniere-announces-substantial-completion-of-ccl-stage-3', '2026-08-31')
COMMERCIAL = source('Cheniere · IPM·FOB·DAP 판매 구조',
    'https://www.cheniere.com/about/marketing-and-commercial', '열람 2026-10-03')

PUBLIC = {
    'WMB': profile('Williams', WMB,
        '천연가스를 생산지에서 모아 처리하고, 장거리 파이프라인·저장을 통해 발전·도시가스·산업·LNG 고객에게 연결합니다. 주요 사업은 운송·전력·Gulf, 북동부 집하·처리, 서부 집하·처리, 가스·NGL 판매이며 일부 상류 사업도 있습니다.',
        '2025년 연결 매출 119억5,000만 달러는 서비스 83억4,800만, 현물 상품으로 받은 서비스 대가 1억9,200만, 제품 판매 32억9,000만, 상품 파생상품 순이익 1억2,000만 달러로 구성됩니다. 파이프라인 운송료와 상품 재판매·파생상품 손익을 구분해야 합니다.',
        [('규제 가스 운송·저장', 'Transco·Northwest Pipeline 등이 장기 확정 수송 용량과 저장 서비스를 제공합니다. FERC 요율 또는 협상 요율을 적용합니다.'),
         ('생산지 집하·처리', '유정의 가스를 모아 압축·불순물 제거·NGL 회수 후 간선망에 넘깁니다. 고정 수수료 계약과 일부 상품 가격 연동 계약이 있습니다.'),
         ('NGL·원유·해상 생산 지원', 'NGL 분별·저장과 Gulf 해상 원유 파이프라인·플랫폼의 압축·수분 제거·생산물 처리 서비스를 제공합니다.'),
         ('가스 판매·현장 전력', 'Sequent의 가스·NGL 구매·판매·저장 최적화와 신규 현장 전력 사업을 구분합니다. 발전 설비의 예정 용량은 현재 전력 판매량이 아닙니다.')],
        customers='가스 생산자, 전력·도시가스 사업자, 산업체와 LNG 사업자가 고객입니다. 2025년 Transco 최대 고객 Duke Energy는 Transco 매출의 약 9%, Northwest Pipeline의 Puget Sound Energy는 해당 회사 매출의 약 31%입니다. Williams 전체 매출 비중이 아닙니다.',
        inputs='가스·NGL 구매, 압축기·전력·연료, 파이프·밸브와 건설·정비 서비스가 필요합니다. 생산자의 시추·생산 활동은 처리 물량, 신규 발전·LNG 설비는 간선망 연결 수요에 연결됩니다.',
        competition='운송·저장 경로, 집하망의 생산지 접근성, 요율·연결성·신뢰성이 경쟁 조건입니다. 주가 비교용 동종 기업 명단을 실제 거래나 확정 경쟁사 명단으로 사용하지 않습니다.'),
    'KMI': profile('Kinder Morgan', KMI,
        '천연가스·연료·원유·CO₂를 운송·저장하고 터미널을 운영하는 북미 에너지 기반시설 기업입니다. 천연가스 파이프라인, 제품 파이프라인, 터미널, CO₂의 네 보고 부문이며 CO₂ 부문에는 원유 생산과 재생가스 사업도 포함됩니다.',
        '2025년 연결 매출은 169억3,700만 달러입니다. 외부 고객 기준 천연가스 파이프라인 109억9,000만, 제품 파이프라인 26억8,600만, 터미널 20억9,400만, CO₂ 11억6,700만 달러입니다. 천연가스 부문에는 운송 수수료뿐 아니라 가스 판매도 포함됩니다.',
        [('가스 운송·저장·처리', '장거리·지역 간선망, 집하·처리·LNG 관련 시설로 생산지·발전소·산업체·수출 거점을 연결합니다.'),
         ('정유제품·원유 물류', '휘발유·경유·항공유와 원유·콘덴세이트를 운송·저장합니다. 수송 용량·최소 물량·실제 처리량 계약을 구별합니다.'),
         ('액체·벌크 터미널', '연료·화학·에탄올 등 액체와 코크스·금속·광물 등 벌크 화물을 처리합니다. Jones Act 제품 탱커도 포함됩니다.'),
         ('CO₂·증진회수·재생가스', 'CO₂ 공급·수송은 성숙 유전의 증진회수를 지원합니다. 유전 원유 생산과 바이오가스·RNG의 상품 가격 노출은 수수료 사업과 다릅니다.')],
        customers='생산자·정유사·발전·도시가스·산업·LNG 사업자가 운송·처리·저장 서비스를 구매합니다. 2025년 연결 매출의 10% 이상인 단일 외부 고객은 없었지만, 이는 고객 이름이나 거래가 존재하지 않는다는 뜻은 아닙니다.',
        inputs='파이프·압축기·펌프·터미널 탱크, 건설·정비·연료·전력이 필요합니다. 가스 재판매에는 매입 가스, CO₂ 유전에는 CO₂·생산 서비스, RNG에는 유기성 원료·정제 설비가 필요합니다.',
        competition='같은 생산지·수요처를 연결하는 다른 파이프라인·저장·처리 서비스와 위치·요율·유연성·신뢰성으로 경쟁합니다. 터미널은 선박·철도·트럭·배관 접근성과 취급 제품이 중요합니다.'),
    'TRGP': profile('Targa Resources', TRGP,
        'Permian 등 미국 생산지의 천연가스를 집하·처리해 NGL과 잔여 가스로 나누고, NGL을 운송·분별·저장·수출하는 기업입니다. 집하·처리와 물류·운송 두 부문이 생산지에서 Mont Belvieu 및 Gulf 수출 거점까지 이어집니다.',
        '2025년 연결 매출 170억2,830만 달러는 상품 판매 144억350만과 중류 서비스 수수료 26억2,480만 달러입니다. 상품 판매에는 파생상품 순손실 1억6,030만 달러가 반영돼 고객 계약상 제품 매출의 단순 합계와 다릅니다.',
        [('천연가스 집하·처리', '유정 가스를 집하·압축·탈수·처리해 파이프라인 품질의 잔여 가스와 NGL을 회수합니다. 산성 가스 처리·주입 설비도 운용합니다.'),
         ('NGL 운송·분별', '원액 NGL을 Mont Belvieu 등으로 운송하고 에탄·프로판·부탄 등 순수 성분으로 분리합니다.'),
         ('저장·LPG 수출', '저장 탱크·터미널·선적 거점을 통해 국내 석유화학·연료 시장과 국제 LPG 시장을 연결합니다.'),
         ('원유·콘덴세이트', '생산지에서 모은 원유·콘덴세이트를 터미널·파이프라인·판매 경로에 연결합니다. 천연가스 처리량과 별도 단위입니다.')],
        customers='가스·원유 생산자와 NGL 구매자, 석유화학·정유·LPG 시장을 연결합니다. 생산자에게 서비스를 제공하면서 해당 생산물 일부를 구매해 다시 파는 거래도 있어 고객·공급자 역할이 겹칠 수 있습니다.',
        inputs='매입 천연가스·NGL·원유, 압축·냉각·분별에 쓰는 전력·연료, 처리약품과 설비·건설·정비가 필요합니다. 생산지 처리 능력과 하류 파이프라인·분별·수출 능력이 함께 맞아야 합니다.',
        competition='집하·처리는 유정·생산지에 대한 접근, 처리 용량·서비스·계약 조건으로, 물류는 분별·저장·운송·수출 연결성과 수수료로 경쟁합니다. 같은 basin 사업자라도 연결 거점과 취급 물질을 구분합니다.'),
    'OKE': profile('ONEOK', OKE,
        '천연가스 집하·처리, NGL, 가스 파이프라인, 정유제품·원유의 네 사업을 연결합니다. Magellan·EnLink·Medallion 인수로 가스·NGL 외에 원유·연료 물류도 큰 부분을 차지합니다.',
        '2025년 연결 매출은 336억2,900만 달러입니다. 내부거래 제거 후 액체 상품 255억6,600만, 잔여 천연가스 33억1,200만, 교환·집하·처리 14억7,000만, 운송·저장 31억3,700만, 기타 1억4,400만 달러입니다. 수수료 기반 이익 약 90%라는 설명은 매출의 90%가 수수료라는 뜻이 아닙니다.',
        [('천연가스 집하·처리', '생산지의 가스를 집하·처리하고 잔여 가스·NGL을 판매합니다. Permian·Rocky Mountain·Midcontinent 등의 생산 활동과 연결됩니다.'),
         ('NGL 교환·분별·물류', '생산지의 혼합 NGL을 모아 처리·분별하고 Conway·Mont Belvieu 등 수요 거점에 순수 성분을 공급합니다.'),
         ('가스 운송·저장', '확정 용량 및 실제 사용량 기반 가스 수송·저장·판매를 제공합니다. 비규제 집하 서비스와 규제 간선망을 구분합니다.'),
         ('정유제품·원유 물류', '제품·원유를 집하·운송·저장·유통·혼합·판매합니다. 정유·수출 거점의 연결과 설비의 실제 가동 범위가 중요합니다.')],
        customers='가스·원유 생산자, 정유·석유화학·연료 유통·수출 고객에 공급·서비스를 제공합니다. 2025년 한 고객이 연결 매출 약 12%였지만 해당 주석은 이름을 공개하지 않습니다. 그 고객을 추정해 관계도에 넣지 않습니다.',
        inputs='가스·NGL·원유·연료의 구매와 파이프·압축·분별·탱크·선적 설비, 전력·연료·정비·건설이 필요합니다. 상품 거래 매출과 매출원가가 크므로 총매출을 운송 수익성으로 읽으면 안 됩니다.',
        competition='공급 지역·수요 거점에 도달하는 물류망, 교환·분별 서비스 조건, 수수료·신뢰성과 대체 경로가 경쟁 조건입니다. 공동사업 상대가 일부 다른 지역·사업에서 경쟁할 수 있으나 공동사업 자체는 경쟁 관계가 아닙니다.'),
    'LNG': profile('Cheniere Energy', LNG,
        '미국 Gulf Coast의 Sabine Pass·Corpus Christi에서 천연가스를 액화해 국제 시장에 판매하는 LNG 기업입니다. 가스 조달·운송, 액화, 선박 용선·수출·고객 인도를 연결하며, Sabine Pass는 상장 자회사 CQP를 통해 운영합니다.',
        '2025년 연결 매출 199억7,600만 달러는 LNG 194억3,500만, 재기화 1억3,600만, 기타 4억500만 달러입니다. LNG 매출에는 파생상품 순이익 3억4,400만 달러가 포함됩니다. 계약된 용량·설비능력·실제 수출량·매출은 서로 다른 수치입니다.',
        [('장기 LNG 판매', '주로 Henry Hub 연동 변동액과 고정 액화 대가를 받습니다. 일반적인 SPA는 화물 취소에도 고정 대가 지급 의무가 있어 단순 현물 LNG 판매와 다릅니다.'),
         ('IPM 가스 조달', '생산자로부터 국제 LNG 지수에서 액화·운송 비용을 뺀 가격으로 가스를 구매하고 Cheniere가 LNG를 판매하는 구조입니다. 생산자는 가스 공급자입니다.'),
         ('FOB·DAP 인도', 'FOB는 출항지 선박 인도, DAP는 목적지 인도 방식입니다. 목적지 인도에서는 용선·물류 범위가 더 넓습니다.'),
         ('재기화·선박 관련 서비스', 'Sabine Pass의 재기화 이용 계약과 선박 재용선·하위 임대 등이 포함됩니다. 원래 LNG 생산설비와 별도 수익 항목입니다.')],
        customers='해외 전력·도시가스·국영 에너지 회사와 국제 LNG 유통사가 구매합니다. JERA·CPC·Petrobras 등의 계약마다 개시일·물량·인도 방식이 다릅니다. 새 계약 물량을 이미 인도한 실적으로 표시하지 않습니다.',
        inputs='북미 천연가스와 운송 용량, 액화 트레인·압축기·냉각·전력·연료, 선박 용선·항만 서비스가 필요합니다. Bechtel은 액화 설비 설계·조달·시공 EPC 상대입니다.',
        competition='글로벌 LNG 공급·가스 조달·용선·수출 설비 개발에서 경쟁합니다. 도착지 가격만 비교하지 않고 액화·운임·원료 가격·계약 인도 범위를 구별합니다.'),
}

_OPERATIONS = {
    'WMB': [
        ('주요 간선망', '2025년 Transco 설계 수송능력은 하루 2,060만 Dth, Northwest Pipeline은 하루 380만 Dth입니다. 에너지 단위 Dth와 가스 부피 Bcf를 동일 수치로 환산하지 않습니다.', WMB),
        ('생산지 집하망', '북동부는 Marcellus·Utica, 서부는 여러 basin의 집하·처리망입니다. Blue Racer 등 비연결 JV의 공시 처리량은 전체 사업 기준으로, Williams 귀속량과 구별합니다.', WMB),
        ('Momentum 인수 완료', '2026년 9월 3일 Momentum Midstream 인수가 완료됐습니다. Haynesville 집하 능력 하루 6 Bcf, 세 take-or-pay 파이프라인 수송능력 하루 4.05 Bcf를 추가합니다. 두 능력은 같은 물량이 지나갈 수 있어 합산하지 않습니다.', MOMENTUM),
        ('Louisiana LNG·JERA 연결', 'Louisiana LNG 지분 10%, Driftwood Pipeline 지분 80%·운영과 가스 조달·연간 150만 톤 LNG 구매 약정을 연결합니다. South Mansfield 생산지 매각 후에도 JERA 자산의 가스 집하·LEG 운송을 맡는 구조입니다.', WOODSIDE),
        ('전력 공동사업', 'Blackstone 주도·Apollo·KKR 참여 자금과 함께 현장 발전 5개 프로젝트를 개발합니다. 2026년 2분기 후속 발표는 JV 확정을 보고했습니다. Williams는 51%와 상업·운영 통제를 유지합니다.', WMB_RESULTS),
    ],
    'KMI': [
        ('네트워크의 범위', '2025년 말 보유 지분 또는 운영 대상은 파이프라인 약 7만8,000마일, 터미널 136곳, 가스 작업 저장능력 약 706 Bcf입니다. 전부 100% 소유라는 의미는 아닙니다.', KMI),
        ('확정 서비스와 실사용 수수료', '고객 계약상 확정 서비스 53억4,200만, 사용량 등 기반 서비스 27억1,900만 달러와 임대·상품 판매 등 수익을 나눠 봅니다. 가스 가격 상승으로 상품 재판매 매출이 늘어도 운송료가 같은 비율로 변하는 것은 아닙니다.', KMI),
        ('Monument 자산 편입', '2026년 5월 1일 Houston권의 225마일 가스 파이프라인·저장 사업을 인수했습니다. 거래 대가 5억300만 달러는 해당 자산의 매출이나 처리능력이 아닙니다.', KMI_Q),
        ('Trident 건설 단계', '현재 공식 설계는 약 219마일·하루 2 Bcf이며 첫 단계 2027년 1분기, 두 번째 단계 2028년 4분기 가동 목표입니다. 과거 발표의 하루 1.5 Bcf를 현재 최종 설계로 표시하지 않습니다.', TRIDENT),
        ('Western Gateway 공동사업', '2026년 8월 최종 투자 결정. Phillips 66 49.9%·Kinder Morgan 35.1%·HF Sinclair 15%로 연료 물류망을 개발합니다. 설계 하루 23만 배럴·완공 목표 2029년이며 인허가 조건이 남아 있습니다.', WESTERN),
    ],
    'TRGP': [
        ('집하·처리 자산', '2025년 말 가스 집하망 약 3만1,600마일과 소유·운영 처리공장 54곳을 공시했습니다. Midland·Delaware 처리 능력과 JV 지분은 전체 공장과 회사 귀속 범위를 구분해야 합니다.', TRGP),
        ('2026년 신규 공장', 'East Pembrook·East Driver는 각각 하루 275 MMcf 규모입니다. 2026년 2분기 공시의 개발 현황은 두 공장의 가동 개시를 보고했으므로 연차보고서의 건설 계획으로 남겨두지 않습니다.', TRGP_Q),
        ('가스 수출 경로 확장', 'Blackcomb는 하루 2.5 Bcf·약 365마일로 2026년 4분기, Traverse는 약 160마일로 2027년 중반 가동 목표입니다. 6월 말에는 건설 중이며 Targa의 비운영 지분은 17.5%입니다.', TRGP_Q),
        ('Stakeholder·Badlands 통합', 'Stakeholder는 2026년 1월 편입돼 Delaware의 집하·처리·산성 가스·CCS 서비스를 보강합니다. Badlands는 2025년 잔여 지분 취득 후 100%로, Blackstone을 현재 공동 소유자로 남기지 않습니다.', TRGP_Q),
    ],
    'OKE': [
        ('부문 총매출과 연결 매출', '2025년 네 부문 매출 합계 385억7,900만 달러에는 내부거래가 포함됩니다. 기타·제거 49억5,000만 달러를 반영한 연결 매출이 336억2,900만 달러입니다. 제거 전 부문 값을 연결 매출 비중으로 표시하지 않습니다.', OKE),
        ('EnLink 연결 범위', '2025년 1월 31일 잔여 EnLink 지분 취득 후 완전 소유했습니다. EnLink를 현재 독립 상장 기업으로 연결하거나 이전 부분 소유 상태로 표시하지 않습니다.', OKE_Q),
        ('LPG 수출 공동사업', 'MPLX와 50:50으로 Texas City Logistics를 개발합니다. 하루 40만 배럴 LPG 수출터미널과 Mont Belvieu–Texas City 배관은 2028년 초 가동 목표이며 MPLX가 시공·운영을 맡습니다.', OKE),
        ('Eiger 가스 파이프라인', 'WhiteWater·MPLX·Enbridge와 개발하는 약 450마일·하루 3.7 Bcf의 Permian–Katy 사업입니다. 2028년 중반 목표이며 ONEOK 총지분 25.5%는 직접 15%와 간접 보유를 합친 수치입니다.', OKE),
    ],
    'LNG': [
        ('두 생산 거점·연결 범위', 'Sabine Pass 6개 대형 트레인은 CQP가, Corpus Christi는 Cheniere가 소유·운영합니다. 2025년 말 CQP의 보통 limited partner 지분 약 48.6%와 일반 파트너 지배로 연결했습니다.', LNG),
        ('Stage 3 완료', '2026년 8월 28일 Bechtel이 Stage 3의 일곱 번째·마지막 트레인을 인계해 실질 준공됐습니다. 회사의 운영 생산능력은 약 5,600만 톤/년으로 늘었습니다. 6월 말 공시의 6개 완료·1개 건설 중 상태를 대체합니다.', STAGE3),
        ('추가 건설과 장기 계약', '2026년 9월 발표의 추가 건설 능력은 약 500만 톤/년입니다. 일반 계약의 고정 대가와 Henry Hub 연동 변동액, IPM의 JKM 연동 가스 매입은 다른 가격 구조입니다.', PETROBRAS_SPA),
        ('JERA 판매 약정', '약 100만 톤/년·FOB 인도·2029–2050년 계약이며 Henry Hub+고정 액화 대가 구조입니다. 미래 약정 물량을 이미 판매한 실적으로 표시하지 않습니다.', JERA_SPA),
        ('CPC 판매 약정', '추가 계약은 최대 120만 톤/년·목적지 인도·2026–2050년입니다. 2018년 체결·2021년 개시한 기존 약 200만 톤/년 계약과 별도입니다.', CPC_SPA),
        ('Petrobras 판매 약정', '2026년 9월 발표 계약은 약 80만 톤/년·FOB·22년 약정입니다. 발표에 없는 개시 연도를 추정하지 않습니다.', PETROBRAS_SPA),
    ],
}
for _symbol, _rows in _OPERATIONS.items():
    PUBLIC[_symbol]['segments'] = [fact(title, detail, origin) for title, detail, origin in _rows]

for _symbol, _rows in {
    'WMB': [('생산지와 계약 물량', '유정 생산량·집하 물량, 고정 수수료·최소 물량 약정·계약 갱신을 확인합니다. 단기 가스 가격보다 생산 활동·계약 조건이 직접 연결되는 서비스가 많습니다.'),
            ('규제·건설·금융', 'FERC 요율·환급, 인허가·건설 일정, 압축·전력·정비 비용과 차입 이자, 신규 발전·LNG 프로젝트의 연결 범위가 반영됩니다.')],
    'KMI': [('서비스와 상품 노출', '확정 용량 수익·실사용 수익·가스 재판매·유전 원유·RNG와 RIN 수익을 구분합니다. 각 사업의 물량·가격·헤지 효과가 다릅니다.'),
            ('시설 가동·비용', '압축·펌프 전력, 연료·인건비·재산세·정비, 설비 장애·기상·규제와 건설 투자를 함께 확인합니다.')],
    'TRGP': [('생산→처리→수출 연결', '유입 가스·NGL 수율, 생산자의 개발 활동, 분별·장거리 배관·수출터미널 가용성이 연결됩니다. 한 시설의 능력만으로 실제 판매량을 설명할 수 없습니다.'),
             ('상품 거래와 서비스', '매입 원료·상품 가격·파생상품 손익과 수수료를 구분합니다. 공장 증설·압축·전력·정비 비용, 가동 개시 시점도 기간 비교에 포함합니다.')],
    'OKE': [('물량과 수수료 계약', '생산자의 시추·생산, 처리·분별·수송 물량, 최소 물량 약정·확정 운송 계약을 확인합니다. fee-based 이익에도 물량 감소 영향은 남습니다.'),
            ('연결 범위·원가', '인수 시점·지분법 사업·내부거래 제거, 상품 구매비·연료·정비·압축·분별 비용과 건설 자본을 구분합니다.')],
    'LNG': [('가격·계약·회계', 'Henry Hub·국제 LNG 지수·계약 고정액·운임과 IPM 공급 조건을 확인합니다. 파생상품 평가손익은 현재 현금 판매량과 다를 수 있습니다.'),
            ('설비·인도·가스 공급', '트레인 가동·정비·가스 배관 용량, EPC 일정·변경 비용·용선·항만 및 수출 허가가 생산·인도에 연결됩니다.')],
}.items():
    _origin = report(_symbol)
    PUBLIC[_symbol]['drivers'] = [fact(title, detail, _origin) for title, detail in _rows]
    PUBLIC[_symbol]['sources'].extend(row[2] for row in _OPERATIONS[_symbol])
    if REPORTS[_symbol].get('revenue_mix'):
        PUBLIC[_symbol]['revenue_mix'] = REPORTS[_symbol]['revenue_mix']

EDGES = {
    'WMB': [
        relation('Duke Energy', 'DUK', 'customer', 'Transco의 가스 운송 고객 · 2025년 Transco 매출 약 9%, Williams 연결 매출 비중 아님', WMB),
        relation('Puget Sound Energy', None, 'customer', 'Northwest Pipeline 가스 운송 고객 · 2025년 해당 자회사 매출 약 31%', WMB, 'puget-sound-energy'),
        relation('Woodside Energy', 'WDS', 'partner', 'Louisiana LNG·Driftwood 배관 개발, Sequent 가스 조달과 LNG 구매를 함께 연결한 운영 협력', WOODSIDE),
        relation('JERA', None, 'customer', 'South Mansfield 가스 자산 매각 후 Williams가 집하·LEG 운송을 계속 제공하는 계약 구조', WOODSIDE, 'jera'),
        relation('Blackstone', 'BX', 'partner', '현장 전력 5개 프로젝트 개발 자금·공동사업 · Blackstone 주도 자금의 비지배 지분 49%, Williams 운영 통제 유지', POWER),
        relation('Apollo Global Management', 'APO', 'partner', 'Blackstone 주도 현장 전력 공동사업 자금에 참여 · 발전 프로젝트명 Apollo와 금융회사를 구별', POWER),
        relation('KKR', 'KKR', 'partner', '관리 보험 기구·계정이 현장 전력 프로젝트 공동사업 자금에 참여', POWER),
        relation('Momentum Midstream', None, 'subsidiary', '2026-09-03 인수 완료 · Haynesville 집하·처리·장기 용량 수송망을 운영', MOMENTUM, 'momentum-midstream'),
        relation('Transco', None, 'subsidiary', 'Gulf Coast에서 동부·New York까지 가스를 수송·저장하는 규제 간선망', WMB, 'transco'),
        relation('Northwest Pipeline', None, 'subsidiary', '미국 서북부 가스 수송·저장망 · 도시가스·발전 수요처 연결', WMB, 'northwest-pipeline'),
        relation('Blue Racer Midstream', None, 'partner', '비연결 지분법 JV 50% · Utica·Marcellus 가스 집하·처리·NGL 물류', WMB, 'blue-racer'),
    ],
    'KMI': [
        relation('Phillips 66', 'PSX', 'partner', 'Western Gateway 연료 물류 개발 · PSX가 신설 배관 시공·운영, KMI가 SFPP 자산·운영 제공', WESTERN),
        relation('HF Sinclair', 'DINO', 'partner', 'Western Gateway 공동사업 15% 참여 · 2029년 목표·인허가 조건부 건설 계획', WESTERN),
        relation('Howard Energy Partners', None, 'partner', 'Dos Caminos 배관 공동 소유 50%·운영 상대 · South Texas 자산 인수 발표에서 확인', STX, 'howard-energy'),
        relation('PEMEX', None, 'partner', '계열 MGI Enterprises가 NET Mexico 배관 10% 보유 · KMI 인수 대상 지분은 90%', STX, 'pemex'),
        relation('Occidental Petroleum', 'OXY', 'partner', 'Occidental Permian이 KMI CO₂·XTO와 Bravo CO₂ 배관 공동 소유 · 증진회수 투입물 운송', CO2),
        relation('ExxonMobil', 'XOM', 'partner', '계열 XTO Energy가 Bravo CO₂ 배관 공동 소유에 참여 · 원유 판매 계약을 뜻하지 않음', CO2),
        relation('Monument Pipeline', None, 'subsidiary', '2026-05-01 인수 완료 · Houston 지역 가스 운송·저장, LNG·유틸리티·산업 고객 연결', KMI_Q, 'monument-pipeline'),
    ],
    'TRGP': [
        relation('ExxonMobil', 'XOM', 'partner', 'WestTX 천연가스 집하·처리 JV · Targa 72.8%·ExxonMobil 27.2%, 실제 처리 운영 관계', TRGP),
        relation('MPLX', 'MPLX', 'partner', 'Centrahoma 처리 JV 지분 40%; Blackcomb 파이프라인 직접 지분 12.5%도 참여 · 서로 다른 프로젝트', TRGP),
        relation('WhiteWater', None, 'partner', 'Blackcomb 가스 배관의 WPC 공동사업 운영·개발 연결 · WPC는 WhiteWater·MPLX·Enbridge 공동 보유', TRGP, 'whitewater'),
        relation('Enbridge', 'ENB', 'partner', 'Blackcomb의 WPC를 통한 간접 공동사업 참여 · Enbridge를 Targa 지분 보유자 전체로 표시하지 않음', TRGP),
        relation('Stakeholder Midstream', None, 'subsidiary', '2026년 1월 편입 · Delaware의 sour gas 처리·집하·탄소 저장을 Targa 운영망에 통합', TRGP_Q, 'stakeholder-midstream'),
        relation('Dovetail Midstream', None, 'subsidiary', '2025년 12월 자산 인수 · Eddy County, New Mexico의 가스 집하·압축 사업', TRGP_Q, 'dovetail-midstream'),
    ],
    'OKE': [
        relation('MPLX', 'MPLX', 'partner', 'Texas City LPG 터미널·MBTC 배관 공동사업 50:50; MPLX 시공·운영 · Eiger 공동사업도 별도 참여', OKE),
        relation('WhiteWater', None, 'partner', 'Eiger Express의 건설·운영 상대 · Permian–Katy 가스 수송 개발, 2028년 중반 목표', OKE, 'whitewater'),
        relation('Enbridge', 'ENB', 'partner', 'Eiger Express 가스 파이프라인 공동 개발 참여 · ONEOK의 직접·간접 지분 합계와 구별', OKE),
        relation('EnLink Midstream', None, 'subsidiary', '2025-01-31 잔여 지분 취득 후 완전 소유 · 집하·처리·물류망을 ONEOK에 연결', OKE_Q, 'enlink-midstream'),
        relation('HF Sinclair', 'DINO', 'customer', 'ONEOK·Magellan 배관의 원유·제품 운송 서비스를 이용 · 원유 생산 공급사 관계와 구별', report('DINO')),
    ],
    'LNG': [
        relation('EOG Resources', 'EOG', 'supplier', '2022년 개정 계약 · JKM 연동 IPM 하루 420,000 MMBtu와 Henry Hub 연동 하루 300,000 MMBtu·15년 · 계약 물량은 실제 인도량 아님', EOG_IPM),
        relation('Canadian Natural Resources', 'CNQ', 'supplier', '2025년 IPM 체결 · 2030년 개시 예상·15년·하루 140,000 MMBtu, JKM에서 고정 액화·운송액 차감', CNQ_IPM),
        relation('Bechtel', None, 'supplier', 'Corpus Christi Stage 3·8/9 트레인 EPC 설계·조달·시공 · Stage 3 마지막 트레인 인계 2026-08-28', STAGE3, 'bechtel'),
        relation('JERA', None, 'customer', '2025년 체결 SPA · 약 100만 톤/년·FOB·2029–2050, Henry Hub+고정 액화 대가', JERA_SPA, 'jera'),
        relation('CPC Corporation, Taiwan', None, 'customer', '2026년 추가 SPA · 최대 120만 톤/년·목적지 인도·2026–2050, 기존 2018년 계약과 별도', CPC_SPA, 'cpc-taiwan'),
        relation('Petrobras', 'PBR', 'customer', '2026-09-29 SPA · 약 80만 톤/년·FOB·22년, 공식 발표에 없는 개시 연도는 추정하지 않음', PETROBRAS_SPA),
        relation('TotalEnergies', 'TTE', 'customer', 'Sabine Pass 재기화 용량 이용 계약 하루 1 Bcf · LNG 화물 구매량이 아니라 재기화 서비스', LNG),
        relation('Cheniere Energy Partners', 'CQP', 'subsidiary', 'Sabine Pass 액화·재기화·Creole Trail 배관 운영 · 상장 MLP로 Cheniere 연결 범위에 포함', LNG),
    ],
    'PSX': [relation('Kinder Morgan', 'KMI', 'partner', 'Western Gateway 신설·기존 연료 배관 공동 개발 · 2026-08 최종 투자 결정', WESTERN),
            relation('HF Sinclair', 'DINO', 'partner', 'Western Gateway 연료 공급 경로 공동 개발 · PSX 49.9%·DINO 15%, 현재 가동망은 아님', WESTERN)],
    'DINO': [relation('Kinder Morgan', 'KMI', 'partner', 'Western Gateway 공동사업 · KMI의 SFPP 기존 배관과 신규 서부 연료 공급 경로 연결', WESTERN),
             relation('Phillips 66', 'PSX', 'partner', 'Western Gateway 공동 개발 · DINO 15%·PSX 신설 배관 시공·운영', WESTERN)],
    'EOG': [relation('Cheniere Energy', 'LNG', 'customer', 'IPM 가스 공급 약정 · Cheniere가 액화·마케팅, 국제 LNG 지수 연동 가스 판매', EOG_IPM)],
}

PRIVATE = {}
for _key, _name, _origin, _business, _role in [
    ('puget-sound-energy', 'Puget Sound Energy', WMB, 'Northwest Pipeline의 주요 가스 운송 고객인 미국 유틸리티입니다.', 'Williams 연결 매출이 아닌 Northwest Pipeline의 2025년 고객 집중도를 이해하는 거래 상대입니다.'),
    ('jera', 'JERA', JERA_SPA, '일본 전력·연료 사업자이자 국제 LNG 구매자입니다.', 'Cheniere에서 2029–2050년 약 100만 톤/년의 LNG를 FOB로 구매하는 계약 상대입니다.'),
    ('momentum-midstream', 'Momentum Midstream', MOMENTUM, 'Haynesville 천연가스 집하·처리·수송망을 운영하며 2026년 9월 Williams에 편입됐습니다.', '생산지를 Gulf Coast LNG·전력·산업 수요처에 연결합니다. 집하 능력과 간선 수송 능력을 합산하지 않습니다.'),
    ('transco', 'Transco', WMB, 'Williams의 규제 천연가스 간선 수송·저장 회사입니다.', 'Texas·Gulf Coast 공급에서 미국 동부·New York 수요처까지 연결합니다. Duke Energy 고객 비중의 분모는 Transco 매출입니다.'),
    ('northwest-pipeline', 'Northwest Pipeline', WMB, 'Williams의 미국 서북부 규제 가스 수송·저장 사업입니다.', 'Puget Sound Energy 등 지역 가스·발전 고객의 수송 용량·저장 수요와 연결됩니다.'),
    ('blue-racer', 'Blue Racer Midstream', WMB, 'Utica·Marcellus에서 가스를 집하·처리하고 NGL을 운송하는 공동사업입니다.', 'Williams의 50% 지분법 투자입니다. 비연결 전체 처리량을 Williams 귀속량으로 표시하면 안 됩니다.'),
    ('howard-energy', 'Howard Energy Partners', STX, 'Dos Caminos 가스 배관의 공동 소유·운영 상대입니다.', 'KMI South Texas망의 Eagle Ford·Mexico·Gulf 수요 연결을 이해하는 운영 기업입니다.'),
    ('pemex', 'PEMEX', STX, 'Mexico 에너지 기업으로 계열 MGI Enterprises가 NET Mexico 배관 지분을 보유합니다.', 'KMI의 배관 인수·Mexico 가스 수송 연결에서 확인한 역할입니다. 이 자료로 회사 전체 공급망을 추정하지 않습니다.'),
    ('monument-pipeline', 'Monument Pipeline', KMI_Q, 'Houston 지역의 가스 운송·저장망으로 2026년 5월 Kinder Morgan에 편입됐습니다.', 'LNG·유틸리티·산업 고객에 서비스를 제공하는 지역망입니다.'),
    ('whitewater', 'WhiteWater', OKE, '미국 가스 배관의 개발·건설·운영 공동사업 상대입니다.', 'Eiger Express를 건설·운영하며 ONEOK·MPLX·Enbridge가 개발에 함께 참여합니다. 프로젝트마다 지분·역할을 구분합니다.'),
    ('stakeholder-midstream', 'Stakeholder Midstream', TRGP_Q, 'Permian Delaware의 가스 집하·처리·산성 가스 처리·탄소 저장 자산입니다.', '2026년 1월 Targa에 편입돼 생산지 처리와 하류 물류망에 연결됩니다.'),
    ('dovetail-midstream', 'Dovetail Midstream', TRGP_Q, 'New Mexico Eddy County의 천연가스 집하·압축 자산입니다.', '2025년 12월 Targa가 인수한 운영 자산이며, 과거 매도자와 현재 운영 회사를 구별합니다.'),
    ('enlink-midstream', 'EnLink Midstream', OKE_Q, '미국 천연가스 집하·처리·물류 사업으로 ONEOK가 2025년 잔여 지분을 취득했습니다.', '현재 독립 상장 ENLC 기업 대신 ONEOK의 완전 소유 운영 자회사로 탐색합니다.'),
    ('cpc-taiwan', 'CPC Corporation, Taiwan', CPC_SPA, '대만 국영 석유·가스 기업으로 LNG 수입·공급과 정유·석유화학을 운영합니다.', 'Cheniere와의 장기 LNG 인도 계약은 대만 가스 수요로 이어지는 실제 판매 경로입니다.'),
    ('bechtel', 'Bechtel', STAGE3, 'Cheniere의 Corpus Christi 액화 설비 EPC 설계·조달·시공 상대입니다.', 'Stage 3의 마지막 트레인을 2026-08-28 인계했습니다. 계약 시공자와 가스 원료 공급자는 역할이 다릅니다.'),
]:
    PRIVATE[_key] = profile(_name, _origin, _business,
        '연결된 계약·운영 역할을 정리한 자료입니다. 상대 기업 전체의 매출 구성을 이 계약만으로 추정하지 않습니다.',
        [('에너지 공급망에서의 역할', _role)])

PRIVATE['jera']['relations'] = [
    relation('Cheniere Energy', 'LNG', 'supplier', '2029–2050 장기 LNG 구매 계약 · FOB·약 100만 톤/년', JERA_SPA),
    relation('Williams', 'WMB', 'supplier', 'South Mansfield 가스의 집하·LEG 운송을 제공하는 계약 구조', WOODSIDE)]
PRIVATE['jera']['products'].append(fact('미국 가스 생산지·운송 연결',
    'South Mansfield 자산 거래와 함께 Williams의 집하·Louisiana Energy Gateway 운송을 연결하는 계약 구조입니다.', WOODSIDE))
PRIVATE['whitewater']['products'].append(fact('Blackcomb·Traverse 경로',
    'Targa가 참여하는 별도 가스 배관 공동사업입니다. Eiger의 지분과 섞지 않습니다.', TRGP_Q))
PRIVATE['bechtel']['relations'] = [relation('Cheniere Energy', 'LNG', 'customer',
    'Corpus Christi Stage 3 액화 시설 EPC · 최종 설비 인계 2026-08-28', STAGE3)]
PRIVATE['whitewater']['relations'] = [
    relation('Targa Resources', 'TRGP', 'partner', 'Blackcomb·Traverse 공동사업 참여', TRGP),
    relation('ONEOK', 'OKE', 'partner', 'Eiger Express 공동 개발·건설·운영', OKE),
    relation('MPLX', 'MPLX', 'partner', 'WPC·Blackcomb와 Eiger의 공동사업 참여 · 프로젝트별 지분 구별', OKE),
    relation('Enbridge', 'ENB', 'partner', 'WPC·Eiger 가스 배관 공동사업 참여', OKE)]
PRIVATE['cpc-taiwan']['relations'] = [relation('Cheniere Energy', 'LNG', 'supplier', '2026년 추가 LNG 구매 계약 · 목적지 인도·2026–2050', CPC_SPA)]
PRIVATE['puget-sound-energy']['relations'] = [relation('Williams', 'WMB', 'supplier',
    'Northwest Pipeline 가스 운송 서비스 이용 · 고객 비중의 분모는 해당 자회사 매출', WMB)]
PRIVATE['blue-racer']['relations'] = [relation('Williams', 'WMB', 'partner',
    '집하·처리·NGL 물류 공동사업 · Williams 50% 지분법 투자', WMB)]
PRIVATE['howard-energy']['relations'] = [relation('Kinder Morgan', 'KMI', 'partner',
    'Dos Caminos 가스 배관 공동 소유·운영 · 각 50%', STX)]
PRIVATE['pemex']['relations'] = [relation('Kinder Morgan', 'KMI', 'partner',
    'NET Mexico 배관 · PEMEX 계열 MGI Enterprises 10%·KMI 인수 지분 90%', STX)]

for _key, _symbol, _origin in [
    ('momentum-midstream', 'WMB', MOMENTUM), ('transco', 'WMB', WMB),
    ('northwest-pipeline', 'WMB', WMB), ('monument-pipeline', 'KMI', KMI_Q),
    ('stakeholder-midstream', 'TRGP', TRGP_Q), ('dovetail-midstream', 'TRGP', TRGP_Q),
    ('enlink-midstream', 'OKE', OKE_Q),
]:
    PRIVATE[_key]['relations'] = [relation(PUBLIC[_symbol]['name'], _symbol, 'parent',
        '현재 운영·연결 회사 · 해당 자산의 역할·편입 기준일은 사업 구성에서 확인', _origin)]
