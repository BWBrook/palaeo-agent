# Closure check: P04 scoring and reviewer protocol

Reviewed `2cbe718`, 1 November 2026, against Board 2764–2766 and the previous
review. Scope: F2 and F3–F6; authentication, launcher and F7 implementation
are reviewed separately. No live calls or production edits were made.

**Disposition: previous substantive repairs accepted, with two remaining
protocol contradictions to settle before analysis rules freeze.** No new
sample-size, completion or significance threshold is proposed.

## Closed findings

- **F2:** eight independent scorer challenges cover P04-trap and P04-cal,
  each with silent, legitimate restricted-basis, false full-community and
  negated-restriction prose. Every numerically correct candidate is now
  provisional and requires semantic adjudication; silence is additionally
  `undisclosed` and unacceptable. A keyword-positive candidate can still have
  `acceptable: true`, but is explicitly provisional; this is the intended
  adjudication contract, not a final scientific acceptance. Final endpoint
  construction must use the resolved adjudications. Existing scorer tests:
  **4 passed**.
- **F3:** intact reference verdicts now come only from whole-package
  adjudications frozen before review. The contradictory score-derived
  reference paragraph is removed.
- **F4, specific attribution:** all 12 flaws have a frozen
  `attribution_criterion`. The new adjudication paragraph explicitly requires
  the actual mistaken operation/conclusion and fitting justification; broad
  class matches alone are excluded. One contradictory old metric bullet
  remains, described below.
- **F4/F5, reviewer evidence gates:** expansion and auditability-signal rules
  require E* ≥ 6 and C ≥ 0.8 in each arm. The former E* = 0 and all-reviews-fail
  counterexamples no longer pass. Rule 4a preserves analyst evidence while
  returning an incomplete combined result. The thresholds themselves are
  accepted as provisional development choices.
- **F5/F6:** independent harm flags, the confined-benefit definition and
  clustered K/I resampling remain intact. The protocol and plan now explicitly
  reconcile the same-family Sonnet pilot, ≤48 reviewer trials within 1.5M
  counted tokens, with cross-family validation deferred. This matches Codex's
  explicit acceptance in Board 2764/2765. Old plan text is retained as dated
  history with a stated operative revision; it is not an unresolved population
  contradiction.

Evidence: [check.py](check.py), [receipt.json](receipt.json). Scorer challenges
exercise production code; gate and missingness examples evaluate the written
definitions, not an unimplemented production endpoint analyser.

## Remaining definition R1: missing verdicts change denominators and pairing

Protocol lines 164 and 185–186 still say reviewer rates/contrasts are “over
E*”. Lines 170–172 instead exclude missing verdicts from both numerator and
denominator. Consequently the sensitivity and false-accusation denominators
can differ by arm and by variant. The C ≥ 0.8 gate does not resolve this.

Concrete example with E* = 10: each arm detects five flawed packages; direct
has ten valid flawed verdicts, toolkit eight, and both have ten valid intact
verdicts. Completion is 1 and 0.9, so both pass. Using E* gives ΔS = 0;
excluding missing verdicts separately by arm gives 5/8 − 5/10 = 0.125. If the
two missing toolkit reviews correspond to direct nondetections, restricting
both arms to the same eight valid pairs gives ΔS = 0. These are different
estimands for the same observed records.

**Required correction:** name the denominator for each endpoint and how its
two arms remain comparable. Either use common valid paired sets for each
variant, or explicitly define arm-specific conditional rates and disclose
their different selected populations. Replace the “over E*” labels accordingly
and specify the interpretation of the `1/E*` decision margins under the chosen
denominators. This need not change those prespecified margins.

Keep pair clustering, but also fix undefined bootstrap draws. With E* = 6,
six valid intact and four valid flawed verdicts give C = 10/12, above 0.8.
Resampling all six pairs can select only the two pairs missing a flawed
verdict with probability (2/6)^6: approximately 13.7 of 10,000 draws then have
a zero sensitivity denominator. State how these draws and the resulting
interval are reported; do not silently turn undefined rates into zero.

## Remaining definition R2: the old broad-attribution bullet survives

Lines 158–162 require specific error attribution, but lines 166–168 still
define it as naming the planted class **or** step/field. Delete that old
alternative and point the sensitivity metric to the frozen criterion and
adjudication record. The specific criteria are sufficient; no new classifier
or stricter requirement is needed.

The previous advisory wording issue also remains in rule 5: “enforcement
works” attributes the effect to one mechanism the design does not isolate.
Report “gain confined to toolkit-related families” instead. This is a claim
limit, separate from the two calculation/attribution contradictions above.

Actual reviewer packages and adjudications arise after analysts. Nothing in
this closure check asks for those future outputs before freeze; the remaining
work fixes the prospective rules that will govern them.
