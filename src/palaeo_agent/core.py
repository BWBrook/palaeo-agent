"""The first supported operation: descriptive reduced-major-axis regression."""

from collections import Counter, defaultdict
import math
from decimal import MAX_EMAX, MIN_EMIN, ROUND_HALF_EVEN, Context, DivisionByZero, InvalidOperation, Overflow
from numbers import Real
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from scipy.special import betaln
from scipy.stats import f as f_distribution, t as t_distribution


def decimal_context(precision, *traps):
    """A fully specified decimal context: results never depend on the caller's ambient decimal settings."""
    return Context(prec=precision, rounding=ROUND_HALF_EVEN, Emin=MIN_EMIN, Emax=MAX_EMAX, capitals=1, clamp=0,
                   flags=[], traps=[InvalidOperation, DivisionByZero, Overflow, *traps])


class AnalysisError(Exception):
    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code = code
        self.details = details

    def as_dict(self):
        return {"status": "error", "code": self.code,
                "message": str(self), "details": self.details}


class RmaInferenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confidence: float = Field(gt=0, lt=1, strict=True, description="Interval confidence and test level 1 - confidence")
    null_magnitude: FiniteFloat = Field(gt=0, description="Slope magnitude sd(y)/sd(x) under the null, on the analysed scale; isometry on log10 axes is 1")


class RmaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["rma"]
    input: Path = Field(description="Classic PAST table; relative to the specification file in the CLI")
    format: Literal["past"]
    x: str = Field(min_length=1, description="Exact predictor column label")
    y: str = Field(min_length=1, description="Exact response column label")
    transform: Literal["none", "log10"]
    missing: Literal["error", "drop_pairs"]
    inference: RmaInferenceSpec | None = Field(
        default=None, description="Optional exact interval and test for the slope magnitude, and a test of direction, "
                                  "under bivariate normality on the analysed scale")


class ResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RmaPair(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    x_raw: FiniteFloat
    y_raw: FiniteFloat
    x: FiniteFloat
    y: FiniteFloat
    residual: FiniteFloat


class RmaExclusion(ResultItem):
    sample_id: str = Field(min_length=1, pattern=r"\S")
    reason: Literal["declared_missing_pair"]
    columns: list[Literal["x", "y"]] = Field(min_length=1, max_length=2)

    @model_validator(mode="after")
    def distinct_columns(self):
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Excluded measurement columns must be distinct")
        return self


class RmaWarning(ResultItem):
    code: Literal["small_computed_correlation", "two_pairs", "padded_column_label", "repeated_pairs", "repeated_block"]
    message: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)


def _check_probability_record(record):
    if record.p_value_underflow != (record.p_value == 0):
        raise ValueError("Zero p-values must be marked as underflow")
    if record.p_value_underflow:
        if record.log10_p_value is None or record.log10_p_value >= 0:
            raise ValueError("Underflow requires a finite negative log10 p-value")
    elif record.log10_p_value is not None:
        raise ValueError("A representable p-value must not carry an underflow log value")
    return record


class MagnitudeTest(ResultItem):
    r_rf: FiniteFloat = Field(gt=-1, lt=1)
    t: FiniteFloat
    df: int = Field(ge=1)
    p_value: FiniteFloat = Field(ge=0, le=1)
    p_value_underflow: bool
    log10_p_value: FiniteFloat | None

    @model_validator(mode="after")
    def coherent_probability(self):
        return _check_probability_record(self)


class DirectionTest(ResultItem):
    r: FiniteFloat = Field(gt=-1, lt=1)
    t: FiniteFloat
    df: int = Field(ge=1)
    p_value: FiniteFloat = Field(ge=0, le=1)
    p_value_underflow: bool
    log10_p_value: FiniteFloat | None
    direction: Literal["positive", "negative", "not_established"]

    @model_validator(mode="after")
    def coherent_probability(self):
        return _check_probability_record(self)


