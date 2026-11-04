import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.authentic.session import CASES, replay, session_prompt  # noqa: E402

RUNTIME = Path(os.environ.get("PALAEO_PILOT_RUNTIME",
                             Path.home() / "palaeo-eval/pilot-runtime-v4-freeze-20261101")) / "direct"
native = pytest.mark.skipif(not RUNTIME.exists() or os.environ.get("PALAEONATIVE_BOUNDARY_TESTS") != "1",
                            reason="requires native sandbox-exec and frozen runtime")

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


@native
def test_honest_package_replays(tmp_path):
    record = package(tmp_path, SCRIPT, {"totals": totals()})
    assert replay(record, CASES, "llanvirn", RUNTIME)["outcome"] == "replayed"


@native
def test_changed_number_is_a_mismatch(tmp_path):
    wrong = totals()
    wrong[0] += 1
    assert replay(package(tmp_path, SCRIPT, {"totals": wrong}), CASES, "llanvirn", RUNTIME)["outcome"] == "mismatch"


@native
def test_failing_and_absent_packages(tmp_path):
    assert replay(package(tmp_path / "a", "raise SystemExit(1)", {"x": 1}), CASES, "llanvirn",
                  RUNTIME)["outcome"] == "failed"
    assert replay(package(tmp_path / "b", SCRIPT, None), CASES, "llanvirn", RUNTIME)["outcome"] == "no_results"


def test_prompt_offers_toolkit_only_in_toolkit_arm():
    assert "palaeo_discover" in session_prompt("dielasma", "toolkit")
    assert "palaeo_" not in session_prompt("dielasma", "direct")
    assert session_prompt("llanvirn", "direct").rstrip().endswith("cannot establish.")


def test_instructed_prompts_are_separate_and_python_prints_full_object():
    mcp = session_prompt("llanvirn", "toolkit", "mcp")
    python = session_prompt("dielasma", "toolkit", "python")
    assert "optional" not in mcp.replace("Figures are optional.", "")
    assert "Using it is optional" not in python
    assert "scientific tools and the worker tools are permitted" in mcp
    assert "primer" not in mcp
    assert "json.dumps(palaeo_agent.primer(), ensure_ascii=False)" in python
    assert 'primer()["text"]' not in python
    assert "Using it is optional" in session_prompt("dielasma", "toolkit")


def test_instructed_plan_pins_modes_and_new_prompt_bytes(tmp_path, monkeypatch):
    from evaluation.authentic import session
    seen = []
    monkeypatch.setattr(session, "fingerprints", lambda *a: {"test": "fingerprint"})
    def capture(runtime, arm, model, config, *, delivery_mode=None):
        seen.append((arm, delivery_mode))
        return ["worker", delivery_mode]
    monkeypatch.setattr(session, "capture_inventory", capture)
    sessions = [{"session_id": "I1", "case": "llanvirn", "arm": "toolkit", "delivery_mode": "mcp"},
                {"session_id": "I2", "case": "dielasma", "arm": "toolkit", "delivery_mode": "python"}]
    plan = session.make_plan(tmp_path / "plan.json", runtime_root=tmp_path / "runtime", work_root=tmp_path,
                             config_dir=tmp_path / "config", capture_config_dir=tmp_path / "capture",
                             ceiling=100, sessions=sessions)
    assert seen == [("toolkit", "mcp"), ("toolkit", "python")]
    assert set(plan["inventory"]) == {"toolkit:mcp", "toolkit:python"}
    assert plan["sessions"] == sessions
    assert all("evaluation/authentic/" + name in plan["session_source"] for name in
               ("instructed-contract.md", "instructed-mcp.md", "instructed-python.md"))
