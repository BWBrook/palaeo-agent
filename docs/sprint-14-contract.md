# Sprint 14 contract: constrained zonation (CONISS) with broken-stick retention

Claude (Opus 5.5), 12 November 2026. **Revision 2.1** (bounded rounding; Board 3299). Revision 2 replaced draft
`cb4b0f5` after Codex's [review](sprint-14-review.md) (Board 3275). It
implements the method that [application 5](application-5-proposal.md)
(Lake Selina zonation, Board 3138) needs. That application is the
acceptance test. No zonation of the Lake Selina core has been computed.

## What changed from the draft

Codex showed that the draft's floating-point arithmetic was wrong in
ordinary cases:
- **Constant data were split.** Four identical count rows gave two zones.
  The weighted centroid update moved a centroid by one ulp, and that
  invented variation passed the broken stick.
- **The tolerance failed nearly constant data.** On such rows the
  zone-SS identity check missed by about 1.6%.
- **Squares underflowed.** Distinct coordinates of about 1e-200 produced
  squared differences of exactly zero, so the method reported zero
  dispersion.
- **The portability claim was too strong.** Python documents that
  `math.fsum` may round differently by a bit on some platforms.

**The repair is to make every clustering decision with exact rational
arithmetic on the coordinates.**
- Coordinates are the nearest doubles to the exact proportions or their
  square roots.
- Merge costs, comparisons, cumulative dispersion, broken-stick
  expectations and the retention verdict are then computed exactly from
  those doubles, using Python integers and `Fraction`.
- Reported numbers are the nearest doubles to the exact values.

Consequences:
- Constant data have exactly zero dispersion and keep one zone.
- Ward's identity holds exactly at every step.
- Ties are exact.
- Inspection needs no tolerance.
- A quantity too small to report as a normal double is refused with
  `numerical_range`, never reported as zero.

A prototype passes all seven of Codex's probes. Its per-boundary heights
agree with a double-precision Lance–Williams recurrence (rioja's
algorithm) on 100 random count tables. Ward's identity held exactly at
every step. It takes 0.05 s at Lake Selina's size (72 × 60) and about
9 s at 2,000 × 250.

Also adopted from the review:
- the common names `method_version`, `retained_counts` and
  `retained_values`;
- the 1e-9 checks renamed as small-margin diagnostics;
- raw-coordinate fixtures labelled as internal tests;
- public count-table tie and constant cases.

## Why

Palynologists zone almost every pollen core with stratigraphically
constrained incremental-sum-of-squares clustering (CONISS; Grimm 1987),
and they choose how many zones to keep by comparison with a broken-stick
model (Bennett 1996). The toolkit can extract, filter and describe a
core. It cannot yet zone one. Application 5 asks which zones a fixed
procedure finds in Lake Selina, and which boundaries survive two declared
data choices.

## Scope

One new method, `coniss` (method version 1), and study support for it.

| Delivers | Definition |
| --- | --- |
| Complete constrained hierarchy | Greedy adjacent-only Ward merges on declared coordinates |
| Cumulative dispersion | Total within-zone sum of squares after each merge |
| Broken-stick comparison | Every split rank, including the final one |
| Retained zones | A declared consecutive-prefix rule |
| Boundaries | Between adjacent sample IDs, with their declared positions and the split rank at which each appears |

**Out of scope:**
- unconstrained clustering and other linkages (CONSLINK, single, average);
- alternative dissimilarities;
- globally optimal segmentation (for example, dynamic programming);
- boundary-location uncertainty (bootstrap or otherwise);
- p-values for zones or boundaries;
- age models, and any weighting by depth or time;
- stratigraphic diagrams. Application 5 draws its figure from inspected
  API fields;
- extended-precision clustering of inputs whose variation cannot be
  reported in double precision. Such inputs are refused.

## Specification

```json
{"method": "coniss", "input": "counts.dat", "format": "past",
 "orientation": "samples_by_taxa", "value_type": "count",
 "metadata": "levels.csv", "position_column": "depth_cm",
 "transform": "hellinger", "missing": "error", "empty_samples": "error"}
```

- **`value_type`:** `count` or `abundance`. Both are validated exactly as
  in `community`. The method uses only row proportions, so it never
  converts one kind into the other.
- **`transform`:** `relative_abundance` or `hellinger`. There is no
  `none`. Raw counts would weight levels by pollen sum, a choice
  application 5 does not make, and nothing else needs it now.
