# Lake Selina: amended report (dryland sum, candidate depth alignment)

Claude (Opus 5.5), 8 November 2026. This report supersedes the
interpretation in [report.md](report.md). That report's numbers still stand
for the archived 66-category definition. What changed, and why, is in
[AMENDMENT-1.md](AMENDMENT-1.md), committed at 9a2ee8f before this analysis
ran. It is driven by the paper (Colhoun et al. 1999) and by Codex's
[source review](COLHOUN1999-SOURCE-REVIEW.md). Codex's
[review of the amendment](AMENDMENT-1-REVIEW.md) reproduced the amended
results byte for byte and passed them; this version applies its four
wording corrections.

The numbers are in `results-amended.json` and `definition-sensitivity.json`.

Reproduce from the repository root:

```bash
uv run analyses/lake-selina/amend_source.py
uv run analyses/lake-selina/run_api.py design-amended.json
uv run analyses/lake-selina/analysis.py design-amended.json
uv run --with scipy analyses/lake-selina/compare_definitions.py
```

The toolkit primer is 0.2.0.dev0, SHA-256
`cdec09d1ab058224869120b2ac6de406be62df6ed112373dfa1057492971f765`.

## What changed

- **Denominator.** The analysis now uses a source-informed dryland
  definition: sedge and aquatic pollen are removed, following the paper's
  stated sum and Figure 6 groups. That leaves 60 categories, with m = 272.
  It is not an exact reconstruction of the printed sums.
- **Depths.** Archive depths are reported with a candidate paper depth
  (archive − 30 cm) beside them. The +30 cm candidate alignment is strongly
  supported by nine exactly matching printed pollen sums and by the zone
  boundaries. It does not establish every archived coordinate, or where
  the discrepancy arose.
- **No ages.** The archived chronologies list their radiocarbon controls
  at the paper's depths. Under the candidate alignment, those controls sit
  about 30 cm from the pollen samples that share their depth labels. Until
  that is reconciled, no level gets an age, and the three "named" pairs are
  only fixed sample-ID contrasts.
- **Withdrawn from report.md:**
  - "early forest recovery or old carbon": the candidate alignment removes
    the basis for that diagnosis;
  - the historical and climatic labels for the named pairs;
  - the agreement with Turney et al. near 41 ka.

## Aggregate results under the two definitions

The two definitions differ in both category membership and subsample size
(66 categories at m = 282; 60 at m = 272). This comparison cannot separate
the contributions of the two.

| Quantity | 66 categories (m = 282) | 60 dryland categories (m = 272) |
| --- | --- | --- |
| Adjacent steps rejected at Holm p < 0.05 (point estimate) | 41 of 71 | 41 of 71 |
| Monte Carlo diagnostic: Holm envelope wholly below / spanning / wholly above 0.05 | 41 / 1 / 29 | 40 / 4 / 27 |
| Median adjacent proportional Bray–Curtis | 0.206 | 0.203 |
| Rank agreement of the 71 step effects (Spearman) | — | 0.994 |
| Rank agreement of rarefied richness across 72 levels (Spearman) | — | 0.993 |
| Minimum coverage at m | 0.955 | 0.953 |

The frozen decision rule is the point estimate: Holm-adjusted plus-one p
below 0.05. The envelope is a sensitivity diagnostic for Monte Carlo
error, not a confidence statement and not a replacement rule.

**Steps that change classification.** Two steps cross 0.05:
- 345→350 cm moves from 0.054 to 0.033;
- 360→365 cm moves from 0.033 to 0.057.

**Unresolved by the diagnostic under the dryland sum:** 125→130, 185→190,
255→260 and 360→365 cm. Of these, 185→190 cm (Holm p 0.045) is also a
point-estimate rejection; the other three are not.

**Taxon attributions also shift.** At 155→160 cm, *Pherosphaera* passes
the global taxon Holm family only under the dryland sum (p = 0.023),
joining Poaceae and *N. gunnii*.

**The six largest steps are the same set under both definitions**
(`adjacent_steps[*].adjacent_rank_by_braycurtis`). Signs are forward in
time, that is, shallower minus deeper:

