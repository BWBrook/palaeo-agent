import csv
import itertools
import json
from fractions import Fraction
from pathlib import Path

samples = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']
taxa = ['Dalmanella', 'Sowerbyella', 'Howellites', 'Platystrophia', 'Orthis', 'Strophomena', 'Rafinesquina', 'Leptaena']
with Path('counts.tsv').open(newline='') as f:
    reader = csv.reader(f, delimiter='\t')
    assert next(reader) == ['.'] + taxa
    rows = list(reader)
assert [r[0] for r in rows] == samples
counts = {}
for row in rows:
    assert len(row) == len(taxa) + 1
    values = [int(x) for x in row[1:]]
    assert all(x >= 0 for x in values)
    counts[row[0]] = values
richness = {s: sum(x > 0 for x in counts[s]) for s in samples}
distances = {}
for a, b in itertools.combinations(samples, 2):
    numerator = sum(abs(x-y) for x, y in zip(counts[a], counts[b]))
    denominator = sum(counts[a]) + sum(counts[b])
    assert denominator > 0
    value = Fraction(numerator, denominator)
    assert value == 1 - Fraction(2 * sum(min(x,y) for x,y in zip(counts[a], counts[b])), denominator)
    distances[f'{a}|{b}'] = float(value)
answer = {
    'status': 'completed',
    'results': {'richness': richness, 'braycurtis': distances},
    'assumptions': [],
    'exclusions': [],
    'issues': [],
    'summary': 'Richness counts genera with positive specimen counts in each sample. All 15 pairwise Bray–Curtis dissimilarities were calculated on raw counts as sum(abs(x-y))/sum(x+y), with no rounding.'
}
Path('answer.json').write_text(json.dumps(answer, indent=2, allow_nan=False) + '\n')
schema = json.loads(Path('answer.schema.json').read_text())
try:
    import jsonschema
except ImportError:
    assert set(answer) == set(schema['required'])
    assert answer['status'] in schema['properties']['status']['enum']
    assert isinstance(answer['results'], dict)
    assert all(isinstance(answer[k], list) for k in ['assumptions', 'exclusions', 'issues'])
    assert isinstance(answer['summary'], str)
else:
    jsonschema.Draft202012Validator(schema).validate(answer)
assert len(distances) == 15
assert all(0 <= v <= 1 for v in distances.values())
print(Path('answer.json').read_text())
print('Validation passed.')
