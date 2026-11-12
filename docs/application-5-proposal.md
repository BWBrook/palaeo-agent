# Application 5: robust pollen zonation of Lake Selina

Codex, 9 November 2026. Proposed in response to Claude's Board 3135.
**GO for the zonation tranche; design accepted by Claude in Board 3246.
The implementation and both saved-record repairs are accepted at `c38696d`;
see the [implementation review](sprint-14-implementation-review.md). The executable
design was frozen at `20c68c2` before any core zonation. The four fixed analyses
are now complete; see the [results report](../analyses/lake-selina-zonation/REPORT.md).**
The sections below preserve the pre-results proposal.

## Research question

**Which contiguous compositional zones does a fixed CONISS procedure
identify in the Lake Selina pollen sequence, and which boundaries persist
when the inferred missing count and the weighting of dominant pollen
categories are changed?**

The scientific target is a reproducible summary of stratigraphic composition
and its sensitivity to two specific choices. The expected broad succession
is basal forest, herb-rich sediment and upper forest, but whether one chosen
partition reproduces that reading is an outcome, not an acceptance test.
Do not tune the transform or retention rule to recover the published zones.

This is a second use of an already inspected core. The published vegetation
interpretation, earlier distances/tests and the source-paper zone boundaries
have already been seen. Only the new algorithmic outputs are unseen; this
is not independent validation or a blind discovery of ecological transitions.

## Fixed source and pollen sum

Use the saved Neotoma dataset 52767 and the existing 72 sample IDs, in
strictly increasing **archive depth, 80–427 cm**. The existing source,
extraction checks and original intake remain unchanged. At launch, use
`neotoma_extract` on the pinned saved download with dataset 52767, NISP,
pollen, ecological groups TRSH/UPHE, absent taxa zero and depth order;
inspect its bundle and confirm the frozen archived table before the study.

The primary input is the **archived-count dryland definition**: the 66
land-plant pollen categories in `analyses/lake-selina/data/counts.tsv`,
followed by the existing study `exclude_taxa` step for Cyperaceae,
*Gymnoschoenus sphaerocephalus*, Restionaceae, Xyridaceae, Portulacaceae and
*Ranunculus*. It reproduces the 60-category `counts-dryland.tsv`. This keeps
the earlier paper-informed denominator; it does not claim an exact
reconstruction of every printed pollen sum. Preserve broad and genus-level
categories separately. Apply no rarity cutoff, taxon merge, sample exclusion,
rarefaction, pseudocount or time/depth weighting.

A declared sensitivity uses `counts-final.tsv`, the accepted working
reconstruction from amendment 2. It differs in exactly one cell:
*Lagarostrobos franklinii* at sample **531331, archive 220 cm**, is 72
instead of 0. Choosing archived counts as the baseline lets this application
measure the effect of that inference; it neither changes nor withdraws the
previous reconstructed example. Neither version establishes the true count.

The preparation check verified this one-cell difference, matching sample IDs
and strictly increasing depths. It computed no zonation or composition metric.

| Frozen input, relative to `analyses/lake-selina/` | SHA-256 |
| --- | --- |
| `source/neotoma-52767-download.json` | `5dd1a71cf7a655f08441e59b866b3eb64c893b164cc8e9320d9ea2d7507ead24` |
| `data/counts.tsv` | `db922456a78fc78754f8d950066f9032659079808966dcd6de38f2457c6423a6` |
| `data/counts-dryland.tsv` | `3ab89275221f80b190dbf34b83cc5eebd1f339378b28e402df6b93f8d4d6bfe1` |
| `data/counts-final.tsv` | `a15f912401a46242a38b48d51211acfb731d70743190cefa27c75474c429d429` |
| `data/levels.csv` | `806c28064bf275275e8fde15e03fd8a0e5a71b248ab016e16551f71d3376840f` |

## Four analyses, fixed before results

For every row, first calculate proportions within the retained dryland sum.
The primary coordinates are **square roots of those proportions**. This
Hellinger representation reduces the dominance of abundant categories while
retaining their compositional information. The sensitivity uses the
proportions themselves. Neither representation propagates unequal-count
sampling uncertainty.

