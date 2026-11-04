import copy
import itertools
import math

import numpy as np
import pytest
from pydantic import ValidationError

from palaeo_agent.core import AnalysisError
from palaeo_agent.count_homogeneity import (
    MAX_POOLED_TOTAL, CountHomogeneityResult, CountHomogeneitySpec,
    _holm, _interval, calculate_count_homogeneity, validate_count_homogeneity,
)


def spec(**changes):
    value = dict(method="count_homogeneity", input="counts.tsv", format="delimited", delimiter="tab",
                 orientation="samples_by_taxa", value_type="count", missing="error", empty_samples="error",
                 pairs=[["a", "b"]], simulations=999, seed=2026)
    value.update(changes)
    return value


def table(rows, taxa=None):
    taxa = taxa or [f"t{i}" for i in range(len(next(iter(rows.values()))))]
    return ("sample\t" + "\t".join(taxa) + "\n" + "\n".join(
        name + "\t" + "\t".join(map(str, row)) for name, row in rows.items()) + "\n").encode()


def test_exact_weighted_enumeration_and_replay():
    data = table({"a": [2, 1, 0], "b": [0, 1, 2]})
    result = calculate_count_homogeneity(spec(simulations=19999), data)
    pair = result["pairs"][0]
    assert pair["expected_counts"] == [[1, 1], [1, 1], [1, 1]]
    assert pair["pearson_chi_squared"] == 4
    assert pair["braycurtis_proportions"] == pytest.approx(2 / 3)
    denominator = math.comb(6, 3)
    tail = 0
    weight = 0
    for allocation in itertools.product(range(3), repeat=3):
        if sum(allocation) != 3:
            continue
        probability = math.prod(math.comb(2, x) for x in allocation) / denominator
        statistic = sum(2 * (x - 1)**2 for x in allocation)
        weight += probability
        if statistic >= 4:
            tail += probability
    assert weight == pytest.approx(1)
    assert tail == pytest.approx(0.6)
    mc = pair["monte_carlo"]
    # A fixed six-standard-error criterion, prespecified independently of the sampled interval.
    assert abs(mc["count_extreme"] / mc["simulations"] - tail) < 6 * math.sqrt(tail * (1 - tail) / mc["simulations"])
    assert result == calculate_count_homogeneity(spec(simulations=19999), data)
    assert result["randomization"]["algorithm"] == "patefield"
    assert result["randomization"]["scipy_version"]
    assert result["randomization"]["numpy_version"]


def test_fisher_holm_effect_and_zero_limits_known_values():
    result = calculate_count_homogeneity(spec(), table({"a": [1, 9], "b": [11, 3]}))
    tests = result["pairs"][0]["taxon_tests"]
    for test in tests:
        assert test["p_value"] == pytest.approx(0.0027594561852200836)
        assert test["p_value_holm"] == pytest.approx(2 * 0.0027594561852200836)
    assert tests[0]["proportion_difference_b_minus_a"] == pytest.approx(11 / 14 - 1 / 10)
    assert _holm([0.01, 0.04, 0.03, 0.002]) == pytest.approx([0.03, 0.06, 0.06, 0.008])
    zeros = calculate_count_homogeneity(spec(), table({"a": [0, 10, 0], "b": [10, 0, 0]}))["zero_count_limits"]
    assert zeros[0]["taxon_ids"] == ["t0"]
    assert zeros[1]["taxon_ids"] == ["t1"]
    assert zeros[0]["upper_limit"] == pytest.approx(0.2588655508930523)
    assert all(item["n"] == 10 and item["scope"] == "pointwise" for item in zeros)


def test_complete_family_shared_samples_pair_absent_and_elsewhere_taxa():
    data = table({"a": [3, 1, 0, 0], "b": [1, 3, 0, 0], "c": [1, 0, 3, 0], "d": [1, 2, 1, 9]})
    result = calculate_count_homogeneity(spec(pairs=[["a", "b"], ["b", "c"]]), data)
    assert result["multiplicity"] == {"omnibus": {"method": "holm", "size": 2},
                                       "taxon": {"method": "holm", "size": 5}, "joint_control": False}
    assert result["pairs"][0]["taxa_absent_from_pair"] == ["t2", "t3"]
    assert result["pairs"][1]["taxa_absent_from_pair"] == ["t3"]
    tests = [test for pair in result["pairs"] for test in pair["taxon_tests"]]
    assert [test["p_value_holm"] for test in tests] == pytest.approx(_holm([test["p_value"] for test in tests]))
    assert [pair["monte_carlo"]["spawn_key"] for pair in result["pairs"]] == [[0], [1]]
    assert [item["sample_id"] for item in result["zero_count_limits"]] == ["a", "b", "c"]
    assert result["zero_count_limits"][0]["taxon_ids"] == ["t2", "t3"]
    assert all(pair["p_value"] > .05 for pair in result["pairs"])
    assert len(tests) == 5  # Taxon testing is never gated by omnibus significance.