INFERENCE_SCOPE = ("Interval and test concern the magnitude sd(y)/sd(x); direction is tested separately; "
                   "no joint signed confidence set; intervals are marginal")


class RmaInference(ResultItem):
    confidence: float = Field(gt=0, lt=1)
    magnitude_estimate: FiniteFloat = Field(gt=0)
    magnitude_interval: list[FiniteFloat] = Field(min_length=2, max_length=2)
    null_magnitude: FiniteFloat = Field(gt=0)
    magnitude_test: MagnitudeTest
    direction_test: DirectionTest
    model: Literal["independent pairs from a nonsingular bivariate normal on the analysed scale"]
    scope: Literal[INFERENCE_SCOPE]

    @model_validator(mode="after")
    def coherent_direction(self):
        test = self.direction_test
        expected = ("positive" if test.r > 0 else "negative") if test.p_value < 1 - self.confidence else "not_established"
        if test.direction != expected:
            raise ValueError("Direction must agree with its saved p-value and confidence")
        return self


class RmaResult(ResultItem):
    method: Literal["rma"]
    method_version: Literal[2]
    transform: Literal["none", "log10"]
    missing: Literal["error", "drop_pairs"]
    n_input: int = Field(ge=2)
    n: int = Field(ge=2)
    excluded: list[RmaExclusion]
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
    inference: RmaInference | None
    warnings: list[RmaWarning]
    pairs: list[RmaPair] = Field(min_length=2)
    references: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_records(self):
        retained = [pair.sample_id for pair in self.pairs]
        excluded = [pair.sample_id for pair in self.excluded]
        if self.n != len(retained) or self.n_input != self.n + len(excluded):
            raise ValueError("Counts must match retained and excluded records")
        if len(set(retained + excluded)) != len(retained + excluded):
            raise ValueError("Retained and excluded IDs must be unique and disjoint")
        if self.missing == "error" and excluded:
            raise ValueError("The error missing-value policy cannot contain exclusions")
        if self.correlation == 0 or self.slope == 0:
            raise ValueError("RMA requires nonzero covariance and slope")
        if self.transform == "log10" and any(pair.x_raw <= 0 or pair.y_raw <= 0 for pair in self.pairs):
            raise ValueError("Log-transformed records require positive raw measurements")
        _check_saved_fit(self)
        return self


REFERENCE = "https://palaeo-electronica.org/2001_1/past/pastprog/study1.html"
INFERENCE_REFERENCES = ["https://doi.org/10.1017/S1464793106007007", "https://doi.org/10.1093/biomet/31.1-2.9",
                        "https://doi.org/10.1093/biomet/31.1-2.13"]
INFERENCE_MODEL = "independent pairs from a nonsingular bivariate normal on the analysed scale"
INFERENCE_LIMITATIONS = [
    "The magnitude interval and test concern sd(y)/sd(x) and are exact only for independent pairs from a nonsingular bivariate normal on the analysed scale",
    "Direction is tested separately by the correlation; there is no joint confidence set for the signed slope, and intervals are marginal",
    "No measurement-error model; a p-value is not an effect size",
]
RMA_ASSOCIATION_LIMITATION = "RMA slope magnitude is sd(y)/sd(x), independent of correlation strength; a fitted line does not establish association"


def discover():
    return {"methods": [{
        "id": "rma", "version": 2,
        "description": "Reduced-major-axis regression of labelled paired measurements, with optional exact magnitude inference",
        "definition": "slope = sign(r) * sample_sd(y) / sample_sd(x); intercept = mean(y) - slope * mean(x)",
        "inference": ("Optional: interval |b|/H to |b|*H, H = sqrt(1+B) + sqrt(B), B = (1 - r^2) F(confidence; 1, n-2)/(n-2), "
                      "for sd(y)/sd(x); Pitman-Morgan test of a declared magnitude; correlation t-test of direction"),
        "requirements": ["At least two complete pairs (three for inference)", "Nonzero variance and covariance",
                         "Positive measurements when log10 is requested"],
        "limitations": ["Without inference: no standard errors, confidence intervals or significance tests",
                        "RMA is symmetric regression, not ordinary least squares",
                        RMA_ASSOCIATION_LIMITATION, *INFERENCE_LIMITATIONS,
                        "No inference of sampling independence or causal effects"],
        "references": [REFERENCE, *INFERENCE_REFERENCES], "input_schema": RmaSpec.model_json_schema(),
        "output_schema": RmaResult.model_json_schema(),
    }]}


