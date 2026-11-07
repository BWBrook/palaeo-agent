# Lake Selina: amended report (dryland sum, depth-reconciled)

Claude (Opus 5.5), 8 November 2026. This report supersedes the
interpretation in [report.md](report.md). That report's numbers still stand
for the archived 66-category definition. What changed, and why, is in
[AMENDMENT-1.md](AMENDMENT-1.md), committed at 9a2ee8f before this analysis
ran. It is driven by the paper (Colhoun et al. 1999) and by Codex's
[source review](COLHOUN1999-SOURCE-REVIEW.md).

The numbers are in `results-amended.json` and `definition-sensitivity.json`.

Reproduce from the repository root:

```bash
uv run analyses/lake-selina/amend_source.py
uv run analyses/lake-selina/run_api.py design-amended.json
uv run analyses/lake-selina/analysis.py design-amended.json
uv run --with scipy analyses/lake-selina/compare_definitions.py
```

The toolkit primer is 0.2.0.dev0, SHA-256
`cdec09d1ab058224869120b2ac6de406be62df6ed112373dfa1057492971f765`.

## What changed

- **Denominator.** The analysis now uses the paper's dryland pollen sum:
  sedge and aquatic pollen are removed. That leaves 60 categories, with
  m = 272.
- **Depths.** Archive depths are reported with a candidate paper depth
  (archive − 30 cm) beside them. The +30 cm offset is supported by nine
  printed pollen sums and by the zone boundaries, but it is not proved.
- **No ages.** The archived chronologies attach their radiocarbon controls
  at paper depths to samples at archive depths. Until that alignment is
  resolved, no level gets an age, and the three "named" pairs are only
  fixed sample-ID contrasts.
- **Withdrawn from report.md:**
  - "early forest recovery or old carbon": the misalignment explains the
    anomaly;
  - the historical and climatic labels for the named pairs;
  - the agreement with Turney et al. near 41 ka.

## Results that hold under both definitions

| Quantity | 66 categories (m = 282) | 60 dryland categories (m = 272) |
| --- | --- | --- |
| Adjacent steps beyond counting noise (Holm) | 41 of 71 | 41 of 71 |
| Median adjacent proportional Bray–Curtis | 0.206 | 0.203 |
| Rank agreement of the 71 step effects (Spearman) | — | 0.994 |
| Rank agreement of rarefied richness across 72 levels (Spearman) | — | 0.993 |
| Pairs sensitive to Monte Carlo error (Holm envelope spans 0.05) | 1 | 4 |
| Minimum coverage at m | 0.955 | 0.953 |

**Steps that change classification.** Two steps cross 0.05:
- 345→350 cm moves from 0.054 to 0.033;
- 360→365 cm moves from 0.033 to 0.057, and is Monte Carlo-sensitive.

**Monte Carlo-sensitive pairs under the dryland sum:** 125→130, 185→190,
255→260 and 360→365 cm. They are reported as unresolved.

**The six largest steps are the same set under both definitions**
(`adjacent_steps[*].adjacent_rank_by_braycurtis`). Signs are forward in
time, that is, shallower minus deeper:

| Rank | Archive (paper) cm | Bray–Curtis | Taxa at Holm p < 0.05 |
| --- | --- | --- | --- |
| 1 | 155→160 (125→130) | 0.453 | Poaceae −0.25; *N. gunnii* +0.14; *Pherosphaera* +0.08 |
| 2 | 315→320 (285→290) | 0.398 | Asteraceae −0.16; *Phyllocladus* +0.14 |
| 3 | 275→280 (245→250) | 0.389 | Asteraceae +0.27 |
| 4 | 290→295 (260→265) | 0.376 | Apiaceae +0.16; *N. gunnii* −0.10; *Pherosphaera* +0.09 |
| 5 | 280→285 (250→255) | 0.365 | Asteraceae −0.17 |
| 6 | 150→155 (120→125) | 0.344 | *Pherosphaera* −0.09; *Phyllocladus* +0.07; *Microcachrys* −0.05 |

**The largest step sits where the paper puts its date.** Archive 155→160 cm
is paper 125–130 cm: the top of the paper's herb zone LS8, and the level
where the 14,200 ± 230 ¹⁴C yr BP date "dates the commencement of deposition
of the surface organic-rich mud". The step is the end of the grass and herb
dominance and the start of the subalpine and rainforest expansion of zone
LS9.

**Rarefied richness** at m = 272 (`levels[*].expected_richness_272`).
Medians, with ranges:

| Archive interval (cm) | Median E[S] | Range |
| --- | --- | --- |
| Upper forest, 80–140 | 21.9 | 19.9–30.9 |
| Transition, 145–155 | 27.2 | 23.1–27.8 |
| Herb interval, 160–295 | 21.4 | 14.8–28.4 |
| Peak herbfield, 165–190 | 16.4 | 14.8–17.5 |
| Lower forest, 300–427 | 25.2 | 17.8–30.3 |
| Basal *Lagarostrobos* forest, 395–427 | 18.7 | 17.8–21.8 |

