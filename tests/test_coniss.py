"""CONISS: independent rounding and exact-oracle checks, the rioja 1.0-7 reference, retention, refusals, bundles."""

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct

import pytest

from palaeo_agent import AnalysisError, inspect_run, reproduce, run
from palaeo_agent import coniss as module
from palaeo_agent.coniss import _hierarchy, broken_stick, coordinates, integer_rows, nearest_double, retention
from palaeo_agent.methods import table_files
from bundle_helpers import rehash

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "references/r/coniss-reference.json").read_text())
CASES = json.loads((ROOT / "references/r/coniss/cases.json").read_text())
LARGEST = 0x7FEFFFFFFFFFFFFF


# Independent rounding reference: bisection over binary64 encodings, then exact midpoint rounding.

def from_bits(bits):
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def reference_round(q, root=False):
    """Nearest binary64 to q (or sqrt q), ties to even; shares no code with the toolkit helper."""
    below = (lambda x: Fraction(x) ** 2 <= q) if root else (lambda x: Fraction(x) <= q)
    low, high = 0, LARGEST
    while high - low > 1:
        middle = (low + high) // 2
        if below(from_bits(middle)):
            low = middle
        else:
            high = middle
    if below(from_bits(high)):
        low = high
    if low == LARGEST:
        return from_bits(low)
    midpoint = (Fraction(from_bits(low)) + Fraction(from_bits(low + 1))) / 2
    target = midpoint ** 2 if root else midpoint
    if q < target or (q == target and low % 2 == 0):
        return from_bits(low)
    return from_bits(low + 1)


def helper(q, root=False):
    return nearest_double(q.numerator, q.denominator, root=root)


ULP1 = Fraction(1, 2**52)
ROUNDING_CASES = [
    Fraction(1, 10**600),                     # float seed underflows to zero; root 1e-300 is normal
    Fraction(10**-323) / (3 + Fraction(10**-323)),  # seed subnormal; root normal
    Fraction(1) + ULP1 / 2,                    # tie between 1 (even) and 1 + ulp (odd): stays 1
    Fraction(1) + 3 * ULP1 / 2,                # tie between 1 + ulp (odd) and 1 + 2 ulp (even): rounds up
    Fraction(1, 2**1022),                      # smallest normal
    Fraction(1, 2**1022) - Fraction(1, 2**1080),  # just below: rounds up to the smallest normal
    Fraction(1, 2**1022) - Fraction(1, 2**1074),  # largest subnormal, exactly
    Fraction(3, 2**1075),                      # subnormal tie: 2^-1074 (odd) vs 2^-1073 (even)
    Fraction(1, 2**1075),                      # tie between 0 and 2^-1074: zero is even
    Fraction(1, 3), Fraction(2, 3), Fraction(7, 10), Fraction(1),
]


@pytest.mark.parametrize("q", ROUNDING_CASES, ids=range(len(ROUNDING_CASES)))
@pytest.mark.parametrize("root", [False, True])
def test_rounding_helper_matches_independent_bisection(q, root):
    assert helper(q, root) == reference_round(q, root)


@pytest.mark.parametrize("low_bits", [0x3FF0000000000000, 0x3FF0000000000001, 0x0000000000000001, 0x0010000000000000])
def test_root_ties_round_half_even(low_bits):
    low, high = from_bits(low_bits), from_bits(low_bits + 1)
    q = ((Fraction(low) + Fraction(high)) / 2) ** 2
    expected = low if low_bits % 2 == 0 else high
    assert helper(q, root=True) == expected == reference_round(q, root=True)


def test_rounding_helper_handles_underflowing_seeds_with_bounded_work():
    assert float(Fraction(1, 10**600)) == 0.0
    assert helper(Fraction(1, 10**600), root=True) == 1e-300
    q = Fraction(10**-323) / (3 + Fraction(10**-323))
    assert helper(q, root=True) == 1.8148749191817537e-162 != math.sqrt(float(q))


# Independent exact oracle: Fraction centroids, every eligible cost recomputed from members, direct partition SS.

