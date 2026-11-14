"""Test whether broad archived pollen bins include their narrower co-recorded bins (Claude, 14 Nov 2026).

If a broad variable were a total that includes its narrower variables, then in every row broad >= sum(narrow).
A single row with broad < sum(narrow) contradicts inclusion for that dataset. Reads only the intake's raw
source tables (unnormalised weights); computes no distance. Writes receipt.json beside this script.

uv run references/independent/2026-11-14-tally-semantics/check.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INTAKE = ROOT / "analyses/lake-selina-analogues"
FAMILIES = {
    "Asteraceae": ["Asteroideae", "Cichorioideae"],
    "Eucalyptus": ["Eucalyptus vernicosa"],
    "Melaleuca": ["Melaleuca squamea"],
    "Plantago": ["Plantago lanceolata"],
    "Pomaderris": ["Pomaderris apetala"],
    "Casuarinaceae": ["Allocasuarina", "Casuarina"],
    "Ericaceae": ["Epacrideae", "Epacris", "Richea", "Sprengelia", "Monotoca", "Leucopogon"],
    "Proteaceae": ["Agastachys", "Banksia", "Bellendena", "Orites", "Telopea", "Lomatia", "Persoonia"],
    "Myrtaceae": ["Leptospermum", "Eucalyptus", "Melaleuca", "Leptospermum/Baeckea", "Melaleuca-type"],
    "Cupressaceae": ["Athrotaxis", "Athrotaxis/Diselma"],
    "Apiaceae": ["Oreomyrrhis"],
}


def read(path):
    rows = list(csv.reader(path.open(), delimiter="\t"))
    header = rows[0][1:]
    return header, [(row[0], dict(zip(header, map(float, row[1:])))) for row in rows[1:]]


def main():
    dataset = {r["sample_id"]: r["datasetid"] for r in csv.DictReader((INTAKE / "metadata-seed.csv").open())}
    out = []
    for source in ("fossil", "modern_percent", "modern_nisp"):
        header, rows = read(INTAKE / "data" / f"{source}.tsv")
        for broad, narrow in FAMILIES.items():
            present = [n for n in narrow if n in header]
            if broad not in header or not present:
                continue
            both = [(sid, r[broad], sum(r[n] for n in present)) for sid, r in rows
                    if r[broad] > 0 and sum(r[n] for n in present) > 0]
            contradicted = [sid for sid, b, s in both if b < s]
            out.append({"source": source, "broad": broad, "narrow": present, "rows_with_both": len(both),
                        "rows_contradicting_inclusion": len(contradicted),
                        "datasets_contradicting": sorted({dataset.get(s, "52767") for s in contradicted}),
                        "datasets_with_both": sorted({dataset.get(s, "52767") for s, _, _ in both})})
    receipt = {"question": "Do broad archived bins include co-recorded narrower bins?",
               "rule": "inclusion implies broad >= sum(narrow) in every row; one violation contradicts it for that dataset",
               "results": out}
    (Path(__file__).parent / "receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")
    for r in out:
        print(f"{r['source']:15s} {r['broad']:13s} both={r['rows_with_both']:3d} contradict={r['rows_contradicting_inclusion']:3d} "
              f"datasets {len(r['datasets_contradicting'])}/{len(r['datasets_with_both'])}")


if __name__ == "__main__":
    main()
