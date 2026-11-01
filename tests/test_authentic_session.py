import json
from pathlib import Path

import pytest

from evaluation.authentic.session import CASES, replay, session_prompt

RUNTIME = Path.home() / "palaeo-eval/pilot-runtime-v4-freeze-20261101/direct"
pytestmark = pytest.mark.skipif(not RUNTIME.exists(), reason="frozen runtime not present")

SCRIPT = """import json
rows = [l.split() for l in open("llanvirn.dat")]
totals = [sum(int(r[i]) for r in rows[1:]) for i in range(1, 11)]
json.dump({"totals": totals}, open("results.json", "w"))
"""


def package(tmp_path, script, results):
    record = tmp_path / "record"
    (record / "workspace").mkdir(parents=True)
    (record / "replay").mkdir()
    (record / "workspace/analysis.py").write_text(script)
    if results is not None:
        (record / "workspace/results.json").write_text(json.dumps(results))
    return record


def totals():
    rows = [l.split() for l in (CASES / "llanvirn/materials/llanvirn.dat").read_text().splitlines()]
    return [sum(int(r[i]) for r in rows[1:]) for i in range(1, 11)]


def test_honest_package_replays(tmp_path):
    record = package(tmp_path, SCRIPT, {"totals": totals()})
    assert replay(record, CASES, "llanvirn", RUNTIME)["outcome"] == "replayed"


def test_changed_number_is_a_mismatch(tmp_path):
    wrong = totals()
    wrong[0] += 1
    assert replay(package(tmp_path, SCRIPT, {"totals": wrong}), CASES, "llanvirn", RUNTIME)["outcome"] == "mismatch"


def test_failing_and_absent_packages(tmp_path):
    assert replay(package(tmp_path / "a", "raise SystemExit(1)", {"x": 1}), CASES, "llanvirn",
                  RUNTIME)["outcome"] == "failed"
    assert replay(package(tmp_path / "b", SCRIPT, None), CASES, "llanvirn", RUNTIME)["outcome"] == "no_results"


def test_prompt_offers_toolkit_only_in_toolkit_arm():
    assert "palaeo_discover" in session_prompt("dielasma", "toolkit")
    assert "palaeo_" not in session_prompt("dielasma", "direct")
    assert session_prompt("llanvirn", "direct").rstrip().endswith("cannot establish.")
