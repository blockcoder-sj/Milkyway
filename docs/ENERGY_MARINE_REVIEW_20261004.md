# 해양 시추·선박·항공·유정 서비스 검토

2026-10-04, Asia/Seoul. NE·RIG·SDRL·VAL·TDW·SMHI·VTOL·HOS·XPRO
9곳의 사업·제품·고객·투입·경쟁·최근 상태와 원문 매출 82행을 통합했다.
주 본문은 184/213개이며 남은 29개와 전체 품질 검수가 있다. 이 체크포인트의
검토·커밋·푸시 후 다음 작업을 계속한다.

## 원문과 범위

연차·분기 18개 수신 원본의 크기·SHA-256을 다시 대조했다. Expro 이전
N.V.의 실제 2025 연차 원문을 추가 확보하고 재무 9개를 연결했다. 현재 Ltd
CIK와 이전 N.V. CIK를 합치지 않는다. 연차 재무 원장은 206개 기록, 수치가
있는 201개, 수치 1,576개다. 다른 문서·CIK·범위의 이전 법인 수치는 거절한다.

| 기업 | 확인한 2025 연결 매출 USD와 주요 구분 |
|---|---|
| NE | 3,285,568,000. floater·jackup·기타와 지역 교차표. 시추 소계 재합산 제외. 연말 36기와 연차 작성일 31기는 서로 다른 기준일. |
| RIG | 3,965,000,000. 초심해·가혹 환경과 지역. 9월15일 신규 수주는 익명 고객·2027 예상·backlog이며 매출/현금 아님. Valaris 결합은 proposed. |
| SDRL | 1,437,000,000. 지역별 연결 표. Sonadrill 전체 JV 매출 제외. 자체 15기, Sonangol 소유 관리 2기를 구별. |
| VAL | 2,369,000,000. 연결 3부문·6지역. ARO 전체 JV 매출 제외. Aramco 50/50 JV와 자체 리그·조건부 주식 교환을 구별. |
| TDW | 1,352,786,000. 선박·기타와 지역. 208척 전체 안의 PSV 하위 분류를 추가하지 않음. 익명 상위 고객 비중에 이름 추정 안 함. |
| SMHI | 227,832,000. time charter·bareboat·기타와 지역. 지분법 JV 제외. SEACOR Marine Arabia의 45% 지분과 고객 역할, 예정 신조 인도를 구별. |
| VTOL | 1,490,512,000. 해양·정부·기타와 지역. 정부 SAR와 해양 항공 수송, OEM 부품 공급사를 구별. |
| HOS | 1,291,474,000. 결합 전 Helix의 제품·외부 부문·지역만 포함. 현재 그룹 비중은 산출 제외. 9월 결합·pro forma 자산과 2027 수주를 과거 매출에 더하지 않음. |
| XPRO | 1,607,095,000. 이전 N.V. 제품·4개 보고 지역. 7월 법인 이전·Enhanced Drilling 실제 취득과 2025/2026 Q2 말 범위를 구별. |

상대 기업 역할 프로필 17개와 편집 관계 57개를 추가했다. Azule·LLOG·Saudi
Aramco는 기존 동일 ID를 재사용했다. Sonadrill·ARO·SEACOR Marine Arabia는
소유/협력과 직접 고객 역할이 겹칠 수 있다. 정부 부처·Sikorsky·Leonardo·Nova
Systems·GE Aviation, Sea1 용선 제공자, Helix Well Ops 실제 자회사,
Hercules Sub LLC 최종 합병 승계 법인과 상장 HOS를 구별한다.

Expro 인수 완료, Hornbeck 결합 완료, 9월 수주 공식 자료를 직접 대조했다.
수신 파일 4개와 별도 웹으로 읽은 공식 자료를 구별한다. 실패/시간 초과
수신을 성공 영수증으로 기록하지 않았다. Hornbeck pro forma 발표 사건일
9월2일과 SEC 제출일 9월3일을 구별했다. 익명 고객·미공개 공급사 이름,
시장점유율·거래금액·계약 완료를 추정하지 않았다.

