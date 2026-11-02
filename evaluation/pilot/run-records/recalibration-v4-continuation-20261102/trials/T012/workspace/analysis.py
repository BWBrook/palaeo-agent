import pandas as pd, numpy as np, json
c=pd.read_csv("counts.tsv",sep="\t",index_col=0)
s=pd.read_csv("samples.csv").set_index("sample_id")
def H(r):
    p=r[r>0]/r.sum(); return float(-(p*np.log(p)).sum())
old=s.depth_cm.idxmax(); young=s.depth_cm.idxmin()
ch=H(c.loc[young])-H(c.loc[old])
json.dump({"status":"completed_with_assumptions","results":{"shannon_change":ch},
"assumptions":["Depth below core top increases with age (undisturbed core), so oldest=%s (350 cm), youngest=%s (5 cm)."%(old,young),
"Shannon computed on raw counts of all taxa, natural log, zero-count taxa ignored; sample totals differ but no rarefaction applied."],
"exclusions":[],
"issues":["Two taxa have all-zero counts in every sample; they do not affect Shannon.","Lab log remarks (archived residue, photographed, re-labelled) do not indicate count problems; processing batches differ but were not adjusted for."],
"summary":"Computed Shannon H (ln) for youngest (shallowest) and oldest (deepest) samples; reported youngest minus oldest."},open("answer.json","w"),indent=1)
