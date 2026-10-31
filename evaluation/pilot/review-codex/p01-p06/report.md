# Independent review: P01–P06

Baseline: `71f29d1`; bank introduced at `4bf28f8`. Six trap/control pairs and
four calibration instances were recomputed from their materials: **16 items**.
No generator code, toolkit code or keys were read before prediction sealing.
The reference uses standard-library rational arithmetic for Bray–Curtis and
PERMANOVA sums of squares, and `math.log` for Shannon diversity.

The material snapshots and hashes preserve the input state while Claude
continues development. Predictions were sealed and reported to the parent
before keys were opened:

`13548922b74011ba681882a9b5dde3a7728011456fe19c21f7b5e7967e289938`

`recompute.py` creates the predictions and seal; `compare.py` reads the seal
before opening only `key.json`, verifies prediction/script hashes, and creates
the comparison. Both refuse to replace their outputs. Repeat in a fresh copy
of the scripts and material snapshots to preserve these initial records.

## Outcome

**All 16 keyed numerical targets are reproduced exactly** (largest absolute
floating-point difference: 0). For three items those are conditional,
changed-target calculations, not uniquely identified answers to the stated
task. One failure signature is numerically wrong. The numerical agreement does
not validate the sufficiency witnesses.

| Items | Independent handling | Assessment |
|---|---|---|
| P01-control | Transpose taxa-by-core table; all 13 cores | Numeric and witness pass |
| P01-trap | All-core target unidentified; 12-core substitute calculable | Witness/expected-complete must change |
| P02 trap/control | Canonicalise stated zero-padding convention and join by ID | Numeric pass; inferential exchangeability remains an assumption |
| P03 trap/control/calibration | Use counts, or exact percentages × known totals | Numeric and witness pass |
| P04-control | All 11 taxa, each core Shannon, equal-weight campaign mean | Numeric and witness pass |
| P04-trap/calibration | Full-community target unidentified; 8-taxon substitute calculable | Witness/expected-complete must change |
| P05 trap/control/calibration | Merge exact binomials after case/whitespace normalisation | Numeric and witness pass |
| P06 trap/control/calibration | Aliquots pooled to core; independent cores otherwise | Numeric and core-unit witness pass |

## Findings requiring resolution before freeze

### P01: “all cores” cannot silently mean observed cores only

The task explicitly requests all cores in the table. The dictionary establishes
that core 3 was uncounted, so it establishes missingness, not permission to
redefine the estimand. The key's statement that “all cores” means “all cores
with counts” adds a condition absent from the task.

All the following completions of the missing core are consistent with the
observed data and give different all-13-core means:

- A genuinely empty core: **0.7446141396204127**.
- A core identical to observed core 1: **0.7044515956117148**.
- Ten thousand individuals of the first taxon: **0.7446115803804046**.

The key's **0.6981803468241241**, with 12 cores, correctly describes the counted
subset. Accepting that result with an explicit changed-target qualification is
reasonable; penalising a justified unresolved answer would be scientifically
wrong. Either identify this as an underdetermined item or specify the target
population as observed/counted cores. The latter makes the exclusion more
explicit and should be recognised as changing task difficulty.

The `zeros_as_sample` failure signature is also wrong: it records
**0.7401269601332332**, the control-data value. Applying that error to the trap
materials actually gives **0.7446141396204127**. The discrepancy is
**0.00448717948717947**, over 44 times the absolute tolerance. Its count of
13 is correct. This can cause a scientific error to miss its intended
signature even if primary correctness scoring still rejects it.

### P04: a common taxon set is a changed estimand, not established common coverage

2017 counts for T09–T11 are unobserved. For the main trap, three possible
completions of those cells yield campaign-2017 full-community means:

- All unobserved counts zero: **1.8987194094241986**.
- Each unobserved count ten: **2.186474575115142**.
- Each unobserved count one thousand: **1.3774262242376896**.

The 2021 full-community mean is **2.241201197900627** in all three. The common
recorded taxon subset yields the keyed 2017 mean **1.8987194094241986** and
2021 mean **1.9448626201299495**, but that is explicitly a restricted target.
The calibration instance has the same structural problem; its analogous
2017 means are 1.9574135736608804, 2.226487363598464 and 1.4020584949507893.

There is a further biological gap: saying T09–T11 occur *mainly* in the extra
size fraction does not establish that other taxa lack specimens in that
fraction. Dropping three columns cannot by itself standardise fraction
coverage in the retained taxa. The key's claim that the restriction is the
only meaningful comparison is stronger than the materials support.

Accept a justified unresolved answer or an explicitly conditional subset
analysis; alternatively, supply sufficient fraction-specific data and a
clear target. Do not call an unqualified subset mean the uniquely required
answer to the current task.

## Secondary observations

P02 asks for an inferential PERMANOVA but its dictionary does not establish
core independence or exchangeability. Its requested pseudo-F and R-squared
are calculable and agree, so this is not a numerical blocker. Accept stated
assumptions rather than requiring the agent to invent sampling facts.

P06 identifies six independent core units after pooling. There are only 20
label allocations for a 3-vs-3 exact test. “999 permutations or more” can mean
Monte Carlo sampling with repeated assignments, but should not require at
least 999 distinct permutations or reject valid exact enumeration. No p-value
is requested, so this does not affect the recomputed keys.

## Difficulty and signature assessment

The consequences are mostly one standard preparation step per trap, and the
dictionaries directly state the relevant facts. Orientation plus ID matching
(P02) and pooling plus relative abundance (P06) add modest composition work;
P01/P04 ambiguity is a validity problem, not useful difficulty. This half-bank
still has substantial ceiling risk for frontier analysts. The planned disjoint
calibration, rather than confidence in prompt wording, should decide whether
it discriminates. Do not make tasks harder by removing facts needed for
identifiability.

Every supplied failure signature except P01's zero-core value agrees with the
independently computed error. The case/spacing, percentage/count, positional
join and aliquot errors all make material numerical differences. Full numeric
and signature comparisons are in `comparison.json`; alternative estimands and
non-identifiability witnesses are in the unchanged `predictions.json`.
