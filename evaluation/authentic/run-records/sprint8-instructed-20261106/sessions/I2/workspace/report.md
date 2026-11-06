# Dielasma: length–width allometry and locality comparison

Toolkit primer 0.2.0.dev0, SHA-256 `47cab28432d1202fad35223999983b4921b4d2721503f8d9e876799faed913d3`. Every number below is in `results.json`, written by `analysis.py` (seed 20240611, 10,000 bootstrap resamples). Toolkit bundle IDs are in `provenance_manifest.json`. They are also listed here: log10 RMA runs L1 `b81bc3ee…`, L2 `00690a10…`, L3 `750e5c7e…`. Raw-scale sensitivity runs: L1 `062ab4df…`, L2 `c6054f6e…`, L3 `31ce54312…`.

## Answer

**Allometry.** Growth is close to isometric in L1 and L2, and possibly weakly positively allometric in L3 (width growing faster than length). The log–log RMA slope of width on length is as follows (bundle `rma_<L>_log10`, field `slope`; the CI is the bootstrap 95% interval from my own code):

| Locality | n | slope | bootstrap 95% CI | r |
|---|---|---|---|---|
| L1 | 103 | 1.018 | 0.989–1.048 | 0.989 |
| L2 | 79 | 0.982 | 0.952–1.016 | 0.993 |
| L3 | 35 | 1.107 | 1.009–1.286 | 0.944 |

- The L1 and L2 intervals contain 1, so they are consistent with isometry.
- The L3 interval excludes 1 only narrowly. That sample is small and covers a narrow size range (length 3.5–11.5), so the slope is imprecise. I would call it suggestive and not established.
- Slopes on raw (untransformed) scales are 0.84, 0.82 and 0.91. They are below 1 only because the intercept is not zero. They are not evidence of allometry, and only the log–log slope bears on the question.
- The pairwise slope differences all have wide intervals. L2 − L3 is −0.125 (CI −0.305 to −0.022), which excludes zero. L1 − L2 and L1 − L3 include zero (`slope_diff_*`). These are unadjusted for multiplicity.

**Localities.**
- **Size.** Length differs clearly (Kruskal–Wallis H = 27.7, p ≈ 1e‑6, `kruskal_length`). All three pairs differ after Holm correction over the six Mann–Whitney tests (`pairwise[*].mwu_p_holm6`): L1–L2 0.023, L1–L3 9e‑7, L2–L3 0.038. Median length is 15.2 in L1, 9.0 in L2 and 8.0 in L3 (`summary`).
- **Size structure.** L1 and L2 are bimodal or multimodal, with a small-shell mode at about 6–8 and a large-shell mode at about 18–20 (`length_hist_2unit_bins_0_26`). L2 is dominated by small shells (54% under 10, against 34% in L1). L3 is unimodal and truncated, with no shell longer than 11.5 and 77% under 10.
- **Shape.** Mean width/length is 0.839 (L1), 0.846 (L2) and 0.804 (L3). The Kruskal–Wallis test gives p = 0.031 (`kruskal_ratio`). L3 is somewhat more elongate than L2 (Holm p = 0.038) and borderline against L1 (Holm p = 0.056). L1 and L2 do not differ in shape (p = 0.56). The shape difference is small, and L3's lower ratio goes with its slightly steeper slope. Because the samples cover different size ranges, a ratio difference could partly reflect size and allometry and not a distinct form.

## Warnings and data problems

- **L2 repeated block.** The toolkit flags `repeated_pairs` and `repeated_block` in L2: rows 57–63 reappear as 64–70, and row 57 appears again as 71. In total 8 pairs are exact repeats, leaving 71 unique (`L2_exact_duplicate_pairs`). This looks like a copy or entry error, but I cannot confirm it. I kept all 79 in the main analysis, as the toolkit did. Using the 71 unique specimens, the slope is 0.977 (CI 0.946–1.011; `L2_unique_only_log10`). The conclusion is unchanged, but L2's small-shell excess and its n are partly uncertain.
- **L3 repeated pairs.** Three pairs repeat (rows 13/16, 17/26, 20/30). With two-decimal values at small sizes these may be coincidences. I did not remove them.
- I made no outlier exclusions.

## Unsupported parts

| Subtask | Why the toolkit could not do it | What I used instead | How I checked it |
|---|---|---|---|
| CI and isometry test for the RMA slope | `rma` states it gives no standard errors, CIs or tests | Nonparametric bootstrap of specimens (10,000) in `analysis.py` | My RMA slope equals the toolkit slope to 1e‑9 for all three (`toolkit_slope_matches_own`) |
| Differences in slope between localities | No operation exists | Bootstrap difference of independent samples | None independent. The intervals are unadjusted |
| Univariate size and shape comparisons (Kruskal–Wallis, Mann–Whitney, KS, Holm) | `permanova` and `community` are for count data. `permanova` needs freely exchangeable independent units, which three single, unreplicated collections do not justify, and these are two-trait morphometrics, not count data | scipy tests | Holm applied across the 6 Mann–Whitney tests only. The omnibus tests and KS are unadjusted |
| Parsing the file for the above | Toolkit does not return a ready table, and the bootstrap needs raw values | pandas read of `dielasma.dat` | The n values (103, 79, 35) match the provenance note |

I did not use `community`, `rarefaction` or `count_homogeneity`, because these are not count data.

## What the samples cannot establish

- **Isometry as a growth law.** These are cross-sectional samples of conjoined shells. They show a static allometry between individuals and not an ontogenetic trajectory, because age was not recorded. A population mixing cohorts or taxa can look isometric or allometric for reasons unrelated to growth.
- **Population differences.** Each locality is a single sample. There is no replication within a locality, and collecting method and stratigraphic position are not recorded. The tests treat specimens as independent, which they may not be for shells in a cluster. P-values describe sample differences only. Differences in length could reflect size-selective collecting, taphonomic sorting or transport, or different cohort or age composition. L3's truncation at about 11.5 in particular could be any of these.
- **Environment.** Nothing here links shape or size to depth, energy, substrate or salinity. Environmental inference would need independent sedimentological and ecological data. The "in-place assemblage" idea in the provenance note is an assumption and is not tested.
- **Taxonomy.** Two measurements cannot define species. The multimodal length distributions, and the small L3 shape difference, could reflect cohorts, a mixed assemblage, or more than one taxon. They do not support any of these. Taxonomic conclusions would need internal morphology and other characters. Units are also unstated, so absolute sizes cannot be compared with other studies.
