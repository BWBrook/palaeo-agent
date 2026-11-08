"""Known development comparisons with independently generated vegan references."""

from fractions import Fraction
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from palaeo_agent.permanova import PermanovaSpec, calculate_permanova


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "references/r/permanova-reference.json").read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(reference):
    path, metadata = ROOT / reference["input"], ROOT / reference["metadata"]
    assert digest(path) == reference["input_sha256"]
    assert digest(metadata) == reference["metadata_sha256"]
    permutation = reference["permutation"]
    assert digest(ROOT / permutation["schedule_path"]) == permutation["schedule_sha256"]
    spec = PermanovaSpec(method="permanova", input=path, metadata=metadata, group_column="group",
        format="past", orientation="samples_by_taxa", value_type="count", distance=reference["distance"],
        transform=reference["transform"], missing="error", empty_samples="error", design="independent",
        permutation_scheme="free", permutations=permutation["requested"], seed=permutation["seed"])
    return calculate_permanova(spec, path.read_bytes(), metadata.read_bytes())


@pytest.fixture(scope="module", params=REFERENCE["cases"], ids=lambda case: case["id"])
def comparison(request):
    return request.param, run_case(request.param)


def test_reference_provenance_is_current():
    assert REFERENCE["contract_commit"] == "2c335a7"
    assert digest(ROOT / "docs/permanova-contract.md") == REFERENCE["contract_sha256"]
    assert digest(ROOT / REFERENCE["generator"]) == REFERENCE["generator_sha256"]
    assert REFERENCE["packages"]["vegan"] == "2.7.6"


def test_observed_statistics_and_permutation_distribution_match_vegan(comparison):
    reference, result = comparison
    assert result["sample_ids"] == reference["sample_ids"]
    assert result["taxon_ids"] == reference["taxon_ids"]
    assert result["groups"] == reference["groups"]
    assert result["group_sizes"] == reference["group_sizes"]
    for field in ("pseudo_f", "r_squared", "ss_total", "ss_within", "ss_between"):
        assert result[field] == pytest.approx(reference["observed"][field], rel=REFERENCE["rtol"], abs=REFERENCE["atol"])
    for field in ("df_between", "df_within"):
        assert result[field] == reference["observed"][field]
    np.testing.assert_allclose(result["distances"], reference["distances"], rtol=REFERENCE["rtol"], atol=REFERENCE["atol"])
    actual, expected = result["permutation"], reference["permutation"]
    for field in ("mode", "requested", "draws", "space_size", "count_extreme", "denominator", "seed",
                  "bit_generator", "index_semantics", "indices", "statuses", "infinite_count", "tie_tolerance"):
        assert actual[field] == expected[field]
    finite = np.array(expected["statuses"]) == "finite"
    np.testing.assert_allclose(np.array(actual["statistics"], dtype=float)[finite],
        np.array(expected["statistics"], dtype=float)[finite], rtol=REFERENCE["rtol"], atol=REFERENCE["atol"])
    assert all(value is None for value, status in zip(actual["statistics"], actual["statuses"], strict=True)
               if status == "positive_infinity")
    assert result["p_value"] == pytest.approx(expected["p_value"], abs=1e-14)
    assert reference["native_adonis2"]["p_agrees_with_declared_counting"] is True
    assert result["p_value"] == pytest.approx(reference["native_adonis2"]["p_value"], abs=1e-14)


def test_centroid_dispersion_matches_declared_vegan_convention(comparison):
    reference, result = comparison
    expected, actual = reference["dispersion"], result["dispersion"]
    for field in ("type", "bias_adjust", "sqrt_dist", "add", "retained_positive_axes", "retained_negative_axes"):
        assert actual[field] == expected[field]
    assert actual["threshold"] == pytest.approx(expected["threshold"], rel=1e-14, abs=0)
    np.testing.assert_allclose(actual["eigenvalues"], expected["eigenvalues"], rtol=REFERENCE["rtol"], atol=REFERENCE["atol"])
    if expected["status"] == "native_betadisper_error":
        assert reference["id"] == "tiny4_bray_exact"
        assert reference["native_distance_observation"]["status"] == "zero_total_variation"
        expected = expected["zero_mode_contract_control"]
    for field in ("distances", "squared_distances"):
        np.testing.assert_allclose(actual[field], expected[field], rtol=REFERENCE["rtol"], atol=REFERENCE["atol"])
    assert actual["group_mean_distances"] == pytest.approx(expected["group_mean_distances"], rel=REFERENCE["rtol"], abs=REFERENCE["atol"])
    assert actual["negative_squared_count"] == expected["negative_squared_count"]
    assert actual["truncated_sample_ids"] == expected["truncated_sample_ids"]


def test_negative_centroid_control_agrees_with_exact_geometry():
    reference = next(case for case in REFERENCE["cases"] if case["id"] == "negative8_jaccard_exact")
    dispersion = reference["dispersion"]
    assert dispersion["squared_distances"][3] == pytest.approx(-1 / 48, abs=1e-14)
    assert dispersion["squared_distances"][7] == pytest.approx(-1 / 48, abs=1e-14)
    assert dispersion["negative_squared_count"] == 2
    assert dispersion["truncated_sample_ids"] == ["neg8_4", "neg8_8"]


def test_tiny_exact_rational_control_remains_distinct_from_vegan_zapping():
    reference = next(case for case in REFERENCE["cases"] if case["id"] == "tiny4_bray_exact")
    result = run_case(reference)
    values = [2**52 + i for i in range(4)]
    expected = np.array([[float(Fraction(abs(a - b), a + b)) for b in values] for a in values])
    np.testing.assert_allclose(result["distances"], expected, rtol=1e-14, atol=0)
    assert 0 < result["ss_total"] < 1e-30
    assert result["ss_total"] == pytest.approx(reference["observed"]["ss_total"], rel=1e-10, abs=0)
    assert result["pseudo_f"] == pytest.approx(8, rel=1e-12, abs=0)
    assert result["p_value"] == pytest.approx(1 / 3, abs=1e-14)
    assert np.max(np.abs(result["dispersion"]["eigenvalues"])) > 0
    assert result["dispersion"]["retained_positive_axes"] == 0
    assert result["dispersion"]["distances"] == [0.0] * 4
    native = reference["native_distance_observation"]
    assert native["documented_ZAP"] == 1e-15
    assert native["distances"] == [[0] * 4 for _ in range(4)]
