"""Comparison with the committed, independently generated vegan reference (references/r)."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from palaeo_agent.community import CommunitySpec, analyse_community, calculate_community


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "references/r/community-vegan.json").read_text())
TOLERANCE = 1e-10


def nonnull(eigenvalues, scale):
    values = np.asarray(eigenvalues, dtype=float)
    return np.sort(values[np.abs(values) > 1e-8 * scale])[::-1]


@pytest.fixture(scope="module")
def data():
    data = (ROOT / REFERENCE["input"]["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == REFERENCE["input"]["sha256"]
    return data


@pytest.mark.parametrize("case", REFERENCE["cases"].values(), ids=lambda case: case["id"])
def test_community_matches_vegan(case, data):
    spec = CommunitySpec(method="community", input=ROOT / REFERENCE["input"]["path"], format="past",
                         orientation=REFERENCE["input"]["orientation"], value_type="count",
                         transform=case["transform"], distance=case["distance"],
                         dimensions=REFERENCE["dimensions"], missing="error", empty_samples="error")
    result = calculate_community(spec, data)
    assert result["sample_ids"] == REFERENCE["sample_ids"]
    assert result["taxon_ids"] == REFERENCE["taxon_ids"]
    for actual, expected in zip(result["diversity"], REFERENCE["diversity"], strict=True):
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
    case = REFERENCE["cases"]["braycurtis_none"]
    totals = np.asarray([row["total"] for row in REFERENCE["diversity"]])
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
    control = REFERENCE["analytical_controls"][name]
    expected = control["expected_" + field.removesuffix("_binary")]
    assert control[field] == pytest.approx(expected, abs=1e-14)
    assert pair(control["matrix"], transform, distance) == pytest.approx(expected, abs=1e-14)
