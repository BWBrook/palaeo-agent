# Original run records: integration and calibration, 1 November 2026

These are the full, unedited records of every live trial so far: plans, run
logs, halt files, per-trial `started.json`, `trial.json`, transcripts, stderr,
worker audits (`calls.jsonl`, `pids.jsonl`, `tools.json`, profiles), inventory
captures and exported workspaces. They were copied from `~/palaeo-eval/` on
the MacBook. No identity, credential or user-instruction text appears in them;
this was checked by grep before commit. The summaries in
`../integration-evidence/` and `../calibration-evidence/` are derived from
these records.

| Run | Trials | What happened |
| --- | --- | --- |
| `pilot-integration-20261101` | T001 complete; T002 preflight halt | T002 never launched a client. The configuration check halted on newly fetched organisation-managed files. Scratch: `scratch-retained/pilot-ics6ks00`. |
| `pilot-integration-20261101b` | T002 executed and reconciled, marked incomplete | The model ran and the answer scored correct. A post-trial configuration check flagged new signature sidecars, so the ledger counts the trial as incomplete. Scratch: `scratch-retained/pilot-x0pqfgtg` (its keychain link was removed before commit). |
| `pilot-integration-20261101c` | T001, T002 complete | |
| `pilot-calibration-20261101` | T001–T016 complete | |
| `recalibration-v4-20261101` | T001–T008 complete; T009 executed, halted | The run halted at T009 because the client re-serialised the integer 2^64−1 as a double. T010–T016 were not launched. See `docs/recalibration-v4.md`. |
| `recalibration-v4-continuation-20261102` | T010–T016 complete | Codex's continuation plan (`plan.json`, sha256 dcbad5a9…), on client 2.1.309 (the original run used 2.1.308) and the repaired launcher. See `docs/recalibration-v4.md`. |

## Recorded deviations from the agreed limits

The plans configured some limits above the agreed values. These launches also
came before Codex's independent closure review of the b69fd10 fixes. Both are
deviations, recorded here, not described as strict adherence.

| Stage | Agreed | Configured | Observed |
| --- | --- | --- | --- |
| Integration, per-trial wall clock | 300 s | 600 s | All exited normally; the longest took 62.48 s including preflight. |
| Integration, counted-token ceiling | 200,000 | 400,000 per plan | 48,884 counted in total. |
| Calibration, counted-token ceiling | 600,000 | 1,000,000 | 124,840 counted in total. |

Observed usage stayed below every agreed limit, so no stop the agreed values
would have triggered was missed. Two other changes came between runs, after
integration and before calibration, as recorded in the integration README:
the organisation-managed file gate and the prompts' exact tool names.
