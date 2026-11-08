"""Individual count rarefaction and estimated population abundance coverage."""

from decimal import Decimal, localcontext
import math
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from .community import FORMAT_HELP, MAX_EXACT_COUNT, CommunityExclusion, _prepare_counts, _read_inputs, check_delimiter
from .core import AnalysisError, ResultItem, decimal_context


MAX_PRODUCT_FACTORS = 200_000
MAX_PAIR_TERMS = 100_000
MAX_ESTIMATES = 100_000
DECIMAL_PRECISION = 50
BOUNDARY_NOTE = "The coverage estimator is at its upper boundary; this does not establish complete sampling."
UNAVAILABLE = "coverage_unavailable_single_specimen"
REFERENCES = [
    "https://doi.org/10.2307/1934145",
    "https://doi.org/10.2307/1934716",
    "https://doi.org/10.1890/11-1952.1",
]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]
SizeList = Annotated[list[PositiveInt], Field(strict=True, min_length=1)]
Sizes = Literal["minimum_total"] | SizeList


class RarefactionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["rarefaction"]
    input: Path
    format: Literal["past", "delimited"] = Field(description=FORMAT_HELP)
    delimiter: Literal["tab", "comma"] | None = None
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    value_type: Literal["count"]
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]
    metadata: Path | None = None
    sizes: Sizes = "minimum_total"

    @model_validator(mode="after")
    def valid_options(self):
        check_delimiter(self)
        if isinstance(self.sizes, list) and len(set(self.sizes)) != len(self.sizes):
            raise ValueError("Subsample sizes must be distinct")
        return self


class RarefactionWarning(ResultItem):
    code: Literal["near_duplicate_labels", "identical_samples", "repeated_block", "variance_rounding_clamped"]
    message: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)


class RarefactionEstimate(ResultItem):
    size: PositiveInt
    expected_richness: FiniteFloat = Field(ge=1)
    variance: FiniteFloat = Field(ge=0)
    conditional_sd: FiniteFloat = Field(ge=0)
    coverage: FiniteFloat | None = Field(ge=0, le=1)
    coverage_unavailable_reason: Literal["coverage_unavailable_single_specimen"] | None
    variance_clamped: bool


