# AI strategy research milestones

Scope: single-owner `compose.personal.yaml`, US equities and validated StrategySpec.
Existing runtime and brokerage ledger are preserved. Every OpenAI call requires
the user's explicit approval; development checks use a synthetic provider only.

1. **M1 — Conversations and approval:** ignored `.env`, configuration status without
   remote probes, durable research sessions and immutable strategy versions,
   request preview/approval/cancel, bounded single-call provider transport.
2. **M2 — Experiments and paper:** common-window candidate comparisons, separate
   development/validation jobs, evidence in follow-up chat, selected-version
   paper accounts, runnable strategy export.
3. **M3 — User workflow:** Korean research interface, approval details, experiment
   comparison and account history, full regression and packaged workflow checks.

Each milestone is reviewed directly, checked with the existing tools, committed,
and pushed to `codex/ai-research-workflow`. No CodeRabbit is used.

## Verification log

M1 implemented. Direct review covered approval replay, owner isolation, request
expiry, failed-call recovery, atomic strategy/version persistence and secret
exclusion. Ten research HTTP/provider tests pass using a synthetic provider.
Actual OpenAI/brokerage calls require separate user approval and are not part of
the offline test suite.

M2 implemented. Experiments capture an immutable history generation and terminal
events, enqueue separate development/validation runs, rank on development only,
and expose result/fill evidence to the next approved turn. Paper creation pins an
immutable version and deduplicates repeated requests. Python exports use the
existing validated execution engine. 49 research/personal API/paper tests pass;
synthetic prices are fed through the real backtest worker. Review found and fixed
empty terminal-event handling. No external AI/broker calls were made.

The default model is now `gpt-5.4-mini` with `reasoning.effort=none`. Both appear
in the exact request preview; changing either invalidates a pending approval.

Local folders were consolidated on 2026-09-29. `Milkyway-local-ready` was a linked
Git worktree, not a separate product. The latest branch is now the ordinary
`Milkyway` checkout. Previous local changes and Git metadata are retained outside
this checkout in `../output/backups/`; runtime volumes were not changed.

M3 implemented. The Korean personal research panel includes sessions, request
preview and explicit paid-call approval, durable chat, version/rule/code views,
comparison selection, split-window results and paper-account history. The local
AI settings are visible without credential probes. The guide documents the single
folder, `.env`, supported strategy grammar, costs/approval and remaining live gates.

Verification on 2026-09-29:
- Full existing + research suite: **273 tests passed** (Python 3.12).
- Python compilation, JavaScript syntax and `git diff --check`: passed.
- Personal Compose configuration parsed with an empty env file: passed.
- Headless Chrome against a temporary SQLite/history fixture: preview, reload of
  awaiting approval, synthetic approved response, version creation, selected-version
  paper creation, history dialog, comparison objective and mobile layout: passed.
- Desktop 1440px and mobile 390px screenshots inspected; no browser errors or
  horizontal page overflow. Browser testing found and fixed disabled-select values
  being omitted by FormData. A fixture-only runner prevents approvals against a real app.
- Updated old test fixtures/source contracts for the new personal-mode setting and
  the shared transaction context managers; quota lock checks remain asserted.

Limits: Docker runtime/image integration was not rerun (daemon unavailable); static
Compose validation and the real local ASGI app/browser path were checked. No real
OpenAI or brokerage calls, live model-quality evaluation or continuous market-hours
paper run was performed. The existing public deployment NO-GO is unchanged.

## M4 — Personal local entry without login (2026-09-30)

The user requested skipping login for the personal installation. Opening the app
now creates or reuses its single local owner and enters the strategy screen.
Existing owner IDs, passwords, strategies, credentials and paper records are
preserved. Multiple owners or an inactive owner fail closed instead of choosing
an account. The personal profile hides the logout action.

The bootstrap is confined to development personal mode with one local owner.
It requires a loopback Host, matching Origin, same-origin Fetch Metadata when
present, and a custom request header. Ordinary signed HttpOnly/SameSite sessions
and CSRF checks remain in use. Creation shares the registration admission lock;
concurrent tabs keep one owner and at most ten stored browser sessions. The
new owner has no usable password. This installation intentionally trusts people
using the PC and must remain bound to loopback.

Direct review and verification:
- **283 tests passed**, including seven new HTTP/session tests and one executable
  JavaScript bootstrap test; no real AI/provider calls.
- JavaScript syntax and `git diff --check` passed.
- Local Docker image rebuilt and all five personal services started. Startup
  health and SQLite integrity passed; all four worker heartbeats were alive.
- Chrome at `http://127.0.0.1:8080/#strategy` visibly entered without account or
  password input. The real UI reported the AI key configured, approval required,
  and brokerage not yet connected. A static asset version bump fixed stale
  browser JavaScript during this check.

This supersedes the earlier local Docker/Chrome availability limitation. Real
OpenAI requests, brokerage authentication, and market-hours fills remain untested.
