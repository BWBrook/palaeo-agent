"""Executable readings of the draft rules, not tests of a production analyser."""

import hashlib
import json
from pathlib import Path


def rule4(e_star, delta_s=None, delta_a=None):
    delta_t = lower = delta_t_tk = delta_t_other = 0.5
    delta_c, cost_ratio = 0.0, 1.0
    confined = delta_t_tk >= 0.15 and delta_t_other < 0.05
    return (
        delta_t >= 0.15
        and lower > 0
        and delta_c <= 0.05
        and cost_ratio <= 2
        and not confined
        and (e_star < 6 or (delta_s >= -1 / e_star and delta_a <= 1 / e_star))
    )


repo = Path(__file__).resolve().parents[4]
protocol = repo / "docs/pilot-protocol.md"
planted = {"class": "preparation", "error": "L3 divided by 10", "field": "L3 measurements"}
reviewer = {
    "verdict": "reject",
    "class": "preparation",
    "field": "excluded specimen I01",
    "justification": "Specimen I01 was excluded without evidence.",
}
result = {
    "kind": "logical_counterexamples_to_documented_rules_not_live_trials",
    "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
    "shared_analyst_endpoints": {
        "I": 0,
        "D": 0.5,
        "delta_T": 0.5,
        "delta_T_interval": [0.5, 0.5],
        "delta_T_toolkit": 0.5,
        "delta_T_other": 0.5,
        "delta_C": 0,
        "K": 1,
    },
    "no_acceptable_paired_packages": {
        "E_star": 0,
        "reviewer_endpoints": "undefined",
        "rule4_expand": rule4(0),
    },
    "all_reviewer_trials_failed": {
        "E_star": 12,
        "valid_verdicts": 0,
        "direct_sensitivity": 0,
        "toolkit_sensitivity": 0,
        "direct_accusations": 0,
        "toolkit_accusations": 0,
        "rule4_expand": rule4(12, 0, 0),
    },
    "unrelated_rejection_same_class": {
        "planted": planted,
        "reviewer": reviewer,
        "class_or_step_rule_counts_detection": reviewer["verdict"] == "reject"
        and (reviewer["class"] == planted["class"] or reviewer["field"] == planted["field"]),
        "planted_error_identified": False,
    },
}
assert result["no_acceptable_paired_packages"]["rule4_expand"]
assert result["all_reviewer_trials_failed"]["rule4_expand"]
print(json.dumps(result, indent=2))
