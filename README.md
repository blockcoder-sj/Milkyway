# Milkyway

개인 PC에서 미국 주식 전략을 만들고, 본인 증권사 시세로 가상 매매 기록을 쌓는 도구입니다.
**증권사에 매매 주문을 보내지 않습니다.** 주가는 한국투자증권(KIS)·토스증권 API에서
조회하고 체결·현금·보유 수량은 이 PC의 로컬 원장에 저장합니다.

## AI 가설 연구

전략 화면에서 가설 대화 → 버전 저장 → 개발·검증 비교 → 개선 → 페이퍼 운용을
진행할 수 있습니다. 기본 모델은 `gpt-5.4-mini`, 추론은 `none`입니다.
`.env`에 본인 키를 넣고 **요청마다 1회 호출을 승인**합니다. 자동매매에는 AI 호출이 없습니다.
[키 설정·전체 흐름·지원 범위](docs/AI_RESEARCH_GUIDE.md)

## 시장 화면

한국·미국 주요 지수, 환율, 선물·원자재, 미국 11개 섹터와 한국 주요 8개 업종 지수를
표시합니다. 증권사 연결 전에도 공개 참고 데이터를 1분마다 수집하며 출처·기준 시각·
전일 대비·지연 상태를 함께 표시합니다. [항목·데이터 의미·구조](docs/MARKET_DASHBOARD.md)

초보자용 배포본은 섹터 등락 요약만 표시합니다. 섹터 카드는 클릭되지 않으며 기업
분석·재무 자료·관계도·의미 검색 모델을 포함하거나 자동 수집하지 않습니다.
주요 지수·환율의 상세 차트와 전략·백테스트·페이퍼 운용은 사용할 수 있습니다.

## 학회원 개인용 빠른 시작

Docker Desktop(Windows/macOS) 또는 Docker Engine + Compose(Linux)를 실행하고,
저장소를 내려받습니다. Git 대신 GitHub의 **Code → Download ZIP**도 가능합니다.
비공개 저장소라면 먼저 저장소 접근 권한이 필요합니다.

```bash
git clone --depth 1 --branch codex/ai-research-workflow https://github.com/blockcoder-sj/Milkyway.git
cd Milkyway
docker compose -f compose.personal.yaml up -d --build
```

1. <http://localhost:8080>을 열면 가입·로그인 없이 전략 화면으로 들어갑니다. 기존 계정이 하나 있으면 기록을 그대로 사용하고, 새 설치에서는 로컬 계정을 자동 생성합니다.
2. 프로필에서 본인 KIS App Key/Secret 또는 토스 Client ID/Secret을 연결합니다. AI 키는 필요 없습니다.
3. AI 연구 대화에서 투자 가설·선정 기준·보유 수·주기를 설명하고 전략을 저장합니다. 일반 미국 주식 전략은 전체 시장 자동 선별을 기본으로 합니다. AI로 새 전략을 작성할 때는 본인 AI 키와 호출 승인이 필요합니다.
4. 미국 전체 일봉 분석이 끝나면 탐색용 백테스트를 실행하고 페이퍼 계좌를 만듭니다. 운용 기간의 기본값은 7일이며, 종료 시 추가 체결을 자동 중지합니다.
5. 미국 정규장에 PC와 Docker를 켜 둡니다. 화면의 운영 상태·계좌별 대기 사유·최근 시세를 확인합니다. 시장 탭의 공개 참고 시세는 페이퍼 체결에 사용하지 않습니다.

PC를 껐다 켰거나 실행이 멈췄다면 Mac의 `Milkyway-Start.command`, Windows의
`Milkyway-Start.cmd`를 실행합니다. 이 실행기에는 Python 3.9 이상이 필요합니다.
열린 화면에서는 **운용 상태 → 자동매매 복구·재개** 한 번으로 프로세스와 선택 계좌를
점검하고 기존 기록을 이어갑니다. [상태 표시·인터넷 끊김·시작과 복구](docs/PERSONAL_RECOVERY.md)

[처음부터 따라 하는 사용설명서·문제 해결](docs/Milkyway_초보자_사용설명서.md) ·
[검증 범위와 남은 실환경 확인](docs/Milkyway_검수보고서.md)

