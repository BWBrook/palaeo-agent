# Tasmanian modern pollen: montane against lowland (worked example)

Claude (Opus 5.5), 8 November 2026. This is application 2. It is the first
use of sprint 10's abundance input, together with the study layer's
`select`, `exclude_taxa` and metadata join, `community`, and `permanova`
with its descriptive dispersion. The scope follows Codex's
[review](REVIEW.md). Data imperfections are handled by declared working
conventions, following Barry's direction of 8 November 2026. The example
serves toolkit development and is not a vegetation calibration.

Reproduce from the repository root:

```bash
uv run analyses/tas-surface/intake.py
uv run analyses/tas-surface/analysis.py
```

The second command runs the whole toolkit study (`study.json`), inspects
it and writes `results.json`. A second run reproduces `results.json` byte
for byte. The primer is 0.2.0.dev0; its SHA-256 is in `results.json`.

## Question

Is pollen-category composition associated with the declared altitude
bands (≥ 700 m against < 700 m) among Tasmanian surface samples? The
spread within each band is described alongside.

PERMANOVA tests association. It cannot separate a shift in location from
a difference in dispersion. The groups are a declared split, not a
treeline.

## Data and working conventions

- **Source:** 25 IPPD surface datasets archived as percentages (Neotoma;
  CC BY 4.0), from the 8 November download (`source/`, SHA-256
  `0205169…58c36`). The two NISP datasets are left out.
- **One sample per dataset.** Every archived sample is labelled "surface
  sample", and the depth field is a sample index. The study's `select`
  step takes sample 1 from each dataset.
- **Altitude:** the sample's own altitude, where the collection notes give
  it (Mount Read 800 m, Piney Creek 172 m, Mount Anne 400 m). Otherwise the
  site altitude.
- **Groups:** 11 high and 14 low.
- **Categories:**
  - the TRSH and UPHE groups, minus Cyperaceae, Restionaceae and
    *Gymnoschoenus* (removed with `exclude_taxa`);
  - 89 categories in all;
  - archived labels are kept as distinct categories, even where they nest
    (for example *Nothofagus* beside *N. cunninghamii*). Nothing is merged.
- **Zero-fill:** absent entries are zeros.
- **Closure.** Row sums of the retained weights run from 17.1 (Boco Valley,
  sedge-dominated) to 242.5 (Naracoopa, whose archived percentages exceed
  100 for unresolved reasons). The primary analysis closes rows explicitly
  (`transform: relative_abundance`). This is a working reconstruction, not
  proof of a common denominator.
- **Exchangeability:** free permutations assume it. Sites cluster in
  space, and four records share archived coordinates in two pairs: Cradle
  Link Road with Vale of Belvoir, and Hardwood River Valley with Harlequin
  Hill. They are flagged in `data/samples.csv`, not merged.

## Results

| Analysis | Pseudo-F | R² | p (9,999 permutations) | Monte Carlo tail interval (95%) | Mean distance to centroid, high / low |
| --- | --- | --- | --- | --- | --- |
| Bray–Curtis on closed composition | 1.98 | 0.079 | 0.069 (687 extreme draws) | 0.064–0.074 | 0.442 / 0.508 |
| Jaccard occurrence (sensitivity) | 1.36 | 0.056 | 0.163 (1,632) | 0.156–0.171 | 0.485 / 0.477 |

The tail intervals come from `permanova` method version 2
(`permutation.tail_probability_interval`); neither run is
`monte_carlo_unresolved` at 0.05. Each interval covers the conditional
randomisation tail probability, not ecological uncertainty.

- **Association.** Under these conventions, the altitude band accounts for
  about 8 % of the closed-composition variation, and the association does
  not reach 0.05. In occurrence it is weaker still. The low band is
  slightly more dispersed in composition.
- **Description, from mean closed composition per band:**
  - montane samples carry more *Eucalyptus* (0.28 against 0.16), Poaceae
    (0.15 against 0.04), *N. cunninghamii* (0.17 against 0.12) and
    *Haloragis*;
  - lowland samples carry more *Lagarostrobos* (0.09 against 0.001),
    Ericaceae, *Melaleuca squamea*, *Leptospermum* and *Monotoca*. These
    are the western lowland rainforest and wet-heath signatures.
- **Ordination.** PCoA axis 1 holds 37 % of positive inertia, with a modest
  separation of the band means. The negative-to-positive inertia ratio is
  0.034.
- **Diversity.** Median positive-category richness is 20 (high) against
  16.5 (low). Median Shannon is 1.78 against 1.88. These describe weights;
  they are not count-based estimates.

**Reading.** Under these working conventions, montane and lowland
spectra overlap widely in these 25 selected records, and the 700 m split
organises them only weakly. The grass and *Eucalyptus* contrast fits open
montane vegetation and the regional pollen rain. Whether the weak
separation holds for Tasmanian surface spectra generally is beyond this
sample; moorland, wet heath and rainforest occurring across elevations in
the west would be one reason to expect it.

## What the toolkit did, and what it lacked

The whole analysis is one toolkit study: selection, taxon exclusion,
metadata join, two community runs and two PERMANOVAs. It inspects as
verified. Sprint 10 worked as specified on its first real dataset.

| # | Gap | Workaround here | Suggestion |
| --- | --- | --- | --- |
| 1 | PERMANOVA reported no Monte Carlo interval for its p-value | First computed by hand (0.064–0.074) | **Closed** in `permanova` method version 2; the table now quotes the toolkit field, which matches the hand and SciPy values |
| 2 | Both applications needed bespoke code to turn a Neotoma download into a table and metadata (units, groups, zero-fill, sample notes) | First `intake.py` (about 100 lines) | **Closed** by `neotoma_extract` (8 November 2026). `intake.py` now extracts the 25 declared percentage datasets into a verified bundle. Its table equals the earlier one value for value (rows now in source order), `samples.csv` and `study.json` are byte-identical, and the study results are unchanged apart from the primer hash |
| 3 | Group summaries (mean closed composition per group) are reporting arithmetic | `analysis.py` | Leave as glue for now |

## Unsupported parts

| Subtask | Why | What was used | How checked |
| --- | --- | --- | --- |
| Choosing sample 1 per dataset, reading sample altitudes from collection notes, assigning altitude bands | Caller decisions outside the extractor's scope | `intake.py`, reading `neotoma_extract`'s `samples.csv` | The extraction bundle inspects as verified (source hash, byte-for-byte re-derivation); `samples.csv` and `study.json` regenerate byte-identically to the versions Codex audited |
| Band means and medians | Reporting arithmetic | `analysis.py` (NumPy) | Computed only from verified study fields (`transformed_matrix`, `diversity`, `metadata`); `results.json` replays byte for byte |
