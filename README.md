# palaeo-agent

Working name for a native Python toolkit for agent-driven ecology and
palaeontology. People discuss scientific questions and review evidence through
agents such as Codex or Claude. The toolkit supplies explicit, validated
scientific operations and reproducible results.

This complements PAST's interactive application. PAST is a source of useful
examples and comparative evidence, not a dependency or a requirement to copy
every feature.

## Current state

Private development repository, established 30 October 2026. The first native
Python operation is descriptive reduced-major-axis regression, available through
the Python API and structured CLI. It saves a self-contained input snapshot,
resolved specification, numerical results, diagnostics and integrity manifest.
The name is provisional. No public release or full PAST compatibility is claimed.

- [Vision and scope](docs/vision.md)
- [Implementation framework](docs/architecture.md)
- [Staged implementation plan](docs/implementation-plan.md)
- [PAST examples and validation design](docs/past-validation.md)
- [Sources and observations](docs/sources.md)
- [Initial legacy example inventory](benchmarks/past/legacy-cases.json)
- [Offline index of all 14 legacy vignettes](benchmarks/past/vignettes/html/doc1.html)
- [First numerical comparison](docs/first-comparison.md)
- [First implementation results and limits](docs/tranche-1-results.md)
- [Third-party reference material](THIRD_PARTY.md)

## Run the first workflow

From the checkout, install the locked environment (Python 3.12.13):

```sh
uv sync --locked
uv run palaeo-agent discover
uv run palaeo-agent validate examples/dielasma-l2.json
uv run palaeo-agent run examples/dielasma-l2.json --output runs
```

The last command returns a JSON summary and a unique `run_dir`. Supply that path
to inspect its integrity or repeat the calculation from its saved input:

```sh
uv run palaeo-agent inspect RUN_DIR
uv run palaeo-agent reproduce RUN_DIR --output runs
```

A complete stored example is already available at
`benchmarks/past/dielasma-l2-run`; it can be inspected or reproduced with the
same commands.

JSON input paths resolve relative to the specification file. Scientific options
are explicit: `transform` is `none` or `log10`; `missing` is `error` or
`drop_pairs`. Unknown options, malformed inputs and unsupported calculations
produce structured errors. Ordinary results go to stdout; errors go to stderr.
The CLI exits 0 on success, 1 on numerical reproduction differences and 2 on a
request or execution error.

The same numerical core can be called directly:

```python
from palaeo_agent import rma_regression

result = rma_regression(
    [1, 2, 3], [3, 5, 7], sample_ids=["a", "b", "c"],
    transform="none", missing="error",
)
assert result["slope"] == 2
```

`run(specification, output_root)` produces the evidence bundle. A direct
`rma_regression` call returns a numerical result; it does not itself save files.
Inspection checks artefact integrity, and reproduction compares numerical
outputs. Neither certifies scientific interpretation or source authenticity.

## Check the implementation and reference archive

```sh
uv run pytest -q
uv run python scripts/capture_past.py --offline
uv run python scripts/reference_dielasma.py
```

The archive contains the supplied PAST 5.4 manual, all 17 data files from the
2001 ZIP, all 14 vignettes, 10 answer pages and 49 images. Original bytes and
offline reading copies are separate. These legacy examples do not establish a
complete current PAST 5 corpus. No PAST executable has been run for this project.

The next scientific capability is a community-data workflow, building on the
validated execution path rather than expanding the transport infrastructure.

## Working principles

- Native Python runtime; no R runtime or GUI requirement.
- Use established numerical libraries where their methods match our needs.
- Make scientific settings, exclusions and diagnostics explicit.
- Return compact summaries with access to complete saved artefacts.
- Keep scientific functions independent of agent clients and transports.
- Validate against analytical cases and independent references as well as PAST.
- Preserve disagreements and investigate them rather than tuning to a comparator.

These documents distinguish the agreed direction from proposed implementation
choices. They are the first design, not a frozen specification.
