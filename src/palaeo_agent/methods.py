"""Explicit dispatch for supported scientific methods."""

import csv
import json
from pathlib import Path
from typing import Annotated

import numpy as np
from pydantic import Field, TypeAdapter

from .core import AnalysisError, RmaResult, RmaSpec, calculate, discover as rma_discover
from .community import (
    CommunityResult, CommunitySpec, REFERENCES, calculate_community, selected_subspace_info, validate_community,
    value_keys, without_absent_branch,
)
from .permanova import PermanovaResult, PermanovaSpec, calculate_permanova, validate_permanova
from .rarefaction import RarefactionResult, RarefactionSpec, calculate_rarefaction, validate_rarefaction
from .count_homogeneity import (
    CountHomogeneityResult, CountHomogeneitySpec, calculate_count_homogeneity, pair_declaration, resolve_pairs,
    validate_count_homogeneity,
)
from .primer import primer_metadata


MethodSpec = Annotated[
    RmaSpec | CommunitySpec | PermanovaSpec | RarefactionSpec | CountHomogeneitySpec,
    Field(discriminator="method"),
]
SPEC_ADAPTER = TypeAdapter(MethodSpec)
COMMON_FILES = {"spec.json", "results.json", "environment.json"}
PLOT_FILES = {"diagnostics.svg", "diagnostics.png"}
METHOD_INDEX = [
    {"id": "rma", "description": "Descriptive reduced-major-axis regression",
     "scope": "Paired measurements; no inferential uncertainty", "refuses": ["constant variables", "undefined covariance"],
     "provides": ["slope", "intercept", "correlation", "means and SDs", "residual RMSE", "raw or log10 scale",
                  "warnings for repeated pairs and repeated consecutive blocks"]},
    {"id": "community", "description": "Count or abundance diversity, dissimilarities and uncorrected PCoA",
     "scope": "Declared counts and orientation", "refuses": ["missing counts", "unresolved positive eigenvalue cutoff"],
     "provides": ["per-sample total, richness, Shannon (natural log) and Simpson (1 - sum p^2)",
                  "Bray-Curtis or binary Jaccard distance matrix", "raw or relative-abundance input",
                  "PCoA coordinates and eigenvalues", "warnings for identical sample count profiles"]},
    {"id": "permanova", "description": "One-factor free-label PERMANOVA with descriptive dispersion",
     "scope": "Independent units; exchangeable labels; two or more samples per group",
     "refuses": ["restricted or repeated designs", "empty samples", "undefined observed finite F"],
     "provides": ["pseudo-F", "R-squared", "permutation p-value", "group dispersions"]},
    {"id": "rarefaction", "description": "Equal-count richness and estimated sample coverage",
     "scope": "Individual-count interpolation; conditional subsample variance",
     "refuses": ["extrapolation", "invalid sizes", "unsupported numerical workload"],
     "provides": ["expected richness, conditional variance and SD", "estimated coverage at declared sizes",
                  "full-sample coverage with singleton/doubleton diagnostics"]},
    {"id": "count_homogeneity", "description": "Conditional comparison of declared count-sample pairs",
     "scope": "Independent multinomial counting units; no between-collection or causal inference",
     "refuses": ["undeclared or duplicate pairs", "empty samples in pairs", "unsupported sampling workload"],
     "provides": ["fixed-margin Pearson Monte Carlo p and uncertainty", "proportional Bray-Curtis effect",
                  "separate omnibus and taxon Holm families", "pointwise zero-count upper limits"]},
]
INPUT_FORMATS = ("Count tables: format 'past' (first header cell '.', tab-separated) or 'delimited' with delimiter "
                 "'tab' or 'comma' (first header cell names the ID column). Metadata: UTF-8 CSV joined by exact ID.")


def parse_spec(value):
    return SPEC_ADAPTER.validate_python(value)


