# Independent blinded P04 adjudication

Scope: read only the supplied P04-cal materials and the T013/T014 workspace materials, analysis.py and answer.json. No keys, score files, trial.json, builder, reports or prior verdicts were consulted. This report is the sealed conclusion; no subsequent unblinding is part of this review.

## Scientific decision

Both trials correctly stop the requested comparison. The estimand is the arithmetic mean, over the cores in each campaign, of per-core Shannon entropy using natural logarithms and the combined >150 and 63–150 micrometre counts. All ten 2017 cores lack fine-fraction counts because their fine residue is explicitly recorded as archived, not picked. All nine 2021 cores have both fractions picked in full. Missing 2017 fine counts are unobserved, not zeros. There is no supplied basis for reconstructing their counts, relative taxon abundances or contribution to pooled per-core entropy. A 2017 >63 micrometre mean and hence the requested campaign comparison cannot be identified from these materials.

T013: scientifically warranted abstention, correct diagnostics, no material factual or numerical error found. Its supplemental >150-only campaign summaries are clearly labelled as a different comparison, and the computed 2021 combined mean is correctly confined to diagnostic issues rather than substituted for the requested comparison.

T014: scientifically warranted abstention and correct numerical diagnostic, but with an overstatement in the issues text. The sentence asserting that a campaign difference "would be an artefact of fraction coverage" is stronger than the evidence permits. A contrast using coarse-only 2017 and combined 2021 counts is confounded by coverage; the underlying complete-assemblage difference could be zero, nonzero, or of either sign. The supplied data do not establish that the entire difference is artificial. This is a bounded interpretive error, not an error in the stop decision. Prefer "would confound campaign differences with fraction coverage". Thus T014 is correct on the requested outcome but not wholly unqualified in its scientific exposition.

## Independent recomputation

Used Python standard-library CSV parsing and math.log, without the saved scripts' numpy/pandas calculation. Confirmed identical taxon order between count tables; 27 taxa, 19 coarse-fraction cores and nine fine-fraction cores; all counts nonnegative. Each fraction was picked in full where counts exist, so summing counts within core is supported.

- >150 mean Shannon, 2017 (10 cores): 2.7790308361619895.
- >150 mean Shannon, 2021 (9 cores): 2.7668293980433427.
- Combined >63 mean Shannon, 2021 (9 cores): 3.0436604058434478.
- Mean of within-2021-core coarse-minus-combined Shannon differences: -0.2768310078001051 nats, rounding to T014's -0.277.

T013's combined value of 3.0436604058434487 differs only by floating-point summation precision. Its other reported means reproduce exactly at the shown precision.

The 2017 missing-fraction IDs are exactly GB01, GB03, GB05, GB07, GB09, GB11, GB13, GB15, GB17 and GB19. Globorotalia inflata and Neogloboquadrina dutertrei are zero in every supplied count column in both fractions. Picker JM/AK does vary among cores and between fractions. Both campaigns used 63 micrometre washing sieves; the obstacle is picking coverage, not a different initial sieve mesh.

T014's qualitative observation of strong coarse/fine compositional differences is supported: independent within-core total-variation distances between the normalized fraction count vectors range from 0.600658 to 0.679509 across the nine paired cores. That supports rejecting simple equality of the fraction compositions. It does not itself prove all possible imputation methods unreliable; the stronger and sufficient reason is that no observed 2017 fine data or validated transport assumption is supplied. Its "cannot be imputed reliably" is reasonable as a statement about the supplied evidence, but should not be read as a universal impossibility claim. "Assemblage exists only for 2021" in the summary should more precisely say that the complete assemblage counts are available only for 2021; archived residue exists for 2017.

## Saved-script audit and reproducibility limits

All eight source-material files in each workspace match the canonical supplied material byte-for-byte by SHA-256 comparison.

T013 analysis.py reads both count tables and core campaigns, computes per-core natural-log Shannon and campaign means, forms combined counts only for fine-table columns, and derives the absent-core list from column absence. Its calculations reproduce the declared diagnostics by independent calculation. It does not read picking.csv: the "archived, not picked" wording, campaign counts and stopped status are hard-coded. Those statements are true for the supplied source evidence, but the script does not establish the picking-status claim itself or implement a general evidence-dependent stop decision.

T014 analysis.py additionally reads picking.csv and determines fine-fraction picked status from it, computes the missing-core list, and calculates the paired Shannon diagnostic. The picked totals by campaign are computed but unused. Its stopping decision, zero-taxon names and several interpretive sentences are hard-coded rather than programmatically tested. All concrete source claims are independently supported here, subject to the interpretive qualifications above. It is an adequate case-specific reproduction script, not a general validator.

Both scripts write stopped status, empty results, empty assumptions and empty exclusions, consistently with their saved answers and the requested schema. Neither drops a subset of cores to manufacture a 2017 combined result; empty exclusions are appropriate because the requested analysis was stopped, not performed on an altered set.

I attempted a read-only replay with answer.json writes intercepted in memory, but the default Python runtime lacks pandas. The import check stopped before either saved script executed. No dependency installation or runtime change was made. Exact script execution/reproduction therefore remains unverified by this reviewer; static logic and independent numerical reproduction support the declared outcomes. Parent-side execution evidence can resolve that remaining operational check without changing this scientific verdict.
