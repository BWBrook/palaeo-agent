import json, os, shutil, csv, glob
import numpy as np
import palaeo_agent

tax = list(csv.DictReader(open("taxonomy.csv")))
mapping = {r["name_as_recorded"]: r["current_name"].split()[0] for r in tax}
study = {"study_version": 1,
 "inputs": {"counts": {"kind": "counts", "path": "counts.tsv", "orientation": "taxa_by_samples",
                       "format": "delimited", "delimiter": "tab"}},
 "datasets": {"genus": {"source": "counts", "operations": [
    {"op": "map_taxa", "mapping": mapping,
     "reason": "Aggregate recorded names to genus of current_name (taxonomy.csv)"}]}},
 "analyses": [{"id": "bc", "dataset": "genus", "spec": {
    "method": "community", "format": "past", "orientation": "samples_by_taxa", "value_type": "count", "transform": "none", "distance": "braycurtis",
    "dimensions": 2, "missing": "error", "empty_samples": "error"}}]}
os.makedirs("specs", exist_ok=True)
json.dump(study, open("specs/study.json", "w"), indent=1)
out = "study_out"
shutil.rmtree(out, ignore_errors=True)
res = palaeo_agent.run_study(study, out, base_dir=".")

run = glob.glob(out + "/runs/bc/*/results.json")[0]
r = json.load(open(run))
D = np.array(r["distances"])
iu = np.triu_indices(len(D), 1)
mean_bc = float(D[iu].mean())
cnt = np.array(r["retained_counts"])
n_gen = int((cnt.sum(axis=0) > 0).sum())
ans = {"status": "completed_with_assumptions",
 "results": {"mean_bray_curtis": mean_bc, "n_genera": n_gen},
 "assumptions": ["Genus = first word of current_name in taxonomy.csv (WoRMS 2025-10); counts summed within genus.",
                 "Raw counts used with no rarefaction/standardisation, as requested; sample N05 (low yield, small total) kept."],
 "exclusions": [],
 "issues": ["Recorded names are 1987 taxonomy; several were renamed (e.g. Globigerina pachyderma -> Neogloboquadrina, G. quinqueloba -> Turborotalita, G. sacculifer -> Trilobatus), merging Neogloboquadrina taxa into one genus.",
            "N05 has a much lower total count than other samples, which affects raw-count Bray-Curtis."],
 "summary": "Mapped recorded names to current genera via palaeo_agent study (map_taxa), computed Bray-Curtis on raw genus counts, averaged over all %d sample pairs." % len(iu[0])}
json.dump(ans, open("answer.json", "w"), indent=1)
print(ans)
