# Milkyway Cloud Deployment Gate

이 문서는 30명, 5주간 사용할 페이퍼 트레이딩 플랫폼의 기준 운영 절차다. production은
공개 앱 VM과 credential/provider-operation broker VM을 분리한다. 같은 VM의 컨테이너 분리는
OCI instance principal을 분리하지 못하므로 허용하지 않는다.
기존 macOS `cron -> watchdog.sh` 실거래 봇과 클라우드 페이퍼 플랫폼은 별개다.

## 현재 준비된 범위

- 초대 코드 기반 회원가입, scrypt 비밀번호 해시, HttpOnly 서명 세션, CSRF 방어
- 사용자별 전략·백테스트·페이퍼 계좌 분리
- 사용자별 암호화 AI API 키 또는 서버 공용 로컬 AI, AI 출력 JSON 검증 및 임의 코드 실행 차단
- 모든 전략의 `backtest_core.run_backtest()` 공통 원장 강제
- PostgreSQL 작업 큐, 중복 체결 방지 키, 단일 leader lease
- 보유/후보 종목을 합친 1회 시세 수집 후 사용자 계좌에 공유
- 첫 인증 스냅샷 이전 성과에 탐색용·생존편향 경고 표시
- 일일 공식 거래소 스냅샷, 목록 이탈 alert, 완료 세션 가격 갱신 및 해시 검증
- 앱·worker·scheduler·PostgreSQL·Caddy·6시간 DB 백업 컨테이너
- HTTPS 자동 인증서, 보안 헤더, readiness/liveness, worker heartbeat

외부에서 채워야 하는 값은 도메인/DNS, OCI 인스턴스 2대·Vault 키·IAM 정책, 브로커 키,
시세 재사용 허용 확인과 서버 비밀값뿐이다. 회원의 클라우드 AI API 키는 설정 화면에서
입력하고 별도 broker가 OCI Vault로 암호화 저장한다.

## 권장 OCI 인스턴스

- 앱 VM: Ubuntu 24.04 ARM64, Ampere A1 4 OCPU/24GB, 부트 볼륨 100GB
- broker VM: Ubuntu 24.04 ARM64, 1~2 OCPU/4GB 이상. 로컬 7B AI를 함께 쓰면 4 OCPU/24GB
- 두 VM 모두 자동 부트 볼륨 백업과 예약 공인 IP 사용
- 앱 VM OCI Network Security Group ingress:
  - TCP 22: 운영자 고정 IP만
  - TCP/UDP 443: 동아리 사용 위치 또는 인터넷
  - TCP 80: HTTPS 인증서 발급/리다이렉트
- broker VM ingress:
  - TCP 22: 운영자 고정 IP만
  - TCP/UDP 443: 앱 VM의 고정 공인 IP만
  - TCP 80: Caddy HTTP-01 인증서 발급용. API는 HTTPS로만 사용한다.
- PostgreSQL 5432, 앱 8000, broker 8010은 절대 공인 ingress로 열지 않는다.

`deploy/oci/cloud-init.yaml`을 두 인스턴스 생성 시 cloud-init으로 넣으면 Docker,
fail2ban, 자동 보안 업데이트가 설치된다. 저장소는 양쪽 `/opt/milkyway`에 배치한다.

## OCI Vault 경계

공개 운영 전에 서울 리전 OCI Vault에 AES 대칭 키 두 개를 만들고 AI와 시세 자격증명에
각각 할당한다. 두 키는 삭제 예약을 걸지 않고 rotation·Audit·경보 정책을 구성한다. Vault
Crypto Endpoint와 두 key OCID를 기록하되 키 material을 export하지 않는다.

**broker 인스턴스 OCID 하나만** 포함하는 dynamic group(예: `MilkywayCredentialBroker`)을 만들고,
키가 위치한 compartment에 다음처럼 두 key만 사용할 수 있게 한다. 런타임에는 Vault 또는
key의 manage/export/delete 권한을 주지 않는다.

