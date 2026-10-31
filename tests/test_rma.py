from pathlib import Path
import json

import numpy as np
import pytest
from pydantic import ValidationError

from palaeo_agent import AnalysisError, RmaSpec, discover, rma_regression, validate


def fit(x, y, **kwargs):
    return rma_regression(x, y, transform="none", missing="error", **kwargs)


def test_exact_signed_lines_and_two_pairs():
    for sign in (1, -1):
        result = fit([1, 2, 3], [2 + sign * 3 * value for value in [1, 2, 3]])
        assert result["slope"] == pytest.approx(sign * 3)
        assert result["intercept"] == pytest.approx(2)
        assert result["correlation"] == pytest.approx(sign)
        assert result["vertical_residual_rmse"] == pytest.approx(0)
    two = fit([1, 2], [3, 7])
    assert two["slope"] == pytest.approx(4)
    assert two["warnings"][0]["code"] == "two_pairs"


def test_known_log_log_power_law():
    result = rma_regression([1, 10, 100], [10, 1000, 100000],
                            transform="log10", missing="error")
    assert result["slope"] == pytest.approx(2)
    assert result["intercept"] == pytest.approx(1)


def test_small_computed_correlation_is_a_numerical_diagnostic():
    result = fit([-1, 0, 1], [1, -2, 1 + 1e-10])
    assert 0 < abs(result["correlation"]) < 1e-8
    assert result["warnings"][0]["code"] == "small_computed_correlation"
    assert "not a statistical test" in result["warnings"][0]["message"]


def test_slope_magnitude_does_not_measure_association_strength():
    result = fit([-1, 0, 1], [1, -2, 1.1])
    assert 1e-8 < abs(result["correlation"]) < 0.1
    assert result["slope"] == pytest.approx(result["sd_y"] / result["sd_x"])
    assert result["warnings"] == []
    for limitations in (result["limitations"], discover()["methods"][0]["limitations"]):
        assert any("independent of correlation strength" in text for text in limitations)


def test_missing_requires_explicit_policy_and_preserves_ids():
    with pytest.raises(AnalysisError, match="drop_pairs") as caught:
        fit([1, None, 3], [2, 4, 6], sample_ids=["a", "b", "c"])
    assert caught.value.code == "missing_pairs"
    result = rma_regression([1, None, 3], [2, 4, 6], sample_ids=["a", "b", "c"],
                            transform="none", missing="drop_pairs")
    assert result["n"] == 2
    assert result["excluded"] == [{"sample_id": "b", "reason": "declared_missing_pair", "columns": ["x"]}]
    assert [row["sample_id"] for row in result["pairs"]] == ["a", "c"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "3", True, 10 ** 1000])
def test_nonfinite_and_nonnumeric_are_not_missing(value):
    with pytest.raises(AnalysisError) as caught:
        rma_regression([1, value, 3], [2, 4, 6], transform="none", missing="drop_pairs")
    assert caught.value.code == "invalid_numeric"


@pytest.mark.parametrize("x,y,code", [
    ([1], [2], "insufficient_pairs"),
    ([1, 1, 1], [1, 2, 3], "zero_variance"),
    ([-1, 0, 1], [1, 0, 1], "zero_covariance"),
    ([1, 2, 3], [1, 2], "pair_alignment"),
])
def test_undefined_fits_are_errors(x, y, code):
    with pytest.raises(AnalysisError) as caught:
        fit(x, y)
    assert caught.value.code == code


def test_log_positivity_and_unique_ids():
    with pytest.raises(AnalysisError) as caught:
        rma_regression([0, 1, 2], [1, 2, 3], transform="log10", missing="error")
    assert caught.value.code == "nonpositive_log"
    with pytest.raises(AnalysisError) as caught:
        fit([1, 2, 3], [2, 4, 6], sample_ids=["a", "a", "c"])
    assert caught.value.code == "duplicate_sample_id"


def spec(path, **changes):
    return RmaSpec.model_validate({"method": "rma", "input": str(path), "format": "past",
                                  "x": "x", "y": "y", "transform": "none", "missing": "error", **changes})


def test_schema_requires_scientific_options_and_forbids_unknowns():
    schema = discover()["methods"][0]["input_schema"]
    assert "transform" in schema["required"]
    assert "missing" in schema["required"]
    assert schema["additionalProperties"] is False
    output = discover()["methods"][0]["output_schema"]
    assert "pairs" in output["required"]
    assert output["additionalProperties"] is False
    with pytest.raises(ValidationError):
        spec("dummy.dat", magic=True)


@pytest.mark.parametrize("text,code", [
    (". x x\na 1 2\nb 2 3", "duplicate_column_id"),
    (". x y\na 1 2\na 2 4", "duplicate_sample_id"),
    (". x y\na 1\nb 2 4", "row_width"),
    (". x y\na nan 2\nb 2 4", "invalid_numeric"),
    (". x y\na 1 2\nb 2 4", "unknown_column"),
])
def test_past_structure_and_numeric_errors(tmp_path, text, code):
    path = tmp_path / "input.dat"
    path.write_text(text)
    request = spec(path, x="z") if code == "unknown_column" else spec(path)
    with pytest.raises(AnalysisError) as caught:
        validate(request)
    assert caught.value.code == code


def test_relabelled_pairs_preserve_fit():
    x = np.array([1.0, 2.5, 4.0, 5.0])
    y = np.array([2.0, 3.0, 7.0, 7.5])
    first = fit(x, y)
    other = fit(x[::-1], y[::-1], sample_ids=["d", "c", "b", "a"])
    assert first["slope"] == pytest.approx(other["slope"])
    assert first["intercept"] == pytest.approx(other["intercept"])


def test_dielasma_matches_independent_reference():
    path = Path(__file__).resolve().parents[1] / "benchmarks/past/legacy-data/dielasma.dat"
    if not path.exists():
        pytest.skip("Local benchmark corpus has not been extracted")
    from palaeo_agent.core import calculate
    references = json.loads((path.parent.parent / "references/dielasma-rma.json").read_text())
    for expected in references["cases"]:
        result = calculate(spec(path, x=expected["x"], y=expected["y"],
                                transform=expected["transform"], missing="drop_pairs"), path.read_bytes())
        assert result["n"] == expected["n"]
        assert [row["sample_id"] for row in result["pairs"]] == expected["retained_ids"]
        assert [row["sample_id"] for row in result["excluded"]] == expected["excluded_ids"]
        for field in ("slope", "intercept"):
            assert result[field] == pytest.approx(expected[field], rel=references["rtol"], abs=references["atol"])
