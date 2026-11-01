You are an independent scientific reviewer. Do not edit any file. Read-only.

Two AI analyst sessions each answered an open palaeontological research brief and delivered a package. Review each package as a referee would, using only the files listed. Do not consult other files in the repository and do not use the web.

Session A1 (Coed Duon Llanvirn shelly fauna), directory evaluation/authentic/run-records/authentic-20261101/sessions/A1/:
- brief: evaluation/authentic/cases/llanvirn/brief.md
- workspace/provenance.md, workspace/llanvirn.dat (the data the analyst received)
- workspace/analysis.py, workspace/results.json, workspace/report.md (the delivered package)

Session A2 (Permian brachiopod Dielasma), directory evaluation/authentic/run-records/authentic-20261101/sessions/A2/:
- brief: evaluation/authentic/cases/dielasma/brief.md
- workspace/provenance.md, workspace/dielasma.dat
- workspace/analysis.py, workspace/results.json, workspace/report.md

For each session:
1. Trace every substantive numerical or inferential claim in report.md to results.json and to the code in analysis.py that produces it. You may recompute values yourself in Python from the data to check them (read-only; do not write files in the repository; use a temporary directory if you must write).
2. Report each claim that is untraceable (no value in results.json or no code producing it), numerically wrong, mislabelled (e.g. wrong row numbers, wrong taxon names, wrong statistic name), overstated relative to its evidence, or an inference the data cannot support. Also report statistical method errors (e.g. invalid test, wrong null, multiplicity ignored where it matters, resampling procedure that does not estimate what is claimed).
3. Report anything in the data the analyst missed that would change a conclusion.
4. Note facts the analyst asserted that are not in the provided materials (e.g. expanding an abbreviated genus name), and whether the assertion is flagged as such.

Use kind values: wrong_value, untraceable, mislabelled, overstated, unsupported_inference, method_error, missed_data_issue, unflagged_external_fact, other. Use severity: major (changes a main conclusion), minor (does not change a main conclusion but should be corrected), note. Use "uncertain" in verdict_confidence when you could not check something. Give the exact location (report section or results.json key or analysis.py line). Keep each statement to one or two sentences and put your evidence (recomputed numbers, line references) in evidence.

Also give, for each session, one overall item with kind "other", severity "note", whose statement is your overall verdict: can the main claims be traced from the package, and are the main conclusions sound?
