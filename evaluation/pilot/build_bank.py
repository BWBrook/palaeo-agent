"""Sprint-4 pilot bank: 12 trap/control families, plus a disjoint calibration set.

Deterministic and independent of palaeo_agent. Each trap states a scientific fact
in its dictionary and never states its consequence in the task. Each key carries
a sufficiency witness: the derivation from stated facts to the keyed handling.
Keys use exact rationals where the definitions allow (Bray-Curtis, PERMANOVA
sums of squares) and float64 once, from exact inputs, for logarithms and roots.

    uv run python evaluation/pilot/build_bank.py            # writes items/ and calibration/
"""

from fractions import Fraction
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import random
import shutil

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LEGACY = REPO / "benchmarks/past/legacy-data"
TOLERANCE = {"abs": 1e-4, "rel": 1e-4}
BANK_VERSION = "pilot-v3"


# ---------- exact definitions ----------

def bc(a, b):
    total = sum(a) + sum(b)
    return Fraction(sum(abs(Fraction(x) - Fraction(y)) for x, y in zip(a, b)), 1) / total


def relative(row):
    total = sum(row)
    return [Fraction(x, total) for x in row]


def mean_pairwise(rows):
    pairs = list(combinations(rows, 2))
    return sum(bc(a, b) for a, b in pairs) / len(pairs)


def permanova(rows, groups):
    n, labels = len(rows), sorted(set(groups))
    d2 = {(i, j): bc(rows[i], rows[j]) ** 2 for i, j in combinations(range(n), 2)}
    ss_t = sum(d2.values()) / n
    ss_w = sum(sum(v for (i, j), v in d2.items() if groups[i] == groups[j] == g) / groups.count(g) for g in labels)
    a = len(labels)
    return {"pseudo_f": float(((ss_t - ss_w) / (a - 1)) / (ss_w / (n - a))), "r_squared": float((ss_t - ss_w) / ss_t)}


def shannon(row):
    total = sum(row)
    return -math.fsum(float(Fraction(x, total)) * math.log(Fraction(x, total)) for x in row if x)


def rma(x, y):
    n = len(x)
    mx, my = math.fsum(x) / n, math.fsum(y) / n
    sxx = math.fsum((v - mx) ** 2 for v in x)
    syy = math.fsum((v - my) ** 2 for v in y)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    slope = math.copysign(math.sqrt(syy / sxx), sxy)
    return {"slope": slope, "intercept": my - slope * mx, "n": n}


# ---------- data helpers ----------

def past_rows(path):
    rows = [line.split() for line in path.read_text().splitlines() if line.strip()]
    return rows[0][1:], [(r[0], r[1:]) for r in rows[1:]]


def table(header, rows, sep="\t"):
    return sep.join(header) + "\n" + "".join(sep.join(map(str, r)) + "\n" for r in rows)


def multinomial(rng, probs, total):
    counts = [0] * len(probs)
    for index in rng.choices(range(len(probs)), weights=probs, k=total):
        counts[index] += 1
    return counts


def community(rng, n_taxa, zones, total_range=(150, 400), strength=1.0):
    """Counts per sample from zone-specific profiles; every sample nonempty."""
    base = [rng.uniform(0.2, 3) for _ in range(n_taxa)]
    profiles = {z: [b * math.exp(strength * rng.gauss(0, 0.8)) for b in base] for z in sorted(set(zones))}
    rows = []
    for zone in zones:
        p = [w * math.exp(rng.gauss(0, 0.35)) for w in profiles[zone]]
        rows.append(multinomial(rng, p, rng.randint(*total_range)))
    return rows


SPECIES = ["Globigerina bulloides", "Globigerinoides ruber", "Orbulina universa", "Neogloboquadrina incompta",
           "Globorotalia inflata", "Globigerinita glutinata", "Turborotalita quinqueloba", "Globorotalia truncatulinoides",
           "Neogloboquadrina dutertrei", "Globigerinoides sacculifer", "Pulleniatina obliquiloculata",
           "Globorotalia menardii"]


def item(family, cls, stratum, task, dictionary, files, results, *, integer=(), failures=(), tokens=(),
         exclusions=(), out_of_scope=(), alternatives=(), disclosure=(), equivalents=(), witness, source, analysis):
    return {"family": family, "class": cls, "stratum": stratum, "task": task, "dictionary": dictionary,
            "files": files, "results": results, "integer": list(integer), "failures": list(failures),
            "tokens": [list(t) for t in tokens], "exclusions": list(exclusions), "out_of_scope": list(out_of_scope),
            "alternatives": list(alternatives), "disclosure": [list(t) for t in disclosure],
            "equivalents": [list(e) for e in equivalents], "witness": witness,
            "source": source, "analysis": analysis}


REPORT = "Write `answer.json` following `answer.schema.json`."


# ---------- families ----------

