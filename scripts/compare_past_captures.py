"""Compare declared native PAST captures with frozen Python workflows."""

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path, PurePosixPath
import platform
import re
import sys

import numpy as np
import palaeo_agent

from palaeo_agent.community import CommunitySpec, calculate_community
from palaeo_agent.core import RmaSpec, calculate, load_past


ROOT = Path(__file__).resolve().parents[1]
INPUT_SHA256 = "a39a2ec7ef405623efdac5e5cd2b9be7dd38e5ca98c4fe9efa4dab2cda076f37"
DIELASMA_SHA256 = "1e471093a057df4d81c944d9f41d2dff4649b205a653c9402083b4a1768249bd"
FLOAT_ALLOWANCE_ULPS = 8
NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


class CaptureError(ValueError):
    pass


def decimal_value(token):
    if not isinstance(token, str) or NUMBER.fullmatch(token) is None:
        raise CaptureError(f"Invalid native numeric token: {token!r}")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise CaptureError(f"Invalid native numeric token: {token!r}") from exc
    if not value.is_finite():
        raise CaptureError("Native values must be finite")
    return value


def rounding_bound(token, significant_digits):
    """Half a rounded last-place unit, restoring omitted trailing zeroes."""
    if not isinstance(significant_digits, int) or isinstance(significant_digits, bool) or significant_digits < 1:
        raise CaptureError("Declared significant digits must be a positive integer")
    value = decimal_value(token)
    if value == 0:
        return Decimal(0)
    exponent = min(value.as_tuple().exponent, value.adjusted() - significant_digits + 1)
    return Decimal("0.5") * Decimal(10) ** exponent


def directional_rounding_bound(token, significant_digits, expected):
    value = decimal_value(token)
    bound = rounding_bound(token, significant_digits)
    if (value and value.copy_abs().normalize().as_tuple().digits == (1,) and
        Decimal(str(expected)).copy_abs() < value.copy_abs()):
        return bound / 10
    return bound


def read_table(data, expected_columns):
    try:
        rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter="\t"))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise CaptureError("Capture must be UTF-8 TSV") from exc
    if not rows or not rows[0] or rows[0][0] != "":
        raise CaptureError("Expected a blank corner followed by native column labels")
    columns = rows[0][1:]
    if columns != list(expected_columns) or len(set(columns)) != len(columns):
        raise CaptureError("Native column labels/order differ from the declared labels")
    labels, tokens = [], []
    for row in rows[1:]:
        if len(row) != len(columns) + 1 or not row[0]:
            raise CaptureError("Native row width or label is invalid")
        labels.append(row[0])
        tokens.append(row[1:])
    if len(set(labels)) != len(labels):
        raise CaptureError("Native row labels must be unique")
    return labels, tokens


def compare_values(expected, tokens, rows, columns, significant_digits, *, exact_rows=()):
    if len(expected) != len(tokens) or len(rows) != len(tokens):
        raise CaptureError("Expected and captured row dimensions differ")
    comparisons = []
    for label, actual_row, token_row in zip(rows, expected, tokens, strict=True):
        if len(actual_row) != len(columns) or len(token_row) != len(columns):
            raise CaptureError("Expected and captured column dimensions differ")
        for column, target, token in zip(columns, actual_row, token_row, strict=True):
            observed_decimal = decimal_value(token)
            observed = float(observed_decimal)
            if not np.isfinite(target) or not np.isfinite(observed):
                raise CaptureError("Comparison values must be finite float64 numbers")
            exact = label in exact_rows
            bound = 0.0 if exact else float(rounding_bound(token, significant_digits))
            used_bound = 0.0 if exact else float(directional_rounding_bound(token, significant_digits, target))
            allowance = 0.0 if exact else FLOAT_ALLOWANCE_ULPS * np.finfo(float).eps * max(1.0, abs(target))
            error = abs(observed - target)
            matched = observed_decimal == Decimal(str(target)) if exact else error <= used_bound + allowance
            comparisons.append({
                "row": label, "column": column, "native_token": token,
                "expected": float(target), "absolute_error": float(error),
                "rounding_bound": bound, "rounding_bound_used": used_bound, "float_allowance": float(allowance),
                "matched": bool(matched),
                "ratio_to_rounding_bound": float(error / used_bound) if used_bound else None,
            })
    failures = [item for item in comparisons if not item["matched"]]
    ratios = [item["ratio_to_rounding_bound"] for item in comparisons if item["ratio_to_rounding_bound"] is not None]
    return {
        "status": "matched" if not failures else "different",
        "compared_values": len(comparisons), "matched_values": len(comparisons) - len(failures),
        "failed_values": len(failures),
        "max_absolute_error": max((item["absolute_error"] for item in comparisons), default=0.0),
        "max_ratio_to_rounding_bound": max(ratios, default=0.0),
        "largest_error": max(comparisons, key=lambda item: item["absolute_error"], default=None),
        "failures": failures[:10], "failure_examples_limit": 10,
    }