- **`metadata` and `position_column` are required.**
  - The position column must hold finite numbers that strictly increase
    in table order after any `empty_samples` drop. Otherwise the method
    refuses with `order_mismatch`, naming the first offending pair.
  - Adjacency is table order. Positions do not enter the merge cost, and
    gaps between levels carry no weight.
  - Positions exist so that order is checked rather than assumed, and so
    boundaries report positions from API fields.
  - A sequence index works where no depth exists.
- **`missing`:** `error` only.
- **`empty_samples`:** `error` or `drop`.
  - A dropped level is listed in `excluded`. Its neighbours then become
    adjacent.
  - The order check runs on the retained rows.
- **Size:** at least 3 retained samples (`insufficient_samples`). At most
  2,000 samples, and at most 500,000 retained cells; above either limit
  the method refuses before computing (`resource_limit`).

## Numerical model

Write ⌊q⌉ for the double nearest to a real number q, with ties to even.

**Input values.** Each value is the exact rational value of the cell as
validated. A count is an integer, and an abundance is the double that
the existing parser produced. Row totals T_i are exact (`Fraction` sums).

**Coordinates.**
- `relative_abundance`: x_ik = ⌊v_ik / T_i⌉.
- `hellinger`: x_ik = ⌊√(v_ik / T_i)⌉. This is the nearest double to the
  exact square root of the exact proportion, not a square root of a
  rounded proportion.

**Rounding.** One helper produces both kinds of ⌊·⌉ from a positive
rational a/b, using integer arithmetic only. (Revision 2.1, after Codex's
[review](sprint-14-revision-2-review.md): the earlier `float`/`sqrt` seed
plus `nextafter` walk had no practical bound when the seed underflowed.)
- It picks the binary exponent e so that the target t (a/b, or √(a/b))
  satisfies 2⁵² ≤ t·2⁻ᵉ < 2⁵³, or e = −1074 for a subnormal result. The
  bit lengths of a and b place log₂ t within one of the answer, so at most
  one correction step is needed.
- It forms the integer m = ⌊t·2⁻ᵉ⌋ directly: an integer division, or
  `math.isqrt` of an integer division for the root.
- It rounds by one exact integer comparison of t·2⁻ᵉ with m + ½ (for the
  root, of 4a·2⁻²ᵉ with (2m + 1)²·b), applying round-half-even at an
  exact midpoint, and returns m·2ᵉ via `math.ldexp`, which is exact.
- The work is a fixed number of big-integer operations whatever the
  magnitude, so seeds that underflow (Codex's 1e-600 proportions, whose
  roots are 1e-300) and subnormal proportions are handled like any other.
- Correctness never depends on the platform's `sqrt` or division.
- The same helper produces every reported double.

The test module checks the helper against an independent bisection over
binary64 encodings with exact midpoint rounding, which shares no code with
it. Cases: seeds that underflow to zero or are subnormal but have normal
roots; exact midpoint ties on even and odd significands, for both the
quotient and the root; and the normal/subnormal boundary, together with the
`numerical_range` rule below.

**Representability.** The method refuses with `numerical_range`:
- if a positive cell gives a coordinate below the smallest positive normal
  double (2⁻¹⁰²²), which includes a coordinate lost to zero;
- if any positive reported quantity would be below 2⁻¹⁰²².

The reported quantities are the costs, runner-up costs, cumulative
dispersions, gains, expectations and zone SS. Codex's example (rows
[1, 1e-200], [1, 2e-200], [1, 3e-200]) has positive exact dispersion
whose squares underflow, so it is refused. It is never reported as
constant. Counts can never trigger the coordinate check, because every
positive proportion is at least 2⁻⁵³.

**Exact arithmetic.**
- Every coordinate is a dyadic rational. Scale them all by one common
  power of two, 2⁻ᴱ, so that every coordinate becomes an integer.
- A cluster keeps its size and its exact integer coordinate sums S.
- For adjacent clusters A and B, the merge cost is

  c(A, B) = Σ_k (n_B·S_Ak − n_A·S_Bk)² / (n_A·n_B·(n_A + n_B)) · 2²ᴱ

  This is algebraically identical to n_A·n_B/(n_A + n_B) · ‖ā − b̄‖². It is
  held as an exact `Fraction`.
- H_j = c_1 + … + c_j exactly.
- Within-zone SS is Σ‖x‖² − ‖S‖²/n per zone, exactly.

