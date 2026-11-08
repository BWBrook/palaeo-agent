"""Intake for the Tasmanian surface-pollen worked example. Run: uv run analyses/tas-surface/intake.py

Unsupported intake glue (declared in REPORT.md): reading the Neotoma download, choosing one sample per
record from the archived notes, assigning altitude bands, and writing the abundance table, metadata and the
toolkit study. Writes data/percent.tsv (all 61 percent samples), data/samples.csv (the 25 selected samples)
and study.json. Computes no composition result.
"""

import csv
import hashlib
import json
import re
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source/neotoma-tas-surface-download.json"
SOURCE_SHA256 = "0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36"
GROUPS = ("TRSH", "UPHE")
WETLAND = ["Cyperaceae", "Restionaceae", "Gymnoschoenus"]
THRESHOLD_M = 700
PERMUTATIONS, SEED = 9999, 8112026


def note_altitude(notes, index):
    """Sample altitude stated in collection notes as 'sample N: X m', if any."""
    match = re.search(rf"sample {index}(?: \([^)]*\))?: (\d+) m", notes or "", flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def main():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise SystemExit("source download differs from the saved intake copy")
    records = json.loads(SOURCE.read_text())["data"]
    rows, taxa, chosen = {}, set(), []
    for rec in records:
        site, unit = rec["site"], rec["site"]["collectionunit"]
        dataset = unit["dataset"]
        units = {d["units"] for s in dataset["samples"] for d in s["datum"]}
        if units != {"percent"}:
            continue
        for sample in dataset["samples"]:
            values = {}
            for d in sample["datum"]:
                if d["ecologicalgroup"] in GROUPS:
                    if d["variablename"] in values:
                        raise SystemExit(f"repeated label {d['variablename']} in sample {sample['sampleid']}")
                    values[d["variablename"]] = d["value"]
            rows[str(sample["sampleid"])] = values
            taxa |= set(values)
        first = next(s for s in dataset["samples"] if s["depth"] == 1)
        stated = note_altitude(unit["notes"], 1)
        altitude = stated if stated is not None else site["altitude"]
        lon, lat = json.loads(site["geography"])["coordinates"][:2]
        chosen.append({"sample_id": str(first["sampleid"]), "site": site["sitename"],
                       "datasetid": str(dataset["datasetid"]), "altitude_m": str(altitude),
                       "altitude_source": "sample note" if stated is not None else "site altitude",
                       "band": "high" if altitude >= THRESHOLD_M else "low",
                       "environment": unit["depositionalenvironment"] or "",
                       "source_pi": "; ".join(p["contactname"] for p in dataset["datasetpi"]),
                       "lon": str(lon), "lat": str(lat)})
    names = sorted(taxa)
    lines = ["\t".join(["sample_id", *names])]
    lines += ["\t".join([sid, *[repr(rows[sid].get(n, 0)) if n in rows[sid] else "0" for n in names]])
              for sid in sorted(rows)]
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data/percent.tsv").write_text("\n".join(lines) + "\n")
    coords = {}
    for c in chosen:
        coords.setdefault((c["lon"], c["lat"]), []).append(c["site"])
    for c in chosen:
        shared = [s for s in coords[(c["lon"], c["lat"])] if s != c["site"]]
        c["shares_coordinates_with"] = "; ".join(shared)
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
    print(json.dumps({"samples_in_table": len(rows), "taxa": len(names), "selected": len(chosen), "bands": bands,
                      "altitude_from_notes": [c["site"] for c in chosen if c["altitude_source"] == "sample note"],
                      "shared_coordinates": sorted({c["site"] for c in chosen if c["shares_coordinates_with"]})}, indent=1))


if __name__ == "__main__":
    main()
