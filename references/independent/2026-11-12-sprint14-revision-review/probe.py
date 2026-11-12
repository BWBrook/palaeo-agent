"""Artificial contract review only; no CONISS API exists and no core data are read."""

from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct
import tempfile

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "2026-11-12-sprint14-revision/prototype.py"
SPEC = importlib.util.spec_from_file_location("revision_prototype", SOURCE)
PROTO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTO)


def from_bits(bits):
    return struct.unpack('>d', struct.pack('>Q', bits))[0]


def nearest_root(q):
    """Independent bounded search of binary64 encodings, then exact midpoint rounding."""
    assert 0 <= q <= 1
    if q in (0, 1):
        return float(q), 0
    low, high, steps = 0, 0x3ff0000000000000, 0
    while high-low > 1:
        middle = (low+high)//2
        if Fraction(from_bits(middle))**2 <= q:
            low = middle
        else:
            high = middle
        steps += 1
    midpoint = (Fraction(from_bits(low))+Fraction(from_bits(high)))/2
    chosen = low if q < midpoint**2 or (q == midpoint**2 and low % 2 == 0) else high
    assert steps <= 62
    return from_bits(chosen), steps


def oracle(rows):
    groups = [[i] for i in range(len(rows))]
    exact = [[Fraction(v) for v in row] for row in rows]
    def mean(indices):
        return [sum(exact[i][j] for i in indices)/len(indices) for j in range(len(rows[0]))]
    def ss(indices):
        mu = mean(indices)
        return sum((exact[i][j]-mu[j])**2 for i in indices for j in range(len(mu)))
    records = []
    while len(groups) > 1:
        gains = [ss(a+b)-ss(a)-ss(b) for a,b in zip(groups,groups[1:])]
        selected = min(range(len(gains)),key=gains.__getitem__)
        left, right = groups[selected:selected+2]
        runner = min(gains[:selected]+gains[selected+1:],default=None)
        groups[selected:selected+2] = [left+right]
        records.append({'boundary':left[-1], 'cost':gains[selected], 'runner_up':runner,
                        'cumulative':sum(ss(group) for group in groups)})
    return records


class ReviewGuard(RuntimeError):
    pass


def main():
    original_nextafter = math.nextafter
    calls = 0
    def guarded_nextafter(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls > 128:
            raise ReviewGuard('Review stopped the unbounded neighbour walk')
        return original_nextafter(*args, **kwargs)
    rows = [[1e300,1e-300],[1e300,1e300],[1e-300,1e300]]
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'artificial.dat'
        path.write_text('.\tA\tB\n'+'\n'.join(f's{i}\t{a}\t{b}' for i,(a,b) in enumerate(rows))+'\n')
        method = next(m for m in pa.discover()['methods'] if m['id']=='community')
        assert 'abundance' in str(method['requirements'])
        validation = pa.validate({'method':'community','input':str(path),'format':'past',
            'orientation':'samples_by_taxa','value_type':'abundance','transform':'relative_abundance',
            'distance':'braycurtis','dimensions':1,'missing':'error','empty_samples':'error'})
        assert validation['status']=='valid'
    PROTO.math.nextafter = guarded_nextafter
    try:
        try:
            PROTO.coordinates(rows,'hellinger')
        except ReviewGuard:
            guarded = True
        else:
            raise AssertionError('Expected the specified seed to enter the neighbour walk')
    finally:
        PROTO.math.nextafter = original_nextafter
    zero_seed_calls = calls
    subnormal_cell = 2 * math.ulp(0.0)
    subnormal_q = Fraction(subnormal_cell)/(Fraction(3)+Fraction(subnormal_cell))
    subnormal_root, _ = nearest_root(subnormal_q)
    assert 0 < float(subnormal_q) < PROTO.TINY <= subnormal_root
    calls = 0
    PROTO.math.nextafter = guarded_nextafter
    try:
        try:
            PROTO.rounded_sqrt(subnormal_q)
        except ReviewGuard:
            subnormal_guarded = True
        else:
            raise AssertionError('Expected a distant subnormal seed')
    finally:
        PROTO.math.nextafter = original_nextafter
    coordinates, iteration_counts = [], []
    for row in rows:
        total = sum(Fraction(v) for v in row)
        output = [nearest_root(Fraction(v)/total) for v in row]
        coordinates.append([value for value,_ in output])
        iteration_counts.extend(steps for _,steps in output)
    merges, comparisons, zones = PROTO.hierarchy(coordinates)
    assert merges == oracle(coordinates) and zones == 1
    assert all(value == 0 or value >= PROTO.TINY for row in coordinates for value in row)
    assert all(record['cost']==0 or record['cost']>=PROTO.TINY for record in merges)
    quantities = [value for record in merges for key,value in record.items() if key != 'boundary' and value is not None]
    quantities += [value for _,gain,expected,_ in comparisons for value in (gain,expected)]
    assert all(value == 0 or value >= PROTO.TINY for value in quantities)
    midpoint_cases = 0
    for low in (1,2,0x10000000000000,0x10000000000001,0x3fdfffffffffffff,0x3fe0000000000000):
        midpoint = (Fraction(from_bits(low))+Fraction(from_bits(low+1)))/2
        root, _ = nearest_root(midpoint**2)
        assert root == from_bits(low if low % 2 == 0 else low+1)
        midpoint_cases += 1
    rng = random.Random(3142026)
    matches = 0
    for _ in range(10):
        data = [[rng.randint(1,10) for _ in range(4)] for _ in range(6)]
        for transform in ('relative_abundance','hellinger'):
            x = PROTO.coordinates(data,transform)
            actual, _, _ = PROTO.hierarchy(x)
            assert actual == oracle(x)
            matches += 1
    result = {'reviewed_commit':'d132377', 'prototype_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'Artificial bounded rounding and independent exact partition-SS checks; no core or production API results',
        'source_rows':rows, 'existing_abundance_validation':'valid',
        'prototype_walk_deliberately_aborted':guarded, 'nextafter_calls_at_abort':zero_seed_calls,
        'float_tiny_proportion':float(Fraction(rows[0][1])/sum(map(Fraction,rows[0]))),
        'neighbour_steps_from_zero_to_expected_root':int.from_bytes(struct.pack('>d',coordinates[0][1]),'big'),
        'independent_binary64_coordinates':coordinates, 'maximum_bisection_iterations':max(iteration_counts),
        'independent_midpoint_half_even_cases':midpoint_cases,
        'subnormal_seed_case':{'source_row':[3.0,subnormal_cell], 'float_proportion':float(subnormal_q),
            'seed_sqrt':math.sqrt(float(subnormal_q)), 'nearest_sqrt':subnormal_root,
            'prototype_walk_deliberately_aborted':subnormal_guarded, 'nextafter_calls_at_abort':calls},
        'hierarchy_matches_independent_partition_ss':True, 'selected_zones':zones,
        'costs':[float(record['cost']) for record in merges], 'synthetic_exact_hierarchies_checked':matches}
    (HERE/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
