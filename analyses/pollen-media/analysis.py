"""Run the frozen pollen-media study and write its API-field summary."""

import json
import hashlib
import shutil
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs-study"


def _read_runs(study_dir):
    manifest = json.loads((study_dir / "manifest.json").read_text(encoding="utf-8"))
    return {name: json.loads((study_dir / item["run_dir"] / "results.json").read_text(encoding="utf-8"))
            for name, item in manifest["runs"].items()}, manifest


def _community_summary(result):
    keys = ("method", "method_version", "orientation", "canonical_orientation", "value_type", "transform",
            "distance", "dimensions", "n_input", "n", "n_taxa", "input_sample_ids", "sample_ids", "taxon_ids",
            "diversity", "distances", "coordinates", "eigenvalues", "axis_positive_inertia",
            "negative_to_positive_inertia", "metadata", "excluded", "warnings", "references", "limitations")
    return {key: result[key] for key in keys if key in result}


def _homogeneity_summary(result):
    pair_keys = ("sample_ids", "taxon_ids", "taxa_absent_from_pair", "observed_counts", "expected_counts",
                 "sample_totals", "pooled_taxon_totals", "pearson_chi_squared", "braycurtis_proportions",
                 "p_value", "p_value_holm", "monte_carlo", "taxon_tests")
    out = {key: result[key] for key in ("method", "method_version", "orientation", "canonical_orientation",
                                         "value_type", "missing", "empty_samples", "n_input", "n", "n_taxa",
                                         "input_sample_ids", "sample_ids", "taxon_ids", "retained_counts", "metadata",
                                         "excluded", "warnings", "pair_declaration", "zero_count_limits", "confidence",
                                         "multiplicity", "randomization", "references", "limitations") if key in result}
    out["pairs"] = [{key: pair[key] for key in pair_keys if key in pair} for pair in result["pairs"]]
    return out


def _rarefaction_summary(result):
    keys = ("method", "method_version", "orientation", "canonical_orientation", "value_type", "missing",
            "empty_samples", "n_input", "n", "n_taxa", "input_sample_ids", "sample_ids", "taxon_ids",
            "sizes", "sizes_resolved", "samples", "metadata", "excluded", "warnings", "references", "limitations")
    return {key: result[key] for key in keys if key in result}


def _pair_distances(community, pairs):
    positions = {sample_id: i for i, sample_id in enumerate(community["sample_ids"])}
    return [{"sample_ids": pair, "distance": community["distances"][positions[pair[0]]][positions[pair[1]]]}
            for pair in pairs]


def _provenance(study_dir, manifest):
    extraction_bundles = sorted(path for path in (HERE / "extraction").iterdir() if path.is_dir())
    if len(extraction_bundles) != 1:
        raise SystemExit(f"expected one extraction bundle, found {len(extraction_bundles)}")
    extraction = extraction_bundles[0]
    out = {"extraction_bundle": str(extraction.relative_to(HERE)),
           "extraction_manifest_sha256": hashlib.sha256((extraction / "manifest.json").read_bytes()).hexdigest(),
           "study_dir": "runs-study", "study_manifest_sha256": hashlib.sha256((study_dir / "manifest.json").read_bytes()).hexdigest(),
           "runs": {}}
    for name, item in manifest["runs"].items():
        run_dir = study_dir / item["run_dir"]
        run_manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        out["runs"][name] = {
            "run_dir": item["run_dir"],
            "run_id": run_manifest.get("run_id"),
            "run_manifest_sha256": hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest(),
            "environment": json.loads((run_dir / "environment.json").read_text(encoding="utf-8")),
        }
    return out


def main():
    if RUNS.exists():
        shutil.rmtree(RUNS)
    outcome = pa.run_study(HERE / "study.json", RUNS)
    if outcome["status"] != "complete":
        raise SystemExit(json.dumps(outcome, indent=1))
    inspected = pa.inspect_study(outcome["study_dir"])
    if inspected["status"] != "verified":
        raise SystemExit(json.dumps(inspected, indent=1))
    study_dir = Path(outcome["study_dir"])
    runs, manifest = _read_runs(study_dir)
    expected = {"primary_community", "inclusive_community", "primary_rarefaction", "trap_primary",
                "trap_inclusive", "baseline_tyndall_surface"}
    if set(runs) != expected:
        raise SystemExit(f"unexpected completed analyses: {sorted(runs)}")

    primary_pairs = json.loads((HERE / "study.json").read_text(encoding="utf-8"))["analyses"][3]["spec"]["pairs"]
    baseline_pairs = json.loads((HERE / "study.json").read_text(encoding="utf-8"))["analyses"][5]["spec"]["pairs"]
    results = {
        "study_status": inspected["study_status"],
        "inspection_status": inspected["status"],
        "primer": {key: pa.primer()[key] for key in ("version", "sha256")},
        "primary_community": _community_summary(runs["primary_community"]),
        "inclusive_community": _community_summary(runs["inclusive_community"]),
        "primary_rarefaction": _rarefaction_summary(runs["primary_rarefaction"]),
        "primary_pair_distances": _pair_distances(runs["primary_community"], primary_pairs + baseline_pairs),
        "inclusive_trap_pair_distances": _pair_distances(runs["inclusive_community"], primary_pairs),
        "trap_primary": _homogeneity_summary(runs["trap_primary"]),
        "trap_inclusive": _homogeneity_summary(runs["trap_inclusive"]),
        "baseline_tyndall_surface": _homogeneity_summary(runs["baseline_tyndall_surface"]),
        "unsupported_parts": [{
            "subtask": "archived collection-medium interpretation and metadata transcription",
            "why_toolkit_could_not_do_it": "The toolkit does not interpret archived notes or infer medium labels.",
            "what_used_instead": "Declared intake transcription from the archived notes and extraction sample metadata.",
            "how_checked": "Exact sample IDs, sitenames and archived depth/index values checked against extraction samples.csv and intake-check.json.",
        }],
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    (HERE / "provenance.json").write_text(json.dumps(_provenance(study_dir, manifest), indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"study": inspected["status"], "study_dir": str(study_dir),
                      "results": str(HERE / "results.json"), "provenance": str(HERE / "provenance.json")}, indent=1))


if __name__ == "__main__":
    main()
