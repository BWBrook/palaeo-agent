"""Declared one-way PERMANOVA with free permutations and centroid dispersion."""

from itertools import combinations
import math
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from .community import (FORMAT_HELP, MAX_EXACT_COUNT, VALUE_TYPE_HELP, value_keys, without_absent_branch, _near_duplicates, _prepare, _read_inputs, check_delimiter,
                        community_distances)
from .core import AnalysisError, ResultItem
from .count_homogeneity import _interval


MAX_SCHEDULE_ENTRIES = 2_000_000
MAX_EXACT_ALLOCATIONS = 10_000
TIE_TOLERANCE = float(np.sqrt(np.finfo(np.float64).eps))
REFERENCES = [
    "https://vegandevs.github.io/vegan/reference/adonis.html",
    "https://vegandevs.github.io/vegan/reference/betadisper.html",
]


class PermanovaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["permanova"]
    input: Path
    metadata: Path
    group_column: str = Field(min_length=1, pattern=r"\S")
    format: Literal["past", "delimited"] = Field(description=FORMAT_HELP)
    delimiter: Literal["tab", "comma"] | None = Field(default=None, description="Required for format 'delimited'")
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    value_type: Literal["count", "abundance"] = Field(description=VALUE_TYPE_HELP)
    distance: Literal["braycurtis", "jaccard"]
    transform: Literal["none", "relative_abundance"]
    missing: Literal["error"]
    empty_samples: Literal["error"]
    design: Literal["independent"]
    permutation_scheme: Literal["free"]
    permutations: int = Field(default=999, ge=1, le=9999, strict=True)
    seed: int = Field(ge=0, le=2**64 - 1, strict=True)

    @model_validator(mode="after")
    def supported_distance_transform(self):
        check_delimiter(self)
        if self.distance == "jaccard" and self.transform != "none":
            raise ValueError("Relative abundance is an unsupported no-op before binary Jaccard; request transform='none'")
        return self


class PermanovaWarning(ResultItem):
    code: Literal["near_duplicate_labels", "negative_eigenvalues", "negative_squared_dispersion", "unequal_group_sizes", "identical_samples", "repeated_block"]
    message: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)


class PermutationRecord(ResultItem):
    mode: Literal["exact", "monte_carlo"]
    requested: int = Field(ge=1, le=9999)
    draws: int = Field(ge=1, le=10000)
    space_size: int = Field(ge=2)
    count_extreme: int = Field(ge=0)
    denominator: int = Field(ge=1)
    seed: int = Field(ge=0, le=2**64 - 1)
    bit_generator: Literal["PCG64"]
    numpy_version: str = Field(min_length=1)
    indices: list[list[int]]
    statistics: list[FiniteFloat | None]
    statuses: list[Literal["finite", "positive_infinity"]]
    infinite_count: int = Field(ge=0)
    tie_tolerance: FiniteFloat = Field(gt=0)
    index_semantics: Literal["distance_matrix_reordering_fixed_groups"]
    tail_probability_interval: list[FiniteFloat] | None = Field(min_length=2, max_length=2)
    interval_status: Literal["clopper_pearson_draw_exceedances", "not_applicable_exact_enumeration"]
    confidence: Literal[0.95]
    reporting_alpha: Literal[0.05]
    monte_carlo_unresolved: bool | None


class DispersionRecord(ResultItem):
    distances: list[FiniteFloat]
    squared_distances: list[FiniteFloat]
    group_mean_distances: dict[str, FiniteFloat]
    negative_squared_count: int = Field(ge=0)
    truncated_sample_ids: list[str]
    threshold: FiniteFloat = Field(gt=0)
    eigenvalues: list[FiniteFloat]
    discarded_eigenvalues: list[FiniteFloat]
    retained_positive_axes: int = Field(ge=0)
    retained_negative_axes: int = Field(ge=0)
    type: Literal["centroid"]
    bias_adjust: Literal[False]
    sqrt_dist: Literal[False]
    add: Literal[False]


