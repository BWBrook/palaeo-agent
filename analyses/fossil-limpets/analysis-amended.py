"""Execute the frozen amendment; scientific quantities come from inspected API results."""

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
SOURCE_SHA = "481c968bebeb96716ae03623361aebb2c6d64e1ee636f30e5406d1a3071285fe"
PRIMER_SHA = "f84855fca5b314f8f608b2ead07d12a94555a93dfe4002195fa537cd2ecf372e"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "runs-amended-study")
    args = parser.parse_args()
    primer = pa.primer()
    assert primer["sha256"] == PRIMER_SHA, "Review the current primer before changing this pin"
    assert sha(HERE / "source/STable1_2DLimpets.csv") == SOURCE_SHA
    freeze = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", "analyses/fossil-limpets/AMENDMENT-1.md"],
                                     cwd=HERE.parents[1], text=True).strip()
    assert freeze, "Commit the amendment before execution"
    for name in ("AMENDMENT-1.md", "study-amended.json"):
        committed = subprocess.check_output(["git", "show", f"{freeze}:analyses/fossil-limpets/{name}"], cwd=HERE.parents[1])
        assert committed == (HERE / name).read_bytes(), "Amendment differs from its frozen commit"
    outcome = pa.run_study(HERE / "study-amended.json", args.output)
    assert outcome["status"] == "complete", outcome
    directory = Path(outcome["study_dir"])
    inspected = pa.inspect_study(directory)
    assert inspected["status"] == "verified"
    assert (directory / "derived/shells.dat").read_bytes() == b".\t" + (HERE / "measurements.tsv").read_bytes().split(b"\t", 1)[1]
    manifest = json.loads((directory / "manifest.json").read_bytes())
    records = {name: pa.inspect_run(directory / item["run_dir"]) for name, item in manifest["runs"].items()}
    assert set(records) == {"caliper_log", "automorph_log", "paired_log"}
    results = {name: record["result"] for name, record in records.items()}
    cohorts = [[p["sample_id"] for p in result["pairs"]] for result in results.values()]
    assert cohorts[0] == cohorts[1] == cohorts[2] and len(cohorts[0]) == 136
    original = json.loads((HERE / "results.json").read_text())["fits"]
    for name in ("caliper_log", "automorph_log"):
        for key in ("n", "mean_x", "mean_y", "sd_x", "sd_y", "correlation", "slope", "intercept", "vertical_residual_rmse", "pairs"):
            assert results[name][key] == original[name][key], (name, key)
    paired = copy.deepcopy(results["paired_log"])
    for key in ("slope_a", "slope_b", "difference"):
        del paired["bootstrap"][key]
    paired["bootstrap"]["replicates_artifact"] = "bootstrap-amended.csv"
    write_json(HERE / "results-amended.json", {"primer": {k: primer[k] for k in ("version", "sha256")},
        "fits": {name: results[name] for name in ("caliper_log", "automorph_log")}, "paired_summary": paired,
        "export_scope": "Single fits are complete native results; paired replicate arrays are exported as native CSV"})
    paired_dir = directory / manifest["runs"]["paired_log"]["run_dir"]
    (HERE / "bootstrap-amended.csv").write_bytes((paired_dir / "bootstrap.csv").read_bytes())
    fields = ["analysis_id", "confidence", "magnitude", "low", "high", "null_magnitude", "magnitude_p", "direction_p"]
    with (HERE / "inference-amended.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for name in ("caliper_log", "automorph_log"):
            inf = results[name]["inference"]
            writer.writerow(dict(analysis_id=name, confidence=inf["confidence"], magnitude=inf["magnitude_estimate"],
                low=inf["magnitude_interval"][0], high=inf["magnitude_interval"][1], null_magnitude=inf["null_magnitude"],
                magnitude_p=inf["magnitude_test"]["p_value"], direction_p=inf["direction_test"]["p_value"]))
    write_json(HERE / "provenance-amended.json", {"freeze_commit": freeze, "approval_board_message": 3131,
        "study_dir": str(directory.relative_to(HERE)), "source_sha256": SOURCE_SHA,
        "study_sha256": sha(HERE / "study-amended.json"), "study_manifest_sha256": sha(directory / "manifest.json"),
        "runs": {name: {"run_dir": manifest["runs"][name]["run_dir"], "run_id": record["manifest"]["run_id"],
                        "results_sha256": sha(directory / manifest["runs"][name]["run_dir"] / "results.json"),
                        "environment": record["environment"]} for name, record in records.items()}})
    print(json.dumps({"study": outcome["status"], "single_fits": {name: result["inference"] for name, result in results.items() if name != "paired_log"},
                      "paired_difference": paired["difference"], "bootstrap_summary": paired["bootstrap"], "warnings": paired["warnings"]}, indent=2))


if __name__ == "__main__":
    main()
