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
