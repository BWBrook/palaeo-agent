# Sprint 14 contract: constrained zonation (CONISS) with broken-stick retention

Claude (Opus 5.5), 11 November 2026. **Draft for Codex's review.** It
implements the method that [application 5](application-5-proposal.md)
(Lake Selina zonation, Board 3138) needs. That application is the
acceptance test. No zonation of the Lake Selina core has been computed.

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
  API fields.

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
- **`transform`:**
  - `relative_abundance`: coordinates are the row proportions p_ik = x_ik / Σ_k x_ik;
  - `hellinger`: coordinates are √p_ik.
  - There is no `none`. Raw counts would weight levels by pollen sum, a
    choice application 5 does not make, and nothing else needs it now.
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
  5,000 samples, and at most 5,000,000 retained cells; above either limit
  the method refuses before computing (`resource_limit`).

## Algorithm

**Coordinates.**
- Each row total is `math.fsum` of the row.
- Each proportion is one IEEE division.
- `hellinger` takes `np.sqrt`, which is correctly rounded.

**Hierarchy.**
- Start with n singleton clusters. Each cluster is a contiguous run of
  rows and keeps a size and a centroid.
- At each step, every adjacent pair (A, B) has the merge cost

  c(A, B) = n_A·n_B/(n_A + n_B) · Σ_k (ā_k − b̄_k)²

  with the sum taken by `math.fsum`.
- Merge the pair with the least cost. `np.argmin` returns the first
  minimum, so an exact tie goes to the leftmost pair, which is also the
  shallowest when positions are depths.
- The merged centroid is (n_A·ā + n_B·b̄)/(n_A + n_B), computed elementwise.
- Only the two costs next to the merged cluster change at each step.
- Step j (j = 1, …, m, where m = n − 1) records:
  - the boundary removed;
  - both clusters' first and last sample IDs and their sizes;
  - the cost c_j;
  - the runner-up cost: the least cost among the other eligible pairs, or
    null at step m;
  - the cumulative dispersion H_j = `math.fsum(c_1 … c_j)`.

Every reduction is correctly rounded, and the other operations are single
IEEE operations. Results are therefore bit-identical across platforms for
the same NumPy major version.
- Inspection recomputes everything and requires exact equality. It needs
  no tolerance.
- Fresh reproduction uses the existing `compare_results`.

