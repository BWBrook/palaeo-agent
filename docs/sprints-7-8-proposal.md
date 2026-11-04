# Sprints 7–8 proposal: comparing assemblages with unequal counts, an agent primer, and instructed use

Claude (Opus 5.5), 3 November 2026. It answers Barry's request in Claude
Code chat on 3 November 2026, quoted where it constrains the design. Revised
after Codex's [critique](sprints-7-8-critique.md) (330286b). No
implementation has started.

## Settled after Codex's critique

Claude accepts every substantive point. The binding scientific contracts are
now [rarefaction-contract.md](rarefaction-contract.md) and
[count-homogeneity-contract.md](count-homogeneity-contract.md); where this
proposal's summaries differ, the contracts govern.

1. **The omnibus test** is the fixed-margin Pearson test with a stated
   sampling model, Monte Carlo convention, plus-one p, exceedance count and
   Clopper–Pearson Monte Carlo interval, with Bray–Curtis as a separate
   effect size.
2. **Multiplicity** has two separately labelled Holm families:
   - the omnibus family, across the declared pairs;
   - **one taxon family across every pair × taxon test**, as Codex
     recommended.

   Neither family is selected post hoc, and together they do not promise a
   single error rate.
3. **Rarefaction** is equal-count rarefaction plus coverage diagnostics,
   with the m < n and m = n coverage branches, the f₁/f₂ boundaries and the
   n = 1 case specified. Equal-coverage standardisation is deferred, for a
   concrete reason: Coed Duon has no common coverage reachable by
   interpolation. Claude reproduced Codex's values, 0.9090342679 and
   0.7046153846.
4. **No `primer_sha256` in scientific bundles.** Delivery is audited from
   session records: the full primer body appears in a visible tool or command
   result, in order, before the first analytical execution.
5. **Deferred:** the public `check_values` helper and the MCP prompt. The
   cross-check is a field-labelled comparison script with a receipt.
6. **Primer guidance corrected:**
   - a refusal is never a reason to coerce or delete data;
   - necessary unsupported preparation is allowed, with saved provenance;
   - a demonstrated toolkit defect makes that operation unsuitable until it
     is repaired, which is not a licence for convenience;
   - suitability is judged for the requested design, with no blanket claim
     about restricted designs;
   - transport-correct names are used.
7. **I2** uses the existing toolkit runtime with the analysis MCP tools
   withheld. This is a new, explicit delivery mode in staging, inventory and
   replay. The bootstrap prints the complete `palaeo_agent.primer()` object
   (version, SHA-256 and text) through `worker_execute`, since the confinement
   has no CLI subprocess.
8. **The worker forwards the server's instructions** verbatim. The scripted
   client-boundary check verifies instruction *content*, and that the full
   primer is delivered below output limits.
9. **New sessions only.** The new sessions use new prompts that allow the
   scientific MCP tools. The A1/A2 prompts and records are unchanged.
10. **Two sessions remain**, as two descriptive demonstrations of different
    cases and paths. Neither the pair nor its outcome supports a causal
    attribution. The explicit bootstrap is the documented baseline.
11. **Codex CLI** documents support for server `instructions`, and
    recommends a self-contained first 512 characters. Ours are written to
    that limit.

## 1. The research need, and why one workflow

Barry: "make the toolkit useful enough that research agents can apply it to
real scientific questions … one coherent, reusable workflow around comparing
fossil assemblages with unequal sample counts."

The named need is the Coed Duon question in
[analyses/coed-duon-llanvirn](../analyses/coed-duon-llanvirn/report.md):
- **The question.** How does composition change through ten horizons whose
  counts range from 13 to 702 specimens, and which conclusions survive those
  unequal totals?
- **Why it recurs.** Unequal counting totals are the usual condition of fossil
  count data. Sieved bulk samples, bed-by-bed collections and museum lots all
  differ in yield. Two questions arise often:
  1. How much of a richness difference is a count effect?
  2. Is a composition difference larger than counting noise would produce?

Neither answer establishes true richness, turnover or cause. Both are the
missing pieces of this workflow.

## 2. What the toolkit already handles, step by step

Mapped against the corrected Llanvirn analysis:

| Workflow step | In the corrected analysis | Toolkit today | Decision |
| --- | --- | --- | --- |
| Read the archived table, declare orientation, refuse bad cells | hand-parsed | `community` reads PAST or delimited tables, with declared orientation; refuses non-integer counts and missing cells; warns on near-duplicate labels, identical samples and repeated blocks | use as is |
| Declare exclusions, taxon merges, sample selection | none needed | `study` operations `exclude`, `select`, `map_taxa`, each recorded with a reason | use as is |
| Totals, richness, Shannon, Simpson | numpy | `community` | use as is |
| Bray–Curtis on proportions; Jaccard; PCoA | numpy | `community` (`transform: relative_abundance`, `distance: braycurtis` or `jaccard`; uncorrected PCoA with negative-eigenvalue warning) | use as is |
| Sensitivity of distances to representation | five representations | `compare` (descriptive comparison of two community runs, including a bound on how much raw-count Bray–Curtis can reflect total imbalance) | use as is; raw versus relative is the comparison that matters |
| **Richness at a common count** | simulated rarefaction to n = 13 | **missing** | **add**: rarefaction (§3.1) |
| **How complete each sample is** | not done | **missing** | **add**: sample coverage, in the same operation |
| **Is a composition difference beyond counting noise?** | pooled multinomial null, Holm across steps | **missing** | **add**: conditional homogeneity test (§3.2) |
| **Which taxa changed, and is a zero an absence?** | Fisher exact with Holm; one-sided upper limits | **missing** | **add**, in the same operation |
| Group differences between lithostratigraphic units | PCoA description only | `permanova` exists, but adjacent horizons in one section are not exchangeable replicates | **do not use**: the design is unsuitable; the primer says so |
| sqrt proportions, log(1 + x) after standardising | done for robustness | missing | **do not add**: the corrected analysis showed proportions and the total-standardised logs agree. The raw-versus-relative `compare` already exposes the one effect that mattered, unequal totals |

**Considered and rejected for this tranche:**
- Hill-number profiles and coverage-based extrapolation (iNEXT-style). They
  are scientifically sound, but interpolation to a common count or coverage
  answers the Llanvirn question, and extrapolation adds estimator choices
  without a named need.
- Restricted permutation for stratigraphic series. Whether a restricted
  design is valid depends on the experimental unit, the contrast, the
  replication and the allowable randomisation. The proposed grouping of this
  single section has no justified exchangeability, and no named need
  requires one.
- More distances and transforms. No named need.

## 3. The smallest scientifically justified additions

Two operations. Both accept the same declared count input as `community`, and
both can be used as analyses inside a `study`. **The binding methods
contracts are [rarefaction-contract.md](rarefaction-contract.md) and
[count-homogeneity-contract.md](count-homogeneity-contract.md).** The
summaries below are from the first draft. Where they differ, the contracts
govern.

### 3.1 `rarefaction`: richness at equal counts, and sample coverage

- **Expected richness.** For each sample, the expected richness of a random
  subsample of m specimens drawn without replacement (Hurlbert 1971), with
  its exact variance (Heck, van Belle & Simberloff 1975). This is computed at
  declared m values, or by default at the smallest retained total, plus
  optionally a curve at declared steps.
- **Coverage.** The sample coverage estimate of each full sample (Chao &
  Jost 2012, the Good–Turing form with the f₂ correction), and the expected
  coverage of the rarefied sample at each m. Coverage tells an agent whether
  samples rarefied to the same count are comparably complete.
- **Refusals.**
  - non-integer counts;
  - m > n for any sample, since this tranche interpolates only and never
    extrapolates;
  - m < 1;
  - empty samples, unless dropped by declaration.
- **Limitations stated in the result.**
  - Rarefaction standardises count, not sampling effort.
  - The variance is conditional on the observed sample (within-sample), not
    between replicate samples.
  - Rarefied richness of a dominance-structured sample reflects evenness as
    well as membership.
- **Reference values.**
  - R `vegan::rarefy` for the expectation and its SE.
  - `iNEXT` for coverage, through the existing R reference lane.
  - PAST "Individual rarefaction" for E(S) and its SD, through a scripted
    GUI capture.

  Agreement is required within 1e-10 for the closed forms.

### 3.2 `count_homogeneity`: is the difference beyond counting noise, and in which taxa?

For each **declared** pair of samples (for example adjacent horizons;
nothing is inferred):

- **Overall composition.** A conditional test of homogeneity of the taxa × 2
  table with both margins fixed, so that every specimen-to-sample allocation
  with those totals is equally likely. It uses the Pearson χ² statistic and a
  Monte Carlo p-value from fixed-margin tables (Patefield 1981, as
  `scipy.stats.random_table`) with a declared seed and number of tables. The
  p-values are Holm-adjusted across the declared pairs.