class PermanovaResult(ResultItem):
    method: Literal["permanova"]
    method_version: Literal[2]
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    canonical_orientation: Literal["samples_by_taxa"]
    value_type: Literal["count", "abundance"]
    transform: Literal["none", "relative_abundance"]
    distance: Literal["braycurtis", "jaccard"]
    missing: Literal["error"]
    empty_samples: Literal["error"]
    design: Literal["independent"]
    permutation_scheme: Literal["free"]
    group_column: str = Field(min_length=1, pattern=r"\S")
    pseudo_f: FiniteFloat
    r_squared: FiniteFloat
    p_value: FiniteFloat = Field(ge=0, le=1)
    ss_total: FiniteFloat = Field(gt=0)
    ss_within: FiniteFloat = Field(gt=0)
    ss_between: FiniteFloat
    df_between: int = Field(ge=1)
    df_within: int = Field(ge=1)
    n: int = Field(ge=4)
    n_input: int = Field(ge=4)
    n_taxa: int = Field(ge=1)
    input_sample_ids: list[str]
    sample_ids: list[str]
    taxon_ids: list[str]
    retained_counts: list[list[FiniteFloat]] | None = Field(default=None, description="Count input only")
    retained_values: list[list[FiniteFloat]] | None = Field(default=None, description="Abundance input only")
    transformed_matrix: list[list[FiniteFloat]]
    distances: list[list[FiniteFloat]]
    metadata: list[dict[str, str]]
    groups: list[str]
    group_labels: list[str]
    group_sizes: dict[str, int]
    excluded: list[dict]
    permutation: PermutationRecord
    dispersion: DispersionRecord
    warnings: list[PermanovaWarning]
    references: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_records(self):
        try:
            _validate_saved_result(self)
        except AnalysisError as exc:
            raise ValueError(f"{exc.code}: {exc}") from exc
        return self


def _monte_carlo_fields(mode, extreme, requested):
    if mode == "exact":
        return {"tail_probability_interval": None, "interval_status": "not_applicable_exact_enumeration",
                "confidence": 0.95, "reporting_alpha": 0.05, "monte_carlo_unresolved": None}
    interval = list(_interval(extreme, requested))
    return {"tail_probability_interval": interval, "interval_status": "clopper_pearson_draw_exceedances",
            "confidence": 0.95, "reporting_alpha": 0.05, "monte_carlo_unresolved": interval[0] <= 0.05 <= interval[1]}


def _grouping(metadata, group_column, sample_ids):
    if metadata is None or [row.get("sample_id") for row in metadata] != sample_ids:
        raise AnalysisError("metadata_alignment", "PERMANOVA requires metadata joined by exact sample ID")
    absent = [row["sample_id"] for row in metadata if group_column not in row]
    if absent:
        raise AnalysisError("missing_group_column", "Grouping column is missing", group_column=group_column, sample_ids=absent)
    groups = [row[group_column] for row in metadata]
    empty = [sample for sample, group in zip(sample_ids, groups, strict=True) if not group.strip()]
    if empty:
        raise AnalysisError("missing_group_label", "Every sample needs a nonblank grouping label", sample_ids=empty)
    labels = list(dict.fromkeys(groups))
    sizes = {label: groups.count(label) for label in labels}
    if len(labels) < 2:
        raise AnalysisError("insufficient_groups", "At least two groups are required")
    small = {label: size for label, size in sizes.items() if size < 2}
    if small:
        raise AnalysisError("small_groups", "Each group requires at least two samples", group_sizes=small)
    return groups, labels, sizes


def _space_size(sizes):
    remaining = sum(sizes)
    size = 1
    for count in sizes:
        size *= math.comb(remaining, count)
        remaining -= count
        if size.bit_length() > 12000:
            raise AnalysisError("resource_limit", "Permutation-space integer exceeds portable JSON size", limit_bits=12000)
    return size


