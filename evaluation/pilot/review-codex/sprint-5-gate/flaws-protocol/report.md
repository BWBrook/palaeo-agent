# Sprint-5 gate: reviewer flaws, alternatives and protocol

Codex, 1 November 2026. Reviewed `799e0de`. This pass read the keys and
builder and is **not** a blinded scientific-sufficiency witness. It owns
only this evidence directory; no implementation changed and no live model
trial ran.

## Gate finding: P09 does not accept all handling it calls defensible

The materials ask for allometry **across individuals** and provide the
individual ID and valve label, but prescribe no preferred valve. The key
accepts globally selecting right valves, globally selecting left valves, or
averaging paired valves. Its reason states that keeping either valve is
equivalent. Because the generator now adds independent valve measurement
jitter, other legitimate one-valve-per-individual selections give different
values outside the numerical tolerance.

Independent calculations and calls to the actual scorer demonstrate:

| Item | Fixed selection rule | Slope | Intercept | n | Actual score |
| --- | --- | ---: | ---: | ---: | --- |
| P09-trap | First row for each individual in measurements.csv | 1.0287744701466837 | -0.13566720110416375 | 52 | wrong |
| P09-cal | First row for each individual in measurements.csv | 1.033514519203255 | -0.13720125062653632 | 49 | wrong |
| P09-trap | Lowest specimen ID within each individual | 1.0284893334555247 | -0.1353073509524616 | 52 | wrong |

The first rule is fully deterministic under the supplied file and retains
exactly one measurement per individual. Random selection with a fixed seed
gives further counterexamples. All five tested ordinary policies failed the
pilot key; three of five failed the calibration key. These are scientifically
defensible sampling choices under the stated contract, not duplicate-valve
pseudoreplication.

Resolve the **task's estimand and admissible methods**, not just the three
enumerated values. Options include making bilateral measurements equivalent
in the designed data, stating an individual-size aggregation rule in the
materials, or using semantic/procedural adjudication plus independent
recomputation for documented one-value-per-individual policies. Adding more
hand-picked result values does not close the general ambiguity. Rebuild both
pilot and calibration and rerun their witnesses after the choice. This affects
calibration acceptability and therefore the A/B gate.

Evidence: `check.py` computes these results independently and `receipt.json`
retains each full answer and scorer output. Relevant code is
`build_bank_v4.py:695` (independent valve jitter), `:729` (the enumerated
alternatives), and `score.py:48` (alternative numerical matching).

## Reviewer flaws: numerical references pass, package mutation remains future work

All **12 control flaw references** were independently recomputed from the
written CSV/TSV materials, using separate standard-library Bray–Curtis,
PERMANOVA sums-of-squares, Shannon and log-RMA routines. The check imports
neither bank builder nor toolkit numerical functions. All match within
`1e-9`; the maximum absolute discrepancy is `1.42e-14`.

- P01 drops the fully counted low-yield KC04 sample.
- P02 assigns the first n station-list zones by row position.
- P03 substitutes relative abundances for requested raw counts.
- P05 merges the sinistral/dextral columns mapped to distinct accepted names.
- P06 and P12 substitute raw counts for requested relative abundances.
- P07 multiplies observer AS measurements by 10 without the recorded unit
  supporting that conversion.
- P09 drops individuals I001–I004 as purported duplicates.
- P11 lumps Globigerinoides into Globigerina.
- P04/P08/P10 retain the numerical answer and add the specified interpretation
  error; P10's appended direction contradicts the negative keyed change.

The specific attribution criteria identify these operations or conclusions,
rather than merely their broad classes. No wrong-sign reference or inert
numerical perturbation was found in these **reviewer flaws**. This does not
assess the separate replay perturbations.

The v4 `reviewer_flaw` records currently contain expected results, answer
edits and attribution criteria. They are **not executable modifications of
actual analyst packages**. The generator can calculate a flawed reference,
but has not shown that a future direct script and toolkit study can both be
modified at the appropriate upstream step and retain consistent downstream
artefacts. Keep that qualification as an explicit pre-reviewer-launch gate:
save the minimal package diff, rerun preparation/analysis/answer generation,
verify each package and require the target results/declaration. A patch only
to `answer.json` is not an admissible numerical flaw. Actual packages do not
yet exist, so this is a remaining reviewer-launch obligation, not by itself a
reason to stop analyst recalibration.

Check interpretation flaws against actual package content too. P04's “no
test was run” and P08's “Pleistocene was not analysed” must be true of the
selected package. The task does not prohibit extra analyses, so an append-only
claim is not automatically false for every possible acceptable package. Use
the existing ineligibility rule if the same flaw cannot be planted honestly
and consistently in both arms.

## Scorer review

The `alternative_results` branch compares all keyed numerical quantities
under the same tolerance and integer checks, and only rescues the `wrong`
outcome. It does not rescue malformed/non-finite answers or false refusals.
For the current v4 keys, alternatives occur only in P06 and P09, and neither
has disclosure-token or equivalent-exclusion requirements. Therefore the
ordering that checks disclosures before alternatives does **not** currently
bypass a P04 disclosure gate. No separate current-bank disclosure bypass is
claimed. The substantive problem is the incomplete P09 admissible-result set
above.

The existing separation between numerical acceptability and whole-package
scientific adjudication must remain: reproducing or matching numbers does not
validate prose, exclusions or assumptions. This matters when retaining
`provisional=False` for recognized numerical alternatives.

## Protocol disposition

The four requested definitions are substantially adopted: symmetric raw-to-
answer replay, all-launched R, a branch-B table without invented D/ΔT, and
explicit A/B/halt routing with no implicit retry. The inherited common-set
minimums and completion gates still apply. Branch B's 24 trials remain at
most 12 paired control packages and provide development evidence only.

Clarify three records before freeze:

1. The v4 amendment calls both replay and scientific acceptability
   “eligibility,” while still asking for separate E and E*. Preserve **E =
   replay-eligible pairs**, **E* = scientifically acceptable pairs within E**,
   then subtract unplantable pairs as explicitly defined. Do not silently
   collapse the two counts.
2. The old adherence sentence requires a recorded `palaeo_run` or
   `palaeo_study_run` call, whereas the new prompt mandates Python API calls
   within `analysis.py`. A legitimate library-based replay may have only a
   worker-execute call. Update the measurement to track the new contract;
   library usage cannot be inferred just from the old top-level tool names.
   The replay/launcher review owns the technical verification of this point.
3. Reviewer launcher and frozen analysis remain future deliverables. State
   their freeze points relative to the live outcomes each consumes; do not
   describe sprint 5's full acceptance as complete merely because its
   recalibration materials exist.

A scientific inconsistency to reconcile with the blinded materials review:
P12's task says **“Test whether assemblage composition differs”** in one core,
while the build report describes its PERMANOVA as descriptive and acknowledges
faunally defined zones. Pseudo-F and R² can be computed descriptively, but
free-label inferential exchangeability is not supplied by this dossier. The
final task/key/adjudication must agree about whether a qualified descriptive
answer or an inference refusal is appropriate. This pass flags the conflict;
the independent materials-only review should determine its gate disposition.
