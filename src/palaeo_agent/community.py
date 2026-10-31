"""Explicit count-table diversity, dissimilarities and principal coordinates."""

from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import io
from numbers import Real
from pathlib import Path
from typing import Literal
import unicodedata

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from .core import AnalysisError, ResultItem


MAX_EXACT_COUNT = 2**53 - 1
MAX_MATRIX_BYTES = 256 * 1024**2
EIGENGAP_THRESHOLD = 1e-8
REFERENCES = [
    "https://vegandevs.github.io/vegan/reference/diversity.html",
    "https://vegandevs.github.io/vegan/reference/vegdist.html",
    "https://vegandevs.github.io/vegan/reference/wcmdscale.html",
]


def selected_subspace_info(eigenvalues, k, eigenvalue_tolerance):
    """Describe whether a cutoff retains complete numerically resolved positive blocks."""
    values = np.asarray(eigenvalues, dtype=float)
    if (values.ndim != 1 or not len(values) or not np.isfinite(values).all() or
        np.any(values[:-1] < values[1:]) or not np.isfinite(eigenvalue_tolerance) or eigenvalue_tolerance <= 0):
        raise ValueError("Expected a finite descending spectrum and positive eigenvalue tolerance")
    rank = int(np.sum(values > eigenvalue_tolerance))
    if not isinstance(k, (int, np.integer)) or isinstance(k, (bool, np.bool_)) or not 1 <= k <= rank:
        raise ValueError("Selected dimensions must lie within the positive eigenvalue rank")
    gaps = {cutoff: float((values[cutoff - 1] - values[cutoff]) / values[0])
            for cutoff in range(1, rank)}
    allowed = [cutoff for cutoff in range(1, rank + 1)
               if cutoff == rank or gaps[cutoff] > EIGENGAP_THRESHOLD]
    return {"identifiable": k in allowed, "requested_dimensions": int(k), "positive_rank": rank,
            "relative_cutoff_gap": gaps.get(k), "threshold": EIGENGAP_THRESHOLD,
            "allowed_identifiable_dimensions": allowed,
            "largest_allowed_dimensions_at_or_below_requested": max((cutoff for cutoff in allowed if cutoff <= k), default=0)}


class CommunitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["community"]
    input: Path
    format: Literal["past"]
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    value_type: Literal["count"]
    metadata: Path | None = None
    transform: Literal["none", "relative_abundance"]
    distance: Literal["braycurtis", "jaccard"]
    dimensions: int = Field(ge=1, strict=True)
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]
    baseline_run: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    purpose: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def sensitivity_purpose(self):
        if self.distance == "jaccard" and self.transform != "none":
            raise ValueError("Relative abundance is an unsupported no-op before binary Jaccard; request transform='none'")
        if self.baseline_run is not None and (self.purpose is None or not self.purpose.strip()):
            raise ValueError("A baseline reference requires a stated sensitivity purpose")
        return self


