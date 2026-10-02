# Company price milestone — 2026-10-02

## Implemented

- Registered listed-company detail pages display the current price, currency,
  actual provider timestamp, source, and a factual comparison with the previous
  close when a compatible baseline exists. Numbers use thousands separators.
- Toss initial REST prices and acknowledged, trade-only WebSocket subscriptions
  are supported. Fixed hosts, at most 12 ephemeral watches, bounded responses,
  credential rotation identity, reconnect backoff and stale-price checks apply.
- The market worker collects free Yahoo fallback prices once per minute. The
  visible company page reads the cache every two seconds and renews its watch
  every 30 seconds; watches expire after 90 seconds. Hidden pages and navigation
  or owner changes stop requests and reject late responses.
- Provider/source failures retain an explicitly stale reference price. No
  synthetic value, order, execution-ledger quote, or AI request is introduced.
  Unsupported or unlisted entities have an explicit status.
- Unchanged, uncurated public company profiles are skipped by exact content and
  sector digest during startup. Reviewed profiles still receive current reading
  notes. Equal timestamps cannot hide changed content or sector classifications.
  Legacy unsupported claims and forbidden encyclopedia sources remain removed.

## Verification

- Final image `milkyway-company-prices-final:verify`: full offline Python suite
  **498 tests passed**, 14 Node-related skips, **267.117 seconds**. The runner
  used an isolated in-memory database, read-only source bind and disposable
  writable runtime. No provider network was enabled.
- Focused graph/migration regression: **25 tests passed**, **2.358 seconds**.
- Explicit host Node/frontend suite: **16 tests passed**, **17.295 seconds**;
  its checks include price formatting, escaping, hidden-page and
  owner/navigation guards, charts, and existing research flows.
- Existing user runtime was recreated with the final image. All eight services
  were running and the app health check was healthy. Runtime and backup volumes,
  credentials, research and paper records were preserved.
- `/health/startup` and `/health/ready` both returned HTTP 200. Readiness reported
  database and the three paper/backtest/personal workers available, but dataset
  and data gate were false. This does not establish a usable real execution feed.
- Authenticated local HTTP checks returned actual public AAPL, AMD and Samsung
  prices. AAPL/AMD were marked closed-session references; Samsung was marked
  delayed reference. Thirty cached HTTP reads: median **17.39 ms**, p95
  **35.31 ms**. Evidence: `/tmp/milkyway-price-real-check.json`.
- An intermediate native process/SQLite/backup check passed all eight checks.
  Evidence was copied to `/tmp/milkyway-price-native-evidence-20261002` before
  removing the completed disposable container. This preceded the final startup
  optimization and is not a claim that the final packaged check passed.
- Two intermediate packaged Docker runs stopped after four checks at the global
  deadline. Their reports are retained in `/tmp/milkyway-price-packaged-checks`
  and `/tmp/milkyway-price-final-packaged`. Parallel verification and repeated
  startup contributed to resource pressure; no final packaged pass is claimed.
- Final direct Toss quote request returned `TossIpNotAllowedError`. The existing
  connection is configured, but real WebSocket delivery is **not verified**.
  The current outbound server IP must be permitted in Toss WTS.
- Chrome's extension connection was unavailable and native control was
  interrupted by the user working in another tab. No new browser window was
  opened. Updated price UI screenshot verification remains outstanding.

## Direct code and security review

- Reviewed route authentication/CSRF, exact registered ticker admission, watch
  quota serialization, private broker-cache identity, bounded provider processes,
  strict finite/time/currency validation, same-day baseline selection and stale
  handling. Reviewed HTML escaping and source-link handling, request cancellation
  guards, SQLite migration and bootstrap behavior.
- Changed Python files parse successfully; `git diff --check` passed. `.env`
  remains ignored. No dependency or credential was added to the browser or Git.
- No CodeRabbit, actual AI call, harness, order, public deployment or user-volume
  removal. This is a scoped local source review, not a fresh whole-repository
  managed security scan or an OCI/KMS readiness claim.

## Resource handling and remaining work

- The two unit runners exited and removed themselves. The retained stopped
  native-check container was removed after copying its evidence. Only the
  existing Milkyway Compose group remains running. Unrelated stopped containers
  and all personal volumes were preserved.
- User reported high memory pressure. Further checks run one at a time, and a
  single existing development tab is reused. Docker measurements at review:
  eight app services used about 1 GiB combined; Chrome's whole process tree used
  about 3.3 GiB, which includes the user's document/Drive tabs.
- Detailed US IT research, Korean industry coverage, current permitted broker
  reception and the newly requested five real AI tests are separate outstanding
  requirements. The five AI calls still await explicit approval.