| Rank | Archive (paper) cm | Bray–Curtis | Taxa at Holm p < 0.05 |
| --- | --- | --- | --- |
| 1 | 155→160 (125→130) | 0.453 | Poaceae −0.25; *N. gunnii* +0.14; *Pherosphaera* +0.08 |
| 2 | 315→320 (285→290) | 0.398 | Asteraceae −0.16; *Phyllocladus* +0.14 |
| 3 | 275→280 (245→250) | 0.389 | Asteraceae +0.27 |
| 4 | 290→295 (260→265) | 0.376 | Apiaceae +0.16; *N. gunnii* −0.10; *Pherosphaera* +0.09 |
| 5 | 280→285 (250→255) | 0.365 | Asteraceae −0.17 |
| 6 | 150→155 (120→125) | 0.344 | *Pherosphaera* −0.09; *Phyllocladus* +0.07; *Microcachrys* −0.05 |

**Under the candidate alignment, the largest step adjoins the paper's dated
interval.** Archive 155→160 cm would be paper 125–130 cm: the top of the
paper's herb zone LS8, overlapping the 123–127 cm sample whose
14,200 ± 230 ¹⁴C yr BP date "dates the commencement of deposition of the
surface organic-rich mud". The step itself is not precisely dated. It is
the end of grass and herb dominance and the start of the subalpine and
rainforest expansion of zone LS9.

**Rarefied richness** at m = 272 (`levels[*].expected_richness_272`).
Medians, with ranges:

| Archive interval (cm) | Median E[S] | Range |
| --- | --- | --- |
| Upper forest, 80–140 | 21.9 | 19.9–30.9 |
| Transition, 145–155 | 27.2 | 23.1–27.8 |
| Herb interval, 160–295 | 21.4 | 14.8–28.4 |
| Peak herbfield, 165–190 | 16.4 | 14.8–17.5 |
| Lower forest, 300–427 | 25.2 | 17.8–30.3 |
| Basal *Lagarostrobos* forest, 395–427 | 18.7 | 17.8–21.8 |

The pattern from report.md holds. Richness is lowest at peak herbfield and
in the basal forest, and highest in mixed, transitional spectra. It is
richness of pollen categories, conditional on the retained table.

**Representation.** Relative and raw Bray–Curtis agree (r = 0.997). PCoA
axis 1 carries 54 % of the positive inertia, and the negative-to-positive
inertia ratio is 0.073, uncorrected.

## The three fixed sample-ID contrasts (no temporal labels)

| Pair (archive cm, paper cm) | Bray–Curtis, 66 → 60 categories | Holm p, 60 categories | Taxa at Holm p < 0.05, 60 categories |
| --- | --- | --- | --- |
| 531333 / 531341 (225/265; 195/235) | 0.196 → 0.197 | 0.0032 | none |
| 531310 / 531319 (145/190; 115/160) | 0.727 → 0.696 | 0.00077 | Poaceae, *Dichosciadium*-type Apiaceae, *Phyllocladus*, Asteraceae, *N. cunninghamii*, *Leptospermum*, *Spyridium* |
| 531321 / 531332 (100/120; 70/90) | 0.289 → 0.305 | 0.00077 | Asteraceae |

**Paper zones.**
- **531310 / 531319** spans the paper's zone LS9 into LS8 at paper
  115/160 cm: forest expansion set against herbfield. It is the
  deglacial-type change, wherever it falls in calendar time.
- **531333 / 531341** lies within the paper's zone LS7 (paper 170–235 cm).
  At archive 255–260 cm (paper 225–230 cm), *N. gunnii*, *Pherosphaera*
  and *N. cunninghamii* are elevated. Descriptively, this corresponds to
  the paper's "small peak in pollen of *Nothofagus* near the base of the
  zone". The statistical support is narrower:

  | Archive pair (cm) | Holm p | Diagnostic | Taxa passing the global taxon Holm family |
  | --- | --- | --- | --- |
  | 247→255 | 0.0013 | envelope below 0.05 | none |
  | 255→260 | 0.052 | unresolved (0.044–0.060) | none |
  | 260→265 | 0.00077 | envelope below 0.05 | *N. gunnii* |

  The episode is bounded by two resolved omnibus steps (247→255 and
  260→265 cm). Only *N. gunnii*, at the upper bound, is resolved as an
  individual taxon.

