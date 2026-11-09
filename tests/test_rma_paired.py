"""Paired RMA bootstrap: independent recomputation, controls, refusals and bundle binding."""

import json
import math
from pathlib import Path

import numpy as np
import pytest

from palaeo_agent import AnalysisError, inspect_run, reproduce, run
from palaeo_agent import rma_paired as module
from palaeo_agent.methods import table_files
from palaeo_agent.rma_paired import RmaPairedSpec, calculate_rma_paired

N = 24


def table(tmp_path, rows=None):
    if rows is None:
        rng = np.random.default_rng(24)
        length = np.exp(rng.normal(2.3, 0.35, N))
        width = length ** 1.04 * np.exp(rng.normal(0, 0.07, N))
        rows = [(f"s{i + 1}", length[i], width[i], length[i] * np.exp(rng.normal(0, 0.03)),
                 width[i] * np.exp(rng.normal(0, 0.06))) for i in range(N)]
    lines = [".\tL\tW\tL2\tW2"] + ["\t".join([str(row[0]), *[f"{value:.4f}" for value in row[1:]]]) for row in rows]
    path = tmp_path / "m.dat"
    path.write_text("\n".join(lines) + "\n")
    return path


def spec(path, a=("L", "W"), b=("L2", "W2"), replicates=999, seed=7, **changes):
    return {"method": "rma_paired", "input": str(path), "format": "past", "a": {"x": a[0], "y": a[1]},
            "b": {"x": b[0], "y": b[1]}, "transform": "log10", "missing": "error",
            "bootstrap": {"replicates": replicates, "seed": seed, "confidence": 0.95}, **changes}


def compute(request):
    parsed = RmaPairedSpec.model_validate(request)
    return calculate_rma_paired(parsed, Path(request["input"]).read_bytes())


def plain_slope(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x) / (n - 1)
    syy = sum((v - my) ** 2 for v in y) / (n - 1)
    sxy = sum((u - mx) * (v - my) for u, v in zip(x, y))
    return math.copysign(math.sqrt(syy) / math.sqrt(sxx), sxy)


def test_replicates_recompute_independently_and_replay(tmp_path):
    request = spec(table(tmp_path))
    result = compute(request)
    pairs = result["pairs"]
    index = np.random.Generator(np.random.PCG64(7)).integers(0, N, size=(999, N), dtype=np.int64)
    for r in range(0, 999, 37):
        rows = [pairs[i] for i in index[r]]
        for fit in ("a", "b"):
            expected = plain_slope([p[f"{fit}_x"] for p in rows], [p[f"{fit}_y"] for p in rows])
            assert math.isclose(result["bootstrap"][f"slope_{fit}"][r], expected, rel_tol=1e-12)
    d = np.asarray(result["bootstrap"]["difference"])
    assert result["bootstrap"]["interval"] == pytest.approx(np.quantile(d, [0.025, 0.975]), rel=1e-15)
    assert compute(request) == result


def test_identity_and_swap_controls(tmp_path):
    path = table(tmp_path)
    identity = compute(spec(path, b=("L", "W")))["bootstrap"]
    assert identity["interval"] == [0.0, 0.0] and identity["standard_error"] == 0.0
    assert identity["resolution"] == "zero_included"
    forward, swapped = compute(spec(path)), compute(spec(path, a=("L2", "W2"), b=("L", "W")))
    assert swapped["difference"] == -forward["difference"]
    assert swapped["bootstrap"]["interval"] == pytest.approx([-v for v in reversed(forward["bootstrap"]["interval"])])
    assert swapped["bootstrap"]["standard_error"] == pytest.approx(forward["bootstrap"]["standard_error"])
    shared = compute(spec(path, b=("L", "W2")))
    assert shared["fit_b"]["x"] == shared["fit_a"]["x"] == "L"


def test_degenerate_draws_are_refused_not_dropped(tmp_path):
    rows = [(f"s{i}", 10.0, 8.0, 10.0, 8.0) for i in range(20)] + [("odd", 20.0, 17.0, 20.0, 17.0)]
    with pytest.raises(AnalysisError) as caught:
        compute(spec(table(tmp_path, rows)))
    assert caught.value.code == "degenerate_bootstrap"
    assert caught.value.details["undefined"]["a"]["zero_variance"] > 0


def test_budget_is_refused_before_allocation(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "bootstrap_slopes", lambda *a, **k: pytest.fail("bootstrap allocated"))
    with pytest.raises(AnalysisError) as caught:
        compute(spec(table(tmp_path), replicates=100_000))
    assert caught.value.code == "resource_limit"


def test_bundle_inspects_and_reproduces(tmp_path):
    outcome = run(spec(table(tmp_path)), tmp_path / "runs")
    assert inspect_run(outcome["run_dir"])["status"] == "verified"
    assert reproduce(outcome["run_dir"], tmp_path / "again")["status"] == "reproduced"


@pytest.mark.parametrize("update", [
    lambda r: r["bootstrap"]["difference"].__setitem__(3, r["bootstrap"]["difference"][3] + 1e-6),
    lambda r: r["bootstrap"]["interval"].__setitem__(0, r["bootstrap"]["interval"][0] - 1e-3),
    lambda r: r["pairs"][0].update(a_y_raw=r["pairs"][0]["a_y_raw"] * 1.01),
])
def test_rehashed_tampering_with_refreshed_tables_fails(tmp_path, update):
    from bundle_helpers import rehash
    run_dir = Path(run(spec(table(tmp_path)), tmp_path / "runs")["run_dir"])
    result = json.loads((run_dir / "results.json").read_text())
    update(result)
    (run_dir / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    rehash(run_dir, "results.json")
    for name, data in table_files(result).items():
        (run_dir / name).write_bytes(data)
        rehash(run_dir, name)
    with pytest.raises(AnalysisError) as caught:
        inspect_run(run_dir)
    assert caught.value.code == "invalid_bundle"
