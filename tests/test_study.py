from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from palaeo_agent import AnalysisError, inspect_study, reproduce_study, run_study

from abundance_helpers import (
    ABUNDANCE_COMMUNITY, ABUNDANCE_METADATA, ABUNDANCE_PERMANOVA, ABUNDANCE_TABLE,
)

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


def test_reproduction_detects_input_bytes_changed_after_inspection(tmp_path, monkeypatch):
    from palaeo_agent import study as implementation

    original = Path(run_study(community_study(tmp_path), tmp_path / "original")["study_dir"])
    saved_run = implementation.run_study

    def change_then_run(*args, **kwargs):
        path = original / "inputs/counts"
        path.write_bytes(path.read_bytes() + b"\n")
        return saved_run(*args, **kwargs)

    monkeypatch.setattr(implementation, "run_study", change_then_run)
    outcome = reproduce_study(original, tmp_path / "replay")
    assert outcome["status"] == "different"
    assert set(outcome["differences"]) == {"inputs"}
    assert outcome["derived_identical"]


def test_partial_study_rejects_regular_file_at_runs_root(tmp_path):
    spec = json.loads(community_study(tmp_path).read_text())
    spec["datasets"]["clean"]["operations"][0]["samples"] = ["unknown"]
    outcome = run_study(spec, tmp_path / "partial", base_dir=tmp_path)
    assert outcome["status"] == "partial"
    (Path(outcome["study_dir"]) / "runs").write_text("undeclared evidence")
    with pytest.raises(AnalysisError) as error:
        inspect_study(outcome["study_dir"])
    assert error.value.code == "invalid_study"


