# Sprint 3–4 closeout evidence check

Codex, 1 November 2026; reviewed `0c3e106`. Offline verification only, with
the existing qualified toolkit Python. No live model call or credential use.
The evidence supports closing the development sprints with the pilot unrun.

- The archive contains **21 attempted records: 20 executed, 19 complete,
  one executed but incomplete after the configuration post-check, and one
  preflight halt without a client transcript**. Keep these counts distinct.
- All 20 executed transcripts re-reconcile against `launch.reconcile` and
  match their saved reconciliation: **149 audited worker calls and six client
  refusals**, no discrepancies. Integration totals **48,884** counted tokens;
  calibration totals **124,840**. The longest integration attempt with a
  completed timestamp lasted **62.48 seconds**, safely below 300 seconds.
- **535 archived run files match their original bytes** under
  `~/palaeo-eval/`, including plans and `.out` files originally held beside
  the run directories. The archive contains no symbolic links or special
  files. Retained scratch copies were not compared with their former source
  directories; the removed keychain link is an explicitly recorded exception.
- The refreshed supervisor receipt matches all current source, prompt,
  qualification-script, runtime-tree, base-interpreter, client and pilot-item
  manifest hashes. Its five recorded qualification checks pass. This review
  verifies the receipt and its bindings; it does not repeat subscription
  authentication or endpoint qualification.
- Every archived bundle was independently inspected and reproduced:
  **11 studies and nine runs**. These are bundle counts, not independent
  trial counts: some runs are nested inside studies. Four studies are complete
  and seven partial. Reproducing a partial study preserves its refusal history;
  it is not evidence of a successful complete analysis. All nine numerical
  run comparisons pass, and every study's derived files match byte for byte.
- Run environment equality is false only because the current platform string
  is `macOS-27.2-arm64-arm-64bit` rather than the recorded
  `macOS-27.2-arm64-64bit`. Python, package versions and source hashes match.
  This is successful numerical reproduction, not a claim that every
  environment descriptor is identical.
- All eight direct calibration workspaces contain source materials and
  `answer.json`, with no saved analysis script. Seven of eight toolkit
  workspaces contain run or study bundles; T013/P04 contains neither. This
  substantiates the package-contract concern. Presence of a bundle alone is
  not a full answer-to-bundle provenance check.

## Wording and interpretation

Two small corrections would improve the reconciliation: use "about 63 s" or
"62.48 s", rather than "no integration trial passed 62 s"; and describe the
three reproduced integration studies as one complete and two partial, rather
than implying three complete successful analyses. Neither changes closeout.

"The boundary held" should remain scoped to the observed calls and explicit
probes. Successful replay of the audited calls is not proof against every
possible confinement attack. The implemented gates and earlier adversarial
tests remain the relevant separate evidence.

The check script and machine-readable receipt accompany this report. They
preserve per-trial counts, replay results, archive-source comparisons,
qualification hash checks and per-bundle reproduction results.
