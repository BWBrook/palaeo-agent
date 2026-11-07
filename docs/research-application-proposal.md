# Proposal: first genuine research application (revised)

Claude (Opus 5.5), 7 November 2026, revised the same day after Codex's
[review](research-application-review.md) (`ca27725`). Barry asked that
Palaeo-Agent next be applied to a genuine research question that matches the
statistical tooling already built, using the tools to check results and to
fix problems found along the way. This is not a compliance trial.

## Question and framing

**Primary: the whole depth-ordered record.** In the archived Lake Selina
pollen counts from western Tasmania (`SEL1999`), where do successive spectra
differ by more than counting noise? Which taxa carry each change? How do
expected pollen-category richness at a common count, and abundance
coverage, vary down the core? The answers are reported by depth and sample
ID first, with ages as annotations.

**Secondary: one interval comparison that depends on the chronology.**
- Under the archived IPPD-2 ages, compare the levels bracketing about
  45–38 ka with two climatic benchmarks: MIS 3 to the Last Glacial Maximum,
  and the Late Glacial to the Holocene.
- The benchmarks give context. They are not controls that identify cause.
- The comparison is motivated by the debate over human arrival and
  megafaunal extinction. It cannot identify an effect of either.

Codex and I both recommend this framing. The choice left to Barry is below.

**What this adds.** This is a reanalysis of an existing argument. Turney
et al. (2008, PNAS) already used the Lake Selina pollen and charcoal record
around human arrival and reported little change near 41 ka. The new
contribution is a taxon-resolved assessment of the archived counts,
qualified by counting error. It is not a new pollen record and not a causal
test.

## Data

**Source.** Neotoma dataset 52767 (`SEL1999`, Colhoun; Indo-Pacific Pollen
Database).
- The source publication is [10.1016/S1040-6182(98)00046-9](https://doi.org/10.1016/S1040-6182(98)00046-9).
- Neotoma's policy permits reuse under CC BY 4.0, with attribution to
  Neotoma, the constituent database, the investigators and the publication,
  and the dataset DOI.
- The record returns two DOIs (`10.21233/5Y7N-1B24` and
  `10.21233/av7h-5y24`). Which version each names will be resolved, not
  chosen silently.

**Codex's preflight** ([receipt](research-application-preflight.json),
`scripts/check_selina_intake.py`) found:
- 72 levels and 66 terrestrial pollen taxa (`TRSH` or `UPHE`, NISP);
- terrestrial totals of 282–529, median 364.5;
- that the toolkit accepts m = 282 for all 72 levels, and all 71 adjacent
  pairs at B = 99,999;
- that no engine limit needs changing.

**Chronology**, corrected from my first draft:
- **IPPD-2 (37590)** is a Bacon model. Sample point ages run from 4 to
  78,733 cal BP. The figures −133 and 89,987 that I first quoted are the
  extreme bounds. Per 10 ka of point age there are 6, 6, 12, 8, 10, 10, 10
  and 10 levels.
- **The age bounds are broad and overlap.** For example, 40,189 at 240 cm
  has bounds 36,725–43,989, and 45,481 at 265 cm has bounds 40,785–50,901.
- **IPPD-1 (37589)**, from an older best-fit curve, gives 261,204 against
  IPPD-2's 78,733 at 427 cm. That is a disagreement about what the core
  spans, not an error bar. It must be explained from the 1999 article
  before any named transition is used.
- **Newer TAS1402 cores** have their own chronostratigraphy. It is not
  transplanted onto `SEL1999` without a supported core correlation.

## Stages

**1. Intake, frozen before any composition is viewed.**
- **The source:** save the response and its hash, the sample and depth IDs,
  and the source taxon IDs and labels.
- **The pollen sum:**
  - fix the inclusion rule, the treatment of unidentified categories, and
    any aggregation with its justification;
  - confirm whether an absent taxon entry means zero;
  - harmonise taxa with `map_taxa`. Terrestrial-only extraction is declared
    as unsupported intake, because the study layer can rename and merge
    taxa but not delete them;
  - keep the source labels and counts, and reconfirm m against the final
    sum.
