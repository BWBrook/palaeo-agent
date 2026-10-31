# Blind fixtures and diagnostic repairs — 31 October 2026

All **60 objective fixtures** authored independently by Claude now pass.
The complete suite passes **156 tests**. A separate Codex reviewer accepted
the repair after checking the original counterexample, internal ties, full
positive rank and saved-result validation. The original PAST comparisons
still match all 1,059 declared cells within export precision.

One judgment item remains an explicit disagreement about warning policy.
Its numerical answers pass. The raw frozen-key score is therefore 60 correct
and one wrong; we do not report 61/61.

## Evidence and independence

Claude published the [fixture archive](../references/blind/2026-10-31/README.md)
in commit 2532dfb. Before running against e04b592, Claude committed the
48-file manifest hash on Board thread 101, message 2650. Codex had not seen
the fixtures before that run. Claude had previously reviewed implementation
code, so these were blind to the implementer, not an untouched assessment
of an unseen codebase. They are now development and regression material;
they are not the isolated held-out set in [evaluation.md](evaluation.md).

The first run found 59/60 objective cases correct, plus the separate judgment
disagreement. The original author, runner, fixtures, keys and baseline results
remain byte-for-byte unchanged. The CI adapter verifies the original manifest
hash and all 48 listed files, runs all 61 cases through the original runner,
requires every objective case to pass and checks the judgment discrepancy
separately. No fixture was discarded or re-keyed.

The [follow-up record](../references/blind/2026-10-31/repair.json) records
source hashes, runtime, fixture commitment, adjudication and result hashes.
[Raw runner output](../references/blind/2026-10-31/results/after-repair.json)
retains the judgment failure. The
[PAST recheck](../references/blind/2026-10-31/results/past-after-repair.json)
uses the same native captures as tranche 3 with the repaired source fingerprint.

## F1: refuse an unresolved PCoA cutoff

Three samples with disjoint supports have unit pairwise distances and PCoA
eigenvalues 0.5, 0.5 and 0. Requesting one axis previously returned a solver's
arbitrary one-dimensional slice of the two-dimensional eigenspace. The full
equilateral geometry was well defined; that selected projection was not.

The analysis now raises `nonidentifiable_axes` before allocating a run bundle.
The error supplies the requested dimensions, spectrum, positive rank, relative
cutoff gap, threshold, allowed dimensions and largest allowed dimension at or
below the request. This example lists `[2]` as allowed, so the agent can
explicitly re-declare two dimensions. It does not silently change the request.

The shared policy is:

- Retaining the entire positive rank is allowed.
- Otherwise require `(lambda[k-1] - lambda[k]) / lambda[0] > 1e-8`.
- A tied block wholly inside the retained subspace is allowed; its coordinate
  basis remains arbitrary, while its geometry is invariant.

The threshold is a declared numerical-stability rule, not a statistical test
or proof of exact degeneracy for every small nonzero gap. Full positive rank
remains allowed even when the final positive eigenvalue is small relative to
the leading one. Its cutoff-gap field is `null`, because no positive block
is being truncated.

Calculation, saved-result validation, sensitivity and reproduction comparisons
use the same helper and threshold. A saved partial tied-block result cannot
pass inspection merely because its checksums agree. Input-only validation
remains an inexpensive check of counts, labels, orientation and policies;
spectral validity is checked during analysis.

## F2: separate a numerical diagnostic from association strength

The judgment fixture R09b has eight pairs and correlation about -0.043. Its
frozen key asks for `near_zero_correlation`; the existing guard only fires
below `abs(r) < 1e-8`. We have not adopted a new statistical warning threshold.

The guard is now named `small_computed_correlation` and explicitly describes
its numerical threshold as distinct from a statistical test. Both discovery
and result limitations state that RMA slope magnitude is `sd(y)/sd(x)`,
independent of correlation strength: a fitted line does not establish
association. The formula, threshold and point estimates are unchanged.
Uncertainty estimation and hypothesis tests remain outside this tranche.

R09b still fails its original warning expectation, while its slope, intercept
and correlation checks pass. This is an adjudicated design choice, preserved
next to the raw result rather than converted into an apparent fixture success.

## Reproduce

```sh
uv run pytest -q
uv run python -I references/blind/2026-10-31/runner.py \
  references/blind/2026-10-31/fixtures /tmp/blind-after-repair.json
uv run python scripts/compare_past_captures.py --output /tmp/past-after-repair.json
```

These checks establish development correctness within their stated cases.
They do not measure whether agents make fewer analytical mistakes. The next
useful tranche is a bounded development smoke of the agent-evaluation protocol,
with its execution budget settled before a campaign. No agent trial or new
inferential method was run here.