def p01_lost_core(cls, seed):
    """T. A database export wrote a lost core as zeros (real Hirnantian counts)."""
    header, rows = past_rows(LEGACY / "hirnanti.dat")
    rng = random.Random(seed)
    samples = [s for s in header if sum(int(r[header.index(s)]) for _, r in rows) > 0][:13]
    taxa = [(name, [int(r[header.index(s)]) for s in samples]) for name, r in rows]
    taxa = [(name, values) for name, values in taxa if any(values)]
    lost = samples[rng.randrange(2, 11)] if cls == "trap" else None
    data = [[name] + [0 if s == lost else v for s, v in zip(samples, values)] for name, values in taxa]
    valid = [s for s in samples if s != lost]
    columns = {s: [values[samples.index(s)] for _, values in taxa] for s in samples}
    key = mean_pairwise([columns[s] for s in valid])
    note = (f"Core {lost} was processed in 2019, but its picked residue was lost in a laboratory flood before counting; "
            "the database export used for this file writes uncounted cores as rows of zeros."
            if lost else "All cores were picked and counted in full by one analyst in 2019.")
    dictionary = (
        "# Hirnantian brachiopod counts\n\n"
        "`counts.tsv` is a classic PAST table: the first line lists core numbers, and each later line gives one "
        "taxon's specimen counts in those cores. Taxon codes are five-letter abbreviations of genera.\n\n"
        "Cores were taken at 1 m spacing through one section; core numbers increase upwards.\n\n"
        f"{note}\n\nCounts are whole specimens; fragments were not counted.\n")
    task = ("# Faunal turnover\n\nSummarise faunal turnover through the section as the mean Bray–Curtis "
            "dissimilarity between pairs of core assemblages, on raw counts.\n\nReport in `results`: "
            f"`mean_bray_curtis` and `n_cores` (the number of cores in the calculation).\n\n{REPORT}\n")
    failures = []
    if lost:
        failures.append({"name": "zeros_as_sample", "results": {
            "mean_bray_curtis": float(mean_pairwise([[0] * len(taxa) if s == lost else columns[s] for s in samples])),
            "n_cores": len(samples)}})
    witness = (f"The dictionary states that core {lost} was never counted and that zeros are an export convention for "
               "uncounted cores. Its row records no observation, so it has no assemblage and is excluded. The "
               "all-core mean including its unknown counts is not identified; the task asks for pairs of core "
               "assemblages." if lost else "Every core was counted; zeros are true absences.")
    return item("P01", cls, "toolkit", task, dictionary, {"counts.tsv": table(["."] + samples, data)},
                {"mean_bray_curtis": float(key), "n_cores": len(valid)}, integer=["n_cores"], failures=failures,
                tokens=[["lost", "flood", "not counted", "uncounted", "missing", lost or "-"]] if lost else [],
                exclusions=[lost] if lost else [], witness=witness, source="real: PAST hirnanti.dat (13 cores)",
                analysis="mean pairwise Bray–Curtis, raw counts")


def p02_padding(cls, seed):
    """T. Field-log IDs lack zero padding; joining by position assigns wrong zones (real Llanvirn counts)."""
    header, rows = past_rows(LEGACY / "llanvirn.dat")
    rng = random.Random(seed)
    cores = [f"LV{int(s):02d}" for s in header]
    zone_of = dict(zip(cores, ["A", "A", "B", "A", "B", "B", "A", "B", "A", "B"]))
    counts = {c: [int(r[i]) for _, r in rows] for i, c in enumerate(cores)}
    data = [[name] + [int(v) for v in r] for name, r in rows]
    log_ids = {c: (f"LV{int(c[2:])}" if cls == "trap" else c) for c in cores}
    order = cores[:]
    rng.shuffle(order)
    metadata = "core,zone,water_depth_m\n" + "".join(f"{log_ids[c]},{zone_of[c]},{rng.randint(80, 400)}\n" for c in order)
    stats = permanova([counts[c] for c in cores], [zone_of[c] for c in cores])
    positional = permanova([counts[c] for c in cores], [zone_of[c] for c in order])
    note = ("Core codes in the field log were written without zero padding." if cls == "trap" else
            "Core codes in the field log match the count file exactly.")
    dictionary = (
        "# Llanvirn trilobite and brachiopod counts\n\n"
        "`counts.tsv` is a classic PAST table: the first line lists core codes, and each later line gives one "
        "taxon's counts across the cores.\n\n"
        "`field_log.csv` records, for each core, the depositional zone assigned in the field (A: inner shelf, "
        "B: outer shelf) and the water depth estimated from sedimentology. Coring sites were drawn at random within each zone, "
        "at least 2 km apart. The log lists cores in the order they "
        f"were described, not in core-code order.\n\n{note}\n")
    task = ("# Zone comparison\n\nTest whether assemblage composition differs between depositional zones with a "
            "one-way PERMANOVA on Bray–Curtis dissimilarities of raw counts (a permutation test).\n\n"
            "Report in `results`: `pseudo_f` and `r_squared`.\n\n" + REPORT + "\n")
    return item("P02", cls, "toolkit", task, dictionary, {"counts.tsv": table(["."] + cores, data),
                                                          "field_log.csv": metadata},
                stats, failures=[{"name": "join_by_position", "results": positional}],
                tokens=[["padding", "leading zero", "zero-pad", "LV1", "pad"]] if cls == "trap" else [],
                witness=("Each log code is the count-file code without its leading zero (LV7 = LV07); matching on the "
                         "core number is the only join consistent with the stated convention."
                         if cls == "trap" else "Codes match exactly; the join is by code, not by order."),
                source="real: PAST llanvirn.dat; zones synthetic", analysis="one-way PERMANOVA, Bray–Curtis raw")