def _schedule(groups, labels, requested, seed):
    n = len(groups)
    sizes = [groups.count(label) for label in labels]
    space = _space_size(sizes)
    if space < 2:
        raise AnalysisError("no_alternative_allocation", "No alternative group allocation exists")
    mode = "exact" if space - 1 <= requested and space <= MAX_EXACT_ALLOCATIONS else "monte_carlo"
    draws = space if mode == "exact" else requested
    if draws * n > MAX_SCHEDULE_ENTRIES:
        raise AnalysisError("resource_limit", "Permutation schedule exceeds the saved-index allocation budget",
                            entries=draws * n, limit_entries=MAX_SCHEDULE_ENTRIES)
    fixed_positions = [np.flatnonzero(np.asarray(groups) == label).tolist() for label in labels]
    if mode == "monte_carlo":
        rng = np.random.Generator(np.random.PCG64(seed))
        return mode, space, [rng.permutation(n).tolist() for _ in range(draws)]
    output = []

    def allocate(group, remaining, selections):
        if group == len(sizes) - 1:
            assigned = selections + [remaining]
            indices = [0] * n
            for positions, chosen in zip(fixed_positions, assigned, strict=True):
                for target, original in zip(positions, chosen, strict=True):
                    indices[target] = original
            output.append(indices)
            return
        for selected in combinations(remaining, sizes[group]):
            selected_set = set(selected)
            allocate(group + 1, [index for index in remaining if index not in selected_set], selections + [list(selected)])

    allocate(0, list(range(n)), [])
    return mode, space, output


def _sums_of_squares(squared, group_positions, indices=None):
    n = len(squared)
    total = math.fsum(float(squared[i, j]) for i, j in combinations(range(n), 2)) / n
    schedule = None if indices is None else np.asarray(indices)
    group_parts = []
    for positions in group_positions:
        selected = positions if schedule is None else schedule[positions]
        group_parts.append(math.fsum(float(squared[i, j]) for i, j in combinations(selected, 2)) / len(positions))
    within = math.fsum(group_parts)
    return total, within, total - within


def _statistics(total, within, between, n, number_groups, *, observed):
    tolerance = 64 * np.finfo(np.float64).eps * total
    if total == 0:
        raise AnalysisError("zero_total_variation", "PERMANOVA requires nonzero total distance variation")
    if within <= tolerance:
        if not observed and between > 0:
            return None, "positive_infinity"
        raise AnalysisError("undefined_observed_statistic" if observed else "undefined_permutation_statistic",
                            "Residual variation does not support a finite pseudo-F", ss_total=total,
                            ss_within=within, residual_tolerance=tolerance)
    statistic = (between / (number_groups - 1)) / (within / (n - number_groups))
    if not math.isfinite(statistic):
        raise AnalysisError("undefined_observed_statistic" if observed else "undefined_permutation_statistic",
                            "PERMANOVA statistic is not finite")
    return float(statistic), "finite"


def _permutation_statistics(squared, groups, labels, indices, observed_f):
    positions = [np.flatnonzero(np.asarray(groups) == label) for label in labels]
    statistics, statuses, extreme = [], [], 0
    for index in indices:
        total, within, between = _sums_of_squares(squared, positions, index)
        value, status = _statistics(total, within, between, len(groups), len(labels), observed=False)
        statistics.append(value)
        statuses.append(status)
        if status == "positive_infinity" or value >= observed_f - TIE_TOLERANCE:
            extreme += 1
    return statistics, statuses, extreme


def _dispersion(distances, groups, labels, sample_ids):
    squared = distances**2
    centred = -0.5 * (squared - squared.mean(axis=0)[None, :] - squared.mean(axis=1)[:, None] + squared.mean())
    try:
        eigenvalues, vectors = np.linalg.eigh(centred)
    except np.linalg.LinAlgError as exc:
        raise AnalysisError("dispersion_failed", "Dispersion eigendecomposition did not converge") from exc
    eigenvalues, vectors = eigenvalues[::-1], vectors[:, ::-1]
    threshold = float(max(TIE_TOLERANCE, TIE_TOLERANCE * eigenvalues[0]))
    keep = np.abs(eigenvalues) > threshold
    coordinates = vectors[:, keep] * np.sqrt(np.abs(eigenvalues[keep]))
    signs = np.sign(eigenvalues[keep])
    signed = np.zeros(len(groups), dtype=np.float64)
    group_array = np.asarray(groups)
    for label in labels:
        selected = group_array == label
        residuals = coordinates[selected] - coordinates[selected].mean(axis=0)
        signed[selected] = np.sum(residuals**2 * signs, axis=1)
    truncated = signed < 0
    values = np.sqrt(np.maximum(signed, 0))
    return {"distances": values.tolist(), "squared_distances": signed.tolist(),
            "group_mean_distances": {label: float(values[group_array == label].mean()) for label in labels},
            "negative_squared_count": int(truncated.sum()),
            "truncated_sample_ids": [sample for sample, flag in zip(sample_ids, truncated, strict=True) if flag],
            "threshold": threshold, "eigenvalues": eigenvalues.tolist(),
            "discarded_eigenvalues": eigenvalues[~keep].tolist(),
            "retained_positive_axes": int(np.sum(eigenvalues > threshold)),
            "retained_negative_axes": int(np.sum(eigenvalues < -threshold)),
            "type": "centroid", "bias_adjust": False, "sqrt_dist": False, "add": False}


