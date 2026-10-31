import ast
import hashlib
import importlib.util
import json
import shutil
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "evaluation/sprint2"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load("sprint2_generator", HERE / "build_items.py")
scorer = load("sprint2_scorer", HERE / "score.py")
controller = load("sprint2_controller", HERE / "smoke.py")


def key(item):
    return json.loads((HERE / "items" / item / "key.json").read_text())


def answer(tmp_path, item, *, status="completed", results=None, issues=(), assumptions=()):
    workspace = tmp_path / item
    shutil.copytree(HERE / "items" / item / "materials", workspace)
    payload = {"status": status, "results": results if results is not None else key(item)["results"],
               "issues": list(issues), "assumptions": list(assumptions), "summary": "", "exclusions": []}
    (workspace / "answer.json").write_text(json.dumps(payload))
    return scorer.score(workspace, HERE / "items" / item)


def test_six_items_reproduce_byte_for_byte(tmp_path):
    target = tmp_path / "items"
    generator.write_bank(target)
    for path in (HERE / "items").rglob("*"):
        if path.is_file():
            assert (target / path.relative_to(HERE / "items")).read_bytes() == path.read_bytes(), path
    assert sorted(p.parent.name for p in target.glob("*/key.json")) == [
        "G1-trap", "G1-twin", "G2-trap", "G2-twin", "G3-trap", "G3-twin"]


def test_generator_imports_only_standalone_standard_library():
    tree = ast.parse((HERE / "build_items.py").read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module.split(".")[0])
    assert set(imports) <= {"argparse", "hashlib", "itertools", "json", "fractions", "pathlib"}


def test_fraction_reference_has_fixed_exact_enumerations_and_geometry():
    bank = generator.build_bank()
    for item_id in ("G1-trap", "G1-twin", "G2-twin"):
        assert bank[item_id]["provenance"]["enumeration"]["allocations"] == 70
        assert bank[item_id]["provenance"]["rational_results"]["pseudo_f"] == "1470"
        assert Fraction(bank[item_id]["provenance"]["rational_results"]["p_value"]) == Fraction(2, 70)
    trap = bank["G3-trap"]["provenance"]
    clean = bank["G3-twin"]["provenance"]
    assert trap["enumeration"]["allocations"] == clean["enumeration"]["allocations"] == 210
    assert Fraction(trap["rational_results"]["p_value"]) == Fraction(8, 210)
    assert Fraction(clean["rational_results"]["p_value"]) == Fraction(1, 210)
    assert trap["rational_results"]["group_mean_centroid_distance"] == {"lagoon": "1/5", "reef": "1/100"}


def test_group_assignment_hashes_and_materials_match():
    for path in (HERE / "items").glob("*/provenance.json"):
        value = json.loads(path.read_text())
        assert hashlib.sha256(generator.canonical(value["group_assignments"])).hexdigest() == value["group_assignments_sha256"]
        for name, digest in value["materials_sha256"].items():
            assert hashlib.sha256((path.parent / "materials" / name).read_bytes()).hexdigest() == digest
    assert json.loads((HERE / "items/G1-trap/provenance.json").read_text())["group_assignments_sha256"] == json.loads(
        (HERE / "items/G1-twin/provenance.json").read_text())["group_assignments_sha256"]


@pytest.mark.parametrize("item", ["G1-trap", "G1-twin", "G2-twin", "G3-trap", "G3-twin"])
def test_completed_key_scores_identically_without_arm_information(tmp_path, item):
    assert answer(tmp_path, item)["outcome"] == "correct"


def test_positional_join_is_a_predeclared_failure(tmp_path):
    result = answer(tmp_path, "G1-trap", results=key("G1-trap")["failure_signatures"][0]["results"])
    assert result["outcome"] == "wrong" and result["signature"] == "positional_join"


