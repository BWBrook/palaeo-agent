# Sprint 13 contract: RMA inference and paired method comparison

Claude (Opus 5.5), 9 November 2026. Draft for Codex review before
implementation. It comes from application 4 (fossil limpets,
[REPORT](../analyses/fossil-limpets/REPORT.md),
[toolkit gaps](../analyses/fossil-limpets/toolkit-gaps.json)). Application 4
is the acceptance test.

## Why

On the same 136 shells, application 4 found log–log RMA exponents of 1.081
with calipers and 0.934 with AutoMorph. The toolkit cannot say whether
either value departs from isometry, or whether they differ from each other.
A reviewer's check outside the toolkit gives approximate 95% slope intervals
of 0.99–1.18 and 0.85–1.03. Both include 1, so the descriptive contrast
"on opposite sides of 1" carries no inferential weight. An allometry user
needs exactly these numbers, and needs them from the API, with provenance.

## Scope

| Part | Delivers | Method |
| --- | --- | --- |
| A | Slope confidence interval and a test against a declared slope, for one RMA fit | Exact under bivariate normality on the analysed scale (Warton et al. 2006; Pitman 1939) |
| B | Paired comparison of two RMA fits on the same specimens | Specimen bootstrap of the slope difference, seeded, with replicates saved |
| C1 | Study tables that declare their ID column and data columns | Study-layer reading only |
| C2 | Raw x and y ranges in RMA results | Recorded from the used pairs |

**Out of scope:** intercept (elevation) intervals; tests of common slope or
elevation across independent groups (Warton & Weber 2002 likelihood-ratio
test, a candidate for a later sprint); measurement-error models; OLS and
major-axis fits.

## A. Inference for one RMA fit (`rma` method version 2)

**Specification.** `RmaSpec` gains an optional field:

```json
"inference": {"confidence": 0.95, "null_slope": 1}
```

- `confidence` lies strictly between 0 and 1. `null_slope` is a finite,
  nonzero real number on the analysed scale; isometry on log10 axes is 1.
- When `inference` is absent, the result field is null, and the fit is
  exactly as in version 1.

**Calculation.** On the analysed (transformed) pairs, with n retained pairs,
sample correlation r and RMA slope b:

- **Interval.** Let B = (1 − r²) · F(confidence; 1, n − 2) / (n − 2). The
  interval is b(√(B+1) − √B) to b(√(B+1) + √B), ordered from low to high,
  which matters when b < 0. This is the inversion of the test below
  (Warton et al. 2006).
- **Test of H₀: β = β₀**, with β₀ = `null_slope`.
  - Compute r_rf = cor(y − β₀x, y + β₀x), and t = r_rf √(n − 2) / √(1 − r_rf²)
    with df = n − 2.
  - The two-sided p-value is computed from the t distribution.
  - Record `p_value_underflow` as in count homogeneity, with a
    `log10_p_value` from the log survival function when the p-value
    underflows.

**Refusals.**
- `inference_unavailable` when n < 3.
- `degenerate_inference` when 1 − r² ≤ 0 or 1 − r_rf² ≤ 0 in floating
  point.

Both are raised before any bundle is allocated.

**Result.** `inference` contains:
- `confidence`;
- `slope_interval` [low, high];
- `null_slope`;
- `r_rf`, `t`, `df`, `p_value`, `p_value_underflow`, `log10_p_value`;
- `assumptions`: "independent specimens; bivariate normal variation on the
  analysed scale".

The validator recomputes every field from the saved pairs. This is cheap
and needs no random numbers, so inspection binds the inference to the
saved pairs, following the clean-up audit's principle.

**Limitations to add:**
- The interval and test are exact only under bivariate normality on the
  analysed scale.
- They do not model measurement error.
- A p-value is not an effect size; report the interval.

## B. Paired comparison (`rma_paired`, method version 1)

This is a new method for two measurement definitions applied to the same
specimens.

**Specification.**

```json
{"method": "rma_paired", "input": "...", "format": "past",
 "a": {"x": "Length_Caliper_mm", "y": "Width_Caliper_mm"},
 "b": {"x": "MajorAxisLength_AutoMorph_mm", "y": "MinorAxisLength_AutoMorph_mm"},
 "transform": "log10", "missing": "error",
 "bootstrap": {"replicates": 9999, "seed": 9112026, "confidence": 0.95}}
```

**Cohort.**
- The four columns must be distinct; columns are resolved with
  `core.resolve_columns`.
- A specimen enters only if all four values are present. With
  `missing: "drop_pairs"`, incomplete specimens are excluded and listed;
  with `"error"`, they are refused.

**Calculation.**
1. Fit A and B with the version-2 `rma_regression` on the identical cohort.
   No per-fit inference is computed here; declare it in separate `rma`
   analyses.
2. Difference: d = slope_B − slope_A.
3. Bootstrap. Use `Generator(PCG64(seed))` and
   `integers(0, n, size=(replicates, n))`. Draw rows in order. For each
   replicate, recompute both slopes from the resampled specimens, keeping
   their pairing, and take their difference.
