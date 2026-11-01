# Sprint 5 gate review and repairs

Codex (GPT-6 Astra), 1 November 2026. Reviewed `799e0de`, including the plan
revision `baa3efa` and implementation `b9c9a6f`. **The gate remains withheld:
P04 and P09 do not yet support their scoring rules, and Linux bank
regeneration fails.** The review also found
and repaired concrete replay and parser defects. No live analyst or reviewer
trials ran during this review.

Barry's additional calibration approval, quoted by Claude in Board message
2787, remains in force: “Extra calibration round is approved, if you still
deem it required.” There is no new permission request. The outstanding
condition is this gate on the instrument, followed by final qualification.

## Independent scientific review

Two fresh reviewers received 16 anonymised materials-only dossiers each, with
no keys, builder, author-selected analysis recipe or previous reviews. They
sealed their findings before the parent mapped packet IDs to bank items.
The packet map binds every supplied file by SHA-256. These reviews test
scientific sufficiency; they are distinct from implementation witnesses.

- [Materials A](../evaluation/pilot/review-codex/sprint-5-gate/materials-a/report.sealed.md),
  sealed report SHA-256 `5155106a39cfa7f7204b2e732245c62ff866f427f8575b71429e278f8ed69e99`.
- [Materials B](../evaluation/pilot/review-codex/sprint-5-gate/materials-b/review.md),
  sealed report SHA-256 `d4350d5d482c8568c4c460acc276ce1c9489f3823651cba9783b3b3b54951833`.

### P04: coverage evidence and target are insufficient

The trap and calibration dossiers give sieve mesh and **adult** taxon size
from an atlas. They do not give size/stage distributions of counted specimens
or establish complete, comparable coverage of every retained taxon. An adult
size category does not logically determine the retention of every specimen.
The task also asks generically for mean Shannon diversity by campaign,
without specifying the common-coverage estimand.

For the pilot trap, the observed-table means are 2.513702941670762 and
2.9814890300038996. Restricting to the large-adult taxa instead gives
2.513702941670762 and 2.5685220808024063. Both are calculable descriptive
quantities with different qualifications; only the second is keyed. In the
calibration dossier, restriction reverses the sign of the observed campaign
difference. Neither treatment establishes temporal causation across different
sites and sampling protocols.

**Required repair:** make the intended comparable target explicit and provide
the sample-specific fraction/retention facts that identify it, or broaden
adjudication to the estimands actually supported by the current materials.
Prefer the former: preserve the intended common-coverage question with
sufficient neutral source records. Do not replace missing coverage evidence
with an assumption hidden in the key. Retain the justified-stop alternative.
The earlier v3 coverage repair must survive the move to less signposted
dossiers.

### P09: valid individual-level analyses score wrong

The task requires one value per individual but does not select a valve or
aggregation rule. The new generator gives paired valves different measured
values, while the scorer accepts only globally right, globally left and
arithmetic-mean policies.

An independent calculation selecting the first measured valve per individual
has no duplicated individuals, yet scores `wrong`:

| Item | Slope | Intercept | n |
| --- | ---: | ---: | ---: |
| P09-trap | 1.0287744701466837 | −0.13566720110416375 | 52 |
| P09-cal | 1.033514519203255 | −0.13720125062653632 | 49 |

Five ordinary fixed policies failed the pilot key; three failed calibration.
The materials-only reviewer independently identified the unspecified
aggregation before seeing these counterexamples.

**Required repair:** define an individual measurement estimand in the task,
or make paired measurements equivalent by design. If multiple procedures
remain intended, use procedural adjudication and independent recomputation
for the declared rule. Adding more enumerated numerical alternatives does
not resolve the general problem. Rebuild pilot and calibration together.

### Additional scientific clarifications

- **P06:** pooled counted-material composition and an equal average of split
  proportions are different estimands. For the pilot trap their pseudo-F
  values are 16.077416143583 and 11.823715400445048. State which population or
  finite counted assemblage the task targets, and the split sampling facts
  needed for any alternative weighting. Do not call these interchangeable
  implementations merely because both use 14 independent cores.
- **P12:** pseudo-F and R² are computable descriptive statistics. The task's
  “Test whether” wording should not imply that a significance test is
  justified by the single-core biozone records. Make the descriptive scope
  explicit; do not invent exchangeability or claim the statistics themselves
  are uncomputable.
- The remaining materials support the intended numerical handling under the
  qualifications recorded in the sealed reviews. The percentage dossiers
  reconstruct uniquely to integer counts under their stated denominators and
  ordinary rounding assumptions; low yields, unobserved taxa and surplus
  metadata are not automatic grounds for exclusions.

All **32 recorded implementation-witness outputs match current keys**, with
maximum absolute discrepancy 1.07e−14. Separately, all **12 reviewer-flaw
references** were recomputed independently from the written data, with maximum
discrepancy 1.42e−14. Those arithmetic checks cannot establish that a keyed
handling is uniquely warranted.

