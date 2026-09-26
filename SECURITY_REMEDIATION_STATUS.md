# Security remediation checkpoint

Saved: 2026-09-05 (Asia/Seoul)

## Resumed managed-session progress (2026-09-05, work in progress)

This section supersedes the earlier environment/tooling and source-state descriptions
below. Historical occurrence lists remain an audit trail, not a current closure claim.
No real OCI gate is superseded.

- Managed `:workspace` and automatic escalation review work. Docker builds, official
  dependency metadata and isolated PostgreSQL checks are available; no session restart
  is needed. The pre-existing dirty baseline remains at
  `/var/folders/bk/f34r9qkn13d_w47jxgcx62nh0000gn/T/milkyway-remediation-weq7mxby`.
  User `runtime/` and pre-existing Docker volumes have not been modified.
- Shared AI and personal brokerage modes are now independently wired. Production
  uses independent broker session/permit/work issuance, direct browser credential
  entry on the broker origin, private encrypted credential rows, and transaction-local
  PostgreSQL RLS contexts. Workers request trusted member batches/jobs instead of
  caller-selected owners, ciphertext or symbols. These six occurrence candidates
  are under fresh independent read-only review; they are not yet declared closed.
- SQL migration clears historical table, column and future-object grants. Admission
  triggers preserve per-member/global limits despite RLS. Metadata queries exclude
  ciphertext. Missing RLS/authority functions or excessive runtime roles fail startup.
- PostgreSQL uses private-interface TLS 1.3 and clients verify the CA and server name.
  Added an offline TLS generator that refuses overwrite; the CA private key stays
  outside both runtime VMs. A disposable test used this generator and the actual
  role-init script, including its existing-database repeat path.
- Latest complete unit/regression suite: **192/192 passed** in the pinned verification
  image, network disabled, current source read-only and temporary runtime. Executable
  temporary storage is enabled only for harmless shell-stub tests.
- Latest PostgreSQL integration: **8/8 passed**, including fresh/upgrade grants, RLS,
  pool context, TLS positive/negative checks, actual PG16 encrypted dump/restore and
  tamper rejection, and real ASGI HTTP routes with separate app/authority/worker DB
  connections. HTTP controls cover two-member registration, key management, cross-member
  denial, exact multiaccount work scope, replay denial, shared AI permit issuance,
  logout and 24 concurrent session issuances retaining the ten-session cap. Dataset,
  provider I/O and credentials were synthetic; these are not provider/OCI success.
- All three Compose configurations (including optional local AI and restore) passed
  `config --quiet` with synthetic values, and rendered service environment checks
  confirmed role/token separation. No real env file was read or printed.
- Runtime/audit/lock-tool dependencies have full Linux/Python3.11 wheel hash locks;
  container images use official digests and OS packages signed immutable snapshots.
  Clean build, pip-audit JSON (no known Python advisories) and CycloneDX were recorded.
  Verification image `milkyway:remediation-20260905` uses manifest index
  `sha256:2dd04e90636c585ec459f6342a795e65c143eabdfe1d972cdfdc115897bb499a`;
  current tests bind newer source, so this is not the final release image.
- Independent final host/provider-process review found no remaining High/Medium
  defect in its bounded candidates. Host checks precede APT mutation and propagate
  failure. Provider slow-body/deadline, error mapping, child reaping/replacement and
  OAuth reuse controls passed. Raw remote provider secrets are rejected before file
  reads; broker-only Vault CURRENT retrieval is process bounded. Real Vault/IAM/Audit
  evidence remains absent.
- Malformed own strategy JSON and oversized member quote batches now quarantine the
  affected account while preserving durable member rotation in configuration_required status. Dataset certification
  failures remain fail closed. Focused regressions are included in the 192 tests.
- Deployment documentation and examples describe the accepted shared-AI/personal-
  brokerage topology, DB-first startup, broker-origin login, KMS, TLS and existing-volume
  migration. Final candidate image `milkyway:remediation-final-20260905` was built,
  manifest index `sha256:fe571c1ad2c84810dbea837615d15ad21bfdbd58544e1cbf1df77ae422be0c68`.
- Fresh final independent authority/ledger review gave bounded approval with no
  remaining concrete High/Medium issue in its scope. It independently passed 8/8
  PostgreSQL and 26/26 owning tests. Verified closures include long backtests, the
  actual threaded-fetch/main-thread-ledger worker, per-account fill-key prefixes,
  frozen-account recovery, multi-hop corporate actions, same-tick holdings/equity,
  freeze-before-stop behavior and provider-specific browser environment choices.
  Test sessions now explicitly match production autoflush=False. The six DB/broker
  source paths are independently reviewed closed, pending the new whole scan.
- The new whole-repository Deep Security Scan has **not started yet**. Source is now
  frozen for final packaged-image checks and the required fresh managed-session scan.
  No real OCI release, KMS/IAM/Audit, member provider authentication, deployed capacity,
  or deployment gate is claimed.

