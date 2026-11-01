# Coed Duon assemblage change (Upper Llanvirn), horizons 1–10

All values come from `results.json`, written by `analysis.py` (seed fixed, ~2000 multinomial resamples per test). The `_N_` label prefixes are undocumented, so I did not use them.

## Answer

- **Horizons 1–5:** the fauna is dominated by *Sowerbyella*. Its share is 0.95, 0.93, 0.95, 0.74 and 0.89 (`prop_Sowerbyella`). Adjacent Bray–Curtis (BC) on proportions is 0.04 for 1–2 and 2–3, 0.21 for 3–4 and 0.18 for 4–5 (`bray_curtis.proportion`).
- **5→6 is the largest compositional shift in the section** (BC 0.67; bootstrap 95% CI 0.64–0.71).
  - *Sowerbyella* falls from 0.89 to 0.27.
  - *Basilicus* (`Basil`) rises from 3 of 473 specimens (0.006) to 330 of 702 (0.47).
  - Several rarer taxa also rise: `crino`, `praso`, `Dalma`, `Rbryo`.
  - Total count rises from 473 to 702, and richness from 14 to 15.
  - Each of these changes is far outside what sampling noise alone produces. Under a pooled-composition null the 95th percentile of BC is 0.09, and p ≈ 0.0005 (`null_homogeneity.5-6`).
- **6→7 is also large** (BC 0.56; CI 0.52–0.65), but it spans the unconformity and horizon 7 has only 26 specimens.
  - *Basilicus* is absent at horizon 7 (0 of 26).
  - *Sowerbyella* is 0.46, so it is not restored to its pre-6 level of about 0.9.
  - The observed BC exceeds the null (median 0.20, 95th percentile 0.30), so it is not just small-sample noise.
  - The sample is small, though. The CI is wide and the horizon-7 profile rests on a few specimens (`Dalma` 4, `Sower` 12).
- **Horizons 7–10** are low-count (n = 26, 68, 57, 13) and mutually indistinguishable or only weakly distinguishable. Adjacent BC is 0.21–0.30, and p is 0.69, 0.015 and 0.43 for 7–8, 8–9 and 9–10. The Ashes and Lavas fauna is more even than horizons 1–5 (inverse Simpson 2.3–4.7, against 1.1–1.8).

## Robustness to counting totals and to the representation of abundance

Totals range from 13 to 702, a 54-fold spread.

- **Richness tracks sample size.** Raw richness correlates with total count (Spearman 0.59). Rarefied to n = 13 (the smallest total, `rarefy_n`), richness is 1.6–2.3 for horizons 1–3 and 5, and 3.6 at horizon 4. It is 4.7 at horizon 6 and 4.2–6.0 for horizons 7–10. The 7–10 values are slightly more uncertain than the others because those samples are small. So the raw richness peak at horizons 5–6 is partly a sampling effect, but the rise in rarefied richness and evenness from 5 to 6 is real. It is the dominance of *Sowerbyella* breaking down.
- **Representations compared** (`bray_curtis`): proportions, square-root proportions, presence/absence, log(count+1), and proportions with *Sowerbyella* removed.
  - Under proportions, sqrt and log, 5–6 and 6–7 are both among the largest steps. Under log(count+1) 6–7 is larger than 5–6 (0.65 against 0.46); under proportions and sqrt, 5–6 is larger.
  - So **the claim "5–6 is larger than 6–7" depends on representation.** Only "both are large" is robust.
  - With *Sowerbyella* removed, the remaining fauna changes strongly at both steps (0.69 and 0.74). Neither step is just a *Sowerbyella* artefact. The 6–7 figure rests on only 14 non-*Sowerbyella* specimens at horizon 7, and the 5–6 figure on 48 at horizon 5, so both are imprecise (`rest_fauna_*`, which excludes both *Sowerbyella* and *Basilicus* and gives 0.59 and 0.41).
  - **Presence/absence shows no unusual step.** BC is 0.31 for 5–6 and 0.39 for 6–7, within the range of other steps (0.08–0.47) and with wide bootstrap CIs. The 5→6 change is therefore one of **relative abundance, not taxon membership**: nearly all taxa at horizon 6 are already present at horizon 5. By contrast, 6→7 shows a modest turnover signal in presence (`Basil`, `Talin`, `Salop` lost; `Glypt` gained). That is weak, because absences in n = 26 are expected by chance for rare taxa.
- **Taxon-level tests** (Fisher exact, Bonferroni over 23 taxa). 5→6: `Basil`, `Sower`, `crino`, `praso`, `Talin` and `Dalma` remain significant. 6→7: only `Basil` survives (p_bonf ≈ 3e-6). The other 6→7 "significant" taxa (`Sower`, `Dalma`, `Glypt`, `Hespe`) do not survive correction, so horizon 7 offers no taxon-level evidence beyond the loss of *Basilicus*.

## Interpretations that remain supported

- A strong abundance reorganisation at horizon 6, centred on a *Basilicus*-rich assemblage with *Sowerbyella* much reduced. Supported by every abundance-based metric.
- Horizons 7–10 are compositionally distinct from horizons 1–5 (PCoA axis 1 on sqrt-BC separates 6–10 from 1–5, explaining 58% of variance). Horizon 4 is intermediate (−0.10) and horizon 9 is partly intermediate (0.12).
- A faunal change across the unconformity: horizon 7 differs from 6 by more than sampling noise, mainly through the loss of *Basilicus*.

## Not supported, or not establishable

- That horizon 6 is a sampling-total artefact. It is the largest sample (702), but the shift is far beyond the multinomial null and larger than any other. However, a large sample does not prove a representative one.
- Gradual versus abrupt change. There are no thicknesses, dates or spacings, so the number of horizons does not translate into time or rate. The 6–7 step spans an unconformity of unknown duration, so it cannot be read as a rate or as an event.
- Ecological cause (environmental change, facies, volcanic influence in the Ashes and Lavas, or taphonomy). The data cannot separate these. The change in lithostratigraphic unit across 6–7 is confounded with the faunal change.
- Whether the *Basilicus* dominance reflects living abundance or counting practice. Counting was not documented. Disarticulated trilobite sclerites (cranidia, pygidia, librigenae) can inflate trilobite counts relative to brachiopods, which would exaggerate the horizon-6 spike. Counts are not separated into articulated and disarticulated material.
- Sampling effort per horizon (volume, area, collecting time) and replicates are not recorded. The counts are therefore not densities, and within-horizon variation is unknown. The bootstrap treats each horizon as a single multinomial draw from a homogeneous population. It captures counting error only, so the CIs are optimistic.
- Horizons 7 and 10 (n = 26 and 13) and 8–9 are too small for reliable taxon-level conclusions, and the rare-taxon turnover signal there is indistinguishable from chance.

## Choices

BC dissimilarity is used throughout because it is bounded and sensitive to relative abundance. Several representations are shown rather than one "correct" one. Wilson intervals on the key taxa (`wilson_Sower`, `wilson_Basil`) are given in `results.json`. Rarefaction is analytic (hypergeometric), at n = 13 and n = 50. No samples or taxa were dropped. No multiple-testing correction is applied to the adjacent BC tests, but 3–4, 4–5, 5–6 and 6–7 have p ≈ 0.0005 (the minimum possible with 2000 resamples), which survives correction for 9 tests. 8–9 (p = 0.015) does not survive it, and 1–2, 2–3, 7–8 and 9–10 are not significant.
