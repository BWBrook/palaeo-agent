# Sprints 3 and 4: agent integration and a test of scientific value

**Revised by Claude, 31 October 2026, from Codex's draft (`679302f`).** Codex
proposed and Claude critiqued and revised, as Barry instructed. Implementation
starts when Codex accepts this revision or the agents settle any disagreement
on Board thread 103. Claude's changes are listed under
[Revision record](#revision-record). These are the next two sprints, numbered
3–4 to keep them distinct from the completed pair.

Barry's instruction in Codex chat: "You propose the next two sprint plans
(try to be even more ambitious than last time with these), and Claude critiques
and updates them. Then you implement sprint 1, after which Claude critiques
and does sprint 2, and then you critique. Reverse order!"

Sequence: **Codex proposal → Claude critique/revision → Codex sprint 3 →
Claude critique/fix → Claude sprint 4 (with a Codex pre-freeze review gate) →
Codex critique/fix → reconciliation.** The two sprints run one after the
other. Delegates may handle bounded work within the current owner's sprint;
ownership never passes by silence.

## Destination

Move from validated numerical operations to a usable scientific agent tool
whose practical value can be measured. At the end we should have:

1. An agent-facing transport that uses the same validated Python engine and
   returns compact, inspectable evidence.
2. A replacement evaluation system in which the worker's tools cannot reach
   the model client's credentials, user state, keys, the network or another
   trial, and in which every tool call is recorded.
3. A reproducible multi-step study bundle that another agent can inspect and
   rerun without the original chat or its own numerical code.
4. A bounded paired pilot and reviewer experiment that can find an advantage,
   no advantage or a disadvantage, and an explicit decision about what to
   develop next.

The [previous reconciliation](sprints-1-2-reconciliation.md) remains binding:

- historical records stay intact;
- the old launcher stays disabled;
- no efficacy claim follows from the old smokes.

Private development and reversible pushes remain authorised. A first public
release, publication and spending beyond existing resources are outside this
programme.

## Sprint 3 — Codex: usable agent tools and trustworthy execution

**Goal:** an agent can discover, execute, inspect and reproduce supported
analyses through a small transport, inside a demonstrably separated trial
environment. The sprint must end in a working end-to-end demonstration, not
only an infrastructure design.

### Product deliverables

- One thin local stdio MCP server, built on the maintained MCP Python SDK, for
  the existing method catalogue, validation, execution, inspection,
  reproduction and descriptive comparison.
  - Request schemas derive from the existing typed specifications.
  - Numerical logic stays in the library.
  - Python and the CLI remain fully usable without MCP.
- Concise method summaries and structured errors. Large tables are selected or
  paginated rather than resent. Artifact references are confined to the
  session's permitted roots; the transport offers no arbitrary path access.
- Runnable examples for RMA, community analysis and declared PERMANOVA,
  including an unsupported-design refusal and a fresh-process reproduction.
  Document the small capability surface an agent actually needs.
- Automated protocol tests:
  - Python, CLI and MCP give equivalent outcomes;
  - malformed requests;
  - artifact-root boundaries;
  - interrupted runs.
- No GUI, hosted service or transport polish beyond this list. Pagination
  beyond the simplest form is the first thing to cut under pressure.

### Evaluation deliverables

**The diagnosis.** The old design wrapped the whole agent CLI in one sandbox
profile. Whatever the CLI needed, its tools could also reach: authentication,
Keychains, Preferences and the network. A profile around the CLI cannot fix
that. The boundary has to sit between the model client and the commands it
runs.

**Preferred architecture, to be verified.** An authenticated supervisor
process (the agent CLI) has its built-in shell and file tools disabled. Its
only tools come from a small worker-execution MCP server. That server runs
each command, file read and file write under a per-call confinement:

- no credentials, Keychains or Preferences;
- no network;
- reads limited to the trial directory and the arm runtime;
- writes limited to the trial directory;
- trial-local `HOME`, `TMPDIR` and cache directories.

On macOS this is `sandbox-exec` per call with a deny-network rule, which the
old CLI-wide profile could not apply. On Linux it is bubblewrap or a
disposable unprivileged user. The toolkit arm's palaeo MCP server runs inside
the same worker confinement. This design has three advantages:

- the network can be denied, because model traffic leaves from the
  supervisor, not the worker;
- every tool call is logged by our own server, which gives the
  toolkit-use measure sprint 4 needs;
- it is independent of the backend, so a Claude backend later costs only a
  launch adapter.

**Readiness evidence.** Codex CLI 0.166.0 lists `shell_tool` and
`unified_exec` as stable features that can be disabled. With
`--ignore-user-config`, the defaults also enable `browser_use`,
`computer_use` and `apps`. A read-only check is enough to see the flags. Whether
disabling them leaves only MCP tools, and whether `apply_patch` or any other
built-in still writes files from the supervisor, must be confirmed by a probe
before the design is adopted.

**Requirements for whichever design is chosen:**

- **Tool inventory.** Freeze the model-visible tool list per backend and arm,
  record it at every launch from the client's own initialisation record, and
  refuse to launch if it differs. A tool the model can see but the boundary
  does not confine fails the boundary.
- **Fallbacks.** If the CLI cannot be reduced to MCP-only tools, use a
  disposable account or VM, or a provider-supported client boundary. Do not
  copy personal authentication into a tool-readable directory, alter personal
  credentials, install a heavyweight runtime, build a general agent framework
  or assume an SDK or API credential exists.
- **Host.** Choose the execution host after read-only readiness checks. The
  MacBook sleeps and has 8 GB of RAM; the always-on `mini`, or `nectar` under
  its operating policy, is the likely host for sprint 4's long runs. Record the
  decision and its tested limits before any live trial.
- **Arm equivalence.** Both arms receive identical task materials, scientific
  dependencies, execution tools, limits and permitted references. Only the
  toolkit wheel, its discovery output and the palaeo MCP server differ.
- **Fingerprints.** Pin, for every launch:
  - the complete installed-package manifest per arm;
  - source;
  - inputs;
  - prompt;
  - tool inventory;
  - transport;
  - model request;
  - runner.
- **Probes.** Use synthetic secrets and canaries, through the actual tool path,
  for both arms. They cover:
  - credentials, Keychains and Preferences;
  - agent state;
  - the checkout and keys;
  - other trials;
  - mutation of the runtime;
  - symlink escapes;
  - writes outside the trial;
  - network attempts.

  Test contamination by running a fresh second trial after the first has tried
  to persist state. Record supervisor permissions separately from worker
  permissions.
- **Run discipline.**
  - Enforce deadlines and no retries.
  - Preserve failed and partial trials, and any trial whose usage is unknown.
  - No new trial starts if usage accounting is unavailable.
  - A token ceiling is a launch-stop rule with possible overshoot by the last
    trial, not a hard provider quota.
  - Frozen plans and results cannot be replaced.

**Acceptance:**

1. Protocol equivalence and the offline adversarial probes pass.
2. Then at most **8 development integration trials**:
   - Codex resources only;
   - **5 minutes** each;
   - **200,000 counted uncached-input-plus-output tokens** in aggregate;
   - no retries;
   - they must include a successful numerical execution, a structured refusal
     and a saved-bundle reproduction.
3. Claude reviews the execution boundary before any scientific pilot use.

These are integration tests, not evidence of scientific superiority. A
passing numerical run and a correctly blocked attempt are different outcomes.

**Handoff:**

- the implementation commit;
- complete runtime and permission evidence;
- the frozen tool inventories;
- observed client-call records;
- preserved failures;
- an explicit recommendation on readiness for sprint 4.

Claude critiques and fixes sprint 3 before accepting the handoff. If the
boundary cannot be demonstrated, the live-evaluation hold stays. Sprint 4's
offline product and bank work can proceed, but no pilot launches.

**Ownership:** Codex owns the MCP server, the replacement executor and their
tests, examples and documentation. Existing frozen evaluation records are
read-only. No new estimators, and no change to the PERMANOVA contract.

## Sprint 4 — Claude: reproducible studies and a discriminating pilot

**Goal:** agents complete realistic multi-step work, and independent reviewers
can assess the evidence it produces. Measure errors, checking and cost rather
than assuming that successful execution or a fuller manifest is the benefit.

### Product deliverables, completed before the pilot freeze

- A bounded **study bundle** that composes existing run specifications and
  declared input preparations. It uses ordinary Python orchestration and a
  simple manifest: no DAG language, scheduler or plugin system. Two concrete
  recipes:
  - community description → ordination → supported group comparison;
  - a measurement analysis with an explicitly declared transformation and
    exclusion decision.
- **A closed set of preparation operations, each a pure function with a typed
  record and an independent test oracle:**
  - an exact ID join between matrix and metadata;
  - explicit sample selection and exclusion with a stated reason;
  - a declared orientation;
  - an explicit taxon-label mapping with merge-by-sum;
  - a declared transformation, which refuses invalid values rather than
    replacing them.

  Nothing is inferred: no merges, missing-value replacements or sampling
  independence. An operation outside this set needs a revision record.
- Inspect and reproduce a whole study from its saved inputs and
  specifications.
  - A partial failure names the failed step, preserves the evidence and does
    not mark the study complete.
  - Compared results require matching provenance.
  - No inferential sensitivity testing is added by accident.
- A factual study report that links each numerical claim to result fields,
  declared assumptions and diagnostics.
- Expose study operations through the sprint-3 MCP server, coordinated with
  Codex.
- Demonstrate one reference-corpus workflow and one realistic synthetic
  example. Verify the numbers independently, and verify the saved study in a
  fresh process.

### Evaluation design

**Bank.** Author **12 trap/control pairs (24 items)**. The families span:

- alignment and orientation;
- count and proportion semantics;
- missingness;
- label resolution and exclusions;
- sampling design;
- transformation;
- interpretation.

Construction rules:

- Several items combine two or more steps. Vary dimensionality, group sizes,
  noise and effect strengths.
- At least 4 items build on real data from the repository's reference corpus,
  such as the PAST captures, where provenance allows. The rest are seeded and
  synthetic.
- **The bank must not be stacked.** Prespecify for each family whether the
  toolkit's declarations bear on it. Aim for about half that do and half that
  do not (interpretation, for example). Report the two strata separately.
- **Uncoached but sufficient.** Dictionaries state the scientific facts;
  task texts never state their consequences. Every trap carries a written
  *sufficiency witness*: a derivation showing that the stated facts entail the
  correct handling. An item that fails this is underdetermined, not a trap.
  Underdetermined items carry an explicit non-identifiability witness, as D2
  now does. A dictated exclusion is a control, as D7-control is.
- **Controls are ordinary, difficult clean analyses,** not obvious refusal
  targets. They measure false refusals and over-caution, which a strict
  toolkit could cause.
- **Independent keys.** Codex, or a Codex delegate, recomputes every key from
  the materials alone before freeze, without reading Claude's key code.

**Calibration before freeze.** Sprint 1 showed that frontier agents handle
traps whose consequences the materials spell out. To avoid a second ceiling,
run up to **16 calibration trials** (8 trap instances × 2 arms) on a disjoint
calibration set. It comes from the same family generators with different
seeds and parameters. Calibration may lead to revised generators and
thresholds; nothing from it enters the pilot data. Pilot items are never
selected by how agents performed on them, which would bias the comparison
towards whichever arm the selection favoured. If the direct arm gets at least
7 of 8 calibration traps right, the families are revised before freeze.

**Arms.**

- Choose one execution interface for the toolkit arm and freeze it: the palaeo
  MCP server if sprint 3 delivers it, otherwise the Python API with run
  records.
- Require toolkit use for supported numerical operations, and allow
  equivalent documented preparation in both arms.
- Measure adherence from the tool-call logs. Report non-adherence separately,
  and keep the assigned-arm result in the primary comparison.
- Capability disclosure, including the refusals the discovery index lists, is
  part of the intervention, not secret information. Interpretation must
  separate enforcement and disclosure from mathematical accuracy.

**Analyst trials.**

- **24 items × 2 arms × 2 independent sessions = 96 trials** on one frozen
  Codex model and effort.
- Randomise order within complete blocks: one item pair × both arms × one
  session = 4 trials. A launch-stop then leaves balanced data.
- Sessions are isolated.
- Freeze the scorer, bank, code, analysis rules, thresholds and plan before
  the first trial. Do not revise items or retry failures after outcomes
  appear.

**Reviewer trials: 48.**

- **Eligibility, fixed in advance.** Use the 12 *control* items' packages from
  analyst session 1, in both arms: 12 items × 2 formats × intact/flawed = 48.
  - Controls are chosen because analysts are more likely to be right on them,
    so an intact package is more likely to be correct. Each intact package's
    reference verdict still comes from the key, not from its origin.
  - If either arm's package for an item is missing or invalid, that pair is
    recorded as ineligible and not run, and no substitute is chosen.
- **Matched flaws.** Plant the same scientific mistake in both formats of an
  item:
  - 6 in preparation (ID assignment, exclusion, label merge, orientation);
  - 3 in design or inference (for example, pseudoreplicated units);
  - 3 in interpretation (for example, a conclusion that descriptive
    dispersion does not support).
- **Each flaw must look like an honest upstream mistake.** Apply it at the
  step where it would arise, then regenerate everything downstream
  consistently: rerun the package's own script or study specification where
  one exists; otherwise recompute with the reference implementation and edit
  every reported number. Hashes, manifests and reports must agree.
  - Validity check: the package's own integrity verification (hashes, schema,
    `inspect`) must pass on every flawed variant. A flaw that an integrity
    check catches is invalid, because it would credit checksums rather than
    reviewability.
  - Each flaw changes a reported number beyond tolerance, or the scientific
    conclusion.
  - Each flaw carries a *detectability witness*: the route by which a reviewer
    with the task, data and evidence could find it.
