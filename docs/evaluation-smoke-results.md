# Evaluation feasibility smoke — 31 October 2026

Sprint 1 of [the two-sprint plan](sprints-1-2.md). Claude (Opus 5.5) built the instrument and ran the smoke;
the [instrument README](../evaluation/README.md) describes the method. **This is a feasibility check, not an
efficacy test:** 7 development items, 2 arms, 1 replicate and 2 agent families, 28 trials in all.

## Result

Every one of the 28 trials reached the correct outcome under the frozen scorer:

- all 24 trials on completable items matched the key;
- all 4 underdetermined trials declared the problem;
- there were no false refusals, failures or wall-limit terminations.

The smoke therefore cannot separate the arms on correctness. That is the main finding, and it is about the
items, not the toolkit. Frontier agents handle these traps when the dictionary states the relevant fact plainly.

| Backend, arm | Correct | Counted tokens | Median time | Evidence score | Toolkit actually used |
| --- | ---: | ---: | ---: | ---: | ---: |
| Codex gpt-6.1-sol (medium), direct | 7/7 | 63,299 | 28 s | 0.43 | — |
| Codex gpt-6.1-sol (medium), toolkit | 7/7 | 140,990 | 48 s | 0.93 | 6/7 runs, plus 1 reasoned refusal |
| Claude Sonnet 5.5, direct | 7/7 | 38,163 | 14 s | 0.39 | — |
| Claude Sonnet 5.5, toolkit | 7/7 | 56,352 | 19 s | 0.61 | 2/7 |

**Counted tokens.** Codex counts uncached input plus output. Claude counts input, cache-creation input and
output; Claude cache reads came to a further 591,261 tokens, and the API-equivalent cost was $0.55 for all 14
Sonnet trials. Both backends stayed within their ceilings: Codex at 204,289 of 300,000, Claude at 94,515 of
1,500,000, or 686k if cache reads are included.

**Evidence score.** This is the arm-neutral completeness checklist in [SCORING.md](../evaluation/SCORING.md).
Toolkit bundles record input hashes and the environment automatically. No direct-arm trial recorded either,
although the checklist would have credited them.

## Feasibility findings

1. **The items are too easy for the confirmatory question.** All 6 traps in the smoke (D1, D3, D6, two arms
   each, two backends) were handled in both arms. A pilot that can measure an effect needs harder items:
   - dictionary facts whose consequence the agent must infer, not consequences stated outright;
   - realistic file sizes and noise;
   - multi-step analyses in which an early data-meaning slip propagates;
   - traps the toolkit's declarations bear on directly, such as D4, D7, D8 and D10, which were not in this
     smoke.
2. **The toolkit arm needs a fidelity measure.** The prompt says to use the toolkit "for the parts of the
   analysis it supports". Sonnet nevertheless computed Bray–Curtis and Shannon by hand in 5 of 7 toolkit trials,
   and Codex used the toolkit in 6 of 7. An efficacy comparison must report whether the toolkit was actually
   invoked, from bundles and executed commands, and must decide in advance whether the arm means "toolkit
   available" or "toolkit required".
3. **Discovery is easy to misread.**
   - One Sonnet agent concluded that "the palaeo_agent package only supports RMA" after reading the first
     1,500 bytes of the 11.8 KB single-line discovery JSON. The RMA input schema fills that span, and
     `community` appears only later.
   - `python -m palaeo_agent --help` lists commands but not methods.
   - **Proposal for Codex:** put a short method index at the top of the discovery output, and list the methods
     in `--help`.
4. **D2-under is defective (my item error).** Two-decimal percentages with totals below 10,000 identify each
   total as the smallest consistent N. Both Sonnet agents recovered the true totals exactly and declared the
   reconstruction as an assumption, so they still scored `correct_unresolved`. Both Codex agents stopped
   instead; the Codex toolkit agent cited the toolkit's refusal of the percentages. The catalogue specified
   integer percentages for this variant. The frozen scores stand, and bank v2 must use integer percentages.
5. **Cost.** The toolkit arm cost more:
   - Codex: 2.2× the counted tokens and 1.7× the median time;
   - Sonnet: 1.5× and 1.4×.

   For Codex, most of the cost is reading the discovery output and writing specifications. Wrapper overhead is
   not success under the vision, so the pilot must weigh this cost against any error reduction.
6. **The instrument worked end to end.**
   - Both isolation preflights passed.
   - Every trial wrote a schema-valid answer.
   - The scorer needed no amendment, and 4 adjudications confirmed its provisional keyword matches.
   - The leak scan found no checkout, configuration, other-trial, install or fetch access.

   Its flags were all benign:
   - reference URLs echoed from the discovery output;
   - Claude's own memory-path string, whose reads the sandbox denies;
   - two blocked matplotlib cache writes.

   The scan patterns need tightening so that real leaks stand out.
7. **Harness fixes for v2.**
   - Set `MPLCONFIGDIR` inside the trial for the Claude backend, which keeps the real `HOME`; two Sonnet trials
     lost time to a blocked `~/.matplotlib`.
   - Exclude the discovery output's reference URLs from the network pattern.

## What the smoke cannot show

It cannot show that the toolkit reduces errors, or that it does not. It does not show that the confirmatory
design is adequately powered. It does not measure reviewer auditability, or performance on items the
developers have not seen. Every item is development material.

## Records

- Frozen instrument: commit 5af0041, made before the first trial.
- Plans, per-trial records, run logs, scores and adjudications: `evaluation/smoke/codex-v1/` and
  `evaluation/smoke/claude-v1/`. Each trial record holds the transcript, final workspace, sandbox profile,
  usage and leak scan.
- The wheel, discovery output and requirements hashes are in each `trial.json`.
- Adjudication of the Sonnet trials was done by Claude, an agent of the same family as the trial agent. Codex
  re-adjudicates in its sprint-1 review.
