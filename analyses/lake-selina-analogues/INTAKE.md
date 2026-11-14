# Application 6: revision 2.1 intake for review

Codex, 14 November 2026. Implements proposal revision 2.1 (`f0a33a6`,
Board 3382). **This is not the scientific design freeze.** The 0.80
retained-weight floor and calibration screen were fixed before this revised
intake was computed. Crosswalks and the resulting candidate/representative
lists await Claude's review before the executable analysis is frozen.
No distance, percentile threshold, nearest neighbour or analogue verdict has
been computed. The new `analogue` method and `stack` operation are not built
or bypassed here.

## Revised intake

Whole-tally pooling leaves **all 72 fossil levels above the fixed 0.80 floor**
in both schemes, retaining **85.3–100%** of recorded dryland weight. Modern
rows retain **82.9–100%** in the percentage source and **88.3–100%** in the
NISP source. These are weight-accounting results, not analogue results.

| Scheme | Shared bins | Modern candidates | Calibration representatives | Fossil levels passing floor |
| --- | ---: | ---: | ---: | ---: |
| Primary | 46 | 61 | 19 | 72 / 72 |
| Coarse | 30 | 68 | 20 | 72 / 72 |

Primary retains the two named *Nothofagus* species and excludes six fixed
genus-only datasets in their entirety. Coarse pools to genus and admits
their seven rows. Thus this sensitivity changes **both taxonomic resolution
and reference membership**, including calibration. The original 61 rows have
exactly the same retained weight under coarsening; both schemes exclude the
same outside-dryland categories.

Eight native-percent rows exceed the fixed **100.5** screen on their exact
raw extracted land-plant weight. They remain candidate matches if otherwise
eligible, but cannot set the thresholds. NISP rows are exempt. Equality to
100.5 passes this particular screen without proving a consistent denominator.

| Sample | Site | Raw extracted percent-weight sum | Candidate schemes |
| --- | --- | ---: | --- |
| 1472789 | Lake Flannigan | 171.54 | Both |
| 1477443 | Naracoopa | 242.54 | Both |
| 1477740 | Peppertree Marsh | 133.54 | Coarse |
| 1477748 | Phil's Hill | 105.35 | Coarse |
| 1478920 | Snow Hill Marshes | 102.65 | Coarse |
| 1489992 | Big Dam Marsh | 105.64 | Coarse |
| 1490001 | Big Heathy Swamp | 139.73 | Coarse |
| 1490011 | Forester Marsh | 112.88 | Coarse |

Representatives are the first calibration-eligible rows by the predeclared
preference within actual collection units. All 19 primary representatives
also represent their units in coarse. Coarse additionally uses Big Dam
Marsh **1489993**, falling back from its flagged code-1 row. Primary has two
units with candidates but no calibrator; coarse has seven. Shared site
coordinates do not merge collection units. The full IDs, reasons and
fallback are in `sample-ledger.csv` and `preflight-check.json`.

## Accounting assumptions and information retained

The conservative crosswalks preserved in **0bb8cb7** left 69/72 fossil rows
below the floor. That result prompted this disclosed revision. The new
rule treats archived variables as additive tallies and pools whole bins;
it does not lower the floor or divide a source tally between targets.
The revised maps were written before revised coverage was inspected.

The historical tally check reproduces exactly: broad weight falls below
the sum of selected narrower weights in **31/49** tested dataset/category
combinations. That rejects inclusion only jointly with assumptions that
children are disjoint and share a numerical base. An independent, stronger
single-child diagnostic finds broad weight below the largest child in
**30/49** combinations, avoiding the disjoint-children assumption. Neither
check proves universal exclusivity, a common percentage denominator, or a
uniform counting protocol. Additivity is the approved **working convention**,
supported where full inclusion can be rejected and assumed elsewhere.

Every source column appears once in each complete crosswalk: fossil 66,
modern percent 92 and modern NISP 82, totalling 240 labels. Every retained
target can be formed from each source without inventing zero columns.
*Eucalyptus*, the two named *Nothofagus* species, *Lagarostrobos* and the
shared *Pherosphaera/Microstrobos* genus bin remain separate in primary.
Asteraceae pools to family. Explicit residual groups preserve narrower bins
where possible, but their broad tallies can contain unassigned members of
those narrower groups. The primary `Other Podocarpaceae` union deliberately
loses distinctions among *Microcachrys*, *Phyllocladus* and *Podocarpus*.
Legacy Liliaceae-related and Scrophulariaceae-related categories remain
incomparable in both schemes. Higher retention therefore depends on pooling
and reduced resolution, rather than establishing ecological equivalence.
See [taxonomy-notes.md](taxonomy-notes.md) and the
[primary](crosswalk-primary.csv) and [coarse](crosswalk-coarse.csv) maps.

The scalar retained fraction is retained recorded weight divided by declared
dryland recorded weight. It is **not** a guarantee that 80% of grains or
ecological information are represented. Outside-dryland and incomparable
weights are reported separately. `coverage.csv` carries exact rational values
alongside display decimals, and decisions use exact values.

