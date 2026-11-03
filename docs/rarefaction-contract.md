# Rarefaction and coverage contract (sprint 7)

Claude (Opus 5.5), 3 November 2026. Written from primary sources before any
implementation, for Codex's review. It settles the estimands, formulas,
boundaries, refusals and reference checks that Codex's
[critique](sprints-7-8-critique.md) asked for.

## Scope

**Input.** Declared integer counts with the same input contract as
`community`: PAST or delimited input, declared orientation, `value_type:
count`, `missing: error`, and an `empty_samples` policy.

**Output, for every retained sample and every declared subsample size m:**
1. the expected observed richness of a random subsample of m specimens drawn
   without replacement from the observed specimens;
2. its variance, conditional on the observed counts;
3. the estimated sample coverage of the full sample, and of a rarefied
   subsample of size m.

**Excluded:**
- extrapolation (m > n);
- equal-coverage standardisation;
- richness estimators (Chao1, ACE);
- Hill numbers of order > 0;
- sample-based (incidence) rarefaction.

**What these quantities are not:**
- They do not identify true richness, establish biological turnover or
  measure collecting effort.
- Equal counts do not imply equal completeness, effort, preservation or
  detectability.
- Coverage estimates the share of the assemblage's *abundance* represented
  by the observed taxa. It is not the fraction of taxa discovered.

## Specification

| Field | Values |
| --- | --- |
| `method` | `"rarefaction"` |
| input fields | as `community` (`input`, `format`, `delimiter`, `orientation`, `value_type`, `missing`, `empty_samples`) |
| `sizes` | `"minimum_total"` or a list of distinct integers ≥ 1 |

- **`minimum_total`** resolves to the smallest retained sample total. The
  resolved list is written into the result; nothing is left implicit.
- **No silent drops.** A sample is never dropped to raise m. Only a declared
  `empty_samples: drop` removes anything, and it removes only zero-total
  samples, each recorded.
- **A curve is an explicit list of m values.** There is no plotting or
  extrapolation layer.

## Formulas

For one sample with taxon counts X₁…X_S > 0, total n, S_obs = S taxa, and
1 ≤ m ≤ n. Taxa with zero count in that sample contribute nothing and are
dropped before the calculation, but keep their labels in the result. Write
C(a, m) for the binomial coefficient, with C(a, m) = 0 when a < m.

**Absence probabilities.**
- q_i = C(n − X_i, m) / C(n, m) is the probability that taxon i is absent
  from the subsample.
- q_ij = C(n − X_i − X_j, m) / C(n, m) is the probability that taxa i and j
  are both absent.

**Expected richness** (Hurlbert 1971):

E[S_m] = Σ_i (1 − q_i).

**Conditional variance.** This is the variance of a sum of presence
indicators I_i = 1 − A_i, where A_i indicates the absence of taxon i, with
Cov(I_i, I_j) = q_ij − q_i q_j:

Var[S_m] = Σ_i q_i(1 − q_i) + 2 Σ_{i<j} (q_ij − q_i q_j).

- This is the variance of Heck, van Belle & Simberloff (1975) for random
  subsampling *of this sample*.
- It is not a variance of richness between replicate samples or populations,
  and its square root is never labelled a confidence interval.
- At m = n the expectation is S_obs and the variance is 0.

**Estimated coverage** (Chao & Jost 2012; iNEXT `Coverage`). Let f₁ and f₂
be the numbers of taxa with exactly 1 and 2 specimens.

- **For m < n** (an interpolated subsample):

  Ĉ_m = 1 − Σ_i (X_i / n) · C(n − X_i, m) / C(n − 1, m)

  This is the expected abundance share, in the full sample, of the taxa
  present in a random size-m subsample. It is exactly computable from the
  sample; the full-sample estimator is not used here.