def p03_percentages(cls, seed):
    """T. Values are percentages of a stated picked total; raw counts are recoverable exactly."""
    rng = random.Random(seed)
    n = 9
    rows = community(rng, 7, ["A"] * 4 + ["B"] * 5)
    totals = [rng.choice([200, 250, 500, 1000]) for _ in range(n)]
    counts = []
    for row, total in zip(rows, totals):
        scaled = [round(v * total / sum(row)) for v in row]
        scaled[scaled.index(max(scaled))] += total - sum(scaled)
        counts.append(scaled)
    ids = [f"M{i + 1}" for i in range(n)]
    taxa = SPECIES[:7]
    if cls == "trap":
        body = [[i] + [f"{Fraction(c * 100, t):.1f}" if Fraction(c * 100, t).denominator <= 10 else None
                       for c in row] for i, row, t in zip(ids, counts, totals)]
        assert all(None not in r for r in body)
        metadata = "sample,n_picked\n" + "".join(f"{i},{t}\n" for i, t in zip(ids, totals))
        files = {"assemblage.tsv": table([".", *[t.replace(" ", "_") for t in taxa]], body),
                 "picking.csv": metadata}
        note = ("Values in `assemblage.tsv` are percentages of the specimens picked from each sample; the number "
                "picked is in `picking.csv` (`n_picked`).")
    else:
        files = {"assemblage.tsv": table([".", *[t.replace(" ", "_") for t in taxa]],
                                         [[i] + row for i, row in zip(ids, counts)]),
                 "picking.csv": "sample,n_picked\n" + "".join(f"{i},{t}\n" for i, t in zip(ids, totals))}
        note = "Values in `assemblage.tsv` are specimen counts; `picking.csv` gives the number picked per sample."
    dictionary = ("# Planktonic foraminifera, margin transect\n\n`assemblage.tsv` is a classic PAST table with "
                  "one row per sample and one column per species (underscores replace spaces).\n\n" + note +
                  "\n\nPicking targeted 200 to 1000 specimens from the >150 µm fraction.\n")
    task = ("# Assemblage dissimilarity\n\nCompute the mean Bray–Curtis dissimilarity over all pairs of samples, "
            "on raw counts.\n\nReport in `results`: `mean_bray_curtis`.\n\n" + REPORT + "\n")
    key = float(mean_pairwise(counts))
    failures = [{"name": "percentages_as_counts", "results": {
        "mean_bray_curtis": float(mean_pairwise([[c * 100 / t for c in row] for row, t in zip(counts, totals)]))}}]
    return item("P03", cls, "toolkit", task, dictionary, files, {"mean_bray_curtis": key},
                failures=failures if cls == "trap" else [],
                tokens=[["percent", "n_picked", "proportion", "convert"]] if cls == "trap" else [],
                witness=("count = percentage × n_picked / 100, an exact integer for every cell, so raw counts are "
                         "identified and Bray–Curtis on them is defined." if cls == "trap" else
                         "Values are counts."), source="synthetic", analysis="mean pairwise Bray–Curtis, raw counts")


