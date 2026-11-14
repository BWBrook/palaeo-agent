"""Independently check the saved intake's exact accounting and metadata selections."""

import ast
import collections
import csv
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLOOR = Fraction(4, 5)
PERCENT_CALIBRATION_LIMIT = Fraction(201, 2)
SCHEMES = ('primary', 'coarse')
TALLY_DIR = HERE.parents[1] / 'references/independent/2026-11-14-tally-semantics'


def rational(token):
    value = Decimal(token)
    assert value.is_finite() and value >= 0
    return Fraction(value)


def rows(path, delimiter=','):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter=delimiter))


def table(path):
    material = rows(path, '\t')
    ids = [row.pop('sample_id') for row in material]
    assert len(ids) == len(set(ids))
    return dict(zip(ids, ({key: rational(value) for key, value in row.items()}
                          for row in material), strict=True))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preference(row):
    return (row['original_sample_code'] != '1', rational(row['original_sample_code']),
            int(row['sample_id']))


def inclusion_diagnostics(sources, seed):
    declarations = [node for node in ast.parse((TALLY_DIR / 'check.py').read_text()).body
                    if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'FAMILIES'
                            for target in node.targets)]
    assert len(declarations) == 1
    families = ast.literal_eval(declarations[0].value)
    historical = json.loads((TALLY_DIR / 'receipt.json').read_text())
    exact_sum, cases = [], []
    for source in ('fossil', 'modern_percent', 'modern_nisp'):
        header = set(next(iter(sources[source].values())))
        for broad, children in families.items():
            present = [label for label in children if label in header]
            if broad not in header or not present:
                continue
            cooccurring, sum_rows, single_rows = [], [], []
            for sample, values in sources[source].items():
                broad_value = values[broad]
                child_values = [values[label] for label in present]
                child_sum = sum(child_values, Fraction())
                if broad_value <= 0 or child_sum <= 0:
                    continue
                dataset = '52767' if source == 'fossil' else seed[sample]['datasetid']
                cooccurring.append(dataset)
                if broad_value < child_sum:
                    sum_rows.append((sample, dataset))
                if broad_value < max(child_values):
                    single_rows.append((sample, dataset))
            sum_datasets = sorted({dataset for _, dataset in sum_rows})
            single_datasets = sorted({dataset for _, dataset in single_rows})
            datasets_with_both = sorted(set(cooccurring))
            exact_sum.append(dict(source=source, broad=broad, narrow=present,
                rows_with_both=len(cooccurring), rows_contradicting_inclusion=len(sum_rows),
                datasets_contradicting=sum_datasets, datasets_with_both=datasets_with_both))
            cases.append(dict(source=source, broad=broad, narrow=present,
                rows_with_both=len(cooccurring), sum_contradiction_rows=len(sum_rows),
                max_child_contradiction_rows=len(single_rows),
                sum_contradicting_datasets=sum_datasets,
                max_child_contradicting_datasets=single_datasets,
                datasets_with_both=datasets_with_both))
    assert exact_sum == historical['results']
    total = sum(len(case['datasets_with_both']) for case in cases)
    summed = sum(len(case['sum_contradicting_datasets']) for case in cases)
    single = sum(len(case['max_child_contradicting_datasets']) for case in cases)
    assert (summed, single, total) == (31, 30, 49)
    return {'arithmetic': 'Exact decimal-to-rational comparisons; original float calculation not imported',
            'canonical_specification': 'FAMILIES literal read by AST from committed check.py; no script execution',
            'historical_sum_receipt_matches_exact': True,
            'cooccurring_dataset_family_combinations': total,
            'sum_contradicting_combinations': summed,
            'max_child_contradicting_combinations': single,
            'cases': cases,
            'limitations': [
                'Counts use the historical subset with positive broad and at least one positive child; broad-zero rows are not included',
                'Broad < sum(children) rejects full inclusion only if child tallies are disjoint and share a common numerical basis',
                'Broad < max(single child) avoids the disjoint-child assumption, but still requires a common numerical basis',
                'Neither diagnostic proves universal mutual exclusivity, residual identification, common denominators or a uniform counting protocol',
                'Additive archived tallies remain the explicitly authorized working convention'],
            'evidence_files': [{'file': str(path.relative_to(HERE.parents[1])), 'sha256': sha(path)}
                               for path in (TALLY_DIR / 'check.py', TALLY_DIR / 'receipt.json')]}


