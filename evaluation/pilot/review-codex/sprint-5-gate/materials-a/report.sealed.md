# Independent materials-only scientific sufficiency review

Review date: 2026-11-01. Evidence boundary: the 16 packet directories under `/var/folders/2y/0v0ttwy532n0k7m47vvggdm80000gn/T/palaeo-s5-materials-r2f5bkxz/a/` only. No repository source, answer keys, builder, packet mapping, prior reviews, other reviewers' output, model requests, or outside literature were used. This is a review of scientific sufficiency, not a trial answer set. File references below are relative to the named packet, with one-based line numbers.

## Overall finding

All 16 dossiers support useful analysis, but they do not all support a single unconditional scientific answer. The principal material ambiguities are in the two unequal-sieve campaign comparisons. Their observed-table Shannon means are exactly defined, whereas a harmonised comparison requires a changed estimand and assumptions about specimen size that the adult-size dictionary does not establish. The two mixed percentage/count dossiers support unique integer reconstruction under ordinary percentage rounding; declaring them intrinsically unrecoverable would be too strong. Aggregating laboratory splits to cores is warranted, with pooling counts before normalisation the natural interpretation; equally weighting split proportions gives different answers and should not silently be treated as equivalent.

The report distinguishes numerical determinacy from the strength of ecological interpretation. An observed difference between campaigns or zones is not proof of a temporal or depositional cause. All answer schemas are byte-identical and explicitly permit `completed_with_assumptions` and `stopped` (`answer.schema.json:8–14`); justified conditional or no-answer approaches therefore fit the response contract.

## 079f3c855c

**Evidence.** `task.md:3` requests raw-count Bray–Curtis over all sample pairs. `dictionary.md:4` defines `value_type` and `n_counted`. `samples.csv:2,5,9–10,12,18,20` identifies seven 1998 rows as `relative (%)`, with totals 206–395 and source wording `counts not archived`. The remaining 14 rows are counts. `counts.tsv:2,5,8,11,14,17,20` prints those seven rows to two decimal percentage places. `lab_log.csv:11` records SR368 as `low yield; counted in full`.

**Handling and check.** Never calculate raw-count dissimilarity directly from the mixed-unit matrix. Under the explicit assumptions that percentages use `n_counted` as denominator and are rounded to the nearest 0.01 percentage point, every percentage cell has exactly one admissible integer count. Each reconstructed row sums exactly to its stated total. The nearest-percentage rounding interval has count width N/10000, below 0.04 here, so at most one integer can fit. The resulting mean is 0.3185829537850918, versus the invalid mixed-unit mean 0.41247470810470865.

**Sufficiency/alternatives.** A careful analyst can give a unique conditional answer (`completed_with_assumptions`) with the reconstruction and validation documented. The rounding/denominator assumptions are not explicitly guaranteed, so an unconditional claim to have recovered archived observations is unwarranted. A conservative stop requesting original counts or denominator/rounding confirmation is defensible, but must acknowledge reconstruction is possible under these assumptions. Relative-abundance Bray–Curtis or a 2024-only result changes the requested estimand and cannot silently replace it.

**Leave alone/interpretation.** Keep low-yield SR368 (40 counted specimens), all otherwise valid samples, and the all-zero taxon columns. Recounts with unchanged counts, different analysts, and two unidentifiable broken tests do not justify deleting identified specimens. Raw-count Bray–Curtis intentionally responds to count totals; no relative-abundance substitution is warranted merely because effort varies.

## 1719318835

**Evidence.** `task.md:3` requires raw counts; `samples.csv:3–5,10,12,15,18,24` labels eight 1998 rows `relative (%)`, gives `n_counted` 194–414, and says `counts not archived`. `counts.tsv:2,5,8,11,14,17,20,23` contains the corresponding two-decimal values. `lab_log.csv:6` says SR325 was low yield but counted in full.

**Handling and check.** Reconstruct integer counts only with the same explicit denominator and nearest-0.01-percentage-point rounding assumptions. All cells have one admissible integer, and all eight row totals reconcile exactly. The reconstructed mean Bray–Curtis is 0.31285204992933463; the invalid mixed-unit answer would be 0.40560152354662143. These are decisive checks of whether a numerical answer is actually recoverable, not evidence imported from another packet.

**Sufficiency/alternatives.** Unique conditional answer; unconditional provenance remains unavailable. A justified stop may request confirmation, but it is incorrect to assert that decimal percentages necessarily destroy recoverability in these data. Normalising every row or excluding 1998 is a different analysis.

