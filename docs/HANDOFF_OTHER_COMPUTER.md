# Milkyway 다른 컴퓨터용 인계

**최신 상태 2026-10-04:** 사용자가 재개했고 개인 데이터 복원·개발 환경·앱 실행을
검증했다. 확정한 213개 기업 범위의 Energy 조사·탐색을 최종 검수했다.
[최종 검토](ENERGY_FINAL_REVIEW_20261004.md),
[기업별 검수표](ENERGY_SECTOR_COVERAGE_20261004.md), WORK_CONTEXT의 마지막 기록을 먼저 읽는다.
후속 기업별·Energy 전체 3차원 지도는 [우주 지도 검토](ENERGY_CONSTELLATION_REVIEW_20261004.md),
제한된 추가 공시 조사 종료는 [추가 확인 기록](ENERGY_FREE_DATA_CLOSURE_20261004.md)에 있다.
추가 공개 자료 `runtime/handoff/milkyway-energy-constellation-20261004.zip`과
대응 SHA/summary를 함께 복사하며 기존 원문 ZIP이나 개인 백업을 덮어쓰지 않는다.
아래 10월 3일 중단·미완료 기록은 역사적 인계다. 복원한 볼륨에 과거 백업을 다시 덮어쓰지 않는다.
공개 자료의 미확인 상태·다음 공시 갱신과 브로커 실운용·공개 OCI/KMS 배포는 구분한다.
이번 최종 원문·영수증·검사 증거 추가 묶음은
`runtime/handoff/milkyway-energy-final-review-20261004.zip`과 같은 이름의
`.sha256`·`.summary.json`이다. Git에 없으므로 이전 조사 ZIP과 함께 복사한다.
개인 DB·키·`.env`·볼륨은 이 공개 추가 묶음에 포함하지 않는다.

기록일: 2026-10-03, Asia/Seoul. 사용자 지시: **“잠시 작업을 중단하고, 다른 컴퓨터에서도 이어갈 수 있게 인계파일 만들어.”**

## 1. 10월 3일 중단 당시 상태

2026-10-03 새 PC에서 재개 준비를 진행한 뒤, 사용자가 컴퓨터 재시작을 위해 다시 중단했습니다.
현재 PC의 실제 상태는 [재시작 인계문서](RESTART_HANDOFF_20261003.md)를 먼저 읽으세요.
다시 재개하면 아래 미완료 작업을 이어가고, 마일스톤마다 검토·검증·커밋·푸시 후 다음 작업을 계속합니다.
후속 사용자 중단 지시나 실제 차단 사유가 없는 한 마일스톤에서 재개 확인을 요청하지 않습니다.

| 구분 | 실제 상태 |
|---|---|
| 저장소 | https://github.com/blockcoder-sj/Milkyway.git |
| 작업 브랜치 | `codex/ai-research-workflow` |
| 마지막 검증·푸시·로컬 배포 커밋 | `dd0b8eae3a06bd5d5b183a1d18f376724bb6a18a` |
| 해당 GitHub 검사 | run `37117351110`, 실제 `completed / success` 확인 |
| 해당 이미지 | `sha256:27a0a9157119af9237985426c480c31ae1b6afb12b0ab09cff874314465b0cd3` |
| 미국 Energy 목록 | 213개. 주요 목록 155개에 편집 자료 반영, 58개 추가 조사 및 전체 깊이 검토 미완료 |
| 현재 변경 | 광물권·로열티·토지 등 15개 기업의 미완료 코드·출처 저장본 |
| 완료 판정 | 155는 완성 기업 수가 아니며 섹터 전체 완료·모든 정보 확보를 뜻하지 않음 |

소스·데이터 범위와 업종 탐색 그룹은 [ENERGY_RESEARCH_PLAN.md](ENERGY_RESEARCH_PLAN.md)를 읽으세요.
전체 작업 이력은 [WORK_CONTEXT.md](WORK_CONTEXT.md), 마지막 검증의 상세는
[ENERGY_SHIPPING_REVIEW_20261003.md](ENERGY_SHIPPING_REVIEW_20261003.md)입니다.

## 2. 다른 컴퓨터로 가져갈 것