There is no centroid rounding, no cancellation and no tolerance:
- constant data have exactly zero cost at every merge;
- Ward's identity (H_j equals the within-zone SS of the partition after j
  merges) holds exactly;
- equal costs are exactly equal.

**Portability.** Given the validated input values, every decision and
every reported double is a function of Python integer arithmetic.
Inspection and fresh reproduction can therefore require exact equality
in any CPython environment. No floating-point library call enters a
coordinate or a reported value. Reading abundance
values from text is the existing parser's responsibility, and its
round-trip is already tested.

## Hierarchy

- Start with n singleton clusters, one per row, each a contiguous run.
- At each step, merge the adjacent pair with the least exact cost. An
  exact tie goes to the leftmost pair, which is also the shallowest when
  positions are depths.
- Only the two costs next to the merged cluster change.
- Step j (j = 1, …, m, where m = n − 1) records:
  - the boundary removed;
  - both clusters' first and last sample IDs and their sizes;
  - ⌊c_j⌉;
  - ⌊runner-up⌉: the least cost among the other eligible pairs, or null
    at step m;
  - ⌊H_j⌉.

**Properties:**
- Merge costs need not increase. Inversions are common under the
  adjacency constraint: they appeared in 194 of 200 random 12 × 4 tables.
  Costs are never sorted or monotonised. H_j is non-decreasing because
  every c_j ≥ 0.
- The greedy hierarchy is not the optimal k-zone segmentation for every k,
  and the result says so.

**Boundaries.**
- There are n − 1 boundaries; boundary b lies between rows b and b + 1.
- Each records:
  - both sample IDs and positions;
  - the merge step j that removed it;
  - its **split rank** r = m − j + 1.
- The partition into k zones is the set of boundaries with r ≤ k − 1. This
  is the state after n − k merges, so a cut at any k reads directly from
  this field. Application 5 cuts each sensitivity at the primary run's k
  this way. No `cut` option is added.

## Broken-stick comparison and retention

For split rank r = 1, …, m, with every quantity exact:

- **gain:** g_r = c_(m−r+1), the cost of the merge undone by that split.
- **expectation:** e_r = (H_m / m) · Σ_{j=r}^{m} 1/j. The m expectations
  sum to H_m exactly.
- **exceeds:** g_r > e_r (strict).

This is vegan's `bstick(m, H_m)` (rioja imports it) with exactly rioja's
indexing. `bstick.chclust` pairs the comparison for `nGroups` = r + 1 with
`bs[r]`, and so does this contract. The result reports ⌊g_r⌉ and ⌊e_r⌉
and the exact verdict.

**Retention rule (declared convention: the consecutive prefix).**
- Retained zones: k = 1 + L, where L is the largest number such that every
  rank r ≤ L exceeds.
- The first failure stops retention, and a tie counts as a failure.
- The result records:
  - `selected_zones`;
  - `stopped_at_rank`: the first failing rank, or null if every rank
    passes;
  - `later_exceedances`: the ranks after the stop that exceed. They are
    reported, never used.
- rioja returns comparisons, not a choice. This convention is the
  toolkit's own, and the result names it
  (`retention_rule: "broken_stick_consecutive_prefix"`).

**Zero dispersion.** When H_m = 0 exactly, every g_r and e_r is 0, so the
rule keeps one zone. The result also carries a `zero_dispersion` warning.
This happens only for exactly constant coordinates.

**Zones.** For the selected k, each zone records:
- its label, from 1 at the first table row;
- its first and last sample IDs and positions;
- its size;
- ⌊its exact within-zone SS⌉.

**Warnings.** In addition to the existing table warnings
(`near_duplicate_labels`, `identical_samples`, `repeated_block`):

- **`small_margin_merge`** lists each step where runner-up − c_j ≤
  1e-9 · runner-up, compared exactly. Each entry carries `exact_tie: true`
  or `false`.
- **`small_margin_retention`** lists each rank r ≤ `stopped_at_rank` (or
  every rank, if none fails) where |g_r − e_r| ≤ 1e-9 · e_r, compared
  exactly.
- **`zero_dispersion`**, as defined above.

The two small-margin warnings are diagnostics, not bounds. Every decision
is exact for the coordinates as rounded. A flag says only that the data,
or the roughly 1e-16 relative rounding of the coordinates, would need to
change by little to alter that decision. An unflagged decision is not
thereby certified against every perturbation. The scientific margin is
visible in every step's runner-up cost and every rank's gain and
expectation.

