# Coed Duon (Upper Llanvirn) assemblage change, horizons 1–10

Primer 0.2.0.dev0, SHA-256 `47cab284…913d3`. All numbers are in `results.json`, written by `analysis.py`. Specs are in `specs/`. Run and comparison bundle paths are in `provenance_manifest.json`. They are fresh on every run, so they are kept out of `results.json`.
Citations below are `results.json` key → field. Counts are 23 taxa × 10 horizons. Totals run 13–702: 321, 243, 304, 156, 473, 702, 26, 68, 57, 13.

## Answer

1. **Horizons 1→5 are Sowerbyella-dominated and change little.**
   - Sower is the `_3_Sower` row. I read it as *Sowerbyella* from the provenance note.
   - Adjacent proportional Bray-Curtis is 0.04, 0.04, 0.21, 0.18 (`comm_rel_bc.adjacent_distance`).
   - Pair 3–4 is flagged by the exact conditional test: Holm p = 4.5e-4, with Sower, Macro and Talin individually flagged. Pair 4–5 has Holm p = 9e-4 (`homog_adj.pairs`).
   - Horizons 1–3 are not distinguishable from each other (Holm p 0.62, 0.56).

2. **5→6 is the largest compositional change in the succession.**
   - Relative-abundance Bray-Curtis is 0.671 (`comm_rel_bc.adjacent_distance[4]`).
   - The count-homogeneity test gives Holm p = 4.5e-4 (`homog_adj.pairs`, pair 5–6).
   - The taxon-level Holm family flags `_1_Basil` (3→330 specimens, +46 percentage points) and Sower (422→190, −62 points). It also flags crino, praso and, weakly, Talin.
   - Horizon 6 is the only horizon where Sower is not overwhelmingly dominant. It has higher Shannon and Simpson (1.62 and 0.70, against 0.58 and 0.20 at horizon 5; `comm_rel_bc.diversity`).
   - Rarefied to 13 specimens, expected richness is 2.30 at horizon 5 and 4.74 at horizon 6 (`rare_multi.samples[*].est`).
   - This is a change in evenness and composition, driven mostly by a single-taxon acme (Basil, 47% of horizon 6) and a drop in Sower share. It is not a plain richness gain: observed richness is 14 and 15, and the rarefied difference partly reflects dominance.

3. **6→7 is a large shift, but it is weakly resolved and confounded.**
   - Proportional Bray-Curtis is 0.557 (`comm_rel_bc.adjacent_distance[5]`).
   - The omnibus test gives Holm p = 7e-4, driven only by `_1_Basil` (330/702 → 0/26; Holm p = 1.4e-5). No other taxon is flagged. Horizon 7 has only 26 specimens, so power is low.
   - Sower is 27% at horizon 6 (190/702) and 46% at horizon 7 (12/26). This is not flagged at taxon level.
   - The raw-count Bray-Curtis for 6→7 is 0.934 (`comm_raw_bc`). Most of that is count-total imbalance (702 vs 26), not composition. The tool's bound is in the comparison bundle's `raw_count_total_imbalance_bound`.
   - Horizon 7 is **not** more similar to horizon 6 than to horizon 5. It is closest to horizons 8–10 (distances 0.21, 0.20 and 0.27 to 8, 9 and 10) and is nearer to horizon 5 (0.486) than to horizon 6 (0.557). (`comm_rel_bc.distances_from_7`.)
   - Horizons 7–10 are statistically indistinguishable from each other at neighbouring pairs (Holm p 0.81, 0.52, 0.62). Their totals are only 13–68, so this is a lack of resolution and not demonstrated similarity.
   - The 6→7 step crosses the **unconformity** (provenance). The stratigraphic gap, the lithology change (Upper Flags and Grits to Ashes and Lavas) and the faunal change are inseparable.

4. **Ordination (relative abundance, Bray-Curtis PCoA).**
   - Horizons 1–5 cluster on axis 1 (−0.13 to −0.24).
   - Horizon 6 is isolated (axis 1 0.38, axis 2 −0.34).
   - Horizons 7–10 lie on the positive side (`comm_rel_bc.axis1_2`).
   - Eigenvalues are 0.53 and 0.20 (`comm_rel_bc.eigenvalues`). A small negative eigenvalue is reported and not corrected.

## Robustness to counting totals and abundance representation

