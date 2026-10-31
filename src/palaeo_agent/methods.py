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
)
from .permanova import PermanovaResult, PermanovaSpec, calculate_permanova, validate_permanova


MethodSpec = Annotated[RmaSpec | CommunitySpec | PermanovaSpec, Field(discriminator="method")]
SPEC_ADAPTER = TypeAdapter(MethodSpec)
COMMON_FILES = {"spec.json", "results.json", "environment.json", "diagnostics.svg", "diagnostics.png"}
METHOD_INDEX = [
    {"id": "rma", "description": "Descriptive reduced-major-axis regression",
     "scope": "Paired measurements; no inferential uncertainty", "refuses": ["constant variables", "undefined covariance"]},
    {"id": "community", "description": "Count diversity, dissimilarities and uncorrected PCoA",
     "scope": "Declared counts and orientation", "refuses": ["missing counts", "unresolved positive eigenvalue cutoff"]},
    {"id": "permanova", "description": "One-factor free-label PERMANOVA with descriptive dispersion",
     "scope": "Independent units; exchangeable labels; two or more samples per group",
     "refuses": ["restricted or repeated designs", "empty samples", "undefined observed finite F"]},
]


def parse_spec(value):
    return SPEC_ADAPTER.validate_python(value)


def discover():
    methods = rma_discover()["methods"]
    methods.append({
        "id": "community", "version": 1,
        "description": "Count-community diversity, explicit dissimilarities and uncorrected PCoA",
        "requirements": ["Declared count values and matrix orientation", "Unique sample/taxon IDs",
                         "Metadata joined by exact sample ID", "Sufficient positive eigenaxes",
                         "Requested dimensions must retain complete numerically resolved positive eigenvalue blocks"],
        "limitations": ["No group inference or causal claim", "Negative eigenvalues are reported, not corrected",
                        "Jaccard is binary occurrence distance, not quantitative Jaccard"],
        "references": REFERENCES,
        "input_schema": CommunitySpec.model_json_schema(),
        "output_schema": CommunityResult.model_json_schema(),
    })
    methods.append({
        "id": "permanova", "version": 1,
        "description": METHOD_INDEX[2]["description"],
        "requirements": ["Independent sampling units and freely exchangeable labels explicitly declared",
                         "Exactly one categorical group factor, two or more samples per group",
                         "Metadata joined by exact sample ID; finite observed pseudo-F"],
        "limitations": ["Association test, not a pure centroid-location test",
                        "No blocks, covariates, repeated measures or restricted permutations",
                        "Dispersion is descriptive and has no p-value; design declarations are assumptions"],
        "references": ["https://vegandevs.github.io/vegan/reference/adonis.html",
                       "https://vegandevs.github.io/vegan/reference/betadisper.html"],
        "input_schema": PermanovaSpec.model_json_schema(),
        "output_schema": PermanovaResult.model_json_schema(),
    })
    return {"method_index": METHOD_INDEX, "methods": methods}


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
    return calculate_community(spec, inputs["matrix"], inputs.get("metadata"))


def validate(spec):
    spec = parse_spec(spec)
    inputs = read_inputs(spec)
    if spec.method == "community":
        return validate_community(spec, inputs["matrix"], inputs.get("metadata"))
    if spec.method == "permanova":
        return validate_permanova(spec, inputs["matrix"], inputs["metadata"])
    result = calculate_method(spec, inputs)
    return {"status": "valid", "n": result["n"], "n_input": result["n_input"],
            "excluded": result["excluded"], "warnings": result["warnings"],
            "scope": "Data and numerical requirements checked; scientific sampling assumptions are not established"}


def validate_result(spec, value):
    model = {"rma": RmaResult, "community": CommunityResult, "permanova": PermanovaResult}[spec.method]
    result = model.model_validate(value).model_dump(mode="json")
    keys = ("method", "transform", "missing")
    if spec.method == "community":
        keys += ("value_type", "distance", "empty_samples", "dimensions")
    if spec.method == "permanova":
        keys += ("value_type", "distance", "empty_samples", "orientation", "group_column", "design", "permutation_scheme")
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
    return result