Current complete test logs: `/private/tmp/milkyway-locked-tests.log` and
`/private/tmp/milkyway-postgres-checks.log`. Canonical fix evidence is also recorded in
the prior scan's `artifacts/fix_report.md`. Public deployment and real credentials
remain **NO-GO**.

## Current decision

Public deployment and real member/provider credential entry remain **NO-GO**.

- The effective session permission profile was confirmed before this work as
  `permission_profile type="managed"`, profile `:workspace`. It is **not**
  `permission_profile type="disabled"`.
- Root `AGENTS.md` and this status file were read completely before the new scan
  or file changes.
- The pre-existing uncommitted working tree, gitignored `runtime/` data, and user
  Docker volumes were preserved. No reset, checkout, data deletion, volume
  deletion, deployment, or real credential entry was performed.
- The latest sealed whole-repository scan has no High findings. Of its 39 Medium
  occurrences, independent source review currently classifies 30 as having their
  traced source path closed and 9 as still vulnerable. Because the full suite and
  live integration gates could not run, the overall remediation outcome is
  **blocked**, not verified/fixed.
- Local mocks, static probes, dummy Compose values, and paper trading are not
  evidence of real OCI KMS/IAM/Audit or provider success.

## Latest sealed whole-repository Deep Security Scan

- Scan ID: `c89a3440-23f1-4951-81be-44fbf08e3196`
- Scanned base revision: `67b2a7474db02cef5615d3ecbf56c884df1cb7ed`
- Completed: `2026-09-04T23:09:13Z`
- Coverage: complete whole-repository coverage; 30 independent scan reviews
- Findings: 52 total: 0 High, 39 Medium, 13 Low
- Aggregate scan token usage: 931,542,058
- Canonical artifact directory:
  `/private/var/folders/bk/f34r9qkn13d_w47jxgcx62nh0000gn/T/codex-security-scans-lXgnbx/Milkyway/67b2a7474db02cef5615d3ecbf56c884df1cb7ed_20260904T060438Z_b_2oux3_`
- Canonical files include `report.md`, `findings.json`, `coverage.json`,
  `scan-manifest.json`, `exports/results.sarif`, checkpoints, and
  `artifacts/fix_report.md`.

The 39 Medium occurrences were independently collapsed into 24 root-cause
groups before patching. Focused regressions were added in
`tests/test_medium_security_regressions.py` and adjacent owning suites.

## Source paths closed during this remediation

Independent read-only review found the traced source paths closed for 30 Medium
occurrences, including:

1. targeted login lockout while preserving bounded correct-password recovery;
2. one-time, expiring, email-bound invitations with pre-hash/global admission;
3. shared credential-backend startup and shared-mode legacy-row bypass removal;
4. stronger scrypt parameters and successful-login hash upgrading;
5. placeholder, file-secret, permission, symlink, and cross-secret validation;
6. bounded HTTP streaming and bounded auxiliary file/count/aggregate reads;
7. durable shared-quote worklist rotation, exact freshness admission, one-batch
   broker cadence, whole-paper-tick deadline, and paused reactivation admission;
8. fair/outstanding/deadline/result/retention controls for backtests;
9. dashboard broker single-flight/caching and DB-session release;
10. authenticated encrypted backup output and a separate restore topology;
11. independently promoted immutable dataset generations and explicit terminal
    event approval, separated from the scheduler writer;
12. provider readiness/preflight consistency, non-rendering Compose validation,
    and immutable GitHub Action commit pins.

This is a source-review classification only. The unavailable focused/full and
live checks listed below prevent a final `fixed` outcome under the fix contract.

## Open Medium occurrences

Nine Medium occurrences remain source-vulnerable:

### Database tenant and service containment (3)

- `occ_240dee7248d3342394fb3ec0`
- `occ_f21cf020aea0766e6d9dd46e`
- `occ_f19a293e0f861adea9e5b504`

Blanket all-table/current-and-future grants were removed and relationship
columns were narrowed, but a stolen runtime DSN can still read or mutate rows
across members within that service's broad table authority. Complete closure
requires a database-enforced tenant/service boundary such as an independently
authenticated per-tenant context plus RLS or tightly scoped approved procedures,
followed by positive/negative tests on fresh and upgraded PostgreSQL databases.
Caller-supplied user IDs from a compromised app are not an independent boundary.

### Reusable coarse broker capabilities (3)

- `occ_143f4e98598ec53b5f7a37d7`
- `occ_f84e28665b83604a4ebdc8fb`
- `occ_ba10a40f3ed321d640d66494`

The long-lived app token still authorizes any allowed AI prompt and the long-lived
paper token still authorizes caller-chosen quote work. Local limits, deadlines,
fixed providers, and quote-only endpoints reduce impact but do not provide
member-bound or schedule/worklist-bound short-lived capabilities, replay-resistant
nonces, a durable authoritative budget, or reserved scheduler capacity outside a
compromised caller. This needs an independently trusted capability issuer/store;
it is an architectural gate, not evidence that OCI has passed.

### Mutable executable supply chain (2)

- `occ_8296379c3a4e7fe2c459be18`
- `occ_dc40e1db16b6e1e885652bf2`

