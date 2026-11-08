import json
from pathlib import Path

import pytest

from palaeo_agent import AnalysisError, inspect_run, inspect_study, reproduce_study, run, run_study, validate
from palaeo_agent.count_homogeneity import _holm, calculate_count_homogeneity
from test_study import COMMUNITY, community_study


def _add_operation(path, operation):
    study = json.loads(path.read_text())
    study["datasets"]["clean"]["operations"].append(operation)
    path.write_text(json.dumps(study))
    return path


def test_exclude_taxa_preserves_order_samples_and_cells(tmp_path):
    path = _add_operation(community_study(tmp_path), {"op": "exclude_taxa", "taxa": ["Orbulina"], "reason": "test sum"})
    outcome = run_study(path, tmp_path / "out")
    assert outcome["status"] == "complete"
    directory = Path(outcome["study_dir"])
    derived = (directory / "derived/clean.dat").read_text().splitlines()
    assert derived[0] == ".\tGlobigerina\tUvigerina"
    assert derived[1:] == ["K1\t15\t5", "K2\t10\t5", "K3\t3\t6", "K4\t3\t9", "K6\t6\t3"]
    record = next(op for op in json.loads((directory / "derived/clean.json").read_text())["operations"]
                  if op["op"] == "exclude_taxa")
    assert record == {"op": "exclude_taxa", "reason": "test sum", "removed": ["Orbulina"],
                      "columns": ["Globigerina", "Uvigerina"], "emptied_samples": []}
    assert "exclude_taxa: removed Orbulina" in (directory / "report.md").read_text()
    assert inspect_study(directory)["status"] == "verified"
    assert reproduce_study(directory, tmp_path / "again")["status"] == "reproduced"


@pytest.mark.parametrize("taxa, code", [
    (["Bolivina"], "unknown_taxon"),
    (["Orbulina", "Orbulina"], "duplicate_id"),
    (["Globigerina", "Orbulina", "Uvigerina"], "no_taxa"),
    (["globigerina"], "unknown_taxon"),  # already merged by the earlier map_taxa step
])
def test_exclude_taxa_refusals(tmp_path, taxa, code):
    path = _add_operation(community_study(tmp_path), {"op": "exclude_taxa", "taxa": taxa, "reason": "x"})
    outcome = run_study(path, tmp_path / "out")
    assert outcome["failed_step"] == "dataset:clean" and outcome["error"]["code"] == code


def test_exclude_taxa_refused_for_measurements(tmp_path):
    (tmp_path / "m.dat").write_text(".\ta\tb\tc\nS1\t1\t2\t1\nS2\t2\t3\t1\nS3\t3\t5\t1\n")
    study = {"study_version": 1,
             "inputs": {"m": {"kind": "measurements", "path": "m.dat", "orientation": "samples_by_taxa"}},
             "datasets": {"d": {"source": "m", "operations": [{"op": "exclude_taxa", "taxa": ["c"], "reason": "x"}]}},
             "analyses": [{"id": "r", "dataset": "d", "spec": {"method": "rma", "format": "past", "x": "a", "y": "b",
                                                              "transform": "none", "missing": "error"}}]}
    assert run_study(study, tmp_path / "out", base_dir=tmp_path)["error"]["code"] == "operation_not_applicable"


@pytest.mark.parametrize("policy", ["error", "drop"])
def test_emptied_samples_follow_the_declared_policy(tmp_path, policy):
    (tmp_path / "c.dat").write_text(".\taquatic\tA\tB\nS1\t9\t0\t0\nS2\t1\t4\t5\nS3\t2\t6\t1\nS4\t0\t3\t3\n")
    study = {"study_version": 1,
             "inputs": {"c": {"kind": "counts", "path": "c.dat", "orientation": "samples_by_taxa"}},
             "datasets": {"d": {"source": "c", "operations": [
                 {"op": "exclude_taxa", "taxa": ["aquatic"], "reason": "dryland sum"}]}},
             "analyses": [{"id": "a", "dataset": "d", "spec": dict(COMMUNITY, empty_samples=policy)}]}
    outcome = run_study(study, tmp_path / "out", base_dir=tmp_path)
    record = json.loads((Path(outcome["study_dir"]) / "derived/d.json").read_text())["operations"][-1]
    assert record["emptied_samples"] == ["S1"]
    if policy == "error":
        assert outcome["status"] == "partial" and outcome["failed_step"] == "analysis:a"
    else:
        assert outcome["status"] == "complete"
        result = json.loads(next((Path(outcome["study_dir"]) / "runs/a").rglob("results.json")).read_text())
        assert [item["sample_id"] for item in result["excluded"]] == ["S1"]


TABLE = ".\tA\tB\tC\tD\nS1\t30\t5\t2\t0\nS2\t28\t9\t1\t3\nS3\t10\t20\t5\t1\nS4\t12\t18\t6\t2\nS5\t25\t6\t3\t0\n"
BASE = {"method": "count_homogeneity", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
        "missing": "error", "empty_samples": "error", "simulations": 999, "seed": 3}


def _spec(tmp_path, **changes):
    (tmp_path / "t.dat").write_text(TABLE)
    return dict(BASE, input=str(tmp_path / "t.dat"), **changes)


def test_holm_envelope_matches_holm_of_interval_bounds(tmp_path):
    result = calculate_count_homogeneity(_spec(tmp_path, pairs="adjacent", extra_pairs=[["S1", "S5"]]),
                                         (tmp_path / "t.dat").read_bytes())
    assert result["method_version"] == 3
    intervals = [p["monte_carlo"]["tail_probability_interval"] for p in result["pairs"]]
    lower, upper = _holm([i[0] for i in intervals]), _holm([i[1] for i in intervals])
    for pair, lo, hi in zip(result["pairs"], lower, upper):
        mc = pair["monte_carlo"]
        assert mc["holm_envelope"] == [lo, hi]
        assert mc["holm_envelope_unresolved"] == (lo <= 0.05 <= hi)
        assert mc["holm_envelope_scope"] == "sensitivity_diagnostic"
        assert lo <= hi


