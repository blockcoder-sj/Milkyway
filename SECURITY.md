# Milkyway 보안 정책

Milkyway는 동아리 회원별 증권사 키와 동아리 공용 AI를 사용하는 페이퍼 트레이딩 서비스다.
실거래 주문 제출은 범위가 아니다. 공개 배포 및 실제 회원 키 입력의 허용 여부는
[SECURITY_REMEDIATION_STATUS.md](SECURITY_REMEDIATION_STATUS.md)의 증거와 gate를 따른다.

## 비공개 제보

GitHub Security Advisory 또는 저장소 소유자의 비공개 채널로 제보한다.
API 키, 세션, 개인정보와 재현 코드는 공개 이슈에 게시하지 않는다.
영향받는 경로, 최소 재현 절차와 영향도를 포함하되 실제 비밀값은 제거한다.

## 보안 경계

- AI 출력은 허용된 StrategySpec JSON만 받으며 Python/셸 코드를 실행하지 않는다.
- 별도 broker VM이 불투명 세션, 일회용 AI 허가, 제한된 worker 작업 권한을 발급한다.
  브라우저 쿠키는 HttpOnly, SameSite=Strict, Secure이며 변경 요청은 CSRF 검증을 거친다.
- DB의 고정 search_path authority 함수와 RLS는 독립 발급된 세션·작업 권한을 확인한다.
  공개 앱은 password hash, 키 암호문, issuer 테이블에 접근하지 못한다. worker는 승인된
  회원·계좌·전략·종목 범위만 사용한다. 호출자가 보내는 회원 ID는 인증 근거가 아니다.
- 개인 키는 broker의 별도 HTTPS origin에서 직접 입력한다. broker만 OCI KMS로 암복호화하고,
  owner/provider/environment/field 결합을 검증한다. raw key와 provider access token은
  앱·worker 응답에 포함하지 않는다. 오류·요청 검증 응답에도 입력 키를 반사하지 않는다.
- 공용 원격 AI 키는 broker instance principal이 OCI Vault CURRENT secret에서 읽는다.
  원격 provider 키의 평문 환경변수·파일 전달은 production에서 거부한다.
- runtime 서비스별 DB 역할과 broker 토큰은 독립적이다. 마이그레이션/authority DSN은
  앱·worker에 주지 않는다. VMroot, Docker 관리자와 DB owner는 신뢰하는 운영자다.
- 요청 본문, 비밀번호 계산, DB 풀, provider 처리, 작업 대기열, 데이터 파일과 결과 보존에
  상한을 적용한다. 시세/인증 I/O는 별도 프로세스의 강제 기한으로 느린 응답을 종료한다.
- PostgreSQL은 사설 IP에서 TLS 1.3만 받고 클라이언트는 CA와 서버 이름을 검증한다.
  OCI ingress는 broker 사설 IP만 허용한다. 8000/8010은 공개하지 않는다.
- 데이터 승격은 scheduler와 분리하고 검토한 동일 세대를 양 VM에 읽기 전용으로 둔다.

## 운영자 필수 사항

- 실제 env 파일은 mode 0600, 서버 인증서 private key와 선택적 local-AI 파일은 전용 UID의
  owner-only 권한으로 관리한다. CA private key와 백업 private key는 격리된 관리 호스트에 둔다.
- 7개 DB 비밀번호, 3개 역할 토큰, 앱 SESSION_SECRET과 AUTHORITY_SESSION_SECRET을 모두
  서로 다른 32자 이상 난수로 만든다. 초대는 broker authority 환경에서 이메일별 발급한다.
- broker VM만 두 credential key의 dynamic group에 넣고 필요한 암복호화·secret 읽기 권한만
  부여한다. key 관리/export/삭제 권한을 런타임에 주지 않는다. 앱 VM은 두 키 모두 거부되어야 한다.
- 두 VM의 실제 allow/deny 및 OCI Audit, 보존·경보·알림 증거 없이 KMS 성공을 주장하지 않는다.
  회원 키 모드에 이 증거는 필수다. 같은 VM의 컨테이너 분리는 이 경계를 충족하지 않는다.
- broker HTTPS는 동아리 브라우저와 앱이 접근하도록 구성하고 `/credentials`의 별도 origin을
  유지한다. provider 연결 성공과 40명 부하·회전·장애 복구는 실제 환경에서 검증한다.
- 배포 파일·의존성·OS 패키지는 고정 revision/digest/hash/signed snapshot으로 관리한다.
  보안 업데이트는 새 고정값 검토, clean build, audit/SBOM, 회귀 검증을 거쳐 반영한다.
- 백업 암호화·접근 제어·복구 시험을 유지한다. 기존 데이터와 볼륨을 임의 삭제하지 않는다.
- 유출 시 IAM/세션/작업 권한과 공급자 키를 폐기하고 Audit으로 영향 범위를 조사한다.
- sealed whole-repository scan 및 실제 OCI gate가 모두 통과하기 전 공개 배포·실제 키 입력은 금지한다.

## 범위

인증·인가·CSRF·세션 폐기, 키 저장과 로그, DB 사용자 격리, 전략 DSL과 체결 원장,
데이터 무결성, 공급망·배포·백업을 포함한다. 공급자 자체 취약점과 단일 리전 장애 등
외부 인프라는 별도 운영 검증 대상이다. 공급자의 허용 범위는 프로그램의 기술적 격리만으로
입증되지 않으며 실제 서비스 사용 조건에 맞춰 확인한다.
# Personal local installation scope (2026-09-26)

`compose.personal.yaml` is a single-owner, loopback-only installation explicitly
requested for the club exercise. Each member keeps their own credentials and
ledger on their own trusted PC. Local AES-GCM keys and session secrets persist
in its private runtime volume; this is not an independent KMS trust boundary.
The app uses quote-only KIS/Toss clients and never places brokerage orders.
Backups include both encrypted credential rows and local decryption roots and
must be treated as private secrets. Do not upload them to GitHub or share them.

This local mode cannot run as `APP_ENV=production`, expose a non-loopback origin,
or silently substitute mock/shared quotes. It is not approval for a public or
multi-tenant service. All cloud/OCI scan, IAM, Vault and Audit requirements below
still apply to public deployment; local tests cannot satisfy those gates.
