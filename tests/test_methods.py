import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from palaeo_agent import AnalysisError, discover, inspect_run, reproduce, run, validate
from palaeo_agent.methods import compare_results


def community_request(tmp_path, *, metadata=True, transform="none"):
    source = tmp_path / "counts.dat"
    source.write_text(". t1 t2 t3\na 3 1 0\nb 0 3 1\nc 1 0 3\n")
    request = {"method": "community", "input": str(source), "format": "past",
               "orientation": "samples_by_taxa", "value_type": "count", "transform": transform,
               "distance": "braycurtis", "dimensions": 2, "missing": "error", "empty_samples": "error"}
    if metadata:
        metadata_path = tmp_path / "meta.csv"
        metadata_path.write_text("sample_id,site\nc,C\na,A\nb,B\n")
        request["metadata"] = str(metadata_path)
    return request


def test_discovery_exposes_all_methods_with_typed_outputs():
    methods = {method["id"]: method for method in discover()["methods"]}
    assert set(methods) == {"rma", "community", "permanova", "rarefaction", "count_homogeneity"}
    assert methods["community"]["input_schema"]["additionalProperties"] is False
    assert {"retained_counts", "retained_values"} <= set(methods["community"]["output_schema"]["properties"])


def test_multi_input_bundle_reproduces_without_source_files(tmp_path):
    spec = community_request(tmp_path)
    first = run(spec, tmp_path / "runs")
    bundle = Path(first["run_dir"])
    inspected = inspect_run(bundle)
    assert set(inspected["manifest"]["inputs"]) == {"matrix", "metadata"}
    assert inspected["manifest"]["schema_version"] == 2
    assert inspected["result"]["metadata"] == [
        {"sample_id": "a", "site": "A"}, {"sample_id": "b", "site": "B"}, {"sample_id": "c", "site": "C"},
    ]
    for filename in ("retained_counts.csv", "transformed_matrix.csv", "diversity.csv", "distances.csv",
                     "ordination.csv", "eigenvalues.csv", "positive_gram.csv", "aligned_metadata.csv"):
        assert filename in inspected["manifest"]["files"]
        assert inspected["manifest"]["files"][filename]["produced_by"]
    Path(spec["input"]).unlink()
    Path(spec["metadata"]).unlink()
    response = subprocess.run([sys.executable, "-m", "palaeo_agent", "reproduce", str(bundle),
                               "--output", str(tmp_path / "fresh")], capture_output=True, text=True)
    assert response.returncode == 0, response.stderr
    payload = json.loads(response.stdout)
    assert payload["status"] == "reproduced"
    assert payload["differences"] == []
    portable = json.loads((Path(payload["new_run"]) / "spec.json").read_text())
    assert portable["input"] == "input.dat" and portable["metadata"] == "metadata.csv"


def test_validate_does_not_run_eigendecomposition(tmp_path, monkeypatch):
    request = community_request(tmp_path, metadata=False)
    def forbidden(*args, **kwargs):
        raise AssertionError("Numerical ordination invoked during validation")
    monkeypatch.setattr(np.linalg, "eigh", forbidden)
    assert validate(request)["status"] == "valid"


def test_missing_checkout_lock_is_explicit(tmp_path, monkeypatch):
    from palaeo_agent import runs
    monkeypatch.setattr(runs, "_find_lockfile", lambda: None)
    record = inspect_run(run(community_request(tmp_path, metadata=False), tmp_path / "runs")["run_dir"])
    assert record["environment"]["lockfile"]["available"] is False
    assert record["environment"]["lockfile"]["path"] is None
    assert record["environment"]["lockfile"]["reason"]
    assert "uv.lock" not in record["manifest"]["files"]
    assert "numpy" in record["environment"]["packages"]


def test_old_schema_is_explicitly_unsupported(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"schema_version": 1, "status": "complete"}))
    with pytest.raises(AnalysisError) as caught:
        inspect_run(tmp_path)
    assert caught.value.code == "unsupported_schema"


def test_changed_named_input_role_is_rejected_before_reproduction(tmp_path):
    first = run(community_request(tmp_path), tmp_path / "runs")
    directory = Path(first["run_dir"])
    path = directory / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["inputs"]["metadata"]["path"] = "input.dat"
    path.write_text(json.dumps(manifest))
    with pytest.raises(AnalysisError) as caught:
        reproduce(directory, tmp_path / "fresh")
    assert caught.value.code == "invalid_bundle"
    assert not (tmp_path / "fresh").exists()


def test_ordination_comparison_uses_geometry_not_axis_signs(tmp_path):
    first = inspect_run(run(community_request(tmp_path, metadata=False), tmp_path / "runs")["run_dir"])["result"]
    rotated = json.loads(json.dumps(first))
    coordinates = np.asarray(first["coordinates"])
    rotated["coordinates"] = (coordinates @ np.array([[0, -1], [1, 0]])).tolist()
    differences, _ = compare_results(first, rotated)
    assert differences == []
    rotated["positive_gram"][0][0] += .1
    with pytest.raises(ValueError):
        compare_results(first, rotated)
