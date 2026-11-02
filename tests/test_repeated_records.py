import json
from pathlib import Path

from palaeo_agent import core
from palaeo_agent.community import analyse_community

ROOT = Path(__file__).resolve().parents[1]
DIELASMA = ROOT / "benchmarks/past/legacy-data/dielasma.dat"


def fit(locality):
    spec = json.loads((ROOT / "benchmarks/past/dielasma-l2-run/spec.json").read_text())
    spec |= {"input": str(DIELASMA), "x": f"{locality}/X1", "y": f"{locality}/X2"}
    return core.calculate(core.RmaSpec.model_validate(spec), DIELASMA.read_bytes())


def codes(result):
    return [w["code"] for w in result["warnings"]]


def test_dielasma_l2_duplicated_block_is_reported_without_changing_the_fit():
    result = fit("L2")
    block = next(w for w in result["warnings"] if w["code"] == "repeated_block")
    assert block["details"] == {"first": [str(i) for i in range(57, 64)], "repeat": [str(i) for i in range(64, 71)]}
    assert result["n"] == 79 and result["slope"] == 0.819167040027981


def test_scattered_coincident_repeats_warn_only_as_repeated_pairs():
    result = fit("L3")
    assert codes(result) == ["repeated_pairs"]
    assert codes(fit("L1")) == []


def test_short_runs_and_overlapping_periodic_runs():
    ids = [str(i) for i in range(8)]
    two = [(1, 1), (2, 2), (3, 5), (1, 1), (2, 2), (4, 4), (5, 9), (6, 1)]
    assert [b for b in core.repeated_records(two, ids)[1]] == []
    constant = [(1, 1)] * 6
    groups, blocks, omitted = core.repeated_records(constant, ids[:6])
    assert omitted == 0
    assert groups == [ids[:6]]
    assert {"first": ids[:3], "repeat": ids[3:6]} in blocks
    assert all(len(b["first"]) == len(b["repeat"]) and b["first"][-1] < b["repeat"][0] for b in blocks)


def test_identical_count_profiles_are_reported():
    result = analyse_community([[3, 1, 0], [0, 2, 5], [3, 1, 0]], sample_ids=["a", "b", "c"],
                               taxon_ids=["x", "y", "z"], transform="none", distance="braycurtis", dimensions=1,
                               empty_samples="error")
    warning = next(w for w in result["warnings"] if w["code"] == "identical_samples")
    assert warning["details"]["groups"] == [["a", "c"]]


def test_block_warning_identifies_consecutive_retained_records_after_dropping_missing():
    result = core.rma_regression([1, 2, None, 3, 1, 2, 3], [2, 4, None, 6, 2, 4, 6],
                                 sample_ids=list("abcdefg"), transform="none", missing="drop_pairs")
    block = next(w for w in result["warnings"] if w["code"] == "repeated_block")
    assert block["details"] == {"first": ["a", "b", "d"], "repeat": ["e", "f", "g"]}
    assert "consecutive retained records" in block["message"]
    assert result["n"] == 6 and result["slope"] == 2


def test_repetitive_input_bounds_block_payload_and_reports_all_omissions():
    ids = [str(i) for i in range(2048)]
    warnings = core.repeated_warnings([(i % 2, i % 2) for i in range(2048)], ids, "pairs")
    assert warnings[0]["details"]["groups"] == [ids[::2], ids[1::2]]
    blocks = [w for w in warnings if w["code"] == "repeated_block"]
    assert len(blocks) == 20
    assert blocks[-1]["details"]["omitted_blocks"] == 1001
    assert blocks[-1]["details"]["reported_blocks"] == 20
    assert "1001 additional block pairs omitted" in blocks[-1]["message"]
    for block, offset in zip(blocks, range(4, 44, 2), strict=True):
        assert block["details"]["first"] == ids[:offset]
        assert block["details"]["repeat"] == ids[offset:2 * offset]
    assert len(json.dumps(warnings)) < 50_000
