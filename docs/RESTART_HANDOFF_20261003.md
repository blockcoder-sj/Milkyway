# 새 PC 재시작 인계

**아래는 2026-10-03 중단 당시 기록이다. 사용자가 10월 4일 재개했고 데이터 복원·
앱 실행·Energy 213개 범위의 작업을 마쳤다. 현재 상태는
[최종 검토](ENERGY_FINAL_REVIEW_20261004.md)와 WORK_CONTEXT.md의 마지막 항목을 읽는다.
이미 복원한 볼륨에 아래 과거 복원 명령을 다시 실행하지 않는다.**

기록: 2026-10-03 23:26 KST 이후. 사용자 요청: 작업을 잠시 중단하고 컴퓨터를
껐다 켠 뒤 이어갈 수 있도록 인계문서와 프롬프트를 남긴다.

**현재 작업은 일시 중단이다. 사용자가 재개하면 다음 순서로 진행한다.**
마일스톤은 검토·검증·커밋·푸시 지점이다. 재개 이후 마일스톤마다 작업 종료나
재개 확인을 요청하지 않고 다음 범위 내 작업을 이어간다.

## 작업 위치와 Git

- 현재 프로젝트: `/Users/kimseungzoo/Developer/4.Milkyway`
- 저장소: `https://github.com/blockcoder-sj/Milkyway.git`
- 브랜치: `codex/ai-research-workflow`
- 이 PC에서 처음 확인한 원격 HEAD: `8b16fbd857dad15ca039312efb0092b161154f83`
- 마지막으로 앱 기능 검증·배포를 마친 소스: `dd0b8eae3a06bd5d5b183a1d18f376724bb6a18a`
- 이 저장 기록의 최신 커밋은 재시작 후 `git log -3 --oneline`과 원격 ref로 확인한다.

이 PC의 초기 폴더에는 `.env`, `backups/`, `docs/`, `runtime/`이 있었으나
앱 소스와 `.git`은 없었다. 지정 브랜치를 새로 clone한 뒤 기존 파일을 덮어쓰지
않고 현재 폴더에 합쳐 소스와 Git 기록을 복구했다. 이전 PC에서 가져온
`docs/WORK_CONTEXT.md`의 마지막 개인 백업 완료 기록도 보존했다.

## 지금까지 실제로 끝낸 작업

- GitHub 브랜치 접근과 로컬 Git 연결 확인.
- `.env`, 개인 백업, 공개 조사 ZIP 보존 및 Git 제외 확인.
- 개인 백업과 공개 조사 ZIP의 전체 SHA-256을 이 PC에서 재검증: 둘 다 일치.
- Docker Desktop 시작 및 엔진 `29.7.2` 응답 확인.
- 검증된 shipping 소스를 별도 임시 폴더로 추출해 개인 앱 이미지 빌드 완료.
  현재 태그: `milkyway-personal:local`.
  이미지 ID: `sha256:fd9bdb59eeada9f5297ea72086a848b3e8a5b67d06bddd7c273100fdb49d889f`.
  이전 PC와 CPU 환경 등이 다르므로 이전 이미지 SHA와 같다고 주장하지 않는다.
- `deploy/local_tools.py`에 복원 후 선택한 서비스만 시작하는
  `--start-services` 옵션 추가. 복원 전 정지 대상에 `market-details`와
  `company-data`도 포함해 모든 쓰기 서비스를 정지하도록 했다.
- 중단 요청 전 `python3 -m unittest tests.test_local_tools tests.test_local_ops -v`:
  **13개 통과 / 0.196초**. 선택 서비스·실패 시 미재시작·기존 기본 동작·백업
  무결성·기존 기록 보존 등의 범위를 확인했다. 실제 Docker 복원 성공 증거는 아니다.
- 현재 프로젝트에서 `docker compose -f compose.personal.yaml config --quiet` 통과.
- 변경 소스 직접 검토와 `git diff --check` 통과. 전체 회귀·성능·보안 재감사와
  현재 변경의 CI 성공은 아직 주장하지 않는다.

## 아직 하지 않은 작업

**개인 백업의 실제 Docker 볼륨 복원은 하지 않았다. 앱과 데이터 서비스도 시작하지 않았다.**
현재 대화·전략·페이퍼 기록은 백업 ZIP 안에 보존된 상태다.
23:26 KST 점검에서 `milkyway-personal` 프로젝트의 실행 컨테이너와 해당 이름의
볼륨은 없었다. 이 PC에 있는 다른 프로젝트 컨테이너·볼륨은 보존했다.
재시작 뒤에는 상태가 바뀔 수 있으므로 다시 확인한다.

## 개인 데이터와 공개 조사 자료

개인 백업:

