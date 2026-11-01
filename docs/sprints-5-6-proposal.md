# Sprints 5 and 6: headroom, equal packages and a decision

**Claude's proposal, 1 November 2026, for Codex's critique.** Barry asked
Claude to lead this pair. Its starting point is the
[sprint 3–4 reconciliation](sprints-3-4-reconciliation.md).

The sequence is:

1. Claude proposes (this document) and Codex critiques. Claude revises, and
   the agents settle any disagreements on the Board.
2. **Claude builds sprint 5;** Codex critiques and fixes.
3. **Sprint 6:**
   - Codex builds the reviewer launcher and the frozen analysis code.
   - Claude runs the live trials, adjudicates and writes the technical report.
   - Codex critiques the report.
4. Reconciliation.

Delegates may take bounded work within the current owner's sprint, and
ownership never passes by silence.

## Where we stand

The infrastructure works. The confined MCP-only supervisor, the study layer,
the launcher gates and the subscription route all held under 20 live Sonnet 5.5
trials. The scientific instrument does not yet work, for three reasons:

1. **No headroom.** Sonnet 5.5 handled every calibration trap in both arms.
   Each remedy rested on one plainly stated fact.
2. **Unequal packages.** No direct-arm package saved its code, so the direct
   arm can neither be reproduced from its package nor enter the reviewer study
   (E\* = 0 as written). Seven of eight toolkit packages carried verifiable
   bundles.
3. **Cost.** The toolkit arm used about twice the tokens (K = 2.05), mostly
   from discovery output and bundle summaries re-entering the context.

The vision asks whether the toolkit makes agent-led analysis **more correct,
easier to check and easier to reproduce** than an agent writing its own
script. These sprints build an instrument that can answer all three, run it,
and decide. A persistent correctness ceiling is a legitimate answer, and the
design does not escalate difficulty until a preferred effect appears.

## Destination

At the end we have:

1. A revised bank (pilot-v4) of realistic multistep analyses that a careful
   analyst can get right from the materials, but on which a frontier agent can
   plausibly go wrong. It has independent witnesses and matched controls, and
   is calibrated to discriminate, or else a documented ceiling.
2. A package contract that makes both arms reproducible and reviewable on
   equal terms, with reproducibility (R) as a measured endpoint.
3. A toolkit whose context cost no longer doubles the analyst's tokens, with
   its discoverability gaps fixed.
4. A completed pilot and reviewer experiment that reaches a decision under the
   frozen table (branch A). If correctness stays at the ceiling, a completed
   checkability and reproducibility study instead (branch B).
5. A technical report in the repository as a first-class output. It holds the
   methods, every result including the ceilings, the AI roles and a pointer to
   the correspondence record.

## Sprint 5: Claude. Instrument repair, offline

### 5.1 Package contract (both arms)

The baseline the vision names is an agent *writing its own script*, so the
package has to contain that script.

- **Direct arm.** The prompt requires the agent to save the code that produces
  its answer as `analysis.py`, and to run it so that it writes `answer.json`.
- **Toolkit arm.** Every reported number must come from a study or run bundle
  in the package. Any glue code goes in `analysis.py` on the same terms.
- **Post-trial re-execution check.** This happens offline, with no model, in a
  fresh confined worker:
  - the direct arm re-runs `analysis.py` from a pristine copy of the materials;
  - the toolkit arm uses `study_reproduce` or `reproduce`, plus `analysis.py`
    where present;
  - the regenerated numbers are compared with `answer.json` within the key
    tolerance.
- **R**, the share of packages that regenerate their reported numbers, becomes
  a prespecified secondary endpoint, per arm and paired by item.
- Reviewer eligibility uses this same check.
- The calibration observation (0 of 8 direct packages kept a script under a
  soft instruction) is reported as historical context, not as an R estimate.

This makes the direct baseline better practice than it was in calibration.
That is the intended comparison: the toolkit must beat an agent that keeps a
script, not one that keeps nothing.

### 5.2 Revised bank, pilot-v4

These principles follow Codex's calibration critique.

- **Coherent multistep chains,** not decorated single steps. For example:
  harmonise taxonomy across two campaigns, aggregate aliquots to cores, join
  the zone metadata, then run the community analysis. A defensible choice
  early on has to carry through to the end.
- **Sufficient, plausibly placed evidence.** The facts needed are present and
  unambiguous to a careful analyst. They sit where real data keeps them: a
  lab-log remark, a provenance sheet, a units line, a second metadata table.
  task.md states the scientific question only. The dictionary describes
  fields neutrally, with no consequences or remedies.
- **Realistic scale with innocuous irregularities.** Use 25–60 taxa and 15–40
  samples. Add irregularities that need no action, so that over-correction is
  scored rather than rewarded.
- **Matched controls.** Same structure and scale, with the pitfall's evidence
  resolved. Over-correction on a control is harm (ΔC).
- **No fixed trap count.** An item may hold one pitfall or a coherent
  interaction of several. Success rates are not assumed to multiply.
  Combined interactions get their own witnesses.
- **Independent witnesses.**
  - A Codex delegate computes the reference values blind, from the materials
    and a written analysis specification, without Claude's key code.
  - Sufficiency witnesses name the evidence that identifies each answer.
  - Disagreements are resolved before freeze, and recorded.
- **Cue audit, as a diagnostic.** A delegate without the key lists every
  irregularity it would act on, with what it inferred and why. The result
  informs revision but proves neither fairness nor difficulty.
- **Calibration set.** 8 disjoint trap instances from the same generators,
  with different seeds and parameters. Nothing is tuned to individual
  calibration answers.
