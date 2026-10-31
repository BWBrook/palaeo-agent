# Sprint 3 review — Claude, 31 October 2026

Claude (Opus 5.5) reviewed Codex's sprint 3 at `29fb800`, as the
[revised plan](sprints-3-4-proposal.md) required.

**Verdict: accepted.**

- **MCP transport and offline worker.** I found no defects in either, and
  their evidence reproduces.
- **Codex client hold.** I agree that the Codex client cannot yet be qualified.
- **New finding:** the installed Claude Code client *can* run as an MCP-only
  supervisor. A credential-free check shows that every request it builds
  offers only the confined worker's tools. When a scripted endpoint asked it
  to run hidden built-in tools, it refused all of them. This gives the pilot
  one qualified client route, subject to the launch conditions below.

## What I checked myself

- **Test suite.** `uv run --extra mcp pytest -q`: 313 passed, 1 skipped (the
  native test). The native worker suite passes 8 of 8 outside the enclosing
  sandbox.
- **Probes.** I reran Codex's adversarial probes into new directories:
  - 29 of 29 checks pass in each arm, through real MCP connections;
  - `--demo` runs RMA, community analysis and PERMANOVA in confinement,
    refuses a repeated design, and reproduces all three bundles in a fresh
    supervisor.
- **Code review** of `evaluation/execution/worker.py`, `server.py` and
  `src/palaeo_agent/mcp_server.py`.
  - The profile denies by default.
  - Each arm reads only its own runtime: the direct arm cannot see the toolkit
    wheel.
  - Model-controlled paths are resolved only inside the sandboxed interpreter.
  - Hardlink and symlink escapes are probed and denied.
  - `python -I` stops a planted module in the trial from shadowing the
    toolkit.
  - The product transport rejects paths that resolve outside its root,
    including through symlinks.

## The Claude Code client boundary

[`evaluation/sprint3/claude-client-boundary/probe.py`](../evaluation/sprint3/claude-client-boundary/probe.py)
runs Claude Code 2.1.308 against a localhost fake Anthropic endpoint, with a
dummy API key, a fresh configuration directory and the sprint-3 worker as its
only MCP server. Nothing is forwarded, and no model is called. It tests both
arms in two client modes:

- `--bare`, which never reads OAuth or the keychain;
- the normal mode.

Both modes use `--tools=`, `--strict-mcp-config`, `--setting-sources=` and
`--allowedTools mcp__worker__*`.

The endpoint records every request and answers with scripted tool calls:

- nine built-ins that must be unavailable: Bash, Read, Write, Edit, WebFetch,
  Agent, Task, ToolSearch and the placeholder;
- a worker read of an outside synthetic secret;
- a positive control.

**Result: all four cases pass**
([receipt](../evaluation/sprint3/claude-client-boundary/receipt.json)).

| Check | bare | normal |
| --- | --- | --- |
| Tools in every actual request | exactly the worker's tools (3 direct, 11 toolkit) | the same, plus an inert `DeferredToolPlaceholder` (`defer_loading`, empty schema, "never call this tool") |
| Client's init record equals the request inventory | yes | yes |
| Only the dummy key sent; no Authorization header | yes | yes |
| Each of the 9 scripted built-in calls | refused: "No such tool available… disabled for this session, in subagents as well as here" | refused, including the placeholder |
| Worker read of the outside secret | denied by Seatbelt | denied |
| Canary files unchanged; secret never returned | yes | yes |
| Positive control (`print(6*7)`) | 42 | 42 |

This is the evidence Codex's investigation could not get for Codex. A model
that names a tool the client did not advertise gets a refusal, not an
execution. The normal mode's extra system text (about 6 kB of Claude Code
environment notes) is context, not capability.

**Conditions before a live Claude launch:**

1. **Inventory gate at every launch.**
   - Immediately before each trial, run the fake-endpoint capture with the
     identical client binary (SHA-256 pinned), flags and MCP configuration.
   - Refuse the launch unless the captured inventory equals the frozen one.
   - At launch, compare the client's own init record with the frozen
     inventory, and invalidate the trial on any mismatch.
   - A small local proxy that checks each real request before forwarding it
     would be stronger. It is trusted infrastructure and needs its own review,
     so it is not required.
2. **Authentication.**
   - `--bare` authenticates only with `ANTHROPIC_API_KEY`, held in the
     supervisor's environment; the worker's environment is an allowlist that
     excludes it.
   - The normal mode can use the existing subscription login, read by the
     supervisor only.
   - The Sonnet reviewer replicate can use either. The choice is made at
     freeze.
3. **A turn cap and a wall limit inside each trial.** My first version of the
   scripted endpoint had a bug that made the client loop: it sent 5,605
   requests in 4 minutes. The aggregate token ceiling stops *new* trials, but
   it cannot stop a runaway inside one. Every launch needs `--max-turns` and a
   wall-clock kill, as the probe now uses.

## Codex client: hold stands, with a suggested route

Codex 0.166.0 still advertises:

- `apply_patch`, nested in code-mode `exec`;
- MCP resource readers and a clock;
- six collaboration tools, including `spawn_agent`.

Disabling the code-mode host makes the client unusable. I agree that
flags alone cannot qualify it. Two points for Codex's next attempt:

1. **Reach, not just advertisement.** The scripted-endpoint method above works
   for the Responses wire format too. It can test, through the actual client:
   - whether `apply_patch` under `-s read-only` can write, or reveal anything
     about, a file outside the trial;
   - whether the resource readers can reach anything besides the configured
     worker;
   - whether unadvertised tool names are refused.

   A tool the model can see but which provably cannot reach outside the
   boundary is a weaker condition than absence, but a defensible one.
   Collaboration tools are different: they start further agents. They must be
   absent or provably inoperative, not merely confined.
2. **`model_catalog_json`.** I disagree that overriding the model's
   `apply_patch_tool_type` is categorically unacceptable. It is client-side
   metadata that decides which tools are advertised, and it would be identical
   in both arms. The bundled instructions may still mention `apply_patch`,
   which costs both arms equally. I would accept it if the overridden catalogue
   is hash-pinned and the resulting request inventory passes the same capture
   and scripted-refusal checks at every launch.

## Residual limits (not defects)

- **No per-call disk or memory quota.** A worker can fill the trial's volume
  or exhaust host memory. That harms the host, not the boundary. A launcher
  should run trials on a bounded volume, or check trial size after each call.
- **Supervisor crash cleanup** is unimplemented, as Codex recorded.
- **Linux confinement** is not implemented. `mini` (macOS, 24 GiB) remains the
  natural host for the long runs, but it is not yet qualified.

## Consequence for sprint 4

- The offline study and bank work proceeds now.
- The analyst pilot was planned on Codex. If Codex's route fails, the qualified
  alternative is Claude analysts. That would need a new authorisation from
  Barry for Anthropic spending well beyond the reviewer replicate. Nothing
  launches until one route passes the conditions above and the pre-freeze
  gate.

## Changes made

- Added [`evaluation/sprint3/claude-client-boundary/`](../evaluation/sprint3/claude-client-boundary/):
  the probe and its receipt.

I made no change to Codex's source.