MIN_REPEATED_BLOCK = 3
MAX_REPORTED_BLOCKS = 20


def repeated_records(records, ids):
    """Return repeated groups, the first 20 maximal block pairs, and the omitted-block count.

    Blocks contain at least three consecutive retained records, with no overlap within each pair.
    Diagnostics only: recurring runs warrant checking the source for duplicated data entry."""
    positions = defaultdict(list)
    for index, record in enumerate(records):
        positions[record].append(index)
    groups = [[ids[i] for i in where] for where in positions.values() if len(where) > 1]
    blocks = []
    omitted = 0
    for where in positions.values():
        for a, i in enumerate(where):
            for j in where[a + 1:]:
                if i > 0 and records[i - 1] == records[j - 1]:
                    continue
                length = 0
                while j + length < len(records) and i + length < j and records[i + length] == records[j + length]:
                    length += 1
                if length >= MIN_REPEATED_BLOCK:
                    if len(blocks) < MAX_REPORTED_BLOCKS:
                        blocks.append({"first": ids[i:i + length], "repeat": ids[j:j + length]})
                    else:
                        omitted += 1
    return groups, blocks, omitted


def repeated_warnings(records, ids, what):
    groups, blocks, omitted = repeated_records(records, ids)
    warnings = []
    if groups:
        warnings.append({"code": "repeated_pairs" if what == "pairs" else "identical_samples",
                         "message": f"{len(groups)} distinct {'measurement pairs' if what == 'pairs' else 'count profiles'} "
                                    f"occur in more than one record ({sum(map(len, groups))} records); check for duplicated "
                                    "entries (repeats can also be coincidences of rounding or of small counts)",
                         "details": {"groups": groups}})
    for block in blocks:
        warnings.append({"code": "repeated_block",
                         "message": f"{len(block['first'])} consecutive retained records {block['first'][0]}..{block['first'][-1]} "
                                    f"recur exactly as {block['repeat'][0]}..{block['repeat'][-1]}; "
                                    "check the source for a duplicated data-entry block",
                         "details": block})
    if omitted:
        warnings[-1]["message"] += f"; {omitted} additional block pairs omitted (first {len(blocks)} reported)"
        warnings[-1]["details"]["omitted_blocks"] = omitted
        warnings[-1]["details"]["reported_blocks"] = len(blocks)
    return warnings


