from fractions import Fraction
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from palaeo_agent import AnalysisError, inspect_study, reproduce_study, run_study

COMMUNITY = {"method": "community", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
             "transform": "none", "distance": "braycurtis", "dimensions": 1, "missing": "error",
             "empty_samples": "error"}
PERMANOVA = {"method": "permanova", "group_column": "zone", "format": "past", "orientation": "samples_by_taxa",
             "value_type": "count", "distance": "braycurtis", "transform": "none", "missing": "error",
             "empty_samples": "error", "design": "independent", "permutation_scheme": "free",
             "permutations": 999, "seed": 11}
# Taxa by samples, with two exact labels for one taxon and a sample (K5) to exclude.
COUNTS = """.\tK1\tK2\tK3\tK4\tK5\tK6
Globigerina\t12\t9\t3\t2\t0\t4
globigerina\t3\t1\t0\t1\t0\t2
Orbulina\t1\t4\t10\t7\t0\t9
Uvigerina\t5\t5\t6\t9\t0\t3
"""
METADATA = "core,zone\nK6,B\nK1,A\nK2,A\nK3,B\nK4,B\nK5,A\nK9,A\n"
# The same data prepared by hand: K5 removed, Globigerina = Globigerina + globigerina.
FINAL = {"K1": [15, 1, 5], "K2": [10, 4, 5], "K3": [3, 10, 6], "K4": [3, 7, 9], "K6": [6, 9, 3]}
ZONES = {"K1": "A", "K2": "A", "K3": "B", "K4": "B", "K6": "B"}


def community_study(tmp_path, **changes):
    (tmp_path / "counts.dat").write_text(COUNTS)
    (tmp_path / "cores.csv").write_text(METADATA)
    study = {"study_version": 1,
             "inputs": {"counts": {"kind": "counts", "path": "counts.dat", "orientation": "taxa_by_samples"},
                        "cores": {"kind": "metadata", "path": "cores.csv", "id_column": "core"}},
             "datasets": {"clean": {"source": "counts", "metadata": "cores", "drop_unmatched_metadata": True,
                                    "operations": [
                                        {"op": "exclude", "samples": ["K5"], "reason": "no specimens recovered"},
                                        {"op": "map_taxa", "mapping": {"globigerina": "Globigerina"},
                                         "reason": "case variant of one taxon"}]}},
             "analyses": [{"id": "describe", "dataset": "clean", "spec": COMMUNITY},
                          {"id": "zones", "dataset": "clean", "spec": PERMANOVA}]}
    study.update(changes)
    path = tmp_path / "study.json"
    path.write_text(json.dumps(study))
    return path


def bray(a, b):
    return Fraction(sum(abs(x - y) for x, y in zip(a, b)), sum(a) + sum(b))


def pseudo_f(samples, groups):
    n, labels = len(samples), sorted(set(groups.values()))
    d2 = {(i, j): bray(FINAL[i], FINAL[j]) ** 2 for i, j in combinations(samples, 2)}
    total = sum(d2.values()) / n
    within = sum(sum(v for (i, j), v in d2.items() if groups[i] == groups[j] == g) /
                 sum(1 for s in samples if groups[s] == g) for g in labels)
    return float(((total - within) / (len(labels) - 1)) / (within / (n - len(labels))))


