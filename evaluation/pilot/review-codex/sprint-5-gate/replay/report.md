# Sprint-5 replay audit and repairs

Codex, 1 November 2026. Reviewed `799e0de`; original replay SHA-256
`c3aafc200d689056febca29b94955ad267ea5375d8b4b42f81bc7daddb3fe68e`.
All checks were offline. Native cases used the existing v4 arm runtime and
macOS confined worker; no model requests or real secret files were used.

## Findings reproduced before repair

1. **Supervisor followed an answer symlink out of confinement.** A worker
   script first attempted to read a synthetic external JSON canary and was
   correctly denied. It then made `answer.json` a symlink to that file. The
   supervisor's `load()` followed it and returned the private canary number
   `918273` in a mismatch record. The same unbounded `read_text()` also lacked
   a regular-file check, so a FIFO or oversized file was an unsafe input.
2. **Replay did not validate or reproduce the answer contract.** Changed
   conclusions and exclusions still counted as `replayed`. Two empty objects
   also counted as successful non-numerical reproduction, and different arrays
   under `results` were ignored because only scalar numbers were compared.
3. **A perturbation was misinterpreted as proof of static code.** A script
   genuinely recomputing from the data, but wrongly excluding the changed
   sample, was called `static`. That contradicts the stated separation of
   scientific correctness from reproducibility. Conversely, a fixed requested
   answer with an extra data-dependent field passed the check. A mutation that
   invalidates a task's assumptions is not a scientific counterfactual witness.
4. **Second-run failure handling was incomplete.** Both an ordinary script
   failure and an injected worker-infrastructure failure during perturbation
   were discarded, with the package still labelled `replayed`. The latter
   should halt the launcher under the agreed infrastructure rule.
5. **Replay evidence was deleted.** Both worker audits and regenerated
   answers lived only in `TemporaryDirectory`; the surviving summary could
   not establish what the reruns actually produced.

The original and repaired counterexample receipts are saved separately.
The second-run infrastructure case is a targeted fault injection; the file
boundary, script outcomes and other replay cases execute the real confined
worker.

## Repairs made

- `replay.py` opens answer files with `O_NOFOLLOW | O_NONBLOCK`, then requires
  a regular, singly-linked file and a maximum of 1 MiB. A link, special file,
  oversize file, duplicate-key JSON, non-finite JSON or invalid answer contract
  cannot enter the comparison or the saved answer evidence. Package files are
  also read without following links, with a five-million-byte per-file bound.
- The existing answer-contract validation was extracted as the pure
  `validate_answer()` function in `evaluation/revised/score.py`, used by its
  existing loader and by replay. Scorer semantics are unchanged.
- Replay compares the complete structured non-result claims exactly and all
  result structures recursively. Dict fields and list sizes must match;
  numerical tolerances apply to values, with integer fields exact. Changed
  refusals, exclusions or conclusions cannot pass merely by retaining a
  status label.
- The parent adopted **diagnostic-only perturbations**. A pristine match is a
  replay candidate with `provenance_review_required: true`; perturbation
  `changed`, `unchanged`, `failed` or non-applicability does not establish or
  refute data dependence. Wrong but recomputable analyses retain their replay
  result. A genuine literal-answer script must be identified in the separate
  source/specification/provenance review before final R classification.
- Worker-infrastructure failure in either execution produces `infrastructure`;
  a normal perturbation script failure is retained as a diagnostic, separately
  from the successful pristine match.
- Each offline replay gets a new supervisor-owned
  `record/replay/attempt-*` directory. It keeps staged file hashes, both worker
  audits, bounded execution receipts, validated regenerated answers, a final
  receipt and the replay-source hash. Arbitrary generated files are not
  exported; unsafe answer bytes are never saved. The temporary working
  directory can be removed without deleting this evidence.

## Verification

**25 focused tests passed in 3.81 s**, with native tests enabled:

`PALAEONATIVE_BOUNDARY_TESTS=1 uv run --offline pytest -q tests/test_pilot_replay.py tests/test_evaluation_revised.py tests/test_pilot_score.py`

This covers real direct/toolkit replay, retained evidence, refusal and claim
comparison, recursive values and integer fields, safe answer reading and
infrastructure classification. The existing toolkit replay fixture now uses
its own actual summary text rather than borrowing a numerically identical
direct answer with different prose.

| Counterexample | Original | Repaired |
| --- | --- | --- |
| Honest computation | replayed | replayed, provenance pending |
| Wrong analysis that genuinely recomputes | static | replayed, unchanged diagnostic, provenance pending |
| Changed claims/exclusions | replayed | mismatch |
| Empty invalid answer | replayed | no_answer |
| Different array values | replayed | mismatch |
| Static requested value plus dynamic extra | replayed | candidate only; provenance review required |
| Perturbed script fails | replayed with weak note | replayed candidate with failed diagnostic and retained evidence |
| Answer symlink to external canary | canary leaked in mismatch output | failed, without canary disclosure |
| Perturbed infrastructure failure | replayed | infrastructure |

`git diff --check` passed for the three edited implementation/test files.
The parent owns the final integrated native suite and protocol changes.

## Remaining integration requirement

The revised prompt makes legitimate toolkit calls from Python inside
`analysis.py`. Those library calls do not appear as MCP `palaeo_run` or
`palaeo_study_run` events: the worker audit records `worker_execute`/replay.
The old protocol's MCP-call-only adherence wording therefore cannot establish
use under this contract. The parent is updating it to source and bundle-field
provenance review. This audit does not claim automated adherence proof.
