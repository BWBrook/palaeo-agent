# Richness and dissimilarity

Report the taxon richness of each sample and the Bray–Curtis dissimilarities between all pairs of samples, on raw counts.

Report in `results`: `richness`, an object keyed by sample ID with the number of taxa present; and `braycurtis`, an object keyed `"A|B"` for every pair of samples, where A is listed before B in `dictionary.md`, with the dissimilarity as the value.