def test_community_recipe_matches_hand_preparation(tmp_path):
    outcome = run_study(community_study(tmp_path), tmp_path / "out")
    assert outcome["status"] == "complete"
    directory = Path(outcome["study_dir"])
    derived = (directory / "derived/clean.dat").read_text().splitlines()
    assert derived[0].split("\t") == [".", "Globigerina", "Orbulina", "Uvigerina"]
    assert {row.split("\t")[0]: list(map(int, row.split("\t")[1:])) for row in derived[1:]} == FINAL
    assert (directory / "derived/clean-metadata.csv").read_text() == "sample_id,zone\nK1,A\nK2,A\nK3,B\nK4,B\nK6,B\n"
    record = json.loads((directory / "derived/clean.json").read_text())
    assert record["operations"][1]["removed"] == ["K5"]
    assert record["operations"][2]["merged"] == {"Globigerina": ["Globigerina", "globigerina"]}
    assert record["operations"][3]["dropped_unmatched"] == ["K5", "K9"]

    verified = inspect_study(directory)
    describe = json.loads((directory / verified["runs"]["describe"]["run_dir"] / "results.json").read_text())
    samples = describe["sample_ids"]
    assert samples == list(FINAL)
    for i, a in enumerate(samples):
        for j, b in enumerate(samples):
            assert describe["distances"][i][j] == pytest.approx(float(bray(FINAL[a], FINAL[b])), abs=1e-15)
    zones = json.loads((directory / verified["runs"]["zones"]["run_dir"] / "results.json").read_text())
    assert zones["pseudo_f"] == pytest.approx(pseudo_f(samples, ZONES), rel=1e-12)
    report = (directory / "report.md").read_text()
    assert "removed K5 — no specimens recovered" in report and "Globigerina ← Globigerina + globigerina" in report
    assert f"`{verified['runs']['zones']['run_dir']}/results.json#pseudo_f`" in report


def test_measurement_recipe_with_declared_exclusion_and_transform(tmp_path):
    (tmp_path / "shells.dat").write_text(".\tlength\twidth\nS1\t10\t4\nS2\t20\t9\nS3\t40\t15\nS4\t0\t2\nS5\t80\t33\n")
    study = {"study_version": 1,
             "inputs": {"shells": {"kind": "measurements", "path": "shells.dat", "orientation": "samples_by_taxa"}},
             "datasets": {"intact": {"source": "shells", "operations": [
                 {"op": "exclude", "samples": ["S4"], "reason": "broken specimen; length not measurable"}]}},
             "analyses": [{"id": "allometry", "dataset": "intact", "spec": {
                 "method": "rma", "format": "past", "x": "length", "y": "width", "transform": "log10",
                 "missing": "error"}}]}
    outcome = run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert outcome["status"] == "complete"
    x = [math.log10(v) for v in (10, 20, 40, 80)]
    y = [math.log10(v) for v in (4, 9, 15, 33)]
    mx, my = sum(x) / 4, sum(y) / 4
    sxx, syy = sum((v - mx) ** 2 for v in x), sum((v - my) ** 2 for v in y)
    slope = math.copysign(math.sqrt(syy / sxx), sum((a - mx) * (b - my) for a, b in zip(x, y)))
    result = inspect_study(outcome["study_dir"])["runs"]["allometry"]["summary"]
    assert result["slope"] == pytest.approx(slope, rel=1e-12)
    assert result["intercept"] == pytest.approx(my - slope * mx, rel=1e-12, abs=1e-12)


