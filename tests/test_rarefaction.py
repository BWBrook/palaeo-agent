import copy
from fractions import Fraction
from itertools import combinations
import math

import pytest
from pydantic import ValidationError

from palaeo_agent.core import AnalysisError
from palaeo_agent.rarefaction import (
    RarefactionResult, RarefactionSpec, analyse_rarefaction,
    calculate_rarefaction, validate_rarefaction,
)


def specification(**changes):
    return RarefactionSpec.model_validate({"method": "rarefaction", "input": "counts.dat", "format": "past",
        "orientation": "samples_by_taxa", "value_type": "count", "missing": "error", "empty_samples": "error", **changes})


def analyse(rows, sizes="minimum_total", **changes):
    return analyse_rarefaction(rows, sample_ids=[f"s{i}" for i in range(len(rows))],
        taxon_ids=[f"t{i}" for i in range(len(rows[0]))], empty_samples="error", sizes=sizes, **changes)


def enumerated(counts, m):
    population = [taxon for taxon, count in enumerate(counts) for _ in range(count)]
    richness = [len({population[index] for index in draw}) for draw in combinations(range(len(population)), m)]
    mean = Fraction(sum(richness), len(richness))
    variance = sum((value - mean)**2 for value in richness) / len(richness)
    return float(mean), float(variance)


def exact_coverage(counts, m):
    n = sum(counts)
    return float(1 - sum(Fraction(x, n) * Fraction(math.comb(n - x, m), math.comb(n - 1, m))
                         for x in counts if x and n - x >= m))


def test_enumerated_conditional_moments_and_exact_rational_coverage():
    for counts in ([3, 2, 1, 1], [4, 3, 2], [1, 1], [2, 2], [2, 1], [1, 0, 3]):
        total = sum(counts)
        result = analyse([counts], sizes=list(range(1, total + 1)))
        for estimate in result["samples"][0]["estimates"]:
            expected, variance = enumerated(counts, estimate["size"])
            assert estimate["expected_richness"] == pytest.approx(expected, rel=1e-12, abs=1e-14)
            assert estimate["variance"] == pytest.approx(variance, rel=1e-12, abs=1e-14)
            assert estimate["conditional_sd"] == pytest.approx(math.sqrt(variance), abs=1e-14)
            if estimate["size"] < total:
                assert estimate["coverage"] == pytest.approx(exact_coverage(counts, estimate["size"]), abs=1e-14)


def test_single_specimen_and_one_taxon_do_not_require_ordination():
    single = analyse([[1]])["samples"][0]
    assert single["full_coverage"] is None
    assert single["coverage_unavailable_reason"] == "coverage_unavailable_single_specimen"
    assert single["estimates"][0] == {"size": 1, "expected_richness": 1, "variance": 0,
        "conditional_sd": 0, "coverage": None, "coverage_unavailable_reason": "coverage_unavailable_single_specimen",
        "variance_clamped": False}
    one_taxon = analyse([[10, 0]], sizes=[1, 4, 10])["samples"][0]
    assert one_taxon["full_coverage"] == 1
    assert one_taxon["coverage_boundary"]
    assert "does not establish" in one_taxon["coverage_note"]
    assert all(row["expected_richness"] == 1 and row["variance"] == 0 and row["coverage"] == 1
               for row in one_taxon["estimates"])


def test_all_singletons_and_f2_zero_boundaries():
    singletons = analyse([[1, 1, 1, 1]], sizes=[1, 2, 4])["samples"][0]
    assert singletons["full_coverage"] == pytest.approx(2 / 11)
    assert not singletons["coverage_boundary"]
    for estimate in singletons["estimates"]:
        assert estimate["expected_richness"] == estimate["size"]
        assert estimate["variance"] == 0
        if estimate["size"] < 4:
            assert estimate["coverage"] == 0
    assert analyse([[5, 1]])["samples"][0]["coverage_boundary"]
    assert analyse([[5, 1]])["samples"][0]["full_coverage"] == 1
    assert analyse([[5, 1, 1]])["samples"][0]["full_coverage"] == pytest.approx(11 / 14)
    with_doubleton = analyse([[3, 2, 1, 1]])["samples"][0]
    assert with_doubleton["full_coverage"] == pytest.approx(37 / 49)


@pytest.mark.parametrize("n", [3, 7, 19])
def test_all_singleton_interpolated_coverage_is_exactly_zero(n):
    result = analyse([[1] * n], sizes=[1, n - 1])
    assert all(estimate["coverage"] == 0 for estimate in result["samples"][0]["estimates"])


