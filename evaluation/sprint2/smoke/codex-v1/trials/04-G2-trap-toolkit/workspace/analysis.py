"""Rerun design audit and write answer with: python analysis.py."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
proc = subprocess.run([sys.executable, '-m', 'palaeo_agent', 'discover'],
                      cwd=root, check=True, capture_output=True, text=True)
discovery = json.loads(proc.stdout)
(root / 'analysis_discover.json').write_text(json.dumps(discovery, indent=2) + '\n')
method = next(m for m in discovery['methods'] if m['id'] == 'permanova')
assert method['input_schema']['properties']['design']['const'] == 'independent'
assert method['input_schema']['properties']['permutation_scheme']['const'] == 'free'

with (root / 'counts.tsv').open(newline='') as f:
    table = list(csv.reader(f, delimiter='\t'))
assert table[0][0] == '.'
assert len(set(table[0][1:])) == len(table[0][1:])
ids = [r[0] for r in table[1:]]
assert ids == ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8']
for row in table[1:]:
    assert len(row) == len(table[0])
    values = [int(v) for v in row[1:]]
    assert all(v >= 0 for v in values) and sum(values) > 0
with (root / 'samples.csv').open(newline='') as f:
    metadata = list(csv.DictReader(f))
assert len(metadata) == len(ids)
assert len({r['sample_id'] for r in metadata}) == len(metadata)
assert {r['sample_id'] for r in metadata} == set(ids)
by_id = {r['sample_id']: r for r in metadata}
site_facies, site_samples = {}, {}
for sample_id in ids:
    row = by_id[sample_id]
    site_facies.setdefault(row['site_id'], set()).add(row['facies'])
    site_samples.setdefault(row['site_id'], []).append(sample_id)
assert site_samples == {'site_reef_01': ids[:4], 'site_lagoon_01': ids[4:]}
assert site_facies == {'site_reef_01': {'reef'}, 'site_lagoon_01': {'lagoon'}}

answer = {
    'status': 'stopped',
    'results': {},
    'assumptions': ['The sampling description in dictionary.md is authoritative: sites are the independent sampling units for the facies comparison, and rows are dependent subsamples within sites.'],
    'exclusions': [],
    'issues': [
        'S1-S4 are subsamples of site_reef_01 (reef); S5-S8 are subsamples of site_lagoon_01 (lagoon). The independent sampling units are the two sites, with only one site per facies.',
        'The requested one-way free-label PERMANOVA on the eight rows is unsupported: within-site subsamples share exposure and are not independent facies replicates. Freely exchanging their facies labels would create pseudoreplication.',
        'Facies is completely confounded with site. At the independent site level there is no within-facies replication and no residual degrees of freedom for the requested test. No aggregation or alternative experimental design was substituted.',
        'Palaeo-Agent discovery confirms that its PERMANOVA requires independent units, freely exchangeable labels, and at least two samples per group. These requirements are unmet, so no PERMANOVA, permutation enumeration, or centroid-distance analysis was run. Requested seed 20261031 and 999 permutations were recorded but not applied.',
        'Input checks found unique matching sample IDs, unique taxon names, nonnegative integer counts, and no missing values or empty samples. No samples or counts were excluded, transformed, or normalized.'
    ],
    'summary': 'Stopped before statistical analysis because the documented subsampling contradicts the requested independent, freely exchangeable design. No facies inference is supported. Rerun with python analysis.py; analysis_provenance.json records input hashes, design, and package requirements, and analysis_discover.json preserves installed Palaeo-Agent discovery.'
}
schema = json.loads((root / 'answer.schema.json').read_text())
# Check every constraint relevant to this stopped answer using the standard library.
assert set(answer) == set(schema['required']) == set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'], dict) and answer['results'] == {}
for key in ['assumptions', 'issues']:
    assert isinstance(answer[key], list) and all(isinstance(v, str) for v in answer[key])
assert answer['exclusions'] == []
assert isinstance(answer['summary'], str)
(root / 'answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
provenance = {
    'rerun': 'python analysis.py',
    'python_version': sys.version,
    'input_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                     for name in ['task.md', 'dictionary.md', 'counts.tsv', 'samples.csv', 'answer.schema.json', 'analysis.py']},
    'package_command': [sys.executable, '-m', 'palaeo_agent', 'discover'],
    'package_method': method['id'],
    'package_method_version': method['version'],
    'package_requirements': method['requirements'],
    'requested_analysis': {'distance': 'braycurtis', 'transform': 'none', 'seed': 20261031, 'permutations': 999},
    'site_samples': site_samples,
    'site_facies': {k: sorted(v) for k, v in site_facies.items()},
    'decision': 'stopped: unsupported independent free-label design',
    'schema_validation': 'passed'
}
(root / 'analysis_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print('answer.json written; JSON Schema validation passed. Status: stopped.')
