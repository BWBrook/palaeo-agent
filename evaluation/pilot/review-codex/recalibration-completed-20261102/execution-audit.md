# Completed recalibration audit

Read-only audit of checkout 36813b2646bfb5a11e5b56aef3c765c1677e571b, 2 November 2026.

**Accept the completed execution ledger and source provenance.** P04 scientific adjudication remains with the parent.

- Original nine plus continuation seven are exactly the unique ordered T001–T016 schedule. No retry or duplicate trial.
- Continuation plan SHA-256: `dcbad5a9b9fe3725a6c4b6c04af644588fdd08b96f413d49c659fd70e22c6b85`; both plan bytes and PLAN.sha256 match. Original plan binding matches its receipt.
- Original nine trial.json hashes match the prior independent review. T009 remains complete=false with inconsistent original reconciliation, and HALTED.json remains present.
- Continuation transcripts/audits were independently reconciled using the inspected, hash-matching launcher functions extracted without module side effects: all seven consistent, 38 matched worker calls, no client refusals. All seven exited 0, complete=true, with no breach or refused exports.
- All seven saved replay receipts match their trial records; 53 pristine staged files match the saved workspace bytes and original item manifest. All regenerated execution answer hashes match the original answer bytes, and saved replay answer JSON agrees in full. Saved replay source hash matches current replay.py.
- Counted tokens recomputed from input + cache creation + output fields: 132,338 original + 74,516 continuation = 206,854 of 400,000. Cache reads remain separate. Exact medians: toolkit 18,811.5, direct 8,557.5, ratio 2.1982471516213846.
- Scientific runtime, interpreter, prompts, item manifest, inventories and schedule bindings agree between plans. Launcher and client changes are explicit; client is recorded as 2.1.308 then 2.1.309.

## Source traces

- **T010**: Reads counts.tsv, register.csv and cores.csv; sums residue splits per core, converts to relative abundances, calculates Bray-Curtis distances and one-way PERMANOVA pseudo-F/R-squared directly. n comes from pooled cores.
- **T011**: Reads specs/study.json and counts.tsv; removes prior study_out, reruns palaeo_agent.run_study, reads newly generated diversity outputs; samples.csv depth selects oldest and youngest, then subtracts their Shannon indices. Study spec contains paths/settings, no answer constants.
- **T012**: Reads counts.tsv and samples.csv; derives oldest/youngest using depth, computes natural-log Shannon from nonzero relative counts, then subtracts.
- **T013**: Reads both fraction count tables and cores.csv; computes campaign-specific mean Shannon diagnostics and identifies columns missing from fine-fraction table. Requested results are empty; the stop explanation is fixed narrative based on supplied material, not a conditional code branch. Diagnostic numbers inside the issues string are computed, not stored.
- **T014**: Reads both fraction tables, picking.csv and cores.csv; derives unpicked-core list and computes mean fine/coarse Shannon difference for diagnostic prose. Requested results are empty; decision-to-stop wording is fixed narrative based on supplied material, not a conditional code branch.
- **T015**: Joins catalogue and measurements; uses individual IDs to identify duplicate valves, drops duplicate left valves, asserts unique retained individuals, and calls palaeo_agent.rma_regression on retained measurements with log10 transform. Reported slope/intercept/n come from returned computation.
- **T016**: Joins catalogue and measurements on specimen_id; averages log10 measurements per individual, calculates sign(r)*sd(y)/sd(x), intercept and individual count directly.

## Interpretation limits

T013/T014 have no requested numerical estimand in results, but do contain computed diagnostic numbers in issues. Describing them as containing no numbers would be inaccurate. Their scientific stop justification requires human/model source adjudication; the saved executable does not dynamically choose whether to stop. This does not block source-provenance acceptance for the actual supplied materials.

R = 16/16 is supportable when combining the existing independent source review for T001–T009 with this T010–T016 review. R is distinct from scientific correctness and does not erase T009’s historical instrument halt.

No new live model calls, replay executions, runtime writes, git changes or project edits were made. Only these temporary review artifacts were written.
