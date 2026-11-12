# Application 5: frozen Lake Selina zonation design

Codex, 12 November 2026. Implements the question accepted in Board 3246 and
[the proposal](../../docs/application-5-proposal.md). This file, `study.json`,
`plot-study.json`, `context.json`, `input-lock.json` and their input tables
must be committed before execution. **No core hierarchy, broken-stick curve
or selected zone count has been computed before this freeze.**

Sprint 14's arithmetic was accepted after independent review. Both saved-record
repairs at `c38696d` are confirmed: all three adversarial cases are refused,
live MCP still reproduces exactly, and the historical review receipt is
preserved. The actual confirmation is in `repair-check.json`.

## Fixed comparison

Keep the previously agreed four CONISS analyses, all 72 levels, the 60-category
dryland sum, equal sample weights and strictly increasing archive depths:

| Analysis ID | Counts | Coordinates |
| --- | --- | --- |
| `archive_hellinger` (primary) | Archived | Square roots of exact row proportions, rounded once |
| `repaired_hellinger` | Working reconstruction | Same |
| `archive_relative` | Archived | Exact row proportions, rounded once |
| `repaired_relative` | Working reconstruction | Same |

Every result uses the exact Ward hierarchy and strict broken-stick passing
prefix from contract revision 2.1. No filtering, rarefaction, taxon merging,
rarity threshold, alternate linkage, alternate denominator or k search is added.
Read every requested cut from the API's `split_rank` fields. Compare each
run's chosen partition and its cut at the primary run's chosen k.

Persistence means the same two sample IDs. Unmatched sensitivity boundaries
receive a descriptive nearest primary gap by gap-index distance, ties to the
shallower gap. Report signed gap-index shifts and the shift of each bracketing
depth, positive deeper. Associations can be many-to-one and do not establish
event identity. With a one-zone primary, no matching is forced.

## Data and prior knowledge

The input hashes are in `input-lock.json`. Intake uses `neotoma_extract` with
explicit dataset 52767, pollen/NISP/TRSH/UPHE, absent taxa zero and depth order.
The study drops the six previously declared sedge/aquatic categories. The
reconstructed table is copied unchanged from application 1 amendment 2;
the only difference is the inferred 72 Lagarostrobos grains at 531331/220 cm.
This is a sensitivity, not a verified correction to the archive.

`prepare.py` performed extraction, joins and column exclusion through the
API. Its preflight called only `validate`, with zonation guarded against
execution. All four inputs pass as 72 levels × 60 categories, with no
exclusions or warnings. `data/positions.csv` projects only the sample ID and
archive depth from extractor metadata, checked against the original levels.
No age field enters either study.

The earlier spectra, tests and source-paper interpretations have been seen.
This is a prospective computation on reused data, not independent ecological
validation. `context.json` locks the seven plotted categories and two already
reviewed source-paper landmarks (LS8 and LS9 under the candidate +30 cm
archive alignment). They are interpretation context, not target boundaries.
No complete published zonation is being reconstructed or scored.

## Supporting figure data and verification

The main study contains exactly four analyses. A **separate supporting
`plot-study.json`** runs `community` once on the same archived dryland table
to obtain API-native row proportions for the pollen figure. Its distance
(Bray–Curtis) and three PCoA dimensions reuse the earlier descriptive setup;
no ordination or diversity result becomes another scientific comparison.
This graphics-only operation is declared before results because the suitable
API must supply percentages. Its derived table must match the primary table
byte for byte. Report its warnings even though only composition is plotted.

The depth-aligned figure uses the seven categories fixed in `context.json`,
the four selected zone columns and the primary cumulative-SS dendrogram.
A line at a bracket midpoint is only drawing geometry. Boundary tables keep
both observed depths and IDs. No ages, event dates, durations or causal
attributions are reported; no post-selection significance test is run.

After execution, inspect every native bundle and reproduce both studies from
copied bundles in a fresh worker with original application paths blocked.
Require byte-identical child result files. Independently establish the canonical
coordinate rounding, then compare matched-coordinate clustering, cumulative
SS, broken-stick values and all k cuts against pinned rioja 1.0-7. Numerical
agreement does not establish ecological truth or boundary uncertainty.

Supported preparation, clustering and descriptive plotting quantities use the
API. External work consists of metadata column projection, the declared
boundary correspondence/offset reporting, scientific interpretation, plotting
geometry and independent reference arithmetic. No supported analysis is
recomputed for reporting.

Run `uv run analyses/lake-selina-zonation/analysis.py` only after this freeze
is committed. Reproduction and reference scripts, plus their receipts, accompany
the final report. A result with one zone or unstable boundaries is a complete
answer; do not change the model to obtain the expected vegetation succession.
