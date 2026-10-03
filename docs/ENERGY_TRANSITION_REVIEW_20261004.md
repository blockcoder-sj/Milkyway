# 신규 법인·복합 사업·생산 전환 8개 검토

2026-10-04. APC·BDCO·IEP·INVX·NUAI·RSRV·SUNC·TBN의 한국어 사업·제품·
판매·투입·경쟁·최근 상태를 편집했다. 매출56행, 실명 역할21개, 편집 관계31개.
주본문206/213이며 신규 상장·OTC7개와 전체 깊이·관계·현재성 검수를 계속한다.

## 원문·수치·현재 상태

- 연차·분기16개 원본 SHA/크기 재확인. 후속 공식6개 원본 수신. IEP 매각
  발표 timeout와 NUAI PPA403은 성공 영수증에서 제외하고 공식 웹 원문을 읽었다.
- APC는 ARKO Petroleum CIK2080921이다. Anadarko와 동일 법인이 아니다.
  비inline 연차의2025 combined statements/F-44 외부 부문을 직접 대조했다.
  연결5,581,264,000 USD를 제품4·외부 부문4로 정리하고, 상장 법인 shell의
  자산2,112천USD와 이전 대상 사업의 자산1,273,474천USD를 섞지 않았다.
  IPO 추가발행 후73.6% 경제·93.3% 의결권, USPP 계약 서명과 완료를 구별했다.
- BDCO 연결279,385,000 USD. 정제276,243,000·외부tolling3,142,000을 사용했다.
  gross tolling5,957,000과 내부2,815,000·연결 소계를 중복 합산하지 않았다.
  자회사 LE/LRM, 주주 측 관계사 LEH, MV Purchasing 원유 공급을 구별했다.
- IEP 전체9,658백만USD는7개 보고 부문+holding8행이다. 투자 순손익과
  계약 제품 매출이 다른 범위라 구성비를 제외했다. 8월20일 Pep Boys 실제
  매각 완료와 잔여 부동산·AAMCO·Precision Tune을 반영했다.
- INVX978,251,000 USD. 제품/서비스/임대3, 시장2, 지리10의 독립 합계를 확인했다.
  NAM/국제·해양 부모 구분을 지리 leaf와 더하지 않는다. 2025 Citadel 취득,
  subsea tree 처분,2026년7월 TCO 취득 완료·소급 미포함을 구별했다.
- NUAI885,400 USD. gas gross2,516,970−집하/처리1,871,492=순645,478과
  NGL239,922만 제품 표에 남겼다. 과거 gas와 현재 TCDC 개발,1월 SharonAI
  지분 취득,9월 PPA 서명·2027Q3 공급 예정·조건부5% project 지분을 구별했다.
  9월24일 공시의 임차인 협상·Texas 허가 중지/감사·일정 지연도 반영했다.
- RSRV17,441,161 USD. 상품16,699,954와lease bonus741,207의 실제 태그를
  각각 읽고 혼합 지표 구성비를 제외했다. Crawley33%·Mewbourne19%는
  회사oil/gas 판매 집중도이며 시장점유율이 아니다. Bailey10%는 비연결 투자다.
- SUNC25,201백만USD. SUN 전체를 모든 비교 기간 연결하는 회계 범위와
  Class D unit 경제 권리·비지배 지분을 구별했다. 제품7·외부4부문·지역3·
  매출 유형3은 각각 같은 총계다. 관리 법인100% 소유를 상장unit100%로 바꾸지 않는다.
- TBN FY2026은6월30일까지 가스 판매 무매출,9월 첫 가스 판매는 이후 실제 변화다.
  dash를 제품별0행으로 발명하지 않는다. gross40TJ/d 계약 plateau·실제
  nomination/ramp·추가 시운전, Falcon 취득/잔여 소수지분 조건·Daly Waters,
  Australia APA 수송과 US APA 생산사, 실제NT계약과비구속LNGMOU를 구별했다.

## 검증

- 최종 전체747개/21.808초 OK(skip18: 컨테이너 Node 부재), 별도 host 화면21개/
  .634초 OK. 관련28개/.302초 OK. CIK·차원·통화·지표·기간·실제 소계/
  gross/net·혼합 지표·반복enrichment·법인·계약 단계·익명 고객 경계를 검사했다.
- 289개 포장 코드/공개데이터 SHA 일치. 직접 source/diff 검토로 모듈 통합,
  원문 좌표·숫자·소유/거래·회계 범위·출처·한국어·미래 단계 경계를 확인했다.
- 1CPU/512MiB 임시 검증:1149entities seed .986초,SQLite quick_check ok,
  213목록50회p95 .155ms,상세24회p95 6.932ms,RSS72308KiB.
  실제 회원feed·장시간 거래·공개 서버 성능의 증거는 아니다.
- 실제 auth 신규8+기존6 기업API200, 역할8개 상세/역방향200,logout.
  app만 sha256:bf1993add5ae702e500aad0efa65ee54032baaceb7fd9e70549ad8c757ed06ef로 교체,healthy.
- 기존Chrome1탭8개 본문·제품·표·관계, NUAI→Luminant 실제 이동/역방향,
  APC·RSRV 지표 한국어와 실제 스크린샷 렌더를 확인했다. 문서 재로딩으로
  갱신된 JS를 읽었으며 표의 raw tag 노출을 한국어 지표 이름으로 바꿨다.
- 초기 canonical 통합의 빈행 cik 참조와 RSRV 혼합 지표 누락을 수정했다.
  실패는 최종 성공 증거에서 제외했다. 원문 요청 실패와 오래된 source는
  현재 완료/미공개 증거로 바꾸지 않는다.
- AI provider/CodeRabbit/DeepScan0. 개인·시장·backup·runtime·Docker 볼륨 보존.
  공개 OCI/KMS 배포·실제 credential 게이트는 별도NO-GO다.

증거는 Git 제외 runtime/verification-20261004/transition-* 등에 보존한다.
검토·커밋·푸시 후 AMEN·EROK·FTW·HMH·NUCL·UNTC·WHK와 최종 전수 검수를 계속한다.
