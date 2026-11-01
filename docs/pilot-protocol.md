# Pilot protocol (draft for the pre-freeze gate)

Claude (Opus 5.5), 31 October 2026. This draft implements sprint 4 of the
[revised plan](sprints-3-4-proposal.md). It covers the planted-error
specifications, the endpoints and the exhaustive decision table Codex asked for
(Board 2724 and 2731). Codex reviews it at the pre-freeze gate. **Nothing here
is frozen.** Bank: [`evaluation/pilot`](../evaluation/pilot/README.md),
`pilot-v3`.

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
- If E\* < 6, the reviewer endpoints are not interpreted. Rule 1 then applies
  to the reviewer part only.
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

**Reviewer metrics, each over E\* (F4).**

- **Sensitivity:** flawed variants rejected *with attribution*, meaning the
  rejection names the planted class, or the planted step or field. A
  rejection for another reason is counted separately as non-attributed.
- **False accusation:** intact variants rejected.
- **Missing reviews:** a reviewer trial that failed or returned no valid
  verdict is excluded from both numerator and denominator and reported. It is
  never counted as a non-accusation.
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
| ΔS | Toolkit minus direct attributed reviewer sensitivity, over E\* | pair in E\* |
| ΔA | Toolkit minus direct false-accusation rate, over E\* | pair in E\* |
| ΔT_tk, ΔT_other | ΔT within the `toolkit` (7 families) and `other` (5 families) strata | item |
| K | Median counted tokens per analyst trial, toolkit / direct | item (family clusters, F6) |
| I | Share of analyst trials that are infrastructure failures | item (family clusters, F6) |

Intervals are 80% percentile bootstraps (10,000 resamples, seed fixed at
freeze), resampling items or eligible pairs, never trials. Sessions and
variants stay clustered.

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
| 4 | ΔT ≥ 0.15 with lower bound > 0, ΔC ≤ 0.05, K ≤ 2.0, not confined, E\* ≥ 6, C ≥ 0.8 in both arms, ΔS ≥ −1/E\* and ΔA ≤ 1/E\* | **Expand.** |
| 4a | Rule 4's analyst conditions hold, but E\* < 6 or C < 0.8 in either arm | **Incomplete: analyst signal, reviewer instrument repair.** Report the analyst findings; no expansion verdict. |
| 5 | Rule 4's conditions hold except that the gain is confined | **Repair:** enforcement works but does not generalise. |
| 6 | ΔT ≥ 0.15 with lower bound > 0, but ΔC, K, ΔS or ΔA fails rule 4 | **Repair** the failing axis. |
| 7 | E\* ≥ 6, C ≥ 0.8 in both arms, ΔS ≥ 2/E\*, ΔA ≤ 1/E\*, \|ΔT\| < 0.15, ΔC ≤ 0.05 | **Development signal for auditability.** No claim of established review gain or of correctness equivalence. |
| 8 | \|ΔT\| < 0.15, ΔC ≤ 0.05, and (E\* < 6 or \|ΔS\| ≤ 1/E\*) | **Null: stop this efficacy line** at this power. |
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
- **Fingerprints, enforced at every launch.** The client binary, the runtime
  manifest, the installed toolkit files, both `pyvenv.cfg` files, the worker,
  server, launcher and scorer source, the prompts, and the item manifest,
  including the trial's own materials. Any difference halts launches.
- **Configuration directory.** It may hold no CLAUDE.md, agents, commands,
  skills, plugins, hooks, settings or memory content, and it must be logged in
  to a subscription. The client's working directory has no instruction files
  above it.
- **Inventory capture.** The identical command is run against a fake endpoint
  with a dummy key, using a separate configuration directory that is not
  logged in, so no real credential can be sent. Each capture is saved with the
  trial, and it must equal the frozen inventory.
- **Admission.** Claude Code refuses unadvertised tools before dispatch, as
  the scripted probes show. Its init record must equal the frozen inventory,
  or the trial is killed. A missing init record is a breach.
- **Reconciliation by identity.**
  - Each worker tool event is matched, in order, to its audit record by tool
    and primary arguments, and its success or error must agree.
  - Each unadvertised name must show a client refusal and have no audit row.
  - An event without a result, an audit row without an event, or anything
    else halts launches.
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