def rma_regression(x, y, *, sample_ids=None, transform, missing, inference=None):
    """Fit RMA, retaining pair identities and declared exclusions.

    Missing values in the native API are None. NaN and infinity are invalid;
    the PAST reader maps its explicit '.' marker to None.
    """
    if transform not in {"none", "log10"} or missing not in {"error", "drop_pairs"}:
        raise AnalysisError("invalid_option", "Declare transform and missing policies explicitly")
    x, y = list(x), list(y)
    ids = list(sample_ids) if sample_ids is not None else [str(i + 1) for i in range(len(x))]
    if len(x) != len(y) or len(x) != len(ids):
        raise AnalysisError("pair_alignment", "x, y and sample IDs must have equal lengths")
    if any(not isinstance(item, str) or not item.strip() for item in ids):
        raise AnalysisError("invalid_sample_id", "Sample IDs must be nonempty strings")
    duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise AnalysisError("duplicate_sample_id", "Sample IDs must be unique", sample_ids=duplicates)
    used, excluded = [], []
    for sample_id, xv, yv in zip(ids, x, y, strict=True):
        for column, value in (("x", xv), ("y", yv)):
            if value is not None:
                try:
                    valid = (not isinstance(value, (bool, np.bool_)) and isinstance(value, Real)
                             and np.isfinite(float(value)))
                except (TypeError, ValueError, OverflowError):
                    valid = False
                if not valid:
                    raise AnalysisError("invalid_numeric", "Measurements must be finite real numbers within float64 range or declared missing",
                                        sample_id=sample_id, column=column)
        if xv is None or yv is None:
            excluded.append({"sample_id": sample_id, "reason": "declared_missing_pair",
                             "columns": [name for name, value in (("x", xv), ("y", yv)) if value is None]})
            continue
        if transform == "log10" and (xv <= 0 or yv <= 0):
            raise AnalysisError("nonpositive_log", "log10 requires positive measurements", sample_id=sample_id)
        used.append({"sample_id": sample_id, "x_raw": float(xv), "y_raw": float(yv)})
    if excluded and missing == "error":
        raise AnalysisError("missing_pairs", "Declared missing measurements require an explicit drop_pairs policy",
                            excluded=excluded)
    if len(used) < 2:
        raise AnalysisError("insufficient_pairs", "At least two complete pairs are required", n=len(used))
    xx = np.asarray([row["x_raw"] for row in used], dtype=np.float64)
    yy = np.asarray([row["y_raw"] for row in used], dtype=np.float64)
    if transform == "log10":
        xx, yy = np.log10(xx), np.log10(yy)
    fit = fit_rma(xx, yy)
    settings = None if inference is None else (
        inference if isinstance(inference, RmaInferenceSpec) else RmaInferenceSpec.model_validate(inference))
    inferred = None if settings is None else rma_inference(xx, yy, fit, settings.confidence, settings.null_magnitude)
    r = fit["correlation"]
    for row, xv, yv, residual in zip(used, xx, yy, fit["residuals"], strict=True):
        row.update(x=float(xv), y=float(yv), residual=float(residual))
    warnings = [{"code": "small_computed_correlation",
                 "message": "Computed |r| is below 1e-8; this numerical diagnostic is not a statistical test of association"}] if abs(r) < 1e-8 else []
    if len(used) == 2:
        warnings.append({"code": "two_pairs", "message": "Two pairs determine a line; residual diagnostics cannot assess its adequacy"})
    warnings += repeated_warnings([(row["x_raw"], row["y_raw"]) for row in used], [row["sample_id"] for row in used],
                                  "pairs")
    summary = {key: fit[key] for key in SUMMARY_KEYS}
    return RmaResult.model_validate({"method": "rma", "method_version": 2, "transform": transform,
            "missing": missing, "n_input": len(ids), "n": len(used), "excluded": excluded, **summary,
            "x_raw_range": _range(row["x_raw"] for row in used), "y_raw_range": _range(row["y_raw"] for row in used),
            "inference": inferred, "warnings": warnings, "pairs": used,
            "references": [REFERENCE] + (INFERENCE_REFERENCES if inferred else []),
            "limitations": rma_limitations(inferred is not None)}).model_dump(mode="json")


SUMMARY_KEYS = ("mean_x", "mean_y", "sd_x", "sd_y", "correlation", "slope", "intercept", "vertical_residual_rmse")


def rma_limitations(inferred):
    return ([RMA_ASSOCIATION_LIMITATION, "Vertical residuals are diagnostics, not an OLS fitting objective"] +
            (INFERENCE_LIMITATIONS if inferred else ["Descriptive fit only; no inferential uncertainty or hypothesis test"]))


def _range(values):
    values = list(values)
    return [min(values), max(values)]