def compare_similarity_matrix(data, result, *, significant_digits=8):
    samples = result["sample_ids"]
    labels, tokens = read_table(data, samples)
    if labels != samples:
        raise CaptureError("Native matrix row labels/order differ from the frozen sample IDs")
    values = [[decimal_value(token) for token in row] for row in tokens]
    for i in range(len(samples)):
        if values[i][i] != 1:
            raise CaptureError("Native similarity matrix diagonal must be exactly one")
        for j in range(len(samples)):
            if not 0 <= values[i][j] <= 1:
                raise CaptureError("Native similarities must lie in [0, 1]")
            if values[i][j] != values[j][i]:
                raise CaptureError("Native similarity matrix must be symmetric")
    expected = 1.0 - np.asarray(result["distances"])
    summary = compare_values(expected, tokens, samples, samples, significant_digits)
    summary.update({"significant_digits": significant_digits,
                    "interpretation": "PAST similarity compared with 1 - Python distance",
                    "shape": [len(samples), len(samples)], "diagonal_values": len(samples),
                    "distinct_off_diagonal_pairs": len(samples) * (len(samples) - 1) // 2,
                    "structure": "labels, dimensions, exact symmetry, unit diagonal and [0,1] bounds verified"})
    return summary


def compare_diversity(data, result, *, significant_digits=4):
    fields = {"Taxa_S": "richness", "Individuals": "total", "Simpson_1-D": "simpson", "Shannon_H": "shannon"}
    labels, tokens = read_table(data, result["sample_ids"])
    lookup = dict(zip(labels, tokens, strict=True))
    missing = set(fields) - lookup.keys()
    if missing:
        raise CaptureError(f"Missing declared diversity rows: {sorted(missing)}")
    rows = list(fields)
    expected = [[sample[fields[label]] for sample in result["diversity"]] for label in rows]
    summary = compare_values(expected, [lookup[label] for label in rows], rows, result["sample_ids"],
                             significant_digits, exact_rows=("Taxa_S", "Individuals"))
    summary.update({"significant_digits": significant_digits,
                    "compared_rows": rows, "uncompared_rows": [label for label in labels if label not in fields],
                    "exact_count_rows": ["Taxa_S", "Individuals"],
                    "interpretation": "Observed plug-in diversity; unbiased and ACE correction off, natural-log Shannon"})
    return summary


def compare_rma_statistics(data, result, *, x, y, transform, significant_digits=5):
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise CaptureError("Regression capture must be UTF-8 text") from exc
    header = f"RMA Regression: {x}-{y}" + (", log-log transformed" if transform == "log10" else "")
    if not lines or lines[0] != header:
        raise CaptureError("Native regression header differs from the declared pair or transformation")
    fields = {}
    for line in lines[1:]:
        cells = line.split("\t")
        field = None
        if len(cells) >= 4 and cells[0] == "Slope a:" and cells[2] == "Std. error a:":
            field = "slope"
        elif len(cells) >= 4 and cells[0] == "Intercept b:" and cells[2] == "Std. error b:":
            field = "intercept"
        elif len(cells) == 2 and cells[0] == "r:":
            field = "correlation"
        if field:
            if field in fields:
                raise CaptureError(f"Duplicate native regression point-estimate field: {field}")
            decimal_value(cells[1])
            fields[field] = cells[1]
    rows = ["slope", "intercept", "correlation"]
    if set(fields) != set(rows):
        raise CaptureError("Native regression capture lacks a required point-estimate field")
    summary = compare_values([[result[field]] for field in rows], [[fields[field]] for field in rows],
                             rows, ["value"], significant_digits)
    summary.update({"significant_digits": significant_digits, "compared_fields": rows,
                    "x": x, "y": y, "transform": transform,
                    "expected_pairs_from_source": result["n"], "past_exported_pair_count": None,
                    "uncompared_outputs": ["standard errors", "bootstrap confidence intervals", "t statistics",
                                           "p values", "permutation results", "r squared"],
                    "interpretation": "Descriptive RMA point estimates only; pair count is verified from source, not the PAST export"})
    return summary


