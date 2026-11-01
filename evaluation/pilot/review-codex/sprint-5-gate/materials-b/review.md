# Independent materials-only scientific sufficiency review

Reviewed 2026-11-01. Evidence root: `/var/folders/2y/0v0ttwy532n0k7m47vvggdm80000gn/T/palaeo-s5-materials-r2f5bkxz/b/`.

Scope: 16 anonymised dossiers, using their own task, dictionary, data, and answer schema only. No repository source, mapping, key, prior review, other reviewer's output, external literature, or live model request was consulted. Source references below are relative to the named packet directory. Numerical checks use Python's standard library, independently applying the stated definitions; `decisive_checks.json` retains the computed checks and paired-valve alternatives. This is a sufficiency review, not a full answer-key reconstruction or a trial.

## Overall finding

Fourteen dossiers determine the requested numerical summaries under ordinary implementations of the explicitly named statistics. Two paired-valve dossiers (`b9e74ecc8a`, `cc7c4015f9`) determine the number of individuals but do not specify a unique reduction from two valve measurements to an individual's dimensions. Their slopes/intercepts require a disclosed analytical choice; a scientifically defensible answer with assumptions or a justified stop must be accepted. A single mandatory numerical key would be too narrow for those two.

Both PERMANOVA dossiers determine pseudo-F, R-squared and sample count, but do not by themselves establish a valid significance test: the requested outputs omit a permutation p-value, and serial core observations need a justified exchangeability design. These are limitations of the word “test” and of inferential interpretation, not reasons to refuse the requested descriptive statistics. The marker-based zone descriptions do not establish that the test is circular; nor do they establish independent zoning evidence. Clarify independence if biological corroboration is claimed.

The radiocarbon dossiers with rejected dates give sufficient authority to omit those dates. Their “age reversal” comments cannot be independently reproduced from the supplied sequence: the flagged age is still younger than the next deeper date. Treat this as a dating-report assertion and retain its rejection status; do not invent a reversal evident in these rows or silently restore the date.

Across all packets, primary row keys are unique, CSV/TSV rows are rectangular, relevant sample/count and catalogue/measurement joins match exactly, all count entries are nonnegative integers, and all valve dimensions are positive. All sample count totals are positive. All-zero taxon columns are harmless for the requested quantities. Counts of biological individuals are distinct from counts of valves.

The common answer schema explicitly allows `completed_with_assumptions` and `stopped` (`answer.schema.json`, status description); the review's alternative outcomes therefore have a natural reporting route.

## 217b2001e5 — numerically sufficient

**Evidence.** `task.md:3–5` requests log10 width-on-length RMA with dimensions in millimetres, plus mean length and n. `dictionary.md:3–4` says dimensions are as recorded and gives observer units. `observers.csv:2` is `KT,ruler,cm,2023`; rows 3–5 specify mm for RM, AS and JB. `shells.csv:2` gives D001, KT, length 2.8, width 1.3; `shells.csv:27` gives D026, AS, 58.0 and 28.8.

**Handling.** Join observer metadata; multiply both dimensions of all 21 KT specimens by 10 before logging or averaging. Fit signed RMA slope `sign(covariance) * sd(log10 width)/sd(log10 length)` and intercept through the log-space means. Use all 95 specimens. Checks: slope 0.9411802461, intercept -0.2187185854, mean length 25.9546315789 mm.

**Limits and innocuous details.** Instruments differ in precision, which does not justify exclusion, numerical de-rounding, or an unrequested weighted regression. The large D026 observation is positive and has no error flag; keep it. Locality and season do not mandate separate fits under the pooled task. This is an across-specimen relationship, not proof of an individual's growth trajectory. No material ambiguity in requested quantities.

## 4c7865607f — numerically sufficient

**Evidence.** `task.md:3` specifies youngest minus oldest Shannon diversity, natural logs. `dictionary.md:4` states depth below top and an undisturbed core. `samples.csv:16` gives S06 at 5 cm and `samples.csv:9` gives S16 at 395 cm. Their counts are `counts.tsv:7,17`. `lab_log.csv:18` records two unidentifiable broken tests for S11, not an instruction to alter any taxon count.

