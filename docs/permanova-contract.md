# Sprint-2 PERMANOVA contract

Frozen before comparator output inspection, 31 October 2026. Implementation
and independent reference generation follow this contract. Claude's blind
fixture directory remains unopened until the implementation commit.

One categorical grouping factor, explicitly declared independent sampling
units, freely exchangeable labels, at least two groups and two samples per
group. Exact sample-ID metadata alignment, count semantics, orientation,
transform and distance are declared. No blocks, covariates, repeated measures,
restricted permutations, automatic distance correction or dispersion test.
An independence declaration records an assumption; it does not verify design.

For squared distances q, SSt=sum(i<j)q/n, SSw=sum(groups)sum(i<j in group)q/n_g,
SSb=SSt-SSw. dfb=G-1, dfw=n-G, F=(SSb/dfb)/(SSw/dfw), R2=SSb/SSt.
Exactly zero total variation refuses; there is no unit-scale floor. Observed residual variation
at or below 64*float64_epsilon*SSt refuses as an unsupported finite-F case.
Zero F with positive residual variation is valid. Signed SSb, F and R2 are
retained for semimetric distances; they are not clamped to zero.

Permuted zero-residual statistics with positive between-group variation are
treated as positive infinity in the reference distribution, counted as
exceedances and reported as such using JSON null plus an explicit status.
No allocation is silently dropped or redrawn. Other undefined permuted
statistics refuse the whole calculation with a structured diagnostic. Ties
count as exceedances when Fperm >= Fobserved - sqrt(float64_epsilon),
matching vegan's absolute pseudo-F tie tolerance. This refinement was fixed
after source review and before any comparator output was generated.

Let M be the number of distinct labelled group allocations preserving sizes.
If M-1 <= requested B and M <= 10,000, enumerate every allocation, observed
exactly once: p=b/M. Otherwise draw B independent uniform index permutations
with replacement using NumPy Generator(PCG64(seed)); this can include the
observed allocation and duplicates. Use p=(b+1)/(B+1). Save actual index
schedules, permuted statistics/statuses, counts, denominator, mode, requested
and actual draws, seed, bit generator and NumPy version. Stored index schedules
permute distance-matrix rows and columns together while keeping group labels
fixed. For exact vegan checks, supply the M-1 non-observed representatives;
vegan supplies the observed allocation through its plus-one rule. Default B=999,
1<=B<=9999; seed is explicitly required. Resource-limit refusals precede
allocation and do not change the reference distribution.

Dispersion is descriptive: centroid, bias.adjust=FALSE, sqrt.dist=FALSE,
add=FALSE. Use the full double-centred eigensystem, retaining axes with
abs(lambda)>max(sqrt(epsilon),sqrt(epsilon)*lambda_max), matching vegan's
betadisper convention. For each sample subtract its group centroid in each
retained coordinate; signed squared distance is sum(positive residuals^2)
minus sum(negative residuals^2). Report sqrt(max(signed,0)), the signed values,
all zero truncations, group summaries and eigenspectrum/threshold, including
discarded modes. Tiny genuine modes can fall below this diagnostic threshold;
zero diagnostic distances do not establish absence of variation. No selected
ordination cutoff is involved and no dispersion p-value is returned.

API: method `permanova`; required metadata path and `group_column`; design
`independent`; `permutation_scheme=free`; `format=past`, count value type,
orientation, distance, transform, missing=error and empty_samples=error.
Result: typed method-specific record with data/metadata alignment, SS/df/F/R2,
p-value, permutation and dispersion records, warnings and limitations. Explicit
independence and free-permutation declarations also declare exchangeability
under the null; neither is inferred from the data. This is a distance-based
group-association test, not a pure centroid-location test. Run,
inspect and reproduce enforce the record and source/environment provenance.
Existing sensitivity comparisons remain community-only.

Python/vegan checks use identical explicit schedules for Monte Carlo and all
allocations for exact inference. Numerical tests are fixed at rtol=atol=1e-10
for these controlled references; actual discrepancies are reported. Native
PAST deterministic outputs use export precision. Stochastic PAST p-values
are a separately labelled check unless draws match. Main references:
[adonis2](https://vegandevs.github.io/vegan/reference/adonis.html),
[betadisper](https://vegandevs.github.io/vegan/reference/betadisper.html).
