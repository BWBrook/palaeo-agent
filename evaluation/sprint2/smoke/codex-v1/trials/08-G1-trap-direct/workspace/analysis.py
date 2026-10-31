import csv, hashlib, itertools, json, math, platform
from fractions import Fraction
from pathlib import Path
root = Path(__file__).resolve().parent
with (root / "counts.tsv").open(newline="") as f:
    rows = list(csv.reader(f, delimiter="\t"))
assert rows[0][0] == "."
ids = [r[0] for r in rows[1:]]
x = [[int(v) for v in r[1:]] for r in rows[1:]]
assert len(ids) == len(set(ids)) == 8
assert all(len(r) == len(rows[0])-1 and min(r) >= 0 and sum(r)>0 for r in x)
with (root / "samples.csv").open(newline="") as f:
    records = list(csv.DictReader(f))
assert len(records) == len(ids)
meta = {r["sample_id"]:r for r in records}
assert len(meta) == len(records) and set(meta) == set(ids)
assert len({r["site_id"] for r in records}) == len(records)
labels = [meta[s]["facies"] for s in ids]
assert set(labels) == {"reef", "lagoon"}
groups = {g:[i for i,l in enumerate(labels) if l==g] for g in ("reef","lagoon")}
n = len(ids)
d = [[Fraction(sum(abs(a-b) for a,b in zip(x[i],x[j])),sum(x[i])+sum(x[j])) for j in range(n)] for i in range(n)]
d2 = [[v*v for v in row] for row in d]
st = sum(d2[i][j] for i,j in itertools.combinations(range(n),2))/n
def within(idx):
    return sum((d2[i][j] for i,j in itertools.combinations(idx,2)),Fraction(0))/len(idx)
def stats(a):
    b = [i for i in range(n) if i not in a]
    sw = within(a)+within(b)
    sb = st-sw
    return sw,sb,sb/(sw/(n-2))
sw,sb,F = stats(groups["reef"])
allocations = list(itertools.combinations(range(n),len(groups["reef"])))
extreme = sum(stats(a)[2]>=F for a in allocations)
p = Fraction(extreme,len(allocations))
means = {}
for g,idx in groups.items():
    m = len(idx)
    squared = [sum(d2[i][j] for j in idx)/m-within(idx)/m for i in idx]
    assert all(v>=0 for v in squared)
    means[g] = sum(math.sqrt(v) for v in squared)/m
results = dict(n=n,pseudo_f=float(F),r_squared=float(sb/st),p_value=float(p),ss_total=float(st),ss_within=float(sw),ss_between=float(sb),df_between=1,df_within=n-2,group_mean_centroid_distance=means)
answer = {
    "status":"completed", "results":results,
    "assumptions":[
        "As specified in dictionary.md, each sample is a distinct site sampled once. Sites are independent and facies labels are freely exchangeable under the null; there are no blocks, covariates or repeated measurements.",
        "The supplied specimen counts are valid; Bray-Curtis uses untransformed counts without normalization."
    ],
    "exclusions":[],
    "issues":[
        "Metadata rows are shuffled relative to the count table. Records were joined by unique sample_id, preserving count-table order. All eight records matched, and site IDs were distinct.",
        "No missing values, negative counts, empty samples or duplicate sample IDs were found; all samples and taxa were retained.",
        "Only 70 distinct labeled allocations preserve group sizes (four reef and four lagoon). All were enumerated, including the observed allocation, instead of drawing 999 random permutations. The exact p-value is 2/70, with no Monte Carlo plus-one correction. Requested seed 20261031 is recorded but unused because enumeration is deterministic.",
        "Centroid distances are descriptive arithmetic means without bias adjustment, distance correction or a dispersion significance test. Equal-total two-taxon counts give Euclidean Bray-Curtis distances here, so negative-axis handling is unnecessary.",
        "This is a facies association, not evidence of causation. Four sites per group limit inference and exact p-value resolution. PERMANOVA alone cannot generally distinguish location and dispersion effects."
    ],
    "summary":"One-way PERMANOVA on raw-count Bray-Curtis distances used eight independent sites, four per facies. Exact enumeration of 70 allocations found pseudo-F = 1470 and p = 2/70. No data were excluded. Rerun with python analysis.py; provenance.json records input hashes, exact intermediate values and software."
}
(root/"answer.json").write_text(json.dumps(answer,indent=2,allow_nan=False)+"\n")
provenance = {
    "command":"python analysis.py", "python_version":platform.python_version(),
    "seed_requested":20261031,"permutations_requested":999,
    "allocations_enumerated":len(allocations),"extreme_allocations":extreme,
    "sample_order":ids,"facies_in_sample_order":labels,"taxa":rows[0][1:],
    "exact_values":{k:str(v) for k,v in dict(ss_total=st,ss_within=sw,ss_between=sb,pseudo_f=F,r_squared=sb/st,p_value=p).items()},
    "sha256":{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ["task.md","dictionary.md","answer.schema.json","counts.tsv","samples.csv","analysis.py"]},
    "method":"SS_total=sum(i<j)d_ij^2/n; SS_within=sum_g sum(i<j in g)d_ij^2/n_g; SS_between=SS_total-SS_within; F=(SS_between/1)/(SS_within/6). Exact Fraction arithmetic determines permutation ties. Squared centroid distances use mean_j d_ij^2 minus sum(j<k)d_jk^2/n_g^2. All reported numbers use Python float serialization without rounding."
}
(root/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
print(json.dumps(results,indent=2))
print(provenance["exact_values"])
