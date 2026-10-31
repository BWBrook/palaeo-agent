import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "references/blind/2026-10-31"
COMMITTED_MANIFEST = "1e249c530fe5b7e5ef18ed3049cbe9c2919c7e29dda5cba47ec703e122731807"


@pytest.fixture(scope="module")
def blind_results(tmp_path_factory):
    manifest = (ARCHIVE / "MANIFEST.sha256").read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == COMMITTED_MANIFEST
    entries = manifest.decode().splitlines()
    assert len(entries) == 48
    for entry in entries:
        digest, name = entry.split("  ", 1)
        assert hashlib.sha256((ARCHIVE / name).read_bytes()).hexdigest() == digest, name
    directory = tmp_path_factory.mktemp("blind-validation")
    output = directory / "results.json"
    completed = subprocess.run(
        [sys.executable, "-I", str(ARCHIVE / "runner.py"), str(ARCHIVE / "fixtures"), str(output)],
        env={**os.environ, "TMPDIR": str(directory)}, text=True, capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(output.read_text())
    assert Path(report["palaeo_agent_file"]).resolve() == ROOT / "src/palaeo_agent/__init__.py"
    fixtures = json.loads((ARCHIVE / "fixtures/fixtures.json").read_text())["fixtures"]
    assert [item["id"] for item in report["results"]] == [item["id"] for item in fixtures]
    assert len(fixtures) == 61
    assert [item["id"] for item in fixtures if item["class"] == "judgment"] == ["R09b"]
    return report["results"]


def test_all_sixty_objective_blind_fixtures(blind_results):
    objective = [item for item in blind_results if item["class"] != "judgment"]
    assert len(objective) == 60
    assert [item for item in objective if item["outcome"] != "correct"] == []
    refusal = next(item for item in objective if item["id"] == "C04")
    assert refusal["refusal"]["code"] == "nonidentifiable_axes"


def test_correlation_judgment_remains_an_explicit_disagreement(blind_results):
    item = next(item for item in blind_results if item["id"] == "R09b")
    assert item["status"] == "result"
    assert item["outcome"] == "wrong"
    failed = [check for check in item["checks"] if not check["ok"]]
    assert len(failed) == 1
    assert failed[0]["path"] == "warning_codes_include"
    assert failed[0]["expected"] == "near_zero_correlation"
