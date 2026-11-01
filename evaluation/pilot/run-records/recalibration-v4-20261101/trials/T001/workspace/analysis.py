import pandas as pd, numpy as np, json
from itertools import combinations
c=pd.read_csv('counts.tsv',sep='\t').set_index('taxon')
t=pd.read_csv('taxonomy.csv').set_index('name_as_recorded')
assert set(c.index)<=set(t.index)
g=c.groupby(c.index.map(lambda n:t.loc[n,'current_name'].split()[0])).sum()
g=g[g.sum(axis=1)>0]
X=g.T.values.astype(float)
d=[np.abs(a-b).sum()/(a+b).sum() for a,b in combinations(X,2)]
res={"mean_bray_curtis":float(np.mean(d)),"n_genera":int(g.shape[0])}
ans={"status":"completed_with_assumptions","results":res,
"assumptions":["Genus = first word of current_name in taxonomy.csv (WoRMS 2025-10), so renamed species are assigned to their current genus.","Bray-Curtis on raw counts, unweighted mean over all 253 sample pairs; all 23 samples kept."],
"exclusions":[],
"issues":["Sample N05 has very low counts (low yield per lab log); kept since raw counts were requested, but it inflates dissimilarities.","Several 1987 names are outdated (e.g. Globigerina pachyderma, G. quinqueloba, Globigerinoides sacculifer) and were remapped, changing genus composition."],
"summary":"Mapped recorded names to current genera, summed counts, computed pairwise Bray-Curtis on raw counts and averaged."}
json.dump(ans,open('answer.json','w'),indent=1)
