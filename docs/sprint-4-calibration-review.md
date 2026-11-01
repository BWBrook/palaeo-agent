# Independent calibration review and next-design decision

Codex (GPT-6 Astra), 1 November 2026. Reviewed `4a80b5f`, including closure
`b69fd10` and integration revision `172c96e`. **The outstanding implementation
and metric-definition findings close. The current bank does not proceed to
pilot freeze: calibration meets the prespecified family-revision rule.**

## Verification

- Full native suite: **372 passed, zero skipped**, 81.78 s. These tests use
  scripted local endpoints; no new live model trials ran in this review.
- Remaining runtime/material and full-value reconciliation checks: **22/22**.
  The actual authentication status check now uses the same HOME/cwd/environment
  as the supervisor launch. See the [launcher review](../evaluation/pilot/review-codex/calibration-review/launcher/report.md).
- Common valid paired reviewer sets, n_S/n_A margins, within-set bootstrap and
  specific attribution now resolve the remaining protocol contradictions.
- The saved supervisor qualification demonstrates clean capture/supervisor
  requests and a detected positive instruction canary. Its pinned launcher
  and prompt hashes predate the managed-policy gate and exact-tool-name edits.
  Those changes were inspected; refresh qualification against the actual final
  freeze version rather than presenting the old receipt as a current-tree run.

## Independent P04 adjudication

A fresh-context reviewer received only the P04-cal materials and the two
answers, labelled A/B, with no keys, scores, arm identities or first-adjudicator
opinion. It computed the warranted summaries before reading the answers and
sealed its verdict. **Both answers are acceptable conditional analyses:**
both disclose restriction to the comparable T01–T08 fraction. Their numbers
agree with the independent calculation to floating-point precision. The whole
assemblage comparison remains unidentified; neither answer is accepted as an
unqualified full-community estimate.

- A maps to T013 (toolkit); B maps to T014 (direct).
- Independent means: 2017 = 1.9574135736608802; 2021 = 1.9395207219402053.
- Verdict SHA-256: `c5d7a1942daf5b2c5a909c3996f65fe832d39ed1b3a9a5dada8ff78eb9d1868e`.
- [Verdict, calculations and qualifications](../evaluation/pilot/review-codex/calibration-review/p04-packet-review/report.md).

An earlier reviewer accidentally exposed embedded trial scores while locating
metadata. Its verdict was discarded; its arithmetic and incident record are
retained separately. The fresh packet reviewer did not inherit that context.
The accepted verdict above is the independent second adjudication.

## What the calibration establishes

The 16 committed answer/trial records give **8/8 acceptable in each arm** after
P04 adjudication. Even without P04, direct 7/8 triggers the prespecified rule.
Recorded calibration usage totals **124,840 counted tokens**. Median counted
usage is 9,547 toolkit versus 4,650 direct, ratio **2.0533**. These are descriptive
costs on eight development instances, not a general cost or efficacy estimate.

Calibration has not observed the pilot's D, so do not say an unrun pilot has
already met D ≥ 0.90. Nor has it measured a reviewer advantage or a between-arm
reproducibility advantage. It demonstrates that these calibration tasks did
not discriminate correctness and supplies usability/cost observations.

## Revision decision

**Support offline revision around realistic multistep work, with sufficient
facts and matched controls.** Move evidence into plausible source records if
that better reflects real work, but do not remove facts needed to identify the
answer or create ambiguity as a proxy for difficulty. More rows and decorative
irregularities do not by themselves establish a harder scientific decision.

Do not require exactly two traps in every item or assume success probabilities
multiply: recognition errors can be dependent, and the combined item is a new
scientific task. Prefer coherent preparation/analysis chains. Recheck combined
interactions, controls, strata and independent numerical/sufficiency witnesses.
The cue audit should record what a reviewer inferred and why. One reviewer's
failure to find a trap is diagnostic, not proof of non-identifiability; absence
of an obvious clue is not evidence of fair difficulty. The revision must not
be tuned to whichever arm happened to err on these observed calibration items.

**Retain 96 analyst trials and two sessions.** Four sessions do not generally
halve the variance of the item-clustered contrast: between-item heterogeneity
does not disappear with more sessions. No advantage has yet been identified
that warrants doubling this allocation. The existing 939,600-token projection
for 96 trials is arithmetically correct under unchanged calibration costs;
larger revised tasks may change those costs. See the [design critique](../evaluation/pilot/review-codex/calibration-review/design/report.md).

Another 16 calibration trials would exceed the explicit calibration count cap,
even inside the 5M-token ceiling. I do not authorise that extension by inference.
Prepare and independently review the concrete revised bank offline first; then
put one bounded additional calibration proposal to Barry, with its costs,
stopping rule and no automatic extra round. No new allocation is needed for
the offline revision. A continued ceiling would be a valid stopping result,
not a reason to keep escalating tasks until a preferred effect appears.

## Evidence and protocol reconciliation

The integration/calibration launches preceded this independent closure review.
Their plans configured integration at 600 s / 400,000 counted tokens rather
than the agreed 300 s / 200,000, and calibration at 1,000,000 rather than
600,000. The recorded totals are below the agreed token ceilings (integration
48,884; calibration 124,840), but the configured departures remain deviations
and must be recorded. Do not retrospectively describe those gates as followed.

The committed integration material includes three complete records, one
executed/reconciled record marked incomplete after a config post-check, and a
preflight-halt record. Preserve those distinctions. The saved integration
receipt reports three reproduced studies; this review has not rerun those
studies from original packages. Full original transcripts, audits, workspaces
and start records were not located in the supplied committed evidence; their
durable locations were requested on Board message 2772. Reconcile and retain
them before stronger launch-history or reproduction claims. The answer-based
P04 verdict and calibration arithmetic do not depend on that missing replay.

**Claude is next:** reconcile original run evidence/deviations, prepare the
bounded revised design offline, and return its materials/witnesses for critique.
Keep historical results unchanged. No extra calibration, doubled session
allocation or pilot freeze is approved by this review.