- **Effect size.** Bray–Curtis on proportions, so the test and the effect
  size are not confused.
- **Per taxon.** Fisher exact tests for each taxon present in either sample,
  Holm-adjusted as one family across every pair × taxon test (revised; see
  the contract).
- **Zeros.** A one-sided 95% upper limit (Clopper–Pearson) on the proportion
  of any taxon counted as zero, so an agent cannot report a zero as an
  absence.
- **Refusals.** Undeclared pairs, empty samples, non-integer counts, and
  fewer than 2 taxa present.
- **Limitations stated in the result.**
  - The test covers counting (sampling) error only, and assumes specimens
    are exchangeable within a sample.
  - Clustering, patchiness or taphonomic aggregation within a horizon makes
    it anticonservative.
  - It is silent on cause, time and rate.
  - It needs no replicates, and in turn says nothing about between-replicate
    variation.
- **Reference values.**
  - R `fisher.test` for the per-taxon tests and `p.adjust(method = "holm")`
    for the adjustments.
  - For the omnibus test, R `chisq.test(simulate.p.value = TRUE)`, whose
    Monte Carlo p must agree within Monte Carlo error. The exact χ² statistic
    must agree to 1e-12.

**Why this test, not A1's pooled-multinomial null with Bray–Curtis.** The
fixed-margin test conditions on both sample totals and taxon totals. It is
the textbook conditional test for a 2 × k table, and it has an independent
reference implementation.

A scratch check on Coed Duon (4,999 tables, before any Holm adjustment) gives:
- **Focal steps:** 5–6 p = 0.0002 (the plus-one floor at this B) and 6–7
  p = 0.0004.
- **1–2, 2–3, 7–8, 9–10:** p = 0.14–0.82.
- **8–9:** p = 0.11, against the multinomial null's unadjusted 0.015. The
  two calculations differ in both null and statistic, so the difference is
  not attributable to either change alone.

**Why not PERMANOVA or ANOSIM on horizons.** They need replicate samples per
group. A single section gives one sample per horizon.

## 4. The agent primer

Barry's rule, verbatim, is the primer's first section:

> NEVER write bespoke code for an analytical task or subtask that a suitable
> existing Palaeo-Agent API operation can perform. Use the API for that part.
> If the toolkit does not support a necessary operation or the required
> scientific design, the agent may use other code for that unsupported part,
> but must say what was unsupported and why. Do not bypass a suitable
> operation merely because writing code seems quicker. The agent must still
> exercise scientific judgment and must not force a method onto an unsuitable
> design.

The full draft is [sprints-7-8-primer-draft.md](sprints-7-8-primer-draft.md).
It covers:
- the rule;
- the start-of-session steps: read the primer, run `discover`, record the
  primer version;
- the workflow pattern: validate → run or study → inspect → cite fields;
- what counts as a "suitable" operation, and how to decide that a design is
  unsuitable;
- the "unsupported parts" declaration to put in the report;
- how to keep `analysis.py` reproducible through the Python API;
- how to use toolkit calculations to check other code (§6), with what that
  can and cannot establish;
- a short worked map of the unequal-counts workflow.

It is about 120 lines: enough to be complete, small enough to read every time.

## 5. Delivering the full, versioned primer

**Constraints we must not assume away.**
- Installing a package injects nothing into an agent's system prompt.
- A repository instruction file is read only by clients that look for it:
  Claude Code reads `CLAUDE.md`, Codex reads `AGENTS.md`. Even then it is read
  only when the working directory is inside the repository, and it is meant
  for developers rather than research users.
- MCP server `instructions` are optional for clients to surface.
  - Claude Code's provider-visible placement is version-dependent; the
    sprint-7 probe checks the actual text in system or user-message prefaces.
  - Other clients may ignore or truncate them.
  - MCP prompts are user-invoked in most clients.

**Design: one source, and four ways to fetch it.**

1. **One source.** `src/palaeo_agent/primer.md`, shipped as package data.
   - Its version is the package version plus the file's SHA-256.
   - The copy on GitHub and the installed copy are the same bytes for the
     same version, and a test enforces this.
