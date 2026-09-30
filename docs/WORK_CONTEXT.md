# Milkyway 작업 맥락

저장일: 2026-09-30 (Asia/Seoul). 사용자 요청으로 다음 작업을 위한 인수인계를
저장했다. 아래 상태는 마지막 확인 당시의 기록이며 현재 상태 확인을 대신하지 않는다.
비밀 키, 환경 변수 값, 개인 원장 데이터는 포함하지 않는다.

## 저장소와 실행

- 작업 폴더: 프로젝트 폴더 아래 `Milkyway` 하나.
  이전 `Milkyway-local-ready`는 별도 제품이 아니라 연결된 Git worktree였으며
  통합했다. 이전 작업 백업은 체크아웃 밖 `../output/backups/`에 보존했다.
- GitHub: `https://github.com/blockcoder-sj/Milkyway.git`.
  작업 브랜치: `codex/ai-research-workflow`.
- 마지막 기능 커밋: `8c3bda3dd0d6369a93c7e70afbff718c00da9b57`.
  GitHub 푸시와 로컬/원격 브랜치 일치를 확인했다. 맥락 문서 저장은 후속 커밋이다.
- 개인 로컬 앱: `http://127.0.0.1:8080`, `compose.personal.yaml`,
  이미지 `milkyway-personal:local`. Supabase가 필요한 구성이 아니다.
- 마지막 배포에서 앱 health 및 7개 서비스 시작을 확인했다:
  app, paper-worker, backtest-worker, personal-data, market-data,
  market-details, backup. 실행/헬스 상태는 다음 작업 시작 시 다시 확인한다.
- 사용자 Docker 데이터와 백업 볼륨을 보존한다. `down --volumes` 금지.
  기존 미커밋 변경, runtime 데이터, 키 설정을 덮어쓰지 않는다.

## 반드시 유지할 사용자 규칙

- 각 구현 마일스톤 끝에 기능·성능·코드·보안 검토를 하고 결과와 한계를 기록한 뒤
  커밋하고 GitHub에 푸시한다. 기존 검사를 활용하고 실제 수행한 검증만 주장한다.
- CodeRabbit 사용 금지: CLI/API/스킬/플러그인/봇/IDE 확장 및 자동 리뷰 활성화도
  금지한다. 무료 여부와 관계없으며 직접 소스를 검토한다.
- 실제 AI API 호출은 호출별로 사용자 승인이 필요하다. 임의 재시도나 자동 호출 금지.
  이전 실제 대화 평가에 허용된 5회는 모두 소진했다. 새 승인 없이 추가 호출하지 않는다.
- 모델 설정은 `gpt-5.4-mini`, 추론 `none`으로 비용을 최소화한다.
  미리보기·승인 단계에서 실제 요청 설정을 확인할 수 있어야 한다.
- AI 평가 하네스를 추가하지 않았다. 사용자는 성능 부족을 보고받은 뒤 도입 여부를
  결정하기 원한다. 임의 도입하지 않는다.
- 개인 PC 로컬 사용, 로그인 스킵 유지. 크롬은 필요한 검증에만 사용한다.
- 수치에 투자 해석을 붙이지 않는다. 계산 방법 버튼에서 산식·입력값·기준 시각·출처와
  재현 한계를 설명한다. 출처가 없는 수치를 만들어 넣지 않는다.
- 현재 세션에서 하위 에이전트는 사용하지 않았다. 명시적 요청/적용 지침 없이 위임 금지.

## 구현된 흐름과 실제 검증 한계

- 개인 로컬 진입, 환경 파일 준비, 전략 연구 세션·지속 대화, 승인 미리보기,
  불변 전략 버전, 공통 비중/리밸런싱 등 직접 조정, 코드 내보내기,
  개발/검증 구간 비교와 선택 버전 페이퍼 계좌 흐름을 구현했다.
- 지원되는 StrategySpec 규격 안에서 실행한다. 임의 전략 전체를 지원하거나
  최적 수익률을 보장한다고 표현하면 안 된다.
- 실제 AI 평가 5회 중 3회 완료, 2회 실패. 가설 → 질문 → 실행 규격 v1 → 조정 v2를
  관찰했다. 직접 조정으로 v3도 생성했다. 구조화 출력과 대화 지침을 보강했지만
  수정 후 추가 실제 호출은 없으며 설명 정확성·지연·다양한 가설 성능은 충분히
  검증되지 않았다. 자세한 기록: `docs/AI_CHAT_EVALUATION.md`.
- 증권사 연결은 아직 완료/검증되지 않았다. 실제 인증, 실시간 수신, 장중 페이퍼 체결,
  장시간 연속 운용이 성공했다고 주장하지 않는다. 키 입력만으로 연결 완료가 아니다.
