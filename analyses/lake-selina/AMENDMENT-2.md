# Lake Selina: amendment 2, working repairs for the case study

Claude (Opus 5.5), 8 November 2026. Barry, through the board, 8 November
2026:

> "this is an example dataset, not a new published analysis. Infer or
> interpolate any data issues and press on. … if in doubt, fix as best you
> can an press on."

The two archive–paper discrepancies left open by amendment 1 are therefore
repaired by inference, not by asking the curators. The curator query draft
is not to be sent. Amendments 1 and 2 and their results stay in the record.

## Repairs

1. **Missing *Lagarostrobos* at 220 cm.** 72 grains of *Lagarostrobos
   franklinii* are imputed at 531331 (archive 220 cm). That is the printed
   sum (480) minus the archived dryland total (408), at the level where the
   paper plots a strong *Lagarostrobos* peak. The archive's peak at
   395–427 cm reaches 78 grains, so 72 is within the observed range.
2. **Inferred age model under the +30 cm alignment.**
   - Paper depth = archive depth − 30 cm for every sample.
   - Controls sit at their printed paper depths, 125, 150, 165, 230 and
     295 cm, plus the surface (0 cm, 0 cal BP).
   - Each control's calibrated age is the age the archived model gives at
     that depth label, where the control dominates the fit: 17,130, 21,876,
     23,132, 38,061 and 51,836 cal BP (IPPD-2, Bacon).
   - Ages are interpolated linearly between controls. Samples deeper than
     paper 295 cm (archive 330–427 cm) stay depth-only, as in stage 1.
   - The alternative chronology applies the same rule to the IPPD-1
     (IntCal09 best-fit) control ages: 17,562, 25,017, 29,457, 40,183 and
     50,587 cal BP.
3. **Named endpoints are reselected** with the stage-1 bracket rule on the
   inferred ages, for the same three windows. The count-homogeneity family
   is the 71 adjacent steps plus the new named and alternative-chronology
   pairs: 76 pairs, with the same B and seed and the adjacent pairs first.
   The random streams for the adjacent steps are therefore unchanged.
4. **m comes from the API.** It is the `minimum_total` validation receipt
   (272), which closes the primer lapse in amendment 1.

The dryland definition from amendment 1 is unchanged.

## What this is

It is a plausible working reconstruction for exercising the toolkit, not a
corrected record. The age model is deliberately simple: linear, one curve,
and no reservoir or contamination modelling. The reversed deeper dates and
the U-series estimate are not used.

Reproduce from the repository root:

```bash
uv run analyses/lake-selina/amend_final.py
uv run analyses/lake-selina/run_api.py design-final.json
uv run analyses/lake-selina/analysis.py design-final.json
```
