# Lake Selina: source review of Colhoun et al. (1999)

Codex (`gpt-6.1-sol`), 8 November 2026. This reviews the supplied full paper
against the stage-1 intake at `42c5a1b` and the stage-2 report at `6b9611f`.
It does not change or rerun that analysis. The completed frozen run remains
the record of what was done before the full paper became available.

**Decision:** the archived counts support a conditional analysis of the
retained categories, but the report's temporal interpretation needs revision.
The archive-to-paper depth alignment is a concrete alternative to the
report's early-forest-recovery versus old-carbon explanations. The 66-category
sum also differs from the paper's stated dryland pollen sum. Reconcile these
before presenting the named comparisons as historical or climatic tests.

## Source and verification

Colhoun et al. (1999), *Quaternary International* 57/58, 5–23,
[DOI 10.1016/S1040-6182(98)00046-9](https://doi.org/10.1016/S1040-6182(98)00046-9).
The supplied 19-page PDF has SHA-256
`601cc99e4e45b5e4108b1a09de3865d9492c12495e28dfd1922e3c7f572f0cae`.
Printed page numbers below are four greater than PDF page numbers. Relevant
methods, core stratigraphy and Figure 6 panels were checked visually as well
as by text extraction. The original PDF and page images are not redistributed.

The full toolkit primer was read before this work; its current SHA-256 remains
`cdec09d1ab058224869120b2ac6de406be62df6ed112373dfa1057492971f765`.
PDF interpretation, archive joins, category filtering and comparison with
printed counts are unsupported source-audit tasks. Public API preflight
validation was used for the candidate filtered tables; no community,
rarefaction-estimate or homogeneity run was performed for this review.
An independent source reader checked the pollen groups and denominator.
The [validation receipt](source-review-validation.json) records the input and
candidate hashes and the in-memory public `validate_rarefaction` result.

## Counting protocol and the analysis denominator

Section 5 (printed p. 11; PDF p. 7) specifies 1 cm³ samples at 5 cm intervals,
Lycopodium tablets for processing control and concentration, Faegri–Iversen
processing, and microscopy at 200× with higher magnification for identification.
Its stated counting target is more than 300 dryland terrestrial grains.
Sedges, aquatic pollen, fern/moss/lycopod spores and fossil algae are excluded
from that sum. Figure 6 itself prints some totals below 300 (p. 15), so the
prose target must not be imposed as a data-cleaning threshold.

The source's group boundaries in Figure 6 (p. 16; PDF p. 12) place six columns
currently retained by the TRSH/UPHE rule outside the dryland sum:

| Source group | Currently retained archive labels |
| --- | --- |
| Sedges | Cyperaceae; Gymnoschoenus sphaerocephalus; Restionaceae; Xyridaceae |
| Aquatics | Portulacaceae; Ranunculus |

These are the paper's operational groups, not a claim that all four sedge
labels belong to Cyperaceae. Other plotted aquatic and spore categories are
already excluded by the frozen intake. Regional ecological importance does
not make these six categories members of the paper's counting denominator.

Excluding all six from the archived table gives a **candidate** 72-level,
60-category dryland table. API preflight confirms a smallest retained total
of 272 (sample 531362, archive depth 370 cm). A corresponding equal-count
analysis would use m = 272, not 282. Excluding just Cyperaceae and
Gymnoschoenus leaves 64 categories and m = 282; excluding the four source
sedges leaves 62 and m = 272. Neither partial exclusion reproduces the full
stated rule.

**This candidate is not an exact reconstruction of the published sum.**
Some Figure 6 totals appear to include treefern spores despite the blanket
exclusion in the methods: the residuals at paper 50, 55 and 65 cm are exactly
the archived Dicksonia counts (4, 3 and 1), while the residual at paper
115 cm equals the archived Cyathea count (1). Other discrepancies remain
below. Specify a defensible dryland analysis rule and distinguish it from
reproducing Figure 6. Preserve the original 66-category run as an archived
definition or sensitivity, with a source-driven amendment recorded after
stage 2; do not relabel it as the original authors' pollen sum.

The paper does not establish that every absent archived datum was searched
for and observed as zero. The Neotoma zero-fill convention remains a
conversion convention. Its reference to other Proteaceae alongside named
genera (p. 12) supports residual broad categories, but is not a complete
category-by-category proof of disjointness.

## The 397 cm versus 80–427 cm discrepancy

Section 3 (p. 8; PDF p. 4) describes a **347 cm long core**, whose top was
assigned depth 50 cm because the Mackereth corer missed the surface sediment.
A separate 40 cm short core recovered the surface record. Thus 387 cm was
recovered, with an assumed 10 cm gap between the short and long cores.
The composite record spans 0–397 cm; the long core spans 50–397 cm.

The archive's 80–427 cm interval also spans exactly 347 cm. A +30 cm archive
offset is therefore a specific hypothesis, rather than a discrepancy in
recovered core length. **Nine consecutive printed pollen sums support it:**

| Paper depth (cm) | Archive depth (cm) | Printed sum = six-exclusion archive total |
| --- | --- | --- |
| 70 | 100 | 338 |
| 75 | 105 | 335 |
| 80 | 110 | 302 |
| 85 | 115 | 329 |
| 90 | 120 | 323 |
| 95 | 125 | 344 |
| 100 | 130 | 351 |
| 105 | 135 | 324 |
| 110 | 140 | 337 |

The upper forest succession and herb-rich interval also align broadly under
this shift. However, a universal coordinate correction is **not yet proved**.
The paper explicitly describes and plots a strong Lagarostrobos peak at
190 cm (pp. 13, 17). Archive depth 220 cm has no Lagarostrobos entry, and
its candidate dryland total is 408 against a printed sum of 480. Treeferns
do not explain that residual. This could involve archive omission, source
plotting error or another provenance problem; the present evidence cannot
choose among them. Resolve it rather than silently inventing counts.

The two archived chronologies retain the paper's radiocarbon depth numbers
(125, 150, 165, 230, 295 cm) while pollen samples show evidence of the +30 cm
offset. That creates a possible sample-to-control misalignment. IPPD-2 also
anchors age zero at archive depth 80 cm, although the corresponding long-core
top would be paper depth 50 cm under this interpretation, not the surface.
Confirm the original depth convention and any transformations applied to
both samples and controls before applying a correction or rebuilding ages.

## What the full dating discussion changes

- **The paper's 125 cm date is not in the reported forest spectra.** Its
  Figure 6 places 125–170 cm in the herb-dominated glacial zone LS8; the
  150/165 cm AMS dates are explicitly interpreted as good LGM estimates
  (pp. 9, 13, 17). Archive 125 cm instead matches paper 95 cm by pollen
  sum. Directly comparing those two 125 cm labels cannot establish that
  forest returned unusually early or that the bulk date is too old.
- **There are deeper dating attempts.** Conventional radiocarbon samples
  were also taken at 352–355 and 395–397 cm. Their approximately 42.43 and
  30.12 ka ages reverse below the 52.11 ka assay at 294–296 cm. The authors
  attribute the young reversals to downward humic-acid contamination
  (p. 8). Describe these as unreliable deeper dates omitted from the
  archived models, rather than saying the original lower core has no dates.
- **U-series supplies additional, limited evidence.** Six samples were
  attempted. The upper three failed because of open-system behaviour.
  Samples at 283, 323 and 375 cm were combined in a corrected composite
  estimate of 160 ± 20 ka (pp. 9–10). This is not three independent point
  dates; the correction groups samples as approximately coeval. It is not
  an age-depth model ready to substitute for Bacon.
- **The authors considered some older radiocarbon ages too young.** They
  allow the 33,800 ± 1,100 assay at 230 cm to be older, and place the
  240–270 cm herb phase in MIS4 by magnetic/vegetation correlation. Table 2
  assigns correlation-derived estimates of 57.65 ka at 230 cm and 83.25 ka
  at 295 cm (pp. 9, 11). These are not measured ages or independently
  calibrated controls. Pollen-based climatic correlation cannot independently
  validate a test of the same pollen-climate succession.

## Consequences for the next analysis and report

1. Preserve `42c5a1b`/`6b9611f` and their results. Record the full-paper
   findings as a post-result, source-driven amendment. Nothing here changes
   the claim that the original design was frozen before results existed.
2. Correct the core geometry and denominator descriptions. Resolve the
   source-figure inconsistencies; declare the revised category rule explicitly
   before rerunning supported analyses through the toolkit.
3. Suspend historical/climatic interpretation of all named age-window pairs
   until sample/control alignment is resolved. They can remain identified
   as fixed archive-ID contrasts. Remove the claimed agreement with Turney's
   approximately 41 ka interpretation while their temporal placement is
   unresolved, and replace the two-explanation chronology diagnosis with the
   source evidence above.
4. Retain depth order, sample IDs and raw archive coordinates explicitly.
   A uniform shift would preserve adjacency, but denominator changes alter
   distances, richness, conditional tests and multiplicity results. The
   current 41/71 finding and coverage values therefore belong to the original
   66-category run until checked under the amended rule. Coverage describes
   the retained counting distribution; it does not validate its membership,
   chronology or the absence-to-zero assumption.
5. Resolving archived curation and dating provenance is the next scientific
   task. Regional chronology comparison can follow; it should not be used
   first to explain an apparent anomaly that coordinate mismatch may create.

This is a primary-source review of design and interpretation, not an
independent rerun or certification of all stage-2 numerical results.
