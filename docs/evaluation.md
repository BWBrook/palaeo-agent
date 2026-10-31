# Agent evaluation protocol

Status: development and pilot principles accepted; confirmatory design remains
provisional, 30 October 2026. Written by Claude (Opus 5.5)
following the Board discussion in the `palaeo-agent` section, thread 101. Not
an executed or frozen confirmatory design. Reviewed and amended by Codex and
a separate Claude review session (Board 2611–2614). A 28-trial feasibility smoke on development items
ran on 31 October 2026 ([results](evaluation-smoke-results.md), [instrument](../evaluation/README.md)); no
pilot or confirmatory trial has been run.

Counter-review update, 31 October 2026: [sprint 1](sprint-1-review.md) reproduced
the historical results but found incomplete credential/shared-state isolation
and prospective instrument defects. Live evaluation through the old launcher
is disabled. A replacement boundary and corrected, independently checked
instrument must precede a larger pilot. The existing smokes are development
evidence; they establish neither efficacy nor complete isolation.

## Question

The [vision](vision.md) asks whether Palaeo-Agent makes agent-led analysis more
correct, easier to check and easier to reproduce than an agent assembling an
equivalent script from general scientific libraries. This protocol turns that
question into a measured comparison.

Primary question: on tasks containing realistic data-meaning pitfalls, do
agents using the toolkit produce fewer scientifically wrong results than agents
writing direct scripts, without more false refusals or failed completions on
clean tasks?

Secondary questions: completeness of saved evidence; whether a reviewer agent
can detect an error from the saved evidence alone; cost in tokens, time and
tool calls.

The toolkit may win through enforcement, explicit declaration and evidence
capture. It must not win by holding scientific information the direct arm
lacks, or by refusing everything.

## Arms

Both arms receive the same task text, data files and data dictionary stating
what each value means. Both have the same Python environment containing the
toolkit's numerical dependencies, the same budget and the same permitted
references.

- **Direct:** no Palaeo-Agent.
- **Toolkit:** additionally a pinned Palaeo-Agent wheel and its `discover`
  output.
- **Checklist control** (pilot option): the direct arm plus a generic
  data-hygiene checklist covering IDs, alignment, missing values, value types
  and orientation. This separates the effect of the toolkit's code from the
  effect of a reminder. If the checklist captures most of the gain, that is a
  finding about the toolkit's value, not a failed trial.

The toolkit may require an agent to declare a choice, such as a missing-value
policy, value type or zero handling. It must not supply the correct choice for
a task. Before a revision is pinned for testing, audit its schemas and
discovery text for task-specific hints.

## Items

Each item contains task text, input files, a data dictionary, its class, an
answer key and provenance. The key states the expected outcome category,
numerical answers with tolerances, and the failure signature of the pitfall.

- **Trap:** the materials contain what is needed to avoid the pitfall, but a
  common handling gives a wrong answer with a known signature.
- **Clean twin:** the same analysis and data without the pitfall. The correct
  outcome is completion with correct numbers, without unjustified refusal or
  warnings that lead the agent to abandon a defensible analysis.
- **Underdetermined:** the materials lack information that the answer depends
  on, for example integer-valued percentages with no stated value type. The
  correct outcome names the missing information and either stops or proceeds
  under a declared assumption with its consequence stated. An undeclared guess
  is wrong even when its numbers happen to match one reading.

Every trap has a clean twin. Answer keys never reward a scientifically
unjustified automatic correction, such as a guessed orientation or a silent
merge of taxon labels.

## Development catalogue

Everything below has been discussed openly and the toolkit may be built
against it. These items support pilots and debugging, never efficacy claims.