## Result (`coniss`, `method_version` 1)

The result keeps the common fields: `method`, `method_version`,
`value_type`, `transform`, `missing`, `empty_samples`, `orientation`,
`input_sample_ids`, `sample_ids`, `taxon_ids`, `excluded`, `metadata` and
`warnings`, and `retained_counts` or `retained_values`, as in `community`.
The `coniss` fields:

| Field | Content |
| --- | --- |
| `position_column`, `positions` | Declared column; one number per retained sample |
| `merges` | m records: step, boundary, left/right first–last IDs and sizes, cost, runner_up_cost, cumulative |
| `boundaries` | n − 1 records in table order: boundary, left/right IDs and positions, merge_step, split_rank |
| `total_dispersion` | ⌊H_m⌉ |
| `broken_stick` | m records: rank, zones (r + 1), gain, expected, exceeds |
| `retention` | rule, selected_zones, stopped_at_rank, later_exceedances |
| `zones` | the selected partition, as above |
| `limitations` | fixed strings, listed below |

`limitations` reads:
- greedy hierarchy, not optimal segmentation;
- broken-stick retention is a heuristic, with no p-values or boundary
  intervals;
- equal sample weights, with no propagation of count sampling error;
- adjacency is table order, and gaps between positions are unweighted.

**Inspection** validates the saved specification against the result. It
then recomputes the complete result from the saved retained values and
positions, using the exact model, and requires every field to be equal,
including warnings and refusals. Because nothing in the recomputation
depends on floating-point library behaviour, exact equality is the
correct test in any environment. A rehashed `results.json` whose
hierarchy, retention, zones or reported numbers have been edited
consistently is therefore refused.

**Bundle files:**
- `input.dat`, `metadata.csv` and `aligned_metadata.csv`;
- `retained_counts.csv` or `retained_values.csv`;
- `coniss_merges.csv`, `coniss_boundaries.csv`, `broken_stick.csv` and
  `zones.csv`, each regenerated by `table_files` and compared byte for
  byte.

**Steps:** `snapshot_inputs`, `resolve_specification`, `record_environment`,
`orient_validate_order`, `constrained_hierarchy`, `broken_stick_retention`
and `collect_results`. No plot.

## Study layer and interfaces

- **Study:** `coniss` is allowed on `counts` and `abundance` datasets, and
  needs a dataset with metadata, as `permanova` does.
  - `exclude_taxa`, `exclude`, `select` and the metadata join work
    unchanged.
  - A `select` that reorders levels, or an `exclude` that leaves positions
    out of order, is caught by `order_mismatch` at analysis time.
  - No new row-filter warning is added. Removing a level is a declared,
    recorded operation, and its new adjacency is visible in `boundaries`.
- **Interfaces:**
  - MCP and CLI enums, `discover()` and the `METHOD_INDEX` entry, staying
    within the 3,072-character budget by shortening, not by raising the
    limit;
  - `summary`: n, transform, selected zones and the boundary IDs;
  - `__init__` exports.
- **Primer:** one paragraph covering:
  - what CONISS is;
  - that adjacency is verified table order;
  - the retention convention and why it is not a significance test;
  - reading a cut at another k from `split_rank`;
  - no zone p-values, and no PERMANOVA on zones chosen from the same data.

## Acceptance

1. **Exact oracle, without R.** A separately written brute-force
   reference in the test file:
   - it keeps `Fraction` centroids rather than integer sums;
   - at every step it recomputes every eligible cost from the cluster
     members;
   - it computes each partition's SS directly about its exact centroid;
   - it takes the method's coordinates only after checking each one
     against the independent bisection rounding reference above, so it
     cannot inherit a coordinate mistake from the production helper.

   It must agree with the method **exactly** (structure, every exact
   quantity and the verdict) on all of the following cases.
   - **Internal hierarchy cases** (raw coordinates, n ≥ 2):
     - the 0/2 fixture: H = 2;
     - the 1-D 0/1/2 tie, merged to the left.
   - **Codex's seven probes**, as public count or abundance tables:
     - constant [1, 9] rows under both transforms: zero dispersion and
       one zone;
     - the nearly constant [1, 1+1e-15, 1+2e-15] rows under both
       transforms: exact agreement;
     - the underflow rows: refused with `numerical_range`.
   - **Public tie, inversion and later exceedance:** count rows
     [1, 0], [0, 1], [1, 0]. Costs are 1 (an exact tie, taken at the
     left), then 1/3 (an inversion). Rank 1 fails (1/3 < 1), so one zone
     is kept, and rank 2 is reported as a later exceedance.
   - **Public duplicate blocks** under `hellinger`: count rows [5, 0, 1]
     twice, [0, 4, 2] twice, then [3, 3, 0]. There are two exact
     zero-cost merges.
   - **Ward's identity:** on a 30 × 8 two-block synthetic count table under
     both transforms, H_j equals the direct partition SS at every step.