def fit_rma(xx, yy):
    """Moments, RMA line and vertical residuals of analysed float64 pairs."""
    try:
        with np.errstate(all="raise"):
            mean_x, mean_y = float(xx.mean()), float(yy.mean())
            sd_x, sd_y = float(xx.std(ddof=1)), float(yy.std(ddof=1))
            if sd_x == 0 or sd_y == 0:
                raise AnalysisError("zero_variance", "RMA requires variation in both measurements")
            r = float(np.mean(((xx - mean_x) / sd_x) * ((yy - mean_y) / sd_y)) * len(xx) / (len(xx) - 1))
            if r == 0:
                raise AnalysisError("zero_covariance", "RMA slope direction is undefined at zero covariance")
            r = float(np.clip(r, -1.0, 1.0))
            slope = float(np.copysign(sd_y / sd_x, r))
            intercept = float(mean_y - slope * mean_x)
            residuals = yy - (intercept + slope * xx)
            rmse = float(np.sqrt(np.mean(residuals ** 2)))
    except (FloatingPointError, OverflowError) as exc:
        raise AnalysisError("numerical_range", "Numerical range exceeded; inspect measurement scales") from exc
    values = [mean_x, mean_y, sd_x, sd_y, r, slope, intercept, rmse]
    if not np.isfinite(values).all():
        raise AnalysisError("numerical_range", "Computed summaries are not finite")
    return dict(zip(SUMMARY_KEYS, values), residuals=residuals)


def _log10_t_two_sided(t, df):
    """log10 of the two-sided t tail I_z(df/2, 1/2), z = df/(df + t^2), by the series DLMF 8.17.22 in log space."""
    a, b = df / 2, 0.5
    log_z = math.log(df) - 2 * math.log(abs(t)) - math.log1p(df / (t * t))
    total = 1.0
    for k in range(MAX_SERIES_TERMS):
        term = math.exp(betaln(a + 1, k + 1) - betaln(a + b, k + 1) + (k + 1) * log_z)
        total += term
        if term < 1e-17 * total:
            break
    else:
        raise AnalysisError("numerical_range", "The tail-probability series did not converge", t=t, df=df)
    log_one_minus_z = math.log(t * t / df) + log_z
    return (a * log_z + b * log_one_minus_z - math.log(a) - betaln(a, b) + math.log(total)) / math.log(10)


MAX_SERIES_TERMS = 10_000


def _t_test(t, df):
    p = float(min(1.0, 2 * t_distribution.sf(abs(t), df)))
    if p > 0:
        return {"t": t, "df": df, "p_value": p, "p_value_underflow": False, "log10_p_value": None}
    return {"t": t, "df": df, "p_value": 0.0, "p_value_underflow": True, "log10_p_value": _log10_t_two_sided(t, df)}