2. **Python:** `palaeo_agent.primer()` returns `{version, sha256, text}`.
3. **CLI:** `palaeo-agent primer` prints the text, with a version and hash
   header.
   - In a checkout: `uv run palaeo-agent primer`.
   - From a built wheel: `uvx --python 3.12.13 --from <wheel> palaeo-agent primer`. This is
     tested against the installed wheel's bytes.
   - From a future PyPI release, for example `uvx palaeo-agent@0.3.0 primer`.
     That command is an example only until the release exists. Retrieval and
     analysis are pinned to the same artifact.
   - On GitHub, the path is pinned to the analysis commit or tag.
4. **MCP:**
   - **A `primer` tool** returns the full text, version and hash.
   - **Server `instructions`** are a short, client-optional preface: the rule
     in one sentence and "call `primer` before any analysis".
   - **`discover` results always include** `primer: {version, sha256}` and a
     `read_first` note. Every agent that discovers the methods is told the
     primer exists even if its client dropped the instructions.
   - The descriptions of `run` and `study_run` say the same in one line.
   - (An MCP prompt is deferred: the tool and the explicit user bootstrap
     cover the named use case.)
   - The confined evaluation worker forwards the tool and the instructions
     unchanged.

**Checkable after the fact (revised).** A supplied hash would be a
declaration, not evidence of reading. Delivery is therefore audited from the
session record: the transcript, worker audit and replayed source together.
Scientific bundles are unchanged.

**The documented bootstrap is an explicit user request.** The
primer and README give a one-line instruction for the user to include:

> Use the Palaeo-Agent toolkit for this analysis. Before any analysis, read
> its primer (`palaeo-agent primer`, or the `primer` tool if it is connected
> over MCP) and follow it.

Everything else raises the odds that an agent finds the primer unprompted; it
does not guarantee it.

**Repository files.** README's quick start begins with the primer command.
`AGENTS.md`, with `CLAUDE.md` importing it, tells coding agents working in the
repository where the primer is. We do not rely on either for research agents.

## 6. Using the toolkit to check work written with other libraries

The named need is the two corrected analyses in `analyses/`, which are
written in numpy and scipy, and the duplicate block in Dielasma that only one
analyst session noticed.

- **Input diagnostics.** `validate` on the analysis's own input table reports
  repeated records and blocks, near-duplicate labels, identical samples,
  empty samples and structural inconsistencies under the declared orientation.
  It cannot infer the scientifically correct orientation. Running it on `dielasma.dat` would
  have flagged the L2 block in every session.
- **Independent recomputation of selected quantities.** Totals, richness,
  Shannon, Simpson, Bray–Curtis, PCoA eigenvalues, RMA slope, rarefied
  richness and coverage, and the homogeneity test statistics.
- **A field-labelled comparison script with a receipt** (revised: the public
  `check_values` helper is deferred). Before comparing values, it matches
  inputs, sample and taxon identities, transformations, estimands and
  numerical conventions.
- **Its output always states** that agreement shows that the same arithmetic
  on the same data gives the same numbers. It does not show that the
  population, design or interpretation is right, and replay does not either.
- **Demonstration.** Check the corrected Llanvirn `results.json` against
  toolkit bundles, then record and investigate any disagreement. The
  simulated rarefaction means are compared with the exact expectations using
  the Monte Carlo error of the mean, not the within-subsample SD.

## 7. A proportionate demonstration of primer delivery and instructed use

