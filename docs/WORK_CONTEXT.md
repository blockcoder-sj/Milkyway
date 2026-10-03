# Milkyway 작업 맥락

저장일: 2026-10-01 (Asia/Seoul). 사용자 요청으로 다음 작업을 위한 인수인계를
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

## 2026-10-01 — milestone 2: company encyclopedia, relationships and final review

This section supersedes older descriptions of the local service count, company
navigation and remaining implementation. Confirm current Git/runtime state when
resuming; no paid AI regression approval has arrived.

- Sector companies now open a company page by name or by clicking the row. It
  combines products/services, business composition, operating inputs, verified
  market-share facts, sourced subsidiaries/parents/owners/suppliers/customers/
  partners/competitors, annual SEC figures and filings. Every item has provenance;
  publicly editable encyclopedia material is clearly distinguished from primary
  sources. Missing market shares or relationships are not guessed.
- Relationship SVG supports mouse/keyboard selection, type filters, 8 nodes per
  page and a source/date panel. Registered public companies link to their own
  page. Products paginate 8/page; same-sector exploration has up to 80 peers.
  TSM has a curated technology classification when absent from Yahoo screening;
  it has no invented market cap or index membership. Quote share explanation uses
  the full received universe, independent of visible pages.
- Modules separate schemas, source notes, bounded public fetchers, cache/queue,
  independent worker and UI. Company GET never calls external providers. POST
  requires login/CSRF and a listed symbol, 60/hour; queue max 200, cooldown 5min,
  provider process deadline 75s. Fixed HTTPS hosts, no redirects/environment
  proxies, bounded bodies/typed arrays, exact ticker/CIK matching. Wrong-company
  cache is rejected; interrupted/partial collections preserve available old data.
- 16 source-backed business profiles cover all 11 US sector categories and key
  Korean technology companies. Wider companies obtain Wikidata/Wikipedia context,
  WiseReport KR business composition or SEC submissions/US GAAP USD annual data.
  This does not certify completeness of every company's market share or business
  relationship. IFRS/nonUSD and KR public filing figures are not standardized.
  Architecture and maintenance: `docs/COMPANY_DATA.md`.
- Actual public probes: AAPL products 26 / relations 24 / financials 6 / filings 8;
  Samsung products 5 / facts 13 / relations 22, no collection errors; Adobe
  products 27 / relations 4 / financials 6 / filings 8, no errors. SEC failures and
  ticker search handling were corrected. A Duke encyclopedia probe later succeeded;
  temporary partial failures remain explicitly reported rather than fabricated.
- Found oversized Google publisher queries could include unrelated indexed-body
  stories. Split into <=6 publishers per request and apply explicit headline
  keyword scope. Selection version 3 replaces obsolete selection caches. Actual
  Technology refresh: 495 companies, 243 recent headlines, 5.56s, no news error;
  publisher labels include BBC/CNN/Al Jazeera/Reuters/AP/FT/WSJ/CNBC and others.
  Four date windows, max 400 retained headlines, 8/page, descending timestamps.
  Google indexing/headline keyword limits mean not every published article is covered.
- Performance: 30 real cached company projections improved median 94.07→17.20ms,
  p95 123.35→27.44ms by resolving registered relations first and searching the
  current sector before other caches. Public collection is outside HTTP/trading.
- Verification: full 382 tests passed in 34.675s; company/personal focused 39 passed;
  Python/JS syntax and whitespace checks passed. Network-disabled Linux/Python3.11
  process integration passed 7 stages, including real auth/CSRF/queue/company worker,
  restart/replay, backtests/paper, crash recovery and backups, all synthetic providers.
  One host-native cold-start check exceeded its 25s startup limit with an empty app
  log; it is not counted as a pass. Packaged native integration passed instead.
- Chrome verified row navigation, company cross-links, filters, paginated companies
  and news, sources open/close, saved-title rename and restoration, black chat and
  aligned grouped inputs. Final local image recreated all 8 services without deleting
  user volumes; app healthy and worker heartbeats current. `company-data` added.
- Direct code/security review covered auth/CSRF, traversal, wrong-identity admission,
  bounded I/O, URL and HTML/SVG escaping, epoch/owner navigation races, failure data
  retention and no coupling to AI/orders. This is scoped local review, not a whole
  deep audit or the unperformed OCI/public deployment gates. CodeRabbit was not used.
- Security dependency commit 4851d28 is pushed. GitHub run 36750257840 passed both
  verification and packaged PostgreSQL/personal/native/frontend integration jobs.
  Final encyclopedia changes are being committed/pushed; verify the latest run before
  declaring GitHub verification complete.
- AI reliability fixes are implemented, but the proposed ONE new live call remains
  awaiting the user's explicit approval. No new paid call or AI evaluation harness
  was used. Existing 5-call evaluation remains 3 success / 2 failure. Real continuous
  paper operation is not claimed; no active user paper accounts were created.

## 2026-10-01 — company wiki milestone 1: normalized local storage

- User authorized the suggested common company IDs, SQLite company/relation/source
  tables and direct Wikipedia-like navigation including identifiable private firms.
  The RAG chatbot was described as a future extension, not implemented or evaluated
  here. No new paid AI call or embedding is authorized/used.
- Public research has its own SQLite database at `company-details/graph.sqlite3`.
  Identity aliases, sources, directed relations and profiles are transactional;
  graph indexes support both ends. Exact ticker/Wikidata matches unify identities
  and preserve old ID redirects. Equal names do not merge entities. Name-only
  references have source-scoped identities and do not trigger guessed collection.
- Existing JSON stays intact and is imported at personal app/worker startup.
  DB profiles take priority afterwards. Collection preserves provenance and
  previous sections on partial failures; private firms use only registered exact
  Wikidata IDs. New local authenticated entity routes share CSRF/rate limits.
- Reverse views preserve the original statement and reporting company. Replacing
  a profile retracts only that profile's claims. Shared sources and identity
  references remain stored. A source may be a publicly editable encyclopedia;
  there is no claim that all relations are current or complete.
- Personal backup/restore snapshots this SQLite DB through its online backup API,
  excludes WAL/SHM files, and validates integrity/FKs before restore. Actual checks
  used temporary databases and did not restore or delete the user's runtime.
- Full regression suite: 397 tests passed in 29.895s. New offline checks cover
  canonical IDs/redirects, no name merging, exact private identity, worker queue,
  conflicts/transactions, concurrent initialization, migration preserving files,
  source/reverse links, auth/CSRF and real WAL backup/restore. Scoped direct code
  review covered these boundaries and bounded fixed-host I/O; no CodeRabbit used.
- Synthetic cached projection benchmark: 100 relations, 30 samples, median 5.26ms,
  p95 5.74ms; no external or AI calls. UI direct navigation is the next milestone.

## 2026-10-01 — company wiki milestone 2: direct navigation and evidence

- Relationship graph nodes and company names now link directly to canonical
  `#company/c_ID` pages. A separate relationship/source button shows evidence
  without navigating. Identifiable private firms have their own pages and collect
  public data by registered Wikidata ID; name-only references remain navigable
  without guessed collection. Listed relationship targets discover actual cached
  sector context and retain common IDs when their profiles are first opened.
- History preserves the origin sector and previous company. Refreshing a deep
  company or market detail address retains that address and does not add a new
  history entry. Executable Node regression checks cover direct clicks, navigation
  races, source escaping, private missing-quote display and deep-link reload.
- Same target/type relations appear once, with all returned original statements
  shown separately in the evidence panel and source collection. Evidence keeps
  reporting company, direction, original explanation, date and URL. The DB still
  stores independent statements; retracting one reporter's claim preserves others.
- Full regression suite: 400 tests passed in 40.432s. Network-disabled packaged
  Linux/Python3.11 process integration passed all 8 stages, including authenticated
  company/entity queues, private worker results, CSRF, synthetic approval replay,
  backtest/paper histories, SIGKILL recovery and isolated backup/restore. No real
  AI call or user account/order was created by those checks. Python formatting,
  JS syntax and diff whitespace checks passed.
- Actual Chrome confirmed Apple graph → Claris canonical page, parent link and
  two original evidence statements grouped into one Apple node after refresh.
  Real public collection for Claris completed with 1 product / 2 facts / no errors.
  Final cached Apple projection: 24 relations, 30 samples, median 23.66ms / p95
  35.08ms; socket connections were blocked during measurement, attempts zero.
  Actual research DB: 28 entities / 29 statements / foreign-key errors zero at
  that checkpoint. Counts and timings are dated observations, not completeness.
- Final local image recreated all 8 existing services without deleting runtime
  or backup volumes; all running and app healthcheck healthy. Direct source and
  scoped security review covered auth/CSRF, common ID admission, traversal,
  fixed-host bounded collection, statement retention, escaped HTML/SVG, history
  and epoch/owner races. No CodeRabbit; this does not clear whole deep-scan/OCI gates.
- Storage milestone commit `2be4ae7` is pushed; GitHub run `36820042971` passed.
  UI milestone commit `72ef323` is also pushed; GitHub run `36823002927` passed.
  Subsequent changes use the same branch `codex/ai-research-workflow`; check latest
  remote HEAD and its CI run before reporting GitHub completion.
- LangGraph, vector search and RAG answering remain future extensions. No paid
  AI/embedding call or new AI harness was used. Per-call approval stays required.

## 2026-10-01 — company wiki milestone 3: business relationships first

- User asked for relationships useful for company analysis rather than a graph
  dominated by investment holders. Default selection now excludes owner/holding
  edges and prioritizes suppliers, customers, partners and competitors, followed
  by parent/subsidiary firms. Primary sources precede provider/encyclopedia material
  within each group. This is a transparent display rule, not a financial importance
  score. Ownership/all/type filters remain available.
- Dedicated pure `static/company-relations.js` owns selection, evidence lead and
  SVG layout. Eight cards per page show business role and evidence count, with
  directional supply/customer and parent/subsidiary arrows. Fixed columns avoid
  overlapping nodes; longer labels wrap by word; narrow screens can scroll the
  graph horizontally. Full explanations, dates and sources remain in the panel/list.
- Apple supplier/partner roles were expanded from its actual 2025-08-06 public
  manufacturing-program release: glass, VCSEL lasers, foundational semiconductors,
  packaging/testing, rare-earth magnets, equipment and wafer collaboration. Planned
  expansions are explicitly described as plans. New curated statements join cached
  provider statements without repeated duplicates; no source or role is guessed.
- Found canonical direct-entry pages could generate same-sector links with a null
  sector. Refresh now adopts the returned actual sector; browser verified the NVIDIA
  link is `#company/us_45/NVDA`. Existing company IDs survive enriched company names.
  Removed an unnecessary second identity/profile read when Wikidata identity is
  already known. Source handling and exact-identity collection boundaries remain.
- Full suite: 402 tests passed in 31.284s. Added executable regression assertions
  for business/default/ownership filters, source priority, arrow direction/anchors,
  descriptive cards, escaping, invalid target rejection, label wrapping, direct
  sector links, and cached note enrichment preserving earlier statements and IDs.
- Chrome verified default supplier cards, ownership filter, Corning evidence panel,
  graph → Corning Incorporated page → back to Apple, canonical refresh and valid
  same-sector links. First-page geometry: 8 nodes / zero overlaps / zero nonempty
  text exceeding card bounds. Original user strategy tab was preserved; the separate
  graph preview tab is the deliverable. No viewport override was used.
- Final graph rendering benchmark: synthetic 400 relations, 100 samples, median
  1.23ms / p95 2.35ms, external calls zero. This measures selection/SVG generation,
  not network latency or every screen/device.
- Final real cached Apple projection: 32 relations / 28 business relations,
  30 samples, median 33.86ms / p95 48.18ms with socket connections blocked and
  zero attempts. Research DB at that checkpoint: 41 entities / 44 statements /
  zero foreign-key errors. During a previous deployment-overlap sample, p95 was
  119.72ms; use the steady sample above, not that mixed-load run, for comparison.
- Final network-disabled Linux image integration passed all 8 stages, including
  canonical private collection, synthetic approval replay, paper/backtest state,
  crash recovery and isolated backup/restore. Latest local image recreated the
  existing 8 services; all running and app healthcheck healthy. User runtime/backup
  volumes remain intact. Latest UI commit/CI must be checked at the branch HEAD.
- Source/code/security review covered bounded cached enrichment, independent
  evidence retention, safe common-ID URLs, escaped text, SVG dimensions and source
  interpretation. No paid AI call, embedding, new AI harness or CodeRabbit used.
  This remains a scoped personal-local review, not pending deep-scan/OCI clearance.

## 2026-10-01 — AI 5-call regression and free filing relationships

- User explicitly requested another five live AI tests. The five approved calls
  were completed through the actual Chrome conversation/preview/one-call approval
  flow in a separate `AI 응답 재검증 · 2026-10-01 · 5회` session. All five completed
  without errors, in 3.743–5.398s. Hypothesis clarification, v1 generation, a
  three-field v2 adjustment, refusal of unsupported rules without mutation, and
  final stored-rule explanation were checked. The two StrategySpecs and exported
  Python ASTs passed. No actual backtest, account deployment or broker order was
  made for this evaluation. Full evidence: `docs/AI_CHAT_REGRESSION_20261001.md`.
- This supersedes the earlier pending one-call question. The new five-call scope
  is entirely consumed; no further paid call is authorized. Model remains
  gpt-5.4-mini, reasoning none, output cap 4,000, automatic retry zero. No AI
  evaluation harness or embedding was added. Five passes do not prove that every
  future provider/network request or strategy hypothesis will succeed.
- Free SEC extraction no longer depends on Wikidata matching: official exact
  ticker/CIK lookup and submissions revalidation precede the filing download.
  The user supplied and authorized a SEC contact email; it is saved only in the
  ignored owner-only `.env`, passed only to company-data and attached only to SEC
  headers. Never copy its value into context, Git, screenshots or error output.
- JPM's submissions exceeded the old 2MiB limit and its annual filing could sit
  beyond the first 2,000 submissions. New bounds are 8MiB/50,000 submissions,
  24MiB HTML, 4MiB subsidiary exhibit and 75s process deadline. Complete annual
  filings precede short amendments. Explicit same-issuer SEC subsidiary links
  and bounded filing indexes are supported; no arbitrary crawler/redirect is used.
- Dedicated `company_filings.py` extracts explicit named business statements,
  product/segment/risk paragraphs and Exhibit 21 tables without AI. Different
  roles for one counterparty keep separate original evidence. Negated, hypothetical,
  unnamed and unsupported-alias relationships are not invented. Body/exhibit caps
  are 80 each; the existing 100-row profile/400-statement view bounds remain.
