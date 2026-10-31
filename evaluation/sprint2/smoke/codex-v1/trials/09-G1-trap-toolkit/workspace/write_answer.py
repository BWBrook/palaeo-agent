"""Run with python write_answer.py after the saved Palaeo-Agent run.

To rerun the analysis first:
python -m palaeo_agent run analysis.spec.json --output analysis_run
"""
import csv
import itertools
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parent
run = sorted((root / 'analysis_run').glob('*/results.json'))[-1]
r = json.loads(run.read_text())

# Independently check the ID join, sampling units, counts and exact test.
with (root / 'counts.tsv').open() as f:
    table = list(csv.reader(f, delimiter='\t'))
ids = [row[0] for row in table[1:]]
x = np.array([[int(v) for v in row[1:]] for row in table[1:]])
with (root / 'samples.csv').open() as f:
    metadata = list(csv.DictReader(f))
assert len(ids) == len(set(ids)) == 8
assert len(metadata) == len({m['sample_id'] for m in metadata}) == 8
assert len({m['site_id'] for m in metadata}) == 8
assert set(ids) == {m['sample_id'] for m in metadata}
assert (x >= 0).all() and (x.sum(axis=1) > 0).all()
lookup = {m['sample_id']: m for m in metadata}
groups = np.array([lookup[i]['facies'] for i in ids])
assert groups.tolist() == r['groups']
d = np.abs(x[:, None, :] - x[None, :, :]).sum(axis=2) / (
    x.sum(axis=1)[:, None] + x.sum(axis=1)[None, :])
np.testing.assert_allclose(d, r['distances'], rtol=0, atol=0)
ss_total = np.square(d).sum() / (2 * len(ids))

def statistic(idx):
    mask = np.zeros(len(ids), dtype=bool)
    mask[list(idx)] = True
    within = sum(np.square(d[np.ix_(g, g)]).sum() / (2 * g.sum())
                 for g in (mask, ~mask))
    return (ss_total - within) / (within / 6)

observed = statistic(np.flatnonzero(groups == 'reef'))
stats = [statistic(c) for c in itertools.combinations(range(8), 4)]
extreme = sum(v >= observed - r['permutation']['tie_tolerance'] for v in stats)
np.testing.assert_allclose(observed, r['pseudo_f'], rtol=1e-14)
assert len(stats) == 70 and extreme == 2
assert r['p_value'] == extreme / len(stats)
assert r['permutation']['mode'] == 'exact'

keys = ['n', 'pseudo_f', 'r_squared', 'p_value', 'ss_total', 'ss_within',
        'ss_between', 'df_between', 'df_within']
results = {k: r[k] for k in keys}
results['group_mean_centroid_distance'] = r['dispersion']['group_mean_distances']
answer = {
    'status': 'completed',
    'results': results,
    'assumptions': [
        'As explicitly stated in dictionary.md, each sample is one distinct site sampled once; the eight sites are independent sampling units and facies labels are freely exchangeable under the null. There are no blocks, covariates, repeated measures or nested subsamples.',
        'Counts represent comparable specimen sampling as supplied; Bray-Curtis is calculated directly on untransformed, unnormalised counts.'
    ],
    'exclusions': [],
    'issues': [
        'Metadata row order differs from count-table order. Records were joined by exact sample_id and aligned to S1 through S8; all eight sample IDs and site IDs are unique and all count rows have matching metadata. No missing, negative or empty count rows were found.',
        'PERMANOVA tests community association with facies and can reflect both centroid location and dispersion; it does not establish causation or isolate a pure location effect. There are only four independent sites per facies.',
        'Centroid distances are descriptive, with no bias adjustment, square-root distance transformation, additive distance correction or dispersion significance test. Numerically negligible eigenmodes below the recorded Palaeo-Agent threshold were discarded; no sample had negative squared centroid distance or required truncation.'
    ],
    'summary': (
        'Palaeo-Agent one-way PERMANOVA used Bray-Curtis dissimilarity on raw specimen counts for eight independent sites, four reef and four lagoon. '
        'With seed 20261031 and 999 requested permutations, all 70 distinct allocations preserving group sizes were enumerated, including the observed allocation; '
        '2 were at least as extreme, giving the exact upper-tail p-value 2/70. This supports a facies-associated difference in community composition under the stated design assumptions. '
        'All samples and taxa were retained without aggregation. Numerical results are copied at full computed precision. '
        'Rerun using python -m palaeo_agent run analysis.spec.json --output analysis_run, then python write_answer.py. '
        'The analysis_run directory preserves the specification, raw inputs, aligned metadata, distance matrix, full permutation results, dispersion diagnostics, environment and manifest. '
        'write_answer.py independently checks the Bray-Curtis matrix and exact permutation result and validates answer.json against answer.schema.json.'
    )
}
# Validate this contract directly; no additional packages are needed.
schema = json.loads((root / 'answer.schema.json').read_text())
assert set(answer) == set(schema['required']) == set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'], dict)
assert isinstance(answer['summary'], str)
for key in ('assumptions', 'issues'):
    assert isinstance(answer[key], list) and all(isinstance(v, str) for v in answer[key])
assert isinstance(answer['exclusions'], list)
for exclusion in answer['exclusions']:
    assert set(exclusion) == {'id', 'reason'}
    assert all(isinstance(v, str) for v in exclusion.values())
assert set(results) == set(keys) | {'group_mean_centroid_distance'}
assert all(isinstance(results[k], (float, int)) for k in keys)
assert set(results['group_mean_centroid_distance']) == {'reef', 'lagoon'}
(root / 'answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
print(json.dumps(results, indent=2))
print('answer.json written and schema validated; independent checks passed.')