**Handling.** Join IDs, select S06 as youngest and S16 as oldest, calculate `-sum(p log p)` using each sample's own count total and zero contribution for zero counts. Checked change = -0.1086284777 (H young 2.9207120470; H old 3.0293405247).

**Limits and innocuous details.** File order, IDs, processing dates, analysts and batches are not ages. Do not add unidentified tests to named taxa or discard their sample. Two zero columns do not affect Shannon diversity. The result is an endpoint contrast; a monotonic temporal trend or an ecological cause is not established. No material numerical ambiguity.

## 4d932ec7d3 — numerically sufficient

**Evidence.** `task.md:3–5` asks for RMA across individuals and n individuals. `dictionary.md:3–4` distinguishes individual IDs from valve IDs. All 52 rows of `catalogue.csv:2–53` have different individual IDs, with one measured valve each; `measurements.csv:2–53` matches those specimen IDs exactly.

**Handling.** Join by specimen ID and use all 52 individuals once. Checks: slope 1.1096280843, intercept -0.2370918040, n = 52. Both axes are log10 dimensions in mm.

**Limits and innocuous details.** Mixed R/L valves alone do not create duplication; do not drop a valve side or collapse different animals. No evidence calls for exclusion by locality. The title “Growth allometry” should not be expanded to a longitudinal growth claim from this cross-sectional collection. No material numerical ambiguity.

## 5745229928 — numerical summaries sufficient; hypothesis-test interpretation incomplete

**Evidence.** `task.md:3–5` specifies one-way PERMANOVA on Bray–Curtis distances of relative abundance, using biozones A/B, and requests pseudo-F, R-squared and n. `dictionary.md:5` defines top inclusive and base exclusive. `zonation.csv:2–3`: A [0,160), B [160,360). `samples.csv:11` places Z08 at 156 cm; `samples.csv:4` places Z09 at 186 cm. All 22 samples fall in a zone: 8 A, 14 B.

**Handling.** Join IDs; normalize each complete sample to relative abundance; assign zones by those intervals; calculate standard distance-based one-way sums of squares, pseudo-F and explained fraction using n = 22. Keep Z08 in A. No exclusion or assumption about unknown zone membership is needed.

**Defects/alternatives.** A valid permutation significance conclusion is not determined by the materials. Sampling is ordered within one core; no exchangeability/serial-dependence treatment, permutation design or requested p-value is supplied. Report requested statistics as descriptive separation and state that they alone are not a significance decision. Dispersion differences could contribute to a PERMANOVA result. Zone boundaries refer to marker first/last occurrence, but the marker identities and independence from counted taxa are absent: do not assert circularity as fact or independent validation as fact. These cautions should not be used to force a numerical no-answer.

**Leave alone.** Unequal group sizes, differing sample totals and two all-zero taxa do not invalidate the specified calculations. Avoid inventing a gap in the published intervals.

## 6bf64e135a — numerically sufficient conditional on supplied age model

**Evidence.** `task.md:3` explicitly specifies younger than 11,700 cal yr BP and linear interpolation. `dates.csv:5` is OZ4926, 198 cm, 12,816 cal BP, `rejected`, “age reversal; reworked shell (Smith 2024)”. Rows 4 and 6 provide accepted 150 cm/7,920 and 255 cm/13,380 ties. `samples.csv:4` places S18 at 222 cm; row 16 places S19 at 223 cm.

**Handling.** Exclude the rejected date from model anchors, not the sample depth interval. Interpolate between accepted ties; all samples are bracketed. The boundary is 222.6923077 cm. S18 is 11,664 cal BP and eligible; S19 is 11,716 and ineligible. Use S01–S18, n_holocene = 18; row-normalize counts and average Bray–Curtis over 153 distinct unordered pairs, excluding self-comparisons.

**Limits and innocuous details.** No uncertainty ranges are supplied; the requested deterministic classification is available but should not be portrayed as uncertainty-free true Holocene membership, particularly at the boundary. The rejection comment's age reversal is not visible in the listed monotonic ages; respect the report's explicit status without claiming to have independently verified its rationale. Do not reinstate a rejected date just because the displayed sequence is monotonic. Zero taxa are harmless. No material numerical ambiguity under the supplied model.

## 74d46da548 — numerically sufficient