- **Reviewer conditions.**
  - Reviewers get the task, data and evidence package, with no transcript, key
    or flaw label.
  - Their environment is identical for both formats and includes the toolkit,
    so a reviewer can rerun a direct script or reproduce a bundle. The format
    is the only difference.
  - Fix each reference verdict before review.
  - Record detection, false accusations, localisation and checking cost.
- Bundle format prevents complete arm blinding, and same-family reviewers
  limit the inference. Report both limitations.

**Resource envelope:**

| Budget line | Trials | Deadline | Counted-token ceiling |
| --- | ---: | ---: | --- |
| Calibration | at most 16 | 10 min | 600,000 |
| Analysts | 96 | 10 min | set at freeze (below) |
| Reviewers | 48 | 5 min | set at freeze (below) |
| **Codex total** | **at most 160** | | analysts + reviewers capped at **6,000,000** |
| Sonnet 5.5 reviewer replicate | 48 | 5 min | 1,500,000 Claude counted (separate) |

- **Why not Codex's 4,000,000.** Sprint-1 and sprint-2 Codex trials used about
  9,000–22,000 counted tokens on toy items. Harder multi-step items in 10
  minutes plausibly use 30,000–50,000, which puts 96 analysts alone near 4
  million. Instead, set the analyst and reviewer ceilings at freeze as 1.5 ×
  the calibration median × the trial count, never above the 6 million cap.
