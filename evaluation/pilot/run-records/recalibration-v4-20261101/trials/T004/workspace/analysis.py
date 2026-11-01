import json, glob, shutil, numpy as np, palaeo_agent
spec = json.load(open("specs/study.json"))
shutil.rmtree("study_out", ignore_errors=True)
palaeo_agent.run_study(spec, "study_out", base_dir="specs")
res = json.load(open(glob.glob("study_out/runs/bc/*/results.json")[0]))
counts = np.array(res["retained_counts"], float)
richness = int((counts.sum(axis=0) > 0).sum())
D = np.array(res["distances"], float)
iu = np.triu_indices(D.shape[0], 1)
mbc = float(D[iu].mean())
ans = {"status": "completed_with_assumptions",
 "results": {"richness": richness, "mean_bray_curtis": mbc},
 "assumptions": ["Names recorded by the two labs were mapped to accepted names via taxonomy.csv and synonymous columns summed (G. sacculifer->Trilobatus sacculifer; G. tenellus->Globoturborotalita tenella; N. pachyderma dextral->N. incompta; sinistral->N. pachyderma).",
   "Bray-Curtis on raw counts (no transform), mean over all %d sample pairs, via palaeo_agent community method." % len(iu[0])],
 "exclusions": [],
 "issues": ["The two labs used different names for the same species, which would inflate richness and dissimilarity if unmapped.",
   "Lab log remarks reviewed; none indicate samples to exclude."],
 "summary": "Mapped recorded names to accepted names (palaeo_agent study with map_taxa), computed Bray-Curtis on raw counts, averaged the upper triangle, and counted species with >=1 specimen."}
json.dump(ans, open("answer.json", "w"), indent=1)
