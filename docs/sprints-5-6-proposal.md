# Sprints 5 and 6: headroom, equal packages and a decision

**Claude's proposal, 1 November 2026, revised the same day for Codex's
[critique](sprints-5-6-critique.md) (`d30718e`), whose four definitions are
adopted: equal end-to-end replay, R measured before eligibility, a separate
branch-B table, and exhaustive recalibration routing.** Barry asked Claude to
lead this pair. Its starting point is the
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

### 5.1 Package contract and replay (both arms; revised for Codex's critique)

The baseline the vision names is an agent *writing its own script*, so the
package has to contain that script. Both arms get one contract and one replay
boundary.

- **One entry point.** In both arms, `analysis.py`, run in the task
  directory, must regenerate `answer.json` from the supplied materials.
  - The toolkit arm's script calls the library's own run and study
    operations, which are the same operations as the `palaeo_*` tools, for
    every keyed quantity the toolkit supports.
  - Preparation, glue and unsupported calculations are saved code in both
    arms.
- **Replay boundary.** A fresh confined worker with no model, running the
  arm's own runtime, starts from the pristine supplied materials. It adds only
  the package's `analysis.py` and the files under `specs/`, and runs
  `python analysis.py`.
  - The old `answer.json`, bundles and every other generated output stay
    outside the replay.
  - The comparison target never enters the worker.
- **Comparison.**
  - Status must match.
  - Each keyed result must match within the key tolerance.
  - For a justified non-numerical outcome (a structured stop or unresolved
    decision), the regenerated decision must match, and numeric agreement is
    not applicable.
- **Data-dependence diagnostic.** A second replay runs on materials with the
  frozen perturbation. Its sensitivity is diagnostic, not an R criterion:
  wrong-but-computed analyses may ignore the affected observation, and one
  changing value cannot establish provenance for every reported quantity.
  Source/specification and bundle-provenance adjudication must confirm actual
  computation from supplied materials before a mechanical replay pass enters
  final R. Confirmed stored-answer scripts are classified `static` there.
- **Outcome per launched trial**, in this order:
  - `replayed`;
  - `mismatch`;
  - `failed` (error or timeout);
  - `missing` (no `analysis.py`);
  - `no_answer`;
  - `infrastructure`.
- **R** is the share of *all launched analyst trials* that are `replayed` and
  confirmed to compute from the supplied materials by provenance adjudication,
  per arm, with every other outcome kept in the denominator and reported by
  reason. The paired contrast uses items with both arms launched, and
  unpaired outcomes stay visible. A wrong answer that replays still counts as
  replayed: reproducibility and correctness are separate endpoints. Preserve
  the mechanical outcome and attributed provenance verdict separately; final
  R awaits resolution of pending adjudications.
- **Reviewer eligibility** follows R. E counts pairs whose two packages pass
  final R; E\* restricts these to scientifically acceptable packages in both
  arms with consistently plantable and regenerated flaws. Record each
  exclusion stage separately. The
  reviewer estimand is therefore checkability conditional on both arms
  delivering replayable, acceptable packages. The full flow, from launched
  trials to R, E, E\*, n_S and n_A, is reported with losses by arm.
- **Integrity checks** (`inspect_study`, `inspect`) remain separate
  diagnostics.
- **Historical context.** The calibration observation (0 of 8 direct packages
  kept a script under a soft instruction) is reported as historical context,
  not as an R estimate.

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
  samples where the family is community data, and specimen counts suited to
  morphometric families. Add irregularities that need no action, so that
  over-correction is scored rather than rewarded.
- **Matched controls.** Same structure and scale, with the pitfall's evidence
  resolved. Over-correction on a control is harm (ΔC).
- **No fixed trap count.** An item may hold one pitfall or a coherent
  interaction of several. Success rates are not assumed to multiply.
  Combined interactions get their own witnesses.
- **Two distinct witnesses.**
  - *Implementation:* a Codex delegate computes the reference values from the
    materials and a written analysis specification, without Claude's key
    code. This validates the calculation, not the handling.
  - *Scientific sufficiency:* a materials-only review, at Codex's gate,
    judges whether the specification's handling is warranted by the evidence.
    An author's recipe cannot establish its own validity.
  - Disagreements are resolved before freeze, and recorded.
- **Cue audit, as a diagnostic.** A delegate without the key lists every
  irregularity it would act on, with what it inferred and why. The result
  informs revision but proves neither fairness nor difficulty.
- **Calibration set.** 8 disjoint trap instances from the same generators,
  with different seeds and parameters. The selection, controls and flaw
  detectability criteria are frozen before live use, and nothing is tuned to
  individual calibration answers.
- **Structure kept.** 12 families in the same two strata (toolkit-supported
  and other). The flaw operators and reference values are regenerated for
  the new materials. Families may be merged or replaced only with the reason
  recorded.

### 5.3 Toolkit cost and discoverability

- **Capability labels in discovery.** Discovery is already a compact index by
  default. It gains each method's capability labels ("community: Shannon,
  Simpson, richness, Bray-Curtis, PCoA …") so that agents stop missing
  supported quantities. Full schemas stay on request.
- **Compact inspection.** `inspect` and `study_inspect` return a digest and
  field names by default; values come through `result`.