@pytest.mark.parametrize("n", [10**9, 2**53 - 1])
def test_extreme_imbalance_retains_tiny_variance(n):
    estimate = analyse([[n - 1, 1]], sizes=[2])["samples"][0]["estimates"][0]
    assert estimate["expected_richness"] == 1 + 2 / n
    assert estimate["variance"] == pytest.approx((2 / n) * (1 - 2 / n), rel=2e-15, abs=0)
    assert estimate["coverage"] == 1 - 1 / n


def test_large_balanced_counts_are_explicitly_refused_without_long_products():
    data = b".\tx\ty\na\t1000000000\t1000000000\n"
    spec = specification(sizes=[10**9])
    for function in (calculate_rarefaction, validate_rarefaction):
        with pytest.raises(AnalysisError) as caught:
            function(spec, data)
        assert caught.value.code == "resource_limit"
        assert caught.value.details["product_factors"] > caught.value.details["limit"]


def test_resource_budget_is_for_whole_operation(monkeypatch):
    import palaeo_agent.rarefaction as operation
    monkeypatch.setattr(operation, "MAX_PAIR_TERMS", 3)
    assert analyse([[3, 2, 1]], sizes=[2])["n"] == 1
    with pytest.raises(AnalysisError) as caught:
        analyse([[3, 2, 1], [3, 2, 1]], sizes=[2])
    assert caught.value.code == "resource_limit"


def test_taxon_and_sample_order_invariance_with_equal_weights():
    matrix = [[3, 2, 2, 1], [1, 4, 1, 2], [2, 2, 2, 2]]
    labels = ["z", "a", "y", "b"]
    first = analyse_rarefaction(matrix, sample_ids=["a", "b", "c"], taxon_ids=labels,
                                empty_samples="error", sizes=[4, 1, 3])
    index = [2, 0, 3, 1]
    second = analyse_rarefaction([[matrix[i][j] for j in index] for i in [2, 0, 1]],
        sample_ids=["c", "a", "b"], taxon_ids=[labels[j] for j in index], empty_samples="error", sizes=[4, 1, 3])
    assert first["sizes"] == [1, 3, 4]
    assert {row["sample_id"]: row for row in first["samples"]} == {row["sample_id"]: row for row in second["samples"]}


def test_identical_samples_repeated_blocks_and_zero_taxon_labels_are_retained():
    result = analyse([[3, 2, 0], [2, 1, 0], [1, 3, 0]] * 2, sizes=[2])
    assert result["taxon_ids"] == ["t0", "t1", "t2"]
    assert all(row[2] == 0 for row in result["retained_counts"])
    assert result["n"] == 6
    assert {warning["code"] for warning in result["warnings"]} == {"identical_samples", "repeated_block"}


def test_near_limit_multi_taxon_moments_against_exact_fractions():
    row = [2**53 - 5, 2, 2]
    n = sum(row)
    result = analyse([row], sizes=[2, 3, 9])
    for estimate in result["samples"][0]["estimates"]:
        m = estimate["size"]
        denominator = math.comb(n, m)
        q = [Fraction(math.comb(n - x, m), denominator) if n - x >= m else Fraction(0) for x in row]
        expected = sum(1 - value for value in q)
        covariance = sum((Fraction(math.comb(n - row[i] - row[j], m), denominator)
                          if n - row[i] - row[j] >= m else Fraction(0)) - q[i] * q[j]
                         for i in range(len(row)) for j in range(i))
        variance = sum(value * (1 - value) for value in q) + 2 * covariance
        assert estimate["expected_richness"] == float(expected)
        assert estimate["variance"] == pytest.approx(float(variance), rel=2e-15, abs=0)


@pytest.mark.parametrize("sizes", [[], [1, 1], [True], ["2"], [2.0], [1.5], [0], [-1], "2", (1, 2)])
def test_strict_size_specification_and_in_memory_api(sizes):
    with pytest.raises(ValidationError):
        specification(sizes=sizes)
    with pytest.raises(AnalysisError) as caught:
        analyse([[2, 1]], sizes=sizes)
    assert caught.value.code == "invalid_sizes"


@pytest.mark.parametrize("value", [True, -1, 1.5, float("nan"), float("inf"), 2**53])
def test_invalid_counts(value):
    with pytest.raises(AnalysisError) as caught:
        analyse([[value, 1]])
    assert caught.value.code in {"invalid_count", "count_range"}


