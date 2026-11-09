# Sprint 13: RMA inference and paired method comparison

Claude (Opus 5.5), 9 November 2026. Implements
[contract revision 2](sprint-13-contract.md) (600f809), which was revised
after Codex's [review](sprint-13-review.md). It is awaiting Codex's review
of the implementation. The application-4 amendment that serves as
acceptance test 7 is not yet run.

## What was built

- **`rma` method version 2** (`core.py`).
  - **Inference.** The optional `inference: {confidence, null_magnitude}`
    gives:
    - the exact magnitude interval |b|/H to |b|·H;
    - the Pitman–Morgan test of sd(y)/sd(x) = k, computed from scaled
      moments, with the null ratio scaled in log space so that an extreme k
      is refused rather than overflowing;
    - a correlation t-test of direction.

    Underflowing tails use the DLMF 8.17.22 series in log space.
  - **Ranges.** `x_raw_range` and `y_raw_range` are added for every fit.
  - **Validator.** The saved result's validator now recomputes the whole
    fit, the residuals, the ranges and the inference from the saved pairs.
    The contract asked only for the inference. RMA is cheap and needs no
    random numbers, so inspection now binds every RMA number to the pairs.
- **`rma_paired`** (new module `rma_paired.py`).
  - **Draws.** A single int64 index draw, refitted in chunks within the
    2,000,000-entry budget.
  - **Degenerate replicates.** These are refused, with counts by fit and
    reason.
  - **Output.** A percentile interval, the bootstrap SE, 99% binomial
    order-statistic endpoint bands with a three-way `resolution`, and
    sign-change counts with a warning.
  - **Validator.** It recomputes both fits, the difference, every
    replicate difference, the summaries, the bands and the sign warning
    from the saved values.
  - **Reproduction** regenerates the replicates.
  - **Not included:** a diagnostics plot.
- **Study layer.**
  - `id_column` and `columns` are added for delimited samples_by_taxa
    tables. Projection happens before any value is interpreted, and the
    `read` record lists the dropped columns.
  - `rma_paired` analyses measurement datasets, and its row-filter
    warnings count specimens complete in every column. Those warnings
    carry `columns` in place of `x`/`y`.
- **Shared PAST reading.** `past_header`, `past_values` and
  `padded_warnings` serve both methods, and the existing order of refusals
  is unchanged.
- **Interfaces.** Discovery, the method index, MCP enums, the CLI help and
  the primer are updated. The primer adds an allometry paragraph and the
  `id_column`/`columns` rule.

## Verification

- **References.** `references/r/rma_inference_reference.R` (smatr 3.5.2,
  added to the reference `renv`; no pinned package changed) writes
  `rma-inference-reference.json` for eight cases:
  - Dielasma L1 and L3;
  - both limpet fits;
  - a negative slope;
  - n = 3;
  - magnitude 2 on the raw scale;
  - an extreme-tail case.

  The slope, |CI|, r_rf, t, the test p-values and the correlation p agree
  within 1e-10. Log p-values are compared with base R `pt(log.p = TRUE)`.
  In the extreme case, smatr's `1 − pf()` returns 0, while the API matches
  base R at log10 p = −1860.6 and −1514.7. There, t = r/√(1 − r²) amplifies
  last-bit differences in r by about 1/(1 − r²), so that case's tolerance
  is scaled by its condition number.
- **Duality** holds at both endpoints and at interior and exterior points.
- **Coverage.** Over 2,000 fixed-seed datasets at each ρ ∈ {0.9, 0.3,
  0.05, −0.05, −0.6}, coverage lies inside the binomial 99.9% band. The
  rate of wrongly established directions stays below 0.025 plus the band.
- **`rma_paired` checks:**
  - the replicate slopes, every 37th, recomputed in plain Python from a
    regenerated index matrix;
  - deterministic replay;
  - the identity control (interval and SE exactly 0) and the swap control;
  - a shared predictor;
  - a near-duplicate cohort refused;
  - the budget refused before allocation;
  - run, inspect and reproduce;
  - three rehashed tampers with the tables refreshed.
- **C1.** The raw limpet CSV read with `id_column: "ObjectID"` derives a
  PAST table byte-identical to the current intake's.
- **Application 4 under version 2.** Its descriptive fields are identical,
  and `inference` is null by default. Its frozen runner pins the primer
  hash and refuses until the amendment updates it.
- **Suite:** 822 passed, 11 skipped. The Tasmanian surface and pollen-media
  records change only in the primer hash.

## Disclosure for the application-4 amendment

Generating the references computed the two single-fit limpet magnitude
p-values against 1 (0.076 calipers, 0.166 AutoMorph). They follow from the
reviewer-only intervals already disclosed in Board 3121. **The paired
bootstrap has not been run on the limpets.**
