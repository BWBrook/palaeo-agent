"""Checked, self-contained comparisons of two descriptive community runs."""

import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import uuid

import numpy as np

from .core import AnalysisError
from .runs import inspect_run


EIGENGAP_THRESHOLD = 1e-8
REPORT_TOLERANCE = 1e-10


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _average_ranks(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="stable")
    ranked = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranked[order[start:end]] = (start + end - 1) / 2 + 1
        start = end
    return ranked


def _correlation(left, right):
    left, right = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if len(left) < 2 or np.ptp(left) == 0 or np.ptp(right) == 0:
        return None
    value = float(np.corrcoef(left, right)[0, 1])
    return float(np.clip(value, -1, 1)) if np.isfinite(value) else None


def _relative_eigengap(result):
    eigenvalues = result["eigenvalues"]
    k = result["dimensions"]
    return float((eigenvalues[k - 1] - eigenvalues[k]) / eigenvalues[0])


def _procrustes_m2(left, right):
    left, right = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    left, right = left - left.mean(axis=0), right - right.mean(axis=0)
    norm_left, norm_right = np.linalg.norm(left), np.linalg.norm(right)
    if norm_left == 0 or norm_right == 0:
        return None
    try:
        singular_values = np.linalg.svd((left / norm_left).T @ (right / norm_right), compute_uv=False)
    except np.linalg.LinAlgError as exc:
        raise AnalysisError("comparison_ordination", "Procrustes decomposition did not converge") from exc
    return float(np.clip(1 - float(singular_values.sum()) ** 2, 0, 1))


def _checked_pair(baseline_run, sensitivity_run):
    baseline, sensitivity = inspect_run(baseline_run), inspect_run(sensitivity_run)
    if any(record["result"]["method"] != "community" for record in (baseline, sensitivity)):
        raise AnalysisError("comparison_method", "Sensitivity comparisons require two community runs")
    left_environment, right_environment = baseline["environment"], sensitivity["environment"]
    changed_environment = [key for key in ("implementation_sha256", "python")
                           if left_environment[key] != right_environment[key]]
    if left_environment["packages"]["numpy"] != right_environment["packages"]["numpy"]:
        changed_environment.append("numpy")
    if changed_environment:
        raise AnalysisError("comparison_environment", "Implementation, Python and NumPy must match across sensitivity arms",
                            fields=changed_environment)
    roles = baseline["manifest"]["inputs"]
    other_roles = sensitivity["manifest"]["inputs"]
    if set(roles) != set(other_roles) or any(
        (item["sha256"], item["bytes"]) != (other_roles[role]["sha256"], other_roles[role]["bytes"])
        for role, item in roles.items()
    ):
        raise AnalysisError("comparison_inputs", "Input roles and exact snapshot bytes must be identical")
    first, second = baseline["specification"], sensitivity["specification"]
    allowed = {"transform", "distance", "baseline_run", "purpose"}
    differences = [key for key in first.keys() | second.keys() if first.get(key) != second.get(key)]
    forbidden = sorted(set(differences) - allowed)
    if forbidden:
        raise AnalysisError("comparison_settings", "Only distance and transformation may change scientifically",
                            fields=forbidden)
    if not set(differences) & {"transform", "distance"}:
        raise AnalysisError("comparison_no_change", "The sensitivity run must change a transformation or distance")
    baseline_hash = _sha((Path(baseline["run_dir"]) / "manifest.json").read_bytes())
    declared = second.get("baseline_run")
    if declared is not None and declared != baseline_hash:
        raise AnalysisError("comparison_baseline", "The declared baseline fingerprint does not match this baseline")
    left, right = baseline["result"], sensitivity["result"]
    for key in ("sample_ids", "input_sample_ids", "taxon_ids", "retained_counts", "diversity", "metadata", "excluded"):
        if left[key] != right[key]:
            raise AnalysisError("comparison_confinement", "Results changed outside distance and ordination stages", field=key)
    return baseline, sensitivity


