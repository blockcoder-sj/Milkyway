"""Edited producer, offshore development and produced-water reading notes.

Named selling routes and operating contracts are separate from acquisitions,
historical accounting periods and future drilling or delivery commitments.
"""
from .company_energy_sources import REPORTS, fact, report
from .company_energy_producers import NOG_UTICA
from .company_research_notes import profile, relation, source

SYMBOLS = ('INR', 'GFR', 'EGY', 'GPRK', 'GTE', 'KOS', 'TALO', 'WTI',
           'DEC', 'REPX', 'HPK', 'SD', 'PED', 'EPSN', 'TXO', 'WBI')
ANNUAL = {s:report(s) for s in SYMBOLS}
QUARTER = {s:report(s, 'quarter') for s in SYMBOLS}
GFR_AIF, GFR_MDA = report('GFR', 'aif'), report('GFR', 'quarter_mda')
INR_Q2 = source('Infinity · 2026 Q2 생산·Ohio 취득 후 사업',
    'https://ir.infinitynaturalresources.com/news/news-details/2026/Infinity-Natural-Resources-Announces-Second-Quarter-2026-Results/default.aspx', '2026-08-10')
EGY_Q2 = source('Vaalco · Baobab 재가동·현재 아프리카 사업',
    'https://www.vaalco.com/investors/news-events/press-releases/detail/452/vaalco-energy-inc-announces-second-quarter-2026-results', '2026-08-06')
EGY_BWE = source('BW Energy · Niosi·Guduma 실제 공동사업',
    'https://www.bwenergy.no/en/operations/gabon/niosi-and-guduma/', '열람 2026-10-03')
BORR_NORVE = source('Borr · Norve 고객·실제 계약 기간',
    'https://live.euronext.com/sites/default/files/company_press_releases/attachments_oslo/2026/02/18/666160_Borr_Drilling_Limited_Q4_2025_Fleet_Status_Report.pdf', '2026-02-18')
GPRK_Q2 = source('GeoPark · 2026 Q2 Colombia·Vaca Muerta',
    'https://ir.geo-park.com/news/news-details/2026/GeoPark-Reports-Second-Quarter-2026-Results/default.aspx', '2026-08-04')
GTE_SALE = source('Gran Tierra · 남미 매각 승인 절차·미완료',
    'https://www.grantierra.com/es/news/gran-tierra-energy-inc-announces-filing-of-definitive-proxy-statement-for-special-meeting-of-stockholders-to-consider-approval-of-sale-of-colombian-and-ecuadorian-businesses-2/', '2026-09-23')
GTE_Q2 = source('Gran Tierra · 2026 Q2·Ecopetrol 계약 조건',
    'https://www.grantierra.com/news/gran-tierra-energy-inc-reports-second-quarter-2026-results/', '2026-08-04')
KOS_Q2 = source('Kosmos · 실제 Tiberius 공동사업·EG 매각 완료',
    'https://investors.kosmosenergy.com/news-releases/news-release-details/kosmos-energy-announces-second-quarter-2026-results', '2026-08-03')
TALO_Q2 = source('Talos · 2026 Q2 개발·시추·Mexico 협력',
    'https://www.talosenergy.com/investor-relations/news/news-details/2026/Talos-Energy-Announces-Second-Quarter-2026-Operational-and-Financial-Results/default.aspx', '2026-08-04')
TALO_CLOSE = source('Talos · Shell 자산 인수 실제 완료',
    'https://www.sec.gov/Archives/edgar/data/1724965/000119312526398060/talo-20260922.htm', '2026-09-22')
SD_Q2 = source('SandRidge · 2026 Q2 개발·생산',
    'https://investors.sandridgeenergy.com/Investor-Relations/press-releases/press-release-details/2026/SandRidge-Energy-Inc--Announces-Financial-and-Operating-Results-for-the-Three-and-Six-Month-Periods-Ended-June-30-2026-and-Declares-Dividend-of-0-13-per-Share/default.aspx', '2026-08-05')
PED_Q2 = source('PEDEVCO · Juniper 통합 후 2026 Q2 사업',
    'https://www.pedevco.com/news-releases/news-release-details/pedevco-reports-second-quarter-2026-results', '2026-08-13')
DEC_RETIREMENT = source('Diversified · Next LVL 실제 유정 정리 사업',
    'https://www.div.energy/operations/next-lvl-energy-2/', '열람 2026-10-03')
WBI_Q2 = source('WaterBridge · Ranger 취득·2026 Q2 물 서비스',
    'https://www.h2obridge.com/news/news-details/2026/WaterBridge-Announces-Second-Quarter-2026-Results/default.aspx', '2026-08-05')

