# Sprints 3 and 4: agent integration and a test of scientific value

**Draft for Claude's critique and revision, 31 October 2026.** Codex proposes;
implementation starts after Claude updates the plan and the agents resolve
material disagreements. These are the next two sprints, numbered 3–4 to avoid
confusion with the completed pair.

Barry's instruction in Codex chat: "You propose the next two sprint plans
(try to be even more ambitious than last time with these), and Claude critiques
and updates them. Then you implement sprint 1, after which Claude critiques
and does sprint 2, and then you critique. Reverse order!"

Sequence: **Codex proposal → Claude critique/revision → Codex sprint 3 →
Claude critique/fix → Claude sprint 4 → Codex critique/fix → reconciliation.**
The two sprints execute sequentially. Delegates may handle bounded work within
the current owner's sprint; ownership does not pass by silence.

## Destination

Move from validated numerical operations to a usable scientific agent tool
whose practical value can be measured. At the end we should have:

1. An agent-facing transport that uses the same validated Python engine and
   returns compact, inspectable evidence.
2. A replacement evaluation system whose worker tools cannot reach the model
   client's credentials, user state, keys or another trial.
3. A reproducible multi-step study bundle that another agent can inspect and
   rerun without the original chat or bespoke numerical implementation.
4. A bounded paired pilot and reviewer experiment capable of finding an
   advantage, no advantage or a disadvantage, with an explicit decision about
   what to develop next.

The [previous reconciliation](sprints-1-2-reconciliation.md) remains binding:
historical records stay intact; the old launcher stays disabled; no efficacy
claim follows from the old smokes. Private development and reversible pushes
remain authorised. First public release, publication and external spending
beyond existing resources remain outside this programme.

## Sprint 3 — Codex: usable agent tools and trustworthy execution

**Goal:** an agent can discover, execute, inspect and reproduce supported
analyses through a small transport, inside a demonstrably separated trial
environment. This sprint earns a working end-to-end demonstration, not just
an infrastructure design.

### Product deliverables

- Add one thin local stdio MCP adapter for the existing method catalogue,
  validation, execution, inspection, reproduction and descriptive comparison.
  Request schemas derive from existing typed specifications; numerical logic
  stays in the library. Python and CLI remain fully usable without MCP.
- Return concise method summaries and structured errors; paginate or select
  large tables rather than repeatedly sending discovery schemas and arrays.
  Artifact references must be constrained to the session's permitted roots;
  arbitrary path traversal is not a transport capability.
- Ship runnable examples for RMA, community analysis and declared PERMANOVA,
  including an unsupported-design response and a fresh-process reproduction.
  Document the small capability surface an agent actually needs.
- Demonstrate the adapter with a real client and record the observed calls.
  Automated protocol tests cover equivalent Python/CLI/MCP outcomes, malformed
  requests, artifact boundaries and interrupted runs. No GUI or hosted service.

### Evaluation deliverables

- Replace the old executor with a supervisor/worker separation. Authentication
  and model-client state belong outside the scientific worker's accessible
  filesystem and privileges. Copying personal authentication into another
  tool-readable directory does not satisfy this requirement.
- Start with the smallest demonstrable implementation. Preferred design is an
  authenticated supervisor dispatching tool operations to a disposable worker
  with no credentials and denied network egress. A CLI backend is acceptable
  only if every file/code tool is actually confined to that worker boundary.
  If the installed clients cannot provide this, use a suitable disposable
  account/VM or a provider-supported client boundary. Do not build a general
  agent framework or assume an SDK/API credential is already available.
- Decide the execution host after read-only readiness checks. Local work stays
  small; authorised Linux jobs use Nectar under its current operating policy.
  Do not install a heavyweight runtime or alter personal credentials merely
  to preserve an initially preferred design. Record the architecture decision
  and its tested limits before live trials.
- Both arms receive identical task materials, scientific dependencies, shell
  capabilities, limits and permitted references. Only toolkit installation,
  discovery and its transport differ. Instrumented tool calls make actual
  toolkit use observable. Pin complete installed-package manifests, source,
  input, prompt, transport, model request and runner fingerprints per launch.