### 현재 프로젝트 폴더에서 무엇을 복사할지

2026-10-03 현재 PC에서 확인한 폴더 기준입니다.

| 폴더·파일 | 옮길 필요 | 용도 |
|---|---|---|
| `Milkyway/` | 개발을 이어갈 때 필요 | 현재 앱 코드, Git 기록, 인계문서, 로컬 설정, `runtime/handoff/`의 공개 조사 ZIP |
| `output/` | 이전 결과도 보관하려면 복사 | 화면 이미지·PDF·통합 전 코드 백업. 현재 Docker 개인 DB 백업을 대신하지 않음 |
| `week10_Milkyway_검수/` | 과거 검수 기록도 보관하려면 복사 | 사용설명서·검수보고서·검증 로그. 앱 실행은 `Milkyway/`에서 진행 |
| `korea-shipping-research/` | 별도 한국 해운 조사도 이어가려면 복사 | 별도 연구 자료·스크립트·대시보드. Milkyway 앱 실행의 필수 폴더는 아님 |
| `report_builder.py` | 기존 PDF를 다시 만들려면 복사 | `output/pdf/`의 별도 보고서 생성 스크립트 |
| `.venv-report/`, `Milkyway/.venv/`, `__pycache__/`, `tmp/` | 새 PC에서 재생성 가능 | 가상환경·캐시·PDF 미리보기 등. OS·경로가 다른 PC의 가상환경은 다시 설치 |

폴더째 옮기는 방법은 **`Milkyway/` 전체 복사**입니다. 숨김 항목 `.git`·`.env`와
`runtime/handoff/`도 포함하세요. 개인 키가 들어 있는 `.env`는 본인 PC로만 안전하게
이전하고 GitHub에 올리지 않습니다. GitHub에서 새로 clone한다면 `.env`와 공개 조사
ZIP은 별도로 옮겨야 합니다. `output/`과 `week10_Milkyway_검수/`는 필요에 따라 함께 보관하세요.

**기존 대화·전략·페이퍼 기록까지 옮기려면 위 폴더 복사 외에 Docker 개인 데이터
백업·복원이 필요합니다.** 실제 DB는 `compose.personal.yaml`의 named volume
`personal-runtime`에 저장됩니다. 호스트 `Milkyway/runtime/` 폴더를 복사해도 이 볼륨은
옮겨지지 않습니다. 인계 때 만든 공개 조사 ZIP에도 개인 DB는 없습니다.
기존 앱 백업 명령·개인 백업 취급 방법은 [README.md](../README.md)의 개인용 빠른 시작과
아래 개인 설정·사용 기록 항목을 참고하세요. 초기 인계 이후 실제 개인 백업을 만들었습니다.
`backups/milkyway-20261003T121021Z-b65f42b0.zip`은 2026-10-03 21:10 KST 시점이며,
SHA 파일·summary·`backups/READ_ME_FIRST.md`와 함께 별도로 옮깁니다.

### GitHub의 코드·문서

새 작업 폴더에서 아래 브랜치를 받으면 중단 시점의 미완료 코드와 이 인계문서도 함께 받습니다.

```sh
git clone --branch codex/ai-research-workflow https://github.com/blockcoder-sj/Milkyway.git
cd Milkyway
git status --short
git log -3 --oneline
```

기존 clone이면 로컬 변경을 먼저 보존하고 해당 브랜치에서 `git pull --ff-only`를 사용하세요.
프로젝트 폴더는 `Milkyway` 하나로 관리합니다. 과거 `milkyway-local-ready` 등을 별도 개발본으로 만들지 마세요.

### 조사 원문 묶음 — 별도로 복사

현재 PC의 파일:

`runtime/handoff/milkyway-energy-handoff-20261003.zip`

코드 저장소와 별도로 다른 PC에 복사하세요. 원문 HTML·읽기 결과·수동 대조 표·조사 스크립트·선택한 검증 로그와 파일별 SHA-256 목록을 포함합니다.
API 키, `.env`, 인증 쿠키, 개인 SQLite DB, 매매 기록, Docker 볼륨은 포함하지 않습니다.
GitHub에는 이 큰 조사 묶음을 넣지 않습니다.

