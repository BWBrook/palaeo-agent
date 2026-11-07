# Sprints 7–8 joint report: unequal-count assemblages, the agent primer, and instructed use

Claude (Opus 5.5) and Codex (gpt-6-astra, gpt-6 and gpt-6.1-sol, as recorded on the board), 7 November 2026.
Claude led the tranche and wrote this report; Codex implemented sprint 7 and
reviewed every stage. Analyst sessions: Claude Sonnet 5.5 in Claude Code
2.1.311. Barry W. Brook set the tranche and its rule. The full record of the
exchange is in [thread 136](correspondence/thread-0136.md).

## What Barry asked for, and what was delivered

| Request (Barry's tranche brief) | Delivered | Where |
| --- | --- | --- |
| One coherent, reusable workflow for comparing fossil assemblages with unequal counts, chosen on scientific merit | `rarefaction` (exact expected richness, its conditional variance, estimated abundance coverage) and `count_homogeneity` (declared pairs, fixed-margin Monte Carlo test, taxon Fisher tests, two Holm families, zero-count limits), alongside the existing `community` and `compare` | [contracts](rarefaction-contract.md), [contracts](count-homogeneity-contract.md), [implementation](sprint-7-results.md), [review](sprint-7-review.md) |
| A primer that makes the NEVER rule unmistakable | One packaged primer with Barry's rule verbatim, the grounds and non-grounds, an unsupported-parts table and a worked map | [`src/palaeo_agent/primer.md`](../src/palaeo_agent/primer.md) |
| A reliable way to deliver the full, versioned primer, without assuming instruction files or system prompts are read | Python `primer()`, CLI `palaeo-agent primer`, MCP `primer` tool and server instructions, `discover` pointers, exact text with version and SHA-256, verified from the installed wheel and `uvx`; an explicit bootstrap line for users | [sprint-7 results](sprint-7-results.md), [qualification](../evaluation/sprint8/qualification.json) |
| A small, realistic demonstration of primer delivery and actual API use, distinct from voluntary adoption | Two live instructed sessions, I1 and I2, with checks fixed before launch | [results](sprint-8-results.md), [review](sprint-8-review.md) |
| Checking other code without claiming that replay or agreement establishes validity | A field-labelled cross-check of the corrected analyses (159/159 matched quantities), framed as arithmetic only | [receipt](../analyses/cross-check/receipt.json), primer §7 |

## The workflow

**Rarefaction.**
- It gives the expected richness of a random subsample of m specimens, with
  the variance of that subsampling, and estimated coverage. Coverage is the
  share of the assemblage's abundance represented, not the share of taxa
  found.
- It interpolates only. Equal-coverage standardisation is excluded because
  the Coed Duon horizons have no common coverage target: horizon 1's
  estimate at m = 1 already exceeds horizon 10's full-sample coverage.
- The arithmetic matches `vegan`, the pinned iNEXT coverage function and a
  fresh PAST 5.4 export (260 comparisons). It uses stable 50-digit products.

**Count homogeneity.**
- For each declared pair it asks whether the counts differ by more than
  counting noise would produce under a common multinomial, and in which
  taxa.
- The omnibus is a Monte Carlo conditional Pearson test. It reports its
  simulation error and an unresolved flag. Taxon tests are Fisher tests.
- Pair claims form one Holm family; all pair × taxon claims form another.
  The result says that the two families do not jointly control one error
  rate.
- It tests counting error only, not between-collection variation or cause.

**The study layer** gained two pre-freeze fixes found in review:
- an `output_exists` refusal;
- a `row_filter_removes_pairs` warning. A row exclusion in a wide
  measurement table silently removed seven L1 specimens when the L2 block
  was excluded in the same dataset.

## The demonstration

| | I1 Coed Duon | I2 Dielasma |
| --- | --- | --- |
| Delivery path | MCP: server instructions and `primer` tool; the user said only "use the toolkit" | Python: the user asked the agent to print the whole `primer()` object first |
| Full primer read before analysis | yes (first model-requested call) | yes (first call) |
| Final package through the API | yes: `community`, `compare`, `rarefaction`, `count_homogeneity` | yes: `validate`, `rma`; inference declared unsupported |
| Whole-session compliance | partial: exploratory horizon totals computed with pandas | partial: deduplicated point slope computed outside the API, undeclared |
| Unsuitable design forced | no (declined PERMANOVA on horizons) | no (descriptive RMA never presented as inference) |
| Package replays | byte-identical | byte-identical |

**Science after review.**
- **I1.** The 5→6 compositional and dominance shift is robust across
  representations. The large 6→7 change is confounded with the
  unconformity, and raw-count distances there are mostly total imbalance:
  0.934 against a lower bound of 0.929.
- **I1 report corrections:**
  - the omnibus is a Monte Carlo test, not an exact one;
  - non-rejection at 1–2 and 2–3 says nothing about 1–3, and does not show
    equivalence;
  - Sower is not the most abundant taxon at horizon 6, which is narrower
    than "uniquely non-dominant";
  - equal-count expected richness is not population richness.
- **I2.** The log–log slopes support near-isometry in L1 and L2, and an
  exploratory, imprecise steeper slope in L3. The claim that all three
  locality pairs differ in length is **not robust** to the unresolved L2
  repeats. L1–L2's Holm p moves from 0.023 to 0.055 (block removed) or
  0.072 (unique pairs). The L3 contrasts hold
  ([sensitivity](../evaluation/sprint8/review_sensitivity.py)).
- **I2's raw-slope explanation was wrong.** Under isometry W = aL the raw
  slope is a ≈ 0.84 because widths are smaller than lengths, not because of
  an intercept.

**What this shows.** In these two sessions, when told to use the toolkit,
both agents obtained the full primer before analysing. They built their
final analyses on the API, declared what it could not do, and avoided
forcing unsuitable designs. They also made small bypasses during the
session and some scientific overstatements that independent review caught.
This is consistent with Barry's hypothesis that A1 and A2 ignored the API
partly because they were not firmly told. Two sessions in one model and
client establish no compliance rate and no causal explanation of the
difference from A1 and A2. They also say nothing about voluntary adoption:
A1 and A2, where neither discovered the toolkit, remain the only evidence
there.

## Deviations

1. **Budget.**
   - Counted tokens totalled 179,946 against the agreed 120,000 ceiling, an
     overrun of 59,946 (50 %). The sessions used 105,037; the follow-up
     retrospective questions used 74,909, because each resumes the full
     context.
   - The launcher checks spending only before each session. I2 started at
     98,628, and I had not projected the retrospectives' cost.
   - Future live work must budget each session together with its
     retrospective at launch, or omit the retrospective when the record
     suffices.
2. **The scorer was repaired after the runs.**
   - It missed I2's primer, which sat in a multi-line, JSON-wrapped output.
   - The check's definition was fixed before launch and is unchanged. Codex
     reproduced the scores, and the A2 negative control still shows no
     delivery.
3. **Summary errors in the first results write-up**, corrected after
   review:
   - it said I1 had no bespoke computation, which is true of the final
     package only;
   - it said I2 kept all three duplicate scenarios visible, which is wrong.
4. **No live evidence on the row-filter warning.** Neither session used
   `study`.
5. **A review-side replay created import caches in the frozen runtime.**
   Excluding exactly those entries recovers the planned tree hash, and the
   original records are unchanged.

## Recommendations

- **Delivery.**
  - Keep the explicit bootstrap line ("Before any analysis, read its
    primer … and follow it") as the documented baseline.
  - MCP-native delivery also worked once in this client, but one session
    shows no reliability, and it does not work under `--bare`.
- **Primer.** Four narrow clarifications are now applied (SHA-256
  `cdec09d1…`; the sessions used `47cab284…`):
  - `inspect_comparison(...)["report"]` in the §4 table;
  - the full 64-character SHA-256 in §9;
  - `study` exclusion followed by the same operation for deduplicated
    sensitivities (§3);
  - exploratory checks of supported quantities listed as non-grounds
    (§1).

  Barry's rule is unchanged.
- **Review stays necessary.** The mechanical checks read package text.
  Codex's independent reading of the whole record found the I1 bypass and
  the I2 robustness problem. Neither a primer nor scripted checks replace
  that.
- **No further trials are proposed on this evidence.**
  - A later tranche could measure compliance properly: more sessions,
    models and clients, with budgets that include retrospectives.
  - It could also test whether agents act on the row-filter warning.
  - Both would need Barry's decision and budget.

## Roles of the AI systems

- **Claude Opus 5.5** (Claude Code desktop):
  - led the tranche;
  - wrote the proposal, both methods contracts and the primer;
  - reviewed the implementation scientifically and wrote the cross-check;
  - added the study fixes and the row-filter warning;
  - froze and qualified the runtime, fixed the checks, ran I1 and I2, and
    wrote this report.
- **Codex** (gpt-6-astra and gpt-6 for implementation; gpt-6.1-sol for reviews):
  - critiqued the proposal and corrected both contracts;
  - implemented both operations, the primer delivery and the R and PAST
    references;
  - specified the row-filter warning;
  - reviewed the sessions independently, including the I2 sensitivity.
- **Claude Sonnet 5.5** was the analyst in I1 and I2.

Agreement between the model families is not independent validation. The
reference implementations (R, iNEXT, PAST) and exact enumerations carry the
numerical checks. Barry reviews this report before anything is released.
