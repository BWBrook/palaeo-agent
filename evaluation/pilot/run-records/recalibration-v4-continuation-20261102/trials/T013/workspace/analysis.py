import json
import numpy as np, pandas as pd
a=pd.read_csv("counts_gt150.tsv",sep="\t",index_col=0)
b=pd.read_csv("counts_63_150.tsv",sep="\t",index_col=0)
cores=pd.read_csv("cores.csv").set_index("core_id")
def H(v):
    v=np.asarray(v,float);p=v[v>0]/v.sum();return float(-(p*np.log(p)).sum())
def mean(df,camp):
    ids=[c for c in df.columns if cores.campaign[c]==camp]
    return float(np.mean([H(df[c]) for c in ids])),len(ids)
comb=a.add(b,fill_value=0)[b.columns]
g17=mean(a,2017);g21=mean(a,2021);c21=mean(comb,2021)
missing=[c for c in a.columns if c not in b.columns]
msg=("The >63 um assemblage is not available for 2017: all 10 2017 cores (%s) have the 63-150 um fraction archived, not picked. "
 "Only the 2021 cores (9) have both fractions. Like-for-like >150 um mean Shannon: 2017=%r (n=%d), 2021=%r (n=%d). "
 "2021 >63 um combined mean=%r. Comparing 2017 >150 only with 2021 combined would confound campaign with size fraction."%(", ".join(missing),g17[0],g17[1],g21[0],g21[1],c21[0]))
ans={"status":"stopped","results":{},"assumptions":[],"exclusions":[],"issues":[msg],
"summary":"Computed per-core Shannon (ln) from the count tables. The requested 2017 >63 um value cannot be computed because the 63-150 um fraction was never picked for 2017 cores, so the campaign comparison was not made. See issues for the like-for-like >150 um values. Shannon computed directly with numpy (not via the palaeo toolkit)."}
json.dump(ans,open("answer.json","w"),indent=1)
