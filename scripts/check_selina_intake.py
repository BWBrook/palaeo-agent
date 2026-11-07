"""Check the Lake Selina proposal against a saved Neotoma download, without computing study results.

JSON extraction and ecological-group filtering are unsupported intake steps.
Count totals and resource checks use the toolkit's public validation API.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median

import palaeo_agent as pa


def check(path):
    raw = path.read_bytes()
    site = json.loads(raw)['data'][0]['site']
    collection = site['collectionunit']
    dataset = collection['dataset']
    if dataset['datasetid'] != 52767:
        raise ValueError('Expected Neotoma dataset 52767')
    samples = sorted(dataset['samples'], key=lambda sample: sample['depth'])
    taxa = {}
    rows = []
    for sample in samples:
        values = {}
        for datum in sample['datum']:
            if datum['element'] != 'pollen' or datum['ecologicalgroup'] not in ('TRSH', 'UPHE'):
                continue
            if datum['units'] != 'NISP' or type(datum['value']) is not int or datum['value'] < 0:
                raise ValueError('Expected nonnegative integer NISP counts')
            if datum['taxonid'] in values:
                raise ValueError('Repeated retained taxon ID within sample')
            taxa[datum['taxonid']] = datum['variablename']
            values[datum['taxonid']] = datum['value']
        rows.append((sample, values))
    labels = sorted(taxa)
    header = '\t'.join(['sample_id', *[f'taxon_{taxon}' for taxon in labels]])
    lines = [header] + ['\t'.join([str(sample['sampleid']), *[str(values.get(taxon, 0)) for taxon in labels]])
                        for sample, values in rows]
    table = ('\n'.join(lines) + '\n').encode()
    base = {'input': 'unused', 'format': 'delimited', 'delimiter': 'tab', 'orientation': 'samples_by_taxa',
            'value_type': 'count', 'missing': 'error', 'empty_samples': 'error'}
    rare = pa.RarefactionSpec(**base, method='rarefaction', sizes='minimum_total')
    validation = pa.validate_rarefaction(rare, table)
    totals = [pa.validate_rarefaction(rare, (header + '\n' + row + '\n').encode())['sizes'][0]
              for row in lines[1:]]
    explicit = pa.RarefactionSpec(**base, method='rarefaction', sizes=[282])
    pairs = [[str(a['sampleid']), str(b['sampleid'])] for a, b in zip(samples, samples[1:])]
    homogeneity = pa.CountHomogeneitySpec(**base, method='count_homogeneity', pairs=pairs,
                                         simulations=99999, seed=7112026)
    ages = []
    for sample in samples:
        primary = next(age for age in sample['ages'] if age['chronologyid'] == 37590)
        alternative = next(age for age in sample['ages'] if age['chronologyid'] == 37589)
        ages.append({'sample_id': sample['sampleid'], 'depth': sample['depth'], 'age': primary['age'],
                     'ageyounger': primary['ageyounger'], 'ageolder': primary['ageolder'],
                     'alternative_age': alternative['age']})
    return {'scope': 'Proposal intake and resource validation only; no rarefaction estimates or random tables computed',
            'source_url': 'https://api.neotomadb.org/v2.0/data/downloads/52767',
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'dataset_id': 52767, 'collection_handle': collection['handle'], 'dataset_dois': dataset['doi'],
            'source_publication_doi': '10.1016/S1040-6182(98)00046-9',
            'intake_rule': 'pollen; ecologicalgroup TRSH or UPHE; NISP; distinct taxon IDs; absent datum assumed zero for preflight only',
            'n_levels': len(samples), 'n_taxa': len(labels),
            'api_totals_summary': {'min': min(totals), 'median': median(totals), 'max': max(totals)},
            'validations': {'minimum_total': validation, 'explicit_282': pa.validate_rarefaction(explicit, table),
                            'adjacent_pairs': pa.validate_count_homogeneity(homogeneity, table)},
            'chronology_id': 37590, 'alternative_chronology_id': 37589,
            'point_age_min': min(age['age'] for age in ages), 'point_age_max': max(age['age'] for age in ages),
            'point_age_bins_10ka': dict(sorted(Counter(str(int(age['age'] // 10000)) for age in ages).items())),
            'chronology_examples': [age for age in ages if 35000 <= age['age'] <= 47000 or age == ages[-1]]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('download', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(check(args.download), indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end='')
