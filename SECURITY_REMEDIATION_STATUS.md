# Security remediation checkpoint

Saved: 2026-09-01 (Asia/Seoul)

## 2026-09-01 continuation update

- The complete remediation working tree was preserved in checkpoint commit
  `51e48e2` (`security: checkpoint remediation and broker boundary`). The tracked
  working tree was clean immediately afterward and `main` was one commit ahead of
  `origin/main`. This checkpoint is not a deployment approval and the test suite
  was not rerun after creating the commit.
- The host `runtime/` directory remains gitignored and preserves the two owner-only
  64-byte development credential roots. They were not included in the commit.
- The prior `milkyway-local-runtime` volume, `quant-club-local` container, and
  `milkyway:local` image were not present in either available Docker context. A
  **new empty development volume** named `milkyway-local-runtime` was created; do
  not describe it as a recovery of the former volume.
- `milkyway:local` was rebuilt successfully. A local-only container named
  `quant-club-local` is currently bound to `127.0.0.1:8080` with automatic restart
  disabled. It uses a temporary 19-symbol smoke dataset copied under
  `/tmp/milkyway-smoke.*`; `/` and `/health/live` returned HTTP 200. Readiness
  remains HTTP 503 because `data_gate=false` and `worker=false`, so this proves
  only local UI/startup behavior, not production readiness. The full 1.1 GiB
  dataset remains under the separate `us_trading_bot/data_cache` tree and direct
  Docker bind mounting failed while macOS/iCloud files were not fully materialized.
- Local Codex CLI is `0.151.0` and the ChatGPT desktop bundle is
  `26.825.51511`. No `/etc/codex/requirements.toml` or
  `/etc/codex/managed_config.toml` exists, and the current session still has
  `permission_profile type="disabled"`. The user must create the system-managed
  requirements file themselves (the agent must not self-elevate), allowing
  `:read-only` and `:workspace` with `default_permissions = ":workspace"`, then
  restart the Codex client, open a new session, and verify `/status` before the
  Deep Security Scan.
- No Deep Security Scan exists and there is still no scan ID. The next scan must
  be a new whole-repository scan. Public deployment and real member credential
  entry remain **NO-GO**.

## Latest handoff marker

- Context was explicitly saved before moving work to a new Mac.
- No Deep Security Scan exists to resume: both attempts failed before scan
  creation because the effective permission profile was `disabled`; there is no
  scan ID or partial result.
- Open the preserved repository in a new Codex session whose effective profile is
  managed `:workspace`, then use the continuation prompt below to start a new
  whole-repository Deep Security Scan.
- The present working tree is intentionally uncommitted. Preserve every existing
  change, `runtime/` data, and the `milkyway-local-runtime` Docker volume.
- Public deployment and real member credential entry remain **NO-GO**.

## Repository state

- Base commit: `5632baf`
- Security remediation is present in the working tree and is not committed yet.
- Preserve the working tree, `milkyway-local-runtime` Docker volume, and `runtime/` files.
- Local server container name: `quant-club-local`.

## Completed verification

- The current 88-test unit/regression suite passed inside the final rebuilt
  `milkyway:local` image.
- The OCI KMS tests use the real OCI SDK models and fake KMS transport.
- The expanded tests cover v3 owner/provider associated-data rejection, no local
  fallback during KMS failure, production legacy rejection, offline migration
  rollback/success/idempotency, corrupted v3 rejection, shared prefixless legacy
  root compatibility, broker role separation, no raw decrypt/proxy route,
  app/paper no-local-decrypt behavior, AI generation, market retain/rebind, and
  Compose broker/KMS/backup scopes.
- A real disposable Docker PostgreSQL 16 database was seeded, dumped in custom
  format, checksum/list verified, deliberately dropped, restored, and content
  verified. This exposed and fixed the non-executable restore entrypoint and the
  incorrect `POSTGRES_DB`/`PGDATABASE` variable. The exact test dump, containers,
  network, and volume were removed after verification.
- Disposable end-to-end flow passed: registration, authentication, CSRF logout,
  copied-cookie rejection, security headers, and oversized-body rejection.
- Python dependency audit reported no known vulnerabilities after upgrading
  `cryptography` to the fixed 50.x line and adding OCI SDK 2.185.x.
- Production example secrets fail startup validation.
- Compose rendering confirmed service-specific secret allowlists and read-only
  dataset mounts for app/paper/backtest; only scheduler has dataset write access.
- All 5,298 manifest-approved price files are SHA-256 checked before readiness.
- Latest local app used about 136 MiB and returned HTTP 200 from health endpoints.

## Security changes in the working tree

- Reject shipped/default/reused production secrets and example hosts.
- Development keeps separate owner-only local v2 roots. Production now rejects
  local roots and uses separate OCI Vault AI/market keys with v3 AES-GCM
  associated data bound to purpose, member, provider, environment, and field.
- Legacy/v2 production records fail startup until the stopped-service,
  interactive migration re-encrypts and verifies every field through OCI KMS in
  one rollback-safe transaction. Current v3 records are also KMS-validated.
- Migration refuses legacy/v2 records without an explicit verified-backup
  attestation. The one-shot backup creates an owner-only custom-format dump,
  verifies its SHA-256 and structure, and keeps pre-KMS rollback dumps out of the
  routine 14-day deletion rule.