묶음의 `research/`에는 남은 58개 기업 중 실제 확보한 연차·분기 원문이 있습니다.
8개 기업의 연차 원문은 아직 확보하지 못했으며 원문을 만들어 채우지 않았습니다.

macOS/Linux에서 묶음을 풀고 기존 조사 스크립트 경로를 재사용하려면:

```sh
python3 -m zipfile -e milkyway-energy-handoff-20261003.zip milkyway-handoff-evidence
mkdir -p /tmp/milkyway-energy-research /tmp/milkyway-energy-equipment-review
cp -R milkyway-handoff-evidence/research/. /tmp/milkyway-energy-research/
cp -R milkyway-handoff-evidence/helpers/. /tmp/milkyway-energy-equipment-review/
```

Windows에서도 ZIP을 풀 수 있습니다. `/tmp`는 고정 요구사항이 아니며 Docker의 호스트 볼륨 경로를 실제 풀어놓은 폴더로 바꾸세요.
Docker 컨테이너 내부는 조사 데이터 `/evidence`, 스크립트 `/review`, 앱 `/app` 경로를 사용합니다.
묶음이 없어도 Git의 보고서 JSON에 원문 URL·수신일·SHA가 있어 무료 원문을 다시 받을 수 있지만 중간 읽기 결과와 로그는 다시 만들어야 합니다.

### 개인 설정·기존 사용 기록

`.env`는 Git에 없습니다. 기존 파일이 없는 새 컴퓨터에서 `.env.example`을 복사하고 사용자가 키를 직접 넣어야 합니다.
모델 기본값은 `gpt-5.4-mini`, 추론 기본값은 `none`입니다. `SEC_CONTACT_EMAIL`은 사용자 승인 이메일 `sjpeter0315@gmail.com`을 사용할 수 있습니다.
증권사 자격정보는 로컬 프로필에서 연결합니다. 원문 키를 채팅·로그·Git·인계문서에 넣지 마세요.

기존 Docker `personal-runtime`/`personal-backups` 볼륨은 Git clone이나 조사 ZIP으로 옮겨지지 않습니다.
과거 대화·전략·페이퍼 기록까지 옮기려면 **개인 백업을 별도로 복사·복원**해야 합니다.
초기 인계 이후 만든 실제 개인 백업을 복원해야 기존 사용 기록을 이어갈 수 있습니다.
새 PC의 기존 개인 데이터가 있다면 먼저 보존하고 모든 쓰기 서비스를 정지합니다.
개인 앱 이미지 준비 후, paper/backtest를 켜지 않는 복원 명령은 다음과 같습니다.

```sh
python3 deploy/local_tools.py restore backups/milkyway-20261003T121021Z-b65f42b0.zip \
  --start-services app personal-data market-data backup
```

이 도구는 현재 데이터가 있으면 사전 백업을 만들며, 복원 실패 시 서비스를 정지 상태로 둡니다.
백업 시점 이후 원본 PC에서 생긴 기록은 이 ZIP에 없습니다.

## 3. 검증된 버전만 실행하는 방법

필요 도구는 Git과 Docker Compose입니다. 아래 명령은 새 clone의 검증된 커밋을 실행하는 선택지입니다.
그 이후 저장본을 완료했다고 판단하고 곧바로 배포하지 마세요.

```sh
git switch --detach dd0b8eae3a06bd5d5b183a1d18f376724bb6a18a
cp .env.example .env
```

이미 `.env`가 있으면 덮어쓰지 마세요. 사용자가 키를 입력한 뒤 최소 개인 로컬 서비스를 실행합니다.

```sh
docker compose -f compose.personal.yaml up -d --build app personal-data market-data backup
```

브라우저는 `http://localhost:8080` 하나만 열면 됩니다. 로그인은 개인 로컬 모드에서 스킵 가능합니다.
Supabase는 이 개인 로컬 실행에 필요하지 않습니다.