class CommunityDiversity(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    total: FiniteFloat = Field(gt=0)
    richness: int = Field(ge=1)
    shannon: FiniteFloat = Field(ge=0)
    simpson: FiniteFloat = Field(ge=0, le=1)


class CommunityExclusion(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    reason: Literal["empty_sample"]


class CommunityWarning(ResultItem):
    code: Literal["near_duplicate_labels", "negative_eigenvalues"]
    message: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)


class CommunityResult(ResultItem):
    method: Literal["community"]
    method_version: Literal[1]
    value_type: Literal["count"]
    canonical_orientation: Literal["samples_by_taxa"]
    transform: Literal["none", "relative_abundance"]
    distance: Literal["braycurtis", "jaccard"]
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]
    dimensions: int = Field(ge=1)
    n_input: int = Field(ge=2)
    n: int = Field(ge=2)
    n_taxa: int = Field(ge=1)
    input_sample_ids: list[str]
    sample_ids: list[str]
    taxon_ids: list[str]
    retained_counts: list[list[FiniteFloat]]
    transformed_matrix: list[list[FiniteFloat]]
    diversity: list[CommunityDiversity]
    distances: list[list[FiniteFloat]]
    eigenvalues: list[FiniteFloat]
    positive_gram: list[list[FiniteFloat]]
    coordinates: list[list[FiniteFloat]]
    axis_positive_inertia: list[FiniteFloat]
    eigenvalue_tolerance: FiniteFloat = Field(gt=0)
    negative_eigenvalues: list[FiniteFloat]
    negative_inertia_magnitude: FiniteFloat = Field(ge=0)
    negative_to_positive_inertia: FiniteFloat = Field(ge=0)
    metadata: list[dict[str, str]] | None
    excluded: list[CommunityExclusion]
    warnings: list[CommunityWarning]
    references: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_records(self):
        ids = self.sample_ids
        excluded = [item.sample_id for item in self.excluded]
        for label in (self.input_sample_ids, ids, self.taxon_ids):
            if any(not item.strip() for item in label) or len(set(label)) != len(label):
                raise ValueError("Labels must be nonblank and unique")
        if self.n != len(ids) or self.n_input != len(self.input_sample_ids):
            raise ValueError("Sample counts disagree with labels")
        if self.n_taxa != len(self.taxon_ids):
            raise ValueError("Taxon count disagrees with labels")
        if len(set(ids + excluded)) != len(ids + excluded) or set(ids + excluded) != set(self.input_sample_ids):
            raise ValueError("Retained and excluded samples must partition the input")
        if self.empty_samples == "error" and excluded:
            raise ValueError("The error empty-sample policy cannot contain exclusions")
        if self.n_input != self.n + len(excluded) or self.dimensions >= self.n:
            raise ValueError("Invalid retained sample count or dimensions")
        for matrix in (self.retained_counts, self.transformed_matrix):
            if len(matrix) != self.n or any(len(row) != self.n_taxa for row in matrix):
                raise ValueError("Community matrix shape disagrees with labels")
            if any(value < 0 for row in matrix for value in row):
                raise ValueError("Community matrices must be nonnegative")
        if any(value > MAX_EXACT_COUNT or value != int(value) for row in self.retained_counts for value in row):
            raise ValueError("Retained counts must be exactly representable nonnegative integers")
        if len(self.diversity) != self.n or [item.sample_id for item in self.diversity] != ids:
            raise ValueError("Diversity records must align with samples")
        if len(self.distances) != self.n or any(len(row) != self.n for row in self.distances):
            raise ValueError("Distance shape disagrees with samples")
        d = np.asarray(self.distances)
        if np.any(d < 0) or not np.allclose(d, d.T, rtol=0, atol=1e-12) or not np.allclose(np.diag(d), 0, rtol=0, atol=1e-12):
            raise ValueError("Distances must be nonnegative, symmetric, and zero on the diagonal")
        if len(self.eigenvalues) != self.n or any(a < b for a, b in zip(self.eigenvalues, self.eigenvalues[1:])):
            raise ValueError("The complete eigenvalue spectrum must be sorted descending")
        if len(self.positive_gram) != self.n or any(len(row) != self.n for row in self.positive_gram):
            raise ValueError("Full positive-space Gram shape disagrees with samples")
        if len(self.coordinates) != self.n or any(len(row) != self.dimensions for row in self.coordinates):
            raise ValueError("Ordination shape disagrees with samples and dimensions")
        eigenvalues = np.asarray(self.eigenvalues)
        positive = eigenvalues[eigenvalues > self.eigenvalue_tolerance]
        if len(positive) < self.dimensions:
            raise ValueError("Requested dimensions exceed the positive eigenvalue rank")
        if not selected_subspace_info(eigenvalues, self.dimensions, self.eigenvalue_tolerance)["identifiable"]:
            raise ValueError("Requested PCoA cutoff is numerically unresolved within the positive spectrum")
        gram = np.asarray(self.positive_gram)
        coordinates = np.asarray(self.coordinates)
        scale = max(1.0, positive[0])
        if (not np.allclose(gram, gram.T, rtol=1e-8, atol=1e-10 * scale) or
            not np.allclose(gram.mean(axis=0), 0, rtol=0, atol=1e-10 * scale) or
            np.any(np.diag(gram) < -1e-10 * scale)):
            raise ValueError("Full positive-space Gram must be symmetric and centred with nonnegative diagonal")
        if (not np.isclose(np.trace(gram), positive.sum(), rtol=1e-8, atol=1e-10 * scale) or
            not np.isclose(np.sum(gram**2), np.sum(positive**2), rtol=1e-8, atol=1e-10 * scale**2)):
            raise ValueError("Full positive-space Gram spectral summaries disagree with positive eigenvalues")
        selected = eigenvalues[:self.dimensions]
        if (not np.allclose(coordinates.mean(axis=0), 0, rtol=0, atol=1e-10 * np.sqrt(scale)) or
            not np.allclose(coordinates.T @ coordinates, np.diag(selected), rtol=1e-8, atol=1e-10 * scale) or
            not np.allclose(gram @ coordinates, coordinates * selected, rtol=1e-8, atol=1e-10 * scale**1.5)):
            raise ValueError("Coordinates must be centred orthogonal eigenaxes of the full positive-space Gram")
        if len(self.axis_positive_inertia) != self.dimensions or any(not 0 < value <= 1 for value in self.axis_positive_inertia):
            raise ValueError("Invalid positive-inertia fractions")
        if any(value >= -self.eigenvalue_tolerance for value in self.negative_eigenvalues):
            raise ValueError("Negative eigenvalue diagnostics must use the declared threshold")
        if self.metadata is not None and [row.get("sample_id") for row in self.metadata] != ids:
            raise ValueError("Metadata records must align by sample ID")
        return self