def artifact_record(path, raw, comparison):
    return {"artifact": str(path), "artifact_sha256": hashlib.sha256(raw).hexdigest(),
            "artifact_bytes": len(raw), **comparison}


def execution_provenance():
    source = Path(palaeo_agent.__file__).resolve().parent
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(source.glob("*.py"))}
    lock = ROOT / "uv.lock"
    return {"runtime": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
            "code_provenance": {"palaeo_agent_version": importlib.metadata.version("palaeo-agent"),
                "source_files_sha256": hashes,
                "implementation_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                "comparison_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() else None}}


def capture_path(capture_root, source_path, case_id):
    if not isinstance(source_path, str) or "\\" in source_path:
        raise CaptureError("Unsafe capture artefact path")
    relative = PurePosixPath(source_path)
    prefix = PurePosixPath("references/past/captures")
    if (relative.is_absolute() or ".." in relative.parts or str(relative) != source_path or
        relative.parts[:4] != (*prefix.parts, case_id)):
        raise CaptureError("Unsafe capture artefact path or wrong case prefix")
    candidate = capture_root / relative.relative_to(prefix)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise CaptureError(f"Capture artefact is unavailable: {source_path}") from exc
    if not resolved.is_relative_to(capture_root) or candidate.is_symlink() or not candidate.is_file():
        raise CaptureError("Capture artefact must be a regular file inside the capture root")
    return candidate


def verify_capture_manifest(capture_root, case_id, input_name, settings, precisions):
    root = Path(capture_root).resolve()
    source = f"references/past/captures/{case_id}/capture.json"
    path = capture_path(root, source, case_id)
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise CaptureError("Capture manifest is not valid JSON") from exc
    expected_input = {"path": f"benchmarks/past/legacy-data/{input_name}",
                      "sha256": DIELASMA_SHA256 if input_name == "dielasma.dat" else INPUT_SHA256}
    if not isinstance(manifest, dict) or manifest.get("case_id") != case_id or manifest.get("input") != expected_input:
        raise CaptureError("Capture manifest case or input identity differs from the declared comparison")
    declared = manifest.get("settings")
    if not isinstance(declared, dict) or any(type(declared.get(key)) is not type(value) or declared[key] != value
                                             for key, value in settings.items()):
        raise CaptureError("Capture manifest settings differ from the declared comparison")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise CaptureError("Capture manifest must enumerate its output artefacts")
    paths, native = set(), {}
    for entry in outputs:
        if not isinstance(entry, dict):
            raise CaptureError("Invalid capture output record")
        output_path = entry.get("path")
        artifact = capture_path(root, output_path, case_id)
        if output_path in paths:
            raise CaptureError("Capture output paths must be unique")
        paths.add(output_path)
        expected_hash, expected_bytes = entry.get("sha256"), entry.get("bytes")
        if (not isinstance(expected_hash, str) or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None or
            type(expected_bytes) is not int or expected_bytes < 0):
            raise CaptureError("Invalid capture output fingerprint record")
        content = artifact.read_bytes()
        if len(content) != expected_bytes or hashlib.sha256(content).hexdigest() != expected_hash:
            raise CaptureError(f"Capture artefact fingerprint differs from its manifest: {output_path}")
        if entry.get("kind") == "native_export":
            suffix = str(PurePosixPath(output_path).relative_to(PurePosixPath("references/past/captures") / case_id))
            digits = entry.get("significant_digits")
            if suffix not in precisions or type(digits) is not int or digits != precisions[suffix]:
                raise CaptureError("Capture native precision or output identity differs from the declared comparison")
            native[suffix] = digits
    if native != precisions:
        raise CaptureError("Capture manifest omits a required native export")
    return {"path": source, "sha256": hashlib.sha256(raw).hexdigest(),
            "verified_output_artifacts": len(outputs), "input": expected_input,
            "verified_settings": settings, "verified_native_precision": native}


