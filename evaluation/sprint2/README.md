# Sprint-2 group-comparison development instrument

Version: `sprint2-group-bank-v1`; scorer: `sprint2-group-score-v1`.
Prepared 31 October 2026. This extends the development evaluation, not a held-out
or efficacy study. The original item bank, scorer, harness, runtime and smoke
records remain unchanged.

There are exactly three trap/clean pairs, six items and twelve planned trials:

| Pair | Trap | Clean twin |
| --- | --- | --- |
| G1 | Metadata order differs from count-table order; join by exact sample ID. | Same data and labels, matching row order. |
| G2 | Four subsamples within each of two sites, one site per facies; stop as unsupported. | Each row is a distinct independent site. |
| G3 | A supplied draft claims a pure centroid-location effect despite differing spread. | A supplied draft states qualified group association and descriptive spread. |

G3 tests evaluation of a supplied claim. It does not demonstrate that an agent
would independently produce a scientifically sound interpretation from numbers
alone. No item requests a dispersion p-value or claims that dispersion proves
location. Clean tasks request only supported free one-way PERMANOVA outputs and
descriptive centroid distances.

All counts are synthetic. Each sample contains two taxa totalling 100. Its
Bray-Curtis geometry is exactly one dimensional, with distance `abs(x-y)/100`.
`build_items.py` calculates squared-distance sums of squares and enumerates all
label allocations using standard-library rational arithmetic. Centroid
distances are exact absolute deviations in that geometry. Keys do not import
the toolkit or derive expected outputs from its implementation. Each item has
separate materials, key and provenance, including group-assignment and
sampling-unit hashes. `items/MANIFEST.json` records every item-file hash.

Both arms receive the original answer contract and are scored by the same
primary rules. The [scoring amendment](SCORING.md) rejects computations on G2's
explicitly unsupported dependent design. Evidence completeness is secondary.

## Smoke controls

`smoke.py` imports the original trial runner with only its execution root and
runtime redirected. It fixes Codex `gpt-6.1-sol`, medium effort, 300 seconds per
trial, no retries, a fixed randomised order and a 300,000 uncached-input-plus-
output launch-stop ceiling. Usage is reported only after each trial; one trial
can overshoot that ceiling. No Anthropic trials are part of this extension.

The runtime is `~/palaeo-eval/sprint2-runtime`; trial roots are separately under
`~/palaeo-eval/sprint2`. A fresh temporary agent home receives the existing
Codex authentication through the original harness; credentials are neither
printed nor retained in trial records. Workers cannot read the checkout,
keys, generators, other trials or agent instruction state under the inherited
outer sandbox. The controller preflight checks actual canary/key reads and
toolkit import origins in each arm. It does not claim complete network
isolation; shell network access remains a disclosed original-harness limit.

Before live smoke: parent pins the implementation commit; build the separate
runtime from it; verify solvability and discovery text; freeze bank, scorer,
source, harness, wheel and discovery hashes; run controller preflight; commit
the freeze and plan. The wrapper refuses a changed or uncommitted instrument.
No runtime build or live trial is authorised merely by generating these files.

The frozen smoke retains every outcome, including missing answers and timeouts.
No tuning or replacement trial occurs during this version. Any later amendment
requires a separately named bank/scorer/smoke version and preserves these files.
