# Milkyway

Milkyway Quant Trading Lab은 퀀트 동아리 회원이 자연어 전략을 안전한 전략 규격으로
변환하고, 공통 체결 엔진으로 백테스트한 뒤 페이퍼 계좌에서 운용할 수 있는 웹 플랫폼이다.

## 주요 기능

- 초대 코드 기반 계정과 사용자별 전략·백테스트·페이퍼 계좌
- 미국·한국 시장 지표, 섹터 흐름과 경제 뉴스 화면
- OpenAI 또는 Anthropic API를 이용한 전략 코드 생성
- 사용자별 API 키 암호화 저장과 연결 해제
- 미래참조를 제한하는 전략 DSL과 공통 백테스트·페이퍼 체결 규칙
- Docker, PostgreSQL, Caddy, worker, scheduler와 백업 구성

AI 웹 구독 계정은 사용하지 않는다. 회원이 설정 화면에서 공급자, 모델 ID와 자신의 API
키를 입력하면 해당 키가 전략 생성 요청에만 사용된다. 운영 환경에서는 반드시
`AI_CREDENTIAL_SECRET`을 세션 비밀값과 다른 32자 이상의 무작위 값으로 설정한다.

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
