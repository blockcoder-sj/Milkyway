# Native startup: macOS cloud placeholders

The native app exited during company-data bootstrap with `input file changed
while it was being read`. This was reproduced on an unmaterialized public JSON
file in the local checkout, without API credentials or external provider calls.

The file had macOS `SF_DATALESS` set before the read. The original reader read
all 875,000 bytes successfully, but downloading the placeholder cleared that
flag and changed its nanosecond modification timestamp by 64 ns. Device, inode
and size stayed the same. The generation guard therefore rejected the read.
This is a local cloud-file materialization problem, not a brokerage connection
failure or a missing Python installation.

The reader now probes one byte through the same no-follow descriptor only for
nonempty dataless files, rewinds, and captures fresh metadata before the bounded
read. It checks the size again after materialization. The existing final
device/inode/size/mtime comparison remains intact. Aggregate read budgets reserve
the additional probe byte before I/O. Local files take the original path with
no probe or extra budget. Platforms without `SF_DATALESS` keep that path too.

The native launcher startup allowance increases from 120 to 600 seconds because
cold cloud files and Python imports can take longer than two minutes. Failed
child processes still fail immediately; this does not retry failed orders or
change any application data.

Verification:

- Six new placeholder regressions plus seven existing bounded-reader and budget
  checks passed (13 total), including actual-change, oversized-file, symlink,
  concurrent-growth and aggregate-budget rejection.
- An actual previously dataless `energy_issuers.json` passed the fixed bounded
  JSON reader on its first read; materialization changed its mtime by -97 ns.
- The patched native launcher started successfully, shut down cleanly, and
  started again. Both startup/ready endpoints returned 200; the second start
  took 3.65 seconds on the warmed installation. All three execution workers
  responded. Brokerage data readiness was false, as expected without API setup.
- The existing native integration script passed startup, authentication, assets
  and the collection queue, then failed its private-company reverse-relation
  assertion at line 98. Running the same script with the unmodified reader
  reproduced the same assertion. This pre-existing unrelated failure remains;
  a full integration pass is not claimed.
- No real API keys, brokerage orders, AI provider calls, personal runtime,
  Docker volumes, or original installed applications were used for these checks.

This fix addresses the reproduced startup failure. It is not evidence of a real
five-day brokerage run or validation of every possible installation failure.
