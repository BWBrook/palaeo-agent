"""Stratigraphically constrained incremental sum-of-squares clustering (CONISS) with broken-stick retention.

Every clustering decision is made in exact rational arithmetic on coordinates that are the nearest
binary64 values to the exact proportions (or their square roots); every reported number is the nearest
binary64 value to its exact quantity. See docs/sprint-14-contract.md.
"""

from fractions import Fraction
import math
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from .community import FORMAT_HELP, VALUE_TYPE_HELP, _prepare_counts, _read_inputs, _table_warnings, check_delimiter, value_keys
from .core import AnalysisError, ResultItem


MAX_SAMPLES = 2_000
MAX_CELLS = 500_000
NORMAL_MIN = Fraction(1, 2**1022)
SMALL_MARGIN = Fraction(1, 10**9)
RETENTION_RULE = "broken_stick_consecutive_prefix"
NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
REFERENCES = [
    "https://doi.org/10.1016/0098-3004(87)90022-7",
    "https://doi.org/10.1111/j.1469-8137.1996.tb04521.x",
    "https://doi.org/10.32614/CRAN.package.rioja",
]
LIMITATIONS = [
    "Greedy agglomerative hierarchy under the adjacency constraint; not the optimal k-zone segmentation for every k",
    "Broken-stick retention is a heuristic comparison, not a significance test; no p-values or boundary intervals",
    "Equal sample weights; count sampling error is not propagated",
    "Adjacency is table order; gaps between positions carry no weight",
]


def nearest_double(numerator: int, denominator: int, *, root: bool = False) -> float:
    """The binary64 value nearest to a/b, or to sqrt(a/b), ties to even; a >= 0, b > 0 integers.

    Pure integer work with a fixed number of operations: the exponent is placed from bit lengths, the
    significand is an integer quotient (or integer square root), and one exact comparison rounds it.
    """
    if numerator < 0 or denominator <= 0:
        raise ValueError("nearest_double needs a nonnegative numerator and positive denominator")
    if numerator == 0:
        return 0.0
    shift = numerator.bit_length() - denominator.bit_length()
    exponent = (shift // 2 if root else shift) - 53
    for _ in range(4):
        exponent = max(exponent, -1074)
        scale = -2 * exponent if root else -exponent
        a, b = (numerator << scale, denominator) if scale >= 0 else (numerator, denominator << -scale)
        significand = math.isqrt(a // b) if root else a // b
        if significand >= 2**53:
            exponent += 1
        elif significand < 2**52 and exponent > -1074:
            exponent -= 1
        else:
            break
    else:
        raise AssertionError("exponent placement did not converge")
    left, right = (4 * a, (2 * significand + 1) ** 2 * b) if root else (2 * a, (2 * significand + 1) * b)
    if left > right or (left == right and significand % 2):
        significand += 1
    try:
        return math.ldexp(significand, exponent)
    except OverflowError as exc:
        raise AnalysisError("numerical_range", "A reported quantity exceeds the binary64 range") from exc


def _double(value: Fraction) -> float:
    return nearest_double(value.numerator, value.denominator)


class ConissSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["coniss"]
    input: Path
    metadata: Path
    position_column: str = Field(min_length=1, pattern=r"\S",
                                 description="Metadata column of finite numbers strictly increasing in table order (depth or sequence index)")
    format: Literal["past", "delimited"] = Field(description=FORMAT_HELP)
    delimiter: Literal["tab", "comma"] | None = Field(default=None, description="Required for format 'delimited'")
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    value_type: Literal["count", "abundance"] = Field(description=VALUE_TYPE_HELP)
    transform: Literal["relative_abundance", "hellinger"]
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]

    @model_validator(mode="after")
    def supported_delimiter(self):
        check_delimiter(self)
        return self


class ConissWarning(ResultItem):
    code: Literal["near_duplicate_labels", "identical_samples", "repeated_block", "small_margin_merge",
                  "small_margin_retention", "zero_dispersion"]
    message: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)


class MergeRecord(ResultItem):
    step: int = Field(ge=1)
    boundary: int = Field(ge=1)
    left_first_id: str
    left_last_id: str
    left_size: int = Field(ge=1)
    right_first_id: str
    right_last_id: str
    right_size: int = Field(ge=1)
    cost: FiniteFloat = Field(ge=0)
    runner_up_cost: FiniteFloat | None = Field(ge=0)
    cumulative: FiniteFloat = Field(ge=0)


