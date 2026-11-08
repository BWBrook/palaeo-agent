"""Run the Tasmanian surface-pollen study and summarise its verified bundles. Run: uv run analyses/tas-surface/analysis.py

Every statistic comes from the study's run bundles. Band means of closed composition and band medians of
diversity are unsupported reporting arithmetic on API outputs (declared in REPORT.md). Writes results.json;
the study bundle goes to runs-study/ (gitignored, regenerable).
"""

import json
import shutil
import statistics
from pathlib import Path

import numpy as np
import palaeo_agent as pa

HERE = Path(__file__).resolve().parent


def main():
    out = HERE / "runs-study"
    shutil.rmtree(out, ignore_errors=True)
    outcome = pa.run_study(HERE / "study.json", out)
    assert outcome["status"] == "complete", outcome
    inspected = pa.inspect_study(outcome["study_dir"])
    directory = Path(outcome["study_dir"])
    runs = {k: json.loads((directory / v["run_dir"] / "results.json").read_text())
            for k, v in json.loads((directory / "manifest.json").read_text())["runs"].items()}
    association = {}
    for name in ("association_braycurtis", "association_jaccard"):
        r = runs[name]
        association[name] = {
            "pseudo_f": r["pseudo_f"], "r_squared": r["r_squared"], "p_value": r["p_value"],
            "permutation": {k: r["permutation"][k] for k in ("mode", "draws", "count_extreme", "denominator", "seed")},
            "group_sizes": r["group_sizes"], "mean_centroid_distance": r["dispersion"]["group_mean_distances"],
            "warnings": [w["code"] for w in r["warnings"]]}
    c = runs["composition"]
    band = {row["sample_id"]: row["band"] for row in c["metadata"]}
    high = np.array([band[s] == "high" for s in c["sample_ids"]])
    closed = np.array(c["transformed_matrix"])
    means = {"high": closed[high].mean(axis=0), "low": closed[~high].mean(axis=0)}
    order = np.argsort(-np.abs(means["high"] - means["low"]))
    diversity = {b: {key: statistics.median(d[key] for d, s in zip(c["diversity"], c["sample_ids"]) if band[s] == b)
                     for key in ("richness", "shannon", "simpson")} for b in ("high", "low")}
    results = {
        "study_status": inspected["status"],
        "primer": {k: pa.primer()[k] for k in ("version", "sha256")},
        "n_selected": c["n"], "n_categories": c["n_taxa"],
        "association": association,
        "ordination": {"axis_positive_inertia": c["axis_positive_inertia"],
                       "negative_to_positive_inertia": c["negative_to_positive_inertia"],
                       "axis1_band_mean": {"high": float(np.array(c["coordinates"])[high, 0].mean()),
                                           "low": float(np.array(c["coordinates"])[~high, 0].mean())}},
        "band_median_diversity": diversity,
        "weight_sum_range": [min(d["weight_sum"] for d in c["diversity"]), max(d["weight_sum"] for d in c["diversity"])],
        "largest_band_mean_differences": [{"taxon": c["taxon_ids"][i], "high": float(means["high"][i]),
                                           "low": float(means["low"][i])} for i in order[:10]],
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=1) + "\n")
    print(json.dumps({k: results[k] for k in ("study_status", "association")}, indent=1))


if __name__ == "__main__":
    main()
