# 새 PC 개발 환경 복구·검증

2026-10-04, Asia/Seoul. 사용자가 재시작 중단을 해제하고 Energy 전체 작업을
계속하도록 요청했다. Chrome은 사용자가 열어 둔 탭 하나를 재사용한다.

- 현재 경로 `/Users/kimseungzoo/Developer/4.Milkyway`, 브랜치
  `codex/ai-research-workflow`. 시작 시 로컬과 실제 GitHub ref가 모두
  `8f10c830107ffadf7cf8a56c637c0955748dd584`였으며 작업 트리는 깨끗했다.
  코드·Git 다운로드는 완료 상태였다.
- Docker Desktop 엔진 29.7.2와 기존 검증된 shipping 이미지
  `fd9bdb59eeada9f5297ea72086a848b3e8a5b67d06bddd7c273100fdb49d889f`를 확인했다.
  현재 미완료 land 소스는 배포하지 않았다. 호스트 Node 24.20.0이 있다.
- 새 PC에 `milkyway-personal` 대상 볼륨·컨테이너가 없는 것을 확인한 뒤,
  인계된 개인 ZIP 전체 SHA를 다시 확인하고 선택 서비스 복원 명령을 실행했다.
  도구가 모든 멤버 checksum과 SQLite 무결성을 검증해 3,972개 파일을 복원했다.
  기존 다른 프로젝트의 컨테이너·볼륨과 원본 ZIP·환경 파일은 보존했다.
- 복원 후 개인 DB와 기업 관계 DB의 `integrity_check`·`foreign_key_check` 정상.
  대화·전략·버전·실험·페이퍼 관련 13개 테이블의 전체 행을 비공개로 해시 대조해
  백업과 정확히 일치했다. 기업 관계 DB의 모든 테이블 행 수도 백업과 일치했다.
  계정·원장 내용·키를 공개 문서나 Git에 기록하지 않았다.
- `app`, `personal-data`, `market-data`, `backup` 네 서비스만 실행한다.
  app healthy, 실제 `/health/startup` 200. `/health/ready` 503의 false 항목은
  중단을 유지한 paper/backtest worker이며 DB·dataset·data gate·personal-data는 true다.
  거래 운용·현재 증권사 인증 성공을 이 결과로 주장하지 않는다.
- 공개 조사 ZIP도 전체 SHA·CRC·248개 payload SHA/크기를 확인해
  Git 제외 경로 `runtime/handoff/evidence-20261004/`에 풀었다.
- 네트워크 없는 512MiB·1 CPU 임시 컨테이너에서 복원 관련 13개 검사
  (`tests.test_local_tools`, `tests.test_local_ops`)가 0.126초에 모두 통과했다.
  임시 컨테이너는 자동 제거했다. 기존 선택 서비스 복원 코드와 ZIP 경로·무결성·
  권한·실패 시 정지 처리 직접 검토를 수행했다.
- 실제 Chrome 기존 탭에서 개인 앱 → 시장 → Energy를 클릭해 진입했다.
  산업 설명과 213개 조사 목록·검색·사업 그룹·페이지 이동이 렌더되는 것을 확인했다.
  Energy 전 기업의 시각 검토가 끝났다는 뜻은 아니다.

복구 검증 로그와 비공개 기록 대조 결과는 `runtime/verification-20261004/`에
보존한다. `.env`, `backups/`, `runtime/`의 Git 제외를 확인했다.
전체 회귀·새 보안 감사·OCI/KMS·유료 AI 호출은 수행하지 않았다.

다음 작업은 land/royalty 15개의 원문·기간·법인·금액 대조, 최신 매출 재파싱,
카탈로그·관계·사업 그룹 통합이다. 그다음 남은 43개와 전체 깊이·현재성·분류·
관계·한국어 가독성·Chrome 검토를 계속한다. 155개 편집 자료는 완료 기업 수가
아니다. 마일스톤마다 검증·검토·커밋·푸시 후 다음 작업을 계속한다.
