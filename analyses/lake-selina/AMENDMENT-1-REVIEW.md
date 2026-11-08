# Lake Selina: review of amendment 1

Codex (`gpt-6.1-sol`), 8 November 2026. Reviewed amendment `9a2ee8f` and
analysis/report `6c934f9`. This review leaves their files unchanged.

**The amended calculations pass. The interpretation needs the focused
corrections below.** No statistical rerun or engine change is needed to
make those corrections. The source-informed dryland definition is defensible,
the original record is preserved, and suspending the temporal comparisons
is the appropriate response to the unresolved coordinate provenance.

## Verified calculations

The [check receipt](amendment-1-review-checks.json) records these checks:

- Scratch regeneration reproduces `counts-dryland.tsv` and
  `design-amended.json` byte-identically. Only the six declared columns are
  removed; retained cells, sample IDs and order are unchanged.
- The 77 pairs and their order, B = 99,999, seed 7112026 and reporting rules
  match the original design. All five public validation receipts match;
  the five saved runs and comparison pass API inspection.
- Fresh API execution and postprocessing reproduce **the entire amended
  results file byte-identically**, SHA-256
  `3b2779413c464a7b4f42ed2cb403efff1554ccb9f1dd1c81ced4ca7e07fd8a47`.
- Replaying `compare_definitions.py` in scratch reproduces
  `definition-sensitivity.json` byte-identically.
- **The amended R cross-check is now done:** 681/681 checks agree; maximum
  absolute difference is 6.24389429049188 × 10⁻¹³. This uses the unchanged
  `reference.R` and `cross_check.py`, substituting the amended table/design
  into their expected scratch filenames. The R record confirms m = 272 and
  the amended input hash. R 4.6.1, vegan 2.7.6 and the pinned iNEXT source
  are recorded in the receipt. Checks cover per-sample diversity,
  rarefaction/coverage, all three distance matrices and named-pair Fisher
  tests. They do not independently test the omnibus Monte Carlo algorithm.

The full primer was read; its version/hash are in the receipt. Supported
recomputation and integrity checks used the public API. Scratch layout,
source comparison, replay comparison and reporting arithmetic are review
glue; R calculations are the primer's permitted independent cross-check.
Independent reviewers checked mechanical reproduction and source interpretation.

## Corrections required in the report

1. **Keep the provenance diagnosis conditional.** The nine exact sums and
   zone correspondences strongly support a +30 cm sample offset. They do
   not establish every archived coordinate or prove where the error arose.
   `AMENDMENT-1.md` lines 42–46 and `report-amended.md` lines 36–38 should
   say that the candidate alignment removes the basis for diagnosing early
   forest recovery or old carbon, rather than claim that misalignment is
   established. The largest step adjoins/overlaps the paper's dated
   123–127 cm interval **under this candidate alignment**; it is not itself
   a precisely dated event. Describe the two issues as archive–paper
   discrepancies to reconcile, not confirmed archive defects or a proven
   Lagarostrobos omission (report lines 134–135, 169–171).

2. **Distinguish the 41 point-estimate rejections from the diagnostic.**
   Of 71 adjacent pairs, 41 have Holm-adjusted plus-one p < 0.05. Under
   the predeclared envelope, 40 have the whole envelope below 0.05,
   four contain 0.05, and 27 are wholly above it. The 185→190 cm pair is
   both a point-estimate rejection and diagnostically unresolved. Label
   the table's 41 as point-estimate rejections, rather than describe all
   41 unconditionally as resolved beyond counting noise. This preserves
   the frozen decision rule; the envelope remains a sensitivity diagnostic,
   not simultaneous confidence coverage or a replacement rejection rule.

3. **Separate the descriptive LS7 episode from taxon resolution.** Report
   lines 113–116 call the expansion of three taxa at 255–260 cm resolved.
   There is support for a composition episode bounded by resolved omnibus
   steps, but not a resolved change in all three individual taxa:

   | Archive pair (cm) | Holm p | Diagnostic | Individual taxa passing the global taxon Holm family |
   | --- | --- | --- | --- |
   | 247→255 | 0.00132 | envelope below 0.05 | none |
   | 255→260 | 0.0522 | unresolved; envelope 0.04446–0.06023 | none |
   | 260→265 | 0.00077 | envelope below 0.05 | Nothofagus gunnii |

   State that the elevated N. gunnii, Pherosphaera and N. cunninghamii
   values correspond descriptively to the source's near-base LS7 peak.
   Name the resolved bounding steps and the supported taxon separately.

4. **Narrow the robustness claim.** Report lines 157–160 overstate what
   unchanged totals and high rank correlations establish. The valid claim
   is aggregate and rank stability under these **two category and
   subsample-size definitions**. Two step classifications change; taxon
   attributions also change. For example, Pherosphaera at 155→160 cm passes
   taxon Holm only in the amended run (p = 0.02280), joining Poaceae and
   N. gunnii. Nothing here establishes robustness to missing counts at the
   flagged level. Because membership and m change together, this comparison
   does not isolate their separate contributions. Use source-informed
   dryland definition and candidate depth alignment consistently; the source
   figure/prose inconsistencies remain unresolved.

## Small toolkit-use correction

`amend_source.py` lines 35–36 recompute totals/minimum with bespoke Python.
The six-column filtering is unsupported preparation, but the resolved minimum
is available from public rarefaction validation with
`sizes="minimum_total"`. Use that receipt for m on future regeneration.
The current m = 272 is API-confirmed, so this is a literal primer-rule lapse,
not a numerical disagreement. It does not warrant changing the engine.

## Next scientific action

Prepare an unsent curator query with the original source pages, nine matching
sums and the missing-peak discrepancy. Ask which depth conventions and
transformations were applied, and request reconciliation of the 190/220 cm
level. Do not identify either source as proven wrong or infer 72 missing
Lagarostrobos grains as a recovered observation. No outside contact was made
or authorized by this review.

The depth/counting provenance should be resolved before choosing an age-model
repair. A new model should evaluate the reversed radiocarbon assays and
grouped U-series evidence under their respective validity limits; it should
not automatically treat every dating attempt as a usable point control.

After these report corrections, the present tranche can close as a verified,
conditional count-table analysis with unresolved temporal provenance.
