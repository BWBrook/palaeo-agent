# Sprint 15: bounded contract check alongside intake

Codex, 13 November 2026. Read-only review of `9f61b15` and Board 3355.
No engine implementation or real-data distance/threshold computation.
The [application-6 intake](../analyses/lake-selina-analogues/INTAKE.md)
is complete as a draft and needs its separate scientific review.

The four architecture choices are reasonable: calibration IDs belong in the
stack declaration; keep stacks narrow to `analogue`; five calibration rows
may be a declared operational floor without claiming statistical adequacy;
and the explicit rounded-coordinate numerical model can reuse sprint 14.
The actual conservative intake has **eight** representatives, not the
approximately 25 anticipated in the draft, and most fossil levels are
taxonomy-limited. A valid numerical acceptance test must disclose that limit.

Clarify these points before implementation:

1. **Stack source kinds.** Explicitly permit only count and abundance
   components; refuse measurement tables. State that `counts` requires all
   components to be counts, while explicit `abundance` is allowed for
   either all-count or mixed count/abundance components. The present
   "counts only if ... abundance otherwise" wording followed by permission
   to promote counts could lead to inconsistent validators.
2. **Three-modern fixture versus five-calibrator minimum.** Label the
   three-modern/two-fossil fixture as an internal arithmetic-only oracle,
   or enlarge it for the public method. The public request cannot both
   compute a result with three modern rows and enforce five calibrators.
3. **The scale [0, 2] is nominal.** Preserve that word in schemas and checks:
   do not clamp or refuse distances merely for exceeding 2 by rounding.
   The valid synthetic rows `[1,1,0,0]` and `[0,0,1,1]`, using the declared
   Hellinger rounder, give an exact rounded-coordinate distance above 2,
   reported as **2.0000000000000004**. This is consistent with the model,
   not an invalid source. Add it as an ordinary boundary fixture.
4. **Exact decisions versus rounded displays.** The contract already
   compares exact values; explicitly say that an exact tie and an apparent
   tie between displayed doubles are different. A displayed minimum equal
   to the displayed cutoff need not determine the saved verdict. Existing
   small-margin diagnostics should make that distinction visible.
5. **Totals on preparation steps.** Accept `exclude_taxa.sample_totals`.
   It closes the current preflight's declared totals-only API gap. Once
   implemented, the final intake must report inspected API totals; the
   separate arithmetic audit remains a check, not the reporting source.
   Cover an already-dryland input, such as the saved repaired query:
   it may need only the incomparable-bin removal, whose `before` total is
   its dryland denominator. Do not require an invalid empty exclusion merely
   to manufacture two steps.

These are bounded contract clarifications, not a request for another numerical
model or a wider workflow framework. Retain the explicit no-real-matching gate.
Resolving the intake's counting-bin assumption has higher scientific value
than implementing around its currently weak whole-spectrum coverage.

Next: Claude — review the intake and clarify the contract before implementation or design freeze.
