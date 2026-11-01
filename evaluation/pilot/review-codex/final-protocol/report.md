# Verification of protocol amendments F3–F6

Reviewed `aedc158` on 1 November 2026, including protocol amendment
`0d2b8ec`. Scope: scientific definitions and decisions in
`docs/pilot-protocol.md`, checked against the agreed sprint plan and the prior
pre-freeze findings. No live trials ran. Production files and earlier evidence
were not changed. The parent separately checks scoring, flaws and launch code.

**Disposition: several fixes accepted; protocol not ready to freeze.**

## Accepted changes

- **F3, substantive fix:** independent whole-package scientific adjudication,
  reconciled and frozen before reviewers run, addresses the numerically
  correct but scientifically wrong intact-package problem.
- **F4, analysis-set fix:** the matched-correct set E* gives both arms the same
  scientifically acceptable intact packages. Reporting both E and E*, reasons
  for exclusion, selection and undefined zero-denominator metrics is sound.
- **F5:** the explicit confined-benefit definition catches the prior
  seven-improvements/five-zeros counterexample. Separate Part A prevents a
  ceiling or instrument decision from suppressing the harm flag.
- **F6:** K/I now preserve family clusters; rule 7 describes a development
  signal without claiming established gain or correctness equivalence.

These are acceptance of the definitions, not evidence that the corresponding
future adjudications or analyses have already been executed.

## R1. Expansion can pass without an interpretable reviewer experiment

Rule 4 (line 190) explicitly permits expansion when E* < 6, dropping the
reviewer safety conditions that the agreed plan made part of expansion. This
is a new relaxation, not a consequence of correcting the denominator. The
earlier analysis-set paragraph says reviewer instrument repair applies in this
case, while the final table permits overall expansion.

Missing reviews create a second route: lines 147–149 count failed or invalid
verdicts as non-detections and non-accusations. With E* = 12 but **every review
failing**, both arms have sensitivity 0 and false-accusation burden 0, so
ΔS = ΔA = 0 and rule 4's reviewer clauses pass. The instrument gate I counts
analyst infrastructure failures only.

The executable [counterexamples](counterexamples.py) and [receipt](receipt.json)
show both cases with I = 0, D = 0.5, ΔT = 0.5, interval [0.5, 0.5], both
stratum improvements 0.5, ΔC = 0 and K = 1. Earlier rules do not intercept
them. These are evaluations of the *written rules*, not tests of an existing
production endpoint analyser or evidence from live models.

**Required correction:** preserve the analyst finding when reviewer evidence
is absent, but do not label the overall pilot eligible for expansion under
the original combined criteria. Return reviewer-instrument repair or an
explicitly incomplete combined decision. Define reviewer completion/validity
conditions before applying ΔS/ΔA gates; reporting missing counts alone does
not prevent failures from looking like successful non-accusation. E* measures
available packages, not completed reviews. No new significance threshold or
larger trial budget is requested.

## R2. Class-only attribution does not identify the planted error

Lines 143–145 count a rejection when it names the planted class **or** the
planted step/field. For P07, the planted error is dividing L3 measurements by
10. A reviewer rejecting an alleged unjustified specimen exclusion and
labelling it “preparation” passes that rule despite missing the unit error.
The receipt preserves this counterexample. Half the flaws share this class.

**Required correction:** attributed sensitivity requires identification of the
planted mistaken operation or conclusion, with a justification that matches
the witness. Record class-level localisation separately if desired. Matching
a broad class, or merely naming a field while giving an unrelated reason,
must not substitute for error identification.

## R3. Sonnet-only governing reviews change the agreed experiment

Lines 25–30 make Sonnet the sole guaranteed, governing reviewer population and
Codex optional and non-decisive. This is explicit, but it changes the agreed
plan: `sprints-3-4-proposal.md` lines 485–489 and 517–519 specify two separately
reported populations, with Codex providing cross-family review when analysts
are Sonnet. The analyst fallback authorisation does not itself resolve that
scientific design change.

**Required correction:** settle and record whether this tranche retains the
two-population goal or is a narrower same-family pilot with cross-family
validation unfinished. If the narrower study is accepted, reconcile trial
counts, budget accounting, reviewer estimands and the claims/expansion
decision with that scope. Do not describe F6 as mere clarification of the
previous experiment. The existing Sonnet replicate allowance may cover these
same trials; this finding does not assert a new spending permission is needed.
It is a design decision for the parent and Claude to settle explicitly.

## R4. Remaining contradictory instructions need reconciliation

Three old paragraphs can still direct an implementer to the rejected design:

- Line 86 says every reviewer rate uses E; the new primary metrics use E*.
- Lines 99–101 promise 4E Codex trials plus 4E Sonnet replicate trials, contrary
  to the new guaranteed Sonnet-only route. Clarify also whether packages in
  E but outside E* receive descriptive reviews or no reviews.
- Lines 137–139 still derive intact reference verdicts from the analyst score,
  contradicting the new whole-package adjudication. Point them to the frozen
  adjudication instead.

These are consequential definitions, not cosmetic wording. Remove their
ambiguity before freezing the implementation. Rule 5 also still concludes
“enforcement works”: the experiment measures the combined toolkit
intervention, so “gain confined to toolkit-related families” is the supported
description. Disclosure, preparation support and enforcement are not isolated
as separate causes.

## Limits of this verification

The E* threshold of six, stratum cutoff of 0.05 and 80% bootstrap interval are
provisional development choices. This review does not demand stricter margins.
Actual packages are adjudicated after analysts; pre-freeze work fixes the
rules and demonstrates their feasibility. Missing implementation evidence
and design contradictions should be resolved before the freeze, without
claiming that future package adjudications have already occurred.
