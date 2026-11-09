import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from pydantic import ValidationError

from palaeo_agent import AnalysisError, discover, inspect_run, reproduce, run, validate
from palaeo_agent.count_homogeneity import calculate_count_homogeneity
from palaeo_agent.methods import compare_results
from abundance_helpers import ABUNDANCE_COMMUNITY, ABUNDANCE_TABLE, abundance_table
from bundle_helpers import rehash as _rehash
from count_homogeneity_helpers import pair_spec


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
    assert set(methods) == {"rma", "rma_paired", "community", "permanova", "rarefaction", "count_homogeneity"}
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


def test_discovery_version_matches_schema_and_results(tmp_path):
    from palaeo_agent import discover
    from palaeo_agent.count_homogeneity import CountHomogeneityResult
    entry = next(m for m in discover()["methods"] if m["id"] == "count_homogeneity") if isinstance(discover(), dict) \
        else next(m for m in discover() if m["id"] == "count_homogeneity")
    schema = CountHomogeneityResult.model_json_schema()["properties"]["method_version"]
    result = calculate_count_homogeneity(pair_spec(tmp_path, pairs="adjacent"), (tmp_path / "t.dat").read_bytes())
    assert entry["version"] == schema["const"] == result["method_version"] == 3


@pytest.mark.parametrize("method", ["rarefaction", "count_homogeneity"])
def test_count_only_methods_refuse_abundance_even_when_integer_valued(tmp_path, method):
    (tmp_path / "t.dat").write_text(".\tA\tB\nS1\t10\t5\nS2\t8\t7\n")
    spec = {"method": method, "input": str(tmp_path / "t.dat"), "format": "past", "orientation": "samples_by_taxa",
            "value_type": "abundance", "missing": "error", "empty_samples": "error"}
    if method == "count_homogeneity":
        spec.update(pairs=[["S1", "S2"]], simulations=999, seed=1)
    with pytest.raises((ValidationError, AnalysisError)):
        run(spec, tmp_path / "out")


@pytest.mark.parametrize("tamper", [
    lambda r: r.update(value_type="count", retained_counts=r.pop("retained_values")),
    lambda r: r["retained_values"][0].__setitem__(0, 51.0),
    lambda r: r.update(transform="none"),
])
def test_inspection_binds_value_type_values_and_transform(tmp_path, tamper):
    (tmp_path / "c.dat").write_bytes(abundance_table(ABUNDANCE_TABLE))
    outcome = run(dict(ABUNDANCE_COMMUNITY, input=str(tmp_path / "c.dat"), transform="relative_abundance"), tmp_path / "run")
    results = Path(outcome["run_dir"]) / "results.json"
    data = json.loads(results.read_text())
    tamper(data)
    results.write_text(json.dumps(data, indent=2))
    _rehash(outcome["run_dir"], "results.json")
    with pytest.raises(Exception):
        inspect_run(outcome["run_dir"])


@pytest.mark.parametrize("method", ["community", "permanova", "rarefaction"])
def test_deleted_table_diagnostic_fails_inspection(tmp_path, method):
    (tmp_path / "c.dat").write_text(".\tA\tB\tC\ns1\t3\t2\t1\ns2\t3\t2\t1\ns3\t1\t5\t2\ns4\t0\t4\t4\n")
    (tmp_path / "m.csv").write_text("sample_id,g\ns1,a\ns2,a\ns3,b\ns4,b\n")
    spec = {"method": method, "input": str(tmp_path / "c.dat"), "format": "past", "orientation": "samples_by_taxa",
            "value_type": "count", "missing": "error", "empty_samples": "error"}
    spec.update({"community": {"transform": "none", "distance": "braycurtis", "dimensions": 1},
                 "permanova": {"metadata": str(tmp_path / "m.csv"), "group_column": "g", "transform": "none",
                               "distance": "braycurtis", "design": "independent", "permutation_scheme": "free",
                               "permutations": 99, "seed": 1},
                 "rarefaction": {"sizes": [2]}}[method])
    run_dir = Path(run(spec, tmp_path / "runs")["run_dir"])
    path = run_dir / "results.json"
    result = json.loads(path.read_text())
    assert "identical_samples" in [warning["code"] for warning in result["warnings"]]
    result["warnings"] = [warning for warning in result["warnings"] if warning["code"] != "identical_samples"]
    path.write_text(json.dumps(result, indent=2) + "\n")
    _rehash(run_dir, "results.json")
    with pytest.raises(AnalysisError) as caught:
        inspect_run(run_dir)
    assert "Input diagnostics" in caught.value.details["reason"]