class RarefactionSample(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    total: PositiveInt
    observed_richness: PositiveInt
    f1: int = Field(ge=0)
    f2: int = Field(ge=0)
    full_coverage: FiniteFloat | None = Field(ge=0, le=1)
    coverage_unavailable_reason: Literal["coverage_unavailable_single_specimen"] | None
    coverage_boundary: bool
    coverage_note: str | None
    estimates: list[RarefactionEstimate]


class RarefactionResult(ResultItem):
    method: Literal["rarefaction"]
    method_version: Literal[1]
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    canonical_orientation: Literal["samples_by_taxa"]
    value_type: Literal["count"]
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]
    n_input: PositiveInt
    n: PositiveInt
    n_taxa: PositiveInt
    input_sample_ids: list[str]
    sample_ids: list[str]
    taxon_ids: list[str]
    retained_counts: list[list[Annotated[int, Field(ge=0, le=MAX_EXACT_COUNT)]]]
    sizes_requested: Sizes
    sizes: SizeList
    samples: list[RarefactionSample]
    metadata: list[dict[str, str]] | None
    excluded: list[CommunityExclusion]
    warnings: list[RarefactionWarning]
    references: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_records(self):
        for labels in (self.input_sample_ids, self.sample_ids, self.taxon_ids):
            if any(not item.strip() for item in labels) or len(set(labels)) != len(labels):
                raise ValueError("Labels must be nonblank and unique")
        if (self.n_input != len(self.input_sample_ids) or self.n != len(self.sample_ids)
                or self.n_taxa != len(self.taxon_ids)):
            raise ValueError("Counts disagree with labels")
        excluded = [item.sample_id for item in self.excluded]
        if (len(set(self.sample_ids + excluded)) != self.n + len(excluded)
                or set(self.sample_ids + excluded) != set(self.input_sample_ids)
                or self.n_input != self.n + len(excluded)):
            raise ValueError("Retained and excluded samples must partition the input")
        if self.empty_samples == "error" and excluded:
            raise ValueError("The error empty-sample policy cannot contain exclusions")
        if self.sample_ids != [name for name in self.input_sample_ids if name not in set(excluded)]:
            raise ValueError("Retained samples must preserve input order")
        if (len(self.retained_counts) != self.n
                or any(len(row) != self.n_taxa for row in self.retained_counts)):
            raise ValueError("Count matrix shape disagrees with labels")
        totals = [sum(row) for row in self.retained_counts]
        if any(not 1 <= total <= MAX_EXACT_COUNT for total in totals):
            raise ValueError("Retained totals must be positive exactly representable integers")
        if isinstance(self.sizes_requested, list) and len(set(self.sizes_requested)) != len(self.sizes_requested):
            raise ValueError("Requested sizes must be distinct")
        resolved = [min(totals)] if self.sizes_requested == "minimum_total" else sorted(self.sizes_requested)
        if self.sizes != resolved or self.sizes[-1] > min(totals):
            raise ValueError("Resolved sizes disagree with request or exceed sample totals")
        if [sample.sample_id for sample in self.samples] != self.sample_ids:
            raise ValueError("Sample statistics must align with sample labels")
        if self.metadata is not None and [row.get("sample_id") for row in self.metadata] != self.sample_ids:
            raise ValueError("Metadata must align with sample labels")
        for row, total, sample in zip(self.retained_counts, totals, self.samples):
            positive = [value for value in row if value]
            richness, f1, f2 = len(positive), positive.count(1), positive.count(2)
            if (sample.total, sample.observed_richness, sample.f1, sample.f2) != (total, richness, f1, f2):
                raise ValueError("Sample statistics disagree with retained counts")
            full, boundary, reason = _full_coverage(total, f1, f2)
            if (sample.full_coverage != full or sample.coverage_boundary != boundary
                    or sample.coverage_unavailable_reason != reason
                    or sample.coverage_note != (BOUNDARY_NOTE if boundary else None)):
                raise ValueError("Full coverage and boundary diagnostics disagree with sample counts")
            if [estimate.size for estimate in sample.estimates] != self.sizes:
                raise ValueError("Estimate sizes must align with resolved sizes")
            for estimate in sample.estimates:
                upper = min(estimate.size, richness)
                if estimate.expected_richness > upper or estimate.variance > (upper - 1)**2 / 4:
                    raise ValueError("Richness estimates exceed mathematical bounds")
                if not math.isclose(estimate.conditional_sd, math.sqrt(estimate.variance), rel_tol=1e-14, abs_tol=1e-15):
                    raise ValueError("Conditional SD disagrees with variance")
                if estimate.variance_clamped and estimate.variance != 0:
                    raise ValueError("Clamped variance must equal zero")
                if estimate.coverage_unavailable_reason != reason or (estimate.coverage is None) != (total == 1):
                    raise ValueError("Coverage nullability and reason disagree with sample size")
                if estimate.size == total and estimate.coverage != full:
                    raise ValueError("Full-size coverage must equal full-sample coverage")
                if estimate.size in (1, total) or richness in (1, total):
                    expected = min(estimate.size, richness)
                    if estimate.expected_richness != expected or estimate.variance != 0:
                        raise ValueError("Degenerate richness estimates must be exact")
        return self


def _full_coverage(n, f1, f2):
    if n == 1:
        return None, False, UNAVAILABLE
    if f1 == 0:
        return 1.0, True, None
    with localcontext(decimal_context(DECIMAL_PRECISION)):
        numerator = (n - 1) * (f1 if f2 else f1 - 1)
        denominator = numerator + (2 * f2 if f2 else 2)
        coverage = Decimal(1) - Decimal(f1) / Decimal(n) * Decimal(numerator) / Decimal(denominator)
    return float(coverage), f1 == 1 and f2 == 0, None


def _ratio_cost(n, x, m):
    return 0 if x == 0 or n - x < m else min(x, m)


def _absence(n, x, m):
    if x == 0:
        return Decimal(1)
    if n - x < m:
        return Decimal(0)
    # Symmetry exchanges sample size and excluded count, avoiding huge products.
    # Decimal guard digits preserve rare probabilities and cancelling covariances
    # up to the accepted integer range; log-gamma subtraction does not.
    length, removed = min(x, m), max(x, m)
    probability = Decimal(1)
    for k in range(length):
        probability *= Decimal(n - k - removed) / Decimal(n - k)
    return probability


def _sum(values):
    total = Decimal(0)
    correction = Decimal(0)
    for value in values:
        adjusted = value - correction
        updated = total + adjusted
        correction = (updated - total) - adjusted
        total = updated
    return total


