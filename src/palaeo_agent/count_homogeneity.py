"""Conditional counting-error tests for explicitly declared sample pairs."""

import math
from pathlib import Path
from typing import Literal

import numpy as np
import scipy
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator, model_validator
from scipy.special import logsumexp
from scipy.stats import beta, fisher_exact, hypergeom, random_table

from .community import (FORMAT_HELP, MAX_EXACT_COUNT, CommunityExclusion, CommunityWarning,
                        _prepare_counts, _read_inputs, check_delimiter)
from .core import AnalysisError, ResultItem


# Patefield's C recurrence multiplies signed int64 margins before converting to double.
MAX_POOLED_TOTAL = math.isqrt(2**63 - 1)
CHUNK_SIZE = 256
MAX_CHUNK_BYTES = 64 * 1024**2
TIE_RELATIVE_TOLERANCE = float(64 * np.finfo(np.float64).eps)
REFERENCES = [
    "https://doi.org/10.2307/2346669",
    "https://doi.org/10.2307/4615733",
    "https://doi.org/10.1093/biomet/26.4.404",
    "https://doi.org/10.2202/1544-6115.1585",
    "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.random_table.html",
    "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html",
]
LIMITATIONS = [
    "A taxon p-value of 0.0 is float64 underflow of a positive Fisher probability, never probability zero: p_value_underflow marks it and log10_p_value gives the unadjusted value from a log-space tail sum; its Holm value is then also an underflowed positive number.",
    "Independent multinomial counting units with a common probability vector within each collection are assumed; clustering or taphonomic aggregation can make inference anticonservative.",
    "Counting error only: this does not test variation between replicate collections, ecological exchangeability between horizons, cause, time or rate.",
    "Full observed counts are used without rarefaction or rescaling.",
    "Omnibus and taxon tests have separate Holm families; they do not jointly control a single 5% error rate across both families.",
    "Monte Carlo intervals are pointwise 95% intervals for unadjusted conditional tail probabilities, not adjusted p-values or simultaneous intervals; unresolved flags do not establish stability near Holm thresholds.",
    "The Holm envelope applies Holm separately to all lower and all upper tail bounds; it is a sensitivity diagnostic, not a simultaneous interval, an interval for the adjusted plus-one p-value, or a measure of stability across seeds.",
    "Holm-adjusted values depend on the whole declared family: adding, removing or replacing pairs can move a pair across the reporting threshold without any change in its own data or draws.",
    "Zero-count upper limits are marginal, pointwise bounds for supplied taxa observed elsewhere in the prepared input; a zero count is not evidence of absence.",
    "SciPy two-sided Fisher tests sum table probabilities at most the observed probability times (1 + 1e-14); R uses (1 + 1e-7).",
    "Zero-count bounds smaller than the least positive float64 are rounded up to that representable value.",
    "Exact random replay requires the same seed, simulations, input and pair order, chunk policy, and NumPy/SciPy versions.",
]


class CountHomogeneitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["count_homogeneity"]
    input: Path
    format: Literal["past", "delimited"] = Field(description=FORMAT_HELP)
    delimiter: Literal["tab", "comma"] | None = None
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    value_type: Literal["count"]
    metadata: Path | None = None
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]
    pairs: list[list[str]] | Literal["adjacent"] = Field(
        description="Explicit pairs, or 'adjacent': consecutive retained samples in input order")
    extra_pairs: list[list[str]] = Field(default=[], description="Pairs after the adjacent ones; only with 'adjacent'")
    simulations: int = Field(strict=True, ge=999, le=99999)
    seed: int = Field(strict=True, ge=0, le=2**32 - 1)
    confidence: float = Field(default=0.95, strict=True, gt=0, lt=1, allow_inf_nan=False)

    @field_validator("pairs", mode="before")
    @classmethod
    def exact_pairs(cls, pairs):
        if pairs != "adjacent":
            _check_pairs(pairs)
        return pairs

    @field_validator("extra_pairs", mode="before")
    @classmethod
    def exact_extra_pairs(cls, pairs):
        if pairs:
            _check_pairs(pairs)
        return pairs

    @model_validator(mode="after")
    def supported_inputs(self):
        check_delimiter(self)
        if self.extra_pairs and self.pairs != "adjacent":
            raise ValueError("extra_pairs is allowed only with pairs: 'adjacent'")
        return self