PUBLIC = {
    'INR': profile('Infinity Natural Resources', ANNUAL['INR'],
        'Ohio Utica와 Pennsylvania Marcellus에서 원유·가스·NGL을 생산하고 자체 집하·압축·물 인프라를 연결합니다. 2026년 Antero Ohio 취득 이후 자산은 2025년 실적 범위와 다릅니다.',
        '2025년 제품 계약 매출 350,375,000 USD는 원유 173,612,000·가스 127,448,000·NGL 49,315,000입니다. 외부 중류 수입 6,056,000을 더한 연결 매출은 356,431,000입니다.',
        [('Ohio · Utica', '원유·콘덴세이트와 액체가 풍부한 가스를 수평정으로 개발합니다. 판매 제품 조성에 따라 가스 처리·NGL 회수·원유 반출 비용이 달라집니다.'),
         ('Pennsylvania · Marcellus', '천연가스 중심 광구입니다. Utica 원유 매출 비중과 Marcellus 생산·지역 가스 가격을 같은 지표로 취급하지 않습니다.'),
         ('Antero Ohio · 취득 완료', '2026-02-23 상류·집하·물 자산 취득 후 Infinity 60%·NOG 40%입니다. Infinity가 운영하며 취득 전 Antero 실적을 2025년 자체 실적에 합산하지 않습니다.'),
         ('집하·압축·물', '취득 자산에는 가스 배관 약 141 mile와 물 인프라 약 90 mile가 있습니다. 600 MMcf/d 설계 용량은 실제 가스 판매량과 다릅니다.'),
         ('상품 인도·정산', '원유·가스·NGL을 계약 인도점에 공급합니다. 구매자별 매출 비율과 기말 매출채권 비율은 분모가 다릅니다.'),
         ('내부·외부 중류 서비스', '자체 생산의 처리와 외부 고객 수수료를 구분합니다. 내부 서비스는 외부 제품 판매에 추가되는 별도 매출이 아닙니다.')],
        customers='2025년 Marathon Oil 33%·BP America 35%·Ergon 16%가 제품 매출 주요 구매자입니다. 같은 회사의 매출채권 24/53/18%를 매출 구성으로 사용하지 않습니다.',
        inputs='시추·완결·강관·모래·물·전력·집하·압축·가스 처리와 원유 운송이 필요합니다. Ohio 취득 후 자체 시설과 외부 수수료 부담의 범위를 구분합니다.',
        competition='Utica·Marcellus 광구, 시추·완결 인력과 지역 가스 처리·반출 용량에서 경쟁합니다. 제품 매출 비율은 업계 시장점유율이 아닙니다.'),
    'GFR': profile('Greenfire Resources', GFR_AIF,
        'Alberta Hangingstone의 SAGD 오일샌드와 2026년 취득한 Great Divide에서 역청을 생산합니다. 증기로 역청을 회수하고 희석제를 혼합해 배관으로 판매하는 사업입니다.',
        '2025년 희석 역청 574,313,000 CAD·비희석 역청 28,990,000의 판매 합계 603,303,000에서 로열티 18,908,000을 차감한 연결 매출은 584,395,000입니다. CAD와 USD를 섞지 않습니다.',
        [('Hangingstone Expansion', 'Greenfire 운영 75%·CNOOC 25% 공동사업입니다. 2025년 gross 14,320 bpd와 Greenfire 귀속 10,740 bpd를 구분합니다.'),
         ('Hangingstone Demo', 'Greenfire가 100% 보유·운영합니다. 2025년 5,429 bpd 생산과 Expansion의 전체 공동사업 물량을 같은 지분 기준으로 합산하지 않습니다.'),
         ('SAGD · 증기 회수', '천연가스로 증기를 만들어 지층 역청을 가열합니다. 증기 투입·회수 비율, 가스·전력 사용과 유정·시설 운전 상태가 비용 구조에 연결됩니다.'),
         ('희석·판매 경로', '콘덴세이트를 섞어 운송 가능한 dilbit를 만듭니다. 희석제 가격·혼합량, WCS 가격 차액, 운송·판매 수수료와 로열티가 각각 다른 항목입니다.'),
         ('배관·에너지 투입', 'NGTL로 가스를 공급받고 Enbridge 계통으로 희석 역청을 반출합니다. Polaris 희석제 배관은 반출 원유 배관과 역할이 다릅니다.'),
         ('자산·중단 상태', 'McKay 시설은 2023년 3월부터 중단 상태입니다. 확인매장량, 잠재 시설 용량과 실제 가동 생산량을 구분합니다.')],
        customers='Trafigura Canada는 Expansion의 희석 역청 구매·콘덴세이트 공급 계약 상대이며 계약은 2028-10-01까지입니다. Demo의 일부 판매·수수료 계약 종료를 Expansion 전체 계약 종료로 표시하지 않습니다.',
        inputs='증기용 천연가스·전력·물·희석제와 배관이 필요합니다. CNOOC는 광구 공동사업 상대, Trafigura는 판매·희석제, NGTL·Enbridge는 에너지·반출 경로의 서로 다른 역할입니다.',
        competition='Alberta 오일샌드의 원유 판매·희석제·배관 용량·인력에서 경쟁합니다. SAGD와 노천 채굴의 공정·비용을 구분하고 자산 귀속 생산량을 업계 점유율로 표시하지 않습니다.'),
    'EGY': profile('Vaalco Energy', ANNUAL['EGY'],
        'Gabon Etame, Egypt 생산분배 사업과 Côte d’Ivoire Baobab을 중심으로 원유를 생산합니다. Canada는 2026-02-19 전면 매각했고 Equatorial Guinea Venus는 개발 단계입니다.',
        '2025년 연결 매출 359,272,000 USD는 Gabon 181,738,000·Egypt 139,963,000·Canada 19,174,000·Côte d’Ivoire 18,397,000입니다. 이집트 PSC의 총판매·정부 몫과 연결 지역 수입을 구분합니다.',
        [('Gabon · Etame', 'Etame Marin 운영 광구입니다. 2025년 WI 58.8%는 정부 carried interest 변경으로 2026-06-20부터 57.2%가 되며 연간 과거 비율과 다릅니다.'),
         ('Egypt · 두 PSC', 'Eastern Desert Merged Concession·Western Desert South Ghazalat을 EGPC와 운영합니다. 공동사업 지분과 비용 회수·이익 원유·정부 몫을 구분합니다.'),
         ('Côte d’Ivoire · Baobab', 'CI-40 비운영 WI 27.4%·paying interest 30.4%입니다. FPSO 정비로 2025년 대부분 중단됐으며 2026년 재가동은 별도 현재 자료입니다.'),
         ('Kossipo·CI-705', 'Kossipo는 2026년 2월 운영 WI 60%, CI-705는 운영 WI 70%입니다. 개발·탐사 광구를 이미 생산하는 Baobab과 같은 상태로 표시하지 않습니다.'),
         ('Niosi·Guduma', 'BW Energy가 운영하고 Vaalco 37.5%·BW Energy 37.5%·Panoro 25%가 참여하는 Gabon 탐사 공동사업입니다. 탐사 면적은 확인매장량·현재 생산량이 아닙니다.'),
         ('Canada·Venus · 서로 다른 상태', 'Canada는 실제 매각 후 현재 운영에서 제외합니다. Equatorial Guinea Block P Venus의 운영 WI 60%는 미개발 자산이며 개발 결정·첫 생산과 구분합니다.')],
        customers='2025년 Gabon·Egypt·Côte d’Ivoire 각각의 주요 원유 구매자는 공시에서 익명입니다. EGPC PSC·수취채권과 헤지 계약을 익명 원유 구매자의 이름으로 바꾸지 않습니다.',
        inputs='해상 시추·유정 정비·FPSO/FSO·해저 연결·운송 및 Egypt 육상 운영이 필요합니다. 정비 기간의 생산 중단, lifting 일정과 재고는 실제 판매 수입에 다른 방식으로 반영됩니다.',
        competition='아프리카 육상·해상 광구, 리그·시설·운송·인력과 원유 판매에서 경쟁합니다. WI·NRI·paying interest 및 연결 판매의 분모를 구분합니다.'),
    'GPRK': profile('GeoPark', ANNUAL['GPRK'],
        'Colombia Llanos 원유 생산과 Argentina Vaca Muerta 개발을 운영합니다. 2025년 말 Brazil Manati와 Ecuador 사업 처분 후 현재 포트폴리오는 과거 국가별 매출 구성과 다릅니다.',
        '2025년 IFRS 매출 492,518,000 USD는 Colombia 461,418,000·Argentina 5,783,000·Brazil 6,435,000·Ecuador 18,463,000·본사 기타 419,000입니다. 처분 사업의 과거 매출을 현재 생산 자산으로 표시하지 않습니다.',
        [('Colombia · Llanos 34', 'Parex와 함께 개발한 원유 생산 기반입니다. 생산·유정 개발·운송과 판매 선급금 상환을 별도 항목으로 파악합니다.'),
         ('Llanos 공동 광구', 'Hocol/Ecopetrol과의 Llanos 87·123 등 공동사업입니다. 상대의 지분 보유와 실제 광구 운영·물량의 역할을 구분합니다.'),
         ('Argentina · Vaca Muerta', 'Neuquén의 비전통 원유 사업입니다. Puesto Silva Oeste의 GeoPark 경제 지분 95%·GyP 5%와 recoverable carry 조건을 구분합니다.'),
         ('Vitol · 물량·금융 연계', '2026년 갱신 계약은 2028-12-31까지입니다. Llanos 34와 CPO-5·Llanos 123의 인도 물량, 선급금 차입·원유 상환은 다른 개념입니다.'),
         ('처분 자산 · Brazil·Ecuador', 'Manati·Ecuador 사업은 2025년 12월 처분됐습니다. 연간 지역 수입에는 처분 전 물량이 포함되지만 현재 운영 지역과 구분합니다.'),
         ('생산·개발·탐사', '개발 유정, 탐사 성공, 배관 연결과 commercial production을 구분합니다. 시추 계약·투자 예산은 이미 판매한 원유량이 아닙니다.')],
        customers='Vitol Colombia는 원유 인도·선급금 계약 상대입니다. 330,000,000 USD committed funding와 추가 170,000,000 옵션은 실제 미상환 차입이나 연간 매출이 아닙니다.',
        inputs='육상 시추·완결·물·원유 처리·저장·배관/트럭과 Colombia·Argentina의 토지·허가가 필요합니다. 회수 가능한 partner carry와 자체 운영 지출을 구분합니다.',
        competition='Colombia 광구·운송과 Vaca Muerta 자원·서비스에서 경쟁합니다. Parex의 공동사업 관계와 기업 취득 제안은 서로 다른 관계입니다.'),
    'GTE': profile('Gran Tierra Energy', ANNUAL['GTE'],
        'Canada·Colombia·Ecuador에서 원유·가스·NGL을 생산합니다. 남미 사업 매각 계약은 2026년 9월 자료 기준 승인 절차 중이며 매각 후 Canada 중심 구상은 아직 완료 사업과 다릅니다.',
        '2025년 고객 계약 매출 596,713,000 USD는 원유 555,430,000·가스 31,790,000·NGL 9,493,000입니다. 국가 구성은 Colombia 418,411,000·Ecuador 62,609,000·Canada 115,693,000이며 두 보기는 합산하지 않습니다.',
        [('Colombia · 기존 생산', 'Acordionero·Costayaco와 Suroriente 등을 생산합니다. field 전체와 working interest·로열티 후 NAR 물량을 구분합니다.'),
         ('Ecopetrol · 공동 개발', 'Suroriente의 투자 carry와 Tisquirama earn-in은 다른 계약입니다. earn-in 조건 충족과 이후 귀속 지분·상환 의무를 따로 확인합니다.'),
         ('Ecuador · Oriente', 'Charapa·Chanangue·Iguana·Perico·Espejo의 profit-sharing 계약으로 운영합니다. 정부와 나누는 물량을 일반 로열티·cost oil 방식과 혼동하지 않습니다.'),
         ('Canada · 편입·처분', 'i3 취득 후 가스·NGL 기반이 추가됐습니다. 2026년 Simonette·Lodgepole 처분을 반영한 현재 광구는 2025년 국가 수입과 다릅니다.'),
         ('판매·선급금', '원유 판매와 prepayment 금융·원유 인도 상환을 구분합니다. 계약 인도 물량이 전체 생산량·확인매장량을 의미하지 않습니다.'),
         ('Azerbaijan · 조건부 사업', '탐사·개발·생산분배 계약은 비준 조건이 남아 있습니다. Canada 기존 생산과 같은 현재 생산 매출로 표시하지 않습니다.')],
        customers='원유·가스 구매자 및 정부 profit-sharing 경로로 판매합니다. 실제 사업 매각 상대 Maurel & Prom을 기존 원유·가스 구매자로 표시하지 않습니다.',
        inputs='육상 시추·완결·물·가스 처리·전력·원유 저장·운송과 공동 광구 운영이 필요합니다. 국가별 유정·서비스·허가 및 원유 운송 방식은 다릅니다.',
        competition='Colombia·Ecuador·Canada의 광구·유정 서비스·반출과 상품 판매에서 경쟁합니다. 거래 완료 전 자산과 승인 조건을 명시합니다.'),
    'KOS': profile('Kosmos Energy', ANNUAL['KOS'],
        'Ghana 해상 원유, Mauritania·Senegal GTA 가스·LNG와 미국 Gulf 심해 원유를 생산합니다. Equatorial Guinea Ceiba·Okume는 2026년 6월 매각 완료한 과거 사업입니다.',
        '2025년 지역 계약 판매 합계는 1,297,846,000 USD이고 파생상품 포함 매출은 1,288,352,000입니다. 같은 지역이라도 계약 매출과 파생상품 포함 수입을 합산하지 않습니다.',
        [('Ghana · Jubilee·TEN', 'Jubilee WI 38.6%·TEN 20.4% 비운영 지분을 보유합니다. Tullow 운영·GNPC 참여 및 gross field 물량과 Kosmos 귀속 물량을 구분합니다.'),
         ('GTA · 가스→LNG', '해저 생산·FPSO 처리·배관·Gimi FLNG로 연결합니다. 전체 시설 설계 2.7 mtpa와 Kosmos 귀속 생산·계약 인도량은 다른 분모입니다.'),
         ('BP Gas Marketing · LNG 구매', 'Phase 1 SPA 초기 기간은 2033년 말까지이며 판매자 10년 연장 옵션이 있습니다. 최소 인도 조건·부족분 지급과 실제 인도는 구분합니다.'),
         ('Gulf · 기존 생산', 'Odd Job·Kodiak·Winterfell 등 심해 원유·가스를 생산합니다. 비운영 유정·시설 운영사와 Kosmos가 직접 운영하는 개발의 역할을 분리합니다.'),
         ('Tiberius · 개발 공동사업', '개발 결정·farm-down 완료와 실제 첫 생산은 다릅니다. Occidental host 연결 및 신규 Navitas 참여는 현재 개발 계약 구조입니다.'),
         ('Norphlet · Shell 협력', '다수 탐사 블록의 공동 이해관계와 Appomattox 연결 가능성을 개발합니다. Trailblazer의 미래 시추·잠재 자원을 확인된 현재 생산으로 표시하지 않습니다.')],
        customers='GTA LNG는 BP Gas Marketing에 판매합니다. 원유 판매·국내 가스 조건 협상과 LNG SPA는 서로 다른 구매 경로입니다.',
        inputs='리그·해저 장비·FPSO·FLNG·운영/정비·배관과 Ghana·GTA·Gulf 공동사업이 필요합니다. 지분·시설 임대·유정 개발·인도 약정의 책임을 구분합니다.',
        competition='해상 탐사 광구·리그·연결 시설과 원유·LNG 판매에서 경쟁합니다. GTA 전체 mtpa·cargos와 Kosmos 회사 매출 비중은 같은 수치가 아닙니다.'),
    'TALO': profile('Talos Energy', ANNUAL['TALO'],
        '미국 Gulf의 심해·대륙붕 원유·가스를 생산하고 Mexico·Honduras 해상 개발·탐사를 진행합니다. 2026년 Shell 자산 인수 완료와 향후 개발·시추 약정을 분리합니다.',
        '2025년 매출 1,780,070,000 USD는 원유·콘덴세이트 1,560,401,000·가스 169,445,000·NGL 50,224,000입니다. 신규 인수 자산의 2026년 전체 실적을 과거 연간 매출에 추가하지 않습니다.',
        [('기존 Gulf 생산', '유정·플랫폼·해저 배관과 육상 인도점으로 연결합니다. 운영/비운영 지분과 회사 귀속 물량을 전체 광구 생산량과 구분합니다.'),
         ('Coulomb·Na Kika', 'Shell에서 실제 취득한 생산 자산입니다. Coulomb 운영 WI 50%와 BP가 운영하는 Na Kika 플랫폼·Kepler/Ariel/Fourier/Herschel 비운영 WI 25%를 구분합니다.'),
         ('Monument · Shenandoah 연결', 'Beacon 운영 41.7%·Talos 29.7%·Navitas 28.6% 개발입니다. 2026년 말 첫 생산 목표와 연결 용량 20,000 bbl/d를 현재 인도량으로 표시하지 않습니다.'),
         ('West Vela · 시추', 'Seadrill drillship으로 탐사·평가를 수행합니다. 2027년 중반 시작 1년 신규 계약은 현재 시추와 다른 기간의 약정입니다.'),
         ('Mexico · Block 29', 'Repsol과의 farm-in 개발 협력입니다. 지분 취득 계약·개발 판단·첫 생산은 서로 다른 단계입니다.'),
         ('Honduras · 탐사', 'CaribX 광구 운영 45% 취득과 추가 35% 승인 대기 조건을 구분합니다. 목표 80%를 모두 완료된 지분으로 표시하지 않습니다.')],
        customers='2025년 Shell Trading 35%·ExxonMobil 23%·Chevron 12%가 상품 구매자입니다. Shell Offshore의 자산 매각과 Shell Trading의 원유 구매는 다른 법인·역할입니다.',
        inputs='심해 리그·해저 장비·플랫폼·tieback·정비·배관과 해체/복구가 필요합니다. 생산시설 지분 취득과 별도 시추·운영 서비스 계약은 구분합니다.',
        competition='Gulf·Mexico 해상 광구, 리그·연결 설비·인력과 원유 판매 경로에서 경쟁합니다. 신발견·개발 자원의 목표와 가동 실적을 구분합니다.'),
    'WTI': profile('W&T Offshore', ANNUAL['WTI'],
        '미국 Gulf의 대륙붕·심해 원유·가스·NGL을 생산합니다. 직접 운영 자산과 Monza 공동사업의 지분비례 연결 및 해체 책임이 사업 구조를 이룹니다.',
        '2025년 고객 계약 매출 501,462,000 USD는 원유·콘덴세이트 327,845,000·가스 143,948,000·NGL 20,371,000·기타 판매 9,298,000입니다.',
        [('대륙붕·주 관할', '얕은 해상 생산 플랫폼·유정과 기존 반출 인프라를 운영합니다. offshore 시설 유지와 유정 plugging·decommissioning 부담이 연결됩니다.'),
         ('심해 생산', '별도 유정·플랫폼 및 처리·해저 연결을 이용합니다. 대륙붕 유정의 운영 조건·비용과 동일하게 취급하지 않습니다.'),
         ('원유·콘덴세이트', 'BP Products North America와 Shell Trading 등을 통해 판매합니다. 인도 지점·품질·운송 차액이 실현 판매 가격에 반영됩니다.'),
         ('천연가스·NGL', '가스 처리와 판매·집하를 통해 액체 성분을 분리합니다. 가스량과 NGL 배럴을 원유 환산으로 표시해도 같은 매출 가치는 아닙니다.'),
         ('Monza · 공동 개발', '회사·외부 투자자·CEO 관련 투자자가 자금을 댄 공동사업입니다. 지분비례 연결하며 Monza 전체 현금·매출을 다시 연결 합계에 더하지 않습니다.'),
         ('해체·보증', '판매한 과거 해상 자산에도 복구 책임이 남을 수 있습니다. surety·법적 정산 상대와 시추·제품 판매 상대의 역할은 다릅니다.')],
        customers='2025년 BP Products North America 33%·Shell Trading US 17%가 제품 판매 구매자입니다. 개별 고객 비율은 업계 원유 시장점유율이 아닙니다.',
        inputs='해상 리그·유정 정비·플랫폼·배관·원유 반출·가스 처리와 해체 서비스가 필요합니다. 보증 비용·법률 지급과 가동 시설 유지 지출을 구분합니다.',
        competition='Gulf 생산 광구·해상 서비스·반출 용량과 상품 구매자에서 경쟁합니다. 비운영 광구와 직접 운영·Monza 귀속 물량을 구분합니다.'),
    'DEC': profile('Diversified Energy', ANNUAL['DEC'],
        'Appalachia와 Central 미국의 기존 원유·가스·NGL 생산 자산을 인수·운영하며 집하·운송과 유정 폐쇄 서비스를 연결합니다. 장수명 자산 운영과 개발·정리 의무를 함께 관리합니다.',
        '2025년 상품 매출 1,538,821,000 USD는 가스 830,247,000·NGL 207,868,000·원유 500,706,000입니다. 집하 40,492,000·기타 32,142,000과 파생상품 포함 매출 1,829,142,000의 범위를 구분합니다.',
        [('Appalachia · 기존 유정', '기존 천연가스 유정·압축·집하 시설을 유지합니다. 생산 유지·정비와 신규 시추를 같은 비용으로 취급하지 않습니다.'),
         ('Central · 복합 제품', 'Texas·Oklahoma 등의 가스·원유·NGL을 생산합니다. 상품 조성과 처리·반출 비용은 Appalachia 건성 가스와 다릅니다.'),
         ('인수·편입 사업', '2025년 Maverick·Summit·Canvas 편입과 2026년 Sheridan·Camino 취득의 기간을 구분합니다. 인수 전 실적을 연결 매출에 소급 추가하지 않습니다.'),
         ('집하·운송', '외부 집하·운송 수수료와 자체 생산 물량을 연결합니다. 같은 원료의 상품 판매·내부 처리·헤지를 세 번 매출로 계산하지 않습니다.'),
         ('Next LVL · 유정 정리', '유정 폐쇄·복구 서비스를 운영합니다. 자체 의무 이행과 외부 서비스 수입 및 장기 자산퇴역 부채는 서로 다른 항목입니다.'),
         ('Camino · 구조화 공동사업', '생산 자산의 Carlyle 공동 SPV와 100% 취득한 미개발 광구를 구분합니다. 공동사업 지분·ABS 부채·광구 면적은 다른 범위입니다.')],
        customers='여러 상품 구매자에게 판매하며 2025년 개별 10% 초과 고객은 없습니다. 인수 상대·금융 공동사업을 기존 가스 구매자로 바꾸지 않습니다.',
        inputs='기존 유정 정비·압축·가스 처리·집하·배관과 폐쇄/복구 인력이 필요합니다. 인수 자산의 가동 서비스·부채·폐쇄 의무를 함께 확인합니다.',
        competition='기존 자산 인수·운영, 지역 집하·운송 및 유정 정리 서비스에서 경쟁합니다. 헤지 평가손익은 실제 추가 상품 판매량이 아닙니다.'),
    'REPX': profile('Riley Exploration Permian', ANNUAL['REPX'],
        'Texas Champions와 New Mexico의 Permian 원유·가스·NGL을 생산하고 발전 공동사업을 연결합니다. 중류 자산 매각 이후 외부 가스 처리 계약과 미래 시설 가동을 구분합니다.',
        '2025년 원유 순판매 398,341,000 USD·가스 -3,322,000·NGL -3,039,000의 합계는 391,980,000입니다. 가스·NGL 처리·운송비가 해당 판매액보다 커 음수이며 비율을 표시하지 않습니다.',
        [('Champions · Texas', 'Permian 원유 중심 유정입니다. 기존 Stakeholder, 현재 Targa의 원유 반출·가스 처리와 자체 생산 조건을 연결합니다.'),
         ('New Mexico · 생산', '원유·동반 가스를 생산합니다. Dovetail 매각과 새 Targa gas purchase agreement의 in-service 이후 약정은 현재 기존 인도 경로와 다릅니다.'),
         ('가스·NGL 순판매', '2025년 가스 총판매 7,272,000에서 GP&T 10,594,000, NGL 총판매 44,159,000에서 GP&T 47,198,000을 차감합니다. 음수를 0으로 버리지 않습니다.'),
         ('RPC Power · 발전', 'Conduit Power와 50/50 공동사업으로 가스를 활용한 현장 발전을 연결합니다. 자체 유정 전력·외부 판매와 가스 제품 판매를 구분합니다.'),
         ('Dovetail·압축 자산 매각', '2025년 12월 Targa에 중류·압축 자산을 실제 매각했습니다. 조건부 추가 대금은 아직 받은 판매대금·현재 시설 소유가 아닙니다.'),
         ('Targa · 장기 처리·구매', 'New Mexico 새 계약은 가동 개시부터 15년·광구 전용/최소 물량 조건입니다. 2026년 말 전 가동 예상과 실제 서비스 개시는 구분합니다.')],
        customers='2025년 주요 구매자 60%·30%는 익명입니다. Targa의 이름이 확인된 처리·향후 구매 계약을 익명 원유 구매자 이름이나 같은 비율로 사용하지 않습니다.',
        inputs='강관·모래·물·시추/완결·전력과 Targa 집하·처리·운송이 필요합니다. RPC 발전 연료와 일반 제품 가스 판매의 귀속·정산을 구분합니다.',
        competition='Permian 광구·유정 서비스·처리·배관·전력에서 경쟁합니다. 원유 매출이 순매출 합계보다 큰 것은 음수 가스·NGL 조정 때문이며 제품 시장점유율이 아닙니다.'),
    'HPK': profile('HighPeak Energy', ANNUAL['HPK'],
        'Texas Midland Basin의 Flat Top·Signal Peak에서 원유·동반 가스·NGL을 생산합니다. 원유 비중이 큰 생산과 장기 Delek 판매·반출 약정이 핵심 구조입니다.',
        '2025년 고객 계약 매출 863,359,000 USD는 원유 785,977,000·천연가스/NGL 77,382,000입니다. 공시가 합산한 가스·NGL을 임의로 각각의 매출로 나누지 않습니다.',
        [('Flat Top', 'Howard·Borden 지역의 연속 광구와 수평정 원유·가스 생산 기반입니다. 유정 위치와 지층·완결·공용 생산시설을 연결합니다.'),
         ('Signal Peak', '별도 생산 권역입니다. 원유 일부는 트럭으로 반출하며 대부분 배관으로 운송하는 Flat Top과 경로·비용 조건이 다릅니다.'),
         ('Delek · 원유 계약', '12년 원유 계약의 지수 가격·최소 물량 조건입니다. 2024-05 시작 첫 10년 gross 23,500 bopd 약정과 실제 인도량은 다릅니다.'),
         ('Energy Transfer · 판매', '나머지 주요 원유 판매 경로입니다. Delek과 달리 해당 계약에는 같은 최소 물량 약정이 없으며 과거 2024년 18%를 2025년 비율로 유지하지 않습니다.'),
         ('물·생산 시설', '염수 처분정·물 배관·저장·분리·계량과 인공 채유를 이용합니다. 물 재사용·자체 처리와 외부 장비 구매를 구분합니다.'),
         ('가스·NGL 처리', '외부 가스 처리자가 액체를 추출합니다. 제품 합산 수입·처리 대가와 원유 파이프라인 판매 조건은 다릅니다.')],
        customers='2025년 Delek(DK Trading & Supply) 82%·Energy Transfer Crude Marketing 약 8%가 제품 매출 구매자입니다. 해당 고객 비율과 최소 gross 배럴 약정은 같은 지표가 아닙니다.',
        inputs='시추·완결·모래·강관·물·전력·인공 채유와 가스 처리·원유 집하가 필요합니다. 확인된 구매자와 이름이 공개되지 않은 가스 처리자를 구분합니다.',
        competition='Midland 광구·시추/완결 서비스·원유 반출과 물 처리에서 경쟁합니다. 경영진의 과거 근무 회사를 현재 공급사·협력사로 연결하지 않습니다.'),
    'SD': profile('SandRidge Energy', ANNUAL['SD'],
        'Oklahoma·Kansas Mid-Continent의 원유·가스·NGL 생산과 NW STACK 개발을 운영합니다. 기존 유정 생산 유지와 신규 원유 유정·비운영 참여를 구분합니다.',
        '2025년 고객 계약 매출 156,357,000 USD는 원유 77,270,000·가스 41,587,000·NGL 37,500,000입니다. 고객별 제품 구매와 원유·가스·NGL 구성은 서로 다른 보기입니다.',
        [('Mid-Continent · 기존 자산', 'Oklahoma·Kansas의 기존 원유·가스 유정을 운영합니다. 생산 감소·유정 정비와 신규 유정 판매 물량을 구분합니다.'),
         ('NW STACK · 개발', 'Oklahoma의 Woodford·Meramec 등 신규 개발을 추진합니다. 계획 유정과 실제 생산을 개시한 유정을 분리합니다.'),
         ('원유 판매', 'Plains·Valero 등 구매자에게 공급합니다. 수취 가격의 지수·품질·운송 조정과 구매자 집중도를 구분합니다.'),
         ('가스·NGL', 'Targa 경로로 가스·액체 제품을 판매합니다. 가스 처리·분리·운송 비용과 원유 생산 매출은 별도입니다.'),
         ('운영·비운영 지분', '직접 운영 유정과 외부 운영자의 투자·완결 일정에 참여하는 지분을 구분합니다. 전체 광구 생산과 SandRidge 귀속분을 별도 표시합니다.'),
         ('매장량·시설·개발 지출', '확인매장량과 생산·설비 능력·개발 지출은 서로 다른 기간·측정 기준입니다. 단일 보고 부문 소계를 제품에 다시 더하지 않습니다.')],
        customers='2025년 Targa Pipeline Mid-Continent West OK 50,896,000 USD·Plains 33,551,000·Valero 21,600,000이 주요 구매자입니다. 회사 제품 매출 기준 집중도이며 업계 점유율이 아닙니다.',
        inputs='시추·완결·전력·물·압축·가스 처리·원유 반출과 기존 유정 정비가 필요합니다. 구매자 계약과 장비 제조사의 추정 계약을 구분합니다.',
        competition='Mid-Continent 자산·시추/완결 자원·가스 처리·배관과 원유 구매자에서 경쟁합니다. 생산량·매장량·매출의 각각 다른 분모를 유지합니다.'),
    'PED': profile('PEDEVCO', ANNUAL['PED'],
        'D-J Basin·Powder River Basin·Permian의 원유·가스·NGL을 생산합니다. 2025-10-31 North Peak·Century 취득 후 직접 운영과 비운영 유정 참여를 함께 운영합니다.',
        '2025년 매출 45,751,000 USD는 원유 40,230,000·가스 2,663,000·NGL 2,858,000입니다. 취득 사업은 10월 말 이후 실적만 연간 연결되므로 2026년 통합 사업 전체와 다릅니다.',
        [('D-J Basin', 'Colorado·Wyoming의 수평정 생산과 비운영 참여입니다. 운영자가 유정 투자·완결·판매를 관리하는 비운영 사업과 자체 운영을 구분합니다.'),
         ('Powder River Basin', 'Wyoming 광구의 원유·가스 생산입니다. 연방 광구 임대·허가와 유정 개발·반출 조건이 연결됩니다.'),
         ('Permian', 'New Mexico 원유·가스 자산입니다. 각 basin의 제품 조성·운영 지분·판매 경로는 다릅니다.'),
         ('North Peak·Century · 실제 편입', '2025-10-31 합병으로 취득한 운영 사업입니다. 취득 자산·주식·부채와 이후 생산 실적의 범위를 구분합니다.'),
         ('비운영 · 대행 판매', '외부 운영자가 상품을 팔고 회사 귀속 현금을 배분합니다. 운영자와 최종 상품 구매자는 다른 상대일 수 있습니다.'),
         ('가격·운송 조정', '원유는 지수·품질·운송 조건으로, 가스·NGL은 처리·판매 조건으로 정산합니다. 공시의 nearby operator 목록을 모두 JV·공급 계약으로 해석하지 않습니다.')],
        customers='2025년 구매자 두 곳 26%·22%, 비운영자 한 곳 약 30%는 익명입니다. 구매자 집중도와 대행 운영자의 물량 비율을 섞거나 이름을 추정하지 않습니다.',
        inputs='시추·완결·물·강관·모래·전력·가스 처리·배관/트럭 및 비운영자 서비스가 필요합니다. 지역 주변 기업 목록은 직접 계약의 근거가 아닙니다.',
        competition='D-J·PRB·Permian 광구·유정 서비스·반출에서 경쟁합니다. 회사 통합 후 사업과 2025년 제한된 취득 후 연결 기간을 구분합니다.'),
    'EPSN': profile('Epsilon Energy', ANNUAL['EPSN'],
        'Pennsylvania 가스·Auburn 집하 사업과 Wyoming·기타 원유/가스 자산을 운영합니다. 직접/비운영 생산과 지분 소유 집하망의 외부 수수료를 구분합니다.',
        '2025년 연결 고객 매출 51,587,556 USD는 원유/콘덴세이트 13,803,515·가스 29,121,446·NGL 1,978,860·외부 집하 6,683,735입니다. 집하 부문 내부 수입 1,864,769는 제거합니다.',
        [('Pennsylvania · Marcellus', 'Susquehanna 가스를 Auburn 집하·압축 후 Shoemaker Dehy의 Tennessee Gas Pipeline Zone 4 인도점에 판매합니다. 자체 firm interstate 운송권은 없습니다.'),
         ('Auburn · 공동 집하', 'Epsilon Midstream 35%·Appalachia Midstream Services 43.875%·Equinor Pipelines 21.125%입니다. Williams 계열 운영사의 역할과 회사 귀속 수수료를 구분합니다.'),
         ('압축·cross-flow', '직접 anchor 가스와 인접 망 cross-flow 가스의 수수료가 다릅니다. 2025년 말 낮은 흡입압 기준 시설 용량 약 127 MMcf/d를 원래 330 MMcf/d와 구분합니다.'),
         ('ARM · 판매 대행', 'Pennsylvania 가스의 nomination·인보이스·정산을 대행합니다. ARM은 최종 가스 구매자 34곳과 다른 서비스 상대입니다.'),
         ('Wyoming · 원유/가스', 'HF Sinclair·WGR Operating 경로로 판매합니다. 지역 매출의 68.4/27.3%는 전체 회사 매출의 같은 비율이 아닙니다.'),
         ('귀속·연결 범위', '상품 판매·외부 집하와 부문 내부 집하를 분리합니다. gross 집하 부문 8,548,504를 전체 연결 매출에 다시 더하지 않습니다.')],
        customers='SWN Energy Services는 2025년 전체 매출 10% 초과 가스 구매자입니다. Expand·Equinor는 Auburn anchor shipper이고 Wyoming 구매자 비율의 분모는 해당 지역입니다.',
        inputs='Williams 계열 집하 운영·압축/탈수·Tennessee 배관 인도와 ARM 판매 대행이 필요합니다. 자체 firm 수송권이 없다는 조건과 물리적 연결 경로를 구분합니다.',
        competition='Appalachian 가스 구매·지역 배관 용량, Wyoming 자산·생산 서비스와 집하 물량에서 경쟁합니다. 설계 압력에 따라 변하는 시설 용량과 실제 처리량은 다릅니다.'),
    'TXO': profile('TXO Partners', ANNUAL['TXO'],
        '미국 기존 원유·가스·NGL 자산을 운영하는 partnership입니다. Cross Timbers 공동사업은 2026년 자산 처분 후 정리 중이며 과거 지분비례 연결 실적과 현재 포트폴리오를 구분합니다.',
        '2025년 고객 계약 판매 363,147,000 USD는 원유/콘덴세이트 257,024,000·가스 74,021,000·NGL 32,102,000입니다. 파생상품 포함 매출 401,012,000과 분모가 다릅니다.',
        [('기존 자산 · Permian·San Juan', '기존 생산 유정과 광물/운영 권리를 관리합니다. 생산 유지·정비와 취득·처분 후 운영 범위를 따로 확인합니다.'),
         ('Williston · 편입 사업', '2025년 취득 후 원유·가스 자산이 추가됐습니다. 취득 전 사업과 편입 후 연결 기간, 상품 매출 조성을 구분합니다.'),
         ('Cross Timbers · 과거 공동사업', 'TXO 50%·XTO 측 50%, TXO 관리·공동위원회 만장일치 구조입니다. 지분비례 연결은 완전 지배 자회사와 다릅니다.'),
         ('2026 · 처분·정리', '세 건의 자산 거래는 4월·5월에 실제 완료했습니다. 2025년 Cross Timbers 매출과 현재 보유·생산 자산을 분리합니다.'),
         ('판매 계약', 'Chevron USA·Gunvor USA·Plains를 포함한 구매자에게 판매합니다. 대부분 12개월 미만 계약으로 고객 집중도와 가격·운송 조건을 구분합니다.'),
         ('partnership · 배분', '현금 배분·관리 수수료와 생산 제품 수입을 구분합니다. JV 전체 현금·매출을 회사 귀속 수치에 한 번 더 더하지 않습니다.')],
        customers='2025년 Chevron USA·Gunvor USA·Plains 세 곳이 상품 판매의 42% 초과입니다. 공동사업 XTO와 자산 인수자 CTOC를 상품 구매자로 표시하지 않습니다.',
        inputs='유정 정비·물·압축·가스 처리·원유 운송과 광구 복구가 필요합니다. 공동사업 관리·인수/처분 비용과 생산 운영비를 구분합니다.',
        competition='기존 자산 취득·생산 유지·광구 서비스·제품 판매에서 경쟁합니다. 공동사업 전체·지분 귀속·처분 이후 수치를 같은 범위로 합산하지 않습니다.'),
    'WBI': profile('WaterBridge', ANNUAL['WBI'],
        'Delaware Basin의 생산수를 집하·운송·처분·재사용하고 에너지 폐기물 처리 서비스를 제공합니다. 원유·가스를 생산하는 E&P 기업이 고객인 물 인프라 사업입니다.',
        '2025년 매출 525,553,000 USD는 생산수 처리 471,626,000·용수/재사용 40,453,000·기타 13,474,000입니다. 회수 원유 37,093,000은 생산수 처리 안에 포함되며 추가 매출이 아닙니다.',
        [('생산수 · 집하·운송', '원유·가스 생산에 따라 나오는 물을 고객 유정에서 배관으로 받습니다. 장기 광구 전용·최소 물량 계약과 실제 처리량을 구분합니다.'),
         ('처분 · 지하 pore space', '주입정·지층 공간과 허가가 필요합니다. LandBridge의 surface·pore 접근과 설계/허가 용량은 실제 처리한 물량이 아닙니다.'),
         ('재사용·용수', '물을 처리해 완결 등 고객 수요에 공급합니다. 생산수 집하 대가와 재사용·freshwater 수입을 분리합니다.'),
         ('회수 원유 · skim oil', '생산수에서 회수한 원유 수입입니다. 2025년 생산수 서비스 434,533,000과 회수 원유 37,093,000이 생산수 처리 매출 471,626,000을 이룹니다.'),
         ('Desert Environmental · 폐기물', '비위험 에너지 폐기물을 받는 별도 시설 사업입니다. 생산수 배관·주입정과 고형 폐기물 시설의 허가·대가를 구분합니다.'),
         ('TPL·LandBridge · 통로', '약 64,000 acre AMI의 배관 통로·시설·생산수 판매 권리와 로열티/수익 배분 조건이 있습니다. 단순 소유 지분보다 실제 시설 접근의 역할이 중요합니다.')],
        customers='bpx·Chevron·Devon·EOG·Permian Resources가 명시된 고객입니다. 주요 5곳의 물 관련 매출 약 51%와 Devon·PR의 전체 연결 매출 합계 약 30%는 다른 분모입니다.',
        inputs='배관·펌프·처리/재사용·주입정·전력과 surface/pore 접근이 필요합니다. LandBridge·TPL 권리, 고객 생산수 공급과 폐기물 수요를 연결합니다.',
        competition='Delaware의 물 집하·주입·재사용·배관 통로·허가와 장기 고객 계약에서 경쟁합니다. 회사 처리 물량·설계 용량·허가 용량을 업계 점유율로 치환하지 않습니다.'),
}

