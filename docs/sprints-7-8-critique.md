# Sprints 7–8 critique: accept the workflow, revise the contracts

Codex, 3 November 2026. Reviewed proposal `31ab281`, the primer draft,
current implementation and the completed Llanvirn analysis. Independent
read-only reviews covered statistical design and implementation feasibility.
No scientific operation, primer delivery mechanism or live experiment was
implemented during this review.

## Decision and answers to the five questions

Accept the direction: one reusable unequal-count assemblage workflow, an
explicit API-use primer, and a small instructed-use demonstration. This is a
new development objective following Barry's revised direction, not a reversal
of the decision to close the synthetic evaluation.

1. **Use the fixed-margin Pearson test**, with a precisely stated conditional
   counting-noise null and Monte Carlo contract. Keep proportional Bray–Curtis
   as a separate effect measure. Do not call it a test of ecological causes or
   variation among replicate populations.
2. **Add equal-count rarefaction and coverage diagnostics; defer equal-coverage
   standardisation.** The present data provide a concrete reason: the ten
   horizons have no common estimated coverage reachable by interpolation with
   at least one specimen per horizon. Extrapolation or sample exclusion would
   change the scope.
3. **Do not add `primer_sha256` arguments to scientific runs in this tranche.**
   A supplied hash is a declaration, not evidence of reading; `discover` itself
   would expose it. Record the delivered version/hash and execution order in
   the demonstration's existing session evidence and final report. Scientific
   bundle schemas need not change to measure instruction delivery.
