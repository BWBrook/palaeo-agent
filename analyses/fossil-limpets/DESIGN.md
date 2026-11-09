# Fossil limpet shell scaling and measurement-method sensitivity

Codex, 9 November 2026. **Pre-results design, awaiting Claude's review.**
This implements [application 4](../../docs/application-4-proposal.md).
No toolkit analysis is authorised to run until that review is complete.

## Question and intended claim

How does shell width scale with shell length among the archived fossil
*Lottia edmitchelli*, and how sensitive is that description to using calipers
or automated outline axes on the same individuals?

The primary target is the descriptive log–log reduced-major-axis (RMA)
exponent for caliper width against caliper length. The prespecified
sensitivity uses AutoMorph minor against major axis. A value above or below
1 describes relative widening or narrowing with size in this sample. It
does not establish a statistically supported departure from isometry.
Correlation and specimen scatter accompany every exponent: an RMA slope
can have a substantial magnitude even with weak association.

This is cross-sectional scaling in a single archived fossil sample. It is
not an individual growth trajectory, a temporal trend, or a population-wide
estimate of ontogenetic allometry. The two methods measure the same shells;
they are not independent biological samples or replicates of a population.

## Frozen source and specimen identity

- Dataset: Hsiang and coauthors, [Measurement verification data for AutoMorph
  vs. hand measurements](https://zenodo.org/records/1002768), fixed record
  DOI **10.5281/zenodo.1002768**. All creators are credited in
  [source/source.json](source/source.json).
- One unchanged measurement download:
  [STable1_2DLimpets.csv](source/STable1_2DLimpets.csv), **9,416 bytes**.
  The Zenodo API declares **CC BY 4.0**. The source card records the direct
  download URL, attribution, licence and registered MD5 checksum.
- SHA-256:
  `481c968bebeb96716ae03623361aebb2c6d64e1ee636f30e5406d1a3071285fe`.
- **136 unique ObjectIDs**, one sample label:
  `Edmitchelli_LAMNH12577_lot_4`. These object IDs identify matched shells;
  they are not individual museum accession numbers. The exact original
  label is preserved, including its `LAMNH` spelling.
- The [source supplement, pp. 7–8](https://finneganlab.org/wp-content/uploads/2024/08/hsiang-et-al-2018-supplemental.pdf)
  identifies fossil *L. edmitchelli* from a San Nicolas Island Pleistocene
  terrace, LACMIP locality 12577. Shells were matched visually to AutoMorph
  object images before caliper measurement. Individual matching is accepted
  from the archive; the images and physical shells are not re-examined here.
- The supplement describes **139** shells, whereas this CSV has **136**.
  The difference is unresolved. Analyse only the frozen records, state the
  discrepancy and make no claim to have recovered all original individuals.

Selection used source identity, accessibility, licence and structural
feasibility. A Pentland Hills brachiopod workbook was considered but could
not be downloaded anonymously. Bounded PBDB queries did not offer an equally
useful same-species, paired-method sample. No candidate's allometric fit or
association was computed to choose this dataset.

## Intake and cohort

Run `uv run analyses/fossil-limpets/intake.py` from the repository root.
It checks the exact source hashes and copies all four measurement columns
as their original decimal text into [measurements.tsv](measurements.tsv),
using `ObjectID` as the first-column row identifier. It writes the original
sample label and CSV row number into [specimens.csv](specimens.csv).

All four source measurements are present, finite and positive on every row;
their headers explicitly specify millimetres. Keep all 136 records, in source
order, for both fits. There are no row exclusions, missing-value replacements,
size cutoffs, data-driven outlier removals, rescalings or taxon merges.
Identical rounded dimensions, if warned about by the toolkit after launch,
will be retained as different labelled specimens. Do not infer a missing
dimension from the other dimension if a future source amendment is needed.

The study has one `measurements` input and one derived dataset. Specimen
provenance stays separate: RMA has no metadata argument, although the study
can attach metadata for other methods. The source label is a lot identifier,
not an analytical grouping variable. No unused study filters are added.

## Fixed analyses

[study.json](study.json) contains exactly these two analyses of the same
dataset, both with `method: rma`, `format: past`, `transform: log10` and
`missing: error`:

| Role / analysis ID | x | y |
| --- | --- | --- |
| Primary: `caliper_log` | `Length_Caliper_mm` | `Width_Caliper_mm` |
| Sensitivity: `automorph_log` | `MajorAxisLength_AutoMorph_mm` | `MinorAxisLength_AutoMorph_mm` |

Use toolkit `run_study`, `inspect_study`, `inspect_run` and
`reproduce_study`; report numbers only from verified result fields.
Lead with `correlation`, `slope`, `intercept`, `n` and the specimen scatter,
then `vertical_residual_rmse`, exclusions and every warning. Both log–log
axes use base 10. The log intercept is the fitted log10 width at length
1 mm and may be extrapolative; it is not a raw width/length ratio.

Show the two fitted relationships side by side, using the same specimens,
scales and identity labels. Keep units and measurement definitions visible.
The toolkit's scatter and residual plots are the primary diagnostics; any
combined figure only reformats its saved pairs and fitted fields. Do not fit
caliper-versus-AutoMorph calibration regressions, try alternative transforms,
search size thresholds, or select a preferred method based on these results.

Describe whether the exponent's position relative to 1 changes between the
two measurement definitions. There is no declared threshold of acceptable
method agreement, no hypothesis test, and no claim that either method is
measurement truth. Preserve a weak, null, discordant or refused result.
No p-values or multiple-testing family are generated.

## Checks, reporting and stopping condition

Before review, use only source/identifier checks, `StudySpec` and `RmaSpec`
schema validation and the toolkit's pure `read_table`/`derive` preparation.
**Do not call RMA `validate` before the freeze:** its implementation computes
the fit even though its response omits the fitted coefficients.
[intake-check.json](intake-check.json) records the preparation, specimen list,
schemas and hashes. It contains no fitted values or association summaries.

After review, run the fixed study, inspect it and reproduce it in a fresh
process after removing any dependence on the original input paths. Compare
both child result records and derived input bytes. Cross-check the supported
arithmetic independently in R on the same saved pairs and log10 convention:
slope, intercept, correlation, means, sample SDs and vertical residual RMSE,
with absolute and relative tolerances of 1e-10. This is a numerical check,
not a new analysis or evidence of scientific validity. Report API values.

The report will contain a two-row fit table, both scatter/residual views,
specimen counts and warnings, the source discrepancy, the unsupported-parts
table below, and bundle/field provenance for every result. It will state
that preservation, collection and selection into a method-verification set
can affect the observed size–shape relationship; there is no representative
sampling design or repeated-measurement error estimate.

Stop after that report, successful reproduction and arithmetic check, and
one focused scientific review. A change to the cohort, measurement definitions
or fitting plan requires a recorded amendment before its new results are
computed. An engine refusal is recorded and reviewed, not bypassed by bespoke
regression code. Toolkit gaps become the next development proposal.

## Unsupported parts

| Subtask | Why the toolkit could not do it | What is used instead | How checked |
| --- | --- | --- | --- |
| Select `ObjectID` as the CSV row key and separate the sample-label column | No intake operation rearranges this source layout into a measurement table | `intake.py`, copying original strings without calculating measurements | Source SHA-256 and registered MD5; every output ID and cell compared to the source; toolkit table read-back and pure preparation |
| Interpret fossil provenance, the two measurement definitions and 139/136 discrepancy | The API does not interpret source documentation | Source methods and archive metadata, with unresolved points retained | Supplement pp. 7–8 visually checked; archived sample label and per-object identities preserved |
| Pure pre-results positivity/missingness checks | RMA `validate` computes a fit, so it cannot preserve this stage's no-fit boundary | Source CSV field/Decimal checks and schema validation | Exact frozen file, all four fields checked, and preparation read-back; no fit function called |
| Isometry inference, confidence intervals and a paired test of slope differences | RMA is descriptive and provides no such inference | Declined in this application | Method catalogue and contract; conclusions confined to the two sampled relationships |
| Independent arithmetic verification | Independent verification is outside the analysis API | A separate R check after launch, using saved pairs only | Fixed conventions and 1e-10 absolute/relative tolerances; discrepancies investigated before reporting |

## What was seen before the freeze

No new RMA fits, correlations, SDs, ratios, tests, scatterplots or residuals
have been computed. Source measurements and structural feasibility were
inspected. The scout and Codex encountered the authors' published
caliper-versus-AutoMorph calibration results while checking methods. Those
are different regressions from the two length–width fits specified here;
this is not a blinded study or an independent validation of AutoMorph.

Primer version **0.2.0.dev0**, SHA-256:
`089a91663185ebff31e358a7e4c5f34e899336d1d1f26c0032f7a17f54c49e99`.
Design prepared against toolkit commit `52187c6`; the design/source commit
is the immutable review reference. No runtime is launched until Claude
reviews this design.
