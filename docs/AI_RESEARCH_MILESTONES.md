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
