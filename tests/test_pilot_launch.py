"""Pilot launcher: failure-path checks (portable) and an offline end-to-end run (native only)."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.pilot import launch  # noqa: E402

RUNTIME = Path(os.environ.get("PALAEO_PILOT_RUNTIME", Path.home() / "palaeo-eval/pilot-runtime-v4-20261101"))
native = pytest.mark.skipif(not os.environ.get("PALAEONATIVE_BOUNDARY_TESTS") or not RUNTIME.exists(),
                            reason="needs native sandbox-exec, the claude client and a built pilot runtime")


def test_export_never_follows_links(tmp_path):
    secret = tmp_path / "outside.txt"
    secret.write_text("SYNTHETIC-SECRET")
    trial = tmp_path / "trial"
    (trial / "sub").mkdir(parents=True)
    (trial / "answer.json").write_text("{}")
    (trial / "export-me.txt").symlink_to(secret)
    (trial / "linked-dir").symlink_to(tmp_path, target_is_directory=True)
    os.mkfifo(trial / "sub/pipe")
    refused = launch.export(trial, tmp_path / "out")
    assert {r["path"] for r in refused} == {"export-me.txt", "linked-dir", "sub/pipe"}
    exported = {p.relative_to(tmp_path / "out").as_posix() for p in (tmp_path / "out").rglob("*") if p.is_file()}
    assert exported == {"answer.json"}
    assert "SYNTHETIC-SECRET" not in "".join(p.read_text() for p in (tmp_path / "out").rglob("*") if p.is_file())


@pytest.mark.parametrize("summary", [None, {"complete": False, "counted_tokens": 5}, {"complete": True, "counted_tokens": None}])
def test_ledger_refuses_after_incomplete_trials(tmp_path, summary):
    trial = tmp_path / "trials/T001"
    trial.mkdir(parents=True)
    (trial / "started.json").write_text("{}")
    if summary is not None:
        (trial / "trial.json").write_text(json.dumps(summary))
    with pytest.raises((launch.Halt, TypeError)):
        launch.ledger(tmp_path, "digest")


def test_halt_is_durable_and_plan_bound(tmp_path):
    (tmp_path / "trials").mkdir()
    (tmp_path / "PLAN.sha256").write_text("other\n")
    with pytest.raises(launch.Halt, match="different plan"):
        launch.ledger(tmp_path, "digest")
    (tmp_path / "HALTED.json").write_text("{}")
    with pytest.raises(launch.Halt, match="halted"):
        launch.ledger(tmp_path, "other")


def events(*blocks):
    return [{"type": "assistant", "message": {"content": [b]}} if b["type"] == "tool_use" else
            {"type": "user", "message": {"content": [b]}} for b in blocks]


def audit(tmp_path, *rows):
    (tmp_path / "calls.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return tmp_path


INVENTORY = ["mcp__worker__worker_execute", "mcp__worker__worker_read", "mcp__worker__worker_write"]


OK = {"status": "ok", "exit_code": 0, "stdout": "1\n", "stderr": "", "duration_seconds": 0.01}


def result_for(use_id, value, **extra):
    return {"type": "tool_result", "tool_use_id": use_id, "content": json.dumps(value, separators=(",", ":")), **extra}


def test_reconciliation_matches_identity_not_counts(tmp_path):
    use = {"type": "tool_use", "id": "a", "name": "mcp__worker__worker_execute", "input": {"code": "print(1)"}}
    ok = result_for("a", OK)
    right = {"request": {"tool": "worker_execute", "code": "print(1)"}, "result": OK}
    wrong = {"request": {"tool": "worker_write", "path": "x", "content": "print(1)"}, "result": OK}
    assert launch.reconcile(events(use, ok), audit(tmp_path, right), INVENTORY)["consistent"]
    assert not launch.reconcile(events(use, ok), audit(tmp_path, wrong), INVENTORY)["consistent"]
    assert not launch.reconcile(events(use), audit(tmp_path, right), INVENTORY)["consistent"]
    hidden = {"type": "tool_use", "id": "b", "name": "Bash", "input": {"command": "x"}}
    refusal = {"type": "tool_result", "tool_use_id": "b", "is_error": True,
               "content": "<tool_use_error>Error: No such tool available: Bash</tool_use_error>"}
    out = launch.reconcile(events(use, ok, hidden, refusal), audit(tmp_path, right), INVENTORY)
    assert out["consistent"] and out["client_refusal"] == 1
    executed = dict(refusal, is_error=False, content="ran")
    assert not launch.reconcile(events(hidden, executed), audit(tmp_path), INVENTORY)["consistent"]


def test_reconciliation_compares_full_arguments_and_returned_values(tmp_path):
    write = {"type": "tool_use", "id": "w", "name": "mcp__worker__worker_write",
             "input": {"path": "answer.json", "content": "EXPECTED"}}
    audited = {"request": {"tool": "worker_write", "path": "answer.json", "content": "DIFFERENT"}, "result": OK}
    assert not launch.reconcile(events(write, result_for("w", OK)), audit(tmp_path, audited), INVENTORY)["consistent"]
    read = {"type": "tool_use", "id": "r", "name": "mcp__worker__worker_read", "input": {"path": "x", "offset": 20, "limit": 10}}
    default_read = {"request": {"tool": "worker_read", "path": "x", "offset": 0, "limit": 32768}, "result": OK}
    assert not launch.reconcile(events(read, result_for("r", OK)), audit(tmp_path, default_read), INVENTORY)["consistent"]
    plain = dict(read, input={"path": "x"})
    assert launch.reconcile(events(plain, result_for("r", OK)), audit(tmp_path, default_read), INVENTORY)["consistent"]
    fabricated = result_for("r", dict(OK, stdout="FABRICATED\n"))
    assert not launch.reconcile(events(plain, fabricated), audit(tmp_path, default_read), INVENTORY)["consistent"]
    flipped = result_for("r", OK, is_error=True)
    assert not launch.reconcile(events(plain, flipped), audit(tmp_path, default_read), INVENTORY)["consistent"]
    orphan = result_for("unknown", OK)
    assert not launch.reconcile(events(orphan), audit(tmp_path), INVENTORY)["consistent"]
    duplicate = launch.reconcile(events(plain, result_for("r", OK), result_for("r", OK)), audit(tmp_path, default_read),
                                 INVENTORY)
    assert not duplicate["consistent"]


def test_reconciliation_applies_the_toolkit_adapter(tmp_path):
    value = {"status": "ok", "methods": ["rma"]}
    raw = {"status": "ok", "exit_code": 0, "stdout": json.dumps(value) + "\n", "stderr": "", "truncated": {"stdout": False}}
    use = {"type": "tool_use", "id": "p", "name": "mcp__worker__palaeo_discover", "input": {}}
    row = {"request": {"tool": "discover", "arguments": {}}, "result": raw}
    inventory = INVENTORY + ["mcp__worker__palaeo_discover"]
    assert launch.reconcile(events(use, result_for("p", value)), audit(tmp_path, row), inventory)["consistent"]
    assert not launch.reconcile(events(use, result_for("p", raw)), audit(tmp_path, row), inventory)["consistent"]
    failed = dict(raw, stdout="not json", status="error", exit_code=1)
    expected = {"status": "error", "code": "worker_failed", "execution": failed}
    out = launch.reconcile(events(use, result_for("p", expected, is_error=True)), audit(tmp_path, dict(row, result=failed)),
                           inventory)
    assert out["consistent"]


def synthetic_runtime(base):
    for arm in ("direct", "toolkit"):
        site = base / arm / "lib/python3.12/site-packages/numpy"
        site.mkdir(parents=True)
        (site / "core.py").write_text("x = 1\n")
        (base / arm / "pyvenv.cfg").write_text("home = x\n")
    (base / "runtime.json").write_text("{}")
    return base


def test_fingerprints_cover_installed_dependency_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(launch, "client_path", lambda: Path(sys.executable))
    runtime = synthetic_runtime(tmp_path / "runtime")
    before = launch.fingerprints(runtime, ROOT / "evaluation/pilot/items")
    (runtime / "direct/lib/python3.12/site-packages/numpy/core.py").write_text("x = 2\n")
    after = launch.fingerprints(runtime, ROOT / "evaluation/pilot/items")
    assert before["runtime_tree"] != after["runtime_tree"]
    (runtime / "toolkit/lib/python3.12/site-packages/numpy/extra.py").symlink_to("/etc/hosts")
    assert launch.fingerprints(runtime, ROOT / "evaluation/pilot/items")["runtime_tree"] != after["runtime_tree"]


def test_staged_materials_equal_the_manifest(tmp_path):
    materials = tmp_path / "items/X/materials"
    materials.mkdir(parents=True)
    (materials / "task.md").write_text("task")
    (tmp_path / "items/MANIFEST.json").write_text(json.dumps({"X/materials/task.md": launch.sha(materials / "task.md")}))
    staged = launch.verify_materials(tmp_path / "items", "X")
    assert [p.name for p in staged] == ["task.md"]
    (materials / "extra-reference.csv").write_text("new")
    with pytest.raises(launch.Halt, match="extra"):
        launch.verify_materials(tmp_path / "items", "X")
    (materials / "extra-reference.csv").unlink()
    (materials / "link.csv").symlink_to(materials / "task.md")
    with pytest.raises(launch.Halt, match="link"):
        launch.verify_materials(tmp_path / "items", "X")


def test_terminate_kills_separate_session_workers(tmp_path):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    (tmp_path / "pids.jsonl").write_text(json.dumps({"pgid": child.pid}) + "\n")
    launch.terminate(None, tmp_path)
    assert child.wait(timeout=5) == -9


def test_usage_must_be_complete():
    assert not launch.complete_usage({"input_tokens": 1, "output_tokens": 1})
    assert launch.complete_usage({k: 0 for k in launch.USAGE_FIELDS})


@native
@pytest.mark.parametrize("replay_failure", [False, True])
def test_launcher_offline_end_to_end(tmp_path, monkeypatch, replay_failure):
    if replay_failure:
        from evaluation.pilot import replay
        def fail_replay(*args):
            raise ValueError("synthetic replay-instrument failure")
        monkeypatch.setattr(replay, "replay", fail_replay)
    key = json.loads((ROOT / "evaluation/pilot/items/P10-control/key.json").read_text())
    answer = {"status": "completed", "results": key["results"], "assumptions": [], "exclusions": [], "issues": [],
              "summary": "Youngest minus oldest Shannon."}
    steps = [("mcp__worker__worker_read", {"path": "task.md"}),
             ("Bash", {"command": "cat ~/.ssh/id_ed25519", "description": "probe"}),
             ("mcp__worker__worker_execute", {"code": "import os; os.symlink('/etc/hosts', 'leak.txt')"}),
             ("mcp__worker__worker_write", {"path": "answer.json", "content": json.dumps(answer)}),
             ("mcp__worker__palaeo_discover", {})]
    log = []
    server = launch.endpoint(steps, log)
    config, capture = tmp_path / "config", tmp_path / "capture"
    config.mkdir()
    capture.mkdir()
    try:
        plan = launch.make_plan(ROOT / "evaluation/pilot/items", tmp_path / "plan.json", runtime_root=RUNTIME,
                                work_root=tmp_path, config_dir=config, capture_config_dir=capture, ceiling=10_000,
                                sessions=1, families=["P10"], wall_seconds=120)
        assert len(plan["trials"]) == 4 and "mcp__worker__palaeo_study_run" in plan["inventory"]["toolkit"]
        results = launch.run(tmp_path / "plan.json", tmp_path / "out", launch.DUMMY,
                             f"http://127.0.0.1:{server.server_address[1]}")
    finally:
        server.shutdown()
    if replay_failure:
        assert len(results) == 1 and "replay_infrastructure" in results[0]["halt"]
        records = list((tmp_path / "out/trials").glob("*/trial.json"))
        assert len(records) == 1
        failed = json.loads(records[0].read_text())
        assert not failed["complete"] and failed["replay"]["outcome"] == "infrastructure"
        assert failed["counted_tokens"] > 0 and launch.complete_usage(failed["usage"])
        assert (tmp_path / "out/HALTED.json").exists()
        return
    assert [r.get("halt") for r in results] == [None] * 4, results
    for trial in (tmp_path / "out/trials").glob("*/trial.json"):
        record = json.loads(trial.read_text())
        toolkit = record["trial"]["arm"] == "toolkit"
        assert record["complete"] and record["reconciliation"]["worker"] == 3 + toolkit
        assert record["reconciliation"]["client_refusal"] == 2 - toolkit
        assert [r["path"] for r in record["refused_exports"]] == ["leak.txt"]
        assert record["score"]["acceptable"] is (record["trial"]["item"] == "P10-control")
        assert (trial.parent / "inventory-capture.json").exists()
    rerun = launch.run(tmp_path / "plan.json", tmp_path / "out", launch.DUMMY, "http://127.0.0.1:9")
    assert rerun == []


def test_configuration_memory_halts(tmp_path):
    memory = tmp_path / "projects/x/memory"
    memory.mkdir(parents=True)
    launch.verify_config_dir(tmp_path)
    (memory / "MEMORY.md").write_text("instructions")
    with pytest.raises(launch.Halt):
        launch.verify_config_dir(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("x")
    with pytest.raises(launch.Halt):
        launch.verify_config_dir(tmp_path)


def test_organisation_managed_files(tmp_path):
    (tmp_path / "remote-settings.json").write_text("{}")
    (tmp_path / "remote-settings.json.signature-iat.json").write_text("{}")
    (tmp_path / "policy-limits.json").write_text(json.dumps({"restrictions": {"allow_product_feedback": {"allowed": False}}}))
    assert launch.verify_config_dir(tmp_path)["policy_limits"]["restrictions"]
    (tmp_path / "remote-settings.json").write_text(json.dumps({"env": {"X": "1"}}))
    with pytest.raises(launch.Halt, match="managed settings"):
        launch.verify_config_dir(tmp_path)
