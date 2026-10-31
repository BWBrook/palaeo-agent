import json,itertools
L=[l.rstrip('\n').split('\t') for l in open('counts.tsv')]
d={r[0]:list(map(float,r[1:])) for r in L[1:]}
ids=list(d)
r={k:sum(1 for x in v if x>0) for k,v in d.items()}
b={}
for a,c in itertools.combinations(ids,2):
    b[a+'|'+c]=1-2*sum(min(x,y) for x,y in zip(d[a],d[c]))/(sum(d[a])+sum(d[c]))
json.dump({"status":"completed","results":{"richness":r,"braycurtis":b},"assumptions":[],"exclusions":[],"issues":[],"summary":"Richness = taxa with count>0; Bray-Curtis on raw counts."},open('answer.json','w'),indent=1)