| Representation | 5→6 | 6→7 | Reading |
|---|---|---|---|
| Relative abundance, Bray-Curtis (baseline) | 0.671 | 0.557 | Both steps are large. 5→6 is the largest. |
| Raw counts, Bray-Curtis | 0.624 | 0.934 | The ranking reverses, because 6→7 is dominated by the 702-vs-26 total mismatch. |
| Presence/absence, Jaccard | 0.474 | 0.562 | 6→7 is slightly larger. Taxon turnover at horizon 7 is partly an undersampling artefact: 26 specimens miss rare taxa. |

- Source: `comm_rel_bc`, `comm_raw_bc` and `comm_jac`, field `adjacent_distance`.
- Relative vs raw (`compare_rel_vs_raw`): Spearman correlation of all 45 distances is 0.60, Pearson 0.71, and the mean absolute change is 0.28. The choice of representation therefore materially changes the distance matrix.
- Which interpretation is robust: "5→6 is a major compositional change" holds in all three representations (every value ≥ 0.47). "6→7 is the largest break" does not hold in the baseline, and holds only in the raw-count representation, which is confounded by counting totals.
- Rarefaction uses the `rarefaction` operation at size 13 (`rare13.sizes`), the smallest total. Coverage is high everywhere except horizon 10 (0.70) and horizon 7 (0.89) (`rare_multi.samples[*].full_coverage`). Richness at horizons 7, 8 and 10 is therefore poorly constrained, and a rarefied richness above horizon 6 is not a defensible increase.

## Choices

- `community` with relative abundance and Bray-Curtis is the baseline. Raw counts and Jaccard are declared one-factor sensitivities. `compare` was run for baseline vs raw only. Its `baseline_link_verified` is false because I did not chain the baseline run hash into the spec; that hash changes on every run.
- `count_homogeneity` covers the nine adjacent pairs, with 19,999 simulations and seed 20240601. The pair Holm family has size 9 and the taxon Holm family has size 118. There is no joint control (`homog_adj.multiplicity`). Monte Carlo p-values at the floor (5e-5) are limited by the simulation count.
- No `permanova` was run. Ten horizons in one section, grouped as two units around an unconformity, are not exchangeable independent units.
- I did not drop the dominant taxa or merge taxa. The toolkit has `map_taxa` and `select` but no taxon-drop operation, and nothing in the data justifies altering labels. A Sower-excluded sensitivity is therefore not done.
- The `_N_` label codes are undocumented, and I did not interpret them.

## What the data cannot establish

- **Sampling.** Effort per horizon (volume, area, collecting time) is unrecorded, as are the counting protocol and replicates. The homogeneity test treats each horizon as one multinomial draw. It therefore tests counting noise only and not between-collection or spatial variance. A "significant" pair means the counts differ beyond that noise. It does not show that the source communities differed.
- **Pooled counts.** Horizons with 156–702 specimens may be time-averaged or spatially pooled, and bed-scale dominance changes (Basil at horizon 6) may reflect a single bed or patch.
- **Time and rate.** There are no dates, thicknesses or spacings, so rates, durations and the uniformity of steps cannot be estimated. The unconformity means the 6→7 step may represent an unknown amount of missing time.
- **Cause.** Environmental change, facies change, preservation, or an ecological replacement cannot be separated. Horizons 7–10 are in a different lithostratigraphic unit.
- **Absence.** Zero counts are not evidence of absence. For example, the pointwise 95% upper limit on the proportion of any taxon with zero count at horizon 7 is 0.109 (`homog_adj.zero_limits`). Basil is absent in horizon 7 and the upper limit is 0.109. This is compatible with Basil being as common as ~10% there, but not with its 47% abundance at horizon 6.
- **Diversity.** Observed richness (6–15 per horizon) depends strongly on total. Rarefaction to 13 specimens throws away almost all of the information in the large samples.

## Unsupported-parts table

| Subtask | Why the toolkit could not do it | What you used instead | How you checked it |
|---|---|---|---|
| Dropping dominant taxa as a sensitivity | No operation drops taxa | Not done | — |
| Rarefaction at a size above 13 including horizon 10 | Rarefaction refuses extrapolation | Not done; size 13 only | — |

No other unsupported analytical step was used. The only non-toolkit code in `analysis.py` is glue: reading result fields and building `results.json`. A toolkit `reproduce` run was not executed by me.

## Warnings reported by the tools

- Community runs: negative PCoA eigenvalues, reported and uncorrected. Negative inertia is 0.0007 for relative abundance and 0.0014 for raw counts (`comm_rel_bc.warnings`, `comm_raw_bc.warnings`).
- Other warnings: see the `warnings` fields in `results.json`.
