# Sprints 1 and 2

Status: **revised by Codex after critique, 31 October 2026; submitted to Claude
for acknowledgment and execution of sprint 1.** Claude proposed the draft at 1299297. The sequence and
scientific direction are accepted, with the scope and acceptance amendments
below. Neither implementation sprint has started.

Barry, 31 October 2026, Claude Code chat: "Let's step up the autonomy for the
next stage of development. My proposal: you and Codex agree on two sprints that
would substantively advance the work, after which you will counter-review each
other's work, in a follow-up handshake. The respective sprints can be isolated
(modular) from each other, or they can be sequential and progressively
dependent. Up to you; they'll be executed sequentially, regardless." He set the
order: Claude drafts, Codex critiques and revises, Claude runs sprint 1, Codex
runs sprint 2, Claude critiques and fixes sprint 2, Codex critiques and fixes
sprint 1, then both reconcile.

## Why these two

The vision's question asks whether the toolkit makes agent-led analysis more
correct, easier to check and easier to reproduce than direct scripting. After
four validation tranches, the numerics are well evidenced and the product
claim has no evidence at all, because no agent has been tested. The vision's
first useful capability is also incomplete: it ends with a group comparison
"only for a declared design whose permutation requirements the implementation
supports", and that comparison does not exist yet.

The two sprints are sequential and progressively dependent:

1. **Sprint 1 (Claude): build the measuring instrument.** This means a
   development item bank, an isolated trial runner, a frozen scorer and a
   feasibility smoke on the existing methods.
2. **Sprint 2 (Codex): build the first inferential method and put it through
   the instrument.** This is a declared one-way PERMANOVA with a descriptive dispersion
   diagnostic, validated against vegan, PAST and analytical cases, with
   group-comparison items added to the bank and smoked.

This order lets sprint 2 add a method, its validation and its agent-facing
traps in one pass. The sprint-1 smoke tests feasibility, not efficacy. An isolation/scoring
preflight must succeed before live trials; the later counter-review does not
replace that preflight. Final reconciliation precedes any larger pilot.

## Sprint 1 (Claude): evaluation instrument and feasibility smoke

Goal: run the development pilot described in [evaluation.md](evaluation.md),
at smoke scale, end to end, with every rule fixed before the first trial.

Deliverables:

1. **Item format and bank.** Each item directory holds `task.md`, input files,
   `dictionary.md` and a separate `key.json` with `provenance.json`. Cover
   catalogue items D1–D10 as trap and clean-twin pairs, plus underdetermined
   variants where the catalogue defines one (D2, D4 and probably D6). That
   gives roughly 22–23 items; enumerate the actual IDs rather than freezing an
   inconsistent count. Each clean task must be solvable through the current
   RMA/community API, with equivalent preprocessing allowed in both arms; do
   not make an unsupported estimator a clean completion target. Every key is computed without palaeo_agent, using
   exact rationals or the renv-locked vegan reference. Each key states the
   outcome category, the numbers with tolerances and the pitfall's failure
   signature.
2. **Answer contract.** Both arms write `answer.json` to a fixed schema:
   outcome claim, requested numbers, declared assumptions, exclusions with
   reasons and refusal reasons. A trial that does not write it scores
   `failed`. This makes the primary outcome machine-scorable in both arms
   without reading prose.
3. **Trial runner: Codex only.** One command builds a fresh workspace outside
   any checkout and launches the installed `codex exec`. A Claude runner is
   deferred. Both arms get identical scientific materials, dependencies,
   permissions and resource limits; only toolkit availability/discovery differ.
   The direct environment must fail to import the toolkit, including editable
   installs. Keys, generators, scored answers, other trials and the development
   checkout are outside the worker's readable filesystem. A fresh agent home,
   no MCP/Board/memory/plugins and an explicit environment are necessary but
   are not proof of filesystem isolation. Test the actual worker sandbox with
   synthetic outside-root canaries and key-path read attempts before any live
   trial. Audit approved runtime/library paths separately; transcript scanning
   detects some leaks and does not establish absence of leaks. If the Mac
   cannot enforce this, use an isolated runtime on an already authorised host;
   do not label an unrestricted run isolated. Preserve any failed preflight.

   Record model/effort as actually reported, CLI version, prompts, dependency
   lock, wheel/discovery hashes, configuration and effective permissions,
   usage events, timeout/termination reason, transcript and final workspace.
   Use a controller-enforced five-minute wall limit per trial, no spawned
   agents or recursive retries, and at most 14 initial trials. Set an aggregate
   reported-token stop ceiling of 300,000 before launching; if the backend
   reports usage only after a call, disclose possible one-call overshoot and
   rely on the wall limit for termination. Do not claim a hard token/turn limit
   that the installed CLI cannot enforce. Freeze the chosen model, effort and
   limits before the first trial; preserve timeout/missing-answer failures.
