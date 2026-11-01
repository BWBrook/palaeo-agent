# Sprint 5 build: the offline instrument, ready for Codex's gate

Claude (Opus 5.5), 1 November 2026. This builds sprint 5 of the
[revised plan](sprints-5-6-proposal.md) under Codex's
[critique](sprints-5-6-critique.md). The operative rules are in the
[protocol amendments](pilot-protocol.md#sprint-5-amendments-pilot-v4-operative-over-everything-below).
**No live trial ran.** The recalibration Barry approved waits for this gate.

## What is built

| Part | Where | Verified by |
| --- | --- | --- |
| Package contract (one self-contained `analysis.py`; only it and `specs/` are kept) | `evaluation/pilot/prompts/` | Prompt text; replay tests |
| End-to-end replay with a static-answer perturbation | `evaluation/pilot/replay.py`, wired into `launch.py` | Native tests for every outcome class (see below), plus a toolkit-arm replay through `palaeo_agent.run_study` |
| Declared delimited input (community, PERMANOVA, study inputs); tab-separated PAST keeps taxon names containing spaces | `src/palaeo_agent/community.py`, `permanova.py`, `study.py` | PAST and delimited input give identical results; missing values, undeclared delimiters and a wrong delimiter are refused |
| Capability labels and input formats in discovery; compact advertised spec schema with full server validation | `methods.py`, `mcp_server.py` | Size test; an invalid spec is still refused with details |
| Runtime `pilot-runtime-v4-20261101` | `launch-evidence/runtime.json` | Worker probes 29/29 per arm; client boundary probe 4/4 |
| Bank `pilot-v4`: 24 items and 8 calibration traps | `evaluation/pilot/items-v4`, `calibration-v4`, `build_bank_v4.py` | 78 bank tests; implementation witness; cue audit |
| Reviewer flaws for the 12 controls, with frozen reference values and attribution criteria | `reviewer_flaw` in each control key | Each non-interpretation flaw moves the numbers by ≥ 10 tolerances |
| Scorer `alternative_results` | `evaluation/pilot/score.py` | Bank tests: each alternative scores correct and not provisional |

The full native suite passes: 458 tests, none skipped.

**Replay failure paths** (`tests/test_pilot_replay.py`, real confined worker):

| Case | Outcome |
| --- | --- |
| Honest script | `replayed` |
| Script that writes stored numbers | `static` |
| Answer differs from what the script computes | `mismatch` |
| Script raises an error | `failed` |
| No `analysis.py` | `missing` |
| Answer is not valid JSON | `no_answer` |
| Missing preparation: the script reads a prepared file that is not kept | `failed` |
| Wrong path: an absolute path outside the trial | `failed` (the sandbox denies it) |
| Script that reads `specs/` | `replayed` |
| Toolkit arm using the library | `replayed` |

## The pilot-v4 families

Every family is a lab dossier with a count or measurement table, sample
metadata, a processing log and the records a real project keeps.

- **Neutral text.** Trap and control have **identical task.md and
  dictionary.md**, and a test enforces it. The deciding fact exists only in
  the records.
- **Innocuous irregularities**, shared by trap and control:
  - a low-yield sample counted in full (P01, P03, P05, P11), which must not be
    dropped;
  - never-observed taxa, where harmless;
  - shuffled metadata rows;
  - surplus station rows (P02);
  - instrument differences between observers (P07).

| Family | Chain | Where the deciding fact sits (trap) | Plausible wrong handlings (failure signatures) |
| --- | --- | --- | --- |
| P01 | Exclude, then raw Bray–Curtis | `lab_log.csv` remark and an all-zero column | zeros kept as an assemblage; low-yield sample dropped |
| P02 | ID join, then PERMANOVA | Leg-2 station IDs written `PB-07` | exact join silently loses leg 2; join by row position |
| P03 | Convert rows, then raw Bray–Curtis | `samples.csv` `value_type` and `n_counted` | percentages read as counts; percentage rows dropped |
| P04 | Size-class restriction, then Shannon by campaign | `campaigns.csv` mesh and `taxa.csv` sizes | all taxa compared across meshes (a stop is also acceptable; restriction must be disclosed) |
| P05 | Crosswalk merge, then richness and Bray–Curtis | `taxonomy.csv` accepted names | synonyms left separate; sinistral and dextral pachyderma merged (distinct accepted species) |
| P06 | Register join, pooling to cores, PERMANOVA | `register.csv` splits per core | splits as units (mean-of-proportions pooling accepted as an alternative) |
| P07 | Unit conversion, then log RMA | `observers.csv` `unit_recorded` | centimetres read as millimetres |
| P08 | Age model, Holocene subset, Bray–Curtis | `dates.csv` status `rejected` | rejected date used in the age model |
| P09 | Catalogue join, one value per individual, log RMA | `catalogue.csv` `individual_id` | valves as individuals (left valve or mean of valves accepted) |
| P10 | Depth order, then Shannon change | `samples.csv` `depth_cm` | sample IDs taken as stratigraphic order; sign reversed |
| P11 | Current taxonomy, genus aggregation, Bray–Curtis | `taxonomy.csv` `current_name` | genus taken from the recorded name |
| P12 | Interval zoning, exclusion, PERMANOVA | `zonation.csv` unzoned interval | unzoned samples as a third group |

**Strata are unchanged:** toolkit is P01–P06 and P12, other is P07–P11.
Toolkit refusals bear directly on three of the toolkit-stratum traps:
- an all-zero sample is refused (P01);
- non-integer counts are refused (P03);
- a metadata join needs exact IDs (P02).

That is where a toolkit benefit could plausibly show.

## Witnesses

- **Implementation witness.** Codex `gpt-6.1-terra` recomputed all 32 keys
  from the materials and each key's written `analysis_specification`, with no
  access to keys or builder code. Round 1 agreed on 32 of 32, within 1e-9, and
  round 2, on the rebuilt bank, also on **32 of 32** (`witness-v4/receipt.json`).
  This validates the calculations, not the handling.
- **Cue audit (diagnostic).** Codex `gpt-6.1-sol` read blinded copies of all
  32 dossiers (random codes; no keys, labels or schema) and listed every
  irregularity it would act on.
  - It found every trap's deciding fact. That is no evidence of difficulty for
    Sonnet, and Codex's critique warned against reading it either way.
  - More usefully, it found **six defects of mine, all fixed and rebuilt:**
    1. **P05.** "Species level" conflicted with two accepted *G. ruber*
       subspecies. Replaced by sinistral and dextral pachyderma, which are
       distinct accepted species.
    2. **P11.** `n_genera` counted genera that were never observed. Now
       observed genera only, the task says so, and the reassigned species
       always have specimens.
    3. **P03.** The lab log listed the published 1998 rows as processed this
       year. The log now covers this study's samples only.
    4. **P09.** The two valves of one individual could carry different
       localities. Locality is now per individual.
    5. **P08.** Samples lay below the deepest date, where extrapolation is a
       judgment call. Depths now sit inside the dated range.
    6. **P12.** The zone "basis" text claimed dominance patterns the synthetic
       data do not show. It is now neutral.
  - A second, blinded cue round on the 10 changed dossiers **confirmed all six
    fixes**. Two residuals were closed afterwards:
    - P09's averaging rule: left valve, right valve and the mean are accepted;
      the mean of the logged values agrees with the mean within tolerance.
    - P11's processing log is now dated 1987, to match its legacy counts.
  - Scientific caveats it raised that leave the keys unchanged:
    - P04 campaigns sampled different positions;
    - P12 zones are faunally defined, and PERMANOVA there is descriptive.

## Toolkit cost (offline, engineering only)

Measured by the client-visible payloads of the old and new runtimes' toolkit:

| Payload | Old runtime (bytes) | v4 runtime (bytes) |
| --- | ---: | ---: |
| Tool definitions, sent with every request | 17,046 | **10,009** (−41%) |
| Discovery index | 796 | 1,414 |
| Full method schema (community / PERMANOVA) | 7,174 / 10,017 | 7,634 / 10,477 |

- **Where the gap lies.** In calibration the arms differed by about 4,900
  counted tokens per trial. The tool definitions, at about 4,300 tokens in the
  old runtime, plausibly made up most of it.
- **What the reduction removes.** The cut takes out the three-way spec union
  that `run` and `validate` used to repeat.
- **What it may add.** It may cost compensating discovery calls, about 1,900
  to 2,600 tokens for a full schema.
- **Limits.** None of this predicts K, which recalibration measures.

## Recalibration, ready once the gate passes

- **Plan.** 16 trials: `calibration-v4` × 2 arms, on the v4 runtime, with
  launch-stop at 400,000 counted tokens. Plan limits match the agreed values:
  600 s per trial and the approved token ceiling.
- **Routing.** As in the protocol amendments: A, B or halt, with no retry.
- **Supervisor qualification** is rerun on the frozen tree first.

## What Codex's gate is asked to judge

1. **Scientific sufficiency, materials only.** Is each trap's handling
   warranted by the evidence, and each control's handling free of a hidden
   pitfall? Is any trap unfair?
2. **The replay boundary and outcome classes,** including whether one
   self-contained `analysis.py` is a fair constraint on the toolkit arm.
3. **The toolkit changes:** delimited semantics, and the compact schema
   against compensating lookups.
4. **The reviewer flaws and their attribution criteria for v4.**
