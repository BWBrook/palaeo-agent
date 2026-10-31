# Sprint 4 interim independent review

**Decision: repair before freeze; arithmetic checks pass conditionally.**
Reviewed bank `4bf28f8`, study implementation `bf168cc`, in checkout `71f29d1`.
This is the early portion of the agreed Codex pre-freeze gate while Claude
continues the scorer, flaw design, protocol and launch work. Those remaining
components have not been approved by this review. No live model trials ran.

## Independent numerical checks

Two separate materials-only computations covered all **32 items**: 24 pilot
items and 8 calibration instances. Neither reviewer read the generator or
keys before saving predictions and reporting their SHA-256 seals. They used
standard-library rational Bray–Curtis/PERMANOVA sums and independent RMA and
Shannon formulas, without importing the toolkit. Only then were keys opened.

All keyed numerical targets agree with the independent primary or explicitly
conditional calculation; the largest absolute difference is **2.78e-17**.
That establishes arithmetic under a chosen handling, not that every handling
is entailed by the task. The unchanged predictions retain alternative answers
and non-identifiability witnesses.

- [P01–P06 report and evidence](../evaluation/pilot/review-codex/p01-p06/report.md)
  — seal `13548922b74011ba681882a9b5dde3a7728011456fe19c21f7b5e7967e289938`.
- [P07–P12 report and evidence](../evaluation/pilot/review-codex/p07-p12/report.md)
  — seal `7b5c493ef2f418303316131544cd5e8f0800b3a8daf3e70ba9dcda4b4b501ca9`.

The parent verified both script and prediction hashes, inspected the reference
formulas and compared the saved receipts. The generator remains unread.

## Bank findings

| Finding | Evidence and required disposition |
| --- | --- |
| P01-trap changes the requested population | “All cores” includes an uncounted core. Different missing-core completions yield all-core mean BC 0.7044515956 or 0.7446141396. The keyed 12-core mean 0.6981803468 is a counted-subset result. Accept a justified unresolved answer or explicitly qualify/change the target. |
| P04-trap and P04-cal change the diversity target | Missing picked fractions leave full-community diversity unidentified. Restricting to eight recorded taxa is a conditional substitute; “mainly” in another size fraction does not establish identical coverage of the retained taxa. Repair the witness and scoring, or provide the missing target/coverage facts. |
| P08-trap and P08-cal omit a boundary convention | A sample is exactly at 142 cm. Strict versus inclusive selection gives pilot n=9/10 and mean BC 0.2343287882/0.2675993771; calibration n=7/8 and BC 0.2649284509/0.2940823193. Supply classification/intervals, avoid a boundary-coincident sample, or accept a declared convention. Also reconcile empty `exclusions_expected` with the requested subsets. |
| P01 zero-sample error signature is wrong | The stored signature 0.7401269601332332 is the control value. Treating the trap's zero-coded core as observed gives **0.7446141396204127**. Correct the error signature; the primary counted-subset arithmetic itself is right. |
| P02/P12 inference remains conditional | Requested F and R² are computable; the facts do not establish free-label exchangeability. Stratigraphic ordering alone does not prove dependence either. Do not require agents to invent independence: distinguish descriptive statistics from an inferential test and score stated assumptions appropriately. |
| P09 is protocol adherence | The right-valve selection is explicitly dictated. Its numbers are correct, but it should not be presented as a difficult, uncoached recognition of pseudoreplication. |
| P06 has a small exact permutation space | After pooling there are six cores, 3 versus 3: 20 label allocations. “999 permutations or more” should not disqualify exact enumeration; repeated Monte Carlo allocations do not create 999 distinct assignments. |

Other supplied failure signatures agree with the independent error
calculations. The weakest documented separation is P11-cal at roughly 16.6
combined tolerances. Detectable wrong numbers do not establish task difficulty.
Most items involve one clear convention or a short preparation chain; ceiling
risk remains. Use the planned disjoint calibration to test that risk. Removing
necessary information would add ambiguity, not useful analytical difficulty.

## Study implementation findings

The parent ran four synthetic challenges against the actual Python/MCP
implementation. The [reproducer](../evaluation/pilot/review-codex/study_checks.py)
and [observed receipt](../evaluation/pilot/review-codex/study-findings.json)
preserve the initial failures. Claude owns the implementation fixes.

| ID | Observed behaviour | Required invariant |
| --- | --- | --- |
| S1 | A study with declared analyses verifies as complete after its run directories are removed and its manifest's steps/runs are emptied. | Validate the exact declared step sequence, statuses and run coverage; complete requires every declared analysis. |
| S2 | MCP `study_inspect` follows a `runs/` symlink outside its configured session root and returns external run summaries. | Reject unsafe nested paths, including symlinked ancestors, before reading them. Checking only a final file's `is_symlink()` is insufficient. |
| S3 | A four-sample canonical derived matrix accepts method orientation `taxa_by_samples`, transposes again, and produces a complete verified result with three “samples” that are actually taxa. | Enforce the format and orientation of canonical derived inputs in method specifications. |
| S4 | A failed dataset is recorded, but later datasets disappear from the step log; only later analyses get `not_run`. | Every declared later step must appear as `not_run`. |

These are integrity and contract defects, separate from the intended ability
of a consistently declared but scientifically mistaken study to pass integrity
checks. That distinction remains appropriate for the reviewer experiment.
Keeping transformations in existing method specifications is a reasonable
narrowing of the preparation API, provided canonical data contracts are
actually enforced.

## Client boundary follow-up

A pinned custom model catalogue is a legitimate candidate for testing. The
prior objection is narrowed: its exact changes and their effects must be
recorded and identical across arms; metadata modification is not by itself a
reason to reject the route. The [scripted Codex client review](codex-client-scripted-review.md)
records successful confined calls in both arms, blocked hidden patch/shell/spawn
calls and inert resource helpers. The parent checked all 104 evidence hashes
and the worker call logs. Initial wire-format and approval failures remain
preserved. Codex initialization still lacks the required full inventory, and
a fail-closed live request gate remains unimplemented. Study tools also need a
new runtime and inventory; the probe used the sprint-3 wheel.

No client change in this review authorises a pilot freeze or bypasses the
remaining inventory, launch-accounting and review conditions.

## Handoff

Findings were posted as they emerged on Board thread 103, messages 2744,
2746 and 2747. Claude continues to own production, bank and protocol changes.
Codex owns these sealed checks and will verify the resulting amendments at the
pre-freeze gate. In particular, no complete gate approval is implied for the
unfinished flaw set, scorer, thresholds, resource accounting or live launcher.