이 PC에서는 RAM 부담 때문에 `app`, `personal-data`, `market-data`, `backup` 4개만 유지합니다.
`paper-worker`와 `backtest-worker`는 중단 상태입니다. 전체 Compose를 조건 없이 올려 worker를 모두 켜지 마세요.
실제 페이퍼 실행이 필요하면 사용자의 재개 범위에 맞춰 별도로 시작하고 증권사 시세 상태를 확인해야 합니다.
worker 중단 때문에 `/health/ready`가 503일 수 있으며 이를 데이터 검증 완료나 주문 장애로 단정하지 마세요.

미완료 개발을 다시 이어갈 때는 작업 브랜치로 돌아옵니다.

```sh
git switch codex/ai-research-workflow
```

새 컴퓨터의 Docker 이미지·IP·시세·현재 상태는 다시 확인해야 합니다.
기존 이미지 SHA는 이전 PC에서 검증한 식별자이며 새 PC에서 같은 이미지가 이미 있다고 가정하지 마세요.
토스 허용 IP는 새 네트워크의 공인 IP에 영향을 받습니다. 사용자에게 키·계정 재입력이나 IP 등록이 필요한 경우 실제 실패 원인을 확인해 알려주세요.

## 4. 중단 직전 미완료 변경 — 다음 작업의 시작점

대상 15개:

`BSM CRT DMLP KRP NRP NRT PBT SBR TPL VNOM CKX MNR MXC LB PNRG`

| 파일 | 현재 상태·다음 작업 |
|---|---|
| `cloud_app/company_energy_land.py` | 15개 한국어 요약·제품·현재 계약 참고·직접 역할·관련 기업 프로필·관계 초안 작성. 법인 동일성·날짜·최근 상태·문구를 직접 재검토할 것 |
| `cloud_app/company_energy_land_revenue.py` | 정확한 issuer/CIK/원문/FY 범위의 매출 좌표·임대/파생상품/처분손익 처리 추가. 마지막 추가 이후 원문 재파싱·회귀검증 미실행 |
| `cloud_app/company_energy_land_tables.py` | CRT/NRT/PBT/SBR 비인라인 표의 수동 대조 값. XBRL이라고 표시하지 않음. 실제 표·앵커·스키마·멱등성 검증 미완료 |
| `cloud_app/company_energy_revenue.py` | land 매출 adapter 연결. 변경분 전체 테스트·성능·보안 검토 미완료 |
| `cloud_app/company_energy_reports.json` | 해당 15개의 실제 연차·분기 30개 수신 메타데이터 추가. 새 adapter 결과를 `revenue_mix`에 저장하는 작업 미완료 |
| `cloud_app/company_research_catalog.py` | **land PUBLIC/PRIVATE/EDGES/COMMON_CONTEXT 미연결**. 연결해야 화면/그래프에 나타남 |
| `cloud_app/energy_issuers.json` | 해당 15개는 아직 `pending` 탐색 그룹. 사업 구조에 맞춰 그룹 배치해야 함 |

중단 직전 결과 파일 `land-royalty-revenue.json`은 **마지막 추가 전**의 11개 인라인 기업 54개 행입니다.
그 뒤 BSM/KRP 파생상품 및 PNRG 기타/처분손익을 추가했으므로 이 JSON을 최신 검증 결과로 복사하지 마세요.
4개 비인라인 신탁의 수입 표는 별도 코드에 있으며 아직 실제 전체 API 응답 검증을 하지 않았습니다.
이 15개를 155개에 더해 “170개 완료”라고 보고하지 마세요.

다음 순서:

1. 중단 시점 diff와 원문을 대조해 법인명·시점·관계 방향·익명 정보 처리·표 금액을 검토합니다.
2. 최신 adapter로 실제 원문을 재파싱하고 매출 자료를 REPORTS와 편집 자료에 연결합니다.
3. 카탈로그·관계 ID·탐색 그룹을 연결합니다. 기존 WBI·Cawley 프로필을 재사용하고 동일 법인을 중복 등록하지 않습니다.
4. 원문 수신 메타데이터·schema·멱등성·부분 구성·관계 역방향·빈 캐시 응답 회귀검증을 추가합니다.
5. 기존 전체 테스트·호스트 Node 검사·원문 값 대조·단일 CPU/512MiB 성능 확인·실제 HTTP를 순서대로 실행합니다.
6. 직접 코드·변경 범위 보안 검토, 문서·완료 범위 기록, 커밋·푸시, 검증한 app만 로컬 반영합니다.
7. 아래 43개와 전체 깊이·현재성·GICS/탐색 범위·출처·화면 검토를 이어갑니다.

