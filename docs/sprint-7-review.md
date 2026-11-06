# Sprint 7: scientific code review and corrected-analysis cross-check

Claude (Opus 5.5), 6 November 2026. Reviews Codex's implementation
(ab28a7a, 21241fe) against the
[rarefaction](rarefaction-contract.md) and
[count-homogeneity](count-homogeneity-contract.md) contracts, then
cross-checks the corrected Llanvirn and Dielasma analyses against the API
with matched inputs. Agreement here is an arithmetic check. It does not
establish that either analysis's design or interpretation is right.

## Verdict

No calculation or inference defect in either operation. The contracts are
implemented as written, including Codex's two corrections (coverage as a
population estimate at both branches; stable products instead of log-gamma
subtraction). Two pre-existing study-layer hazards bear directly on the
sprint-8 Dielasma session (I2); both are fixed or documented below, before
the freeze.

## Rarefaction (`src/palaeo_agent/rarefaction.py`)

- **Absence probabilities.** `_absence(n, x, m)` computes
  C(n − x, m)/C(n, m) as a product over min(x, m) factors, using the
  identity C(n − x, m)/C(n, m) = C(n − m, x)/C(n, x). Both branches are
  correct; 50-digit Decimal keeps the covariance cancellation exact enough
  for the accepted range.
- **Expectation and variance.** Hurlbert's sum and the presence-indicator
  variance Σq(1 − q) + 2Σ(q_ij − q_i q_j), with q_ij from the pooled count
  x_i + x_j. Pair terms are summed in sorted-label order. The negative
  variance clamp uses 64ε·E², as contracted.
- **Coverage.** m < n uses `_absence(n − 1, x − 1, m)` =
  C(n − x, m)/C(n − 1, m), which is the iNEXT `Chat.Ind` interpolation term.
  The m = n branch evaluates f₁ = 0 first, then the f₂ = 0 and f₂ > 0
  forms of A. The all-singleton and single-taxon shortcuts (0 and 1) equal
  the formula's value.
- **Boundaries.** E = min(m, S) and Var = 0 exactly at m ∈ {1, n} and
  S ∈ {1, n}; n = 1 gives null coverage with its reason. The saved-result
  validator rederives f₁, f₂, full coverage and the boundary flag, and
  bounds Var by Popoviciu's (min(m, S) − 1)²/4.
- **Resource refusals** are explicit and named. They are implementation
  bounds, as the results report says.

## Count homogeneity (`src/palaeo_agent/count_homogeneity.py`)

- **Table and statistic.** Taxa absent from both samples are removed and
  listed. E = row × column / total, X² without continuity correction; the
  simulated statistic uses the same expected cells.
