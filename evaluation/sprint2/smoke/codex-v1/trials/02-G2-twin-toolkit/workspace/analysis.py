"""Run with: python analysis.py (uses the installed Palaeo-Agent; no network)."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent


def main():
    with (ROOT / 'counts.tsv').open() as f:
        table = list(csv.reader(f, delimiter='\t'))
    ids = [row[0] for row in table[1:]]
    taxa = table[0][1:]
    counts = np.array([row[1:] for row in table[1:]], dtype=float)
    with (ROOT / 'samples.csv').open() as f:
        metadata = list(csv.DictReader(f))
    assert len(ids) == len(set(ids)) == 8
    assert len(taxa) == len(set(taxa)) == 2
    assert len(metadata) == len({r['sample_id'] for r in metadata}) == 8
    assert set(ids) == {r['sample_id'] for r in metadata}
    assert len({r['site_id'] for r in metadata}) == 8
    assert np.isfinite(counts).all() and (counts >= 0).all()
    assert (counts == np.floor(counts)).all() and (counts.sum(axis=1) > 0).all()
    spec = ROOT / 'permanova.spec.json'
    subprocess.run([sys.executable, '-m', 'palaeo_agent', 'validate', str(spec)],
                   cwd=ROOT, check=True)
    run_root = ROOT / 'permanova_run'
    existing = sorted(run_root.glob('*/results.json'))
    if not existing:
        subprocess.run([sys.executable, '-m', 'palaeo_agent', 'run', str(spec),
                        '--output', str(run_root)], cwd=ROOT, check=True)
        existing = sorted(run_root.glob('*/results.json'))
    assert len(existing) == 1
    result_path = existing[0]
    r = json.loads(result_path.read_text())
    assert r['sample_ids'] == ids
    assert np.array_equal(r['retained_counts'], counts)
    assert r['group_sizes'] == {'reef': 4, 'lagoon': 4}
    assert not r['excluded'] and not r['warnings']
    assert r['permutation']['mode'] == 'exact'
    assert r['permutation']['draws'] == r['permutation']['space_size'] == 70
    assert r['permutation']['count_extreme'] == 2
    assert r['permutation']['seed'] == 20261031
    # Independently verify Bray-Curtis dissimilarities and sums of squares.
    distances = (np.abs(counts[:, None, :] - counts[None, :, :]).sum(axis=2)
                 / (counts[:, None, :] + counts[None, :, :]).sum(axis=2))
    np.testing.assert_allclose(distances, r['distances'], rtol=1e-14, atol=1e-15)
    total = np.triu(distances ** 2, 1).sum() / len(ids)
    groups = np.array(r['groups'])
    within = sum(np.triu(distances[np.ix_(groups == g, groups == g)] ** 2, 1).sum()
                 / sum(groups == g) for g in r['group_labels'])
    np.testing.assert_allclose([total, within, total - within],
                               [r['ss_total'], r['ss_within'], r['ss_between']])
    fields = ['n', 'pseudo_f', 'r_squared', 'p_value', 'ss_total', 'ss_within',
              'ss_between', 'df_between', 'df_within']
    results = {key: r[key] for key in fields}
    results['group_mean_centroid_distance'] = r['dispersion']['group_mean_distances']
    answer = {
        'status': 'completed',
        'results': results,
        'assumptions': [
            'As explicitly stated in dictionary.md, each row is one distinct site sampled once; the eight sites are independent sampling units and facies labels are freely exchangeable under the null.',
            'The analysis uses one facies factor with four reef and four lagoon sites, without blocks, covariates, repeated measurements or nested subsamples. Counts are used without transformation, normalisation or aggregation.'
        ],
        'exclusions': [],
        'issues': [
            'No data problems identified: sample and taxon IDs are unique, metadata match count rows by exact sample_id, site IDs are distinct, and all counts are finite nonnegative integers with no empty samples. Palaeo-Agent reported no warnings.',
            'Independence and null exchangeability are supported by the supplied sampling description but cannot be verified from the count matrix. PERMANOVA tests facies-associated composition and is not exclusively a centroid-location test or evidence of causation.',
            'Centroid distances are descriptive, with no bias adjustment, square-root transformation, additive distance correction or dispersion significance test. Palaeo-Agent discarded numerical eigenmodes below its recorded tolerance; no sample distances required truncation.'
        ],
        'summary': (
            'One-way PERMANOVA on untransformed specimen counts using Bray-Curtis dissimilarity, '
            'performed with Palaeo-Agent. All 70 distinct label allocations preserving group sizes '
            'were enumerated, including the observed allocation; 2 were at least as extreme, '
            'so the exact p-value is 2/70. The requested permutation count was 999 and seed was '
            '20261031; enumeration makes the result independent of random draws. Facies is '
            'associated with composition at the conventional 0.05 level. '
            'Rerun with python analysis.py; permanova.spec.json preserves the specification. '
            'The permanova_run directory preserves complete results, permutation allocations, '
            'statistics, dispersion diagnostics, input copies, manifest and environment. '
            'provenance.json records input hashes. Numbers are copied without rounding.'
        )
    }
    # Validate this contract using its supplied constraints, without extra packages.
    schema = json.loads((ROOT / 'answer.schema.json').read_text())
    assert set(answer) == set(schema['required']) == set(schema['properties'])
    assert answer['status'] in schema['properties']['status']['enum']
    assert isinstance(answer['results'], dict)
    assert isinstance(answer['summary'], str)
    for key in ['assumptions', 'issues']:
        assert isinstance(answer[key], list)
        assert all(isinstance(item, str) for item in answer[key])
    assert isinstance(answer['exclusions'], list)
    for item in answer['exclusions']:
        assert set(item) == {'id', 'reason'}
        assert all(isinstance(value, str) for value in item.values())
    assert set(results) == set(fields) | {'group_mean_centroid_distance'}
    assert all(isinstance(results[key], (int, float)) for key in fields)
    assert set(results['group_mean_centroid_distance']) == {'reef', 'lagoon'}
    (ROOT / 'answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
    provenance = {
        'command': 'python analysis.py',
        'result_file': str(result_path.relative_to(ROOT)),
        'sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                   for name in ['counts.tsv', 'samples.csv', 'task.md', 'dictionary.md',
                                'permanova.spec.json', 'answer.schema.json']},
        'validation': 'Schema and data-integrity checks passed; Bray-Curtis distances and sums of squares independently checked.'
    }
    (ROOT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(answer, indent=2))


if __name__ == '__main__':
    main()