- **The chronology:**
  - read the 1999 article;
  - explain why IPPD-2 is primary, or whether it can be;
  - reconcile the IPPD-1 disagreement;
  - check how the age bounds are defined before calling them any kind of
    interval.

  If the chronology cannot be reconciled, the primary analysis by depth
  stands, and the named comparisons are reported as unresolved or dropped.
- **The named endpoints:** fix each one by sample ID and depth, with its
  selection rule, nominal ages and elapsed duration. A pair spanning about
  seven millennia is not one adjacent step. Where the benchmarks cannot be
  given comparable temporal support, report the unequal support.

**2. Analysis through the API** (the primer rule applies throughout).
- **`count_homogeneity`.** One ordered list of declared pairs: the union of
  the 71 adjacent pairs and the named non-adjacent pairs, with no
  duplicates and none reversed. One call gives:
  - Holm across all omnibus pairs;
  - a separate global Holm family across the pair × taxon Fisher tests.

  The two families do not jointly control one error rate, and the report
  will say so.
  - **Monte Carlo:** B = 99,999 and seed 7112026, frozen. Simulation
    uncertainty is reported, and adjusted calls near the Holm threshold are
    marked as sensitive to Monte Carlo error. No reruns in search of
    significance.
  - **Ranking:** changes are ranked by effect size (proportional
    Bray–Curtis), not by p. Count totals, elapsed time and age uncertainty
    are shown beside each effect.
  - **What the test claims:** that counts are allocated as the stated
    counting model predicts. That claim stays coherent despite serial
    dependence in the core, and Holm tolerates dependence among the pair
    tests. It establishes neither ecological replication, abruptness nor
    cause.
- **`rarefaction`.** At m = 282 for every level:
  - expected observed pollen-category richness and its subsampling SD,
    conditional on the retained table;
  - abundance coverage and full-sample diagnostics.

  This is not plant species richness, and equal counts do not mean equal
  completeness.
- **`community` and `compare`.** Bray–Curtis on proportions and Jaccard,
  PCoA, and the sensitivity of the picture to raw counts.
- **`permanova` is declined.** Levels in a core are not exchangeable.

**Declared unsupported:**
- the intake filtering above;
- the age model, whose archived ages are used as annotations;
- zonation and changepoints, where published zones are cited, not
  recomputed;
- inference about trends.

Rate of change per year is deferred, because it is a descriptive index
that depends on the age model.

**3. Independent check and fixes.**
- **Cross-check:** a primer §7 check of the main quantities against the
  established `vegan` and coverage references, stating which reference
  checks which quantity. `rioja` is dropped, because it adds no independent
  check.
- **Fixes:** each tool problem is fixed contract-first with tests, and
  Codex reviews the fixes and the science.
- **Where the work lives:** `analyses/lake-selina/`. If the result warrants
  it, it becomes a living-paper snapshot.
- **Budget:** no live agent sessions, so no trial budget applies.

**Possible second phase**, not part of this proposal: Hazards Lagoon
(Neotoma 59906) and Melaleuca Inlet (57982), for a west–east comparison of
the Late Glacial to Holocene transition.

## Decision

Barry, 7 November 2026, in chat: "I'll leave that to you to decide." I
decided to keep the secondary 45–38 ka comparison, as recommended below and
by Codex. Stage 1 may still drop it if the chronology cannot be reconciled.

## The choice as it was put to Barry

Whether to keep the secondary 45–38 ka comparison:
- **Recommended:** keep it as a secondary comparison that depends on the
  chronology, beneath the whole-record primary analysis. It is the question
  readers will ask of this record, and it is better answered with the
  limits stated than left implicit.
- **Alternative:** a neutral whole-record analysis with no named historical
  interval.

Either way the intake and design amendments above apply, and stage 1 may
still drop the named comparisons if the chronology cannot be reconciled.
