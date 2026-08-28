# Milkyway

Milkyway Quant Trading Lab은 퀀트 동아리 회원이 자연어 전략을 안전한 전략 규격으로
변환하고, 공통 체결 엔진으로 백테스트한 뒤 페이퍼 계좌에서 운용할 수 있는 웹 플랫폼이다.

## 주요 기능

- 초대 코드 기반 계정과 사용자별 전략·백테스트·페이퍼 계좌
- 미국·한국 시장 지표, 섹터 흐름과 경제 뉴스 화면
- OpenAI·Anthropic 또는 서버 공용 로컬 AI를 이용한 전략 코드 생성
- 사용자별 API 키 암호화 저장과 연결 해제
- 회원별 한국투자증권·토스증권 시세 API 자격증명 검증·암호화 저장
- 미래참조를 제한하는 전략 DSL과 공통 백테스트·페이퍼 체결 규칙
- Docker, PostgreSQL, Caddy, worker, scheduler와 백업 구성

AI 웹 구독 계정은 사용하지 않는다. OpenAI·Anthropic을 선택한 회원은 설정 화면에 자신의
API 키를 입력하며, 해당 키는 전략 생성 요청에만 사용된다. 운영 환경에서는 반드시
`AI_CREDENTIAL_SECRET`을 세션 비밀값과 다른 32자 이상의 무작위 값으로 설정한다.

설정의 `증권사 시세 API`에서 회원이 본인의 KIS App Key·App Secret과
실전/모의 환경을 선택할 수 있다. 저장 전 KIS OAuth 토큰 발급으로 실제 인증하며,
원문은 응답이나 브라우저에 다시 노출하지 않는다. 이 연결은 키 소유자의 개인
페이퍼 트레이딩 체결가 용도이며, 다른 회원에게 시세를 공유하는 공용 피드로 사용하지 않는다.
공용 실시간 표시와 페이퍼 체결은 외부 표시·재배포·비표시 사용이 명시적으로 허용된
별도 데이터 계약을 전제로 한다.

토스증권은 `토스증권 WTS > 설정 > Open API`에서 발급한 Client ID·Client Secret을
사용한다. 토스증권 설정의 허용 IP에는 Milkyway 서버의 고정 공인 IP를 먼저 등록해야 한다.
현재 연결기는 주문 API를 포함하지 않고 국내·미국 주식 현재가를 한 요청당 최대 200종목씩
REST로 조회해 해당 회원의 내부 페이퍼 계좌에만 저장한다. 토스증권이 제공하는 실시간
WebSocket은 후속 고빈도 화면 갱신에 사용할 수 있지만, 현재 페이퍼 worker는 안정적인
일괄 현재가 조회를 기본으로 한다.

시세 경로는 용도별로 분리한다.

- TradingView Widget은 사이트 표시에만 사용하고 Widget 데이터를 추출해 페이퍼 엔진에 넣지 않는다.
  TradingView는 일반 시세 API/다운로드를 제공하지 않는다.
- 회원 KIS 키는 `member_quotes` 테이블에 회원 ID별로 격리하고 해당 회원의 페이퍼 계좌에만
  적용한다. 현재 엔진은 REST 주기 조회이며 초단위 푸시가 필요하면 KIS WebSocket 수집기를 별도로
  운영해야 한다.
- 모든 회원에게 보이는 네이티브 실시간 지수·종목과 페이퍼 체결을 하나의 피드로 제공하려면
  공급자에게 외부 표시, 재배포, 비표시 사용 권한을 모두 확인한다.

`로컬 AI`는 회원별 키 대신 운영자가 관리하는 공용 모델 서버를 사용한다. 기본 배포 구성은
llama.cpp의 OpenAI 호환 API와 `Qwen2.5-Coder-7B-Instruct-GGUF` Q4_K_M 모델이다. 모델
엔드포인트는 서버 환경변수로만 정하며 사용자가 임의 URL을 입력할 수 없다. 활성화하려면
`deploy/.env`에서 `COMPOSE_PROFILES=local-ai`, `LOCAL_AI_ENABLED=true`와 임의의
`LOCAL_AI_API_KEY`를 설정한 뒤 다음과 같이 로컬 AI 프로필을 함께 실행한다. 첫 실행에서는
약 5GB 모델 다운로드와 로딩 때문에 수 분이 걸릴 수 있다.

기본 `LOCAL_AI_MODEL_URL`은 검증한 Hugging Face revision에 고정되어 새 서버에서도 같은
GGUF를 받는다. 운영자가 모델을 바꿀 때는 모델 ID와 revision 고정 URL을 함께 변경한다.

```bash
docker compose --env-file deploy/.env --profile local-ai up -d --build
```

로컬 AI는 별도 API 호출료가 없지만 CPU/RAM을 사용한다. 7B Q4 모델 기준으로 앱·데이터베이스와
함께 운영하려면 16GB보다 24GB RAM 구성이 안전하며, 동시 생성은 기본 2개 슬롯으로 제한한다.

## 로컬 실행

현재 데이터 스냅샷은 Git에서 제외되지만 이 로컬 프로젝트의 `data_cache/`에는 복사되어
있다. Docker Desktop이 실행 중인 상태에서 다음 명령을 사용한다.

```bash
cp deploy/.env.example deploy/.env
# deploy/.env의 비밀번호, 세션/AI 암호화 비밀값과 초대 코드를 변경
docker compose --env-file deploy/.env up -d --build
```

로컬 단일 컨테이너 개발 실행은 다음과 같다.

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
docker run --rm milkyway:test python -m unittest discover -s tests -v
```

클라우드 배포와 데이터 준비 절차는 [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)를 참고한다.
