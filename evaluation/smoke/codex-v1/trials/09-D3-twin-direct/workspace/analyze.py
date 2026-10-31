import csv
import json
import math
from collections import defaultdict
from pathlib import Path

with open('counts.tsv', newline='') as f:
    reader = csv.reader(f, delimiter='\t')
    header = next(reader)
    assert header[0] == '.'
    counts = {}
    for row in reader:
        sample_id = row[0]
        assert sample_id not in counts
        values = [int(value) for value in row[1:]]
        assert len(values) == len(header) - 1
        assert all(value >= 0 for value in values)
        assert sum(values) > 0
        counts[sample_id] = values

with open('samples.csv', newline='') as f:
    samples = list(csv.DictReader(f))
assert len({row['sample_id'] for row in samples}) == len(samples)
assert {row['sample_id'] for row in samples} == set(counts)
groups = defaultdict(list)
for row in samples:
    assert row['facies'] in {'reef', 'lagoon'}
    values = counts[row['sample_id']]
    total = sum(values)
    h = -math.fsum((value / total) * math.log(value / total)
                   for value in values if value > 0)
    groups[row['facies']].append(h)
    print(row['sample_id'], row['facies'], repr(h))

answer = {
    'status': 'completed',
    'results': {
        'mean_shannon_reef': math.fsum(groups['reef']) / len(groups['reef']),
        'mean_shannon_lagoon': math.fsum(groups['lagoon']) / len(groups['lagoon']),
    },
    'assumptions': [],
    'exclusions': [],
    'issues': [],
    'summary': 'Computed sample Shannon diversity as H = -sum(p * ln(p)) from genus specimen proportions, with zero counts contributing zero, and took the unweighted arithmetic mean of the four sample indices in each facies. All eight samples were included.'
}
Path('answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
schema = json.loads(Path('answer.schema.json').read_text())
try:
    import jsonschema
except ImportError:
    assert set(answer) == set(schema['required'])
    assert answer['status'] in schema['properties']['status']['enum']
    assert set(answer['results']) == {'mean_shannon_reef', 'mean_shannon_lagoon'}
    assert all(isinstance(v, float) and math.isfinite(v) for v in answer['results'].values())
    assert all(isinstance(answer[k], list) for k in ['assumptions', 'exclusions', 'issues'])
    assert isinstance(answer['summary'], str)
else:
    jsonschema.validate(answer, schema)
print(json.dumps(answer, indent=2))
