import csv
import json
import math
from pathlib import Path
from statistics import mean

root = Path(__file__).parent
run = next((root / 'community_run').glob('*/results.json'))
result = json.loads(run.read_text())
with (root / 'samples.csv').open() as handle:
    metadata = list(csv.DictReader(handle))
facies = {row['sample_id']: row['facies'] for row in metadata}
assert len(facies) == len(metadata)
with (root / 'counts.tsv').open() as handle:
    rows = list(csv.reader(handle, delimiter='\t'))
counts = {row[0]: [int(value) for value in row[1:]] for row in rows[1:]}
assert len(counts) == len(rows) - 1
assert set(counts) == set(facies) == {row['sample_id'] for row in result['diversity']}
assert not result['excluded']
groups = {'reef': [], 'lagoon': []}
for row in result['diversity']:
    values = counts[row['sample_id']]
    assert all(value >= 0 for value in values)
    total = sum(values)
    expected = -sum((value / total) * math.log(value / total) for value in values if value)
    assert math.isclose(row['shannon'], expected, rel_tol=1e-14, abs_tol=1e-14)
    groups[facies[row['sample_id']]].append(row['shannon'])
answer = {
    'status': 'completed',
    'results': {f'mean_shannon_{group}': mean(values) for group, values in groups.items()},
    'assumptions': [],
    'exclusions': [],
    'issues': [],
    'summary': 'Computed sample Shannon diversity H = -sum(p*ln(p)) from genus counts using Palaeo-Agent, joined facies by exact sample ID, and calculated the arithmetic mean across the four samples in each facies. Zero counts contribute zero. Independently verified sample diversity values; the ancillary PCoA negative-eigenvalue warning does not affect diversity.'
}
schema = json.loads((root / 'answer.schema.json').read_text())
assert set(answer) == set(schema['required']) == set(schema['properties'])
assert answer['status'] in schema['properties']['status']['enum']
assert isinstance(answer['results'], dict)
assert set(answer['results']) == {'mean_shannon_reef', 'mean_shannon_lagoon'}
assert all(isinstance(value, float) and math.isfinite(value) for value in answer['results'].values())
assert all(isinstance(answer[key], list) and not answer[key] for key in ['assumptions', 'exclusions', 'issues'])
assert isinstance(answer['summary'], str)
(root / 'answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
print(json.dumps(answer, indent=2))
