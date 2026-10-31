# Pilot protocol pre-freeze review

Reviewed `a3ca570`, 1 November 2026. This is an independent methodological
review of `docs/pilot-protocol.md` against `docs/sprints-3-4-proposal.md`, the
pilot keys/materials and the existing `evaluation/revised/score.py`. No live
trials ran. No production, bank or protocol files were changed.

**Disposition: repair before freeze.** The explicit flaw classes, retained
ineligible pairs, clustered resampling and ordered catch-all decision are
useful improvements. The following definitions still affect what the
experiment would measure or decide.

## 1. Intact reference verdicts need scientific package review

Protocol lines 96–98 derive the intact verdict from the analyst score. The
existing scorer establishes numerical agreement for completed controls, not
the scientific correctness of their prose, preparation or evidence package.
It can therefore assign `accept` to the very interpretation errors that this
reviewer experiment is designed to detect.

**Executed counterexample.** Calling `evaluation.revised.score.score` on a
schema-valid P10-control answer with the correct keyed `shannon_change`
`0.24585556544429088`, but the summary “Shannon diversity decreased from the
oldest to the youngest sample”, returned:

```json
{"outcome": "correct", "adjudication_required": false}
```

That answer has precisely the opposite-direction flaw specified for
P10-control in line 87. Hashing the answer or embedding it in an otherwise
integrity-valid package cannot repair this semantic problem. An accurate
reviewer rejecting the intact answer would be counted as falsely accusing it.

**Required correction:** fix reference verdicts by an explicit scientific
package adjudication before reviewer outputs are opened. The numerical score
can be an input to that adjudication, not its entirety. Define the evidence
needed for `accept`, including conclusions and their support, and preserve
the adjudication record. This is distinct from the pending scorer additions
for alternative answers, out-of-scope rows and strata.

## 2. Eligibility and reviewer denominators are inconsistent

Lines 51–56 admit schema-valid, integrity-valid but scientifically incorrect
intact packages and say every reviewer rate has denominator E. Lines 100–104
repeat that rule, whereas line 115 defines false accusation over *correct*
intact packages. Those denominators can differ between arms.

For example, with E = 12, eight correct direct intact packages and twelve
correct toolkit packages, one erroneous rejection per arm gives rates 1/8
and 1/12 under conditional denominators, but 1/12 and 1/12 under E. The
conditional arm difference is -1/24; the E-normalised difference is zero.
The threshold `1/E` consequently has different meanings. An arm may have no
correct intact packages at all even with E = 12; its conditional rate is then
undefined. A bootstrap resample can also contain no qualifying packages.

Incorrect intact packages create a second problem: rejecting their flawed
variants may detect a pre-existing mistake rather than the planted flaw.
Line 102 counts any rejection as sensitivity. Naming the planted class alone
also does not distinguish two mistakes in the same class.

**Required correction:** prespecify the analysis sets and estimands. A simple
option is a matched subset whose intact packages are scientifically acceptable
in both arms, with its own denominator and minimum-size gate; report all
original eligibility and exclusion counts without substitution. Another is
to retain the current E but call rejection/E an unconditional burden, report
conditional false accusations separately, and require the planted step/error
to be identified for planted-flaw detection. Whichever choice is made, define
zero denominators, bootstrap empty subsets, and failure/malformed reviewer
outputs. Do not silently score missing reviews as successful non-accusations.

## 3. Expansion currently permits entirely stratum-confined benefit

The agreed plan says a benefit confined to the stratum directly addressed by
the toolkit calls for repair/broader coverage. Protocol rule 4 instead accepts
`other` ΔT = 0; rule 5 only intercepts `other` ΔT < 0.

A concrete feasible example is improvement of 1 on all seven toolkit trap
families and 0 on all five other families. Overall ΔT = 7/12, its item
bootstrap lower 80% bound is positive, and `other` ΔT = 0. With the remaining
safety/review/cost conditions satisfied, rule 4 says **Expand**, although the
entire benefit is confined to toolkit families.

**Required correction:** define “confined” operationally and make the ordered
rules implement it. At minimum zero improvement in the other stratum belongs
in the confined-benefit case if the agreed interpretation is retained. State
whether a positive point estimate or stronger evidence of transfer is needed;
five families cannot support a confident mechanism claim. Neither the stratum
contrast nor randomised arm comparison isolates enforcement from disclosure,
workflow support or other parts of the intervention.

## 4. Decision labels overstate what the pilot estimates

- Rule 7 calls a two-pair sensitivity difference “real” and a small primary
  point estimate “null”, regardless of their intervals. These are useful
  development thresholds, not evidence that correctness is equivalent or that
  the reviewer gain is established. Use “observed reviewability signal;
  correctness benefit not established”, and report the intervals.
- Rule 2 precedes the adverse rule. If direct trap success is 1 and toolkit
  success is 0, it returns only a ceiling/design stop although ΔT = -1. A
  ceiling can coexist with severe harm. Make adverse flags independent of the
  single development disposition, or give the adverse rule priority.
  Similarly, E < 8 in rule 1 can invalidate the reviewer instrument without
  erasing an otherwise valid analyst harm signal. An instrument/design stop
  can remain the operational decision while all interpretable adverse results
  are reported; infrastructure-corrupted results still need qualification.
- Rule 8 can mean a decision to stop investment at this pilot's resolution;
  it must not become an equivalence or absence-of-effect claim.

These changes need not increase sample size or authorise further trials.

## 5. Reviewer population and resampling units need one definition

The plan requires Codex and Sonnet reviewer populations to be reported
separately. The draft has one ΔS/ΔA in the decision table without saying which
population governs the decision or how a conflicting replicate is treated.
Prespecify the primary population and the role of the replicate; never choose
after seeing results or pool them implicitly.

The endpoint table calls the resampling unit for K and I “trial”, but the next
paragraph says never to resample trials. Preserve the agreed item/family
clusters across arms, sessions and class when bootstrapping quantities that
use all analyst trials; label trial as the observational unit if that is what
was intended. State the treatment of interrupted blocks and unknown token
usage. These are definition gaps, not demonstrated implementation bugs.

## 6. Flaw specification is not yet flaw validation

The 6/3/3 list supplies plausible witnesses. It does not yet freeze which two
species P05 merges or which four right valves P09 drops, nor demonstrate that
every proposed numerical flaw changes a reported quantity beyond tolerance.
Those deterministic selectors and numerical witnesses must be fixed before
outcomes can influence flaw choice. For P04, the detectability argument should
be the unsupported inferential claim, not that a small difference itself
cannot be statistically significant.

Before freeze, supply deterministic flaw operators/selectors and representative
demonstrations in both formats that establish feasibility, integrity and a
numerical change beyond tolerance (or the specified changed conclusion).
Actual analyst packages do not yet exist: those arrive after analyst trials.

After analysts finish and before reviewer outputs are opened, validate every
realised intact/flawed package and fix its scientific reference verdict. An
honest upstream mistake must propagate consistently through inputs,
scripts/specifications, results, prose and hashes. The pre-freeze demonstration
does not substitute for these per-package checks. The draft properly allows
an unplantable pair to be recorded as ineligible rather than replaced. Report
resulting eligibility by flaw class and arm as well as E.

## Remaining gate evidence

The scorer amendment, deterministic flaw construction/validation, launcher,
runtime rebuild and client requalification were explicitly unfinished in
Claude's Board message 2752. Their absence is an open delivery item, not a
failed test result. This review neither approves those implementations nor
changes their ownership. The parent review covers the client-boundary
proposal independently.
