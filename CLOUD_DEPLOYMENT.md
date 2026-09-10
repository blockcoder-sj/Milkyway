# Milkyway OCI 배포 절차

동아리 회원은 자신의 증권사 API로 페이퍼 전략을 테스트하고, AI는 동아리 공용 키를 사용한다.
실제 주문 제출은 지원하지 않는다. 공개 앱 VM과 독립 credential broker VM을 사용한다.
현재 공개 배포·실제 회원 키 입력은 **NO-GO**다. 최종 판단과 미완료 항목은
[SECURITY_REMEDIATION_STATUS.md](SECURITY_REMEDIATION_STATUS.md)가 우선한다.
아래는 실제 OCI 검증 단계에서 사용할 절차이며, 이 문서 자체는 배포 성공 증거가 아니다.

## 실행 구조와 키 경계

- 앱 VM: Caddy, 공개 앱, paper/backtest worker, scheduler, PostgreSQL, 암호화 백업.
- broker VM: 회원 인증 발급, 개인 키 입력 전용 HTTPS 페이지, 작업 권한 발급,
  OCI KMS 암복호화, 공용 AI 및 회원별 증권사 조회. 앱과 같은 VM에 두지 않는다.
- `AUTHORITY_ENABLED=true`, `MEMBER_CREDENTIALS_ENABLED=true`, `SHARED_AI_ENABLED=true`가
  production 고정값이다. 앱과 worker는 `CREDENTIAL_BACKEND=broker`, broker는 `oci-kms`다.
- 회원은 앱 설정의 링크로 **broker 도메인의 `/credentials`**에 직접 로그인하고 키를 입력한다.
  이 요청은 공개 앱 서버를 거치지 않는다. 키 입력은 저장 요청 직전에 화면에서 지운다.
  키를 검증한 후 회원·공급자·환경·필드에 결합한 KMS 암호문만 DB에 저장한다.
- 앱 DB 역할은 암호문과 비밀번호 해시, 인증 발급 테이블을 읽거나 수정할 수 없다.
  독립 발급된 불투명 세션을 PostgreSQL이 확인하고 RLS로 해당 회원의 행만 허용한다.
- app/paper/backtest는 서로 다른 broker 토큰을 하나씩 받는다. AI에는 유효한 회원 세션,
  CSRF, 프롬프트 결합 단일 사용 허가가 추가로 필요하다. worker는 broker가 고른 작업과
  종목에만 유효한 짧은 작업 권한을 받는다. 회원 ID·암호문·임의 종목을 지정하지 않는다.
- AI 공급자와 모델은 broker 설정으로 고정한다. 원격 AI 키는 broker instance principal이
  `OCI_SHARED_AI_SECRET_ID`의 `CURRENT` 버전을 읽는다. 원격 키의 환경변수·파일 주입은 거부한다.
  공용 AI의 비용 한도와 공급자 사용량 경보는 공급자 계정에도 설정한다.
- DB 관리자와 VM/Docker 관리자는 신뢰하는 운영자다. 이 권한까지 유출되면 런타임 역할의
  RLS 경계로 보호할 수 없다. migration/authority DSN을 앱·worker 컨테이너에 주지 않는다.

## 두 VM과 네트워크

앱 VM의 검증 대상 구성은 Ubuntu 24.04 ARM64, 4 OCPU/24GB이고 broker는 2 OCPU/4GB 이상이다.
로컬 AI를 함께 쓰면 broker에 추가 CPU·메모리가 필요하다. 실제 최대 회원 수 부하는 OCI에서
측정한다. 두 VM 모두 `/opt/milkyway`에 같은 검증된 소스를 배치한다.
`deploy/oci/cloud-init.yaml`은 서명된 고정 Ubuntu 스냅샷과 명시적 패키지 버전을 사용한다.
업데이트 절차는 [deploy/DEPENDENCY_LOCKS.md](deploy/DEPENDENCY_LOCKS.md)에 있다.

- 두 VM의 SSH 22는 운영자 고정 IP만 허용한다.
- 앱과 broker의 HTTPS 443은 동아리 브라우저가 접근할 수 있어야 한다. broker 443을 앱 VM에만
  허용하면 회원 키 입력 페이지가 작동하지 않는다. HTTP 80은 Caddy 인증서 발급·리다이렉트용이다.
