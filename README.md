# palaeo-agent

Working name for a native Python toolkit for agent-driven ecology and
palaeontology. People discuss scientific questions and review evidence through
agents such as Codex or Claude. The toolkit supplies explicit, validated
scientific operations and reproducible results.

This complements PAST's interactive application. PAST is a source of useful
examples and comparative evidence, not a dependency or a requirement to copy
every feature.

## Current state

Local design repository, established 30 October 2026. No analysis code,
installed environment, numerical results or compatibility claims yet. No
remote repository or public release has been created. The name is provisional.

- [Vision and scope](docs/vision.md)
- [Implementation framework](docs/architecture.md)
- [Staged implementation plan](docs/implementation-plan.md)
- [PAST examples and validation design](docs/past-validation.md)
- [Sources and observations](docs/sources.md)
- [Initial legacy example inventory](benchmarks/past/legacy-cases.json)

The immediate next tranche is to establish the example corpus and build one
complete analysis through the Python API and a structured command-line
interface. Its evidence bundle must be reproducible in a fresh process.

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
