import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from palaeo_agent import AnalysisError, inspect_run, run
from palaeo_agent.community import selected_subspace_info
from palaeo_agent.sensitivity import (
    _average_ranks, _correlation, _procrustes_m2, _report,
    compare_community_runs, inspect_comparison,
)


def make_pair(tmp_path, **changes):
    source = tmp_path / "counts.dat"
    source.write_text(". t1 t2 t3\na 30 10 0\nb 0 3 1\nc 1 0 3\nd 2 3 1\n")
    spec = {"method": "community", "input": str(source), "format": "past",
            "orientation": "samples_by_taxa", "value_type": "count",
            "transform": "relative_abundance", "distance": "braycurtis",
            "dimensions": 2, "missing": "error", "empty_samples": "error"}
    baseline = Path(run(spec, tmp_path / "runs")["run_dir"])
    spec.update(transform="none", purpose="Effect of unequal totals",
                baseline_run=hashlib.sha256((baseline / "manifest.json").read_bytes()).hexdigest())
    spec.update(changes)
    sensitivity = Path(run(spec, tmp_path / "runs")["run_dir"])
    return source, baseline, sensitivity


def test_self_contained_comparison_and_count_bound(tmp_path):
    source, baseline, sensitivity = make_pair(tmp_path)
    response = compare_community_runs(baseline, sensitivity, tmp_path / "comparisons")
    directory = Path(response["comparison_dir"])
    source.unlink()
    shutil.rmtree(baseline)
    shutil.rmtree(sensitivity)
    checked = inspect_comparison(directory)
    assert checked["status"] == "verified"
    report = checked["report"]
    assert report["baseline_link_verified"] is True
    assert report["numeric_environment"]["numpy"]
    assert report["numeric_environment"]["python"]
    assert report["numeric_environment"]["platform_identical"] is True
    assert report["settings_changed"] == ["transform"]
    assert report["upper_triangle_pairs"] == 6
    assert 0 <= report["symmetric_procrustes_m2"] <= 1
    assert report["maximum_absolute_distance_change"] > 0
    assert report["raw_count_total_imbalance_bound"][0][1] == pytest.approx(36 / 44)
    assert (directory / "raw_count_total_imbalance_bound.csv").is_file()
    assert set(checked["manifest"]["files"]) >= {"baseline/manifest.json", "sensitivity/manifest.json", "report.json"}


@pytest.mark.parametrize("changes,code", [
    ({"dimensions": 1}, "comparison_settings"),
    ({"baseline_run": "0" * 64}, "comparison_baseline"),
    ({"transform": "relative_abundance"}, "comparison_no_change"),
])
def test_invalid_comparisons_fail_before_output_allocation(tmp_path, changes, code):
    _, baseline, sensitivity = make_pair(tmp_path, **changes)
    destination = tmp_path / "comparison"
    with pytest.raises(AnalysisError) as caught:
        compare_community_runs(baseline, sensitivity, destination)
    assert caught.value.code == code
    assert not destination.exists()


def test_changed_input_is_rejected_before_output_allocation(tmp_path):
    source, baseline, _ = make_pair(tmp_path)
    source.write_text(source.read_text().replace("30 10", "31 10"))
    spec = json.loads((baseline / "spec.json").read_text())
    spec.update(input=str(source), transform="none", purpose="Wrong source")
    sensitivity = run(spec, tmp_path / "runs")["run_dir"]
    with pytest.raises(AnalysisError) as caught:
        compare_community_runs(baseline, sensitivity, tmp_path / "comparison")
    assert caught.value.code == "comparison_inputs"
    assert not (tmp_path / "comparison").exists()


@pytest.mark.parametrize("change", ["implementation", "numpy", "python"])
def test_environment_confounds_are_rejected_before_output_allocation(tmp_path, change):
    _, baseline, sensitivity = make_pair(tmp_path)
    path = baseline / "environment.json"
    environment = json.loads(path.read_text())
    if change == "implementation":
        key = next(iter(environment["source_files_sha256"]))
        environment["source_files_sha256"][key] = "0" * 64
        environment["implementation_sha256"] = hashlib.sha256(
            json.dumps(environment["source_files_sha256"], sort_keys=True).encode()
        ).hexdigest()
    elif change == "numpy":
        environment["packages"]["numpy"] = "999.0"
        for distribution in environment["distributions"]:
            if distribution["name"] == "numpy":
                distribution["version"] = "999.0"
    else:
        environment["python"] += " changed"
    path.write_text(json.dumps(environment))
    manifest_path = baseline / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["environment.json"].update(
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size
    )
    manifest_path.write_text(json.dumps(manifest))
    assert inspect_run(baseline)["status"] == "verified"
    assert inspect_run(sensitivity)["status"] == "verified"
    destination = tmp_path / "comparison"
    with pytest.raises(AnalysisError) as caught:
        compare_community_runs(baseline, sensitivity, destination)
    assert caught.value.code == "comparison_environment"
    assert not destination.exists()