| ID | Pitfall | Common wrong handling | Correct outcome |
| --- | --- | --- | --- |
| D1 | Dielasma locality columns padded with `.` | Complete-case filtering across all columns: L1 raw slope ≈ 0.8036 from 35 rows | Declared pair only: 0.8428 from 103 rows, exclusions recorded |
| D2 | Proportions presented as counts | Count-dependent estimators (Chao1, rarefaction, Fisher's alpha) on proportions | Refuse count-dependent estimators; underdetermined variant uses integer percentages |
| D3 | Metadata rows ordered differently from the matrix | Positional join | Join by sample ID; mismatched ID sets fail with the differences listed |
| D4 | Taxon labels differing by case or whitespace | Silent merge or silent split | Follow the dictionary's label rule; without one, report the near-duplicates as unresolved |
| D5 | Zeros under a log transform | Dropping zeros, or unreported `log(x + 1)` | Declared and recorded zero handling |
| D6 | Matrix supplied taxa by samples | Analysing the transpose | Orientation established from labels matched to the dictionary and metadata |
| D7 | Empty samples | NaN distances propagate, or samples vanish | Explicit exclusion with reason, or failure for affected pairs |
| D8 | Unknown values recorded as zero | Absences inflated | Missing kept distinct from zero, per the dictionary |
| D9 | Duplicate sample IDs | Last value wins, or double counting | Rejected |
| D10 | Task requests distances on raw counts | Library default normalisation applied | Requested input used and recorded |

D1 can run against the current RMA operation. The others need the community
methods.

## Held-out set

The held-out set measures transfer beyond the pitfalls we designed for. Every
item discussed on the Board or in this repository counts as development
material.

- A fresh agent instance authors the set. It has no access to the repository,
  the Board or our chats. It receives the item format, the class definitions
  and the method families in scope, but not the development catalogue.
- The author computes each key with an independent implementation inside its
  sandbox, for example R with vegan.
- The authoring run writes directly into an archive encrypted to a public key
  whose private key Barry holds, for example with `age`. Preserve the authoring
  transcript inside the encrypted archive for audit. Remove only ephemeral
  plaintext copies after the capture pipeline is checked. Claude and Codex never
  hold the decryption key, so secrecy relies on the environment, not on an
  instruction.
- Freeze the isolated set and commit its ciphertext hash before pinning the
  revision under test. These community methods were developed before any
  held-out set existed; do not claim otherwise. The authors and implementers
  must remain isolated from each other's material. Key custody, recovery and
  encryption verification are unresolved mechanisms, not completed safeguards.
- Decrypt only after the toolkit revision under test is pinned and the
  confirmatory protocol is committed.
- A rule fixed before decryption governs defective keys. For example, an item
  is dropped when two independent references contradict its key, and every
  drop is reported. Apply the rule before seeing arm results.

## Trials

- Run each trial in a fresh session with no memory, Board, repository checkout
  or prior transcript. The workspace contains only the item materials, plus
  the wheel in the toolkit arm.
- Record the agent family, the model identifier the harness reports, harness
  version, prompt hash, item, arm, replicate, toolkit revision and wheel hash,
  timestamps, token use, full transcript and final workspace.
- Randomise item and arm order. Arms for the same item run in separate
  sessions. Replicates of an item are correlated, so analyse with the item as
  the unit.
- Preserve every trial, including crashes, timeouts and refusals. Rerun only
  infrastructure failures that occur before the agent receives the task, under
  a rule written in advance.
- Execution host and sandbox are still to be chosen. Claude Code needs a host
  where it can authenticate non-interactively, which is untested on `nectar`.

## Scoring

Fix all scoring rules before the first trial. Script them wherever possible.

Each trial receives one **outcome**:

- `correct`: the requested estimand, numbers within the item's tolerances.
- `correct_unresolved`: underdetermined items only. The missing information is
  named, with no answer or an answer under a declared assumption.
- `wrong`: wrong estimand, numbers outside tolerance, or an undeclared guess on
  an underdetermined item.
- `false_refusal`: refusal or an unresolved question when the materials
  suffice.
- `failed`: no result, from a crash, timeout or exhausted budget.

Additional measures:

- **Pitfall handling** on trap items: handled, detected but mishandled, or
  undetected. On clean twins, count spurious warnings.
- **Evidence completeness:** a scripted checklist over the final workspace,
  covering input hashes, resolved settings, exclusions with reasons, numerical
  outputs and environment. It applies equally to both arms; a direct script
  that saves all of these scores fully.
- **Auditability:** a reviewer agent receives the task and the saved evidence,
  without the transcript, and judges whether the result is correct and why.
  The reviewer is scored against the key. Toolkit bundles are recognisable, so
  full blinding is impossible. Treat reviewer scores as secondary to scripted
  numerical scoring.
- **Cost:** tokens, wall time and tool calls.

## Pilot

The pilot tests feasibility. It is not an efficacy test.

- Check that items are understood as intended, scoring scripts work, budgets
  fit, and between-trial variability is large or small enough to size a
  confirmatory run.
- Use development items only. Start with D1 and add community items as their
  methods land.
- Start with a smaller feasibility smoke before the indicative pilot size below.
- Indicative size: six trap and clean pairs, two or three arms, two agent
  families and two replicates, about 96 to 144 trials. Barry agrees the
  Anthropic-token cost before launch.
- Report outcomes descriptively and make no efficacy claim.

## Confirmatory evaluation

- Commit the frozen protocol, analysis script and toolkit revision before
  decrypting the held-out set.
- The primary endpoint is the non-`correct` rate on well-specified trap items:
  `wrong`, `false_refusal` or `failed`, with each component also reported.
  An unresolved tool error counts against the toolkit arm. The guard endpoint
  is the combined `false_refusal` and `failed` rate on clean twins, which must
  not exceed the direct arm's rate by more than a margin fixed in the protocol.
- Compare arms within item and agent family using a paired test fixed in the
  protocol. Report effect sizes with intervals, by agent family and item
  class.
- Justify the number of items and replicates from pilot variability.
- Report every trial, dropped item and protocol amendment.
- Limit claims to the tested models, harness versions, item population and
  toolkit revision.

## Proposals for the community data contract

The catalogue suggests these requirements. They are proposals for the
implementer, not decisions.

1. Declare the value type: count, proportion, presence or measurement.
   Count-dependent methods refuse other declarations. Integer-valued data are
   a diagnostic, not proof of counts.
2. Declare the orientation and check it against sample and taxon IDs.
3. Join matrix and metadata by ID only. ID sets must match exactly, or the run
   fails and lists the differences.
4. Treat taxon labels as exact strings. Labels differing only by case or
   whitespace produce a warning naming them, never an automatic merge.
5. Keep missing values distinct from zero. Unknown values never become
   absences.
6. Require a declared zero policy for transforms undefined at zero.
7. Require a declared empty-sample policy: exclude with a record, or fail.

Clean twins must run under these requirements without warnings that invite
abandoning the analysis.

## Open questions

- Which execution host and sandbox will run trials.
- Whether reviewer agents come from the same family as test agents.
- Whether the checklist arm stays in the confirmatory design.
- Key custody for the held-out archive, which needs Barry's agreement when
  that step arrives.
