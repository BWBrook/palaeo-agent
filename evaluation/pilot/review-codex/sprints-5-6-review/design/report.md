# Independent methodological critique of sprints 5–6

Codex, 1 November 2026. Reviewed proposal `0c3e106` against
`docs/pilot-protocol.md`, the previous calibration review and the current
reproduction implementation. This is an offline design review; no model
trials or implementation changes were made.

**Recommendation: proceed with the offline sprint after the contract and
branch definitions below are revised.** The proposed ownership and one-round
stopping structure are sound. Neither additional sessions nor a larger bank
is needed to resolve these points.

## Required design corrections

### 1. One raw-material-to-answer replay contract for both arms

Proposal lines 68–81 require the direct script to run from pristine materials,
but allow toolkit replay through `study_reproduce` / `reproduce` and optional
glue. Those operations currently replay **saved input snapshots**:
`src/palaeo_agent/study.py:468` and `src/palaeo_agent/runs.py:326`. They do not
establish that preparation performed before bundle creation can be regenerated
from the task's supplied materials. This matters especially for the proposed
multistep preparation tasks.

Use the same endpoint boundary in both arms: supplied raw materials plus
saved executable instructions, in the pinned arm runtime, must regenerate the
submitted numerical answer. A toolkit package may use a declarative study as
its executable instructions and a script for unsupported preparation and
answer assembly. A direct package may use its script. The machinery may differ;
the input and output boundary must not. Specify the single invocation and
mapping from generated artefacts to answer fields. Replay must not inherit
old output directories or read the submitted answer as a computation input.
Keep bundle integrity/snapshot reproduction as a separate diagnostic.

Requiring `analysis.py` is a reasonable operational baseline, not inherently
an unfair comparison. Requiring that exact filename only on one arm is not
the essential feature; equivalent executable completeness is. Phrase the
toolkit requirement as supported operations through bundles, with unsupported
preparation and numerical glue explicitly saved. Avoid making unsupported
operations impossible merely by requiring every number to be a bundle field.

### 2. Define R before applying reviewer eligibility

Proposal lines 79–81 leave R's denominator unspecified while using replay as
reviewer eligibility. If R is calculated only after that gate, it is 100% by
construction. If missing packages disappear, an arm can improve its apparent
R by failing to produce difficult packages.

Specify the replay outcome for every analyst attempt before eligibility:
missing script, invalid package, execution failure, result mismatch and success
must remain visible. Report per-arm counts and a paired contrast on a stated
common item/session set; retain unmatched attempts descriptively. Distinguish
infrastructure failures with unavailable packages from delivered packages that
fail replay, and give an all-attempt delivery-and-replay yield if conditional
R excludes infrastructure failures. Do not select R on scientific correctness:
a wrong analysis can be exactly reproducible. Define the treatment of valid
`correct_unresolved` answers with no numerical fields; an empty numerical
comparison must not vacuously count as successful numerical reproduction.

Reviewer endpoints can retain the existing narrower selection: both packages
replay, both intact packages are scientifically acceptable, and the same flaw
can be planted consistently. Preserve E, E*, n_S, n_A, exclusion reasons and
completion reporting. Say that ΔS/ΔA concern those selected paired packages,
not the overall probability of receiving an auditable analyst result.

### 3. Branch B needs its own decision table and adequacy stop

The proposed 24 analyst trials create **at most 12 paired control packages**,
not 24 independent units. This is a sensible bounded development study and
matches the maximum reviewer package pool already planned for branch A. It
cannot guarantee that the reviewer sets are usable: failed replay, unacceptable
intact work or unplantable flaws reduce E*; missing reviews reduce n_S/n_A.

Carry forward the existing requirements E* ≥ 6, n_S ≥ 6, n_A ≥ 6, and C ≥ 0.8
in both arms. If they fail, report insufficient reviewer evidence/instrument
repair and stop; do not promise that branch B will answer checkability. Do not
replace exclusions or add trials until a result appears. With all 12 pairs,
one package is 8.33 percentage points and two packages are 16.67 points; at
six pairs these are 16.67 and 33.33 points. This is development-scale resolution.

