# Lake Selina: final case-study report

Claude (Opus 5.5), 8 November 2026. This is the working end point of the
Lake Selina application. It uses the dryland pollen sum from
[amendment 1](AMENDMENT-1.md) and the inferred repairs from
[amendment 2](AMENDMENT-2.md). Barry's direction, 8 November 2026: the case
study exists "to service development of the tool", so data issues are
"infer[red] or interpolate[d]" and the analysis presses on.

The record of the earlier stages stays in [report.md](report.md) and
[report-amended.md](report-amended.md). The numbers are in
`results-final.json`.

**Status: a worked example on a reconstructed record.** The ages come from
a simple inferred model, and one count is imputed. The results are fit for
demonstrating and testing the toolkit. They are not a revision of the
published record.

## The questions and the answers

**1. Where do successive spectra differ beyond counting noise, and which
taxa carry the change?**
- 45 of 71 adjacent steps are rejected at Holm p < 0.05 (point estimate).
  The Monte Carlo diagnostic puts 43 envelopes wholly below 0.05, 3
  spanning it (125→130, 255→260 and 360→365 cm) and 25 wholly above.
- The six largest steps, by proportional Bray–Curtis:

| Rank | Archive cm | Inferred cal BP | Bray–Curtis | Taxa at taxon Holm p < 0.05 (forward change) |
| --- | --- | --- | --- | --- |
| 1 | 155→160 | 17,130 / 18,079 | 0.453 | Poaceae −0.25; *N. gunnii* +0.14; *Pherosphaera* +0.08 |
| 2 | 315→320 | 49,717 / 50,776 | 0.398 | Asteraceae −0.16; *Phyllocladus* +0.14 |
| 3 | 275→280 | 41,240 / 42,299 | 0.389 | Asteraceae +0.27 |
| 4 | 290→295 | 44,419 / 45,478 | 0.376 | *Dichosciadium*-type Apiaceae +0.15; *N. gunnii* −0.10; *Pherosphaera* +0.09 |
| 5 | 280→285 | 42,299 / 43,359 | 0.365 | Asteraceae −0.17 |
| 6 | 150→155 | 16,445 / 17,130 | 0.344 | *Pherosphaera* −0.09; *Phyllocladus* +0.07; *Microcachrys* −0.05 |

- The largest step is the end of the last-glacial grass and herb dominance
  at about 17–18 ka. Peak herbfield, with the lowest rarefied richness
  (E[S] 14.8–17.5 at m = 272), falls at about 19–23 ka. That matches the
  regional deglacial timing, which is a useful check on the inferred
  chronology.

**2. How does rarefied pollen-category richness vary?** Richness is lowest
in the peak herbfield and in the basal *Lagarostrobos* forest (archive
395–427 cm, E[S] 17.8–21.8), and highest in mixed and transitional spectra
(up to 30.9). Minimum coverage at m is 0.953.

**3. Secondary: 45 to 38 ka.** The bracket rule selects 531339 (archive
255 cm, 36,913 cal BP) and 531347 (295 cm, 45,478 cal BP).
- **The endpoint contrast is modest but resolved:** Bray–Curtis 0.259, Holm
  p 0.00076. Only *Pherosphaera* passes taxon Holm, at +0.09 toward the
  younger end.
- **The interval is volatile, not directional.** Six of the eight adjacent
  steps inside it are rejected. Three of them are among the six largest in
  the whole record: 275→280, 280→285 and 290→295 cm, all between about 41
  and 45 ka, driven mainly by Asteraceae swinging up and back down. The
  largest internal step (0.389) exceeds the endpoint contrast.
- **On the IPPD-1 control ages,** the young endpoint moves to 245 cm and
  the contrast rises to 0.395, with *N. gunnii* (−0.11), *Dichosciadium*-type
  Apiaceae (+0.09) and *Melaleuca* (−0.06). The qualitative reading is the
  same: large herb oscillations within 41–45 ka and a moderate net
  difference across the window.

**Benchmarks.**
- **8–15 ka** (85→140 cm): Bray–Curtis 0.577, the largest named contrast,
  led by *Phyllocladus* (−0.31). Both chronologies select the same pair.
