# Milkyway 맥락 저장·작업 중단 인계

기록일: 2026-10-11, Asia/Seoul. 사용자 요청은 “맥락저장”, 이후
“지금은 작업 멈출거니까 … 도커 쓰거나 메모리 쓰는거 있으면 다 작업종료해서 메모리 압력좀 줄이자”다.
문서와 기억을 저장하고 요청한 Milkyway 런타임을 종료한 뒤 작업을 중단한다.
새 재개 요청 전에는 구현·자료 수집·복원·앱 시작을 진행하지 않는다.

## 최신 코드와 완료 범위

- 폴더: `/Users/kimseungzoo/Developer/4.Milkyway`
- 브랜치: `codex/ai-research-workflow`
- 마지막 구현: `f2b2608ad90cecb422e37f30273496c23f1c2fa7`
  (`Make constellation drag pan by default and add initial view reset`).
  이번 저장 전 GitHub 원격과 일치했고 작업 트리는 깨끗했다.
  이번 후속은 문서 전용 커밋이며 같은 브랜치로 푸시한다.
- 상세: [10월 5일 관계도 검토](ENERGY_CONSTELLATION_CONTROLS_REVIEW_20261005.md),
  [로컬 의미 검색·연관성 검토](ENERGY_SEMANTIC_RAG_REVIEW_20261004.md),
  [이전 세션 인계](SESSION_HANDOFF_20261004.md), `WORK_CONTEXT.md` 마지막 기록.

기업·섹터 모두 일반 왼쪽 드래그는 화면 이동, Shift+왼쪽 드래그는 3D 회전이다.
드래그 중 Shift 전환을 지원하며 2D에서는 이동한다. `처음 화면`은 원래 중심·
전체 요소·카메라·표시/검색 설정·자동 회전·크게 보기를 초기화한다.
전체 지도 복귀는 현재 표시 설정을 유지한다. 클릭하면 주요 직접 연결 최대8개를 집중 표시한다.
의미 군집을 유지하고 전체 간격을 더 줄였다. 당시 Energy7435개/8114연결 기준
평균 화면 중심 거리40.91% 축소이며 경제적 영향 크기를 계산한 수치는 아니다.

확정한 Energy213개 기업의 공개 연구 범위와 로컬 E5 의미 검색·군집·출처 기반 연관성
패널은 완료 기록을 유지한다. 무료 자료 추가 조사는 종료했다.
생성형 LLM 자유 답변·공시 전문 전수·미공개 거래/경제 노출/주가 영향 추정·
실제 브로커 운용·공개 OCI/KMS 배포는 완료했다고 주장하지 않는다.

10월 5일 검증은 frontend23개 통과, 격리 전체777개 중756통과·21건너뜀,
Chrome 기업/섹터 이동·확대·초기화 확인이다. Shift 드래그 자체는 Node pointer-event
검사로 검증했고 Chrome 재생을 주장하지 않는다. 당시 관련289개 파일 SHA가
실행 이미지와 일치했다. 이번 저장에서 코드 수정·전체 검사·UI 재검수는 수행하지 않았다.

## 10월 11일 실제 확인과 종료

중단 전 마지막 구현 HEAD/원격 일치, 실행 이미지
`sha256:d14ee901625d94043ad9fa1cdf53df37c6008b4a258cd797c20b93aca0af8887`,
app healthy·live/startup200·ready503을 확인했다. ready503은 이전 운용 조건과 구분한다.

사용자 요청에 따라 아래4개 컨테이너에 정상 종료 신호를 보냈다.

| 서비스 | 종료 전 메모리 표본 | 종료 확인 |
| --- | ---: | --- |
| app | 272MiB | exited143 |
| personal-data | 245.6MiB | exited143 |
| market-data | 269.2MiB | exited143 |
| backup | 122.8MiB | exited143 |

143은 SIGTERM 종료다. 종료 전 합계909.6MiB였으며 이후 Milkyway 실행 컨테이너는0개다.
앱 localhost8080에 연결되지 않음을 확인했다. paper/backtest는 시작하지 않았다.
컨테이너를 삭제하지 않았고 모든 컨테이너ID·마운트·Docker 볼륨 목록이 전후 일치했다.
개인 DB·`.env`·키·백업·원문 ZIP·모델·파생 인덱스를 삭제하거나 복원하지 않았다.
새 백업·데이터 전수 검사도 수행하지 않았다.

다른 프로젝트의 `fancy_app-postgres-1`이 실행 중이므로 이를 보존했고 Docker Desktop
전체는 종료하지 않았다. Chrome의 조회된 창/탭은 다른 프로젝트였고 Milkyway 탭은 없었다.
VS Code에는 다른 프로젝트와 Milkyway 창이 있으나 사용자 UI 변경이 감지되어 추가 조작을
중단했다. 현재 Codex 저장 세션의 프로세스도 강제 종료하지 않았다. 별도 Milkyway
개발 서버/로컬 모델 질의 프로세스는 확인하지 못했다. 다른 앱·프로젝트는 보존한다.
시스템 memory_pressure의 free percentage는 전후43%로 같아 전체 메모리 압력 해소나
그만큼의 실제 물리 메모리 증가를 주장하지 않는다.

로컬 보존 증거: `runtime/verification-20261011/context-stop/`의 컨테이너·볼륨 전후 기록.
이 자료와 개인 데이터는 Git에 포함하지 않는다. 새 AI 제공사 호출·보안 스캔·CodeRabbit·
하위 agent·빌드·앱 재시작은 수행하지 않았다.

## 다음 재개 순서

1. 이 문서, `AGENTS.md`, `HANDOFF.md`, `WORK_CONTEXT.md` 마지막 기록을 읽고
   실제 Git·Docker·컨테이너·볼륨 상태를 다시 확인한다. 오늘의 종료 상태는 날짜가 있는 기록이다.
2. 사용자가 앱/개발 재개를 요청했을 때만 기존 개인 런타임을 시작한다.
   Docker 엔진이 종료돼 있으면 `docker desktop start`로 먼저 시작한다.
   현재 기존4개 컨테이너를 재사용하는 명령은 아래다.

   ```sh
   docker compose -f compose.personal.yaml start app personal-data market-data backup
   ```

   기존 볼륨에 과거 백업을 다시 복원하지 않는다. paper/backtest는 별도 요청 없이 시작하지 않는다.
3. localhost8080·live/startup 및 실제 자료 상태를 확인하고 Chrome 탭 하나를 재사용한다.
   정적 연구와 brokerage readiness/공개 배포 준비를 구분한다.
4. 새로운 구현 범위는 사용자가 지정한다. 직접 검토·검증·커밋·푸시를 체크포인트로 삼되
   사용자 중단 지시를 우선한다. CodeRabbit과 새 agent를 사용하지 않는다.
   실제 AI 제공사 호출은 개별 승인이 필요하다.