```text
Allow dynamic-group MilkywayCredentialBroker to use keys in compartment <KEY_COMPARTMENT> where all {target.key.id = '<AI_KEY_OCID>', request.permission = 'KEY_ENCRYPT'}
Allow dynamic-group MilkywayCredentialBroker to use keys in compartment <KEY_COMPARTMENT> where all {target.key.id = '<AI_KEY_OCID>', request.permission = 'KEY_DECRYPT'}
Allow dynamic-group MilkywayCredentialBroker to use keys in compartment <KEY_COMPARTMENT> where all {target.key.id = '<MARKET_KEY_OCID>', request.permission = 'KEY_ENCRYPT'}
Allow dynamic-group MilkywayCredentialBroker to use keys in compartment <KEY_COMPARTMENT> where all {target.key.id = '<MARKET_KEY_OCID>', request.permission = 'KEY_DECRYPT'}
```

broker만 OCI Python SDK의 instance principal로 Vault를 호출한다. 사용자 API private key나
OCI config 파일은 어느 컨테이너에도 넣지 않는다. 앱 VM OCID가 dynamic group에 포함되지
않았음을 OCI 정책 시뮬레이션과 Audit으로 확인한다. broker는 app/paper 역할별 토큰을 별도로
검증하고 raw decrypt, 임의 URL·header·method proxy, access-token 반환을 제공하지 않는다.
OCI Audit에서 `Encrypt`/`Decrypt` 급증, 인증 실패와 평소와 다른 시간대 호출을 경보로 연결한다.

이 경계는 앱/worker 프로세스가 침해돼도 기존 저장 credential 원문을 대량 추출하지 못하게
한다. 다만 침해된 앱은 허용된 전략 생성·연결 교체 작업을 남용하거나 새로 입력되는 키를
가로챌 수 있다. 이를 막으려면 브라우저가 별도의 신뢰 origin으로 직접 연결하고 사용자별
서명 capability를 검증하는 추가 구조가 필요하다. 현재 30명 운영에서는 rate limit, 역할별
토큰, broker 443 source restriction, Audit/공급자 사용량 경보를 필수 보완 통제로 둔다.

`data_cache/`는 Git에 포함되지 않는다. 코드 배치 후 로컬에서 다음 두 디렉터리를 서버로
별도 전송해야 한다. 현재 필요한 전송량은 약 102MB다.

```bash
rsync -az data_cache/backtest_datasets/2026_equities_pit_20260824/ \
  ubuntu@SERVER_IP:/opt/milkyway/data_cache/backtest_datasets/2026_equities_pit_20260824/
rsync -az data_cache/universe_snapshots/ \
  ubuntu@SERVER_IP:/opt/milkyway/data_cache/universe_snapshots/
```

`data_cache/universe_events/events.jsonl`이 존재하면 함께 전송한다. `.env`, `runtime/`, 기존 DB,
브로커 토큰 파일은 로컬에서 서버로 복사하지 않는다.

## 최초 배포

### 1. credential broker VM

실제 broker 도메인을 DNS에 연결하고 broker VM에서 다음을 실행한다. app/paper 토큰은 각각
`openssl rand -hex 32`로 만들고 서로 재사용하지 않는다. `credential-broker.env`는 broker
VM에만 존재해야 한다.

```bash
cd /opt/milkyway
umask 077
install -m 600 deploy/credential-broker.env.example deploy/credential-broker.env
# BROKER_DOMAIN, 두 역할 토큰, Vault endpoint와 서로 다른 두 key OCID를 교체
docker compose --env-file deploy/credential-broker.env \
  -f compose.credential-broker.yaml config
docker compose --env-file deploy/credential-broker.env \
  -f compose.credential-broker.yaml up -d --build
curl -fsS https://BROKER_DOMAIN/health/live
```

broker startup은 두 OCI key에 대해 실제 Encrypt/Decrypt round trip을 실행한다. 실패하면
컨테이너가 ready 상태가 되지 않는다. broker VM의 443 ingress를 앱 VM의 고정 IP로 제한한 뒤
앱 VM에서만 HTTPS 연결을 확인한다. `compose.credential-broker.yaml`은 KMS·공용 KIS·로컬 AI
비밀을 broker에만 전달한다.

수동 검증이 끝나면 broker용 systemd unit을 설치한다.

```bash
sudo install -m 0644 deploy/systemd/milkyway-credential-broker.service \
  /etc/systemd/system/milkyway-credential-broker.service
sudo systemctl daemon-reload
sudo systemctl enable --now milkyway-credential-broker.service
```

### 2. 앱 VM

