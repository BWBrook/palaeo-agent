# Reconciliation of sprints 3 and 4

1 November 2026, Claude (Opus 5.5). This closes the sprint 3–4 programme
([plan](sprints-3-4-proposal.md)). Codex (GPT-6 Astra) proposed the plan,
Claude revised it, Codex built sprint 3 and Claude built sprint 4, each
critiquing the other's work, all on Board thread 103. Codex's last review
([sprint-4-calibration-review.md](sprint-4-calibration-review.md), `9d0fe97`)
closed every open implementation and metric-definition finding. This document
records the outcome, the evidence and the decision about what comes next.
CI passed at every commit from `7800ad9` to `9d0fe97`; the full native suite
had 372 passed, none skipped.

## Outcome against the plan's four destinations

| Destination | Status |
| --- | --- |
| 1. Agent-facing transport returning compact, inspectable evidence | **Delivered** (sprint 3). A stdio MCP server over the validated engine, extended in sprint 4 with `study_run`, `study_inspect` and `study_reproduce`. |
| 2. An evaluation system whose worker cannot reach credentials, user state, keys, the network or other trials, with every call recorded | **Delivered for the Claude route.** Claude Code runs MCP-only, with every tool call executed by a per-call `sandbox-exec` worker. Verified by scripted probes, the native suite and 20 live trials (below). The Codex client is not qualified: no pre-dispatch admission route exists. |
| 3. A multi-step study bundle another agent can inspect and rerun without the chat | **Delivered** (sprint 4). The live agents' own study bundles re-verified and reproduced outside their trials: 3 of 3 checked in integration. |
| 4. A bounded paired pilot and reviewer experiment, ending in an explicit decision | **Not run.** Calibration triggered the prespecified family revision before freeze. The decision is below. |

## What the live trials showed

All trials used Claude Sonnet 5.5 through Barry's subscription. The records are
in [run-records](../evaluation/pilot/run-records/README.md), with summaries in
[integration-evidence](../evaluation/pilot/integration-evidence/README.md) and
[calibration-evidence](../evaluation/pilot/calibration-evidence/).

- **The boundary held under a real model.**
  - Every worker call in every complete trial reconciled with the audit on its
    full request and exact returned value.
  - The model's 6 calls to a non-existent bare tool name were refused by the
    client before dispatch.
  - No exported workspace held a link or special file.
- **Correctness hit the ceiling.** Every calibration trap was handled in both
  arms: 8 of 8 each, with P04 accepted by two independent adjudications. The
  direct arm meets the "at least 7 of 8" revision rule. Calibration does not
  observe the pilot's D. It shows that these items cannot discriminate
  correctness for this analyst.
- **Cost.** Median counted tokens were 9,547 (toolkit) and 4,650 (direct): K =
  2.05 on eight development instances. The toolkit arm made 9.5 worker calls
  to the direct arm's 3, and had about 7 times the cache reads.
- **Reproducibility of the packages (new; descriptive).**
  - None of the 8 direct-arm calibration packages contains a script, though
    the prompt asked agents to keep their scripts. Every direct analysis ran
    as inline code, and its only record is the transcript and worker audit.
  - 7 of 8 toolkit packages contain run or study bundles. The exception is
    P04, where the agent missed that the community method reports Shannon
    diversity.
  - This bears on the programme's "easier to reproduce" question. It also
    means the reviewer study as written cannot run: its eligibility rule
    requires re-running a saved script, so every direct package would be
    ineligible and E\* would be 0. Sprint 5 must fix the package contract
    before any reviewer trial.
- **Usability.** Agents missed Shannon in the community method and passed a
  tab-delimited table as PAST input.

## Deviations, recorded

- **Limits configured above the agreed values.** Integration plans set 600 s
  and 400,000 counted tokens, against the agreed 300 s and 200,000.
  Calibration set 1,000,000 against 600,000. Observed use stayed below every
  agreed limit: 48,884 and 124,840 counted tokens, and every integration
  trial finished in under 63 s including preflight (maximum 62.48 s).
- **Launches before Codex's closure review** of `b69fd10`.
- **Fixes between runs.** The organisation-managed file gate and the exact
  tool names in the prompts both changed between runs, and both are recorded.
- **Records.** Full details are in the run-records README. Historical results
  are unchanged.

## Decision

The trap families are revised before any pilot freeze, as the rule requires.
This work moves to the next programme rather than extending this one, for
three reasons:

- it is a new bank design, not a repair;
- Codex asked for a concrete, reviewed revised bank before any further live
  allocation;
- the package-contract defect above has to be solved in the same redesign.

The infrastructure, protocol and launcher carry forward unchanged except
where the next plan says otherwise. The supervisor qualification was rerun on
the current tree at close-out; it is rerun again at freeze.

## Standing agreements carried forward

- Subscription-only authentication; no API accounts (Barry, 1 November 2026).
- Same-family Sonnet pilot, with cross-family review deferred.
- 96 analyst trials in 2 sessions. Claude accepts Codex's point that more
  sessions do not generally halve item-clustered variance.
- No extra live allocation by inference: an additional calibration round
  needs Barry's explicit approval.
- No public release; historical records stay intact.

## AI roles

| System | Role |
| --- | --- |
| Codex (GPT-6 Astra) | Sprint 3 build: confined worker, MCP transport, probes. Pre-freeze, closure and calibration reviews, including the independent P04 adjudication through a fresh-context packet reviewer. |
| Claude (Opus 5.5, Claude Code desktop) | Plan revision, sprint 3 critique and the sprint 4 build: study layer, pilot bank, scorer, flaws, protocol, launcher, subscription supervisor and its qualification. Ran the live trials, did the first P04 adjudication and wrote this reconciliation. |
| Claude Sonnet 5.5 | The analyst in all 20 live trials. |

Barry set direction and authorisations in chat; the agents coordinated on the
Board.
