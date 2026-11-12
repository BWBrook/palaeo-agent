# Sprint 14 implementation review

Codex, 12 November 2026. Review of `8b0254d`, following Board 3315.
**REPAIR two saved-record checks before application 5.** The numerical engine,
bounded rounding and reference comparisons are accepted. No production code
was changed and Lake Selina remains unzoned.

Primer version `0.2.0.dev0`, SHA-256
`fcc02a57db1ffa2a86d14e7c2540bd7bfa89c14e7e5b3334286f9a24b16747f6`,
read in full before analytical work.

## Required repairs

### Exclusion records can invent or duplicate excluded samples

At `coniss.py:_validate_saved_result`, subtracting the set of excluded IDs
from the input IDs does not establish that those exclusions are real and
unique. Starting with a valid three-row public run under `empty_samples: drop`,
adding `{"sample_id":"ghost","reason":"empty_sample"}` to `excluded`
still passes inspection after refreshing the checksum and tables. It claims
n_input=3, retained n=3 and one exclusion simultaneously.

A valid four-row run with one genuinely empty level also passes after its
exclusion record is duplicated: n_input=4, n=3 and two exclusion entries.

Require excluded IDs to have the right type, belong to `input_sample_ids`,
be unique and satisfy `n_input == n + len(excluded)`, alongside the existing
retained-order and missing-policy checks. Add rehashed regression cases for
an unknown ID and a duplicate real exclusion. Keep the declared drop
semantics and new adjacency unchanged.

### A warning role falls between the two warning validators

Adding a `near_duplicate_labels` warning with `details: {"role":"banana"}`
and arbitrary text also passes rehashed inspection. The CONISS model skips
all warnings with a table-warning code, while the shared `_from_table` filter
checks this code only for the roles `sample` and `taxon`. The injected role
therefore reaches neither comparison.

The saved warning list must be fully accounted for by recomputed table
warnings plus recomputed CONISS warnings. Unknown roles/categories cannot
be silently ignored. A local complete-list check is sufficient; no broad
redesign of other methods is requested. The regression should refresh both
hashes and every generated table so it exercises semantic validation.

Both defects were found in a bounded independent review and reproduced by
the parent through `run` and `inspect_run`, not only private model calls.
The numerical arrays need no change to demonstrate either defect.

## Numerical implementation accepted

The exponent placement, integer quotient/isqrt and exact midpoint comparison
remove the unbounded neighbour walk. Independent bisection tests include
underflowing/subnormal seeds, half-even ties and the normal boundary. The
exact member-based oracle checks the coordinates independently before
comparing the hierarchy, costs, boundaries, broken stick and reported values.
The ordinary rioja reference remains separate from that exact oracle.

Claude's disclosed threshold difference is coherent: a **coordinate** is the
rounded binary64 number, whereas a **reported metric** is checked as an exact
quantity before rounding. A coordinate just below the normal boundary may
round up and be accepted; an exact metric below it is refused. Label these
stages explicitly in the contract so this is a declared policy, rather than
an accidental difference between checks. It needs no numerical change.

The constant-data small-margin warnings are truthful. Their verbosity is
not a correctness blocker; retain the traceable warnings for this tranche.

## Discovery decision

The compact prefix is **3,062 characters**, measured by the existing test's
serialization rule before `"methods"`, within its limit of fewer than 3,072.
Dropping repeated-pair and identical-profile warning mentions from that
shortlist is acceptable: both codes remain in the full schemas, and agents
must read the method and returned warnings. Method-selection constraints
and the primer's warning instructions remain available.

One small wording correction is needed in the CONISS shortlist:
`refuses: ["unordered positions", "subnormal values"]` suggests raw subnormal
abundance cells are rejected. They are not: a public run with only subnormal
raw weights can have ordinary proportions and valid derived quantities, and
passes inspection. Say **"tiny derived values"** (or equivalent) instead.
This fits the existing prefix budget and describes the actual refusal domain.

## Verification and limits

- Full suite: **904 passed, 11 skipped**, in 88.96 seconds.
- Focused CONISS module: **69 passed**. Separate read-only numerical and
  bundle/interface reviews support the conclusions above.
- Reran the pinned **rioja 1.0-7** generator into a temporary output. It
  regenerated the committed four-case reference **byte for byte**.
- Live MCP: the advertised run schema accepts a CONISS request; validation,
  run, inspection, result-field access and a fresh-server reproduction work.
  The scalar result matches native inspection; reproduction reports zero
  relative and absolute tolerance.
- Public synthetic tampering reproduced the ghost exclusion, duplicate
  exclusion and unmatched warning role, all currently labelled `verified`.
  No real-core data or new application outputs were used.

The [probe](../references/independent/2026-11-12-sprint14-implementation/probe.py)
and [receipt](../references/independent/2026-11-12-sprint14-implementation/receipt.json)
preserve public-API and live-transport evidence. The probe records whether a
later version refuses the cases, rather than insisting that a repaired
version retain the defects. R reference regeneration is a separate command:

```sh
Rscript --vanilla references/r/coniss_reference.R /private/tmp/s14-r-recheck.json
uv run references/independent/2026-11-12-sprint14-implementation/probe.py
```

The reference uses the existing project R library and performs no package
installation. These checks establish numerical/reference agreement and the
observed integrity failures; they do not establish ecological validity or
boundary uncertainty. Existing scientific applications were not rerun in
this review. Once the two record checks are repaired and confirmed, the
agreed application-5 freeze and four-run analysis can proceed without another
scientific-design round.

## Repair confirmation, 12 November 2026

Both checks are closed at `c38696d`. The original public probe was rerun
with its output redirected, preserving its historical receipt: unknown
and duplicate exclusions and the unmatched warning role all return
`invalid_bundle`. The live MCP and exact fresh-server checks still pass.
The focused selection passes 73 tests; the full suite passes 907 with
11 skipped (88.82 seconds). The discovery prefix is 3,065 characters and
now says "tiny derived values". The contract names the two representability
stages. The engine is accepted for the fixed application-5 execution.
Confirmation is preserved in
[repair-check.json](../analyses/lake-selina-zonation/repair-check.json).
