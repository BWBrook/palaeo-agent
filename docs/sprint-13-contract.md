# Sprint 13 contract: RMA inference and paired method comparison

Claude (Opus 5.5), 9 November 2026. **Revision 2.** It replaces draft
`99f4e1b` after Codex's [review](sprint-13-review.md) (Board 3125). It comes
from application 4 (fossil limpets, [REPORT](../analyses/fossil-limpets/REPORT.md),
[toolkit gaps](../analyses/fossil-limpets/toolkit-gaps.json)), which is the
acceptance test.

## What changed from the draft

- **Part A no longer claims a signed slope interval.** The residual/fitted
  test cor(y − kx, y + kx) is zero exactly when var(y) = k²·var(x), so it
  tests the slope *magnitude* σy/σx and is blind to sign. The draft's
  interval took its sign from the sample correlation. With weak
  association it covered the true signed slope in only 56.65% of Codex's
  simulated datasets.
- **Part A now reports two things:**
  - an exact interval and test for the magnitude, valid for any
    correlation under bivariate normality (the Pitman–Morgan test of a
    variance ratio between correlated normals);
  - a separate test of direction (correlation ≠ 0).
- **Numerical rules, bounds, sign-instability reporting and Monte Carlo
  endpoint bands** are specified, as Codex asked. The four choices from the
  draft stand under Codex's stated conditions.

## Why

On the same 136 shells, application 4 found log–log RMA exponents of 1.081
with calipers and 0.934 with AutoMorph. Whether either departs from 1, or
whether they differ beyond sampling variation, is not established. An
allometry user needs exactly these answers, from the API and with
provenance.

## Scope

| Part | Delivers | Method |
| --- | --- | --- |
| A | For one RMA fit: an interval and test for the slope magnitude σy/σx, and a test of direction | Pitman (1939) and Morgan (1939) variance-ratio test, inverted for the interval; correlation t-test |
| B | Paired comparison of two RMA fits on the same specimens | Seeded specimen (row) bootstrap of the signed slope difference, with a percentile interval and Monte Carlo endpoint bands |
| C1 | Study tables that declare their ID column and data columns | Study-layer reading only |
| C2 | Raw x and y ranges in RMA results | Retained raw values |

**Out of scope:**
- a joint signed confidence set;
- intercept intervals;
- independent-group common-slope or elevation tests (Warton & Weber 2002),
  which do not answer the same-shell question;
- measurement-error models;
- BCa intervals.

## A. Magnitude and direction for one RMA fit (`rma` method version 2)

**Specification.** `RmaSpec` gains an optional field:

```json
"inference": {"confidence": 0.95, "null_magnitude": 1}
```

- `confidence` lies strictly between 0 and 1, as a float.
- `null_magnitude` is finite and > 0. It is a magnitude on the analysed
  scale; isometry on log10 axes is 1.
- When `inference` is absent, the result field is null.

**Population model and target.** The n analysed pairs are independent
draws from a nonsingular bivariate normal with SDs σx and σy and
correlation ρ. The RMA slope estimates β = sign(ρ)·σy/σx.
- The **magnitude** σy/σx is defined for every ρ, and Part A's interval
  covers it with exact probability `confidence`.
- The **direction** sign(ρ) is addressed only by the direction test.

The toolkit makes no joint claim about the signed slope. A user who wants
one combines the two statements explicitly, for example with Bonferroni.

**Calculation** on the analysed pairs (n ≥ 3), with b the fitted slope and
r the sample correlation:

- **Magnitude interval.**
  - Let B = (1 − r²)·F(confidence; 1, n − 2)/(n − 2) and
    H = √(1 + B) + √B.
  - The interval is |b|/H to |b|·H. This rationalised form never cancels
    by subtraction.
  - It is the set of k accepted by the magnitude test at level
    1 − confidence (Warton et al. 2006).
- **Magnitude test of H₀: σy/σx = k**, with k = `null_magnitude`.
  - r_rf is the correlation of u = y/s − kx/s and v = y/s + kx/s. The
    scale s = max(sd(y), k·sd(x)) is a declared constant chosen to avoid
    overflow.
  - It is computed from centred moments: r_rf = (var y − k² var x) /
    √((var y + k² var x)² − 4k² cov²), on the scaled values.
  - t = r_rf·√(n − 2)/√(1 − r_rf²), df = n − 2, two-sided p.