**Evidence.** `task.md:3`, `dictionary.md:4`: natural-log endpoint contrast in an undisturbed core. `samples.csv:5` gives S06 at 5 cm; row 11 gives S05 at 350 cm. Counts are `counts.tsv:7,6`. `lab_log.csv:4` says S05 was re-counted after audit, “counts unchanged”.

**Handling.** Use S06 youngest and S05 oldest. Checked Shannon change = -0.1184557923 (3.0034188631 minus 3.1218746554).

**Limits and innocuous details.** Recounting with unchanged counts is reassurance, not grounds for exclusion or adjustment. Processing batches and file order do not define chronology. Keep all taxon counts, with zero terms contributing zero. Do not infer a monotonic trend or cause from the endpoints. No material numerical ambiguity.

## 7e1dd826bb — numerically sufficient conditional on supplied age model

**Evidence.** `task.md:3` fixes linear interpolation and the strict 11,700-year threshold. `dates.csv:2–7` marks all six dates accepted, including OZ4926 at 198 cm/10,416 (`dates.csv:5`). The date ages rise with depth. `samples.csv:4,16` locate S18 at 222 cm and S19 at 223 cm.

**Handling.** Use every accepted date. All samples are bracketed, with interpolated S18 = 11,664 and S19 = 11,716 cal BP. Select S01–S18; n_holocene = 18; normalize rows and average the 153 unordered pairwise Bray–Curtis values.

**Limits and innocuous details.** There is no date rejection or visible reversal; do not invent one. The accepted 198 cm anchor lies exactly on its neighbours' straight line and needs no removal. Lack of age uncertainty limits interpretation, not the specified point calculation. Two all-zero taxa need no special handling.

## 7fec1108ad — numerically sufficient

**Evidence.** `task.md:3` and `dictionary.md:4` fix endpoint difference and depth chronology. `samples.csv:8` gives S01 at 5 cm; row 11 gives S17 at 395 cm. `counts.tsv:2,18` hold those samples. `lab_log.csv:4` describes S01 “sieved twice (clay); counted in full”.

**Handling.** Select S01 youngest and S17 oldest by depth. Checked Shannon change = -0.1086284777 (H young 2.9207120470; H old 3.0293405247).

**Limits and innocuous details.** Although IDs happen to follow chronology here, depth is the evidence. Sieving twice with complete counting does not call for halving counts or removal. Processing order and batches do not change ages. No causal or monotonic-trend inference follows. No material numerical ambiguity.

## 999b14b7e2 — numerically sufficient using supplied taxonomy snapshot

**Evidence.** `task.md:3` specifically requests raw genus-count Bray–Curtis over all sample pairs and genera with at least one specimen. `dictionary.md:3` puts taxa in rows and samples in columns. `taxonomy.csv:2–27` supplies identity mappings under its WoRMS 2025-10 source. `counts.tsv:4,12,23` already use Turborotalita quinqueloba, Neogloboquadrina pachyderma and Trilobatus sacculifer. `lab_log.csv:19` says N05 “low yield; counted in full”.

**Handling.** Match rows to the supplied taxonomy, extract genus, sum species rows within each genus, transpose conceptually to samples, and calculate raw-count Bray–Curtis over 210 unordered sample pairs. All 26 recorded names map. There are 16 positive genera. Retain all 21 samples, including N05 with 51 specimens.

**Limits and innocuous details.** “Legacy counts, 1987” does not require changing names already reconciled to the supplied taxonomy. Low yield is not a failed or incomplete sample; do not discard it or normalize against the explicit raw-count request. The metric mixes count-total differences with composition differences, so pure ecological turnover is a stronger claim than the output supports. “Current” is operationally the provided 2025-10 snapshot; no independent current-taxonomy verification was performed or needed to compute the dossier's specified statistic.

## b3501ee399 — numerically sufficient

**Evidence.** `task.md:3–5` specifies mm-based log10 RMA and mean length. All four observers have `unit_recorded=mm` (`observers.csv:2–5`). `shells.csv:2` gives KT specimen D001 as 27.7, 12.7; row 9 gives KT D008 as 16.6, 8.8. D026 is 58.0, 28.8 at row 27.

**Handling.** Use values as recorded for all 95 specimens; no unit conversion. Checks: slope 0.9503018692, intercept -0.2318175648, mean length 25.9483157895 mm.

