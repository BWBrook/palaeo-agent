"""Compare the amended dryland run (results-amended.json) with the archived 66-category run (results.json).

Run: uv run analyses/lake-selina/compare_definitions.py. Writes definition-sensitivity.json. Reporting
arithmetic on API outputs only (unsupported postprocessing, declared in AMENDMENT-1.md).
"""

import json
from pathlib import Path

from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ALPHA = 0.05


def main():
    old = json.loads((HERE / "results.json").read_text())
    new = json.loads((HERE / "results-amended.json").read_text())
    key = lambda s: (s["younger"], s["older"])
    o = {key(s): s for s in old["adjacent_steps"]}
    n = {key(s): s for s in new["adjacent_steps"]}
    assert o.keys() == n.keys()
    ks = list(o)
    rho = spearmanr([o[k]["braycurtis_proportions"] for k in ks], [n[k]["braycurtis_proportions"] for k in ks])
    changed = [{"step_cm": [o[k]["depths_cm"][0], o[k]["depths_cm"][1]],
                "holm_66": o[k]["p_value_holm"], "holm_60": n[k]["p_value_holm"],
                "bc_66": o[k]["braycurtis_proportions"], "bc_60": n[k]["braycurtis_proportions"],
                "monte_carlo_sensitive_60": n[k]["monte_carlo_sensitive"]}
               for k in ks if (o[k]["p_value_holm"] < ALPHA) != (n[k]["p_value_holm"] < ALPHA)]
    top = lambda d: [list(d[k]["depths_cm"]) for k in sorted(ks, key=lambda k: d[k]["adjacent_rank_by_braycurtis"])[:6]]
    lo = {l["sample_id"]: l for l in old["levels"]}
    rich = []
    for l in new["levels"]:
        rich.append({"sample_id": l["sample_id"], "depth_cm": l["depth_cm"],
                     "expected_richness_282_66": lo[l["sample_id"]]["expected_richness_282"],
                     "expected_richness_272_60": l["expected_richness_272"], "coverage_272_60": l["coverage_272"]})
    rr = spearmanr([r["expected_richness_282_66"] for r in rich], [r["expected_richness_272_60"] for r in rich])
    named = {name: {"bc_66": old["named_comparisons"][name][part]["braycurtis_proportions"],
                    "bc_60": v[part]["braycurtis_proportions"],
                    "holm_66": old["named_comparisons"][name][part]["p_value_holm"], "holm_60": v[part]["p_value_holm"],
                    "taxa_60": [t["taxon"] for t in v[part]["taxa_holm_lt_005_by_forward_change"]]}
             for name, v in new["named_comparisons"].items() for part in ("primary",)}
    out = {"adjacent_bc_spearman": rho.statistic, "adjacent_lt_005": {"66": old["homogeneity"]["adjacent_lt_005"],
                                                                     "60": new["homogeneity"]["adjacent_lt_005"]},
           "monte_carlo_sensitive": {"66": old["homogeneity"]["n_monte_carlo_sensitive"],
                                     "60": new["homogeneity"]["n_monte_carlo_sensitive"]},
           "steps_changing_classification": changed, "top6_steps_66": top(o), "top6_steps_60": top(n),
           "median_adjacent_bc": {"66": sorted(s["braycurtis_proportions"] for s in o.values())[35],
                                  "60": sorted(s["braycurtis_proportions"] for s in n.values())[35]},
           "richness_spearman": rr.statistic, "min_coverage_272_60": min(r["coverage_272_60"] for r in rich),
           "named_primary": named, "richness": rich}
    (HERE / "definition-sensitivity.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "richness"}, indent=1))


if __name__ == "__main__":
    main()