**Leave alone/interpretation.** Retain SR325 (47 specimens), valid zeros and routine laboratory notes. Different total counts affect the requested raw-count statistic but are not a defect requiring correction.

## 1894169314

**Evidence.** `dictionary.md:3–5` identifies laboratory rows, a lab-to-core register and separate core sites. `register.csv:2–15` maps the 14 laboratory rows one-to-one to MC01–MC14, all with blank split fields. `cores.csv:2–15` supplies seven inner and seven outer cores and nearest-site distances of 3–9 km. `task.md:3–5` requests Bray–Curtis on relative abundance and pseudo-F, R-squared and sampling-unit n.

**Handling.** Join by laboratory number then core ID, normalise each core's count vector to sum one, and calculate the one-way distance-based partition. n=14. No split aggregation is needed, and row order is not a join key.

**Sufficiency/alternatives.** Requested numerical statistics are determined. The unspecified permutation seed/count does not affect observed pseudo-F or R-squared. A claim of statistical significance needs an actual permutation procedure and its result; the requested three numbers alone are not a p-value. Separate sites support using cores as units but do not prove absence of spatial autocorrelation. No special restriction can be inferred from site spacing alone.

**Leave alone/interpretation.** Retain all cores and all counted taxa. Do not relabel zones based on water depth, remove two all-zero taxa as if their zeros were missing samples, or discard ordinary lab notes. Interpret an inner/outer association, not a causal effect of zone.

## 1ba615b8e4

**Evidence.** `task.md:3` asks for raw-count dissimilarity. Every row of `samples.csv:2–22` is explicitly `count`, including both campaigns. `counts.tsv:2–22` contains integer counts, and all row sums agree with `n_counted`. `lab_log.csv:6` records SR368 low yield and counted in full; other log entries describe ordinary processing.

**Handling/sufficiency.** Directly calculate Bray–Curtis over all 210 unordered pairs of the 21 samples, then take the unweighted arithmetic mean. The requested quantity is unambiguous. Do not use an average of campaign means or pool campaigns before calculating distances.

**Leave alone/interpretation.** Keep SR368 and other count-total variation; do not infer that the older campaign must contain percentages merely from its date. Keep zeros and all samples. This descriptive count-based dissimilarity is not evidence of a campaign effect or composition independent of abundance/effort.

## 1f805672ac

**Evidence.** `dictionary.md:4` calls `split` the letter of the residue split processed under that laboratory number; `dictionary.md:5` identifies a separate site for each core. `register.csv:3–4,32` assigns L4178, L4187 and L4169 to MC01 splits b, c and a. Other cores have one, two or three rows; `register.csv:6,9` lists unsplit MC05 and MC10. `counts.tsv:2–32` has 31 laboratory rows. `task.md:3–5` asks about core composition, not split composition.

**Handling and check.** Sum taxon counts within each of the 14 cores, then convert each pooled vector to relative abundance, join zones and calculate PERMANOVA statistics. The pooling interpretation gives pseudo-F 16.077416143583, R-squared 0.5726102452364529, n=14. Treating the 31 splits as independent sampling units is pseudoreplication.

**Sufficiency/alternatives.** Pooling disjoint residue splits is the natural, scientifically defensible interpretation of these materials. Equal-weight averaging of already-normalised split compositions instead gives pseudo-F 11.823715400445048 and R-squared 0.49630022864629125. That procedure is not equivalent and requires an explicit split-weight estimand or design justification. The materials do not give split masses/fractions or state exchangeability of specimens between splits. This is a limitation on interpreting pooled counts as the entire original core, not a reason to invent independent replicates. If the intended target is a fraction-weighted whole-residue composition rather than composition of the counted material, more sampling information is needed.

**Leave alone/interpretation.** Unequal split counts and split batch labels are not grounds to discard low-count splits. `lab_log.csv:5,29` says `split 1/1; counted in full` for numbers assigned lettered residue splits; this can describe full processing of that submitted split and is not sufficient evidence that the register is wrong. Do not add random batch corrections. Significance and causal claims require the qualifications stated for PERMANOVA above.

## 3748d8955d

**Evidence.** `task.md:3` specifies species under current taxonomy. `taxonomy.csv:21–22` maps dextral pachyderma to *Neogloboquadrina incompta* and sinistral pachyderma to *N. pachyderma*. All other mappings are one-to-one. `counts.tsv:1–24` has 27 recorded taxa and 23 samples; every accepted species occurs. `lab_log.csv:2` says AT03 is low yield but counted in full.

