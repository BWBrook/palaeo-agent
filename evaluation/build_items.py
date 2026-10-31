"""Generate the development item bank and its keys without importing palaeo_agent.

Every item directory holds materials/ (copied into a trial workspace), key.json and
provenance.json. Counts are integers and keys use exact rational arithmetic where the
quantity is rational (Bray-Curtis, means and variances); square roots and logarithms are
taken once, in float64, from exact inputs. Rerunning this script must reproduce the bank
byte for byte.
"""

import hashlib
import json
import math
import shutil
from fractions import Fraction as F
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent / "items"
TOL = {"abs": 1e-4, "rel": 1e-4}
SEPARATION = 10  # a failure signature must differ from the key by at least this many tolerances somewhere

ITEMS = {}


# ---------- formats and exact quantities ----------

def past_table(rows, cols, cells):
    lines = ["\t".join(["."] + list(cols))]
    for label, row in zip(rows, cells, strict=True):
        lines.append("\t".join([label] + [c if isinstance(c, str) else str(c) for c in row]))
    return "\n".join(lines) + "\n"


def csv_table(header, rows):
    return "\n".join(",".join(str(c) for c in r) for r in [header] + rows) + "\n"


def bc(a, b):
    total = sum(a) + sum(b)
    return F(sum(abs(x - y) for x, y in zip(a, b)), total)


def bc_pairs(ids, matrix):
    return {f"{ids[i]}|{ids[j]}": float(bc(matrix[i], matrix[j]))
            for i in range(len(ids)) for j in range(i + 1, len(ids))}


def relative(row):
    total = sum(row)
    return [F(x, total) for x in row]


def shannon(row):
    n = sum(row)
    return -math.fsum((x / n) * math.log(x / n) for x in row if x)


def richness(row):
    return sum(1 for x in row if x)


def rma(xs, ys):
    xs, ys = [F(x) for x in xs], [F(y) for y in ys]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = math.copysign(math.sqrt(syy / sxx), sxy)
    return {"slope": slope, "intercept": float(my) - slope * float(mx), "n": n}


def rma_float(xs, ys):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    r = np.corrcoef(xs, ys)[0, 1]
    slope = math.copysign(ys.std(ddof=1) / xs.std(ddof=1), r)
    return {"slope": float(slope), "intercept": float(ys.mean() - slope * xs.mean()), "n": len(xs)}


def mm(value):
    return f"{value:.2f}"


# ---------- keys ----------

