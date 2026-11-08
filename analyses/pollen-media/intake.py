"""Extract the frozen Neotoma pollen-media table and write the declared study.

The toolkit performs all supported extraction and analytical preparation. The
medium labels are transcription glue from the archived collection notes, as
declared in PROPOSAL.md; this script computes no scientific quantities.
"""

import csv
import json
import shutil
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "tas-surface/source/neotoma-tas-surface-download.json"
EXTRACTION_SPEC = {
    "source": str(SOURCE),
    "source_sha256": "0205169197c51e03da06e914d157136c965cd7bffb13f103817888ff2fb58c36",
    "datasets": [74305, 74913],
    "units": "NISP",
    "elements": ["pollen", "pollen/spore", "spore"],
    "ecological_groups": ["TRSH", "UPHE"],
    "absent_taxa": "zero",
    "row_order": "source",
}
SAMPLE_ORDER = ["1466027", "1466028", "1466029", "1480879", "1480880", "1480881", "1480882"]
MEDIUM = {
    "1466027": ("Hartz Mountains", "1", "core top"),
    "1466028": ("Hartz Mountains", "2", "moss polster"),
    "1466029": ("Hartz Mountains", "3", "pollen trap"),
    "1480879": ("Tyndall Ranges", "1", "pollen trap"),
    "1480880": ("Tyndall Ranges", "2", "surface sample"),
    "1480881": ("Tyndall Ranges", "3", "surface sample"),
    "1480882": ("Tyndall Ranges", "4", "surface sample"),
}
DRYLAND_EXCLUDED = ["Cyperaceae", "Restionaceae", "Gymnoschoenus"]
PAIRS = [
    ["1466029", "1466027"],
    ["1466029", "1466028"],
    ["1480879", "1480880"],
    ["1480879", "1480881"],
    ["1480879", "1480882"],
]
BASELINE_PAIRS = [["1480880", "1480881"], ["1480880", "1480882"], ["1480881", "1480882"]]
SIMULATIONS, SEED = 99999, 20261108


def _metadata(samples_path):
    rows = {row["sample_id"]: row for row in csv.DictReader(samples_path.open(encoding="utf-8"))}
    if set(rows) != set(SAMPLE_ORDER):
        raise SystemExit(f"extraction sample IDs differ: {sorted(rows)}")
    metadata = []
    for sample_id in SAMPLE_ORDER:
        row = rows[sample_id]
        site, index, medium = MEDIUM[sample_id]
        if row["sitename"] != site or row["depth"] != index:
            raise SystemExit(f"archived mapping mismatch for {sample_id}: {row['sitename']} depth {row['depth']}")
        metadata.append({"sample_id": sample_id, "site": site, "archived_index": index, "medium": medium})
    return metadata


def main():
    extraction_root = HERE / "extraction"
    if extraction_root.exists():
        shutil.rmtree(extraction_root)
    extracted = pa.neotoma_extract(EXTRACTION_SPEC, extraction_root)
    inspected = pa.inspect_neotoma(extracted["bundle"])
    if inspected["status"] != "verified" or (extracted["n_samples"], extracted["n_labels"]) != (7, 82):
        raise SystemExit(f"unexpected extraction: {extracted}")

    data_dir = HERE / "data"
    data_dir.mkdir(exist_ok=True)
    shutil.copyfile(extracted["table"], data_dir / "counts.tsv")
    metadata = _metadata(Path(extracted["samples"]))
    with (data_dir / "samples.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["sample_id", "site", "archived_index", "medium"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(metadata)

    common = {"format": "delimited", "delimiter": "tab", "orientation": "samples_by_taxa",
              "value_type": "count", "missing": "error", "empty_samples": "error"}
    analysis_common = {"format": "past", "orientation": "samples_by_taxa", "value_type": "count",
                       "missing": "error", "empty_samples": "error"}
    study = {
        "study_version": 1,
        "inputs": {
            "counts": {"kind": "counts", "path": "data/counts.tsv", "format": "delimited",
                       "delimiter": "tab", "orientation": "samples_by_taxa"},
            "samples": {"kind": "metadata", "path": "data/samples.csv", "id_column": "sample_id"},
        },
        "datasets": {
            "primary": {"source": "counts", "metadata": "samples", "operations": [
                {"op": "select", "samples": SAMPLE_ORDER,
                 "reason": "predeclared presentation order from archived sample identities"},
                {"op": "exclude_taxa", "taxa": DRYLAND_EXCLUDED,
                 "reason": "dryland pollen sum excludes the three declared sedge/rush categories"},
            ]},
            "inclusive": {"source": "counts", "metadata": "samples", "operations": [
                {"op": "select", "samples": SAMPLE_ORDER,
                 "reason": "predeclared presentation order from archived sample identities"},
            ]},
        },
        "analyses": [
            {"id": "primary_community", "dataset": "primary",
             "spec": {**analysis_common, "method": "community", "transform": "relative_abundance",
                      "distance": "braycurtis", "dimensions": 2}},
            {"id": "inclusive_community", "dataset": "inclusive",
             "spec": {**analysis_common, "method": "community", "transform": "relative_abundance",
                      "distance": "braycurtis", "dimensions": 2}},
            {"id": "primary_rarefaction", "dataset": "primary",
             "spec": {**analysis_common, "method": "rarefaction", "sizes": "minimum_total"}},
            {"id": "trap_primary", "dataset": "primary",
             "spec": {**analysis_common, "method": "count_homogeneity", "pairs": PAIRS,
                      "simulations": SIMULATIONS, "seed": SEED}},
            {"id": "trap_inclusive", "dataset": "inclusive",
             "spec": {**analysis_common, "method": "count_homogeneity", "pairs": PAIRS,
                      "simulations": SIMULATIONS, "seed": SEED}},
            {"id": "baseline_tyndall_surface", "dataset": "primary",
             "spec": {**analysis_common, "method": "count_homogeneity", "pairs": BASELINE_PAIRS,
                      "simulations": SIMULATIONS, "seed": SEED}},
        ],
    }
    (HERE / "study.json").write_text(json.dumps(study, indent=1) + "\n", encoding="utf-8")
    receipt = {
        "primer": {k: pa.primer()[k] for k in ("version", "sha256")},
        "extraction": inspected,
        "metadata_rows": metadata,
        "sample_order": SAMPLE_ORDER,
        "primary_excluded_taxa": DRYLAND_EXCLUDED,
        "pairs": PAIRS,
        "baseline_pairs": BASELINE_PAIRS,
        "scope": "verified extraction and declared metadata/study preparation; no analysis results",
    }
    (HERE / "intake-receipt.json").write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"extraction": inspected["status"], "samples": extracted["n_samples"],
                      "categories": extracted["n_labels"], "study": str(HERE / "study.json")}, indent=1))


if __name__ == "__main__":
    main()
