# Data dictionary

`counts.tsv` is tab-separated in PAST-style tabular format: the top-left cell is `.`, the first row names the taxa, and the first column contains sample IDs. Samples are rows; taxa are columns. Values are nonnegative integer specimen counts, not percentages. There are no missing values or empty samples. Use no transformation or normalisation.

`samples.csv` is comma-separated, one row per sample with `sample_id`, `facies` and `site_id`. `sample_id` identifies count-table rows and metadata records.

Count-table sample order: S1, S2, S3, S4, S5, S6, S7, S8.

Four subsamples were taken within each of two sites. Rows S1-S4 are subsamples of site_reef_01, and rows S5-S8 are subsamples of site_lagoon_01. Facies is a site-level attribute. Subsamples within a site share the same exposure and are not independent replicates of the facies comparison. There is one site per facies.
