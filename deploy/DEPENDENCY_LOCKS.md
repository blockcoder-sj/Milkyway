# Reproducible build inputs

`requirements.in` contains direct dependency ranges. `requirements.lock` pins the
complete Python 3.11/Linux resolution and the official PyPI SHA256 values of its
non-yanked wheels. Install with `--require-hashes --only-binary=:all:`. The
`requirements.txt` compatibility entry point enforces the same flags.

The lock supports Linux ARM64 and AMD64 wheel selection. Other Python versions
and operating systems require their own resolution and verification. Audit and
lock-generation tools have separate `.in` and hash-locked `.lock` files so they
do not enter the application runtime.

To update, install `requirements-lock.lock` in a disposable Python 3.11/Linux
environment and run `python deploy/lock-dependencies.py`. Review all changed
versions and hashes, build from scratch, run regressions on the built image,
and run the hash-locked pip-audit commands in CI. Retain its JSON and CycloneDX
SBOM with the release evidence. A lock prevents unnoticed input changes; it
still needs regular reviewed updates when vulnerabilities are disclosed.

The Python, PostgreSQL, Caddy and local-model images are pinned by digest.
Debian inputs are restricted to the signed 2026-09-01 archive snapshot in
`deploy/debian.sources`; the Dockerfile replaces every inherited package source
and pins its direct OS packages. Archive expiry checking is disabled only for
these immutable snapshots; archive signature verification remains enabled.

2026-09-05 verification artifacts are recorded in
`SECURITY_REMEDIATION_STATUS.md`. Host cloud-init package updates are separate
from the image build and still require a reviewed deployment record.

Reference: [pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/),
[Debian snapshots](https://snapshot.debian.org/).
# OCI host bootstrap

`deploy/oci/cloud-init.yaml` uses Ubuntu 24.04 archive packages from the signed
`20260901T000000Z` snapshot only. Docker Engine 29.1.3, Compose 2.40.3, Buildx
0.30.1, containerd 2.2.1 and runc 1.3.4 are pinned to exact Ubuntu package
versions. Both ARM64 and AMD64 indexes contain those versions. Inherited live
APT sources are preserved outside the active source directory. The bootstrap
does not fetch a new Docker signing key or execute a live repository installer.

The complete install script passed in the ARM64 verification image
`ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`.
APT verified archive signatures and package hashes; CLI/Compose/Buildx version
checks passed. The test used a temporary container and suppressed daemon startup.
OCI boot, kernel, systemd and host networking still require the real environment.

Choose and record an immutable OCI Ubuntu image OCID dated no later than the
snapshot. For updates, change the snapshot and exact versions in a reviewed
patch, repeat installation/compatibility/security checks, and roll out the same
approved set to both VMs. Do not add a live APT source alongside the snapshot.
Snapshot availability and the update mechanism are documented by
[Ubuntu Snapshot Service](https://snapshot.ubuntu.com/).
