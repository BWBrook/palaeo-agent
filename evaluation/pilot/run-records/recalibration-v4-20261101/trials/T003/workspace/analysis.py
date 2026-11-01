import pandas as pd, numpy as np, json
from scipy.spatial.distance import pdist
c=pd.read_csv("counts.tsv",sep="\t").set_index("sample")
t=pd.read_csv("taxonomy.csv").set_index("name_as_recorded")["accepted_name"]
m=c.T.groupby(t.reindex(c.columns).values).sum().T
rich=int((m.sum()>0).sum())
bc=float(pdist(m.values.astype(float),"braycurtis").mean())
json.dump({"status":"completed_with_assumptions","results":{"richness":rich,"mean_bray_curtis":bc},
"assumptions":["Recorded names merged to accepted_name via taxonomy.csv (synonyms from the two labs summed); all 24 samples used, raw counts, no rarefaction."],
"exclusions":[],"issues":["Labs used different names for the same species (e.g. Globigerinoides sacculifer/Trilobatus sacculifer, G. tenellus/Globoturborotalita tenella, N. pachyderma dextral/sinistral renamed to N. incompta/N. pachyderma); merged under current taxonomy."],
"summary":"Merged synonyms, counted species with >=1 specimen, mean Bray-Curtis over all 276 sample pairs on raw counts."},open("answer.json","w"),indent=1)
