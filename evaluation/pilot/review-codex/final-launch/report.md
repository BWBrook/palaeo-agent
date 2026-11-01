# Launcher pre-freeze review

Reviewed `aedc1585a239abddea825f813d30c7fdfb91de17`, 1 November 2026.
**Do not qualify this launcher for live integration or calibration yet.**
The happy-path implementation exists, but the following error-path and
boundary checks fail. Production files were not changed.

[check.py](check.py) runs direct production functions with mocked client,
inventory and scoring, synthetic files and one owned finite process.
[receipt.json](receipt.json) records 12 observations. The separate
[native_link.py](native_link.py) and [native receipt](native-link-receipt.json)
exercise the actual confined worker on the rebuilt direct runtime. There were
no provider requests, real model-client launches or credential reads.

## L1 — supervisor export follows worker-created external links (P1)

`launch.py:214` calls `shutil.copytree` with its default `symlinks=False` on
the worker-controlled tree. A worker can create a link without being allowed
to read its target. The trusted supervisor subsequently follows that link and
copies the external file into the saved workspace.

**Native result:** the real worker created `export-me.txt` pointing to a
synthetic secret outside the trial; its own read was denied by Seatbelt with
`PermissionError`; the supervisor export nevertheless saved the canary
contents as a regular file. The mocked `run_trial` reproducer independently
shows the same export through the production launch path.

Reject links and special files using no-follow traversal before copying or
reading exported content, and keep the same restriction in downstream scoring
and reviewer staging. Do not merely preserve an external symlink and then
allow the scorer to follow it. This is a supervisor boundary failure, not an
escape of the confined interpreter. No real private file was accessed.

## L2 — a prior halt does not survive restarting the runner (P1)

`run():265–269` treats missing/null counted usage as zero and skips any trial
whose directory exists. It does not inspect an earlier `breach` or persisted
halt. Three independent cases—only `started.json`, `counted_tokens: null`,
and a previous `init_inventory` breach—all launch T002 on rerun. The no-retry
property for T001 is preserved, but the mandatory no-further-launch property
is lost.

Resume must validate the entire preceding ledger, require known valid usage
and absence of unresolved infrastructure/boundary halts, and bind output to
the exact frozen plan. Do not turn an incomplete directory into permission to
continue. Unknown counts remain unknown rather than zero.

## L3 — declared fingerprints are not enforced (P1)

`make_plan():248–255` records runtime, item-manifest and prompt hashes, but
neither `run` nor `run_trial` checks them. Only client binary and tool names
are compared. The synthetic trial with stale hashes for all three completes
with five counted tokens. Actual prompts/materials are read from live paths,
and the supervisor MCP adapter runs from the mutable repository checkout.

Validate frozen inputs, prompts, actual runtime contents, runner/adapter and
configuration before every launch, not just the manifest file's recorded
hash. A manifest whose bytes remain unchanged does not prove its listed files
are unchanged. Freeze and bind the relevant source as required by the plan.

## L4 — reconciliation accepts a different operation and no result (P1)

`reconcile():129–155` counts advertised worker events and audit rows. It never
compares names, arguments or outputs, and it does not require a result for an
advertised worker call. A `worker_execute` event for `print(42)` and no result
matches one audit row for an unrelated failed `worker_write`; `consistent`
is true. A genuinely unadvertised successful tool is rejected in the positive
control, so this is a specific incomplete reconciliation, not a bypass of all
checking.

Reconcile one-to-one identities, tool names, normalised arguments and
completion/results, with explicit trusted bootstrap/refusal categories.
Reject missing, duplicate, conflicting or orphan records. Retain mismatches.

## L5 — argv-based cleanup does not identify ordinary worker children (P1)

`cleanup():113–126` searches argv for the *trial root*. A worker executes
`python -I -c CODE`; neither its code nor its interpreter need name that root.
The profile path supplied before exec belongs to `record/worker-audit`, not
the trial tree. Worker children run in separate sessions.

A finite synthetic Python child with precisely that interpreter/-I/-c shape,
whose cwd is the trial root, survived `cleanup(trial_root)` outside the nested
sandbox: `pgrep` returned 1 (no match), and cleanup declared success. The
reproducer killed and reaped its own child afterwards. A first nested-sandbox
attempt also showed that a process-list failure is silently treated as no
survivors; the retained successful native receipt is the no-match case.

Track actual child PIDs/process groups under the trusted supervisor and
verify their termination. Treat process-inventory failures as failures. Do
not infer process ownership from an optional pathname in model code.

## L6 — missing init and incomplete token usage are accepted (P1)

`run_trial():186–190` rejects a mismatching init if one arrives, but does not
require any init record. A transcript containing only a result is accepted
with `breach=[]`. Usage containing only `cache_read_input_tokens: 100` is
accepted as zero counted tokens because missing required fields default to
zero at lines 210–212.

Require the prescribed initialization and event ordering, a valid final
record and complete non-negative numeric accounting. Reject absent or
malformed fields; do not infer known zero usage from missing data. The external
reader itself is not a pre-dispatch acknowledgement barrier; retain the
client's proven disabled-tool dispatcher as the confinement basis.

## L7 — cleanup failure loses canonical trial evidence (P1)

`cleanup()` runs before transcript, stderr, workspace and `trial.json` are
saved. A synthetic cleanup error leaves only `started.json` in the record,
even though client events and valid usage were available. The scratch path
is not in `started.json`. This combines with L2 to permit continuation on
restart.

Persist transcript/usage and scratch location incrementally, and write a
failure receipt in a `finally` path before surfacing cleanup/export/scoring
errors. Keep unsafe payloads quarantined without following their paths.

## L8 — balanced ordering does not ensure a balanced stopping point (P2)

A four-trial family block with a ceiling of five tokens and first-trial use
of six stops after the first trial. The sequence is balanced in advance, but
completed observations are not. A launch-stop ceiling should still stop the
next trial; do not quietly exceed it to finish a block. Freeze the analysis
of incomplete blocks, preserve them and report their count; if complete blocks
are required for the primary comparison, define that subset prospectively.

## Evidence limits and next check

The full native Claude end-to-end test was not rerun here; the parent owns
suite and runtime receipt verification. These focused counterexamples already
invalidate live readiness irrespective of the happy-path test. The inventory
capture itself preserves only tool names from the first request, not full
schemas or a per-launch raw capture, and its timeout path has no explicit
worker cleanup; include those in the repaired gate's adversarial tests.

Once repaired, rerun the exact synthetic counterexamples as negative tests,
then actual confined export and supervisor-abort cleanup, then the real-client
offline path. Only after those pass should bounded live integration begin.