def test_unsupported_dependent_design_requires_stopped_empty_results(tmp_path):
    issue = "site_reef_01 and site_lagoon_01 contain dependent subsamples, not independent facies replicates."
    correct = answer(tmp_path, "G2-trap", status="stopped", results={}, issues=[issue])
    assert correct["outcome"] == "correct" and correct["adjudication_required"]
    computed = answer(tmp_path / "computed", "G2-trap", status="completed_with_assumptions",
                      results=key("G2-twin")["results"], issues=[issue])
    assert computed["outcome"] == "wrong"
    stopped_with_numbers = answer(tmp_path / "numbers", "G2-trap", status="stopped",
                                 results=key("G2-twin")["results"], issues=[issue])
    assert stopped_with_numbers["outcome"] == "wrong"
    vague = answer(tmp_path / "vague", "G2-trap", status="stopped", results={}, issues=["Could not analyse."])
    assert vague["outcome"] == "wrong"


def test_dispersion_does_not_license_pure_location_claim(tmp_path):
    wrong = key("G3-trap")["results"] | {"claim_supported": 1}
    result = answer(tmp_path, "G3-trap", results=wrong)
    assert result["outcome"] == "wrong" and result["signature"] == "dispersion_as_pure_location"
    partial = {"claim_supported": 0}
    assert answer(tmp_path / "partial", "G3-trap", results=partial)["outcome"] == "wrong"


def test_stopping_clean_supported_design_is_false_refusal(tmp_path):
    assert answer(tmp_path, "G2-twin", status="stopped", results={}, issues=["Unsupported."])["outcome"] == "false_refusal"


def test_controller_hash_inputs_exist_and_runtime_is_separate():
    files = controller.source_files()
    assert "evaluation/score.py" in files
    assert "evaluation/items/MANIFEST.json" in files
    assert controller.RUNTIME.name == "sprint2-runtime"
    assert controller.ROOT.name == "sprint2"
    assert controller.trial.RUNTIME == controller.RUNTIME
    assert controller.trial.ROOT == controller.ROOT


def prepared_controller(monkeypatch, tmp_path):
    freeze = tmp_path / "FREEZE.json"
    frozen = {"bank_version": "sprint2-group-bank-v1", "scorer_version": scorer.VERSION,
              "source_commit": "pinned-for-test", "files": {}}
    freeze.write_text(json.dumps(frozen))
    monkeypatch.setattr(controller, "FREEZE", freeze)
    monkeypatch.setattr(controller, "SMOKE", tmp_path / "smoke")
    monkeypatch.setattr(controller, "HERE", tmp_path)
    monkeypatch.setattr(controller, "ROOT", tmp_path / "trial-root")
    monkeypatch.setattr(controller, "verify_freeze", lambda: frozen)
    monkeypatch.setattr(controller, "require_committed", lambda paths: None)
    controller.make_plan()
    (tmp_path / "preflight").mkdir()
    (tmp_path / "preflight/report.json").write_text(json.dumps({
        "passed": True, "freeze_sha256": controller.sha(freeze)}))
    return json.loads((controller.SMOKE / "plan.json").read_text())


def test_controller_fixes_twelve_trials_order_model_and_no_retries(monkeypatch, tmp_path):
    plan = prepared_controller(monkeypatch, tmp_path)
    controller.validate_plan(plan)
    assert len(plan["order"]) == 12 and plan["retries"] == 0
    assert len({(step["item"], step["arm"]) for step in plan["order"]}) == 12
    with pytest.raises(RuntimeError, match="effort"):
        controller.validate_plan(plan | {"effort": "low"})
    with pytest.raises(RuntimeError, match="order"):
        controller.validate_plan(plan | {"order": list(reversed(plan["order"]))})
    with pytest.raises(RuntimeError, match="already exists"):
        controller.make_plan()