def pair_declaration(spec, sample_ids):
    """How the saved pair list was declared, as implied by the specification and retained samples."""
    if spec.pairs != "adjacent":
        return {"mode": "explicit", "n_adjacent": 0, "n_extra": len(spec.pairs)}
    return {"mode": "adjacent", "n_adjacent": len(sample_ids) - 1, "n_extra": len(spec.extra_pairs)}


def resolve_pairs(spec, sample_ids):
    """The complete declared pair list: explicit pairs, or adjacent retained samples then the extras."""
    if spec.pairs != "adjacent":
        return [list(pair) for pair in spec.pairs]
    if len(sample_ids) < 2:
        raise AnalysisError("insufficient_samples", "Adjacent pairs need at least two retained samples")
    adjacent = [[a, b] for a, b in zip(sample_ids, sample_ids[1:])]
    seen = {frozenset(pair) for pair in adjacent}
    repeated = [pair for pair in spec.extra_pairs if frozenset(pair) in seen]
    if repeated:
        raise AnalysisError("duplicate_pair", "Extra pairs repeat adjacent pairs; remove them", pairs=repeated)
    return adjacent + [list(pair) for pair in spec.extra_pairs]


def _check_pairs(pairs):
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("Pairs must be a nonempty list")
    seen = set()
    for pair in pairs:
        if (not isinstance(pair, list) or len(pair) != 2 or
                any(not isinstance(item, str) or not item.strip() for item in pair)):
            raise ValueError("Each pair requires exactly two nonblank string sample IDs")
        identity = frozenset(pair)
        if len(identity) != 2 or identity in seen:
            raise ValueError("Pairs must be distinct, including reversed duplicates, with different sample IDs")
        seen.add(identity)


class MonteCarloRecord(ResultItem):
    simulations: int = Field(ge=999, le=99999)
    count_extreme: int = Field(ge=0)
    p_value: FiniteFloat = Field(gt=0, le=1)
    tail_probability_interval: list[FiniteFloat] = Field(min_length=2, max_length=2)
    confidence: Literal[0.95]
    reporting_alpha: Literal[0.05]
    monte_carlo_unresolved: bool
    unresolved_scope: Literal["unadjusted_tail_only"]
    holm_envelope: list[FiniteFloat] = Field(min_length=2, max_length=2)
    holm_envelope_unresolved: bool
    holm_envelope_scope: Literal["sensitivity_diagnostic"]
    spawn_key: list[int] = Field(min_length=1, max_length=1)


class TaxonTest(ResultItem):
    taxon_id: str = Field(min_length=1)
    counts: list[int] = Field(min_length=2, max_length=2)
    proportion_difference_b_minus_a: FiniteFloat = Field(ge=-1, le=1)
    p_value: FiniteFloat = Field(ge=0, le=1)
    p_value_holm: FiniteFloat = Field(ge=0, le=1)
    p_value_underflow: bool = Field(description="True when the positive Fisher probability underflowed float64 to 0")
    log10_p_value: FiniteFloat | None = Field(
        description="Only when underflowed: log10 of the unadjusted two-sided p, summed in log space")


class PairResult(ResultItem):
    sample_ids: list[str] = Field(min_length=2, max_length=2)
    taxon_ids: list[str] = Field(min_length=2)
    taxa_absent_from_pair: list[str]
    observed_counts: list[list[int]]
    expected_counts: list[list[FiniteFloat]]
    sample_totals: list[int] = Field(min_length=2, max_length=2)
    pooled_taxon_totals: list[int]
    pearson_chi_squared: FiniteFloat = Field(ge=0)
    braycurtis_proportions: FiniteFloat = Field(ge=0, le=1)
    p_value: FiniteFloat = Field(gt=0, le=1)
    p_value_holm: FiniteFloat = Field(gt=0, le=1)
    monte_carlo: MonteCarloRecord
    taxon_tests: list[TaxonTest] = Field(min_length=2)


