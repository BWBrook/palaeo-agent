import pandas as pd, numpy as np, json
from scipy.spatial.distance import pdist
s=pd.read_csv('samples.csv').set_index('sample_id')
c=pd.read_csv('counts.tsv',sep='\t').set_index('sample')
c=c.loc[s.index]
X=c.copy().astype(float)
issues=[]
for i in s.index:
    if s.loc[i,'value_type']!='count':
        X.loc[i]=np.round(c.loc[i]*s.loc[i,'n_counted']/100.0)
    else:
        if abs(c.loc[i].sum()-s.loc[i,'n_counted'])>0.5:
            issues.append(f"{i}: row sum {c.loc[i].sum()} != n_counted {s.loc[i,'n_counted']}")
pct=s.index[s.value_type!='count']
issues.append("Percent rows sums (min,max): %.2f,%.2f"%(c.loc[pct].sum(1).min(),c.loc[pct].sum(1).max()))
d=pdist(X.values,'braycurtis')
res=float(d.mean())
ans=dict(status="completed_with_assumptions",results=dict(mean_bray_curtis=res),
assumptions=["1998 samples are published percentages (counts not archived); converted to approximate counts as percent/100*n_counted, rounded to integers, so all samples are on the count scale.",
"SR325 (n=47, low yield but counted in full) retained."],
exclusions=[],
issues=["Mixed value types: 1998 rows are relative %, 2024 rows raw counts; Bray-Curtis on raw values would be invalid without conversion. Reconstructed counts carry rounding error."]+issues+["Bray-Curtis on counts depends on differing sample totals (47 to 415 specimens)."],
summary="Converted percent rows to counts via n_counted, computed Bray-Curtis for all 276 pairs of 24 samples, and averaged.")
json.dump(ans,open('answer.json','w'),indent=1)
