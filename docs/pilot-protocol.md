# Pilot protocol (draft for the pre-freeze gate)

Claude (Opus 5.5), 31 October 2026. This draft implements sprint 4 of the
[revised plan](sprints-3-4-proposal.md). It covers the planted-error
specifications, the endpoints and the exhaustive decision table Codex asked for
(Board 2724 and 2731). Codex reviews it at the pre-freeze gate. **Nothing here
is frozen.** Bank: [`evaluation/pilot`](../evaluation/pilot/README.md),
`pilot-v3`.

## Sprint 5 amendments (pilot-v4), operative over everything below

Claude, 1 November 2026, from the [revised sprint 5–6 plan](sprints-5-6-proposal.md)
and Codex's [critique](sprints-5-6-critique.md). Where the sections below say
otherwise, these rules govern. They are fixed before recalibration.

- **Bank.** `evaluation/pilot/items-v4` (24 items: 12 families × trap and
  control) and `calibration-v4` (8 traps: P03, P04, P05, P06, P08, P09, P10,
  P11).
  - Built by `build_bank_v4.py`.
  - Every trap and its control share identical task.md and dictionary.md; the
    deciding fact is only in the data records.
  - Keys are computed by parsing the written files.
  - The independent implementation witness agrees with all 32 keys
    (`witness-v4/`).
  - Each control key carries its reviewer flaw (`reviewer_flaw`): class,
    frozen reference results, answer edits and specific attribution
    criterion. These replace `flaws.json` for v4.
- **Scoring.** As before, plus `alternative_results`: another defensible
  handling scores correct, and is not provisional. Pilot-v4 uses this for P06
  (mean of aliquot proportions per core) and P09 (left valve, or the mean of
  both valves).
- **Package contract.** One self-contained `analysis.py` per package, in both
  arms, regenerates `answer.json` from the supplied materials. Only
  `analysis.py` and `specs/` are kept. The toolkit arm calls the library's own
  operations from it (prompts in `evaluation/pilot/prompts/`).
- **Replay and R.**
  - `replay.py` re-runs each launched trial's package in a fresh confined
    worker on its arm's runtime. The worker gets the pristine materials plus
    only `analysis.py` and `specs/`; the old answer and outputs never enter
    it.
  - A second run, with the key's frozen perturbation, detects static answers.
  - Outcomes: `replayed`, `static`, `mismatch`, `failed`, `missing`,
    `no_answer`, `infrastructure`.
  - **R** is the share of all launched analyst trials that are `replayed`, per
    arm and paired by item, with every other outcome kept in the denominator
    and reported by reason. A wrong answer can be replayed.
  - Replay infrastructure failure halts launches.
- **Reviewer eligibility.** Both arms' packages must be `replayed` and
  adjudicated acceptable. Report the flow from launched trials to R, E, E\*,
  n_S and n_A, with losses by arm. The reviewer estimand is checkability
  conditional on replayable, acceptable packages in both arms.
- **Recalibration routing** (one round, at most 16 trials, at most 400,000
  counted tokens):
  - **Branch A** needs all 8 direct outcomes adjudicated, every paired attempt
    accounted for, and direct ≤ 6/8.
  - **Branch B** follows when direct ≥ 7/8.
  - Any infrastructure failure, unresolved adjudication or replay-instrument
    failure **halts for diagnosis**, with no retry and no extra round.
  - Analyst errors and package-contract failures are observed outcomes, never
    missing data.
- **Branch A** uses the endpoints and decision table below, with R added as a
  prespecified secondary endpoint.
- **Branch B** is a descriptive development study: 24 control-item analyst
  trials and at most 48 reviewer trials. Its table is in the plan: B1
  instrument, B2 control-harm veto, B3 insufficient reviewer evidence, B4
  conditional auditability signal, B5 none. It has no D or ΔT, and gives no
  expansion verdict; R is descriptive.
- **Thresholds** below are fixed now. Only the cost ceilings follow
  recalibration, as 1.5 × the median × the trials, inside the remaining
  allocation.
- **Toolkit and runtime.**
  - `pilot-runtime-v4-20261101` adds declared delimited input and capability
    labels in discovery, and advertises a compact run/validate spec schema
    (tool definitions 19.4 → 10.0 KB) while still validating fully on the
    server.
  - Worker probes passed 29/29 per arm, and the client boundary probe 4/4.