def _ids(values, role):
    try:
        labels = list(values)
    except TypeError as exc:
        raise AnalysisError("invalid_id", "IDs must be an iterable of nonblank strings", role=role) from exc
    if any(not isinstance(item, str) or not item.strip() for item in labels):
        raise AnalysisError("invalid_id", "IDs must be nonblank strings", role=role)
    duplicate = sorted(item for item, count in Counter(labels).items() if count > 1)
    if duplicate:
        raise AnalysisError("duplicate_id", "IDs must be unique", role=role, ids=duplicate)
    return labels


def _near_duplicates(labels, role):
    groups = defaultdict(list)
    for label in labels:
        groups[unicodedata.normalize("NFKC", label).strip().casefold()].append(label)
    repeated = [items for items in groups.values() if len(items) > 1]
    if not repeated:
        return []
    return [{"code": "near_duplicate_labels", "message": "Similar labels retained as distinct exact strings",
             "details": {"role": role, "groups": repeated}}]


def _metadata(rows, ids):
    if rows is None:
        return None
    material = list(rows)
    if any(not isinstance(row, dict) or "sample_id" not in row or
           any(not isinstance(k, str) or not isinstance(v, str) for k, v in row.items())
           for row in material):
        raise AnalysisError("invalid_metadata", "Metadata must be string-valued records with a sample_id")
    names = _ids([row["sample_id"] for row in material], "metadata_sample")
    if set(names) != set(ids):
        raise AnalysisError("metadata_alignment", "Metadata and input sample ID sets must match exactly",
                            missing=sorted(set(ids) - set(names)), extra=sorted(set(names) - set(ids)))
    lookup = {row["sample_id"]: row for row in material}
    return [lookup[name] for name in ids]


def _prepare(matrix, *, sample_ids, taxon_ids, dimensions, empty_samples, metadata):
    samples, taxa = _ids(sample_ids, "sample"), _ids(taxon_ids, "taxon")
    if not isinstance(dimensions, int) or isinstance(dimensions, bool) or dimensions < 1:
        raise AnalysisError("invalid_dimensions", "dimensions must be a positive integer")
    if not isinstance(empty_samples, str) or empty_samples not in {"error", "drop"}:
        raise AnalysisError("invalid_option", "Declare empty_samples as error or drop")
    if not taxa:
        raise AnalysisError("empty_taxa", "At least one taxon column is required")
    try:
        values = [list(row) for row in matrix]
    except TypeError as exc:
        raise AnalysisError("invalid_matrix", "Counts must be a rectangular sample-by-taxon matrix") from exc
    if len(values) != len(samples) or any(len(row) != len(taxa) for row in values):
        raise AnalysisError("matrix_alignment", "Matrix dimensions must match sample and taxon IDs")
    if not values:
        raise AnalysisError("insufficient_samples", "The count matrix has no sample rows")
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            try:
                valid = (not isinstance(value, (bool, np.bool_)) and isinstance(value, Real) and
                         np.isfinite(float(value)) and 0 <= value <= MAX_EXACT_COUNT and int(value) == value)
            except (ValueError, OverflowError, TypeError):
                valid = False
            if not valid:
                raise AnalysisError("invalid_count", "Counts must be finite nonnegative exactly representable integers; proportions are unsupported and must not be rescaled or rounded into counts",
                                    sample_id=samples[i], taxon_id=taxa[j])
    counts = np.asarray(values, dtype=np.float64)
    total = counts.sum(axis=1)
    if np.any(total > MAX_EXACT_COUNT):
        raise AnalysisError("count_range", "Sample totals exceed exact float64 integer range")
    aligned = _metadata(metadata, samples)
    empty = total == 0
    excluded = [{"sample_id": name, "reason": "empty_sample"} for name, flag in zip(samples, empty) if flag]
    if excluded and empty_samples == "error":
        raise AnalysisError("empty_samples", "Empty samples require an explicit drop policy", excluded=excluded)
    keep = ~empty
    retained_ids = [name for name, flag in zip(samples, keep) if flag]
    if len(retained_ids) <= dimensions:
        raise AnalysisError("insufficient_samples", "More retained samples than ordination dimensions are required",
                            retained=len(retained_ids), dimensions=dimensions)
    estimated = 6 * len(retained_ids)**2 * 8
    if estimated > MAX_MATRIX_BYTES:
        raise AnalysisError("resource_limit", "Distance/eigen matrices exceed the local allocation budget",
                            estimated_bytes=estimated, limit_bytes=MAX_MATRIX_BYTES)
    return {"counts": counts[keep], "input_sample_ids": samples, "sample_ids": retained_ids,
            "taxon_ids": taxa, "excluded": excluded,
            "metadata": None if aligned is None else [row for row, flag in zip(aligned, keep) if flag],
            "warnings": _near_duplicates(samples, "sample") + _near_duplicates(taxa, "taxon")}


