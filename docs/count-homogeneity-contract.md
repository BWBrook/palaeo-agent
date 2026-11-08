# Count-homogeneity contract (sprint 7)

Claude (Opus 5.5), 3 November 2026. Written from primary sources before any
implementation, for Codex's review. It settles the sampling model, Monte
Carlo convention, multiplicity families and zero-count limits that Codex's
[critique](sprints-7-8-critique.md) asked for.

## Question and sampling model

For each **declared** pair of samples, the operation asks whether the two
taxon compositions differ by more than counting noise alone would produce,
and in which taxa.

**Model.**
- Each sample is an independent multinomial draw of its observed total from
  a taxon-probability vector.
- Under the null hypothesis, the two samples share one vector.
- The test conditions on both sample totals and the pooled taxon totals.
  Under that null, every allocation of the pooled specimens to the two
  samples with those totals is equally likely. The contingency tables
  themselves are *not* equally likely; each carries its multivariate
  hypergeometric probability.

**What the model assumes and does not test.**
- Counting units within each collection are independent categorical
  observations with a common probability vector. Positive clustering or
  taphonomic aggregation can make the test anticonservative; validity
  depends on this counting model, not exchangeability alone.
- The test concerns counting error only. It says nothing about variation
  between replicate collections, ecological exchangeability between
  horizons, cause, time or rate.
- The within-sample counting assumption and any claim that two horizons are
  ecologically exchangeable are separate matters, and the result says so.

## Specification

| Field | Values |
| --- | --- |
| `method` | `"count_homogeneity"` |
| input fields | as `community` |
| `pairs` | list of distinct `[sample_a, sample_b]`, with a ≠ b; order is recorded and defines the signed taxon effect (b minus a) |
| `pairs: "adjacent"`, `extra_pairs` | sprint 9: consecutive retained samples, then explicit extras; see [sprint-9-contracts.md](sprint-9-contracts.md) |
| `simulations` | integer B, 999 ≤ B ≤ 99,999; no default, so the caller fixes it before seeing results |
| `seed` | strict integer, required, 0 ≤ seed ≤ 2³² − 1 |
| `confidence` | for zero-count limits; default 0.95 |

Settings are not coerced from Boolean values, strings or fractional
integers. Confidence is finite and strictly between 0 and 1. Pairs are a
nonempty list of exact, distinct string IDs. Pooled margins are summed in
exact integer arithmetic; backend numerical/resource limits are checked
explicitly before sampling. The seed bound is exactly representable through
the JSON client boundary.

Pearson X², proportional Bray–Curtis and exact two-sided Fisher p-values
are symmetric under swapping the pair. The signed taxon effects reverse;
finite Monte Carlo draws need not be identical after reordering margins.

## Calculations, for each pair

1. **Table.** The taxa × 2 table of counts. Taxa with zero in *both*
   samples are removed from the calculation, and their labels are listed as
   `taxa_absent_from_pair`.
   - Refused: either sample total is 0; fewer than 2 taxa remain;
     non-integer or negative cells.
2. **Statistic.** The Pearson statistic X² = Σ (O − E)² / E with
   E = row total × column total / grand total, with no continuity
   correction.
3. **Conditional Monte Carlo p-value.**
   - B tables are drawn with fixed margins by
     `scipy.stats.random_table(row, col).rvs(B, method="patefield")`
     (Patefield 1981). The method is named so that SciPy's automatic method
     choice cannot change replay.
   - Each pair has its own random stream, from
     `numpy.random.SeedSequence(seed).spawn(len(pairs))` taken in declared
     pair order.
   - The tail is inclusive, with R's tolerance: a simulated table counts as
     an exceedance when X²_sim ≥ (1 − 64 ε) · X²_obs, with ε the float64
     machine epsilon.
   - The p-value is p = (b + 1)/(B + 1), where b is the number of
     exceedances.
4. **Monte Carlo uncertainty.**
   - The result reports b, B and p.
   - It also reports a two-sided 95% Clopper–Pearson interval for the unknown
     conditional tail probability, estimated by b/B. This interval is never zero-width: at
     b = 0 its upper end is 1 − 0.025^(1/B).
   - The fixed `reporting_alpha` is 0.05. `monte_carlo_unresolved` is true
     exactly when that interval contains 0.05, including its endpoints;
     its scope is `unadjusted_tail_only`. A false flag means only that the
     raw-tail interval excludes 0.05. It does not establish stability near a
     Holm threshold. The interval is neither for the adjusted p-value nor
     simultaneous across pairs. There is no automatic re-run with a larger B.
   - Results replay exactly under the same seed, B, input order and
     SciPy/NumPy versions, and the result records those versions. A
     different input order or library version gives a different Monte Carlo
     draw of the same p-value.
5. **Effect size.** Bray–Curtis on proportions, reported beside the test and
   never as the test.

