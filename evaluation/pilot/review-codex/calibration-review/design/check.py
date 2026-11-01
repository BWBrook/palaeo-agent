"""Arithmetic checks; no model calls or answer/adjudication reads."""

import json
from pathlib import Path


root = Path(__file__).resolve().parents[5]
summary = json.loads((root / "evaluation/pilot/calibration-evidence/summary.json").read_text())
direct = summary["arms"]["direct"]["median_counted_tokens"]
toolkit = summary["arms"]["toolkit"]["median_counted_tokens"]
median = summary["tokens"]["median_counted"]

# Variance of the mean of J item means under an illustrative random-effects
# decomposition: (between_item_variance + within_item_variance / sessions) / J.
variance_examples = []
for between, within in ((0, 1), (1, 1), (4, 1)):
    v2 = (between + within / 2) / 12
    v4 = (between + within / 4) / 12
    variance_examples.append({
        "between_item_variance": between,
        "within_item_variance": within,
        "variance_ratio_4_over_2_sessions": v4 / v2,
        "standard_error_ratio": (v4 / v2) ** 0.5,
    })

# The prior missing-review counterexample now uses one common valid set.
direct_verdicts = [1] * 5 + [0] * 5
toolkit_verdicts = [1] * 5 + [0] * 3 + [None] * 2
pairs = [(d, t) for d, t in zip(direct_verdicts, toolkit_verdicts) if d is not None and t is not None]
delta = sum(t - d for d, t in pairs) / len(pairs)
assert len(pairs) == 8 and delta == 0

print(json.dumps({
    "source_revision": "4a80b5f",
    "calibration_trials": len(summary["trials"]),
    "total_counted_tokens": summary["tokens"]["total_counted"],
    "direct_median_counted_tokens": direct,
    "toolkit_median_counted_tokens": toolkit,
    "ratio_of_arm_medians": toolkit / direct,
    "pooled_median_counted_tokens": median,
    "working_ceiling_96_at_unchanged_cost": 1.5 * median * 96,
    "hypothetical_ceiling_192_at_unchanged_cost": 1.5 * median * 192,
    "variance_examples_not_power_estimates": variance_examples,
    "independent_double_success_examples_not_fitted_rates": {str(p): p * p for p in (0.95, 0.98)},
    "prior_missingness_counterexample_under_current_rules": {"n_S": len(pairs), "delta_S": delta},
}, indent=2))