- Real NVIDIA refresh: 1,431 paragraphs, 35 business statements plus 3 exhibit
  statements, 58 raw profile relations, 6 financial fields, errors empty. UI groups
  the evidence into 37 business nodes: suppliers 7, partners 4, competitors 19,
  subsidiaries 7; customers/parent 0. These counts are dated observations, not
  complete coverage. JPM returned 5 financial fields and 18 exhibit subsidiaries,
  plus 3 official partners; its body rule found no named business edge. Wikidata
  was rate limited for JPM while the independent SEC collection succeeded.
- Official free notes add Chase–Amazon/United, announced Apple Card transition,
  Microsoft–OpenAI, and NVIDIA–Meta/AWS/Anthropic partnerships. Plans remain plans;
  technology partners are not automatically labelled paying customers. Newest
  actual statement dates lead within a source grade; retrieval dates do not.
- Company-data now scans received sector directories in the background, at most
  one new job per sector/minute, with 20 manual slots and manual priority. A saved
  cursor limits each sector scan to 50 candidates; success is due after 24h and
  errors after 1h. HTTP 429 pauses that host for bounded Retry-After time (1min–24h),
  with no immediate retry. Other sources continue. Source-specific retention
  preserves failed-source evidence alongside fresh rows, while refreshed sources
  can retract their old claims. Collection is outside HTTP/trading and has no AI key.
- Start/default local entry now opens `#market`; explicit strategy/detail/company
  links stay supported. Chrome verified the actual Start button and NVIDIA graph
  → Micron canonical detail → previous screen, source panels and filter counts.
  Sector card lines remain latest-session 1d/5m Yahoo series, not the detailed
  chart's default 3-month daily series; ETF fallback remains separately identified.
- Final packaged Python regression has 423 tests; 11 Node-dependent cases are
  skipped inside the Python image and all 13 host Node frontend cases passed.
  Packaged network-disabled native process integration passed all 8 stages,
  including auth/CSRF, queues, private navigation, synthetic approval replay,
  research/backtest/paper recovery and isolated backup/restore. These synthetic
  checks neither consume paid calls nor restore the user's runtime.
- Public-cache copy benchmark, 30 samples each, network attempts zero: NVIDIA
  snapshot median 48.60ms/p95 76.07ms; JPM 51.19ms/p95 62.34ms. Real public HTML
  parser, 3 samples: NVIDIA 1.11s median, JPM 7.791s median. A concurrent regression
  load sample had up to 228.53ms p95; figures do not measure provider latency.
- Source/code/scoped security review covered identity validation, source-local
  exhibit identities, contact CRLF rejection and credential separation, fixed-host
  no-redirect bounded I/O, pathname guards, safe diagnostics, source retention,
  queue/cursor bounds and escaped HTML/SVG. No dependencies or CodeRabbit added.
  Whole deep-scan/OCI/public deployment gates remain unchanged.
- Existing 8 local services were rebuilt/recreated with runtime and backup volumes
  preserved; app startup reported ready. Completion/push/CI evidence is recorded
  in `docs/LOCAL_REVIEW_20261001_EDGAR.md`; check branch HEAD/run before reporting
  current GitHub status. No public deployment or real trading order was performed.
- Remaining data limits: large directories are still being collected; not every
  relationship category/company is populated. Free sources can omit counterparties,
  fail temporarily or exceed supported formats/alias rules. Korean OpenDART key
  request remains unanswered; `.env`/example has an empty reserved DART_API_KEY,
  but the DART collector is not implemented or verified. LangGraph/RAG is also a
  separate future extension, not part of the paid-call approval or this collector.

## 2026-10-01 — company research redesign in progress

- User now explicitly rejects Wikipedia/Wikidata company knowledge, including old
  cached business text and relationships. Keep wiki-style internal company navigation;
  replace encyclopedic knowledge with official filings/IR/verified public research.
  Source links should live in a bottom source collection; essential Korean business,
  revenue model, products, customers, supply chain and competition lead the page.
- M1 implemented exact-ticker public fund disclosure cross-checks. Real ITOT + 11
  Select Sector files provide 2,444 US equities as of 2026-09-30. All 3,689 received
  US sector rows audited: 207 sector corrections; disclosed members added for a
  3,880-row display (2,444 matched, 1,436 unverified). This is not a licensed GICS
  master validation; nonmatched companies remain labelled unverified.
- M1 focused 56 checks include host Node. Final immutable M1 package: 429 regression
  tests in 75.745s OK, 11 Node-dependent skipped; existing offline native process
  integration passes all 8 stages. Actual directory reconciliation median 3.69ms,
  max 10.05ms. Initial host mount permission failures and collection CPU contention
  caused fixture/startup failures; production deadlines/tests were not relaxed.
- M2 provenance cleanup and primary business relationships; M3 Korean concise brief,
  structured revenue, collapsed originals and bottom sources remain required work.
  See docs/COMPANY_RESEARCH_MILESTONES.md. Paid AI approval question is unanswered;
  zero new actual AI provider calls are authorized or made in this task.

## 2026-10-02 — M2 primary company research complete

- Removed active Wikipedia/Wikidata I/O and rejected encyclopedia facts by source
  grade AND domain, including legacy JSON and SQLite migrations. Existing opaque
  ID aliases preserve internal navigation. Source-linked English originals are
  separate from concise Korean business-role notes.
- Reviewed free primary research now covers 30 public / 20 additional entities and
  85 curated relationship statements. Common verified registry IDs support direct
  nonlisted company pages and reverse business edges; no name-only identity merge.
- Consistent online public graph backup: integrity ok, 718 encyclopedia sources
  removed, zero retained rejected sources and FK errors; migration 7.156 seconds.
  Repeat 1,500-file public-cache bootstrap 15.770 seconds. Latest focused 64 checks
  passed. Packaged regression 436 and isolated native 8-stage integration passed;
  latest small index/bootstrap improvements will also receive final package/CI checks.
- Actual stored annual HTML single parse: NVIDIA 0.758s, JPM 7.867s (one sample each).
  No new dependencies/AI calls/CodeRabbit. Background company/market-detail collector
  CPU shares 128 reduce contention without relaxing deadlines. Personal volumes intact.
- M3 remains: essentials first, structured reported annual revenue, collapsed English
  excerpts and all external source links at the bottom. No new AI approval arrived.
  Evidence: docs/LOCAL_REVIEW_20261002_COMPANY_RESEARCH.md.

## 2026-10-02 — M3 company reading screen complete; M4/M5 continuing

- Korean essentials lead company pages; actual reported annual revenue is separated
  into product/segment/geography/alternate product-service views. Same-document,
  metric, period, currency denominators only. Verified child rows are indented;
  slices are not summed. Actual SEC HTML: NVIDIA 11, Microsoft 17, McDonald's 3 rows.
- All external source links are in the bottom folded collection; main citations
  open the document there. English originals are folded. Optional free translation
  links send only the public excerpt on user click; no automatic paid API calls.
- Immutable sector views and a bounded company-name index avoid repeated deep
  copies and chart/news parsing. Public cache median over 30 reads: NVDA 121.11ms,
  MCD 82.71ms, MSFT 116.39ms; network and cold index costs are separate.
- Final image 6de1cdf09ef0f104091ff41a10d22f5c27716bbb277febfbe1767dd17f850bf9:
  450 packaged checks / 172.834s OK (12 Node skipped), host CI frontend files
  14 checks passed, offline native process integration all 8 stages passed.
  An existing 3-second OCI synthetic worker test failed intermittently and alone;
  moved fake spawn targets to a small helper to avoid reimporting the full FastAPI
  test module. Runtime deadlines, pipe bounds and process cleanup assertions remain.
  This is not actual deployed OCI/Vault evidence.
- Same tested image deployed to 8 local services, app healthy, original personal
  runtime/backup volumes preserved. Read-only public graph check: integrity ok,
  rejected sources 0, FK errors 0, 1,815 collected profiles at inspection time.
  Curated reading coverage remains limited; collected profiles are not all reviewed.
- Chrome verified SEC revenue refresh, group changes, bottom citations, Foxconn
  internal detail/back navigation; encyclopedia links and external links outside
  the source section both zero. Selected relation now survives reordered refresh.
  Proof: /tmp/milkyway-company-research-m3.png; full review in the M2/M3 review doc.
- Latest user steering extends the work: free-source industry-level relationship
  coverage, processed/summarized information, and reliable AI strategy replies.
  Continue M4 data/value-chain coverage and M5 AI failure handling/validation.
  Do not claim complete all-company coverage or zero possible external failures.
  No renewed paid-call approval has arrived; new actual AI calls remain prohibited.
  Use the existing user-configured key/model; no CodeRabbit or new eval harness.

## 2026-10-02 — M5 local AI response validation complete

- Keep gpt-5.4-mini / none, one provider attempt per approval, no paid retries.
  Shorter output constraints reduce truncation; only complete validated prose can
  survive failed schema/universe/output checks. Refusals are never recovered.
  Failed strategy fields are discarded, save rollback preserves history/usage and
  the previous selected strategy. Copying a hypothesis is local and requires a new
  approval for re-sending. Canonical rules come from the actual saved strategy.
- SQLite first-WAL concurrent-open race reproduced and fixed with bounded initial
  BUSY/LOCKED handling; already-WAL connections avoid mode writes.
- Immutable image 47ad955673aa8e16a33d74c6b80680f66dff8b2c9957b48eee8478688543adb8:
  regression 459 / 84.588s OK (12 Node skip), host frontend 14 / 2.326s,
  offline native integration 8 stages. Initial Docker check exhausted its global
  300s after 6 stages under collection load. Same-condition recheck with company
  collection paused passed all 7; collector resumed, personal volumes untouched.
- No new actual AI calls: pending maximum-five approval remains unanswered.
  See docs/AI_RESPONSE_REVIEW_20261002.md. Current deployed runtime remains M3;
  deploy the final tested company-network image after M4. M4 is still required.

## 2026-10-02 — M4 local industry exploration verified

- Expanded free primary-source reading to 75 symbol profiles, 43 registry profiles,
  171 curated symbol-catalogue relationship statements. These include stock classes
  and scoped alliance-role profiles; not 75 equally complete company analyses or
  171 distinct current contracts. Source dates, plans and regional roles remain.
- Separate notes/industry modules provide Korean business, revenue, products,
  customers and inputs. Foxconn/Cargill/McCain/Wistron received business-specific
  profiles. Long originals and all external sources remain folded at the bottom.
- SEC legal-name index adds exact known ticker/CIK names without fuzzy guesses;
  ambiguity, multiple classes, self and brand-substring collisions are rejected.
  Explicit relation clauses prevent competitor sections from relabelling suppliers.
  Collector v3 upgrades old data through the existing bounded scheduler.
- Selected two-hop business network is cache-only, authenticated, eight rows/page,
  four business kinds, 400 statements/company and 10 displayed evidence items/edge.
  Root -> via must be confirmed; no inferred root -> leaf trade. Business precedes
  ownership, aliases are read in one bounded query. Canonical internal navigation,
  source footer and actor/workspace/request-epoch guards remain.
- Initial full suite found a missing FastAPI Query import at startup. Fixed it and
  added an API auth/cache/query-bound/schema regression. Immutable image
  6afb3c1732b19d76cc3f7314376a59b9683330694a29e3eb2fe5ab8ae21423ae:
  full 471 / 74.738s OK (13 Node skip), host frontend 15 / 2.164s OK,
  offline native 8 stages, Docker packaged 7 stages with public collectors running.
  Existing limits unchanged; original and synthetic test volumes preserved.
- Exact index of 10,434 official rows built in .264s; lookup median/p95 .052/.191ms.
  Actual public DB copy network medians/p95: NVDA->DELL 18.61/56.45ms,
  AAPL->TSM 16.97/37.09ms, TSM->AMKR 15.35/23.50ms. Integrity ok/FK0.
  Read-only compatibility check of personal saved strategies: valid5/invalid0;
  no prompts/keys/account records printed or sent. These are not provider latency.
- Direct scoped code/security review, Python/JS syntax and diff checks passed.
  Changed-file credential pattern check found no candidates; .env remains ignored.
  No CodeRabbit, new dependencies, eval harness, actual AI calls or orders.
- M5 pushed as 49778b1; CI 36896059671 success in both jobs. M4 commit/push and
  final deployment/Chrome proof are the next steps. Current personal runtime remains
  M3 and collectors are running. Maximum-five actual AI approval is still pending.
  See docs/COMPANY_NETWORK_REVIEW_20261002.md and COMPANY_RESEARCH_MILESTONES.md.

## 2026-10-02 — M4/M5 applied; final industry screen and corrections verified

- Initial M4 pushed as `2c345a2`; both jobs of GitHub CI 36900893992 succeeded.
  M5 `49778b1` also has successful CI 36896059671. Check Git HEAD and the latest
  branch workflow for this final corrective commit; do not infer its CI from the
  preceding commits. Branch/remote remain codex/ai-research-workflow and origin.
- Chrome found an old CHRN→NVDA customer false claim caused by treating access
  to NVIDIA H100 products as selling to NVIDIA. Added counterparty/clause checks
  and collector_version4. Recheck only old automatic SEC claims. Exact physical
  deletion includes owner/target/kind/detail/original/source; reviewed statements,
  unrelated owners, filings and private trading/research DB remain intact.
- Bootstrap now reingests changed cleaned/enriched JSON even with an unchanged
  attempted_at. Cleanup idempotence, full legal names, real competition lists,
  reviewed claims and independent owner evidence have regression coverage.
- Read actual CHRN FY2026 annual filing: NVIDIA GPU supplier, Together AI customer,
  later Microsoft 2-year service contract, announced Nutanix framework and four
  AI cloud rivals. Curated Korean business notes keep May31/FY2026 and plans apart.
  Read rival official product sites, verify exact SEC alias titles and Lambda's
  old official domain redirect. No performance/market-share marketing used.
- Final curated scope:78 symbol profiles,46 registry profiles,179 statements.
  Includes stock classes and limited-role notes, not124 fully analyzed unique
  companies or179 distinct contracts. Broad free automatic filing collection stays
  bounded and continues; all thousands of profiles are not fully curated Korean.
- Final immutable local image:
  sha256:7215bab13782e05133943a67f0b25fc17260a8446ab390c17722f2900017d0f7
  Pinned as milkyway-company-m4-cloud:verify and applied to milkyway-personal:local.
  Full477/109.359s OK(13 Node skips);host Node15/3.653s;native8 and packaged Docker7
  passed. Collectors ran normally, limits unchanged. A prior package run failed
  because its old SHA image disappeared during another build; final pin passed.
  A test-name fixture collision, wrong host test module names and omitted explicit
  development env were corrected; review document records failures and results.
- Same verified image recreated existing8services, all running, app healthy.
  Read-only public DB:2521 profiles,integrityok,FK0,forbidden encyclopedia sources0,
  unsupported old automatic claims0,wrong CHRN customer NVDA0; reviewed roles1
  supplier/2customers/1partner/4competitors. User/test runtime/backup volumes retained.
