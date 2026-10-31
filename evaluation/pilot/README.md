# Pilot bank (sprint 4, offline) — `pilot-v2`, not yet frozen

Claude (Opus 5.5) built this on 31 October 2026 under the
[revised sprint plan](../../docs/sprints-3-4-proposal.md). It holds 12
trap/control families (24 items) and a disjoint 8-item calibration set.
[`build_bank.py`](build_bank.py) generates both deterministically, without
importing `palaeo_agent`. `tests/test_pilot_bank.py` checks that they
regenerate, and checks the design rules. These are development items, not
held-out evidence. **Nothing here is frozen until Codex's pre-freeze review.**

## Design rules, as implemented

- **Uncoached.**
  - Each trap's dictionary states a fact; the task never states its
    consequence. A test checks that no trap's issue keywords appear in its
    task.
  - Results are named neutrally. For example, P06 asks for `n`, "the number of
    observations entering the test", not for independent units.
- **Sufficiency witness.** Every key carries one: the derivation from the
  stated facts to the keyed handling. A trap whose facts do not entail its
  handling would be underdetermined; none is intended to be.
- **Twins.**
  - A control uses the same task and the same data, except where the trap
    feature itself changes the data (P01, P04, P06, P12).
  - Its dictionary replaces the trap fact with a benign one, so controls
    measure false refusals and over-caution on ordinary analyses.
- **Failure signatures.** Each trap keys at least one plausible error. The
  generator asserts that each lies at least ten tolerances from the key on
  some result.
- **Strata.** 7 of the 12 trap families bear on what the toolkit declares or
  refuses; 5 do not. The plan asked for about half each. Results are to be
  reported by stratum.
- **Real data.** P01, P02, P07 and P12 use PAST example datasets from
  `benchmarks/past/legacy-data`; their zone assignments are synthetic.
- **Exact keys.** Bray–Curtis and PERMANOVA sums of squares use exact
  rationals; logarithms and square roots are float64, computed once.

| Family | Stratum | Data | Trap fact (dictionary) | Correct handling | Keyed failure |
| --- | --- | --- | --- | --- | --- |
| P01 | toolkit | real, Hirnantian | a core's residue was lost; the export writes uncounted cores as zeros | exclude that core | zeros as a sample |
| P02 | toolkit | real, Llanvirn | field-log codes lack zero padding | join on the core number | join by position |
| P03 | toolkit | synthetic | values are percentages of a stated picked total | recover the counts exactly | Bray–Curtis on percentages |
| P04 | toolkit | synthetic | one campaign did not pick the small fraction; `.` means not picked | compare on taxa common to both campaigns | `.` as 0 / different taxon bases |
| P05 | toolkit | synthetic | transcription left case and spacing variants | merge variants by summing | variants as species |
| P06 | toolkit | synthetic | rows are three equal aliquots per core | pool aliquots into cores; 6 units | aliquots as units |
| P07 | other | real, Dielasma | L3 was measured in centimetres | convert to mm | mixed units |
| P08 | other | synthetic | the epoch boundary is at 142 cm depth | Holocene means shallower than 142 cm | deeper read as younger |
| P09 | other | synthetic | one right valve per individual; both valves sometimes catalogued | drop the left valves | both valves counted |
| P10 | other | synthetic | samples are numbered downcore | S1 is youngest | reversed age |
| P11 | other | synthetic | an obsolete combination puts a species in the wrong genus | assign it to Neogloboquadrina | genus taken from the first word |
| P12 | toolkit | real, alveolinid | transition samples have a blank zone | exclude them | blank as a third group |

**Calibration** (`calibration/`) uses the trap generators of P03, P04, P05,
P06 and P08–P11 with different seeds. Its only purposes are to check that the
bank is not at ceiling and to project costs. Pilot items are never selected or
revised on agent performance.

**Cross-check.** Four keys (P01, P02, P11 and P12) were recomputed through the
toolkit and the new study layer, with legitimate preparation, and agree to
about 1e-15. This shares no code with the generator. It is not the independent
key recomputation the plan requires; Codex does that at the gate.

## Changes in `pilot-v2` (after Codex's interim review)

Codex's [interim review](../../docs/sprint-4-interim-review.md) recomputed all
32 keys independently; the largest difference was 2.8e-17. It also found
problems with what several items ask, which `pilot-v2` repairs:

- **P01.** The task now asks about "pairs of core assemblages"; "all cores"
  had included an uncounted core whose all-core mean is not identified. The
  zero-sample failure signature is corrected to 0.74461, matching Codex.
- **P02.** The dictionary states that coring sites were random and separated,
  so inference has a design basis. "999 permutations or more" became "a
  permutation test" in P02 and P06, so P06's exact enumeration of its 20
  allocations is not penalised.
- **P04.**
  - The dictionary now states exact fraction coverage: T01–T08 occur only in
    >150 µm, which both campaigns picked completely, and T09–T11 only in
    63–150 µm.
  - The common-coverage Shannon is keyed.
  - Stopping with the coverage issue named is an `acceptable_alternative`.
- **P08.** No sample lies at the boundary. Depths are midpoints of 1 cm
  slices. The Pleistocene samples are listed as `out_of_scope_ids`, not as
  exclusions.
- **P09.**
  - The valve to use is no longer dictated. The task's unit is the individual.
  - Paired left valves have measurements identical to their right valves, so
    every reasonable handling gives the key; only double counting fails.
- **P12.** The task is now descriptive (pseudo-F and R², no p-value), because
  the facts do not establish free exchangeability along a section.

## Known limits

- **No interpretation family.** A keyed numerical answer does not fit an
  interpretation error well. The plan's interpretation class is carried by the
  reviewer flaws instead.
- **Weak calibration items.** P10's trap is a sign reversal, and its
  calibration instance has a small magnitude (0.05). P11's calibration failure
  sits 20 tolerances from its key. Both pass the generator's rule but are
  weakly separated.
- **Uncertain difficulty.** P05, P10 and P12 may still be easy for frontier
  agents. Calibration exists to tell us.

## Remaining before freeze (sprint 4, Claude)

1. Flaw specifications for the 12 control packages (6 preparation / 3 design /
   3 interpretation), each with a detectability witness and an integrity-pass
   check.
2. The scorer amendment for this bank (strata, and adherence from tool-call
   logs), and the exhaustive decision table Codex asked for, including
   balanced and null gains and reviewer-eligibility denominators.
3. The launch route:
   - the qualified Claude client, which needs Barry's authorisation for
     analyst spending; or
   - a qualified Codex client.

   Either way, with the inventory gate, turn cap and wall limit from the
   [sprint-3 review](../../docs/sprint-3-review.md).
4. Codex's pre-freeze review: keys recomputed independently from materials,
   witnesses, difficulty, flaws, scorer, thresholds and protocol.
