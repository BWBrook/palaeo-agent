# Sprint 13 implementation review

Codex, 9 November 2026. Reviewed `fd74076` following Board 3131. The
revised magnitude/direction split is accepted. Six bounded defects were
repaired before the application-4 amendment was frozen or computed.

## Findings and repairs

1. **Discovery descriptions.** Inserting the paired method shifted two
   positional catalogue lookups. PERMANOVA and rarefaction now obtain
   descriptions by method ID.
2. **Projection ambiguity.** Duplicate source headers are refused even
   when both copies would be dropped by the declared projection.
3. **Partial studies.** Malformed paired selectors previously crashed the
   final row-filter warning pass after validation had already failed.
   That pass now skips invalid selectors, preserving the original
   structured failure in an inspectable partial study.
4. **Saved inference coherence.** The generic absolute tolerance admitted
   tiny positive p-values changed to zero, or a p-value nudged across its
   saved direction threshold. Probability flags/log values and the
   direction verdict are checked for coherence; p-values must also
   recompute with relative tolerance only.
5. **Unbounded endpoint bands.** Binomial ranks 0 and R+1 represent
   unbounded order-statistic limits. Replacing them with observed extrema
   cannot retain the advertised 99% coverage. They now remain ranks 0/R+1,
   with null lower/upper endpoints and `unbounded: true`; resolution stays
   unresolved. This corrects the clipping sentence in the contract.
6. **Bootstrap numerical range.** A finite observed fit could overflow
   only in resamples and escape as a raw model-validation error. Refits,
   differences and summary arithmetic now refuse with `numerical_range`.
   Valid zero differences and zero standard errors remain valid.

For finding 5, with R=999 and q=0.0005, the probability of no bootstrap
value below the target quantile is `(1-q)**R = 0.606758`. The observed
minimum therefore cannot be a 99% lower confidence bound. The binomial
rank construction follows the [SciPy binomial inverse-CDF definition](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html);
rank 0 is the negative-infinite lower limit, and rank R+1 the
positive-infinite upper limit. Bands are pointwise for each endpoint,
not a joint 99% interval and not a claim about sampling coverage.

## Evidence

- Eleven artificial regression cases exercise the six findings. Ten fail
  against the archived `fd74076` source; one malformed-selector case was
  already refused correctly and retains that behavior.
- All 999 bootstrap replicates in the independent plain-Python reference
  test are now checked, rather than every 37th draw.
- Three independent bounded reviews covered single-fit inference, paired
  bootstrap and study/interfaces. A focused second review accepted the
  repaired paired calculation and its 12 tests.
- The first complete suite after the repairs passed **833 tests, 11
  skipped**. A subsequently added live MCP test passed for both single-fit
  inference and paired bootstrap, including fresh-server reproduction and
  an unbounded endpoint case. The final full suite passes **834 tests, 11 skipped** (95.29 seconds).
- Existing pinned smatr/base-R reference, interval/test duality, simulated
  coverage and bundle tampering tests are retained. No new limpet paired
  result was computed during this review.

## Decision

The methods are suitable for the fixed application-4 amendment. The
magnitude interval/test and separate correlation test are marginal;
there is no joint signed confidence set. The paired percentile interval
is approximate, conditional on independent, exchangeable specimens,
and its Monte Carlo resolution must be reported. Inspection checks saved
consistency; reproduction alone binds the bootstrap statistics to the
seed-generated resamples. Numerical agreement does not establish the
normal sampling model, fossil sampling independence or measurement truth.

## Application acceptance

Amendment 1 was frozen at `73596b8` before the paired limpet analysis.
The [amended report](../analyses/fossil-limpets/REPORT-AMENDED.md) records
the resulting marginal inferences, fresh byte-identical reproduction and
30,021 base-R comparisons. A separate read-only Codex scientific review
checked the report against the saved results and accepted its numbers,
assumptions, prior-knowledge disclosure and interpretation without changes.
The original descriptive artifacts remain byte-identical to `fd74076`.