- 토스 IP 차단은 요청 서버의 공인 IP 허용 목록과 관련된다. 네트워크 이동에 따라
  공인 IP가 달라질 수 있다. 사용자의 현재 IP/연결 상태를 추정해서 확정하지 않는다.
- 개인 로컬 변경 범위의 직접 보안 검토를 수행했다. 전체 저장소 심층 감사나
  실제 OCI/KMS 검증 완료를 의미하지 않는다. 관련 작업 전에
  `SECURITY_REMEDIATION_STATUS.md`를 전부 읽고 AGENTS의 해당 제한을 따른다.

## 시장·상세 화면의 현재 상태

- 총 37개: 지수 9, 환율 5, 선물·원자재 4, 미국 섹터 11, 한국 업종 8.
  주요 회사, 표시 기업 내 시총 비중, 확인된 사업 점유율, 지정 언론사의 최근 뉴스,
  공식 출처 링크를 상세 화면에 모았다. 표 안 비중과 실제 시장점유율을 구분한다.
- 현재 시세는 지원 증권사 우선, 미지원/미수신은 Yahoo 1분 수집으로 보완한다.
  KIS 지원 국내 지표는 WebSocket, 토스 코스피/코스닥은 REST 15초,
  토스 원/달러 참고 환율은 1분이다. 실제 연결 수신을 검증한 기록은 아니다.
- 상세 일봉·기업·뉴스는 별도 worker가 15분 간격 목표로 수집한다.
  상세 화면은 캐시를 15초마다 확인한다. 읽기 API 자체는 외부 수집을 하지 않는다.
  시장 참고 자료와 페이퍼 체결 자료를 분리한다.
- 최대 3년 차트. 기본은 3개월 일봉 캔들, SMA 5/20/60/120 켜짐, 거래량 꺼짐.
  기간/봉 주기/날짜/눈금/표시 설정, 우측 가격 축, 최근 종가,
  네 색상 범례, 포인터 십자선·OHLC, 클릭 확대와 Esc 복귀를 지원한다.
- 이전 구간으로 이평선을 준비하며 종료일 이후 자료를 제외한다. 부족한 표본은
  이유를 표시한다. 유효 종가는 보존하고 불완전 OHLC는 캔들 대신 종가 점을 쓴다.
- 일부 지수는 Yahoo 일봉이 1개뿐이었다. 관련 ETF 장기 자료는 별도 시계열로
  표시하며 원래 지수와 혼합하지 않는다. 공급자 자료 부족을 앱 오류로 숨기지 않는다.
- CSP가 차단하던 범례 인라인 색상을 고정 외부 CSS로 옮겼다. CSP를 완화하지 않았다.

## 마지막 완료 요청: 카드 전체 클릭

사용자: 이름뿐 아니라 칸을 눌러도 상세 페이지로 이동하게 변경.

- `market.js`: article에 escaping한 `data-market-card` 식별자 추가.
- `market-detail.js`: 기존 단일 위임 클릭 리스너를 확장했다. 수치/여백은 상세로,
  작은 차트는 확대창으로 이동한다. 설명/details, 출처 링크, 다른 입력 조작,
  선택한 텍스트에는 카드 이동을 적용하지 않는다. 수정 키/중간 클릭을 가로채지 않는다.
- 제목은 실제 링크로 유지해 키보드 탐색을 보존한다. 카드 커서/포커스 표시와
  수정 정적 파일의 캐시 버전을 갱신했다. 카드별 리스너를 추가하지 않았다.
- 관련 기존 검사 8개, Node 문법 검사, `git diff --check` 통과.
  이번 작은 탐색 변경의 별도 지연 벤치마크는 수행하지 않았다.
- Docker 빌드·재실행 후 Chrome에서 S&P 500 수치/빈 공간,
  정보기술 섹터 수치 클릭 → 실제 상세 화면을 확인했다.
  계산 설명/정보 펼치기/본문 클릭, 작은 차트 확대, 제목 Enter 탐색도 확인했다.
- 직접 코드·보안 검토: 식별자 escaping, 상세 ID 검증/허용 목록, 인증/CSRF 유지.
  새 패키지나 AI 호출 없음.
- 마지막 기능 커밋 CI: **success**, verify와 postgres-integration 모두 통과.
  `https://github.com/blockcoder-sj/Milkyway/actions/runs/36683156625`.
  전체 회귀·의존성 감사·PostgreSQL 경계·설치/강제 종료 복구·Node 검사를 포함한다.
- 로컬 증거 화면: `/tmp/milkyway-evidence/card-click-detail.png`.
  임시 파일은 다음 세션에 남아 있음을 보장하지 않는다.

## 이어서 작업할 때

현재 카드 클릭 요청은 완료되어 푸시됐다. 이번 맥락 저장 외에 진행 중인 구현은 없다.
새 요청이 오면 Git 상태와 해당 파일을 확인해서 이어간다. AI/증권사 실제 검증을
재개하려면 위의 승인 조건과 미검증 한계를 적용한다.

