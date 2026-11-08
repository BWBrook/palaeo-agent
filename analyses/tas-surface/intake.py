"""Intake for the Tasmanian surface-pollen worked example. Run: uv run analyses/tas-surface/intake.py

The toolkit's neotoma_extract reads the saved download (declared datasets, units, filters, zero-fill) into a
verified extraction bundle under extraction/ (gitignored, regenerable). Its table becomes data/percent.tsv.
Remaining declared glue (REPORT.md): choosing sample 1 per dataset, reading sample altitudes from the archived
collection notes, assigning altitude bands and writing data/samples.csv and study.json. Computes no
composition result.
"""

import csv
import json
import re
import shutil
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
EXTRACTION = {
    "source": str(HERE / "source/neotoma-tas-surface-download.json"),
    "source_sha256": "0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36",
    "datasets": [74429, 75430, 74914, 74643, 74779, 74795, 74778, 74764, 74160, 74142, 74304, 74699, 74569,
                 74618, 74701, 74780, 73988, 74777, 74303, 74141, 75423, 74644, 74798, 74766, 75421],
    "units": "percent", "elements": ["pollen", "pollen/spore", "spore"], "ecological_groups": ["TRSH", "UPHE"],
    "absent_taxa": "zero", "row_order": "source",
}
WETLAND = ["Cyperaceae", "Restionaceae", "Gymnoschoenus"]
THRESHOLD_M = 700
PERMUTATIONS, SEED = 9999, 8112026


def note_altitude(notes, index):
    """Sample altitude stated in collection notes as 'sample N: X m', if any."""
    match = re.search(rf"sample {index}(?: \([^)]*\))?: (\d+) m", notes or "", flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def main():
    root = HERE / "extraction"
    shutil.rmtree(root, ignore_errors=True)
    extracted = pa.neotoma_extract(EXTRACTION, root)
    inspected = pa.inspect_neotoma(extracted["bundle"])
    (HERE / "data").mkdir(exist_ok=True)
    shutil.copyfile(extracted["table"], HERE / "data/percent.tsv")
    chosen = []
    for row in csv.DictReader(open(extracted["samples"], encoding="utf-8")):
        if row["depth"] != "1":
            continue
        stated = note_altitude(row["collectionunit_notes"], 1)
        altitude = stated if stated is not None else int(row["site_altitude"])
        chosen.append({"sample_id": row["sample_id"], "site": row["sitename"], "datasetid": row["datasetid"],
                       "altitude_m": str(altitude), "altitude_source": "sample note" if stated is not None else "site altitude",
                       "band": "high" if altitude >= THRESHOLD_M else "low",
                       "environment": row["depositionalenvironment"],
                       "source_pi": "; ".join(p["contactname"] for p in json.loads(row["dataset_pi"])),
                       "lon": row["lon"], "lat": row["lat"], "shares_coordinates_with": row["shares_coordinates_with"]})
    if len(chosen) != len(EXTRACTION["datasets"]):
        raise SystemExit("expected exactly one sample with archived depth 1 per dataset")
    with (HERE / "data/samples.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(chosen[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(chosen)
    common = {"format": "past", "orientation": "samples_by_taxa", "value_type": "abundance", "missing": "error",
              "empty_samples": "error"}
    permanova = dict(common, method="permanova", group_column="band", design="independent",
                     permutation_scheme="free", permutations=PERMUTATIONS, seed=SEED)
    study = {
        "study_version": 1,
        "inputs": {"percent": {"kind": "abundance", "path": "data/percent.tsv", "format": "delimited",
                               "delimiter": "tab", "orientation": "samples_by_taxa"},
                   "samples": {"kind": "metadata", "path": "data/samples.csv", "id_column": "sample_id"}},
        "datasets": {"surface": {"source": "percent", "metadata": "samples", "operations": [
            {"op": "select", "samples": [c["sample_id"] for c in chosen],
             "reason": "one record per archived dataset: sample 1 (archive depth field is a sample index)"},
            {"op": "exclude_taxa", "taxa": WETLAND,
             "reason": "sedge and rush categories excluded from the dryland comparison, as at Lake Selina"}]}},
        "analyses": [
            {"id": "composition", "dataset": "surface",
             "spec": dict(common, method="community", transform="relative_abundance", distance="braycurtis", dimensions=2)},
            {"id": "occurrence", "dataset": "surface",
             "spec": dict(common, method="community", transform="none", distance="jaccard", dimensions=2)},
            {"id": "association_braycurtis", "dataset": "surface",
             "spec": dict(permanova, transform="relative_abundance", distance="braycurtis")},
            {"id": "association_jaccard", "dataset": "surface",
             "spec": dict(permanova, transform="none", distance="jaccard")}],
    }
    (HERE / "study.json").write_text(json.dumps(study, indent=1) + "\n")
    bands = {b: sum(c["band"] == b for c in chosen) for b in ("high", "low")}
    print(json.dumps({"extraction": inspected["status"], "samples_in_table": extracted["n_samples"],
                      "taxa": extracted["n_labels"], "selected": len(chosen), "bands": bands,
                      "altitude_from_notes": [c["site"] for c in chosen if c["altitude_source"] == "sample note"],
                      "shared_coordinates": sorted({c["site"] for c in chosen if c["shares_coordinates_with"]})}, indent=1))


if __name__ == "__main__":
    main()
