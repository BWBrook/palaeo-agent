# Pilot launcher (Claude route): status and evidence

[`launch.py`](launch.py) implements the launch conditions in
[the pilot protocol](../../docs/pilot-protocol.md). No live trial has run.
Codex reviews this before the integration and calibration trials.

## Per-trial conditions

The full list is under "Launch conditions" in
[the pilot protocol](../../docs/pilot-protocol.md). In summary, before any
live trial:

- **Authentication.** Barry's subscription only, through a dedicated
  configuration directory that holds no instructions or memory. It is checked
  before every trial: allowed entries only, no memory content, and
  `claude auth status` reporting a subscription login. The client runs in
  normal mode, with no `--bare`, from a fresh `HOME` and a working directory
  with no instruction files above it.
- **Fingerprints, inventory and admission.** Frozen fingerprints are enforced.
  A dummy-key fake-endpoint inventory capture, made with a separate
  configuration directory that is not logged in, is saved with each trial. The
  client's init record is checked.
- **Reconciliation** by identity, with explicit refusal categories.
- **Cleanup.** The client group, the worker server and every recorded worker
  group are killed, then verified gone from a full process listing.
- **Export** copies regular files only, never following links.
- **Usage and ledger.** Usage must be complete. The halt ledger is durable
  (`HALTED.json`), the output directory is bound to its plan, and no trial is
  rerun.

## Failure-path evidence

`tests/test_pilot_launch.py` covers the paths Codex's pre-freeze review
(L1–L8) found unprotected:

- a worker-created link and a FIFO refused at export;
- the ledger refusing started-only, incomplete or unknown-usage trials;
- a durable halt and a plan-bound output directory;
- reconciliation rejecting a mismatched audit record, a missing result and an
  unrefused hidden tool;
- termination killing a separate-session worker;
- incomplete usage refused;
- configuration memory or CLAUDE.md halting.

The native end-to-end run sends 4 trials through the real client and a
scripted fake endpoint. It includes a hidden Bash call (refused and
reconciled) and a worker-created symlink (refused at export), and checks that
a rerun launches nothing.

## Before live use

1. **Barry logs in a dedicated configuration directory once, with his
   subscription:**
   `CLAUDE_CONFIG_DIR=~/palaeo-eval/claude-pilot-config claude auth login --claudeai`.
   The agents cannot do this for him.
2. **Codex verifies** the changed paths and the native abort and export
   behaviour.
3. **Host.** On the MacBook, the machine must stay awake during runs; `mini`
   would need the same runtime build and probe rerun. Integration (≤ 8) and
   calibration (≤ 16) trials are short enough for the MacBook.
4. **Reviewer launcher.** Built after the analyst run, using the same gates.