def p04_not_assessed(cls, seed):
    """T. One campaign did not pick the small fraction; '.' means not assessed, not absent."""
    rng = random.Random(seed)
    campaign = ["2017"] * 6 + ["2021"] * 6
    rows = community(rng, 11, ["x"] * 12, strength=0.3)
    small = [8, 9, 10]
    ids = [f"K{i + 1:02d}" for i in range(12)]
    taxa = [f"T{i + 1:02d}" for i in range(11)]
    body = []
    for i, row, year in zip(ids, rows, campaign):
        body.append([i] + ["." if (cls == "trap" and year == "2017" and j in small) else v for j, v in enumerate(row)])
    common = [[v for j, v in enumerate(row) if j not in small] for row in rows]
    key = {"shannon_mean_2017": math.fsum(shannon(r) for r, y in zip(common, campaign) if y == "2017") / 6,
           "shannon_mean_2021": math.fsum(shannon(r) for r, y in zip(common, campaign) if y == "2021") / 6}
    if cls == "control":
        key = {"shannon_mean_2017": math.fsum(shannon(r) for r, y in zip(rows, campaign) if y == "2017") / 6,
               "shannon_mean_2021": math.fsum(shannon(r) for r, y in zip(rows, campaign) if y == "2021") / 6}
    failure = {"shannon_mean_2017": math.fsum(shannon(r) for r, y in zip(common, campaign) if y == "2017") / 6,
               "shannon_mean_2021": math.fsum(shannon(r) for r, y in zip(rows, campaign) if y == "2021") / 6}
    note = ("Taxa T09–T11 occur only in the 63–150 µm fraction and taxa T01–T08 only in the >150 µm fraction. The "
            ">150 µm fraction was picked completely in both campaigns; the 63–150 µm fraction was picked only in "
            "2021. Cells for fractions that were not picked are entered as '.'." if cls == "trap" else
            "Both campaigns picked the same size fractions with the same protocol; zeros are absences.")
    dictionary = ("# Benthic foraminifera, two campaigns\n\n`counts.tsv` is a classic PAST table, one row per core, "
                  "one column per taxon. `cores.csv` gives each core's campaign.\n\n" + note + "\n")
    meta = "core,campaign\n" + "".join(f"{i},{y}\n" for i, y in zip(ids, campaign))
    task = ("# Diversity change between campaigns\n\nCompare Shannon diversity (natural logarithm) between the "
            "2017 and 2021 campaigns.\n\nReport in `results`: `shannon_mean_2017` and `shannon_mean_2021`, the mean "
            "Shannon index of each campaign's cores.\n\n" + REPORT + "\n")
    return item("P04", cls, "toolkit", task, dictionary, {"counts.tsv": table([".", *taxa], body), "cores.csv": meta},
                key, failures=[{"name": "different_taxon_basis", "results": failure}] if cls == "trap" else [],
                tokens=[["T09", "fraction", "not picked", "common", "not assessed", "comparab"]] if cls == "trap" else [],
                alternatives=[{"status": "stopped", "issue_tokens": [["T09", "fraction", "not picked", "not assessed"]]}]
                if cls == "trap" else [],
                disclosure=[["T01", "T09", "fraction", "common", "63", "not picked", "comparable"]] if cls == "trap" else [],
                witness=("Full-community Shannon for 2017 is not identified ('.' is not 0). The only comparable quantity "
                         "is Shannon on T01–T08, the fraction both campaigns picked completely; it is keyed and must be "
                         "disclosed as the basis. Stopping because the full-community comparison is not identified, "
                         "with the coverage issue named, is the accepted alternative."
                         if cls == "trap" else "Identical protocols; all taxa enter."),
                source="synthetic", analysis="Shannon per core, campaign means")


def p05_labels(cls, seed):
    """T. Transcription introduced case and spacing variants of the same binomials."""
    rng = random.Random(seed)
    species = SPECIES[:8]
    rows = community(rng, 8, ["x"] * 10)
    ids = [f"B{i + 1}" for i in range(10)]
    if cls == "trap":
        variants = {1: "globigerinoides ruber", 3: "Neogloboquadrina  incompta", 4: "Globorotalia Inflata"}
        columns, body = [], [[i] for i in ids]
        for j, name in enumerate(species):
            if j in variants:
                split = [rng.randint(0, row[j]) for row in rows]
                columns += [name, variants[j]]
                for b, row, s in zip(body, rows, split):
                    b += [row[j] - s, s]
            else:
                columns.append(name)
                for b, row in zip(body, rows):
                    b.append(row[j])
        unmerged = [r[1:] for r in body]
        failures = [{"name": "variants_as_species", "results": {"richness": len(columns),
                                                                "mean_bray_curtis": float(mean_pairwise(unmerged))}}]
        note = ("The bench sheets of three analysts were transcribed without standardising capitalisation or "
                "spacing; every taxon is a species identified to its standard binomial.")
    else:
        columns, body, failures = species, [[i] + row for i, row in zip(ids, rows)], []
        note = "Names were standardised against the 2020 checklist; every column is a distinct species."
    lines = ["sample\t" + "\t".join(columns)] + ["\t".join(map(str, b)) for b in body]
    dictionary = ("# Core-top planktonic foraminifera\n\n`counts.txt` is tab-separated: one row per sample, one "
                  "column per taxon name as written on the bench sheets.\n\n" + note + "\n")
    task = ("# Richness and dissimilarity\n\nReport the number of species recorded across all samples, and the mean "
            "Bray–Curtis dissimilarity over all pairs of samples on raw counts.\n\nReport in `results`: `richness` "
            "and `mean_bray_curtis`.\n\n" + REPORT + "\n")
    return item("P05", cls, "toolkit", task, dictionary, {"counts.txt": "\n".join(lines) + "\n"},
                {"richness": 8, "mean_bray_curtis": float(mean_pairwise(rows))}, integer=["richness"],
                failures=failures, tokens=[["capital", "spacing", "case", "variant", "merge"]] if cls == "trap" else [],
                witness=("Binomials are case-insensitive in this sense and spacing carries no meaning, so columns whose "
                         "names differ only in case or spacing are one species; their counts sum." if cls == "trap"
                         else "Standardised distinct species."), source="synthetic",
                analysis="richness; mean pairwise Bray–Curtis, raw counts")


