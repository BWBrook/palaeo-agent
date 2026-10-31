"""Check that every item expecting a completed answer is solvable through the current toolkit API.

Each item gets the preprocessing an agent in either arm could legitimately do from the
dictionary, then the toolkit computes the requested quantities. Agreement with key.json is
also an independent cross-check of the keys, which build_items.py computes without
palaeo_agent. Run with the toolkit runtime or the development environment.
"""

import json
import math
import sys
import tempfile
from pathlib import Path

from palaeo_agent.community import CommunitySpec, calculate_community
from palaeo_agent.core import RmaSpec, calculate

ITEMS = Path(__file__).resolve().parent / "items"
TMP = Path(tempfile.mkdtemp())


def read(path):
    rows = [line.split("\t") for line in path.read_text().splitlines()]
    return rows[0][1:], [r[0] for r in rows[1:]], [r[1:] for r in rows[1:]]


def csv(path):
    return [line.split(",") for line in path.read_text().splitlines()[1:]]


def write(name, cols, rows, cells):
    path = TMP / name
    path.write_text("\n".join(["\t".join(["."] + cols)] + ["\t".join([r] + [str(c) for c in row])
                                                           for r, row in zip(rows, cells)]) + "\n")
    return path


def community(path, orientation="samples_by_taxa", empty="error", metadata=None):
    spec = CommunitySpec(method="community", input=path, format="past", orientation=orientation, value_type="count",
                         transform="none", distance="braycurtis", dimensions=1, missing="error",
                         empty_samples=empty, metadata=metadata)
    return calculate_community(spec, path.read_bytes(), metadata.read_bytes() if metadata else None)


def pairs(res):
    ids, d = res["sample_ids"], res["distances"]
    return {f"{ids[i]}|{ids[j]}": d[i][j] for i in range(len(ids)) for j in range(i + 1, len(ids))}


def rma(path, x, y, transform="none", missing="error"):
    r = calculate(RmaSpec(method="rma", input=path, format="past", x=x, y=y, transform=transform, missing=missing),
                  path.read_bytes())
    return {"slope": r["slope"], "intercept": r["intercept"], "n": r["n"]}


def richness_bc(res):
    return {"richness": {d["sample_id"]: d["richness"] for d in res["diversity"]}, "braycurtis": pairs(res)}


def solve(item_id, m):
    family = item_id.split("-")[0]
    if family == "D1":
        return rma(m / "shells.tsv", "L1/length", "L1/width", missing="drop_pairs" if item_id == "D1-trap" else "error")
    if item_id == "D2-trap":
        cols, ids, pct = read(m / "assemblages.tsv")
        n = {r[0]: int(r[1]) for r in csv(m / "samples.csv")}
        counts = [[round(float(p) * n[s] / 100) for p in row] for s, row in zip(ids, pct)]
        return {"braycurtis": pairs(community(write("d2.tsv", cols, ids, counts)))}
    if item_id in ("D2-twin", "D8-twin", "D10-trap", "D10-twin"):
        name = "assemblages.tsv" if item_id == "D2-twin" else "counts.tsv"
        return {"braycurtis": pairs(community(m / name))}
    if family == "D3":
        res = community(m / "counts.tsv", metadata=m / "samples.csv")
        facies = {r[0]: r[1] for r in csv(m / "samples.csv")}
        out = {}
        for f in ("reef", "lagoon"):
            vals = [d["shannon"] for d in res["diversity"] if facies[d["sample_id"]] == f]
            out[f"mean_shannon_{f}"] = math.fsum(vals) / len(vals)
        return out
    if item_id == "D4-trap":
        cols, ids, cells = read(m / "counts.tsv")
        names = []
        for c in cols:
            key = "".join(c.split()).lower()
            if key not in names:
                names.append(key)
        merged = [[sum(int(v) for c, v in zip(cols, row) if "".join(c.split()).lower() == k) for k in names] for row in cells]
        return richness_bc(community(write("d4.tsv", names, ids, merged)))
    if item_id in ("D4-twin", "D6-twin", "D9-twin"):
        return richness_bc(community(m / "counts.tsv"))
    if item_id == "D5-trap":
        cols, ids, cells = read(m / "measurements.tsv")
        cells = [["." if v == "0" else v for v in row] for row in cells]
        return rma(write("d5.tsv", cols, ids, cells), "length", "width", "log10", "drop_pairs")
    if item_id == "D5-twin":
        return rma(m / "measurements.tsv", "length", "width", "log10")
    if item_id == "D6-trap":
        return richness_bc(community(m / "counts.tsv", orientation="taxa_by_samples"))
    if family == "D7":
        res = community(m / "counts.tsv", empty="drop" if item_id == "D7-trap" else "error")
        vals = list(pairs(res).values())
        return {"mean_braycurtis": math.fsum(vals) / len(vals), "n_pairs": len(vals)}
    if item_id == "D8-trap":
        cols, ids, cells = read(m / "counts.tsv")
        keep = [k for k, c in enumerate(cols) if c != "Lingula"]
        return {"braycurtis": pairs(community(write("d8.tsv", [cols[k] for k in keep], ids, [[r[k] for k in keep] for r in cells])))}
    raise KeyError(item_id)


def compare(expected, actual, tol, path=""):
    bad = []
    if isinstance(expected, dict):
        if set(expected) != set(actual):
            return [f"{path}: keys {sorted(set(expected) ^ set(actual))}"]
        for k in expected:
            bad += compare(expected[k], actual[k], tol, f"{path}.{k}")
    elif isinstance(expected, int):
        bad += [] if expected == actual else [f"{path}: {actual} != {expected}"]
    elif abs(actual - expected) > max(tol["abs"], tol["rel"] * abs(expected)) / 1000:
        bad.append(f"{path}: {actual} vs {expected}")
    return bad


failures = 0
for d in sorted(p for p in ITEMS.iterdir() if p.is_dir()):
    key = json.loads((d / "key.json").read_text())
    if key["expected"] != "complete":
        print(f"{d.name:10s} skipped (expects {key['expected']})")
        continue
    problems = compare(key["results"], solve(d.name, d / "materials"), key["tolerance"])
    failures += bool(problems)
    print(f"{d.name:10s} {'agrees' if not problems else 'DISAGREES ' + '; '.join(problems[:3])}")
sys.exit(1 if failures else 0)