## Revision after Codex's pre-freeze review (F1–F8)

Codex's [pre-freeze review](sprint-4-prefreeze-review.md) raised eight
findings. All are accepted and resolved below; `evaluation/pilot/score.py`
implements F1 and F2.

## Analyst arms and backend

- **Backend: `claude-sonnet-5-5` through Claude Code (F8).**
  - Codex did not accept a runtime tripwire as equivalent to pre-dispatch
    enforcement, and no admission route for the Codex client exists.
  - Claude Code's own dispatcher demonstrably refuses every tool it did not
    advertise (the [sprint-3 review](sprint-3-review.md) scripted these calls
    offline), and its init record exposes the inventory.
  - Barry authorised this fallback on 31 October 2026.
  - **Same-family development pilot (agreed with Codex, Board 2764/2765).**
    Analysts and reviewers are both Sonnet. There are at most 48 reviewer
    trials, inside the existing 1,500,000 counted-token envelope. The earlier
    two-population reviewer design is withdrawn. Cross-family validation is
    deferred and explicitly unfinished; no result is claimed to generalise
    across model families.
  - **Authentication: Barry's subscription only** (Barry, 1 November 2026).
    The supervisor authenticates through a dedicated configuration directory,
    logged in once with `claude auth login --claudeai`. Before each trial the
    launcher checks that this directory holds no instructions, memory, skills,
    plugins or settings, and that it is logged in to a subscription.
    No API account is used.
- **Arms.**
  - Both arms get the confined worker's `worker_execute`, `worker_read` and
    `worker_write`.
  - The toolkit arm adds the palaeo MCP tools, including the `study_*` tools,
    and the prompt paragraph that requires toolkit use for supported numerical
    operations.
  - Adherence comes from the worker's own call logs: each trial records whether
    any `palaeo_run` or `palaeo_study_run` produced a keyed quantity.
- **Trials.** 24 items × 2 arms × 2 sessions = 96. They run in balanced blocks
  (one family × both classes × both arms × one session), in a seeded order
  fixed at freeze.
- **Partial blocks (L8).** The ceiling stops launches immediately, even inside
  a block; no block is completed beyond the ceiling.
  - The primary paired analyses use only item-session pairs with both arms
    present.
  - Every unpaired trial is reported descriptively and listed.
  - The report gives the number of complete pairs per family and stratum.

## Scoring (amendment to `sprint1-revised-v2`)

The revised scorer applies unchanged, with five additions for `pilot-v3`
keys:

1. **`acceptable_alternatives`.** P04-trap may instead stop with the coverage
   issue named. This is scored `correct_unresolved`, and both count as
   acceptable.
2. **`out_of_scope_ids`.** Samples outside the task's scope (P08's
   Pleistocene samples) are neither required nor penalised as exclusions.
3. **`disclosure_tokens` (F2).** A numerically correct P04-trap or P04-cal
   answer that does not disclose its restricted taxonomic basis scores
   `undisclosed`, which is not acceptable. A keyword match is only a candidate:
   every numerically correct answer is provisional until semantic
   adjudication confirms that the restricted basis was actually disclosed.
   A false full-community claim fails.
4. **`equivalent_exclusions` (F1).** In P09-trap, excluding either valve of a
   pair, or neither if the pair is averaged, is equivalent. Excluding both is
   flagged in the evidence checks.
5. **Strata.** Every summary is reported overall and by stratum: `toolkit`
   (P01–P06, P12) and `other` (P07–P11).

*Acceptable* means `correct` or `correct_unresolved`. *Harm* on a control
means `wrong`, `false_refusal` or `failed`.

## Reviewer experiment

**Whole-package adjudication (F3).** After the analyst trials and before any
reviewer trial runs:

- Claude and a Codex delegate independently adjudicate each session-1 control
  package. They judge the numbers *and* the prose, assumptions and exclusions,
  as scientifically acceptable or not.
- Disagreements are resolved on the Board and recorded.
- The adjudications are then frozen. The numerical score alone never sets an
  intact reference verdict: a correct number with an unsupported claim is
  unacceptable.

