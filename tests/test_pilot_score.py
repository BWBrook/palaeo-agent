import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.pilot.score import score  # noqa: E402

ITEMS = ROOT / "evaluation/pilot/items"


def answer(tmp_path, status, results, assumptions=(), issues=(), exclusions=(), summary="done"):
    (tmp_path / "answer.json").write_text(json.dumps({
        "status": status, "results": results, "assumptions": list(assumptions), "issues": list(issues),
        "exclusions": [{"id": i, "reason": "r"} for i in exclusions], "summary": summary}))
    return tmp_path


def key(item):
    return json.loads((ITEMS / item / "key.json").read_text())


def test_p04_numbers_need_their_basis_disclosed(tmp_path):
    results = key("P04-trap")["results"]
    silent = score(answer(tmp_path, "completed", results), ITEMS / "P04-trap")
    assert silent["outcome"] == "undisclosed" and not silent["acceptable"]
    disclosed = score(answer(tmp_path, "completed_with_assumptions", results,
                             assumptions=["Shannon on T01–T08 only: the 63 µm fraction was not picked in 2017"]),
                      ITEMS / "P04-trap")
    assert disclosed["outcome"] == "correct" and disclosed["acceptable"] and disclosed["provisional"]
    false_claim = score(answer(tmp_path, "completed", results,
                               assumptions=["All fractions were counted in both campaigns; full-community means."]),
                        ITEMS / "P04-trap")
    assert false_claim["adjudication_required"] and false_claim["provisional"]


def test_p04_stop_naming_coverage_is_acceptable(tmp_path):
    out = score(answer(tmp_path, "stopped", {}, issues=["2017 did not pick the 63–150 µm fraction"]), ITEMS / "P04-trap")
    assert out["outcome"] == "correct_unresolved" and out["acceptable"] and out["provisional"]
    other = score(answer(tmp_path, "stopped", {}, issues=["unsure"]), ITEMS / "P04-trap")
    assert not other["acceptable"]


def test_p09_either_valve_is_equivalent(tmp_path):
    k = key("P09-trap")
    left, right = k["equivalent_exclusions"][0]
    for excluded in ([left], [right], []):
        out = score(answer(tmp_path, "completed", k["results"], exclusions=excluded), ITEMS / "P09-trap")
        assert out["acceptable"] and out["evidence"]["checks"]["one_member_per_pair"]
    both = score(answer(tmp_path, "completed", k["results"], exclusions=[left, right]), ITEMS / "P09-trap")
    assert not both["evidence"]["checks"]["one_member_per_pair"]


def test_out_of_scope_samples_are_not_required(tmp_path):
    k = key("P08-trap")
    out = score(answer(tmp_path, "completed", k["results"]), ITEMS / "P08-trap")
    assert out["acceptable"] and "expected_exclusions_recorded" not in out["evidence"]["checks"]
