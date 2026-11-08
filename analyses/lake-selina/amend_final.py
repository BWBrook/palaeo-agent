"""Amendment 2 (AMENDMENT-2.md): working case-study repairs. Run: uv run analyses/lake-selina/amend_final.py

Barry, 8 November 2026: this is an example dataset; infer or interpolate data issues and press on. From the
amendment-1 dryland table and the archived chronologies this writes:
- data/counts-final.tsv: 72 Lagarostrobos franklinii grains imputed at 531331 (printed sum 480 minus 408);
- data/levels-final.csv: an inferred age model under the +30 cm alignment (paper depth = archive - 30);
- design-final.json: the 71 adjacent pairs plus named and alternative-chronology endpoints reselected
  with the stage-1 window rule. Computes no composition result.
"""

import hashlib
import json
from pathlib import Path

import palaeo_agent as pa
from intake import WINDOWS, bracket

HERE = Path(__file__).resolve().parent
OFFSET_CM = 30
IMPUTED = {"sample_id": "531331", "taxon": "Lagarostrobos franklinii", "count": 72}
CONTROL_DEPTHS = (125, 150, 165, 230, 295)
DATED_BASE_PAPER_CM = 295


def interp(x, xs, ys):
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise ValueError(x)


def main():
    base = json.loads((HERE / "design-amended.json").read_text())
    source = HERE / "data/counts-dryland.tsv"
    if hashlib.sha256(source.read_bytes()).hexdigest() != base["counts_sha256"]:
        raise SystemExit("data/counts-dryland.tsv differs from amendment 1")
    rows = [line.split("\t") for line in source.read_text().splitlines()]
    col = rows[0].index(IMPUTED["taxon"])
    row = next(r for r in rows if r[0] == IMPUTED["sample_id"])
    if row[col] != "0":
        raise SystemExit("imputation target is not an absent count")
    row[col] = str(IMPUTED["count"])
    table = HERE / "data/counts-final.tsv"
    table.write_text("\n".join("\t".join(r) for r in rows) + "\n")

    archived = [line.split(",") for line in (HERE / "data/levels.csv").read_text().splitlines()[1:]]
    by_depth = {int(r[1]): r for r in archived}
    # Calibrated control ages: each archived model's own age at the control's depth label, with the
    # surface (paper 0 cm) at 0 cal BP.
    primary = [0] + [int(by_depth[d][2]) for d in CONTROL_DEPTHS]
    young = [-50] + [int(by_depth[d][3]) for d in CONTROL_DEPTHS]
    old = [50] + [int(by_depth[d][4]) for d in CONTROL_DEPTHS]
    alternative = [0] + [int(by_depth[d][5]) for d in CONTROL_DEPTHS]
    xs = [0, *CONTROL_DEPTHS]
    levels = []
    for r in archived:
        depth = int(r[1])
        paper = depth - OFFSET_CM
        dated = paper <= DATED_BASE_PAPER_CM
        f = (lambda ys: round(interp(paper, xs, ys))) if dated else (lambda ys: None)
        levels.append({"sample_id": r[0], "depth_cm": depth, "age_inferred": f(primary),
                       "age_inferred_younger": f(young), "age_inferred_older": f(old),
                       "age_alternative": f(alternative)})
    cols = list(levels[0])
    (HERE / "data/levels-final.csv").write_text(
        "\n".join([",".join(cols)] + [",".join("" if lv[c] is None else str(lv[c]) for c in cols) for lv in levels])
        + "\n")

    dated = [lv for lv in levels if lv["age_inferred"] is not None]
    keep = ("sample_id", "depth_cm", "age_inferred", "age_alternative")
    named, sensitivity = {}, {}
    for name, window in WINDOWS.items():
        p = bracket(dated, "age_inferred", window)
        a = bracket(dated, "age_alternative", window)
        named[name] = {"window_cal_bp": list(window), "rule": "stage-1 bracket rule on the inferred ages",
                       "endpoints": [{k: lv[k] for k in keep} for lv in p],
                       "elapsed_years": p[1]["age_inferred"] - p[0]["age_inferred"]}
        sensitivity[name] = {"alternative_selects_same_endpoints": [lv["sample_id"] for lv in a] ==
                             [lv["sample_id"] for lv in p],
                             "alternative_endpoints": [{k: lv[k] for k in keep} for lv in a]}

    ids = [lv["sample_id"] for lv in levels]
    pairs = [[a, b] for a, b in zip(ids, ids[1:])]
    for v in [*named.values(), *sensitivity.values()]:
        pair = [e["sample_id"] for e in v.get("endpoints", v.get("alternative_endpoints"))]
        if pair not in pairs:
            pairs.append(pair)
    specs = {}
    for name, spec in base["specs"].items():
        spec = dict(spec, input="data/counts-final.tsv")
        if name == "rarefaction":
            spec["sizes"] = "minimum_total"
        if name == "count_homogeneity":
            spec["pairs"] = pairs
        specs[name] = spec
    validation = {k: pa.validate(dict(v, input=str(table))) for k, v in specs.items()}
    specs["rarefaction"]["sizes"] = validation["rarefaction"]["sizes"]
    design = {
        "stage": "amendment 2: working case-study repairs on Barry's instruction; see AMENDMENT-2.md",
        "base_design_counts_sha256": base["counts_sha256"],
        "imputed": IMPUTED,
        "chronology": {"model": "linear interpolation on paper depth (archive - 30 cm) through the surface "
                                "(0 cm, 0 cal BP) and the five radiocarbon controls, each at the calibrated age "
                                "the archived model gives at its depth label",
                       "primary_controls_cal_bp": dict(zip(map(str, xs), primary)),
                       "alternative_controls_cal_bp": dict(zip(map(str, xs), alternative)),
                       "alternative": "same rule on the IPPD-1 (IntCal09 best-fit) control ages",
                       "dated_base_archive_cm": DATED_BASE_PAPER_CM + OFFSET_CM},
        "levels_file": "data/levels-final.csv", "age_labels": {"primary": "inferred", "alternative": "alternative"},
        "candidate_offset_cm": OFFSET_CM,
        "named_comparisons": named, "chronology_sensitivity": sensitivity,
        "declared_pairs": {"n": len(pairs), "adjacent": len(ids) - 1,
                           "named_or_sensitivity": len(pairs) - len(ids) + 1},
        "reporting_rules": base["reporting_rules"], "specs": specs, "validation": validation,
        "amend_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "counts_sha256": hashlib.sha256(table.read_bytes()).hexdigest(),
    }
    (HERE / "design-final.json").write_text(json.dumps(design, indent=1) + "\n")
    print(json.dumps({"named": named, "sensitivity": sensitivity, "pairs": len(pairs),
                      "validation": {k: v["status"] for k, v in validation.items()},
                      "size": specs["rarefaction"]["sizes"]}, indent=1))


if __name__ == "__main__":
    main()
