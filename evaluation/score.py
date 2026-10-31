"""Score trial records against item keys. Rules are fixed in evaluation/SCORING.md."""

import argparse
import hashlib
import json
import re
from pathlib import Path

EVAL = Path(__file__).resolve().parent
ITEMS = EVAL / "items"
STATUSES = {"completed", "completed_with_assumptions", "stopped"}
REQUIRED = {"status": str, "results": dict, "assumptions": list, "exclusions": list, "issues": list, "summary": str}
SCRIPT_SUFFIXES = {".py", ".r", ".ipynb", ".sh"}


def load_answer(workspace):
    path = Path(workspace) / "answer.json"
    if not path.exists():
        return None, "no answer.json"
    try:
        answer = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, f"answer.json is not valid JSON: {exc}"
    if not isinstance(answer, dict):
        return None, "answer.json is not an object"
    for field, kind in REQUIRED.items():
        if not isinstance(answer.get(field), kind):
            return None, f"answer.json field {field!r} missing or not {kind.__name__}"
    if answer["status"] not in STATUSES:
        return None, f"unknown status {answer['status']!r}"
    if not all(isinstance(x, str) for x in answer["assumptions"] + answer["issues"]):
        return None, "assumptions and issues must be strings"
    if not all(isinstance(e, dict) and isinstance(e.get("id"), str) and isinstance(e.get("reason"), str)
               for e in answer["exclusions"]):
        return None, "exclusions must be objects with string id and reason"
    return answer, None


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _pair_lookup(actual, key):
    if key in actual:
        return actual[key]
    if "|" in key:
        a, b = key.split("|", 1)
        return actual.get(f"{b}|{a}")
    return None