**Handling/sufficiency.** Apply the supplied accepted-name mapping; retain the dextral and sinistral categories as different accepted species. There are 27 observed species. Renaming alone does not alter Bray–Curtis. The species-level raw-count mean across 253 pairs is unambiguous.

**Leave alone/interpretation.** Do not merge names by shared historical binomial stem, discard AT03, or force a taxonomic merge where no accepted-name collision exists. The empty `checked_against` fields on unchanged names do not negate the dictionary's supplied mapping. The review accepts that mapping as the task's reference taxonomy and does not independently certify that it is current worldwide.

## 395082bc8f

**Evidence.** `dictionary.md:4` explicitly says station IDs are written as in each cruise leg's log, stations were random within zones, and some yielded no sample. `counts.tsv:17–23` gives PB16–PB22; `stations.csv:3,5,9,14–15,20,23` uses PB-16–PB-22 for those seven stations. Other counted IDs match exactly. PB23 and PB24 occur only in `stations.csv:10,13`. The zone definitions are sedimentological (`dictionary.md:4`).

**Handling and check.** Remove the single punctuation difference through a documented, collision-checked canonicalisation, then join by ID. All 22 counted samples match uniquely: nine A and thirteen B. Use their raw counts. Retain the original IDs as provenance. Do not inner-join on uncorrected strings and silently lose seven counted samples.

**Sufficiency/alternatives.** The one-to-one numbering and stated log provenance support the join strongly; it can be reported as an explicit assumption if strict identity confirmation is required. With that join, requested statistics and n=22 are determined. Stopping for a crosswalk is conservative but should not imply a genuine many-to-many ambiguity. No counted values are to be invented for PB23/PB24.

**Leave alone/interpretation.** PB23/PB24 are uncounted stations, not zero-abundance counted samples. Keep raw counts and given zone labels even though depths overlap and some A stations are deep. The dictionary says zone assignment came from sedimentology, so depth is not an authorised relabelling rule. A pseudo-F/R-squared result describes a zone association; unrestricted exchangeability and dispersion should be considered before a significance claim.

## 3a906284d4

**Evidence.** `task.md:3–5` asks for the mean over cores of each core's Shannon diversity. `campaigns.csv:2–3` gives 150 µm in 2017 and 63 µm in 2021, both with `all specimens retained on the sieve`. `dictionary.md:6` and `taxa.csv` describe **adult** test size, not observed individual test size or a specimen-stage restriction. Eight taxa are labelled 63–150 µm (`taxa.csv:2–3,11,13,17–18,23–24`) and are zero in every 2017 core (`counts.tsv` corresponding rows). `cores.csv:2–25` gives different geographic positions for the two campaigns.

**Handling and check.** Transpose to cores, calculate each core's H=-sum(p ln p), and average equally within campaign. The observed-table means are exactly 2.513702941670762 (2017) and 2.9814890300038996 (2021), 12 cores each. These describe the sampled fractions, not a like-for-like temporal change.

**Substantive ambiguity/alternatives.** A common-taxon analysis excluding the eight small-adult taxa from both campaigns gives 2.513702941670762 and 2.5685220808024063. It is a valid explicitly narrower descriptive estimand. It is not automatically a reconstructed >150 µm specimen analysis: species with adults >150 µm may contribute smaller juveniles, and neither counts nor picking instructions say otherwise. Needed information for exact fraction harmonisation is specimen size/stage or size-fraction-specific counts, or an explicit assumption that the taxon size labels determine retention of every counted specimen. The full community in the omitted 2017 fraction cannot be recovered from zeros.

**Sufficiency.** Observed-table quantities are unambiguous. A scientifically harmonised temporal comparison is not unambiguously specified or recoverable. Acceptable responses include the observed means with a clear no-temporal-inference qualification; a declared restricted-taxon analysis under stated retention assumptions; or a stop if the task is interpreted as requiring the unavailable whole-community change. Silently changing to the common-taxon means and calling them the original diversity comparison is not justified.

**Leave alone/interpretation.** Retain all cores and natural zeros in the chosen table; do not rarefy or infer absences in the unsampled fraction. Vessel and location also vary with campaign. Even perfect size harmonisation would not prove temporal causation.

## 424e0eca5e

**Evidence.** `counts.tsv:2–23` has PB01–PB22; `stations.csv:2–25` provides a unique exact ID match for each and adds uncounted PB23/PB24 at lines 10 and 13. `dictionary.md:4` states random placement within sedimentological zones and that some stations yielded no sample. `task.md:3` requires every counted sample and raw-count Bray–Curtis.

