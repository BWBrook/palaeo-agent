# Dielasma: isometry, shape and size structure at three localities

Corrected derivative of authentic session A2 (Sonnet 5.5, 1 November 2026),
written by Claude (Opus 5.5) on 2 November 2026. It answers the same brief
from the same data: `benchmarks/past/legacy-data/dielasma.dat`, Ford
Formation, Sunderland, via the PAST case studies.

The corrections address every finding of Codex's independent review
(`evaluation/authentic/run-records/authentic-20261101/review-codex.json`).
Every number below comes from `results.json`, which
`uv run analyses/dielasma/analysis.py` writes (seed 20261102). Keys are given
in backticks, and values without a scenario label are for `as_archived`.

## Brief

Is shell growth isometric or allometric in length against width, and do the
three localities differ in shell shape or size structure? What can these
samples establish about the populations, their environments and their
taxonomy?

## The data defect, and how it is carried through

The archived L2 columns repeat a block. Specimens 57–63 recur exactly as
specimens 64–70: seven consecutive length/width pairs (`data_integrity.L2`).
Specimen 71 repeats the pair 7.00/6.00 a third time. L3 repeats three pairs,
but in no consecutive block, which is consistent with rounding to 0.5. L1 has
no repeats.

Whether the block is a data-entry duplicate cannot be settled from the file,
so **every inference is computed under three scenarios** (`scenarios`):

| Scenario | L2 n | What it assumes |
| --- | ---: | --- |
| `as_archived` | 79 | the file is right |
| `block_removed` | 72 | specimens 64–70 duplicate 57–63 |
| `unique_pairs` | 71 | every repeated L2 pair is a duplicate (also drops 71) |

L1 (n = 103) and L3 (n = 35) are the same in all three. The archived bytes are
unchanged. The source, Hollingworth & Pettigrew (1988), should be checked
before anyone chooses a scenario.

## Answer

### 1. Allometry

Growth of width against length is close to isometric. No locality shows
allometry that survives the estimator and scenario checks.

Standardised major axis (SMA = RMA) slopes of log width on log length
(`sma_log10_width_on_length`):

| Locality | SMA slope | Exact 95% CI | p (slope = 1) | Bootstrap 95% CI | OLS slope, CI |
| --- | ---: | --- | ---: | --- | --- |
| L1 | 1.018 | 0.989–1.048 | 0.21 | 0.988–1.052 | 1.007, 0.978–1.037 |
| L2 as archived | 0.982 | 0.955–1.009 | 0.19 | 0.953–1.015 | 0.975, 0.948–1.002 |
| L2 block removed | 0.976 | 0.949–1.005 | 0.11 | 0.944–1.011 | 0.969, 0.941–0.997 |
| L3 | 1.107 | 0.986–1.244 | 0.085 | 1.009–1.292 | 1.045, 0.916–1.174 |

The exact interval and the slope = 1 test (correlation of y − x with y + x)
are the standard SMA methods (Warton et al. 2006). They assume bivariate
normality on the log scale.

- **L1 and L2 are consistent with isometry** under every scenario and
  estimator. One exception: the L2 OLS slope falls just short of 1 after
  deduplication (CI to 0.997 or 0.998). OLS is not the appropriate line here,
  because both measurements carry error and neither is a predictor, and the
  SMA interval includes 1.
- **L3 is unresolved, not "probably isometric".** Its SMA slope is the
  largest (1.107). The percentile bootstrap excludes 1 and the exact interval
  includes it, and the slope = 1 test gives p = 0.085. With n = 35, the
  weakest correlation (r = 0.944) and the narrowest size range, the evidence
  for positive allometry in L3 is weak and depends on the interval method.
- **No curvature detected.** The quadratic term has p = 0.057 (L1), 0.65
  (L2) and 0.37 (L3) (`quadratic_term_p`). This does not establish
  linearity, and L1 is borderline.

**Do the slopes differ?** This is the SMA common-slope likelihood-ratio test
(Warton & Weber 2002), calibrated three ways (`common_slope`); A2 tested OLS
slopes instead. The calibrations are:
- the χ² asymptotic;
- a Gaussian parametric bootstrap, which imposes the common slope while
  keeping each locality's correlation and length scale;
- a pairs bootstrap, which centres each locality, rescales log width to the
  common slope and resamples the observed pairs. This keeps the empirical
  distribution shapes, and it matters because log length is far from normal:
  Shapiro–Wilk p = 2e-6 (L1), 4e-5 to 3e-4 (L2) and 0.03 (L3)
  (`shapiro_log_length_p`).

| Scenario | Common slope (bootstrap CI) | LR | p (χ²₂) | p (Gaussian bootstrap) | p (pairs bootstrap) |
| --- | --- | ---: | ---: | ---: | ---: |
| As archived | 1.002 (0.980–1.025) | 6.55 | 0.038 | 0.051 | 0.071 |
| Block removed | 1.000 (0.978–1.023) | 7.50 | 0.024 | 0.025 | 0.057 |
| Unique pairs | 1.001 (0.977–1.023) | 7.40 | 0.025 | 0.027 | 0.046 |

Bootstrap p-values use 1,999 replicates, so their Monte Carlo standard error
is about 0.005.

- The evidence that the three slopes differ is **tentative**: p = 0.024–0.071,
  depending on the scenario and the calibration. It is weakest under the
  calibration that does not assume normality.
- No pair differs after Bonferroni correction (`common_slope_pairwise`: all
  p_Bonferroni ≥ 0.10). The heterogeneity is diffuse: L2 sits slightly below
  1, L1 slightly above, and L3 above both.