**Hypothesis (Barry's, held as a hypothesis):** the API was ignored in A1 and
A2 partly because agents were not firmly told to use it.

**This demonstration tests whether, when told, an agent:**
1. obtains the primer before analysis;
2. uses the API for every supported subtask;
3. declares the unsupported parts;
4. does not force a method onto an unsuitable design.

It does **not** test whether agents choose the toolkit voluntarily. A1 and A2
(0 of 2 discovered the toolkit) remain the only evidence on that, and this
tranche does not re-run it.

**Two live sessions.** Both use Sonnet 5.5 on the existing authentic-session
harness: the same confined worker, safeguards, contract, replay and
retrospective. The runtime is rebuilt with the tranche's wheel, and probes and
supervisor qualification are rerun.

| Session | Case | Delivery path tested | User instruction |
| --- | --- | --- | --- |
| I1 | Coed Duon (supported workflow) | MCP: server instructions, `discover` pointer, `primer` tool | "Use the Palaeo-Agent toolkit for this analysis." Nothing about the primer |
| I2 | Dielasma (inference unsupported) | toolkit runtime; analysis MCP tools withheld; Python package through `worker_execute` | "Use the Palaeo-Agent toolkit for this analysis. Before any analysis, print the complete object returned by `palaeo_agent.primer()` (version, SHA-256 and text), read it, and follow it." |

- **I1 checks MCP-native delivery.** Does the agent find and read the primer
  with no help from the user?
- **I2 checks the user bootstrap path,** and the rule's second half. The
  toolkit has descriptive RMA but no slope inference, so a compliant agent
  uses `rma`, `validate` and its warnings through the API. It writes its own
  code for the slope tests and says why. It must not present descriptive RMA
  as inference.

**Checks, fixed before launch and scored by script from the worker audit,
transcript and package; then read by Codex:**
- delivery, recorded at three separate levels:
  1. the primer bytes were available;
  2. the full body appeared in a visible tool or command result before the
     first analytical execution;
  3. API use and scientific decisions (below).

  A hash alone proves neither of the last two;
- a per-case list of supported subtasks, written before launch, each done
  through the API:
  - I1: diversity, Bray–Curtis, rarefaction/coverage, homogeneity tests;
  - I2: `validate`, `rma`;
- every bespoke computation is either of an unsupported part, declared in the
  report with a reason, or a violation;
- unsuitable designs are not forced: no PERMANOVA on horizons in I1, and no
  descriptive RMA presented as a test in I2;
- the package replays, and an independent Codex scientific review is done.

**Budget.** At most 120,000 counted tokens, with launch-stop. No twins, no
repeats, no scoring bank. Two sessions give descriptive evidence about
delivery and compliance in one client and model. They give no compliance
rate.

**If I1 fails on delivery but I2 succeeds,** record those two outcomes and
recommend the explicit bootstrap as the documented baseline. Different cases
and sessions cannot establish a causal effect of the bootstrap, or prove that
MCP-native delivery always fails in this client. No additional trials follow
automatically.

## 8. Division of work

The proposal follows the agreed split: Claude owns live runs and the
synthesis; Codex owns most implementation, independent reference values and
review. Barry's Codex allocation is the larger one.

| Work | Owner | Reviewer |
| --- | --- | --- |
| Methods notes for `rarefaction` and `count_homogeneity` (primary sources, formulas, refusals, limitations, reference targets) | Claude | Codex |
| Implementation of both operations in the library, CLI, MCP and `study` | Codex | Claude (scientific review against the notes) |
| R and PAST reference values | Codex | Claude |
| Primer text | Claude | Codex |
| Primer delivery plumbing: package data, `primer()`, CLI, MCP tool, server instructions (first 512 characters self-contained), `discover` pointer, worker forwarding of instructions, installed-wheel byte test | Codex | Claude |
| Explicit delivery modes in staging, inventory and replay (I1: MCP tools exposed; I2: toolkit runtime, analysis tools withheld); content-level boundary check | Codex | Claude |
| Cross-check script and receipt on the corrected analyses | Claude | Codex |
| Runtime rebuild, probes, supervisor qualification, live sessions I1 and I2, report | Claude | Codex (review of the record and science) |

**Sequence.**
- **Sprint 7:**
  - Claude writes the methods notes and primer; Codex reviews them.
  - Codex implements the two operations and the delivery
    plumbing, with reference values; Claude reviews.
  - Claude runs the cross-check demonstration.
- **Sprint 8:**
  - Claude freezes the runtime and fixes the checks.
  - Claude runs I1 and I2; Codex reviews.
  - Joint report, with a recommendation on the primer and delivery.

## 9. Questions for Codex (answered in the critique; see "Settled" above)

1. Is the fixed-margin χ² test the right omnibus test? The alternative is A1's
   multinomial null with Bray–Curtis as the statistic. I chose χ² for its
   textbook conditioning and independent reference.
2. Should coverage-based rarefaction (Chao & Jost 2012 standardisation to
   equal coverage) be in scope instead of, or as well as, equal-count
   rarefaction? I propose estimating coverage but interpolating by count only.
3. Is `primer_sha256` in bundles worth its schema change? The alternative is
   reading primer use from transcripts.
4. Do you know whether Codex CLI surfaces MCP server `instructions`? If it
   does not, the `discover` pointer is the only MCP-native channel there.
5. Is a two-session demonstration enough, given that it answers only "does
   delivery work and do agents comply when told"? Or would you cut it to one?
