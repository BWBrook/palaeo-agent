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
  `claude auth status` reporting a subscription login *in the launch
  environment itself*. The client runs in normal mode, with no `--bare`, from a
  fresh `HOME` whose only content is a link to the login keychain (macOS finds
  the stored login through `HOME`), and from a working directory with no
  instruction files above it. CLAUDE.md loading is off (empty
  `--setting-sources`) and so is auto-memory.
- **Supervisor qualification.** `qualify_supervisor.py` runs the exact command
  and environment against a fake endpoint that records request bodies.
  [`supervisor-qualification.json`](launch-evidence/supervisor-qualification.json)
  shows:
  - the capture and supervisor environments carry none of 98 distinctive
    lines from Barry's global instructions, policy and memory, no instruction
    preamble and no memory section;
  - a planted CLAUDE.md is detected when the user setting source is switched
    on, so the scan works;
  - the supervisor environment is logged in with a subscription;
  - no credential header reached the fake endpoint.
- **Fingerprints, inventory and admission.** Frozen fingerprints are enforced,
  including every byte of both runtimes and their base interpreter. The item
  directory must equal its manifest exactly, and only listed materials are
  staged.
  A dummy-key fake-endpoint inventory capture, made with a separate
  configuration directory that is not logged in, is saved with each trial. The
  client's init record is checked.
- **Reconciliation** pairs one use, one result and one audit record. They must
  match on the full request and on the exact value the adapter returned; client
  refusals are a separate category.
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

## Status

1. Barry logged in the dedicated configuration directory with his
   subscription (1 November 2026).
2. Codex verified the L1–L8 repairs (7800ad9). The remaining items it raised
   (dependency bytes, exact material set, full-value reconciliation, the
   launch-environment login) are fixed with tests, and the qualification above
   is complete.
3. **Host.** The MacBook, kept awake, for integration (≤ 8) and calibration
   (≤ 16). The client's working directories live under
   `/Users/Shared/palaeo-pilot-work`, because `~/.claude` would sit above any
   directory under the home folder.
4. **Reviewer launcher.** Built after the analyst run, using the same gates.
