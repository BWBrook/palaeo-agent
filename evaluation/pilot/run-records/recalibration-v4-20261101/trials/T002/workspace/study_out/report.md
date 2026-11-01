# Study report

Factual record generated from the saved study. Every number links to the field it came from;
scientific interpretation and sampling validity are not established by this report.


## Dataset `genus`

23 samples × 17 columns (`derived/genus.json`).
- map_taxa: Globigerinoides ← Globigerinoides ruber + Globigerinoides conglobatus; Neogloboquadrina ← Neogloboquadrina incompta + Neogloboquadrina dutertrei + Globigerina pachyderma; Globoturborotalita ← Globoturborotalita tenella + Globoturborotalita rubescens; Globigerinella ← Globigerinella calida + Globigerinella siphonifera; Globigerinita ← Globigerinita uvula + Globigerinita glutinata; Globorotalia ← Globorotalia truncatulinoides + Globorotalia menardii — Aggregate recorded names to genus of current_name (taxonomy.csv)

## Analysis `bc` (community, dataset `genus`)

- n = 23 (`runs/bc/8763b16cf2ab454da90fbba33471acff/results.json#n`)
- n_input = 23 (`runs/bc/8763b16cf2ab454da90fbba33471acff/results.json#n_input`)
- n_taxa = 17 (`runs/bc/8763b16cf2ab454da90fbba33471acff/results.json#n_taxa`)
- transform = "none" (`runs/bc/8763b16cf2ab454da90fbba33471acff/results.json#transform`)
- distance = "braycurtis" (`runs/bc/8763b16cf2ab454da90fbba33471acff/results.json#distance`)
- negative_inertia_magnitude = 0.0321544136255098 (`runs/bc/8763b16cf2ab454da90fbba33471acff/results.json#negative_inertia_magnitude`)
- warning `negative_eigenvalues`: Dissimilarities have material negative PCoA eigenvalues; no correction applied
- limitations: Descriptive community analysis only; no group inference; Count declaration and sampling meaning require scientific judgment; Diversity is observed and unstandardised; unequal totals can confound comparisons through sampling effort; PCoA coordinates retain positive axes only; negative eigenvalues are reported, not corrected; Axis proportions refer to positive inertia, not total variance; Eigenaxis signs and orientations within tied eigenspaces are arbitrary