4. **Frozen scorer.** A script maps `answer.json` plus the key to the five
   outcomes, pitfall handling and spurious-warning counts. It also runs the
   evidence-completeness checklist over the final workspace. Scoring rules and
   the scorer's hash are committed before the first trial. A scorer unit test
   feeds synthetic answers covering each outcome, including a correct number
   reached by an undeclared guess on an underdetermined item, which must score
   `wrong`. Evidence that an agent actually followed a policy is distinct from
   an assertion in its answer. Flag unverifiable or ambiguous process claims
   for recorded adjudication; do not automatically certify them as correct.
   Use the same primary scientific scoring rules for both arms; native bundle
   completeness is a separate auditability measure.
5. **Hint audit.** Before pinning the wheel, check the discovery text and
   schemas for task-specific hints against the bank. Record findings; Codex
   owns any fix.
6. **Feasibility smoke.** Three trap and twin pairs (D1, D3, D6) plus one
   underdetermined item (D2), in the direct and toolkit arms, one replicate,
   with the Codex family as agent: 14 trials, on Codex tokens, in a fixed
   randomised order with no shared conversation or trial workspace. No tuning
   or retries during that frozen smoke; any subsequent amended smoke is
   versioned separately. No Claude-family trials in this sprint. The
   report is descriptive: whether items were read as intended, whether the
   scorer and runner worked, cost per trial, leak-scan results and what must
   change before the indicative pilot. No efficacy claim.

Ownership: `evaluation/**` (new: items, runner, scorer, schemas, smoke
outputs), `docs/evaluation.md` and a new `docs/evaluation-smoke-results.md`.
Wheel builds use the existing package unchanged; Claude edits no `src/**`.

Done when the scorer tests pass, every key is reproduced from its generator,
all smoke trials are preserved including failures, isolation/arm-equivalence
preflights pass, and the results document states what the smoke can and cannot
show. Freeze the scorer, bank and wheel in a private commit before the smoke;
the package source remains unchanged. Before handing off, Claude also freezes
the specification-independent sprint-2 reference fixtures described below,
posts their manifest hash and keeps their contents unavailable to Codex until
sprint 2 is implemented. The handoff identifies the sprint-1 commit, commands,
artifacts, unresolved issues and files released.

Out of scope: held-out set authoring, encryption and key custody, the
checklist arm, reviewer-agent auditability scoring (designed, not run),
confirmatory sizing.

## Sprint 2 (Codex): declared one-way group comparison

Goal: complete the vision's first useful capability with a permutation test
whose design requirements the toolkit enforces.

Deliverables:

1. **Method: free permutations only.** One categorical grouping factor,
   independent sampling units, no covariates, blocks, repeated measures or
   restricted permutations. Return pseudo-F, R², sums of squares and degrees
   of freedom using the existing declared distances and transformations.
   Metadata joins by exact sample ID. Require an explicit independent-unit
   design declaration; this records an assumption and cannot verify it from
   the table. Blocked/pseudoreplicated designs receive a structured unsupported
   response, not a claimed correction through shuffling rows within strata.
   Reuse count validation and distance construction independently of selected
   PCoA dimensions: inference must not depend on a plotting cutoff.

   Freeze a short method contract before inspecting comparator outputs:
   sums-of-squares formula, zero/nonpositive residual variation, negative
   eigenvalues, tie tolerance, permutation space and degeneracies. Preserve
   undefined permutation statistics rather than silently dropping/redrawing
   them; any refusal policy must avoid conditioning the reference distribution
   on a favourable subset. Use unique label allocations preserving group
   sizes for exact enumeration, include the observed allocation exactly once,
   and use count(T >= observed)/M. Enumerate when M-1 <= requested B and
   M <= 10,000; otherwise use Monte Carlo. Monte Carlo uses the predeclared sampling
   scheme and (b+1)/(B+1), with a recorded PCG64 seed and actual permutation
   schedule or its reproducible representation. Default B=999; cap B at 9999
   and exact enumeration at 10,000 allocations. Record the mode, admissible
   space size, requested/actual draws and counting denominator explicitly.
2. **Descriptive dispersion diagnostic, always reported.** Report per-sample
   and per-group distances to group centroids, explicitly using centroid
   rather than vegan's default spatial median, `bias.adjust=FALSE`, and no
   automatic distance correction. Match vegan's treatment of negative
   eigenvalues, recording negative squared distances, any zero truncations and
   their count. Explain the small-sample limitation and possible confounding
   of location and dispersion, especially with unequal group sizes. No
   dispersion p-value, PERMDISP claim or dispersion pass/fail threshold in
   this sprint. That second inferential method is deferred.
3. **Refusals.** Fewer than two groups, groups smaller than two, missing/empty
   group labels, unsupported dependent-unit designs, no admissible alternative
   allocation and undefined statistics under the frozen contract. Unequal
   group sizes are allowed and recorded. Do not infer exchangeability from
   labels, or claim that a non-significant dispersion result proves it.
4. **Run, inspect and reproduce.** Integrate the method with existing bundles,
   API/CLI discovery and saved-result validation, including the permutation
   record, resolved assumptions and RNG provenance. Leave sensitivity
   comparisons explicitly restricted to descriptive community runs: extending
   inferential sensitivity is a separate design task.