def p06_aliquots(cls, seed):
    """T. Rows are aliquots of cores; the replicate unit is the core."""
    rng = random.Random(seed)
    zones = ["A"] * 3 + ["B"] * 3 if cls == "trap" else ["A"] * 9 + ["B"] * 9
    if cls == "trap":
        cores = community(rng, 6, zones, strength=0.6, total_range=(300, 300))
        rows, ids, groups = [], [], []
        for c, (core, zone) in enumerate(zip(cores, zones)):
            for k, part in enumerate("abc"):
                p = [v + 0.5 for v in core]
                rows.append(multinomial(rng, p, 100))
                ids.append(f"C{c + 1}{part}")
                groups.append(zone)
        units = [[sum(rows[3 * c + k][j] for k in range(3)) for j in range(6)] for c in range(6)]
        key = permanova([relative(u) for u in units], zones) | {"n": 6}
        fail = permanova([relative(r) for r in rows], groups) | {"n": 18}
        note = ("Each core was split into three aliquots (a, b, c) that were picked separately, 100 specimens each. "
                "Aliquots share one core's sediment.")
    else:
        rows = community(rng, 6, zones, strength=0.6, total_range=(100, 100))
        ids, groups = [f"C{i + 1}" for i in range(18)], zones
        key = permanova([relative(r) for r in rows], zones) | {"n": 18}
        fail = None
        note = "Each row is a separate core, 100 specimens picked from each."
    meta = "sample,zone\n" + "".join(f"{i},{g}\n" for i, g in zip(ids, groups))
    taxa = [f"sp{j + 1}" for j in range(6)]
    dictionary = ("# Seafloor cores, two zones\n\n`counts.tsv` is a classic PAST table, one row per sample. "
                  "`zones.csv` gives each sample's zone. Cores were placed at random within each zone.\n\n" + note + "\n")
    task = ("# Zone effect\n\nTest whether assemblages differ between zones with a one-way PERMANOVA on Bray–Curtis "
            "dissimilarities of relative abundances (a permutation test).\n\nReport in `results`: `pseudo_f`, "
            "`r_squared` and `n` (the number of observations entering the test).\n\n" + REPORT + "\n")
    return item("P06", cls, "toolkit", task, dictionary,
                {"counts.tsv": table([".", *taxa], [[i] + r for i, r in zip(ids, rows)]), "zones.csv": meta},
                key, integer=["n"], failures=[{"name": "aliquots_as_units", "results": fail}] if fail else [],
                tokens=[["aliquot", "pseudorep", "split", "pool", "independent"]] if cls == "trap" else [],
                witness=("Cores are the randomised units; aliquots are subsamples of one core, so they are pooled "
                         "(counts summed; equal aliquot sizes make this identical to averaging proportions) and the "
                         "test uses 6 units." if cls == "trap" else "18 independent cores."),
                source="synthetic", analysis="one-way PERMANOVA, Bray–Curtis on relative abundance")


def p07_units(cls, seed):
    """N. One locality was measured in centimetres (real Dielasma measurements); untransformed RMA."""
    header, rows = past_rows(LEGACY / "dielasma.dat")
    records = []
    for loc in ("L1", "L2", "L3"):
        xi, yi = header.index(f"{loc}/X1"), header.index(f"{loc}/X2")
        for sid, values in rows:
            if values[xi] != ".":
                records.append((loc, Fraction(values[xi]), Fraction(values[yi])))
    lines = ["specimen,locality,length,width"]
    for k, (loc, x, y) in enumerate(records, 1):
        if cls == "trap" and loc == "L3":
            lines.append(f"D{k:03d},{loc},{float(x / 10):.3f},{float(y / 10):.3f}")
        else:
            lines.append(f"D{k:03d},{loc},{float(x):.2f},{float(y):.2f}")
    key = rma([float(x) for _, x, _ in records], [float(y) for _, _, y in records])
    key["mean_length_mm"] = float(sum(x for _, x, _ in records) / len(records))
    bad = rma([float(x / 10 if l == "L3" else x) for l, x, _ in records],
              [float(y / 10 if l == "L3" else y) for l, _, y in records])
    bad["mean_length_mm"] = float(sum(x / 10 if l == "L3" else x for l, x, _ in records) / len(records))
    note = ("L1 and L2 were measured in the laboratory with digital calipers reading in millimetres. L3 was measured "
            "in the field with a vernier caliper reading in centimetres." if cls == "trap" else
            "All localities were measured in the laboratory with digital calipers reading in millimetres.")
    dictionary = ("# Dielasma shell measurements\n\n`shells.csv` lists one brachiopod per row: specimen code, "
                  "locality (L1–L3), shell length and shell width.\n\n" + note + "\n")
    task = ("# Pooled shape relation\n\nFit a reduced major axis regression of width (y) on length (x), untransformed "
            "and in millimetres, pooling all specimens.\n\nReport in `results`: `slope`, `intercept`, "
            "`n` and `mean_length_mm` (the mean shell length of the specimens in the fit).\n\n" + REPORT + "\n")
    return item("P07", cls, "other", task, dictionary, {"shells.csv": "\n".join(lines) + "\n"}, key, integer=["n"],
                failures=[{"name": "mixed_units", "results": bad}] if cls == "trap" else [],
                tokens=[["centimet", "cm", "unit", "convert", "L3"]] if cls == "trap" else [],
                witness=("L3 values are in cm; the task asks for mm, so L3 lengths and widths are multiplied by 10."
                         if cls == "trap" else "All in mm."),
                source="real: PAST dielasma.dat (217 specimens)", analysis="RMA, untransformed, mm")


