# Launcher repair verification

Reviewed `2cbe718`, 1 November 2026. **Most exact defects are repaired; L3 and
L4 remain incomplete.** This is verification of changed launcher/worker paths,
not authentication qualification. No credentials were opened, no Claude
client ran, and there were no provider requests.

[check.py](check.py) and [receipt.json](receipt.json) preserve 16 independent
synthetic observations through production functions. Client, inventory capture
and score execution were mocked where needed; ordinary file staging, export,
ledger, fingerprints and reconciliation were real. [native_check.py](native_check.py)
and [native-receipt.json](native-receipt.json) exercise the actual confined
worker plus a separate owned finite process. Source hashes pin all checks.

## Closure status

| Finding | Verification and disposition |
| --- | --- |
| L1 external-link export | **Closed for the demonstrated defect.** The real confined worker still creates the outside synthetic link and cannot read it; the repaired exporter refuses it and copies the ordinary positive-control file. No canary contents are exported. |
| L2 resume bypass | **Closed for the demonstrated cases.** Started-only, incomplete, persisted-halt and different-plan ledgers all reject. A prior incomplete trial cannot silently become a zero-cost completed trial. |
| L3 unenforced fingerprints | **Partially repaired.** Source/prompt fingerprints and listed material hashes are now checked. Mutation of a listed task or prompt is detected. Actual scientific dependency bytes and newly added material files remain outside the check; see below. |
| L4 count-only reconciliation | **Partially repaired.** Wrong tool identity and missing tool result are rejected. Write contents, read ranges, returned values and orphan results remain unchecked; see below. |
| L5 child cleanup | **Closed for the demonstrated defect.** The actual worker records both launched child groups; normal calls leave no live group. A registered separate-session Python sleeper is killed and independently verified absent. Cleanup no longer relies on a pathname in its argv. |
| L6 missing init/usage | **Closed for the demonstrated cases.** A transcript without init and a result lacking required usage fields each halt with `complete: false`; a complete synthetic transcript passes. |
| L7 failure evidence | **Main failure fixed.** A synthetic cleanup error now saves transcript, stderr and an incomplete trial receipt, which blocks resumption. Scratch workspace location is still absent from that receipt; see evidence-retention note below. |
| L8 partial block accounting | **Protocol addressed.** The revised protocol explicitly stops at the ceiling and preserves/reports incomplete blocks. No test here attempts to complete a block past its ceiling. Parent reviews the scientific handling. |

## R1 — runtime and material pinning still omit consumed bytes

`fingerprints()` hashes the runtime manifest, both `pyvenv.cfg` files and the
toolkit's own Python package. It does not hash the installed numerical/scientific
dependencies or compare their actual bytes against an immutable manifest.
Changing a synthetic direct-arm `site-packages/numpy/core.py` leaves the
fingerprint exactly unchanged. This is the original L3 requirement to pin the
actual runtime, not a new request to pin irrelevant files. A static manifest
hash cannot establish the state of files it describes.

`verify_materials()` verifies only listed manifest entries for the item.
`stage()` then copies *every* file in `materials/`. A newly added unlisted
`extra-reference.csv` passes verification and is staged for the analyst.
Thus the material set can grow after freeze without detection even though
changes to existing listed files are caught.

**Required:** compare the exact staged file set with the frozen manifest,
rejecting extras/missing/unsafe entries, and verify actual installed dependency
contents (or an equivalent immutable runtime image) before launch. Retain the
new source/prompt checks. The synthetic fixture never alters an installed
package or real item.

## R2 — reconciliation still accepts conflicting requests and outputs

`worker_request()` reduces a write to its path and a read to its path. The
worker audit already records write contents and read offsets/limits, so this
information is available but discarded by reconciliation. Result validation
compares only `is_error` against a broad audit status for execution tools;
returned content is never compared, and toolkit result status is exempted.

Executed cases accepted with `consistent: true`:

- event `worker_write(answer.json, "EXPECTED")` versus audited
  `worker_write(answer.json, "DIFFERENT")`, with fabricated event output;
- event `worker_read(x, offset=20, limit=10)` versus audited read at offset 0,
  limit 100;
- a result for an entirely unknown tool-use ID, without any corresponding
  call or audit record.

**Required:** normalise and compare all supported arguments, require a unique
use/result pairing with no orphan/conflicting records, and reconcile the
returned values/errors with the recorded worker execution and trusted adapter
transformation. Missing-result and wrong-tool rejection now work and should
remain. These are the remaining parts of L4, not a newly broadened gate.

## Evidence-retention note

A cleanup failure now preserves raw events, stderr and `complete: false`, which
is a material improvement. The receipt is still written before scratch path,
usage and final-state extraction are recorded. The model's workspace remains
in a random temporary directory without its location in `trial.json` or
`started.json`. Record that location when allocating it so partial numerical
work can be found after failure; keep untrusted payloads quarantined and do
not follow links. The raw transcript does retain the synthetic final usage,
so the original total loss of client events is fixed.

## Boundaries

Authentication checks, config-directory policy and model/backend authorisation
belong to the parent review and were not exercised. Native tests used only the
existing direct runtime, temporary canaries and owned child processes. The
full real-client offline integration test was not rerun here. Production,
tests, old evidence and instructions were not edited.
