# Sprint 10 and application 2 review

Codex (`gpt-6.1-sol`), 8 November 2026. Reviewed implementation `239b209`
and application `5b8874f`. Production code, tests and application outputs
are unchanged by this review.

**Original disposition: the percentage workflow and worked example pass.
One numerical-range repair remains before accepting the general abundance
input path.**

**Closed at `7dfe07b`:** the sprint-11 review confirms all three range
repairs and accepts the abundance path. The original counterexamples below
remain as the review record; see [the confirmation](sprint-11-review.md).

## Labels and method version

Accept the branch-specific names. `retained_counts` and specimen `total`
accurately describe count input; `retained_values` and `weight_sum`
accurately describe abundance input. Preserve those names. The input type
discriminator, branch validation and implementation fingerprint make the
extension explicit. Retaining method version 1 is reasonable here: the
distance, diversity and PERMANOVA definitions have not changed. No forced
renaming of count outputs is requested.

## P2: numerical-range handling is incomplete

Three reproducible cases need focused guards/regressions:

1. **Pairwise overflow can return a false zero distance.** At
   `src/palaeo_agent/community.py:468`, the raw Bray–Curtis denominator
   adds weights directly. With abundance rows below, every cell and row
   sum is finite, but the x/y denominator overflows:

   | Sample | A | B |
   | --- | --- | --- |
   | x | 1e308 | 0 |
   | y | 1e308 | 1e307 |
   | z | 0 | 1 |

   Public `validate`, `run` and `inspect_run`, with raw Bray–Curtis and
   one ordination dimension, accept this table. The reported x/y distance
   is **0**, and the bundle inspects as verified. The distance should be
   **1/21 = 0.047619047619047616**. Dividing the entire table by 1e308
   gives that value through the same API. Compute the ratio stably or
   refuse an unsupported arithmetic range; never silently return zero.
   Apply the same care to the pairwise row-sum imbalance ratio in
   `sensitivity.py:125`.

2. **The native Python route silently loses positive values.** At
   `community.py:328–332`, a positive `Real` whose float64 conversion is
   zero still passes. This public call succeeds:

   ```python
   from fractions import Fraction
   import palaeo_agent as pa

   pa.analyse_community(
       [[Fraction(1, 10**400), 1, 0], [1, 0, 0], [0, 1, 1]],
       sample_ids=["A", "B", "C"], taxon_ids=["x", "y", "z"],
       value_type="abundance", transform="none", distance="jaccard",
       dimensions=1, empty_samples="error")
   ```

   It changes the positive fraction to zero, reports richness 1 instead
   of 2 for A, and A/B Jaccard 1 instead of 0.5. The file route correctly
   refuses `1e-400`. Apply that positive-to-zero refusal consistently to
   native input before constructing the float64 matrix.

3. **Row overflow escapes the named refusal.** At `community.py:346`,
   a row `[1e308, 1e308]` raises an uncaught `OverflowError` from
   `math.fsum`; it does not reach the intended `abundance_range` check.
   Translate this into the documented structured error in both validation
   and execution.

These cases do not affect the supplied pollen weights. Fix them without
changing ordinary count arithmetic. Tests should cover file/native entry
points, stable common-factor behaviour or explicit refusal, and structured
row-total errors.

## Verification completed

- Full suite: **717 passed, 11 skipped**, with the process-list access
  needed by the pilot cleanup test. Optional native confinement tests were
  not enabled.
- Independent R 4.6.1 / vegan 2.7.6: **492/492 fields agree**, maximum
  absolute difference **1.78e-15**, with atol = rtol = 1e-10. This covers
  raw/closed Bray–Curtis, binary Jaccard, richness, Shannon, Simpson,
  weight/count sums and PERMANOVA F/R² across percentage, proportion,
  row-scaled and count-smoke fixtures. It does not independently check
  permutation p-values or establish ecological validity.
- All 24 reference run bundles inspect as verified. Expected negative
  eigenvalue warnings occur in 22 runs and remain uncorrected.
- Live MCP SDK/stdio checks pass for schemas, fractional community and
  PERMANOVA runs, explicit closure, honest branch fields, exact decimal
  study merging, exclusion, metadata joins, reproduction, count-only
  refusals and study/value-type binding.
- Application intake regenerates `percent.tsv`, `samples.csv` and
  `study.json` byte-identically. Every one of the 61 × 92 source-table
  cells matches the saved archive or declared zero-fill. Selection and
  note-derived altitude assignments yield the stated 25 samples, 11/14
  bands. Fresh API study execution and postprocessing reproduce the entire
  `results.json` byte-identically; study inspection verifies.

The full primer and current catalogue were read: version 0.2.0.dev0,
SHA-256 `f45b76b868bd1c317bb0c803935784bb9040a9d3f763ee8dc5cec7952d661e7b`.
Supported calculations used the API. Source parsing/replay checks and
adversarial fixtures are review tasks; R is the permitted independent
arithmetic reference. The review did not revisit source-paper provenance.

## Application interpretation

Accept application 2 as the declared, conditional worked example. Its
reported quantities and descriptive contrasts match the saved outputs.
Two small reporting improvements can accompany the guard fix:

- Restrict the final ecological reading to **these 25 selected records
  under the working conventions**, rather than generalising the weak
  altitude separation across Tasmanian surface spectra.
- Add the primer's **How checked** column to the unsupported-parts table.
  Record source hash/regeneration for intake, verified API fields for group
  summaries, and the calculation behind the quoted Monte Carlo interval.

The quoted interval is reasonable at its reported precision: 687/9,999
exceedances give a 95% exact binomial interval of
**0.0638249554–0.0738417566** for the conditional randomisation tail
probability. The reported plus-one p remains 0.0688. This interval is
unsupported review arithmetic using SciPy's
[exact proportion interval](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html),
not an interval for the realised plus-one estimate or ecological uncertainty.

## Next tranche

Agree with the proposed order after repairing the range guards:

1. **PERMANOVA Monte Carlo uncertainty.** The current schedule samples
   independent permutations with replacement. Add the same exact-tail
   binomial interval and a recorded-alpha unresolved diagnostic, without
   changing the statistic, schedule, seed, B or plus-one p. Exact
   enumeration has no Monte Carlo uncertainty: mark the interval
   inapplicable. Cover b = 0/B, a threshold case and rehashed semantic
   tampering; validate against an independent reference. No automatic
   extra permutations or new significance rule.
2. **A saved-Neotoma-download adapter, specified first.** Limit the first
   version to the frozen download format used by these examples. Preserve
   dataset/sample/taxon IDs, source labels, units, metadata, source hashes
   and declared filters. Make zero-fill and units/kind handling explicit;
   refuse ambiguous collisions or mixed units rather than inventing counts.
   Keep sample selection, altitude overrides, taxon harmonisation,
   denominator choices and imputation declared by the caller. Do not infer
   a surface horizon from the depth field or treat PI metadata as an analyst.
   Live retrieval, authentication and a general ecological-data workflow
   are outside this first adapter.

Evidence is archived under
[`references/independent/2026-11-08-sprint10/`](../references/independent/2026-11-08-sprint10/checks.json).
Recompute the R reference from the repository root:

```bash
Rscript --vanilla references/independent/2026-11-08-sprint10/reference.R \
  references/independent/2026-11-08-sprint10
```
