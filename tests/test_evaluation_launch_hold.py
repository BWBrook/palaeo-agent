import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "evaluation/harness"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_trial_and_smoke_fail_before_creating_or_reading_trial_materials(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(HARNESS))
    trial = load("trial", HARNESS / "trial.py")
    monkeypatch.setitem(sys.modules, "trial", trial)
    smoke = load("review_held_smoke", HARNESS / "smoke.py")
    monkeypatch.setattr(trial, "ROOT", tmp_path / "must-not-be-created")
    with pytest.raises(trial.LiveEvaluationBlocked, match="live_evaluation_blocked"):
        trial.run(tmp_path / "missing-materials", "toolkit", "codex", tmp_path / "record")
    with pytest.raises(trial.LiveEvaluationBlocked, match="live_evaluation_blocked"):
        smoke.run(tmp_path / "missing-plan.json")
    assert not list(tmp_path.iterdir())


def test_standalone_launcher_exits_without_creating_work_or_credentials(tmp_path):
    result = subprocess.run([sys.executable, str(HARNESS / "trial.py"),
                             str(tmp_path / "missing"), "direct", "claude", str(tmp_path / "record")],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
    assert "live_evaluation_blocked" in result.stderr
    assert not list(tmp_path.iterdir())