def p08_boundary(cls, seed):
    """N. The epoch boundary is given as a depth; deeper is older."""
    rng = random.Random(seed)
    depths = sorted(rng.sample(range(11, 300, 6), 16))
    boundary = 142
    while not 5 <= sum(d < boundary for d in depths) <= 11:
        depths = sorted(rng.sample(range(11, 300, 6), 16))
    epochs = ["Holocene" if d < boundary else "Pleistocene" for d in depths]
    rows = community(rng, 8, epochs, strength=0.7)
    ids = [f"S{i + 1:02d}" for i in range(16)]
    order = list(range(16))
    rng.shuffle(order)
    if cls == "trap":
        meta = "sample,depth_cm\n" + "".join(f"{ids[i]},{depths[i]}\n" for i in order)
        note = f"An age model from eight radiocarbon dates places the Pleistocene–Holocene boundary at {boundary} cm."
    else:
        meta = "sample,depth_cm,epoch\n" + "".join(f"{ids[i]},{depths[i]},{epochs[i]}\n" for i in order)
        note = "The `epoch` column comes from an age model based on eight radiocarbon dates."
    holo = [r for r, e in zip(rows, epochs) if e == "Holocene"]
    pleis = [r for r, e in zip(rows, epochs) if e == "Pleistocene"]
    dictionary = ("# Gravity core GC-4\n\n`counts.tsv` is a classic PAST table, one row per sample. `samples.csv` "
                  "gives each sample's depth below the sea floor, at the midpoint of a 1 cm thick slice.\n\n" + note + "\n")
    task = ("# Holocene assemblages\n\nFor the Holocene samples only, compute the mean Bray–Curtis dissimilarity over "
            "all pairs of samples on raw counts.\n\nReport in `results`: `mean_bray_curtis` and `n_samples`.\n\n"
            + REPORT + "\n")
    return item("P08", cls, "other", task, dictionary,
                {"counts.tsv": table([".", *[f"t{j + 1}" for j in range(8)]], [[i] + r for i, r in zip(ids, rows)]),
                 "samples.csv": meta},
                {"mean_bray_curtis": float(mean_pairwise(holo)), "n_samples": len(holo)}, integer=["n_samples"],
                out_of_scope=[i for i, e in zip(ids, epochs) if e == "Pleistocene"],
                failures=[{"name": "deeper_as_younger", "results": {"mean_bray_curtis": float(mean_pairwise(pleis)),
                                                                    "n_samples": len(pleis)}}] if cls == "trap" else [],
                tokens=[["142", "boundary", "depth", "age model"]] if cls == "trap" else [],
                witness=(f"Sediment is younger upwards, so Holocene samples are those shallower than {boundary} cm."
                         if cls == "trap" else "Epoch given."), source="synthetic",
                analysis="subset; mean pairwise Bray–Curtis, raw counts")


def p09_valves(cls, seed):
    """N. Paired valves of one individual are both listed; protocol measures right valves."""
    rng = random.Random(seed)
    n = 30
    lengths = [round(rng.uniform(12, 40), 1) for _ in range(n)]
    heights = [round(0.72 * L + rng.gauss(0, 1.4), 1) for L in lengths]
    records = [(f"V{i + 1:02d}", "R", L, H, "") for i, (L, H) in enumerate(zip(lengths, heights))]
    extra = []
    if cls == "trap":
        for k in rng.sample(range(n), 4):
            sid, _, L, H, _ = records[k]
            extra.append((f"{sid}L", "L", L, H, f"left valve of {sid}"))
    allrec = records + extra
    rng.shuffle(allrec)
    lines = ["specimen,valve,length_mm,height_mm,note"] + [",".join(map(str, r)) for r in allrec]
    key = rma([float(r[2]) for r in records], [float(r[3]) for r in records])
    bad = rma([float(r[2]) for r in allrec], [float(r[3]) for r in allrec])
    note = ("Each individual is catalogued from its right valve. Where both valves of an individual were recovered, "
            "both were catalogued and measured." if cls == "trap" else "Each individual is catalogued from its right valve.")
    dictionary = ("# Cerastoderma valves, one shell bed\n\n`valves.csv` lists catalogued valves with their side, "
                  "length and height (mm) and any curatorial note.\n\n" + note + "\n")
    task = ("# Growth allometry\n\nFit a reduced major axis regression of height (y) on length (x), untransformed, "
            "across individuals.\n\nReport in `results`: `slope`, `intercept` and `n`.\n\n" + REPORT + "\n")
    return item("P09", cls, "other", task, dictionary, {"valves.csv": "\n".join(lines) + "\n"}, key, integer=["n"],
                failures=[{"name": "both_valves", "results": bad}] if cls == "trap" else [],
                tokens=[["left valve", "pair", "same individual", "duplicate"]] if cls == "trap" else [],
                equivalents=[[r[0], r[0][:-1]] for r in extra], witness=(
                    "The task's unit is the individual. Four left valves are second valves of listed individuals with "
                    "identical measurements, so dropping them, keeping either valve, or averaging a pair all give the "
                    "keyed answer; counting both valves weights four individuals twice." if cls == "trap" else
                    "One valve per individual."), source="synthetic", analysis="RMA, untransformed")