def test_size_extrapolation_names_sample_and_total():
    with pytest.raises(AnalysisError) as caught:
        analyse([[2, 1], [1, 1]], sizes=[3])
    assert caught.value.code == "size_exceeds_total"
    assert caught.value.details == {"sample_id": "s1", "total": 2, "size": 3}


def test_empty_policy_and_metadata_align_before_minimum_total():
    data = b".\tx\ty\nempty\t0\t0\na\t2\t1\nb\t1\t1\n"
    with pytest.raises(AnalysisError, match="Empty samples"):
        calculate_rarefaction(specification(), data)
    result = calculate_rarefaction(specification(empty_samples="drop", metadata="meta.csv"), data,
                                  b"sample_id,group\nb,B\nempty,E\na,A\n")
    assert result["sample_ids"] == ["a", "b"]
    assert result["sizes"] == [2]
    assert result["excluded"] == [{"sample_id": "empty", "reason": "empty_sample"}]
    assert result["metadata"] == [{"sample_id": "a", "group": "A"}, {"sample_id": "b", "group": "B"}]
    with pytest.raises(AnalysisError):
        calculate_rarefaction(specification(empty_samples="drop"), b".\tx\na\t0\n")
    with pytest.raises(AnalysisError):
        analyse_rarefaction([], sample_ids=[], taxon_ids=["x"], empty_samples="drop")


def test_parser_orientation_delimiter_missing_and_validation_no_estimates(monkeypatch):
    result = calculate_rarefaction(specification(format="delimited", delimiter="comma", orientation="taxa_by_samples"),
                                  b"taxon,a,b\nx,2,1\ny,1,1\n")
    assert result["orientation"] == "taxa_by_samples"
    assert result["canonical_orientation"] == "samples_by_taxa"
    assert result["retained_counts"] == [[2, 1], [1, 1]]
    with pytest.raises(AnalysisError) as caught:
        calculate_rarefaction(specification(), b".\tx\na\t.\n")
    assert caught.value.code == "missing_counts"
    import palaeo_agent.rarefaction as operation
    def forbidden(*args, **kwargs):
        raise AssertionError("preflight must not compute ratios")
    monkeypatch.setattr(operation, "_absence", forbidden)
    validation = validate_rarefaction(specification(sizes=[2]), b".\tx\ty\na\t3\t2\n")
    assert validation["status"] == "valid"
    assert validation["sizes"] == [2]


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(n=2),
    lambda r: r.update(sample_ids=["wrong"]),
    lambda r: r.update(taxon_ids=["x"] * 4),
    lambda r: r.update(sizes=[1]),
    lambda r: r.update(sizes_requested=[1, 1]),
    lambda r: r["retained_counts"][0].__setitem__(0, 5),
    lambda r: r["retained_counts"][0].__setitem__(0, 3.5),
    lambda r: r["samples"][0].update(f1=5),
    lambda r: r["samples"][0].update(coverage_boundary=True),
    lambda r: r["samples"][0].update(full_coverage=None),
    lambda r: r["samples"][0]["estimates"][0].update(expected_richness=float("nan")),
    lambda r: r["samples"][0]["estimates"][0].update(expected_richness=3),
    lambda r: r["samples"][0]["estimates"][0].update(variance=-1),
    lambda r: r["samples"][0]["estimates"][0].update(conditional_sd=1),
    lambda r: r["samples"][0]["estimates"][0].update(coverage=None),
    lambda r: r["samples"][0]["estimates"][0].update(coverage_unavailable_reason="coverage_unavailable_single_specimen"),
    lambda r: r["samples"][0]["estimates"][0].update(coverage=1.1),
])
def test_result_tampering_is_rejected(mutation):
    result = copy.deepcopy(analyse([[3, 2, 1, 1]], sizes=[2, 7]))
    mutation(result)
    with pytest.raises(ValidationError):
        RarefactionResult.model_validate(result)


def test_single_specimen_result_cannot_claim_coverage():
    result = analyse([[1]])
    result["samples"][0]["estimates"][0]["coverage"] = 1
    with pytest.raises(ValidationError):
        RarefactionResult.model_validate(result)


def test_results_do_not_depend_on_the_ambient_decimal_context():
    import decimal
    expected = analyse([[4, 2, 1], [1, 1, 5]], sizes=[2, 3])
    with decimal.localcontext() as context:
        context.prec, context.rounding = 5, decimal.ROUND_FLOOR
        context.traps[decimal.Inexact] = True
        assert analyse([[4, 2, 1], [1, 1, 5]], sizes=[2, 3]) == expected
