import csv,json,itertools
rows=list(csv.reader(open('assemblages.tsv'),delimiter='\t'))
d={r[0]:[float(x) for x in r[1:]] for r in rows[1:]}
cnt={};info={}
for s,v in d.items():
    c=[n for n in range(1,3000) if all(abs(round(k/n*100,2)-p)<1e-9 for p in v for k in [round(p*n/100)])]
    info[s]=c[:3]
    n=c[0];cnt[s]=[round(p*n/100) for p in v]
print(info,cnt)
res={}
for a,b in itertools.combinations(d,2):
    x,y=cnt[a],cnt[b]
    res[f"{a}|{b}"]=1-2*sum(map(min,x,y))/(sum(x)+sum(y))
print(res)
json.dump({"status":"completed_with_assumptions","results":{"braycurtis":res},
"assumptions":["Input is percentages, not raw counts; raw counts were reconstructed by finding the smallest sample total N for which every percentage equals round(100*k/N,2) with integer k. Bray-Curtis was computed on those counts, unstandardised."],
"exclusions":[],"issues":["assemblages.tsv holds rounded percentages, not the raw specimen counts the task asks for. Reconstructed totals: "+str({s:i[0] for s,i in info.items()})+". Candidate totals are not guaranteed unique. The palaeo_agent package only supports RMA, so it was not used."],
"summary":"Reconstructed integer counts from percentages and computed pairwise Bray-Curtis dissimilarities."},open('answer.json','w'),indent=1)
