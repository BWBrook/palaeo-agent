# Sprint 2: declared group comparisons

31 October 2026. Initial implementation pinned at **1093bb0**, following the
[agreed plan](sprints-1-2.md) and [frozen method contract](permanova-contract.md).
The subsequent numerical repair is **1943c30**, described below.
Claude's independent blind fixtures remain unseen by Codex and its delegates.
The planned counter-review and reconciliation have not yet occurred.

## Capability and validation

Palaeo-Agent now provides one-way PERMANOVA with explicitly declared count
semantics, orientation, transformation, distance, independent sampling units
and free exchangeability under the null. Metadata joins by exact sample ID.
These are declared assumptions; neither independence nor exchangeability can
be established from a count matrix and grouping column.

Results contain SS, degrees of freedom, pseudo-F, R-squared and a permutation
p-value, together with the actual index schedule, mode, exceedances, denominator,
seed, bit generator and NumPy version. Exact enumeration covers distinct
labelled allocations and counts the observed allocation once. Monte Carlo uses
independent PCG64 shuffles with replacement and a plus-one p-value. Ties and
positive-infinite permutation outcomes are counted explicitly. No draw is
silently dropped or redrawn. The contract permits signed semimetric statistics
and refuses unsupported finite-statistic or resource-limit cases explicitly.

Centroid dispersion is descriptive, uses all retained signed eigenspace
components, and records negative squared-distance truncations and discarded
eigenmodes. No dispersion test, block/repeated-measures design, covariate model
or inferential sensitivity comparison was added. Inference does not depend on
a selected PCoA plotting cutoff.

The API and CLI support validation, run, inspection and reproduction. Bundles
save aligned metadata, input snapshots, count/distance tables, SS/df statistics,
dispersion and permutation records with named provenance. The discovery output
starts with a compact index of all three methods; CLI help lists them too.
This addresses the discovery truncation observed during sprint 1.

Validation before the agent smoke:

- **272 tests passed**, including the original methods, new numeric and
  integration tests, independent reference checks and evaluation-item tests.
- A separate Codex auditor independently calculated all 210 allocations of a
  three-group rational example and checked exact/Monte Carlo boundaries, zero
  F, infinite permuted statistics, tiny variation, negative statistics,
  metadata alignment and saved-record integrity. A later stress check exposed
  the high-F accumulation defect described below.
- [Ten R reference cases](../references/r/permanova/README.md), six exact and
  four Monte Carlo, agree with independently generated vegan results on the
  same schedules. Largest F/permuted-F difference: **4.27e-14**; centroid-distance
  difference: **1.03e-15**. All compared p-values agree exactly.
- The [native PAST 5.4 capture](../references/past/captures/sprint2-permanova/capture.json)
  agrees on total SS, within-group SS and F within its four-significant-digit
  export precision. It uses all ten Llanvirn samples with a synthetic A/B split
  purely for validation. It supports no ecological group hypothesis.

Two upstream numerical differences are preserved. vegan's `vegdist` zeros
Bray–Curtis values below 1e-15, while our contract retains genuinely nonzero
tiny distances. Its `betadisper` also errors when every eigenmode is discarded.
For that control we separately supply exact-rational distances to `adonis2`
and verify F=8 and p=1/3; the zero-retained-mode dispersion control follows the
declared formula. Those controls are not reported as native vegan agreement.

PAST's accepted export reports 999 permutations, p=0.024 and F=6.65. Our exact
enumeration gives p=4/252, about 0.015873. The PAST draws are unavailable, so
its stochastic p is retained separately and is not an equality comparator.
An initial edit reverted to 9,999 before computation; that screenshot and
earlier input-format experiments are retained. The accepted export itself
verifies the intended 999-permutation setting.

## Numerical repair after the smoke

A separate stress audit found an order-dependent exact p-value at very large
pseudo-F. For six samples in three groups, exact rational calculation gives
F=191999616000192/365 and six tied extreme allocations out of 90. Ordinary
summation could split those ties and return p=2/90 instead of 6/90 for two
tested row orders, changing a conventional 0.05 decision.

The smoke continued on its frozen source without alteration. After all twelve
trials ended, **1943c30** replaced ordinary pair/group accumulation with
`math.fsum`; the statistical formula and absolute tie tolerance are unchanged.
All eight regression orders now return six extremes and p=1/15. A separate
Codex auditor independently verified the rational expectation, the before/after
counts and the unchanged statistical definitions. This control does not prove
stability for every possible matrix.

On the repaired source, **282 tests pass**, including all R reference tests;
the native PAST deterministic comparison and all six item-solvability checks
also pass. [Repair evidence](../references/independent/permanova-high-f/README.md)
preserves before/after logs, source fingerprints and verification receipts.
No extra live agent trials were run after the repair.

## Agent smoke and limits

The new [evaluation extension](../evaluation/sprint2/README.md) contains three
trap/twin pairs: metadata alignment, dependent sampling units and over-reading
dispersion as a pure location effect. Keys come from independent rational
calculations; the five completable items agree with the API, and the dependent
design requires a stopped answer. Interpretation items assess a response to a
supplied claim, not independent ecological judgment inferred from numbers.

The twelve-trial Codex smoke uses a separately pinned wheel/runtime, frozen
bank/scorer/plan, isolation preflight, five-minute trial limits and a 300,000
uncached-input-plus-output token ceiling. Frozen sprint-1 records remain
unchanged. All twelve trials completed normally, with no timeouts or retries,
using **230,839** counted tokens. All twelve primary frozen scores were correct,
including the two dependent-design stops. These results describe the initial
implementation **1093bb0**, not the repaired source. They do not constitute
efficacy evidence or the subsequent blind method review.

Both arms scored 6/6. The five numerical toolkit trials actually invoked the
CLI and saved bundles; its dependent-design trial read discovery/help and
stopped before inference. Mean counted tokens were 15,936 for direct scripting
and 22,538 with the toolkit; mean elapsed time was 67.3 and 69.7 seconds,
respectively. This smoke provides no evidence of an accuracy advantage and
shows higher observed token use with the toolkit on these items.

The scanner's 42 URL matches in six toolkit transcripts were reviewed as
printed reference/documentation URLs, with no observed fetch commands or
protected-key/source reads. Successful filesystem/arm preflights and finite
transcript review do not establish network isolation or absence of every
possible leak. [Full smoke results and records](../evaluation/sprint2/smoke/codex-v1/RESULTS.md)
retain the original flags, manual adjudication, invocation evidence and costs.
All numerical items have two taxa and two groups, use exact enumeration and
have F no larger than 1470. They do not cover the subsequent high-F failure.

## Reproduce

```sh
uv run pytest -q
uv run palaeo-agent run examples/permanova-llanvirn.json --output runs
uv run python scripts/compare_past_permanova.py
```

R generator, exact inputs, schedules and provenance are under
`references/r/permanova/` and `references/r/permanova_reference.R`. R is a
validation-time dependency only. The next handshake is Claude's critique/fix
of sprint 2, then Codex's critique/fix of sprint 1, followed by reconciliation.
