"""Run the approved study and report inspected API results."""

import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path

import palaeo_agent as pa

from intake import main as prepare

HERE = Path(__file__).resolve().parent
SCALARS = ["n", "mean_x", "mean_y", "sd_x", "sd_y", "correlation", "slope",
           "intercept", "vertical_residual_rmse"]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def write_csv(path, fields, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "runs-study")
    args = parser.parse_args()
    prepare()
    outcome = pa.run_study(HERE / "study.json", args.output)
    assert outcome["status"] == "complete", outcome
    directory = Path(outcome["study_dir"])
    inspected = pa.inspect_study(directory)
    assert inspected["status"] == "verified"
    manifest = json.loads((directory / "manifest.json").read_bytes())
    records = {name: pa.inspect_run(directory / item["run_dir"])
               for name, item in manifest["runs"].items()}
    assert set(records) == {"caliper_log", "automorph_log"}
    fits = {name: record["result"] for name, record in records.items()}
    assert [p["sample_id"] for p in fits["caliper_log"]["pairs"]] == [
        p["sample_id"] for p in fits["automorph_log"]["pairs"]]
    spans = {}
    for name, result in fits.items():
        length = [pair["x_raw"] for pair in result["pairs"]]
        low, high = min(length), max(length)
        spans[name] = {"min": low, "max": high, "max_min_ratio": high / low,
                       "source_field": "pairs[].x_raw"}
    source = list(csv.DictReader(io.StringIO((HERE / "source/STable1_2DLimpets.csv").read_text())))
    caliper = [row[c] for row in source for c in ("Length_Caliper_mm", "Width_Caliper_mm")]
    auto = [row[c] for row in source for c in ("MajorAxisLength_AutoMorph_mm", "MinorAxisLength_AutoMorph_mm")]
    precision = {
        "all_fields_have_two_decimal_places": all(len(value.split(".")[1]) == 2 for value in caliper + auto),
        "all_caliper_values_on_0.1_mm_grid": all(Decimal(v) * 10 == (Decimal(v) * 10).to_integral() for v in caliper),
        "automorph_has_nonzero_hundredths": any(v[-1] != "0" for v in auto),
        "archived_caliper_grid_mm": 0.1, "archived_automorph_decimal_step_mm": 0.01,
        "published_caliper_resolution_mm": 0.1, "published_automorph_typical_resolution_mm": 0.001,
        "published_source": "source/source.json: supplement_url, pages 8-9",
        "scope": "Decimal representation and source-stated resolution, not an estimate of measurement error",
    }
    primer = pa.primer()
    write_json(HERE / "results.json", {"primer": {k: primer[k] for k in ("version", "sha256")},
                                      "fits": fits, "length_span_mm": spans, "measurement_precision": precision})
    provenance = {"study_dir": str(directory.relative_to(HERE)),
                  "study_manifest_sha256": hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest(),
                  "design_commit": "39815c3", "approval_board_message": 3117,
                  "study_sha256": hashlib.sha256((HERE / "study.json").read_bytes()).hexdigest(),
                  "runs": {}}
    for name, record in records.items():
        provenance["runs"][name] = {"run_dir": manifest["runs"][name]["run_dir"],
                                    "run_id": record["manifest"]["run_id"],
                                    "environment": record["environment"]}
    write_json(HERE / "provenance.json", provenance)
    write_csv(HERE / "api-scalars.csv", ["analysis_id", *SCALARS],
              [dict(analysis_id=name, **{key: result[key] for key in SCALARS}) for name, result in fits.items()])
    write_csv(HERE / "api-pairs.csv", ["analysis_id", "sample_id", "x_raw", "y_raw", "x", "y", "residual"],
              [dict(analysis_id=name, **pair) for name, result in fits.items() for pair in result["pairs"]])
    print(json.dumps({name: {key: result[key] for key in ("n", "correlation", "slope", "intercept", "warnings")}
                      for name, result in fits.items()}, indent=2))


if __name__ == "__main__":
    main()
