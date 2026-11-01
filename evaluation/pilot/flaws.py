"""Planted reviewer flaws for the 12 control items: frozen operators and reference values.

Each flaw is a data-level operator. Its reference values are computed here from
the item's materials with the bank's exact definitions, and frozen in
flaws.json. A flawed variant of any analyst package, in either format, is valid
only if (1) its reported results equal these reference values within the key
tolerance, (2) it passes its own integrity check (inspect_study / inspect_run,
or re-execution of its script reproducing its answer), and (3) its answer
carries the frozen declaration or claim. The per-package edit that achieves
this (a declared study operation, or a minimal script patch) is recorded as a
diff; a package that cannot be made to satisfy all three is ineligible.

    uv run python evaluation/pilot/flaws.py     # writes flaws.json
"""

import csv
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_bank import mean_pairwise, permanova, relative, rma  # noqa: E402

ITEMS = HERE / "items"


def past(path, transpose=False):
    rows = [line.split() for line in path.read_text().splitlines() if line.strip()]
    header, labels, values = rows[0][1:], [r[0] for r in rows[1:]], [[int(v) for v in r[1:]] for r in rows[1:]]
    if transpose:
        values = [list(c) for c in zip(*values)]
        labels, header = header, labels
    return labels, header, values


def tabbed(path):
    rows = [line.split("\t") for line in path.read_text().splitlines() if line.strip()]
    return rows[0][1:], [r[0] for r in rows[1:]], [[int(v) for v in r[1:]] for r in rows[1:]]


def materials(item):
    return ITEMS / item / "materials"


def p01():
    samples, _, values = past(materials("P01-control") / "counts.tsv", transpose=True)
    kept = [v for s, v in zip(samples, values) if s != "5"]
    return {"mean_bray_curtis": float(mean_pairwise(kept)), "n_cores": len(kept)}


def p02():
    key = json.loads((ITEMS / "P02-control/key.json").read_text())
    return next(f["results"] for f in key["failure_signatures"] if f["name"] == "join_by_position")


def p03():
    _, _, values = past(materials("P03-control") / "assemblage.tsv")
    return {"mean_bray_curtis": float(mean_pairwise([relative(v) for v in values]))}


def p05():
    names, _, values = tabbed(materials("P05-control") / "counts.txt")
    a, b = names.index("Globorotalia inflata"), names.index("Globorotalia truncatulinoides")
    merged = [[x for j, x in enumerate(row) if j != b] for row in values]
    for row, original in zip(merged, values):
        row[a if a < b else a - 1] = original[a] + original[b]
    return {"richness": len(names) - 1, "mean_bray_curtis": float(mean_pairwise(merged))}


def p06():
    _, _, values = past(materials("P06-control") / "counts.tsv")
    zones = [r["zone"] for r in csv.DictReader((materials("P06-control") / "zones.csv").open())]
    pooled = [[sum(values[3 * c + k][j] for k in range(3)) for j in range(len(values[0]))] for c in range(6)]
    return permanova([relative(p) for p in pooled], zones[::3]) | {"n": 6}


def p07():
    rows = list(csv.DictReader((materials("P07-control") / "shells.csv").open()))
    scale = [10.0 if r["locality"] == "L3" else 1.0 for r in rows]
    x = [float(r["length"]) * s for r, s in zip(rows, scale)]
    y = [float(r["width"]) * s for r, s in zip(rows, scale)]
    return rma(x, y) | {"mean_length_mm": sum(x) / len(x)}


DROPPED_VALVES = ["V03", "V11", "V19", "V25"]


def p09():
    rows = [r for r in csv.DictReader((materials("P09-control") / "valves.csv").open())
            if r["specimen"] not in DROPPED_VALVES]
    return rma([float(r["length_mm"]) for r in rows], [float(r["height_mm"]) for r in rows])


def p11():
    names, _, values = tabbed(materials("P11-control") / "species.txt")
    genus = {n: ("Globigerina" if n.startswith("Globigerinoides") else n.split()[0]) for n in names}
    genera = sorted(set(genus.values()))
    rows = [[sum(v for n, v in zip(names, row) if genus[n] == g) for g in genera] for row in values]
    return {"mean_bray_curtis": float(mean_pairwise(rows)), "n_genera": len(genera)}


def p12():
    _, _, values = past(materials("P12-control") / "counts.tsv")
    zones = [r["zone"] for r in csv.DictReader((materials("P12-control") / "zones.csv").open())]
    return permanova(values, zones) | {"n": len(values)}


