# Dielasma: isometry and locality differences

All numbers below are in `results.json`, written by `analysis.py` (seed fixed; bootstrap 2000, permutation 4999). Units are not stated in the source, so I treat them as arbitrary. They cancel out of log-log slopes and W/L ratios.

## Answer
1. **Length against width is close to isometric in L1 and L2, and probably in L3.**
   - Log-log RMA slopes of width on length:

     | Locality | RMA slope | Bootstrap 95% CI |
     |---|---|---|
     | L1 | 1.018 | 0.990–1.050 |
     | L2 | 0.982 | 0.952–1.015 |
     | L3 | 1.107 | 1.008–1.286 |
     | Pooled | 1.019 | 0.998–1.043 |

   - r² is 0.98 (L1), 0.99 (L2) and 0.89 (L3).
   - L1, L2 and the pooled sample have CIs containing 1.
   - L3's RMA CI just excludes 1. Its OLS slope is 1.045 (95% CI 0.92–1.17, p=0.48 against 1), and with n=35 and the lowest r, RMA slope estimates are the least stable.
   - I read L3 as weak, inconclusive evidence for slight positive allometry, not as a finding.
   - Slopes do not differ detectably among localities (ANCOVA slope homogeneity F=1.70, p=0.18).
   - No quadratic curvature is detectable (the L1 quadratic term has p=0.057, the others p>0.3).
   - Isometry here means a constant W/L ratio of about 0.80–0.85. Any deviation from it is small (a slope within about ±0.05 of 1 in the two large samples).

2. **The localities differ clearly in size structure, and only weakly in shape.**
   - Length differs strongly (Kruskal-Wallis p=9.6e-7).
   - Mean length is 14.2 in L1, 11.9 in L2 and 8.1 in L3. L3 has no shells longer than 11.5, while L1 and L2 reach 25 and 24.4.
   - Pairwise length tests with Bonferroni correction (×3):
     - L1–L3: Mann-Whitney p=4e-7.
     - L2–L3: Mann-Whitney p=0.033 and KS p=4e-4.
     - L1–L2: Mann-Whitney p=0.014, but KS p=0.051.
   - L1 and L2 are multimodal. A cluster at 6–10 is present in both, and L1 has a second mode at 18–20 (see `length_hist`).
     - BIC favours two Gaussians over one for log length in L1 and L2 (95.8 vs 133.5, and 82.2 vs 111.3).
     - BIC favours one Gaussian in L3 (13.8 vs 18.8).
   - Shape, measured by the W/L ratio, is borderline: Kruskal-Wallis p=0.031. Mean W/L is 0.839 in L1, 0.846 in L2 and 0.804 in L3. Only L2–L3 survives the pairwise correction (p=0.029).
   - The ANCOVA intercept (the allometric "elevation") differs (p=0.0008), driven by L3 (L1–L3 p=0.023; L2–L3 p=0.0002). L1 and L2 are indistinguishable (p=0.42).
   - A permutation MANOVA-style test on log length and log width gives F=20.1, p=0.0002. This is dominated by size.
   - L3 shells are somewhat narrower for their length, but L3 is also the small-size sample with the weakest fit. Part of this could come from an ontogenetic effect or from a slight allometry (slope above 1) combined with its different size range. The data cannot separate these.

## Choices and why
- **Log-log RMA (reduced major axis) as the primary slope.** Both variables are measured with error and neither is a predictor. OLS is given alongside as a check, and the two agree on the conclusion except for L3's CI.
- **Bootstrap CIs.** Used for the RMA slope because there is no simple exact interval.
- **Nonparametric tests for size.** Length distributions are multimodal and non-normal.
- **Specimens are analysed as paired X1/X2 within a locality.** Row position across localities means nothing, as the provenance note states.

## Data issue found
- The L2 column contains repeated (length, width) pairs, including consecutive blocks. Rows 58–63 are repeated at rows 65–70, for example 6.98/5.78, 7.50/6.00, 7.36/5.98 and 7.10/5.92. Another repeat is 15.00/13.52 at rows 59 and 66.
- This looks like a possible duplicated data-entry block. Some repeats could arise by chance from rounding, and L3 also has 3 repeated pairs.
- Sensitivity check with repeated pairs removed (L2 n=71):
  - The RMA slope is 0.977 (CI 0.946–1.010), still consistent with isometry.
  - The OLS slope CI is just below 1 (0.940–0.998, p=0.036), so a slight negative allometry in L2 cannot be excluded.
  - The ANCOVA and Kruskal-Wallis conclusions are unchanged.
  - The raw-data conclusions therefore hold, but the duplicates should be checked against the original source.

## What the data cannot establish
- **Populations.** These are single samples from unknown collecting procedures, and sampling bias is possible (for example selection of whole conjoined shells, or size-sorting by collectors). Differences in size structure may reflect taphonomy, such as transport and winnowing of juveniles, rather than the living populations. No ages were recorded, so size is not age. Multimodality hints at cohorts, but this cannot be proved without growth lines.
- **Growth.** The cross-sectional pooled allometry is a static allometry. It is not an ontogenetic trajectory unless the samples are of one cohort-mixed population. Only length and width are measured, so thickness and other shape dimensions are not covered.
- **Environment.** The localities' ecological and stratigraphic positions are not recorded, so the data do not support any inference linking size or shape to environment. L3's small, unimodal size range is compatible with a younger cohort, a stunted population, size-sorting or a small sample (n=35), and these cannot be told apart.
- **Taxonomy.** Nothing here tests species identity. Near-identical allometry and overlapping W/L ratios do not show conspecificity, and the small shape differences do not show separate species. Diagnostic characters (internal structures, loop, beak) were not measured. Species identity of the localities is assumed, not tested.
- **Statistics.** Individuals within a locality are treated as independent. Units are unstated. The multiple tests were not corrected beyond pairwise Bonferroni, so the borderline shape result (p≈0.03) should be read cautiously.
