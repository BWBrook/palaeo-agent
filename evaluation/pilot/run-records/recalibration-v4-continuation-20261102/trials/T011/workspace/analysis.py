import json, os, shutil, pandas as pd, palaeo_agent
spec = json.load(open("specs/study.json"))
spec["inputs"]["counts"]["path"] = "../counts.tsv"
out = "study_out"
shutil.rmtree(out, ignore_errors=True)
os.makedirs("specs", exist_ok=True)
r = palaeo_agent.run_study(spec, out, base_dir="specs")

import glob
res = json.load(open(glob.glob(out + "/runs/comm/*/results.json")[0]))
sh = {d["sample_id"]: d["shannon"] for d in res["diversity"]}
meta = pd.read_csv("samples.csv").set_index("sample_id")
oldest = meta["depth_cm"].idxmax()
youngest = meta["depth_cm"].idxmin()
change = sh[youngest] - sh[oldest]
ans = {
    "status": "completed_with_assumptions",
    "results": {"shannon_change": change},
    "assumptions": [
        "Depth is the age proxy (undisturbed core): oldest = deepest sample (%s, %s cm), youngest = shallowest (%s, %s cm)." % (oldest, meta.loc[oldest, "depth_cm"], youngest, meta.loc[youngest, "depth_cm"]),
        "Shannon computed on raw counts, natural log, via the palaeo_agent community method; two all-zero taxa columns do not affect it.",
    ],
    "exclusions": [],
    "issues": [
        "Sample order in counts.tsv is not depth order; ordered using samples.csv depth_cm.",
        "Sample totals differ (184-385 specimens); Shannon is not rarefied, so the difference in totals may bias comparisons.",
        "Lab log remarks (re-counted, archived residue, re-labelled slide) do not indicate count problems; no samples excluded. Processing batches differ (S05 B1, S06 B3) and are not adjusted for.",
    ],
    "summary": "Shannon (ln) of %s (youngest) minus %s (oldest): %.6f - %.6f." % (youngest, oldest, sh[youngest], sh[oldest]),
}
json.dump(ans, open("answer.json", "w"), indent=2)
