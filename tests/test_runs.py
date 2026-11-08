import json
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

from palaeo_agent import AnalysisError, inspect_run, reproduce, run


def request(path):
    return {"method": "rma", "input": str(path), "format": "past", "x": "x", "y": "y",
            "transform": "none", "missing": "error"}


def make_run(tmp_path):
    source = tmp_path / "original.dat"
    source.write_text(". x y\na 1 3\nb 2 5\nc 4 9\n")
    return source, run(request(source), tmp_path / "runs")


def test_unresolved_pcoa_cutoff_is_refused_before_bundle_allocation(tmp_path):
    source = tmp_path / "equilateral.dat"
    source.write_text(". x y z\na 1 0 0\nb 0 1 0\nc 0 0 1\n")
    spec = {"method": "community", "input": str(source), "format": "past",
            "orientation": "samples_by_taxa", "value_type": "count", "transform": "none",
            "distance": "braycurtis", "dimensions": 1, "missing": "error", "empty_samples": "error"}
    with pytest.raises(AnalysisError) as caught:
        run(spec, tmp_path / "runs")
    assert caught.value.code == "nonidentifiable_axes"
    assert not (tmp_path / "runs").exists()


def test_reproduction_compares_full_positive_geometry_with_a_small_final_axis(tmp_path):
    source = tmp_path / "counts.dat"
    source.write_text(". x y z\na 10000 0 0\nb 10000 1 0\nc 0 0 10000\n")
    spec = {"method": "community", "input": str(source), "format": "past",
            "orientation": "samples_by_taxa", "value_type": "count", "transform": "none",
            "distance": "braycurtis", "dimensions": 2, "missing": "error", "empty_samples": "error"}
    first = run(spec, tmp_path / "runs")
    result = inspect_run(first["run_dir"])["result"]
    assert result["eigenvalue_tolerance"] < result["eigenvalues"][1] < 1e-8 * result["eigenvalues"][0]
    receipt = reproduce(first["run_dir"], tmp_path / "reproduced")
    assert receipt["status"] == "reproduced"
    policy = receipt["ordination_comparison"]
    assert policy["selected_gram_compared"] is True
    assert policy["selected_subspace_ambiguous"] is False
    assert policy["cutoff_relative_eigengap"] is None