class ZeroCountLimit(ResultItem):
    sample_id: str = Field(min_length=1)
    n: int = Field(gt=0)
    confidence: FiniteFloat = Field(gt=0, lt=1)
    upper_limit: FiniteFloat = Field(gt=0, lt=1)
    taxon_ids: list[str]
    scope: Literal["pointwise"]


class HolmFamily(ResultItem):
    method: Literal["holm"]
    size: int = Field(ge=1)


class Multiplicity(ResultItem):
    omnibus: HolmFamily
    taxon: HolmFamily
    joint_control: Literal[False]


class RandomizationRecord(ResultItem):
    seed: int = Field(ge=0, le=2**32 - 1)
    simulations: int = Field(ge=999, le=99999)
    bit_generator: Literal["PCG64"]
    sampler: Literal["scipy.stats.random_table"]
    algorithm: Literal["patefield"]
    numpy_version: str = Field(min_length=1, pattern=r"\S")
    scipy_version: str = Field(min_length=1, pattern=r"\S")
    chunk_size: Literal[256]
    max_pooled_total: Literal[3037000499]
    tie_relative_tolerance: FiniteFloat = Field(gt=0)
    stream_policy: Literal["SeedSequence.spawn_declared_pair_order"]


class PairDeclaration(ResultItem):
    mode: Literal["adjacent", "explicit"]
    n_adjacent: int = Field(ge=0)
    n_extra: int = Field(ge=0)


class CountHomogeneityResult(ResultItem):
    method: Literal["count_homogeneity"]
    method_version: Literal[3]
    orientation: Literal["samples_by_taxa", "taxa_by_samples"]
    canonical_orientation: Literal["samples_by_taxa"]
    value_type: Literal["count"]
    missing: Literal["error"]
    empty_samples: Literal["error", "drop"]
    n_input: int = Field(ge=2)
    n: int = Field(ge=2)
    n_taxa: int = Field(ge=2)
    input_sample_ids: list[str]
    sample_ids: list[str]
    taxon_ids: list[str]
    retained_counts: list[list[int]]
    metadata: list[dict[str, str]] | None
    excluded: list[CommunityExclusion]
    warnings: list[CommunityWarning]
    pair_declaration: PairDeclaration
    pairs: list[PairResult] = Field(min_length=1)
    zero_count_limits: list[ZeroCountLimit] = Field(min_length=2)
    confidence: FiniteFloat = Field(gt=0, lt=1)
    multiplicity: Multiplicity
    randomization: RandomizationRecord
    references: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent_records(self):
        try:
            _validate_saved_result(self)
        except AnalysisError as exc:
            raise ValueError(f"{exc.code}: {exc}") from exc
        return self


def _fisher(xa, na, xb, nb):
    """Two-sided Fisher p, an underflow flag, and when underflowed log10 p from a log-space tail sum.

    Same tail as SciPy: tables no more probable than the observed one, with relative tolerance 1e-7."""
    p = float(fisher_exact([[xa, na - xa], [xb, nb - xb]], alternative="two-sided").pvalue)
    if p > 0:
        return p, False, None
    total, column = na + nb, xa + xb
    support = np.arange(max(0, na - (total - column)), min(column, na) + 1)
    masses = hypergeom.logpmf(support, total, column, na)
    observed = float(hypergeom.logpmf(xa, total, column, na))
    return p, True, float(logsumexp(masses[masses <= observed + math.log1p(1e-7)])) / math.log(10)


