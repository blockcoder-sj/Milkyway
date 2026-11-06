# Milkyway project instructions

## Current beginner distribution

- On 2026-11-03 the user requested a smaller beginner download. Keep sector
  summary cards visible and noninteractive. Company/sector research, financial
  catalogues, graph views and semantic dependencies are excluded from Git and
  default collection. Preserve the original files under the gitignored
  `runtime/archives/sector-research-20261103/`; do not restore or collect them
  without a new request. Major-index/FX charts and paper trading remain in scope.
- Current implementation and running status are recorded at the end of
  `docs/WORK_CONTEXT.md`. October pause observations below are historical.

## Resume context

- Latest instruction on 2026-10-11: save context and pause work. The user also
  requested stopping Milkyway-related runtime to reduce memory pressure.
  Read `docs/SESSION_HANDOFF_20261011.md` first. The four personal services are
  stopped with containers, volumes and data preserved. Do not implement,
  restore, collect or start the app until the user resumes. Other projects'
  services and the shared Docker engine must be preserved.
- Prior instruction on 2026-10-05: the user resumed UI development, requesting
  plain drag to pan, Shift+drag to rotate, an initial-view reset button and
  closer spacing across company/sector maps. This supersedes the October 4
  session pause for that scope. Preserve existing personal data and services;
  do not restart the completed free-data investigation or restore old backups.
  Read `docs/ENERGY_CONSTELLATION_CONTROLS_REVIEW_20261005.md` for this update,
  `docs/SESSION_HANDOFF_20261004.md` for the preceding checkpoint,
  `docs/NEW_PC_RESUME_REVIEW_20261004.md` for actual restoration evidence,
  `docs/WORK_CONTEXT.md` for progress, and `docs/RESUME_PROMPT.md` for resuming.
  Earlier restart observations and resume instructions are historical.
- For cross-computer continuation, read `HANDOFF.md` and
  `docs/HANDOFF_OTHER_COMPUTER.md` first. The latest explicit user pause overrides
  older instructions to continue without stopping; resume on the user's request.
- Read `docs/WORK_CONTEXT.md` when resuming this project. It records the latest
  completed work, verification evidence, user preferences, and remaining limits.
- Treat runtime observations as dated evidence; confirm current Git/runtime state
  before claiming that those observations still hold. Never store secrets there.

## Single-owner local exercise

- `compose.personal.yaml` is explicitly authorized for a member's own trusted
  PC, with loopback-only access and local credential custody. It is separate
  from public multi-tenant deployment and does not claim OCI/KMS isolation.
- Preserve personal runtime and backup volumes. Never substitute mock quotes
  for a failed member feed or describe accelerated tests as a real week of
  uninterrupted brokerage operation.

## Security remediation handoff

- Before continuing security, deployment, credential, OCI, KMS, backup, or
  production-readiness work, read `SECURITY_REMEDIATION_STATUS.md` completely.
- Preserve the existing uncommitted working tree, `runtime/` data, and user Docker
  volumes. Do not discard or overwrite pre-existing changes.
- When asked to continue the remediation, first confirm that the effective session
  uses a managed `:workspace` permission profile rather than
  `permission_profile type="disabled"`.
- Run a new whole-repository Codex Deep Security Scan only in that managed session.
  Remediate every validated or plausible high/medium finding with a focused
  regression test, full verification, and a fresh independent read-only reviewer;
  repeat until the reviewer and tests pass.
- Do not claim real OCI Vault/IAM/Audit or KMS success without evidence from the
  deployed two-VM environment. The public app VM must remain outside the
  credential-key dynamic group and must be proven unable to use both keys.
- Public deployment and real member credentials remain NO-GO until the sealed scan
  and every real OCI gate listed in `SECURITY_REMEDIATION_STATUS.md` pass.

## Milestone completion checks

- The user resumed on the new PC on 2026-10-03 and requested continuous work.
  A milestone is a review, verification, commit and push checkpoint, not a reason
  to stop or ask to continue. Continue the next in-scope task after each push.
  Stop only when the requested work is complete, the user pauses it, or a concrete
  blocker requires new information or authority. Report the blocker precisely.
- For every completed milestone, check functionality, performance, code quality,
  and security before committing and pushing to GitHub. Record actual evidence
  and remaining limitations; do not claim unperformed checks.
- Review source directly. Never use CodeRabbit (including its CLI, API, plugins,
  IDE extension, or GitHub review bot).
- Actual AI provider calls require the user's explicit approval for that call.

## Local resource use

- The user reported high RAM pressure on 2026-10-02. Reuse one development
  browser tab and run expensive verification jobs one at a time. Remove disposable
  verification containers after preserving their evidence; preserve personal
  runtime and backup volumes and the user's other apps/tabs.

## One canonical distribution

- The user requested one original Milkyway distribution on 2026-11-06. Use
  `main` for code, downloads and updates. Do not create or maintain separate
  classroom/education branches. Preserve historical account specifications;
  compatibility adapters do not represent separate product editions.
