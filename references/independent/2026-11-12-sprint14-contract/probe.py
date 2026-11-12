"""Artificial contract probes only: CONISS has no toolkit operation yet. No core data are read."""

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np

HERE = Path(__file__).resolve().parent


def coordinates(rows, transform):
    proportions = [[value / math.fsum(row) for value in row] for row in rows]
    return np.sqrt(proportions).tolist() if transform == "hellinger" else proportions


def ss(rows, exact=False):
    n = len(rows)
    if exact:
        values = [[Fraction(value) for value in row] for row in rows]
        mean = [sum(column) / n for column in zip(*values)]
        return sum((value - centre) ** 2 for row in values for value, centre in zip(row, mean))
    mean = [math.fsum(column) / n for column in zip(*rows)]
    return math.fsum((value - centre) * (value - centre) for row in rows for value, centre in zip(row, mean))


def hierarchy(rows, update):
    clusters = [{"indices": [i], "centroid": row} for i, row in enumerate(rows)]
    merges, costs = [], []
    while len(clusters) > 1:
        candidates = []
        for left, right in zip(clusters, clusters[1:]):
            a, b = len(left["indices"]), len(right["indices"])
            candidates.append(a * b / (a + b) * math.fsum((x-y)*(x-y) for x, y in zip(left["centroid"], right["centroid"])))
        chosen = min(range(len(candidates)), key=candidates.__getitem__)
        left, right = clusters[chosen:chosen+2]
        a, b = len(left["indices"]), len(right["indices"])
        if update == "weighted":
            centroid = [(a*x+b*y)/(a+b) for x, y in zip(left["centroid"], right["centroid"])]
        else:
            centroid = [x+b/(a+b)*(y-x) for x, y in zip(left["centroid"], right["centroid"])]
        clusters[chosen:chosen+2] = [{"indices": left["indices"]+right["indices"], "centroid": centroid}]
        costs.append(candidates[chosen])
        direct = math.fsum(ss([rows[i] for i in cluster["indices"]]) for cluster in clusters)
        merges.append({"cost": costs[-1], "cumulative": math.fsum(costs), "direct_partition_ss": direct})
    total = math.fsum(costs)
    m = len(costs)
    comparisons = [{"rank": r, "gain": costs[m-r], "expected": total/m*math.fsum(1/j for j in range(r,m+1))}
                   for r in range(1,m+1)]
    passing = 0
    for comparison in comparisons:
        if comparison["gain"] <= comparison["expected"]:
            break
        passing += 1
    exact_total = ss(rows, exact=True)
    return {"update": update, "coordinates": rows, "merges": merges, "selected_zones": 1+passing,
            "total_dispersion": total, "direct_total_ss": ss(rows), "exact_float_coordinate_ss": float(exact_total),
            "exact_total_positive": exact_total > 0,
            "identity_tolerance": 1e-12*max(total, float.fromhex('0x1.0p-1022'))}


def main():
    cases = []
    for transform in ("relative_abundance", "hellinger"):
        result = hierarchy(coordinates([[1,9]]*4, transform), "weighted")
        assert result["total_dispersion"] > 0 and result["selected_zones"] == 2
        assert result["exact_float_coordinate_ss"] == result["direct_total_ss"] == 0
        cases.append({"id": "identical_counts_"+transform, "transform": transform, "input": [[1,9]]*4, **result})
        raw = [[1,1], [1,1+1e-15], [1,1+2e-15]]
        for update in ("weighted", "difference"):
            result = hierarchy(coordinates(raw, transform), update)
            assert any(abs(step["cumulative"]-step["direct_partition_ss"]) > result["identity_tolerance"]
                       for step in result["merges"])
            cases.append({"id": "nearconstant_"+transform+"_"+update, "transform": transform, "input": raw, **result})
    raw = [[1,1e-200],[1,2e-200],[1,3e-200]]
    result = hierarchy(coordinates(raw, "relative_abundance"), "weighted")
    assert result["total_dispersion"] == 0 and result["exact_total_positive"]
    cases.append({"id":"underflow_relative_abundance", "transform":"relative_abundance", "input":raw, **result})
    receipt = {"reviewed_commit":"cb4b0f5", "scope":"Artificial numerical contract checks; no toolkit implementation or Lake Selina results",
               "python":platform.python_version(), "numpy":np.__version__, "probe_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "cases":cases}
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps([{"id":case["id"], "total":case["total_dispersion"], "direct":case["direct_total_ss"],
                       "selected_zones":case["selected_zones"]} for case in cases],indent=2))


if __name__ == "__main__":
    main()