- The common slope is indistinguishable from 1.
- Read together: near-isometry overall, with small differences among
  localities (slopes within about ±0.1 of 1) that these samples cannot
  attribute to any one site.

### 2. Size structure

The localities differ clearly in size structure (`length`, `length_pairwise`).

- Mean length is 14.2 at L1 and 11.9 at L2 (12.3 without the block). At L3 it
  is 8.1, and no L3 shell exceeds 11.5, against maxima of 25.0 (L1) and 24.4
  (L2).
- Kruskal–Wallis p ≤ 1.5e-6 in every scenario.
- Pairwise (Bonferroni over three pairs):
  - L1–L3 and L2–L3 differ in every scenario and by both Mann–Whitney and KS
    (p_Bonferroni ≤ 0.034).
  - **L1–L2 does not survive deduplication.** Mann–Whitney p_Bonferroni is
    0.014 as archived, 0.055 with the block removed and 0.072 with unique
    pairs. KS gives 0.051, 0.16 and 0.22. **A2's claim that the conclusions
    were unchanged by deduplication was wrong for this comparison.**
- **Modes** (`log_length_mixture`, `length_histogram`):
  - L1 and L2 are bimodal. A two-Gaussian mixture on log length beats one
    Gaussian by 21–38 BIC units in every scenario. The fitted density has
    peaks near 7.2–7.4 and 16.9–17.2 length units; the component medians
    are 7.4–7.7 and 17.5–17.7.
  - L3 is better described by one Gaussian: BIC 13.8 against 17.9 for the
    best two-component fit from 48 EM starts.
  - Histogram bins are two recorded units wide, starting at 2. Units are not
    stated in the source.
  - The duplicated block falls in the small mode, so it inflates the 6–8
    class at L2 (28 specimens as archived, 23 with the block removed).

### 3. Shape

Shape differs only modestly (`width_length_ratio`, `elevation_*`).

- Mean width/length is 0.839 (L1), 0.846 (L2) and 0.804 (L3).
  Kruskal–Wallis p = 0.031–0.034.
- Only L2–L3 differs after Bonferroni correction (p = 0.029–0.033). L1–L3 has
  p_Bonferroni = 0.083 and L1–L2 1.0.
- SMA elevation at the common slope gives the same picture:
  - L3 shells are narrower for their length. Welch ANOVA p = 0.014–0.015.
  - L2–L3 p_Bonferroni = 0.013–0.014.
  - L1–L3 is 0.050–0.056 (borderline).
  - L1–L2 is 0.88–0.95.
- Because the common-slope test is itself borderline, and L3 occupies a
  different, smaller size range, the L3 elevation difference cannot be
  separated from a slightly steeper L3 slope. "L3 is narrower" and "L3 has
  slight positive allometry over a smaller size range" describe the same
  observations.

## What these samples cannot establish

- **Populations and growth.**
  - Each locality is one collection, of unknown method. Selecting complete
    articulated shells, collector size-sorting, and transport or winnowing of
    small shells could each shape the size distributions.
  - Size is not age, and no growth lines were measured, so the modes are
    candidate cohorts, not demonstrated ones.
  - The slopes are static (cross-sectional) allometry, not individual growth
    trajectories.
- **Environment.** The positions of the localities within the reef are not
  recorded. L3's small, unimodal size range fits a younger cohort, stunting,
  size-sorting or chance in a sample of 35, and nothing here distinguishes
  them.
- **Taxonomy.**
  - Two measurements cannot test species or subspecies identity. Near-equal
    allometry does not show conspecificity, and a modest L3 shape difference
    does not show a separate taxon.
  - Outside knowledge, not in the provided materials: terebratulide
    taxonomy usually rests on internal characters (for example the loop and
    cardinalia) and on beak and foramen features, none of which were
    measured.
- **Statistics.**
  - Specimens within a locality are treated as independent.
  - The exact SMA interval assumes bivariate normality; the bootstrap does
    not, and the two disagree for L3.
  - The elevation tests take the estimated common slope as fixed.
  - Units are not stated. They cancel from log-log slopes and ratios.

## Changes from A2, in response to the independent review

| Review finding | Correction |
| --- | --- |
| "Probably isometric in L3" conflicted with its own RMA interval | L3 is reported as unresolved, with the exact SMA interval and test alongside the bootstrap |
| The slope-homogeneity test compared OLS slopes while RMA slopes were reported | The SMA common-slope LR test (Warton & Weber 2002) is used, with χ², Gaussian and pairs-bootstrap calibration. It finds tentative heterogeneity (p = 0.024–0.071), where A2's OLS test gave p = 0.18 |
| Pairwise ANCOVA p-values were unadjusted | All pairwise tests are Bonferroni-adjusted over three pairs |
| The deduplication check missed the change in the L1–L2 length difference | Every inference runs under three scenarios; L1–L2 length is reported as not robust |
| "No simple exact RMA interval" | The exact SMA interval is reported |
| The ANCOVA and permutation test were not calibrated for unequal scatter | Welch tests for elevation; residual SDs reported (`residual_sd_log10`); the size-dominated multivariate permutation test is dropped |
| Diagnostic characters were asserted without flagging them | Labelled as outside knowledge |
| Duplicate rows were not traceable in `results.json` | `data_integrity` lists the repeated pairs and the recurring block by specimen number |
| Second review (Codex, 2 November 2026): rounding slips; heterogeneity calibrated under normality only; mixture modes mislabelled and L3 fitted from one start; one L3 specimen outside the histogram bins; "no curvature" overstated | Corrected values; pairs-bootstrap calibration and Shapiro–Wilk tests added; 48 EM starts, with component medians and fitted density modes reported separately; bins start at 2; "no curvature detected" |