- 앱 VM의 PostgreSQL 5432는 `APP_VM_PRIVATE_IP`의 RFC1918 주소에만 바인딩한다.
  OCI NSG는 broker VM의 사설 IP에서 오는 TCP 5432만 허용한다. 인터넷 ingress는 금지한다.
- 8000과 8010은 컨테이너 내부 전용이다. DB는 TLS 1.3, 모든 DB 클라이언트는
  `sslmode=verify-full`과 명시적인 CA 파일을 사용한다. 평문 및 호스트 이름 불일치는 거부한다.
- broker의 사설 DB DNS 이름은 앱 VM의 사설 IP로 해석되어야 한다.
- broker만 두 credential key의 dynamic group에 포함한다. 공개 앱 VM에서 **두 키 모두**
  사용 거부, broker의 두 키 사용 성공, Vault secret release 및 각각의 OCI Audit 증거가 필요하다.

## 오프라인 준비

실제 비밀값은 채팅이나 Git에 넣지 않는다. 채워진 env 파일은 일반 파일 mode `0600`으로 둔다.
각 DB 비밀번호 7개, app/paper/backtest 토큰 3개, 공개 앱의 `SESSION_SECRET`, broker의
`AUTHORITY_SESSION_SECRET`은 각각 독립된 32자 이상 난수를 사용한다. DSN 비밀번호는 URL 인코딩한다.
공개 앱의 SESSION_SECRET은 발급 권한이 없으며 broker의 AUTHORITY_SESSION_SECRET을 복사하지 않는다.

DB TLS 자료는 격리된 관리 호스트에서 만든다. 아래 이름을 실제 broker 측 DB DNS로 바꾼다.
출력 디렉터리가 이미 있으면 도구는 덮어쓰지 않고 실패한다.

```bash
python3 deploy/create-postgres-tls.py --server-name db.milkyway.internal --output-dir postgres-tls
```

`ca.key`는 관리 호스트에만 보관한다. 앱 VM에는 `server.key`(UID/GID 70, mode `0600`),
`server.crt`와 `ca.crt`(읽기 가능한 공개 인증서)만 전송한다. broker VM에는 `ca.crt`만 전송한다.
서버 인증서는 사설 DNS 이름과 Compose 내부 이름 `postgres`를 모두 포함하고 365일 유효하므로
만료 전에 관리 호스트에서 갱신·검증한다. 경로는 각 env 예제의 `POSTGRES_TLS_*_PATH`로 지정한다.

백업 키도 격리된 recovery host에서 생성한다.

```bash
umask 077
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out backup-private.pem
openssl pkey -in backup-private.pem -pubout -out backup-public.pem
chmod 0400 backup-private.pem backup-public.pem
```

private key는 recovery host에만 두고 public key만 앱 VM의 UID 10001이 읽는 경로로 전송한다.
`BACKUP_PUBLIC_KEY_PATH`에 지정한다.

## 데이터 준비

`data_cache/`는 Git에 포함되지 않는다. 검토한 가격 데이터·인증 스냅샷·terminal event를
앱 VM의 `data_staging/`에 별도 전송한다. 가격 파일은 schema version 2 `csv-gzip-v1`만
허용한다. 예전 pickle 파일은 실행·변환하지 않고 신뢰하는 공급자로부터 다시 생성한다.

운영자가 provenance, validation report 및 terminal event를 검토한 뒤 승격한다.
신규 terminal event는 각 `event_id`를 `--approve-event`로 명시해야 한다.

```bash
DATA_PROMOTION_CONFIRM=REVIEWED_SOURCE_PROVENANCE \
  docker compose --env-file deploy/.env --profile maintenance run --rm data-promote
```

출력된 `generation-<manifest-sha256>` 전체를 broker VM에도 전송하고 양쪽 env의
`PROMOTED_DATA_PATH`에 그 경로를 지정한다. 앱·worker·broker는 같은 세대의 읽기 전용 데이터만
사용한다. scheduler는 staging만 수정하며 검토 없이 런타임 데이터를 바꿀 수 없다.
최초 승격 전에는 `PROMOTED_DATA_PATH`에 검토 전용 임시 경로를 지정해 Compose 치환만 수행하고,
승격이 끝나기 전에는 앱이나 broker를 시작하지 않는다.

## 최초 기동과 기존 DB 업그레이드

이 단계는 상태 문서의 공개 배포 허용 이후 수행한다. 두 VM의 `.env`를 예제에서 준비한다.
기존 env 파일을 덮어쓰지 않는다.