def _holm(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [0.0] * len(values)
    previous = 0.0
    for rank, index in enumerate(order):
        previous = min(1.0, max(previous, (len(values) - rank) * values[index]))
        adjusted[index] = previous
    return adjusted


def _holm_envelopes(intervals):
    lower = _holm([interval[0] for interval in intervals])
    upper = _holm([interval[1] for interval in intervals])
    return [[lo, hi] for lo, hi in zip(lower, upper, strict=True)]


def _interval(b, simulations):
    lower = 0.0 if b == 0 else float(beta.ppf(0.025, b, simulations - b + 1))
    upper = 1.0 if b == simulations else float(beta.ppf(0.975, b + 1, simulations - b))
    return [lower, upper]


def _pair_data(counts, sample_ids, taxon_ids, pair):
    unknown = [sample for sample in pair if sample not in sample_ids]
    if unknown:
        raise AnalysisError("unknown_pair_sample", "Declared pairs must name retained samples; empty paired samples cannot be dropped", sample_ids=unknown)
    a, b = (counts[sample_ids.index(sample)] for sample in pair)
    totals = [sum(int(value) for value in row) for row in (a, b)]
    if min(totals) <= 0:
        raise AnalysisError("empty_pair_sample", "Every declared pair sample must have a positive count total", sample_ids=pair)
    total = sum(totals)
    if total > MAX_POOLED_TOTAL:
        raise AnalysisError("sampler_count_range", "Pooled pair total exceeds the safe signed-int64 product bound of the Patefield backend", pooled_total=total, limit=MAX_POOLED_TOTAL, sample_ids=pair)
    pooled = [int(x) + int(y) for x, y in zip(a, b, strict=True)]
    positions = [i for i, value in enumerate(pooled) if value]
    if len(positions) < 2:
        raise AnalysisError("insufficient_pair_taxa", "At least two taxa must be present in each declared pair", sample_ids=pair)
    estimated = CHUNK_SIZE * len(positions) * 2 * 8 * 4
    if estimated > MAX_CHUNK_BYTES:
        raise AnalysisError("resource_limit", "Fixed Monte Carlo chunks exceed the temporary allocation budget", estimated_bytes=estimated, limit_bytes=MAX_CHUNK_BYTES)
    observed = [[int(a[i]), int(b[i])] for i in positions]
    margins = [pooled[i] for i in positions]
    expected = np.asarray(margins, dtype=float)[:, None] * (np.asarray(totals, dtype=float) / total)
    statistic = float(np.sum((np.asarray(observed, dtype=float) - expected)**2 / expected))
    effect = math.fsum(abs(int(x) / totals[0] - int(y) / totals[1]) for x, y in zip(a, b, strict=True)) / 2
    return {"sample_ids": pair, "taxon_ids": [taxon_ids[i] for i in positions],
            "taxa_absent_from_pair": [taxon_ids[i] for i, value in enumerate(pooled) if not value],
            "observed_counts": observed, "expected_counts": expected.tolist(), "sample_totals": totals,
            "pooled_taxon_totals": margins, "pearson_chi_squared": statistic,
            "braycurtis_proportions": effect}


def _prepare_input(spec, data, metadata):
    matrix, samples, taxa, meta = _read_inputs(spec, data, metadata)
    prepared = _prepare_counts(matrix, sample_ids=samples, taxon_ids=taxa,
                               empty_samples=spec.empty_samples, metadata=meta)
    declared = resolve_pairs(spec, prepared["sample_ids"])
    pairs = [_pair_data(prepared["counts"], prepared["sample_ids"], taxa, pair) for pair in declared]
    return prepared, pairs


def validate_count_homogeneity(spec, data, metadata=None):
    spec = spec if isinstance(spec, CountHomogeneitySpec) else CountHomogeneitySpec.model_validate(spec)
    prepared, pairs = _prepare_input(spec, data, metadata)
    return {"status": "valid", "n_input": len(prepared["input_sample_ids"]),
            "n": len(prepared["sample_ids"]), "n_taxa": len(prepared["taxon_ids"]),
            "n_pairs": len(pairs), "excluded": prepared["excluded"], "warnings": prepared["warnings"],
            "scope": "Input, declared pairs, exact margins and backend bounds checked; no Monte Carlo tables sampled"}


def _zero_limits(counts, sample_ids, taxon_ids, pairs, confidence):
    paired = set(sample for pair in pairs for sample in pair)
    present = [any(int(row[i]) > 0 for row in counts) for i in range(len(taxon_ids))]
    result = []
    for sample, row in zip(sample_ids, counts, strict=True):
        if sample not in paired:
            continue
        total = sum(int(value) for value in row)
        result.append({"sample_id": sample, "n": total, "confidence": confidence,
                       "upper_limit": max(math.nextafter(0.0, 1.0), -math.expm1(math.log1p(-confidence) / total)),
                       "taxon_ids": [taxon for taxon, value, exists in zip(taxon_ids, row, present, strict=True) if value == 0 and exists],
                       "scope": "pointwise"})
    return result


def calculate_count_homogeneity(spec, data, metadata=None):
    spec = spec if isinstance(spec, CountHomogeneitySpec) else CountHomogeneitySpec.model_validate(spec)
    prepared, pairs = _prepare_input(spec, data, metadata)
    streams = np.random.SeedSequence(spec.seed).spawn(len(pairs))
    for index, (pair, stream) in enumerate(zip(pairs, streams, strict=True)):
        rng = np.random.Generator(np.random.PCG64(stream))
        distribution = random_table(pair["pooled_taxon_totals"], pair["sample_totals"])
        expected = np.asarray(pair["expected_counts"])
        threshold = (1 - TIE_RELATIVE_TOLERANCE) * pair["pearson_chi_squared"]
        b = 0
        for offset in range(0, spec.simulations, CHUNK_SIZE):
            tables = distribution.rvs(size=min(CHUNK_SIZE, spec.simulations - offset), method="patefield", random_state=rng)
            statistics = np.sum((tables - expected)**2 / expected, axis=(1, 2))
            b += int(np.count_nonzero(statistics >= threshold))
        p = (b + 1) / (spec.simulations + 1)
        interval = _interval(b, spec.simulations)
        pair.update(p_value=p, p_value_holm=p,
                    monte_carlo={"simulations": spec.simulations, "count_extreme": b, "p_value": p,
                                 "tail_probability_interval": interval, "confidence": 0.95,
                                 "reporting_alpha": 0.05, "monte_carlo_unresolved": interval[0] <= 0.05 <= interval[1],
                                 "unresolved_scope": "unadjusted_tail_only", "spawn_key": [index]}, taxon_tests=[])
        na, nb = pair["sample_totals"]
        for taxon, (xa, xb) in zip(pair["taxon_ids"], pair["observed_counts"], strict=True):
            fisher_p, underflow, bounds = _fisher(xa, na, xb, nb)
            pair["taxon_tests"].append({"taxon_id": taxon, "counts": [xa, xb],
                                        "proportion_difference_b_minus_a": xb / nb - xa / na,
                                        "p_value": fisher_p, "p_value_holm": fisher_p,
                                        "p_value_underflow": underflow, "log10_p_value": bounds})
    for pair, adjusted in zip(pairs, _holm([pair["p_value"] for pair in pairs]), strict=True):
        pair["p_value_holm"] = adjusted
    for pair, envelope in zip(pairs, _holm_envelopes([pair["monte_carlo"]["tail_probability_interval"] for pair in pairs]), strict=True):
        pair["monte_carlo"].update(holm_envelope=envelope, holm_envelope_unresolved=envelope[0] <= 0.05 <= envelope[1],
                                   holm_envelope_scope="sensitivity_diagnostic")
    taxon_tests = [test for pair in pairs for test in pair["taxon_tests"]]
    for test, adjusted in zip(taxon_tests, _holm([test["p_value"] for test in taxon_tests]), strict=True):
        test["p_value_holm"] = adjusted
    counts = [[int(value) for value in row] for row in prepared["counts"]]
    result = {"method": "count_homogeneity", "method_version": 3, "orientation": spec.orientation,
              "canonical_orientation": "samples_by_taxa", "value_type": "count", "missing": spec.missing,
              "empty_samples": spec.empty_samples, "n_input": len(prepared["input_sample_ids"]),
              "n": len(prepared["sample_ids"]), "n_taxa": len(prepared["taxon_ids"]),
              "input_sample_ids": prepared["input_sample_ids"], "sample_ids": prepared["sample_ids"],
              "taxon_ids": prepared["taxon_ids"], "retained_counts": counts, "metadata": prepared["metadata"],
              "excluded": prepared["excluded"], "warnings": prepared["warnings"],
              "pair_declaration": pair_declaration(spec, prepared["sample_ids"]), "pairs": pairs,
              "confidence": spec.confidence,
              "zero_count_limits": _zero_limits(counts, prepared["sample_ids"], prepared["taxon_ids"],
                                                [pair["sample_ids"] for pair in pairs], spec.confidence),
              "multiplicity": {"omnibus": {"method": "holm", "size": len(pairs)},
                               "taxon": {"method": "holm", "size": len(taxon_tests)}, "joint_control": False},
              "randomization": {"seed": spec.seed, "simulations": spec.simulations, "bit_generator": "PCG64",
                                "sampler": "scipy.stats.random_table", "algorithm": "patefield",
                                "numpy_version": np.__version__, "scipy_version": scipy.__version__,
                                "chunk_size": CHUNK_SIZE, "max_pooled_total": MAX_POOLED_TOTAL,
                                "tie_relative_tolerance": TIE_RELATIVE_TOLERANCE,
                                "stream_policy": "SeedSequence.spawn_declared_pair_order"},
              "references": REFERENCES, "limitations": LIMITATIONS}
    return CountHomogeneityResult.model_validate(result).model_dump(mode="json")


def _close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=0):
        raise ValueError("Numerical result disagrees with its defining calculation")