5. **Validation.** Analytical small-n cases with exact enumeration; vegan
   `adonis2` (F and R² to tolerance; p equal under exact enumeration and
   under an identical explicit schedule in Monte Carlo checks) and `betadisper(type="centroid", bias.adjust=FALSE)` distances;
   a native PAST 5.4
   one-way PERMANOVA capture on a grouped legacy or manual dataset that Codex
   identifies, with a prespecified permutation budget and recorded settings.
   Compare deterministic statistics to export precision; a PAST p-value is
   not an equality oracle without identical permutations. Use Monte Carlo
   uncertainty only as a separately declared stochastic check, following [the protocol](../references/past/protocol.md). The
   R script lives under `references/r/`. Codex may edit there for this sprint,
   and Claude reviews it.
6. **Instrument extension.** Add group-comparison trap and twin items to the
   sprint 1 bank. Examples: dispersion difference read as a location effect;
   pseudoreplicated subsamples that require an unsupported design response;
   group labels joined positionally. Freeze three trap/twin pairs, run the
   two arms once each (12 trials maximum), under the sprint-1 controls and
   resource ceilings, and retain every outcome. API-declared independence must
   not be mistaken for independently verified sampling independence.
7. **Deferred:** statistical axis-stability diagnostics and additional result
   fields. Keep both sprints focused on the instrument and group comparison.

Ownership: `src/**`, `tests/**` excluding sprint-1 evaluation tests, `scripts/**`,
`references/r/**` for the PERMANOVA reference, `references/past/captures/**`,
new items under `evaluation/items/**` and a results document.

Done when the full suite and CI pass, every validation comparison matches
under rules fixed before inspection, the smoke extension is preserved, and the
results document states its denominators.

Out of scope: restricted permutations, repeated/nested/two-way designs,
PERMDISP inference, inferential sensitivity comparisons, ANOSIM, pairwise
post-hoc tests, NMDS and the SMA slope test.

## Cross-review handshake

**Claude reviews sprint 2.**

- Adversarial code review.
- An independent recomputation of the vegan and PAST comparisons.
- A blind fixture round for the new method. Claude authors data and keys,
  including exact-enumeration p-values, in a specification-agnostic form
  outside the checkout, and posts their manifest hash on the Board *before
  Codex starts sprint 2*. After the API lands, a thin adapter maps fixtures to
  specifications. The adapter is disclosed with its own hash and cannot change
  any key.
- Claude may fix defects it finds, claiming files first. Changes to method
  semantics go back to Codex.

**Codex reviews sprint 1.**

- Recompute a sample of keys independently.
- Challenge the scoring rules and the answer contract for arm bias.
- Audit isolation and the leak scan, and repeat the hint audit.
- Rerun at least one smoke trial from its record.
- Codex may fix defects it finds, claiming files first.

**Reconcile.** Hold a joint Board discussion that settles each disagreement
or records it as open. Then write a short reconciliation document, together
with one chat summary per agent for Barry.

## Guardrails

- Commit and push at coherent states; CI stays green on main. Claim files on
  the Board before editing, as now.
- No held-out material is authored or seen. Everything in this sprint pair is
  development material.
- Only the bounded Codex-family smoke trials above are included. No new
  credentials, paid API setup, public release or Anthropic trial campaign is
  part of this plan.
- Results documents separate observed outcomes from interpretation, and make
  no efficacy claim.

## Codex critique and resolution

Keep the instrument-first order and PERMANOVA as the first group method.
Reduce sprint 1 to one runner backend. Reduce sprint 2 to free permutations,
explicit independent-unit assumptions and descriptive centroid dispersion.
Restricted randomisation is not a general cure for pseudoreplication, and a
second permutation test plus inferential sensitivity would make this sprint
substantially broader than one scientifically auditable method.

Compare Python and vegan permutation p-values with identical saved schedules,
not merely a broad Monte Carlo-error band. Treat centroid and spatial median
as distinct choices, and keep stochastic PAST checking separate from numeric
identity. Primary references: [adonis2](https://vegandevs.github.io/vegan/reference/adonis.html)
and [betadisper](https://vegandevs.github.io/vegan/reference/betadisper.html).

Local read-only CLI inspection: codex-cli 0.166.0 exposes `--ephemeral`,
`--ignore-user-config`, `--ignore-rules`, `--output-schema`, `--json`, `--cd`
and sandbox selection. Those flags alone do not prove a clean instruction or
filesystem boundary. The nested `codex sandbox macos --help` invocation was
blocked by this session's sandbox, so enforcement has not been verified here.
Sprint 1 must establish it in its actual runtime before live trials. See
[OpenAI security guidance](https://developers.openai.com/codex/security/);
record observed capability rather than assuming a CLI turn-limit flag.

On sprint-1 completion, Codex starts sprint 2 from the pinned handoff without
another scope-approval cycle. A short integrity/interface check at that handoff
is necessary; the substantive counter-reviews remain in Barry's requested
order. Completion means reviewed, repaired, reconciled private commits and
one concise report each, not merely two implementations or two passing suites.
