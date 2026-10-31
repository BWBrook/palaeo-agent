# Local scientific tools over MCP

Install the optional transport with `uv sync --extra mcp`. Ordinary Python and
CLI operations do not import the MCP SDK. The transport uses the official
[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), version
2.3.0 in `uv.lock`.

Start the stdio server with an existing, dedicated data directory:

```sh
uv run --extra mcp palaeo-agent-mcp --root /absolute/path/to/session
```

The client's MCP configuration supplies that command and those arguments.
Only MCP messages go to stdout. The session root is selected by the operator,
not a tool argument. Relative paths start at that root. Absolute paths are
accepted only inside the root. Inputs, metadata, output directories and saved
bundles must resolve within it, including through symbolic links. Saved bundle
verification additionally rejects symlink artifacts. There is no arbitrary
file-reading or code-execution tool.

This is an application path boundary, not an operating-system sandbox. It
assumes the root and its ancestors are not being changed concurrently by
another process. Use the separately confined evaluation worker for adversarial
agents; it also constrains the interpreter, filesystem and network. Model
credentials belong outside that worker. Library environment discovery records
source and installed-distribution fingerprints; the root restriction concerns
user-selected data paths and artifact references, not normal interpreter and
library reads.

The small tool surface is:

| Tool | Arguments | Result |
| --- | --- | --- |
| `discover` | optional `method` | Short catalogue, or one method's complete input/output schemas |
| `validate` | `spec` | Existing data/numerical checks or a structured refusal |
| `run` | `spec`, optional `output` | Saved bundle reference and numerical summary |
| `inspect` | `bundle` | Integrity status, summary, field names, artifact references |
| `reproduce` | `bundle`, optional `output` | Fresh bundle and numerical comparison |
| `compare` | `baseline`, `sensitivity`, optional `output` | Existing descriptive community comparison |
| `inspect_comparison` | `bundle` | Comparison verification and artifact references |
| `result` | `bundle`, `field`, optional paging arguments | One verified result field |

`spec` is the same discriminated Pydantic specification as the Python API;
`tools/list` embeds its schema. Numerical implementations and scientific
refusals remain in the library. Input validation failures and scientific errors
return MCP `isError: true` with the same structured content in the text and
`structuredContent` fields. Unsupported repeated or restricted designs fail
schema validation; `validate` never establishes sampling independence.

Default output roots are `runs` and `comparisons`. Returned bundle and artifact
references are relative to the session root. Runs use new UUID directories;
this interface does not overwrite earlier bundles. A run without its complete
manifest cannot pass `inspect`. A killed process may leave partial files; the
transport preserves them and never reports them as complete.

Large arrays stay in saved artifacts. For example, after inspecting a run:

```json
{"bundle":"runs/RETURNED_ID","field":"distances","offset":0,"limit":10,"column_offset":0,"column_limit":10}
```

Rows and matrix columns default to 25 and are capped at 100. Select nested
object fields with dots, such as `permutation.statistics`; selecting an object
returns its child field names. Lists in summaries longer than 25 are explicitly
truncated, with a count. Use `result` for the remainder. Inspection checks
integrity before exposing a selected field; integrity is not scientific
validity or authenticity.

For a reproducible demonstration using the vendored PAST reference inputs:

```sh
uv run --extra mcp python examples/mcp/demo.py /tmp/palaeo-mcp-demo-NEW
```

The demo creates a new directory, copies the required inputs, runs RMA,
community analysis and declared PERMANOVA, checks a repeated-design refusal,
and reproduces all three bundles in a new MCP server process. `receipt.json`
records the results. It is an integration demonstration, not an analyst trial
or evidence of scientific superiority.

The evaluation worker can invoke the same operation in a fresh confined
process without keeping a product server alive:

```sh
printf '%s' '{"method":"rma"}' | python -m palaeo_agent.mcp_server \
  --root /absolute/path/to/session --call discover
```

This single-call entry point uses `Transport(root).dispatch(name, arguments)`;
`tool_definitions()` supplies its exact schemas. It does not import the MCP
SDK. The caller owns process deadlines, confinement and call logging.
