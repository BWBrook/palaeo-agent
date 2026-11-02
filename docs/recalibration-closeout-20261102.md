# Completed recalibration review and practical decision

Codex reviewed `36813b2` on 2 November 2026, including Claude's completed
round and corrected authentic analyses. Two independent Codex reviewers
checked execution/provenance and the final P04 stops separately. The P04
reviewer saw only materials, answers and scripts before sealing its verdict;
the parent then checked that verdict against the frozen key. No additional
live analyst or reviewer experiment ran.

## Decision

Accept the completed round as **branch B**, and close this evaluation tranche.
Do not launch the 96-trial correctness pilot, the 24/48 checkability study,
or another synthetic bank. This agrees with Claude's recommendation and
Barry's direction to prefer evidence that can change a development decision.
It is a decision not to spend on the branch-B study, not an observed B2–B5
reviewer outcome or an equivalence verdict.

| Endpoint | Direct | Toolkit |
| --- | ---: | ---: |
| Correct requested outcome, including one justified stop per arm | 8/8 | 7/8 |
| Replay with source provenance confirmed | 8/8 | 8/8 |
| Median counted tokens | 8,557.5 | 18,811.5 |

T005 remains wrong for the requested population. T014's correct stop has a
separate interpretive flaw below. Total counted tokens are **206,854**;
the ratio of arm medians is **2.198**. These are descriptive results from
eight pairs, one analyst configuration and a development bank, not a causal
cost estimate or evidence that the toolkit has no benefit. The client changed
from 2.1.308 to separately qualified 2.1.309 between phases; that deviation
remains visible. The scientific runtime and task bindings were retained.

## Independent verification

The [execution audit](../evaluation/pilot/review-codex/recalibration-completed-20261102/execution-audit.md)
and [machine-readable receipt](../evaluation/pilot/review-codex/recalibration-completed-20261102/execution-audit.json)
confirm the unique ordered T001–T016 schedule, exact continuation-plan hash,
seven clean reconciliations with 38 matched worker calls, and 53 staged files
matching their source materials. Saved regenerated answers match the delivered
answers. All seven continuation scripts were inspected, including T011's
study specification; their reported numbers derive from the supplied inputs.
The original nine record hashes match the prior review. T009 remains marked
incomplete in its original ledger and its historical halt remains intact.
R = 16/16 measures reproducibility, not scientific correctness or flawless
execution of the original instrument.

The [sealed P04 adjudication](../evaluation/pilot/review-codex/recalibration-completed-20261102/P04-independent-review.md)
independently reproduces the diagnostic quantities and confirms both stops.
The unpicked 2017 fine residues prevent the requested complete-assemblage
comparison. T014's claim that a campaign difference would be an artefact
overstates this: fraction coverage confounds the comparison, while the true
campaign difference remains unknown. The parent retains the correct-stop
endpoint because it meets the frozen acceptable alternative, and records
the flaw rather than certifying every sentence. Even a downgrade of T014
would leave direct 7/8 and the same branch-B classification.

Both P04 scripts have empty requested `results` but compute diagnostic
numbers in their `issues` text. Their stopping decisions are fixed narrative
for these cases, not general evidence-dependent validators. Source review
and independent recomputation support the case-specific outputs. The P04
reviewer's attempted script execution stopped at a missing pandas import;
the separate execution audit verified existing replay receipts and hashes.
No new P04 replay is claimed. The additive
[adjudication receipt](../evaluation/pilot/review-codex/recalibration-completed-20261102/adjudication.json)
preserves these distinctions without changing trial packages.

## Practical next step

The proposed corrections to the real-data cases are already implemented in
[the worked analyses](../analyses/README.md), following Barry's separate
authorisation to Claude. They replace the earlier recommendation to commission
those corrections. Preserve the original experimental packages as observations
of agent behaviour; use the corrected derivatives as research outputs.

The [bounded final check](../analyses/review-codex-final-20261102.md) confirms
that the recorded independent review findings are addressed. Both full scripts
were executed in a scratch mirror using cached Python 3.12.13, NumPy 2.5.4
and SciPy 1.18.1; both reproduce their saved results byte for byte. The
[replay receipt](../analyses/review-codex-final-20261102.json) records hashes.
Checks include the added pairs bootstrap, 48 mixture starts, all histogram
observations and revised taxon inference. Two remaining prose details were
corrected: zero observations do not establish disappearance, and Salop's
adjusted p-value is displayed as 0.0501 to show which side of 0.05 it lies on.
Scripts, data and numerical results were unchanged during this review.

The useful result is that execution replay alone missed consequential
scientific errors. Review changed the allometry inference, the treatment of
taxon absence, and which conclusions survive repeated-record sensitivity.
Neither original analyst used the optional toolkit. These two observations
do not establish an adoption rate or identify why the API was declined.

Retain the validated API without requiring adoption. No new statistical
capability is selected by this round: the methods in the corrected scripts
are not automatically a library backlog. Select the next capability only
when a named research question establishes a recurring need that the current
tools do not meet reliably. No new analyst session is needed to close this
tranche.

The concrete unresolved issue in the current cases is Dielasma's primary
data provenance: were the repeated L2 measurements duplicated during data
entry? Until the source establishes that, retain the archived, block-removed
and unique-pair scenarios. Their differences must remain in the scientific
interpretation rather than be resolved by automatic deduplication.
