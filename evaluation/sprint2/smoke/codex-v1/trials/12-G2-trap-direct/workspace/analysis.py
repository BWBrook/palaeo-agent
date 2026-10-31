"""Rerun with python analysis.py. Standard library only; no statistics run."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
with (root / 'counts.tsv').open(newline='') as f:
    counts = list(csv.reader(f, delimiter='\t'))
with (root / 'samples.csv').open(newline='') as f:
    records = list(csv.DictReader(f))
assert counts[0][0] == '.'
ids = [row[0] for row in counts[1:]]
assert ids == ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']
assert len(records) == len({r['sample_id'] for r in records}) == 8
assert set(ids) == {r['sample_id'] for r in records}
for row in counts[1:]:
    assert len(row) == len(counts[0])
    values = [int(v) for v in row[1:]]
    assert all(v >= 0 for v in values) and sum(values) > 0
for r in records:
    reef = r['sample_id'] in ids[:4]
    assert r['site_id'] == ('site_reef_01' if reef else 'site_lagoon_01')
    assert r['facies'] == ('reef' if reef else 'lagoon')

answer = {
    'status': 'stopped',
    'results': {},
    'assumptions': [
        'The sampling description in dictionary.md is authoritative: facies is a site-level attribute and subsamples within a site are not independent facies replicates.'
    ],
    'exclusions': [],
    'issues': [
        'The independent sampling units for the facies comparison are sites. S1-S4 are subsamples of site_reef_01, and S5-S8 are subsamples of site_lagoon_01. There is one site per facies.',
        'The requested freely exchangeable sample-level one-way PERMANOVA is unsupported. Exchanging subsample labels would treat dependent subsamples as independent replicates (pseudoreplication). Facies and site are completely confounded, preventing separation of a facies effect from a site effect.',
        'No samples were aggregated and no alternative experimental design was substituted. A site-level comparison would have no within-group replication or residual degrees of freedom. No statistics, centroid-distance summaries or permutations were computed; results is empty as required for an unsupported design.',
        'Input validation found unique matching sample IDs, the documented count-table row order, nonnegative integer counts, and no missing values or empty samples. No corrections, transformations, normalisation or exclusions were made.'
    ],
    'summary': 'Stopped before statistical computation because the sampling design lacks independent replication within facies. All eight count rows and their metadata were validated. analysis.py preserves the validation and decision specification; provenance.json records input hashes and requested permutation settings.'
}
schema = json.loads((root / 'answer.schema.json').read_text())
assert set(answer) == set(schema['required']) == set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'], dict) and not answer['results']
for field in ['assumptions', 'issues']:
    assert isinstance(answer[field], list) and all(isinstance(v, str) for v in answer[field])
assert answer['exclusions'] == []
assert isinstance(answer['summary'], str)
(root / 'answer.json').write_text(json.dumps(answer, indent=2) + '\n')
provenance = {
    'rerun_command': 'python analysis.py',
    'input_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                     for name in ['task.md', 'dictionary.md', 'answer.schema.json', 'counts.tsv', 'samples.csv']},
    'analysis_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'requested_method': 'One-way PERMANOVA; Bray-Curtis; untransformed specimen counts',
    'requested_seed': 20261031,
    'requested_permutations': 999,
    'permutations_run': 0,
    'reason': 'Unsupported independence design; stopped before statistical computation.',
    'validated_sample_count': len(ids),
    'independent_site_count': len({r['site_id'] for r in records})
}
(root / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print('Input and answer-contract checks passed; wrote answer.json and provenance.json.')