CURRENT = {
    'INR': [('Ohio 취득 후 · 2026 Q2', '2026-02-23 취득 후 Q2 회사 귀속 생산은 348.5 MMcfe/d입니다. 설계 용량이나 2025년 연간 매출의 생산 기준과 다릅니다.', INR_Q2),
            ('NOG 공동사업', '상류·중류 취득은 Infinity 운영60%·NOG 비운영40%이며 실제 완료 거래입니다.', NOG_UTICA)],
    'GFR': [('Great Divide · 실제 취득 완료', '2026-08-05 Connacher 취득 완료로 Pod One·Algar SAGD를100% 보유합니다. 조정 포함 현금 대가1.297b CAD와 2025년 Hangingstone 실적을 구분합니다.', GFR_MDA),
            ('판매 계약 · 2026 Q2 확인', '일부 production의 판매 수수료 계약은2028년10월까지 이어집니다. 일부 Demo 계약 종료를 전체 물량·신규 Great Divide 구매 경로로 확대하지 않습니다.', GFR_MDA)],
    'EGY': [('Baobab · 실제 재가동', 'FPSO 정비 후 2026년6월 원유 생산을 다시 시작했습니다. 연말 개발 유정 계획·Kossipo 개발은 현재 재가동 물량과 다릅니다.', EGY_Q2),
            ('Canada · 실제 사업 철수', '2026-02-19 전면 매각을 완료했습니다. 2025년 지역 매출은 처분 전 생산 자료이며 현재 운영 자산에서 제외합니다.', ANNUAL['EGY'])],
    'GPRK': [('2026 Q2 · 현재 개발', 'Colombia 생산과 Argentina Vaca Muerta 개발에 투자합니다. 2025년 처분 Brazil·Ecuador 수입과 현재 운영을 구분합니다.', GPRK_Q2),
             ('Vitol · 2026 갱신', '원유 offtake·선급금 계약은2028년말까지 연장됐습니다. 인도 확대·차입 한도와 실제 사용 금액을 구분합니다.', ANNUAL['GPRK'])],
    'GTE': [('남미 매각 · 승인 대기', '2026-09-23 자료상 주주총회는10월9일 예정이며 Colombia·Ecuador 규제 승인도 남아 있습니다. Maurel & Prom 매각을 완료로 표시하지 않습니다.', GTE_SALE),
            ('Ecopetrol · 조건 충족', 'Tisquirama49% earn-in 조건은Q2 충족했고 Suroriente carry 약정은2026-07-18 충족했습니다. 상품 구매와 공동개발은 다릅니다.', GTE_Q2)],
    'KOS': [('Tiberius · 실제 farm-down', '2026년7월 거래 완료 후 Kosmos33.34%·Occidental33.33%·Navitas33.33%입니다. 개발·host 연결 계약이며 이미 첫 생산한 물량이 아닙니다.', KOS_Q2),
            ('Equatorial Guinea · 매각 완료', 'Ceiba·Okume 지분40.375%는2026-06-16 Panoro에 매각 완료했습니다. 2025년 지역 매출과 현재 생산 자산을 구분합니다.', KOS_Q2)],
    'TALO': [('Shell 자산 · 실제 인수 완료', '2026-09-22 Coulomb·Na Kika 취득을 완료했습니다. Talos closing cash420,000,000 USD에는 escrow42,500,000이 포함되며 최초850,000,000과 조정 전/후 범위가 다릅니다.', TALO_CLOSE),
             ('Monument·West Vela · 향후 단계', 'Monument 첫 생산은2026년말 목표, 신규 West Vela 계약은2027년중반 시작입니다. 완료 자산 인수와 향후 가동·인도를 구분합니다.', TALO_Q2)],
    'WTI': [('2026 Q2 · 보고 생산', '2026년Q2 생산34,700 boe/d·liquids49%는 회사의 해당 분기 자료입니다. 전체 시장점유율이나 향후 물량 보장이 아닙니다.', QUARTER['WTI'])],
    'DEC': [('Sheridan · 실제 취득', '2026-04-30 East Texas 자산 취득 완료, 조정 후 대가236,000,000 USD입니다. 약정 가격245,000,000과 범위가 다릅니다.', QUARTER['DEC']),
            ('Camino·Carlyle · 실제 완료', '2026-07-02 거래 완료로 생산 자산 SPV는DEC40%·Carlyle60%, 미개발 광구는DEC100%입니다. ABS895,000,000과 양측 equity contribution은 별도입니다.', QUARTER['DEC'])],
    'REPX': [('New Mexico · 계약 단계', '2026년 새 가스 구매·처리 계약의 광구 전용·최소 물량 조건은 가동 개시부터 적용됩니다. 계약 체결과 실제 가동일을 같은 상태로 표시하지 않습니다.', QUARTER['REPX'])],
    'HPK': [('현재 시설·제품', '2026년Q2 자료는 Flat Top·Signal Peak 생산과 현금·투자 범위를 보고합니다. 과거 인력 경력·계획 광구를 현재 계약 상대·판매 물량으로 바꾸지 않습니다.', QUARTER['HPK'])],
    'SD': [('2026 Q2 · 신규 유정', 'NW STACK 신규 유정 판매와 기존 생산·비운영 투자를 구분합니다. 계획 drilling inventory는 가동 유정 수·판매 실적이 아닙니다.', SD_Q2)],
    'PED': [('Juniper 편입 후 · 2026 Q2', 'North Peak·Century를 포함한 통합 사업의 Q2 생산6,801 boe/d입니다. 2025년 취득 후2개월 연결 수입과 같은 기간 비교가 아닙니다.', PED_Q2)],
    'EPSN': [('2026 Q2 · 소규모 처분', '2026-05 Pennsylvania ORRI3,900,000 USD와 Texas wellbore300,000을 처분했습니다. 수취 대금은 원유·가스 제품 수입이 아닙니다.', QUARTER['EPSN'])],
    'TXO': [('Cross Timbers · 세 거래 실제 완료', '2026-04-01·04-30·05-28 처분 완료 후TXO net proceeds는각8.2m·30.8m·59.4m USD입니다. 마지막CTOC 거래를 승인 대기·현재 생산 자산으로 표시하지 않습니다.', QUARTER['TXO'])],
    'WBI': [('Ranger · 실제 취득', '2026-06-22 Ranger Water Midstream 취득 완료 후Lea County 기반이 추가됐습니다. Q2 보고 물 처리2.6m bpd와 매출217.8m USD는 해당 분기 범위입니다.', WBI_Q2),
            ('Speedway · 실제 초기 가동', 'Phase I는2026년7월 첫 물량을 처리했습니다. 신규 폐기물 시설·Phase II 확장 계약/건설과 실제 초기 처리량을 구분합니다.', WBI_Q2)],
}
DRIVERS = {
    'INR': [('제품·가격 차액', 'Ohio 원유·가스·NGL 조성, 지역 가격 차액과 판매 경로를 확인합니다.'), ('집하·물', '취득 후 자체 망의 처리·압축·물 비용과 외부 수수료를 구분합니다.')],
    'GFR': [('SAGD 투입', '증기·천연가스·전력·물 사용과 시설 정비를 확인합니다.'), ('WCS·희석제', '역청 기준 가격 차액·콘덴세이트 가격/혼합량·배관·로열티가 순수입에 연결됩니다.')],
    'EGY': [('PSC·지분', 'WI·paying interest·NRI와 정부 비용 회수·이익 원유 조건을 구분합니다.'), ('해상 가동·lifting', 'FPSO 정비·유정 연결·원유 재고와 실제 lifting 일정이 판매 시점에 연결됩니다.')],
    'GPRK': [('운송·판매·상환', '원유 인도와 선급금 금융 상환, 지역 운송 조건을 분리합니다.'), ('개발·carry', 'Vaca Muerta 투자와 GyP recoverable carry·시추·허가를 확인합니다.')],
    'GTE': [('국가 계약', 'Ecuador profit-sharing과 Colombia royalties·carry, Canada 제품 조성을 구분합니다.'), ('매각 조건', '남미 처분의 주주·규제 승인 및 매각 전/후 실적을 확인합니다.')],
    'KOS': [('LNG 약정', 'SPA 최소 인도·FLNG 운전·기온·원료 처리와 실제 cargos를 구분합니다.'), ('심해 개발', '리그·해저 연결·host 시설·partner carry 및 유정 상태가 개발 지출에 연결됩니다.')],
    'TALO': [('해상 시설', '기존 플랫폼 uptime·유정 연결·리그·배관과 해체 책임을 확인합니다.'), ('개발 시점', '인수 완료·farm-in·개발 결정·시추·첫 생산의 단계와 비용을 구분합니다.')],
    'WTI': [('상품 조성', '원유·가스·NGL 실현 가격·반출 비용과 생산 비율을 확인합니다.'), ('퇴역 책임', '현재·과거 매각 자산의 plugging·decommissioning·surety 비용을 구분합니다.')],
    'DEC': [('기존 유정 유지', '정비·압축·집하·생산 감소·폐쇄 의무와 인수 후 운영 지출을 확인합니다.'), ('헤지·구조', '실물 판매·파생상품 평가·ABS·공동사업과 별도 광구 귀속 범위를 구분합니다.')],
    'REPX': [('순판매 비용', '가스·NGL 판매에서 처리·운송비를 차감해 음수가 되는 순정산을 보존합니다.'), ('처리·발전', 'Targa 최소 물량·새 시설 가동일과 RPC 발전·연료·전력 비용을 구분합니다.')],
    'HPK': [('물·인공 채유', '자체 물 처리·재사용·전력·인공 채유와 신규 완결 지출을 확인합니다.'), ('원유 약정', 'Delek 최소 gross 물량·초과 인도 offset·가격 지수와 실제 판매를 구분합니다.')],
    'SD': [('개발·기존 생산', 'NW STACK 신규 유정과 기존 Mid-Continent 유지·비운영 완결을 확인합니다.'), ('제품 처리', '가스·NGL 처리 대가·원유 운송·가격 차액을 별도 확인합니다.')],
    'PED': [('운영자 의존', '비운영자의 시추·완결·판매·현금 배분과 자체 운영 투자 조건을 구분합니다.'), ('허가·통합', '연방 광구·물/배관 허가와 취득 후 운영·비용 범위가 연결됩니다.')],
    'EPSN': [('Auburn 요율', 'anchor와cross-flow 요율, CPI 조정·흡입압·처리량에 따라 집하 수입이 달라집니다.'), ('인도점', 'firm 운송권 없이Zone4에서 판매하는 지역 가스 가격·구매자·배관 제약을 확인합니다.')],
    'TXO': [('유정·처분', '기존 생산 유지·정비와Williston 편입·Cross Timbers 처분 후 범위를 확인합니다.'), ('판매·헤지', '상품 인도·수취 가격·파생상품과partnership 분배 현금을 구분합니다.')],
    'WBI': [('물량·계약', '고객 유정 생산수·광구 전용·최소 물량·요율·고객별 분모를 확인합니다.'), ('주입·접근', 'pore/surface 접근·주입 허가·유발 지진 제한·펌프 전력·재사용 수요를 구분합니다.')],
}
for _symbol, _notes in PUBLIC.items():
    _notes['brief'].extend(fact(title, detail, origin) for title, detail, origin in CURRENT[_symbol])
    _notes['drivers'] = [fact(title, detail, GFR_AIF if _symbol == 'GFR' else ANNUAL[_symbol])
                         for title, detail in DRIVERS[_symbol]]
    _notes['revenue_mix'] = REPORTS[_symbol]['revenue_mix']
    _notes['filings'] = [ANNUAL[_symbol], QUARTER[_symbol]]
    _notes['sources'].extend(row[2] for row in CURRENT[_symbol])

