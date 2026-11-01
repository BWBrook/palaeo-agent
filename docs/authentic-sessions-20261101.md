# Authentic-workflow sessions: Llanvirn and Dielasma

Claude (Opus 5.5), 1 November 2026. Barry approved two small real-data sessions
with optional toolkit use (Claude Code chat, 1 November 2026: "Approved."),
following Codex's proposal in [research-workflow-next-step.md](research-workflow-next-step.md).
Harness: `evaluation/authentic/` (commit b70c14d). Records:
`evaluation/authentic/run-records/authentic-20261101/`. Independent review:
Codex `gpt-6.1-sol`, read-only, from the packages and data alone
(`review-codex.json` beside the records).

## Conditions, fixed before launch

- **Analyst:** `claude-sonnet-5-5` under the frozen pilot supervisor and
  runtime (`pilot-runtime-v4-freeze-20261101`, toolkit arm), with every pilot
  safeguard: fingerprints, config-directory checks, inventory capture,
  init-record check, worker reconciliation, link-refusing export.
- **Workspace:** the original archived data file and a factual provenance and
  stratigraphy note. No tutorial text, suggested answers, benchmarks or toolkit
  documentation beyond what the toolkit's own discovery tool returns.
- **Prompt:** `contract.md` (deliver `analysis.py`, `results.json`,
  `report.md`), one sentence offering the toolkit as optional (`toolkit.md`),
  and the brief. Briefs are in `evaluation/authentic/cases/*/brief.md`; the
  Llanvirn brief is Codex's text verbatim.
- **Limits:** 80 turns, 1,800 s, 150,000 counted tokens for the batch with
  launch-stop.
- **Plan:** A1 Llanvirn and A2 Dielasma with the toolkit offered. A3 and A4,
  toolkit-free twins, were run only if a named decision depended on them.
- **After each session:** one neutral retrospective question, asked by resuming
  the session with no tool permitted; then a replay of `analysis.py` in a fresh
  confined worker from pristine data, comparing `results.json`.

## What happened

| | A1 Llanvirn | A2 Dielasma |
| --- | --- | --- |
| Outcome | complete, no breach, reconciliation consistent | same |
| Turns / wall time | 7 / 72 s | 7 / 64 s |
| Counted tokens, session + retrospective | 30,636 + 18,207 | 24,431 + 17,652 |
| Worker calls | 5 execute, 1 write | 4 execute, 1 read, 1 write |
| Toolkit calls | **0** (never ran `palaeo_discover`) | **0** (never ran `palaeo_discover`) |
| `analysis.py` | 88 lines: numpy, pandas, scipy | 113 lines: numpy, pandas, scipy |
| Replay | replayed, byte-identical `results.json` | replayed, byte-identical |
| Provenance review (Claude) | computes everything from `llanvirn.dat`; no stored answers | computes everything from `dielasma.dat`; no stored answers |

Total 90,926 counted tokens, of 150,000. A3 and A4 were not run (see below).

**Retrospectives (self-report, separate from the observed actions above).** Both
analysts said they never looked at the toolkit and defaulted to writing the
calculations themselves "to keep every step visible" in `analysis.py`. Both
noted that the worker blocks subprocesses, so they ran the script with `exec`
rather than as `python analysis.py`. The replay showed the scripts do run
standalone. A2 named statsmodels and scikit-learn as missing; A1 named
scikit-bio and vegan-style packages.

## The science, as delivered and as reviewed

**A1, Llanvirn.**
- The answer is substantive and well hedged:
  - 5→6 is the largest compositional step: proportional Bray–Curtis 0.67, *Sowerbyella* 0.89→0.27, `Basil` 0.006→0.47.
  - 6→7, across the unconformity, is also large (0.56) but rests on 26 specimens.
  - Horizons 7–10 are more even and small.
  - Which of the two steps is larger depends on the abundance representation.
  - Cause, rate and representativeness cannot be established.
- Methods it chose unprompted:
  - analytic rarefaction;
  - five abundance representations;
  - multinomial bootstrap and pooled-composition null tests;
  - per-taxon Fisher tests with Bonferroni correction;
  - Wilson intervals;
  - PCoA.
- **Review (Sol):** main numbers traceable and reproduced; main conclusions
  sound under the stated specimen-sampling model. Nine minor issues:
  - "5→6 is abundance, not membership" is overstated: 5 taxa gained and 4 lost.
  - Two taxa are mislisted as 6→7 losses.
  - The log(count+1) comparison confounds representation with unequal totals.
    After standardising totals, 5→6 again exceeds 6→7.
  - One count is wrong (48 for 51).
  - The bootstrap cannot represent unseen taxa.
  - `Basil` = *Basilicus*, a trilobite, is asserted without flagging that it
    is outside knowledge.
  - One unused output is mislabelled.

**A2, Dielasma.**
- Log-log RMA slopes of width on length (bootstrap CIs):
  - L1 1.018 (0.990–1.050);
  - L2 0.982 (0.952–1.015);
  - L3 1.107 (1.008–1.286).
