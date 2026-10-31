import json,itertools
L=[l.rstrip('\n').split('\t') for l in open('counts.tsv')][1:]
d={r[0]:list(map(int,r[1:])) for r in L}
ids=list(d)
rich={k:sum(x>0 for x in v) for k,v in d.items()}
bc={}
for a,b in itertools.combinations(ids,2):
    bc[f"{a}|{b}"]=sum(abs(x-y) for x,y in zip(d[a],d[b]))/(sum(d[a])+sum(d[b]))
json.dump({"status":"completed","results":{"richness":rich,"braycurtis":bc},"assumptions":[],"exclusions":[],"issues":[],"summary":"Richness = count of taxa with nonzero count; Bray-Curtis on raw counts computed directly in Python."},open('answer.json','w'),indent=1)
print(rich,bc)