def flat(results, prefix=""):
    out = {}
    for k, v in results.items():
        if isinstance(v, dict):
            out.update(flat(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def separated(key, signature):
    a, b = flat(key), flat(signature)
    if set(a) != set(b):
        return True
    for k in a:
        if isinstance(a[k], int) and a[k] != b[k]:
            return True
        if abs(a[k] - b[k]) > SEPARATION * max(TOL["abs"], TOL["rel"] * abs(a[k])):
            return True
    return False


def item(item_id, *, catalogue, cls, files, task, dictionary, expected, results=None, integer=(),
         signatures=(), issue_tokens=(), token_kind=None, exclusions=(), purpose, smoke=False):
    for name, sig in signatures:
        assert separated(results, sig), (item_id, name)
    ITEMS[item_id] = {
        "files": files, "task": task, "dictionary": dictionary,
        "key": {"item": item_id, "catalogue": catalogue, "class": cls, "expected": expected,
                "results": results or {}, "integer_results": list(integer), "tolerance": TOL,
                "failure_signatures": [{"name": n, "results": s} for n, s in signatures],
                "issue_tokens": [list(g) for g in issue_tokens], "issue_token_kind": token_kind,
                "exclusions_expected": list(exclusions), "smoke": smoke},
        "purpose": purpose,
    }


PAIRS_SPEC = ("an object keyed `\"A|B\"` for every pair of samples, where A is listed before B in "
              "`dictionary.md`, with the dissimilarity as the value")

FORMAT_NOTE = ("Tables are tab-separated. The first row holds column labels and its first cell is `.`; "
               "the first column holds row labels.")


# ---------- D1: locality columns padded with '.' (RMA) ----------

rng = np.random.default_rng(101)
loc_n = {"L1": 40, "L2": 25, "L3": 14}
loc_mean = {"L1": 30.0, "L2": 22.0, "L3": 38.0}
shells = {}
for loc, n in loc_n.items():
    length = np.round(rng.normal(loc_mean[loc], 6.0, n), 2)
    width = np.round(0.82 * length + rng.normal(0, 1.6, n), 2)
    shells[loc] = [(mm(a), mm(b)) for a, b in zip(length, width)]
broken = {4, 21}  # zero-based rows of L1 whose width could not be measured
d1_cols = [f"{loc}/{v}" for loc in loc_n for v in ("length", "width")]
d1_cells = []
for r in range(max(loc_n.values())):
    row = []
    for loc in loc_n:
        if r < loc_n[loc]:
            length, width = shells[loc][r]
            row += [length, "." if (loc == "L1" and r in broken) else width]
        else:
            row += [".", "."]
    d1_cells.append(row)
l1_used = [(F(a), F(b)) for r, (a, b) in enumerate(shells["L1"]) if r not in broken]
d1_key = rma([a for a, _ in l1_used], [b for _, b in l1_used])
complete_rows = [r for r in range(max(loc_n.values())) if "." not in d1_cells[r]]
d1_cc = rma([F(shells["L1"][r][0]) for r in complete_rows], [F(shells["L1"][r][1]) for r in complete_rows])
d1_task = ("# Shell allometry\n\n`shells.tsv` holds length and width measurements (mm) of brachiopod shells from {what}.\n\n"
           "Fit a reduced major axis (RMA) regression of width (y) on length (x) for locality L1, on untransformed "
           "measurements.\n\nReport in `results`: `slope`, `intercept`, and `n` (the number of specimens used in the fit).\n")
d1_dict_trap = (f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`shells.tsv`: columns `L1/length`, `L1/width`, `L2/length`, "
                "`L2/width`, `L3/length`, `L3/width`, in millimetres. Each locality's specimens are listed from the "
                "first row downwards independently of the other localities, so a row number does not identify the "
                "same specimen across localities. The row labels are row numbers only.\n\nA `.` means no value: either "
                "the locality has fewer specimens than the longest column, or the measurement could not be taken "
                "because the shell was broken.\n")
item("D1-trap", catalogue="D1", cls="trap", smoke=True,
     files={"shells.tsv": past_table([str(r + 1) for r in range(len(d1_cells))], d1_cols, d1_cells)},
     task=d1_task.format(what="three localities, L1 to L3"), dictionary=d1_dict_trap, expected="complete",
     results=d1_key, integer=["n"], signatures=[("complete_case_all_columns", d1_cc)],
     issue_tokens=[["L2", "L3", "complete", "pad", "missing", "broken"]], token_kind="keyword",
     purpose="Columns of unequal length padded with '.', plus two genuinely missing widths; complete-case filtering across all columns discards valid L1 pairs.")
d1_twin_rows = [(a, b) for r, (a, b) in enumerate(shells["L1"]) if r not in broken]
item("D1-twin", catalogue="D1", cls="twin", smoke=True,
     files={"shells.tsv": past_table([str(r + 1) for r in range(len(d1_twin_rows))], ["L1/length", "L1/width"],
                                     [list(p) for p in d1_twin_rows])},
     task=d1_task.format(what="locality L1"),
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`shells.tsv`: columns `L1/length` and `L1/width`, in "
                 "millimetres, one specimen per row. The row labels are row numbers only.\n"),
     expected="complete", results=d1_key, integer=["n"],
     purpose="Clean twin of D1: the same L1 specimens with no padding or missing values.")


# ---------- shared community generator ----------

TAXA = ["Dalmanella", "Sowerbyella", "Howellites", "Platystrophia", "Orthis", "Strophomena", "Rafinesquina",
        "Leptaena", "Hesperorthis", "Lingula"]


def assemblage(seed, n_samples, n_taxa, totals, concentration=1.0):
    g = np.random.default_rng(seed)
    out = []
    for total in totals:
        p = g.dirichlet(np.full(n_taxa, concentration))
        out.append([int(x) for x in g.multinomial(total, p)])
    return out


# ---------- D2: proportions presented as counts ----------

d2_ids = [f"P{i}" for i in range(1, 7)]
d2_taxa = TAXA[:8]
d2_counts = assemblage(202, 6, 8, [48, 310, 125, 77, 402, 190], 0.8)
d2_pct = [[f"{100 * x / sum(row):.2f}" for x in row] for row in d2_counts]
for row, pct in zip(d2_counts, d2_pct):
    assert [round(float(p) * sum(row) / 100) for p in pct] == row
d2_key = {"braycurtis": bc_pairs(d2_ids, d2_counts)}
d2_pct_values = [[F(p) for p in row] for row in d2_pct]
d2_sig = {"braycurtis": {f"{d2_ids[i]}|{d2_ids[j]}": float(bc(d2_pct_values[i], d2_pct_values[j]))
                         for i in range(6) for j in range(i + 1, 6)}}
d2_task = ("# Assemblage dissimilarity\n\nCompute Bray–Curtis dissimilarities between all pairs of samples from the raw "
           f"specimen counts, without standardisation.\n\nReport in `results`: `braycurtis`, {PAIRS_SPEC}.\n")
d2_sample_list = "Samples, in order: " + ", ".join(d2_ids) + "."
item("D2-trap", catalogue="D2", cls="trap",
     files={"assemblages.tsv": past_table(d2_ids, d2_taxa, d2_pct),
            "samples.csv": csv_table(["sample_id", "n_counted"], [[s, sum(r)] for s, r in zip(d2_ids, d2_counts)])},
     task=d2_task,
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`assemblages.tsv`: samples in rows, brachiopod genera in "
                 "columns. Each value is the percentage of the specimens counted in that sample that belong to the "
                 "genus, rounded to two decimal places.\n\n`samples.csv`: comma-separated; `n_counted` is the number "
                 f"of specimens counted in each sample.\n\n{d2_sample_list}\n"),
     expected="complete", results=d2_key, signatures=[("percentages_as_counts", d2_sig)],
     issue_tokens=[["percent", "n_counted", "proportion"]], token_kind="keyword",
     purpose="Percentages with sample totals supplied; Bray-Curtis on raw counts requires reconstructing counts.")
