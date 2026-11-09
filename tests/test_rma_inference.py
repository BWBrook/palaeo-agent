"""RMA magnitude and direction inference against smatr, base-R tails, duality and coverage."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from palaeo_agent import AnalysisError, inspect_run, rma_regression, run
from palaeo_agent.core import RmaSpec, calculate, fit_rma, rma_inference
from palaeo_agent.methods import table_files
from bundle_helpers import rehash

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "references/r/rma-inference-reference.json").read_text())


def close(actual, expected):
    return math.isclose(actual, expected, rel_tol=REFERENCE["rtol"], abs_tol=REFERENCE["atol"])


def test_reference_provenance_is_current():
    generator = ROOT / REFERENCE["generator"]
    assert hashlib.sha256(generator.read_bytes()).hexdigest() == (
        "54fc0374e9ef5ca55c8d051801584a8f796f08215285a9a748c42c9a257ac869")
    assert REFERENCE["packages"]["smatr"] == "3.5.2"


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda case: case["id"])
def test_inference_matches_smatr_and_base_r_tails(case):
    path = (ROOT / "references/r" / case["input"]).resolve()
    data = path.read_bytes()
    if path.suffix == ".tsv":
        data = data.replace(b"specimen_id\t", b".\t", 1)
    spec = RmaSpec(method="rma", input=path, format="past", x=case["x"], y=case["y"], transform=case["transform"],
                   missing="drop_pairs", inference={"confidence": case["confidence"], "null_magnitude": case["null_magnitude"]})
    result = calculate(spec, data)
    inference, smatr, base = result["inference"], case["smatr"], case["base"]
    assert result["n"] == case["n"]
    assert close(result["slope"], smatr["slope"])
    assert all(close(a, b) for a, b in zip(inference["magnitude_interval"],
                                           sorted([abs(smatr["slope_low"]), abs(smatr["slope_high"])])))
    test, direction = inference["magnitude_test"], inference["direction_test"]
    assert close(test["r_rf"], base["r_rf"]) and close(abs(test["r_rf"]), abs(smatr["slope_test_r"]))
    # t = r / sqrt(1 - r^2) amplifies last-bit differences in r by about 1 / (1 - r^2); scale the tolerance to it.
    for statistic, r, expected in ((test["t"], test["r_rf"], base["t_rf"]), (direction["t"], direction["r"], base["t_r"])):
        assert math.isclose(statistic, expected, rel_tol=1e-10 / (1 - r * r), abs_tol=1e-10)
    assert test["df"] == base["df"]
    for record, r, key in ((test, test["r_rf"], "magnitude_log10_p"), (direction, direction["r"], "direction_log10_p")):
        log10_p = record["log10_p_value"] if record["p_value_underflow"] else math.log10(record["p_value"])
        assert math.isclose(log10_p, base[key], rel_tol=1e-9 / (1 - r * r) ** 0.5, abs_tol=1e-10)
    if not test["p_value_underflow"]:
        assert close(test["p_value"], smatr["slope_test_p"])
        assert close(direction["p_value"], smatr["correlation_p"])
    if case["id"] == "extreme_tails":
        assert test["p_value_underflow"] and direction["p_value_underflow"]
        assert smatr["slope_test_p"] == 0


def _data(rho, n, rng):
    x, y = rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], n).T
    return x, y


def test_interval_and_test_are_dual():
    rng = np.random.default_rng(1)
    x, y = _data(0.6, 25, rng)
    fit = fit_rma(x, y)
    low, high = rma_inference(x, y, fit, 0.9, 1)["magnitude_interval"]
    for k in (low, high):
        assert math.isclose(rma_inference(x, y, fit, 0.9, k)["magnitude_test"]["p_value"], 0.1, abs_tol=1e-10)
    assert rma_inference(x, y, fit, 0.9, (low + high) / 2)["magnitude_test"]["p_value"] > 0.1
    assert rma_inference(x, y, fit, 0.9, high * 1.01)["magnitude_test"]["p_value"] < 0.1


@pytest.mark.parametrize("rho", [0.9, 0.3, 0.05, -0.05, -0.6])
def test_magnitude_interval_covers_at_every_correlation(rho):
    rng = np.random.default_rng(int(1000 * (rho + 1)))
    covered, wrong_direction, datasets = 0, 0, 2000
    for _ in range(datasets):
        x, y = _data(rho, 20, rng)
        fit = fit_rma(x, y)
        inference = rma_inference(x, y, fit, 0.95, 1)
        low, high = inference["magnitude_interval"]
        covered += low <= 1 <= high
        claimed = inference["direction_test"]["direction"]
        wrong_direction += claimed != "not_established" and (claimed == "positive") != (rho > 0)
    band = 3.29 * math.sqrt(0.95 * 0.05 / datasets)
    assert abs(covered / datasets - 0.95) < band
    assert wrong_direction / datasets < 0.025 + band


def test_refusals_before_any_bundle(tmp_path):
    with pytest.raises(AnalysisError) as caught:
        rma_regression([1, 2], [2, 3], transform="none", missing="error",
                       inference={"confidence": 0.95, "null_magnitude": 1})
    assert caught.value.code == "inference_unavailable"
    with pytest.raises(AnalysisError) as caught:
        rma_regression([1, 2, 3, 4], [2, 4, 6, 8], transform="none", missing="error",
                       inference={"confidence": 0.95, "null_magnitude": 1})
    assert caught.value.code == "degenerate_inference"


@pytest.mark.parametrize("field, update", [
    ("inference", lambda r: r["inference"]["magnitude_interval"].__setitem__(1, r["inference"]["magnitude_interval"][1] * 1.01)),
    ("inference", lambda r: r["inference"]["direction_test"].update(direction="not_established")),
    ("ranges", lambda r: r["x_raw_range"].__setitem__(1, r["x_raw_range"][1] + 1)),
    ("fit", lambda r: r.update(slope=r["slope"] * 1.001)),
])
def test_rehashed_results_must_recompute_from_pairs(tmp_path, field, update):
    source = tmp_path / "m.dat"
    source.write_text(".\tx\ty\na\t1\t2.1\nb\t2\t3.9\nc\t3\t6.2\nd\t4\t7.7\ne\t5.5\t11\n")
    outcome = run({"method": "rma", "input": str(source), "format": "past", "x": "x", "y": "y", "transform": "log10",
                   "missing": "error", "inference": {"confidence": 0.95, "null_magnitude": 1}}, tmp_path / "runs")
    path = Path(outcome["run_dir"]) / "results.json"
    result = json.loads(path.read_text())
    update(result)
    path.write_text(json.dumps(result, indent=2) + "\n")
    rehash(outcome["run_dir"], "results.json")
    with pytest.raises(AnalysisError) as caught:
        inspect_run(outcome["run_dir"])
    assert caught.value.code == "invalid_bundle"


@pytest.mark.parametrize("change", ["threshold", "zero", "tiny_positive"])
def test_probability_consistency_survives_rehashed_tables(tmp_path, change):
    source = tmp_path / "m.dat"
    if change == "threshold":
        source.write_text(".\tx\ty\na\t-2\t-1\nb\t-1\t-2\nc\t0\t0\nd\t1\t2\ne\t2\t1\n")
        confidence = 1 - 0.10408803866222782
    else:
        source.write_text(".\tx\ty\n" + "".join(f"s{i}\t{i}\t{i + 0.01 * (i % 3)}\n" for i in range(1, 25)))
        confidence = 0.95
    directory = Path(run({"method": "rma", "input": str(source), "format": "past", "x": "x", "y": "y",
                          "transform": "none", "missing": "error",
                          "inference": {"confidence": confidence, "null_magnitude": 1}}, tmp_path / "runs")["run_dir"])
    result = json.loads((directory / "results.json").read_text())
    record = result["inference"]["direction_test"]
    if change == "threshold":
        assert record["direction"] == "positive"
        record["p_value"] += 8e-13
    elif change == "zero":
        assert 0 < record["p_value"] < 1e-12
        record["p_value"] = 0.0
    else:
        assert 0 < record["p_value"] < 1e-12
        record["p_value"] *= 2
    (directory / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    rehash(directory, "results.json")
    for name, data in table_files(result).items():
        (directory / name).write_bytes(data)
        rehash(directory, name)
    with pytest.raises(AnalysisError) as caught:
        inspect_run(directory)
    assert caught.value.code == "invalid_bundle"
