"""Freeze explicit permutation schedules without importing the tested package."""

import csv
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from math import factorial
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
PLAN = Path(__file__).with_name("cases.json")


def exact_indices(groups):
    labels = list(dict.fromkeys(groups))
    slots = {label: [i for i, group in enumerate(groups) if group == label] for label in labels}
    def allocations(remaining, position, chosen):
        if position == len(labels) - 1:
            yield {**chosen, labels[position]: remaining}
            return
        label = labels[position]
        for selected in combinations(remaining, len(slots[label])):
            leftover = tuple(i for i in remaining if i not in selected)
            yield from allocations(leftover, position + 1, {**chosen, label: selected})
    for allocation in allocations(tuple(range(len(groups))), 0, {}):
        indices = [None] * len(groups)
        for label in labels:
            for slot, original in zip(slots[label], allocation[label], strict=True):
                indices[slot] = original
        yield indices


def main():
    plan = json.loads(PLAN.read_text())
    for case in plan["cases"]:
        sample_ids = [row.split()[0] for row in (ROOT / case["input"]).read_text().splitlines()[1:]]
        with (ROOT / case["metadata"]).open(newline="") as stream:
            metadata = {row["sample_id"]: row["group"] for row in csv.DictReader(stream)}
        assert set(sample_ids) == set(metadata)
        groups = [metadata[sample] for sample in sample_ids]
        sizes = [groups.count(label) for label in dict.fromkeys(groups)]
        space = factorial(len(groups))
        for size in sizes:
            space //= factorial(size)
        exact = space <= 10000 and space - 1 <= case["permutations"]
        if exact:
            indices = list(exact_indices(groups))
            assert len(indices) == space
            assert indices.count(list(range(len(groups)))) == 1
        else:
            rng = np.random.Generator(np.random.PCG64(case["seed"]))
            indices = [rng.permutation(len(groups)).tolist() for _ in range(case["permutations"])]
        record = {"case_id": case["id"], "mode": "exact" if exact else "monte_carlo",
                  "requested": case["permutations"], "draws": len(indices), "space_size": space,
                  "seed": case["seed"], "bit_generator": "PCG64", "numpy_version": np.__version__,
                  "index_base": 0, "index_semantics": "distance_matrix_reordering_fixed_groups",
                  "sample_ids": sample_ids, "groups": groups, "indices": indices,
                  "input_sha256": hashlib.sha256((ROOT / case["input"]).read_bytes()).hexdigest(),
                  "metadata_sha256": hashlib.sha256((ROOT / case["metadata"]).read_bytes()).hexdigest()}
        (ROOT / case["schedule"]).write_text(json.dumps(record, indent=2) + "\n")
    source = ROOT / "references/r/permanova/tiny4.dat"
    counts = [int(row.split()[1]) for row in source.read_text().splitlines()[1:]]
    ratios = [[Fraction(abs(a - b), a + b) for b in counts] for a in counts]
    with localcontext() as context:
        context.prec = 80
        decimals = [[str(Decimal(value.numerator) / Decimal(value.denominator)) for value in row] for row in ratios]
    control = {"kind": "exact_rational_braycurtis_decimal_control", "count_strings": [str(value) for value in counts],
               "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "formula": "abs(integer_a-integer_b)/(integer_a+integer_b), exact Python Fraction then 80-digit Decimal",
               "rational_distances": [[str(value) for value in row] for row in ratios], "decimal_distances": decimals}
    source.with_name("tiny4-exact-distances.json").write_text(json.dumps(control, indent=2) + "\n")


if __name__ == "__main__":
    main()