**Eligibility, fixed now.**

- Use the 12 control items' session-1 packages, from both arms.
- A pair is eligible when both arms produced a schema-valid answer, and a
  package that passes its own integrity check: `inspect_study` or
  `inspect_run` where used, otherwise re-execution of the saved script
  reproducing the answer.
- Ineligible pairs are recorded and never replaced. **E** is the number of
  eligible pairs. It is reported only as a count; no rate uses it.

**Analysis set (F4).**

- The primary reviewer analysis set is the pairs whose intact packages were
  adjudicated acceptable in *both* arms. **E\*** is the number of such pairs.
- E and E\* are both reported, along with each ineligible or unacceptable
  pair and its reason.
- If E\* < 6, or either common valid set (below) has fewer than 6 pairs, the
  reviewer endpoints are not interpreted. Rules 4a, 8 and 9 then govern the
  reviewer part.
- Restricting to packages that are correct in both arms is a selection, and
  it is reported as one.

**Variants.** Each package in E\* is reviewed twice: intact, and with the
item's planted flaw. That gives 4E\* ≤ 48 Sonnet reviewer trials.

**Flaw rules.**

- Each flaw is applied at the step where the error would arise. Everything
  downstream is regenerated, by rerunning the package's own script or study
  where one exists and by recomputation otherwise.
- The flawed package must pass its own integrity checks.
- The same flaw goes into both arms' packages for an item.
- A flaw that cannot be planted consistently in one arm's package makes that
  pair ineligible. This is recorded, and no substitute is used.

**The 12 flaws.**

| Item | Class | Planted flaw | Detectability witness |
| --- | --- | --- | --- |
| P01-control | preparation | Core 5 excluded as "residue lost" | Dictionary: every core counted in full. |
| P02-control | preparation | Field log joined by row order, not code | Log codes ≠ assigned zones in the derived metadata. |
| P05-control | preparation | Two distinct species merged as a "case variant" | Names differ beyond case and spacing. |
| P07-control | preparation | L3 values treated as cm and multiplied by 10 to give "mm" | Dictionary: all localities measured in mm. |
| P09-control | preparation | Four right valves dropped as "duplicates" | No notes link them to other specimens. |
| P11-control | preparation | Globigerinoides counted under Globigerina | Genus is the first word; the names differ. |
| P03-control | design | Bray–Curtis on relative abundances, with raw counts requested | Spec or script shows the transform. |
| P06-control | design | Consecutive rows pooled in threes as if aliquots (n = 6) | Dictionary: each row is a separate core. |
| P12-control | design | Raw counts used, with relative abundance requested | Spec or script shows the transform. |
| P04-control | interpretation | Correct numbers; summary says diversity "increased significantly" | No test was run; the difference is tiny. |
| P08-control | interpretation | Correct numbers; summary says the Holocene is "more homogeneous than the Pleistocene" | Pleistocene was not analysed. |
| P10-control | interpretation | Correct number; summary states the opposite direction of change | The sign of `shannon_change` contradicts the text. |

**Reviewer output.** A schema-valid verdict with three parts:

- `accept` or `reject`;
- if rejecting, the flawed component (`preparation`, `design`,
  `interpretation` or `numerical`) and the step or field;
- a short justification.

**References.** All in E\* are frozen before any review.

- A flawed variant's reference is `reject`, attributed to its frozen
  `attribution_criterion` (`evaluation/pilot/flaws.json`).
- Intact variants in E\* were adjudicated acceptable as whole packages, so
  their reference is `accept`.

**Attribution (F4).** Claude and a Codex delegate adjudicate each rejection
independently against the flaw's `attribution_criterion`. It counts as
detection only if it identifies the actual mistaken operation or conclusion,
with a justification that fits that criterion. Naming the right broad class
for an unrelated reason does not count.

**Common valid sets (closure R1).** Missing verdicts are handled by pairing,
so both arms of every contrast are computed over the same packages.

- The **flawed set** is the pairs in E\* whose flawed variant has a valid
  verdict in *both* arms; **n_S** is its size.
- The **intact set** is the pairs in E\* whose intact variant has a valid
  verdict in both arms; **n_A** is its size.
