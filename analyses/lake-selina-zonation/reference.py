"""Independent canonical-coordinate and pinned-rioja arithmetic check of inspected API results."""

import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
IDS = ('archive_hellinger', 'repaired_hellinger', 'archive_relative', 'repaired_relative')
RTOL = 1e-10
ATOL = 0.0


def from_bits(bits):
    return struct.unpack('>d', struct.pack('>Q', bits))[0]


def nearest_coordinate(q, root):
    """Round q or sqrt(q) independently by bounded binary64-encoding bisection."""
    if not 0 <= q <= 1:
        raise ValueError('Coordinate target must lie in [0,1]')
    if q in (0, 1):
        return float(q)
    low, high = 0, 0x3ff0000000000000
    while high - low > 1:
        middle = (low + high) // 2
        value = Fraction(from_bits(middle))
        if (value * value if root else value) <= q:
            low = middle
        else:
            high = middle
    midpoint = (Fraction(from_bits(low)) + Fraction(from_bits(high))) / 2
    threshold = midpoint * midpoint if root else midpoint
    if q < threshold or (q == threshold and low % 2 == 0):
        return from_bits(low)
    return from_bits(high)


def independent_coordinates(values, transform):
    root = transform == 'hellinger'
    if transform not in ('hellinger', 'relative_abundance'):
        raise ValueError(f'Unsupported fixed transform: {transform}')
    coordinates = []
    for row in values:
        exact = [Fraction(value) for value in row]
        total = sum(exact)
        if total <= 0:
            raise ValueError('Reference requires nonempty retained rows')
        coordinates.append([nearest_coordinate(value / total, root) for value in exact])
    return coordinates


def api_memberships(result, k):
    cuts = {boundary['boundary'] for boundary in result['boundaries'] if boundary['split_rank'] < k}
    label, labels = 1, []
    for index in range(result['n']):
        if index in cuts:
            label += 1
        labels.append(label)
    return labels


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path):
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return path.name