def oracle(rows):
    exact = [[Fraction(v) for v in row] for row in rows]
    p = len(exact[0])

    def ss(members):
        centroid = [sum(exact[i][k] for i in members) / len(members) for k in range(p)]
        return sum((exact[i][k] - centroid[k]) ** 2 for i in members for k in range(p))

    groups, records = [[i] for i in range(len(rows))], []
    while len(groups) > 1:
        gains = [ss(a + b) - ss(a) - ss(b) for a, b in zip(groups, groups[1:])]
        j = min(range(len(gains)), key=lambda k: (gains[k], k))
        runner = min(gains[:j] + gains[j + 1:], default=None)
        left, right = groups[j], groups[j + 1]
        groups[j:j + 2] = [left + right]
        records.append({"boundary": left[-1] + 1, "left": (left[0], left[-1], len(left)),
                        "right": (right[0], right[-1], len(right)), "cost": gains[j], "runner_up": runner,
                        "cumulative": sum(ss(g) for g in groups)})
    m = len(records)
    stick = []
    for r in range(1, m + 1):
        gain = records[m - r]["cost"]
        expected = records[-1]["cumulative"] / m * sum(Fraction(1, j) for j in range(r, m + 1))
        stick.append({"rank": r, "zones": r + 1, "gain": gain, "expected": expected, "exceeds": gain > expected})
    return records, stick


def checked_coordinates(values, transform):
    ids, taxa = [f"s{i}" for i in range(len(values))], [f"t{j}" for j in range(len(values[0]))]
    rows = coordinates(values, transform, ids, taxa)
    for row, raw in zip(rows, values):
        total = sum(Fraction(v) for v in raw)
        assert row == [reference_round(Fraction(v) / total, transform == "hellinger") for v in raw]
    return rows


def assert_oracle_agrees(rows):
    merges, _ = _hierarchy(*integer_rows(rows))
    records, stick = oracle(rows)
    assert merges == records
    assert broken_stick(merges) == stick
    return merges, stick


def table_rows(name):
    lines = (ROOT / "references/r/coniss" / name).read_text().splitlines()
    return [[int(v) for v in line.split("\t")[1:]] for line in lines[1:]]


@pytest.mark.parametrize("rows, cost", [([[0.0], [2.0]], [Fraction(2)]), ([[0.0], [1.0], [2.0]], None)])
def test_internal_hierarchy_cases(rows, cost):
    merges, _ = assert_oracle_agrees(rows)
    if cost:
        assert [m["cost"] for m in merges] == cost
    else:
        assert merges[0]["boundary"] == 1 and merges[0]["cost"] == merges[0]["runner_up"] == Fraction(1, 2)


@pytest.mark.parametrize("values, transform", [
    ([[1, 9]] * 4, "relative_abundance"), ([[1, 9]] * 4, "hellinger"),
    ([[1, 1], [1, 1 + 1e-15], [1, 1 + 2e-15]], "relative_abundance"),
    ([[1, 1], [1, 1 + 1e-15], [1, 1 + 2e-15]], "hellinger"),
    ([[1e300, 1e-300], [1e300, 1e300], [1e-300, 1e300]], "hellinger"),
    ([[3, 1e-323], [1, 1], [2, 1]], "hellinger"),
    ([[1, 0], [0, 1], [1, 0]], "relative_abundance"),
    ([[5, 0, 1], [5, 0, 1], [0, 4, 2], [0, 4, 2], [3, 3, 0]], "hellinger"),
])
def test_exact_oracle_on_public_tables(values, transform):
    merges, stick = assert_oracle_agrees(checked_coordinates(values, transform))
    if values[0] == [1, 9]:
        assert all(m["cost"] == 0 for m in merges) and retention(stick)["selected_zones"] == 1
    if values[0] == [1, 0]:
        assert [m["cost"] for m in merges] == [1, Fraction(1, 3)] and merges[0]["boundary"] == 1
        assert retention(stick) == {"rule": "broken_stick_consecutive_prefix", "selected_zones": 1,
                                    "stopped_at_rank": 1, "later_exceedances": [2]}
    if values[0] == [5, 0, 1]:
        assert [m["cost"] for m in merges[:2]] == [0, 0]


@pytest.mark.parametrize("transform", ["relative_abundance", "hellinger"])
def test_ward_identity_on_two_block_table(transform):
    assert_oracle_agrees(checked_coordinates(table_rows("two-block-30x8.dat"), transform))


def test_reported_values_are_nearest_doubles_of_oracle(tmp_path):
    values = table_rows("two-block-30x8.dat")
    records, stick = oracle(checked_coordinates(values, "hellinger"))
    result = run(spec(write(tmp_path, values), transform="hellinger"), tmp_path / "runs")
    saved = json.loads((Path(result["run_dir"]) / "results.json").read_text())
    assert [m["cost"] for m in saved["merges"]] == [reference_round(r["cost"]) for r in records]
    assert [m["cumulative"] for m in saved["merges"]] == [reference_round(r["cumulative"]) for r in records]
    assert [b["expected"] for b in saved["broken_stick"]] == [reference_round(s["expected"]) for s in stick]