PUBLIC['DEC']['products'][4]['source'] = DEC_RETIREMENT
PUBLIC['DEC']['sources'].append(DEC_RETIREMENT)
PUBLIC['EPSN']['brief'].append(fact('Peak·현재 생산 지역',
    '2025-11-14 Peak 취득 후 Powder River Wyoming이 추가됐습니다. Pennsylvania 가스·집하, Texas/New Mexico Permian, Alberta 생산을 구분합니다. Oklahoma 전 지분은2025년 처분됐습니다.', ANNUAL['EPSN']))
PUBLIC['EPSN']['products'].extend([
    fact('Permian · Texas·New Mexico', '직접·비운영 지분의 원유·가스·NGL입니다. 비운영자의 완결·판매·정산과 Pennsylvania 자체 가스 인도점이 다릅니다.', ANNUAL['EPSN']),
    fact('Alberta · Canada', 'Western Canadian Sedimentary Basin 원유·가스 생산입니다. Canada 운영 지역과 보고 재무의 USD 표시 통화를 구분합니다.', ANNUAL['EPSN']),
    fact('Peak · 실제 Wyoming 취득', '2025-11-14 취득으로 직접·비운영 광구와 운영 인력이 추가됐습니다. 원유·가스 매출의 취득 후 연결 기간과 전체 연간 실적을 구분합니다.', ANNUAL['EPSN']),
])