- Active-cache30reads median/p95(ms):NVDA→CHRN17.49/60.05,NVDA→DELL15.65/20.57,
  AAPL→TSM28.34/108.42. Load/profile counts differ from earlier measurements.
- Chrome:NVDA→CHRN→cloud ecosystem;Together AI internal detail/disabled SEC collect/
  back;AAPL supplier page5→TSMC;42 business neighbors;partner26,page1→2,8perpage;
  refresh retains filter/page;Foxconn full Korean40/38/15/7 business composition;
  footer expand/collapse. Wiki links and external links outside footer0.
  Proof /tmp/milkyway-company-research-m4.png. Deliverable Chrome tab810509737
  at AAPL, TSMC partner exploration. Original user MCD tab untouched.
- Direct scoped source/security review, AST/diff checks and changed credential
  pattern scans passed; .env ignored. No CodeRabbit/new dependencies/harness/AI
  paid requests/orders. Single-owner loopback local scope; public OCI/KMS NO-GO.
- M5 reliability code is deployed. New actual provider calls remain0; maximum5
  GPT-5.4-mini/reasoningnone approval question is still unanswered. Prepared public
  5-turn prompts/criteria in AI_RESPONSE_REVIEW_20261002.md; do not call until approval.
  Previous5-call approval was consumed. Do not assert zero external outages, future
  returns, all-company relationship completeness or licensed whole-GICS verification.

## Company prices and resource correction — 2026-10-02

- User additionally requested a current stock price on each company page and
  reported high RAM pressure from container/browser proliferation. Use one
  development tab and sequential expensive checks. Temporary unit runners have
  exited; the stopped native-check container was removed after copying evidence.
  The existing Milkyway group has eight running services, not three required
  independent deployments. All personal runtime/backup volumes were preserved.
- Added registered-company REST/watch APIs, strict bounded quotes, Toss initial
  REST + acknowledged trade-only WebSocket support, and Yahoo once-per-minute
  fallback. Visible pages read every two seconds; no off-page/hidden-page requests.
  Provider, actual price timestamp, delayed/closed/stale status, same-day compatible
  previous-close calculation and thousands separators are displayed. Sources are
  registered in the existing footer. No order, ledger quote or AI call introduced.
- Fixed restart slowdown from thousands of public profiles: skip identical
  uncurated content by exact digest plus sector, still enrich reviewed firms,
  reimport equal-timestamp content changes, and only revalidate legacy migration
  candidates. Existing encyclopedia removal and false-claim tests still pass.
- Final price image: `milkyway-company-prices-final:verify`, applied to existing
  `milkyway-personal:local`. Full offline498/267.117s OK(skipped14), host
  frontend16/17.295s OK, graph/legacy25/2.358s OK. Python AST/diff checks passed;
  direct scoped source/security review, no CodeRabbit or new dependency.
- Actual AAPL/AMD/Samsung cached prices received from Yahoo; cached HTTP median
  17.39ms/p95 35.31ms over30 reads. Existing Toss connection is configured but
  a direct current quote request failed with TossIpNotAllowedError. Do not claim
  that current Toss real-time delivery is working; allowed outbound IP is pending.
- App healthy, all8 services running. Startup/ready HTTP200; database/worker flags
  true, dataset/data_gate false. No real paper execution feed success is claimed.
- Two intermediate packaged checks timed out after4 checks; no final packaged
  success. An intermediate native8 pass preceded final startup optimization.
  Reports/evidence retained under /tmp; see COMPANY_PRICE_REVIEW_20261002.md.
- Browser extension was unavailable; native Chrome control was interrupted while
  the user edited another document. No new window opened, and a fresh price UI
  screenshot remains outstanding. Do not interfere with the user's documents.
- US IT detailed Korean business notes and supply/customer/partner research are
  still outstanding: 453 IT profiles were audited, only30 with briefs; major
  AMD/AVGO/ORCL/etc gaps. Samsung official Supplier_List.pdf was read and saved
  under /tmp. Use its declared historical 80%-of-procurement consented scope,
  not product-specific purchasing or assumed present contracts. Korean industry
  scope is still eight KOSPI entries; verified KIS master has24KOSPI/22KOSDAQ.
- Five newly requested real GPT-5.4-mini/reasoningnone tests still await explicit
  approval; new paid provider calls remain0. No harness authorized.

## User paused work — 2026-10-02

- Explicit latest request: "작업 잠시 중단". Stop implementation, tests, browser
  actions and deployment until the user requests resumption. Existing app services
  remain running; no request to shut down the app or remove personal data.
- Price milestone committed/pushed as `8931bdd74cb5b1dc9ba135d69e16bb351cf92370`.
  GitHub CI36963462532 completed successfully for that exact commit.
- User asked whether Toss is essential. Explained that encyclopedia/display,
  strategy development and backtesting can use free sources; current Yahoo
  quotes are display-only. A separately labelled one-minute reference-price
  paper feed would need implementation. Do not imply it already executes paper
  trades or silently substitute display caches into the execution ledger.
- UNCOMMITTED and UNVERIFIED after that milestone: new
  `cloud_app/company_it_research.py` with17 issuer-based Korean business/product/
  customer/input/competition briefs and3 operating-condition notes each; curated
  AMD/AVGO/QCOM/INTC/CRWD/LRCX/CRM relation statements; imports/merges in
  `company_research_catalog.py`. These are not in the deployed image or GitHub yet.
- Also unverified: `company_revenue.py` supports checked operating-segment
  presentation qualifiers for AMD2488/INTC50863/DELL1571996/AMAT6951, exact AMD
  product/segment pairs, the standard including-assessed-tax revenue metric,
  Korean labels and value-reconciled AMD/Intel parent links. `company_schemas.py`
  adds RevenueLine.includes_intersegment. Tests, further review, complete label
  mapping and UI presentation remain undone. Do not report this as finished.
- Actual primary annual XML showed missing business figures were a parser gap:
  AMD3 segments use srt:ConsolidationItemsAxis=us-gaap:OperatingSegmentsMember plus
  the business segment axis. AMD Client10,640/Gaming3,910 million sum to
  ClientAndGaming14,550; DataCenter16,635 and Embedded3,454; total34,639.
  Intel/Dell/AMAT have the same qualifier; Intel has internal Foundry transactions
  and a Products subtotal. CRWD uses the including-assessed-tax revenue tag.
- Public temporary issuer documents: host `/tmp/milkyway-amd-annual-2025.html`;
  company-data container `/tmp/milkyway-it-primary/{INTC,DELL,AMAT,CRWD}.html`.
  Copy these public documents before replacing that container if needed.
  App container `/tmp/milkyway-it-members.json` holds existing IT revenue rows.
- Complete translations/hierarchies still needed for exact observed members:
  avgo:SubscriptionsandServices; CRM AgentforceIntegrationAndAgentforceAnalytics,
  AgentforceMarketingAndAgentforceCommerce, AgentforceSales, AgentforceService,
  ProfessionalServicesandOther, SubscriptionandSupport; adbe:SubscriptionRevenue;
  hpe:HybridCloudSegment/ServerSegment, us-gaap:CorporateAndOther;
  lrcx:CustomerSupportandOther; klac:OtherRevenue; adi:ReportableSegment. ADI is
  one reporting segment with4 end markets, which should be presented accurately.
- Source source-checks: PANW issuer copy
  https://investors.paloaltonetworks.com/node/20811/html (FY2026 July31), includes
  CyberArk acquisition2026-02-11 and Chronosphere2026-01-29, Prisma/Cortex/identity/
  observability. HPE issuer FY2025 PDF verifies Juniper acquisition2025-07-02.
  LRCX FY2026 explicitly names MU/Samsung/SK hynix/TSMC customers. QCOM FY2025
  names TSMC/Samsung/GFS foundries, ASE/Amkor/SPIL/STATSChipPAC ATMP, and
  Apple/Samsung/Xiaomi each >=10% consolidated customer/licensee revenues.
- Samsung supplier-list expansion remains unimplemented. KIS official current
  master verified exact Korean stock identities (avoid guessing YC): Daeduck
  Electronics353200.KS; Dongjin005290.KQ; Wonik Holdings030530.KQ; Wonik
  Materials104830.KQ; Wonik IPS240810.KQ; PSK319660.KQ; Soulbrain357780.KQ;
  YC232140.KQ. 112290.KQ is YC Chem, a different company. Master snapshots at
  `/tmp/milkyway-kospi-master.txt` and `/tmp/milkyway-kosdaq-master.txt`; downloaded
  with verified TLS, without running the issuer sample's unsafe TLS override.
  Official parsing code filenames are kis_kospi_code_mst.py/kis_kosdaq_code_mst.py
  under koreainvestment/open-trading-api/stocks_info (not kosdaq_code.py).
