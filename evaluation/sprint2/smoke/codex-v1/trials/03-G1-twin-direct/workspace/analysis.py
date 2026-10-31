"""Rerun: python analysis.py. Exact one-way Bray-Curtis PERMANOVA."""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import platform
import numpy as np

BASE = Path(__file__).resolve().parent
SEED = 20261031
REQUESTED = 999
rng = np.random.default_rng(SEED)
with (BASE / 'counts.tsv').open(newline='') as f:
    rows = list(csv.reader(f, delimiter='\t'))
assert rows[0][0] == '.'
ids = [r[0] for r in rows[1:]]
x = np.array([[int(v) for v in r[1:]] for r in rows[1:]], dtype=float)
with (BASE / 'samples.csv').open(newline='') as f:
    metadata = list(csv.DictReader(f))
assert len(set(ids)) == len(ids)
assert len({r['sample_id'] for r in metadata}) == len(metadata)
assert set(ids) == {r['sample_id'] for r in metadata}
lookup = {r['sample_id']: r for r in metadata}
meta = [lookup[s] for s in ids]
assert len({r['site_id'] for r in meta}) == len(ids)
assert np.all(np.isfinite(x)) and np.all(x >= 0)
assert np.all(x.sum(axis=1) > 0)
labels = np.array([r['facies'] for r in meta])
groups = ['reef', 'lagoon']
assert set(labels) == set(groups)
n = len(ids)
d = np.abs(x[:, None, :] - x[None, :, :]).sum(axis=2) / (x[:, None, :] + x[None, :, :]).sum(axis=2)
d2 = d ** 2
ss_total = np.triu(d2, 1).sum() / n

def within(indices):
    return np.triu(d2[np.ix_(indices, indices)], 1).sum() / len(indices)

def statistic(first):
    second = np.array([i for i in range(n) if i not in set(first)], dtype=int)
    ssw = within(first) + within(second)
    ssb = ss_total - ssw
    return (ssb / (len(groups) - 1)) / (ssw / (n - len(groups))), ssw, ssb

observed = np.flatnonzero(labels == 'reef')
f_obs, ss_within, ss_between = statistic(observed)
allocations = list(itertools.combinations(range(n), len(observed)))
f_perm = np.array([statistic(np.array(a, dtype=int))[0] for a in allocations])
# Include ties differing only by floating-point error.
tolerance = 1e-12 * max(1.0, abs(float(f_obs)))
exceedances = int(np.count_nonzero(f_perm >= f_obs - tolerance))
p = exceedances / len(allocations)
centroid_means = {}
for group in groups:
    idx = np.flatnonzero(labels == group)
    block = d2[np.ix_(idx, idx)]
    # Gower centroid identity, with no distance or bias correction.
    squared = block.mean(axis=1) - block.mean() / 2
    assert np.all(squared >= -1e-12)
    centroid_means[group] = float(np.sqrt(np.maximum(squared, 0)).mean())
h = np.eye(n) - np.ones((n,n)) / n
eigenvalues = np.linalg.eigvalsh(-0.5 * h @ d2 @ h)
assert eigenvalues.min() >= -1e-12
answer = {
    'status': 'completed',
    'results': {
        'n': n,
        'pseudo_f': float(f_obs),
        'r_squared': float(ss_between / ss_total),
        'p_value': p,
        'ss_total': float(ss_total),
        'ss_within': float(ss_within),
        'ss_between': float(ss_between),
        'df_between': len(groups) - 1,
        'df_within': n - len(groups),
        'group_mean_centroid_distance': centroid_means,
    },
    'assumptions': [
        'As stated in dictionary.md, each count row represents a distinct independent site sampled once; facies labels are freely exchangeable under the null, with no blocks, covariates, repeated measures or nested subsamples.',
        'Bray-Curtis dissimilarities use untransformed, unnormalised specimen counts. The test assesses facies association and does not establish causation.'
    ],
    'exclusions': [],
    'issues': [
        'No data problems identified: all eight unique sample IDs match one-to-one across files, each has a unique site ID, and all counts are nonnegative integers with no missing values or empty samples.',
        'All 70 distinct allocations preserving the 4:4 group sizes were enumerated instead of sampling 999 permutations. The exact upper-tail p-value includes the observed allocation and its label-swapped equivalent; no Monte Carlo plus-one adjustment is applied.',
        'Centroid distances are descriptive and use uncorrected Bray-Curtis geometry without bias adjustment. These distances are Euclidean to numerical precision. No dispersion significance test was performed; PERMANOVA alone cannot generally distinguish location from dispersion effects.',
        'The small sample size limits inference and exact permutation p-value resolution. Seed 20261031 is recorded; exhaustive enumeration does not consume random numbers.'
    ],
    'summary': 'One-way PERMANOVA of eight independent sites (four reef, four lagoon), using untransformed counts and Bray-Curtis dissimilarities, found a facies-associated difference in composition. All 70 allocations were enumerated, with 2 at least as extreme as observed. No samples were aggregated or excluded. Rerun with python analysis.py; provenance.json records input hashes, versions and permutation details.'
}
# Validate this supplied contract using the standard library (no installation).
schema = json.loads((BASE / 'answer.schema.json').read_text())
assert set(answer) == set(schema['required']) == set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'], dict)
for key in ['assumptions', 'issues']:
    assert isinstance(answer[key], list) and all(isinstance(v, str) for v in answer[key])
assert isinstance(answer['summary'], str)
assert isinstance(answer['exclusions'], list)
for exclusion in answer['exclusions']:
    assert set(exclusion) == {'id', 'reason'}
    assert all(isinstance(v, str) for v in exclusion.values())
assert set(answer['results']) == {'n', 'pseudo_f', 'r_squared', 'p_value', 'ss_total', 'ss_within', 'ss_between', 'df_between', 'df_within', 'group_mean_centroid_distance'}
(BASE / 'answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
provenance = {
    'command': 'python analysis.py',
    'python_version': platform.python_version(),
    'numpy_version': np.__version__,
    'seed': SEED,
    'requested_permutations': REQUESTED,
    'method': 'exhaustive allocations preserving group sizes',
    'allocations_evaluated': len(allocations),
    'upper_tail_count': exceedances,
    'tie_tolerance': tolerance,
    'sample_order': ids,
    'taxa': rows[0][1:],
    'distance_gram_eigenvalues': eigenvalues.tolist(),
    'sha256': {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest() for name in ['task.md', 'dictionary.md', 'counts.tsv', 'samples.csv', 'answer.schema.json', 'analysis.py']}
}
(BASE / 'provenance.json').write_text(json.dumps(provenance, indent=2, allow_nan=False) + '\n')
print(json.dumps(answer['results'], indent=2))
print('answer.json validated against answer.schema.json')