def test_pair_and_taxon_order_invariance_of_deterministic_outputs():
    rows = {"a": [2, 5, 0], "b": [1, 4, 7]}
    forward = calculate_count_homogeneity(spec(), table(rows))["pairs"][0]
    reverse = calculate_count_homogeneity(spec(pairs=[["b", "a"]]), table(rows))["pairs"][0]
    reorder = calculate_count_homogeneity(spec(), table({key: row[::-1] for key, row in rows.items()}, ["t2", "t1", "t0"]))["pairs"][0]
    for alternate in (reverse, reorder):
        for key in ("pearson_chi_squared", "braycurtis_proportions"):
            assert alternate[key] == pytest.approx(forward[key], rel=1e-14)
        assert {test["taxon_id"]: test["p_value"] for test in alternate["taxon_tests"]} == pytest.approx(
            {test["taxon_id"]: test["p_value"] for test in forward["taxon_tests"]})
    assert reverse["sample_totals"] == forward["sample_totals"][::-1]
    assert reverse["observed_counts"] == [row[::-1] for row in forward["observed_counts"]]
    for left, right in zip(forward["taxon_tests"], reverse["taxon_tests"], strict=True):
        assert left["proportion_difference_b_minus_a"] == -right["proportion_difference_b_minus_a"]


def test_extreme_imbalance_and_transpose_metadata():
    rows = {"a": [1, 12], "b": [342, 360]}
    normal = calculate_count_homogeneity(spec(), table(rows))
    transposed = b"taxon\ta\tb\nt0\t1\t342\nt1\t12\t360\n"
    other = calculate_count_homogeneity(spec(orientation="taxa_by_samples", metadata="meta.csv"), transposed,
                                        b"sample_id,group\nb,second\na,first\n")
    assert normal["pairs"] == other["pairs"]
    assert other["metadata"] == [{"sample_id": "a", "group": "first"}, {"sample_id": "b", "group": "second"}]
    assert other["pairs"][0]["sample_totals"] == [13, 702]
    assert other["retained_counts"] == [[1, 12], [342, 360]]


@pytest.mark.parametrize("field,value", [
    ("simulations", 998), ("simulations", 100000), ("simulations", 999.0), ("simulations", True), ("simulations", "999"),
    ("seed", -1), ("seed", 2**32), ("seed", False), ("seed", 1.0), ("seed", "1"),
    ("confidence", False), ("confidence", "0.95"), ("confidence", 0), ("confidence", 1),
    ("confidence", math.inf), ("confidence", math.nan),
    ("pairs", []), ("pairs", [["a", "a"]]), ("pairs", [["a", "b"], ["b", "a"]]),
    ("pairs", [["a", "b"], ["a", "b"]]), ("pairs", [["a", 1]]), ("pairs", [["a", " "]]),
    ("pairs", [["a", "b", "c"]]), ("pairs", [("a", "b")]),
])
def test_strict_invalid_settings(field, value):
    with pytest.raises(ValidationError):
        CountHomogeneitySpec.model_validate(spec(**{field: value}))


@pytest.mark.parametrize("missing", ["seed", "simulations", "pairs"])
def test_required_design_settings(missing):
    settings = spec()
    del settings[missing]
    with pytest.raises(ValidationError):
        CountHomogeneitySpec.model_validate(settings)


@pytest.mark.parametrize("rows,changes,code", [
    ({"a": [4, 0], "b": [2, 0]}, {}, "insufficient_pair_taxa"),
    ({"a": [1, 1], "b": [0, 0]}, {}, "empty_samples"),
    ({"a": [1, 1], "b": [0, 0]}, {"empty_samples": "drop"}, "unknown_pair_sample"),
    ({"a": [1, 1], "b": [1, 1]}, {"pairs": [["a", "z"]]}, "unknown_pair_sample"),
    ({"a": [1.1, 1], "b": [1, 1]}, {}, "invalid_count"),
    ({"a": [-1, 1], "b": [1, 1]}, {}, "invalid_count"),
    ({"a": [MAX_POOLED_TOTAL, 1], "b": [1, 1]}, {}, "sampler_count_range"),
    ({"a": [2**53 - 1, 1], "b": [1, 1]}, {}, "count_range"),
])
def test_pair_refusals_before_sampling(rows, changes, code, monkeypatch):
    monkeypatch.setattr("palaeo_agent.count_homogeneity.random_table", lambda *a, **k: pytest.fail("Sampling attempted"))
    with pytest.raises(AnalysisError) as error:
        validate_count_homogeneity(spec(**changes), table(rows))
    assert error.value.code == code


def test_preflight_identical_samples_and_unpaired_empty_drop(monkeypatch):
    monkeypatch.setattr("palaeo_agent.count_homogeneity.random_table", lambda *a, **k: pytest.fail("Sampling attempted"))
    valid = validate_count_homogeneity(spec(empty_samples="drop"), table({"a": [2, 2], "b": [2, 2], "c": [0, 0]}))
    assert valid["n"] == 2
    assert valid["excluded"] == [{"sample_id": "c", "reason": "empty_sample"}]


