import importlib.util
import json
import shutil
from pathlib import Path

from decimal import Decimal
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("compare_past_captures", ROOT / "scripts/compare_past_captures.py")
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


@pytest.mark.parametrize("token,digits,bound", [
    ("0.72", 8, "5e-9"),
    ("0.047904192", 8, "5e-10"),
    ("4.7904192e-2", 8, "5e-10"),
    ("0.2559", 4, "5e-5"),
    ("1.627", 4, "5e-4"),
    ("0", 8, "0"),
])
def test_export_rounding_restores_omitted_trailing_zeros(token, digits, bound):
    assert capture.rounding_bound(token, digits) == Decimal(bound)


def test_numeric_comparison_rejects_change_hidden_by_short_display_token():
    result = capture.compare_values([[0.720001]], [["0.72"]], ["a"], ["b"], 8)
    assert result["status"] == "different"
    assert result["failed_values"] == 1
    assert result["max_ratio_to_rounding_bound"] > 100


@pytest.mark.parametrize("expected,token,status", [
    (0.099996, "0.1", "different"),
    (-0.099996, "-0.1", "different"),
    (0.0999996, "0.1", "matched"),
    (-0.0999996, "-0.1", "matched"),
    (0.100004, "0.1", "matched"),
    (-0.100004, "-0.1", "matched"),
])
def test_significant_rounding_is_asymmetric_at_signed_powers_of_ten(expected, token, status):
    result = capture.compare_values([[expected]], [[token]], ["a"], ["b"], 5)
    assert result["status"] == status
    item = result["largest_error"]
    assert item["rounding_bound"] == 5e-6
    assert item["rounding_bound_used"] == (5e-7 if abs(expected) < 0.1 else 5e-6)


def test_counts_are_exact_even_when_float_conversion_would_hide_a_fraction():
    result = capture.compare_values([[321.0]], [["321.000000000000001"]], ["Individuals"], ["1"],
                                    4, exact_rows=("Individuals",))
    assert result["status"] == "different"
    assert result["failed_values"] == 1


def test_native_c1_c2_and_c3_captures_match_declared_outputs():
    result = capture.compare_captures(ROOT / "benchmarks/past/legacy-data/llanvirn.dat",
                                     ROOT / "references/past/captures")
    assert result["status"] == "matched"
    assert result["case_count"] == 13
    assert result["compared_values"] == result["matched_values"] == 1059
    assert result["cases"][2]["uncompared_rows"]
    assert result["cases"][2]["significant_digits"] == 4
    assert result["cases"][3]["expected_pairs_from_source"] == 103
    assert result["cases"][3]["past_exported_pair_count"] is None
    paired = result["cases"][9]["artifacts"][1]
    assert paired["native_row_count"] == 103
    assert [group["past_observed_pair_count"] for group in paired["groups"]] == [103, 79, 35]
    assert all(case["percent_convention"] == "absolute" for case in result["cases"][10:])
    assert all(case["percent_definition_status"] == "explained_difference" for case in result["cases"][10:])
    assert result["verified_capture_manifests"] == 13
    assert result["verified_capture_output_artifacts"] == 63


@pytest.mark.parametrize("change,match", [
    ("missing_manifest", "unavailable"),
    ("wrong_hash", "fingerprint"),
    ("wrong_settings", "settings"),
    ("wrong_precision", "precision"),
    ("wrong_input", "input identity"),
    ("outside_path", "Unsafe capture"),
])
def test_comparison_rejects_manifest_faults_even_when_export_numbers_match(tmp_path, change, match):
    folder = tmp_path / "c1-bray-raw"
    shutil.copytree(ROOT / "references/past/captures/c1-bray-raw", folder)
    manifest = folder / "capture.json"
    record = json.loads(manifest.read_text())
    if change == "missing_manifest":
        manifest.unlink()
    else:
        if change == "wrong_hash":
            record["outputs"][0]["sha256"] = "0" * 64
        elif change == "wrong_settings":
            record["settings"]["index"] = "Jaccard"
        elif change == "wrong_precision":
            record["outputs"][0]["significant_digits"] = 4
        elif change == "wrong_input":
            record["input"]["path"] = "benchmarks/past/legacy-data/dielasma.dat"
        elif change == "outside_path":
            record["outputs"][0]["path"] = "references/past/captures/c1-bray-raw/../../../outside"
        manifest.write_text(json.dumps(record))
    with pytest.raises(capture.CaptureError, match=match):
        capture.compare_captures(ROOT / "benchmarks/past/legacy-data/llanvirn.dat", tmp_path)


def test_stale_diversity_capture_is_not_accepted_for_current_settings():
    reference = json.loads((ROOT / "references/r/community-vegan.json").read_text())
    stale = ROOT / "references/past/captures/c2-before-recompute/raw/indices.tsv"
    result = capture.compare_diversity(stale.read_bytes(), reference)
    assert result["status"] == "different"
    assert result["failed_values"] == 20
    assert all(item["row"] in {"Simpson_1-D", "Shannon_H"} for item in result["failures"])