item("D2-twin", catalogue="D2", cls="twin",
     files={"assemblages.tsv": past_table(d2_ids, d2_taxa, d2_counts)}, task=d2_task,
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`assemblages.tsv`: samples in rows, brachiopod genera in "
                 f"columns. Each value is the number of specimens counted.\n\n{d2_sample_list}\n"),
     expected="complete", results=d2_key,
     purpose="Clean twin of D2: the counts themselves.")
item("D2-under", catalogue="D2", cls="underdetermined", smoke=True,
     files={"assemblages.tsv": past_table(d2_ids, d2_taxa, d2_pct)}, task=d2_task,
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`assemblages.tsv`: samples in rows, brachiopod genera in "
                 "columns. Each value is the percentage of the specimens counted in that sample that belong to the "
                 f"genus, rounded to two decimal places.\n\n{d2_sample_list}\n"),
     expected="unresolved",
     issue_tokens=[["count", "total", "sample size", "number of specimens", "n_counted", "absolute"]],
     token_kind="keyword",
     purpose="Percentages without sample totals: raw-count Bray-Curtis cannot be recovered.")


# ---------- D3: metadata rows in a different order ----------

d3_ids = [f"C{i:02d}" for i in range(1, 9)]
d3_facies = ["reef", "lagoon", "reef", "lagoon", "lagoon", "reef", "lagoon", "reef"]
g3 = np.random.default_rng(303)
d3_counts = []
for facies in d3_facies:
    conc = 3.0 if facies == "reef" else 0.25
    d3_counts.append([int(x) for x in g3.multinomial(int(g3.integers(120, 260)), g3.dirichlet(np.full(7, conc)))])
d3_heights = [f"{h:.1f}" for h in np.round(np.linspace(1.5, 12.0, 8), 1)]
d3_meta_order = [5, 0, 7, 2, 6, 1, 4, 3]