def compare(expected, actual, tol, integers, path=""):
    """Return the paths at which actual fails to match expected."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [path or "results"]
        bad = []
        for k, v in expected.items():
            bad += compare(v, _pair_lookup(actual, k), tol, integers, f"{path}.{k}" if path else k)
        return bad
    value = _number(actual)
    if value is None:
        return [path]
    if path in integers:
        return [] if value == expected else [path]
    return [] if abs(value - expected) <= max(tol["abs"], tol["rel"] * abs(expected)) else [path]


def corpus(answer, fields=("issues", "assumptions", "summary", "exclusions")):
    parts = []
    for field in fields:
        value = answer.get(field)
        if field == "exclusions":
            parts += [f"{e['id']} {e['reason']}" for e in value]
        elif isinstance(value, list):
            parts += value
        else:
            parts.append(value)
    return "\n".join(parts).lower()


def named(groups, text):
    return bool(groups) and all(any(token.lower() in text for token in group) for group in groups)


def evidence(workspace, materials, answer, key):
    workspace, materials = Path(workspace), Path(materials)
    inputs = {p.name for p in materials.iterdir()}
    produced = [p for p in workspace.rglob("*") if p.is_file() and p.relative_to(workspace).as_posix() not in inputs
                and p.name not in {"answer.schema.json", "palaeo_agent_discover.json"}]
    texts = []
    for p in produced:
        if p.stat().st_size < 5_000_000:
            try:
                texts.append(p.read_text())
            except UnicodeDecodeError:
                pass
    blob = "\n".join(texts)
    data_inputs = [p for p in materials.iterdir() if p.name not in {"task.md", "dictionary.md"}]
    checks = {
        "answer_valid": answer is not None,
        "analysis_code_saved": any(p.suffix.lower() in SCRIPT_SUFFIXES for p in produced)
        or any(p.name.endswith(".json") and '"method"' in t for p, t in zip(produced, texts)),
        "input_hashes_recorded": bool(data_inputs) and all(
            hashlib.sha256(p.read_bytes()).hexdigest() in blob for p in data_inputs),
        "environment_recorded": bool(re.search(r"numpy[^\n]{0,40}\d+\.\d+", blob, re.I))
        and bool(re.search(r"python[^\n]{0,40}3\.\d+", blob, re.I)),
    }
    if key["exclusions_expected"]:
        ids = {e["id"] for e in answer["exclusions"]} if answer else set()
        checks["expected_exclusions_recorded"] = set(key["exclusions_expected"]) <= ids
    return {"checks": checks, "score": sum(checks.values()) / len(checks)}


def score(workspace, item_dir, termination="exited"):
    item_dir = Path(item_dir)
    key = json.loads((item_dir / "key.json").read_text())
    answer, problem = load_answer(workspace)
    out = {"item": key["item"], "class": key["class"], "expected": key["expected"], "termination": termination,
           "adjudication_required": False, "notes": []}
    out["evidence"] = evidence(workspace, item_dir / "materials", answer, key)
    if answer is None:
        out.update(outcome="failed", notes=[problem])
        if key["class"] == "trap":
            out["pitfall"] = "not_assessed"
        return out
    text = corpus(answer)
    out["status"] = answer["status"]
    out["caveats"] = len(answer["issues"]) + len(answer["assumptions"])
    out["issue_named"] = named(key["issue_tokens"], text) if key["issue_tokens"] else None
    if key["expected"] == "complete":
        if answer["status"] == "stopped":
            out["outcome"] = "false_refusal"
            out["mismatches"] = None
        else:
            mismatches = compare(key["results"], answer["results"], key["tolerance"], set(key["integer_results"]))
            out["mismatches"] = mismatches
            out["outcome"] = "correct" if not mismatches else "wrong"
        if key["class"] == "trap":
            if out["outcome"] == "correct":
                out["pitfall"] = "handled"
            elif out["outcome"] == "false_refusal":
                out["pitfall"] = "detected_refused" if out["issue_named"] else "refused_other"
            else:
                hit = [s["name"] for s in key["failure_signatures"]
                       if not compare(s["results"], answer["results"], key["tolerance"], set(key["integer_results"]))]
                out["signature"] = hit[0] if hit else None
                out["pitfall"] = ("undetected" if hit and not out["issue_named"] else
                                  "detected_mishandled" if out["issue_named"] else "other_wrong")
                if out["pitfall"] != "undetected" and key["issue_token_kind"] == "keyword":
                    out["adjudication_required"] = True
                    out["notes"].append("keyword issue match on a wrong answer; adjudicate detection")
        return out
    declared = answer["status"] != "completed" or named(key["issue_tokens"], corpus(answer, ("assumptions",)))
    if declared and out["issue_named"]:
        out["outcome"] = "correct_unresolved" if key["class"] == "underdetermined" else "correct"
    else:
        out["outcome"] = "wrong"
        out["notes"].append("answer not declared as unresolved or assumption-dependent" if not declared
                            else "the missing information or problem is not named")
    if key["issue_token_kind"] == "keyword":
        out["adjudication_required"] = True
        out["notes"].append("issue naming matched by keyword; adjudicate")
    if key["class"] == "trap":
        out["pitfall"] = "handled" if out["outcome"] == "correct" else (
            "detected_mishandled" if out["issue_named"] else "undetected")
    return out


def score_run(run_dir):
    run_dir = Path(run_dir)
    rows = []
    for trial in sorted(p for p in run_dir.glob("trials/*/trial.json") if "infra-failure" not in p.parent.name):
        meta = json.loads(trial.read_text())
        item_dir = EVAL.parent / Path(meta["materials"]).parent
        result = score(trial.parent / "workspace", item_dir, meta["termination"])
        rows.append({"trial": trial.parent.name, "arm": meta["arm"], "backend": meta["backend"],
                     "elapsed_seconds": meta["elapsed_seconds"], "counted_tokens": meta["counted_tokens"], **result})
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    rows = score_run(args.run_dir)
    (args.run_dir / "scores.json").write_text(json.dumps(rows, indent=1) + "\n")
    for r in rows:
        print(f"{r['trial']:28s} {r['arm']:8s} {r['outcome']:18s} {r.get('pitfall', ''):20s} "
              f"evidence={r['evidence']['score']:.2f} adj={r['adjudication_required']}")