PRIVATE = {}
def _role(key, name, origin, business, role, inputs):
    PRIVATE[key] = profile(name, origin, business, role,
        [('사업 역할', role), ('연결 공정·투입', inputs)],
        customers='관계도에서 확인된 고객·공동사업과 각 계약의 기준일을 확인합니다.',
        inputs=inputs, competition='이 페이지는 출처가 확인된 특정 사업 역할을 정리합니다. 전체 모기업의 모든 사업·계약이나 제품 시장점유율을 뜻하지 않습니다.')

_role('marathon-oil-inr', 'Marathon Oil Company', ANNUAL['INR'], 'Infinity의 원유·가스 제품 구매자입니다.',
      '2025년 Infinity 제품 매출33% 구매. 기말 매출채권24%와 다른 기준입니다.', '상품 인도·운송·정산 경로입니다. 시추 장비 공급 계약과 다릅니다.')
_role('bp-america-inr', 'BP America', ANNUAL['INR'], 'Infinity의 제품 구매자입니다.',
      '2025년 제품 매출35%·매출채권53%는 다른 분모입니다.', '원유·가스 제품 인도와 계약 정산을 연결합니다.')
_role('ergon-inr', 'Ergon', ANNUAL['INR'], 'Infinity의 제품 구매자입니다.',
      '2025년 제품 매출16%·기말 매출채권18%를 구분합니다.', '원유·가스 제품 인도·처리·정산 경로입니다.')
