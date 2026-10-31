# Study repair verification

Reviewed commit `a3ca5706a3cc5b72a26c854366d4c887cfdd9b82` on macOS.
**S1–S4 are verified fixed for the reported defects.** No residual defect was
found in the checks below. No production code, old evidence, bank or keys were
changed or used by this verification.

The independent [check script](check.py) ran **29 checks, all passed**;
[the receipt](receipt.json) retains outcomes and the script SHA-256. The scratch
bundles were temporary and have been removed. Run from the repository root:

```sh
uv run python evaluation/pilot/review-codex/recheck-study/check.py /tmp/study-recheck.json
```

| Finding | Verification |
| --- | --- |
| S1 | The original empty-step/deleted-run forgery is rejected. Missing, duplicate, reordered and unknown steps; missing run records; inconsistent study status; unknown step status; not-run without failure; complete after failure; and multiple failures are rejected. A legitimate partial analysis keeps its earlier completed run, verifies and reproduces. |
| S2 | MCP inspection rejects external symlinked `runs/`, `derived/` and `inputs/`. A symlink at the nested UUID run-directory level, a dangling link and a FIFO are rejected. No external numerical summary is returned in the MCP cases. |
| S3 | The canonical-table transpose defect is rejected before execution. Wrong/missing format, RMA over declared counts and community analysis over declared measurements are also rejected. |
| S4 | A study with a completed dataset, then a failed dataset, then a later dataset records `complete`, `failed`, `not_run`, followed by `not_run` for the analysis. The legitimate partial bundle verifies and reproduces. |

Positive controls include a complete study and its reproduction. The existing
study test file also passes: **17 passed in 7.18 s**, using
`uv run pytest -q tests/test_study.py`.

This is verification of the reported integrity/contract repairs, not a complete
security audit or a scientific-validity assertion. It does not qualify the
rebuilt confined runtime, live launcher, pilot scorer or the full pre-freeze
gate. Consistently declared scientific mistakes remain a separate reviewer
judgment, as intended by the study contract.
