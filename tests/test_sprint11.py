import json
from pathlib import Path

import pytest
from scipy.stats import binom

from palaeo_agent import inspect_run, run
from palaeo_agent.permanova import _monte_carlo_fields
from test_sprint10 import META, PCT, PERMANOVA, _rehash, _table


@pytest.mark.parametrize("b,draws", [(0, 999), (999, 999), (49, 999), (687, 9999), (3, 99)])
def test_interval_meets_the_clopper_pearson_defining_tails(b, draws):
    fields = _monte_carlo_fields("monte_carlo", b, draws)
    lower, upper = fields["tail_probability_interval"]
    assert fields["interval_status"] == "clopper_pearson_draw_exceedances"
    assert lower == 0.0 if b == 0 else binom.sf(b - 1, draws, lower) == pytest.approx(0.025, rel=1e-9)
    assert upper == 1.0 if b == draws else binom.cdf(b, draws, upper) == pytest.approx(0.025, rel=1e-9)
    assert fields["monte_carlo_unresolved"] == (lower <= 0.05 <= upper)


def test_reported_application_interval_and_threshold_flags():
    assert _monte_carlo_fields("monte_carlo", 687, 9999)["tail_probability_interval"] == pytest.approx(
        [0.0638249554, 0.0738417566], abs=1e-10)
    assert _monte_carlo_fields("monte_carlo", 49, 999)["monte_carlo_unresolved"] is True
    assert _monte_carlo_fields("monte_carlo", 10, 999)["monte_carlo_unresolved"] is False
    assert _monte_carlo_fields("monte_carlo", 200, 999)["monte_carlo_unresolved"] is False


def test_exact_enumeration_marks_the_interval_inapplicable():
    fields = _monte_carlo_fields("exact", 3, 20)
    assert fields["tail_probability_interval"] is None and fields["monte_carlo_unresolved"] is None
    assert fields["interval_status"] == "not_applicable_exact_enumeration"


def _run(tmp_path, permutations):
    (tmp_path / "p.dat").write_bytes(_table(PCT))
    (tmp_path / "m.csv").write_text(META)
    spec = dict(PERMANOVA, input=str(tmp_path / "p.dat"), metadata=str(tmp_path / "m.csv"), permutations=permutations)
    return run(spec, tmp_path / "run")


@pytest.mark.parametrize("permutations,mode", [(9, "monte_carlo"), (999, "exact")])
def test_runs_record_the_interval_and_keep_the_p_value(tmp_path, permutations, mode):
    outcome = _run(tmp_path, permutations)
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
    outcome = _run(tmp_path, 9)
    results = Path(outcome["run_dir"]) / "results.json"
    data = json.loads(results.read_text())
    tamper(data["permutation"])
    results.write_text(json.dumps(data, indent=2))
    _rehash(outcome["run_dir"], "results.json")
    with pytest.raises(Exception):
        inspect_run(outcome["run_dir"])
