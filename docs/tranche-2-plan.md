# Community workflow tranche

Status: bounded scope and definitions accepted in the separate Claude review
session in Board message 2611; Codex's resolutions to its conditions are recorded
in message 2613. Barry authorised collaborative implementation on 30 October
2026. Numerical definitions were posted before implementation in messages
2605–2608. Cross-implementation references use base R; the interactive Claude
session's separate reference lane remains available for later work.

## Scope and division

One complete descriptive workflow: a declared count matrix, diversity,
dissimilarities, uncorrected PCoA, named intermediate artefacts and a sensitivity
comparison. Codex implements and integrates the Python core and execution
contract. Claude's agreed role is evaluation design, independent R references
and adversarial review. File claims and review correspondence live in the
`palaeo-agent` Board section. Barry receives decisions and material questions
through the agents' chats; he is not expected to read the Board.

The shared checkout is on macbook. Stage only owned files; preserve another
writer's dirty work. Pull with fast-forward only when the tree is clean and
no writer is active. Commits and pushes remain on the private main branch.

## Frozen development input

`benchmarks/past/legacy-data/llanvirn.dat`, SHA-256
`a39a2ec7ef405623efdac5e5cd2b9be7dd38e5ca98c4fe9efa4dab2cda076f37`.
The source has 23 taxa in rows, ten samples in columns. Preserve every label,
including the original taxon prefixes. Explicitly transpose to the canonical
sample-by-taxon matrix. Sample totals in source order are
321, 243, 304, 156, 473, 702, 26, 68, 57 and 13.

This is a known development example, not held-out evaluation material. No
metadata group comparison or causal interpretation is inferred from it.

## Definitions

Declared values are counts: finite, nonnegative, exactly representable integers.
Integer appearance is a numerical diagnostic, not evidence of sampling meaning.
Missing values fail and never become absences. Exact sample/taxon IDs are
unique; near-duplicates generate informative warnings without automatic merges.
Empty samples fail unless an explicit policy excludes them and records the IDs.

Optional metadata CSV has a unique `sample_id` column and exactly the original
matrix sample ID set. Join by ID before exclusions, never by position. A metadata
file is not required for exploratory diversity and ordination.

For retained raw counts, compute total N, observed richness, Shannon entropy
using natural logs and zero terms equal to zero, and Simpson diversity
`1 - sum(p_i**2)`. Do not apply bias correction or report inferential intervals.

Before distances, explicitly select raw counts or relative abundance (divide
each retained row by its total). Bray-Curtis is `sum(abs(x-y))/sum(x+y)`.
Jaccard is binary occurrence dissimilarity, `1 - intersection/union` after
mapping positive counts to occurrences. It is not quantitative Jaccard.

PCoA double-centres squared distances and diagonalises the resulting symmetric
matrix. Preserve the complete sorted eigenvalue spectrum. Select requested
positive coordinate axes; fail if there are insufficient positive axes. No
Cailliez or Lingoes correction is applied. Report numerically negative eigenvalues,
their magnitude and their ratio to positive inertia. Axis proportions explicitly
refer to positive inertia rather than total variance. The numerical threshold
is `machine_epsilon * n_samples * max(1, max(abs(eigenvalues)))`.

Save the full positive-space Gram matrix as invariant geometry, in addition
to the requested coordinates. Signs and rotations, particularly when a selected
axis boundary falls inside a repeated eigenspace, are not correctness criteria.

## Execution and provenance

RMA and community are distinct typed methods with method-owned validation,
calculation, outputs and comparisons. Validation of community inputs does not
compute pairwise distances or eigendecompositions. Guard dense matrix allocation
before starting the numerical calculation.

Use one self-contained bundle per workflow, with a portable resolved spec,
named input snapshots, retained counts, transformed matrix, diversity,
dissimilarities, eigenvalues, coordinates, diagnostics, full results and a
completion manifest. Name the producing step for intermediate artefacts.
Record installed distributions and explicit lockfile availability, including
wheel installations where no checkout lockfile exists.

The development manifest becomes schema 2. Regenerate the committed RMA example
under the new contract and document the change. Its original schema-1 evidence
remains in Git commit 445da1b; do not relabel old results or add compatibility
dispatch solely for a development format.

## Sensitivity and acceptance

Baseline: relative-abundance Bray-Curtis, for the explicit exploratory question
of compositional differences among samples. Sensitivity: raw-count Bray-Curtis,
same matrix and diversity definitions. Standardisation is a declared choice,
not evidence that sample totals contain no ecological information. The sensitivity spec records
the baseline manifest hash and its purpose, without recursive parent resolution.
Jaccard is another explicitly selected distance, tested against references.
Relative abundance plus binary Jaccard is rejected as a no-op combination.

A separate comparison step consumes both verified bundles, checks identical
input hashes and fixed settings, and permits only transformation/distance and
relationship/purpose differences. It copies both bundles into its own
self-contained, checksummed comparison artefact. Report upper-triangle distance
Pearson/Spearman correlations, a descriptive symmetric Procrustes statistic
when the selected subspace is identifiable, and the raw-count Bray-Curtis
lower-bound matrix `abs(N_i-N_j)/(N_i+N_j)`. There are no p-values.

Compare selected-axis Gram geometry only when the cutoff eigengap relative to
the leading eigenvalue exceeds 1e-8; otherwise report that the selected subspace
is ambiguous. Always compare the full positive-space Gram matrix. Plug-in
diversity is observed and unstandardised: unequal totals confound direct
sampling-effort comparisons. Plot sample N and defer rarefaction/coverage.

Both example specifications and this plan are committed before the final
recorded baseline/sensitivity runs. Earlier numerical exploration and reference
generation have already occurred and are not retrospectively prospective.

Check simple analytical diversity/distance controls, label/orientation changes,
metadata order/mismatch, missing and empty samples, rank and negative inertia.
Compare independently authored reference values for diversity, distances,
eigenvalues and full positive-space geometry. Proposed reference tolerance is
`rtol=atol=1e-10`, subject to reference review before numerical comparison;
this is not a blanket precision claim for other methods or datasets.

Acceptance requires fresh-process reproduction from snapshots, structured
rejection of damaged bundles, retention of RMA numerical checks, inspection of
figures and independent review. Cross-language validation and actual PAST GUI
agreement are separate evidence levels; do not claim either without results.

The installed macOS PAST About dialog was directly inspected through CUA on
30 October 2026 and displays Past 5.4, October 2026. This corrects reliance on
the website's older Mac download label. No new numerical GUI reference is
implied by that observation.

## Deferred

Group inference, RMA slope inference, NMDS, rarefaction, arbitrary data-format
support, MCP servers and recursive DAG storage remain outside this tranche.
Evaluation design proceeds alongside development, but no agent trial campaign
or held-out key-custody infrastructure is launched. Future efficacy claims need
separately frozen tasks, a pinned implementation and a justified trial design.

## Primary implementation references

- [vegan diversity definitions](https://vegandevs.github.io/vegan/reference/diversity.html).
- [vegan dissimilarity definitions](https://vegandevs.github.io/vegan/reference/vegdist.html).
- [Classical scaling and negative axes](https://vegandevs.github.io/vegan/reference/wcmdscale.html).
- [Symmetric eigendecomposition](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html).
