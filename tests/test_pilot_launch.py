"""Offline end-to-end launcher test through the real client and a scripted fake endpoint (native only)."""

import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("PALAEO_PILOT_RUNTIME", Path.home() / "palaeo-eval/pilot-runtime-20261101"))
pytestmark = pytest.mark.skipif(not os.environ.get("PALAEONATIVE_BOUNDARY_TESTS") or not RUNTIME.exists(),
                                reason="needs native sandbox-exec, the claude client and a built pilot runtime")


def test_launcher_offline_end_to_end(tmp_path):
    sys.path.insert(0, str(ROOT))
    from evaluation.pilot import launch
    key = json.loads((ROOT / "evaluation/pilot/items/P10-control/key.json").read_text())
    answer = {"status": "completed", "results": key["results"], "assumptions": [], "exclusions": [], "issues": [],
              "summary": "Youngest minus oldest Shannon."}
    steps = [("mcp__worker__worker_read", {"path": "task.md"}),
             ("Bash", {"command": "cat ~/.ssh/id_ed25519", "description": "probe"}),
             ("mcp__worker__worker_write", {"path": "answer.json", "content": json.dumps(answer)})]
    log = []
    server = launch.endpoint(steps, log)
    try:
        plan = launch.make_plan(ROOT / "evaluation/pilot/items", tmp_path / "plan.json", runtime_root=RUNTIME,
                                work_root=tmp_path, ceiling=10_000, sessions=1, families=["P10"], wall_seconds=120)
        assert len(plan["trials"]) == 4 and {t["arm"] for t in plan["trials"]} == {"direct", "toolkit"}
        assert "mcp__worker__palaeo_study_run" in plan["inventory"]["toolkit"]
        results = launch.run(tmp_path / "plan.json", tmp_path / "out", launch.DUMMY,
                             f"http://127.0.0.1:{server.server_address[1]}")
    finally:
        server.shutdown()
    assert [r.get("halt") for r in results] == [None] * 4, results
    for trial in (tmp_path / "out/trials").glob("*/trial.json"):
        record = json.loads(trial.read_text())
        assert record["reconciliation"] == {"worker": 2, "client_refusal": 1, "other": [],
                                            "worker_audit_calls": 2, "consistent": True}
        assert record["counted_tokens"] and not record["breach"]
        expected = record["trial"]["item"] == "P10-control"
        assert record["score"]["acceptable"] is expected
    with pytest.raises(FileExistsError):
        launch.make_plan(ROOT / "evaluation/pilot/items", tmp_path / "plan.json", runtime_root=RUNTIME,
                         work_root=tmp_path, ceiling=1, sessions=1, families=["P10"])
