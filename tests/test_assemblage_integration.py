import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from palaeo_agent import (
    AnalysisError, inspect_run, inspect_study, reproduce, reproduce_study,
    run, run_study, validate,
)
from palaeo_agent.methods import compare_results


METHODS = ("rarefaction", "count_homogeneity")
COUNTS = ".\tx\ty\tz\tunused\na\t8\t2\t0\t0\nb\t1\t6\t3\t0\nc\t2\t2\t6\t0\n"
METADATA = "sample_id,zone\nc,C\na,A\nb,B\n"


def options(method):
    common = {"method": method, "format": "past", "orientation": "samples_by_taxa",
              "value_type": "count", "missing": "error", "empty_samples": "error"}
    if method == "rarefaction":
        return {**common, "sizes": [1, 5]}
    return {**common, "pairs": [["a", "b"], ["b", "c"]], "simulations": 999, "seed": 27}


def request(tmp_path, method):
    source = tmp_path / "counts.dat"
    source.write_text(COUNTS)
    metadata = tmp_path / "metadata.csv"
    metadata.write_text(METADATA)
    return {**options(method), "input": str(source), "metadata": str(metadata)}


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def replace_json_with_checksum(directory, filename, mutate):
    path = directory / filename
    payload = json.loads(path.read_text())
    mutate(payload)
    path.write_text(json.dumps(payload))
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    data = path.read_bytes()
    manifest["files"][filename].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest_path.write_text(json.dumps(manifest))


def cli(*arguments):
    return subprocess.run([sys.executable, "-m", "palaeo_agent", *map(str, arguments)],
                          cwd="/", text=True, capture_output=True)


@pytest.mark.parametrize("method", METHODS)
def test_portable_assemblage_bundle_tables_metadata_and_fresh_process_replay(tmp_path, method):
    spec = request(tmp_path, method)
    receipt = run(spec, tmp_path / "runs")
    directory = Path(receipt["run_dir"])
    for key in ("input", "metadata"):
        Path(spec[key]).unlink()
    inspected = inspect_run(directory)
    assert inspected["status"] == "verified"
    assert set(inspected["manifest"]["inputs"]) == {"matrix", "metadata"}
    assert inspected["result"]["metadata"] == [
        {"sample_id": "a", "zone": "A"}, {"sample_id": "b", "zone": "B"}, {"sample_id": "c", "zone": "C"}]
    assert read_csv(directory / "aligned_metadata.csv") == inspected["result"]["metadata"]
    assert read_csv(directory / "retained_counts.csv")[0] == {
        "sample_id": "a", "x": "8", "y": "2", "z": "0", "unused": "0"}
    files = inspected["manifest"]["files"]
    assert "diagnostics.png" not in files
    if method == "rarefaction":
        rows = read_csv(directory / "rarefaction.csv")
        assert [(row["sample_id"], int(row["size"])) for row in rows] == [
            (sample, size) for sample in ("a", "b", "c") for size in (1, 5)]
        assert float(rows[0]["expected_richness"]) == 1
        assert float(rows[0]["conditional_sd"]) == 0
        assert len(read_csv(directory / "coverage.csv")) == 3
    else:
        randomization = json.loads((directory / "randomization.json").read_text())
        assert randomization == inspected["result"]["randomization"]
        assert randomization["seed"] == 27 and randomization["simulations"] == 999
        assert randomization["sampler"] == "scipy.stats.random_table"
        for package in ("numpy", "scipy"):
            assert randomization[package + "_version"] == inspected["environment"]["packages"][package]
        rows = read_csv(directory / "count_homogeneity.csv")
        assert [(row["sample_a"], row["sample_b"]) for row in rows] == [("a", "b"), ("b", "c")]
        assert all(int(row["simulations"]) == 999 for row in rows)
        assert len(read_csv(directory / "taxon_tests.csv")) == 6
        zeros = read_csv(directory / "zero_count_limits.csv")
        assert [(row["sample_id"], row["taxon_id"]) for row in zeros] == [("a", "z")]
    completed = cli("reproduce", directory, "--output", tmp_path / "fresh")
    assert completed.returncode == 0, completed.stderr
    replay = json.loads(completed.stdout)
    assert replay["status"] == "reproduced" and replay["differences"] == []
    fresh = inspect_run(replay["new_run"])
    assert fresh["specification"]["input"] == "input.dat"
    assert fresh["specification"]["metadata"] == "metadata.csv"
    assert compare_results(inspected["result"], fresh["result"])[0] == []
    if method == "count_homogeneity":
        assert [pair["monte_carlo"] for pair in fresh["result"]["pairs"]] == [
            pair["monte_carlo"] for pair in inspected["result"]["pairs"]]


@pytest.mark.parametrize("method", METHODS)
def test_cli_relative_spec_runs_and_reports_input_refusals(tmp_path, method):
    spec = request(tmp_path, method)
    spec.update(input="counts.dat", metadata="metadata.csv")
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    validated = cli("validate", path)
    assert validated.returncode == 0, validated.stderr
    assert json.loads(validated.stdout)["status"] == "valid"
    executed = cli("run", path, "--output", tmp_path / "runs")
    assert executed.returncode == 0, executed.stderr
    receipt = json.loads(executed.stdout)
    inspected = cli("inspect", receipt["run_dir"])
    assert inspected.returncode == 0, inspected.stderr
    assert json.loads(inspected.stdout)["result"]["method"] == method
    if method == "rarefaction":
        spec["sizes"] = [11]
    else:
        spec["pairs"] = [["a", "missing"]]
    path.write_text(json.dumps(spec))
    refused = cli("run", path, "--output", tmp_path / "refused")
    assert refused.returncode == 2 and refused.stdout == ""
    assert json.loads(refused.stderr)["status"] == "error"
    assert not (tmp_path / "refused").exists()


