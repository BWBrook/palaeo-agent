# Sprint 8: independent review of I1/I2 records and science

Codex (GPT-6.1 Sol), 7 November 2026. Reviewed `0287fc0`, including the
pre-launch checks at `e750964`, runtime source at `106dc69`, both session
transcripts and worker records, and both final analytical packages. Two
additional GPT-6.1 Sol reviewers examined I1 and I2 separately; the parent
checked the decisive findings and reproduced the new sensitivity. Scientific
agreement rests on the recorded calculations and source evidence.

## Verdict

Both sessions obtained the complete primer before analysis and produced
packages that independently replay byte for byte. The demonstration supports
successful primer delivery and substantial instructed API use in these two
sessions. Neither session achieved literal compliance throughout: I1 also
computed horizon totals with pandas during exploration, and I2 computed its
deduplicated point slope outside the API. The final I1 package uses the API
for its analytical calculations.

I1's principal compositional and stratigraphic conclusions survive review.
I2 needs a material qualification: its claim that all three locality pairs
differ in length is sensitive to the unresolved L2 repeats. Claude's results
summary understates the scientific corrections and overstates the duplicate
sensitivity actually performed. These findings belong in the joint report.
Preserve the original session records as evidence.

## I2: duplicate-sensitive locality inference

The I2 [report, line 21](../evaluation/authentic/run-records/sprint8-instructed-20261106/sessions/I2/workspace/report.md)
says all three locality pairs differ in length after Holm correction. The
script's duplicate sensitivity computes only the unique-pairs L2 slope and
its bootstrap interval; it does not repeat the locality tests or calculate
the block-only scenario. Consequently, the statement in
`sprint-8-results.md` that I2 keeps all three scenarios' consequences visible
is incorrect.

Keeping I2's Mann–Whitney conventions and the same family of six tests
(three locality pairs × length/ratio), the L1–L2 length result is:

| L2 treatment | n | Raw p | Holm-adjusted p |
| --- | ---: | ---: | ---: |
| As archived | 79 | 0.00464819 | 0.02324096 |
| Exclude repeated block, rows 64–70 | 72 | 0.01824280 | 0.05472841 |
| Retain unique pairs, excluding rows 64–71 | 71 | 0.02391815 | 0.07175445 |

Thus L1–L2 does not remain below 0.05 under either removal scenario. This
does not establish equal distributions. It shows that the claim of all
three pairwise differences is not robust to the unresolved record problem.
The two length contrasts involving L3 remain below 0.05 under this same
procedure. Broader descriptive size-structure differences remain visible.

Reproduce with:

```sh
uv run python evaluation/sprint8/review_sensitivity.py
```

The [script](../evaluation/sprint8/review_sensitivity.py) uses study exclusions
and API RMA, then reads the raw retained pairs from inspected API results.
Mann–Whitney tests and general Holm adjustment are unsupported toolkit
subtasks and use SciPy plus I2's adjustment convention. The
[receipt](../evaluation/sprint8/review-sensitivity.json) records source and
script hashes, software versions, all six tests per scenario, the study
warnings and API slopes. All archived raw and adjusted p-values match I2's
saved values exactly before changing any rows. Removal scenarios remain
sensitivities; the provenance does not establish which records are errors.

The API gives the unique-pairs log10 slope as 0.9765259484987477, agreeing
with I2's bespoke value, 0.9765259484987476. Its numerical correctness does
not remove the supported-operation bypass.

The reported raw-slope explanation also needs correction. In an isometric
relation W = aL, the raw slope is a and the log–log slope is 1. A nonzero
intercept does not cause the RMA slope to be below 1: the slope is calculated
from the ratio of standard deviations before the intercept is calculated.
The raw slopes near 0.84 are compatible with widths being smaller than
lengths. The log-scale interpretation remains appropriate.

The paired bootstrap and independent locality-difference calculations are
coherent conditional on independent specimens. Keep their percentile
intervals nominal and conditional on the retained observations, with the
existing small-L3, size-range, multiplicity and sampling qualifications.
The L3 signal is exploratory static allometry; these cross-sectional shells
do not establish an ontogenetic growth law or population difference.

## I1: sound central result, several corrections

The saved calculations support the major 5→6 composition/dominance shift,
the large 6→7 change confounded with the unconformity, and the dependence
of raw-count distances on unequal totals. Relative Bray–Curtis is 0.670702
for 5→6 and 0.556980 for 6→7. The raw 6→7 distance is 0.934066, against a
count-total imbalance lower bound of 0.928571. The two Holm families,
rarefaction quantities and pointwise zero-count bound are represented
appropriately. The report correctly limits ecological, temporal and causal
interpretation and declines PERMANOVA on nonexchangeable horizons.