```bash
cd /opt/milkyway
umask 077
install -m 600 deploy/.env.example deploy/.env
mkdir -p backups models
chmod 700 backups models
sudo chown -R 10001:10001 data_cache
```

`deploy/.env`에서 다음 값을 반드시 교체한다.

- `PUBLIC_BASE_URL`, `DOMAIN`, `ALLOWED_HOSTS`
- `POSTGRES_PASSWORD`와 그 값을 URL 인코딩한 `DATABASE_URL`
- `SESSION_SECRET`: `openssl rand -hex 32` 결과
- `CLUB_INVITE_CODE`: 동아리 전용 임의 문자열
- `CREDENTIAL_BROKER_URL`: 위 broker의 credential-free HTTPS origin
- `CREDENTIAL_BROKER_APP_TOKEN`, `CREDENTIAL_BROKER_PAPER_TOKEN`: broker VM 값과 일치하는
  서로 다른 난수. Compose는 각 컨테이너에 자기 역할 토큰 하나만 전달한다.

`deploy/.env`는 일반 파일·권한 `0600`을 유지해야 한다. Compose의 `--env-file`은
변수 치환에만 사용하며, 각 컨테이너에는 `compose.yaml`의 서비스별 허용 목록에 있는
환경변수만 전달한다.
웹·paper·backtest 컨테이너의 데이터셋은 읽기 전용이며, 공급자 갱신을 담당하는
scheduler만 `data_cache` 쓰기 권한을 가진다.
앱 VM의 `.env`에는 OCI endpoint/key OCID, 회원 credential root, 공용 KIS key, 로컬 AI key를
두지 않는다. 앱 VM은 Vault dynamic group에도 포함하지 않는다.

AI 없이 먼저 기동한다.

```bash
docker compose --env-file deploy/.env config
docker compose --env-file deploy/.env up -d postgres
docker compose --env-file deploy/.env run --rm app python -m cloud_app.preflight --check-database --skip-docker
docker compose --env-file deploy/.env up -d
docker compose --env-file deploy/.env exec app python -m cloud_app.manage create-admin --email ADMIN_EMAIL --name ADMIN_NAME
docker compose --env-file deploy/.env ps
curl -fsS https://YOUR_DOMAIN/health/ready
```

preflight의 `forward_data_gate`가 `false`이면 배포를 강행하지 않는다. 일일 공급자 데이터에서
누락 또는 불가능한 OHLC가 발견됐다는 뜻이며 scheduler가 15분 뒤 다시 받는다. 이 상태에서도
보유 종목 시세 확인과 손절은 계속되지만, 편향을 만들 수 있는 신규 리밸런싱과 엄격 PIT
백테스트는 중단된다. `validation_report.json`의 blocker가 0이 된 뒤 다시 preflight를 실행한다.
수동 재시도는 `python -m cloud_app.data_refresh`로 실행할 수 있다.

관리자 생성 명령은 비밀번호를 터미널에서만 입력받는다. 셸 히스토리나 `.env`에 관리자
비밀번호를 남기지 않는다.

app preflight의 `credential_broker=true`는 app 역할 토큰으로 broker에 연결하고 broker가 두
key round trip을 완료했다는 뜻이다. paper-worker startup은 paper 역할 토큰으로 market key
round trip을 별도로 확인한다. 어느 쪽이든 실패하면 배포를 중단하며 로컬 암호화로 fallback하지
않는다.

기존 DB에 prefix 없는 legacy 또는 `v2:` credential이 있다면 모든 DB writer를
중지하고, 전용 pre-migration dump의 SHA-256과 PostgreSQL custom-format을 검증한
뒤에만 1회성 migration을 실행한다. 과거 AI/시세 root는 환경변수나
명령행이 아니라 TTY prompt로 입력한다. migration은 앱 VM에서 실행하지 않는다.
broker instance principal과 앱 PostgreSQL에 대한 일시적 private 연결을 함께 가진
단발성 migration 컨테이너에서만 실행하고, 완료 직후 DB 경로와 임시 컨테이너를 제거한다.
모든 필드는 한 transaction으로 KMS 재암호화·검증되며 실패하면 rollback된다.