def _read_inputs(spec, data, metadata):
    try:
        rows = [line.split() for line in data.decode("utf-8-sig").splitlines() if line.strip()]
    except UnicodeDecodeError as exc:
        raise AnalysisError("invalid_encoding", "The supported PAST matrix must be UTF-8 text") from exc
    if len(rows) < 2 or not rows[0] or rows[0][0] != ".":
        raise AnalysisError("invalid_past_header", "Expected a classic PAST header beginning with '.'")
    columns = _ids(rows[0][1:], "column")
    labels = _ids([row[0] for row in rows[1:]], "row")
    values = []
    for line, row in enumerate(rows[1:], 2):
        if len(row) != len(columns) + 1:
            raise AnalysisError("row_width", "Row width differs from the header", line=line)
        if "." in row[1:]:
            raise AnalysisError("missing_counts", "Missing counts cannot be converted to absences", line=line)
        try:
            parsed = [Decimal(token) for token in row[1:]]
            if any(not value.is_finite() or value < 0 or value > MAX_EXACT_COUNT or
                   value != value.to_integral_value() for value in parsed):
                raise ValueError("Count token is not a finite nonnegative exact integer")
            values.append([float(value) for value in parsed])
        except (ValueError, InvalidOperation, OverflowError) as exc:
            raise AnalysisError("invalid_count", "Invalid count token; proportions are unsupported and must not be rescaled or rounded into counts", line=line) from exc
    if spec.orientation == "taxa_by_samples":
        values = list(map(list, zip(*values)))
        labels, columns = columns, labels
    meta_rows = None
    if metadata is not None:
        try:
            reader = csv.reader(io.StringIO(metadata.decode("utf-8-sig")))
            material = list(reader)
        except (UnicodeDecodeError, csv.Error) as exc:
            raise AnalysisError("invalid_metadata", "Metadata must be UTF-8 CSV") from exc
        if not material or not material[0] or "sample_id" not in material[0]:
            raise AnalysisError("invalid_metadata", "Metadata CSV requires a sample_id column")
        names = _ids(material[0], "metadata_column")
        if any(len(row) != len(names) for row in material[1:]):
            raise AnalysisError("invalid_metadata", "Metadata row width differs from its header")
        meta_rows = [dict(zip(names, row)) for row in material[1:]]
    if (spec.metadata is None) != (metadata is None):
        raise AnalysisError("metadata_input", "Metadata bytes must match the declared metadata input")
    return values, labels, columns, meta_rows


def validate_community(spec, data, metadata=None):
    spec = spec if isinstance(spec, CommunitySpec) else CommunitySpec.model_validate(spec)
    matrix, samples, taxa, meta = _read_inputs(spec, data, metadata)
    prepared = _prepare(matrix, sample_ids=samples, taxon_ids=taxa, dimensions=spec.dimensions,
                        empty_samples=spec.empty_samples, metadata=meta)
    return {"status": "valid", "n_input": len(samples), "n": len(prepared["sample_ids"]),
            "n_taxa": len(taxa), "excluded": prepared["excluded"], "warnings": prepared["warnings"],
            "scope": "Input structure and count semantics checked; no distance matrix or eigendecomposition computed"}