def _report(baseline, sensitivity):
    left, right = baseline["result"], sensitivity["result"]
    first, second = baseline["specification"], sensitivity["specification"]
    d1, d2 = np.asarray(left["distances"]), np.asarray(right["distances"])
    upper = np.triu_indices(left["n"], 1)
    x, y = d1[upper], d2[upper]
    pearson = _correlation(x, y)
    spearman = _correlation(_average_ranks(x), _average_ranks(y))
    gaps = {"baseline": _relative_eigengap(left), "sensitivity": _relative_eigengap(right)}
    identifiable = all(value > EIGENGAP_THRESHOLD for value in gaps.values())
    m2 = _procrustes_m2(left["coordinates"], right["coordinates"]) if identifiable else None
    warnings = []
    if pearson is None or spearman is None:
        warnings.append({"code": "undefined_distance_correlation", "message": "A distance vector is constant or too short"})
    if not identifiable:
        warnings.append({"code": "nonidentifiable_selected_subspace",
                         "message": "The selected-axis boundary is tied or nearly tied; Procrustes m2 is not reported"})
    totals = np.asarray([row["total"] for row in left["diversity"]], dtype=float)
    lower_bound = np.abs(totals[:, None] - totals[None, :]) / (totals[:, None] + totals[None, :])
    delta = np.abs(x - y)
    record = {
        "kind": "community_sensitivity_comparison", "method_version": 1,
        "numeric_environment": {
            "implementation_sha256": baseline["environment"]["implementation_sha256"],
            "python": baseline["environment"]["python"],
            "numpy": baseline["environment"]["packages"]["numpy"],
            "platforms": {"baseline": baseline["environment"]["platform"],
                          "sensitivity": sensitivity["environment"]["platform"]},
            "platform_identical": baseline["environment"]["platform"] == sensitivity["environment"]["platform"],
        },
        "baseline_specification": first, "sensitivity_specification": second,
        "baseline_manifest_sha256": _sha((Path(baseline["run_dir"]) / "manifest.json").read_bytes()),
        "sensitivity_manifest_sha256": _sha((Path(sensitivity["run_dir"]) / "manifest.json").read_bytes()),
        "baseline_link_verified": second.get("baseline_run") is not None,
        "purpose": second.get("purpose"), "sample_ids": left["sample_ids"],
        "settings_changed": [key for key in ("transform", "distance") if first[key] != second[key]],
        "upper_triangle_pairs": len(x), "pearson_distance_correlation": pearson,
        "spearman_distance_correlation": spearman,
        "maximum_absolute_distance_change": float(delta.max()),
        "mean_absolute_distance_change": float(delta.mean()),
        "symmetric_procrustes_m2": m2,
        "procrustes_definition": "1 - sum(svd(X_centered_normalised.T @ Y_centered_normalised))**2",
        "selected_subspace_identifiable": identifiable, "relative_eigengaps": gaps,
        "eigengap_threshold": EIGENGAP_THRESHOLD,
        "negative_inertia_magnitude": {"baseline": left["negative_inertia_magnitude"],
                                       "sensitivity": right["negative_inertia_magnitude"]},
        "raw_count_total_imbalance_bound": lower_bound.tolist(),
        "warnings": warnings,
        "limitations": ["Descriptive comparison only; no p-values or group inference",
                        "The total-imbalance matrix bounds raw-count Bray-Curtis only, not relative-abundance distances",
                        "Correlation does not establish equality of distances or scientific equivalence"],
    }
    return record


def _file_record(path):
    data = path.read_bytes()
    types = {".json": "application/json", ".csv": "text/csv", ".png": "image/png", ".svg": "image/svg+xml"}
    return {"sha256": _sha(data), "bytes": len(data), "media_type": types.get(path.suffix, "text/plain")}


