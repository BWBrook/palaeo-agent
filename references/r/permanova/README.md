# Synthetic PERMANOVA development fixtures

Prepared before reference execution on 31 October 2026. These are known
development examples, not the separate unseen cross-review fixtures.

- `balanced6`: six samples in groups of three, separated count compositions.
- `unequal8`: eight samples in groups of three and five; raw and relative
  abundance Bray-Curtis address unequal-total sensitivity.
- `negative8`: two groups of four using binary Jaccard, each containing the
  three two-taxon subsets and their three-taxon union on disjoint supports.
  The union's squared distance to its group's centroid is analytically -1/48
  in the uncorrected pseudo-Euclidean representation. This exercises a material
  negative centroid squared distance and its truncation to zero.

Metadata rows are deliberately reversed relative to the count tables. The R
generator must join by exact sample ID. No Palaeo-Agent parser or numerical
function is used to generate the reference.

Exact enumeration uses every unique allocation preserving the observed group
sizes, including the observed allocation exactly once. The labelled spaces
contain 20, 56 and 70 allocations respectively. Explicit MC schedules were
recorded after the method contract froze, before comparator execution.

The method contract was frozen at `2c335a7` before reference execution. Added
controls include three groups of two, a zero-F case with infinite permuted
statistics, and one-taxon counts `2^52 + [0,1,2,3]`. For the tiny control,
vegan 2.7-6 `vegdist` sets all distances below its hard-coded `ZAP = 1e-15` to
zero. That native discrepancy is retained in the reference. A separate exact
rational distance matrix, converted through 80-digit decimal strings and fed
directly to `adonis2`, checks its F/p calculations without claiming native
`vegdist` agreement. No package distance definition is changed.

On that exact-distance control, native `betadisper` also fails after its
threshold discards every eigenaxis. The JSON retains the error and a separate
zero-mode diagnostic control derived from the frozen threshold; it does not
label those zero distances native `betadisper` output.

## Reproduce from the repository root

```sh
.venv/bin/python references/r/permanova/prepare_schedules.py
Rscript --vanilla references/r/permanova_reference.R
.venv/bin/python -m pytest -q tests/test_permanova_reference.py
```

The R generator selects the existing project renv library for its R platform;
it does not restore packages or change global R configuration. Its JSON records
the contract and generator fingerprints, input/metadata/schedule hashes,
package versions and full explicit schedules. Exact native `adonis2` checks
receive the M-1 non-observed representatives because vegan supplies its own
observed plus-one; the independently counted reference includes all M once.
Both use the frozen absolute `sqrt(float64 epsilon)` tie tolerance.

These are ten known development cases: six exact enumerations and four MC
schedules. Agreement is not independent of shared method definitions or LAPACK,
and none of this material is blind or held out.

The zero-F input also has a three-draw MC case to exercise ties and the
plus-one denominator directly. It was added as a named diagnostic control
after the first nine cases were inspected; those original cases and their
reference values were not altered.