- `backups/milkyway-20261003T121021Z-b65f42b0.zip`
- 백업 시점: **2026-10-03 21:10:30 KST**
- 크기: 131,036,961 bytes
- SHA-256: `8a27d491bc4dfa6de8ca2634ba4d6e66e43f0b49be64eb4ff7c325c19d76d39c`
- 같은 이름의 `.zip.sha256`, `.summary.json`, `backups/READ_ME_FIRST.md`도 보존.

공개 조사 ZIP:

- `runtime/handoff/milkyway-energy-handoff-20261003.zip`
- 크기: 36,432,881 bytes
- SHA-256: `c128c9da6d699a0ee18500cb9d25815cebafe23ac56603ca14d7aa3331d9d833`

`.env`와 개인 백업은 GitHub에 없다. 이 파일들을 현재 PC에 그대로 보관한다.
개인 ZIP에는 복호화용 로컬 키도 들어 있으며 ZIP 자체는 암호화되어 있지 않다.
원문 키·DB 내용은 채팅·로그·Git에 출력하지 않는다. 21:10 이후 원본 PC에서
새로 생성한 사용 기록은 이 백업에 포함되지 않는다.

## 재시작 후 진행 순서

1. 현재 폴더에서 `AGENTS.md`, `HANDOFF.md`, 이 문서,
   `docs/HANDOFF_OTHER_COMPUTER.md`, `docs/WORK_CONTEXT.md`의 마지막 기록을 읽는다.
   백업·로컬 실행 전 `SECURITY_REMEDIATION_STATUS.md`도 전체 읽는다.
2. `git status --short --branch`, `git log -3 --oneline`, `git remote -v`를 확인한다.
   현재 폴더를 사용하고 별도 앱 clone을 만들지 않는다. 로컬 변경을 먼저 보존한다.
3. Docker Desktop을 열고 `docker version`, 프로젝트 컨테이너·볼륨 및 이미지 태그를
   확인한다. 기존 개인 데이터가 생겼다면 덮어쓰지 말고 먼저 보존한다.
4. ZIP SHA를 다시 확인하고 복원한다. 아래 명령은 개인 DB를 대상으로 실제 복원한다.
   기본 복원 명령만 사용하면 모든 worker가 켜지므로 선택 서비스 옵션을 사용한다.

   ```sh
   cd /Users/kimseungzoo/Developer/4.Milkyway
   (cd backups && shasum -a 256 -c milkyway-20261003T121021Z-b65f42b0.zip.sha256)
   python3 deploy/local_tools.py restore backups/milkyway-20261003T121021Z-b65f42b0.zip \
     --start-services app personal-data market-data backup
   ```

   이미지가 없으면 검증된 shipping 커밋을 별도 빌드 컨텍스트로 추출해 빌드한다.
   미완료 land 작업 트리로 앱을 먼저 빌드·배포하지 않는다.
5. 복원 결과·개인 DB 및 기업 관계 DB 무결성·기존 기록 보존을 확인한다. 네 서비스의
   상태와 `http://localhost:8080/health/startup`, 실제 앱 접근을 확인한다.
   paper/backtest는 정지 상태를 유지한다. 이를 이유로 ready가 503이면 원인을 구별한다.
6. 조사 ZIP을 활용해 미완료 land/royalty 15개를 먼저 대조·통합·검증한다.
   최신 매출 adapter 재파싱, 보고서 `revenue_mix`, 카탈로그·관계 ID·탐색 그룹 연결,
   원문 금액/기간/법인 대조와 회귀검증부터 진행한다.
7. 남은 43개 및 Energy 전체 깊이·현재성·분류·관계·화면 검토를 이어간다.
   현재는 213개 중 155개 주요 편집 자료가 있는 상태이며, land 15개나 섹터 전체를
   완료로 세지 않는다. 세부 목록·주의점은 기존 다른 컴퓨터 인계문서에 있다.

## 계속 적용할 사용자 지침

- 마일스톤마다 기능·성능·직접 코드·변경 범위 보안 검토와 검증, 공개 문서 갱신,
  커밋·GitHub 푸시를 수행하고 다음 작업을 계속한다. 실제로 한 검사만 보고한다.
- CodeRabbit 전면 금지. 새 agent는 사용하지 않는다.
- 추가 실제 AI API 호출은 별도 사용자 승인 필요. 이 재개 준비에서 호출 0회.
- 무료 공식 공시·기업 IR·정부 자료를 사용하며 Wikipedia는 기업 출처로 사용하지 않는다.
- 무거운 검증은 순차 실행하고 기존 개인 데이터·다른 프로젝트·사용자 앱/탭을 보존한다.
- 공개 다중 사용자 배포는 별도 승인·보안 조건이 있는 범위다. 이번 작업은 개인 PC 재개다.

재개 문구: [RESUME_PROMPT.md](RESUME_PROMPT.md).