def community_distances(counts, *, transform, distance):
    """Construct declared dissimilarities without any ordination cutoff."""
    if transform not in {"none", "relative_abundance"} or distance not in {"braycurtis", "jaccard"}:
        raise AnalysisError("invalid_option", "Declare supported transformation and distance explicitly")
    if distance == "jaccard" and transform != "none":
        raise AnalysisError("unsupported_combination", "Relative abundance is an unsupported no-op before binary Jaccard; request transform='none'")
    transformed = counts if transform == "none" else counts / counts.sum(axis=1)[:, None]
    n = len(counts)
    distances = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i):
            if distance == "braycurtis":
                value = np.abs(transformed[i] - transformed[j]).sum() / (transformed[i] + transformed[j]).sum()
            else:
                a, b = transformed[i] > 0, transformed[j] > 0
                value = 1 - np.count_nonzero(a & b) / np.count_nonzero(a | b)
            distances[i, j] = distances[j, i] = value
    return transformed, distances


def analyse_community(matrix, *, sample_ids, taxon_ids, transform, distance, dimensions,
                      empty_samples, metadata=None):
    """Analyse declared counts in canonical sample-by-taxon orientation."""
    if (not isinstance(transform, str) or not isinstance(distance, str) or
        transform not in {"none", "relative_abundance"} or distance not in {"braycurtis", "jaccard"}):
        raise AnalysisError("invalid_option", "Declare supported transformation and distance explicitly")
    if distance == "jaccard" and transform != "none":
        raise AnalysisError("unsupported_combination", "Relative abundance is an unsupported no-op before binary Jaccard; request transform='none'")
    data = _prepare(matrix, sample_ids=sample_ids, taxon_ids=taxon_ids, dimensions=dimensions,
                    empty_samples=empty_samples, metadata=metadata)
    counts = data["counts"]
    totals = counts.sum(axis=1)
    relative = counts / totals[:, None]
    diversity = []
    for name, row, proportions, total in zip(data["sample_ids"], counts, relative, totals):
        positive = proportions[proportions > 0]
        diversity.append({"sample_id": name, "total": float(total), "richness": int(np.count_nonzero(row)),
                          "shannon": float(-np.sum(positive * np.log(positive))),
                          "simpson": float(1 - np.sum(proportions**2))})
    transformed, distances = community_distances(counts, transform=transform, distance=distance)
    n = len(counts)
    squared = distances**2
    centred = -0.5 * (squared - squared.mean(axis=0)[None, :] - squared.mean(axis=1)[:, None] + squared.mean())
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(centred)
    except np.linalg.LinAlgError as exc:
        raise AnalysisError("ordination_failed", "Symmetric eigendecomposition did not converge") from exc
    eigenvalues, eigenvectors = eigenvalues[::-1], eigenvectors[:, ::-1]
    tolerance = float(np.finfo(np.float64).eps * n * max(1.0, np.abs(eigenvalues).max()))
    positive = eigenvalues > tolerance
    if int(positive.sum()) < dimensions:
        raise AnalysisError("insufficient_positive_axes", "Requested dimensions exceed positive PCoA rank",
                            requested=dimensions, available=int(positive.sum()), eigenvalue_tolerance=tolerance)
    subspace = selected_subspace_info(eigenvalues, dimensions, tolerance)
    if not subspace["identifiable"]:
        raise AnalysisError("nonidentifiable_axes", "Requested PCoA cutoff is numerically unresolved between retained and excluded positive axes",
                            eigenvalues=eigenvalues.tolist(), **subspace)
    coordinates = eigenvectors[:, :dimensions] * np.sqrt(eigenvalues[:dimensions])
    positive_coordinates = eigenvectors[:, positive] * np.sqrt(eigenvalues[positive])
    positive_gram = positive_coordinates @ positive_coordinates.T
    negative = eigenvalues[eigenvalues < -tolerance]
    negative_magnitude = float(-negative.sum())
    positive_total = float(eigenvalues[positive].sum())
    warnings = data["warnings"]
    if len(negative):
        warnings.append({"code": "negative_eigenvalues", "message": "Dissimilarities have material negative PCoA eigenvalues; no correction applied",
                         "details": {"count": len(negative), "threshold": tolerance,
                                     "negative_inertia_magnitude": negative_magnitude}})
    result = {"method": "community", "method_version": 1, "value_type": "count",
              "canonical_orientation": "samples_by_taxa", "transform": transform, "distance": distance,
              "missing": "error", "empty_samples": empty_samples, "dimensions": dimensions,
              "n_input": len(data["input_sample_ids"]), "n": n, "n_taxa": counts.shape[1],
              "input_sample_ids": data["input_sample_ids"], "sample_ids": data["sample_ids"],
              "taxon_ids": data["taxon_ids"], "retained_counts": counts.tolist(),
              "transformed_matrix": transformed.tolist(), "diversity": diversity,
              "distances": distances.tolist(), "eigenvalues": eigenvalues.tolist(),
              "positive_gram": positive_gram.tolist(),
              "coordinates": coordinates.tolist(), "axis_positive_inertia": (eigenvalues[:dimensions] / positive_total).tolist(),
              "eigenvalue_tolerance": tolerance, "negative_eigenvalues": negative.tolist(),
              "negative_inertia_magnitude": negative_magnitude,
              "negative_to_positive_inertia": negative_magnitude / positive_total,
              "metadata": data["metadata"], "excluded": data["excluded"], "warnings": warnings,
              "references": REFERENCES,
              "limitations": ["Descriptive community analysis only; no group inference",
                              "Count declaration and sampling meaning require scientific judgment",
                              "Diversity is observed and unstandardised; unequal totals can confound comparisons through sampling effort",
                              "PCoA coordinates retain positive axes only; negative eigenvalues are reported, not corrected",
                              "Axis proportions refer to positive inertia, not total variance",
                              "Eigenaxis signs and orientations within tied eigenspaces are arbitrary"]}
    return CommunityResult.model_validate(result).model_dump(mode="json")