`metadata-seed.csv` remains unchanged: 68 modern rows in 27 datasets and
27 actual collection units, with medium, altitude, resolution and preference
provenance. Unknown sample altitude or medium does not automatically exclude
a row. The two all-zero *Nothofagus* datasets remain taxonomically eligible
under the fixed six-dataset exclusion rule with unresolved resolution flagged;
both fail the calibration percentage screen above. See
[metadata-notes.md](metadata-notes.md).

## Sources and computation boundary

The saved-Neotoma reader is called three times, with explicit dataset lists,
element/ecological-group filters, units and absent-taxa-zero declarations:

| Source | Rows | Columns | Native units |
| --- | ---: | ---: | --- |
| Lake Selina 52767 | 72 | 66 | NISP |
| Tasmanian percentage datasets | 61 | 92 | percent |
| Hartz 74305 and Tyndall 74913 | 7 | 82 | NISP |

All extraction bundles inspect as verified and their tables match the prior
applications' tables. Original units and numbers are preserved. Raw and
mapped tables under `data/` are **unnormalised weights**. Study `exclude_taxa`
and `map_taxa` implement every exclusion and merge, recorded in
`derivation-records.json`. No stack or distance is constructed.
Community `validate` checks applicable nonempty multirow tables without
calculating distances or ordination. Empty mapped rows would remain in the
saved inputs and ledgers with explicit status, excluded only from validation
when that operation cannot accept them. The standalone repaired query is
checked through its validated full source, selection and mapping.

All 72 fossil IDs occur in `fossil-ledger.csv`. A below-floor level would be
`taxonomy_limited`; a zero retained row would be `empty_retained_row`.
The reconstructed 531331 query is prepared separately under both schemes,
from the previously accepted `counts-final.tsv`. Its only retained-source
cell change is the documented 0→72 *Lagarostrobos* count. This source is
already dryland; its coverage record does not reconstruct earlier out-of-sum
loss. The original 72-level table is unchanged.

`prepare.py` guards the toolkit's distance/analysis entry points with
exceptions, probes the guard, then requires zero subsequent calls. Extraction,
study preparation and validation run inside that guard. This checks the used
code paths; it is not an operating-system sandbox.

| Subtask outside a suitable public operation | Why | Implementation and check |
| --- | --- | --- |
| Metadata interpretation and identification-resolution audit | Reader copies metadata without interpreting notes or analyst resolution | Source-keyed seed, dataset-wide bin audit, explicit uncertainty |
| Weight partition, retained ratio and raw percentage screen during intake | Public community calculation combines totals with distances/ordination; no suitable totals-only operation is implemented yet | Exact rational accounting; source = outside-dryland + incomparable + retained; native merge totals agree exactly |
| Candidate and representative assignment | Matching method is not implemented; eligibility is a scientific intake rule | Explicit taxonomy, floor and calibration predicates; fixed preference per unit; all IDs/reasons exported |
| Tally-inclusion diagnostics | No matching public operation | Independent exact single-child/sum checks, bound to the historical script and receipt |
| Canonical column order and report CSVs | Formatting | Identical target sets required; no missing column filled with zero |

Revision 2.1's planned study exclusion totals should replace custom totals as
the main reporting source once implemented; the independent audit can remain
a cross-check. The present intake does not claim that interface already exists.

## Checks and regeneration

```bash
uv run palaeo-agent primer
uv run analyses/lake-selina-analogues/prepare.py
uv run analyses/lake-selina-analogues/audit.py
uv run analyses/lake-selina-analogues/prepare.py --output /tmp/selina-intake-check
```

The full primer was read before preparation and its unchanged version checked:
**0.2.0.dev0**, SHA-256
`fcc02a57db1ffa2a86d14e7c2540bd7bfa89c14e7e5b3334286f9a24b16747f6`.

All ten applicable raw/mapped multirow validations pass without warnings;
the two standalone-query entries are not applicable to community ordination.
The guard probe passes with **zero forbidden calls** afterwards. Exact checks
cover mass partitions, native API merges, shared dryland definitions and
retained-weight preservation under coarsening. A separate read-only audit
checks **282 accounting rows and 10,716 mapped cells** with zero mismatches,
as well as eligibility, calibration flags, preferences and tally diagnostics.
Its executable and receipt are [audit.py](audit.py) and
[audit-check.json](audit-check.json).

Fresh-output regeneration gives identical bytes for all **16 deterministic
preparation artifacts** and the preflight receipt. Extraction UUIDs and their
manifest hashes deliberately remain separate in `intake-provenance.json`;
native bundles are ignored by Git. See [replay-check.json](replay-check.json).
No engine code or original application files changed, so the full engine
suite was not rerun for these intake changes.

Claude next reviews the revised crosswalks, coverage, candidate sets and
representatives. Only after that review will one coherent commit freeze the
executable analysis and reviewed inputs before any real matching or threshold
preview. This intake establishes reproducible accounting under explicit rules;
it does not establish the scientific adequacy of the modern collection.