def required_files(spec):
    tables = {"used-pairs.csv"} if spec.method == "rma" else {
        "retained_counts.csv", "transformed_matrix.csv", "diversity.csv", "distances.csv", "ordination.csv",
        "eigenvalues.csv", "positive_gram.csv",
    }
    if spec.method == "permanova":
        tables = {"retained_counts.csv", "transformed_matrix.csv", "distances.csv", "groups.csv",
                  "permanova.csv", "permutations.json", "dispersion.csv", "group_dispersion.csv", "eigenvalues.csv"}
    return COMMON_FILES | {"input.dat"} | tables | (
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
    for filename, key in (("retained_counts.csv", "retained_counts"), ("transformed_matrix.csv", "transformed_matrix")):
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
    if spec.method == "community":
        steps += [
            {"id": "orient_validate_exclude", "inputs": sources,
             "outputs": ["retained_counts.csv"] + (["aligned_metadata.csv"] if spec.metadata is not None else [])},
            {"id": "raw_count_diversity", "inputs": ["retained_counts.csv"], "outputs": ["diversity.csv"]},
            {"id": "transform_for_distance", "inputs": ["retained_counts.csv"], "outputs": ["transformed_matrix.csv"]},
            {"id": "dissimilarity", "inputs": ["transformed_matrix.csv"], "outputs": ["distances.csv"]},
            {"id": "uncorrected_pcoa", "inputs": ["distances.csv"],
             "outputs": ["ordination.csv", "eigenvalues.csv", "positive_gram.csv"]},
        ]
    elif spec.method == "permanova":
        steps += [
            {"id": "orient_validate_align_groups", "inputs": sources,
             "outputs": ["retained_counts.csv", "aligned_metadata.csv", "groups.csv"]},
            {"id": "transform_for_distance", "inputs": ["retained_counts.csv"], "outputs": ["transformed_matrix.csv"]},
            {"id": "dissimilarity", "inputs": ["transformed_matrix.csv"], "outputs": ["distances.csv"]},
            {"id": "permutation_association", "inputs": ["distances.csv", "groups.csv"],
             "outputs": ["permanova.csv", "permutations.json"]},
            {"id": "descriptive_centroid_dispersion", "inputs": ["distances.csv", "groups.csv"],
             "outputs": ["dispersion.csv", "group_dispersion.csv", "eigenvalues.csv"]},
        ]
    else:
        steps += [{"id": "descriptive_rma", "inputs": sources, "outputs": ["used-pairs.csv"]}]
    steps += [{"id": "collect_results", "inputs": sources + ["spec.json"], "outputs": ["results.json"]},
              {"id": "plot_diagnostics", "inputs": ["results.json"], "outputs": ["diagnostics.svg", "diagnostics.png"]}]
    return steps


def summary(result):
    keys = ("method", "n", "n_input", "excluded", "warnings")
    if result["method"] == "rma":
        keys += ("slope", "intercept", "correlation")
    elif result["method"] == "community":
        keys += ("n_taxa", "transform", "distance", "negative_inertia_magnitude")
    else:
        keys += ("n_taxa", "transform", "distance", "group_column", "group_sizes", "pseudo_f", "r_squared", "p_value")
    return {key: result[key] for key in keys}


def compare_results(expected, actual):
    tolerance = 1e-12 if expected["method"] == "rma" else 1e-10
    policy = {"rtol": tolerance, "atol": tolerance}
    differences = []
    left, right = dict(expected), dict(actual)
    if expected["method"] == "permanova":
        PermanovaResult.model_validate(left)
        PermanovaResult.model_validate(right)
        left["permutation"] = {key: value for key, value in left["permutation"].items() if key != "numpy_version"}
        right["permutation"] = {key: value for key, value in right["permutation"].items() if key != "numpy_version"}
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
            if not np.isclose(a, b, rtol=tolerance, atol=tolerance):
                differences.append(path)
        elif a != b:
            differences.append(path)

    visit(left, right, "")
    return differences, policy