- **Monte Carlo.** `random_table(pooled, totals).rvs(..., method="patefield")`
  on one PCG64 stream per declared pair from `SeedSequence(seed).spawn`,
  inclusive tail at (1 − 64ε)·X²_obs (R's `almost.1`), p = (b + 1)/(B + 1).
  Chunking at 256 is deterministic given the stream.
- **Clopper–Pearson** bounds are Beta(0.025; b, B − b + 1) and
  Beta(0.975; b + 1, B − b), with 0 and 1 at the ends; the unresolved flag
  is interval ∋ 0.05, scoped to the raw tail.
- **Multiplicity.** Omnibus Holm over pairs; one Holm family over every
  pair × taxon Fisher test. `_holm` matches R `p.adjust` (cumulative maximum,
  capped at 1). `joint_control: false` is recorded.
- **Effects and limits.** Signed effect b − a; Bray–Curtis on proportions;
  zero limits 1 − (1 − conf)^(1/n) via `expm1`/`log1p`, with taxa that are
  zero in that sample and present anywhere in the prepared input.
- **Saved-result validation** recomputes every deterministic field, the
  Fisher p-values and both Holm families; only b is taken on trust, which
  `reproduce` covers.

## Primer and delivery

The packaged primer carries Barry's rule verbatim, and Python, CLI and MCP
return the same body with version and SHA-256. The MCP `instructions`
preface is self-contained in its first 512 characters. I did not rerun the
client-qualification matrix; that is part of the sprint-8 freeze.

## Fixes made in this review

1. **`run_study` into an existing directory** raised a raw
   `FileExistsError`, while `run` creates a fresh subdirectory under its
   root. An agent following the primer's `run_study(study, output_root)`
   hint would hit that. It now refuses with `output_exists`, and the primer
   table says the argument is the new bundle directory. Regression test in
   `tests/test_study.py`.
2. **Row exclusion in wide measurement tables.** In `dielasma.dat` the three
   localities sit side by side, so row 64 of L1 and row 64 of L2 are
   different specimens. A study that excludes the L2 duplicate block
   (rows 64–70) silently drops seven L1 specimens if L1 is analysed from
   the same dataset (n 103 → 96, no warning). This is the I2 case. The
   primer (§3) and `docs/study.md` now say that `exclude` removes whole
   rows and that such exclusions need a dataset of their own. A
   column-scoped exclusion or a study warning would be the stronger fix;
   I have left that design choice to Codex.

Both change the primer's SHA-256, so the sprint-7 delivery receipt now
describes an earlier primer; the sprint-8 freeze requalifies delivery.

## Cross-check of the corrected analyses

`uv run python analyses/cross-check/cross_check.py` writes
[`analyses/cross-check/receipt.json`](../analyses/cross-check/receipt.json),
which replays byte for byte (bundles go to a temporary directory; no run IDs
are recorded). It follows primer §7: `validate` on the same inputs (no
warnings for Llanvirn), operations run and read back through
`run`/`inspect_run` and, for Dielasma, `run_study` with declared
exclusions, then a field-by-field comparison.

**159 of 159 matched quantities agree.**

| Case | Quantities | Rule |
| --- | --- | --- |
| Llanvirn | totals, richness, rarefaction size | exact |
| Llanvirn | Shannon; inverse Simpson as 1/(1 − Gini–Simpson) | relative 1e-12 |
| Llanvirn | proportional Bray–Curtis for the nine adjacent steps, from both `count_homogeneity` and `community` | relative 1e-12 |
| Llanvirn | counts and Fisher p for every taxon in steps 5–6 and 6–7 | exact; relative 1e-10 |
| Llanvirn | the analysis's 2,000-draw mean rarefied richness against the exact E[S₁₃] | 3.29 Monte Carlo SE of the mean |
| Dielasma | n, SMA slope, intercept and r on log10 scale, L1–L3 as archived and L2 under both corrected scenarios | exact; relative 1e-12 |

One Monte Carlo comparison sits near its bound: horizon 8's simulated mean
is 5.950 against the exact 5.8772 (z = 2.87). A 400,000-draw simulation
gives 5.8767 ± 0.0018 and exact rational arithmetic gives 5.877219, so the
API value is right and the analysis's figure is an ordinary Monte Carlo
excursion. The report's rounded range (horizons 7–10: 4.2–6.0) is
unaffected.

**Not matched, by design** (listed in the receipt with reasons): the
analysis's unconditional multinomial Bray–Curtis null against the
conditional Pearson test; per-pair against global taxon Holm families;
subsample quantiles, rarefied Sørensen, counting-error bootstraps and other
representations; and the Dielasma SMA intervals, slope tests, common-slope
and elevation tests, which no operation computes (`rma` is descriptive).

Side by side, the two homogeneity procedures agree on the large steps
(3–4, 4–5, 5–6 and 6–7 at or near their p floors) and differ at 8–9:
multinomial Bray–Curtis p = 0.015 against conditional Pearson p = 0.109
(B = 9,999). They differ in both null and statistic, so the difference is
not attributable to either alone, as the contract says.

## Ready for sprint 8

Nothing here blocks the freeze. I propose Codex checks the two fixes above
(and decides whether row exclusion needs a column-scoped form or a warning
before the freeze), then I freeze the sprint-8 runtime, requalify delivery
and run I1 and I2 as agreed.
