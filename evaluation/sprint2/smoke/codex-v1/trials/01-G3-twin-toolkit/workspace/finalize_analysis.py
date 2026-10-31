"""Run after: python -m palaeo_agent run analysis_spec.json --output permanova_run"""
import csv
import itertools
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parent
run = sorted((root / "permanova_run").glob("*/results.json"))[-1]
r = json.loads(run.read_text())
with (root / "counts.tsv").open() as f:
    rows = list(csv.reader(f, delimiter="\t"))
ids = [row[0] for row in rows[1:]]
x = np.array([[int(v) for v in row[1:]] for row in rows[1:]], dtype=float)
with (root / "samples.csv").open() as f:
    metadata = list(csv.DictReader(f))
assert len(ids) == len(set(ids)) == len(metadata) == 10
assert len({m["sample_id"] for m in metadata}) == 10
assert len({m["site_id"] for m in metadata}) == 10
lookup = {m["sample_id"]: m for m in metadata}
assert set(ids) == set(lookup)
assert np.isfinite(x).all() and (x >= 0).all() and (x.sum(axis=1) > 0).all()
groups = np.array([lookup[i]["facies"] for i in ids])
assert ids == r["sample_ids"]
d = np.abs(x[:, None, :] - x[None, :, :]).sum(axis=2) / (x.sum(axis=1)[:, None] + x.sum(axis=1)[None, :])
assert np.allclose(d, r["distances"])
ss_total = np.square(d).sum() / (2 * len(x))

def statistic(reef_indices):
    reef = np.zeros(len(x), dtype=bool)
    reef[list(reef_indices)] = True
    within = sum(np.square(d[np.ix_(mask, mask)]).sum() / (2 * mask.sum()) for mask in (reef, ~reef))
    return (ss_total - within) / (within / 8)

observed = statistic(np.flatnonzero(groups == "reef"))
statistics = [statistic(c) for c in itertools.combinations(range(10), 4)]
extreme = sum(v >= observed - r["permutation"]["tie_tolerance"] for v in statistics)
assert len(statistics) == 210 and extreme == 1
assert np.isclose(observed, r["pseudo_f"])
assert extreme / len(statistics) == r["p_value"]
# Equal sample totals and two taxa make Bray-Curtis one-dimensional here.
direct_means = {g: float(np.abs(x[groups == g, 0] / 100 - (x[groups == g, 0] / 100).mean()).mean()) for g in ("reef", "lagoon")}
for g, v in direct_means.items():
    assert np.isclose(v, r["dispersion"]["group_mean_distances"][g])

keys = ["n", "pseudo_f", "r_squared", "p_value", "ss_total", "ss_within", "ss_between", "df_between", "df_within"]
results = {k: r[k] for k in keys}
results["group_mean_centroid_distance"] = r["dispersion"]["group_mean_distances"]
results["claim_supported"] = 1
answer = {
    "status": "completed_with_assumptions",
    "results": results,
    "assumptions": [
        "Each sample is a distinct site sampled once; the ten sites are independent sampling units, as declared in dictionary.md.",
        "Facies labels are freely exchangeable among sites under the null, preserving the observed group sizes (reef 4, lagoon 6); there are no blocks, covariates, repeated measures or nested subsamples.",
        "The supplied nonnegative integer counts measure comparable community composition; they are used without transformation, normalization or aggregation."
    ],
    "exclusions": [],
    "issues": [
        "No count or metadata problems were found: sample IDs are unique and match exactly, site IDs are unique, all counts are finite nonnegative integers, and no sample is empty. Metadata were aligned by sample ID.",
        "Group sizes are unequal (reef 4, lagoon 6). PERMANOVA association can reflect location and dispersion; this analysis does not isolate a pure location effect or establish causation.",
        "Centroid distances are descriptive, without bias adjustment, square-root distance transformation, additive correction or dispersion significance testing. One positive eigenaxis is retained; nine numerical near-zero eigenmodes are discarded at the package threshold, with no substantive negative eigenvalues and no truncated negative squared centroid distances.",
        "Although 999 permutations were requested with seed 20261031, all 210 distinct size-preserving allocations were feasible and enumerated. The exact p-value is 1/210, including the observed allocation; no Monte Carlo plus-one correction is applied.",
        "Rerun with python -m palaeo_agent run analysis_spec.json --output permanova_run, then python finalize_analysis.py. The specification and full run directory preserve inputs, environment, manifest, distances, eigenvalues, permutations and results; finalize_analysis.py independently checks the distances, pseudo-F, exact p-value and centroid means."
    ],
    "summary": "The full draft claim is supported (claim_supported=1): exact one-way PERMANOVA on untransformed Bray-Curtis dissimilarities provides evidence of a facies-associated community difference under the stated independence and exchangeability assumptions (pseudo-F=873.8133333333333, R-squared=0.9909277851699528, p=0.004761904761904762). Group mean centroid distances describe within-facies spread separately and do not isolate a pure location effect. All ten sites were retained. Numerical results are copied at computed precision from Palaeo-Agent, without rounding."
}
schema = json.loads((root / "answer.schema.json").read_text())
# Validate the complete supplied contract without installing a schema package.
def validate(value, rule):
    types = {"object": dict, "array": list, "string": str}
    if "type" in rule:
        assert isinstance(value, types[rule["type"]])
    if "enum" in rule:
        assert value in rule["enum"]
    if isinstance(value, dict):
        assert set(rule.get("required", [])) <= set(value)
        if rule.get("additionalProperties") is False:
            assert set(value) <= set(rule.get("properties", {}))
        for key, child in rule.get("properties", {}).items():
            if key in value:
                validate(value[key], child)
    if isinstance(value, list) and "items" in rule:
        for item in value:
            validate(item, rule["items"])

validate(answer, schema)
assert set(results) == set(keys) | {"group_mean_centroid_distance", "claim_supported"}
assert set(results["group_mean_centroid_distance"]) == {"reef", "lagoon"}
(root / "answer.json").write_text(json.dumps(answer, indent=2, allow_nan=False) + "\n")
print("answer.json written and schema validated; independent numerical checks passed.")
