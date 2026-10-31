import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REVISED = ROOT / "evaluation" / "revised"
sys.path.insert(0, str(ROOT))
from evaluation.revised import VERSION  # noqa: E402
from evaluation.revised import score as revised_score  # noqa: E402


def build(tmp_path):
    output = tmp_path / "items"
    revised_score  # keep module import explicit for test diagnostics
    from evaluation.revised.build_items import build as build_bank
    build_bank(output)
    return output


def answer_workspace(tmp_path, item, answer, files=None):
    materials = build(tmp_path) / item / "materials"
    workspace = tmp_path / f"workspace-{item}"
    shutil.copytree(materials, workspace)
    (workspace / "answer.json").write_text(json.dumps(answer, allow_nan=False))
    for name, content in (files or {}).items():
        (workspace / name).write_text(content)
    return workspace


def valid_answer(**changes):
    answer = {
        "status": "stopped",
        "results": {},
        "assumptions": [],
        "exclusions": [],
        "issues": ["count totals are not supplied"],
        "summary": "stopped because raw totals are unavailable",
    }
    answer.update(changes)
    return answer


def test_revised_bank_is_deterministic_and_keeps_legacy_unchanged(tmp_path):
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT / "evaluation/items").rglob("*") if path.is_file()}
    first = build(tmp_path / "first")
    second = build(tmp_path / "second")
    assert VERSION == "sprint1-revised-v2"
    assert {p.relative_to(first): hashlib.sha256(p.read_bytes()).hexdigest() for p in first.rglob("*") if p.is_file()} == {
        p.relative_to(second): hashlib.sha256(p.read_bytes()).hexdigest() for p in second.rglob("*") if p.is_file()
    }
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT / "evaluation/items").rglob("*") if path.is_file()}
    assert before == after
    manifest = json.loads((first / "MANIFEST.json").read_text())
    assert manifest["version"] == VERSION
    assert manifest["amended_items"] == ["D2-under", "D7-control"]
    assert manifest["source_manifest_sha256"] == hashlib.sha256((ROOT / "evaluation/items/MANIFEST.json").read_bytes()).hexdigest()


def test_builder_refuses_existing_and_source_related_outputs(tmp_path):
    from evaluation.revised.build_items import SOURCE, build as build_bank

    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "sentinel.txt"
    sentinel.write_text("preserve")
    with pytest.raises(FileExistsError):
        build_bank(existing)
    assert sentinel.read_text() == "preserve"
    with pytest.raises(ValueError):
        build_bank(SOURCE / "refuse-descendant")
    with pytest.raises(ValueError):
        build_bank(SOURCE.parent)


def test_d2_integer_percentages_preserve_nonidentifiability(tmp_path):
    bank = build(tmp_path)
    values = (bank / "D2-under/materials/assemblages.tsv").read_text().splitlines()[1:]
    assert all(field.isdigit() for line in values for field in line.split("\t")[1:])
    dictionary = (bank / "D2-under/materials/dictionary.md").read_text()
    assert "integer percentage" in dictionary and "harder uncoached ambiguity" in dictionary


def test_d7_explicitly_defines_invalid_k5_and_retains_key(tmp_path):
    bank = build(tmp_path)
    dictionary = (bank / "D7-control/materials/dictionary.md").read_text()
    task = (bank / "D7-control/materials/task.md").read_text()
    key = json.loads((bank / "D7-control/key.json").read_text())
    assert "failed sampling" in dictionary and "does not establish absence" in dictionary
    assert "valid samples" in task and "must be excluded" in task
    assert key["results"]["n_pairs"] == 10 and key["exclusions_expected"] == ["K5"]
    assert key["item"] == "D7-control" and key["class"] == "twin"
    workspace = answer_workspace(tmp_path / "control", "D7-control", valid_answer(
        status="completed", results={name: str(value) for name, value in key["results"].items()},
        issues=[], exclusions=[{"id": "K5", "reason": "failed sampling"}]))
    result = revised_score.score(workspace, bank / "D7-control")
    assert result["outcome"] == "correct" and "pitfall" not in result


def test_strict_answer_contract_rejects_fabrication_and_nonfinite(tmp_path):
    bank = build(tmp_path)
    item = bank / "D2-under"
    malformed = [
        valid_answer(results={"fabricated": 1}),
        valid_answer(results={"x": float("nan")}),
        {**valid_answer(), "extra": 1},
        {**valid_answer(), "exclusions": [{"id": "K5", "reason": "bad", "extra": 1}]},
        {**valid_answer(), "status": ["stopped"]},
        {**valid_answer(), "summary": 42},
        {**valid_answer(), "results": {"huge": 10**10000}},
    ]
    for index, answer in enumerate(malformed):
        workspace = tmp_path / f"bad-{index}"
        shutil.copytree(item / "materials", workspace)
        path = workspace / "answer.json"
        if index == 1:
            path.write_text('{"status":"stopped","results":{"x":NaN},"assumptions":[],"exclusions":[],"issues":["count"],"summary":""}')
        elif index == 6:
            path.write_text('{"status":"stopped","results":{"huge":' + "1" + "0" * 10000 + '},"assumptions":[],"exclusions":[],"issues":["count"],"summary":""}')
        else:
            path.write_text(json.dumps(answer, allow_nan=True))
        parsed, error = revised_score.load_answer(workspace)
        assert parsed is None and error


