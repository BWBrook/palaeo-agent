# Recalibration on pilot-v4: halted at trial 9 for diagnosis

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

**Repair** (with a test; not yet used live). Reconciliation now compares both
sides in the client's number form: only integers beyond 2^53 are compared as
doubles. A genuinely different large value still fails. Re-reconciled offline
under the repair, T009 is fully consistent: 14 worker calls, with no problems.
T009 stays marked incomplete in the ledger, and its record is unchanged.

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
the direct arm (4), a ratio of about 2.4. The toolkit arm made 8–14 worker
calls against the direct arm's 3–5.

The smaller tool definitions did not lower the ratio. Under the new package
contract, the toolkit agents write a study spec, run it through the library,
read the bundle back and rerun the script. The calls and context that adds
outweigh the schema saving. That bears directly on Barry's hypothesis below.

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
