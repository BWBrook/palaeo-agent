"""Independent regression and adversarial checks of S1-S4; no bank/key access."""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from palaeo_agent import AnalysisError, inspect_study, reproduce_study, run_study
from palaeo_agent.mcp_server import Transport


def main(receipt):
    observations = []
    spec = {"study_version": 1,
            "inputs": {"m": {"kind": "measurements", "path": "data.dat", "orientation": "samples_by_taxa"}},
            "datasets": {"d": {"source": "m"}},
            "analyses": [{"id": "r", "dataset": "d", "spec": {
                "method": "rma", "format": "past", "x": "x", "y": "y", "transform": "none", "missing": "error"}}]}
    with tempfile.TemporaryDirectory(prefix="study-recheck-") as scratch:
        root = Path(scratch)
        materials = root / "materials"
        materials.mkdir()
        (materials / "data.dat").write_text(". x y\na 1 2\nb 2 3\nc 4 7\n")
        template = root / "template"
        run_study(spec, template, base_dir=materials)

        def check(name, call, expected):
            try:
                result = call()
            except AnalysisError as exc:
                result = exc.as_dict()
            passed = expected(result)
            observations.append({"case": name, "passed": passed, "observed": result})
            assert passed, (name, result)

        def clone(name):
            dest = root / name
            shutil.copytree(template, dest)
            return dest

        def alter_manifest(name, change):
            dest = clone(name)
            path = dest / "manifest.json"
            manifest = json.loads(path.read_text())
            change(manifest)
            path.write_text(json.dumps(manifest))
            return dest

        rejected = lambda value: value.get("code") == "invalid_study"
        check("complete_positive_control", lambda: inspect_study(template),
              lambda v: v["status"] == "verified" and v["study_status"] == "complete")
        check("complete_reproduction", lambda: reproduce_study(template, root / "reproduced"),
              lambda v: v["status"] == "reproduced")

        dest = alter_manifest("empty-steps", lambda m: m.update(steps=[], runs={}))
        shutil.rmtree(dest / "runs")
        check("S1_empty_steps_and_deleted_runs", lambda: inspect_study(dest), rejected)
        mutations = {
            "missing_step": lambda m: m["steps"].pop(),
            "reordered_steps": lambda m: m["steps"].reverse(),
            "duplicate_step": lambda m: m["steps"].append(deepcopy(m["steps"][0])),
            "unknown_step": lambda m: m["steps"][0].update(id="dataset:unknown"),
            "missing_run": lambda m: m.update(runs={}),
            "wrong_overall_status": lambda m: m.update(status="partial"),
            "unknown_step_status": lambda m: m["steps"][0].update(status="unknown"),
            "not_run_without_failure": lambda m: m["steps"][1].update(status="not_run"),
            "complete_after_failure": lambda m: m["steps"][0].update(status="failed"),
            "two_failures": lambda m: [s.update(status="failed") for s in m["steps"]],
        }
        for name, mutation in mutations.items():
            dest = alter_manifest(name, mutation)
            check("S1_" + name, lambda: inspect_study(dest), rejected)

        for component in ("runs", "derived", "inputs"):
            session = root / ("link-" + component)
            session.mkdir()
            dest = session / "study"
            shutil.copytree(template, dest)
            outside = root / ("outside-" + component)
            (dest / component).rename(outside)
            (dest / component).symlink_to(outside, target_is_directory=True)
            check("S2_MCP_outside_" + component,
                  lambda: Transport(session).dispatch("study_inspect", {"study_dir": "study"}),
                  lambda v: rejected(v) and "link" in v["details"]["reason"])
        dest = clone("nested-link")
        nested = next((dest / "runs" / "r").iterdir())
        outside = root / "outside-nested"
        nested.rename(outside)
        nested.symlink_to(outside, target_is_directory=True)
        check("S2_nested_run_directory_link", lambda: inspect_study(dest), rejected)
        dest = clone("fifo")
        os.mkfifo(dest / "unexpected-pipe")
        check("S2_special_file", lambda: inspect_study(dest), rejected)
        dest = clone("dangling-link")
        (dest / "unexpected-link").symlink_to(root / "missing")
        check("S2_dangling_link", lambda: inspect_study(dest), rejected)

        community = {"method": "community", "format": "past", "orientation": "samples_by_taxa",
                     "value_type": "count", "transform": "none", "distance": "braycurtis",
                     "dimensions": 1, "missing": "error", "empty_samples": "error"}
        (materials / "counts.dat").write_text(". t1 t2 t3\na 2 4 8\nb 3 7 1\nc 9 1 2\nd 5 3 9\n")
        counts = deepcopy(spec)
        counts["inputs"]["m"].update(kind="counts", path="counts.dat")
        counts["analyses"][0]["spec"] = community
        for name, method, kind in (
            ("retranspose", dict(community, orientation="taxa_by_samples"), "counts"),
            ("wrong_format", dict(community, format="csv"), "counts"),
            ("missing_format", {k: v for k, v in community.items() if k != "format"}, "counts"),
            ("rma_on_counts", spec["analyses"][0]["spec"], "counts"),
            ("community_on_measurements", community, "measurements"),
        ):
            changed = deepcopy(counts)
            changed["analyses"][0]["spec"] = method
            changed["inputs"]["m"]["kind"] = kind
            check("S3_" + name, lambda: run_study(changed, root / name, base_dir=materials), rejected)

        partial = deepcopy(spec)
        partial["datasets"] = {
            "before": {"source": "m"},
            "bad": {"source": "m", "operations": [{"op": "exclude", "samples": ["absent"], "reason": "synthetic failure"}]},
            "later": {"source": "m"}}
        partial["analyses"][0]["dataset"] = "later"
        expected = [("dataset:before", "complete"), ("dataset:bad", "failed"),
                    ("dataset:later", "not_run"), ("analysis:r", "not_run")]
        check("S4_dataset_failure_preserves_full_order", lambda: run_study(partial, root / "partial-dataset", base_dir=materials),
              lambda v: [(s["id"], s["status"]) for s in v["steps"]] == expected)
        check("S4_valid_partial_dataset_verifies", lambda: inspect_study(root / "partial-dataset"),
              lambda v: v["status"] == "verified" and v["study_status"] == "partial" and not v["runs"])
        check("S4_valid_partial_dataset_reproduces", lambda: reproduce_study(root / "partial-dataset", root / "partial-dataset-again"),
              lambda v: v["status"] == "reproduced")
        partial = deepcopy(spec)
        partial["analyses"].extend([
            {"id": "bad", "dataset": "d", "spec": dict(spec["analyses"][0]["spec"], x="absent")},
            {"id": "later", "dataset": "d", "spec": spec["analyses"][0]["spec"]}])
        run_study(partial, root / "partial-analysis", base_dir=materials)
        check("S1_valid_partial_analysis_verifies", lambda: inspect_study(root / "partial-analysis"),
              lambda v: [s["status"] for s in v["steps"]] == ["complete", "complete", "failed", "not_run"]
              and set(v["runs"]) == {"r"})
        check("S1_valid_partial_analysis_reproduces", lambda: reproduce_study(root / "partial-analysis", root / "partial-analysis-again"),
              lambda v: v["status"] == "reproduced")

    payload = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
               "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "checks": len(observations), "passed": sum(x["passed"] for x in observations), "observations": observations}
    receipt.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "observations"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    main(parser.parse_args().receipt)