- New primary materials: Dongjin official business/semiconductor.php and
  en/company/be_overseas.php (explicit Xi'an Samsung supply relationship);
  Soulbrain en/m33.php semiconductor chemicals; Salesforce official2025-10-17
  Google Workspace/Gemini partnership. Research used no new Chrome tab, paid
  API, AI or harness. No new development verification job remains running.

## Resumed M6 — US IT summaries and semiconductor supply chains, 2026-10-02

- User explicitly resumed with "이어서 진행" and asked whether work was active.
  The prior pause is revoked. Focus remains deeper US IT coverage, semiconductor
  partners/suppliers, accurate processed Korean information, and local operation.
- Added 17 issuer-report IT briefs (business/revenue/products/customers/inputs/
  competition and three operating-condition cards each). Added Samsung's37 exact
  official supplier-list entities with their own Korean business sources. Separate
  dated Dongjin/Wonik customer evidence; AMD Tongfu/KYEC and other annual-report
  trade roles. Curated symbol profiles100, registry profiles59, symbol-catalogue
  relationship statements252. These include stock classes/scoped notes, not159
  equally complete company analyses or252 current contracts. Samsung list scope
  is publication-time80% procurement with consent; no publication date is given.
- New data lives in company_it_research.py and company_semiconductor_catalog.py.
  Exact ticker/registry business context is cached/bounded and copied for graph
  responses. It has a distinct source from a supplier-list/trade statement.
  YC232140 is not YC Chem112290; PSK/Soulbrain/Daeduck operating tickers and the
  ASML Netherlands operating legal entity are distinct from their holding companies.
- Revenue parser now accepts exact reviewed operating-segment qualifier pairs
  for AMD/Intel/Dell/AMAT/QCOM and AMD product children. Adds including-tax standard
  revenue, Korean labels, value-tied Oracle/CRM/AMD/Intel hierarchy, ADI end-market
  distinction, strict official-SEC CIK, and cached-row normalization. Intel internal
  segment revenue has no consolidated share. Different documents/periods/currencies/
  metrics or duplicate members cannot support subtotal links or denominator mixing.
- Display adds major-revenue cards, same-basis tables, child indentation and folded
  calculation details. Source-backed business context accompanies relationship
  lists/focus/two-hop neighbours. Actual6 free annual HTMLs were parsed and their
  public cache revenue rows updated (AMD10,INTC10,DELL6,AMAT10,CRWD6,QCOM2), without
  changing private data or broad profile collection timestamps. Collector was stopped
  briefly to avoid write races and restarted. Provider collection later uses the
  same parser. Public originals/parsed JSON remain under /tmp/milkyway-it-*.
- Focused47/1.018s passed after detecting/filling3 missing supplier descriptions.
  First full505 test run had4 errors because disposable /app/runtime was read-only;
  add a private tmpfs, never a user volume. Recheck505/29.033s OK(skipped14), host16
  /0.853s OK, native8 stages OK. Chrome found a pre-existing price/network citation
  registry collision. Added useReading/prepareReading and a real combined Node
  regression covering page switches, price ticks, bounded sources and no extra calls.
  Corrected code image full506/45.935s OK(skipped15), host17/1.683s OK, native8 OK.
- Chrome also retained an older company-price.js after reload, causing useReading
  missing. All7 company JS/CSS asset versions are now20261002-6. Final release
  image/retest/deployment and final visible citation verification are recorded below.
- Actual annual single parses405.15–824.79ms at1CPU; active public DB Samsung→Wonik
  network30reads median5.16ms/p955.49ms,6,537bytes. These exclude external latency.
  Public DB at inspection:3754 profiles,integrityok,FK0,encyclopedia sources0;
  Samsung49 business relations/38 suppliers,37 official-list suppliers all with their
  own business-source context. Existing personal runtime/backup volumes preserved.
- Direct scoped source/security review, Python AST13/JS syntax4, credential patterns0
  and diff checks passed; .env remains ignored. No new dependency, CodeRabbit,
  harness, actual AI provider call or order. Extra check containers auto-remove.
  Chrome extension remains unavailable but native Chrome control works on the
  existing single Milkyway tab. AMD current price/brief/revenue and internal link to
  Samsung, pages1→2 and Samsung→Wonik→SK hynix/GFS were visibly exercised.
- DB and workers healthy; readyHTTP200 but dataset/data_gate remainfalse. This is
  not completed paper-feed/data readiness. Toss IP denial remains unresolved; Yahoo
  current prices are display-only and a separate free reference-price paper feed
  is not implemented. Korean24KOSPI/22KOSDAQ taxonomy expansion and broad company
  depth remain. Samsung quantitative annual revenue still has no reviewed rows.
- New actual GPT-5.4-mini/reasoningnone5-call approval remains unanswered. The earlier
  five-call authorization was consumed. Do not call a paid provider or say five new
  tests passed. Details: docs/IT_SEMICONDUCTOR_REVIEW_20261002.md.

## Resumed final release and new five-call approval — 2026-10-02

- The user paused again, then explicitly said "작업 이어서 진행". Work resumed from
  the saved M6 tree. The user then authorized five additional actual AI calls.
  This supersedes the earlier pending-approval entries above.
- Deployed company asset revision20261002-6 with image139a6bc24497. Its full suite
  was506/103.842s OK(skipped15), native8 passed. Chrome existing single tab verified
  Samsung page2→Wonik→GFS/SK hynix. No useReading error; price/source registry remained
  separate from the additional network sources. No new browser tab was opened.
- Exactly5 actual OpenAI calls ran through Chrome preview/approve in the new room
  `AI 기능 재검증 · 2026-10-02 · 승인 5회`. Modelgpt-5.4-mini, reasoningnone,
  outputcap4000, noretry. All5 completed, no error/blank/schema/save failure.
  Call durations7.704/8.357/8.564/7.538/7.790seconds from DB approval→finish;
  tokens10888input/2164output/13052total. No price/billing claim was inferred.
  This five-call authorization is now fully consumed; further real AI needs approval.
- First vague hypothesis prompted3questions. Second saved60-session momentum across
  AAPL/MSFT/NVDA/AMD/AVGO/ORCL/CRM/ADBE, top5, cash100000, exposure1/cap.25,
  calendar30, rebalance_weights=true, stop-.05, per-sidecost.003, filters5/200000/60.
  Third changed only exposure.8/cap.2/calendar7. Fourth changed only stop-.08/cost.001.
  Fifth explained unsupported private order values/5minRSI without saving/changing
  the selected v3. Exact execution-field comparisons and3export AST/spec checks passed.
- Call3 prose confused the20% invested-sleeve weight with a20% total-equity cap;
  saved spec was correct. Call2 holiday wording was ambiguous. Updated SYSTEM to
  explain total-equity min(exposure/N,cap),16%/20%cash versus10%/50%cash, and next
  executable session. Calls4/5 used this update, with16%,cash20%,nonbinding20%cap,
  4percentage-point difference and next trading day correctly explained in call4.
  No new harness. Existing reply history is retained as evidence, not rewritten.
- Added a deterministic allocation example to saved execution-rule tables, including
  caps/cash/cost caveats and holiday timing. Host Node regression covers uncapped,
  capped, retain-quantity and empty-universe cases. Chrome confirmed16%/20%,stop8%,
  fee0.1%. Final visual pass also corrected narrow table header wrapping via CSS.
- AI/source imageb020ce40eb6b full506/86.765s OK(skipped15); host17/2.220s OK;
  AST15/JS5/credentialpatterns0 and diff passed. Native first run failed worker
  start25sec under normal public collection (company-data~101%CPU afterward).
  With company-data/market-details stopped, sameCPU1/RAM768MiB/time limits passed
  all8 stages. One intermediate runner invocation omitted writable/tmp and failed
  before startup; final run used an isolated temporary volume for evidence, removed
  with its disposable container. Do not hide the normal-load startup limitation.
  Native evidence:/tmp/milkyway-it-ai-native-report-20261002.json and matchinglog.
- Executed final v3 using the ordinary app research experiment API, no AI call.
  Actual backtest worker completed2025-10-01..2026-03-31(development151trades) and
  2026-04-01..2026-10-01(validation148trades), sameYahoo generation fingerprint
  2b94e4422026c4eed80ffb00b19c3664c31ea7a5c58b9c9ca695e8f78ec9527b.
  Request→completion observed5.223s with5s polling. This is exploratory current
  universe data, not unbiased performance or proof of profitability. No paper account
  activated and no real brokerage order. Test room/versions remain visible for review.
- Current runtime observations supersede old unconditional Toss-IP claims: Chrome
  showed SamsungToss realtime-trade price and credential confirmed in this session.
  Later healthreadyHTTP200 still has dataset/data_gate=false; completed historical
  bars supported the backtest but today's corporate-action/forward gate is pending.
  No uninterrupted provider/paper-feed success is claimed. Yahoo display data still
  does not automatically become an execution feed. Korean taxonomy/all-company depth
  remain open. See docs/AI_CHAT_REGRESSION_20261002.md for the full bounded results.
- Final CSS image952c974691a25469c4036a2fb16f20a365eb75a92e5a87a000bf05e05891acc7
  deployed to all8 existing services; both paused collectors restored, apphealthy.
  Changed20Python/JS files match full-testedimageb020/workspace/deployedimage bySHA256.
  Final host17/2.623s OK, Chrome final v3 calculation table headings now stay on one
  line. One existing Milkyway tab remains showing this test conversation/controls.
  No disposable check containers remain. Personal runtime and backup volumes intact.
- This milestone is ready for the normal branch commit/push after direct review.
  Record/confirm exact GitHub head and CI in the next handoff; do not infer CI success
  from the prior commit8931bdd's run. Main scope/remaining limits are documented above.


## 2026-10-02 · one US session paper operation armed (follow-up)

- Latest request: run today’s US regular session with the best existing strategy;
  compare backtests and explain survivorship bias. Additional AI authorization was
  already consumed in the prior milestone. This follow-up made 0 AI calls.
- Prior milestone is committed/pushed at 044056c8b880ce6e6242701bb40713c6d4ab7372;
  GitHub CI36998426773 succeeded. This supersedes the older “ready to commit” line.
- 8 saved strategies → 6 distinct specs; 18 app backtests (full year plus two
  separate half-years) completed on the same dataset fingerprint. C2/C3 got
  separate 0.1% cost comparison copies; original specs preserved. Full-year
  Sharpe selected C5, existing strategy9ac37176f4bc4feea965f6f065957ad3.
  2025-10-01..2026-10-01: return10.9586%, Sharpe0.873964, MDD-11.4524%.
  First half-1.6043%, second half+8.5307%; half runs restart cash independently.
  No untouched holdout/PIT/profitability claim. See docs/PAPER_SESSION_20261002.md
  and docs/PAPER_COMPARISON_20261002.json for all candidates/job IDs.
- Added durable personal_paper_sessions table (local ResearchBase), optional
  account session_date, US holiday/DST/early-close bounds, per-fill date guard,
  expiry before provider I/O, immutable last-known summary, expired resume denial.
  No fake closing sale; retained holdings are not proof of official closing value.
- Actual account b1042a427dec4e1991be17f24f8becc8 created11:44UTC, active, no fills.
  Name: 미국장 하루 검증 · 2026-10-02 · Momentum LowVol.
  $100,000; 60% invested in top3 out of AAPL/MSFT/NVDA/AMZN/GOOGL/META;
  momentum60weight.6 + lowvol20weight.4; 7calendar day rebalance; stop-5%; fee.1%.
  Open13:30UTC / first rebalance13:35UTC / end20:00UTC (KST22:30/22:35/05:00).
  It is armed for the upcoming real session, NOT a completed day of trading.
- Toss quote-only preflight11:37UTC returned all6 US symbols in5.855s. Current
  completed daily history through10-01 exists; today's action check awaits open.
  Personal data worker retries every60s; paper refuses missing/stale quotes and
  unverified actions. Do not bypass those gates to manufacture fills.
- caffeinate PID25591 prevents idle sleep until20:10UTC/05:10KST, automatically
  exits. Does not protect against lid/manual sleep/power/network/Docker shutdown.
  Later restart expires the dated account before new fills, never resumes Monday.
- Final local full suite517/70.232s OK(skipped16Node); host18/12.038s OK. Initial
  full run had1 existing provider warmup10s timeout under concurrent collector
  load; repeat with company/detail collectors temporarily stopped passed at same
  1CPU/768MiB. Both collectors restored; no timeout weakened. Direct scoped
  security/code review done; no full public scan claim; no new dependencies.
- Deployed image097f64ade4b15072d52754d4f2293ceb8dceb9724bf0a635ed97bb6312d4927d
  in all8 existing services, runtime/backup volumes retained. Median of5account
  API reads25.275ms. Browser now has unrelated user Docs/Drive tabs; did not
  navigate/close them or add tabs. New account visible at local portfolio view.
- Must confirm final push/CI and current paper worker heartbeat before finalizing.
  At market close, read account.paper_session.summary plus full fills/history;
  report actual fills or specific waiting/error state. Never describe premarket
  setup as successful full-day paper operation.

## 2026-10-02 · energy scope and immediate memory reduction (in progress)

- Paper-session milestone committed/pushed ef7dc32320f6fb5290add6c34728843f166425b4;
  CI37002994456 completed successfully. One-day account remains armed for today.
- User clarified energy means a comprehensive industry encyclopedia, not a sample
  of major issuers. Sector completion is NOT achieved. Initial universe107 includes
  IXPZ6 (XLE sector future) and HNR (liquidated Harvest); company coverage is shallow.
  Scope must include MLPs missing from broad common-stock ETFs and dated corporate
  changes. Official Hornbeck release confirms Helix merger completed2026-09-01;
  legacy Helix2025 annual is not the combined company's annual. ExxonMobil holdco
  reorganization2026-07-01 needs predecessor reporting provenance.
- Uncommitted classification fix rejects fund synthetic identifiers without equity
  SEDOL, dated contract names and exact-name historical HNR liquidation. It also
  filters legacy caches. Focused8tests passed; not yet full-reviewed/deployed/pushed.
- Research uses free official sources, 0 AI calls. Temporary sequential collector
  /tmp/energy_sources_collect.py saved56annual/quarter documents for28issuers with
  SHA256+date manifest in /tmp/milkyway-energy-research before being stopped.
  Downloaded documents have NOT all been read/summarized/verified. Baselines:
  /tmp/milkyway-energy-baseline.json and /tmp/milkyway-energy-profiles-baseline.json.
- User then requested memory cleanup. Around12:12UTC:8containers~1.05GiB; company-data
  ~308MiB/~103%CPU; market-details~148MiB; backtest~85MiB. Host16GiB, swap~5GiB.
  Stopped company-data, market-details, idle backtest-worker after confirming all20
  jobs completed/noqueued/running. Terminated only our temporary collector PID29036.
  Existing data/volumes retained. Do not blindly restart all8services.
- Remaining5:app,market-data,paper-worker,personal-data,backup total~534MiB at12:13UTC.
  /health/startup returnedready. Paper/data/backup needed for today's real-time
  exercise remain running. New backtests and company/detail refreshes require their
  paused workers to be started when needed; cached pages still work.
- CUA inventory now ChromeextensionID2profile'seung zoo', oneMilkyway#strategy tab
  id810509711. Native Chrome confirmed one tab (~223MBtabindicator); no duplicate
  research tabs to close. Did not killrendererprocesses or touch userSafari/Word/Code.
  Browser tab has expiredlocal-session warning, original8:47PMdata; refresh only when
  needed, don't create APIlogin that invalidates user's browser session unnecessarily.
- Continue energy implementation with one heavy collector/test at a time, default
  5services during research. No further paid AI approval remains.


## 2026-10-02 · Energy intermediate changes and graph recovery

- Resource request remains in effect: only app/market-data/paper-worker/personal-data/
  backup run. company-data/market-details/backtest-worker remain stopped; no duplicate
  browser tabs, one heavy test/build/collector at a time. Do not blindly start8.
- Added Energy industry guide (7GICSsubindustries, physical chains, units, formulas,
  regulations, bottom source links), CVX/COP/VLO primary-source Korean notes, exact
  FY2025 revenue tables and6contextual counterparty profiles. Only an intermediate
  change; even these3companies do NOT meet all-sector/full-company completion.
  MLP/fullissuer scope and remaining company/contract/competition research still open.
- CVX composite segment/geography and VLO qualified product coordinates are exact
  symbol+CIK allowlists. COP subtotal hierarchy requires matching sums. Curated
  coordinates replace old same-source/period values to avoid English-label duplicates.
  All3issuer revenue group root sums matched original reported denominators.
- Found actual public graph corruption during app restart at~12:55UTC. Trading
  ledger club.sqlite3 quick_check was ok and paper/personal workers stayed active.
  Original197,378,048-byte graph preserved at runtime/company-details/
  quarantine-20261002T125625Z/graph.sqlite3, SHA256
  8d9f82690d0489975f36a7e17676097e03bc4b98013810b6fa717c83c70f52d1.
- Restored ONLY public graph from backup milkyway-20261002T114320Z-d0c23e5d.zip,
  validating manifest hash/size and full integrity_check. Backup graph hash
  4f06fdce8720cd160690af63e582006b7f88d695b7f18105382f8b276da358bc.
  Existing3815JSONprofiles retained and reimported through bootstrap; user ledger/
  keys/accounts were not restored. Do not claim all graph-only post-backup data
  was recovered; keep corrupt original for further inspection. Post-restore both
  DBquick_checks passed. App subsequently healthy, new backup130623 succeeded.
- Fixed graph connection's unsafe raw os.open/close of an existing SQLite file.
  Separate-process POSIX lock regression failed on prior image and passed on fix.
  O_EXCL create-only plus process lock protects first creators; existing regular
  files checked no-follow and chmod no-follow. Raced-symlink target data/mode tested.
  Independent read-only reviewer approved bounded patch after two suggestions;
  no remaining concrete High/Medium in scope. Not proof of original corruption cause.
- Full528tests87.704s passed(skipped17Node); host19Node/frontend tests1.076s passed.
  Final image focused70tests17.077s passed. Initial failures were test runtime
  permissions/noexec setup, subsequently corrected; host .venv iCloud dataless
  import also caused an interrupted run. Direct source/security/performance review
  recorded in docs/ENERGY_REVIEW_20261002.md; no CodeRabbit and0provider AI calls.
- App final image7ab8a5b63636ad0c725bb2750e17deed54fae5607e51c9c4bd3a86beac2d2202.
  market-data/backup and stopped company-data/market-details/backtest use earlier
  14f9c9fdaaffeaf19de606699d40eea360e2116f60f785ec7a9b7186ce35a23d, already has graph fix.
  paper/personal-data remain prior097f64ade4b15072d52754d4f2293ceb8dceb9724bf0a635ed97bb6312d4927d.
  Main final difference separates paper readiness from optional stopped backtest worker.
- CUA Chrome2 existing tab810509711; current controlled handle energyReviewTab
  (browser energyBrowser). Native cleanupChrome has snapshot rendering issues;
  extension screenshot showed actual page correctly. Verified industry links, source
  disclosure, VLO product/segment tables and direct DGDentity navigation. No new tabs.
- Today's real paper session remains open13:30UTC / initial rebalance13:35UTC /
  expires20:00UTC, account b1042a427dec4e1991be17f24f8becc8. Check actual session
  after open, pending today's Yahoo action data gate. Do not claim a full day yet.
- That checkpoint was committed/pushed as dfb39cd1ba22b77b3a7cbf9c590fddde7a21de6e.
  GitHub CI37012409210 succeeded in verify and postgres-integration.

## 2026-10-02 · resumed Energy refining research

- User asked whether Energy work was actually happening. Acknowledged that the
  preceding final answer had ended research; do not claim background research
  continues after ending a turn. Resumed with substantive primary-source work.
- Added MPC/PSX/DINO annual/quarter Korean analysis, actual operating contracts,
  11 contextual counterparty profiles and MPLX role notes. Existing CVX relations
  extended without replacing prior work. Six main Energy companies now have expanded
  notes (CVX/COP/VLO/MPC/PSX/DINO); NONE is certified complete across every criterion.
- Reviewed primary SEC FY2025 tables and Q2 changes plus corporate/FTC contracts.
  Six new source documents' hashes/byte lengths match retained /tmp evidence.
  DINO Aug3 Chevron/SK Enmove base-oil agreement and PSX Oct1 United supply route
  checked. Historical Linde2021 and Speedway2021 contracts explicitly dated.
  Raw oil sellers were not guessed from pipeline operators; Shell2023/24 shares
  are not current customer shares. WRB's former Cenovus stake is not current JV.
- Exact revenue roots reconcile: MPC132699m/PSX132376m/DINO26869m USD.
  Added exact MPC/PSX corporate axis, DINO product subtotal and separate RIN subset
  view. Canonicalize legacy cache before merging; exact promoted facts no longer
  duplicate hidden raw appendix entries. Eight brief cards remain bounded; further
  reviewed notes are visible in product/business/driver sections.
- Tiny positive revenue percentages show <0.01% rather than0%; same-kind/source
  graph neighbours with reviewed business descriptions precede bare legal entities.
- Latest whole regression534/93.432s OK(skipped17Node), host20frontend/structure
  tests2.994s OK. Release image focused70/1.855s OK.13changed app/test SHA256 files
  matched deployed image. Direct code/security review, no new dependencies, no
  CodeRabbit. Actual AI provider calls0; previous5-call authorization exhausted.
- Final app image ef7d5d589a377528a099069b7d9db128a8d750fac63a2be9e3ca29c803659e3f.
  App-only Compose deployment; paper/personal-data and their real session retained.
  Other running services retain their prior images (all graph writers had lock fix).
  company-data/market-details/backtest-worker stay stopped. No collector restarted.
- One-at-a-time temporary --rm jobs; normal5services only. Brief test job used ~171MiB,
  host memory_pressure reported36%free. During US session paper/data workers grew to
  ~184/237MiB; don't stop them just to reproduce idle premarket memory numbers.
- Existing Chrome2 tab810509711 reused, no extra tabs. Verified MPC Korean briefing,
  external revenue and Green Bison linked page; DINO product hierarchy and actual
  pipeline/base-oil supplier roles. Final current tab is DINO's company page.
- Today's paper session's first3fills at13:35:08UTC verified by read-only ledger:
  MSFT38.389893323124184@520.45, AAPL60.12373795952631@332.315,
  NVDA84.58941566477556@236.2. This is not a finished-day result. Expiry20:00UTC
  (Oct3 05:00KST), idle protection until20:10UTC; preserve live session.
- Details and limits: docs/ENERGY_REFINING_REVIEW_20261002.md. Remaining: full Energy
  issuer/MLP scope, counterparties/raw suppliers/competitors/market-share research,
  midstream/LNG/E&P/services/coal/nuclear fuel. Collected docs are not completed research.


### Final refining UI and workspace check

- Final native Chrome reload confirmed reviewed operating companies first in DINO
  graph, including Industrial Oils Unlimited before bare numbered subsidiaries.
  Saved /tmp/milkyway-energy-refining.png; kept existing one Chrome usertab.
  Extension disconnected; native controls worked. DINO quote remained awaitingreceipt.
- Postdeploy both club.sqlite3 and public graph.sqlite3 quick_check=ok.
  Running5services remained app/backup/market-data/paper/personal; app159MiB,
  backup33/market251/paper185/personal237. macOS memory free61% at finalcheck.
- iCloud temporarily evicted .git/index/refs/objects and docs, blocking git/read.
  Requested brctl download .git docs. Created a temporary safety checkout at
  /tmp/milkyway-refining-publish-20261002 from remote dfb39cd and copied only
  deployed changed code/tests/docs (no credentials/runtime). Original files then
  hydrated; all13 local app/test files matched verified release SHA256 again.
  Continue using original Milkyway repo; no reset/overwrite of local code. Temporary
  checkout was not pushed and is only a fallback. Final commit occurs in original.

## 2026-10-03 · uninterrupted Energy continuation

- User explicitly asked to continue until whole-sector research is complete; do not end
  at a batch, commit or deployment and do not imply background work after a final reply.
- Added WMB/KMI/TRGP/OKE/LNG Korean business/products/operating/contract notes, original
  FY2025 revenue tables and 15 contextual counterparties. Existing operating links kept.
  Eleven expanded primary profiles are NOT certified complete across all criteria.
- Original collection finished: 345 annual/quarter documents for 185 ticker targets,
  zero collection errors. Target counts are not unique-company or research-complete counts.
- Exact TRGP operating segment coordinates prevent internal/elimination mix; -5.3m
  adjustment explicitly excludes percentage. OKE product/service subtotals and LNG
  third-party subset bound to exact issuer/CIK/document/period. Historical source date
  for EOG IPM corrected to2022-02-24; WMB Momentum closed2026-09-03; Stage3 handed over
  Aug28; Petrobras Sept29 newSPA, no guessedstartyear. No paid/model provider calls.
- Focused54 passed0.764s; full539 passed54.552s(skipped17Node); host9frontend passed
  6.141s. Initial full-test setup failures solved only in isolated test tmp/runtime.
  Direct diff/security review; no CodeRabbit. git diff --check before commit required.
- App-only image81cdd8d58504416d17f62326a943810fc8a1ddf30cbd2d1e9b9e49465c82f1ce
  deployed healthy. Five existing services only. Paper session expires20UTC, preserve
  workers/caffeinate and check actual day-end report if work continues past then.
- Offline merge benchmark512MiB/1CPU500reads:2.844s/p503.610ms/p9511.273ms/RSS33.1MiB.
  This excludes network/graph/UI latency. Native Chrome existingone tab verified LNG
  updatedanalysis/contractstatus/revenuehierarchy/linkedcounterparties/quote.
- Next immediate substantive work: EPD/ET/MPLX/PAA/PAGP/WES/HESM own original reports,
  full issuer registry and per-field audit, E&P/services/coal/nuclear fuel/royalties/
  shipping. PAA Canadian NGL sale closedMay12,2026(Keyera), ET LakeCharles export
  development suspendedDec2025, HESM Chevron sponsor/GIPexitMay2025; current/source
  scope needs actual review before editing. XOM current CIK2115436 successor Jul1.
- Temporary original documents/evidence in /tmp/milkyway-energy-research; exact source
  manifests/SHA retained. No user secrets/runtime copied. No additional AI approval.

### MLP milestone continuing work

- 0b84a52b09cbb9c36d388770683e3c2ceae86c03 pushed; GitHub CI37033177582 SUCCESS
  verify+postgres-integration. Local app remains gas/NGL/LNG image until next release.
- New EPD/ET/MPLX/PAA/PAGP/WES/HESM notes, exact original tables and7context records.
  58focused tests passed1.051s. ExactET3axes external-only,HESM2axes; no generic widening.
- WES4.281744b is acquisition PRO FORMA, actual3.843403b revenue+other; don't confuse
  it with a second registrant. HESMcontract1.6172b vssegment1.6213b. MPC48% excludes
  significantnoncashitems. ActualSeaway supplier payments andMPCITengineering supplier
  roles added. Latestbriefsources boundtoquarter whereannualdoesnotcover2026facts.
- Wholeissueridentity audit discovered APC=ARKOPetroleum(current), not oldAnadarko;
  SMC=SummitMidstream, SUNC=SunocoCorp. SECexchangeindexOct3 downloadedpublicly;
  FGPR/RSRVOTC; AMEN/UNTC absentindexbutnotthereforeinactive.
- Continue fullEnergy; do not final after thiscommit. Next wholeissuerregistry,
  currentXOMsuccessorCIKfix, restmidstream/compression/LNG/E&P/services/etc.

### Services and issuer directory continuation

- ee911c59c86bf4542a0e894715675b74855fcbc4 pushed; CI37037198451 SUCCESS.
- Added DTM/AM/KNTK/CQP/SUN/USAC/KGS/AROC edited primary notes and19context records.
  Expanded26mainprofiles are NOT complete across all criteria. Do not stop after thisbatch.
- Added187issuer research roster, SEC current ticker/exchange identity plus official
  AMEN/UNTC IR; official disclosed sectors override research navigation. Business groups
  are not GICS. Pending classifications remain explicit. API list1100/static500 bound.
- AM customer relationship amortization negative adjustment preserved; KNTKserviceMVC
  subset, CQPexact2axes party/product; acquisition/current/planned states are distinct.
  Ariel package-provider listing only proves KGS/AROCpartner role, not purchase value.
- SEC contract revenue label corrected without changing source/value/period; current
  XOMsuccessor CIK2115436 used while historical filing identity remains original.
- Full555tests91.998s OK(skipped18Node); host10frontend4.828s OK; postprecision11/0.093s OK.
  Offline p95directory2.186ms/merge5.797ms/SQLite snapshot20.106ms/RSS55.1MiB.
- App-only deployment with workers/volumes retained; startupready. Native Chromeexisting
  one tab verified187displayed roster/group filter/USACedited business+equipment suppliers.
  No paidAIcalls, no CodeRabbit, no additional agents. docs/ENERGY_SERVICES_REVIEW_20261003.md.
- Finalapp5a337842418fdabca30d6e3aa7902f02ad00b3382b7d6a4a3741e96a14d8c66f;
  18app/testfileSHA256 matched. Postlayout host10tests1.377s passed. Prior16:08 appimage
  observed529acc6640d2, correcting the older81cddnote as a dated observation.
- Next active research EOG/FANG/OXY/DVN/EQT/EXE/AR/RRC. Originallatestquarter: Devon+Coterra
  closedMay7,2026; OxyChem soldJan2,2026; EQTMVPConEd3.94%stakeboughtMar30; EXENG3CO2
  delivery to Exxon beganFeb2026. Check exactoriginals before curating, not stale2025scope.

### Upstream and supplier-source continuation

- Previous services milestone a9827017d76561c184b7d72a6979a7ce3974a22a pushed;
  CI37043161067 SUCCESS. No final at a milestone; whole Energy request remains active.
- Added EOG/FANG/OXY/DVN/EQT/EXE/AR/RRC notes,27context profiles,16original receipts.
  Main expanded34 are NOT certified complete across all required fields.
- DVN exact product/location axes; OXY gross segments/own E&P products exclude whole
  percentages; EQT exact segment metric and equivalent production subtotal de-duplication;
  FANG/EXE own production vsresale hierarchy. Exact years/source/CIK retained.
- EXE Twin Eagle CLOSED Sep16,2026; Delfin Apr22 SPA FIDconditional and oldGunvor
  terminated. AR Utica sale CLOSED Feb23. Supplier originalPUMP/LBRT/SND shows actual
  EOG/OXY/EQT/XOM/PR services. Range own drilling/completions page has namedroles but
  unknown publication/currentcontractduration. Do not treat these as verified2026newdeals.
- Flowco FLOC is NOT ProFrac. PrimarySEC ProFracACDC/CIK1881487 annualMar13/latestQAug6
  foundmissingroster. Next own providerbatch must addit+resolve Rangecontextpublicalias.
- Focused48 tests1.000s; host21tests16.456s OK. Final fullsuite/deployment pending;
  first final discover command without -s tests discovered0 and is NOT validation evidence.
- Offline EOG performancep95 merge3.209ms/graph48.687ms/RSS55.6MiB; directory1.772ms.
  No actual AI calls; CodeRabbit unused; no new agents; serial heavyweight jobs.
- docs/ENERGY_UPSTREAM_REVIEW_20261003.md records scope,calculations,current gaps.
  Continue providers,allremainingroster,fieldaudit. Preserve five necessaryservices and
  paper sessionexpires20:00UTC; caffeinate25591 until20:10UTC. Otherworkers remainstopped.
- Final full562tests65.979s OK(skipped18Node,host21alreadypassed). App-only image
  9e5a53050a179da3ccd305b50d7e19e75c82088ecbfbc7284563fb893910f80a ready;
  10source/testSHA matched; appDB+graphDBquick_checkOK. Existingone Chrome tab confirmed
  directoryCSSrowalignment and EXEown/revenue/latestactualcontracts+Keydetailclickthrough.

### Service-provider continuation · 2026-10-03

- Upstream1308039c61a9e9fb3141bd7e1d173c27b283cd73 pushed; CI37049578304 SUCCESS.
  Whole Energy objective remains active. Do not end at a batch/commit/deploy.
- Added12 provider dossiers: SLB/BKR/HAL/PTEN/PUMP/LBRT/SND/AESI/FLOC/ACDC/DTI/KLXE,
  24 original SHA receipts, actual equipment/tool/field customers,36 context profiles.
  Registry190; main expanded46 are NOT all-field completion counts.
- Exact FY2025 provider revenue coordinates: gross/internal elimination no percentages;
  Atlas shortfall not additive; DTI rental/sales vs regional rounding; other annual
  reports do not reuse reviewed elimination. Flowco Valiant note121.3m vs MD&A113.2m
  acquired cash inconsistency is explicit, not silently reconciled.
- Manual ProFrac range-profrac→ACDC identity bridge preserves old bookmarks/edges,
  normalizes old cached name, rejects FLOC/conflicting tickers, keeps unrelated
  private registries tickerless. Public cached financials preserved during seed.
- Final570 tests61.214s OK(skipped18Node); host26tests all OK; focused38tests8.874s OK.
  Final perf1CPU/512MiB p95 directory3.590ms, ACDCnotes3.820ms/graph32.823ms/RSS57.7MiB.
- App-only image5ae0b7e3b9d69f039f3b9b0ce018aaced8e9d7a504b847bde5c9f32edcfd081d,
  15appSHA match, startupready/healthy. ExistingChrome1tab verified newProFracname,
  graph→LBRT, single-segment revenue explanation after intentional static reload.
- 2026-10-02 US paper session completed20:00:02.510410UTC, paused,3BUY fills,
  77valuationpoints. Last-known99,710.06549USD/-0.2899345%; last-complete19:56:29
  valuation99,632.630394USD. closing_price_verified=false; no synthetic closing sale.
  details docs/PAPER_SESSION_20261002.md. Activeaccounts0→idlepaper-worker stopped.
  Four necessary services app/market-data/personal-data/backup remain. Runtimevolumes
  preserved. Start paper-worker before new paper run. Caffeinate25591 autoexpires20:10UTC.
- No actual AI calls, no CodeRabbit, no new agents. Serial heavy jobs. Whole public
  security scan still requires managedworkspace; bounded source review only.
- Next12 FTI/NOV/WHD/WTTR/FTK/NINE/TTI/NBR/HP/WFRD/RES/RNGR originals already
  in /tmp/milkyway-energy-research, bounded paragraphs /tmp/energy-equipment-key-blocks.json.
  WHD CactusInternational CLOSEDJan1(not Jan2announcement); WTTRPilot Sept24deal
  pendingQ4; FTKLithium/ProFrac saleleaseback and NINEfreshstart require own review.
  Also fill financials currently absent for newly added providers, field audit,
  foreignADR/newOTC inventory audit and all remaining industrial groups.

### Equipment and original-financial continuation · 2026-10-03

- Whole Energy remains active. User explicitly rejects stopping at partial batches.
  Do not final after this milestone/commit/deploy. No actual AI calls or new agents.
- Added12 equipment/drilling/water/completion dossiers and34 context profiles;
  receipts58/mainedited58 are NOT all-field completion counts. Registry190, twelve
  source-based business navigation groups updated independently of official GICS.
- Original annual financial archive182receipts:173populated/1344values. ExactCIK,
  consolidatedcontext/annualduration/currency/unit/declaredDEIperiod validated;
  signedloss/OCF kept. Reuse alreadyfetchedannual ifcompanyfactsfail; no new call.
  9empty PBA/SOBO/TRP/GFR40Fattachments andAPC/CRT/NRT/PBT/SBRplaintables remain.
- XOMold34088annual/new2115436holdco, HOS2025Helix/2026combinedgroup, NINEpredecessor/
  successor andACDC68.8m mezzanine preferredstock(notNCI) scope cards added.
- WTTRdetailed1.420376b−13.032m=1.407344b; notgrosssegment1.421047b/13.703m.
  NBR Saudi1b isinsideNonUS; FTKothercountries excludesUAE. Exactdocument/year
  qualifiers avoid applying these FY2025 adjustments to other reports.
- FTKPREPAofficialterminationAug18 confirmedlaterAug19 8K; norevenue/payment/
  equipmentdeployment. PowerExpectationsidentityhasseparateearlierreceipt.
  WFRDNCSclosedSep1, domicileIrishcourt/Q4pending. RNGR AWSclosedNov7,2025;
  HessECHO3rigs delivery2027. TTI FIDMay28 andactualDCDconstructioncounterparty.
- ActualUI foundoldEX21two-name-columns parsedasjurisdiction, geographiclegalforms
  asfakecompanies. Newboundedcompany_subsidiaries parser andlegacycleanup fixthis.
  Matchingcompanyfactsfigureonlycorroboratedwhenissuer/tag/currency/period/date/value
  exactlyagree; API sourcekeptbelow, differentfigures/dates/documentspreserved.
- Final602tests85.857s OK(skipped18Node); host21frontend/statictests1.915s OK.
  A host attemptincludingHTTPtestmodule failedmissinghttpx, notsuccess evidence.
  Screenregressions73/2.136s andfinalfocused65/1.471s OK.
  512MiB/1CPUcoldseed551entities4.031s/RSS61.1MiB/SQLitequick_checkOK;
  directoryp953.828ms/FTKmerge7.271ms/graph119.393ms(p5034.577)/RSS61.5MiB.
- App-onlyfinal8793551c7805ace9acd01ecc46faae4b568179717021ad900d0c8f50ac9afc68,
  22appSHA match, startupready. NativeChromeoneexistingtab verifiedFTKsinglefinancial
  row/noTexasCorp-or-OklahomaLegalFormlinks; NINEfinancialscope; graph→NewGen
  detailandreversetoNine. Fournecessarycontainersonly; paperworkerpaused/stopped.
- Next: missingUSlistedforeignShell/BP/TTE/E/EQNR/PBR/EC/YPF/SU/CNQ/IMO/CVE/BTE/
  VET/OBE +TS/PDS/SSL andnuclearCCJ/DNN/NXE/EU/UUUU currentidentity/originalaudit.
  Collectorprepared /tmp/milkyway-energy-equipment-review/global-collect.py,
  Useexistingissuer-exchanges-20261003.json; nofakequarterfor6Kcovers. Submissions23
  received. Initialtempcollector rejectedzero-paddedstringCIK vsint andstoppedbefore
  annualdownloads; exactnumericCIKcheckfixedandannualsearchnotlimitedby12recent6Ks.
  Restartcorrectedcollector; do NOTcount23annualreceiptsascollectedyet.
  Thenremainingwhole roster/fieldaudit/namedlinks. FTKEX21actual4subsverifiedfreeSEC;
  newcollectorwillreadfourcorrectly; cachedtwojurisgenericcorrectedbutneedsreviewed
  fullfour-sourceupdatewhencontinuingdossiers. Do notlose thisfollowup.

### Integrated major continuation · 2026-10-03

- Whole US Energy objective is still unfinished and active. User explicitly asks
  to continue until the whole sector is researched and edited. Never end at a
  partial batch, commit, test run, or deployment. Listing/receipts are not completion.
- SEC identity audit and annual collector completed 23 foreign US listed issuers;
  BP 29,303,585-byte annual needed separate bounded research download. Actual
  originals, SHA, access dates in /tmp/milkyway-energy-research. No fake 6-K quarters.
- Registry 213 now; added nine edited profiles XOM/SHEL/BP/TTE/E/EQNR/PBR/EC/YPF,
  35 contextual counterpart pages, named project/supply links, 72 annual financial
  values and 126 revenue rows. 190 receipts/181 populated/1,408 figures are coverage
  counts, not full company/sector analysis. docs/ENERGY_MAJOR_REVIEW_20261003.md
  records exact dimensions, gross elimination, currencies, date/scope limits.
- BP day-first DEI date and IFRS customer-contract revenue fixed. Revenue axes
  remain issuer/CIK/document/period bounded. PBR product subtotal/geography nesting,
  EC external third-party axes and COP billions, XOM sales vs income, EQNR gross
  148883m minus internal42421m, BP three denominators separately verified.
- Actual FTK Exhibit21 four entities/jurisdictions now reviewed; same generic cached
  entries replaced only for exact identity/date/document/kind. New edited brief
  replaces old cards before schema limit, preserves citations; enrich idempotent.
- Source-bound updates: Shell ARC closedSep2; LNGCanada Phase2 FIDSep29 future28Mtpa,
  five partners' own gas/lifting vs JGC/Fluor EPC. Eni Plenitude joint-control Oct1
  deconsolidation despite65.03%; BP Castrol completion not proven. XOM Baytown paused,
  active named CCS distinct; YPF local common split != ADR split. No anonymous buyers.
- Final actual image617tests34.540s OK(skipped18Node); host9modules21tests1.196sOK;
  focused63/0.776s, offline70/0.682s. Source16SHA matched final actual image
  000037b7d025b715a4e81cee90aabf862f659566039cfed0e58cebbe1deb4867.
  App-only personal update completed; startupready(web+DB)/healthy confirmed.
  Existing Chrome1tab verified Shell brief/revenue/financials, relationpage2,
  graphclick→LNGCanada detail with two EPC and five partners. Four existing services.
- Offline512MiB/1CPU cold592entityseed1.330s/RSS63.8MiB/SQLitequick_checkOK;
  directoryp950.822ms/merge2.625ms/SHELgraph12.722ms/RSS64.2MiB. No network/UI RAM claim.
- Direct bounded code/security review; no dependencies, permissions, SQL or order
  changes. No CodeRabbit, actual AI provider calls(0), or new agents. Whole public
  scan still needs managedworkspace; no OCI/KMS or whole-repo scan claim.
- NEXT immediately continue Canadians SU/CNQ/IMO/CVE/OBE/BTE/VET and PDS, then
  TS/SSL/nuclear/context+whole remaining roster. Newly completed FREE observed
  attachments collector /tmp/milkyway-energy-equipment-review/canada-collect.py
  fetched26AIF/MD&A/auditedfinancial originals(60,966,841bytes), same parent SEC
  accession only, original SHA receipts in canada-attachment-manifest.json.
  CNQ/IMO originals already full; 40-F cover absence does not mean no financials.
  Need exact attachment/parent association parser, no injected DEI/fake XBRL label.
  PDS main annual contains AIF rather than guessed extra URL. Read actual source.
  Then named suppliers/customers/current JV, essential KO notes, all-field audit.
  This milestone still needs commit/push+new CI confirmation; continue after it.

### Canadian original-source continuation · 2026-10-03

- Whole Energy remains unfinished and active: 213 research entries, 75 edited
  main companies, 138 unedited. Counts are not all-field completion. Continue
  immediately after Canadian commit/push; never final at a partial milestone.
- Added SU/CNQ/IMO/CVE/OBE/BTE/VET/PDS edited Korean dossiers, 25 role-specific
  context pages, 56 annual financial values and 55 revenue rows. Actual AIF, MD&A
  and audited attachment receipts; current assets vs annual/discontinued scope
  kept separate. docs/ENERGY_CANADA_REVIEW_20261003.md holds detailed evidence.
- Correct previous PDS note: main 40-F is cover, actual SEC ex99_1 AIF separately
  collected SHA d0cc5029f0e2fab7be4bdab7ec808e52229389f66f441e6d9f23c4c4008db9c4.
  Verified same CIK/accession/date/observed cover link before sharing XBRL resources.
  No invented DEI. Duplicate resource conflicts rejected. Precision-bound CVE
  2740m cash vs rounded2700m; VET limited continue/discontinue balance totals.
- OBE PCU11 Whitecap operator verified government unit65643 on actual PDF p33,
  asofSep17,2026; OBE45% from AIF, other ownership unknown. Named GLJ/ISN service
  and Sept14 compressor/guidance update. SU Komatsu secondPC9000 actualAug2025
  delivery distinguished from initial plan. CVE WRB soldSep30,2025; new transaction
  kind separate from current business/JV and shown in dedicated graph filter.
- Final source638tests32.554s, actual packaged638tests33.517s OK(skipped18Node);
  realhost10frontend modules26tests1.166s; focus83tests0.530s. Direct bounded
  source/security review, no dependencies/auth/schema/order changes; noCodeRabbit.
- Offline512MiB/1CPU cold622entities1.224s/RSS62.4MiB/quick_checkOK; directory
  p95.746ms, CVEmerge1.791ms, graph11.506ms/RSS63.0MiB. Not network/UI RAM claim.
- App-only image0ff07807fb49d76f8490bd69c6b942be318fda40c56388ae573f858421c923f7;
  18appSHA match; healthy/readiness200. ExistingChrome1tab verified CVE notes,
  financials, transactionfilter, graph→HMLP and reverse CVE link. Observed expired
  local12h session401 recovered after refresh(localauth200, detail/price200).
  CVE32.40USD actualYahoo closed quoteOct2 20:00:02UTC, not live-new-transaction.
- Prior major commit0ccca69905bba4551d414a25cf5aac4e67de83e3 pushed; CI37079074349
  SUCCESS. Canadian commit pending at this context append. Four needed services,
  paper worker paused/stopped; runtime/backup volumes preserved. 0 actual AI calls.
- NEXT: ENB/PBA/TRP/SOBO Canadian oil/gas transport actual attachments/contracts;
  TS/SSL, then whole remaining producers/refiners/marine/fuels/nuclear/trusts.
  /tmp/milkyway-energy-remaining-20261003.json lists actual remaining138.
  Original annuals already local in /tmp/milkyway-energy-research; reuse receipts.
  FTK actual four subsidiaries source verified earlier; no global public scan
  unless managedworkspace; no paid data, new agents, OCI/KMS claims.

### Infrastructure/materials continuation · 2026-10-03

- Whole Energy remains unfinished and active. 213 entries, 81 edited main
  companies, 132 remaining plus all-field deep audit. Continue after commit/push;
  NEVER final/stop at a partial milestone. Literal all knowledge is not claimed.
- Added ENB/PBA/TRP/SOBO/TS/SSL Korean dossiers and role-specific counterparts,
  39 new financial figures, 64 revenue rows. 200 receipts/194 populated/1503
  financial values are coverage, not completion. Actual observed same-accession
  audited attachments PBA/TRP/SOBO/SSL; SSL FY2026 endsJun30/ZAR.
- docs/ENERGY_INFRASTRUCTURE_REVIEW_20261003.md records exact coordinate/metric/
  denominator checks, current named supplier/customer/EPC roles and project stages.
  SOBO169m corrected to Keystone variable toll dispute revenue reduction, NOT
  lease; gross1634m separate revenue_type, product1465m+403m+118m=1986m, no doubleadd.
  TSrounded segment totals differ157k; no fabricated allocation. PGI/ORYX/investee
  own revenue excluded. TransMountainCrown890kbpdcapacity preservesDINOcontext;
  AirLiquide merged older XOMevidence with actual SSLoxygen/renewables.
- Final source645/119.557s OK(skipped18Node), host9modules21/1.199s OK, focus51/
  1.923s. Actual package645/146.540s OK18skip. Intermediate verifier runs failed
  due PYTHONPATH/APP_ENV and tmpfs exec/runtime settings; corrected verifier only,
  no app security change. Initial archive count expectation198 updated to200.
- Offline512MiB/1CPU seed685entities4.186s/RSS63.0MiB/quick_checkOK; directoryp95
  3.735ms, PBAmerge11.077ms, graph63.121ms/RSS63.5MiB;80focus1.604s OK. Measurements
  not network/UI or total RAM; no causal comparison claim with earlier Canadian run.
- App-only imagebac88e809780636f696e8b9424405cc84a7c1da650dad4aa01d7b2d4360ae953,
  10editedsource SHA match;healthy/startup200webDB. /health/ready503 expected existing
  paper/backtestworkerfalse, database/dataset/data_gate/personal_dataworkertrue.
  Do NOT claim all trading workers active. Four existing services, volumes preserved.
  Chromeoneexistingtab PBAbrief/products/financials25businessedges paged8; actual
  graphclick→SiemensEnergy detail with reversePBA/Greenlight customers confirmed.
  PBAactualYahoo45.89USD closedquoteOct2 20:00:02UTC, not freshlivefill.
- Direct scoped code/security review; no deps/auth/schema/orders/permissions
  changes, actualAIcalls0, noCodeRabbit/newagents/paiddata/publicscan/OCI-KMSclaims.
  Prior Canadian d2f3e2331cfa65b66bf7584936572be2d9d6270c pushed;
  CI37085463606SUCCESS. Current infrastructure commit pending at this append.
- NEXT immediately continue nuclear CCJ/DNN/NXE/UEC/EU/URG/LEU/LTBR/UUUU, then
  remainingwholeproducers/refiners/marine/trusts/fuels. Current parser reader
  /tmp/milkyway-energy-equipment-review/nuclear-read.py running in isolated512MiB
  singlecontainer, evidence /tmp/milkyway-energy-research/nuclear-read.json.
  Actual annual originals alreadylocal. CCJ/DNN/NXE actualAIF/FS/MDA from existing
  canada-attachment-manifest, UECFY2026Jul31. No fakeDEI/quarterfor6Kcovers.
  CCJ CigarLake54.547%2025→57.418%actualJul2closed (Orano42.582%); Q2releaseJul31
  +actualSECQ2FS subsequent note20 verified. DNN direct90%+JCUindirect5%=effective95%,
  July28fullconstructionactual, mid2028productiontarget; WoodCM/SaskPoweractual,
  UEXnonconsentinteresttransferNOTcomplete. NXE CNSCMar5constructionlicense NOT
  operatinglicense, officialAug25page documentsAug13groundbreaking. Historic2021
  Stantec/Wood/SLR feasibility roles NOT currentEPC. UEC actualFluorUR&Cdevelopment
  and Cameco/ConverDyn storage from Sep29annual; convertfacilitynotoperating.
  LTBR actualINL/Battelle irradiationNov2025 and RATENengineering; no commercial
  fuelcustomer guessed. UUUU actualChemoursmonazite and POSCO1.7tonsample notlarge
  commercialrecurringpurchase; Astron9.48%actual2025 vsfuture49%earn-in separate.
  URG/enCore vendors still need freeprimary deeperresearch; no guesses to fill holes.

### Nuclear original-source continuation · 2026-10-03

- Whole Energy stays active and unfinished: 213 entries, 90 edited main companies,
  123 remaining plus all-field depth audit. NEVER final/stop at a partial milestone.
- Added CCJ/DNN/NXE/UEC/EU/URG/LEU/LTBR/UUUU Korean dossiers, 30 role counterparts.
  205 financial receipts/199 populated/1545 values; 24 original files bytes/SHA
  verified. docs/ENERGY_NUCLEAR_REVIEW_20261003.md records original scope and stages.
- Bounded nuclear revenue coordinates: actual issuer/CIK/doc/year/full axes; LEU
  erroneous461.1m tech member is whole business before12.4m elimination, not division.
  UUUU Austria/UAE country-product errors only exact source/year/value/unit corrected;
  raw members preserved. CCJ contract-vs-IFRS revenue not forced to one denominator.
- Current LEU X-energy/Radiant/Antares actual contracts future delivery. UUUU ASM
  Aug28 closed vs VAC pending; POSCO sample capital cost offset not annual sales.
  URG Aug19 first Shirley resin shipment verified, EU anonymous buyers not named.
  Nuclear context entries do NOT make a GICS assignment or complete every field.
- Actual image653tests52.499s OK(18skip); focus73/1.270s; hostNode21/1.989s OK.
  Offline512MiB/1CPU seed722entities1.406s/RSS63.9MiB/quick_checkOK; directoryp95
  1.717ms/LEUmerge6.8ms/detail44.957ms/RSS64.2MiB;81focus0.929sOK. Not network/UI RAM.
- App-only image59e4cae2ae9a5ba30340a505a4d877a8ecfe16758b35253e41f660abf81fd19e
  healthy/startup200(webDB), ready503(existingpaper/backtestpaused); four existing
  services and volumes preserved. Chromeoneexistingtab LEU cards/financials/graph
  ->X-energy detail reverseCentrus confirmed. LEU quote pending, not live-verified.
- Direct scoped code/security review, no new deps/auth/schema/orders/network/model;
  actual AI calls0, no CodeRabbit/new agents/paiddata/publicscan/OCI-KMS claims.
  Infrastructure7b92a5d5c9849ea7c2ed3ae9a1bcdb00d06d0431 pushed, CI37091087956SUCCESS.
- NEXT immediately continue producers APA/CHRD/OVV/MGY/MTDR/PR/SM/CRC/CRGY/GPOR/
  CRK/CNX/BKV/MUR/NOG/VTS. Offline source reader completed16 actual originals at
  /tmp/milkyway-energy-research/producer-read.json; annual+quarter manifests reused.
  Need human table/metric review, current primary updates, named counterpart roles.
  Then whole remaining roster (remaining-nuclear-20261003.json) and depth audit.


### Producer continuation and real exhibit repair · 2026-10-03

- Whole Energy remains active, unfinished: 213 entries /106 edited main /107 left
  plus whole all-field depth audit. NEVER final or stop at this commit/batch.
- APA CHRD OVV MGY MTDR PR SM CRC CRGY GPOR CRK CNX BKV MUR NOG VTS Korean
  business/current contract dossiers;36 role counterparts,76 revenue coordinates.
  Financial205 receipts /199 populated /1550 values.33 annual/quarter/ex21 originals
  bytes+SHA verified. docs/ENERGY_PRODUCERS_REVIEW_20261003.md has exact scopes.
- Actual Murphy Exhibit21 td ordinal parser broke on indentation/colspans;fixed
  physical column ranges, item prefixes/cross references and registrant exclusion.
  Actual original51 names, immediate-parent stakes not fabricated ultimate stakes.
  Scoped legacy generated-row repair, manually reviewed claims preserved. Runtime
  MUR57edges=51subs+6business, enum/registrant0. Pinnacle exact verified LLC aliases
  share one registry ID/2evidence preserving oldbookmarks; GasTreating separate.
- Final actual image667tests40.593sOK18Node skips;host9modules21tests1.660sOK.
  Fourteen edited app/data/test SHA matched. Initial nonexistentmodule names and
  Dockerfile.personal failed; corrected actualtestlist and Dockerfile, not successes.
- Offline512MiB/1CPU seed809entities1.682s/RSS66.4MiB/quick_checkOK; directoryp95
  .912ms/BKVmerge1.759ms/detail11.766ms/RSS66.7MiB;83focused/.740sOK.
- App imagea3712836e8c99316abb57c3da82c78a0acccef47058cceb341c570a007f64ec0,
  startup200webDB/ready503existingpausedpaperbacktest;all otherdata checks true.
  Four preservedservices, no tradingreactivation/volume deletion. RAMobserved
  app156MiB/backup40.39/marketdata267.1/personaldata240.4, notwholeVM/Chrome RAM.
- Native Chrome user's shippingresearch8766 tab active,8080existingtab retained;
  extension getTabtimeoutreset. Do not overwrite usertab or countUI verification.
  Actual graphchecked; UI followup stillrequired afterremainingdossiers.
- Direct scoped source/security review: no new deps/auth/schema/order/networkpaths;
  AIcalls0, CodeRabbit/newagents/paiddata/publicscan/OCI-KMSclaims0.
- Prior nuclear52eaf317282b97fd73b9c97812311c9af705c2c1 pushed CI37093535121SUCCESS.
  Current producer commit/push pending at contextappend. Continue immediately.
- NEXT INR GFR EGY GPRK GTE KOS TALO WTI DEC REPX HPK SD PED EPSN TXO WBI.
  Actualreadercompleted next-producer-read.json, next-producer-business.json and
  originals at /tmp/milkyway-energy-research. GFRactual40FAIF/FS/MDA newlyreceived
  observedparentlinks /next-producer-attachment-manifest.json (actual8financials,
  financialsourceCAD584395000revenue). /tmp/milkyway-energy-equipment-review/
  next-producer-read.py. No modelcalls needed. ActualMURex21cached/51parsedtoo.
  GFR TrafiguraCanada buysallblends;Enbridgepipeline,NGTLgas,Polariscondensate,
  CNOOCExpansion25%;McKay suspendedMar2023. GPRKVitol2026offtakeextended2028,
  HocolcurrentLlanosJV;ManatiBrazilsoldDecember2025notcurrent. INR table
  customer namesMarathonOil/BPAmerica/BlueRacer butannualparagraphslose tablecells,
  inspectactualHTMLrowfor2025%. Receivable24/53/18notrevenue. EGYsignificant
  customer namesnotyetparsed; needsactualtable, suppliedparagraphsexclude names.
  All107remaining list /tmp/milkyway-energy-remaining-producers-20261003.json.

### Extended producer continuation · 2026-10-03

- Whole US Energy is ACTIVE, unfinished: 213 entries /122 edited main /91 left
  plus ALL-field depth/readability/relationship audit. NEVER final/stop at a batch,
  commit, CI success or deployment. User explicitly requires continued completion.
- INR GFR EGY GPRK GTE KOS TALO WTI DEC REPX HPK SD PED EPSN TXO WBI edited
  Korean business/product/current notes;38 role counterparts,69 revenue rows.
  39 original receipts bytes/SHA matched. Financial205/200 populated/1561 values.
  Exact scopes and failed runs: docs/ENERGY_EXTENDED_REVIEW_20261003.md.
- Fixed GFR extra parent_url schema error; preserved validated parent_annual.
  Pure company_reviewed_excerpts replaces only matching parser excerpts when
  edited products/drivers/revenue brief exist, keeps citations/manual translation,
  other issuers and unreviewed originals. Old translated detail+original preserved.
- Actual HTTP found EGY old contract-only income mixed with derivative-inclusive
  geography; canonical stored rows now use same exact doc/year/issuer metric filter
  as new parsing. Actual final EGY4geographies, REPXnegative -3322000/-3039000.
- Final image1f1cd3858fcbe3b8381df7c0f7a0f64d2bd79be1be0f6883d5c3b3bd4294239e:
  source16SHA match;678tests63.528sOK18Node skip;host9modules24tests1.289sOK;
  focused23/.363sOK. Helper image678/145.810sOK; earlier failed runs preserved.
- Offline512MiB/1CPU final helper benchmark seed849entities4.208s/RSS65.0MiB,
  sqlite quick_checkOK;directoryp95 .750ms/WBImerge1.813ms/detail17.733ms/
  RSS65.5MiB;84focus/.977sOK. First benchmark20.091s also preserved, no causal claim.
- App-only recreate healthy;actual16company HTTP200+GFR→Trafigura reverse supplier
  verified. startup200webDB/ready503existingpausedpaper/backtest, otherchecks true.
  Four services/volumes preserved;no trading reactivation. ActualUI still pending:
  two existing Chrome tabs, extension debugger unattached, native user's shipping
  research active;do not alter/close their tab or claim visual verification.
- Direct source/security review;no deps/auth/permissions/orders/network/schema
  additions;actual paidAI calls0, no CodeRabbit/newagents/paiddata/publicscan claims.
  Producer f2548231a9a4e32836ebebc710ab33795ff4dffd pushed;CI37098982483SUCCESS
  on rerun, earlier SIGKILLrecovery/composewait failure retained. Currentpush pending.
- NEXT DK DKL PBF PARR CVI CLMT GLP CAPL SGU SPH MMLP NGL GEL WKC GPRE REX GEVO.
  Prepared17 actual annual+quarter sources and offline facts/business blocks under
  /tmp/milkyway-energy-research/refining-distribution-read.json and -business.json.
  Noncalendar FY SGU2025-09-30/SPH2025-09-27/NGL2026-03-31/REX2026-01-31.
  Added extra current-year revenue/lease reading aid refining-extra-read.py and
  refining-distribution-extra-facts.json; GPRESalesContract zero ethanol must NOT
  override actual Revenues ethanol;REX -254000 derivative adjustment and BigRiver
  unconsolidated1007906000;DKL lease215888000;GLP derivatives wholesale+lease;
  CAPL rental62546000. Need human exact tag/table processing, no generic negative.
  All91remaining list in prior remaining-producer-sources-20261003.json;8annual
  missing AMEN EROK FTW HMH NUCL UNTC WHK XPRO require actual official originals.
  Immediately continue next17 then whole remainder+depthaudit;no final at commit.

### Downstream continuation · 2026-10-03

- WHOLE US Energy ACTIVE, unfinished: 213 roster /139 edited main /74 left plus
  ALL-field depth/readability/actual relationship/source/current/classification/UI
  audit. NEVER final/stop at commit/test/deploy/CI milestone. Latest user asked
  remaining time; commentary estimated 1–3 more workdays with uncertainty, not a
  cancellation or authorization to stop. Counts are not full-completion counts.
- DK DKL PBF PARR CVI CLMT GLP CAPL SGU SPH MMLP NGL GEL WKC GPRE REX GEVO:
  34 original annual/quarter receipts matched;104 reviewed revenue rows;
  financial205 records/200 populated/1562 values. Exact scopes and failed runs in
  docs/ENERGY_DOWNSTREAM_REVIEW_20261003.md. Preserve old MPC/PSX/DINO refining.
- Fixed noncalendar fiscal dates;GPRE current annual cannot fall back to prior
  partial product;SPH end_market parse;SGU cash24683000;REX derivative -254000;
  DKL/GLP/CAPL partial lease/derivative bases;WKC rounding100000 has no share.
  Named NGL→Hydrosource, GEL→BOE/LLOG, WKC→JetBlue/DHL with actual source dates.
  JetBlue registry maps JBLU/single graph ID;preserve existing public profiles.
- Actual HTTP found revenue data missing from module enrichment. Connected
  PUBLIC notes to REPORTS rows and added empty-cache response regression test.
  Final actual image8412753ceb92a5c6b3a71cf685f6a01d88063e2e5d8f62522d486074c90f3c84:
  691tests125.251sOK18skip;host24/1.312sOK;236 packaged app/test SHA match;
  70focus/.911sOK. Offline512MiB/1CPU seed905/4.864s/RSS67.8MiB/quick_checkOK;
  directoryp95 .997ms/WKCmerge1.832ms/details10.886ms/RSS68.6MiB.
- App-only recreate healthy, actual17+3counterpart+3priorrefiner HTTP200 sums/
  reverse roles/cash/signed/rounded/period basis verified. startup200/ready503
  pausedpaperbacktest, otherdatachecks true. Fourservices/data preserved, noAIcall.
- Current Chrome extension energy tab810509711 remains debugger unattached.
  Native Chrome now shows unrelated university window, do not alter it or claim
  visual verification. No extra tabs/newagents/CodeRabbit/paiddata/publicscan claims.
- Extended commit f2a1fdf029ebe1a1e6e63b8dc54e243ecf67cb52 pushed CI37105317411SUCCESS.
  Downstream current commit/push pending at append. Continue remaining74 immediately.
- NEXT shipping16 DHT FRO GLNG FLNG LPG INSW NAT NVGS STNG TEN TK TNK TORO IMPP
  PXS KNOP. /tmp/milkyway-energy-equipment-review/shipping-read.py offline read
  running; /tmp/milkyway-energy-research/shipping-business.json actual annual/quarter
  blocks available. Only LPG/INSW local10Q, other foreign issuers use actual6K/
  official interim release (not fabricated10Q). Official primary latest web found
  DHT Sep14 Panther3yr/Jun3Hanwha2028newbuild/Aug5Q2;FROAug28Q2/Sep11sale2VLCC;
  GolarAug13Q2new4thFLNGCIMCRaffles2029/SeatriumLOI;FlexAug19Q2actual106.8m and
  March18extensions/March25Aurora. Need receive/read full primary sources and
  exact annual facts/contract dates before editing. Preserve non-Energy official
  classification, business exploration groups are not GICS certification.

### Shipping continuation · 2026-10-03

- WHOLE US Energy ACTIVE, unfinished: 213 roster /155 edited main /58 left plus
  ALL-field depth/readability/actual relationship/source/current/classification/UI
  audit. NEVER final/stop at commit/test/deploy/CI milestone. Latest time question
  answered with uncertain 1–3 more workdays; no cancellation or reason to stop.
- DHT FRO GLNG FLNG LPG INSW NAT NVGS STNG TEN TK TNK TORO IMPP PXS KNOP:
  18 annual/availablequarter receipts matched;69 reviewed revenue rows;95 scoped
  counterpart profiles.5 additional issuerPDForiginals downloaded/SHA recorded.
  Financial205 records/200 populated/1567 values. See ENERGY_SHIPPING_REVIEW_20261003.
- Reviewed issuer/document/FY/USD guards, actual undimensioned metric keys, lease/
  pool/TCE/equitymethod distinctions, nestedsubtotal exclusion, TENbothmetrics+total
  reconciliation. IMPPpartial154775747 vs161004306 no fabricated6228559component.
  BWLP/RBNE officialtickers map to one relationship ID, not new213roster entries.
- Actual ToroSep17/18MRdeliveries reflected:4MR+2LPG; AI OKTO Oct8 distribution
  conditional/future Oct3. Updated Sept21record and Sept9proposal originals. Dorian
  Aug5actual25fleet. HilliCameroonended/Gimiactual/Argentinafuture separated.
- Final image27a0a9157119af9237985426c480c31ae1b6afb12b0ab09cff874314465b0cd3:
  actual703tests79.358sOK18skip;host9modules21tests1.416sOK covers all18Node skips;
  236 packagedsourceSHA match;40focus1.844s/82focus2.278sOK;69rowsactualparsematch.
  Offline512MiB/1CPU seed1001/4.816s/RSS67.0MiB/quick_checkOK; directoryp95.745ms,
  KNOPmerge1.445ms/details10.582ms/maxRSS67.7MiB. Existingdependencyimage reused;
  offlineaptbuild/discoveryoption/PYTHONPATH/testassumption failures preserved.
- App-only recreatehealthy,16+4counterpart+6priorcompanyactualHTTP200;periods/sums/
  reverse relations verified. BWLP/RBNE sectorrosterURL404 is expected; actual
  entityID URL200. HTTPhelper statusvar corrected, not appauth/API boundary change.
  startup200/ready503existingpausedpaperbacktest; otherdata checks true.
  Fourservices/data preserved, app151.1MiB/backup44.3/market268.3/personal240.6.
- Existing Chrome energy810509711 debuggerunattached; actualvisualaudit pending.
  No extra tabs/userunrelatedwindowchanges/paidAI/CodeRabbit/newagents/paiddata.
  Scoped directcode/securityreview only; no publicscan/OCI-KMS/dependencyreaudit claims.
- Downstream87a350c7bc1ba4f63366f0ae08c55495d91cbf9a pushed;CI37110770464SUCCESS.
  Current shippingcommit/push pending at append. CONTINUE remaining58 immediately.
- NEXT land/royalty15 BSM CRT DMLP KRP NRP NRT PBT SBR TPL VNOM CKX MNR MXC LB PNRG.
  Actualoriginals at /tmp/milkyway-energy-research; land-royalty-business.json ready.
  AMEN noannual yet, do not fabricate. BSMcurrent2025Aethon14% vsXOM13%2024;KRP
  top10operatornamed47.1%;CRTXTOoperator/royaltynotphysicalsales;NRTFYOct31/EUR-USD;
  PBTBlackbearddeficitWaddellnotalltrust0;NRPSisecam49%equitymethod;LBWaterBridge
  operating/producerSUAs;TPLimagecustomerpie needs actualsource notdirector links.
  Then remaining43 and entiredepthaudit.8missingannual AMEN EROK FTW HMH NUCL
  UNTC WHK XPRO require actualIR/newlistinghistory. No final at intermediate batch.

### Explicit pause and cross-computer handoff · 2026-10-03

- USER explicitly paused feature development and requested a portable handoff.
  This overrides older ACTIVE/no-intermediate-stop notes. Do not continue feature
  work or invoke providers until the user resumes. Only handoff preservation is
  authorized in this final part of the session.
- Read HANDOFF.md and docs/HANDOFF_OTHER_COMPUTER.md first on the next computer.
  Latest validated/pushed/deployed shipping SHA is
  dd0b8eae3a06bd5d5b183a1d18f376724bb6a18a; actual CI37117351110 completed SUCCESS.
  Image27a0a9157119af9237985426c480c31ae1b6afb12b0ab09cff874314465b0cd3 unchanged.
- Current WIP: new company_energy_land.py, _land_revenue.py, _land_tables.py;
  modified company_energy_revenue.py and company_energy_reports.json.
  30 actual annual/quarter receipts for15 added. Profiles/roles/manual tables are
  DRAFT, not catalog/group connected, no current land tests or deployment.
  Initial actual parse11 produced54 rows before the last added BSM/KRP derivative
  and PNRG other/disposal statement projections. Reparse before archiving results.
- Current progress remains155 edited main /213;58 plus whole-depth review left.
  Current15 must NOT be reported completed170. Other43/missing8 and exact pending
  integration/verification/source points are listed in the new handoff.
- Original58-company evidence, land intermediate readings/helpers and selected
  logs are preserved in a separate public-source ZIP at
  runtime/handoff/milkyway-energy-handoff-20261003.zip (not Git tracked).
  No .env/keys/cookies/privateDB/runtimevolumes in it. Clone supplies code/docs;
  ZIP supplies /tmp originals. User personal DB/backups need separate migration.
- User memory constraint preserved: no Chrome or Docker mutation, no paidAI,
  no CodeRabbit, no new agents, no feature tests/deployment resumed for handoff.
  This checkpoint is a saved unfinished state, not a completed milestone.

### Cross-computer folder selection · 2026-10-03

- User asked which workspace folders to transfer. Feature work remains paused.
- Main handoff/code checkpoint19826f82b4ca13dd7bd7239dab9e15ab8ae9e3e1 is pushed;
  actual GitHub ref matched. Working tree was clean after that checkpoint.
- Added the actual folder map to docs/HANDOFF_OTHER_COMPUTER.md: Milkyway is the
  current app; output and week10_Milkyway_검수 preserve previous artifacts; sibling
  korea-shipping-research is a separate research project; report_builder.py makes
  the separate PDF. Virtual environments/caches/previews can be recreated.
- Whole-folder copies must retain .git/.env/runtime handoff evidence as needed;
  Git clones omit private .env and the public-source ZIP. Docker named volume
  personal-runtime holds current personal data and is not a host runtime folder.
  Existing conversations/strategies/paper records need a separate app backup.
- Guidance only: no new personal DB export/restore, no Docker/app mutation, no
  provider calls, no feature tests or development resumed. The public evidence
  ZIP remains the original verified archive; the latest handoff prose is in Git.


### Context saved · 2026-10-03 · personal backup complete, development paused

- Latest user instruction is “맥락저장”. Feature development/research remains
  explicitly paused. Continue only when the user resumes. This supersedes older
  ACTIVE/no-intermediate-stop notes. No paid AI/provider call was made for handoff,
  backup or context save. CodeRabbit remains globally forbidden; no new agents.
- Last VERIFIED pushed branch head: codex/ai-research-workflow,
  8b16fbd857dad15ca039312efb0092b161154f83 (folder transfer documentation).
  Unfinished land checkpoint19826f82b4ca13dd7bd7239dab9e15ab8ae9e3e1 is also pushed.
  Last validated/deployed shipping remains dd0b8eae3a06bd5d5b183a1d18f376724bb6a18a,
  image27a0a9157119af9237985426c480c31ae1b6afb12b0ab09cff874314465b0cd3.
  Do not deploy the unchecked land checkpoint or count it as completed.
- US Energy remains155 edited main issuers /213, not155 fully completed companies.
  Remaining58 and the entire depth/currentness/classification/UI audit are pending.
  Land15 BSM CRT DMLP KRP NRP NRT PBT SBR TPL VNOM CKX MNR MXC LB PNRG have
  unfinished profiles/revenue adapters/manual tables and30 original receipts.
  Catalog/groups/latest revenue_mix integration and current land tests are pending.
  The older11-issuer54-row parse is stale. Read HANDOFF_OTHER_COMPUTER.md for
  the exact pending files, original-source cautions, remaining43 and missing8.
- Public research bundle remains runtime/handoff/milkyway-energy-handoff-20261003.zip:
  36,432,881 bytes,248 payload files; CRC/all memberSHA/path checks passed.
  SHA256 c128c9da6d699a0ee18500cb9d25815cebafe23ac56603ca14d7aa3331d9d833.
  This bundle contains no private DB/keys/.env and is not Git tracked.
- USER subsequently authorized exporting the Docker personal DB into the project.
  ACTUAL PRIVATE BACKUP is now backups/milkyway-20261003T121021Z-b65f42b0.zip,
  created2026-10-03 21:10:30 KST;131,036,961 bytes;3,972 payload files;
  uncompressed495,661,515 bytes. SHA256:
  8a27d491bc4dfa6de8ca2634ba4d6e66e43f0b49be64eb4ff7c325c19d76d39c.
  Docker source/host SHA matched; ALL archive CRC/memberSHA checks passed;
  personal club.sqlite3 and company-details/graph.sqlite3 both passed SQLite
  integrity and foreign_key checks. This is an actual snapshot/export, NOT a
  performed live restore. No financial data/secret values were printed.
- Private backup companion files: same-stem .zip.sha256 and .summary.json,
  plus backups/READ_ME_FIRST.md. Directory0700/files0600. Backups are Git ignored
  and MUST NOT be committed/pushed/shared. The ZIP itself is not encrypted and
  contains encrypted credential rows plus LOCAL DECRYPTION ROOTS. Host .env is
  separate: preserve/copy it privately. Do not put keys into any context document.
- Latest actual Docker status at the end of backup: app healthy; app, personal-data,
  market-data, backup running; paper-worker Exited143; backtest-worker/company-data/
  market-details Created. Same containers/volumes preserved; no restart, removal,
  live restore, new helper container, browser tab, feature test or deployment.
  Existing backup source SHA matched app+host50f18ed867707dad820cea331ccff8667be931a02220c5aa882ed96f3f3e9b6c.
- Default Docker socket /Users/kimseungjoo/.docker/run/docker.sock accepted connections
  but _ping/API timed out. Desktop UI displayed Engine running. Working local
  endpoint was unix:///Users/kimseungjoo/Library/Containers/com.docker.docker/Data/docker.raw.sock.
  Used docker -H with that endpoint for read-only status, backup exec and archive
  copy; no persistent Docker context/settings change. Do not infer Docker/Chrome
  are generally uncontrollable. Probe the current PC before reusing a path.
- macOS iCloud placeholders remain a real blocker for normal Git operations:
  .git/HEAD, refs/heads/codex/ai-research-workflow and HANDOFF.md were
  compressed,dataless. Finder showed roughly47,000 download requests queued.
  Reads/Git check-ignore/public handoff edit hung. brctl download/Finder Download
  Now did not clear these particular placeholders. The pending root-handfile edit
  cell and our read-only/writer attempts were terminated; no Git metadata was
  rewritten and no user/editor/Docker processes were killed. Root HANDOFF.md was
  still899 bytes at the latest observation. Do not assume that private-backup
  completion was already pushed to GitHub. Its previous authoritative completion
  record is backups/READ_ME_FIRST.md; this new entry supersedes earlier “not exported”.
- Transfer: current Milkyway folder is the app. Include .git/.env as appropriate,
  runtime/handoff PUBLIC evidence and backups PRIVATE evidence. output and
  week10_Milkyway_검수 preserve optional older artifacts; korea-shipping-research
  is an independent8766 research app. Do not overwrite/use its repository or
  user terminal/editor processes. Virtualenvs/caches can be recreated on the new PC.
- NEXT on explicit resume: read this last entry, HANDOFF_OTHER_COMPUTER.md and the
  private backup guide. Bring the latest LOCAL docs too if Git metadata is still
  blocked; a clone alone omits both ignored bundles and possibly these new notes.
  Validate the selected archive on the NEW PC and preserve existing data before
  restoration. Stop all writers for restoration and afterwards start ONLY app,
  personal-data, market-data, backup until the user resumes paper/backtest.
  deploy/local_tools.py restore currently ends with unrestricted compose up -d;
  do not silently enable all workers when maintaining the user's paused state.
  Never restore this migration archive over the original PC merely to test it.
  Resolve iCloud/Git availability and commit/push only public docs; private ZIPs
  and .env stay excluded. Resume land15 integration/verification and remaining
  Energy work only when requested. Read SECURITY_REMEDIATION_STATUS.md fully
  before security/deployment/backup work; personal local authorization remains
  distinct from the public deployment NO-GO and managed remediation gates.
- Context-save verification: latest entry was written, fsynced and reread.
  A bounded normal git status attempt then timed out after5seconds. This context
  update is saved LOCALLY; its commit/push is still pending on iCloud Git metadata.
  No Git metadata rewrite, force push, DB restoration or feature resume was done.

### New PC preparation and explicit restart pause · 2026-10-03 23:26 KST

- Current project is /Users/kimseungzoo/Developer/4.Milkyway. The user's latest
  instruction explicitly pauses work to restart the computer and requests a
  handoff and resume prompt. Do not resume restoration, app startup or feature
  development until the user resumes. The continuous milestone preference applies
  after resumption; this explicit pause takes precedence now.
- Read docs/RESTART_HANDOFF_20261003.md and docs/RESUME_PROMPT.md first on restart,
  then the original handoff/context and AGENTS. Those files list the exact state,
  archive digests, commands, constraints and next development tasks.
- Initial new-PC directory had .env/backups/docs/runtime but no app code or .git.
  Cloned the actual branch codex/ai-research-workflow and merged missing files
  without overwriting copied local files. Remote HEAD was verified as
  8b16fbd857dad15ca039312efb0092b161154f83. Existing local backup/context entry
  above was preserved. GitHub access works; old-PC iCloud problems do not apply
  to this current checkout as an observed blocker.
- BOTH private backup and public evidence ZIP passed current-PC whole-archive
  SHA checks. .env/backups/runtime remain Git ignored and untracked.
  No secret values or private DB contents were printed.
- Docker Desktop was started and engine29.7.2 responded. Built ONLY validated
  shipping source dd0b8eae3a06bd5d5b183a1d18f376724bb6a18a as
  milkyway-personal:local, imageID
  sha256:fd9bdb59eeada9f5297ea72086a848b3e8a5b67d06bddd7c273100fdb49d889f.
  No app deployment or source completeness is implied by this successful build.
- deploy/local_tools.py now supports --start-services after restore and stops
  all8 Compose writers including company-data/market-details. Tests were run
  BEFORE the pause: tests.test_local_tools + tests.test_local_ops,13 passed/.196s.
  Scoped direct review and diff check passed. Compose config--quiet passed.
  No whole test/security scan/performance run/current CI success is claimed.
- Crucial pending state: NO live Docker archive restore, NO app/service startup,
  NO personal Milkyway volume created. At23:26 there were no running
  milkyway-personal containers or volumes of that prefix. Other Docker projects
  and existing volumes were preserved. No paidAI, CodeRabbit or newagents used.
- NEXT on explicit resume: recheck Git/Docker/image/archive/current volumes;
  preserve any existing target data; restore the 21:10KST private snapshot with
  --start-services app personal-data market-data backup; verify DBs and prior
  records/local HTTP; leave paper/backtest stopped. Then resume land15 and
  remaining Energy review from the detailed handoff. Do not deploy unchecked
  land source or report the155 edited profiles/213 roster as fully completed.
- This restart save is a preservation checkpoint, not a completed Energy
  milestone. Save/push public instructions and the tested host recovery change;
  private files remain local. Verify actual remote HEAD after push; CI may still
  be pending when the computer is shut down.