class BoundaryRecord(ResultItem):
    boundary: int = Field(ge=1)
    left_id: str
    right_id: str
    left_position: FiniteFloat
    right_position: FiniteFloat
    merge_step: int = Field(ge=1)
    split_rank: int = Field(ge=1)


class BrokenStickRecord(ResultItem):
    rank: int = Field(ge=1)
    zones: int = Field(ge=2)
    gain: FiniteFloat = Field(ge=0)
    expected: FiniteFloat = Field(ge=0)
    exceeds: bool


class RetentionRecord(ResultItem):
    rule: Literal["broken_stick_consecutive_prefix"]
    selected_zones: int = Field(ge=1)
    stopped_at_rank: int | None = Field(ge=1)
    later_exceedances: list[int]


class ZoneRecord(ResultItem):
    label: int = Field(ge=1)
    first_id: str
    last_id: str
    first_position: FiniteFloat
    last_position: FiniteFloat
    size: int = Field(ge=1)
    within_ss: FiniteFloat = Field(ge=0)


class ConissResult(ResultItem):
    method: Literal["coniss"]
    method_version: Literal[1]
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    value_type: Literal["count", "abundance"]
    transform: Literal["relative_abundance", "hellinger"]
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]
    position_column: str = Field(min_length=1, pattern=r"\S")
    n: int = Field(ge=3, le=MAX_SAMPLES)
    n_input: int = Field(ge=3)
    n_taxa: int = Field(ge=1)
    input_sample_ids: list[str]
    sample_ids: list[str]
    taxon_ids: list[str]
    retained_counts: list[list[FiniteFloat]] | None = Field(default=None, description="Count input only")
    retained_values: list[list[FiniteFloat]] | None = Field(default=None, description="Abundance input only")
    metadata: list[dict[str, str]]
    excluded: list[dict]
    positions: list[FiniteFloat]
    merges: list[MergeRecord]
    boundaries: list[BoundaryRecord]
    total_dispersion: FiniteFloat = Field(ge=0)
    broken_stick: list[BrokenStickRecord]
    retention: RetentionRecord
    zones: list[ZoneRecord]
    warnings: list[ConissWarning]
    references: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_records(self):
        try:
            _validate_saved_result(self)
        except AnalysisError as exc:
            raise ValueError(f"{exc.code}: {exc}") from exc
        return self


def _positions(metadata, column, sample_ids):
    if metadata is None or [row.get("sample_id") for row in metadata] != sample_ids:
        raise AnalysisError("metadata_alignment", "CONISS requires metadata joined by exact sample ID")
    absent = [row["sample_id"] for row in metadata if column not in row]
    if absent:
        raise AnalysisError("missing_position_column", "Position column is missing", position_column=column,
                            sample_ids=absent)
    positions = []
    for row in metadata:
        token = row[column].strip()
        value = float(token) if NUMBER.fullmatch(token) else math.nan
        if not math.isfinite(value):
            raise AnalysisError("order_mismatch", "Positions must be finite decimal numbers", position_column=column,
                                sample_id=row["sample_id"], value=row[column])
        positions.append(value)
    for i in range(1, len(positions)):
        if not positions[i] > positions[i - 1]:
            raise AnalysisError("order_mismatch", "Positions must strictly increase in table order",
                                position_column=column, sample_ids=[sample_ids[i - 1], sample_ids[i]],
                                positions=[positions[i - 1], positions[i]])
    return positions


def _check_size(n, n_taxa):
    if n < 3:
        raise AnalysisError("insufficient_samples", "CONISS needs at least three retained samples", retained=n)
    if n > MAX_SAMPLES or n * n_taxa > MAX_CELLS:
        raise AnalysisError("resource_limit", "Table exceeds the exact-arithmetic budget", samples=n,
                            cells=n * n_taxa, limit_samples=MAX_SAMPLES, limit_cells=MAX_CELLS)