def p10_downcore(cls, seed):
    """N. Samples are numbered downcore; the youngest is S1."""
    rng = random.Random(seed)
    rows = community(rng, 9, ["x"] * 12, strength=0.2)
    ids = [f"S{i + 1}" for i in range(12)]
    while abs(shannon(rows[0]) - shannon(rows[-1])) < 0.05:
        rows[-1] = multinomial(rng, [v + 1 for v in rows[-1][::-1]], sum(rows[-1]))
    if cls == "trap":
        note = "Samples are numbered downcore from the sediment surface: S1 is the uppermost sample."
        young, old = 0, 11
    else:
        note = "Samples are numbered upcore from the base of the section: S1 is the lowest sample."
        young, old = 11, 0
    change = shannon(rows[young]) - shannon(rows[old])
    dictionary = ("# Lake core LK-2, chironomid head capsules\n\n`counts.tsv` is a classic PAST table, one row per "
                  "sample at 4 cm spacing.\n\n" + note + "\n")
    task = ("# Diversity trend\n\nReport the change in Shannon diversity (natural logarithm) from the oldest to the "
            "youngest sample, as youngest minus oldest.\n\nReport in `results`: `shannon_change`.\n\n" + REPORT + "\n")
    return item("P10", cls, "other", task, dictionary,
                {"counts.tsv": table([".", *[f"c{j + 1}" for j in range(9)]], [[i] + r for i, r in zip(ids, rows)])},
                {"shannon_change": change},
                failures=[{"name": "reversed_age", "results": {"shannon_change": -change}}],
                tokens=[["downcore", "uppermost", "surface", "S1"]] if cls == "trap" else [],
                witness=("S1 is uppermost and therefore youngest; S12 is oldest." if cls == "trap" else
                         "S1 is lowest and therefore oldest; S12 is youngest."), source="synthetic",
                analysis="Shannon difference")


def p11_synonym(cls, seed):
    """N. An obsolete combination places a species in the wrong genus for genus-level work."""
    rng = random.Random(seed)
    names = ["Globigerina bulloides", "Globigerina falconensis", "Globigerinoides ruber", "Globigerinoides conglobatus",
             "Neogloboquadrina pachyderma", "Neogloboquadrina incompta", "Globorotalia inflata",
             "Orbulina universa"]
    rows = community(rng, len(names), ["x"] * 10)
    ids = [f"N{i + 1:02d}" for i in range(10)]
    columns, body = list(names), [[i] + r for i, r in zip(ids, rows)]
    if cls == "trap":
        columns.append("Globigerina pachyderma")
        sheets_2009 = set(rng.sample(range(10), 5))
        for k, b in enumerate(body):
            moved = b[5] if k in sheets_2009 else 0
            b[5] -= moved
            b.append(moved)
        note = ("Bench sheets from 2009 use the obsolete combination Globigerina pachyderma for the species now "
                "placed in Neogloboquadrina as Neogloboquadrina pachyderma.")
    else:
        note = "All names follow the current classification."
    genus_of = {c: c.split()[0] for c in columns}
    if cls == "trap":
        genus_of["Globigerina pachyderma"] = "Neogloboquadrina"
    genera = sorted(set(genus_of.values()))

    def by_genus(mapping):
        gs = sorted(set(mapping.values()))
        return gs, [[sum(v for c, v in zip(columns, b[1:]) if mapping[c] == g) for g in gs] for b in body]

    gs, grows = by_genus(genus_of)
    naive_gs, naive_rows = by_genus({c: c.split()[0] for c in columns})
    lines = ["sample\t" + "\t".join(columns)] + ["\t".join(map(str, b)) for b in body]
    dictionary = ("# Core-top planktonic foraminifera, species level\n\n`species.txt` is tab-separated: one row per "
                  "sample, one column per name as written on the bench sheets.\n\n" + note + "\n")
    task = ("# Genus-level dissimilarity\n\nAggregate counts to genus and compute the mean Bray–Curtis dissimilarity "
            "over all pairs of samples on raw counts.\n\nReport in `results`: `mean_bray_curtis` and `n_genera`.\n\n"
            + REPORT + "\n")
    return item("P11", cls, "other", task, dictionary, {"species.txt": "\n".join(lines) + "\n"},
                {"mean_bray_curtis": float(mean_pairwise(grows)), "n_genera": len(gs)}, integer=["n_genera"],
                failures=[{"name": "obsolete_genus", "results": {"mean_bray_curtis": float(mean_pairwise(naive_rows)),
                                                                 "n_genera": len(naive_gs)}}] if cls == "trap" else [],
                tokens=[["obsolete", "synonym", "pachyderma", "Neogloboquadrina"]] if cls == "trap" else [],
                witness=("Globigerina pachyderma is Neogloboquadrina pachyderma, so its counts belong to "
                         "Neogloboquadrina at genus level." if cls == "trap" else "Current names; genus = first word."),
                source="synthetic", analysis="genus aggregation; mean pairwise Bray–Curtis, raw counts")


