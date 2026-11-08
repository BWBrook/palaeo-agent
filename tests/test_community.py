import json
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from palaeo_agent import AnalysisError, run
from palaeo_agent.community import (
    CommunityResult, CommunitySpec, analyse_community, calculate_community,
    selected_subspace_info, validate_community,
)

from abundance_helpers import (
    ABUNDANCE_COMMUNITY, ABUNDANCE_PERMANOVA, ABUNDANCE_TABLE,
    abundance_table,
)


def analyse(matrix=None, **changes):
    matrix = matrix if matrix is not None else [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
    options = {"sample_ids": ["a", "b", "c"], "taxon_ids": ["x", "y", "z"],
               "transform": "none", "distance": "braycurtis", "dimensions": 2,
               "empty_samples": "error", **changes}
    return analyse_community(matrix, **options)


def specification(**changes):
    return CommunitySpec.model_validate({"method": "community", "input": "dummy.dat", "format": "past",
        "orientation": "samples_by_taxa", "value_type": "count", "transform": "none",
        "distance": "braycurtis", "dimensions": 2, "missing": "error", "empty_samples": "error", **changes})


def test_exact_diversity_and_distances():
    result = analyse([[2, 2, 0], [0, 4, 0], [0, 0, 4]])
    first = result["diversity"][0]
    assert first == {"sample_id": "a", "total": 4, "richness": 2,
                     "shannon": pytest.approx(np.log(2)), "simpson": 0.5}
    np.testing.assert_allclose(result["distances"], [[0, 0.5, 1], [0.5, 0, 1], [1, 1, 0]])
    assert result["diversity"][1]["shannon"] == 0
    assert result["diversity"][1]["simpson"] == 0


def test_jaccard_is_binary_not_quantitative():
    result = analyse([[1, 1, 0], [0, 9, 0], [0, 0, 5]], distance="jaccard")
    np.testing.assert_allclose(result["distances"], [[0, 0.5, 1], [0.5, 0, 1], [1, 1, 0]])
    scaled = analyse([[10, 10, 0], [0, 1, 0], [0, 0, 90]], distance="jaccard")
    np.testing.assert_array_equal(result["distances"], scaled["distances"])


def test_transform_is_explicit_and_does_not_change_raw_diversity():
    matrix = [[2, 2, 0], [1, 1, 0], [0, 0, 5]]
    raw = analyse(matrix, dimensions=1)
    relative = analyse(matrix, dimensions=1, transform="relative_abundance")
    assert raw["distances"][0][1] == pytest.approx(1 / 3)
    assert relative["distances"][0][1] == 0
    assert raw["diversity"] == relative["diversity"]
    np.testing.assert_allclose(np.sum(relative["transformed_matrix"], axis=1), 1)
    assert raw["retained_counts"] == relative["retained_counts"]


def test_pcoa_geometry_for_equilateral_three_points():
    result = analyse()
    points = np.array(result["coordinates"])
    gram = points @ points.T
    np.testing.assert_allclose(gram, (np.eye(3) - np.ones((3, 3)) / 3) / 2, atol=1e-14)
    np.testing.assert_allclose(result["eigenvalues"], [0.5, 0.5, 0], atol=1e-14)
    np.testing.assert_allclose(result["axis_positive_inertia"], [0.5, 0.5])
    np.testing.assert_allclose(result["positive_gram"], gram, atol=1e-14)


def test_full_positive_geometry_allows_rotations_inside_a_retained_tied_block():
    result = analyse_community(np.eye(4), sample_ids=["a", "b", "c", "d"],
                               taxon_ids=["w", "x", "y", "z"], transform="none",
                               distance="braycurtis", dimensions=3, empty_samples="error")
    expected = (np.eye(4) - np.ones((4, 4)) / 4) / 2
    np.testing.assert_allclose(result["positive_gram"], expected, atol=1e-14)
    rotation = np.array([[0., -1, 0], [1, 0, 0], [0, 0, 1]])
    result["coordinates"] = (np.asarray(result["coordinates"]) @ rotation).tolist()
    CommunityResult.model_validate(result)
    result["coordinates"][0][0] += 0.1
    with pytest.raises(ValidationError, match="Coordinates"):
        CommunityResult.model_validate(result)


def test_equilateral_c04_cutoff_refuses_one_axis_and_allows_two():
    with pytest.raises(AnalysisError, match="numerically unresolved") as caught:
        analyse(dimensions=1)
    assert caught.value.code == "nonidentifiable_axes"
    details = caught.value.details
    assert details["requested_dimensions"] == 1
    assert details["positive_rank"] == 2
    assert details["allowed_identifiable_dimensions"] == [2]
    assert details["largest_allowed_dimensions_at_or_below_requested"] == 0
    assert details["relative_cutoff_gap"] <= details["threshold"]
    assert len(details["eigenvalues"]) == 3
    assert analyse(dimensions=2)["dimensions"] == 2


def test_subspace_rule_allows_internal_ties_and_full_positive_rank():
    internal = selected_subspace_info([3, 3, 1, 0], 2, 1e-14)
    assert internal["identifiable"] is True
    assert internal["allowed_identifiable_dimensions"] == [2, 3]
    assert internal["largest_allowed_dimensions_at_or_below_requested"] == 2
    complete = selected_subspace_info([1, 1e-10, 0], 2, 1e-14)
    assert complete["positive_rank"] == 2
    assert complete["identifiable"] is True
    assert complete["relative_cutoff_gap"] is None


@pytest.mark.parametrize("second,identifiable", [
    (2.0, False),
    (float(np.nextafter(2.0, np.inf)), True),
    (float(np.nextafter(2.0, -np.inf)), False),
])
def test_selected_subspace_cutoff_threshold_is_strict(second, identifiable):
    info = selected_subspace_info([1e8, second, 1, 0], 2, 1e-14)
    assert info["threshold"] == 1e-8
    assert info["identifiable"] is identifiable
    assert (2 in info["allowed_identifiable_dimensions"]) is identifiable


def test_near_tied_positive_cutoff_is_refused():
    info = selected_subspace_info([1, 1 - 5e-9, 0], 1, 1e-14)
    assert info["identifiable"] is False
    assert info["allowed_identifiable_dimensions"] == [2]


def force_spectrum(monkeypatch, eigenvalues):
    original = np.linalg.eigh
    def eigendecomposition(matrix):
        _, eigenvectors = original(matrix)
        return np.asarray(eigenvalues, dtype=float), eigenvectors
    monkeypatch.setattr(np.linalg, "eigh", eigendecomposition)


def test_engine_rejects_near_tie_before_returning_coordinates(monkeypatch):
    force_spectrum(monkeypatch, [0, 0.5, 0.5 + 1e-9])
    with pytest.raises(AnalysisError) as caught:
        analyse(dimensions=1)
    assert caught.value.code == "nonidentifiable_axes"
    assert 0 < caught.value.details["relative_cutoff_gap"] < caught.value.details["threshold"]


def test_complete_retained_tied_block_allows_rotation_below_full_rank(monkeypatch):
    force_spectrum(monkeypatch, [0, 0.1, 0.5, 0.5])
    result = analyse_community(np.eye(4), sample_ids=["a", "b", "c", "d"],
                               taxon_ids=["w", "x", "y", "z"], transform="none",
                               distance="braycurtis", dimensions=2, empty_samples="error")
    angle = np.pi / 5
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    coordinates = np.asarray(result["coordinates"]) @ rotation
    assert not np.allclose(coordinates @ coordinates.T, result["positive_gram"])
    result["coordinates"] = coordinates.tolist()
    CommunityResult.model_validate(result)


def test_engine_and_saved_result_allow_full_rank_with_tiny_last_positive_axis(monkeypatch):
    force_spectrum(monkeypatch, [0, 1e-10, 1])
    result = analyse(dimensions=2)
    assert result["eigenvalues"][1] / result["eigenvalues"][0] < 1e-8
    CommunityResult.model_validate(result)


def test_engine_and_saved_result_share_strict_cutoff_threshold(monkeypatch):
    force_spectrum(monkeypatch, [0, 1, 2, 1e8])
    options = {"sample_ids": ["a", "b", "c", "d"], "taxon_ids": ["w", "x", "y", "z"],
               "transform": "none", "distance": "braycurtis", "empty_samples": "error"}
    result = analyse_community(np.eye(4), dimensions=3, **options)
    with pytest.raises(AnalysisError) as caught:
        analyse_community(np.eye(4), dimensions=2, **options)
    assert caught.value.code == "nonidentifiable_axes"
    assert caught.value.details["relative_cutoff_gap"] == caught.value.details["threshold"]
    result["dimensions"] = 2
    result["coordinates"] = [row[:2] for row in result["coordinates"]]
    result["axis_positive_inertia"] = result["axis_positive_inertia"][:2]
    with pytest.raises(ValidationError, match="numerically unresolved"):
        CommunityResult.model_validate(result)


def test_saved_result_cannot_cut_an_unresolved_positive_block():
    result = analyse()
    result["dimensions"] = 1
    result["coordinates"] = [row[:1] for row in result["coordinates"]]
    result["axis_positive_inertia"] = result["axis_positive_inertia"][:1]
    with pytest.raises(ValidationError, match="numerically unresolved"):
        CommunityResult.model_validate(result)


def test_full_positive_geometry_rejects_inconsistent_spectral_summary():
    result = analyse()
    result["positive_gram"][0][0] += 0.1
    with pytest.raises(ValidationError):
        CommunityResult.model_validate(result)


def test_ordination_records_material_negative_eigenvalues():
    path = Path(__file__).resolve().parents[1] / "benchmarks/past/legacy-data/llanvirn.dat"
    result = calculate_community(specification(orientation="taxa_by_samples"), path.read_bytes())
    assert result["n"] == 10 and result["n_taxa"] == 23
    assert len(result["eigenvalues"]) == 10
    assert result["negative_eigenvalues"]
    assert result["negative_inertia_magnitude"] > 0
    assert any(w["code"] == "negative_eigenvalues" for w in result["warnings"])
    assert all(v < -result["eigenvalue_tolerance"] for v in result["negative_eigenvalues"])


def test_explicit_orientation_and_metadata_reordering():
    data = b". a b c\nx 2 0 0\ny 0 2 0\nz 0 0 2\n"
    metadata = b"sample_id,site\nc,C\na,A\nb,B\n"
    result = calculate_community(specification(orientation="taxa_by_samples", metadata="meta.csv"), data, metadata)
    assert result["sample_ids"] == ["a", "b", "c"]
    assert result["taxon_ids"] == ["x", "y", "z"]
    assert [row["site"] for row in result["metadata"]] == ["A", "B", "C"]


def test_metadata_sets_checked_before_exclusions():
    data = [[2, 0, 0], [0, 2, 0], [0, 0, 2], [0, 0, 0]]
    with pytest.raises(AnalysisError) as caught:
        analyse_community(data, sample_ids=["a", "b", "c", "empty"], taxon_ids=["x", "y", "z"],
                          transform="none", distance="braycurtis", dimensions=2, empty_samples="drop",
                          metadata=[{"sample_id": name} for name in ["a", "b", "c"]])
    assert caught.value.code == "metadata_alignment"
    assert caught.value.details["missing"] == ["empty"]


def test_empty_sample_policy_preserves_omissions():
    with pytest.raises(AnalysisError) as caught:
        analyse([[2, 0, 0], [0, 2, 0], [0, 0, 0]], dimensions=1)
    assert caught.value.code == "empty_samples"
    result = analyse([[2, 0, 0], [0, 2, 0], [0, 0, 0]], dimensions=1, empty_samples="drop")
    assert result["sample_ids"] == ["a", "b"]
    assert result["input_sample_ids"] == ["a", "b", "c"]
    assert result["excluded"] == [{"sample_id": "c", "reason": "empty_sample"}]


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), -1, 0.2, True, "1", 2**53])
def test_invalid_count_never_becomes_missing_or_zero(value):
    with pytest.raises(AnalysisError) as caught:
        analyse([[2, 0, 0], [0, value, 0], [0, 0, 2]])
    assert caught.value.code == "invalid_count"