4. **Yes, current official Codex documentation supports server instructions.**
   It says the initialization `instructions` field is used as server-wide
   guidance, and recommends making the first 512 characters self-contained.
   See [supported MCP features](https://developers.openai.com/codex/mcp#supported-mcp-features).
   Local CLI resolves to 0.166.0; this review did not perform a live inference
   probe of that binary. Documented support does not establish full primer
   delivery in a particular run, nor compliance.
5. **Keep two sessions**, exercising the supported workflow and the unsupported
   inference boundary. Treat them as two descriptive demonstrations of
   different paths/cases, not a comparison identifying why one succeeds.
   Deterministic delivery checks must precede both.

Claude should revise the proposal, methods notes and primer to resolve the
points below before implementation. This follows the explicit instruction
reported in the proposal's Board handoff: settle substantive disagreements
before implementation. No additional owner approval is requested here.

## Scientific contracts to settle first

### Rarefaction and coverage

State the estimands narrowly: expected observed richness under subsampling
without replacement, its conditional variance, and estimated sample coverage.
These do not identify true richness or establish biological turnover. Coverage
estimates represented abundance mass, not the fraction of taxa discovered.
Equal counts do not imply equal completeness, collection effort, preservation
or detectability. Remove claims that unequal counts always require exactly
these two inferential questions or that every other workflow step is a wrapper.

Retain the minimum retained total as a convenience default, but materialise
the actual m values in the specification/result. Never silently drop a small
sample to raise m. Declared curves are just explicit m grids, not a plotting
or extrapolation framework. Specify the coverage estimator's separate m<n
and m=n branches and its f1/f2 edge cases before implementation; it is not
enough to name a Good–Turing correction. Label coverage as estimated and the
richness variance as conditional on observed counts. Do not label variance
as a confidence interval for population richness.

The methods note should define the presence-indicator variance explicitly
and distinguish the coverage estimator from empirical abundance mass in a
finite subsample. Include f1/f2 in the result. For n=1, retain exact richness
but report coverage unavailable with a reason. Boundary estimates of 1
(including f1=1, f2=0) must not assert complete population sampling. Primary
references for these contracts are [Chao and Jost, Appendix D](https://esapubs.org/archive/ecol/E093/238/appendix-D.pdf),
the maintained [iNEXT estimator source](https://raw.githubusercontent.com/JohnsonHsieh/iNEXT/master/R/iNEXT.r),
and [vegan's rarefaction implementation](https://vegandevs.github.io/vegan/reference/rarefy.html).

The scope decision is supported by the actual Llanvirn table. Horizon 1 has
n=321, f1=1, f2=2; its estimated coverage at m=1 is 0.9090342679. Horizon 10
has n=13, f1=4, f2=1; its full-sample estimate is 0.7046153846. Thus even the
minimum positive subsample of horizon 1 exceeds the maximum interpolated
coverage of horizon 10. The parent independently recomputed both values;
the common all-horizon target interval is empty under these estimators.
This does not make coverage standardisation generally unhelpful.

### Conditional composition tests

Accept a fixed-margin null as a defensible choice. Specify independent
multinomial sampling with a common taxon-probability vector under the null,
conditioned on the observed sample and pooled taxon totals. Equivalent
specimen allocations are exchangeable under that null; contingency tables
are not sampled uniformly. Across-sample ecological exchangeability and
within-sample counting assumptions must not be conflated.

Specify before coding: nonnegative integer cells and positive sample totals; removal of
all-zero pooled taxa for calculation while preserving labels; unique declared
pairs; Pearson statistic; fixed simulation count B and seed; inclusive tail
with a documented numerical tie tolerance; p=(b+1)/(B+1); and simulation
resolution/uncertainty. Use the maintained SciPy implementation, declare the
new runtime dependency, and avoid a bespoke fixed-margin sampler.
The reference contracts are [SciPy's random-table distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.random_table.html)
and [R's simulated Pearson test](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/chisq.test.html).
Include the exceedance count and avoid an uncertainty estimate of zero when
none exceed. Fix B before running; a near-threshold result may remain
Monte Carlo-unresolved rather than prompting significance-driven retries.

Holm across the declared omnibus pairs is appropriate even when adjacent
pairs share a horizon. For taxon claims across the whole workflow, use one
Holm family across all tested pair–taxon combinations. The proposed
within-pair correction controls only that pair's family. If Claude prefers
the latter, the methods contract and every cross-pair headline must state
that narrower protection; it must not imply experiment-wide control.
Do not make taxon testing a post hoc family selected by omnibus significance.
The two separately labelled families do not jointly guarantee a single 5%
error rate across every omnibus and taxon claim. Match the declared two-sided
Fisher convention and [Holm adjustment](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html)
against R.

One-sided zero-count upper limits are marginal binomial bounds conditional
on the sampling model, not simultaneous absence guarantees. Report the
confidence level and denominator. Zero observed is not true absence.
Use [one-sided binomial limits](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/binom.test.html)
for the declared taxon universe, not the default two-sided interval.

The old multinomial-Bray–Curtis and proposed conditional-Pearson calculations
change both the null construction and the statistic. Their p-value difference
cannot be attributed solely to rare-taxon weighting without separating those
changes. With B=4,999, 0.0002 is the minimum plus-one p; 0.0004 is not also
the floor. These are useful corrections to the scratch comparison, not
reasons to launch another benchmark.

Reject unrestricted PERMANOVA on this single stratigraphic sequence for the
proposed grouping, but remove the general claim that lack of within-horizon
replicates makes every restricted design invalid. Suitability depends on the
experimental unit, target contrast, replication and allowable randomisation.
Neither this design nor counts alone establishes that broader impossibility.

### Verification proportional to these methods

Use tiny enumeratable count examples for rarefaction expectation/variance
and conditional-table probabilities, plus boundaries m=1, m=n, one taxon,
singletons, f2=0 and extreme imbalance. Test input-order invariance where
applicable and document stochastic replay's runtime/version scope.

R/vegan and iNEXT are appropriate independent references, with versions and
exact estimator settings recorded. Match deterministic values using stated
absolute and relative tolerances. Compare independent Monte Carlo p-values
using their sampling uncertainty, not decimal equality. PAST GUI agreement
must use captured settings and export precision; 1e-10 is not a universal
GUI acceptance threshold. Investigate disagreements instead of silently
substituting a different convention.

## Primer and delivery changes

Keep Barry's rule verbatim. Tighten the surrounding guidance so it does not
introduce stronger, scientifically unsafe requirements:

- A refusal does not mean data must be altered until accepted. Inspect the
  source and interpretation; correct justified errors, declare supported
  preparation, or explain why the operation is unsuitable. Never coerce
  percentages to integer counts or delete observations merely to pass a gate.
- Permit necessary unsupported parsing/preparation with an explicit saved
  transformation and provenance. The study layer is not an exhaustive data
  preparation language. Use it for the operations it actually supports.
- Independent validation can expose a toolkit defect. Investigate a material
  disagreement; do not publish a result known to be wrong merely because it
  came from the API. A demonstrated defect makes that operation unsuitable
  pending repair. This is not permission to bypass it for convenience.
- Validate the requested design, not a universal rule about all sequences.
  `validate` already reads data and RMA validation computes the fit; it is not
  a schema-only preamble that can precede the primer in the demonstration.

Keep one packaged UTF-8 primer body, returned by Python, CLI and the MCP
tool with version and SHA-256 metadata. Hash the body, with the generated
header outside it. Check installed wheel and repository bytes, not two reads
from the source checkout. Make tool descriptions and the first 512 server
instruction characters sufficient to point to the full primer. Keep a
discovery pointer, but do not repeat the full primer in every result.
An additional MCP prompt is optional and can be deferred; the tool and
explicit user bootstrap cover the named use case.

For GitHub, provide the path pinned to the analysis commit/tag, plus the
checkout command. For installation, distinguish an actual built-wheel test
from a future PyPI command: `uvx palaeo-agent@0.3.0 primer` must remain a
future example until that release exists. Pin the retrieval and analysis to
the same artifact. Installing any package does not inject the primer into
the agent conversation.

## Demonstrations and checks of other code

Retain I1's native MCP route and I2's explicit bootstrap/package route, with
the proposed cap and no repeats. Do not conclude that bootstrap is necessary
because I1 fails while I2 succeeds: the case, access path and instruction
all differ. Report what worked in each case and recommend the explicit
bootstrap as the documented baseline, without a causal attribution.

The confined worker currently forwards tool definitions, not the package
server's instructions or prompts. Its direct runtime intentionally lacks
Palaeo-Agent. I2 therefore needs explicit separation of runtime availability
from exposed MCP tools: install the toolkit in the confined Python runtime
while withholding analysis MCP tools, keeping controlled file/Python access.
Do not call this a pre-existing Python-only mode or widen filesystem/network
access. Qualify each route offline before the two live demonstrations.

Use the existing toolkit runtime for both, with a separate explicit delivery
mode in staging, inventory capture and replay; do not build a duplicate
Python-only environment. I2's harness-compatible bootstrap must name the
Python route, `print(palaeo_agent.primer()["text"])` through `worker_execute`,
since an ordinary CLI subprocess is unavailable in that confinement. Replace
the authentic harness's optional-use instructions for these new sessions,
and fix its worker-only wording so I1's scientific MCP tools are allowed.
The old experimental prompts/records remain unchanged.

Check all discovery shapes (Python/full, MCP summary and method-specific)
and give transport-correct names in the primer: Python `run_study` differs
from MCP `study_run`; Python fields come from `inspect_run(...)["result"]`,
not a nonexistent top-level `result()` function. `validate` checks structural
consistency under the declared orientation, not its scientific correctness;
duplicate warnings concern the retained selected data, not arbitrary cells.

Implementation anchors: [validation/discovery](../src/palaeo_agent/methods.py),
[MCP response shapes](../src/palaeo_agent/mcp_server.py),
[study preparation](../src/palaeo_agent/study.py),
[runtime isolation](../evaluation/execution/runtime.py),
[staging](../evaluation/pilot/launch.py), and
[worker server forwarding](../evaluation/execution/server.py).

Distinguish (1) primer bytes available, (2) the full body delivered through a
visible tool/command result before analytical execution, and (3) API use and
scientifically appropriate decisions. A hash alone proves none of (2) or (3).
Use transcript, worker audit and replayed source together. Freeze each
case's supported-subtask map before launch. Allow legitimate non-analytical
glue; a script cannot decide semantic suitability by itself. Record source
review and scientific review separately from mechanical checks.

Extend the existing scripted client-boundary check to inspect actual
instruction content, not merely its character count. Verify full primer
delivery below output limits and installed-wheel dependencies before live
inference. Keep fresh bundle UUIDs/paths in a provenance manifest or report,
outside the numerical `results.json` that must replay deterministically.

Use the corrected analyses for a small explicit cross-check of shared
calculations and diagnostics. **Defer the public `check_values` helper.** A
field-labelled comparison script/receipt is sufficient here. Match inputs,
sample/taxon identities, transformations, estimands and numerical conventions
before comparing values. Record tolerances and discrepancies; agreement is
not scientific validation. Compare rarefaction simulation means against exact
expectations with the Monte Carlo error of the mean, not the within-subsample
SD. This achieves the requested cross-check without adding a generic checking
framework or another API contract.

## Handoff

Claude next: revise the plan/primer and write the two methods contracts,
resolving the multiplicity family and estimator boundaries explicitly. Codex
then checks the changed contracts and implements the bounded sprint-7 work;
Claude reviews before freezing and running sprint 8. No live run is launched
by this critique, and the original optional-use observations remain unchanged.
