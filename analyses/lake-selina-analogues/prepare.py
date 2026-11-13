"""Draft application-6 intake and weight accounting; all distance entry points are guarded."""

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
import csv
from decimal import Decimal
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
from unittest.mock import patch

import palaeo_agent as pa
from palaeo_agent import community, coniss, methods, permanova
from palaeo_agent.study import ExcludeTaxa, MapTaxa, Select, TableInput, apply, read_table

HERE = Path(__file__).resolve().parent
PRIMER = 'fcc02a57db1ffa2a86d14e7c2540bd7bfa89c14e7e5b3334286f9a24b16747f6'
FLOOR = Fraction(4, 5)
PERCENT_DATASETS = [74429, 75430, 74914, 74643, 74779, 74795, 74778, 74764, 74160,
                    74142, 74304, 74699, 74569, 74618, 74701, 74780, 73988, 74777,
                    74303, 74141, 75423, 74644, 74798, 74766, 75421]
MODERN_SOURCE = HERE.parent / 'tas-surface/source/neotoma-tas-surface-download.json'
FOSSIL_SOURCE = HERE.parent / 'lake-selina/source/neotoma-52767-download.json'
MODERN_SHA = '0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36'
FOSSIL_SHA = '5dd1a71cf7a655f08441e59b866b3eb64c893b164cc8e9320d9ea2d7507ead24'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def csv_bytes(rows, fields=None, delimiter=','):
    fields = fields or list(rows[0])
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter=delimiter, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def write_table(path, table):
    order = sorted(table['columns'])
    indices = [table['columns'].index(label) for label in order]
    rows = [dict(zip(['sample_id', *order], [sample, *[row[i] for i in indices]]))
            for sample, row in zip(table['samples'], table['values'], strict=True)]
    path.write_bytes(csv_bytes(rows, delimiter='\t'))


def table(data, kind):
    declaration = TableInput(kind=kind, path='unused.tsv', format='delimited',
                             delimiter='tab', orientation='samples_by_taxa')
    return read_table(data, declaration)


def number(token):
    value = Decimal(token)
    assert value.is_finite() and value >= 0
    return Fraction(value)


def text(value):
    return format(float(value), '.12g')


def validate_file(path, kind):
    return pa.validate(dict(method='community', input=str(path), format='delimited', delimiter='tab',
        orientation='samples_by_taxa', value_type='abundance' if kind == 'abundance' else 'count',
        transform='relative_abundance', distance='braycurtis', dimensions=1, missing='error', empty_samples='error'))


