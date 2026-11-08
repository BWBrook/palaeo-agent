"""Community comparisons with independently generated R references."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from palaeo_agent.community import CommunitySpec, analyse_community, calculate_community


ROOT = Path(__file__).resolve().parents[1]


BASE_R_REFERENCE = json.loads((ROOT / "benchmarks/past/references/community-base-r.json").read_text())


@pytest.mark.parametrize("reference", BASE_R_REFERENCE["cases"], ids=lambda r: f"{r['transform']}-{r['distance']}")
def test_community_matches_base_r_library_reference(reference):
    path = ROOT / BASE_R_REFERENCE["input"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == BASE_R_REFERENCE["input_sha256"]
    spec = CommunitySpec(method="community", input=path, format="past",
                         orientation="taxa_by_samples", value_type="count",
                         transform=reference["transform"], distance=reference["distance"],
                         dimensions=2, missing="error", empty_samples="error")
    result = calculate_community(spec, data)
    assert result["sample_ids"] == reference["sample_ids"]
    assert result["taxon_ids"] == reference["taxon_ids"]
    for actual, expected in zip(result["diversity"], reference["diversity"], strict=True):
        assert actual["sample_id"] == expected["sample_id"]
        for key in ("total", "richness", "shannon", "simpson"):
            assert actual[key] == pytest.approx(expected[key], rel=BASE_R_REFERENCE["rtol"], abs=BASE_R_REFERENCE["atol"])
    for field in ("distances", "eigenvalues", "positive_gram"):
        np.testing.assert_allclose(result[field], reference[field],
                                   rtol=BASE_R_REFERENCE["rtol"], atol=BASE_R_REFERENCE["atol"])


VEGAN_REFERENCE = json.loads((ROOT / "references/r/community-vegan.json").read_text())


TOLERANCE = 1e-10


def nonnull(eigenvalues, scale):
    values = np.asarray(eigenvalues, dtype=float)
    return np.sort(values[np.abs(values) > 1e-8 * scale])[::-1]


@pytest.fixture(scope="module")
def data():
    data = (ROOT / VEGAN_REFERENCE["input"]["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == VEGAN_REFERENCE["input"]["sha256"]
    return data


@pytest.mark.parametrize("case", VEGAN_REFERENCE["cases"].values(), ids=lambda case: case["id"])
def test_community_matches_vegan(case, data):
    spec = CommunitySpec(method="community", input=ROOT / VEGAN_REFERENCE["input"]["path"], format="past",
                         orientation=VEGAN_REFERENCE["input"]["orientation"], value_type="count",
                         transform=case["transform"], distance=case["distance"],
                         dimensions=VEGAN_REFERENCE["dimensions"], missing="error", empty_samples="error")
    result = calculate_community(spec, data)
    assert result["sample_ids"] == VEGAN_REFERENCE["sample_ids"]
    assert result["taxon_ids"] == VEGAN_REFERENCE["taxon_ids"]
    for actual, expected in zip(result["diversity"], VEGAN_REFERENCE["diversity"], strict=True):
        assert actual["sample_id"] == expected["sample_id"]
        assert actual["richness"] == expected["richness"]
        for key in ("total", "shannon", "simpson"):
            assert actual[key] == pytest.approx(expected[key], rel=TOLERANCE, abs=TOLERANCE)
    np.testing.assert_allclose(result["distances"], case["distances"], rtol=TOLERANCE, atol=TOLERANCE)

    # vegan drops the structural null eigenvalue of double centring; compare the non-null spectrum.
    scale = max(np.abs(result["eigenvalues"]).max(), np.abs(case["eigenvalues"]).max())
    ours, theirs = nonnull(result["eigenvalues"], scale), nonnull(case["eigenvalues"], scale)
    assert len(ours) == len(theirs)
    np.testing.assert_allclose(ours, theirs, rtol=0, atol=TOLERANCE * scale)
    assert len(result["negative_eigenvalues"]) == int(np.sum(theirs < 0))
    np.testing.assert_allclose(result["positive_gram"], case["positive_gram"], rtol=0, atol=TOLERANCE * scale)

    assert result["eigenvalues"][1] - result["eigenvalues"][2] > 0
    gap = (result["eigenvalues"][1] - result["eigenvalues"][2]) / result["eigenvalues"][0]
    assert gap == pytest.approx(case["relative_eigengap"], rel=1e-8)
    assert case["selected_gram"] is not None
    coordinates = np.asarray(result["coordinates"])
    np.testing.assert_allclose(coordinates @ coordinates.T, case["selected_gram"], rtol=0, atol=TOLERANCE * scale)


def test_raw_braycurtis_respects_total_imbalance_bound(data):
    case = VEGAN_REFERENCE["cases"]["braycurtis_none"]
    totals = np.asarray([row["total"] for row in VEGAN_REFERENCE["diversity"]])
    bound = np.abs(totals[:, None] - totals[None, :]) / (totals[:, None] + totals[None, :])
    assert np.all(np.asarray(case["distances"]) >= bound - 1e-12)


def pair(matrix, transform, distance):
    # A third, all-taxa sample keeps the ordination nondegenerate when the controlled pair has distance 0.
    width = len(matrix[0])
    result = analyse_community([*matrix, [1] * width], sample_ids=["a", "b", "c"],
                               taxon_ids=[f"t{i}" for i in range(width)],
                               transform=transform, distance=distance, dimensions=1, empty_samples="error")
    return result["distances"][0][1]


@pytest.mark.parametrize("name, field, transform, distance", [
    ("disjoint_supports", "bray", "none", "braycurtis"),
    ("disjoint_supports", "jaccard_binary", "none", "jaccard"),
    ("proportional_rows", "bray_relative", "relative_abundance", "braycurtis"),
    ("proportional_rows", "bray_raw", "none", "braycurtis"),
])
def test_analytical_controls_agree_with_vegan_and_theory(name, field, transform, distance):
    control = VEGAN_REFERENCE["analytical_controls"][name]
    expected = control["expected_" + field.removesuffix("_binary")]
    assert control[field] == pytest.approx(expected, abs=1e-14)
    assert pair(control["matrix"], transform, distance) == pytest.approx(expected, abs=1e-14)
