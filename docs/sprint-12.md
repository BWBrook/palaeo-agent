# Sprint 12: Fisher underflow diagnostic and compact extraction inspection

Claude (Opus 5.5), 8 November 2026. These close the two toolkit gaps left
open by application 3 and the reader review.

## `count_homogeneity` method version 3

A two-sided Fisher probability is always positive, because the observed
table has positive probability. A taxon-test `p_value` of 0.0 is therefore
always float64 underflow. Before this version it was reported with no flag;
application 3 hit it twice, for *N. gunnii* with counts 0 against 1,110.

- **New fields on each taxon test:**
  - `p_value_underflow` is true exactly when the float p is 0.0.
  - `log10_p_value` is then the unadjusted two-sided p on a log10 scale; it
    is `null` otherwise. It is computed as a log-space sum
    (`scipy.special.logsumexp` over `hypergeom.logpmf`) of the same tail
    SciPy uses: tables no more probable than the observed one, with
    relative tolerance 10⁻⁷.
  - The Holm-adjusted value of an underflowed test is also an underflowed
    positive number.
- **Unchanged:** `p_value`, `p_value_holm`, every decision and every other
  field.
- **Inspection** recomputes the flag and the log value.
- **Resource limit:** reconstructing an underflowed tail is refused with
  `resource_limit` when its estimated support and working arrays exceed
  the existing 64 MiB temporary-allocation budget. The check precedes
  allocation; ordinary representable Fisher probabilities need no reconstruction.
- **Output files:** `taxon_tests.csv` gains `p_value_underflow` and
  `log10_p_value`. The new limitation text states the reading.
- **Evidence:** `tests/test_count_homogeneity.py` and
  `tests/test_assemblage_integration.py` (formerly `tests/test_sprint12.py`).
  - An exact two-sided Fisher tail is computed in Python integers (no
    SciPy), with the same tie tolerance. It agrees with `log10_p_value` to
    within 10⁻⁹ for three underflowing tables, including application 3's
    case.
  - Ordinary p-values carry no log value and match the exact reference.
  - A run that inspects as verified, and two rehashed tamper cases.
- **Application 3** regenerates with only the added fields, the method
  version and the limitation text changed. The two flagged tests give
  log10 p = −363.14 (primary) and −377.45 (inclusive).

## Compact `neotoma_inspect` over MCP

The MCP tool now returns:
- the status;
- a summary of the extraction record: kind, datasets, counts, dropped
  tallies, all-zero samples and source hash;
- the specification;
- three environment fields: implementation hash, Python version and
  whether the lockfile was captured;
- the bundle's file paths;
- the scope.

The Python `inspect_neotoma` still returns the full record.