def facies_means(assign):
    out = {}
    for f in ("reef", "lagoon"):
        vals = [shannon(d3_counts[i]) for i in range(8) if assign[i] == f]
        out[f"mean_shannon_{f}"] = math.fsum(vals) / len(vals)
    return out


d3_key = facies_means(d3_facies)
d3_positional = facies_means([d3_facies[k] for k in d3_meta_order])
d3_task = ("# Diversity by facies\n\nReport the mean Shannon diversity index H (natural logarithm, computed from the "
           "counts) of the samples in each facies.\n\nReport in `results`: `mean_shannon_reef` and "
           "`mean_shannon_lagoon`.\n")
d3_dict = (f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: samples in rows (labelled by sample ID), brachiopod "
           "genera in columns; values are specimen counts.\n\n`samples.csv`: comma-separated, one row per sample, with "
           "its `sample_id`, `facies` (reef or lagoon) and stratigraphic `height_m`.\n")
d3_counts_file = past_table(d3_ids, TAXA[:7], d3_counts)
for cls, order, smoke in (("trap", d3_meta_order, True), ("twin", list(range(8)), True)):
    item(f"D3-{cls}", catalogue="D3", cls=cls, smoke=smoke,
         files={"counts.tsv": d3_counts_file,
                "samples.csv": csv_table(["sample_id", "facies", "height_m"],
                                         [[d3_ids[k], d3_facies[k], d3_heights[k]] for k in order])},
         task=d3_task, dictionary=d3_dict, expected="complete", results=d3_key,
         signatures=[("positional_join", d3_positional)] if cls == "trap" else [],
         issue_tokens=[["order", "join", "sample id", "align"]] if cls == "trap" else [],
         token_kind="keyword" if cls == "trap" else None,
         purpose=("Metadata rows ordered differently from the count matrix; a positional join mislabels facies."
                  if cls == "trap" else "Clean twin of D3: metadata rows in matrix order."))


# ---------- D4: taxon labels differing by case or whitespace ----------

d4_ids = [f"Q{i}" for i in range(1, 7)]
d4_base_taxa = ["Dalmanella", "Sowerbyella", "Platystrophia", "Orthis", "Leptaena", "Strophomena"]
d4_counts = assemblage(404, 6, 6, [90, 140, 75, 160, 110, 95], 1.2)
split = {"Platystrophia": "PLATYSTROPHIA", "Leptaena": "Leptaena "}
g4 = np.random.default_rng(405)
d4_cols, d4_cells_cols = [], []
for t, name in enumerate(d4_base_taxa):
    column = [row[t] for row in d4_counts]
    if name in split:
        part = [int(g4.integers(0, c + 1)) if k % 2 == 0 else 0 for k, c in enumerate(column)]
        d4_cols += [name, split[name]]
        d4_cells_cols += [[c - p for c, p in zip(column, part)], part]
    else:
        d4_cols.append(name)
        d4_cells_cols.append(column)
d4_split = [list(r) for r in zip(*d4_cells_cols)]
d4_key = {"richness": {s: richness(r) for s, r in zip(d4_ids, d4_counts)}, "braycurtis": bc_pairs(d4_ids, d4_counts)}
d4_sig = {"richness": {s: richness(r) for s, r in zip(d4_ids, d4_split)}, "braycurtis": bc_pairs(d4_ids, d4_split)}
d4_task = ("# Richness and dissimilarity\n\nReport the taxon richness of each sample and the Bray–Curtis dissimilarities "
           "between all pairs of samples, on raw counts.\n\nReport in `results`: `richness`, an object keyed by sample "
           f"ID with the number of taxa present; and `braycurtis`, {PAIRS_SPEC}.\n")
d4_list = "Samples, in order: " + ", ".join(d4_ids) + "."
d4_rule = ("Taxon names are not case-sensitive, and spaces in them are not significant: column labels that differ "
           "only in letter case or spacing denote the same taxon, and their counts belong together.\n\n")
d4_dict = (f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: samples in rows, taxa in columns; values are "
           "specimen counts.\n\n{rule}" + d4_list + "\n")
