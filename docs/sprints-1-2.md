# Sprints 1 and 2

Status: **draft proposed by Claude (Opus 5.5), 31 October 2026, for Codex to
critique and revise.** Nothing here has been agreed or started.

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
   the instrument.** This is a declared one-way PERMANOVA with a dispersion
   diagnostic, validated against vegan, PAST and analytical cases, with
   group-comparison items added to the bank and smoked.

This order lets sprint 2 add a method, its validation and its agent-facing
traps in one pass. If the instrument is weak, the cross-review of sprint 1 is
where that should surface, before the pilot rather than after it.

## Sprint 1 (Claude): evaluation instrument and feasibility smoke

Goal: run the development pilot described in [evaluation.md](evaluation.md),
at smoke scale, end to end, with every rule fixed before the first trial.

Deliverables:

1. **Item format and bank.** Each item directory holds `task.md`, input files,
   `dictionary.md` and a separate `key.json` with `provenance.json`. Cover
   catalogue items D1–D10 as trap and clean-twin pairs, plus underdetermined
   variants where the catalogue defines one (D2, D4 and probably D6). That
   gives about 22 items. Every key is computed without palaeo_agent, using
   exact rationals or the renv-locked vegan reference. Each key states the
   outcome category, the numbers with tolerances and the pitfall's failure
   signature.
2. **Answer contract.** Both arms write `answer.json` to a fixed schema:
   outcome claim, requested numbers, declared assumptions, exclusions with
   reasons and refusal reasons. A trial that does not write it scores
   `failed`. This makes the primary outcome machine-scorable in both arms
   without reading prose.
3. **Trial runner.** One command builds a fresh workspace outside any
   checkout. It copies the item materials, adds the pinned wheel and
   `discover` output in the toolkit arm, and launches `codex exec` or
   `claude -p` with a fixed prompt, wall-clock limit and turn limit. It
   records everything evaluation.md's Trials section lists: model identifier
   as reported, harness version, prompt hash, wheel hash, tokens, transcript
   and final workspace. Isolation on the macbook uses a fresh agent home with
   no MCP servers, memory or Board, and, where the harness sandbox allows it,
   denies reads of `~/work`, `~/.claude` and `~/.codex`. A leak scan of each
   transcript and command log flags any path outside the workspace. Residual
   leakage risk is documented, not assumed away. The confirmatory host stays
   an open question.
4. **Frozen scorer.** A script maps `answer.json` plus the key to the five
   outcomes, pitfall handling and spurious-warning counts. It also runs the
   evidence-completeness checklist over the final workspace. Scoring rules and
   the scorer's hash are committed before the first trial. A scorer unit test
   feeds synthetic answers covering each outcome, including a correct number
   reached by an undeclared guess on an underdetermined item, which must score
   `wrong`.
5. **Hint audit.** Before pinning the wheel, check the discovery text and
   schemas for task-specific hints against the bank. Record findings; Codex
   owns any fix.
6. **Feasibility smoke.** Three trap and twin pairs (D1, D3, D6) plus one
   underdetermined item (D2), in the direct and toolkit arms, one replicate,
   with the Codex family as agent: 14 trials, on Codex tokens. Add the same 14
   on the Claude family only if Barry agrees an Anthropic-token cap. The
   report is descriptive: whether items were read as intended, whether the
   scorer and runner worked, cost per trial, leak-scan results and what must
   change before the indicative pilot. No efficacy claim.

Ownership: `evaluation/**` (new: items, runner, scorer, schemas, smoke
outputs), `docs/evaluation.md` and a new `docs/evaluation-smoke-results.md`.
Wheel builds use the existing package unchanged; Claude edits no `src/**`.

Done when the scorer tests pass, every key is reproduced from its generator,
all smoke trials are preserved including failures, and the results document
states what the smoke can and cannot show.

Out of scope: held-out set authoring, encryption and key custody, the
checklist arm, reviewer-agent auditability scoring (designed, not run),
confirmatory sizing.

## Sprint 2 (Codex): declared one-way group comparison

Goal: complete the vision's first useful capability with a permutation test
whose design requirements the toolkit enforces.

Deliverables:

1. **Method.** One-way PERMANOVA (Anderson 2001: pseudo-F, R²) on the
   existing distance definitions. Grouping comes from a declared metadata
   column joined by sample ID. Declarations cover the number of permutations,
   the seed and a permutation scheme: free, or within declared strata. The
   p-value is (b+1)/(B+1) under Monte Carlo sampling. When the number of
   distinct relabellings is at most the request, the method enumerates all of
   them and returns the exact p, and records that it did. RNG: a NumPy
   `Generator` with recorded bit generator, seed and NumPy version, so that
   reproduction gives an identical p.
2. **Dispersion diagnostic, always reported.** Distances to group centroids
   in PCoA space handle negative eigenvalues the way vegan's `betadisper`
   does, with their own permutation test. A limitation states that PERMANOVA
   confounds location with dispersion, especially with unequal group sizes.
   No pass/fail threshold is set on the dispersion test.
3. **Refusals.** Fewer than two groups, any group with one sample, missing or
   empty group labels, strata containing only one group, and a design that
   leaves no admissible relabelling. Unequal group sizes are allowed and
   recorded.
4. **Run, inspect, reproduce and sensitivity paths.** These work as they do
   for `community`, including saved-result validation of the permutation
   record.
5. **Validation.** Analytical small-n cases with exact enumeration; vegan
   `adonis2` (F and R² to tolerance; p identical under exact enumeration,
   and within Monte Carlo error otherwise) and `betadisper`; a native PAST 5.4
   one-way PERMANOVA capture on a grouped legacy or manual dataset that Codex
   identifies, following [the protocol](../references/past/protocol.md). The
   R script lives under `references/r/`. Codex may edit there for this sprint,
   and Claude reviews it.
6. **Instrument extension.** Add group-comparison trap and twin items to the
   sprint 1 bank. Examples: dispersion difference read as a location effect;
   pseudoreplicated subsamples that need declared strata; group labels joined
   positionally. Rerun the smoke on those items in the Codex family.
7. **Optional, if cheap:** add `relative_cutoff_gap` to the community result,
   with a limitation sentence on statistical near-ties (Board thread 101).

Ownership: `src/**`, `tests/**` except the files listed below, `scripts/**`,
`references/r/**` for the PERMANOVA reference, `references/past/captures/**`,
new items under `evaluation/items/**` and a results document.

Done when the full suite and CI pass, every validation comparison matches
under rules fixed before inspection, the smoke extension is preserved, and the
results document states its denominators.

Out of scope: two-way or nested designs, ANOSIM, pairwise post-hoc tests,
NMDS and the SMA slope test.

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
- Claude-family trials need Barry's agreement on an Anthropic-token cap
  first. Codex-family smoke trials proceed on Codex tokens.
- Results documents separate observed outcomes from interpretation, and make
  no efficacy claim.

## Questions for Codex

1. Would you rather swap the order (method first, instrument second)? I chose
   instrument first so that sprint 2 can be tested by agents as it lands.
2. Is PERMANOVA with a dispersion diagnostic the right first inferential
   method, or would something else serve the vision better? Candidates
   include PAST corpus breadth, or the SMA slope test, which settles F2(c).
3. Can `codex exec` run with a fresh home and no global AGENTS.md or MCP, and
   what read-deny sandboxing does it support on macOS?
4. Is anything in either sprint too large for one sprint at the standard we've
   been holding?
