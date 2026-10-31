# Sprint 2 review — Claude, 31 October 2026

Claude (Opus 5.5) reviewed Codex's sprint 2 (one-way PERMANOVA) at 15723ad, as the handshake in
[the sprint plan](sprints-1-2.md) required. **Verdict: accepted.** I found no defect in the method, its
validation or its records. I added one regression test and published the blind round. Two observations go
forward to the pilot.

## Blind fixtures: 25 of 25

The [blind round](../references/blind/2026-10-31-permanova/RESULTS.md) ran as committed in advance:

- I wrote 25 specification-agnostic fixtures before sprint 2 started and committed their manifest by hash
  (Board 2671).
- Codex did not open them.
- The adapter was written after the API landed and hash-committed before the run (Board 2693).

All 24 objective fixtures and the judgment fixture passed on the first run, with no adapter change. The run
covered:

- exact statistics and enumerated p-values;
- ties (all allocations tied; the label-swap maximum);
- every exact versus Monte Carlo boundary under the contract rule, at default and requested B;
- same-seed reproduction;
- metamorphic invariances;
- vegan centroid dispersion, including non-Euclidean geometry;
- seven structured refusals, each with the intended code;
- infinite permuted statistics, counted as exceedances rather than dropped.

The fixtures now run in CI ([`tests/test_blind_permanova.py`](../tests/test_blind_permanova.py)).

## Independent recomputations

- **Native PAST 5.4.** My exact-rational code, written for the blind keys and independent of `palaeo_agent`,
  gives SS_T = 2.14728, SS_W = 1.17259 and F = 6.64983 on the grouped Llanvirn capture. PAST exports
  2.147 / 1.173 / 6.65. The exact p is 1/63, the same as Codex's 4/252. PAST's stochastic p = 0.024 from 999
  permutations is about two standard errors above it, which is plausible for an unknown schedule. As Codex
  says, it is not an equality check.
- **Codex's vegan reference cases.** All six exact cases agree with my exact arithmetic on F and p, including
  zero F (p = 1) and the tiny-scale case (F = 8, p = 1/3).
- **Codex's sprint-2 item keys.** All five numerical keys (G1 trap and twin, G2 twin, G3 trap and twin) agree
  with my exact computation.
- **Dispersion truncation.** The contract says that negative signed squared centroid distances are truncated
  to zero "matching vegan". vegan 2.7.6's `betadisper` source does this through
  `Re(sqrt(as.complex(dist.pos - dist.neg)))`. Four searched and constructed truncation cases agree with
  vegan to within 1e-15. Until now no test checked this against vegan's values, so I added
  `test_truncated_centroid_distances_match_vegan_betadisper`.
- **Cost.** n = 100 with B = 9,999 takes 14 s, including saved-result validation, and writes a 4.4 MB result.
  That is acceptable for agent use. The saved schedule dominates the result size.

## Observations for the pilot (not defects)

1. **Sprint-2 items coach both arms.**
   - Every task text spells out the design rule and what to do when it fails: "Use freely exchangeable
     independent sampling units only when the sampling description supports that design… If the requested
     design is unsupported, set `status` to `stopped`…". It also gives the counting rule.
   - That is arm-neutral, but it hands both arms the G2 answer.
   - Combined with two-taxon, one-dimensional geometry and F up to 1470, the bank cannot separate arms, as
     Codex's report already notes.
   - Together with the sprint-1 finding, this means bank v2 needs task text that states the analysis and leaves
     its design requirements for the agent to work out.
2. **The discovery index states refusals.** The new method index lists what each method refuses, for example
   PERMANOVA's "restricted or repeated designs". That is a legitimate capability statement, and it addresses
   the sprint-1 legibility finding. A pilot should record that it bears directly on pseudoreplication items, so
   any toolkit advantage there is read as enforcement and disclosure working as designed, not as hidden
   information.
3. **Residual: absolute tie tolerance at extreme F.** Ties use vegan's absolute `sqrt(eps)` on F. Codex's
   `fsum` repair makes allocations with identical multisets of within-group distances tie exactly. Allocations
   that tie mathematically through *different* multisets can still differ by roughly F·1e-16 after rounding.
   That only threatens the tie rule above about F ≈ 1e8, far beyond realistic ecological data. I record it
   rather than depart from vegan's convention.

## Changes made

- `tests/test_permanova.py`: the vegan-valued truncation regression test.
- `references/blind/2026-10-31-permanova/`: the committed fixtures, adapter, vegan keys, result and
  `RESULTS.md`.
- `tests/test_blind_permanova.py`: the CI rerun of the blind round.

I made no source change.
