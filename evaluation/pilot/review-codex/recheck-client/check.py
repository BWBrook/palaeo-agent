"""Audit the proposed monitor against preserved offline client evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PROBE = ROOT / "evaluation/sprint3/codex-client-scripted"


def main():
    cases = {}
    hashes = {}
    for arm in ("direct", "toolkit"):
        base = PROBE / arm
        files = [base / p for p in ("stdout.jsonl", "scripted-results.json", "worker-audit/calls.jsonl", "request-tools.json")]
        for p in files:
            hashes[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
        events = [json.loads(line) for line in files[0].read_text().splitlines() if line]
        started = [e["item"] for e in events if e["type"] == "item.started"]
        replies = json.loads(files[1].read_text())
        audit = [json.loads(line) for line in files[2].read_text().splitlines() if line]
        helpers = [e for e in started if e.get("server") == "codex"]
        hidden = {k: v for k, v in replies.items() if v.startswith("unsupported")}
        assert {e["tool"] for e in helpers} == {"list_mcp_resources", "list_mcp_resource_templates"}
        assert len(hidden) == 6
        assert not any(e.get("tool") in {"apply_patch", "shell", "exec_command", "spawn_agent"} for e in started)
        cases[arm] = {"tool_start_events": len(started), "scripted_tool_replies": len(replies),
            "worker_audit_rows": len(audit), "legitimate_events_literal_rule_would_kill": helpers,
            "refused_hidden_calls_without_tool_start_events": hidden,
            "extra_worker_bootstrap_rows": sum(r["request"]["tool"] == "supervisor_load_tool_definitions" for r in audit)}
    source = ROOT / "evaluation/execution/worker.py"
    hashes[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
    assert "start_new_session=True" in source.read_text()
    receipt = {"baseline": "a3ca5706a3cc5b72a26c854366d4c887cfdd9b82",
        "evidence_kind": "Static replay of previously captured offline client records; no new client launches.",
        "source_sha256": hashes, "cases": cases,
        "cleanup_code_observation": "Worker.run_python starts its child in a separate session. Killing only the supervisor process group does not target that child group. No crash-liveness experiment rerun here.",
        "inference_calls": 0}
    receipt["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({arm: {k: v for k, v in case.items() if isinstance(v, int)} for arm, case in cases.items()}))


if __name__ == "__main__":
    main()