- Accounting is separate for analysts and reviewers, with no retries.
- Analyst, calibration and primary reviewer trials use Barry's Codex
  resources. Barry has authorised one Anthropic addition: a replicate of the
  48 reviewer trials on Claude Sonnet 5.5 (see the revision record).
- Claude owns scientific design, interpretation and integration, and
  delegates mechanically checkable work to Codex.
- Freeze the actual model, configuration and accounting at launch; an obsolete
  model name is not a requirement. Choose concurrency from measured host
  capacity.

### Pre-freeze review gate

Before the pilot freezes, Codex reviews:

- the study-bundle layer, which is the intervention;
- the bank, its sufficiency and non-identifiability witnesses, and the keys,
  recomputed independently;
- the flaw set and its integrity and detectability checks;
- the scorer amendment;
- the thresholds;
- the protocol.

Claude resolves or records each finding before freeze. This gate replaces
nothing in the post-sprint critique. It exists because a frozen pilot built on
an intervention nobody else has reviewed would waste the run.

### Endpoints, thresholds and decision

**Primary endpoint:** on trap items, the paired item-level difference in
*acceptable* outcomes (correct, or correctly unresolved), averaged over the two
sessions.

**Co-primary safety endpoint:** on controls, the difference in false refusals
plus wrong answers.

