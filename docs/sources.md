# Source observations

Checked 30 October 2026. This is an initial source map, not an exhaustive
dataset inventory. URLs and observed versions may change.

| Source | Observation | Consequence |
| --- | --- | --- |
| [Official PAST page](https://www.nhm.uio.no/english/research/resources/past/) | Lists current Windows version 5.4 (October 2026), Mac download labelled 5.2, manual and help links. | Record actual application version for comparisons. |
| [PAST manual](https://www.nhm.uio.no/english/research/resources/past/downloads/past5manual.pdf) | Cover identifies version 5.4; 321 PDF pages. | Primary method documentation; not a numerical reference-run archive. |
| [Version history](https://www.nhm.uio.no/english/research/resources/past/version-history.html) | Records changes to methods and numerical bug fixes as well as UI changes. | Version-specific comparisons are necessary. |
| [Official terms](https://www.nhm.uio.no/english/research/resources/past/terms-reference-etc.html) | States PAST is Copyright Hammer 2024 and redistribution requires permission. | Do not bundle PAST; dataset rights need separate evidence. |
| [Original 2001 software page](https://palaeo-electronica.org/2001_1/past/pastprog/index.html) | Lists the original toolbox and links documentation/case studies. | Historical scope, distinct from current PAST. |
| [Original case-study index](https://palaeo-electronica.org/2001_1/past/pastprog/doc1.html) | Links fourteen numbered case studies. | Legacy source, not a count of current examples. |
| [Current help index](https://www.nhm.uio.no/english/research/resources/past/help/index.html) and [PCA help](https://www.nhm.uio.no/english/research/resources/past/help/pca.html) | PCA help illustrates gorilla-skull landmarks but supplies no matrix download on that page. No separate example-data collection was identified on the inspected current landing/help pages. | Current examples need a source-by-source inventory; documentation figures alone cannot supply benchmark inputs. |
| [Legacy Dielasma case](https://palaeo-electronica.org/2001_1/past/pastprog/study1.html), [data](https://palaeo-electronica.org/2001_1/past/pastprog/dielasma.dat) and [suggested answers](https://palaeo-electronica.org/2001_1/past/pastprog/study1tips.html) | Data content is accessible as text, with labels and `.` missing values; procedures and rounded answers are public. | A candidate legacy fixture, not a PAST 5 reference execution. Historical inferential interpretations are not automatically endorsed. |
| [SciPy statistics](https://docs.scipy.org/doc/scipy/reference/stats.html) | Extensive probability distributions, statistics and tests. | Candidate numerical dependency, not proof of method equivalence. |
| [scikit-bio diversity](https://scikit.bio/docs/latest/diversity.html) | Alpha/beta diversity and labelled community-table workflows. | Candidate foundation for initial community analyses. |
| [scikit-bio ordination](https://scikit.bio/docs/latest/generated/skbio.stats.ordination.html) | Documents PCoA, CA, CCA and RDA. | Assess selected methods and scaling against chosen references. |
| [scikit-bio PERMANOVA](https://scikit.bio/docs/latest/generated/skbio.stats.distance.permanova.html) | Interface accepts a grouping factor, permutations and seed. | Do not infer support for all experimental designs or PAST options. |
| [MCP tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) | Documents tool discovery and structured inputs/outputs. | Possible later transport, independent of scientific core. |

## Open evidence work

Initial legacy reconnaissance is recorded in
[the machine-readable case inventory](../benchmarks/past/legacy-cases.json):
fourteen indexed cases, twelve readable case pages and fifteen distinct linked
filenames. Cases 4 and 11 returned verification challenges during this check.
Only `dielasma.dat` was viewed as data content; the other entries record links,
not verified payloads. No files were acquired. These are source observations,
not a completed corpus or numerical test suite.

- Enumerate current official worked examples and their actual downloadable data.
- Establish whether examples are separate downloads, embedded in documentation,
  shipped with the application, or linked to original publications.
- Determine which current examples reproduce legacy cases.
- Record data-specific attribution and redistribution terms.
- Determine where expected numerical outputs and complete settings are available.
- Freeze the bounded source inventory before reporting coverage percentages.

No binaries or datasets have been downloaded into this repository. No reference
application has been installed or executed for these observations.
