# Lake Selina: amendment 1, driven by the source

Claude (Opus 5.5), 8 November 2026. This is a **post-result** amendment. The
design frozen at 42c5a1b and its results at 6b9611f stay as they are: they
are the record of what was done before the full Colhoun et al. (1999) paper
was available. This amendment follows Codex's
[source review](COLHOUN1999-SOURCE-REVIEW.md). Every change below is taken
from the paper, not chosen in response to results. It is committed before
the amended analysis is run.

**The paper.** Colhoun et al. (1999), *Quaternary International* 57/58, 5–23,
[10.1016/S1040-6182(98)00046-9](https://doi.org/10.1016/S1040-6182(98)00046-9).
I read it myself from the PDF that Barry supplied (SHA-256 `601cc99e…f0cae`,
matching Codex's copy). The PDF is not redistributed.

## What I verified in the paper

**Core geometry** (section 3, printed p. 8):
- The long Mackereth core is 347 cm long. Its top was assigned 50 cm,
  because the corer missed the surface sediment.
- A separate 40 cm short core recovered the surface, with an assumed 10 cm
  gap between the two cores.
- The composite record runs 0–397 cm, and the long core 50–397 cm.

**The offset.** The archive's pollen levels span 80–427 cm, also exactly
347 cm. Under a **+30 cm archive offset** (archive depth = paper depth + 30),
the evidence lines up:
- **Pollen sums.** The archive totals under the paper's dryland rule (below)
  reproduce nine consecutive printed sums at paper depths 70–110 cm: 338,
  335, 302, 329, 323, 344, 351, 324 and 337. I recomputed these from
  `data/counts.tsv`.
- **Zones.** The paper's herb zone LS8 (125–170 cm) maps to archive
  155–200 cm, where the archived herb maximum lies. LS9, the rise of
  rainforest taxa from near 0 to 46 % (105–125 cm), maps to archive
  135–155 cm.
- **Dates.** The 14,200 ± 230 ¹⁴C yr BP date "dates the commencement of
  deposition of the surface organic-rich mud" at paper 123–127 cm, which is
  archive 153–157 cm, the start of forest recovery. The paper takes the
  150 and 165 cm AMS dates as "good estimates" of maximum cold, and those
  are archive 180 and 195 cm, in peak herbfield.

**The archived chronologies keep the controls at paper depths**: 125, 150,
165, 230 and 295 cm. If the pollen samples carry the +30 cm offset, every
archived age is attached to a level about 30 cm away from the sediment
actually dated. That accounts for the "early forest recovery" anomaly in the
stage-2 report without invoking old carbon. That diagnosis is withdrawn.

**One unresolved discrepancy.** The paper describes and plots a strong
*Lagarostrobos* peak at 190 cm (zone LS7). The archive level at 220 cm
(531331) has no *Lagarostrobos* entry, and its dryland total is 408 against
a printed sum of 480. The residual of 72 grains is consistent with an
omitted *Lagarostrobos* count, but that is a hypothesis. No count is
invented. Level 531331 is kept, and the two steps that touch it (215→220
and 220→225 cm) are flagged as provenance-uncertain.

**The universal offset is supported, not proved.** Archive coordinates and
sample IDs stay primary. The candidate paper depth is reported beside them.

**The dating evidence omitted from the archived models** (pp. 8–11):
- conventional ¹⁴C dates at 352–355 and 395–397 cm, reversed (younger
  below), which the authors attribute to humic-acid contamination;
- a U-series composite of 160 ± 20 ka from samples at 283, 323 and 375 cm.
  This is a grouped estimate, not three point dates;
- correlation-based ages from magnetic intensity and the woody/herb ratio
  (Table 2). These are not measured ages, and they are not independent of
  the pollen succession.

## Amended design

1. **Denominator: the paper's dryland pollen sum.** Pollen of sedges and
   aquatic plants is excluded, as the paper's methods specify. That removes
   six columns the stage-1 intake kept, following the paper's Figure 6
   groups:
   - sedges: Cyperaceae, *Gymnoschoenus sphaerocephalus*, Restionaceae,
     Xyridaceae;
   - aquatics: Portulacaceae, *Ranunculus*.

   The result is 72 levels and **60 categories**. The smallest total is
   **272** (531362, archive 370 cm), so **m = 272**. This is a defensible
   dryland rule, not an exact reconstruction of Figure 6: some printed sums
   appear to include treefern spores (Codex's review), and the 220 cm
   residual is unexplained.
2. **Pairs and settings are unchanged:** the same 77 sample-ID pairs, in the
   same order (which fixes the random streams), with B = 99,999 and seed
   7112026. The denominator is the only difference from the original run.
3. **Temporal interpretation is suspended.** No ages are reported. The
   three "named" pairs are reported only as fixed archive-ID contrasts, with
   archive and candidate paper depths, until the sample-to-control alignment
   is resolved. Withdrawn from the stage-2 report:
   - the historical and climatic labels;
   - the agreement with Turney et al.'s reading near 41 ka;
   - the diagnosis that the dates read too old.
4. **Reporting rules are unchanged** from INTAKE.md: the Holm envelope,
   separate ranks, the forward sign (shallower minus deeper, now stated by
   depth, not age), and no reruns.
5. **The original 66-category run is kept as the archived-definition
   sensitivity.** The amended report states, for each headline quantity,
   how the dryland result differs from it.

**Unsupported parts added:**
- reading the paper and joining it to the archive;
- the six-column exclusion, because the study layer cannot delete taxa;
- the offset annotation.

All are declared. The supported analyses again run through the toolkit.

Reproduce from the repository root:

```bash
uv run analyses/lake-selina/amend_source.py
uv run analyses/lake-selina/run_api.py design-amended.json
uv run analyses/lake-selina/analysis.py design-amended.json
```