def coordinates(values, transform, sample_ids, taxon_ids):
    """Nearest doubles to the exact row proportions (or their square roots); refuses non-normal positives."""
    rows = []
    for sample, row in zip(sample_ids, values, strict=True):
        exact = [Fraction(value) for value in row]
        total = sum(exact)
        output = []
        for taxon, value in zip(taxon_ids, exact, strict=True):
            proportion = value / total
            coordinate = nearest_double(proportion.numerator, proportion.denominator, root=transform == "hellinger")
            if proportion > 0 and coordinate < 2.0**-1022:
                raise AnalysisError("numerical_range", "A positive cell gives a coordinate below the smallest normal double",
                                    sample_id=sample, taxon_id=taxon)
            output.append(coordinate)
        rows.append(output)
    return rows


def integer_rows(rows):
    """Coordinates as integers on one common power-of-two scale: x = integer / 2**power exactly."""
    ratios = [[value.as_integer_ratio() for value in row] for row in rows]
    power = max((denominator.bit_length() - 1 for row in ratios for _, denominator in row), default=0)
    return [[numerator << (power - denominator.bit_length() + 1) for numerator, denominator in row]
            for row in ratios], power


def _hierarchy(integers, power):
    """Greedy adjacent-only Ward merges on exact integer sums. Costs are exact Fractions."""
    sums = [list(row) for row in integers]
    scale = Fraction(1, 4**power)
    n = len(sums)
    size, first, last = [1] * n, list(range(n)), list(range(n))
    clusters = list(range(n))

    def cost(a, b):
        na, nb = size[a], size[b]
        return Fraction(sum((nb * x - na * y) ** 2 for x, y in zip(sums[a], sums[b], strict=True)), na * nb * (na + nb))

    costs = [cost(i, i + 1) for i in range(n - 1)]
    merges, cumulative = [], Fraction(0)
    while len(clusters) > 1:
        j = min(range(len(costs)), key=lambda k: (costs[k], k))
        runner = min((c for k, c in enumerate(costs) if k != j), default=None)
        a, b = clusters[j], clusters[j + 1]
        c = costs[j] * scale
        cumulative += c
        merges.append({"boundary": last[a] + 1, "left": (first[a], last[a], size[a]), "right": (first[b], last[b], size[b]),
                       "cost": c, "runner_up": None if runner is None else runner * scale, "cumulative": cumulative})
        sums[a] = [x + y for x, y in zip(sums[a], sums[b], strict=True)]
        size[a] += size[b]
        last[a] = last[b]
        del clusters[j + 1], costs[j]
        if j > 0:
            costs[j - 1] = cost(clusters[j - 1], a)
        if j < len(clusters) - 1:
            costs[j] = cost(a, clusters[j + 1])
    return merges, scale


def zone_ss(members, scale):
    """Exact within-zone sum of squares about the zone centroid."""
    size = len(members)
    square = sum(value * value for row in members for value in row)
    return Fraction(size * square - sum(sum(column) ** 2 for column in zip(*members)), size) * scale


def broken_stick(merges):
    m = len(merges)
    total = merges[-1]["cumulative"]
    harmonic, suffix = [Fraction(0)] * (m + 2), Fraction(0)
    for j in range(m, 0, -1):
        suffix += Fraction(1, j)
        harmonic[j] = suffix
    records = []
    for r in range(1, m + 1):
        gain, expected = merges[m - r]["cost"], total / m * harmonic[r]
        records.append({"rank": r, "zones": r + 1, "gain": gain, "expected": expected, "exceeds": gain > expected})
    return records


def retention(records):
    stopped = next((record["rank"] for record in records if not record["exceeds"]), None)
    passing = len(records) if stopped is None else stopped - 1
    later = [] if stopped is None else [record["rank"] for record in records[stopped:] if record["exceeds"]]
    return {"rule": RETENTION_RULE, "selected_zones": 1 + passing, "stopped_at_rank": stopped, "later_exceedances": later}


