# Study report

Factual record generated from the saved study. Every number links to the field it came from;
scientific interpretation and sampling validity are not established by this report.


## Dataset `d`

16 samples × 26 columns (`derived/d.json`).
- select: removed SR198, SR209, SR219, SR142, SR236, SR328, SR366, SR295 — 1998 rows are published relative abundances (%), not raw counts

## Analysis `bc` (community, dataset `d`)

- n = 16 (`runs/bc/baf32bf0b2df4833bb60aa64eb043d4e/results.json#n`)
- n_input = 16 (`runs/bc/baf32bf0b2df4833bb60aa64eb043d4e/results.json#n_input`)
- n_taxa = 26 (`runs/bc/baf32bf0b2df4833bb60aa64eb043d4e/results.json#n_taxa`)
- transform = "none" (`runs/bc/baf32bf0b2df4833bb60aa64eb043d4e/results.json#transform`)
- distance = "braycurtis" (`runs/bc/baf32bf0b2df4833bb60aa64eb043d4e/results.json#distance`)
- negative_inertia_magnitude = 0.002593513473214738 (`runs/bc/baf32bf0b2df4833bb60aa64eb043d4e/results.json#negative_inertia_magnitude`)
- warning `negative_eigenvalues`: Dissimilarities have material negative PCoA eigenvalues; no correction applied
- limitations: Descriptive community analysis only; no group inference; Count declaration and sampling meaning require scientific judgment; Diversity is observed and unstandardised; unequal totals can confound comparisons through sampling effort; PCoA coordinates retain positive axes only; negative eigenvalues are reported, not corrected; Axis proportions refer to positive inertia, not total variance; Eigenaxis signs and orientations within tied eigenspaces are arbitrary