def validate_mapped(path, current, kind, out, key):
    nonempty = [sample for sample, row in zip(current['samples'], current['values'], strict=True)
                if any(number(value) > 0 for value in row)]
    empty = [sample for sample in current['samples'] if sample not in set(nonempty)]
    if len(nonempty) <= 1:
        return {'status': 'not_applicable', 'intake_empty_ids': empty,
                'scope': 'Fewer than two nonempty rows; community ordination validation is not applicable; source values and API preparation checked'}
    if empty:
        subset, _ = apply(Select(op='select', samples=nonempty,
            reason='Structural validation subset only; every empty row remains in the intake ledger'), current, kind)
        path = out / 'runs-validation' / f'{key.replace("/", "-")}.tsv'
        path.parent.mkdir(parents=True, exist_ok=True)
        write_table(path, subset)
    return {**validate_file(path, kind), 'intake_empty_ids': empty,
            'scope_note': 'Validation uses nonempty rows only; no intake row is silently removed'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE)
    args = parser.parse_args()
    out = args.output.resolve()
    (out / 'data').mkdir(parents=True, exist_ok=True)
    primer = pa.primer()
    assert primer['sha256'] == PRIMER
    guarded_calls = []

    def forbidden(*args, **kwargs):
        guarded_calls.append('forbidden analysis')
        raise AssertionError('Distances and scientific analyses are forbidden during intake drafting')

    targets = [(pa, 'run'), (pa, 'run_study'), (methods, 'calculate_method'),
               (community, 'community_distances'), (community, 'analyse_community'),
               (community, 'calculate_community'), (coniss, 'zonation'),
               (permanova, 'calculate_permanova')]
    with ExitStack() as stack:
        for owner, name in targets:
            stack.enter_context(patch.object(owner, name, forbidden))
        try:
            community.community_distances(None, transform='relative_abundance', distance='braycurtis')
        except AssertionError:
            pass
        else:
            raise AssertionError('Distance guard probe failed')
        guarded_calls.clear()
        extracted, provenance, metadata, validations = {}, {}, {}, {}
        requests = {
            'fossil': (FOSSIL_SOURCE, FOSSIL_SHA, [52767], 'NISP', ['pollen'], 'depth'),
            'modern_percent': (MODERN_SOURCE, MODERN_SHA, PERCENT_DATASETS, 'percent',
                               ['pollen', 'pollen/spore', 'spore'], 'source'),
            'modern_nisp': (MODERN_SOURCE, MODERN_SHA, [74305, 74913], 'NISP',
                            ['pollen', 'pollen/spore', 'spore'], 'source'),
        }
        existing = {'fossil': HERE.parent / 'lake-selina/data/counts.tsv',
                    'modern_percent': HERE.parent / 'tas-surface/data/percent.tsv',
                    'modern_nisp': HERE.parent / 'pollen-media/data/counts.tsv'}
        for name, (source, digest, datasets, units, elements, order) in requests.items():
            request = dict(source=str(source), source_sha256=digest, datasets=datasets, units=units,
                           elements=elements, ecological_groups=['TRSH', 'UPHE'], absent_taxa='zero', row_order=order)
            result = pa.neotoma_extract(request, out / 'runs-extraction')
            bundle = Path(result['bundle'])
            assert pa.inspect_neotoma(bundle)['status'] == 'verified'
            data = (bundle / 'table.tsv').read_bytes()
            kind = 'abundance' if units == 'percent' else 'counts'
            parsed = table(data, kind)
            old = table(existing[name].read_bytes(), kind)
            assert parsed == old, name
            (out / 'data' / f'{name}.tsv').write_bytes(data)
            validations[f'raw/{name}'] = validate_file(out / 'data' / f'{name}.tsv', kind)
            assert validations[f'raw/{name}']['status'] == 'valid'
            extracted[name] = parsed, kind, units
            metadata[name] = list(csv.DictReader((bundle / 'samples.csv').open()))
            provenance[name] = {'bundle': str(bundle.relative_to(out)), 'source_sha256': digest,
                                'manifest_sha256': sha(bundle / 'manifest.json'),
                                'table_sha256': hashlib.sha256(data).hexdigest()}
        seeds = list(csv.DictReader((HERE / 'metadata-seed.csv').open()))
        seed_ids = {row['sample_id'] for row in seeds}
        assert len(seeds) == len(seed_ids) == 68
        assert not seed_ids.intersection(extracted['fossil'][0]['samples'])
        modern_meta = {row['sample_id']: row for name in ('modern_percent', 'modern_nisp') for row in metadata[name]}
        assert seed_ids == set(modern_meta)
        units_by_id = {sample: extracted[name][2] for name in ('modern_percent', 'modern_nisp')
                       for sample in extracted[name][0]['samples']}
        for row in seeds:
            actual = modern_meta[row['sample_id']]
            assert actual['collunittype'] == 'Modern' and actual['analysisunitname'] == 'surface sample'
            assert row['metadata_modern_eligible'] == 'true' and row['source_units'] == units_by_id[row['sample_id']]
            for seed_key, native_key in [('datasetid', 'datasetid'), ('collectionunitid', 'collectionunitid'),
                                         ('site', 'sitename'), ('original_sample_code', 'depth')]:
                assert row[seed_key] == actual[native_key], (row['sample_id'], seed_key)
        recorded = defaultdict(set)
        for name in ('modern_percent', 'modern_nisp'):
            raw = extracted[name][0]
            for sample, values in zip(raw['samples'], raw['values'], strict=True):
                unit = modern_meta[sample]['collectionunitid']
                for label, value in zip(raw['columns'], values, strict=True):
                    if label in ('Nothofagus', 'Nothofagus cunninghamii', 'Nothofagus gunnii') and number(value) > 0:
                        recorded[unit].add(label)
        genus_only_datasets = set()
        for row in seeds:
            bins = recorded[row['collectionunitid']]
            assert not ('Nothofagus' in bins and len(bins) > 1)
            resolution = 'genus_only' if bins == {'Nothofagus'} else 'species_recorded' if bins else 'uninformative'
            assert row['nothofagus_resolution'] == resolution, row['sample_id']
            assert (row['primary_taxonomic_eligible'] == 'true') == (resolution != 'genus_only')
            assert row['coarse_taxonomic_eligible'] == 'true'
            if resolution == 'genus_only': genus_only_datasets.add(int(row['datasetid']))
        assert genus_only_datasets == {75430, 74779, 74795, 74777, 75423, 75421}
        weights, derivations, maps = [], {}, {}
        schemes = ('primary', 'coarse')
        for scheme in schemes:
            rows = list(csv.DictReader((HERE / f'crosswalk-{scheme}.csv').open()))
            maps[scheme] = {}
            for name, (raw, kind, units) in extracted.items():
                selected = [row for row in rows if row['source_table'] == name]
                assert len(selected) == len(raw['columns'])
                assert {r['source_label'] for r in selected} == set(raw['columns'])
                assert len({r['source_label'] for r in selected}) == len(selected)
                maps[scheme][name] = {r['source_label']: r for r in selected}
            assert {r['source_table'] for r in rows} == set(extracted)
        coarsen = defaultdict(set)
        for name, (raw, _, _) in extracted.items():
            assert {label for label, r in maps['primary'][name].items() if r['loss_class'] == 'outside_dryland'} == {
                label for label, r in maps['coarse'][name].items() if r['loss_class'] == 'outside_dryland'}, (name, 'dryland denominator changed')
            for label in raw['columns']:
                a, b = maps['primary'][name][label], maps['coarse'][name][label]
                if a['action'] == 'map':
                    assert b['action'] == 'map', (name, label, 'coarse drops a primary bin')
                    coarsen[a['target_bin']].add(b['target_bin'])
        assert all(len(values) == 1 for values in coarsen.values()), coarsen
        final_path = HERE.parent / 'lake-selina/data/counts-final.tsv'
        assert sha(final_path) == 'a15f912401a46242a38b48d51211acfb731d70743190cefa27c75474c429d429'
        final = table(final_path.read_bytes(), 'counts')
        validations['raw/repaired_dryland'] = validate_file(final_path, 'counts')
        assert validations['raw/repaired_dryland']['status'] == 'valid'
        repaired, _ = apply(Select(op='select', samples=['531331'], reason='Previously accepted one-row reconstruction'), final, 'counts')
        raw_fossil = extracted['fossil'][0]
        original = dict(zip(raw_fossil['columns'], raw_fossil['values'][raw_fossil['samples'].index('531331')]))
        changes = [(label, original[label], value) for label, value in zip(repaired['columns'], repaired['values'][0])
                   if number(original[label]) != number(value)]
        assert changes == [('Lagarostrobos franklinii', '0', '72')]
        write_table(out / 'data/repaired-query.tsv', repaired)
        cases = dict(extracted, repaired_query=(repaired, 'counts', 'NISP'))
        for scheme in schemes:
            target_sets = []
            for name, (raw, kind, units) in cases.items():
                source = 'fossil' if name == 'repaired_query' else name
                mapping = {label: maps[scheme][source][label] for label in raw['columns']}
                for record in mapping.values():
                    assert record['action'] in ('map', 'exclude')
                    assert record['loss_class'] in ('none', 'outside_dryland', 'incomparable')
                    assert (record['action'] == 'map') == (record['loss_class'] == 'none')
                    assert bool(record['target_bin']) == (record['action'] == 'map')
                    assert record['reason'] and record['evidence']
                current, records = raw, []
                for loss in ('outside_dryland', 'incomparable'):
                    labels = [label for label, record in mapping.items() if record['loss_class'] == loss]
                    if labels:
                        current, record = apply(ExcludeTaxa(op='exclude_taxa', taxa=labels,
                            reason=f'Draft {scheme}: {loss}; individual reasons in crosswalk CSV'), current, kind)
                        records.append(record)
                current, record = apply(MapTaxa(op='map_taxa', mapping={label: r['target_bin'] for label, r in mapping.items()
                                                       if r['action'] == 'map'}, reason=f'Draft {scheme} crosswalk'), current, kind)
                records.append(record)
                target_sets.append(set(current['columns']))
                derivations[f'{scheme}/{name}'] = records
                destination = out / 'data' / f'{scheme}-{name}.tsv'
                write_table(destination, current)
                for sample, values, after in zip(raw['samples'], raw['values'], current['values'], strict=True):
                    values = {label: number(value) for label, value in zip(raw['columns'], values, strict=True)}
                    outside = sum((values[label] for label, r in mapping.items() if r['loss_class'] == 'outside_dryland'), Fraction())
                    incomparable = sum((values[label] for label, r in mapping.items() if r['loss_class'] == 'incomparable'), Fraction())
                    retained = sum((values[label] for label, r in mapping.items() if r['action'] == 'map'), Fraction())
                    total = sum(values.values(), Fraction())
                    assert total == outside + incomparable + retained
                    assert retained == sum(map(number, after), Fraction())
                    dryland = total - outside
                    ratio = retained / dryland if dryland else None
                    weights.append(dict(scheme=scheme, source_table=name, sample_id=sample, source_units=units,
                        source_scope='previously_dryland' if name == 'repaired_query' else 'filtered_land_plant_archive',
                        source_weight=text(total), outside_dryland_weight=text(outside), dryland_weight=text(dryland),
                        incomparable_weight=text(incomparable), retained_weight=text(retained),
                        source_weight_exact=str(total), dryland_weight_exact=str(dryland), retained_weight_exact=str(retained),
                        retained_fraction='' if ratio is None else text(ratio),
                        retained_fraction_exact='' if ratio is None else str(ratio),
                        proposed_floor='0.8', meets_proposed_floor=ratio is not None and ratio >= FLOOR,
                        empty_retained=retained == 0))
                validations[f'{scheme}/{name}'] = validate_mapped(destination, current, kind, out, f'{scheme}/{name}')
            assert all(group == target_sets[0] for group in target_sets), (scheme, target_sets)
        indexed = {(r['scheme'], r['sample_id']): r for r in weights if r['source_table'] != 'repaired_query'}
        for row in seeds:
            if row['primary_taxonomic_eligible'] == 'true':
                assert indexed['primary', row['sample_id']]['retained_weight_exact'] == indexed['coarse', row['sample_id']]['retained_weight_exact']
        for sample in raw_fossil['samples']:
            assert indexed['primary', sample]['retained_weight_exact'] == indexed['coarse', sample]['retained_weight_exact']
        ledger = [dict(row) for row in seeds]
        representatives = {}
        for scheme in schemes:
            candidates = []
            for row in ledger:
                accounting = indexed[scheme, row['sample_id']]
                reasons = []
                if row['metadata_modern_eligible'] != 'true': reasons.append('metadata_ineligible')
                if row[f'{scheme}_taxonomic_eligible'] != 'true': reasons.append('dataset_resolution_ineligible')
                if accounting['empty_retained']: reasons.append('empty_retained')
                if not accounting['meets_proposed_floor']: reasons.append('below_proposed_retained_weight_floor')
                row[f'{scheme}_retained_fraction'] = accounting['retained_fraction']
                row[f'{scheme}_candidate_provisional'] = not reasons
                row[f'{scheme}_candidate_reason'] = ';'.join(reasons) if reasons else 'qualifies_under_proposed_0.80_rule'
                row[f'{scheme}_calibration_provisional'] = False
                if not reasons: candidates.append(row)
            by_unit = defaultdict(list)
            for row in candidates: by_unit[row['collectionunitid']].append(row)
            chosen = [min(group, key=lambda r: int(r['representative_preference'])) for group in by_unit.values()]
            for row in chosen: row[f'{scheme}_calibration_provisional'] = True
            representatives[scheme] = {'candidate_ids': [r['sample_id'] for r in candidates],
                'calibration_ids': [r['sample_id'] for r in chosen],
                'units_without_qualifying_candidate': sorted(set(r['collectionunitid'] for r in ledger) - set(by_unit)),
                'fallback_representatives': [r['sample_id'] for r in chosen if int(r['representative_preference']) > 1]}
        positions = {r['sample_id']: r['depth'] for r in metadata['fossil']}
        fossils = []
        for sample in raw_fossil['samples']:
            row = {'sample_id': sample, 'archive_depth_cm': positions[sample]}
            for scheme in schemes:
                account = indexed[scheme, sample]
                row[f'{scheme}_retained_fraction'] = account['retained_fraction']
                row[f'{scheme}_provisional_status'] = ('empty_retained_row' if account['empty_retained'] else
                    'ready' if account['meets_proposed_floor'] else 'taxonomy_limited')
            fossils.append(row)
        assert len(fossils) == 72 and not guarded_calls
        (out / 'coverage.csv').write_bytes(csv_bytes(weights))
        (out / 'sample-ledger.csv').write_bytes(csv_bytes(ledger))
        (out / 'fossil-ledger.csv').write_bytes(csv_bytes(fossils))
        write_json(out / 'derivation-records.json', derivations)
        write_json(out / 'intake-provenance.json', provenance)
        inputs = [{'file': name, 'sha256': sha(HERE / name)} for name in
                  ('prepare.py', 'metadata-seed.csv', 'crosswalk-primary.csv', 'crosswalk-coarse.csv')]
        artifacts = [path for path in (out / 'data').glob('*.tsv')]
        artifacts += [out / name for name in ('coverage.csv', 'sample-ledger.csv', 'fossil-ledger.csv', 'derivation-records.json')]
        receipt = dict(status='draft_for_review', proposal_commit='a351379', primer={k: primer[k] for k in ('version', 'sha256')},
            proposed_retained_weight_floor='0.80; not frozen', guard_probe_passed=True, forbidden_calls_after_probe=0,
            source_tables={name: {'rows': len(raw['samples']), 'columns': len(raw['columns']), 'units': units,
                                 'sha256': sha(out / 'data' / f'{name}.tsv')} for name, (raw, _, units) in extracted.items()},
            source_column_accounting='Every input bin accounted exactly once per scheme; no zero-fill',
            exact_weight_partition_check=True, exact_api_merge_total_check=True,
            same_dryland_bins_across_schemes=True,
            retained_weight_preserved_by_coarsening_for_primary_eligible_rows=True,
            representatives=representatives, validations=validations, input_files=inputs,
            fossil_status_counts={scheme: dict(Counter(r[f'{scheme}_provisional_status'] for r in fossils)) for scheme in schemes},
            artifacts=[{'file': str(path.relative_to(out)), 'sha256': sha(path)} for path in sorted(artifacts)])
        write_json(out / 'preflight-check.json', receipt)
        print(json.dumps({'status': receipt['status'], 'candidates': {k: len(v['candidate_ids']) for k, v in representatives.items()},
                          'calibration_representatives': {k: len(v['calibration_ids']) for k, v in representatives.items()},
                          'fossil_status_counts': receipt['fossil_status_counts'], 'distance_calls': len(guarded_calls)}, indent=2))


if __name__ == '__main__':
    main()