**Required properties.**
- H_j equals the total within-cluster sum of squares of the partition
  after j merges (Ward's identity). This is tested, not assumed.
- H_m equals the total sum of squares about the grand centroid.
- Merge costs need not increase. Inversions are common under the adjacency
  constraint: a prototype found them in 194 of 200 random 12 × 4 tables.
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

For split rank r = 1, …, m:

- **gain:** g_r = c_(m−r+1), the cost of the merge undone by that split.
  It equals H_(m−r+1) − H_(m−r) in exact arithmetic. Using the cost
  directly avoids cancellation.
- **expectation:** e_r = (H_m / m) · Σ_{j=r}^{m} 1/j, with the tail sum by
  `math.fsum`. The m expectations sum to H_m.
- **exceeds:** g_r > e_r (strict).

This is vegan's `bstick(m, H_m)` (rioja imports it) with exactly rioja's
indexing. `bstick.chclust` pairs the comparison for `nGroups` = r + 1 with
`bs[r]`, and so does this contract.

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

**Zero dispersion.** When H_m = 0, every g_r and e_r is 0, so the rule
keeps one zone. The result also carries a `zero_dispersion` warning.

**Zones.** For the selected k, each zone records:
- its label, from 1 at the first table row;
- its first and last sample IDs and positions;
- its size;
- its within-zone SS, by direct two-pass `math.fsum` about the zone
  centroid. This is a second route to H_(n−k), compared by the validator
  within 1e-12 · max(H_m, smallest positive normal).

**Warnings.** In addition to the existing table warnings
(`near_duplicate_labels`, `identical_samples`, `repeated_block`):

- **`near_tie_merge`** lists each step whose runner-up cost is within
  1e-9 · max(c_j, runner-up) of c_j, including exact ties.
  - An exact tie is resolved to the left, as specified.
  - A near-tie means a different but equally valid rounding path (rioja's
    Lance–Williams recurrence, for instance) could merge another pair.
  - It flags numerical fragility only. The scientific margin is visible
    in every step's `runner_up_cost`.
- **`near_tie_retention`** lists each rank r ≤ `stopped_at_rank` (or every
  rank, if none fails) where |g_r − e_r| ≤ 1e-9 · e_r. A rounding-level
  change at such a rank could change k.
- **`zero_dispersion`**, as defined above.

## Result (`coniss`, version 1)

The result keeps the common fields: `method`, `version`, `value_type`,
`transform`, `missing`, `empty_samples`, `orientation`, `input_sample_ids`,
`sample_ids`, `taxon_ids`, `excluded`, `metadata` and `warnings`, and the
retained `counts` or `values`, as in `community`. The `coniss` fields:

| Field | Content |
| --- | --- |
| `position_column`, `positions` | Declared column; one number per retained sample |
| `merges` | m records: step, boundary, left/right first–last IDs and sizes, cost, runner_up_cost, cumulative |
| `boundaries` | n − 1 records in table order: boundary, left/right IDs and positions, merge_step, split_rank |
| `total_dispersion` | H_m |
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

**Inspection** validates the saved specification against the result, then
recomputes from the saved retained values and positions:
- coordinates, the full merge record, boundaries and split ranks;
- the broken stick, retention, zones and every warning.

Every value must match exactly, apart from the zone-SS identity
tolerance above. A rehashed `results.json` whose hierarchy, retention or
zones have been edited consistently is therefore refused.

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

1. **Independent reference: pinned R `rioja` 1.0-7**, added to the
   reference renv. The generator `coniss_reference.R` calls `chclust(dist(X)^2,
   "coniss")` on our coordinates. Squared Euclidean input is the convention
   for this objective; the manual's unsquared `dist` example is a
   different objective.
   - **Per boundary:** the generator also makes the wrapper's own call,
     `.Call("chclust_c", as.matrix(d), 2L, PACKAGE = "rioja")`. Its
     output, before the wrapper sorts it, gives each boundary the
     cumulative dispersion at which it disappeared. Compare it with our
     H at that boundary's `merge_step`. This identifies the whole merge
     order, which is stronger than comparing sorted heights or plotted
     trees.
   - **Partitions:** `cutree(tree, k)` against our split ranks, for every
     k.
   - **Broken stick:** `bstick(tree, ng = n − 1)` against our ranks 1 to
     m − 1. Rank m, which rioja's `diff(rev(height))` omits, is checked
     against `bstick(m, H_m)[m]` and the smallest height, both computed
     in R.
   - **Tolerance:** rtol 1e-10 on dispersions. Partitions and ranks must
     match exactly unless our record flags `near_tie_merge` at the step
     concerned, and the test then asserts that flag.
   - **Cases:**
     - the 0/2 fixture: H = 2; supplying unsquared distances gives 1,
       which the generator records as the trap;
     - an exact tie (1-D 0, 1, 2), merged to the left;
     - exact duplicate rows with representable values;
     - a constant sequence (zero dispersion);
     - a 30 × 8 two-block synthetic table under both transforms, with at
       least one inversion and at least one later exceedance;
     - n = 3.
2. **Ward identity, without R:** on the synthetic table, H_j equals the
   directly computed within-zone SS of the partition after every j.
3. **Retention rule unit cases:** passing a prefix and then failing; a
   tie at the stop (fails); a later exceedance reported but not used;
   all ranks passing; zero dispersion.
4. **Refusals:**
   - `order_mismatch` for a decreasing position, a repeated position and
     a non-finite position;
   - `insufficient_samples` for n < 3;
   - `resource_limit` before allocation;
   - `empty_samples: drop` recorded, and the order check applied to the
     retained rows.
5. **Bundles:** inspection and fresh reproduction succeed. Rehashed tampers
   are refused at inspection, each with its tables refreshed so that the
   semantic check is the one exercised:
   - a merge cost;
   - a split rank;
   - `selected_zones`;
   - a zone's within-SS.
6. **Study:** an `exclude_taxa` plus metadata-join study with a `coniss`
   analysis runs, inspects and reproduces. An abundance dataset is
   accepted.
7. **Application 5** freezes its study (four analyses) before any core
   zonation is computed. It then runs, inspects and reproduces in a fresh
   worker, and cross-checks against rioja on the frozen coordinates as
   declared external work.

Tests replace rather than accumulate: one reference module
(`tests/test_coniss.py`), plus one study case added to `test_study.py`.

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