# rioja 1.0-7 reference on ordinary cases.

def test_reference_provenance_is_current():
    assert REFERENCE["packages"]["rioja"] == "1.0.7"
    assert REFERENCE["cases_sha256"] == hashlib.sha256((ROOT / "references/r/coniss/cases.json").read_bytes()).hexdigest()
    assert hashlib.sha256((ROOT / REFERENCE["generator"]).read_bytes()).hexdigest() == (
        "10085765373692bd765fd583c8f8fb1081d41d05899f4e96c8954b2499c2621c")


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda case: case["id"])
def test_matches_rioja(case):
    reference = next(item for item in REFERENCE["cases"] if item["id"] == case["id"])
    values = table_rows(case["input"])
    n = len(values)
    ids, taxa = [f"s{i + 1}" for i in range(n)], [f"t{j + 1}" for j in range(len(values[0]))]
    rows = coordinates(values, case["transform"], ids, taxa)
    assert rows == case["coordinates"]
    record = module.zonation(values, transform=case["transform"], sample_ids=ids, taxon_ids=taxa,
                             positions=[float(i) for i in range(n)])
    flags = [w for w in record["warnings"] if w["code"].startswith("small_margin")]
    assert flags == ([] if case["id"] != "public_tie" else
                     [{"code": "small_margin_merge", "message": flags[0]["message"],
                       "details": {"steps": [{"step": 1, "exact_tie": True}]}}])
    rtol = REFERENCE["rtol"]
    cumulative = {m["boundary"]: m["cumulative"] for m in record["merges"]}
    assert all(math.isclose(cumulative[b], h, rel_tol=rtol) for b, h in enumerate(reference["per_boundary"], start=1))
    for k, partition in enumerate(reference["partitions"], start=1):
        cuts = {b["boundary"] for b in record["boundaries"] if b["split_rank"] <= k - 1}
        labels, label = [], 1
        for i in range(n):
            labels.append(label)
            label += (i + 1) in cuts
        assert labels == partition
    stick, expected = record["broken_stick"], reference["bstick"]
    assert [s["zones"] for s in stick[:-1]] == expected["groups"]
    for s, gain, bs in zip(stick, expected["dispersion"], expected["expected"], strict=False):
        assert math.isclose(s["gain"], gain, rel_tol=rtol) and math.isclose(s["expected"], bs, rel_tol=rtol)
        assert s["exceeds"] == (gain > bs)
    last = stick[-1]
    assert math.isclose(last["gain"], reference["final_rank"]["gain"], rel_tol=rtol)
    assert math.isclose(last["expected"], reference["final_rank"]["expected"], rel_tol=rtol)
    if case["id"].startswith("two_block"):
        costs = [m["cost"] for m in record["merges"]]
        assert any(b < a for a, b in zip(costs, costs[1:])) and record["retention"]["later_exceedances"]


# Retention rule.

def stick_records(pairs):
    return [{"rank": r, "zones": r + 1, "gain": Fraction(g), "expected": Fraction(e), "exceeds": Fraction(g) > Fraction(e)}
            for r, (g, e) in enumerate(pairs, start=1)]


@pytest.mark.parametrize("pairs, zones, stopped, later", [
    ([(5, 3), (4, 2), (1, 2), (3, 1)], 3, 3, [4]),
    ([(5, 3), (2, 2), (3, 1)], 2, 2, [3]),
    ([(1, 2), (3, 1), (4, 1)], 1, 1, [2, 3]),
    ([(5, 3), (4, 2), (3, 1)], 4, None, []),
    ([(0, 0), (0, 0)], 1, 1, []),
])
def test_consecutive_prefix_retention(pairs, zones, stopped, later):
    assert retention(stick_records(pairs)) == {"rule": "broken_stick_consecutive_prefix", "selected_zones": zones,
                                               "stopped_at_rank": stopped, "later_exceedances": later}


# Public interface, refusals and bundles.

def write(tmp_path, values, positions=None, abundance=False):
    lines = [".\t" + "\t".join(f"t{j + 1}" for j in range(len(values[0])))]
    lines += [f"s{i + 1}\t" + "\t".join(repr(v) for v in row) for i, row in enumerate(values)]
    (tmp_path / "x.dat").write_text("\n".join(lines) + "\n")
    positions = [str(10 * i) for i in range(len(values))] if positions is None else positions
    (tmp_path / "m.csv").write_text("sample_id,depth\n" + "".join(f"s{i + 1},{p}\n" for i, p in enumerate(positions)))
    return tmp_path


