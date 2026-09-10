# OCI 및 공급자 운영 게이트 런북

> 상태: 실행 전용 체크리스트. 이 문서는 배포 승인이나 실제 키 사용의 증거가 아니다.
> `SECURITY_REMEDIATION_STATUS.md`의 최신 **NO-GO** 결정이 이 문서보다 우선한다.

이 런북의 목적은 Milkyway가 실제 회원 증권사 키를 받거나 공개 배포를 시작하기 전에
OCI와 공급자 경계를 하나씩 증명하는 것이다. 앱은 주문을 제출하지 않으며, 이 절차로도
그 제한을 바꾸지 않는다.

## 완료 조건

다음 네 묶음이 모두 통과하고 승인자가 증거를 검토하기 전에는 **NO-GO**를 해제하지
않는다.

- [ ] 최종 소스에 대한 봉인된 whole-repository Deep Security Scan에 미해결 High/Medium이 없다.
- [ ] 해당 스캔 뒤의 모든 수정은 회귀 테스트, 전체 검증, 독립 읽기 전용 리뷰를 통과했다.
- [ ] 실제 OCI 두 VM에서 broker만 두 KMS credential key와 필요한 Vault secret을 사용할 수 있고,
  public app VM은 모두 거부된다.
- [ ] 실제 공급자 인증, 회전·철회, member 격리, Audit 조회·보존·알림이 제한된 테스트 계정으로
  증명됐다.

어느 한 칸이라도 실패하거나 증거가 누락되면 해당 단계를 중지하고 **NO-GO를 유지**한다.
실패 원인과 시간만 기록한다. API 키, 세션, 암호문, 환경 파일, DB 덤프, 민감한 Audit 본문은
증거에 넣지 않는다.

## 0. 공통 안전 준비

### 0.1 담당자와 범위 고정

- [ ] OCI tenancy/security 관리자, VM 운영자, 공급자 계정 관리자, 애플리케이션 검증자를
  서로 지정한다. 한 사람이 모든 증거를 승인하지 않는다.
- [ ] public app VM과 credential broker VM의 OCID, 사설 IP, compartment OCID, 리전,
  broker 도메인을 비밀이 아닌 운영 기록에 적는다.
- [ ] KMS AI credential key, KMS market credential key, shared-AI Vault secret, 필요 시
  shared-market Vault secret의 OCID를 보안 운영 기록에 적는다. 이 식별자는 앱 VM의 env 파일에
  넣지 않는다.
- [ ] 실제 회원 계정 대신, 최소 권한·조회 전용·주문 권한 없는 KIS/Toss/AI 테스트 계정만 준비한다.
  테스트 계정의 공급자 콘솔에서 주문·출금·계좌변경 권한이 없는지 먼저 확인한다.
- [ ] 검증 중 공개 가입, 실제 회원 초대, 실제 주문, 기존 DB/볼륨 삭제, 기존 env 파일 덮어쓰기를
  금지한다.

### 0.2 증거 보관소 준비

Git 작업 트리 밖의 접근 제한된 위치에 증거 폴더를 만든다. 다음만 저장한다: 명령의 exit code,
UTC 시간, 리소스 OCID의 마지막 8자, 소프트웨어/이미지 digest, 해시, 무해한 probe ID,
승인자. 평문 출력과 인증 헤더는 저장하지 않는다.

```text
evidence/
  01-deep-scan/
  02-oci-identity/
  03-kms-vault/
  04-network-db/
  05-provider/
  06-audit-alerts/
  07-final-review/
```

- [ ] 모든 실행 터미널에서 shell history가 실제 키를 보관하지 않도록 한다.
- [ ] 채워진 `deploy/.env`, `deploy/credential-broker.env`, 백업 키, TLS CA private key는
  Git·채팅·증거 보관소에 복사하지 않는다.
- [ ] 증거에는 비밀값 대신 `redacted`, key hint 또는 SHA-256의 짧은 식별자만 사용한다.

