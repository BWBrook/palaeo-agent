# Proposal: first genuine research application

Claude (Opus 5.5), 7 November 2026, for Barry and Codex. Barry asked that
Palaeo-Agent next be applied to a genuine research question that matches the
statistical tooling already built, using the tools to check results and to
fix problems found along the way. This is not a compliance trial.

## Recommendation

**Question.** In the Lake Selina pollen record from western Tasmania (about
90 ka to the present), where do successive pollen spectra differ by more than
counting noise? Which taxa carry each change? How does palynological
richness at a common count change through the last glacial cycle? In
particular, is the change between the levels that bracket about 45–38 ka
(the interval of human arrival in Tasmania and of the last dated megafauna)
larger than counting noise, and how does it rank against the changes at two
climatic transitions declared as references: MIS 3 to the Last Glacial
Maximum, and the Late Glacial to the Holocene?

**Data.** Neotoma dataset 52767, Lake Selina (Colhoun, PI). Checked today
through the Neotoma API:
- 72 levels, of raw counts, not percentages;
- 66 terrestrial pollen taxa;
- terrestrial sums of 282 to 529 per level, median 365;
- a published chronology (IPPD-2) running from −133 to 89,987 cal BP;
- 8 to 12 levels per 10 ka, including 8 at 30–40 ka and 11 at 40–50 ka.

Neotoma distributes its data under CC BY 4.0; I will confirm that on the
record before committing a derived table. The table is small (well under
1 MB). It will be fetched by a script and stored with its SHA-256, with
Colhoun et al. and Neotoma cited.

**Why this one.**
- The sprint-7 workflow was built for exactly this data structure: unequal
  counts of many taxa in many samples.
- Rarefied richness at a common pollen count is standard palynology (Birks
  and Line 1992), and estimated coverage tells us whether that comparison is
  well posed.
- Testing declared adjacent pairs for homogeneity asks a question that
  zonation by eye cannot: whether a change exceeds what recounting the same
  assemblage would produce, and which taxa carry it. Zero-count limits
  bound "absences".
- `community` and `compare` give Bray–Curtis on proportions, PCoA, and how
  sensitive the picture is to the choice of representation.
- The record also contains a design the toolkit must not be forced onto.
  Levels in a core are not exchangeable, so `permanova` across zones is
  unsuitable, and declining it is part of the analysis.
- It is real Tasmanian palaeoecology on a question of standing interest,
  and the record is long enough for the 40 ka contrast to be judged against
  the record's own background of change, not in isolation.

## Analytical scope

**Through the API (primer rule applies throughout):**
- `community`: diversity, Bray–Curtis on proportions and Jaccard, PCoA;
  `compare` against raw counts;
- `rarefaction`: expected richness and conditional SD at m = 282 (the
  smallest terrestrial sum) for all 72 levels, coverage at that size, and
  full-sample coverage with singleton and doubleton diagnostics;
- `count_homogeneity`: all 71 adjacent pairs as the declared family (Holm
  across pairs; taxon Fisher tests in the second Holm family), plus the
  three pre-declared bracket contrasts reported separately;
- the study layer for building the terrestrial pollen sum and harmonising
  taxa, where it supports the step.

**Unsupported, to be declared with reasons:**
- **The age model.** The published IPPD-2 ages are used as given. Ages near
  and beyond the radiocarbon limit are the weakest part of the record, and
  this matters most for the 40 ka contrast.
- **Zonation and changepoints.** There is no constrained clustering or
  broken-stick test in the toolkit. Published zones are cited, not
  recomputed.
- **Rate of change.** Adjacent Bray–Curtis distances from `community`
  divided by the age gap is arithmetic on API output. It is reported as
  descriptive.
- **Inference about trends.** Levels are autocorrelated, and nothing here
  tests a trend.

**What the record cannot establish:** cause. A compositional change at
about 40 ka would be consistent with fire, climate or herbivore release, and
one site cannot separate them. Charcoal and *Sporormiella* are not in this
dataset. Pollen richness is not plant species richness. The analysis can
say whether, and in which taxa, the spectra change beyond counting noise,
and how that change compares with the climatic transitions.

**Working method.**
- Each problem the tools show is fixed contract-first with tests. Expect
  pressure from 71 declared pairs in one homogeneity run, 72 × 66
  rarefaction, sparse taxa and negative PCoA eigenvalues. Codex reviews the
  fixes and the science.
- An independent cross-check in the style of primer §7 is run against `vegan`
  and `rioja` in R.
- The analysis lives in `analyses/lake-selina/`. If the result warrants it,
  it becomes a living-paper snapshot: the article, a two-page brief and an
  agent guide.
- No live agent sessions are involved, so no trial budget applies.

**Possible second phase**, not part of this proposal: Hazards Lagoon
(Neotoma 59906, eastern Tasmania, 22.6 ka to the present, 32 levels) and
Melaleuca Inlet (57982, the Holocene), for a west–east comparison of the Late
Glacial to Holocene transition.

## The one choice that needs Barry

Whether to frame the analysis around the 45–38 ka contrast at all. The
chronology is weakest there, and both human arrival and megafaunal
extinction are contested topics where a single-site pollen result could be
over-read. My recommendation is to include it as one of three pre-declared
contrasts, with the two climatic transitions as references and the
chronological caveat stated up front. The alternative is a neutral analysis
of the whole record with no named contrast.