def validate_permanova(spec, data, metadata):
    spec = spec if isinstance(spec, PermanovaSpec) else PermanovaSpec.model_validate(spec)
    matrix, samples, taxa, rows = _read_inputs(spec, data, metadata)
    prepared = _prepare(matrix, sample_ids=samples, taxon_ids=taxa, dimensions=1,
                        empty_samples="error", metadata=rows, value_type=spec.value_type)
    groups, labels, sizes = _grouping(prepared["metadata"], spec.group_column, prepared["sample_ids"])
    space = _space_size(list(sizes.values()))
    mode = "exact" if space - 1 <= spec.permutations and space <= MAX_EXACT_ALLOCATIONS else "monte_carlo"
    draws = space if mode == "exact" else spec.permutations
    if draws * len(groups) > MAX_SCHEDULE_ENTRIES:
        raise AnalysisError("resource_limit", "Permutation schedule exceeds the saved-index allocation budget",
                            entries=draws * len(groups), limit_entries=MAX_SCHEDULE_ENTRIES)
    return {"status": "valid", "n": len(samples), "n_input": len(samples), "n_taxa": len(taxa),
            "groups": labels, "group_sizes": sizes, "warnings": prepared["warnings"],
            "scope": f"Input/{spec.value_type}/group requirements checked; independence and null exchangeability are declared assumptions, not verified"}


def calculate_permanova(spec, data, metadata):
    spec = spec if isinstance(spec, PermanovaSpec) else PermanovaSpec.model_validate(spec)
    matrix, samples, taxa, rows = _read_inputs(spec, data, metadata)
    prepared = _prepare(matrix, sample_ids=samples, taxon_ids=taxa, dimensions=1,
                        empty_samples="error", metadata=rows, value_type=spec.value_type)
    groups, labels, sizes = _grouping(prepared["metadata"], spec.group_column, prepared["sample_ids"])
    mode, space, indices = _schedule(groups, labels, spec.permutations, spec.seed)
    counts = prepared["counts"]
    transformed, distances = community_distances(counts, transform=spec.transform, distance=spec.distance)
    squared = distances**2
    positions = [np.flatnonzero(np.asarray(groups) == label) for label in labels]
    total, within, between = _sums_of_squares(squared, positions)
    statistic, _ = _statistics(total, within, between, len(groups), len(labels), observed=True)
    statistics, statuses, extreme = _permutation_statistics(squared, groups, labels, indices, statistic)
    denominator = space if mode == "exact" else spec.permutations + 1
    p_value = extreme / denominator if mode == "exact" else (extreme + 1) / denominator
    permutation = {"mode": mode, "requested": spec.permutations, "draws": len(indices), "space_size": space,
                   "count_extreme": extreme, "denominator": denominator, "seed": spec.seed,
                   "bit_generator": "PCG64", "numpy_version": np.__version__, "indices": indices,
                   "statistics": statistics, "statuses": statuses, "infinite_count": statuses.count("positive_infinity"),
                   "tie_tolerance": TIE_TOLERANCE, "index_semantics": "distance_matrix_reordering_fixed_groups",
                   **_monte_carlo_fields(mode, extreme, spec.permutations)}
    dispersion = _dispersion(distances, groups, labels, samples)
    warnings = prepared["warnings"] + _near_duplicates(labels, "group")
    if len(set(sizes.values())) > 1:
        warnings.append({"code": "unequal_group_sizes", "message": "Unequal group sizes can complicate location-dispersion interpretation",
                         "details": {"group_sizes": sizes}})
    if dispersion["retained_negative_axes"]:
        warnings.append({"code": "negative_eigenvalues", "message": "Centroid dispersion retains signed negative-eigenvalue coordinates; no correction applied",
                         "details": {"threshold": dispersion["threshold"]}})
    if dispersion["negative_squared_count"]:
        warnings.append({"code": "negative_squared_dispersion", "message": "Negative signed squared centroid distances were truncated to zero for square roots",
                         "details": {"sample_ids": dispersion["truncated_sample_ids"]}})
    result = {"method": "permanova", "method_version": 2, "orientation": spec.orientation,
              "canonical_orientation": "samples_by_taxa", "value_type": spec.value_type, "transform": spec.transform,
              "distance": spec.distance, "missing": "error", "empty_samples": "error", "design": "independent",
              "permutation_scheme": "free", "group_column": spec.group_column,
              "pseudo_f": statistic, "r_squared": between / total, "p_value": p_value,
              "ss_total": total, "ss_within": within, "ss_between": between,
              "df_between": len(labels) - 1, "df_within": len(groups) - len(labels),
              "n": len(samples), "n_input": len(samples), "n_taxa": len(taxa),
              "input_sample_ids": samples, "sample_ids": samples, "taxon_ids": taxa,
              value_keys(spec.value_type)[0]: counts.tolist(), "transformed_matrix": transformed.tolist(),
              "distances": distances.tolist(), "metadata": prepared["metadata"], "groups": groups,
              "group_labels": labels, "group_sizes": sizes, "excluded": [], "permutation": permutation,
              "dispersion": dispersion, "warnings": warnings, "references": REFERENCES,
              "limitations": ["Independence and exchangeability under the null are declared assumptions, not verified properties",
                              "One categorical factor with free permutations only; no blocks, repeated measures or covariates",
                              "Distance-based group association can reflect location and dispersion, particularly with unequal group sizes",
                              "Centroid dispersion is descriptive, unadjusted for small-sample bias and has no p-value",
                              "Tiny eigenmodes below the recorded dispersion threshold are discarded; zero diagnostic distances do not prove zero variation",
                              "Negative signed between-group sums of squares, pseudo-F and R-squared are retained for semimetric distances",
                              "The Monte Carlo interval is a 95% Clopper-Pearson interval for the conditional randomisation tail probability from the draw exceedances; it is not an interval for the plus-one p-value or for ecological uncertainty, and monte_carlo_unresolved flags only that Monte Carlo error alone could move the result across the recorded alpha. Exact enumeration has no Monte Carlo error"]}
    return without_absent_branch(PermanovaResult.model_validate(result).model_dump(mode="json"))


