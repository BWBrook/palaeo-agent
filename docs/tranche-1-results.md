# First implementation tranche

Completed 30 October 2026. The first capability is descriptive RMA regression
of labelled measurements, through a Python API and structured CLI. The
scientific contract and comparison tolerances were recorded in
[first-comparison.md](first-comparison.md) before implementation was compared
with the independent numerical reference.

Historical note: version 0.2 subsequently regenerated the stored L2 example
under run schema 2. Original schema-1 bytes remain in Git commit 445da1b.
The numerical results reported here are unchanged.

## Acquired reference material

- PAST 5.4 manual: 321 pages, supplied by Barry, preserved unchanged.
- 2001 case-study ZIP: supplied by Barry, original preserved; all 17 members
  CRC-checked, hashed and extracted byte-for-byte.
- All 14 substantive vignettes, their 10 linked suggested-answer pages, the
  original index and 49 images: 74 captured source assets.
- Original HTML and derived UTF-8 offline reading copies are separate, with
  source URLs, dates and checksums in the capture manifest.

Start at the [offline index](../benchmarks/past/vignettes/html/doc1.html).
`uv run python scripts/capture_past.py --offline` verifies source hashes and
regenerates the reading copies without a network request.

## Numerical evidence

All six Dielasma raw/log10 fits agree with independently computed
standard-library results within the prespecified `rtol=atol=1e-12`.

| Locality | Retained pairs | Raw RMA slope | Log10 RMA slope |
| --- | ---: | ---: | ---: |
| L1 | 103 | 0.8427557846904125 | 1.0183654435676799 |
| L2 | 79 | 0.8191670400279810 | 0.9817911055076792 |
| L3 | 35 | 0.9054241567685909 | 1.1071123900450557 |

**Data defect found later (1 November 2026).** The archived L2 columns hold a
repeated block. Specimens 57–63 recur exactly as 64–70, seven consecutive
length/width pairs. An analyst session found it in the authentic-workflow
study ([authentic-sessions-20261101.md](authentic-sessions-20261101.md)), and
the RMA input diagnostics now warn on it (`repeated_block`). The archived bytes
and the fits above are unchanged. The L2 values above include the block;
without it, they become:

| L2 input | Retained pairs | Raw RMA slope | Log10 RMA slope |
| --- | ---: | ---: | ---: |
| As archived | 79 | 0.8191670400279810 | 0.9817911055076792 |
| Specimens 64–70 removed | 72 | 0.8155490421432005 | 0.9764206000434580 |
| Each distinct pair kept once | 71 | 0.8155133648572809 | 0.9765259484987477 |

These are the toolkit's own RMA results, computed in that session's follow-up.
The change does not alter any rounded published value (0.82). L3 also repeats
three pairs, but in no consecutive block, consistent with coincidences of
rounding.

Only the raw slopes are comparable with the published two-decimal values
0.84, 0.82 and 0.91. Rounded published answers are distinct from the independent
full-precision calculation; neither is a new run of PAST 5.

The [numerical comparison report](../benchmarks/past/references/verification.json)
records differences for seven numerical summaries in each case. The
[stored L2 run bundle](../benchmarks/past/dielasma-l2-run/manifest.json) includes
input bytes, portable specification, retained pairs, exclusions, numerical
results, PNG/SVG diagnostics, implementation fingerprints, environment metadata
and the lockfile. Fresh-process reproduction from this stored bundle succeeded
with no numerical differences and an identical recorded environment. A separate
automated test reproduces a bundle after the original input file is deleted.

## Failure handling and review

The suite has 38 passing tests on macOS ARM64 / Python 3.12.13. It challenges
invalid IDs, missing data, malformed tables, invalid numeric ranges, unsupported
options, constant variables, zero covariance, nonpositive log inputs, incomplete
bundles, altered files and malformed records. The source archive also passed
offline hash verification. Local source-distribution and wheel builds succeeded.
The saved diagnostic plot was visually inspected for labels and clipping.

Independent review confirmed the RMA formula and identified a saved-result
validation defect: valid checksums alone allowed a structurally malformed result
through inspection. The fix uses one typed output schema for execution,
inspection and discovery. A bounded independent recheck confirmed the original
failure now returns a structured error before reproduction creates outputs.

GitHub Actions runs the locked environment, offline archive verification and
the same tests on Linux. Its actual run outcome is separate evidence from the
local checks; consult the repository's Actions results for the pushed revision.

## What this shows about the north star

The first operation makes preprocessing, omissions and evidence inspectable.
For example, indiscriminate complete-case filtering of the full Dielasma table
would retain only 35 rows for L1 and produce a raw slope of about 0.803635.
Selecting the declared L1 pair correctly retains 103 rows and gives 0.842756.
The API selects the declared pair and records omissions rather than letting
unrelated locality columns change that sample. This is an illustrated failure
mode, not evidence from a controlled comparison of agent performance.

The independent reference script remains a valid direct implementation of the
same calculation. We have demonstrated working safeguards and a reproducible
evidence path; we have not yet measured a reduction in agents' analytical errors
or independent-review effort. That comparative evaluation remains part of the
north star.

## Remaining scope and next tranche

There is one supported numerical method, in raw and log10 coordinates. There
are no standard errors, confidence intervals or significance tests. The file
reader supports the observed classic whitespace PAST table; it does not claim
to accept every PAST project or data format. Only Python 3.12 has been tested
locally. Numerical comparisons use explicit tolerances; figure bytes are not
required to be identical across environments. Bundle checksums establish
integrity relative to the manifest, not independent authenticity.

The next tranche should implement a complete community-data workflow using
the acquired Llanvirn or Llandovery examples: explicit sample/taxon semantics,
diversity, distances, an initial ordination and a small sensitivity analysis.
Select the scientific definitions and comparison references before extending
the existing execution path. No MCP server or GUI is needed for that work.

All third-party sources remain in a private development repository at Barry's
request. A public release and its redistribution/licensing decisions remain
separate. No PAST executable was installed or run, and no full PAST 5
compatibility is claimed.