- Its reading: near-isometry in L1 and L2, inconclusive in L3. Clear
  size-structure differences, with L3 small and unimodal. Shape differs only
  weakly. Populations, environment and taxonomy are appropriately not inferred.
- Methods it chose unprompted:
  - RMA and OLS with bootstrap;
  - an ANCOVA slope-homogeneity and elevation test;
  - Kruskal–Wallis, Mann–Whitney and KS tests;
  - a permutation multivariate test;
  - a curvature test;
  - a two-Gaussian mixture compared by BIC.
- **It found a defect in the archived data:** a block of six or seven
  consecutive L2 specimens is repeated exactly.
  - Rows 58–63 repeat at rows 65–70; 7.00/6.00 also occurs at rows 57, 64
    and 71.
  - The session reported it, flagged it for checking against the source, and
    ran a sensitivity analysis without the repeats.
  - None of us had noticed it. The tranche-1 L2 RMA benchmark
    (`benchmarks/past/dielasma-l2-run`) uses all 79 rows, block included, and
    the toolkit has no check that would flag it.
- **Review (Sol):** main numbers traceable and accurate. Issues:
  - The headline "probably isometric in L3" conflicts with the RMA interval,
    which excludes 1.
  - The slope-homogeneity test compares OLS slopes, not the reported RMA slopes.
  - The pairwise ANCOVA p-values are unadjusted. L1–L3 does not survive the
    Bonferroni correction applied elsewhere.
  - **Most material:** with the repeats removed, the L1–L2 length difference is
    no longer significant (adjusted p 0.072 against 0.014). The session's
    sensitivity analysis rechecked only the omnibus tests and said the
    conclusions held.

Neither package contains an error that changes its main answer. Every reviewed
issue is the kind a careful referee raises: multiplicity applied
inconsistently, an estimator mismatch, a headline slightly stronger than its
evidence, a sensitivity check not carried through to every claim.

## Why no toolkit-free twins

Codex's rule: run a twin only if a named decision depends on it. Neither
session touched the toolkit, so a toolkit-free twin would differ only by the
offer sentence. It could not inform any decision about the toolkit. The
remaining ~59k tokens are unspent.

## What this evidence says

1. **Adoption.**
   - When the toolkit is optional, a capable analyst does not even discover it,
     on a supported workflow (Llanvirn: diversity, Bray–Curtis, PCoA) or an
     unsupported one (Dielasma: slope inference). This adds to the calibration
     record, where the direct arm has made no error in 12 trials and costs
     about 2.4 times fewer tokens.
   - Self-reported reason: hand-written code is more visible and checkable.
     That is a defensible preference, not a documentation failure.
2. **What the analyses needed.**
   - Rarefaction, resampling nulls and multiplicity-aware per-taxon tests for
     composition change.
   - Slope inference, slope and elevation comparison and mixture models for
     allometry.
   - Input-integrity checks.
   - The toolkit offers almost none of these, and the analysts wrote all of
     them correctly in a few lines each.
   - Adding them to the toolkit would mostly re-implement what agents already
     do well, which Barry's direction warns against.
3. **Where the value showed: the package contract, not the API.**
   - Requiring a runnable `analysis.py`, a `results.json` and a report, then
     replaying it in a clean confined worker and having an independent model
     review it, produced:
     - traceable claims;
     - byte-identical replays;
     - a referee-level list of overstatements and inconsistencies;
     - the discovery of a real data defect.
   - That verification layer, not the calculation API, is what made two
     70-second analyses checkable.
4. **One recurring need the toolkit should meet: input integrity.** Duplicate
   records are a common defect in legacy palaeontological tables. The toolkit
   refuses duplicate IDs and warns on near-duplicate labels, but reports
   nothing about repeated measurement records or blocks. Our own reference run carried the defect silently.

## Recommendation

- **Record the Dielasma defect now (cheap, needed).**
  - Note the repeated L2 block in the case provenance and in the tranche-1
    results.
  - Keep the archived bytes unchanged.
  - Have any benchmark that uses L2 report the result with and without the
    repeated rows.
- **Add one diagnostic to the toolkit's input validation (small, justified by
  this use case):** a report of exact repeated records and repeated consecutive
  blocks per sample, warning rather than refusing. Nothing else is to be
  added to the calculation API on this evidence.
- **Re-centre the project on the verification layer** (a decision for Barry
  with Codex):
  - the package contract;
  - clean confined replay;
  - an independent cross-model review that traces claims;
  - the toolkit's validated implementations (PAST and R cross-checks) used as
    reference values to check agents' numbers, rather than as the path agents
    must take.
  
  The 96-trial toolkit-versus-direct pilot would measure a benefit that every
  observation so far says is absent. I recommend not running it.
- **Housekeeping for any future sessions:**
  - The retrospective resume re-creates the prompt cache, so it costs about
    18k tokens each (37% of this batch). Ask the question within the session's
    final turn budget or accept the cost knowingly.
  - The worker's subprocess block means analysts cannot test their own script
    as a standalone run. The replay covers this, but a `worker_run_script`
    tool would let them.

Still outstanding from the recalibration round, and unaffected by this:
Codex's decision on resuming T010–T016, and the second adjudication of T005.
