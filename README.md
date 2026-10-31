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
Python operations include descriptive reduced-major-axis regression, an
explicit count-community workflow and one-way free-permutation PERMANOVA, available through
the Python API, structured CLI and optional local MCP server. It saves a self-contained input snapshot,
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
- [Community workflow plan](docs/tranche-2-plan.md)
- [Community workflow results](docs/tranche-2-results.md)
- [Agent evaluation protocol](docs/evaluation.md)
- [PERMANOVA statistical contract](docs/permanova-contract.md)
- [Sprint plan and counter-review sequence](docs/sprints-1-2.md)
- [PERMANOVA validation and sprint-2 smoke results](docs/sprint-2-results.md)
- [Sprint-1 counter-review and evaluation repairs](docs/sprint-1-review.md)
- [Two-sprint reconciliation and next programme](docs/sprints-1-2-reconciliation.md)
- [Local scientific tools over MCP](docs/mcp.md)
- [Sprint-3 implementation and execution hold](docs/sprint-3-results.md)
- [Revised sprints 3–4 plan](docs/sprints-3-4-proposal.md)
- [Third-party reference material](THIRD_PARTY.md)

## Use from an agent

Install the optional MCP transport, then configure your agent to start the
server with a dedicated data directory:

```sh
uv sync --locked --extra mcp
uv run --extra mcp palaeo-agent-mcp --root /absolute/path/to/session
```

The tools discover methods, validate specifications, execute analyses, inspect
and reproduce bundles, and retrieve selected results. See the [MCP guide](docs/mcp.md)
for the tool contract and runnable examples. This local product server is
separate from the confined evaluation worker; live comparative evaluation
remains on hold pending a verified supervisor boundary.

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

## Community workflow and sensitivity

The complete stored comparison at `benchmarks/past/community-comparison`
contains a relative-abundance Bray-Curtis baseline and a raw-count sensitivity
run for the 10-sample, 23-taxon Llanvirn example. Each child is a normal run
bundle with snapshots, intermediate tables, diversity, PCoA and diagnostics.

```sh
uv run palaeo-agent validate examples/community-llanvirn-relative.json
uv run palaeo-agent run examples/community-llanvirn-relative.json --output runs
uv run palaeo-agent run examples/community-llanvirn-raw.json --output runs
uv run palaeo-agent compare BASELINE_RUN_DIR SENSITIVITY_RUN_DIR --output runs
uv run palaeo-agent inspect-comparison benchmarks/past/community-comparison
uv run palaeo-agent reproduce benchmarks/past/community-comparison/baseline --output runs
```

The comparison checks input identity, fixed settings and the same implementation,
Python and NumPy before attributing differences to transformation/distance.
Count semantics, orientation, missing values and empty-sample handling must be
declared. Metadata are joined by exact sample ID. Diversity is observed and
unstandardised. Negative PCoA eigenvalues remain visible; no correction or group
inference is applied. Binary Jaccard is also supported with `transform: none`.

`compare_community_runs` and `inspect_comparison` are also Python API functions.
Use `uv run python scripts/verify_community.py` to regenerate the complete
development verification in a new run directory. Reference regeneration uses
`python3 scripts/reference_community.py`, requiring R and jsonlite only for that
optional validation step; R is not an analysis runtime dependency.

Run bundle schema 2 replaces the development schema 1. The committed RMA demo
was regenerated with version 0.2; the original remains in Git commit `445da1b`.

## Check the implementation and reference archive

The group-comparison example uses synthetic A/B assignments on Llanvirn solely
for numerical validation; it asserts no ecological group hypothesis:

```sh
uv run palaeo-agent run examples/permanova-llanvirn.json --output runs
uv run python scripts/compare_past_permanova.py
```

PERMANOVA requires declared independent sampling units and free exchangeability
under the null. These assumptions cannot be verified from counts and group
labels. Results include exact or seeded Monte Carlo permutation schedules and
descriptive centroid dispersion. Blocks/repeated measures, dispersion inference
and inferential sensitivity comparisons are unsupported.

```sh
uv run pytest -q
uv run python scripts/capture_past.py --offline
uv run python scripts/reference_dielasma.py
uv run python scripts/compare_past_captures.py --output /tmp/past-comparison.json
```

The archive contains the supplied PAST 5.4 manual, all 17 data files from the
2001 ZIP, all 14 vignettes, 10 answer pages and 49 images. Original bytes and
offline reading copies are separate. These legacy examples do not establish a
complete current PAST 5 corpus. Native exports from the installed PAST 5.4
app now agree with the declared community and RMA calculations on two legacy
datasets, within export precision. See the
[validation results](docs/validation-tranche-3-results.md) for the captures,
independent R/vegan checks and the explained PCoA percentage convention.

Community workflows remain descriptive. Agent efficacy trials, inferential
methods and broader held-out validation remain future tranches.

The subsequent [blind-fixture validation](docs/validation-tranche-4-results.md)
passes all 60 objective fixtures and preserves one warning-policy judgment
disagreement. Requested PCoA dimensions must retain complete numerically
resolved positive eigenvalue blocks; an unresolved cutoff produces a structured
refusal with permissible dimensions.

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
