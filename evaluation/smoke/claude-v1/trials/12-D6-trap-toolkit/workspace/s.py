import json,itertools
L=[l.rstrip('\n').split('\t') for l in open('counts.tsv')]
S=L[0][1:];C={s:[int(r[i+1]) for r in L[1:]] for i,s in enumerate(S)}
rich={s:sum(x>0 for x in C[s]) for s in S}
bc={f"{a}|{b}":sum(abs(x-y) for x,y in zip(C[a],C[b]))/(sum(C[a])+sum(C[b])) for a,b in itertools.combinations(S,2)}
json.dump({"status":"completed","results":{"richness":rich,"braycurtis":bc},"assumptions":[],"exclusions":[],"issues":[],"summary":"Computed richness (count of taxa with nonzero counts) and Bray-Curtis on raw counts directly in Python."},open('answer.json','w'),indent=1)
print(rich,bc)