item("D4-trap", catalogue="D4", cls="trap", files={"counts.tsv": past_table(d4_ids, d4_cols, d4_split)},
     task=d4_task, dictionary=d4_dict.format(rule=d4_rule), expected="complete", results=d4_key,
     integer=[f"richness.{s}" for s in d4_ids], signatures=[("labels_not_merged", d4_sig)],
     issue_tokens=[["platystrophia"], ["leptaena"]], token_kind="identifier",
     purpose="Near-duplicate taxon labels with a stated merging rule.")
item("D4-twin", catalogue="D4", cls="twin", files={"counts.tsv": past_table(d4_ids, d4_base_taxa, d4_counts)},
     task=d4_task, dictionary=d4_dict.format(rule=""), expected="complete", results=d4_key,
     integer=[f"richness.{s}" for s in d4_ids],
     purpose="Clean twin of D4: one column per taxon.")
item("D4-under", catalogue="D4", cls="underdetermined", files={"counts.tsv": past_table(d4_ids, d4_cols, d4_split)},
     task=d4_task, dictionary=d4_dict.format(rule=""), expected="unresolved",
     issue_tokens=[["platystrophia"], ["leptaena"]], token_kind="identifier",
     purpose="Near-duplicate taxon labels with no stated rule: they must be reported as unresolved, or handled under a declared assumption naming them.")


# ---------- D5: zeros under a log transform (RMA) ----------

g5 = np.random.default_rng(505)
d5_len = np.round(np.exp(g5.normal(math.log(25), 0.35, 30)), 2)
d5_wid = np.round(0.55 * d5_len ** 1.08 * np.exp(g5.normal(0, 0.06, 30)), 2)
d5_zero = {6, 17, 25}
d5_ids = [f"sp{i:02d}" for i in range(1, 31)]
d5_rows = [[mm(a), "0" if i in d5_zero else mm(b)] for i, (a, b) in enumerate(zip(d5_len, d5_wid))]
keep = [i for i in range(30) if i not in d5_zero]
d5_x = [math.log10(float(F(mm(d5_len[i])))) for i in keep]
d5_y = [math.log10(float(F(mm(d5_wid[i])))) for i in keep]
d5_key = rma_float(d5_x, d5_y)
all_x = [float(F(r[0])) for r in d5_rows]
all_y = [float(F(r[1])) for r in d5_rows]
d5_sig1 = rma_float([math.log10(x + 1) for x in all_x], [math.log10(y + 1) for y in all_y])
d5_sig2 = rma_float([math.log10(x) for x in all_x], [math.log10(y + 1) for y in all_y])
d5_task = ("# Log-scale allometry\n\nFit a reduced major axis (RMA) regression of log10(width) on log10(length).\n\n"
           "Report in `results`: `slope`, `intercept`, and `n` (the number of specimens used in the fit).\n")
d5_dict = (f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`measurements.tsv`: one specimen per row, labelled by specimen ID; "
           "columns `length` and `width` in millimetres.{zero}\n")
item("D5-trap", catalogue="D5", cls="trap",
     files={"measurements.tsv": past_table(d5_ids, ["length", "width"], d5_rows)}, task=d5_task,
     dictionary=d5_dict.format(zero=" A width of `0` means the width could not be measured because the shell margin "
                                    "is damaged; it is not a measurement."),
     expected="complete", results=d5_key, integer=["n"],
     signatures=[("log10_plus_one_both", d5_sig1), ("log10_plus_one_width", d5_sig2)],
     exclusions=[d5_ids[i] for i in sorted(d5_zero)],
     issue_tokens=[["zero", "damaged", "not measur"]], token_kind="keyword",
     purpose="Zero widths meaning 'not measurable' under a log transform.")
item("D5-twin", catalogue="D5", cls="twin",
     files={"measurements.tsv": past_table([d5_ids[i] for i in keep], ["length", "width"], [d5_rows[i] for i in keep])},
     task=d5_task, dictionary=d5_dict.format(zero=""), expected="complete", results=d5_key, integer=["n"],
     purpose="Clean twin of D5: only specimens with measured widths.")


