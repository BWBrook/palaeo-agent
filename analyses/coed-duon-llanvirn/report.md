# Coed Duon shelly fauna: how composition changes through the succession

Corrected derivative of authentic session A1 (Sonnet 5.5, 1 November 2026),
written by Claude (Opus 5.5) on 2 November 2026. It answers the same brief
from the same data: `benchmarks/past/legacy-data/llanvirn.dat`, Williams,
Lockley & Hurst (1981), via the PAST case studies.

The corrections address every finding of Codex's independent review
(`evaluation/authentic/run-records/authentic-20261101/review-codex.json`); the
list of changes is at the end. Every number below comes from `results.json`,
which `uv run analyses/coed-duon-llanvirn/analysis.py` writes (seed 20261102).
Keys are given in backticks.

## Brief

How does assemblage composition change through the Coed Duon succession,
particularly between horizons 5–6 and 6–7? Which interpretations remain
supported after considering differences in counting totals and defensible
ways of representing abundance? What can the sampling and stratigraphic
record not establish?

## Answer

1. **Horizons 1–5 are dominated by the label `Sower`, *Sowerbyella*.** Its
   proportions are 0.95, 0.93, 0.95, 0.74 and 0.89 (`proportion.Sower`).
   - Adjacent steps 1–2 and 2–3 are within counting noise: composition-null
     p_Holm = 0.56 (`composition_null`).
   - Steps 3–4 and 4–5 are small but detectable: proportional Bray–Curtis 0.21
     and 0.18, p_Holm = 0.002.
2. **5→6 is the largest compositional step in the section.**
   - Proportional Bray–Curtis is 0.67. The pooled-composition null at fixed
     totals has a 95th percentile of 0.09, and p_Holm = 0.002, the floor of
     4,999 simulations.
   - It ranks first among the nine steps under every representation that does
     not depend on counting totals (`rank_of_focal_steps`): proportions,
     square-root proportions, and log(1 + x) of counts standardised to 100 or
     to 13 specimens.
   - At the taxon level (Fisher exact, Holm over the 19 taxa present at either
     horizon, `taxa_5_6`):
     - `Sower` falls from 422/473 to 190/702.
     - `Basil` rises from 3/473 to 330/702.
     - `crino`, `praso`, `Rostr` and `Dalma` rise, and `Talin` falls from
       9/473 to 0/702.
     - All seven have p_Holm < 0.05. No other taxon reaches significance,
       `Rbryo` included.
3. **6→7, across the unconformity, is the second-largest step.**
   - Proportional Bray–Curtis is 0.56, against a null 95th percentile of
     0.30. p_Holm = 0.002.
   - It ranks second under every total-independent representation.
   - Only `Basil` changes significantly at the taxon level (330/702 to 0/26,
     p_Holm = 2e-6).
   - Zero in 26 specimens does not show that *Basil* was absent. Its
     proportion at horizon 7 could still be up to 0.11 (one-sided 95% upper
     limit, `membership_6_7.upper95_proportion_of_taxon_unseen_at_b`).
   - Horizon 7 has only 26 specimens, so nothing finer than "*Basil* falls
     from 0.47 to below about 0.11, and *Sowerbyella* is at 0.46" is
     resolved.
4. **Horizons 7–10 are small and more even than 1–5.**
   - Totals are 26, 68, 57 and 13. Inverse Simpson is 2.3–4.7 here, against
     1.1–1.3 for 1–3 and 5, 1.8 at 4 and 3.3 at 6 (`inverse_simpson`).
   - No adjacent step among 7–10 is distinguishable after Holm correction.
     8–9 has unadjusted p = 0.015 and p_Holm = 0.074.
   - The PCoA of square-root-proportion Bray–Curtis separates horizons 1–5
     from 6–10 on axis 1. Axis 1 holds 58% of the positive eigenvalues, and
     negative eigenvalues are negligible (1%) (`pcoa_sqrt_proportion`).
   - Horizon 4 lies between the two groups (−0.10). Horizon 6 sits with
     7–10 (+0.23), not with the flags and grits below it.

## Robustness to counting totals and to the representation of abundance

Totals range from 13 to 702.