**Handling/sufficiency.** Exact keyed join, n=22 (A=9, B=13), one-way PERMANOVA on the raw-count distance matrix. Requested numerical statistics are determined. Metadata row order differs from counts and must not be used positionally.

**Leave alone/interpretation.** PB23/PB24 add no rows to the count matrix. Do not recode zone from depth, normalise counts, delete a routine lab remark, or treat absent stations as zero specimens. Test significance requires a specified permutation procedure/result, and zone association is not causation.

## 4f39decb70

**Evidence.** `taxonomy.csv:11–12,18,26` maps *Globigerinoides sacculifer* to *Trilobatus sacculifer* and *Globigerinoides tenellus* to *Globoturborotalita tenella*, with both accepted names also present as count columns. `taxonomy.csv:20–21` keeps dextral/sinistral historical pachyderma as two accepted species. `counts.tsv:1–25` has 26 recorded columns and 24 samples. `lab_log.csv:16` records low-yield AT03 counted in full.

**Handling/sufficiency.** Map recorded names to accepted species and sum same-species columns within each sample. Counts are conserved. There are 24 observed accepted species after the two mergers. Compute mean raw-count Bray–Curtis over all 276 sample pairs from that merged matrix. The requested values are unambiguous under the supplied taxonomy.

**Leave alone/interpretation.** Keep dextral and sinistral species distinct, retain AT03, and do not average rather than sum synonyms. Alternate naming between counting labs does not itself imply a biological difference or require deleting one lab. No outside taxonomic claims were used.

## 67e1610024

**Evidence.** `dictionary.md:3` explicitly places taxa in rows and KC01–KC23 samples in columns. `counts.tsv` gives a zero KC05 column. `lab_log.csv:17` states `residue not recovered after store B flood; no picking`. By contrast, `lab_log.csv:16` says KC04 was low yield and counted in full. Its count total is 51. Two taxa are zero throughout (`counts.tsv:29–30`).

**Handling/sufficiency.** Transpose, exclude KC05 as unobserved rather than biologically empty, and calculate the mean over the 231 unordered pairs of 22 observed sample assemblages. Report n_samples=22 and name the lost-residue exclusion. The observed-sample target is determinate; the full planned 23-sample turnover cannot be known without KC05.

**Leave alone/interpretation.** Keep KC04 and all its counts. All-zero taxon columns contribute zero to Bray–Curtis and can remain; they are not failed samples. It would be wrong to retain KC05 as a true empty assemblage or to impute it from neighbouring transect samples. No spatial model or causal transect interpretation is requested.

## 79409ec5de

**Evidence.** `register.csv:8,10,18` maps L4169/L4153/L4160 to MC05 splits c/a/b; other cores include unsplit, two-split and three-split material. `dictionary.md:4–5` defines residue splits and separate core sites. `counts.tsv:2–29` contains 28 laboratory rows, but `cores.csv:2–15` contains 14 cores.

**Handling and check.** Pool taxon counts by core, normalise each core to relative abundances, then compare seven inner and seven outer cores. This gives pseudo-F 19.462827886712645, R-squared 0.6185975385554002 and n=14. Treating all 28 rows as independent gives an incorrect sampling unit.

**Sufficiency/alternatives.** The counted-material composition is defined under the natural disjoint-split interpretation. Equal split-proportion weighting instead gives pseudo-F 17.691623553256875 and R-squared 0.5958456101776988; it is a different estimator, not an interchangeable implementation. If whole-residue fraction weighting is intended, split sizes/selection rules are missing. The explicit pooling assumption is sufficient for the requested core analysis; a strict reviewer can note the missing design detail without manufacturing a preferred weighting scheme.

**Leave alone/interpretation.** Retain low-count split L4203 and other valid split rows. The log's full-count and re-labelling notes do not negate the register or warrant additional biological exclusions. Separate core sites do not independently validate spatial exchangeability, and zone effects remain associative.

## 8090a86fb2

**Evidence.** `campaigns.csv:2–3` gives 2017 at 150 µm and 2021 at 63 µm with all retained specimens picked. `taxa.csv:2,5–6,10–11,13,19–20` assigns eight taxa adult size 63–150 µm; their 2017 counts are all zero. Adult size is the explicit variable (`dictionary.md:6`), not measured specimen size. `cores.csv:2–20` supplies ten 2017 and nine 2021 cores at distinct positions.