def _same_numeric(actual, expected, *, scale=1.0):
    return np.allclose(actual, expected, rtol=1e-10, atol=1e-12 * scale)


def _validate_saved_result(result):
    samples, taxa = result.sample_ids, result.taxon_ids
    for ids in (samples, taxa, result.input_sample_ids):
        if any(not value.strip() for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("IDs must be nonblank and unique")
    if result.n != len(samples) or result.n_input != result.n or result.input_sample_ids != samples or result.excluded:
        raise ValueError("PERMANOVA retains every input sample; counts and IDs must agree")
    if result.n_taxa != len(taxa):
        raise ValueError("Taxon count must agree with IDs")
    matrix_key = value_keys(result.value_type)[0]
    other_key = value_keys("abundance" if result.value_type == "count" else "count")[0]
    if getattr(result, matrix_key) is None or getattr(result, other_key) is not None:
        raise ValueError(f"{result.value_type} results carry {matrix_key} only")
    for matrix in (getattr(result, matrix_key), result.transformed_matrix):
        if len(matrix) != result.n or any(len(row) != result.n_taxa for row in matrix):
            raise ValueError("Matrix shape disagrees with IDs")
    counts = np.asarray(getattr(result, matrix_key))
    if np.any(counts < 0) or not np.all(np.isfinite(counts.sum(axis=1))) or np.any(counts.sum(axis=1) == 0):
        raise ValueError("Retained values must be nonnegative with finite positive row sums")
    if result.value_type == "count" and (np.any(counts > MAX_EXACT_COUNT) or np.any(counts != np.floor(counts)) or
                                         np.any(counts.sum(axis=1) > MAX_EXACT_COUNT)):
        raise ValueError("Retained counts must be exactly representable count samples")
    groups, labels, sizes = _grouping(result.metadata, result.group_column, samples)
    if result.groups != groups or result.group_labels != labels or result.group_sizes != sizes:
        raise ValueError("Grouping records must match exactly aligned metadata")
    if result.df_between != len(labels) - 1 or result.df_within != result.n - len(labels):
        raise ValueError("Degrees of freedom must match sample and group counts")
    transformed, expected_distances = community_distances(counts, transform=result.transform, distance=result.distance)
    if (result.transform == "none" and not np.array_equal(result.transformed_matrix, counts)) or not _same_numeric(result.transformed_matrix, transformed):
        raise ValueError("Transformed matrix disagrees with declared count transformation")
    if len(result.distances) != result.n or any(len(row) != result.n for row in result.distances):
        raise ValueError("Distance matrix shape disagrees with samples")
    distances = np.asarray(result.distances)
    if np.any(distances < 0) or not np.array_equal(distances, distances.T) or np.any(np.diag(distances) != 0):
        raise ValueError("Distances must be nonnegative, symmetric and zero on the diagonal")
    if not _same_numeric(distances, expected_distances, scale=float(np.max(expected_distances))):
        raise ValueError("Distance matrix disagrees with the declared dissimilarity")
    positions = [np.flatnonzero(np.asarray(groups) == label) for label in labels]
    total, within, between = _sums_of_squares(distances**2, positions)
    statistic, _ = _statistics(total, within, between, result.n, len(labels), observed=True)
    if not _same_numeric([result.ss_total, result.ss_within, result.ss_between], [total, within, between], scale=total):
        raise ValueError("Sums of squares disagree with the distance matrix")
    if not _same_numeric([result.pseudo_f, result.r_squared], [statistic, between / total]):
        raise ValueError("Pseudo-F or R-squared disagrees with sums of squares")
    record = result.permutation
    mode, space, indices = _schedule(groups, labels, record.requested, record.seed)
    if record.mode != mode or record.space_size != space or record.draws != len(indices) or record.indices != indices:
        raise ValueError("Permutation mode, space, draw count or recorded index schedule is inconsistent")
    statistics, statuses, extreme = _permutation_statistics(distances**2, groups, labels, indices, statistic)
    if record.statuses != statuses or len(record.statistics) != len(statistics):
        raise ValueError("Permutation statistic statuses or counts disagree with the schedule")
    for actual, expected in zip(record.statistics, statistics, strict=True):
        if (actual is None) != (expected is None) or (expected is not None and not _same_numeric(actual, expected)):
            raise ValueError("Permutation statistics disagree with the recorded schedule")
    recorded_extreme = sum(status == "positive_infinity" or value >= result.pseudo_f - record.tie_tolerance
                           for value, status in zip(record.statistics, record.statuses, strict=True))
    if recorded_extreme != record.count_extreme:
        raise ValueError("Saved statistics and observed pseudo-F imply different permutation exceedances")
    denominator = space if mode == "exact" else record.requested + 1
    expected_p = extreme / denominator if mode == "exact" else (extreme + 1) / denominator
    if (record.count_extreme != extreme or record.denominator != denominator or
        record.infinite_count != statuses.count("positive_infinity") or record.tie_tolerance != TIE_TOLERANCE or
        result.p_value != expected_p):
        raise ValueError("Permutation exceedances, denominator, tie rule or p-value are inconsistent")
    expected_fields = _monte_carlo_fields(mode, extreme, record.requested)
    if any(getattr(record, key) != value for key, value in expected_fields.items()):
        raise ValueError("Monte Carlo interval, status or unresolved flag disagrees with the exceedances")
    expected_dispersion = _dispersion(distances, groups, labels, samples)
    dispersion = result.dispersion.model_dump(mode="json")
    for key in ("distances", "squared_distances", "eigenvalues", "discarded_eigenvalues", "threshold"):
        if np.shape(dispersion[key]) != np.shape(expected_dispersion[key]) or not _same_numeric(dispersion[key], expected_dispersion[key]):
            raise ValueError("Centroid dispersion values disagree with the full eigensystem")
    for key in ("negative_squared_count", "truncated_sample_ids", "retained_positive_axes", "retained_negative_axes"):
        if dispersion[key] != expected_dispersion[key]:
            raise ValueError("Centroid dispersion truncation or axis counts disagree with the eigensystem")
    if set(dispersion["group_mean_distances"]) != set(labels) or any(not _same_numeric(dispersion["group_mean_distances"][label], expected_dispersion["group_mean_distances"][label]) for label in labels):
        raise ValueError("Group centroid-distance summaries disagree with sample distances")