def test_portable_bundle_and_fresh_process_reproduction(tmp_path):
    source, first = make_run(tmp_path)
    source.unlink()
    inspected = inspect_run(first["run_dir"])
    assert inspected["status"] == "verified"
    assert inspected["manifest"]["files"]["diagnostics.png"]["media_type"] == "image/png"
    assert (Path(first["run_dir"]) / "diagnostics.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    result = subprocess.run([sys.executable, "-m", "palaeo_agent", "reproduce", first["run_dir"],
                             "--output", str(tmp_path / "fresh")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "reproduced"
    assert payload["differences"] == []
    assert payload["new_run"] != first["run_dir"]
    spec = json.loads((Path(payload["new_run"]) / "spec.json").read_text())
    assert spec["input"] == "input.dat"


def test_bundle_tampering_is_detected_before_reproduction(tmp_path):
    _, first = make_run(tmp_path)
    (Path(first["run_dir"]) / "results.json").write_text("{}")
    with pytest.raises(AnalysisError) as caught:
        reproduce(first["run_dir"], tmp_path / "fresh")
    assert caught.value.code == "invalid_bundle"
    assert not (tmp_path / "fresh").exists()


def test_extra_file_and_symlink_are_not_verified(tmp_path):
    _, first = make_run(tmp_path)
    directory = Path(first["run_dir"])
    (directory / "unexpected").write_text("x")
    with pytest.raises(AnalysisError):
        inspect_run(directory)
    (directory / "unexpected").unlink()
    stored = (directory / "input.dat").read_bytes()
    elsewhere = tmp_path / "external.dat"
    elsewhere.write_bytes(stored)
    (directory / "input.dat").unlink()
    (directory / "input.dat").symlink_to(elsewhere)
    with pytest.raises(AnalysisError):
        inspect_run(directory)


def test_cli_relative_input_and_structured_error(tmp_path):
    source = tmp_path / "source.dat"
    source.write_text(". x y\na 1 3\nb 2 5\nc 4 9\n")
    spec = request(Path("source.dat"))
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    command = [sys.executable, "-m", "palaeo_agent", "validate", str(path)]
    result = subprocess.run(command, cwd="/", capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "valid"
    spec["x"] = "absent"
    path.write_text(json.dumps(spec))
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["code"] == "unknown_column"


@pytest.mark.parametrize("arguments", [[], ["unknown"], ["run"]])
def test_cli_argument_errors_are_json(arguments):
    result = subprocess.run([sys.executable, "-m", "palaeo_agent", *arguments],
                             capture_output=True, text=True)
    assert result.returncode == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["code"] == "invalid_arguments"


def test_bundle_write_failure_has_no_completion_manifest(tmp_path, monkeypatch):
    from palaeo_agent import runs
    source = tmp_path / "source.dat"
    source.write_text(". x y\na 1 3\nb 2 5\nc 4 9\n")
    def broken_plot(*args):
        raise OSError("Deliberate plot failure")
    monkeypatch.setattr(runs, "_plot", broken_plot)
    with pytest.raises(AnalysisError) as caught:
        run(request(source), tmp_path / "runs")
    directory = Path(caught.value.details["run_dir"])
    assert (directory / "failure.json").is_file()
    assert not (directory / "manifest.json").exists()


def replace_record_with_valid_checksum(directory, filename, update):
    path = directory / filename
    value = json.loads(path.read_text())
    update(value)
    path.write_text(json.dumps(value))
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    data = path.read_bytes()
    manifest["files"][filename].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest_path.write_text(json.dumps(manifest))


@pytest.mark.parametrize("update", [
    lambda result: result.pop("pairs"),
    lambda result: result["pairs"][0].update(residual="not a number"),
    lambda result: result.update(n=9),
    lambda result: result["pairs"][1].update(sample_id="a"),
    lambda result: result.update(excluded=[{"sample_id": "a", "reason": "declared_missing_pair", "columns": ["x"]}], n_input=4),
    lambda result: result.update(transform="log10"),
])
def test_structurally_invalid_results_are_rejected_even_with_valid_checksums(tmp_path, update):
    _, first = make_run(tmp_path)
    directory = Path(first["run_dir"])
    replace_record_with_valid_checksum(directory, "results.json", update)
    for operation in (lambda: inspect_run(directory), lambda: reproduce(directory, tmp_path / "fresh")):
        with pytest.raises(AnalysisError) as caught:
            operation()
        assert caught.value.code == "invalid_bundle"
    assert not (tmp_path / "fresh").exists()


@pytest.mark.parametrize("filename,update", [
    ("results.json", lambda value: value.pop("pairs")),
    ("environment.json", lambda value: value.update(packages=["numpy"])),
    ("spec.json", lambda value: value.update(input="../external.dat")),
])
def test_malformed_bundle_records_produce_structured_cli_errors(tmp_path, filename, update):
    _, first = make_run(tmp_path)
    directory = Path(first["run_dir"])
    replace_record_with_valid_checksum(directory, filename, update)
    for command in ("inspect", "reproduce"):
        arguments = [sys.executable, "-m", "palaeo_agent", command, str(directory)]
        if command == "reproduce":
            arguments += ["--output", str(tmp_path / "fresh")]
        completed = subprocess.run(arguments, capture_output=True, text=True)
        assert completed.returncode == 2
        assert completed.stdout == ""
        assert json.loads(completed.stderr)["code"] == "invalid_bundle"
    assert not (tmp_path / "fresh").exists()


def _rehash(directory, manifest, name):
    data = (directory / name).read_bytes()
    manifest["files"][name].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    (directory / "manifest.json").write_text(json.dumps(manifest))


@pytest.mark.parametrize("tamper", ["table", "extra_step"])
def test_rehashed_tables_and_steps_must_derive_from_the_result(tmp_path, tamper):
    _, first = make_run(tmp_path)
    directory = Path(first["run_dir"])
    manifest = json.loads((directory / "manifest.json").read_text())
    if tamper == "table":
        name, path = "used-pairs.csv", directory / "used-pairs.csv"
        edited = path.read_text().replace("5.0", "5.5", 1)
        assert edited != path.read_text()
        path.write_text(edited)
    else:
        name = "notes.csv"
        (directory / name).write_text("note\n")
        manifest["steps"].append({"id": "annotate", "inputs": [], "outputs": [name]})
        manifest["files"][name] = {"sha256": "0" * 64, "bytes": 0, "media_type": "text/csv", "produced_by": "annotate"}
    _rehash(directory, manifest, name)
    with pytest.raises(AnalysisError) as caught:
        inspect_run(directory)
    assert caught.value.code == "invalid_bundle"


def test_output_inside_a_read_bundle_is_refused(tmp_path):
    _, first = make_run(tmp_path)
    with pytest.raises(AnalysisError) as caught:
        reproduce(first["run_dir"], Path(first["run_dir"]) / "again")
    assert caught.value.code == "output_inside_bundle"
    assert inspect_run(first["run_dir"])["status"] == "verified"