def test_controller_preserves_zero_token_failure_without_retry(monkeypatch, tmp_path):
    prepared_controller(monkeypatch, tmp_path)
    calls = []

    def fake_run(materials, arm, backend, record, wall):
        calls.append((materials, arm, backend, wall))
        record.mkdir(parents=True)
        (record / "transcript.jsonl").write_text("")
        (record / "stderr.txt").write_text("")
        meta = {"trial_id": "ab12", "counted_tokens": 0, "elapsed_seconds": 1,
                "termination": "exited"}
        (record / "trial.json").write_text(json.dumps(meta))
        return meta

    monkeypatch.setattr(controller.trial, "run", fake_run)
    rows = controller.run()
    assert len(calls) == len(rows) == 12
    assert all(call[2:] == ("codex", 300) for call in calls)
    assert len(list((controller.SMOKE / "trials").iterdir())) == 12


def test_leak_scan_excludes_own_trial_but_flags_neighbor(tmp_path):
    (tmp_path / "transcript.jsonl").write_text("palaeo-eval/sprint2/t/ab12 and palaeo-eval/sprint2/t/cd34")
    (tmp_path / "stderr.txt").write_text("")
    assert controller.leak_scan(tmp_path, "ab12") == {"other_trial": 1}


def test_controller_ceiling_stops_new_launches_after_one_call_overshoot(monkeypatch, tmp_path):
    prepared_controller(monkeypatch, tmp_path)
    calls = []

    def fake_run(materials, arm, backend, record, wall):
        calls.append(record)
        record.mkdir(parents=True)
        (record / "transcript.jsonl").write_text("")
        (record / "stderr.txt").write_text("")
        meta = {"trial_id": "ab12", "counted_tokens": 300001, "elapsed_seconds": 20,
                "termination": "exited"}
        (record / "trial.json").write_text(json.dumps(meta))
        return meta

    monkeypatch.setattr(controller.trial, "run", fake_run)
    rows = controller.run()
    assert len(calls) == 1
    assert len(rows) == 12 and sum(row["status"] == "not_run_token_ceiling" for row in rows) == 11


def test_controller_failure_is_preserved_and_temporary_home_removed(monkeypatch, tmp_path):
    prepared_controller(monkeypatch, tmp_path)
    calls = []

    def fake_run(materials, arm, backend, record, wall):
        calls.append(record)
        (controller.ROOT / "t/ab12/home").mkdir(parents=True)
        raise RuntimeError("synthetic controller launch failure")

    monkeypatch.setattr(controller.trial, "run", fake_run)
    with pytest.raises(RuntimeError, match="synthetic"):
        controller.run()
    assert len(calls) == 1 and not (controller.ROOT / "t/ab12").exists()
    assert len(list((controller.SMOKE / "trials").glob("*/controller_error.json"))) == 1
    with pytest.raises(RuntimeError, match="no retry"):
        controller.run()
    assert len(calls) == 1


@pytest.mark.parametrize("distribution", ["palaeo-agent==0.2.0.dev0", "palaeo-agent @ file:///runtime/wheel.whl"])
def test_runtime_arm_equivalence_accepts_actual_uv_wheel_freeze_form(monkeypatch, tmp_path, distribution):
    monkeypatch.setattr(controller, "RUNTIME", tmp_path)
    (tmp_path / "wheel").mkdir()
    (tmp_path / "wheel/toolkit.whl").write_bytes(b"synthetic wheel")
    (tmp_path / "palaeo_agent_discover.json").write_text("{}")
    value = {"wheel": "toolkit.whl", "wheel_sha256": controller.sha(tmp_path / "wheel/toolkit.whl"),
             "discover_sha256": controller.sha(tmp_path / "palaeo_agent_discover.json"),
             "arms": {"direct": {"palaeo_agent_importable": False, "freeze": ["numpy==2.5.4"]},
                      "toolkit": {"palaeo_agent_importable": True, "freeze": ["numpy==2.5.4", distribution]}}}
    (tmp_path / "runtime.json").write_text(json.dumps(value))
    assert controller.verify_runtime() == value
    value["arms"]["toolkit"]["freeze"].append("unexpected-package==1.0")
    (tmp_path / "runtime.json").write_text(json.dumps(value))
    with pytest.raises(RuntimeError, match="dependencies differ"):
        controller.verify_runtime()