def rma_inference(xx, yy, fit, confidence, null_magnitude):
    """Exact interval and Pitman-Morgan test for sd(y)/sd(x), and the correlation test of direction.

    Both are exact for independent pairs from a nonsingular bivariate normal on the analysed scale."""
    n = len(xx)
    if n < 3:
        raise AnalysisError("inference_unavailable", "Inference needs at least three complete pairs", n=n)
    df, r, magnitude = n - 2, fit["correlation"], abs(fit["slope"])
    try:
        with np.errstate(all="raise"):
            if not 1 - r * r > 0:
                raise AnalysisError("degenerate_inference", "Perfect correlation leaves no sampling variation to infer from")
            b_term = (1 - r * r) * float(f_distribution.ppf(confidence, 1, df)) / df
            h = math.sqrt(1 + b_term) + math.sqrt(b_term)
            interval = [magnitude / h, magnitude * h]
            zx = (xx - fit["mean_x"]) / fit["sd_x"]
            zy = (yy - fit["mean_y"]) / fit["sd_y"]
            log_ratio = math.log(null_magnitude) + math.log(fit["sd_x"]) - math.log(fit["sd_y"])
            u, v = (zy, math.exp(log_ratio) * zx) if log_ratio <= 0 else (math.exp(-log_ratio) * zy, zx)
            var_u, var_v, cov_uv = float(np.mean(u * u)), float(np.mean(v * v)), float(np.mean(u * v))
            r_rf = (var_u - var_v) / math.sqrt((var_u + var_v) ** 2 - 4 * cov_uv * cov_uv)
            if not 1 - r_rf * r_rf > 0:
                raise AnalysisError("degenerate_inference", "The magnitude test statistic is degenerate at this null magnitude")
            t_rf = r_rf * math.sqrt(df) / math.sqrt(1 - r_rf * r_rf)
            t_r = r * math.sqrt(df) / math.sqrt(1 - r * r)
    except (FloatingPointError, OverflowError, ValueError, ZeroDivisionError) as exc:
        raise AnalysisError("numerical_range", "Inference exceeded floating-point range") from exc
    if not (np.isfinite(interval + [r_rf, t_rf, t_r]).all() and interval[0] > 0):
        raise AnalysisError("numerical_range", "Interval bounds or test statistics are not representable", interval=interval)
    direction = _t_test(t_r, df)
    established = direction["p_value"] < 1 - confidence
    return {"confidence": confidence, "magnitude_estimate": magnitude, "magnitude_interval": interval,
            "null_magnitude": float(null_magnitude), "magnitude_test": {"r_rf": r_rf, **_t_test(t_rf, df)},
            "direction_test": {"r": r, **direction,
                               "direction": ("positive" if r > 0 else "negative") if established else "not_established"},
            "model": INFERENCE_MODEL, "scope": INFERENCE_SCOPE}


def _same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[key], b[key]) for key in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, (int, float)) and not isinstance(b, bool):
        return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
    return type(a) is type(b) and a == b


def _check_saved_fit(result):
    """Recompute the line, residuals, ranges and inference from the saved pairs."""
    raw_x = np.asarray([pair.x_raw for pair in result.pairs])
    raw_y = np.asarray([pair.y_raw for pair in result.pairs])
    xx = np.asarray([pair.x for pair in result.pairs])
    yy = np.asarray([pair.y for pair in result.pairs])
    expected = (np.log10(raw_x), np.log10(raw_y)) if result.transform == "log10" else (raw_x, raw_y)
    if not (np.allclose(xx, expected[0], rtol=1e-12, atol=0) and np.allclose(yy, expected[1], rtol=1e-12, atol=0)):
        raise ValueError("Analysed pairs differ from the raw pairs under the declared transform")
    fit = fit_rma(xx, yy)
    saved = {key: getattr(result, key) for key in SUMMARY_KEYS}
    if not _same(saved, {key: fit[key] for key in SUMMARY_KEYS}) or not _same(
            [pair.residual for pair in result.pairs], [float(value) for value in fit["residuals"]]):
        raise ValueError("Saved RMA summaries or residuals do not recompute from the saved pairs")
    if result.x_raw_range != _range(raw_x.tolist()) or result.y_raw_range != _range(raw_y.tolist()):
        raise ValueError("Saved ranges differ from the retained raw values")
    if result.inference is not None:
        recomputed = rma_inference(xx, yy, fit, result.inference.confidence, result.inference.null_magnitude)
        if not _same(result.inference.model_dump(mode="json"), recomputed):
            raise ValueError("Saved inference does not recompute from the saved pairs")
        for name in ("magnitude_test", "direction_test"):
            if not math.isclose(getattr(result.inference, name).p_value, recomputed[name]["p_value"],
                                rel_tol=1e-10, abs_tol=0):
                raise ValueError("Saved p-value does not recompute from the saved pairs")
    if result.limitations != rma_limitations(result.inference is not None):
        raise ValueError("Limitations do not match the inference record")