_role('cnooc-hangingstone', 'CNOOC · Hangingstone', GFR_AIF, 'Hangingstone Expansion 오일샌드 공동사업 상대입니다.',
      'Greenfire 운영75%·CNOOC25%. Demo100%와 별도입니다.', 'SAGD 원유·증기·에너지·희석 및 배관을 연결합니다.')
_role('trafigura-canada-greenfire', 'Trafigura Canada', GFR_AIF, 'Greenfire Expansion의 희석 역청 구매·콘덴세이트 공급 계약 상대입니다.',
      'Expansion 계약은2028-10-01까지입니다. 다른 Demo·Great Divide 물량 전체로 확대하지 않습니다.', '역청 구매·희석제 제공·운송/판매 정산이 서로 다른 역할입니다.')
_role('connacher-greenfire', 'Connacher Oil and Gas', GFR_MDA, 'Great Divide Pod One·Algar SAGD 운영 사업입니다.',
      '2026-08-05 Greenfire가 실제 취득해100% 편입했습니다.', '오일샌드 증기·가스·물·전력·희석제와 원유 반출이 필요합니다.')
_role('bw-energy-vaalco', 'BW Energy', EGY_BWE, 'Gabon Niosi·Guduma 탐사 공동사업 운영사입니다.',
      'BW Energy37.5%·Vaalco37.5%·Panoro25%의 탐사 공동사업입니다.', '지질·물리 탐사·허가·시추와 이후 개발 판단을 연결합니다.')
_role('panoro-energy', 'Panoro Energy', KOS_Q2, '아프리카 원유 광구 공동사업·취득 상대입니다.',
      'Kosmos Ceiba·Okume 지분을2026-06-16 취득 완료했습니다.', '해상 유정·시설·원유 반출·공동 운영을 연결합니다.')
_role('vitol-colombia-geopark', 'Vitol C.I. Colombia', ANNUAL['GPRK'], 'GeoPark Colombia 원유 구매·선급금 계약 상대입니다.',
      '2026년 갱신 offtake는2028년말까지, committed330m USD+추가170m 옵션입니다. 실제 사용금액과 다릅니다.', '원유 인도·선급금·원유 상환과 운송 조건을 연결합니다.')
_role('hocol-geopark', 'Hocol', ANNUAL['GPRK'], 'Ecopetrol 계열 Llanos 광구 공동사업 상대입니다.',
      'GeoPark과 여러 Colombia Llanos 탐사·생산 광구에 참여합니다.', '공동 유정 개발·탐사·허가·원유 반출을 연결합니다.')
_role('parex-geopark', 'Parex Resources', ANNUAL['GPRK'], 'GeoPark Llanos34 원유 공동사업 상대입니다.',
      '광구 공동 개발과 기업 취득 제안·지분 투자 역할은 별도입니다.', '유정·원유 처리·운송과 공동 투자 결정을 연결합니다.')
_role('gyp-neuquen', 'Gas y Petróleo del Neuquén', ANNUAL['GPRK'], 'Neuquén의 주정부 에너지 기업이며GeoPark Vaca Muerta 사업 상대입니다.',
      'Puesto Silva Oeste 경제 지분5%, GeoPark95%·회수 가능한carry 조건입니다.', '광구 권리·개발 지출·생산 몫과carry 회수를 연결합니다.')
_role('ecopetrol-grantierra', 'Ecopetrol', GTE_Q2, 'Gran Tierra Colombia 광구 공동사업 상대입니다.',
      'Tisquirama49% earn-in 조건과Suroriente 투자carry 충족은 서로 다른 계약입니다.', '공동 광구 개발·유정 운영·투자와 제품 인도를 연결합니다.')
_role('maurel-prom-grantierra', 'Maurel & Prom', GTE_SALE, 'Gran Tierra Colombia·Ecuador 사업의 인수 계약 상대입니다.',
      '2026-09-23 기준 주주·규제 승인 대기입니다. 인수 완료·기존 상품 구매자로 표시하지 않습니다.', '거래 승인·부채/선급금 승계와 취득 후 광구 운영을 구분합니다.')
_role('tullow-kosmos', 'Tullow Oil', ANNUAL['KOS'], 'Ghana Jubilee·TEN의 해상 광구 운영사입니다.',
      'Kosmos의 비운영 지분과Tullow 운영·유정·FPSO 관리를 연결합니다.', '해상 유정·시설·해저 연결·물 주입·원유 판매가 필요합니다.')
_role('gnpc-kosmos', 'Ghana National Petroleum Corporation', ANNUAL['KOS'], 'Ghana Jubilee·TEN의 국영 광구 공동사업 상대입니다.',
      '광구 참여·계약·paying interest와정부 royalties는 다른 권리·의무입니다.', '광구 개발·정부 계약·유정/시설 공동 운영을 연결합니다.')
_role('bp-gas-marketing-gta', 'BP Gas Marketing', ANNUAL['KOS'], 'GTA Phase1 LNG offtake 구매자입니다.',
      'SPA는초기2033년말·판매자10년연장 옵션, 최소 인도·부족분 조건이 있습니다.', '원료 가스·FPSO·배관·FLNG·선적과 계약 인도를 연결합니다.')
_role('navitas-offshore', 'Navitas Petroleum', KOS_Q2, 'Gulf 심해 개발 공동사업 상대입니다.',
      'Tiberius33.33% 실제 farm-in·Kosmos33.34%·Occidental33.33% 개발 공동사업입니다.', '해저 유정·host 연결·개발 지출·carry와 첫 생산 단계를 구분합니다.')
_role('beacon-offshore-talos', 'Beacon Offshore Energy', TALO_Q2, 'Talos Monument·Shenandoah 연결 개발의 운영사입니다.',
      'Monument41.7% 운영, Talos29.7%·Navitas28.6%입니다. 첫 생산은향후목표입니다.', '심해 개발 유정·시설tieback·운영·원유 반출을 연결합니다.')
_role('ridgewood-talos', 'Ridgewood Energy', TALO_CLOSE, 'Talos와Shell Gulf 자산을 공동 취득한 투자·광구 상대입니다.',
      '2026-09-22 Coulomb·Na Kika 관련 실제 취득, Talos 귀속 지분/대가와구분합니다.', '광구 지분·공동 취득·생산시설 운영과제품 판매를 구분합니다.')