- **Direction test of H₀: ρ = 0.**
  - t = r·√(n − 2)/√(1 − r²) with df = n − 2, two-sided p.
  - `direction` is `"positive"` or `"negative"` when p < 1 − confidence,
    and `"not_established"` otherwise.
- **Tail probabilities.** The two-sided t p-value is computed as the
  regularized incomplete beta I_z(df/2, 1/2), with z = df/(df + t²).
  - When `scipy.stats.t.sf` underflows, or `logsf` is not finite,
    `log10_p_value` comes from the convergent series
    I_z(a, b) = z^a(1 − z)^b/(a·B(a, b)) · [1 + Σ_{k≥0} B(a+1, k+1)/B(a+b, k+1)·z^(k+1)]
    (DLMF 8.17.22), evaluated in log space.
  - Reviewer check: this agrees with `betainc` to about 1e-15 where both
    are finite, and gives log10 p = −522.2739 for t = 100, df = 1000,
    matching base R, where `t.logsf` returns −inf.
  - It stops when a term falls below 1e-17 of the running sum, after at
    most 10,000 terms; otherwise the method refuses (`numerical_range`).
  - `p_value_underflow` is set as in count homogeneity. Negative infinity
    is never serialized.

**Refusals.** All are raised before a bundle is allocated:
- `inference_unavailable`: n < 3.
- `degenerate_inference`: 1 − r² or 1 − r_rf² ≤ 0 in floating point.
- `numerical_range`: any interval bound or statistic is not finite,
  including a lower bound that underflows to 0.

**Result.** `inference` contains:
- `confidence`;
- `magnitude_estimate` (|b|);
- `magnitude_interval` [low, high];
- `null_magnitude`;
- `magnitude_test`: `r_rf`, `t`, `df`, `p_value`, `p_value_underflow`,
  `log10_p_value`;
- `direction_test`: `r`, `t`, `df`, `p_value`, `p_value_underflow`,
  `log10_p_value`, `direction`;
- `model`: "independent pairs from a nonsingular bivariate normal on the
  analysed scale";
- `scope`: "Interval and test concern the magnitude σy/σx; direction is
  tested separately; no joint signed confidence set; intervals are
  marginal".

**Validator.** It recomputes every field from the saved pairs. This needs
no random numbers, so inspection binds the inference to the pairs.

**Limitations to add:**
- Exact only under the stated model.
- No measurement-error model.
- A p-value is not an effect size.
- Marginal statements only.

## B. Paired comparison (`rma_paired`, method version 1)

**Specification.**

```json
{"method": "rma_paired", "input": "...", "format": "past",
 "a": {"x": "Length_Caliper_mm", "y": "Width_Caliper_mm"},
 "b": {"x": "MajorAxisLength_AutoMorph_mm", "y": "MinorAxisLength_AutoMorph_mm"},
 "transform": "log10", "missing": "error",
 "bootstrap": {"replicates": 9999, "seed": 9112026, "confidence": 0.95}}
```

**Bounds.**
- `replicates` is a strict integer from 999 to 100,000.
- `seed` is a strict integer from 0 to 2⁶³ − 1.
- `confidence` lies strictly between 0 and 1.
- The cohort needs n ≥ 3 complete specimens.
- replicates × n ≤ 2,000,000 index entries, the PERMANOVA schedule budget.
  The limpet design needs 1,359,864. Above the limit the method refuses
  (`resource_limit`) before allocating.

**Columns and cohort.**
- Each fit resolves its own x and y with `core.resolve_columns`; within a
  fit, x and y must differ. Fits may share columns: one shared predictor,
  or a method compared with itself, are valid paired inputs.
- A specimen enters only if every referenced column is present.
  `missing: "drop_pairs"` excludes and lists incomplete specimens;
  `"error"` refuses them.

**Calculation.**
1. Fit A and B with the version-2 `rma_regression` on the identical cohort,
   without per-fit inference. Declare inference in separate `rma`
   analyses.
