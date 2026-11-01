# Pilot launcher (Claude route): status and evidence

[`launch.py`](launch.py) implements the launch conditions in
[the pilot protocol](../../docs/pilot-protocol.md). No live trial has run.
Codex reviews this before the integration and calibration trials.

## Per-trial conditions

- **Pinned client.** Claude Code 2.1.308. The plan records its SHA-256, and
  each launch rechecks it.
- **Mode.** `--bare`: no CLAUDE.md, memory, hooks, plugins or keychain. The
  model's tools are only those of the confined worker MCP server
  (`--tools= --strict-mcp-config --allowedTools mcp__worker__*`). The
  supervisor runs with a fresh `HOME`.
- **Inventory gate.** Immediately before each trial, the identical command runs
  against a fake endpoint. If the captured tool list differs from the frozen
  one, launches halt.
- **Init check.** If the client's own init record differs from the inventory,
  the trial is killed and launches halt.
- **Reconciliation.** Every tool event must be either a worker call matching
  the worker audit log, or a client refusal ("No such tool available") of an
  unadvertised name. Anything else halts launches.
- **Limits.** `--max-turns` (default 60), a wall-clock kill (600 s for
  analysts), and process-group termination.
- **Cleanup.** The launcher kills any surviving process whose arguments name
  the trial, and verifies that none remain. If one does, launches halt.
- **Usage.** Counted tokens are input + cache-creation + output; cache reads
  are recorded separately. Unavailable usage halts launches, and the ceiling
  stops new trials.
- **No retries.** A trial directory, once created, is never rerun.
- **Plans** are written with exclusive creation. The order uses balanced
  family blocks with a fixed seed.

## Evidence at this commit

- **Rebuilt runtime.** `~/palaeo-eval/pilot-runtime-20261101` contains the
  current wheel with the study tools ([manifest](launch-evidence/runtime.json)).
- **Worker probes.** On that runtime, 29 of 29 per arm pass
  ([receipt](launch-evidence/worker-probes-receipt.json)).
- **Client probes.** Bare and normal mode, both arms, all pass
  ([receipt](launch-evidence/claude-client-receipt.json)). The inventories are:
  - 3 worker tools in the direct arm;
  - 14 in the toolkit arm (the 11 product tools plus the 3 study tools).
- **Offline end-to-end test.** `tests/test_pilot_launch.py`, native only, runs
  4 trials through the real client and a scripted fake endpoint. Every gate,
  init check, reconciliation (2 worker calls and 1 refused hidden Bash call
  per trial), cleanup, usage and scoring step runs.

## Before live use

- **An Anthropic API key.** `--bare` authenticates only with
  `ANTHROPIC_API_KEY`. The launcher reads it from a file given by
  `--key-file`, places it only in the supervisor's environment (the worker's
  environment is an allowlist), and never records it. Barry must supply that
  file; the agents cannot create keys.
- **Host.** The MacBook sleeps. `mini` needs the same runtime build and a
  rerun of the probes before it hosts the 96-trial run.
- **Reviewer launcher.** The same gates apply. Reviewer trials stage
  `package/` from frozen analyst records and use `prompts/reviewer.md`. This
  is built after the analyst run, because it depends on the packages.
