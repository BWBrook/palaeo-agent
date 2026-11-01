import json, shutil, glob
import numpy as np
import palaeo_agent as pa

# 1998 samples are published relative abundances (%), not raw counts: excluded by the study spec's select.
spec = json.load(open("specs/study.json"))
spec["inputs"]["c"]["path"] = "counts.tsv"
shutil.rmtree("study_out", ignore_errors=True)
pa.run_study(spec, "study_out", base_dir=".")
r = json.load(open(glob.glob("study_out/runs/bc/*/results.json")[0]))
r = r.get("result", r)
D = np.array(r["distances"])
iu = np.triu_indices(D.shape[0], 1)
mean_bc = float(D[iu].mean())
ids = r["sample_ids"]
excl = [{"id": s, "reason": "1998 campaign row is a published relative abundance (%), not a raw count; counts not archived, so raw-count Bray-Curtis is not defined"}
        for s in ["SR295","SR209","SR366","SR328","SR198","SR236","SR142","SR219"]]
ans = {"status": "completed_with_assumptions",
 "results": {"mean_bray_curtis": mean_bc},
 "assumptions": ["Mean taken over all %d pairs among the %d 2024 count samples only." % (len(iu[0]), len(ids)),
   "Percent-only 1998 samples could not be converted to counts faithfully (rounding, unarchived counts), so they are left out rather than mixing scales."],
 "exclusions": excl,
 "issues": ["Mixed value types: 8 samples are percentages summing to ~100, Bray-Curtis on raw values would be meaningless across scales.",
            "SR325 has only 47 specimens counted; retained but its dissimilarities are noisy.",
            "Bray-Curtis PCoA has a small negative eigenvalue; irrelevant to the mean dissimilarity."],
 "summary": "Used palaeo_agent run_study (select 16 count samples, community Bray-Curtis on untransformed counts) and averaged the upper-triangle of the distance matrix."}
json.dump(ans, open("answer.json", "w"), indent=1)
