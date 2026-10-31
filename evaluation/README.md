# Evaluation instrument

**Post-smoke counter-review, 31 October 2026:** the account below documents the
historical v1 instrument. Its named checkout/key denials worked, but credential
and shared-state isolation was incomplete. The live launcher is now disabled,
without an override. [Counter-review and evidence](../docs/sprint-1-review.md)
explain the boundary and preserved results; [prospective scoring/item repairs](revised/README.md)
are available for offline checks. The original instrument is preserved at
freeze commit `5af0041`. Do not read the historical reproduction commands below
as an operational live-evaluation recommendation.

Sprint 1 of [the two-sprint plan](../docs/sprints-1-2.md). This directory holds the development item bank, the
isolated trial runner, the frozen scorer and the feasibility-smoke records described in
[evaluation.md](../docs/evaluation.md). Claude (Opus 5.5) built it on 31 October 2026. Everything here is
development material; no held-out item exists.

| Path | Contents |
| --- | --- |
| [`build_items.py`](build_items.py) | Generates `items/` deterministically, without importing palaeo_agent |
| `items/<ID>/` | `materials/` (copied into a trial), `key.json`, `provenance.json`; `items/MANIFEST.json` |
| [`check_solvable.py`](check_solvable.py) | Solves every completable item through the current toolkit API, cross-checking the keys |
| [`answer.schema.json`](answer.schema.json) | The answer contract, identical in both arms |
| [`score.py`](score.py), [`SCORING.md`](SCORING.md) | Frozen scorer and its rules |
| `harness/` | Runtime builder, sandbox profile, trial runner, smoke driver, prompts |
| `preflight/` | Isolation preflight materials and records |
| `runtime/requirements.txt` | Hash-locked dependencies shared by both arms |
| `smoke/<version>/` | Frozen plan, per-trial records, run log, scores |

## Item bank

The bank has 23 items: trap and clean-twin pairs for catalogue items D1–D10, plus underdetermined variants of
D2, D4 and D6. All data are synthetic and seeded. Keys come from the definitions:

- **Exact rationals** for Bray–Curtis, means, variances and covariances.
- **Float64, once, from exact inputs**, for logarithms (Shannon, log10) and square roots.

Every completable item was also solved through the toolkit API with legitimate preprocessing, and all 19 agree
with their keys to within 1e-7. Each trap's failure signature differs from its key by at least ten tolerances,
as the generator asserts.

| Catalogue | Trap | Twin | Underdetermined |
| --- | --- | --- | --- |
| D1 padded locality columns (RMA) | D1-trap | D1-twin | |
| D2 percentages presented for a raw-count analysis | D2-trap (totals given) | D2-twin | D2-under (no totals) |
| D3 metadata order differs from matrix | D3-trap | D3-twin | |
| D4 taxon labels differing by case/space | D4-trap (merge rule given) | D4-twin | D4-under (no rule) |
| D5 zeros meaning "not measurable" under log10 (RMA) | D5-trap | D5-twin | |
| D6 taxa-by-samples orientation | D6-trap | D6-twin | D6-under (opaque labels) |
| D7 empty sample | D7-trap | D7-twin | |
| D8 not-assessed cells | D8-trap | D8-twin | |
| D9 duplicate sample ID (unresolvable) | D9-trap | D9-twin | |
| D10 very unequal totals, raw counts requested | D10-trap | D10-twin | |

The D9 trap expects an unresolved answer: the materials cannot say which of two T4 rows is right.

## Arms and runtime

Both arms get identical materials, prompt, Python 3.12.13 environment (numpy, scipy, pandas, matplotlib and
pydantic from one hash-locked file), permissions and limits. The toolkit arm adds three things:

- the palaeo_agent wheel, built from the commit under test and installed without dependencies;
- `palaeo_agent_discover.json`;
- one prompt paragraph ([`prompt-toolkit.md`](harness/prompt-toolkit.md)), which tells the agent to use the
  toolkit for the parts of the analysis it supports.

The runtimes live outside any checkout, at `~/palaeo-eval/runtime`. The direct runtime cannot import the
toolkit (the builder asserts this, and preflight confirmed it). The toolkit runtime imports it from its own
`site-packages`.

## Isolation

The controller confines each worker from outside its agent CLI using macOS `sandbox-exec`
([`harness/sandbox.py`](harness/sandbox.py)). The profile:

- denies reads under the home directory except the trial's own directory, its arm runtime and the uv Python;
- denies reads of `/Volumes`, `/private/tmp`, `/private/var/folders`, Homebrew Python and R;
- denies writes everywhere except the trial directory.

The worker runs in a fresh randomly named directory, with an explicit environment. Its prompt names neither the
item nor the arm.

**Codex backend** (`codex exec`, codex-cli 0.166.0): `--ephemeral --ignore-user-config --ignore-rules`, a fresh
`CODEX_HOME` holding only a temporary copy of the auth file (deleted with the trial and never recorded), web
search disabled, and Codex's own sandbox bypassed in favour of the outer profile.

**Claude backend** (`claude -p`, Claude Code 2.1.308). Claude Code authenticates only through its default
configuration, so the profile instead denies the instruction, memory, transcript, skill, plugin and settings
paths under `~/.claude`. It runs with `--setting-sources "" --strict-mcp-config --no-session-persistence
--exclude-dynamic-system-prompt-sections` and only the Bash, Read, Edit and Write tools.

**Preflight results**, recorded in `preflight/runs/`. A worker was asked to read or run each of these targets:

- a canary outside its trial;
- a canary beside the keys in the checkout;
- the checkout README;
- global `CLAUDE.md`, `~/.claude/projects` and `~/.codex/AGENTS.md`;
- `~/Documents` and `/private/tmp/claude-501`;
- Homebrew Python and Rscript;
- writes outside the trial;
- a toolkit import, a dependency import and a network fetch.

In both backends, every canary, instruction and memory read was blocked, and so was every write outside the
trial. The toolkit imported only in the toolkit arm, and only from the wheel.

Residual exposures, recorded rather than assumed away:

1. **Network.** Shell commands have network access, because the outer profile cannot separate the CLI's own
   model traffic from its tools. The prompt forbids installs and network use, and the leak scan flags install
   and fetch commands.
2. **Claude temp listing.** A Claude worker can list the names (not the contents) of entries in
   `/private/tmp/claude-501`, because Claude Code needs that directory.
3. **Claude account email.** Claude Code injects the account email into its system prompt; Codex receives no
   such context. Records redact the email.
4. **Leak scan limits.** The scan detects some leaks and cannot establish their absence. Its patterns are
   checkout paths, agent configuration paths, other trials, package installs, network fetches and blocked-access
   errors.

## Smoke

The smoke uses 7 items: D1-trap, D1-twin, D3-trap, D3-twin, D6-trap, D6-twin and D2-under. Each runs in both
arms, once, in an order shuffled with a fixed seed: 14 trials per backend. Each plan file under `smoke/` fixes
the backend, model, effort, wall limit, token ceiling and order before the first trial.

| Backend | Model, effort | Token ceiling (counted) | Authority |
| --- | --- | --- | --- |
| Codex | gpt-6.1-sol, medium | 300,000 | Plan agreed with Codex, 03c5097 |
| Claude | claude-sonnet-5-5, CLI default | 1,500,000 | Barry, 31 October 2026, chat: "Yes, you may run Sonnet 5.5 i that way." |

**Amendment to the counted-token definition, made before any live trial.** The plan specified "an aggregate
reported-token stop ceiling of 300,000". A trivial Codex preflight reported 61,937 input tokens, of which 57,984
were cached, so a ceiling on all reported tokens could not cover even a few trials. The ceiling therefore
applies to uncached input plus output. The preflight counted 5,380 tokens on that measure. Full usage is
reported for every trial. The Claude ceiling uses the same principle: input, cache-creation input and output,
with cache reads reported separately. Codex reviews this amendment in its sprint-1 critique.

Reproduce:

```sh
uv run --no-project python evaluation/harness/runtime.py ~/palaeo-eval/runtime   # both arm runtimes and the wheel
uv run python evaluation/build_items.py                                          # bank; must reproduce MANIFEST.json
uv run python evaluation/check_solvable.py                                       # keys vs toolkit API
uv run pytest -q tests/test_evaluation.py                                        # scorer rules
~/palaeo-eval/runtime/direct/bin/python evaluation/harness/smoke.py run evaluation/smoke/<version>/plan.json
uv run python evaluation/score.py evaluation/smoke/<version>
```