def main():
    receipt = json.loads((HERE / 'preflight-check.json').read_text())
    for group in ('input_files', 'artifacts'):
        for item in receipt[group]:
            assert sha(HERE / item['file']) == item['sha256'], item['file']
    sources = {name: table(HERE / 'data' / f'{name}.tsv')
               for name in ('fossil', 'modern_percent', 'modern_nisp')}
    legacy = {'fossil': HERE.parent / 'lake-selina/data/counts.tsv',
              'modern_percent': HERE.parent / 'tas-surface/data/percent.tsv',
              'modern_nisp': HERE.parent / 'pollen-media/data/counts.tsv'}
    for name, path in legacy.items():
        assert sources[name] == table(path), name
    repaired = table(HERE / 'data/repaired-query.tsv')
    assert list(repaired) == ['531331']
    original = table(HERE.parent / 'lake-selina/data/counts-final.tsv')['531331']
    assert repaired['531331'] == original
    changes = [(label, sources['fossil']['531331'][label], value)
               for label, value in original.items()
               if value != sources['fossil']['531331'][label]]
    assert changes == [('Lagarostrobos franklinii', Fraction(0), Fraction(72))]
    cases = {**sources, 'repaired_query': repaired}
    walk = {scheme: {name: {} for name in sources} for scheme in SCHEMES}
    for scheme in SCHEMES:
        for record in rows(HERE / f'crosswalk-{scheme}.csv'):
            bucket = walk[scheme][record['source_table']]
            assert record['source_label'] not in bucket
            bucket[record['source_label']] = record
        for name, raw in sources.items():
            assert set(walk[scheme][name]) == set(next(iter(raw.values())))
    coarse_targets = collections.defaultdict(set)
    for name in sources:
        assert {key for key, rule in walk['primary'][name].items()
                if rule['loss_class'] == 'outside_dryland'} == {
                    key for key, rule in walk['coarse'][name].items()
                    if rule['loss_class'] == 'outside_dryland'}
        for label, primary in walk['primary'][name].items():
            if primary['action'] == 'map':
                coarse = walk['coarse'][name][label]
                assert coarse['action'] == 'map'
                coarse_targets[primary['target_bin']].add(coarse['target_bin'])
    assert all(len(targets) == 1 for targets in coarse_targets.values())

    coverage = rows(HERE / 'coverage.csv')
    index = {(row['scheme'], row['source_table'], row['sample_id']): row for row in coverage}
    assert len(index) == len(coverage) == sum(map(len, cases.values())) * len(SCHEMES)
    computed, matched_cells = {}, 0
    for scheme in SCHEMES:
        target_sets = []
        for name, raw in cases.items():
            rules = walk[scheme]['fossil' if name == 'repaired_query' else name]
            mapped = table(HERE / 'data' / f'{scheme}-{name}.tsv')
            assert set(mapped) == set(raw)
            target_sets.append(set(next(iter(mapped.values()))))
            for sample_id, values in raw.items():
                buckets = collections.defaultdict(Fraction)
                target = collections.defaultdict(Fraction)
                for label, value in values.items():
                    rule = rules[label]
                    assert rule['action'] in ('map', 'exclude')
                    assert (rule['action'] == 'map') == (rule['loss_class'] == 'none')
                    assert rule['loss_class'] in ('none', 'outside_dryland', 'incomparable')
                    buckets[rule['loss_class']] += value
                    if rule['action'] == 'map':
                        target[rule['target_bin']] += value
                assert dict(target) == mapped[sample_id], (scheme, name, sample_id)
                matched_cells += len(target)
                total = sum(values.values(), Fraction())
                retained = buckets['none']
                dryland = total - buckets['outside_dryland']
                ratio = retained / dryland if dryland else None
                assert total == sum(buckets.values(), Fraction())
                assert retained == sum(mapped[sample_id].values(), Fraction())
                saved = index[scheme, name, sample_id]
                for field, value in (('source_weight_exact', total),
                                     ('dryland_weight_exact', dryland),
                                     ('retained_weight_exact', retained)):
                    assert Fraction(saved[field]) == value, (scheme, name, sample_id, field)
                for field, value in (('source_weight', total), ('dryland_weight', dryland),
                                     ('retained_weight', retained),
                                     ('outside_dryland_weight', buckets['outside_dryland']),
                                     ('incomparable_weight', buckets['incomparable'])):
                    assert saved[field] == format(float(value), '.12g'), field
                assert saved['retained_fraction_exact'] == ('' if ratio is None else str(ratio))
                assert saved['retained_fraction'] == ('' if ratio is None else format(float(ratio), '.12g'))
                assert Fraction(saved['retained_weight_floor']) == FLOOR
                assert (saved['meets_floor'] == 'True') == (ratio is not None and ratio >= FLOOR)
                assert (saved['empty_retained'] == 'True') == (retained == 0)
                computed[scheme, name, sample_id] = ratio, retained, dryland
        assert all(targets == target_sets[0] for targets in target_sets)

    seed_rows = rows(HERE / 'metadata-seed.csv')
    seed = {row['sample_id']: row for row in seed_rows}
    ledger = rows(HERE / 'sample-ledger.csv')
    modern_where = {sample: name for name in ('modern_percent', 'modern_nisp')
                    for sample in sources[name]}
    assert len(seed_rows) == len(seed) == len(ledger) == len(modern_where) == 68
    assert set(seed) == set(modern_where) == {row['sample_id'] for row in ledger}
    all_units = collections.defaultdict(list)
    for row in seed_rows:
        all_units[row['collectionunitid']].append(row)
    ranks = {}
    for group in all_units.values():
        for rank, row in enumerate(sorted(group, key=preference), 1):
            assert int(row['representative_preference']) == rank
            ranks[row['sample_id']] = rank
    denominator_flags = {}
    for row in ledger:
        sample = row['sample_id']
        source = modern_where[sample]
        units = 'percent' if source == 'modern_percent' else 'NISP'
        assert seed[sample]['source_units'] == units
        source_total = sum(sources[source][sample].values(), Fraction())
        assert Fraction(row['source_input_weight_exact']) == source_total
        assert row['source_input_weight'] == format(float(source_total), '.12g')
        denominator_flags[sample] = units == 'percent' and source_total > PERCENT_CALIBRATION_LIMIT
        assert (row['denominator_unresolved'] == 'True') == denominator_flags[sample]
        assert row['denominator_screen'] == 'raw_extracted_land_plant_weight_above_100.5_for_percent_only'
    assert {sample for sample, flag in denominator_flags.items() if flag} == set(receipt['denominator_unresolved_ids'])
    candidates, calibrations, flagged_candidates = {}, {}, {}
    for scheme in SCHEMES:
        good, calibration_eligible = [], []
        for row in ledger:
            sample = row['sample_id']
            metadata = seed[sample]
            assert all(row[key] == value for key, value in metadata.items())
            ratio, retained, _ = computed[scheme, modern_where[sample], sample]
            reasons = []
            if metadata['metadata_modern_eligible'] != 'true':
                reasons.append('metadata_ineligible')
            if metadata[f'{scheme}_taxonomic_eligible'] != 'true':
                reasons.append('dataset_resolution_ineligible')
            if retained == 0:
                reasons.append('empty_retained')
            if ratio is None or ratio < FLOOR:
                reasons.append('below_retained_weight_floor')
            eligible = not reasons
            assert (row[f'{scheme}_candidate_provisional'] == 'True') == eligible
            assert row[f'{scheme}_candidate_reason'] == (';'.join(reasons) if reasons else 'qualifies_under_fixed_0.80_rule')
            calibration_reasons = [*reasons, *(['denominator_unresolved'] if denominator_flags[sample] else [])]
            assert (row[f'{scheme}_calibration_eligible'] == 'True') == (not calibration_reasons)
            assert row[f'{scheme}_calibration_reason'] == (';'.join(calibration_reasons) if calibration_reasons else
                                                         'passes_declared_calibration_eligibility_rule')
            if eligible:
                good.append(metadata)
            if not calibration_reasons:
                calibration_eligible.append(metadata)
        candidate_units = {row['collectionunitid'] for row in good}
        units = collections.defaultdict(list)
        for row in calibration_eligible:
            units[row['collectionunitid']].append(row)
        chosen = {min(group, key=preference)['sample_id'] for group in units.values()}
        saved = receipt['representatives'][scheme]
        assert chosen == set(saved['calibration_ids'])
        assert {row['sample_id'] for row in good} == set(saved['candidate_ids'])
        assert set(saved['units_without_qualifying_candidate']) == set(all_units) - candidate_units
        assert set(saved['units_without_eligible_calibrator']) == set(all_units) - set(units)
        assert set(saved['units_with_candidates_without_calibrator']) == candidate_units - set(units)
        flagged_candidates[scheme] = {row['sample_id'] for row in good if denominator_flags[row['sample_id']]}
        assert set(saved['candidate_denominator_unresolved_ids']) == flagged_candidates[scheme]
        assert set(saved['fallback_representatives']) == {sample for sample in chosen if ranks[sample] > 1}
        for row in ledger:
            assert (row[f'{scheme}_calibration_provisional'] == 'True') == (row['sample_id'] in chosen)
        candidates[scheme] = {row['sample_id'] for row in good}
        calibrations[scheme] = chosen

    fossils = rows(HERE / 'fossil-ledger.csv')
    assert len(fossils) == len(sources['fossil']) == 72
    assert {row['sample_id'] for row in fossils} == set(sources['fossil'])
    statuses = {}
    for scheme in SCHEMES:
        counts = collections.Counter()
        for row in fossils:
            ratio, retained, _ = computed[scheme, 'fossil', row['sample_id']]
            expected = ('empty_retained_row' if retained == 0 else
                        'ready' if ratio is not None and ratio >= FLOOR else 'taxonomy_limited')
            assert row[f'{scheme}_provisional_status'] == expected
            counts[expected] += 1
        statuses[scheme] = dict(counts)
        assert statuses[scheme] == receipt['fossil_status_counts'][scheme]
    for sample, metadata in seed.items():
        if metadata['primary_taxonomic_eligible'] == 'true':
            name = modern_where[sample]
            assert computed['primary', name, sample][1:] == computed['coarse', name, sample][1:]
    for name in ('fossil', 'repaired_query'):
        for sample in cases[name]:
            assert computed['primary', name, sample][1:] == computed['coarse', name, sample][1:]
    assert receipt['guard_probe_passed'] and receipt['forbidden_calls_after_probe'] == 0
    assert receipt['same_dryland_bins_across_schemes']
    tally = inclusion_diagnostics(sources, seed)
    audit = {
        'status': 'passed',
        'scope': 'Independent exact accounting and metadata selection from saved source tables and crosswalks; no distance calculation or scientific-validity claim',
        'coverage_rows_verified': len(coverage),
        'mapped_cells_verified': matched_cells,
        'mass_mismatches': 0,
        'candidate_counts': {key: len(value) for key, value in candidates.items()},
        'representative_counts': {key: len(value) for key, value in calibrations.items()},
        'identical_candidate_sets': candidates['primary'] == candidates['coarse'],
        'identical_calibration_sets': calibrations['primary'] == calibrations['coarse'],
        'percentage_calibration_limit_exact': str(PERCENT_CALIBRATION_LIMIT),
        'percentage_screen_scope': 'Native percent rows only; exact raw extracted land-plant sum before exclusions; NISP exempt; candidates unaffected',
        'denominator_unresolved_ids': sorted(sample for sample, flag in denominator_flags.items() if flag),
        'candidate_denominator_unresolved_ids': {scheme: sorted(samples) for scheme, samples in flagged_candidates.items()},
        'fossil_status_counts': statuses,
        'ready_fossil_ids': [row['sample_id'] for row in fossils if row['primary_provisional_status'] == 'ready'],
        'same_dryland_bins_verified': True,
        'retained_weight_and_dryland_preserved_for_primary_eligible_rows': True,
        'preparation_receipt_forbidden_calls': receipt['forbidden_calls_after_probe'],
        'audit_uses_only_standard_library': True,
        'inclusion_diagnostics': tally,
        'inputs': [{'file': name, 'sha256': sha(HERE / name)}
                   for name in ('audit.py', 'preflight-check.json')],
        'command': 'uv run analyses/lake-selina-analogues/audit.py',
    }
    (HERE / 'audit-check.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