```bash
cd /opt/milkyway
umask 077
# 앱 VM의 새 설치에서만:
cp -n deploy/.env.example deploy/.env
# broker VM의 새 설치에서만:
cp -n deploy/credential-broker.env.example deploy/credential-broker.env
```

앱 예제에는 7개 DB 비밀번호와 각 DSN, 앱·broker 도메인, 사설 IP, 인증서·백업·데이터 경로를
채운다. broker 예제에는 authority DSN, 독립 SESSION_SECRET, 역할 토큰 3개, KMS crypto endpoint,
서로 다른 AI/market credential key OCID, 공용 AI secret OCID와 고정 모델을 채운다.
`LOCAL_AI_API_KEY_PATH`는 선택적 로컬 AI 서버 인증용 파일이다. 현재 Compose는 해당 파일을
항상 마운트하므로 원격 AI만 사용해도 UID 10001, mode `0400`의 독립 무작위 값 파일을 둔다.
원격 AI 키나 회원 증권사 키를 이 파일에 넣지 않는다.

앱 VM에서 DB를 먼저 준비한다.

```bash
docker compose --env-file deploy/.env config --quiet
docker compose --env-file deploy/.env up -d postgres
# 기존 DB에서도 반드시 실행: 누락된 역할만 생성하며 기존 비밀번호를 덮어쓰지 않는다.
docker compose --env-file deploy/.env exec postgres sh /docker-entrypoint-initdb.d/10-runtime-roles.sh
docker compose --env-file deploy/.env run --rm database-migrate
```

기존 설치는 먼저 검증된 암호화 백업을 확보하고 모든 writer와 broker를 중지한다. 볼륨을
삭제하거나 다시 초기화하지 않는다. 마이그레이션은 이전 column/default grants를 회수하고,
authority 테이블·RLS·admission trigger를 적용한다. 기존 역할 비밀번호가 env와 다르면 운영자가
별도 회전 절차로 맞춘다. 이후 모든 런타임 역할의 정상 접근·거부 검증을 수행한다.

이전 세션은 새 인증 경계에서 사용할 수 없으므로 재로그인한다. 이전 초대는 새 authority
비밀값으로 다시 발급한다. legacy 회원 암호문은 앱에서 자동 변환하지 않는다. 검증된 백업과
유지보수 계획을 갖추고 broker의 KMS 권한이 있는 관리 환경에서 별도 마이그레이션한다.
기존 보유 종목은 승인 기록이 없으면 `configuration_required`로 정지되므로 운영자가 데이터·원장을
검토해야 한다. 이 절차는 legacy 데이터나 실제 키를 자동 삭제하지 않는다.

broker VM에서 DB 연결, KMS, Vault, 데이터 준비 후 기동한다.

```bash
docker compose --env-file deploy/credential-broker.env -f compose.credential-broker.yaml config --quiet
docker compose --env-file deploy/credential-broker.env -f compose.credential-broker.yaml up -d --build
```

broker 시작 검사는 두 credential key와 Vault secret 전달을 확인한다. 이어서 앱 VM에서 각
역할의 사전 검증을 통과시킨다. 이 검사는 개인 회원의 실제 증권사 인증 성공을 대신하지 않는다.

```bash
docker compose --env-file deploy/.env run --rm --no-deps app python -m cloud_app.preflight --check-database --skip-docker
docker compose --env-file deploy/.env run --rm --no-deps paper-worker python -m cloud_app.preflight --service paper --check-database --skip-docker
docker compose --env-file deploy/.env run --rm --no-deps backtest-worker python -m cloud_app.preflight --service backtest --check-database --skip-docker
docker compose --env-file deploy/.env up -d
```

관리자와 초대는 **broker의 authority 환경**에서 생성한다. 비밀번호는 터미널에서 입력하고
수신자 이메일에 결합된 1회 초대 token은 한 번만 출력된다.

```bash
docker compose --env-file deploy/credential-broker.env -f compose.credential-broker.yaml exec credential-broker python -m cloud_app.manage create-admin --email ADMIN_EMAIL --name ADMIN_NAME
docker compose --env-file deploy/credential-broker.env -f compose.credential-broker.yaml exec credential-broker python -m cloud_app.manage create-invitation --email MEMBER_EMAIL --expires-hours 24
```

