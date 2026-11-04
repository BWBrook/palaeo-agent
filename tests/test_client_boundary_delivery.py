"""Deterministic provider-request evidence checks; no model inference."""

import copy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evaluation/sprint3/claude-client-boundary"))
from probe import delivery_checks, delivery_steps


def fixture(mode):
    text = "A complete primer, including the final line.\n"
    expected = {"instructions": "Canonical server instruction text.",
                "primer": {"version": "test", "sha256": hashlib.sha256(text.encode()).hexdigest(), "text": text}}
    primer = expected["primer"]
    analysis = {"status": "valid"}
    if mode == "python":
        primer = {"stdout": json.dumps(primer), "truncated": {"stdout": False},
                  "output_bytes": {"stdout": len(json.dumps(primer).encode())}}
        analysis = {"stdout": json.dumps(analysis)}
    results = [{"tool_use_id": f"toolu_{i:02d}", "content": json.dumps(v)} for i, v in enumerate((primer, analysis))]
    system = [{"type": "text", "text": "prefix " + expected["instructions"] + " suffix"}] if mode == "mcp" else []
    log = [{"system": system, "tool_results": results[:n]} for n in range(3)]
    return expected, log


def test_actual_content_and_full_metadata_required_for_each_delivery_route():
    for mode in ("mcp", "python"):
        expected, log = fixture(mode)
        assert all(delivery_checks(log, expected, mode).values())
        assert delivery_steps(mode)[0][0] == ("mcp__worker__palaeo_primer" if mode == "mcp"
                                             else "mcp__worker__worker_execute")
        broken = copy.deepcopy(log)
        first = json.loads(broken[1]["tool_results"][0]["content"])
        if mode == "python":
            first["stdout"] = json.dumps({k: v for k, v in expected["primer"].items() if k != "text"})
        else:
            first.pop("text")
        broken[1]["tool_results"][0]["content"] = json.dumps(first)
        assert not delivery_checks(broken, expected, mode)["full_primer_before_analysis"]
        assert not delivery_checks(log, expected, mode, max_output_bytes=4)["primer_below_output_limit"]
        assert not delivery_checks([log[0], log[2]], expected, mode)["full_primer_before_analysis"]


def test_instruction_length_cannot_substitute_for_content():
    expected, log = fixture("mcp")
    for row in log:
        row["system"] = [{"type": "text", "text": "X" * len(expected["instructions"])}]
    assert not delivery_checks(log, expected, "mcp")["canonical_instructions_delivered"]
    expected, log = fixture("python")
    log[0]["system"] = expected["instructions"]
    assert not delivery_checks(log, expected, "python")["canonical_instructions_withheld"]


def test_truncated_or_failed_python_output_cannot_pass_delivery():
    expected, log = fixture("python")
    value = json.loads(log[1]["tool_results"][0]["content"])
    value["truncated"]["stdout"] = True
    log[1]["tool_results"][0]["content"] = json.dumps(value)
    log[1]["tool_results"][0]["is_error"] = True
    checks = delivery_checks(log, expected, "python")
    assert not checks["primer_below_output_limit"]
    assert not checks["full_primer_before_analysis"]


@pytest.mark.parametrize("role", ["user", "system"])
def test_client_may_place_exact_server_instructions_in_message_preface(role):
    expected, log = fixture("mcp")
    for row in log:
        row["system"] = []
        row["messages"] = [{"role": role, "content": [
            {"type": "text", "text": "# MCP Server Instructions\n" + expected["instructions"]}]}]
    assert all(delivery_checks(log, expected, "mcp").values())
    for row in log:
        row["messages"] = [{"role": "user", "content": [
            {"type": "tool_result", "content": expected["instructions"]}]}]
    assert not delivery_checks(log, expected, "mcp")["canonical_instructions_delivered"]