**Timing.** These depths lie near the paper's 230 cm date of
33,800 ± 1,100 ¹⁴C yr BP. The authors say this "could be older" and place it
in early isotope stage 3 by correlation. Whether they correspond to 45–38 ka
is unresolved, and no historical inference is drawn.

## The flagged level (531331, archive 220 cm, paper 190 cm)

The paper reports a strong *Lagarostrobos* peak at 190 cm. The archive level
has no *Lagarostrobos* entry, and its dryland total is 408, against a
printed sum of 480. In the archived counts, the two steps touching this
level are among the smallest in the record:
- 215→220 cm: 0.159, Holm p 0.25;
- 220→225 cm: 0.095, Holm p 1.0, the smallest of all 71.

If *Lagarostrobos* counts were missing from the archived level, both steps
would be understated. The 72-grain shortfall is consistent with that, but
it is not a recovered observation, so no counts are invented and nothing
here shows robustness to missing counts at this level. It is an
archive–paper discrepancy for the curators to reconcile, not something an
analysis can repair.

## Unsupported parts (additions to report.md)

| Subtask | Why the toolkit could not do it | What was used | Check |
| --- | --- | --- | --- |
| Reading the paper and aligning it with the archive | Outside the toolkit | Manual reading; candidate offset | Nine printed sums reproduced exactly; zone boundaries; Codex's independent reading |
| Removing the six sedge and aquatic columns | The study layer cannot delete taxa | `amend_source.py` | API validation; m = 272 confirmed |
| Comparing definitions | Reporting arithmetic | `compare_definitions.py` (SciPy Spearman) | Same 77 pairs and seed in both runs |

**A primer-rule lapse.** `amend_source.py` computes the column totals and
their minimum in its own Python to set m. The public rarefaction
validation resolves the same minimum with `sizes="minimum_total"`, so that
part was supported and should have used the API. The value agrees
(m = 272, confirmed by the validation receipt), so no number changes. The
script is left as committed because it is the pre-result record and its
hash is embedded in `results-amended.json`; a future regeneration should
take m from the validation receipt.

**Independent R cross-check of the amended table** (Codex, in
[the review](AMENDMENT-1-REVIEW.md)): 681 of 681 checks agree, maximum
absolute difference 6.2 × 10⁻¹³, receipt in
`amendment-1-review-checks.json`. It covers per-sample diversity,
rarefaction and coverage, the three distance matrices and the named-pair
Fisher tests. It does not independently test the omnibus Monte Carlo
algorithm.

## Toolkit

No defects. The amended runs verified on inspection. Codex reproduced
`results-amended.json` byte for byte from fresh API runs, and the original
results.json still replays byte for byte after the scripts were
parameterised.

## Where this leaves the research question

- **Stable under the two definitions:** the aggregate patterns and
  rankings. The number of point-estimate rejections, the ranking of step
  sizes, the set of six largest steps and the ranking of pollen-category
  richness barely change. Individual classifications and taxon
  attributions do change at the margin, as listed above. All of this is
  tied to depth and sample ID, under the source-informed dryland definition
  and the candidate depth alignment.
- **Not yet answerable from these archives:** anything temporal, including
  the 45–38 ka question. Answering it needs either:
  1. a reconciled sample-to-control depth alignment, then a rebuilt age
     model that weighs the paper's dating evidence under each method's
     validity limits. The reversed deeper radiocarbon assays and the
     grouped U-series estimate should not automatically become point
     controls; or
  2. the TAS1402 cores, with their own multi-method chronology (Fletcher et
     al.), which would be a new application.
- **What should happen next:**
  - **Ask the curators to reconcile the two discrepancies.** An unsent
    draft query to Neotoma and the IPPD is in
    [CURATOR-QUERY-DRAFT.md](CURATOR-QUERY-DRAFT.md). Sending it is
    outward-facing, so it waits for Barry.
  - **Then choose an age-model repair:** the depth provenance should be
    settled first. The repair is outside the toolkit's scope.

This tranche closes as a verified, conditional count-table analysis with
unresolved temporal provenance.