# ---------- D6: matrix supplied taxa by samples ----------

d6_ids = [f"M{i}" for i in range(1, 7)]
d6_taxa = TAXA[:8]
d6_counts = assemblage(606, 6, 8, [85, 130, 64, 150, 98, 120], 0.6)
d6_t = [list(c) for c in zip(*d6_counts)]
d6_key = {"richness": {s: richness(r) for s, r in zip(d6_ids, d6_counts)}, "braycurtis": bc_pairs(d6_ids, d6_counts)}
d6_sig = {"richness": {t: richness(r) for t, r in zip(d6_taxa, d6_t)}, "braycurtis": bc_pairs(d6_taxa, d6_t)}
d6_task = d4_task
d6_list = ("Samples, in order: " + ", ".join(d6_ids) + ", from successive beds of one section.\n\nTaxa recorded: "
           + ", ".join(d6_taxa) + ".")
item("D6-trap", catalogue="D6", cls="trap", smoke=True,
     files={"counts.tsv": past_table(d6_taxa, d6_ids, d6_t)}, task=d6_task,
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: specimen counts of brachiopod genera in "
                 f"samples.\n\n{d6_list}\n"),
     expected="complete", results=d6_key, integer=[f"richness.{s}" for s in d6_ids],
     signatures=[("transposed", d6_sig)], issue_tokens=[["orientation", "transpos", "rows", "columns"]],
     token_kind="keyword", purpose="Taxa in rows and samples in columns, identifiable only from the labels.")
item("D6-twin", catalogue="D6", cls="twin", smoke=True,
     files={"counts.tsv": past_table(d6_ids, d6_taxa, d6_counts)}, task=d6_task,
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: specimen counts of brachiopod genera in "
                 f"samples.\n\n{d6_list}\n"),
     expected="complete", results=d6_key, integer=[f"richness.{s}" for s in d6_ids],
     purpose="Clean twin of D6: samples in rows.")
d6u_rows, d6u_cols = [f"R{i}" for i in range(1, 9)], [f"C{i}" for i in range(1, 7)]
item("D6-under", catalogue="D6", cls="underdetermined",
     files={"counts.tsv": past_table(d6u_rows, d6u_cols, d6_t)},
     task=("# Richness and dissimilarity\n\nReport the taxon richness of each sample and the Bray–Curtis "
           "dissimilarities between all pairs of samples, on raw counts.\n\nReport in `results`: `richness`, an object "
           "keyed by sample label with the number of taxa present; and `braycurtis`, an object keyed `\"A|B\"` for "
           "every pair of samples, with the dissimilarity as the value.\n"),
     dictionary=("# Data dictionary\n\nTab-separated table of brachiopod specimen counts from samples in a measured "
                 "section. The first row and the first column hold labels.\n"),
     expected="unresolved",
     issue_tokens=[["orientation", "transpos", "rows", "columns", "which axis", "which dimension"]],
     token_kind="keyword",
     purpose="Opaque labels and no dictionary statement of orientation.")


# ---------- D7: empty samples ----------

d7_ids = [f"K{i}" for i in range(1, 7)]
d7_counts = assemblage(707, 6, 7, [70, 115, 90, 60, 1, 140], 1.0)
d7_counts[4] = [0] * 7
d7_kept = [i for i in range(6) if i != 4]
d7_vals = [bc(d7_counts[i], d7_counts[j]) for a, i in enumerate(d7_kept) for j in d7_kept[a + 1:]]
d7_key = {"mean_braycurtis": float(sum(d7_vals) / len(d7_vals)), "n_pairs": len(d7_vals)}
d7_with = [F(1) if 4 in (i, j) else bc(d7_counts[i], d7_counts[j]) for i in range(6) for j in range(i + 1, 6)]
d7_sig = {"mean_braycurtis": float(sum(d7_with) / len(d7_with)), "n_pairs": 15}
d7_task = ("# Mean dissimilarity\n\nReport the mean of the Bray–Curtis dissimilarities (raw counts) over all pairs of "
           "samples.\n\nReport in `results`: `mean_braycurtis`, and `n_pairs`, the number of pairwise values "
           "averaged.\n")
