# Application 2 and sprint 10: scope review

Codex (`gpt-6.1-sol`), 8 November 2026. Review of `49c57d5` and
[PROPOSAL.md](PROPOSAL.md). **Proceed with fractional abundance support and
the worked example, using the adjustments below.** Source imperfections need
declared working assumptions, not another record-repair project.

No composition, ordination, diversity or PERMANOVA result was calculated in
this review. JSON/metadata inspection is unsupported intake work. The full
primer was read (0.2.0.dev0, SHA-256
`1557cf7444a59526c8d6e9b910ec3b4a9103e21c4f1714fe032a51ededa6486b`),
and the current method requirements and output definitions were checked.

## The application

Reframe the question as **association between the declared altitude bands
and the selected pollen-category compositions, accompanied by descriptive
dispersion**. The existing dispersion diagnostic cannot establish that a
PERMANOVA result is a pure location shift. The method can confound location
and dispersion; [vegan's primary documentation](https://vegandevs.github.io/vegan/reference/adonis.html)
states this limitation.

One selected record per actual sampling unit is sensible. It does not by
itself establish free exchangeability across spatial clusters or sources.
Treat the one-way free-permutation analysis as a worked example under an
explicit working exchangeability assumption, with the observed spatial/source
structure recorded. Do not claim a causal altitude effect, a separation of
location from dispersion, or an independently validated treeline calibration.
No restricted-permutation engine or dispersion hypothesis test is requested
in sprint 10.

### Intake facts that change the proposal

The saved download's SHA-256 is
`0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36`.
It contains 27 distinct archive site IDs/collection units/datasets and
68 samples. These identifiers are not proof of 27 independent field sites.

- **Groups:** site-level altitude gives 13 high / 14 low, rather than
  14 / 13. The 25 percent datasets contain 61 samples and give 11 high /
  14 low by site altitude. The two NISP datasets contain seven samples,
  both from high-altitude records.
- **Sample choice:** depth can be a sample index. Mount Anne's collection
  notes describe an elevational transect: sample 1 at 400 m, 2 at 500 m,
  4 at 750 m and 7 at 600 m. Tyndall sample 1 is a pollen trap; Hartz
  distinguishes a core top, moss polster and trap. Do not call the
  minimum-index sample the uppermost surface horizon. Select a declared
  eligible modern sample using the saved notes; prefer sample altitude
  where supplied, and label site-altitude substitution as an assumption.
- **Attribution:** all sample-analyst objects are null. There are eight
  distinct dataset-PI identifiers, which are source-attribution proxies,
  not evidence for six actual analysts. Record source group without
  claiming analyst adjustment.
- **Coordinates:** two pairs of differently named records share archived
  coordinates; one pair even has different reported elevations. Coordinates
  may be coarse. Flag the clusters; do not automatically merge records.
- **Percentage sums:** eight minimum-index percent samples have TRSH+UPHE
  sums above 100. Naracoopa dataset 74764/sample 1477443 sums to 242.54,
  with distinct values for Leptospermum (91.85), Banksia (79.09) and
  Monotoca (38.60). These are unique pollen/percent entries, not repeated
  taxon IDs or mixed units. The cause is unresolved. Row closure can be
  the example's explicit working reconstruction; it does not prove a
  common original denominator.
- **Categories:** TRSH+UPHE is not automatically a dryland sum; it can retain
  wetland taxa. Declare the retained categories and the mapping before
  results. Do not automatically sum broad categories with their genera
  without an explicit disjoint-category assumption. Sparse zero-fill and
  the effect of rounding on presence also need a stated working convention.

For the first run, use the **25 percent records**. This exercises the new
capability without a mixed-unit conversion step. The two counted records
can be added later through an explicit count-to-relative-abundance route;
never label unchanged counts as percentages. Tabulate final group sizes
after sample selection and altitude assignment. The 700 m boundary can stay
as the declared example split, without calling it a universal treeline.

## Minimal coherent sprint 10

**Recommendation: one explicit `value_type: "abundance"` branch for finite,
nonnegative fractional weights**, alongside strict `"count"`. Percentages
and proportions are supported representations of that branch. Record the
source units and denominator/working interpretation in intake/provenance;
do not infer units from row sums or integer-looking cells. A separate public
value type for every common scaling is unnecessary for these calculations.

### Preserve transformation meaning

- `transform: "none"` preserves supplied values. It means untransformed
  weights, not necessarily raw counts. Raw Bray–Curtis on percentage weights
  is mathematically defined; it should not be refused merely for lacking
  integer counts.
- `transform: "relative_abundance"` explicitly closes retained rows to one.
  After exclusion this describes composition conditional on retained
  categories. Do not close rows silently because the input is non-count.
  Row-total standardisation has this definition in
  [vegan's documentation](https://vegandevs.github.io/vegan/reference/decostand.html).
- Binary Jaccard stays `value > 0`, with `transform: "none"`. Preserve
  zeros; introduce no rounding or automatic detection threshold.

### Keep valid outputs and honest labels

PCoA, the supported dissimilarities, positive-category richness, Shannon
and ordinary Simpson diversity remain available. Shannon and Simpson use
normalised relative weights; they do not require specimen counts.
[Vegan distinguishes these from count-dependent estimators](https://vegandevs.github.io/vegan/reference/diversity.html).
They remain conditional descriptions of the retained category weights.

An abundance row sum is useful provenance, but must be labelled a **weight
sum**, not specimen N. Update result models, plots, tables and comparison
wording accordingly, including `raw_count_total_imbalance_bound`. Keep
rarefaction, coverage/singleton estimators, count homogeneity and their
uncertainty calculations strictly count-only.

### Study operations and refusal boundaries

Declare the new input kind and bind it to each analysis's value type.
An integer-looking percentage table must not become eligible for count-only
methods. `exclude_taxa` preserves remaining values without renormalisation.
`map_taxa` can sum declared disjoint weights sharing a denominator; preserve
decimal addition without a float round trip or hidden default-context
rounding. Retain the exact integer path for counts.

Finite cells alone are insufficient: guard nonfinite totals/arithmetic and
positive tokens that would silently underflow to zero. Preserve existing
missing/empty-sample, orientation, metadata, ordination-rank and inference
restrictions. This is input support, not a new inferential method.

### Acceptance checks

1. Existing count arithmetic and refusals stay unchanged. Abundance input
   is refused by rarefaction and count homogeneity, including integer-valued
   examples and conflicting study/method declarations.
2. A common factor of 100 leaves distances and descriptive diversity
   unchanged. Row-specific scaling affects raw Bray–Curtis but disappears
   after explicit closure; Jaccard is unchanged for preserved positive cells.
3. Fractional exclusion/merging, empty samples and decimal precision have
   focused tests; unsupported numerical values are refused without coercion.
4. Inspection binds type, retained values and transformation to the saved
   specification. Exercise altered results with updated hashes.
5. R references compare the new distance/diversity/PERMANOVA quantities
   under matched inputs and permutation conventions. Check CLI/MCP schema
   exposure and a small study end to end.

Write the concise contract, implement within this scope, then run the
conditional example. No curator contact or further source-paper campaign
is needed to begin toolkit development.

## Small note on the sprint-9 real-data check

The receipt correctly records **74 compared pairs**, although all 77 pair
identities match. `study_check.py` builds its comparison lookup from adjacent
and primary pairs and omits the three saved alternative pairs. Include those
already available `ippd1_sensitivity` records to check all 77. This is a
reporting-coverage fix; it needs no new analytical run and does not block
sprint 10.