def p12_unassigned(cls, seed):
    """T. Transition samples carry a blank zone; they are not a third group (real alveolinid counts)."""
    header, rows = past_rows(LEGACY / "alveolinid.dat")
    rng = random.Random(seed)
    ids = [f"A{k + 1:02d}" for k in range(len(rows))]
    counts = [[int(v) for v in r] for _, r in rows]
    n = len(ids)
    cut = n // 2
    zone = ["A" if k < cut else "B" for k in range(n)]
    blank = sorted(rng.sample(range(cut - 3, cut + 3), 3)) if cls == "trap" else []
    meta = "sample,zone\n" + "".join(f"{i},{'' if k in blank else zone[k]}\n" for k, i in enumerate(ids))
    keep = [k for k in range(n) if k not in blank]
    key = permanova([relative(counts[k]) for k in keep], [zone[k] for k in keep]) | {"n": len(keep)}
    failures = []
    if blank:
        third = [("T" if k in blank else zone[k]) for k in range(n)]
        failures.append({"name": "blank_as_group", "results": permanova([relative(c) for c in counts], third) | {"n": n}})
    note = ("Samples from the transition interval were not assigned to either zone; their zone field is blank."
            if blank else "Every sample was assigned to zone A or zone B.")
    dictionary = ("# Alveolinid foraminifera, Ilerdian section\n\n`counts.tsv` is a classic PAST table, one row per "
                  "sample (stratigraphic order, base first), one column per species. `zones.csv` gives each "
                  "sample's biozone.\n\n" + note + "\n")
    task = ("# Biozone contrast\n\nDescribe the compositional contrast between biozones A and B with the one-way "
            "PERMANOVA statistics pseudo-F and R² on Bray–Curtis dissimilarities of relative abundances. These are "
            "descriptive; no p-value is required.\n\nReport in `results`: `pseudo_f`, `r_squared` and `n` (samples "
            "in the calculation).\n\n" + REPORT + "\n")
    return item("P12", cls, "toolkit", task, dictionary,
                {"counts.tsv": table(["."] + header, [[i] + c for i, c in zip(ids, counts)]), "zones.csv": meta},
                key, integer=["n"], failures=failures,
                tokens=[["blank", "transition", "unassigned", "not assigned"]] if blank else [],
                exclusions=[ids[k] for k in blank], witness=(
                    "The test compares zones A and B; samples assigned to neither belong to no level of the factor "
                    "and are excluded, not treated as a third zone." if blank else "All assigned."),
                source="real: PAST alveolinid.dat; zones synthetic", analysis="one-way PERMANOVA, relative abundance")


FAMILIES = [p01_lost_core, p02_padding, p03_percentages, p04_not_assessed, p05_labels, p06_aliquots,
            p07_units, p08_boundary, p09_valves, p10_downcore, p11_synonym, p12_unassigned]
CALIBRATION = [p03_percentages, p04_not_assessed, p05_labels, p06_aliquots, p08_boundary, p09_valves,
               p10_downcore, p11_synonym]


def far(key, failure):
    """Every failure signature differs from the key by at least ten tolerances in some result."""
    for name, value in key.items():
        other = failure.get(name)
        if other is not None and abs(value - other) >= 10 * max(TOLERANCE["abs"], TOLERANCE["rel"] * abs(value)):
            return True
    return False


def write(root, label, built):
    directory = root / label
    materials = directory / "materials"
    materials.mkdir(parents=True)
    (materials / "task.md").write_text(built["task"])
    (materials / "dictionary.md").write_text(built["dictionary"])
    shutil.copyfile(REPO / "evaluation/answer.schema.json", materials / "answer.schema.json")
    for name, text in built["files"].items():
        (materials / name).write_text(text)
    for failure in built["failures"]:
        assert far(built["results"], failure["results"]), (label, failure["name"])
    key = {"item": label, "bank_version": BANK_VERSION, "family": built["family"], "class": built["class"],
           "stratum": built["stratum"], "expected": "complete", "results": built["results"],
           "integer_results": built["integer"], "tolerance": TOLERANCE, "failure_signatures": built["failures"],
           "issue_tokens": built["tokens"], "issue_token_kind": "keyword", "exclusions_expected": built["exclusions"],
           "out_of_scope_ids": built["out_of_scope"], "acceptable_alternatives": built["alternatives"],
           "disclosure_tokens": built["disclosure"], "equivalent_exclusions": built["equivalents"],
           "sufficiency_witness": built["witness"], "analysis": built["analysis"]}
    (directory / "key.json").write_text(json.dumps(key, indent=1) + "\n")
    (directory / "provenance.json").write_text(json.dumps({"source": built["source"], "generator": "build_bank.py",
                                                           "bank_version": BANK_VERSION}, indent=1) + "\n")


def manifest(root):
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(root.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    (root / "MANIFEST.json").write_text(json.dumps(files, indent=1) + "\n")


def build(root=HERE):
    for name in ("items", "calibration"):
        if (root / name).exists():
            shutil.rmtree(root / name)
    for index, family in enumerate(FAMILIES, 1):
        for cls in ("trap", "control"):
            write(root / "items", f"P{index:02d}-{cls}", family(cls, 1000 + index))
    for family in CALIBRATION:
        built = family("trap", 5000 + FAMILIES.index(family))
        write(root / "calibration", f"{built['family']}-cal", built)
    manifest(root / "items")
    manifest(root / "calibration")


if __name__ == "__main__":
    build()