def compare(result, reference):
    numeric = []
    def add(field, actual, expected):
        if not (math.isfinite(actual) and math.isfinite(expected)):
            raise ValueError(f'Non-finite comparison at {field}')
        difference = abs(actual - expected)
        numeric.append({'field': field, 'r_value': actual, 'api_value': expected,
                        'absolute_difference': difference, 'allowed_difference': RTOL * abs(expected),
                        'relative_difference': difference / abs(expected) if expected else (0.0 if not difference else None),
                        'passed': difference <= RTOL * abs(expected)})
    by_boundary = {row['boundary']: row for row in result['merges']}
    for boundary, value in enumerate(reference['per_boundary'], start=1):
        add(f'boundary:{boundary}:cumulative', value, by_boundary[boundary]['cumulative'])
    add('total_dispersion', reference['total_dispersion'], result['total_dispersion'])
    for rank, (gain, expectation, api) in enumerate(zip(reference['gains'], reference['expectations'],
                                                     result['broken_stick'], strict=True), start=1):
        if api['rank'] != rank:
            raise ValueError('API broken-stick ranks are not sequential')
        add(f'rank:{rank}:gain', gain, api['gain'])
        add(f'rank:{rank}:expected', expectation, api['expected'])
    rank_mismatches = []
    for boundary, r_rank in enumerate(reference['split_ranks'], start=1):
        api_rank = result['boundaries'][boundary - 1]['split_rank']
        if r_rank != api_rank:
            rank_mismatches.append({'boundary': boundary, 'r_rank': r_rank, 'api_rank': api_rank})
    verdict_mismatches = [{'rank': index+1, 'r_exceeds': actual, 'api_exceeds': expected['exceeds']}
                          for index, (actual, expected) in enumerate(zip(reference['exceeds'], result['broken_stick'], strict=True))
                          if actual != expected['exceeds']]
    selection_mismatch = None if reference['selected_zones'] == result['retention']['selected_zones'] else {
        'r_selected_zones': reference['selected_zones'], 'api_selected_zones': result['retention']['selected_zones']}
    partition_mismatches, membership_checks = [], 0
    for k, r_labels in enumerate(reference['partitions'], start=1):
        expected = api_memberships(result, k)
        membership_checks += len(expected)
        differences = [{'sample_id': result['sample_ids'][i], 'r_zone': r_value, 'api_zone': api_value}
                       for i, (r_value, api_value) in enumerate(zip(r_labels, expected, strict=True)) if r_value != api_value]
        if differences:
            partition_mismatches.append({'zones': k, 'differences': differences})
    finite_relative = [row['relative_difference'] for row in numeric if row['relative_difference'] is not None]
    summary = {'n': result['n'], 'numeric_quantities_checked': len(numeric),
               'numeric_failures': sum(not row['passed'] for row in numeric),
               'maximum_absolute_difference': max(row['absolute_difference'] for row in numeric),
               'maximum_relative_difference': max(finite_relative, default=0.0),
               'zero_expected_nonzero_reference': sum(row['api_value'] == 0 and row['r_value'] != 0 for row in numeric),
               'partition_memberships_checked': membership_checks,
               'partition_mismatches': partition_mismatches, 'split_rank_mismatches': rank_mismatches,
               'retention_comparisons_checked': len(result['broken_stick'])+1,
               'retention_verdict_mismatches': verdict_mismatches, 'selection_mismatch': selection_mismatch,
               'small_margin_warnings': [warning for warning in result['warnings'] if warning['code'].startswith('small_margin_')]}
    summary['passed'] = not (summary['numeric_failures'] or partition_mismatches or rank_mismatches or verdict_mismatches or selection_mismatch)
    return summary, numeric


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, default=HERE / 'results.json')
    parser.add_argument('--work', type=Path, default=HERE / 'runs-reference')
    parser.add_argument('--receipt', type=Path, default=HERE / 'reference-check.json')
    args = parser.parse_args()
    source = json.loads(args.results.read_text())
    analyses = source['coniss']
    if set(analyses) != set(IDS):
        raise ValueError('Expected exactly the four frozen CONISS analyses')
    args.work.mkdir(parents=True, exist_ok=True)
    cases, coordinate_checks = [], 0
    from palaeo_agent.coniss import coordinates as engine_coordinates
    for name in IDS:
        result = analyses[name]
        values = result['retained_counts']
        coordinates = independent_coordinates(values, result['transform'])
        engine = engine_coordinates(values, result['transform'], result['sample_ids'], result['taxon_ids'])
        if coordinates != engine:
            raise AssertionError(f'Independently rounded coordinates disagree: {name}')
        coordinate_checks += sum(len(row) for row in coordinates)
        cases.append({'id': name, 'coordinates': coordinates, 'sample_ids': result['sample_ids']})
    request_path = args.work / 'coordinates.json'
    request_path.write_text(json.dumps({'cases': cases}, indent=2) + '\n')
    r_output = args.work / 'rioja.json'
    subprocess.run(['Rscript', '--vanilla', str(HERE / 'reference.R'), str(request_path), str(r_output)], check=True)
    r = json.loads(r_output.read_text())
    r_cases = {case['id']: case for case in r['cases']}
    summaries, comparisons = {}, []
    for name in IDS:
        if analyses[name]['sample_ids'] != r_cases[name]['sample_ids']:
            raise AssertionError(f'R sample identities/order disagree: {name}')
        summary, numeric = compare(analyses[name], r_cases[name])
        summaries[name] = summary
        comparisons.extend({'analysis_id': name, **row} for row in numeric)
    with (args.work / 'numeric-comparisons.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparisons[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(comparisons)
    receipt = {'status': 'passed' if all(case['passed'] for case in summaries.values()) else 'failed',
               'scope': 'Independent exact coordinate rounding and rioja arithmetic on matched coordinates; no sampling coverage or ecological-validity claim',
               'coordinate_rounding': 'Independent bounded binary64 bisection with exact midpoint/half-even checks; compared with production coordinates',
               'coordinate_values_checked': coordinate_checks, 'rtol': RTOL, 'atol': ATOL,
               'partition_rule': 'Every k from 1 to n; labels normalized to first occurrence, no membership tolerance',
               'r_version': r['r_version'], 'packages': r['packages'], 'cases': summaries,
               'numeric_quantities_checked': len(comparisons),
               'partition_memberships_checked': sum(case['partition_memberships_checked'] for case in summaries.values()),
               'retention_comparisons_checked': sum(case['retention_comparisons_checked'] for case in summaries.values()),
               'reference_retention': 'Declared consecutive-prefix rule applied to R gains and expectations; rioja does not return a selected k',
               'maximum_absolute_difference': max(row['absolute_difference'] for row in comparisons),
               'inputs': [{'file': display_path(args.results), 'sha256': digest(args.results)}],
               'reference_files': [{'file': display_path(path), 'sha256': digest(path)} for path in
                                   (Path(__file__), HERE / 'reference.R', ROOT / 'references/r/renv.lock')],
               'intermediates': [{'file': path.name, 'sha256': digest(path)} for path in (request_path, r_output)],
               'command': 'uv run analyses/lake-selina-zonation/reference.py'}
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'coordinate_values_checked': coordinate_checks,
                      'numeric_quantities_checked': receipt['numeric_quantities_checked'],
                      'partition_memberships_checked': receipt['partition_memberships_checked'],
                      'maximum_absolute_difference': receipt['maximum_absolute_difference'],
                      'case_status': {name: summary['passed'] for name, summary in summaries.items()}}, indent=2))
    if receipt['status'] != 'passed':
        raise SystemExit('Independent reference disagreement: inspect reference-check.json and runs-reference/')


if __name__ == '__main__':
    main()
