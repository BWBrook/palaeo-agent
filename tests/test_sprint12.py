import json
import math
from fractions import Fraction
from pathlib import Path

import pytest

from palaeo_agent import inspect_run, run
from palaeo_agent.count_homogeneity import _fisher


def _exact_log10_p(xa, na, xb, nb):
    """Exact two-sided Fisher p in integers (SciPy's 1e-7 relative tie tolerance), as log10."""
    total, column = na + nb, xa + xb
    denominator = math.comb(total, na)
    lo, hi = max(0, na - (total - column)), min(column, na)
    masses = {k: math.comb(column, k) * math.comb(total - column, na - k) for k in range(lo, hi + 1)}
    threshold = Fraction(masses[xa]) * (1 + Fraction(1, 10**7))
    numerator = sum(m for m in masses.values() if m <= threshold)
    return math.log10(numerator) - math.log10(denominator)


@pytest.mark.parametrize("xa,na,xb,nb", [(0, 1226, 1110, 1714), (0, 1000, 990, 1000), (3, 900, 850, 1000)])
def test_underflowed_fisher_values_are_flagged_and_bracketed(xa, na, xb, nb):
    p, underflow, bounds = _fisher(xa, na, xb, nb)
    exact = _exact_log10_p(xa, na, xb, nb)
    assert exact < -307.6 and p == 0.0 and underflow
    assert bounds == pytest.approx(exact, abs=1e-9)


@pytest.mark.parametrize("xa,na,xb,nb", [(5, 500, 20, 500), (0, 100, 3, 100), (40, 532, 60, 540)])
def test_ordinary_fisher_values_carry_no_bounds(xa, na, xb, nb):
    p, underflow, bounds = _fisher(xa, na, xb, nb)
    assert p > 0 and not underflow and bounds is None
    assert math.log10(p) == pytest.approx(_exact_log10_p(xa, na, xb, nb), abs=1e-9)


def _bundle(tmp_path):
    (tmp_path / "t.dat").write_text(".\tA\tB\tC\nS1\t0\t600\t626\nS2\t1110\t300\t304\nS3\t10\t500\t520\n")
    spec = {"method": "count_homogeneity", "input": str(tmp_path / "t.dat"), "format": "past",
            "orientation": "samples_by_taxa", "value_type": "count", "missing": "error", "empty_samples": "error",
            "pairs": [["S1", "S2"], ["S1", "S3"]], "simulations": 999, "seed": 1}
    return run(spec, tmp_path / "out")["run_dir"]


def test_runs_record_underflow_and_inspection_recomputes_it(tmp_path):
    run_dir = _bundle(tmp_path)
    result = inspect_run(run_dir)["result"]
    assert result["method_version"] == 3
    tests = {(tuple(p["sample_ids"]), t["taxon_id"]): t for p in result["pairs"] for t in p["taxon_tests"]}
    flagged = tests[(("S1", "S2"), "A")]
    assert flagged["p_value"] == 0.0 and flagged["p_value_underflow"] and flagged["log10_p_value"] < -307
    assert not tests[(("S1", "S3"), "B")]["p_value_underflow"]
    header = (Path(run_dir) / "taxon_tests.csv").read_text().splitlines()[0]
    assert header.endswith("p_value_underflow,log10_p_value")


@pytest.mark.parametrize("tamper", [
    lambda t: t.update(p_value_underflow=False, log10_p_value=None),
    lambda t: t.update(log10_p_value=-1.0),
])
def test_rehashed_underflow_tampering_fails_inspection(tmp_path, tamper):
    from test_sprint10 import _rehash
    run_dir = _bundle(tmp_path)
    path = Path(run_dir) / "results.json"
    data = json.loads(path.read_text())
    tamper(next(t for p in data["pairs"] for t in p["taxon_tests"] if t["p_value_underflow"]))
    path.write_text(json.dumps(data, indent=2))
    _rehash(run_dir, "results.json")
    with pytest.raises(Exception):
        inspect_run(run_dir)
