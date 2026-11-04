# Palaeo-Agent

For research analysis, read the complete versioned primer before any analytical
work: `uv run palaeo-agent primer`, or `palaeo_agent.primer()` in Python. The
canonical text is `src/palaeo_agent/primer.md`. Use suitable existing API
operations; explicitly identify unsupported subtasks and designs.

For implementation, follow the method contracts in `docs/` and keep the engine
independent of the CLI and MCP transports. Run the relevant numerical and
bundle-reproduction tests. Inspection establishes integrity and specified
consistency checks; fresh reproduction checks numerical agreement. Neither
establishes the scientific validity of a sampling design or interpretation.