**Secondary endpoints:**

- evidence completeness and actual reproduction;
- reviewer sensitivity, false-accusation rate and localisation;
- tokens and time;
- adherence.

Sessions and flaw variants are clustered within items and original packages.
Report bootstrap intervals that resample items, not trials, and preserve
every failure.

**Provisional thresholds,** fixed after calibration and before freeze. A
change made at calibration is recorded with its reason; none may be made after
freeze.

| Decision | Rule |
| --- | --- |
| **Expand** | All of: (1) the toolkit raises trap acceptability by at least 0.15 absolute, with the item-bootstrap 80% interval above 0; (2) control false refusals plus wrong answers rise by no more than 0.05; (3) reviewer detection of flaws in toolkit packages is no worse than in direct packages, by more than 1 of 12; (4) the median counted-token ratio, toolkit to direct, is at most 2.0. |
| **Repair** | A benefit on one axis (correctness or reviewability) with a cost or safety rule failed. Or a benefit confined to the stratum where toolkit declarations bear directly, which is read as enforcement working and calls for broader coverage rather than expansion. |
| **Stop this design** | The direct arm reaches at least 0.90 acceptability on traps, so the bank cannot discriminate; or the toolkit is worse on the primary or safety endpoint by the same margins. |

A null or adverse result completes the sprint. Trials are never added until
an advantage appears.

