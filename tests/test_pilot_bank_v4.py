"""Pilot bank v4: deterministic, unsignposted, matched, and scored as its keys say."""

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "evaluation/pilot"
sys.path.insert(0, str(PILOT))
sys.path.insert(0, str(ROOT))
import build_bank_v4 as bank  # noqa: E402
from evaluation.pilot.replay import perturb  # noqa: E402
from evaluation.pilot.score import score  # noqa: E402

ITEMS, CAL = PILOT / "items-v4", PILOT / "calibration-v4"
KEYS = sorted(ITEMS.glob("*/key.json")) + sorted(CAL.glob("*/key.json"))


def test_rebuild_is_identical(tmp_path):
    bank.build(tmp_path)
    for name in ("items-v4", "calibration-v4"):
        assert (tmp_path / name / "MANIFEST.json").read_text() == (PILOT / name / "MANIFEST.json").read_text()


def test_bank_shape():
    keys = [json.loads(p.read_text()) for p in sorted(ITEMS.glob("*/key.json"))]
    assert len(keys) == 24 and {k["family"] for k in keys} == {f"P{i:02d}" for i in range(1, 13)}
    assert {k["stratum"] for k in keys if k["family"] in ("P07", "P08", "P09", "P10", "P11")} == {"other"}
    assert len(list(CAL.glob("*/key.json"))) == 8


@pytest.mark.parametrize("family", [f"P{i:02d}" for i in range(1, 13)])
def test_trap_and_control_share_task_dictionary_and_files(family):
    trap, control = ITEMS / f"{family}-trap/materials", ITEMS / f"{family}-control/materials"
    assert sorted(p.name for p in trap.iterdir()) == sorted(p.name for p in control.iterdir())
    for name in ("task.md", "dictionary.md"):
        assert (trap / name).read_text() == (control / name).read_text()


def answer(results):
    return {"status": "completed", "results": results, "assumptions": [], "exclusions": [], "issues": [],
            "summary": "s"}


@pytest.mark.parametrize("path", KEYS, ids=lambda p: f"{p.parent.parent.name}/{p.parent.name}")
def test_keys_score_and_signatures_fail(path, tmp_path):
    key = json.loads(path.read_text())
    item = path.parent
    (tmp_path / "answer.json").write_text(json.dumps(answer(key["results"])))
    out = score(tmp_path, item)
    assert out["outcome"] in ("correct", "undisclosed") and (out["outcome"] == "correct") != bool(key["disclosure_tokens"])
    for failure in key["failure_signatures"]:
        (tmp_path / "answer.json").write_text(json.dumps(answer(failure["results"])))
        assert score(tmp_path, item)["outcome"] == "wrong", failure["name"]
    for alternative in key["alternative_results"]:
        (tmp_path / "answer.json").write_text(json.dumps(answer(alternative["results"])))
        out = score(tmp_path, item)
        assert out["outcome"] == "correct" and out["alternative"] == alternative["name"] and not out["provisional"]


@pytest.mark.parametrize("path", KEYS, ids=lambda p: f"{p.parent.parent.name}/{p.parent.name}")
def test_perturbation_applies_to_a_material_file(path, tmp_path):
    key = json.loads(path.read_text())
    source = path.parent / "materials" / key["replay_perturbation"]["file"]
    target = tmp_path / source.name
    target.write_text(source.read_text())
    perturb(target, key["replay_perturbation"])
    assert target.read_text() != source.read_text()


@pytest.mark.parametrize("item", ["items-v4/P04-trap", "calibration-v4/P04-cal"])
def test_p04_accepts_justified_stop_and_identified_partial(item, tmp_path):
    key = json.loads((PILOT / item / "key.json").read_text())
    partial = key["acceptable_alternatives"][0]["partial_results"]
    reason = "The 2017 63-150 µm residues were archived, not picked, so the 2017 >63 µm assemblage is unobserved."
    for status, results in (("stopped", {}), ("completed_with_assumptions", partial)):
        (tmp_path / "answer.json").write_text(json.dumps(dict(answer(results), status=status, issues=[reason],
                                                             assumptions=[reason] if results else [])))
        assert score(tmp_path, PILOT / item)["outcome"] == "correct_unresolved"
    disclosed = dict(answer(key["results"]), status="completed_with_assumptions",
                     assumptions=["Both campaigns compared on the >150 µm fraction only."])
    (tmp_path / "answer.json").write_text(json.dumps(disclosed))
    assert score(tmp_path, PILOT / item)["outcome"] == "correct"
    (tmp_path / "answer.json").write_text(json.dumps(answer(key["failure_signatures"][0]["results"])))
    assert score(tmp_path, PILOT / item)["outcome"] == "wrong"
