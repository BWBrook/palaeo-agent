# Study report

Factual record generated from the saved study. Every number links to the field it came from;
scientific interpretation and sampling validity are not established by this report.


## Dataset `holocene`

26 samples × 29 columns (`derived/holocene.json`).
- select: removed S27, S28, S29, S30 — Holocene: age < 11700 cal BP from linear interpolation over accepted dates

## Analysis `bc` (community, dataset `holocene`)

- n = 26 (`runs/bc/2f6a9de08fbc4087abe8198043206231/results.json#n`)
- n_input = 26 (`runs/bc/2f6a9de08fbc4087abe8198043206231/results.json#n_input`)
- n_taxa = 29 (`runs/bc/2f6a9de08fbc4087abe8198043206231/results.json#n_taxa`)
- transform = "relative_abundance" (`runs/bc/2f6a9de08fbc4087abe8198043206231/results.json#transform`)
- distance = "braycurtis" (`runs/bc/2f6a9de08fbc4087abe8198043206231/results.json#distance`)
- negative_inertia_magnitude = 0.04276530867438656 (`runs/bc/2f6a9de08fbc4087abe8198043206231/results.json#negative_inertia_magnitude`)
- warning `negative_eigenvalues`: Dissimilarities have material negative PCoA eigenvalues; no correction applied
- limitations: Descriptive community analysis only; no group inference; Count declaration and sampling meaning require scientific judgment; Diversity is observed and unstandardised; unequal totals can confound comparisons through sampling effort; PCoA coordinates retain positive axes only; negative eigenvalues are reported, not corrected; Axis proportions refer to positive inertia, not total variance; Eigenaxis signs and orientations within tied eigenspaces are arbitrary