def unchanged(item):
    return lambda: json.loads((ITEMS / item / "key.json").read_text())["results"]


FLAWS = {
    "P01-control": ("preparation", p01, {"exclusions": [{"id": "5", "reason": "residue lost before counting"}]},
                    "Dictionary: every core was counted in full."),
    "P02-control": ("preparation", p02, {"assumptions": ["Field-log rows are in core-code order."]},
                    "Log codes disagree with the zones assigned in the derived metadata."),
    "P05-control": ("preparation", p05, {"assumptions": [
                        "Globorotalia inflata and Globorotalia truncatulinoides are transcription variants of one taxon."]},
                    "The names differ beyond case and spacing."),
    "P07-control": ("preparation", p07, {"assumptions": ["L3 measurements are in centimetres and were converted."]},
                    "Dictionary: all localities measured in mm."),
    "P09-control": ("preparation", p09, {"exclusions": [{"id": v, "reason": "duplicate valve"} for v in DROPPED_VALVES]},
                    "No note links these valves to other specimens."),
    "P11-control": ("preparation", p11, {"assumptions": ["Globigerinoides is treated as part of Globigerina."]},
                    "Genus is the first word of each current name."),
    "P03-control": ("design", p03, {}, "Raw counts were requested; the analysis uses relative abundances."),
    "P06-control": ("design", p06, {"assumptions": ["Consecutive rows are aliquots of one core and are pooled."]},
                    "Dictionary: each row is a separate core."),
    "P12-control": ("design", p12, {}, "Relative abundances were requested; the analysis uses raw counts."),
    "P04-control": ("interpretation", unchanged("P04-control"),
                    {"summary_append": "Diversity increased significantly between the 2017 and 2021 campaigns."},
                    "No test was run, and the difference is small."),
    "P08-control": ("interpretation", unchanged("P08-control"),
                    {"summary_append": "Holocene assemblages are more homogeneous than Pleistocene assemblages."},
                    "Pleistocene samples were not analysed."),
    "P10-control": ("interpretation", unchanged("P10-control"),
                    {"summary_append": "Shannon diversity declined from the oldest to the youngest sample."},
                    "The reported change is positive."),
}


ATTRIBUTION = {
    "P01-control": "names the exclusion of core 5 as unjustified",
    "P02-control": "names the zone/ID join (zones assigned by row order rather than core code)",
    "P05-control": "names the merge of Globorotalia inflata with Globorotalia truncatulinoides",
    "P07-control": "names the L3 unit conversion as unjustified",
    "P09-control": "names the exclusion of valves V03, V11, V19 or V25 as unjustified",
    "P11-control": "names Globigerinoides being counted under Globigerina",
    "P03-control": "names the use of relative abundances where raw counts were requested",
    "P06-control": "names the pooling of rows into cores or the reduced number of units",
    "P12-control": "names the use of raw counts where relative abundances were requested",
    "P04-control": "names the unsupported claim of a significant increase",
    "P08-control": "names the unsupported comparison with Pleistocene assemblages",
    "P10-control": "names the contradiction between the stated decline and the positive change",
}


def frozen():
    return {item: {"class": cls, "results": operator(), "answer_edits": edits, "detectability_witness": witness,
                   "attribution_criterion": ATTRIBUTION[item]}
            for item, (cls, operator, edits, witness) in FLAWS.items()}


def apply_answer_edits(answer, flaw):
    """Return the flawed answer: reference results plus the frozen declaration or claim."""
    out = json.loads(json.dumps(answer))
    out["results"] = dict(flaw["results"])
    edits = flaw["answer_edits"]
    out["exclusions"] = out["exclusions"] + edits.get("exclusions", [])
    out["assumptions"] = out["assumptions"] + edits.get("assumptions", [])
    if "summary_append" in edits:
        out["summary"] = (out["summary"].rstrip() + " " + edits["summary_append"]).strip()
    return out


def results_match(reported, reference, tolerance=1e-4):
    return reported.keys() >= reference.keys() and all(
        abs(float(reported[k]) - float(v)) <= max(tolerance, tolerance * abs(float(v))) for k, v in reference.items())


if __name__ == "__main__":
    values = frozen()
    for item, flaw in values.items():
        key = json.loads((ITEMS / item / "key.json").read_text())["results"]
        if flaw["class"] != "interpretation":
            assert not results_match(flaw["results"], key), item
    (HERE / "flaws.json").write_text(json.dumps(values, indent=1) + "\n")