def compare_community_runs(baseline_run, sensitivity_run, output_root):
    baseline, sensitivity = _checked_pair(baseline_run, sensitivity_run)
    report = _report(baseline, sensitivity)
    directory = Path(output_root).resolve() / uuid.uuid4().hex
    try:
        directory.mkdir(parents=True, exist_ok=False)
        for name, record in (("baseline", baseline), ("sensitivity", sensitivity)):
            shutil.copytree(record["run_dir"], directory / name)
        baseline, sensitivity = _checked_pair(directory / "baseline", directory / "sensitivity")
        report = _report(baseline, sensitivity)
        _json(directory / "report.json", report)
        with (directory / "raw_count_total_imbalance_bound.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["sample_id", *report["sample_ids"]])
            for sample, row in zip(report["sample_ids"], report["raw_count_total_imbalance_bound"], strict=True):
                writer.writerow([sample, *row])
        files = {path.relative_to(directory).as_posix(): _file_record(path)
                 for path in sorted(directory.rglob("*")) if path.is_file()}
        _json(directory / "manifest.json", {"kind": "community_comparison", "schema_version": 1,
              "status": "complete", "comparison_id": directory.name, "files": files,
              "baseline": "baseline", "sensitivity": "sensitivity"})
    except Exception as exc:
        if directory.is_dir():
            _json(directory / "failure.json", {"status": "failed", "error_type": type(exc).__name__, "message": str(exc)})
        raise AnalysisError("comparison_write_failed", "Comparison did not complete", comparison_dir=str(directory), reason=str(exc)) from exc
    return {"status": "complete", "comparison_dir": str(directory),
            "summary": {key: report[key] for key in ("settings_changed", "pearson_distance_correlation",
                        "spearman_distance_correlation", "symmetric_procrustes_m2", "warnings")}}


def _equivalent(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equivalent(a[key], b[key]) for key in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equivalent(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, float) and isinstance(b, (int, float)) and not isinstance(b, bool):
        return bool(np.isclose(a, b, rtol=REPORT_TOLERANCE, atol=REPORT_TOLERANCE))
    return type(a) is type(b) and a == b


def inspect_comparison(comparison_dir):
    directory = Path(comparison_dir).resolve()
    try:
        manifest_path = directory / "manifest.json"
        if manifest_path.is_symlink():
            raise ValueError("Manifest must not be a symbolic link")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int:
            raise ValueError("Invalid comparison manifest structure")
        if (manifest.get("kind"), manifest.get("schema_version"), manifest.get("status")) != ("community_comparison", 1, "complete"):
            raise ValueError("Unsupported comparison completion record")
        if manifest.get("baseline") != "baseline" or manifest.get("sensitivity") != "sensitivity":
            raise ValueError("Comparison must name its two local child bundles")
        files = manifest["files"]
        if not isinstance(files, dict):
            raise ValueError("Invalid comparison file map")
        actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file() or path.is_symlink()}
        if actual != set(files) | {"manifest.json"}:
            raise ValueError("Comparison file set differs from manifest")
        for name, expected in files.items():
            relative = PurePosixPath(name)
            if relative.is_absolute() or ".." in relative.parts or "\\" in name or not relative.parts:
                raise ValueError("Unsafe comparison artefact path")
            path = directory / name
            if any((directory / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
                raise ValueError("Symbolic links are not comparison artefacts")
            if not path.is_file() or _file_record(path) != expected:
                raise ValueError(f"Comparison artefact integrity failure: {name}")
        if not {"report.json", "raw_count_total_imbalance_bound.csv", "baseline/manifest.json", "sensitivity/manifest.json"} <= files.keys():
            raise ValueError("Required comparison artefacts are missing")
        baseline, sensitivity = _checked_pair(directory / "baseline", directory / "sensitivity")
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        if not _equivalent(report, _report(baseline, sensitivity)):
            raise ValueError("Comparison report disagrees with the verified child results")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, AnalysisError) as exc:
        raise AnalysisError("invalid_comparison", "Comparison could not be verified", comparison_dir=str(directory), reason=str(exc)) from exc
    return {"status": "verified", "comparison_dir": str(directory), "manifest": manifest, "report": report,
            "scope": "Child bundles, artefact integrity, settings confinement and descriptive report verified; scientific interpretation remains separate"}