- **Which focal step is larger.** A1 reported that log(1 + count) reverses
  the order (6–7 larger). That comparison applied the transform to raw counts,
  so it confounds representation with the 27-fold difference between 702 and
  26 specimens (`bray_curtis.log1p_raw_counts_confounded`: 0.46 for 5–6 and
  0.65 for 6–7). Standardised to a common total first, log(1 + x) gives:
  - 0.50 and 0.43 at 100 specimens;
  - 0.56 and 0.48 at 13.

  **That 5→6 is the larger step is robust to representation. That both steps
  are large is robust too.**
- **Richness.** Raw richness rises with total count (Spearman ρ = 0.59,
  p = 0.07, n = 10). Rarefied to 13 specimens (`rarefied_richness`; the ranges
  are 95% within-sample rarefaction intervals):
  - horizons 1–3 and 5: 1.6–2.3 (ranges 1–4);
  - horizon 4: 3.6 (2–6);
  - horizon 6: 4.7 (3–7);
  - horizons 7–10: 4.2–6.0 (2–8).

  So the raw richness peak at 5–6 is largely a sample-size effect. The rise in
  rarefied richness from 5 to 6 reflects *Sowerbyella*'s dominance breaking
  down, which is the same signal as the evenness change. It is not separate
  evidence of new taxa.
- **The dominant taxa.** With `Sower` excluded, the rest of the fauna still
  changes strongly at both steps (`without_dominants_*`):
  - 5→6: Bray–Curtis 0.69, on 51 and 512 specimens;
  - 6→7: 0.74, on 512 and 14.

  With both `Sower` and `Basil` excluded, the values are 0.59 (48 and 182
  specimens) and 0.41 (182 and 14). The horizon-7 figure rests on 14
  specimens.

## Membership: what can and cannot be said

- **5→6.** Ten taxa are shared, five appear and four disappear
  (`membership_5_6`).
  - Appearances: `Tripl` (10 specimens), `Schiz`, `Pseud` (3 each), `Ortho`
    and `Hespe` (1 each).
  - Disappearances: `Talin` (9 specimens), `Salop` (6), `Marro` and `Gastr`
    (1 each).
  - **Tested with Holm-adjusted Fisher tests** (`taxa_5_6`):
    - Only `Talin`'s decline is significant (9/473 to 0/702, p_Holm = 0.004).
    - `Salop` (6 to 0, p_Holm = 0.0501) and `Tripl` (0 to 10, p_Holm = 0.081)
      are suggestive.
    - The singletons are uninformative.
  - The plug-in probabilities in `membership_5_6` (for example, 1e-6 for
    missing `Talin` at horizon 6 if its horizon-5 proportion held) are
    descriptive only. They treat an estimated proportion as known and are not
    adjusted for multiplicity.
  - A zero count never establishes absence. Even for `Talin`, the proportion
    at horizon 6 could be up to 0.004 (one-sided 95% upper limit).
  - So 5→6 is primarily a large reorganisation of abundance. Its membership
    changes are real in the counts, but only one decline of a minor taxon is
    statistically supported. A1's "a change of abundance, not membership"
    was too categorical, and "turnover" would be too strong in the other
    direction.
- **6→7.** Seven taxa are shared, eight disappear and one appears
  (`membership_6_7`).
  - Of the eight losses, only `Basil`'s is informative. The rest (`hyalo`,
    `Rostr`, `Tripl`, `Horde`, `Schiz`, `Pseud`, `Ortho`) would each go unseen
    in 26 specimens with probability 0.55–0.96.
  - The one gain, `Glypt`, is a single specimen. Its tail probability uses a
    point estimate of 1/26, so it means nothing.
  - (A1 listed `Talin` and `Salop` as 6→7 losses. Both had already
    disappeared at 5→6.)
- **Rarefied Sørensen** (presence/absence after rarefying both horizons to 13
  specimens, `sorensen_rarefied`):
  - 0.63 (95% range 0.33–0.80) for 5–6 and 0.55 (0.27–0.80) for 6–7, against
    0.33–0.52 elsewhere.
  - The intervals overlap widely. Rarefying to 13 also mixes evenness into
    presence: a *Sowerbyella*-dominated sample of 13 shows few taxa.
  - So presence/absence alone does not single out either step.