실제 두 VM에서 정상/거부·Audit·부하·재부팅 검증 후 각 VM에 해당 systemd unit을 설치한다.
앱은 `deploy/systemd/milkyway.service`, broker는 `milkyway-credential-broker.service`다.

## 개인 증권사와 공용 AI

회원은 broker `/credentials`에서 별도로 로그인한 뒤 개인 증권사 연결을 등록·교체·삭제한다.
KIS는 paper/real 조회 환경, Toss는 지원되는 live 조회 경로를 사용한다. 어떤 경우에도 이
웹서비스는 실거래 주문을 제출하지 않는다. 공급자 측 허용 범위와 실제 인증은 배포 검증에 포함한다.
개인 키 기반 시세는 해당 회원에게만 저장되며 다른 회원의 시세로 대체하지 않는다.
`QUOTE_PROVIDER=mock`은 production 개인 키 조회를 mock으로 바꾸는 스위치가 아니다.
`QUOTE_PROVIDER`와 `MARKET_DATA_SHARING_ALLOWED`는 남아 있는 개발용 공용 조회 설정이며
개인 회원 production에서는 예제 기본값을 유지한다.

broker는 승인 데이터에서 보유·후보 종목을 정하고 한 회원의 계좌를 하나의 시세 배치로 묶는다.
기본 동시 처리 8개, 배치 최대 200종목, provider 작업 제한 20초, 전체 tick 30초,
시세 유효기간 180초다. 임의 종목 요청과 권한 재사용은 거부된다. 전략 형식이나 승인 보유 종목,
회원 배치 용량에 문제가 있는 계좌는 검토 상태로 정지하고 다른 회원의 순환을 계속한다.
40명 최악 조건의 실제 CPU·메모리·시세 freshness는 OCI에서 별도 입증해야 한다.

AI는 고정 공급자/모델과 공용 Vault secret을 사용한다. 회원별 AI 키 입력 API는 없다.
회원별 시간당 10회와 전체 durable budget을 적용하고 실패한 provider 요청도 소비한 허가를
재사용하지 못한다. 로컬 AI를 선택하면 broker env의 `COMPOSE_PROFILES=local-ai`,
`LOCAL_AI_ENABLED=true`, `SHARED_AI_PROVIDER=local`을 사용한다. 고정 모델 revision과 이미지
digest를 유지하고 변경 시 다시 검증한다.

## 운영·백업·복구

```bash
docker compose --env-file deploy/.env ps
docker compose --env-file deploy/.env logs --since 30m app paper-worker backtest-worker scheduler
curl -fsS https://YOUR_DOMAIN/health/ready
```

ready의 `worker=false`는 작업 엔진 상태 점검이 필요하다는 뜻이다. `data_gate=false`면
신규 리밸런싱과 엄격 PIT 백테스트를 재개하지 않는다. scheduler 결과를 독립 검토·승격한 뒤
양쪽 읽기 전용 데이터 세대를 갱신한다. 브로커나 개별 증권사 장애 시 시세를 다른 회원 키나
공용 값으로 대체하지 않는다.

DB dump는 tmpfs에서 생성해 RSA-OAEP-SHA256 + AES-256-GCM으로 암호화하고 `.mwbak`과
checksum만 `backups/`에 게시한다. 기본 6시간 주기, 14일 보존이다. private key는 VM에 두지
않고 recovery host에 보관한다. OCI 부트 볼륨 백업과 실제 복구 훈련도 별도로 수행한다.
DB 백업에는 회원 키의 암호문이 포함되므로 복원 시 KMS 키의 접근 권한과 보존도 필요하다.

복구는 현재 DB를 교체하는 작업이다. 유지보수 중 recovery host에서만 수행하며 실제 실행 전
대상 DB·백업을 검토한다. `compose.restore.yaml`에는 전용 관리 계정의 pgpass, backup private key,
DB CA와 recovery network를 지정한다.

```bash
docker compose -f compose.restore.yaml --profile maintenance config --quiet
RESTORE_CONFIRM=quantclub docker compose -f compose.restore.yaml --profile maintenance run --rm restore /backups/quantclub_YYYYMMDDTHHMMSSZ.mwbak
```

단일 PostgreSQL과 두 VM은 다중 리전 고가용성을 제공하지 않는다. 컨테이너 재시작·VM 재부팅과
DB/볼륨 전체 손실 복구는 구별해 검증한다. 공개 GO에는 sealed scan과 상태 문서의 모든 실제
OCI gate가 필요하다.
