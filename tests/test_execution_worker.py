import json
import os
from pathlib import Path
import platform
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.execution.server import ExecutionTransport
from evaluation.execution.worker import BoundaryError, Worker, profile


RUNTIME = Path(sys.prefix)
BASE = Path(sys.base_prefix).resolve()


def worker(tmp_path, **options):
    trial = tmp_path / "trial"
    trial.mkdir()
    return Worker(trial, RUNTIME, sys.executable, tmp_path / "audit", trusted_read_roots=[BASE], **options)


@pytest.fixture(autouse=True)
def darwin_config(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")


def test_profile_is_deny_default_with_no_process_state_or_network_allow(tmp_path):
    text = profile(tmp_path / "trial", RUNTIME, Path(sys.executable), [BASE])
    assert "(deny default)" in text
    assert "(deny process-info* sysctl-read)" in text
    assert "(allow default)" not in text
    assert "(allow network" not in text
    assert "(allow process-fork" not in text
    assert "(allow sysctl-read)" not in text
    assert "kern.procargs" not in text
    assert "Keychains" not in text and "Preferences" not in text
    assert '(subpath "/Users")' not in text


def test_runtime_and_audit_must_be_outside_trial(tmp_path):
    trial = tmp_path / "trial"
    trial.mkdir()
    with pytest.raises(BoundaryError, match="outside"):
        Worker(trial, RUNTIME, sys.executable, trial / "audit", trusted_read_roots=[BASE])
    with pytest.raises(BoundaryError, match="disjoint"):
        Worker(RUNTIME, RUNTIME, sys.executable, tmp_path / "audit", trusted_read_roots=[BASE])


def test_startup_refuses_symlinked_worker_state_without_external_write(tmp_path):
    trial = tmp_path / "trial"
    trial.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (trial / ".worker").symlink_to(outside, target_is_directory=True)
    with pytest.raises(BoundaryError, match="fresh"):
        Worker(trial, RUNTIME, sys.executable, tmp_path / "audit", trusted_read_roots=[BASE])
    assert list(outside.iterdir()) == []
    assert json.loads((tmp_path / "audit/startup.json").read_text())["code"] == "trial_state_not_fresh"


def test_clean_environment_and_invalid_calls_are_audited(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNTHETIC_TOKEN", "do-not-inherit")
    w = worker(tmp_path)
    assert "SYNTHETIC_TOKEN" not in w.environment
    assert all(str(w.trial_root) in w.environment[k] for k in ("HOME", "TMPDIR", "MPLCONFIGDIR"))
    transport = ExecutionTransport(w)
    monkeypatch.setattr(w, "run_python", lambda *args, **kwargs: pytest.fail("Must reject before launching"))
    assert transport.dispatch("worker_execute", {"code": "pass", "outside": True})["status"] == "error"
    assert transport.dispatch("worker_read", {"path": "foo", "offset": True})["status"] == "error"
    records = [json.loads(line) for line in (w.log_dir / "calls.jsonl").read_text().splitlines()]
    assert len(records) == 2
    assert all(r["result"]["status"] == "error" for r in records)


def test_supervisor_never_opens_model_selected_paths(tmp_path, monkeypatch):
    w = worker(tmp_path)
    calls = []
    monkeypatch.setattr(w, "run_python", lambda *args, **kwargs: calls.append((args, kwargs)) or {"status": "ok"})
    target = tmp_path / "not-opened.txt"
    w.write(str(target), "canary")
    w.read(str(target))
    assert not target.exists()
    assert len(calls) == 2
    assert all("path_outside_trial" in call[0][0][1] for call in calls)


NATIVE = pytest.mark.skipif(os.environ.get("PALAEONATIVE_BOUNDARY_TESTS") != "1",
                           reason="Requires opt-in native macOS sandbox-exec outside a nested sandbox")


@NATIVE
def test_native_execution_confinement_and_cleanup(tmp_path):
    w = worker(tmp_path, timeout_seconds=0.3, max_output_bytes=1024)
    forbidden = tmp_path / "secret"
    forbidden.write_text("synthetic")
    result = w.execute(f"open({str(forbidden)!r}).read()")
    assert result["status"] == "error" and "PermissionError" in result["stderr"]
    assert w.execute("print(42)")["stdout"] == "42\n"
    assert w.execute("import os; os.fork()")["status"] == "error"
    output = w.execute("print('x'*10000)")
    assert output["truncated"]["stdout"] is True and len(output["stdout"]) == 1024
    assert w.execute("import time; time.sleep(10)")["status"] == "timed_out"
    assert w.execute("print('fresh')")["stdout"] == "fresh\n"


def test_startup_rejects_hardlink_without_mutating_external_file(tmp_path):
    trial = tmp_path / "trial"
    trial.mkdir()
    outside = tmp_path / "outside-canary"
    outside.write_text("synthetic")
    (trial / "data").hardlink_to(outside)
    with pytest.raises(BoundaryError, match="hardlinks"):
        Worker(trial, RUNTIME, sys.executable, tmp_path / "audit", trusted_read_roots=[BASE])
    assert outside.read_text() == "synthetic"
    assert not (trial / ".worker").exists()


def test_startup_fails_closed_on_unreadable_directory(tmp_path):
    trial = tmp_path / "trial"
    trial.mkdir()
    hidden = trial / "unreadable"
    hidden.mkdir()
    outside = tmp_path / "outside-canary"
    outside.write_text("synthetic")
    (hidden / "data").hardlink_to(outside)
    hidden.chmod(0)
    try:
        with pytest.raises(BoundaryError):
            Worker(trial, RUNTIME, sys.executable, tmp_path / "audit", trusted_read_roots=[BASE])
        assert not (trial / ".worker").exists()
        assert outside.read_text() == "synthetic"
    finally:
        hidden.chmod(0o700)


def test_confined_metadata_forwards_verbatim_and_primer(tmp_path, monkeypatch):
    from evaluation.execution.server import SERVER_METADATA_CODE, SERVER_METADATA_REQUEST, create_server
    w = worker(tmp_path)
    metadata = {"instructions": "installed canonical instructions\nexact bytes", "tools": [
        {"name": "primer", "description": "full primer", "inputSchema": {"type": "object", "properties": {}}}]}
    calls = []
    def load(arguments, *, request):
        calls.append((arguments, request))
        return {"status": "ok", "exit_code": 0, "stdout": json.dumps(metadata), "truncated": {"stdout": False}}
    monkeypatch.setattr(w, "run_python", load)
    transport = ExecutionTransport(w, toolkit=True)
    assert calls == [(["-c", SERVER_METADATA_CODE], SERVER_METADATA_REQUEST)]
    assert transport.instructions == metadata["instructions"]
    assert json.loads((w.log_dir / "server-metadata.json").read_text()) == metadata
    assert create_server(transport).create_initialization_options().instructions == metadata["instructions"]
    document = {"version": "test", "sha256": "digest", "text": "full primer"}
    def palaeo(name, arguments):
        assert (name, arguments) == ("primer", {})
        return {"status": "ok", "exit_code": 0, "stdout": json.dumps(document), "truncated": {"stdout": False}}
    monkeypatch.setattr(w, "palaeo", palaeo)
    assert transport.dispatch("palaeo_primer", {}) == document


@pytest.mark.parametrize("response", [
    {"status": "ok", "exit_code": 0, "stdout": "{}", "truncated": {"stdout": True}},
    {"status": "error", "exit_code": 1, "stdout": "{}", "truncated": {"stdout": False}},
    {"status": "ok", "exit_code": 0, "stdout": '{"tools": [], "instructions": ""}', "truncated": {"stdout": False}},
])
def test_metadata_fails_closed_on_failed_truncated_or_empty_instructions(tmp_path, monkeypatch, response):
    w = worker(tmp_path)
    monkeypatch.setattr(w, "run_python", lambda *a, **k: response)
    with pytest.raises(ValueError):
        ExecutionTransport(w, toolkit=True)


def test_python_delivery_never_imports_package_for_instructions(tmp_path, monkeypatch):
    w = worker(tmp_path)
    monkeypatch.setattr(w, "run_python", lambda *a, **k: pytest.fail("Python-only startup must not import toolkit"))
    transport = ExecutionTransport(w, toolkit=False)
    assert transport.instructions is None
    assert [t["name"] for t in transport.tools] == ["worker_execute", "worker_read", "worker_write"]


def test_primer_truncation_is_an_error(tmp_path, monkeypatch):
    w = worker(tmp_path)
    metadata = {"instructions": "installed", "tools": [
        {"name": "primer", "inputSchema": {"type": "object", "properties": {}}}]}
    monkeypatch.setattr(w, "run_python", lambda *a, **k: {
        "status": "ok", "exit_code": 0, "stdout": json.dumps(metadata), "truncated": {"stdout": False}})
    transport = ExecutionTransport(w, toolkit=True)
    monkeypatch.setattr(w, "palaeo", lambda *a, **k: {"truncated": {"stdout": True}})
    assert transport.dispatch("palaeo_primer", {})["code"] == "output_limit"