- **The bootstrap intervals** (`bray_curtis_bootstrap`) resample observed
  proportions. A taxon unseen at a horizon stays at zero in every replicate.
  They describe counting error around the observed profiles and say nothing
  about unseen taxa.

## Interpretations that remain supported

- A strong reorganisation of relative abundance at horizon 6. *Sowerbyella*
  dominance gives way to an assemblage in which `Basil` makes up 47%,
  alongside increases in several minor taxa and a significant decline of
  `Talin` to zero in the sample.
- A further compositional change across the unconformity (6→7), carried
  mainly by the decline of `Basil` to zero observed specimens.
- The Ashes and Lavas samples (7–10) are more even than horizons 1–5 and
  group with horizon 6 in ordination.

## Not supported, or not establishable from these data

- **Time and rate.** There are no thicknesses, spacings or dates. The 6→7
  step spans an unconformity of unknown duration, so neither step can be read
  as abrupt or gradual, or as an event.
- **Cause.** Environmental change, facies, volcanic influence and taphonomy
  are all confounded with the change of lithostratigraphic unit at 6–7, and
  the data cannot separate them.
- **Counting practice.**
  - The materials do not say how specimens were counted (for example, how
    disarticulated valves or sclerites were treated), so the counts are not
    known to be comparable across taxa.
  - Outside knowledge, not in the provided materials: `Basil` is probably the
    asaphid trilobite *Basilicus*. If so, and if trilobite sclerites were
    counted separately, its horizon-6 abundance could be inflated relative to
    the brachiopods. This is a hypothesis to check against Williams et al.
    (1981), not a finding.
- **Densities and replication.** Sampling effort is unrecorded and each
  horizon is a single collection. Abundances are therefore relative, not
  densities. All tests here treat each horizon as one multinomial sample from
  a homogeneous assemblage, so they cover counting error only, not
  within-horizon heterogeneity. Their p-values are optimistic.
- **Small horizons.** Horizons 7 and 10 (n = 26 and 13) cannot support
  taxon-level conclusions, except the loss of an abundant taxon.

## Choices

- **Tests.**
  - The composition test is one test per adjacent step of overall
    proportional composition at fixed totals, with Holm correction across the
    nine steps.
  - Per-taxon claims rest on Fisher exact tests with Holm correction across
    the taxa present at either horizon. They do not rest on the composition
    test.
- **Labels.** Taxa are reported by their file labels, without the
  undocumented `_N_` code. Only `Sower` (*Sowerbyella*) and `Dalma`
  (*Dalmanella*) are expanded in the provenance.
- **Data.** No samples or taxa were dropped.

## Changes from A1, in response to the independent review

| Review finding | Correction |
| --- | --- |
| The null test was described as showing that each listed taxon change exceeds noise; `Rbryo` was listed but is not significant | The composition test is now described as testing overall composition; taxon claims use Holm-adjusted Fisher tests; `Rbryo` is no longer listed |
| Horizon 5 has 51 non-*Sowerbyella* specimens, not 48 | Both counts reported, each with its definition |
| "Abundance, not membership" overstated | Gains and losses enumerated; membership claims rest on Holm-adjusted Fisher tests (only `Talin`'s decline is significant); zero counts are not treated as absence |
| `Talin` and `Salop` mislisted as 6→7 losses | Computed loss lists; both occur at 5→6 |
| Log-count comparison confounded with totals | Log transform applied after standardising totals; 5→6 > 6→7 under every total-independent representation |
| "Slightly more uncertain" rarefied richness unquantified | 95% rarefaction ranges reported |
| The bootstrap cannot represent unseen taxa | Stated; membership claims no longer rest on bootstrap intervals |
| `Basil` = *Basilicus*, a trilobite, asserted without being flagged | Labelled as outside knowledge and a hypothesis |
| `mean_pooled_prop` summed over horizons, not taxa | `pooled_composition` gives specimen-weighted taxon composition per unit |

Also changed: Holm correction replaces "survives Bonferroni" reasoning for
the adjacent-step tests (8–9 is not significant after correction), and the
standalone script runs with pinned library versions.

A second independent review (Codex, 2 November 2026) found that the
membership correction leaned on plug-in absence probabilities, and that one
percentile was mis-rounded. Membership claims now rest on the Holm-adjusted
tests, and zero counts carry upper limits instead of being read as absence.