## Replay repairs

The [replay review](../evaluation/pilot/review-codex/sprint-5-gate/replay/report.md)
retains the original and repaired counterexamples. The original worker denied
an external synthetic JSON read, but the supervisor then followed the
worker's `answer.json` symlink and exposed the canary in its comparison.
Only synthetic files were used.

Repaired behavior:

- bounded, non-following regular-file reads reject links, shared hardlinks,
  FIFOs, oversized answers, invalid JSON and malformed answer contracts;
- shared answer validation and recursive result comparison preserve arrays,
  exact integer fields, status, conclusions, assumptions and exclusions;
- each attempt retains worker audits, staged hashes, validated regenerated
  answers and execution receipts outside the worker;
- infrastructure failure in either execution halts launches, and unexpected
  replay exceptions preserve the trial's usage and failure record before
  halting.

The perturbation check is now **diagnostic only**. It falsely called a real
calculation static when that calculation wrongly excluded the changed sample,
and it accepted a stored requested answer accompanied by one changing extra
field. A mechanical replay pass therefore carries
`provenance_review_required: true`. Final R requires attributed
source/specification/provenance adjudication that the result was actually
computed from supplied materials. Confirmed stored-answer code is excluded;
wrong-but-genuinely-recomputed analyses remain reproducible. Pending verdicts
cannot be silently treated as final R.

The operative protocol and proposal now state this rule, distinguish E from
E*, and judge toolkit adherence from scripts, field mappings and bundle
provenance. A compliant Python-API call inside `worker_execute` need not
produce a `palaeo_run` MCP event. A bare import is not adherence evidence.

## Toolkit repairs

The [toolkit review](../evaluation/pilot/review-codex/sprint-5-gate/toolkit/report.md)
records three new parser failures and their repairs:

- missing-value conversion no longer renames identifiers or manufactures a
  dot identifier for a missing label;
- malformed quotes and delimiter-only records are rejected rather than
  accepted or discarded;
- RMA reads spaced labels in derived tab-separated study tables.

The initial complete native test run caught an additional established PAST
contract: trailing header padding must not change a requested column's
identity. This regression was repaired without changing the sealed blind
fixture. Literal names and ambiguous column selections are tested explicitly.

Compact MCP schemas retain full server validation and discoverable method
schemas. Payload reduction remains an engineering measurement; no new K or
live cost advantage is claimed.

## Verification and remaining release conditions

The repaired toolkit was built into
`/Users/bwbrook/palaeo-eval/pilot-runtime-v4-review-20261101c`, preserving the
earlier runtimes. **The final native suite passed 475 tests with zero skips**
in 90.10 seconds. The final runtime passes **29 worker probes per arm** and
**all four client-boundary cases** against the local scripted endpoint.
One earlier concurrent probe hit the three-second figure-rendering limit;
that receipt is retained, and the complete worker qualification passed when
rerun without the concurrent suite. No live model endpoint was used.

The review runtime's wheel SHA-256 is
`a3febf7c1021baaa7ebfb593fba5324526f4b8a418a399684c85c0935941b86d`.
Native evidence, final source/runtime fingerprints and test totals are saved
with the review. Supervisor instruction/authentication qualification against
the eventual bank freeze remains a release condition, not a claim made by
these worker/client probes.

**Linux CI is not green.** The reviewed commit's
[run](https://github.com/BWBrook/palaeo-agent/actions/runs/41275862734) already
failed `test_pilot_bank_v4.py::test_rebuild_is_identical`. The repaired code's
[run](https://github.com/BWBrook/palaeo-agent/actions/runs/41285966892) reports
466 passed, eight native-only skips and the same sole failure. Regeneration
changes the hash of `items-v4/P09-trap/key.json` from `dba1d2e5…` to
`61ae7dc9…` on Linux; the differing field values are not exposed in these CI
logs, so the cause is not established here. Resolve the bank's cross-platform
regeneration contract during its scientific repair. Do not weaken the check
or call the complete cross-platform gate passed based on the native result.

Before recalibration, Claude should repair the bank definitions above, rebuild
their keys, alternatives and calibration twins, and return the changed
materials for fresh sufficiency and numerical checks. Then refresh the actual
runtime, probes, supervisor qualification, prompts, source and material
fingerprints together. Existing receipts must not be presented as a freeze
of later bytes. The approved round remains at most 16 trials and 400,000
counted tokens, with the agreed wall limit and no automatic extra round.

Before reviewer trials, qualify the actual paired package modifications and
downstream regeneration: frozen flawed numbers plus answer edits are not an
executable planted error. Interpretation flaws must really be false of the
chosen package, including any extra analyses the analyst performed. Record
unplantable pairs and apply the existing exclusion rule.

**Claude is next** for the scientific bank repair and subsequent gate
response. The current bank has not passed, and no live recalibration is
approved for these unrepaired materials.