## Multiplicity: two families, labelled separately

| Family | Members | Adjustment | What it controls |
| --- | --- | --- | --- |
| Omnibus | one test per declared pair | Holm, across all declared pairs | the family-wise error rate over the pair tests, including pairs that share a sample |
| Taxon | one Fisher test per (pair, taxon) for each taxon present in either sample of that pair | **one Holm family across every pair × taxon test in the call** | the family-wise error rate over all taxon claims in the call |

- **The taxon family is fixed by the declaration.** It is never selected by
  omnibus significance.
- **The two families do not jointly guarantee a single 5% error rate over
  every omnibus and taxon claim.** The result states this, and so does any
  report built on it.
- **Fisher tests.** Each test uses the 2 × 2 table [[x_a, n_a − x_a],
  [x_b, n_b − x_b]] with `scipy.stats.fisher_exact`, two-sided.
  - SciPy's two-sided convention sums the probabilities of tables with
    probability ≤ p_obs · (1 + 10⁻¹⁴). R's `fisher.test` uses a 1 + 10⁻⁷
    relative tolerance.
  - The reference check therefore requires agreement within 1e-10 except at
    tables whose probabilities tie within 10⁻⁷. Those are listed and
    examined, not silently accepted.
- **Holm.** As R `p.adjust(method = "holm")`: cumulative maximum of
  (k − i + 1) · p₍ᵢ₎, capped at 1.

## Zero-count upper limits

For each sample in a declared pair, the result gives the one-sided upper
confidence limit on the proportion of any taxon with zero count there:

U = 1 − (1 − confidence)^(1/n).

This is the exact Clopper–Pearson one-sided bound for 0 of n, as R
`binom.test(0, n, alternative = "less")`. It is reported once per sample,
with its confidence level and denominator n, together with the list of
taxa that are zero there and present elsewhere in the input. The taxa list
is drawn from the input's full taxon list after declared preparation.

These limits are marginal and pointwise. They are not simultaneous across
taxa or samples, and a zero count is not evidence of absence.

## Refusals

- Undeclared pairs; duplicate pairs (including reversed duplicates); a ≠ b
  violated; unknown sample IDs.
- Empty samples in any declared pair.
- Fewer than 2 taxa present in a pair.
- B outside its bounds, or a missing seed.
- Any input refusal of `community`.

## Reference checks

- **Exact statistics.** X² and the expected cells must match R
  `chisq.test(t, correct = FALSE)` within relative 1e-12.
- **Monte Carlo p-value.** R `chisq.test(t, simulate.p.value = TRUE, B = B)`
  is an independent Monte Carlo estimate. It agrees when the two
  exceedance proportions are compatible under their binomial sampling
  error. Decimal equality is not expected.
- **Enumerated tables.** For a tiny table (for example (2, 1, 0) against
  (0, 1, 2)), the exact conditional tail probability is computed by
  enumerating every table with those margins, with hypergeometric weights.
  A fixed-seed sampler check uses a prespecified binomial-error tolerance;
  a pointwise 95% interval is not guaranteed to cover the exact probability
  on every run.
- **Fisher, Holm and zero limits:** R `fisher.test`, `p.adjust` and
  `binom.test`, under the tolerances above.
- **Tests:** pairs sharing a sample, a taxon zero in both samples, a single
  shared taxon (refused), extreme imbalance (n = 13 against 702), reversed
  pair order, and taxon-order invariance of every non-Monte Carlo output.

## Coed Duon, for orientation

These are scratch values to orient review, not acceptance targets. With
4,999 tables, before Holm:
- **5–6:** p = 0.0002, the plus-one floor for that B.
- **6–7:** p = 0.0004.
- **1–2, 2–3, 7–8, 9–10:** p = 0.14–0.82.
- **8–9:** p = 0.11.

The corrected analysis's multinomial-null Bray–Curtis test gave an
unadjusted p of 0.015 for 8–9. That calculation differs in both its null
(unconditional on taxon totals) and its statistic, so the difference cannot
be attributed to either change alone.

## References

- Patefield, W.M. (1981). An efficient method of generating random R × C
  tables with given row and column totals. *Applied Statistics* 30, 91–97.
- Agresti, A. (2002). *Categorical Data Analysis*, 2nd edn. Wiley
  (conditional and exact tests for contingency tables, including Fisher's
  test).
- Holm, S. (1979). A simple sequentially rejective multiple test procedure.
  *Scandinavian Journal of Statistics* 6, 65–70.
- Clopper, C.J. & Pearson, E.S. (1934). The use of confidence or fiducial
  limits illustrated in the case of the binomial. *Biometrika* 26, 404–413.
- Phipson, B. & Smyth, G.K. (2010). Permutation p-values should never be
  zero. *Statistical Applications in Genetics and Molecular Biology* 9, 39
  (the plus-one p-value).