- **21–28 ka:** the primary pair (175/220 cm) has 531331, the imputed level,
  as its old endpoint. Its *Lagarostrobos* term (−0.15) is the imputation
  itself. The alternative pair (165/195 cm) avoids that level: Bray–Curtis
  0.189, Poaceae +0.14.

## What the repairs changed

- **The imputed level.** It turns its two steps from the smallest in the
  record into ordinary ones: 215→220 cm goes from 0.159 to 0.252, and
  220→225 cm from 0.095 to 0.204. Both are now rejected, carried by
  *Lagarostrobos*.
- **Holm family effects.** 125→130 and 255→260 cm cross from Holm p 0.052
  to 0.049. Their raw p-values are identical, because the random streams
  are unchanged. The testing family changed in two ways:
  - the two imputation-adjacent raw p-values fell;
  - the reselected endpoints replaced all six earlier extra pairs with five
    new ones (omnibus family 77 → 76; taxon family 2,350 → 2,324).

  Together these lower the two steps' step-down multipliers. Both remain
  unresolved under the diagnostic.
- **Everything else:** among adjacent pairs, only 215→220 and 220→225 cm
  change raw p-values, and the top six steps are the same. 51 adjacent
  ranks shift as the two affected effects move through the ranking.

**Checks and their reach.** The R cross-checks (agreement about
6 × 10⁻¹³) cover the original and amendment-1 tables, not the final imputed
table. The regional timing agreement is a plausibility check within the
assumed reconstruction, not an independent validation of the chronology.
The interpolated younger and older age curves are working annotations, not
propagated age-model confidence intervals.

## Toolkit: what this case study taught

The case study ran end to end through the API. It found no numerical
defects: the R cross-checks agree to about 6 × 10⁻¹³, and every results
file replays byte for byte. It did expose gaps, all at the boundary between
the toolkit and a real palynological workflow:

| # | Gap | What we did instead | Suggested toolkit change |
| --- | --- | --- | --- |
| 1 | No way to drop taxa (columns). Pollen-sum definitions that exclude aquatics, sedges and spores are routine in palynology. | `amend_source.py` wrote a filtered table | A `study` `exclude_taxa` operation with a reason and provenance, mirroring row `exclude` |
| 2 | The Monte Carlo sensitivity envelope (Holm over the Clopper–Pearson bounds) is postprocessing we wrote twice | `analysis.py` reimplements Holm | Report per-pair Holm envelopes and a `monte_carlo_unresolved_after_holm` flag in `count_homogeneity` |
| 3 | 71 adjacent pairs had to be spelled out | Generated in scripts | Accept `pairs: "adjacent"` (in table order) plus explicit extras |
| 4 | Turning bundles into a per-pair table (forward sign, distances from three community runs, ranks) took about 160 lines of glue | `analysis.py` | A tidy per-pair export from `count_homogeneity`, with an optional sign convention |
| 5 | `compare_community_runs` reports `baseline_link_verified: false` unless `baseline_run` is passed | Noted | Make the primer say so, or infer the link when both runs share an input hash |
| 6 | No count-correction operation. A justified correction (the imputed 72 grains) had to edit the table | `amend_final.py` | Probably keep it outside the toolkit; the primer forbids coercion. Leave as is |
| 7 | Holm results depend on which long-interval pairs join the family | Reported | Document it in the primer next to the family rules |

Gaps 1–3 recur in any stratigraphic count analysis and are cheap to add. I
recommend them as the next development tranche, each with its method
contract in `docs/` and tests.

## Unsupported parts (this amendment)

| Subtask | Why | What was used |
| --- | --- | --- |
| Imputing one count | No toolkit operation; not a supported correction | `amend_final.py`, declared in AMENDMENT-2.md |
| Age model | Outside the toolkit's scope | Linear interpolation in `amend_final.py` |
| Endpoint reselection by age window | Intake glue | The stage-1 `bracket` rule, reused |

m = 272 now comes from the API's `minimum_total` receipt.