| Role | Count version | Coordinates |
| --- | --- | --- |
| Primary | Archived dryland | sqrt(row proportions) |
| Imputation sensitivity | Reconstructed dryland | sqrt(row proportions) |
| Weighting sensitivity | Archived dryland | row proportions |
| Combined sensitivity | Reconstructed dryland | row proportions |

Run the same adjacent-only, greedy incremental-sum-of-squares hierarchy and
broken-stick rule in all four cases. Samples have equal weight. Sample order
constrains eligibility; physical depth gaps do not contribute to the merge
cost. No alternative dissimilarity search is proposed. In particular, the
existing Bray–Curtis summaries are context, not an input to this SS hierarchy.

At each merge, choose the adjacent pair minimizing
`n_A*n_B/(n_A+n_B) * squared_distance(mean_A, mean_B)`, with an exact tie
resolved toward the shallower/leftmost pair. Retain the actual merge cost
and the cumulative total within-zone SS separately. Individual merge costs
can decrease under the adjacency constraint; do not sort or monotonize them.
This is a greedy hierarchy, not a globally optimal segmentation at every k.

### Declared broken-stick convention

The contract must distinguish the comparison table from the chosen cut.
Let m=n−1, H_j be total within-zone SS after j agglomerations, and H_0=0.
For top-down split rank r=1,...,m, define gain
`g_r = H_(m-r+1) - H_(m-r)` and expectation
`e_r = H_m/m * sum(1/j for j=r,...,m)`.

Start at one zone. Accept successive splits while each `g_r > e_r`; stop
at the first failure, with equality a failure. The resulting zone count is
one plus the length of that passing prefix. This is our explicit conservative
selection convention, not a uniquely specified automatic choice returned by
`rioja`. Report every comparison and later exceedance, rather than discarding
values after the stopping point or silently limiting the display to ten zones.
A zero-dispersion sequence has one zone and a stated diagnostic.

Each run reports its own selected k. Also compare its boundaries at the
primary run's selected k, a rule fixed now, to distinguish changes in the
hierarchy from changes caused by selecting a different number of zones.
The contract may implement a requested cut separately from the broken-stick
recommendation; no set of alternative k values is searched for a preferred
result. If the rule keeps one zone, report that outcome without a forced split.

Call these **broken-stick-retained zones**. The criterion supplies neither
calibrated p-values nor confidence intervals on boundaries. No bootstrap or
boundary-location uncertainty method is included in this tranche.

## Depth and interpretation

For every boundary, report the two adjacent sample IDs and their archive
depths. A midpoint may be plotted only as a drawing convention; the result
is a between-sample interval. Zone labels increase from shallow to deep.
Show the actual depth spacing in the diagram while keeping the clustering
weights equal.

**Persistence means the identical gap between the same two sample IDs.**
A boundary displaced by even one level is not persistent. Report exact
matches first, then all unmatched boundaries in each partition. For
descriptive proximity, associate each unmatched sensitivity boundary with
the nearest primary boundary by gap index; break an equal-distance tie
toward the shallower gap. State explicitly that this can be many-to-one
and does not establish that the two boundaries represent the same event.
For every such comparison, name both ID brackets and give the signed
offset in gap indices (positive is deeper), plus the signed changes in
both bracketing depths in centimetres. This avoids treating a between-level
boundary as an exactly located event. If the primary has one zone, there
is no reference boundary and no offset; list the sensitivity boundaries
without a forced match. Apply the same reporting rule to each run's chosen
partition and to the cuts at the primary-selected k. No tolerance window
or approximate match counts as persistence.

The +30 cm archive offset is a supported candidate alignment, not established
for every coordinate. Candidate paper depths may be shown as secondary
labels, clearly marked `archive minus 30 cm`. **Do not use ages to fit,
choose, name or date zones.** The inferred chronology and age windows from
amendment 2 are not inputs. No duration, rate, climatic-event, human-arrival,
megafaunal or causal attribution is claimed.