## 5. 조사에서 이미 확인한 주의점

- NRT FY2025는 2024-11-01~2025-10-31입니다. 원문 사업 표의 제품·지역·운영사별 합계 8,649,904 USD와 수취액 표 8,650,094는 190 차이가 있습니다. 보정 항목을 만들지 않습니다.
- PBT 운영 Texas Royalties 11,555,301 + 실제 합의금 4,500,000은 수입 표 16,055,300과 1 USD 차이가 있습니다. Waddell 운영 수입 0을 신탁 전체 수입 0으로 표시하지 않습니다.
- PBT 2026-07-28 New PBT 결합은 조건부 제안입니다. 현재 초안은 8월 공시를 인용하며 **9월18일 최신 공식 배포문 추가 읽기·반영은 아직 하지 않았습니다**.
- CRT/PBT/SBR의 신탁 분배 가능 수입과 기업 GAAP 손익·현금흐름을 구분합니다. 엄격한 financial archive schema에 가짜 XBRL을 넣지 않습니다.
- NRP Sisecam Wyoming 자체 판매 529,382,000 USD는 49% 비지배 JV 전체 금액입니다. NRP 연결 매출에 더하지 않습니다.
- LB 상품×특수관계자 여부의 두 축을 보존합니다. WaterBridge는 기존 WBI이며 LB가 소유한 자회사가 아닙니다. 인근 생산사라는 이유만으로 계약 고객으로 만들지 않습니다.
- TPL 고객 그림 실제 수신·시각 확인: OXY 19% / CVX 11% / COP 10%, 2025 전사 매출 기준. 이사회 이력·타사 소유 비율을 고객 관계로 만들지 않습니다.
- TPL Orla는 2026 Q2 건설 완료·시운전이며 대규모 상업 확장 완료가 아닙니다. Kilby는 Chevron 계열 토지·용수 개발 약정입니다.
- MNR 2025-09-16 SIMCOE LLC·Simlog LLC 취득을 2026-04-06 8-K에서 확인했습니다. 매도 법인 Simlog Inc.와 취득 대상 LLC를 합치지 않습니다. CRT Simcoe와 공유 ID는 법인 동일성을 재검토합니다.
- BSM Aethon의 14%는 2025 석유·가스 수입, Exxon 계열 13%는 2024입니다. Revenant 6→4 유정 약정 수정·반환 면적과 실제/계획 유정을 구분합니다.
- PNRG 제품 185,909,000 + 실제 기타 수입 1,536,000 + 처분손익 1,607,000 = 189,052,000입니다. 원문 태그와 앵커를 확보했습니다.
- 관계 비교 peers는 사업 범위를 대조한 추론으로 표시하며 공시가 실명 경쟁사로 지목했다는 주장과 구분합니다.
- 익명 구매자·미공개 공급 계약·제품 점유율은 추정해서 채우지 않습니다. 공개 자료의 정보 한계와 수집 실패를 구분합니다.

## 6. 나머지 기업과 전체 검토

현재 15개 반영·검증 후에도 남는 43개:

`AMEN APC ARLP BDCO BTU CLB CLNE CNR EE EROK FET FGPR FTW HMH HOS IEP INVX NC NE NESR NEXT NFE NFG NGS NUAI NUCL OII OIS RIG RSRV SDRL SEI SMC SMHI SUNC TBN TDW UNTC VAL VG VTOL WHK XPRO`

그중 연차 원문 미확보 8개:

`AMEN EROK FTW HMH NUCL UNTC WHK XPRO`

공식 IR·상장 이력·실제 SEC 공시를 확인해야 합니다. 조회 실패를 근거로 공시 기간·CIK·문서를 만들어 넣지 마세요.
중요 기업의 사업·매출·제품·투입 비용·고객/공급/협력·경쟁·관련사·최근 거래를 사용자가 이해할 수 있게 한국어로 편집해야 합니다.
원문을 길게 나열하거나 위키피디아 내용을 가져오는 작업은 사용자가 명시적으로 원하지 않습니다.
모든 기업을 채우는 것과 섹터 전체 깊이 검토가 끝나는 것은 별도 단계입니다.