def test_tampered_envelope_fails_inspection(tmp_path):
    outcome = run(_spec(tmp_path, pairs="adjacent"), tmp_path / "run")
    results = Path(outcome["run_dir"]) / "results.json"
    data = json.loads(results.read_text())
    data["pairs"][0]["monte_carlo"]["holm_envelope_unresolved"] ^= True
    results.write_text(json.dumps(data))
    with pytest.raises(Exception):
        inspect_run(outcome["run_dir"])


def test_adjacent_pairs_equal_the_explicit_list(tmp_path):
    explicit = [["S1", "S2"], ["S2", "S3"], ["S3", "S4"], ["S4", "S5"], ["S1", "S5"]]
    _spec(tmp_path)
    data = (tmp_path / "t.dat").read_bytes()
    short = calculate_count_homogeneity(_spec(tmp_path, pairs="adjacent", extra_pairs=[["S1", "S5"]]), data)
    full = calculate_count_homogeneity(_spec(tmp_path, pairs=explicit), data)
    assert short["pair_declaration"] == {"mode": "adjacent", "n_adjacent": 4, "n_extra": 1}
    assert full["pair_declaration"] == {"mode": "explicit", "n_adjacent": 0, "n_extra": 5}
    assert {k: v for k, v in short.items() if k != "pair_declaration"} == \
        {k: v for k, v in full.items() if k != "pair_declaration"}


def test_adjacent_pairs_follow_retained_order_after_drop(tmp_path):
    (tmp_path / "t.dat").write_text(TABLE.replace("S3\t10\t20\t5\t1", "S3\t0\t0\t0\t0"))
    spec = dict(BASE, input=str(tmp_path / "t.dat"), pairs="adjacent", empty_samples="drop")
    result = calculate_count_homogeneity(spec, (tmp_path / "t.dat").read_bytes())
    assert [p["sample_ids"] for p in result["pairs"]] == [["S1", "S2"], ["S2", "S4"], ["S4", "S5"]]
    assert validate(spec)["n_pairs"] == 3


@pytest.mark.parametrize("extra", [[["S2", "S1"]], [["S3", "S4"]]])
def test_extra_pair_repeating_an_adjacent_pair_is_refused(tmp_path, extra):
    with pytest.raises(AnalysisError) as error:
        calculate_count_homogeneity(_spec(tmp_path, pairs="adjacent", extra_pairs=extra), (tmp_path / "t.dat").read_bytes())
    assert error.value.code == "duplicate_pair"


def test_extra_pairs_require_adjacent_mode(tmp_path):
    with pytest.raises(Exception):
        calculate_count_homogeneity(_spec(tmp_path, pairs=[["S1", "S2"]], extra_pairs=[["S1", "S3"]]),
                                    (tmp_path / "t.dat").read_bytes())


def test_adjacent_run_inspects_and_saves_resolved_pairs(tmp_path):
    outcome = run(_spec(tmp_path, pairs="adjacent", extra_pairs=[["S1", "S5"]]), tmp_path / "run")
    inspected = inspect_run(outcome["run_dir"])
    assert inspected["status"] == "verified"
    assert [p["sample_ids"] for p in inspected["result"]["pairs"]][-1] == ["S1", "S5"]
    assert "holm_envelope_lower" in (Path(outcome["run_dir"]) / "count_homogeneity.csv").read_text()


def _rehash(run_dir, name):
    import hashlib
    manifest_path = Path(run_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    data = (Path(run_dir) / name).read_bytes()
    manifest["files"][name].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest_path.write_text(json.dumps(manifest, indent=2))


@pytest.mark.parametrize("declared, forged", [
    ("adjacent", {"mode": "explicit", "n_adjacent": 0, "n_extra": 2}),
    ([["S1", "S2"], ["S2", "S3"]], {"mode": "adjacent", "n_adjacent": 2, "n_extra": 0}),
])
def test_inspection_binds_pair_declaration_to_the_specification(tmp_path, declared, forged):
    (tmp_path / "t.dat").write_text(".\tA\tB\nS1\t10\t5\nS2\t8\t7\nS3\t2\t12\n")
    spec = dict(BASE, input=str(tmp_path / "t.dat"), pairs=declared, seed=5)
    outcome = run(spec, tmp_path / "run")
    assert inspect_run(outcome["run_dir"])["status"] == "verified"
    results = Path(outcome["run_dir"]) / "results.json"
    data = json.loads(results.read_text())
    data["pair_declaration"] = forged
    results.write_text(json.dumps(data, indent=2))
    _rehash(outcome["run_dir"], "results.json")
    with pytest.raises(Exception):
        inspect_run(outcome["run_dir"])


def test_discovery_version_matches_schema_and_results(tmp_path):
    from palaeo_agent import discover
    from palaeo_agent.count_homogeneity import CountHomogeneityResult
    entry = next(m for m in discover()["methods"] if m["id"] == "count_homogeneity") if isinstance(discover(), dict) \
        else next(m for m in discover() if m["id"] == "count_homogeneity")
    schema = CountHomogeneityResult.model_json_schema()["properties"]["method_version"]
    result = calculate_count_homogeneity(_spec(tmp_path, pairs="adjacent"), (tmp_path / "t.dat").read_bytes())
    assert entry["version"] == schema["const"] == result["method_version"] == 3
