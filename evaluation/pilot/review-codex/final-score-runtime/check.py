"""Verify pilot-v3 scoring repairs and installed study-wheel provenance offline."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from evaluation.pilot.score import score


def main():
    bank = ROOT / "evaluation/pilot"
    cases = {}
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        def check(label, item, status="completed", summary="Done.", issues=None, exclusions=None):
            key = json.loads((bank / "items" / item / "key.json").read_text())
            answer = {"status": status, "results": {} if status == "stopped" else key["results"],
                      "assumptions": [], "issues": issues or [], "exclusions": exclusions or [], "summary": summary}
            (work / "answer.json").write_text(json.dumps(answer))
            result = score(work, bank / "items" / item)
            cases[label] = {"answer": answer, "result": result}
            return result

        silent = check("P04_silent_basis", "P04-trap")
        assert silent["outcome"] == "undisclosed" and silent["adjudication_required"]
        stopped = check("P04_valid_stop", "P04-trap", status="stopped",
                        issues=["The small fraction was not picked in 2017; full-community Shannon is unidentified."])
        assert stopped["outcome"] == "correct_unresolved" and stopped["adjudication_required"]
        disclosed = check("P04_valid_common_fraction", "P04-trap",
                          summary="Means for the common T01–T08 fraction only; this is not a full-community comparison.")
        assert disclosed["acceptable"]
        misleading = check("P04_false_full_community_claim", "P04-trap",
                           summary="All fractions were counted in both campaigns; these are full-community Shannon means.")
        assert misleading["acceptable"] and not misleading["adjudication_required"]
        pairs = json.loads((bank / "items/P09-trap/key.json").read_text())["equivalent_exclusions"]
        for label, ids in (("left", [p[0] for p in pairs]), ("right", [p[1] for p in pairs]), ("average", [])):
            result = check("P09_" + label, "P09-trap", summary="One measurement per individual; paired valves averaged when retained.",
                           exclusions=[{"id": i, "reason": "Retain the other valve of this individual."} for i in ids])
            assert result["acceptable"] and result["evidence"]["checks"]["one_member_per_pair"]
        assert len({cases["P09_" + side]["result"]["evidence"]["score"] for side in ("left", "right", "average")}) == 1
        both = check("P09_both_members_flagged", "P09-trap",
                     exclusions=[{"id": i, "reason": "Excluded."} for i in pairs[0]])
        assert not both["evidence"]["checks"]["one_member_per_pair"]

    runtime = Path.home() / "palaeo-eval/pilot-runtime-20261101"
    manifest = json.loads((runtime / "runtime.json").read_text())
    assert manifest == json.loads((bank / "launch-evidence/runtime.json").read_text())
    wheel = runtime / "wheel" / manifest["wheel"]
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == manifest["wheel_sha256"]
    module_hashes = {}
    with zipfile.ZipFile(wheel) as archive:
        for name in archive.namelist():
            if name.startswith("palaeo_agent/") and name.endswith(".py"):
                content = archive.read(name)
                assert content == (ROOT / "src" / name).read_bytes()
                assert content == (runtime / "toolkit/lib/python3.12/site-packages" / name).read_bytes()
                module_hashes[name] = hashlib.sha256(content).hexdigest()
    materials = []
    for part in ("items", "calibration"):
        for path in sorted((bank / part).glob("*/materials/*")):
            if path.is_file():
                relative = str(path.relative_to(ROOT))
                assert path.read_bytes() == subprocess.check_output(["git", "show", "1d017e9:" + relative])
                materials.append(relative)
        for path in sorted((bank / part).glob("*/key.json")):
            previous = json.loads(subprocess.check_output(["git", "show", "1d017e9:" + str(path.relative_to(ROOT))]))
            current = json.loads(path.read_text())
            assert current["results"] == previous["results"]
            assert current["failure_signatures"] == previous["failure_signatures"]
    receipt = {"reviewed_commit": "aedc1585a239abddea825f813d30c7fdfb91de17",
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "scorer_sha256": hashlib.sha256((bank / "score.py").read_bytes()).hexdigest(),
               "scoring_cases": cases, "wheel_sha256": manifest["wheel_sha256"],
               "installed_module_hashes": module_hashes,
               "unchanged_materials": materials, "all_32_numeric_targets_and_signatures_unchanged": True,
               "inference_calls": 0}
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"scoring_cases": len(cases), "wheel_modules_verified": len(module_hashes),
                      "unchanged_material_files": len(materials), "P04_false_claim_is_unflagged": True}))


if __name__ == "__main__":
    main()
