# Sprint 4 calibration: the trap families hit the ceiling

**Claude Sonnet 5.5 handled every calibration trap in both arms, so the
pre-registered rule requires revising the families before freeze.** Claude
(Opus 5.5), 1 November 2026. Run on Barry's subscription through the qualified
supervisor. Evidence is in
[calibration-evidence/](../evaluation/pilot/calibration-evidence/) and
[integration-evidence/](../evaluation/pilot/integration-evidence/).

## What ran

- **Integration.** 4 trials on P05-cal and P10-cal, both arms. All four were
  correct, and all three integration criteria were met: successful execution,
  structured toolkit refusals, and every saved study bundle reproduced outside
  the trial. Two gate halts on organisation-managed configuration files were
  diagnosed and fixed (see the integration README).
- **Calibration.** 16 trials: 8 calibration traps × 2 arms, 1 session, 10
  minutes and 60 turns each, no retries.
  - All 16 completed, with no breach, and every worker call reconciled on its
    full request and returned value.
  - There were 0 client refusals; the prompt's tool names had been corrected
    after integration.
  - 124,840 counted tokens in total.

## Result

| Item | Direct | Toolkit |
| --- | --- | --- |
| P03-cal (percentages, not counts) | correct | correct |
| P04-cal (unpicked fraction) | correct* | correct* |
| P05-cal (spelling variants) | correct | correct |
| P06-cal (aliquots as replicates) | correct | correct |
| P08-cal (unsorted metadata, boundary) | correct | correct |
| P09-cal (duplicate valves) | correct | correct |
| P10-cal (downcore order) | correct | correct |
| P11-cal (obsolete synonym) | correct | correct |

\*Provisional pending semantic adjudication. Claude's adjudication: both
answers state the restricted T01–T08 basis and why, so both are acceptable.
The Codex delegate's independent adjudication is still pending.

- **Rule.** The [plan](sprints-3-4-proposal.md) says: "If the direct arm gets
  at least 7 of 8 calibration traps right, the families are revised before
  freeze."
- **Direct arm:** 7 of 8 acceptable without adjudication, 8 of 8 with it. The
  rule is met either way.
- **Consequence for the pilot as built.** Its decision table would stop at
  rule 2 (D ≥ 0.90: the design cannot discriminate).

## Why the traps were easy

In every direct trial, the answer named the trap in `issues` and applied the
remedy. Each remedy rests on a fact the materials state plainly, once, near
where the analyst reads first:

- P11's dictionary note reassigns the obsolete name. The answer cites it as
  "per task note".
- P09's catalogue shows left and right valves with identical measurements.
- P04 marks unpicked cells with `.`, and its dictionary defines `.`.
- P06's sample IDs carry the aliquot suffixes a–c.

These items test reading, not vigilance. Sprint 1 found the same ceiling;
the pilot-v3 families lengthened the materials but kept one salient cue per
item.

## Two findings that hold regardless

- **The toolkit costs about twice the tokens on these items.** The median
  counted tokens were 9,547 (toolkit) and 4,650 (direct), giving K ≈ 2.05,
  just over rule 4's K ≤ 2.0. The toolkit arm made a median of 9.5 worker calls
  to the direct arm's 3. Its cache reads were about 7 times higher: discovery
  output and bundle summaries re-enter the context.
- **Toolkit discoverability.** These are usability findings, not efficacy
  evidence.
  - On P04-cal the toolkit agent wrote that the "toolkit has no Shannon
    method". In fact the community method reports Shannon diversity.
  - On P05-cal the agent passed a tab-delimited table as PAST input, then
    converted it itself.

## Revision design (for Codex's critique before implementation)

The goal is items where a careful analyst can still find the problem from the
materials, but nothing points at it. Fairness stays checkable through the
existing sufficiency witnesses.

1. **No signposting.** task.md states the question only. The dictionary
   describes every field neutrally, with no consequences and no remedies. The
   trap evidence sits where it would in real data: a lab-sheet remark column,
   a provenance log, a units line in a header, a second metadata sheet.
2. **Realistic dilution.** Each item gets realistic scale:
   - 25–60 taxa and 15–40 samples;
   - 12–25 dictionary entries;
   - several innocuous irregularities that need no action, which also guards
     against agents "fixing" everything.

   The trap is one detail among many.
3. **Two independent pitfalls per trap item**, drawn from different families,
   with acceptability requiring both. Per-item success multiplies, which moves
   D off the ceiling without making any single cue unfair. Controls keep
   their innocuous irregularities and no pitfall.
4. **Blind cue audit.** A Codex delegate sees each item's materials without the
   key and lists every irregularity that, in its judgment, needs action. An
   item fails the audit if task.md or the dictionary states a remedy or
   consequence. It also fails if the delegate cannot find the trap at all
   (unfair) or finds an unintended one (key defect).
5. **Recalibrate on the revised families.** This means a second round of 16
   calibration trials, about 125,000 counted tokens at the observed rate. That
   goes beyond the 16 calibration trials in the plan, but stays far inside the
   5,000,000 Sonnet tokens Barry authorised. The same ≥ 7/8 rule applies.
6. **If the revised direct arm still reaches the ceiling,** stop the
   correctness-efficacy line for frontier analysts at this design (rule 2).
   The pilot then reports cost (K), reproducibility and the reviewer endpoints.
   Calibration already shows those are where the arms differ.

**Budget consequence.** The working analyst ceiling under the 1.5 × median
rule would be 939,600 counted tokens for 96 trials. At this cost, 4 sessions
instead of 2 (192 analyst trials, about 1.9 million at 1.5 × median) would fit
the 5,000,000 authorisation and roughly halve the variance of ΔT. This is
proposed for the revised design, not adopted.

## Not done

- No family has been revised yet. The design above goes to Codex first.
- P04-cal's second adjudication (Codex delegate) is pending.
- No threshold was changed. K's provisional 2.0 limit stays as written.
