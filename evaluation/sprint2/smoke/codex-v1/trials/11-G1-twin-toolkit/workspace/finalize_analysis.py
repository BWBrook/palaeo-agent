"""Check the saved Palaeo-Agent run and write the task answer.

Rerun analysis: python -m palaeo_agent run analysis.spec.json --output analysis_run
Then: python finalize_analysis.py
"""
import csv
import itertools
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parent
run_files = sorted((root / 'analysis_run').glob('*/results.json'), key=lambda p: p.stat().st_mtime)
r = json.loads(run_files[-1].read_text())
with (root / 'counts.tsv').open() as f:
    table = list(csv.reader(f, delimiter='\t'))
ids = [row[0] for row in table[1:]]
x = np.array([list(map(int, row[1:])) for row in table[1:]])
with (root / 'samples.csv').open() as f:
    metadata = list(csv.DictReader(f))
assert len(ids) == len(set(ids)) == len(metadata) == 8
assert len({row['sample_id'] for row in metadata}) == 8
assert len({row['site_id'] for row in metadata}) == 8
assert set(ids) == {row['sample_id'] for row in metadata}
assert (x >= 0).all() and (x.sum(axis=1) > 0).all()
lookup = {row['sample_id']: row for row in metadata}
groups = np.array([lookup[s]['facies'] for s in ids])
d = np.abs(x[:, None, :] - x[None, :, :]).sum(axis=2) / (x.sum(axis=1)[:, None] + x.sum(axis=1)[None, :])
np.testing.assert_allclose(d, r['distances'], rtol=1e-14, atol=1e-15)
total = np.square(d).sum() / (2 * len(ids))

def statistic(a):
    b = [i for i in range(8) if i not in a]
    within = sum(np.square(d[np.ix_(g, g)]).sum() / (2 * len(g)) for g in [a, b])
    return ((total - within) / 1) / (within / 6)

observed = statistic(list(np.flatnonzero(groups == 'reef')))
np.testing.assert_allclose(observed, r['pseudo_f'], rtol=1e-14)
statistics = [statistic(list(a)) for a in itertools.combinations(range(8), 4)]
extreme = sum(v >= observed - 1e-8 for v in statistics)
assert len(statistics) == 70 and extreme == 2
assert r['p_value'] == extreme / len(statistics)
assert r['permutation']['mode'] == 'exact'
assert r['permutation']['draws'] == r['permutation']['space_size'] == 70
assert r['permutation']['seed'] == 20261031
# Here Bray-Curtis is exactly a one-dimensional Euclidean distance because
# the two taxa sum to 100 in every row. Check the uncorrected centroid means.
z = x[:, 0] / 100
for group in ['reef', 'lagoon']:
    values = z[groups == group]
    mean_distance = np.abs(values - values.mean()).mean()
    np.testing.assert_allclose(mean_distance, r['dispersion']['group_mean_distances'][group], rtol=1e-13)

keys = ['n', 'pseudo_f', 'r_squared', 'p_value', 'ss_total', 'ss_within', 'ss_between', 'df_between', 'df_within']
results = {key: r[key] for key in keys}
results['group_mean_centroid_distance'] = r['dispersion']['group_mean_distances']
answer = {
    'status': 'completed',
    'results': results,
    'assumptions': [
        'As explicitly stated in dictionary.md, each sample is one distinct site sampled once; the eight sites are independent sampling units and facies labels are freely exchangeable under the null. There are no blocks, covariates, repeated measurements or nested subsamples.',
        'Counts are untransformed nonnegative integer specimen counts, with samples in rows and taxa in columns; no normalisation or aggregation was applied.'
    ],
    'exclusions': [],
    'issues': [
        'No data problems identified: sample IDs match exactly between the count table and metadata, all eight site IDs are distinct, all counts are valid, and no samples are missing or empty. Metadata were aligned by exact sample ID.',
        'All 70 distinct allocations preserving four reef and four lagoon sites were enumerated instead of Monte Carlo sampling the requested 999 permutations. Two allocations were at least as extreme as observed, including the observed allocation; the exact p-value is 2/70. Seed 20261031 was recorded but exhaustive enumeration does not depend on it.',
        'PERMANOVA measures community association with facies and can reflect both location and dispersion; it does not establish a causal effect or isolate a pure centroid-location effect. Only four sites per group were sampled, and the exact permutation p-value has limited resolution.',
        'Centroid distances are descriptive with no bias adjustment, square-root distance transformation, additive distance correction or dispersion significance test. Palaeo-Agent retained one positive eigenaxis and discarded seven numerical-zero eigenmodes below its recorded threshold of 1.4901161193847656e-08; no negative squared distances were truncated.'
    ],
    'summary': 'One-way Bray-Curtis PERMANOVA on all eight untransformed count samples supports a facies-associated community difference under the declared independent-site, freely exchangeable-label design. Numerical results are copied without rounding from Palaeo-Agent. Rerun using python -m palaeo_agent run analysis.spec.json --output analysis_run, then python finalize_analysis.py. The full run, input snapshots, aligned metadata, exact allocation statistics, environment and manifest are preserved under analysis_run/. Independent distance, pseudo-F, exhaustive p-value and centroid checks and answer-schema validation are in finalize_analysis.py.'
}
schema = json.loads((root / 'answer.schema.json').read_text())
# The supplied contract uses only these simple constraints; validate directly
# because jsonschema is not installed in the provided environment.
assert set(answer) == set(schema['required']) == set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'], dict)
for key in ['assumptions', 'issues']:
    assert isinstance(answer[key], list) and all(isinstance(v, str) for v in answer[key])
assert isinstance(answer['exclusions'], list)
for exclusion in answer['exclusions']:
    assert set(exclusion) == {'id', 'reason'}
    assert all(isinstance(v, str) for v in exclusion.values())
assert isinstance(answer['summary'], str)
assert set(results) == set(keys) | {'group_mean_centroid_distance'}
assert all(isinstance(results[k], (int, float)) and np.isfinite(results[k]) for k in keys)
assert set(results['group_mean_centroid_distance']) == {'reef', 'lagoon'}
(root / 'answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
print(json.dumps(results, indent=2))
print('answer.json validated against answer.schema.json')
