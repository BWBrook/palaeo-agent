# Codex client: scripted catalogue follow-up

**31 October 2026. Offline route demonstrated; live-launch gate still pending.**
Claude's suggestion to test a pinned custom catalogue was productive. The
installed Codex 0.166.0 can execute the confined worker while omitting patch,
shell and collaboration tools from its request. This supersedes the earlier
conclusion about the proposed flags alone, not the live-evaluation hold.

## Observations

A localhost fake Responses endpoint scripted tool calls without inference,
credentials or forwarding. Both arms used a fresh HOME/CODEX_HOME, ignored user
configuration and rules, and used the same catalogue and disabling flags. The
full client binary hash is recorded. Every constructed request was preserved.
The endpoint has a 25-request cap and each process a 90-second wall deadline.
The successful cases used 14 requests (direct) and 15 (toolkit).

| Check | Direct | Toolkit |
| --- | --- | --- |
| Worker tools advertised | 3 | 11 |
| Additional tools | 3 MCP resource helpers | the same |
| Inventory unchanged across all requests | yes | yes |
| Two confined `print(6*7)` calls | 42 | 42 |
| Outside synthetic secret read through worker | denied | denied |
| Hidden function and custom `apply_patch` | unsupported | unsupported |
| Hidden shell, exec and plain/namespaced spawn | unsupported | unsupported |
| Resource read from the known worker using outside file URI | method not found | method not found |
| Resource read naming an unknown server | refused | refused |
| Resource and template lists | empty | empty |
| Toolkit discovery through confined worker | not applicable | succeeded |
| Canary writes or changes | none | none |
| Authorization header | absent | absent |

The helpers are scoped to the sole configured worker server. They do not open
host file URIs themselves; the worker implements no resource-reading method.
This extra surface is retained explicitly in the frozen candidate inventory,
rather than called MCP-only without qualification.

The first attempt used an obsolete flattened name instead of the Responses
`namespace` field, so its positive controls failed. The second used the right
wire format but the client's read-only/never policy refused MCP approval.
Both failures are preserved. Explicit `approval_mode="approve"` for the named
worker tools in the disposable command configuration produced the successful
cases. This approves only those already-confined tools; it changes no personal
configuration or worker permissions. Two effective configurations were tested,
with a wire-format correction and then the same final configuration in each arm.

## Catalogue and source evidence

The exact before/after values are in
[`overrides.json`](../evaluation/sprint3/codex-client-scripted/overrides.json).
Eight metadata fields changed: patch becomes null, shell disabled, tool mode
direct, multi-agent version null, experimental tools empty, node REPL disabled,
search support false, and Responses Lite false. Model identity and bundled
instructions remain unchanged; this is a controlled client configuration shared
by both arms, not an untouched provider catalogue.

The matching public source supports static-catalogue precedence:

- The [configured provider constructor](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/model-provider/src/provider.rs#L507-L518)
  selects `StaticModelsManager` when an explicit catalogue is supplied, before
  constructing the remote endpoint manager.
- The [static manager](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/models-manager/src/manager.rs#L807-L888)
  serves those supplied models and ignores refresh strategy and ETag refresh.
  Remote catalogue refresh therefore cannot replace these explicit settings
  through this manager. This is source evidence, not an authenticated-provider
  experiment.
- [Model metadata types](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/protocol/src/openai_models.rs#L302-L335)
  define disabled shell and direct tool mode; the
  [Responses item schema](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/protocol/src/models.rs#L1053-L1066)
  supplies the tool namespace field.

## What is not yet qualified

**Codex's JSONL initialization still does not expose a complete tool inventory.**
The observed pre-tool stream contains `thread.started` and `turn.started`, not
an inventory. The request capture gives the complete actual tool definitions,
but the capture endpoint replaces the real provider. No live fail-closed
request admission gate or evaluation launcher was implemented here.

The result is therefore an offline candidate route. It does not yet meet the
plan's literal requirement for a complete client-init inventory at every live
launch. A reviewed adapter must enforce that requirement (or record an agreed
replacement such as inspection of every constructed request before forwarding),
while preserving the authentication/worker separation. A pre-launch fake
capture plus a pinned binary/catalogue supplies useful evidence but is not the
same as such a gate. No authenticated provider was contacted in this review.

The runtime is the tested sprint-3 wheel, with eight palaeo tools. Sprint-4
study tools require a new wheel and corresponding inventories/probes. The
supervisor crash-cleanup, resource-limit and host-qualification limitations
from sprint 3 also remain. No integration, calibration or pilot trial ran.

Evidence and reproducible script are in
[`evaluation/sprint3/codex-client-scripted`](../evaluation/sprint3/codex-client-scripted/).
The aggregate receipt pins all evidence files and records both successful and
failed cases. Repeat with `probe.py NEW_OUTPUT_DIRECTORY --arm direct` or
`--arm toolkit`, outside a nested sandbox that prevents Seatbelt.