def verified_capture_manifests(capture_root):
    declarations = {}
    for case_id, index in (("c1-bray-raw", "Bray-Curtis"), ("c1-jaccard", "Jaccard")):
        declarations[case_id] = ("llanvirn.dat", {"index": index, "data_transform": "none",
            "output_semantics": "similarity (diagonal 1), compared with 1 - distance",
            "orientation": "samples_by_taxa"}, {"raw/matrix.tsv": 8})
    declarations["c2-diversity"] = ("llanvirn.dat", {"unbiased_versions": False, "use_ACE_for_S": False,
        "log2": False, "CI_type": "None", "orientation": "taxa_by_samples",
        "recomputed_after_setting_change": True}, {"raw/indices.tsv": 4})
    for locality in (1, 2, 3):
        for suffix, transform in (("raw", "none"), ("log10", "log10")):
            declarations[f"c3-l{locality}-{suffix}"] = ("dielasma.dat", {"method": "RMA",
                "x": f"L{locality}/X1", "y": f"L{locality}/X2", "selected_columns": "specified pair only",
                "transform": transform, "zero_intercept": False}, {"raw/statistics.txt": 5})
    declarations["c3-all6-l1-raw"] = ("dielasma.dat", {"method": "RMA", "x": "L1/X1", "y": "L1/X2",
        "selected_columns": "all six", "transform": "none", "zero_intercept": False},
        {"raw/statistics.txt": 5, "raw/residuals.tsv": 5})
    for case_id, index, transform in (("c4-bray-raw", "Bray-Curtis", "none"),
        ("c4-jaccard", "Jaccard", "none"), ("c4-bray-relative", "Bray-Curtis", "row percentage")):
        precision = {"raw/eigenvalues.tsv": 5, "raw/scores.tsv": 5}
        if case_id == "c4-bray-raw":
            precision["raw/scores-unscaled.tsv"] = 5
        declarations[case_id] = ("llanvirn.dat", {"index": index, "data_transform": transform,
            "transformation_exponent": 2, "eigenvalue_scale": True, "correction": "none offered in this module",
            "orientation": "samples_by_taxa", "recomputed_after_setting_change": True}, precision)
    return {case_id: verify_capture_manifest(capture_root, case_id, *declaration)
            for case_id, declaration in declarations.items()}


def combine_summaries(parts):
    return {"status": "matched" if all(part["status"] == "matched" for part in parts) else "different",
            **{field: sum(part[field] for part in parts) for field in ("compared_values", "matched_values", "failed_values")},
            **{field: max(part[field] for part in parts) for field in ("max_absolute_error", "max_ratio_to_rounding_bound")}}


def compare_all_pairs(data, results, source_ids, *, significant_digits=5):
    try:
        lines = list(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter="\t"))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise CaptureError("Native paired-data export must be UTF-8 TSV") from exc
    header = [label for site in (1, 2, 3) for label in (f"L{site}/X1", f"L{site}/X2", "Regress.", "Residual")]
    if not lines or lines[0] != header:
        raise CaptureError("Native paired-data header differs from the declared six measurement columns")
    rows = lines[1:]
    if len(rows) != len(source_ids) or any(len(row) != len(header) for row in rows):
        raise CaptureError("Native paired-data row dimensions differ from the frozen source")
    groups = []
    for site in (1, 2, 3):
        result = results[site]
        expected = {row["sample_id"]: row for row in result["pairs"]}
        observed_tokens, expected_values, retained_ids = [], [], []
        observed_count = 0
        for sample_id, row in zip(source_ids, rows, strict=True):
            cells = row[(site - 1) * 4:site * 4]
            present = [bool(token) for token in cells]
            if any(present) and not all(present):
                raise CaptureError("Native paired-data group has a partially empty row")
            observed_count += all(present)
            if bool(sample_id in expected) != all(present):
                raise CaptureError("Native paired-data missing mask differs from its locality's source pairs")
            if sample_id in expected:
                pair = expected[sample_id]
                retained_ids.append(sample_id)
                observed_tokens.append(cells[:3])
                expected_values.append([pair["x_raw"], pair["y_raw"], result["intercept"] + result["slope"] * pair["x_raw"]])
        summary = compare_values(expected_values, observed_tokens, retained_ids,
                                 [f"L{site}/X1", f"L{site}/X2", "Regress."], significant_digits)
        groups.append({"locality": f"L{site}", "past_observed_pair_count": observed_count,
                       "expected_pairs_from_source": result["n"], "missing_mask": "matched",
                       "row_identity": "source order checked by observed X and Y values; native table has no row-ID column",
                       **summary})
    return {**combine_summaries(groups), "significant_digits": significant_digits,
            "native_row_count": len(rows), "native_column_count": len(header),
            "groups": groups, "uncompared_columns": "Residual in each locality block",
            "interpretation": "Six-column selection retains each locality's complete pairs; observed X/Y and fitted values compared"}


