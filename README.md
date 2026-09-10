# Milkyway

Milkyway Quant Trading Lab은 퀀트 동아리 회원이 자연어 전략을 안전한 전략 규격으로
변환하고, 공통 체결 엔진으로 백테스트한 뒤 페이퍼 계좌에서 운용할 수 있는 웹 플랫폼이다.

## 주요 기능

- 수신자 이메일 결합 1회 초대 기반 계정과 사용자별 전략·백테스트·페이퍼 계좌
- 미국·한국 시장 지표, 섹터 흐름과 경제 뉴스 화면
- 운영자 소유 OpenAI·Anthropic 키 또는 서버 공용 로컬 AI를 이용한 전략 코드 생성
- 각 회원의 증권사 키로 수집하는 개인 페이퍼 트레이딩 시세
- 미래참조를 제한하는 전략 DSL과 공통 백테스트·페이퍼 체결 규칙
- Docker, PostgreSQL, Caddy, worker, scheduler와 백업 구성

회원은 AI 키를 입력하지 않고 동아리 공용 AI를 사용한다. 증권사 키는 별도 broker VM의
`/credentials` 페이지에서 본인 계정으로 등록·교체·삭제한다. 공개 앱을 거치지 않은 키를
broker가 검증하고 OCI KMS 암호문으로 저장하며, 앱·worker는 원문 키나 암호문을 받지 않는다.

독립 발급된 불투명 회원 세션과 PostgreSQL RLS가 회원 데이터를 분리한다. 공용 AI에는
회원·프롬프트에 결합된 일회용 허가가, worker에는 broker가 선택한 계좌·종목에만 유효한
작업 권한이 필요하다. 개인 키로 받은 시세는 해당 회원의 계좌에만 사용하며 공용 시세로
대체하지 않는다. TradingView Widget은 화면 표시용이며 페이퍼 엔진 입력으로 추출하지 않는다.
REST 현재가 polling을 사용하며 WebSocket 체결 스트림이나 실거래 주문은 지원하지 않는다.

**공개 배포·실제 회원 키 입력은 현재 NO-GO다.** 로컬 테스트는 실제 두 VM의 KMS allow/deny,
Vault secret release와 OCI Audit 검증을 대신하지 않는다. 현재 증거와 남은 gate는
[SECURITY_REMEDIATION_STATUS.md](SECURITY_REMEDIATION_STATUS.md)를 확인한다.

공용 AI는 `SHARED_AI_PROVIDER`, `SHARED_AI_MODEL`과 `OCI_SHARED_AI_SECRET_ID`로 고정한다.
운영 환경에서 원격 OpenAI/Anthropic 키는 broker VM의 instance principal이 OCI Vault에서
조회한다. 평문 키 환경변수나 키 파일은 시작 전에 거부한다. `local`을 선택하면 운영자가 관리하는 공용 모델 서버를
사용한다. 기본 배포 구성은
llama.cpp의 OpenAI 호환 API와 `Qwen2.5-Coder-7B-Instruct-GGUF` Q4_K_M 모델이다. 모델
엔드포인트는 서버 환경변수로만 정하며 사용자가 임의 URL을 입력할 수 없다. 활성화하려면
브로커 VM의 `deploy/credential-broker.env`에서 `COMPOSE_PROFILES=local-ai`,
`LOCAL_AI_ENABLED=true`와 임의의 키 파일을 가리키는
`LOCAL_AI_API_KEY_PATH`를 설정한 뒤 다음과 같이 로컬 AI 프로필을 함께 실행한다. 첫 실행에서는
약 5GB 모델 다운로드와 로딩 때문에 수 분이 걸릴 수 있다.

기본 `LOCAL_AI_MODEL_URL`은 검증한 Hugging Face revision에 고정되어 새 서버에서도 같은
GGUF를 받는다. 운영자가 모델을 바꿀 때는 모델 ID와 revision 고정 URL을 함께 변경한다.

```bash
docker compose --env-file deploy/credential-broker.env \
  -f compose.credential-broker.yaml --profile local-ai up -d --build
```

로컬 AI는 별도 API 호출료가 없지만 CPU/RAM을 사용한다. 7B Q4 모델 기준으로 앱·데이터베이스와
함께 운영하려면 16GB보다 24GB RAM 구성이 안전하며, 동시 생성은 기본 2개 슬롯으로 제한한다.

## 실행

production은 공개 앱 VM과 broker VM을 분리하고 PostgreSQL TLS, 역할별 DB 계정,
독립 인증 발급, KMS/Vault 및 검토한 데이터 세대를 함께 설정한다. 실제 배포는
[CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)의 **DB → broker → 앱·worker** 순서를 따른다.
기존 env·DB·runtime·Docker 볼륨을 덮어쓰거나 초기화하지 않는다.

### 개인 PC 로컬 실행

GitHub에서 내려받은 각 사본은 서로 완전히 독립적으로 실행된다. Docker Desktop(또는 Docker
Engine과 Compose plugin)만 설치한 뒤 다음 명령을 실행한다.

```bash
git clone https://github.com/blockcoder-sj/Milkyway.git
cd Milkyway
docker compose -f compose.local.yaml up --build
```

브라우저에서 <http://localhost:8080>을 연다. 첫 실행은 세 개의 합성 종목과 약 1년치의
결정론적 OHLCV 데이터를 로컬 Docker 볼륨에 생성한다. 앱·백테스트 worker·페이퍼 worker가
함께 실행되므로 계정 생성, 전략 저장, 탐색용 백테스트와 mock 페이퍼 계좌 흐름을 확인할 수
있다. 이 데이터는 실제 시세가 아니며 strict/PIT 백테스트, 투자 판단, 성과 주장에 사용할 수
없다. 로컬 기본 구성은 실행 중 API 키, 증권사 연결, OCI 및 외부 네트워크 호출을 사용하지 않는다.

중지는 `docker compose -f compose.local.yaml down`으로 한다. 로컬 데이터까지 처음 상태로
지우려는 경우에만 `docker compose -f compose.local.yaml down -v`를 사용한다.

실제 인증된 데이터셋으로 연구하려면 별도 `data_cache/`를 준비하고 아래의 개발 실행 경로를
사용한다. `data_cache/`, `runtime/`, `.env`와 개인 키 파일은 Git에 포함하지 않는다.

```bash
docker build -t milkyway:local .
docker run --rm -p 127.0.0.1:8080:8000 \
  -e APP_ENV=development \
  -e DATASET_DIR=/app/data_cache/backtest_datasets/2026_equities_pit_20260824 \
  -v "$PWD/data_cache:/app/data_cache:ro" \
  milkyway:local uvicorn cloud_app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

## 테스트

```bash
docker build -t milkyway:test .
docker run --rm -e APP_ENV=development milkyway:test python -m unittest discover -s tests -v
```

실제 PostgreSQL 역할 초기화·업그레이드·TLS·RLS·HTTP 흐름 및 암호화 복구는 별도의
임시 DB에서 검증한다. 기존 DB나 Docker 볼륨을 사용하지 않는다.

```bash
python3 tests/run_postgres_checks.py --image milkyway:test
```

클라우드 배포와 데이터 준비 절차는 [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)를 참고한다.
