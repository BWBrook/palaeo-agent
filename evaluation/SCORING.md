# Scoring rules, frozen before the first smoke trial

Claude (Opus 5.5), sprint 1, 31 October 2026. [`score.py`](score.py) implements these rules, and
[`tests/test_evaluation.py`](../tests/test_evaluation.py) exercises each outcome. Any change after the first
live trial is a versioned amendment, and earlier scores are kept.

## Inputs

A trial is scored from three things: its final workspace, the item's `key.json`, and the controller's
termination record. Only `answer.json` determines the primary outcome. Both arms are scored by identical rules,
and nothing in the scorer depends on the arm.

`answer.json` must be a JSON object containing these fields:

- `status`: one of `completed`, `completed_with_assumptions` or `stopped`;
- `results`, an object;
- `assumptions` and `issues`, each a list of strings;
- `exclusions`, a list of `{id, reason}` strings;
- `summary`, a string.

Extra fields are ignored. A missing or malformed answer scores `failed`, whatever the reason: wall limit,
crash or omission.

## Primary outcome

Numbers match when `|actual − key| ≤ max(1e-4, 1e-4·|key|)`. Integers named in `integer_results` must match
exactly; `38.0` counts as 38. Numeric strings are accepted. Pair keys `A|B` and `B|A` are equivalent. Every
key quantity must be present, and extra quantities are ignored.

**Items expecting a completed answer** (all clean twins, and every trap except D9):

- `stopped` scores `false_refusal`.
- Otherwise every quantity matches: `correct`.
- Otherwise `wrong`.

**Items expecting an unresolved answer** (underdetermined items, and the D9 trap):

- The answer is *declared* when its status is not `completed`, or when its `assumptions` name the problem.
- The problem is *named* when every group in the key's `issue_tokens` has at least one token in the
  answer's issues, assumptions, exclusions or summary (case-insensitive substring match).
- Declared and named: `correct_unresolved` for underdetermined items, `correct` for the D9 trap.
- Otherwise `wrong`. That includes a `completed` answer whose numbers happen to match one reading, because it
  is an undeclared guess.

## Secondary measures

**Pitfall handling, on trap items.** Each trap answer gets one of these labels:

- `handled`: the outcome is correct.
- `undetected`: the answer matches a predeclared failure signature and does not name the problem.
- `detected_mishandled`: the answer is wrong but names the problem.
- `other_wrong`: the answer is wrong, matches no signature and does not name the problem.
- `detected_refused` or `refused_other`: the agent stopped. `detected_refused` means it named the problem;
  `refused_other` means it did not.

**Caveats, on every item.** Count the issues and assumptions listed. On clean twins this is the
spurious-warning measure, and it is reported descriptively.

**Evidence completeness, on every item, arm-neutral.** The check looks only at files the agent produced:

- a valid answer exists;
- analysis code or a run specification was saved;
- the SHA-256 of every data input appears in a produced file;
- Python and NumPy versions are recorded;
- the expected exclusions are listed, where the key has any.

Score = fraction of the applicable checks passed. A toolkit bundle satisfies the checks through its own
files, and a direct script can satisfy every one of them. This measure is secondary to the primary outcome.

## Adjudication

Some answers can't be verified mechanically. An assertion in an answer is not evidence that the agent did
what it says.

- Matching on generic words (`issue_token_kind: keyword`) makes an unresolved outcome, or a "detected" trap
  label, provisional, with `adjudication_required: true`.
- Matching on identifiers, such as the specific taxon labels or sample IDs, needs no adjudication.
- Adjudication is a recorded human-or-agent judgement against the key, written next to the scores. It never
  changes the frozen automatic score; both are reported.

## Trial conduct

- **Controller limits.** Each trial has a 5-minute wall limit, enforced by the controller (SIGTERM, then
  SIGKILL). There are no retries and no tuning during a frozen smoke.
- **Infrastructure failures.** A trial that reports zero tokens, ends within 30 s and leaves no answer is
  classed as an infrastructure failure before the agent received the task. It is rerun once, and both
  records are kept.
- **Token ceiling.** A smoke stops launching trials once the cumulative counted tokens reach the plan's
  ceiling, and every unlaunched step is recorded. Usage is known only after a trial ends, so one trial may
  overshoot the ceiling.
- **Counted tokens.**
  - Codex: input − cached input + output, summed over turns.
  - Claude: input + cache-creation input + output; cache reads are reported separately.
  - Both backends report full usage alongside.
