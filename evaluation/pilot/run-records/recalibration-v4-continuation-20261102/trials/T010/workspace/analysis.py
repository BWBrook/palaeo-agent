import json
import numpy as np, pandas as pd
from scipy.spatial.distance import pdist, squareform

c = pd.read_csv('counts.tsv', sep='\t').set_index('lab_number')
reg = pd.read_csv('register.csv').set_index('lab_number')
cores = pd.read_csv('cores.csv').set_index('core_id')

# splits of one core's residue are not independent units: pool counts per core
pooled = c.groupby(reg.loc[c.index, 'core_id']).sum()
pooled = pooled.loc[:, pooled.sum() > 0]
rel = pooled.div(pooled.sum(axis=1), axis=0)
g = cores.loc[rel.index, 'zone'].values

D = squareform(pdist(rel.values, 'braycurtis'))
n = len(g)
def ss(idx):
    d = D[np.ix_(idx, idx)]
    return (d**2).sum() / 2 / len(idx)
sst = ss(np.arange(n))
ssw = sum(ss(np.where(g == k)[0]) for k in np.unique(g))
a = len(np.unique(g))
F = ((sst - ssw) / (a - 1)) / (ssw / (n - a))
R2 = (sst - ssw) / sst

out = {
    "status": "completed_with_assumptions",
    "results": {"pseudo_f": float(F), "r_squared": float(R2), "n": int(n)},
    "assumptions": ["Sampling unit is the core (each core is one site); multiple lab numbers per core are splits of the same residue and were pooled by summing counts before computing relative abundances.",
                    "Taxa with zero counts in all samples dropped (no effect on Bray-Curtis)."],
    "exclusions": [],
    "issues": ["28 lab numbers map to 14 cores (splits a/b/c); treating them as separate units would be pseudoreplication.",
               "lab_log remarks (re-labelling, re-counts with unchanged counts) did not indicate any data change."],
    "summary": "One-way PERMANOVA (inner vs outer) on Bray-Curtis of relative abundances of core-pooled counts, 14 cores."
}
json.dump(out, open('answer.json', 'w'), indent=2)
