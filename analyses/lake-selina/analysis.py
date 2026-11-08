"""Stage 2, step 2: summarise the Lake Selina API runs into results.json. Run: uv run analyses/lake-selina/analysis.py

Every quantity comes from verified run bundles (inspect_run, inspect_comparison) written by run_api.py.
Unsupported postprocessing, declared in INTAKE.md and report.md: the Holm envelope over Monte Carlo tail
bounds, ranking, sign reversal to forward time, and picking adjacent distances from the API matrices.
"""

import json
import sys
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
DATED_BASE_CM = 295
ALPHA = 0.05


def holm(p):
    order = sorted(range(len(p)), key=lambda i: p[i])
    out, running = [0.0] * len(p), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        out[i] = running
    return out


def main(design_name="design.json"):
    design = json.loads((HERE / design_name).read_text())
    original = design_name == "design.json"
    runs_dir = HERE / ("runs" if original else f"runs-{Path(design_name).stem}")
    index = json.loads((runs_dir / "index.json").read_text())
    runs = {k: pa.inspect_run(HERE / v["run_dir"]) for k, v in index.items() if "run_dir" in v}
    suppress = design.get("suppress_ages", False)
    flagged = design.get("flagged_levels", {})
    labels = design.get("age_labels", {})
    lp, la = labels.get("primary", "ippd2"), labels.get("alternative", "ippd1")
    offset = 30 if suppress else design.get("candidate_offset_cm")
    comparison = pa.inspect_comparison(HERE / index["compare_relative_vs_raw"]["comparison_dir"])
    assert all(r["status"] == "verified" for r in runs.values()) and comparison["status"] == "verified"

    levels = {}
    for line in (HERE / design.get("levels_file", "data/levels.csv")).read_text().splitlines()[1:]:
        sid, depth, age, young, old, age1 = line.split(",")
        dated = age != "" and (int(depth) <= DATED_BASE_CM or "levels_file" in design) and not suppress
        levels[sid] = {"sample_id": sid, "depth_cm": int(depth),
                       "temporal_scope": "suspended" if suppress else ("dated" if dated else "depth_only"),
                       f"age_{lp}": int(age) if dated else None,
                       f"age_{lp}_bounds": [int(young), int(old)] if dated else None}
        if lp == "ippd2":
            levels[sid]["archived_ages_provenance"] = {"ippd2": int(age), "ippd1": int(age1)}
        else:
            levels[sid][f"age_{la}"] = int(age1) if dated else None
        if offset:
            levels[sid]["candidate_paper_depth_cm"] = int(depth) - offset
        if sid in flagged:
            levels[sid]["provenance_flag"] = flagged[sid]

    rare = runs["rarefaction"]["result"]
    rel = runs["community_relative_braycurtis"]["result"]
    raw = runs["community_raw_braycurtis"]["result"]
    jac = runs["community_jaccard"]["result"]
    diversity = {d["sample_id"]: d for d in rel["diversity"]} if isinstance(rel["diversity"], list) else None
    per_level = []
    for s in rare["samples"]:
        e = s["estimates"][0]
        d = diversity[s["sample_id"]] if diversity else None
        per_level.append({**levels[s["sample_id"]], "total": s["total"], "observed_richness": s["observed_richness"],
                          "f1": s["f1"], "f2": s["f2"], "full_coverage": s["full_coverage"],
                          f"expected_richness_{e['size']}": e["expected_richness"],
                          f"conditional_sd_{e['size']}": e["conditional_sd"], f"coverage_{e['size']}": e["coverage"], "variance_clamped": e["variance_clamped"],
                          "diversity": d})

    hom = runs["count_homogeneity"]["result"]
    pairs = hom["pairs"]
    taxa = hom["taxon_ids"]
    lower = holm([p["monte_carlo"]["tail_probability_interval"][0] for p in pairs])
    upper = holm([p["monte_carlo"]["tail_probability_interval"][1] for p in pairs])
    recomputed = holm([p["p_value"] for p in pairs])
    holm_matches_api = all(abs(a - p["p_value_holm"]) <= 1e-15 for a, p in zip(recomputed, pairs))
    pos = {sid: i for i, sid in enumerate(rel["sample_ids"])}

    def summarise(p, i):
        a, b = p["sample_ids"]
        tests = [{"taxon": t["taxon_id"], "counts_younger_older": t["counts"],
                  "forward_change_younger_minus_older": -t["proportion_difference_b_minus_a"],
                  "p_value": t["p_value"], "p_value_holm": t["p_value_holm"]} for t in p["taxon_tests"]]
        significant = sorted([t for t in tests if t["p_value_holm"] < ALPHA],
                             key=lambda t: -abs(t["forward_change_younger_minus_older"]))
        flag = {"provenance_flagged": a in flagged or b in flagged} if flagged else {}
        return {"younger": a, "older": b, **flag, "depths_cm": [levels[a]["depth_cm"], levels[b]["depth_cm"]],
                f"ages_{lp}": [levels[a][f"age_{lp}"], levels[b][f"age_{lp}"]],
                f"elapsed_{lp}_years": None if levels[b][f"age_{lp}"] is None or levels[a][f"age_{lp}"] is None
                else levels[b][f"age_{lp}"] - levels[a][f"age_{lp}"],
                "totals": p["sample_totals"], "braycurtis_proportions": p["braycurtis_proportions"],
                "community_relative_braycurtis": rel["distances"][pos[a]][pos[b]],
                "community_raw_braycurtis": raw["distances"][pos[a]][pos[b]],
                "community_binary_jaccard": jac["distances"][pos[a]][pos[b]],
                "pearson_chi_squared": p["pearson_chi_squared"], "p_value": p["p_value"],
                "p_value_holm": p["p_value_holm"], "tail_probability_interval": p["monte_carlo"]["tail_probability_interval"],
                "holm_envelope": [lower[i], upper[i]],
                "monte_carlo_sensitive": lower[i] <= ALPHA <= upper[i],
                "monte_carlo_unresolved_raw": p["monte_carlo"]["monte_carlo_unresolved"],
                "n_taxa_tested": len(tests), "n_taxa_holm_lt_005": len(significant),
                "taxa_holm_lt_005_by_forward_change": significant}

    summaries = [summarise(p, i) for i, p in enumerate(pairs)]
    n_adjacent = design["declared_pairs"]["adjacent"]
    adjacent = summaries[:n_adjacent]
    for rank, s in enumerate(sorted(adjacent, key=lambda s: -s["braycurtis_proportions"]), start=1):
        s["adjacent_rank_by_braycurtis"] = rank
    by_ids = {(s["younger"], s["older"]): s for s in summaries}
    named = {}
    for name, spec in design["named_comparisons"].items():
        ids = tuple(e["sample_id"] for e in spec["endpoints"])
        sens_spec = design["chronology_sensitivity"][name]
        sens = sens_spec.get("ippd1_endpoints") or sens_spec["alternative_endpoints"]
        sens_ids = tuple(e["sample_id"] for e in sens)
        between = [s for s in adjacent
                   if ids[0] and levels[ids[0]]["depth_cm"] <= levels[s["younger"]]["depth_cm"]
                   and levels[s["older"]]["depth_cm"] <= levels[ids[1]]["depth_cm"]]
        named[name] = {"primary": by_ids[ids], f"{la}_sensitivity": by_ids[sens_ids],
                       "adjacent_steps_within": [{"younger": s["younger"], "older": s["older"],
                                                  "braycurtis_proportions": s["braycurtis_proportions"],
                                                  "p_value_holm": s["p_value_holm"],
                                                  "adjacent_rank_by_braycurtis": s["adjacent_rank_by_braycurtis"]}
                                                 for s in between]}

    zero_limits = {z["sample_id"]: {"n": z["n"], "upper_limit": z["upper_limit"], "n_absent_taxa": len(z["taxon_ids"])}
                   for z in hom["zero_count_limits"]}
    report = comparison["report"]
    results = {
        "design_sha256_inputs": {"counts_sha256": design["counts_sha256"],
                                 **({"intake_script_sha256": design["intake_script_sha256"]} if original else
                                    {"amend_script_sha256": design["amend_script_sha256"],
                                     "base_design_counts_sha256": design["base_design_counts_sha256"]})},
        "environment": runs["count_homogeneity"]["environment"],
        "primer": {k: pa.primer()[k] for k in ("version", "sha256")},
        "levels": per_level,
        "rarefaction_warnings": rare["warnings"],
        "homogeneity": {"multiplicity": hom["multiplicity"], "warnings": hom["warnings"],
                        "randomization": hom["randomization"], "holm_recomputed_matches_api": holm_matches_api,
                        "n_monte_carlo_sensitive": sum(s["monte_carlo_sensitive"] for s in summaries),
                        "n_pairs_holm_lt_005": sum(s["p_value_holm"] < ALPHA for s in summaries),
                        "adjacent_lt_005": sum(s["p_value_holm"] < ALPHA for s in adjacent)},
        "adjacent_steps": adjacent,
        "named_comparisons": named,
        "zero_count_limits": zero_limits,
        "ordination": {"relative_braycurtis": {"eigenvalues": rel["eigenvalues"][:5],
                                                "axis_positive_inertia": rel["axis_positive_inertia"][:3],
                                                "negative_to_positive_inertia": rel["negative_to_positive_inertia"],
                                                "coordinates_axis1_2": {sid: c[:2] for sid, c in
                                                                        zip(rel["sample_ids"], rel["coordinates"])},
                                                "warnings": rel["warnings"]},
                       "raw_warnings": raw["warnings"], "jaccard_warnings": jac["warnings"]},
        "compare_relative_vs_raw": {k: report[k] for k in (
            "settings_changed", "pearson_distance_correlation", "spearman_distance_correlation",
            "maximum_absolute_distance_change", "mean_absolute_distance_change", "symmetric_procrustes_m2",
            "selected_subspace_identifiable", "relative_eigengaps", "baseline_link_verified", "warnings")},
    }
    (HERE / ("results.json" if original else f"results-{Path(design_name).stem.removeprefix('design-')}.json")).write_text(
        json.dumps(results, indent=1) + "\n")
    print(json.dumps(results["homogeneity"], indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:2])
