# Calibration design critique and protocol closure

Reviewed `4a80b5f`, 1 November 2026: current protocol, agreed sprint plan,
`docs/sprint-4-calibration.md`, integration README and aggregate calibration
summary. **No P04 answer or adjudication files were accessed.** Its independent
semantic review belongs to another delegate. No live calls or production
changes were made.

**Recommendation:** close the earlier missing-data protocol findings; accept
offline revision towards realistic multistep tasks; retain the 96-trial,
two-session analyst design. A second calibration round needs a new explicit
trial-count authorisation. Do not adopt blanket double traps or infer pilot
efficacy/reviewability from the calibration ceiling.

## Previous protocol findings are closed

The current text defines separate common-valid paired sets for flawed and
intact reviews, n_S and n_A. Both arms use the same packages for each contrast;
unpaired verdicts are descriptive only. Margins now retain their intended
one-/two-package meanings through 1/n and 2/n, and the existing minimum of
six applies to the actual analysed sets. C remains separately reported and
gated. Bootstrap sampling within each valid set cannot produce the earlier
zero-denominator draws; an empty set is explicitly undefined.

The broad-class-or-field attribution alternative is removed. Specific frozen
criteria govern detection. Rule 5 no longer claims to isolate enforcement as
the causal mechanism. The prior missingness counterexample now gives ΔS = 0
on its eight common-valid pairs, as it should. See [check.py](check.py) and
[receipt.json](receipt.json).

These definitions resolve the last two review findings without new thresholds.
Results remain conditional on the selected valid packages, as the protocol
states. They are not an estimate over all potentially attempted reviews.

## What calibration establishes

The supplied aggregate summary records eight completed trials in each arm,
seven acceptable and one provisional in each. Thus the prespecified direct
≥7/8 **family-revision trigger is met without deciding P04**. The safe
conclusion is that this calibration bank provides little opportunity to
demonstrate an accuracy improvement at the observed performance.

Three stronger claims in the calibration document should be narrowed:

1. **The unrun pilot has not reached rule 2.** Calibration success does not
   establish D ≥ 0.90 on twelve pilot families, different instances and two
   sessions. Four pilot families were not represented in this calibration.
   Revision is required by the calibration rule; a pilot stop is a plausible
   forecast, not an observed decision-table result.
2. **Success does not isolate why the bank was easy.** The observed answers
   may support the reported use of factual cues, but moving those facts does
   not necessarily make the analytical decisions difficult. The same capable
   analyst may resolve the larger task equally well. “Reading” versus
   “vigilance” is not a measured causal distinction here.
3. **Reviewer/reproducibility advantages have not been measured by these
   calibration outcomes.** Cost and recorded usability problems are supported
   findings. The document's statement that calibration already shows
   reproducibility and reviewer endpoints are where the arms differ goes
   beyond the available experiment. Integration reproduction is a capability
   check, not a comparative reviewability result.

## A defensible harder bank

**Keep necessary information explicit and accessible.** Moving units,
sampling history or taxonomic provenance to the file where they naturally
belong is reasonable. Do not turn “no signposting” into a ban on necessary
definitions or provenance. A synonym mapping or description of an unpicked
fraction may be indispensable to identifying the estimand. Removing it would
produce an unresolved scientific question, not a better trap. The task should
still specify its target clearly, and both arms must receive identical
references within the permitted environment.

**Use multistep workflows for scientific reasons.** Some real questions
require an ID join, unit reconciliation and a numerical analysis. Such
compositions are useful candidates. A requirement for exactly two unrelated
pitfalls in every item is artificial and risks making the bank a puzzle test.
Two all-or-nothing success probabilities multiply only under statistical
independence; conceptual separation of pitfalls does not establish that.
Even under independence, 0.95 × 0.95 = 0.9025 and 0.98 × 0.98 = 0.9604, so
doubling easy pitfalls does not guarantee leaving the ceiling. These are
illustrations, not fitted success probabilities.

For every accepted composition, independently verify the correct joint
handling and the meaningful one-error/two-error alternatives. Ensure that
errors cannot cancel numerically or that one correction does not silently
remove the other. Preserve the end-to-end acceptability endpoint; optional
per-error diagnostics can explain failures without changing its threshold.

**Maintain matched, difficult controls.** Controls should retain the same
scientific question, file structure, scale, provenance burden and substantive
analysis as their trap twins, replacing only the problematic facts. Harmless
irregularities can test overcorrection if their harmlessness is entailed by
the materials. Do not make controls trivially clean while trap difficulty
comes from an unrelated extra workload. More rows, taxa or dictionary entries
alone do not demonstrate greater scientific difficulty.

Mixed composites may span both the current `toolkit` and `other` strata. Fix
their classification and the resulting family balance prospectively; do not
assign a stratum after seeing which arm succeeds. Preserve the agreed
reference-data contribution and independently recompute all amended keys.

**Use the blind cue audit as evidence, not an oracle.** A materials-only
reviewer can expose ambiguous targets, hidden assumptions and excessive
coaching. Its success does not prove realistic difficulty; its failure does
not prove unfairness. An alleged unintended trap may be a real key defect or
a reviewer false alarm. Adjudicate each against the facts and sufficiency
witness, retain legitimate alternative answers, and keep numerical key
verification separate from the cue audit.

## Adaptation, counts and stopping

Calibration-driven generator revision before freeze was contemplated by the
plan. Its acceptability depends on preserving all versions and outcomes,
using new disjoint instances, and freezing the revised bank and analysis
before pilot performance is observed. Do not repeatedly select compositions
for a favourable toolkit-versus-direct difference. Any extra calibration
round should have a fixed maximum and stopping rule agreed beforehand; a
repeated ceiling can close this particular development design without a
claim about frontier analysts in general.

**The current authorisation is ≤16 calibration trials and 96 analyst trials.**
The 16 calibration trials have been used. A second set of 16 would exceed
that cap; four analyst sessions would mean 192 and exceed its cap. The 5M
token ceiling is an additional bound, not permission to increase trial counts.
The parent owns the authority decision; this critique authorises neither.

If correctness evaluation stops, reviewer work still needs its agreed source:
eligible session-1 control packages in both arms. Calibration consists of
trap items and cannot silently substitute for those control packages. A
narrower reviewability study would need an explicit package-selection and
trial plan; no reviewer benefit should be reported before it runs.

## Cost and the four-session suggestion

The aggregate arithmetic checks: 124,840 counted tokens; arm medians 9,547
and 4,649.5; ratio **2.0533**. At the observed pooled median of 6,525,
1.5 × median × 96 = **939,600** counted tokens. Doubling trials gives
1,879,200 under the same cost assumption. Revised larger multistep tasks may
cost materially more; these figures are conditional projections. K ≈ 2.05
is an observed calibration ratio, not a precise estimate of revised-pilot
cost or a reason to move its provisional cutoff.

Four sessions do **not generally halve the variance of item-level ΔT**. Under
an illustrative decomposition with J families and m sessions,

`Var(mean difference) = (between-family variance + within-family variance/m) / J`.

Changing m from 2 to 4 halves only the within-family component; it adds no
independent families. With equal between-/within-family variances, total
variance falls to 5/6 of its previous value, not 1/2. The receipt includes
other illustrative ratios; none is a power estimate from the all-success
calibration. Keep two sessions and focus on the validity and relevance of the
questions before considering additional replication.
