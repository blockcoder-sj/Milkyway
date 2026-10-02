# Milkyway project instructions

## Resume context

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
