from copy import deepcopy
from fractions import Fraction
from itertools import combinations, permutations
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from palaeo_agent.core import AnalysisError
from palaeo_agent.permanova import (
    PermanovaResult, PermanovaSpec, TIE_TOLERANCE, calculate_permanova, validate_permanova,
)


def spec(**changes):
    return PermanovaSpec.model_validate({
        "method": "permanova", "input": "counts.dat", "metadata": "meta.csv", "group_column": "site",
        "format": "past", "orientation": "samples_by_taxa", "value_type": "count",
        "distance": "braycurtis", "transform": "none", "missing": "error", "empty_samples": "error",
        "design": "independent", "permutation_scheme": "free", "seed": 42, **changes,
    })


def payload(matrix, groups, *, metadata_order=None, orientation="samples_by_taxa"):
    ids = [f"s{i}" for i in range(len(matrix))]
    taxa = [f"t{i}" for i in range(len(matrix[0]))]
    if orientation == "samples_by_taxa":
        header, names, values = taxa, ids, matrix
    else:
        header, names, values = ids, taxa, list(map(list, zip(*matrix)))
    body = ". " + " ".join(header) + "\n"
    body += "".join(name + " " + " ".join(map(str, row)) + "\n" for name, row in zip(names, values, strict=True))
    order = range(len(ids)) if metadata_order is None else metadata_order
    metadata = "sample_id,site\n" + "".join(f"{ids[i]},{groups[i]}\n" for i in order)
    return body.encode(), metadata.encode()


def calculate(matrix, groups, **options):
    request = spec(**options)
    return calculate_permanova(request, *payload(matrix, groups, orientation=request.orientation))


MATRIX = [[8, 1, 0], [7, 2, 1], [9, 1, 1], [1, 8, 2], [2, 7, 1], [1, 9, 0]]
GROUPS = ["A", "A", "A", "B", "B", "B"]


def test_analytical_equidistant_balanced_and_unequal_groups():
    for groups in (["A", "A", "B", "B"], ["A", "A", "B", "B", "B"]):
        n = len(groups)
        result = calculate(np.eye(n, dtype=int).tolist(), groups)
        assert result["pseudo_f"] == pytest.approx(1)
        assert result["r_squared"] == pytest.approx(1 / (n - 1))
        assert result["p_value"] == 1
        assert result["df_between"] == 1
        assert result["df_within"] == n - 2
        assert result["permutation"]["draws"] == (6 if n == 4 else 10)
        assert result["dispersion"]["group_mean_distances"]["A"] == pytest.approx(.5)
        expected_b = np.sqrt((groups.count("B") - 1) / (2 * groups.count("B")))
        assert result["dispersion"]["group_mean_distances"]["B"] == pytest.approx(expected_b)


def test_zero_f_and_infinite_permutations_are_preserved():
    result = calculate([[1, 0], [0, 1], [1, 0], [0, 1]], ["A", "A", "B", "B"])
    assert result["pseudo_f"] == result["r_squared"] == 0
    assert result["p_value"] == 1
    record = result["permutation"]
    assert record["infinite_count"] == 2
    assert record["statistics"].count(None) == 2
    assert record["statuses"].count("positive_infinity") == 2
    assert record["count_extreme"] == 6
    assert record["tie_tolerance"] == TIE_TOLERANCE


def test_small_true_variation_is_not_refused_by_absolute_floor():
    counts = [[2**52 + increment] for increment in range(4)]
    result = calculate(counts, ["A", "A", "B", "B"])
    assert result["ss_total"] > 0
    assert result["pseudo_f"] == pytest.approx(8)
    assert result["p_value"] == pytest.approx(Fraction(1, 3))
    assert result["dispersion"]["distances"] == [0, 0, 0, 0]
    assert len(result["dispersion"]["discarded_eigenvalues"]) == 4


def fraction_reference(matrix, groups, index):
    n = len(matrix)
    squared = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for i, j in combinations(range(n), 2):
        a, b = matrix[i], matrix[j]
        d = Fraction(sum(abs(x - y) for x, y in zip(a, b)), sum(a) + sum(b))
        squared[i][j] = squared[j][i] = d * d
    total = sum(squared[i][j] for i, j in combinations(range(n), 2)) / n
    within = Fraction(0)
    for group in dict.fromkeys(groups):
        selected = [index[i] for i, label in enumerate(groups) if label == group]
        within += sum(squared[i][j] for i, j in combinations(selected, 2)) / len(selected)
    number_groups = len(set(groups))
    statistic = ((total - within) / (number_groups - 1)) / (within / (n - number_groups))
    return float(statistic)