The pattern from report.md holds. Richness is lowest at peak herbfield and
in the basal forest, and highest in mixed, transitional spectra. It is
richness of pollen categories, conditional on the retained table.

**Representation.** Relative and raw Bray–Curtis agree (r = 0.997). PCoA
axis 1 carries 54 % of the positive inertia, and the negative-to-positive
inertia ratio is 0.073, uncorrected.

## The three fixed sample-ID contrasts (no temporal labels)

| Pair (archive cm, paper cm) | Bray–Curtis, 66 → 60 categories | Holm p, 60 categories | Taxa at Holm p < 0.05, 60 categories |
| --- | --- | --- | --- |
| 531333 / 531341 (225/265; 195/235) | 0.196 → 0.197 | 0.0032 | none |
| 531310 / 531319 (145/190; 115/160) | 0.727 → 0.696 | 0.00077 | Poaceae, *Dichosciadium*-type Apiaceae, *Phyllocladus*, Asteraceae, *N. cunninghamii*, *Leptospermum*, *Spyridium* |
| 531321 / 531332 (100/120; 70/90) | 0.289 → 0.305 | 0.00077 | Asteraceae |

**Paper zones.**
- **531310 / 531319** spans the paper's zone LS9 into LS8 at paper
  115/160 cm: forest expansion set against herbfield. It is the
  deglacial-type change, wherever it falls in calendar time.
- **531333 / 531341** lies within the paper's zone LS7 (paper 170–235 cm).
  The brief resolved expansion of *N. gunnii*, *Pherosphaera* and
  *N. cunninghamii* at archive 255–260 cm (paper 225–230 cm) corresponds to
  the paper's "small peak in pollen of *Nothofagus* near the base of the
  zone".

**Timing.** These depths lie near the paper's 230 cm date of
33,800 ± 1,100 ¹⁴C yr BP. The authors say this "could be older" and place it
in early isotope stage 3 by correlation. Whether they correspond to 45–38 ka
is unresolved, and no historical inference is drawn.

## The flagged level (531331, archive 220 cm, paper 190 cm)

The paper reports a strong *Lagarostrobos* peak at 190 cm. The archive level
has no *Lagarostrobos* entry, and its dryland total is 408, against a
printed sum of 480. In the archived counts, the two steps touching this
level are among the smallest in the record:
- 215→220 cm: 0.159, Holm p 0.25;
- 220→225 cm: 0.095, Holm p 1.0, the smallest of all 71.

If about 72 *Lagarostrobos* grains were omitted from the archive, both steps
would be understated. The 72-grain residual fits that, but it is not
proof, so no counts are invented. This is a provenance defect for Neotoma
and the IPPD, not something an analysis can repair.

## Unsupported parts (additions to report.md)

| Subtask | Why the toolkit could not do it | What was used | Check |
| --- | --- | --- | --- |
| Reading the paper and aligning it with the archive | Outside the toolkit | Manual reading; candidate offset | Nine printed sums reproduced exactly; zone boundaries; Codex's independent reading |
| Removing the six sedge and aquatic columns | The study layer cannot delete taxa | `amend_source.py` | API validation; m = 272 confirmed |
| Comparing definitions | Reporting arithmetic | `compare_definitions.py` (SciPy Spearman) | Same 77 pairs and seed in both runs |

**Not repeated for the amended table:** the R cross-check. The operations and
code paths are those already checked to within 3.5 × 10⁻¹³ on the
66-category table. Only the input matrix differs.

## Toolkit

No defects. The amended runs verified on inspection, and the original
results.json still replays byte for byte from fresh runs after the scripts
were parameterised.

## Where this leaves the research question

- **Robust to how the record is read:** the count-level findings. These
  are which steps exceed counting noise, which taxa carry them, and where
  pollen-category richness is low or high. They hold under both
  definitions and are tied to depth and sample ID.
- **Not yet answerable from these archives:** anything temporal, including
  the 45–38 ka question. Answering it needs either:
  1. a corrected sample-to-control depth alignment and a rebuilt age model
     that uses all the paper's dating evidence, including the reversed
     deeper dates, the U-series composite and their stated limits; or
  2. the TAS1402 cores, with their own multi-method chronology (Fletcher et
     al.), which would be a new application.
- **What should happen next:**
  - **Report the archive defects to Neotoma and the IPPD:** the +30 cm
    depth offset between samples and chronology controls, and the
    *Lagarostrobos* omission at 220 cm. That is outward-facing, so it waits
    for Barry.
  - **Rebuild the age model:** the next scientific step, outside the
    toolkit's scope.
