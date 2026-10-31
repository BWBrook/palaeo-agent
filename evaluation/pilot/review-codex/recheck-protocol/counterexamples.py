"""Reproduce protocol counterexamples without model calls or toolkit imports."""
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from evaluation.revised.score import score


def main():
    item = ROOT / "evaluation/pilot/items/P10-control"
    key = json.loads((item / "key.json").read_text())
    answer = {"status": "completed", "results": key["results"], "assumptions": [],
              "exclusions": [], "issues": [],
              "summary": "Shannon diversity decreased from the oldest to the youngest sample."}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / "answer.json").write_text(json.dumps(answer))
        result = score(path, item)
    assert result["outcome"] == "correct" and not result["adjudication_required"]
    rng = random.Random(20261101)
    effects = [1] * 7 + [0] * 5
    means = sorted(sum(rng.choices(effects, k=12)) / 12 for _ in range(10000))
    assert means[1000] > 0
    files = [Path(__file__), ROOT / "docs/pilot-protocol.md",
             ROOT / "docs/sprints-3-4-proposal.md",
             ROOT / "evaluation/revised/score.py", item / "key.json"]
    receipt = {
        "baseline": "a3ca5706a3cc5b72a26c854366d4c887cfdd9b82",
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "intact_reference_counterexample": {"answer": answer, "score": result},
        "denominator_counterexample": {"E": 12, "correct_direct": 8, "correct_toolkit": 12,
            "false_rejections_each": 1, "conditional_delta": 1/12 - 1/8, "E_normalised_delta": 0},
        "confined_benefit_counterexample": {"item_effects": effects, "delta_T": sum(effects)/12,
            "bootstrap_80_percent_order_statistic_bounds": [means[999], means[8999]],
            "seed": 20261101, "resamples": 10000, "other_delta_T": 0,
            "other_rule4_conditions": "Assume delta_C=delta_S=delta_A=0, K=1, E=12, I=0 and D=0.",
            "draft_decision": "expand", "agreed_plan_decision": "stratum-confined repair"},
        "precedence_counterexample": {"D": 1, "delta_T": -1, "E": 12, "I": 0,
            "first_matching_rule": 2, "hidden_adverse_condition": "rule 3 primary harm"},
        "inference_calls": 0,
    }
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"counterexamples": 4, "receipt": str(HERE / "receipt.json")}))


if __name__ == "__main__":
    main()