def test_mc_endpoint_intervals_and_never_zero_p_values():
    low = calculate_count_homogeneity(spec(), table({"a": [100, 0], "b": [0, 100]}))["pairs"][0]
    high = calculate_count_homogeneity(spec(), table({"a": [10, 10], "b": [10, 10]}))["pairs"][0]
    assert low["monte_carlo"]["count_extreme"] == 0
    assert low["p_value"] == 1 / 1000
    assert low["monte_carlo"]["tail_probability_interval"] == pytest.approx([0, 1 - .025**(1 / 999)])
    assert high["monte_carlo"]["count_extreme"] == 999
    assert high["p_value"] == 1
    assert high["monte_carlo"]["tail_probability_interval"] == pytest.approx([.025**(1 / 999), 1])
    assert _interval(49, 999)[0] < .05 < _interval(49, 999)[1]
    assert not low["monte_carlo"]["monte_carlo_unresolved"]
    assert low["monte_carlo"]["unresolved_scope"] == "unadjusted_tail_only"


@pytest.fixture(scope="module")
def saved():
    return calculate_count_homogeneity(spec(pairs=[["a", "b"], ["b", "c"]]),
                                       table({"a": [2, 5, 0], "b": [1, 4, 7], "c": [5, 0, 1]}))


@pytest.mark.parametrize("path,value", [
    (("randomization", "seed"), True), (("randomization", "seed"), 2**32),
    (("randomization", "simulations"), 1999), (("randomization", "chunk_size"), 128),
    (("randomization", "algorithm"), "boyett"), (("randomization", "numpy_version"), ""),
    (("randomization", "tie_relative_tolerance"), 1e-8),
    (("retained_counts", 0, 0), 2.5), (("retained_counts", 0, 0), -1),
    (("pairs", 0, "p_value"), 0), (("pairs", 0, "p_value_holm"), 0.12345),
    (("pairs", 0, "monte_carlo", "count_extreme"), 1000),
    (("pairs", 0, "monte_carlo", "spawn_key"), [1]),
    (("pairs", 0, "monte_carlo", "tail_probability_interval"), [0, 1]),
    (("pairs", 0, "monte_carlo", "unresolved_scope"), "holm_stable"),
    (("pairs", 0, "taxon_tests", 0, "p_value"), 0.314159),
    (("pairs", 0, "taxon_tests", 0, "taxon_id"), "unknown"),
    (("pairs", 0, "observed_counts", 0, 0), 100),
    (("pairs", 0, "expected_counts", 0, 0), 100),
    (("multiplicity", "taxon", "size"), 3), (("multiplicity", "joint_control"), True),
    (("zero_count_limits", 0, "taxon_ids"), []), (("zero_count_limits", 0, "upper_limit"), .5),
])
def test_saved_result_rejects_inconsistent_records(saved, path, value):
    changed = copy.deepcopy(saved)
    location = changed
    for key in path[:-1]:
        location = location[key]
    location[path[-1]] = value
    with pytest.raises(ValidationError):
        CountHomogeneityResult.model_validate(changed)


def test_result_validation_does_not_resample(saved, monkeypatch):
    monkeypatch.setattr("palaeo_agent.count_homogeneity.random_table", lambda *a, **k: pytest.fail("Sampling attempted"))
    assert CountHomogeneityResult.model_validate(saved).model_dump(mode="json") == saved


def test_unresolved_flag_true_is_only_unadjusted_scope():
    result = calculate_count_homogeneity(spec(), table({"a": [2, 5], "b": [5, 2]}))
    pair = result["pairs"][0]
    pair["p_value"] = pair["p_value_holm"] = .05
    pair["monte_carlo"].update(count_extreme=49, p_value=.05, tail_probability_interval=_interval(49, 999),
                                monte_carlo_unresolved=True)
    assert CountHomogeneityResult.model_validate(result).pairs[0].monte_carlo.monte_carlo_unresolved
    pair["monte_carlo"]["monte_carlo_unresolved"] = False
    with pytest.raises(ValidationError, match="Unresolved flag"):
        CountHomogeneityResult.model_validate(result)


def test_backend_memory_guard_before_sampling(monkeypatch):
    monkeypatch.setattr("palaeo_agent.count_homogeneity.random_table", lambda *a, **k: pytest.fail("Sampling attempted"))
    with pytest.raises(AnalysisError) as error:
        validate_count_homogeneity(spec(), table({"a": [1] * 4097, "b": [1] * 4097}))
    assert error.value.code == "resource_limit"


def test_tiny_confidence_has_a_conservative_representable_zero_limit():
    confidence = math.nextafter(0.0, 1.0)
    result = calculate_count_homogeneity(spec(confidence=confidence), table({"a": [0, 10], "b": [10, 0]}))
    assert result["confidence"] == confidence
    assert result["zero_count_limits"][0]["upper_limit"] == confidence
