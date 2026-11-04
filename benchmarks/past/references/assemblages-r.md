# Independent R assemblage reference

`assemblages-r.json` is a library/source-function reference, **not a PAST
execution or held-out validation**. Its generator never imports Palaeo-Agent.
R reads the frozen Llanvirn input independently. The receipt records input and
generator SHA-256, R/package versions, calls, source hashes, RNG and settings.

- Expectation and conditional variance: installed `vegan::rarefy`, vegan
  2.7.6 in the existing `references/r/renv` library. Values include each
  Llanvirn sample at 1, 13 and its full total, plus small boundary fixtures.
- Coverage: the unmodified `Chat.Ind` function parsed and evaluated from the
  [iNEXT upstream source at revision 27ac034](https://github.com/JohnsonHsieh/iNEXT/blob/27ac0343bd4f6133fe585c49a583e7de694cfb58/R/iNEXT.r),
  whose DESCRIPTION identifies version 3.0.2. This is source-function parity,
  not an installed iNEXT package run. Neither upstream source nor package
  dependencies are committed here. The generator checks the source and
  DESCRIPTION hashes before execution. For one specimen the contract returns
  unavailable/null, whereas upstream returns 1; both are labelled explicitly.
- Count homogeneity: base-R `chisq.test`, `fisher.test`, `p.adjust` and
  `binom.test`, with nine declared adjacent pairs and a single 118-test taxon
  Holm family. No observed Fisher result includes an extra table because of
  R's wider probability-tie tolerance. Zero-count limits cover all ten samples.
- Monte Carlo: 9,999 tables, sequential R Mersenne-Twister stream seeded at
  7,112,026; Python uses its own independent seed/streams. Compatibility uses
  the prespecified six-standard-error difference bound plus a two-count
  allowance recorded in the receipt. Decimal equality is not expected.
- The tiny table `(2,1,0)` versus `(0,1,2)` has seven feasible allocations.
  Their weights are six times 0.1 and once 0.4, with exact inclusive Pearson
  tail 0.6. Tests check the Python sampler against this weighted tail using a
  prespecified six-binomial-standard-error tolerance.

At exact zero-variance boundaries, vegan sometimes returns a residual
variance below 1e-12 (SD up to about 2.7e-7 in these fixtures). The receipt
retains these raw results. Tests apply the contract's variance tolerance and
require exactly zero variance/SD from Palaeo-Agent at deterministic boundaries;
they do not use a tight SD comparison to magnify harmless variance rounding.
Away from these boundaries, SD is also compared directly.

Regeneration requires R with the existing project vegan library and jsonlite.
Download the pinned `R/iNEXT.r` and `DESCRIPTION` to an external temporary
directory, named `iNEXT.r` and `DESCRIPTION`, then run:

```sh
Rscript --vanilla scripts/reference_assemblages.R /path/to/pinned-iNEXT-source-directory
.venv/bin/python -m pytest tests/test_assemblage_references.py -q
```

The committed receipt is under 100 KB and lets ordinary Python CI validate
these values without R, network access or an installed iNEXT package.