_role('caribx-honduras-talos', 'CaribX', TALO_Q2, 'Talos Honduras 탐사 광구의 기존 보유·공동사업 상대입니다.',
      'Talos45% 실제 취득과추가35% 승인대기, CaribX 목표잔존20%의조건을구분합니다.', '광구 권리·탄성파 탐사·승인과향후시추·개발단계를연결합니다.')
_role('bp-products-na-wti', 'BP Products North America', ANNUAL['WTI'], 'W&T 원유·가스·NGL 제품 구매자입니다.',
      '2025년 W&T 제품 판매33%이며BP America의Infinity 구매비율과별도입니다.', '제품 인도·반출·계량·가격차액과정산을연결합니다.')
_role('monza-energy-wt', 'Monza Energy', ANNUAL['WTI'], 'W&T와외부투자자의해상유정공동개발사업입니다.',
      '회사·제삼자·CEO 관련투자자가참여하며지분비례연결합니다. 단독전액지배자회사로표시하지않습니다.', '시추·완결·시설연결·공동자금과귀속생산을연결합니다.')
_role('sheridan-diversified', 'Sheridan Holding Company III', QUARTER['DEC'], 'Diversified의East Texas 자산매도자입니다.',
      '2026-04-30 실제완료·조정후236m USD이며기존가스구매자가아닙니다.', '생산유정·집하·임차권·관련의무의취득범위를구분합니다.')
_role('carlyle-camino', 'Carlyle · Camino', QUARTER['DEC'], 'Diversified Camino 생산자산SPV 공동사업상대입니다.',
      '2026-07-02 완료후생산자산DEC40%·Carlyle60%, 미개발광구는DEC100%입니다.', 'equity·ABS부채·생산자산과별도미개발광구를구분합니다.')
_role('conduit-riley', 'Conduit Power', ANNUAL['REPX'], 'Riley의가스발전RPC Power 50/50 공동사업상대입니다.',
      '가스활용현장발전·전력공급과별도원유/가스판매를구분합니다.', '가스연료·발전설비·전력인도·운영과투자가연결됩니다.')
_role('rpc-power-riley', 'RPC Power', ANNUAL['REPX'], 'Riley·Conduit의가스발전공동사업입니다.',
      '각50% 공동참여이며Riley의전액지배자회사·일반가스구매자로표시하지않습니다.', '자체생산전력·외부판매와유정전력수요·연료정산을구분합니다.')
_role('north-peak-pedevco', 'North Peak Oil & Gas', ANNUAL['PED'], 'PEDEVCO가취득한원유·가스운영사업입니다.',
      '2025-10-31 실제취득후연결됐으며취득전실적은연간자체매출에합산하지않습니다.', 'D-J·PRB 등광구와유정·운영/비운영참여·제품반출을연결합니다.')
_role('century-pedevco', 'Century Oil and Gas Sub-Holdings', ANNUAL['PED'], 'PEDEVCO 취득운영사업입니다.',
      'North Peak과함께2025-10-31 실제편입한법인이며외부상품구매자와다릅니다.', '취득후자산·부채·운영인력과지분귀속실적을구분합니다.')
_role('auburn-epsilon', 'Auburn Gas Gathering System', ANNUAL['EPSN'], 'Pennsylvania 가스집하·압축공동사업입니다.',
      'Epsilon35%·AMS43.875%·Equinor21.125%, Williams계열운영입니다.', 'anchor·cross-flow요율·압축/탈수·Tennessee배관연결을구분합니다.')
_role('arm-epsilon', 'ARM Energy Management', ANNUAL['EPSN'], 'Epsilon Pennsylvania 가스판매대행서비스입니다.',
      'nomination·인보이스·수금·정산을관리하며최종구매자34곳과구분합니다.', '구매계약·배관인도점·물량지명과대행수수료를연결합니다.')
_role('gunvor-txo', 'Gunvor USA', ANNUAL['TXO'], 'TXO 원유·가스·NGL 제품구매자입니다.',
      'Chevron USA·Plains와합쳐2025년상품매출42%초과입니다. 각자비율을추정하지않습니다.', '제품인도·운송·가격조정과정산을연결합니다.')
_role('cross-timbers-txo', 'Cross Timbers Energy', QUARTER['TXO'], 'TXO·XTO 측50/50 공동사업이며2026년자산처분후정리중입니다.',
      '세거래는2026년4·5월완료했습니다. 과거생산자산을현재동일자산으로표시하지않습니다.', '지분비례연결·관리·현금배분과청산/자산처분을구분합니다.')
_role('ctoc-txo', 'CTOC Energy', QUARTER['TXO'], 'Cross Timbers 자산의실제인수자입니다.',
      '2026-05-28 마지막자산거래완료, TXO net proceeds59.4m USD입니다.', '광구·생산시설취득과권리/의무이전을연결하며상품구매와구분합니다.')
_role('mewbourne-waterbridge', 'Mewbourne', ANNUAL['WBI'], 'WaterBridge Delaware 물서비스의주요고객입니다.',
      '주요5곳물관련매출집중도에포함되며개별전체회사비율은추정하지않습니다.', '원유·가스유정생산수·배관전용·처리·재사용과인도물량을연결합니다.')
_role('ranger-waterbridge', 'Ranger Water Midstream', WBI_Q2, 'Lea County 생산수인프라운영사업입니다.',
      '2026-06-22 WaterBridge 실제취득으로편입됐습니다.', '생산수집하·처분·배관·고객계약과주입허가를연결합니다.')

_role('next-lvl-diversified', 'Next LVL Energy', DEC_RETIREMENT, 'Diversified의 완전지배 유정 폐쇄·복구 서비스 사업입니다.',
      '자체 퇴역의무 이행과 타사업자·주정부 프로그램의 외부 유정 서비스를 구분합니다.', 'cementing·wireline·폐쇄·복구와 계약 범위·현금 대가를 연결합니다.')
_role('peak-epsilon', 'Peak Exploration & Production', ANNUAL['EPSN'], 'Epsilon이 취득한 Powder River 운영 사업입니다.',
      '2025-11-14 실제 취득으로 Wyoming 직접·비운영 광구와 인력이 편입됐습니다.', '취득 후 유정·시설·임차권·상품 판매와 연간 연결기간을 구분합니다.')