**Limits and innocuous details.** Different caliper precision and seasons do not imply unit mismatch. Keep the largest specimen without evidence of error. Pooling is the requested descriptive estimand, not a causal or individual-growth conclusion. No material numerical ambiguity.

## b9e74ecc8a — individual count clear; slope/intercept not uniquely specified

**Evidence.** `task.md:3–5` says “across individuals” and n individuals. `dictionary.md:3–4` defines individual identity and per-valve measurements. `catalogue.csv:4,6` assigns V73357 L and V95943 R to I046; `measurements.csv:14–15` gives (15.35,13.07) and (15.43,13.14). `catalogue.csv:9,25` assigns two valves to I048 with dimensions (23.25,17.45) and (22.44,16.84) in `measurements.csv:37,8`. There are 64 valves from 49 individuals: 15 pairs and 34 singletons.

**Handling.** Do not call 64 valves 64 individuals or silently weight paired animals twice. A reasonable completion averages each individual's length and height in mm, then logs and fits RMA, with this explicitly disclosed: n = 49, slope 1.0328838181, intercept -0.1364159166. `completed_with_assumptions` is appropriate.

**Substantive ambiguity.** No averaging or valve-selection rule is supplied. Averaging logs (geometric dimensions), choosing R when present, or choosing L when present are defensible alternative conventions if stated, not necessarily errors. Checks: geometric mean gives slope 1.0328866194; R preferred 1.0326099154; L preferred 1.0331596053. They differ despite often small changes. A justified stop asking for the biological measurement convention is also defensible if a unique answer is required. A single exact numerical key needs a clarified rule or acceptance of alternatives. Retaining all valves with an explicit individual-weighted model changes the simple unweighted RMA estimand and needs justification.

**Leave alone and interpret carefully.** Paired valves are real measurements, not duplicate records to delete by row equality. Singletons are not invalid. Do not sum valve lengths/heights as body dimensions. The task supports cross-sectional size allometry, not observed individual growth.

## cc7c4015f9 — individual count clear; slope/intercept not uniquely specified

**Evidence.** Same individual-level request in `task.md:3–5` and valve definitions in `dictionary.md:3–4`. `catalogue.csv:2,52` maps V17737 R and V17648 L to I044; `measurements.csv:62,29` gives (19.26,14.64) and (19.31,14.68). `catalogue.csv:4,10` maps two valves to I052; `measurements.csv:28,32` gives (15.05,13.51) and (14.99,13.46). There are 72 valves from 52 individuals: 20 pairs and 32 singletons.

**Handling.** Use one defined representation per individual. Arithmetic mean dimensions before log10 is a reasonable disclosed choice: n = 52, slope 1.0281815922, intercept -0.1349127417. Do not silently use the 72-valve fit (slope 1.0155058770) as an equally weighted individual fit.

**Substantive ambiguity.** No unique within-individual reduction is prescribed. Geometric means give slope 1.0281782654, R-preferred 1.0280346644, L-preferred 1.0283098306. Accept explicit scientifically reasonable alternatives or a justified no-answer; do not require a single hidden averaging convention. To make the dossier determinate, specify the individual dimension definition and whether averaging precedes the log transformation.

**Leave alone and interpret carefully.** Mixed valve sides and real pair differences are expected data structure, not evidence of corrupted records. Do not exclude singletons or sum valves. “Growth” remains an interpretation of cross-sectional allometry, not a tracked growth trajectory.

## dd5fa79d7f — numerical summaries sufficient; hypothesis-test interpretation incomplete

**Evidence.** `task.md:3–5` asks specifically for A versus B. `dictionary.md:5` states interval conventions. `zonation.csv:2–4` has A [0,140), `unzoned` [140,185) with “marker taxa absent; not assignable”, and B [185,360). `samples.csv:11` gives Z08 at 156 cm. Z09 is 186 cm (`samples.csv:4`).

**Handling.** Exclude Z08 from the A/B comparison and record its actual unzoned status; retain 7 A and 14 B samples, n = 21. Normalize rows to relative abundance before Bray–Curtis and one-way distance-based sums of squares. Do not nearest-zone impute, carry forward A, create a third test group, or delete every sample from a vaguely described transitional region.

