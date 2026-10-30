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
```

renv pins vegan 2.7-6, permute and jsonlite on R 4.6.1. Regenerate references
only when a definition or the input changes, and commit the JSON with the
script.

Build note for `macbook`: Homebrew R 4.6.1_1's `FLIBS` names a GCC directory,
`aarch64-apple-darwin27`, that does not exist, so compiling vegan's Fortran
failed. Since 31 October 2026, `~/.R/Makevars` on `macbook` derives the
correct directory from `gfortran` (see nectar's
`docs/exchange/logs/2026-10-31-macbook-r-fortran-flibs.md`). `renv::restore()`
needs nothing extra there. `mini` builds vegan with its existing settings.
