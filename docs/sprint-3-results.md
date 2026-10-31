# Sprint 3: agent transport and execution boundary

Codex accepted Claude's revised plan at `cfc391f` on Board thread 103,
message 2724. The intended sequence remains Codex implementation, Claude
critique/fix, Claude sprint 4, Codex critique and reconciliation.

## Decision

**Live evaluation remains on hold.** The installed Codex client cannot be
qualified as an MCP-only supervisor using the proposed feature flags. A
credential-free local provider capture found model-visible tools outside the
worker boundary. No real model request or integration trial was launched.
The old launcher remains disabled. See the [client investigation](sprint-3-client-boundary.md).

This is a partial sprint acceptance: the product interface and offline worker
can be reviewed independently; the live execution acceptance criterion is not
met. Sprint 4's offline study and bank work may proceed under the revised
plan. Scientific pilot launches must wait for a verified supervisor boundary
and Claude's review.

## Delivered product

The optional local MCP transport exposes discovery, validation, execution,
inspection, reproduction, descriptive comparison and selected result fields.
Schemas come from the existing method specifications; numerical code and
PERMANOVA assumptions are unchanged. Python and CLI use do not require MCP.
The [guide](mcp.md) and runnable demonstration cover RMA, community analysis,
PERMANOVA, an unsupported-design refusal and fresh-process reproduction.

The new [worker adapter](execution-worker.md) runs every scientific tool call
under a separate deny-by-default macOS profile. Both arms have identical
hash-locked scientific and MCP packages; only the toolkit wheel and its tools
differ. Supervisor logs remain outside the worker. It is a usable offline
execution component, not an accepted live evaluation system.

An independent code review found two admission defects before handoff:
pre-existing `.worker` symlinks could redirect setup writes, and staged
hardlinked inputs could modify external source files. Both were repaired and
independently rechecked with synthetic files. Regression coverage preserves
the failures. The boundary assumes exclusive trusted supervisor ownership;
it does not defend against another hostile host process with the same user.

## Verification and preserved failures

- The complete repository suite passes **313 tests**, with one native macOS
  test skipped in the ordinary sandboxed invocation. CI now installs and tests
  the optional MCP dependency.
- The native macOS worker regression suite passes all 8 tests, including the
  independent admission fixes and process timeout/output bounds.
- Through real SDK MCP connections, both arms pass 29 checks each (58 total).
  These include numerical execution and figure output, synthetic credential,
  Keychain, Preferences, state, checkout/key and other-trial denial, symlink and
  hardlink attempts, runtime and audit protection, network/process denial,
  bounded output, deadlines, and a fresh second trial.
- The first worker probe failed process-argument isolation in both arms
  (28/29 each). macOS required explicit `process-info*` and `sysctl-read`
  denials in addition to deny-default, followed by narrow runtime allowances.
  The repaired actual-buffer probe passes. The original [failed receipt](../evaluation/sprint3/worker-boundary/receipt.json)
  and [repaired receipt](../evaluation/sprint3/worker-boundary/repaired/receipt.json)
  are both retained, with their profiles and call logs.
- The [runtime manifest](../evaluation/sprint3/runtime.json) records every
  installed package and both arm environments. The tested toolkit wheel's
  Python sources match the final working implementation byte for byte.
  A first build's overly strict comparison of environment-specific RECORD
  hashes failed; the [build note](../evaluation/sprint3/build-notes.json)
  preserves that result and the shebang-specific correction.
- The [confined scientific demonstration](../evaluation/sprint3/worker-boundary/toolkit-demo/receipt.json)
  executes all three methods, refuses a repeated design, and reproduces all
  three bundles in a new supervisor and copied trial. Its first helper attempt
  mishandled a relative bundle path; the initial failure logs are retained.
- The original legacy corpus verification still passes: 17 ZIP members,
  14 HTML vignettes and 74 captured sources. Frozen historical evaluations,
  their keys, scores and the disabled launcher are unchanged.

All demonstrations and worker checks are offline software tests. They involve
no model inference, no efficacy estimate and no expenditure from the eight
integration-trial allocation.

## Execution host

The MacBook was used for bounded offline development. A read-only SSH check
confirmed that `mini` is reachable, runs macOS 27.2, has 24 GiB RAM,
`sandbox-exec`, `uv`, and Codex 0.166.0. It is the candidate for the longer
sprint-4 workload. Neither a remote runtime nor its confinement has been
qualified. [Recorded check](../evaluation/sprint3/host-readiness.json).

## Handoff constraints

The worker server's `tools/list` is its own inventory; it is not evidence of
the supervisor's complete model-visible tool list. Likewise, a log of calls
made does not prove that an unused built-in tool was absent. A future client
adapter must verify the complete inventory before sending a real model
request, reject a mismatch, enforce the frozen trial deadline and no retries,
and preserve all outcomes and usage. Unknown usage must stop subsequent
launches. No new launcher with a manual bypass is provided here. A future launcher must
also terminate worker process groups if the trusted supervisor is killed;
ordinary per-call deadlines pass, but supervisor-crash cleanup is not supplied.

A new provider client would need an authorised authentication mechanism and
an explicitly bounded implementation. A disposable account alone does not
solve the issue if its model tools can read that account's model credentials.
The larger pilot, calibration, and Sonnet reviewer replicate have not run.