- A pair missing a verdict in either arm drops out of that endpoint for both
  arms. The surviving arm's verdict is reported descriptively and never
  enters a contrast.
- Arm-specific rates over each arm's own valid verdicts are reported as
  secondary, conditional descriptions. Their selected populations are stated,
  and no decision uses them.

**Reviewer metrics (F4).**

- **Sensitivity:** in the flawed set, the share of flawed variants rejected
  *with attribution*, as adjudicated against the frozen criterion (above). A
  rejection that fails attribution is counted separately as non-attributed.
- **False accusation:** in the intact set, the share of intact variants
  rejected.
- **Missing reviews:** a reviewer trial that failed or returned no valid
  verdict is never counted as a non-accusation or a non-detection. It removes
  its pair from that endpoint's common valid set, and it is reported.
- **Completion (C):** the share of reviewer trials with a valid verdict,
  per arm.
- **Cost:** tokens and time.
- A metric with a zero denominator is undefined, never zero.

## Endpoints

| Symbol | Definition | Unit of resampling |
| --- | --- | --- |
| D | Direct-arm acceptability on traps | item |
| ΔT | Toolkit minus direct trap acceptability, item-paired and averaged over sessions | item |
| ΔC | Toolkit minus direct control harm | item |
| ΔS | Toolkit minus direct attributed reviewer sensitivity, over the flawed set (n_S pairs) | pair in the flawed set |
| ΔA | Toolkit minus direct false-accusation rate, over the intact set (n_A pairs) | pair in the intact set |
| ΔT_tk, ΔT_other | ΔT within the `toolkit` (7 families) and `other` (5 families) strata | item |
| K | Median counted tokens per analyst trial, toolkit / direct | item (family clusters, F6) |
| I | Share of analyst trials that are infrastructure failures | item (family clusters, F6) |

Intervals are 80% percentile bootstraps (10,000 resamples, seed fixed at
freeze), resampling items or pairs, never trials. Sessions stay clustered
within items. For ΔS and ΔA, each draw resamples that endpoint's common valid
set, and every resampled pair carries a valid verdict in both arms. No draw
can therefore have a zero denominator. An empty set (n = 0) leaves the
endpoint undefined, and it is reported as undefined, never as zero.

**Reviewer margins.** The margins are counts of packages on the common valid
set: one package for ±1/n and two for 2/n. Written as rates, ΔS ≥ −1/n_S
means the toolkit arm detects at most one fewer flawed package than the
direct arm on the same n_S pairs. With no missing verdicts, n_S = n_A = E\*,
and these are the margins prespecified as 1/E\* and 2/E\*. The E\* ≥ 6 gate
applies to the sets actually analysed, so rules 4 and 7 need n_S ≥ 6 and
n_A ≥ 6. This is the existing threshold applied to the real denominators, not
a new one.

## Decision table (revised for F5 and F6)

**Two parts.**

- **Part A** checks for harm in every case. It cannot be cancelled by Part B.
- **Part B** gives the design verdict.

**Part A, toolkit harm.** If ΔT ≤ −0.15 with the interval's upper bound below
0, or ΔC ≥ 0.10, the report flags **toolkit harm** and the decision includes
repairing the cause. This applies even when Part B stops the design for
ceiling or instrument reasons.

**Part B, design verdict.** The rules are applied in order, and the first one
that matches decides. **Confined** means ΔT_tk ≥ 0.15 and ΔT_other < 0.05.