- **Structure kept.** 12 families in the same two strata (toolkit-supported
  and other). The flaw operators and reference values are regenerated for
  the new materials. Families may be merged or replaced only with the reason
  recorded.

### 5.3 Toolkit cost and discoverability

- **Compact discovery.** One line per method by default, with full schemas on
  request. Discovery includes a capability index ("community: Shannon,
  Simpson, richness, Bray-Curtis, PCoA, PERMANOVA …").
- **Compact inspection.** `inspect` and `study_inspect` return a digest and
  field names by default; values come through `result`.
- **Declared delimited input.** Accept tab- or comma-delimited count tables
  (`format: "delimited"`) alongside PAST.
- **Offline measurement.** Replay the call sequences of the 8 calibration
  toolkit trials against the old and new servers, and compare the bytes
  returned. The target is at least a 40% reduction, with no task-relevant
  information lost.
- K ≤ 2.0 remains the decision threshold, and recalibration reports K
  descriptively.
- The runtime is rebuilt, the worker and client probes rerun, and the
  fingerprints refrozen.

### 5.4 Offline evidence from existing records

Re-verify and reproduce every run and study bundle in the 20 existing trial
records, and tabulate script presence. This is descriptive development data,
with no new trials.

### 5.5 Codex review gate

Codex reviews pilot-v4 and the package contract before any live use. The
review covers blind witnesses, cue-audit notes, controls, strata, the
re-execution check and the toolkit changes.

### 5.6 Bounded recalibration (needs Barry's approval)

- **Scope.** One round, at most 16 trials (8 calibration traps × 2 arms), on
  the frozen v4 materials, prompts and toolkit.
- **Cost.** At most 400,000 counted tokens. This is inside the existing
  5,000,000 Sonnet authorisation, but beyond the plan's 16-trial calibration
  cap, so it needs Barry's explicit approval.
- **Stopping rule.** If the direct arm gets 7 or more of 8 acceptable, the
  correctness-efficacy line stops and sprint 6 takes branch B. There is no
  further escalation round.
- **Thresholds.** These are fixed after recalibration and before freeze,
  each change recorded with its reason.

### 5.7 Freeze

Freeze the bank, prompts, toolkit, launcher, scorer, analysis rules,
thresholds and plan. Rerun the supervisor qualification on the frozen version.
The analyst ceiling is 1.5 × the recalibration median × the trial count.

**Sprint 5 acceptance:**

- pilot-v4 with blind witnesses agreeing;
- the re-execution check passing its failure-path tests;
- the toolkit byte reduction measured;
- Codex's gate passed;
- recalibration run, if Barry approves;
- a frozen plan.

## Sprint 6: run and decide

### Branch A: recalibration discriminates (direct ≤ 6 of 8)

1. **96 analyst trials:** 12 families × trap and control × 2 arms × 2
   sessions, in balanced blocks with no retries.
2. **Adjudication** of provisional outcomes, by Claude and an independent
   blind Codex delegate.
3. **Reviewer launcher,** built by Codex with the same gates. Then at most
   4E\* = 48 Sonnet reviewer trials over the common valid sets.
4. **Frozen analysis** produces D, ΔT, ΔC, ΔS, ΔA, R, K and I, and a decision
   under the table.

### Branch B: ceiling persists (direct ≥ 7 of 8)

The correctness-efficacy line stops at this design, as prespecified. The
remaining two questions are answered instead.

1. **24 analyst trials:** 12 control items × 2 arms × 1 session, under the
   new contract. These produce the packages and the R endpoint.
2. **At most 48 reviewer trials,** intact and flawed, giving ΔS and ΔA. The
   question is whether toolkit packages are easier to check.
3. Cost and reproducibility are reported alongside.

Both branches use only existing authorisations: at most 96 analyst trials
within the 5,000,000 Sonnet tokens, and at most 48 reviewer trials within
1,500,000.

### Both branches

- **Technical report** (`docs/pilot-report.md`), with methods, results,
  ceilings, deviations and limitations. Limitations include same-family
  reviewers, bundle formats that prevent full blinding, and development-scale
  samples. It names the AI roles and versions, and links the Board record.
- **Decision for the next programme:** expand, repair the named axis, or stop
  the efficacy line.

### Stretch, not gating

A real-data reanalysis: an agent reproduces a published palaeoecological
analysis from its archived data with the toolkit, every number traceable to a
versioned operation. Claude selects the case and Codex verifies it
independently. It runs only if sprint 6's core completes within the existing
allocation.

## Resources

| Line | Trials | Counted tokens | Authorisation |
| --- | ---: | ---: | --- |
| Recalibration | ≤ 16 | ≤ 400,000 | **New approval needed** (trial cap) |
| Analysts (A) or package trials (B) | ≤ 96 / 24 | 1.5 × median × trials | Existing 5,000,000 Sonnet |
| Reviewers | ≤ 48 | ≤ 1,500,000 | Existing reviewer replicate |

All runs use Barry's subscription through the qualified supervisor, on the
MacBook kept awake, or on `mini` after the runtime is rebuilt and the probes
rerun there. There are no API accounts and no public release.

## Risks

- **The revision may still hit the ceiling.** That is a result, and branch B
  answers the other two questions.
- **The package contract changes the direct baseline.** This is deliberate,
  and the historical observation is reported.
- **Toolkit changes between calibration and pilot.** Everything is frozen
  before recalibration, and the pilot uses exactly that freeze.
- **Subscription rate limits.** Trials are small (median 6,500 counted). A
  rate-limit failure is an infrastructure failure, counted in I, never retried.
- **Two-agent agreement is not independent validation.** Blind witnesses and
  fresh-context reviewers reduce this but do not remove it. Disagreements stay
  visible.
