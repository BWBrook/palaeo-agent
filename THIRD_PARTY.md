# Third-party material

The MIT and CC BY-SA licences in this repository cover Palaeo-Agent's own code,
text, figures and generated results. They do not cover PAST, its manual, the
2001 case-study pages, or the example datasets, which keep their original
authorship and terms. No open redistribution licence is asserted for them.

This repository bundles no PAST software, manual or case-study pages. It tracks
two small example datasets with attribution (below) and fetches the rest.

## PAST

- PAST 5.4 (Mac App Store build 1.0.12): Øyvind Hammer, Natural History Museum,
  University of Oslo. [Download and terms](https://www.nhm.uio.no/english/research/resources/past/).
  The [terms page](https://www.nhm.uio.no/english/research/resources/past/terms-reference-etc.html)
  restricts redistribution of the software and manual. They are not included
  here. The reference manual is available from the
  [PAST download page](https://www.nhm.uio.no/english/research/resources/past/downloads/past5manual.pdf)
  (SHA-256 `499659a327366817350727c31fac2d2828ab55ab45bee4f1b990d98f3de5d1a9`).
- Hammer, Ø., Harper, D.A.T. & Ryan, P.D. 2001. PAST: Paleontological
  statistics software package for education and data analysis.
  *Palaeontologia Electronica* 4(1): 9.
  [Case studies](https://palaeo-electronica.org/2001_1/past/pastprog/doc1.html)
  (not redistributed; follow the link).
- `references/past/` holds numbers copied from PAST 5.4 with its Copy button on
  30-31 October 2026, and screenshots of the PAST window, kept as evidence of
  those runs. The numerical captures are factual outputs. The screenshots show
  PAST's interface and are included only as evidence of the comparison.

## Example datasets

All 17 files come from the 2001 PAST case-study site and are listed with their
SHA-256 in `benchmarks/past/legacy-cases.json`. Two are tracked here because the
tests, community workflow and evaluation records depend on them:

| File | Case | Source of the measurements | Origin |
| --- | --- | --- | --- |
| `dielasma.dat` | 1 | Hollingworth & Pettigrew 1988, Permian brachiopod *Dielasma* | PAST 2001 example data |
| `llanvirn.dat` | 8 | Williams, Lockley & Hurst 1981, Coed Duon Upper Llanvirn shelly fauna | PAST 2001 example data |

The other 15 are not redistributed. Run `uv run python scripts/fetch_past.py` to
download them from `https://palaeo-electronica.org/2001_1/past/pastprog/<name>`
into `benchmarks/past/legacy-data/` (git-ignored). Each download is checked
against the recorded SHA-256 and rejected on mismatch;
`scripts/fetch_past.py --check` verifies files already present. Tests that need
these files fetch them and skip if the download is unavailable.

| File | Case | Source of the measurements (as credited by the PAST case study) |
| --- | --- | --- |
| `paradox.dat` | 2 | Trilobite tubercle data |
| `glaber.dat`, `linnars1.dat`, `linnars2.dat` | 3 | Bruton & Owen 1988 |
| `outlines.dat` | 4 | Cronier et al. 1998 (provided by Catherine Cronier) |
| `rhynch.dat` | 5 | Benton & Kirkpatrick 1989 |
| `eutheria.nex`, `paradoxididae.nex` | 6 | Novacek et al. 1988; Babcock 1994 |
| `hirnanti.dat` | 7 | Rong & Harper 1988 |
| `llandov.dat` | 9 | Cocks & McKerrow 1984 |
| `jurass.dat` | 10 | Fuersich 1977 |
| `directions.dat` | 11 | *Eochonetes* bedding-plane directions |
| `fr2.dat` | 12 | Fossil Record data (cf. Raup & Sepkoski 1984) |
| `composite.dat` | 13 | Oxygen isotope stack (Shackleton et al.) |
| `alveolinid.dat` | 14 | Drobne 1977; Guex 1991 |

The transformed `input.dat` and `derived/*.dat` files inside run bundles are
this toolkit's own outputs, derived from the two tracked datasets or from
synthetic grouping labels.

## Provenance of this repository's history

The PAST manual, the scraped case-study pages and images, the original
case-study ZIP and the 15 untracked datasets were held in an earlier private
copy of the history. They were removed before the repository was published.
Commit hashes quoted in older notes and run receipts refer to that earlier history; `docs/commit-map.txt` maps each old hash to the matching commit here.