def test_unresolved_contract_requires_empty_stops_and_assumptions(tmp_path):
    bank = build(tmp_path)
    item = bank / "D2-under"
    for index, answer in enumerate((
        valid_answer(results={"fabricated": 999}),
        valid_answer(status="completed_with_assumptions", assumptions=[], results={}),
    )):
        workspace = answer_workspace(tmp_path / f"bad-{index}", "D2-under", answer)
        parsed, error = revised_score.load_answer(workspace)
        assert parsed is None and error
    issues_only = valid_answer(status="completed_with_assumptions", results={"fabricated": 999}, assumptions=[], issues=["count"])
    workspace = tmp_path / "issues-only"
    shutil.copytree(item / "materials", workspace)
    (workspace / "answer.json").write_text(json.dumps(issues_only))
    # Empty assumptions is a contract error before issue-only wording can pass.
    assert revised_score.load_answer(workspace)[0] is None


def test_numeric_unresolved_answer_is_provisional_and_requires_adjudication(tmp_path):
    bank = build(tmp_path)
    answer = valid_answer(
        status="completed_with_assumptions",
        results={"illustrative": 1},
        assumptions=["Raw count totals are unavailable; this is an illustrative relative-abundance calculation."],
    )
    workspace = answer_workspace(tmp_path / "answer", "D2-under", answer)
    result = revised_score.score(workspace, bank / "D2-under")
    assert result["outcome"] == "correct_unresolved"
    assert result["provisional"] and result["adjudication_required"]


def test_keyword_unresolved_stop_retains_provisional_adjudication_flag(tmp_path):
    bank = build(tmp_path)
    workspace = answer_workspace(tmp_path / "answer", "D2-under", valid_answer())
    result = revised_score.score(workspace, bank / "D2-under")
    assert result["outcome"] == "correct_unresolved"
    assert result["provisional"] and result["adjudication_required"]


def test_identifier_unresolved_numeric_answer_is_provisional(tmp_path):
    bank = build(tmp_path)
    answer = valid_answer(
        status="completed_with_assumptions",
        results={"illustrative": 1},
        assumptions=["Platystrophia and Leptaena labels may differ by case or whitespace; no merge rule was supplied."],
        issues=[],
    )
    workspace = answer_workspace(tmp_path / "identifier", "D4-under", answer)
    result = revised_score.score(workspace, bank / "D4-under")
    assert result["outcome"] == "correct_unresolved"
    assert result["provisional"] and result["adjudication_required"]


def test_missing_information_in_issues_only_cannot_approve_numeric_answer(tmp_path):
    bank = build(tmp_path)
    answer = valid_answer(
        status="completed_with_assumptions",
        results={"illustrative": 1},
        assumptions=["Used a convenient scaling."],
        issues=["count totals are not supplied"],
    )
    workspace = answer_workspace(tmp_path / "answer", "D2-under", answer)
    result = revised_score.score(workspace, bank / "D2-under")
    assert result["outcome"] == "wrong" and not result["provisional"]


def test_evidence_pairs_paths_and_texts_without_zip_shift(tmp_path):
    bank = build(tmp_path)
    materials = bank / "D5-trap/materials"
    workspace = tmp_path / "evidence"
    shutil.copytree(materials, workspace)
    answer = valid_answer(status="completed", issues=[], summary="done")
    answer["results"] = json.loads((bank / "D5-trap/key.json").read_text())["results"]
    (workspace / "answer.json").write_text(json.dumps(answer))
    digest = hashlib.sha256((materials / "measurements.tsv").read_bytes()).hexdigest()
    (workspace / "000-binary.bin").write_bytes(b"\xff\xfe\x00" * 100)
    (workspace / "001-oversized.bin").write_bytes(b"x" * 5_000_001)
    (workspace / "002-method.json").write_text('{"method":"rma"}\n')
    (workspace / "provenance.txt").write_text(f"measurements.tsv sha256 {digest}\npython 3.12.13\nnumpy 2.5.4\n")
    evidence = revised_score.evidence(workspace, materials, answer, json.loads((bank / "D5-trap/key.json").read_text()))
    assert evidence["checks"]["analysis_code_saved"]
    assert evidence["checks"]["input_hashes_recorded"] and evidence["checks"]["environment_recorded"]


def test_historical_answers_keep_primary_outcomes_under_revised_contract(tmp_path):
    bank = ROOT / "evaluation/items"
    rows = []
    for run in (ROOT / "evaluation/smoke/codex-v1", ROOT / "evaluation/smoke/claude-v1"):
        for trial in sorted((run / "trials").glob("*/trial.json")):
            meta = json.loads(trial.read_text())
            item = bank / Path(meta["materials"]).parent.name
            result = revised_score.score(trial.parent / "workspace", item, meta["termination"])
            rows.append(result["outcome"])
    assert len(rows) == 28
    assert all(outcome in {"correct", "correct_unresolved"} for outcome in rows)


def test_revised_score_cli_refuses_to_overwrite_existing_receipt(tmp_path):
    bank = build(tmp_path)
    destination = tmp_path / "existing-scores.json"
    destination.write_text("preserve this receipt\n")
    result = subprocess.run([sys.executable, "-m", "evaluation.revised.score",
                             str(tmp_path / "no-trials"), str(bank), "--output", str(destination)],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert destination.read_text() == "preserve this receipt\n"
