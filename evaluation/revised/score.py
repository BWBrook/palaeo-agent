"""Prospective sprint-1 scorer with strict answer-contract validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from . import VERSION

STATUSES = {"completed", "completed_with_assumptions", "stopped"}
FIELDS = {"status", "results", "assumptions", "exclusions", "issues", "summary"}
SCRIPT_SUFFIXES = {".py", ".r", ".ipynb", ".sh"}


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _finite(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return True
    if isinstance(value, (int, float)):
        try:
            return math.isfinite(value)
        except (OverflowError, ValueError):
            return False
    if isinstance(value, list):
        return all(_finite(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _finite(item) for key, item in value.items())
    return False


def load_answer(workspace: Path) -> tuple[dict[str, Any] | None, str | None]:
    path = Path(workspace) / "answer.json"
    if not path.exists():
        return None, "no answer.json"
    try:
        answer = json.loads(path.read_text(), parse_constant=_reject_constant)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return None, f"answer.json is not strict finite JSON: {exc}"
    if not isinstance(answer, dict) or set(answer) != FIELDS:
        return None, "answer.json top-level fields are not exactly the answer contract"
    if not isinstance(answer.get("status"), str) or answer["status"] not in STATUSES:
        return None, "unknown status"
    if not isinstance(answer.get("results"), dict) or not isinstance(answer.get("summary"), str) or not _finite(answer):
        return None, "results or answer contains a non-finite or unsupported value"
    if not all(isinstance(answer[field], list) for field in ("assumptions", "exclusions", "issues")):
        return None, "answer lists are malformed"
    if not all(isinstance(item, str) for item in answer["assumptions"] + answer["issues"]):
        return None, "assumptions and issues must be strings"
    if not all(
        isinstance(item, dict)
        and set(item) == {"id", "reason"}
        and isinstance(item["id"], str)
        and isinstance(item["reason"], str)
        for item in answer["exclusions"]
    ):
        return None, "exclusions must contain exactly id and reason"
    if answer["status"] == "stopped" and answer["results"]:
        return None, "stopped answers must have empty results"
    if answer["status"] == "completed_with_assumptions" and not answer["assumptions"]:
        return None, "completed_with_assumptions requires a nonempty assumptions list"
    return answer, None


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return float(value) if math.isfinite(value) else None
        except (OverflowError, ValueError):
            return None
    if isinstance(value, str):
        try:
            result = float(value)
        except ValueError:
            return None
        return result if math.isfinite(result) else None
    return None


def _lookup(actual: Any, key: str) -> Any:
    if not isinstance(actual, dict):
        return None
    if key in actual:
        return actual[key]
    if "|" in key:
        left, right = key.split("|", 1)
        return actual.get(f"{right}|{left}")
    return None


def compare(expected: Any, actual: Any, tolerance: dict[str, float], integers: set[str], path: str = "") -> list[str]:
    if isinstance(expected, dict):
        return [failure for key, value in expected.items() for failure in compare(
            value, _lookup(actual, key), tolerance, integers, f"{path}.{key}" if path else key
        )]
    number = _number(actual)
    if number is None:
        return [path]
    if path in integers:
        return [] if number == expected else [path]
    return [] if abs(number - expected) <= max(tolerance["abs"], tolerance["rel"] * abs(expected)) else [path]


def corpus(answer: dict[str, Any], fields: tuple[str, ...] = ("issues", "assumptions", "summary", "exclusions")) -> str:
    parts: list[str] = []
    for field in fields:
        value = answer[field]
        if field == "exclusions":
            parts.extend(f"{item['id']} {item['reason']}" for item in value)
        elif isinstance(value, list):
            parts.extend(value)
        else:
            parts.append(value)
    return "\n".join(parts).lower()


def named(groups: list[list[str]], text: str) -> bool:
    return bool(groups) and all(any(token.lower() in text for token in group) for group in groups)


def evidence(workspace: Path, materials: Path, answer: dict[str, Any] | None, key: dict[str, Any]) -> dict[str, Any]:
    workspace, materials = Path(workspace), Path(materials)
    input_names = {path.name for path in materials.iterdir()}
    produced = sorted([
        path for path in workspace.rglob("*")
        if path.is_file()
        and path.relative_to(workspace).as_posix() not in input_names
        and path.name not in {"answer.schema.json", "palaeo_agent_discover.json"}
    ])
    readable: list[tuple[Path, str]] = []
    for path in produced:
        if path.stat().st_size >= 5_000_000:
            continue
        try:
            readable.append((path, path.read_text()))
        except UnicodeDecodeError:
            continue
    blob = "\n".join(text for _, text in readable)
    data_inputs = [path for path in materials.iterdir() if path.name not in {"task.md", "dictionary.md"}]
    checks = {
        "answer_valid": answer is not None,
        "analysis_code_saved": any(path.suffix.lower() in SCRIPT_SUFFIXES for path in produced)
        or any(path.suffix.lower() == ".json" and '"method"' in text for path, text in readable),
        "input_hashes_recorded": bool(data_inputs)
        and all(hashlib.sha256(path.read_bytes()).hexdigest() in blob for path in data_inputs),
        "environment_recorded": bool(re.search(r"numpy[^\n]{0,40}\d+\.\d+", blob, re.I))
        and bool(re.search(r"python[^\n]{0,40}3\.\d+", blob, re.I)),
    }
    if key["exclusions_expected"]:
        ids = {item["id"] for item in answer["exclusions"]} if answer else set()
        checks["expected_exclusions_recorded"] = set(key["exclusions_expected"]) <= ids
    return {"checks": checks, "score": sum(checks.values()) / len(checks)}


def score(workspace: Path, item_dir: Path, termination: str = "exited") -> dict[str, Any]:
    item_dir = Path(item_dir)
    key = json.loads((item_dir / "key.json").read_text(), parse_constant=_reject_constant)
    answer, problem = load_answer(Path(workspace))
    output: dict[str, Any] = {
        "version": VERSION,
        "item": key["item"],
        "class": key["class"],
        "expected": key["expected"],
        "termination": termination,
        "adjudication_required": False,
        "provisional": False,
        "notes": [],
    }
    output["evidence"] = evidence(Path(workspace), item_dir / "materials", answer, key)
    if answer is None:
        output.update(outcome="failed", notes=[problem])
        return output
    output["status"] = answer["status"]
    output["caveats"] = len(answer["issues"]) + len(answer["assumptions"])
    output["issue_named"] = named(key["issue_tokens"], corpus(answer)) if key["issue_tokens"] else None
    if key["expected"] == "complete":
        if answer["status"] == "stopped":
            output.update(outcome="false_refusal", mismatches=None)
            if key["class"] == "trap":
                output["pitfall"] = "detected_refused" if output["issue_named"] else "refused_other"
        else:
            mismatches = compare(key["results"], answer["results"], key["tolerance"], set(key["integer_results"]))
            output["mismatches"] = mismatches
            output["outcome"] = "correct" if not mismatches else "wrong"
            if key["class"] == "trap":
                if output["outcome"] == "correct":
                    output["pitfall"] = "handled"
                else:
                    hit = [signature["name"] for signature in key["failure_signatures"]
                           if not compare(signature["results"], answer["results"], key["tolerance"], set(key["integer_results"]))]
                    output["signature"] = hit[0] if hit else None
                    output["pitfall"] = ("undetected" if hit and not output["issue_named"] else
                                          "detected_mishandled" if output["issue_named"] else "other_wrong")
                    if output["pitfall"] != "undetected" and key["issue_token_kind"] == "keyword":
                        output["adjudication_required"] = True
                        output["provisional"] = True
                        output["notes"].append("keyword issue match requires adjudication")
        return output
    # For an unresolved item a stopped answer must be empty, and a numerical
    # answer must make its assumption in assumptions, not only in issues.
    if answer["status"] == "stopped":
        if output["issue_named"]:
            output["outcome"] = "correct_unresolved" if key["class"] == "underdetermined" else "correct"
        else:
            output["outcome"] = "wrong"
        if key["class"] == "trap":
            output["pitfall"] = "handled" if output["outcome"] == "correct" else (
                "detected_mishandled" if output["issue_named"] else "undetected"
            )
        if key["issue_token_kind"] == "keyword":
            output["adjudication_required"] = True
            output["provisional"] = True
            output["notes"].append("keyword issue match requires adjudication")
        return output
    assumption_named = named(key["issue_tokens"], corpus(answer, ("assumptions",)))
    if answer["status"] == "completed_with_assumptions" and assumption_named:
        output["outcome"] = "correct_unresolved" if key["class"] == "underdetermined" else "correct"
        if answer["results"]:
            output["provisional"] = True
            output["adjudication_required"] = True
            output["notes"].append("numerical unresolved answer requires adjudication")
        elif key["issue_token_kind"] == "keyword":
            output["provisional"] = True
            output["adjudication_required"] = True
            output["notes"].append("keyword issue match requires adjudication")
        return output
    output["outcome"] = "wrong"
    output["notes"].append("missing information must be named in assumptions")
    return output


def score_run(run_dir: Path, items: Path) -> list[dict[str, Any]]:
    rows = []
    for trial in sorted(Path(run_dir).glob("trials/*/trial.json")):
        meta = json.loads(trial.read_text())
        item_dir = Path(items) / Path(meta["materials"]).parent.name
        rows.append({
            "trial": trial.parent.name,
            "arm": meta["arm"],
            "backend": meta["backend"],
            "elapsed_seconds": meta["elapsed_seconds"],
            "counted_tokens": meta["counted_tokens"],
            **score(trial.parent / "workspace", item_dir, meta["termination"]),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("items", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = score_run(args.run_dir, args.items)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(rows, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