def test_monte_carlo_indices_mean_reordered_distance_fixed_groups():
    result = calculate(MATRIX, GROUPS, permutations=7, seed=719)
    repeat = calculate(MATRIX, GROUPS, permutations=7, seed=719)
    assert repeat["permutation"] == result["permutation"]
    record = result["permutation"]
    expected_rng = np.random.Generator(np.random.PCG64(719))
    expected_indices = [expected_rng.permutation(6).tolist() for _ in range(7)]
    assert record["mode"] == "monte_carlo"
    assert record["indices"] == expected_indices
    observed = fraction_reference(MATRIX, GROUPS, list(range(6)))
    expected = [fraction_reference(MATRIX, GROUPS, index) for index in expected_indices]
    assert result["pseudo_f"] == pytest.approx(observed, rel=1e-12)
    assert record["statistics"] == pytest.approx(expected, rel=1e-12)
    extreme = sum(value >= observed - TIE_TOLERANCE for value in expected)
    assert record["count_extreme"] == extreme
    assert result["p_value"] == (extreme + 1) / 8
    assert record["denominator"] == 8


def test_exact_allocations_unique_and_observed_once_for_interleaved_groups():
    groups = ["A", "B", "A", "B", "A", "B"]
    result = calculate(MATRIX, groups, permutations=19)
    schedules = result["permutation"]["indices"]
    assignments = []
    for index in schedules:
        assignment = [None] * 6
        for position, original in enumerate(index):
            assignment[original] = groups[position]
        assignments.append(tuple(assignment))
    assert len(schedules) == len(set(assignments)) == 20
    assert assignments.count(tuple(groups)) == 1
    assert schedules.count(list(range(6))) == 1
    assert result["permutation"]["denominator"] == 20
    expected = [fraction_reference(MATRIX, groups, index) for index in schedules]
    assert result["permutation"]["statistics"] == pytest.approx(expected)
    assert result["p_value"] == sum(value >= result["pseudo_f"] - TIE_TOLERANCE for value in expected) / 20


def test_metadata_reordering_orientation_and_no_pcoa_cutoff(monkeypatch):
    data, metadata = payload(MATRIX, GROUPS, metadata_order=[5, 1, 3, 0, 4, 2], orientation="taxa_by_samples")
    import palaeo_agent.community as community
    monkeypatch.setattr(community, "selected_subspace_info", lambda *args: pytest.fail("PERMANOVA must not select PCoA dimensions"))
    result = calculate_permanova(spec(orientation="taxa_by_samples"), data, metadata)
    assert result["sample_ids"] == [f"s{i}" for i in range(6)]
    assert result["groups"] == GROUPS
    assert result["retained_counts"] == MATRIX
    assert result["orientation"] == "taxa_by_samples"


@pytest.mark.parametrize("changes", [
    {"design": "repeated"}, {"permutation_scheme": "blocked"}, {"permutations": True},
    {"permutations": 0}, {"permutations": 10000}, {"seed": True}, {"seed": -1},
    {"seed": 2**64}, {"value_type": "proportion"}, {"empty_samples": "drop"},
    {"distance": "jaccard", "transform": "relative_abundance"},
])
def test_unsupported_specifications_refuse(changes):
    with pytest.raises(ValidationError):
        spec(**changes)


@pytest.mark.parametrize("matrix,groups,code", [
    ([[1], [2], [3], [4]], ["A", "A", "A", "A"], "insufficient_groups"),
    ([[1], [2], [3], [4]], ["A", "B", "B", "B"], "small_groups"),
    ([[1], [2], [3], [4]], ["A", "A", "", "B"], "missing_group_label"),
    ([[1], [1], [1], [1]], ["A", "A", "B", "B"], "zero_total_variation"),
    ([[1, 0], [1, 0], [0, 1], [0, 1]], ["A", "A", "B", "B"], "undefined_observed_statistic"),
    ([[1], [2], [0], [4]], ["A", "A", "B", "B"], "empty_samples"),
    ([[1], [2], [.5], [4]], ["A", "A", "B", "B"], "invalid_count"),
])
def test_invalid_inputs_and_undefined_statistics_refuse(matrix, groups, code):
    with pytest.raises(AnalysisError) as caught:
        calculate(matrix, groups)
    assert caught.value.code == code


def test_missing_metadata_ids_or_group_column_refuse():
    data, metadata = payload(MATRIX, GROUPS)
    with pytest.raises(AnalysisError) as caught:
        calculate_permanova(spec(), data, metadata.replace(b"s5,B", b"other,B"))
    assert caught.value.code == "metadata_alignment"
    with pytest.raises(AnalysisError) as caught:
        calculate_permanova(spec(group_column="absent"), data, metadata)
    assert caught.value.code == "missing_group_column"


def test_validation_checks_structure_without_eigendecomposition(monkeypatch):
    monkeypatch.setattr(np.linalg, "eigh", lambda *args: pytest.fail("validation must not compute eigensystems"))
    output = validate_permanova(spec(), *payload(MATRIX, GROUPS))
    assert output["status"] == "valid"
    assert output["group_sizes"] == {"A": 3, "B": 3}


