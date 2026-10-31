"""Run with python analysis.py; uses the standard library only.

Exact rational Bray-Curtis distances and sums of squares; exhaustive label
allocations. JSON numbers are converted to Python floats without rounding.
"""
import csv
import hashlib
import itertools
import json
import math
import platform
import random
from fractions import Fraction as Q
from pathlib import Path

SEED = 20261031
REQUESTED_PERMUTATIONS = 999
random.seed(SEED)

root = Path(__file__).resolve().parent
with (root / 'counts.tsv').open(newline='') as f:
    rows = list(csv.reader(f, delimiter='\t'))
assert rows[0][0] == '.'
ids = [r[0] for r in rows[1:]]
counts = [[int(v) for v in r[1:]] for r in rows[1:]]
assert len(ids) == len(set(ids))
assert all(len(x) == len(rows[0])-1 and min(x) >= 0 and sum(x) > 0 for x in counts)
with (root / 'samples.csv').open(newline='') as f:
    metadata = list(csv.DictReader(f))
assert len(metadata) == len({r['sample_id'] for r in metadata})
assert set(ids) == {r['sample_id'] for r in metadata}
assert len(metadata) == len({r['site_id'] for r in metadata})
by_id = {r['sample_id']: r for r in metadata}
labels = [by_id[s]['facies'] for s in ids]
assert set(labels) == {'reef', 'lagoon'}
n = len(ids)
d2 = [[Q(sum(abs(a-b) for a,b in zip(counts[i], counts[j])),
         sum(counts[i])+sum(counts[j]))**2 for j in range(n)] for i in range(n)]
ss_total = sum(d2[i][j] for i in range(n) for j in range(i+1,n)) / n
df_between, df_within = 1, n-2

def statistics(reef):
    reef = set(reef)
    groups = [sorted(reef), [i for i in range(n) if i not in reef]]
    ss_within = sum(sum(d2[i][j] for pos,i in enumerate(g) for j in g[pos+1:]) / len(g)
                    for g in groups)
    ss_between = ss_total - ss_within
    pseudo_f = (ss_between / df_between) / (ss_within / df_within)
    return pseudo_f, ss_within, ss_between, groups

observed = [i for i,label in enumerate(labels) if label == 'reef']
pseudo_f, ss_within, ss_between, groups = statistics(observed)
allocation_count = math.comb(n, len(observed))
assert allocation_count <= REQUESTED_PERMUTATIONS
permuted = [statistics(g)[0] for g in itertools.combinations(range(n), len(observed))]
extreme = sum(f >= pseudo_f for f in permuted)
p_value = Q(extreme, allocation_count)

# Squared distance to a centroid from the original squared dissimilarities:
# mean_j d(i,j)^2 - sum_{j<k} d(j,k)^2 / m^2.
# These particular data are Euclidean: both taxon counts total 100 per site,
# so Bray-Curtis is exactly |taxon1_i/100 - taxon1_j/100|.
# Verify that embedding and calculate exact rational centroid distances.
assert all(sum(row) == 100 for row in counts)
assert all(d2[i][j] == Q(counts[i][0]-counts[j][0],100)**2
           for i in range(n) for j in range(n))
means = {}
individual_distances = {}
for name,g in zip(['reef', 'lagoon'], groups):
    centroid = sum(Q(counts[i][0],100) for i in g) / len(g)
    distances = [abs(Q(counts[i][0],100)-centroid) for i in g]
    correction = sum(d2[i][j] for pos,i in enumerate(g) for j in g[pos+1:]) / len(g)**2
    assert all(dist**2 == sum(d2[i][j] for j in g)/len(g)-correction
               for i,dist in zip(g,distances))
    means[name] = float(sum(distances)/len(g))
    individual_distances[name] = {ids[i]: str(dist) for i,dist in zip(g,distances)}

