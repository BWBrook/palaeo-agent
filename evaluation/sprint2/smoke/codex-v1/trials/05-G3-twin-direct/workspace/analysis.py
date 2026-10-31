"""Rerun: python analysis.py. Uses standard library only; no data changes.

Exact rational Bray-Curtis, sums of squares, F and permutation comparisons.
Centroid squared distance = mean_j(d_ij^2) - SS_group/n_group.
All totals are 100 and there are two taxa, so Bray-Curtis here equals
abs(taxon1_i-taxon1_j)/100 and is Euclidean on a line. No correction is needed.
"""
import csv
import hashlib
import itertools
import json
import math
import random
from fractions import Fraction as Q
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 20261031
random.seed(SEED)
with (ROOT/'counts.tsv').open(newline='') as f:
    rows = list(csv.reader(f, delimiter='\t'))
assert rows[0][0] == '.'
taxa = rows[0][1:]
ids = [r[0] for r in rows[1:]]
assert len(set(ids)) == len(ids)
assert ids == ['S'+str(i) for i in range(1,11)]
counts = [[int(v) for v in r[1:]] for r in rows[1:]]
assert all(len(r)==len(taxa) and all(v>=0 for v in r) and sum(r)>0 for r in counts)
assert len(taxa)==2 and all(sum(r)==100 for r in counts)
with (ROOT/'samples.csv').open(newline='') as f:
    metadata = list(csv.DictReader(f))
assert len({r['sample_id'] for r in metadata})==len(metadata)
assert {r['sample_id'] for r in metadata}==set(ids)
assert len({r['site_id'] for r in metadata})==len(metadata)
lookup = {r['sample_id']:r for r in metadata}
labels = [lookup[s]['facies'] for s in ids]
assert set(labels)=={'reef','lagoon'}
n = len(ids)
d = [[Q(sum(abs(a-b) for a,b in zip(x,y)),sum(x)+sum(y)) for y in counts] for x in counts]
d2 = [[v*v for v in r] for r in d]
ss_total = sum((d2[i][j] for i,j in itertools.combinations(range(n),2)),Q(0))/n

def group_ss(group):
    return sum((d2[i][j] for i,j in itertools.combinations(group,2)),Q(0))/len(group)

def statistic(reef):
    lagoon = tuple(i for i in range(n) if i not in reef)
    within = group_ss(reef)+group_ss(lagoon)
    between = ss_total-within
    return between/(within/(n-2)), within, between

reef = tuple(i for i,l in enumerate(labels) if l=='reef')
f_obs, ss_within, ss_between = statistic(reef)
allocations = list(itertools.combinations(range(n),len(reef)))
extreme = sum(statistic(a)[0]>=f_obs for a in allocations)
p_value = Q(extreme,len(allocations))
means = {}
individual_distances = {}
for label in ['reef','lagoon']:
    group = tuple(i for i,l in enumerate(labels) if l==label)
    ss = group_ss(group)
    distances = []
    for i in group:
        squared = sum((d2[i][j] for j in group),Q(0))/len(group)-ss/len(group)
        assert squared>=0
        distance = math.sqrt(squared)
        distances.append(distance)
        individual_distances[ids[i]] = distance
    means[label] = sum(distances)/len(distances)

answer = {
    'status':'completed_with_assumptions',
    'results':{
        'n':n, 'pseudo_f':float(f_obs), 'r_squared':float(ss_between/ss_total),
        'p_value':float(p_value), 'ss_total':float(ss_total),
        'ss_within':float(ss_within), 'ss_between':float(ss_between),
        'df_between':1, 'df_within':n-2,
        'group_mean_centroid_distance':means, 'claim_supported':1
    },
    'assumptions':[
        'As stated in dictionary.md, each row is a distinct site sampled once; the 10 sites are independent sampling units and facies labels are freely exchangeable under the null, with no blocks, covariates, repeated measurements or nested subsamples.',
        'Evidence for the community difference is assessed at conventional alpha=0.05; inference is conditional on the stated exchangeability assumption and does not establish causation.'
    ],
    'exclusions':[],
    'issues':[
        'No data problems were found: sample IDs match one-to-one, site IDs are unique, and all values are nonnegative integer counts with no missing values or empty samples. All 10 samples and both taxa were retained in count-table order.',
        'Only 210 distinct allocations preserve the 4 reef and 6 lagoon group sizes. All were enumerated, including the observed allocation, instead of drawing 999 permutations. The exact upper-tail p-value is 1/210, with no extra plus-one adjustment. Seed 20261031 was set but is immaterial to enumeration.',
        'Counts were used without transformation, normalisation or aggregation. All row totals are 100; with two taxa, Bray-Curtis is Euclidean here. Centroid distances use uncorrected geometry without bias adjustment or distance correction; no dispersion significance test was performed.',
        'PERMANOVA can respond to differences in location and dispersion. Descriptive centroid distances do not isolate a pure location effect. The small sample and assumed independence and exchangeability limit inference.'
    ],
    'summary':'The exact draft claim is supported (claim_supported=1): one-way PERMANOVA using Bray-Curtis on raw counts finds a facies-associated community difference under the stated exchangeability assumption (exact p=1/210). Distances to group centroids describe within-facies spread separately and do not isolate a pure location effect. All 210 group-size-preserving allocations were evaluated. Rerun with python analysis.py; provenance.json records input hashes, exact statistics, permutation details and individual centroid distances.'
}

# Validate the supplied schema contract without installing dependencies.
schema = json.loads((ROOT/'answer.schema.json').read_text())
assert set(answer)==set(schema['required'])
assert set(answer)<=set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'],dict)
for field in ['assumptions','issues']:
    assert isinstance(answer[field],list) and all(isinstance(v,str) for v in answer[field])
assert isinstance(answer['exclusions'],list)
for exclusion in answer['exclusions']:
    assert set(exclusion)=={'id','reason'} and all(isinstance(v,str) for v in exclusion.values())
assert isinstance(answer['summary'],str)
assert set(answer['results'])=={'n','pseudo_f','r_squared','p_value','ss_total','ss_within','ss_between','df_between','df_within','group_mean_centroid_distance','claim_supported'}
(ROOT/'answer.json').write_text(json.dumps(answer,indent=2,allow_nan=False)+'\n')
provenance = {
    'command':'python analysis.py', 'seed':SEED, 'requested_permutations':999,
    'allocations_enumerated_including_observed':len(allocations),
    'allocations_at_least_as_extreme':extreme,
    'exact_rational_statistics':{k:str(v) for k,v in {'ss_total':ss_total,'ss_within':ss_within,'ss_between':ss_between,'pseudo_f':f_obs,'r_squared':ss_between/ss_total,'p_value':p_value}.items()},
    'individual_centroid_distances':individual_distances,
    'sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['task.md','dictionary.md','answer.schema.json','counts.tsv','samples.csv','analysis.py']}
}
(ROOT/'provenance.json').write_text(json.dumps(provenance,indent=2,allow_nan=False)+'\n')
print(json.dumps(answer['results'],indent=2))
print('answer.json passes supplied schema contract checks')