def zonation(values, *, transform, sample_ids, taxon_ids, positions):
    """The complete CONISS record from validated values and checked positions."""
    rows = coordinates(values, transform, sample_ids, taxon_ids)
    n = len(rows)
    integers, power = integer_rows(rows)
    merges, scale = _hierarchy(integers, power)
    m = len(merges)
    stick = broken_stick(merges)
    kept = retention(stick)
    k = kept["selected_zones"]
    step_of = {record["boundary"]: step for step, record in enumerate(merges, start=1)}
    boundaries = [{"boundary": b, "left_id": sample_ids[b - 1], "right_id": sample_ids[b],
                   "left_position": positions[b - 1], "right_position": positions[b],
                   "merge_step": step_of[b], "split_rank": m - step_of[b] + 1} for b in range(1, n)]
    cuts = [record["boundary"] for record in boundaries if record["split_rank"] <= k - 1]
    edges = [0, *cuts, n]
    zones = []
    for label, (start, stop) in enumerate(zip(edges, edges[1:]), start=1):
        zones.append({"label": label, "first_id": sample_ids[start], "last_id": sample_ids[stop - 1],
                      "first_position": positions[start], "last_position": positions[stop - 1], "size": stop - start,
                      "within_ss": zone_ss(integers[start:stop], scale)})
    reported = ([record["cost"] for record in merges] + [record["runner_up"] for record in merges if record["runner_up"] is not None]
                + [record["cumulative"] for record in merges] + [record["expected"] for record in stick]
                + [zone["within_ss"] for zone in zones])
    tiny = [value for value in reported if 0 < value < NORMAL_MIN]
    if tiny:
        raise AnalysisError("numerical_range", "A positive reported quantity is below the smallest normal double",
                            count=len(tiny))
    warnings = []
    close = [{"step": step, "exact_tie": record["runner_up"] == record["cost"]}
             for step, record in enumerate(merges, start=1)
             if record["runner_up"] is not None and record["runner_up"] - record["cost"] <= SMALL_MARGIN * record["runner_up"]]
    if close:
        warnings.append({"code": "small_margin_merge",
                         "message": "Merge choices within 1e-9 relative of the runner-up; exact for these coordinates, but a tiny data change could alter them",
                         "details": {"steps": close}})
    checked = stick if kept["stopped_at_rank"] is None else stick[:kept["stopped_at_rank"]]
    marginal = [record["rank"] for record in checked
                if abs(record["gain"] - record["expected"]) <= SMALL_MARGIN * record["expected"]]
    if marginal:
        warnings.append({"code": "small_margin_retention",
                         "message": "Broken-stick comparisons within 1e-9 relative of the expectation; exact for these coordinates, but a tiny data change could alter the retained zones",
                         "details": {"ranks": marginal}})
    if merges[-1]["cumulative"] == 0:
        warnings.append({"code": "zero_dispersion", "message": "All coordinates are identical; one zone is kept", "details": {}})
    ids = sample_ids
    return {
        "positions": positions,
        "merges": [{"step": step, "boundary": record["boundary"],
                    "left_first_id": ids[record["left"][0]], "left_last_id": ids[record["left"][1]], "left_size": record["left"][2],
                    "right_first_id": ids[record["right"][0]], "right_last_id": ids[record["right"][1]], "right_size": record["right"][2],
                    "cost": _double(record["cost"]),
                    "runner_up_cost": None if record["runner_up"] is None else _double(record["runner_up"]),
                    "cumulative": _double(record["cumulative"])}
                   for step, record in enumerate(merges, start=1)],
        "boundaries": boundaries,
        "total_dispersion": _double(merges[-1]["cumulative"]),
        "broken_stick": [{**record, "gain": _double(record["gain"]), "expected": _double(record["expected"])} for record in stick],
        "retention": kept,
        "zones": [{**zone, "within_ss": _double(zone["within_ss"])} for zone in zones],
        "warnings": warnings,
    }


def _prepare(spec, data, metadata):
    spec = spec if isinstance(spec, ConissSpec) else ConissSpec.model_validate(spec)
    matrix, samples, taxa, rows = _read_inputs(spec, data, metadata)
    prepared = _prepare_counts(matrix, sample_ids=samples, taxon_ids=taxa, empty_samples=spec.empty_samples,
                               metadata=rows, value_type=spec.value_type)
    _check_size(len(prepared["sample_ids"]), len(taxa))
    positions = _positions(prepared["metadata"], spec.position_column, prepared["sample_ids"])
    return spec, prepared, positions