def test_count_totals_remain_exactly_representable():
    with pytest.raises(AnalysisError) as caught:
        analyse([[2**53 - 1, 1, 0], [0, 1, 0], [0, 0, 2]])
    assert caught.value.code == "count_range"


def test_duplicate_ids_fail_but_near_labels_warn_without_merging():
    with pytest.raises(AnalysisError) as caught:
        analyse(sample_ids=["a", "a", "c"])
    assert caught.value.code == "duplicate_id"
    result = analyse(taxon_ids=["Taxon", "taxon ", "z"])
    assert result["n_taxa"] == 3
    assert result["taxon_ids"] == ["Taxon", "taxon ", "z"]
    assert result["warnings"][0]["code"] == "near_duplicate_labels"
    unicode_result = analyse(taxon_ids=["Ａ", "A", "z"])
    assert unicode_result["taxon_ids"] == ["Ａ", "A", "z"]
    assert unicode_result["warnings"][0]["details"]["groups"] == [["Ａ", "A"]]


@pytest.mark.parametrize("body,changes,code", [
    (b". x y\na 1 .\nb 2 3", {}, "missing_counts"),
    (b". x x\na 1 2\nb 2 3", {}, "duplicate_id"),
    (b". x y\na 1\nb 2 3", {}, "row_width"),
    (b". x y\na 1 2\nb 2 3", {"metadata": "meta.csv"}, "metadata_input"),
    (b". x y\na 1.00000000000000001 2\nb 2 3", {}, "invalid_count"),
])
def test_past_structure_rejections(body, changes, code):
    with pytest.raises(AnalysisError) as caught:
        validate_community(specification(dimensions=1, **changes), body)
    assert caught.value.code == code