def spec(path, **changes):
    return {"method": "coniss", "input": str(path / "x.dat"), "metadata": str(path / "m.csv"), "position_column": "depth",
            "format": "past", "orientation": "samples_by_taxa", "value_type": "count", "transform": "hellinger",
            "missing": "error", "empty_samples": "error", **changes}


def refusal(request, output):
    with pytest.raises(AnalysisError) as caught:
        run(request, output)
    return caught.value


@pytest.mark.parametrize("positions", [["0", "10", "5"], ["0", "10", "10"], ["0", "nan", "20"], ["0", "inf", "20"],
                                       ["0", "1_0", "20"]])
def test_positions_must_strictly_increase(tmp_path, positions):
    assert refusal(spec(write(tmp_path, [[1, 2], [3, 1], [2, 2]], positions)), tmp_path / "r").code == "order_mismatch"


def test_insufficient_samples(tmp_path):
    assert refusal(spec(write(tmp_path, [[1, 2], [3, 1]])), tmp_path / "r").code == "insufficient_samples"


def test_resource_limit_before_computing(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "zonation", lambda *a, **k: pytest.fail("computed"))
    error = refusal(spec(write(tmp_path, [[1, 1]] * 2001)), tmp_path / "r")
    assert error.code == "resource_limit"


@pytest.mark.parametrize("values, transform", [
    ([[3, 1e-323], [1, 1], [2, 1]], "relative_abundance"),               # coordinate below 2^-1022
    ([[1, 1e-200], [1, 2e-200], [1, 3e-200]], "relative_abundance"),     # costs below 2^-1022
])
def test_numerical_range_refusals(tmp_path, values, transform):
    request = spec(write(tmp_path, values), value_type="abundance", transform=transform)
    assert refusal(request, tmp_path / "r").code == "numerical_range"


def test_dropped_level_is_recorded_and_order_checked_on_retained_rows(tmp_path):
    path = write(tmp_path, [[1, 2], [0, 0], [3, 1], [2, 2]], ["0", "99", "10", "20"])
    assert refusal(spec(path), tmp_path / "r").code == "empty_samples"
    result = json.loads((Path(run(spec(path, empty_samples="drop"), tmp_path / "r")["run_dir"]) / "results.json").read_text())
    assert result["excluded"] == [{"sample_id": "s2", "reason": "empty_sample"}]
    assert result["positions"] == [0.0, 10.0, 20.0]
    assert [(b["left_id"], b["right_id"]) for b in result["boundaries"]] == [("s1", "s3"), ("s3", "s4")]


def test_bundle_inspects_and_reproduces_exactly(tmp_path):
    outcome = run(spec(write(tmp_path, table_rows("two-block-30x8.dat"))), tmp_path / "runs")
    assert inspect_run(outcome["run_dir"])["status"] == "verified"
    reproduced = reproduce(outcome["run_dir"], tmp_path / "again")
    assert reproduced["status"] == "reproduced" and reproduced["tolerance"] == {"rtol": 0.0, "atol": 0.0}
    assert outcome["summary"]["selected_zones"] >= 2


def _bump_cost(result):
    result["merges"][4]["cost"] = math.nextafter(result["merges"][4]["cost"], math.inf)


def _drop_margin_warning(result):
    result["warnings"] = [w for w in result["warnings"] if w["code"] != "small_margin_merge"]


@pytest.mark.parametrize("update", [
    _bump_cost,
    lambda r: r["boundaries"][0].update(split_rank=r["boundaries"][0]["split_rank"] + 1),
    lambda r: r["retention"].update(selected_zones=r["retention"]["selected_zones"] + 1),
    _drop_margin_warning,
], ids=["cost_ulp", "split_rank", "selected_zones", "margin_warning"])
def test_rehashed_tampering_with_refreshed_tables_fails(tmp_path, update):
    rows = table_rows("two-block-30x8.dat") + [[5, 5, 5, 5, 5, 5, 5, 5]] * 3
    run_dir = Path(run(spec(write(tmp_path, rows)), tmp_path / "runs")["run_dir"])
    result = json.loads((run_dir / "results.json").read_text())
    assert any(w["code"] == "small_margin_merge" for w in result["warnings"])
    update(result)
    (run_dir / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    rehash(run_dir, "results.json")
    for name, data in table_files(result).items():
        (run_dir / name).write_bytes(data)
        rehash(run_dir, name)
    with pytest.raises(AnalysisError) as caught:
        inspect_run(run_dir)
    assert caught.value.code == "invalid_bundle"
