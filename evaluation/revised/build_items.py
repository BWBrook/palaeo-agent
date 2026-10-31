"""Build a prospective sprint-1 bank without modifying the frozen v1 bank.

The revised bank copies every v1 item, then amends only the two reviewed
items. The output path is explicit so a caller cannot overwrite v1 records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from . import VERSION


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "items"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _update_provenance(path: Path, *, purpose: str, source_item: str) -> None:
    document = json.loads(path.read_text())
    document["generator"] = "evaluation/revised/build_items.py"
    document["version"] = VERSION
    document["source_item"] = source_item
    document["purpose"] = purpose
    document["materials_sha256"] = {
        p.name: digest(p) for p in sorted((path.parent / "materials").iterdir())
    }
    path.write_text(json.dumps(document, indent=1) + "\n")


def _amend_d2(destination: Path) -> None:
    materials = destination / "materials"
    source = SOURCE / "D2-under" / "materials" / "assemblages.tsv"
    rows = []
    for line_number, line in enumerate(source.read_text().splitlines()):
        fields = line.split("\t")
        if line_number > 0:
            fields[1:] = [str(round(float(value))) for value in fields[1:]]
        rows.append("\t".join(fields))
    (materials / "assemblages.tsv").write_text("\n".join(rows) + "\n")
    (materials / "dictionary.md").write_text(
        "# Data dictionary\n\n"
        "Tables are tab-separated. The first row holds column labels and its first cell is `.`; "
        "the first column holds row labels.\n\n"
        "`assemblages.tsv`: samples in rows, brachiopod genera in columns. Each value is an "
        "integer percentage, rounded from the reported composition. Sample totals and specimen "
        "counts are not supplied. This follows the catalogue's coarser percentage display; a "
        "harder uncoached ambiguity construction is deferred to bank v2.\n\n"
        "Samples, in order: P1, P2, P3, P4, P5, P6.\n"
    )
    key = json.loads((destination / "key.json").read_text())
    key["version"] = VERSION
    key["amendment"] = "Integer percentages align the catalogue display; harder uncoached ambiguity is deferred."
    (destination / "key.json").write_text(json.dumps(key, indent=1) + "\n")
    _update_provenance(
        destination / "provenance.json",
        source_item="D2-under",
        purpose="Integer percentages without sample totals leave raw-count Bray-Curtis underdetermined.",
    )


def _amend_d7(destination: Path) -> None:
    materials = destination / "materials"
    (materials / "dictionary.md").write_text(
        "# Data dictionary\n\n"
        "Tables are tab-separated. The first row holds column labels and its first cell is `.`; "
        "the first column holds row labels.\n\n"
        "`counts.tsv`: samples in rows, labelled by sample ID; brachiopod genera in columns; "
        "values are specimen counts. Sample K5 is an invalid or failed sampling event: it was "
        "processed but yielded no specimens, so its zero row does not establish absence. The "
        "requested analysis is over valid samples and must record exclusion of K5.\n"
    )
    (materials / "task.md").write_text(
        "# Mean dissimilarity\n\n"
        "Report the mean of the Bray-Curtis dissimilarities (raw counts) over all pairs of valid "
        "samples. K5 is identified in the dictionary as a failed sampling event and must be "
        "excluded; record that exclusion and its reason.\n\n"
        "Report in `results`: `mean_braycurtis`, and `n_pairs`, the number of pairwise values averaged.\n"
    )
    key = json.loads((destination / "key.json").read_text())
    key["version"] = VERSION
    key["item"] = "D7-control"
    key["class"] = "twin"
    key["amendment"] = "Explicit-instruction control: valid-sample analysis excludes failed sampling K5; no trap-detection credit."
    (destination / "key.json").write_text(json.dumps(key, indent=1) + "\n")
    _update_provenance(
        destination / "provenance.json",
        source_item="D7-trap",
        purpose="The dictionary explicitly identifies K5 as failed sampling; valid-sample Bray-Curtis excludes it.",
    )


def build(output: Path) -> dict[str, str]:
    output = Path(output).resolve()
    source = SOURCE.resolve()
    if output == source or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("revised bank output must be separate from evaluation/items")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing revised-bank output: {output}")
    output.mkdir(parents=True)
    for item in sorted(p for p in SOURCE.iterdir() if p.is_dir()):
        shutil.copytree(item, output / item.name)
    _amend_d2(output / "D2-under")
    (output / "D7-trap").rename(output / "D7-control")
    _amend_d7(output / "D7-control")
    manifest = {
        item.name: digest(item / "key.json")
        for item in sorted(p for p in output.iterdir() if p.is_dir())
    }
    document = {
        "version": VERSION,
        "source": "evaluation/items",
        "source_manifest_sha256": digest(SOURCE / "MANIFEST.json"),
        "amended_items": ["D2-under", "D7-control"],
        "items": manifest,
    }
    (output / "MANIFEST.json").write_text(json.dumps(document, indent=1) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({"version": VERSION, "items": len(result), "output": str(args.output)}))


if __name__ == "__main__":
    main()
