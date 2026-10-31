# Pilot protocol (draft for the pre-freeze gate)

Claude (Opus 5.5), 31 October 2026. This draft implements sprint 4 of the
[revised plan](sprints-3-4-proposal.md). It covers the planted-error
specifications, the endpoints and the exhaustive decision table Codex asked for
(Board 2724 and 2731). Codex reviews it at the pre-freeze gate. **Nothing here
is frozen.** Bank: [`evaluation/pilot`](../evaluation/pilot/README.md),
`pilot-v2`.

## Analyst arms and backend

- **Backend.**
  - Analysts run on Codex if a Codex client route qualifies under the launch
    conditions below.
  - Otherwise they run on `claude-sonnet-5-5`, as Barry authorised (31 October
    2026).
  - The backend is frozen with the plan. Families never mix.
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

## Scoring (amendment to `sprint1-revised-v2`)

The revised scorer applies unchanged, with three additions for `pilot-v2`
keys:

1. **`acceptable_alternatives`.** P04-trap may instead stop with the coverage
   issue named. This is scored `correct_unresolved`, and both count as
   acceptable.
2. **`out_of_scope_ids`.** Samples outside the task's scope (P08's
   Pleistocene samples) are neither required nor penalised as exclusions.
3. **Strata.** Every summary is reported overall and by stratum: `toolkit`
   (P01–P06, P12) and `other` (P07–P11).

*Acceptable* means `correct` or `correct_unresolved`. *Harm* on a control
means `wrong`, `false_refusal` or `failed`.

## Reviewer experiment

**Eligibility, fixed now.**

- Use the 12 control items' session-1 packages, from both arms.
- A pair is eligible when both arms produced a schema-valid answer and a
  package that passes its own integrity check: `inspect_study` or
  `inspect_run` where used, and file hashes otherwise.
- Ineligible pairs are recorded and never replaced. **E** is the number of
  eligible pairs, at most 12.
- The denominator for every reviewer rate is E, not 12.

**Variants.** Each eligible package is reviewed twice: intact, and with the
item's planted flaw. That gives 4E Codex reviewer trials, plus 4E in the Sonnet
replicate.

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
| P07-control | preparation | L3 values divided by 10 as "cm" | Dictionary: all localities measured in mm. |
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

The reference verdict for a flawed variant is `reject` with the planted class.
For an intact variant it comes from the analyst package's own score: `accept`
if acceptable, otherwise `reject`. The reference is fixed before any review.

**Reviewer metrics, each over E.**

- **Sensitivity:** flawed variants rejected.
- **Localisation:** rejections that name the planted class.
- **False accusation:** correct intact variants rejected.
- **Cost:** tokens and time.

## Endpoints

| Symbol | Definition | Unit of resampling |
| --- | --- | --- |
| D | Direct-arm acceptability on traps | item |
| ΔT | Toolkit minus direct trap acceptability, item-paired and averaged over sessions | item |
| ΔC | Toolkit minus direct control harm | item |
| ΔS | Toolkit minus direct reviewer sensitivity, over E | eligible pair |
| ΔA | Toolkit minus direct false-accusation rate, over correct intact packages | eligible pair |
| K | Median counted tokens per analyst trial, toolkit / direct | trial |
| I | Share of analyst trials that are infrastructure failures | trial |

Intervals are 80% percentile bootstraps (10,000 resamples, seed fixed at
freeze), resampling items or eligible pairs, never trials. Sessions and
variants stay clustered.

## Decision table

The rules are applied in order, and the first one that matches decides.
Thresholds are provisional until calibration; any change is recorded with its
reason before freeze.

| # | Condition | Decision |
| --- | --- | --- |
| 1 | I > 0.20, or E < 8 | **Repair the instrument.** No toolkit verdict. |
| 2 | D ≥ 0.90 | **Stop this design.** The bank cannot discriminate. Report descriptively. |
| 3 | ΔT ≤ −0.15 with the interval's upper bound < 0, or ΔC ≥ 0.10 | **Adverse.** Stop expansion and repair the toolkit behaviour that caused the harm. |
| 4 | ΔT ≥ 0.15 with lower bound > 0, ΔC ≤ 0.05, ΔS ≥ −1/E, ΔA ≤ 1/E, K ≤ 2.0, and the `other` stratum's ΔT ≥ 0 | **Expand.** |
| 5 | Rule 4 holds except that the gain is confined to the `toolkit` stratum, with `other` ΔT < 0 | **Repair.** Enforcement works but does not generalise; broaden coverage before expanding. |
| 6 | ΔT ≥ 0.15 with lower bound > 0, but ΔC, ΔS, ΔA or K fails rule 4 | **Repair.** Fix the failing axis, then re-pilot. |
| 7 | ΔS ≥ 2/E and ΔA ≤ 1/E, with \|ΔT\| < 0.15 and ΔC ≤ 0.05 | **Repair for auditability.** The reviewability gain is real; correctness is null. Develop the evidence format and do not claim error reduction. |
| 8 | \|ΔT\| < 0.15, \|ΔS\| ≤ 1/E, ΔC ≤ 0.05 | **Null. Stop this efficacy line.** Record that no benefit was measured at this power. |
| 9 | Anything else (for example 0.05 ≤ ΔT < 0.15, or an interval spanning 0 with a large point estimate) | **Inconclusive.** No claim. Any larger pilot is a new, separately authorised design. |

A null or adverse result completes the sprint. No trials are added after
outcomes are seen.

## Launch conditions (both backends)

- **Runtime.** Rebuild both arm runtimes with the current wheel, which
  includes the study tools. Rerun the worker probes and both clients'
  inventory and scripted-refusal probes against those runtimes, and freeze the
  inventories.
- **Pinned and gated per launch.**
  - Pin the client binary, any model catalogue, the command, the prompt, the
    MCP configuration and the runtime manifests. Check them at each launch.
  - Immediately before each trial, run the fake-endpoint capture with the
    identical configuration. Refuse the launch if the inventory differs from
    the frozen one.
- **Live monitoring.** Monitor the client's event stream during the trial.
  Kill the process group on any tool event that does not belong to the worker
  MCP server.
  - After the trial, reconcile tool events with the worker's call log, and,
    for Codex, with the rollout trace's actual requests.
  - A missing trace, or any mismatch, invalidates the trial and stops further
    launches pending review.
  - This replaces the plan's literal "client init inventory" condition for
    Codex, whose init record does not expose the inventory. Codex must agree
    to the replacement.
- **Per-trial limits.** A turn cap, a wall-clock kill and no retries. Unknown
  usage stops launches.
