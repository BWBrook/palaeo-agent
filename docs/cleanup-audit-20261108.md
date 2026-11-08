# Clean-up and correctness audit, 8 November 2026

Claude (Opus 5.5), with a first-pass engine review and a test-portfolio
inventory by Codex (`gpt-6.1-sol`, read-only, through `codex-delegate`).
Barry asked for a pass over hidden correctness risks: implicit state
machines, invariants relied on but not enforced, and assumptions about
ordering, timing, concurrency and atomicity. The test suite was to be treated
as a portfolio of evidence.

## The state model, as audited

Every bundle type (run, study, comparison, Neotoma extraction) follows the
same lifecycle. It writes into a fresh directory, writes `manifest.json`
last, and is complete only if inspection verifies that manifest. That design
is sound. A crash at any point leaves no manifest, or a truncated one that
cannot parse, so no partial bundle can verify. Directories are UUID-named
with `exist_ok=False`, so concurrent writers never share one.

The defects were in what inspection did *not* bind to the manifest, and in
operations that could write into evidence they had just verified.

## Defects fixed

| # | Defect | Failure it allowed | Fix |
| --- | --- | --- | --- |
| 1 | Run inspection hashed the CSV tables and the permutation/randomization records but never checked them against `results.json` (two JSON records were compared; every CSV was trusted). | A rehashed edit to `taxon_tests.csv`, `permanova.csv` or any other table verified, although agents and people read those tables. | `methods.table_files(result)` is now a pure function returning every table as bytes. `run` writes it; `inspect_run` compares it byte for byte. |
| 2 | Run inspection checked the manifest's steps only for internal coherence. | A rehashed extra file with a self-declared producing step verified. | The manifest's steps must equal `steps_for(spec, lockfile)`, which fixes the file set exactly. |
| 3 | The implementation fingerprint and `uv.lock` were read from disk when each run happened. | A long-lived process (the MCP server) whose source was edited afterwards recorded code it had not run. | Both are captured once, at package import. |
| 4 | `reproduce`, `study_reproduce`, `neotoma_reproduce` and `compare` accepted an output root inside a bundle they read. | The new directory became part of the original bundle, which then failed inspection permanently. | `require_outside` refuses this (`output_inside_bundle`). |
| 5 | `reproduce` did not check that the rerun used the same input bytes. | A concurrent change to the snapshot between inspection and rerun could be reported as `reproduced`. | Input fingerprints are compared; a difference is reported. |
| 6 | Study `report.md` was hashed but never recomputed. | A rehashed edit to the report verified. | `inspect_study` recomputes the report from the verified records. |
| 7 | Study IDs allowed `.` and `..`, and they become path components. | Analysis ID `..` wrote its run into the study root. | IDs may not start with a dot. |
| 8 | Derived PAST tables were written without checking they read back. | A delimited label holding a tab or a Unicode line separator broke the derived table and produced a misleading downstream refusal. | The derived table must parse back to the same table; otherwise `unsupported_label`. |
| 9 | (Codex PA-02) A child run that failed while writing left its directory. | The partial study failed its own inspection. | The incomplete child directory is removed; the error stays in the step record. |
| 10 | (PA-03) Inspection ignored unmanifested files under `runs/`. | `runs/<id>/notes.txt` verified. | `runs/` must hold exactly `runs/<analysis>/<run id>` for completed analyses. |
| 11 | (PA-04) The study manifest's version and keys were never checked. | A manifest from another schema was read with current semantics. | Exact keys and `study_version == 1` are required. |
| 12 | (PA-05) A child bundle with metadata passed when its dataset declared none. | Contradictory provenance verified. | Metadata presence must agree. |
| 13 | (PA-06) Row-filter warnings matched RMA columns exactly; RMA itself also accepts a uniquely padded label. | An exclusion removing complete pairs in a padded column gave no warning. | Both use `core.resolve_columns`. |
| 14 | (PA-07) Rarefaction and the exact study sum used `localcontext()`, which inherits the caller's decimal settings. | A caller's precision, rounding or traps could change or crash a result. | `core.decimal_context` builds a fully specified context. |
| 15 | (PA-08) Study inspection read files again after hashing them. | Bytes that were never hashed could be the ones parsed. | Each file is read once and used from memory. |
| 16 | `reproduce_study` compared only the overall status. | Two partial studies that failed at different steps were reported as `reproduced`. | Step outcomes (ID, status, error code) are compared. |

Also removed: an unused relative-abundance array computed in every
community analysis.

**Declined.** Codex PA-01 showed that a rehashed `results.json` with permuted
coordinates and Gram axes still passes inspection. Inspection deliberately
does not recompute numerical results (it may not run eigensystems, by
design); `reproduce` catches this. The boundary is unchanged, and the primer
now says that inspection checks tables against the saved result.

## Test portfolio

- **Added (14 cases in 9 tests), each for a distinct failure mode above.**
  Twelve fail on the pre-audit engine. The other two are earlier coverage
  folded into the new parametrisations.
- **Removed, after checking each claim:**
  - three controller lifecycle tests that mock around a launcher that is now
    permanently held (`evaluation/harness/trial.py` refuses on entry);
  - two zero-F PERMANOVA checks already covered by the parametrised vegan
    comparison;
  - a pilot-v4 perturbation check subsumed by the full rebuild;
  - a relative-abundance smoke test subsumed by the sensitivity comparison;
  - a "tampered envelope" test that never rehashed, and so tested only the
    checksum;
  - a literal inventory-length test;
  - a direct MCP schema test duplicated by the live stdio test.
- **Upgraded:** two tamper tests that edited a file without rehashing it now
  rehash, so they exercise semantic checks rather than the checksum.
- **Suite:** 809 → 780 passing (11 skipped). Most of the fall is the
  perturbation test, parametrised over every pilot key.
- **Left for the next round:** the sprint-named files (`test_sprint9` to
  `test_sprint12`, `test_sprint2_items`) should be dissolved into their
  subject files, following Codex's inventory.

## Replays

The Tasmanian surface, Lake Selina (both designs, study check, extraction
check, final amendment) and pollen-media applications all replay. No
scientific value changed. The committed Tasmanian and pollen-media records
change only in the primer hash, which moved because the primer's inspection
sentence changed.

## Remaining risks

- **Inspection is not reproduction.** A coordinated, internally consistent
  rewrite of `results.json` is caught only by `reproduce`.
- **Plots are hash-checked only.** Matplotlib output is not byte-stable
  across versions, so diagnostics are not re-derived.
- **Failed study steps' error records are not recomputed.** Only the status
  sequence is checked.
- **MCP root confinement resolves each path once.** A symbolic link swapped
  afterwards is outside the local trust model.
- **Manifests are written in place, not by atomic rename.** This fails
  closed: an interrupted write leaves a bundle that does not verify.
- **No dedicated tests** cover the metadata-presence check (12) or the
  step-outcome comparison (16). Both are single comparisons, and building
  their fixtures would cost more than they protect.
