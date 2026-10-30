# Implementation framework

Status: proposed design, 30 October 2026. No interfaces below exist yet.

## Smallest complete architecture

Use a native Python package with a `src/` layout, a `pyproject.toml`, and a
`uv`-managed environment when implementation starts. Select and test a supported
Python version against the numerical dependencies then; do not choose versions
from website snippets or create an untested lockfile now.

The execution path is:

    Python call or CLI request
        -> typed method specification and input validation
        -> scientific function using a selected numerical library
        -> common result and diagnostics
        -> saved evidence bundle plus compact response

Use direct, documented Python functions as the primary API. Expose the same
functions through a small CLI with structured JSON input/output and meaningful
exit codes. A method catalogue supplies machine-readable descriptions and
schemas. Generate transport schemas from the same definitions used for request
validation, avoiding independently maintained copies.

An MCP adapter is a later, thin transport for discovery, validation, execution
and result inspection. Do not create one server per analysis or require an HTTP
daemon for local work. The scientific engine must work without MCP, an agent
SDK, an API key or a language model.

## Scientific core

Keep data validation, transformations, numerical calculations and plotting
separate enough to test independently. Start with ordinary modules and
functions; introduce interfaces or registries only for actual shared needs.

Candidate dependencies are NumPy/SciPy for numerical work, pandas for labelled
tables, scikit-bio for relevant diversity and ordination methods, and Matplotlib
for figures. Assess statsmodels or scikit-learn when a selected method needs
them. These are candidates, not commitments to install everything at once.

Wrap only scientifically meaningful behaviour: explicit definitions, data
alignment, diagnostics, stable outputs and evidence capture. A library being
widely used does not establish equivalence with a PAST method. For example,
scikit-bio's documented PERMANOVA interface addresses a categorical grouping
factor; do not describe it as a general multifactor or restricted-permutation
implementation without separate evidence and implementation work.

## Data contract

The first data object contains a labelled sample-by-taxon matrix plus sample
metadata keyed by sample ID. Declare value semantics, row/column orientation,
missing-value handling and taxonomic resolution where known. Preserve raw input
and record derived transformations as explicit operations.

Check unique IDs, exact alignment, numeric validity and method-specific domain
restrictions. Count-dependent methods must reject proportions masquerading as
counts. Do not turn unknown values into absences, drop empty samples silently,
or assume pooled observations are independent. Missing-data policies belong to
the analysis specification and result.

Keep large arrays in files or memory, not in repeated agent messages. Use
explicit paths and stable identifiers to access them. Begin with transparent
CSV/TSV and JSON artefacts; adopt other formats only when an actual data volume
or scientific object warrants them. Parse PAST formats only after inspecting
real examples and their format variants.

## Method and run contracts

Each implemented method describes its identifier, version, required data,
options and defaults, supported designs, assumptions, limitations, numerical
backend, outputs and scientific references. Options affecting scientific
meaning must be resolved explicitly before computation and recorded afterwards.

A run specification identifies inputs, ordered preprocessing, method settings,
seed where relevant and output location. Fail on unknown or contradictory
options. Validation distinguishes mechanically checkable requirements from
scientific assumptions the agent must assess.

A result contains:

- Run identity, success/failure status and the resolved specification.
- Input fingerprints and retained/excluded observation IDs with reasons.
- Estimates, uncertainty measures and diagnostic metrics where applicable.
- Structured warnings and errors with codes, affected entities and explanations.
- Paths, media types and checksums for saved tables, plots and other artefacts.
- Package/dependency versions, execution environment and RNG details.
- Method references and a factual account of what was computed.

Return a compact summary by default. Full arrays, intermediate values and
figures remain available for inspection. Do not describe computational success
as evidence that the inferential assumptions hold. Seed capture does not
promise bit-for-bit agreement across numerical libraries or platforms.

Write each run to its own directory and publish its completion manifest only
after outputs are written successfully. Preserve failure diagnostics and
distinguish incomplete outputs from accepted results. Reopening a result must
not require access to a hidden interpreter session or the original chat.

## Execution and expansion

Start with synchronous, bounded local execution. Inspect expected data size
before allocating pairwise distance matrices, whose storage grows quadratically.
Add job handles, cancellation or remote execution when real workloads require
them, not as an initial scheduler project.

Ordinary Python scripts can compose analyses. Reuse established orchestration
tools if later workflows demand them. Preserve alternative analytical runs and
their stated purpose so sensitivity checks remain distinguishable from
selective reporting. The package does not automatically search for favourable
results.

New scientific modules should reuse the data, specification, diagnostic and
artefact conventions where they fit. Do not force trees, landmarks or uncertain
occurrence ages into a count-matrix schema. Add their contracts when needed.
