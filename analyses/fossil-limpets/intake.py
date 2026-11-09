"""Prepare the frozen fossil-limpet CSV and check the design without fitting it."""

import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path

import palaeo_agent as pa
from palaeo_agent.core import RmaSpec
from palaeo_agent.study import StudySpec, derive, read_table

HERE = Path(__file__).resolve().parent
COLUMNS = ["Length_Caliper_mm", "MajorAxisLength_AutoMorph_mm",
           "Width_Caliper_mm", "MinorAxisLength_AutoMorph_mm"]
PRIMER_SHA256 = "089a91663185ebff31e358a7e4c5f34e899336d1d1f26c0032f7a17f54c49e99"


def encoded_table(header, rows, delimiter):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=delimiter, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode()


def main():
    card = json.loads((HERE / "source/source.json").read_text())
    data = (HERE / "source" / card["file"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == card["sha256"]
    assert len(data) == card["bytes"]
    assert "md5:" + hashlib.md5(data).hexdigest() == card["registered_checksum"]
    assert card["license"] == "CC-BY-4.0"
    reader = csv.DictReader(io.StringIO(data.decode()))
    assert reader.fieldnames == ["SampleID", "ObjectID", *COLUMNS]
    rows = list(reader)
    assert {row["SampleID"] for row in rows} == {"Edmitchelli_LAMNH12577_lot_4"}
    assert all(Decimal(row[column]).is_finite() and Decimal(row[column]) > 0
               for row in rows for column in COLUMNS)
    table = encoded_table(["specimen_id", *COLUMNS],
                          ([row["ObjectID"], *[row[c] for c in COLUMNS]] for row in rows), "\t")
    provenance = encoded_table(["ObjectID", "SampleID", "source_csv_row"],
                               ([row["ObjectID"], row["SampleID"], i] for i, row in enumerate(rows, 2)), ",")
    spec = StudySpec.model_validate_json((HERE / "study.json").read_bytes())
    parsed = read_table(table, spec.inputs["limpets"])
    assert parsed["samples"] == [row["ObjectID"] for row in rows]
    assert parsed["values"] == [[row[c] for c in COLUMNS] for row in rows]
    files, preparation = derive(spec, {"limpets": table}, "shells")
    assert preparation["operations"][0]["samples"] == 136
    for analysis in spec.analyses:
        RmaSpec.model_validate(dict(analysis.spec, input="derived/shells.dat"))
    primer = pa.primer()
    assert primer["sha256"] == PRIMER_SHA256
    (HERE / "measurements.tsv").write_bytes(table)
    (HERE / "specimens.csv").write_bytes(provenance)
    receipt = {
        "stage": "pre_results_design", "source_sha256": card["sha256"],
        "primer": {k: primer[k] for k in ("version", "sha256")},
        "preparation": preparation,
        "measurements_sha256": hashlib.sha256(table).hexdigest(),
        "specimens_sha256": hashlib.sha256(provenance).hexdigest(),
        "derived_table_sha256": hashlib.sha256(files["shells.dat"]).hexdigest(),
        "study_schema_valid": True, "rma_specifications_schema_valid": True,
        "all_four_measurements_present_and_positive": True,
        "new_fits_computed": False, "method_validate_called": False,
        "source_discrepancy": "Supplement describes 139 shells; the frozen CSV has 136. No absent specimens are reconstructed.",
    }
    (HERE / "intake-check.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"stage": receipt["stage"], "specimens": len(preparation["samples"]),
                      "new_fits_computed": False}))


if __name__ == "__main__":
    main()
