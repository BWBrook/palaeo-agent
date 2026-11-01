"""Independent P04-cal calculation; Python standard library only."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MATERIALS = ROOT / 'calibration' / 'P04-cal' / 'materials'
OUT = Path(__file__).resolve().parent
with (MATERIALS / 'cores.csv').open() as f:
    campaigns = {r['core']: r['campaign'] for r in csv.DictReader(f)}
with (MATERIALS / 'counts.tsv').open() as f:
    rows = list(csv.reader(f, delimiter='\t'))
taxa = rows[0][1:]

def shannon(counts):
    n = sum(counts)
    return -math.fsum((v / n) * math.log(v / n) for v in counts if v > 0)

cores = []
for row in rows[1:]:
    values = [None if x == '.' else int(x) for x in row[1:]]
    common = values[:8]
    observed = [x for x in values if x is not None]
    cores.append({
        'core': row[0], 'campaign': campaigns[row[0]],
        'common_T01_T08_N': sum(common),
        'common_T01_T08_H': shannon(common),
        'observed_taxa_count': len(observed),
        'observed_N': sum(observed), 'observed_H': shannon(observed),
        'unpicked_taxa': [t for t, v in zip(taxa, values) if v is None],
    })
means = {}
for year in ['2017', '2021']:
    subset = [r for r in cores if r['campaign'] == year]
    means[year] = {
        'n_cores': len(subset),
        'common_T01_T08_mean_H': math.fsum(r['common_T01_T08_H'] for r in subset) / len(subset),
        'observed_mean_H': math.fsum(r['observed_H'] for r in subset) / len(subset),
    }
result = {
    'method': 'Per-core H = -sum(p_i * ln(p_i)), p_i = count_i / sum(counts); arithmetic campaign mean over six cores. No pooling.',
    'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(MATERIALS.iterdir()) if p.is_file()},
    'cores': cores, 'campaign_means': means,
    'common_T01_T08_delta_2021_minus_2017': means['2021']['common_T01_T08_mean_H'] - means['2017']['common_T01_T08_mean_H'],
    'unmatched_observed_delta_2021_minus_2017': means['2021']['observed_mean_H'] - means['2017']['observed_mean_H'],
    'interpretation': 'Matched comparison identifiable for fully picked >150 micrometre fraction, taxa T01-T08 only. Full-community comparison including T09-T11 is not identifiable in 2017: dots denote unpicked fraction, not zeros. Observed-coverage means use different taxon/fraction bases and cannot establish temporal community diversity change.'
}
(OUT / 'independent-calculation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
