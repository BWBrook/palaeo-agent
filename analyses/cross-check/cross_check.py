"""Field-labelled cross-check of the corrected analyses against Palaeo-Agent operations (primer §7).

Run from the repository root: `uv run python analyses/cross-check/cross_check.py`.
Writes receipt.json beside this file. Bundles go to a temporary directory; run IDs are not recorded,
so the receipt replays byte for byte. Agreement is an arithmetic check only, not scientific validation.
"""

import json
import math
import tempfile
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LLANVIRN = ROOT / "benchmarks/past/legacy-data/llanvirn.dat"
DIELASMA = ROOT / "benchmarks/past/legacy-data/dielasma.dat"
EXACT_REL = 1e-12
FISHER_REL = 1e-10
MC_Z = 3.29  # two-sided 0.999 normal quantile for Monte Carlo error of a mean

llanvirn = json.loads((ROOT / "analyses/coed-duon-llanvirn/results.json").read_text())
dielasma = json.loads((ROOT / "analyses/dielasma/results.json").read_text())
checks = []


def check(case, quantity, analysis_field, api_field, analysis_value, api_value, rule, tolerance=None, se=None):
    if rule == "exact":
        ok = analysis_value == api_value
    elif rule == "relative":
        ok = math.isclose(analysis_value, api_value, rel_tol=tolerance, abs_tol=0)
    elif rule == "monte_carlo_mean":
        tolerance = MC_Z * se
        ok = abs(analysis_value - api_value) <= tolerance
    else:
        raise ValueError(rule)
    checks.append({"case": case, "quantity": quantity, "analysis_field": analysis_field, "api_field": api_field,
                   "analysis": analysis_value, "api": api_value, "rule": rule, "tolerance": tolerance,
                   "agrees": ok})


def run_result(spec, root):
    out = pa.run(spec, root)
    directory = out["run_dir"] if isinstance(out, dict) and "run_dir" in out else out
    return pa.inspect_run(directory)["result"]


counts = {"input": str(LLANVIRN), "format": "past", "orientation": "taxa_by_samples", "value_type": "count",
          "missing": "error", "empty_samples": "error"}
specs = {
    "rarefaction": counts | {"method": "rarefaction", "sizes": "minimum_total"},
    "count_homogeneity": counts | {"method": "count_homogeneity", "simulations": 9999, "seed": 7112026,
                                   "pairs": [[str(a), str(a + 1)] for a in range(1, 10)]},
    "community_relative": counts | {"method": "community", "transform": "relative_abundance",
                                    "distance": "braycurtis", "dimensions": 2},
}
validation = {name: pa.validate(spec) for name, spec in specs.items()}