def resolve_columns(names, x, y):
    """Indices of the x and y columns: the exact label, else the single label equal to it after stripping padding."""
    selected, absent = [], []
    for name in (x, y):
        matches = [i for i, label in enumerate(names) if label == name]
        if not matches and name == name.strip():
            matches = [i for i, label in enumerate(names) if label.strip() == name]
        if len(matches) > 1:
            raise AnalysisError("ambiguous_column", "Selected column matches multiple whitespace-padded labels", column=name)
        if not matches:
            absent.append(name)
        else:
            selected.append(matches[0])
    if absent:
        raise AnalysisError("unknown_column", "Selected columns do not exist", columns=absent, available=names)
    if selected[0] == selected[1]:
        raise AnalysisError("same_column", "x and y must select different columns")
    return selected


def past_header(data: bytes):
    """Column names and raw token rows of a classic PAST measurement table."""
    try:
        lines = [line for line in data.decode("utf-8-sig").splitlines() if line.strip()]
    except UnicodeDecodeError as exc:
        raise AnalysisError("invalid_encoding", "The supported PAST table must be UTF-8 text") from exc
    tabbed = bool(lines) and "\t" in lines[0]
    rows = [line.split("\t") if tabbed else line.split() for line in lines]
    if len(rows) < 2 or rows[0][0] != ".":
        raise AnalysisError("invalid_past_header", "Expected classic PAST header beginning with '.'")
    names = rows[0][1:]
    if len(names) != len(set(names)):
        raise AnalysisError("duplicate_column_id", "Column labels must be unique")
    return names, rows[1:]


def past_values(names, rows):
    """Row IDs and parsed values (None for the explicit '.' missing marker) of every column."""
    ids, values = [], []
    for line_number, row in enumerate(rows, 2):
        if len(row) > len(names) + 1 and all(not cell.strip() for cell in row[len(names) + 1:]):
            row = row[:len(names) + 1]
        if len(row) != len(names) + 1:
            raise AnalysisError("row_width", "Row width differs from the header", line=line_number)
        ids.append(row[0])
        parsed = []
        for column, token in zip(names, row[1:], strict=True):
            try:
                value = None if token == "." else float(token)
            except ValueError as exc:
                raise AnalysisError("invalid_numeric", "Invalid measurement token", sample_id=row[0], column=column) from exc
            if value is not None and not np.isfinite(value):
                raise AnalysisError("invalid_numeric", "Nonfinite measurement token", sample_id=row[0], column=column)
            parsed.append(value)
        values.append(parsed)
    return ids, values


def padded_warnings(names, selectors):
    """Warnings for selectors that matched a whitespace-padded header label; selectors are (axis, name, index)."""
    return [{"code": "padded_column_label",
             "message": f"{axis} selector {name!r} uses PAST header label {names[index]!r} at data column {index + 1}"}
            for axis, name, index in selectors if name != names[index]]


def load_past(data: bytes, spec: RmaSpec):
    if spec.x == spec.y:
        raise AnalysisError("same_column", "x and y must select different columns")
    names, rows = past_header(data)
    selected = resolve_columns(names, spec.x, spec.y)
    ids, values = past_values(names, rows)
    x, y = [row[selected[0]] for row in values], [row[selected[1]] for row in values]
    return x, y, ids, padded_warnings(names, zip(("x", "y"), (spec.x, spec.y), selected, strict=True))


def calculate(spec: RmaSpec, data: bytes):
    x, y, ids, selection_warnings = load_past(data, spec)
    result = rma_regression(x, y, sample_ids=ids, transform=spec.transform, missing=spec.missing,
                            inference=spec.inference)
    result["warnings"].extend(selection_warnings)
    return result


def validate(spec: RmaSpec | dict):
    spec = spec if isinstance(spec, RmaSpec) else RmaSpec.model_validate(spec)
    try:
        data = spec.input.read_bytes()
    except OSError as exc:
        raise AnalysisError("input_unreadable", "Cannot read input file", path=str(spec.input), reason=str(exc)) from exc
    result = calculate(spec, data)
    return {"status": "valid", "n": result["n"], "n_input": result["n_input"],
            "excluded": result["excluded"], "warnings": result["warnings"],
            "scope": "Data and numerical requirements checked; scientific sampling assumptions are not established"}
