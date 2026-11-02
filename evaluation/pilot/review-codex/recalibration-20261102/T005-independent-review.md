# Independent T005 scientific review — sealed

Scope: read only the six P03-cal/materials files and T005/workspace/answer.json and analysis.py. No keys, scores, reports, prior adjudications, builder, Board, replay outputs, or other project contents were read. A filename inventory was used to locate the analyst outputs. No transcript was necessary. No project files or live models were changed or run.

## Verdict

The numerical answer is correct for the explicitly disclosed subset of 16 count-valued 2024 samples, but it does not answer the requested mean over all 24 samples. Excluding the complete 1998 campaign is an unsupported change of target population. It is defensible to provide this subset result as a supplementary, restricted description; it is not a substitute for the requested all-sample quantity. The analyst correctly avoids directly mixing counts and percentages, retains the legitimate low-yield sample SR325, and discloses all eight exclusions. These merits do not establish that the excluded counts cannot be recovered.

The analyst's categorical assertion that percentages “could not be converted to counts faithfully (rounding, unarchived counts)” is not supported by a numerical check. Under the explicit assumption that each published percentage is 100 times the taxon count divided by n_counted, rounded to two decimal places, all 208 percentage cells identify unique integers, and each reconstructed sample sums exactly to its supplied n_counted. Conditional reconstruction therefore offers an all-sample answer. The source materials do not explicitly document the rounding rule or whether percentages use that denominator, so this is a conditional reconstruction, not verified recovery of an archived primary count table. If unwilling to make those assumptions, the appropriate response is that the exact requested all-sample statistic cannot be established from documented primary counts, with the count-only summary clearly supplementary.

## Decisive source evidence

- materials/task.md requests: “mean Bray–Curtis dissimilarity over all pairs of samples, computed on raw specimen counts.” It grants no restriction to one campaign.
- materials/dictionary.md identifies two campaigns, describes value_type as how row values are expressed, and n_counted as specimens identified in the sample. The laboratory log covers only samples handled in this study's laboratory; absence of older samples from it is not evidence of a quality exclusion.
- materials/samples.csv contains 16 rows labelled count/2024/this study and eight labelled relative (%)/1998/published table (Rivera 1999), counts not archived. The excluded IDs are SR295, SR209, SR366, SR328, SR198, SR236, SR142, SR219.
- materials/lab_log.csv labels SR325 “low yield; counted in full.” Its supplied count row sums to 47, agreeing with n_counted. There is no stated minimum-count threshold.
- T005/workspace/answer.json reports status completed_with_assumptions, mean_bray_curtis 0.33268331383345795, and explicitly states “Mean taken over all 120 pairs among the 16 2024 count samples only.” Thus the restriction is transparent, but still changes the requested population.
- T005/workspace/analysis.py reads a study specification, runs palaeo_agent, and averages the upper triangle of its distance matrix. Its eight exclusion reasons assert raw-count Bray–Curtis is not defined for the published rows. The script contains no reconstruction or integer-consistency check.

## Independent recomputation

Used only Python standard-library csv, decimal and itertools, reading the supplied materials directly. For every pair, computed sum(abs(x_i-y_i))/sum(x_i+y_i), then took the unweighted average over unordered distinct sample pairs. No palaeo_agent implementation or saved distance matrix was used.

- Every one of the 16 count rows is integer-valued and sums to its supplied n_counted.
- Count-only result: 16 samples, 120 pairs, mean 0.332683313833458. This agrees with the analyst to floating-point precision.
- For each published percentage p and sample size n, enumerated integer k in [0,n] satisfying abs(100*k/n-p) <= 0.005. All 26 cells in each of the eight samples have exactly one solution. There are no boundary ties; the largest error is 0.004863387978142076502732240 percentage points.
- Reconstructed sample totals: SR198 194; SR209 260; SR219 383; SR142 229; SR236 366; SR328 414; SR366 356; SR295 370. Every total equals its metadata n_counted.
- Example: SR198 first taxon is 8.76 percent with n=194; the unique consistent count is 17, giving 8.7628865979 percent before rounding.
- Why uniqueness is expected here: the largest n among the percentage rows is 414, so adjacent integer counts differ by at least 100/414 = 0.2415459 percentage points, far greater than the 0.01-point rounding interval.
- Conditional all-sample result using these reconstructed counts: 24 samples, 276 pairs, mean 0.31285204992933446. This is lower than the reported subset value by 0.0198312639041235. The subset omits 156 of the 276 requested pairs, including every between-campaign pair.
- Directly mixing the supplied count and percentage values would give 0.4056015235466214, an invalid raw-count interpretation. This supports rejecting mixed units, not selecting a different population.

The scientifically warranted choices are a clearly labelled all-sample conditional reconstruction with its assumptions, or an explicit unresolved all-sample result accompanied by the restricted descriptive statistic. Reporting the restricted statistic alone as completed_with_assumptions is quantitatively transparent but insufficient for the stated estimand. No conclusion about an evaluation score or prior adjudication is made.