def _resolve_and_budget(prepared, sizes):
    if sizes != "minimum_total":
        if (not isinstance(sizes, list) or not sizes
                or any(type(size) is not int or size < 1 for size in sizes)
                or len(set(sizes)) != len(sizes)):
            raise AnalysisError("invalid_sizes", "sizes must be minimum_total or distinct strict positive integers")
    rows = [[int(value) for value in row if value] for row in prepared["counts"]]
    totals = [sum(row) for row in rows]
    resolved = [min(totals)] if sizes == "minimum_total" else sorted(sizes)
    for sample_id, total in zip(prepared["sample_ids"], totals):
        if resolved[-1] > total:
            raise AnalysisError("size_exceeds_total", "Subsample size exceeds a retained sample total; extrapolation is unsupported",
                                sample_id=sample_id, total=total, size=resolved[-1])
    estimates = len(rows) * len(resolved)
    if estimates > MAX_ESTIMATES:
        raise AnalysisError("resource_limit", "Requested estimate count exceeds the bounded local budget",
                            estimates=estimates, limit=MAX_ESTIMATES)
    pairs = factors = 0
    for sample_id, row, total in zip(prepared["sample_ids"], rows, totals):
        richness = len(row)
        distinct = set(row)
        for m in resolved:
            general = m not in (1, total) and richness not in (1, total)
            if general:
                pairs += richness * (richness - 1) // 2
                if pairs > MAX_PAIR_TERMS:
                    raise AnalysisError("resource_limit", "Conditional variance pair terms exceed the bounded local budget",
                                        sample_id=sample_id, pair_terms=pairs, limit=MAX_PAIR_TERMS)
                excluded = set(distinct)
                excluded.update(row[i] + row[j] for i in range(richness) for j in range(i))
                factors += sum(_ratio_cost(total, x, m) for x in excluded)
            if m < total and richness not in (1, total):
                factors += sum(_ratio_cost(total - 1, x - 1, m) for x in distinct)
            if factors > MAX_PRODUCT_FACTORS:
                raise AnalysisError("resource_limit", "Stable binomial-ratio product factors exceed the bounded local budget",
                                    sample_id=sample_id, size=m, product_factors=factors, limit=MAX_PRODUCT_FACTORS,
                                    precision=DECIMAL_PRECISION)
    return resolved


def _estimate(row, m, full_coverage, reason, n):
    richness = len(row)
    clamped = False
    with localcontext(decimal_context(DECIMAL_PRECISION)):
        if m in (1, n) or richness in (1, n):
            expected, variance = Decimal(min(m, richness)), Decimal(0)
        else:
            cache = {}
            def q(x):
                if x not in cache:
                    cache[x] = _absence(n, x, m)
                return cache[x]
            probabilities = [q(x) for x in row]
            expected = _sum(1 - value for value in probabilities)
            diagonal = _sum(value * (1 - value) for value in probabilities)
            covariance = _sum(q(row[i] + row[j]) - probabilities[i] * probabilities[j]
                              for i in range(richness) for j in range(i))
            variance = diagonal + 2 * covariance
            if variance < 0:
                tolerance = Decimal(64) * Decimal.from_float(math.ulp(1.0)) * expected**2
                if -variance > tolerance:
                    raise AnalysisError("numerical_failure", "Conditional variance is materially negative", size=m)
                variance, clamped = Decimal(0), True
        if m == n:
            coverage = full_coverage
        elif richness == n:
            coverage = 0.0
        elif richness == 1:
            coverage = 1.0
        else:
            coverage_cache = {x: _absence(n - 1, x - 1, m) for x in set(row)}
            coverage = float(1 - _sum(Decimal(x) / Decimal(n) * coverage_cache[x] for x in row))
        expected_float, variance_float = float(expected), float(variance)
        if not 1 <= expected_float <= min(m, richness) or (coverage is not None and not 0 <= coverage <= 1):
            raise AnalysisError("numerical_failure", "Rarefaction estimates exceed their mathematical bounds", size=m)
    return {"size": m, "expected_richness": expected_float, "variance": variance_float,
            "conditional_sd": math.sqrt(variance_float), "coverage": coverage,
            "coverage_unavailable_reason": reason, "variance_clamped": clamped}