def discover():
    methods = rma_discover()["methods"]
    methods.append({
        "id": "community", "version": 1,
        "description": "Count- or abundance-community diversity, explicit dissimilarities and uncorrected PCoA",
        "requirements": ["Declared value type (count, or abundance weights such as percentages) and matrix orientation",
                         "Unique sample/taxon IDs",
                         "Metadata joined by exact sample ID", "Sufficient positive eigenaxes",
                         "Requested dimensions must retain complete numerically resolved positive eigenvalue blocks"],
        "limitations": ["No group inference or causal claim", "Negative eigenvalues are reported, not corrected",
                        "Jaccard is binary occurrence distance, not quantitative Jaccard",
                        "Abundance row sums are weight sums, not specimen counts; no count-based estimator applies"],
        "references": REFERENCES,
        "input_schema": CommunitySpec.model_json_schema(),
        "output_schema": CommunityResult.model_json_schema(),
    })
    methods.append({
        "id": "permanova", "version": 1,
        "description": METHOD_INDEX[2]["description"],
        "requirements": ["Independent sampling units and freely exchangeable labels explicitly declared",
                         "Exactly one categorical group factor, two or more samples per group",
                         "Declared value type: count, or abundance weights such as percentages",
                         "Metadata joined by exact sample ID; finite observed pseudo-F"],
        "limitations": ["Association test, not a pure centroid-location test",
                        "No blocks, covariates, repeated measures or restricted permutations",
                        "Dispersion is descriptive and has no p-value; design declarations are assumptions"],
        "references": ["https://vegandevs.github.io/vegan/reference/adonis.html",
                       "https://vegandevs.github.io/vegan/reference/betadisper.html"],
        "input_schema": PermanovaSpec.model_json_schema(),
        "output_schema": PermanovaResult.model_json_schema(),
    })
    methods.extend([
        {"id": "rarefaction", "version": 1, "description": METHOD_INDEX[3]["description"],
         "requirements": ["Nonnegative integer counts and declared orientation", "Positive retained sample totals",
                          "Subsample sizes from one through each retained total"],
         "limitations": ["Conditional richness variance is not population uncertainty",
                         "Coverage is estimated abundance mass, not the proportion of taxa discovered",
                         "No extrapolation or equal-coverage standardisation"],
         "references": ["https://vegandevs.github.io/vegan/reference/rarefy.html",
                        "https://esapubs.org/archive/ecol/E093/238/appendix-D.pdf"],
         "input_schema": RarefactionSpec.model_json_schema(),
         "output_schema": RarefactionResult.model_json_schema()},
        {"id": "count_homogeneity", "version": 2, "description": METHOD_INDEX[4]["description"],
         "requirements": ["Independent multinomial counts under a common composition null",
                          "Declared distinct pairs (or 'adjacent' in table order, plus extras), simulation count and seed"],
         "limitations": ["Counting-model inference only; no ecological cause or between-collection variance",
                         "Two Holm families do not jointly guarantee one global error rate",
                         "Monte Carlo intervals describe unadjusted tails, not adjusted decision stability",
                         "The Holm envelope over tail bounds is a sensitivity diagnostic, not a simultaneous interval",
                         "Holm-adjusted values depend on the whole declared pair family",
                         "Zero-count limits are pointwise, not evidence of absence"],
         "references": ["https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.random_table.html",
                        "https://stat.ethz.ch/R-manual/R-devel/library/stats/html/chisq.test.html"],
         "input_schema": CountHomogeneitySpec.model_json_schema(),
         "output_schema": CountHomogeneityResult.model_json_schema()},
    ])
    return {"primer": primer_metadata(), "method_index": METHOD_INDEX, "input_formats": INPUT_FORMATS,
            "methods": methods}


def read_inputs(spec):
    paths = {"measurements" if spec.method == "rma" else "matrix": spec.input}
    if getattr(spec, "metadata", None) is not None:
        paths["metadata"] = spec.metadata
    payload = {}
    for role, path in paths.items():
        try:
            payload[role] = Path(path).read_bytes()
        except OSError as exc:
            raise AnalysisError("input_unreadable", "Cannot read input file", role=role,
                                path=str(path), reason=str(exc)) from exc
    return payload


def calculate_method(spec, inputs):
    if spec.method == "rma":
        return calculate(spec, inputs["measurements"])
    if spec.method == "permanova":
        return calculate_permanova(spec, inputs["matrix"], inputs["metadata"])
    if spec.method == "rarefaction":
        return calculate_rarefaction(spec, inputs["matrix"], inputs.get("metadata"))
    if spec.method == "count_homogeneity":
        return calculate_count_homogeneity(spec, inputs["matrix"], inputs.get("metadata"))
    return calculate_community(spec, inputs["matrix"], inputs.get("metadata"))