- Persistent hashed browser-session records make logout revocable.
- Owner-only SQLite/runtime permissions.
- Pre-parser fixed-length and streamed HTTP body limits.
- Async, disconnect-aware, per-user/global-limited SSE.
- Service-specific Compose environments and network separation.
- Finnhub token moved to a header and exception logs sanitized.
- Lightweight web dataset views remove the former full OHLCV memory load.
- Strict strategy DSL rejects unknown fields; AI output is never executed.
- Production app and paper processes now use a separately deployed
  provider-operation broker. Only the broker VM receives OCI KMS, deployment KIS,
  or local-AI secrets. App/paper receive different bearer tokens and can invoke
  only fixed encrypt/validate/generate/quote operations; no raw decrypt or generic
  provider proxy is exposed. Broker requests are bounded and rate/concurrency
  limited.
- The broker has its own Compose, HTTPS Caddy edge, systemd unit, env template,
  read-only runtime, and explicit two-VM deployment/IAM procedure.

## Remaining deployment blockers

Do not enter real member API keys or publicly deploy yet. All remaining blockers
require authority or infrastructure that is not available in this session:

1. Provision two OCI instances. The public app VM must be excluded from every
   credential-key dynamic group; only the broker VM may receive the four exact
   KEY_ENCRYPT/KEY_DECRYPT permissions. Provision the real Vault, two keys, broker
   DNS/TLS, source-restricted NSG, Audit retention/alarms, and provider usage alarms.
2. Put real endpoint/key OCIDs only in `deploy/credential-broker.env` on the broker
   VM, deploy both Compose stacks, and prove the broker startup two-key KMS round
   trip plus app/paper role preflights. No OCI account, CLI, instance principal, or
   production credentials are available locally, so this cannot be simulated as
   a successful real KMS operation.
3. Run the whole-repository Deep Security Scan in a new managed `:workspace`
   permission session. The current session still reports
   `permission_profile type="disabled"`.

The former High raw bulk-decryption path is structurally removed for an app or
paper process compromise in the documented two-VM topology: those processes have
only ciphertext and a fixed-operation broker token, not a KMS identity, endpoint,
key OCID, raw decrypt route, provider token, or arbitrary proxy. Independent review
found implementation/deployment regressions in the first patch (broker read-only
startup import, paper egress, stale deployment/migration instructions); all were
corrected and sent through a second independent audit.

Residual risk remains: a compromised public app can capture credentials newly
submitted while it is compromised and can misuse rate-limited allowed operations
for multiple members. A paper token can request normalized quotes for stored
connections. Neither role can retrieve stored plaintext through the implemented
API. Eliminating new-input capture and tenant-global operation authority requires
a separately trusted browser-facing auth/origin or per-user execution identity;
this is a different integrity architecture, not a missing local code fix.

The required Deep Security Scan did not start. Exact tool error:

> Deep Scan cannot safely start a read-only worker: the parent must provide a managed filesystem permission profile.

The current continuation session also reports `permission_profile type="disabled"`.
The scan was actually retried on 2026-08-30 and failed with the same error before
creating a scan, so there is no scan ID or partial scan to resume. On a new session
with a managed filesystem permission profile, start a new Deep Scan over the whole
repository and remediate any validated high/medium findings before deployment.

## Latest independent verification

Three fresh read-only reviewers completed after the broker correction loop:

- `HIGH-CRED-BULK-DECRYPT`: **fixed**. Production app/paper cannot locally decrypt,
  receive a KMS identity or key metadata, call a raw-decrypt route, or use a generic
  provider proxy. The broker exposes only fixed normalized operations.
- No additional locally actionable High/Medium was found in the credential boundary.
- The role-global operation authority and capture of credentials newly submitted to
  an already-compromised public app are architectural residual risks. Removing them
  requires an independently trusted browser-facing identity/capability issuer or
  per-user/job-isolated execution, with corresponding DNS/TLS/NSG/auth changes.
- A separate environment audit confirmed that real OCI creation, two-key KMS round
  trips, app-VM denial, and Audit evidence require external OCI authority. The Deep
  Scan tool is present, but its managed permission profile is not active in this
  session.

## New-session continuation prompt

Open this repository in a new Codex session and paste:

```text
현재 effective permission_profile이 managed :workspace이고 disabled가 아닌지 먼저 확인해.
루트 AGENTS.md와 SECURITY_REMEDIATION_STATUS.md를 끝까지 읽고 기존 작업 트리를 보존해.
남은 보안 작업을 계속 진행해: 새 whole-repository Deep Security Scan을 시작하고,
발견된 high/medium은 focused regression test -> 최소 완전 수정 -> 전체 테스트 ->
fresh independent read-only agent 검증 순서로 통과할 때까지 반복해.
실제 OCI 권한/인프라 없이는 수행할 수 없는 항목만 마지막에 정확한 증거와 함께 보고해.
실제 OCI KMS/Audit 성공을 시뮬레이션 결과로 대체하거나 공개 배포 GO를 선언하지 마.
```

## Resume checklist

1. Review `git diff` and keep the uncommitted remediation intact.
2. Provision the documented two-VM broker boundary, Vault keys, exact broker-only
   dynamic group/IAM, TLS/NSG, Audit and provider usage alarms.
3. Require broker startup KMS round trip and app preflight
   `credential_broker=true`; verify the app VM receives AccessDenied for both keys.
4. Run the blocked whole-repository Deep Security Scan in managed `:workspace`.
5. Re-run the checked-in commands after inserting deployment-specific values and
   record the results. Only then accept real member API keys.

For the scan session, select a managed `:workspace` permission profile before
starting Codex; the current `permission_profile type="disabled"` cannot be changed
in place. Public deployment remains **NO-GO** until both the real OCI gates and a
sealed scan with no unresolved high/medium findings are recorded as passing.
