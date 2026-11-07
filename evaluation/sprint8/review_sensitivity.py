"""Reproduce the I2 duplicate sensitivity identified in the independent review.

Run from the repository root: uv run python evaluation/sprint8/review_sensitivity.py
Study exclusions and point slopes use the API. Mann–Whitney tests and their
six-test Holm family are unsupported by the toolkit and retain I2's conventions.
The original session records are read only; bundles use a temporary directory.
"""

import hashlib
import itertools
import json
from pathlib import Path
import tempfile

import numpy as np
import palaeo_agent as pa
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / 'evaluation/authentic/run-records/sprint8-instructed-20261106/sessions/I2/workspace'
OUTPUT = Path(__file__).with_name('review-sensitivity.json')
SCENARIOS = {'as_archived': [], 'block_removed': list(range(64, 71)), 'unique_pairs': list(range(64, 72))}


def main():
    source = WORKSPACE / 'dielasma.dat'
    datasets = {'as_archived': {'source': 'dielasma'}}
    for scenario, removed in SCENARIOS.items():
        if removed:
            datasets[scenario] = {'source': 'dielasma', 'operations': [{
                'op': 'exclude', 'samples': list(map(str, removed)),
                'reason': f'L2 duplicate sensitivity: {scenario}; provenance remains unresolved',
            }]}
    analyses = []
    for locality in ('L1', 'L2', 'L3'):
        for scenario in SCENARIOS if locality == 'L2' else ['as_archived']:
            analyses.append({'id': f'{scenario}.{locality}', 'dataset': scenario, 'spec': {
                'method': 'rma', 'format': 'past', 'x': f'{locality}/X1', 'y': f'{locality}/X2',
                'transform': 'log10', 'missing': 'drop_pairs',
            }})
    study = {'study_version': 1, 'inputs': {'dielasma': {'kind': 'measurements', 'path': str(source),
             'format': 'past', 'orientation': 'samples_by_taxa'}}, 'datasets': datasets, 'analyses': analyses}
    with tempfile.TemporaryDirectory() as temporary:
        outcome = pa.run_study(study, Path(temporary) / 'study')
        inspected = pa.inspect_study(outcome['study_dir'])
        assert inspected['study_status'] == 'complete'
        results = {name: pa.inspect_run(Path(outcome['study_dir']) / run['run_dir'])['result']
                   for name, run in inspected['runs'].items()}
    recorded = json.loads((WORKSPACE / 'results.json').read_text())
    scenarios = []
    for scenario, removed in SCENARIOS.items():
        fitted = {locality: results[f'{scenario if locality == "L2" else "as_archived"}.{locality}']
                  for locality in ('L1', 'L2', 'L3')}
        pairs = {locality: np.array([[row['x_raw'], row['y_raw']] for row in fit['pairs']])
                 for locality, fit in fitted.items()}
        tests = []
        for first, second in itertools.combinations(('L1', 'L2', 'L3'), 2):
            for variable in ('length', 'ratio'):
                values = {locality: data[:, 0] if variable == 'length' else data[:, 1] / data[:, 0]
                          for locality, data in pairs.items()}
                p = float(stats.mannwhitneyu(values[first], values[second]).pvalue)
                tests.append({'pair': f'{first}-{second}', 'var': variable, 'p': p})
        pvalues = np.array([test['p'] for test in tests])
        order = np.argsort(pvalues)
        adjusted = np.empty_like(pvalues)
        adjusted[order] = np.minimum(1, np.maximum.accumulate((len(tests) - np.arange(len(tests))) * pvalues[order]))
        for test, value in zip(tests, adjusted):
            test['holm6'] = float(value)
        if scenario == 'as_archived':
            for test, saved in zip(tests, recorded['pairwise'], strict=True):
                assert (test['pair'], test['var']) == (saved['pair'], saved['var'])
                assert test['p'] == saved['mwu_p'] and test['holm6'] == saved['mwu_p_holm6']
        scenarios.append({'scenario': scenario, 'L2_rows_removed': removed, 'L2_n': fitted['L2']['n'],
                          'L2_log10_rma_slope': fitted['L2']['slope'], 'tests': tests})
    receipt = {'purpose': 'Independent I2 review sensitivity; original session records unchanged',
               'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'primer': {key: pa.primer()[key] for key in ('version', 'sha256')},
               'numpy_version': np.__version__, 'scipy_version': __import__('scipy').__version__,
               'conventions': 'I2 two-sided scipy.stats.mannwhitneyu defaults; Holm across three pairs x length/ratio',
               'archived_pvalues_match_exactly': True, 'row_filter_warnings': inspected['row_filter_warnings'],
               'scenarios': scenarios}
    OUTPUT.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({row['scenario']: next(test['holm6'] for test in row['tests']
                     if test['pair'] == 'L1-L2' and test['var'] == 'length') for row in scenarios}))


if __name__ == '__main__':
    main()