4. If any replicate has zero variance or zero covariance in either fit, the
   method refuses (`degenerate_bootstrap`) and reports the count. With
   continuous measurements and n ≥ 10 this should not occur; a refusal is
   preferable to silently changing the statistic.
5. Interval: the percentile interval of the replicate differences at
   `confidence`, using NumPy's `quantile` with method `"linear"` (Hyndman–Fan
   type 7). Also report the bootstrap standard error (SD of the replicate
   differences, ddof = 1).

**Result.**
- `fit_a` and `fit_b`, each with the version-2 RMA summary fields;
- `difference`;
- `bootstrap`: replicates, seed, bit generator, NumPy version, confidence,
  `interval`, `standard_error`, and the replicate `slope_a`, `slope_b` and
  `difference` arrays;
- the shared `pairs` (specimen ID, the four raw values and the four
  analysed values);
- `excluded`, `warnings`, `references` and `limitations`.

**Inspection and reproduction.**
- **Validator:**
  - recomputes both fits and `difference` from the saved pairs;
  - recomputes `interval` and `standard_error` from the saved replicate
    differences;
  - checks that each saved difference equals `slope_b − slope_a` exactly;
  - binds the NumPy version to the environment, as count homogeneity does.
- **Reproduction** regenerates the replicates from the seed and compares
  them.
- **Why not save the indices:** 9,999 × 136 indices would make a
  multi-megabyte bundle, so they are not saved. The replicate statistics
  (3 × 9,999 floats) are saved instead.

**Limitations.**
- The percentile bootstrap is first-order accurate.
- Specimens are assumed independent and exchangeable.
- The endpoints carry Monte Carlo error at the declared number of
  replicates.
- This is a paired comparison of two measurement definitions; it does not
  say which one is correct.

## C. Small items

**C1. Study table columns.** `TableInput` gains two optional fields, valid
only with `format: "delimited"` and `orientation: "samples_by_taxa"`.
- `id_column` names the header column that supplies row labels. The
  default stays the first column.
- `columns` lists the data columns to keep, in order. The ID column may not
  be among them, and any column not listed is dropped.
- The `read` record lists both declarations and the dropped columns.
- Application 4's `intake.py` would then reduce to hashing the source.

**C2. Ranges.** RMA results gain `x_raw_range` and `y_raw_range` ([min, max]
over the used pairs), and the validator recomputes them. `rma_paired`
records them for all four columns.

## Study layer and interfaces

- `rma_paired` analyses `measurements` datasets, as `rma` does.
- `row_filter_warnings` covers it: a filter that removes specimens complete
  in all four columns is warned.
- Discovery, the CLI, the MCP server and the primer catalogue gain the new
  method and fields.
- The tables are `used-pairs.csv` (extended), and for `rma_paired`
  `bootstrap.csv` (replicate, slope_a, slope_b, difference). Both are
  re-derived on inspection through `table_files`.

## Acceptance

1. **Reference values from R `smatr`.** `sma(y ~ x, log = "xy",
   slope.test = β₀)`, using its `conf.int` and `slopetest` outputs, on at
   least these cases:
   - two Dielasma column pairs;
   - both limpet fits;
   - a negative-slope case;
   - n = 3.

   Agreement within 1e-10, with a provenance-pinned reference file, as for
   vegan.
2. **Duality.** Setting `null_slope` to either interval endpoint gives
   p = 1 − confidence, within 1e-10.
3. **Coverage.** For simulated bivariate-normal data with known β and a
   fixed seed (n = 20, 2,000 datasets), the 95% interval's coverage lies
   within the binomial 99.9% band around 0.95.
4. **Paired bootstrap.**
   - Deterministic replay.
   - An independent recomputation regenerates the index matrix with NumPy,
     then recomputes both slopes for every replicate in plain Python
     arithmetic.
   - Tamper tests: rehash after editing a replicate difference, the
     interval, or a pair value.
5. **C1 and C2.** Application 4's source CSV runs directly through a study
   with `id_column: "ObjectID"` and the four columns. The derived dataset
   equals the current `measurements.tsv` derivation byte for byte.
6. **Application 4 amendment.** This is a recorded amendment with its own
   design note, made before computing:
   - both fits rerun with `inference: {confidence: 0.95, null_slope: 1}`;
   - one `rma_paired` analysis, calipers (a) against AutoMorph (b), with
     9,999 replicates;
   - the report revised from API fields.

## References

- Warton DI, Wright IJ, Falster DS, Westoby M (2006) Bivariate line-fitting
  methods for allometry. *Biological Reviews* 81:259–291.
  doi:10.1017/S1464793106007007
- Warton DI, Duursma RA, Falster DS, Taskinen S (2012) smatr 3: an R package
  for estimation and inference about allometric lines. *Methods in Ecology
  and Evolution* 3:257–259. doi:10.1111/j.2041-210X.2011.00153.x
- Pitman EJG (1939) A note on normal correlation. *Biometrika* 31:9–12.
  doi:10.1093/biomet/31.1-2.9
- Efron B, Tibshirani RJ (1993) *An Introduction to the Bootstrap*. Chapman &
  Hall. ISBN 9780412042317
