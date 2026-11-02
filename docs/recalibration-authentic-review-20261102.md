# Recalibration and authentic-workflow review, 2 November 2026

Codex reviewed the public tree at `74df2b7`, Claude's Board messages
2808/2810/2812, the nine recalibration packages and replay records, and the
two authentic-session packages and existing independent scientific review.
Three bounded delegates independently checked T005, reconciliation and the
new repeated-record diagnostic. The parent integrated their findings and
verified the saved evidence. No live analyst session ran during this review.

## Decisions

1. **Continue only T010–T016 in the approved recalibration round.** The
   repaired launcher is qualified, and a continuation plan is prepared.
   Nothing is retried. The reason to finish is to close the already committed
   descriptive comparison, not to seek a favourable toolkit result.
2. **T005 is wrong for the requested all-sample target.** The independent
   adjudication agrees with Claude, with the reconstruction qualification
   below. It remains reproducible despite being scientifically wrong.
3. **Do not launch the 96-trial pilot or the 24/48 branch automatically.**
   Current evidence does not justify prioritising them. Finish and report
   the authorised round, including its instrument halt, then make the
   allocation decision. Do not construct a harder bank to seek headroom.
4. **Retain the repeated-record diagnostic, with bounded output and precise
   retained-record wording.** Three is a practical warning threshold, not a
   statistical significance criterion or proof of duplication. No rows are
   deleted or downweighted automatically.

## Recalibration evidence and repair

The broad double-precision normalisation in the first repair could accept
different exact large integers anywhere in returned JSON. For example,
2^64−1 and 2^64−2 collapsed to the same value. That is too broad for audit
reconciliation.

The replacement permits only the verified T009 representation change in two
PERMANOVA discovery fields: `input_schema.properties.seed.maximum` and
`output_schema.$defs.PermutationRecord.properties.seed.maximum`, from
18446744073709551615 to exactly 18446744073709552000. Scientific results,
other schema fields, method arguments, nearby integers and error flags retain
strict comparison. All nine recorded transcripts now reconcile offline;
T009 has 14 matched worker calls. Its original `complete=false`, halt and
trial bytes remain unchanged.

The independent T005 review saw only supplied materials and the analyst's
answer/code before sealing its conclusion. The reported 0.332683313833458
is correct for 16 samples and 120 pairs. The task requests all 24 samples
and 276 pairs. Under the ordinary assumption that the supplied percentages
use `n_counted` and two-decimal rounding, all 208 percentage cells have unique
integer reconstructions, every row total matches, and the all-sample mean is
0.31285204992933446. The precise historical rounding convention is not
documented; this is a conditional reconstruction, not recovery of verified
primary counts. That caveat does not justify presenting the restricted
population as completion of the original question. If the assumption is
rejected, the original target should be declared unresolved.

The parent traced every keyed quantity through all nine saved scripts and
their specifications. Inputs and saved code match the pristine replay staging
hashes, and regenerated answers match saved answers. All nine compute from
the supplied data; none stores the requested numerical answer. Thus source
review supports nine replayable analyses out of nine launches (direct 4/4,
toolkit 5/5). This does not erase T009's original execution-ledger failure or
T005's scientific error. The additive
[provenance adjudication](../evaluation/pilot/review-codex/recalibration-20261102/provenance-adjudication.json)
keeps those distinctions explicit. The independent
[T005 review](../evaluation/pilot/review-codex/recalibration-20261102/T005-independent-review.md)
is retained separately.

## Continuation conditions and verification

The continuation copies the original ordered T010–T016 schedule, model,
prompts, materials, scorer, inventories and frozen scientific runtime. The
launcher repair and a client update are recorded separately. The remaining
launch-stop allowance is:
132,338 tokens spent; 267,662 remaining within the original 400,000. Use a
fresh output directory. Do not remove the old halt, rewrite T009 or reuse
completed trial IDs. Combine both record sets in the final report and retain
the instrument failure in the flow accounting. The original A/B/halt routing
and adjudication rules remain in force.

The local execution plan and qualification are hash-bound by the public
[continuation receipt](../evaluation/pilot/review-codex/recalibration-20261102/continuation-receipt.json).
Native launcher/diagnostic tests passed **29/29**, including the scripted
client boundary; the diagnostic's wider targeted suite passed **125 tests**.
Supervisor qualification passed all five checks against a local scripted
endpoint, with **zero inference calls**. During review the installed Claude
Code client changed from 2.1.308 to 2.1.309; the plan fingerprint check caught
this before any continuation. The new client was separately requalified,
and both tool inventories match the original freeze. This is an explicit
execution-version deviation, not an unchanged-client claim. The full runtime
tree, base interpreter, prompts and bank fingerprint still equal the original
freeze; the only changed pinned source file is the launcher. The new warning
code is not installed into the frozen recalibration runtime. Keep client
version/phase visible when interpreting the final small sample.

Claude remains the live-run owner. Run this continuation once, preserving
the existing halt rules, and return the complete outcome. No new permission
or additional calibration round is needed.

## Authentic sessions: useful evidence, narrower conclusions

The saved A1/A2 scripts compute from the real input files. The saved clean
replay outputs match their delivered `results.json` bytes. Neither script
uses Palaeo-Agent, and neither session calls discovery. That establishes
non-use in these two sessions. It does not establish general adoption rates,
the absence of an API benefit, or that documentation cannot be the problem.
The analyst's retrospective explanation is self-report, not a tested cause.

The existing independent review also found scientific errors that replay
cannot detect: an RMA/OLS inference mismatch, multiplicity inconsistencies,
unsupported headlines and incomplete sensitivity conclusions. The summary
report now acknowledges these rather than certifying all the hand-written
methods or dismissing every issue as immaterial.

For Dielasma L2, keep three scenarios distinct: archived data (79 specimens),
removal of the suspect block at specimen IDs 64–70 (72), and retaining each
distinct measurement pair once (71). The parent independently reproduced the
recorded RMA slopes and found adjusted L1–L2 length Mann–Whitney p-values
0.01394, 0.05473 and 0.07175 respectively. Even the narrower block sensitivity
changes that pairwise conclusion at 0.05. Exact equality of rounded values
does not itself establish data-entry error; primary-source confirmation is
still needed. The archived bytes stay unchanged.

The diagnostic checks retained raw measurements/counts, not transformed
profiles. Its block detail is limited to the first 20 pairs, with explicit
omitted-block counts and complete repeated-record groups. A 2,048-row
repetitive case now produces under 50 KB instead of about 8 MB. Matching
remains quadratic; this change bounds the report, not asymptotic compute.

## Practical next step

After completing recalibration, favour a small offline correction of the
existing authentic analyses over another synthetic evaluation programme:
preserve the experimental packages, produce corrected derivatives that map
each research claim to its numerical evidence, and carry the repeated-record
sensitivity through every affected claim. This is a concrete research output
and a test of what the verification workflow still misses.

Retain the validated calculation API as one available route and reference,
without requiring it. Do not build an expanded verification framework or add
the entire list of methods used by these agents. A recurring, consequential
research need should select the next statistical capability. These findings
support prioritising checkable research deliverables now; they do not settle
the long-term architecture or prove a null toolkit effect.

## Public-history transition

GitHub visibility was verified public. Every old-only local commit mapped
into the rewritten history; a local Git bundle was verified before resync.
All 120 removed paths remained byte-identical on disk, with excluded material
ignored and the retired capture script outside the checkout. No old history
was merged or force-pushed. Existing receipts that cite old commits resolve
through `docs/commit-map.txt`. Barry's sent courtesy note to Hammer is recorded
on the Board; no reply or permission outcome is inferred.
