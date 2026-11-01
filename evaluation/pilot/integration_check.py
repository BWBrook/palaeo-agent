"""Integration criteria over exported trials: numerical execution, structured toolkit refusals, bundle reproduction.

For every completed trial it counts successful worker executions and the
toolkit's structured errors (palaeo_* results with status "error" and a code),
and reruns every saved study bundle in the exported workspace with
reproduce_study, outside the trial, into a fresh directory.

    python evaluation/pilot/integration_check.py OUT_DIR [OUT_DIR ...] > receipt.json
"""

import json
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from palaeo_agent import inspect_study  # noqa: E402
from palaeo_agent.study import reproduce_study  # noqa: E402


def tool_events(transcript):
    uses, results = {}, {}
    for line in transcript.read_text().splitlines():
        message = json.loads(line).get("message")
        for block in message.get("content", []) if isinstance(message, dict) and isinstance(message.get("content"), list) else []:
            if block.get("type") == "tool_use":
                uses[block["id"]] = block
            elif block.get("type") == "tool_result":
                results[block["tool_use_id"]] = block
    for use_id, use in uses.items():
        result = results.get(use_id, {})
        try:
            value = json.loads(result.get("content")) if isinstance(result.get("content"), str) else None
        except ValueError:
            value = None
        yield use["name"], value, bool(result.get("is_error"))


def check(record):
    summary = json.loads((record / "trial.json").read_text())
    executions, refusals = 0, []
    for name, value, is_error in tool_events(record / "transcript.jsonl"):
        if name == "mcp__worker__worker_execute" and isinstance(value, dict) and value.get("status") == "ok":
            executions += 1
        if name.startswith("mcp__worker__palaeo_") and isinstance(value, dict) and value.get("status") == "error":
            refusals.append({"tool": name.removeprefix("mcp__worker__"), "code": value.get("code")})
    studies = []
    for manifest in sorted((record / "workspace").rglob("study.json")):
        directory = manifest.parent
        entry = {"study": directory.relative_to(record / "workspace").as_posix()}
        try:
            entry["inspect"] = inspect_study(directory)["status"]
            with tempfile.TemporaryDirectory() as scratch:
                entry["reproduce"] = reproduce_study(directory, Path(scratch) / "rerun")["status"]
        except Exception as exc:  # a failed bundle is a finding, not a crash
            entry["error"] = f"{type(exc).__name__}: {exc}"
        studies.append(entry)
    return {"trial": summary["trial"]["trial_id"], "item": summary["trial"]["item"], "arm": summary["trial"]["arm"],
            "complete": summary.get("complete"), "outcome": summary.get("score", {}).get("outcome"),
            "counted_tokens": summary.get("counted_tokens"), "successful_executions": executions,
            "toolkit_structured_errors": refusals, "studies": studies}


if __name__ == "__main__":
    trials = [check(r) for out in sys.argv[1:] for r in sorted((Path(out) / "trials").glob("*"))
              if (r / "trial.json").exists() and json.loads((r / "trial.json").read_text()).get("complete")]
    print(json.dumps({"trials": trials,
                      "criteria": {"numerical_execution": any(t["successful_executions"] for t in trials),
                                   "structured_refusal": any(t["toolkit_structured_errors"] for t in trials),
                                   "bundle_reproduction": any(s.get("reproduce") for t in trials for s in t["studies"])}},
                     indent=1))