- Probe both backends/arms for credentials, keychain/preferences, agent state,
  checkout/keys, other trials, runtime mutation, symlink escapes, outside
  writes and network attempts. Use synthetic secrets and canaries. Test
  contamination by running a second fresh trial after the first tries to
  persist state. Probe the actual tool-execution path, not only a standalone
  sandbox shell. Record supervisor permissions separately from worker ones.
- Enforce deadlines and no retries; preserve failed/partial trials and unknown
  usage. No new trial starts if usage accounting is unavailable. A token
  ceiling is a launch-stop rule with possible last-trial overshoot, not an
  asserted hard provider quota. Refuse replacement of frozen plans/results.

**Acceptance:** protocol equivalence and offline adversarial probes pass;
Claude reviews the execution boundary before scientific pilot use. After
those checks, at most **8 development integration trials**, Codex resources
only, at most **5 minutes each** and **200,000 counted uncached-input-plus-output
tokens in aggregate**, no retries. Include successful numerical execution,
structured refusal and saved-bundle reproduction. These are integration tests,
not evidence of scientific superiority. Passing numerical runs and correctly
blocked attempts are distinct outcomes.

**Handoff:** implementation commit, complete runtime/permission evidence,
observed client-call records, preserved failures and an explicit recommendation
on readiness for sprint 4. Claude critiques/fixes sprint 3 before accepting that
handoff. If the boundary cannot be demonstrated, the live-evaluation hold
persists; sprint 4's offline product/bank work can proceed, but no pilot launches.

**Ownership:** Codex owns the adapter, replacement executor and their tests,
examples and documentation. Existing frozen evaluation records are read-only.
Avoid new estimators or changing the PERMANOVA contract in this sprint.

## Sprint 4 — Claude: reproducible studies and a discriminating pilot

**Goal:** agents complete realistic multi-step work, and independent reviewers
can assess the resulting evidence. Measure errors, checking and cost, rather
than assuming that successful execution or a fuller manifest is the benefit.

### Product deliverables, completed before pilot freeze

- Add a bounded **study bundle** composing existing run specifications and
  declared input preparations. Begin with two concrete recipes: community
  description → ordination → supported group comparison; and a measurement
  analysis with an explicitly declared transformation/exclusion decision.
  Use ordinary Python orchestration and a simple manifest, not a general DAG
  language, scheduler or plugin system.
- Capture raw inputs, exact ID joins, every declared exclusion/transformation,
  derived inputs and constituent run identities. Support explicit sample
  selection and taxon-label mappings when supplied by the analyst; never
  infer merges, missing-value replacements or sampling independence.
- Inspect/reproduce the whole study from its saved inputs and specifications.
  Partial failure identifies the failed step and preserves evidence without
  labelling the study complete. Require matching provenance where results are
  compared. Do not add inferential sensitivity testing by accident.
- Produce a factual study report linking numerical claims to result fields,
  declared assumptions and diagnostics. Demonstrate one reference-corpus
  workflow and one realistic synthetic example. Verify numerical outputs
  independently and verify the saved study in a fresh process.

### Evaluation design

- Author **12 trap/control pairs (24 items)** spanning alignment, orientation,
  count/proportion semantics, missingness, label resolution, exclusions,
  sampling design, transformation and interpretation. Several must combine
  two or more steps; vary dimensionality, group sizes and effect strengths.
  Include ordinary difficult clean cases, not just obvious refusal targets.
- State the scientific facts in dictionaries without supplying their
  consequences in task instructions. A dictated exclusion is a control, as
  D7-control now is. Include explicit non-identifiability witnesses for
  underdetermined material and independent keys for every supported estimand.
  Codex critiques keys, difficulty and scorer validity before any live result
  is inspected. These openly reviewed items are development material, not a
  held-out confirmatory set.
- Choose one execution interface for the toolkit arm and freeze it. Require
  toolkit use for supported numerical operations; allow equivalent documented
  preparation in both arms. Record non-adherence separately and retain the
  assigned-arm result in the primary comparison. Capability disclosure is part
  of the intervention, not secret information. Interpretation of an observed
  benefit must distinguish enforcement/disclosure from mathematical accuracy.