GitHub Actions and the Python base/llama images are pinned, but Python dependencies
remain ranged and unhashed, `pip-audit` is unpinned, the Docker build upgrades pip
and OS packages from mutable repositories, and PostgreSQL/Caddy use mutable tags.
Closure needs an authoritative transitive hash lock, approved image/package
digests, `--require-hashes`, a clean image build, and audit/SBOM evidence. Those
values were not guessed while registry/package network access was unavailable.

### Provider-secret manager boundary (1)

- `occ_d839d825b71cf34ea8506204`

Raw provider secrets were removed from container environment variables and are
now mounted from owner-only no-follow files, but they are still plaintext host
files rather than values released by a protected secret manager/KMS identity.
No OCI Vault deployment or equivalent protected secret-delivery evidence exists.

## Earlier checkpoint verification (superseded where updated above)

Passed in this managed session:

- `APP_ENV=development python3 -m unittest -v
  tests.test_universe_data_pipeline tests.test_dashboard_frontend_contract`:
  24/24 passed after the final patches.
- Focused standalone quote-capacity probe: all 200 default-admitted symbols were
  covered in five 40-symbol ticks using the durable worklist rotation.
- Focused whole-paper-tick signal deadline probe: passed.
- Dataset promotion, exact snapshot aggregate-budget, and daily-refresh
  new-versus-prior snapshot regressions: passed within the 24 tests above.
- Python source compilation: 37 files, zero failures.
- `bash -n deploy/*.sh deploy/postgres/*.sh`: passed.
- `git diff --check`: passed.
- Main, credential-broker (including `local-ai`), and restore Compose
  `config --quiet` validation with non-secret dummy values: passed. This proves
  configuration shape only.
- Direct deployment-secret, secret-file permission/symlink, bounded-I/O, and
  encrypted-backup boundary probes run earlier in this cycle passed.
- Fresh independent read-only review repeatedly found no new High/Medium in the
  final quote/snapshot delta and judged the quote starvation occurrence's source
  path closed.

Not passed or unavailable:

- `APP_ENV=development python3 -m unittest discover -s tests -v` discovered 27
  entries: 24 passed and three test modules failed to import. The host lacks
  `PyYAML` and `FastAPI`; it also lacks SQLAlchemy, cryptography, OCI, and
  `hashlib.scrypt`. Therefore the new Medium-focused suite and the broader cloud
  security suites did **not** run to completion.
- Installing requirements in an isolated temporary virtual environment failed
  because package-index DNS/network access was unavailable.
- Docker is installed, but access to
  `/Users/kimseungzoo/.docker/run/docker.sock` is denied. Images, disposable
  PostgreSQL, and containerized full tests could not run.
- No live PostgreSQL role/RLS/procedure matrix, concurrency/load test, encrypted
  restore drill, real KIS/AI provider authentication, or provider licence proof
  was performed.
- No trusted production dataset generation has been deployed and promoted on the
  target topology.

## Real OCI infrastructure gates — none simulated as success

This session has no deployed public-app VM, credential-broker VM, Vault keys,
dynamic groups, IAM policies, or OCI Audit/Alarm resources. Consequently:

1. Broker-VM successful use of both required Vault keys is **not tested**.
2. Public-app-VM `AccessDenied` for both keys is **not tested**; the public VM's
   exclusion from both key dynamic groups is also not proven.
3. OCI Audit records for successful key use and denied attempts, Audit retention,
   queries, alarms, and notification delivery are **not tested**.
4. Broker-only secret release, backup-key custody, network security lists/NSGs,
   DNS/TLS, and two-VM source restrictions are **not deployed or evidenced**.

No local mock, dummy value, file encryption test, or paper-trading result may be
substituted for these gates.

## Handoff

- Preserve all current tracked/untracked changes, `runtime/`, and user Docker
  volumes.
- Do not enter real API keys or member credentials and do not publicly deploy.
- Next local work is to finish the independent DB and broker boundaries,
  integrate shared AI with member brokerage, run fresh/upgraded PostgreSQL
  role/RLS/capability tests, complete independent reviews, and seal a fresh scan.
- After that, deploy the real two-VM/Vault/IAM/Audit topology and collect the
  exact allow/deny/Audit evidence above. Only a fresh sealed whole-repository
  scan plus all real gates can reconsider the **NO-GO** decision.
# Personal exercise scope — 2026-09-26

The user explicitly requested a separate single-owner local paper-trading
installation, implemented in `compose.personal.yaml`. Its credentials stay on
the member's trusted PC, with a local encryption root and loopback-only web
access. It does not claim the independent cloud KMS boundary. Public deployment
and collecting members' keys on a shared server remain NO-GO under the gates in
this document. The older "real member credentials" prohibition concerns that
shared deployment, not the newly requested per-owner local installation.

No real brokerage credentials were entered, no brokerage orders were sent, and
no real OCI gate or whole-repository security scan is claimed by the local
functional/fault-injection tests. Current local verification is documented in
`docs/Milkyway_검수보고서.md`.