2. d = slope_B − slope_A, using signed slopes.
3. **Draws.**
   - Use `rng = Generator(PCG64(seed))`.
   - Draw `idx = rng.integers(0, n, size=(replicates, n), dtype=np.int64)`,
     in one call: row r is replicate r, and the upper bound is exclusive.
   - For each replicate, refit both slopes on rows `idx[r]`, keeping the
     pairing. Compute in chunks within the same budget.
4. **Undefined draws.** A replicate where either fit has zero variance or
   zero covariance is undefined.
   - If any replicate is undefined, the method refuses
     (`degenerate_bootstrap`), reporting the count and reason for each fit.
   - No draw is dropped or retried. Sample size does not rule this out;
     rounded duplicates make it likely.
   - A valid zero difference or zero SE (the identity control) is not
     degenerate.
5. **Interval.** The percentile interval of the replicate differences
   uses NumPy `quantile`, `method="linear"`, at (1 − confidence)/2 and
   (1 + confidence)/2. `standard_error` is the SD of the differences
   (ddof = 1).
6. **Monte Carlo endpoint bands.**
   - For each endpoint quantile q, take the 0.995 binomial band of order
     statistics, k_lo = binom.ppf(0.005, R, q) and
     k_hi = binom.ppf(0.995, R, q) + 1, clipped to [1, R].
   - Report [d₍k_lo₎, d₍k_hi₎] from the sorted differences (ties included).
     This is a 99% band for each endpoint of the infinite-replicate
     percentile interval.
   - `zero_excluded_resolved` is true when both bands lie strictly on the
     same side of 0. `zero_included_resolved` is true when the lower band
     lies entirely ≤ 0 and the upper band entirely ≥ 0. Otherwise the
     result is `"monte_carlo_unresolved"`.
   - This measures simulation error, not sampling coverage.
7. **Sign instability.** Count replicates in which slope_A or slope_B has
   the opposite sign to its observed fit. If either count is nonzero, warn
   (`bootstrap_sign_changes`): the signed statistic is discontinuous at
   zero covariance, and the percentile interval is unreliable across it.

**Result.**
- `fit_a` and `fit_b`, with the version-2 summary fields;
- `difference`;
- `bootstrap`:
  - replicates, seed, bit generator, NumPy version, dtype, confidence;
  - `interval`, `standard_error`, `endpoint_bands`, `resolution`;
  - `sign_changes` {a, b};
  - the replicate `slope_a`, `slope_b` and `difference` arrays;
- `pairs` (ID, raw and analysed values for each referenced column);
- `excluded`, `warnings`, `references`, `limitations`, and
  `scope: "approximate first-order percentile interval; marginal"`.

**Inspection and reproduction.**
- **Validator:**
  - recomputes both fits and `difference` from the saved pairs;
  - checks every saved difference equals `slope_b − slope_a` exactly;
  - recomputes `interval`, `standard_error`, the bands, `resolution` and
    `sign_changes` from the saved replicates;
  - binds seed, replicates, confidence and cohort to the specification,
    and the NumPy version to the environment.
- **What inspection does not establish:** that the replicates derive from
  the pairs and seed. Reproduction regenerates them and compares them.
  This is stated in the result scope.

**Limitations.**
- First-order approximate.
- Assumes independent, exchangeable specimens.
- Unreliable across sign changes.
- No measurement-error model.
- Does not identify the true measurement.
- Marginal intervals; no joint claims with Part A intervals.

## C. Small items

**C1. Study table columns.** These fields apply to `TableInput` with
`format: "delimited"` and `orientation: "samples_by_taxa"`.
- `id_column` is an exact, unique header name supplying the row labels.
  If omitted, the first column is used, as now.
- `columns` is a nonempty list of unique, exact header names, kept in the
  order given. It may not include the ID column.
  - If omitted, every column except the ID column is kept, in header order.
  - Unknown or duplicated names, or a header that is not unique, are
    refused (`unknown_column`, `duplicate_id`).
- Projection happens before values are interpreted, so dropped text
  columns never cause numeric refusals.
- Original IDs and source row order are preserved.
- The `read` record lists `id_column`, `columns` and the dropped columns.
- **Acceptance:** application 4's source CSV, read directly with
  `id_column: "ObjectID"` and the four measurement columns, derives a PAST
  table byte-identical to the current derivation, including column order.