def test_validate_does_not_compute_eigenvalues(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("validation invoked eigendecomposition")
    monkeypatch.setattr(np.linalg, "eigh", forbidden)
    result = validate_community(specification(), b". x y z\na 1 0 0\nb 0 1 0\nc 0 0 1")
    assert result["status"] == "valid"


def test_positive_rank_and_sample_count_requirements():
    with pytest.raises(AnalysisError) as caught:
        analyse([[1, 0, 0], [1, 0, 0], [1, 0, 0]])
    assert caught.value.code == "insufficient_positive_axes"
    with pytest.raises(AnalysisError) as caught:
        analyse([[1, 0, 0], [0, 1, 0]], sample_ids=["a", "b"])
    assert caught.value.code == "insufficient_samples"
    with pytest.raises(AnalysisError) as caught:
        analyse_community([], sample_ids=[], taxon_ids=["x"], transform="none",
                          distance="braycurtis", dimensions=1, empty_samples="error")
    assert caught.value.code == "insufficient_samples"


def test_pairwise_memory_guard_precedes_allocation(monkeypatch):
    from palaeo_agent import community
    monkeypatch.setattr(community, "MAX_MATRIX_BYTES", 1)
    with pytest.raises(AnalysisError) as caught:
        analyse()
    assert caught.value.code == "resource_limit"


@pytest.mark.parametrize("mutate", [
    lambda r: r["sample_ids"].append("new"),
    lambda r: r["distances"][0].pop(),
    lambda r: r["coordinates"][0].append(0.0),
    lambda r: r["retained_counts"][0].__setitem__(0, 0.5),
    lambda r: r["eigenvalues"].reverse(),
    lambda r: r["diversity"][0].__setitem__("shannon", float("nan")),
])
def test_saved_result_schema_rejects_malformed_structure(mutate):
    result = analyse()
    mutate(result)
    with pytest.raises(ValidationError):
        CommunityResult.model_validate_json(json.dumps(result))


def test_schema_forbids_undeclared_options_and_noncount_semantics():
    with pytest.raises(ValidationError):
        specification(value_type="proportion")
    with pytest.raises(ValidationError):
        specification(normalize=True)
    with pytest.raises(ValidationError):
        specification(dimensions=True)
    with pytest.raises(ValidationError, match="unsupported no-op"):
        specification(distance="jaccard", transform="relative_abundance")
    with pytest.raises(AnalysisError) as caught:
        analyse(distance="jaccard", transform="relative_abundance")
    assert caught.value.code == "unsupported_combination"


def abundance_community(data, **changes):
    return calculate_community(dict(ABUNDANCE_COMMUNITY, input="x.dat", **changes), data)


def test_abundance_community_labels_weights_honestly():
    result = abundance_community(abundance_table(ABUNDANCE_TABLE))
    assert result["value_type"] == "abundance" and "retained_counts" not in result
    assert result["retained_values"][0] == [50.5, 30.25, 19.25]
    row = result["diversity"][0]
    assert "total" not in row and row["weight_sum"] == 100 and row["richness"] == 3
    p = np.array([50.5, 30.25, 19.25]) / 100
    assert row["shannon"] == pytest.approx(-(p * np.log(p)).sum(), rel=1e-12)
    assert row["simpson"] == pytest.approx(1 - (p**2).sum(), rel=1e-12)
    assert any("weights carry no specimen counts" in item for item in result["limitations"])


def test_common_factor_leaves_distances_and_diversity_unchanged():
    base = abundance_community(abundance_table(ABUNDANCE_TABLE))
    scaled = abundance_community(abundance_table(ABUNDANCE_TABLE, [0.01] * 6))
    assert np.allclose(base["distances"], scaled["distances"], rtol=0, atol=1e-12)
    for key in ("richness", "shannon", "simpson"):
        assert [r[key] for r in base["diversity"]] == pytest.approx([r[key] for r in scaled["diversity"]], rel=1e-12)


def test_row_specific_scaling_affects_raw_braycurtis_only_before_closure():
    factors = [1, 2, 0.5, 3, 1, 0.25]
    raw = (abundance_community(abundance_table(ABUNDANCE_TABLE)), abundance_community(abundance_table(ABUNDANCE_TABLE, factors)))
    assert not np.allclose(raw[0]["distances"], raw[1]["distances"])
    closed = [abundance_community(abundance_table(ABUNDANCE_TABLE, f), transform="relative_abundance") for f in (None, factors)]
    assert np.allclose(closed[0]["distances"], closed[1]["distances"], rtol=0, atol=1e-12)
    jaccard = [abundance_community(abundance_table(ABUNDANCE_TABLE, f), distance="jaccard", dimensions=1) for f in (None, factors)]
    assert jaccard[0]["distances"] == jaccard[1]["distances"]


@pytest.mark.parametrize("token", ["-1", "inf", "NaN", "1e-400", "1e400", "abc"])
def test_unsupported_abundance_tokens_are_refused(token):
    with pytest.raises(AnalysisError) as error:
        abundance_community(abundance_table(ABUNDANCE_TABLE.replace("50.5", token)))
    assert error.value.code == "invalid_abundance"


def test_empty_abundance_rows_follow_the_policy():
    data = abundance_table(ABUNDANCE_TABLE.replace("S3\t0\t80.5\t19.5", "S3\t0\t0\t0.0"))
    with pytest.raises(AnalysisError) as error:
        abundance_community(data)
    assert error.value.code == "empty_samples"
    assert [e["sample_id"] for e in abundance_community(data, empty_samples="drop")["excluded"]] == ["S3"]


def test_count_input_still_refuses_fractions_and_points_to_abundance():
    with pytest.raises(AnalysisError) as error:
        abundance_community(abundance_table(ABUNDANCE_TABLE), value_type="count")
    assert error.value.code == "invalid_count" and "abundance" in error.value.args[0]


OVERFLOW = ".\tA\tB\nx\t1e308\t0\ny\t1e308\t1e307\nz\t0\t1\n"


@pytest.mark.parametrize("entry", ["validate", "run"])
@pytest.mark.parametrize("table", [OVERFLOW, ".\tA\tB\nx\t1e308\t1e308\ny\t1\t2\nz\t2\t1\n"])
def test_abundance_range_is_refused_in_validation_and_execution(tmp_path, entry, table):
    from palaeo_agent import validate
    (tmp_path / "o.dat").write_text(table)
    spec = dict(ABUNDANCE_COMMUNITY, input=str(tmp_path / "o.dat"), dimensions=1)
    for method_spec in (spec, dict(ABUNDANCE_PERMANOVA, input=spec["input"], transform="none", metadata=None)):
        method_spec = {k: v for k, v in method_spec.items() if v is not None}
        if method_spec["method"] == "permanova":
            (tmp_path / "m.csv").write_text("sample_id,band\nx,a\ny,a\nz,b\n")
            method_spec["metadata"] = str(tmp_path / "m.csv")
        with pytest.raises(AnalysisError) as error:
            validate(method_spec) if entry == "validate" else run(method_spec, tmp_path / f"out-{method_spec['method']}")
        assert error.value.code == "abundance_range"


def test_rescaled_overflow_table_gives_the_exact_distance():
    rescaled = abundance_community(OVERFLOW.replace("1e308", "1").replace("1e307", "0.1").replace("z\t0\t1", "z\t0\t1e-308").encode(),
                          dimensions=1)
    assert rescaled["distances"][0][1] == pytest.approx(1 / 21, rel=1e-15)


def test_community_distances_refuses_rows_outside_the_range():
    from palaeo_agent.community import community_distances
    with pytest.raises(AnalysisError) as error:
        community_distances(np.array([[1e308, 0.0], [1e308, 1e307], [0.0, 1.0]]), transform="none", distance="braycurtis")
    assert error.value.code == "abundance_range"


def test_native_positive_weights_may_not_underflow_or_overflow():
    from fractions import Fraction
    from palaeo_agent import analyse_community
    common = dict(sample_ids=["A", "B", "C"], taxon_ids=["x", "y", "z"], value_type="abundance", transform="none",
                  distance="jaccard", dimensions=1, empty_samples="error")
    for tiny in (Fraction(1, 10**400), Fraction(10**400)):
        with pytest.raises(AnalysisError) as error:
            analyse_community([[tiny, 1, 0], [1, 0, 0], [0, 1, 1]], **common)
        assert error.value.code == "invalid_abundance"
    with pytest.raises(AnalysisError) as error:
        analyse_community([[1e308, 1e308, 0], [1, 0, 0], [0, 1, 1]], **common)
    assert error.value.code == "abundance_range"
    ok = analyse_community([[Fraction(1, 10**300), 1, 0], [1, 0, 0], [0, 1, 1]], **common)
    assert ok["diversity"][0]["richness"] == 2 and ok["distances"][0][1] == 0.5