@pytest.mark.parametrize("method", METHODS)
def test_assemblage_table_tampering_refuses_reproduction_before_allocation(tmp_path, method):
    directory = Path(run(request(tmp_path, method), tmp_path / "runs")["run_dir"])
    path = directory / ("rarefaction.csv" if method == "rarefaction" else "taxon_tests.csv")
    path.write_text(path.read_text() + "corrupted\n")
    with pytest.raises(AnalysisError) as caught:
        reproduce(directory, tmp_path / "replay")
    assert caught.value.code == "invalid_bundle"
    assert not (tmp_path / "replay").exists()


@pytest.mark.parametrize("method,filename,mutate", [
    ("rarefaction", "results.json", lambda value: value.update(orientation="taxa_by_samples")),
    ("rarefaction", "spec.json", lambda value: value.update(sizes=[2, 5])),
    ("count_homogeneity", "randomization.json", lambda value: value.update(seed=99)),
    ("count_homogeneity", "environment.json", lambda value: value["packages"].update(scipy="0.0.0")),
    ("count_homogeneity", "spec.json", lambda value: value.update(pairs=[["b", "c"], ["a", "b"]])),
])
def test_saved_spec_and_randomization_invariants_survive_rewritten_checksums(tmp_path, method, filename, mutate):
    directory = Path(run(request(tmp_path, method), tmp_path / "runs")["run_dir"])
    replace_json_with_checksum(directory, filename, mutate)
    for operation in (lambda: inspect_run(directory), lambda: reproduce(directory, tmp_path / "fresh")):
        with pytest.raises(AnalysisError) as caught:
            operation()
        assert caught.value.code == "invalid_bundle"
    assert not (tmp_path / "fresh").exists()


def test_prepared_assemblage_study_replays_without_originals(tmp_path):
    source = tmp_path / "raw.dat"
    source.write_text(".\ta\tb\tc\tempty\nx\t6\t1\t2\t0\nx_alias\t2\t0\t0\t0\n"
                      "y\t2\t6\t2\t0\nz\t0\t3\t6\t0\nunused\t0\t0\t0\t0\n")
    metadata = tmp_path / "raw-metadata.csv"
    metadata.write_text("core,zone\nc,C\na,A\nempty,E\nb,B\nunused_metadata,U\n")
    study = {
        "study_version": 1,
        "inputs": {"raw": {"kind": "counts", "path": "raw.dat", "orientation": "taxa_by_samples"},
                   "sites": {"kind": "metadata", "path": "raw-metadata.csv", "id_column": "core"}},
        "datasets": {"clean": {"source": "raw", "metadata": "sites", "drop_unmatched_metadata": True,
                                "operations": [
                                    {"op": "exclude", "samples": ["empty"], "reason": "no specimens recovered"},
                                    {"op": "map_taxa", "mapping": {"x_alias": "x"}, "reason": "declared synonym"}]}},
        "analyses": [{"id": method, "dataset": "clean", "spec": options(method)} for method in METHODS],
    }
    declaration = tmp_path / "study.json"
    declaration.write_text(json.dumps(study))
    receipt = run_study(declaration, tmp_path / "studies")
    assert receipt["status"] == "complete", receipt
    directory = Path(receipt["study_dir"])
    assert (directory / "derived/clean.dat").read_text() == COUNTS
    preparation = json.loads((directory / "derived/clean.json").read_text())
    assert any(record.get("merged") == {"x": ["x", "x_alias"]} for record in preparation["operations"])
    for path in (source, metadata, declaration):
        path.unlink()
    inspected = inspect_study(directory)
    assert inspected["status"] == "verified"
    original_results = {}
    for method in METHODS:
        child = inspect_run(directory / inspected["runs"][method]["run_dir"])
        original_results[method] = child["result"]
        assert child["result"]["retained_counts"] == [[8, 2, 0, 0], [1, 6, 3, 0], [2, 2, 6, 0]]
        assert child["result"]["metadata"][0] == {"sample_id": "a", "zone": "A"}
    report = (directory / "report.md").read_text()
    assert "rarefaction" in report and "count_homogeneity" in report
    assert "declared synonym" in report
    replay = reproduce_study(directory, tmp_path / "replayed")
    assert replay["status"] == "reproduced" and replay["derived_identical"]
    fresh = inspect_study(replay["new"])
    for method in METHODS:
        child = inspect_run(Path(replay["new"]) / fresh["runs"][method]["run_dir"])
        assert compare_results(original_results[method], child["result"])[0] == []


@pytest.mark.parametrize("method", METHODS)
def test_validate_new_methods_does_not_compute_rarefaction_or_random_tables(tmp_path, monkeypatch, method):
    import palaeo_agent.count_homogeneity as homogeneity
    import palaeo_agent.rarefaction as rarefaction

    def forbidden(*args, **kwargs):
        raise AssertionError("Numerical analysis invoked during input validation")

    monkeypatch.setattr(rarefaction, "_absence", forbidden)
    monkeypatch.setattr(homogeneity, "random_table", forbidden)
    spec = request(tmp_path, method)
    assert validate(spec)["status"] == "valid"