def validate(spec):
    spec = parse_spec(spec)
    inputs = read_inputs(spec)
    if spec.method == "community":
        return validate_community(spec, inputs["matrix"], inputs.get("metadata"))
    if spec.method == "permanova":
        return validate_permanova(spec, inputs["matrix"], inputs["metadata"])
    if spec.method == "rarefaction":
        return validate_rarefaction(spec, inputs["matrix"], inputs.get("metadata"))
    if spec.method == "count_homogeneity":
        return validate_count_homogeneity(spec, inputs["matrix"], inputs.get("metadata"))
    result = calculate_method(spec, inputs)
    return {"status": "valid", "n": result["n"], "n_input": result["n_input"],
            "excluded": result["excluded"], "warnings": result["warnings"],
            "scope": "Data and numerical requirements checked; scientific sampling assumptions are not established"}


def validate_result(spec, value):
    model = {"rma": RmaResult, "community": CommunityResult, "permanova": PermanovaResult,
             "rarefaction": RarefactionResult, "count_homogeneity": CountHomogeneityResult}[spec.method]
    result = model.model_validate(value).model_dump(mode="json")
    if spec.method in {"community", "permanova"}:
        result = without_absent_branch(result)
    keys = ("method", "missing")
    if spec.method in {"rma", "community", "permanova"}:
        keys += ("transform",)
    if spec.method == "community":
        keys += ("value_type", "distance", "empty_samples", "dimensions")
    if spec.method == "permanova":
        keys += ("value_type", "distance", "empty_samples", "orientation", "group_column", "design", "permutation_scheme")
    if spec.method in {"rarefaction", "count_homogeneity"}:
        keys += ("value_type", "empty_samples", "orientation")
    if any(getattr(spec, key) != result[key] for key in keys):
        raise ValueError("Saved specification and result describe different analyses")
    if spec.method == "rma" and spec.x == spec.y:
        raise ValueError("Saved specification must select distinct measurement columns")
    if spec.method != "rma" and (spec.metadata is None) != (result["metadata"] is None):
        raise ValueError("Metadata specification and result disagree")
    if spec.method == "permanova":
        if result["permutation"]["requested"] != spec.permutations or result["permutation"]["seed"] != spec.seed:
            raise ValueError("Permutation specification and result disagree")
        if any(row.get(spec.group_column) != group for row, group in zip(result["metadata"], result["groups"], strict=True)):
            raise ValueError("Grouping labels disagree with aligned metadata")
    if spec.method == "rarefaction" and result["sizes_requested"] != spec.sizes:
        raise ValueError("Rarefaction sizes differ from the saved specification")
    if spec.method == "count_homogeneity":
        if (result["randomization"]["simulations"] != spec.simulations or
                result["randomization"]["seed"] != spec.seed or
                [pair["sample_ids"] for pair in result["pairs"]] != resolve_pairs(spec, result["sample_ids"]) or
                result["pair_declaration"] != pair_declaration(spec, result["sample_ids"]) or
                any(row["confidence"] != spec.confidence for row in result["zero_count_limits"])):
            raise ValueError("Pairwise comparison settings differ from the saved specification")
    return result


def required_files(spec):
    if spec.method in {"rarefaction", "count_homogeneity"}:
        tables = ({"rarefaction.csv", "coverage.csv"} if spec.method == "rarefaction" else
                  {"count_homogeneity.csv", "taxon_tests.csv", "zero_count_limits.csv", "randomization.json"})
        return COMMON_FILES | {"input.dat", "retained_counts.csv"} | tables | (
            {"metadata.csv", "aligned_metadata.csv"} if spec.metadata is not None else set()
        )
    tables = {"used-pairs.csv"} if spec.method == "rma" else {
        "retained_counts.csv" if spec.value_type == "count" else "retained_values.csv", "transformed_matrix.csv", "diversity.csv", "distances.csv", "ordination.csv",
        "eigenvalues.csv", "positive_gram.csv",
    }
    if spec.method == "permanova":
        tables = {"retained_counts.csv" if spec.value_type == "count" else "retained_values.csv", "transformed_matrix.csv", "distances.csv", "groups.csv",
                  "permanova.csv", "permutations.json", "dispersion.csv", "group_dispersion.csv", "eigenvalues.csv"}
    return COMMON_FILES | PLOT_FILES | {"input.dat"} | tables | (
        {"metadata.csv", "aligned_metadata.csv"} if getattr(spec, "metadata", None) is not None else set()
    )