def validate_coniss(spec, data, metadata):
    spec, prepared, _ = _prepare(spec, data, metadata)
    return {"status": "valid", "n": len(prepared["sample_ids"]), "n_input": len(prepared["input_sample_ids"]),
            "n_taxa": len(prepared["taxon_ids"]), "excluded": prepared["excluded"], "warnings": prepared["warnings"],
            "scope": "Input, value type, size and strictly increasing positions checked; the zonation itself is descriptive"}


def calculate_coniss(spec, data, metadata):
    spec, prepared, positions = _prepare(spec, data, metadata)
    values = prepared["counts"].tolist()
    record = zonation(values, transform=spec.transform, sample_ids=prepared["sample_ids"],
                      taxon_ids=prepared["taxon_ids"], positions=positions)
    result = {"method": "coniss", "method_version": 1, "orientation": spec.orientation, "value_type": spec.value_type,
              "transform": spec.transform, "missing": "error", "empty_samples": spec.empty_samples,
              "position_column": spec.position_column, "n": len(prepared["sample_ids"]),
              "n_input": len(prepared["input_sample_ids"]), "n_taxa": len(prepared["taxon_ids"]),
              "input_sample_ids": prepared["input_sample_ids"], "sample_ids": prepared["sample_ids"],
              "taxon_ids": prepared["taxon_ids"], value_keys(spec.value_type)[0]: values,
              "metadata": prepared["metadata"], "excluded": prepared["excluded"],
              **{key: value for key, value in record.items() if key != "warnings"},
              "warnings": prepared["warnings"] + record["warnings"],
              "references": REFERENCES, "limitations": LIMITATIONS}
    dumped = ConissResult.model_validate(result).model_dump(mode="json")
    dumped.pop(value_keys("abundance" if spec.value_type == "count" else "count")[0])
    return dumped


def _validate_saved_result(result):
    samples, taxa = result.sample_ids, result.taxon_ids
    for ids in (samples, taxa, result.input_sample_ids):
        if any(not value.strip() for value in ids) or len(set(ids)) != len(ids):
            raise ValueError("IDs must be nonblank and unique")
    excluded = [item.get("sample_id") for item in result.excluded]
    if (any(not isinstance(s, str) for s in excluded) or len(set(excluded)) != len(excluded)
            or not set(excluded) <= set(result.input_sample_ids)
            or result.n != len(samples) or result.n_input != len(result.input_sample_ids)
            or result.n_input != result.n + len(excluded) or result.n_taxa != len(taxa)
            or [s for s in result.input_sample_ids if s not in set(excluded)] != samples
            or result.excluded != [{"sample_id": s, "reason": "empty_sample"} for s in excluded]
            or (excluded and result.empty_samples != "drop")):
        raise ValueError("Sample counts, IDs and exclusions disagree")
    matrix_key = value_keys(result.value_type)[0]
    other_key = value_keys("abundance" if result.value_type == "count" else "count")[0]
    values = getattr(result, matrix_key)
    if values is None or getattr(result, other_key) is not None:
        raise ValueError(f"{result.value_type} results carry {matrix_key} only")
    if len(values) != result.n or any(len(row) != result.n_taxa for row in values):
        raise ValueError("Retained matrix shape disagrees with IDs")
    prepared = _prepare_counts(values, sample_ids=samples, taxon_ids=taxa, empty_samples="error",
                               metadata=result.metadata, value_type=result.value_type)
    _check_size(result.n, result.n_taxa)
    positions = _positions(prepared["metadata"], result.position_column, samples)
    if positions != result.positions:
        raise ValueError("Positions disagree with the aligned metadata column")
    expected = zonation(values, transform=result.transform, sample_ids=samples, taxon_ids=taxa, positions=positions)
    saved = result.model_dump(mode="json")
    table = _table_warnings(result.input_sample_ids, taxa, values, samples)
    if saved["warnings"] != table + expected["warnings"]:
        raise ValueError("Warnings are not exactly the recomputed table and zonation warnings")
    for key, value in expected.items():
        if key == "warnings":
            continue
        if saved[key] != value:
            raise ValueError(f"{key} disagrees with the exact recomputation")
    if result.references != REFERENCES or result.limitations != LIMITATIONS:
        raise ValueError("References or limitations differ from the method's fixed text")
