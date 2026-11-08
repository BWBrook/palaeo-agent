import json
from pathlib import Path
import subprocess
import sys

import pytest

from palaeo_agent import AnalysisError, discover, inspect_run, reproduce, run, validate
from palaeo_agent.permanova import _monte_carlo_fields
from abundance_helpers import (
    ABUNDANCE_METADATA, ABUNDANCE_PERMANOVA, ABUNDANCE_TABLE,
    abundance_table,
)
from bundle_helpers import rehash as _rehash


def request(tmp_path, *, permutations=999):
    matrix = tmp_path / "counts.dat"
    matrix.write_text(". t1 t2\na 9 1\nb 8 2\nc 2 8\nd 1 9\n")
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("sample_id,habitat\nd,B\nb,A\na,A\nc,B\n")
    return {"method": "permanova", "input": str(matrix), "metadata": str(metadata),
            "group_column": "habitat", "format": "past", "orientation": "samples_by_taxa",
            "value_type": "count", "distance": "braycurtis", "transform": "none",
            "missing": "error", "empty_samples": "error", "design": "independent",
            "permutation_scheme": "free", "permutations": permutations, "seed": 107}


def rewrite_record(directory, name, change):
    path = directory / name
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value, allow_nan=False))
    _rehash(directory, name)


@pytest.mark.parametrize("field", ["pseudo_f", "permutation_statistic"])
def test_saved_tail_count_matches_saved_statistics_even_within_numeric_tolerance(tmp_path, field):
    from palaeo_agent.methods import table_files

    spec = request(tmp_path)
    Path(spec["input"]).write_text(". A B\na 100000 0\nb 100000 1\nc 0 100000\nd 1 100000\n")
    bundle = Path(run(spec, tmp_path / "runs")["run_dir"])
    result = inspect_run(bundle)["result"]
    assert result["permutation"]["mode"] == "exact"
    assert result["permutation"]["count_extreme"] == 2
    if field == "pseudo_f":
        result["pseudo_f"] += 1
    else:
        statistics = result["permutation"]["statistics"]
        statistics[statistics.index(max(statistics))] -= 1
    (bundle / "results.json").write_text(json.dumps(result))
    _rehash(bundle, "results.json")
    for name, data in table_files(result).items():
        (bundle / name).write_bytes(data)
        _rehash(bundle, name)
    with pytest.raises(AnalysisError) as error:
        inspect_run(bundle)
    assert error.value.code == "invalid_bundle"
    assert "exceedances" in str(error.value.details)


def test_compact_discovery_precedes_all_large_schemas():
    output = discover()
    encoded = json.dumps(output)
    prefix = encoded[:encoded.index('"methods"')]
    assert list(output)[:2] == ["primer", "method_index"]
    assert all(name in prefix for name in ("rma", "community", "permanova", "rarefaction", "count_homogeneity"))
    assert len(prefix) < 3072
    completed = subprocess.run([sys.executable, "-m", "palaeo_agent", "--help"], capture_output=True, text=True)
    assert completed.returncode == 0
    assert "Supported methods: rma, community, permanova" in completed.stdout


@pytest.mark.parametrize("permutations,mode", [(999, "exact"), (3, "monte_carlo")])
def test_named_permanova_bundle_reproduces_without_original_inputs(tmp_path, permutations, mode):
    spec = request(tmp_path, permutations=permutations)
    first = run(spec, tmp_path / "runs")
    bundle = Path(first["run_dir"])
    record = inspect_run(bundle)
    assert record["result"]["groups"] == ["A", "A", "B", "B"]
    assert record["result"]["permutation"]["mode"] == mode
    assert set(record["manifest"]["inputs"]) == {"matrix", "metadata"}
    for name in ("retained_counts.csv", "transformed_matrix.csv", "distances.csv", "aligned_metadata.csv",
                 "groups.csv", "permanova.csv", "permutations.json", "dispersion.csv", "group_dispersion.csv", "eigenvalues.csv"):
        assert name in record["manifest"]["files"]
        assert record["manifest"]["files"][name]["produced_by"]
    assert json.loads((bundle / "permutations.json").read_text()) == record["result"]["permutation"]
    assert "PCG64" in record["environment"]["rng"] if mode == "monte_carlo" else "exact" in record["environment"]["rng"]
    Path(spec["input"]).unlink()
    Path(spec["metadata"]).unlink()
    fresh = reproduce(bundle, tmp_path / "fresh")
    assert fresh["status"] == "reproduced" and fresh["differences"] == []
    assert "ordination_comparison" not in fresh
    portable = json.loads((Path(fresh["new_run"]) / "spec.json").read_text())
    assert portable["input"] == "input.dat" and portable["metadata"] == "metadata.csv"


def test_relative_cli_inputs_and_fresh_process_reproduction(tmp_path):
    spec = request(tmp_path, permutations=3)
    spec.update(input="counts.dat", metadata="metadata.csv")
    path = tmp_path / "request.json"
    path.write_text(json.dumps(spec))
    completed = subprocess.run([sys.executable, "-m", "palaeo_agent", "run", str(path), "--output", str(tmp_path / "runs")],
                               cwd="/", capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    bundle = json.loads(completed.stdout)["run_dir"]
    (tmp_path / "counts.dat").unlink()
    (tmp_path / "metadata.csv").unlink()
    repeated = subprocess.run([sys.executable, "-m", "palaeo_agent", "reproduce", bundle,
                               "--output", str(tmp_path / "fresh")], capture_output=True, text=True)
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)["status"] == "reproduced"