with tempfile.TemporaryDirectory() as tmp:
    rare = run_result(specs["rarefaction"], tmp)
    homog = run_result(specs["count_homogeneity"], tmp)
    community = run_result(specs["community_relative"], tmp)

    case = "llanvirn"
    by_id = {s["sample_id"]: s for s in rare["samples"]}
    check(case, "rarefaction size", "rarefaction_n", "rarefaction.sizes[0]", llanvirn["rarefaction_n"], rare["sizes"][0], "exact")
    r_rare = 2000
    for h in map(str, range(1, 11)):
        sample = by_id[h]
        check(case, f"total {h}", f"totals.{h}", f"rarefaction.samples[{h}].total", llanvirn["totals"][h], sample["total"], "exact")
        check(case, f"richness {h}", f"richness.{h}", f"rarefaction.samples[{h}].observed_richness",
              llanvirn["richness"][h], sample["observed_richness"], "exact")
        est = sample["estimates"][0]
        se = est["conditional_sd"] / math.sqrt(r_rare)
        if se == 0:
            check(case, f"rarefied richness {h}", f"rarefied_richness.{h}.mean", f"rarefaction.samples[{h}].estimates[0].expected_richness",
                  llanvirn["rarefied_richness"][h]["mean"], est["expected_richness"], "relative", EXACT_REL)
        else:
            check(case, f"rarefied richness {h}", f"rarefied_richness.{h}.mean", f"rarefaction.samples[{h}].estimates[0].expected_richness",
                  llanvirn["rarefied_richness"][h]["mean"], est["expected_richness"], "monte_carlo_mean", se=se)

    order = community["sample_ids"]
    for h in map(str, range(1, 11)):
        row = community["diversity"][order.index(h)]
        shannon = row["shannon"]
        check(case, f"Shannon {h}", f"shannon.{h}", f"community.samples[{h}].shannon", llanvirn["shannon"][h], shannon, "relative", EXACT_REL)
        check(case, f"inverse Simpson {h}", f"inverse_simpson.{h}", f"1/(1 - community.samples[{h}].simpson)",
              llanvirn["inverse_simpson"][h], 1 / (1 - row["simpson"]), "relative", EXACT_REL)

    matrix = community["distances"]
    for pair in homog["pairs"]:
        a, b = pair["sample_ids"]
        k = f"{a}-{b}"
        check(case, f"Bray-Curtis proportions {k}", f"bray_curtis.proportion.{k}", f"count_homogeneity.pairs[{k}].braycurtis_proportions",
              llanvirn["bray_curtis"]["proportion"][k], pair["braycurtis_proportions"], "relative", EXACT_REL)
        check(case, f"Bray-Curtis proportions {k}", f"bray_curtis.proportion.{k}", f"community.distances[{a}][{b}]",
              llanvirn["bray_curtis"]["proportion"][k], matrix[order.index(a)][order.index(b)], "relative", EXACT_REL)

    taxa_rows = llanvirn["taxa"]
    for a, b in [(5, 6), (6, 7)]:
        k = f"{a}-{b}"
        pair = next(p for p in homog["pairs"] if p["sample_ids"] == [str(a), str(b)])
        api_by_row = {homog["taxon_ids"].index(t["taxon_id"]): t for t in pair["taxon_tests"]}
        analysis_tests = llanvirn[f"taxa_{a}_{b}"]
        if sorted(taxa_rows.index(t) for t in analysis_tests) != sorted(api_by_row):
            raise SystemExit(f"Taxon sets differ for {k}")
        for name, test in analysis_tests.items():
            api = api_by_row[taxa_rows.index(name)]
            check(case, f"taxon counts {k} {name}", f"taxa_{a}_{b}.{name}.count_a/b", f"count_homogeneity.pairs[{k}].taxon_tests[{api['taxon_id']}].counts",
                  [test["count_a"], test["count_b"]], api["counts"], "exact")
            check(case, f"Fisher p {k} {name}", f"taxa_{a}_{b}.{name}.fisher_p", f"count_homogeneity.pairs[{k}].taxon_tests[{api['taxon_id']}].p_value",
                  test["fisher_p"], api["p_value"], "relative", FISHER_REL)

    not_matched = [{
        "case": case, "analysis_field": f"composition_null.{p['sample_ids'][0]}-{p['sample_ids'][1]}.p",
        "analysis": llanvirn["composition_null"][f"{p['sample_ids'][0]}-{p['sample_ids'][1]}"]["p"],
        "api_field": f"count_homogeneity.pairs[{p['sample_ids'][0]}-{p['sample_ids'][1]}].p_value", "api": p["p_value"],
        "api_p_holm": p["p_value_holm"], "api_monte_carlo_unresolved": p["monte_carlo"]["monte_carlo_unresolved"],
        "reason": "different null (unconditional multinomial at pooled proportions vs fixed-margin conditional) and statistic (Bray-Curtis vs Pearson X2); shown side by side, no tolerance applies"}
        for p in homog["pairs"]]
    not_matched.append({"case": case, "analysis_field": "taxa_<a>_<b>.<taxon>.p_holm",
                        "reason": "per-pair Holm family over that pair's taxa; the API uses one Holm family over all 9 pairs x taxa, by contract"})
    not_matched.append({"case": case, "analysis_field": "rarefied_richness.<h>.q025/q975, sorensen_rarefied, bray_curtis_bootstrap, other bray_curtis representations, pcoa_sqrt_proportion",
                        "reason": "no matching API estimand (quantiles of simulated subsample richness, rarefied presence dissimilarity, counting-error bootstrap, sqrt or log1p representations)"})

    case = "dielasma"
    measurements = {"kind": "measurements", "path": str(DIELASMA), "format": "past", "orientation": "samples_by_taxa"}
    removals = {"as_archived": [], "block_removed": [str(i) for i in range(64, 71)],
                "unique_pairs": [str(i) for i in range(64, 72)]}
    for scenario, removed in removals.items():
        recorded = dielasma["scenarios"][scenario]["L2_rows_removed"]
        if recorded != removed:
            raise SystemExit(f"{scenario}: analysis removed {recorded}, cross-check removes {removed}")
    datasets = {"as_archived": {"source": "dielasma"}}
    datasets["block_removed"] = {"source": "dielasma", "operations": [
        {"op": "exclude", "samples": removals["block_removed"], "reason": "L2 rows 64-70 repeat rows 57-63 exactly (repeated_block warning)"}]}
    datasets["unique_pairs"] = {"source": "dielasma", "operations": [
        {"op": "exclude", "samples": removals["unique_pairs"], "reason": "L2 rows repeating an earlier (X1, X2) pair, including row 71"}]}
    analyses = []
    for scenario in removals:
        for loc in ("L1", "L2", "L3"):
            if scenario != "as_archived" and loc != "L2":
                continue
            analyses.append({"id": f"{scenario}.{loc}", "dataset": scenario, "spec": {
                "method": "rma", "format": "past", "x": f"{loc}/X1", "y": f"{loc}/X2", "transform": "log10", "missing": "drop_pairs"}})
    study = {"study_version": 1, "inputs": {"dielasma": measurements}, "datasets": datasets, "analyses": analyses}
    study_dir = pa.run_study(study, Path(tmp) / "dielasma-study")
    study_dir = study_dir["study_dir"] if isinstance(study_dir, dict) else study_dir
    inspected = pa.inspect_study(study_dir)
    study_status = inspected.get("status")
    for analysis in analyses:
        scenario, loc = analysis["id"].split(".")
        run_dir = next((Path(study_dir) / "runs" / analysis["id"]).iterdir())
        rma = pa.inspect_run(run_dir)["result"]
        source = dielasma["scenarios"][scenario]["sma_log10_width_on_length"][loc]
        field = f"scenarios.{scenario}.sma_log10_width_on_length.{loc}"
        api = f"study[{analysis['id']}].rma"
        check(case, f"n {scenario} {loc}", f"{field}.n", f"{api}.n", source["n"], rma["n"], "exact")
        for mine, theirs in (("slope", "slope"), ("intercept", "intercept"), ("r", "correlation")):
            check(case, f"{mine} {scenario} {loc}", f"{field}.{mine}", f"{api}.{theirs}", source[mine], rma[theirs], "relative", EXACT_REL)
    not_matched.append({"case": case, "analysis_field": "SMA ci95, slope = 1 test, bootstrap CI, common-slope LR, elevation, length and ratio tests, mixtures",
                        "reason": "rma is descriptive (no inferential uncertainty); no API operation computes these"})