answer = {
    'status': 'completed',
    'results': {
        'n': n, 'pseudo_f': float(pseudo_f),
        'r_squared': float(ss_between/ss_total), 'p_value': float(p_value),
        'ss_total': float(ss_total), 'ss_within': float(ss_within),
        'ss_between': float(ss_between), 'df_between': df_between,
        'df_within': df_within, 'group_mean_centroid_distance': means,
        'claim_supported': 0,
    },
    'assumptions': [
        'As specified in dictionary.md, each row is a distinct independent site sampled once; facies labels are freely exchangeable under the null, with no blocks, repeated measures, covariates or nested subsamples.',
        'The one-way PERMANOVA uses Bray-Curtis dissimilarities on the untransformed, unnormalised integer specimen counts.'
    ],
    'exclusions': [],
    'issues': [
        'No data problems were found: sample IDs are unique and match between files, site IDs are unique, and counts are nonnegative integers with no missing or empty samples. Metadata were matched by sample_id.',
        'The groups are unequal in size (4 reef, 6 lagoon) and have very different descriptive within-facies spreads. PERMANOVA can reflect location and/or dispersion differences, so it cannot establish the draft interpretation.',
        'There are only 210 distinct allocations preserving group sizes. All 210, including the observed allocation, were enumerated instead of drawing 999 permutations; the exact upper-tail p-value includes ties, with no Monte Carlo plus-one adjustment. Seed 20261031 was set but does not affect exhaustive enumeration.'
    ],
    'summary': (
        f'Analysed all {n} independent sites with a one-way Bray-Curtis PERMANOVA. '
        f'The exact permutation p-value is {float(p_value)} ({extreme}/{allocation_count} allocations), '
        'significant at the conventional 0.05 level. The full claim is unsupported (claim_supported=0). '
        'Although the observed facies centroids differ, the test does not isolate a centroid-location effect '
        'from dispersion: reef and lagoon mean centroid distances are '
        f'{means["reef"]} and {means["lagoon"]}, respectively. '
        'These descriptive distances show unequal spread but do not test dispersion significance or establish '
        'that spread caused the PERMANOVA result; they prevent ruling it out. '
        'No bias adjustment, distance correction, aggregation or dispersion significance test was used. '
        'For these equal-total two-taxon data, Bray-Curtis is exactly a Euclidean distance on taxon-1 count/100, '
        'allowing uncorrected centroid distances without negative eigenvalue ambiguity. '
        'Rerun with python analysis.py; provenance.json records input hashes, exact fractions and permutation details.'
    ),
}
# Validate the supplied contract with standard-library checks (no installation).
schema = json.loads((root/'answer.schema.json').read_text())
assert set(answer) == set(schema['required']) == set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'], dict)
assert all(isinstance(answer[k], list) and all(isinstance(v,str) for v in answer[k])
           for k in ['assumptions','issues'])
assert isinstance(answer['summary'], str)
assert answer['exclusions'] == []
assert set(answer['results']) == {'n','pseudo_f','r_squared','p_value','ss_total',
    'ss_within','ss_between','df_between','df_within','group_mean_centroid_distance','claim_supported'}
assert ss_total == ss_within + ss_between
(root/'answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False)+'\n')
provenance = {
    'command': 'python analysis.py', 'python_version': platform.python_version(),
    'input_sha256': {p: hashlib.sha256((root/p).read_bytes()).hexdigest()
                     for p in ['task.md','dictionary.md','counts.tsv','samples.csv','answer.schema.json','analysis.py']},
    'seed': SEED, 'requested_permutations': REQUESTED_PERMUTATIONS,
    'enumerated_allocations_including_observed': allocation_count,
    'allocations_at_least_as_extreme': extreme,
    'exact_results': {k: str(v) for k,v in {'pseudo_f':pseudo_f, 'r_squared':ss_between/ss_total,
        'p_value':p_value,'ss_total':ss_total,'ss_within':ss_within,'ss_between':ss_between}.items()},
    'centroid_distances_exact': individual_distances,
    'schema_validation': 'All supplied schema constraints checked using standard-library assertions.'
}
(root/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
print(json.dumps(answer['results'], indent=2))