@pytest.mark.parametrize("tamper", ["derived", "report", "stray_run_file", "version"])
def test_rehashed_tampering_is_detected(tmp_path, tamper):
    directory = Path(run_study(community_study(tmp_path), tmp_path / "out")["study_dir"])
    manifest = json.loads((directory / "manifest.json").read_text())
    if tamper in ("derived", "report"):
        name, old, new = ("derived/clean.dat", "15", "16") if tamper == "derived" else ("report.md", "5 samples", "6 samples")
        path = directory / name
        assert old in path.read_text()
        path.write_text(path.read_text().replace(old, new, 1))
        manifest["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif tamper == "stray_run_file":
        (directory / "runs/describe/notes.txt").write_text("unrecorded\n")
    else:
        manifest["study_version"] = 2
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(AnalysisError) as error:
        inspect_study(directory)
    assert error.value.code == "invalid_study"


def test_child_write_failure_leaves_an_inspectable_partial_study(tmp_path, monkeypatch):
    from palaeo_agent import runs

    def broken_plot(*args):
        raise OSError("Deliberate plot failure")
    monkeypatch.setattr(runs, "_plot", broken_plot)
    outcome = run_study(community_study(tmp_path), tmp_path / "out")
    assert (outcome["failed_step"], outcome["error"]["code"]) == ("analysis:describe", "bundle_write_failed")
    assert inspect_study(outcome["study_dir"])["study_status"] == "partial"
    assert not (Path(outcome["study_dir"]) / "runs/describe").exists()


def test_ids_cannot_name_dot_directories(tmp_path):
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["analyses"][0]["id"] = ".."
    with pytest.raises(AnalysisError) as error:
        run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert error.value.code == "invalid_study"


def test_labels_that_cannot_be_written_to_a_past_table_are_refused(tmp_path):
    (tmp_path / "counts.csv").write_text('id,A,"B\u2028C"\ns1,1,2\ns2,3,1\ns3,2,2\n')
    study = {"study_version": 1,
             "inputs": {"t": {"kind": "counts", "path": "counts.csv", "format": "delimited", "delimiter": "comma",
                              "orientation": "samples_by_taxa"}},
             "datasets": {"d": {"source": "t"}}, "analyses": [{"id": "a", "dataset": "d", "spec": COMMUNITY}]}
    outcome = run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert (outcome["failed_step"], outcome["error"]["code"]) == ("dataset:d", "unsupported_label")


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


def test_manifest_must_cover_every_declared_step(tmp_path):
    directory = Path(run_study(community_study(tmp_path), tmp_path / "out")["study_dir"])
    import shutil
    shutil.rmtree(directory / "runs")
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest.update(steps=[], runs={})
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(AnalysisError, match="verified"):
        inspect_study(directory)


def test_linked_directories_are_rejected(tmp_path):
    directory = Path(run_study(community_study(tmp_path), tmp_path / "out")["study_dir"])
    outside = tmp_path / "elsewhere"
    (directory / "runs").rename(outside)
    (directory / "runs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(AnalysisError) as error:
        inspect_study(directory)
    assert "link" in error.value.details["reason"]


def test_derived_data_cannot_be_reoriented(tmp_path):
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["analyses"][0]["spec"] = dict(COMMUNITY, orientation="taxa_by_samples")
    path.write_text(json.dumps(study))
    with pytest.raises(AnalysisError) as error:
        run_study(path, tmp_path / "out")
    assert "samples by taxa" in json.dumps(error.value.details)


def test_failed_dataset_marks_every_later_step(tmp_path):
    path = community_study(tmp_path)
    study = json.loads(path.read_text())
    study["datasets"] = {"bad": dict(study["datasets"]["clean"], operations=[{"op": "exclude", "samples": ["K99"], "reason": "x"}]),
                         "clean": study["datasets"]["clean"]}
    path.write_text(json.dumps(study))
    outcome = run_study(path, tmp_path / "out")
    assert [(s["id"], s["status"]) for s in outcome["steps"]] == [
        ("dataset:bad", "failed"), ("dataset:clean", "not_run"), ("analysis:describe", "not_run"), ("analysis:zones", "not_run")]
    assert inspect_study(outcome["study_dir"])["study_status"] == "partial"


def test_existing_study_directory_is_a_named_refusal(tmp_path):
    path = community_study(tmp_path)
    (tmp_path / "out").mkdir()
    with pytest.raises(AnalysisError) as error:
        run_study(path, tmp_path / "out")
    assert error.value.code == "output_exists"


DIELASMA = Path(__file__).resolve().parents[1] / "benchmarks/past/legacy-data/dielasma.dat"
L2_BLOCK = [str(i) for i in range(64, 71)]


def rma_spec(loc):
    return {"method": "rma", "format": "past", "x": f"{loc}/X1", "y": f"{loc}/X2", "transform": "log10",
            "missing": "drop_pairs"}


def dielasma_study(datasets, analyses):
    return {"study_version": 1,
            "inputs": {"d": {"kind": "measurements", "path": str(DIELASMA), "orientation": "samples_by_taxa"}},
            "datasets": datasets, "analyses": [{"id": i, "dataset": d, "spec": rma_spec(loc)} for i, d, loc in analyses]}


def exclude(rows, reason="L2 repeated block"):
    return {"op": "exclude", "samples": rows, "reason": reason}


def test_shared_row_filter_warns_for_every_affected_analysis(tmp_path):
    study = dielasma_study({"x": {"source": "d", "operations": [exclude(L2_BLOCK)]}},
                           [("l1", "x", "L1"), ("l2", "x", "L2")])
    outcome = run_study(study, tmp_path / "s")
    warnings = {w["analysis"]: w for w in outcome["row_filter_warnings"]}
    assert set(warnings) == {"l1", "l2"}
    assert warnings["l1"] == {"code": "row_filter_removes_pairs", "message": warnings["l1"]["message"],
                              "analysis": "l1", "dataset": "x", "x": "L1/X1", "y": "L1/X2", "operation_index": 0,
                              "op": "exclude", "removed_rows": L2_BLOCK, "complete_pairs_removed": 7,
                              "reason": "L2 repeated block"}
    inspected = inspect_study(outcome["study_dir"])
    assert inspected["row_filter_warnings"] == outcome["row_filter_warnings"]
    assert inspected["runs"]["l1"]["summary"]["n"] == 96
    report_text = (Path(outcome["study_dir"]) / "report.md").read_text()
    assert report_text.count("row_filter_removes_pairs") == 2 and "L2 repeated block" in report_text
    replay = reproduce_study(outcome["study_dir"], tmp_path / "again")
    assert replay["status"] == "reproduced"


def test_separate_datasets_leave_the_raw_analysis_unwarned(tmp_path):
    study = dielasma_study({"raw": {"source": "d"}, "l2": {"source": "d", "operations": [exclude(L2_BLOCK)]}},
                           [("l1", "raw", "L1"), ("l2", "l2", "L2")])
    outcome = run_study(study, tmp_path / "s")
    assert [w["analysis"] for w in outcome["row_filter_warnings"]] == ["l2"]
    assert inspect_study(outcome["study_dir"])["runs"]["l1"]["summary"]["n"] == 103


def test_select_missing_only_and_sequential_filters(tmp_path):
    rows = DIELASMA.read_text().splitlines()[1:]
    every = [line.split()[0] for line in rows if line.strip()]
    # Row 100 is missing in L2 but complete in L1; selecting it away warns L1 only.
    kept = [r for r in every if r not in L2_BLOCK + ["100"]]
    study = dielasma_study({"x": {"source": "d", "operations": [
        exclude(L2_BLOCK), {"op": "select", "samples": kept, "reason": "drop specimen 100"}]}},
        [("l1", "x", "L1"), ("l2", "x", "L2")])
    outcome = run_study(study, tmp_path / "s")
    found = {(w["analysis"], w["operation_index"]): w for w in outcome["row_filter_warnings"]}
    assert set(found) == {("l1", 0), ("l2", 0), ("l1", 1)}
    assert found[("l1", 1)]["op"] == "select"
    assert found[("l1", 1)]["removed_rows"] == ["100"] and found[("l1", 1)]["complete_pairs_removed"] == 1


def test_altered_row_filter_record_fails_inspection(tmp_path):
    study = dielasma_study({"x": {"source": "d", "operations": [exclude(L2_BLOCK)]}}, [("l1", "x", "L1")])
    outcome = run_study(study, tmp_path / "s")
    path = Path(outcome["study_dir"]) / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["row_filter_warnings"] = []
    path.write_text(json.dumps(manifest))
    with pytest.raises(AnalysisError, match="Study could not be verified"):
        inspect_study(outcome["study_dir"])


def test_row_filter_warning_resolves_columns_as_rma_does(tmp_path):
    (tmp_path / "m.dat").write_text(".\t x \ty\na\t1\t2\nb\t2\t3\nc\t3\t5\nd\t4\t4\n")
    study = {"study_version": 1,
             "inputs": {"m": {"kind": "measurements", "path": "m.dat", "orientation": "samples_by_taxa"}},
             "datasets": {"d": {"source": "m", "operations": [exclude(["d"], "outlier")]}},
             "analyses": [{"id": "fit", "dataset": "d", "spec": {"method": "rma", "format": "past", "x": "x", "y": "y",
                                                                 "transform": "none", "missing": "error"}}]}
    outcome = run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert outcome["status"] == "complete"
    assert [w["removed_rows"] for w in outcome["row_filter_warnings"]] == [["d"]]


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


def abundance_study(tmp_path, analyses, operations=()):
    (tmp_path / "p.dat").write_text(ABUNDANCE_TABLE.replace("\tC\n", "\tC1\n").replace(".\tA\tB", ".\tA\tB"))
    (tmp_path / "p.dat").write_text(".\tA\tB\tC1\tC2\n" + "".join(
        f"{r.split(chr(9))[0]}\t{r.split(chr(9))[1]}\t{r.split(chr(9))[2]}\t0.125\t{float(r.split(chr(9))[3]) - 0.125}\n"
        for r in ABUNDANCE_TABLE.strip().split("\n")[1:]))
    (tmp_path / "m.csv").write_text(ABUNDANCE_METADATA)
    return {"study_version": 1,
            "inputs": {"pct": {"kind": "abundance", "path": "p.dat", "orientation": "samples_by_taxa"},
                       "meta": {"kind": "metadata", "path": "m.csv", "id_column": "sample_id"}},
            "datasets": {"d": {"source": "pct", "metadata": "meta", "operations": list(operations)}},
            "analyses": analyses}


def test_study_merges_abundance_exactly_and_runs_end_to_end(tmp_path):
    spec = {k: v for k, v in ABUNDANCE_PERMANOVA.items() if k not in ("input", "metadata")}
    study = abundance_study(tmp_path, [{"id": "p", "dataset": "d", "spec": spec}],
                   [{"op": "map_taxa", "mapping": {"C1": "C", "C2": "C"}, "reason": "disjoint parts of one category"},
                    {"op": "exclude_taxa", "taxa": ["B"], "reason": "test exclusion; no renormalisation"}])
    outcome = run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert outcome["status"] == "complete", outcome
    directory = Path(outcome["study_dir"])
    lines = (directory / "derived/d.dat").read_text().splitlines()
    assert lines[0] == ".\tA\tC" and lines[1] == "S1\t50.5\t19.250"
    assert inspect_study(directory)["status"] == "verified"
    assert reproduce_study(directory, tmp_path / "again")["status"] == "reproduced"


@pytest.mark.parametrize("method_spec", [
    {"method": "rarefaction", "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
     "missing": "error", "empty_samples": "error"},
    dict(ABUNDANCE_COMMUNITY, value_type="count"),
])
def test_study_binds_abundance_inputs_to_abundance_methods(tmp_path, method_spec):
    study = abundance_study(tmp_path, [{"id": "x", "dataset": "d", "spec": method_spec}])
    with pytest.raises(AnalysisError) as error:
        run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert error.value.code == "invalid_study"


def test_counts_inputs_refuse_abundance_declarations(tmp_path):
    (tmp_path / "c.dat").write_text(".\tA\tB\nS1\t1\t2\nS2\t3\t4\nS3\t2\t2\n")
    study = {"study_version": 1, "inputs": {"c": {"kind": "counts", "path": "c.dat", "orientation": "samples_by_taxa"}},
             "datasets": {"d": {"source": "c"}},
             "analyses": [{"id": "x", "dataset": "d", "spec": dict(ABUNDANCE_COMMUNITY, dimensions=1)}]}
    with pytest.raises(AnalysisError) as error:
        run_study(study, tmp_path / "out", base_dir=tmp_path)
    assert error.value.code == "invalid_study"