Compare the new partitions descriptively with the already-known herb-rich
interval and upper forest recovery, and with the published zone interpretation.
If using the paper's boundary labels, lock their transcription before launch.
Do not label correspondence with the earlier adjacent-pair tests as independent
confirmation, calculate post-selection zone p-values, or run PERMANOVA on
core horizons grouped by the newly chosen zones.

## Necessary sprint-14 scope and reference check

Add a `coniss` method accepting declared count/abundance tables, sample order,
row-proportion or square-root-proportion coordinates, a complete merge record,
cumulative dispersion, the complete broken-stick comparison and deterministic
cut memberships/boundaries. Reuse the study and bundle mechanisms. Leave
unconstrained clustering, alternate linkage methods, age modelling and
uncertainty in boundary positions outside this contract.

**Reference trap:** the official `rioja` wrapper passes the supplied
dissimilarities unchanged, and its C++ initializes the singleton merge cost
as half that value. To check the centroid SS objective above, give it
**squared Euclidean dissimilarities of the chosen coordinates**. Its manual's
unsquared `dist(...)` example is a different numerical convention. A two-point
one-dimensional fixture at 0 and 2 has within-SS=2: supplying squared distance
4 gives 2, whereas supplying distance 2 gives 1. Pin the reference package
version and test this simple fixture independently, alongside nontrivial
trees, ties and constant sequences. Compare cumulative dispersion and
partitions, not just a plotted dendrogram. Direct centroid calculations and
the reference recurrence can round differently near a tie: diagnose such
cases explicitly rather than weakening whole-tree acceptance tolerances.

`bstick.chclust` returns comparisons rather than a selected zone count. Its
`diff(rev(height))` also omits the final split, so requesting all n groups
produces a missing final gain. Construct the complete series with H_0=0,
compare all valid reference rows, and independently test the final rank and
the selection convention. Do not copy the display truncation or treat an
`NA` as a substantive stopping decision.

Sources inspected: the official [package manual](https://search.r-project.org/CRAN/refmans/rioja/help/chclust.html),
[R wrapper](https://raw.githubusercontent.com/cran/rioja/master/R/consclust.r),
[C++ implementation](https://raw.githubusercontent.com/cran/rioja/master/src/chclust.cpp),
[broken-stick code](https://raw.githubusercontent.com/cran/rioja/master/R/bstick.r),
and [Bennett's own manual](https://chrono.qub.ac.uk/psimpoll/psimpoll_manual/4.27/ppmenm2.htm).
The method papers are Grimm (1987), *Computers & Geosciences* 13, 13–35,
[10.1016/0098-3004(87)90022-7](https://doi.org/10.1016/0098-3004(87)90022-7),
and Bennett (1996), *New Phytologist* 132, 155–170,
[10.1111/j.1469-8137.1996.tb04521.x](https://doi.org/10.1111/j.1469-8137.1996.tb04521.x).
Their full texts were not retrieved for this design; no claim of full-paper
verification is made. An independent bounded methods review checked the
source conventions and these limits before this draft was committed.

## Delivery and stopping condition

After the contract and implementation are reviewed, freeze the executable
study without computing the core's new clustering outputs. Then run the four
analyses through the toolkit, inspect and reproduce the bundles in a fresh
worker, and cross-check the tree/dispersion/broken-stick values and cut
memberships against pinned `rioja` under matched conventions. All reported
scientific numbers must come from inspected API fields.

Deliver one short scientific report, a depth-aligned pollen/zone/dendrogram
figure, a table of all selected boundaries and the four sensitivities, and
the unsupported-parts table. A stable partition, an unstable partition or
no retained split all complete the scientific question. Stop after that
verified synthesis and one independent scientific review; do not add methods
until another research question requires them.

Extraction, pollen-sum exclusion and metadata joins already use the toolkit.
CONISS was unavailable when this question was drafted; its implementation
and saved-record repairs are now accepted for execution.
No supported analysis is bypassed. Paper interpretation, candidate-depth
annotation and the independent R
arithmetic reference remain declared external work. Reading/formatting
result fields is reporting glue.
