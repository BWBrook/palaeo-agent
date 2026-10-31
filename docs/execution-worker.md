# Confined scientific worker

This backend is for offline testing and a future reviewed evaluation client.
It is **not a live analyst launcher**. The installed Codex client has not met
its supervisor tool-inventory gate; see [the investigation](sprint-3-client-boundary.md).
The old launcher remains disabled.

The trusted MCP adapter exposes `worker_execute` (Python), `worker_read` and
`worker_write`. The toolkit arm additionally exposes the eight product tools
with a `palaeo_` prefix. Each call starts the arm's Python interpreter under a
macOS `sandbox-exec` profile. The scientific engine is unchanged. Product calls
use the same single-call transport as the standalone server.

The worker can read and write its trial, read its arm runtime and the selected
Python installation, and read explicitly listed operating-system libraries.
The profile denies network, child processes, user configuration, other trials,
supervisor audit records and runtime writes. It permits a small list of runtime
sysctl fields, not process-argument inspection. Python runs in isolated mode
with an allowlisted environment; HOME, temporary files and caches are local to
the trial. Deadlines kill the worker process group, and captured output is
bounded. If the supervisor itself is killed abruptly, its worker process group
can survive until separately terminated; a future live launcher must own that
crash cleanup. It is not implemented or claimed here. Call records and the exact profile remain outside worker access.

The operator must control the runtime, interpreter, configuration, audit
location and trial admission. These are never model arguments. Trial files
must be staged by copying, without shared hardlinks. Admission rejects
multiply-linked files and pre-existing `.worker` state. The operator must
retain exclusive control of admission and prevent concurrent external changes
to trial ancestors, runtimes and audit paths. Application path checks alone
are not a defence against another hostile host process with the same user.

A fresh worker is required for each trial. Within a trial, calls share only
trial-local files. The implementation intentionally has no subprocess/shell
tool: Python supplies the execution surface equally to both arms. The backend
is tested on macOS; Linux confinement is not implemented or claimed.

Build fresh, matched arm runtimes:

```sh
uv run --extra mcp python -m evaluation.execution.runtime /absolute/new/runtime-root
```

The builder refuses an existing destination, uses hash-locked scientific and
MCP packages, and installs the project wheel only in the toolkit arm. It saves
the complete installed-package manifests, RECORD hashes and wheel hash.
Entry-point shebangs differ by environment, so RECORD hashes are preserved per
arm rather than incorrectly required to match. No historical runtime is
changed.

A supervisor-owned JSON configuration supplies:

```json
{
  "trial_root": "/absolute/fresh/trial",
  "runtime": "/absolute/runtime-root/toolkit",
  "python": "/absolute/runtime-root/toolkit/bin/python",
  "trusted_read_roots": ["/absolute/exact/python/base-prefix"],
  "log_dir": "/absolute/new/audit-directory",
  "toolkit": true,
  "timeout_seconds": 60,
  "max_output_bytes": 65536
}
```

Use the selected interpreter's `sys.base_prefix` for its exact installation,
not the user's home or all of the package manager's directories. Start the
trusted adapter in the checkout environment:

```sh
uv run --extra mcp python -m evaluation.execution.server --config /absolute/config.json
```

To repeat synthetic tests through a real MCP client/server connection:

```sh
uv run --extra mcp python -m evaluation.execution.probes /absolute/runtime-root \
  /absolute/new/evidence-directory --work-root /absolute/new/synthetic-work-directory
```

Add `--demo` to run all three reference analyses, a structured refusal and
fresh-process reproduction through the same confined MCP interface. Use new
evidence and work directories for each invocation.

On macOS, run this outside an enclosing sandbox that prevents applying
Seatbelt. The optional native unit test also requires that context:

```sh
PALAEONATIVE_BOUNDARY_TESTS=1 uv run --extra mcp pytest -q tests/test_execution_worker.py
```

The probe inventories describe this worker server. They do not establish the
complete tool inventory of an authenticated agent supervisor. A future adapter
must capture and enforce that inventory before inference, freeze the model,
prompt, inputs, implementation, transport, runner and runtime manifests, and
enforce the agreed trial and token accounting. Until that is demonstrated and
reviewed by Claude, neither the integration trials nor the scientific pilot
may launch.
