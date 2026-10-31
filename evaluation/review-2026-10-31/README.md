# Codex's sprint-1 counter-review evidence

The [review](../../docs/sprint-1-review.md) describes scope, findings, repairs
and limits. No live evaluation trials were run during this review.

- `independent-key-check.json`: materials-only numerical recomputation and
  exact alternative count matrices proving D2's non-identifiability. Recompute
  with `uv run python evaluation/review-2026-10-31/check_keys.py`.
- `scorer-edge-cases.json`: contradictory answers approved by the frozen v1
  scorer; new regressions exercise their rejection by the revised scorer.
- `evidence-mapping-audit.json`: no historical checklist change from repairing
  path/text alignment.
- `smoke-review.json`: independent costs, toolkit-use audit and all four D2
  adjudications, preserving the formal-underdetermination distinction.
- `isolation/`: actual generated sandbox profiles for synthetic credentials and
  state, plus a 20-probe native macOS receipt. No real secrets were read.
- `preservation.json`: original-evaluation path comparison against `b2e2964`
  and declared post-smoke launcher/documentation amendments. Bank, scorer,
  plans, raw trials and original scores remain unchanged.

The original harness source is preserved at freeze commit `5af0041`. Its
working-tree launcher is disabled. These receipts establish the stated
observations, not absence of every possible leak or scientific efficacy.
