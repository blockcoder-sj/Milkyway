# ZIP installation updater and market display supervision

The native launcher omitted market-data and market-details, so authentication
could succeed while the market display cache stayed empty. Both display workers
now start, restart and stop under the same supervisor as the other services.
Brokerage execution prices remain separate from the display fallback.

`update_milkyway.py` adds a standard-library updater for existing ZIP installs.
README contains a one-line GitHub bootstrap for old versions; updated launchers
also support `run_milkyway.py update`. The updater locks setup and launcher state,
resolves the classroom branch to a commit, bounds the archive, rejects unsafe
paths/symlinks/duplicate names, and installs only source directories and files.
It does not read personal keys or replace runtime/backups/logs/.venv/.env. Handled
file-replacement failures roll back changed code. An interrupted OS process or
power failure during replacement is not claimed to be an atomic whole-tree update.
Restart is explicit; updating does not itself start trading or provider requests.
The requirements fingerprint now includes the native lock so the usual next
start installs a changed dependency set.

Verification: 37 focused tests passed, including updater data preservation,
network/write failure, rollback, active-launcher refusal, path/symlink rejection,
parent extraction directory resolution, market-worker launch/restart/shutdown,
and existing market-cache/broker projection checks. Python syntax and diff
whitespace checks passed. Tests use temporary data and synthetic providers;
no real credentials, brokerage requests or orders were used. Native Windows
end-to-end execution and a five-day brokerage run are not claimed.
