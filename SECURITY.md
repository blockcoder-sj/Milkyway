# Milkyway 보안 정책

Milkyway는 동아리용 페이퍼 트레이딩 서비스이며 회원의 AI·시세 공급자 API 키를
처리한다. 실거래 주문은 이 웹 플랫폼의 범위가 아니다.

## 비공개 제보

- GitHub Security Advisory: <https://github.com/blockcoder-sj/Milkyway/security/advisories/new>
- 저장소 소유자에게 비공개로 연락

API 키, 세션, 개인정보 또는 재현 가능한 공격 코드는 공개 이슈에 게시하지 않는다.
제보에는 영향받는 파일·경로, 최소 재현 절차, 영향도와 가능한 완화책을 포함한다.

## 보안 경계

- AI가 반환한 Python이나 셸 코드는 실행하지 않는다. 허용 목록 기반
  `StrategySpec` JSON만 저장하고 공통 엔진으로 실행한다.
- 브라우저 세션은 서명 쿠키, 서버측 폐기 가능한 세션 레코드, HttpOnly,
  SameSite=Strict, production Secure 속성과 CSRF 헤더를 함께 사용한다.
- production 회원 API 키는 OCI Vault의 AI용·시세용 독립 대칭 키로 암호화하고
  사용자·공급자·환경·필드를 associated data로 인증 결합한다. 별도 OCI 인스턴스의
  provider-operation broker만 KMS와 공급자 자격증명에 접근한다. 공개 앱과 paper-worker는
  역할별 broker 토큰만 가지며 raw decrypt, 임의 URL, 원문 credential/token 응답은 존재하지
  않는다. 회원 credential 평문은 broker의 승인된 공급자 요청 직전에만 메모리에 존재한다.
  development만 owner-only 로컬 v2 저장소를 쓴다.
- production은 예시 값이 아닌 독립 난수 비밀값, PostgreSQL, HTTPS 공개 URL,
  명시적 Host 허용 목록이 없으면 시작하지 않는다.
- 앱 요청 본문과 사용자별·전체 SSE 연결 수에는 상한이 있다.
- Compose는 서비스별 환경변수 허용 목록과 내부 네트워크를 사용한다.
  PostgreSQL과 worker는 공인 포트를 열지 않으며 Caddy만 80/443을 공개한다.
- 개인 KIS·토스 키로 받은 시세는 그 회원의 페이퍼 계좌에만 사용한다. 공용 시세는
  외부 표시·재배포·비표시 이용을 명시적으로 허용하는 별도 계약이 필요하다.

## 운영자 필수 사항

- `deploy/.env`는 저장소 밖의 비밀 관리 또는 서버의 mode `0600` 일반 파일로
  관리하고 절대 커밋하지 않는다.
- `SESSION_SECRET`, `CLUB_INVITE_CODE`, 데이터베이스 비밀번호는 모두 서로 다른 난수로
  만들고, production 앱에는 `AI_CREDENTIAL_SECRET`이나 `MARKET_CREDENTIAL_SECRET`을
  절대 전달하지 않는다. 역할별 broker 토큰도 서로와 다른 32자 이상 난수로 만들며 앱에는
  app token만, paper-worker에는 paper token만 전달한다.
- OCI instance principal은 **broker 인스턴스 한 대만** 포함하는 dynamic group으로 제한하고,
  서로 다른 두 credential key의 `KEY_ENCRYPT`·`KEY_DECRYPT` 권한만 부여한다. Vault
  관리·key export·삭제 권한은 런타임 identity에 부여하지 않으며 모든 KMS 호출을 OCI
  Audit에서 감시한다. 공개 앱 인스턴스는 이 dynamic group에 절대 포함하지 않는다.
- broker는 별도 VM과 HTTPS origin으로 배포하고 443 ingress를 앱 VM의 고정 IP로 제한한다.
  같은 OCI VM의 Compose 서비스 분리는 instance-principal 경계가 아니므로 production에서
  허용하지 않는다.
- TLS, 방화벽, 자동 보안 업데이트, 백업 암호화·접근 제어와 복구 시험을 유지한다.
- 인스턴스나 KMS 권한 유출 시 dynamic-group/IAM 권한을 먼저 폐기하고 OCI Audit으로
  사용 범위를 확인한 뒤 영향받은 공급자 키를 폐기한다. DB와 KMS 사용 권한이 함께
  유출됐다고 가정해 대응한다.
- 배포 전 app preflight의 `credential_broker=true`, broker preflight의 실제 두-key KMS
  round trip, 전체 테스트와 두 Compose 파일의 `config` 검증을 모두 통과시킨다.

## 범위

포함: 인증·인가·CSRF·세션 폐기, API 키 저장/복호화/로그, 사용자 데이터 격리,
전략 DSL 검증, 공통 체결·중복 체결 방지, 데이터 무결성 게이트, 배포 설정과 백업.

제외: 공급자 자체 취약점, 공급자가 허용하지 않은 시세 라이선스의 임의 확대,
단일 VM·단일 리전 장애를 포함한 외부 인프라 가용성. 제외 항목도 운영 전 별도
계약과 인프라 통제로 확인해야 한다.

Critical 제보는 가능한 즉시 초기 확인하고, 확인된 취약점은 공개 설명보다 키 폐기와
완화를 먼저 수행한다.