- **Declared delimited input.** Accept tab- or comma-delimited count tables
  (`format: "delimited"`), with an explicit delimiter, orientation, ID column
  and missing-value semantics. Converted input must preserve IDs and values
  and give the same result as equivalent PAST input. Nothing is inferred from
  filenames, and malformed input is never repaired silently.
- **Offline measurement, an engineering aspiration rather than a gate.**
  Replay the call sequences of the 8 calibration toolkit trials against the
  old and new servers. Compare the client-visible bytes returned, the tool
  schemas separately, and any extra lookups a smaller reply would require.
  The aspiration is a 40% reduction, with warnings, limitations and refusal
  information kept. A byte count does not predict K.
- K ≤ 2.0 remains the decision threshold, and recalibration reports K
  descriptively.
- The runtime is rebuilt, the worker and client probes rerun, and the
  fingerprints refrozen.

### 5.4 Offline evidence from existing records

Done by Codex at close-out: all 11 study bundles and 9 run bundles in the 20
trial records verified and reproduced. Seven studies preserve partial or
refusal histories. Direct packages held scripts in 0 of 8 cases.

### 5.5 Codex review gate

Codex reviews pilot-v4 and the package contract before any live use. The
review covers blind witnesses, cue-audit notes, controls, strata, the
re-execution check and the toolkit changes.

### 5.6 Bounded recalibration (Barry approved, 1 November 2026)

- **Scope.** One round, at most 16 trials (8 calibration traps × 2 arms), on
  the frozen v4 materials, prompts and toolkit.
- **Cost.** At most 400,000 counted tokens. Barry, in Claude chat, 1 November
  2026: "Extra calibration round is approved, if you still deem it required."
  It runs only after Codex's gate on the concrete bank and contract.
- **Routing is exhaustive.**
  - **Branch A** requires all 8 direct outcomes adjudicated, every paired
    attempt accounted for, and direct ≤ 6 of 8.
  - **Branch B** follows if direct ≥ 7 of 8.
  - **Halt for diagnosis** if there is any infrastructure failure, an
    unresolved adjudication or a failure of the replay instrument. This
    brings no automatic retry and no additional round.
  - An analyst's scientific error, or failure to meet a functioning package
    contract, is an observed failure, never missing data.
- **Fixed before recalibration:** the branch rules, the package and R rules,
  the eligibility rules, and the efficacy and reviewer thresholds. Only the
  cost ceilings come afterwards, from the existing 1.5 × median formula, within
  the remaining cumulative allocation. This precommitment is a prospective
  change: earlier plans allowed calibration-informed thresholds.

### 5.7 Freeze

Freeze the bank, prompts, toolkit, launcher, scorer, analysis rules,
thresholds and plan. Rerun the supervisor qualification on the frozen version.
The analyst ceiling is 1.5 × the recalibration median × the trial count.

**Sprint 5 acceptance:**

- pilot-v4 with blind witnesses agreeing;
- the replay check passing its failure-path tests (missing script, missing
  preparation, wrong path, failed execution, static answer);
- the toolkit byte change measured;
- the reviewer launcher and analysis code built and tested before the live
  outcomes they analyse exist;
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
other two questions are answered as a **bounded descriptive development
study**, under its own frozen table.

1. **24 analyst trials:** 12 control items × 2 arms × 1 session, under the
   new contract. These give at most 12 paired packages, so each paired binary
   contrast moves in steps of 1/12 before attrition. They produce the R
   endpoint.
2. **At most 48 reviewer trials,** intact and flawed, over the common valid
   sets, giving ΔS and ΔA. Excluded pairs are never replaced.

**Branch B table.** It has no D or ΔT, and borrows neither calibration D nor
an assumed ΔT = 0. The rules apply in order:

| # | Condition | Result |
| --- | --- | --- |
| B1 | I > 0.20, or replay-instrument failure | **Repair the instrument.** |
| B2 | ΔC ≥ 0.10 | **Toolkit harm.** It vetoes every favourable claim below. |
| B3 | n_S < 6, n_A < 6, or C < 0.8 in either arm | **Inconclusive: insufficient reviewer evidence.** R is still reported. |
| B4 | ΔS ≥ 2/n_S and ΔA ≤ 1/n_A | **Development signal for conditional auditability.** No efficacy, expansion or equivalence claim. |
| B5 | Anything else | **No auditability signal** at this scale. |

R and its paired difference are reported descriptively, with no decision
threshold. Branch B yields no expansion verdict.

### Both branches

- **Technical report** (`docs/pilot-report.md`), with methods, results,
  ceilings, deviations and limitations. Limitations include same-family
  reviewers, bundle formats that prevent full blinding, and development-scale
  samples. It names the AI roles and versions, and links the Board record.
- **Decision for the next programme:** expand, repair the named axis, or stop
  the efficacy line.

### Deferred

A real-data reanalysis of a published palaeoecological analysis is deferred to
a later programme, as Codex recommends. Unused tokens do not define extra
live scope.

## Resources

| Line | Trials | Counted tokens | Authorisation |
| --- | ---: | ---: | --- |
| Recalibration | ≤ 16 | ≤ 400,000 | Approved by Barry, 1 November 2026, after Codex's gate |
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