def score_tokens(data, sample_ids):
    try:
        header = next(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter="\t"))
    except (UnicodeDecodeError, csv.Error, StopIteration) as exc:
        raise CaptureError("Native PCoA scores must be nonempty UTF-8 TSV") from exc
    columns = [f"Coord {i + 1}" for i in range(len(header) - 1)]
    if len(columns) < 4:
        raise CaptureError("Native PCoA export lacks four coordinate axes")
    labels, tokens = read_table(data, columns)
    if labels != sample_ids:
        raise CaptureError("Native PCoA score rows differ from the declared source sample order")
    return columns, [row[:4] for row in tokens]


def compare_pcoa(eigen_data, score_data, result, *, unscaled_data=None, significant_digits=5):
    try:
        rows = list(csv.reader(io.StringIO(eigen_data.decode("utf-8-sig")), delimiter="\t"))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise CaptureError("Native PCoA eigenvalues must be UTF-8 TSV") from exc
    expected_axes = [str(i + 1) for i in range(result["n"])]
    if (not rows or rows[0] != ["Axis", "Eigenvalue", "Percent"] or
        any(len(row) != 3 for row in rows[1:]) or [row[0] for row in rows[1:]] != expected_axes):
        raise CaptureError("Native PCoA spectrum axes/header differ from the complete source sample count")
    native_eigen = np.asarray([float(decimal_value(row[1])) for row in rows[1:]])
    eigen = np.asarray(result["eigenvalues"])
    scale = float(np.max(np.abs(eigen)))
    null_tolerance = float(128 * np.finfo(float).eps * len(eigen) * scale)
    nulls = [i for i in range(len(eigen)) if abs(eigen[i]) <= null_tolerance and abs(native_eigen[i]) <= null_tolerance]
    if len(nulls) != 1:
        raise CaptureError("Expected exactly one shared structural null eigenvalue within the declared roundoff tolerance")
    retained = [i for i in range(len(eigen)) if i not in nulls]
    spectrum = compare_values([[eigen[i]] for i in retained], [[rows[i + 1][1]] for i in retained],
                              [expected_axes[i] for i in retained], ["Eigenvalue"], significant_digits)
    columns, tokens = score_tokens(score_data, result["sample_ids"])
    observed = np.asarray([[float(decimal_value(token)) for token in row] for row in tokens])
    coordinates = np.asarray(result["coordinates"])[:, :4]
    gaps = []
    for axis in range(4):
        adjacent = [eigen[axis] - eigen[axis + 1]]
        if axis:
            adjacent.append(eigen[axis - 1] - eigen[axis])
        gaps.append(float(min(adjacent) / eigen[0]))
    if min(gaps) <= 1e-8:
        raise CaptureError("PCoA axes are not individually identified at the declared relative eigengap threshold")
    signs = [1 if np.dot(coordinates[:, axis], observed[:, axis]) >= 0 else -1 for axis in range(4)]
    scores = compare_values(coordinates * signs, tokens, result["sample_ids"], columns[:4], significant_digits)
    positive = eigen[eigen > result["eigenvalue_tolerance"]]
    denominators = {"positive": float(positive.sum()), "signed": float(eigen.sum()), "absolute": float(np.abs(eigen).sum())}
    percent_candidates = {}
    for name, denominator in denominators.items():
        percent_candidates[name] = {"denominator": denominator,
            **compare_values([[100 * eigen[i] / denominator] for i in retained], [[rows[i + 1][2]] for i in retained],
                             [expected_axes[i] for i in retained], ["Percent"], significant_digits)}
    matched_candidates = [name for name, candidate in percent_candidates.items() if candidate["status"] == "matched"]
    convention = matched_candidates[0] if len(matched_candidates) == 1 else "ambiguous_or_unresolved"
    summary = {**combine_summaries([spectrum, scores]), "significant_digits": significant_digits,
        "spectrum": spectrum, "scaled_scores": scores,
        "compared_coordinate_axes": [1, 2, 3, 4], "axis_signs": signs,
        "minimum_adjacent_relative_eigengaps": gaps, "relative_eigengap_threshold": 1e-8,
        "native_score_columns": columns, "uncompared_score_columns": columns[4:],
        "sample_identity": "Native numeric row labels matched to declared frozen source order",
        "structural_null": {"axis": nulls[0] + 1, "native_token": rows[nulls[0] + 1][1],
                            "python_value": float(eigen[nulls[0]]), "absolute_tolerance": null_tolerance,
                            "rule": "128 * float64 epsilon * n * largest absolute eigenvalue; both values must qualify",
                            "excluded_from_numeric_count": True},
        "percent_convention": convention,
        "percent_definition_status": ("matched" if convention == "positive" else
                                      "explained_difference" if convention in {"signed", "absolute"} else "unresolved"),
        "percent_candidates": percent_candidates,
        "percent_scope": "Candidate denominator checks diagnose PAST's convention; excluded from product-match counts because product fractions use positive inertia",
        "interpretation": "Nine non-null eigenvalues and four scaled coordinate axes compared; sign flips only, no rescaling or rotation"}
    if unscaled_data is not None:
        unscaled_columns, unscaled_tokens = score_tokens(unscaled_data, result["sample_ids"])
        unscaled_observed = np.asarray([[float(decimal_value(token)) for token in row] for row in unscaled_tokens])
        unit_axes = coordinates / np.sqrt(eigen[:4])
        unscaled_signs = [1 if np.dot(unit_axes[:, axis], unscaled_observed[:, axis]) >= 0 else -1 for axis in range(4)]
        summary["unscaled_diagnostic"] = {**compare_values(unit_axes * unscaled_signs, unscaled_tokens,
            result["sample_ids"], unscaled_columns[:4], significant_digits), "axis_signs": unscaled_signs,
            "scope": "Unit eigenvectors explain scaling-off output; diagnostic only, excluded from product-match count"}
    return summary


