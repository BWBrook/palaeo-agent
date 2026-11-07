# Lake Selina: stage 1 intake and frozen design

Claude (Opus 5.5), 7 November 2026. This freezes the intake, the chronology
treatment, the named comparisons and the test settings **before any
composition, richness or test result was computed or viewed**. The git commit
that adds this file is the record of that order.
- **Design:** [proposal](../../docs/research-application-proposal.md) and
  Codex's [review](../../docs/research-application-review.md).
- **Framing:** keep the secondary 45–38 ka comparison. Barry left the choice
  to Claude ("I'll leave that to you to decide", 7 November 2026, in chat).

Reproduce:

```bash
uv run analyses/lake-selina/intake.py
```

It checks the SHA-256 of both saved Neotoma responses. It then rewrites
`data/counts.tsv`, `data/levels.csv`, `data/taxa.csv` and `design.json`,
and validates the specs through the toolkit.

## Source

- **Records:** Neotoma dataset 52767 (`SEL1999`, Colhoun; Indo-Pacific
  Pollen Database), downloaded 7 November 2026. The download and the
  chronology responses are saved in `source/` (SHA-256 `5dd1a71c…` and
  `8bda8c89…`). The download hash matches Codex's preflight.
- **Licence and citation:** CC BY 4.0 under Neotoma policy. Cite Neotoma, the
  IPPD, Colhoun et al. (1999,
  [10.1016/S1040-6182(98)00046-9](https://doi.org/10.1016/S1040-6182(98)00046-9))
  and the dataset DOIs. The record returns two DOIs (`10.21233/5Y7N-1B24`
  and `10.21233/av7h-5y24`). Which version each names is still to be
  resolved before publication.

## Pollen sum

The rule:
- terrestrial pollen only: ecological group `TRSH` or `UPHE`, element
  `pollen`, units NISP;
- source labels and counts kept;
- no aggregation and no renaming.

The result is 72 levels from 80 to 427 cm and 66 taxa. Levels are 5 cm
apart, except for 247 cm (in place of 250), an extra level at 382 cm, and
the basal 427 cm. The smallest terrestrial total is 282, so m = 282
is reconfirmed and stated explicitly in the rarefaction spec.

**Absent entries are zero-filled.** Neotoma stores positive counts only:
all 2,195 entries in the download are positive, 1,891 of them in the
retained terrestrial groups. Absent entries are zero-filled by the archive's
own conversion convention, as in [Neotoma's pollen
workflow](https://open.neotomadb.org/EPD_binder/simple_workflow.html)
(`values_fill = 0`). This is not proof that every category was searched for
uniformly, and it says nothing about biological absence. The 1999 counting
protocol has not been checked.

**Excluded:**
- spores: ferns and fern allies (`VACR`), *Sphagnum* (`AQBR`), *Isoëtes*
  (`AQVP`);
- aquatic pollen (`AQVP`): *Myriophyllum*, *Utricularia*, *Liparophyllum*.

**Residual categories** are kept as archived:
- "Proteaceae" sits beside seven Proteaceae genera, "Rutaceae" beside
  *Boronia* and *Phebalium*, "Epacrideae" beside *Monotoca*, *Richea* and
  *Sprengelia*, and "Myrtaceae cf. *Baeckea*" beside three Myrtaceae genera;
- the archived variables are **assumed to be disjoint counting
  categories**, pending confirmation from the source. Some levels support
  this, for example 531305 (Proteaceae 0, *Banksia* 6) and 531323
  (Rutaceae 0, *Boronia* 1), so the broad columns are not family totals.
  Nothing is merged on speculation. Category richness depends on how finely
  grains were identified, so richness is reported as *pollen-category*
  richness.

**Wetland taxa** (Cyperaceae, Restionaceae, *Gymnoschoenus*) stay in the sum
as the archive assigns them. Buttongrass moorland is regional vegetation in
western Tasmania.

**Not used:** `map_taxa`, because labels are unique and no synonyms need
merging.

**Declared unsupported intake:** extracting the table from JSON, filtering
by ecological group, and selecting endpoints from the archived ages. The
study layer can filter rows and rename or merge taxa. It cannot delete taxa
or read Neotoma JSON.

## Chronology

**Both archived models rest on the same six controls** (from the chronology
response):

| Depth (cm) | Control | Age (¹⁴C yr BP) | Lab no. | Material |
| --- | --- | --- | --- | --- |
| 80 (IPPD-2) / 0 (IPPD-1) | core top, estimated | 0 | | |
| 125 | radiocarbon | 14,200 ± 230 | SUA 3040 | organic-rich mud |
| 150 | radiocarbon | 18,250 ± 200 | OZA 236U | silt |
| 165 | radiocarbon | 18,900 ± 220 | OZA 237U | silt |
| 230 | radiocarbon | 33,800 ± 1,100 | OZA 238U | silt |
| 295 | radiocarbon | 52,110 ± 5,800 | SUA 3041 | silt |

**How the three chronologies relate:**
- **IPPD-2** (default, a Bacon model by S. Flantua) runs from 80 to 427 cm
  and puts the base at 78.7 ka.
- **IPPD-1** (a best-fit curve in Excel with IntCal09, by A. Herbert) places
  the core top at 0 cm, not 80 cm, and puts the base at 261 ka.
- **The original authors** read the base as the Last Interglacial
  (substage 5e, about 130 ka), from the pollen sequence. Turney et al. (2008)
  repeat this. The abstract reports a 397 cm core, which does not match the
  80–427 cm depth range in the archive. The full article has not been
  inspected.

**What this reconciles:**
- **Below 295 cm, no model has a date.** All three ages there are
  extrapolation or correlation, and they differ by a factor of three. That
  disagreement is about the undated lower core. No named comparison uses
  it. Levels below 295 cm are analysed by depth only, and the report will
  give no age for them.
- **Between 125 and 295 cm, ages are interpolated between bulk-sediment
  radiocarbon dates.**
  - The 33,800 ± 1,100 date at 230 cm (about 38 ka calibrated) lies just
    below the young endpoint of the 45–38 ka comparison (225 cm, 36,902
    under IPPD-2).
  - The 52,110 ± 5,800 date at 295 cm is archived as finite
    (`infinite = false`) with a two-sided error. It lies near the method's
    useful limit, so it is a weak finite control whose dating and
    calibration warrant checking. It is not treated as a minimum age. Old
    and young carbon can bias bulk-sediment dates in either direction.
  - The models disagree even inside the dated interval: at 190 cm, IPPD-2
    gives 28,830 and IPPD-1 gives 36,818.

  The 45–38 ka comparison is therefore *chronology-dependent*, as the
  proposal states. The lower-core disagreement is scoped out, not resolved.
- **Above 125 cm, ages are interpolated** between an estimated core top and
  one date. Both Late Glacial → Holocene pairs (100/120 cm, and 95/120 cm
  under IPPD-1) lie wholly above the 125 cm date. The IPPD-2 bounds at
  100 cm run from 3,369 to 11,806. Three intervening levels support an
  endpoint contrast but cannot resolve the trajectory or how abrupt the
  change was.
- **The calibration curve** behind IPPD-2 is not stated in the archive;
  SHCal would be appropriate for Tasmania. Ages are annotations, and no
  age model is rebuilt here, because rebuilding one is unsupported and
  outside scope.
- **The newer TAS1402 chronology** is not used, because there is no core
  correlation to `SEL1999`.

## Named comparisons (frozen)

**Rule.** For a window [young, old] in cal BP:
- the young endpoint is the level with the largest IPPD-2 point age that is
  ≤ young;
- the old endpoint is the level with the smallest IPPD-2 point age that is
  ≥ old.

Each window spans 7 ka, so the three comparisons have similar temporal
support.

| Comparison | Window (cal BP) | Young endpoint | Old endpoint | Elapsed (IPPD-2) | Levels between |
| --- | --- | --- | --- | --- | --- |
| Historical, 45–38 ka (secondary) | 38,000–45,000 | 531333, 225 cm, 36,902 | 531341, 265 cm, 45,481 | 8,579 yr | 7 |
| Benchmark, MIS 3 → LGM | 21,000–28,000 | 531310, 145 cm, 20,928 | 531319, 190 cm, 28,830 | 7,902 yr | 8 |
| Benchmark, Late Glacial → Holocene | 8,000–15,000 | 531321, 100 cm, 7,532 | 531332, 120 cm, 15,176 | 7,644 yr | 3 |

**Chronology sensitivity.**
- The same rule applied to IPPD-1 ages picks different endpoints in all
  three comparisons:
  - historical: 190 and 270 cm;
  - MIS 3 → LGM: 135 and 165 cm;
  - Late Glacial → Holocene: 95 and 120 cm.
- These three IPPD-1 pairs are declared now as **archived-model endpoint
  sensitivities**. IPPD-1 is not treated as an equally validated chronology
  or as a distribution of chronological uncertainty.
- Changing the age *annotation* of a fixed pair is reported separately from
  changing the *endpoints*.
- IPPD-2's marginal age bounds are not treated as independent age draws.

## Tests (frozen)

**`count_homogeneity`.** One call over one ordered list of 77 unique declared
pairs: the 71 adjacent pairs, then the 3 named pairs, then the 3 IPPD-1
sensitivity pairs. It uses B = 99,999 and seed 7112026.
- Holm across the 77 omnibus pairs is one family. The global pair × taxon
  Fisher tests are a second family. The two do not jointly control one
  error rate.
- **Primary results.** The API's plus-one p-values and its Holm adjustment
  across all 77 pairs, with the IPPD-1 pairs kept in the common families.
- **Monte Carlo sensitivity** (amended before results, per Codex's stage-1
  review):
  - apply Holm separately to the 77 lower and to the 77 upper
    Clopper–Pearson bounds of the exact conditional tail probabilities;
  - flag pair i when Holm(lower)[i] ≤ 0.05 ≤ Holm(upper)[i].

  This is a sensitivity envelope, not a simultaneous interval or a new
  significance rule. It is computed outside the API and declared as
  unsupported postprocessing. B and the seed are fixed, and there are no
  reruns.
- **Ranks.**
  - The 71 adjacent steps are ranked by proportional Bray–Curtis among
    themselves.
  - The three primary long-interval comparisons are reported separately,
    each beside its IPPD-1 sensitivity pair.
  - There is no pooled rank over the 77 pairs.
  - Count totals, elapsed IPPD-2 years and age bounds are shown beside each
    effect.
- **Direction.** Pairs run from shallow and younger (a) to deep and older
  (b), and the API's taxon effect is b − a. Change forward in time is
  reported as younger minus older, that is −(b − a), labelled with both
  sample IDs. The frozen pair order, which also fixes the random streams,
  is unchanged.

**`rarefaction`** at m = 282 for all 72 levels.

**`community`:**
- Bray–Curtis on relative abundance (primary);
- Bray–Curtis on raw counts and binary Jaccard;
- `compare` of relative against raw.

**Not used:**
- `permanova`, because levels in a core are not exchangeable;
- rate of change per year, which is deferred.

Public `validate` of all five specs: `valid`, with no exclusions or
warnings (see `design.json`). No random tables have been sampled and no
estimates computed.

## Stage 2

Stage 2 is the analysis, which will run `design.json` unchanged. A
correction to the design found later will be labelled as a deviation, with
its reason, not folded in silently.
