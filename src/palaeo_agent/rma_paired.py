"""Paired comparison of two RMA fits on the same specimens by a seeded specimen bootstrap."""

from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from scipy.stats import binom

from .core import (
    REFERENCE, SUMMARY_KEYS, AnalysisError, ResultItem, RmaWarning, _same, past_header, past_values,
    padded_warnings, resolve_columns, rma_regression,
)

MAX_INDEX_ENTRIES = 2_000_000
CHUNK_ENTRIES = 250_000
BAND_LEVEL = 0.99
AXES = ("a_x", "a_y", "b_x", "b_y")
REFERENCES = [REFERENCE, "ISBN 9780412042317", "https://doi.org/10.1017/S1464793106007007"]
SCOPE = ("Approximate first-order percentile interval for the paired slope difference; marginal. Inspection checks the "
         "saved replicates' internal consistency; only reproduction checks that they derive from the pairs and seed")
LIMITATIONS = [
    "The percentile bootstrap is first-order approximate and assumes independent, exchangeable specimens",
    "The signed RMA slope is discontinuous at zero covariance; intervals are unreliable when replicate slopes change sign",
    "Endpoint bands describe Monte Carlo error at the declared replicate count, not sampling coverage",
    "No measurement-error model; the comparison does not identify which measurement definition is correct",
    "Marginal interval; make no joint claims with intervals from separate analyses",
]


class Axes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: str = Field(min_length=1, description="Exact predictor column label")
    y: str = Field(min_length=1, description="Exact response column label")


class Bootstrap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    replicates: int = Field(ge=999, le=100_000, strict=True)
    seed: int = Field(ge=0, le=2**63 - 1, strict=True)
    confidence: float = Field(gt=0, lt=1, strict=True)


class RmaPairedSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["rma_paired"]
    input: Path = Field(description="Classic PAST table; relative to the specification file in the CLI")
    format: Literal["past"]
    a: Axes = Field(description="First measurement definition; fits may share columns")
    b: Axes = Field(description="Second measurement definition on the same specimens")
    transform: Literal["none", "log10"]
    missing: Literal["error", "drop_pairs"]
    bootstrap: Bootstrap


