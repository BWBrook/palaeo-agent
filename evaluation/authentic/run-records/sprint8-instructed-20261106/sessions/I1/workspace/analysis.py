"""Coed Duon analysis via the Palaeo-Agent Python API. Run: python analysis.py"""
import json, pathlib, palaeo_agent as pa
root = pathlib.Path(__file__).resolve().parent
runs = root / "runs"
prov = {"primer": {k: pa.primer()[k] for k in ("version", "sha256")}, "runs": {}}
res, dirs = {}, {}
for p in sorted((root / "specs").glob("*.json")):
    spec = json.loads(p.read_text()); spec["input"] = str(root / spec["input"])
    out = pa.run(spec, runs / p.stem)
    d = out["run_dir"] if isinstance(out, dict) and "run_dir" in out else out
    dirs[p.stem] = d
    res[p.stem] = pa.inspect_run(d)["result"]
    prov["runs"][p.stem] = str(d)
out = {}
for k in ("comm_rel_bc", "comm_raw_bc", "comm_jac"):
    r = res[k]
    out[k] = {"sample_ids": r["sample_ids"], "diversity": r["diversity"], "warnings": r["warnings"],
              "adjacent_distance": [r["distances"][i][i + 1] for i in range(r["n"] - 1)],
              "distances_from_7": r["distances"][6], "eigenvalues": r["eigenvalues"][:3], "axis1_2": [c[:2] for c in r["coordinates"]],
              "negative_to_positive_inertia": r["negative_to_positive_inertia"]}
for k in ("rare13", "rare_multi"):
    r = res[k]
    out[k] = {"sizes": r["sizes"], "warnings": r["warnings"], "samples": [
        {"id": s["sample_id"], "total": s["total"], "obs": s["observed_richness"], "f1": s["f1"], "f2": s["f2"],
         "full_coverage": s["full_coverage"], "est": [(e["size"], e["expected_richness"], e["conditional_sd"]) for e in s["estimates"]]}
        for s in r["samples"]]}
h = res["homog_adj"]
out["homog_adj"] = {"multiplicity": h["multiplicity"], "warnings": h["warnings"], "pairs": [
    {"pair": q["sample_ids"], "totals": q["sample_totals"], "chi2": q["pearson_chi_squared"], "bc_prop": q["braycurtis_proportions"],
     "p": q["p_value"], "p_holm": q["p_value_holm"], "mc_interval": q["monte_carlo"]["tail_probability_interval"],
     "taxa_holm_lt_0.05": [(t["taxon_id"], t["counts"], round(t["proportion_difference_b_minus_a"], 4), t["p_value_holm"])
                           for t in q["taxon_tests"] if t["p_value_holm"] < 0.05]} for q in h["pairs"]],
    "zero_limits": [z for z in h["zero_count_limits"] if z["sample_id"] in ("5", "6", "7")]}
cmp = pa.compare_community_runs(dirs["comm_rel_bc"], dirs["comm_raw_bc"], root / "comparisons")
cd = cmp["comparison_dir"] if "comparison_dir" in cmp else cmp.get("run_dir", cmp.get("path"))
prov["comparison"] = str(cd)
try:
    rep = json.loads((pathlib.Path(cd) / "report.json").read_text())
    keys = ("settings_changed", "pearson_distance_correlation", "spearman_distance_correlation", "maximum_absolute_distance_change",
            "mean_absolute_distance_change", "symmetric_procrustes_m2", "relative_eigengaps", "baseline_link_verified")
    out["compare_rel_vs_raw"] = {k: rep[k] for k in keys}
except Exception as e:
    out["compare_rel_vs_raw"] = {"note": repr(e)}
json.dump(out, open(root / "results.json", "w"), indent=1, default=str)
json.dump(prov, open(root / "provenance_manifest.json", "w"), indent=1)