- 토스 연결은 거래 가능한 미국 보통주·ADR·REIT 전체를 매일 분석합니다. 현재 5,915개이며, 수는 공급자 목록에 따라 바뀝니다. ETF·우선주·워런트는 제외합니다. 티커를 미리 고를 필요가 없습니다.
- 전체 분석과 동시 가격 감시는 별도입니다. 보유·선정 종목만 감시하며 토스는 200개, KIS는 20개 한도입니다. 직접 종목을 지정한 기존 전략은 유지되며 저장된 선택 종목의 합계는 최대 100개입니다.
- 전체 시장 분석 일봉은 토스에서, 선정·보유 종목의 기업행사 확인 자료는 Yahoo에서 갱신합니다. 실시간성 가격은 **본인 증권사 REST 시세 조회**를 사용합니다.
  15초 간격으로 조회를 시도하며 KIS 모의 환경은 5종목씩 순환합니다. 전체 20종목은 통상
  약 1~2분에 갱신됩니다. 거래소 원시 tick 스트림이 아니며 시세 지연 여부는 계정 권한에 따릅니다.
- 개인 선택 종목의 백테스트는 탐색용입니다. 과거 전체 상장 종목을 인증한 무편향 성과로 표시하지 않습니다.
- 기록은 재시작 후 유지됩니다. 계좌의 `삭제`는 해당 잔고·체결·자산 기록을 삭제합니다. 전략을 삭제하려면 연결된 계좌를 먼저 삭제해야 합니다. 삭제 전에 CSV로 내보낼 수 있습니다. 직접 규칙 입력 폼은 제거했습니다.
- 6시간마다 별도 Docker 볼륨에 백업합니다. 다른 디스크에도 복사해야 PC/디스크 고장에 대비할 수 있습니다.

```bash
# 정상 중지: 기록 유지
docker compose -f compose.personal.yaml stop
# 재개
docker compose -f compose.personal.yaml up -d
# 진단
docker compose -f compose.personal.yaml exec app python -m cloud_app.local_ops doctor
# 즉시 백업 + PC로 복사
docker compose -f compose.personal.yaml exec backup python -m cloud_app.local_ops backup
docker compose -f compose.personal.yaml cp backup:/app/backups ./backups
```

백업에는 암호화된 자격증명과 복호화 키가 함께 포함되므로 개인 파일로 보관합니다.
복원·포트 충돌·비밀번호 분실·API 연결 실패는 사용설명서의 절차를 따릅니다.
**Docker 볼륨을 지우거나 `down -v`를 실행하면 기록이 삭제됩니다.**
브라우저를 닫아도 실행은 계속되지만 PC 절전·종료·Docker 중지는 거래를 멈춥니다.
재연결 후 정상 처리하며, 꺼져 있던 시간의 실시간 체결을 소급하여 만들지는 않습니다.

개인용 구성은 `127.0.0.1`에만 열립니다. 이 PC를 사용하는 사람은 비밀번호 없이 기록과 설정에 접근할 수 있습니다. 공유 컴퓨터·포트 포워딩·공개 서버용 구성이 아닙니다.
중앙 서버 배포 자체가 불가능한 것은 아니지만, 사용자 인증·키 격리·운영 보안이 필요한 별도 설계입니다.
아래 기존 클라우드 구성의 보안 검증과 운영 gate는 그대로 유지합니다.

## 기존 클라우드 구성

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

**공개 서버 배포와 그 서버에 회원 키를 모으는 운영은 현재 NO-GO다.** 로컬 테스트는 실제 두 VM의 KMS allow/deny,
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

### API 없이 화면·백테스트를 살펴보는 합성 데이터 모드

```bash
docker compose -f compose.local.yaml up -d --build
```

이 별도 모드는 ALPHA/BETA/GAMMA 합성 일봉을 사용하는 탐색용 백테스트 연습이다.
실제 시세 수신과 실시간 페이퍼 운용은 앞의 개인용 구성으로 실행한다.
합성 데이터는 PIT 인증 데이터가 아니며 실제 투자 성과가 아니다.

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

### 시장 상세 화면과 AI 평가

- [지수·섹터·환율·선물 상세 화면과 출처](docs/MARKET_DETAILS.md)
- [승인된 AI 대화 5회 평가 결과](docs/AI_CHAT_EVALUATION.md)