```bash
docker compose --env-file deploy/.env stop app paper-worker backtest-worker scheduler
docker compose --env-file deploy/.env run --rm --no-deps --entrypoint /bin/sh backup \
  /backup/backup-once.sh
# 아래 명령은 app VM이 아니라 private DATABASE_URL을 임시로 받은 broker/migration VM에서 실행한다.
docker compose --env-file deploy/credential-broker.env \
  -f compose.credential-broker.yaml run --rm -e DATABASE_URL credential-broker \
  python -m cloud_app.manage migrate-credentials-to-oci \
  --confirm MIGRATE_TO_OCI_KMS --backup-confirmed
docker compose --env-file deploy/.env up -d app paper-worker backtest-worker scheduler
```

`Verified pre-migration backup` 명령이 실패하거나 출력된 dump 파일을 별도의
암호화된 보관소에 복사하지 못했으면 `--backup-confirmed`를 붙이지 않는다.
새 버전의 수동 검증과 정한 rollback window가 끝날 때까지 dump, `.sha256`,
예전 root를 생산 runtime 밖의 암호화된 저장소에 보관한다. 새 app/worker
환경에는 예전 root나 OCI endpoint/key OCID를 절대 다시 주입하지 않는다.

마이그레이션 후 rollback이 필요하면 먼저 모든 서비스를 중지하고 아래
`백업과 복구` 절차로 해당 `quantclub_pre_kms_*.dump`를 복원한 뒤에만
이전 image로 되돌린다. 이전 image의 읽기에 필요한 예전 root는 구 image의 일시적
환경에만 주입하고, 새 image와 혼용하지 않는다. rollback window가 지나고
실전 복구 검증이 끝난 뒤 보관 정책에 따라 dump와 예전 root를 폐기한다.

수동 검증이 끝나면 재부팅 후에도 자동 기동하도록 systemd unit을 설치한다.

```bash
sudo install -m 0644 deploy/systemd/milkyway.service /etc/systemd/system/milkyway.service
sudo systemctl daemon-reload
sudo systemctl enable milkyway.service
sudo systemctl restart milkyway.service
```

## AI 연결

회원은 설정 화면에서 OpenAI 또는 Anthropic 공급자, 모델 ID와 자신의 API 키를 입력한다.
키는 broker가 OCI Vault AES-GCM으로 사용자·공급자 context에 결합해 서버 데이터베이스에
저장하며, 전략 생성도 broker 내부의 고정 공급자 endpoint에서 수행한다. 앱은 암호문과 hint만
저장하고 키 원문·KMS 권한·공급자 access token을 받지 않는다.

공용 로컬 AI를 사용할 때는 `COMPOSE_PROFILES=local-ai`, `LOCAL_AI_ENABLED=true`,
`LOCAL_AI_BASE_URL=http://ai:8080/v1`, `LOCAL_AI_MODEL=Qwen2.5-Coder-7B-Instruct-GGUF`와
20자 이상의 무작위 `LOCAL_AI_API_KEY`를 broker VM의 `credential-broker.env`에 설정한다.
`COMPOSE_PROFILES`를 그 파일에 두어야
systemd가 서버 재부팅 후에도 모델 컨테이너를 다시 실행한다. 그 다음 로컬 AI 프로필을 포함해
실행한다.

```bash
docker compose --env-file deploy/credential-broker.env \
  -f compose.credential-broker.yaml --profile local-ai up -d --build
docker compose --env-file deploy/credential-broker.env \
  -f compose.credential-broker.yaml --profile local-ai logs -f ai
```

첫 실행은 Q4_K_M 모델 약 5GB를 내려받아 `local-ai-model-cache` 볼륨에 보관한다. 모델
컨테이너는 공인 포트를 열지 않고 broker 내부망에서만 broker가 접근한다. 회원은 로컬 주소나
서버 API 키를 입력할 수 없으며 설정에서 `로컬 AI`만 선택한다. 기본 두 개의 동시 생성
슬롯을 사용하며 앱은 최대 네 요청만 모델 서버에 진입시켜 두 요청까지만 대기시킨다. 그
이상의 동시 요청은 HTTP 429로 빠르게 재시도를 안내한다. OCI A1 4 OCPU에서는 생성 속도가 느릴 수
있으므로 클럽 시작 전에 실제 전략 프롬프트로 부하 테스트한다.

기본 모델 URL은 승인한 Hugging Face commit `13fb94bfda8c8cf22497dc57b78f391a9acb426a`에
고정되어 있다. 모델을 교체할 때 `main` 링크를 쓰지 말고 새 revision의 고정 URL과 모델 ID를
함께 기록한다.