def tiny_result():
    return {"sample_ids": ["a", "b"], "distances": [[0, 0.25], [0.25, 0]]}


@pytest.mark.parametrize("raw,match", [
    (b"\ta\tx\na\t1\t0.75\nb\t0.75\t1\n", "column labels"),
    (b"\ta\tb\na\t1\t0.75\nx\t0.75\t1\n", "row labels"),
    (b"\ta\tb\na\t0\t0.75\nb\t0.75\t1\n", "diagonal"),
    (b"\ta\tb\na\t1\t0.75\nb\t0.74\t1\n", "symmetric"),
    (b"\ta\tb\na\t1\t0.75\n", "row labels"),
])
def test_similarity_structure_is_checked(raw, match):
    with pytest.raises(capture.CaptureError, match=match):
        capture.compare_similarity_matrix(raw, tiny_result())


def test_changed_symmetric_numeric_capture_fails():
    altered = b"\ta\tb\na\t1\t0.750001\nb\t0.750001\t1\n"
    result = capture.compare_similarity_matrix(altered, tiny_result())
    assert result["status"] == "different"
    assert result["failed_values"] == 2


def test_frozen_input_tampering_rejected_before_comparison(tmp_path):
    source = tmp_path / "llanvirn.dat"
    source.write_text("different data")
    with pytest.raises(capture.CaptureError, match="fingerprint"):
        capture.compare_captures(source, tmp_path)


@pytest.mark.parametrize("change,match", [
    (lambda text: text.replace("L1/X1-L1/X2", "L2/X1-L2/X2"), "header"),
    (lambda text: text.replace("r:\t0.98329", "r_missing:\t0.98329"), "required point-estimate"),
])
def test_regression_capture_identity_and_point_fields_are_checked(change, match):
    raw = (ROOT / "references/past/captures/c3-l1-raw/raw/statistics.txt").read_text()
    with pytest.raises(capture.CaptureError, match=match):
        capture.compare_rma_statistics(change(raw).encode(), {}, x="L1/X1", y="L1/X2", transform="none")


def test_all_six_export_rejects_partially_missing_locality_pair():
    path = ROOT / "references/past/captures/c3-all6-l1-raw/raw/residuals.tsv"
    lines = path.read_text().splitlines()
    cells = lines[-1].split("\t")
    cells[4] = "1"
    lines[-1] = "\t".join(cells)
    fake = {1: {"pairs": [{"sample_id": str(i + 1), "x_raw": 1.0, "y_raw": 1.0} for i in range(103)],
                "n": 103, "intercept": 0.0, "slope": 1.0},
            2: {"pairs": [{"sample_id": str(i + 1), "x_raw": 1.0, "y_raw": 1.0} for i in range(79)],
                "n": 79, "intercept": 0.0, "slope": 1.0}}
    with pytest.raises(capture.CaptureError, match="partially empty"):
        capture.compare_all_pairs("\n".join(lines).encode(), fake, [str(i + 1) for i in range(103)])


@pytest.fixture(scope="module")
def pcoa_case():
    path = ROOT / "benchmarks/past/legacy-data/llanvirn.dat"
    spec = capture.CommunitySpec(method="community", input=path, format="past", orientation="taxa_by_samples",
                                 value_type="count", transform="none", distance="braycurtis", dimensions=4,
                                 missing="error", empty_samples="error")
    result = capture.calculate_community(spec, path.read_bytes())
    folder = ROOT / "references/past/captures/c4-bray-raw/raw"
    return (folder / "eigenvalues.tsv").read_bytes(), (folder / "scores.tsv").read_bytes(), result


def test_nonzero_eigenvalue_cannot_be_discarded_as_structural_null(pcoa_case):
    eigen, scores, result = pcoa_case
    altered = eigen.replace(b"1.3556E-16", b"0.00001")
    assert altered != eigen
    with pytest.raises(capture.CaptureError, match="structural null"):
        capture.compare_pcoa(altered, scores, result)


@pytest.mark.parametrize("factor,expected_status", [(-1, "matched"), (1.01, "different")])
def test_pcoa_axis_sign_is_allowed_but_rescaling_is_not(pcoa_case, factor, expected_status):
    eigen, scores, result = pcoa_case
    rows = [line.split("\t") for line in scores.decode().splitlines()]
    for row in rows[1:]:
        row[1] = format(float(row[1]) * factor, ".5g")
    altered = ("\n".join("\t".join(row) for row in rows) + "\n").encode()
    comparison = capture.compare_pcoa(eigen, altered, result)
    assert comparison["status"] == expected_status