- Run **24 items × 2 arms × 2 independent sessions = 96 analyst trials** on
  one frozen Codex model/effort. Randomise execution order and keep sessions
  isolated. Freeze the scorer, bank, code, analysis rules and plan before the
  first trial; do not revise items or retry failures after outcomes appear.
- Add **48 reviewer trials**: choose a preregistered subset of 12 paired
  direct/toolkit evidence packages from the first analyst replicate, and make
  an intact and a deliberately flawed variant of each. The selection rule is
  fixed before seeing outcomes. Label intact origin separately from verified
  correctness: an analyst's original output may itself contain errors.
  If a prespecified eligible package is missing/invalid, record that failure
  under the frozen rule rather than quietly substituting an easier one.
- Plant matched scientific mistakes in both formats: e.g. wrong ID assignment
  or a conclusion unsupported by the design. Do not make every error merely
  a broken checksum. Supply the reviewer with task/data/evidence but no agent
  transcript, key or injected-error label. Fix the reference verdict before
  review. Record detection, false accusations, localisation and checking cost.
  Bundle format prevents complete arm blinding; reviewers from the same model
  family also limit the inference. Report both limitations.

**Proposed resource envelope for Claude to critique:** at most **144 sessions**
total; analyst deadlines **10 minutes**, reviewer deadlines **5 minutes**;
aggregate launch-stop ceiling **4 million counted uncached-input-plus-output
tokens**, with separate analyst/reviewer accounting and no retries. All trial
actors/reviewers use Barry's Codex resources. Claude owns scientific design,
interpretation and integration and may delegate mechanically checkable work
to Codex. This draft authorises no new Anthropic trial expenditure. Actual
model/configuration and valid accounting must be frozen at launch; an obsolete
model name is not a requirement. Choose concurrency from measured host capacity.

### Decision and acceptance

- Report paired item-level correctness, wrong answers, false refusals and
  failures separately; evidence completeness and actual reproduction; reviewer
  sensitivity/false-positive rate; tokens/time. Repeated sessions and injected
  variants are clustered within item/original artifact, not independent samples.
  Predeclare descriptive uncertainty summaries and preserve all failures.
- Make an explicit **expand / repair / stop this evaluation design** decision
  based on the joint correctness, reviewer and cost evidence. A null or adverse
  result is successful completion of the sprint. Do not keep adding trials
  until an advantage appears. Establish practical decision thresholds before
  launch, after offline calibration, not after seeing arm outcomes.
- Deliver the study API, complete trial/audit evidence and a paper-shaped
  technical report with reproducible tables and the strongest claim supported
  by this development pilot. No public submission or confirmatory efficacy
  claim. Codex then critiques/fixes Claude's sprint and both reconcile.

**Ownership:** Claude owns the study-bundle layer, new bank/scoring amendment,
pilot protocol and synthesis. Sprint-3 executor fixes are coordinated with
Codex and require re-freezing before any affected trial; a material defect
during a frozen run stops launch and preserves the affected version.

## Questions for Claude's critique

1. Can sprint 3 deliver both a thin MCP adapter and a verified execution
   boundary without turning into an infrastructure project? Cut optional
   transport polish before weakening isolation or evidence.
2. Is the study-bundle contract sufficiently small and scientifically useful?
   Challenge any preparation step whose semantics or independent oracle is vague.
3. Are 96 analyst plus 48 reviewer trials and the proposed ceiling proportionate?
   Reduce dimensions deliberately if needed; do not quietly discard reviewability,
   which is half the product question. A checklist-control arm is valuable but
   deferred to avoid expanding this already bounded pilot.
4. Are matched scientific-error injections and reviewer eligibility rules
   defensible? Freeze explicit examples and failure rules before launch.
5. Which practical benefit/cost thresholds would justify further expansion?
   Record disagreement rather than substituting a test-count target.

Claude should revise this document directly, post the changed scope and resolved
trade-offs on the new Board thread, and hand the agreed plan back to Codex.
