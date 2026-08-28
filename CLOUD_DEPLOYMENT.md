# Milkyway Cloud Deployment Gate

이 문서는 30명, 5주간 사용할 페이퍼 트레이딩 플랫폼의 단일 기준 운영 절차다.
기존 macOS `cron -> watchdog.sh` 실거래 봇과 클라우드 페이퍼 플랫폼은 별개다.

## 현재 준비된 범위

- 초대 코드 기반 회원가입, scrypt 비밀번호 해시, HttpOnly 서명 세션, CSRF 방어
- 사용자별 전략·백테스트·페이퍼 계좌 분리
- 사용자별 암호화 AI API 키, AI 출력 JSON 검증 및 임의 코드 실행 차단
- 모든 전략의 `backtest_core.run_backtest()` 공통 원장 강제
- PostgreSQL 작업 큐, 중복 체결 방지 키, 단일 leader lease
- 보유/후보 종목을 합친 1회 시세 수집 후 사용자 계좌에 공유
- 첫 인증 스냅샷 이전 성과에 탐색용·생존편향 경고 표시
- 일일 공식 거래소 스냅샷, 목록 이탈 alert, 완료 세션 가격 갱신 및 해시 검증
- 앱·worker·scheduler·PostgreSQL·Caddy·6시간 DB 백업 컨테이너
- HTTPS 자동 인증서, 보안 헤더, readiness/liveness, worker heartbeat

외부에서 채워야 하는 값은 도메인/DNS, OCI 인스턴스, 브로커 키, 시세 재사용 허용
확인과 서버 비밀값뿐이다. 회원의 AI API 키는 설정 화면에서 입력하고 암호화 저장한다.

## 권장 OCI 인스턴스

- Ubuntu 24.04 ARM64, Ampere A1 4 OCPU/24GB
- 부트 볼륨 최소 100GB, 자동 부트 볼륨 백업 활성화
- 예약 공인 IP 사용
- OCI Network Security Group ingress:
  - TCP 22: 운영자 고정 IP만
  - TCP/UDP 443: 동아리 사용 위치 또는 인터넷
  - TCP 80: HTTPS 인증서 발급/리다이렉트
- PostgreSQL 5432와 앱 8000은 절대 공인 ingress로 열지 않는다.

`deploy/oci/cloud-init.yaml`을 인스턴스 생성 시 cloud-init으로 넣으면 Docker,
fail2ban, 자동 보안 업데이트가 설치된다. 저장소는 `/opt/milkyway`에 배치한다.

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

```bash
cd /opt/milkyway
cp deploy/.env.example deploy/.env
mkdir -p backups models
chmod 700 backups models
sudo chown -R 10001:10001 data_cache
```

`deploy/.env`에서 다음 값을 반드시 교체한다.

- `PUBLIC_BASE_URL`, `DOMAIN`, `ALLOWED_HOSTS`
- `POSTGRES_PASSWORD`와 그 값을 URL 인코딩한 `DATABASE_URL`
- `SESSION_SECRET`: `openssl rand -hex 32` 결과
- `CLUB_INVITE_CODE`: 동아리 전용 임의 문자열

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

수동 검증이 끝나면 재부팅 후에도 자동 기동하도록 systemd unit을 설치한다.

```bash
sudo install -m 0644 deploy/systemd/milkyway.service /etc/systemd/system/milkyway.service
sudo systemctl daemon-reload
sudo systemctl enable milkyway.service
sudo systemctl restart milkyway.service
```

## 사용자별 AI API 연결

`AI_CREDENTIAL_SECRET`에는 세션 비밀값과 다른 32자 이상의 무작위 값을 설정한다.
회원은 설정 화면에서 OpenAI 또는 Anthropic 공급자, 모델 ID와 자신의 API 키를 입력한다.
키는 서버 데이터베이스에 암호화되어 저장되고 전략 생성 요청에만 복호화해 사용한다.
키 원문은 API 응답이나 화면에 다시 표시하지 않는다.

## 실시간 시세 전환

기본 `QUOTE_PROVIDER=mock`은 마지막 완료 일봉을 사용한다. KIS 시세로 전환하려면
계약/이용약관상 30명 웹 공유가 허용되는지 먼저 확인한 뒤에만 다음 값을 설정한다.

```dotenv
QUOTE_PROVIDER=kis
MARKET_DATA_SHARING_ALLOWED=true
BROKER_API_KEY=...
BROKER_API_SECRET=...
BROKER_ACCOUNT_ID=...
```

worker는 모든 활성 계좌의 보유·다음 후보 ticker를 합집합으로 만든 후 종목별 한 번만
조회하고 `quotes` 테이블에 기록한다. 각 사용자 계좌는 같은 관측값을 읽는다. 허용 확인
플래그가 없으면 production 시작 검사가 의도적으로 실패한다.

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
- OCI 부트 볼륨 백업을 별도로 켜서 VM/로컬 dump 동시 손실에 대비한다.
- 매주 한 번 별도 테스트 DB에서 restore를 확인한다.

복구는 현재 DB를 교체하므로 유지보수 중에만 수행한다. `deploy/restore.sh`는 명시적인
`RESTORE_CONFIRM=quantclub`과 `/backups/quantclub_*.dump` 경로가 아니면 거부한다.

```bash
docker compose --env-file deploy/.env stop app paper-worker backtest-worker scheduler
docker compose --env-file deploy/.env run --rm --entrypoint /restore.sh \
  -e RESTORE_CONFIRM=quantclub backup /backups/quantclub_YYYYMMDDTHHMMSSZ.dump
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

5주 동아리 운영에서는 단일 유료 OCI 노드, 6시간 DB dump, OCI 부트 볼륨 백업, 외부
uptime alert가 현실적인 기준이다. “절대 중단 없음”은 어느 단일 VM 구성도 보장하지 않는다.
