import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "references/blind/2026-10-31-permanova"
COMMITTED_MANIFEST = "621c3edcbb7791746ea649202a0f82553e6a61c6a0965d039da2f9e49e784950"
ADAPTER = "d07df424cc313d03b4c778bbce3e8153392c772e2f2b91d7401432305b4d027b"


@pytest.fixture(scope="module")
def blind_results(tmp_path_factory):
    manifest = (ARCHIVE / "MANIFEST.sha256").read_bytes()
    assert hashlib.sha256(manifest).hexdigest() == COMMITTED_MANIFEST
    entries = manifest.decode().splitlines()
    assert len(entries) == 56
    for entry in entries:
        digest, name = entry.split("  ", 1)
        assert hashlib.sha256((ARCHIVE / name).read_bytes()).hexdigest() == digest, name
    assert hashlib.sha256((ARCHIVE / "adapter.py").read_bytes()).hexdigest() == ADAPTER
    directory = tmp_path_factory.mktemp("blind-permanova")
    output = directory / "results.json"
    completed = subprocess.run([sys.executable, "-I", str(ARCHIVE / "adapter.py"), str(output)],
                               env={**os.environ, "TMPDIR": str(directory)}, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(output.read_text())
    assert Path(report["palaeo_agent_file"]).resolve() == ROOT / "src/palaeo_agent/__init__.py"
    return report["records"]


def test_all_objective_blind_permanova_fixtures(blind_results):
    objective = [r for r in blind_results if r["class"] == "objective"]
    assert len(objective) == 24
    assert [r["id"] for r in objective if r["outcome"] != "correct"] == []


def test_undefined_permutation_judgment_keeps_infinite_exceedances(blind_results):
    item = next(r for r in blind_results if r["id"] == "P15")
    assert item["class"] == "judgment" and item["outcome"] == "correct"