@pytest.mark.parametrize("name", ["report.json", "raw_count_total_imbalance_bound.csv"])
def test_tampered_comparison_records_and_symlink_rejected(tmp_path, name):
    _, baseline, sensitivity = make_pair(tmp_path)
    directory = Path(compare_community_runs(baseline, sensitivity, tmp_path / "comparison")["comparison_dir"])
    report_path = directory / name
    if name == "report.json":
        report = json.loads(report_path.read_text())
        report["maximum_absolute_distance_change"] = 999
        report_path.write_text(json.dumps(report))
    else:
        rows = report_path.read_text().splitlines()
        rows[1] = rows[1].rsplit(",", 1)[0] + ",0.5"
        report_path.write_text("\n".join(rows) + "\n")
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][name].update(sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                                   bytes=report_path.stat().st_size)
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(AnalysisError) as caught:
        inspect_comparison(directory)
    assert caught.value.code == "invalid_comparison"
    report_path.unlink()
    report_path.symlink_to(tmp_path / "nonexistent")
    with pytest.raises(AnalysisError):
        inspect_comparison(directory)


def test_rank_ties_constant_vectors_and_rotation_invariance():
    np.testing.assert_allclose(_average_ranks([3, 1, 1, 4]), [3, 1.5, 1.5, 4])
    assert _correlation([1, 1, 1], [1, 2, 3]) is None
    points = np.array([[1., 0], [0, 1], [-1, -.2], [.1, -.8]])
    other = 3 * points @ np.array([[0., -1], [1, 0]]) + np.array([7, -4])
    assert _procrustes_m2(points, other) == pytest.approx(0, abs=1e-14)


def test_full_positive_tied_subspace_and_constant_distances_are_reported(tmp_path):
    source = tmp_path / "counts.dat"
    source.write_text(". t1 t2 t3\na 1 0 0\nb 0 4 0\nc 0 0 7\n")
    spec = {"method": "community", "input": str(source), "format": "past",
            "orientation": "samples_by_taxa", "value_type": "count",
            "transform": "relative_abundance", "distance": "braycurtis",
            "dimensions": 2, "missing": "error", "empty_samples": "error"}
    baseline = run(spec, tmp_path / "runs")["run_dir"]
    spec.update(transform="none", purpose="Disjoint-support control")
    sensitivity = run(spec, tmp_path / "runs")["run_dir"]
    directory = compare_community_runs(baseline, sensitivity, tmp_path / "comparison")["comparison_dir"]
    report = inspect_comparison(directory)["report"]
    assert report["selected_subspace_identifiable"] is True
    assert report["relative_eigengaps"] == {"baseline": None, "sensitivity": None}
    assert report["symmetric_procrustes_m2"] == pytest.approx(0, abs=1e-14)
    assert report["pearson_distance_correlation"] is None
    assert report["spearman_distance_correlation"] is None
    assert {warning["code"] for warning in report["warnings"]} == {"undefined_distance_correlation"}


def test_sensitivity_uses_shared_strict_cutoff_boundary():
    eigenvalues = [1e8, 2, 1, 0]
    expected = selected_subspace_info(eigenvalues, 2, 1e-14)
    assert expected["relative_cutoff_gap"] == expected["threshold"]
    result = {"n": 4, "distances": (np.ones((4, 4)) - np.eye(4)).tolist(),
              "eigenvalues": eigenvalues, "dimensions": 2, "eigenvalue_tolerance": 1e-14}
    arm = {"result": result, "specification": {}}
    with pytest.raises(AnalysisError) as caught:
        _report(arm, arm)
    assert caught.value.code == "nonidentifiable_axes"
    assert caught.value.details["subspaces"] == {"baseline": expected, "sensitivity": expected}
