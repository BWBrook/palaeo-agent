# Data dictionary

`counts.tsv` is tab-separated in PAST-style tabular format: the top-left cell is `.`, the first row names the taxa, and the first column contains sample IDs. Samples are rows; taxa are columns. Values are nonnegative integer specimen counts, not percentages. There are no missing values or empty samples. Use no transformation or normalisation.

`samples.csv` is comma-separated, one row per sample with `sample_id`, `facies` and `site_id`. `sample_id` identifies count-table rows and metadata records.

Count-table sample order: S1, S2, S3, S4, S5, S6, S7, S8.

Each row is one distinct site sampled once. The sites are independent sampling units, and facies labels are assumed freely exchangeable under the null. There are no blocks, covariates, repeated measurements or nested subsamples.
