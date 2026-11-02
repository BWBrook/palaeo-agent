# Recalibration on pilot-v4: halted at trial 9 for diagnosis

**Review update, 2 November 2026.** Codex confirms T005 as wrong for the
requested all-sample estimand and accepts a continuation containing only
T010–T016 after qualification of the narrowly repaired launcher. The original
nine records and halt stay immutable. See
[the review and continuation conditions](recalibration-authentic-review-20261102.md).
No remaining trial has been launched by that review; the routing is still
halted/undetermined until the continuation runs and is adjudicated.

Claude (Opus 5.5), 1 November 2026. This run is the single recalibration
round Barry approved ("Extra calibration round is approved, if you still deem
it required"), launched after Codex accepted the gate on `e86714b`. Freeze
`3e31feb`:
- runtime `pilot-runtime-v4-freeze-20261101`, whose wheel `a3febf7…` is
  identical to Codex's review build;
- worker probes 29/29 per arm, client boundary probe 4/4;
- supervisor qualification passed on the frozen tree;
- the plan bound by hash.

Full records are in
[run-records/recalibration-v4-20261101](../evaluation/pilot/run-records/recalibration-v4-20261101/).

## What happened

Nine of the 16 planned trials ran, using 132,338 counted tokens of the
400,000 allowed. The launcher then halted on a reconciliation problem in T009,
and T010–T016 were never launched.

| Trial | Item | Arm | Outcome | Replay (mechanical) | Counted |
| --- | --- | --- | --- | --- | ---: |
| T001 | P11-cal | direct | correct | replayed | 10,225 |
| T002 | P11-cal | toolkit | correct | replayed | 24,737 |
| T003 | P05-cal | direct | correct | replayed | 7,686 |
| T004 | P05-cal | toolkit | correct | replayed | 17,180 |
| T005 | P03-cal | toolkit | **wrong** (detected, mishandled) | replayed | 20,443 |
| T006 | P03-cal | direct | correct | replayed | 9,654 |
| T007 | P08-cal | toolkit | correct | replayed | 13,524 |
| T008 | P08-cal | direct | correct | replayed | 7,373 |
| T009 | P06-cal | toolkit | correct; halted by the instrument | replayed | 21,516 |

- **Clean execution.** All nine trials exited normally. There were no client
  refusals: the exact tool names now in the prompts work. No exports were
  refused.
- **Replay.** Every package replayed mechanically, including the static-answer
  check. Each still needs the provenance review the protocol requires before
  it counts toward R.

**T005, scientific error, provisional pending adjudication.**
- What the agent did: the toolkit agent found the 1998 percentage rows and
  excluded them. It judged that they "could not be converted to counts
  faithfully" and reported the mean over the 16 count samples.
- Why that is wrong: the reconstruction is exact from `n_counted`, and the
  task asks for all samples, so the answer matches the `percent_rows_dropped`
  signature.
- Claude's first adjudication: **wrong**. The handling was disclosed but
  unwarranted, and it answers about a different set of samples. A second,
  independent adjudication is still needed.
- What it was not: the toolkit's integer-count refusal message never appears
  in the transcript, so it did not steer this decision.

## Halt diagnosis (T009)

One `palaeo_discover(method="permanova")` result differed from its audit
record in exactly two places: the schema's seed `maximum`. The audit record
holds 2^64 − 1 (18446744073709551615). The client delivered
18446744073709552000.

- **Cause.** Claude Code re-serialises tool results' JSON numbers as IEEE-754
  doubles, which cannot represent integers above 2^53 exactly.
- **What it was not.** Nothing crossed the boundary, the worker returned what
  it audited, and the model saw a schema bound rounded in the 16th digit.
- **Why it halted.** The reconciliation compared values exactly, which was
  correct to do. Under the frozen routing, an instrument failure halts for
  diagnosis, with no retry and no extra round, and that is what the launcher
  did.

**Initial repair, superseded in review.** Converting all large integers to
doubles also accepted different exact integers, including 2^64−1 and 2^64−2.
Codex replaced it with an exact exception for the two PERMANOVA discovery
schema seed maxima observed in T009: audited 18446744073709551615 may arrive
as 18446744073709552000. Other fields, scientific results, tool inputs and
nearby integers retain strict comparison. All nine saved trials reconcile
under this repair; T009 has 14 matched worker calls and no problems. T009
stays marked incomplete in the original ledger. The repair has not been used
for a live trial.

## Routing status

The routing is **not yet determined.** The direct arm is 4 of 4 correct, with
4 direct trials (P06, P10, P04, P09) unlaunched. The frozen routing defines
two outcomes from here:
- **Branch A** needs all 8 direct outcomes and direct ≤ 6/8.
- **Branch B** needs direct ≥ 7/8.

Neither can be decided on 4 trials. Halting for diagnosis is the defined
outcome so far.

**Proposal for Codex's reviewed decision.** Launch the 7 unlaunched trials,
T010–T016, under a continuation plan bound to the repaired launcher.
- This retries nothing (T009 is not rerun). It stays inside the approved round
  and its ≤ 16 trials. At the observed rate it uses about 100,000 more counted
  tokens, so the round total stays under 400,000.
- The 9 completed records stand as they are.
- If Codex prefers not to resume, the round ends here as a halted, partial
  calibration, and the bank's discriminating power stays unknown.

## Cost (descriptive)

Median counted tokens were 20,443 in the toolkit arm (5 trials) and 8,670 in
the direct arm (4), a ratio of about 2.36. This unbalanced descriptive ratio
includes toolkit-only T009 and is not a matched treatment-effect estimate.
The toolkit arm made 8–14 worker
calls against the direct arm's 3–5.

The observed ratio remains above two. Under the new package contract, toolkit
agents write a study spec, run it through the library, read the bundle back
and rerun the script. These are observed sources of work. Changed tasks,
contract and incomplete pairing prevent isolating the effect of the schema
reduction from these runs alone.

## Next step: recommendation

Barry's direction, via Codex (Codex chat, 1 November 2026, exact): "A ceiling
or a null result is useful evidence." And: "Let the use case inform what
statistical capability to build next; don't add complexity merely to make
the toolkit look advantageous."

Claude's reading of the evidence so far:

- **Correctness.** Across 24 calibration trials on two bank designs, the
  direct arm has made no error (12 of 12, counting 8 in v3 and 4 in v4). The
  only error came from the toolkit arm. This is small-sample, development
  evidence, but it consistently fails to show headroom for a correctness
  benefit on single-analysis tasks.
- **Cost.** The toolkit roughly doubles to 2.4-fold the counted tokens.
- **What the toolkit plausibly does offer** is the saved, verifiable bundle,
  but the new package contract now makes the direct arm reproducible too.
  Replay of both arms succeeded mechanically.

**Recommendation.**
1. **Finish the approved round, if Codex agrees to resume.** The 7 trials
   cost little, and they settle the descriptive A/B classification the bank
   was built for.
2. **Do not spend the 96-trial pilot or the 24/48 branch-B allocation
   automatically.** The result that could justify them is a direct arm below
   the ceiling together with a toolkit arm that is not worse. Even then, the
   cost difference must be weighed against the gain.
3. **Run the authentic-workflow complement next, as two small cases.**
   - **Coed Duon Llanvirn** (Codex's candidate): composition change through
     the section, and its robustness to counting totals and abundance
     representation. This is a supported, multi-run workflow, including the
     toolkit's sensitivity comparison, so it tests whether an
     *involved* workflow benefits from the API.
   - **Dielasma allometry**: about 100 real brachiopod measurements from
     three localities, already in `benchmarks/past/legacy-data/dielasma.dat`.
     The research question is whether growth is isometric and whether the
     localities differ in shape. That needs slope inference the toolkit
     lacks (it is descriptive RMA only). The session would show directly
     what agents need and do without, which is the "use case informs
     capability" probe.
   - **Protocol.**
     - One fresh optional-toolkit session per case, with no forced use. The
       same brief, data, libraries, budget and runnable deliverable apply
       throughout.
     - A direct-only twin session runs only where a named decision depends
       on it.
     - Sessions are isolated, with no tutorial recipes, benchmark outputs or
       answers in the workspace.
     - Record adoption or decline, friction, unsupported needs, cost, and an
       independent replay and scientific review.
   - **Cost.** Two to four sessions, likely under 150,000 counted tokens in
     total.
   - **Authorisation.** This is a new kind of live use, so it needs Barry's
     go-ahead.

## Final outcome: the round is complete and routes to branch B

Claude (Opus 5.5), 2 November 2026.

**Continuation.**
- Codex accepted resuming T010–T016 only, with no rerun of T009.
- It narrowed the reconciliation repair to the two observed PERMANOVA
  seed-maximum substitutions, and prepared a continuation plan (sha256
  `dcbad5a9…`).
- Its review is
  [recalibration-authentic-review-20261102.md](recalibration-authentic-review-20261102.md).
- Immediately before launch, the plan fingerprints matched the machine.
- The client was 2.1.309, which Codex had qualified; the original run used
  2.1.308. That is a recorded execution-version deviation. The scientific
  runtime, prompts, bank and scorer are unchanged.
- Records:
  [run-records/recalibration-v4-continuation-20261102](../evaluation/pilot/run-records/recalibration-v4-continuation-20261102/).
- All seven trials completed. Every trial exited normally, with no breach, a
  consistent reconciliation, no refused exports and a mechanical replay.

| Trial | Item | Arm | Scored | Adjudicated | Replay | Counted |
| --- | --- | --- | --- | --- | --- | ---: |
| T010 | P06-cal | direct | correct | correct | replayed (perturbation changed) | 10,746 |
| T011 | P10-cal | toolkit | correct | correct | replayed (changed) | 22,435 |
| T012 | P10-cal | direct | correct | correct | replayed (changed) | 6,052 |
| T013 | P04-cal | toolkit | correct_unresolved, provisional | **correct (justified stop)** | replayed (no numbers) | 10,093 |
| T014 | P04-cal | direct | correct_unresolved, provisional | **correct (justified stop)** | replayed (no numbers) | 9,429 |
| T015 | P09-cal | toolkit | correct | correct | replayed (changed) | 10,153 |
| T016 | P09-cal | direct | correct | correct | replayed (changed) | 5,608 |

**T013 and T014 adjudication (Claude).**
- Both stopped and named the deciding fact: every 2017 core's 63–150 µm
  residue was archived, not picked, so the 2017 >63 µm assemblage does not
  exist.
- Both explained why comparing 2017 >150 µm with 2021 >63 µm would confound
  campaign with size fraction. That is the key's accepted "justified stop"
  alternative.
- T013 also reported, in its issues, the like-for-like >150 µm means
  (2.7790, 2.7668) and the 2021 >63 µm mean (3.0437). All three equal the key
  values.
- Neither stop is over-cautious, because the target is not identified in this
  item by design.

**T005 second adjudication (Codex, sealed, materials and answer only):**
wrong. It answers the 16-sample count subset (0.3327) instead of the requested
all-sample population. Conditional reconstruction gives 0.3129 over 276 pairs.
This agrees with Claude's adjudication.

**Provenance.**
- Codex source-reviewed T001–T009: all compute from the supplied materials
  (R = 9/9).
- Claude skimmed T010–T016: each script reads only the item's materials (and
  `specs/` for T011) and contains no stored long decimals. T013 and T014 report
  no numerical result, so their perturbation is not applicable.
- On mechanical replay and this review, R = 16/16 launched trials replayed.
  T009's original ledger halt stays in the flow accounting.

| Arm | Adjudicated correct | Error |
| --- | --- | --- |
| Direct | **8/8** (one a justified stop) | none |
| Toolkit | 7/8 (one a justified stop) | T005, a population change on P03 |

**Routing.**
- The direct arm is 8/8, which is ≥ 7/8, so the frozen routing gives
  **branch B**. The ceiling persists on the redesigned bank, as it did on v3.
- The classification would be the same if T014 had been judged wrong, since
  7/8 is also ≥ 7.

**Spend.**
- 74,516 counted in the continuation, so the round total is **206,854 of
  400,000**.
- Median counted tokens: toolkit 18,812 and direct 8,558, a ratio of
  **about 2.2**.

**What branch B means here.**
- Branch B prescribes a descriptive checkability study: 24 control analyst
  trials and up to 48 reviewer trials, outcomes B1–B5, with no expansion
  verdict.
- Codex and Claude agree, following Barry's direction, that a ceiling does not
  by itself justify spending on it.
- The open question it would address is whether toolkit packages are easier to
  review. The authentic sessions bear on that directly: neither analyst
  adopted the toolkit. Both direct-style packages could be replayed, traced
  and refereed by an independent model (with the qualifications in Codex's
  review).
- **Claude's recommendation: classify the round as branch B, and do not run
  the 24/48 trials.** No named development decision depends on their result.
  Either B4 or B5 would leave the next step the same: improve the analyses and
  their verification on real cases, not the API's scope.
