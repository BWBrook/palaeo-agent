# Community workflow results

Completed 30 October 2026, version 0.2.0.dev0. The bounded scope and scientific
definitions were reviewed with Claude through Correspondence Board thread 101.
The separate Claude review session accepted the design after its conditions
were addressed; that review did not execute numerical checks. The interactive
Claude session's future `references/r/` lane remains separate.

## What the workflow now does

The Llanvirn example runs from a declared count table through orientation,
ID-based metadata alignment, observed diversity, a chosen transformation and
dissimilarity, and uncorrected PCoA. All inputs, intermediate tables, full
eigenvalues, positive-space geometry and diagnostic figures are saved in a
self-contained run. RMA remains a supported method with unchanged coefficients.

The committed [comparison](../benchmarks/past/community-comparison/report.json)
contains both verified child bundles and a separate completion manifest. The
metadata file deliberately arrives in reverse sample order; it contains only
the administrative `archive_column` field and is joined by sample ID. It does
not supply ecological groups or environmental covariates.

## Prespecified development contrast

Plan and both example specs were committed in 228aa27. The same-environment
constraint was recorded in plan amendment 6377d9c before the final recorded
runs. Earlier numerical exploration is disclosed in the plan; this is a known
development example, not prospective efficacy or held-out evidence.

Baseline: relative-abundance Bray-Curtis for an exploratory compositional
question. Sensitivity: raw-count Bray-Curtis. The comparison verifies identical
input snapshots, IDs, metadata, diversity, exclusions and all other scientific
settings, and the same implementation fingerprint, Python and NumPy versions.
The executed example specs do not add a baseline hash retrospectively; the
comparison records both verified manifest hashes.

| Descriptive comparison | Result |
| --- | ---: |
| Samples / taxa | 10 / 23 |
| Sample totals | 13 to 702 |
| Pearson correlation of upper-triangle distances | 0.714815 |
| Spearman correlation of upper-triangle distances | 0.601054 |
| Symmetric Procrustes m², two-axis configurations | 0.490449 |
| Negative inertia magnitude, relative baseline | 0.000719547 |
| Negative inertia magnitude, raw sensitivity | 0.001401229 |

The transformation changes this example's dissimilarities and ordination
substantially. This does not establish that one representation is universally
preferable: totals can represent sampling effort, ecological density or both.
The raw-count total-imbalance lower-bound matrix is saved to show the portion
of raw Bray-Curtis forced by unequal totals. There are no p-values or group
inference. Diversity is plug-in, observed and unstandardised, with sample N
shown in each plot; sampling-effort comparisons require additional methods.

## Numerical and execution evidence

- **Three cross-implementation cases:** raw Bray-Curtis, relative Bray-Curtis
  and binary Jaccard agree with base R 4.6.1 `stats::dist` and `cmdscale`.
  Diversity definitions are also checked in the R reference script.
- Maximum distance disagreement is 2.22e-16; maximum eigenvalue disagreement
  is 1.33e-15; maximum full positive-space Gram disagreement is 8.05e-16.
  Declared comparison tolerance remains `rtol=atol=1e-10` for this example.
- Axis signs are not compared. Full positive-space Gram geometry is always
  checked; selected-axis geometry is checked only when the recorded eigengap
  establishes an identifiable cutoff. Negative eigenvalues are retained and
  diagnosed, without Cailliez/Lingoes correction.
- Both copied child bundles reproduced in fresh processes, with no numerical
  differences and identical recorded environments.
- **95 tests passed locally**, including the original RMA numerical cases,
  orientation/count/missing-data failures, metadata joins, ambiguous eigenaxis
  cutoffs, input/artefact corruption and rejection of confounded comparisons.
- Source distribution and wheel builds passed. An actual installed-wheel run
  and inspection confirmed that missing checkout lockfiles are explicitly
  recorded, with installed distribution versions retained.
- Both saved plots were visually inspected. Sample labels were separated after
  the first rendered plots showed collisions; numerical values were unchanged.

Reference scripts and recorded versions live in
[the R library reference](../benchmarks/past/references/community-base-r.json).
[The verification report](../benchmarks/past/references/community-verification.json)
records comparison errors and reproduction outcomes. Regenerate with:

```sh
python3 scripts/reference_community.py
uv run python scripts/verify_community.py
```

R and jsonlite are optional reference-generation requirements, not runtime or
CI requirements for Python analysis. This is not yet a separately renv-locked
R environment, a vegan comparison, a PAST numerical match or general method
validation. Package source fingerprints and captured Python lockfiles concern
the implemented engine; operating-system libraries are not container-frozen.

## What Claude's review changed

The review changed the demonstration's baseline to match its compositional
question, strengthened diversity caveats and sample-size labels, rejected a
no-op Jaccard transformation, and required checked sensitivity artefacts. A
subsequent focused review identified the need to hold numerical implementation
and environment fixed between sensitivity arms; that is now enforced and tested.

The evaluation protocol now counts refusals/failures on solvable trap tasks
against the toolkit and retains authoring records encrypted for audit. Its
development principles are accepted; confirmatory trial design, key custody
and execution infrastructure remain provisional. No agent trial campaign was
run, and no reduction in agents' error rates is claimed.

The installed Mac PAST About dialog was inspected and reports version 5.4.
No numerical GUI reference run was executed during tranche 2. The next useful validation work
is a curated PAST capture and/or the interactive Claude reference lane, followed
by a small development smoke of the agent evaluation protocol. Additional
methods should follow scientific demand rather than precede those checks.

The subsequent [31 October validation tranche](validation-tranche-3-results.md)
completed the scoped native PAST captures and independent R/vegan regeneration.
The following [blind-fixture tranche](validation-tranche-4-results.md) repaired
the earlier warning-only treatment of cutoffs inside tied positive eigenspaces.
