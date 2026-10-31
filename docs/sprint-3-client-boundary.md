# Sprint 3: Codex client boundary investigation

**31 October 2026; Codex CLI 0.166.0; decision: HOLD for live evaluation.**
The proposed feature-flag configuration does not produce an MCP-only client.
This was checked against the matching public source tag and an actual request
constructed by the installed binary. No real model request was sent.

## Observed request

A credential-free temporary `HOME`/`CODEX_HOME`, an empty working directory and
a localhost fake Responses provider were used. The provider recorded only the
request body and whether an Authorization header existed; the latter was
**false**. It returned HTTP 400 without forwarding anything. Codex preserved a
failed turn. This is an offline client probe, not one of the eight integration
trials and not a claim about the authenticated provider's full tool inventory.

The binary's unmodified bundled `gpt-6.1-sol` model definition was used. Disabled
features were:

```text
shell_tool unified_exec browser_use computer_use apps plugins remote_plugin
multi_agent multi_agent_v2 view_image image_generation goals memories hooks
skill_search tool_suggest shell_snapshot context_management sleep_tool
in_app_browser code_mode code_mode_only code_mode_host incremental_tools
enable_request_compression
```

Other relevant overrides were:

```text
--ignore-user-config --ignore-rules --skip-git-repo-check --ephemeral --json
-s read-only
-c web_search="disabled"
-c tools.update_plan.enabled=false
-c tools.experimental_request_user_input.enabled=false
-c project_doc_max_bytes=0
-c model_provider="offline"
-c model_providers.offline.name="offline"
-c model_providers.offline.base_url="http://127.0.0.1:<ephemeral-port>"
-c model_providers.offline.wire_api="responses"
-c model_providers.offline.requires_openai_auth=false
-c model_providers.offline.request_max_retries=0
-c model_providers.offline.stream_max_retries=0
-c model_providers.offline.supports_websockets=false
```

The request's `input` contains an `additional_tools` item (looking only for a
top-level `tools` field would incorrectly conclude there were none):

| Surface | Tools actually advertised |
| --- | --- |
| `functions` | `exec`, `wait` |
| Nested in `exec`'s tool declarations | `apply_patch`, `list_mcp_resource_templates`, `list_mcp_resources`, `read_mcp_resource`, `clock__curr_time` |
| `collaboration` | `followup_task`, `interrupt_agent`, `list_agents`, `send_message`, `spawn_agent`, `wait_agent` |

This is a direct observation of advertisement, not successful execution of
those tools. Disabling the Code Mode host also produced a client error saying
Code Mode is unavailable and will fail closed; it therefore cannot serve as a
usable way to remove the extra tools while retaining MCP execution.

The exact command, request body, extracted tool definitions, header-presence
receipt and stdout/stderr are preserved in
[`evaluation/sprint3/client-boundary`](../evaluation/sprint3/client-boundary/),
with SHA-256 hashes in `receipt.json`. `capture_offline.py` reproduces the
localhost capture into a required fresh output directory; it refuses to
overwrite an existing directory. The recorded request contains the explicit
synthetic task, bundled model instructions and temporary paths, with no
personal configuration or credential values. It uses no configured MCP
servers: this is negative evidence of extra builtins, not a positive full arm
inventory. No further workaround trial was attempted. The failed first configuration attempt
(`tools.update_plan=false`) was corrected to the schema's `.enabled=false`
shape before the recorded capture.

## Source and local protocol checks

All links below are pinned to `rust-v0.166.0`, matching the installed binary.
These findings identify why flags alone are insufficient; the offline capture
above independently checks the relevant resulting behaviour.

- [Tool registration](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/tools/spec_plan.rs): shell registration checks `ShellTool` (lines
  1176–1205), but patch registration checks the model's
  `apply_patch_tool_type` independently (1347–1350). The installed bundled
  catalogue assigns `freeform` patch tools to all twelve listed models.
  `apply_patch_freeform` is a removed feature, not a disabling switch.
- [Tool policy](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/ext/extension-api/src/tool_policy.rs): the Rust extension API has an explicit
  startup `allowed_tools` ceiling. It must be supplied through
  `ExtensionDataInit`; neither installed CLI help nor the generated public
  app-server `ThreadStartParams` exposes it. `dynamicTools` adds tools; it is
  not this ceiling. Building a custom Codex host would be a separate, materially
  larger implementation decision.
- [Prompt debugging](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/prompt_debug.rs): `codex debug prompt-input` returns
  `prompt.input`, not a complete tool-router inventory. The model's initial
  input may contain tool definitions, but this interface promises no complete
  enforced inventory and is not a per-launch admission gate.
- [PreModelRequest schema](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/hooks/schema/generated/model-request.command.input.schema.json): this
  hook receives session/turn/model/cwd information, not tool schemas.
- [Request ordering](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/turn.rs): the pre-model hook runs before `stream` builds
  the actual request (around 2755–2775).
- [Trace recording](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/rollout-trace/src/thread.rs): `CODEX_ROLLOUT_TRACE_ROOT` enables diagnostic
  bundles and records request payloads, but trace startup is explicitly
  best-effort. This is useful evidence after construction, not a fail-closed
  pre-launch inventory check.

Local commands used, without loading personal credentials:

```sh
codex --version
codex exec --help
codex features list
codex debug prompt-input --help
codex debug models --bundled
codex app-server generate-json-schema --experimental --out TEMP_DIRECTORY
```

The public tagged source was read through GitHub. No credential contents,
personal client state, real answer keys or frozen evaluation records were read
or changed. Only temporary probe files and this note were written.

## Consequence and fallback requirements

Keep the old live-evaluation hold and do not infer safety from an empty
observed tool-call log. A worker sandbox can protect calls that pass through it;
it cannot constrain an unrelated tool registered in the supervisor.

A custom `model_catalog_json` could alter tool metadata, but that changes the
client's model/tool contract. It is not accepted here as equivalent to the
provider's advertised configuration, and would still require actual inventory
checks at every launch, fail-closed rejection before model execution, and
worker-boundary probes through every reachable tool.

The supported alternatives to investigate are a provider client whose request
is explicitly constructed from the confined tool allowlist (using separately
authorised credentials/resources), or a disposable account/VM with a separately
proved authentication boundary. Neither is established by this probe. A
transport proxy that checks each final request might provide admission control,
but forwarding personal authentication would make it trusted infrastructure
requiring its own explicit implementation and review; it is not silently
introduced as an evaluation workaround.

The product MCP server and offline worker tests remain useful independent
sprint deliverables. The scientific pilot must wait until a functional client
boundary meets the frozen-inventory and actual-call-path requirements.
