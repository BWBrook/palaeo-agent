# Review: Lake Selina research application and Sprint 8 wording

Codex (GPT-6.1 Sol), 7 November 2026. Reviewed `0833728`, the current
primer, method contracts and live Neotoma metadata. Two bounded reviewers
separately checked the I2 wording and statistical design; the parent checked
the source record and decisive findings. This is a proposal review and data
preflight, not the proposed ecological analysis.

## Recommendation

Lake Selina is a useful next research application. The unequal-count matrix
fits the existing operations, and the questions about pollen composition
and conditional richness are worthwhile. Amend the intake, chronology and
contrast definitions before launching the analysis. No new toolkit method
or compliance programme is needed on the evidence available here.

Make the whole depth-ordered record the primary analysis. I recommend
retaining 45–38 ka as a secondary, explicitly chronology-dependent interval
comparison. It can be motivated by the historical question, but it cannot
identify a human-arrival or megafaunal-extinction effect. The two climatic
transitions are contextual benchmarks, not controls that identify cause.
Barry's framing choice remains open; the design corrections below apply
whichever framing he chooses.

## What the source and preflight establish

I downloaded [Neotoma dataset 52767](https://api.neotomadb.org/v2.0/data/downloads/52767)
and its [chronology metadata](https://api.neotomadb.org/v2.0/data/datasets/52767/chronologies)
on 7 November. The record is collection `SEL1999`, attributed to Colhoun,
in the Indo-Pacific Pollen Database. The
[preflight receipt](research-application-preflight.json) records the raw
response hash, intake rule, API validations and chronology examples.

An intake retaining `element=pollen`, ecological group `TRSH` or `UPHE`,
and `units=NISP` yields 72 levels and 66 distinct taxon IDs. API validation
confirms nonnegative integer counts, no excluded levels or warnings, a
minimum total of 282 and acceptable resource bounds for all 72 levels at
explicit m=282. Individual-level API validation gives totals of 282–529,
median 364.5. The proposed 71 adjacent pairs also pass API validation with
B=99,999 and seed 7112026; no random tables were sampled. There is no
preflight evidence that an engine limit needs changing.

The proposal's temporal description needs correction:

- Default chronology **37590, IPPD-2**, is a Bacon model. Its sample point
  ages span **4–78,733 cal BP**. The proposed −133 and 89,987 are the extreme
  younger/older bounds, not the sample point-age range.
- Counts per 10-ka bin of point ages are 6, 6, 12, 8, 10, 10, 10 and 10
  from 0–10 through 70–80 ka. Thus “8–12 levels per 10 ka” and “11 at
  40–50 ka” are not correct for these point ages.
- Sample 531336 at depth 240 has age 40,189 and reported bounds
  36,725–43,989. Sample 531341 at depth 265 has age 45,481 and bounds
  40,785–50,901. These are broad, overlapping chronological assignments.
  Do not label the bounds as a particular probability interval until
  their definition is checked.
- The same download includes **37589, IPPD-1**, a best-fit-curve model
  described as using Excel and IntCal09. At depth 427 the two point ages
  are 261,204 and 78,733. This large disagreement requires a provenance
  account, rather than treating the alternative chronology as a modest
  error bar. The original article's long-record interpretation must not
  be conflated with the imported IPPD-2 time scale.

Reproduce the preflight from a saved API response:

```sh
curl -fLsS https://api.neotomadb.org/v2.0/data/downloads/52767 -o /tmp/selina-52767.json
uv run python scripts/check_selina_intake.py /tmp/selina-52767.json
```

The API may change; compare the response hash with the receipt. The script
uses public toolkit validation for totals and resource bounds. JSON
extraction, ecological-group filtering and age metadata summaries are
unsupported intake operations. Absent taxon entries are treated as zero
**for this preflight**; that convention needs confirmation before scientific
use. No rarefaction estimates, composition contrasts or significance
results were generated in this review.

## Required design amendments

1. **Freeze intake and the pollen denominator.** Save the source response,
   sample/depth IDs, source taxon IDs, ecological/element inclusion rule,
   missing-versus-zero convention, unidentified categories and any justified
   aggregation. The study layer supports row filtering and taxon
   rename/merge, but not taxon deletion. Terrestrial-only extraction must
   therefore be declared as unsupported intake; supported harmonisation
   uses `map_taxa`. Preserve source labels and counts. Reconfirm the common
   m after the final curated denominator, keeping it explicit in every run.

2. **Freeze the chronology and exact contrasts before viewing composition.**
   Explain why IPPD-2 is primary, distinguish archived model ages from the
   original paper's chronology, and check the controls and bound definition.
   Specify the three pairs by sample ID, depth, selection rule, nominal
   ages and elapsed duration. A pair bracketing a roughly seven-millennium
   interval is not one adjacent step. Define how the climatic comparisons
   have comparable temporal support; report unequal support where it
   cannot be matched. Chronology sensitivity should preserve sample
   identities and distinguish changing the age annotation from changing
   the selected endpoints. Marginal age bounds are not independent age
   draws and do not supply a joint age-depth posterior.

3. **Define the testing families once.** “71 adjacent pairs, plus three
   reported separately” is ambiguous. The simplest policy is one ordered
   list containing the unique union of all adjacent and named pairs,
   highlighting the named ones in reporting. Avoid duplicate/reversed
   pairs. One API call gives Holm across its omnibus pairs and a separate
   global Holm family across its pair×taxon Fisher tests. These two
   families do not jointly control a single error rate. Separate families
   would need an explicit rationale and separately stated claims.

4. **Specify Monte Carlo precision and the interpretation of change.**
   Freeze B and seed; B=99,999 is supported by the present interface and
   is a reasonable proposed starting allocation. Report simulation
   uncertainty. The built-in unresolved flag concerns raw p near 0.05,
   not Holm-adjusted decisions near roughly 0.05/74. Treat borderline
   adjusted classifications as Monte Carlo-sensitive; do not automatically
   rerun until significance appears. Rank composition change by effect
   size, such as proportional Bray–Curtis, rather than p-value. Display
   count totals, elapsed time and chronology uncertainty beside the effects.

The conditional counting tests remain coherent despite serial dependence
in the core: their claim concerns count allocation under the stated model,
and Holm tolerates dependence among pair tests. They do not establish
independent ecological replication, abruptness or cause. Check counting
protocol and pooling assumptions. Similarly, rarefaction supplies expected
observed pollen-category richness and subsampling SD, conditional on the
retained count table. Coverage is abundance coverage; equal counts and
high coverage do not establish equal completeness or plant-species richness.

Keep depth-ordered changes primary. A distance divided by an uncertain
age gap is an age-model-dependent descriptive index; it can be deferred
from this first application. Specify which existing R reference checks
which API quantity. Reuse the established `vegan`/coverage machinery;
adding `rioja` is unnecessary unless it supplies a stated independent check.

## Historical context and source limits

This is a reanalysis of an existing argument. Turney et al. already used
the Lake Selina vegetation/charcoal record to discuss environmental change
around human arrival and reported little change around 41 ka. The useful
contribution here is a taxon-resolved, counting-error-qualified assessment
of the archived counts, not an independent new pollen record or a causal
test of extinction. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC2527880/).

There is also newer, multi-method Lake Selina chronostratigraphy for the
**TAS1402** cores. It is relevant literature, but must not be transplanted
onto `SEL1999` without a supported core correlation.
[Primary data paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9036109/).

The full 1999 article was not inspected here; its abstract, publication
metadata and the API chronology record were checked. Reconcile the
original stratigraphic/chronological interpretation during the intake
stage before using named temporal transitions. The current
[Neotoma policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
permits attribution-based CC BY 4.0 reuse and asks for Neotoma, constituent
database, original investigators/publication and dataset DOI attribution.
The record returns two DOI identifiers; resolve their version/status in
the final provenance rather than choosing one silently.

## I2 wording verification and tranche closeout

The revised compliance account is accurate. I2's final package recomputes
supported n, length mean/SD and width mean, as well as the deduplicated point
slope. Its eight repeated L2 records are also recoverable from the API
duplicate groups. Fresh temporary API runs confirm exact agreement for
the duplicated summaries. Medians, ranges, skewness, histograms, fractions,
ratios and OLS are unsupported operations whose declarations are incomplete.
This extends the recomputation inventory missed in my earlier review.

Two remaining phrases should be corrected in the synthesis:

- `sprint-8-results.md` says the original report “quotes neither set”. It
  does quote n in the RMA table. Prefer: “The report does not separately
  cite the duplicated summary fields; results.json carries both.”
- `sprints-7-8-report.md` says I2 “started legitimately”. Prefer: “I2 was
  allowed to start by the implemented launch-stop guard.” Passing that
  guard does not establish compliance with the agreed total ceiling.

The proposed 150,000 reservation is a future policy, not current enforcement
or an established cost bound. With the old 120,000 ceiling it would permit
no launch. Any future trial needs a compatible agreed budget, and a
stream-driven stop remains conditional on verified usage semantics. No
future-trial implementation or new evaluation is needed for this application.

Next: Claude — correct the two phrases and revise the application design for Barry's framing decision.
