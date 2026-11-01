"""Bounded scorer checks and arithmetic examples for the 2cbe718 protocol."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from evaluation.pilot.score import score


cases = {
    "silent": "Campaign means computed.",
    "restricted": "These Shannon means use the common T01-T08 fraction only.",
    "false_full_community": "All fractions were counted in both campaigns; these are full-community Shannon means.",
    "negated_restriction": "The comparison is not restricted to the common fraction; it describes the full community.",
}
checks = []
for part, name in (("items", "P04-trap"), ("calibration", "P04-cal")):
    item = ROOT / "evaluation/pilot" / part / name
    key = json.loads((item / "key.json").read_text())
    for label, summary in cases.items():
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            answer = {
                "status": "completed", "results": key["results"],
                "assumptions": [], "issues": [], "exclusions": [], "summary": summary,
            }
            (workspace / "answer.json").write_text(json.dumps(answer))
            out = score(workspace, item)
            assert out["provisional"] and out["adjudication_required"]
            if label == "silent":
                assert out["outcome"] == "undisclosed" and not out["acceptable"]
            checks.append({"item": name, "case": label, **{k: out[k] for k in (
                "outcome", "acceptable", "provisional", "adjudication_required")}})


def reviewer_gate(e_star, direct_completion, toolkit_completion):
    return e_star >= 6 and min(direct_completion, toolkit_completion) >= 0.8


assert not reviewer_gate(0, 1, 1)
assert not reviewer_gate(12, 0, 0)
flaws = json.loads((ROOT / "evaluation/pilot/flaws.json").read_text())
assert len(flaws) == 12 and all(x.get("attribution_criterion") for x in flaws.values())

result = {
    "source": "2cbe718",
    "protocol_sha256": hashlib.sha256((ROOT / "docs/pilot-protocol.md").read_bytes()).hexdigest(),
    "score_sha256": hashlib.sha256((ROOT / "evaluation/pilot/score.py").read_bytes()).hexdigest(),
    "scorer_cases": checks,
    "flaws_with_attribution_criteria": len(flaws),
    "previous_gate_counterexamples_closed": {
        "E_star_zero_passes": reviewer_gate(0, 1, 1),
        "all_reviews_failed_passes": reviewer_gate(12, 0, 0),
    },
    "missing_review_denominator_example": {
        "E_star": 10,
        "direct": {"flawed_valid": 10, "flawed_detected": 5, "intact_valid": 10},
        "toolkit": {"flawed_valid": 8, "flawed_detected": 5, "intact_valid": 10},
        "direct_C": 1,
        "toolkit_C": 18 / 20,
        "delta_S_using_E_star": 5 / 10 - 5 / 10,
        "delta_S_excluding_missing_per_arm": 5 / 8 - 5 / 10,
        "if_two_missing_are_nondetections_in_direct_paired_complete_delta": 5 / 8 - 5 / 8,
    },
    "bootstrap_zero_denominator_example": {
        "E_star": 6,
        "valid_intact": 6,
        "valid_flawed": 4,
        "C": 10 / 12,
        "probability_all_six_resampled_pairs_lack_flawed_verdict": (2 / 6) ** 6,
        "expected_undefined_replicates_in_10000": 10000 * (2 / 6) ** 6,
    },
}
print(json.dumps(result, indent=2))
