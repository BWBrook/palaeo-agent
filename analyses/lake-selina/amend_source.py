"""Amendment 1 (AMENDMENT-1.md): dryland pollen sum from Colhoun et al. (1999). Run: uv run analyses/lake-selina/amend_source.py

Derives data/counts-dryland.tsv from the frozen data/counts.tsv by removing the paper's sedge and aquatic
columns, and writes design-amended.json with the same 77 pairs, B and seed. Computes no result.
"""

import hashlib
import json
from pathlib import Path

import palaeo_agent as pa

HERE = Path(__file__).resolve().parent
EXCLUDED = {
    "sedges": ["Cyperaceae", "Gymnoschoenus sphaerocephalus", "Restionaceae", "Xyridaceae"],
    "aquatics": ["Portulacaceae", "Ranunculus"],
}
OFFSET_CM = 30
FLAGGED = {"531331": "archive 220 cm: no Lagarostrobos entry and dryland total 408 against printed 480 at paper "
                     "190 cm, where the paper reports a strong Lagarostrobos peak"}


def main():
    design = json.loads((HERE / "design.json").read_text())
    source = HERE / "data/counts.tsv"
    if hashlib.sha256(source.read_bytes()).hexdigest() != design["counts_sha256"]:
        raise SystemExit("data/counts.tsv differs from the stage-1 freeze")
    rows = [line.split("\t") for line in source.read_text().splitlines()]
    drop = {name for names in EXCLUDED.values() for name in names}
    if not drop <= set(rows[0]):
        raise SystemExit("an excluded label is missing from the frozen table")
    keep = [i for i, name in enumerate(rows[0]) if name not in drop]
    table = HERE / "data/counts-dryland.tsv"
    table.write_text("\n".join("\t".join(r[i] for i in keep) for r in rows) + "\n")
    totals = {r[0]: sum(int(r[i]) for i in keep[1:]) for r in rows[1:]}
    size = min(totals.values())
    specs = {}
    for name, spec in design["specs"].items():
        spec = dict(spec, input="data/counts-dryland.tsv")
        if name == "rarefaction":
            spec["sizes"] = [size]
        specs[name] = spec
    validation = {k: pa.validate(dict(v, input=str(table))) for k, v in specs.items()}
    amended = {
        "stage": "amendment 1: source-driven, after stage-2 results; see AMENDMENT-1.md",
        "base_design_counts_sha256": design["counts_sha256"],
        "denominator": {"rule": "Colhoun et al. (1999) dryland terrestrial sum: stage-1 table minus sedge and "
                                "aquatic pollen columns per Figure 6 groups", "excluded": EXCLUDED,
                        "n_levels": len(rows) - 1, "n_taxa": len(keep) - 1, "size": size,
                        "size_sample": [k for k, v in totals.items() if v == size]},
        "depth_annotation": {"candidate_paper_depth": f"archive depth - {OFFSET_CM} cm",
                             "status": "supported by nine printed sums and zone boundaries; not proved"},
        "suppress_ages": True,
        "flagged_levels": FLAGGED,
        "named_comparisons": design["named_comparisons"], "chronology_sensitivity": design["chronology_sensitivity"],
        "declared_pairs": design["declared_pairs"], "reporting_rules": design["reporting_rules"],
        "specs": specs, "validation": validation,
        "amend_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "counts_sha256": hashlib.sha256(table.read_bytes()).hexdigest(),
    }
    (HERE / "design-amended.json").write_text(json.dumps(amended, indent=1) + "\n")
    print(json.dumps({"n_taxa": len(keep) - 1, "size": size, "validation": {k: v["status"] for k, v in validation.items()}}))


if __name__ == "__main__":
    main()
