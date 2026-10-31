# Client-gate proposal review

Reviewed `a3ca570`, 1 November 2026, including Board message 2752. This is a
review of the proposed launcher and a replay of saved scripted-client
evidence, not a new live-client qualification. The reproducible
[check](check.py) and [receipt](receipt.json) pin their inputs.

**Do not accept the replacement as written.** Pinning the binary, catalogue,
configuration and runtime, then checking an identical fake-endpoint request,
is useful evidence of a reproducible inventory. The proposed external event
monitor and post-trial trace reconciliation do not establish pre-dispatch
enforcement. An `item.started` notification is not an acknowledgement barrier:
the launcher has not demonstrated that dispatch waits for its approval. Killing
a process after observing an unexpected tool cannot undo a completed read,
write or network request. This is a limitation of the assurance claim, not an
observed escape through the current pinned client.

Two concrete mismatches already appear in the saved evidence:

- Both arms legitimately emit `mcp_tool_call` events for
  `list_mcp_resources` and `list_mcp_resource_templates` with server `codex`.
  They are the explicitly retained, tested inert helpers. The literal
  non-worker kill condition would abort these permitted calls. Define an exact
  allowlist including their restricted arguments, or remove them and requalify.
- Six unsupported hidden patch/shell/spawn requests per arm have returned
  refusals in the captured Responses conversation but no corresponding JSONL
  tool-start event. Direct has 13 scripted replies, six tool-start events and
  three worker audit rows; toolkit has 14, seven and five respectively. One
  toolkit audit row is trusted startup discovery. Resource operations also do
  not traverse the worker's execute-call logger. Reconciliation must distinguish
  these categories and compare calls/arguments/results where applicable;
  equality of counts is neither expected nor sufficient. The absent events
  are rejected calls, not evidence of unlogged successful execution.

For an enforced Codex route, demonstrate a request admission/dispatch check
that cannot be bypassed before forwarding/acting, plus the existing pinning,
inventory and refusal checks. Otherwise the already authorised Claude analyst
fallback can proceed when its own rebuilt-runtime and launcher conditions
pass. An alternative configuration-based assurance claim would be a different
explicitly agreed contract; calling the external monitor “fail-closed” does
not create that guarantee. The pinned-catalogue result remains a valid offline
candidate and is not withdrawn.

Abort cleanup also needs a concrete check. `Worker.run_python` starts worker
children with `start_new_session=True`; therefore killing only the supervisor
process group does not target those children. Normal `finally` cleanup works
while that supervisor remains alive, but SIGKILL cannot execute it. The launcher
must terminate/track worker groups as well and verify no trial process survives
deadline/abort before the next launch. This is code-derived; no crash-liveness
experiment was rerun in this review. It carries forward the sprint-3 residual.

Before qualification, rebuild both arm runtimes with the study wheel and run
the worker probes, actual client inventories and scripted refusals again on
the selected host. The current captured inventory predates the study tools.
Then test the new launcher's inventory mismatch, missing/truncated trace,
unexpected call, timeout/cleanup, unknown usage and balanced-block stop paths
offline. Usage, turn limits and deadlines need per-trial records; a whole-run
token ceiling does not enforce a single trial's budget.

No provider request, authentication change or live trial was performed.