class PairedRecord(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    a_x_raw: FiniteFloat
    a_y_raw: FiniteFloat
    b_x_raw: FiniteFloat
    b_y_raw: FiniteFloat
    a_x: FiniteFloat
    a_y: FiniteFloat
    b_x: FiniteFloat
    b_y: FiniteFloat


class PairedExclusion(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    reason: Literal["declared_missing_value"]
    columns: list[Literal["a_x", "a_y", "b_x", "b_y"]] = Field(min_length=1)


class FitSummary(ResultItem):
    x: str
    y: str
    mean_x: FiniteFloat
    mean_y: FiniteFloat
    sd_x: FiniteFloat = Field(gt=0)
    sd_y: FiniteFloat = Field(gt=0)
    correlation: FiniteFloat = Field(ge=-1, le=1)
    slope: FiniteFloat
    intercept: FiniteFloat
    vertical_residual_rmse: FiniteFloat = Field(ge=0)
    x_raw_range: list[FiniteFloat] = Field(min_length=2, max_length=2)
    y_raw_range: list[FiniteFloat] = Field(min_length=2, max_length=2)
    warnings: list[RmaWarning]


class EndpointBand(ResultItem):
    quantile: float
    order_statistics: list[int] = Field(min_length=2, max_length=2)
    band: list[FiniteFloat | None] = Field(min_length=2, max_length=2)
    unbounded: bool


class BootstrapRecord(ResultItem):
    replicates: int
    seed: int
    bit_generator: Literal["PCG64"]
    numpy_version: str = Field(min_length=1)
    dtype: Literal["int64"]
    draw: Literal["integers(0, n, size=(replicates, n), dtype=int64), one call, row r is replicate r"]
    confidence: float
    interval: list[FiniteFloat] = Field(min_length=2, max_length=2)
    standard_error: FiniteFloat = Field(ge=0)
    band_level: Literal[0.99]
    endpoint_bands: list[EndpointBand] = Field(min_length=2, max_length=2)
    resolution: Literal["zero_excluded", "zero_included", "monte_carlo_unresolved"]
    sign_changes: dict[Literal["a", "b"], int]
    slope_a: list[FiniteFloat]
    slope_b: list[FiniteFloat]
    difference: list[FiniteFloat]


class PairedWarning(ResultItem):
    code: Literal["padded_column_label", "bootstrap_sign_changes"]
    message: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)


class RmaPairedResult(ResultItem):
    method: Literal["rma_paired"]
    method_version: Literal[1]
    transform: Literal["none", "log10"]
    missing: Literal["error", "drop_pairs"]
    n_input: int = Field(ge=3)
    n: int = Field(ge=3)
    excluded: list[PairedExclusion]
    fit_a: FitSummary
    fit_b: FitSummary
    difference: FiniteFloat
    bootstrap: BootstrapRecord
    pairs: list[PairedRecord] = Field(min_length=3)
    warnings: list[PairedWarning]
    references: list[str]
    limitations: list[str]
    scope: Literal[SCOPE]

    @model_validator(mode="after")
    def consistent_records(self):
        _check_saved(self)
        return self


def _summary(result, x, y):
    return {"x": x, "y": y, **{key: result[key] for key in SUMMARY_KEYS},
            "x_raw_range": result["x_raw_range"], "y_raw_range": result["y_raw_range"], "warnings": result["warnings"]}


def _fits(pairs, transform, labels):
    ids = [pair["sample_id"] for pair in pairs]
    fits = {}
    for fit in ("a", "b"):
        result = rma_regression([pair[f"{fit}_x_raw"] for pair in pairs], [pair[f"{fit}_y_raw"] for pair in pairs],
                                sample_ids=ids, transform=transform, missing="error")
        fits[fit] = _summary(result, *labels[fit])
    return fits


def _signed_slopes(x, y):
    """Signed RMA slopes of each row of x and y (replicates by specimens), with undefined rows flagged by reason."""
    try:
        with np.errstate(over="raise", invalid="raise"):
            sd_x, sd_y = x.std(axis=1, ddof=1), y.std(axis=1, ddof=1)
            covariance = ((x - x.mean(axis=1, keepdims=True)) * (y - y.mean(axis=1, keepdims=True))).sum(axis=1)
    except FloatingPointError as exc:
        raise AnalysisError("numerical_range", "Bootstrap refits exceed the supported numerical range") from exc
    zero_variance = (sd_x == 0) | (sd_y == 0)
    zero_covariance = ~zero_variance & (covariance == 0)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        slopes = np.copysign(sd_y / sd_x, covariance)
    if not np.isfinite(slopes[~zero_variance & ~zero_covariance]).all():
        raise AnalysisError("numerical_range", "Bootstrap slopes exceed the supported numerical range")
    return slopes, zero_variance, zero_covariance


def bootstrap_slopes(analysed, replicates, seed):
    """Replicate slopes for fits a and b; one int64 index draw, refitted in chunks within the index budget."""
    n = len(analysed["a_x"])
    rng = np.random.Generator(np.random.PCG64(seed))
    index = rng.integers(0, n, size=(replicates, n), dtype=np.int64)
    chunk = max(1, CHUNK_ENTRIES // n)
    slopes = {"a": np.empty(replicates), "b": np.empty(replicates)}
    undefined = {fit: {"zero_variance": 0, "zero_covariance": 0} for fit in ("a", "b")}
    for start in range(0, replicates, chunk):
        rows = index[start:start + chunk]
        for fit in ("a", "b"):
            values, zero_variance, zero_covariance = _signed_slopes(analysed[f"{fit}_x"][rows], analysed[f"{fit}_y"][rows])
            slopes[fit][start:start + chunk] = values
            undefined[fit]["zero_variance"] += int(zero_variance.sum())
            undefined[fit]["zero_covariance"] += int(zero_covariance.sum())
    return slopes, undefined


def summarise(slope_a, slope_b, difference, confidence, observed):
    """Interval, standard error, Monte Carlo endpoint bands, resolution and sign changes from saved replicates."""
    d = np.asarray(difference, dtype=np.float64)
    if not np.isfinite(d).all():
        raise AnalysisError("numerical_range", "Bootstrap differences exceed the supported numerical range")
    replicates = len(d)
    quantiles = [(1 - confidence) / 2, (1 + confidence) / 2]
    try:
        with np.errstate(over="raise", invalid="raise"):
            interval = [float(value) for value in np.quantile(d, quantiles, method="linear")]
            standard_error = float(np.std(d, ddof=1))
    except FloatingPointError as exc:
        raise AnalysisError("numerical_range", "Bootstrap summaries exceed the supported numerical range") from exc
    if not all(np.isfinite([*interval, standard_error])):
        raise AnalysisError("numerical_range", "Bootstrap summaries exceed the supported numerical range")
    ordered = np.sort(d)
    bands = []
    for q in quantiles:
        low = int(binom.ppf((1 - BAND_LEVEL) / 2, replicates, q))
        high = int(binom.ppf((1 + BAND_LEVEL) / 2, replicates, q)) + 1
        bands.append({"quantile": q, "order_statistics": [low, high],
                      "band": [float(ordered[low - 1]) if low > 0 else None,
                               float(ordered[high - 1]) if high <= replicates else None],
                      "unbounded": low == 0 or high == replicates + 1})
    lower, upper = bands[0]["band"], bands[1]["band"]
    if any(band["unbounded"] for band in bands):
        resolution = "monte_carlo_unresolved"
    elif lower[0] > 0 or upper[1] < 0:
        resolution = "zero_excluded"
    elif lower[1] <= 0 <= upper[0]:
        resolution = "zero_included"
    else:
        resolution = "monte_carlo_unresolved"
    sign_changes = {fit: int(np.sum(np.sign(np.asarray(values)) != np.sign(observed[fit])))
                    for fit, values in (("a", slope_a), ("b", slope_b))}
    return {"interval": interval, "standard_error": standard_error, "band_level": BAND_LEVEL,
            "endpoint_bands": bands, "resolution": resolution, "sign_changes": sign_changes}


def _sign_warning(sign_changes):
    if not any(sign_changes.values()):
        return []
    return [{"code": "bootstrap_sign_changes",
             "message": "Some replicate slopes change sign; the signed statistic is discontinuous at zero covariance "
                        "and the percentile interval is unreliable across it",
             "details": dict(sign_changes)}]


def calculate_rma_paired(spec: RmaPairedSpec, data: bytes):
    for fit, axes in (("a", spec.a), ("b", spec.b)):
        if axes.x == axes.y:
            raise AnalysisError("same_column", "x and y must select different columns within a fit", fit=fit)
    names, rows = past_header(data)
    selected = {fit: resolve_columns(names, axes.x, axes.y) for fit, axes in (("a", spec.a), ("b", spec.b))}
    ids, values = past_values(names, rows)
    if len(set(ids)) != len(ids) or any(not item.strip() for item in ids):
        raise AnalysisError("duplicate_sample_id", "Sample IDs must be unique and nonblank")
    columns = {"a_x": selected["a"][0], "a_y": selected["a"][1], "b_x": selected["b"][0], "b_y": selected["b"][1]}
    pairs, excluded = [], []
    for sample_id, row in zip(ids, values, strict=True):
        missing = [axis for axis in AXES if row[columns[axis]] is None]
        if missing:
            excluded.append({"sample_id": sample_id, "reason": "declared_missing_value", "columns": missing})
            continue
        pair = {"sample_id": sample_id, **{f"{axis}_raw": float(row[columns[axis]]) for axis in AXES}}
        if spec.transform == "log10" and any(pair[f"{axis}_raw"] <= 0 for axis in AXES):
            raise AnalysisError("nonpositive_log", "log10 requires positive measurements", sample_id=sample_id)
        pairs.append(pair)
    if excluded and spec.missing == "error":
        raise AnalysisError("missing_pairs", "Declared missing measurements require an explicit drop_pairs policy",
                            excluded=excluded)
    n = len(pairs)
    if n < 3:
        raise AnalysisError("insufficient_pairs", "At least three complete specimens are required", n=n)
    if spec.bootstrap.replicates * n > MAX_INDEX_ENTRIES:
        raise AnalysisError("resource_limit", "Bootstrap index matrix exceeds the allocation budget",
                            entries=spec.bootstrap.replicates * n, limit=MAX_INDEX_ENTRIES)
    labels = {"a": (spec.a.x, spec.a.y), "b": (spec.b.x, spec.b.y)}
    fits = _fits(pairs, spec.transform, labels)
    analysed = {}
    for axis in AXES:
        raw = np.asarray([pair[f"{axis}_raw"] for pair in pairs], dtype=np.float64)
        analysed[axis] = np.log10(raw) if spec.transform == "log10" else raw
        for pair, value in zip(pairs, analysed[axis], strict=True):
            pair[axis] = float(value)
    slopes, undefined = bootstrap_slopes(analysed, spec.bootstrap.replicates, spec.bootstrap.seed)
    if any(count for fit in undefined.values() for count in fit.values()):
        raise AnalysisError("degenerate_bootstrap", "Some bootstrap replicates have an undefined RMA slope; no draw is "
                            "dropped or redrawn", undefined=undefined, replicates=spec.bootstrap.replicates)
    with np.errstate(over="ignore", invalid="ignore"):
        difference = slopes["b"] - slopes["a"]
    observed = {fit: fits[fit]["slope"] for fit in ("a", "b")}
    summary = summarise(slopes["a"], slopes["b"], difference, spec.bootstrap.confidence, observed)
    observed_difference = fits["b"]["slope"] - fits["a"]["slope"]
    if not np.isfinite(observed_difference):
        raise AnalysisError("numerical_range", "Observed slope difference exceeds the supported numerical range")
    selection = padded_warnings(names, [(f"{fit}.{axis}", name, index) for fit, axes in labels.items()
                                        for axis, name, index in zip(("x", "y"), axes, selected[fit], strict=True)])
    result = {"method": "rma_paired", "method_version": 1, "transform": spec.transform, "missing": spec.missing,
              "n_input": len(ids), "n": n, "excluded": excluded, "fit_a": fits["a"], "fit_b": fits["b"],
              "difference": observed_difference,
              "bootstrap": {"replicates": spec.bootstrap.replicates, "seed": spec.bootstrap.seed, "bit_generator": "PCG64",
                            "numpy_version": np.__version__, "dtype": "int64",
                            "draw": "integers(0, n, size=(replicates, n), dtype=int64), one call, row r is replicate r",
                            "confidence": spec.bootstrap.confidence, **summary,
                            "slope_a": slopes["a"].tolist(), "slope_b": slopes["b"].tolist(),
                            "difference": difference.tolist()},
              "pairs": pairs, "warnings": selection + _sign_warning(summary["sign_changes"]),
              "references": REFERENCES, "limitations": LIMITATIONS, "scope": SCOPE}
    return RmaPairedResult.model_validate(result).model_dump(mode="json")


def _check_saved(result):
    retained = [pair.sample_id for pair in result.pairs]
    excluded = [item.sample_id for item in result.excluded]
    if result.n != len(retained) or result.n_input != result.n + len(excluded) or len(set(retained + excluded)) != len(
            retained + excluded):
        raise ValueError("Counts must match unique retained and excluded records")
    if result.missing == "error" and excluded:
        raise ValueError("The error missing-value policy cannot contain exclusions")
    pairs = [pair.model_dump() for pair in result.pairs]
    for axis in AXES:
        raw = np.asarray([pair[f"{axis}_raw"] for pair in pairs])
        if result.transform == "log10" and (raw <= 0).any():
            raise ValueError("Log-transformed records require positive raw measurements")
        expected = np.log10(raw) if result.transform == "log10" else raw
        if not np.allclose([pair[axis] for pair in pairs], expected, rtol=1e-12, atol=0):
            raise ValueError("Analysed values differ from the raw values under the declared transform")
    labels = {fit: (getattr(result, f"fit_{fit}").x, getattr(result, f"fit_{fit}").y) for fit in ("a", "b")}
    fits = _fits(pairs, result.transform, labels)
    if not all(_same(getattr(result, f"fit_{fit}").model_dump(mode="json"), fits[fit]) for fit in ("a", "b")):
        raise ValueError("Saved fits do not recompute from the saved pairs")
    if not _same(result.difference, fits["b"]["slope"] - fits["a"]["slope"]):
        raise ValueError("Saved slope difference does not recompute")
    record = result.bootstrap
    if not (len(record.slope_a) == len(record.slope_b) == len(record.difference) == record.replicates):
        raise ValueError("Replicate arrays must have one value per replicate")
    if any(d != b - a for a, b, d in zip(record.slope_a, record.slope_b, record.difference, strict=True)):
        raise ValueError("Each replicate difference must equal slope_b - slope_a")
    observed = {fit: fits[fit]["slope"] for fit in ("a", "b")}
    summary = summarise(record.slope_a, record.slope_b, record.difference, record.confidence, observed)
    if not _same({key: record.model_dump(mode="json")[key] for key in summary}, summary):
        raise ValueError("Saved bootstrap summaries do not recompute from the saved replicates")
    saved_sign = [warning.model_dump(mode="json") for warning in result.warnings if warning.code == "bootstrap_sign_changes"]
    if saved_sign != _sign_warning(summary["sign_changes"]):
        raise ValueError("Sign-change warning disagrees with the saved replicates")
    if result.references != REFERENCES or result.limitations != LIMITATIONS:
        raise ValueError("References or limitations differ from the method record")


def validate_rma_paired(spec, data):
    result = calculate_rma_paired(spec, data)
    return {"status": "valid", "n": result["n"], "n_input": result["n_input"], "excluded": result["excluded"],
            "warnings": result["warnings"],
            "scope": "Data, numerical and bootstrap requirements checked; scientific sampling assumptions are not established"}


def discover():
    return {"id": "rma_paired", "version": 1,
            "description": "Paired comparison of two RMA fits on the same specimens: slope difference with a seeded "
                           "specimen-bootstrap percentile interval",
            "definition": "difference = slope_b - slope_a (signed RMA slopes); replicates refit both slopes on the "
                          "same resampled specimens",
            "requirements": ["At least three specimens complete in every referenced column",
                             f"replicates x n <= {MAX_INDEX_ENTRIES}", "No undefined replicate slope"],
            "limitations": LIMITATIONS, "references": REFERENCES,
            "input_schema": RmaPairedSpec.model_json_schema(), "output_schema": RmaPairedResult.model_json_schema()}
