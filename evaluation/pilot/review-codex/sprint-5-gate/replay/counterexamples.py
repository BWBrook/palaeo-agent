import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
from evaluation.pilot import replay

RUNTIME = Path.home() / "palaeo-eval/pilot-runtime-v4-20261101"
COUNTS = "sample\ta\tb\tc\nS1\t5\t3\t2\nS2\t1\t4\t6\nS3\t2\t2\t2\n"
BASE = {"status": "completed", "results": {"sum": 27}, "assumptions": [], "exclusions": [], "issues": [], "summary": "Calculated total"}
CALCULATE = '''import json
rows = [l.split("\\t") for l in open("counts.tsv").read().splitlines()[1:]]
total = sum(int(x) for r in rows for x in r[1:])
answer = {"status": "completed", "results": {"sum": total}, "assumptions": [], "exclusions": [], "issues": [], "summary": "Calculated total"}
'''
SAVE = 'json.dump(answer, open("answer.json", "w"))\n'


def make_items(root):
    items = root / "items"
    materials = items / "X/materials"
    materials.mkdir(parents=True)
    (materials / "counts.tsv").write_text(COUNTS)
    (items / "X/key.json").write_text(json.dumps({"tolerance": {"abs": 1e-4, "rel": 1e-4}, "replay_perturbation": {
        "file": "counts.tsv", "kind": "add_row", "match": "S2", "value": 5}}))
    files = list((items / "X").rglob("*"))
    (items / "MANIFEST.json").write_text(json.dumps({str(p.relative_to(items)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                    for p in files if p.is_file()}))
    return items


def record(root, name, script, answer):
    rec = root / name
    (rec / "workspace").mkdir(parents=True)
    (rec / "trial.json").write_text(json.dumps({"trial": {"trial_id": name, "item": "X", "arm": "direct"}}))
    (rec / "workspace/analysis.py").write_text(script)
    (rec / "workspace/answer.json").write_text(json.dumps(answer))
    return rec


def main():
    output = {"source_sha256": hashlib.sha256((REPO / "evaluation/pilot/replay.py").read_bytes()).hexdigest(), "cases": {}}
    with tempfile.TemporaryDirectory(prefix="palaeo-s5-replay-audit-") as tmp:
        root = Path(tmp)
        items = make_items(root)
        changed = BASE | {"summary": "These numbers establish the opposite biological conclusion", "exclusions": [{"id": "S1", "reason": "excluded"}]}
        cases = {
            "honest": (CALCULATE + SAVE, BASE),
            "wrong_but_recomputes": (CALCULATE.replace('sum(int(x) for r in rows for x in r[1:])', 'sum(int(x) for r in rows if r[0] != "S2" for x in r[1:])') + SAVE, BASE | {"results": {"sum": 16}}),
            "changed_claims_and_exclusions": (CALCULATE + SAVE, changed),
            "invalid_empty_answer": ('import json\njson.dump({}, open("answer.json", "w"))\n', {}),
            "ignored_arrays": ('import json\njson.dump(' + repr(BASE | {"results": {"x": [99]}}) + ', open("answer.json", "w"))\n', BASE | {"results": {"x": [1, 2]}}),
            "static_keyed_result_with_dynamic_extra": (CALCULATE + 'answer["results"] = {"sum": 27, "unrequested_probe": total}\n' + SAVE, BASE | {"results": {"sum": 27, "unrequested_probe": 27}}),
            "perturbed_script_failure": (CALCULATE + 'if total != 27: raise SystemExit(3)\n' + SAVE, BASE),
        }
        for name, (script, answer) in cases.items():
            output["cases"][name] = replay.replay(record(root, name, script, answer), items, RUNTIME)
        outside = root / "synthetic-external.json"
        outside.write_text(json.dumps(BASE | {"results": {"sum": 918273}}))
        symlink = 'from pathlib import Path\ntry:\n Path(' + repr(str(outside)) + ').read_text()\nexcept PermissionError:\n pass\nelse:\n raise RuntimeError("canary unexpectedly worker-readable")\nPath("answer.json").symlink_to(' + repr(str(outside)) + ')\n'
        output["cases"]["symlink_supervisor_read"] = replay.replay(record(root, "symlink_supervisor_read", symlink, BASE), items, RUNTIME)
        native = replay.execute
        calls = 0
        def second_infrastructure(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                return {"status": "error", "code": "execution_failed", "message": "synthetic worker launch error"}, None
            return native(*args, **kwargs)
        with patch.object(replay, "execute", side_effect=second_infrastructure):
            output["cases"]["perturbed_infrastructure_failure"] = replay.replay(record(root, "perturbed_infrastructure_failure", CALCULATE + SAVE, BASE), items, RUNTIME)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
