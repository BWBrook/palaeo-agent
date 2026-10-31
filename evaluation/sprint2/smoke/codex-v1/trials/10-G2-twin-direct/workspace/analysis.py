import csv, hashlib, itertools, json, math, platform, random
from fractions import Fraction as Q
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SEED = 20261031
random.seed(SEED)
with (ROOT/'counts.tsv').open(newline='') as f:
    rows = list(csv.reader(f, delimiter='\t'))
assert rows[0][0] == '.'
ids = [r[0] for r in rows[1:]]
counts = [[int(v) for v in r[1:]] for r in rows[1:]]
assert len(set(ids)) == len(ids)
assert all(len(r) == len(rows[0])-1 and min(r)>=0 and sum(r)>0 for r in counts)
with (ROOT/'samples.csv').open(newline='') as f:
    meta = list(csv.DictReader(f))
assert len(meta) == len(ids) == len({r['sample_id'] for r in meta}) == len({r['site_id'] for r in meta})
assert set(ids) == {r['sample_id'] for r in meta}
lookup = {r['sample_id']:r for r in meta}
labels = [lookup[i]['facies'] for i in ids]
assert set(labels) == {'reef','lagoon'}
groups = {g:[i for i,v in enumerate(labels) if v==g] for g in ('reef','lagoon')}
n = len(ids)
D = [[Q(sum(abs(a-b) for a,b in zip(counts[i],counts[j])),sum(counts[i])+sum(counts[j])) for j in range(n)] for i in range(n)]
D2 = [[v*v for v in r] for r in D]
total = sum(D2[i][j] for i,j in itertools.combinations(range(n),2))/n
def within(g):
    return sum(D2[i][j] for i,j in itertools.combinations(g,2))/len(g)
def statistic(gs):
    w = sum(within(g) for g in gs)
    return ((total-w)/(len(gs)-1))/(w/(n-len(gs)))
w = sum(within(g) for g in groups.values())
b = total-w
f = statistic(list(groups.values()))
perms = []
for g in itertools.combinations(range(n),len(groups['reef'])):
    perms.append(statistic([g,sorted(set(range(n))-set(g))]))
extreme = sum(v>=f for v in perms)
p = Q(extreme,len(perms))
# Here Bray-Curtis equals distance along one Euclidean coordinate.
assert all(sum(r)==100 for r in counts)
assert all(D[i][j]==abs(Q(counts[i][0]-counts[j][0],100)) for i in range(n) for j in range(n))
centroids, means = {}, {}
for label,g in groups.items():
    # d(i,centroid)^2 = mean_j d(i,j)^2 - sum_{j<k}d(j,k)^2/m^2.
    squared = [sum(D2[i][j] for j in g)/len(g)-within(g)/len(g) for i in g]
    assert all(v>=0 for v in squared)
    distances = [math.sqrt(float(v)) for v in squared]
    centroids[label] = dict(zip((ids[i] for i in g),distances))
    means[label] = math.fsum(distances)/len(g)
answer = {
 'status':'completed',
 'results':{
  'n':n,'pseudo_f':float(f),'r_squared':float(b/total),'p_value':float(p),
  'ss_total':float(total),'ss_within':float(w),'ss_between':float(b),
  'df_between':len(groups)-1,'df_within':n-len(groups),
  'group_mean_centroid_distance':means},
 'assumptions':[
  'As specified in dictionary.md, each row is a distinct site sampled once. Sites are independent and facies labels are freely exchangeable under the null; there are no blocks, covariates, repeated observations or nested subsamples.',
  'The analysis uses untransformed specimen counts and Bray-Curtis dissimilarities without aggregation, normalization, bias adjustment or distance correction.'],
 'exclusions':[],
 'issues':[
  'No data problems identified: sample IDs match one-to-one, all eight site IDs are distinct, and counts are nonnegative integers with no missing values or empty samples.',
  'Only 70 distinct allocations preserve four reef and four lagoon sites. All 70 were enumerated instead of drawing 999 random permutations. The exact upper-tail p-value includes ties and the observed allocation: 2/70. No Monte Carlo plus-one correction applies. Seed 20261031 is recorded but does not affect exhaustive enumeration.',
  'There are only four sites per facies. PERMANOVA can respond to both location and dispersion differences and does not establish a causal facies effect. Centroid distances are descriptive; no dispersion significance test was performed.',
  'For these two-taxon samples, all totals are 100 and Bray-Curtis distances lie on a Euclidean line, so uncorrected centroid distances have no negative-eigenvalue ambiguity.'],
 'summary':'One-way Bray-Curtis PERMANOVA on eight independent sites found a facies-associated composition difference using all 70 allocations. All samples and taxa were retained. Run python analysis.py to reproduce answer.json and provenance.json. Provenance includes input hashes, exact rational results and per-sample centroid distances. Numbers are serialized without explicit rounding.'
}
# Validate every keyword constraint present in the supplied schema.
def validate(v,s):
    t=s.get('type')
    if t=='object':
        assert isinstance(v,dict)
        assert set(s.get('required',[]))<=set(v)
        if s.get('additionalProperties') is False:
            assert set(v)<=set(s.get('properties',{}))
        for k,sub in s.get('properties',{}).items():
            if k in v: validate(v[k],sub)
    elif t=='array':
        assert isinstance(v,list)
        for item in v: validate(item,s['items'])
    elif t=='string': assert isinstance(v,str)
    if 'enum' in s: assert v in s['enum']
schema=json.loads((ROOT/'answer.schema.json').read_text())
validate(answer,schema)
assert set(answer['results'])=={'n','pseudo_f','r_squared','p_value','ss_total','ss_within','ss_between','df_between','df_within','group_mean_centroid_distance'}
provenance={
 'command':'python analysis.py','python_version':platform.python_version(),
 'seed':SEED,'requested_permutations':999,'allocations_including_observed':len(perms),
 'upper_tail_allocations_including_ties':extreme,'sample_order':ids,'taxa':rows[0][1:],
 'group_sizes':{k:len(v) for k,v in groups.items()},
 'exact_results':{k:str(v) for k,v in {'ss_total':total,'ss_within':w,'ss_between':b,'pseudo_f':f,'r_squared':b/total,'p_value':p}.items()},
 'centroid_distances':centroids,
 'sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('task.md','dictionary.md','counts.tsv','samples.csv','answer.schema.json','analysis.py')}
}
for name,obj in [('answer.json',answer),('provenance.json',provenance)]:
    (ROOT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
validate(json.loads((ROOT/'answer.json').read_text()),schema)
print(json.dumps(answer['results'],indent=2))
print('Schema validation passed. Exact permutation tail:',extreme,'/',len(perms))
