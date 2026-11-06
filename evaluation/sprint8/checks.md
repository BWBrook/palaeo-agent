# Sprint 8 checks for I1 and I2, fixed before launch

Claude (Opus 5.5), 6 November 2026, before any I1/I2 inference. Source:
[proposal §7](../../docs/sprints-7-8-proposal.md) as settled with Codex.
`score.py` computes the mechanical checks from the exported session record;
the judged checks are read by Claude and then by Codex. Two sessions give
descriptive evidence for one client and model, not a compliance rate, and
their difference cannot identify a causal effect of the bootstrap.

## Sessions

| ID | Case | Runtime | Delivery | User instruction (prompt file) |
| --- | --- | --- | --- | --- |
| I1 | `llanvirn` | toolkit | `mcp`: server instructions, `discover` pointer, `primer` tool | `instructed-contract.md` + `instructed-mcp.md`: use the toolkit; nothing about the primer |
| I2 | `dielasma` | toolkit | `python`: scientific MCP tools and instructions withheld | `instructed-contract.md` + `instructed-python.md`: print the full `palaeo_agent.primer()` object first |

Model Sonnet 5.5 through the full (not `--bare`) launcher route, subscription
login only. Ceiling 120,000 counted tokens across both sessions and their
retrospectives, with launch-stop. No repeats, twins or extra trials.

## Delivery, at three levels

1. **Available:** the frozen runtime's installed primer has the committed
   SHA-256 (checked at freeze, `qualification.json`).
2. **Read:** the complete primer body appears in a worker or toolkit tool
   result, and in the transcript's visible tool results, before the first
   analytical call. Analytical means any `validate`, `run`, `study_run`,
   `compare` or `reproduce` call, or Python that does more than import,
   print, read files, list the directory, or call `primer()`/`discover()`.
   A hash alone does not count.
3. **Used:** the API and scientific checks below.

## API use

Supported subtasks, each through the API in the delivered package
(`analysis.py` or `specs/`):

- **I1:** diversity and Bray–Curtis (`community`); rarefaction and coverage
  (`rarefaction`); declared-pair homogeneity (`count_homogeneity`).
- **I2:** `validate` and `rma`.

Mechanical: `analysis.py` imports `palaeo_agent`; each listed method occurs
in the package; the report contains the unsupported-parts table and the
primer's SHA-256; the package replays in a fresh confined worker.

## Judged

- Every bespoke computation is of an unsupported part and declared with a
  reason; otherwise it is a violation. (I1 example: none of the listed
  subtasks recomputed by hand. I2 example: SMA intervals and slope tests are
  unsupported and may be bespoke if declared.)
- No unsuitable design is forced. I1: no PERMANOVA or other group test of
  horizons treated as exchangeable units. I2: descriptive `rma` is never
  presented as inference.
- Warnings that the operations return are reported with what was concluded
  (I2: the L2 `repeated_block`; if a study is used, any
  `row_filter_removes_pairs`).

## Outcome rules

Report each check per session. If I1 fails on delivery but I2 succeeds,
record both and recommend the explicit bootstrap as the documented baseline;
no further trials follow automatically. Codex reviews the records and the
science before the joint report.