d7_dict = (f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: samples in rows, labelled by sample ID; brachiopod "
           "genera in columns; values are specimen counts.{note}\n")
item("D7-trap", catalogue="D7", cls="trap", files={"counts.tsv": past_table(d7_ids, TAXA[:7], d7_counts)},
     task=d7_task, dictionary=d7_dict.format(note=" Sample K5 was processed but yielded no specimens."),
     expected="complete", results=d7_key, integer=["n_pairs"], signatures=[("empty_sample_as_one", d7_sig)],
     exclusions=["K5"], issue_tokens=[["K5"]], token_kind="identifier",
     purpose="An empty sample, whose dissimilarity to any other sample is undefined in composition.")
item("D7-twin", catalogue="D7", cls="twin",
     files={"counts.tsv": past_table([d7_ids[i] for i in d7_kept], TAXA[:7], [d7_counts[i] for i in d7_kept])},
     task=d7_task, dictionary=d7_dict.format(note=""), expected="complete", results=d7_key, integer=["n_pairs"],
     purpose="Clean twin of D7: the five samples with specimens.")


# ---------- D8: unknown values that must not become zeros ----------

d8_ids = [f"B{i}" for i in range(1, 7)]
d8_taxa = TAXA[:6] + ["Lingula"]
d8_counts = assemblage(808, 6, 7, [95, 120, 80, 130, 105, 88], 1.0)
d8_cells = [[("." if (t == 6 and s < 3) else c) for t, c in enumerate(row)] for s, row in enumerate(d8_counts)]
d8_kept = [row[:6] for row in d8_counts]
d8_key = {"braycurtis": bc_pairs(d8_ids, d8_kept)}
d8_zeroed = [[0 if c == "." else c for c in row] for row in d8_cells]
d8_sig = {"braycurtis": bc_pairs(d8_ids, d8_zeroed)}
d8_task = ("# Assemblage dissimilarity\n\nCompute Bray–Curtis dissimilarities between all pairs of samples on raw "
           f"counts.\n\nReport in `results`: `braycurtis`, {PAIRS_SPEC}.\n")
d8_list = "Samples, in order: " + ", ".join(d8_ids) + "."
item("D8-trap", catalogue="D8", cls="trap", files={"counts.tsv": past_table(d8_ids, d8_taxa, d8_cells)},
     task=d8_task,
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: samples in rows, brachiopod genera in columns; "
                 "values are specimen counts. A `.` means the genus was not assessed in that sample: Lingula was not "
                 "identified separately in samples processed before 1998 (B1–B3). Comparisons between samples must use "
                 f"only taxa assessed in every sample.\n\n{d8_list}\n"),
     expected="complete", results=d8_key, signatures=[("unknown_as_zero", d8_sig)],
     issue_tokens=[["Lingula"]], token_kind="identifier",
     purpose="Not-assessed cells coded '.', which become false absences if treated as zero.")
item("D8-twin", catalogue="D8", cls="twin", files={"counts.tsv": past_table(d8_ids, TAXA[:6], d8_kept)},
     task=d8_task,
     dictionary=(f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: samples in rows, brachiopod genera in columns; "
                 f"values are specimen counts.\n\n{d8_list}\n"),
     expected="complete", results=d8_key,
     purpose="Clean twin of D8: only taxa assessed in every sample.")


# ---------- D9: duplicate sample IDs ----------

d9_ids = [f"T{i}" for i in range(1, 7)]
d9_counts = assemblage(909, 7, 7, [100, 85, 120, 95, 110, 75, 90], 1.0)
d9_rows = d9_ids[:4] + ["T4"] + d9_ids[4:]
d9_unique = d9_counts[:4] + d9_counts[5:]
d9_key = {"richness": {s: richness(r) for s, r in zip(d9_ids, d9_unique)}, "braycurtis": bc_pairs(d9_ids, d9_unique)}
d9_task = d4_task
d9_dict = (f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: samples in rows, labelled by sample ID; brachiopod "
           "genera in columns; values are specimen counts. Each sample was counted once.\n\nSamples, in order: "
           + ", ".join(d9_ids) + ".\n")
