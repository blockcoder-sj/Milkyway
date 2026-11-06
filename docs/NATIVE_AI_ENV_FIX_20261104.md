# Python 실습 설치의 AI 키 파일 수정

2026-11-04. 사용자가 이미 GitHub ZIP 설치를 마친 학회원들을 위해
Docker 없이 AI 키를 적용하고 한 줄로 수정하는 방법을 요청했다.

기존 AI 모듈은 Python 실행에서도 루트 `.env`를 읽고 있었다.
`.env.example`에만 넣은 키가 적용되지 않는 것이 실제 문제였다.
기존 설치에서도 `.env.example`을 `.env`로 복사하고 재실행하면 해결된다.
Windows·Mac 한 줄 복사·실행 명령은 `AI_RESEARCH_GUIDE.md`에 기록했다.

이번 변경은 개인 로컬 모드에서 `.env`가 없을 때 `.env.example`을 대신 읽는다.
기존 `.env`는 빈 키를 포함해 우선하고 프로세스 환경변수 우선순위도 유지한다.
UTF-8 BOM과 Windows 줄바꿈을 허용하며 16KB 파일 상한과 기존 키 형식 검증을 유지한다.
파일을 수정하거나 키를 출력하지 않는다. ZIP 업데이트는 두 환경 파일과
runtime·backups·logs·가상환경을 보존한다. 요청별 AI 호출 승인 흐름은 유지한다.

검증: Python 3.14에서 `APP_ENV=development`로
`tests.test_research_env tests.test_native_update` 17개 통과, 0.027초.
첫 실행은 샌드박스가 감독 프로세스 테스트의 loopback bind를 막아 1개 실패했으며,
승인된 실행에서 같은 17개를 재실행해 모두 통과했다.
기존 `.env` 유무에 따른 한 줄 복사·실행 명령도 임시 폴더와 가짜 실행기로 확인했다.
기능·성능·직접 소스·변경 범위 보안 검토와 `git diff --check`를 완료했다.
실제 OpenAI 요청·실제 키 유효성 검증은 수행하지 않았다.
Windows·Mac CI에 같은 테스트를 추가했으며 원격 실행 결과는 별도로 확인한다.