def compare_captures(input_path, capture_root):
    data = Path(input_path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != INPUT_SHA256:
        raise CaptureError("Frozen Llanvirn input fingerprint differs from the declared reference")
    manifests = verified_capture_manifests(capture_root)
    results = {}
    for distance in ("braycurtis", "jaccard"):
        spec = CommunitySpec(method="community", input=Path(input_path), format="past", orientation="taxa_by_samples",
                             value_type="count", transform="none", distance=distance, dimensions=2,
                             missing="error", empty_samples="error")
        results[distance] = calculate_community(spec, data)
    cases = []
    for name, filename, kind, distance, digits in (
        ("c1-bray-raw", "matrix.tsv", "similarity", "braycurtis", 8),
        ("c1-jaccard", "matrix.tsv", "similarity", "jaccard", 8),
        ("c2-diversity", "indices.tsv", "diversity", "braycurtis", 4),
    ):
        artifact = Path(capture_root) / name / "raw" / filename
        raw = artifact.read_bytes()
        comparison = (compare_similarity_matrix(raw, results[distance], significant_digits=digits)
                      if kind == "similarity" else compare_diversity(raw, results[distance], significant_digits=digits))
        cases.append({"case_id": name, "input_id": "llanvirn", **artifact_record(artifact, raw, comparison)})
    dielasma_path = Path(input_path).with_name("dielasma.dat")
    dielasma = dielasma_path.read_bytes()
    dielasma_hash = hashlib.sha256(dielasma).hexdigest()
    if dielasma_hash != DIELASMA_SHA256:
        raise CaptureError("Frozen Dielasma input fingerprint differs from the declared reference")
    raw_results = {}
    for locality in (1, 2, 3):
        for suffix, transform in (("raw", "none"), ("log10", "log10")):
            name = f"c3-l{locality}-{suffix}"
            x, y = f"L{locality}/X1", f"L{locality}/X2"
            spec = RmaSpec(method="rma", input=dielasma_path, format="past", x=x, y=y,
                           transform=transform, missing="drop_pairs")
            result = calculate(spec, dielasma)
            if transform == "none":
                raw_results[locality] = result
            artifact = Path(capture_root) / name / "raw/statistics.txt"
            raw = artifact.read_bytes()
            comparison = compare_rma_statistics(raw, result, x=x, y=y, transform=transform)
            cases.append({"case_id": name, "input_id": "dielasma", **artifact_record(artifact, raw, comparison)})
    folder = Path(capture_root) / "c3-all6-l1-raw/raw"
    statistics_path, pairs_path = folder / "statistics.txt", folder / "residuals.tsv"
    statistics_raw, pairs_raw = statistics_path.read_bytes(), pairs_path.read_bytes()
    statistics = compare_rma_statistics(statistics_raw, raw_results[1], x="L1/X1", y="L1/X2", transform="none")
    _, _, source_ids, _ = load_past(dielasma, spec)
    pairs = compare_all_pairs(pairs_raw, raw_results, source_ids)
    cases.append({"case_id": "c3-all6-l1-raw", "input_id": "dielasma",
                  **combine_summaries([statistics, pairs]),
                  "artifacts": [artifact_record(statistics_path, statistics_raw, statistics),
                                artifact_record(pairs_path, pairs_raw, pairs)]})
    for name, transform, distance in (("c4-bray-raw", "none", "braycurtis"),
                                       ("c4-jaccard", "none", "jaccard"),
                                       ("c4-bray-relative", "relative_abundance", "braycurtis")):
        folder = Path(capture_root) / name / "raw"
        spec = CommunitySpec(method="community", input=Path(input_path), format="past", orientation="taxa_by_samples",
                             value_type="count", transform=transform, distance=distance, dimensions=4,
                             missing="error", empty_samples="error")
        result = calculate_community(spec, data)
        eigen_path, scores_path = folder / "eigenvalues.tsv", folder / "scores.tsv"
        eigen_raw, scores_raw = eigen_path.read_bytes(), scores_path.read_bytes()
        unscaled_path = folder / "scores-unscaled.tsv"
        unscaled_raw = unscaled_path.read_bytes() if unscaled_path.exists() else None
        comparison = compare_pcoa(eigen_raw, scores_raw, result, unscaled_data=unscaled_raw)
        artifacts = [artifact_record(eigen_path, eigen_raw, comparison["spectrum"]),
                     artifact_record(scores_path, scores_raw, comparison["scaled_scores"])]
        if unscaled_raw is not None:
            artifacts.append(artifact_record(unscaled_path, unscaled_raw, comparison["unscaled_diagnostic"]))
        cases.append({"case_id": name, "input_id": "llanvirn", **comparison, "artifacts": artifacts})
    for case in cases:
        case["capture_manifest"] = manifests[case["case_id"]]
    return {
        "status": "matched" if all(case["status"] == "matched" for case in cases) else "different",
        **execution_provenance(),
        "inputs": {"llanvirn": {"path": str(input_path), "sha256": digest, "bytes": len(data)},
                   "dielasma": {"path": str(dielasma_path), "sha256": dielasma_hash, "bytes": len(dielasma)}},
        "rounding_policy": "Half a last-place unit at each case's declared significant digits; omitted trailing zeroes restored; at signed powers of ten the toward-zero bound is one order finer",
        "rounding_assumption": "Native export rounds rather than truncates",
        "float_allowance": f"{FLOAT_ALLOWANCE_ULPS} * float64 epsilon * max(1, abs(expected)); zero for exact count rows",
        "case_count": len(cases), "compared_values": sum(case["compared_values"] for case in cases),
        "verified_capture_manifests": len(manifests),
        "verified_capture_output_artifacts": sum(item["verified_output_artifacts"] for item in manifests.values()),
        "matched_values": sum(case["matched_values"] for case in cases),
        "max_absolute_error": max(case["max_absolute_error"] for case in cases),
        "max_ratio_to_rounding_bound": max(case["max_ratio_to_rounding_bound"] for case in cases),
        "cases": cases,
        "scope": "Only named captured outputs and declared settings; no claim for other PAST methods, indices or full workflow parity",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, default=ROOT / "references/past/captures")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)
    try:
        result = compare_captures(ROOT / "benchmarks/past/legacy-data/llanvirn.dat", arguments.captures)
        text = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if arguments.output:
            arguments.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0 if result["status"] == "matched" else 1
    except (OSError, CaptureError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
