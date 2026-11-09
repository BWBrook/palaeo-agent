"""Explicit count- or abundance-table diversity, dissimilarities and principal coordinates."""

from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import io
import math
from numbers import Real
from pathlib import Path
from typing import Literal
import unicodedata

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from .core import AnalysisError, ResultItem, repeated_warnings


MAX_EXACT_COUNT = 2**53 - 1
MAX_ABUNDANCE_ROW_SUM = float(np.finfo(np.float64).max) / 4
VALUE_TYPE_HELP = ("'count': exact nonnegative integer specimen counts. 'abundance': finite nonnegative fractional "
                   "weights such as percentages or proportions; never converted to counts, so count-only methods refuse them.")
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


FORMAT_HELP = ("'past': classic PAST table, first header cell '.', tab-separated (whitespace if the file has no tabs). "
               "'delimited': tab- or comma-separated with a declared delimiter; the first header cell names the ID "
               "column. Empty and NA cells are missing counts.")


def check_delimiter(spec):
    if (spec.format == "delimited") != (spec.delimiter is not None):
        raise ValueError("Declare a delimiter exactly when format is 'delimited'")


def parse_table(text, format, delimiter=None, *, id_column=None, columns=None):
    """Header and rows of a count or measurement table. Nothing is inferred from file names or repaired.

    For delimited tables, id_column and columns project the table by exact header names before any value is read."""
    if format == "delimited":
        try:
            rows = [row for row in csv.reader(io.StringIO(text), delimiter="\t" if delimiter == "tab" else ",",
                                             strict=True) if row]
        except csv.Error as exc:
            raise AnalysisError("invalid_delimited", "Malformed delimited table", reason=str(exc)) from exc
        if id_column is not None or columns is not None:
            rows = _project(rows, id_column, columns)
        if len(rows) < 2 or not rows[0][0].strip():
            raise AnalysisError("invalid_header", "A delimited table needs a header whose first cell names the ID column")
        if any(not cell.strip() for cell in rows[0][1:]):
            raise AnalysisError("invalid_id", "Column labels must be nonblank strings", role="column")
        if any(not row[0].strip() for row in rows[1:]):
            raise AnalysisError("invalid_id", "Row labels must be nonblank strings", role="row")
        return [rows[0]] + [[row[0]] + ["." if cell.strip() in ("", "NA") else cell.strip() for cell in row[1:]]
                            for row in rows[1:]]
    lines = [line for line in text.splitlines() if line.strip()]
    tabbed = bool(lines) and "\t" in lines[0]
    rows = [line.split("\t") if tabbed else line.split() for line in lines]
    if len(rows) < 2 or not rows[0] or rows[0][0] != ".":
        raise AnalysisError("invalid_past_header", "Expected a classic PAST header beginning with '.'")
    return rows


def _project(rows, id_column, columns):
    if not rows:
        raise AnalysisError("invalid_header", "A delimited table needs a header")
    header = rows[0]
    if any(len(row) != len(header) for row in rows[1:]):
        raise AnalysisError("row_width", "Row width differs from the header")
    wanted = [id_column or header[0], *(columns if columns is not None else
                                         [name for name in header if name != (id_column or header[0])])]
    unknown = [name for name in wanted if name not in header]
    if unknown:
        raise AnalysisError("unknown_column", "Declared columns do not exist", columns=unknown, available=header)
    repeated = sorted({name for name in wanted if header.count(name) > 1} | {name for name in wanted if wanted.count(name) > 1})
    if repeated:
        raise AnalysisError("duplicate_id", "Declared columns must name unique header labels, once each", ids=repeated)
    index = [header.index(name) for name in wanted]
    return [[row[i] for i in index] for row in rows]


class CommunitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["community"]
    input: Path
    format: Literal["past", "delimited"] = Field(description=FORMAT_HELP)
    delimiter: Literal["tab", "comma"] | None = Field(default=None, description="Required for format 'delimited'")
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    value_type: Literal["count", "abundance"] = Field(description=VALUE_TYPE_HELP)
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
        check_delimiter(self)
        if self.distance == "jaccard" and self.transform != "none":
            raise ValueError("Relative abundance is an unsupported no-op before binary Jaccard; request transform='none'")
        if self.baseline_run is not None and (self.purpose is None or not self.purpose.strip()):
            raise ValueError("A baseline reference requires a stated sensitivity purpose")
        return self


class CommunityDiversity(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    total: FiniteFloat | None = Field(default=None, gt=0, description="Specimen total; count input only")
    weight_sum: FiniteFloat | None = Field(default=None, gt=0, description="Sum of abundance weights, not specimen N; abundance input only")
    richness: int = Field(ge=1)
    shannon: FiniteFloat = Field(ge=0)
    simpson: FiniteFloat = Field(ge=0, le=1)


class CommunityExclusion(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    reason: Literal["empty_sample"]


class CommunityWarning(ResultItem):
    code: Literal["near_duplicate_labels", "negative_eigenvalues", "identical_samples", "repeated_block"]
    message: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)


class CommunityResult(ResultItem):
    method: Literal["community"]
    method_version: Literal[1]
    value_type: Literal["count", "abundance"]
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
    retained_counts: list[list[FiniteFloat]] | None = Field(default=None, description="Count input only")
    retained_values: list[list[FiniteFloat]] | None = Field(default=None, description="Abundance input only")
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
        matrix_key, sum_key = value_keys(self.value_type)
        other_matrix, other_sum = value_keys("abundance" if self.value_type == "count" else "count")
        if getattr(self, matrix_key) is None or getattr(self, other_matrix) is not None:
            raise ValueError(f"{self.value_type} results carry {matrix_key} only")
        if any(getattr(row, sum_key) is None or getattr(row, other_sum) is not None for row in self.diversity):
            raise ValueError(f"{self.value_type} diversity records carry {sum_key} only")
        retained = getattr(self, matrix_key)
        for matrix in (retained, self.transformed_matrix):
            if len(matrix) != self.n or any(len(row) != self.n_taxa for row in matrix):
                raise ValueError("Community matrix shape disagrees with labels")
            if any(value < 0 for row in matrix for value in row):
                raise ValueError("Community matrices must be nonnegative")
        if self.value_type == "count" and any(value > MAX_EXACT_COUNT or value != int(value)
                                              for row in retained for value in row):
            raise ValueError("Retained counts must be exactly representable nonnegative integers")
        if len(self.diversity) != self.n or [item.sample_id for item in self.diversity] != ids:
            raise ValueError("Diversity records must align with samples")
        values = np.asarray(retained, dtype=float)
        if np.any(values.sum(axis=1) <= 0) or not np.all(values.sum(axis=1) <= MAX_ABUNDANCE_ROW_SUM):
            raise ValueError("Retained rows must have positive sums within the supported float64 range")
        expected_transformed, expected_distances = community_distances(values, transform=self.transform, distance=self.distance)
        if (not np.allclose(self.transformed_matrix, expected_transformed, rtol=1e-12, atol=0) or
                not np.allclose(self.distances, expected_distances, rtol=1e-10, atol=1e-12)):
            raise ValueError("Transformed values or distances disagree with the retained values and declared settings")
        for item, row in zip(self.diversity, values, strict=True):
            expected = _diversity_row(item.sample_id, row, self.value_type)
            if (item.richness != expected["richness"] or
                    not np.allclose([getattr(item, sum_key), item.shannon, item.simpson],
                                    [expected[sum_key], expected["shannon"], expected["simpson"]], rtol=1e-12, atol=1e-15)):
                raise ValueError("Diversity disagrees with the retained values")
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


def value_keys(value_type):
    """Result field names: counts keep specimen-count labels; abundance uses value/weight labels."""
    return ("retained_counts", "total") if value_type == "count" else ("retained_values", "weight_sum")


def without_absent_branch(result):
    """Drop the unused count/abundance field names so each result carries only honest labels."""
    matrix_key, sum_key = value_keys("abundance" if result["value_type"] == "count" else "count")
    result.pop(matrix_key, None)
    for row in result.get("diversity", []):
        row.pop(sum_key, None)
    return result


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


def _table_warnings(input_ids, taxon_ids, counts, retained_ids):
    return (_near_duplicates(input_ids, "sample") + _near_duplicates(taxon_ids, "taxon")
            + repeated_warnings([tuple(row) for row in counts], retained_ids, "samples"))


def _prepare_counts(matrix, *, sample_ids, taxon_ids, empty_samples, metadata, value_type="count"):
    samples, taxa = _ids(sample_ids, "sample"), _ids(taxon_ids, "taxon")
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
    if value_type not in {"count", "abundance"}:
        raise AnalysisError("invalid_option", "Declare value_type as count or abundance")
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            try:
                numeric = not isinstance(value, (bool, np.bool_)) and isinstance(value, Real) and np.isfinite(float(value))
                if value_type == "count":
                    valid = numeric and 0 <= value <= MAX_EXACT_COUNT and int(value) == value
                else:
                    valid = numeric and value >= 0 and not (value > 0 and float(value) == 0)
            except (ValueError, OverflowError, TypeError):
                valid = False
            if not valid:
                if value_type == "count":
                    raise AnalysisError("invalid_count", "Counts must be finite nonnegative exactly representable integers; proportions are unsupported and must not be rescaled or rounded into counts; declare value_type 'abundance' for weights",
                                        sample_id=samples[i], taxon_id=taxa[j])
                raise AnalysisError("invalid_abundance", "Abundance weights must be finite nonnegative numbers representable in float64; a positive weight may not underflow to zero",
                                    sample_id=samples[i], taxon_id=taxa[j])
    if value_type == "count":
        exact_totals = [sum(int(value) for value in row) for row in values]
        if any(total > MAX_EXACT_COUNT for total in exact_totals):
            raise AnalysisError("count_range", "Sample totals exceed exact float64 integer range")
    else:
        try:
            exact_totals = [math.fsum(float(value) for value in row) for row in values]
        except OverflowError:
            exact_totals = [math.inf]
        if any(not total <= MAX_ABUNDANCE_ROW_SUM for total in exact_totals):
            raise AnalysisError("abundance_range", "Abundance row sums must be finite and at most a quarter of the float64 maximum, so pairwise sums cannot overflow; rescale the table by a common factor",
                                limit=MAX_ABUNDANCE_ROW_SUM)
    counts = np.asarray(values, dtype=np.float64)
    total = np.asarray(exact_totals, dtype=np.float64)
    aligned = _metadata(metadata, samples)
    empty = total == 0
    excluded = [{"sample_id": name, "reason": "empty_sample"} for name, flag in zip(samples, empty) if flag]
    if excluded and empty_samples == "error":
        raise AnalysisError("empty_samples", "Empty samples require an explicit drop policy", excluded=excluded)
    keep = ~empty
    retained_ids = [name for name, flag in zip(samples, keep) if flag]
    if not retained_ids:
        raise AnalysisError("insufficient_samples", "No nonempty sample remains after declared exclusions")
    return {"counts": counts[keep], "input_sample_ids": samples, "sample_ids": retained_ids,
            "taxon_ids": taxa, "excluded": excluded,
            "metadata": None if aligned is None else [row for row, flag in zip(aligned, keep) if flag],
            "warnings": _table_warnings(samples, taxa, counts[keep].tolist(), retained_ids)}


def _prepare(matrix, *, sample_ids, taxon_ids, dimensions, empty_samples, metadata, value_type="count"):
    if not isinstance(dimensions, int) or isinstance(dimensions, bool) or dimensions < 1:
        raise AnalysisError("invalid_dimensions", "dimensions must be a positive integer")
    prepared = _prepare_counts(matrix, sample_ids=sample_ids, taxon_ids=taxon_ids,
                               empty_samples=empty_samples, metadata=metadata, value_type=value_type)
    n = len(prepared["sample_ids"])
    if n <= dimensions:
        raise AnalysisError("insufficient_samples", "More retained samples than ordination dimensions are required",
                            retained=n, dimensions=dimensions)
    estimated = 6 * n**2 * 8
    if estimated > MAX_MATRIX_BYTES:
        raise AnalysisError("resource_limit", "Distance/eigen matrices exceed the local allocation budget",
                            estimated_bytes=estimated, limit_bytes=MAX_MATRIX_BYTES)
    return prepared


def _read_inputs(spec, data, metadata):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AnalysisError("invalid_encoding", "The count matrix must be UTF-8 text") from exc
    rows = parse_table(text, spec.format, spec.delimiter)
    columns = _ids(rows[0][1:], "column")
    labels = _ids([row[0] for row in rows[1:]], "row")
    values = []
    abundance = getattr(spec, "value_type", "count") == "abundance"
    for line, row in enumerate(rows[1:], 2):
        if len(row) != len(columns) + 1:
            raise AnalysisError("row_width", "Row width differs from the header", line=line)
        if "." in row[1:]:
            raise AnalysisError("missing_counts", "Missing values cannot be converted to absences", line=line)
        if abundance:
            values.append(_abundance_row(row[1:], line))
            continue
        try:
            parsed = [Decimal(token) for token in row[1:]]
            if any(not value.is_finite() or value < 0 or value > MAX_EXACT_COUNT or
                   value != value.to_integral_value() for value in parsed):
                raise ValueError("Count token is not a finite nonnegative exact integer")
            values.append([float(value) for value in parsed])
        except (ValueError, InvalidOperation, OverflowError) as exc:
            raise AnalysisError("invalid_count", "Invalid count token; proportions are unsupported and must not be rescaled or rounded into counts; declare value_type 'abundance' for weights", line=line) from exc
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


def _abundance_row(tokens, line):
    """Parse finite nonnegative weights without rounding a positive value to zero or infinity."""
    parsed = []
    for token in tokens:
        try:
            value = Decimal(token)
        except InvalidOperation as exc:
            raise AnalysisError("invalid_abundance", "Invalid abundance token", line=line) from exc
        number = float(value) if value.is_finite() else math.nan
        if not value.is_finite() or value < 0 or not math.isfinite(number) or (value > 0 and number == 0):
            raise AnalysisError("invalid_abundance", "Abundance weights must be finite nonnegative values representable in float64",
                                line=line)
        parsed.append(number)
    return parsed


def validate_community(spec, data, metadata=None):
    spec = spec if isinstance(spec, CommunitySpec) else CommunitySpec.model_validate(spec)
    matrix, samples, taxa, meta = _read_inputs(spec, data, metadata)
    prepared = _prepare(matrix, sample_ids=samples, taxon_ids=taxa, dimensions=spec.dimensions,
                        empty_samples=spec.empty_samples, metadata=meta, value_type=spec.value_type)
    return {"status": "valid", "n_input": len(samples), "n": len(prepared["sample_ids"]),
            "n_taxa": len(taxa), "excluded": prepared["excluded"], "warnings": prepared["warnings"],
            "scope": f"Input structure and {spec.value_type} semantics checked; no distance matrix or eigendecomposition computed"}


def community_distances(counts, *, transform, distance):
    """Construct declared dissimilarities without any ordination cutoff."""
    if transform not in {"none", "relative_abundance"} or distance not in {"braycurtis", "jaccard"}:
        raise AnalysisError("invalid_option", "Declare supported transformation and distance explicitly")
    if distance == "jaccard" and transform != "none":
        raise AnalysisError("unsupported_combination", "Relative abundance is an unsupported no-op before binary Jaccard; request transform='none'")
    sums = counts.sum(axis=1)
    if not np.all(sums <= MAX_ABUNDANCE_ROW_SUM):
        raise AnalysisError("abundance_range", "Row sums exceed the supported float64 range for pairwise dissimilarities",
                            limit=MAX_ABUNDANCE_ROW_SUM)
    transformed = counts if transform == "none" else counts / sums[:, None]
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


def _diversity_row(name, row, value_type):
    row = np.asarray(row, dtype=float)
    total = row.sum()
    proportions = row / total
    positive = proportions[proportions > 0]
    return {"sample_id": name, value_keys(value_type)[1]: float(total), "richness": int(np.count_nonzero(row)),
            "shannon": float(-np.sum(positive * np.log(positive))), "simpson": float(1 - np.sum(proportions**2))}


def analyse_community(matrix, *, sample_ids, taxon_ids, transform, distance, dimensions,
                      empty_samples, metadata=None, value_type="count"):
    """Analyse declared counts or abundance weights in canonical sample-by-taxon orientation."""
    if (not isinstance(transform, str) or not isinstance(distance, str) or
        transform not in {"none", "relative_abundance"} or distance not in {"braycurtis", "jaccard"}):
        raise AnalysisError("invalid_option", "Declare supported transformation and distance explicitly")
    if distance == "jaccard" and transform != "none":
        raise AnalysisError("unsupported_combination", "Relative abundance is an unsupported no-op before binary Jaccard; request transform='none'")
    data = _prepare(matrix, sample_ids=sample_ids, taxon_ids=taxon_ids, dimensions=dimensions,
                    empty_samples=empty_samples, metadata=metadata, value_type=value_type)
    counts = data["counts"]
    diversity = [_diversity_row(name, row, value_type) for name, row in zip(data["sample_ids"], counts)]
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
    count_limit = ("Diversity is observed and unstandardised; unequal totals can confound comparisons through sampling effort"
                   if value_type == "count" else
                   "Abundance weights carry no specimen counts: richness counts positive categories, Shannon and Simpson "
                   "describe normalised weights, and no count-based estimator or sampling-effort correction is possible")
    result = {"method": "community", "method_version": 1, "value_type": value_type,
              "canonical_orientation": "samples_by_taxa", "transform": transform, "distance": distance,
              "missing": "error", "empty_samples": empty_samples, "dimensions": dimensions,
              "n_input": len(data["input_sample_ids"]), "n": n, "n_taxa": counts.shape[1],
              "input_sample_ids": data["input_sample_ids"], "sample_ids": data["sample_ids"],
              "taxon_ids": data["taxon_ids"], value_keys(value_type)[0]: counts.tolist(),
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
                              "Value declaration and sampling meaning require scientific judgment",
                              count_limit,
                              "PCoA coordinates retain positive axes only; negative eigenvalues are reported, not corrected",
                              "Axis proportions refer to positive inertia, not total variance",
                              "Eigenaxis signs and orientations within tied eigenspaces are arbitrary"]}
    return without_absent_branch(CommunityResult.model_validate(result).model_dump(mode="json"))


def calculate_community(spec, data, metadata=None):
    spec = spec if isinstance(spec, CommunitySpec) else CommunitySpec.model_validate(spec)
    matrix, samples, taxa, meta = _read_inputs(spec, data, metadata)
    return analyse_community(matrix, sample_ids=samples, taxon_ids=taxa, transform=spec.transform,
                             distance=spec.distance, dimensions=spec.dimensions,
                             empty_samples=spec.empty_samples, metadata=meta, value_type=spec.value_type)


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
    prefix = "N=" if result["value_type"] == "count" else "Σw="
    key = value_keys(result["value_type"])[1]
    axes[1].bar_label(bars, labels=[f"{prefix}{row[key]:g}" for row in result["diversity"]], fontsize=8, padding=3)
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
