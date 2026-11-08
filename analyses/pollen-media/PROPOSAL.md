# Application 3: agreement among modern pollen collection media

Codex (`gpt-6.1-sol`), 8 November 2026. Selected after closing the saved-Neotoma
reader at `f578045`. This is a bounded toolkit case study. No composition,
sample richness, rarefaction or test result has been computed for this design.
Only extraction, metadata and the presence of the three exclusion labels
have been checked. Codex handles implementation and execution; Claude reviews
the scientific design and interpretation.

## Question

Within an archived mountain site, how closely do pollen traps agree with
core-top, moss-polster or surface assemblages? Which disagreements exceed
the toolkit's conditional counting-error model, and does standardising
count depth change the pollen-category richness comparison?

This bears on the comparability of modern calibration records assembled from
different collection media. It adds five within-site contrasts and a count
standardisation question using seven samples omitted from application 2.

## Frozen source and intake

Use the existing saved surface download, not a new live retrieval:
`../tas-surface/source/neotoma-tas-surface-download.json`, SHA-256
`0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36`.

The two datasets are [Hartz Mountains, 74305](https://data.neotomadb.org/74305)
and [Tyndall Ranges, 74913](https://data.neotomadb.org/74913). Their archived
collection notes identify the media below. The API extraction already
verifies as 7 samples × 82 categories. The structural intake receipt is
[`intake-check.json`](intake-check.json).

Call `neotoma_extract` with:

```json
{
  "source": "../tas-surface/source/neotoma-tas-surface-download.json",
  "source_sha256": "0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36",
  "datasets": [74305, 74913],
  "units": "NISP",
  "elements": ["pollen", "pollen/spore", "spore"],
  "ecological_groups": ["TRSH", "UPHE"],
  "absent_taxa": "zero",
  "row_order": "source"
}
```

The archived depth field is a sample index here. All Hartz ages are the same,
as are all Tyndall ages. Neither source order nor depth represents a temporal
sequence; do not request adjacent-pair tests or infer durations.

## Sample identities, order and contrasts

Use study `select` in this presentation order and join a seven-row metadata
CSV carrying site and medium. The mapping is transcribed from the archived
notes; retain the raw notes in the extraction bundle.

| Sample ID | Site | Archived index | Medium |
| --- | --- | --- | --- |
| 1466027 | Hartz Mountains | 1 | core top |
| 1466028 | Hartz Mountains | 2 | moss polster |
| 1466029 | Hartz Mountains | 3 | pollen trap |
| 1480879 | Tyndall Ranges | 1 | pollen trap |
| 1480880 | Tyndall Ranges | 2 | surface sample |
| 1480881 | Tyndall Ranges | 3 | surface sample |
| 1480882 | Tyndall Ranges | 4 | surface sample |

Fix these five explicit pairs, in this order, with the trap first:

```json
[
  ["1466029", "1466027"],
  ["1466029", "1466028"],
  ["1480879", "1480880"],
  ["1480879", "1480881"],
  ["1480879", "1480882"]
]
```

No cross-site hypothesis tests or selection of contrasts after viewing
distances. The three Tyndall surface samples are separate records, not three
independent replicates of a general collection-medium effect.

## Analysis fixed before results

All analytical specifications declare `value_type: "count"`,
`missing: "error"` and `empty_samples: "error"`.

Use one study from the verified extracted table, with two derived datasets:

- **Primary dryland sum:** study `exclude_taxa` removes `Cyperaceae`,
  `Restionaceae` and `Gymnoschoenus`, with the same stated convention as
  application 2. All three labels are present. Keep the remaining source
  labels unmerged; richness means pollen-category richness.
- **Pollen-sum sensitivity:** retain all 82 extracted TRSH/UPHE categories.
  This is the declared alternative to the primary exclusion, not a second
  opportunity to choose a preferred result.

| Quantity | API and settings |
| --- | --- |
| Primary totals, observed category richness, diversity and composition | `community`, counts, `relative_abundance`, Bray–Curtis, 2 PCoA dimensions; no eigenvalue correction |
| Primary expected richness at equal count and estimated coverage | `rarefaction`, `sizes: "minimum_total"`; the API resolves and records the common size |
| Primary pair differences and taxon contributions beyond counting noise | `count_homogeneity`, the five explicit pairs, `simulations: 99999`, `seed: 20261108` |
| Pollen-sum sensitivity | Repeat community and the same five-pair homogeneity family on the inclusive table, with the same settings; richness sensitivity across sums is outside this design |

For each homogeneity run, the five omnibus comparisons form one Holm family;
its full pair × taxon output forms the toolkit's separate taxon family. Keep
primary and sensitivity results labelled separately and report every pair.
Report the built-in Holm simulation-error envelopes; do not add draws or
change decisions in response to a borderline result.

Handle validation refusals through the primer's documented correction route.
Record any empty primary row or failed assumption before a justified,
prospective amendment; do not silently change the design to obtain a run.
All supported quantities, including totals and the rarefaction size, come
from API fields. Note interpretation/metadata transcription is declared
unsupported intake glue. Keep the primer's unsupported-parts table.

## Interpretation and stopping point

The conditional null is equality of the two counted category-probability
vectors. Sharing a trap across pairs makes those tests dependent; Holm does
not require independent p-values. These tests quantify counting error, not
environmental replication or variation among traps.

There is one trap per site, no exposure-duration metadata and no precise
positions or repeat dates for the surface collections. A difference can
reflect medium, local vegetation, integration time, sample placement or
other archive conventions. This design cannot identify a causal medium
effect or estimate a general bias. Decline PERMANOVA: two sites with this
sampling structure do not justify freely exchangeable medium labels. Do not
fit an age model or a trend.

Deliver a short report, verified study bundle and reproducible `analysis.py`:
five-pair Bray–Curtis/taxon/counting-error results, the primary observed and
rarefied richness profiles with common size and coverage, and the declared
pollen-sum sensitivity. Report warnings and assumptions, and any concrete
toolkit gap encountered. Fresh reproduction must retain numerical results;
separate bundle IDs and implementation provenance. No new toolkit feature
is required in advance. The minor verbose-inspection follow-up can wait.