receipt = {
    "purpose": "Arithmetic cross-check of matched quantities between the corrected analyses and Palaeo-Agent operations; not scientific validation (primer section 7).",
    "palaeo_agent_version": pa.__version__,
    "primer": {k: v for k, v in pa.primer().items() if k in ("version", "sha256")},
    "inputs": {"llanvirn": llanvirn["source"], "dielasma": dielasma["source"]},
    "validation": validation,
    "dielasma_study_status": study_status,
    "conventions": {
        "exact": "integer or list equality",
        "relative": f"relative tolerance {EXACT_REL} for deterministic floats; {FISHER_REL} for Fisher p-values (SciPy on both sides)",
        "monte_carlo_mean": f"|analysis mean of {2000} hypergeometric subsamples - exact expectation| <= {MC_Z} x conditional SD / sqrt(2000)",
        "taxa": "matched by row position in llanvirn.dat; the analysis strips the _x_ label prefix, the API keeps raw labels",
        "inverse_simpson": "API reports Gini-Simpson 1 - sum p^2; compared as 1 / (1 - simpson)",
    },
    "summary": {"checks": len(checks), "agree": sum(c["agrees"] for c in checks)},
    "checks": checks,
    "not_matched": not_matched,
}
(HERE / "receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")
print(json.dumps(receipt["summary"]))
for c in checks:
    if not c["agrees"]:
        print("DISAGREES", json.dumps(c))
