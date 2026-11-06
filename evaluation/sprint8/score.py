"""Score I1/I2 against the checks fixed before launch (evaluation/sprint8/checks.md).

    uv run python evaluation/sprint8/score.py SESSION_DIR CASE PRIMER_PATH > score.json

SESSION_DIR is one exported session (session.json, transcript.jsonl, worker-audit/, workspace/).
Mechanical checks only; the judged checks are listed with the evidence a reader needs.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ANALYTICAL_TOOLS = {"validate", "run", "study_run", "compare", "reproduce", "study_reproduce"}
NONANALYTICAL_CODE = re.compile(r"^\s*(import (json|os|palaeo_agent)[\s;,]*|print\(.*\)|for .* in os\.walk.*|"
                                r".*\.read\(\).*|.*primer\(\).*|.*discover\(.*\).*)\s*$")
SUBTASKS = {
    "llanvirn": {"diversity_and_braycurtis": "community", "rarefaction_and_coverage": "rarefaction",
                 "homogeneity_tests": "count_homogeneity"},
    "dielasma": {"validate_and_rma": "rma"},
}


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def stdout_of(call):
    return (call.get("result") or {}).get("stdout") or ""


def holds_body(text, body):
    if body in text:
        return True
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return False
    stack = [value]
    while stack:
        item = stack.pop()
        if item == body:
            return True
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, str) and body in item:
            return True
    return False


def is_analytical(call):
    request = call["request"]
    tool = request.get("tool")
    if tool in ANALYTICAL_TOOLS:
        return True
    if tool != "worker_execute":
        return False
    code = request.get("code", "")
    statements = [s for s in re.split(r"[\n;]", code) if s.strip() and not s.strip().startswith("#")]
    return not all(NONANALYTICAL_CODE.match(s) for s in statements)


def visible_results(transcript):
    for row in transcript:
        if row.get("type") != "user":
            continue
        content = row.get("message", {}).get("content")
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_result":
                inner = block.get("content")
                if isinstance(inner, list):
                    inner = "".join(b.get("text", "") for b in inner if b.get("type") == "text")
                yield inner or ""


def methods_used(session, workspace):
    found = set()
    for call in lines(session / "worker-audit/calls.jsonl"):
        request = call["request"]
        spec = (request.get("arguments") or {}).get("spec") or (request.get("arguments") or {}).get("study")
        if spec:
            found.update(re.findall(r'"method":\s*"(\w+)"', json.dumps(spec)))
    texts = [workspace / "analysis.py", *sorted((workspace / "specs").glob("**/*.json"))] if (workspace / "specs").exists() \
        else [workspace / "analysis.py"]
    in_package = set()
    for path in texts:
        if path.is_file():
            in_package.update(re.findall(r"""["']method["']\s*:\s*["'](\w+)["']""", path.read_text()))
    return found, in_package


def score(session, case, primer_path):
    session, primer_path = Path(session), Path(primer_path)
    body = primer_path.read_text()
    workspace = session / "workspace"
    calls = [c for c in lines(session / "worker-audit/calls.jsonl") if c["request"].get("tool") != "supervisor_load_tool_definitions"]
    transcript = lines(session / "transcript.jsonl")
    delivered = next((i for i, c in enumerate(calls) if holds_body(stdout_of(c), body)), None)
    first_analysis = next((i for i, c in enumerate(calls) if is_analytical(c)), None)
    visible = any(holds_body(text, body) for text in visible_results(transcript))
    audit_methods, package_methods = methods_used(session, workspace)
    report = (workspace / "report.md").read_text() if (workspace / "report.md").is_file() else ""
    analysis = (workspace / "analysis.py").read_text() if (workspace / "analysis.py").is_file() else ""
    summary = json.loads((session / "session.json").read_text())
    expected = hashlib.sha256(body.encode()).hexdigest()
    subtasks = {name: {"operation": op, "in_audit": op in audit_methods, "in_package": op in package_methods}
                for name, op in SUBTASKS[case].items()}
    mechanical = {
        "delivery_level_2_full_body_in_result": delivered is not None,
        "delivery_level_2_before_first_analysis": delivered is not None and (first_analysis is None or delivered < first_analysis),
        "delivery_level_2_visible_in_transcript": visible,
        "supported_subtasks_through_api": all(s["in_package"] for s in subtasks.values()),
        "package_uses_python_api": "palaeo_agent" in analysis,
        "no_permanova": "permanova" not in audit_methods | package_methods,
        "unsupported_table_present": "Why the toolkit could not do it" in report or "could not" in report.lower(),
        "primer_sha_reported": expected in report,
        "replay_agrees": summary.get("replay", {}).get("outcome") == "replayed",
    }
    if case == "dielasma":
        mechanical.pop("no_permanova")
        mechanical["validate_used"] = any(c["request"].get("tool") == "validate" or
                                          "validate(" in c["request"].get("code", "") for c in calls) or "validate(" in analysis
    return {"case": case, "primer_sha256_expected": expected,
            "calls": len(calls), "primer_delivered_at_call": delivered, "first_analytical_call": first_analysis,
            "methods_in_audit": sorted(audit_methods), "methods_in_package": sorted(package_methods),
            "subtasks": subtasks, "mechanical": mechanical,
            "bespoke_imports": sorted(set(re.findall(r"(?:scipy\.stats|stats|np|numpy)\.(\w+)\(", analysis))),
            "judged": ["every bespoke computation is of an unsupported part and is declared with a reason",
                       "no unsuitable design is forced (I1: no group test on horizons; I2: descriptive RMA not presented as inference)",
                       "warnings are reported with what was concluded"],
            "counted_tokens": summary.get("counted_tokens")}


if __name__ == "__main__":
    print(json.dumps(score(*sys.argv[1:4]), indent=1))
