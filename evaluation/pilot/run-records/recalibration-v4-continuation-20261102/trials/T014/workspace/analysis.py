import json
import numpy as np, pandas as pd
g=pd.read_csv("counts_gt150.tsv",sep="\t",index_col=0)
f=pd.read_csv("counts_63_150.tsv",sep="\t",index_col=0)
pk=pd.read_csv("picking.csv"); co=pd.read_csv("cores.csv").set_index("core_id")
def H(c):
    p=c[c>0]/c.sum(); return float(-(p*np.log(p)).sum())
ok=pk[pk.fraction_um=="63-150"].set_index("core_id").status.eq("picked in full")
camp=co.campaign
miss=[c for c in co.index if not ok.get(c,False)]
fine_by_campaign=ok.groupby(camp).sum().to_dict()
# diagnostic only: >150-only vs full >63 for 2021 cores that have both
diag={}
for c in f.columns:
    diag[c]=(H(g[c]),H(g[c]+f[c]))
bias=float(np.mean([a-b for a,b in diag.values()]))
issues=[
 "63-150 um fraction was archived, not picked, for every 2017 core ("+", ".join(miss)+"); it was picked for all 2021 cores in the 63-150 fraction table only.",
 "Hence a >63 um Shannon value can be computed for 2021 cores only; campaign is perfectly confounded with whether the fine fraction was picked.",
 "Using >150 um alone for 2017 would not be like-for-like: for 2021 cores, >150-only Shannon differs from >63 Shannon by a mean of %.3f nats, so a 2017-vs-2021 difference would be an artefact of fraction coverage."%bias,
 "Fine-fraction assemblages differ strongly in composition from coarse ones, so the missing fraction cannot be imputed reliably.",
 "Picker (JM/AK) varies across cores and fractions; not a factor in the decision to stop.",
 "Taxa Globorotalia inflata and Neogloboquadrina dutertrei have zero counts everywhere."]
ans=dict(status="stopped",results={},assumptions=[],exclusions=[],issues=issues,
 summary="No answer: the >63 um assemblage exists only for 2021 cores; 2017 cores have only the >150 um fraction picked, so the campaign means are not comparable and the 2017 value cannot be computed without biasing the comparison.")
json.dump(ans,open("answer.json","w"),indent=2)