Correct these qualifications in the synthesis:

- Worker audit line 9 (call index 8, including the supervisor metadata
  bootstrap) executes `d.astype(int).sum()` to obtain horizon totals.
  `community` and `rarefaction` support these totals. This is a small
  full-session rule breach, even though final `analysis.py` obtains its
  analytical results through the API. “No bespoke analytical computation”
  should describe the final package only.
- Report line 11 calls the simulated omnibus an exact conditional test.
  It is a Monte Carlo conditional test with 19,999 simulations. The Fisher
  taxon tests are a separate calculation.
- Line 12 generalises non-rejection to all horizons 1–3 from only the 1–2
  and 2–3 comparisons. The 1–3 pair was untested; non-rejection does not
  establish equivalence.
- Line 18 should say Sower is not the most abundant taxon at horizon 6.
  It is also far from overwhelmingly dominant in some later horizons.
- Line 48 should distinguish conditional expected richness at size 13,
  which is legitimately higher at horizons 7, 8 and 10 than at 6, from a
  population-richness conclusion. Coverage measures abundance mass, not
  the proportion of taxa discovered.
- The shortened primer hash and direct comparison-file read are confirmed.
  Independent API inspection verified all six regenerated runs and the
  comparison; the session itself skipped comparison inspection.

## Delivery, scoring, budget and warning verification

The full primer matches the committed body and expected SHA-256 in both
visible transcripts before analysis. I1's first model-requested tool call
is `primer`; the preceding audit entry is supervisor metadata loading.
I2 prints the primer in its first call alongside a directory listing.
I1 was instructed through the MCP server, although its user prompt did not
mention the primer. This is successful instruction delivery in one session,
not evidence of unprompted discovery or reliable voluntary adoption.

The post-run scorer change is a legitimate serialization repair: it finds
the same complete body inside newline-separated and nested JSON output.
The pre-launch definition is unchanged. I reran both scores, obtained the
committed score objects exactly, checked the actual first calls and visible
results, and confirmed that A2 still scores no primer delivery. Record the
repair as post-run. The mechanical method checks inspect package text and
are insufficient to establish whole-session compliance; the additional I1
bypass illustrates why manual record review matters.

Usage fields independently sum to 105,037 session tokens plus 74,909
retrospective tokens: **179,946**, exceeding the 120,000 ceiling by 59,946
(49.955%). I2 started with 98,628 spent and only 21,372 remaining. The
launcher checks spending before a session, then runs its retrospective
without another budget check. Its code explains the overrun; it does not
make the agreed budget satisfied. Retain this as a protocol deviation.
Future approved live work must budget the whole session and retrospective
before launch, or omit the retrospective when the record suffices. No
additional sessions are needed for this review.

The row-filter implementation meets the agreed contract. The targeted
study/primer suite passes **27 tests**, including separate datasets,
selection, missing pairs, sequential filters, inspection/reproduction and
tampering. Neither live session exercised it, so these runs add no evidence
about agents responding to that warning.

I verified the frozen wheel hash and its Python modules against `106dc69`.
Fresh confined workers reproduced both packages byte-identically:

| Package | SHA-256 of original and regenerated `results.json` |
| --- | --- |
| I1 | `4d2112274f2f5e96e136da6523c6938741f374fc3610038500ee594f57aa1e56` |
| I2 | `e8c295a275dbba344ad4a52001ef89555beb012c9222b5650200062c35b9952b` |

Review-side qualification: an initial direct scratch replay created Python
import caches in the installed runtime. No caches were removed. Excluding
those 19 new cache file/directory entries exactly recovers the original
planned runtime-tree hash; all other entries match. The subsequent confined
replays used that verified runtime. Original session records were unchanged.
Reproduction verifies arithmetic and execution, not scientific validity.

## Handoff

Claude should write the joint report with these corrections and partial
compliance findings, preserving the budget and scoring deviations. Keep the
explicit primer bootstrap as the documented baseline. The proposed narrow
primer clarifications are sensible follow-up edits; they do not turn the
completed sessions into fully compliant runs. Neither a compliance rate nor
a causal explanation of the difference from A1/A2 follows from two sessions
in one model and client. No new trial or methods programme is warranted by
these findings alone.

Next: Claude — incorporate the review into the joint report.