## 1. Deep Security Scan 게이트

### 1.1 관리형 세션에서만 시작

- [ ] Codex 세션의 effective permission profile이 `type="managed"`, profile `:workspace`인지
  확인한다. `type="disabled"`이면 이 단계를 시작하지 않는다.
- [ ] `SECURITY_REMEDIATION_STATUS.md`와 `AGENTS.md`를 처음부터 끝까지 읽고,
  기존 작업트리·`runtime/`·Docker volume을 보존한다.
- [ ] 실제 키와 회원 자격증명을 넣지 않은 상태에서 소스를 동결한다. `git status --short`와
  기준 revision을 증거에 기록한다.

### 1.2 스캔 실행과 판정

- [ ] Codex Security의 **whole-repository Deep Security Scan**을 repository root, scope `.`로
  한 번 시작한다. 기존 스캔이 실행 중이면 새 스캔을 중복 시작하지 않는다.
- [ ] coordinator가 생성한 `scan-manifest.json`, `findings.json`, `coverage.json`이 모두 있는지
  확인하고, 같은 scan을 정확히 한 번 seal/complete한다.
- [ ] 생성된 `report.md`, scan ID, 기준 revision, coverage, High/Medium/Low 개수를
  `01-deep-scan/`에 기록한다. 결과 파일 자체에 민감한 경로가 있으면 접근 제어된 원본 위치만
  기록하고 Git에 복사하지 않는다.

### 1.3 발견 항목 처리 규칙

- High 또는 Medium이 있으면: 항목별로 원인, 최소 수정, focused regression test, 전체 테스트,
  독립 read-only review를 완료한다. 검증 실패는 수정 완료가 아니다.
- 스캔 뒤 코드·Compose·IAM 계약·의존성 lock이 변경되면 스캔은 최종 소스의 증거가 아니다.
  수정들을 하나의 검증 묶음으로 끝낸 뒤 1.2의 **새 최종 Deep Scan**을 실행한다.
- Low는 소유자·기한·수용 근거를 기록하고, 정책상 Medium으로 승격될 가능성을 검토한다.
- [ ] 최종 스캔이 현재 배포 후보 revision을 대상으로 하고 미해결 High/Medium이 없음을 승인한다.

## 2. OCI 두 VM과 네트워크 경계

### 2.1 VM 역할을 분리

- [ ] public app VM과 credential broker VM을 서로 다른 instance OCID로 생성한다. broker를
  public VM의 Docker Compose profile이나 같은 VM에 배치하지 않는다.
- [ ] 양쪽에 검증 완료한 같은 source revision과 고정 image digest를 배치한다.
- [ ] broker에만 `deploy/credential-broker.env`를 `0600` 일반 파일(심볼릭 링크 아님)으로 둔다.
  public VM에는 `deploy/.env`만 둔다.
- [ ] public VM 설정에 `OCI_KMS_CRYPTO_ENDPOINT`, `OCI_AI_CREDENTIAL_KEY_ID`,
  `OCI_MARKET_CREDENTIAL_KEY_ID`, `OCI_*_SECRET_ID`, provider plaintext key가 없는지 확인한다.
- [ ] broker 설정에는 서로 다른 두 KMS key OCID와 필요한 Vault secret OCID만 둔다. Vault secret의
  plaintext를 env나 mounted file로 넣지 않는다.

### 2.2 NSG와 경로 확인

- [ ] SSH 22는 운영자의 고정 IP만 허용한다.
- [ ] HTTP 80은 인증서 발급/redirect에만, HTTPS 443은 app과 broker 각각의 도메인에만 연다.
  broker 443은 회원 브라우저가 직접 접근해야 하므로 app VM으로만 제한하지 않는다.
- [ ] PostgreSQL 5432는 public VM의 RFC1918 사설 IP와 broker VM의 사설 IP에서만 허용한다.
  인터넷 ingress, `0.0.0.0/0`, public IP source rule은 허용하지 않는다.