참고 문서: `docs/AI_RESEARCH_GUIDE.md`, `docs/AI_RESEARCH_MILESTONES.md`,
`docs/STRATEGY_CHAT.md`, `docs/AI_CHAT_EVALUATION.md`,
`docs/MARKET_DASHBOARD.md`, `docs/MARKET_DETAILS.md`,
`docs/LOCAL_MAINTENANCE_20260930.md`.

## 2026-10-01 — milestone 1: presentation, directory, news and AI failure handling

- Landing uses `시작하기`. US sector names use English GICS names. Market cards
  contain name, price/change and a larger intraday line; calculation, source,
  timestamps and range disclosures moved to detail. Preserve provider separation.
- Shared grouped number formatter/parser accepts `100,000` inputs without changing
  stored values. Chat uses black background, borders, aligned equal columns and
  compact operation facts. Saved research title can be renamed (owner + CSRF scoped),
  preserving turns, versions and pending approval digests.
- Companies: Yahoo screen pages (100 per request, 4 concurrent, upper bound 1,000
  per sector); Korean business examples expanded from 4 to 9–20 per group. These
  are not certified current S&P/KRX constituents. Tables search and paginate 8 rows;
  weights use the entire received universe, independently of page/search.
- News: four time windows over 30 days, up to 400 collected headlines per instrument,
  8 per page, timestamp ordered, allowlisted publishers including NYT/BBC/CNN/
  Al Jazeera. Retain still-current previous headlines on partial failures. Collection
  is limited by Google News indexing; it does not guarantee every published article.
  Sources collection is collapsible. No full article/paywall content is collected.
- AI: one approved request still means one provider attempt. Keep gpt-5.4-mini,
  reasoning none and 4,000 output tokens. Response read timeout 150s / process
  deadline 180s; show running immediately. Distinguish timeout/network/provider/
  refusal/incomplete/output-limit/JSON/schema/universe errors. Store bounded safe
  request ID/status/elapsed time and known usage; never raw provider messages or keys.
- Existing 5 paid evaluation calls remain the only calls used. All were consumed.
  No new AI call was made during this milestone. An asynchronous question is pending
  asking for ONE new paid regression call with a concrete 3-ticker momentum prompt.
  Do not call unless the user explicitly approves it; no automatic retries/harness.
- Toss connection now verified. Read-only AAPL check returned one quote at
  2026-09-30T16:02:11Z (337.55 USD); exchange-rate cache also collected real Toss
  data. Fixed FX freshness: allow the provider's <=5min observation window while
  requiring a fetch <=90s old and validUntil still in the future. Active paper
  accounts are absent; do not claim a live paper fill/continuous run.
- Verification: full suite 351 tests passed (430.465s, includes cold dependency
  loading); focused suite 65 passed (3.573s); additional list/news suite 19 passed
  (0.251s). AST/JS syntax and diff whitespace checks passed. Direct source review
  covered owner/CSRF, approval replay, error redaction, source URL/XML handling and
  bounded external I/O. CodeRabbit was not used. This is scoped review for local
  personal use, not the pending managed whole-repository security/OCI gates.
- Docker image rebuilt and existing 7 services recreated without deleting volumes;
  Chrome confirmed compact market cards and research borders/alignment. Cache-only
  detail JSON with 494 companies + 108 news: 30 samples median 10.35ms/p95 17.62ms.
- Next milestone in progress: company detail/relationship graph, source-backed
  product/business notes, public company data worker and regression tests. All
  current and latest user requests remain active; do not report the whole task done
  before this milestone, review, push and visible browser proof are complete.

## 2026-10-01 — dependency security correction after milestone 1 CI

- GitHub run 36745485334 rejected the dependency audit: four known advisories in
  PyJWT 2.14.0 and urllib3 2.7.0. Updated both hash locks to PyJWT 2.15.0 and
  urllib3 2.8.0, using verified official PyPI release SHA256 values. Updated direct
  floors; BeautifulSoup 4.15 was already locked transitively and is now declared
  directly for the company HTML parser. Do not suppress the audit gate.
- Actual isolated pip-audit inspected all 65 locked dependencies and reported
  zero known advisories. pip check passed. Five dependency tests passed, including
  deeply nested JWT JSON, bounded HTTP chunk-size lines and deflate stream EOF.
  Full suite at this checkpoint: 357 tests passed in 29.463s. New company tests
  were added afterwards and will be included in the next complete verification.
- Immutable dependency patch SHA256:
  60b1afb312fdf04b21a59bddce313e9c5a6f51579ebcc926de65aa66e00c3344.
  Fresh read-only review found no blocking defect, verified upstream wheel hashes
  and offline OCI token/proxy TLS compatibility. Packaged Linux checks remain for
  CI. This is not a whole-repository deep scan or public OCI clearance.
