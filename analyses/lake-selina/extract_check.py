"""Demonstrate neotoma_extract on the Lake Selina download. Run: uv run analyses/lake-selina/extract_check.py

Extracts the archived pollen counts (NISP; TRSH and UPHE; depth order) into a verified bundle under
runs-extraction/ (gitignored), then compares its table with the frozen intake's data/counts.tsv and its age
rows with data/levels.csv. Writes extract-check.json. The frozen intake is left unchanged.
"""

import csv
import hashlib
import json
import shutil
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source/neotoma-52767-download.json"
PRIMARY, ALTERNATIVE = "37590", "37589"


def main():
    root = HERE / "runs-extraction"
    shutil.rmtree(root, ignore_errors=True)
    out = pa.neotoma_extract({"source": str(SOURCE), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                              "datasets": "all", "units": "NISP", "elements": ["pollen"],
                              "ecological_groups": ["TRSH", "UPHE"], "absent_taxa": "zero", "row_order": "depth"}, root)
    bundle = Path(out["bundle"])
    ages = list(csv.DictReader(open(bundle / "ages.csv", encoding="utf-8")))
    by = {(a["sample_id"], a["chronologyid"]): a for a in ages}
    levels = list(csv.DictReader(open(HERE / "data/levels.csv", encoding="utf-8")))
    check = {
        "extraction_status": pa.inspect_neotoma(bundle)["status"],
        "shape": [out["n_samples"], out["n_labels"]],
        "table_byte_identical_to_frozen_counts": (bundle / "table.tsv").read_bytes() == (HERE / "data/counts.tsv").read_bytes(),
        "age_rows": len(ages),
        "default_chronology_rows": sum(a["is_default_chronology"] == "true" for a in ages),
        "ages_match_levels": all(by[(lv["sample_id"], PRIMARY)]["age"] == lv["age_ippd2"] and
                                 by[(lv["sample_id"], PRIMARY)]["ageyounger"] == lv["age_ippd2_younger"] and
                                 by[(lv["sample_id"], PRIMARY)]["ageolder"] == lv["age_ippd2_older"] and
                                 by[(lv["sample_id"], ALTERNATIVE)]["age"] == lv["age_ippd1"] for lv in levels),
        "dropped": json.loads((bundle / "extract.json").read_text())["dropped"],
    }
    (HERE / "extract-check.json").write_text(json.dumps(check, indent=1) + "\n")
    print(json.dumps(check, indent=1))


if __name__ == "__main__":
    main()