**Deliverables:**

- the study API;
- complete trial and audit evidence;
- a paper-shaped technical report with reproducible tables, stating the
  strongest claim this development pilot supports;
- a full account of the roles of the AI systems, by name and version.

There is no public submission and no confirmatory efficacy claim. Codex then
critiques and fixes Claude's sprint, and both reconcile.

**Ownership:** Claude owns the study-bundle layer, the new bank and scoring
amendment, the pilot protocol and the synthesis. Sprint-3 executor fixes are
coordinated with Codex and need a re-freeze before any affected trial. A
material defect found during a frozen run stops launches and preserves the
affected version.

## Revision record

Claude's answers to Codex's five questions, and the other changes.

1. **Can sprint 3 do both without becoming an infrastructure project?** Yes,
   if the isolation boundary *is* an MCP server. A worker-execution server
   with per-call confinement solves credentials and network together, gives
   the instrumented tool logs sprint 4 needs, and shares its plumbing with the
   palaeo transport. Added the explicit diagnosis, the preferred architecture,
   the readiness evidence (Codex's `shell_tool`/`unified_exec` flags, and
   `browser_use`/`computer_use`/`apps` on by default), and a frozen
   tool-inventory requirement. Cut point: transport polish, never isolation.
2. **Is the study bundle small and useful?** Yes, once preparation is a closed
   list of five operations, each with a typed record and an independent
   oracle. Vague steps are out by construction. Study operations are added to
   the MCP server.
3. **Are 96 + 48 trials proportionate?** Kept both, and so kept reviewability.
   Added at most 16 calibration trials on a disjoint set, because the
   largest risk is another ceiling. Added balanced blocks, so that a stop
   leaves usable data. Raised the cap to 6 million counted tokens, with the
   working ceiling derived from calibration; 4 million looked short for
   10-minute multi-step trials.
4. **Are the flaw injections and eligibility rules defensible?** Only with
   three rules, now required:
   - flaws are regenerated consistently and must pass the package's own
     integrity checks, otherwise the toolkit is credited for checksums;
   - each flaw has a detectability witness;
   - reviewers work in an identical environment for both formats.

   Eligibility is the control items' session-1 packages, with matched pairs
   dropped rather than substituted. Flaws are split 6/3/3 across preparation,
   design and interpretation.
5. **Which thresholds justify expansion?** Concrete provisional thresholds
   above, fixed at calibration and frozen with the plan. They include a
   control-safety rule and a cost rule, and treat a benefit confined to
   enforcement as a reason to repair, not to expand.

Other changes:

- **Bank validity:** sufficiency witnesses for traps; a prespecified split
  between items the toolkit addresses and items it does not; at least 4
  items from real data; keys recomputed independently by Codex.
- **Sequence:** a Codex pre-freeze review gate inside sprint 4.
- **Endpoints:** a primary endpoint, a co-primary safety endpoint, and
  bootstrap intervals that resample items.

**Authorised by Barry: a Sonnet 5.5 reviewer replicate.** Asked in Claude
chat on 31 October 2026, "Authorise the optional 48-trial Sonnet 5.5
reviewer replicate in sprint 4?", Barry answered: "Yes, authorise it".

- The replicate reruns the same 48 reviewer packages, with the same reference
  verdicts and the same environment, on `claude-sonnet-5-5`.
- It tests whether reviewability holds beyond the analysts' own model family.
  It is reported as a second reviewer population, not pooled with the Codex
  reviewers.
- It needs a Claude launch adapter for the sprint-3 boundary. That adapter is
  built and probed in sprint 4, by Claude, against the same tool-inventory and
  canary requirements.
- It runs under a separate launch-stop ceiling of 1,500,000 counted Claude
  tokens (input, cache-creation input and output, with cache reads reported
  separately), the same ceiling as the earlier Sonnet smoke.
- No other Anthropic trial spending is authorised.

**Not changed, and agreed:**

- Codex-only trials by default;
- no new numerical-method family;
- no public release;
- the extreme-F limit stays explicit;
- the old launcher stays disabled;
- these are development items, not held-out confirmatory evidence.
