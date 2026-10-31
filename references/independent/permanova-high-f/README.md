# High-F permutation ties

A separate stress audit found an order-dependent exact p-value after the
sprint-2 smoke had been frozen at `b670270` using source `1093bb0`.
The smoke continued unchanged; the repair was applied only after all twelve
trials ended and their 69 frozen-file hashes had been rechecked.

The six count rows in `tests/test_permanova.py::HIGH_F_COUNTS` form three
groups of two. Exact rational calculation gives
F = 191999616000192/365, approximately 5.26026345206e11. Among 90 distinct
labelled allocations, six tie for the maximum, giving p = 6/90 = 1/15.
Ordinary accumulation of within-group sums changed with group order by one
ULP. At this F scale, that difference exceeds the frozen absolute tie
tolerance. Two of eight tested row orders incorrectly counted only two
extremes, giving p = 2/90 and changing a conventional 0.05 decision.

`math.fsum` now accumulates pair contributions and group contributions. The
formula, permutation space and absolute tie rule are unchanged. All six
group-block orders and two interleaved orders retain six extremes. This is
a regression control for the demonstrated failure, not a proof of numerical
stability for every possible matrix.

The before/after scratch-test logs are preserved here. `verification.json`
records the repaired-source fingerprint and subsequent full-suite, native
PAST and item-solvability checks. The full suite includes comparisons with
the independently generated R reference values. No additional live trials
were run on the repaired source; the smoke remains evidence about `1093bb0`.
