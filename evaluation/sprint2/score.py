"""Versioned sprint-2 wrapper; the original scorer is not modified."""

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
VERSION = "sprint2-group-score-v1"
spec = importlib.util.spec_from_file_location("sprint2_original_score", HERE.parent / "score.py")
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
original.ITEMS = HERE / "items"


def score(workspace, item_dir, termination="exited"):
    result = original.score(workspace, item_dir, termination)
    result["scorer_version"] = VERSION
    key = json.loads((Path(item_dir) / "key.json").read_text())
    answer, _ = original.load_answer(workspace)
    if key.get("requires_stopped_empty_results") and answer is not None:
        if answer["status"] != "stopped" or answer["results"]:
            result["outcome"] = "wrong"
            result["pitfall"] = "detected_mishandled" if result["issue_named"] else "undetected"
            matches = [entry["name"] for entry in key["failure_signatures"]
                       if not original.compare(entry["results"], answer["results"], key["tolerance"],
                                               set(key["integer_results"]))]
            result["signature"] = matches[0] if matches else None
            result["notes"].append("unsupported dependent design requires stopped status and empty results")
    return result


def score_run(run_dir):
    rows = []
    for path in sorted((Path(run_dir) / "trials").glob("*/trial.json")):
        meta = json.loads(path.read_text())
        item_dir = REPO / Path(meta["materials"]).parent
        result = score(path.parent / "workspace", item_dir, meta["termination"])
        rows.append({"trial": path.parent.name, "arm": meta["arm"], "backend": meta["backend"],
                     "elapsed_seconds": meta["elapsed_seconds"], "counted_tokens": meta["counted_tokens"], **result})
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    rows = score_run(args.run_dir)
    (args.run_dir / "scores.json").write_text(json.dumps(rows, indent=2) + "\n")
    for row in rows:
        print(row["trial"], row["outcome"], row.get("pitfall", ""))