EDGES = {
    'INR': [relation('Marathon Oil Company', None, 'customer', '2025년 제품 매출33%·매출채권24%는 별도 기준.', ANNUAL['INR'], 'marathon-oil-inr'),
            relation('BP America', None, 'customer', '2025년 제품 매출35%·매출채권53%는 별도 기준.', ANNUAL['INR'], 'bp-america-inr'),
            relation('Ergon', None, 'customer', '2025년 제품 매출16%·매출채권18%는 별도 기준.', ANNUAL['INR'], 'ergon-inr'),
            relation('Northern Oil and Gas', 'NOG', 'partner', 'Ohio 취득 완료 · Infinity운영60%·NOG40%.', NOG_UTICA),
            relation('Antero Resources', 'AR', 'transaction', '2026-02-23 Ohio 상류 자산 매각 완료 · 현재 운영자는Infinity.', ANNUAL['INR']),
            relation('Antero Midstream', 'AM', 'transaction', '2026-02-23 Ohio 집하·물 자산 매각 완료 · 현재 외부 집하 서비스 계약으로 추정하지 않음.', ANNUAL['INR'])],
    'GFR': [relation('CNOOC · Hangingstone', None, 'partner', 'Expansion25%·Greenfire운영75%, Demo100%와 별도.', GFR_AIF, 'cnooc-hangingstone'),
            relation('Trafigura Canada', None, 'customer', 'Expansion 희석 역청 구매·2028-10-01까지 · Demo/Great Divide 전체 물량으로 확대하지 않음.', GFR_AIF, 'trafigura-canada-greenfire'),
            relation('Trafigura Canada', None, 'supplier', 'Expansion 콘덴세이트 공급·원유 구매와 다른 역할.', GFR_AIF, 'trafigura-canada-greenfire'),
            relation('TC Energy', 'TRP', 'supplier', 'NGTL 천연가스 공급 경로 · SAGD 증기 투입용 가스·송수송.', GFR_AIF),
            relation('Enbridge', 'ENB', 'supplier', 'Cheecham·Waupisoo/Athabasca·Wood Buffalo 계통의 희석 역청 반출.', GFR_AIF),
            relation('Connacher Oil and Gas', None, 'subsidiary', '2026-08-05 실제 취득 · Great Divide100% 편입.', GFR_MDA, 'connacher-greenfire')],
    'EGY': [relation('EGPC', None, 'partner', 'Egypt 두PSC·운영JV50/50 · cost recovery·정부 몫과 구분.', ANNUAL['EGY'], 'egpc-egypt'),
            relation('BW Energy', None, 'partner', 'Niosi·Guduma 운영37.5%·Vaalco37.5%·Panoro25%.', EGY_BWE, 'bw-energy-vaalco'),
            relation('Panoro Energy', None, 'partner', 'Niosi·Guduma25% 탐사 공동사업.', EGY_BWE, 'panoro-energy'),
            relation('Borr Drilling', 'BORR', 'supplier', 'Norve Gabon 시추 · 2026-02 FSR의2025-11~2026-09 계약·연장옵션, 이후 연장 완료를 추정하지 않음.', BORR_NORVE)],
    'GPRK': [relation('Vitol C.I. Colombia', None, 'customer', '2026년 갱신 원유 offtake·선급금 · 2028년말까지.', ANNUAL['GPRK'], 'vitol-colombia-geopark'),
             relation('Hocol', None, 'partner', 'Ecopetrol 계열·Llanos87/123 등 광구 공동 개발.', ANNUAL['GPRK'], 'hocol-geopark'),
             relation('Parex Resources', None, 'partner', 'Llanos34 공동 개발 · 취득 제안·지분투자와 별도.', ANNUAL['GPRK'], 'parex-geopark'),
             relation('Gas y Petróleo del Neuquén', None, 'partner', 'Puesto Silva Oeste5% 경제 지분·GeoPark95%·회수 가능한carry.', ANNUAL['GPRK'], 'gyp-neuquen')],
    'GTE': [relation('Ecopetrol', None, 'partner', 'Tisquirama·Suroriente 공동 개발·carry · 2026년 조건충족과 원유 구매는 별도.', GTE_Q2, 'ecopetrol-grantierra'),
            relation('Maurel & Prom', None, 'transaction', '2026-09-23 남미 사업 매각 주주·규제 승인 대기 · 미완료.', GTE_SALE, 'maurel-prom-grantierra')],
    'KOS': [relation('BP Gas Marketing', None, 'customer', 'GTA LNG SPA·초기2033년말+판매자10년연장옵션·최소 인도 조건.', ANNUAL['KOS'], 'bp-gas-marketing-gta'),
            relation('BP', 'BP', 'partner', 'GTA 가스·LNG 공동사업 운영 · BPGM 구매 계약과 별도.', ANNUAL['KOS']),
            relation('Tullow Oil', None, 'partner', 'Ghana Jubilee·TEN 해상 광구 운영사.', ANNUAL['KOS'], 'tullow-kosmos'),
            relation('GNPC', None, 'partner', 'Ghana 공동 광구 참여·계약과 paying interest.', ANNUAL['KOS'], 'gnpc-kosmos'),
            relation('Occidental', 'OXY', 'partner', '2026년7월 Tiberius33.33%·host시설 소유/운영 · 개발 단계.', KOS_Q2),
            relation('Navitas Petroleum', None, 'partner', 'Tiberius33.33% 실제 farm-in · Kosmos33.34%·OXY33.33%.', KOS_Q2, 'navitas-offshore'),
            relation('Shell', 'SHEL', 'partner', 'Norphlet10블록 공동 탐사·Trailblazer 미래 시추 · 현재 생산 아님.', KOS_Q2),
            relation('Panoro Energy', None, 'transaction', 'Ceiba·Okume40.375% 매각2026-06-16 실제 완료.', KOS_Q2, 'panoro-energy')],
    'TALO': [relation('Shell Trading (US)', None, 'customer', '2025년 제품 매출35% 구매 · Shell Offshore 자산 취득과 별도.', ANNUAL['TALO'], 'shell-trading-us-producers'),
             relation('ExxonMobil', 'XOM', 'customer', '2025년 제품 매출23% 구매.', ANNUAL['TALO']),
             relation('Chevron', 'CVX', 'customer', '2025년 제품 매출12% 구매.', ANNUAL['TALO']),
             relation('Seadrill', 'SDRL', 'supplier', 'West Vela 시추·평가 및 신규2027년중반 시작1년계약 · 기간 구분.', TALO_Q2),
             relation('Beacon Offshore Energy', None, 'partner', 'Monument운영41.7%·Talos29.7%·Navitas28.6%·미래 첫생산.', TALO_Q2, 'beacon-offshore-talos'),
             relation('Navitas Petroleum', None, 'partner', 'Monument28.6% 개발 공동사업 · Tiberius 별도.', TALO_Q2, 'navitas-offshore'),
             relation('Repsol', 'REPYY', 'partner', '2026년7월 MexicoBlock29 개발farm-in 계약.', TALO_Q2),
             relation('Shell', 'SHEL', 'transaction', 'Coulomb·Na Kika 자산2026-09-22 실제 취득 완료.', TALO_CLOSE),
             relation('BP', 'BP', 'partner', '취득한Na Kika25% 비운영 지분의 플랫폼·광구 운영사.', TALO_CLOSE),
             relation('Ridgewood Energy', None, 'partner', 'Shell자산 공동취득2026-09-22 완료 · Talos 귀속지분·대가 별도.', TALO_CLOSE, 'ridgewood-talos'),
             relation('CaribX', None, 'partner', 'Honduras Talos운영45% 완료·추가35% 승인대기 · 목표80% 전체 완료 아님.', TALO_Q2, 'caribx-honduras-talos')],
    'WTI': [relation('BP Products North America', None, 'customer', '2025년 제품 판매33% 구매.', ANNUAL['WTI'], 'bp-products-na-wti'),
            relation('Shell Trading (US)', None, 'customer', '2025년 제품 판매17% 구매.', ANNUAL['WTI'], 'shell-trading-us-producers'),
            relation('Monza Energy', None, 'partner', '해상 유정 공동자금·지분비례 연결 · 전액지배자회사와 다름.', ANNUAL['WTI'], 'monza-energy-wt')],
    'DEC': [relation('Next LVL Energy', None, 'subsidiary', '완전지배 유정폐쇄·복구·외부서비스 · 자체퇴역의무와 외부매출 별도.', DEC_RETIREMENT, 'next-lvl-diversified'),
            relation('Sheridan Holding Company III', None, 'transaction', '2026-04-30 EastTexas 자산취득 완료 · 조정후236mUSD.', QUARTER['DEC'], 'sheridan-diversified'),
            relation('Carlyle · Camino', None, 'partner', '2026-07-02 Camino생산SPV DEC40%·Carlyle60%, 미개발광구DEC100%.', QUARTER['DEC'], 'carlyle-camino')],
    'REPX': [relation('Targa Resources', 'TRGP', 'supplier', '기존Stakeholder Champions처리·운송과 NewMexico미래15년계약 · 가동시점 별도.', ANNUAL['REPX']),
             relation('Targa Resources', 'TRGP', 'customer', 'NewMexico 새가스구매계약 · 가동일부터15년, 기존익명구매자 비율과별도.', ANNUAL['REPX']),
             relation('Conduit Power', None, 'partner', 'RPC Power50/50 가스발전 공동사업.', ANNUAL['REPX'], 'conduit-riley'),
             relation('RPC Power', None, 'partner', 'Riley50%·Conduit50% 발전 · 자체유정전력/외부판매 별도.', ANNUAL['REPX'], 'rpc-power-riley')],
    'HPK': [relation('Delek', 'DK', 'customer', 'DKTrading&Supply2025년제품매출82%·12년계약·gross최소23,500bopd.', ANNUAL['HPK']),
            relation('Energy Transfer', 'ET', 'customer', 'EnergyTransferCrudeMarketing2025년약8%·Delek와다른최소물량조건.', ANNUAL['HPK'])],
    'SD': [relation('Targa Resources', 'TRGP', 'customer', '2025년TargaPipelineMid-ContinentWestOK50,896,000USD 제품구매.', ANNUAL['SD']),
           relation('Plains All American', 'PAA', 'customer', '2025년제품구매33,551,000USD.', ANNUAL['SD']),
           relation('Valero', 'VLO', 'customer', '2025년제품구매21,600,000USD.', ANNUAL['SD'])],
    'PED': [relation('North Peak Oil & Gas', None, 'subsidiary', '2025-10-31 실제취득 후연결.', ANNUAL['PED'], 'north-peak-pedevco'),
            relation('Century Oil and Gas Sub-Holdings', None, 'subsidiary', '2025-10-31 실제취득 후연결.', ANNUAL['PED'], 'century-pedevco')],
    'EPSN': [relation('Peak Exploration & Production', None, 'subsidiary', '2025-11-14 실제취득 · Wyoming 운영자산 편입.', ANNUAL['EPSN'], 'peak-epsilon'),
             relation('Auburn Gas Gathering System', None, 'partner', 'Epsilon35%·AMS43.875%·Equinor21.125% 집하·압축.', ANNUAL['EPSN'], 'auburn-epsilon'),
             relation('Williams', 'WMB', 'supplier', '계열운영사Auburn 집하·압축 운영 · 자체firm interstate 운송권 없음.', ANNUAL['EPSN']),
             relation('Equinor', 'EQNR', 'partner', 'EquinorPipelines21.125% 집하공동사업·USAOnshore는anchor shipper.', ANNUAL['EPSN']),
             relation('Expand Energy', 'EXE', 'customer', 'SWNEnergyServices2025년전체매출10%초과 구매 및Auburnanchor 역할.', ANNUAL['EPSN']),
             relation('ARM Energy Management', None, 'supplier', 'Pennsylvania가스nomination·인보이스·수금 판매대행 · 최종구매자와별도.', ANNUAL['EPSN'], 'arm-epsilon'),
             relation('HF Sinclair', 'DINO', 'customer', 'HF SinclairRefining&Marketing2025년Wyoming매출68.4% · 전체회사비율아님.', ANNUAL['EPSN']),
             relation('Western Midstream', 'WES', 'customer', 'WGROperating2025년Wyoming매출27.3% · 가스처리역할을구매자비율과구분.', ANNUAL['EPSN'])],
    'TXO': [relation('Chevron', 'CVX', 'customer', 'ChevronUSA·Gunvor·Plains합계2025년상품매출42%초과 · 개별비율미공개.', ANNUAL['TXO']),
            relation('Gunvor USA', None, 'customer', '2025년주요제품구매자 · 세곳합계42%초과.', ANNUAL['TXO'], 'gunvor-txo'),
            relation('Plains All American', 'PAA', 'customer', '2025년주요제품구매자 · 세곳합계42%초과.', ANNUAL['TXO']),
            relation('Cross Timbers Energy', None, 'partner', 'TXO50%·XTO측50% · 2026년자산처분완료·정리중.', QUARTER['TXO'], 'cross-timbers-txo'),
            relation('CTOC Energy', None, 'transaction', '마지막CrossTimbers 자산거래2026-05-28 완료 · TXO순대금59.4mUSD.', QUARTER['TXO'], 'ctoc-txo')],
    'WBI': [relation('BP', 'BP', 'customer', 'bpx Delaware 생산수·물서비스 명시고객.', ANNUAL['WBI']),
            relation('Chevron', 'CVX', 'customer', 'Delaware 물서비스 명시고객.', ANNUAL['WBI']),
            relation('Devon Energy', 'DVN', 'customer', '물서비스·PR과전체매출합계30% · 물관련매출분모와구분.', ANNUAL['WBI']),
            relation('EOG Resources', 'EOG', 'customer', 'Delaware 물서비스 주요고객.', ANNUAL['WBI']),
            relation('Permian Resources', 'PR', 'customer', '생산수·물서비스 · 회사제품매출·원유시장점유율아님.', ANNUAL['WBI']),
            relation('Mewbourne', None, 'customer', '주요물관련매출5곳에포함 · 개별연결매출비율추정하지않음.', ANNUAL['WBI'], 'mewbourne-waterbridge'),
            relation('LandBridge', 'LB', 'supplier', 'surface·pore 접근·주입공간·배관통로 · 미래허가/설계용량과실물처리분리.', ANNUAL['WBI']),
            relation('Texas Pacific Land', 'TPL', 'supplier', '64,000acre AMI reciprocalcrossing·시설·생산수판매권리·royalty/수익배분.', ANNUAL['WBI']),
            relation('Ranger Water Midstream', None, 'subsidiary', '2026-06-22 실제취득 · LeaCounty 물인프라편입.', WBI_Q2, 'ranger-waterbridge')],
}

# Additional evidence for shared counterpart pages; preserve their existing
# contracts instead of replacing a company page with one producer's role.
COMMON_CONTEXT = {
    'shell-trading-us-producers': dict(brief=[fact('Talos · 제품 구매',
        '2025년 Talos 제품매출35% 구매자입니다. Shell Offshore 자산매각과 별도 법인·역할입니다.', ANNUAL['TALO']),
        fact('W&T · 제품 구매', '2025년 W&T 제품매출17% 구매자이며 다른 생산자의 판매비율과 분모가 다릅니다.', ANNUAL['WTI'])], sources=[ANNUAL['TALO'], ANNUAL['WTI']]),
}
PRIVATE['panoro-energy']['sources'].append(EGY_BWE)
PRIVATE['panoro-energy']['brief'].append(fact('Vaalco · 탐사 공동사업',
    'Niosi·Guduma25%·Vaalco37.5%·BW Energy운영37.5%이며 Kosmos 자산 인수와 별도입니다.', EGY_BWE))
PRIVATE['navitas-offshore']['sources'].append(TALO_Q2)
PRIVATE['navitas-offshore']['brief'].append(fact('Talos · Monument',
    'Monument28.6%·Talos29.7%·Beacon운영41.7%입니다. 첫 생산은 목표이며 실제 인도량이 아닙니다.', TALO_Q2))