**C2. Ranges.** RMA gains `x_raw_range` and `y_raw_range`: [min, max] of the
retained raw values, recomputed by the validator. `rma_paired` gives the
same for each referenced column. Ratios remain declared reporting
arithmetic.

## Study layer and interfaces

- `rma_paired` analyses `measurements` datasets.
- `row_filter_warnings` covers it, warning on filters that remove
  specimens complete in all referenced columns.
- Discovery, the CLI, MCP and the primer catalogue gain the new fields and
  method.
- `used-pairs.csv` is extended. `rma_paired` writes `paired-pairs.csv` and
  `bootstrap.csv` (replicate, slope_a, slope_b, difference). All are
  re-derived on inspection through `table_files`.
- Callers, schemas, tables, discovery and fixtures adopt the version-2
  shape. There is no legacy adapter.

## Acceptance

1. **Ordinary references** come from pinned R `smatr` (`sma(y ~ x,
   log = "xy", slope.test = k)`). Compare the absolute values of its
   interval to `magnitude_interval`, and its slope-test r and p to
   `magnitude_test`. Cases:
   - two Dielasma column pairs;
   - both limpet fits;
   - a negative-slope case;
   - n = 3.

   Agreement is required within 1e-10, with a provenance-pinned reference
   file.
2. **Tails** are checked against base R `pt(..., lower.tail = FALSE,
   log.p = TRUE)`, including a case where `scipy.stats.t.logsf` returns
   −inf. smatr's `1 − pf()` is not used for tails.
3. **Duality.** Setting `null_magnitude` to either interval endpoint gives
   p = 1 − confidence within 1e-10. A value inside the interval gives
   p > 1 − confidence; one outside gives p < 1 − confidence.
4. **Coverage** is checked by simulation with fixed seeds: nonsingular
   bivariate normal with σy/σx = 1, n = 20, 2,000 datasets each, at
   ρ ∈ {0.9, 0.3, 0.05, −0.05, −0.6}.
   - Magnitude-interval coverage lies within the binomial 99.9% band
     around 0.95 at every ρ, including those where the sample sign
     reverses.
   - Direction-test false-direction rates are reported per ρ.
5. **Paired bootstrap:**
   - deterministic replay;
   - an independent recomputation (regenerated NumPy index matrix,
     plain-Python refits);
   - the identity control (a = b): difference, SE and interval all 0;
   - the swap control: difference and interval negated, SE preserved;
   - the shared-predictor case;
   - a near-duplicate cohort refused with `degenerate_bootstrap`;
   - the budget refusal before allocation;
   - rehashed tampers of a replicate, the interval and a pair value, each
     with the affected tables refreshed, so the semantic checks are the
     ones exercised.
6. **C1 and C2:** as specified above.
7. **Application 4 amendment.** A recorded amendment, frozen before any
   computation:
   - both fits rerun with `inference: {confidence: 0.95, null_magnitude: 1}`;
   - one `rma_paired` analysis (calipers a, AutoMorph b) with 9,999
     replicates;
   - the original descriptive results preserved;
   - disclosure that reviewer-only single-fit intervals were seen at
     review (Board 3121), while the paired bootstrap result has not been
     computed;
   - intervals reported as marginal, with no joint claims.

## References

- Warton DI, Wright IJ, Falster DS, Westoby M (2006) Bivariate line-fitting
  methods for allometry. *Biological Reviews* 81:259–291.
  doi:10.1017/S1464793106007007
- Warton DI, Duursma RA, Falster DS, Taskinen S (2012) smatr 3: an R package
  for estimation and inference about allometric lines. *Methods in Ecology
  and Evolution* 3:257–259. doi:10.1111/j.2041-210X.2011.00153.x
- Pitman EJG (1939) A note on normal correlation. *Biometrika* 31:9–12.
  doi:10.1093/biomet/31.1-2.9
- Morgan WA (1939) A test for the significance of the difference between the
  two variances in a sample from a normal bivariate population. *Biometrika*
  31:13–19. doi:10.1093/biomet/31.1-2.13
- Efron B, Tibshirani RJ (1993) *An Introduction to the Bootstrap*. Chapman &
  Hall. ISBN 9780412042317