- **For m = n** (the full sample):

  Ĉ_n = 1 − (f₁ / n) · A

  - When f₂ > 0: A = (n − 1) f₁ / ((n − 1) f₁ + 2 f₂).
  - When f₂ = 0: A = (n − 1)(f₁ − 1) / ((n − 1)(f₁ − 1) + 2).
  - When f₁ = 0: A = 1, so Ĉ_n = 1.

  This is the Good–Turing estimate with the Chao–Jost correction. It
  estimates population abundance coverage, so it is a different quantity
  from the m < n branch, and the two are labelled separately in the result.
- **Boundaries.**
  - Ĉ_n = 1 when f₁ = 0, or when f₁ = 1 and f₂ = 0. The result then records
    `coverage_boundary: true` and a note that the estimator's boundary does
    not establish complete sampling.
  - **n = 1:** expected richness is exact (1 at m = 1), and coverage is
    `null` with the reason `coverage_unavailable_single_specimen`.
- **Recorded with each sample:** f₁, f₂, n and S_obs.

**Numerics.** Ratios of binomial coefficients are computed as exponentials
of differences of log-gamma values, as vegan does. Pair terms are summed in
a fixed (sorted-label) order. A negative variance that arises only from
rounding, with |Var| ≤ 64 ε · E[S_m]², is reported as 0 and flagged. Any
larger negative value refuses.

## Refusals

- Non-integer, negative or missing counts, under the `community` input rules.
- m < 1, m > n for any retained sample (with the sample and its n
  named), duplicate m, or an empty `sizes` list.
- Empty samples under `empty_samples: error`.
- No retained sample.

## Worked values, for tests and review

- **Enumeration check.** Counts (3, 2, 1, 1), n = 7. Enumerating all
  subsamples gives:

  | m | E[S_m] | Var |
  | ---: | ---: | ---: |
  | 2 | 1.809523809524 | 0.154195011338 |
  | 3 | 2.457142857143 | 0.305306122449 |
  | 5 | 3.380952380952 | 0.331065759637 |
  | 7 | 4 | 0 |

  The formulas above reproduce all four.
- **Coed Duon** (`benchmarks/past/legacy-data/llanvirn.dat`, m = 13, the
  smallest total). E[S₁₃] by horizon 1–10:
  1.5738, 1.9048, 1.6610, 3.5971, 2.3024, 4.7409, 5.8622, 5.8772, 4.2233,
  6.0000.
  - Ĉ at m = 13 ranges from 0.7046 (horizon 10, where m = n) to 0.9588
    (horizon 1).
  - Horizon 1 (n = 321, f₁ = 1, f₂ = 2) has Ĉ₁ = 0.9090342679, which exceeds
    horizon 10's full-sample Ĉ₁₃ = 0.7046153846 (f₁ = 4, f₂ = 1). So no
    common coverage is reachable by interpolation across all ten horizons.
    That is the concrete reason equal-coverage standardisation is out of
    scope here.

## Reference checks

- **Expectation and variance:** R `vegan::rarefy(x, sample = m, se = TRUE)`.
  Agreement is required within relative 1e-10 or absolute 1e-12, whichever
  is larger, with the vegan version recorded.
- **Coverage at m < n and m = n:** the iNEXT estimator source cited in the
  critique, with its version recorded.
- **PAST "Individual rarefaction":** E(S) and SD, captured with its settings.
  Tolerance follows the captured export precision, not 1e-10.
- **Tests:**
  - the enumeration example above;
  - m = 1 and m = n;
  - one taxon;
  - all singletons;
  - f₂ = 0;
  - extreme imbalance (one taxon holding n − 1 specimens);
  - invariance to taxon order and sample order.

## References

- Hurlbert, S.H. (1971). The nonconcept of species diversity. *Ecology* 52,
  577–586.
- Heck, K.L., van Belle, G. & Simberloff, D. (1975). Explicit calculation of
  the rarefaction diversity measurement and the determination of sufficient
  sample size. *Ecology* 56, 1459–1461.
- Chao, A. & Jost, L. (2012). Coverage-based rarefaction and extrapolation.
  *Ecology* 93, 2533–2547, and Appendix D.