The existing decision table cannot be reused unchanged: it needs D and ΔT,
which branch B does not observe, and rule 2 stops on a pilot ceiling before
its auditability rule. Do not substitute calibration D or set ΔT = 0. Write
a branch-B table now: infrastructure/eligibility gates; observed control harm;
conditional auditability development signal versus inconclusive result; and
separate descriptive R/cost outcomes. A practical R gain threshold is needed
only if it will drive an expansion decision. Otherwise label it descriptive.
No claim of correctness equivalence or general reviewer advantage follows.

### 4. A complete recalibration outcome rule

The ≥7/8 rule is clear for eight observed direct answers, but “direct ≤6 of 8”
is not sufficient to enter branch A when calibration stops early, suffers
infrastructure failures or produces unresolved adjudications. Freeze a complete
routing rule before live recalibration: route only after the planned direct
outcomes are available and adjudicated, or explicitly stop as incomplete.
Do not count missing trials as evidence of scientific difficulty. There must
be no automatic extra round or pilot launch after an infrastructure halt.

Clarify the two freeze points. Materials, prompts, tooling, the branch rule,
R definition and eligibility must be fixed before recalibration; the final
pilot plan may then fill in its cost ceiling from the observed median. Proposal
line 166 allows threshold changes after recalibration while lines 247–248 say
the pilot uses exactly the same freeze. The earlier plan explicitly allowed
calibration-informed efficacy thresholds, so this is not a newly discovered
historical violation. Nevertheless, precommitting scientific decision thresholds
now is preferable; any retained development-stage adjustment must be declared
as such and cannot alter the already-used branching rule retrospectively.

## Requirements to preserve in the offline build

- **Numerical witnesses and sufficiency witnesses do different jobs.** A
  delegate following a supplied analysis specification can independently check
  arithmetic but may inherit the author's choice of preprocessing. The cue/
  sufficiency witness should first infer a defensible analysis plan from the
  same materials available to the analyst, without the hidden solution or
  author-selected preprocessing instructions. Freeze that record before giving
  it the numerical specification; retain disagreements and equivalent answers.
- **Controls are substantive.** Preserve unchanged information availability,
  task scale and provenance structure across each trap/control pair. Resolve
  the harmful condition without inserting an explicit remedy. Validate the
  control's innocuous irregularities and every revised flaw's propagation in
  both package forms. Separate calibration seeds do not make generator-level
  design choices independent; keep the development history and untouched
  pilot instances explicit.
- **Small controls are not another live round.** The 16-trial recalibration
  remains eight trap instances by two arms. Inspecting matched controls and
  testing scorer harm cases offline is necessary; it need not enlarge live
  calibration. Control harm is then observed in the pilot/branch-B trials.

## Cost target: retain as engineering, not as an efficacy claim

A 40% reduction in returned bytes is a useful engineering target, but there
is no demonstrated conversion from that percentage to K. The fixed historical
call sequence is not a counterfactual agent policy: compact schemas and
summaries may require extra discovery/result calls. A replay that simply drops
fields can achieve the target while making the new interface more expensive
to use.

Measure both exact-call response bytes and the calls/bytes needed to recover
the same task-relevant fields. Include errors/refusals and preserve schema,
scientific scope and diagnostics. Treat this as an offline interface measure,
with live counted tokens, cache reads, call counts and K reported separately.
Revise the destination promising that context cost “no longer doubles” tokens
to a measured reduction target; only new observed trials can establish their
K. No extra live benchmark allocation is required to make this distinction.

## Disposition

Accept offline bank repair, equivalent executable packages, compact discovery,
explicit delimited input, existing-record replay, the 96-trial/two-session cap,
and a single bounded recalibration subject to the existing approval gate.
Require the four design corrections above before considering the plan settled.
Branch B's 24 trials are adequate for the proposed bounded descriptive exercise,
not a guarantee of an interpretable reviewer contrast or a definitive efficacy
finding. The real-data stretch should remain outside the acceptance criteria.
