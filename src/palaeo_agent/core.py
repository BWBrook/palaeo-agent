"""The first supported operation: descriptive reduced-major-axis regression."""

from collections import Counter
from numbers import Real
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


class AnalysisError(Exception):
    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code = code
        self.details = details

    def as_dict(self):
        return {"status": "error", "code": self.code,
                "message": str(self), "details": self.details}


class RmaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["rma"]
    input: Path = Field(description="Classic PAST table; relative to the specification file in the CLI")
    format: Literal["past"]
    x: str = Field(min_length=1, description="Exact predictor column label")
    y: str = Field(min_length=1, description="Exact response column label")
    transform: Literal["none", "log10"]
    missing: Literal["error", "drop_pairs"]


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
    code: Literal["small_computed_correlation", "two_pairs", "padded_column_label"]
    message: str = Field(min_length=1)


class RmaResult(ResultItem):
    method: Literal["rma"]
    method_version: Literal[1]
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
        return self


REFERENCE = "https://palaeo-electronica.org/2001_1/past/pastprog/study1.html"
RMA_ASSOCIATION_LIMITATION = "RMA slope magnitude is sd(y)/sd(x), independent of correlation strength; a fitted line does not establish association"


def discover():
    return {"methods": [{
        "id": "rma", "version": 1,
        "description": "Descriptive reduced-major-axis regression of labelled paired measurements",
        "definition": "slope = sign(r) * sample_sd(y) / sample_sd(x); intercept = mean(y) - slope * mean(x)",
        "requirements": ["At least two complete pairs", "Nonzero variance and covariance",
                         "Positive measurements when log10 is requested"],
        "limitations": ["No standard errors, confidence intervals or significance tests",
                        "RMA is symmetric regression, not ordinary least squares",
                        RMA_ASSOCIATION_LIMITATION,
                        "No inference of sampling independence or causal effects"],
        "references": [REFERENCE], "input_schema": RmaSpec.model_json_schema(),
        "output_schema": RmaResult.model_json_schema(),
    }]}


def rma_regression(x, y, *, sample_ids=None, transform, missing):
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
    for row, xv, yv, residual in zip(used, xx, yy, residuals, strict=True):
        row.update(x=float(xv), y=float(yv), residual=float(residual))
    warnings = [{"code": "small_computed_correlation",
                 "message": "Computed |r| is below 1e-8; this numerical diagnostic is not a statistical test of association"}] if abs(r) < 1e-8 else []
    if len(used) == 2:
        warnings.append({"code": "two_pairs", "message": "Two pairs determine a line; residual diagnostics cannot assess its adequacy"})
    return RmaResult.model_validate({"method": "rma", "method_version": 1, "transform": transform,
            "missing": missing, "n_input": len(ids), "n": len(used),
            "excluded": excluded, "mean_x": mean_x, "mean_y": mean_y,
            "sd_x": sd_x, "sd_y": sd_y, "correlation": r,
            "slope": slope, "intercept": intercept, "vertical_residual_rmse": rmse,
            "warnings": warnings, "pairs": used, "references": [REFERENCE],
            "limitations": ["Descriptive fit only; no inferential uncertainty or hypothesis test",
                            RMA_ASSOCIATION_LIMITATION,
                            "Vertical residuals are diagnostics, not an OLS fitting objective"]}).model_dump(mode="json")


def load_past(data: bytes, spec: RmaSpec):
    if spec.x == spec.y:
        raise AnalysisError("same_column", "x and y must select different columns")
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
    selected = []
    absent = []
    for name in (spec.x, spec.y):
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
    ids, x, y = [], [], []
    for line_number, row in enumerate(rows[1:], 2):
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
        x.append(parsed[selected[0]])
        y.append(parsed[selected[1]])
    selection_warnings = [
        {"code": "padded_column_label",
         "message": f"{axis} selector {name!r} uses PAST header label {names[index]!r} at data column {index + 1}"}
        for axis, name, index in zip(("x", "y"), (spec.x, spec.y), selected, strict=True)
        if name != names[index]
    ]
    return x, y, ids, selection_warnings


def calculate(spec: RmaSpec, data: bytes):
    x, y, ids, selection_warnings = load_past(data, spec)
    result = rma_regression(x, y, sample_ids=ids, transform=spec.transform, missing=spec.missing)
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