def _table(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_tables(directory, result):
    if result["method"] == "rma":
        fields = list(result["pairs"][0])
        _table(directory / "used-pairs.csv", fields, ([row[key] for key in fields] for row in result["pairs"]))
        return
    ids, taxa = result["sample_ids"], result["taxon_ids"]
    if result["method"] in {"rarefaction", "count_homogeneity"}:
        _table(directory / "retained_counts.csv", ["sample_id", *taxa],
               ([sid, *row] for sid, row in zip(ids, result["retained_counts"], strict=True)))
        if result["metadata"] is not None:
            fields = list(result["metadata"][0])
            _table(directory / "aligned_metadata.csv", fields,
                   ([row[key] for key in fields] for row in result["metadata"]))
        if result["method"] == "rarefaction":
            fields = ["size", "expected_richness", "variance", "conditional_sd", "coverage", "coverage_unavailable_reason",
                      "variance_clamped"]
            _table(directory / "rarefaction.csv", ["sample_id", *fields],
                   ([sample["sample_id"], *[row[key] for key in fields]]
                    for sample in result["samples"] for row in sample["estimates"]))
            fields = ["sample_id", "total", "observed_richness", "f1", "f2", "full_coverage",
                      "coverage_unavailable_reason", "coverage_boundary", "coverage_note"]
            _table(directory / "coverage.csv", fields,
                   ([sample[key] for key in fields] for sample in result["samples"]))
        else:
            fields = ["sample_a", "sample_b", "pearson_chi_squared", "braycurtis_proportions", "p_value",
                      "p_value_holm", "simulations", "count_extreme", "tail_lower", "tail_upper",
                      "reporting_alpha", "monte_carlo_unresolved", "unresolved_scope", "holm_envelope_lower",
                      "holm_envelope_upper", "holm_envelope_unresolved", "holm_envelope_scope"]
            _table(directory / "count_homogeneity.csv", fields,
                   ([*pair["sample_ids"], pair["pearson_chi_squared"], pair["braycurtis_proportions"],
                     pair["p_value"], pair["p_value_holm"], pair["monte_carlo"]["simulations"],
                     pair["monte_carlo"]["count_extreme"], *pair["monte_carlo"]["tail_probability_interval"],
                     pair["monte_carlo"]["reporting_alpha"], pair["monte_carlo"]["monte_carlo_unresolved"],
                     pair["monte_carlo"]["unresolved_scope"], *pair["monte_carlo"]["holm_envelope"],
                     pair["monte_carlo"]["holm_envelope_unresolved"], pair["monte_carlo"]["holm_envelope_scope"]]
                    for pair in result["pairs"]))
            _table(directory / "taxon_tests.csv",
                   ["sample_a", "sample_b", "taxon_id", "count_a", "count_b", "p_value", "p_value_holm"],
                   ([*pair["sample_ids"], test["taxon_id"], *test["counts"], test["p_value"], test["p_value_holm"]]
                    for pair in result["pairs"] for test in pair["taxon_tests"]))
            _table(directory / "zero_count_limits.csv", ["sample_id", "taxon_id", "n", "confidence", "upper_limit", "scope"],
                   ([row["sample_id"], taxon, row["n"], row["confidence"], row["upper_limit"], row["scope"]]
                    for row in result["zero_count_limits"] for taxon in row["taxon_ids"]))
            (directory / "randomization.json").write_text(
                json.dumps(result["randomization"], indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return
    matrix_key = value_keys(result["value_type"])[0]
    for filename, key in ((f"{matrix_key}.csv", matrix_key), ("transformed_matrix.csv", "transformed_matrix")):
        _table(directory / filename, ["sample_id", *taxa], ([sid, *row] for sid, row in zip(ids, result[key], strict=True)))
    _table(directory / "distances.csv", ["sample_id", *ids], ([sid, *row] for sid, row in zip(ids, result["distances"], strict=True)))
    if result["metadata"] is not None:
        fields = list(result["metadata"][0])
        _table(directory / "aligned_metadata.csv", fields,
               ([row[key] for key in fields] for row in result["metadata"]))
    if result["method"] == "permanova":
        fields = ["pseudo_f", "r_squared", "p_value", "ss_total", "ss_within", "ss_between", "df_between", "df_within"]
        _table(directory / "permanova.csv", fields, [[result[key] for key in fields]])
        _table(directory / "groups.csv", ["sample_id", result["group_column"]], zip(ids, result["groups"], strict=True))
        dispersion = result["dispersion"]
        _table(directory / "dispersion.csv", ["sample_id", "group", "signed_squared_distance", "centroid_distance"],
               zip(ids, result["groups"], dispersion["squared_distances"], dispersion["distances"], strict=True))
        _table(directory / "group_dispersion.csv", ["group", "n", "mean_centroid_distance"],
               ([group, result["group_sizes"][group], dispersion["group_mean_distances"][group]]
                for group in result["group_labels"]))
        _table(directory / "eigenvalues.csv", ["axis", "dispersion_eigenvalue"], enumerate(dispersion["eigenvalues"], start=1))
        (directory / "permutations.json").write_text(json.dumps(result["permutation"], indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return
    fields = list(result["diversity"][0])
    _table(directory / "diversity.csv", fields, ([row[key] for key in fields] for row in result["diversity"]))
    _table(directory / "ordination.csv", ["sample_id", *[f"PCoA{i + 1}" for i in range(result["dimensions"])]],
           ([sid, *row] for sid, row in zip(ids, result["coordinates"], strict=True)))
    _table(directory / "eigenvalues.csv", ["axis", "eigenvalue"], enumerate(result["eigenvalues"], start=1))
    _table(directory / "positive_gram.csv", ["sample_id", *ids],
           ([sid, *row] for sid, row in zip(ids, result["positive_gram"], strict=True)))


def steps_for(spec, has_lock):
    sources = ["input.dat"] + (["metadata.csv"] if getattr(spec, "metadata", None) is not None else [])
    steps = [{"id": "snapshot_inputs", "inputs": [], "outputs": sources},
             {"id": "resolve_specification", "inputs": [], "outputs": ["spec.json"]},
             {"id": "record_environment", "inputs": [], "outputs": ["environment.json"] + (["uv.lock"] if has_lock else [])}]
    retained = f"{value_keys(getattr(spec, 'value_type', 'count'))[0]}.csv"
    if spec.method in {"rarefaction", "count_homogeneity"}:
        tables = (["rarefaction.csv", "coverage.csv"] if spec.method == "rarefaction" else
                  ["count_homogeneity.csv", "taxon_tests.csv", "zero_count_limits.csv", "randomization.json"])
        steps += [
            {"id": "orient_validate_exclude", "inputs": sources,
             "outputs": ["retained_counts.csv"] + (["aligned_metadata.csv"] if spec.metadata is not None else [])},
            {"id": "conditional_rarefaction" if spec.method == "rarefaction" else "conditional_count_comparison",
             "inputs": ["retained_counts.csv", "spec.json"], "outputs": tables},
        ]
    elif spec.method == "community":
        steps += [
            {"id": "orient_validate_exclude", "inputs": sources,
             "outputs": [retained] + (["aligned_metadata.csv"] if spec.metadata is not None else [])},
            {"id": "raw_count_diversity" if spec.value_type == "count" else "observed_weight_diversity",
             "inputs": [retained], "outputs": ["diversity.csv"]},
            {"id": "transform_for_distance", "inputs": [retained], "outputs": ["transformed_matrix.csv"]},
            {"id": "dissimilarity", "inputs": ["transformed_matrix.csv"], "outputs": ["distances.csv"]},
            {"id": "uncorrected_pcoa", "inputs": ["distances.csv"],
             "outputs": ["ordination.csv", "eigenvalues.csv", "positive_gram.csv"]},
        ]
    elif spec.method == "permanova":
        steps += [
            {"id": "orient_validate_align_groups", "inputs": sources,
             "outputs": [retained, "aligned_metadata.csv", "groups.csv"]},
            {"id": "transform_for_distance", "inputs": [retained], "outputs": ["transformed_matrix.csv"]},
            {"id": "dissimilarity", "inputs": ["transformed_matrix.csv"], "outputs": ["distances.csv"]},
            {"id": "permutation_association", "inputs": ["distances.csv", "groups.csv"],
             "outputs": ["permanova.csv", "permutations.json"]},
            {"id": "descriptive_centroid_dispersion", "inputs": ["distances.csv", "groups.csv"],
             "outputs": ["dispersion.csv", "group_dispersion.csv", "eigenvalues.csv"]},
        ]
    else:
        steps += [{"id": "descriptive_rma", "inputs": sources, "outputs": ["used-pairs.csv"]}]
    steps += [{"id": "collect_results", "inputs": sources + ["spec.json"], "outputs": ["results.json"]}]
    if PLOT_FILES <= required_files(spec):
        steps += [{"id": "plot_diagnostics", "inputs": ["results.json"], "outputs": ["diagnostics.svg", "diagnostics.png"]}]
    return steps


def summary(result):
    keys = ("method", "n", "n_input", "excluded", "warnings")
    if result["method"] == "rma":
        keys += ("slope", "intercept", "correlation")
    elif result["method"] == "community":
        keys += ("n_taxa", "transform", "distance", "negative_inertia_magnitude")
    elif result["method"] == "rarefaction":
        keys += ("n_taxa", "sizes")
    elif result["method"] == "count_homogeneity":
        return {**{key: result[key] for key in keys}, "n_taxa": result["n_taxa"],
                "n_pairs": len(result["pairs"]), "simulations": result["randomization"]["simulations"],
                "seed": result["randomization"]["seed"]}
    else:
        keys += ("n_taxa", "transform", "distance", "group_column", "group_sizes", "pseudo_f", "r_squared", "p_value")
    return {key: result[key] for key in keys}


def compare_results(expected, actual):
    tolerance = 1e-12 if expected["method"] == "rma" else 1e-10
    absolute = 1e-12 if expected["method"] in {"rarefaction", "count_homogeneity"} else tolerance
    policy = {"rtol": tolerance, "atol": absolute}
    differences = []
    left, right = dict(expected), dict(actual)
    if expected["method"] == "permanova":
        PermanovaResult.model_validate(left)
        PermanovaResult.model_validate(right)
        left["permutation"] = {key: value for key, value in left["permutation"].items() if key != "numpy_version"}
        right["permutation"] = {key: value for key, value in right["permutation"].items() if key != "numpy_version"}
    if expected["method"] == "rarefaction":
        RarefactionResult.model_validate(left)
        RarefactionResult.model_validate(right)
    if expected["method"] == "count_homogeneity":
        CountHomogeneityResult.model_validate(left)
        CountHomogeneityResult.model_validate(right)
        for record in (left, right):
            record["randomization"] = {key: value for key, value in record["randomization"].items()
                                       if key not in {"numpy_version", "scipy_version"}}
    if expected["method"] == "community":
        CommunityResult.model_validate(left)
        CommunityResult.model_validate(right)
        a, b = np.asarray(left.pop("coordinates")), np.asarray(right.pop("coordinates"))
        subspace = selected_subspace_info(expected["eigenvalues"], expected["dimensions"],
                                          expected["eigenvalue_tolerance"])
        identifiable = subspace["identifiable"]
        policy["ordination"] = {"full_positive_gram_compared": True,
                                "selected_gram_compared": identifiable,
                                "cutoff_relative_eigengap": subspace["relative_cutoff_gap"],
                                "cutoff_relative_eigengap_threshold": subspace["threshold"],
                                "selected_subspace_ambiguous": not identifiable}
        if identifiable:
            left["selected_ordination_gram"] = (a @ a.T).tolist()
            right["selected_ordination_gram"] = (b @ b.T).tolist()
    for record in (left, right):
        record.pop("references")
        record.pop("limitations")
        record["warnings"] = [{key: value for key, value in warning.items() if key != "message"}
                              for warning in record["warnings"]]

    def visit(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            if a.keys() != b.keys():
                differences.append(path)
                return
            for key in a:
                visit(a[key], b[key], f"{path}.{key}" if path else key)
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                differences.append(path)
                return
            for index, (x, y) in enumerate(zip(a, b, strict=True)):
                visit(x, y, f"{path}[{index}]")
        elif isinstance(a, float) and isinstance(b, (int, float)) and not isinstance(b, bool):
            if not np.isclose(a, b, rtol=tolerance, atol=absolute):
                differences.append(path)
        elif a != b:
            differences.append(path)

    visit(left, right, "")
    return differences, policy
