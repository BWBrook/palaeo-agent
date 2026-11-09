# Sprint 13 contract review

Codex, 9 November 2026. Review of draft `99f4e1b`, following Board 3121.
**REPAIR before implementation.** The scope is useful, but Part A's general
signed-slope inference claim is not supported by its proposed interval.
No engine code was changed, and no application-4 inference was computed.

## Application 4 wording

The report now leads with the two point estimates being about 0.15 apart,
and states that neither departure from isometry nor a paired difference
beyond sampling variation is established. The title and closing section
use that framing. The subtraction is declared as reporting arithmetic on
API fields. The reviewer-only intervals are not imported into the report.
I also omitted the proposed claim about the estimates being small relative
to typical uncertainty: the current application has not estimated that
uncertainty. Its source data, numerical results and verification records
are unchanged.

## A. Resolve the inferential target and direction first

The proposed residual/fitted-score test has the same two-sided p-value for
null slopes +k and −k. Its inverted acceptance set therefore has two
components. The drafted interval returns only the component selected by the
sample correlation's sign. Those are not an unrestricted signed test and
its full confidence set.

This qualification appears explicitly in the primary
[smatr `line.cis` documentation](https://traitecoevo.github.io/smatr/reference/line.cis.html).
[Warton et al. (2006), pp. 272–273 and Appendix E](https://pdodds.w3.uvm.edu/files/papers/others/2006/warton2006b.pdf)
discusses the secondary component and selects the prior-positive component
in its simulations when the sample's major-axis direction reverses.
Matching smatr's returned primary interval does not remove that qualification.

An artificial check makes the mismatch concrete:

```text
x = [-2, -1, 0, 1, 2]
y = [-1, -2, 0, 2, 1]
b = 1; r = 0.8
primary 95% interval = [0.385975, 2.590839]
drafted p-value for null +1 = 1
drafted p-value for null −1 = 1
```

A review-only simulation used bivariate-normal observations with equal
variances, true correlation +0.05, n = 20, 2,000 datasets and seed 9132026.
The sample-sign primary interval covered the true signed slope +1 in
**56.65%** of datasets. Selecting the positive component in advance gave
**95.05%**. There were 803 sample-sign reversals. This is an artificial
contract check, not a limpet result.

The [independent probe](../references/independent/2026-11-09-sprint13-contract/probe.py)
and [receipt](../references/independent/2026-11-09-sprint13-contract/receipt.json)
preserve the numerical checks. Run
`uv run references/independent/2026-11-09-sprint13-contract/probe.py`.

**Recommendation:** for the advertised general signed-null API, return the
full two-component confidence set. A primary component may be identified
for display, with its selection and limitations explicit. Document that
this test alone does not distinguish null directions. If the intended
product is instead a single interval under a declared prior direction,
revise the specification, sign-conflict behavior and coverage claim before
implementation. Selecting the direction from the observed correlation is
not a substitute for a prior direction; silently dropping conflicts from
coverage calculations is not valid.

The revised acceptance test should fix correlations in advance, include
weak positive and negative associations, count sign conflicts and refusals,
and test both null signs. Check duality against the actual returned set,
not only two endpoints of its primary component. State the nonsingular
normal model and the population parameter being covered.

### Numerical repairs

1. Use a rationalized interval calculation. With
   `H = sqrt(1+B) + sqrt(B)`, magnitude bounds are `abs(b)/H` and
   `abs(b)*H`. At n = 3, r = 0.5 and the largest float confidence below 1,
   the drafted subtraction rounds the lower factor to zero; the equivalent
   rationalized value is about 1.00686e-16. Define a structured refusal for
   unrepresentable results. Scale the moments used for the null test rather
   than directly forming overflowing `y ± null_slope*x`.
2. A log-survival function is not by itself a finite log-tail guarantee.
   In the installed SciPy 1.18.1, `t.logsf(100, 1000)` is `-inf`, although
   the mathematical log probability is finite. Specify a verified stable
   fallback or a structured numerical refusal. Do not serialize a false
   negative infinity as the log probability.
3. Use pinned smatr references for ordinary inference, but base R
   `pt(..., lower.tail=FALSE, log.p=TRUE)` for tiny-tail checks. The
   [smatr test source](https://raw.githubusercontent.com/traitecoevo/smatr/master/R/slope.test.R)
   computes its ordinary p-value as `1 - pf(...)`, which can lose tiny tails.
   A 1e-10 absolute comparison to that zero would not test underflow handling.

## B. The four requested choices

| Choice | Recommendation | Conditions |
| --- | --- | --- |
| Save statistics rather than resampled rows | Keep | Bind the request's seed, replicate count, confidence, cohort and NumPy version to the result. Inspection checks internal consistency; reproduction checks the seed-generated distribution. Say explicitly that inspection does not establish that distribution's derivation from the pairs/seed. |
| Refuse if a resample is undefined | Keep | Do not discard draws or retry until valid. Report affected replicate count and reason; distinguish undefined individual fits from a valid zero difference/zero bootstrap SE. Remove the assurance that n ≥ 10 prevents the issue. |
| Percentile rather than BCa | Keep for this tranche | Identify it as an approximate first-order method, not an exact interval. Address endpoint Monte Carlo error and weak-association sign instability. BCa adds bias/jackknife handling and does not repair an undefined statistic. |
| Defer independent-group common-slope tests | Keep deferred | They do not answer the same-shell paired question. Do not expand this sprint into a second inferential design. |

Saving the index matrix would not itself validate bootstrap statistics;
inspection would also have to refit every draw. Keeping that work in
reproduction is consistent with the existing inspection boundary.

### Required details before coding

- **Bounds and allocation.** The bootstrap specification has no numerical
  bounds or memory guard. Specify strict integer replicate/seed limits,
  minimum usable cohort, confidence bounds and a pre-allocation budget.
  Pin `dtype=int64`, draw order and endpoint semantics. The existing
  PERMANOVA cap of 2,000,000 schedule entries is a reasonable simple option
  for this first implementation; the limpet schedule has 1,359,864 entries.
  A caller must receive a structured refusal before an oversized allocation.
- **Degeneracy is not ruled out by sample size.** In an artificial cohort
  with 135 identical rows and one distinct row, a 136-row bootstrap sample
  has probability about **0.3665** of containing only one unique row. The
  data can have a valid point fit while many draws are undefined. This is
  why refusing is honest and why rounded duplicates must remain visible.
- **Shared columns are legitimate.** Remove the requirement that all four
  column names differ. Comparing two responses against one shared predictor,
  or checking a method against itself, is valid paired input. Resolve each
  fit's columns using the existing rules. Add an identity control with
  difference/SE/interval all zero and a swap-A/B control that negates the
  difference and interval while preserving SE.
- **Sign instability.** Record how many resampled slopes change direction
  relative to each observed fit, and warn when this occurs. The signed RMA
  statistic is discontinuous at zero covariance; a percentile interval is
  not uniformly reliable through that boundary. A nonzero sample covariance
  alone does not establish the regularity assumption.
- **Simulation uncertainty.** A limitation sentence alone cannot show
  whether a near-zero interval endpoint is stable. Specify an endpoint
  Monte Carlo uncertainty check, preferably an order-statistic/binomial
  band with explicit tie and unbounded-tail handling. At minimum the
  acceptance analysis must quantify this uncertainty and label unresolved
  zero-inclusion conclusions rather than treating one seeded interval as
  numerically settled. This concerns simulation error, not sampling coverage.
- **Independent acceptance.** Keep the independent arithmetic reference,
  and test the shared complete cohort, exclusions, identity and swap cases.
  Rehashed tamper cases must refresh affected tables too, so they exercise
  the intended consistency check rather than only a checksum/table mismatch.

The specified paired row sampling agrees with the semantics in the
[SciPy bootstrap documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
That documentation also distinguishes percentile and BCa intervals and
notes BCa's difficulties with degenerate distributions. The explicit integer
draw settings follow [NumPy's generator contract](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.integers.html).
These support the algorithmic choices; they do not establish coverage for
this particular slope-difference estimator.

## C. Accept the column and range additions with explicit reading rules

Keep both additions. For column selection, specify exact unique header
names, nonempty unique data-column lists, refusal of unknown/ambiguous names,
and what happens when only `id_column` is supplied. Project columns before
interpreting the selected values; unused textual columns must not cause a
numeric refusal. Record declared and dropped columns, and preserve original
IDs and source order. The direct-CSV acceptance test should reproduce the
current derived PAST table, including column order, byte for byte.

Ranges describe retained raw values, not transformed coordinates or
excluded rows. Part C supplies endpoints; max/min ratios can remain declared
reporting arithmetic. The version-2 point estimates should remain unchanged,
while callers, schemas, tables, discovery and reference fixtures adopt the
new result shape. No legacy-result adapter is needed.

## Application amendment and handoff

Freeze the amendment only after the inferential target and numerical rules
are settled. Preserve the original descriptive result. Disclose that the
reviewer-only single-fit intervals were already seen; the paired bootstrap
result has not been computed. Specify whether reported intervals are marginal
or simultaneous, and avoid joint claims from unadjusted marginal intervals.
The source's sampling and measurement limitations remain even after a
numerically correct inference implementation.

Next: Claude — revise Part A and the bootstrap details before implementation.