**Defects/alternatives.** Requested pseudo-F and R-squared are well defined; significance is not established without an appropriate permutation/exchangeability scheme and p-value. The same within-core dependence, possible dispersion contribution, and unverified independence of marker-defined zoning noted for 5745229928 apply on this packet's own evidence. A descriptive completion is justified; an assertion of significant independent ecological validation is not.

**Leave alone.** The explicit unzoned interval is not a data formatting error. Unequal group sizes and all-zero taxa do not prevent calculation. There is no evidence to exclude any of the 21 assigned samples.

## e212f56966 — numerically sufficient conditional on supplied age model

**Evidence.** `task.md:3` fixes the age threshold and interpolation. `dates.csv:5` explicitly rejects OZ4817 at 198 cm/12,816 as reworked; rows 4 and 6 provide accepted 150/7,920 and 255/13,380 anchors. `samples.csv:31` places S26 at 219 cm; row 16 places S27 at 224 cm.

**Handling.** Drop the rejected dating anchor and interpolate between accepted levels. Boundary depth = 222.6923077 cm; S26 = 11,508 cal BP and S27 = 11,768. Use S01–S26, n_holocene = 26; normalize rows and average Bray–Curtis over 325 unordered distinct pairs. All samples are bracketed by accepted dates.

**Limits and innocuous details.** The listed “age reversal” cannot itself be demonstrated by the displayed ages, but explicit rejected status resolves the model construction. Do not turn that caveat into inclusion of reworked material. Age uncertainty is not supplied and cannot be propagated; identify the summary as conditional on the point age model. Zero taxa and nonchronological metadata row order are harmless. No material ambiguity in requested point quantities.

## e4bcfe8f7c — numerically sufficient using supplied taxonomy snapshot

**Evidence.** `task.md:3` requests current-genus raw counts. `dictionary.md:3–4` gives orientation and taxonomy mapping. `taxonomy.csv:6,7,13` maps Globigerina pachyderma to Neogloboquadrina pachyderma, Globigerina quinqueloba to Turborotalita quinqueloba and Globigerinoides sacculifer to Trilobatus sacculifer. `counts.tsv:12,4,23` contains those recorded names. `lab_log.csv:19` says N05 “low yield; counted in full”.

**Handling.** Apply the supplied name mappings before genus aggregation; match all 26 taxa, yielding 16 positive genera. Retain all 21 samples including N05 (51 specimens) and calculate raw-count Bray–Curtis over 210 pairs. Genus grouping of legacy strings alone would misassign abundance.

**Limits and innocuous details.** Low count yield, repeat sieving and rechecked counts are not failures. No rarefaction, normalization, invented split correction or genus assignment for unidentified broken tests is requested. Raw-count dissimilarity does not isolate composition from count-total differences. Treat the provided WoRMS 2025-10 mapping as the operational taxonomy rather than asserting independently verified contemporary taxonomy. No material numerical ambiguity.

## e5fac005db — numerically sufficient using supplied taxonomy snapshot

**Evidence.** `task.md:3` and `dictionary.md:3–4` fix raw genus counts and orientation. `taxonomy.csv:6,7,14` gives the three genus-changing mappings for pachyderma, quinqueloba and sacculifer; their rows are `counts.tsv:25,9,11`. `lab_log.csv:17` says N05 “low yield; counted in full”; row 7 notes two unidentifiable broken tests at N10.

**Handling.** Map names, aggregate counts by current genus, retain all 23 samples, and calculate raw-count Bray–Curtis over 253 unordered pairs. All 24 recorded names map; 17 genera have positive total counts. N05 has 44 specimens and is a valid observed sample.

**Limits and innocuous details.** Do not delete N05 as an outlier, add guessed taxa for broken tests, or normalize against the task. Raw-count dissimilarity combines abundance-total and compositional differences. Operational “current taxonomy” is the supplied dated mapping, not an independently refreshed external taxonomic assessment. No material numerical ambiguity.

## Bounded review conclusion

No packet requires an invented correction, fabricated taxonomic inference, age extrapolation, or recovery of missing IDs. Two need an explicit within-individual measurement convention for unique numerical grading; two need restrained significance language and, if a real test is intended, an inferential design extension. The remaining limitations concern the interpretation of otherwise computable summaries. These conclusions are based only on the materials and the decisive checks reported here.
