# Reconciliation of sprints 1 and 2

31 October 2026. Both counter-reviews and the reconciliation are complete.
This closes the approved two-sprint development programme, without a public
release, efficacy claim or new live evaluation trial.

Claude's original sprint-2 review accepted `e60729d` after its precommitted
25-case blind round passed on the first run. Codex's sprint-1 counter-review
and repairs are `0674118`. A fresh Claude Opus 5.5 session challenged that
patch; Codex resolved its findings at `59aeb77`. A second fresh Claude session
read the Board discussion and amended source, then accepted the reconciliation
in Board thread 102, **message 2706**, conditional on successful full final CI.
The [initial](../evaluation/review-2026-10-31/claude-reconciliation-initial.json)
and [final](../evaluation/review-2026-10-31/claude-reconciliation-final.json)
returns preserve the roles and checks. These reconciliation sessions are
distinct from the original reviewer and did not perform new blind validation.

The condition is satisfied: [full CI at `59aeb77`](https://github.com/BWBrook/palaeo-agent/actions/runs/41191815567)
passed **301 tests**, plus the offline corpus check. Codex confirmed this in
Board message **2707**. The final closeout adds documentation and receipts;
the reconciled implementation is unchanged.

## Accepted findings

- **Scientific capability:** one-way PERMANOVA, explicit design declarations,
  exact/Monte Carlo provenance and descriptive centroid dispersion are
  accepted for private development within the stated contract and numerical
  limits. The blind cases and independent vegan/PAST comparisons support the
  recorded calculations, not full PAST compatibility.
- **Historical evaluation:** all 28 sprint-1 and 12 sprint-2 outcomes stand.
  The smokes cannot establish error reduction: both arms answered correctly,
  items were small and partly coached, and actual toolkit invocation varied.
  Token/evidence differences are descriptive observations.
- **Scoring repair:** the prospective scorer enforces coherent stops and
  assumption-dependent answers; unresolved numerical completions stay
  provisional until adjudicated. Finite JSON validation and evidence path/text
  alignment are repaired. Numeric strings remain intentionally accepted under
  the documented contract. V1 scores and source remain preserved in Git.
- **Item repair:** D2 retains formal raw-count non-identifiability; integer
  percentages align the catalogue without proving difficulty. D7 now supplies
  the missing sampling-validity fact as `D7-control`, class `twin`, without
  trap-handling credit. The original D7 item was not in the smoke.
- **Execution boundary:** checkout/key protections worked, but credentials
  and some shared user state were exposed to worker tools. Synthetic probes
  confirmed both the protections and exposures. No exploitation was observed;
  absence of all leakage or contamination is not established.
- **Operational repair:** the exposed evaluation launcher is disabled before
  any worker setup or authentication copy. There is no unsafe override. Its
  automatic retry branch is removed, and offline plan creation cannot replace
  an existing plan. The analysis API and ordinary collaborator sessions remain
  available.
- **Numerical residual:** compensated sums repair the demonstrated high-F
  row-order defect, but mathematical ties reached through different distance
  multisets can still encounter the absolute tie-tolerance limit at extreme F.
  This is recorded, not declared resolved or categorically unrealistic.

No disagreements remain in the reconciliation. Agreement between Claude and
Codex is a development decision, not independent validation of all claims.
The individual reviews distinguish firsthand checks from reported evidence.

## Next programme

Restore a trustworthy evaluation boundary before spending tokens on more live
trials. A replacement must separate model-client credentials and shared user
state from worker tools, freeze and verify complete per-launch runtime
provenance, and pass expanded credential/state, key/context and arm-equivalence
preflights. The existing launcher stays disabled until that work is complete;
it is not treated as repaired isolation merely because launch is blocked.

Then build harder tasks that state scientific facts without supplying their
consequences, define whether the toolkit arm requires actual use, and freeze
an independently checked pilot. Reviewer-auditability and confirmatory
efficacy remain untested. The next programme should be bounded separately;
this reconciliation launches no larger pilot or new method tranche.

## Review records

- [Sprint-1 counter-review](sprint-1-review.md) and [receipts](../evaluation/review-2026-10-31/README.md).
- [Sprint-2 implementation/results](sprint-2-results.md) and [Claude's review](sprint-2-review.md).
- [Prospective offline instrument](../evaluation/revised/README.md).
- [Agreed sequence and authority](sprints-1-2.md).