## 실시간 시세 전환

기본 `QUOTE_PROVIDER=mock`은 마지막 완료 일봉을 사용한다. KIS 시세로 전환하려면
계약/이용약관상 30명 웹 공유가 허용되는지 먼저 확인한 뒤에만 broker VM의
`credential-broker.env`에 다음 값을 설정한다.

```dotenv
QUOTE_PROVIDER=kis
MARKET_DATA_SHARING_ALLOWED=true
BROKER_API_KEY=...
BROKER_API_SECRET=...
BROKER_ACCOUNT_ID=...
```

worker는 종목 목록만 broker에 보내며, broker가 공용 KIS credential로 조회한 정규화 시세만
반환한다. provider key/token은 worker에 전달되지 않는다. 각 사용자 계좌는 같은 관측값을
읽으며, 허용 확인 플래그가 없으면 broker 시작 검사가 의도적으로 실패한다.

## 운영 확인

```bash
docker compose --env-file deploy/.env ps
docker compose --env-file deploy/.env logs --since 30m app paper-worker backtest-worker scheduler
curl -fsS https://YOUR_DOMAIN/health/live
curl -fsS https://YOUR_DOMAIN/health/ready
ls -lh backups
```

`ready`의 `worker=false`는 웹은 열리지만 신규 시세·페이퍼 체결이 진행되지 않는다는 뜻이다.
즉시 worker 로그와 브로커 인증을 확인한다. `data_gate=false`면 readiness는 HTTP 503을
반환하며 신규 리밸런싱이 정지된다. scheduler는 미국 거래일 ET 18:30 이후
스냅샷과 완료 일봉을 갱신하며 실패 시 15분 후 재시도한다.

## 백업과 복구

- PostgreSQL custom-format dump가 6시간마다 `backups/`에 원자적으로 생성된다.
- 14일이 지난 dump는 자동 삭제된다.
- `quantclub_pre_kms_*.dump`는 credential rollback 전용이므로 14일 자동 삭제에서
  제외된다. 정한 rollback window 종료 후 수동으로 파기한다.
- OCI 부트 볼륨 백업을 별도로 켜서 VM/로컬 dump 동시 손실에 대비한다.
- 복구 대상 리전에서 두 Vault key가 enabled 상태이며 broker 인스턴스 dynamic group이 사용할
  수 있는지 함께 확인한다. DB dump만 있고 Vault key 접근을 잃으면 회원 credential은 복구할
  수 없다.
- 매주 한 번 별도 테스트 DB에서 restore를 확인한다.

복구는 현재 DB를 교체하므로 유지보수 중에만 수행한다. `deploy/restore.sh`는 명시적인
`RESTORE_CONFIRM=quantclub`과 `/backups/quantclub_*.dump` 경로가 아니면 거부한다.

```bash
docker compose --env-file deploy/.env stop app paper-worker backtest-worker scheduler
docker compose --env-file deploy/.env run --rm --no-deps --entrypoint /bin/sh \
  -e RESTORE_CONFIRM=quantclub backup /restore.sh \
  /backups/quantclub_YYYYMMDDTHHMMSSZ.dump
docker compose --env-file deploy/.env up -d
```

## 무중단 범위

이 Compose 구성은 컨테이너 crash와 VM 재부팅에는 자동 복구되지만, 단일 OCI 서울 AD나
부트 볼륨 전체 장애까지 무중단으로 막지는 않는다. 두 앱 서버가 하나의 PostgreSQL을
공유하면 웹/worker 프로세스는 lease와 멱등키 덕분에 중복 없이 확장할 수 있지만 DB가
단일 장애점으로 남는다. 실제 zone/region 무중단이 필요하면 배포 전에 다음 중 하나가
추가되어야 한다.

1. 다중 AZ 관리형 PostgreSQL + 두 앱 노드 + 외부 load balancer
2. 3개 이상의 quorum 노드로 구성한 PostgreSQL 자동 failover

5주 동아리 운영에서는 앱+broker 두 OCI 노드, 6시간 DB dump, OCI 부트 볼륨 백업, 외부
uptime alert가 현실적인 기준이다. “절대 중단 없음”은 어느 단일 VM 구성도 보장하지 않는다.
