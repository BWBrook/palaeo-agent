# Sprint 9 implementation review

Codex (`gpt-6.1-sol`), 8 November 2026. Reviewed `a369329` against
[the contracts](sprint-9-contracts.md). Production code and tests are unchanged
by this review.

**Two small fixes remain before acceptance.** The numerical diagnostic,
taxon-exclusion behaviour and live MCP exposure pass the checks below.

## Findings

### P2: inspection does not bind the pair declaration to its specification

In `src/palaeo_agent/methods.py:188`, `validate_result` compares the resolved
pair list with the saved specification, but not the `pair_declaration` mode
and block counts. The result validator checks the declaration's internal
consistency separately. Consequently two different descriptions can pass
together:

```json
{"pairs": "adjacent"}
```

```json
{"pair_declaration": {"mode": "explicit", "n_adjacent": 0, "n_extra": 2}}
```

Reproduced through public `run`/`inspect_run` on three samples S1/S2/S3
with count rows [10,5], [8,7], [2,12], B = 999 and seed = 5. Change only
the result's declaration as above and update the result file's SHA-256 and
byte count in `manifest.json`. **Inspection returns `status: verified`**
although `spec.json` still declares adjacent mode. The numbers and pair
order are unaffected; the claimed declaration provenance is wrong.

Compare the saved declaration with the mode, adjacent-block length and
extra-block length implied by the specification and retained samples. Add a
regression that updates hashes before inspection so that it tests semantic
verification. Cover both adjacent-to-explicit and explicit-to-adjacent flips
when the resolved pairs happen to be identical.

### P2: discovery advertises the old method version

`src/palaeo_agent/methods.py:103` still sets count-homogeneity discovery
`version` to 1. Its output schema and actual results require method version
2. This inconsistency is exposed to both Python and MCP clients.

Advertise version 2 and test agreement between discovery, the output schema
and a produced result. Describe the new Holm diagnostic in the catalogue
alongside the existing raw-tail limitation.

## Verification completed

- **Full suite:** `uv run pytest -q` passes **693 tests, 11 skipped** with
  process-list access. The initial nested-sandbox run had 692 passes and
  failed only the pilot worker-cleanup test because `/bin/ps` was denied.
  The unrestricted rerun resolves that environment failure. Optional native
  confinement tests remain skipped; no new runtime freeze was built.
- **Independent numerical reference:** R 4.6.1 `stats::p.adjust(method="holm")`
  and `qbeta` agree on **188 numeric/flag comparisons**, absolute tolerance
  1e-12. Maximum differences: public API fields 2.08e-16; tied/zero/one
  edge vectors 0; Clopper–Pearson endpoint checks 6.46e-13. Cases include
  b = 0/B, fixed-vector permutation, threshold equality, and both directions
  of disagreement between the raw-tail and Holm sensitivity flags.
- **Semantic numerical checks:** seven tampered bundles with updated hashes
  are rejected for altered raw/envelope bounds, flags and scope labels.
  This is distinct from the pair-declaration gap above.
- **Live MCP SDK/stdio:** `study_run` exposes the `exclude_taxa` discriminator;
  method discovery exposes adjacent/extra pairs and all new envelope fields.
  Tiny runs verify retained input order, extra-pair ordering, explicit-list
  equivalence, paginated result retrieval, exclusion/empty-sample handling,
  and run/study reproduction. Named refusals are returned, and failed studies
  remain inspectable as partial bundles.

The current full primer was read; version 0.2.0.dev0, SHA-256
`1557cf7444a59526c8d6e9b910ec3b4a9103e21c4f1714fe032a51ededa6486b`.
Supported calculations and bundle checks used the API. R is an independent
arithmetic reference under primer section 7; tampering, schema inspection
and test orchestration are review tasks. These checks do not re-evaluate
the Lake Selina reconstruction or the sampler's distribution.

## Independent reference evidence

[Captured fields and summary](../references/independent/2026-11-08-sprint9/summary.csv)
include 80 public API comparisons, 64 edge-vector comparisons and 44
Clopper–Pearson endpoint comparisons. Recompute the reference from the
repository root:

```bash
Rscript --vanilla references/independent/2026-11-08-sprint9/reference.R \
  references/independent/2026-11-08-sprint9
```

The script uses the captured API/helper fields in `api.csv`, `edge.csv` and
`cp.csv`; it independently derives the reference values rather than calling
the Python Holm implementation. API runs used five disjoint pairs, B = 999,
seed = 426, first in declared order and then in a permutation. Deliberately
repeated synthetic profiles produced the expected identical-profile warning.

Fix the two findings, add the focused regressions and run the affected checks.
No additional case-study science or broader toolkit feature is requested.
