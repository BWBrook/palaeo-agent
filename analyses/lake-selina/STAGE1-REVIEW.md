# Lake Selina: review of the stage-1 freeze

Codex (GPT-6.1 Sol), 8 November 2026. Reviewed `02db7b5`, the saved Neotoma
responses, intake code, derived tables, design and method contracts. Two
bounded reviewers checked computational integrity and statistical design
separately. No composition, richness estimate, ordination or test result
was computed during the review.

## Decision

The count-analysis design is suitable. Retain the 72 levels, archived
66-category denominator, m=282, six named/sensitivity comparisons, all
77 declared pairs, B=99,999 and seed 7112026. Keep the IPPD-1 sensitivity
pairs in the same two Holm families as the other comparisons. They were
declared before results and should not be selected or separated according
to their eventual significance.

Before stage 2, record the operational Monte Carlo flag and the reporting
clarifications below, and correct the source-assumption wording. These do
not require changing the count matrix, endpoints, simulation allocation or
scientific question. Once these specified amendments are committed before
results, proceed with the API analysis; another review round is unnecessary
unless the amendments uncover a different substantive problem.

This accepts analysis of the archived count table under its stated intake
assumptions. It does not establish the original counting protocol, the
validity of either age model or the timing of a historical event.

## Computational integrity

- Both source responses match the pinned hashes.
- A scratch copy of `intake.py` regenerates `design.json` and all three
  derived data files byte for byte. The checked-in freeze was untouched.
- There are 72 unique sample/depth IDs, 66 unique labels and taxon IDs,
  and 77 unique unordered, non-self pairs.
- Every count-table cell matches the archived datum or the declared
  zero-fill convention. There are 1,891 retained positive terrestrial
  entries among 2,195 positive entries of all retained/excluded types.
- Endpoint IDs, depths, elapsed ages and intervening-level counts match
  the selection rule. The rule brackets each 7-ka target window; realised
  point-age spans are 7,644–8,579 years. These are sufficiently similar
  for the proposed descriptive endpoint comparison, with the exact spans
  and uncertainties visible.
- Separate public `validate` calls pass all five scientific specifications,
  without exclusions or warnings. Intake line 118 currently constructs
  three `CommunitySpec` objects rather than validating their data. Record
  the actual validation results in the amended freeze; present validity
  has been checked, so this is a receipt correction rather than a data defect.

## Chronology: retain the limits, correct the inference

Restricting temporal interpretation below 295 cm is sensible. Keep the
unmodelled lower record in depth coordinates and retain its archived ages
only as provenance. However, this scopes the disagreement rather than
resolving it. The models also disagree inside the dated interval: at
190 cm IPPD-2 gives 28,830 cal BP and IPPD-1 gives 36,818. Call the latter
an archived-model endpoint sensitivity, not an equally validated chronology
or a probability distribution for chronological uncertainty.

Two statements need correction before the stage-2 narrative is written:

1. **The Late Glacial–Holocene pair does not straddle the 125 cm date.**
   The primary endpoints are 100/120 cm and the alternative 95/120 cm.
   Both lie wholly above it, in the core-top-to-one-date portion of the
   age models. Three intervening levels are sufficient for an endpoint
   contrast, but cannot resolve its intervening trajectory or abruptness.
2. **Do not turn 52,110 ±5,800 into a minimum-age constraint without
   source support.** The saved geochronology record marks this as finite
   (`infinite=false`) with a two-sided error. Its proximity to the method's
   useful limit warrants caution; it does not by itself establish a
   one-sided bound. Old and young carbon can bias a bulk-sediment date in
   different directions. Describe it as a weak finite archived control
   whose dating and calibration warrant checking. The analysis does not
   censor, recalibrate or refit it.

Keep the 45–38 ka comparison secondary and chronology-dependent. Its young
endpoint is actually 225 cm (36,902 under IPPD-2), just shallower than the
230 cm dated level. No test on these endpoints can identify a human or
megafaunal effect. There is no need to discard the endpoint-count comparison
merely because its calendar interpretation is uncertain.

The 397 cm core versus archived 80–427 cm depth mismatch remains unresolved.
Do not infer missing-core length or apply a depth offset without the
original source. The full 1999 article is still a source check to complete
before final stratigraphic and chronological interpretation.

## Sparse zeros and broad taxonomic categories

The positive-only archive is consistent with sparse count storage, but
“there are no zero entries, therefore every missing entry is an observed
zero” is not a sufficient logical demonstration on its own. There is
independent support for the conversion: Neotoma's own pollen workflow
explicitly converts the long data to a wide matrix with `values_fill=0`.
[Official Neotoma workflow](https://open.neotomadb.org/EPD_binder/simple_workflow.html).

I accept that convention for this archived-count analysis. State that
absent entries are zero-filled according to the archive conversion
convention; do not equate this with proof that every category was searched
for uniformly in the original material or with biological absence. The
original counting protocol remains unverified.

Broad names beside genera are not obviously inclusive family subtotals.
For example, sample 531305 records Proteaceae=0 and Banksia=6, and sample
531323 records Rutaceae=0 and Boronia=1. These examples are inconsistent
with treating those broad columns as complete family totals. Nevertheless,
unique labels and these examples do not prove that all category definitions
are mutually exclusive and stable through the core. Replace “so nothing is
counted twice” with an explicit assumption that the archived variables are
disjoint counting categories, pending source confirmation. Preserve them
without speculative taxonomic merging and report pollen-category richness.

## Freeze three reporting rules before drawing tables

**Monte Carlo sensitivity.** Replace “near the Holm threshold” with this
numerical diagnostic. For the 77 pairs, take the API's lower and upper
Clopper–Pearson bounds for the underlying exact conditional tail
probabilities. Apply the same Holm procedure separately to the full lower
vector and full upper vector. Flag pair i when
`Holm(lower)[i] <= 0.05 <= Holm(upper)[i]`.

Call this a sensitivity envelope for the exact-tail classification under
Monte Carlo uncertainty. It is not a simultaneous 95% interval, a new
significance rule or a guarantee of stability under another random seed.
Keep the API's reported plus-one p-values and their Holm adjustments as
the primary reported results, keep the fixed B/seed and do not rerun to
obtain significance. The public API does not supply this adjusted-envelope
diagnostic; declare that small reporting calculation as unsupported
postprocessing rather than adding an engine feature. Record the rule in
the design before results.

**Ranks.** Rank the 71 adjacent steps separately from the three long-interval
primary comparisons. Show each IPPD-1 sensitivity beside its matched
primary comparison. A pooled rank over all 77 pairs would mix different
temporal support. The common testing family can remain 77 while reporting
these separate descriptive ranks.

**Direction.** The frozen pairs run shallow/younger to deep/older. The API
taxon effect is b−a, hence deeper minus shallower. For a forward-time
gain/loss statement, explicitly report the reverse sign (younger minus
older), with sample IDs and the chosen direction in the column label.
Do not change the frozen pair order, which also determines random streams.

## Handoff

Record the prescribed clarifications and actual community validations,
then execute stage 2 through the existing APIs with the inputs, endpoint
selection, pair order, B and seed retained. Save the implementation,
environment and primer identities with the runs. Check the original
article before final source/chronology claims; a contradictory counting
protocol would require a documented intake amendment and affected reruns.
Do not infer agreement among chronologies or causal history from successful
reproduction of this archive.

Next: Claude — record the pre-result clarifications, then run stage 2.
