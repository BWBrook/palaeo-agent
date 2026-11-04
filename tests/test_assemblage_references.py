"""Independent vegan, pinned iNEXT source, and base-R numerical references."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from palaeo_agent.count_homogeneity import (
    CountHomogeneitySpec,
    _holm,
    _interval,
    calculate_count_homogeneity,
)
from palaeo_agent.rarefaction import RarefactionSpec, analyse_rarefaction, calculate_rarefaction


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "benchmarks/past/references/assemblages-r.json").read_text())


@pytest.fixture(scope="module")
def llanvirn():
    data = (ROOT / REFERENCE["input"]["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == REFERENCE["input"]["sha256"]
    return data


def test_reference_provenance():
    script = ROOT / REFERENCE["generator"]
    assert hashlib.sha256(script.read_bytes()).hexdigest() == REFERENCE["generator_sha256"]
    assert REFERENCE["reference_kind"] == "independent_R_library_and_pinned_upstream_source_not_PAST_execution"
    assert REFERENCE["coverage_reference"]["kind"] == "unmodified_upstream_function_executed_without_installing_package"


def check_rarefaction_sample(actual, expected):
    for key in ("sample_id", "total", "observed_richness", "f1", "f2"):
        assert actual[key] == expected[key]
    if expected["full_coverage"] is None:
        assert actual["full_coverage"] is None
    else:
        assert actual["full_coverage"] == pytest.approx(expected["full_coverage"], rel=1e-10, abs=1e-12)
    by_size = {item["size"]: item for item in expected["estimates"]}
    for estimate in actual["estimates"]:
        ref = by_size[estimate["size"]]
        for key in ("expected_richness", "variance", "coverage"):
            if ref[key] is None:
                assert estimate[key] is None
            else:
                assert estimate[key] == pytest.approx(ref[key], rel=1e-10, abs=1e-12)
        deterministic = (estimate["size"] in (1, expected["total"]) or expected["observed_richness"] == 1
                         or expected["f1"] == expected["total"])
        if deterministic:
            assert estimate["variance"] == estimate["conditional_sd"] == 0
        else:
            assert estimate["conditional_sd"] == pytest.approx(ref["sd"], rel=1e-10, abs=1e-12)


def test_llanvirn_m13_matches_vegan_and_inext(llanvirn):
    spec = RarefactionSpec(method="rarefaction", input=ROOT / REFERENCE["input"]["path"],
                          format="past", orientation="taxa_by_samples", value_type="count",
                          missing="error", empty_samples="error", sizes="minimum_total")
    result = calculate_rarefaction(spec, llanvirn)
    assert result["sizes"] == [13]
    for actual, expected in zip(result["samples"], REFERENCE["rarefaction"]["llanvirn"], strict=True):
        check_rarefaction_sample(actual, expected)


def test_fresh_PAST_export_matches_expectations_and_conditional_sd(llanvirn):
    reference = json.loads((ROOT / "benchmarks/past/references/rarefaction-past.json").read_text())
    assert hashlib.sha256(llanvirn).hexdigest() == reference["input"]["sha256"]
    spec = RarefactionSpec(method="rarefaction", input=ROOT / reference["input"]["path"],
                          format="past", orientation="taxa_by_samples", value_type="count",
                          missing="error", empty_samples="error", sizes=list(range(1, 14)))
    result = calculate_rarefaction(spec, llanvirn)
    estimates = {(s["sample_id"], e["size"]): e for s in result["samples"] for e in s["estimates"]}
    for row in reference["comparisons"]:
        actual = estimates[row["sample_id"], row["size"]][row["quantity"]]
        assert actual == pytest.approx(row["past"], rel=0, abs=row["tolerance"])


@pytest.mark.parametrize("case", REFERENCE["rarefaction"]["fixtures"] + REFERENCE["rarefaction"]["llanvirn"],
                         ids=lambda case: case["sample_id"])
def test_rarefaction_boundaries_and_curves_match_R(case):
    result = analyse_rarefaction([case["counts"]], sample_ids=[case["sample_id"]],
                                taxon_ids=[f"t{i}" for i in range(len(case["counts"]))],
                                sizes=[e["size"] for e in case["estimates"]], empty_samples="error")
    check_rarefaction_sample(result["samples"][0], case)
    if case["total"] == 1:
        assert result["samples"][0]["coverage_unavailable_reason"] == "coverage_unavailable_single_specimen"
        assert case["raw_inext_full_coverage"] == 1


def count_spec(pairs, **kwargs):
    return CountHomogeneitySpec(method="count_homogeneity", input=ROOT / REFERENCE["input"]["path"],
                               format="past", orientation="taxa_by_samples", value_type="count",
                               missing="error", empty_samples="error", pairs=pairs,
                               simulations=REFERENCE["settings"]["simulations"], seed=20261107, **kwargs)


@pytest.fixture(scope="module")
def count_result(llanvirn):
    return calculate_count_homogeneity(count_spec([p["sample_ids"] for p in REFERENCE["count_homogeneity"]["pairs"]]), llanvirn)


def check_pair(actual, expected):
    for key in ("sample_ids", "taxon_ids", "taxa_absent_from_pair", "observed_counts"):
        assert actual[key] == expected[key]
    assert actual["pearson_chi_squared"] == pytest.approx(expected["pearson_chi_squared"], rel=1e-12)
    np.testing.assert_allclose(actual["expected_counts"], expected["expected_counts"], rtol=1e-12, atol=0)
    for taxon, ref in zip(actual["taxon_tests"], expected["taxon_tests"], strict=True):
        assert taxon["taxon_id"] == ref["taxon_id"]
        assert not ref["near_ties_added_by_R_tolerance"], "R/SciPy Fisher tolerance exception needs explicit review"
        for key in ("p_value", "p_value_holm"):
            assert taxon[key] == pytest.approx(ref[key], abs=1e-10)
    a, b = actual["monte_carlo"], expected["monte_carlo"]
    pooled = (a["count_extreme"] + b["count_extreme"]) / (a["simulations"] + b["simulations"])
    tolerance = 6 * math.sqrt(pooled * (1 - pooled) * (1 / a["simulations"] + 1 / b["simulations"])) + 2 / min(a["simulations"], b["simulations"])
    assert abs(a["count_extreme"] / a["simulations"] - b["count_extreme"] / b["simulations"]) <= tolerance


def test_llanvirn_pearson_fisher_and_global_taxon_holm_match_R(count_result):
    reference = REFERENCE["count_homogeneity"]
    for actual, expected in zip(count_result["pairs"], reference["pairs"], strict=True):
        check_pair(actual, expected)
    assert count_result["multiplicity"]["omnibus"]["size"] == reference["omnibus_family_size"] == 9
    assert count_result["multiplicity"]["taxon"]["size"] == reference["taxon_family_size"] == 118
    assert _holm([p["p_value"] for p in reference["pairs"]]) == pytest.approx([p["p_value_holm"] for p in reference["pairs"]], abs=1e-14)


def test_zero_count_limits_match_R_binom_test(count_result):
    for actual, expected in zip(count_result["zero_count_limits"], REFERENCE["zero_count_limits"], strict=True):
        assert actual["sample_id"] == expected["sample_id"]
        assert actual["n"] == expected["total"]
        assert actual["taxon_ids"] == expected["taxon_ids"]
        assert actual["confidence"] == expected["confidence"]
        assert actual["upper_limit"] == pytest.approx(expected["upper_limit"], rel=1e-12)


@pytest.mark.parametrize("case", REFERENCE["monte_carlo_interval_controls"])
def test_mc_interval_boundaries_match_R_binom_test(case):
    assert _interval(case["count_extreme"], case["simulations"]) == pytest.approx(case["interval"], abs=1e-12)


def test_fixed_margin_sampler_matches_exact_weighted_small_table():
    data = b". a b\nt1 2 0\nt2 1 1\nt3 0 2\nabsent 0 0\n"
    result = calculate_count_homogeneity(count_spec([["a", "b"]]), data)
    reference = REFERENCE["tiny_count_homogeneity"]
    check_pair(result["pairs"][0], reference["pairs"][0])
    exact = reference["exact"]
    assert exact["probability_sum"] == pytest.approx(1)
    assert exact["table_count"] == 7
    assert exact["conditional_tail_probability"] == pytest.approx(0.6)
    assert len(set(exact["probabilities"])) > 1
    mc = result["pairs"][0]["monte_carlo"]
    p = exact["conditional_tail_probability"]
    assert abs(mc["count_extreme"] / mc["simulations"] - p) <= 6 * math.sqrt(p * (1 - p) / mc["simulations"])