def test_reproduce_in_a_fresh_process(tmp_path):
    outcome = run_study(community_study(tmp_path), tmp_path / "out")
    completed = subprocess.run([sys.executable, "-m", "palaeo_agent", "study-reproduce", outcome["study_dir"],
                                "--output", str(tmp_path / "again")], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    reproduced = json.loads(completed.stdout)
    assert reproduced["status"] == "reproduced" and reproduced["derived_identical"]
    assert reproduce_study(outcome["study_dir"], tmp_path / "third")["status"] == "reproduced"


def test_tampering_is_detected(tmp_path):
    directory = Path(run_study(community_study(tmp_path), tmp_path / "out")["study_dir"])
    derived = directory / "derived/clean.dat"
    derived.write_text(derived.read_text().replace("15", "16"))
    with pytest.raises(AnalysisError) as error:
        inspect_study(directory)
    assert error.value.code == "invalid_study"


def test_a_consistent_upstream_change_passes_integrity(tmp_path):
    # Flawed but honest studies are not caught by integrity checks; reviewers must judge declarations.
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["datasets"]["clean"]["operations"][0]["samples"] = ["K3", "K5"]
    path.write_text(json.dumps(study))
    outcome = run_study(path, tmp_path / "out")
    assert inspect_study(outcome["study_dir"])["status"] == "verified"


def test_partial_failure_names_the_step_and_preserves_evidence(tmp_path):
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["datasets"]["clean"]["operations"].insert(0, {"op": "exclude", "samples": ["K3", "K4"], "reason": "test"})
    study["analyses"].append({"id": "after", "dataset": "clean", "spec": COMMUNITY})
    path.write_text(json.dumps(study))
    outcome = run_study(path, tmp_path / "out")
    assert outcome["status"] == "partial" and outcome["failed_step"] == "analysis:zones"
    assert outcome["error"]["code"] == "small_groups"
    verified = inspect_study(outcome["study_dir"])
    assert verified["study_status"] == "partial" and set(verified["runs"]) == {"describe"}
    assert [step["status"] for step in verified["steps"]] == ["complete", "complete", "failed", "not_run"]
    assert "**analysis:zones: failed**" in (Path(outcome["study_dir"]) / "report.md").read_text()


@pytest.mark.parametrize("operation, code", [
    ({"op": "exclude", "samples": ["K7"], "reason": "x"}, "unknown_sample"),
    ({"op": "map_taxa", "mapping": {"Bolivina": "X"}, "reason": "x"}, "unknown_taxon"),
    ({"op": "select", "samples": ["K1", "K1"], "reason": "x"}, "duplicate_id"),
])
def test_invalid_operations_stop_before_analysis(tmp_path, operation, code):
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["datasets"]["clean"]["operations"].append(operation)
    path.write_text(json.dumps(study))
    outcome = run_study(path, tmp_path / "out")
    assert outcome["failed_step"] == "dataset:clean" and outcome["error"]["code"] == code
    assert [step["status"] for step in outcome["steps"]] == ["failed", "not_run", "not_run"]


def test_missing_cells_are_never_merged(tmp_path):
    path = community_study(tmp_path)
    (tmp_path / "counts.dat").write_text(COUNTS.replace("globigerina\t3", "globigerina\t."))
    outcome = run_study(path, tmp_path / "out")
    assert outcome["error"]["code"] == "missing_counts"


def test_unmatched_metadata_requires_a_declaration(tmp_path):
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["datasets"]["clean"]["drop_unmatched_metadata"] = False
    path.write_text(json.dumps(study))
    outcome = run_study(path, tmp_path / "out")
    assert outcome["error"]["code"] == "metadata_alignment"
    assert outcome["error"]["details"]["unmatched"] == ["K5", "K9"]


def test_taxon_mapping_refused_for_measurements(tmp_path):
    (tmp_path / "m.dat").write_text(".\ta\tb\nS1\t1\t2\nS2\t2\t3\nS3\t3\t5\n")
    study = {"study_version": 1,
             "inputs": {"m": {"kind": "measurements", "path": "m.dat", "orientation": "samples_by_taxa"}},
             "datasets": {"d": {"source": "m", "operations": [{"op": "map_taxa", "mapping": {"a": "b"}, "reason": "x"}]}},
             "analyses": [{"id": "r", "dataset": "d", "spec": {"method": "rma", "format": "past", "x": "a", "y": "b",
                                                              "transform": "none", "missing": "error"}}]}
    assert run_study(study, tmp_path / "out", base_dir=tmp_path)["error"]["code"] == "operation_not_applicable"


def test_study_cannot_override_input_paths(tmp_path):
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["analyses"][0]["spec"] = dict(COMMUNITY, input="/etc/passwd")
    path.write_text(json.dumps(study))
    with pytest.raises(AnalysisError) as error:
        run_study(path, tmp_path / "out")
    assert error.value.code == "invalid_study"