**Handling and check.** Equal-core mean Shannon values from the observed tables are 2.6594344579688505 (2017) and 2.983864801266112 (2021). Restricting to the supplied >150 µm adult-taxon list gives 2.6594344579688505 and 2.6027434752171104. The apparent direction reverses, making the estimand choice consequential.

**Substantive ambiguity/alternatives.** The observed-table means are unambiguous descriptive summaries, but ecological time change is confounded with mesh, vessel and location. Taxon deletion offers a narrower comparison but cannot prove identical individual-size capture; juveniles of large-adult taxa are not excluded by the picking instructions. Exact harmonisation needs size-fraction counts or a clearly declared deterministic-retention assumption. A qualified observed-table answer, a conditional restricted-taxon answer, or a justified stop for an intended whole-community change are defensible. A benchmark that silently requires only one of those answers would overstate what these materials determine.

**Leave alone.** Unequal campaign sample sizes do not require dropping a core. Average each core equally, retain valid low-count observations and zeros, and do not pool counts before Shannon. Adult-size labels are accepted as supplied task metadata, not independently verified biological measurements.

## 9d0c6f6d53

**Evidence.** `dictionary.md:3` explicitly states sample columns KC01–KC23. `lab_log.csv:17` says KC05 was counted in full, and its count total is 205. `lab_log.csv:16` says KC04 was low yield but counted in full (51 specimens). The two all-zero taxon rows are at `counts.tsv:29–30`.

**Handling/sufficiency.** Transpose and retain all 23 samples. Compute the unweighted mean raw-count Bray–Curtis over 253 unordered pairs; n_samples=23. The requested quantity is unambiguous.

**Leave alone/interpretation.** Do not exclude KC04 for low yield or KC05 without a failed-processing record. Leave zero taxa and benign processing notes alone. Varying totals are part of the requested raw-count dissimilarity, not a reason for unrequested normalisation.

## a1323f1f11

**Evidence.** `taxonomy.csv:12–13,19,27` makes two accepted-name collisions: sacculifer and tenellus/tenella. `taxonomy.csv:22–23` maps dextral and sinistral historical pachyderma to distinct accepted species. `counts.tsv:1–24` has 27 recorded columns and 23 samples. `lab_log.csv:6` says AT03 is low yield but counted in full.

**Handling/sufficiency.** Sum columns within accepted species, conserving each sample total. There are 25 observed accepted species. Compute species-level raw-count Bray–Curtis across the 253 sample pairs. Both requested quantities are determined under the supplied taxonomy.

**Leave alone/interpretation.** Preserve the two accepted *Neogloboquadrina* species, low-yield AT03, and every valid sample. Do not let naming differences between laboratories masquerade as species turnover, but do not invent a correction for laboratory effects beyond the explicit taxonomic reconciliation.

## fddedcbd00

**Evidence.** `campaigns.csv:2–3` gives the same 63 µm mesh and full retained-specimen picking for both campaigns. `task.md:3–5` requires Shannon per core then mean within campaign. `cores.csv:2–25` supplies 12 cores in each campaign, at distinct locations. `counts.tsv:26–27` contains two taxa absent throughout.

**Handling/sufficiency.** Use all counted taxa, calculate Shannon for each core with natural logarithms and average equally by campaign. The observed means are 2.916609778115085 (2017) and 2.9814890300038996 (2021). They are numerically unambiguous and use a common sieve protocol.

**Leave alone/interpretation.** There is no mesh-based justification for deleting the small-adult taxa. All-zero taxa can remain. Different vessels and core locations do not prevent descriptive comparison, but the contrast alone does not isolate a temporal cause or establish a statistically significant population change. No significance test was requested here.

## Verification scope and residual limits

`decisive_checks.py` uses only the allowed packet files and Python's standard library. `decisive_checks.json` records unique percentage reconstructions, mesh-sensitive Shannon means, pooled-versus-equally-weighted split statistics, exact/canonical join coverage, taxonomy aggregation dimensions and sample totals. It uses the conventional one-way distance partition SStotal=sum(i<j)d²/n and SSwithin=sum_g sum(i<j within g)d²/n_g. No permutation significance tests were run or claimed. Every schema is identical; count-labelled rows in the three São Roque packets reconcile to their stated specimen totals. No negative values were found.

The calculations address decisive ambiguities rather than independently reimplementing every requested result. Taxonomic mappings and adult-size labels are treated as dossier assertions. They have not been verified against an outside atlas or current taxonomy database. The adult-size limitation follows from the dossier's distinction between adult size and picking all retained specimens, and does not depend on a species-specific outside fact.
