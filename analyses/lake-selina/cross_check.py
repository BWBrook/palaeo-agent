"""Primer section 7 cross-check: Lake Selina API results against the independent R reference (reference-r.json).

Run: uv run analyses/lake-selina/cross_check.py   (after run_api.py and reference.R). Writes cross-check.json.
Agreement is arithmetic only; it does not validate the design or the interpretation.
"""

import json
import math
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
REL, FISHER_REL, ABS = 1e-10, 1e-7, 1e-12


def main():
    ref = json.loads((HERE / "reference-r.json").read_text())
    index = json.loads((HERE / "runs/index.json").read_text())
    run = {k: pa.inspect_run(HERE / v["run_dir"])["result"] for k, v in index.items() if "run_dir" in v}
    design = json.loads((HERE / "design.json").read_text())
    assert ref["input_sha256"] == design["counts_sha256"]
    checks = []

    def check(quantity, api, r, rel=REL):
        ok = math.isclose(api, r, rel_tol=rel, abs_tol=ABS)
        checks.append({"quantity": quantity, "api": api, "r": r, "agrees": ok, "max_abs": abs(api - r)})

    rare = {s["sample_id"]: s for s in run["rarefaction"]["samples"]}
    div = {d["sample_id"]: d for d in run["community_relative_braycurtis"]["diversity"]}
    for s in ref["samples"]:
        sid, a = s["sample_id"], rare[s["sample_id"]]
        e = a["estimates"][0]
        check(f"{sid} total", a["total"], s["total"])
        check(f"{sid} richness", a["observed_richness"], s["richness"])
        check(f"{sid} shannon", div[sid]["shannon"], s["shannon"])
        check(f"{sid} simpson", div[sid]["simpson"], s["simpson"])
        check(f"{sid} expected richness 282", e["expected_richness"], s["expected_richness"])
        check(f"{sid} conditional sd 282", e["conditional_sd"], s["conditional_sd"], rel=1e-8)
        check(f"{sid} coverage 282", e["coverage"], s["coverage_at_m"])
        check(f"{sid} full coverage", a["full_coverage"], s["full_coverage"])
    for api_name, ref_name in (("community_relative_braycurtis", "relative_braycurtis"),
                               ("community_raw_braycurtis", "raw_braycurtis"),
                               ("community_jaccard", "binary_jaccard")):
        d, rd = run[api_name]["distances"], ref["distances"][ref_name]
        worst = max(abs(d[i][j] - rd[i][j]) for i in range(len(d)) for j in range(len(d)))
        checks.append({"quantity": f"{ref_name} matrix (72 x 72)", "max_abs": worst, "agrees": worst <= 1e-12})
    hom = {tuple(p["sample_ids"]): p for p in run["count_homogeneity"]["pairs"]}
    for pair in ref["named_pair_fisher"]:
        api = {t["taxon_id"]: t for t in hom[tuple(pair["sample_ids"])]["taxon_tests"]}
        for t in (pair["taxa"].values() if isinstance(pair["taxa"], dict) else pair["taxa"]):
            check(f"{pair['comparison']} {t['taxon']} fisher p", api[t["taxon"]]["p_value"], t["p_value"], rel=FISHER_REL)
            assert api[t["taxon"]]["counts"] == t["counts"]
    receipt = {"reference": {k: ref[k] for k in ("r_version", "vegan_version", "inext_source_sha256", "settings")},
               "tolerances": {"default_relative": REL, "conditional_sd_relative": 1e-8, "fisher_relative": FISHER_REL,
                              "absolute": ABS, "distance_absolute": 1e-12},
               "n_checks": len(checks), "n_agree": sum(c["agrees"] for c in checks),
               "max_abs_difference": max(c["max_abs"] for c in checks),
               "disagreements": [c for c in checks if not c["agrees"]]}
    (HERE / "cross-check.json").write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps({k: receipt[k] for k in ("n_checks", "n_agree", "max_abs_difference")}))


if __name__ == "__main__":
    main()
