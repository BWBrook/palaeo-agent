import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "evaluation"
sys.path.insert(0, str(EVAL))
import score  # noqa: E402


def key(item):
    return json.loads((EVAL / "items" / item / "key.json").read_text())


def trial(tmp_path, item, status="completed", results=None, assumptions=(), issues=(), exclusions=(), summary="",
          files=None):
    ws = tmp_path / item
    shutil.copytree(EVAL / "items" / item / "materials", ws)
    answer = {"status": status, "results": results or {}, "assumptions": list(assumptions),
              "exclusions": list(exclusions), "issues": list(issues), "summary": summary}
    (ws / "answer.json").write_text(json.dumps(answer))
    for name, text in (files or {}).items():
        (ws / name).write_text(text)
    return score.score(ws, EVAL / "items" / item)


def test_bank_regenerates_byte_for_byte(tmp_path):
    subprocess.run([sys.executable, str(EVAL / "build_items.py"), str(tmp_path / "items")], check=True,
                   capture_output=True)
    assert (tmp_path / "items/MANIFEST.json").read_bytes() == (EVAL / "items/MANIFEST.json").read_bytes()
    for path in (EVAL / "items").rglob("*"):
        if path.is_file():
            twin = tmp_path / "items" / path.relative_to(EVAL / "items")
            assert hashlib.sha256(twin.read_bytes()).digest() == hashlib.sha256(path.read_bytes()).digest(), path


def test_every_trap_has_a_twin_and_smoke_set_is_fixed():
    keys = [json.loads(p.read_text()) for p in (EVAL / "items").glob("*/key.json")]
    traps = {k["catalogue"] for k in keys if k["class"] == "trap"}
    twins = {k["catalogue"] for k in keys if k["class"] == "twin"}
    assert traps == twins == {f"D{i}" for i in range(1, 11)}
    assert sorted(k["item"] for k in keys if k["smoke"]) == [
        "D1-trap", "D1-twin", "D2-under", "D3-trap", "D3-twin", "D6-trap", "D6-twin"]


def test_correct_and_rounding_tolerance(tmp_path):
    k = key("D1-trap")["results"]
    result = trial(tmp_path, "D1-trap", results={"slope": round(k["slope"], 6), "intercept": k["intercept"], "n": 38.0})
    assert result["outcome"] == "correct" and result["pitfall"] == "handled"


def test_failure_signature_is_undetected_pitfall(tmp_path):
    sig = key("D1-trap")["failure_signatures"][0]["results"]
    result = trial(tmp_path, "D1-trap", results=sig)
    assert result["outcome"] == "wrong"
    assert result["signature"] == "complete_case_all_columns" and result["pitfall"] == "undetected"


def test_stopping_on_a_solvable_item_is_false_refusal(tmp_path):
    result = trial(tmp_path, "D3-twin", status="stopped", issues=["Unsure how to join metadata"])
    assert result["outcome"] == "false_refusal"


def test_missing_or_malformed_answer_fails(tmp_path):
    ws = tmp_path / "ws"
    shutil.copytree(EVAL / "items/D6-twin/materials", ws)
    assert score.score(ws, EVAL / "items/D6-twin")["outcome"] == "failed"
    (ws / "answer.json").write_text(json.dumps({"status": "done", "results": {}}))
    assert score.score(ws, EVAL / "items/D6-twin")["outcome"] == "failed"


def test_pairs_accept_either_order(tmp_path):
    k = key("D6-twin")["results"]
    flipped = {"|".join(reversed(p.split("|"))): v for p, v in k["braycurtis"].items()}
    assert trial(tmp_path, "D6-twin", results={"richness": k["richness"], "braycurtis": flipped})["outcome"] == "correct"


def test_transposed_analysis_matches_its_signature(tmp_path):
    sig = key("D6-trap")["failure_signatures"][0]["results"]
    result = trial(tmp_path, "D6-trap", results=sig)
    assert result["outcome"] == "wrong" and result["signature"] == "transposed"


def test_undeclared_guess_on_underdetermined_item_is_wrong(tmp_path):
    guess = key("D2-trap")["failure_signatures"][0]["results"]
    result = trial(tmp_path, "D2-under", results=guess, summary="Computed Bray-Curtis on the table values.")
    assert result["outcome"] == "wrong"


def test_declared_assumption_or_stop_on_underdetermined_item(tmp_path):
    guess = key("D2-trap")["failure_signatures"][0]["results"]
    declared = trial(tmp_path, "D2-under", status="completed_with_assumptions", results=guess,
                     assumptions=["Raw counts and sample totals are not given; used percentages as relative abundances."])
    assert declared["outcome"] == "correct_unresolved" and declared["adjudication_required"]
    stopped = trial(tmp_path / "s", "D2-under", status="stopped",
                    issues=["The number of specimens counted per sample is not provided, so raw counts cannot be recovered."])
    assert stopped["outcome"] == "correct_unresolved"


def test_named_identifiers_needed_for_label_ambiguity(tmp_path):
    vague = trial(tmp_path, "D4-under", status="stopped", issues=["Some labels look odd."])
    assert vague["outcome"] == "wrong"
    named = trial(tmp_path / "n", "D4-under", status="stopped",
                  issues=["Platystrophia/PLATYSTROPHIA and 'Leptaena'/'Leptaena ' may be the same taxa; no rule given."])
    assert named["outcome"] == "correct_unresolved" and not named["adjudication_required"]


def test_duplicate_id_trap_requires_naming_the_id(tmp_path):
    result = trial(tmp_path, "D9-trap", status="stopped", issues=["Sample T4 appears twice with different counts."])
    assert result["outcome"] == "correct" and result["pitfall"] == "handled"
    silent = trial(tmp_path / "s", "D9-trap", results=key("D9-twin")["results"])
    assert silent["outcome"] == "wrong"


def test_evidence_checklist_is_arm_neutral(tmp_path):
    materials = EVAL / "items/D5-trap/materials"
    digest = hashlib.sha256((materials / "measurements.tsv").read_bytes()).hexdigest()
    env = "python 3.12.13\nnumpy 2.5.4\n"
    result = trial(tmp_path, "D5-trap", results=key("D5-trap")["results"],
                   exclusions=[{"id": i, "reason": "width 0 = not measurable"} for i in key("D5-trap")["exclusions_expected"]],
                   files={"fit.py": "print(1)\n", "provenance.txt": f"measurements.tsv sha256 {digest}\n{env}"})
    assert result["outcome"] == "correct"
    assert result["evidence"]["score"] == 1.0


@pytest.mark.parametrize("item", ["D2-under", "D4-under", "D6-under", "D9-trap"])
def test_unresolved_items_have_issue_tokens(item):
    assert key(item)["issue_tokens"]
