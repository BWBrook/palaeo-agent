# Independent R references

Reference calculations from independently authored R implementations, used to
check Palaeo-Agent's numerical outputs. R is a validation-time dependency
only. The toolkit runtime and CI need no R: `tests/test_vegan_reference.py`
compares against the committed JSON.

## Community workflow: vegan

[`community_vegan.R`](community_vegan.R) parses the frozen Llanvirn file with
its own reader (`read.table`, character labels, `check.names = FALSE`). It
writes [`community-vegan.json`](community-vegan.json), which records:

- input SHA-256, R and package versions, LAPACK version and the exact vegan
  call for each case;
- total, richness, Shannon and Simpson per sample (`specnumber`, `diversity`);
- raw Bray-Curtis, relative-abundance Bray-Curtis (`decostand(x, "total")`)
  and binary Jaccard (`binary = TRUE`; vegan's default Jaccard is
  quantitative);
- the non-null `wcmdscale` eigenvalue spectrum, the Gram matrix over all
  positive axes, and the Gram matrix over the first two axes when the relative
  eigengap exceeds 1e-8;
- analytical controls: identical rows (distance 0), disjoint supports
  (Bray-Curtis = Jaccard = 1), and proportional rows (relative Bray-Curtis 0;
  raw Bray-Curtis |Nx − Ny| / (Nx + Ny), the total-imbalance bound attained).

`wcmdscale` drops the structural null eigenvalue that double centring always
produces, so its spectrum has n − 1 values where ours has n. The test compares
the non-null spectra.

Result at commit time, against the package at c5df648: every compared
quantity agrees within 2.5e-15 absolute. That is diversity, distances and
eigenvalues for all three cases, plus the Gram matrices over all positive axes
and over the two selected axes. The declared tolerance is `1e-10`, scaled by
the largest eigenvalue for spectral quantities.

## Constrained zonation: rioja

[`coniss/make_cases.py`](coniss/make_cases.py) writes three public count
tables and the toolkit's coordinates for four cases to
[`coniss/cases.json`](coniss/cases.json): a 30 × 8 two-block table under
both transforms (seed chosen so each has a cost inversion and a later
broken-stick exceedance), a 40 × 12 Dirichlet-like table under `hellinger`,
and the three-row exact-tie fixture. It asserts that no case carries a
small-margin flag except the declared tie.
[`coniss_reference.R`](coniss_reference.R) reads only those coordinates and
calls rioja 1.0-7: `chclust(dist(X)^2, "coniss")`, the wrapper's own
`.Call("chclust_c", ...)` for unsorted per-boundary dispersion, `cutree` for
every k and `bstick(tree, ng = n - 1)`. Rank m, which rioja's
`diff(rev(height))` omits, is recorded from `bstick(m, H_m)[m]` and the
smallest height. [`coniss-reference.json`](coniss-reference.json) holds the
results; `tests/test_coniss.py` compares them (rtol 1e-10, partitions and
verdicts exactly) and pins the generator and cases hashes.

rioja uses a double-precision Lance–Williams recurrence, so it is a
reference for ordinary cases only. Exact ties beyond the declared fixture,
nearly constant data and underflow are checked against the exact oracle in
the test module instead.

## What this does and does not establish

vegan is an independently authored community-ecology implementation, and its
author is not us. Agreement therefore guards against errors in our own
transcription of the definitions, our parsing and our orientation handling.
It does not guard against a definition both implementations share. Shannon
with natural logs and Simpson as 1 − Σp² are definitional choices, recorded in
the JSON, not facts that vegan confirms. Both implementations also rely on
LAPACK symmetric eigensolvers.

This is cross-implementation agreement on one development dataset. It is not
method validation, a PAST comparison or held-out evidence.

## Regenerate

```sh
cd references/r
Rscript -e 'renv::restore()'
Rscript community_vegan.R
uv run python coniss/make_cases.py
Rscript coniss_reference.R
```

renv pins vegan 2.7-6, permute, smatr, rioja 1.0-7 and jsonlite on R 4.6.1. Regenerate references
only when a definition or the input changes, and commit the JSON with the
script.

Build note for `macbook`: Homebrew R 4.6.1_1's `FLIBS` names a GCC directory,
`aarch64-apple-darwin27`, that does not exist, so compiling vegan's Fortran
failed. Since 31 October 2026, `~/.R/Makevars` on `macbook` derives the
correct directory from `gfortran` (see nectar's
`docs/exchange/logs/2026-10-31-macbook-r-fortran-flibs.md`). `renv::restore()`
needs nothing extra there. `mini` builds vegan with its existing settings.
