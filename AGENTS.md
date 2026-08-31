# Milkyway project instructions

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