def test_validation_does_not_generate_a_permutation_schedule(tmp_path, monkeypatch):
    from palaeo_agent import permanova
    def forbidden(*args, **kwargs):
        raise AssertionError("Permutation schedule constructed during validation")
    monkeypatch.setattr(permanova, "_schedule", forbidden)
    assert validate(request(tmp_path))["status"] == "valid"


@pytest.mark.parametrize("filename,change", [
    ("spec.json", lambda record: record.update(seed=108)),
    ("spec.json", lambda record: record.update(group_column="absent")),
    ("spec.json", lambda record: record.update(metadata="../external.csv")),
    ("results.json", lambda record: record["metadata"][0].update(habitat="B")),
    ("results.json", lambda record: record["permutation"].update(requested=2)),
    ("permutations.json", lambda record: record.update(seed=108)),
    ("environment.json", lambda record: record.update(rng="not used; deterministic method")),
])
def test_mismatched_permanova_records_refuse_before_reproduction(tmp_path, filename, change):
    directory = Path(run(request(tmp_path, permutations=3), tmp_path / "runs")["run_dir"])
    rewrite_record(directory, filename, change)
    with pytest.raises(AnalysisError) as caught:
        reproduce(directory, tmp_path / "fresh")
    assert caught.value.code == "invalid_bundle"
    assert not (tmp_path / "fresh").exists()


def test_unsupported_design_is_a_structured_cli_failure(tmp_path):
    spec = request(tmp_path)
    spec["design"] = "repeated"
    path = tmp_path / "request.json"
    path.write_text(json.dumps(spec))
    completed = subprocess.run([sys.executable, "-m", "palaeo_agent", "validate", str(path)], capture_output=True, text=True)
    assert completed.returncode == 2 and completed.stdout == ""
    assert json.loads(completed.stderr)["code"] == "invalid_specification"


def test_sensitivity_comparison_explicitly_refuses_permanova(tmp_path):
    from palaeo_agent import compare_community_runs
    bundle = run(request(tmp_path), tmp_path / "runs")["run_dir"]
    with pytest.raises(AnalysisError) as caught:
        compare_community_runs(bundle, bundle, tmp_path / "comparison")
    assert caught.value.code == "comparison_method"
    assert not (tmp_path / "comparison").exists()


def test_abundance_permanova_runs_and_inspects(tmp_path):
    (tmp_path / "p.dat").write_bytes(abundance_table(ABUNDANCE_TABLE))
    (tmp_path / "m.csv").write_text(ABUNDANCE_METADATA)
    outcome = run(dict(ABUNDANCE_PERMANOVA, input=str(tmp_path / "p.dat"), metadata=str(tmp_path / "m.csv")), tmp_path / "run")
    inspected = inspect_run(outcome["run_dir"])
    assert inspected["status"] == "verified"
    result = inspected["result"]
    assert result["value_type"] == "abundance" and "retained_counts" not in result
    assert (Path(outcome["run_dir"]) / "retained_values.csv").is_file()
    assert 0 < result["p_value"] <= 1 and 0 <= result["r_squared"] <= 1


def abundance_run(tmp_path, permutations):
    (tmp_path / "p.dat").write_bytes(abundance_table(ABUNDANCE_TABLE))
    (tmp_path / "m.csv").write_text(ABUNDANCE_METADATA)
    spec = dict(ABUNDANCE_PERMANOVA, input=str(tmp_path / "p.dat"), metadata=str(tmp_path / "m.csv"), permutations=permutations)
    return run(spec, tmp_path / "run")


@pytest.mark.parametrize("permutations,mode", [(9, "monte_carlo"), (999, "exact")])
def test_runs_record_the_interval_and_keep_the_p_value(tmp_path, permutations, mode):
    outcome = abundance_run(tmp_path, permutations)
    result = inspect_run(outcome["run_dir"])["result"]
    record = result["permutation"]
    assert result["method_version"] == 2 and record["mode"] == mode
    if mode == "exact":
        assert record["tail_probability_interval"] is None and result["p_value"] == record["count_extreme"] / record["space_size"]
    else:
        assert result["p_value"] == (record["count_extreme"] + 1) / (permutations + 1)
        assert record == {**record, **_monte_carlo_fields(mode, record["count_extreme"], permutations)}
    header = (Path(outcome["run_dir"]) / "permanova.csv").read_text().splitlines()[0]
    assert header.endswith("tail_interval_lower,tail_interval_upper,monte_carlo_unresolved")


@pytest.mark.parametrize("tamper", [
    lambda p: p.update(monte_carlo_unresolved=not p["monte_carlo_unresolved"]),
    lambda p: p.update(tail_probability_interval=[0.0, 0.5]),
    lambda p: p.update(tail_probability_interval=None, interval_status="not_applicable_exact_enumeration",
                       monte_carlo_unresolved=None),
])
def test_rehashed_interval_tampering_fails_inspection(tmp_path, tamper):
    outcome = abundance_run(tmp_path, 9)
    results = Path(outcome["run_dir"]) / "results.json"
    data = json.loads(results.read_text())
    tamper(data["permutation"])
    results.write_text(json.dumps(data, indent=2))
    _rehash(outcome["run_dir"], "results.json")
    with pytest.raises(Exception):
        inspect_run(outcome["run_dir"])