def calculate_community(spec, data, metadata=None):
    spec = spec if isinstance(spec, CommunitySpec) else CommunitySpec.model_validate(spec)
    matrix, samples, taxa, meta = _read_inputs(spec, data, metadata)
    return analyse_community(matrix, sample_ids=samples, taxon_ids=taxa, transform=spec.transform,
                             distance=spec.distance, dimensions=spec.dimensions,
                             empty_samples=spec.empty_samples, metadata=meta)


def plot_community(path, result, spec):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    coordinates = np.asarray(result["coordinates"])
    x = coordinates[:, 0]
    y = coordinates[:, 1] if coordinates.shape[1] > 1 else np.zeros(len(x))
    fractions = result["axis_positive_inertia"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    axes[0].scatter(x, y)
    axes[0].set(xlabel=f"PCoA 1 ({fractions[0]:.1%} of positive inertia)",
                ylabel=f"PCoA 2 ({fractions[1]:.1%} of positive inertia)" if len(fractions) > 1 else "Zero display axis (one-dimensional fit)",
                title=f"{spec.distance}; {spec.transform}")
    bars = axes[1].bar(result["sample_ids"], [row["shannon"] for row in result["diversity"]])
    axes[1].bar_label(bars, labels=[f"N={row['total']:g}" for row in result["diversity"]], fontsize=8, padding=3)
    axes[1].margins(y=0.15)
    axes[1].set(xlabel="Sample ID", ylabel="Shannon entropy (natural log)", title="Observed, unstandardised diversity")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    occupied = []
    offsets = [(5, 7), (5, -12), (-12, 7), (-12, -12),
               (18, 18), (18, -22), (-24, 18), (-24, -22)]
    for sample, xv, yv in zip(result["sample_ids"], x, y):
        for offset in offsets:
            label = axes[0].annotate(sample, (xv, yv), xytext=offset,
                                     textcoords="offset points", fontsize=9,
                                     arrowprops={"arrowstyle": "-", "linewidth": 0.4})
            bounds = label.get_window_extent(renderer).expanded(1.05, 1.05)
            if not any(bounds.overlaps(previous) for previous in occupied):
                break
            label.remove()
        else:
            label = axes[0].annotate(sample, (xv, yv), xytext=offsets[-1],
                                     textcoords="offset points", fontsize=9)
            bounds = label.get_window_extent(renderer)
        occupied.append(bounds)
    fig.savefig(path, format="svg", metadata={"Date": None})
    fig.savefig(Path(path).with_suffix(".png"), format="png", dpi=150)
    plt.close(fig)
