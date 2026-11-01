import json, shutil, os
import numpy as np, pandas as pd
import palaeo_agent
from scipy.spatial.distance import pdist

dates = pd.read_csv("dates.csv")
good = dates[dates.status == "accepted"].sort_values("depth_cm")
s = pd.read_csv("samples.csv")
s["age"] = np.interp(s.depth_cm, good.depth_cm, good.age_cal_bp)
hol = s[s.age < 11700].sort_values("depth_cm")
ids = list(hol.sample_id)
older = s[s.age >= 11700]

spec = {"study_version": 1,
 "inputs": {"counts": {"kind": "counts", "path": "counts.tsv", "orientation": "samples_by_taxa", "format": "delimited", "delimiter": "tab"}},
 "datasets": {"holocene": {"source": "counts", "operations": [
   {"op": "select", "samples": ids, "reason": "Holocene: age < 11700 cal BP from linear interpolation over accepted dates"}]}},
 "analyses": [{"id": "bc", "dataset": "holocene", "spec": {"method": "community", "format": "past",
   "orientation": "samples_by_taxa", "value_type": "count", "transform": "relative_abundance", "distance": "braycurtis",
   "dimensions": 2, "missing": "error", "empty_samples": "error"}}]}
os.makedirs("specs", exist_ok=True)
json.dump(spec, open("specs/study.json", "w"), indent=1)
out = "study_out"
shutil.rmtree(out, ignore_errors=True)
res = palaeo_agent.run_study(palaeo_agent.StudySpec.model_validate(spec), out, base_dir=".")
# locate the distance matrix in the saved bundle
D = None
for root, _, fs in os.walk(out):
    for f in fs:
        if f.endswith(".json"):
            try: j = json.load(open(os.path.join(root, f)))
            except Exception: continue
            def find(o):
                if isinstance(o, dict):
                    if "distances" in o and "sample_ids" in o: return o
                    for v in o.values():
                        r = find(v)
                        if r: return r
                elif isinstance(o, list):
                    for v in o:
                        r = find(v)
                        if r: return r
            r = find(j)
            if r and D is None: D = r
d = np.array(D["distances"]); n = len(d)
mean_bc = float(d[np.triu_indices(n, 1)].mean())
# independent check
c = pd.read_csv("counts.tsv", sep="\t", index_col=0).loc[ids]
chk = float(pdist(c.div(c.sum(1), axis=0).values, "braycurtis").mean())
assert abs(chk - mean_bc) < 1e-9, (chk, mean_bc)
ans = {"status": "completed_with_assumptions",
 "results": {"mean_bray_curtis": mean_bc, "n_holocene": n},
 "assumptions": ["Age model: linear interpolation between accepted dated levels only (OZ4817 rejected).",
   "Holocene = interpolated age < 11700 cal BP (boundary at ~222.7 cm); no extrapolation needed as all samples lie within dated range.",
   "Mean over all unordered pairs of Holocene samples; Bray-Curtis on per-sample relative abundances."],
 "exclusions": [{"id": "OZ4817", "reason": "date rejected: age reversal; reworked shell (dating report); excluded from age model"}]
   + [{"id": r.sample_id, "reason": f"older than Holocene (interpolated age {r.age:.0f} cal BP)"} for r in older.itertuples()],
 "issues": ["Dated level OZ4817 (198 cm, 12816 BP) is a reversal and was rejected; had it been used, samples near 198-219 cm would be classed pre-Holocene."],
 "summary": f"Built age model from accepted dates, selected {n} Holocene samples, computed mean pairwise Bray-Curtis on relative abundances via palaeo_agent study = {mean_bc}."}
json.dump(ans, open("answer.json", "w"), indent=1)
