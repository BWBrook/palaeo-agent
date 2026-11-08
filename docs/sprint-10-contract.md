# Sprint 10 contract: abundance input for `community` and `permanova`

Claude (Opus 5.5), 8 November 2026. Scope as agreed in Codex's
[review](../analyses/tas-surface/REVIEW.md) (Board 3024). It was written
alongside the implementation, which follows it.

## Value types

| `value_type` | Meaning | Methods |
| --- | --- | --- |
| `count` | exact nonnegative integer specimen counts | all count methods, unchanged |
| `abundance` | finite nonnegative fractional weights: percentages, proportions, or other weights | `community`, `permanova` only |

- **No conversion either way.** `rarefaction` and `count_homogeneity`
  accept `count` only, so they refuse abundance input, including
  integer-valued abundance tables. A count declaration still refuses
  fractional tokens, and its message now points to `abundance`.
- **Units and denominator are not inferred.** The source unit (percentage,
  proportion) and its denominator belong in intake provenance. The toolkit
  never infers units from row sums or integer-looking cells.

## Parsing and refusals for abundance

Each token must be a finite, nonnegative decimal. A positive token that
would underflow to 0.0, or overflow to infinity, in float64 is refused
(`invalid_abundance`), as is any nonfinite row sum (`abundance_range`).
Missing cells, orientation, metadata, the empty-sample policy and the
ordination rank rules are unchanged.

## Transformations keep their meaning

- **`transform: "none"`** uses the supplied weights unchanged. Raw
  Bray–Curtis on percentage weights is defined and allowed.
- **`transform: "relative_abundance"`** explicitly closes each retained
  row to 1. After a taxon exclusion, that composition is conditional on
  the retained categories. Rows are never closed silently.
- **Jaccard** is binary, `value > 0`, with `transform: "none"`. There is
  no rounding and no detection threshold.

## Outputs and honest labels

- **Count results keep their existing field names**, and their outputs
  are byte for byte unchanged: `retained_counts`, diversity `total`, and
  `raw_count_total_imbalance_bound` in comparisons.
- **Abundance results use honest names instead:**
  - `retained_values` (saved as `retained_values.csv`);
  - diversity `weight_sum`, which is not specimen N;
  - `raw_weight_sum_imbalance_bound`.
- **Each result carries only its own branch's names.** The validator
  refuses a result that carries both, or the wrong one.
- **Diversity:** richness counts positive categories. Shannon and Simpson
  use row-normalised weights. The limitations state that abundance input
  supports no count-based estimator and no sampling-effort correction.
- **`method_version` stays 1** for both methods. The abundance branch is
  additive and identified by `value_type`, count outputs do not change,
  and existing count bundles still validate.

## Study layer

- **Input kinds:** `counts`, `abundance`, `measurements`.
- **Binding:** each analysis's `value_type` must match its input kind.
  An abundance input feeds only `community` or `permanova`.
- **`exclude_taxa`:** works on abundance tables and does not renormalise.
- **`map_taxa`:** sums abundance weights as exact decimals, refusing on
  inexact arithmetic. Count merging keeps its exact integer path. Summing
  assumes the merged categories are disjoint and share one denominator;
  the reason field must say so.

## Inspection

`CommunityResult` validation now recomputes the transformed matrix, the
distances and each diversity record from the retained values and the
declared transform and distance. This closes a gap that predates sprint 10
and also applied to count runs. `permanova` already recomputed them. The
specification's `value_type` is bound to the result, as before.

## Evidence

- `tests/test_sprint10.py`, 21 tests:
  - honest labels;
  - invariance to a common factor;
  - row scaling against closure;
  - Jaccard;
  - token refusals;
  - empty rows;
  - count-only refusals;
  - PERMANOVA run and inspection;
  - three tamper cases with rehashed manifests;
  - an exact-decimal study merge from start to finish;
  - study binding in both directions.
- **Full suite:** 717 passed, 11 skipped.
- **Lake Selina final design** rerun under sprint 10: every number is
  identical; only the environment and primer hashes change.
- **vegan 2.7.6** (repo renv), on a percentage table: raw and closed
  Bray–Curtis, Shannon, Simpson and PERMANOVA F match exactly; R² differs
  by 5.6 × 10⁻¹⁷.
