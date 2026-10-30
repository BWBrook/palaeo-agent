# Staged implementation plan

Status: staged route authorised by Barry on 30 October 2026, including source
capture and a private GitHub main branch. The founding design tranche is complete
when these documents are coherent, the source inventory states its gaps, and
the local Git repository has a clean initial commit. No numerical validation is
implied by completing this tranche.

Stages 1 (bounded legacy-corpus acquisition) and 2 (one complete operation)
have now been implemented and checked; see
[the first implementation results](tranche-1-results.md). The current PAST 5
example corpus remains unenumerated. Stage 3 describes the community tranche.

The descriptive community workflow in stage 3 has since been implemented;
see [tranche 2 results](tranche-2-results.md). The comparative agent experiment
has not been run. Its accepted development principles and provisional
confirmatory design are documented in [evaluation.md](evaluation.md).

## 1. Ground the corpus and select the first comparison

Inventory all publicly accessible PAST 5 example sources, including worked
examples in the manual and help articles. Distinguish current examples,
legacy examples and datasets available only inside distributions. Freeze source
scope and record unavailable material rather than claiming universal discovery.

Create a machine-readable inventory once actual datasets are acquired: source,
identity, attribution/terms, original format, checksum, documented procedure,
PAST version, reference-output availability and planned method coverage. Barry
explicitly authorised storing his uploaded sources and captured vignettes in
the private development repository. Preserve third-party rights and review
redistribution before public release; see [THIRD_PARTY.md](../THIRD_PARTY.md).
Record corrections as derivatives, never overwrite originals.

Choose one publicly available tabular example with a straightforward numerical
method and defensible expected result. If a current PAST example cannot yet be
acquired, use an explicitly labelled synthetic fixture to exercise plumbing
without claiming PAST compatibility.

Completion evidence: a bounded corpus inventory and one fully specified
comparison with known reference provenance and predetermined acceptance rules.

## 2. Build one complete operation

Create the Python package and environment. Implement one useful operation,
request/result types, CLI, method discovery and a saved evidence bundle. Use
one numerical backend and one small real example where possible.

Verify numerical correctness with an analytical or independently computed
fixture. Exercise meaningful failure cases such as duplicate sample IDs,
incorrect metadata alignment and invalid values. Reopen outputs in a fresh
process and rerun the saved specification. Do not add placeholder analyses,
network services or a broad framework around this first operation.

Completion evidence: an agent can discover, validate, run and inspect the
operation through Python and CLI, and another process reproduces its outputs
within the specified numerical tolerance.

## 3. Complete the community-analysis demonstrator

Add selected diversity metrics, explicit transforms, Bray-Curtis/Jaccard
distances and an initial ordination. Prefer PCA or PCoA before NMDS so the first
workflow has fewer stochastic and convergence choices. Add NMDS and group
comparisons only with appropriate diagnostics and supported experimental
designs. Include figures and numerical outputs together.

Test a real question with sample metadata, a suitable baseline, and a small
prespecified sensitivity analysis. Compare the experience with an ordinary
script calling the same underlying libraries. Record errors prevented, evidence
omitted and reproducibility failures; token counts and speed are secondary.

Completion evidence: the saved workflow answers the chosen question, reproduces
from frozen inputs, and remains scientifically interpretable under its stated
limitations. An independent agent reviews central numerical and inferential
claims before this capability is treated as accepted.

## 4. Expand the PAST comparison suite

Work through the frozen public-example inventory in coherent method families.
Every dataset receives a disposition, including cases pending acquisition,
reference outputs, rights clarification or a method outside current coverage.
Set tolerance and comparison rules before inspecting discrepancies. Investigate
differences without changing settings just to obtain agreement.

Use analytical controls and independent implementations in addition to PAST.
Check the same relevant settings and preprocessing, not merely similarly named
menu entries. Keep stochastic uncertainty and equivalent ordination solutions
distinct from numerical errors.

Completion evidence: a report with explicit denominators for datasets,
documented workflows, method/setting combinations and tested outputs. Passing
selected cases supports those comparisons, not a claim of full PAST parity.

## 5. Improve agent integration and grow scientific scope

Add a thin MCP adapter if it materially improves access in the chosen clients.
Test the same scientific core with Codex and Claude when the available sessions
allow it. No live model credentials or provider dependency are needed by the
package itself.

Choose the next scientific family from demonstrated research demand and gaps
in existing tools. Assess numerical implementation, relevant datasets,
computational cost and validation references before committing to coverage.

Before first release, settle the name and software licence, verify dependency
and dataset redistribution terms, document AI contributions with actual model
versions, and present the release artefacts for Barry's review.

## Reporting and unresolved choices

Keep progress in this plan until it needs a dedicated tracking surface. Report
at complete capabilities, consequential scientific choices or real blockers.

The first benchmark is Dielasma descriptive RMA regression, with independent
reference calculations and acceptance criteria in
[first-comparison.md](first-comparison.md). The first runtime is Python 3.12,
with NumPy, Pydantic and Matplotlib. The project name is a taste
decision that can wait; it does not block implementation. A choice about a
scientific estimand, unsupported sampling design or unexplained comparator
disagreement must be resolved before making a validation claim.

No heavy compute, public hosting, external correspondence, PAST installation
or numerical implementation was undertaken in the founding tranche.