- [ ] 8000/8010은 OCI ingress와 host 공개 포트를 만들지 않는다.
- [ ] broker DB DNS가 public VM의 사설 DB endpoint로만 해석되고, 모든 DSN이
  `sslmode=verify-full` 및 명시적 CA를 쓰는지 확인한다.
- [ ] 승인된 운영자 네트워크에서만 NSG와 route table의 export/스크린샷을 수집한다.

## 3. IAM, dynamic group, KMS, Vault

OCI dynamic group은 instance certificate의 조건으로 런타임 멤버십을 정한다. 따라서
`public`과 `broker`가 같은 broad compartment rule에 함께 매치되면 안 된다. OCI의
dynamic-group 및 정책 문법은 변경될 수 있으므로 적용 전 보안 관리자가 현재 공식 문서를
대조한다.

공식 참고: [OCI dynamic groups](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm),
[OCI policy templates](https://docs.oracle.com/en-us/iaas/Content/Identity/policiescommon/commonpolicies.htm),
[OCI secret-bundle access](https://docs.oracle.com/en-us/iaas/Content/container-instances/vault-secrets-image-authorization.htm).

### 3.1 broker 전용 dynamic group

- [ ] broker instance OCID 하나만 매치하는 `milkyway-credential-broker` dynamic group을 만든다.
  instance OCID 기반의 좁은 rule을 사용한다. public VM의 instance OCID, 전체 compartment,
  광범위한 tag rule을 포함하지 않는다.
- [ ] IAM 콘솔에서 해당 dynamic group의 member/matching rule과 public VM의 instance OCID를
  별도로 대조한다.
- [ ] public VM이 다른 dynamic group을 통해서도 두 key 또는 Vault secret에 도달할 수 없는지
  모든 effective policy를 검토한다. OCI IAM은 명시적 deny보다 **어떤 allow도 없는 상태**가
  거부의 근거이므로, 이름만 다른 broad policy도 찾는다.

### 3.2 최소 권한 정책

KMS key와 secret은 각각 별도 권한으로 다룬다. 다음은 보안 관리자가 실제 compartment 및
개별 OCID로 치환해 검토할 정책 형태다. tenancy 전체, `manage all-resources`, 전체 key/secret
family 허용으로 넓히지 않는다.

```text
Allow dynamic-group milkyway-credential-broker to use keys in compartment <vault-compartment>
  where target.key.id = '<AI_CREDENTIAL_KEY_OCID>'
Allow dynamic-group milkyway-credential-broker to use keys in compartment <vault-compartment>
  where target.key.id = '<MARKET_CREDENTIAL_KEY_OCID>'
Allow dynamic-group milkyway-credential-broker to read secret-bundles in compartment <vault-compartment>
  where target.secret.id = '<SHARED_AI_SECRET_OCID>'
```

- [ ] market shared-secret를 사용하면 같은 형태로 그 **개별** secret OCID를 추가한다.
- [ ] key의 rotate/disable/delete 권한, secret의 create/update/delete 권한은 broker dynamic group에
  부여하지 않는다.
- [ ] IAM 변경 직후 OCI가 정책을 적용할 시간을 고려하고, 적용 전후의 policy version과 시간을
  증거에 기록한다.

### 3.3 broker 허용 증명

broker VM에서 아래의 무해한 KMS round-trip을 수행한다. 이 코드는 랜덤 probe만 암복호화하고
회원 키를 저장하지 않으며 AI와 market 두 key를 모두 검증한다.

```bash
cd /opt/milkyway
docker compose --env-file deploy/credential-broker.env \
  -f compose.credential-broker.yaml exec credential-broker \
  python -m cloud_app.preflight --service broker --check-database --skip-docker
```

- [ ] exit code 0 및 `credential_kms: true`를 redacted 기록으로 저장한다.
- [ ] broker 기동 시 production provider secret retrieval도 성공하는지 health/readiness와
  container log의 비밀값 없는 상태 메시지로 확인한다.
- [ ] 실패하면 policy를 넓히지 말고 key OCID, broker instance membership, endpoint region,
  network egress, time sync, KMS/Vault Audit event를 원인별로 확인한다.

### 3.4 public VM 거부 증명

public VM에는 key/secret ID를 지속 설정하지 않는다. 보안 운영자가 일회성, history를 남기지 않는
세션에서 harmless probe를 실행하며 OCI CLI의 **instance principal** 인증을 명시한다. plaintext나
secret bundle 본문은 출력하거나 파일에 저장하지 않는다.

각 KMS key에 대해 한 번씩 다음 조건을 검증한다.

```text
OCI CLI authentication: instance_principal
operation: KMS encrypt of a fixed harmless probe
expected result: AccessDenied / NotAuthorized (non-zero exit)
```

shared-AI secret과 필요한 market secret에도 다음 조건을 검증한다.

```text
OCI CLI authentication: instance_principal
operation: SecretsClient GetSecretBundle at stage CURRENT
expected result: AccessDenied / NotAuthorized (non-zero exit)
```

- [ ] AI KMS key 거부, market KMS key 거부, shared AI secret 거부, 필요 시 market secret 거부를
  각각 기록한다.
- [ ] 단순 DNS/timeout은 권한 거부의 증거가 아니다. OCI service가 반환한 authorization denial과
  대응하는 Audit event가 있어야 한다.
- [ ] public VM에서 성공하면 즉시 테스트를 중단하고 secret을 rotate/revoke할지 보안 책임자가
  판단한다. broad dynamic group과 inherited policy를 제거한 뒤, 새 인스턴스 principal로 다시
  검증한다.

## 4. 애플리케이션·DB 운영 검증

### 4.1 기동 순서

- [ ] TLS CA/private key 및 recovery backup private key가 각각 지정된 host에만 있는지 점검한다.
- [ ] public VM에서 PostgreSQL을 먼저 기동하고, 역할/기존 DB migration을 `CLOUD_DEPLOYMENT.md`의
  기존-volume 보존 절차로 수행한다. 롤백을 위해 검증된 암호화 backup을 먼저 확보한다.
- [ ] broker를 먼저 기동하여 KMS/Vault/authority DB를 검증한 뒤 app/paper/backtest를 기동한다.
- [ ] 아래 preflight는 각 runtime role이 broker에 도달하고 DB를 TLS로 접속하는지 확인한다.

```bash
cd /opt/milkyway
docker compose --env-file deploy/.env run --rm --no-deps app \
  python -m cloud_app.preflight --check-database --skip-docker
docker compose --env-file deploy/.env run --rm --no-deps paper-worker \
  python -m cloud_app.preflight --service paper --check-database --skip-docker
docker compose --env-file deploy/.env run --rm --no-deps backtest-worker \
  python -m cloud_app.preflight --service backtest --check-database --skip-docker
```

### 4.2 DB role/RLS 확인

- [ ] 별도 app, authority, worker connection으로 정상 한 회원 접근과 다른 회원 행 거부를 각각
  PostgreSQL integration test로 확인한다.
- [ ] public app/paper/backtest DSN이 credential ciphertext, password hash, invitation/authority
  테이블에 직접 접근할 수 없는지 negative test로 확인한다.
- [ ] migration을 새 DB와 기존 DB 복제본에서 반복해 historical/future grant 회수와 RLS
  admission trigger가 유지되는지 확인한다.
- [ ] test DB, synthetic provider data, disposable test member만 사용한다.

## 5. 공급자 검증: 실제 회원 키 전 단계

### 5.1 공통 원칙

- [ ] 공급자 약관, API 이용 승인, rate/cost limit, 테스트/실계좌 사용 조건을 공급자 담당자 또는
  공식 포털에서 확인한다.
- [ ] KIS는 먼저 paper/virtual-investment 조회 자격증명으로 시험한다. live quote 검증은
  별도 승인된 조회 전용 테스트 계정으로만 수행한다.
- [ ] Toss와 외부 AI도 전용 테스트 credential을 사용한다. 앱이 주문 제출 기능을 갖지 않음을
  재확인하고, provider credential에 주문/송금 권한을 부여하지 않는다.
- [ ] 실제 회원 API key를 채팅, 지원 티켓, browser HAR, frontend log, reverse-proxy log,
  database query 결과에 포함하지 않는다.

### 5.2 broker-origin 입력·검증

- [ ] test member A와 B를 broker authority 환경에서 만든다. invitation은 이메일 결합·일회성으로
  전달하고, 토큰을 증거에 저장하지 않는다.
- [ ] 각 test member는 public app이 아닌 `https://<broker-domain>/credentials`에 직접 로그인한다.
  TLS certificate/hostname이 맞고 redirect가 public app을 경유하지 않는지 확인한다.
- [ ] member A의 read-only provider key를 등록한다. browser 화면이 저장 요청 직전에 key를 지우고,
  응답과 UI에는 hint만 반환하는지 확인한다.
- [ ] broker가 provider의 가벼운 인증/quote 준비 요청으로 key를 검증하고, 실패 시 generic error를
  반환하며 raw key를 log에 남기지 않는지 확인한다.
- [ ] member B로 로그인해 A의 등록 상태·시세·암호문을 열람/변경/삭제할 수 없는지 negative test를
  수행한다.
- [ ] DB에서 app/worker role로 raw key 또는 member A의 ciphertext에 접근하려는 negative test를
  수행한다. SQL 출력에는 data를 덤프하지 않고 행 접근 허용/거부만 기록한다.

### 5.3 공급자 동작과 장애 처리

- [ ] KIS paper에서 작은 허용 종목 목록의 quote가 broker를 통해 반환되는지 확인한다.
- [ ] 승인된 경우에만 KIS live와 Toss live에서 1회 최소 조회를 수행한다. 가격 결과·계좌번호·key는
  증거에 저장하지 않고 성공 code, timestamp, provider request ID의 허용된 일부만 기록한다.
- [ ] 잘못된/철회된 test key로 재시도해 broker가 fail-closed하고 다른 회원 또는 공용 key로
  대체하지 않는지 확인한다.
- [ ] provider timeout, 429/rate-limit, malformed response에서 worker가 bounded deadline 내 실패하고
  계정이 `configuration_required` 또는 안전한 재시도 상태로 전이하는지 확인한다.
- [ ] 40명 최악 조건을 대표하는 synthetic load에서 CPU, memory, quote freshness, provider quota를
  실제 OCI instance size에서 측정한다. 한 회원의 실패가 다른 회원 작업을 굶기지 않는지 확인한다.

### 5.4 Vault secret 회전과 철회

- [ ] shared AI/market secret의 `CURRENT` 버전으로 broker 정상 호출을 확인한다. secret 본문은 보지
  않거나 기록하지 않는다.
- [ ] 공급자 포털에서 새 전용 test key를 만들고 Vault에 새 version을 만든 뒤 `CURRENT`를 새 version으로
  전환한다. 구 key는 즉시 출력·복사하지 않는다.
- [ ] 다음 broker operation이 새 version으로 성공하는지, 이전 version을 cache/fallback하지 않는지
  확인한다.
- [ ] 이전 provider key를 철회한다. `CURRENT`를 의도적으로 철회된 test key로 돌린 경우 broker가
  안전하게 실패하고, 마지막 정상 plaintext를 재사용하지 않는지 확인한 후 올바른 새 version으로
  복구한다.
- [ ] 회전·철회·복구 각각에 broker allow 및 public deny Audit event가 연결되는지 확인한다.

## 6. OCI Audit, 보존, 알림 증명

OCI Audit은 console/CLI/API로 event를 조회할 수 있다. 공식 방법은
[OCI Audit event search](https://docs.oracle.com/en-us/iaas/Content/Audit/Tasks/searching-log-events.htm)를
따르고, 조직의 retention/alerting 규칙은 보안 책임자가 별도 승인한다.

- [ ] 3.3의 broker KMS allow와 Vault secret retrieval마다 Audit event가 보이는지 확인한다.
- [ ] 3.4의 public deny마다 해당 public instance principal, key/secret target, authorization denial이
  보이는지 확인한다. event 전문이나 secret bundle은 증거에 복사하지 않는다.
- [ ] Audit query의 UTC start/end, filter, 결과 개수, event OCID/hash를 기록한다. 모든 event가
  delivery될 때까지 기다린 뒤 조회한다.
- [ ] 조직이 요구하는 기간으로 Audit archive/retention을 구성하고, 저장소 접근 권한과 삭제 보호를
  검토한다.
- [ ] KMS/Vault allow/deny 또는 policy/dynamic-group 변경을 탐지하는 승인된 Logging/Monitoring
  경로를 구성한다. 실제 **test denial** 이벤트로 alarm과 notification delivery를 한 번 끝까지
  시험한다.
- [ ] 수신자, 알림 시간, incident ticket ID만 증거에 남긴다. webhook URL, email token, event 본문은
  남기지 않는다.

## 7. 최종 독립 검토와 GO 판정

- [ ] 애플리케이션 개발자가 아닌 검토자가 Deep Scan report, source revision, test logs, OCI
  allow/deny evidence, provider test evidence, Audit/alert evidence를 read-only로 검토한다.
- [ ] 검토자는 public VM이 두 key와 secret에 접근 불가하고 broker만 필요한 최소 권한을 가진다는
  결론을 각각의 실제 evidence로 확인한다. 코드 mock이나 Compose dummy 값은 인정하지 않는다.
- [ ] 운영 책임자가 backup restore drill, TLS certificate 만료 계획, key/secret rotation owner,
  incident/rollback 연락망을 확인한다.
- [ ] 모든 미해결 Medium/High, 실환경 실패, 라이선스/공급자 승인 누락이 없을 때만 제한된 pilot의
  범위·기간·회원 수·중단 기준을 문서화한다.
- [ ] pilot 이후에도 신규 provider, OCI IAM/VM 변경, key rotation 방식 변경, dependency/image 변경은
  변경 관리와 영향 범위에 맞는 재검증 대상이다. 보안 수정 묶음으로 최종 소스가 바뀌면 다시 1장을
  따른다.

## 실패 시 즉시 할 일

1. 실제 회원 키 입력과 공개 배포를 중단한다.
2. 증거에서 비밀을 제거한 뒤 실패 시간, 역할, resource 종류, error class만 기록한다.
3. IAM broad grant/public membership 문제면 보안 담당자가 최소 권한으로 되돌리고 영향받은
   provider secret/key의 회전 필요성을 판단한다.
4. source 또는 Compose 수정이 필요하면 focused test와 전체 검증을 수행하고 독립 검토를 받는다.
5. 최종 소스가 달라졌다면 새 봉인 Deep Scan을 수행한 뒤 이 런북의 해당 OCI/공급자 검증을 다시
   실행한다.

## 관련 문서

- `SECURITY_REMEDIATION_STATUS.md` — 최종 보안·배포 판단의 우선 문서
- `CLOUD_DEPLOYMENT.md` — VM, Compose, DB/TLS, 데이터·복구 기동 절차
- `deploy/PROVIDER_SECRET_DELIVERY.md` — broker-only Vault secret 전달 계약
- `deploy/credential-broker.env.example` — broker 환경변수의 비밀 미포함 예시