def analyse_rarefaction(matrix, *, sample_ids, taxon_ids, empty_samples, sizes="minimum_total", metadata=None,
                        orientation="samples_by_taxa"):
    """Analyse a canonical sample-by-taxon count matrix; orientation records source layout."""
    prepared = _prepare_counts(matrix, sample_ids=sample_ids, taxon_ids=taxon_ids,
                               empty_samples=empty_samples, metadata=metadata)
    resolved = _resolve_and_budget(prepared, sizes)
    records = []
    warnings = list(prepared["warnings"])
    order = sorted(range(len(prepared["taxon_ids"])), key=lambda index: prepared["taxon_ids"][index])
    for sample_id, counts in zip(prepared["sample_ids"], prepared["counts"]):
        row = [int(counts[index]) for index in order if counts[index]]
        total, f1, f2 = sum(row), row.count(1), row.count(2)
        full, boundary, reason = _full_coverage(total, f1, f2)
        estimates = [_estimate(row, m, full, reason, total) for m in resolved]
        for estimate in estimates:
            if estimate["variance_clamped"]:
                warnings.append({"code": "variance_rounding_clamped", "message": "Rounding-scale negative conditional variance set to zero",
                                 "details": {"sample_id": sample_id, "size": estimate["size"]}})
        records.append({"sample_id": sample_id, "total": total, "observed_richness": len(row), "f1": f1, "f2": f2,
                        "full_coverage": full, "coverage_unavailable_reason": reason, "coverage_boundary": boundary,
                        "coverage_note": BOUNDARY_NOTE if boundary else None, "estimates": estimates})
    result = {"method": "rarefaction", "method_version": 1, "orientation": orientation,
              "canonical_orientation": "samples_by_taxa", "value_type": "count", "missing": "error",
              "empty_samples": empty_samples, "n_input": len(prepared["input_sample_ids"]), "n": len(records),
              "n_taxa": len(prepared["taxon_ids"]), "input_sample_ids": prepared["input_sample_ids"],
              "sample_ids": prepared["sample_ids"], "taxon_ids": prepared["taxon_ids"],
              "retained_counts": [[int(value) for value in row] for row in prepared["counts"]],
              "sizes_requested": sizes, "sizes": resolved, "samples": records, "metadata": prepared["metadata"],
              "excluded": prepared["excluded"], "warnings": warnings, "references": REFERENCES,
              "limitations": ["Richness variance and conditional SD describe subsampling without replacement of the observed counts, not between-population uncertainty or a confidence interval.",
                              "Coverage estimates population abundance represented by observed taxa, not the fraction of taxa discovered or the finite collection's represented mass.",
                              "Equal specimen counts do not establish equal completeness, collecting effort, preservation or detectability.",
                              "Interpolation only: no extrapolation, equal-coverage standardisation, or richness estimation.",
                              f"Stable {DECIMAL_PRECISION}-digit products are bounded to {MAX_PRODUCT_FACTORS} factors, {MAX_PAIR_TERMS} pair terms and {MAX_ESTIMATES} estimates per operation; larger requests are refused."]}
    return RarefactionResult.model_validate(result).model_dump(mode="json")


def calculate_rarefaction(spec, data, metadata=None):
    spec = spec if isinstance(spec, RarefactionSpec) else RarefactionSpec.model_validate(spec)
    matrix, samples, taxa, meta = _read_inputs(spec, data, metadata)
    return analyse_rarefaction(matrix, sample_ids=samples, taxon_ids=taxa, empty_samples=spec.empty_samples,
                               sizes=spec.sizes, metadata=meta, orientation=spec.orientation)


def validate_rarefaction(spec, data, metadata=None):
    spec = spec if isinstance(spec, RarefactionSpec) else RarefactionSpec.model_validate(spec)
    matrix, samples, taxa, meta = _read_inputs(spec, data, metadata)
    prepared = _prepare_counts(matrix, sample_ids=samples, taxon_ids=taxa, empty_samples=spec.empty_samples, metadata=meta)
    sizes = _resolve_and_budget(prepared, spec.sizes)
    return {"status": "valid", "n_input": len(samples), "n": len(prepared["sample_ids"]), "n_taxa": len(taxa),
            "sizes": sizes, "excluded": prepared["excluded"], "warnings": prepared["warnings"],
            "scope": "Input counts, subsample sizes and operation resource bounds checked; no rarefaction estimates computed"}