item("D9-trap", catalogue="D9", cls="trap", files={"counts.tsv": past_table(d9_rows, TAXA[:7], d9_counts)},
     task=d9_task, dictionary=d9_dict, expected="unresolved", issue_tokens=[["T4"]], token_kind="identifier",
     purpose="Two different rows share sample ID T4; neither can be chosen from the materials.")
item("D9-twin", catalogue="D9", cls="twin", files={"counts.tsv": past_table(d9_ids, TAXA[:7], d9_unique)},
     task=d9_task, dictionary=d9_dict, expected="complete", results=d9_key,
     integer=[f"richness.{s}" for s in d9_ids],
     purpose="Clean twin of D9: unique sample IDs.")


# ---------- D10: raw counts requested where a default standardisation is tempting ----------

d10_ids = [f"V{i}" for i in range(1, 7)]
d10_counts = assemblage(1010, 6, 7, [24, 1850, 160, 610, 45, 980], 0.9)
d10_key = {"braycurtis": bc_pairs(d10_ids, d10_counts)}
d10_rel = [relative(r) for r in d10_counts]
d10_sig = {"braycurtis": {f"{d10_ids[i]}|{d10_ids[j]}": float(bc(d10_rel[i], d10_rel[j]))
                          for i in range(6) for j in range(i + 1, 6)}}
d10_eq = assemblage(1011, 6, 7, [200] * 6, 0.9)
d10_task = ("# Assemblage dissimilarity\n\nCompute Bray–Curtis dissimilarities between all pairs of samples on the raw "
            f"counts, without any standardisation or transformation.\n\nReport in `results`: `braycurtis`, {PAIRS_SPEC}.\n")
d10_dict = (f"# Data dictionary\n\n{FORMAT_NOTE}\n\n`counts.tsv`: samples in rows, brachiopod genera in columns; "
            "values are specimen counts.\n\nSamples, in order: " + ", ".join(d10_ids) + ".\n")
item("D10-trap", catalogue="D10", cls="trap", files={"counts.tsv": past_table(d10_ids, TAXA[:7], d10_counts)},
     task=d10_task, dictionary=d10_dict, expected="complete", results=d10_key,
     signatures=[("relative_abundance", d10_sig)], issue_tokens=[["raw", "standardis", "relative"]],
     token_kind="keyword", purpose="Very unequal sample totals, where relative-abundance standardisation changes every value.")
item("D10-twin", catalogue="D10", cls="twin", files={"counts.tsv": past_table(d10_ids, TAXA[:7], d10_eq)},
     task=d10_task, dictionary=d10_dict, expected="complete", results={"braycurtis": bc_pairs(d10_ids, d10_eq)},
     purpose="Clean twin of D10: equal totals, so standardisation cannot change the answer.")


# ---------- write ----------

def write(root=ROOT):
    root = Path(root)
    shutil.rmtree(root, ignore_errors=True)
    manifest = {}
    for item_id, spec in ITEMS.items():
        d = root / item_id
        (d / "materials").mkdir(parents=True)
        for name, text in {**spec["files"], "task.md": spec["task"], "dictionary.md": spec["dictionary"]}.items():
            (d / "materials" / name).write_text(text)
        (d / "key.json").write_text(json.dumps(spec["key"], indent=1) + "\n")
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((d / "materials").iterdir())}
        (d / "provenance.json").write_text(json.dumps({
            "item": item_id, "purpose": spec["purpose"], "generator": "evaluation/build_items.py",
            "author": "Claude (Opus 5.5), sprint 1, 31 October 2026",
            "data": "Synthetic, seeded; keys from exact rational arithmetic where the quantity is rational",
            "materials_sha256": hashes}, indent=1) + "\n")
        manifest[item_id] = hashlib.sha256((d / "key.json").read_bytes() + json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    (root / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


if __name__ == "__main__":
    import sys
    m = write(sys.argv[1] if len(sys.argv) > 1 else ROOT)
    print(len(m), "items:", ", ".join(m))