def test_schedule_resource_guard_precedes_distance_allocation(monkeypatch):
    import palaeo_agent.permanova as module
    monkeypatch.setattr(module, "MAX_SCHEDULE_ENTRIES", 5)
    monkeypatch.setattr(module, "community_distances", lambda *a, **k: pytest.fail("distance allocation occurred"))
    with pytest.raises(AnalysisError) as caught:
        calculate(MATRIX, GROUPS)
    assert caught.value.code == "resource_limit"


def test_non_euclidean_dispersion_records_signed_geometry():
    path = Path(__file__).resolve().parents[1] / "benchmarks/past/legacy-data/llanvirn.dat"
    header = path.read_text().splitlines()[0].split()[1:]
    metadata = "sample_id,site\n" + "".join(f"{name},{'A' if i < 5 else 'B'}\n" for i, name in enumerate(header))
    result = calculate_permanova(spec(orientation="taxa_by_samples", permutations=7), path.read_bytes(), metadata.encode())
    dispersion = result["dispersion"]
    assert dispersion["retained_negative_axes"] > 0
    assert any(value < -dispersion["threshold"] for value in dispersion["eigenvalues"])
    assert len(dispersion["distances"]) == 10
    assert dispersion["type"] == "centroid"
    assert "p_value" not in dispersion


def test_negative_semimetric_between_group_variation_is_not_clamped():
    matrix = [[3, 3, 3, 0], [2, 3, 0, 3], [2, 1, 2, 1],
              [0, 1, 2, 3], [2, 2, 3, 0], [3, 3, 1, 0]]
    result = calculate(matrix, GROUPS)
    assert result["ss_between"] < 0
    assert result["pseudo_f"] < 0
    assert result["r_squared"] < 0
    assert result["pseudo_f"] == pytest.approx(fraction_reference(matrix, GROUPS, list(range(6))))


def test_negative_signed_centroid_square_is_reported_and_truncated():
    matrix = [[1, 1, 2, 0], [3, 3, 2, 1], [2, 0, 2, 0],
              [2, 1, 0, 1], [3, 0, 0, 2], [3, 1, 0, 1]]
    result = calculate(matrix, GROUPS)
    dispersion = result["dispersion"]
    assert dispersion["squared_distances"][5] < 0
    assert dispersion["distances"][5] == 0
    assert dispersion["negative_squared_count"] == 1
    assert dispersion["truncated_sample_ids"] == ["s5"]
    assert any(warning["code"] == "negative_squared_dispersion" for warning in result["warnings"])


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(p_value=r["p_value"] / 2),
    lambda r: r["permutation"]["indices"][0].__setitem__(0, 99),
    lambda r: r["permutation"]["indices"][0].__setitem__(0, r["permutation"]["indices"][0][1]),
    lambda r: r["permutation"].update(count_extreme=r["permutation"]["count_extreme"] + 1),
    lambda r: r["permutation"]["statistics"].__setitem__(0, 123.0),
    lambda r: r["dispersion"]["distances"].__setitem__(0, 123.0),
    lambda r: r["metadata"][0].update(site="other"),
    lambda r: r.update(group_sizes={"A": 2, "B": 4}),
    lambda r: r.update(ss_total=123.0),
    lambda r: r["distances"][0].__setitem__(0, -1e-14),
    lambda r: r["transformed_matrix"][0].__setitem__(0, r["transformed_matrix"][0][0] + 1e-12),
])
def test_saved_result_rejects_scientific_and_schedule_tampering(mutate):
    result = deepcopy(calculate(MATRIX, GROUPS, permutations=7))
    mutate(result)
    with pytest.raises(ValidationError):
        PermanovaResult.model_validate(result)


HIGH_F_COUNTS = [[1999988, 17999992], [2000008, 17999972],
                 [9999979, 10000001], [10000001, 9999979],
                 [17999970, 2000010], [17999994, 1999986]]
HIGH_F_GROUPS = ["A", "A", "B", "B", "C", "C"]
HIGH_F_ORDERS = [tuple(index for block in order for index in (2 * block, 2 * block + 1))
                 for order in permutations(range(3))] + [(0, 2, 4, 1, 3, 5), (5, 0, 3, 2, 1, 4)]


@pytest.mark.parametrize("order", HIGH_F_ORDERS)
def test_high_f_exact_ties_are_invariant_to_group_block_and_sample_order(order):
    matrix = [HIGH_F_COUNTS[index] for index in order]
    groups = [HIGH_F_GROUPS[index] for index in order]
    result = calculate(matrix, groups, permutations=89)
    assert result["pseudo_f"] == pytest.approx(float(Fraction(191999616000192, 365)), rel=1e-14)
    assert result["permutation"]["mode"] == "exact"
    assert result["permutation"]["draws"] == result["permutation"]["space_size"] == 90
    assert result["permutation"]["count_extreme"] == 6
    assert result["p_value"] == float(Fraction(1, 15))