2. **Independent implementation: pinned R `rioja` 1.0-7**, added to the
   reference renv.
   - **Calls:**
     - the generator `coniss_reference.R` calls `chclust(dist(X)^2,
       "coniss")` on our coordinates. Squared Euclidean input is the
       convention for this objective; the manual's unsquared `dist`
       example is a different objective;
     - it also makes the wrapper's own `.Call("chclust_c", as.matrix(d),
       2L, PACKAGE = "rioja")`. That call's output, before the wrapper
       sorts it, gives each boundary the cumulative dispersion at which
       it disappeared.
   - **Comparisons:**
     - per-boundary dispersion within rtol 1e-10;
     - `cutree(tree, k)` partitions for every k, which must match
       exactly;
     - `bstick(tree, ng = n − 1)` for ranks 1 to m − 1. Rank m, which
       rioja's `diff(rev(height))` omits, is checked against `bstick(m,
       H_m)[m]` and the smallest height, both computed in R.
   - **Cases:**
     - the 30 × 8 table under both transforms (with at least one
       inversion and one later exceedance);
     - a 40 × 12 Dirichlet-like count table;
     - the public tie fixture.

     The generator asserts that none of these has a small-margin flag
     except the declared exact tie. Partitions and ranks must then match
     exactly, with no exceptions.

     Nearly constant and underflow cases stay with the exact oracle.
     There, a double-precision recurrence such as rioja's is not a
     meaningful reference.
3. **Retention rule unit cases:**
   - a prefix that passes, then a failure;
   - an exact tie at the stop, which fails;
   - a later exceedance, reported but not used;
   - every rank passing;
   - zero dispersion.
4. **Refusals:**
   - `order_mismatch` for a decreasing position, a repeated position and
     a non-finite position;
   - `insufficient_samples` for n < 3;
   - `resource_limit` before allocation;
   - `numerical_range` both for a coordinate below 2⁻¹⁰²² and for a
     reported quantity below it;
   - `empty_samples: drop` recorded, and the order check applied to the
     retained rows.
5. **Bundles:** inspection and fresh reproduction succeed, with exact
   equality. Rehashed tampers are refused at inspection, each with its
   tables refreshed so that the semantic check is the one exercised:
   - a merge cost changed by one ulp;
   - a split rank;
   - `selected_zones`;
   - a small-margin warning removed.
6. **Study:** an `exclude_taxa` plus metadata-join study with a `coniss`
   analysis runs, inspects and reproduces. An abundance dataset is
   accepted.
7. **Application 5** freezes its study (four analyses) before any core
   zonation is computed. It then runs, inspects and reproduces in a fresh
   worker, and cross-checks against rioja on the frozen coordinates as
   declared external work. A boundary persists only when it lies between
   the same two sample IDs, as the application now defines.

Tests replace rather than accumulate: one module (`tests/test_coniss.py`)
holds the oracle, the reference comparison, the retention cases and the
refusals, plus one study case added to `test_study.py`. Codex's probe stays
under `references/independent/` as review evidence. Its cases enter the
suite through the oracle tests, not as a second copy.

## References

- Grimm EC (1987) CONISS: a FORTRAN 77 program for stratigraphically
  constrained cluster analysis by the method of incremental sum of squares.
  *Computers & Geosciences* 13:13–35. doi:10.1016/0098-3004(87)90022-7
- Bennett KD (1996) Determination of the number of zones in a
  biostratigraphical sequence. *New Phytologist* 132:155–170.
  doi:10.1111/j.1469-8137.1996.tb04521.x
- Juggins S. rioja: Analysis of Quaternary Science Data. R package version
  1.0-7. doi:10.32614/CRAN.package.rioja

Metadata for all three DOIs was checked against registered records
(Crossref and DataCite) on 11 November 2026. The rioja behaviour above
comes from its source: `R/consclust.r`, `R/bstick.r` and
`src/chclust.cpp` for version 1.0-7.
