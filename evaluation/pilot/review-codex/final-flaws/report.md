# Final F7 review: frozen flaws and feasibility

Reviewed `aedc158`, 1 November 2026. **Numerical references accepted;
two limited F7 repairs remain.** No live model calls, generator imports or
production edits were made. The independent [script](check.py) reads the
control materials and uses rational Bray–Curtis/PERMANOVA sums with separate
RMA/Shannon formulae. The [receipt](receipt.json) pins inputs and results.

## Verified

- All **12 frozen flaw reference results agree exactly** with independent
  materials-based calculations. Nine change numbers; three leave numbers
  unchanged and add an interpretation error.
- Every numerical flaw changes at least one keyed field beyond tolerance.
  The smallest maximum separation across its reported fields is about
  **769 key tolerances** (P01, through its changed sample count).
- P02's positional metadata assignment was independently calculated, rather
  than accepted from the existing error signature used by `flaws.py`.
- P05's two named taxa and P09's four valve IDs now fix the previously missing
  selectors. The preparation/design selections are deterministic.
- The existing flaw test file passes: **15 passed in 2.02 s**. Its P01 test
  demonstrates an integrity-valid toolkit study and a direct script rerun at
  the frozen wrong answer. The P12 test verifies a toolkit study with the
  altered transform.

## F7a: P07's declaration and operator disagree

`p07()` multiplies L3 lengths and widths by **0.1**, and the frozen result has
`mean_length_mm = 11.242096774193548`. The frozen answer assumption is:

> L3 measurements are in centimetres and were converted.

The task requires the pooled analysis in millimetres. If the asserted unit
were centimetres, converting to the requested unit requires multiplication
by **10**, not 0.1. That declared conversion gives independent
`mean_length_mm = 24.191935483870967`, materially different from the reference.

The intended planted error is the incorrect unit premise (the dictionary
says all measurements are mm), but this implementation adds an inconsistent
conversion direction. A reviewer can reject the arithmetic/unit conversion
without locating the intended preparation error. Make the operator and its
declaration consistent: either use the centimetre premise and multiply by 10,
or describe the actual erroneous division and corresponding mistaken premise.
Then regenerate and independently recheck the P07 reference and witness.

## F7b: representative package demonstrations are incomplete

The test module's opening description promises preparation, design and
interpretation demonstrations in both formats. Its actual coverage is:

| Class | Toolkit | Direct |
| --- | --- | --- |
| Preparation, P01 | Executed study, inspected, wrong values checked | Patched script rerun, answer and exclusion checked |
| Design, P12 | Executed study, inspected, wrong values checked | No demonstration |
| Interpretation, P10 | No package demonstration | No package demonstration |

P10 only applies `apply_answer_edits()` to an in-memory dictionary. It does not
construct a saved package, update the source that generates the answer/report,
rerun it, or check any package integrity. Merely editing a final answer after
script execution would be overwritten when that script is rerun. This matters
specifically for the interpretation flaws, whose intended effect is in prose.

Complete the promised small examples: one direct design script, and a saved
interpretation example in each format whose supported numerical claims and
upstream data remain consistent while the planted conclusion persists through
the applicable rerun/integrity checks. These are representative feasibility
demonstrations, not a requirement for all future analyst packages to exist
before the pilot. Every actual package will still require individual
propagation, integrity and reference adjudication before reviewer outputs.

## Detectability qualification

P04's frozen witness still says the difference is small. Small magnitude alone
does not establish lack of statistical significance. The valid witness is
the unsupported significance claim, and its per-package check must establish
that no valid supporting inferential analysis accompanies it. Similarly,
P08's witness requires checking that the particular package did not analyse
Pleistocene samples. Extra analyses in a realised package can affect whether
the fixed interpretation edit actually introduces a flaw. The protocol's
per-package adjudication/ineligibility mechanism can handle this; use it
instead of assuming the prose edit is always scientifically false.

The available references and preparation demonstration resolve most of F7.
They do not justify treating P07's intended single error or the interpretation
package propagation as already verified.