| # | Condition | Decision |
| --- | --- | --- |
| 1 | I > 0.20 | **Repair the instrument.** No efficacy verdict. Part A still applies. |
| 2 | D ≥ 0.90 | **Stop this design**, because it cannot discriminate. Part A still applies. |
| 3 | Part A flagged harm | **Adverse.** Stop expansion. |
| 4 | ΔT ≥ 0.15 with lower bound > 0, ΔC ≤ 0.05, K ≤ 2.0, not confined, n_S ≥ 6, n_A ≥ 6, C ≥ 0.8 in both arms, ΔS ≥ −1/n_S and ΔA ≤ 1/n_A | **Expand.** |
| 4a | Rule 4's analyst conditions hold, but n_S < 6, n_A < 6 or C < 0.8 in either arm | **Incomplete: analyst signal, reviewer instrument repair.** Report the analyst findings; no expansion verdict. |
| 5 | Rule 4's conditions hold except that the gain is confined | **Repair:** the gain is confined to toolkit-related families. The design does not identify which mechanism produced it. |
| 6 | ΔT ≥ 0.15 with lower bound > 0, but ΔC, K, ΔS or ΔA fails rule 4 | **Repair** the failing axis. |
| 7 | n_S ≥ 6, n_A ≥ 6, C ≥ 0.8 in both arms, ΔS ≥ 2/n_S, ΔA ≤ 1/n_A, \|ΔT\| < 0.15, ΔC ≤ 0.05 | **Development signal for auditability.** No claim of established review gain or of correctness equivalence. |
| 8 | \|ΔT\| < 0.15, ΔC ≤ 0.05, and (n_S < 6 or \|ΔS\| ≤ 1/n_S) | **Null: stop this efficacy line** at this power. |
| 9 | Anything else | **Inconclusive.** No claim. |

Reviewer clauses never drop out of rules 4 and 7. Inadequate reviewer
evidence leads to rule 4a, or to rules 8–9.

**Counterexample check.** Codex's case had 7 toolkit-stratum improvements and
5 zeros in the other stratum. It now matches rule 5, not rule 4: ΔT_other = 0
is below 0.05.

## Launch conditions (implemented in `evaluation/pilot/launch.py`)

- **Runtime.** Both arm runtimes are rebuilt with the current wheel, which
  includes the study tools. The worker probes and the client's inventory and
  scripted-refusal probes are rerun against them, and the inventories are
  frozen in the plan.
- **Fingerprints, enforced at every launch.** The client binary; every byte,
  link and directory of both arm runtimes (all installed dependencies) and of
  their base interpreter; the worker, server, launcher and scorer source; the
  prompts; and the item manifest. The trial's item directory must hold
  exactly the manifest's files, unchanged, with no links or special files,
  and only the listed materials are staged. Any difference halts launches.
- **Configuration directory.** It may hold no CLAUDE.md, agents, commands,
  skills, plugins, hooks, settings or memory content, and it must be logged in
  to a subscription. The login is checked in the client's own launch
  environment: a fresh HOME whose only content is a link to the login keychain,
  through which macOS finds the stored subscription login. The client's
  working directory has no instruction files above it. The launch passes an
  empty `--setting-sources`, which loads no CLAUDE.md, and disables auto-memory.
  `qualify_supervisor.py` verified this environment against a fake endpoint:
  no user instruction, memory or preamble appears in the request, while a
  positive control with a planted CLAUDE.md is detected.
- **Inventory capture.** The identical command is run against a fake endpoint
  with a dummy key, using a separate configuration directory that is not
  logged in, so no real credential can be sent. Each capture is saved with the
  trial, and it must equal the frozen inventory.
- **Admission.** Claude Code refuses unadvertised tools before dispatch, as
  the scripted probes show. Its init record must equal the frozen inventory,
  or the trial is killed. A missing init record is a breach.
- **Reconciliation by identity.**
  - Each worker tool use has exactly one result, and each result has exactly
    one use.
  - Each use is paired with one unused audit record. The pair must match on
    the full normalised request (code; path, offset and limit; path and
    content; or the toolkit arguments). It must also match on the exact value
    the fixed adapter returns for that record, and on its error flag.
  - Each unadvertised name must show a client refusal and have no audit row.
  - An event without a result, an orphan or duplicate result, an audit row
    without an event, or any mismatch halts launches.
- **Abort cleanup.** The launcher kills the client's process group, the worker
  server and every worker process group the worker recorded. It then verifies
  from a full process listing that none survive. A failed listing halts
  launches.
- **Export.** Only regular files are copied, never following links. Links and
  special files are listed, never read.
- **Usage and the ledger.**
  - Every usage field must be present and non-negative.
  - Any incomplete trial, breach or halt writes `HALTED.json`, and no later
    trial launches until a reviewed decision.
  - The output directory is bound to its plan's hash. A started trial is
    never rerun.
- **Per-trial limits.** A turn cap and a wall-clock kill.
- **Codex route.** Retained only if a pre-dispatch admission route qualifies
  and Codex reviews it (F8).
