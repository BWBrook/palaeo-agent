# Application 2 proposal: Tasmanian modern pollen, montane against lowland

Claude (Opus 5.5), 8 November 2026. This is the next toolkit application
after Lake Selina. Its main purpose is to exercise the parts of the toolkit
Lake Selina did not reach:
- `permanova` with its dispersion diagnostic, on genuinely independent
  sites;
- `study` metadata joins, `select` and `map_taxa` on real data from several
  analysts.

Following Barry's direction of 8 November 2026, data imperfections are
repaired by inference and declared. The case study serves tool development.

## Question

Do modern pollen spectra from Tasmanian montane sites (≥ 700 m) differ in
composition from lowland sites (< 700 m), and is any difference in location
rather than in dispersion?

This is a calibration question that bears on Lake Selina. That site lies
at 516 m, and its glacial herbfield is read as a lowered treeline.

## Data

27 Tasmanian and Bass Strait surface-sample datasets from the Indo-Pacific
Pollen Database, through Neotoma (CC BY 4.0):
- downloaded 8 November 2026 to
  `source/neotoma-tas-surface-download.json`, SHA-256 `0205169…58c36`;
- 68 samples, between 1 and 7 per site;
- six principal analysts;
- altitudes 2–1,000 m, giving about 14 sites at ≥ 700 m and 13 below.

## Design

- **Unit: one sample per site.** Use the uppermost (surface) sample, chosen
  with `study` `select`. Several samples from one site are not independent
  replicates.
- **Group:** altitude band, joined from site metadata with the study
  metadata join. The 700 m threshold is declared now. It approximates the
  lower limit of subalpine vegetation in western Tasmania.
- **Harmonisation:** `map_taxa` to a common taxonomic level across the
  analysts. `exclude_taxa` reduces the data to the dryland sum, the TRSH
  and UPHE groups.
- **Analyses:**
  - `community`: Bray–Curtis on proportions, with PCoA;
  - `permanova`: independent design, free permutations, fixed seed;
  - the dispersion diagnostic;
  - a sensitivity run on Jaccard presence–absence.
- **Exchangeability caveat:** sites cluster spatially (Cradle–Tyndall, Mt
  Anne, the Central Plateau marshes). The report will say that PERMANOVA's
  free exchangeability ignores that clustering.

## First finding: the toolkit cannot read these data

25 of the 27 datasets are archived as **percentages**, not counts. Only
Hartz Mountains and Tyndall Ranges hold NISP counts.
- `community` and `permanova` accept only `value_type: "count"`.
- The primer rightly forbids converting percentages into counts.
- So the application stops at intake.

This is a substantial gap. Much archived palynology, the IPPD surface
atlas among it, is published only as percentages. Bray–Curtis on
proportions, Jaccard on presence, PCoA and PERMANOVA are all valid on such
data. What is not valid is anything that needs counts: totals, rarefaction,
count homogeneity, and the count-based diversity estimators.

**Proposed sprint 10: proportion input for `community` and `permanova`.**
- Accept `value_type: "percent"` or `"proportion"`. Non-negative finite
  values; rows are rescaled to proportions; the declared denominator is
  recorded.
- Refuse `transform: "none"` where it would mean raw counts. Report richness
  as presence only. Omit totals and count-based estimators.
- In the study layer, allow `exclude_taxa` and `map_taxa` on percentage
  tables. Summing percentages of mapped labels is valid; exclusion
  renormalises when the analysis rescales rows.
- Do not change `rarefaction` or `count_homogeneity`. They keep refusing
  anything that is not a count.

Once sprint 10 lands, this application runs as designed. If Codex prefers,
it could run now on the two counted sites. That is too few for PERMANOVA,
so I do not recommend it.
