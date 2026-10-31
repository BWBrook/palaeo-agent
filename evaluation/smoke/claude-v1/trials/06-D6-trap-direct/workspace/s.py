import pandas as pd,json,itertools
d=pd.read_csv('counts.tsv',sep='\t',index_col=0)
r={c:int((d[c]>0).sum()) for c in d}
b={}
for a,c in itertools.combinations(d.columns,2):
    b[f"{a}|{c}"]=float(abs(d[a]-d[c]).sum()/(d[a]+d[c]).sum())
json.dump({"status":"completed","results":{"richness":r,"braycurtis":b},"assumptions":[],"exclusions":[],"issues":[],"summary":"Richness = taxa with count>0; Bray-Curtis on raw counts."},open('answer.json','w'),indent=1)
