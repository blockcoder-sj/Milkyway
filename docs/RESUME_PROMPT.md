# 재시작 후 붙여 넣을 프롬프트

**2026-10-04 갱신:** 아래는 재시작 당시의 복원 프롬프트다. 이후 사용자가 재개했고
복원·개발 환경·개인 앱 실행과 213개 Energy 조사·탐색 검수를 완료했다.
현재는 HANDOFF.md와 [최종 검토](ENERGY_FINAL_REVIEW_20261004.md), WORK_CONTEXT의
마지막 기록을 먼저 읽는다. 이 과거 프롬프트로 복원된 볼륨을 다시 덮어쓰지 않는다.

현재 상태에서 새 대화에 붙여 넣을 문구:

```text
Milkyway 작업 맥락을 확인해.
폴더는 /Users/kimseungzoo/Developer/4.Milkyway,
GitHub 브랜치는 codex/ai-research-workflow야.
AGENTS.md, HANDOFF.md, docs/HANDOFF_OTHER_COMPUTER.md,
docs/ENERGY_FINAL_REVIEW_20261004.md, docs/WORK_CONTEXT.md 마지막 항목을 읽어.
10월 4일 새 PC 복원·개발 환경·앱 실행과 확정한 Energy 기업213개 조사를 완료했어.
현재 Git/앱/볼륨 상태를 확인하고 기존 개인 데이터·백업·runtime을 보존해.
과거 재시작 프롬프트의 복원 명령을 이미 복원된 볼륨에 다시 실행하지 마.
새 작업은 내가 요청한 범위로 진행하고, 기존 Chrome 탭 하나를 재사용해.
마일스톤마다 직접 검토·검증·커밋·푸시 후 범위 내 다음 작업을 계속해.
CodeRabbit과 새 agent는 사용하지 말고 실제 AI provider 호출은 승인받아.
브로커 피드 실패·중단 worker의 readiness503과 공개 OCI/KMS NO-GO는
정적 연구의 완료와 구분해. 실제 성공 증거 없이 실운용 성공을 주장하지 마.
```

## 보존한 10월 3일 재시작 프롬프트

아래 문구는 당시 기록이며 현재 복원 지시로 사용하지 않는다.

```text
컴퓨터 재시작을 마쳤으니 Milkyway 작업을 이어서 진행해.
작업 폴더는 /Users/kimseungzoo/Developer/4.Milkyway,
GitHub 브랜치는 codex/ai-research-workflow야.

AGENTS.md, HANDOFF.md, docs/RESTART_HANDOFF_20261003.md,
docs/HANDOFF_OTHER_COMPUTER.md, docs/WORK_CONTEXT.md의 마지막 기록을 먼저 읽어.
백업·로컬 실행 전 SECURITY_REMEDIATION_STATUS.md도 전체 읽어.

코드와 .git은 복구했고 .env와 개인 백업·조사 ZIP은 이미 이 폴더에 있어.
개인 백업과 조사 ZIP의 SHA는 확인했지만 실제 Docker 볼륨 복원과 앱 시작은 아직 안 했어.
검증된 shipping 소스로 milkyway-personal:local 이미지를 빌드해 뒀으니 현재 상태를 재확인해.
개인 백업 backups/milkyway-20261003T121021Z-b65f42b0.zip을 검증하고 새 PC의 개인 볼륨에 복원해.
기존 데이터가 있으면 먼저 보존하고, 복원 후 app, personal-data, market-data, backup 네 개만 시작해.
deploy/local_tools.py의 --start-services 옵션을 사용하고 paper/backtest는 꺼 둬.
10/3 21:10 백업 시점의 기존 대화·전략·페이퍼 기록과 DB 무결성을 확인해.

그다음 미완료 land/royalty 15개부터 원문 대조·매출 재파싱·카탈로그/관계/탐색 그룹 연결과 검증을 진행해.
조사 ZIP을 활용하고 남은 Energy 기업 및 전체 깊이·현재성·분류·관계망·가독성·화면 검토까지 이어가.
land 15개 저장본이나 155개 편집 자료를 전체 완료로 보고하지 마.

마일스톤마다 기능·성능·직접 코드·변경 범위 보안 검토와 검증을 마친 뒤
공개 문서를 갱신하고 커밋·GitHub 푸시해. 마일스톤에서는 멈추거나 계속할지 묻지 말고 다음 작업을 이어가.
실제 차단 사유나 새 승인이 필요한 작업만 구체적으로 알려줘.
CodeRabbit과 새 agent는 사용하지 말고, 추가 실제 AI API 호출은 승인받아.
무료 공식 자료만 사용하고 Wikipedia는 쓰지 마.
.env, 키, 개인 DB, 백업 ZIP은 GitHub에 올리거나 채팅/로그에 출력하지 마.
현재 데이터·다른 프로젝트·사용자 앱/탭을 보존하고 무거운 검증은 순차 실행해.
```