def _validate_saved_result(result):
    for labels in (result.input_sample_ids, result.sample_ids, result.taxon_ids):
        if any(not name.strip() for name in labels) or len(set(labels)) != len(labels):
            raise ValueError("Labels must be nonblank and unique")
    excluded = [item.sample_id for item in result.excluded]
    if (len(set(excluded)) != len(excluded) or set(excluded) & set(result.sample_ids) or
            set(excluded) | set(result.sample_ids) != set(result.input_sample_ids)):
        raise ValueError("Retained and excluded samples must partition the input")
    if result.empty_samples == "error" and excluded:
        raise ValueError("Error policy cannot exclude samples")
    if result.sample_ids != [sample for sample in result.input_sample_ids if sample not in excluded]:
        raise ValueError("Retained sample order must follow input order")
    if (result.n != len(result.sample_ids) or result.n_input != len(result.input_sample_ids) or
            result.n_taxa != len(result.taxon_ids) or len(result.retained_counts) != result.n or
            any(len(row) != result.n_taxa for row in result.retained_counts)):
        raise ValueError("Count shape and declared dimensions disagree")
    if any(any(value < 0 or value > MAX_EXACT_COUNT for value in row) or
           not 0 < sum(row) <= MAX_EXACT_COUNT for row in result.retained_counts):
        raise ValueError("Retained counts must be nonnegative exact counts with positive exact totals")
    if result.metadata is not None and [row.get("sample_id") for row in result.metadata] != result.sample_ids:
        raise ValueError("Metadata must align exactly with retained samples")
    pairs = [pair.sample_ids for pair in result.pairs]
    _check_pairs(pairs)
    if result.randomization.tie_relative_tolerance != TIE_RELATIVE_TOLERANCE:
        raise ValueError("Incorrect inclusive-tail tolerance")
    for index, pair in enumerate(result.pairs):
        expected = _pair_data(result.retained_counts, result.sample_ids, result.taxon_ids, pair.sample_ids)
        for key in ("taxon_ids", "taxa_absent_from_pair", "observed_counts", "sample_totals", "pooled_taxon_totals"):
            if getattr(pair, key) != expected[key]:
                raise ValueError(f"Pair {key} disagrees with retained counts")
        if (len(pair.expected_counts) != len(expected["expected_counts"]) or
                any(len(row) != 2 for row in pair.expected_counts)):
            raise ValueError("Expected-cell shape disagrees with the pair table")
        for actual_row, expected_row in zip(pair.expected_counts, expected["expected_counts"], strict=True):
            for actual, value in zip(actual_row, expected_row, strict=True):
                _close(actual, value)
        for key in ("pearson_chi_squared", "braycurtis_proportions"):
            _close(getattr(pair, key), expected[key])
        mc = pair.monte_carlo
        if (mc.simulations != result.randomization.simulations or mc.spawn_key != [index] or
                mc.count_extreme > mc.simulations):
            raise ValueError("Monte Carlo draw counts or stream provenance disagree")
        p = (mc.count_extreme + 1) / (mc.simulations + 1)
        _close(mc.p_value, p)
        _close(pair.p_value, p)
        interval = _interval(mc.count_extreme, mc.simulations)
        for actual, value in zip(mc.tail_probability_interval, interval, strict=True):
            _close(actual, value)
        if mc.monte_carlo_unresolved != (interval[0] <= 0.05 <= interval[1]):
            raise ValueError("Unresolved flag must describe only the unadjusted tail interval")
        if [test.taxon_id for test in pair.taxon_tests] != pair.taxon_ids:
            raise ValueError("Taxon tests must cover every pair-present taxon in input order")
        na, nb = pair.sample_totals
        for test, observed in zip(pair.taxon_tests, pair.observed_counts, strict=True):
            if test.counts != observed:
                raise ValueError("Taxon counts disagree with pair table")
            xa, xb = observed
            _close(test.proportion_difference_b_minus_a, xb / nb - xa / na)
            p, underflow, bounds = _fisher(xa, na, xb, nb)
            _close(test.p_value, p)
            if test.p_value_underflow != underflow or (bounds is None) != (test.log10_p_value is None):
                raise ValueError("Underflow flag or log10 p-value disagrees with the Fisher calculation")
            if bounds is not None:
                _close(test.log10_p_value, bounds)
    for pair, adjusted in zip(result.pairs, _holm([pair.p_value for pair in result.pairs]), strict=True):
        _close(pair.p_value_holm, adjusted)
    envelopes = _holm_envelopes([pair.monte_carlo.tail_probability_interval for pair in result.pairs])
    for pair, envelope in zip(result.pairs, envelopes, strict=True):
        for actual, value in zip(pair.monte_carlo.holm_envelope, envelope, strict=True):
            _close(actual, value)
        if pair.monte_carlo.holm_envelope_unresolved != (envelope[0] <= 0.05 <= envelope[1]):
            raise ValueError("Holm envelope flag disagrees with its envelope")
    declaration = result.pair_declaration
    if declaration.n_adjacent + declaration.n_extra != len(pairs):
        raise ValueError("Pair declaration counts disagree with the saved pairs")
    if declaration.mode == "explicit" and declaration.n_adjacent:
        raise ValueError("Explicit pair lists have no adjacent block")
    if declaration.mode == "adjacent" and (
            declaration.n_adjacent != len(result.sample_ids) - 1 or
            pairs[:declaration.n_adjacent] != [[a, b] for a, b in zip(result.sample_ids, result.sample_ids[1:])]):
        raise ValueError("Adjacent pairs must be the consecutive retained samples")
    tests = [test for pair in result.pairs for test in pair.taxon_tests]
    if result.multiplicity.omnibus.size != len(pairs) or result.multiplicity.taxon.size != len(tests):
        raise ValueError("Holm family sizes must match every declared pair and pair-present taxon")
    for test, adjusted in zip(tests, _holm([test.p_value for test in tests]), strict=True):
        _close(test.p_value_holm, adjusted)
    limits = _zero_limits(result.retained_counts, result.sample_ids, result.taxon_ids, pairs, result.confidence)
    if len(limits) != len(result.zero_count_limits):
        raise ValueError("Zero limits must cover each declared-pair sample once")
    for actual, expected in zip(result.zero_count_limits, limits, strict=True):
        for key in ("sample_id", "n", "confidence", "taxon_ids", "scope"):
            if getattr(actual, key) != expected[key]:
                raise ValueError("Zero-count limit identity, taxa, confidence or denominator disagree")
        _close(actual.upper_limit, expected["upper_limit"])