## 기능·성능·코드·보안 증거

- 최종 이미지 전체 검사 728개 / 21.017초 통과, 컨테이너 Node 부재로 18개
  건너뜀. 별도 호스트 Node 연계 9모듈 21개 / 0.613초 통과.
- 해양 회귀 검사 7개: 실제 enrichment·원문 합계·합병 전 범위·조건부 거래,
  소유/용선/JV, 정확한 이전 CIK·accession, 차원·통화·캐시 충돌,
  공유 ID·역방향 이동, 출처 정정 후 중복 카드/원본 보존을 검사한다.
- Chrome에서 Hornbeck의 동일 설명이 서로 다른 출처로 두 번 나오는 것을
  발견했다. 동일 제목·본문은 한 번 표시하고 캐시 원문 출처는 보존하도록
  수정했다. 다른 기간의 다른 설명은 남는다. 첫 전체 검사에서 반복
  enrichment의 source-list 변경 3건을 발견해 수정했으며, 관련 29개와
  최종 전체 검사가 통과했다. 초기 실패 로그를 보존한다.
- 원문 파서·정적 좌표·데이터 연결·source merge 코드를 직접 검토했다.
  네트워크/모델 호출 없는 파서, 한정된 문서·CIK·기간·USD·차원, 내부거래와
  JV/지역 소계 제외를 확인했다. `git diff --check` 통과.
- 최종 이미지 코드·공개 데이터 277개 SHA-256이 로컬 검토 소스와 일치.
- 1 CPU·512 MiB·네트워크 차단 임시 컨테이너: 1,084 entity 초기화 0.884초,
  SQLite quick_check `ok`. 213개 목록 50회 p95 0.238ms, 상세 27회
  p95 7.334ms, 최대 RSS 69,376 KiB. 실제 거래 연속 운영 성능이 아니다.
- 앱만 최종 이미지로 교체했다:
  `sha256:a43de7198879ac0e5c01b6730ada0c667fc6fe9869d7b77025af5e63af49fe82`.
  healthy·startup 200. 다른 개인/시장/backup 서비스와 볼륨은 보존했다.
- 실제 local auth로 신규 9개+기존 6개 API 200, 신규 매출 합계 82행.
  Sonadrill·ARO·SEACOR Marine Arabia·Sikorsky·Helix Well Ops·Enhanced
  Drilling·Azule·LLOG 상세와 역방향 관계 확인. 검증 세션 logout 완료.
- 기존 Chrome 탭 하나로 9개 제목·한국어 제품·매출·관계 표시를 확인했다.
  HOS 합병 전 경고와 비중 제외를 실제 화면으로 확인하고 중복 카드 제거를
  재확인했다. Enhanced Drilling·Sikorsky 링크 클릭 및 Expro·Bristow
  역방향 관계 표시를 확인했다.
- AI 공급자 호출 0회·CodeRabbit 0회. 공개 배포·OCI/KMS는 별도 NO-GO이며
  disabled 권한 세션에서 Deep Scan을 실행하지 않았다. 거래/credential
  권한 경로는 변경하지 않았다.

상세 로그·원본·성능·파일 대조는 Git 제외
`runtime/verification-20261004/marine-*` 및 `service-original-updates/`에 있다.
과거 수집 대기/실패와 10월3일 시세를 새 수집 성공으로 설명하지 않는다.
paper·backtest·company-data·market-details 작업자는 계속 정지 상태다.

다음은 나머지 LNG·석탄·연료·소형 생산자·신규 상장·OTC 기업 29곳이다.
전 기업의 필수 항목·현재성·분류·관계·가독성·화면 검수까지 완료한 뒤
전체 Energy 완료 여부를 판정한다.