## 7. 이미 끝낸 검증의 실제 기록

마지막 shipping 배포 기준이며 현재 미완료 land 변경의 검사 결과가 아닙니다.

- 전체 Python: 실제 703개 / 79.358초 통과, Node 부재로 18개 skip.
- 호스트 Node 관련 9개 모듈: 실제 21개 / 1.416초 통과, 위 skip 범위 검사.
- 패키징한 app/test 소스 236개 SHA 일치. 실제 원문 매출 69개 행 대조.
- 오프라인 512MiB·1 CPU: seed 1,001개 / 4.816초, SQLite quick_check 정상, 최대 RSS 67.7MiB.
- p95: 기업 목록 .745ms / KNOP 병합 1.445ms / 개별 상세 10.582ms.
- 로컬 실제 HTTP: shipping 16개·관계 상대 4개·기존 기업 6개 200 확인, 기간·금액·역방향 이동 검증.
- BWLP/RBNE는 213개 roster 외 기업이므로 섹터 roster URL 404는 정상. 실제 entity ID 상세 URL은 200.
- app만 재생성해 healthy 확인. 4개 서비스·개인 데이터 유지. paper/backtest 중단 때문에 ready 503 기록.
- Chrome 기존 Energy 탭은 debugger unattached. **실제 화면 검토는 미완료**이며 관련 없는 사용자 대학 창을 건드리지 않았습니다.
- CodeRabbit·새 agent·유료 자료·추가 AI 호출은 사용하지 않았습니다. scoped 직접 변경 검토만 했으며 전체 보안 재감사·새 의존성 재검증·OCI/KMS 성공을 주장하지 않습니다.

## 8. 지속되는 사용자 지침

- CodeRabbit 전면 금지: CLI·API·봇·확장·스킬·체험도 금지합니다. 직접 소스와 기존 검증 도구를 사용합니다.
- 실제 AI API 호출은 사용자 승인 필요. 이전 5회 승인을 무제한 승인으로 해석하지 않습니다. 이번 Energy 조사·인계에서 추가 호출 0회입니다.
- 무료 공식 공시·기업 IR·정부/신뢰할 수 있는 무료 자료만 사용합니다. Wikipedia는 기업 정보 출처로 사용하지 않습니다.
- 한국어로 필요한 정보를 정리하고 출처·기준일을 연결합니다. 계약 상태·고객/운영사·권리 소유자를 구분합니다.
- 완료 마일스톤은 기능·성능·직접 코드·보안 검토 후 커밋·GitHub 푸시를 수행하고 실제 한 검사만 보고합니다.
- RAM을 위해 브라우저 탭 하나 재사용, 무거운 검증 순차 실행, 임시 컨테이너는 `--rm --network none --memory 512m --cpus 1`로 제한합니다.
- 개인 DB·runtime·Docker 볼륨·사용자 앱/탭을 보존합니다. 기존 대학 Chrome 창과 별도 8766 연구 앱은 사용자 소유 작업입니다.
- 개인 로컬 사용과 공개 다중 사용자 배포를 구분합니다. 공개 보안/배포 작업을 재개한다면 `SECURITY_REMEDIATION_STATUS.md` 전체를 읽고 그 검증 조건을 지킵니다.

## 9. 새 대화에서 전달할 재개 문구

> Milkyway 작업을 이어서 진행해. HANDOFF.md와 docs/HANDOFF_OTHER_COMPUTER.md, docs/WORK_CONTEXT.md의 마지막 기록, AGENTS.md를 먼저 읽어. 검증된 shipping 커밋 이후 land 15개는 미완료 저장본이야. CodeRabbit 사용 금지, AI API 추가 사용은 승인받고, 무료 공식 자료만 사용해. 미국 Energy 전체 기업과 관계망·가독성·현재성 검토까지 이어가고 완료 마일스톤마다 검토·커밋·푸시해. 조사 ZIP도 복사해뒀으면 그 원문을 활용해.
